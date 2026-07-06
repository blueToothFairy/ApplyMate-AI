import React, { useState, useEffect } from 'react';
import {
  checkBackendHealth,
  createApplication,
  generateApplication,
  draftEmail,
  approveApplication,
  rejectApplication,
  sendApplication,
  getApplication,
  exportPdf,
} from './api/applications';

import Header from './components/Header';
import IntakePanel from './components/IntakePanel';
import WorkflowControls from './components/WorkflowControls';
import CvReviewPanel from './components/CvReviewPanel';
import EmailDraftPanel from './components/EmailDraftPanel';
import StatusTimeline from './components/StatusTimeline';
import ErrorNotice from './components/ErrorNotice';
import ScoreBlock from './components/ScoreBlock';

const INITIAL_FORM = {
  companyName: '',
  roleTitle: '',
  recruiterName: '',
  recipientEmail: '',
  jobDescriptionText: '',
};

export default function App() {
  // Application Session States
  const [applicationId, setApplicationId] = useState(() => {
    return localStorage.getItem('applymate_app_id') || '';
  });
  const [application, setApplication] = useState(null);
  
  // Input Form States
  const [form, setForm] = useState(INITIAL_FORM);
  const [selectedFile, setSelectedFile] = useState(null);

  // Status & UI States
  const [loadingAction, setLoadingAction] = useState(null);
  const [error, setError] = useState(null);
  const [backendHealth, setBackendHealth] = useState('connecting');

  // Perform backend health check on mount and setup recurring checks
  useEffect(() => {
    const verifyHealth = async () => {
      try {
        await checkBackendHealth();
        setBackendHealth('online');
      } catch (err) {
        setBackendHealth('offline');
      }
    };

    verifyHealth();
    const interval = setInterval(verifyHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  // Fetch session details if applicationId is set (e.g., on reload)
  useEffect(() => {
    if (applicationId) {
      localStorage.setItem('applymate_app_id', applicationId);
      fetchSession(applicationId);
    } else {
      localStorage.removeItem('applymate_app_id');
      setApplication(null);
    }
  }, [applicationId]);

  const fetchSession = async (id) => {
    setLoadingAction('refresh');
    setError(null);
    try {
      const data = await getApplication(id);
      if (data && data.application) {
        setApplication(data.application);
        // Pre-fill form fields to show what was submitted if someone reloads
        setForm({
          companyName: data.application.company_name || '',
          roleTitle: data.application.role_title || '',
          recruiterName: data.application.ai_application?.cv_analysis?.candidate_name || '',
          recipientEmail: data.application.recipient_email || '',
          jobDescriptionText: data.application.job_description_text || '',
        });
      }
    } catch (err) {
      setError(err);
      // If session not found, clear it
      if (err.message && err.message.toLowerCase().includes('not found')) {
        handleClearSession();
      }
    } finally {
      setLoadingAction(null);
    }
  };

  const handleFormChange = (key, value) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const handleFileChange = (file) => {
    setError(null);
    if (!file) return;

    // Validate size (8MB max)
    if (file.size > 8 * 1024 * 1024) {
      setError('File is too large. Maximum supported CV size is 8MB.');
      return;
    }

    // Validate extension
    const ext = file.name.split('.').pop().toLowerCase();
    if (!['pdf', 'docx', 'txt', 'md'].includes(ext)) {
      setError('Unsupported file type. Please upload a PDF, DOCX, TXT, or MD file.');
      return;
    }

    setSelectedFile(file);
  };

  const handleUseSampleJd = () => {
    setForm({
      companyName: 'NovaTech Solutions Vietnam',
      roleTitle: 'Fullstack Engineer Intern',
      recruiterName: 'Nguyen Minh Anh',
      recipientEmail: 'safe-recipient@example.com',
      jobDescriptionText: `NovaTech Solutions Vietnam is looking for a Fullstack Engineer Intern to support the development of internal business web applications and customer-facing SaaS features.

Responsibilities:
- Build responsive frontend screens using React.js or Next.js.
- Develop and maintain RESTful APIs using Node.js and Express.js.
- Work with PostgreSQL or MongoDB for data storage and querying.
- Integrate frontend workflows with backend APIs.
- Improve API reliability, error handling, and performance.
- Use Git/GitHub in a collaborative development workflow.
- Communicate clearly with team members during sprint planning, implementation, and bug fixing.

Requirements:
- Basic to intermediate experience with JavaScript or TypeScript.
- Experience building web applications with React.js or Next.js.
- Understanding of Node.js, Express.js, and REST API design.
- Familiarity with relational or NoSQL databases such as PostgreSQL, MongoDB, or Supabase.
- Basic understanding of caching or performance optimization is a plus.
- Ability to write clear, maintainable code.
- Willingness to learn production engineering practices.

Nice to have:
- Redis experience.
- Cloud deployment experience.
- Docker or Kubernetes experience is a plus, but not required.

Honesty rule:
The candidate CV does not explicitly list Docker or Kubernetes. Do not add Docker or Kubernetes as candidate skills.`,
    });
  };

  const handleClearSession = () => {
    setApplicationId('');
    setApplication(null);
    setForm(INITIAL_FORM);
    setSelectedFile(null);
    setError(null);
    setLoadingAction(null);
  };

  // Submit Intake Form to API
  const handleCreateApplication = async () => {
    if (!selectedFile) {
      setError(' baseline CV file is required to create an application.');
      return;
    }
    if (!form.jobDescriptionText || !form.companyName || !form.roleTitle || !form.recipientEmail) {
      setError('Please fill in all required fields before creating the application.');
      return;
    }

    setLoadingAction('create');
    setError(null);

    const formData = new FormData();
    formData.append('cv', selectedFile);
    formData.append('job_description_text', form.jobDescriptionText);
    formData.append('company_name', form.companyName);
    formData.append('role_title', form.roleTitle);
    formData.append('recipient_email', form.recipientEmail);

    try {
      const data = await createApplication(formData);
      if (data && data.application) {
        setApplication(data.application);
        setApplicationId(data.application.id);
      }
    } catch (err) {
      setError(err);
    } finally {
      setLoadingAction(null);
    }
  };

  // AI Tailoring Execution
  const handleGenerateCv = async () => {
    setLoadingAction('generate');
    setError(null);
    try {
      const data = await generateApplication(applicationId);
      if (data && data.application) {
        setApplication(data.application);
      }
    } catch (err) {
      setError(err);
    } finally {
      setLoadingAction(null);
    }
  };

  // Compose email draft
  const handleDraftEmail = async () => {
    setLoadingAction('draft-email');
    setError(null);
    try {
      const data = await draftEmail(applicationId);
      if (data && data.application) {
        setApplication(data.application);
      }
    } catch (err) {
      setError(err);
    } finally {
      setLoadingAction(null);
    }
  };

  // Verify and Approve draft
  const handleApprove = async () => {
    setLoadingAction('approve');
    setError(null);
    try {
      const data = await approveApplication(applicationId);
      if (data && data.application) {
        setApplication(data.application);
      }
    } catch (err) {
      setError(err);
    } finally {
      setLoadingAction(null);
    }
  };

  // Verify and Reject draft
  const handleReject = async () => {
    setLoadingAction('reject');
    setError(null);
    try {
      const data = await rejectApplication(applicationId);
      if (data && data.application) {
        setApplication(data.application);
      }
    } catch (err) {
      setError(err);
    } finally {
      setLoadingAction(null);
    }
  };

  // Send CV and Email
  const handleSend = async () => {
    setLoadingAction('send');
    setError(null);
    try {
      const data = await sendApplication(applicationId);
      if (data && data.application) {
        setApplication(data.application);
      }
    } catch (err) {
      setError(err);
    } finally {
      setLoadingAction(null);
    }
  };

  // Export Tailored PDF via Blob
  const handleExportPdf = async () => {
    setLoadingAction('export-pdf');
    setError(null);
    try {
      const blob = await exportPdf(applicationId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `tailored_cv_${applicationId}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setError(err);
    } finally {
      setLoadingAction(null);
    }
  };

  // Manual session refresh
  const handleRefresh = async () => {
    if (applicationId) {
      await fetchSession(applicationId);
    }
  };

  // Helper selectors for application state
  const status = application ? application.status : 'no_application';
  const aiApp = application?.ai_application;
  
  // Selected resume version information
  const selectedResumeVersionId = aiApp?.selected_resume_version_id;
  const selectedResumeVersion = (aiApp?.tailored_resume_versions || []).find(
    (v) => v.version_id === selectedResumeVersionId
  ) || aiApp?.tailored_resume_versions?.[0];

  const tailoredResumeText = selectedResumeVersion?.content || '';
  const changeSummary = selectedResumeVersion?.change_summary || [];
  const honestyReport = selectedResumeVersion?.honesty_report;
  const matchScore = selectedResumeVersion?.match_score;
  const atsScoreDetails = selectedResumeVersion?.ats_score || application?.review_bundle?.ats_score;

  const emailDraft = aiApp?.email_draft || null;
  const approvalStatus = aiApp?.approval_status || 'not_requested';
  const approvalId = aiApp?.approval_id || '';
  
  const tailoredCvExists = (aiApp?.tailored_resume_versions || []).length > 0;
  const emailDraftExists = emailDraft !== null;
  const auditEvents = application?.audit_events || [];
  const emailSendResult = application?.email_send_result || null;

  return (
    <div className="app-container">
      {/* Header status bar */}
      <Header
        status={status}
        applicationId={applicationId}
        onClearSession={handleClearSession}
        backendHealth={backendHealth}
      />

      {/* Global Error Banner */}
      <ErrorNotice error={error} onDismiss={() => setError(null)} />

      {/* Main Workspace Workspace */}
      <main className="workspace-grid">
        {/* Left Column: Form & Controller inputs */}
        <div className="workspace-left-col">
          <IntakePanel
            form={form}
            selectedFile={selectedFile}
            onFormChange={handleFormChange}
            onFileChange={handleFileChange}
            onUseSampleJd={handleUseSampleJd}
            onSubmit={handleCreateApplication}
            loading={loadingAction === 'create'}
            applicationId={applicationId}
          />

          <WorkflowControls
            applicationId={applicationId}
            status={status}
            tailoredCvExists={tailoredCvExists}
            emailDraftExists={emailDraftExists}
            approvalStatus={approvalStatus}
            loadingAction={loadingAction}
            onGenerateCv={handleGenerateCv}
            onDraftEmail={handleDraftEmail}
            onApprove={handleApprove}
            onReject={handleReject}
            onSend={handleSend}
            onExportPdf={handleExportPdf}
            onRefresh={handleRefresh}
            emailSendResult={emailSendResult}
          />
        </div>

        {/* Right Area: Large editor sheets / analysis reports */}
        <div className="workspace-right-col">
          {/* match status & honesty meters */}
          <ScoreBlock
            matchScore={matchScore}
            honestyReport={honestyReport}
          />

          {/* Tailored CV sheet before/after toggles */}
          <CvReviewPanel
            originalResumeText={application?.resumeText || ''}
            tailoredResumeText={tailoredResumeText}
            changeSummary={changeSummary}
            honestyReport={honestyReport}
            atsScoreDetails={atsScoreDetails}
          />

          {/* Email compose sheet */}
          <EmailDraftPanel
            emailDraft={emailDraft}
            approvalStatus={approvalStatus}
            approvalId={approvalId}
          />

          {/* Audit events feed */}
          <StatusTimeline auditEvents={auditEvents} />
        </div>
      </main>
    </div>
  );
}
