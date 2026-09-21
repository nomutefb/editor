#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""속보 판정 후처리 결정적 게이트 — 운영자 260917 «기준 타이트하게» · LLM 콜 0 · 정본 = 이 파일.

AI 판정(RUBRIC)이 O를 줘도 아래 3축은 **제목만으로** 기계 판정해 X로 내린다. RUBRIC 본문은 무접촉 —
루브릭 해시(RUBRIC_VER)가 바뀌면 48h 후보가 전건 재판정되고 회귀 도장이 깨지므로, 루브릭이 이미 명문화한
문턱을 코드가 집행하는 자리다(EXCLUDE 하드가드와 같은 층 · 판정 도장 무접촉 = 재급증 시 재판정 경로 불변).

실측 근거(260907~0917 속보 O 80건 · 채점판 정리): 해외 사고 19건 중 루브릭 문턱 충족 8건뿐(스위스 버스 5명·프랑스
열차 44명 부상은 루브릭 본문의 X 예시 그대로인데 O) · 연예 관계 소식 18건 · 사법 절차 후속 16건.

① 인명 문턱(casualty) — 재해·사고·군사행위 제목은 **명시된 확정 수**로만 통과.
   해외 = 사망≥10 ∨ 부상≥50 ∨ 실종≥150(각 독립 · 합산 금지) / 국내 = 사망≥3. 수 미상 = X.
   사형·테러·한국인 피해·전면전·지진(규모 규칙)·대인 강력범죄(피해자 수 축)·사법 어휘(③이 담당)는 이 축 밖.
   합산 표기(사망·실종자 N명)는 비둘기집으로 어느 한 문턱을 반드시 넘는 N(해외 210↑)만 통과.
② 연예 관계·지위(celeb) — 열애·결혼·결별·이혼·소속사 이동·입대·컴백·근황 = X.
   사망·사고·범죄 연루(입건·구속·음주·마약·폭행 …)·해체·은퇴는 통과(그쪽은 사건).
③ 사법 절차·판결(judicial) — 수사·영장·기소·구형·재판·1심/2심/항소심/상고·선고·판결·무죄·유죄·법정구속·확정 = **전부 X**
   (운영자 260921 «항소심 선고 이런 관련된거는 다 긴급 안오게» · 구판의 선고·판결 통과와 매체 몰림(cross≥8) 통과를 폐지).
   예외 2 = 사형(운영자 260831 «사형은 아무나 안때려» · 구형이어도 통과) · 탄핵(헌재 선고 = 정치 사태 축 · 사법 후속 아님).

되돌리기 = env BRK_GATES=0(전 축 OFF) · 축별 문턱은 env(아래). 사용 = gate_reason(title, cat, cross) → 사유 문자열 | None.
"""
import os
import re

GATES_ON = os.environ.get("BRK_GATES", "1").strip() != "0"
FOREIGN_DEAD = int(os.environ.get("BRK_GATE_FOREIGN_DEAD", "10"))
FOREIGN_INJ = int(os.environ.get("BRK_GATE_FOREIGN_INJ", "50"))
FOREIGN_MISS = int(os.environ.get("BRK_GATE_FOREIGN_MISS", "150"))
DOMESTIC_DEAD = int(os.environ.get("BRK_GATE_DOMESTIC_DEAD", "3"))

# ── ① 인명 문턱 어휘 ──────────────────────────────────────────────────────────────────────────
_ACCIDENT = re.compile(
    r"사고|화재|(?<![가-힣])불(?=[\s…·,.]|$)|불나|폭발|붕괴|추락|침몰|전복|탈선|충돌|매몰|산불|홍수|폭우|산사태|감전|중독|"
    r"누출|누설|누수|유출|정전|단수|땅꺼짐|싱크홀|참사|익사|질식|실종|"
    r"\bfire\b|crash|collapse|derail|capsiz|explosion|blast|\bsink|\bsank|flood|landslide|accident|wreck", re.I)
_MILITARY = re.compile(r"공습|폭격|포격|피격|교전|airstrike|air strike|shelling|bombard", re.I)
_SKIP = re.compile(
    r"사형|테러|terror|한국인|교민|재외국민|한국 ?기업|한국군|우리 국민|전면전|침공|선전포고|지진|earthquake|규모 ?\d|연락 ?두절|"
    r"살해|살인|피살|흉기|찔|난동|총격|총기|납치|인질|성폭|\bstab|\bshoot|gunman|murder|hostage|kidnap|femicide", re.I)
_VERDICT_WORDS = re.compile(r"선고|판결|무죄|유죄|금고|징역|법정 ?구속|구형|기소|재판|영장|송치|입건|수사|압수수색|공판|항소|상고|소송|고소|고발|배상|구속")

_EN_ONES = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
            "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17,
            "eighteen": 18, "nineteen": 19}
_EN_TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90}


def _en_num(s):
    s = (s or "").strip().lower().replace(",", "")
    if s.isdigit():
        return int(s)
    total, ok = 0, False
    for part in re.split(r"[-\s]+", s):
        if part in _EN_ONES:
            total += _EN_ONES[part]; ok = True
        elif part in _EN_TENS:
            total += _EN_TENS[part]; ok = True
        elif part == "hundred" and ok:
            total *= 100
        elif part in ("a", "and"):
            continue
        else:
            return None
    return total if ok else None


def _ko_num(n, unit):
    try:
        v = int(str(n).replace(",", ""))
    except ValueError:
        return None
    return v * {"천": 1000, "만": 10000}.get(unit or "", 1)


_KO_N = r"(\d[\d,]*)\s*(천|만)?\s*여?\s*명"
_P_DEAD = [re.compile(_KO_N + r"(?:이|의|이나|가)?\s*(?:이상\s*)?(?:넘게\s*)?(?:사망|숨|목숨|참변|희생)"),
           re.compile(r"(?:사망자|사망|희생자)(?:가|는|이|는)?\s*(?:최소\s*)?(?:현재\s*)?" + _KO_N)]
_P_INJ = [re.compile(_KO_N + r"(?:이|가)?\s*(?:이상\s*)?(?:부상|다쳐|다침)"),
          re.compile(r"부상(?:자)?(?:가|는|이)?\s*(?:최소\s*)?" + _KO_N)]
_P_MISS = [re.compile(_KO_N + r"(?:이|가)?\s*(?:이상\s*)?실종"),
           re.compile(r"실종(?:자)?(?:가|는|이)?\s*(?:추정\s*)?(?:최소\s*)?" + _KO_N)]
_P_COMB = [re.compile(r"(?:사망·실종자|사망·부상자|사상자|인명피해|인명 피해)(?:가|는|이)?\s*(?:최소\s*)?" + _KO_N)]
_EN_Q = r"(?:at least |over |more than |some |about |nearly )?([a-z]+(?:[-\s][a-z]+)?|\d[\d,]*)"
_P_DEAD_EN = [re.compile(r"\b" + _EN_Q + r"\s+(?:people\s+|residents\s+|passengers\s+)?(?:dead|killed|die|dies|died)\b", re.I),
              re.compile(r"\bkill(?:s|ed)?\s+(?:at least\s+)?(\d[\d,]*|[a-z]+(?:-[a-z]+)?)\b", re.I),
              re.compile(r"death toll\D{0,24}?(\d[\d,]*)", re.I)]
_P_INJ_EN = [re.compile(r"\b" + _EN_Q + r"\s+(?:people\s+)?(?:injured|hurt|wounded)\b", re.I)]
_P_MISS_EN = [re.compile(r"\b" + _EN_Q + r"\s+(?:people\s+)?missing\b", re.I)]


def _max_ko(pats, t):
    best = None
    for p in pats:
        for m in p.finditer(t):
            v = _ko_num(m.group(1), m.group(2))
            if v is not None and (best is None or v > best):
                best = v
    return best


def _max_en(pats, t):
    best = None
    for p in pats:
        for m in p.finditer(t):
            v = _en_num(m.group(1))
            if v is not None and (best is None or v > best):
                best = v
    return best


def _is_english(t):
    latin = len(re.findall(r"[A-Za-z]", t)); han = len(re.findall(r"[가-힣]", t))
    return latin > han * 2 and latin >= 8


def casualty_counts(title):
    """제목에 명시된 확정 (사망, 부상, 실종, 합산) — 없으면 None(수 미상). 심정지·이송·대피·매몰은 세지 않는다."""
    t = title or ""
    d = _max_ko(_P_DEAD, t); i = _max_ko(_P_INJ, t); m = _max_ko(_P_MISS, t); c = _max_ko(_P_COMB, t)
    de, ie, me = _max_en(_P_DEAD_EN, t), _max_en(_P_INJ_EN, t), _max_en(_P_MISS_EN, t)
    pick = lambda a, b: a if (b is None or (a is not None and a >= b)) else b
    return pick(d, de), pick(i, ie), pick(m, me), c


def casualty_gate(title, cat=None):
    t = title or ""
    if _SKIP.search(t) or _VERDICT_WORDS.search(t):
        return None
    mil = bool(_MILITARY.search(t))
    if not (mil or _ACCIDENT.search(t)):
        return None
    d, i, m, comb = casualty_counts(t)
    if (comb or 0) >= FOREIGN_DEAD + FOREIGN_INJ + FOREIGN_MISS:
        return None   # 합산 표기라도 비둘기집으로 어느 축이든 문턱을 넘는 규모(해외 210↑ · 국내는 당연) = 축 무관 통과
    foreign = mil or _is_english(t) or (cat or "") == "국제"
    if foreign:
        if (d or 0) >= FOREIGN_DEAD or (i or 0) >= FOREIGN_INJ or (m or 0) >= FOREIGN_MISS:
            return None
        return f"해외 인명 문턱 미달(사망 {d}·부상 {i}·실종 {m} / 기준 {FOREIGN_DEAD}·{FOREIGN_INJ}·{FOREIGN_MISS})"
    if (d or 0) >= DOMESTIC_DEAD:
        return None
    return f"국내 인명 문턱 미달(사망 {d} / 기준 {DOMESTIC_DEAD})"


# ── ② 연예 관계·지위 ──────────────────────────────────────────────────────────────────────────
_CELEB = re.compile(r"열애|결혼|결별|이혼|재혼|약혼|파혼|♥|혼인|예비신랑|예비신부|웨딩|상견례|재계약|전속계약|소속사|엔터(?:테인먼트)?와|"
                    r"입대|군대|제대|컴백|화보|근황|데이트|목격담|품절남|품절녀|득남|득녀|임신|출산")
_CELEB_KEEP = re.compile(r"사망|별세|숨|타계|부고|구속|입건|기소|체포|피소|송치|영장|사고|중상|의식불명|폭행|성폭|마약|음주|사기|협박|"
                         r"고소|수사|경찰|검찰|해체|은퇴|탈퇴|제명|사형|실종|피해|학대|살해")


def celeb_gate(title):
    t = title or ""
    if _CELEB.search(t) and not _CELEB_KEEP.search(t):
        return "연예 관계·지위 소식(열애·혼인·결별·소속·입대 = 콘텐츠 축)"
    return None


# ── ③ 사법 절차·판결 ──────────────────────────────────────────────────────────────────────────
# 운영자 260921 «항소심 선고 이런 관련된거는 다 긴급 안오게» — 절차(수사·영장·기소·구형)뿐 아니라 결과(선고·판결·
# 무죄·유죄·법정구속·확정)도 X. 매체가 몰려도 X(구판 cross≥8 통과 폐지 = 판결 보도는 원래 매체가 몰린다).
# 예외 = 사형(260831 별도 규칙) · 탄핵(헌재 선고 = 정치 사태). 킬스위치 = BRK_GATES=0(전 축).
_JUD = re.compile(r"구형|재판(?!매)|공판|(?<!특)수사|입건|송치|불송치|영장|기소|항소|상고|파기환송|대법원|헌재|증거|고소|고발|소송|압수수색|"
                  r"조사 ?착수|감사 ?착수|징계|선고|판결|무죄|유죄|법정 ?구속|실형|집행유예|징역|금고|벌금|형 ?확정|배상|"
                  r"1심|2심|3심|항소심|상고심")
_JUD_KEEP = re.compile(r"사형|탄핵")


def judicial_gate(title, cross=0):
    """cross 는 호출부 호환용(판정에 안 쓴다 · 매체 몰림 통과 폐지 260921)."""
    t = title or ""
    if _JUD_KEEP.search(t):
        return None
    if _JUD.search(t):
        return "사법 절차·판결(수사·기소·구형·선고·항소심·확정 = 긴급 축 밖 · 운영자 260921)"
    return None


def gate_reason(title, cat=None, cross=0):
    """속보 O를 X로 내려야 하면 사유, 아니면 None. 순서 = 인명 문턱 → 연예 → 사법."""
    if not GATES_ON:
        return None
    return casualty_gate(title, cat) or celeb_gate(title) or judicial_gate(title, cross)
