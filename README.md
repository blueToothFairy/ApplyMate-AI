# ApplyMate AI — Human-in-the-Loop CV Tailoring & Job Application Agent

> A full-stack, multi-agent AI system that tailors CVs to job descriptions, drafts application emails, and sends them **only after explicit human approval**.

---

## Table of Contents

1. [The Problem](#1-the-problem)
2. [The Solution](#2-the-solution)
3. [Architecture Overview](#3-architecture-overview)
4. [Document Parsing Boundary](#4-document-parsing-boundary)
5. [Multi-Agent Workflow](#5-multi-agent-workflow)
6. [Security Features](#6-security-features)
7. [Project Structure](#7-project-structure)
8. [Setup & Installation](#8-setup--installation)
9. [Environment Variables](#9-environment-variables)
10. [Running Locally](#10-running-locally)
11. [API Reference](#11-api-reference)
12. [Known Issues & QA Notes](#12-known-issues--qa-notes)
13. [Deployment](#13-deployment)

---

## 1. The Problem

Job applicants face a set of recurring, time-consuming challenges:

- Sending the **same generic CV** to every role with no tailoring to the specific Job Description.
- Not knowing which **keywords, skills, or experience levels** the JD actually prioritises.
- Writing bullet points that are **vague, impact-free**, or full of buzzwords.
- Missing **ATS-critical keywords** that prevent the CV from reaching a human recruiter.
- Drafting **generic cover emails** that do not reference the specific role or company.
- Worrying that AI tools will **fabricate skills or experience** not present in the original CV.
- Losing control — unsure of **what exactly will be sent** before it is sent.

---

## 2. The Solution

ApplyMate AI is a **human-in-the-loop job application assistant** that:

1. Accepts a CV and Job Description from the user.
2. Runs a **multi-agent pipeline** to analyse, gap-detect, rewrite, and score the CV.
3. Checks every proposed change against an **honesty guardrail** — no fabricated skills, companies, or metrics.
4. Drafts a professional **application email** targeting the specific role.
5. Shows the user everything (CV diff, match score, honesty warnings, email draft) in a review UI.
6. **Blocks email sending** until the user explicitly approves — enforced by both the UI and the AI-server's send-policy validator.
7. Keeps a full **audit trail** of every agent action.

| Layer | Technology | Responsibility |
|---|---|---|
| **Frontend** | React + Vite | User input, review UI, diff viewer, approval controls |
| **API-Server** | Express.js | HTTP gateway, file upload, email delivery after approval |
| **AI-Server** | FastAPI + Python | Document parsing, multi-agent CV pipeline, policy validation |

---

## 3. Architecture Overview

```
+---------------------------------------------------------------+
|                      React Frontend                           |
|  Upload CV/JD  Review CV diff  Approve & Send  Audit view    |
+--------------------------------+------------------------------+
                                 |  REST (JSON + multipart)
                                 v
+---------------------------------------------------------------+
|                 Express API-Server  :3001                     |
|                                                               |
|  * Receives CV file upload (multer, field name: cv)           |
|  * Converts file buffer to base64                             |
|  * Forwards base64 payload to /ai/documents/parse             |
|  * Proxies all other AI workflow calls                        |
|  * Sends real/mock application email after validated approval  |
|  * Does NOT parse PDF / DOCX / TXT / MD locally               |
+---------------------------+------------------+----------------+
                            |  Axios (JSON)    |  Nodemailer
                            v                  v
+---------------------------------+   +----------------------+
|   FastAPI AI-Server  :8010      |   |  Email Provider/SMTP |
|                                 |   |  (or MOCK_EMAIL_MODE)|
|  POST /ai/documents/parse       |   +----------------------+
|  POST /ai/parse                 |
|  POST /ai/generate-tailored-cv  |
|  POST /ai/revise                |
|  POST /ai/draft-email           |
|  POST /ai/approval/request      |
|  POST /ai/approval/mark         |
|  POST /ai/validate-send         |
|  POST /ai/evaluate              |
|  GET  /ai/applications/:id      |
|                                 |
|  +---------------------------+  |
|  |  10-Agent Pipeline        |  |
|  +---------------------------+  |
|  +------------+ +----------+ |  |
|  | MCP Tools  | |  Skills  | |  |
|  +------------+ +----------+ |  |
|  +---------------------------+  |
|  | Prompt Injection &        |  |
|  | Honesty Guardrails        |  |
|  +---------------------------+  |
+---------------------------------+
```

---

## 4. Document Parsing Boundary

### The Problem (Legacy Behaviour)

In earlier versions, the API-server used `pdf-parse` and `mammoth` to extract text locally in Express, then passed raw text to the AI-server. This violated the architecture requirement: document parsing is a content intelligence concern, not a gateway concern.

### The Solution (Current Architecture)

The parsing boundary is **owned entirely by the AI-server**:

```
BEFORE (legacy):
  Frontend -[file]-> API-server -[pdf-parse/mammoth]-> AI-server [text only]

AFTER (current):
  Frontend -[file]-> API-server -[base64]-> AI-server /ai/documents/parse
                     (gateway only)          (parse + injection scan + structure)
```

**API-Server** (`aiClient.parseDocument`):
1. Accepts multipart file upload via multer (field: `cv`).
2. Reads file buffer and base64-encodes it.
3. POSTs `{ filename, mime_type, content_base64, document_type }` to `/ai/documents/parse`.

**AI-Server** (`POST /ai/documents/parse`):
1. Base64-decodes the payload.
2. Routes to the correct extractor by file suffix / MIME type:
   - `.txt`, `.md` — UTF-8 decode
   - `.docx` — `python-docx`
   - `.pdf` — `pypdf`
3. Runs `detect_prompt_injection()` on the extracted text.
4. Runs structural parsing (`parse_resume_text` or `parse_jd_text`).
5. Returns `{ text, structured_resume/jd, prompt_injection_hits, character_count }`.

**Key files:**

| File | Role |
|---|---|
| `API-server/src/services/aiClient.js` | `parseDocument()` — base64 encode & forward |
| `API-server/src/middleware/upload.js` | Multer config, field name `cv` |
| `AI-server/app/main.py` | `POST /ai/documents/parse` endpoint |
| `AI-server/app/utils/file_extractors.py` | `extract_text_from_bytes()` — PDF/DOCX/TXT/MD |
| `AI-server/app/utils/text.py` | `detect_prompt_injection()` |

---

## 5. Multi-Agent Workflow

```
              +----------------+
User Input -> |  IntakeAgent   |  Validates & normalises CV / JD input
              +-------+--------+
                      |
              +-------v----------------+
              | DocumentParserAgent    |  Structures CV sections & JD requirements
              +-------+----------------+
                      |
           +----------+-----------+
           |                      |
    +------v------+    +----------v----+
    | JDAnalyzer  |    |  CVAnalyzer   |  Parallel analysis
    +------+------+    +----------+----+
           +----------+-----------+
                      |
              +-------v---------------------+
              | TailoringStrategistAgent    |  Selects rewrite plan
              +-------+---------------------+
                      |
              +-------v-------+
              |  CVRewrite    |  Rewrites bullets, summary, skills
              +-------+-------+
                      |
           +----------+-----------+
           |                      |
    +------v--------+    +--------v-----+
    | HonestyCritic |    |  ATSScoring  |  Guardrail + score
    +------+--------+    +--------+-----+
           +----------+-----------+
                      |
              +-------v-------------+
              | EmailComposer       |  Drafts application email
              +-------+-------------+
                      |
              +-------v-------+
              | ApprovalAgent |  Review bundle, waits for human gate
              +---------------+
```

| Agent | File | Key Output |
|---|---|---|
| IntakeAgent | `agents/intake.py` | `application_id`, normalised session |
| DocumentParserAgent | `agents/document_parser.py` | `structured_resume`, `structured_jd` |
| JDAnalyzerAgent | `agents/jd_analyzer.py` | `jd_requirements`, `jd_keywords`, `priority_matrix` |
| CVAnalyzerAgent | `agents/cv_analyzer.py` | `cv_strengths`, `cv_weaknesses`, `missing_keywords` |
| TailoringStrategistAgent | `agents/tailoring_strategist.py` | `tailoring_strategy`, `rewrite_plan` |
| CVRewriteAgent | `agents/cv_rewrite.py` | `tailored_resume`, `changed_sections` |
| HonestyCriticAgent | `agents/honesty_critic.py` | `honesty_report`, `risky_claims` |
| ATSScoringAgent | `agents/ats_scoring.py` | `match_score`, `keyword_coverage` |
| EmailComposerAgent | `agents/email_composer.py` | `email_subject`, `email_body` |
| ApprovalAgent | `agents/approval.py` | `approval_id`, `approval_status` |

**Agent Skills** (`.skills/`) inject domain-specific playbooks into prompts:

| Skill | Coverage |
|---|---|
| `resume-tailoring` | Bullet rewrite rules, ATS keyword placement, honesty rules |
| `jd-analysis` | Role taxonomy, must-have vs nice-to-have, seniority detection |
| `cover-email-writing` | Professional email patterns, internship examples |
| `application-safety` | Prompt injection rules, send-email policy, PII handling |

---

## 6. Security Features

### Human-in-the-Loop Approval Gate

Email sending is impossible without an explicit approval chain:
1. User clicks **Approve & Send** in the frontend.
2. API-server calls `POST /ai/validate-send` — the AI-server policy engine checks every field.
3. Only if validation passes does the API-server call the email provider.

The approval record is **bound** to a specific CV version, recipient address, subject, and body. Any post-approval change invalidates the approval.

### Send-Policy Validation

Before any email is dispatched, the policy engine verifies:
- `approval_status == approved` for this `application_id`.
- Recipient email, subject, and body match the approved version exactly.
- No unreplaced placeholders (`[Company Name]`, `[Your Name]`, etc.).
- No prompt injection signals in the email body itself.

### Prompt Injection Detection

CV and JD content is treated as **untrusted user input**. `detect_prompt_injection()` scans for patterns such as:
- `ignore.*instructions`
- `send.*cv.*to`
- `disregard.*previous`
- `new.*instructions`
- `override.*policy`

Detected hits are returned in the API response and logged in the audit trail.

### Honesty Guardrail

The `HonestyCriticAgent` compares the rewritten CV against the original and flags any claim that:
- Adds a technology not evidenced in the original CV.
- Introduces a company, project, or metric without basis.
- Overstates impact in a way that cannot be defended in an interview.

### Audit Log

| Event | Trigger |
|---|---|
| `cv.uploaded` | File received by API-server |
| `session.created` | Application session initialised |
| `cv.generated` | Tailored CV version created |
| `email.drafted` | Email draft created |
| `approval.requested` | Review bundle created |
| `approval.marked` | User decision recorded |
| `send_policy.validated` | Policy engine cleared send |
| `send_policy.rejected` | Policy engine blocked send |
| `email.sent` | Email dispatched by API-server |

---

## 7. Project Structure

```
ApplyMate AI/
├── README.md
├── frontend/                   <- React + Vite user interface
│   ├── src/
│   ├── package.json
│   └── vite.config.js
│
├── API-server/                 <- Express.js gateway
│   ├── src/
│   │   ├── controllers/
│   │   │   └── applications.controller.js
│   │   ├── middleware/
│   │   │   └── upload.js          <- multer, field name: cv
│   │   ├── routes/
│   │   ├── services/
│   │   │   ├── aiClient.js        <- parseDocument(), proxy calls
│   │   │   └── emailService.js    <- Nodemailer send
│   │   └── config/
│   ├── package.json
│   └── .env.example
│
├── AI-server/                  <- FastAPI AI engine
│   ├── app/
│   │   ├── main.py             <- All endpoints incl. /ai/documents/parse
│   │   ├── models.py
│   │   ├── store.py            <- In-memory session store
│   │   ├── agents/             <- 10 specialised agents
│   │   │   └── workflow.py     <- Orchestrates the pipeline
│   │   ├── prompts/
│   │   │   └── builders.py     <- Prompt construction + skill injection
│   │   ├── services/
│   │   │   ├── llm_provider.py <- Gemini / Mock LLM
│   │   │   └── policy_service.py
│   │   ├── mcp_server/         <- MCP tool definitions
│   │   └── utils/
│   │       ├── file_extractors.py  <- PDF/DOCX/TXT/MD parsing
│   │       └── text.py             <- detect_prompt_injection()
│   ├── .skills/                <- Agent Skill playbooks
│   ├── evals/
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
│
└── docs/
    ├── project-description.txt.txt
    └── requirements.md
```

---

## 8. Setup & Installation

### Prerequisites

| Tool | Version |
|---|---|
| Node.js | >= 18.18.0 |
| Python | >= 3.11 |
| npm | >= 9.x |
| pip | bundled with Python |

### AI-Server (FastAPI)

```bash
cd "AI-server"

python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

Edit `AI-server/.env`:

```env
MOCK_LLM_MODE=true           # Set to false for real Gemini calls
GOOGLE_API_KEY=your_key_here
LLM_MODEL=gemini-2.0-flash
APP_ENV=development
AI_SERVER_PORT=8010
```

> Set `MOCK_LLM_MODE=true` for local development to avoid Gemini API rate limits.

### API-Server (Express)

```bash
cd "API-server"
npm install
cp .env.example .env
```

Edit `API-server/.env`:

```env
PORT=3001
AI_SERVER_URL=http://127.0.0.1:8010
AI_REQUEST_TIMEOUT_MS=120000
MOCK_EMAIL_MODE=true
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your@email.com
SMTP_PASS=yourpassword
EMAIL_FROM=ApplyMate AI <noreply@example.com>
```

### Frontend (React + Vite)

```bash
cd frontend
npm install
cp .env.example .env
```

Edit `frontend/.env`:

```env
VITE_API_BASE_URL=http://localhost:3001
```

---

## 9. Environment Variables

### AI-Server

| Variable | Default | Description |
|---|---|---|
| `MOCK_LLM_MODE` | `false` | `true` skips Gemini, returns mock data |
| `GOOGLE_API_KEY` | — | Gemini API key (required when MOCK_LLM_MODE=false) |
| `LLM_MODEL` | `gemini-2.0-flash` | Gemini model name |
| `APP_ENV` | `development` | Environment label |
| `AI_SERVER_PORT` | `8010` | FastAPI listen port |

### API-Server

| Variable | Default | Description |
|---|---|---|
| `PORT` | `3001` | Express listen port |
| `AI_SERVER_URL` | `http://127.0.0.1:8010` | FastAPI AI-server base URL |
| `AI_REQUEST_TIMEOUT_MS` | `120000` | Request timeout in milliseconds |
| `MOCK_EMAIL_MODE` | `false` | `true` logs email to console instead of sending |
| `SMTP_HOST` | — | SMTP server hostname |
| `SMTP_PORT` | `587` | SMTP port |
| `SMTP_USER` | — | SMTP username / address |
| `SMTP_PASS` | — | SMTP password |
| `EMAIL_FROM` | — | Sender display name and address |

---

## 10. Running Locally

Open three separate terminals:

**Terminal 1 — AI-Server**

```bash
cd "AI-server"
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux
uvicorn app.main:app --reload --host 127.0.0.1 --port 8010
```

Interactive docs: http://127.0.0.1:8010/docs

**Terminal 2 — API-Server**

```bash
cd "API-server"
npm run dev
```

Listens on: http://localhost:3001

**Terminal 3 — Frontend**

```bash
cd frontend
npm run dev
```

Opens at: http://localhost:5173

### Verify the stack

```bash
curl http://127.0.0.1:8010/health
```

### Quick smoke test — document parse

```bash
python -c "
import base64, json, urllib.request
data = base64.b64encode(b'Software Engineer. Skills: Python, FastAPI, Docker.').decode()
payload = json.dumps({'filename':'cv.txt','mime_type':'text/plain','content_base64':data,'document_type':'resume'}).encode()
req = urllib.request.Request('http://127.0.0.1:8010/ai/documents/parse', data=payload, headers={'Content-Type':'application/json'}, method='POST')
print(json.loads(urllib.request.urlopen(req).read()))
"
```

---

## 11. API Reference

### AI-Server (`http://127.0.0.1:8010`)

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `GET` | `/ai/skills` | List loaded Agent Skills |
| `POST` | `/ai/documents/parse` | Parse CV/JD file from base64 |
| `POST` | `/ai/parse` | Parse CV & JD from raw text |
| `POST` | `/ai/generate-tailored-cv` | Run full multi-agent CV tailoring pipeline |
| `POST` | `/ai/revise` | Revise CV or email with natural-language feedback |
| `POST` | `/ai/draft-email` | Draft application email |
| `POST` | `/ai/approval/request` | Create review bundle |
| `POST` | `/ai/approval/mark` | Record user approval decision |
| `POST` | `/ai/validate-send` | Validate send policy before email dispatch |
| `POST` | `/ai/evaluate` | Run evaluation checks |
| `GET` | `/ai/applications/{id}` | Get application session state |
| `GET` | `/ai/applications/{id}/export/docx` | Download tailored CV as DOCX |

### API-Server (`http://localhost:3001`)

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/applications` | Create application session (CV upload via `cv` field) |
| `GET` | `/api/applications/:id` | Get session state |
| `POST` | `/api/applications/:id/generate` | Run CV tailoring pipeline |
| `POST` | `/api/applications/:id/revise` | Revise with natural-language feedback |
| `POST` | `/api/applications/:id/draft-email` | Draft email |
| `POST` | `/api/applications/:id/approve` | Record approval |
| `POST` | `/api/applications/:id/send` | Validate & send email |
| `GET` | `/api/applications/:id/export/docx` | Download DOCX |

#### File Upload Format

```
POST /api/applications
Content-Type: multipart/form-data

Fields:
  cv              (file)    CV file — PDF, DOCX, TXT, or MD
  job_description (string)  Raw JD text
  company_name    (string)  Company name
  role_title      (string)  Role/position title
  recipient_email (string)  Recruiter or HR email address
```

> **Important:** The multipart file field must be named `cv` (not `resume_file`).

---

## 12. Known Issues & QA Notes

A full QA verification was performed after the document parsing boundary patch was applied.

| ID | Severity | Description | Status |
|---|---|---|---|
| BUG-01 | Critical | `pypdf` was missing from `AI-server/requirements.txt`, causing startup crash | Fixed — `pypdf>=5.0.0` added |
| BUG-02 | Critical | `parseDocument()` method was missing from `aiClient.js`, causing 500 on file upload | Fixed — method implemented |
| BUG-03 | Minor | Upload field name mismatch — test clients used `resume_file`, server expects `cv` | Documented — use field name `cv` |
| BUG-04 | Minor | Legacy `mammoth` and `pdf-parse` packages remained in `API-server/package.json` | Fixed — packages removed |

### Running Tests

```bash
# AI-server unit tests
cd "AI-server"
python -m pytest tests

# Offline evaluation suite (mock LLM)
MOCK_LLM_MODE=true python evals/run_evals.py

# Real LLM evaluation
MOCK_LLM_MODE=false GOOGLE_API_KEY=your_key python evals/run_evals.py

# API-server tests
cd "API-server"
npm test
```

---

## 13. Deployment

### Frontend

```bash
cd frontend && npm run build
# Deploy dist/ to Vercel, Netlify, or any static host
```

### API-Server

Deploy to Render, Railway, or Fly.io as a Node.js service.
Required env vars: `AI_SERVER_URL`, `MOCK_EMAIL_MODE`, `SMTP_*`, `EMAIL_FROM`.

### AI-Server

Deploy to Render, Railway, Cloud Run, or any Python container host.
Required env vars: `MOCK_LLM_MODE`, `GOOGLE_API_KEY`, `LLM_MODEL`.

### Docker (optional)

Both servers include a `Dockerfile`. Compose with:

```bash
docker compose up --build
```

> **Security reminder:** Never hardcode secrets. Use environment variables or a secrets manager for `GOOGLE_API_KEY` and SMTP credentials.

---

## Tech Stack Summary

| Component | Technology | Notes |
|---|---|---|
| Frontend | React 18, Vite | Diff viewer, review panel, approval controls |
| API-Server | Express 4, Multer, Nodemailer, Axios | Gateway + email sender |
| AI-Server | FastAPI, Uvicorn, Pydantic v2 | Agent pipeline host |
| LLM | Google Gemini (google-genai) | Toggle via MOCK_LLM_MODE |
| Document parsing | pypdf, python-docx | AI-server only |
| MCP Tools | mcp Python SDK | Tool abstraction layer |
| Agent Skills | Markdown files under .skills/ | Injected into agent prompts |
| Session Store | In-memory dict | Demo only — replace with Redis/DB for production |

---

*ApplyMate AI — built to demonstrate ADK multi-agent orchestration, MCP tool usage, human-in-the-loop security, and deployable full-stack architecture.*
