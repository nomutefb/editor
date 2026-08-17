// Cloudflare Pages Function — 진행 중 제작 공유 원장(260817 · 운영자 "하드웨어를 바꾸든, 브라우저를 바꾸든
//   동시간에 들어가면 제작중인 내용이 동일하게 떠야되는데 그렇지가 않아").
//
// 무엇을 고치나 = 진행 중 작업 슬롯이 **브라우저 로컬 저장소에만** 있었다(nm-jobs.js `nm_*_pend`·`sb_jobs`).
//   260810 nm-jobs는 「한 브라우저 안에서 두 작업이 서로를 덮는 것」을 고쳤고, 260816 thumb는 storage 이벤트로
//   「같은 브라우저의 형제 탭」까지 넓혔다 — 그런데 storage 이벤트는 **같은 브라우저 안에서만** 울린다.
//   폰에서 걸고 PC로 가면(또는 크롬에서 걸고 사파리로 가면) 그 작업이 화면에서 통째로 사라진다.
//   러너는 계속 돌아 결과가 R2에 착지하는데 그 기기만 영영 모른다 = 운영자가 본 「제작중이 안 뜬다」의 실체.
//   ⚠ 완료분은 이미 기기 간 공유가 있었다(thumb-hist.json 병합 · ?recent= R2 발견) — 빠져 있던 건 「지금 돌고 있는 것」뿐.
//
// 계약(이 파일은 **원장**이지 판정기가 아니다)
//   · 기록 = functions/_middleware.js putLive(발사 성공 200 + ok:true + id) — 발사 API 28종이 지나는 한 관문 1자리.
//   · 완료 판정은 **여기서 안 한다** — 각 탭의 폴이 이미 완료 정본을 쥐고 있다(산출 경로·형태가 레인마다 다르고
//     thumb `out`은 R2 키가 아니라 공개 절대 URL이라 서버가 되짚으면 사본 판정이 하나 더 생긴다 = 갈릴 자리).
//     화면이 완료를 확정하면 POST {done:[…]}로 지운다. 알리기 전에 브라우저를 닫아도 다른 기기가 폴로 확인하고 지운다(자가치유).
//   · TTL 24h = nm-jobs.js 슬롯 TTL 동값(판정을 두 곳에 두면 갈린다) — 넘긴 레코드는 조회하는 김에 청소.
//   · 전 경로 fail-soft: R2 미바인딩·장애 = 빈 목록(화면은 종전대로 자기 로컬 슬롯만 쓴다 = 악화 경로 0).
const PFX = 'jobs/live/';
const TTL = 24 * 3600e3;
const CAP = 60;   // 응답 상한(서버 동시 캡 3 대비 충분 · 폭주 방어)

const J = (o, s = 200) => new Response(JSON.stringify(o), {   // seal-ok: 형제 중 유일 미보유인 _rate.js 는 응답을 만들지 않는 판정 헬퍼(캡 초과 사유 객체 ∨ null 반환)라 응답 문법이 없는 게 정당한 차이다
  status: s,
  headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' },   // 폴링 응답을 엣지가 굳히면 새 발사를 영영 못 본다(edit.js ?stat= 동문) · seal-ok: 위와 같은 사유(_rate.js = 응답 비생성 헬퍼)
});

const keyOf = (kind, id) => PFX + String(kind) + '-' + String(id).replace(/\//g, '_') + '.json';

export async function onRequestGet({ env }) {
  if (!env.R2) return J({ items: [], reason: 'r2-unbound' });
  const items = [], dead = [];
  try {
    let cursor;
    for (let page = 0; page < 3; page++) {   // 상한 3페이지 = 폭주 방어(edit.js ?recent= 관례)
      const l = await env.R2.list(cursor ? { prefix: PFX, limit: 1000, cursor } : { prefix: PFX, limit: 1000 });
      for (const o of (l.objects || [])) {
        // 만료는 본문을 열지 않고 업로드 시각으로 먼저 거른다(레코드 수만큼 get 하면 조회가 비싸진다)
        const up = o.uploaded ? new Date(o.uploaded).getTime() : 0;
        if (up && Date.now() - up > TTL) { dead.push(o.key); continue; }
        items.push(o.key);
      }
      if (!l.truncated) break;
      cursor = l.cursor;
    }
  } catch { return J({ items: [], reason: 'r2-error' }); }

  const out = [];
  for (const k of items.slice(0, CAP)) {
    try {
      const o = await env.R2.get(k);
      if (!o) continue;
      const r = JSON.parse(await o.text());
      if (!r || !r.id) { dead.push(k); continue; }
      if (Date.now() - (+r.t0 || 0) > TTL) { dead.push(k); continue; }   // 본문 t0 = 발사 시각 정본(업로드 시각과 어긋나도 이쪽이 맞다)
      out.push(r);
    } catch { dead.push(k); }   // 손상 레코드 = 청소 대상(조용히 쌓이면 목록이 영영 안 준다)
  }
  for (const k of dead.slice(0, 40)) { try { await env.R2.delete(k); } catch { /* 다음 회차 재시도 */ } }
  out.sort((a, b) => (+b.t0 || 0) - (+a.t0 || 0));   // 최신 먼저 = 화면 진행 중 큐 정렬 동축(nm-rail pendList)
  return J({ items: out });
}

// POST {done:[{kind,id}|"id", …]} — 화면이 완료·포기를 확정한 작업을 원장에서 뺀다.
//   kind를 같이 주면 키를 곧바로 짚고(조회 0), id만 오면 목록에서 찾아 지운다(구판 화면 하위호환).
export async function onRequestPost({ request, env }) {
  if (!env.R2) return J({ ok: true, n: 0, reason: 'r2-unbound' });
  let body;
  try { body = await request.json(); } catch { return J({ error: '잘못된 요청' }, 400); }
  const list = Array.isArray(body && body.done) ? body.done.slice(0, 40) : [];
  if (!list.length) return J({ ok: true, n: 0 });

  const direct = [], loose = new Set();
  for (const d of list) {
    if (typeof d === 'string') { if (/^[A-Za-z0-9._\-/]{1,80}$/.test(d)) loose.add(d); continue; }
    if (d && typeof d.id === 'string' && typeof d.kind === 'string'
      && /^[A-Za-z0-9._\-/]{1,80}$/.test(d.id) && /^[a-z0-9-]{1,24}$/.test(d.kind)) direct.push(keyOf(d.kind, d.id));
    else if (d && typeof d.id === 'string' && /^[A-Za-z0-9._\-/]{1,80}$/.test(d.id)) loose.add(d.id);
  }
  let n = 0;
  for (const k of direct) { try { await env.R2.delete(k); n++; } catch { /* 무해 */ } }
  if (loose.size) {
    try {
      const l = await env.R2.list({ prefix: PFX, limit: 1000 });
      for (const o of (l.objects || [])) {
        for (const id of loose) {
          if (o.key.endsWith('-' + id.replace(/\//g, '_') + '.json')) { try { await env.R2.delete(o.key); n++; } catch { /* 무해 */ } break; }
        }
      }
    } catch { /* 목록 실패 = 다음 회차 · TTL이 최후 그물 */ }
  }
  return J({ ok: true, n });
}
