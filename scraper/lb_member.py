#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 클러스터 「최신 국면 멤버」(lb) 선택 — 대표 제목이 예고·이전 국면에 고정돼 진짜 사건 1보가 판정기 눈에 한 번도 안 가던
# 사고(260913 용혜인: 10:48 「[속보] 오전 11시 30분 국회 기자회견」이 대표 → 11:37 「[속보] 자진사퇴」 1보는 같은 덩어리의
# 멤버로만 흡수 · 판정 도장 = 규칙+대표 제목이라 재판정 0 · 하루 종일 grade 1 = 배지·푸시·자동픽 전부 0) 봉합.
#
# 왜 여기서: 대표(rep) = 클러스터 최초 발행 기사, 픽 = 최상위 매체 최초 기사(knews_scraper.score_crosspost)라
# 「예고 → 발생」 순서면 발생 기사는 구조적으로 제목이 될 수 없다. 이 모듈은 클러스터마다 **대표와 약하게 이어진 최근
# [속보] 멤버 1건**을 골라 rep 기사에 `lb = {t, u, p, m}`(≤~200B · 해당 클러스터만)로 싣는다.
# 소비: scraper/to_candidates.py(캐리·스왑 고정) → .github/scripts/breaking_judge.py(대표 행 + lb 행 2행 판정 ·
# BREAKING_LB=shadow|live). 8인 평의회(260913) 수렴안 = 판정 입력만 넓히고 클러스터·cross·랭킹·배지 술어 무접촉.
#
# 선택 규칙(결정적 · 폰/클라우드가 같은 기사 집합이면 같은 선택):
#  ① 창 = 클러스터 **최신 발행** 기준 LB_WINDOW_MIN(60분) — 스크랩 시각이 아니라 발행시각 축(스크래퍼 간 동일).
#     최신 발행이 LB_STALE_H(2h)보다 오래된 클러스터는 emit 0(묵은 사건에 필드 안 얹음 = 예산).
#  ② 후보 = 창 안 ∧ 제목에 [속보|N보|상보|긴급] 태그 ∧ 대표·픽 자신이 아님 ∧ 토큰이 대표 토큰의 부분집합이 아님(같은 국면 재탕 제외).
#  ③ 약한 연결 = 대표 제목과 **비숫자 토큰 1개 이상 공유**(직함·기관·정당 공통어 LB_LINK_STOP 제외) —
#     공유 0 = 순수 transitive 체인(무관 사건)이라 배제 · 병기 제목(「김승원·용혜인」)은 통과 → 최종 판별은 판정기 2행이 맡는다.
#  ④ 선택 = (발행 오름차, 매체 순위, url 사전순) 최소 = 창 안 **최초** [속보](끈적임 → 새 재탕이 붙어도 선택 불변 = 재판정 창당 1회 수렴).
# 순수 함수 · 네트워크·파일 0 · 어떤 예외도 None(수집을 못 깸 — 호출부 try 이중).
import re
from datetime import datetime, timedelta, timezone

LB_WINDOW_MIN = 60
LB_STALE_H = 2.0
LB_TITLE_MAX = 80
LB_TAG = re.compile(r"\[\s*(속보|\d보|상보|긴급)\s*\]")
# 연결 판정 전용 공통어(클러스터링 STOPWORDS와 분리 — 그쪽은 건드리지 않는다). 직함·기관·정당은 같은 덩어리의 **다른 인물**
# 기사도 공유하므로(「[속보] 김승원 후보자, 국회…」 vs 용혜인 대표 = {후보자, 국회}) 연결 근거에서 뺀다.
LB_LINK_STOP = frozenset({
    "후보자", "후보", "장관", "장관직", "의원", "의원직", "국회", "대통령", "대통령실", "청와대", "정부", "여당", "야당",
    "국힘", "국민의힘", "민주당", "민주", "총리", "위원장", "대표", "당대표", "정당", "지명", "인사", "청문회", "인사청문회",
})


def _ts(s):
    """ISO 문자열 → aware datetime(naive = UTC 가정). 실패 = None."""
    if not s:
        return None
    try:
        t = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except ValueError:
        try:
            t = datetime.strptime(str(s), "%Y-%m-%dT%H:%M:%S%z")
        except ValueError:
            return None
    return t if t.tzinfo else t.replace(tzinfo=timezone.utc)


def pick_lb(members, articles, rep, pick, tokenize, pick_rank, now=None):
    """members = 클러스터 멤버 인덱스 · articles = 기사 dict 리스트(title·link·publisher·published) · rep/pick = 인덱스.
    tokenize/pick_rank = knews_scraper 정본 주입(이 모듈은 feedparser 의존 0 = 테스트·폰 어디서나 import 가능).
    반환 = {"t": 제목≤80자, "u": url, "p": 발행 ISO, "m": 매체} 또는 None."""
    try:
        now = now or datetime.now(timezone.utc)
        rep_title = (articles[rep].get("title") or "")
        rep_toks = tokenize(rep_title)
        if not rep_toks:
            return None
        pts = [(m, _ts(articles[m].get("published"))) for m in members]
        pts = [(m, t) for m, t in pts if t is not None]
        if not pts:
            return None
        newest = max(t for _, t in pts)
        if (now - newest) > timedelta(hours=LB_STALE_H):
            return None
        win = newest - timedelta(minutes=LB_WINDOW_MIN)
        best = None
        for m, t in pts:
            if t < win or m == rep or m == pick:
                continue
            a = articles[m]
            title = a.get("title") or ""
            if not LB_TAG.search(title):
                continue
            toks = tokenize(title)
            if not toks or toks <= rep_toks:
                continue
            link = {x for x in (toks & rep_toks) if not x.isdigit() and x not in LB_LINK_STOP}
            if not link:
                continue
            key = (t, pick_rank(a.get("publisher") or ""), a.get("link") or "")
            if best is None or key < best[0]:
                best = (key, m)
        if best is None:
            return None
        a = articles[best[1]]
        return {
            "t": (a.get("title") or "")[:LB_TITLE_MAX],
            "u": a.get("link") or "",
            "p": a.get("published") or "",
            "m": a.get("publisher") or "",
        }
    except Exception:  # noqa: BLE001 — 부가 필드 실패가 수집을 못 깸
        return None
