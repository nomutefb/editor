import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

// 진입 = 캐시 무시 최신 셸(운영자 260929 「사이트 접속 시 캐시 무시하는 강제 새로고침 · 컨트롤 쉬프트 알 개념」) —
//   viewer/sw.js 를 가짜 SW 전역에서 실행해 index 셸 내비게이션을 흉내 낸다.
//   ① 저장본이 있어도 평소 진입이 서버 최신본을 받는다(종전 = 저장본 즉시 = 배포 뒤 첫 진입이 옛 화면)
//   ② 3s 안에 못 받으면·서버 오류면 저장본(깨진 앱·오류 화면 대신) ③ Access 만료 리다이렉트는 그대로 넘겨 로그인으로
const SRC = readFileSync(new URL('../viewer/sw.js', import.meta.url), 'utf8');
const ORIGIN = 'https://edit.nomute.kr';

function boot(fetchImpl) {
  const on = {}, store = new Map(), msgs = [];
  const self = {
    location: new URL(ORIGIN + '/sw.js'),
    addEventListener: (t, f) => { on[t] = f; },
    registration: {showNotification: async () => {}},
    clients: {matchAll: async () => [{postMessage: m => msgs.push(m)}], openWindow: async () => {}},
    skipWaiting() {},
  };
  const cache = {
    match: async k => store.has(String(k.url || k)) ? new Response(store.get(String(k.url || k))) : undefined,
    put: async (k, r) => { store.set(new URL(String(k), ORIGIN).href, await r.text()); },
    keys: async () => [...store.keys()].map(u => ({url: u})),
    delete: async k => store.delete(String(k.url || k)),
  };
  const caches = {open: async () => cache};
  vm.runInNewContext(SRC, {self, caches, URL, URLSearchParams, console, fetch: fetchImpl, Response, atob, setTimeout: f => setTimeout(f, 30)});   // 3s 캡 = 30ms 로 압축(순서만 본다)
  return {on, store, msgs};
}

async function navigate(h, path = '/', cacheMode = 'default') {
  let responded = null; const waits = [];
  h.on.fetch({
    request: {method: 'GET', mode: 'navigate', url: ORIGIN + path, cache: cacheMode},
    respondWith: p => { responded = p; },
    waitUntil: p => { waits.push(p); },
  });
  const res = await responded;
  await Promise.race([Promise.allSettled(waits), new Promise(r => setTimeout(r, 300))]);   // 뒤 갱신(waitUntil)은 상한까지만 기다린다 = 영영 안 오는 요청 사례에서 테스트가 안 멈춤
  return res;
}

const basic = (body, status = 200) => { const r = new Response(body, {status}); Object.defineProperty(r, 'type', {value: 'basic'}); return r; };
const OLD = '<html>OLD</html>', NEW = '<html>NEW</html>';

test('평소 진입(새로고침 제스처 아님)도 저장본 대신 서버 최신 셸', async () => {
  const h = boot(async () => basic(NEW));
  h.store.set(ORIGIN + '/', OLD);
  const res = await navigate(h, '/', 'default');
  assert.equal(await res.text(), NEW);   // seal-ok: node:test 표준 단언(형제 12/13 보유 · shell-build 는 단언 없는 문자열 대조 테스트)
  assert.equal(h.store.get(ORIGIN + '/'), NEW);   // 저장본도 최신으로 갈아 끼운다(다음 오프라인 폴백 = 최신) · seal-ok: node:test 표준 단언(형제 12/13 보유 · shell-build 는 단언 없는 문자열 대조 테스트)
});

test('딥링크 쿼리 진입도 같은 규칙(저장 키는 쿼리 제거)', async () => {
  const h = boot(async () => basic(NEW));
  h.store.set(ORIGIN + '/', OLD);
  assert.equal(await (await navigate(h, '/?a=260929-1200', 'default')).text(), NEW);   // seal-ok: node:test 표준 단언(형제 12/13 보유 · shell-build 는 단언 없는 문자열 대조 테스트)
});

test('3s 안에 못 받으면 저장본(오프라인·느린 회선 = 빈 화면 대신)', async () => {
  const h = boot(() => new Promise(() => {}));   // 영영 안 옴
  h.store.set(ORIGIN + '/', OLD);
  const res = await Promise.race([navigate(h), new Promise(r => setTimeout(() => r('hang'), 2000))]);
  assert.notEqual(res, 'hang');
  assert.equal(await res.text(), OLD);   // seal-ok: node:test 표준 단언(형제 12/13 보유 · shell-build 는 단언 없는 문자열 대조 테스트)
});

test('서버 오류(5xx)면 저장본 — 오류 화면을 띄우지 않는다', async () => {
  const h = boot(async () => basic('<html>err</html>', 503));
  h.store.set(ORIGIN + '/', OLD);
  assert.equal(await (await navigate(h)).text(), OLD);   // seal-ok: node:test 표준 단언(형제 12/13 보유 · shell-build 는 단언 없는 문자열 대조 테스트)
});

test('Access 만료 리다이렉트는 그대로 넘긴다(로그인 화면) · 저장본은 안 덮는다', async () => {
  const redir = {type: 'opaqueredirect', ok: false, status: 0, redirected: false, clone() { return this; }};
  const h = boot(async () => redir);
  h.store.set(ORIGIN + '/', OLD);
  const res = await navigate(h);
  assert.equal(res.type, 'opaqueredirect');   // seal-ok: node:test 표준 단언(형제 12/13 보유 · shell-build 는 단언 없는 문자열 대조 테스트)
  assert.equal(h.store.get(ORIGIN + '/'), OLD);   // seal-ok: node:test 표준 단언(형제 12/13 보유 · shell-build 는 단언 없는 문자열 대조 테스트)
  assert.ok(h.msgs.some(m => m && m.type === 'nm-auth-stale'));
});

test('처음 방문(저장본 없음) = 네트워크 그대로 · ?nosw=1 = SW 불간섭(종전)', async () => {
  const h = boot(async () => basic(NEW));
  assert.equal(await (await navigate(h)).text(), NEW);   // seal-ok: node:test 표준 단언(형제 12/13 보유 · shell-build 는 단언 없는 문자열 대조 테스트)
  let touched = false;
  h.on.fetch({request: {method: 'GET', mode: 'navigate', url: ORIGIN + '/?nosw=1', cache: 'default'}, respondWith: () => { touched = true; }, waitUntil() {}});
  assert.equal(touched, false);   // seal-ok: node:test 표준 단언(형제 12/13 보유 · shell-build 는 단언 없는 문자열 대조 테스트)
});
