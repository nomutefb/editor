/* 픽셀 펫 부품 — 아틀라스 1장을 82프레임으로 쪼개 돌리고, 가끔 화면 구석에 들어와 서성이다 사라진다.
   정본 = viewer/index.html #petcrab 블록(운영자 260710 · 업로드 캐릭터 영상 → 아틀라스). 이 파일은 그 로직의 이식본이고
   등장·페이드·배회·프레임 스텝 산식·확률값은 전부 정본 값 사본이다(새 값 창작 0).

   정본에 없던 것 = 「자세 게이트」 1축(아래 sitFrames).
   근거 = 아틀라스 82칸 실측(apps/pet/frames.json · 측정기 = build_pet_demo.py · 몸통 = 붙어 있는 가장 큰 덩이):
     · 웅크려 앉은 자세 45칸(몸 높이 48~51px) = 0~13 · 23~28 · 38~43 · 53~58 · 69~81
     · 일어서서 목 뻗는 자세 37칸(몸 높이 70~80px) = 14~22 · 29~37 · 44~52 · 59~68
     · 즉 원본은 「앉았다 일어섰다」를 4번 반복한다 = 구간이 연속이 아니라서 범위 두 값으로는 표현이 안 된다(목록이 필요한 이유)
     · 발 접지 중심 = 전 칸 67px 근방(변동은 걸음 폭 ±15.5px뿐) = 아틀라스는 이미 접지 기준으로 정렬돼 있다
   정본은 이동/멈춤을 프레임과 무관하게 확률로만 정해서 「앉은 자세로 미끄러지는」 시간이 전체의 55%였다.
   그 자리를 자세로 잠근다 = 앉은 칸에선 x 고정, 선 칸에서만 전진·방향 전환.

   장식 전용 = pointer-events 없음(클릭 무간섭) · aria-hidden · reduced-motion 미출현(정본 계약 계승).
   상속 = <link rel="stylesheet" href="nm-pet.css"> + <script src="nm-pet.js"></script> 2줄 · 자동 시작 안 함(nmPet.start() 호출이 정문). */
(function () {
  'use strict';

  /* 아틀라스 지오메트리 = 단일출처(정본 PET 상수 값 그대로 · viewer/pet_crab.png 실측과 일치: 1320x1080 = 132x120 x 10x9) */
  var BASE = {
    atlas: 'pet_crab.png',
    tw: 132, th: 120, frames: 82, cols: 10, rows: 9,   // 타일 폭·높이·총 프레임·열·행
    fps: 30,            // 아트 = 원본 30fps 스텝(픽셀아트 보간 = 뭉개짐이라 금지 · 정본 주석)
    scale: 0.75,        // 화면 배율(정본 값)
    // 웅크려 앉은 칸 목록(실측 45칸) — 이 칸에선 제자리. 빈 배열로 두면 정본과 똑같이 프레임 무관하게 움직인다.
    sitFrames: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 23, 24, 25, 26, 27, 28,
                38, 39, 40, 41, 42, 43, 53, 54, 55, 56, 57, 58, 69, 70, 71, 72, 73, 74,
                75, 76, 77, 78, 79, 80, 81],
    bottom: 58,         // 바닥 = 하단 내비 위(정본 calc(58px + safe-area))
    side: 'left',       // 어느 쪽에서 서성이나(정본 = 좌하단 = 설정 픽토 반대편)
    span: 0.55,         // 배회 폭 = 화면의 이 비율까지만(정본 0.55 = 반대편 메뉴 침범 X)
    speedMin: 16, speedMax: 30,        // px/ms x1000 (정본 값)
    turnChance: 0.0025, pauseChance: 0.002,   // 프레임당 방향 전환·멈춤 확률(정본 값)
    pauseMin: 900, pauseMax: 2600,     // 멈춰 서성이는 시간(정본 값)
    host: null,         // 붙일 자리 = 없으면 화면 전체(정본 = document.body 고정) · 요소·선택자를 주면 그 상자 안에서만 서성인다
    stayMin: 14000, stayMax: 26000,    // 한 번 방문에 머무는 시간(정본 값)
    gapMin: 90000, gapMax: 240000,     // 다음 방문까지 = 1.5~4분(정본 값)
    firstMin: 12000, firstMax: 35000,  // 첫 등장 = 부팅 12~35초 뒤(정본 값)
    fadeMs: 750                        // 페이드아웃 뒤 정리(정본 값 · CSS transition .7s와 한 쌍)
  };

  var cfg = {};
  for (var k in BASE) cfg[k] = BASE[k];

  var el = null, visiting = false, timer = 0, running = false, forced = false;
  var rand = function (a, b) { return a + Math.random() * (b - a); };
  var reduced = function () {
    try { return matchMedia('(prefers-reduced-motion: reduce)').matches; } catch (e) { return false; }
  };

  function W() { return cfg.tw * cfg.scale; }
  function H() { return cfg.th * cfg.scale; }

  /* 붙일 자리 = 옵션이 없으면 화면 전체(정본 동작) */
  function hostEl() {
    var h = cfg.host;
    if (typeof h === 'string') h = document.querySelector(h);
    return h || document.body;
  }

  /* 배회 가능 폭 = 화면 전체면 창 폭, 상자 안이면 그 상자 폭 */
  function stageW() {
    var h = hostEl();
    return h === document.body ? innerWidth : h.clientWidth;
  }

  function ensure() {
    var host = hostEl();
    if (el && el.parentNode === host) return el;
    if (!el) {
      el = document.createElement('div');
      el.setAttribute('aria-hidden', 'true');
    }
    el.className = 'nm-pet' + (host === document.body ? '' : ' inhost');
    host.appendChild(el);
    geom();
    return el;
  }

  /* 지오메트리 반영 = 타일 1장이 요소를 꽉 채우고 배경이 아틀라스 전체로 확대되게(정본 backgroundSize 산식 그대로) */
  function geom() {
    if (!el) return;
    el.style.width = W() + 'px';
    el.style.height = H() + 'px';
    el.style.backgroundImage = 'url(' + cfg.atlas + ')';
    el.style.backgroundSize = (cfg.cols * W()) + 'px ' + (cfg.rows * H()) + 'px';
    el.style.setProperty('--nmpet-bottom', cfg.bottom + 'px');
  }

  function frameAt(elapsed) {
    return Math.floor(elapsed / (1000 / cfg.fps)) % cfg.frames;   // 정본 산식
  }

  function paint(p, f) {
    p.style.backgroundPosition = (-(f % cfg.cols) * W()) + 'px ' + (-Math.floor(f / cfg.cols) * H()) + 'px';
  }

  function visit() {
    if (visiting || (document.hidden && !forced)) { schedule(); return; }
    visiting = true;
    var p = ensure(), t0 = performance.now(), stay = rand(cfg.stayMin, cfg.stayMax);
    var maxX = function () { return Math.max(60, stageW() * cfg.span - W()); };
    var x = rand(8, Math.max(40, stageW() * cfg.span * 0.55));
    var dir = Math.random() < 0.5 ? -1 : 1;
    var speed = rand(cfg.speedMin, cfg.speedMax) / 1000;
    var pauseUntil = 0, last = t0;

    p.style.opacity = '0';
    p.classList.add('on');
    requestAnimationFrame(function () { p.style.opacity = '1'; });   // 페이드인(CSS transition)

    var step = function (now) {
      var dt = Math.min(64, now - last); last = now;
      var f = frameAt(now - t0);
      paint(p, f);

      /* 자세 게이트 = 선 칸에서만 전진·방향 전환(앉은 칸은 제자리) */
      if (api.walking(f) && now >= pauseUntil) {
        x += dir * speed * dt;
        var mx = maxX();
        if (x < 4) { x = 4; dir = 1; }
        else if (x > mx) { x = mx; dir = -1; }
        else if (Math.random() < cfg.turnChance) dir = -dir;
        if (Math.random() < cfg.pauseChance) pauseUntil = now + rand(cfg.pauseMin, cfg.pauseMax);
      }

      /* 오른쪽에서 서성이는 배치 = 좌표를 화면 오른쪽 기준으로 뒤집어 읽는다(값 창작 0 · 같은 x를 반대편에서 셈) */
      var px = cfg.side === 'right' ? (stageW() - W() - x) : x;
      p.style.transform = 'translateX(' + px + 'px) scaleX(' + dir + ')';

      if (running && now - t0 < stay && (!document.hidden || forced)) { requestAnimationFrame(step); return; }
      p.style.opacity = '0';   // 페이드아웃 → 다음 방문 예약
      setTimeout(function () {
        p.classList.remove('on'); visiting = false;
        if (running) schedule();
      }, cfg.fadeMs);
    };
    requestAnimationFrame(step);
  }

  function schedule() {
    clearTimeout(timer);
    if (!running) return;
    timer = setTimeout(visit, rand(cfg.gapMin, cfg.gapMax));   // 종종 = 1.5~4분 간격 랜덤(정본)
  }

  var api = {
    /* 상시 가동 시작 = 부팅 12~35초 뒤 첫 등장, 그 뒤 1.5~4분마다(정본 스케줄) */
    start: function (opt) {
      if (reduced()) return api;              // 장식 = 접근성 우선 미출현(정본 계약)
      api.set(opt);
      if (running) return api;
      running = true;
      clearTimeout(timer);
      timer = setTimeout(visit, rand(cfg.firstMin, cfg.firstMax));
      return api;
    },
    /* 정지 = 예약 취소(도는 방문은 자기 머무는 시간까지 마치고 사라진다) */
    stop: function () { running = false; clearTimeout(timer); return api; },
    /* 지금 한 번 등장(데모·확인용 · 접근성 설정도 무시하지 않는다) */
    show: function (opt) {
      if (reduced()) return api;
      api.set(opt);
      running = true; forced = true;
      clearTimeout(timer);
      if (!visiting) visit();
      return api;
    },
    /* 즉시 퇴장 */
    hide: function () {
      running = false; clearTimeout(timer);
      if (el) { el.style.opacity = '0'; }
      return api;
    },
    /* 설정 갱신(도는 중에도 크기·바닥·속도 즉시 반영) */
    set: function (opt) {
      if (opt) for (var k in opt) if (k in cfg) cfg[k] = opt[k];
      geom();
      return api;
    },
    /* 값 읽기 = 현재 설정 사본(원본 잠금) */
    get: function () { var o = {}; for (var k in cfg) o[k] = cfg[k]; return o; },
    /* 기본값 = 정본 값 사본(플레이그라운드 「현행」 기준) */
    base: function () { var o = {}; for (var k in BASE) o[k] = BASE[k]; return o; },
    /* 프레임 1장만 그리기(프레임 판독표·정지 미리보기용) */
    frameStyle: function (f, scale) {
      var s = scale || cfg.scale, w = cfg.tw * s, h = cfg.th * s;
      return 'width:' + w + 'px;height:' + h + 'px;background-image:url(' + cfg.atlas + ');'
        + 'background-size:' + (cfg.cols * w) + 'px ' + (cfg.rows * h) + 'px;'
        + 'background-position:' + (-(f % cfg.cols) * w) + 'px ' + (-Math.floor(f / cfg.cols) * h) + 'px;'
        + 'background-repeat:no-repeat;image-rendering:pixelated;';
    },
    /* 자세 판정 = 일어선 칸인가(실측 목록의 여집합) */
    walking: function (f) {
      var s = cfg.sitFrames;
      if (!s || !s.length) return true;          // 목록을 비우면 정본 동작(프레임 무관)
      return s.indexOf(f) < 0;
    }
  };

  window.nmPet = api;
})();
