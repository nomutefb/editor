/* ═══ nm-alpha.js — 스택 알파 재생기 단일정본 ═══════════════════════════════════════════════
   운영자 260929 «윈도우랑 아이폰 크로마키를 한번에 볼 수 있는 방법» → «B 진짜 투명 재생기».
   왜 = 알파 webm(VP9)은 아이폰 사파리가 알파를 못 읽어 투명이 안 된다(빠진 배경이 그대로 남거나 아예 재생이 안 됨 · 아이폰 실기 미확인 · 윈도우 크롬만 투명).
   원리 = 러너가 만든 스택 H.264(위 절반 = 색 · 아래 절반 = 알파를 밝기로 · .github/scripts/edit_track.py make_stacked)를
          숨긴 <video>로 재생하고 WebGL이 매 프레임 두 절반을 합쳐 투명 캔버스에 그린다 = 모든 브라우저 공통(H.264는 어디서나 읽힌다).
   ⚠ 같은 출처 필수 — 다른 출처 영상을 WebGL에 올리면 보안 오염으로 읽기가 막힌다(R2 공개 도메인은 CORS 헤더가 없다).
     그래서 주소는 /ly_out/… (functions/_r2live.js = 같은 출처 R2 서빙 · 아이폰용 구간 요청 206 지원)로 받는다.
   모양 = 숏폼 모니터 정본(vd.html `.mon .monplay`·`.monseek`) 계승 — 탭 = 재생/일시정지 · 가운데 ▶ · 바닥 진행선 · 값 = nm-shared.css「.nm-alpha」.
   실패(WebGL 없음·영상 못 읽음·보안 오염·문맥 유실) = 원래 <video>(webm) 그대로 = 종전 화면(악화 0).
   API = nmAlpha.mount(video, src, {w, h}) — video = 이미 그려진 결과 <video>(폴백 겸 메타 원천 · 제자리 유지 · 숨김만)
                                             src = 같은 출처 스택 mp4 · w·h = 색 절반 치수(있으면 첫 프레임 전에도 틀 비율이 맞다)
         nmAlpha.unmount(video) — 재생기 걷고 원래 video 복원(다음 제작·대기 진입). 원래 video 에 hidden 이 서면 자동으로 걷힌다. */
(function () {
  if (window.nmAlpha) return;
  const VS = 'attribute vec2 p;varying vec2 t;void main(){t=vec2((p.x+1.)*.5,(1.-p.y)*.5);gl_Position=vec4(p,0.,1.);}';
  // 색 = 위 절반 · 알파 = 아래 절반 밝기(G) · h = 반 텍셀(경계 번짐 차단) · 알파 양끝 2% = 압축 잡음 정리(바닥 잔상·몸 안 얼룩)
  // 정밀도 = 가능하면 highp(1920줄 텍스처에서 mediump 반정밀은 알파 행이 ±0.7텍셀 흔들릴 수 있다 · 평의회 계산)
  const FS = '#ifdef GL_FRAGMENT_PRECISION_HIGH\nprecision highp float;\n#else\nprecision mediump float;\n#endif\nuniform sampler2D s;uniform float h;varying vec2 t;'
    + 'void main(){vec3 c=texture2D(s,vec2(t.x,min(t.y*.5,.5-h))).rgb;float a=texture2D(s,vec2(t.x,max(.5+t.y*.5,.5+h))).g;'
    + 'a=clamp((a-.02)/.96,0.,1.);gl_FragColor=vec4(c*a,a);}';
  const PLAY = '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M8 5v14l11-7z"/></svg>';   // vd·ys·index .monplay 정본 글리프

  function gl0(cv) {
    let g = null;
    try { g = cv.getContext('webgl', { alpha: true, premultipliedAlpha: true, antialias: false }) || cv.getContext('experimental-webgl'); } catch (e) { g = null; }
    if (!g) return null;
    const sh = (type, src) => { const s = g.createShader(type); g.shaderSource(s, src); g.compileShader(s); return g.getShaderParameter(s, g.COMPILE_STATUS) ? s : null; };
    const vs = sh(g.VERTEX_SHADER, VS), fs = sh(g.FRAGMENT_SHADER, FS);
    if (!vs || !fs) return null;
    const pr = g.createProgram(); g.attachShader(pr, vs); g.attachShader(pr, fs); g.linkProgram(pr);
    if (!g.getProgramParameter(pr, g.LINK_STATUS)) return null;
    g.useProgram(pr);
    const b = g.createBuffer(); g.bindBuffer(g.ARRAY_BUFFER, b);
    g.bufferData(g.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), g.STATIC_DRAW);
    const loc = g.getAttribLocation(pr, 'p'); g.enableVertexAttribArray(loc); g.vertexAttribPointer(loc, 2, g.FLOAT, false, 0, 0);
    const tx = g.createTexture(); g.bindTexture(g.TEXTURE_2D, tx);
    [[g.TEXTURE_WRAP_S, g.CLAMP_TO_EDGE], [g.TEXTURE_WRAP_T, g.CLAMP_TO_EDGE], [g.TEXTURE_MIN_FILTER, g.LINEAR], [g.TEXTURE_MAG_FILTER, g.LINEAR]]
      .forEach(([k, v]) => g.texParameteri(g.TEXTURE_2D, k, v));
    g.pixelStorei(g.UNPACK_PREMULTIPLY_ALPHA_WEBGL, false);
    g.clearColor(0, 0, 0, 0);
    return { g, uh: g.getUniformLocation(pr, 'h') };
  }

  // 재생기 하나 = st 하나. 걷을 땐 **그 st 만** 죽인다 — 같은 video 에 다시 붙인 뒤 옛 재생기의 늦은 이벤트(load() 가 큐에 넣는
  //   timeupdate · 밀려난 WebGL 문맥의 contextlost)가 새 재생기를 걷던 사고 차단(평의회 260929 실측 = 작업 내역에서 자막+배경 빼기 작업을 연달아 열면 두 번째가 webm 으로 떨어졌다).
  function destroy(st) {
    if (!st || st.dead) return;
    st.dead = true;
    const orig = st.orig;
    if (orig._nma === st) { orig._nma = null; orig.style.display = st.disp; }
    try { st.mo.disconnect(); st.mo2.disconnect(); } catch (e) {}
    try { st.v.pause(); st.v.removeAttribute('src'); st.v.load(); } catch (e) {}   // 떼어낸 뒤에도 소리가 이어지는 것 차단
    try { const x = st.g.getExtension('WEBGL_lose_context'); if (x) x.loseContext(); } catch (e) {}   // 문맥 반납(브라우저 동시 문맥 상한 ≈16 · 쌓이면 가장 오래된 것부터 강제 유실)
    if (st.box.parentNode) st.box.parentNode.removeChild(st.box);
  }

  function unmount(orig) { if (orig && orig._nma) destroy(orig._nma); }

  function mount(orig, src, o) {
    if (!orig || !src || !orig.parentNode) return false;
    if (orig._nma && orig._nma.src === src && orig._nma.box.isConnected) return true;   // 같은 결과 다시 표시 = 그대로(재생 위치 유지)
    unmount(orig);
    const cv = document.createElement('canvas');
    const ctx = gl0(cv);
    if (!ctx) return false;   // WebGL 없음 = 원래 video 그대로
    const { g, uh } = ctx;
    const w0 = (o && +o.w) | 0, h0 = (o && +o.h) | 0;
    if (w0 > 1 && h0 > 1) { cv.width = w0; cv.height = h0; }
    const box = document.createElement('div');
    box.className = 'nm-alpha';
    box.innerHTML = '<button type="button" class="monplay" aria-label="재생 — 탭=재생/일시정지">' + PLAY + '</button>'
      + '<div class="monseek" role="slider" tabindex="0" aria-label="진행 위치 — 탭·드래그=이동 · 스페이스=재생/일시정지" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0"><i></i></div>';
    box.insertBefore(cv, box.firstChild);
    const v = document.createElement('video');
    v.setAttribute('playsinline', ''); v.playsInline = true; v.preload = 'auto';
    v.setAttribute('aria-hidden', 'true'); v.tabIndex = -1;
    box.appendChild(v);
    const pb = box.querySelector('.monplay'), sk = box.querySelector('.monseek'), fill = sk.querySelector('i');
    const st = { src, orig, box, v, g, disp: orig.style.display, mo: null, mo2: null, dead: false, looping: false, priming: false };
    const alive = () => !st.dead && orig._nma === st;

    const fail = () => destroy(st);
    const draw = () => {
      if (!alive() || v.readyState < 2) return;
      if (!box.isConnected) { destroy(st); return; }   // 창이 통째로 갈아엎였다(다음 제작) = 소리까지 정리
      const vw = v.videoWidth | 0, vh = (v.videoHeight / 2) | 0;
      if (vw < 2 || vh < 2) return;
      if (cv.width !== vw || cv.height !== vh) { cv.width = vw; cv.height = vh; }
      try {
        g.viewport(0, 0, vw, vh);
        g.texImage2D(g.TEXTURE_2D, 0, g.RGB, g.RGB, g.UNSIGNED_BYTE, v);   // 보안 오염(다른 출처) = 여기서 던진다 → 폴백
        g.uniform1f(uh, 0.5 / v.videoHeight);
        g.clear(g.COLOR_BUFFER_BIT);
        g.drawArrays(g.TRIANGLE_STRIP, 0, 4);
      } catch (e) { fail(); }
    };
    const loop = () => {   // 루프는 한 줄기만(재생·멈춤 반복마다 줄기가 늘어 업로드가 배로 불던 것 차단 · 평의회 실측 22→100회/초)
      if (!alive() || v.paused || v.ended) { st.looping = false; draw(); return; }
      draw();
      if (v.requestVideoFrameCallback) v.requestVideoFrameCallback(loop); else requestAnimationFrame(loop);
    };
    cv.addEventListener('webglcontextlost', e => { e.preventDefault(); fail(); });
    v.addEventListener('error', fail);
    v.addEventListener('loadeddata', draw);
    v.addEventListener('seeked', () => { draw(); if (v.paused && v.requestVideoFrameCallback) v.requestVideoFrameCallback(() => draw()); });   // 멈춘 채 이동 = 새 프레임이 늦게 오는 엔진 대비 한 번 더
    v.addEventListener('play', () => { if (!alive()) return; pb.hidden = true; if (!st.looping) { st.looping = true; loop(); } });
    v.addEventListener('pause', () => { if (!alive()) return; pb.hidden = false; draw(); });
    v.addEventListener('ended', () => { if (alive()) pb.hidden = false; });
    v.addEventListener('timeupdate', () => {
      if (!alive()) return;
      if (!box.isConnected) { destroy(st); return; }   // 떼어진 채 재생 중(프레임 콜백은 화면 밖 영상엔 안 온다) = 소리 정리
      if (!v.duration) return;
      const p = v.currentTime / v.duration * 100;
      fill.style.width = p + '%'; sk.setAttribute('aria-valuenow', String(Math.round(p)));
    });
    const toggle = () => {
      if (!alive()) return;
      if (st.priming) { st.priming = false; v.muted = false; if (v.paused) { const p = v.play(); if (p && p.catch) p.catch(() => {}); } return; }   // 첫 장면 채우는 중 탭 = 그대로 소리 켜고 재생(탭이 멈춤으로 먹히던 것 차단)
      if (v.paused || v.ended) { v.muted = false; const p = v.play(); if (p && p.catch) p.catch(() => {}); } else v.pause();
    };
    cv.addEventListener('click', toggle);
    pb.addEventListener('click', toggle);   // 키보드(Enter·Space) = 버튼 click — 마우스는 pointer-events:none 이라 캔버스가 받는다
    const seek = p => { if (v.duration) { v.currentTime = Math.min(1, Math.max(0, p)) * v.duration; } };
    sk.onpointerdown = ev => {
      ev.stopPropagation();
      const at = e2 => { const r = sk.getBoundingClientRect(); seek((e2.clientX - r.left) / r.width); };
      at(ev);
      try { sk.setPointerCapture(ev.pointerId); } catch (e) {}
      sk.onpointermove = at; sk.onpointerup = () => { sk.onpointermove = null; sk.onpointerup = null; };
    };
    sk.onkeydown = ev => {
      if (ev.key === ' ' || ev.key === 'k') { ev.preventDefault(); toggle(); return; }   // 재생 중엔 ▶ 가 숨어 포커스를 못 받는다 = 진행선에서 재생/멈춤
      if (!v.duration) return;
      if (ev.key === 'ArrowRight') { ev.preventDefault(); seek(v.currentTime / v.duration + .05); }
      else if (ev.key === 'ArrowLeft') { ev.preventDefault(); seek(v.currentTime / v.duration - .05); }
    };
    // 원래 video 에 hidden 이 서면(대기 진입·스킵·에러 표시) 재생기도 같이 걷는다 = 표면 코드가 재생기를 몰라도 형제 상태가 갈리지 않는다
    st.mo = new MutationObserver(() => { if (alive() && orig.hidden) destroy(st); });
    st.mo.observe(orig, { attributes: true, attributeFilter: ['hidden'] });
    // 창을 통째로 갈아엎으면(다음 제작 대기·새 결과) 재생기도 떨어져 나간다 = 그 순간 소리까지 정리
    st.mo2 = new MutationObserver(() => { if (alive() && !box.isConnected) destroy(st); });
    st.mo2.observe(orig.parentNode, { childList: true });

    orig._nma = st;
    try { orig.pause(); } catch (e) {}
    orig.style.display = 'none';
    orig.parentNode.insertBefore(box, orig.nextSibling);   // 원래 video 바로 뒤 = querySelector('video') 는 여전히 원래 video(메타 칩·다운로드 배선 무접촉)
    v.src = src;
    // 첫 장면 채우기 = 소리 끈 한 박자 재생 후 멈춤(아이폰은 재생 전엔 프레임을 안 준다 · 막히면 ▶만 남는다 = 누르면 된다)
    v.muted = true;
    st.priming = true;
    const pr = v.play();
    if (pr && pr.then) pr.then(() => { if (alive() && st.priming) { st.priming = false; v.pause(); try { v.currentTime = 0; } catch (e) {} v.muted = false; } })
      .catch(() => { st.priming = false; v.muted = false; });
    else { st.priming = false; v.muted = false; }
    return true;
  }

  window.nmAlpha = { mount, unmount };
})();
