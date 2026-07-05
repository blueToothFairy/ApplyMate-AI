from __future__ import annotations

from app.services.document_service import parse_resume_text, parse_jd_text
from app.services.diff_service import create_resume_diff
from app.services.policy_service import validate_send_policy
from app.models import ValidateSendRequest, GenerateRequest, DraftEmailRequest, ReviseRequest
from app.store import store
from app.utils.text import find_keywords, detect_role_focus, detect_prompt_injection


def parse_resume(file_text: str) -> dict:
    return parse_resume_text(file_text).model_dump()


def parse_job_description(text: str) -> dict:
    return parse_jd_text(text).model_dump()


def analyze_resume_jd_fit(resume_text: str, jd_text: str) -> dict:
    resume_keywords = set(find_keywords(resume_text))
    jd_keywords = set(find_keywords(jd_text))
    covered = sorted(resume_keywords & jd_keywords)
    missing = sorted(jd_keywords - resume_keywords)
    score = int((len(covered) / max(1, len(jd_keywords))) * 100)
    return {
        "score": score,
        "covered_keywords": covered,
        "missing_keywords": missing,
        "role_focus": detect_role_focus(jd_text),
        "prompt_injection_hits": detect_prompt_injection(jd_text),
    }


async def generate_tailored_resume(payload: dict) -> dict:
    """Run the LLM-backed multi-agent workflow and create a review bundle."""
    from app.agents.workflow import workflow
    request = GenerateRequest(**payload)
    response = await workflow.generate(request)
    return response.model_dump()


async def create_email_draft(application_id: str, tone: str = "professional, concise") -> dict:
    from app.agents.workflow import workflow
    response = await workflow.draft_email(application_id, tone)
    return response.model_dump()


async def revise_application(application_id: str, feedback: str, target: str = "resume") -> dict:
    from app.agents.workflow import workflow
    request = ReviseRequest(application_id=application_id, feedback=feedback, target=target)
    response = await workflow.revise(request.application_id, request.feedback, request.target.value)
    return response.model_dump()


def create_resume_diff_tool(original_resume: str, tailored_resume: str) -> dict:
    return create_resume_diff(original_resume, tailored_resume)


def score_resume_against_jd(tailored_resume: str, job_description_text: str) -> dict:
    jd_keywords = set(find_keywords(job_description_text))
    cv_keywords = set(find_keywords(tailored_resume))
    covered = sorted(jd_keywords & cv_keywords)
    missing = sorted(jd_keywords - cv_keywords)
    return {
        "match_score": int((len(covered) / max(1, len(jd_keywords))) * 100),
        "keyword_coverage": {"covered": covered, "missing": missing},
    }


def create_review_bundle(application_id: str) -> dict:
    session = store.get(application_id)
    version = next((v for v in session.tailored_resume_versions if v.version_id == session.selected_resume_version_id), None)
    return {
        "application_id": application_id,
        "approval_status": session.approval_status,
        "approval_id": session.approval_id,
        "tailored_resume": version.model_dump() if version else None,
        "email_draft": session.email_draft.model_dump() if session.email_draft else None,
    }


def validate_send_policy_tool(payload: dict) -> dict:
    request = ValidateSendRequest(**payload)
    return validate_send_policy(request).model_dump()


def log_audit_event(application_id: str, action: str, detail: dict) -> dict:
    return store.add_audit(application_id, action, detail).model_dump()


def send_application_email(*args, **kwargs):
    raise RuntimeError("Email sending is owned by the ExpressJS API server in this MVP. Use validate_send_policy first.")
