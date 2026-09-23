// Cloudflare Pages Function — candidates.json 라이브 서빙(빌드 우회).
// scrape 가 main 에 커밋한 viewer/candidates.json 을 GitHub 에서 직접 읽어 반환 →
// 페이지 재빌드(Cloudflare 500/월 한도) 없이 수집함이 최신. 15분 수집이 화면에 바로 반영됨.
// env: GH_TOKEN(있으면 contents API=최신), 없으면 raw(공개·~5분 캐시) 폴백.
//
// ⚠ 순서가 곧 계약이다(260816 실사고 2차 봉합 · 운영자 「그냥 최신 기사가 계속 꽂혀야 되는데」).
//   원본 = 저장소 main. R2 live/ 미러는 **원본이 안 읽힐 때만** 쓰는 보험이다.
//   ── 왜 순서를 뒤집었나
//   260815 판은 R2 를 0차에 뒀다(260814 계정 제재로 깃허브 사다리가 전멸했던 시기의 대책).
//   그 뒤 미러를 굽는 맥 레인이 08-16 08:07 KST 에 멈췄는데 「객체가 있으면 무조건 0차 승리」라
//   얼어붙은 사본이 더 신선한 저장소를 영구히 가렸다 = 화면 5시간 동결(기사가 안 들어온다).
//   1차 봉합은 「30분 넘게 낡으면 진다」는 **신선도 규칙**이었는데 그건 보장이 아니라 창이다 —
//   29분 낡은 미러도 이기므로 그 사이 착지한 수집 2회분이 화면에 안 꽂힌다(운영자 지적 = 정확).
//   → 규칙을 없애고 **원본을 먼저 본다**. 신선도 판단·유효기간 자체가 사라져 「최신이 계속
//   꽂힌다」가 규칙이 아니라 구조로 성립한다. 제재가 재발하면 깃허브가 실패하고 그때
//   자동으로 미러로 내려가므로 보험은 그대로 산다(같은 파일, 순서만 뒤).
// ── 전송량(260924 운영자 「추천 순서대로」 ⑨ 화면 무게) — 열린 화면이 1분마다 ~950KB(압축 ~150KB)를 통째로 다시 받았다(시간당 ~9MB).
//    내용 지문(ETag)을 달아 브라우저가 max-age 만료 뒤 If-None-Match 로 재검증하면 **바뀐 게 없을 때 304(본문 0)**.
//    수집·판정 커밋은 15분에 몇 번뿐이라 대부분의 폴이 304가 된다. 지문 = 본문 SHA-1 앞 20자(원본·미러 공통 · 소스가 달라도 같은 내용이면 같은 지문).
async function etagOf(body) {
  const d = await crypto.subtle.digest('SHA-1', new TextEncoder().encode(body));
  return '"' + [...new Uint8Array(d)].map(b => b.toString(16).padStart(2, '0')).join('').slice(0, 20) + '"';
}
async function reply(request, body, headers) {
  const etag = await etagOf(body);
  const inm = (request && request.headers && request.headers.get('if-none-match')) || '';
  if (inm && inm.split(',').map(x => x.trim().replace(/^W\//, '')).includes(etag)) return new Response(null, { status: 304, headers: { ...headers, etag } });
  return new Response(body, { status: 200, headers: { ...headers, etag } });
}

export async function onRequestGet({ env, request }) {
  const H = { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'public, max-age=60' };
  // ── 1차: 원본(저장소 main) — 여기가 항상 최신이다.
  const tries = [];
  if (env.GH_TOKEN) tries.push([
    'https://api.github.com/repos/nomutefb/editor/contents/viewer/candidates.json?ref=main',
    { authorization: `Bearer ${env.GH_TOKEN}`, accept: 'application/vnd.github.raw', 'user-agent': 'nomute-viewer' },
  ]);
  tries.push([
    'https://raw.githubusercontent.com/nomutefb/editor/main/viewer/candidates.json',
    { 'user-agent': 'nomute-viewer' },
  ]);
  for (const [url, headers] of tries) {
    try {
      const r = await fetch(url, { headers, cf: { cacheTtl: 30, cacheEverything: true } });
      if (r.ok) {
        const body = await r.text();
        JSON.parse(body);   // 유효 JSON 확인 — 깨진 응답이면 throw → 다음 소스
        return reply(request, body, { ...H, 'x-nm-src': 'gh' });
      }
    } catch { /* 다음 소스 */ }
  }
  // ── 2차: R2 live/ 미러(맥 레인이 굽는 사본) = 원본 전멸 시의 보험.
  //    ⚠ 낡았을 수 있다 — 그래도 빈 화면보다 낫다. 얼마나 낡았는지를 헤더로 같이 낸다
  //    (x-nm-age-min = 사본 나이 · 관측이 지워지면 다음 세션이 추측으로 메운다).
  try {
    if (env.R2) {
      const o = await env.R2.get('live/candidates.json');
      if (o) {
        const b = await o.text();
        JSON.parse(b);
        const up = o.uploaded ? new Date(o.uploaded).getTime() : 0;
        const age = up ? Math.round((Date.now() - up) / 60000) : -1;
        return reply(request, b, { ...H, 'x-nm-src': 'r2', 'x-nm-age-min': String(age) });
      }
    }
  } catch { /* 낼 게 없다 */ }
  return new Response('[]', { status: 200, headers: { ...H, 'x-nm-src': 'none' } });
}
