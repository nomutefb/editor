#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ═══════════════════════════════════════════════════════════════════════════════
# access_token.py — Cloudflare Access 서비스 토큰 비밀값 정규화(단일 정본 · 260925)
#
# ▷ 왜: Cloudflare 대시보드의 토큰 복사 버튼은 값만이 아니라 헤더 줄 전체
#   (`CF-Access-Client-Id: ….access` / `CF-Access-Client-Secret: …`)를 복사한다.
#   그대로 GitHub 비밀값에 넣으면 헤더가 `CF-Access-Client-Id: CF-Access-Client-Id: …`가 되어
#   Access가 거부한다(260925 live-smoke #192 실측 = ACCESS=denied · 토큰 '마지막 확인' 공란).
#   값 앞말·공백·줄바꿈·따옴표·ID↔Secret 뒤바뀜을 여기서 한 번에 걷어 모든 소비자가 같은 값을 싣게 한다.
#
# ▷ 규칙(순서대로):
#   1) 두 비밀값 어디든 `CF-Access-Client-Id:` / `CF-Access-Client-Secret:` 헤더 이름이 있으면 그 뒤 값을 쓴다
#   2) 없으면 마지막 `:` 앞을 버리고(다른 이름표 앞말) 공백·따옴표를 지운다 — 토큰 값에는 `:`·공백이 없다
#   3) ID는 `.access`로 끝난다 — ID 쪽에 없고 Secret 쪽에 있으면 둘을 맞바꾼다
#
# ▷ 소비자: shared/live_smoke.py · scraper/watchdog.py(파이썬 import) /
#   .github/scripts/notify_summary.sh · live-smoke.yml 수렴 curl · pages-redeploy.yml(셸 = --shell eval)
#
# 사용: python3 shared/access_token.py --shell   → 정규화된 export 2줄(Actions면 ::add-mask:: 동반) · 둘 다 비면 출력 0
#       python3 shared/access_token.py --shape   → 값 없이 모양 진단 1줄(ACCESS_SHAPE …)
# ═══════════════════════════════════════════════════════════════════════════════
import os
import re
import shlex
import sys

ENV_ID, ENV_SECRET = "CF_ACCESS_CLIENT_ID", "CF_ACCESS_CLIENT_SECRET"
_HDR_ID = re.compile(r"cf-access-client-id\s*:\s*[\"']?([^\s\"',;]+)", re.I)
_HDR_SECRET = re.compile(r"cf-access-client-secret\s*:\s*[\"']?([^\s\"',;]+)", re.I)
_JUNK = re.compile(r"[\s\"']")


def _bare(raw, fixes):
    v = (raw or "").strip()
    if ":" in v:
        v = v.rsplit(":", 1)[1]
        fixes.add("prefix")
    out = _JUNK.sub("", v)
    if out != v.strip():
        fixes.add("space")
    return out


def normalize(raw_id, raw_secret):
    """(id, secret, fixes) — 값은 헤더에 바로 실을 수 있는 모양. fixes = 고친 종류(prefix·space·swap)."""
    fixes = set()
    blob = f"{raw_id or ''}\n{raw_secret or ''}"
    m_id, m_sec = _HDR_ID.search(blob), _HDR_SECRET.search(blob)
    if m_id:
        cid = m_id.group(1)
        fixes.add("prefix")
    else:
        cid = _bare(raw_id, fixes)
    if m_sec:
        sec = m_sec.group(1)
        fixes.add("prefix")
    else:
        sec = _bare(raw_secret, fixes)
    if cid and sec and not cid.endswith(".access") and sec.endswith(".access"):
        cid, sec = sec, cid
        fixes.add("swap")
    return cid, sec, fixes


def from_env(env=None):
    env = os.environ if env is None else env
    return normalize(env.get(ENV_ID, ""), env.get(ENV_SECRET, ""))


def headers(env=None):
    """둘 다 있을 때만 Access 헤더 dict — 하나라도 비면 {}(= 토큰 미설정 판정 유지)."""
    cid, sec, _ = from_env(env)
    return {"CF-Access-Client-Id": cid, "CF-Access-Client-Secret": sec} if cid and sec else {}


def shape(env=None):
    """값을 드러내지 않는 모양 진단 1줄 — 거부(denied) 원인 좁히기용."""
    cid, sec, fixes = from_env(env)
    return ("ACCESS_SHAPE id_suffix=" + ("ok" if cid.endswith(".access") else "bad")
            + f" id_len={len(cid)} secret_len={len(sec)}"
            + " secret_hex=" + ("yes" if sec and re.fullmatch(r"[0-9a-fA-F]+", sec) else "no")
            + " fixed=" + (",".join(sorted(fixes)) or "none"))


def shell_lines(env=None):
    env = os.environ if env is None else env
    if not (env.get(ENV_ID) or env.get(ENV_SECRET)):
        return []
    cid, sec, _ = from_env(env)
    lines = []
    for name, val in ((ENV_ID, cid), (ENV_SECRET, sec)):
        if env.get("GITHUB_ACTIONS") == "true" and val and val != env.get(name, ""):
            lines.append("echo " + shlex.quote("::add-mask::" + val))   # 원본 비밀값의 부분 문자열 = 자동 마스킹 대상 아님 → 명시 마스킹
        lines.append(f"export {name}={shlex.quote(val)}")
    return lines


if __name__ == "__main__":
    if "--shell" in sys.argv[1:]:
        print("\n".join(shell_lines()))
    elif "--shape" in sys.argv[1:]:
        print(shape())
    else:
        print(__doc__ or "사용: --shell | --shape", file=sys.stderr)
        sys.exit(2)
