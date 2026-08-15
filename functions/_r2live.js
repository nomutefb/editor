// 산출 라이브 서빙 공용부(260815 코워크) — 맥 2선 잡워커가 R2에 즉시 게시한 산출을
// 뷰어가 폴링하는 **정적 경로 그대로** 배포 전에 서빙한다(뷰어 수정 0 · track.js 라이브 서빙의 일반화).
// 왜: 정적 폴링 축은 커밋→재배포(≈40초+틱 대기)를 기다려야 화면에 떴다 — 깃액션 시절 대비 지연의 몸통(운영자 260815).
// 계약: R2 히트 = no-store로 즉시 서빙 · 미스/이상 = env.ASSETS(종전 정적 자산) 폴백 = 악화 경로 0.
// 짝: 워커 [live] 스테이지(nomute_job_worker.sh — 잡 커밋 diff분을 같은 키로 PUT · viewer/ 접두 제거).
const CT = {
  md: 'text/markdown; charset=utf-8', json: 'application/json; charset=utf-8',
  txt: 'text/plain; charset=utf-8', log: 'text/plain; charset=utf-8',
  srt: 'text/plain; charset=utf-8', vtt: 'text/vtt; charset=utf-8',
  jpg: 'image/jpeg', jpeg: 'image/jpeg', png: 'image/png', webp: 'image/webp',
  mp4: 'video/mp4', mp3: 'audio/mpeg', wav: 'audio/wav', m4a: 'audio/mp4',
};

export async function r2live(prefix, { request, env, params }) {
  const rel = Array.isArray(params.path) ? params.path.join('/') : String(params.path || '');
  // 경로 위생 — 세그먼트 화이트리스트(경로 탈출·인젝션 차단 · track.js crop 검증 관례 축)
  if (!rel || rel.includes('..') || !/^[A-Za-z0-9._\-/]+$/.test(rel)) return env.ASSETS.fetch(request);
  try {
    if (env.R2) {
      const o = await env.R2.get(`${prefix}/${rel}`);
      if (o) {
        const ext = rel.split('.').pop().toLowerCase();
        return new Response(o.body, {
          headers: { 'content-type': CT[ext] || 'application/octet-stream', 'cache-control': 'no-store', 'x-nomute-live': 'r2' },
        });
      }
    }
  } catch (_) { /* R2 이상 = 정적 폴백(악화 경로 0) */ }
  return env.ASSETS.fetch(request);   // 미스 = 종전 정적 자산 그대로(배포분)
}
