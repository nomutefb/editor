# -*- coding: utf-8 -*-
"""민감어 마스킹 — 산출물에 그려지는 글자만 가린다(운영자 260831 «썸네일 제작에서 자살 이라는 걸 쓰면 *살 이라고 자동으로 필터링»).

거처가 `shared/` = 썸네일(thumb-make)·카드뉴스(comp-make) **두 레인 공용**(둘 다 sparse 목록에 shared 보유).
썸네일 절대규칙1(코드 4파일 불변) 밖 신규 헬퍼 = `quote_indent.py` 선례 그대로 — 4파일은 import·런타임 치환만.

⚠ **자리가 계약 = 강조 파싱 *이후***.
   `nomute_overlay.parse()`는 별표 1~2개를 강조 델리미터로 읽는다(3+만 리터럴) → 파싱 전에 「자살」을
   「*살」로 바꾸면 그 별표가 강조를 열어 **별표는 안 그려지고 뒤 글자가 통째로 초록**이 된다
   (실측 `parse('*살 예방')` → `[('h','살 예방')]`). 그래서 치환은 파서가 세그먼트를 다 가른
   뒤에 세그먼트 **본문**에만 건다 = 별표가 마크업이 아니라 글자로 남는 유일한 자리.

⚠ 폭·자간 축은 **원문 기준 그대로 둔다**(sweep `_plain`·뷰어 힌트 무접촉). 마스킹은 글자 수를
   줄이므로(자살 3자 → *살 2자) 원문 기준 sweep은 항상 같거나 더 보수적 = 마진 초과가 새로 생길 수
   없다. 두 축을 같이 건드리면 뷰어 힌트·게이트·러너가 서로 다른 글자의 폭을 재게 된다(260807 6차 사고축).

⚠ 발사 페이로드(`_src.json`)는 **원문 보존** = 「수정」 복원이 원문으로 열린다(다시 편집 가능).
"""

# 마스킹 표 — 화면·산출물에 그려질 때만 적용. ⚠ 뷰어 사본 `viewer/thumb.html` SENS_MASK와 한 쌍(게이트 check_sens_mask가 동기 강제).
MASK_PAIRS = [('자살', '*살')]


def mask(s):
    """문자열 1개 마스킹(리터럴 치환 · 멱등 = 결과에 원어가 안 남는다)."""
    out = '' if s is None else str(s)
    for a, b in MASK_PAIRS:
        out = out.replace(a, b)
    return out


def wrap_parse(parse):
    """`nomute_overlay.parse` / `card_news.parse_segments` 래퍼 — 세그먼트 본문에만 마스킹(강조 구분 무손상).

    반환 함수는 원 파서와 시그니처·구조가 같아 호출측 코드는 한 줄도 안 바뀐다.
    ⚠ 멱등이라 이중 래핑돼도 결과 동일(모듈 재import·맥 잡워커 재실행 안전).
    """
    def _parse(t):
        return [(st, mask(stx)) for st, stx in parse(t)]
    return _parse
