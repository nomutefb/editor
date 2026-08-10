"""grok_api — X(엑스) 구독 자격으로 xAI(그록)의 그림·영상을 굽는 단일 통로.

배경(260810 · 운영자 "이거로 편하게 만들 수 있으면 슈퍼그록까지 할 의사도 있음"):
  영상은 지금 `viewer/k.html` 이 **복붙용 프롬프트만** 뽑아주고 운영자가 그 글을 들고 클링 사이트로
  건너가 직접 만든다(`functions/api/k.js` 머리 = 「Kling 복붙 프롬프트」). 그록은 우리가 API 로
  직접 구울 수 있으므로 **건너가는 단계 자체가 사라진다** — 그게 이 모듈의 존재 이유다.

  자격 = API 키(종량제)가 아니라 **구독 OAuth**. 260810 실호출로 통과 확인(계정 muteno@pm.me ·
  grok-4.3 HTTP 200 · 판정기 = `scripts/노뮤트_그록자격_확인.bat`). 즉 이 통로로 나가는 그림·영상은
  **추가 과금 0**(구독료 안에서 돈다) — 이 레포가 종량제로 쓰던 그림 벤더와 성격이 다르다.

⚠ 이 모듈은 **프롬프트를 짓지 않는다.** 문장 설계는 별건(오퍼스 6인 수집 → 정제 → 페이블 검토 축)이고
  여기는 「받은 문장을 어떻게 보내고 어떻게 받아오는가」만 책임진다. 그래야 프롬프트 개정이
  통로를 안 건드린다(= 이 레포가 반복해 겪은 사본 드리프트 차단).

⚠ 계약 앵커(CONTRACT)는 짝 게이트를 만드는 커밋에 함께 단다 — 강제가 없는 선언은
  조용히 낡는다(`check_contract_anchors` 계약 = 고아 앵커 차단).

── 고정값(운영자 260810 "10초 720p는 고정(그록 선택 시), 비율만 선택할 수 있게")
  이 요금제(X Premium+)에서 실제로 도는 값만 화면이 약속한다 — 15초·1080p 를 옵션으로 열면
  거절이 **옵션 화면이 아니라 발사 뒤에** 터진다. 슈퍼그록 승급 시 아래 두 상수만 바꾼다.
"""
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

# ── 자격(구독 OAuth) ───────────────────────────────────────────────────────────
AUTH_TOKEN_URL = "https://auth.x.ai/oauth2/token"
CLIENT_ID = os.environ.get("XAI_OAUTH_CLIENT_ID", "b1a00492-073a-47ea-816f-4c329264a828")
API_BASE = os.environ.get("XAI_BASE_URL", "https://api.x.ai/v1")

# ── 산출 규격(운영자 260810 확정) ─────────────────────────────────────────────
VID_MODEL = os.environ.get("GROK_VID_MODEL", "grok-imagine-video-1.5")
VID_SECONDS = int(os.environ.get("GROK_VID_SECONDS", "10"))     # 슈퍼그록 = 15 까지
VID_RES = os.environ.get("GROK_VID_RES", "720p")                # 슈퍼그록 = 1080p
VID_RATIOS = ("16:9", "9:16", "1:1")                            # 화면이 고르게 하는 유일한 축
IMG_MODEL = os.environ.get("GROK_IMG_MODEL", "grok-imagine-image")
IMG_MODEL_HQ = os.environ.get("GROK_IMG_MODEL_HQ", "grok-imagine-image-quality")

POLL_SEC = 6            # 영상은 몇 분 걸린다(공식 문서) — 6초 간격이면 분당 10회
POLL_MAX_SEC = 900      # 15분 상한(러너 타임아웃보다 짧게)


class GrokError(RuntimeError):
    """호출 실패. code = HTTP 상태(0 = 네트워크), body = 서버가 한 말 원문.

    ⚠ 사유 원문을 반드시 들고 다닌다 — 260807 스모크 경보 사고(사유 0자 경보가 8일 살았다)와 같은 축.
    """

    def __init__(self, code, body, where=""):
        self.code, self.body, self.where = code, body, where
        super().__init__(f"[{where} HTTP {code}] {str(body)[:400]}")


def _req(url, *, data=None, token=None, method=None, timeout=120):
    """(코드, 본문, 파싱된 json|None). 예외는 안 던진다 — 판정은 호출부 몫."""
    hdr = {}
    if token:
        hdr["Authorization"] = f"Bearer {token}"
    body = None
    if isinstance(data, dict) and method != "FORM":
        body = json.dumps(data, ensure_ascii=False).encode()
        hdr["Content-Type"] = "application/json"
    elif method == "FORM":
        body = urllib.parse.urlencode(data).encode()
        hdr["Content-Type"] = "application/x-www-form-urlencoded"
        method = "POST"
    req = urllib.request.Request(url, data=body, headers=hdr,
                                 method=method or ("POST" if body else "GET"))
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            txt = r.read().decode("utf-8", "replace")
            code = r.getcode()
    except urllib.error.HTTPError as e:
        txt, code = e.read().decode("utf-8", "replace"), e.code
    except Exception as e:  # noqa: BLE001
        return 0, f"{type(e).__name__}: {e}", None
    try:
        return code, txt, json.loads(txt)
    except Exception:  # noqa: BLE001
        return code, txt, None


# ── 자격 갱신 ─────────────────────────────────────────────────────────────────
def access_token(refresh_token=None):
    """리프레시 토큰으로 액세스 토큰을 받아온다.

    ⚠ **그록은 갱신할 때마다 리프레시 토큰을 새것으로 바꿔준다(회전).** 그래서 반환값 두 번째를
    호출부가 **반드시 다시 저장**해야 다음 런이 산다 — 안 하면 며칠 뒤 조용히 끊긴다(화면 증상 0).
    저장 자리 = 러너 축이면 레포 시크릿(`.github/scripts/grok_token_store.py` 담당).

    반환 = (액세스 토큰, 새 리프레시 토큰 or None)
    """
    rt = refresh_token or os.environ.get("XAI_REFRESH_TOKEN") or ""
    if not rt:
        raise GrokError(0, "리프레시 토큰이 없다(XAI_REFRESH_TOKEN 미설정)", "auth")
    code, txt, obj = _req(AUTH_TOKEN_URL, method="FORM", data={
        "client_id": CLIENT_ID, "grant_type": "refresh_token", "refresh_token": rt,
    }, timeout=60)
    if code != 200 or not obj or not obj.get("access_token"):
        # invalid_grant = 그 열쇠는 죽었다(재로그인 필요). 그 외 = 일시 장애일 수 있다.
        raise GrokError(code, txt, "auth")
    return obj["access_token"], obj.get("refresh_token")


# ── 그림 ──────────────────────────────────────────────────────────────────────
def make_image(prompt, *, token, n=1, hq=False, fmt="b64_json"):
    """그림 생성. 반환 = [bytes 또는 url 문자열] n개.

    ⚠ 우리 파이프는 받은 바이트를 그대로 R2 에 올린다(재인코딩 0 = `check_image_format` 계약).
    """
    body = {"model": IMG_MODEL_HQ if hq else IMG_MODEL, "prompt": prompt,
            "n": max(1, int(n)), "response_format": fmt}
    code, txt, obj = _req(f"{API_BASE}/images/generations", data=body, token=token, timeout=180)
    if code != 200 or not obj:
        raise GrokError(code, txt, "image")
    out = []
    for d in (obj.get("data") or []):
        if d.get("b64_json"):
            import base64
            out.append(base64.b64decode(d["b64_json"]))
        elif d.get("url"):
            out.append(d["url"])
    if not out:
        raise GrokError(code, txt, "image-empty")
    return out


# ── 영상 ──────────────────────────────────────────────────────────────────────
def start_video(prompt, *, token, ratio="16:9", image=None, refs=None,
                seconds=None, res=None):
    """영상 발사. 반환 = 작업 번호(request_id).

    image = 첫 프레임으로 삼을 그림(data URI 또는 URL) — 운영자 260810 「이미지를 참고할 수 있게」.
    refs  = 참조용 그림 목록(인물·화풍 유지 축 · 첫 프레임 고정과 다른 입력).
    ⚠ 이미지→영상이면 **결과 비율이 그 그림의 비율을 따라간다**(공식 문서) → 비율 칩은 그림이
      없을 때만 실효. 화면이 그걸 모르면 「9:16 골랐는데 16:9 가 나왔다」로 보인다.
    """
    body = {
        "model": VID_MODEL,
        "prompt": prompt,
        "duration": int(seconds or VID_SECONDS),
        "resolution": res or VID_RES,
    }
    if ratio in VID_RATIOS and not image:
        body["aspect_ratio"] = ratio
    if image:
        body["image"] = image
    if refs:
        body["reference_images"] = list(refs)
    code, txt, obj = _req(f"{API_BASE}/videos/generations", data=body, token=token, timeout=120)
    if code != 200 or not obj or not obj.get("request_id"):
        raise GrokError(code, txt, "video-start")
    return obj["request_id"]


def wait_video(request_id, *, token, on_tick=None, max_sec=POLL_MAX_SEC):
    """완료까지 기다린다. 반환 = {url, duration, ...}.

    ⚠ 폴링 중 일시 오류(5xx·네트워크)는 삼키고 계속 돈다 — 몇 분짜리 작업을 한 번의 딸꾹질로
      버리면 그 판이 통째로 날아간다. 확정 실패(failed·expired)와 상한 초과만 예외로 올린다.
    """
    t0 = time.time()
    while time.time() - t0 < max_sec:
        time.sleep(POLL_SEC)
        code, txt, obj = _req(f"{API_BASE}/videos/{request_id}", token=token, timeout=60)
        if code != 200 or not obj:
            if code in (401, 403, 404):
                raise GrokError(code, txt, "video-poll")
            continue
        st = obj.get("status")
        if callable(on_tick):
            try:
                on_tick(st, int(time.time() - t0))
            except Exception:  # noqa: BLE001
                pass
        if st == "done":
            v = obj.get("video") or {}
            if not v.get("url"):
                raise GrokError(code, txt, "video-done-nourl")
            return v
        if st in ("failed", "expired"):
            raise GrokError(code, txt, f"video-{st}")
    raise GrokError(0, f"{max_sec}초 안에 안 끝났다(작업번호 {request_id})", "video-timeout")


def fetch(url, *, timeout=300):
    """완성된 영상·그림 바이트를 받아온다(결과 주소는 수명이 있다 = 받는 즉시 R2 로 옮긴다)."""
    code, txt, _ = 0, "", None
    try:
        with urllib.request.urlopen(urllib.request.Request(url), timeout=timeout) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        code, txt = e.code, e.read().decode("utf-8", "replace")[:300]
    except Exception as e:  # noqa: BLE001
        code, txt = 0, f"{type(e).__name__}: {e}"
    raise GrokError(code, txt, "fetch")
