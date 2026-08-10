// Cloudflare Pages Function — R2 직업로드(대용량 · 편집기/변환 공용). GitHub 경유(base64 40M자 = 30MB 병목)를 대체.
// 요구: Pages 대시보드 → Settings → Bindings → R2 bucket, 변수명 R2(러너 시크릿 R2_BUCKET과 같은 버킷).
//   바인딩 없음 = GET {ok:false} → 뷰어가 기존 30MB base64 경로로 자동 폴백(회귀 0 · 머지만으론 라이브 무영향).
// 흐름: POST{action:create,name,size} → {key,uploadId,part} → PUT ?key&uploadId&n=1..64(원시 바디 · 32MB 균일 조각)
//   → POST{action:complete,parts} → 러너가 aws s3 cp로 회수(**읽기만** — 수정 0).
//   ⚠ (260810) up_src/* 는 **일회용이 아니다** — 잡 끝 즉시 삭제를 폐지하고 나이 기준 청소로 바꿨다(정본 = shared/r2_upsrc_gc.sh · TTL 24h).
//   같은 영상으로 두 번째·세 번째 작업을 걸 때 전체 재업로드가 없어진다(운영자 260810 "한번 올린거 바로 휘발시키지말고 냅둬봐").
// 보안: 키 = 서버 발급 up_src/<id>.<ext>만(정규식 강제 = ly_out 등 타 키 덮어쓰기 차단) · Access 게이트 뒤(뷰어 동일) ·
//   총량 2GB 캡(기틀 캡 — 완화 = 운영자 확인 · 실질 제한은 각 도구의 길이 캡). 조각 32MB = 워커 메모리(128MB) 안전권.
// 잔재 수명: 미완결 멀티파트 = R2 기본 수명규칙이 7일에 자동 중단(공식 문서 확인 · 평의회9) · 완결됐지만 미소비된 고아 객체 =
//   뷰어가 delete 액션으로 즉시 정리(대체·URL 발사 시) + 백스톱 = 잡마다 도는 shared/r2_upsrc_gc.sh(24h 초과분 삭제 ·
//   운영자 조치 0 = 대시보드 수명규칙을 안 걸어도 고아가 안 쌓인다 · 규칙을 따로 걸어도 둘 다 "나이 든 것만"이라 충돌 0).
const KEY_RE = /^up_src\/\d{12}-[a-f0-9]{6}\.(mp4|mov|m4v|webm|mkv|avi|mp3|m4a|wav|ogg|aac|flac|jpg)$/;   // +오디오 6종(260722 song 보이스 학습 R2 편입) · +jpg(260810 번역카드 원본 사진 = 러너가 모델에게 직접 보여줄 소스 · dispatch inputs 64KB 상한을 b64로는 못 넘어 R2 경유 = edit r2key 정본 문법) — 각 API(edit·conv·framethumb=영상만 · voice=오디오)가 자기 확장자 셋을 재검증 = 교차 오용 차단
const CHUNK = 32 * 1024 * 1024;             // 조각 크기 — R2 멀티파트는 마지막 외 균일 크기 요구(≥5MB)
const MAX_TOTAL = 2 * 1024 * 1024 * 1024;   // 2GB(= 64조각) — 4K 10분(길이 캡)도 여유

const json = (o, s = 200) => new Response(JSON.stringify(o), { status: s, headers: { 'content-type': 'application/json' } });

export async function onRequestGet({ env }) {   // 기능 감지(뷰어 세션 1회 핑) — 바인딩 없으면 기존 경로 폴백
  return json({ ok: !!env.R2, max: MAX_TOTAL, part: CHUNK });
}

export async function onRequestPost({ request, env }) {
  if (!env.R2) return json({ error: '대용량 업로드 미설정 — Pages에 R2 바인딩(변수명 R2) 필요' }, 501);
  let b;
  try { b = await request.json(); } catch { return json({ error: '잘못된 요청' }, 400); }
  const act = String(b.action || '');

  if (act === 'create') {
    const size = Number(b.size) || 0;
    if (size < 1 || size > MAX_TOTAL) return json({ error: '파일은 2GB까지 — 더 크면 구간을 잘라서 올려줘' }, 400);
    const ext = (String(b.name || '').match(/\.(mp4|mov|m4v|webm|mkv|avi|mp3|m4a|wav|ogg|aac|flac|jpg)$/i) || ['.mp4'])[0].toLowerCase();   // +오디오 6종(260722 · KEY_RE 짝) · +jpg(260810 · 위 짝)
    const id = new Date(Date.now() + 9 * 3600e3).toISOString().replace(/[^0-9]/g, '').slice(2, 14) + '-' + crypto.randomUUID().slice(0, 6);   // KST(+9h · pick.js 규칙)
    const key = `up_src/${id}${ext}`;
    try {
      const mp = await env.R2.createMultipartUpload(key);
      return json({ key, uploadId: mp.uploadId, part: CHUNK });
    } catch (e) { return json({ error: '업로드 시작 실패 — 재시도 (' + String(e && e.message || e).slice(0, 120) + ')' }, 502); }
  }

  const key = String(b.key || ''), uploadId = String(b.uploadId || '');
  if (!KEY_RE.test(key) || /\s/.test(key)) return json({ error: '잘못된 키' }, 400);   // \s = JS $의 후행 개행 허용 봉합(평의회1)

  if (act === 'delete') {   // 고아 완결 객체 정리(낡은 업로드 대체·URL 발사로 미소비 키 — 평의회7 F2) · KEY_RE로 up_src/* 한정 = 타 프리픽스 불가 · uploadId 불요
    try { await env.R2.delete(key); } catch { /* 미존재 = 무해(멱등) */ }
    return json({ ok: true });
  }
  if (!uploadId) return json({ error: '잘못된 키' }, 400);   // complete/abort = 멀티파트 핸들 필수

  if (act === 'complete') {
    const parts = Array.isArray(b.parts) ? b.parts.slice(0, 64).map(p => ({ partNumber: Number(p.n), etag: String(p.etag || '') })) : [];
    if (!parts.length || parts.some(p => !Number.isInteger(p.partNumber) || p.partNumber < 1 || p.partNumber > 64 || !p.etag)) {
      return json({ error: '조각 목록이 이상해 — 다시 올려줘' }, 400);
    }
    try {
      const obj = await env.R2.resumeMultipartUpload(key, uploadId).complete(parts);
      if (obj.size > MAX_TOTAL) { await env.R2.delete(key); return json({ error: '파일은 2GB까지' }, 400); }   // 조각 산술 우회 방어
      return json({ ok: true, key, size: obj.size });
    } catch (e) { return json({ error: '업로드 마무리 실패 — 다시 올려줘 (' + String(e && e.message || e).slice(0, 120) + ')' }, 502); }
  }

  if (act === 'abort') {
    try { await env.R2.resumeMultipartUpload(key, uploadId).abort(); } catch { /* 이미 정리됨 = 무해 */ }
    return json({ ok: true });
  }

  return json({ error: '알 수 없는 요청' }, 400);
}

export async function onRequestPut({ request, env }) {   // 조각 본체(원시 바디) — ?key=&uploadId=&n=1..64
  if (!env.R2) return json({ error: '대용량 업로드 미설정' }, 501);
  const u = new URL(request.url);
  const key = u.searchParams.get('key') || '', uploadId = u.searchParams.get('uploadId') || '';
  const n = Number(u.searchParams.get('n'));
  if (!KEY_RE.test(key) || /\s/.test(key) || !uploadId || !Number.isInteger(n) || n < 1 || n > 64) return json({ error: '잘못된 조각 요청' }, 400);
  let buf;
  try { buf = await request.arrayBuffer(); } catch { return json({ error: '조각 수신 실패 — 다시' }, 400); }
  if (!buf.byteLength || buf.byteLength > CHUNK) return json({ error: '조각 크기 초과' }, 413);
  try {
    const p = await env.R2.resumeMultipartUpload(key, uploadId).uploadPart(n, buf);
    return json({ etag: p.etag, n });
  } catch (e) { return json({ error: '조각 업로드 실패 — 다시 (' + String(e && e.message || e).slice(0, 120) + ')' }, 502); }
}
