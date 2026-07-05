import fs from 'node:fs';
import { createApp } from './app.js';
import { env } from './config/env.js';

fs.mkdirSync(env.uploadDir, { recursive: true });
fs.mkdirSync(env.exportDir, { recursive: true });

const app = createApp();

app.listen(env.port, () => {
  console.log(`ApplyMate API Server listening on http://127.0.0.1:${env.port}`);
  console.log(`AI_SERVER_URL=${env.aiServerUrl}`);
  console.log(`MOCK_EMAIL_MODE=${env.mockEmailMode}`);
});
