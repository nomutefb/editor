#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sb_cost.py — 콘티 한 판에 든 값을 **벤더별로 한 곳에** 모은다(운영자 260811
「도중에 제미나이 호출하는것도 값에 넣어야지」).

⚠ 왜 필요했나 = 값이 **세 스텝에 흩어져** 있었다. 참조 그림은 k_refgen 이, 콘티 시트는
  sb_sheet 가, 영상은 grok_sb_video 가 각각 부르는데 화면에 뜨는 숫자는 영상 값 하나뿐이라
  **운영자가 보는 금액이 실제보다 작았다**. 스텝끼리는 서로를 모르므로 값을 합칠 자리가
  아예 없었다 → 산출 폴더에 원장 파일 하나를 두고 각자 자기 몫을 적는다.

⚠ 실측과 계산을 **문장에서 가른다**([1] 정직) — 그록은 응답이 청구액을 실어 보내므로 실측이고,
  제미나이는 응답에 금액이 없어 **단가 × 장수** 계산이다. 원장에 `est` 로 표시하고 화면도
  그렇게 읽는다. 계산값을 실측인 척하면 다음 세션이 그 숫자를 근거로 잘못 판단한다.

⚠ 단가 출처 = CLAUDE.md 「Gemini 3.1 Flash Image · 1K 이미지 1콜 기준 $0.067」. 값 창작 0.
  ⚠ 2K 단가는 **미확인**이라 1K 단가로 센다 = 시트 한 장은 **하한**이다(그 사실을 원장에 남긴다).

CONTRACT: check_grok_sb_chain
"""
import json
import os

GEMINI_1K_USD = 0.067   # 정본 = CLAUDE.md 씨앗 파이프 항목(1K 이미지 1콜)
FNAME = "cost.json"


def add(out_dir, vendor, kind, n, usd=None, est=True, note="", unit="usd"):
    """원장에 한 줄 더한다. 같은 종류가 다시 오면 덮어쓴다(재실행이 값을 부풀리지 않는다).

    ⚠ **단위를 섞지 않는다**(260812 페이블 검증) — 달러와 크레딧은 서로 다른 화폐고 환산율은
      요금제 종속이라 우리가 모른다. 한 칸에 같이 더하면 화면이 「청구 $195」처럼 **실제로는
      나간 적 없는 금액**을 그것도 실측인 척(`est=False`) 띄운다. 그래서 칸 자체를 가른다 —
      달러는 `usd` · 크레딧은 `cr` · 합계도 각각(`total_usd` · `total_cr`).
    ⚠ 칸 이름을 그대로 둔 이유 = 이미 구워진 옛 산출물이 `usd`·`total_usd` 를 들고 있고,
      화면이 그걸 그대로 읽는다(새 이름으로 갈아엎으면 옛 판이 조용히 0원이 된다).
    """
    try:
        path = os.path.join(out_dir, FNAME)
        try:
            with open(path, encoding="utf-8") as f:
                led = json.load(f)
        except Exception:  # noqa: BLE001
            led = {"items": []}
        unit = (str(unit or "usd").strip().lower())
        if unit not in ("usd", "credit"):
            unit = "usd"
        if usd is None:
            usd = round(GEMINI_1K_USD * int(n or 0), 4)   # 그림 단가 계산 = 달러 축 전용
            unit = "usd"
        row = {"vendor": vendor, "kind": kind, "n": int(n or 0),
               "unit": unit, "est": bool(est)}
        row["cr" if unit == "credit" else "usd"] = round(float(usd or 0), 2 if unit == "credit" else 4)
        if note:
            row["note"] = note
        led["items"] = [x for x in led.get("items", []) if x.get("kind") != kind] + [row]
        led["total_usd"] = round(sum(float(x.get("usd") or 0) for x in led["items"]), 4)
        led["total_cr"] = round(sum(float(x.get("cr") or 0) for x in led["items"]), 2)
        led["est_any"] = any(x.get("est") for x in led["items"])
        with open(path, "w", encoding="utf-8") as f:
            json.dump(led, f, ensure_ascii=False)
        return led
    except Exception as e:  # noqa: BLE001
        print("::warning::값 원장 기록 실패(비치명): {}".format(str(e)[:150]))
        return None
