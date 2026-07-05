from __future__ import annotations

import base64

from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.models import (
    GenerateRequest,
    ParseRequest,
    DocumentParseRequest,
    DocumentParseResponse,
    ReviseRequest,
    DraftEmailRequest,
    ApprovalRequestCreate,
    ApprovalMarkRequest,
    ValidateSendRequest,
    EvaluateRequest,
    ApprovalDecision,
    ApplicationStatus,
)
from app.agents.workflow import workflow
from app.agents.approval import ApprovalAgent, create_review_bundle
from app.services.document_service import parse_resume_text, parse_jd_text
from app.services.policy_service import validate_send_policy
from app.services.export_service import export_resume_docx
from app.store import store
from app.utils.ids import make_id
from app.utils.text import detect_prompt_injection
from app.utils.file_extractors import extract_text_from_bytes

settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": settings.app_name, "env": settings.app_env}


@app.get("/ai/skills")
def list_skills() -> dict:
    from app.services.skill_loader import SkillLoader
    return {"skills": SkillLoader().list_skills()}



@app.post("/ai/documents/parse", response_model=DocumentParseResponse)
def parse_document(request: DocumentParseRequest) -> DocumentParseResponse:
    """Parse uploaded CV/JD files inside the AI-server boundary.

    The ExpressJS API-server should only receive the upload and forward base64 bytes here.
    This endpoint owns PDF/DOCX/TXT/MD extraction so document parsing stays with the
    FastAPI AI-server as defined by the project architecture.
    """
    try:
        raw = base64.b64decode(request.content_base64, validate=True)
        text = extract_text_from_bytes(raw, request.filename, request.mime_type)
        if not text.strip():
            raise ValueError("Document parsing produced empty text.")
        hits = detect_prompt_injection(text)
        structured_resume = parse_resume_text(text) if request.document_type == "resume" else None
        structured_jd = parse_jd_text(text) if request.document_type == "job_description" else None
        return DocumentParseResponse(
            filename=request.filename,
            mime_type=request.mime_type,
            document_type=request.document_type,
            text=text,
            character_count=len(text),
            structured_resume=structured_resume,
            structured_jd=structured_jd,
            prompt_injection_hits=hits,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to parse document in AI-server: {exc}") from exc


@app.post("/ai/parse")
async def parse(request: ParseRequest) -> dict:
    return {
        "structured_resume": parse_resume_text(request.resume_text).model_dump(),
        "structured_jd": parse_jd_text(request.job_description_text).model_dump(),
        "prompt_injection_hits": detect_prompt_injection(request.job_description_text + "\n" + request.resume_text),
    }


@app.post("/ai/generate-tailored-cv")
async def generate_tailored_cv(request: GenerateRequest):
    try:
        return await workflow.generate(request)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/ai/revise")
async def revise(request: ReviseRequest):
    try:
        return await workflow.revise(request.application_id, request.feedback, request.target.value)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/ai/draft-email")
async def draft_email(request: DraftEmailRequest):
    try:
        return await workflow.draft_email(request.application_id, request.tone)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/ai/approval/request")
async def request_approval(request: ApprovalRequestCreate):
    try:
        session = store.get(request.application_id)
        state = {"session": session}
        await ApprovalAgent().run(state)
        store.save(session)
        store.add_audit(session.application_id, "approval.requested", {"approval_id": session.approval_id})
        return create_review_bundle(session)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/ai/approval/mark")
async def mark_approval(request: ApprovalMarkRequest):
    try:
        session = store.get(request.application_id)
        if request.approval_id and request.approval_id != session.approval_id:
            raise HTTPException(status_code=409, detail="Approval ID does not match active approval.")
        session.approval_status = request.decision.value
        if request.decision == ApprovalDecision.approved:
            session.status = ApplicationStatus.approved
        elif request.decision == ApprovalDecision.rejected:
            session.status = ApplicationStatus.rejected
        else:
            session.status = ApplicationStatus.pending_approval
        store.save(session)
        store.add_audit(session.application_id, "approval.marked", {
            "decision": request.decision.value,
            "feedback": request.feedback,
            "approval_id": session.approval_id,
        })
        return create_review_bundle(session)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/ai/validate-send")
async def validate_send(request: ValidateSendRequest):
    response = validate_send_policy(request)
    if response.allowed:
        session = store.get(request.application_id)
        session.status = ApplicationStatus.validated_for_send
        store.save(session)
        store.add_audit(request.application_id, "send_policy.validated", {"approval_id": request.approval_id})
    else:
        try:
            store.add_audit(request.application_id, "send_policy.rejected", {"reasons": response.reasons})
        except Exception:
            pass
    return response


@app.post("/ai/evaluate")
async def evaluate(request: EvaluateRequest) -> dict:
    result = await workflow.generate(GenerateRequest(**request.model_dump()))
    app_session = result.application
    version = next(v for v in app_session.tailored_resume_versions if v.version_id == app_session.selected_resume_version_id)
    return {
        "case_status": "pass" if version.match_score >= 40 else "needs_review",
        "match_score": version.match_score,
        "honesty_status": version.honesty_report.get("status"),
        "prompt_injection_hits": detect_prompt_injection(request.job_description_text),
        "must_not_send_email": True,
        "application_id": app_session.application_id,
    }


@app.get("/ai/applications/{application_id}")
def get_application(application_id: str):
    try:
        return store.get(application_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/ai/applications/{application_id}/export/docx")
def export_docx(application_id: str, resume_version_id: str | None = None):
    try:
        path = export_resume_docx(application_id, resume_version_id)
        return FileResponse(
            path=path,
            filename=Path(path).name,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
