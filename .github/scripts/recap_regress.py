#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 되새김 검토 회귀 실행기(운영자 261001 · 짝 = rubric_regress.py) — recap_check 의 프롬프트·조립부를 고치면
# 정답지(recap_regress_cases.json · 실발송 원문 스냅샷 + 경계 사례)를 실제 AI 로 다시 판정해 뒤집힘을 기계가 잡는다.
# 전부 통과 = recap_regress_stamp.json 도장 → check_refs.check_recap_regress 가 「프롬프트 변경 후 회귀 미실행」 커밋을 차단
# (게이트 자체는 정적 해시 대조 = 네트워크·LLM 0). 원문은 케이스에 박제된 스냅샷을 쓴다 = 매체 사정과 무관하게 같은 입력.
# 사용: python3 .github/scripts/recap_regress.py [--check]   (REGRESS_RUNS = 다수결 회차 · 기본 regress_lib.DEFAULT_RUNS)
import importlib.util
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
CASES = HERE / "recap_regress_cases.json"
STAMP = HERE / "recap_regress_stamp.json"
sys.path.insert(0, str(HERE))
import recap_check as RC  # noqa: E402

_rspec = importlib.util.spec_from_file_location("regress_lib", HERE / "regress_lib.py")
_rl = importlib.util.module_from_spec(_rspec)
_rspec.loader.exec_module(_rl)

# 스탬프 해시 = 프롬프트 본문 + 조립부(build_prompt) — 둘 중 하나만 바뀌어도 회귀 재실행.
_REGVER = _rl.regress_ver(RC._PROMPT, RC.build_prompt)


def regress_ver():
    return _REGVER


def _entry(c):
    return {"title": c["t"], "media": c.get("media"), "cat": c.get("cat"), "published": c.get("published"), "url": c.get("url")}


def main():
    cases = json.loads(CASES.read_text(encoding="utf-8"))["cases"]
    if "--check" in sys.argv:
        try:
            st = json.loads(STAMP.read_text(encoding="utf-8"))
        except Exception:
            print(f"❌ 스탬프 없음/파손 — python3 {Path(__file__).name} 실행으로 회귀 도장 필요")
            return 1
        ok = st.get("regress_ver") == _REGVER and st.get("cases") == len(cases)
        print(("✅ 스탬프 = 현행 프롬프트+조립부" if ok else "❌ 프롬프트/조립부/케이스 변경 후 회귀 미실행") + f" (stamp={st.get('regress_ver')} · now={_REGVER})")
        return 0 if ok else 1

    items = [(str(i), _entry(c), c.get("src") or "") for i, c in enumerate(cases)]
    expected = {k for k, _, _ in items}

    def once():
        out, err = RC._ask(RC.build_prompt(items))
        if out is None:
            return {}, 1, err
        v = RC.parse(out, expected)
        return v, (0 if v else 3), ("" if v else f"해석 불가: {out[:120]!r}")

    runs = int(os.environ.get("REGRESS_RUNS", _rl.DEFAULT_RUNS))
    print(f"되새김 회귀 {len(items)}케이스 × {runs}회 다수결 · regress {_REGVER} · 모델 {RC.MODEL}")
    verdicts, unstable, rcs = _rl.run_multi(once, runs)
    if not verdicts:
        print(f"❌ 호출 전 회차 실패(rcs={rcs}) — 스탬프 미갱신.")
        _rl.log_run("recap", _REGVER, len(cases), runs, rcs, [], [], {}, False)
        return 2
    flips, miss = [], []
    for i, c in enumerate(cases):
        v = verdicts.get(str(i))
        if v is None:
            miss.append(c["t"])
        elif ("RECAP" if v else "FRESH") != c["expect"]:
            flips.append((c, "RECAP" if v else "FRESH"))
    for c, got in flips:
        print(f"  ❌ 뒤집힘: expect {c['expect']} → got {got} | {c['t']} ({c['why']})")
    for t in miss:
        print(f"  ⚠ 응답 누락: {t}")
    if unstable:
        print(f"  ⚠ 흔들린 케이스 {len(unstable)}건(회차별 값): " + " · ".join(f"{k}={v}" for k, v in list(unstable.items())[:8]))
    _fl = [{"t": c["t"][:60], "expect": c["expect"], "got": got} for c, got in flips]
    _rl.log_run("recap", _REGVER, len(cases), runs, rcs, _fl, [t[:60] for t in miss],
                {k: v for k, v in list(unstable.items())[:20]}, not (flips or miss))
    if flips or miss:
        print(f"❌ 회귀 실패 — 뒤집힘 {len(flips)} · 누락 {len(miss)} / {len(cases)}. 프롬프트를 고치거나, 방침 변경이면 기대값을 사유와 함께 개정하라.")
        return 1
    STAMP.write_text(json.dumps({
        "regress_ver": _REGVER, "cases": len(cases), "runs": runs, "model": RC.MODEL,
        "ts": datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds"),
    }, ensure_ascii=False, indent=0) + "\n", encoding="utf-8")
    print(f"✅ 되새김 회귀 전건 통과 {len(cases)}/{len(cases)} · {runs}회 다수결 — 스탬프 도장(regress {_REGVER})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
