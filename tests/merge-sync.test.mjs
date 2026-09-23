import {test} from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFileSync} from 'node:fs';
import {onRequestPost} from '../functions/api/mapsync.js';

// 수집함 병합 계정 동기 — 미동기 큐(nm_merges_pend)·base 조건부 패치 회귀(260923 Access 만료 중 병합 유실).
const html = readFileSync(new URL('../viewer/index.html', import.meta.url), 'utf8');
const source = html.slice(html.indexOf("const MERGE_KEY = 'nm_merges'"), html.indexOf('const kstNow = () =>'));
const turn = () => new Promise(resolve => setTimeout(resolve, 5));
function client(fetch, storage = new Map()) {
  const flashes = [];
  const context = {
    fetch, console, setTimeout, clearTimeout, Promise, JSON, Date, Math, Set, Object, Array, String,
    localStorage: {getItem: k => storage.has(k) ? storage.get(k) : null, setItem: (k, v) => storage.set(k, String(v)), removeItem: k => storage.delete(k)},
    qFlash: t => flashes.push(t), renderScrap: () => {}, CURTAB: 'feed',
  };
  vm.createContext(context);
  vm.runInContext(source + '\nglobalThis.api = {saveMerges, loadMergesSrv, flushMerges, mergesAll, mergePend};', context);
  return {...context.api, storage, flashes};
}
const reject = () => Promise.reject(new TypeError('Failed to fetch'));   // Access 만료 = 302 → 교차 출처 = CORS reject

test('merge made while expired survives the post-login load and lands on the server', async () => {
  let online = false; const server = {}, posts = [];
  const c = client(async (url, opt) => {
    if (!online) return reject();
    if (String(url).startsWith('api/mapsync')) {
      const b = JSON.parse(opt.body); posts.push(b);
      Object.entries(b.set || {}).forEach(([k, v]) => { server[k] = v; }); (b.del || []).forEach(k => delete server[k]);
      return new Response('{"ok":true,"conflicts":[]}');
    }
    return new Response(JSON.stringify(server));
  });
  const v = {members: ['B'], at: 't1'};
  assert.equal(c.saveMerges({A: v}, {set: {A: v}}), true);
  await turn();
  assert.ok(c.mergePend().set.A, 'failed POST keeps the patch queued');
  online = true;
  c.storage.set('nm_merges_ts', String(Date.now() - 400e3));   // 5분 유예 경과
  await c.loadMergesSrv();
  assert.deepEqual(JSON.parse(JSON.stringify(c.mergesAll().A)), v, 'local merge not overwritten by the stale server copy');
  assert.deepEqual(server.A, v, 'queued patch landed on the server');
  assert.equal(posts[0].base.A, null, 'base = value the user saw before editing (absent)');
  assert.equal(c.storage.has('nm_merges_pend'), false, 'queue cleared after confirmed ok');
});

test('conflicting stale patch is dropped with a notice instead of overwriting', async () => {
  let online = false;
  const c = client(async url => {
    if (!online) return reject();
    return new Response(JSON.stringify(String(url).startsWith('api/mapsync') ? {ok: true, conflicts: ['A']} : {}));
  });
  c.storage.set('nm_merges', JSON.stringify({A: {members: ['B'], at: 't0'}}));
  c.saveMerges({}, {del: ['A']});
  await turn();
  assert.deepEqual(JSON.parse(JSON.stringify(c.mergePend().base)), {A: {members: ['B'], at: 't0'}});
  online = true;
  await c.flushMerges();
  assert.equal(c.storage.has('nm_merges_pend'), false);
  assert.equal(c.flashes.length, 1);
});

test('GC deletes are sent once and never queued', async () => {
  const bodies = [];
  const c = client(async (_u, opt) => { bodies.push(JSON.parse(opt.body)); return reject(); });
  c.saveMerges({}, {del: ['A', 'B']}, true);
  await turn();
  assert.equal(c.storage.has('nm_merges_pend'), false, 'offline GC decision is not replayed later');
  assert.deepEqual(bodies[0].del, ['A', 'B']);
});

test('server-answered failure backs off; a new edit still sends immediately', async () => {
  let n = 0;
  const c = client(async () => { n++; return new Response('{"error":"GitHub write 502"}', {status: 502}); });
  c.saveMerges({A: {members: ['B']}}, {set: {A: {members: ['B']}}});
  await turn();
  assert.equal(n, 1);
  await c.flushMerges();
  assert.equal(n, 1, 'poll retry waits for the backoff window');
  c.saveMerges({A: {members: ['B', 'C']}}, {set: {A: {members: ['B', 'C']}}});
  await turn();
  assert.equal(n, 2, 'fresh edit forces a send');
});

// ── 서버(functions/api/mapsync.js) base 의미론 ──
function gh(initial) {
  let cur = initial, puts = 0;
  globalThis.fetch = async (url, opt = {}) => {
    if ((opt.method || 'GET') === 'GET') return new Response(JSON.stringify({sha: 's', content: btoa(unescape(encodeURIComponent(JSON.stringify(cur))))}));
    puts++; cur = JSON.parse(decodeURIComponent(escape(atob(JSON.parse(opt.body).content)))); return new Response('{}');
  };
  return {state: () => cur, puts: () => puts};
}
const post = body => onRequestPost({request: new Request('https://x/api/mapsync', {method: 'POST', body: JSON.stringify(body)}), env: {GH_TOKEN: 't'}}).then(r => r.json());

test('server applies a patch whose base matches and skips one another device changed', async () => {
  const g = gh({A: {members: ['X']}, B: {members: ['Y']}});
  const r = await post({file: 'merges', set: {A: {members: ['X', 'Z']}, B: {members: ['Q']}}, base: {A: {members: ['X']}, B: {members: ['OLD']}}});
  assert.deepEqual(r.conflicts, ['B']);
  assert.deepEqual(g.state(), {A: {members: ['X', 'Z']}, B: {members: ['Y']}});
});

test('server replay of an already-landed patch is a no-op, and base-less requests stay unconditional', async () => {
  const g = gh({A: {members: ['X', 'Z']}});
  const r = await post({file: 'merges', set: {A: {members: ['X', 'Z']}}, base: {A: null}});
  assert.equal(r.noop, true); assert.deepEqual(r.conflicts, []); assert.equal(g.puts(), 0);
  const r2 = await post({file: 'merges', del: ['A']});
  assert.equal(r2.ok, true); assert.deepEqual(g.state(), {});
});

test('server skips a stale delete when the entry changed since the client read it', async () => {
  const g = gh({A: {members: ['NEW']}});
  const r = await post({file: 'merges', del: ['A'], base: {A: {members: ['OLD']}}});
  assert.deepEqual(r.conflicts, ['A']);
  assert.deepEqual(g.state(), {A: {members: ['NEW']}});
});
