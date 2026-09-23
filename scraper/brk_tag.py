#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 속보 제목 태그 — SSOT (운영자 260923 «속보로 뜨는 게 늦어버리는 점 = 제일 우선순위»)
# 소비처 = scraper/to_candidates.py(1차 후보·단독 입장 → 엔트리 "solo" 표식) · .github/scripts/push_send.py(단독 푸시 허용·[단독] 대형 알림).
# 뷰어는 정규식을 복제하지 않고 "solo" 표식만 읽는다(사본 0). lb_member.LB_TAG 는 목적이 다른 별도 집합(최신 국면 멤버 선택 · [2보] 포함).
# 뉴시스는 첫 보도를 제목 끝 "(1보)"로도 낸다(260923 라이브 피드 실측) — 대괄호형만 보던 구판이 놓치던 형식.
import re

BREAKING_TAG = re.compile(r"\[\s*(속보|상보|긴급|1보)\s*\]|\(\s*1보\s*\)")
# 단독 푸시용 = 첫 보도 태그만([상보]는 이미 나간 사건의 상세 후속이라 제외 — 수집함 입장·판정은 BREAKING_TAG 그대로 · 평의회3 260923).
FIRST_REPORT_TAG = re.compile(r"\[\s*(속보|긴급|1보)\s*\]|\(\s*1보\s*\)")


def has_breaking_tag(*titles):
    return any(BREAKING_TAG.search(t or "") for t in titles)


def has_first_report_tag(*titles):
    return any(FIRST_REPORT_TAG.search(t or "") for t in titles)


# [단독] = 한 매체 특종(운영자 260924 «승리 CCTV 같은 건 항상 먼저 알림» — JTBC 단독 20:45 → 두 번째 매체·묶음 대기로 수집함 23:16).
#   속보 태그가 아니라 breaking_candidate 는 안 켠다(속보 판정은 JUDGE_ALL 이 어차피 전건) · 입장·경중 채점만 앞당긴다.
EXCLUSIVE_TAG = re.compile(r"\[\s*단독\s*\]")


def has_exclusive_tag(*titles):
    return any(EXCLUSIVE_TAG.search(t or "") for t in titles)
