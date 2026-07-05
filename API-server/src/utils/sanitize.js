const PLACEHOLDER_RE = /\[[^\]]+\]|\{\{[^}]+\}\}|<[^>]+>/;

export function normalizeString(value) {
  return typeof value === 'string' ? value.trim() : '';
}

export function hasUnresolvedPlaceholder(value) {
  return PLACEHOLDER_RE.test(String(value || ''));
}

export function redactSecret(value) {
  if (!value) return value;
  const str = String(value);
  if (str.length <= 8) return '*'.repeat(str.length);
  return `${str.slice(0, 4)}...${str.slice(-4)}`;
}
