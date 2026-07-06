import React from 'react';

export default function EmailDraftPanel({ emailDraft, approvalStatus, approvalId }) {
  if (!emailDraft) {
    return (
      <div className="panel email-draft-panel empty">
        <h2>Application Email Draft</h2>
        <div className="empty-state-message">
          <p>No email draft has been generated yet.</p>
          <p className="subtext">Generate your tailored CV first, then click <strong>Draft Email</strong> in the control panel to write your introductory email.</p>
        </div>
      </div>
    );
  }

  const getApprovalStatusBanner = () => {
    switch (approvalStatus) {
      case 'approved':
        return {
          text: '✓ Email draft is approved. Ready for distribution.',
          class: 'approval-banner approved',
        };
      case 'rejected':
        return {
          text: '⚠ Email draft is rejected. Please review feedback or regenerate.',
          class: 'approval-banner rejected',
        };
      case 'pending':
      case 'pending_approval':
        return {
          text: '⏳ Email draft is pending review. Approve this draft using the control panel to enable sending.',
          class: 'approval-banner pending',
        };
      default:
        return {
          text: 'Draft created. Submit for approval before distribution.',
          class: 'approval-banner info',
        };
    }
  };

  const banner = getApprovalStatusBanner();

  return (
    <div className="panel email-draft-panel">
      <h2>Application Email Draft</h2>

      <div className={banner.class}>
        <span>{banner.text}</span>
        {approvalId && (
          <span className="approval-id-sub">Approval Token: <code>{approvalId}</code></span>
        )}
      </div>

      <div className="email-envelope">
        <div className="email-header-fields">
          <div className="email-field">
            <span className="field-label">To:</span>
            <span className="field-value">{emailDraft.to || '(Empty Recipient)'}</span>
          </div>
          <hr className="envelope-divider" />
          <div className="email-field">
            <span className="field-label">Subject:</span>
            <span className="field-value subject-line">{emailDraft.subject || '(Empty Subject)'}</span>
          </div>
        </div>
        <div className="email-body-view">
          {emailDraft.body ? (
            <pre className="email-body-pre">{emailDraft.body}</pre>
          ) : (
            <p className="no-body-placeholder">Draft body is empty.</p>
          )}
        </div>
      </div>

      <div className="email-envelope-info">
        <small>Note: The email contains placeholder variables parsed by the EmailComposerAgent. Once approved and sent, the tailored CV is attached automatically as a PDF file.</small>
      </div>
    </div>
  );
}
