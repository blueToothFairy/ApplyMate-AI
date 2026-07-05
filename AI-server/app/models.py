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
    # Legacy fields
    jd_requirements: dict[str, list[str]] = Field(default_factory=dict)
    jd_keywords: list[str] = Field(default_factory=list)
    priority_matrix: list[dict[str, Any]] = Field(default_factory=list)

    # Union field to accept both legacy dict and new string role focus
    role_focus: dict[str, str] | str = ""

    # New fast agent fields
    role_title: str = ""
    company_name: str = ""
    responsibilities: list[str] = Field(default_factory=list)
    must_have_requirements: list[str] = Field(default_factory=list)
    nice_to_have_requirements: list[str] = Field(default_factory=list)
    technical_keywords: list[str] = Field(default_factory=list)
    soft_skill_keywords: list[str] = Field(default_factory=list)
    domain_keywords: list[str] = Field(default_factory=list)
    seniority_level: str = ""


class CVAnalysis(BaseModel):
    # Legacy fields
    cv_strengths: list[str] = Field(default_factory=list)
    cv_weaknesses: list[str] = Field(default_factory=list)
    missing_keywords: list[str] = Field(default_factory=list)
    weak_bullets: list[str] = Field(default_factory=list)
    improvement_opportunities: list[str] = Field(default_factory=list)

    # New fast agent fields
    candidate_name: str = ""
    current_positioning: str = ""
    supported_skills: list[str] = Field(default_factory=list)
    supported_projects: list[str] = Field(default_factory=list)
    strong_evidence: list[str] = Field(default_factory=list)
    weak_or_missing_keywords: list[str] = Field(default_factory=list)
    unsupported_jd_claims_to_avoid: list[str] = Field(default_factory=list)
    most_relevant_experiences: list[str] = Field(default_factory=list)


class TailoringStrategy(BaseModel):
    # Legacy fields
    tailoring_strategy: str = ""
    rewrite_plan: list[str] = Field(default_factory=list)
    section_priority: list[str] = Field(default_factory=list)
    evidence_map: dict[str, str] = Field(default_factory=dict)

    # New fast agent fields
    summary_direction: str = ""
    skills_to_emphasize: list[str] = Field(default_factory=list)
    projects_to_prioritize: list[str] = Field(default_factory=list)
    bullets_to_rewrite: list[str] = Field(default_factory=list)
    keywords_to_add_if_supported: list[str] = Field(default_factory=list)
    claims_to_avoid: list[str] = Field(default_factory=list)
    tone: str = "professional, concise, factual"


class ResumeVersion(BaseModel):
    version_id: str
    content: str
    created_at: str = Field(default_factory=now_iso)
    change_summary: list[Any] = Field(default_factory=list)
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


class FitAnalysisResult(BaseModel):
    jd_analysis: JDAnalysis
    cv_analysis: CVAnalysis
    tailoring_strategy: TailoringStrategy


class TailoredResumeSection(BaseModel):
    summary: str = ""
    skills: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    education: str = ""


class TailoredResumeDetails(BaseModel):
    content: str
    format: str = "markdown"
    sections: TailoredResumeSection


class ChangeSummaryItem(BaseModel):
    section: str = ""
    change: str = ""
    reason: str = ""
    evidence_source: str = ""


class HonestyReportDetails(BaseModel):
    status: Literal["pass", "needs_review"]
    risky_claims: list[str] = Field(default_factory=list)
    unsupported_claims: list[str] = Field(default_factory=list)
    safe_rewrite_suggestions: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class ATSScoreDetails(BaseModel):
    score: int
    matched_keywords: list[str] = Field(default_factory=list)
    missing_keywords: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    reasoning: str = ""


class ResumeRewriteReviewResult(BaseModel):
    tailored_resume: TailoredResumeDetails
    change_summary: list[ChangeSummaryItem] = Field(default_factory=list)
    honesty_report: HonestyReportDetails
    ats_score: ATSScoreDetails
