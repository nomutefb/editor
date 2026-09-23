import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

// 알림 PICK 버튼(운영자 260924 «푸시에서 바로 PICK») — viewer/sw.js 를 가짜 SW 전역에서 실행해
//   ① 발송기가 실은 버튼만 표시되는가 ② 버튼 탭 = 요청 보관(탭 이동에도 유실 0) + 열린 앱 통지 or 새 창 ③ 본문 탭·남의 사이트는 종전 그대로인가.
const SRC = readFileSync(new URL('../viewer/sw.js', import.meta.url), 'utf8');

function boot(tabs = []) {
  const on = {}, shown = [], opened = [], store = new Map();
  const self = {
    location: new URL('https://edit.nomute.kr/sw.js'),
    addEventListener: (t, f) => { on[t] = f; },
    registration: {showNotification: async (title, opts) => { shown.push({title, opts}); }},
    clients: {matchAll: async () => tabs, openWindow: async u => { opened.push(u); }},
    skipWaiting() {},
  };
  const cache = {
    match: async k => store.has(String(k.url || k)) ? new Response(store.get(String(k.url || k))) : undefined,
    put: async (k, r) => { store.set(new URL(String(k), 'https://edit.nomute.kr').href, await r.text()); },
    keys: async () => [...store.keys()].map(u => ({url: u})),
    delete: async k => store.delete(String(k.url || k)),
  };
  const caches = {open: async () => cache};
  vm.runInNewContext(SRC, {self, caches, URL, URLSearchParams, console, fetch: async () => ({}), Response, atob});
  return {on, shown, opened, store, cache};
}

async function fire(h, type, ev) {
  let p = null;
  h.on[type]({...ev, waitUntil: x => { p = x; }});
  await p;
}

test('발송기가 실은 PICK 버튼만 표시 · 모르는 버튼은 버린다', async () => {
  const h = boot();
  const data = {json: () => ({title: 'News', body: '(긴급) x', url: 'https://edit.nomute.kr/?brk=k&nmv=1', kind: 'brk',
    actions: [{action: 'pick', title: 'PICK'}, {action: 'evil', title: 'X'}]})};
  await fire(h, 'push', {data});
  assert.deepEqual(h.shown[0].opts.actions, [{action: 'pick', title: 'PICK'}]);
  const h2 = boot();
  await fire(h2, 'push', {data: {json: () => ({title: 'T', body: 'b', url: '/'})}});
  assert.equal(h2.shown[0].opts.actions, undefined);   // 제작완료 등 = 버튼 없음(종전)
});

test('PICK 버튼 = 요청 보관 → 앱 없으면 새 창(act 표식) · 페이지가 가져가면 비워진다', async () => {
  const h = boot();
  await fire(h, 'notificationclick', {action: 'pick', notification: {close() {}, data: {url: 'https://edit.nomute.kr/?brk=k&bl=https%3A%2F%2Fy.kr&nmv=1', kind: 'iss'}}});
  assert.equal(new URL(h.opened[0]).searchParams.get('act'), 'pick');
  assert.equal(h.store.size, 1);
  let got = null;
  await fire(h, 'message', {data: {type: 'nm-pickreq-take'}, ports: [{postMessage: x => { got = x; }}]});
  assert.equal(got.length, 1);
  assert.equal(JSON.stringify([got[0].brk, got[0].bl, got[0].kind]), JSON.stringify(['k', 'https://y.kr', 'iss']));
  assert.equal(h.store.size, 0);   // 가져가며 지움 = 두 번째 탭은 빈손(이중 발사 0)
});

test('열린 앱이 있으면 새로고침 없이 통지·포커스', async () => {
  const msgs = []; let focused = 0, navigated = 0;
  const tab = {url: 'https://edit.nomute.kr/?tab=feed', postMessage: m => msgs.push(m), focus: async () => { focused++; }, navigate: async () => { navigated++; }};
  const h = boot([tab]);
  await fire(h, 'notificationclick', {action: 'pick', notification: {close() {}, data: {url: 'https://edit.nomute.kr/?brk=k&nmv=1', kind: 'brk'}}});
  assert.equal(JSON.stringify(msgs), JSON.stringify([{type: 'nm-pickreq'}]));   // vm 경계 객체 = 프로토타입이 달라 JSON 대조
  assert.equal(focused, 1); assert.equal(navigated, 0); assert.equal(h.opened.length, 0);
});

test('본문 탭·남의 사이트·긴급 아닌 알림은 act 를 안 붙인다', async () => {
  for (const [action, url] of [['', 'https://edit.nomute.kr/?brk=k&nmv=1'], ['pick', 'https://www.google.com/search?q=x'], ['pick', 'https://edit.nomute.kr/thumb.html?nmv=1#done']]) {
    const h = boot();
    await fire(h, 'notificationclick', {action, notification: {close() {}, data: {url}}});
    assert.equal(new URL(h.opened[0]).searchParams.get('act'), null, url);
  }
});
