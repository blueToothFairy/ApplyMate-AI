from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal
from pydantic import BaseModel, EmailStr, Field


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class RevisionTarget(str, Enum):
    resume = "resume"
    email = "email"
    both = "both"


class ApprovalDecision(str, Enum):
    approved = "approved"
    rejected = "rejected"
    needs_revision = "needs_revision"


class ApplicationStatus(str, Enum):
    created = "created"
    parsed = "parsed"
    generated = "generated"
    email_drafted = "email_drafted"
    pending_approval = "pending_approval"
    approved = "approved"
    rejected = "rejected"
    validated_for_send = "validated_for_send"


class ParseRequest(BaseModel):
    resume_text: str = Field(..., min_length=1)
    job_description_text: str = Field(..., min_length=1)


class DocumentParseRequest(BaseModel):
    filename: str = Field(..., min_length=1)
    mime_type: str = "application/octet-stream"
    content_base64: str = Field(..., min_length=1)
    document_type: Literal["resume", "job_description"] = "resume"


class DocumentParseResponse(BaseModel):
    filename: str
    mime_type: str
    document_type: Literal["resume", "job_description"]
    text: str
    character_count: int
    structured_resume: StructuredResume | None = None
    structured_jd: StructuredJD | None = None
    prompt_injection_hits: list[str] = Field(default_factory=list)


class GenerateRequest(ParseRequest):
    company_name: str = ""
    role_title: str = ""
    recipient_email: EmailStr | None = None


class ReviseRequest(BaseModel):
    application_id: str
    feedback: str = Field(..., min_length=1)
    target: RevisionTarget = RevisionTarget.resume


class DraftEmailRequest(BaseModel):
    application_id: str
    tone: str = "professional, concise, internship-friendly"


class ApprovalRequestCreate(BaseModel):
    application_id: str


class ApprovalMarkRequest(BaseModel):
    application_id: str
    decision: ApprovalDecision
    approval_id: str | None = None
    feedback: str = ""


class ValidateSendRequest(BaseModel):
    application_id: str
    approval_id: str
    recipient_email: EmailStr
    email_subject: str
    email_body: str
    attachment_version_id: str


class EvaluateRequest(BaseModel):
    resume_text: str
    job_description_text: str
    company_name: str = "Demo Company"
    role_title: str = "Backend Intern"
    recipient_email: EmailStr | None = None


class StructuredResume(BaseModel):
    summary: str = ""
    skills: list[str] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)
    experience: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    certificates: list[str] = Field(default_factory=list)
    raw_sections: dict[str, str] = Field(default_factory=dict)


class StructuredJD(BaseModel):
    responsibilities: list[str] = Field(default_factory=list)
    requirements: list[str] = Field(default_factory=list)
    qualifications: list[str] = Field(default_factory=list)
    tech_stack: list[str] = Field(default_factory=list)
    company_context: str = ""


class JDAnalysis(BaseModel):
    jd_requirements: dict[str, list[str]] = Field(default_factory=dict)
    jd_keywords: list[str] = Field(default_factory=list)
    role_focus: dict[str, str] = Field(default_factory=dict)
    priority_matrix: list[dict[str, Any]] = Field(default_factory=list)


class CVAnalysis(BaseModel):
    cv_strengths: list[str] = Field(default_factory=list)
    cv_weaknesses: list[str] = Field(default_factory=list)
    missing_keywords: list[str] = Field(default_factory=list)
    weak_bullets: list[str] = Field(default_factory=list)
    improvement_opportunities: list[str] = Field(default_factory=list)


class TailoringStrategy(BaseModel):
    tailoring_strategy: str
    rewrite_plan: list[str] = Field(default_factory=list)
    section_priority: list[str] = Field(default_factory=list)
    evidence_map: dict[str, str] = Field(default_factory=dict)


class ResumeVersion(BaseModel):
    version_id: str
    content: str
    created_at: str = Field(default_factory=now_iso)
    change_summary: list[str] = Field(default_factory=list)
    honesty_report: dict[str, Any] = Field(default_factory=dict)
    match_score: int = 0


class EmailDraft(BaseModel):
    to: EmailStr | None = None
    subject: str = ""
    body: str = ""
    attachment_version_id: str = ""
    created_at: str = Field(default_factory=now_iso)


class ApprovalRecord(BaseModel):
    approval_id: str
    approved_resume_version_id: str
    approved_email_subject: str
    approved_email_body: str
    approved_recipient: EmailStr | None = None
    status: Literal["pending", "approved", "rejected", "needs_revision"] = "pending"
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)
    feedback: str = ""


class AuditEvent(BaseModel):
    event_id: str
    action: str
    detail: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=now_iso)


class ApplicationSession(BaseModel):
    application_id: str
    original_resume_text: str
    job_description_text: str
    company_name: str = ""
    role_title: str = ""
    recipient_email: EmailStr | None = None
    structured_resume: StructuredResume | None = None
    structured_jd: StructuredJD | None = None
    jd_analysis: JDAnalysis | None = None
    cv_analysis: CVAnalysis | None = None
    tailoring_strategy: TailoringStrategy | None = None
    tailored_resume_versions: list[ResumeVersion] = Field(default_factory=list)
    selected_resume_version_id: str = ""
    email_draft: EmailDraft | None = None
    approval_status: str = "not_requested"
    approval_id: str = ""
    audit_events: list[AuditEvent] = Field(default_factory=list)
    status: ApplicationStatus = ApplicationStatus.created


class WorkflowResponse(BaseModel):
    application: ApplicationSession
    review_bundle: dict[str, Any]


class PolicyValidationResponse(BaseModel):
    allowed: bool
    reasons: list[str] = Field(default_factory=list)
    send_payload: dict[str, Any] | None = None
