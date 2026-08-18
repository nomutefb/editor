/* 이미지 스튜디오 제작 순번 SSOT — 「스튜디오 안 산출물은 모두 같은 번호줄을 공유한다」(운영자 260818 12차 «그 이미지 들도, 순번은 쭉 잇게해줄래 · 이미지 스튜디오 안에 있는거는 모두 같은 인덱싱을 공유하는거임»).
 *
 * 왜 모듈인가 = 카드 제작 문서에만 있던 발번기를 번역·AI 생성 문서가 각자 베끼면 그날부터 세 벌이 따로 센다(같은 번호가 두 산출물에 붙는다).
 *   카운터 키는 카드 제작이 260818 8차부터 쓰던 `nomute_jobseq` **그대로** = 새 키 신설 0 = 지금까지 매긴 번호 **다음부터** 이어진다(운영자 「쭉 잇게」).
 *
 * 왜 주소별 표인가 = 세 칸의 사정이 다르다 — 카드 제작은 발사 때 번호를 매겨 제작 기록에 실어 보내지만(src.jn),
 *   번역은 화면이 직접 굽고, AI 생성은 이력 자체를 서버 목록에서 조립한다(발사 시점에 번호를 실을 자리가 없다).
 *   그래서 「그 산출물 주소에 번호를 한 번 도장하고 다음부터 그 도장을 읽는다」가 세 칸 모두에 성립하는 유일한 축이다.
 *
 * ⚠ 번호는 **이 모듈이 들어온 시각 이후에 만들어진 산출물**만 받는다(`nomute_seqfrom`) = 운영자 260818 8차 「새로 발행하는 새로운것부터 001」 계약의 연장.
 *   그렇게 안 하면 이미 쌓인 수백 건이 한 번에 번호를 먹어 다음 제작이 갑자기 400번대로 뛴다.
 *   ⚠ 「칸별 첫 렌더 = 시드」로 두면 안 된다(첫 판 실측 사고) — 한 문서 안에서도 결과 칸이 이전 제작 칸보다 **먼저** 그려지면
 *     그 첫 렌더가 시드를 먹어치우고 곧바로 이어지는 이전 제작 수백 건이 전부 발번된다(실측 = 과거 항목이 002를 받았다).
 *     제작 시각으로 자르면 렌더 순서·부팅 순서·칸 개수와 무관하게 같은 답이 나온다.
 *   단 카드 제작이 이미 매겨 기록에 실어둔 번호(src.jn·jn)는 시각과 무관하게 그대로 계승한다(그 칸의 과거 번호는 살아 있다).
 * ⚠ 번호는 이 브라우저 축이다(카운터가 브라우저 저장소 = 8차 계약 그대로) — 기기가 다르면 자기 번호줄을 센다.
 * ⚠ 표는 기계산출물 = 손편집 금지. 저장 실패(시크릿 모드 등)는 fail-soft(그 세션 안에서만 이어 센다).
 */
(function () {
  var CNT = 'nomute_jobseq';    // 번호 카운터(카드 제작 8차 슬롯 = 공유 원천)
  var MAP = 'nomute_seqmap';    // 산출물 주소 → 번호(0 = 도입 전 과거분 = 무표기)
  var FROM = 'nomute_seqfrom';  // 이 모듈 도입 시각(이 시각 이후 제작분부터 번호를 준다)
  var CAP = 900;                // 표 상한(넘으면 번호 낮은 것부터 버린다 = 오래된 것부터)
  var mem = 0;                  // 저장 실패 환경의 세션 카운터

  function rd(k, d) { try { var v = JSON.parse(localStorage.getItem(k)); return (v && typeof v === 'object') ? v : d; } catch (e) { return d; } }
  function wr(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} }
  function key(u) { return String(u || '').split('?')[0]; }   // 주소 정규화 = 캐시버스트 꼬리(?v=·?t=) 무시 — 같은 산출물이 두 번 도장되지 않는다

  function issue() {   // 발번 = 재읽기 + 증가 + 즉시 저장(카드 제작 jobSeqIssue 정본 문법 그대로 = 형제 탭이 먼저 발번한 값을 안 덮는다)
    var v = 0; try { v = parseInt(localStorage.getItem(CNT), 10) || 0; } catch (e) {}
    if (v < mem) v = mem;
    mem = v + 1;
    try { localStorage.setItem(CNT, String(mem)); } catch (e) {}
    return mem;
  }
  /* 표는 메모리에 들고 있는다 — 이 함수들은 타일 렌더마다(그리고 10초 폴마다) 불려서 매번 저장소를 파싱하면
     항목 수백 개짜리 표를 계속 다시 읽는다(렌더 1타 예산·유휴 정숙 계약과 같은 축). 형제 탭이 발번하면 storage 이벤트로 버린다. */
  var _m = null;
  function rdMap() { if (!_m) _m = rd(MAP, {}); return _m; }
  function wrMap(m) { _m = m; wr(MAP, m); }
  try { window.addEventListener('storage', function (e) { if (e && (e.key === MAP || e.key === CNT)) _m = null; }); } catch (e) {}
  function of(url) { var n = rdMap()[key(url)]; return (typeof n === 'number' && n > 0) ? n : 0; }   // 0 = 번호 없음(무표기 = 오표기보다 무표기)
  function set(url, n) { if (!url || !(+n > 0)) return; var m = rdMap(); m[key(url)] = +n; prune(m); wrMap(m); }
  function prune(m) {
    var ks = Object.keys(m); if (ks.length <= CAP) return;
    ks.sort(function (a, b) { return (m[a] || 0) - (m[b] || 0); });
    for (var i = 0; i < ks.length - CAP; i++) delete m[ks[i]];
  }
  /* 그 칸이 지금 그리려는 목록을 통째로 넘긴다 — 표에 없는 산출물만 **제작 시각 오름차순**으로 발번한다.
     ⚠ 오름차순이 실효 조건 = 타일은 최신 먼저 정렬이라 그 순서로 발번하면 번호가 거꾸로 붙는다. */
  function since() {   // 도입 시각 = 처음 이 모듈이 실행된 순간(한 번만 기록)
    var v = 0; try { v = parseInt(localStorage.getItem(FROM), 10) || 0; } catch (e) {}
    if (!v) { v = Date.now(); try { localStorage.setItem(FROM, String(v)); } catch (e) {} }
    return v;
  }
  function tag(list) {
    if (!list || !list.length) return;
    var m = rdMap(), from = since(), pend = [], i;
    for (i = 0; i < list.length; i++) {
      var e = list[i]; if (!e || !e.url) continue;
      var k = key(e.url); if (m[k] != null) continue;
      var own = (e.jn != null && e.jn !== '') ? e.jn : (e.src && e.src.jn != null && e.src.jn !== '' ? e.src.jn : null);   // 카드 제작이 기록에 실어둔 번호
      pend.push({ k: k, ts: +(e.ts || 0), own: own });
    }
    for (i = 0; i < pend.length; i++) if (pend[i].own != null && isFinite(+pend[i].own)) m[pend[i].k] = +pend[i].own;   // 기록 동봉 번호는 도입 시각과 무관하게 계승
    var fresh = pend.filter(function (p) { return m[p.k] == null; }).sort(function (a, b) { return a.ts - b.ts; });   // ⚠ 오름차순 = 타일은 최신 먼저라 그 순서로 발번하면 번호가 거꾸로 붙는다
    for (i = 0; i < fresh.length; i++) m[fresh[i].k] = (fresh[i].ts > from) ? issue() : 0;   // 도입 전 제작분 = 0(무표기) · 그 뒤 = 공유 번호줄에서 발번
    if (pend.length) { prune(m); wrMap(m); }
  }
  window.nmSeq = { issue: issue, of: of, set: set, tag: tag, since: since };
})();
