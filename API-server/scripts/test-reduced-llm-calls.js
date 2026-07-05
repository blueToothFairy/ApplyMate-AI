import axios from 'axios';

const PORT = process.env.PORT || 3001;
const BASE_URL = `http://127.0.0.1:${PORT}/api`;
const API_KEY = process.env.API_KEY || 'socrates';

const client = axios.create({
  headers: {
    'x-api-key': API_KEY,
    'Content-Type': 'application/json'
  }
});

function getSelectedResumeVersion(aiApplication) {
  if (!aiApplication) return null;
  const selectedId = aiApplication.selected_resume_version_id;
  return (aiApplication.tailored_resume_versions || []).find(v => v.version_id === selectedId) || null;
}

async function runTests() {
  console.log('=== Running API Server Integration Tests ===');
  
  try {
    // 1. Create application
    console.log('1. POST /api/applications ...');
    const createRes = await client.post(`${BASE_URL}/applications`, {
      resume_text: 'Phan Quoc Thinh. Experience: Software Developer at ApplyMate. Skills: Node.js, SQL, REST APIs, Git. Projects: Workshop Platform.',
      job_description_text: 'Backend Intern. Requirements: Node.js, SQL, REST API, Git. Docker is a nice to have.',
      company_name: 'Google DeepMind',
      role_title: 'Backend Intern',
      recipient_email: 'recruiter@deepmind.com',
    });
    
    const app = createRes.data.application;
    const appId = app.id;
    console.log(`   Created Application ID: ${appId}`);
    
    // 2. Generate Tailored CV
    console.log('2. POST /api/applications/:id/generate ...');
    const genRes = await client.post(`${BASE_URL}/applications/${appId}/generate`);
    
    const genApp = genRes.data.application;
    const aiApp = genApp.ai_application;
    console.log(`   AI Application ID: ${aiApp.application_id}`);
    
    const resumeVersion = getSelectedResumeVersion(aiApp);
    console.log('   Checking generated tailored resume version:', resumeVersion ? 'found' : 'missing');
    
    if (!resumeVersion) {
      throw new Error('No selected resume version found after generate.');
    }
    
    console.log('   Tailored resume content snippet:', resumeVersion.content.substring(0, 100).replace(/\n/g, ' '));
    console.log('   Honesty status:', resumeVersion.honesty_report.status);
    console.log('   Match score:', resumeVersion.match_score);
    console.log('   Change summary length:', resumeVersion.change_summary.length);
    
    if (!resumeVersion.content) throw new Error('Resume content is empty.');
    if (!resumeVersion.honesty_report) throw new Error('Honesty report is missing.');
    if (typeof resumeVersion.match_score !== 'number') throw new Error('Match score is not a number.');
    if (!resumeVersion.change_summary) throw new Error('Change summary is missing.');
    
    console.log('   Checking that email draft is NOT generated yet...');
    if (aiApp.email_draft) {
      throw new Error('Email draft should NOT be generated during /generate flow.');
    }
    console.log('   Email draft is empty (correct)');
    
    // 3. Draft Email
    console.log('3. POST /api/applications/:id/draft-email ...');
    const draftRes = await client.post(`${BASE_URL}/applications/${appId}/draft-email`, {
      tone: 'professional, concise',
    });
    
    const draftApp = draftRes.data.application;
    const draftAiApp = draftApp.ai_application;
    console.log('   Email draft details:', draftAiApp.email_draft ? 'found' : 'missing');
    
    if (!draftAiApp.email_draft) {
      throw new Error('Email draft was not generated.');
    }
    console.log('   Subject:', draftAiApp.email_draft.subject);
    console.log('   Body snippet:', draftAiApp.email_draft.body.substring(0, 100).replace(/\n/g, ' '));
    console.log('   Approval Status:', draftAiApp.approval_status);
    console.log('   Approval ID:', draftAiApp.approval_id);
    
    if (!draftAiApp.email_draft.subject) throw new Error('Email subject is empty.');
    if (!draftAiApp.email_draft.body) throw new Error('Email body is empty.');
    if (draftAiApp.approval_status !== 'pending') {
      throw new Error(`Expected approval status 'pending', got '${draftAiApp.approval_status}'`);
    }
    if (!draftAiApp.approval_id) throw new Error('Approval ID is missing.');
    
    // 4. Approve Application
    console.log('4. POST /api/applications/:id/approve ...');
    const approveRes = await client.post(`${BASE_URL}/applications/${appId}/approve`, {
      approval_id: draftAiApp.approval_id,
      feedback: 'Looks good!',
    });
    
    const approvedApp = approveRes.data.application;
    console.log('   Approved status in API-server:', approvedApp.status);
    console.log('   Approval Status in AI-application:', approveRes.data.ai_application.approval_status);
    
    if (approvedApp.status !== 'approved') {
      throw new Error(`Expected status 'approved', got '${approvedApp.status}'`);
    }
    if (approveRes.data.ai_application.approval_status !== 'approved') {
      throw new Error(`Expected approval_status 'approved', got '${approveRes.data.ai_application.approval_status}'`);
    }
    
    // 5. Send Application
    console.log('5. POST /api/applications/:id/send ...');
    const sendRes = await client.post(`${BASE_URL}/applications/${appId}/send`);
    console.log('   Send result:', sendRes.data.send_result);
    
    if (sendRes.data.application.status !== 'sent') {
      throw new Error(`Expected status 'sent', got '${sendRes.data.application.status}'`);
    }
    console.log('   Send policy allowed:', sendRes.data.validation.allowed);
    console.log('   Send mode:', sendRes.data.send_result.mode);
    
    console.log('=== All Integration Tests Passed Successfully! ===');
  } catch (err) {
    console.error('Test run failed:', err.response ? err.response.data : err.message);
    process.exit(1);
  }
}

runTests();
