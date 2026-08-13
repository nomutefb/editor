#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""화질 확인 한 발 — 짧은 영상 하나를 실제로 쏘고 **나온 파일의 화소를 잰다**.

⚠ 왜 있나(260813 실사고) = 창구는 **모르는 화질 이름을 거절하지 않고 조용히 기본값으로 되돌린다**
  (엉터리 "9k" 도 720p 와 같은 22.5 크레딧을 회신했다). 견적은 그 되돌림을 값으로 드러내지만,
  「값도 맞고 이름도 아는 이름인데 실제로 그 화소로 나오는가」는 견적이 답할 수 없는 축이다 —
  나온 파일을 재는 수밖에 없다. 콘티 레인으로 그 확인을 하면 한 발이 15초라 값이 세 배 나간다.

⚠ 이건 **값이 나가는 확인**이다(견적 창구 hf-check 와 다르다). 길이를 최소로 두고 한 발만 쏜다.
⚠ 산출은 안 남긴다 — 화소·길이·소리만 찍는다(확인이 목적이지 쓸 영상을 만드는 게 아니다).
"""
import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, "shared")
import lane_seedance as LANE  # noqa: E402

# 중립 장면 — 사람·상표·글자가 안 들어가는 것으로 고정한다(실존 인물·상표 축 위험 0).
PROMPT = ("A slow push-in on an empty wooden desk beside a window, morning light, "
          "dust motes drifting. Static composition, no people, no text, no logos.")


def probe(path):
    """나온 파일의 실제 화소·길이·소리를 잰다 — 창구가 뭐라 했든 파일이 답이다."""
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "stream=codec_type,codec_name,width,height,r_frame_rate:format=duration",
         "-of", "json", path],
        capture_output=True, text=True, timeout=120)
    return json.loads(out.stdout or "{}")


def main():
    sec = int(os.environ.get("SD_SHOT_SEC") or LANE.SHOT_SEC)
    ratio = os.environ.get("SD_RATIO") or "9:16"
    print("── 화질 확인 한 발 ── {} · {} · {} · {}초".format(
        LANE.NAME, LANE.PRESET["res"], ratio, sec))

    tok = LANE.fresh_token()
    cr = LANE.estimate(sec, ratio, token=tok)
    print("① 견적 {} 크레딧".format(cr))
    cap = float(os.environ.get("SB_COST_CAP") or "400")
    if cr is None:
        print("::error::견적을 못 읽었다 — 값이 얼마 나갈지 모르는 채로는 안 쏜다")
        return 1
    if float(cr) > cap:
        print("::error::견적 {} > 상한 {} — 안 쏜다".format(cr, cap))
        return 1

    jid = LANE.start(PROMPT, token=tok, seconds=sec, ratio=ratio, sound=False)
    print("② 작업 번호 {}".format(jid))
    url = LANE.wait(jid, token=tok)
    print("③ 산출 {}".format(url))
    if not url:
        print("::error::주소가 안 왔다 — 값은 나갔는데 결과를 못 집었다(작업 번호로 창구에서 회수하라)")
        return 1

    blob = LANE.fetch(url)
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
        f.write(blob)
        p = f.name
    info = probe(p)
    vs = [s for s in info.get("streams", []) if s.get("codec_type") == "video"]
    as_ = [s for s in info.get("streams", []) if s.get("codec_type") == "audio"]
    dur = float((info.get("format") or {}).get("duration") or 0)
    if not vs:
        print("::error::영상 트랙이 없다 — 파일 {} 바이트".format(len(blob)))
        return 1
    v = vs[0]
    print("④ 실측 {}×{} · {} · {:.2f}초 · 소리 {} · {:,} 바이트".format(
        v.get("width"), v.get("height"), v.get("codec_name"), dur,
        (as_[0].get("codec_name") if as_ else "없음"), len(blob)))
    print("── 요청 화질 {} → 나온 화소 {}×{} ──".format(
        LANE.PRESET["res"], v.get("width"), v.get("height")))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except LANE.LaneError as e:
        print("::error::화질 확인 실패 — {}".format(e.why))
        if e.body:
            print("   원문: {}".format(str(e.body)[:400]))
        sys.exit(1)
