#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""픽셀 펫 데모 생성기 — 아틀라스를 실제로 재서 판독표를 만들고, 부품 2파일과 그림을 한 파일에 넣어 데모를 굽는다.

  python3 apps/pet/build_pet_demo.py            # 실측 + 데모 굽기(기본)
  python3 apps/pet/build_pet_demo.py --measure  # 실측만(apps/pet/frames.json)

산출 2개 = 기계산출물(손편집 금지 · 값 바꾸려면 이 스크립트나 템플릿을 고쳐 다시 돌린다)
  · apps/pet/frames.json    82칸 실측표
  · apps/pet/펫_데모.html    자기완결 1파일(외부 요청 0 · 폰에서 열어도 돈다)

아틀라스 정본 = viewer/pet_crab.png(1320x1080 · 운영자 260710 업로드 캐릭터 → 아틀라스).
루트에 올라온 jpg 판(apps/pet/원본업로드_260817_아틀라스_jpg판.jpg)은 같은 그림의 검은 배경 사본이라 보관만 하고 쓰지 않는다
(실측 = 실루엣 99.3% 일치 · 배경 투명이 아니라 화면에 얹으면 검은 사각형이 남는다).
"""
import base64
import json
import os
import sys
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PET = os.path.join(ROOT, 'apps', 'pet')
VIEWER = os.path.join(ROOT, 'viewer')   # 부품 2파일의 거처 = 라이브 폴더(화면이 읽는 자리 · 사본 0)
ATLAS = os.path.join(ROOT, 'viewer', 'pet_crab.png')
TPL = os.path.join(PET, '_데모_템플릿.html')
OUT = os.path.join(PET, '펫_데모.html')
FRAMES = os.path.join(PET, 'frames.json')

# 지오메트리 = viewer/index.html 픽셀 펫 블록의 PET 상수 값 사본(단일출처 · 여기서 창작 0)
TW, TH, COLS, ROWS, N = 132, 120, 10, 9, 82
SIT_MAX_H = 70   # 몸 높이가 이보다 낮으면 웅크린 자세(실측 = 앉음 48~51 vs 서기 70~80 사이의 골)


def measure():
    """82칸 각각의 몸 크기·발 접지 중심을 잰다.

    ⚠ 몸통 = 「가장 큰 한 덩이」로 잡는다(붙어 있는 화소를 번져 나가며 모은다).
       열 화소 개수로 파티클(반짝임)을 걸러내려던 첫 판은 세로로 3~4개 붙은 반짝임이 그대로 통과해
       몸 높이가 48 → 107로 부풀었고, 그 값으로 자세를 갈랐더니 앉은 칸 28개가 걷기로 오분류됐다
       (260817 실측 · 판독표를 눈으로 봐야 드러났다 = 숫자만으론 안 보이는 자리).
    """
    from PIL import Image
    im = Image.open(ATLAS)
    if im.size != (COLS * TW, ROWS * TH):
        raise SystemExit('아틀라스 크기가 %s — 기대값 %s' % (im.size, (COLS * TW, ROWS * TH)))
    px = im.convert('RGBA').load()
    rows = []
    for f in range(N):
        cx, cy = (f % COLS) * TW, (f // COLS) * TH
        seen = [[False] * TW for _ in range(TH)]
        best = None
        for sy in range(TH):
            for sx in range(TW):
                if seen[sy][sx] or px[cx + sx, cy + sy][3] <= 40:
                    continue
                stack, cells = [(sx, sy)], []
                seen[sy][sx] = True
                while stack:
                    x, y = stack.pop()
                    cells.append((x, y))
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < TW and 0 <= ny < TH and not seen[ny][nx] and px[cx + nx, cy + ny][3] > 40:
                            seen[ny][nx] = True
                            stack.append((nx, ny))
                if best is None or len(cells) > len(best):
                    best = cells
        if not best:
            rows.append({'f': f, 'empty': True})
            continue
        xs = [x for x, _ in best]
        ys = [y for _, y in best]
        bottom = max(ys)
        feet = [x for (x, y) in best if y >= bottom - 3]
        h = bottom - min(ys) + 1
        rows.append({'f': f, 'x0': min(xs), 'x1': max(xs), 'y0': min(ys), 'y1': bottom,
                     'w': max(xs) - min(xs) + 1, 'h': h, 'px': len(best),
                     'feetC': round((min(feet) + max(feet)) / 2.0, 1), 'sit': h < SIT_MAX_H})
    return rows


def summary(rows):
    sit = [r['f'] for r in rows if r.get('sit')]
    walk = [r['f'] for r in rows if not r.get('sit') and not r.get('empty')]
    fc = [r['feetC'] for r in rows if 'feetC' in r]
    return {
        'atlas': 'viewer/pet_crab.png', 'tile': [TW, TH], 'cols': COLS, 'rows': ROWS, 'frames': N,
        'sit_frames': sit, 'walk_frames': walk,
        'feet_center': {'min': min(fc), 'max': max(fc), 'avg': round(sum(fc) / len(fc), 1)},
        'floor_y': {'min': min(r['y1'] for r in rows if 'y1' in r), 'max': max(r['y1'] for r in rows if 'y1' in r)},
    }


def check_sitframes(rows):
    """부품이 들고 있는 앉은 칸 목록이 방금 실측과 같은지 대조.

    ⚠ 이 대조가 실효 조건 — 목록이 두 곳(부품 nm-pet.js · 실측 frames.json)에 있어서,
       아틀라스를 갈고 실측만 다시 돌리면 부품은 옛 목록으로 남는다(화면은 멀쩡하고 자세만 어긋난다 = 조용한 낡음).
       어긋나면 데모를 굽지 않고 그 자리에서 멈춘다.
    """
    js = open(os.path.join(VIEWER, 'nm-pet.js'), encoding='utf-8').read()
    i = js.find('sitFrames:')
    if i < 0:
        raise SystemExit('부품에 sitFrames 목록이 없다 — viewer/nm-pet.js 확인')
    lit = js[js.index('[', i):js.index(']', i) + 1]
    have = [int(x) for x in __import__('re').findall(r'\d+', lit)]
    want = [r['f'] for r in rows if r.get('sit')]
    if have != want:
        raise SystemExit('부품 앉은 칸 목록이 실측과 다르다.\n  부품 %d칸 = %s\n  실측 %d칸 = %s\n'
                         '  → viewer/nm-pet.js sitFrames 를 아래 줄로 교체하고 다시 돌려라.\n  sitFrames: [%s]'
                         % (len(have), have, len(want), want, ','.join(str(x) for x in want)))
    return len(want)


def build(rows):
    check_sitframes(rows)
    tpl = open(TPL, encoding='utf-8').read()
    b64 = base64.b64encode(open(ATLAS, 'rb').read()).decode('ascii')
    css = open(os.path.join(VIEWER, 'nm-pet.css'), encoding='utf-8').read()
    js = open(os.path.join(VIEWER, 'nm-pet.js'), encoding='utf-8').read()
    kst = datetime.now(timezone(timedelta(hours=9))).strftime('%y%m%d %H:%M')
    # ⚠ 닫는 태그 이스케이프가 실효 조건 — 부품 주석에 상속 예시(<script …></script>)가 그대로 들어 있어서
    #    그대로 넣으면 그 자리에서 데모의 스크립트가 끊기고 펫이 아예 안 만들어진다(260817 첫 실행 실측).
    def inline(txt, tag):
        return txt.replace('</' + tag, '<\\/' + tag).replace('</' + tag.upper(), '<\\/' + tag.upper())

    html = (tpl
            .replace('__ATLAS_B64__', 'data:image/png;base64,' + b64)
            .replace('__FRAMES_JSON__', json.dumps(rows, ensure_ascii=False).replace('</', '<\\/'))
            .replace('__PET_CSS__', css.replace('</style', '<\\/style'))
            .replace('__PET_JS__', inline(js, 'script'))
            .replace('__BUILT__', kst))
    for slot in ('__ATLAS_B64__', '__FRAMES_JSON__', '__PET_CSS__', '__PET_JS__', '__BUILT__'):
        if slot in html:
            raise SystemExit('치환 안 된 자리 = %s' % slot)
    open(OUT, 'w', encoding='utf-8').write(html)
    return len(html)


if __name__ == '__main__':
    rows = measure()
    s = summary(rows)
    json.dump({'_meta': s, 'frames': rows}, open(FRAMES, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('실측 = 앉음 %d칸 / 서기 %d칸 / 발 접지 중심 %.1f~%.1f(평균 %.1f) / 바닥 y %d~%d'
          % (len(s['sit_frames']), len(s['walk_frames']),
             s['feet_center']['min'], s['feet_center']['max'], s['feet_center']['avg'],
             s['floor_y']['min'], s['floor_y']['max']))
    print('  앉음 =', s['sit_frames'])
    print('  서기 =', s['walk_frames'])
    print('  JS sitFrames 줄 =', 'sitFrames: [' + ','.join(str(x) for x in s['sit_frames']) + ']')
    if '--measure' in sys.argv:
        print('실측표 =', os.path.relpath(FRAMES, ROOT))
        sys.exit(0)
    n = build(rows)
    print('데모 = %s (%.0fKB)' % (os.path.relpath(OUT, ROOT), n / 1024))
