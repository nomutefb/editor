import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

// 알림 PICK 버튼(운영자 260924 «푸시에서 바로 PICK») — viewer/sw.js 를 가짜 SW 전역에서 실행해
//   ① 발송기가 실은 버튼만 표시되는가 ② 버튼 탭 = 같은 딥링크 + act=pick 으로 여는가 ③ 본문 탭·남의 사이트는 종전 그대로인가.
const SRC = readFileSync(new URL('../viewer/sw.js', import.meta.url), 'utf8');

function boot(tabs = []) {
  const on = {}, shown = [], opened = [];
  const self = {
    location: new URL('https://edit.nomute.kr/sw.js'),
    addEventListener: (t, f) => { on[t] = f; },
    registration: {showNotification: async (title, opts) => { shown.push({title, opts}); }},
    clients: {matchAll: async () => tabs, openWindow: async u => { opened.push(u); }},
    skipWaiting() {},
  };
  const caches = {open: async () => ({match: async () => undefined})};
  vm.runInNewContext(SRC, {self, caches, URL, URLSearchParams, console, fetch: async () => ({}), Response, atob});
  return {on, shown, opened};
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

test('PICK 버튼 탭 = 같은 딥링크 + act=pick', async () => {
  const h = boot();
  await fire(h, 'notificationclick', {action: 'pick', notification: {close() {}, data: {url: 'https://edit.nomute.kr/?brk=k&bl=https%3A%2F%2Fy.kr&nmv=1'}}});
  const u = new URL(h.opened[0]);
  assert.equal(u.searchParams.get('act'), 'pick');
  assert.equal(u.searchParams.get('brk'), 'k');
});

test('본문 탭·남의 사이트·긴급 아닌 알림은 act 를 안 붙인다', async () => {
  for (const [action, url] of [['', 'https://edit.nomute.kr/?brk=k&nmv=1'], ['pick', 'https://www.google.com/search?q=x'], ['pick', 'https://edit.nomute.kr/thumb.html?nmv=1#done']]) {
    const h = boot();
    await fire(h, 'notificationclick', {action, notification: {close() {}, data: {url}}});
    assert.equal(new URL(h.opened[0]).searchParams.get('act'), null, url);
  }
});
