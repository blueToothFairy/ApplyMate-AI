import { env } from '../config/env.js';

export function apiKeyGuard(req, res, next) {
  if (!env.apiKey) {
    next();
    return;
  }
  const provided = req.header('x-api-key') || req.query.api_key || req.body?.api_key;
  if (provided !== env.apiKey) {
    res.status(401).json({ error: 'Unauthorized', message: 'Invalid or missing API key.' });
    return;
  }
  next();
}
