import { aiClient } from '../services/aiClient.js';
import { ensureResumeText } from '../services/documentService.js';
import { renderResumePdfBuffer } from '../services/pdfService.js';
import { sendApplicationEmail } from '../services/emailService.js';
import { getEmailDraft, getSelectedResumeVersion, toPublicSession } from '../services/applicationMapper.js';
import { sessionStore } from '../stores/sessionStore.js';
import { badRequest, conflict } from '../utils/httpErrors.js';
import { normalizeString, hasUnresolvedPlaceholder } from '../utils/sanitize.js';
import { parseBody } from '../validators/validateRequest.js';
import {
  createApplicationSchema,
  reviseSchema,
  draftEmailSchema,
  approvalSchema,
  rejectSchema,
} from '../validators/applicationSchemas.js';

export async function health(_req, res) {
  let ai = null;
  try {
    ai = await aiClient.health();
  } catch (err) {
    ai = { status: 'unreachable', message: err.message };
  }
  res.json({ status: 'ok', service: 'ApplyMate API Server', ai_server: ai });
}

export async function listApplications(_req, res) {
  res.json({ applications: sessionStore.list().map(toPublicSession) });
}

export async function createApplication(req, res) {
  const parsed = parseBody(createApplicationSchema, req.body);
  const jdText = normalizeString(parsed.job_description_text);

  // Boundary rule: the API-server does not parse CV files. It only receives the
  // upload, base64-encodes it in aiClient.parseDocument(), and forwards it to
  // the FastAPI AI-server. The AI-server is the document parsing owner.
  const resumeFile = getUploadedResumeFile(req);
  const parsedUpload = resumeFile ? await aiClient.parseDocument(resumeFile, 'resume') : null;
  const resumeText = ensureResumeText(parsedUpload?.text || parsed.resume_text);

  const session = sessionStore.create({
    resumeText,
    jobDescriptionText: jdText,
    companyName: parsed.company_name,
    roleTitle: parsed.role_title,
    recipientEmail: parsed.recipient_email || '',
    upload: resumeFile
      ? {
          path: resumeFile.path,
          originalName: resumeFile.originalname,
          mimeType: resumeFile.mimetype,
          size: resumeFile.size,
          parsedBy: 'AI-server',
          parserEndpoint: '/ai/documents/parse',
          extractedCharacters: parsedUpload?.text?.length || 0,
          promptInjectionHits: parsedUpload?.prompt_injection_hits || [],
        }
      : null,
  });

  sessionStore.addAudit(session.id, 'api.document.forwarded_to_ai_server', {
    hasUpload: Boolean(resumeFile),
    parserEndpoint: resumeFile ? '/ai/documents/parse' : null,
    extractedCharacters: parsedUpload?.text?.length || 0,
    promptInjectionHits: parsedUpload?.prompt_injection_hits || [],
  });

  res.status(201).json({ application: toPublicSession(session), parsed_document: parsedUpload });
}

export async function getApplication(req, res) {
  const session = sessionStore.get(req.params.id);
  res.json({ application: toPublicSession(session) });
}

export async function parseApplication(req, res) {
  const session = sessionStore.get(req.params.id);
  const aiResult = await aiClient.parse({
    resume_text: session.resumeText,
    job_description_text: session.jobDescriptionText,
  });
  sessionStore.update(session.id, { status: 'parsed' });
  sessionStore.addAudit(session.id, 'api.application.parsed', { promptInjectionHits: aiResult.prompt_injection_hits || [] });
  res.json({ parse_result: aiResult, application: toPublicSession(sessionStore.get(session.id)) });
}

export async function generateTailoredCv(req, res) {
  const session = sessionStore.get(req.params.id);
  const result = await aiClient.generateTailoredCv({
    resume_text: session.resumeText,
    job_description_text: session.jobDescriptionText,
    company_name: session.companyName,
    role_title: session.roleTitle,
    recipient_email: session.recipientEmail || null,
  });

  const aiApplication = result.application;
  const updated = sessionStore.update(session.id, {
    aiApplicationId: aiApplication.application_id,
    aiApplication,
    reviewBundle: result.review_bundle,
    status: aiApplication.status || 'generated',
  });
  sessionStore.addAudit(session.id, 'api.application.generated', {
    aiApplicationId: aiApplication.application_id,
    approvalId: aiApplication.approval_id,
    llmEnabled: true,
  });

  res.json({ application: toPublicSession(updated), ai_response: result });
}

export async function reviseApplication(req, res) {
  const body = parseBody(reviseSchema, req.body);
  const session = requireAiApplication(req.params.id);
  const result = await aiClient.revise(session.aiApplicationId, body.feedback, body.target);
  const updated = sessionStore.update(session.id, {
    aiApplication: result.application,
    reviewBundle: result.review_bundle,
    status: result.application.status || 'revised',
  });
  sessionStore.addAudit(session.id, 'api.application.revised', { target: body.target, feedback: body.feedback });
  res.json({ application: toPublicSession(updated), ai_response: result });
}

export async function draftEmail(req, res) {
  const body = parseBody(draftEmailSchema, req.body);
  const session = requireAiApplication(req.params.id);
  const result = await aiClient.draftEmail(session.aiApplicationId, body.tone);
  const updated = sessionStore.update(session.id, {
    aiApplication: result.application,
    reviewBundle: result.review_bundle,
    status: result.application.status || 'email_drafted',
  });
  sessionStore.addAudit(session.id, 'api.email.drafted', { tone: body.tone });
  res.json({ application: toPublicSession(updated), ai_response: result });
}

export async function requestApproval(req, res) {
  const session = requireAiApplication(req.params.id);
  const result = await aiClient.requestApproval(session.aiApplicationId);
  const aiApplication = await aiClient.getApplication(session.aiApplicationId);
  const updated = sessionStore.update(session.id, {
    aiApplication,
    reviewBundle: result,
    status: aiApplication.status || 'pending_approval',
  });
  sessionStore.addAudit(session.id, 'api.approval.requested', { approvalId: aiApplication.approval_id });
  res.json({ application: toPublicSession(updated), review_bundle: result });
}

export async function approveApplication(req, res) {
  const body = parseBody(approvalSchema, req.body);
  const session = requireAiApplication(req.params.id);
  const approvalId = body.approval_id || session.aiApplication?.approval_id;

  // /ai/approval/mark returns a review bundle, not a nested WorkflowResponse.
  // The AI-server application record is the source of truth for approval_status,
  // approval_id, selected CV version, and email draft state, so always refresh it
  // after marking approval. This prevents the API session response from showing
  // stale `pending` approval status after the user approves.
  const reviewBundle = await aiClient.markApproval(session.aiApplicationId, 'approved', approvalId, body.feedback || '');
  const aiApplication = await aiClient.getApplication(session.aiApplicationId);

  const updated = sessionStore.update(session.id, {
    aiApplication,
    reviewBundle,
    status: aiApplication.status || 'approved',
  });
  sessionStore.addAudit(session.id, 'api.approval.approved', {
    approvalId: aiApplication.approval_id || approvalId,
    approvalStatus: aiApplication.approval_status,
  });
  res.json({
    application: toPublicSession(updated),
    review_bundle: reviewBundle,
    ai_application: aiApplication,
  });
}

export async function rejectApplication(req, res) {
  const body = parseBody(rejectSchema, req.body);
  const session = requireAiApplication(req.params.id);
  const approvalId = body.approval_id || session.aiApplication?.approval_id;

  // Same contract as approval: mark first, then refresh the canonical
  // AI-server application state to avoid returning stale local session data.
  const reviewBundle = await aiClient.markApproval(session.aiApplicationId, 'rejected', approvalId, body.feedback || '');
  const aiApplication = await aiClient.getApplication(session.aiApplicationId);

  const updated = sessionStore.update(session.id, {
    aiApplication,
    reviewBundle,
    status: aiApplication.status || 'rejected',
  });
  sessionStore.addAudit(session.id, 'api.approval.rejected', {
    approvalId: aiApplication.approval_id || approvalId,
    approvalStatus: aiApplication.approval_status,
    feedback: body.feedback || '',
  });
  res.json({
    application: toPublicSession(updated),
    review_bundle: reviewBundle,
    ai_application: aiApplication,
  });
}

export async function sendApplication(req, res) {
  const session = requireAiApplication(req.params.id);

  // Refresh the source-of-truth AI session before validating and sending.
  const aiApplication = await aiClient.getApplication(session.aiApplicationId);
  sessionStore.update(session.id, { aiApplication, status: aiApplication.status || session.status });

  const emailDraft = getEmailDraft(aiApplication);
  const selectedVersion = getSelectedResumeVersion(aiApplication);
  if (!emailDraft) throw conflict('No email draft exists. Draft the email before sending.');
  if (!selectedVersion) throw conflict('No selected tailored CV version exists.');
  if (!aiApplication.approval_id || aiApplication.approval_status !== 'approved') {
    throw conflict('Application must be explicitly approved before sending.');
  }
  if (hasUnresolvedPlaceholder(emailDraft.subject) || hasUnresolvedPlaceholder(emailDraft.body)) {
    throw conflict('Email contains unresolved placeholders. Please revise it before sending.');
  }

  const validation = await aiClient.validateSend({
    application_id: session.aiApplicationId,
    approval_id: aiApplication.approval_id,
    recipient_email: emailDraft.to,
    email_subject: emailDraft.subject,
    email_body: emailDraft.body,
    attachment_version_id: emailDraft.attachment_version_id,
  });

  if (!validation.allowed) {
    sessionStore.addAudit(session.id, 'api.send_policy.rejected', { reasons: validation.reasons });
    throw conflict('AI send policy validation failed.', validation.reasons);
  }

  let attachment;
  try {
    const buffer = await renderResumePdfBuffer({
      title: `${aiApplication.role_title || 'Tailored'} CV`,
      resumeText: selectedVersion.content,
    });
    attachment = {
      buffer,
      filename: `tailored_cv_${session.aiApplicationId}.pdf`,
      contentType: 'application/pdf',
    };
  } catch (err) {
    // Fallback keeps the send flow usable during demos even if PDF generation fails.
    attachment = {
      buffer: Buffer.from(selectedVersion.content, 'utf8'),
      filename: `tailored_cv_${session.aiApplicationId}.md`,
      contentType: 'text/markdown; charset=utf-8',
      exportFallbackReason: err.message,
    };
  }

  const sendResult = await sendApplicationEmail({
    to: emailDraft.to,
    subject: emailDraft.subject,
    body: emailDraft.body,
    attachment,
  });

  const updated = sessionStore.update(session.id, {
    emailSendResult: sendResult,
    status: 'sent',
  });
  sessionStore.addAudit(session.id, 'api.email.sent', {
    mode: sendResult.mode,
    messageId: sendResult.messageId,
    to: emailDraft.to,
    attachmentFilename: attachment.filename,
  });

  res.json({
    application: toPublicSession(updated),
    validation,
    send_result: sendResult,
  });
}


export async function exportPdf(req, res) {
  const session = requireAiApplication(req.params.id);
  const aiApplication = session.aiApplication || (await aiClient.getApplication(session.aiApplicationId));
  const selectedVersion = getSelectedResumeVersion(aiApplication);
  if (!selectedVersion) throw conflict('No selected tailored CV version exists.');
  const buffer = await renderResumePdfBuffer({
    title: `${aiApplication.role_title || 'Tailored'} CV`,
    resumeText: selectedVersion.content,
  });
  const filename = `tailored_cv_${session.aiApplicationId}.pdf`;
  res.setHeader('Content-Type', 'application/pdf');
  res.setHeader('Content-Disposition', `attachment; filename="${filename}"`);
  res.send(buffer);
}


function getUploadedResumeFile(req) {
  if (req.file) return req.file;
  if (req.files?.cv?.[0]) return req.files.cv[0];
  if (req.files?.resume_file?.[0]) return req.files.resume_file[0];
  return null;
}

function requireAiApplication(localId) {
  const session = sessionStore.get(localId);
  if (!session.aiApplicationId) {
    throw conflict('This application has not been generated by the AI Server yet. Call /generate first.');
  }
  return session;
}
