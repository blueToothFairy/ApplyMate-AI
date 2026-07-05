# ApplyMate API Server Contract

This ExpressJS server is the gateway used by the React frontend. It owns file upload, temporary application sessions, and real email delivery through Nodemailer. The FastAPI AI Server owns AI workflow, prompt/LLM calls, MCP-style tools, CV rewriting, email drafting, approval state, and send-policy validation.

## Base URL

`http://127.0.0.1:8000`

If `API_KEY` is configured, every `/api/*` call must include one of:

- Header: `x-api-key: <API_KEY>`
- Query: `?api_key=<API_KEY>`

## Endpoints

### `GET /health`

Checks Express and AI Server health.

### `POST /api/applications`

Creates a temporary gateway session.

Content types:

- `multipart/form-data` with `cv` file
- JSON with `resume_text`

Fields:

- `cv`: PDF, DOCX, TXT, or MD file
- `resume_text`: alternative to file upload
- `job_description_text`: required
- `company_name`: optional
- `role_title`: optional
- `recipient_email`: optional

### `POST /api/applications/:id/generate`

Calls FastAPI `/ai/generate-tailored-cv`. This creates the AI-side application session, tailored CV, email draft, review bundle, approval ID, and audit events.

### `POST /api/applications/:id/revise`

Body:

```json
{
  "feedback": "Make the CV more backend-focused.",
  "target": "resume"
}
```

`target` can be `resume`, `email`, or `both`.

Any revision invalidates prior approval in the AI Server.

### `POST /api/applications/:id/draft-email`

Body:

```json
{
  "tone": "professional and concise"
}
```

### `POST /api/applications/:id/approve`

Marks the active AI approval as approved. This does not send email yet.

### `POST /api/applications/:id/reject`

Marks the active AI approval as rejected.

### `POST /api/applications/:id/send`

Final real email sending endpoint.

Flow:

1. Refresh AI session.
2. Ensure `approval_status === approved`.
3. Call FastAPI `/ai/validate-send`.
4. Export the approved DOCX from FastAPI.
5. Send email with Nodemailer.
6. Return send confirmation.

### `GET /api/applications/:id/export/docx`

Proxies DOCX export from FastAPI.

### `GET /api/applications/:id/export/pdf`

Creates a simple PDF from the selected tailored CV content inside ExpressJS.

## Security Rules

- ExpressJS must never send email before AI policy validation passes.
- ExpressJS must use the AI-approved recipient, subject, body, and attachment version.
- If CV or email is revised, the old approval is invalidated by the AI Server.
- If unresolved placeholders remain, sending is blocked.
- SMTP credentials must be stored in environment variables only.
