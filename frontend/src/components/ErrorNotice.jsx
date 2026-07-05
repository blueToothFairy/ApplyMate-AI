import React from 'react';

export default function ErrorNotice({ error, onDismiss }) {
  if (!error) return null;

  const errorMessage = typeof error === 'string' ? error : error.message || 'An unexpected error occurred';
  const errorDetails = typeof error === 'object' && error.details ? error.details : null;

  return (
    <div className="error-notice-card">
      <div className="error-header">
        <div className="error-title-wrapper">
          <span className="error-icon">⚠</span>
          <h4>Action Request Failed</h4>
        </div>
        {onDismiss && (
          <button className="error-dismiss-btn" onClick={onDismiss} title="Dismiss notice">
            ✕
          </button>
        )}
      </div>
      <div className="error-body">
        <p className="error-message-text">{errorMessage}</p>
        
        {errorDetails && (
          <div className="error-details-box">
            <h5>Technical details:</h5>
            <pre>{typeof errorDetails === 'object' ? JSON.stringify(errorDetails, null, 2) : errorDetails}</pre>
          </div>
        )}
      </div>
    </div>
  );
}
