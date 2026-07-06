import React from 'react';

export default function WorkflowControls({
  applicationId,
  status,
  tailoredCvExists,
  emailDraftExists,
  approvalStatus,
  loadingAction,
  onGenerateCv,
  onDraftEmail,
  onApprove,
  onReject,
  onSend,
  onExportPdf,
  onRefresh,
  emailSendResult,
}) {
  const isAnyLoading = !!loadingAction;

  // Disabled logic
  const isGenerateDisabled = !applicationId || isAnyLoading;
  const isDraftDisabled = !tailoredCvExists || isAnyLoading;
  const isApproveRejectDisabled = !emailDraftExists || isAnyLoading;
  const isSendDisabled = approvalStatus !== 'approved' || status === 'sent' || isAnyLoading;
  const isExportDisabled = !tailoredCvExists || isAnyLoading;
  const isRefreshDisabled = !applicationId || isAnyLoading;

  return (
    <div className="panel workflow-controls-panel">
      <h2>Workflow Control Panel</h2>
      <p className="panel-instruction">Control application generation, approval, and distribution state.</p>

      <div className="workflow-grid">
        {/* Core AI Actions */}
        <div className="workflow-section">
          <h3>Core Steps</h3>
          <div className="button-group-vertical">
            <button
              className="btn-action-primary"
              onClick={onGenerateCv}
              disabled={isGenerateDisabled}
            >
              {loadingAction === 'generate' ? 'Generating CV...' : '1. Generate Tailored CV'}
            </button>
            <button
              className="btn-action-primary"
              onClick={onDraftEmail}
              disabled={isDraftDisabled}
            >
              {loadingAction === 'draft-email' ? 'Drafting Email...' : '2. Draft Email'}
            </button>
          </div>
        </div>

        {/* Approval Actions */}
        <div className="workflow-section">
          <h3>Verification</h3>
          <div className="button-group-row">
            <button
              className="btn-approve"
              onClick={onApprove}
              disabled={isApproveRejectDisabled}
            >
              {loadingAction === 'approve' ? 'Approving...' : 'Approve Draft'}
            </button>
            <button
              className="btn-reject"
              onClick={onReject}
              disabled={isApproveRejectDisabled}
            >
              {loadingAction === 'reject' ? 'Rejecting...' : 'Reject Draft'}
            </button>
          </div>
        </div>

        {/* Send Actions */}
        <div className="workflow-section">
          <h3>Distribution</h3>
          <button
            className="btn-send"
            onClick={onSend}
            disabled={isSendDisabled}
          >
            {loadingAction === 'send' ? 'Sending...' : 'Send Application'}
          </button>
          {emailSendResult && (
            <div className="email-send-status">
              <span className={`badge-send-mode ${emailSendResult.mode}`}>
                {emailSendResult.mode === 'mock' ? 'MOCK MODE ENABLED' : 'REAL SMTP SENT'}
              </span>
              <small className="message-id" title={emailSendResult.messageId || emailSendResult.message_id}>
                ID: {emailSendResult.messageId || emailSendResult.message_id || 'N/A'}
              </small>
            </div>
          )}
        </div>

        {/* Utilities & Exports */}
        <div className="workflow-section">
          <h3>Workspace Utilities</h3>
          <div className="button-group-row">
            <button
              className="btn-utility"
              onClick={onExportPdf}
              disabled={isExportDisabled}
            >
              {loadingAction === 'export-pdf' ? 'Downloading...' : 'Export PDF'}
            </button>
          </div>
          <button
            className="btn-refresh"
            onClick={onRefresh}
            disabled={isRefreshDisabled}
          >
            {loadingAction === 'refresh' ? 'Refreshing...' : 'Refresh Status'}
          </button>
        </div>
      </div>
    </div>
  );
}
