import pytest
from app.agents.workflow import workflow
from app.models import GenerateRequest


@pytest.mark.asyncio
async def test_generate_tailored_cv_workflow():
    response = await workflow.generate(GenerateRequest(
        resume_text="Software Engineering student. Skills: Node.js, React, SQL, Git. Project: Built REST API for workshop platform.",
        job_description_text="Backend Intern. Requirements: Node.js, RESTful API, SQL, Git. Docker is a plus.",
        company_name="Acme Tech",
        role_title="Backend Intern",
        recipient_email="hr@example.com",
    ))
    app = response.application
    assert app.application_id
    assert app.structured_resume is not None
    assert app.structured_jd is not None
    assert app.jd_analysis is not None
    assert app.cv_analysis is not None
    assert app.tailored_resume_versions
    assert app.email_draft is not None
    assert app.approval_status == "pending"
