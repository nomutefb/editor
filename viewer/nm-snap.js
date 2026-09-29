/* ═══ nm-snap.js — Snap Rail 하네스 단일정본 ═══════════════════════════════════════════════
   운영자 260929 «선택 요소를 snap rail 로 통일»(유튜브 탭) → «편집탭 통일» — 유튜브(ys)·편집(edit) 탭 공용.
   동작 = kinetics «Snap Rail»: 트랙 안 같은 폭 칸 + 선택 알약이 .45s 스프링으로 선택 칸까지 미끄러진다(transform 만).
   원본 = 각 탭의 버튼 그대로(클릭 = 그 탭의 기존 위임 핸들러가 받는다 · 선택 상태 = 버튼의 .on).
   포커스 링 = 공용 :focus-visible(바깥 2px 강조색 · nm-shared.css) — 레일 전용 링을 두지 않는다(안쪽 링은 강조색 알약 위라 안 보인다).
     · 표시 = <… data-nmsnap="키"> 컨테이너(자식 button = 칸) · 나중에 그려진 레일도 자동(MutationObserver)
     · 선택 원천 = 버튼의 .on · 칸 수 = --n · 선택 칸 = --i(선택 없음 = .none · 알약 숨김) · 라디오 문법(role·aria-checked·roving tabindex · ←→↑↓)
     · 다시 그려도 이어진다 = 같은 키의 레일이 새로 붙으면 **지난 칸에서 새 칸으로** 알약이 미끄러진다(편집 탭은 칩을 누를 때마다 카드를 다시 그린다)
   모양 = nm-shared.css「.nm-snap」 · 칸 폭·행 배치(라벨 열·최대 폭)는 표면 몫 */
(function () {
  if (window.nmSnap) return;
  const last = new Map();   // 키 → 마지막 선택 칸(다시 그린 레일의 알약 출발점)
  const btns = el => [...el.children].filter(b => b.tagName === 'BUTTON');
  const isOn = b => b.classList.contains('on');   // 선택 원천 = 표면의 .on 한 가지(aria-checked·aria-pressed = 하네스가 쓰고 지우는 결과 — 읽으면 옛 칸이 먼저 잡힌다)

  function paint(el) {
    if (!el || !el._nms) return;
    const bs = btns(el), i = bs.findIndex(isOn);
    el._nmsBusy = true;   // 아래 속성 쓰기가 관찰자를 다시 부르지 않게
    bs.forEach((b, n) => {
      const on = n === i;
      b.setAttribute('role', 'radio');
      b.setAttribute('aria-checked', String(on));
      b.removeAttribute('aria-pressed');   // 라디오 = aria-checked 한 벌(토글 표기와 겹치면 스크린리더가 두 번 읽는다)
      b.tabIndex = on || (i < 0 && n === 0) ? 0 : -1;
    });
    el.style.setProperty('--n', String(Math.max(1, bs.length)));
    el.classList.toggle('none', i < 0);
    if (i >= 0) el.style.setProperty('--i', String(i));
    const k = el.dataset.nmsnap;
    if (k) last.set(k, i);
    el._nmsBusy = false;
  }

  function mount(el) {
    if (!el || el._nms || !el.parentNode) return;
    el._nms = true;
    el.classList.add('nm-snap');
    el.setAttribute('role', 'radiogroup');
    const k = el.dataset.nmsnap, bs = btns(el), i = bs.findIndex(isOn), was = k && last.has(k) ? last.get(k) : undefined;
    if (was !== undefined && was >= 0 && i >= 0 && was !== i) {   // 다시 그린 레일 = 지난 칸에서 출발 → 새 칸으로 스프링
      el.style.setProperty('--n', String(Math.max(1, bs.length)));
      el.style.setProperty('--i', String(was));
      void el.offsetWidth;   // 출발점 확정(스타일 반영) 뒤 목적지를 준다 = 전환이 돈다
    }
    paint(el);
    new MutationObserver(() => { if (!el._nmsBusy) paint(el); })   // 표면이 .on 만 바꿔도(다시 그리지 않는 탭) 알약이 따라간다
      .observe(el, { subtree: true, attributes: true, attributeFilter: ['class', 'aria-pressed'], childList: true });
  }

  document.addEventListener('keydown', e => {   // ←→↑↓ = 다음 칸 선택(클릭을 흘려 표면 핸들러가 그대로 받는다) · 비활성 칸은 건너뛴다
    const b = e.target && e.target.closest && e.target.closest('[data-nmsnap] > button'); if (!b) return;
    const d = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[e.key]; if (!d) return;
    const bs = btns(b.parentElement).filter(x => !x.disabled); if (bs.length < 2) return;
    const nb = bs[(bs.indexOf(b) + d + bs.length) % bs.length];
    const k = b.parentElement.dataset.nmsnap, v = [...nb.parentElement.children].indexOf(nb);
    e.preventDefault(); nb.click();
    if (nb.isConnected) { nb.focus(); return; }   // 다시 그리지 않는 표면 = 바로 포커스(연타해도 다음 키가 새 칸 기준)
    const r = k ? document.querySelector('[data-nmsnap="' + CSS.escape(k) + '"]') : null;   // 클릭이 레일을 다시 그렸다 = 새 레일의 같은 칸
    const t = r && r.children[v];
    if (t && t.tagName === 'BUTTON') t.focus(); else requestAnimationFrame(() => { const r2 = k && document.querySelector('[data-nmsnap="' + CSS.escape(k) + '"]'); const t2 = r2 && r2.children[v]; if (t2) t2.focus(); });
  });

  function scan(root) {
    const r = root && root.querySelectorAll ? root : document;
    if (r.matches && r.matches('[data-nmsnap]')) mount(r);
    r.querySelectorAll('[data-nmsnap]').forEach(mount);
  }

  window.nmSnap = { mount, scan, paint };
  const go = () => {
    scan(document);
    new MutationObserver(ms => ms.forEach(m => m.addedNodes.forEach(n => { if (n.nodeType === 1) scan(n); })))
      .observe(document.documentElement, { childList: true, subtree: true });
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', go); else go();
})();
