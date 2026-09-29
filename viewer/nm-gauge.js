/* ═══ nm-gauge.js — 러버밴드 게이지 하네스 단일정본 ═══════════════════════════════════════
   운영자 260929 «게이지 바 조정 = 영상 제작(자막 입히는 편집 메뉴)에도 · 하네스 통일» — 유튜브(ys)·편집(edit) 탭 공용.
   동작 = kinetics «Rubber-band Slider»: 끝을 넘겨 끌면 넘친 거리 ×.32 만 따라가고, 놓으면 .5s 스프링으로 제자리.
   원본 = 네이티브 <input type="range"> 그대로(값·키보드·접근성·기존 input/change 리스너 무수정) → 위에 트랙·채움·손잡이를 덧입힌다.
     · 표시 = <input type="range" data-nmg> 만 장착(나중에 그려진 행도 자동 · MutationObserver)
     · 코드가 값을 바꿔도(el.value = v) 그림이 따라간다(그 칸의 value 접근자만 감싼다 · 원형 무접촉)
     · data-def = 두 번 누르기 기본값(없으면 두 번 누르기 무동작)
   이동 = transform 만(채움 scaleX · 손잡이 translateX = 레이아웃 전환 0) · 모양 = nm-shared.css「.nm-rbs」 */
(function () {
  if (window.nmGauge) return;
  const K = 0.32;   // 넘친 거리 추종 비율 = kinetics 원본 동값
  const D = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value');
  const num = (v, d) => { const n = parseFloat(v); return Number.isFinite(n) ? n : d; };
  const lim = el => { const mn = num(el.min, 0), mx = num(el.max, 100); return [mn, mx > mn ? mx : mn + 1, num(el.step, 1) || 1]; };
  const frac = el => { const [mn, mx] = lim(el); return Math.min(1, Math.max(0, (num(D.get.call(el), mn) - mn) / (mx - mn))); };
  const paint = (el, p) => { if (el._nmg) el._nmg.style.setProperty('--p', String(p === undefined ? frac(el) : p)); };
  const fire = (el, t) => el.dispatchEvent(new Event(t, { bubbles: true }));
  const snap = w => { w.classList.add('snap'); clearTimeout(w._sn); w._sn = setTimeout(() => w.classList.remove('snap'), 520); };

  function mount(el) {
    if (!el || el._nmg || el.type !== 'range' || !el.parentNode) return;
    const w = document.createElement('span');
    w.className = 'nm-rbs';
    w.innerHTML = '<span class="nm-rbs-track" aria-hidden="true"><span class="nm-rbs-fill"></span></span><span class="nm-rbs-knob" aria-hidden="true"></span>';
    el.parentNode.insertBefore(w, el);
    w.insertBefore(el, w.firstChild);
    el.classList.add('nm-rbs-in');
    el._nmg = w;
    Object.defineProperty(el, 'value', { configurable: true, get() { return D.get.call(this); }, set(v) { D.set.call(this, v); paint(this); } });
    let on = false, wait = null, v0 = null;   // v0 = 누르기 전 값(바뀐 때만 change · 네이티브 동형)   // wait = 터치 시작 좌표(가로로 움직여야 끌기 · 세로 = 브라우저 스크롤 · 그냥 떼면 탭 = 그 자리로)
    const at = x => {
      const r = w.getBoundingClientRect(), raw = (x - r.left) / (r.width || 1), c = Math.min(1, Math.max(0, raw));
      const [mn, mx, st] = lim(el), old = D.get.call(el);
      const v = Math.min(mx, Math.max(mn, mn + Math.round(c * (mx - mn) / st) * st));
      D.set.call(el, String(+v.toFixed(6)));
      w.style.setProperty('--p', String(c + (raw - c) * K));   // 트랙 밖 = 넘친 거리 ×.32 만 따라간다
      if (D.get.call(el) !== old) fire(el, 'input');
    };
    const start = e => {
      on = true; wait = null; w.dataset.ptr = '1';   // 포인터 조작 = 포커스 링 숨김(키보드로 옮기면 다시 보인다)
      try { w.setPointerCapture(e.pointerId); } catch (x) { /* 캡처 불가 = 창 밖 이탈만 못 따라간다 */ }
      try { el.focus({ preventScroll: true }); } catch (x) { /* 포커스 불가 무해 */ }
      w.classList.remove('snap'); w.classList.add('drag'); at(e.clientX);
    };
    w.addEventListener('pointerdown', e => {
      if (el.disabled || (e.pointerType === 'mouse' && e.button !== 0)) return;
      v0 = D.get.call(el);
      if (e.pointerType === 'mouse') { e.preventDefault(); start(e); } else wait = { x: e.clientX, y: e.clientY };
    });
    w.addEventListener('pointermove', e => {
      if (on) { at(e.clientX); return; }
      if (wait && Math.abs(e.clientX - wait.x) > 4 && Math.abs(e.clientX - wait.x) > Math.abs(e.clientY - wait.y)) start(e);   // 가로가 이겼다 = 끌기
    });
    const end = () => { if (!on) return; on = false; w.classList.remove('drag'); snap(w); paint(el); if (D.get.call(el) !== v0) fire(el, 'change'); };
    w.addEventListener('pointerup', e => {
      if (wait && !on) { start(e); }   // 움직임 없이 뗐다 = 탭 → 그 자리로(스프링)
      wait = null; end();
    });
    w.addEventListener('pointercancel', () => { wait = null; end(); });   // 브라우저가 세로 스크롤로 가져갔다 = 값 무변경
    el.addEventListener('input', () => { if (!on) paint(el); });          // 키보드·코드 발 input = 그림 동기
    el.addEventListener('keydown', e => {   // 키보드 = 포커스 링 복귀 · 한 칸 = 스프링으로 붙는다 · Shift+방향키 = 10칸(유튜브 탭 구 조작 승계)
      if (!/^(Arrow|Home|End|Page)/.test(e.key)) return;
      delete w.dataset.ptr; snap(w);
      if (e.shiftKey && /^Arrow/.test(e.key)) {
        const [mn, mx, st] = lim(el), d = /Right|Up/.test(e.key) ? 1 : -1;
        e.preventDefault();
        D.set.call(el, String(Math.min(mx, Math.max(mn, num(D.get.call(el), mn) + d * st * 10))));
        paint(el); fire(el, 'input'); fire(el, 'change');
      }
    });
    w.addEventListener('dblclick', () => {
      if (el.dataset.def === undefined || el.disabled) return;
      D.set.call(el, el.dataset.def); snap(w); paint(el); fire(el, 'input'); fire(el, 'change');
    });
    paint(el);
  }

  function scan(root) {
    const r = root && root.querySelectorAll ? root : document;
    if (r.matches && r.matches('input[type=range][data-nmg]')) mount(r);
    r.querySelectorAll('input[type=range][data-nmg]').forEach(mount);
  }

  window.nmGauge = { mount, scan, paint };
  const go = () => {
    scan(document);
    new MutationObserver(ms => ms.forEach(m => m.addedNodes.forEach(n => { if (n.nodeType === 1) scan(n); })))
      .observe(document.documentElement, { childList: true, subtree: true });
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', go); else go();
})();
