#!/usr/bin/env python3
"""누끼 정본 엔진 = GPT Image 2.0 투명 배경(운영자 260822 «지피티누끼로 대체»).

구판(SAM2 실루엣)은 ⓐ 피사체를 손으로 골라야 하고 ⓑ 헤비 스택(torch) 설치까지 껴서 20분 상한이었다.
GPT 축은 사진 한 장이면 끝이고 실측 33초다 — 대신 **원본 화소를 오려내는 게 아니라 다시 그린다**
(실측 확정 = `input_fidelity`를 이 모델이 거부한다 400 `invalid_input_fidelity_model` = 원본을 붙잡을
손잡이가 API에 없다 · 얼굴·주름이 미세하게 달라질 수 있고 크기도 지원 3종으로 스냅된다).

실측 근거(run 32587881471 · 260822) = 편집(images/edits) + background=transparent + output_format=png
→ RGBA 1024x1536 · 투명 화소 76.1% · 33s. 파라미터가 아니라 **알파 평면**으로 판정했다(PNG 표기는 증거가 못 된다).

실패 = None 반환 → 호출부가 구판 SAM2/박스 알파로 폴백(기능 무중단 · engine 정직 표기).
"""
import base64
import hashlib
import io
import json
import os
import time
import urllib.request

# 모델 후보 = 앞에서부터(미존재 400/404면 다음) · 정본 = shared/models.json gpt_image
MODELS = [m for m in (os.environ.get("IMGEDIT_CUT_MODEL", "").strip(), "gpt-image-2", "gpt-image-1") if m]
# 누끼 주문 = 「배경만 빼라」 — edits는 마스크가 없으면 사실상 재생성이라 이 문장이 원본 보존의 유일한 손잡이다
# (input_fidelity가 이 모델에서 거부되는 게 실측 확정 · 문법 = gen_image.CLONE_ONLY 「달라지는 것은 …뿐」 계승).
PROMPT = ("Remove the background completely and keep only the main subject, exactly as it appears in the "
          "attached photo. Do not redraw, restyle, or change the subject — same person, same face, same pose, "
          "same clothing, same colors, same lighting. Output the subject on a fully transparent background. "
          "Do not add any new element, shadow, text, or border.")
CLEAR_MIN = 3.0   # 투명 화소 하한(%) — 이보다 적으면 「알파는 있는데 배경이 안 빠진」 무동작이다(실측 정상 76.1%)


def _stats(png):
    """알파 평면 실측 — 「투명 PNG가 왔다」를 화소로 확정(무동작 검출 · 크로마키 알파 프로브 동축)."""
    from PIL import Image
    im = Image.open(io.BytesIO(png))
    if im.mode != "RGBA":
        return None
    a = im.getchannel("A")
    h = a.histogram()
    n = sum(h) or 1
    clear = sum(h[:16]) * 100.0 / n
    return {"w": im.size[0], "h": im.size[1], "clear_pct": round(clear, 2)}


def _post(model, img_bytes, key):
    parts = [("model", model), ("prompt", PROMPT), ("n", "1"),
             ("background", "transparent"), ("output_format", "png")]   # ← 투명 산출 2파라미터(실측 확정)
    bnd = "----nomutecut" + hashlib.sha1((model + str(len(img_bytes))).encode()).hexdigest()[:12]
    body = b""
    for k, v in parts:
        body += ('--{}\r\nContent-Disposition: form-data; name="{}"\r\n\r\n{}\r\n'.format(bnd, k, v)).encode()
    body += ('--{}\r\nContent-Disposition: form-data; name="image"; filename="src.png"\r\n'
             'Content-Type: image/png\r\n\r\n'.format(bnd)).encode() + img_bytes + b"\r\n"
    body += ("--{}--\r\n".format(bnd)).encode()
    req = urllib.request.Request("https://api.openai.com/v1/images/edits", data=body, headers={
        "Authorization": "Bearer " + key, "Content-Type": "multipart/form-data; boundary=" + bnd})
    with urllib.request.urlopen(req, timeout=300) as resp:
        j = json.loads(resp.read().decode())
    b64 = (j.get("data") or [{}])[0].get("b64_json")
    return base64.b64decode(b64) if b64 else None


def cutout_png(img_bgr):
    """BGR 배열 → 투명 PNG 바이트(성공) 또는 None(실패 = 호출부가 구판으로 폴백).

    반환 = (png_bytes, engine, note) · engine = 'gpt-image-2' 등 · note = 실패 사유(정직 표기용)."""
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        return None, "", "OPENAI_API_KEY 없음"
    try:
        import cv2
        from PIL import Image
        rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        im = Image.fromarray(rgb)
        im.thumbnail((1536, 1536))   # 편집 API 권장 규격 상한 · 원본비 유지
        # 첨부 = 무손실 PNG — JPEG 압축 잡음이 경계에 끼면 모델이 그 자국까지 피사체로 읽어 알파 경계가 흔들린다.
        b = io.BytesIO(); im.save(b, "PNG"); src = b.getvalue()
    except Exception as e:  # noqa: BLE001
        return None, "", "원본 변환 실패 {}".format(type(e).__name__)

    for model in MODELS:
        t0 = time.time()
        try:
            png = _post(model, src, key)
        except Exception as e:  # noqa: BLE001
            det = ""
            try:
                det = e.read().decode("utf-8", "ignore")[:200]
            except Exception:
                pass
            print("::warning::GPT 누끼 실패(model={}): {} {}".format(model, str(e)[:100], det), flush=True)
            if "model" in det.lower():
                continue   # 모델 ID 자체가 없다 = 다음 후보
            return None, "", "GPT 호출 실패"
        if not png:
            continue
        st = _stats(png)
        if not st:
            print("::warning::GPT 누끼 — 알파 채널 없음(투명 미적용)", flush=True)
            return None, "", "알파 없음"
        if st["clear_pct"] < CLEAR_MIN:
            print("::warning::GPT 누끼 무동작 — 투명 화소 {}%(하한 {}%)".format(st["clear_pct"], CLEAR_MIN), flush=True)
            return None, "", "배경이 안 빠졌어"
        print("🎯 GPT 누끼 = {} · {}x{} · 투명 {}% · {}s".format(
            model, st["w"], st["h"], st["clear_pct"], round(time.time() - t0, 1)), flush=True)
        return png, model, ""
    return None, "", "GPT 후보 전건 실패"
