// Cloudflare Pages Function — candidates.json 라이브 서빙(빌드 우회).
// scrape 가 main 에 커밋한 viewer/candidates.json 을 GitHub 에서 직접 읽어 반환 →
// 페이지 재빌드(Cloudflare 500/월 한도) 없이 수집함이 최신. 15분 수집이 화면에 바로 반영됨.
// env: GH_TOKEN(있으면 contents API=최신), 없으면 raw(공개·~5분 캐시) 폴백.
export async function onRequestGet({ env }) {
  const H = { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'public, max-age=60' };
  // ── 0차: R2 live/ 미러(맥 5분 레인이 매 회차 업로드 · 깃허브 무풍) — 260815 코워크.
  //    왜: 260814 계정 플래그로 아래 깃허브 사다리(contents·raw)가 간헐/전멸 → 화면 동결.
  //    R2 는 우리 계정 자산이라 외부 제재 무풍 = 수집함 신선도의 새 정본 경로. 실패 시 기존 사다리 그대로.
  // ⚠ 신선도 게이트 = 260816 실사고 봉합. 구판은 「객체가 있으면 무조건 0차 승리」라
  //    맥 레인이 멈춘 순간(실측 08-16 08:07 KST 정지) 그 낡은 미러가 **더 신선한 깃허브를
  //    영구히 가렸다** — 저장소 main 은 12:40 KST 까지 정상 수집(Actions 성공)인데
  //    화면만 5시간 동결 = 「기사가 안 들어온다」의 실체. 증상이 「빈 화면」이 아니라
  //    「옛 기사만 보임」이라 로그·에러 어디에도 안 남고 운영자 눈이 유일한 검출기였다.
  //    → 미러는 **신선할 때만** 이긴다. 낡았으면 깃허브가 이기고, 깃허브가 다 죽으면
  //    그때 낡은 미러라도 낸다(빈 배열보다 낫다 = 종전 제재 상황의 보험은 그대로 산다).
  const FRESH_MS = 30 * 60 * 1000;   // 수집 주기 15분 + 여유 · 이보다 낡으면 미러를 못 믿는다
  let stale = null;                  // 낡은 미러 본문 = 최후의 보루
  try {
    if (env.R2) {
      const o = await env.R2.get('live/candidates.json');
      if (o) {
        const b = await o.text();
        JSON.parse(b);               // 유효 JSON 확인
        const up = o.uploaded ? new Date(o.uploaded).getTime() : 0;
        const age = up ? Date.now() - up : Infinity;
        if (age <= FRESH_MS) return new Response(b, { status: 200, headers: { ...H, 'x-nm-src': 'r2' } });
        stale = b;                   // 낡음 → 깃허브 사다리를 먼저 태운다
      }
    }
  } catch { /* 깃허브 사다리로 */ }
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
        return new Response(body, { status: 200, headers: { ...H, 'x-nm-src': 'gh' } });
      }
    } catch { /* 다음 소스 */ }
  }
  // 깃허브 사다리 전멸 → 낡은 미러라도 낸다(제재 상황의 보험 = 종전 동작 보존)
  if (stale) return new Response(stale, { status: 200, headers: { ...H, 'x-nm-src': 'r2-stale' } });
  return new Response('[]', { status: 200, headers: { ...H, 'x-nm-src': 'none' } });
}
