import fs from 'node:fs';
import multer from 'multer';
import { env } from '../config/env.js';
import { makeId } from '../utils/id.js';

fs.mkdirSync(env.uploadDir, { recursive: true });

const storage = multer.diskStorage({
  destination: (_req, _file, cb) => cb(null, env.uploadDir),
  filename: (_req, file, cb) => {
    const safeOriginal = file.originalname.replace(/[^a-zA-Z0-9._-]/g, '_');
    cb(null, `${Date.now()}-${makeId('cv')}-${safeOriginal}`);
  },
});

const allowedMimeTypes = new Set([
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'text/plain',
  'text/markdown',
  'application/octet-stream',
]);

export const uploadCv = multer({
  storage,
  limits: { fileSize: env.maxUploadMb * 1024 * 1024 },
  fileFilter: (_req, file, cb) => {
    const lower = file.originalname.toLowerCase();
    const extensionAllowed = lower.endsWith('.pdf') || lower.endsWith('.docx') || lower.endsWith('.txt') || lower.endsWith('.md');
    if (allowedMimeTypes.has(file.mimetype) || extensionAllowed) {
      cb(null, true);
      return;
    }
    cb(new Error('Unsupported CV file type. Please upload PDF, DOCX, TXT, or Markdown.'));
  },
});


export const uploadResumeFile = uploadCv.fields([
  { name: 'cv', maxCount: 1 },
  { name: 'resume_file', maxCount: 1 },
]);
