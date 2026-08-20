// (260820) 발사 유실 봉합 SSOT — 카드 발사 실사고(uploads 98건 중 22건 산출 0 · CLAUDE.md 「카드 발사 유실」 항목)의
// 형제 이식(운영자 «같이 하되, 문제 없는데 고치는거 아닌지 주의»). 대상 = 「dispatch 1발 + 실패 시 queue/jobs 착지 +
// ok 응답」 모양의 레인만(14레인 실측 동형) — 각 레인의 **응답 모양·발사 입력은 무접촉**(그 검증 = 전/후 스냅샷 맞대조).
//
// ① dispatchWf = 워크플로 발사 재시도(3회 · 0.4s/0.8s 간격 · 회당 10s 상한{행 걸림 = 함수 통째 사망 5xx 축 차단} ·
//    404·422 류 영구 실패는 1발 중단 · 403은 2차 유량제한 축이라 재시도 대상).
//    ⚠ 드롭인 계약: 반환값은 응답 모양 {status, text()} — 기존 호출부의 `r.status === 204` 판정과 최종 502 문구의
//    `await r.text()`가 그대로 성립한다(text = 저장분 반환 = 재호출 안전 · 전 시도 네트워크 실패 = status 0).
//    `_note` = 큐 원장용 실패 사유(왜 큐로 왔는지가 남는다 — 구판은 사유가 어디에도 안 남아 사후 추적 불가).
// ② rescueJobs = 잠든 발사 회수 — 큐(queue/jobs)의 소비자가 맥 잡 워커 하나뿐이라(260815 우회 유산) 워커가 잠들면
//    발사가 영영 안 나오던 축. 발사 성공이 지나가는 자리(관문 _middleware.js = 발사 API 전 레인 공통 · 손 목록 0)와
//    thumb ?recent= 폴이 부른다. 재발사 원료 = 큐 원장의 wfYml(+wfInputs) 자기서술 — 레인별 재조립 사본 0.
//    ⚠ wfInputs 가 따로 있는 이유 = 4레인(make-cards·thumbredo·revise·revise-cards)은 맥 워커용 inputs 에
//    id 를 덧붙여 저장해서 그대로 재발사하면 워크플로 미정의 입력 = 422 다. 나머지 레인은 inputs == 발사 입력.
//    ⚠ claim = 회수 임대(90s) — 병렬 발사·폴이 같은 잡을 겹쳐 집는 창을 초 단위 → ms 로 줄인다(유료 레인 이중 발사 방어 ·
//    실패 시 임대만 남아 다음 회수가 90s 뒤 재시도 = 깃허브 장애 중 재발사 폭주도 같이 눌린다).
//    ⚠ 24h 초과 잡·맥 워커 전용 형식(미들웨어 stamp-kind-rand · id 계약 없음)은 무접촉 = 종전대로 맥 몫.
const REPO = 'nomutefb/editor';
export const DISPATCH_TRIES = 3, DISPATCH_TMO_MS = 10000;

export async function dispatchWf(env, yml, body) {
  let note = '', lastStatus = 0, lastText = '';
  for (let t = 0; t < DISPATCH_TRIES; t++) {
    if (t) await new Promise(rs => setTimeout(rs, 400 * t));
    try {
      const ac = new AbortController(); const tm = setTimeout(() => ac.abort(), DISPATCH_TMO_MS);
      const r = await fetch(`https://api.github.com/repos/${REPO}/actions/workflows/${yml}/dispatches`, {
        method: 'POST',
        headers: {
          authorization: `Bearer ${env.GH_TOKEN}`,
          accept: 'application/vnd.github+json',
          'user-agent': 'nomute-viewer',
          'x-github-api-version': '2022-11-28',
        },
        body: JSON.stringify(body), signal: ac.signal,
      });
      clearTimeout(tm);
      if (r.status === 204) return { status: 204, text: async () => '', _note: '' };
      lastStatus = r.status; lastText = await r.text().catch(() => '');
      note = `GitHub ${r.status}: ${lastText.slice(0, 200)}`;
      if (r.status >= 400 && r.status < 500 && r.status !== 403 && r.status !== 408 && r.status !== 429) break;   // 영구 실패(404·422 등) = 재시도 무익
    } catch (e) { lastStatus = 0; lastText = note = '네트워크: ' + String(e && e.message || e).slice(0, 120); }
  }
  return { status: lastStatus, text: async () => lastText, _note: note };
}

export const idTsKst = id => { const m = String(id).match(/^(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})/); if (!m) return 0; const t = Date.parse('20' + m[1] + '-' + m[2] + '-' + m[3] + 'T' + m[4] + ':' + m[5] + ':' + m[6] + '+09:00'); return Number.isFinite(t) ? t : 0; };   // id 선두 12자리 = KST 발급 시각(발사 API id 계약 · 뷰어 thIdTs 미러)

export async function rescueJobs(env, kind, legacy) {
  try {
    if (!env.R2 || !env.GH_TOKEN || !/^[a-z0-9-]+$/.test(String(kind))) return;
    const l = await env.R2.list({ prefix: 'queue/jobs/', limit: 100 });
    let n = 0;
    for (const o of (l.objects || [])) {
      if (n >= 2) break;   // 회당 2건 상한(폭주 방어 · 다음 발사·폴이 이어받는다)
      const m = o.key.match(new RegExp('^queue/jobs/(\\d{12}-[A-Za-z0-9_-]{1,52})-' + kind + '\\.json$'));
      if (!m) continue;
      let rec = null; try { rec = await (await env.R2.get(o.key)).json(); } catch { continue; }
      if (!rec || rec.kind !== kind) continue;
      const qts = Date.parse((rec && rec.ts) || '') || idTsKst(m[1]);   // 유효기간 축 = 큐에 담긴 시각(원장 ts) 우선 — id 시각으로만 재면 재합성(옛 산출 id 재사용) 정상 잡이 억울하게 버려진다 · ts 없는 옛 원장 = id 시각 폴백
      if (!qts || Date.now() - qts > 24 * 3600e3) continue;   // 24h 넘은 잡 = 되살리면 유령 「제작중」(뷰어 재개 TTL 동값)
      if (rec.claim && Date.now() - rec.claim < 90e3) continue;   // 회수 임대 중 = 다른 실행이 방금 집었다
      let yml = rec.wfYml, inputs = (rec.wfInputs && typeof rec.wfInputs === 'object') ? rec.wfInputs : (rec.wfYml ? rec.inputs : null);
      if ((!yml || !inputs) && typeof legacy === 'function') { const lb = legacy(rec); if (lb && lb.yml && lb.inputs) { yml = lb.yml; inputs = lb.inputs; } }   // 자기서술 없는 옛 원장 = 레인이 준 재조립기(현행 = thumb 뿐)
      if (!yml || !inputs) continue;   // 재발사 원료 없음 = 종전대로 맥 워커 몫
      try { await env.R2.put(o.key, JSON.stringify({ ...rec, claim: Date.now() })); } catch {}
      const d = await dispatchWf(env, yml, { ref: 'main', inputs });
      if (d.status === 204) { try { await env.R2.delete(o.key); } catch {} n++; }
    }
  } catch { /* 회수 실패가 본 요청을 못 죽인다 */ }
}
