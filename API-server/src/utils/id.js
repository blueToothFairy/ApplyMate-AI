import crypto from 'node:crypto';

export function makeId(prefix = 'id') {
  return `${prefix}-${crypto.randomBytes(5).toString('hex')}`;
}
