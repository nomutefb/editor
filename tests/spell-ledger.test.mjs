// 맞춤법 학습 사전 계정 동기 원장 회귀(260923 · viewer/thumb.html learnPend/flushLearned · 평의회7 초안 이식)
// thumb.html 의 실제 블록(const _LEARN_KEY … function spellPairs · 부팅 IIFE 포함)을 vm 으로 돌린다.
import {test} from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFileSync} from 'node:fs';
const html = readFileSync(new URL('../viewer/thumb.html', import.meta.url), 'utf8');
const source = html.slice(html.indexOf('const _LEARN_KEY ='), html.indexOf('function spellPairs()'));
const settle = async (n = 30) => { for (let i = 0; i < n; i++) await new Promise(r => setImmediate(r)); };

function boot(storage, mapsync) {   // 페이지 1회 적재 = 블록(부팅 IIFE 포함)을 같은 저장소로 실행
  const bodies = [], events = {};
  const fetch = async (url, o = {}) => {
    url = String(url);
    if (url.startsWith('api/mapsync')) { bodies.push(JSON.parse(o.body)); return mapsync(); }
    if (url.startsWith('spell-learned.json')) return new Response('{}');
    throw Error('unexpected fetch ' + url);
  };
  const context = {
    fetch, Response, console, window: {addEventListener: (n, f) => { events[n] = f; }},
    localStorage: {getItem: k => storage.has(k) ? storage.get(k) : null, setItem: (k, v) => storage.set(k, String(v))},
  };
  vm.createContext(context);
  vm.runInContext(source + '\nglobalThis.api = {saveLearned, loadLearned, flushLearned};', context);
  return {...context.api, bodies, events};
}

test('a learned correction whose sync POST failed is re-sent on the next page load and then cleared', async () => {
  const storage = new Map();
  const a = boot(storage, async () => { throw new TypeError('Failed to fetch'); });   // 로그인 만료(Access 302 → reject)
  await settle();
  a.saveLearned({'됬다': '됐다'}, {'됬다': '됐다'}); await settle();
  assert.equal(a.bodies.length, 1);
  const b = boot(storage, async () => new Response('{"ok":true}'));
  await settle();
  assert.deepEqual(b.bodies, [{file: 'spell', set: {'됬다': '됐다'}}]);   // 구판: [] — 이 기기만 알고 끝
  assert.deepEqual(JSON.parse(storage.get('nomute_spell_pend')), {});
});

test('a 5xx keeps the pending pair and the online event retries it', async () => {
  const storage = new Map(); let reply = () => new Response('{"error":"GitHub write 502"}', {status: 502});
  const a = boot(storage, async () => reply());
  await settle();
  a.saveLearned({'않되': '안 돼'}, {'않되': '안 돼'}); await settle();
  assert.deepEqual(JSON.parse(storage.get('nomute_spell_pend')), {'않되': '안 돼'});
  reply = () => new Response('{"ok":true}');
  a.events.online(); await settle();
  assert.deepEqual(a.bodies.at(-1), {file: 'spell', set: {'않되': '안 돼'}});
  assert.deepEqual(JSON.parse(storage.get('nomute_spell_pend')), {});
});

test('the ledger is capped like the dictionary and one flush is one request', async () => {
  const storage = new Map();
  const a = boot(storage, async () => { throw new TypeError('Failed to fetch'); });
  await settle();
  for (let i = 0; i < 405; i++) a.saveLearned({}, {['k' + i]: 'v' + i});
  await settle();
  const pend = JSON.parse(storage.get('nomute_spell_pend'));
  assert.equal(Object.keys(pend).length, 400, 'capped at _LEARN_CAP (oldest dropped)');
  assert.equal(pend.k0, undefined); assert.equal(pend.k404, 'v404');
  const b = boot(storage, async () => new Response('{"ok":true}'));
  await settle();
  assert.equal(b.bodies.length, 1, 'boot flush = one request (≤50 keys) — no commit burst');
  assert.equal(Object.keys(b.bodies[0].set).length, 50);
});
