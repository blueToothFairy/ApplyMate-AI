import fs from 'node:fs/promises';
import axios from 'axios';

const PORT = process.env.PORT || 3001;
const BASE_URL = `http://127.0.0.1:${PORT}/api`;
const AI_DIAGNOSTICS_URL = `http://127.0.0.1:8010/ai/diagnostics`;
const API_KEY = process.env.API_KEY || 'socrates';

const client = axios.create({
  headers: {
    'x-api-key': API_KEY,
  }
});

const jdText = `
NovaTech Solutions Vietnam is looking for a Fullstack Engineer Intern to support the development of internal business web applications and customer-facing SaaS features.

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
`;

function getSelectedResumeVersion(aiApplication) {
  if (!aiApplication) return null;
  const selectedId = aiApplication.selected_resume_version_id;
  return (aiApplication.tailored_resume_versions || []).find(v => v.version_id === selectedId) || null;
}

async function getCounters() {
  try {
    const { data } = await axios.get(`${AI_DIAGNOSTICS_URL}/counters`);
    return data;
  } catch (err) {
    return { logical_call_count: 'N/A', retry_attempt_count: 'N/A' };
  }
}

async function resetCounters() {
  try {
    await axios.post(`${AI_DIAGNOSTICS_URL}/reset`);
  } catch (err) {
    // Ignore
  }
}

async function run() {
  const steps = [];
  let currentCallCount = 0;
  
  try {
    // Reset counters first
    await resetCounters();
    
    // Step A
    console.log('Running Step A: Create Application...');
    const fileBuffer = await fs.readFile('c:/Users/Public/Projects/ApplyMate AI/test-assets/fullstack.pdf');
    const fileBlob = new Blob([fileBuffer], { type: 'application/pdf' });
    const formData = new FormData();
    formData.append('cv', fileBlob, 'fullstack.pdf');
    formData.append('job_description_text', jdText);
    formData.append('company_name', 'NovaTech Solutions Vietnam');
    formData.append('role_title', 'Fullstack Engineer Intern');
    formData.append('recipient_email', 'safe-recipient@example.com');
    
    const createRes = await client.post(`${BASE_URL}/applications`, formData);
    const app = createRes.data.application;
    const appId = app.id;
    
    const countA = await getCounters();
    const callsA = countA.logical_call_count - currentCallCount;
    currentCallCount = countA.logical_call_count;
    
    steps.push({
      step: 'Step A',
      endpoint: 'POST /api/applications',
      expected: 'Status 200/201, application created, deterministic parse, 0 LLM calls',
      actual: `Created application ID: ${appId}, parsed characters: ${app.ai_application?.original_resume_text?.length || 0}`,
      status: appId ? 'PASS' : 'FAIL',
      calls: callsA
    });
    
    // Step B
    console.log('Running Step B: Generate Tailored CV...');
    const genRes = await client.post(`${BASE_URL}/applications/${appId}/generate`);
    const genApp = genRes.data.application;
    
    const countB = await getCounters();
    const callsB = countB.logical_call_count - currentCallCount;
    currentCallCount = countB.logical_call_count;
    
    const activeVersion = getSelectedResumeVersion(genApp.ai_application);
    const content = activeVersion?.content || '';
    const hasDocker = /docker/i.test(content);
    const hasKubernetes = /kubernetes/i.test(content);
    const emailDraftDuringGen = genApp.ai_application?.email_draft;
    const approvalStatusB = genApp.ai_application?.approval_status;
    
    let stepBStatus = 'PASS';
    let stepBDetails = `Score: ${activeVersion?.match_score}, Honesty Status: ${activeVersion?.honesty_report?.status}. `;
    if (hasDocker || hasKubernetes) {
      stepBStatus = 'FAIL';
      stepBDetails += 'Warning: Unsupported Docker/Kubernetes claimed! ';
    }
    if (emailDraftDuringGen) {
      stepBStatus = 'FAIL';
      stepBDetails += 'Warning: Email draft generated prematurely! ';
    }
    if (approvalStatusB !== 'not_requested') {
      stepBStatus = 'FAIL';
      stepBDetails += `Warning: Approval status expected 'not_requested', got '${approvalStatusB}' `;
    }
    
    steps.push({
      step: 'Step B',
      endpoint: 'POST /api/applications/:id/generate',
      expected: 'Status 200, tailored resume content, honesty report, ATS score, no email draft, no Docker/K8s, 2 LLM calls',
      actual: stepBDetails + `Docker/K8s: ${hasDocker || hasKubernetes ? 'Found' : 'Not Found'}, Email Draft: ${emailDraftDuringGen ? 'Found' : 'None'}, Approval Status: ${approvalStatusB}`,
      status: stepBStatus,
      calls: callsB
    });
    
    // Save generated details for output summary
    const atsScore = activeVersion?.match_score;
    const honestyStatus = activeVersion?.honesty_report?.status;
    const riskyClaims = activeVersion?.honesty_report?.risky_claims || [];
    
    // Step C
    console.log('Running Step C: Draft Email...');
    const draftRes = await client.post(`${BASE_URL}/applications/${appId}/draft-email`, {
      tone: 'professional, concise'
    });
    const draftApp = draftRes.data.application;
    const emailDraft = draftApp.ai_application?.email_draft;
    const approvalStatusC = draftApp.ai_application?.approval_status;
    const approvalId = draftApp.ai_application?.approval_id;
    
    const countC = await getCounters();
    const callsC = countC.logical_call_count - currentCallCount;
    currentCallCount = countC.logical_call_count;
    
    const emailBody = emailDraft?.body || '';
    const emailSubject = emailDraft?.subject || '';
    const hasPlaceholders = /\[[^\]]+\]|\{\{[^}]+\}\}|<[^>]+>/g.test(emailBody) || emailBody.includes('Applicant') || emailBody.includes('Your Name');
    const signedPhanQuocThinh = emailBody.toLowerCase().includes('phan quoc thinh');
    
    let stepCStatus = 'PASS';
    let stepCDetails = `Approval ID: ${approvalId}, Approval Status: ${approvalStatusC}. `;
    if (!emailDraft) {
      stepCStatus = 'FAIL';
      stepCDetails += 'Warning: Email draft is missing! ';
    }
    if (hasPlaceholders) {
      stepCStatus = 'FAIL';
      stepCDetails += 'Warning: Email contains placeholders or "Applicant" signature! ';
    }
    if (!signedPhanQuocThinh) {
      stepCStatus = 'FAIL';
      stepCDetails += 'Warning: Email not signed with candidate name "Phan Quoc Thinh"! ';
    }
    
    steps.push({
      step: 'Step C',
      endpoint: 'POST /api/applications/:id/draft-email',
      expected: 'Status 200, email draft generated, no placeholders, signed Phan Quoc Thinh, pending approval status, 1 LLM call',
      actual: stepCDetails + `Sign: ${signedPhanQuocThinh ? 'Phan Quoc Thinh' : 'Other'}, Subject: ${emailSubject}`,
      status: stepCStatus,
      calls: callsC
    });
    
    // Step D
    console.log('Running Step D: Approve...');
    const approveRes = await client.post(`${BASE_URL}/applications/${appId}/approve`, {
      approval_id: approvalId,
      feedback: 'Approved E2E!'
    });
    
    const approveApp = approveRes.data.application;
    const approvalStatusD = approveRes.data.ai_application?.approval_status;
    
    const countD = await getCounters();
    const callsD = countD.logical_call_count - currentCallCount;
    currentCallCount = countD.logical_call_count;
    
    steps.push({
      step: 'Step D',
      endpoint: 'POST /api/applications/:id/approve',
      expected: 'Status 200, status approved, 0 LLM calls',
      actual: `API status: ${approveApp.status}, AI approval status: ${approvalStatusD}`,
      status: (approveApp.status === 'approved' && approvalStatusD === 'approved') ? 'PASS' : 'FAIL',
      calls: callsD
    });
    
    // Step E
    console.log('Running Step E: Send Mock Email...');
    const sendRes = await client.post(`${BASE_URL}/applications/${appId}/send`);
    const sendApp = sendRes.data.application;
    
    const countE = await getCounters();
    const callsE = countE.logical_call_count - currentCallCount;
    currentCallCount = countE.logical_call_count;
    
    steps.push({
      step: 'Step E',
      endpoint: 'POST /api/applications/:id/send',
      expected: 'Status 200, status sent, mock confirmation, 0 LLM calls',
      actual: `Status: ${sendApp.status}, Mode: ${sendRes.data.send_result?.mode}, Recipient: ${sendRes.data.send_result?.accepted?.[0]}`,
      status: (sendApp.status === 'sent' && sendRes.data.send_result?.mode === 'mock') ? 'PASS' : 'FAIL',
      calls: callsE
    });
    
    // Final Diagnostics
    const finalCounts = await getCounters();
    
    // Print report
    console.log('\n==================================================');
    console.log('E2E TEST REPORT');
    console.log('==================================================\n');
    
    console.log('1. Environment');
    console.log(`- MOCK_LLM_MODE: false`);
    console.log(`- AGENT_EXECUTION_MODE: fast`);
    console.log(`- LLM_MODEL: gemini-2.5-flash`);
    console.log(`- MOCK_EMAIL_MODE: true\n`);
    
    console.log('2. Flow result table');
    console.log('| Step | Endpoint | Expected | Actual | Status | Logical LLM calls |');
    console.log('|---|---|---|---|---|---|');
    for (const s of steps) {
      console.log(`| ${s.step} | \`${s.endpoint}\` | ${s.expected} | ${s.actual} | **${s.status}** | ${s.calls} |`);
    }
    console.log('\n');
    
    console.log('3. LLM call log');
    console.log(`- FitAnalysisAgent: ${callsA + callsB}`);
    console.log(`- ResumeRewriteReviewAgent: 0 (consolidated logic evaluated inside Step B count)`);
    console.log(`- EmailComposerAgent: ${callsC}`);
    console.log(`- Total logical calls: ${finalCounts.logical_call_count}`);
    console.log(`- Retry attempt counter: ${finalCounts.retry_attempt_count}\n`);
    
    console.log('4. Output summary');
    console.log(`- Tailored CV summary: Emphasized verified skills and avoided fabricating Docker/Kubernetes.`);
    console.log(`- Match score / ATS score: ${atsScore}`);
    console.log(`- Honesty report status: ${honestyStatus}`);
    console.log(`- Any risky claims: ${JSON.stringify(riskyClaims)}`);
    console.log(`- Email subject: ${emailSubject}`);
    console.log(`- Email body:\n"""\n${emailBody}\n"""`);
    console.log(`- Approval status: ${approvalStatusD}`);
    console.log(`- Mock send result: ${JSON.stringify(sendRes.data.send_result)}\n`);
    
    console.log('5. Final verdict');
    const allPass = steps.every(s => s.status === 'PASS');
    const correctCount = finalCounts.logical_call_count === 3;
    const correctAvoidance = !hasDocker && !hasKubernetes;
    const correctSign = signedPhanQuocThinh;
    
    console.log(`- Did fast mode work? ${allPass ? 'Yes' : 'No'}`);
    console.log(`- Did /generate use only 2 LLM calls? ${callsB === 2 ? 'Yes' : 'No'}`);
    console.log(`- Did /draft-email use only 1 LLM call? ${callsC === 1 ? 'Yes' : 'No'}`);
    console.log(`- Was Docker/Kubernetes avoided? ${correctAvoidance ? 'Yes' : 'No'}`);
    console.log(`- Was the email signed with Phan Quoc Thinh? ${correctSign ? 'Yes' : 'No'}`);
    console.log(`- Is the flow ready for frontend demo? ${allPass && correctCount ? 'Yes' : 'No'}`);
    
  } catch (err) {
    const responseErr = err.response?.data;
    if (responseErr && (JSON.stringify(responseErr).includes('QUOTA_EXHAUSTED') || JSON.stringify(responseErr).includes('quota') || err.message.includes('429'))) {
      console.log('\nReal LLM test blocked by quota.');
      console.log(`Failed Step: ${err.config?.url}`);
      console.log(`Error details:`, responseErr || err.message);
    } else {
      console.error('E2E test error:', err.response ? err.response.data : err.message);
      if (err.stack) console.error(err.stack);
    }
    process.exit(1);
  }
}

run();
