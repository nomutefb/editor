#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sb_audit.py — 콘티가 **정말 라이브러리를 보고 짜였는지** 그 자리에서 검증한다.

  sb_audit.py <board.md> <out_dir>

⚠ 왜 필요했나(운영자 260813 「각 파이프라인이 제대로 돌고있는지 검증이 안되네」) =
  감독 지침은 「연출 라이브러리를 훑고 쓴 모듈 번호를 설계 요약에 남겨라」인데, 그 번호가
  **실재하는 값인지 아무도 안 봤다.** 지어낸 번호를 적어도 콘티는 멀쩡해 보이고 영상도 나온다
  = 라이브러리가 죽어도 화면 증상이 0인 구조였다(사람이 손으로 대조해야만 드러난다).
  → 번호를 라이브러리 실파일과 대조해 산출에 박제한다. 다음 세션이 추측할 자리가 없어진다.

⚠ **막지는 않는다**(경고만) — 감독이 라이브러리 밖 표현을 쓰는 것 자체는 정당할 수 있고,
  콘티는 이미 나온 뒤라 여기서 죽이면 그 판이 통째로 버려진다. 대신 숫자로 남긴다.

⚠ 네트워크·LLM 0. 파일 대조뿐이다.

CONTRACT: check_grok_sb_chain
"""
import json
import os
import re
import sys

LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "apps", "k", "library")
# 설계 요약의 `연출 모듈: L06 · H15 · M32 · VR-28` 한 줄(감독 지침이 정한 형식)
_LINE = re.compile(r"^연출\s*모듈\s*[:：]\s*(.+)$", re.M)
# 설계 요약의 `논평 구조: CS-01 — {이유}` 한 줄(절차 0-c · 260813 신설)
# ⚠ 왜 검사하나 = 이 줄이 **작품 단위 각**을 고른 유일한 흔적이다. 없으면 감독이 각을 안 고르고
#   바로 컷부터 쓴 것이고, 그 판은 실측상 기사를 그림으로 옮긴 삽화가 된다(260813 실사고).
#   지침만 고치고 검사를 안 두면 지켜졌는지 아무도 모른다 — 이 레포가 반복해 겪은 자리다.
_CS_LINE = re.compile(r"^논평\s*구조\s*[:：]\s*(.+)$", re.M)
# 모듈 번호 = 영문 대문자 접두 + 숫자(하이픈 있는 것도 있다: COMP-04 · VR-28)
_ID = re.compile(r"\b([A-Z]{1,4}-?\d{2,3})\b")


def cited(md):
    """콘티가 인용한 모듈 번호(문서 순·중복 제거)."""
    m = _LINE.search(md)
    if not m:
        return []
    seen, out = set(), []
    for i in _ID.findall(m.group(1)):
        if i not in seen:
            seen.add(i)
            out.append(i)
    return out


def structure(md, have):
    """고른 논평 구조 — (표기 문자열, 번호, 실재 여부). 줄 자체가 없으면 (None, ...)."""
    m = _CS_LINE.search(md)
    if not m:
        return None, None, False
    txt = m.group(1).strip()
    hit = re.search(r"\bCS-\d{2}\b", txt)
    if not hit:
        # 「없음 — 왜 안 골랐는가」도 정당한 답이다(억지로 끼워 맞춘 구조가 더 나쁘다).
        return txt, None, True
    return txt, hit.group(0), hit.group(0) in have


def known():
    """라이브러리가 실제로 들고 있는 번호 전부(유닛 TSV 첫 칸)."""
    ids = set()
    try:
        for fn in sorted(os.listdir(LIB)):
            if not fn.endswith(".tsv") or fn.startswith("archive_"):
                continue
            with open(os.path.join(LIB, fn), encoding="utf-8", errors="replace") as f:
                for ln in f:
                    head = ln.split("\t", 1)[0].strip()
                    if _ID.fullmatch(head):
                        ids.add(head)
    except Exception as e:  # noqa: BLE001
        print("::warning::라이브러리를 못 읽었다(검증 생략): {}".format(str(e)[:160]))
    return ids


def main():
    if len(sys.argv) < 3:
        sys.exit("usage: sb_audit.py <board.md> <out_dir>")
    md_path, out_dir = sys.argv[1], sys.argv[2]
    try:
        md = open(md_path, encoding="utf-8").read()
    except Exception as e:  # noqa: BLE001
        print("::warning::콘티를 못 읽었다(검증 생략): {}".format(str(e)[:160]))
        return 0
    use = cited(md)
    have = known()
    if not have:
        print("콘티 검증: 미시도(라이브러리 목록이 비었다)")   # 무성 스킵 금지(계측 문법)
        return 0
    bad = [i for i in use if i not in have]
    cs_txt, cs_id, cs_ok = structure(md, have)
    rec = {"cited": use, "unknown": bad, "library_ids": len(have),
           "structure": cs_txt, "structure_id": cs_id, "structure_ok": cs_ok}
    try:
        with open(os.path.join(out_dir, "audit.json"), "w", encoding="utf-8") as f:
            json.dump(rec, f, ensure_ascii=False)
    except Exception as e:  # noqa: BLE001
        print("::warning::검증 기록 실패(비치명): {}".format(str(e)[:140]))
    # 논평 구조 = 작품 단위 각을 고른 흔적. 먼저 말한다(컷 단위 모듈보다 상위 판단이다).
    if cs_txt is None:
        print("콘티 검증: 논평 구조 줄 없음 — 각을 안 고르고 컷부터 썼다는 뜻이다")
        print("::warning::설계 요약에 「논평 구조:」 줄이 없다(지침 절차 0-c · 표 = 48_commentary_structures)")
    elif not cs_ok:
        print("콘티 검증: 논평 구조 {} — 표에 없는 번호다".format(cs_id))
        print("::warning::논평 구조 {} 가 48_commentary_structures 에 없다 — 지어낸 값일 수 있다".format(cs_id))
    else:
        print("콘티 검증: 논평 구조 {}".format(cs_txt[:120]))
    if not use:
        # 인용 줄 자체가 없다 = 라이브러리를 안 봤거나 형식을 안 지켰다. 둘 다 알아야 한다.
        print("콘티 검증: 인용 모듈 0개 — 감독이 라이브러리를 안 봤거나 표기 형식이 어긋났다")
        print("::warning::콘티에 연출 모듈 인용이 없다(지침은 「쓴 ID 를 설계 요약에 남겨라」)")
        return 0
    print("콘티 검증: 인용 {}개 · 라이브러리 실재 {}개 · 모르는 값 {}개{}".format(
        len(use), len(use) - len(bad), len(bad), (" = " + ", ".join(bad)) if bad else ""))
    if bad:
        print("::warning::콘티가 라이브러리에 없는 모듈을 인용했다({}) — 지어낸 값일 수 있다"
              .format(", ".join(bad[:8])))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:  # noqa: BLE001
        print("::warning::sb_audit 예외(비치명): {}".format(str(e)[:200]))
        sys.exit(0)
