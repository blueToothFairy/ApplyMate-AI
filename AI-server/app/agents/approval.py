from __future__ import annotations

from app.agents.base import BaseAgent, AgentResult
from app.models import ApprovalRecord, ApplicationStatus
from app.utils.ids import make_id


class ApprovalAgent(BaseAgent):
    name = "ApprovalAgent"

    async def run(self, state: dict) -> AgentResult:
        session = state["session"]
        if not session.email_draft:
            raise ValueError("Cannot create approval bundle before email draft exists.")
        approval = ApprovalRecord(
            approval_id=make_id("appr"),
            approved_resume_version_id=session.selected_resume_version_id,
            approved_email_subject=session.email_draft.subject,
            approved_email_body=session.email_draft.body,
            approved_recipient=session.email_draft.to,
            status="pending",
        )
        session.approval_status = "pending"
        session.approval_id = approval.approval_id
        session.status = ApplicationStatus.pending_approval
        state["approval_record"] = approval
        return AgentResult(self.name, approval.model_dump(), ["Review bundle and pending approval created."])


def create_review_bundle(session, diff: dict | None = None) -> dict:
    selected_version = next((v for v in session.tailored_resume_versions if v.version_id == session.selected_resume_version_id), None)
    return {
        "application_id": session.application_id,
        "status": session.status,
        "approval_status": session.approval_status,
        "approval_id": session.approval_id,
        "company_name": session.company_name,
        "role_title": session.role_title,
        "recipient_email": str(session.recipient_email) if session.recipient_email else None,
        "tailored_resume": selected_version.model_dump() if selected_version else None,
        "email_draft": session.email_draft.model_dump() if session.email_draft else None,
        "jd_analysis": session.jd_analysis.model_dump() if session.jd_analysis else None,
        "cv_analysis": session.cv_analysis.model_dump() if session.cv_analysis else None,
        "diff": diff,
        "audit_events": [e.model_dump() for e in session.audit_events],
    }
