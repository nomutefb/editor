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
   누적·기간 집계는 문턱에 쓰지 않는다. 신규 피해와 함께 적히면 신규 수만 센다.
   사형·테러·한국인 피해·전면전·지진(규모 규칙)·대인 강력범죄(피해자 수 축)·사법 어휘(③이 담당)는 이 축 밖.
   합산 표기(사망·실종자 N명)는 비둘기집으로 어느 한 문턱을 반드시 넘는 N(해외 210↑)만 통과.
② 연예 관계·지위(celeb) — 열애·결혼·결별·이혼·소속사 이동·입대·컴백·근황 = X.
   사망·사고·범죄 연루(입건·구속·음주·마약·폭행 …)·폭력·폭로·활동 중단·하차·해체·은퇴는 통과(그쪽은 사건).
   메이저급 참조 명단(apps/news/major_award_winners.json) 인물의 관계·지위 소식이면 이 축을 건너뛴다 = 루브릭 🎤
   «메이저급 연예인 혼인·사건 예외»가 판정한다(운영자 260929 A2 · 코드가 루브릭 예외를 뒤집던 모순 해소).
③ 사법 절차·판결(judicial) — 수사·영장·기소·구형·재판·1심/2심/항소심/상고·선고·판결·무죄·유죄·법정구속·확정 = **전부 X**
   (운영자 260921 «항소심 선고 이런 관련된거는 다 긴급 안오게» · 구판의 선고·판결 통과와 매체 몰림(cross≥8) 통과를 폐지).
   예외 2 = 사형(운영자 260831 «사형은 아무나 안때려» · 구형이어도 통과) · 탄핵(헌재 선고 = 정치 사태 축 · 사법 후속 아님).

④ 확산 [강](lv.t≥3 · scraper/live_signal.py) + 연예·문화 인물(분류 문화·사회 ∨ 연예 직업어 ∨ 명단 인물 · 공직·체육 역할어 제외) = ② 관계·지위 축을
   명단 인물과 같게 열고(운영자 260929 A9 — 닛몰캐쉬 「데이트폭력 폭로」가 비메이저로 막히던 자리를 분포 증거로 푼다) ③은 **수사 단계**(고소·피소·고발·수사·
   입건·영장·송치·기소·재판에 넘겨짐·압수수색·조사 착수·증거인멸)만 연다(운영자 260929 «고소 수사도 열어» · 피의자인지는 루브릭 📡 가 가린다).
   재판 단계(구형·공판·선고·판결·항소심·확정 …)는 [강]이어도 그대로 X(운영자 260921 «항소심 선고 이런 관련된거는 다 긴급 안오게»). 판정 = 루브릭 📡 〔확산〕 규칙.
⑤ 유명인 본인 사망 = ① 인명 문턱 밖(운영자 260929 «사망자수는 불특정 다수일때만이야»). 사망어 ∧ 반응·주변인 문맥 아님 ∧ (명단 3자↑ 실명 ∨
   ([강] 연예 인물 ∨ 직업·직함어) ∧ 확정 사망 1명 이하)이면 ①을 건너뛰고 ③에서 수사 단계 어휘도 지운다(피살 1보의 「수사 착수」) —
   유명인 본인인지는 루브릭 👤 규칙으로 판정기가 가린다(게이트는 강등만 하는 층).

되돌리기 = env BRK_GATES=0(전 축 OFF) · 축별 문턱은 env(아래). 사용 = gate_reason(title, cat, cross, live) → 사유 문자열 | None.
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
# `(?<![촬수])영장` = 「촬영장」·「수영장」은 영장이 아니다(260929 · 「드라마 촬영장 화재 N명 사망」·「수영장 붕괴로 5명 사망」이 사법 어휘로 인명 문턱·연예 축을 비껴가던 오인 · 세 정규식 공통 · 평의회260929-2 #1).
_VERDICT_WORDS = re.compile(r"선고|판결|무죄|유죄|금고|징역|법정 ?구속|구형|기소|재판|(?<![촬수])영장|송치|입건|수사|압수수색|공판|항소|상고|소송|고소|고발|배상|구속")

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
_P_DEAD = [re.compile(_KO_N + r"(?:이|의|이나|가)?\s*(?:이상\s*)?(?:넘게\s*)?(?:추가로?\s*|새로\s*|더\s*)?(?:사망|숨|목숨|참변|희생)"),
           re.compile(r"(?:사망자|사망|희생자)(?:가|는|이|는)?\s*(?:최소\s*)?(?:현재\s*)?(?:누적\s*)?" + _KO_N +
                      r"(?!\s*(?:이|가)?\s*(?:이상\s*)?(?:부상|다쳐|다침|실종|중상|경상))")]   # 「5명 사망 12명 부상」의 「사망 12명」 = 부상 수(평의회260929-3 B#8)
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


# 숫자마다 집계 범위를 본다. 제목 전체를 누적 여부로 자르면 같은 제목의 신규 피해도 사라진다.
# '사망자 35명으로 늘어' / 'death toll rises to 35'는 단일 사고일 수 있어 그 표현만으로 제외하지 않는다.
_CUMULATIVE = re.compile(
    r"누적(?!\s*(?:강수|강우|적설|강설|\d[\d,.]*\s*(?:㎜|mm|㎝|cm)))|누계|통산|"
    r"(?:올해|금년|작년|지난해|금월|이달|이번\s*달|지난달|올여름|올겨울)(?!\s*첫)|올\s*들어|"
    r"(?:최근|지난)\s*(?:\d+|[한두세네])\s*(?:년|개월|달|주)(?:간|동안)?|\d+\s*(?:년간|개월간|주간)|"
    r"(?:개전|전쟁|내전|분쟁|발발|발생|시작|침공)(?:\s*(?:발발|시작))?\s*(?:이후|이래)|연간|월간|주간|"
    r"\b(?:cumulative|overall|so far|to date|this (?:year|month|week)|last (?:year|month)|"
    r"since\b|(?:over|in|during) the (?:past|last)\s+(?:\d+|\w+)\s+(?:years?|months?|weeks?))", re.I)
_CURRENT = re.compile(
    r"(?:오늘|방금|이번|추가|새로)(?!\s*(?:까지|누적|집계))|"
    r"\btoday\b|\b(?:new|latest|another)\s+(?:airstrike|attack|fire|crash|explosion|flood|collapse)\b", re.I)
_CLAUSE = re.compile(r"…+|\.{2,}|[;；!?。\n]|(?<!\d),(?!\d)|,(?=\s)|\s[—–]\s")


def _cumulative_count(t, match, mentions):
    """명시적 누적/기간 표현이 이 피해 수에 붙는가. 다른 절의 배경 누적 수는 전파하지 않는다."""
    start, end = match.span(1)
    left, right = 0, len(t)
    for boundary in _CLAUSE.finditer(t):
        if boundary.end() <= start:
            left = boundary.end()
        elif boundary.start() >= end:
            right = boundary.start()
            break
    # '올해 교통사고…100명 사망'처럼 피해 숫자 전에 붙은 기간 표제도 적용.
    # '누적 강수량 300㎜…12명 사망'은 별도 수치가 있으므로 사망 수로 전파하지 않는다.
    if left and not re.search(r"\d", t[:left]):
        left = 0
    before = t[left:match.end()]
    cues = list(_CUMULATIVE.finditer(before))
    if cues:
        # '누적 집계 오늘 100명 사망'의 오늘은 신규 사건이 아니다. 시간어만으로 누적을 해제하지 않는다.
        fresh = any(c.group() in ("추가", "새로") or _ACCIDENT.search(before[c.start():]) or
                    _MILITARY.search(before[c.start():]) for c in _CURRENT.finditer(before, cues[-1].end()))
        if not fresh:
            return True
    # 뒤에 붙은 집계 표현('100명 사망, 올해 누적'은 별도 절이므로 해당 없음).
    # '2명 사망해 누적 사망자 100명'의 누적은 뒤의 100명에만 붙는다.
    if not any(end <= other.start(1) < right for other in mentions):
        after = t[end:right]
        cue = _CUMULATIVE.search(after)
        if cue and cue.group() in ("누적", "누계", "통산") and re.search(_KO_N, after[cue.end():]):
            return False   # '12명 사망해 누적 100명': 뒤에서 생략된 사망 명사도 앞의 12명을 지우지 않는다.
        return bool(cue)
    return False


def _is_english(t):
    latin = len(re.findall(r"[A-Za-z]", t)); han = len(re.findall(r"[가-힣]", t))
    return latin > han * 2 and latin >= 8


def _casualty_counts(title):
    t = title or ""
    mentions = []
    for kind, ko, en in [(0, _P_DEAD, _P_DEAD_EN), (1, _P_INJ, _P_INJ_EN),
                         (2, _P_MISS, _P_MISS_EN), (3, _P_COMB, [])]:
        for pats, korean in [(ko, True), (en, False)]:
            for pattern in pats:
                for match in pattern.finditer(t):
                    value = _ko_num(match.group(1), match.group(2)) if korean else _en_num(match.group(1))
                    if value is not None:
                        mentions.append((kind, value, match))
    counts, excluded = [None] * 4, False
    matches = [m for _, _, m in mentions]
    for kind, value, match in mentions:
        if _cumulative_count(t, match, matches):
            excluded = True
        elif counts[kind] is None or value > counts[kind]:
            counts[kind] = value
    return tuple(counts), excluded


def casualty_counts(title):
    """누적·기간 집계를 뺀 확정 (사망, 부상, 실종, 합산). 미상은 None. 피해 종류는 합치지 않는다."""
    return _casualty_counts(title)[0]


def casualty_gate(title, cat=None, notable=False):
    """notable = 유명인 개인 사망일 수 있는 제목(gate_reason ⑤) = 문턱 밖(운영자 260929 · 판정기 👤 규칙이 가린다)."""
    t = title or ""
    if notable or _SKIP.search(t) or _VERDICT_WORDS.search(t):
        return None
    mil = bool(_MILITARY.search(t))
    (d, i, m, comb), cumulative = _casualty_counts(t)
    if not (mil or _ACCIDENT.search(t) or cumulative):
        return None
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
# `데이트(?!\s*폭)` = 데이트폭력·데이트 폭행은 연애 소식이 아니다(운영자 260929 A1 · 닛몰캐쉬 「데이트폭력·비하발언 폭로」가
#   `데이트` 에 걸려 **판정기가 YES 를 줘도 X 로 확정될 자리**였다 — 9/29 실제 X 는 판정기 NO[런 36514123616 「속보 0건」·게이트 X 줄 0]).
#   통과어 = 강력·성범죄 사건 명사만(평의회260929 #3 실측 — `폭로`·`하차`·`활동 중단` 은 「♥남편 반응 폭로」·「나란히 하차」 같은
#   가십을 명단과 무관하게 다시 열어 260917 타이트닝에 역행 → 제외 · `폭력` 은 조직폭력배·법률 상담 칼럼 오탐을 줄이려 앞뒤 경계).
_CELEB = re.compile(r"열애|결혼|결별|이혼|재혼|약혼|파혼|♥|혼인|예비신랑|예비신부|웨딩|상견례|재계약|전속계약|소속사|엔터(?:테인먼트)?와|"
                    r"입대|군대|제대|컴백|화보|근황|데이트(?!\s*폭)|목격담|품절남|품절녀|득남|득녀|임신|출산")
_CELEB_KEEP = re.compile(r"사망|별세|숨|타계|부고|구속|입건|기소|체포|(?<!에)피소(?!드)|송치|(?<![촬수])영장|사고|중상|의식불명|폭행|성폭|마약|음주|사기|협박|"
                         r"고소|수사|경찰|검찰|해체|은퇴|탈퇴|제명|사형|실종|피해|학대|살해|(?<!조직)폭력(?!배)|폭언|성추행|추행|불법촬영|스토킹|강간")

# 메이저급 참조 명단(breaking_judge ROSTER 와 같은 파일) — 명단 인물이면 ② 축을 건너뛰고 루브릭 🎤 메이저 예외에 맡긴다.
#   이름 일치(평의회260929 #4 실측 = 2자 이름 299개 대부분이 일반명사와 겹쳐 14일 524제목에 걸렸다 · 3자도 「서프라이즈⊃라이즈」):
#     · 3자↑ = 앞 글자가 한글·영문이 아닐 때만(낱말 중간 부분일치 차단)
#     · 2자 = **주어 자리**만 — 제목 첫 낱말이거나(조사 꼬리 허용) 바로 뒤가 `,`·`·`·`♥`·`&` 이거나 같은 제목에 그 사람의 그룹명이 있을 때
#     · 1자 = 제외(「비」 같은 이름은 제목 낱말과 구별 불가)
#   파일 없음·깨짐 = 빈 명단(종전 동작 = 전원 ② 축 적용) + ::warning::(조용한 엄격 모드 전환 금지 · 평의회 #6).
_ROSTER_P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "apps", "news", "major_award_winners.json")
_JOSA = set("이가은는을를의와과도만에서부터께랑님씨측")
_roster_cache = None


def _roster():
    """(3자↑ 이름 집합, 2자 이름 → 소속 그룹명 집합)."""
    global _roster_cache
    if _roster_cache is None:
        try:
            import json
            with open(_ROSTER_P, encoding="utf-8") as f:
                d = json.load(f)
            groups = d.get("idol_groups") or {}
            names = set(d.get("names") or []) | set(groups) | {m for ms in groups.values() for m in ms}
            names = {n.strip() for n in names if isinstance(n, str) and len(n.strip()) >= 2}
            grp_of = {}
            for g, ms in groups.items():
                for m in ms:
                    grp_of.setdefault(str(m).strip(), set()).add(str(g).strip())
            _roster_cache = (frozenset(n for n in names if len(n) >= 3),
                             {n: frozenset(grp_of.get(n, ())) for n in names if len(n) == 2})
        except Exception as e:  # noqa: BLE001
            import sys
            print(f"::warning::brk_gates 메이저급 명단 미도달({_ROSTER_P}) — 연예 ② 축을 명단 예외 없이 적용한다: {e}", file=sys.stderr)
            _roster_cache = (frozenset(), {})
    return _roster_cache


def _long_hit(n, t):
    i = t.find(n)
    while i >= 0:
        if i == 0 or not re.match(r"[가-힣A-Za-z]", t[i - 1]):
            return True
        i = t.find(n, i + 1)
    return False


def major_in(title):
    """제목에 메이저급 참조 명단 인물이 있으면 그 이름(없으면 None)."""
    t = title or ""
    longs, shorts = _roster()
    for n in longs:
        if _long_hit(n, t):
            return n
    toks = [(m.group(0), m.end()) for m in re.finditer(r"[가-힣A-Za-z0-9]+", t)]
    for idx, (w, end) in enumerate(toks):
        for n in ((w,) if w in shorts else ()) + tuple(w[:2] for _ in (0,) if len(w) > 2 and w[:2] in shorts and all(ch in _JOSA for ch in w[2:])):
            if idx == 0 or t[end:end + 1] in (",", "·", "♥", "&") or any(g and g in t for g in shorts[n]):
                return n
    return None


# 명단 인물이라도 건너뛰는 건 **루브릭 메이저 예외가 다루는 축**뿐 — 관계(열애·결혼·결별·이혼) · 지위(소속·전속계약·입대).
#   컴백·화보·근황·임신·출산·데이트 목격·♥ 표기만 있는 근황은 루브릭도 X 라 종전대로 여기서 X(260917 타이트닝 보존 ·
#   실측 14일 = 명단 인물 관문 X 192건 중 이 축 68건만 판정기로 넘어간다).
_MAJOR_AXIS = re.compile(r"열애|결별|이혼|파경|재혼|약혼|파혼|결혼|혼인|교제|품절|예비신|상견례|전속계약|재계약|소속사|입대|군대")   # 제대 = 복귀(활동 소식)라 비대상


_WHEN_REL = re.compile(r"(?:결혼|이혼|열애|입대|교제|전역|제대)\s*(?:\d+\s*(?:년|개월|주년|일)\s*(?:만에|째)|이후|후|뒤|앞두고|전)")


def celeb_gate(title, major=False):
    """major = 호출부가 이미 전국적 인지도를 확인한 건(확산 [강] · 260929) = 명단 인물과 같게 관계·지위 축만 연다(콘텐츠 축은 그대로 X)."""
    t = title or ""
    ax = _WHEN_REL.sub(" ", t)             # 「결혼 3년 만에 임신」·「입대 앞두고 콘서트」·「이혼 후 근황」 = 관계어가 시점 부사일 뿐 = 관계 축 아님(검증 V3)
    if _CELEB.search(t) and not _CELEB_KEEP.search(t) and not (_MAJOR_AXIS.search(ax) and (major or major_in(t))):
        return "연예 관계·지위 소식(열애·혼인·결별·소속·입대 = 콘텐츠 축)"
    return None


# ── ③ 사법 절차·판결 ──────────────────────────────────────────────────────────────────────────
# `증거` = 사법 절차어(인멸·조작·능력·불충분·채택)로만 — 낱말 하나면 폭로 1보(「«증거 있다»…녹취 공개」)·칼럼 제목을 사법으로 오인(평의회260929-2 V6) ·
#   `피소` = 🔎 목록 짝(「에피소드」 제외 · _CELEB_KEEP 같은 식).
# 운영자 260921 «항소심 선고 이런 관련된거는 다 긴급 안오게» — 절차(수사·영장·기소·구형)뿐 아니라 결과(선고·판결·
# 무죄·유죄·법정구속·확정)도 X. 매체가 몰려도 X(구판 cross≥8 통과 폐지 = 판결 보도는 원래 매체가 몰린다).
# 예외 = 사형(260831 별도 규칙) · 탄핵(헌재 선고 = 정치 사태). 킬스위치 = BRK_GATES=0(전 축).
_JUD = re.compile(r"구형|재판(?!매)|공판|(?<!특)수사|입건|송치|불송치|(?<![촬수])영장|기소|항소|상고|파기환송|대법원|헌재|증거 ?(?:인멸|조작|능력|불충분|채택)|"
                  r"고소(?![영득])|(?<!에)피소(?!드)|고발|소송|압수수색|"   # 고소영(배우)·고소득 ≠ 고소(평의회260929-3 A#9)
                  r"조사 ?착수|감사 ?착수|징계|선고|판결|무죄|유죄|법정 ?구속|실형|집행유예|징역|금고|벌금|형 ?확정|배상|"
                  r"1심|2심|3심|항소심|상고심")
_JUD_KEEP = re.compile(r"사형|탄핵")


# 수사 단계 어휘(운영자 260929 «고소 수사도 열어» — 연예·문화 인물 확산 [강] 한정) · 재판 단계(구형·공판·선고·판결·항소심·확정·소송 …)는 남긴다.
_JUD_EARLY = re.compile(r"고소(?![영득송])|(?<!에)피소(?!드)|고발|(?<!특)수사|입건|불?송치|(?<![촬수])(?:구속\s*)?영장|기소|재판에? ?넘겨|재판행|"
                        r"압수수색|조사 ?착수|증거 ?인멸")   # 「항고소송」의 소송은 남긴다 · 재판에 넘겨/재판행 = 기소(평의회260929-3 A#3·#4·G#1)


def judicial_gate(title, cross=0, early_ok=False):
    """cross 는 호출부 호환용(판정에 안 쓴다 · 매체 몰림 통과 폐지 260921). early_ok = 수사 단계 어휘를 지우고 본다(gate_reason ④)."""
    t = title or ""
    if early_ok:
        t = _JUD_EARLY.sub(" ", t)
    if _JUD_KEEP.search(t):
        return None
    if _JUD.search(t):
        return "사법 절차·판결(수사·기소·구형·선고·항소심·확정 = 긴급 축 밖 · 운영자 260921)"
    return None


def gate_reason(title, cat=None, cross=0, live=0):
    """속보 O를 X로 내려야 하면 사유, 아니면 None. 순서 = 인명 문턱 → 연예 → 사법.
    live = 확산 단계(scraper/live_signal.py lv.t) — [강](3↑)이면 연예·문화 인물(분류 문화 ∨ 연예 직업어 · 공직·체육 제외)의 ②연예 축을 명단 인물과 같게
    관계·지위만 열고 ③ 사법 축은 수사 단계만 연다(운영자 260929 A9 · «고소 수사도 열어» · 루브릭 📡 〔확산〕 규칙) — 재판 단계는 그대로(운영자 260921).
    ① 인명 문턱은 불특정 다수 피해에만 — 유명인 개인 사망 신호(⑤)면 건너뛴다(운영자 260929 · 루브릭 👤 규칙). 숫자 문턱 자체는 [강]이어도 그대로."""
    if not GATES_ON:
        return None
    t = title or ""
    live3 = (live or 0) >= 3
    # 연예·문화 인물 판별(평의회260929-3 A#1·#2·F#6·G#2) — 연예인 사법 기사는 분류기가 「사회」로 보내고(gate_judge 셀럽 범죄 = 사회 하드가드)
    #   체육 기사는 「문화」로 들어온다 → 분류 문화·사회 ∨ 연예 직업어 ∨ 명단 인물 · 공직·체육어가 있으면 제외(누가 연예인인지는 루브릭 📡 가 최종 판정).
    major = live3 and not _OFFICE.search(t) and (cat in ("문화", "사회") or bool(_ENT_HINT.search(t)) or bool(major_in(t)))
    dead = casualty_counts(t)[0]
    # ⑤ 유명인 **본인** 사망 신호 — 반응(애도·사과·방문)·주변인(가족·스태프·관객) 문맥이면 불특정 다수 사고로 본다(평의회260929-3 B#1·G#5 ·
    #   실측 「HL그룹 회장, 평택공장 사망사고 유족에 사과」가 풀리던 자리). 명단 3자↑ 실명 = 동반 사망 수와 무관 · [강] 연예 인물·직업·직함어 = 사망 1명 이하만.
    notable = bool(_DEATH.search(t)) and not _NOTABLE_CTX.search(t) and (
        _roster_long_hit(t) or ((major or bool(_NOTABLE.search(t))) and (dead is None or dead <= 1)))
    return casualty_gate(t, cat, notable=notable) or celeb_gate(t, major=major) or judicial_gate(t, cross, early_ok=major or notable)


# 확산 [강]의 ②·③ 완화 범위 = 연예·문화 인물만(루브릭 📡 「④ 간주는 연예·문화 인물만 · 정치인·공직자·기업인·운동선수 제외」와 같은 선 · 검증 V7 —
#   「손흥민 결혼」·「○○ 의원 결혼」이 [강]이면 결정적 X 가 풀리던 것) · 판별 = 분류 문화·사회 ∨ 연예 직업어 ∨ 명단 인물 · 공직·체육 역할어 = 제외.
_ENT_HINT = re.compile(r"유튜버|크리에이터|스트리머|인플루언서|\bBJ\b|배우(?!자)|가수(?!요)|아이돌|걸그룹|보이그룹|래퍼|개그맨|개그우먼|코미디언|방송인|예능|연예|아나운서|웹툰 ?작가")
_OFFICE = re.compile(r"장관|(?<!한)의원|대통령|총리|위원장|도지사|구청장|군수|여사|검찰총장|대법관|당선인|"
                     r"선수(?!단|촌)|(?<![가-힣])감독(?!원|관)|코치|국가대표|대표팀|투수|타자|포수|골키퍼|구단|KBO|MLB|K리그|EPL|NBA|UFC|올림픽")
#   `배우자`·`판사` 제거 = 「배우자 폭행 혐의」·「영장전담 판사」는 연예인 기사에도 나온다 · `감독` = 앞 글자 없을 때만(영화감독·금융감독원·관리감독 제외) ·
#   체육 역할어 추가 = 체육 기사가 분류 「문화」로 들어와 운동선수가 연예 완화를 받던 구멍(평의회260929-3 A#1·#5)
# ⑤ 유명인 개인 사망 신호(운영자 260929 «사망자수는 불특정 다수일때만이야») — 사망어 ∧ (확산 [강] ∨ 명단 인물 ∨ 직업·직함어).
#   게이트는 강등만 하는 층이라 넓게 잡아도 판정기(👤 규칙 = 전국적으로 이름이 알려진 **특정** 인물만 O)가 무명·불특정 다수를 X 로 가린다.
#   중상·의식불명 등 사망이 아닌 피해는 대상 밖(종전 ① 문턱) · `의원` = 병원·한의원·치과의원 제외.
#   확정 사망 2명↑이 명시된 제목 = 다수 피해 사고 = ① 그대로(「유튜버 ○○ 촬영장 화재로 스태프 2명 사망」이 [강]으로 문턱을 비껴가지 않게 ·
#   「배우 ○○ 등 2명 사망」류 동반 사망은 놓칠 수 있다 = 희소 · 판정기 대신 운영자 교정 축).
_DEATH = re.compile(r"사망|숨져|숨지|숨진|숨졌|별세|타계|서거|작고(?:한|했|하|(?=\s*(?:$|[…·,.!?\]\)'])))|영면|세상을? ?떠|숨을? ?거|요절|참변|사고사|추락사|익사|피살|순직|"
                    r"\bdie[sd]?\b|\bdead\b|\bkilled\b", re.I)
_NOTABLE = re.compile(r"유튜버|크리에이터|스트리머|인플루언서|\bBJ\b|배우(?![자러며던고는])|가수(?!요)|아이돌|걸그룹|보이그룹|래퍼|개그맨|개그우먼|코미디언|방송인|아나운서|"
                      r"(?<![A-Za-z])MC(?![A-Za-z])|\bDJ\b|프로듀서|셰프|작가|(?<![리융])감독(?!원|관|\s*(?:부실|소홀))|화백|명창|국가대표|선수(?!단|촌|금|\s*파손)|메달리스트|"
                      r"대통령(?!실|령)|총리|장관|(?<![병한치과])의원|(?<![람시연대])회장|총수|창업주|교수|거장|원로|향년|"
                      r"\b(?:actor|actress|singer|rapper|legend|former (?:president|prime minister))\b", re.I)
# 반응·주변인 문맥(평의회260929-3 B#1·G#5) — 이 말이 있으면 숨진 사람이 유명인 본인이 아닐 가능성이 크다 = ① 그대로(판정기 👤 ③과 같은 선).
_NOTABLE_CTX = re.compile(r"애도|조문|사과|위로|방문|희생자|사망자|속출|부친|모친|아버지|어머니|아내|남편|자녀|매니저|스태프|직원|관객|행인|운전자|근로자|노동자")


def _roster_long_hit(t):
    """⑤ 전용 명단 신호 = 3자↑ 실명만(2자는 「가을·수영·지연·청하(지명)」 같은 일반명사와 겹쳐 사망 문턱을 풀던 오탐 · 평의회260929-3 B#4·E#1)."""
    longs, _ = _roster()
    for n in longs:
        for m in re.finditer(re.escape(n), t):
            i, j = m.start(), m.end()
            left_ok = i == 0 or not re.match(r"[가-힣A-Za-z]", t[i - 1])
            right_ok = j >= len(t) or not re.match(r"[가-힣A-Za-z]", t[j]) or t[j] in _JOSA   # 「브라이언트」 ⊅ 브라이언 · 조사 꼬리 허용
            if left_ok and right_ok:
                return True
    return False   # 향년 = 부고 표기(특정 개인)

