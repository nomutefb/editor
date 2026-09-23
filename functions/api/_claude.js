// Anthropic Messages API 직결 공용(k·tr 즉답) — 거절 대비 서버 측 폴백(운영자 260923 "비용 과부하가 없으면 조치").
// 정본 = Claude API 마이그레이션 문서: `fallbacks: "default"` + 베타 `server-side-fallback-2026-07-01` =
//   안전 분류기 거절(정책)일 때만 Anthropic 추천 모델로 서버가 다시 돌린다(모델 목록 관리 0).
// 비용: 출력 전 거절 시도는 무과금 · 폴백 시도만 그 모델 단가 = 거절이 없으면 추가 0 · 한도·과부하·서버 오류엔 발동 안 함.
// 베타 자체가 400으로 거절되면 폴백 없이 1회 재요청(= 종전 동작 · 400은 무과금) — 즉답이 통째로 러너로 밀리는 퇴행 방지.
const API = 'https://api.anthropic.com/v1/messages';
const FALLBACK_BETA = 'server-side-fallback-2026-07-01';

export async function claudeMessages(env, body) {
  const base = { 'content-type': 'application/json', 'x-api-key': env.ANTHROPIC_API_KEY, 'anthropic-version': '2023-06-01' };   // seal-ok: Anthropic JSON 요청 헤더 — 형제 _fire·_rate는 이 API를 안 부른다
  let r = await fetch(API, { method: 'POST', headers: { ...base, 'anthropic-beta': FALLBACK_BETA }, body: JSON.stringify({ ...body, fallbacks: 'default' }) });
  if (r.status === 400) {
    const t = await r.text();
    if (!/fallback/i.test(t)) throw new Error(`anthropic 400 ${t.slice(0, 200)}`);
    console.warn('claude 폴백 베타 거부 → 폴백 없이 재요청:', t.slice(0, 200));
    r = await fetch(API, { method: 'POST', headers: base, body: JSON.stringify(body) });
  }
  if (!r.ok) throw new Error(`anthropic ${r.status} ${(await r.text()).slice(0, 200)}`);   // 본문 = 모델 부재·권한·한도 사유(로그 판독용)
  const m = await r.json();
  if (((m.usage || {}).iterations || []).some(it => it.type === 'fallback_message') && m.stop_reason !== 'refusal') {
    console.warn('claude 거절 → 서버 폴백 모델이 응답:', m.model);   // 어느 모델이 답했나(운영 가시성 · 단가는 그 모델 기준)
  }
  return m;
}
