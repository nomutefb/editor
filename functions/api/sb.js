// Cloudflare Pages Function — 뷰어 콘티(스토리보드) 폼 → sb-make 워크플로 발사(이야기 → 텍스트 콘티).
// 흐름: 브라우저가 이야기 텍스트 POST → sb-make.yml 발사 → 러너가 claude -p(감독 모델 스위치 · storyboard-v1 스킬 Read)
//        → viewer/sb_out/<id>/board.md 커밋 → 폼이 폴링해 렌더(컷 리스트).
// env: GH_TOKEN = k.js와 동일 PAT. 인증·생성은 러너의 구독 OAuth(무료). 이미지·영상 생성 없음(0크레딧 초안 게이트).
// 2축 분리(운영자 260714): director = 감독(연출·claude 모델) / shoot = 촬영(kling 수동 · seedance MCP 자동 — 콘티 하류 분기 안내).
const REPO = 'nomutefb/editor';
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
  const _lbl = (typeof body.lbl === 'string' && body.lbl.trim()) ? body.lbl.trim().slice(0, 80) : '';   // 발사 이름표 에코(260818 «영상 쪽도 실명» — api/thumb.js 동문) · 진행 중 원장(putLive)이 응답만 읽으므로 여기 실어야 다른 기기 합류분이 종류 이름 대신 실명을 단다

  let story = String(body.story || '').slice(0, 16000);   // 상한 2배(260812) — 화면이 [지시]+[기사 요약] 두 칸을 합쳐 보낸다(각 8000) · 구 8000 이면 긴 기사 하나에 지시가 잘려 나갔다
  // 변형·2차 기준 콘티(경로 화이트리스트 = sb_out 산출물만 · 임의 파일 읽기 차단) — 2차 판정에 먼저 필요해 위로 올렸다(260817).
  const base = (typeof body.base === 'string' && /^sb_out\/[0-9]{12}-[0-9a-f]{6}\/board\.md$/.test(body.base)) ? body.base : '';
  const shootOnly = (body.shootOnly === true || body.shootOnly === 'true') && !!base;
  // ⚠ 2차(촬영만)는 이야기가 **비어 있는 게 정상**이다(비우는 것 자체가 러너 표식) — 구판은 이 빈 칸
  //   검사가 2차 판정보다 먼저 돌아 **화면의 2차 발사가 전건 400 으로 죽었다**(260817 스텁 실행 실측 ·
  //   러너 실호출들은 손 발사라 이 층을 안 지나 잠복했다).
  if (!story.trim() && !shootOnly) return json({ error: '이야기/기사 입력이 필요해' }, 400);

  const id = new Date(Date.now() + 9 * 3600e3).toISOString().replace(/[^0-9]/g, '').slice(2, 14) + '-' + crypto.randomUUID().slice(0, 6);   // YYMMDDHHMMSS = KST(+9h · k.js 규칙)
  // 화이트리스트 = 임의 문자열 주입 차단(k.js 패턴 계승 — 키는 서버 목록만 순회 = 사용자 키 자체를 안 읽음).
  // 값 2면 동기: 이 표 = viewer/sb.html SB_DIRECTORS/SB_SHOOTS/SB_VALS.
  const SB_DIRECTORS = ['fable', 'opus', 'gpt'];   // gpt = OpenAI API 레인(운영자 260714 "지피티도 가능하게" — 러너 시크릿 OPENAI_API_KEY 필요 · sbmake.sh 분기)
  const SB_SHOOTS = ['grok', 'seedance', 'seedance20', 'seedance5', 'motion'];   // seedance20 = 같은 통로의 두 번째 프리셋(2.0 · 720p · 15초 두 발) — 입력 칸을 새로 만들지 않고 촬영 칸을 나눈 것(발사 입력은 10칸이 상한이라 신설이 곧 상한 소모)   // 운영자 260811 = kling 제거(종량제 미사용 = 이 메뉴에서 의미 0) · grok 신설(구독 OAuth 직결 · 그림→영상)   // motion = 플랫 모션그래픽 사내 렌더 레인(실사 생성 AI 아님 · 콘티 「## 🎞 모션 스펙」 → 같은 잡의 mg_render.py가 mp4까지 · 외부 API 0)
  const SB_SET = {
    '비율': ['9:16', '16:9', '1:1'],
    '화질': ['720p', 'FHD', '2K', '4K'],   // 어휘·순서 = 뷰어 SB_VALS·이미지 스튜디오 UPS_ORDER 동기(260813) · 2K = 사내 렌더 레인 전용(창구 판에는 그 이름이 없다 = 뷰어 SB_CAPS가 레인별로 거른다)     // 프롬프팅 이관 축(운영자 Q1145) — 값 집합 = api/k.js K_SET 동일
    '프레임': ['30fps'],                       // 30fps 고정(운영자 260804 "60fps 어짜피 불가하니까 30fps 고정") — 뷰어 「설계」 선택 행 폐지와 2면 동기(구 60fps 값은 화이트리스트에서도 회수 = 옛 폼·직접 호출이 몰래 60을 넣는 경로 차단)
    '길이': ['10s', '20s', '30s', '40s', '50s', '60s'],
    // 화풍·세부 화풍(운영자 260813) — 값 = 뷰어 nm-styles.js 정본의 **사람 말** 그대로.
    // ⚠ 여기 목록이 곧 화이트리스트라 정본에 화풍을 더하면 이 줄도 같이 늘려야 한다.
    //   안 늘리면 화면에서는 골라지는데 서버가 조용히 버려서 감독이 그 화풍을 영영 못 본다.
    '화풍': ['극화', '수채', '실사', '만평', '시네마틱', '일러스트', '3D', '픽토', '레고'],
    '세부 화풍': ['필름', '흑백', '시네다큐', '뉴스릴', '게키카', '하드보일드', '시대극', '순정', '명랑',
                  '붓선', '플랫', '판화', '번짐', '세밀', '수묵', '과슈', '유화',
                  '누아르', '네온', '35mm', '표현주의', '리소', '페이퍼', '애니', '레트로80',
                  '클레이', '로우폴리', '디오라마', '라인', '청사진'],   // 자(ruler) 축 = **10초 눈금 6칸 = 1~6컷**(운영자 260812 「컷 1개 = 10초 고정 · 10*n 개수로」) — 구 5~15s 1초 눈금 폐지(1초 눈금이면 10의 배수 아닌 값이 골라져 보드가 10초로 안 쪼개진다) · 컷수 = 길이 ÷ 10(뷰어 sbCutN · prompts/sb-make.md 동기)
  };
  const DIRECTOR_NM = { fable: 'Fable 5', opus: 'Opus 5', gpt: 'GPT 5.6 Sol' };   // 표시명 = 정식 모델명 단일화(운영자 260803 4차 · 뷰어 SB_DIRECTORS nm 2면 동기)
  const director = SB_DIRECTORS.includes(body.director) ? body.director : 'fable';
  const shoot = SB_SHOOTS.includes(body.shoot) ? body.shoot : 'grok';
  story += '\n\n[감독: ' + DIRECTOR_NM[director] + ']';   // 에코용 마커(모델 스위치는 워크플로 director 입력이 전담)
  story += '\n\n[촬영: ' + shoot + ']';   // 다음 단계 안내 분기(kling=수동 복붙 레인 · seedance=MCP 자동 레인)
  const set = (body.set && typeof body.set === 'object' && !Array.isArray(body.set)) ? body.set : {};
  const pairs = [];
  for (const k of Object.keys(SB_SET)) {
    const v = set[k];
    if (typeof v !== 'string') continue;
    if (k === '비율' && /^(?:[1-9]|[1-9][0-9]):(?:[1-9]|[1-9][0-9])$/.test(v)) { pairs.push(k + '=' + v); continue; }   // '직접' N:M 허용 = 각 1~99(뷰어 sbArVal 계약 · api/k.js '길이' 게이지 정규식 선례 동문법 — 화이트리스트 리터럴은 무접촉이라 2면 동기 게이트 그대로)
    if (SB_SET[k].includes(v)) pairs.push(k + '=' + v);
  }
  if (pairs.length) story += '\n\n[설정: ' + pairs.join(' · ') + ']';
  // 레퍼런스 이미지 생성 여부(운영자 Q1161): 시댄스 = 강제 ON(md만 산출하는 레인 = 이미지가 발사 필수 재료) · 클링 = 폼 선택값(옵션)
  // motion = 강제 false(플랫 그래픽 레인 = 실사 레퍼런스가 쓰이는 곳이 없다 → Gemini 미과금) · seedance = 강제 true · kling = 폼 선택값
  const sound = (body.sound === false || body.sound === 'false' || body.sound === '0') ? '0' : '1';   // 운영자 260810 「소리 온오프도 옵션」 · 촬영=grok 전용(다른 레인은 러너가 무시)
  const refimage = (shoot === 'motion') ? 'false' : ((shoot.startsWith('seedance') || shoot === 'grok') ? 'true' : ((body.ref === false || body.ref === 'false') ? 'false' : 'true'));   // grok = 콘티 컷 그림이 영상의 첫 장면 재료 = 강제 생성
  story += '\n\n[레퍼런스: ' + (refimage === 'true' ? 'ON' : 'OFF') + ']';   // 절 출력 게이트(prompts/sb-make.md)
  if (body.ad === true || body.ad === 'true') story += '\n\n[광고: ON]';   // 광고 모드 = 마지막 컷 키비주얼 의무(storyboard-v1 하드룰)
  // 🎬 **2차 = 촬영만**(운영자 260813 「생성 버튼은 총 2번」 · base·shootOnly 판정은 위(빈 이야기
  //    검사보다 먼저 필요해 260817 상향)) — 1차 콘티를 보고 승인한 뒤 모델만 골라 제작을 건다.
  //    이야기를 비우고 기준 콘티만 넘기면 러너가 감독을 건너뛴다.
  //    ⚠ 감독을 다시 안 부른다 = **승인한 그 콘티가 그대로 찍힌다**(다시 부르면 승인 대상이 바뀐다).
  // 화질 실값 — 화이트리스트를 이미 통과한 설정값만 넘긴다(임의 문자열 주입 0).
  // ⚠ 러너는 그 판이 모르는 이름을 받으면 **멈춘다**(조용히 다른 화질로 나가는 것보다 안 나가는 쪽이 싸다).
  const res = (typeof set['화질'] === 'string' && SB_SET['화질'].includes(set['화질'])) ? set['화질'] : '';
  if (shootOnly) story = '';   // 마커까지 통째로 비운다(빈 이야기 = 러너의 2차 표식)
  // 📷 참조 사진(운영자 260817 「콘티에 참조할 사진도 넣을 수 있게」) — 발사 입력 10칸이 만석이라
  //    칸을 안 늘리고 ⓐ 사진 바이트는 보관함(R2)에 앉히고 ⓑ 주소만 이야기 말미 표식으로 태운다
  //    ([설정:] 마커 관례 · 러너 sbmake.sh 가 내려받아 감독 열람 + 인물 시트 얼굴 정본으로 쓴다).
  //    ⚠ jpeg 만 받는다(화면 압축기가 jpeg 로 굽는다) — 다른 형식을 .jpg 로 앉히면 거짓 확장자다.
  //    ⚠ 2차(촬영만)는 이야기가 비므로 사진 축 자체가 없다 · 올리다 실패하면 조용히 빼지 않고
  //      막는다(사진을 시켰는데 없이 나가는 쪽이 더 비싼 사고 = 조용한 유실).
  const photos = (!shootOnly && Array.isArray(body.photos)) ? body.photos.slice(0, 3) : [];
  if (photos.length) {
    if (!env.R2) return json({ error: '사진 보관함(R2) 미설정 — 사진을 빼고 다시 보내거나 배포 설정 확인' }, 500);
    const pubBase = String(env.R2_PUBLIC_BASE || '').replace(/\/+$/, '');
    if (!pubBase) return json({ error: '사진 공개 주소(R2_PUBLIC_BASE) 미설정 — 사진을 빼고 다시 보내거나 배포 설정 확인' }, 500);
    const purls = [];
    for (let i = 0; i < photos.length; i++) {
      const m = /^data:image\/jpeg;base64,([A-Za-z0-9+/=]+)$/.exec(String(photos[i] || ''));
      if (!m) return json({ error: '사진 ' + (i + 1) + '번 형식 오류(jpeg 만 · 화면 첨부를 다시 해봐)' }, 400);
      let bin;
      try { bin = Uint8Array.from(atob(m[1]), c => c.charCodeAt(0)); } catch { return json({ error: '사진 ' + (i + 1) + '번 손상' }, 400); }
      if (bin.length > 3 * 1024 * 1024) return json({ error: '사진 ' + (i + 1) + '번이 너무 크다(3MB 상한 — 화면 압축을 거치면 안 넘는다)' }, 400);
      const key = `sb_out/${id}/photo_${i + 1}.jpg`;
      try { await env.R2.put(key, bin, { httpMetadata: { contentType: 'image/jpeg' } }); }
      catch { return json({ error: '사진 ' + (i + 1) + '번 보관함 저장 실패 — 잠시 뒤 다시' }, 502); }
      purls.push(pubBase + '/' + key);
    }
    story += '\n\n[참조 사진: ' + purls.join(' ') + ']';
  }
  const r = await GH(env.GH_TOKEN, 'actions/workflows/sb-make.yml/dispatches', 'POST', {
    // 화질은 **마커가 아니라 입력 칸**으로도 보낸다 — 러너가 실제로 그 화질로 쏘려면
    // 이야기 속 문구가 아니라 발사 인자로 와야 한다(260813 봉합 · 손입력 칸 10/10 소진).
    ref: REF, inputs: { id, story, director, shoot, sound, refimage, base, res },   // shoot·refimage·res = 워크플로 입력(러너 조건 분기 — 마커와 별개 축).
  });
  if (r.status === 204) return json({ ok: true, id, out: `sb_out/${id}/board.md`, ...(_lbl ? { lbl: _lbl } : {}) });
  // 발사 실패 → R2 잡 큐 착지(260815 코워크 · conv.js fail-soft 미러) — id 보존 = 뷰어 폴링 무변 · 맥 잡워커 소비.
  if (env.R2) {
    try {
      await env.R2.put(`queue/jobs/${id}-sb.json`, JSON.stringify({
        kind: 'sb', id, ts: new Date().toISOString(),
        inputs: { id, story, director, shoot, sound, refimage, base, res },
      }));
      return json({ ok: true, id, out: `sb_out/${id}/board.md`, ...(_lbl ? { lbl: _lbl } : {}), via: 'r2-queue', note: '깃허브 발사 실패 — 맥 워커 큐 접수' });
    } catch { /* R2도 실패 → 종전 502(아래) */ }
  }
  return json({ error: `발사 실패 GitHub ${r.status}: ${(await r.text()).slice(0, 200)}` }, 502);
}
