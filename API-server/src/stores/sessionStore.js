import { makeId } from '../utils/id.js';
import { notFound } from '../utils/httpErrors.js';

class SessionStore {
  constructor() {
    this.sessions = new Map();
  }

  create(data) {
    const id = makeId('appgw');
    const now = new Date().toISOString();
    const session = {
      id,
      aiApplicationId: null,
      status: 'created',
      createdAt: now,
      updatedAt: now,
      resumeText: data.resumeText,
      jobDescriptionText: data.jobDescriptionText,
      companyName: data.companyName || '',
      roleTitle: data.roleTitle || '',
      recipientEmail: data.recipientEmail || '',
      upload: data.upload || null,
      aiApplication: null,
      reviewBundle: null,
      emailSendResult: null,
      auditEvents: [
        {
          id: makeId('audit'),
          action: 'api.application.created',
          createdAt: now,
          detail: { hasUpload: Boolean(data.upload), hasRecipient: Boolean(data.recipientEmail) },
        },
      ],
    };
    this.sessions.set(id, session);
    return session;
  }

  get(id) {
    const session = this.sessions.get(id);
    if (!session) throw notFound(`Application session not found: ${id}`);
    return session;
  }

  update(id, patch) {
    const session = this.get(id);
    Object.assign(session, patch, { updatedAt: new Date().toISOString() });
    this.sessions.set(id, session);
    return session;
  }

  addAudit(id, action, detail = {}) {
    const session = this.get(id);
    const event = {
      id: makeId('audit'),
      action,
      createdAt: new Date().toISOString(),
      detail,
    };
    session.auditEvents.push(event);
    session.updatedAt = new Date().toISOString();
    return event;
  }

  list() {
    return [...this.sessions.values()];
  }
}

export const sessionStore = new SessionStore();
