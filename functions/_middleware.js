// pages.dev 접속을 커스텀 도메인(apps.nomute.kr)으로 강제 리다이렉트.
// 왜: production `editor-6dw.pages.dev`(및 미리보기 `*.pages.dev`)는 Cloudflare Access가
//     기본으로 막지 못한다(서브도메인만 보호, 메인 도메인 미보호 = 알려진 제약) → 비번(Access) 우회 구멍.
// 이 미들웨어가 서버(엣지)에서 pages.dev로 오는 모든 요청을 정본 도메인으로 301 리다이렉트해
// 반드시 Access 인증을 거치게 한다(JS 끄기·시크릿·타 기기 우회 불가). 정본 도메인 요청은 그대로 통과.
// + 260815 코워크 확장 2건:
//   ① 정본 도메인을 env(CANONICAL_HOST)로 — 백업 판이 같은 미들웨어를 그대로 쓴다(미설정 = 기존 동일).
//   ② 제작 POST 안전망 — 깃허브 축 사망으로 함수가 5xx(JSON·CF HTML 불문)를 내면 요청 본문을
//      R2 queue/jobs/ 에 착지시키고 접수 성공을 돌려준다(맥 잡 워커가 소비 = 요청 유실 0 계약).
//      GET/읽기 표면 비대상 · 5xx 미만(정상·4xx)은 그대로 통과 = 기존 동작 불변.
const JOB_API = new Set(['pick', 'make-cards', 'genimg', 'moreimg', 'imgedit', 'thumbredo', 'thumb',
  'comp', 'compose', 'edit', 'vidl', 'vidlout', 'conv', 'k', 'resize', 'upscale', 'song', 'track', 'voice',
  'sb', 'ly', 'nb', 'framethumb', 'revise', 'revise-cards', 'cards-revise', 'tr']);

// ── 진행 중 작업 공유 원장(260817 · 운영자 "하드웨어를 바꾸든, 브라우저를 바꾸든 동시간에 들어가면 제작중인 내용이 동일하게 떠야")
// 왜: 진행 중 슬롯이 **브라우저 로컬 저장소에만** 있었다(nm-jobs.js `nm_*_pend`) → 같은 사람이 폰에서 걸고 PC로 가면
//   그 작업이 화면에서 통째로 사라진다(러너는 계속 돌아 결과가 R2에 착지하는데 그 기기만 영영 모른다 = 260810 nm-jobs가
//   **한 브라우저 안**에서 고친 병의 기기 간 판). 완료분은 이미 공유 경로가 있었다(thumb-hist·?recent= R2 발견) —
//   빠져 있던 건 「지금 돌고 있는 것」 하나뿐이라 여기만 메운다.
// 자리가 이 미들웨어인 이유 = 발사 API 28종이 **전부 이 관문을 지난다**. 각 api/*.js에 1줄씩 심으면 새 레인이 조용히 빠진다
//   (이 레포가 반복해 겪은 손 목록 드리프트) · 아래 큐 안전망과 같은 JOB_API 집합을 쓰므로 둘이 같이 낡는다 = 짝이 안 맞을 수 없다.
// 계약: 발사 **성공**(200 + ok:true + id)만 기록 · 기록은 waitUntil 백그라운드(발사 응답 지연 0) · 전 경로 fail-soft.
const LIVE_PFX = 'jobs/live/';
async function putLive(env, kind, j, ctx) {
  try {
    if (!env.R2 || !j || !j.id) return;
    const id = String(j.id).slice(0, 80);
    if (!/^[A-Za-z0-9._\-/]+$/.test(id)) return;   // 키 위생(경로 탈출 차단 · _r2live 세그먼트 규칙 축)
    const rec = {
      kind, id, t0: Date.now(),
      out: typeof j.out === 'string' ? j.out.slice(0, 200) : '',
      outs: Array.isArray(j.outs) ? j.outs.slice(0, 12) : undefined,   // thumb 폴 재개 최소 상태(restorePending가 outs 없으면 안 선다)
      mode: typeof j.mode === 'string' ? j.mode.slice(0, 24) : undefined,   // song/voice/vidl = 같은 슬롯에 모드가 갈린다
    };
    const p = env.R2.put(LIVE_PFX + kind + '-' + id.replace(/\//g, '_') + '.json', JSON.stringify(rec));
    if (ctx && typeof ctx.waitUntil === 'function') ctx.waitUntil(p); else await p;
  } catch { /* 원장 실패가 발사를 못 죽인다 */ }
}

export async function onRequest(context) {
  const url = new URL(context.request.url);
  if (url.hostname.endsWith('.pages.dev')) {
    // sw.js 는 리다이렉트 제외 — 비정본 origin(pages.dev)에 남은 구 서비스워커가 '자기소멸' 업데이트를
    // 받으려면 스크립트 요청이 200이어야 한다(3xx면 브라우저가 SW 업데이트를 실패 처리 → 좀비 SW가 영영
    // 안 죽어 중복 알림 지속). sw.js 는 공개 클라이언트 코드(민감정보 없음)라 Access 우회 노출 위험 없음.
    if (url.pathname === '/sw.js') return context.next();
    url.hostname = (context.env && context.env.CANONICAL_HOST) || 'apps.nomute.kr';
    return Response.redirect(url.toString(), 301);
  }
  const m = url.pathname.match(/^\/api\/([a-z0-9-]+)\/?$/);
  if (m && JOB_API.has(m[1]) && context.request.method === 'POST' && context.env && context.env.R2) {
    let bodyText = '';
    try { bodyText = await context.request.clone().text(); } catch { /* 본문 없음도 허용 */ }
    const res = await context.next();
    if (res.status < 500) {
      // 발사 성공 = 진행 중 원장에 적립(기기·브라우저 공유 축 · 위 putLive 주석 참조).
      // ⚠ 응답은 clone으로 읽는다 — 원본 body를 소비하면 그 발사가 그 자리에서 죽는다.
      if (res.status === 200) {
        try {
          const j = JSON.parse(await res.clone().text());
          if (j && j.ok && j.id) await putLive(context.env, m[1], j, context);
        } catch { /* JSON 아님·본문 없음 = 기록 안 함(발사는 그대로 성공) */ }
      }
      return res;
    }
    try {
      const k = new Date(Date.now() + 9 * 3600e3).toISOString();   // KST 스탬프(픽 함수와 동일 규칙)
      const stamp = k.slice(2, 4) + k.slice(5, 7) + k.slice(8, 10) + '-' + k.slice(11, 13) + k.slice(14, 16) + k.slice(17, 19);
      const key = `queue/jobs/${stamp}-${m[1]}-${Math.random().toString(16).slice(2, 6)}.json`;
      await context.env.R2.put(key, JSON.stringify({ kind: m[1], ts: k, body: bodyText }));
      return new Response(JSON.stringify({ ok: true, via: 'r2-queue', kind: m[1], note: '접수됨 — 맥 레인이 처리(깃허브 정지 우회)' }),
        { status: 200, headers: { 'content-type': 'application/json' } });
    } catch { /* 큐도 죽으면 원 응답 그대로 */ }
    return res;
  }
  return context.next();
}
