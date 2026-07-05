import { badRequest } from '../utils/httpErrors.js';

export function ensureResumeText(text) {
  const value = (text || '').trim();
  if (!value) {
    throw badRequest('A CV file or resume_text is required. Uploaded files are parsed by the AI-server.');
  }
  if (value.length < 20) {
    throw badRequest('Resume text extracted by AI-server is too short. Please upload a valid CV file or provide resume_text.');
  }
  return value;
}
