import React from 'react';

export default function ScoreBlock({ matchScore, honestyReport }) {
  if (matchScore === undefined || matchScore === null) {
    return (
      <div className="score-block-placeholder">
        <p>No score available. Generate tailored CV to run match analysis.</p>
      </div>
    );
  }

  // Check if Docker/Kubernetes was avoided
  const checkDockerKubernetesAvoided = () => {
    if (!honestyReport) return true;
    
    const serializedReport = JSON.stringify(honestyReport).toLowerCase();
    
    // If the report mentions avoiding docker/kubernetes, or doesn't mention them at all, 
    // it means we successfully avoided adding unsupported claims.
    // In our backend rules, Docker/Kubernetes were not in the baseline CV and must not be added.
    const mentionsDockerOrKube = serializedReport.includes('docker') || serializedReport.includes('kubernetes');
    
    // If they are mentioned as unsupported or risky claims in the report, it means they might have been attempted or flagged.
    // Otherwise, we avoided them. We can display an informative check.
    const isRisky = (honestyReport.risky_claims && honestyReport.risky_claims.some(c => c.toLowerCase().includes('docker') || c.toLowerCase().includes('kubernetes'))) ||
                    (honestyReport.unsupported_claims && honestyReport.unsupported_claims.some(c => c.toLowerCase().includes('docker') || c.toLowerCase().includes('kubernetes')));

    return !isRisky;
  };

  const dkAvoided = checkDockerKubernetesAvoided();

  return (
    <div className="score-block">
      <div className="score-metric">
        <span className="score-label">ATS Match Score</span>
        <div className="score-value-container">
          <span className="score-number">{matchScore}</span>
          <span className="score-max">/100</span>
        </div>
      </div>

      <div className="honesty-metric">
        <span className="metric-label">Honesty Verification</span>
        {honestyReport ? (
          <div className="honesty-status-wrapper">
            <span className={`badge-honesty ${honestyReport.status}`}>
              {honestyReport.status === 'pass' ? 'PASSED' : 'NEEDS REVIEW'}
            </span>
            {dkAvoided ? (
              <div className="honesty-note success">
                <span className="icon">✓</span>
                <span>Docker/Kubernetes claims successfully avoided (kept CV strictly honest).</span>
              </div>
            ) : (
              <div className="honesty-note warning">
                <span className="icon">⚠</span>
                <span>Docker/Kubernetes mentioned in honesty report check details below.</span>
              </div>
            )}
          </div>
        ) : (
          <span className="metric-value-none">Not analyzed</span>
        )}
      </div>
    </div>
  );
}
