import { badRequest } from '../utils/httpErrors.js';

export function parseBody(schema, body) {
  const result = schema.safeParse(body);
  if (!result.success) {
    throw badRequest('Request validation failed.', result.error.flatten());
  }
  return result.data;
}
