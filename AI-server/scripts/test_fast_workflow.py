import asyncio
import os
import sys

# Ensure project root is in python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.workflow import workflow
from app.models import GenerateRequest
from app.services.llm_provider import llm_provider

async def main():
    print("=== Running direct fast workflow test ===")
    
    from app.config import get_settings
    settings = get_settings()
    settings.mock_llm_mode = True
    settings.agent_execution_mode = "fast"
    
    # Reset counters
    llm_provider.reset_call_counter()
    
    print("1. Testing /generate flow...")
    response = await workflow.generate(GenerateRequest(
        resume_text="Software Engineering student. Name: Phan Quoc Thinh. Skills: Node.js, React, SQL, Git. Project: Built REST API.",
        job_description_text="Backend Intern. Requirements: Node.js, SQL, REST API, Git. Docker is a plus.",
        company_name="Acme Tech",
        role_title="Backend Intern",
        recipient_email="hr@example.com",
    ))
    
    app = response.application
    print("   Application generated:", app.application_id)
    print("   Structured Resume projects:", app.structured_resume.projects if app.structured_resume else "None")
    print("   JD requirements:", app.jd_analysis.must_have_requirements if app.jd_analysis else "None")
    print("   CV weaknesses:", app.cv_analysis.cv_weaknesses if app.cv_analysis else "None")
    print("   Tailoring strategy summary direction:", app.tailoring_strategy.summary_direction if app.tailoring_strategy else "None")
    print("   Selected CV Version ID:", app.selected_resume_version_id)
    print("   Email draft:", app.email_draft)
    print("   Approval status:", app.approval_status)
    print("   Review bundle:", response.review_bundle)
    
    # Assertions
    assert app.email_draft is None, "Email draft should not be generated during generate step in fast mode."
    assert app.approval_status == "not_requested", "Approval status should be not_requested."
    assert response.review_bundle == {}, "Review bundle should be empty dict when ApprovalAgent is not run."
    
    generate_calls = llm_provider.get_call_count()
    print(f"   Logical LLM call count for /generate: {generate_calls}")
    assert generate_calls == 2, f"Expected exactly 2 logical LLM calls, got {generate_calls}."
    
    print("2. Testing /draft-email flow...")
    draft_response = await workflow.draft_email(app.application_id)
    app = draft_response.application
    print("   Drafted email subject:", app.email_draft.subject)
    print("   Drafted email body:\n" + app.email_draft.body)
    print("   Approval status:", app.approval_status)
    print("   Approval ID:", app.approval_id)
    print("   Review bundle contents:", draft_response.review_bundle.keys())
    
    assert app.email_draft is not None, "Email draft should be populated."
    assert app.approval_status == "pending", "Approval status should be pending."
    assert app.approval_id != "", "Approval ID should not be empty."
    assert "Phan Quoc Thinh" in app.email_draft.body, "Email draft signature should use the candidate's real name."
    
    total_calls = llm_provider.get_call_count()
    print(f"   Total logical LLM call count (generate + draft-email): {total_calls}")
    assert total_calls == 3, f"Expected exactly 3 total logical LLM calls, got {total_calls}."
    print("   Retry attempt counter:", llm_provider.retry_attempt_count)
    
    print("3. Testing /revise flow (resume feedback)...")
    selected_version_id_before = app.selected_resume_version_id
    revise_response = await workflow.revise(app.application_id, "Highlight my Git skills in summary", "resume")
    app = revise_response.application
    print("   Selected CV Version ID after revise:", app.selected_resume_version_id)
    print("   Approval status after revise:", app.approval_status)
    print("   Approval ID after revise:", app.approval_id)
    
    assert app.selected_resume_version_id != selected_version_id_before, "New resume version should be created."
    assert app.approval_status == "not_requested", "Approval status should be reset to not_requested after revision."
    assert app.approval_id == "", "Approval ID should be empty/invalidated."
    
    revise_calls = llm_provider.get_call_count() - total_calls
    print(f"   Logical LLM call count for revise resume: {revise_calls}")
    assert revise_calls == 1, f"Expected exactly 1 logical LLM call for revise resume, got {revise_calls}."
    
    print("=== Direct fast workflow test passed successfully! ===")

if __name__ == "__main__":
    asyncio.run(main())
