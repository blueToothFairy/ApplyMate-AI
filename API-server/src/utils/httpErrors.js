export class HttpError extends Error {
  constructor(statusCode, message, details = undefined) {
    super(message);
    this.name = 'HttpError';
    this.statusCode = statusCode;
    this.details = details;
  }
}

export function notFound(message = 'Resource not found.') {
  return new HttpError(404, message);
}

export function badRequest(message = 'Bad request.', details = undefined) {
  return new HttpError(400, message, details);
}

export function conflict(message = 'Conflict.', details = undefined) {
  return new HttpError(409, message, details);
}
