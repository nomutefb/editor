#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""비밀칸·변수 등록 전수 점검 — 「코드가 쓰는 이름」 vs 「저장소에 실제로 등록된 이름」 대조.

왜 신설했나(260816 운영자 승인 · 계정 이관 후속):
  260816 계정 이관에서 인스타 접속 열쇠가 안 따라왔는데, 그게 **우연히** 발견됐다 — 3시간마다 도는
  워크플로라 마침 그날 실패 메일이 왔고 운영자가 그 화면을 세션에 넘겨서다. 며칠에 한 번만 도는
  레인(주간 집계·백필·프로브)의 열쇠가 빠졌다면 그때 가서야 터진다 = **비어 있는 칸은 터지기 전까지
  화면 증상이 0이다**(insta-thumb-miss·brk_misfire 동축). 기존 게이트는 전부 다른 축이다 —
  check_workflow_yaml = 문법 · check_paths = 경로 실존 · account-selftest = GH_TOKEN 한 개의 읽기·쓰기
  → 「이 저장소가 쓰는 이름이 **실제로 등록돼 있는가**」는 축 자체가 없었다.

⚠ 값은 한 글자도 출력하지 않는다 — 키 이름만 다룬다(토큰 원문 저장 금지 = insta_fetch token_meta 관례).
   러너가 넘기는 toJSON(secrets)는 이 프로세스 메모리에서 키만 뽑고 값은 즉시 버린다.

⚠ 「미등록 = 곧 결함」이 아니다 — 이 레포는 「시크릿 미등록 = no-op 스캐폴드」가 정상 관례다
   (insta_fetch·thumb_gen·fb_fetch 전부). 그래서 **폴백 유무로 두 단을 가른다**:
     ㉠ 폴백 없음 = 빈 값이 그대로 흘러간다 = 그 기능은 죽거나 조용히 스캐폴드로 빠진다(먼저 볼 것)
     ㉡ 폴백 있음(`|| '기본값'`) = 미등록이어도 기본값으로 돈다(정상 설계 · 참고만)
   판정은 사람이 한다 — 이 스크립트는 「무엇이 비어 있는지」를 이름으로 보이게만 한다.

산출: 알림 messages/secret-coverage.json(빠진 것 있을 때 · 없으면 자동 clear) + 표준출력 요약.
"""
import json
import os
import re
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
WF_DIR = os.path.join(ROOT, '.github', 'workflows')
MSG_ID = 'secret-coverage'

# 러너가 자동 주입 = 등록 대상이 아니다(항상 있다).
AUTO = {'GITHUB_TOKEN'}

_REF_RE = re.compile(r'\b(secrets|vars)\.([A-Z_][A-Z0-9_]*)')
# 같은 표현식 안에서 그 이름 뒤에 `|| '…'`/`|| "…"` 가 붙으면 폴백 보유(미등록이어도 기본값으로 돈다).
_FALLBACK_RE = re.compile(r'\b(?:secrets|vars)\.([A-Z_][A-Z0-9_]*)\s*\|\|')


def scan_refs():
    """워크플로 전수 → {kind: {name: {'files': set, 'fallback': bool}}}. 표면 자동 발견 = 새 워크플로가 조용히 못 빠진다."""
    out = {'secrets': {}, 'vars': {}}
    try:
        files = sorted(f for f in os.listdir(WF_DIR) if f.endswith(('.yml', '.yaml')))
    except OSError:
        return out
    for f in files:
        try:
            with open(os.path.join(WF_DIR, f), encoding='utf-8') as fh:
                raw = fh.read()
        except OSError:
            continue
        # 주석 줄 제외 = 「예전엔 이 열쇠를 썼다」는 기록이 현행 사용으로 잡히는 것 차단.
        body = '\n'.join(ln for ln in raw.splitlines() if not ln.lstrip().startswith('#'))
        has_fb = set(_FALLBACK_RE.findall(body))
        for kind, name in _REF_RE.findall(body):
            if name in AUTO:
                continue
            e = out[kind].setdefault(name, {'files': set(), 'fallback': False})
            e['files'].add(f)
            if name in has_fb:
                e['fallback'] = True
    return out


def registered(env_key):
    """러너가 넘긴 toJSON(...) → 키 이름 집합. ⚠ 값은 읽지도 남기지도 않는다."""
    raw = os.environ.get(env_key, '') or ''
    if not raw.strip():
        return None          # 미주입 = 「등록분을 모른다」 = 대조 불가(빈 집합과 구분 = 전건 빠짐 오보 차단)
    try:
        return set(json.loads(raw).keys())
    except Exception:
        return None


def _msg_py():
    return os.path.join(ROOT, 'shared', 'msg.py')


def main():
    have_s = registered('ALL_SECRETS')
    have_v = registered('ALL_VARS')
    if have_s is None and have_v is None:
        print('no-op — 등록분 미주입(ALL_SECRETS/ALL_VARS). 이 스크립트는 워크플로 안에서만 대조할 수 있다.')
        return 0

    refs = scan_refs()
    miss = {'secrets': [], 'vars': []}
    for kind, have in (('secrets', have_s), ('vars', have_v)):
        if have is None:
            continue
        for name, e in sorted(refs[kind].items()):
            if name not in have:
                miss[kind].append((name, e['fallback'], sorted(e['files'])))

    n_used = len(refs['secrets']) + len(refs['vars'])
    hard = [(k, n, f) for k in ('secrets', 'vars') for (n, fb, f) in miss[k] if not fb]
    soft = [(k, n, f) for k in ('secrets', 'vars') for (n, fb, f) in miss[k] if fb]
    print(f'· 코드가 쓰는 이름 {n_used}종(비밀칸 {len(refs["secrets"])} · 변수 {len(refs["vars"])})')
    print(f'· 등록 안 된 것 {len(hard) + len(soft)}종 — 폴백 없음 {len(hard)} · 폴백 있음 {len(soft)}')
    for k, n, f in hard:
        print(f'  ❌ [{ "비밀칸" if k == "secrets" else "변수" }] {n} — {", ".join(f[:3])}')
    for k, n, f in soft:
        print(f'  · [{ "비밀칸" if k == "secrets" else "변수" }] {n}(기본값 있음) — {", ".join(f[:3])}')

    if not hard and not soft:
        subprocess.run(['python3', _msg_py(), 'clear', MSG_ID], check=False)
        return 0

    def _ko(k):
        return '비밀칸' if k == 'secrets' else '변수'

    lines = [f'저장소에 안 채워진 칸이 {len(hard) + len(soft)}개 있어(코드가 쓰는 이름 {n_used}종 전수 대조).', '']
    if hard:
        lines.append('[먼저 볼 것 — 기본값이 없어서 빈 값이 그대로 흘러가]')
        for k, n, f in hard:
            lines.append(f' · {_ko(k)} {n} — 쓰는 곳: {", ".join(x.replace(".yml", "") for x in f[:3])}')
        lines.append('')
    if soft:
        lines.append('[참고 — 기본값이 있어서 안 채워도 돌아]')
        for k, n, f in soft:
            lines.append(f' · {_ko(k)} {n} — 쓰는 곳: {", ".join(x.replace(".yml", "") for x in f[:3])}')
        lines.append('')
    lines += [
        '⚠ 안 채워졌다고 다 고장은 아니야 — 이 저장소는 「열쇠가 없으면 그 기능만 조용히 쉰다」가 정상 설계야.',
        '   위 목록은 「무엇이 비어 있나」를 보여줄 뿐이고, 채울지 말지는 네가 정하면 돼.',
        '',
        '👉 네가 할 일: 위 「먼저 볼 것」 칸이 원래 쓰던 기능이면 깃허브 저장소 설정에서 값을 채워 줘 '
        '(비밀칸 = Settings → Secrets and variables → Actions → Secrets · 변수 = 같은 화면 Variables 탭). '
        '안 쓰는 기능이면 그냥 둬도 돼 — 그 기능만 쉬고 나머지는 그대로 돌아.',
    ]
    subprocess.run(['python3', _msg_py(), 'set', MSG_ID, '\n'.join(lines), 'warn'], check=False)
    return 0


if __name__ == '__main__':
    sys.exit(main())
