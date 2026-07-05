from __future__ import annotations

from app.models import PolicyValidationResponse, ValidateSendRequest
from app.store import store
from app.utils.text import has_placeholder, detect_prompt_injection


def validate_send_policy(request: ValidateSendRequest) -> PolicyValidationResponse:
    reasons: list[str] = []
    try:
        session = store.get(request.application_id)
    except KeyError:
        return PolicyValidationResponse(allowed=False, reasons=["Application session not found."])

    if session.approval_status != "approved":
        reasons.append("Application is not approved by the user.")
    if request.approval_id != session.approval_id:
        reasons.append("Approval ID does not match the active approval record.")
    if not session.email_draft:
        reasons.append("No email draft exists.")
    else:
        if str(request.recipient_email) != str(session.email_draft.to):
            reasons.append("Recipient email does not match the approved draft.")
        if request.email_subject != session.email_draft.subject:
            reasons.append("Email subject does not match the approved draft.")
        if request.email_body != session.email_draft.body:
            reasons.append("Email body does not match the approved draft.")
        if request.attachment_version_id != session.email_draft.attachment_version_id:
            reasons.append("Attachment version does not match the approved draft.")

    if request.attachment_version_id != session.selected_resume_version_id:
        reasons.append("Attachment version is not the selected resume version.")
    if has_placeholder(request.email_subject) or has_placeholder(request.email_body):
        reasons.append("Email contains unresolved placeholders.")
    if detect_prompt_injection(request.email_body):
        reasons.append("Email body contains suspicious instruction-like content.")

    if reasons:
        return PolicyValidationResponse(allowed=False, reasons=reasons)

    return PolicyValidationResponse(
        allowed=True,
        reasons=[],
        send_payload={
            "to": str(request.recipient_email),
            "subject": request.email_subject,
            "body": request.email_body,
            "attachment_version_id": request.attachment_version_id,
            "application_id": request.application_id,
            "approval_id": request.approval_id,
        },
    )
