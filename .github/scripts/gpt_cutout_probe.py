#!/usr/bin/env python3
"""GPT Image 2.0 투명 배경(누끼) 실호출 프로브 — 「편집 탭 누끼를 GPT로 뽑을 수 있나」의 실측기.

배경 = 260822 운영자 지시(첨부 = GPT Image 2.0 API에 투명 배경 프리뷰 추가 소식) — 지금 편집 탭 누끼는
SAM2 실루엣 축(apps/imgedit/img_mosaic.py cutout)이고 GPT 축은 배선이 아예 없다. 그래서 배선하기 전에
「그 파라미터가 이 계정·이 모델에서 실제로 알파를 주는가」를 먼저 실호출로 확정한다(추측 금지 = 정직 축).

재는 것 3케이스 = ① 편집(images/edits) + background=transparent ② 같은 편집에 input_fidelity=high 동반
③ 생성(images/generations) + background=transparent(파라미터 자체 지원 여부 = 편집이 죽어도 갈래를 가른다).
판정 = 산출 PNG 알파 평면 실측(투명 화소 비율·알파 평균) — 「PNG로 왔다」는 알파가 있다는 뜻이 아니다.

산출 = R2 probe/<id>/ 업로드 + 로그에 URL·통계(레포 커밋 0 = 착지 게이트 무관 · 원장 오염 0).
"""
import base64, hashlib, io, json, os, sys, time, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import thumb_gen as tg   # r2_upload(bytes, key, ctype) · R2_ON — 업로드 정본 재사용(사본 0)

KEY = os.environ.get("OPENAI_API_KEY", "").strip()
SRC = os.environ.get("PROBE_SRC", "").strip()
PID = os.environ.get("PROBE_ID", "").strip() or time.strftime("%y%m%d%H%M%S")
MODELS = [m for m in (os.environ.get("PROBE_MODEL", "").strip(), "gpt-image-2", "gpt-image-1") if m]
# 누끼 주문 = 「배경만 빼라」 — 피사체를 다시 그리지 말라고 못박는다(edits는 마스크가 없으면 사실상 재생성이라
# 이 문장이 원본 보존의 유일한 손잡이다 · 문법 = gen_image.CLONE_ONLY 계승).
PROMPT = ("Remove the background completely and keep only the main subject, exactly as it appears in the "
          "attached photo. Do not redraw, restyle, or change the subject — same person, same face, same pose, "
          "same clothing, same colors, same lighting. Output the subject on a fully transparent background. "
          "Do not add any new element, shadow, text, or border.")


def alpha_stats(png):
    """알파 평면 실측 — 「투명 PNG가 왔다」를 화소로 확정(포맷 표기는 증거가 못 된다)."""
    from PIL import Image
    im = Image.open(io.BytesIO(png))
    mode, size = im.mode, im.size
    if mode != "RGBA":
        return {"mode": mode, "size": list(size), "has_alpha": False, "note": "알파 채널 없음 = 누끼 아님"}
    a = im.getchannel("A")
    px = list(a.getdata())
    n = len(px) or 1
    clear = sum(1 for v in px if v < 16)      # 완전 투명
    solid = sum(1 for v in px if v > 239)     # 완전 불투명
    return {"mode": mode, "size": list(size), "has_alpha": True,
            "alpha_mean": round(sum(px) / n, 2),
            "clear_pct": round(clear * 100.0 / n, 2),   # 배경이 실제로 빠진 비율
            "solid_pct": round(solid * 100.0 / n, 2),
            "verdict": "누끼 성립" if clear >= 5.0 else "알파는 있으나 뺀 화소 거의 없음"}


def post(url, parts, img_bytes=None):
    if img_bytes is None:
        body = json.dumps({k: (int(v) if k == "n" else v) for k, v in parts}).encode()
        hdr = {"Authorization": "Bearer " + KEY, "Content-Type": "application/json"}
    else:
        bnd = "----nomuteprobe" + hashlib.sha1(str(parts).encode()).hexdigest()[:12]
        body = b""
        for k, v in parts:
            body += ('--{}\r\nContent-Disposition: form-data; name="{}"\r\n\r\n{}\r\n'.format(bnd, k, v)).encode()
        body += ('--{}\r\nContent-Disposition: form-data; name="image"; filename="src.png"\r\n'
                 'Content-Type: image/png\r\n\r\n'.format(bnd)).encode() + img_bytes + b"\r\n"
        body += ("--{}--\r\n".format(bnd)).encode()
        hdr = {"Authorization": "Bearer " + KEY, "Content-Type": "multipart/form-data; boundary=" + bnd}
    req = urllib.request.Request(url, data=body, headers=hdr)
    with urllib.request.urlopen(req, timeout=300) as resp:
        j = json.loads(resp.read().decode())
    b64 = (j.get("data") or [{}])[0].get("b64_json")
    return base64.b64decode(b64) if b64 else None


def case(name, model, kind, img_bytes, fidelity):
    parts = [("model", model), ("prompt", PROMPT), ("n", "1"),
             ("background", "transparent"), ("output_format", "png")]   # ← 실측 대상 2파라미터(문서 §투명 배경)
    if kind == "edits" and fidelity:
        parts.append(("input_fidelity", "high"))
    url = "https://api.openai.com/v1/images/" + kind
    t0 = time.time()
    try:
        png = post(url, parts, img_bytes if kind == "edits" else None)
    except Exception as e:  # noqa: BLE001
        det = ""
        try:
            det = e.read().decode("utf-8", "ignore")[:400]
        except Exception:
            pass
        print("❌ {} — {} {}".format(name, str(e)[:120], det), flush=True)
        return {"case": name, "model": model, "kind": kind, "ok": False, "err": (str(e)[:120] + " " + det)[:400]}
    sec = round(time.time() - t0, 1)
    if not png:
        print("❌ {} — 빈 응답".format(name), flush=True)
        return {"case": name, "model": model, "kind": kind, "ok": False, "err": "빈 응답"}
    st = alpha_stats(png)
    key = "probe/{}/{}.png".format(PID, name)
    # 투명 산출 = PNG 필수(알파 보존 = 이 프로브의 판정 대상 자체 · JPEG는 알파를 못 담아 측정이 성립하지 않는다)
    u = tg.r2_upload(png, key, "image/png") if tg.R2_ON else ""
    print("✅ {} · {} · {}s · {}B · {} · url={}".format(name, model, sec, len(png), json.dumps(st, ensure_ascii=False), u), flush=True)
    return {"case": name, "model": model, "kind": kind, "ok": True, "sec": sec, "bytes": len(png), "url": u, **st}


def main():
    if not KEY:
        print("::error::OPENAI_API_KEY 없음 — 프로브 불가"); return 1
    img = b""
    if SRC and os.path.exists(SRC):
        from PIL import Image
        im = Image.open(SRC).convert("RGB")
        im.thumbnail((1536, 1536))   # 업로드 상한 여유(편집 API 권장 규격) · 원본비 유지
        # 첨부 = 무손실 PNG로 보낸다 — JPEG 압축 잡음이 경계에 끼면 모델이 그 자국까지 피사체로 읽어
        # 알파 경계가 흔들린다(이 프로브의 판정 축이 곧 알파 경계라 원료를 흐리면 측정이 무효).
        b = io.BytesIO(); im.save(b, "PNG"); img = b.getvalue()
        print("📎 원본 {} → {}x{} · {}B".format(SRC, im.size[0], im.size[1], len(img)), flush=True)
        u0 = tg.r2_upload(img, "probe/{}/00_src.png".format(PID), "image/png") if tg.R2_ON else ""
        print("📎 원본 url={}".format(u0), flush=True)
    else:
        print("::warning::PROBE_SRC 없음({}) — 편집 케이스 생략, 생성만".format(SRC), flush=True)
    out = []
    for model in MODELS[:1]:   # 1순위 모델만(과금 최소 · 실패 시 로그의 사유로 다음 판단)
        if img:
            out.append(case("01_edits_fid", model, "edits", img, True))
            if not out[-1].get("ok"):
                out.append(case("02_edits_nofid", model, "edits", img, False))
        out.append(case("03_gen", model, "generations", None, False))
    print("\n📊 결과=" + json.dumps(out, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
