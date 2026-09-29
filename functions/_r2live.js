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
  mp4: 'video/mp4', mp3: 'audio/mpeg', wav: 'audio/wav', m4a: 'audio/mp4', webm: 'video/webm', mov: 'video/quicktime',
};

// 단일 구간만 푼다(bytes=a-b · a- · -n) — 여러 구간·형식 이상 = null(= Range 무시하고 200 전량 · RFC 9110 허용)
//   ⚠ 원문 헤더를 R2 에 그대로 넘기면 R2 가 무효·범위 밖 헤더를 조용히 전량으로 바꿔 주는데 우리는 그걸 206 으로 내보냈다(평의회 260929 workerd 실측).
export function parseRange(h) {
  const m = /^bytes=(\d*)-(\d*)$/.exec(String(h || '').trim());
  if (!m || (m[1] === '' && m[2] === '')) return null;
  if (m[1] === '') { const n = +m[2]; return n > 0 ? { suffix: n } : null; }
  const a = +m[1];
  if (m[2] === '') return { offset: a };
  const b = +m[2];
  return b >= a ? { offset: a, length: b - a + 1 } : null;
}

export async function r2live(prefix, { request, env, params }) {
  const rel = Array.isArray(params.path) ? params.path.join('/') : String(params.path || '');
  // 경로 위생 — 세그먼트 화이트리스트(경로 탈출·인젝션 차단 · track.js crop 검증 관례 축)
  if (!rel || rel.includes('..') || !/^[A-Za-z0-9._\-/]+$/.test(rel)) return env.ASSETS.fetch(request);
  const key = `${prefix}/${rel}`;
  const rr = parseRange(request.headers.get('range'));
  try {
    if (env.R2) {
      // 구간 요청(Range) = 206(260929 «아이폰 진짜 투명 재생») — 아이폰 사파리는 영상을 **구간 요청으로만** 재생한다
      //   (첫 요청 bytes=0-1 → 206이 아니면 재생 거부). 스택 알파 미리보기(nm-alpha.js)는 WebGL 보안 규칙상 같은 출처라야 해서
      //   이 경로로 받는다 = 여기가 구간을 못 주면 아이폰에서만 조용히 안 나온다. Range 없는·못 푸는 요청 = 종전 그대로(200 전량).
      let o;
      try {
        o = await env.R2.get(key, rr ? { range: rr } : undefined);
      } catch (e) {
        if (!rr) throw e;
        const hd = await env.R2.head(key);   // 범위 밖 구간 = R2 가 던진다 → 객체가 있으면 416(정적 폴백으로 새면 SPA index.html 이 영상 자리에 간다)
        if (hd) return new Response(null, { status: 416, headers: { 'content-range': `bytes */${hd.size}`, 'cache-control': 'no-store' } });
        throw e;
      }
      if (o) {
        const ext = rel.split('.').pop().toLowerCase();
        const h = { 'content-type': CT[ext] || 'application/octet-stream', 'cache-control': 'no-store', 'x-nomute-live': 'r2', 'accept-ranges': 'bytes' };
        const r = rr && o.range;
        if (r && typeof o.size === 'number' && o.size > 0) {
          const off = 'suffix' in r ? Math.max(0, o.size - r.suffix) : (r.offset || 0);
          const len = Math.min(o.size - off, 'suffix' in r ? o.size - off : (typeof r.length === 'number' ? r.length : o.size - off));
          if (off >= o.size || len <= 0) return new Response(null, { status: 416, headers: { 'content-range': `bytes */${o.size}`, 'cache-control': 'no-store' } });
          h['content-range'] = `bytes ${off}-${off + len - 1}/${o.size}`;
          h['content-length'] = String(len);
          return new Response(o.body, { status: 206, headers: h });
        }
        return new Response(o.body, { headers: h });   // Range 없음·0바이트 = 200 전량
      }
    }
  } catch (_) { /* R2 이상 = 정적 폴백(악화 경로 0) */ }
  return env.ASSETS.fetch(request);   // 미스 = 종전 정적 자산 그대로(배포분)
}
