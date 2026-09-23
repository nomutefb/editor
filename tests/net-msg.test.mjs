// 실패 문구 보정 회귀(260923 후속) — 26 파트 isNetErr/netMsg: fetch reject 만 만료·회선으로 가르고(코드 오류는 기존 문구),
// 만료 판별은 nmAuthNote(= head 가드 window.nmAuthCheck · /nm-sync.js HEAD 프로브 SSOT)에 위임한다.
import {test} from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFileSync} from 'node:fs';
const html = readFileSync(new URL('../viewer/index.html', import.meta.url), 'utf8');
const i = html.indexOf("const AUTH_EXPIRED_TXT ="), j = html.indexOf('function isNetErr', i), k = html.indexOf('\n// ', html.indexOf('async function netMsg', j));
assert.ok(i > 0 && j > i && k > j, 'slice markers');
const source = html.slice(i, k);

test('netMsg: only browser fetch rejections are classified; expiry vs line; code errors keep the caller text', async () => {
  let verdict = 'auth', calls = 0;
  const context = {nmAuthNote: async () => { calls++; return verdict; }, String, TypeError};
  vm.createContext(context);
  vm.runInContext(source + '\nglobalThis.api = {isNetErr, netMsg, AUTH_EXPIRED_TXT};', context);
  const {isNetErr, netMsg, AUTH_EXPIRED_TXT} = context.api;
  for (const m of ['Failed to fetch', 'Load failed', 'NetworkError when attempting to fetch resource.']) assert.equal(isNetErr(new context.TypeError(m)), true, m);
  for (const e of [new context.TypeError("Cannot read properties of undefined (reading 'x')"), new Error('Failed to fetch'), null]) assert.equal(isNetErr(e), false, String(e));
  const net = new context.TypeError('Failed to fetch');
  assert.equal(await netMsg(net), AUTH_EXPIRED_TXT);
  verdict = 'ok'; assert.match(await netMsg(net), /^네트워크 오류/);
  verdict = 'net'; assert.match(await netMsg(net), /^네트워크 오류/);
  calls = 0;
  assert.equal(await netMsg(new context.TypeError('x is not a function')), '', 'code bug → caller keeps its own text');
  assert.equal(await netMsg(new Error('HTTP 500')), '');
  assert.equal(calls, 0, 'non-network errors never fire the probe');
});
