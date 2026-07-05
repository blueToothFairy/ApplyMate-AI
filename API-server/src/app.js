import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import { env } from './config/env.js';
import { apiKeyGuard } from './middleware/auth.js';
import { errorHandler, notFoundHandler } from './middleware/errorHandler.js';
import { applicationsRouter } from './routes/applications.routes.js';
import { health } from './controllers/applications.controller.js';

export function createApp() {
  const app = express();

  app.use(helmet());
  app.use(cors({ origin: env.frontendOrigin === '*' ? true : env.frontendOrigin, credentials: true }));
  app.use(express.json({ limit: '2mb' }));
  app.use(express.urlencoded({ extended: true, limit: '2mb' }));

  app.get('/health', health);
  app.use('/api', apiKeyGuard);
  app.use('/api/applications', applicationsRouter);

  app.use(notFoundHandler);
  app.use(errorHandler);
  return app;
}
