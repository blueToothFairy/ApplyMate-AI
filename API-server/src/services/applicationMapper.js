export function getSelectedResumeVersion(aiApplication) {
  if (!aiApplication) return null;
  const selectedId = aiApplication.selected_resume_version_id;
  return (aiApplication.tailored_resume_versions || []).find(v => v.version_id === selectedId) || null;
}

export function getEmailDraft(aiApplication) {
  return aiApplication?.email_draft || null;
}

export function toPublicSession(session) {
  return {
    id: session.id,
    ai_application_id: session.aiApplicationId,
    status: session.status,
    created_at: session.createdAt,
    updated_at: session.updatedAt,
    company_name: session.companyName,
    role_title: session.roleTitle,
    recipient_email: session.recipientEmail,
    upload: session.upload
      ? {
          original_name: session.upload.originalName,
          mime_type: session.upload.mimeType,
          size: session.upload.size,
        }
      : null,
    ai_application: session.aiApplication,
    review_bundle: session.reviewBundle,
    email_send_result: session.emailSendResult,
    audit_events: session.auditEvents,
  };
}
