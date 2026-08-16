#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sd_fire.py — 콘티 발사 폴더의 shots.json 을 시댄스(힉스필드 통로)로 실발사한다.

흐름(편마다 순차) = 견적(과금 0) → 상한 검문 → 발사 → 완료 대기 → mp4 내려받아 폴더에 저장.
⚠ 통로·자격·폴링은 전부 `shared/lane_seedance.py` 정본 경유(사본 0) — 대기는 창구의
  기다리기 도구(회당 15초 장기폴 + 서버가 시키는 간격) 뿐이라 깃허브축 호출 0.
⚠ 실패한 편이 있어도 앞서 내려받은 편은 지우지 않는다(부분 산출 보존) — rc 로 실패를 말한다.
"""
import json
import os
import sys

sys.path.insert(0, "shared")
import lane_seedance as LANE  # noqa: E402


def main():
    sid = (os.environ.get("SD_ID") or "").strip()
    if not sid:
        print("::error::SD_ID 가 비어 있다 — 발사 폴더를 모른다")
        return 1
    base = os.path.join("sb_out", sid)
    spec_p = os.path.join(base, "shots.json")
    if not os.path.exists(spec_p):
        print("::error::{} 가 없다 — 발사 명세 없이는 안 쏜다".format(spec_p))
        return 1
    spec = json.load(open(spec_p, encoding="utf-8"))
    ratio = spec.get("ratio") or "9:16"
    sound = bool(spec.get("sound", True))
    raw = spec.get("raw_base") or ""
    ident = (spec.get("identity") or "").strip()
    shots = spec.get("shots") or []
    cap = float(os.environ.get("SB_COST_CAP") or "200")   # 편당 상한(크레딧)
    # 🎬 콘티 두 장(스토리보드·스케치 동작)을 **편마다 반드시** 싣는다(운영자 260816 「이를 반드시
    #    참조하게 해주셈」). 자동 레인(grok_sb_video.sheet_slots)은 이미 그렇게 도는데 이 손조립
    #    경로만 `shots.json` 의 refs[] 밖을 안 봐서 두 장이 통째로 빠져 있었다 — 같은 병의 형제.
    #    ⚠ 자리 = **맨 뒤**(인물·장소 사진 뒤) = 시트가 얼굴·장소 잠금을 밀어내지 않는다(cap_refs 계약 동축).
    #    ⚠ 주소만 싣는다 — 「설계도지 장면이 아니다」라는 정체 문장은 이 경로에선 사람이 쓴 프롬프트가 말한다.
    #    ⚠ 끄기 = SB_SHEET_REF=0(자동 레인과 같은 손잡이) · sheet.json 부재 = 종전 동작(무회귀).
    sheets = []
    if os.environ.get("SB_SHEET_REF") != "0":
        try:
            _sj = json.load(open(os.path.join(base, "sheet.json"), encoding="utf-8"))
            sheets = [u for u in (_sj.get("url"), _sj.get("conti")) if u]
        except Exception:  # noqa: BLE001
            pass
    print("콘티 참조 {}장{}".format(len(sheets), "" if sheets else " — sheet.json 없음(시트 없이 쏜다)"))

    print("── 콘티 발사 ── {} · {} · {} · {}편".format(LANE.NAME, LANE.PRESET["res"], ratio, len(shots)))
    tok = LANE.fresh_token()
    bal = LANE.balance(tok)
    print("잔액 회신: {}".format(json.dumps(bal, ensure_ascii=False)[:200]))

    results, rc = [], 0
    for s in shots:
        name, sec = s["name"], int(s["sec"])
        out_p = os.path.join(base, name + ".mp4")
        if os.path.exists(out_p):
            print("[{}] 이미 있음 — 건너뜀(재발사 = 파일 지우고 다시)".format(name))
            continue
        prompt = (ident + " " + s["prompt"]).strip()
        refs = [raw + r for r in (s.get("refs") or [])] + sheets
        try:
            cr = LANE.estimate(sec, ratio, token=tok)
            print("[{}] 견적 {} 크레딧".format(name, cr))
            if cr is None:
                print("::error::[{}] 견적을 못 읽었다 — 값이 얼마 나갈지 모르는 채로는 안 쏜다".format(name))
                rc = 1
                break
            if float(cr) > cap:
                print("::error::[{}] 견적 {} > 상한 {} — 안 쏜다".format(name, cr, cap))
                rc = 1
                break
            jid = LANE.start(prompt, token=tok, refs=refs, seconds=sec, ratio=ratio, sound=sound)
            print("[{}] 작업 번호 {}".format(name, jid))
            done = LANE.wait(jid, token=tok)
            url = (done or {}).get("url") if isinstance(done, dict) else done
            if not url:
                print("::error::[{}] 주소가 안 왔다 — 작업 번호 {} 로 창구에서 회수하라".format(name, jid))
                rc = 1
                break
            blob = LANE.fetch(url)
            with open(out_p, "wb") as f:
                f.write(blob)
            info = {"name": name, "job_id": jid, "sec": sec, "bytes": len(blob),
                    "cost": (done or {}).get("cost"), "cost_known": (done or {}).get("cost_known")}
            results.append(info)
            print("[{}] 착지 {} 바이트 · 청구 {}".format(name, len(blob), info["cost"]))
        except Exception as e:  # noqa: BLE001
            print("::error::[{}] 실패 — {}".format(name, str(e)[:400]))
            rc = 1
            break

    if results:
        with open(os.path.join(base, "shots_result.json"), "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=1)
    print("── 끝 ── 성공 {}/{} · rc={}".format(len(results), len(shots), rc))
    return rc


if __name__ == "__main__":
    sys.exit(main())
