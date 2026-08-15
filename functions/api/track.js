// Cloudflare Pages Function — 뷰어 트래킹 폼 → track-make 워크플로 발사(핀셋/모자이크/키잉).
// 2모드: analyze(영상 URL/업로드 → tracks.json 폴링) · render(선택 페이로드 → video.json 폴링 — 모자이크/핀셋 번인 · 키잉 알파 분리).
// 이 함수 = LLM 0콜(발사·폴링 경로만 — 캡션 콜은 워크플로 스텝 축·track-make.yml 참조). 인증·업로드(일회용 up-<id> 브랜치)·발사 골격 = ly.js 미러. env: GH_TOKEN 동일 PAT.
import { rateGate } from './_rate.js';
const REPO = 'muteno/nomute-editor';
const REF = 'main';
const GH = (token, path, method, body) => fetch(`https://api.github.com/repos/${REPO}/${path}`, {
  method,
  headers: {
    authorization: `Bearer ${token}`,
    accept: 'application/vnd.github+json',
    'user-agent': 'nomute-viewer',
    'x-github-api-version': '2022-11-28',
  },
  body: body ? JSON.stringify(body) : undefined,
});

export async function onRequestPost({ request, env }) {
  const json = (o, s = 200) => new Response(JSON.stringify(o), { status: s, headers: { 'content-type': 'application/json' } });
  if (!env.GH_TOKEN) return json({ error: '서버 미설정 — Cloudflare 환경변수 GH_TOKEN 필요' }, 500);

  let body;
  try { body = await request.json(); } catch { return json({ error: '잘못된 요청' }, 400); }
  if (!body || typeof body !== 'object' || Array.isArray(body)) return json({ error: '잘못된 요청' }, 400);   // null/비객체 본문 = body.render 역참조 500 크래시 차단(미디어 파이프 동형 가드 · 실측 260720)

  // 싼 선검증 = 게이트 앞(무효 요청이 GH GET 2콜을 안 태우게 — edit/conv와 대칭 · 검증 A4/A5) · 본검증은 아래 각 경로에 그대로(이중 방어)
  const _r0 = (body.render && typeof body.render === 'object') ? body.render : null;
  if (_r0 && !/^[0-9]{12}-[0-9a-f]{6}$/.test(String(_r0.id || '').trim())) return json({ error: '잘못된 작업 ID' }, 400);
  // ⚠ r2key 축 포함(260809 실사고) — 이 선검증이 url·fileB64만 봐서 **R2 직업로드 키로 보낸 분석 요청이 전부 400**이었다.
  //   아래 144행 본검증은 r2key를 정상으로 받는데 그 앞에서 막혀, 대용량(>28MB) 파일 분석은 track.html에서도 늘 실패했다
  //   (운영자 260809 실측 = 영상이 붙어 있는데 "영상 URL이나 파일이 필요해"). 싼 선검증이 본검증보다 **좁으면** 그 차집합이 통째로 죽는다.
  if (!_r0 && !String(body.url || '').trim() && !String(body.fileB64 || '') && !String(body.r2key || '')) return json({ error: '영상 URL이나 파일이 필요해' }, 400);
  const rl = await rateGate(GH, env.GH_TOKEN, 'track-make.yml');   // 발사 레이트리밋(렌더·분석 공통 초입 = 업로드 전 · fail-open · 260711)
  if (rl) return json({ error: rl.error }, 429);

  // ── 렌더 경로 — 기존 분석 id + 선택 페이로드(모자이크/핀셋 번인 · 키잉 알파) 재실행(분석 1회 = 렌더 N회)
  if (body.render && typeof body.render === 'object') {
    const r = body.render;
    const id = String(r.id || '').trim();
    if (!/^[0-9]{12}-[0-9a-f]{6}$/.test(id)) return json({ error: '잘못된 작업 ID' }, 400);
    const mode = r.mode === 'pinset' ? 'pinset' : r.mode === 'keying' ? 'keying' : r.mode === 'maskfx' ? 'maskfx' : r.mode === 'chroma' ? 'chroma' : 'mosaic';
    const num = (v, lo, hi) => (typeof v === 'number' && Number.isFinite(v)) ? Math.max(lo, Math.min(hi, v)) : null;
    // ── 크로마키(M3) — 대상 선택 없음(색만) · 노출 노브 = 색·강도·테두리·부드럽게(운영자 260712) · 나머지 = 서버 고정 주입 · py에서 재클램프 = 이중 방어
    if (mode === 'chroma') {
      const o = (r.opts && typeof r.opts === 'object') ? r.opts : {};
      const copts = { despill: 0.5, blend: 0.05, edge: 'high' };   // 고정 = 그린물 제거·경계 전이·테두리 우선(속도 대가 수용 — 운영자 "테두리" 우선)
      const CKC = { green: '#00FF00', blue: '#0000FF' };   // 뷰어 = 키워드만(디자인 게이트 hex 0) → 여기서 hex 해석 · 직접 hex도 허용(직접 dispatch)
      copts.color = CKC[o.color] || ((typeof o.color === 'string' && /^#[0-9a-fA-F]{6}$/.test(o.color)) ? o.color : CKC.green);
      // ⚠ 단위 봉합(260808 실측 사고) — 뷰어 강도 슬라이더는 **1~50 정수(%)** 인데 이 줄이 0.01~0.5로 클램프해서
      //   슬라이더를 어디에 두든 전부 **0.5(최대)** 로 붙었다 → 그린/블루 유사도가 극단이라 크로마키가 **화면 전체를
      //   투명하게** 지웠다(실호출 실측: similarity 0.5 = 알파 전면 0 = 빈 영상 / 0.18 = 배경만 정확히 제거).
      //   슬라이더가 죽어 있었을 뿐 아니라 크로마키 자체가 라이브에서 늘 실패였다. 1보다 크면 %로 해석해 환산한다
      //   (직접 dispatch로 0.18 같은 비율을 주는 경로도 종전 그대로 = 하위호환).
      const sraw = (typeof o.similarity === 'number' && Number.isFinite(o.similarity)) ? (o.similarity > 1 ? o.similarity / 100 : o.similarity) : null;
      const si = num(sraw, 0.01, 0.5); copts.similarity = si === null ? 0.18 : Math.round(si * 1000) / 1000;
      const ch = num(o.choke, -4, 4); copts.choke = ch === null ? 0 : Math.round(ch);
      const fe = num(o.feather, 0, 10); copts.feather = fe === null ? 1 : Math.round(fe);
      const payload = JSON.stringify({ mode, opts: copts });
      const rr = await GH(env.GH_TOKEN, 'actions/workflows/track-make.yml/dispatches', 'POST', {
        ref: REF, inputs: { id, mode: 'render', render: payload },
      });
      if (rr.status === 204) return json({ ok: true, id, out: `track_out/${id}/video.json` });
      // 발사 실패 → R2 잡 큐 착지(260815 코워크 · conv.js fail-soft 미러) — id 보존 = 뷰어 폴링 무변 · 맥 잡워커 소비.
      if (env.R2) {
        try {
          await env.R2.put(`queue/jobs/${id}-track.json`, JSON.stringify({
            kind: 'track', id, ts: new Date().toISOString(),
            inputs: { id, mode: 'render', render: payload },
          }));
          return json({ ok: true, id, out: `track_out/${id}/video.json`, via: 'r2-queue', note: '깃허브 발사 실패 — 맥 워커 큐 접수' });
        } catch { /* R2도 실패 → 종전 502(아래) */ }
      }
      return json({ error: `렌더 발사 실패 GitHub ${rr.status}: ${(await rr.text()).slice(0, 200)}` }, 502);
    }
    // ── 키잉·실루엣(M4) 경로 — keep(피사체 sid) + keepP(얼굴 단위 pid · 260710) + extra(수동 지정 {t초, x·y 정규 0..1}) · py에서 재클램프 = 이중 방어
    if (mode === 'keying' || mode === 'maskfx') {
      const keep = Array.isArray(r.keep) ? [...new Set(r.keep.filter(t => Number.isInteger(t) && t >= 1 && t <= 99))].slice(0, 4) : [];
      const keepP = Array.isArray(r.keepP) ? [...new Set(r.keepP.filter(t => Number.isInteger(t) && t >= 1 && t <= 99))].slice(0, 4) : [];   // keep 산식 미러
      const extra = [];
      if (Array.isArray(r.extra)) {
        for (const e of r.extra) {
          if (!e || typeof e !== 'object') continue;
          const t = num(e.t, 0, 90), x = num(e.x, 0, 1), y = num(e.y, 0, 1);   // 90 = py KEY_MAX_SEC 정합(평의회5) — 분석 300s 상향과 무관(키잉·실루엣 캡 불변)
          if (t !== null && x !== null && y !== null) extra.push({ t: Math.round(t * 100) / 100, x: Math.round(x * 10000) / 10000, y: Math.round(y * 10000) / 10000 });
          if (extra.length >= 4) break;
        }
      }
      if (keep.length + keepP.length + extra.length < 1) return json({ error: mode === 'maskfx' ? '가릴 피사체를 골라줘' : '남길 피사체를 골라줘' }, 400);
      if (keep.length + keepP.length + extra.length > 4) return json({ error: '피사체는 최대 4개까지야' }, 400);
      const kopts = {};
      const fe = num(r.opts && r.opts.feather, 0, 40); if (fe !== null) kopts.feather = Math.round(fe);
      const base = { mode, keep, keepP, extra, opts: kopts };
      if (mode === 'maskfx') {   // 채움 = 블록 픽셀레이트 ↔ 내장 가면(경로 아닌 프리셋명만 — py 화이트리스트와 이중)
        base.fill = r.fill === 'image' ? 'image' : 'mosaic';
        if (base.fill === 'image') base.preset = ['smile', 'black', 'heart'].includes(r.preset) ? r.preset : 'smile';
      }
      const payload = JSON.stringify(base);
      if (payload.length > 4000) return json({ error: '선택이 너무 많아 — 줄여줘' }, 400);
      const rr = await GH(env.GH_TOKEN, 'actions/workflows/track-make.yml/dispatches', 'POST', {
        ref: REF, inputs: { id, mode: 'render', render: payload },
      });
      if (rr.status === 204) return json({ ok: true, id, out: `track_out/${id}/video.json` });
      // 발사 실패 → R2 잡 큐 착지(260815 코워크 · conv.js fail-soft 미러) — id 보존 = 뷰어 폴링 무변 · 맥 잡워커 소비.
      if (env.R2) {
        try {
          await env.R2.put(`queue/jobs/${id}-track.json`, JSON.stringify({
            kind: 'track', id, ts: new Date().toISOString(),
            inputs: { id, mode: 'render', render: payload },
          }));
          return json({ ok: true, id, out: `track_out/${id}/video.json`, via: 'r2-queue', note: '깃허브 발사 실패 — 맥 워커 큐 접수' });
        } catch { /* R2도 실패 → 종전 502(아래) */ }
      }
      return json({ error: `렌더 발사 실패 GitHub ${rr.status}: ${(await rr.text()).slice(0, 200)}` }, 502);
    }
    const targets = Array.isArray(r.targets) ? [...new Set(r.targets.filter(t => Number.isInteger(t) && t >= 1 && t <= 99))].slice(0, 32) : [];
    const invert = r.invert === true;
    const names = {}, colors = {};
    if (r.names && typeof r.names === 'object') {
      for (const [k, v] of Object.entries(r.names)) {
        if (!/^[0-9]{1,2}$/.test(k)) continue;
        const nm = String(v).replace(/[\u0000-\u001f\u007f]/g, '').trim().slice(0, 24);
        if (nm) names[k] = nm;
        if (Object.keys(names).length >= 32) break;
      }
    }
    if (r.colors && typeof r.colors === 'object') {
      for (const [k, v] of Object.entries(r.colors)) {
        if (/^[0-9]{1,2}$/.test(k) && /^#[0-9a-fA-F]{6}$/.test(String(v))) colors[k] = String(v);
        if (Object.keys(colors).length >= 32) break;
      }
    }
    // 가림 범위(260710) — 'body'만 담아 전송('face' = 기본값 생략 = 4000자 컷 여유) · 렌더 py에서 재검증 = 이중
    const scopes = {};
    if (r.scopes && typeof r.scopes === 'object') {
      for (const [k, v] of Object.entries(r.scopes)) {
        if (!/^[0-9]{1,2}$/.test(k)) continue;
        if (v === 'body') scopes[k] = 'body';
        if (Object.keys(scopes).length >= 32) break;
      }
    }
    if (mode === 'mosaic' && !targets.length && !invert) return json({ error: '가릴 인물을 골라줘' }, 400);
    if (mode === 'pinset' && !Object.keys(names).length) return json({ error: '이름을 하나는 넣어줘' }, 400);
    // 모자이크 조절 옵션(운영자 260708) — 화이트리스트 수치 클램프(렌더 py에서 재클램프 = 이중 방어)
    const opts = {};
    if (r.opts && typeof r.opts === 'object') {
      const num = (v, lo, hi) => (typeof v === 'number' && Number.isFinite(v)) ? Math.max(lo, Math.min(hi, v)) : null;   // 숫자 타입 선요구 = ly.js 관례(강제변환 관용 제거 · 평의회E F2)
      const pw = num(r.opts.pxw, 3, 20); if (pw !== null) opts.pxw = Math.round(pw);   // 상한 20 = 얼굴당 ~14블록(재식별 방지 바닥 · 평의회G)
      const ph = num(r.opts.pxh, 3, 20); if (ph !== null) opts.pxh = Math.round(ph);
      const sz = num(r.opts.size, 0.75, 2.5); if (sz !== null) opts.size = Math.round(sz * 100) / 100;   // 하한 0.75 = 하단 시프트 구속(0.4+0.8s≥1) — 커버 ≥ 검출박스 전 변(초상권 바닥 · 평의회G①)
      const fe = num(r.opts.feather, 0, 40); if (fe !== null) opts.feather = Math.round(fe);   // 상한 40 = UI 정렬(평의회H)
      if (r.opts.shape === 'ellipse' || r.opts.shape === 'rect') opts.shape = r.opts.shape;
    }
    const payload = JSON.stringify({ mode, targets, invert, names, colors, opts, scopes });
    if (payload.length > 4000) return json({ error: '선택이 너무 많아 — 줄여줘' }, 400);
    const rr = await GH(env.GH_TOKEN, 'actions/workflows/track-make.yml/dispatches', 'POST', {
      ref: REF, inputs: { id, mode: 'render', render: payload },
    });
    if (rr.status === 204) return json({ ok: true, id, out: `track_out/${id}/video.json` });
    // 발사 실패 → R2 잡 큐 착지(260815 코워크 · conv.js fail-soft 미러) — id 보존 = 뷰어 폴링 무변 · 맥 잡워커 소비.
    if (env.R2) {
      try {
        await env.R2.put(`queue/jobs/${id}-track.json`, JSON.stringify({
          kind: 'track', id, ts: new Date().toISOString(),
          inputs: { id, mode: 'render', render: payload },
        }));
        return json({ ok: true, id, out: `track_out/${id}/video.json`, via: 'r2-queue', note: '깃허브 발사 실패 — 맥 워커 큐 접수' });
      } catch { /* R2도 실패 → 종전 502(아래) */ }
    }
    return json({ error: `렌더 발사 실패 GitHub ${rr.status}: ${(await rr.text()).slice(0, 200)}` }, 502);
  }

  // ── 분석 경로 — 영상 URL 또는 업로드 파일
  const url = String(body.url || '').trim().slice(0, 500);
  let fileB64 = String(body.fileB64 || '');
  const r2key = String(body.r2key || '');   // R2 직업로드 키(대용량 ≤2GB · api/upload 발급 — edit.js 동문 · 260722)
  const name = String(body.name || '');
  if (!url && !fileB64 && !r2key) return json({ error: '영상 URL이나 파일이 필요해' }, 400);
  if (url && !/^https?:\/\//i.test(url)) return json({ error: 'URL은 http(s)로 시작해야 해' }, 400);
  if (url) {
    // 러너發 SSRF 가드(edit.js 원본 동형) — 이 분석 url은 러너가 그대로 fetch하므로 IP리터럴·내부·메타데이터 호스트 거부.
    if (/[\r\n\t]/.test(url)) return json({ error: '잘못된 URL' }, 400);
    let uh = '';
    try { const x = new URL(url); if (x.protocol !== 'http:' && x.protocol !== 'https:') return json({ error: 'URL은 http(s)로 시작해야 해' }, 400); uh = x.hostname.toLowerCase(); } catch { return json({ error: '잘못된 URL' }, 400); }
    if (/^\d{1,3}(\.\d{1,3}){3}$/.test(uh) || uh === 'localhost' || uh.endsWith('.local') || uh.startsWith('[')
      || uh === 'metadata.google.internal' || uh.endsWith('.internal') || uh === 'instance-data'
      || !/^[a-z0-9.-]+\.[a-z]{2,}$/i.test(uh)) return json({ error: '지원하지 않는 URL 호스트' }, 400);
  }

  const id = new Date(Date.now() + 9 * 3600e3).toISOString().replace(/[^0-9]/g, '').slice(2, 14) + '-' + crypto.randomUUID().slice(0, 6);   // YYMMDDHHMMSS = KST(+9h · pick.js 규칙)

  // R2 직업로드 키(대용량 ≤2GB · api/upload 발급 — edit.js 동문 · 260722) — 존재·크기 검증 후 러너에 r2_src로 전달(base64/up-브랜치 경로 건너뜀)
  let r2src = '';
  if (!url && r2key) {
    if (!/^up_src\/\d{12}-[a-f0-9]{6}\.(mp4|mov|m4v|webm|mkv|avi)$/.test(r2key) || /\s/.test(r2key)) return json({ error: '잘못된 업로드 키 — 파일을 다시 선택해줘' }, 400);   // \s = $ 후행 개행 봉합(conv 평의회1 계승)
    if (!env.R2) return json({ error: '대용량 업로드 미설정 — 파일을 다시 선택해줘' }, 501);
    const h = await env.R2.head(r2key);
    if (!h) return json({ error: '업로드 파일이 없어(만료·정리됨) — 다시 올려줘' }, 400);
    if (h.size > 2 * 1024 * 1024 * 1024) return json({ error: '파일은 2GB까지' }, 400);
    r2src = r2key;
  }

  // 파일 업로드(uploads/<id>/src.*) — url 우선. 일회용 브랜치 up-<id> 커밋(main 히스토리 비대 0 · ly.js 동일)
  let filePath = '';
  let upBranch = '';
  if (!url && !r2src && fileB64) {
    const dm = fileB64.match(/^data:[^;,]*;base64,(.+)$/);   // mediatype 빈값(data:;base64,) 허용 — 미매치 시 프리픽스 잔존 → GH PUT 422(평의회2)
    if (dm) fileB64 = dm[1];
    if (!fileB64 || fileB64.length > 40_000_000) return json({ error: '파일은 ≤30MB — 큰 영상은 URL로(드라이브 등 직링크)' }, 400);
    const ext = (name.match(/\.(mp4|mov|m4v|webm|mkv|avi)$/i) || ['.mp4'])[0].toLowerCase();
    filePath = `uploads/${id}/src${ext}`;
    try {
      const ref = await GH(env.GH_TOKEN, `git/ref/heads/${REF}`, 'GET');
      if (ref.status === 200) {
        const sha = (await ref.json()).object.sha;
        const mk = await GH(env.GH_TOKEN, 'git/refs', 'POST', { ref: `refs/heads/up-${id}`, sha });
        if (mk.status === 201) upBranch = `up-${id}`;
      }
    } catch { /* 폴백 = main 경로 */ }
    const put = await GH(env.GH_TOKEN, `contents/${filePath}`, 'PUT', { message: `track upload ${id}`, content: fileB64, branch: upBranch || REF });
    if (put.status !== 201 && put.status !== 200) {
      if (upBranch) { try { await GH(env.GH_TOKEN, `git/refs/heads/${upBranch}`, 'DELETE'); } catch { /* 잔존 무해 */ } }
      return json({ error: `업로드 실패 GitHub ${put.status}: ${(await put.text()).slice(0, 200)}` }, 502);
    }
  }

  const r = await GH(env.GH_TOKEN, 'actions/workflows/track-make.yml/dispatches', 'POST', {
    ref: REF, inputs: { id, mode: 'analyze', url, file: filePath, up_branch: upBranch, r2_src: r2src },   // r2_src = R2 직업로드 키(빈값 = 종전 · 260722)
  });
  if (r.status === 204) return json({ ok: true, id, out: `track_out/${id}/tracks.json` });
  // 발사 실패 → R2 잡 큐 착지(260815 코워크 · conv.js fail-soft 미러) — 업로드 브랜치는 잡이 쓰므로 보존.
  if (env.R2) {
    try {
      await env.R2.put(`queue/jobs/${id}-track.json`, JSON.stringify({
        kind: 'track', id, ts: new Date().toISOString(),
        inputs: { id, mode: 'analyze', url, file: filePath, up_branch: upBranch, r2_src: r2src },
      }));
      return json({ ok: true, id, out: `track_out/${id}/tracks.json`, via: 'r2-queue', note: '깃허브 발사 실패 — 맥 워커 큐 접수' });
    } catch { /* R2도 실패 → 종전 502(아래) */ }
  }
  if (upBranch) { try { await GH(env.GH_TOKEN, `git/refs/heads/${upBranch}`, 'DELETE'); } catch { /* 고아 잔존 무해 — 수동 정리 대상 */ } }
  return json({ error: `발사 실패 GitHub ${r.status}: ${(await r.text()).slice(0, 200)}` }, 502);
}

// ── 산출 라이브 서빙(빌드 우회) — 골격·폴백 체인·헤더 = functions/api/trends.js 정본 계승(새 문법 0) ──
// 왜(260810 실측): 뷰어는 `track_out/<id>/tracks.json` 을 **정적 경로**로 폴링한다 → 러너가 커밋을 밀어도
//   Cloudflare Pages 가 사이트를 다시 빌드해야만 카드가 뜬다(analyze 런 31321357588 배포 게이트 **134s** =
//   전체 374s의 36% · 봇 커밋이 초당급이라 큐가 밀리면 그 이상). 실제 얼굴 검출·군집은 10s 뿐인데
//   「분석은 끝났는데 화면이 못 받는」 구간이 그 13배였다. trends.js 헤더가 박제한 것과 **같은 병**이고,
//   그쪽은 `check_coalesce_pair` 가 8표면에 라이브 서빙을 강제하는데 track_out 만 그 계약 밖이었다.
// ⚠ crop 동반이 실효 조건 — tracks.json 만 라이브로 주면 얼굴 사진(`crops/p*.jpg`)이 빌드 전엔 404 =
//   카드가 통째로 깨진 이미지가 된다(= 이 우회의 유일한 기능 저하 경로라 같은 함수에서 같이 서빙한다).
// ⚠ 뷰어는 **라이브 우선 → 정적 폴백** 2단이라 이 함수가 죽어도 종전 동작으로 내려앉는다(악화 경로 0).
const OUT_F = {   // 화이트리스트 — 임의 경로 주입 차단(trends.js FILES 관례 · 값 = track_out/<id>/ 하위 상대경로)
  tracks: 'tracks.json',
  error: 'error.log',
  video: 'video.json',
};
export async function onRequestGet({ request, env }) {
  const u = new URL(request.url).searchParams;
  const id = String(u.get('id') || '').trim();
  const f = String(u.get('f') || 'tracks');
  const JH = { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' };   // 폴링 축 = 캐시 금지(옛 404/구본이 굳으면 그게 곧 지연)
  if (!/^[0-9]{12}-[0-9a-f]{6}$/.test(id)) return new Response('{"error":"bad id"}', { status: 400, headers: JH });
  let rel, bin = false;
  if (f === 'crop') {
    const n = String(u.get('n') || '');
    if (!/^[ps][0-9]{1,3}\.jpg$/.test(n)) return new Response('{"error":"bad crop"}', { status: 400, headers: JH });   // 얼굴 p<N>.jpg · 피사체 s<N>.jpg 뿐(경로 탈출 차단)
    rel = `crops/${n}`; bin = true;
  } else if (Object.prototype.hasOwnProperty.call(OUT_F, f)) {   // hasOwnProperty = 프로토타입 키(`?f=constructor`) 누수 차단(trends.js P0 교훈)
    rel = OUT_F[f];
  } else {
    return new Response('{"error":"unknown f"}', { status: 404, headers: JH });
  }
  const path = `viewer/track_out/${id}/${rel}`;
  const tries = [];
  if (env.GH_TOKEN) tries.push([   // 1순위 = contents API(토큰) — raw 는 ~5분 캐시라 폴링 1순위로 쓰면 그 캐시가 그대로 지연이 된다
    `https://api.github.com/repos/${REPO}/contents/${path}?ref=${REF}`,
    { authorization: `Bearer ${env.GH_TOKEN}`, accept: 'application/vnd.github.raw', 'user-agent': 'nomute-viewer' },
  ]);
  tries.push([`https://raw.githubusercontent.com/${REPO}/${REF}/${path}`, { 'user-agent': 'nomute-viewer' }]);
  for (const [url, headers] of tries) {
    try {
      const r = await fetch(url, { headers, cf: { cacheTtl: bin ? 300 : 5, cacheEverything: true } });   // 크롭 = 불변 산출이라 캐시 · 폴링 산출 = 5s
      if (!r.ok) continue;
      if (bin) {
        return new Response(r.body, { status: 200, headers: { 'content-type': 'image/jpeg', 'cache-control': 'public, max-age=600' } });
      }
      const body = await r.text();
      if (f === 'error') {
        if (!body.trim()) continue;
        return new Response(body, { status: 200, headers: { 'content-type': 'text/plain; charset=utf-8', 'cache-control': 'no-store' } });
      }
      const j = JSON.parse(body);   // 유효 JSON 확인 — 깨진/부분 응답이면 throw → 다음 소스(trends.js 미러)
      if (f === 'tracks' && !(j && Array.isArray(j.people))) continue;   // 뷰어 완료 술어와 **같은 축**(people 배열) — 반쪽 파일을 완료로 오판하지 않는다
      if (f === 'video' && !(j && (j.url || j.error))) continue;
      return new Response(body, { status: 200, headers: JH });
    } catch { /* 다음 소스 */ }
  }
  return new Response('{"error":"not ready"}', { status: 404, headers: JH });   // 아직 커밋 전 = 404 = 뷰어 폴링 계속(정적 폴백도 그대로 시도된다)
}
