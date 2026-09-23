import {test} from 'node:test';
import assert from 'node:assert/strict';
import {claudeMessages} from '../functions/api/_claude.js';

// k·tr 즉답 공용 직결(functions/api/_claude.js) — 거절 대비 서버 폴백 opt-in · 베타 거부 시 종전 동작 · 오류 사유 보존
const env = {ANTHROPIC_API_KEY: 'k'};
const ok = body => ({status: 200, ok: true, json: async () => body, text: async () => JSON.stringify(body)});
const bad = (status, text) => ({status, ok: false, json: async () => ({}), text: async () => text});
console.warn = () => {};
function mockFetch(responses) {
  const calls = [];
  globalThis.fetch = async (url, init) => { calls.push({url, init, body: JSON.parse(init.body)}); return responses.shift(); };
  return calls;
}

test('every call opts into server-side fallback (default routing)', async () => {
  const calls = mockFetch([ok({stop_reason: 'end_turn', content: [{type: 'text', text: 'hi'}]})]);
  const m = await claudeMessages(env, {model: 'm', max_tokens: 10, messages: []});
  assert.equal(m.content[0].text, 'hi');
  assert.equal(calls.length, 1);
  assert.equal(calls[0].init.headers['anthropic-beta'], 'server-side-fallback-2026-07-01');
  assert.equal(calls[0].body.fallbacks, 'default');
  assert.equal(calls[0].body.model, 'm');
});

test('beta rejected with 400 → one retry without fallback (previous behavior, no runner detour)', async () => {
  const calls = mockFetch([bad(400, '{"error":{"message":"fallbacks is not supported for this model"}}'),
                           ok({stop_reason: 'end_turn', content: []})]);
  await claudeMessages(env, {model: 'm', max_tokens: 10, messages: []});
  assert.equal(calls.length, 2);
  assert.equal(calls[1].init.headers['anthropic-beta'], undefined);
  assert.equal(calls[1].body.fallbacks, undefined);
});

test('other 400 / http errors throw with the reason and never retry', async () => {
  let calls = mockFetch([bad(400, 'max_tokens: too large')]);
  await assert.rejects(claudeMessages(env, {model: 'm'}), /anthropic 400 max_tokens/);
  assert.equal(calls.length, 1);
  calls = mockFetch([bad(429, 'rate limited')]);
  await assert.rejects(claudeMessages(env, {model: 'm'}), /anthropic 429 rate limited/);
  assert.equal(calls.length, 1);
});

test('fallback-served response keeps text parsing unchanged (fallback block ignored by type filter)', async () => {
  mockFetch([ok({model: 'fallback-model', stop_reason: 'end_turn',
                 usage: {iterations: [{type: 'message'}, {type: 'fallback_message'}]},
                 content: [{type: 'fallback', from: {model: 'm'}, to: {model: 'fallback-model'}}, {type: 'text', text: 'ok'}]})]);
  const m = await claudeMessages(env, {model: 'm'});
  assert.equal(m.content.filter(b => b.type === 'text').map(b => b.text).join(''), 'ok');
  assert.equal(m.model, 'fallback-model');
});
