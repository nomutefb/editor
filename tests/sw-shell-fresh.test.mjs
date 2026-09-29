import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

// 진입 = 캐시 무시 최신 셸(운영자 260929 「사이트 접속 시 캐시 무시하는 강제 새로고침 · 컨트롤 쉬프트 알 개념」 · 평의회 8인 반영) —
//   viewer/sw.js 를 가짜 SW 전역에서 실행해 index 셸 내비게이션을 흉내 낸다.
//   ① 저장본이 있어도 평소 진입이 서버 최신본(종전 = 저장본 즉시 = 배포 뒤 첫 진입이 옛 화면)
//   ② 첫 응답 무소식·서버 오류·잘린 본문·본문 지연 = 저장본(빈·깨진 화면 대신) ③ Access 만료 = 그대로 로그인으로(만료 통지는 저장본을 띄웠을 때만)
//   ④ 방금 반영한 사본(x-nm-put 30s) = 네트워크 없이 즉시 ⑤ 새 버전 통지 = 방금 새 셸을 받은 문서 제외 ⑥ 알림 탭 = 앞으로 먼저, 이동은 그다음
const SRC = readFileSync(new URL('../viewer/sw.js', import.meta.url), 'utf8');
const ORIGIN = 'https://edit.nomute.kr';

function boot(fetchImpl, tabs) {
  const on = {}, store = new Map(), msgs = [], calls = {fetch: 0};
  const list = tabs || [{id: 'other', url: ORIGIN + '/', postMessage: m => msgs.push(['other', m.type])}];
  const self = {
    location: new URL(ORIGIN + '/sw.js'),
    addEventListener: (t, f) => { on[t] = f; },
    registration: {showNotification: async () => {}},
    clients: {matchAll: async () => list, openWindow: async () => {}},
    skipWaiting() {},
  };
  const cache = {
    match: async k => store.has(String(k.url || k)) ? store.get(String(k.url || k)).clone() : undefined,
    put: async (k, r) => { const t = await r.text(); store.set(new URL(String(k), ORIGIN).href, new Response(t, {headers: r.headers})); },
    keys: async () => [...store.keys()].map(u => ({url: u})),
    delete: async k => store.delete(String(k.url || k)),
  };
  const caches = {open: async () => cache};
  const fetch = (...a) => { calls.fetch++; return fetchImpl(...a); };
  vm.runInNewContext(SRC, {self, caches, URL, URLSearchParams, console, fetch, Response, Headers, atob, setTimeout: f => setTimeout(f, 30)});   // 캡(3s·10s·30s 안전핀) = 30ms 로 압축(순서만 본다)
  return {on, store, msgs, calls};
}
const seed = (h, body, headers) => h.store.set(ORIGIN + '/', new Response(body, {headers: headers || {}}));
const cachedText = h => h.store.get(ORIGIN + '/').clone().text();

async function navigate(h, path = '/', extra = {}) {
  let responded = null; const waits = [];
  h.on.fetch({
    request: {method: 'GET', mode: 'navigate', url: ORIGIN + path, cache: 'default'},
    respondWith: p => { responded = p; },
    waitUntil: p => { waits.push(p); },
    ...extra,
  });
  const res = await responded;
  await Promise.race([Promise.allSettled(waits), new Promise(r => setTimeout(r, 400))]);   // 뒤 저장·통지(waitUntil)는 상한까지만 = 영영 안 오는 요청 사례에서도 테스트가 안 멈춤
  return res;
}

const basic = (body, status = 200) => { const r = new Response(body, {status}); Object.defineProperty(r, 'type', {value: 'basic'}); return r; };
const redirect = () => ({type: 'opaqueredirect', ok: false, status: 0, redirected: false, clone() { return this; }});
const OLD = '<html>OLD</html>', NEW = '<html>NEW</html>';
const EQ = assert.equal;   // seal-ok: node:test 표준 단언(형제 12/13 보유 · shell-build 는 단언 없는 문자열 대조 테스트)

test('평소 진입(새로고침 제스처 아님)도 저장본 대신 서버 최신 셸 · 저장본도 최신으로', async () => {
  const h = boot(async () => basic(NEW));
  seed(h, OLD);
  EQ(await (await navigate(h)).text(), NEW);
  EQ(await cachedText(h), NEW);
});

test('딥링크·알림 진입(?a= · ?brk= · ?act=pick)도 같은 규칙', async () => {
  for (const q of ['/?a=260929-1200', '/?brk=k&nmv=1', '/?act=pick']) {
    const h = boot(async () => basic(NEW));
    seed(h, OLD);
    EQ(await (await navigate(h, q)).text(), NEW, q);
  }
});

test('첫 응답 무소식(오프라인·먹통 회선) = 저장본', async () => {
  const h = boot(() => new Promise(() => {}));
  seed(h, OLD);
  const res = await Promise.race([navigate(h), new Promise(r => setTimeout(() => r('hang'), 2000))]);
  assert.notEqual(res, 'hang');
  EQ(await res.text(), OLD);
});

test('응답은 왔는데 본문이 안 끝남 = 본문 캡 뒤 저장본', async () => {
  const h = boot(async () => { const r = new Response(new ReadableStream({start() {}})); Object.defineProperty(r, 'type', {value: 'basic'}); return r; });
  seed(h, OLD);
  EQ(await (await navigate(h)).text(), OLD);
});

test('잘린 본문(200인데 꼬리 </html> 없음) = 저장본 · 저장본을 안 덮는다', async () => {
  const h = boot(async () => basic('<html><head>NEW trunc'));
  seed(h, OLD);
  EQ(await (await navigate(h)).text(), OLD);
  EQ(await cachedText(h), OLD);
});

test('서버 오류(5xx·404) = 저장본 — 오류 화면을 띄우지 않는다', async () => {
  for (const st of [503, 404]) {
    const h = boot(async () => basic('<html>err</html>', st));
    seed(h, OLD);
    EQ(await (await navigate(h)).text(), OLD, String(st));
  }
});

test('Access 만료(리다이렉트·401·403) = 그대로 넘긴다 · 저장본 유지 · 만료 통지 없음(딥링크 이동과 경합 차단)', async () => {
  for (const mk of [redirect, () => basic('denied', 401), () => basic('denied', 403)]) {
    const h = boot(async () => mk());
    seed(h, OLD);
    const res = await navigate(h, '/?a=260929-1200');
    assert.ok(res.type === 'opaqueredirect' || res.status === 401 || res.status === 403);
    EQ(await cachedText(h), OLD);
    assert.ok(!h.msgs.some(m => m[1] === 'nm-auth-stale'));
  }
});

test('저장본을 띄운 뒤(첫 응답 캡 초과) 만료가 보이면 = 열린 페이지에 만료 통지', async () => {
  const h = boot(() => new Promise(r => setTimeout(() => r(redirect()), 120)));   // 캡(30ms)보다 늦게 도착
  seed(h, OLD);
  EQ(await (await navigate(h)).text(), OLD);
  assert.ok(h.msgs.some(m => m[1] === 'nm-auth-stale'));
});

test('방금 반영한 사본(x-nm-put 30s 안) = 네트워크 없이 즉시 · 오래된 도장 = 네트워크 우선', async () => {
  const h = boot(async () => basic(NEW));
  seed(h, OLD, {'x-nm-put': String(Date.now() - 2000)});
  EQ(await (await navigate(h)).text(), OLD);
  EQ(h.calls.fetch, 0);
  const h2 = boot(async () => basic(NEW));
  seed(h2, OLD, {'x-nm-put': String(Date.now() - 60000)});
  EQ(await (await navigate(h2)).text(), NEW);
});

test('새 버전 통지 = 다른 열린 창에만(새 셸을 받은 이 문서·떠나는 옛 문서 제외) · 저장본을 띄웠으면 이 문서도', async () => {
  const got = [];
  const tabs = ['new', 'leaving', 'other'].map(id => ({id, url: ORIGIN + '/', postMessage: m => got.push([id, m.type])}));
  const h = boot(async () => basic(NEW), tabs);
  seed(h, OLD);
  await navigate(h, '/', {resultingClientId: 'new', replacesClientId: 'leaving'});
  assert.deepEqual(got.filter(g => g[1] === 'nm-shell-updated').map(g => g[0]), ['other']);
  got.length = 0;
  const h2 = boot(() => new Promise(r => setTimeout(() => r(basic(NEW)), 120)), tabs);   // 캡보다 늦음 = 저장본 서빙
  seed(h2, OLD);
  EQ(await (await navigate(h2, '/', {resultingClientId: 'new', replacesClientId: 'leaving'})).text(), OLD);
  assert.ok(got.some(g => g[0] === 'new' && g[1] === 'nm-shell-updated'));   // 옛 셸을 받은 문서 = 자동 반영 대상
});

test('처음 방문(저장본 없음) = 네트워크 그대로 · ?nosw=1 = SW 불간섭(종전)', async () => {
  const h = boot(async () => basic(NEW));
  EQ(await (await navigate(h)).text(), NEW);
  let touched = false;
  h.on.fetch({request: {method: 'GET', mode: 'navigate', url: ORIGIN + '/?nosw=1', cache: 'default'}, respondWith: () => { touched = true; }, waitUntil() {}});
  EQ(touched, false);
});

test('알림 본문 탭(열린 창이 다른 화면) = 앞으로 먼저 올리고 그다음 이동', async () => {
  const order = [];
  const tab = {id: 't', url: ORIGIN + '/?tab=feed', postMessage() {}, focus: async () => { order.push('focus'); }, navigate: async () => { order.push('navigate'); return null; }};
  const h = boot(async () => basic(NEW), [tab]);
  let p = null;
  h.on.notificationclick({notification: {close() {}, data: {url: ORIGIN + '/?a=260929-1200&nmv=1'}}, waitUntil: x => { p = x; }});
  await p;
  assert.deepEqual(order, ['focus', 'navigate']);
});
