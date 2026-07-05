from __future__ import annotations

from typing import Any

from app.agents.intake import IntakeAgent
from app.agents.document_parser import DocumentParserAgent
from app.agents.jd_analyzer import JDAnalyzerAgent
from app.agents.cv_analyzer import CVAnalyzerAgent
from app.agents.tailoring_strategist import TailoringStrategistAgent
from app.agents.cv_rewrite import CVRewriteAgent
from app.agents.honesty_critic import HonestyCriticAgent
from app.agents.ats_scoring import ATSScoringAgent
from app.agents.email_composer import EmailComposerAgent
from app.agents.approval import ApprovalAgent, create_review_bundle
from app.models import GenerateRequest, WorkflowResponse, ResumeVersion, ApplicationStatus
from app.prompts.builders import build_json_prompt
from app.services.diff_service import create_resume_diff
from app.services.llm_provider import llm_provider
from app.store import store
from app.utils.ids import make_id


class ApplyMateWorkflow:
    """LLM-backed, ADK-style multi-agent workflow for ApplyMate AI.

    The implementation keeps each agent as a small class with one responsibility. Several
    agents call Gemini through `LLMProvider` and inject relevant Agent Skill prompt context.
    This can later be converted to native Google ADK nodes without changing the API shape.
    """

    def __init__(self) -> None:
        self.pipeline = [
            IntakeAgent(),
            DocumentParserAgent(),
            JDAnalyzerAgent(),
            CVAnalyzerAgent(),
            TailoringStrategistAgent(),
            CVRewriteAgent(),
            HonestyCriticAgent(),
            ATSScoringAgent(),
            EmailComposerAgent(),
            ApprovalAgent(),
        ]

    async def generate(self, request: GenerateRequest) -> WorkflowResponse:
        state = {"request": request}
        completed_agents: list[str] = []
        for agent in self.pipeline:
            await agent.run(state)
            completed_agents.append(agent.name)
        session = state["session"]
        diff = create_resume_diff(session.original_resume_text, session.tailored_resume_versions[-1].content)
        store.create(session)
        store.add_audit(session.application_id, "workflow.generated", {
            "agents": completed_agents,
            "llm_enabled": True,
            "note": "CV and email drafts are generated for review only; ExpressJS owns final email delivery.",
        })
        return WorkflowResponse(application=session, review_bundle=create_review_bundle(session, diff))

    async def parse_only(self, request: GenerateRequest) -> dict:
        state = {"request": request}
        for agent in [IntakeAgent(), DocumentParserAgent(), JDAnalyzerAgent()]:
            await agent.run(state)
        return state["session"].model_dump()

    async def draft_email(self, application_id: str, tone: str = "professional") -> WorkflowResponse:
        session = store.get(application_id)
        state = {"session": session, "tone": tone}
        await EmailComposerAgent().run(state)
        await ApprovalAgent().run(state)
        store.save(session)
        store.add_audit(application_id, "email.drafted", {"tone": tone, "llm_enabled": True})
        return WorkflowResponse(application=session, review_bundle=create_review_bundle(session))

    async def revise(self, application_id: str, feedback: str, target: str) -> WorkflowResponse:
        session = store.get(application_id)
        selected_version = next(v for v in session.tailored_resume_versions if v.version_id == session.selected_resume_version_id)

        if target in ["resume", "both"]:
            revised_resume = await self._revise_resume_with_llm(session, selected_version.content, feedback)
            version = ResumeVersion(
                version_id=make_id("rv"),
                content=revised_resume["tailored_resume"],
                change_summary=revised_resume.get("change_summary", [f"Applied user feedback: {feedback}"]),
                honesty_report={
                    "status": "pending_honesty_review",
                    "notes": ["Revision created by LLM and should be reviewed again."],
                    "unsupported_claim_warnings_from_revision": revised_resume.get("unsupported_claim_warnings", []),
                },
                match_score=selected_version.match_score,
            )
            session.tailored_resume_versions.append(version)
            session.selected_resume_version_id = version.version_id
            # Re-run honesty + score on the revised resume.
            state = {"session": session}
            await HonestyCriticAgent().run(state)
            await ATSScoringAgent().run(state)

        if target in ["email", "both"]:
            await self._revise_email_with_llm(session, feedback)

        # Any content change invalidates prior approval.
        session.approval_status = "not_requested"
        session.approval_id = ""
        session.status = ApplicationStatus.generated
        store.save(session)
        store.add_audit(application_id, "revision.created", {
            "target": target,
            "feedback": feedback,
            "llm_enabled": True,
            "approval_invalidated": True,
        })
        diff = create_resume_diff(session.original_resume_text, session.tailored_resume_versions[-1].content)
        return WorkflowResponse(application=session, review_bundle=create_review_bundle(session, diff))

    async def _revise_resume_with_llm(self, session, current_resume: str, feedback: str) -> dict[str, Any]:
        schema = {
            "type": "object",
            "required": ["tailored_resume", "change_summary", "unsupported_claim_warnings"],
            "properties": {
                "tailored_resume": {"type": "string"},
                "change_summary": {"type": "array", "items": {"type": "string"}},
                "unsupported_claim_warnings": {"type": "array", "items": {"type": "string"}},
            },
        }
        system, prompt = build_json_prompt(
            task=(
                "Revise the current tailored CV using the user's natural-language feedback. "
                "Keep all factual claims grounded in the original CV. Do not add unsupported skills, "
                "metrics, employers, degrees, or project details."
            ),
            schema=schema,
            inputs={
                "user_feedback": feedback,
                "original_resume_text": session.original_resume_text,
                "job_description_text": session.job_description_text,
                "current_tailored_resume": current_resume,
                "jd_analysis": session.jd_analysis.model_dump() if session.jd_analysis else {},
                "cv_analysis": session.cv_analysis.model_dump() if session.cv_analysis else {},
                "tailoring_strategy": session.tailoring_strategy.model_dump() if session.tailoring_strategy else {},
            },
            skill_names=["resume-tailoring", "application-safety"],
        )
        data = await llm_provider.complete_json(prompt, system, max_output_tokens=8192)
        if isinstance(data, dict) and data.get("mock"):
            return {
                "tailored_resume": current_resume + f"\n\n<!-- Revision requested: {feedback} -->",
                "change_summary": [f"Recorded user feedback for offline/mock mode: {feedback}"],
                "unsupported_claim_warnings": [],
            }
        if not str(data.get("tailored_resume", "")).strip():
            raise ValueError("LLM returned empty revised resume.")
        return data

    async def _revise_email_with_llm(self, session, feedback: str) -> None:
        if not session.email_draft:
            await EmailComposerAgent().run({"session": session})
            return
        schema = {
            "type": "object",
            "required": ["subject", "body", "summary"],
            "properties": {
                "subject": {"type": "string"},
                "body": {"type": "string"},
                "summary": {"type": "string"},
            },
        }
        version = next(v for v in session.tailored_resume_versions if v.version_id == session.selected_resume_version_id)
        system, prompt = build_json_prompt(
            task=(
                "Revise the application email using the user's feedback. Do not send the email. "
                "Keep it professional, concise, and free of unresolved placeholders."
            ),
            schema=schema,
            inputs={
                "user_feedback": feedback,
                "current_email": session.email_draft.model_dump(),
                "tailored_resume": version.content,
                "company_name": session.company_name,
                "role_title": session.role_title,
                "recipient_email": str(session.recipient_email) if session.recipient_email else None,
            },
            skill_names=["cover-email-writing", "application-safety"],
        )
        data = await llm_provider.complete_json(prompt, system)
        if isinstance(data, dict) and data.get("mock"):
            session.email_draft.body += f"\n\n<!-- Email revision requested: {feedback} -->"
            return
        if data.get("subject"):
            session.email_draft.subject = str(data["subject"]).strip()
        if data.get("body"):
            session.email_draft.body = str(data["body"]).strip()


workflow = ApplyMateWorkflow()
