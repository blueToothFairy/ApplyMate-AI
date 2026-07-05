import fs from 'node:fs/promises';
import axios from 'axios';
import { env } from '../config/env.js';

class AIClient {
  constructor() {
    this.client = axios.create({
      baseURL: env.aiServerUrl,
      timeout: env.aiRequestTimeoutMs,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  async health() {
    const { data } = await this.client.get('/health');
    return data;
  }

  async listSkills() {
    const { data } = await this.client.get('/ai/skills');
    return data;
  }


  async parseDocument(file, documentType = 'resume') {
    if (!file) {
      throw new Error('parseDocument requires a Multer file object.');
    }

    const fileBuffer = file.buffer
      ? file.buffer
      : await fs.readFile(file.path);

    const payload = {
      filename: file.originalname || file.filename || 'uploaded-document',
      mime_type: file.mimetype || 'application/octet-stream',
      content_base64: fileBuffer.toString('base64'),
      document_type: documentType,
    };

    const { data } = await this.client.post('/ai/documents/parse', payload);
    return data;
  }

  async parse(payload) {
    const { data } = await this.client.post('/ai/parse', payload);
    return data;
  }

  async generateTailoredCv(payload) {
    const { data } = await this.client.post('/ai/generate-tailored-cv', payload);
    return data;
  }

  async revise(applicationId, feedback, target = 'resume') {
    const { data } = await this.client.post('/ai/revise', {
      application_id: applicationId,
      feedback,
      target,
    });
    return data;
  }

  async draftEmail(applicationId, tone = 'professional, concise, internship-friendly') {
    const { data } = await this.client.post('/ai/draft-email', {
      application_id: applicationId,
      tone,
    });
    return data;
  }

  async requestApproval(applicationId) {
    const { data } = await this.client.post('/ai/approval/request', {
      application_id: applicationId,
    });
    return data;
  }

  async markApproval(applicationId, decision, approvalId, feedback = '') {
    const { data } = await this.client.post('/ai/approval/mark', {
      application_id: applicationId,
      decision,
      approval_id: approvalId || null,
      feedback,
    });
    return data;
  }

  async validateSend(payload) {
    const { data } = await this.client.post('/ai/validate-send', payload);
    return data;
  }

  async getApplication(applicationId) {
    const { data } = await this.client.get(`/ai/applications/${encodeURIComponent(applicationId)}`);
    return data;
  }

  async exportDocx(applicationId, resumeVersionId) {
    const params = {};
    if (resumeVersionId) params.resume_version_id = resumeVersionId;
    const { data, headers } = await this.client.get(`/ai/applications/${encodeURIComponent(applicationId)}/export/docx`, {
      params,
      responseType: 'arraybuffer',
    });
    return {
      buffer: Buffer.from(data),
      contentType: headers['content-type'] || 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      filename: getFilenameFromDisposition(headers['content-disposition']) || `tailored_cv_${applicationId}.docx`,
    };
  }
}

function getFilenameFromDisposition(disposition) {
  if (!disposition) return null;
  const match = /filename="?([^";]+)"?/i.exec(disposition);
  return match ? match[1] : null;
}

export const aiClient = new AIClient();
