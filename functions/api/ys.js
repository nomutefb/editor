// Cloudflare Pages Function — 영상 스튜디오 「유튜브」 탭 → ys-make 워크플로 발사(운영자 260928 · 기존 레인과 독립).
// 입력 = 유튜브 URL 1개 + 옵션(음성·받아쓰기·장면 그림·길이·폰트·지시) → 산출 = viewer/ys_out/<id>/result.json
//   진행 = R2 ys_out/<id>/progress.json(워크플로가 단계마다 게시 · functions/ys_out = r2live 즉시 서빙).
// 옵션은 여기서 화이트리스트로 자르고, 워크플로가 한 번 더 자른다(상류 신뢰 대신 최후 방어선 · vd/conv 선례).
import { rateGate } from './_rate.js';
import { dispatchWf, rescueJobs } from './_fire.js';
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
// 유튜브 영상 주소만(채널·재생목록 = 이 탭 대상 밖 — 자료화 nb 탭 몫)
export const YT_RE = /^https:\/\/(?:(?:www\.|m\.)?youtube\.com\/(?:watch\?(?:[^#\s]*&)?v=|shorts\/|live\/)|youtu\.be\/)[A-Za-z0-9_-]{11}(?:[?&#][^\s]*)?$/;
export const OPTS = {
  voice: ['eleven', 'edge'],          // 고급(ElevenLabs · 기본) / 무료 음성 — 첫 값 = 기본(운영자 260928 «60초 고급 정밀 맥 그림 기본»)
  stt: ['scribe', 'subs'],            // 정밀 받아쓰기(Scribe · 기본) / 유튜브 자막 우선
  img: ['codex', 'none'],             // 맥 Codex 장면 그림(기본 · 맥 꺼짐 = 글자 화면 자동) / 글자 화면
  len: ['60', '45', '90'],            // 목표 초
  font: ['pretendard', 'gothic', 'barun'],   // 운영자 260928 "프리텐다드·노토산스·나눔바른고딕 · 기본 프리텐다드"
  ratio: ['9:16', '16:9'],            // 세로(기본) / 가로
  subbg: ['on', 'off'],               // 자막 배경 점등(기본 켬)
};
export function cleanOpts(body) {
  const src = (body && typeof body.opts === 'object' && body.opts && !Array.isArray(body.opts)) ? body.opts : (body || {});   // 새 모양 = {opts:{…}} · 옛 모양(최상위) 하위호환
  const o = {};
  for (const [k, allow] of Object.entries(OPTS)) o[k] = allow.includes(String(src[k] ?? '')) ? String(src[k]) : allow[0];
  const op = Number.parseInt(src.subop, 10);
  o.subop = String(Number.isFinite(op) ? Math.min(100, Math.max(0, op)) : 100);   // 자막 배경 불투명도 %(기본 100)
  o.el_voice = /^[A-Za-z0-9]{16,32}$/.test(String(src.el_voice || '')) ? String(src.el_voice) : '';   // ElevenLabs 목소리 id(빈 값 = AI 자동)
  return o;
}

export async function onRequestPost({ request, env }) {
  const json = (o, s = 200) => new Response(JSON.stringify(o), { status: s, headers: { 'content-type': 'application/json' } });   // seal-ok: 응답 JSON 헤더 — _fire·_rate 는 응답을 만들지 않는 헬퍼라 대상 밖
  if (!env.GH_TOKEN) return json({ ok: false, error: '서버 미설정 — Cloudflare 환경변수 GH_TOKEN 필요' }, 500);
  let body;
  try { body = await request.json(); } catch { return json({ ok: false, error: '잘못된 요청' }, 400); }
  if (!body || typeof body !== 'object' || Array.isArray(body)) return json({ ok: false, error: '잘못된 요청' }, 400);

  const url = String(body.url || '').replace(/[\u0000-\u001F\u007F\s]/g, '').slice(0, 300);
  if (!YT_RE.test(url)) return json({ ok: false, error: '유튜브 영상 주소를 넣어줘 — youtube.com/watch?v=… · youtu.be/… · youtube.com/shorts/…' }, 400);
  const ask = String(body.ask || '').replace(/[\u0000-\u001F\u007F]+/g, ' ').trim().slice(0, 300);
  const o = cleanOpts(body);

  const rl = await rateGate(GH, env.GH_TOKEN, 'ys-make.yml');   // 발사 레이트리밋(파이프 공통 문법 · fail-open)
  if (rl) return json({ ok: false, error: rl.error }, 429);

  const id = new Date(Date.now() + 9 * 3600e3).toISOString().replace(/[^0-9]/g, '').slice(2, 14) + '-' + crypto.randomUUID().slice(0, 6);   // KST(+9h · pick.js 규칙)
  const inputs = { id, url, ask, opts: JSON.stringify(o) };   // 옵션 = JSON 1칸(디스패치 입력 개수 상한 여유 · vd opts 선례) — 워크플로가 한 번 더 화이트리스트
  const out = `ys_out/${id}/result.json`;
  const r = await dispatchWf(env, 'ys-make.yml', { ref: REF, inputs });   // 재시도 3회(_fire.js SSOT)
  if (r.status === 204) return json({ ok: true, id, out });
  if (env.R2) {   // 발사 실패 → R2 잡 큐 착지 = rescueJobs 가 다음 발사 때 재발사(wfYml·inputs 자기서술 · nb.js 문법)
    try {
      await env.R2.put(`queue/jobs/${id}-ys.json`, JSON.stringify({ kind: 'ys', id, ts: new Date().toISOString(), wfYml: 'ys-make.yml', failNote: r._note, inputs }));
      return json({ ok: true, id, out, via: 'r2-queue' });
    } catch { /* 아래 502 */ }
  }
  return json({ ok: false, error: `발사 실패 GitHub ${r.status}: ${(await r.text()).slice(0, 200)}` }, 502);
}

// GET /api/ys?rescue=1 = 발사 실패로 큐에 착지한 ys 잡 재발사(화면이 러너 소식 없는 동안 1분마다 부른다 · 회당 2건·임대 90초·24시간 = _fire.js 정본)
export async function onRequestGet({ request, env }) {
  const u = new URL(request.url);
  const out = (o, st) => new Response(JSON.stringify(o), { status: st, headers: { 'content-type': 'application/json', 'cache-control': 'no-store' } });   // seal-ok: 응답 JSON 헤더(위 json 헬퍼와 같은 모양 · GET 전용 캐시 금지)
  if (u.searchParams.get('rescue') !== '1') return out({ ok: false, error: '잘못된 요청' }, 400);
  await rescueJobs(env, 'ys');
  return out({ ok: true }, 200);
}
