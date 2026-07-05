import test from 'node:test';
import assert from 'node:assert/strict';
import { hasUnresolvedPlaceholder } from '../src/utils/sanitize.js';
import { makeId } from '../src/utils/id.js';

test('placeholder detection catches common template markers', () => {
  assert.equal(hasUnresolvedPlaceholder('Dear [Company Name]'), true);
  assert.equal(hasUnresolvedPlaceholder('Hello {{name}}'), true);
  assert.equal(hasUnresolvedPlaceholder('Dear Hiring Team'), false);
});

test('makeId uses requested prefix', () => {
  assert.match(makeId('appgw'), /^appgw-[0-9a-f]+$/);
});
