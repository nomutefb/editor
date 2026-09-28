#!/usr/bin/env python3
"""유튜브 숏폼(ys) 모션 그래픽 — 장면 내용에 맞는 도식(비교·흐름·숫자·막대·목록·순환·아이콘·인용)을 CSS 애니메이션으로 그리고
헤드리스 Chromium 에서 프레임 단위로 찍는다(운영자 260928 «관련된 그래픽 모션 · 무조건 타이포그래피는 아님»).

  normalize_mg(mg, sc)                → 형식 게이트를 통과한 도식 사양(dict) · 틀리면 아이콘 도식으로 강하
  mg_html(tokens, font_css, family, mg, w, h) → 그림 칸(w×h) 한 장짜리 HTML
  capture(page, html_path, outdir, dur) → outdir/f0000.png… (투명 배경) · 반환 = (프레임 수, 반복 시작 프레임, 반복 길이)

시간 계약: 등장 = 0~ENTER 초 안에 끝난다 · 그 뒤 = 주기 LOOP 초의 은은한 반복(주기는 LOOP 의 약수만) → 등장 + 한 주기만 찍고
ffmpeg loop 필터로 장면 길이만큼 늘린다(찍는 장수 = 장면 길이와 무관한 상한 · 이음매 없음).
프레임 구동 = Web Animations API(document.getAnimations() 정지 → currentTime 지정) = 벽시계와 무관한 결정론 렌더.
디자인 값은 창작하지 않는다 — :root 색 토큰 8개(palette_css · --c1~--c8)만 쓴다 · 다색 면 위주(운영자 260928 «네온 단색 금지») · 아이콘 = Lucide(ISC · apps/ys/mg_icons.json).
"""
import html
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ICONS = json.load(open(ROOT / 'apps' / 'ys' / 'mg_icons.json', encoding='utf-8'))['icons']
TYPES = ('compare', 'flow', 'number', 'bars', 'list', 'cycle', 'icon', 'quote')
PALETTE = [('c1', 'accent'), ('c2', 'accent-2'), ('c3', 'cat-intl'), ('c4', 'cat-pol'), ('c5', 'cat-tech'),
           ('c6', 'accent-6'), ('c7', 'cat-soc'), ('c8', 'bias-l2')]   # 무대 팔레트 = viewer :root 색 토큰 8개(운영자 260928 «네온 단색 금지 · 강조색 살릴 필요 없음»)
FPS = 30
ENTER = 2.4        # 등장 애니메이션 전부 이 안에 끝난다(마지막 지연 + 길이 ≤ 2.4s)
LOOP = 3.0         # 반복 주기(모든 반복 애니메이션 주기 = 3.0 · 1.5 · 1.0 · 0.75 중 하나)
LBL = 10           # 도식 라벨 최대 글자(한 줄) = prompts/ys-make.md 규격과 동값


def esc(s):
    return html.escape(str(s or ''))


def _lbl(v, cap=LBL):
    return re.sub(r'\s+', ' ', str(v or '')).strip()[:cap]


def _icon(v, fallback='sparkles'):
    v = str(v or '').strip().lower()
    return v if v in ICONS else fallback


def _num(v):
    try:
        f = float(str(v).replace(',', '').strip().rstrip('%'))
    except (TypeError, ValueError):
        return None
    return f if math.isfinite(f) else None


def palette_css(tokens):
    """--c1~--c8(토큰 참조) + --cN-rgb(토큰 hex → 삼중값) + --ink·--muted — 무대 전용 짧은 이름(값 창작 0)."""
    out = []
    for short, tok in PALETTE:
        m = re.search(r'--' + re.escape(tok) + r'\s*:\s*(#[0-9a-fA-F]{6})', tokens)
        rgb = ','.join(str(int(m.group(1)[k:k + 2], 16)) for k in (1, 3, 5)) if m else '238,247,240'
        out.append(f'--{short}:var(--{tok});--{short}-rgb:{rgb};')
    return ':root{' + ''.join(out) + '--ink:var(--fg);--muted:var(--mut)}'


def normalize_mg(mg, sc=None):
    """모델 산출 도식 사양 → 검증된 사양. 형식이 어긋나면 그 장면 핵심어로 「아이콘」 도식을 만든다(빈 칸 0 · 조용한 누락 0)."""
    sc = sc or {}
    fb_label = _lbl((sc.get('chips') or [''])[0] or sc.get('tag') or '')
    fallback = {'type': 'icon', 'icon': 'lightbulb', 'label': fb_label or '핵심', 'sub': ''}
    if not isinstance(mg, dict):
        return fallback
    t = str(mg.get('type') or '').strip().lower()
    if t not in TYPES:
        return fallback
    items = mg.get('items') if isinstance(mg.get('items'), list) else []
    if t == 'compare':
        a, b = mg.get('a') if isinstance(mg.get('a'), dict) else {}, mg.get('b') if isinstance(mg.get('b'), dict) else {}
        if not (_lbl(a.get('label')) and _lbl(b.get('label'))):
            return fallback
        win = mg.get('win') if mg.get('win') in ('a', 'b') else ''
        return {'type': t, 'a': {'label': _lbl(a['label']), 'icon': _icon(a.get('icon'))},
                'b': {'label': _lbl(b['label']), 'icon': _icon(b.get('icon'))}, 'mid': _lbl(mg.get('mid') or 'VS', 3), 'win': win}
    if t in ('flow', 'list'):
        its = [{'label': _lbl(x.get('label')), 'icon': _icon(x.get('icon'), 'check' if t == 'list' else 'sparkles')}
               for x in items[:4] if isinstance(x, dict) and _lbl(x.get('label'))]
        return {'type': t, 'items': its} if len(its) >= 2 else fallback
    if t == 'cycle':
        its = [_lbl(x.get('label') if isinstance(x, dict) else x) for x in items[:4]]
        its = [x for x in its if x]
        return {'type': t, 'items': its, 'icon': _icon(mg.get('icon'), 'refresh-cw')} if len(its) >= 3 else fallback
    if t == 'number':
        v = _num(mg.get('value'))
        if v is None:
            return fallback
        return {'type': t, 'value': v, 'unit': _lbl(mg.get('unit'), 4), 'label': _lbl(mg.get('label'), 16)}
    if t == 'bars':
        its = [{'label': _lbl(x.get('label'), 8), 'value': _num(x.get('value'))} for x in items[:4] if isinstance(x, dict)]
        its = [x for x in its if x['label'] and x['value'] is not None and x['value'] >= 0]
        return {'type': t, 'items': its, 'unit': _lbl(mg.get('unit'), 4)} if len(its) >= 2 and max(x['value'] for x in its) > 0 else fallback
    if t == 'icon':
        return {'type': t, 'icon': _icon(mg.get('icon'), 'lightbulb'), 'label': _lbl(mg.get('label'), 16) or fallback['label'],
                'sub': _lbl(mg.get('sub'), 24)}
    if t == 'quote':
        txt = re.sub(r'\s+', ' ', str(mg.get('text') or '')).strip()[:40]
        return {'type': t, 'text': txt, 'by': _lbl(mg.get('by'), 16)} if len(txt) >= 4 else fallback
    return fallback


def textless(mg):
    """모션 그래픽 모드의 대체 도식 = 「화면 글자 없음」 계약(운영자 260928) — 문장 글자(보조문·인용문)를 뺀다 · 짧은 라벨만 남긴다."""
    if mg.get('type') == 'quote':
        return {'type': 'icon', 'icon': 'quote', 'label': mg.get('by') or '', 'sub': ''}
    if mg.get('type') == 'icon':
        return {**mg, 'sub': ''}
    return mg


def svg(name, cls='ic', draw=0.0, dur=0.9, px=None, c=None):
    """Lucide 아이콘 → 선 그리기 애니메이션(pathLength=1 · stroke-dashoffset 1→0 · transform 무관) · px = 한 변 크기 · c = 팔레트 번호(1~8)."""
    els = ''.join(re.sub(r'/>$', f' pathLength="1" style="animation-delay:{draw:.2f}s;animation-duration:{dur:.2f}s"/>', e)
                  for e in ICONS[_icon(name)])
    st = (f'width:{px}px;height:{px}px;' if px else '') + (f'color:var(--c{c});' if c else '')
    size = f' style="{st}"' if st else ''
    return f'<svg class="{cls} draw" viewBox="0 0 24 24"{size} aria-hidden="true">{els}</svg>'


def _fs(text, avail, cap):
    """keep-all 이라 안 끊기는 가장 긴 덩어리(공백 사이) 기준 글자 크기 — 한글 1자 ≈ 1em(보수적) · 상한 cap."""
    run = max((len(t) for t in str(text).split()), default=1) or 1
    return int(min(cap, avail / run))


def _fmt(v):
    return str(int(v)) if float(v).is_integer() else (f'{v:.2f}'.rstrip('0').rstrip('.'))   # 전사 숫자 그대로(반올림 왜곡 0)


CSS = """
@property --n{syntax:'<integer>';inherits:false;initial-value:0}
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:%(w)dpx;height:%(h)dpx;background:transparent;overflow:hidden;font-family:%(family)s,'Noto Sans CJK KR',sans-serif;color:var(--fg);word-break:keep-all;-webkit-font-smoothing:antialiased}
.box{position:absolute;inset:0;overflow:hidden;
  background:radial-gradient(%(gw)dpx %(gh)dpx at 30%% 25%%,rgba(var(--c5-rgb),.20),transparent 60%%),radial-gradient(%(gw)dpx %(gh)dpx at 75%% 75%%,rgba(var(--c4-rgb),.16),transparent 60%%),var(--bg)}
.box::after{content:'';position:absolute;left:0;right:0;bottom:0;height:%(fade)dpx;background:linear-gradient(transparent,var(--bg));pointer-events:none}
.grid{position:absolute;inset:-46px;background-image:linear-gradient(rgba(255,255,255,.04) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.04) 1px,transparent 1px);
  background-size:46px 46px;animation:drift 3s linear infinite}
@keyframes drift{to{transform:translate(46px,46px)}}
.dot{position:absolute;width:14px;height:14px;border-radius:50%%;background:rgba(var(--c2-rgb),.45);animation:bob 3s ease-in-out infinite}
@keyframes bob{0%%,100%%{transform:translateY(0);opacity:.25}50%%{transform:translateY(-26px);opacity:.8}}
.stage{position:absolute;inset:0;display:flex;align-items:center;justify-content:center}
.draw *{fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:1 2;stroke-dashoffset:1;
  animation-name:drawk;animation-timing-function:cubic-bezier(.65,0,.35,1);animation-fill-mode:forwards}
@keyframes drawk{to{stroke-dashoffset:0}}
.pop{opacity:0;animation:pop .6s cubic-bezier(.34,1.56,.64,1) forwards}
@keyframes pop{0%%{opacity:0;transform:scale(.4)}100%%{opacity:1;transform:scale(1)}}
.rise{opacity:0;animation:rise .55s cubic-bezier(.16,1,.3,1) forwards}
@keyframes rise{from{opacity:0;transform:translateY(34px)}to{opacity:1;transform:none}}
.inl{opacity:0;animation:inl .6s cubic-bezier(.16,1,.3,1) forwards}
@keyframes inl{from{opacity:0;transform:translateX(-70px)}to{opacity:1;transform:none}}
.inr{opacity:0;animation:inr .6s cubic-bezier(.16,1,.3,1) forwards}
@keyframes inr{from{opacity:0;transform:translateX(70px)}to{opacity:1;transform:none}}
.breathe{animation:breathe 1.5s ease-in-out infinite}
@keyframes breathe{0%%,100%%{transform:scale(1)}50%%{transform:scale(1.045)}}
.glow{animation:glow 1.5s ease-in-out infinite}
@keyframes glow{0%%,100%%{transform:scale(1)}50%%{transform:scale(1.03)}}
.ring{position:absolute;border:3px solid rgba(var(--c2-rgb),.45);border-radius:50%%;animation:ripple 3s ease-out infinite;opacity:0}
@keyframes ripple{0%%{transform:scale(.55);opacity:.7}100%%{transform:scale(1.5);opacity:0}}
.card{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:26px;border-radius:26px;border:1px solid rgba(var(--cc,238,247,240),.35);background:linear-gradient(160deg,rgba(var(--cc,238,247,240),.22),rgba(var(--cc,238,247,240),.06))}
.lab{font-weight:800;letter-spacing:-.02em;text-align:center;line-height:1.2}
.mut{color:var(--mut)}
.acc{color:var(--c2)}
.ic{display:block;color:var(--ink)}
.num{counter-reset:n var(--n)}
.num::after{content:counter(n)}
.count{animation:count 1.3s cubic-bezier(.16,1,.3,1) forwards}
@keyframes count{from{--n:0}to{--n:var(--to)}}
.bar{height:100%%;border-radius:14px;background:linear-gradient(90deg,rgba(var(--cc,0,238,210),.35),rgb(var(--cc,0,238,210)));transform-origin:left center;transform:scaleX(0);animation:grow .9s cubic-bezier(.16,1,.3,1) forwards}
@keyframes grow{to{transform:scaleX(var(--s))}}
.spin{animation:spin 3s linear infinite}
@keyframes spin{to{transform:rotate(var(--turn))}}
.run{position:absolute;width:18px;height:18px;border-radius:50%%;background:var(--c2);animation:run 1.5s linear infinite;opacity:0}
@keyframes run{0%%{transform:translateX(0);opacity:0}15%%{opacity:1}85%%{opacity:1}100%%{transform:translateX(var(--dx));opacity:0}}
.wipe{clip-path:inset(0 100%% 0 0);animation:wipe 1.2s cubic-bezier(.65,0,.35,1) forwards}
@keyframes wipe{to{clip-path:inset(0 0 0 0)}}
"""


def _dots(w, h):
    pts = [(.12, .2, 0), (.86, .26, .6), (.2, .78, 1.2), (.8, .74, 1.8), (.5, .12, 2.4)]
    return ''.join(f'<i class=dot style="left:{int(x * w)}px;top:{int(y * h)}px;animation-delay:{d:.1f}s"></i>' for x, y, d in pts)


def body_compare(mg, w, h):
    cw, ch = int(w * .38), int(h * .62)
    isz = int(min(cw, ch) * .46)

    def card(side, cls, d, win, c):
        halo = f'<i class=glow style="position:absolute;inset:0;border-radius:26px;animation-delay:{ENTER:.2f}s"></i>' if win else ''
        return (f'<div class="card {cls}" style="position:relative;width:{cw}px;height:{ch}px;animation-delay:{d:.2f}s;--cc:var(--c{c}-rgb)">{halo}'
                f'<div style="width:{isz}px;height:{isz}px">{svg(side["icon"], "ic", d + .35, c=c)}</div>'
                f'<div class="lab{" acc" if win else ""}" style="font-size:{_fs(side["label"], cw * .88, cw * .15)}px">{esc(side["label"])}</div></div>')
    mid = f'<div class="pop lab acc" style="font-size:{int(w * .07)}px;width:{int(w * .16)}px;animation-delay:1.1s">{esc(mg["mid"])}</div>'
    return (f'<div class=stage style="gap:{int(w * .02)}px">{card(mg["a"], "inl", .1, mg["win"] == "a", 4)}{mid}'
            f'{card(mg["b"], "inr", .35, mg["win"] == "b", 6)}</div>')


def body_flow(mg, w, h):
    n = len(mg['items'])
    nw = int(w * (.8 / n))
    gap = int((w * .92 - nw * n) / max(1, n - 1))
    isz = int(min(nw * .56, h * .3))
    parts = []
    for i, it in enumerate(mg['items']):
        d = .15 + i * .45
        parts.append(f'<div class="pop" style="width:{nw}px;display:flex;flex-direction:column;align-items:center;gap:22px;animation-delay:{d:.2f}s">'
                     f'<div class="card breathe" style="width:{isz + 44}px;height:{isz + 44}px;animation-delay:{d:.2f}s,{ENTER:.2f}s;--cc:var(--c{(4, 5, 6, 7)[i]}-rgb)">{svg(it["icon"], "ic", d + .2, .7, isz, (4, 5, 6, 7)[i])}</div>'
                     f'<div class=lab style="font-size:{_fs(it["label"], nw + gap * .8, min(nw * .2, 50))}px">{esc(it["label"])}</div></div>')
        if i < n - 1:
            ad = d + .35
            parts.append(f'<div style="position:relative;width:{gap}px;height:4px;flex:none;margin-bottom:{int(h * .12)}px">'
                         f'<svg class="draw" viewBox="0 0 {gap} 12" style="position:absolute;left:0;top:-4px;width:{gap}px;height:12px;color:var(--mut)" preserveAspectRatio="none">'
                         f'<path d="M4 6H{gap - 6}M{gap - 16} 1l10 5-10 5" pathLength="1" style="animation-delay:{ad:.2f}s;animation-duration:.45s"/></svg>'
                         f'<i class=run style="--dx:{gap - 14}px;top:-5px;animation-delay:{ENTER - (1.5 - i * .5) % 1.5:.2f}s"></i></div>')
    return f'<div class=stage style="gap:0;align-items:center">{"".join(parts)}</div>'


def body_number(mg, w, h):
    v, unit = mg['value'], mg['unit']
    pct = unit == '%' and 0 <= v <= 100
    r = int(min(w, h) * .3)
    big = int(r * (.62 if len(_fmt(v)) <= 3 else .46))
    ring = ''
    if pct:
        ring = (f'<svg viewBox="0 0 100 100" style="position:absolute;width:{r * 2}px;height:{r * 2}px;transform:rotate(-90deg)">'
                f'<circle cx=50 cy=50 r=46 fill=none stroke="rgba(255,255,255,.08)" stroke-width=5 />'
                f'<circle cx=50 cy=50 r=46 fill=none stroke="var(--c2)" stroke-width=7 stroke-linecap=round pathLength=100 '
                f'style="stroke-dasharray:100;stroke-dashoffset:100;animation:ringk 1.3s cubic-bezier(.16,1,.3,1) .3s forwards;--p:{100 - v:.1f}"/></svg>'
                '<style>@keyframes ringk{to{stroke-dashoffset:var(--p)}}</style>')
    intv = float(v).is_integer() and abs(v) < 1e7
    numhtml = (f'<span class="num count" style="--to:{int(v)};animation-delay:.3s"></span>' if intv else f'<span class=rise style="animation-delay:.3s">{esc(_fmt(v))}</span>')
    return (f'<div class=stage style="flex-direction:column;gap:{int(h * .05)}px"><div class="breathe" style="position:relative;width:{r * 2}px;height:{r * 2}px;display:flex;align-items:center;justify-content:center;animation-delay:{ENTER:.2f}s">'
            f'{ring}{"" if pct else f"<i class=ring style=width:{r * 2}px;height:{r * 2}px;animation-delay:{ENTER:.2f}s></i>"}'
            f'<div class="lab acc" style="font-size:{big}px;font-variant-numeric:tabular-nums">{numhtml}<span style="font-size:{int(big * .42)}px;margin-left:6px">{esc(unit)}</span></div></div>'
            f'<div class="rise lab" style="font-size:{int(w * .055)}px;animation-delay:1.1s">{esc(mg["label"])}</div></div>')


def body_bars(mg, w, h):
    its = mg['items']
    mx = max(x['value'] for x in its) or 1
    rh = int(min(h * .7 / len(its) * .56, 70))
    rows = []
    for i, it in enumerate(its):
        d = .2 + i * .3
        s = max(.04, it['value'] / mx)
        top = it['value'] == mx
        val = (f'<span class="num count" style="--to:{int(it["value"])};animation-delay:{d:.2f}s"></span>' if float(it['value']).is_integer()
               else esc(_fmt(it['value'])))
        glow = f', glow 1.5s ease-in-out {ENTER:.2f}s infinite' if top else ''
        rows.append(f'<div class=rise style="display:grid;grid-template-columns:{int(w * .2)}px 1fr {int(w * .16)}px;align-items:center;gap:22px;animation-delay:{d - .1:.2f}s">'
                    f'<div class="lab{"" if top else " mut"}" style="font-size:{_fs(it["label"], w * .2, rh * .62)}px;text-align:right">{esc(it["label"])}</div>'
                    f'<div style="height:{rh}px;border-radius:14px;background:rgba(255,255,255,.05)"><div class=bar style="--s:{s:.3f};--cc:var(--c{2 if top else (4, 5, 7, 6)[i]}-rgb);animation:grow .9s cubic-bezier(.16,1,.3,1) {d:.2f}s forwards{glow}"></div></div>'
                    f'<div class="lab{" acc" if top else ""}" style="font-size:{int(min(rh * .66, w * .16 / (.62 * len(_fmt(it["value"])) + len(mg["unit"]) + .2)))}px;font-variant-numeric:tabular-nums;white-space:nowrap">{val}{esc(mg["unit"])}</div></div>')
    return f'<div class=stage style="flex-direction:column;align-items:stretch;justify-content:center;gap:{int(rh * .55)}px;padding:0 {int(w * .07)}px">{"".join(rows)}</div>'


def body_list(mg, w, h):
    its = mg['items']
    rh = int(min(h * .72 / len(its), 150))
    isz = int(rh * .5)
    rows = ''.join(
        f'<div class=inl style="display:flex;align-items:center;gap:30px;animation-delay:{.15 + i * .4:.2f}s">'
        f'<div class=card style="width:{isz + 34}px;height:{isz + 34}px;flex:none;border-radius:50%;--cc:var(--c{(7, 4, 6, 5)[i]}-rgb)">{svg(it["icon"], "ic", .35 + i * .4, .6, isz, (7, 4, 6, 5)[i])}</div>'
        f'<div class=lab style="font-size:{int(rh * .36)}px;text-align:left">{esc(it["label"])}</div></div>' for i, it in enumerate(its))
    return f'<div class=stage style="flex-direction:column;align-items:flex-start;gap:{int(rh * .18)}px;padding:0 {int(w * .12)}px">{rows}</div>'


def body_cycle(mg, w, h):
    its = mg['items']
    n = len(its)
    R = int(min(w, h) * .33)
    cx, cy = w // 2, h // 2
    nodes = ''
    for i, lab in enumerate(its):
        a = -math.pi / 2 + 2 * math.pi * i / n
        x, y = cx + R * math.cos(a), cy + R * math.sin(a)
        nodes += (f'<div class="pop card" style="position:absolute;left:{int(x - w * .13)}px;top:{int(y - 44)}px;width:{int(w * .26)}px;height:88px;border-radius:44px;animation-delay:{.3 + i * .35:.2f}s;--cc:var(--c{(4, 6, 5, 7)[i]}-rgb)">'
                  f'<div class=lab style="font-size:{int(min(w * .045, 44, (w * .26 - 40) / max(1, len(lab))))}px;white-space:nowrap">{esc(lab)}</div></div>')
    arcs = ''
    for i in range(n):   # n 개 호(화살 끝) = n 겹 대칭 → 주기 3초에 360/n 도 회전 = 이음매 없는 반복
        a0 = 2 * math.pi * i / n + .35
        a1 = 2 * math.pi * (i + 1) / n - .35
        x0, y0 = 50 + 44 * math.cos(a0), 50 + 44 * math.sin(a0)
        x1, y1 = 50 + 44 * math.cos(a1), 50 + 44 * math.sin(a1)
        arcs += f'<path d="M{x0:.2f} {y0:.2f}A44 44 0 0 1 {x1:.2f} {y1:.2f}" pathLength="1" style="animation-delay:{.2 + i * .25:.2f}s;animation-duration:.6s"/>'
    isz = int(R * .62)
    return (f'<div style="position:absolute;left:{cx - R}px;top:{cy - R}px;width:{R * 2}px;height:{R * 2}px">'
            f'<svg class="draw spin" viewBox="0 0 100 100" style="width:100%;height:100%;color:var(--mut);--turn:{360 / n:.2f}deg;animation:spin 3s linear {ENTER:.2f}s infinite">{arcs}</svg></div>'
            f'<div class=breathe style="position:absolute;left:{cx - isz // 2}px;top:{cy - isz // 2}px;width:{isz}px;height:{isz}px;animation-delay:{ENTER:.2f}s">{svg(mg["icon"], "ic", .1, .9, c=2)}</div>'
            f'{nodes}')


def body_icon(mg, w, h):
    isz = int(min(w, h) * .4)
    rings = ''.join(f'<i class=ring style="width:{int(isz * 1.5)}px;height:{int(isz * 1.5)}px;animation-delay:{d:.1f}s"></i>' for d in (0.9, 2.4))
    sub = f'<div class="rise lab mut" style="font-size:{int(w * .04)}px;animation-delay:1.35s">{esc(mg["sub"])}</div>' if mg.get('sub') else ''
    return (f'<div class=stage style="flex-direction:column;gap:{int(h * .05)}px"><div style="position:relative;display:flex;align-items:center;justify-content:center;width:{int(isz * 1.5)}px;height:{int(isz * 1.2)}px">{rings}'
            f'<div class=breathe style="width:{isz}px;height:{isz}px;animation-delay:{ENTER:.2f}s">{svg(mg["icon"], "ic", .1, 1.2, c=2)}</div></div>'
            f'<div class="rise lab" style="font-size:{int(w * .065)}px;animation-delay:1.05s">{esc(mg["label"])}</div>{sub}</div>')


def body_quote(mg, w, h):
    q = int(min(w, h) * .2)
    by = f'<div class="rise lab mut" style="font-size:{int(w * .04)}px;animation-delay:1.6s">— {esc(mg["by"])}</div>' if mg.get('by') else ''
    return (f'<div class=stage style="flex-direction:column;gap:{int(h * .05)}px;padding:0 {int(w * .09)}px">'
            f'<div style="width:{q}px;height:{q}px">{svg("quote", "ic", .05, .8, c=5)}</div>'
            f'<div class="wipe lab" style="font-size:{int(w * .062)}px;animation-delay:.5s;line-height:1.35">{esc(mg["text"])}</div>{by}</div>')


BODY = {'compare': body_compare, 'flow': body_flow, 'number': body_number, 'bars': body_bars, 'list': body_list,
        'cycle': body_cycle, 'icon': body_icon, 'quote': body_quote}


CREDIT_CSS = ".credit{position:absolute;right:60px;top:40px;max-width:70%;font-size:28px;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;z-index:5}"


def mg_html(tokens, font_css, family, mg, w, h, credit=''):
    css = CSS % {'w': w, 'h': h, 'family': family, 'gw': int(w * 1.1), 'gh': int(h * 1.1), 'fade': int(h * .12)}   # 아래 12% = 바탕으로 녹임(자막 자리와 이음매 0)
    cr = f'<div class=credit>{esc(credit)}</div>' if credit else ''
    return (f'<!doctype html><html><head><meta charset=utf-8><style>{tokens}{palette_css(tokens)}{font_css}{css}{CREDIT_CSS}</style></head><body>'
            f'<div class=box><div class=grid></div>{_dots(w, h)}{BODY[mg["type"]](mg, w, h)}</div>{cr}</body></html>')


FREEZE_JS = "() => { document.getAnimations().forEach(a => a.pause()); return document.getAnimations().length; }"
SEEK_JS = "(t) => { document.getAnimations().forEach(a => { a.currentTime = t; }); }"
CHECK_JS = """() => { const r = document.querySelector('.s'); if (!r) return {n: 0, t: 0};
  return {n: r.querySelectorAll('*').length, t: (r.innerText || '').replace(/\\s+/g, '').length, a: document.getAnimations().length}; }"""
CSP = "<meta http-equiv=Content-Security-Policy content=\"default-src 'none'; style-src 'unsafe-inline'; img-src data:; font-src file: data:\">"


def motion_page(tokens, font_css, family, css, html_, w, h, credit=''):
    """모션 디자이너(Opus) 산출 한 장면 = 격리 페이지 — CSP(스크립트·네트워크 0) · 팔레트·폰트·무대 크기는 여기서 준다."""
    cr = f'<div class=credit>{esc(credit)}</div>' if credit else ''
    base = (f"*{{box-sizing:border-box;margin:0;padding:0}}html,body{{width:{w}px;height:{h}px;overflow:hidden;background:var(--bg);"
            f"font-family:{family},'Noto Sans CJK KR',sans-serif;color:var(--ink);word-break:keep-all;-webkit-font-smoothing:antialiased}}"
            f".s{{position:absolute;inset:0;overflow:hidden}}"
            # 무대 바탕 = 틀 도식(.box)과 같은 은은한 두 빛(팔레트 토큰) + 아래 12% 녹임(자막 자리와 이음매 0)
            f".amb{{position:absolute;inset:0;background:radial-gradient({int(w * 1.1)}px {int(h * 1.1)}px at 30% 25%,rgba(var(--c5-rgb),.20),transparent 60%),"
            f"radial-gradient({int(w * 1.1)}px {int(h * 1.1)}px at 75% 75%,rgba(var(--c4-rgb),.16),transparent 60%),var(--bg)}}"
            f".fade{{position:absolute;left:0;right:0;bottom:0;height:{int(h * .12)}px;background:linear-gradient(transparent,var(--bg));pointer-events:none}}")
    return (f'<!doctype html><html><head><meta charset=utf-8>{CSP}<style>{tokens}{palette_css(tokens)}{font_css}{base}{CREDIT_CSS}</style>'
            f'<style>{css}</style></head><body><div class=amb></div><div class="s">{html_}</div><div class=fade></div>{cr}</body></html>')


def _open(page, html_path, w, h):
    page.set_viewport_size({'width': w, 'height': h})
    page.goto('file://' + str(html_path))
    page.evaluate('document.fonts.ready')
    page.wait_for_timeout(80)
    page.evaluate(FREEZE_JS)


def capture(page, html_path, outdir, dur, w, h):
    """틀 도식 = 등장(ENTER) + 반복 한 주기(LOOP)만 찍는다(장면이 짧으면 장면 길이까지만). 반환 = (장수, 반복 시작, 반복 길이) — 반복 길이 0 = 반복 불요."""
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    _open(page, html_path, w, h)
    ef, lf = int(round(ENTER * FPS)), int(round(LOOP * FPS))
    need = int(math.ceil(dur * FPS))
    n = min(need, ef + lf)
    for k in range(n):
        page.evaluate(SEEK_JS, k * 1000.0 / FPS)
        page.screenshot(path=str(outdir / f'f{k:04d}.jpg'), type='jpeg', quality=92)
    return n, ef, (lf if n == ef + lf and need > n else 0)


def capture_full(page, html_path, outdir, dur, w, h):
    """모션 디자이너 장면 = 장면 전체를 찍는다(비트가 문장 박자를 따라 끝까지 바뀐다 · 반복 가정 없음).
    반환 = 장수 · 검문 실패(요소 3개 미만 · 애니메이션 0 · 글자 과다) = 0 → 호출부가 틀 도식으로 바꾼다."""
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    _open(page, html_path, w, h)
    c = page.evaluate(CHECK_JS)
    if c.get('n', 0) < 3 or c.get('a', 0) < 1 or c.get('t', 0) > 40:
        return 0
    n = int(math.ceil(dur * FPS))
    for k in range(n):
        page.evaluate(SEEK_JS, k * 1000.0 / FPS)
        page.screenshot(path=str(outdir / f'f{k:04d}.jpg'), type='jpeg', quality=92)
    return n
