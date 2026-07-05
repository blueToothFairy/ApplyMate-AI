import React, { useState } from 'react';
import { parseMarkdown } from '../utils/markdownParser';

export default function CvReviewPanel({
  originalResumeText,
  tailoredResumeText,
  changeSummary,
  honestyReport,
  atsScoreDetails,
}) {
  const [activeTab, setActiveTab] = useState('tailored');

  if (!tailoredResumeText) {
    return (
      <div className="panel cv-review-panel empty">
        <h2>CV Tailoring Review</h2>
        <div className="empty-state-message">
          <p>No tailored CV generated yet.</p>
          <p className="subtext">Configure your intake details and click <strong>Generate Tailored CV</strong> to run the optimization workflow.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="panel cv-review-panel">
      <div className="panel-header-tabs">
        <h2>CV Tailoring Review</h2>
        <div className="tabs-navigation">
          <button
            className={`tab-btn ${activeTab === 'tailored' ? 'active' : ''}`}
            onClick={() => setActiveTab('tailored')}
          >
            Tailored CV
          </button>
          <button
            className={`tab-btn ${activeTab === 'original' ? 'active' : ''}`}
            onClick={() => setActiveTab('original')}
          >
            Original CV
          </button>
          <button
            className={`tab-btn ${activeTab === 'changes' ? 'active' : ''}`}
            onClick={() => setActiveTab('changes')}
          >
            Change Summary ({changeSummary?.length || 0})
          </button>
        </div>
      </div>

      {/* Tab Contents */}
      <div className="tab-viewport">
        {activeTab === 'tailored' && (
          <div className="document-container tailored-view">
            <div className="document-paper">
              {parseMarkdown(tailoredResumeText)}
            </div>
          </div>
        )}

        {activeTab === 'original' && (
          <div className="document-container original-view">
            <div className="document-paper raw-text">
              {originalResumeText ? (
                <pre className="original-cv-pre">{originalResumeText}</pre>
              ) : (
                <p className="no-text-message">Original CV text was not provided.</p>
              )}
            </div>
          </div>
        )}

        {activeTab === 'changes' && (
          <div className="changes-view">
            <h3>Modifications Audit</h3>
            {changeSummary && changeSummary.length > 0 ? (
              <ul className="changes-list">
                {changeSummary.map((item, idx) => (
                  <li key={idx} className="change-item">
                    <div className="change-header">
                      <span className="change-section-badge">{item.section || 'General'}</span>
                      {item.evidence_source && (
                        <span className="change-evidence">Source: <em>{item.evidence_source}</em></span>
                      )}
                    </div>
                    <p className="change-desc"><strong>Change:</strong> {item.change}</p>
                    {item.reason && (
                      <p className="change-reason"><strong>Reasoning:</strong> {item.reason}</p>
                    )}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="no-changes-message">No specific changes were documented by the tailoring agent.</p>
            )}
          </div>
        )}
      </div>

      {/* Honesty & ATS Analysis Sidebar/Footer */}
      <div className="cv-metadata-footer">
        {/* Honesty Report Details */}
        {honestyReport && (
          <div className="cv-metadata-section honesty-details">
            <h4>Honesty Analysis Details</h4>
            
            {honestyReport.risky_claims && honestyReport.risky_claims.length > 0 && (
              <div className="honesty-category risky">
                <h5>Risky Claims / Embellishments Flagged:</h5>
                <ul>
                  {honestyReport.risky_claims.map((claim, i) => (
                    <li key={i}>{claim}</li>
                  ))}
                </ul>
              </div>
            )}

            {honestyReport.unsupported_claims && honestyReport.unsupported_claims.length > 0 && (
              <div className="honesty-category unsupported">
                <h5>Unsupported Claims (Avoided or Flagged):</h5>
                <ul>
                  {honestyReport.unsupported_claims.map((claim, i) => (
                    <li key={i}>{claim}</li>
                  ))}
                </ul>
              </div>
            )}

            {honestyReport.safe_rewrite_suggestions && honestyReport.safe_rewrite_suggestions.length > 0 && (
              <div className="honesty-category suggestions">
                <h5>Safe Rewrite Suggestions Applied:</h5>
                <ul>
                  {honestyReport.safe_rewrite_suggestions.map((suggestion, i) => (
                    <li key={i}>{suggestion}</li>
                  ))}
                </ul>
              </div>
            )}

            {honestyReport.status === 'pass' && 
             (!honestyReport.risky_claims || honestyReport.risky_claims.length === 0) &&
             (!honestyReport.unsupported_claims || honestyReport.unsupported_claims.length === 0) && (
              <p className="honesty-clean-msg">✓ No honesty issues or embellishments detected. The tailored CV remains completely factual.</p>
            )}
          </div>
        )}

        {/* ATS Keywords analysis */}
        {atsScoreDetails && (
          <div className="cv-metadata-section keywords-details">
            <h4>Keyword & Coverage Analysis</h4>
            <div className="keywords-grid">
              <div className="keyword-column matched">
                <h5>Matched Keywords ({atsScoreDetails.matched_keywords?.length || 0})</h5>
                <div className="keyword-badges">
                  {atsScoreDetails.matched_keywords && atsScoreDetails.matched_keywords.length > 0 ? (
                    atsScoreDetails.matched_keywords.map((kw, i) => <span key={i} className="kw-badge match">{kw}</span>)
                  ) : (
                    <span className="no-kws">None</span>
                  )}
                </div>
              </div>

              <div className="keyword-column missing">
                <h5>Missing Keywords ({atsScoreDetails.missing_keywords?.length || 0})</h5>
                <div className="keyword-badges">
                  {atsScoreDetails.missing_keywords && atsScoreDetails.missing_keywords.length > 0 ? (
                    atsScoreDetails.missing_keywords.map((kw, i) => <span key={i} className="kw-badge miss">{kw}</span>)
                  ) : (
                    <span className="no-kws">None</span>
                  )}
                </div>
              </div>
            </div>

            {atsScoreDetails.reasoning && (
              <div className="ats-reasoning">
                <h5>ATS Analysis Reasoning</h5>
                <p>{atsScoreDetails.reasoning}</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
