import {test} from 'node:test';
import assert from 'node:assert/strict';
import {onRequestGet} from '../functions/api/candidates.js';

// 수집함 후보 전송량(260924 ⑨) — 같은 내용 재요청 = 304(본문 0) · 내용 바뀌면 200 + 새 지문 · 미러 폴백도 같은 규칙
const body = JSON.stringify([{url: 'https://x.kr/1', title: 't'}]);
const req = inm => ({headers: new Headers(inm ? {'if-none-match': inm} : {})});
function gh(text) { globalThis.fetch = async () => ({ok: true, text: async () => text}); }

test('첫 요청 = 200 + ETag · 같은 ETag 재요청 = 304 본문 0', async () => {
  gh(body);
  const r1 = await onRequestGet({env: {}, request: req()});
  assert.equal(r1.status, 200);
  const et = r1.headers.get('etag');
  assert.match(et, /^"[0-9a-f]{20}"$/);
  const r2 = await onRequestGet({env: {}, request: req(et)});
  assert.equal(r2.status, 304);
  assert.equal(await r2.text(), '');
  assert.equal(r2.headers.get('etag'), et);
  const r3 = await onRequestGet({env: {}, request: req('W/' + et)});
  assert.equal(r3.status, 304);   // 약한 비교(중간 압축기가 W/ 를 붙여도)
});

test('내용 바뀌면 200 + 새 ETag', async () => {
  gh(body);
  const et = (await onRequestGet({env: {}, request: req()})).headers.get('etag');
  gh(JSON.stringify([{url: 'https://x.kr/2'}]));
  const r = await onRequestGet({env: {}, request: req(et)});
  assert.equal(r.status, 200);
  assert.notEqual(r.headers.get('etag'), et);
});

test('원본 실패 → R2 미러 폴백도 ETag·304', async () => {
  globalThis.fetch = async () => ({ok: false});
  const env = {R2: {get: async () => ({text: async () => body, uploaded: new Date()})}};
  const r1 = await onRequestGet({env, request: req()});
  assert.equal(r1.headers.get('x-nm-src'), 'r2');
  const r2 = await onRequestGet({env, request: req(r1.headers.get('etag'))});
  assert.equal(r2.status, 304);
});

test('전 소스 실패 = [] · no-store(재시도가 캐시를 다시 읽지 않게) · x-nm-try 소스별 사유', async () => {
  globalThis.fetch = async u => (String(u).includes('api.github.com') ? {ok: false, status: 403} : {ok: false, status: 429});
  const r = await onRequestGet({env: {GH_TOKEN: 't', R2: {get: async () => null}}, request: req()});
  assert.equal(await r.text(), '[]');
  assert.equal(r.headers.get('x-nm-src'), 'none');
  assert.equal(r.headers.get('cache-control'), 'no-store');
  assert.equal(r.headers.get('x-nm-try'), 'api=403 raw=429 r2=miss');
});

test('앞 소스 실패 후 성공 = 성공 응답에도 x-nm-try', async () => {
  globalThis.fetch = async u => (String(u).includes('api.github.com') ? {ok: false, status: 401} : {ok: true, text: async () => body});
  const r = await onRequestGet({env: {GH_TOKEN: 't'}, request: req()});
  assert.equal(r.status, 200);
  assert.equal(r.headers.get('x-nm-src'), 'gh');
  assert.equal(r.headers.get('x-nm-try'), 'api=401');
});
