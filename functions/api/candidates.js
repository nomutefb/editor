// Cloudflare Pages Function — candidates.json 라이브 서빙(빌드 우회).
// scrape 가 main 에 커밋한 viewer/candidates.json 을 GitHub 에서 직접 읽어 반환 →
// 페이지 재빌드(Cloudflare 500/월 한도) 없이 수집함이 최신. 15분 수집이 화면에 바로 반영됨.
// env: GH_TOKEN(있으면 contents API=최신), 없으면 raw(공개·~5분 캐시) 폴백.
export async function onRequestGet({ env }) {
  const H = { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'public, max-age=60' };
  // ── 0차: R2 live/ 미러(맥 5분 레인이 매 회차 업로드 · 깃허브 무풍) — 260815 코워크.
  //    왜: 260814 계정 플래그로 아래 깃허브 사다리(contents·raw)가 간헐/전멸 → 화면 동결.
  //    R2 는 우리 계정 자산이라 외부 제재 무풍 = 수집함 신선도의 새 정본 경로. 실패 시 기존 사다리 그대로.
  try {
    if (env.R2) {
      const o = await env.R2.get('live/candidates.json');
      if (o) { const b = await o.text(); JSON.parse(b); return new Response(b, { status: 200, headers: H }); }
    }
  } catch { /* 깃허브 사다리로 */ }
  const tries = [];
  if (env.GH_TOKEN) tries.push([
    'https://api.github.com/repos/muteno/nomute-editor/contents/viewer/candidates.json?ref=main',
    { authorization: `Bearer ${env.GH_TOKEN}`, accept: 'application/vnd.github.raw', 'user-agent': 'nomute-viewer' },
  ]);
  tries.push([
    'https://raw.githubusercontent.com/muteno/nomute-editor/main/viewer/candidates.json',
    { 'user-agent': 'nomute-viewer' },
  ]);
  for (const [url, headers] of tries) {
    try {
      const r = await fetch(url, { headers, cf: { cacheTtl: 30, cacheEverything: true } });
      if (r.ok) {
        const body = await r.text();
        JSON.parse(body);   // 유효 JSON 확인 — 깨진 응답이면 throw → 다음 소스
        return new Response(body, { status: 200, headers: H });
      }
    } catch { /* 다음 소스 */ }
  }
  return new Response('[]', { status: 200, headers: H });
}
