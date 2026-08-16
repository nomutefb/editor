// Cloudflare Pages Function — gen_out/resize.json 라이브 서빙(빌드 우회 · genihist.js 정본 문법 사본).
// 왜(운영자 260816 "이거 큐잉 - ai합성 지연문제 해결해줘"): 비율 재구성·AI 합성(img-resize.yml) 산출 인덱스(resize.json)는
// 러너가 main에 커밋하지만, 뷰어(thumb rszLoad)는 그 **정적 사본**을 폴링했다 → 그림은 R2에 이미 올라와 살아 있는데
// 화면의 완료 판정만 Pages 재빌드(커밋당 1회 FIFO·46s · 봇 커밋 밀리면 분 단위)를 기다렸다 = 형제 탭(카드 제작·편집 =
// R2 즉시)과 달리 이 축만 「제작중 → 지연」으로 오래 앉아 있던 비대칭의 서버 절반. 클라가 이 응답을 먼저 보고 즉시 완료 처리한다.
// ⚠ 캐시 TTL = 10s(genihist 60s와 다른 값 = **이 응답은 이력이 아니라 완료 신호**라 캐시가 곧 지연 · 폴 주기 25s보다 짧게).
// env: GH_TOKEN(있으면 contents API=최신), 없으면 raw(공개·~5분 캐시) 폴백 — candidates.js·genihist.js 동문.
export async function onRequestGet({ env }) {
  const H = { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'public, max-age=10' };
  const tries = [];
  if (env.GH_TOKEN) tries.push([
    'https://api.github.com/repos/nomutefb/editor/contents/viewer/gen_out/resize.json?ref=main',
    { authorization: `Bearer ${env.GH_TOKEN}`, accept: 'application/vnd.github.raw', 'user-agent': 'nomute-viewer' },
  ]);
  tries.push([
    'https://raw.githubusercontent.com/nomutefb/editor/main/viewer/gen_out/resize.json',
    { 'user-agent': 'nomute-viewer' },
  ]);
  for (const [url, headers] of tries) {
    try {
      const r = await fetch(url, { headers, cf: { cacheTtl: 10, cacheEverything: true } });
      if (r.ok) {
        const body = await r.text();
        JSON.parse(body);   // 유효 JSON 확인 — 깨진 응답이면 throw → 다음 소스
        return new Response(body, { status: 200, headers: H });
      }
    } catch { /* 다음 소스 */ }
  }
  return new Response('[]', { status: 200, headers: H });
}
