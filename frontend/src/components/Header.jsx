import React from 'react';

export default function Header({ status, applicationId, onClearSession, backendHealth }) {
  const getStatusLabel = () => {
    switch (status) {
      case 'created':
        return { label: 'Intake Created', class: 'status-created' };
      case 'parsed':
        return { label: 'CV Parsed', class: 'status-parsed' };
      case 'generated':
        return { label: 'CV Tailored', class: 'status-generated' };
      case 'email_drafted':
        return { label: 'Email Drafted', class: 'status-drafted' };
      case 'pending_approval':
        return { label: 'Pending Approval', class: 'status-pending' };
      case 'approved':
        return { label: 'Approved', class: 'status-approved' };
      case 'rejected':
        return { label: 'Rejected', class: 'status-rejected' };
      case 'sent':
        return { label: 'Sent', class: 'status-sent' };
      case 'error':
        return { label: 'Error State', class: 'status-error' };
      default:
        return { label: 'No Active Application', class: 'status-none' };
    }
  };

  const statusInfo = getStatusLabel();

  return (
    <header className="app-header">
      <div className="header-brand">
        <h1>ApplyMate AI</h1>
        <p className="header-subtitle">CV tailoring and application review workspace</p>
      </div>

      <div className="header-status-bar">
        <div className="status-indicator">
          <span className="status-dot-label">API Server:</span>
          <span className={`status-dot ${backendHealth}`}></span>
          <span className="health-text">{backendHealth.toUpperCase()}</span>
        </div>

        {applicationId && (
          <div className="app-id-display">
            <span className="label">ID:</span>
            <span className="value" title={applicationId}>{applicationId.substring(0, 8)}...</span>
          </div>
        )}

        <div className={`app-status-badge ${statusInfo.class}`}>
          {statusInfo.label}
        </div>

        {applicationId && (
          <button className="btn-clear-session" onClick={onClearSession} title="Reset and start new session">
            Clear current session
          </button>
        )}
      </div>
    </header>
  );
}
