from __future__ import annotations

from typing import Any

from app.agents.base import BaseAgent, AgentResult
from app.models import EmailDraft, ApplicationStatus
from app.prompts.builders import build_json_prompt
from app.services.llm_provider import llm_provider


class EmailComposerAgent(BaseAgent):
    name = "EmailComposerAgent"

    async def run(self, state: dict) -> AgentResult:
        session = state["session"]
        version_id = session.selected_resume_version_id
        version = next(v for v in session.tailored_resume_versions if v.version_id == version_id)
        tone = state.get("tone", "professional, concise, internship-friendly")

        schema: dict[str, Any] = {
            "type": "object",
            "required": ["subject", "body", "summary"],
            "properties": {
                "subject": {"type": "string"},
                "body": {"type": "string"},
                "summary": {"type": "string"},
            },
        }
        system, prompt = build_json_prompt(
            task=(
                "Draft a professional job application email for user review. The email must be concise, "
                "specific to the role/company when provided, and must not claim details beyond the tailored CV. "
                "Do not include unresolved placeholders. Do not send the email."
            ),
            schema=schema,
            inputs={
                "company_name": session.company_name,
                "role_title": session.role_title,
                "recipient_email": str(session.recipient_email) if session.recipient_email else None,
                "tone": tone,
                "tailored_resume": version.content,
                "job_description_text": session.job_description_text,
                "honesty_report": version.honesty_report,
            },
            skill_names=["cover-email-writing", "application-safety"],
        )
        data = await llm_provider.complete_json(prompt, system)
        if isinstance(data, dict) and data.get("mock"):
            subject, body = _fallback_email(session)
        else:
            subject = str(data.get("subject", "")).strip()
            body = str(data.get("body", "")).strip()
            if not subject or not body:
                subject, body = _fallback_email(session)

        draft = EmailDraft(
            to=session.recipient_email,
            subject=subject,
            body=body,
            attachment_version_id=version_id,
        )
        session.email_draft = draft
        session.status = ApplicationStatus.email_drafted
        return AgentResult(self.name, draft.model_dump(), ["Application email drafted by LLM for user review."])


def _fallback_email(session) -> tuple[str, str]:
    role = session.role_title or "the open position"
    company = session.company_name or "your company"
    subject = f"Application for {role}"
    if session.company_name:
        subject += f" at {company}"
    body = (
        "Dear Hiring Team,\n\n"
        f"I am writing to apply for {role} at {company}. "
        "I have attached a tailored CV that highlights my most relevant skills and projects for this position. "
        "I would appreciate the opportunity to discuss how my background can contribute to your team.\n\n"
        "Thank you for your time and consideration.\n\n"
        "Best regards,\n"
        "Applicant"
    )
    return subject, body
