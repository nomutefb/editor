// Cloudflare Pages Function — 뷰어 ✏️요약 수정 요청 → GitHub news-revise 워크플로 발사.
// 입력 = { file, instruction } : file=큐 항목 id(260616-0823-...) · instruction=재작성 지시(자연어).
// → 워크플로가 queue/<file>.md 의 IG·Thread 초안만 지시대로 재작성(기사 재수집·재요약 X = 구독 쿼터 절약).
// env: GH_TOKEN = GitHub fine-grained PAT(이 레포, Actions: Read and write) — rate/pick/make-cards와 동일 토큰.
// 과금 0: 워크플로 Claude는 구독 OAuth(per-run 과금 0). 종량제 API 키 미사용(직접 Messages API 아님).
import { dispatchWf } from './_fire.js';   // (260820) 발사 재시도 SSOT — thumb 발사 유실 실사고 형제 이식(1발 즉실패 → 큐행 = 조용한 유실 봉합)
export async function onRequestPost({ request, env }) {
  const json = (o, s = 200) =>
    new Response(JSON.stringify(o), { status: s, headers: { 'content-type': 'application/json' } });

  let body;
  try { body = await request.json(); } catch { return json({ error: '잘못된 요청' }, 400); }
  if (!env.GH_TOKEN) return json({ error: '서버 미설정 — GH_TOKEN 필요' }, 500);

  // file = 큐 항목 id(확장자·경로 없이). 안전 패턴(260616-0823-…)만 — 경로주입 차단.
  const file = String(body.file || '').trim().replace(/\.md$/, '');
  const instruction = String(body.instruction || '').trim().slice(0, 2000);
  if (!/^\d{6}-\d{4}-[A-Za-z0-9._-]{1,80}$/.test(file)) return json({ error: '잘못된 대상(file)' }, 400);
  if (!instruction) return json({ error: '빈 지시 — 어떻게 고칠지 적어줘' }, 400);

  // 디스패치 fetch throw(깃허브 접속 불가)는 dispatchWf 가 안에서 받는다(260720 장애 실증의 try 감싸기 계승) —
  // 전 시도 실패 = status 0 으로 내려와 아래 R2 큐행 = 구판 503 즉포기보다 나은 착지(접수 유실 0 · 260820).
  const r = await dispatchWf(env, 'news-revise.yml', { ref: 'main', inputs: { file, instruction } });   // (260820) 재시도 3회(_fire.js) — 판정·에러 문구 계약 종전 동일(반환 = {status,text()})
  if (r.status === 204) return json({ ok: true });
  // 발사 실패 → R2 잡 큐 착지(260815 코워크 fail-soft)
  if (env.R2) {
    try {
      const qid = new Date(Date.now() + 9 * 3600e3).toISOString().replace(/[^0-9]/g, '').slice(2, 14) + '-' + Math.random().toString(16).slice(2, 8);
      await env.R2.put(`queue/jobs/${qid}-revise.json`, JSON.stringify({
        kind: 'revise', id: qid, ts: new Date().toISOString(),
        wfYml: 'news-revise.yml', wfInputs: { file, instruction }, failNote: r._note,   // (260820) 자기서술 = rescueJobs 재발사 원료 · ⚠ wfInputs 분리 = 아래 inputs(맥 워커용)는 id 가 덧붙어 그대로 재발사하면 워크플로 미정의 입력(422)
        inputs: { id: qid, file, instruction },
      }));
      return json({ ok: true, via: 'r2-queue' });
    } catch { /* R2도 실패 → 아래 종전 응답 */ }
  }
  if (r.status >= 500) return json({ error: `GitHub 서버 장애(${r.status}) — 재시도` }, 503);
  return json({ error: `GitHub ${r.status}: ${(await r.text()).slice(0, 300)}` }, 502);
}
