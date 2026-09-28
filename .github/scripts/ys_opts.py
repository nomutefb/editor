#!/usr/bin/env python3
"""유튜브 숏폼(ys) 옵션 검문 — env IN_OPTS(JSON) → stdout `KEY=VALUE` 줄(워크플로가 $GITHUB_ENV 에 붙인다).

api/ys.js cleanOpts 와 같은 화이트리스트를 러너에서 한 번 더 적용한다(상류 신뢰 대신 최후 방어선 · vd opts 선례).
허용 목록의 첫 값 = 기본(운영자 260928 «60초 · 고급 음성 · 정밀 받아쓰기 · 맥 그림 · 9:16 · 자막 배경 켬 100%»).
"""
import json
import os
import re

ALLOW = {
    'voice': ['eleven', 'edge'],
    'stt': ['scribe', 'subs'],
    'img': ['codex', 'none'],
    'len': ['60', '45', '90'],
    'font': ['pretendard', 'gothic', 'barun'],
    'ratio': ['9:16', '16:9'],
    'subbg': ['on', 'off'],
}


def clean(raw):
    try:
        o = json.loads(raw or '{}')
    except ValueError:
        o = {}
    if not isinstance(o, dict):
        o = {}
    out = {k: (str(o.get(k, '')) if str(o.get(k, '')) in allow else allow[0]) for k, allow in ALLOW.items()}
    try:
        out['subop'] = str(max(0, min(100, int(o.get('subop', 100)))))
    except (TypeError, ValueError):
        out['subop'] = '100'
    ev = str(o.get('el_voice', ''))
    out['el_voice'] = ev if re.fullmatch(r'[A-Za-z0-9]{16,32}', ev) else ''
    return out


def main():
    o = clean(os.environ.get('IN_OPTS', ''))
    names = {'voice': 'YS_VOICE', 'stt': 'YS_STT', 'img': 'YS_IMG', 'len': 'YS_LEN', 'font': 'YS_FONT',
             'ratio': 'YS_RATIO', 'subbg': 'YS_SUBBG', 'subop': 'YS_SUBOP', 'el_voice': 'YS_EL_VOICE_IN'}
    for k, env in names.items():
        print(f'{env}={o[k]}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
