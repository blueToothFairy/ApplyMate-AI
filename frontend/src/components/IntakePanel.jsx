import React, { useRef } from 'react';
import { formatBytes } from '../utils/formatters';

export default function IntakePanel({
  form,
  selectedFile,
  onFormChange,
  onFileChange,
  onUseSampleJd,
  onSubmit,
  loading,
  applicationId,
}) {
  const fileInputRef = useRef(null);

  const handleJdChange = (e) => {
    onFormChange('jobDescriptionText', e.target.value);
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      onFileChange(e.target.files[0]);
    }
  };

  const jdLength = form.jobDescriptionText ? form.jobDescriptionText.length : 0;

  return (
    <div className="panel intake-panel">
      <h2>Intake & Job Requirements</h2>
      <p className="panel-instruction">Upload your baseline CV and target job details to start tailoring.</p>

      <form onSubmit={(e) => { e.preventDefault(); onSubmit(); }} className="intake-form">
        
        {/* CV File Upload */}
        <div className="form-group file-upload-group">
          <label htmlFor="cv-upload" className="form-label required">Baseline CV File</label>
          <div className="file-dropzone">
            <input
              type="file"
              id="cv-upload"
              ref={fileInputRef}
              accept=".pdf,.docx,.txt,.md"
              onChange={handleFileChange}
              disabled={loading || !!applicationId}
              className="hidden-file-input"
            />
            <button
              type="button"
              className="btn-secondary file-select-trigger"
              onClick={() => fileInputRef.current?.click()}
              disabled={loading || !!applicationId}
            >
              Choose CV File
            </button>
            <span className="file-format-info">Accepts PDF, DOCX, TXT, MD (Max 8MB)</span>
          </div>
          
          {selectedFile && (
            <div className="file-meta-info">
              <span className="file-name" title={selectedFile.name}>{selectedFile.name}</span>
              <span className="file-size">({formatBytes(selectedFile.size)})</span>
            </div>
          )}
        </div>

        {/* Company & Role info */}
        <div className="form-row">
          <div className="form-group">
            <label htmlFor="company_name" className="form-label required">Company Name</label>
            <input
              type="text"
              id="company_name"
              placeholder="e.g., NovaTech Solutions"
              value={form.companyName}
              onChange={(e) => onFormChange('companyName', e.target.value)}
              disabled={loading || !!applicationId}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="role_title" className="form-label required">Role Title</label>
            <input
              type="text"
              id="role_title"
              placeholder="e.g., Software Intern"
              value={form.roleTitle}
              onChange={(e) => onFormChange('roleTitle', e.target.value)}
              disabled={loading || !!applicationId}
              required
            />
          </div>
        </div>

        {/* Recruiter & Recipient info */}
        <div className="form-row">
          <div className="form-group">
            <label htmlFor="recruiter_name" className="form-label">Recruiter Name</label>
            <input
              type="text"
              id="recruiter_name"
              placeholder="e.g., Nguyen Minh Anh"
              value={form.recruiterName}
              onChange={(e) => onFormChange('recruiterName', e.target.value)}
              disabled={loading || !!applicationId}
            />
          </div>
          <div className="form-group">
            <label htmlFor="recipient_email" className="form-label required">Recipient Email</label>
            <input
              type="email"
              id="recipient_email"
              placeholder="e.g., HR@company.com"
              value={form.recipientEmail}
              onChange={(e) => onFormChange('recipientEmail', e.target.value)}
              disabled={loading || !!applicationId}
              required
            />
          </div>
        </div>

        {/* Job Description Textarea */}
        <div className="form-group">
          <div className="label-with-counter">
            <label htmlFor="job_description" className="form-label required">Job Description</label>
            <span className="char-counter">{jdLength} characters</span>
          </div>
          <textarea
            id="job_description"
            rows="10"
            placeholder="Paste complete target job description here..."
            value={form.jobDescriptionText}
            onChange={handleJdChange}
            disabled={loading || !!applicationId}
            required
          ></textarea>
        </div>

        {/* Action button row */}
        <div className="intake-actions">
          <button
            type="button"
            className="btn-secondary"
            onClick={onUseSampleJd}
            disabled={loading || !!applicationId}
          >
            Use sample JD
          </button>
          
          <button
            type="submit"
            className="btn-primary"
            disabled={loading || !!applicationId || !selectedFile || !form.jobDescriptionText || !form.companyName || !form.roleTitle || !form.recipientEmail}
          >
            {loading ? 'Creating...' : 'Create Application'}
          </button>
        </div>
      </form>
      
      {applicationId && (
        <div className="intake-lock-banner">
          <span>Application locked. Clear session to start a new application.</span>
        </div>
      )}
    </div>
  );
}
