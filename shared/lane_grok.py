#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lane_grok.py — 그록 통로(계약 정본 = `lane.py`).

⚠ 이 파일은 **옮겨온 것이지 새로 쓴 게 아니다.** 러너에 흩어져 있던 그록 결합 자리를
  계약 뒤로 모았을 뿐이고, 값·문구·순서는 260812 시점 러너와 바이트 단위로 같다.
  (새 판단을 섞으면 「통로화하다 조용히 동작이 바뀌었다」가 되고, 그건 이 레포가
   반복해 겪은 사고 모양이다.)

CONTRACT: check_grok_sb_chain
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".github", "scripts"))
import grok_api as gk          # noqa: E402  구독 자격 통로(벤더 원본)
import thumb_gen as tg         # noqa: E402  http_image = 우리 저장소에서 받는 정본 손
from lane import LaneError     # noqa: E402

# ── 상수 8 ────────────────────────────────────────────────────────────────────
NAME = "grok"
# ⚠ **한 발 = 10초 고정**(운영자 260812) — 콘티 컷을 이 초로 묶는다. 롤백 레버 = env 1줄.
SHOT_SEC = int(os.environ.get("GROK_CUT_SEC") or "10")
SEC_MAX = 15                   # 엔진 상한(260812 실측 = 15초까지 실제로 나온다) · SHOT_SEC 과 다른 값
RATIOS = gk.VID_RATIOS
REF_CAP_TECH = gk.REF_MAX      # 기술 한도 7 — 우리 운영 계약(2 기본·3 사유)과 별개
EMBED_MAX = int(os.environ.get("GROK_REF_EMBED_MAX") or "900000")
EMBED_SIDE = 1280              # 줄일 때 긴 변(참조 모드 산출이 720p 상한이라 이만하면 넉넉)
FAIL_COSTS = False             # 260812 실측 = 실패한 호출은 청구가 0(그래서 1회 재시도가 공짜에 가깝다)
COST_KIND = "usd"              # 응답이 청구 실값을 실어 준다


def fresh_token():
    try:
        return gk.fresh_token()
    except gk.GrokError as e:
        raise classify(e) from None


# ── 참조 수송 ────────────────────────────────────────────────────────────────
# ⚠ 실사고 = 260812 `260812-bushouse-lib` 영상1이 참조 그림 다운로드 중단으로 죽었다 —
#   우리가 보낸 건 **주소**였고 그 주소를 내려받는 주체는 xAI 서버다. 그 다운로드가 끊기면
#   우리 코드·프롬프트가 전부 정상이어도 그 편이 통째로 실패한다(같은 그림으로 다른 편은 성공).
#   → 바이트를 본문에 실으면 그 다운로드 자체가 사라져 이 실패 종류가 구조적으로 소멸한다.
def _one(url):
    """참조 1장을 바이트로 쥔다(필요하면 줄여서). 실패 = 예외 → 부르는 쪽이 주소로 내려앉는다."""
    # ⚠ 받아오는 손은 `thumb_gen.http_image` 정본을 쓴다 — 맨 urllib 은 파이썬 기본 서명으로
    #   나가서 우리 저장소 앞단이 403(1010)으로 막는다(260812 실측). 그걸 모르고 넘어가면
    #   바이트 적재가 매번 조용히 실패해 주소 방식으로 되돌아간다 = 봉합 무효.
    raw, _ct, _ext = tg.http_image(url)
    if not raw:
        raise RuntimeError("참조 그림을 못 받았다: " + url[:80])
    if len(raw) <= EMBED_MAX:
        return raw
    from PIL import Image                       # noqa: PLC0415  워크플로가 이 스텝에서 깐다
    im = Image.open(io.BytesIO(raw)).convert("RGB")
    if max(im.size) > EMBED_SIDE:
        r = EMBED_SIDE / float(max(im.size))
        im = im.resize((max(1, int(im.width * r)), max(1, int(im.height * r))), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=90, subsampling=0, optimize=True)   # CONTRACT: check_image_format — q90 단일
    # ⚠ **줄인 뒤에 다시 잰다**(260814 실사고 진단 중 발견) — 구판은 한 번 줄이고 크기를 재확인하지
    #   않아서, 줄여도 여전히 한도를 넘는 그림을 그대로 실어 보냈다. 그러면 창구가 몸집으로 거절하고
    #   러너가 주소 방식으로 갈아타는데, 그 주소를 창구가 못 받으면(회선 끊김) 그 편은 통째로 죽는다.
    #   여기서 한 단 더 줄이면 애초에 그 사슬에 안 들어간다(줄이는 건 우리 손 안이라 값 0).
    for _side in (EMBED_SIDE, 960, 720):
        if buf.tell() <= EMBED_MAX:
            break
        if max(im.size) > _side:
            _r = _side / float(max(im.size))
            im = im.resize((max(1, int(im.width * _r)), max(1, int(im.height * _r))), Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=90, subsampling=0, optimize=True)   # CONTRACT: check_image_format — q90 단일
    if buf.tell() > EMBED_MAX:
        # ⚠ 여기까지 와도 안 줄면 **주소로 내려앉는 게 맞다** — 거절당할 걸 알면서 싣는 것보다 낫다.
        raise RuntimeError("참조가 줄여도 한도를 넘는다({}KB) — 주소 방식으로 보낸다".format(buf.tell() // 1024))
    print("  · 참조 축소 {}KB → {}KB({}×{})".format(len(raw) // 1024, buf.tell() // 1024, im.width, im.height))
    return buf.getvalue()


def refs_payload(urls, embed=True):
    """발사에 실을 참조 = **바이트 우선**, 못 가져오면 그 장만 주소(종전 동작 = 무회귀).

    반환 = (보낼 것들, 방식 이름). 방식은 산출 원장에 남긴다 — 다음 세션이 「이번 판은 어느
    방식으로 쐈나」를 추측 없이 읽어야 실패 축을 가른다(관측이 지워지면 추측이 메운다).
    """
    if not embed:
        return list(urls), "주소"
    out, fell = [], 0
    for u in urls:
        try:
            out.append(_one(u))
        except Exception as e:                  # noqa: BLE001
            print("::warning::참조 바이트 적재 실패 — 그 장만 주소로 보낸다: {}".format(str(e)[:140]))
            out.append(u)
            fell += 1
    return out, ("바이트" if not fell else "섞임({}장 주소)".format(fell))


# ── 발사·대기·받기 ───────────────────────────────────────────────────────────
def start(prompt, *, token, refs=None, seconds=None, ratio=None, sound=None):
    # ⚠ `sound` 는 받되 안 쓴다 — 그록 영상 창구에는 **오디오 끄기 값이 아예 없다**(xAI 스스로
    #   무음 프롬프트가 실패할 수 있다고 인정). 끄기의 확실한 수단은 산출 트랙 제거다.
    try:
        return gk.start_video(prompt, token=token, refs=refs or None, seconds=seconds,
                              **({"ratio": ratio} if ratio else {}))
    except gk.GrokError as e:
        raise classify(e) from None


def wait(job_id, *, token):
    try:
        v = gk.wait_video(job_id, token=token)
    except gk.GrokError as e:
        raise classify(e) from None
    return {"url": v.get("url"), "duration": v.get("duration"), "cost": float(v.get("cost_usd") or 0)}


def fetch(url):
    try:
        return gk.fetch(url)
    except gk.GrokError as e:
        raise classify(e) from None


def estimate(seconds, ratio=None):
    """발사 전 견적 — 그록은 **못 잰다**(응답이 와야 값을 안다). 지어내지 않고 None."""
    return None


# ── 프롬프트 문법 훅 ─────────────────────────────────────────────────────────
def ref_lock_clause(n):
    """참조 잠금 절 — 그록 공식 문법(슬롯 지목은 0부터 센다)."""
    tags = ", ".join("<IMAGE_{}>".format(i) for i in range(n))
    return "Keep the people, wardrobe, and setting identical to {}.".format(tags)


def ref_id_clause(i, text):
    """참조 i 번이 무엇인지 못 박는 문장 — 그록은 **번호로 지목**한다(공식 문법).

    ⚠ 이 한 줄이 260811 실사고의 봉합이다(인물 참조가 둘일 때 `He`·`She` 가 갈 곳을 몰라
      남자가 쏘는 컷이 여자가 쏘는 컷으로 뒤집혔다) — 번호에 정체를 묶어 대명사를 하나로 만든다.
    """
    return "<IMAGE_{}> shows {}.".format(i, text)


def sound_clause(on, sfx):
    """소리 절.

    ⚠ 끄기의 확실한 수단은 프롬프트가 아니라 **산출 트랙 제거**다(그록 영상 창구에 오디오 끄기
      값이 아예 없고 xAI 스스로 「무음 프롬프트가 실패할 수 있다」고 인정했다). 아래 4수법은 보조.
    ⚠ 컷이 대사를 적었어도 **말소리는 넣지 않는다** — 이미지→영상은 립싱크가 구조적으로 불리하고,
      실존 인물 축 위험도 여기서 함께 차단된다.
    """
    if on:
        return ["Sound: {}. No music.".format("; ".join(sfx)) if sfx
                else "Sound: ambient room tone and the natural sounds of the action, no music."]
    return ["Lips still and sealed, calm neutral expression.",
            "The only sounds are faint ambient room tone. No spoken words."]


# ── 오류 분류 ────────────────────────────────────────────────────────────────
def too_big(e):
    """몸집 축으로 거절당했나 — 이때만 주소 방식으로 갈아탄다(그 외엔 같은 방식으로 다시 쏜다)."""
    b = str(getattr(e, "body", "")).lower()
    return getattr(e, "code", 0) == 413 or "too large" in b or "payload" in b or "request entity" in b


def ref_unfetched(e):
    """창구가 **우리 그림을 못 받았다**고 답했는가(주소 방식에서만 나는 실패).

    ⚠ 왜 별도 술어인가(260814 실측) = 이 실패는 「다시 쏘면 되는 축」인데 **같은 방식으로 다시
      쏘면 같은 자리에서 또 끊긴다**. 몸집 거절이 「바이트 → 주소」로 갈아타는 것과 정확히 거울이라,
      그 짝이 없으면 회선이 한 번 흔들린 편은 영영 못 살린다(실측 = 폐버스 1편이 두 번 다 이 자리).
    ⚠ 창구 문구에 기대는 술어라 문구가 바뀌면 안 걸린다 — 그래서 **못 걸려도 종전 동작**(그냥 재시도)
      으로 내려앉게 두고, 걸리면 방식만 바꾼다(놓쳐도 나빠지지 않는다).
    """
    b = str(getattr(e, "body", "") or getattr(e, "why", "")).lower()
    return ("image_download" in b) or ("failed to download the provided image" in b)


def classify(e):
    """벤더 예외 → 통로 무관 3속성.

    ⚠ 사유를 **사람 말로** 옮긴다 — 코드만 남기면 운영자가 다음 수를 못 정한다. 이 레포가 세 번
      봉합한 병(사유 0자 경보)과 같은 축이라, 분류를 못 해도 원문을 싣는다.
    """
    if isinstance(e, LaneError):
        return e
    b = str(getattr(e, "body", ""))
    code = getattr(e, "code", 0)
    where = getattr(e, "where", "")
    if where == "video-moderated" or "moderat" in b.lower():
        return LaneError("검열에 걸렸다 — 같은 문장으로 다시 쏴도 안 풀린다. 컷 내용을 바꿔야 한다"
                         "(사람·폭력·실사 어휘 축)", retryable=False, body=b)
    if getattr(e, "tier_blocked", False):
        return LaneError("구독은 살아 있는데 xAI 가 영상 통로를 이 계정에 안 열어줬다(403) — 재시도 무의미",
                         retryable=False, auth_dead=True, body=b)
    if getattr(e, "dead_auth", False):
        return LaneError("자격이 죽었다 — 판정기를 다시 돌려 열쇠를 새로 받아야 한다",
                         retryable=False, auth_dead=True, body=b)
    if code == 429:
        return LaneError("한도에 걸렸다 — 잠시 뒤 손으로 다시 시도하면 된다", body=b)
    if where == "video-timeout":
        return LaneError("15분 안에 안 끝났다 — 서버가 밀린 상태다. 손으로 다시 시도", body=b)
    if code in (500, 502, 503, 504) or code == 0:
        return LaneError("서버·회선 일시 장애({}) — 손으로 다시 시도하면 대개 풀린다".format(code or "연결 실패"),
                         body=b)
    return LaneError("HTTP {} · {}".format(code, b[:160]), body=b)
