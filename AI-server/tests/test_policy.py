from app.models import GenerateRequest, ValidateSendRequest, ApprovalDecision
from app.agents.workflow import workflow
from app.services.policy_service import validate_send_policy

import pytest


@pytest.mark.asyncio
async def test_validate_send_requires_approval():
    response = await workflow.generate(GenerateRequest(
        resume_text="Skills: Node.js, SQL. Project: Built REST API.",
        job_description_text="Backend Intern requiring Node.js, REST API, SQL.",
        company_name="Acme",
        role_title="Backend Intern",
        recipient_email="hr@example.com",
    ))
    app = response.application
    # Draft email explicitly in fast mode
    draft_response = await workflow.draft_email(app.application_id)
    app = draft_response.application
    assert app.email_draft is not None
    validation = validate_send_policy(ValidateSendRequest(
        application_id=app.application_id,
        approval_id=app.approval_id,
        recipient_email=app.email_draft.to,
        email_subject=app.email_draft.subject,
        email_body=app.email_draft.body,
        attachment_version_id=app.email_draft.attachment_version_id,
    ))
    assert not validation.allowed
    assert "not approved" in " ".join(validation.reasons).lower()
