/* 결과·이전 제작 레일 부품 SSOT — 상속 1줄로 어느 스튜디오 탭에도 같은 세트가 선다(운영자 260806 "항상 저렇게 유지되어야하고, 사진끼리는 저렇게 공유하고, 영상끼리도 저렇게 공유할수있게해줘").
 * ─────────────────────────────────────────────────────────────────────────────
 * 무엇 = 「결과 = [요약 줄(완료 · N장 · 시각 + 수정 · 전체 다운로드)] + [개별 썸네일 타일]」 + 「이전 제작」 한 세트.
 *   부품·값 = 이미지 스튜디오 정본 100% 사본(마크업 = thumb `.out` 블록 · CSS = nm-hist.css `.hist-*` + nm-job.css `.job*` · 신규 클래스·값·색 0).
 *   ⚠ 마크업을 **여기서 한 번만** 만든다 = 표면마다 사본을 두지 않는다. 260806 하루에 이 레일이 네 번 갈라졌고(결론형/썸네일형 · 타일 배경 투명 · 요약 줄 부재 · 마진 상쇄 10px)
 *   전부 운영자 눈이 유일한 검출기였다 — 사본이 있는 한 같은 일이 반복된다는 게 그날의 결론이라, 신규 표면은 **사본 대신 상속**으로 간다.
 *
 * 데이터 격리 = 스코프별 저장소(운영자 260806 "근데 사진 과 영상은 작업 결과를 공유하지 않음 - 형태 목업만 일치").
 *   img = `nomute_thumb_hist`(이미지 스튜디오 5탭이 이미 쓰는 공유 키 · 이 모듈은 **읽지도 쓰지도 않는다** = 그쪽은 종전 자체 배선 유지)
 *   cap = `nomute_cap_hist`(영상 스튜디오 5탭 전용 · 신설) → 영상끼리는 공유, 사진과는 완전 분리.
 *
 * 쓰는 법(신규 탭 3줄):
 *   <link rel="stylesheet" href="nm-hist.css"> <link rel="stylesheet" href="nm-job.css"> <script src="nm-rail.js"></script>
 *   그리고 마운트 1줄 = nmRail.mount(document.getElementById('out'), { scope:'cap', dlname:'video.mp4' })
 *   완료 시 1줄 = nmRail.add({ url, cap:'편집', dlname:'…' })   // ts 생략 = 지금
 *
 * 의존 = nm-svg.js(DOWNLOAD_SVG·EDIT_SVG) · nm-hist.css · nm-job.css · 각 문서 :root(--hist-accent/--hist-rgb/--pan/--line).
 */
(function () {
  'use strict';
  if (window.nmRail) return;   // 중복 로드 = 무동작(idempotent · nm-clip/nm-sync 관례)

  var KEYS = { img: 'nomute_thumb_hist', cap: 'nomute_cap_hist' };   // ⚠ 스코프별 저장소 = 사진↔영상 결과 격리 계약(운영자 260806) — 한 키로 합치면 영상 결과가 사진 레일에 섞인다
  var HMS = 12 * 3600e3;      // 보관창 = 이미지 정본 동값(12h 로컬 브리지)
  var HMAX = 240;             // 상한 = thumb THUMB_HMAX 동값
  var T0 = Date.now();        // 이 문서 부팅 = '이번 세션' 경계(이미지 GENI_T0·TR_T0 동문)
  var mounts = [];            // 이 문서에 마운트된 레일들(보통 1개)

  function toText(s) { return String(s == null ? '' : s); }   // ⚠ 이스케이프 아님 = **textContent 전용 캐스팅**(운영자 260806 평의회7 ③ — 구 이름 `esc`는 함정이었다: 두 줄 아래 innerHTML에 그 이름을 믿고 쓰면 즉시 XSS). innerHTML에는 절대 넣지 마라.
  function keyOf(u) { return String(u || '').split('?')[0].replace(/^https?:\/\/[^/]+\//, ''); }   // 중복판정 키 = 이미지 정본 동문(호스트 제거)
  function load(scope) { try { var a = JSON.parse(localStorage.getItem(KEYS[scope]) || '[]'); return Array.isArray(a) ? a : []; } catch (e) { return []; } }
  function save(scope, a) { try { localStorage.setItem(KEYS[scope], JSON.stringify(a)); return true; } catch (e) { return false; } }   // 성패 반환 = 쿼터 초과·프라이빗 모드에서 「성공한 척」 하지 않는다(운영자 260806 평의회1 ⑤)

  /* ══ 기기·브라우저 간 공유(운영자 260818 「같은 도메인으로 같은 메뉴에 들어갔으면 어떤 조건에서든 같은 내용이 나오게」) ══
     ⚠ 진단 = 이 레일은 **그 브라우저의 localStorage 단독**이었다(위 load/save가 전부). 그래서 폰에서 만든 영상이
       PC 에서 통째로 안 보이고, 같은 주소·같은 메뉴인데 기기마다 다른 목록이 뜬다 = 「다른 저장소인 것처럼 따로 논다」의 실체.
       ⚠ 파일은 멀쩡히 보관함에 있다 — 실측 260818 = `/api/edit?recent=48` 이 영상 8건을 정상 반환하는데 레일이
         그 경로를 **한 번도 부르지 않았다**(모듈 머리 주석은 「공유 이력」이라 적혀 있었지만 코드에 그 층이 없었다).
     ⚠ 이미지 스튜디오는 이 층을 이미 갖고 있었다(thumb.html = 서버 인덱스 thumb-hist.json 병합 + `?recent=` 보관함
       발견 + 미보유 id 개별 조회) → **그 문법을 그대로 이식한다**(값·구조 창작 0 · 260817 진행중 작업 공유와 같은 축).
     설계 = ⓐ 목록 API(`data-srv`)로 최근 id 발견 → ⓑ 로컬·캐시에 없는 id만 개별 조회(`data-srvstat`)로 url 확보
       → ⓒ 메모리 캐시 SRV 에 적재 → ⓓ render 가 로컬과 **url 기준 dedup 병합**.
     ⚠ 로컬에 안 쓴다 = 남의 기기 제작분이 이 기기 12h 브리지 저장소를 밀어내지 않는다(HMAX 상한 경합 0 · 격리 유지).
     ⚠ 전 경로 fail-soft = 서버·회선 장애면 종전대로 로컬만 그린다(화면 오류 0). */
  var SRV = { img: [], cap: [] };      // 서버(보관함) 발견 이력 = 메모리 전용 · 스코프 격리는 KEYS 와 같은 축
  var srvSeen = { img: {}, cap: {} };  // 조회 완료 id = 같은 id 재조회 0(콜 폭주 방어)
  var srvBusy = {};
  /* ⚠️ 보관창 비대칭이 계약이다(260818 2차 실측 봉합) — 로컬 12h(HMS) 창은 **이 기기 브리지**의 수명이고,
     서버(보관함) 발견분은 **만료 없음**이다(이미지 정본 = 「서버 인덱스 thumb-hist.json = 전 기기·만료 없음·캡 400」
     vs 「localStorage는 완성 직후~빌드 배포 사이 브리지(12h)」). 두 층에 같은 창을 걸면 **어제 만든 게 안 보인다**
     = 「어떤 조건에서든 같은 내용」 계약 위반이고, 실측으로 그 상태였다(가짜 서버 2건 → 타일 0 · 1차 편집 축도
     보관함 8건 중 최근 3건만 떴다 = 5건이 이 창에 잘렸다). → prune 은 **로컬 조각에만** 적용한다.
     ⚠ 상한은 그대로 살아 있다(render 의 HMAX·캡 60 = 서버 API 쪽 slice) = 무한 증가 0. */
  function merged(scope) {             // 표시 정본 = 로컬(이 기기 즉시분 · 12h 창) + 서버(전 기기분 · 만료 없음) · url 키 dedup
    var out = [], k = {};
    prune(load(scope)).concat(SRV[scope] || []).forEach(function (e) {
      if (!e || !e.url) return;
      var kk = keyOf(e.url); if (k[kk]) return; k[kk] = 1; out.push(e);
    });
    return out;
  }
  function srvSync(m) {                // ⓐ~ⓒ — data-srv 를 선언한 탭만 동작(미선언 탭 = 종전 로컬 단독)
    var o = m.opt, scope = o.scope;
    if (!o.srv || srvBusy[scope]) return;
    srvBusy[scope] = 1;
    fetch(o.srv, { cache: 'no-store' }).then(function (r) { return r.ok ? r.json() : null; }).then(function (d) {
      var items = d && (Array.isArray(d) ? d : d.items);
      if (!Array.isArray(items)) return null;
      var have = {};
      load(scope).forEach(function (e) { if (e && e.url) have[String(e.url).split('/').slice(-2)[0]] = 1; });
      var todo = items.map(function (it) { return it && (it.id || it); })
        .filter(function (id) { return id && typeof id === 'string' && !srvSeen[scope][id] && !have[id]; }).slice(0, 24);
      if (!o.srvstat) {   // 목록이 url 을 직접 주는 형태(trhist 문법) = 개별 조회 불요
        items.forEach(function (it) { if (it && it.url && SAFE_URL.test(String(it.url))) addSrv(scope, it); });
        return null;
      }
      return Promise.all(todo.map(function (id) {
        srvSeen[scope][id] = 1;
        return fetch(o.srvstat + encodeURIComponent(id), { cache: 'no-store' })
          .then(function (r) { return r.ok ? r.json() : null; })
          .then(function (v) { if (v && v.url) addSrv(scope, { id: id, url: v.url, ts: Date.parse(v.ts || '') || 0, cap: v.cap || '' }); })
          .catch(function () { });
      }));
    }).catch(function () { }).then(function () {
      srvBusy[scope] = 0;
      mounts.forEach(function (x) { if (x.opt.scope === scope) { x.sig = null; render(x); } });   // sig 무효화 = 병합분 반영
    });
  }
  function addSrv(scope, e) {
    if (!e || !e.url || !SAFE_URL.test(String(e.url))) return;
    var kk = keyOf(e.url);
    for (var i = 0; i < SRV[scope].length; i++) if (keyOf(SRV[scope][i].url) === kk) return;
    SRV[scope].push({ url: e.url, ts: e.ts || 0, cap: e.cap || '', id: e.id || '' });
  }
  var SAFE_URL = /^(https?:|blob:|data:image\/)/i;   // 적재 허용 스킴 = 이미지·영상 산출이 실제로 오는 3종(javascript: 등 차단 · 평의회7 ④)
  /* 영상·소리 판정(운영자 260810 "이전 제작이 안떠") — 이 레일은 이미지 스튜디오에서 왔고 타일을 `<img>`로만 그렸다.
     영상 스튜디오 산출은 mp4·mp3라 img 디코드가 **반드시** 실패하고, 구 onerror가 그걸 「죽은 슬롯」으로 읽어 타일을 지웠다
     → 저장소엔 남는데 화면은 영구 빈칸(무증상 = 콘솔 에러 0). 확장자 축으로 갈라 미디어 태그로 그린다. */
  var AV_RE = /\.(mp4|webm|mov|m4v|mp3|m4a|wav|aac|ogg|flac)(\?|#|$)/i;
  function isAV(u) { return AV_RE.test(String(u || '')); }
  function mkAV(u) {   // 영상·소리 타일 = `<video>` 1종(소리 파일도 같은 태그 = 검은 판 + 캡션칩이 무엇인지 말한다 · 새 부품·값 창작 0)
    var v = document.createElement('video');
    v.muted = true; v.playsInline = true; v.setAttribute('playsinline', ''); v.preload = 'metadata'; v.src = u;
    return v;   // ⚠ 실패해도 지우지 않는다 — 파일은 R2에 살아 있고 [↓] 다운로드는 그대로 동작한다(제작물이 목록에서 사라지는 쪽이 훨씬 비싼 사고)
  }
  function prune(a) { var cut = Date.now() - HMS; return a.filter(function (e) { return e && e.ts && e.ts >= cut; }); }

  function histTime(ts) {   // 표기 = 이미지 정본 동문(오늘/어제 · M/D 접두 · 오전/오후 H:MM)
    var d = new Date(ts), h = d.getHours(), m = d.getMinutes(), ap = h < 12 ? '오전' : '오후';
    h = h % 12 || 12;
    var now = new Date();
    var dd = Math.round((new Date(now.getFullYear(), now.getMonth(), now.getDate()) - new Date(d.getFullYear(), d.getMonth(), d.getDate())) / 86400000);
    var pre = dd === 0 ? '오늘 ' : dd === 1 ? '어제 ' : (d.getMonth() + 1) + '/' + d.getDate() + ' ';
    return pre + ap + ' ' + h + ':' + String(m).padStart(2, '0');
  }
  function dlBlob(url, name) {   // R2(교차출처) = api/dl 프록시 강제 저장 · 비R2 = download 직접 — 이미지 정본 동문
    var a = document.createElement('a');
    a.href = /\/\/pub-[0-9a-fA-F]+\.r2\.dev\//.test(url) ? ('api/dl?u=' + encodeURIComponent(url) + '&n=' + encodeURIComponent(name || 'out')) : url;
    a.download = name || 'out';
    document.body.appendChild(a); a.click(); a.remove();
  }
  var DL_SVG = function () { return window.DOWNLOAD_SVG || '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v12"/><path d="M7 11l5 5 5-5"/><path d="M5 21h14"/></svg>'   /* 폴백도 nm-svg.js DOWNLOAD_SVG 정본 바이트 그대로(구 폴백은 밑변 `M4 21h16` = 정본 `M5 21h14`와 **다른 그림**이었다 · 운영자 260806 평의회5 실측) */; };
  var CK_SVG = function () { return window.CHECK_SVG || '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M5 13l4 4L19 7"/></svg>'; };
  var CHEV = '<svg class="hist-ar" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9l6 6 6-6"/></svg>';

  /* 레일 셸 = thumb `.out` 정본 마크업 그대로(결과 헤더 → 요약 줄 → 타일 → 빈 상태 → 이전 제작 접이).
     ⚠ 순서가 계약이다 — 요약 줄이 **타일 위**(운영자 260806 "이게 저 개별 썸네일형 위에 있어야됨 · 원래 저게 세트였는데 갈라진거네"). */
  function shellHTML(id) {
    return '<button class="hist-h car-h" id="' + id + 'ResH" type="button" aria-expanded="true" aria-controls="' + id + 'ResJobs ' + id + 'ResGrid">'   /* aria-controls = thumb 접이 정본 계약(무엇이 열리는지 SR 연결 · 운영자 260806 평의회7 ⑥) */
      + '<span class="hist-ttl"><span class="car-bul" aria-hidden="true">•</span>결과 <span class="hist-cnt" id="' + id + 'ResCnt">(0)</span></span>' + CHEV + '</button>'
      + '<div class="jobs" id="' + id + 'ResJobs"></div>'
      + '<div class="hist-grid" id="' + id + 'ResGrid"></div>'
      + '<div class="hist-empty" id="' + id + 'ResEmpty">아직 제작한 게 없습니다</div>'
      + '<div class="hist" id="' + id + 'Hist">'
      + '<button class="hist-h" id="' + id + 'PrevH" type="button" aria-expanded="false" aria-controls="' + id + 'PrevBody">'
      + '<span class="hist-ttl"><span class="hist-bul" aria-hidden="true">•</span>이전 제작 <span class="hist-cnt" id="' + id + 'PrevCnt">(0)</span></span>'
      + '<span class="hist-note">전 기기 제작 내역</span>' + CHEV + '</button>'
      + '<div class="hist-body" id="' + id + 'PrevBody" hidden>'
      + '<div class="hist-empty" id="' + id + 'PrevEmpty" hidden>아직 제작한 게 없습니다</div>'
      + '<div class="hist-grid" id="' + id + 'PrevGrid"></div></div></div>';
  }

  function tileEl(m, e, gridSel, cntSel) {   // 항목 = 이미지 정본 `.hist-it` 빌더 그대로(시각 라벨 + 타일 + 캡션칩 + [연필][↓])
    var it = document.createElement('div'); it.className = 'hist-it';
    var hd = document.createElement('div'); hd.className = 'hist-hd'; hd.textContent = histTime(e.ts);
    var th = document.createElement('div'); th.className = 'hist-thumb';
    var dl = document.createElement('a'); dl.className = 'imgdl dlbtn'; dl.href = e.url;
    dl.setAttribute('aria-label', '다운로드'); dl.innerHTML = DL_SVG();
    dl.addEventListener('click', function (ev) { ev.preventDefault(); ev.stopPropagation(); dlBlob(e.url, e.dlname || m.opt.dlname); });
    var av = isAV(e.url);   // 영상·소리 산출 = `<img>`로는 **절대** 못 그린다(디코드 실패 = onerror 확정)
    var img;
    if (av && !e.poster) { img = mkAV(e.url); }   // 포스터 없는 영상·소리 = 미디어 자신으로 그린다(첫 프레임이 곧 포스터)
    else {
      img = document.createElement('img'); img.loading = 'lazy'; img.alt = ''; img.src = e.poster || e.url;
      img.onerror = function () {   // ⚠ 포스터 실패 ≠ 원본 실패(운영자 260806 평의회1 ② — 구판은 포스터 404 하나로 멀쩡한 영상 항목을 영구 삭제했고 같은 url 재적재도 중복차단에 막혀 리로드 전엔 복구 불가였다)
        if (av) { try { img.replaceWith(mkAV(e.url)); } catch (er) { it.remove(); } return; }   // ⚠ 영상·소리는 원본 재시도가 **구조적으로 무의미**하다(mp4를 img에 다시 넣는 것 = 같은 실패) → 미디어 태그로 강등해 타일을 살린다. 구판은 여기서 `it.remove()`까지 흘러 **저장소엔 2건인데 화면은 「아직 제작한 게 없습니다」**였다(운영자 260810 "이전 제작이 안떠" 실측 = 결과 0·이전 0·store 2)
        if (e.poster && img.src !== e.url && !img.dataset.rt) { img.dataset.rt = '1'; img.src = e.url; return; }   // 1회 원본 재시도 = index `chThFail` dataset.rt 문법 계승(무한루프 0)
        it.remove(); m.dead[keyOf(e.url)] = 1;
        var cc = document.getElementById(cntSel); var g = document.getElementById(gridSel); if (cc && g) cc.textContent = '(' + g.children.length + ')';
      };   // 죽은 슬롯 제거 + 카운트 정정 = 이미지 정본 동문
    }
    var cap = document.createElement('span'); cap.className = 'hist-cap'; cap.textContent = toText(e.cap);
    if (e.varStr) { var v = document.createElement('span'); v.className = 'hist-cap-v'; v.textContent = (cap.textContent ? ' ' : '') + e.varStr; cap.appendChild(v); }   // 캡션과 값이 붙어 「편집9:16」으로 읽히던 자리(실측 260811) — 띄어쓰기 한 칸(값·부품 변경 0)
    th.append(dl, img, cap);
    /* 수정(연필) = 복원 경로를 **가진 표면만** 그린다(갈 곳 없는 버튼 금지 = 이미지 정본 canEditSrc 계약 동문).
       ⚠ 문서가 훅으로도 줄 수 있다(`window.nmJobEdit`) — 이 레일은 자동 마운트라 각 문서가 mount 옵션을 넘길 자리가 없다
       (운영자 260811 "여기도 수정버튼 있게 해주고(원본을 가지고 있다면)" · 진행 중 행의 nmJobOpen과 같은 문법). */
    var onEd = (typeof m.opt.onEdit === 'function') ? m.opt.onEdit : (typeof window.nmJobEdit === 'function' ? window.nmJobEdit : null);
    if (e.src && e.src.app && onEd) {
      var ed = document.createElement('button'); ed.type = 'button'; ed.className = 'imgedit'; ed.title = '이 설정으로 수정'; ed.setAttribute('aria-label', '수정');
      if (window.EDIT_SVG) {   // 아이콘 SSOT 미도달 = 버튼을 **안 그린다**(구판 `|| ''`는 내용 0인 포커스 가능 버튼을 만들어 「갈 곳 없는 버튼 금지」 계약과 자기모순 · 운영자 260806 평의회7 ⑤)
        ed.innerHTML = window.EDIT_SVG;
        ed.addEventListener('click', function (ev) { ev.preventDefault(); ev.stopPropagation(); onEd(e.src, e.url); });
        th.appendChild(ed);
      }
    }
    /* 타일 탭 = **그 제작물을 위 결과 창에서 다시 본다**(운영자 260812 "해당 건을 클릭해도 바로 위에 보는 창에서 볼 수가 없거든? · 바로 위에 보는 창은 미리보기가 아니라, 제작 완료된 거 보여주는 부분임").
       ⚠ 구판 타일엔 [연필][↓] 두 버튼뿐이고 **타일 본체는 정적**이었다 — 눌러도 아무 일이 없고 콘솔 에러도 0(무증상).
       게다가 편집 탭은 레일이 든 작업을 작업 내역에서 **빼기까지 해서**(jlRailIds) 그 제작물을 다시 열 길이 화면에 **하나도 없었다**(딥링크뿐).
       화면 주인 전환은 탭마다 생김새가 달라 이 모듈이 못 정한다 → 문서가 `window.nmJobShow(url, entry)`를 정의하면 그때만 누를 수 있게 그린다
       (미정의 = 종전 정적 타일 = 회귀 0 · 진행 중 행의 nmJobOpen·연필의 nmJobEdit과 **같은 문법**). */
    var onShow = (typeof m.opt.onShow === 'function') ? m.opt.onShow : (typeof window.nmJobShow === 'function' ? window.nmJobShow : null);
    if (onShow) {
      th.classList.add('hist-go');   // 어포던스(손가락 커서·눌림)는 **실제로 갈 곳이 있을 때만** 붙는다(어포던스 비계승 계약)
      th.setAttribute('role', 'button'); th.tabIndex = 0;
      th.title = '탭 = 이 제작물을 위 결과 창에서 보기';
      var goT = function (ev) { if (ev) ev.preventDefault(); try { onShow(e.url, e); } catch (er) {} };
      th.addEventListener('click', goT);
      th.addEventListener('keydown', function (ev) { if (ev.key === 'Enter' || ev.key === ' ') goT(ev); });   // [↓]·[연필]은 각자 stopPropagation 보유 = 버튼을 눌렀을 때 타일까지 같이 열리지 않는다
    }
    it.append(hd, th);
    return it;
  }

  /* ══ 진행 중 큐(운영자 260810 "제작 중인거는 그위 결과에 큐잉되어 들어가야해 순차적으로") ══
     부품 = nm-job.css `.job`(진행 행) 그대로 = 이미지 스튜디오 잡 행과 **같은 부품**(새 클래스·값 창작 0).
     읽는 곳 = 각 탭이 script 태그 `data-jobkey`로 선언한 슬롯 저장소 — 두 문법을 다 읽는다:
       ⓐ nm-jobs 슬롯(`nm_edit_pend`·`nm_song_pend` = {id,t0,lbl}) ⓑ 탭 자체 작업 배열(`sb_jobs`·`vd_jobs` = {id,status:'run'}).
     ⚠ 통지는 폴링이 아니라 **nm-jobs가 슬롯을 건드릴 때 부른다**(유휴 정숙 계약 = 가려진 동안 조용해야 한다). */
  function jobDur(s) { return s < 60 ? s + 's' : Math.floor(s / 60) + 'm ' + (s % 60) + 's'; }   // 경과 표기 = thumb `jobDur` 정본 바이트 그대로(60초부터 분·초 · 운영자 260728)
  function pendList(m) {
    var k = m.opt.jobkey; if (!k) return [];
    var a = [];
    try {
      if (window.nmJobs && /_pend$/.test(k)) a = nmJobs.list(k) || [];
      else { var raw = JSON.parse(localStorage.getItem(k) || '[]'); if (Array.isArray(raw)) a = raw.filter(function (x) { return x && x.status === 'run'; }); }
    } catch (e) { a = []; }
    /* 최신이 맨 위 · 옛날 게 아래(운영자 260811 "옛날거가 더 아래쪽에 배치되어야 함") —
       바로 아래 완료 타일 그리드도 최신 먼저(render의 ts 내림차순)라 한 칸 안에서 두 목록이 같은 방향으로 읽힌다.
       구판은 **발사 순서 오름차순**(먼저 건 게 위)이라 진행 중 줄만 혼자 반대로 흘렀다(260810 → 260811 개정). */
    return a.slice().sort(function (x, y) { return (+y.t0 || 0) - (+x.t0 || 0); });
  }
  /* 진행 중 행 탭 = **그 작업의 제작 화면으로 들어간다**(운영자 260811 "첨부2의 결과 표시되는 박스를 눌렀을때 나오는 화면으로 들어가야").
     화면 주인 전환은 탭마다 생김새가 달라 이 모듈이 못 정한다 → 문서가 `window.nmJobOpen(id, job)`을 정의하면 그때만 누를 수 있게 그린다
     (미정의 = 종전 그대로 정적 행 = 「갈 곳 없는 버튼 금지」 계약 · tileEl의 연필이 onEdit 유무로 갈리는 문법 동문). */
  function pendRows(m, host) {
    var a = pendList(m);
    var open = (typeof window.nmJobOpen === 'function') ? window.nmJobOpen : null;
    a.forEach(function (j) {
      var row = document.createElement('div'); row.className = 'job';
      var lab = document.createElement('span'); lab.className = 'jlab'; lab.textContent = toText(j.lbl || j.label || j.cap || '제작');
      var st = document.createElement('span'); st.className = 'jst';
      var sec = (+j.t0) ? Math.max(0, Math.round((Date.now() - (+j.t0)) / 1000)) : 0;
      st.innerHTML = (window.nmOrbHTML ? nmOrbHTML('solving', 14) : '')
        + '<span class="nm-shim">제작중' + (sec ? ' · <b class="jsec">' + jobDur(sec) + '</b>' : '') + '</span>';   // 문구·부품 = thumb 진행 행 정본(「제작중 · 21s」 · 빛 스윕 = 진행 중 전용)
      row.append(lab, st);
      if (open) {
        row.className = 'job job-go';   // 어포던스(손가락 커서·눌림)는 **실제로 갈 곳이 있을 때만** 붙는다
        row.setAttribute('role', 'button'); row.tabIndex = 0;
        row.title = '탭 = 이 작업의 제작 화면 열기';
        var go = function (ev) { if (ev) ev.preventDefault(); try { open(j.id, j); } catch (e) {} };
        row.addEventListener('click', go);
        row.addEventListener('keydown', function (ev) { if (ev.key === 'Enter' || ev.key === ' ') go(ev); });
      }
      host.appendChild(row);
    });
    return a.length;
  }
  /* 1초 틱은 **경과 숫자만** 갈아끼운다(운영자 260811 "이전 제작 계쏙 반짝거리는데 확인좀 해줘").
     ⚠ 구판은 매초 `m.sig=null; render(m)`으로 레일을 통째로 다시 그렸다 — 그 안엔 이전 제작 타일 재생성이 들어 있고
     영상 타일은 `<video>`라 매초 새로 만들어져 **제작 중인 동안 이전 제작이 계속 깜빡였다**(콘솔 에러 0 = 무증상).
     개수가 바뀌는 순간(발사·완료)엔 지문이 이미 달라지므로 render가 정상적으로 다시 그린다 = 표시 손실 0. */
  function pendTick(m) {
    var host = document.getElementById(m.id + 'ResJobs'); if (!host) return;
    var rows = host.querySelectorAll('.job:not(.done)');
    var a = pendList(m);
    if (rows.length !== a.length) { m.sig = null; render(m); return; }   // 구성이 갈렸다 = 다시 그린다(방어)
    for (var i = 0; i < rows.length; i++) {
      var sec = (+a[i].t0) ? Math.max(0, Math.round((Date.now() - (+a[i].t0)) / 1000)) : 0;
      var b = rows[i].querySelector('.jsec');
      if (!b) { if (sec > 0) { m.sig = null; render(m); return; } continue; }   // 0초라 아직 숫자 자리가 없다 = 첫 숫자가 붙는 순간만 다시 그린다
      var t = jobDur(sec);
      if (b.textContent !== t) b.textContent = t;
    }
  }
  var _tick = null;
  function tickSync() {   // 경과 1초 틱 = **진행 중이 있을 때만** 돈다(없으면 자기 손으로 끈다 = 유휴 rAF·타이머 0 계약)
    var live = mounts.some(function (m) { return pendList(m).length; });
    if (!live) { if (_tick) { clearInterval(_tick); _tick = null; } return; }
    if (_tick) return;
    _tick = setInterval(function () {
      if (document.hidden) return;   // 가려진 동안은 안 그린다(보는 사람이 없다)
      if (!mounts.some(function (m) { return pendList(m).length; })) { clearInterval(_tick); _tick = null; return; }
      mounts.forEach(pendTick);
    }, 1000);   // raw-ok: 경과 표기 주기(ms — 지속시간 토큰 아님) · thumb 잡 행 틱 동값
  }

  function jobRow(m, a) {   // 요약 줄 = thumb `renderJob` 완료 행(.job.done > .jlab + .jst + .jsave-row) 마크업 그대로
    var host = document.getElementById(m.id + 'ResJobs'); if (!host) return;
    host.innerHTML = '';
    var np = pendRows(m, host);   // 진행 중 = 완료 요약 줄 **위**(큐가 위에서 쌓여 내려온다)
    if (!a.length) return;
    var row = document.createElement('div'); row.className = 'job done';
    var lab = document.createElement('span'); lab.className = 'jlab'; lab.textContent = toText(a[0].cap) || '결과';
    var st = document.createElement('span'); st.className = 'jst';
    st.innerHTML = CK_SVG() + '<span>완료 · ' + a.length + '장 · ' + histTime(a[0].ts) + '</span>';
    row.append(lab, st);
    var sv = document.createElement('div'); sv.className = 'jsave-row';
    if (a[0].src && a[0].src.app && typeof m.opt.onEdit === 'function') {
      var ed = document.createElement('button'); ed.type = 'button'; ed.className = 'imgedit'; ed.title = '이 설정으로 수정'; ed.setAttribute('aria-label', '수정');
      if (window.EDIT_SVG) {   // 위 tileEl과 같은 계약(아이콘 없으면 미노출)
        ed.innerHTML = window.EDIT_SVG;
        ed.addEventListener('click', function (ev) { ev.preventDefault(); ev.stopPropagation(); m.opt.onEdit(a[0].src, a[0].url); });
        sv.appendChild(ed);
      }
    }
    var dl = document.createElement('button'); dl.type = 'button'; dl.className = 'sbtn cref-dlall dlbtn'; dl.title = '전체 다운로드'; dl.setAttribute('aria-label', '전체 다운로드');
    dl.innerHTML = (window.DLSEQ_IC || DL_SVG()) + '<span class="cref-dllbl">전체</span>';
    dl.addEventListener('click', function () { a.forEach(function (e, i) { setTimeout(function () { dlBlob(e.url, e.dlname || m.opt.dlname); }, i * 220); }); });   // 순차 저장 = 이미지 정본 간격(브라우저 다중저장 차단 회피)
    sv.appendChild(dl);
    row.appendChild(sv);
    host.appendChild(row);
  }

  function adoptCount(m) {   // 편입 목록의 항목 수 — 화면에 실제로 붙어 있는 것만 센다(문서가 지웠으면 자동 0)
    var n = 0;
    (m.adopt || []).forEach(function (el) { if (el && el.parentNode) n += el.children.length; });
    return n;
  }
  function applyFold(m) {   // 접힘 상태 단일 원천 = 헤더 aria-expanded(운영자 260806 평의회1 ④·평의회7 ⑧) — 구판은 render가 접힘을 무시하고 빈 상태 안내를 접힌 섹션에 되살렸고, 다시 펼쳐도 안내가 안 돌아왔다
    var rh = document.getElementById(m.id + 'ResH'); if (!rh) return;
    var open = rh.getAttribute('aria-expanded') !== 'false';
    [m.id + 'ResJobs', m.id + 'ResGrid'].forEach(function (i) { var e = document.getElementById(i); if (e) e.hidden = !open; });
    var re = document.getElementById(m.id + 'ResEmpty');
    if (re) re.hidden = !open || re.dataset.has === '1';
  }
  function render(m) {
    var all = merged(m.opt.scope).filter(function (e) { return e && e.url && !m.dead[keyOf(e.url)]; });   // merged = 로컬(12h 창 적용) + 서버(만료 없음) 병합(260818 · 구판 load 단독 = 그 브라우저만 보였다 · ⚠ prune 은 merged 안에서 로컬에만 = 서버분을 자르면 어제 것이 안 보인다)
    all.sort(function (x, y) { return (y.ts || 0) - (x.ts || 0); });
    var pend = pendList(m);
    var sig = all.length + ':' + ((all[0] || {}).url || '') + ':' + ((all[all.length - 1] || {}).url || '')
      + ':' + pend.length + ':' + pend.map(function (j) { return j.id; }).join(',');   // 무변경 지문 = 이미지 정본 `_histSig` 문법(길이 + 첫/끝 url) + **진행 중 슬롯**(새 발사·완료가 지문을 바꾼다) — 사진 완료 1건마다 영상 5탭이 **안 바뀐 데이터를 통째로 재빌드**하며 img 1,200개를 재생성하던 축 봉합(운영자 260806 평의회6 ① 실측 CPU 104ms·깜빡임 창 실재)
    if (m.sig === sig) { applyFold(m); return; }   // ⚠ 구판은 여기에 `&& !pend.length`가 붙어 **제작 중인 내내 지문 스킵이 통째로 꺼졌다**(= 매초 전면 재빌드 = 이전 제작 깜빡임 · 260811). 경과 숫자는 pendTick이 그 자리에서 갈아끼우고, 발사·완료는 지문(pend id·개수)이 바뀌어 정상 재빌드된다
    m.sig = sig;
    var res = all.filter(function (e) { return (e.ts || 0) >= T0; });          // 결과 = **이번 세션 완료분만**
    /* ⚠ (260810 제거) 「세션분 0이면 최신 1건 추종」 — 운영자 260810 "전에 제작한건 이전 제작에 남아있어야하고".
       구판은 창을 다시 열 때마다 지난 제작 1건을 결과로 끌어올렸고, 그 1건은 이전 제작 목록에서 **빠졌다**(이중노출 차단 필터 때문).
       그래서 어제 만든 게 오늘 「결과」에 있고 「이전 제작」은 그만큼 비는, 두 칸의 뜻이 뒤섞인 상태가 됐다. 이제 결과 = 이번 세션 것뿐. */
    var resK = {}; res.forEach(function (e) { resK[keyOf(e.url)] = 1; });
    var prev = all.filter(function (e) { return !resK[keyOf(e.url)]; });       // 이전 제작 = 결과에 뜬 것 제외(이중노출 차단 = 이미지 정본 동문)

    var rc = document.getElementById(m.id + 'ResCnt'); if (rc) rc.textContent = '(' + (res.length + pend.length) + ')';   // 결과 개수 = 완료 + 진행 중(큐가 결과 칸에서 자란다)
    var re = document.getElementById(m.id + 'ResEmpty');
    var rg = document.getElementById(m.id + 'ResGrid');
    if (rg) { rg.innerHTML = ''; res.forEach(function (e) { rg.appendChild(tileEl(m, e, m.id + 'ResGrid', m.id + 'ResCnt')); }); }
    jobRow(m, res);

    var ext = adoptCount(m);   // 문서가 편입시킨 목록(편집 탭 서버 인덱스 등) = 같은 「이전 제작」 칸의 일부 → 개수·빈 상태를 함께 센다
    var pc = document.getElementById(m.id + 'PrevCnt'); if (pc) pc.textContent = '(' + (prev.length + ext) + ')';
    var pe = document.getElementById(m.id + 'PrevEmpty'); if (pe) pe.hidden = !!(prev.length + ext);
    var pg = document.getElementById(m.id + 'PrevGrid');
    if (pg) { pg.innerHTML = ''; prev.forEach(function (e) { pg.appendChild(tileEl(m, e, m.id + 'PrevGrid', m.id + 'PrevCnt')); }); }
    if (re) re.dataset.has = (res.length || pend.length) ? '1' : '0';   // 「결과가 있는가」를 DOM에 박아 접힘 재적용이 데이터와 접힘을 함께 본다 · 진행 중도 「있는 것」(제작 중인데 "아직 제작한 게 없습니다"가 뜨면 거짓말)
    applyFold(m);
    tickSync();   // 경과 틱 = 진행 중이 있을 때만 켜지고 없으면 스스로 꺼진다
  }

  function bindFold(m) {   // 접이 = 이미지 정본 동문(hidden + closing 촤르륵 · reduced-motion 즉시)
    var pairs = [[m.id + 'PrevH', m.id + 'PrevBody']];
    pairs.forEach(function (p) {
      var h = document.getElementById(p[0]), b = document.getElementById(p[1]);
      if (!h || !b) return;
      var t = null;
      h.addEventListener('click', function () {
        var open = b.hidden;
        clearTimeout(t); b.classList.remove('closing');
        h.setAttribute('aria-expanded', String(open));
        var hist = document.getElementById(m.id + 'Hist'); if (hist) hist.classList.toggle('open', open);
        if (open) { b.hidden = false; }
        else if (matchMedia('(prefers-reduced-motion:reduce)').matches) { b.hidden = true; }
        else { b.classList.add('closing'); t = setTimeout(function () { b.hidden = true; b.classList.remove('closing'); }, 270); }
      });
    });
    var rh = document.getElementById(m.id + 'ResH');
    if (rh) {
      var els = [m.id + 'ResJobs', m.id + 'ResGrid'];
      rh.addEventListener('click', function () {
        rh.setAttribute('aria-expanded', String(rh.getAttribute('aria-expanded') !== 'true'));
        applyFold(m);   // 여닫기 = 단일 진입(구판은 접을 때 빈 상태를 숨기기만 하고 펼칠 때 복원을 안 했다 · 평의회7 ⑧-A)
      });
    }
  }

  var api = {
    mount: function (anchor, opt) {   // anchor = 이 요소 **뒤**에 레일을 붙인다(기존 산출 블록 무접촉 = 회귀 0)
      if (!anchor || !anchor.parentNode) return null;
      opt = opt || {};
      if (!Object.prototype.hasOwnProperty.call(KEYS, opt.scope)) return null;   // 미인식 스코프 = **마운트 거부**(운영자 260806 평의회2 ② — 구판 `|| 'cap'` 기본값은 오타 한 글자에 사진↔영상 격리가 깨지는 fail-open이었고, `data-scope="constructor"` 같은 프로토타입 키까지 통과해 쓰레기 localStorage 키를 만들었다)
      var scope = opt.scope;
      var m = { id: 'nmr' + (mounts.length ? mounts.length + 1 : ''), opt: { scope: scope, dlname: opt.dlname || 'out', onEdit: opt.onEdit, jobkey: opt.jobkey || '', srv: opt.srv || '', srvstat: opt.srvstat || '' }, dead: {}, sig: null };   // id 유일화 = 이중 마운트 시 둘째 레일이 **첫 레일 DOM을 조작**하던 축 봉합(운영자 260806 평의회1·2·6·7 공통 · 구 고정 'nmr'은 getElementById가 항상 첫 것을 물어 둘째는 영구 빈칸 + PrevH에 리스너 2개 = 이전 제작이 열리자마자 닫혔다)
      var wrap = document.createElement('div'); wrap.className = 'out nm-rail'; wrap.innerHTML = shellHTML(m.id);
      anchor.parentNode.insertBefore(wrap, anchor.nextSibling);
      m.el = wrap;
      mounts.push(m);
      bindFold(m);
      render(m);
      srvSync(m);   // 부팅 1회 = 이 기기에 없는 타 기기 제작분 즉시 발견(260818 · 로컬만 그려놓고 기다리지 않는다)
      return m;
    },
    add: function (e) {   // 완료 1건 적재 = 이 문서 + 형제 탭(같은 스코프) 즉시 반영
      if (!e || !e.url || !SAFE_URL.test(String(e.url))) return false;   // 스킴 화이트리스트 = 신뢰경계 1지점(운영자 260806 평의회7 ④ — localStorage는 타 탭·확장·수동 조작으로 오염 가능하고 이 값이 곧 href·img.src가 된다)
      /* ⚠ 저장은 **스코프 단위 1회**, 렌더는 전 마운트(운영자 260806 평의회1 ⑥·평의회2 ⑦) —
         구판은 마운트마다 각자 스토어에 push해 ⓐ 한 문서에 img·cap 마운트가 공존하면 같은 결과가 **양쪽에 실려 격리가 깨지고**
         ⓑ 같은 스코프 마운트 2개면 중복차단 `return`이 둘째의 render까지 건너뛰어 그 레일만 stale이었다. */
      var scopes = {}, ok = false;
      mounts.forEach(function (m) { scopes[m.opt.scope] = m; });
      Object.keys(scopes).forEach(function (sc) {
        var a = prune(load(sc));
        var k = keyOf(e.url);
        if (a.some(function (x) { return keyOf(x.url) === k; })) { ok = true; return; }   // 중복 적재 차단
        a.push({ url: e.url, poster: e.poster || '', dlname: e.dlname || scopes[sc].opt.dlname, cap: e.cap || '', varStr: e.varStr || '', ts: e.ts || Date.now(), src: e.src || null });
        while (a.length > HMAX) a.shift();
        ok = save(sc, a) || ok;   // save 실패(쿼터·프라이빗 모드)를 삼키지 않고 호출자에게 알린다(평의회1 ⑤)
      });
      mounts.forEach(function (m) { m.sig = null; render(m); });   // sig 무효화 후 렌더 = 방금 적재분 반영 보장
      return ok;
    },
    /* 문서 고유 「이전 제작」 목록을 이 칸 안으로 편입(운영자 260811 "작업 내역은 > 이전 제작이랑 같은 의미야. 그렇게 조치해줘야하고") —
       ⚠ 칸이 둘이면 같은 뜻을 두 번 말하고, 데이터 원천이 달라 하나는 늘 비어 보인다(실측 = 「이전 제작 (0)」 바로 아래 「작업 내역 (N)」).
       셸(머리·개수·접이)은 이 레일이 전담하고 문서는 자기 목록 요소만 넘긴다 = 머리 2개가 생길 여지 0. */
    adopt: function (el) {
      if (!el) return false;
      var m = mounts[0]; if (!m) return false;
      var body = document.getElementById(m.id + 'PrevBody'); if (!body) return false;
      if (el.parentNode !== body) body.appendChild(el);
      m.adopt = m.adopt || [];
      if (m.adopt.indexOf(el) < 0) m.adopt.push(el);
      m.sig = null; render(m);
      return true;
    },
    /* 이미 얹은 항목의 값 칩만 갈아끼운다(운영자 260811 "비율, 해상도, 영상 길이가 각각 값만 나오게") —
       그 값은 영상 메타가 와야 완성되는데, 적재는 그걸 기다리면 안 된다(기다리다 유실된 게 260810 사고). 그래서 **먼저 얹고 나중에 채운다**. */
    meta: function (url, varStr) {
      if (!url) return false;
      var k = keyOf(url), hit = false;
      var scopes = {};
      mounts.forEach(function (m) { scopes[m.opt.scope] = 1; });
      Object.keys(scopes).forEach(function (sc) {
        var a = load(sc), ch = false;
        a.forEach(function (e) { if (e && keyOf(e.url) === k && e.varStr !== varStr) { e.varStr = varStr || ''; ch = true; } });
        if (ch) { save(sc, a); hit = true; }
      });
      if (hit) mounts.forEach(function (m) { m.sig = null; render(m); });
      return hit;
    },
    /* 이 문서 스코프의 완료 이력 — 편입 목록이 **같은 작업을 두 번 그리지 않도록** 대조하는 용도.
       문서가 저장 키를 자기 손으로 읽으면 그 키가 갈린다(이 레포가 반복해 겪은 사본 드리프트) → 읽기 창구도 여기 하나. */
    items: function () { var m = mounts[0]; return m ? prune(load(m.opt.scope)) : []; },
    refresh: function () { mounts.forEach(render); }
  };
  window.nmRail = api;

  /* 자동 마운트 = **상속을 진짜 1줄로**(운영자 260806 "항상 저렇게 유지되어야하고") ──
     구판은 각 문서가 마운트 1줄을 따로 들었는데, 그 한 줄이 문서마다 다른 자리에 놓이며 **콘티·큐영상 2탭이 조용히 안 붙었다**(실측 260806:
     `nmRail` 로드·`#out` 실존인데 `.nm-rail` 0 = 스니펫 미실행 · 에러 0 = 무증상). 사본이 있으면 갈라진다는 오늘의 결론과 같은 축이라 진입점을 여기로 회수한다.
     앵커 = 문서가 이미 가진 산출 컨테이너를 순서대로 탐색(그 블록 **뒤**에 붙어 무접촉) · 하나도 없으면 본문 말미 = 어느 문서든 반드시 선다.
     스코프·파일명은 `<script src="nm-rail.js" data-scope="cap" data-dlname="video.mp4">`로 문서가 선언(속성 없으면 cap 기본). */
  function autoMount() {
    if (document.querySelector('.nm-rail')) return;   // 이미 수동 마운트한 문서 = 무동작(idempotent)
    var tag = document.querySelector('script[src$="nm-rail.js"]');
    var scope = (tag && tag.getAttribute('data-scope')) || 'cap';
    var dln = (tag && tag.getAttribute('data-dlname')) || 'out';
    var want = tag && tag.getAttribute('data-anchor');   // 문서가 자기 앵커를 지목할 수 있다(자동 탐색이 못 고르는 골격 = vd처럼 `#jobs`가 팝업 안에 있는 문서)
    var jkey = (tag && tag.getAttribute('data-jobkey')) || '';   // 진행 중 슬롯 저장소(운영자 260810 "제작 중인거는 그위 결과에 큐잉") — 선언 없으면 진행 중 행 0 = 종전 동작
    var vis = function (e) { return !!(e && (e.offsetParent || e.getClientRects().length)); };   // 숨은 조상 안 앵커 = 레일도 같이 사라진다(실측 260806 큐영상: DOM엔 섰는데 rect 0 = 무증상 실종) → 가시성까지 판정
    var anchor = null;
    if (want) { var w = document.querySelector(want); if (vis(w)) anchor = w; }
    if (!anchor) ['out', 'jobs'].some(function (id) { var e = document.getElementById(id); if (vis(e)) { anchor = e; return true; } return false; });
    if (!anchor) ['.out', '.jobs'].some(function (q) { var e = document.querySelector(q); if (vis(e)) { anchor = e; return true; } return false; });
    if (!anchor) {   // 산출 컨테이너가 없는 문서 = 본문 말미에 자기 자리를 만든다(빈 상태 레일이 서고, add()가 들어오면 그대로 채워진다)
      var wrapEl = document.querySelector('.wrap') || document.body;
      anchor = document.createElement('div'); anchor.className = 'nm-rail-anchor'; wrapEl.appendChild(anchor);
    }
    // 기기·브라우저 간 공유 선언(260818) = `data-srv`(최근 목록) · `data-srvstat`(미보유 id 개별 조회 접두).
    //   미선언 탭은 종전 로컬 단독 동작 그대로 = 이식이 나머지 탭을 건드리지 않는다(회귀 0).
    api.mount(anchor, { scope: scope, dlname: dln, jobkey: jkey,
      srv: (tag && tag.getAttribute('data-srv')) || '', srvstat: (tag && tag.getAttribute('data-srvstat')) || '' });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', autoMount);
  else autoMount();

  /* 형제 탭 동기 = 같은 스코프 키를 쓰는 다른 탭의 적재를 즉시 수신(이미지 정본 storage 수신 동문) + 복귀 3축.
     ⚠ 영상 5탭은 각자 iframe 문서라 같은 키를 공유하면 이 리스너만으로 전부 수렴한다(폴링 불요 = 부하 0). */
  /* 수렴 3축 = **내 스코프만** + 코얼레싱(운영자 260806 평의회6 ①② 실측 봉합) —
     구판은 ⓐ 사진 키 변경에도 반응해 영상 5탭이 헛렌더하고 ⓑ 탭 복귀 1회에 visibilitychange+focus가 연달아 터져 문서당 2회 재빌드였다(합 10회·img 2,400개·CPU 215ms). */
  var _kickT = null;
  function kick() { clearTimeout(_kickT); _kickT = setTimeout(function () { api.refresh(); mounts.forEach(srvSync); }, 60); }   // raw-ok: 병합 간격(ms — 지속시간 토큰 아님) · rAF 1틱 등가로 vis+focus 동시 발화를 1회로 · srvSync 동승(260818) = 복귀 시 타 기기 제작분 재발견(srvBusy 가드로 중복 요청 0)
  window.addEventListener('storage', function (ev) {
    if (!ev || !ev.key) return;
    var mine = mounts.some(function (m) { return KEYS[m.opt.scope] === ev.key; });   // 남의 스코프 = 무동작(격리 계약을 성능 축에서도 지킨다)
    if (mine) kick();
  });
  document.addEventListener('visibilitychange', function () { if (!document.hidden) kick(); });
  window.addEventListener('focus', kick);
})();
