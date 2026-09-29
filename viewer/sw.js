// 노뮤트 서비스워커 — ① 긴급(breaking) 속보 웹푸시 수신·표시 ② HTML 셸 네트워크 우선 + 폴백 캐시.
// 발송 = .github/scripts/push_send.py(pywebpush) / 구독 = api/push. 정본 설명 = docs/라우터_법령전문.md 제66조③·제67조.
//
// ── ② 셸 캐시(운영자 승인 260706 · 기틀검증 5인 260706 — 260929 네트워크 우선 전환 = 평의회 8인) ──
// 뷰어 index 셸(/·/index.html) 최상위 내비게이션*만* 캐시 대상. 260706 원안 = 캐시-우선(스플래시 최단화) →
// 260929 운영자 지시로 네트워크 우선(아래 '진입 전략') — 캐시는 오프라인·지연·서버 오류 때 깨진 앱 대신 띄우는 폴백.
// ⚠️ 스코프 = index 두 경로 화이트리스트가 기틀(평의회 1·2·4·5 수렴): 도구 HTML(thumb/ly/k/comp/track)은
//    loadToolFrame의 `?v=Date.now()` 버스트 + _headers no-cache = '항상 최신' 계약이라 절대 캐시 대상 아님
//    (전 내비게이션 캐시였던 초안이 이 계약을 무력화 → REJECT·수정). 스코프 넓히기 = 기틀 변경(재검증 필수).
// 진입 전략(운영자 260929 「사이트 접속 시 캐시 무시하는 강제 새로고침」 — 260706 캐시 즉시 트레이드를 뒤집음):
//    저장본이 있어도 매 진입 네트워크 우선(첫 응답 3s · 본문 10s 캡) = 배포 뒤 첫 진입부터 최신 셸. 캐시 = 오프라인·지연·서버 오류·잘린 본문 폴백
//    + 방금(30s) 페이지가 받아 꽂은 최신(x-nm-put) 즉시 서빙.
//    데이터 JSON(articles 등)·외부 JS·이미지는 fetch(비내비게이션)라 SW 불간섭 = 기사 내용 '항상 최신' 불변.
// 가드 3중: ⓐ res.type==='basic' && ok && !redirected만 캐시 = Cloudflare Access 로그인/리다이렉트 오염 차단
//          ⓑ ?nosw=1 = 캐시 전면 우회 탈출구(순수 네트워크)
//          ⓒ 진입 응답이 리다이렉트/401·403 = 그대로 넘겨 로그인 화면 · 3s 넘겨 저장본을 띄운 뒤 만료가 보이면 nm-auth-stale 통지 → 페이지가 ?nosw=1 재진입
//             = Access 세션 만료 시 '깨진 앱'에 안 갇히고 로그인 화면으로 자가치유(index 리스너와 한 쌍).
// 롤백 런북(평의회 4): sw.js *삭제(404) 금지* — 삭제해도 브라우저는 기존 SW를 언레지스터하지 않고 캐시 서빙
//    계속함. 반드시 '무해화 sw.js 배포'(fetch 핸들러 제거 + activate에서 nm-shell-* *전량* delete)로 되돌릴 것.
// ── 좀비 SW 자기소멸(운영자 260723 · 중복 알림·회색아이콘 근본픽스 · 8인 평의회 하드닝) ──
// 정본 호스트 = edit.nomute.kr 단독(260821 운영자 «옛 거는 아예 안쓰게» — 구 병존분 apps.nomute.kr 회수).
// ⚠ 회수의 실효 범위 = 선언까지다. 옛 화면은 옛 계정 배포라 이 파일을 영영 안 받으므로 거기 남아 도는
//    서비스워커는 이 목록 변화를 못 본다(자기소멸도 안 한다) — 새 화면·미리보기 판정은 종전과 같다
//    (edit = 정본 유지 · *.pages.dev = 종전대로 자기소멸 대상). 즉 이 줄은 「코드가 옛 걸 정본으로
//    인정하지 않는다」를 못박는 것이고, 옛 화면 좀비 SW의 실제 소멸은 그쪽 배포 축이라 코드로 못 한다.
// ⚠ 260816 실사고 = 이관 때 새 도메인을 이 목록에 안 넣어서, 새 화면을 여는 순간 정상 서비스워커가
//    자기를 '비정본'으로 오판해 **푸시 구독을 스스로 해제하고 등록 말소**했다(= 바로 아래 주석이
//    경고한 그 파국이 실제로 일어난 것). 도메인을 늘릴 땐 반드시 이 배열에 먼저 추가한다.
// 구 editor-6dw.pages.dev 등 비정본 origin에 남아 도는 서비스워커는
// 같은 속보를 한 번 더 띄우는 '중복 알림'의 원인 — _middleware.js 의 301 리다이렉트는 페이지 이동만 막고,
// 푸시 수신(FCM→SW 직배달)은 내비게이션을 안 거쳐 못 막기 때문(아이콘도 pages.dev→301→Access벽에 막혀 회색 N).
// 그런 SW는 알림을 띄우지 말고 자기 구독을 해제·언레지스터해 스스로 소멸한다.
// 실효 킬 레버 = pushManager.unsubscribe()(로컬↔FCM 연산이라 Access 무관 즉시 성공) → 다음 발송이 410 Gone
//   → push_send.py 가 subscriptions.json 에서 자동 정리. unregister()는 컨트롤 클라이언트가 없어질 때 정리(지연 가능)
//   지만, 잔존해도 push 핸들러 가드가 매번 알림을 억제하므로 중복은 안 뜬다(2중 방어). 서버 통지 fetch는 제거함
//   — cross-origin + Access + CORS 프리플라이트로 사실상 항상 실패하는 죽은 코드였다(평의회 2·3, 260723).
// ⚠️ CANON_HOSTS 화이트리스트(평의회 1·4) — 단일 문자열이면 향후 정본 도메인 교체·추가 시 정상 SW가 오판
//    자기소멸(전 구독 말소) 파국. localhost = 로컬 푸시 테스트 보존. _middleware.js 목적지와 한 쌍(동시 갱신).
const CANON_HOSTS = ['edit.nomute.kr', 'localhost', '127.0.0.1'];
function isCanonHost() { return CANON_HOSTS.includes(self.location.hostname); }
async function selfDestructIfStale() {
  if (isCanonHost()) return false;   // 정본 origin = 정상 동작(자기소멸 안 함)
  try {
    const s = await self.registration.pushManager.getSubscription();
    if (s) await s.unsubscribe().catch(() => {});   // 즉시 구독 파기 = 실효 킬(다음 발송 410 → 서버 자동 정리)
  } catch (_) {}
  await self.registration.unregister().catch(() => {});
  return true;
}

const SHELL_CACHE = 'nm-shell-v2';   // v1→v2(260802 2차 재발) — activate 청소가 구 v1(절단 오염 사본 포함)을 전 기기에서 원격 소각
const SHELL_PATHS = ['/', '/index.html'];   // 캐시 화이트리스트 — 여기 없는 HTML은 SW가 손 안 댐

self.addEventListener('fetch', event => {
  const req = event.request;
  if (req.method !== 'GET' || req.mode !== 'navigate') return;   // 최상위/iframe HTML 문서 외 불간섭
  const url = new URL(req.url);
  if (url.origin !== self.location.origin || !SHELL_PATHS.includes(url.pathname) || url.searchParams.has('nosw')) return;
  event.respondWith((async () => {
    const t0 = Date.now();
    const key = url.origin + url.pathname;   // 쿼리 제거 정규화 = 딥링크(?a=·?msg=) 변형이 캐시를 늘리지도 가르지도 않음
    const cache = await caches.open(SHELL_CACHE);
    const cachedRaw = await cache.match(key);
    // 방금 받은 최신 = 다시 안 받는다(평의회260929 — 네트워크 우선이 된 뒤 「새 버전 반영」 재진입이 방금 꽂은 셸을 두고 한 번 더 받아 260821 흰 번쩍이 되살아나던 것):
    //    applyShellUpdate가 네트워크에서 막 받아 꽂은 사본엔 x-nm-put(꽂은 시각)이 붙는다 → 30s 안이면 네트워크와 같다 = 즉시 서빙(아래 절단 검문은 그대로 거친다).
    const putAt = cachedRaw ? +(cachedRaw.headers.get('x-nm-put') || 0) : 0;
    const justPut = putAt > 0 && Date.now() - putAt < 30000;
    const resP = justPut ? null : fetch(req);   // 네트워크 먼저 출발 = 아래 저장본 검문 read와 겹쳐 돈다(캡 기준점 = 요청 시작)
    if (resP) resP.catch(() => {});             // 체인이 붙기 전 거부 = 미처리 경고만 막는다(실제 처리는 아래)
    // ── 서빙 전 절단 검문(260802 2차 재발 봉합) — put 검문만으론 '이미 오염된 기기'를 못 구한다: 절단이 문서 초반부면
    //    head 자가치유 가드조차 사본에 안 실려 페이지 JS 전멸 = 페이지측 탈출 전무. SW는 no-cache로 항상 자동 갱신되므로
    //    「절단 사본은 서빙 자체가 안 된다」를 SW 불변식으로 승격 — 꼬리 </html> 아니면 즉시 소각 + 네트워크 직행.
    //    비용 = 진입당 캐시 본문 1회 read(수십 ms급) — 무결성 우선(운영자 260802 재발 실측).
    const cachedBody = cachedRaw ? await cachedRaw.clone().text().catch(() => null) : null;
    const cachedOk = cachedBody != null && /<\/html>\s*$/i.test(cachedBody);
    const cached = cachedOk ? cachedRaw : null;   // 이하 로직은 '검증된 사본'만 캐시로 취급
    if (cachedRaw && !cachedOk) event.waitUntil(cache.delete(key).catch(() => {}));   // 오염 사본 소각(다음 진입 = 순수 네트워크)
    if (justPut && cached) return cached;
    const netRes = resP || fetch(req);
    const sleep = ms => new Promise(r => setTimeout(() => r(null), Math.max(0, ms)));
    const isAuth = r => !!r && (r.type === 'opaqueredirect' || r.status === 401 || r.status === 403);   // Access 만료 = 로그인 리다이렉트(내비게이션 = redirect 'manual' → opaqueredirect)·401·403
    let netBody = null, netIntact = false, putRes = null;
    const netP = netRes.then(async res => {
      if (res.ok && !res.redirected && res.type === 'basic') {
        // ── 절단 검문(260802 '상단만 렌더' 사고) — 라이브 index 응답은 content-length 없는 청크 스트림이라(실측)
        //    전송 중 절단이 '정상 EOF'로 보여 res.ok 그대로다. 본문 꼬리가 </html>인 것만 서빙·캐시 자격(잘린 응답은 저장본이 있으면
        //    저장본을 띄우고 · 없으면(첫 방문) 그대로 넘겨 head 자가치유 가드가 탈출 담당 · 평의회260929 #6-1).
        putRes = res.clone();
        netBody = await res.clone().text().catch(() => null);
        netIntact = netBody != null && /<\/html>\s*$/i.test(netBody);
      }
      return res;
    });
    // 저장·새 버전 통지 = 응답 경로 밖(첫 화면을 캐시 쓰기·비교에 붙잡지 않는다) — 무엇을 띄웠는지(served)가 정해진 뒤에만 판정.
    let decide = () => {}; const decided = new Promise(r => { decide = r; }); setTimeout(() => decide(false), 20000);   // 안전핀 = 판정 누락이어도 수명 유한
    const saveP = Promise.all([netP.catch(() => null), decided]).then(async ([res, servedNet]) => {
      if (res && netIntact) {
        let changed = false;   // 새 index 셸 배포 감지(옛≠새) → 열린 페이지에 nm-shell-updated 통지(운영자 260717 새버전 토스트)
        if (cached) {
          const scrub = s => (s || '').replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, m => (/cdn-cgi|cloudflareinsights/i.test(m) ? '' : m));   // 엣지 주입 노이즈 소거(운영자 260717 무한루프 실기록) — Cloudflare가 응답마다 다르게 심는 스크립트(RUM beacon rayId·챌린지 토큰)를 비교에서 제외. 같은 셸인데 주입 토큰만 달라 '다름' 오판 → 반영 탭 직후 또 "새 버전" 무한 재알림의 근원 차단(앱 자체 스크립트는 cdn-cgi·cloudflareinsights 문자열 0 = 소거 비대상)
          changed = scrub(cachedBody) !== scrub(netBody);   // 두 본문 = 이미 읽음(재read 0 · 비교 문법은 종전 그대로)
        }
        await cache.put(key, putRes).then(() => {}, () => {});   // waitUntil 수명 안(쓰기 유실 차단·평의회 1) · 실패(quota 등)해도 진행 · 절단 사본 = put 자격 없음
        if (changed) {   // 갱신 완료 후 통지 = 탭→reload가 새 셸 서빙 보장 · 방금 새 셸을 받은 이 내비게이션의 새·옛 문서는 제외(헛 리로드·옛 문서의 반영 도장 오염 차단)
          const skip = servedNet ? [event.resultingClientId, event.replacesClientId].filter(Boolean) : [];
          self.clients.matchAll({ type: 'window' }).then(list => list.forEach(c => { if (!skip.includes(c.id)) c.postMessage({ type: 'nm-shell-updated' }); }));
        }
      } else if (cached && !servedNet && isAuth(res)) {
        // Access 세션 만료 추정 + 저장본을 띄운 경우만(3s 초과 폴백) — 캐시는 안 덮고(로그인 페이지 오염 방지) 열린 페이지에 통지.
        //    로그인 리다이렉트를 그대로 넘긴 진입은 통지 안 함 = 떠나는 옛 페이지의 nosw 재진입이 딥링크 내비게이션과 경합하던 것 차단(평의회260929 #2-1·#5-1)
        self.clients.matchAll({ type: 'window' }).then(list => list.forEach(c => c.postMessage({ type: 'nm-auth-stale' })));
      }
    }).catch(() => {});
    event.waitUntil(saveP);
    if (cached) {   // 진입 = 네트워크 우선(운영자 260929 「사이트 접속 시 캐시 무시하는 강제 새로고침 · 컨트롤 쉬프트 알 개념」) — 종전엔 명시적 새로고침(Ctrl+R·당겨서 · 260720 F6)·알림 PICK 진입(act · 260924)만 네트워크 우선이었고 평소 진입은 캐시 즉시(SWR) = 배포 뒤 첫 진입이 직전판이라 「고쳤는데 안 뜸」이 반복됐다(260929 실측)
      const head = await Promise.race([netRes.catch(() => null), sleep(3000 - (Date.now() - t0))]);   // 첫 응답 3s 캡 = 서버가 살아 있나(본문 전체가 아니라 응답 머리 기준 · 느린 폰 회선에서 2.5MB 본문 때문에 옛 셸로 떨어지던 것 차단 · 평의회260929 #1-3·#3-1·#8-1)
      if (isAuth(head)) { decide(true); return head; }   // Access 만료 = 그대로 넘겨 로그인 화면(옛 셸에 갇혀 목록이 비는 것 차단)
      if (head && head.ok && head.type === 'basic' && !head.redirected) {
        const res = await Promise.race([netP.catch(() => null), sleep(10000 - (Date.now() - t0))]);   // 응답이 왔으면 본문은 10s(요청 시작 기준)까지 기다린다 = 최신 우선
        if (res && netIntact) { decide(true); return res; }   // 온전한 최신 = 즉시(Ctrl+Shift+R 과 같은 결과)
      }
      decide(false); return cached;   // 3s 무응답(오프라인·지연)·서버 오류(5xx·404)·본문 10s 초과·잘린 본문 = 저장본(깨진 앱·오류 화면 방지 · 갱신은 백그라운드 지속 → 새 버전 통지)
    }
    decide(true);
    return netP.catch(() => Response.error());                              // 첫 방문 = 네트워크 그대로
  })());
});
// ── 알림 아이콘 테마 적응(운영자 260727 "배경이 투명이 아니라 색이 묻어나온다 · 어두운 테마엔 반대색") ──
// ⓐ 배경 투명 = 알림판 색이 그대로 비쳐 검은 판이 안 뜬다. 78% 여백은 유지 → 크롬 안드로이드 원형 크롭에
//    잘리는 픽셀 0.00%(실측). 구 maskable판(78% on #000)이 '색 묻어남'의 원인이었다.
// ⓑ 테마 짝 = favicon-globe-260724.svg 의 @media(prefers-color-scheme) 매핑을 그대로 계승
//    (라이트 = globe-blue 파랑 / 다크 = globe-sig 시그니처). 밝은 알림판엔 진한 파랑, 어두운 알림판엔 형광 —
//    어느 쪽이든 배경과 반대 명도로 떠서 대비가 산다.
// ⚠ SW에는 matchMedia가 없다 = OS 테마를 스스로 못 본다. 페이지가 message로 1비트를 넘겨주고(index.html
//    _sendTheme) 여기서 Cache에 적재 → push 때 읽는다. SW는 이벤트마다 재시작되므로 메모리 변수는 못 쓴다.
// 기본값 = 다크(앱 자체가 다크 UI · 통지 도착 전 첫 알림도 어긋나지 않게).
const PREF_CACHE = 'nm-pref-v1', THEME_KEY = '/__nm_theme';
// ── 알림 종류별 아이콘(운영자 260727 "알림 종류별로 카테고라이징해서 로고를 다르게" · 선택 = 「5종 · 같은 지구본 + 색만」) ──
// 값 = 파일명 조각(''이면 위 브랜드 기본판). 색은 index :root 토큰 의미축 계승 — brk=--danger · make=--accent(기본)
// · sys=--warn · trend=--info · kw=--cat-tech(보라 = 뷰어 키워드 알림 축과 동일 토큰 · 운영자 260818 — 구 test[--mut] 슬롯 대체
//   = 연결 테스트는 기본판 폴백으로). 에셋 생성 = shared/build_notif_icons.py(손편집 금지 · D2-1).
// 모르는 kind·미지정 = 기본판 폴백 = 구 발송 경로(kind 없는 워크플로) 무손상.
const NOTIF_ICON = { brk: 'brk', make: 'make', sys: 'sys', trend: 'trend', kw: 'kw', iss: 'iss' };
function iconFor(kind, dark) {
  const t = dark ? 'sig' : 'blue', k = NOTIF_ICON[kind] || '';
  return `/assets/brand/icon-notif-${k ? k + '-' : ''}${t}-512-260727.png`;
}
async function readThemeDark() {
  try { const c = await caches.open(PREF_CACHE), r = await c.match(THEME_KEY); return r ? (await r.text()) !== 'light' : true; }
  catch (_) { return true; }
}
self.addEventListener('message', event => {
  const d = event.data || {};
  if (d.type === 'nm-pickreq-take') { event.waitUntil(takePickReqs().then(list => { try { event.ports[0].postMessage(list); } catch (_) {} })); return; }
  if (d.type !== 'nm-theme') return;
  event.waitUntil(caches.open(PREF_CACHE)
    .then(c => c.put(THEME_KEY, new Response(d.dark ? 'dark' : 'light')))
    .catch(() => {}));
});

// ── 알림 PICK 요청 보관(운영자 260924 «푸시에서 바로 PICK» · 검토 반영) — 요청을 탭 주소에만 실으면 앱이 뜨는 사이
//    다른 알림 탭·당겨서 새로고침이 그 탭을 갈아치워 PICK이 조용히 사라진다. SW가 요청을 캐시에 적재하고 페이지가 가져간다
//    (가져가며 지움 = 두 탭 이중 발사 0). 페이지는 주소 쿼리만으로는 절대 발사하지 않는다(외부 링크 무확인 과금 차단).
const PICK_REQ = '/__nm_pickreq/', PICK_REQ_TTL = 4 * 3600e3;
async function savePickReq(r) {
  const c = await caches.open(PREF_CACHE);
  await c.put(PICK_REQ + Date.now() + '-' + Math.random().toString(36).slice(2, 8), new Response(JSON.stringify(r)));
}
async function takePickReqs() {
  const c = await caches.open(PREF_CACHE), out = [];
  for (const k of await c.keys()) {
    if (!new URL(k.url).pathname.startsWith(PICK_REQ)) continue;
    const res = await c.match(k);
    if (!(await c.delete(k)) || !res) continue;
    try { const r = await res.json(); if (r && r.brk && Date.now() - (r.ts || 0) < PICK_REQ_TTL) out.push(r); } catch (_) {}
  }
  return out;
}

self.addEventListener('push', event => {
  if (!isCanonHost()) { event.waitUntil(selfDestructIfStale()); return; }   // 좀비 SW = 알림 억제 + 자기소멸(중복 차단)
  let d = {};
  try { d = event.data ? event.data.json() : {}; } catch { d = { body: event.data && event.data.text() }; }
  const title = d.title || '🚨 긴급 속보';
  const opts = {
    body: d.body || '',
    badge: d.badge || '/assets/brand/badge-260723.png',   // 상태바 배지 = 흑백+투명 실루엣(N) — 불투명 컬러는 안드로이드가 흰 네모로 칠함 · 버전도장(260723) = immutable 캐시 편입

    tag: d.tag || 'nomute-breaking',          // 같은 tag = 교체(중복 알림 안 쌓임)
    data: { url: d.url || '/', kind: d.kind || '', pick: d.pick || '' },   // kind = PICK 사유(긴급/이슈/급상승) 판별용 · pick = 본문 목적지와 별개인 PICK 딥링크(급상승 = 본문 구글·PICK 관련 뉴스)
    lang: 'ko',
  };
  // 소리·진동(운영자 260819 «웹 푸시는 오는데 소리나 진동이 안 나는건» · 발송기가 긴급·이슈에만 실어 보낸다).
  // ⚠ 서버가 안 보낸 종류엔 이 두 키가 아예 없다 = 제작 완료·시스템·트렌드·키워드는 종전대로 조용(회귀 0).
  // ⚠ renotify 는 tag 가 있어야 유효하다(우리는 항상 준다) — 같은 묶음표로 교체될 때도 다시 울려서
  //    뒤에 온 긴급이 앞 알림을 **조용히 덮는 것**을 막는다(손목에서 놓치는 축).
  // ⚠ 이건 요청이지 보장이 아니다 — 안드로이드 알림 채널이 무음·중요도 낮음이면 그쪽이 이긴다.
  if (Array.isArray(d.vibrate) && d.vibrate.length) opts.vibrate = d.vibrate;
  if (d.renotify) opts.renotify = true;
  // 알림 PICK 버튼(운영자 260924 «푸시에서 바로 PICK») — 발송기가 긴급·이슈에만 싣는다 · 버튼 미지원 기기(iOS 등)는 무시 = 본문 탭 종전대로.
  if (Array.isArray(d.actions)) opts.actions = d.actions.filter(a => a && a.action === 'pick' && typeof a.title === 'string').slice(0, 1);
  event.waitUntil((async () => {
    opts.icon = d.icon || iconFor(d.kind, await readThemeDark());   // 페이로드 icon 지정이 최우선 · 없으면 {종류 × 저장된 테마} 짝 선택
    return self.registration.showNotification(title, opts);
  })());
});

// ── 정본 화면 표식 제거(260821 · 짝 = .github/scripts/push_send.py NM_CANON_Q) ──
// 서버가 우리 화면 딥링크에 `nmv=1`을 붙인다 — 옛 화면 SW(8월 13일 배포 · origin을 안 보고 경로·쿼리·해시만
// 대조해 옛 탭에 포커스하던 것)가 「같은 탭」이라 오판하는 경로를 구조적으로 끊기 위한 표식이다.
// 새 화면(여기)에서는 그 표식이 붙었다는 이유로 매번 불일치가 나면 안 된다 — 그러면 이미 그 화면을 보고
// 있는데도 매번 다시 불러와 「불필요한 새로고침 방지」 계약(260706)이 깨진다 → 비교 전에 표식만 걷어낸다.
const nmQs = s => { try { const p = new URLSearchParams(s || ''); p.delete('nmv'); const q = p.toString(); return q ? '?' + q : ''; } catch (_) { return s || ''; } };
self.addEventListener('notificationclick', event => {
  event.notification.close();
  const raw = (event.notification.data && event.notification.data.url) || '/';
  const target = new URL(raw, self.location.origin);   // 알림이 가리키는 화면(제작완료=/thumb.html#done · 긴급=/)
  const d0 = event.notification.data || {};
  let pt = null;
  if (event.action === 'pick') { try { pt = d0.pick ? new URL(d0.pick, self.location.origin) : target; } catch (_) { pt = null; } }
  if (pt && pt.origin === self.location.origin && pt.searchParams.has('brk')) {   // PICK 버튼 = 요청 보관 → 앱이 가져가 발사
    event.waitUntil((async () => {
      await savePickReq({ brk: pt.searchParams.get('brk'), bl: pt.searchParams.get('bl') || '', kind: d0.kind || '', ts: Date.now() });
      const list = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
      const app = list.find(c => { try { const u = new URL(c.url); return u.origin === self.location.origin && SHELL_PATHS.includes(u.pathname); } catch (_) { return false; } });
      if (app) { try { app.postMessage({ type: 'nm-pickreq' }); } catch (_) {} if ('focus' in app) return app.focus(); }   // 열린 앱 = 새로고침 없이 처리(작업 중 입력·도구 보존)
      if (self.clients.openWindow) return self.clients.openWindow(pt.origin + '/?act=pick');
    })());
    return;
  }
  event.waitUntil((async () => {
    // 0) 남의 사이트(우리 화면이 아닌 곳)면 **무조건 새 창**(운영자 260819 «검색한 구글 창으로 · 새창으로»).
    //    ⚠ 아래 2)를 그대로 타면 열려 있던 우리 앱 탭이 그 주소로 **갈아치워진다** = 앱이 사라진다.
    //    급상승 알림이 구글 검색 결과를 가리키게 되면서 생긴 자리 — 우리 화면 딥링크(상대경로)는 종전 경로 그대로.
    if (target.origin !== self.location.origin) {
      if (self.clients.openWindow) return self.clients.openWindow(target.href);
      return;
    }
    const list = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
    // 1) 이미 타깃 화면(경로+쿼리+해시 일치)에 있는 탭이면 그냥 포커스(불필요한 새로고침 방지).
    //    ⚠️ 쿼리(search)까지 비교해야 함 — 요약 딥링크(/?a=stem)는 쿼리가 유일 구별자라, 쿼리 무시 시
    //    루트(/)에 열린 탭이 '일치'로 오판돼 focus만 하고 navigate를 안 해 딥링크가 안 열렸음(분신술 2번 발견).
    for (const c of list) {
      try { const u = new URL(c.url); if (u.pathname === target.pathname && nmQs(u.search) === nmQs(target.search) && u.hash === target.hash && 'focus' in c) return c.focus(); } catch (_) {}
    }
    // 2) 열린 탭이 있으면 그 탭을 타깃으로 *이동*시켜 제작 화면을 보여줌(과거: 무조건 포커스만 → 옛 화면/모달에 머묾)
    for (const c of list) {
      if ('navigate' in c && 'focus' in c) {
        try { await c.focus().catch(() => {}); const nc = await c.navigate(target.href); return nc || c; } catch (_) { /* navigate 불가 → 새 창 폴백 */ }   // 앞으로 먼저(탭 권한 = focus 몫 · navigate 는 네트워크 우선이라 최대 수 초 · 평의회260929 #3-4·#5-2)
      }
    }
    // 3) 열린 탭 없음 → 새 창
    if (self.clients.openWindow) return self.clients.openWindow(target.href);
  })());
});

// 구독 로테이션 자가치유(운영자 260707 "ON 해놔도 어느 순간 OFF") — 브라우저(FCM)가 push 구독을 만료·교체하면
//   이 이벤트가 오는데 미처리 시 구독이 조용히 죽어 다음 진입 때 OFF로 보임(표준 원인). 여기서 즉시 재구독+서버 저장.
//   VAPID_PUB = index.html:VAPID_PUB와 짝(키 교체 시 두 곳 동시 갱신).
const VAPID_PUB = 'BORNTh3cNd05vsxi2fZ-BykxM0NwKGTvIETz81g757RVFL6cDu29aAv5I7uit0WbGOmiZ4hlyMOEvb8B2HptU-I';
function b64ToU8(s) {
  const pad = '='.repeat((4 - s.length % 4) % 4);
  const raw = atob((s + pad).replace(/-/g, '+').replace(/_/g, '/'));
  const u8 = new Uint8Array(raw.length);
  for (let i = 0; i < raw.length; i++) u8[i] = raw.charCodeAt(i);
  return u8;
}
self.addEventListener('pushsubscriptionchange', event => {
  if (!isCanonHost()) { event.waitUntil(selfDestructIfStale()); return; }   // 비정본 = 재구독 금지(좀비 부활 봉합 · push 가드와 대칭 · 평의회 3·4)
  event.waitUntil((async () => {
    try {
      const sub = await self.registration.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: b64ToU8(VAPID_PUB) });
      const r = await fetch('api/push', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ action: 'subscribe', subscription: sub.toJSON() }) }).catch(() => null);
      if (!r || !r.ok) { await sub.unsubscribe().catch(() => {}); return; }   // 서버 무등록 구독을 남기면 pushHeal이 「살아있음」으로 오판 = 알림 영구 무착(260923 · 앱 닫힘 중 발화 = Access 만료 확률 최고) → 지워야 다음 진입 heal이 재구독
      const old = event.oldSubscription;   // 옛 endpoint = 서버에서 정리(죽은 구독 잔존 방지 · 미지원 브라우저면 undefined = 스킵)
      if (old) await fetch('api/push', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ action: 'unsubscribe', subscription: old.toJSON() }) }).catch(() => {});
    } catch (e) { /* 재구독 실패(권한 회수 등) = 다음 앱 진입 시 pushHeal이 재시도 */ }
  })());
});

self.addEventListener('install', () => self.skipWaiting());           // 새 sw 즉시 활성
self.addEventListener('activate', event => event.waitUntil((async () => {
  if (await selfDestructIfStale()) return;                             // 비정본 origin이면 캐시 정리 대신 즉시 자기소멸
  const keys = await caches.keys();                                    // 구버전 셸 캐시 청소(SHELL_CACHE 버전업 대비)
  await Promise.all(keys.filter(k => k.startsWith('nm-shell-') && k !== SHELL_CACHE).map(k => caches.delete(k)));
  await self.clients.claim();
})()));
