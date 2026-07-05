import dotenv from 'dotenv';
import path from 'node:path';

// Load .env from the API-server working directory.
dotenv.config();

function requiredNumber(name, fallback) {
  const raw = process.env[name];
  if (raw === undefined || raw === '') return fallback;
  const value = Number(raw);
  if (Number.isNaN(value)) {
    throw new Error(`Invalid numeric env var ${name}: ${raw}`);
  }
  return value;
}

function requiredBool(name, fallback) {
  const raw = process.env[name];
  if (raw === undefined || raw === '') return fallback;
  return ['true', '1', 'yes', 'on'].includes(raw.toLowerCase());
}

export const env = {
  nodeEnv: process.env.NODE_ENV || 'development',
  port: requiredNumber('PORT', 8000),
  frontendOrigin: process.env.FRONTEND_ORIGIN || 'http://localhost:5173',
  apiKey: process.env.API_KEY || '',

  aiServerUrl: (process.env.AI_SERVER_URL || 'http://127.0.0.1:8010').replace(/\/$/, ''),
  aiRequestTimeoutMs: requiredNumber('AI_REQUEST_TIMEOUT_MS', 180000),

  uploadDir: path.resolve(process.cwd(), process.env.UPLOAD_DIR || 'tmp/uploads'),
  exportDir: path.resolve(process.cwd(), process.env.EXPORT_DIR || 'tmp/exports'),
  maxUploadMb: requiredNumber('MAX_UPLOAD_MB', 8),

  smtp: {
    host: process.env.SMTP_HOST || '',
    port: requiredNumber('SMTP_PORT', 587),
    secure: requiredBool('SMTP_SECURE', false),
    user: process.env.SMTP_USER || '',
    pass: process.env.SMTP_PASS || '',
    from: process.env.SMTP_FROM || process.env.SMTP_USER || '',
  },
  mockEmailMode: requiredBool('MOCK_EMAIL_MODE', false),
};

export function assertEmailConfig() {
  if (env.mockEmailMode) return;
  const missing = [];
  if (!env.smtp.host) missing.push('SMTP_HOST');
  if (!env.smtp.user) missing.push('SMTP_USER');
  if (!env.smtp.pass) missing.push('SMTP_PASS');
  if (!env.smtp.from) missing.push('SMTP_FROM or SMTP_USER');
  if (missing.length) {
    throw new Error(`Missing SMTP config for real email sending: ${missing.join(', ')}`);
  }
}
