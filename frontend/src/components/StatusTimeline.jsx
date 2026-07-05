import React from 'react';
import { formatDate } from '../utils/formatters';

export default function StatusTimeline({ auditEvents }) {
  if (!auditEvents || auditEvents.length === 0) {
    return (
      <div className="panel timeline-panel empty">
        <h2>Audit Timeline</h2>
        <p className="no-events">No audit logs available for this session.</p>
      </div>
    );
  }

  // Format action name for readability
  const formatActionName = (action) => {
    return action
      .replace(/^api\./, '')
      .replace(/\./g, ' ')
      .replace(/_/g, ' ')
      .replace(/\b\w/g, c => c.toUpperCase());
  };

  return (
    <div className="panel timeline-panel">
      <h2>Audit Timeline</h2>
      <p className="panel-instruction">Internal event log for tracking agent executions and validation results.</p>
      
      <div className="timeline-container">
        {auditEvents.map((evt, idx) => (
          <div key={evt.event_id || idx} className="timeline-item">
            <div className="timeline-marker"></div>
            <div className="timeline-content">
              <div className="timeline-header">
                <span className="timeline-action">{formatActionName(evt.action || 'Event')}</span>
                <span className="timeline-time">{formatDate(evt.created_at || evt.timestamp)}</span>
              </div>
              {evt.detail && Object.keys(evt.detail).length > 0 && (
                <div className="timeline-details">
                  <pre>{JSON.stringify(evt.detail, null, 2)}</pre>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
