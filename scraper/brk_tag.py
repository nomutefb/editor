#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 속보 제목 태그 — SSOT (운영자 260923 «속보로 뜨는 게 늦어버리는 점 = 제일 우선순위»)
# 소비처 = scraper/to_candidates.py(1차 후보·단독 입장) · .github/scripts/push_send.py(단독 푸시 허용).
# 뷰어 사본 = viewer-src/35-applyAutoGroups.part BRK_TAG_RE(언어 경계라 사본 불가피) — 동기 = tests/test_solo_breaking.py.
# 뉴시스는 첫 보도를 제목 끝 "(1보)"로도 낸다(260923 라이브 피드 실측) — 대괄호형만 보던 구판이 놓치던 형식.
import re

BREAKING_TAG = re.compile(r"\[\s*(속보|상보|긴급|1보)\s*\]|\(\s*1보\s*\)")


def has_breaking_tag(*titles):
    return any(BREAKING_TAG.search(t or "") for t in titles)
