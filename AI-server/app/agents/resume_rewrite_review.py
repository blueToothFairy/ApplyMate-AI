from __future__ import annotations

from app.agents.base import BaseAgent, AgentResult
from app.models import (
    ResumeRewriteReviewResult,
    ResumeVersion,
    ApplicationStatus,
    ChangeSummaryItem,
    TailoredResumeSection,
    TailoredResumeDetails,
    HonestyReportDetails,
    ATSScoreDetails,
)
from app.prompts.builders import build_json_prompt
from app.services.llm_provider import llm_provider
from app.utils.ids import make_id


class ResumeRewriteReviewAgent(BaseAgent):
    name = "ResumeRewriteReviewAgent"

    async def run(self, state: dict) -> AgentResult:
        session = state["session"]
        user_feedback = state.get("user_feedback")
        current_tailored_resume = state.get("current_tailored_resume")

        schema = ResumeRewriteReviewResult.model_json_schema()
        
        # Prepare inputs dictionary
        inputs = {
            "company_name": session.company_name,
            "role_title": session.role_title,
            "original_resume_text": session.original_resume_text,
            "structured_resume": session.structured_resume.model_dump() if session.structured_resume else {},
            "job_description_text": session.job_description_text,
            "jd_analysis": session.jd_analysis.model_dump() if session.jd_analysis else {},
            "cv_analysis": session.cv_analysis.model_dump() if session.cv_analysis else {},
            "tailoring_strategy": session.tailoring_strategy.model_dump() if session.tailoring_strategy else {},
        }
        
        # Inject optional user feedback inputs if running in revise mode
        if user_feedback:
            inputs["user_feedback"] = user_feedback
            inputs["current_tailored_resume"] = current_tailored_resume

        task_desc = (
            "You are a resume tailoring and quality assurance expert.\n"
            "Task: Rewrite the candidate's CV for the target JD, audit it for honesty, and score it against the JD.\n"
            "Requirements:\n"
            "1. Ground all claims in the original CV. Never add tools, skills, or achievements (such as Docker, "
            "Kubernetes, SQL, React) that are not directly mentioned or clearly supported in the original CV.\n"
            "2. Avoid subjective exaggerations (e.g. 'seamlessly', 'expertly', 'highly secure') unless fully supported.\n"
            "3. Audit the final rewritten resume in honesty_report. If risky claims remain, flag them and recommend safe rewrites.\n"
            "4. Score the rewritten resume against the JD in ats_score. Evaluate keyword coverage and alignment.\n"
            "5. Return only valid JSON adhering to the specified schema."
        )

        if user_feedback:
            task_desc += (
                "\n6. In this run, the user provided feedback/modifications. Adjust the resume to address: "
                f"'{user_feedback}' while maintaining the same strict grounding and validation constraints."
            )

        system, prompt = build_json_prompt(
            task=task_desc,
            schema=schema,
            inputs=inputs,
            skill_names=["resume-tailoring", "jd-analysis", "application-safety"],
        )

        data = await llm_provider.complete_json(prompt, system, agent_name=self.name)
        if isinstance(data, dict) and data.get("mock"):
            result = _fallback_rewrite_review(session, user_feedback, current_tailored_resume)
        else:
            result = ResumeRewriteReviewResult.model_validate(data)

        # Build new ResumeVersion and add to tailored_resume_versions
        new_version = ResumeVersion(
            version_id=make_id("rv"),
            content=result.tailored_resume.content.strip(),
            change_summary=[c.model_dump() if hasattr(c, "model_dump") else c for c in result.change_summary],
            honesty_report={
                "status": result.honesty_report.status,
                "risky_claims": result.honesty_report.risky_claims,
                "unsupported_claims": result.honesty_report.unsupported_claims,
                "safe_rewrite_suggestions": result.honesty_report.safe_rewrite_suggestions,
                "notes": result.honesty_report.notes,
                "ats_score": result.ats_score.model_dump(),
            },
            match_score=result.ats_score.score,
        )

        session.tailored_resume_versions.append(new_version)
        session.selected_resume_version_id = new_version.version_id
        session.status = ApplicationStatus.generated

        return AgentResult(self.name, result.model_dump(), ["Rewrote, audited, and scored CV with one LLM call."])


def _fallback_rewrite_review(session, user_feedback=None, current_tailored_resume=None) -> ResumeRewriteReviewResult:
    from app.agents.cv_rewrite import _fallback_rewrite
    from app.agents.honesty_critic import _fallback_report
    from app.agents.ats_scoring import _fallback_score

    # Determine tailoring content and change logs
    if user_feedback and current_tailored_resume:
        content = current_tailored_resume + f"\n\n<!-- Revision requested: {user_feedback} -->"
        change_summary_items = [
            ChangeSummaryItem(
                section="Summary",
                change=f"Applied user feedback: {user_feedback}",
                reason="User request",
                evidence_source="User feedback"
            )
        ]
    else:
        content, changes = _fallback_rewrite(session)
        change_summary_items = [
            ChangeSummaryItem(
                section="Multiple",
                change=c,
                reason="Aligning with JD requirements",
                evidence_source="Original CV"
            ) for c in changes
        ]

    # Run legacy fallbacks deterministically
    honesty_report_dict = _fallback_report(session, content)
    ats_score_dict = _fallback_score(session, content)

    # Reconstruct resume details
    sections = TailoredResumeSection(
        summary="A professional software developer with core capabilities matching the target role.",
        skills=session.structured_resume.skills if session.structured_resume else [],
        projects=session.structured_resume.projects if session.structured_resume else [],
        education=", ".join(session.structured_resume.education) if session.structured_resume and session.structured_resume.education else ""
    )

    tailored_details = TailoredResumeDetails(
        content=content,
        format="markdown",
        sections=sections
    )

    honesty_details = HonestyReportDetails(
        status="needs_review" if honesty_report_dict.get("status") == "needs_review" else "pass",
        risky_claims=honesty_report_dict.get("risky_claims", []),
        unsupported_claims=honesty_report_dict.get("risky_claims", []),
        safe_rewrite_suggestions=honesty_report_dict.get("safe_rewrite_suggestions", []),
        notes=honesty_report_dict.get("notes", [])
    )

    ats_details = ATSScoreDetails(
        score=ats_score_dict.get("match_score", 50),
        matched_keywords=ats_score_dict.get("keyword_coverage", {}).get("covered", []),
        missing_keywords=ats_score_dict.get("keyword_coverage", {}).get("missing", []),
        strengths=ats_score_dict.get("improvement_notes", []),
        weaknesses=ats_score_dict.get("improvement_notes", []),
        reasoning="Fallback mock analysis completed."
    )

    return ResumeRewriteReviewResult(
        tailored_resume=tailored_details,
        change_summary=change_summary_items,
        honesty_report=honesty_details,
        ats_score=ats_details
    )
