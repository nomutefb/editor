#!/usr/bin/env python3
"""Short reminder; detailed rules stay in the current project documents."""
import json
import sys

if '--if-ui-prompt' in sys.argv:
    try:
        prompt = json.load(sys.stdin).get('prompt', '').lower()
    except (ValueError, AttributeError):
        prompt = ''
    if not any(word in prompt for word in ('ui', 'ux', 'css', '디자인', '버튼', '모달', '폰트', '레이아웃', '여백', '아이콘', '뷰어')):
        sys.exit(0)
print('[디자인] 현재 계약은 AGENTS.md와 CLAUDE.md §🎨. '
      '관련 작업에만 디자인기틀/디자인기틀_SSOT.md와 CII_컴포넌트계승인덱스.md를 읽는다. '
      'viewer-src를 수정하고 node shared/build_shell.mjs로 조립한다. '
      '기존 토큰·컴포넌트를 계승하며 사용자 명시 개편 지시를 우선한다. '
      '디자인 거울은 생성하고, 화면 변경은 check_refs와 smoke_all로 검증한다.')
