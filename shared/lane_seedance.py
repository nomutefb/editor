#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lane_seedance.py — 시댄스 통로(창구 = 힉스필드 · 계약 정본 = `lane.py`).

운영자 260812 = 「키값만 깃 시크릿에 넣으면 바로 테스트」. 그 열쇠가 여기로 들어온다.

## 자격 (실측 규격 · 260812 실호출로 확인)
창구 = https://fnf-device-auth.higgsfield.ai
  POST /authorize            → {device_code, verification_uri, expires_in 900, interval 3}   ← 판정기 몫
  POST /token {device_code}  → {access_token, refresh_token, expires_in, refresh_expires_in}  ← 판정기 몫
  POST /refresh {refresh_token} → 같은 모양                                                   ← **러너가 쓰는 것**
  POST /validate {token}     → {user_id}
⚠ 클라이언트 등록이 필요 없다 = 비밀값이 **갱신 열쇠 1개**로 끝난다.
⚠ /refresh 가 새 갱신 열쇠를 실어 보낼 수 있다(회전형 가능성) → 왔을 때만 저장·되쓰기.
  회전형이든 아니든 이 계약 하나가 양쪽을 흡수한다(그록 260811 실사고의 교훈).

## 창구 (실측 · 260812)
MCP = https://mcp.higgsfield.ai/mcp · `Authorization: Bearer <접속 열쇠>`
  무자격 요청은 401 + `www-authenticate: Bearer … scope="openid email offline_access"`
  = 위 기기 코드 흐름이 주는 그 자격이 맞다.

## ⚠ 확인된 것과 아직 아닌 것을 가른다([1] 정직)
확인 = 자격 4창구 · MCP 401 규격 · `balance` 회신 모양 · `generate_video{get_cost:true}` 견적 실값
       (시댄스 2.5 720p 30초 = 195 크레딧 · 2.0 1080p 15초 = 135 · 그록 720p 15초 = 67.5).
미확인 = 발사 응답 모양 · 실패 응답 생김새 · **실패 시 크레딧 환불 여부** · 참조 올리기 도구 규격 ·
       기다리기 회당 상한. → 이 축들은 `--check`(과금 0)와 첫 실호출이 확정한다. 지어내지 않는다.

CONTRACT: check_grok_sb_chain
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lane import LaneError     # noqa: E402

AUTH = os.environ.get("HF_AUTH_BASE", "https://fnf-device-auth.higgsfield.ai")
MCP = os.environ.get("HF_MCP_URL", "https://mcp.higgsfield.ai/mcp")
SECRET_NAME = "HIGGSFIELD_REFRESH_TOKEN"
PROTO = "2025-06-18"
# 브라우저 서명 — 창구 앞단이 파이썬 기본 서명을 막는다(위 _post 주석 참조)
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36")

# ── 프리셋(운영자 260812 확정 · 산출 = 세로 30초 쇼츠) ─────────────────────────
#   A = 시댄스 2.5 720p 30초 한 발(이음매 0) · B = 시댄스 2.0 1080p 15초 두 발(화질 최상)
#   ⚠ 2.5 는 1080p 이상을 **아예 지원 안 한다**(창구 목록 실측 = 480p·720p 뿐) —
#     「이음매 없는 30초」와 「FHD」는 지금 동시에 안 된다. 그래서 프리셋이 갈린다.
PRESETS = {
    "A": {"model": "seedance_2_5", "shot_sec": 30, "sec_max": 30, "res": "720p",
          "extra": {"mode": "omni_reference"}},
    "B": {"model": "seedance_2_0", "shot_sec": 15, "sec_max": 15, "res": "1080p",
          "extra": {"mode": "std"}},
}
PRESET = PRESETS.get((os.environ.get("SD_PRESET") or "A").strip().upper(), PRESETS["A"])

# ── 상수 8(계약) ──────────────────────────────────────────────────────────────
NAME = "seedance"
SHOT_SEC = int(os.environ.get("SD_SHOT_SEC") or PRESET["shot_sec"])
SEC_MAX = PRESET["sec_max"]
RATIOS = ("16:9", "9:16", "1:1", "4:3", "3:4", "21:9")   # 창구 목록 실측
REF_CAP_TECH = 9                                          # 참조 상한 — 창구 문서 기준(미검증 = --check 축)
EMBED_MAX = 8_000_000
FAIL_COSTS = None      # ⚠ **미확인** — 실패분 크레딧 환불 여부. None = 「모른다」(재시도 정책이 이 값을 본다)
COST_KIND = "credit"   # 크레딧 과금 · 달러 환산율은 요금제 종속이라 **지어내지 않는다**

_TOK = {"access": None, "exp": 0.0}
_SESS = {"id": None, "n": 0}


# ── 자격 ──────────────────────────────────────────────────────────────────────
def _post(url, body, *, token=None, timeout=60, accept="application/json"):
    data = json.dumps(body or {}).encode()
    # ⚠ **브라우저 서명이 필수다**(260812 첫 실행 실측) — 파이썬 기본 서명으로 나가면 창구 앞단이
    #   `1010 browser_signature_banned` 로 통째 거절한다(자격도 창구도 멀쩡한데 403). 같은 함정을
    #   같은 날 참조 그림 받기에서도 밟았다 = 이 레포에서 **두 번째**라 통로 진입부에 못박는다.
    hd = {"Content-Type": "application/json", "Accept": accept, "User-Agent": UA}
    if token:
        hd["Authorization"] = "Bearer " + token
        hd["MCP-Protocol-Version"] = PROTO
    if _SESS["id"] and url == MCP:
        hd["Mcp-Session-Id"] = _SESS["id"]
    req = urllib.request.Request(url, data=data, headers=hd, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            if url == MCP and r.headers.get("Mcp-Session-Id"):
                _SESS["id"] = r.headers["Mcp-Session-Id"]
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")[:600]
    except Exception as e:  # noqa: BLE001
        return 0, "{}: {}".format(type(e).__name__, e)


def _persist(rt):
    """새 갱신 열쇠를 깃 비밀값에 되써 넣는다 — 없으면 **다음 발사가 죽는다**(그록 260811 실사고).

    ⚠ 봉인·전송은 `grok_api._persist_secret` 정본을 그대로 쓴다(사본 0). 그 함수가 저장할
      비밀값 이름을 인자로 받으므로 벤더가 섞이지 않는다 — 인자를 안 주면 그록 열쇠를 덮어쓴다.
    """
    try:
        import grok_api as gk   # noqa: PLC0415  봉인·PUT 만 빌린다(깃허브 축이라 벤더 무관)
        gk._persist_secret(rt, name=SECRET_NAME)
    except Exception as e:      # noqa: BLE001
        print("::warning::갱신 열쇠 되쓰기 실패(다음 발사가 죽을 수 있다): {}".format(str(e)[:200]))


def fresh_token():
    """접속 열쇠를 얻는다(수명 안이면 재사용). 갱신 열쇠가 새로 오면 저장·되쓰기."""
    if _TOK["access"] and time.time() < _TOK["exp"]:
        return _TOK["access"]
    rt = (os.environ.get(SECRET_NAME) or "").strip()
    if not rt:
        raise LaneError("힉스필드 갱신 열쇠가 없다 — 판정기(노뮤트_힉스필드자격_확인.bat)를 돌려 "
                        "{} 비밀값에 넣어라".format(SECRET_NAME), retryable=False, auth_dead=True)
    code, txt = _post(AUTH + "/refresh", {"refresh_token": rt})
    if code != 200:
        raise LaneError("자격 갱신 실패({}) — 판정기를 다시 돌려 열쇠를 새로 받아야 한다".format(code),
                        retryable=False, auth_dead=True, body=txt)
    try:
        d = json.loads(txt)
    except Exception:  # noqa: BLE001
        raise LaneError("자격 갱신 응답을 못 읽었다", retryable=False, auth_dead=True, body=txt) from None
    _TOK["access"] = d.get("access_token")
    # ⚠ 수명은 **응답 실값**을 쓴다 — 그록의 5시간 상수를 이식하면 벤더가 다를 때 조용히 어긋난다.
    _TOK["exp"] = time.time() + max(60, int(d.get("expires_in") or 900) - 60)
    new_rt = d.get("refresh_token")
    if new_rt and new_rt != rt:      # 회전형일 때만 저장 = 비회전형도 같은 코드로 옳게 돈다
        os.environ[SECRET_NAME] = new_rt
        _persist(new_rt)
    if not _TOK["access"]:
        raise LaneError("접속 열쇠가 응답에 없다", retryable=False, auth_dead=True, body=txt)
    return _TOK["access"]


# ── 창구(MCP) ────────────────────────────────────────────────────────────────
def _sse(txt):
    """응답이 이벤트 스트림이면 그 안의 JSON 을 꺼낸다(창구가 두 형식을 다 쓴다)."""
    for line in txt.splitlines():
        if line.startswith("data:"):
            try:
                return json.loads(line[5:].strip())
            except Exception:  # noqa: BLE001
                continue
    return None


def _rpc(method, params, token):
    _SESS["n"] += 1
    code, txt = _post(MCP, {"jsonrpc": "2.0", "id": _SESS["n"], "method": method, "params": params},
                      token=token, accept="application/json, text/event-stream")
    if code == 401:
        raise LaneError("자격이 거절됐다(401) — 판정기를 다시 돌려 열쇠를 새로 받아야 한다",
                        retryable=False, auth_dead=True, body=txt)
    if code not in (200, 202):
        raise LaneError("창구 오류 HTTP {}".format(code), body=txt)
    obj = None
    try:
        obj = json.loads(txt)
    except Exception:  # noqa: BLE001
        obj = _sse(txt)
    if obj is None:
        raise LaneError("창구 응답을 못 읽었다", body=txt[:300])
    if obj.get("error"):
        msg = json.dumps(obj["error"], ensure_ascii=False)[:300]
        low = msg.lower()
        if "credit" in low or "balance" in low or "insufficient" in low:
            raise LaneError("크레딧이 모자란다 — 충전하거나 요금제를 올려야 한다",
                            retryable=False, no_credit=True, body=msg)
        raise LaneError("창구가 거절했다 — {}".format(msg), body=msg)
    return obj.get("result") or {}


def _handshake(token):
    if _SESS["id"]:
        return
    _rpc("initialize", {"protocolVersion": PROTO, "capabilities": {},
                        "clientInfo": {"name": "nomute-sb", "version": "1.0"}}, token)
    _post(MCP, {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
          token=token, accept="application/json, text/event-stream")


def call(tool, args, token):
    """도구 하나를 부른다. 회신 본문이 글자에 담긴 JSON 이면 풀어서 준다."""
    _handshake(token)
    r = _rpc("tools/call", {"name": tool, "arguments": args}, token)
    for c in (r.get("content") or []):
        if c.get("type") == "text":
            try:
                return json.loads(c["text"])
            except Exception:  # noqa: BLE001
                return {"text": c["text"]}
    return r.get("structuredContent") or r


# ── 계약 구현 ────────────────────────────────────────────────────────────────
def _params(seconds, ratio, cost_only=False):
    """견적과 발사가 **같은 조립 함수**를 쓴다 — 두 벌이면 「승인한 금액과 다른 금액이 나간다」."""
    p = {"model": PRESET["model"], "duration": int(seconds), "resolution": PRESET["res"],
         "generate_audio": True}
    p.update(PRESET["extra"])
    if ratio:
        p["aspect_ratio"] = ratio
    # ⚠ 무제한 사용 여부를 **명시**한다 — 미전달이면 창구가 「무제한 쓸까요」를 되묻고
    #   **잡을 제출하지 않는다**(사람 없는 러너에선 무성 무산출이 초록으로 통과한다).
    p["use_unlim"] = False
    if cost_only:
        p["get_cost"] = True
    return p


def balance(token=None):
    """잔액 — 자격 실증을 겸한다(과금 0)."""
    return call("balance", {}, token or fresh_token())


def estimate(seconds, ratio=None, token=None):
    """발사 전 견적(제출 없이 크레딧만 회신 · **과금 0**). 반환 = 크레딧 수 또는 None."""
    # ⚠ 단건 도구는 인자를 **한 겹 감싼다**(`{"params": {...}}`) — 일괄 도구의 `{"requests":[…]}` 와
    #   모양이 다르다. 첫 실행이 `Invalid input at params` 로 그 자리를 정확히 지목했다(260812).
    d = call("generate_video", {"params": dict(_params(seconds, ratio, cost_only=True),
                                               prompt="cost check")}, token or fresh_token())
    return _credits(d)


def _credits(d):
    """크레딧 수를 꺼낸다.

    ⚠ 창구는 **회신을 사람 읽는 글자로도 준다**(260812 실측 = 잔액이 `Credits: 3060 | Plan: ultra`).
      숫자 자리만 보면 첫 실행처럼 조용히 None 이 되고, 그러면 예산 검문이 **없는 것과 같아진다** —
      돈 나가기 직전의 유일한 문이라 여기서 지어내지도, 조용히 넘기지도 않는다.
    """
    if not isinstance(d, dict):
        return None
    c = d.get("cost") or {}
    v = c.get("credits_exact", c.get("credits"))
    if v is None:
        txt = d.get("text") or json.dumps(d, ensure_ascii=False)
        m = re.search(r"([\d,]+(?:\.\d+)?)\s*(?:credits?|크레딧)", txt, re.I) or \
            re.search(r"(?:credits?|크레딧)\D{0,4}([\d,]+(?:\.\d+)?)", txt, re.I)
        if m:
            v = m.group(1).replace(",", "")
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def refs_payload(urls, embed=True):
    """참조 수송 — 창구가 **주소 직전달을 금지**한다(올려서 받은 번호로만 받는다).

    ⚠ 올리기 도구 규격은 **실측 확인분**이다(260812 실호출 = 주소를 주면 `media_id` 를 돌려준다 ·
      상한 50MB). 주소를 그대로 돌려주고 `start()` 가 번호로 바꾼다.
    """
    return list(urls), "주소(번호 변환은 발사 직전)"


def _media_ids(urls, token):
    out = []
    for u in urls:
        d = call("media_import_url", {"url": u}, token)
        mid = (d or {}).get("media_id") or (d or {}).get("id")
        if not mid:
            raise LaneError("참조 그림을 창구에 못 올렸다(회신에 번호가 없다)", body=json.dumps(d)[:200])
        out.append(mid)
    return out


def start(prompt, *, token, refs=None, seconds=None, ratio=None):
    """발사 = **헤드리스 일괄 도구**로 쏜다.

    ⚠ 단건 도구(`generate_video`)는 **화면 위젯용**이다(창구 설명 명시) — 사람 없는 러너는
      일괄 도구를 써야 작업 번호를 그대로 돌려받는다. 대신 일괄에는 견적 값을 못 싣는다
      (`get_cost` 미지원) → 견적은 단건 도구로 따로 부른다(`estimate`).
    ⚠ 참조 역할 키는 **단수** `role` 이고 값은 **번호**다(주소 직전달 금지 = 창구 스키마 명시).
    """
    args = dict(_params(seconds or SHOT_SEC, ratio), prompt=prompt)
    if refs:
        args["medias"] = [{"value": m, "role": "image_references"} for m in _media_ids(refs, token)]
    d = call("generate_video_batch", {"requests": [{"index": 0, "params": args}]}, token)
    jid = _job_id(d)
    if not jid:
        # ⚠ 회신 모양이 미확인 축이라 **원문을 그대로 남긴다** — 다음 세션이 추측으로 메우지 않게.
        raise LaneError("발사는 됐는데 작업 번호를 못 찾았다 — 회신 모양을 확인해야 한다",
                        body=json.dumps(d, ensure_ascii=False)[:600])
    return jid


def _job_id(d):
    """일괄 발사 회신에서 작업 번호를 꺼낸다(모양이 미확인이라 흔한 자리를 훑는다)."""
    if not isinstance(d, dict):
        return None
    for key in ("jobs", "results", "requests"):
        arr = d.get(key)
        if isinstance(arr, list) and arr:
            j = arr[0]
            if isinstance(j, dict):
                for k in ("job_id", "id", "request_id"):
                    if j.get(k):
                        return j[k]
    for k in ("job_id", "id", "request_id"):
        if d.get(k):
            return d[k]
    return None


def wait(job_id, *, token):
    """완료 대기 — 기다리기 도구가 **회당 상한**이 있어 총상한은 러너 몫이다."""
    cap = int(os.environ.get("SD_POLL_MAX_SEC", "1200"))
    t0 = time.time()
    while time.time() - t0 < cap:
        # ⚠ 기다리기 도구는 **회당 15초가 상한**이다(창구 스키마) → 총상한은 우리가 센다.
        #   상한 없이 붙이면 큐 고착이 잡 시간을 통째로 태운다.
        d = call("jobs_wait", {"jobs": [{"index": 0, "job_id": job_id}], "timeout_seconds": 15}, token)
        jobs = (d or {}).get("jobs") or (d or {}).get("results") or []
        j = jobs[0] if jobs else (d or {})
        st = str(j.get("status") or "").lower()
        url = j.get("url") or j.get("output_url") or (j.get("result") or {}).get("url")
        if url:
            return {"url": url, "duration": j.get("duration"), "cost": float(j.get("credits") or 0)}
        if st in ("failed", "error", "canceled", "cancelled"):
            raise LaneError("창구가 실패로 끝냈다 — {}".format(str(j.get("error") or st)[:160]),
                            body=json.dumps(j, ensure_ascii=False)[:400])
        time.sleep(max(1, int((d or {}).get("poll_after_seconds") or 3)))
    raise LaneError("{}분 안에 안 끝났다 — 큐가 밀린 상태다. 손으로 다시 시도".format(cap // 60))


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (nomute)"})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return r.read()
    except Exception as e:  # noqa: BLE001
        raise LaneError("산출물을 못 받았다: {}".format(str(e)[:160])) from None


def ref_lock_clause(n):
    """참조 잠금 절. ⚠ 시댄스가 그록의 슬롯 지목 문법을 받는지 **미확인** — 지목 없이 뜻만 쓴다."""
    return "Keep the people, wardrobe, and setting identical to the reference images."


def sound_clause(on, sfx):
    """소리 절. ⚠ 시댄스는 소리를 **파라미터로** 끈다(`generate_audio`) — 문장은 보조."""
    if on:
        return ["Sound: {}. No music.".format("; ".join(sfx)) if sfx
                else "Sound: ambient room tone and the natural sounds of the action, no music."]
    return ["The only sounds are faint ambient room tone. No spoken words."]


def too_big(e):
    return False   # 참조를 번호로 올리므로 본문 몸집 축이 없다


def classify(e):
    return e if isinstance(e, LaneError) else LaneError(str(e)[:200])


# ── 자격·견적 확인(과금 0) ────────────────────────────────────────────────────
def _check():
    print("── 시댄스 통로 확인(과금 0) ──")
    print("프리셋 {} · 모델 {} · {} · 한 발 {}초".format(
        (os.environ.get("SD_PRESET") or "A").upper(), PRESET["model"], PRESET["res"], SHOT_SEC))
    tok = fresh_token()
    print("① 자격 ✓ (접속 열쇠 {}자)".format(len(tok)))
    b = balance(tok)
    print("② 잔액 ✓ {}".format(json.dumps(b, ensure_ascii=False)[:200]))
    raw = call("generate_video", {"params": dict(_params(SHOT_SEC, os.environ.get("SD_RATIO") or "9:16",
                                                         cost_only=True), prompt="cost check")}, tok)
    cr = _credits(raw)
    print("③ 견적 원문: {}".format(json.dumps(raw, ensure_ascii=False)[:300]))
    if cr is None:
        print("::error::견적 숫자를 못 읽었다 — 예산 검문이 무력해진다(위 원문을 보고 파서를 고쳐라)")
        return 1
    print("③ 견적 ✓ {}초 = {} 크레딧".format(SHOT_SEC, cr))
    print("── 통과 — 발사만 남았다(이 확인은 크레딧을 쓰지 않았다) ──")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(_check())
    except LaneError as e:
        print("::error::시댄스 통로 확인 실패 — {}".format(e.why))
        if e.body:
            print("   원문: {}".format(str(e.body)[:400]))
        sys.exit(1)
