#!/usr/bin/env python3
"""유튜브 숏폼(ys) 연출 도서관 — apps/k/library TSV = 도서관 · 색인만 보여 주고 고른 번호의 원문만 꺼낸다.
(운영자 260929 «라이브러리는 완전히 도서관 · 어떤 걸 꺼내 쓸지 그때그때 참조 · 이 화각을 써야겠다고 구상하는 장치 ·
  정해 준 대로 그것만 참조해서 용량을 줄인다 · 그 상황에 그게 효과적이라고 판단하는 감독 알고리즘이 중요»)

  ys_lib.py index scene|director       → stdout = 색인 블록(번호 · 이름 · 언제 효과적인지 한 줄) — 고르는 콜(대본 초안 · 감독 구상)에 붙인다
  ys_lib.py fetch scene|director ID…   → stdout = 고른 번호의 원문 블록(정확한 방법 · 추천/피할 조합 · 리스크) — 쓰는 콜(다듬기 · 감독 쓰기)에 붙인다

흐름 = ① 색인(작다)으로 고른다 → ② 기계가 그 번호의 행만 도서관에서 꺼낸다 → ③ 쓰는 콜은 그 원문만 보고 구현한다.
정본 = 라이브러리 TSV(여기는 실행할 때 읽기만 · 행을 지침에 옮겨 적지 않는다 = PROJECT_MEMORY 라이브러리 인라인 금지 준수).
색인에서 뺀다 = ys 규칙과 부딪치는 행(얼굴 초근접·칸 분할·말하는 입·돌아서기 · 영상 실측 ⚪) — 색인에 없는 번호는 꺼내지도 않는다.
원문 위생 = 영문 칸의 부정 조각·화풍 낱말은 지우고 대명사는 「the subject」로(쓰는 콜 규칙 = 대명사·부정문·화풍 낱말 금지).
라이브러리가 없거나 깨져도 빈 블록(fail-soft) — 고르고 쓰는 콜은 그대로 돈다.
"""
import csv
import os
import re
import sys
from pathlib import Path

LIB = Path(os.environ.get('YS_LIB_DIR') or Path(__file__).resolve().parents[2] / 'apps' / 'k' / 'library')

PRON = re.compile(r"(?i)\b(he|she|him|himself|herself)\b|\b(his|her|hers)\b")
NEG = re.compile(r"(?i)^\s*(no|not|without|avoid|never|don't|do not)\b|\bno\s+(camera\s+)?(movement|motion|text|people)\b")
STYLEW = re.compile(r"(?i)\b(cinematic|photo-?real\w*|realistic|realism|documentary|film grain|film still|anime|cartoon|3d render|hyper-?detailed|8k|4k|35mm film)\b|\b[\w-]+ style\b")
KO = re.compile('[가-힣]')

# 색인에서 뺀다: 얼굴 초근접(빅 클로즈업·익스트림 클로즈업·초커·비통 눈물·충격 초커·광각 더치 얼굴·발화 빅클로즈업 = 자막 띠·얼굴 드리프트)
#   · 칸 분할(전/후 분할 = 한 화면 계약) · 얼굴 크래시 줌 · 립싱크·말하며 손짓(입 움직임 = 나레이션 영상에선 립싱크처럼 보인다) · 돌아서기(얼굴이 사라지면 다른 사람)
DROP = {'S09', 'S10', 'S12', 'DF-01', 'DF-16', 'DF-29', 'DF-31', 'SG-01', 'M14', 'AN-23', 'AN-24', 'AN-34'}
LENS = {f'L{n:02d}' for n in (3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 18, 19)}   # 흔한 초점거리 + 틸트시프트·심도(어안·아나모픽·빈티지 = 화풍 축)
VR_DEVICES = {'VR-16', 'VR-17', 'VR-18', 'VR-19'}   # 은유·환유·반어·과장 = 썸네일 만평 장치(CARTOON_DEVICES)와 같은 네 갈래


def _ok(marks):
    """영상 실측 신뢰도 칸(✅·🟡·⚪) — ⚪ = 실측 없음."""
    return lambda rid, r, hdr: (lambda i: i is not None and i < len(r) and r[i].strip()[:1] in marks)(_col(hdr, 'AI 신뢰도'))


# 서랍 = (도서관 파일, 색인 제목, 거르개) — 호출별로 여는 서랍만 색인에 싣는다
SHELVES = {
    'scene': [
        ('16_curation_dispatch', '정서 배정표(출발점 · 정서 → 샷·앵글·화각·조명 · 표는 출발점, 장면 내용이 우선)', lambda rid, r, h: rid.startswith('CD-') and rid != 'CD-10'),
        ('22_expression_emotion', '표정·자세(인물 장면 · 감정 형용사 대신 보이는 몸 단서)', None),
        ('33_gesture_interaction', '몸짓·손(인물 장면)', None),
        ('38_cardnews_distance_crop', '거리·크롭(핵심 피사체·손 인서트)', None),
        ('40_cardnews_staging', '상황 연출(상황 장면 · 한 프레임에 상황이 읽히게)', None),
        ('15_visual_rhetoric', '은유 장치(피사체 장면 · 하나만 골라 끝까지)', lambda rid, r, h: rid in VR_DEVICES),
        ('11_acting_shadow_light', '미세 움직임(motion)', lambda rid, r, h: rid.startswith('AN-') and _ok('✅🟡')(rid, r, h)),
    ],
    'director': [
        ('16_curation_dispatch', '정서 배정표(출발점 · 정서 → 샷·앵글·화각·조명 · 표는 출발점, 장면 내용이 우선)', lambda rid, r, h: rid.startswith('CD-') and rid != 'CD-10'),
        ('01b_camera_shot_size', '샷 크기(S)', None),
        ('01a_camera_lens_focal_length', '렌즈·심도(L)', lambda rid, r, h: rid in LENS),
        ('01c_camera_height_tilt', '카메라 높이·각도(H)', None),
        ('01d_camera_orientation', '카메라 방향·시선(O)', None),
        ('01e_camera_relationship_pov', '관계·시점(R)', None),
        ('06_camera_movement_video', '카메라 무브(M · 영상 실측 ✅만)', _ok('✅')),
        ('12_lighting_emotion', '빛·분위기(LGT · 장면 첫 비트에만)', None),
        ('11_acting_shadow_light', '연기(AN · 인물 비트)', lambda rid, r, h: rid.startswith('AN-') and _ok('✅🟡')(rid, r, h)),
        ('22_expression_emotion', '표정 움직임(EM · 인물 비트)', None),
        ('17_composition', '구도(COMP · 세로 화면)', lambda rid, r, h: not KO.search(r[2] if len(r) > 2 else '가')),
        ('21_transitions_editing', '비트·장면 잇기(TR)', lambda rid, r, h: rid in {'TR-02', 'TR-03', 'TR-04', 'TR-12', 'TR-16', 'TR-17', 'TR-18', 'TR-20', 'TR-24'}),
    ],
}
NAME_KEYS = ('한국어명', '상황 유형', '카드 정서/역할', '항목', '기법', '구조')
WHEN_KEYS = ('사용하면 좋은 상황', '정서 효과', '분위기/용도', '무엇을·왜', '적용/효과', '추천 상황', '언제 쓰나', '효과', '기준', '설명/키워드')
FETCH_SKIP = ('GPT Image', 'NanoBanana', 'Nanobanana', '예시장면', '유사어', '강도', '변수 역할', '대분류', '화풍', 'ChatGPT지시문', '비고',
              '비교판정', '분리인덱스', 'Gemini_메모')   # 이미지 전용·편집 메타 칸 = 쓰는 콜에 쓸모없다
CUT_WHEN, CUT_CELL = 38, 150


def _rows(name):
    try:
        with open(LIB / f'{name}.tsv', encoding='utf-8') as f:
            rows = list(csv.reader(f, delimiter='\t'))
    except (OSError, csv.Error):
        return [], []
    if not rows:
        return [], []
    return [h.lstrip('﻿').strip() for h in rows[0]], rows[1:]


def _col(hdr, *keys):
    """헤더 이름으로 칸을 찾는다(파일마다 위치가 달라도) — 앞선 키가 우선."""
    for k in keys:
        for i, h in enumerate(hdr):
            if k in h:
                return i
    return None


def _cell(r, i, cap):
    return re.sub(r'\s+', ' ', r[i]).strip()[:cap] if i is not None and i < len(r) else ''


def clean_en(s):
    """원문 영문 칸 위생 — 쉼표 조각 단위로 부정·화풍 낱말 조각을 빼고 대명사는 the subject 로."""
    s = re.sub(r'\(/\w+\)', '', str(s or '')).replace('—', ', ')
    s = PRON.sub(lambda m: 'the subject' if m.group(1) else "the subject's", s)
    keep = [p.strip() for p in s.split(',') if p.strip() and not NEG.search(p) and not STYLEW.search(p)]
    return ', '.join(keep)


def _shelf(kind):
    """(파일, 제목, [(ID, 이름, 행, 헤더)]) — DROP·거르개 통과분만."""
    out = []
    for name, title, keep in SHELVES.get(kind, []):
        hdr, rows = _rows(name)
        ni = _col(hdr, *NAME_KEYS)
        got = []
        for r in rows:
            rid = (r[0] if r else '').lstrip('﻿').strip()
            if not rid or rid in DROP or not re.match(r'^[A-Z]{1,5}-?\d{2,3}$', rid) or (keep and not keep(rid, r, hdr)):
                continue
            got.append((rid, _cell(r, ni, 30).rstrip(' —-(·:'), r, hdr))
        if got:
            out.append((name, title, got))
    return out


def _when(rid, r, hdr):
    if rid.startswith('CD-'):   # 배정표 = 정서 → 번호 묶음 그대로(이게 곧 출발점)
        return ' · '.join(f'{h} {_cell(r, i, 30)}' for i, h in enumerate(hdr) if i > 1 and h not in ('화풍',) and _cell(r, i, 30))
    t = _cell(r, _col(hdr, *WHEN_KEYS), 200)
    t = re.sub(r'[\(\[].*?[\)\]]', '', t).strip(' ·—-')
    return t[:CUT_WHEN] + ('…' if len(t) > CUT_WHEN else '')


def index(kind):
    """색인 블록 — 번호 · 이름 · 언제 효과적인지(짧게). 정확한 방법은 싣지 않는다(고른 뒤 fetch)."""
    shelves = _shelf(kind)
    if not shelves:
        return ''
    head = {'scene': '[장면 색인] (연출 도서관 색인 — 번호·이름·언제 효과적인지만 · 정확한 방법은 고른 뒤 원문으로 받는다)',
            'director': '[연출 색인] (연출 도서관 색인 — 번호·이름·언제 효과적인지만 · 정확한 방법은 고른 뒤 원문으로 받는다)'}[kind]
    head += '\n(배정표가 가리키는 번호 중 아래 색인에 없는 것 = 이 영상에선 쓰지 않는 기법 — 얼굴 초근접 등 · 가장 가까운 색인 번호로 바꿔 고른다)'
    out = [head]
    for _name, title, got in shelves:
        out.append(f'▸ {title}')
        out.extend(f'{rid} {nm} — {_when(rid, r, hdr)}' if nm else f'{rid} — {_when(rid, r, hdr)}' for rid, nm, r, hdr in got)
    return '\n'.join(out)


def offered(kind):
    """그 색인에 실린 번호 — 고른 번호 감사 기준(색인 밖 번호 = 지어낸 번호로 센다)."""
    return {rid for _n, _t, got in _shelf(kind) for rid, _nm, _r, _h in got}


def fetch(ids, kind, cap=24):
    """고른 번호 → 원문 블록(색인에 있는 번호만 · 처음 나온 순서 · 최대 cap 행). 영문 칸은 위생을 거친다."""
    want, seen = [], set()
    for x in ids or []:
        x = str(x).strip()
        if x and x not in seen:
            seen.add(x); want.append(x)
    rows = {rid: (nm, r, hdr) for _n, _t, got in _shelf(kind) for rid, nm, r, hdr in got}
    out = []
    for rid in [x for x in want if x in rows][:cap]:
        nm, r, hdr = rows[rid]
        lines = [f'■ {rid} {nm}']
        for i, h in enumerate(hdr):
            if i == 0 or i >= len(r) or not r[i].strip() or any(k in h for k in FETCH_SKIP) or h in NAME_KEYS:
                continue
            v = _cell(r, i, 400)
            if not KO.search(v):
                v = clean_en(v)
            if v:
                lines.append(f"  · {re.sub(r'[(].*?[)]', '', h).strip() or h}: {v[:CUT_CELL]}")   # 칸 이름 괄호 설명 = 카드 편집용 메모
        out.append('\n'.join(lines))
    if not out:
        return ''
    return ('[고른 번호 원문] (연출 도서관에서 꺼낸 정확한 방법 — 이 방법대로 구현하되 영어 구절을 그대로 베끼지 말고 장면에 맞게 · '
            '추천/피할 조합과 리스크를 지킨다)\n' + '\n'.join(out))


ID_RE = re.compile(r'^[A-Z]{1,5}-?\d{2,3}$')


def audit(ids, kind):
    """산출 ids → (색인에 있는 번호, 지어낸 번호) — 번호 형식이 아닌 문자열은 버린다."""
    got = []
    for x in ids if isinstance(ids, list) else []:
        x = str(x).strip()
        if ID_RE.match(x) and x not in got:
            got.append(x)
    got = got[:8]
    ok = offered(kind)
    return [x for x in got if x in ok], [x for x in got if x not in ok]


if __name__ == '__main__':
    a = sys.argv[1:]
    if len(a) >= 2 and a[0] == 'index' and a[1] in SHELVES:
        print(index(a[1]))
        sys.exit(0)
    if len(a) >= 2 and a[0] == 'fetch' and a[1] in SHELVES:
        print(fetch(a[2:], a[1]))
        sys.exit(0)
    print(__doc__, file=sys.stderr)
    sys.exit(2)
