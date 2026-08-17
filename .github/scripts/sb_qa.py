#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sb_qa · 콘티 산출 자기검문 원장 — 「왜 잘 뽑혔나」를 나중에 되짚을 수 있게 값으로 남긴다.

운영자 260817 3차 = 「나중에 영상 잘뽑힌거 왜 잘뽑혔는지 분석해서 녹일때 필요하니 관련된 내용」
  → 잘 나온 판을 되짚으려면 **그 판이 무슨 값으로 만들어졌는지**가 남아 있어야 한다. 지금까지는
    콘티 본문만 남아서 「이 판은 라이브러리를 훑었나 · 카메라를 얼마나 자세히 썼나」를 사람이
    매번 눈으로 세야 했고, 260816 정청래 판은 `연출 모듈:` 줄이 아예 빠진 채로 나갔다
    (= 다음 판에서 「H07 말고 H03 으로」 라고 지목할 대상이 사라졌다).

⚠ 이 파일은 **판정만 하고 아무것도 안 막는다**(rc 항상 0). 콘티는 이미 만들어졌고, 여기서 죽으면
  잘 나온 판까지 같이 버리게 된다 = 러너 전면 fail-soft 관례 그대로.

⚠ 카메라 깊이 임계 = **실측 두 분포 사이**(값 창작 0):
    · 판형 견본 `9-3.png`(종이 인쇄용 축약) = 컷 12개 전건 3~5 낱말 · 최대 **5**
    · 260816 정청래 판(운영자가 「이게 더 낫다」고 확정한 정본) = 컷 11개 전건 13~20 낱말 · 최소 **13**
  → 사이 구간 6~12 의 중앙 = `CAM_MIN_WORDS` **9**. 견본 축약은 전건 걸리고 정본은 전건 통과한다.

산출 = `<콘티 폴더>/board_qa.json`
  { "cuts": 11, "modules": "H07 · S12 · M23", "structure": "CS-07", "camera_words": [14, 20, …],
    "camera_min": 13, "camera_median": 15, "thin_cuts": [], "verdict": "ok" }
"""
import json
import os
import re
import sys

CAM_MIN_WORDS = 9        # 카메라 서술 낱말 하한(위 실측 근거) — 이 밑 = 견본 축약을 베낀 것
_CUT = re.compile(r"^###\s*컷\s*(\d+)", re.M)
_CAM = re.compile(r"^CAMERA:\s*(.+)$", re.M)
_MOD = re.compile(r"^연출\s*모듈\s*:\s*(.+)$", re.M)
_STR = re.compile(r"^논평\s*구조\s*:\s*(.+)$", re.M)


def measure(md):
    """콘티 본문 → 분석 원장 dict(네트워크·모델 호출 0 · 순수 계산)."""
    cuts = _CUT.findall(md)
    cams = [c.strip() for c in _CAM.findall(md)]
    words = [len(c.split()) for c in cams]
    thin = [i + 1 for i, w in enumerate(words) if w < CAM_MIN_WORDS]
    mod = _MOD.search(md)
    stru = _STR.search(md)
    out = {
        "cuts": len(cuts),
        "camera_lines": len(cams),
        "modules": (mod.group(1).strip() if mod else ""),
        "structure": (stru.group(1).strip()[:120] if stru else ""),
        "camera_words": words,
        "camera_min": (min(words) if words else 0),
        "camera_median": (sorted(words)[len(words) // 2] if words else 0),
        "thin_cuts": thin,
        "cam_min_words": CAM_MIN_WORDS,
    }
    # verdict = 사람이 읽는 한 낱말 — 원장을 훑을 때 정렬·필터의 축이 된다
    if not words:
        out["verdict"] = "unknown"          # 컷을 못 읽었다(형식이 다르다)
    elif thin or not out["modules"]:
        out["verdict"] = "thin"
    else:
        out["verdict"] = "ok"
    return out


def main():
    if len(sys.argv) < 3:
        print("usage: sb_qa.py <board.md> <out_dir>")
        return 0
    md_path, out_dir = sys.argv[1], sys.argv[2]
    try:
        md = open(md_path, encoding="utf-8").read()
    except Exception as e:  # noqa: BLE001
        print("::warning::콘티 자기검문 건너뜀(본문 못 읽음): {}".format(str(e)[:120]))
        return 0
    try:
        qa = measure(md)
        with open(os.path.join(out_dir, "board_qa.json"), "w", encoding="utf-8") as f:
            json.dump(qa, f, ensure_ascii=False, indent=1)
    except Exception as e:  # noqa: BLE001
        print("::warning::콘티 자기검문 기록 실패(콘티는 그대로 진행): {}".format(str(e)[:160]))
        return 0

    # ⚠ 경고 문구가 **무엇을 고치면 되는지**까지 말해야 한다(알림 조치주체 규약 동축) —
    #   「얕다」만 남기면 다음 세션이 어느 자리를 고칠지 모른다.
    if not qa["modules"]:
        print("::warning::콘티 설계 요약에 `연출 모듈:` 줄이 없다 — 어느 카메라 값을 썼는지 기록이 0이라 "
              "나중에 「왜 잘 뽑혔나」를 되짚을 수 없다(감독 지침 2항 · prompts/sb-make.md)")
    if qa["thin_cuts"]:
        print("::warning::카메라 서술이 얕은 컷 {}개(컷 {}) — 낱말 {}개 미만은 판형 견본의 종전 축약 수준이다. "
              "정본 = 260816 정청래 판(샷 크기·렌즈/심도·높이/무브·빛/분위기 4요소 · 감독 지침 2-b)".format(
                  len(qa["thin_cuts"]), " · ".join(str(x) for x in qa["thin_cuts"][:12]), CAM_MIN_WORDS))
    print("콘티 자기검문 = 컷 {} · 카메라 낱말 최소 {} 중앙 {} · 연출 모듈 {} · 판정 {}".format(
        qa["cuts"], qa["camera_min"], qa["camera_median"],
        qa["modules"] or "(없음)", qa["verdict"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
