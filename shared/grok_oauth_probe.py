#!/usr/bin/env python3
"""grok_oauth_probe — X(엑스) 구독 자격으로 Grok API를 부를 수 있는지 실호출로 판정한다.

배경(260810 · 운영자 "이미 내가 가지고 있는 x계정에 속한 그록 oauth 를 빼서 배선시킬 수 있는 방법있나?"):
  xAI 는 2026-05 부터 구독자용 OAuth 를 열었다 — API 키(종량제) 없이 SuperGrok / X Premium+ 자격만으로
  https://api.x.ai/v1 를 부른다. 다만 xAI 백엔드가 OAuth 표면에 자체 허용목록을 걸고 있다는 신고가
  다수 있어(표준 SuperGrok·X Premium 이 추론 단계에서 403), **우리 계정이 되는지는 실호출로만 알 수 있다**.
  → 이 파일은 그 한 가지만 한다: 로그인 → 1콜 → 통과/거절을 사유 원문과 함께 못박는다.

⚠ 이건 배선이 아니라 **판정기**다. 통과가 확인된 뒤에야 shared/claude_py.py 형제로 배선한다
  (구독 축 호출 SSOT 관례 = 종량제 벤더 신설 0 · shared/models.json vendors 무접촉).

실측 확인분(260810 · 이 파일 작성 시점):
  - https://auth.x.ai/.well-known/openid-configuration 가 device_code grant 를 광고한다(실 GET 200).
  - POST https://auth.x.ai/oauth2/device/code 가 user_code·verification_uri 를 실제로 발급한다(실 POST 200).
  - 그 뒤(승인·토큰교환·추론)는 운영자 계정 로그인이 필요해 **이 파일을 돌려야 확인된다**.

쓰는 법:
    python3 shared/grok_oauth_probe.py
  화면에 뜨는 주소를 폰이나 PC 브라우저로 열고 코드 승인하면 나머지는 자동이다.

산출:
  - 판정 = 화면 마지막 3줄(통과 / 거절 / 로그인 실패)
  - 로그 = ./grok_probe_log.json (요청·응답 원문 · 토큰은 앞 12자만 남기고 가린다)
  - 토큰 = ./grok_oauth_token.json (통과 시에만 · 배선 재료 · ⚠ 커밋 금지)

끄는 법: 이 파일을 안 돌리면 끝이다(레포 라이브 코드에 아무것도 안 건다 · 자동 실행 배선 0).
"""
import base64
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

# ── xAI 공개 데스크톱 클라이언트(비밀키 없는 public client · 값 원천 = hermes-agent PR #26534 실측)
CLIENT_ID = os.environ.get("XAI_OAUTH_CLIENT_ID", "b1a00492-073a-47ea-816f-4c329264a828")
SCOPE = os.environ.get("XAI_OAUTH_SCOPE", "openid profile email offline_access grok-cli:access api:access")
DISCOVERY = "https://auth.x.ai/.well-known/openid-configuration"
API_BASE = os.environ.get("XAI_BASE_URL", "https://api.x.ai/v1")

# 추론 1콜에 쓸 후보 모델(앞에서부터 시도 · 모델명 거절과 자격 거절을 갈라내려고 여러 개)
MODELS = [m for m in (os.environ.get("XAI_PROBE_MODELS") or "grok-4.5,grok-4.3,grok-3,grok-beta").split(",") if m]

LOG = []
HERE = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(os.getcwd(), "grok_probe_log.json")
TOKEN_PATH = os.path.join(os.getcwd(), "grok_oauth_token.json")


def _mask(s):
    """토큰류는 앞 12자만 남긴다(로그가 곧 자격증명이 되는 사고 차단)."""
    if not isinstance(s, str) or len(s) <= 12:
        return s
    return s[:12] + f"…<{len(s)}자 가림>"


def _mask_obj(o):
    if isinstance(o, dict):
        return {k: (_mask(v) if k in ("access_token", "refresh_token", "id_token", "device_code") else _mask_obj(v))
                for k, v in o.items()}
    if isinstance(o, list):
        return [_mask_obj(x) for x in o]
    return o


def _log(step, **kw):
    LOG.append({"step": step, "t": time.strftime("%Y-%m-%d %H:%M:%S"), **_mask_obj(kw)})
    try:
        with open(LOG_PATH, "w", encoding="utf-8") as f:
            json.dump(LOG, f, ensure_ascii=False, indent=2)
    except Exception:  # noqa: BLE001
        pass


def _req(url, data=None, headers=None, method=None, timeout=60):
    """표준 라이브러리만 쓴다(설치물 0). (상태코드, 본문텍스트, 파싱된 json|None) 반환 · 예외는 안 던진다."""
    body = None
    hdr = dict(headers or {})
    if isinstance(data, dict):
        body = urllib.parse.urlencode(data).encode()
        hdr.setdefault("Content-Type", "application/x-www-form-urlencoded")
    elif isinstance(data, (bytes, str)):
        body = data.encode() if isinstance(data, str) else data
    req = urllib.request.Request(url, data=body, headers=hdr, method=method or ("POST" if body else "GET"))
    ctx = ssl.create_default_context()
    ca = "/root/.ccr/ca-bundle.crt"   # 원격 실행 환경의 프록시 CA(있을 때만 · 운영자 PC 에선 무시된다)
    if os.path.exists(ca):
        try:
            ctx.load_verify_locations(ca)
        except Exception:  # noqa: BLE001
            pass
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            txt = r.read().decode("utf-8", "replace")
            code = r.getcode()
    except urllib.error.HTTPError as e:
        txt = e.read().decode("utf-8", "replace")
        code = e.code
    except Exception as e:  # noqa: BLE001
        return 0, f"{type(e).__name__}: {e}", None
    try:
        return code, txt, json.loads(txt)
    except Exception:  # noqa: BLE001
        return code, txt, None


def _die(title, detail, hint=""):
    print("")
    print("=" * 62)
    print(f"❌ {title}")
    print("=" * 62)
    print(detail.strip()[:1500])
    if hint:
        print("")
        print(hint)
    print("")
    print(f"기록: {LOG_PATH}")
    sys.exit(1)


def main():
    print("")
    print("┌" + "─" * 60 + "┐")
    print("│ 그록 구독 자격 판정기 — 로그인 1회 + 실제 호출 1회        │")
    print("└" + "─" * 60 + "┘")

    # ① 발견 문서 = 엔드포인트 원천(하드코딩 대신 xAI 가 알려주는 값을 쓴다 = 주소가 바뀌어도 따라간다)
    code, txt, doc = _req(DISCOVERY, timeout=30)
    _log("discovery", http=code, body=(doc or txt))
    if code != 200 or not doc:
        _die("인증 서버 정보를 못 받았다", f"HTTP {code}\n{txt}",
             "네트워크나 방화벽 문제일 수 있다. 브라우저로 https://auth.x.ai/.well-known/openid-configuration 가 열리는지 확인.")
    dev_url = doc.get("device_authorization_endpoint")
    tok_url = doc.get("token_endpoint")
    if not dev_url or not tok_url:
        _die("이 서버는 코드 방식 로그인을 안 받는다", json.dumps(doc, ensure_ascii=False, indent=2)[:1200])
    print(f"  인증 서버 확인 완료")

    # ② 코드 발급
    code, txt, dev = _req(dev_url, data={"client_id": CLIENT_ID, "scope": SCOPE}, timeout=30)
    _log("device_code", http=code, body=(dev or txt))
    if code != 200 or not dev or not dev.get("user_code"):
        _die("로그인 코드 발급이 거절됐다", f"HTTP {code}\n{txt}",
             "클라이언트 값이 바뀌었을 수 있다. XAI_OAUTH_CLIENT_ID 환경변수로 다른 값을 넣어 다시 시도할 수 있다.")

    uri_full = dev.get("verification_uri_complete") or dev.get("verification_uri")
    interval = int(dev.get("interval") or 5)
    expires = int(dev.get("expires_in") or 900)

    print("")
    print("  ┌──────────────────────────────────────────────────────┐")
    print("  │ 아래 주소를 폰이나 브라우저로 열고 승인해라           │")
    print("  └──────────────────────────────────────────────────────┘")
    print("")
    print(f"    주소 : {uri_full}")
    print(f"    코드 : {dev.get('user_code')}")
    print("")
    print(f"  (제한 시간 {expires // 60}분 · 승인하면 여기서 자동으로 넘어간다)")
    print("")
    sys.stdout.flush()

    # ③ 승인 대기
    deadline = time.time() + expires
    tokens = None
    waited = 0
    while time.time() < deadline:
        time.sleep(interval)
        waited += interval
        code, txt, tk = _req(tok_url, data={
            "client_id": CLIENT_ID,
            "device_code": dev["device_code"],
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
        }, timeout=30)
        err = (tk or {}).get("error")
        if code == 200 and tk and tk.get("access_token"):
            tokens = tk
            break
        if err == "authorization_pending":
            if waited % 30 < interval:
                print(f"  … 승인 기다리는 중 ({waited}초)")
                sys.stdout.flush()
            continue
        if err == "slow_down":
            interval += 5
            continue
        if err in ("expired_token", "access_denied"):
            _log("device_poll_fail", http=code, body=(tk or txt))
            _die("로그인이 끝나기 전에 끊겼다", f"사유: {err}\n{txt}", "다시 실행해서 승인해라.")
        _log("device_poll_other", http=code, body=(tk or txt))
    if not tokens:
        _die("제한 시간 안에 승인이 안 됐다", "다시 실행해라.")

    _log("token_ok", http=200, body=tokens)
    print("")
    print("  ✅ 1단계 통과 — 로그인 성공(내 계정이 인증됐다)")

    at = tokens["access_token"]
    auth = {"Authorization": f"Bearer {at}", "Content-Type": "application/json"}

    # ④ 내 자격이 뭘로 보이는지(신원 확인 · 실패해도 진행한다)
    code, txt, who = _req(doc.get("userinfo_endpoint") or "https://auth.x.ai/oauth2/userinfo",
                          headers={"Authorization": f"Bearer {at}"}, method="GET", timeout=30)
    _log("userinfo", http=code, body=(who or txt))
    if code == 200 and who:
        print(f"     계정: {who.get('email') or who.get('name') or who.get('sub')}")

    # ⑤ 부를 수 있는 모델 목록(자격 거절이면 여기서 이미 갈린다)
    code, txt, ml = _req(f"{API_BASE}/models", headers={"Authorization": f"Bearer {at}"}, method="GET", timeout=40)
    _log("models", http=code, body=(ml or txt)[:4000] if isinstance(ml, str) else (ml or txt))
    avail = []
    if code == 200 and isinstance(ml, dict):
        avail = [m.get("id") for m in (ml.get("data") or []) if m.get("id")]
        print(f"     쓸 수 있는 모델 {len(avail)}개: {', '.join(avail[:8])}{' …' if len(avail) > 8 else ''}")
    else:
        print(f"     모델 목록은 못 받았다(HTTP {code}) — 그래도 호출은 시도한다")

    # ⑥ 실제 1콜 — 이게 판정의 전부다
    order = ([m for m in avail if m in MODELS] + [m for m in MODELS if m not in avail] + avail)[:6]
    seen, last = set(), None
    for m in order:
        if not m or m in seen:
            continue
        seen.add(m)
        payload = json.dumps({
            "model": m,
            "messages": [{"role": "user", "content": "한국어로 '통과'라고만 답해."}],
            "max_tokens": 16,
        }, ensure_ascii=False)
        code, txt, res = _req(f"{API_BASE}/chat/completions", data=payload, headers=auth, timeout=90)
        _log("infer", model=m, http=code, body=(res or txt)[:2000] if isinstance(res or txt, str) else (res or txt))
        print(f"     호출 시도 [{m}] → HTTP {code}")
        last = (m, code, txt, res)
        if code == 200 and res:
            try:
                say = res["choices"][0]["message"]["content"]
            except Exception:  # noqa: BLE001
                say = str(res)[:200]
            try:
                with open(TOKEN_PATH, "w", encoding="utf-8") as f:
                    json.dump({"access_token": at, "refresh_token": tokens.get("refresh_token"),
                               "expires_in": tokens.get("expires_in"), "client_id": CLIENT_ID,
                               "scope": SCOPE, "token_endpoint": tok_url, "api_base": API_BASE,
                               "model_ok": m, "saved_at": time.strftime("%Y-%m-%d %H:%M:%S")}, f,
                              ensure_ascii=False, indent=2)
                os.chmod(TOKEN_PATH, 0o600)
            except Exception:  # noqa: BLE001
                pass
            print("")
            print("=" * 62)
            print("✅ 통과 — 네 구독 자격으로 그록이 실제로 대답했다")
            print("=" * 62)
            print(f"  모델   : {m}")
            print(f"  대답   : {str(say).strip()[:200]}")
            print(f"  토큰   : {TOKEN_PATH} (갱신용 열쇠 포함 · ⚠ 커밋하지 마라)")
            print(f"  기록   : {LOG_PATH}")
            print("")
            print("  → 이 파일 2개를 클로드 세션에 주면 그대로 배선한다.")
            print("")
            return 0
        if code == 404 and "model" in (txt or "").lower():
            continue   # 모델 이름 문제 = 다음 후보로

    m, code, txt, res = last if last else ("", 0, "시도 자체를 못 했다", None)
    reason = ""
    if isinstance(res, dict):
        reason = str(res.get("error") or res.get("message") or "")
    print("")
    print("=" * 62)
    print("❌ 거절 — 로그인은 됐는데 호출을 막았다")
    print("=" * 62)
    print(f"  마지막 시도 : {m} → HTTP {code}")
    print(f"  서버가 한 말 : {(reason or txt).strip()[:600]}")
    print("")
    if code == 403:
        print("  403 = 자격 거절이다. 구독은 살아 있는데 xAI 가 이 통로를 안 열어준 것.")
    elif code == 401:
        print("  401 = 토큰 문제다. 다시 실행해서 로그인부터 해봐라.")
    elif code == 429:
        print("  429 = 한도다. 자격은 있다는 뜻이니 잠시 뒤 다시 돌려라.")
    print(f"\n  기록 : {LOG_PATH}  (이 파일을 클로드 세션에 주면 원인 판정한다)")
    print("")
    return 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n중단됨.")
        sys.exit(130)
