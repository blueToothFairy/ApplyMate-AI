# ApplyMate AI — ExpressJS API Server

This is the API gateway for ApplyMate AI.

It connects the ReactJS frontend to the FastAPI AI Server, manages temporary application sessions, receives CV/JD input, proxies AI workflow calls, validates approval state, and sends the final application email with Nodemailer after explicit user approval.

## Responsibility Boundary

| Layer | Responsibility |
|---|---|
| ReactJS Frontend | User interface: upload CV, paste JD, review CV/email, approve/send |
| ExpressJS API Server | Gateway, file upload, temporary session state, AI Server calls, Nodemailer sending |
| FastAPI AI Server | LLM prompts, ADK-style workflow, MCP tools, CV rewriting, email drafting, safety checking |

The Express server does **not** rewrite CVs by itself. It calls the FastAPI AI Server for AI tasks.

The FastAPI AI Server does **not** send the final email. It drafts and validates. This Express server sends with Nodemailer only after approval.

## Setup

```bash
cd API-server
npm install
cp .env.example .env
npm run dev
```

PowerShell:

```powershell
cd API-server
npm install
copy .env.example .env
npm run dev
```

Server URL:

```text
http://127.0.0.1:8000
```

Health check:

```text
GET http://127.0.0.1:8000/health
```

## Required AI Server

Start the FastAPI AI Server first:

```powershell
cd AI-server
.\.venv\Scripts\activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8010
```

Then set in `API-server/.env`:

```env
AI_SERVER_URL=http://127.0.0.1:8010
```

## Real Email Sending with Nodemailer

Set these values in `.env`:

```env
MOCK_EMAIL_MODE=false
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_SECURE=false
SMTP_USER=your_email@gmail.com
SMTP_PASS=your_app_password
SMTP_FROM="ApplyMate AI <your_email@gmail.com>"
```

For Gmail, use an App Password rather than your normal account password.

## Main Flow

1. Create application session.
2. Generate tailored CV through AI Server.
3. Review CV and email draft.
4. Revise if needed.
5. Approve.
6. Send.

## API Flow Example

Create session with multipart form-data:

```http
POST /api/applications
Content-Type: multipart/form-data

cv=<file>
job_description_text=Backend Intern JD text
company_name=Example Company
role_title=Backend Intern
recipient_email=recruiter@example.com
```

Generate tailored CV:

```http
POST /api/applications/:id/generate
```

Revise:

```http
POST /api/applications/:id/revise
Content-Type: application/json

{
  "feedback": "Make it more backend-focused and keep it honest.",
  "target": "resume"
}
```

Approve:

```http
POST /api/applications/:id/approve
Content-Type: application/json

{
  "approval_id": "appr-xxxx"
}
```

Send:

```http
POST /api/applications/:id/send
```

## Important Safety Behavior

`/api/applications/:id/send` performs this sequence:

1. Refreshes AI session from FastAPI.
2. Checks `approval_status === approved`.
3. Calls `/ai/validate-send` on the FastAPI server.
4. Blocks if recipient, subject, body, attachment version, or approval ID mismatch.
5. Blocks if unresolved placeholders remain.
6. Sends with Nodemailer only after validation passes.

## Scripts

```bash
npm run dev
npm run start
npm run check
npm run test
```

## File Structure

```text
API-server/
├── src/
│   ├── app.js
│   ├── server.js
│   ├── config/
│   ├── controllers/
│   ├── middleware/
│   ├── routes/
│   ├── services/
│   ├── stores/
│   ├── utils/
│   └── validators/
├── docs/
├── scripts/
├── tests/
├── tmp/
├── package.json
├── .env.example
├── Dockerfile
└── README.md
```
