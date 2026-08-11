#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""grok_sb_video.py — 콘티(board.md)를 컷마다 그림 → 영상으로 굽는다(촬영=grok 레인).

  grok_sb_video.py <board.md> <out_dir>

운영자 260811 확정 흐름:
  ① 운영자가 상황을 말한다(글 · 사진)
  ② **감독**(Fable 5 / Opus 5 / GPT 5.6 Sol)이 콘티를 짠다 = `sbmake.sh` 가 이미 하는 일
     → board.md 에 컷마다 `### 컷N · a~b s` + ACTION / CAMERA / DIALOGUE
  ③ **이 파일** = 컷마다 그림(Gemini) → 그 그림을 **첫 장면**으로 그록 영상
  ④ 결과가 sb_out/<id>/ 에 앉는다

⚠ 왜 컷마다 그림을 새로 굽나 = `## 🖼 레퍼런스` 절의 그림은 **인물·배경·키비주얼 몇 장**이지
  컷 그림이 아니다(sb-make.md 규약). 그록 이미지→영상은 **컷의 첫 프레임**을 요구하므로
  컷 수만큼 그림이 있어야 한다. 이 그림들이 곧 「스토리보드 컷」이기도 하다.

⚠ 컷 길이는 우리가 정하지 않는다 — **콘티가 이미 `0~2s` 로 적는다.** 그 값을 그대로 쓴다
  (운영자 260810 「10초 고정」은 **단독 영상 1편** 축이고, 콘티 컷은 컷마다 다르다 =
  10초를 컷에 그대로 박으면 12컷이 120초가 된다).

⚠ 프롬프트 조립 규칙 = `prompts/grok-make.md` 정본. 특히 §3 — 첫 프레임이 구도·조명·색을
  이미 확정하므로 프롬프트는 **무엇이 움직이는지만** 쓴다(재묘사는 희석).

CONTRACT: check_grok_sb_chain

fail-soft = 컷 하나가 죽어도 나머지는 간다. 전부 죽어도 콘티·레퍼런스는 그대로 남는다.
"""
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "shared"))
import thumb_gen as tg          # noqa: E402  gemini_image · r2_upload · R2_ON (k_refgen 과 같은 배관)
import grok_api as gk           # noqa: E402  구독 자격 통로

CUT_MAX = int(os.environ.get("GROK_SB_CUT_MAX", "12"))     # 한 번에 굽는 컷 상한(비용·시간 가드)
SEC_MIN, SEC_MAX = 1, 15                                   # 공식 허용 범위
SEC_FALLBACK = 5                                           # 콘티가 시각을 안 적었을 때
IMG_ASPECT = os.environ.get("REFGEN_ASPECT", "16:9")

# 컷 머리 = `### 컷3 · 4~7s · 한 줄 설명`(sb-make.md 출력 형식) — 시각 표기는 없을 수도 있다
_CUT = re.compile(r"^###\s*컷\s*(\d+)\s*(?:·\s*([\d.]+)\s*~\s*([\d.]+)\s*s)?\s*(?:·\s*(.*))?$", re.M)
_FIELD = re.compile(r"^(ACTION|CAMERA|DIALOGUE|MOTION)\s*:\s*(.*)$", re.M)

# 그림에 글자가 들어가면 영상에서 반드시 뭉개진다(정본 §6) → 그림 단계에서 억제한다.
# ⚠ 이 부정문은 **그림 축 한정 허용**(정본 §5 표) — 영상 프롬프트엔 절대 넣지 않는다.
IMG_TAIL = " 글자·자막·캡션·워터마크·로고 없이 깨끗한 장면만."


def cuts_of(md):
    """board.md → [{n, sec, desc, action, camera, dialogue}] (문서 순)."""
    out, ms = [], list(_CUT.finditer(md))
    for i, m in enumerate(ms):
        body = md[m.end(): ms[i + 1].start() if i + 1 < len(ms) else len(md)]
        f = {k: v.strip() for k, v in _FIELD.findall(body)}
        sec = SEC_FALLBACK
        if m.group(2) and m.group(3):
            try:
                sec = round(float(m.group(3)) - float(m.group(2)))
            except ValueError:
                sec = SEC_FALLBACK
        out.append({
            "n": int(m.group(1)),
            "sec": max(SEC_MIN, min(SEC_MAX, sec or SEC_FALLBACK)),
            "desc": (m.group(4) or "").strip(),
            "action": f.get("ACTION", ""),
            # MOTION = 촬영=grok 전용 **영어** 동작 줄(감독이 쓴다). 없으면 ACTION 폴백.
            # ⚠ 왜 별도 필드인가 = ACTION 은 운영자가 화면에서 읽는 한국어인데, 그록 프롬프트는
            #   영어가 안전하다(정본 §4-4). 한 필드에 둘을 겸하게 하면 화면이 영어가 되거나
            #   프롬프트가 한국어가 된다 — 둘 다 손해라 축을 가른다.
            "motion": f.get("MOTION", ""),
            "camera": f.get("CAMERA", ""),
            "dialogue": f.get("DIALOGUE", ""),
        })
    return out


def img_prompt(c):
    """컷 그림(첫 장면) 프롬프트. 구도·인물·공간을 여기서 확정한다."""
    bits = [c["desc"], c["action"], c["camera"]]
    return " ".join(b for b in bits if b) + IMG_TAIL


def vid_prompt(c, sound=True):
    """컷 영상 프롬프트 — 정본 `prompts/grok-make.md` 규칙 적용.

    ⚠ **바뀌는 것만 쓴다**(§3-1). 첫 프레임이 구도·조명·색을 이미 쥐고 있어서 그걸 다시 쓰면
      강화가 아니라 희석이다. 그래서 desc(장면 묘사)는 **일부러 뺀다** — ACTION(무엇이 움직이나)과
      CAMERA(어떻게 보나) 둘만 간다.
    ⚠ 어순 = 시간순(§0-②). 동작을 첫 문장에 둔다.
    ⚠ 소리 = 안 적으면 제네릭 배경음악이 붙는다(§0-③) → 켜기면 명시, 끄기면 4수법(§4-3).
    """
    parts = []
    mv = c.get("motion") or c["action"]   # 영어 줄 우선 · 없으면 한국어라도 보낸다(fail-soft)
    if mv:
        parts.append(mv.rstrip(". ") + ".")
    if c["camera"]:
        parts.append(c["camera"].rstrip(". ") + ".")
    if sound:
        # 컷이 대사를 적었어도 **말소리는 넣지 않는다** — 이미지→영상은 립싱크가 구조적으로
        # 불리하고(§4-3), 실존 인물 축 위험도 여기서 함께 차단된다(§7-3 ①).
        parts.append("Sound: ambient room tone and the natural sounds of the action, no music.")
    else:
        # 끄기 = 4수법을 순서대로(마지막 부정문만 단독으로 쓰면 역효과 · §4-3)
        parts.append("Lips still and sealed, calm neutral expression.")
        parts.append("The only sounds are faint ambient room tone. No spoken words.")
    return " ".join(parts)


def _why(e):
    """실패 사유를 **사람 말로** 옮긴다 — 코드만 남기면 운영자가 다음 수를 못 정한다.

    ⚠ 이 레포가 세 번 봉합한 병(사유 0자 경보)과 같은 축이라, 분류를 못 해도 원문을 싣는다.
    """
    b = str(e.body)
    if e.where == "video-moderated" or "moderat" in b.lower():
        return "검열에 걸렸다 — 같은 문장으로 다시 쏴도 안 풀린다. 컷 내용을 바꿔야 한다(사람·폭력·실사 어휘 축)"
    if e.tier_blocked:
        return "구독은 살아 있는데 xAI 가 영상 통로를 이 계정에 안 열어줬다(403) — 재시도 무의미"
    if e.dead_auth:
        return "자격이 죽었다 — 판정기를 다시 돌려 열쇠를 새로 받아야 한다"
    if e.code == 429:
        return "한도에 걸렸다 — 잠시 뒤 손으로 다시 시도하면 된다"
    if e.where == "video-timeout":
        return "15분 안에 안 끝났다 — 서버가 밀린 상태다. 손으로 다시 시도"
    if e.code in (500, 502, 503, 504) or e.code == 0:
        return "서버·회선 일시 장애({}) — 손으로 다시 시도하면 대개 풀린다".format(e.code or "연결 실패")
    return "HTTP {} · {}".format(e.code, b[:160])


def strip_audio(path):
    """소리 끄기 = 산출 트랙을 버린다.

    ⚠ 프롬프트 무음 지시에 기대지 않는다 — 그록 영상 API 에 오디오 끄기 값이 없고,
      xAI 스스로 「무음 프롬프트가 실패할 수 있다」고 인정했다(정본 §4-1). 이게 확실한 수단이다.
    """
    out = path[:-4] + "_mute.mp4"
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-c", "copy", "-an", out],
                       capture_output=True)
    if r.returncode == 0 and os.path.getsize(out) > 0:
        os.replace(out, path)
        return True
    print("::warning::소리 제거 실패(원본 유지): {}".format(r.stderr.decode("utf-8", "replace")[:200]))
    return False


def main():
    if len(sys.argv) < 3:
        sys.exit("usage: grok_sb_video.py <board.md> <out_dir>")
    md_path, out_dir = sys.argv[1], sys.argv[2]
    md = open(md_path, encoding="utf-8").read()
    stem = os.path.basename(os.path.normpath(out_dir))
    prefix = os.environ.get("REFGEN_PREFIX", "sb_out")
    sound = (os.environ.get("GROK_SOUND", "1") != "0")

    cuts = cuts_of(md)[:CUT_MAX]
    if not cuts:
        print("::warning::컷을 못 찾았다(board.md 형식 확인) — 영상 생략")
        return 0
    print("컷 {}개 · 소리 {}".format(len(cuts), "켜기" if sound else "끄기"))

    if not tg.KEY:
        print("::warning::GEMINI_API_KEY 미등록 — 컷 그림을 못 굽는다(영상 생략)")
        return 0
    try:
        token = gk.fresh_token()
    except gk.GrokError as e:
        # 자격 실패는 여기서 끝낸다 — 사유를 원문 그대로 남긴다(추적 가능성 = 이 레포 계약).
        print("::warning::그록 자격 실패({}) — 영상 생략".format(e))
        return 0

    items, spent = [], 0.0
    for c in cuts:
        rec = {"n": c["n"], "sec": c["sec"], "desc": c["desc"], "img": None, "video": None}
        try:
            png = tg.gemini_image(img_prompt(c), aspect=IMG_ASPECT)
            key = "{}/{}/cut{:02d}.jpg".format(prefix, stem, c["n"])
            rec["img"] = tg.r2_upload(png, key, tg._img_type(png)[0] or "image/jpeg") if tg.R2_ON else None
        except Exception as e:  # noqa: BLE001
            print("::warning::컷{} 그림 실패: {}".format(c["n"], str(e)[:200]))
            items.append(rec)
            continue
        if not rec["img"]:
            # ⚠ 그록에 넘기려면 **공개 주소**여야 한다 → R2 없으면 이 레인은 성립하지 않는다.
            print("::warning::컷{} 그림 주소 없음(R2 미설정) — 영상 생략".format(c["n"]))
            items.append(rec)
            continue
        try:
            rid = gk.start_video(vid_prompt(c, sound), token=token, image=rec["img"], seconds=c["sec"])
            v = gk.wait_video(rid, token=token)
            spent += float(v.get("cost_usd") or 0)
            raw = gk.fetch(v["url"])
            local = os.path.join(out_dir, "cut{:02d}.mp4".format(c["n"]))
            open(local, "wb").write(raw)
            if not sound:
                strip_audio(local)
            vkey = "{}/{}/cut{:02d}.mp4".format(prefix, stem, c["n"])
            rec["video"] = tg.r2_upload(open(local, "rb").read(), vkey, "video/mp4") if tg.R2_ON else None
            if rec["video"]:
                os.remove(local)   # R2 로 갔으면 레포에 안 남긴다(레포 비대 0 = k_refgen 관례)
            print("컷{} ✓ {}초 · {}".format(c["n"], c["sec"], rec["video"] or local))
        except gk.GrokError as e:
            # ⚠ 자동 재시도 없음(운영자 260811) — 다시 쏘면 돈이 또 나가고, 검열 차단은
            #   같은 프롬프트로 몇 번을 쏴도 안 풀린다. 대신 **막힌 이유를 사람 말로 남겨**
            #   운영자가 보고 손으로 다시 시도할지 정한다.
            rec["fail"] = _why(e)
            print("::warning::컷{} 영상 실패 — {}".format(c["n"], rec["fail"]))
            if e.tier_blocked or e.dead_auth:
                # 자격 축이면 남은 컷도 전부 같은 이유로 죽는다 → 돈·시간을 더 쓰지 않는다.
                print("::warning::자격 축 실패 — 남은 컷 중단")
                items.append(rec)
                break
        items.append(rec)

    done = sum(1 for r in items if r.get("video"))
    for r in items:
        if not r.get("video") and not r.get("fail"):
            r["fail"] = r.get("fail") or "그림 단계에서 막혔다(위 경고 참조)"
    json.dump({"cuts": items, "done": done, "total": len(cuts), "sound": sound,
               "cost_usd": round(spent, 4)},
              open(os.path.join(out_dir, "video.json"), "w", encoding="utf-8"), ensure_ascii=False)
    print("영상 {}/{}컷 · 청구 {} 달러".format(done, len(cuts), round(spent, 4)))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:  # noqa: BLE001
        # ⚠ 전면 fail-soft = 영상이 실패해도 콘티·레퍼런스 산출은 그대로 살아야 한다.
        print("::warning::grok_sb_video 예외(비치명): {}".format(str(e)[:300]))
        sys.exit(0)
