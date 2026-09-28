#!/usr/bin/env python3
"""유튜브 숏폼(ys) 모션 디자이너 — 장면별 모션 그래픽 코드(HTML·CSS·SVG)를 Opus 5.5 high 에 맡기는 1콜의 입력 조립·산출 검문.
(운영자 260928 «모션 그래픽 = 화면 글자 없이 · 화면을 넓게 · 액팅이 다채롭게 · 네온 단색 금지 · LLM 이 필요하면 opus 5.5 high»)

  ys_motion.py prompt <plan.json> <timing.json> <meta.json> <ratio 9:16|16:9>  → stdout = 지침 뒤에 붙일 [영상]·[캔버스]·[장면] 블록
  ys_motion.py parse  <raw.txt> <outdir> <n_scenes>                          → outdir/motion.json {scenes:[{i, css, html}]} (검문 통과분만)

검문 = 신뢰 불가 산출(모델이 쓴 코드) → 금지 태그·속성·url(·@import·전환·레이아웃 애니메이션 제거 + 길이 상한.
렌더 쪽 이중 방어 = 페이지 CSP(script-src 'none' · 네트워크 0) · 장면마다 따로 연 페이지(서로 간섭 0) · 실패 장면 = 기본 도식(ys_mg).
"""
import json
import os
import re
import sys

CAP = 12000        # 장면 하나 css+html 상한(지침 9000 + 여유)
TEXT_CAP = 40      # 화면 글자 상한(공백 제외) — 넘으면 「글자 없는 모션」 계약 위반 = 그 장면 기본 도식
PALETTE = [('c1', 'accent'), ('c2', 'accent-2'), ('c3', 'cat-intl'), ('c4', 'cat-pol'), ('c5', 'cat-tech'),
           ('c6', 'accent-6'), ('c7', 'cat-soc'), ('c8', 'bias-l2')]   # 무대 팔레트 = viewer :root 색 토큰(값 창작 0 · 이름만 짧게)


def canvas(ratio):
    """무대(자막 자리 위 전체) = (W, H). 자막 = 9:16 1480~ · 16:9 900~(ys_render caption_html 과 동값)."""
    return (1920, 880) if ratio == '16:9' else (1080, 1440)


def prompt_block(plan, timing, meta, ratio):
    w, h = canvas(ratio)
    out = [f"[영상] 제목: {meta.get('title', '')} · 채널: {meta.get('channel', '')} · 숏폼 제목: {plan.get('short_title') or plan.get('title', '')}",
           f"[캔버스] W={w} H={h} · 비율 {ratio}", '[장면]']
    only = {int(x) for x in re.findall(r'\d+', os.environ.get('YS_MOTION_ONLY', ''))}   # 맥·그록이 못 채운 장면만(비면 전부)
    for i, sc in enumerate(plan['scenes']):
        if only and i not in only:
            continue
        t = timing['scenes'][i] if i < len(timing.get('scenes') or []) else {}
        d = float(t.get('dur') or 0) + 0.5
        beats = '; '.join(f"{a:.1f}~{z:.1f}s 「{s}」" for a, z, s in (t.get('sents') or []))
        mg = sc.get('mg') or {}
        key = ' / '.join(x for x in (str(sc.get('big') or '').replace('\n', ' '), str(sc.get('head') or '').replace('\n', ' ')) if x)
        out.append(f"- i={i} · 길이 {d:.1f}s · 문장 박자: {beats or sc.get('vo', '')}\n  핵심: {key} · 도식 힌트: {mg.get('type', '')}")
    return '\n'.join(out)


BAD_TAGS = r'script|iframe|object|embed|link|meta|base|img|image|foreignobject|audio|video|source|form|input|button|textarea|select|style|title|a'


def clean_html(h):
    h = re.sub(r'(?is)<\s*(script|style|iframe|object|embed|foreignobject|title)\b.*?<\s*/\s*\1\s*>', '', h)
    h = re.sub(rf'(?is)<\s*/?\s*(?:{BAD_TAGS})\b[^>]*>', '', h)
    h = re.sub(r'(?is)\son[a-z]+\s*=\s*("[^"]*"|\'[^\']*\'|[^\s>]+)', '', h)                 # 이벤트 속성
    h = re.sub(r'(?is)\s(?:xlink:)?href\s*=\s*("(?!#)[^"]*"|\'(?!#)[^\']*\')', '', h)          # 문서 밖 참조(내부 #id 만 허용)
    h = re.sub(r'(?is)javascript:|url\s*\(', '', h)
    return h


def clean_css(c):
    c = re.sub(r'(?is)@import[^;]*;?', '', c)
    c = re.sub(r'(?is)[^;{}]*url\s*\([^)]*\)[^;{}]*;?', '', c)                             # url( 든 선언 통째 제거
    c = re.sub(r'(?is)expression\s*\(|javascript:|behavior\s*:', '', c)
    c = re.sub(r'(?is)(^|[;{\s])transition(-[a-z-]+)?\s*:[^;{}]*;?', r'\1', c)               # 전환 = 벽시계 의존(프레임 구동 밖)
    c = re.sub(r'</', '', c)
    return c


def visible_text_len(h):
    t = re.sub(r'(?is)<[^>]+>', ' ', h)
    return len(re.sub(r'\s+', '', re.sub(r'&[a-z#0-9]+;', 'x', t)))


def extract(raw):
    m = re.search(r'```[ \t]*(?:json)?\s*(\{[\s\S]*?)(?:```|\Z)', raw, re.I)
    for cand in ([m.group(1)] if m else []):
        try:
            return json.loads(cand.strip())
        except ValueError:
            pass
    dec = json.JSONDecoder()
    for mm in re.finditer(r'\{', raw):
        try:
            obj, _ = dec.raw_decode(raw, mm.start())
        except ValueError:
            continue
        if isinstance(obj, dict) and isinstance(obj.get('scenes'), list):
            return obj
    return None


def normalize(j, n):
    """검문 → [{i, css, html}] · 버린 장면 사유 목록. 계약 위반 장면은 버린다(렌더가 기본 도식으로 채움)."""
    keep, drop = [], []
    seen = set()
    for sc in (j.get('scenes') or [])[:24]:
        if not isinstance(sc, dict):
            continue
        try:
            i = int(sc.get('i'))
        except (TypeError, ValueError):
            continue
        if not 0 <= i < n or i in seen:
            continue
        css, html = str(sc.get('css') or ''), str(sc.get('html') or '')
        if len(css) + len(html) > CAP:
            drop.append((i, '코드가 너무 김'))
            continue
        html, css = clean_html(html), clean_css(css)
        if '<' not in html or '@keyframes' not in css:
            drop.append((i, '움직임 없음'))
            continue
        if visible_text_len(html) > TEXT_CAP:
            drop.append((i, '화면 글자가 너무 많음'))
            continue
        seen.add(i)
        keep.append({'i': i, 'css': css, 'html': html})
    return sorted(keep, key=lambda x: x['i']), drop


def main(argv):
    if len(argv) >= 6 and argv[1] == 'prompt':
        plan, timing, meta = (json.load(open(p, encoding='utf-8')) for p in argv[2:5])
        print(prompt_block(plan, timing, meta, argv[5]))
        return 0
    if len(argv) >= 5 and argv[1] == 'parse':
        raw = open(argv[2], encoding='utf-8', errors='replace').read()
        j = extract(raw)
        if not isinstance(j, dict):
            print('산출에서 JSON을 찾지 못함', file=sys.stderr)
            return 1
        keep, drop = normalize(j, int(argv[4]))
        json.dump({'scenes': keep, 'dropped': [{'i': i, 'why': w} for i, w in drop]},
                  open(f'{argv[3]}/motion.json', 'w', encoding='utf-8'), ensure_ascii=False)
        print(f'모션 디자인: 장면 {len(keep)}개 통과 · 버림 {len(drop)}')
        return 0 if keep else 1
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == '__main__':   # seal-ok: 단독 CLI(prompt·parse) — ys_mg 는 렌더가 부르는 라이브러리라 진입점 불요
    sys.exit(main(sys.argv))
