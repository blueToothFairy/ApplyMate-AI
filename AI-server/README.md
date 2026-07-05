# ApplyMate AI Server

FastAPI AI server for **ApplyMate AI — Human-in-the-Loop CV Tailoring & Job Application Agent**.

This version uses **real LLM calls through Gemini** when `MOCK_LLM_MODE=false`. The AI server contains prompt builders, Agent Skill loading, LLM-backed agents, MCP-compatible tools, CV/JD parsing, CV rewriting, email drafting, honesty checking, ATS scoring, and send-policy validation.

The AI server **does not send email directly** in this MVP. It only drafts and validates. The ExpressJS API server performs the final email delivery after user approval and `/ai/validate-send` succeeds.

## Architecture Boundary

```text
ReactJS Frontend
  -> ExpressJS API Server
      -> FastAPI AI Server
          - LLM-backed multi-agent workflow
          - MCP-compatible tools
          - Agent Skills
          - CV/JD analysis
          - CV rewriting
          - Email drafting
          - Honesty and safety checks
          - Send policy validation

ExpressJS API Server
  -> Email provider or mock email sender after approval
```

## Key Features

- FastAPI endpoints under `/ai/*`.
- Real Gemini LLM integration via `app/services/llm_provider.py`.
- Prompt construction via `app/prompts/builders.py`.
- LLM-backed agents:
  - `JDAnalyzerAgent`
  - `CVAnalyzerAgent`
  - `TailoringStrategistAgent`
  - `CVRewriteAgent`
  - `HonestyCriticAgent`
  - `ATSScoringAgent`
  - `EmailComposerAgent`
- Agent Skills loaded from `.skills/`:
  - `resume-tailoring`
  - `jd-analysis`
  - `cover-email-writing`
  - `application-safety`
- MCP-compatible tool layer.
- Human-in-the-loop approval model.
- Prompt injection detection.
- Honesty guardrail to avoid fabricated CV claims.
- In-memory session store for demo.
- DOCX export helper.
- Offline test mode through `MOCK_LLM_MODE=true`.

## Directory Structure

```text
AI-server/
  app/
    main.py
    config.py
    models.py
    store.py
    agents/
    prompts/
      builders.py
    services/
      llm_provider.py
      skill_loader.py
    mcp_server/
    utils/
  .skills/
    resume-tailoring/
    jd-analysis/
    cover-email-writing/
    application-safety/
  evals/
  tests/
  requirements.txt
  .env.example
  Dockerfile
```

## Setup

```bash
cd AI-server
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`:

```env
MOCK_LLM_MODE=false
GOOGLE_API_KEY=your_google_api_key_here
LLM_MODEL=gemini-2.0-flash
```

## Run

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8010
```

Open:

```text
http://127.0.0.1:8010/docs
```

## Minimal Generate Request

```bash
curl -X POST http://127.0.0.1:8010/ai/generate-tailored-cv \
  -H "Content-Type: application/json" \
  -d '{
    "resume_text": "Software Engineering student. Skills: Node.js, React, SQL. Project: Built REST API for workshop platform.",
    "job_description_text": "Backend Intern. Requirements: Node.js, RESTful API, SQL, Git. Docker is a plus.",
    "company_name": "Acme Tech",
    "role_title": "Backend Intern",
    "recipient_email": "hr@example.com"
  }'
```

## Main API Endpoints

| Endpoint | Purpose |
|---|---|
| `GET /health` | Health check |
| `GET /ai/skills` | List loaded Agent Skills |
| `POST /ai/parse` | Parse resume and JD |
| `POST /ai/generate-tailored-cv` | Run full LLM-backed multi-agent CV tailoring workflow |
| `POST /ai/revise` | Revise CV/email using natural-language feedback |
| `POST /ai/draft-email` | Draft application email |
| `POST /ai/approval/request` | Create review/approval bundle |
| `POST /ai/approval/mark` | Mark user decision |
| `POST /ai/validate-send` | Validate that ExpressJS is allowed to send email |
| `POST /ai/evaluate` | Run evaluation checks |
| `GET /ai/applications/{application_id}` | Retrieve application session |
| `GET /ai/applications/{application_id}/export/docx` | Export selected CV as DOCX |

## Where LLM and Prompts Are Used

Real LLM integration:

```text
app/services/llm_provider.py
```

Prompt builder and skill injection:

```text
app/prompts/builders.py
```

Agents that call the LLM:

```text
app/agents/jd_analyzer.py
app/agents/cv_analyzer.py
app/agents/tailoring_strategist.py
app/agents/cv_rewrite.py
app/agents/honesty_critic.py
app/agents/ats_scoring.py
app/agents/email_composer.py
app/agents/workflow.py        # revise flow uses LLM prompts
```

Agent Skill content used in prompts:

```text
.skills/resume-tailoring/
.skills/jd-analysis/
.skills/cover-email-writing/
.skills/application-safety/
```

## Important MVP Boundary

The AI server prepares and validates the application content. The ExpressJS API server performs the final email sending after calling `/ai/validate-send` successfully.

```text
ReactJS -> ExpressJS -> FastAPI AI Server
                      ↑
             CV rewriting, email drafting, policy validation

ReactJS -> ExpressJS -> Email Provider
          ↑
     final send step after approval
```

## Security Rules

- CV and JD are untrusted user-provided content.
- JD text must never override system/tool policy.
- The AI server must not send email directly.
- Approval is bound to a specific CV version, recipient, subject, and email body.
- If CV or email changes after approval, old approval becomes invalid.
- The agent must not fabricate skills, companies, metrics, or experience.

## Run Tests

Tests use mock mode automatically through `tests/conftest.py`.

```bash
python -m pytest tests
```

To run evals offline:

```bash
MOCK_LLM_MODE=true python evals/run_evals.py
```

To run evals with the real LLM:

```bash
MOCK_LLM_MODE=false GOOGLE_API_KEY=your_key python evals/run_evals.py
```

## Optional MCP Server

```bash
python -m app.mcp_server.server
```

The MCP server exposes parsing, analysis, generation, revision, review-bundle, scoring, diff, validation, and audit tools. The `send_application_email` tool intentionally raises an error because final email delivery belongs to the ExpressJS API server in this MVP.
