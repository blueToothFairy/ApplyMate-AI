import nodemailer from 'nodemailer';
import { env, assertEmailConfig } from '../config/env.js';
import { makeId } from '../utils/id.js';

let transporter = null;

function getTransporter() {
  if (transporter) return transporter;
  assertEmailConfig();
  transporter = nodemailer.createTransport({
    host: env.smtp.host,
    port: env.smtp.port,
    secure: env.smtp.secure,
    auth: {
      user: env.smtp.user,
      pass: env.smtp.pass,
    },
  });
  return transporter;
}

export async function sendApplicationEmail({ to, subject, body, attachment }) {
  if (env.mockEmailMode) {
    return {
      mode: 'mock',
      accepted: [to],
      rejected: [],
      messageId: makeId('mockmail'),
      sentAt: new Date().toISOString(),
    };
  }

  const tx = getTransporter();
  const info = await tx.sendMail({
    from: env.smtp.from,
    to,
    subject,
    text: body,
    attachments: attachment
      ? [
          {
            filename: attachment.filename,
            content: attachment.buffer,
            contentType: attachment.contentType,
          },
        ]
      : [],
  });

  return {
    mode: 'real',
    accepted: info.accepted || [],
    rejected: info.rejected || [],
    messageId: info.messageId,
    response: info.response,
    sentAt: new Date().toISOString(),
  };
}
