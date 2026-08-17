// Cloudflare Pages Function — 영상 스튜디오 결과·이전 제작의 **기기·브라우저 간 공유** 읽기 전용 창구
// (운영자 260818 「같은 도메인으로 같은 메뉴에 들어갔으면 어떤 조건에서든 같은 내용이 나오게」).
//
// 왜: `viewer/nm-rail.js`(영상 5탭 공용 레일)는 그 브라우저 localStorage 단독이었다 → 폰에서 만든 것이
//     PC 에서 통째로 안 보였다. 260818 1차에서 편집 탭은 `api/edit?recent=` 를 이미 갖고 있어 바로 붙었지만,
//     **콘티·음원은 그 창구 자체가 없어서** 못 붙었다(실측 = api/sb·song 전건 `recent=` 미보유 → GET 이 셸 HTML 폴백).
//     이 파일이 그 빠진 절반이다.
//
// ⚠️ 신설 파일인 이유 = **리스크 격리**(운영자 260818 2차 「도중에 다른 기능 안건드리게, 리스크 매우매우 신경써서」).
//     기존 `api/sb.js`·`api/song.js` 에 분기를 심으면 그 파일의 **발사 경로와 한 함수를 공유**하게 되어,
//     이 읽기 기능의 실수가 제작 발사를 죽일 수 있다. 새 파일은 GET 하나뿐이라 그 접점이 물리적으로 0이다.
//     (같은 이유로 이 파일에는 POST·PUT 이 없다 = 쓰기 권한 0 · GH_TOKEN 미사용 = 커밋 경로 0.)
//
// 문법 정본 = `functions/api/trhist.js` onRequestGet **100% 계승**(값·구조 창작 0) —
//   KST 12자리 선두 id 컷오프(startAfter)로 전체 스캔 없이 최근 창만 · 3페이지 상한 · 캡 60 · 최신 먼저 ·
//   R2 미바인딩·장애 = 빈 목록(클라는 종전 로컬 단독 = fail-soft).
//
// 흐름: GET /api/caphist?recent=<시간>[&k=sb|song] → { items:[{id,url,cap}] }
//   레일은 목록이 url 을 직접 주면 개별 조회를 **건너뛴다**(nm-rail srvSync 의 `!o.srvstat` 분기) →
//   왕복 1회로 끝난다 = 편집(`?stat=` 개별 조회 필요)보다 오히려 싸다.
//
// ⚠️ 접두별 대표 키를 **정확 정규식**으로 못박는다 — 같은 폴더에 중간 산출(원본·조각·메타)이 함께 앉으므로
//   느슨하게 잡으면 이전 제작에 쓰레기가 뜬다. 대표 = 「그 탭이 운영자에게 내주는 완성물」 1개뿐:
//     song = `song_out/<id>/song.<mp3|wav|m4a>`  (러너 `song_out/<id>/song.mp3` + song.json 중 미디어만)
//     sb   = `sb_out/<id>/sheet.jpg`             (러너 sb_sheet.py KINDS board → sheet.jpg · 260817 conti 폐지분 제외)
//   ⚠️ 큐영상(vd)은 이 창구 대상이 **아니다** — 산출이 R2 가 아니라 레포 `viewer/vd_out/<id>/video.json` 커밋이라
//     이미 전 기기 공유가 구조적으로 성립한다(별 축 = 폴더 인덱스). 프롬프팅(k)도 아니다(산출이 텍스트 =
//     썸네일 타일에 그릴 그림 0 = `check_cap_rail_land._CAP_LAND_EXEMPT` 계약).
const R2_BASE = 'https://pub-6121e8a6f6194091b5502a72ed28a87b.r2.dev';   // = trhist.js·thumb.js R2_BASE(시크릿 R2_PUBLIC_BASE). ⚠️ 베이스 변경 시 함께 갱신.

// 접두 사전 = 대표 산출 1종씩. 새 영상 탭이 생기면 여기 1줄(레일 쪽 변경 0).
const LANES = {
  song: { prefix: 'song_out/', re: /^song_out\/(\d{12}[A-Za-z0-9_-]{0,52})\/song\.(mp3|wav|m4a)$/, cap: '음원' },
  sb: { prefix: 'sb_out/', re: /^sb_out\/(\d{12}[A-Za-z0-9_-]{0,52})\/sheet\.jpg$/, cap: '콘티' },
};

// id 앞 12자리 = KST 벽시계 도장(YYMMDDHHMMSS · 발사 시점 발급 규칙) → epoch ms.
// ⚠️ ts 를 반드시 실어야 한다 = 레일이 시각으로 정렬·표기하고, 값이 없으면 그 항목이 **화면에서 통째로 빠진다**
//   (실측 260818 = ts 미동봉 → 타일 0). 파싱 실패분은 R2 업로드 시각으로 폴백(둘 다 없으면 0 = 레일이 뒤로 정렬).
function tsOf(id, uploaded) {
  const m = /^(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})/.exec(String(id || ''));
  if (m) {
    const t = Date.UTC(2000 + +m[1], +m[2] - 1, +m[3], +m[4], +m[5], +m[6]) - 9 * 3600e3;   // KST 벽시계 → UTC(도장 발급 축의 역산)
    if (Number.isFinite(t)) return t;
  }
  const u = uploaded ? Date.parse(uploaded) : NaN;
  return Number.isFinite(u) ? u : 0;
}

export async function onRequestGet({ request, env }) {
  const j = (o, s = 200) => new Response(JSON.stringify(o), { status: s, headers: { 'content-type': 'application/json', 'cache-control': 'no-store' } });   // seal-ok: 응답 조립 관용구 = 형제 59개 API 와 동일. 미보유 1건 `_rate.js` 는 API 가 아니라 접두 `_` 헬퍼(rateGate 판정만 하고 Response 를 만들지 않는다) = 미보유가 정당한 차이(맥락 앵커 미신설 축의 알려진 위양성 유형).
  const q = new URL(request.url).searchParams;
  if (q.get('recent') == null) return j({ error: 'recent 파라미터 필요' }, 400);
  if (!env.R2) return j({ items: [], reason: 'r2-unbound' });   // 미바인딩 = 빈 목록(트리거 아님 · trhist 동문)
  const want = String(q.get('k') || '').trim();
  const lanes = Object.prototype.hasOwnProperty.call(LANES, want) ? [want] : Object.keys(LANES);   // ?k= 미지정·미인식 = 전 레인(프로토타입 키 차단 = hasOwnProperty)
  const hrs = Math.max(1, Math.min(48, +q.get('recent') || 24));
  const d = new Date(Date.now() - hrs * 3600e3 + 9 * 3600e3);   // KST 벽시계 = UTC+9(id 도장과 동일 축 · trhist.js 동문)
  const p2 = n => String(n).padStart(2, '0');
  const cut = String(d.getUTCFullYear()).slice(2) + p2(d.getUTCMonth() + 1) + p2(d.getUTCDate()) + p2(d.getUTCHours()) + p2(d.getUTCMinutes()) + p2(d.getUTCSeconds());
  let base = R2_BASE;
  if (env.R2_PUBLIC_BASE) { try { base = new URL(env.R2_PUBLIC_BASE).origin; } catch { /* 잘못된 env → 하드코딩(trhist 동문) */ } }
  const items = [];
  try {
    for (const name of lanes) {
      const L = LANES[name]; let cursor;
      for (let i = 0; i < 3; i++) {   // 상한 3페이지(trhist·thumb 동문 · 24h 창 실사용량 대비 여유)
        const l = await env.R2.list(cursor ? { prefix: L.prefix, limit: 1000, cursor } : { prefix: L.prefix, startAfter: L.prefix + cut, limit: 1000 });
        for (const o of (l.objects || [])) { const m = o.key.match(L.re); if (m) items.push({ id: m[1], url: `${base}/${o.key}`, cap: L.cap, ts: tsOf(m[1], o.uploaded) }); }
        if (!l.truncated) break; cursor = l.cursor;
      }
    }
  } catch (e) { return j({ items: [], reason: 'r2-error' }); }   // R2 장애 = 빈 목록(클라는 종전 로컬 단독 유지)
  return j({ items: items.sort((a, b) => (a.id < b.id ? 1 : -1)).slice(0, 60) });   // 최신 먼저 · 캡 60(trhist·thumb 동문)
}
