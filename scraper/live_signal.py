#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 살아있는 확산 신호(lv) — 기사 **밖** 모집단 신호로 「그 이름을 지금 전국이 쓰고 찾는가」를 잰다.
# (운영자 260929 «닛몰캐쉬 같은 기사가 원체 빨리 들어오고 긴급으로 뜰 수 있는지» · 명성(메이저급) 대신 분포 증거 = A4/A5)
#
# 왜: 판정기 입력은 제목 한 줄뿐이라 「이 사람이 전국구인가」를 모델 기억(명단·수상 이력)으로만 풀었다. 9/29 닛몰캐쉬 =
#   커뮤니티 07:15 → tbs 4곳 실명 09:37 → X 트렌드 09:37 → 구글뉴스 3매체 10:21 → 우리 피드 10:34(익명 제목) →
#   판정 NO 11:16·11:46(비메이저 🎤 규칙) → 운영자 손 제작 11:59. 후보가 생긴 뒤 파이프는 빠르다(후보→푸시 ≈1분).
#   늦은 건 「이게 큰 이름인가」를 증명할 수단이 판정기에 없었기 때문이다 → 사람들이 실제로 그 이름을 쓰는 흔적을 잰다.
#
# 갈래(family · 서로 독립인 모집단) — 같은 원천은 한 갈래로 센다:
#   C = 커뮤니티(tbs_data 21곳 스냅샷에서 같은 이름이 **3곳↑** · 또는 커뮤니티 레인 social_candidates source_count≥3 · 둘은 같은 원천 = 1갈래)
#   X = X 실시간 트렌드 상위 15 · G = 구글 급상승 상위 10 · N = 나무위키 검색 순위(폰 레인 · namu_updated 90분 넘으면 무시)
#   ⚠ 시그널 실검은 뺀다(백테스트 = 뉴스보다 늦게 뜨는 후행 지표 · leadlag 7일).
# 단계(tier) — 판정 꼬리표 〔확산 강|중|약〕의 원천:
#   t1 = 한 갈래(참고) · t2 = 서로 다른 갈래 2개가 6시간 안에 동시(armed) · t3 = t2 + 언론 확인(novel):
#        ⓐ 구글 뉴스 검색에서 그 이름 제목을 6시간 안에 낸 매체 3곳↑ ⓑ 우리 수집함 매칭 후보 cross≥3
#        novel = 무장(armed) 3시간 전보다 이른 보도가 24시간 안에 없어야(묵은 사건의 재점화 = 속보 아님).
#   ⚠ 한 갈래만으로는 절대 t2 이상이 안 된다(커뮤니티 단일 신호 정밀도 = 단일 원천 잡음 90%↑ · 백테스트 실측).
#   ⚠ 만성어(지난 72h tbs 스냅샷의 15%↑에서 2곳↑에 뜬 말 · 최근 6h 제외)는 C 갈래로 안 센다(늘 떠 있는 말 = 사건 아님).
# 실측(9/22~9/29 백테스트 · scratch leadlag) = 고확신(t3) ≈0.4건/일 · 닛몰캐쉬 armed 09:37 → t3 10:21~10:31(구글뉴스).
#
# 상태 = scraper/obs/live_state.json(작게 · 72h 넘은 것 정리) — 갈래별 최초·최근 관측 · 만성어 계수(tbs 스냅샷을 `updated`로
#   세어 같은 스냅샷 재독 중복 0) · 무장 시각 · 구글뉴스 확인 캐시(10분) · 씨앗(seed) 장부.
# 순수 함수 원칙 = 네트워크는 gn_poll(명시 확인 함수) 하나뿐 · 나머지는 입력 dict → 출력 dict(테스트 = 픽스처만).
# 소비 = scraper/live_seed.py(후보 첨부·입장·씨앗) → .github/scripts/breaking_judge.py(꼬리표·도장) · brk_gates · push_send.
# 롤백 = env LIVE_SIGNAL=0(첨부·입장·씨앗 전부 멈춤 · 이미 붙은 lv 는 그대로 = 도장 폭풍 0).
import json
import os
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TBS = ROOT / "viewer" / "tbs_data.json"
SOCIAL = ROOT / "viewer" / "social_candidates.json"
SNS = ROOT / "viewer" / "sns_trends.json"
STATE = ROOT / "scraper" / "obs" / "live_state.json"
KST = timezone(timedelta(hours=9))

ON = os.environ.get("LIVE_SIGNAL", "1").strip().lower() not in ("0", "false", "no", "off")
PAIR_H = 6              # 두 갈래 「동시」 창(h)
COMM_MIN = 3            # C 갈래 = 같은 tbs 스냅샷 3곳↑ 또는 커뮤니티 레인 source_count≥3
X_TOP, G_TOP, N_TOP = 15, 10, 10
SNAP_MAX_MIN = 90       # tbs·트렌드·나무위키 스냅샷이 이보다 오래되면 이번 회차 관측 없음(정체 스냅샷이 신호를 끝없이 연장하는 것 차단)
CHRONIC_H, CHRONIC_SKIP_H, CHRONIC_RATIO, CHRONIC_MIN_SNAP = 72, 6, 0.15, 12
NOVEL_H, NOVEL_BACK_H = 3, 24
GN_MIN, GN_WIN_H, GN_TTL_S = 3, 6, 600
GN_MAX_Q = int(os.environ.get("LIVE_GN_MAX_Q", "6"))    # 회차당 구글뉴스 검색 상한(예의 · 차단 회피)
GN_PAUSE_S = 1.0
IDLE_H = 12             # 모든 갈래가 이만큼 조용하면 에피소드 종료(다음에 다시 뜨면 새 사건)
STRONG_KEEP_H = 24      # 확인 뒤 [강] 유지 창 — 그 뒤 새 첨부는 [중](이미 붙은 [강]은 엔트리에 동결 = live_seed)
KEEP_H = 72             # 상태 보관
TIER_STRONG = 3         # 확산 [강] = breaking_judge·brk_gates·push_send·뷰어 isBreaking 이 읽는 단계(값 사본 = 3 고정)
FAM = "CXGN"

# ── 불용어 = 수집 정본 STOPWORDS + 소셜 레인 _STOP + 일반 명사(직업·지명·수식어) — 이름이 아닌 말이 갈래를 만들지 않게 ──
_GENERIC = set("""
유튜버 연예인 배우 가수 아이돌 그룹 멤버 방송인 개그맨 개그우먼 인플루언서 크리에이터 스트리머 bj 래퍼 모델 감독 작가 아나운서 선수 코치 교수
논란 폭로 근황 현재 오늘 어제 내일 지금 방금 요즘 오늘자 최근 당시 올해 작년 내년 지난해 이번 다음 하루 첫날 당일 연휴 추석 설날
한국 일본 미국 중국 북한 러시아 대한민국 서울 부산 대구 인천 광주 대전 울산 경기 국내 해외 세계 전국 현지 외국인 한국인 일본인 중국인
대통령 정부 국회 여당 야당 국힘 민주당 경찰 검찰 법원 의원 장관 총리 청와대 대통령실
뉴스 기사 기자 영상 사진 방송 채널 유튜브 인스타 인스타그램 틱톡 트위터 네이버 카카오 구글 커뮤니티 게시판 게시글 댓글 네티즌 누리꾼 팬들 대중 sns
사람 사람들 남자 여자 여성 남성 아내 남편 엄마 아빠 아들 딸 부모 아버지 어머니 가족 친구 동생 누나 언니 오빠 형 할머니 할아버지 아이 아기 학생 직장인 회사 사장 손님
전여친 여친 남친 전남친 전남편 전처 결혼 이혼 열애 결별 임신 출산 사망 별세 사고 사건 의혹 해명 사과 입장 공개 발표 공식 역대 최초 최고 최대 기록
난리 난리남 대박 진짜 레전드 충격 경악 논란중 역대급 근데 그냥 우리 이거 저거 그거 이게 무슨 어떤 누가 왜 뭐 어느
이유 방법 생각 느낌 상황 모습 반응 후기 정리 요약 등장 시작 결국 드디어 다시 계속 처음 마지막 수준 정도 소식 화제 인기 실시간 속보 단독
녹취록 녹취 폭언 폭행 폭력 데이트폭력 비하 발언 저격 갑질 학폭 마약 음주운전 성범죄 협박 사기 고소 고발 수사 입건 구속 기소 재판 선고
컴백 데뷔 앨범 신곡 드라마 영화 예능 출연 공연 콘서트 활동 중단 은퇴 하차 탈퇴 계약 소속사 전속계약
해지 종료 확정 예고 시즌 첫방 개봉 관객 돌파 흥행 이슈 심경 고백 눈물 오열 분노 극찬 연예계 팬 구독자 계정 상대 동료 후배 선배
경기 회장 대표 농구 야구 축구 삼성 kt skt lg 과거 향후 유명 정체 결과 올해 금메달 은메달 동메달 메달 대표팀 아시안게임 올림픽 월드컵
가장 때문에 보고 안되 다들 정말 먼저 실제 올린 대한 하면 얼마나 마음 마음에 사는 살기 사라진 밝혀진 충격적인 없애야 인생 기분 나이 순위
실력 새벽 세대 동네 명절 단축 은행 부동산 라면 지하철 여배우 여직원 참교육 제주 ai mz vs
너무 제일 완전 그리고 그래서 하지만 이제 아직 벌써 이런 저런 그런 이렇게 저렇게 그렇게 어떻게 제발 진심 역시 혹시 과연
때문 많이 문제 하나 사유 난리난 일침 개인정보 유포 사생활 스토킹 영구정지 게임 만화 아파트 신입사원
공식입장 추가 확산 직접 사실 인정 부인 반박 사실무근 법적 대응 자숙 퇴출 폐쇄 삭제 비공개 파혼 재혼 득남 득녀 모친상 부친상 비보 발인
발매 첫방 예매율 관객수 연속 인터뷰 포토 온라인 성추행 명예훼손 허위사실 악플 루머 가짜뉴스 합성 딥페이크 서울시 인천시 대구시 부산시 경기도
jpg jpeg gif png mp4 webp ㄷㄷ ㄷㄷㄷ ㅋㅋ ㅋㅋㅋ ㅎㄷㄷ
""".split())
# 제목에서 뽑는 토큰만 거르는 동사·형용사 꼬리(백테스트 ents.VERBISH 계승) — 트렌드 검색어(이미 이름)는 이 필터 밖.
_VERBISH = re.compile(r"(다|해|게|고|며|서|냐|요|네|데|까|면|도|만|된|할|던|을|를|께|지만|는데|아냐|했|됐|위해|출신|최다|강력|정상|받아|"
                      r"없이|연애|발견|끝내|앞에서|싶은데|축하|노답|완패|결혼식|새신랑|활짝|전국민|최강|추격|판도|적인|스러운|(?<=..)하)$")
try:
    from knews_scraper import STOPWORDS as _KSTOP   # 수집 정본(클러스터 정형구 포함)
except Exception:  # noqa: BLE001
    _KSTOP = set()
try:
    from social_burst import _STOP as _SSTOP        # 소셜 레인 chatter(추가·폭로·근황 …)
except Exception:  # noqa: BLE001
    _SSTOP = set()
STOP = frozenset({w.lower() for w in (set(_KSTOP) | set(_SSTOP) | _GENERIC)})

_JOSA = ("에서는", "에게서", "으로부터", "으로는", "이라는", "라는", "에서", "에게", "으로", "까지", "부터", "마저", "조차", "처럼",
         "보다", "이랑", "하고", "과의", "와의", "이의", "의", "은", "는", "이", "가", "을", "를", "에", "도", "와", "과", "로", "만", "측", "씨")
_JOSA1 = set("이가은는을를의와과도만에서부터께랑님씨측")   # 조사 꼬리 글자 = .github/scripts/trend_watch._JOSA 사본(kw_hit 의미 동일)
_BAD_END = re.compile(r"(하는|하던|했던|하게|하고|해서|했다|한다|된다|됐다|되는|되던|이는|이던|스러운|같은|없는|있는|많은|좋은|나는|가는|오는|"
                      r"보는|먹는|싶은|받은|당한|입은|터진|터짐|했음|했네|하네|인데|는데|라는|이라|이다|합니다|해요|했어|같음|없음|있음|ㄷㄷ|ㅋㅋ)$")
_WORD = re.compile(r"[가-힣]{2,}|[A-Za-z][A-Za-z0-9]+")
_ANYW = re.compile(r"[가-힣A-Za-z0-9]+")


def norm_key(s):
    """키 정규화 = 소문자 · #·_·공백·기호 제거(「닛몰 캐쉬」·「#닛몰캐쉬」 = 「닛몰캐쉬」)."""
    return re.sub(r"[^0-9a-z가-힣]", "", str(s or "").lower())


def disp(s):
    """표시형 = #·_ 를 공백으로 · 공백 정리(트렌드 해시태그 대비)."""
    return re.sub(r"\s+", " ", re.sub(r"[#_]", " ", str(s or ""))).strip()


def _strip_josa(w):
    if re.fullmatch(r"[가-힣]{3,}", w):
        for j in _JOSA:
            if w.endswith(j) and len(w) - len(j) >= 2:
                return w[: -len(j)]
    return w


def _key_ok(k):
    """키 기본 자격(트렌드 검색어 포함) = 2자↑ · 불용어·숫자 아님."""
    return bool(k) and len(k) >= 2 and k not in STOP and not k.isdigit() and not re.fullmatch(r"[0-9]+[가-힣]?", k)


def _name_ok(k):
    """제목 토큰 자격 = 기본 + 동사·형용사 꼬리 아님 + 영문은 3자↑(AI·MZ·VS 같은 두 글자 약어 = 이름 아님)."""
    return _key_ok(k) and not _BAD_END.search(k) and not _VERBISH.search(k) \
        and not (k.isascii() and len(k) < 3)


def tokens(title):
    """제목 → 후보 이름 토큰(소문자) — 2자↑ 한글·영문 낱말 · 조사 꼬리 제거형 · 불용어·동사형 제외 ·
    띄어 쓴 이름(「닛몰 캐쉬」) = 붙인 형도 후보. 한 글자 조사를 뗀 경우만 원형도 함께 낸다(「김고은」→「김고」 오절단 보완 ·
    둘 중 무엇을 남길지는 observe 가 낱말 그대로 쓰인 횟수로 고른다)."""
    t = re.sub(r"\[[^\]]*\]", " ", str(title or ""))
    raw = _WORD.findall(t)
    out = set()
    for w in raw:
        lw = w.lower()
        if len(lw) >= 3 and lw[-1] in "인적하" and lw[:-1] in STOP:
            continue              # 「논란인」·「일침하」 = 불용어 + 서술 꼬리
        s = _strip_josa(lw)
        if s != lw:
            if s in STOP:
                continue          # 「유튜버가」 = 불용어 + 조사 → 원형도 버린다
            if _name_ok(s):
                out.add(s)
            if lw[len(s):] not in ("은", "이", "도"):
                continue          # 이름 끝 글자와 겹칠 수 있는 조사(김고은·재이·이도)만 원형을 함께 낸다 — 나머지(에서·으로·로 …) = 원형 버림
        if _name_ok(lw):
            out.add(lw)
    for a, b in zip(raw, raw[1:]):   # 띄어 쓴 이름 붙이기(「닛몰 캐쉬」 = 두 글자 + 두 글자 한글만 · 긴 낱말끼리 붙이면 「게임영구정지」류 잡음)
        if re.fullmatch(r"[가-힣]{2}", a) and re.fullmatch(r"[가-힣]{2}", b) and a not in STOP and b not in STOP:
            k = a + b
            if _name_ok(k):
                out.add(k)
    return out


def _contains_ok(k):
    """다른 이름 안에 들어 있음으로 같은 이름이라 볼 자격 = 3자↑ 이름꼴(「시험 보고」의 「보고」·「sl vs nep」의 「vs」 = 우연 일치 차단)."""
    return len(k) >= 3 and _name_ok(k)


def hit(key, text):
    """이름 key 가 text 에 있는가 — .github/scripts/trend_watch.kw_hit 의미 사본(4자↑ = 포함 · 2~3자 = 낱말 일치 또는 조사 꼬리 ≤2자).
    key 는 정규화형(공백 없음) · text 쪽 공백은 무시(「닛몰 캐쉬」도 4자↑ 포함으로 잡힌다)."""
    k = norm_key(key)
    if len(k) < 2:
        return False
    t = str(text or "").lower()
    if len(k) >= 4:
        return k in norm_key(t)
    for w in _ANYW.findall(t):
        if w == k or (len(w) <= len(k) + 2 and w.startswith(k) and all(ch in _JOSA1 for ch in w[len(k):])):
            return True
    return False


def prep(text):
    """hit 반복 대조용 전처리 = (붙인 본문, 낱말 바탕형 집합) — 같은 제목을 이름 수만큼 다시 쪼개지 않게(live_seed 매칭)."""
    t = str(text or "").lower()
    bases = set()
    for w in _ANYW.findall(t):
        bases.add(w)
        for n in (1, 2):
            if len(w) - n >= 2 and all(ch in _JOSA1 for ch in w[-n:]):
                bases.add(w[:-n])
    return norm_key(t), bases


def hitp(k, p):
    """hit 과 같은 판정 — k = norm_key 끝난 이름 · p = prep(text)."""
    if len(k) < 2:
        return False
    return k in p[0] if len(k) >= 4 else k in p[1]


class _Corpus:
    """커뮤니티별 제목 묶음 — 키 적중 계수를 빠르게(4자↑ = 붙인 본문 포함 · 2~3자 = 낱말 바탕형 집합)."""

    def __init__(self, groups):
        self.g = []
        for gid, titles in groups:
            text = "\x00".join(norm_key(t) for t in titles)   # 제목 경계 유지(앞 제목 꼬리 + 뒤 제목 머리 우연 일치 차단)
            bases = set()
            for ti in titles:
                for w in _ANYW.findall(str(ti or "").lower()):
                    bases.add(w)
                    for n in (1, 2):
                        if len(w) - n >= 2 and all(ch in _JOSA1 for ch in w[-n:]):
                            bases.add(w[:-n])
            self.g.append((gid, text, bases))

    def count(self, key):
        k = norm_key(key)
        if len(k) < 2:
            return 0
        if len(k) >= 4:
            return sum(1 for _, text, _ in self.g if k in text)
        return sum(1 for _, _, b in self.g if k in b)


def _ts(s):
    """ISO·「YYYY-MM-DD HH:MM」(KST) → epoch 초. 실패 = None."""
    s = str(s or "").strip()
    if not s:
        return None
    for f in (None, "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            t = datetime.fromisoformat(s.replace("Z", "+00:00")) if f is None else datetime.strptime(s, f)
        except ValueError:
            continue
        if t.tzinfo is None:
            t = t.replace(tzinfo=KST)
        return t.timestamp()
    return None


def iso(ep):
    return datetime.fromtimestamp(ep, KST).strftime("%Y-%m-%dT%H:%M:%S%z") if ep else ""


def _jload(p, d):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return d


def load_snapshots(root=None):
    """라이브 스냅샷 3종(없거나 깨지면 빈 값 = fail-soft)."""
    r = Path(root) if root else ROOT
    return {"tbs": _jload(r / "viewer" / "tbs_data.json", {}), "social": _jload(r / "viewer" / "social_candidates.json", []),
            "sns": _jload(r / "viewer" / "sns_trends.json", {})}


def _vol(g):
    v = g.get("vol")
    if isinstance(v, (int, float)) and v > 0:
        return int(v)
    m = re.match(r"\s*([\d,]+)", str(g.get("traffic") or ""))
    return int(m.group(1).replace(",", "")) if m else 0


def observe(snap, now):
    """스냅샷 → 이번 회차 관측 {key: {"d": 표시형, "C": 곳수, "S": source_count, "X": 순위, "G": (순위, 검색량), "N": 순위}}
    + 메타(tbs 스냅샷 시각·신선 여부 · 2곳↑ 키 목록 = 만성어 계수 원료). 네트워크·파일 0."""
    tbs = snap.get("tbs") if isinstance(snap.get("tbs"), dict) else {}
    sns = snap.get("sns") if isinstance(snap.get("sns"), dict) else {}
    soc = snap.get("social") if isinstance(snap.get("social"), list) else []
    t_tbs = _ts(tbs.get("updated"))
    t_sns = _ts(sns.get("updated"))
    t_nm = _ts(sns.get("namu_updated"))
    fresh = lambda t: t is not None and -600 <= now - t <= SNAP_MAX_MIN * 60   # noqa: E731
    groups = []
    for cm in tbs.get("communities") or []:
        if isinstance(cm, dict):
            groups.append((str(cm.get("id") or cm.get("name") or len(groups)),
                           [str(p.get("title") or "") for p in (cm.get("posts") or []) if isinstance(p, dict)]))
    corp = _Corpus(groups)
    obs, dmap = {}, {}

    def put(k, d, f, v):
        if not _key_ok(k):
            return
        e = obs.setdefault(k, {})
        dmap.setdefault(k, d)
        if f == "X" or f == "N":
            e[f] = min(e.get(f, 99), v)
        elif f == "G":
            e[f] = max(e.get(f, (0, 0)), v, key=lambda z: (z[1], -z[0]))
        else:
            e[f] = max(e.get(f, 0), v)

    # ① tbs 토큰 → 곳수(2곳↑만 = 만성어 원료 · 3곳↑ = C 갈래) — 토큰이 2곳↑에 나온 것만 적중 계수(속도)
    tg, exact = {}, {}
    for gi, (_, titles) in enumerate(groups):
        for ti in titles:
            for k in tokens(ti):
                tg.setdefault(k, set()).add(gi)
            for w in _WORD.findall(re.sub(r"\[[^\]]*\]", " ", ti)):
                exact[w.lower()] = exact.get(w.lower(), 0) + 1
    hi = []
    for k, gs in tg.items():
        if len(gs) < 2:
            continue
        n = corp.count(k)
        if n >= 2:
            hi.append(k)
            put(k, k, "C", n)
    # 조사 한 글자 차이 짝(「닛몰캐쉬」↔「닛몰캐쉬가」 · 「김고」↔「김고은」) = 한 이름 — 낱말 그대로 더 많이 쓰인 쪽만 남긴다
    for k in sorted(list(obs), key=len, reverse=True):
        if k not in obs or len(k) < 3 or k[-1] not in _JOSA1:
            continue
        s = k[:-1]
        if s in obs:
            keep, drop = (k, s) if exact.get(k, 0) > exact.get(s, 0) else (s, k)
            for f, v in obs[drop].items():
                put(keep, keep, f, v)
            obs.pop(drop, None)
            hi = [x for x in hi if x != drop]
            if keep not in hi:
                hi.append(keep)
    # ② 커뮤니티 레인(source_count≥3 항목 제목의 토큰)
    soc3 = [x for x in soc if isinstance(x, dict) and (x.get("source_count") or 0) >= COMM_MIN]
    for x in soc3:
        for k in tokens(x.get("title")):
            put(k, k, "S", int(x.get("source_count") or 0))
    # ③ 트렌드(표시 상위만 = 화면과 같은 구간)
    trends = []
    if fresh(t_sns):
        for i, g in enumerate((sns.get("gtrends") or [])[:G_TOP]):
            if isinstance(g, dict) and g.get("query"):
                trends.append(("G", g["query"], (i + 1, _vol(g))))
        for i, g in enumerate((sns.get("xtrends") or [])[:X_TOP]):
            if isinstance(g, dict) and g.get("query"):
                trends.append(("X", g["query"], i + 1))
    if fresh(t_nm):
        for i, g in enumerate((sns.get("namu") or [])[:N_TOP]):
            if isinstance(g, dict) and g.get("query"):
                trends.append(("N", g["query"], int(g.get("rank") or i + 1)))
    # 일반어 조합 검색어(「법적 대응」·「추석 연휴」 = 낱말 전부 불용어) = 이름 아님 — 리플레이 실측 오발 봉합
    trends = [(f, q, v) for f, q, v in trends
              if not all(w in STOP or _strip_josa(w) in STOP for w in disp(q).lower().split())]
    tkeys = [(f, norm_key(q), disp(q), v) for f, q, v in trends]
    for f, k, d, v in tkeys:
        put(k, d, f, v)
        c = corp.count(k)          # 트렌드 이름 자체의 커뮤니티 곳수(여러 낱말 검색어 = 붙인 형 포함)
        if c >= 2:
            put(k, d, "C", c)
            if k not in hi:
                hi.append(k)
        s = max((int(x.get("source_count") or 0) for x in soc3 if hit(k, x.get("title"))), default=0)
        if s:
            put(k, d, "S", s)
    # ④ 갈래 통합 — 이름이 트렌드 검색어 안에 있거나(「닛몰캐쉬」 ⊂ 「닛몰캐쉬 데이트폭력」) 그 반대면 같은 이름
    for k in list(obs):
        kd = dmap.get(k, k)
        for f, qk, qd, v in tkeys:
            if qk != k and ((_contains_ok(k) and hit(k, qd)) or (_contains_ok(qk) and hit(qk, kd))):
                put(k, kd, f, v)
    for k, e in obs.items():
        e["d"] = dmap.get(k, k)
    return obs, {"t_tbs": t_tbs, "tbs_fresh": fresh(t_tbs), "t_sns": t_sns, "sns_fresh": fresh(t_sns),
                 "t_nm": t_nm, "hi": sorted(hi)}


def new_state():
    # tb = {6시간 칸(epoch//21600): 그 칸 tbs 스냅샷 수} · tl = 최근 스냅샷 id(분 · 재독 중복 차단) · hi = {이름: {칸: 2곳↑였던 스냅샷 수}}
    # (분 단위 목록이면 72h 에 220KB · 시 단위 136KB · 6시간 칸 ≈47KB = 리플레이 실측 · 만성 판정은 칸 단위 근사로 충분)
    return {"v": 1, "tb": {}, "tl": [], "hi": {}, "k": {}, "gn": {}, "sd": {}}


def load_state(p=None):
    s = _jload(p or STATE, None)
    if not isinstance(s, dict) or s.get("v") != 1 or not isinstance(s.get("tb"), dict):
        return new_state()
    for k, d in new_state().items():
        s.setdefault(k, d)
    return s


def save_state(st, p=None):
    p = Path(p or STATE)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(st, ensure_ascii=False, separators=(",", ":"), sort_keys=True), encoding="utf-8")
    os.replace(tmp, p)


BUCKET_S = 6 * 3600     # 만성어 계수 칸(6시간)


def chronic(st, key, now):
    """만성어 = 지난 72h(최근 6h 칸 제외 · 6시간 칸 근사) tbs 스냅샷의 15%↑에서 2곳↑. 표본 12개 미만 = 판정 보류(False)."""
    lo, hi_h = int((now - CHRONIC_H * 3600) // BUCKET_S), int((now - CHRONIC_SKIP_H * 3600) // BUCKET_S)
    tot = sum(n for h, n in (st.get("tb") or {}).items() if lo <= int(h) < hi_h)
    if tot < CHRONIC_MIN_SNAP:
        return False
    n = sum(v for h, v in ((st.get("hi") or {}).get(key) or {}).items() if lo <= int(h) < hi_h)
    return n / tot >= CHRONIC_RATIO


def update(st, snap, now):
    """한 회차 관측을 상태에 반영 → {key: 에피소드}. 만성어 계수·갈래 최근 관측·무장·만료·정리."""
    obs, meta = observe(snap, now)
    if meta["t_tbs"]:
        m, h = int(meta["t_tbs"] // 60), str(int(meta["t_tbs"] // BUCKET_S))
        tl = st.setdefault("tl", [])
        if m not in tl:                    # 같은 스냅샷(updated) 재독 = 이중 계수 0
            st["tl"] = (tl + [m])[-24:]
            tb = st.setdefault("tb", {})
            tb[h] = tb.get(h, 0) + 1
            for k in meta["hi"]:
                d = st["hi"].setdefault(k, {})
                d[h] = d.get(h, 0) + 1
    eps = st.setdefault("k", {})
    for k, e in obs.items():
        fams = {}
        comm = (e.get("C", 0) >= COMM_MIN and meta["tbs_fresh"]) or e.get("S", 0) >= COMM_MIN
        if comm and not chronic(st, k, now):
            fams["C"] = meta["t_tbs"] if (e.get("C", 0) >= COMM_MIN and meta["tbs_fresh"]) else now
        if "X" in e:
            fams["X"] = meta["t_sns"]
        if "G" in e:
            fams["G"] = meta["t_sns"]
        if "N" in e:
            fams["N"] = meta["t_nm"]
        if not fams:
            continue
        ep = eps.setdefault(k, {"f": {}, "m": {}})
        if e["d"] != k:
            ep["d"] = e["d"]               # 표시형(여러 낱말 검색어) — 키와 같으면 생략(상태 작게)
        for f, t in fams.items():
            t = int(min(t or now, now))
            ep["f"][f] = max(ep["f"].get(f, 0), t)
        mm = ep["m"]
        if "C" in fams:
            mm["c"] = max(e.get("C", 0), e.get("S", 0)) if meta["tbs_fresh"] else e.get("S", 0)
        if "X" in fams:
            mm["x"] = e["X"]
        if "G" in fams:
            mm["g"] = e["G"][1]
        if "N" in fams:
            mm["n"] = e["N"]
    for k in list(eps):
        ep = eps[k]
        last = max(ep["f"].values() or [0])
        if last < now - IDLE_H * 3600:
            eps.pop(k, None)
            st.get("gn", {}).pop(k, None)
            continue
        act = active(ep, now)
        if len(act) >= 2 and not ep.get("a"):
            ep["a"] = int(now)
    prune(st, now)
    return eps


def active(ep, now):
    return "".join(f for f in FAM if (ep.get("f") or {}).get(f, 0) >= now - PAIR_H * 3600)


def tier(ep, now):
    if not ep:
        return 0
    if ep.get("a"):
        if ep.get("cf") and now - ep["cf"] < STRONG_KEEP_H * 3600:
            return 3
        return 2
    return 1 if active(ep, now) else 0


def confirm_ours(ep, matches, now, older=()):
    """우리 수집함 확인 = 신선 매칭 후보 중 최대 cross≥3 ∧ novel(무장 24h~3h 전 사이에 처음 본 매칭 후보 0 — older = 나이 무관 전 매칭).
    ⚠ novel 을 신선분만으로 재면 하루 전부터 보도된 사건(포로·법적 대응 같은 일반어)이 매번 「새 사건」이 된다(리플레이 실측). 반환 = 확인 여부."""
    if not ep.get("a") or ep.get("cf") or not matches:
        return bool(ep.get("cf"))
    a = ep["a"]
    for c in list(matches) + list(older):
        t = _ts(c.get("first_seen"))
        if t and a - NOVEL_BACK_H * 3600 <= t < a - NOVEL_H * 3600:
            return False
    cr = max((c.get("cross") or 0) for c in matches)
    if cr >= GN_MIN:
        ep["cf"], ep["cs"], ep["o"] = int(now), "o", int(cr)
        return True
    return False


# ── 구글 뉴스 확인(명시 네트워크 함수) ──────────────────────────────────────────────
def _gn():
    """구글 뉴스 검색 정본(.github/scripts/gnews_search.py · 파서·차단 판정 사본 0) — 못 읽으면 None(확인 축만 쉰다)."""
    import sys
    p = str(ROOT / ".github" / "scripts")
    if p not in sys.path:
        sys.path.insert(0, p)
    try:
        import gnews_search
        return gnews_search
    except Exception:  # noqa: BLE001
        return None


def gn_count(items, key, now, armed):
    """검색 RSS 항목 → (매체 수, novel, 가장 이른 관련 항목). 순수 함수(테스트 = 픽스처).
    관련 = 제목(끝 「 - 매체」 제거)에 이름 적중 · 매체 = sname(없으면 원천 호스트) · 포털 재게재 제외.
    매체 수 = 지금부터 6h 안에 발행한 서로 다른 매체 · novel = 무장 24h~3h 전 사이 관련 보도 0."""
    G = _gn()
    if G is not None:
        portal, host, tail = G._PORTAL_HOSTS, G._host, G._SRC_TAIL_RE
    else:
        portal, host, tail = (), (lambda u: ""), re.compile(r"\s+-\s+[^-]{1,40}$")
    outs, first, novel = set(), None, True
    a = armed or now
    for it in items or []:
        p = it.get("pub") or 0
        t = tail.sub("", it.get("title") or "")
        if not p or not hit(key, t):
            continue
        h = host(it.get("source") or "")
        if h in portal:
            continue
        if a - NOVEL_BACK_H * 3600 <= p < a - NOVEL_H * 3600:
            novel = False
        if now - GN_WIN_H * 3600 <= p <= now + 600:
            outs.add(re.sub(r"\s+", "", (it.get("sname") or h or "")).lower())
            if first is None or p < first["p"]:
                first = {"p": int(p), "t": t.strip(), "m": (it.get("sname") or h or "").strip(), "l": it.get("link") or ""}
    outs.discard("")
    return len(outs), novel, first


GN_POLL_H = 6           # 무장 뒤 이 시간 안에만 확인 검색(그 뒤 미확인 = 언론이 안 받은 소동 = 더 두드리지 않는다)


def gn_poll(st, keys, now, fetch=None, pause=None, max_q=None):
    """무장(t2)·미확인 이름만 구글 뉴스 검색(회차당 max_q · 10분 캐시 · 차단 = 즉시 중단 · 실패 = 조용히 다음 회차).
    fetch(query) → RSS xml(없으면 gnews_search._http). 반환 = 이번 회차 실제 요청 수."""
    eps, cache = st.get("k") or {}, st.setdefault("gn", {})
    pause = GN_PAUSE_S if pause is None else pause
    max_q = GN_MAX_Q if max_q is None else max_q
    G = _gn()
    if fetch is None:
        if G is None:
            return 0
        fetch = lambda q: G._http(G.rss_url(q + " when:2d"))   # noqa: E731
    n = 0
    for k in keys:
        ep = eps.get(k)
        if not ep or not ep.get("a") or ep.get("cf") or now - ep["a"] > GN_POLL_H * 3600:
            continue
        c = cache.get(k) or {}
        if c.get("at") and now - c["at"] < GN_TTL_S:
            continue
        if n >= max_q:
            break
        if G is not None and G.STATS.get("hard"):
            break
        n += 1
        try:
            xml = fetch(ep.get("d") or k)
            items = G.parse_rss(xml) if G is not None else []
        except Exception:  # noqa: BLE001
            items, xml = [], ""
        if not xml:
            continue                       # 실패는 캐시하지 않는다(다음 회차 재시도)
        cnt, nov, first = gn_count(items, k, now, ep.get("a"))
        c = {"at": int(now), "n": cnt, "nov": int(bool(nov))}
        if first:
            c["e"] = first
        if (cache.get(k) or {}).get("ru"):
            c["ru"] = cache[k]["ru"]
        cache[k] = c
        if cnt >= GN_MIN and nov:
            ep["cf"], ep["cs"] = int(now), "g"
        if pause:
            time.sleep(pause)
    return n


def gn_candidates(st, now):
    """구글 뉴스 확인 대기 순서 = 무장·미확인 · 갈래 많은 순 → 커뮤니티 곳수 → 최근 무장."""
    eps = st.get("k") or {}
    ks = [k for k, ep in eps.items() if ep.get("a") and not ep.get("cf")]
    return sorted(ks, key=lambda k: (-len(active(eps[k], now)), -((eps[k].get("m") or {}).get("c") or 0), -eps[k]["a"], k))


def lv_of(st, key, now):
    """후보 엔트리에 싣는 증거(작게 · 있는 값만) = {k, t, f, c, x, g, n, gn, a}."""
    ep = (st.get("k") or {}).get(key)
    t = tier(ep, now)
    if not t:
        return None
    d = {"k": ep.get("d") or key, "t": t}
    f = active(ep, now)
    if f:
        d["f"] = f
    m = ep.get("m") or {}
    for s in ("c", "x", "g", "n"):
        if m.get(s):
            d[s] = m[s]
    g = (st.get("gn") or {}).get(key) or {}
    o = max(g.get("n") or 0, ep.get("o") or 0)
    if o:
        d["gn"] = o
    if ep.get("a"):
        d["a"] = iso(ep["a"])
    return d


def prune(st, now):
    """72h 넘은 만성어 계수·스냅샷 목록 정리 · 에피소드 없는 캐시·씨앗 장부 정리(상태 파일 = 작게)."""
    lo, rec = int((now - KEEP_H * 3600) // BUCKET_S), int((now - IDLE_H * 3600) // BUCKET_S)
    st["tb"] = {h: n for h, n in (st.get("tb") or {}).items() if int(h) >= lo}
    hi = {}
    for k, d in (st.get("hi") or {}).items():
        d = {h: n for h, n in d.items() if int(h) >= lo}
        if not d or (sum(d.values()) <= 2 and max(int(h) for h in d) < rec):
            continue                       # 잠깐 스친 말(12h 전 2회 이하) = 만성 판정(15% ≈ 20회↑)에 영향 0 → 버린다(상태 작게)
        hi[k] = d
    st["hi"] = hi
    eps = st.get("k") or {}
    st["gn"] = {k: v for k, v in (st.get("gn") or {}).items() if k in eps}
    st["sd"] = {k: v for k, v in (st.get("sd") or {}).items()
                if k in eps or (isinstance(v, dict) and now - (v.get("at") or 0) < KEEP_H * 3600)}


# ── 판정 꼬리표(breaking_judge 가 읽는 한국어 표기) ─────────────────────────────────────
TIER_LABEL = {3: "강", 2: "중", 1: "약"}


def _man(v):
    v = int(v or 0)
    if v >= 10000:
        return f"{v / 10000:g}만".replace(".0만", "만")
    if v >= 1000:
        return f"{v // 1000}천"
    return str(v)


def tail(lv):
    """lv → 〔확산 강 «닛몰캐쉬»: 커뮤니티 4곳 동시 · X 1위 · 구글 급상승 1만 · 나무위키 2위 · 언론 7곳〕(없는 칸 생략)."""
    if not isinstance(lv, dict) or not lv.get("t"):
        return ""
    parts = []
    if lv.get("c"):
        parts.append(f"커뮤니티 {lv['c']}곳 동시")
    if lv.get("x"):
        parts.append(f"X {lv['x']}위")
    if lv.get("g"):
        parts.append(f"구글 급상승 {_man(lv['g'])}")
    if lv.get("n"):
        parts.append(f"나무위키 {lv['n']}위")
    if lv.get("gn"):
        parts.append(f"언론 {lv['gn']}곳")
    head = f"확산 {TIER_LABEL.get(int(lv['t']), '약')} «{lv.get('k') or ''}»"
    return "〔" + head + (": " + " · ".join(parts) if parts else "") + "〕"


def lv_tier(c):
    """엔트리의 확산 단계(없음 = 0) — 판정·게이트·푸시·뷰어 공용 술어의 입력."""
    lv = c.get("lv") if isinstance(c, dict) else None
    try:
        return int(lv.get("t") or 0) if isinstance(lv, dict) else 0
    except (TypeError, ValueError):
        return 0
