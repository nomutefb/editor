// Cloudflare Pages Function — 뷰어 🃏카드 수정 요청 → GitHub cards-revise 워크플로 발사.
// 입력 = { file, instruction } : file=큐 항목 id(260616-0823-...) · instruction=카드 재기획 지시(자연어).
// → 워크플로가 cards/<file>/cards.md(카드 프롬프트 전체)만 지시대로 재기획(기사 재수집·재요약 X · 이미지 재슛 X = 구독 쿼터·제미나이 0).
// env: GH_TOKEN = GitHub fine-grained PAT(이 레포, Actions: Read and write) — revise/pick/make-cards와 동일 토큰.
// 과금 0: 워크플로 Claude는 구독 OAuth(per-run 과금 0). 종량제 API 키 미사용. revise.js(요약 수정)의 카드판 미러.
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

  const r = await dispatchWf(env, 'cards-revise.yml', { ref: 'main', inputs: { file, instruction } });   // (260820) 재시도 3회(_fire.js) — 판정·에러 문구 계약 종전 동일(반환 = {status,text()})
  if (r.status === 204) return json({ ok: true });
  // 발사 실패 → R2 잡 큐 착지(260815 코워크 fail-soft)
  if (env.R2) {
    try {
      const qid = new Date(Date.now() + 9 * 3600e3).toISOString().replace(/[^0-9]/g, '').slice(2, 14) + '-' + Math.random().toString(16).slice(2, 8);
      await env.R2.put(`queue/jobs/${qid}-revise-cards.json`, JSON.stringify({
        kind: 'revise-cards', id: qid, ts: new Date().toISOString(),
        wfYml: 'cards-revise.yml', wfInputs: { file, instruction }, failNote: r._note,   // (260820) 자기서술 = rescueJobs 재발사 원료 · ⚠ wfInputs 분리 = 아래 inputs(맥 워커용)는 id 가 덧붙어 그대로 재발사하면 워크플로 미정의 입력(422)
        inputs: { id: qid, file, instruction },
      }));
      return json({ ok: true, via: 'r2-queue' });
    } catch { /* R2도 실패 → 종전 502 */ }
  }
  return json({ error: `GitHub ${r.status}: ${(await r.text()).slice(0, 300)}` }, 502);
}
