#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 루브릭 회귀 실행기(운영자 260803 승인) — breaking_judge RUBRIC 개정 시 과거 실측 판정(rubric_regress_cases.json)을
# 현행 RUBRIC으로 드라이런 재판정해 정답 뒤집힘(오컷·오발 회귀)을 사람 눈 대신 기계가 잡는다.
# 전부 통과 = rubric_regress_stamp.json 에 RUBRIC 해시 도장 → check_refs.check_rubric_regress 하드게이트가
# 「RUBRIC 변경 후 회귀 미실행」 커밋을 차단(정적 대조 = 게이트 자체는 네트워크·LLM 0 · LLM은 이 실행기 1콜뿐).
# 실패 = 스탬프 미갱신 + 뒤집힌 케이스 목록 출력 — RUBRIC을 고치든 기대값을 사유와 함께 바꾸든 사람이 결정.
# ⚠️ 케이스 제목엔 〔발행 1시간내〕 라벨을 강제 부착 = ⏱ 발행나이 게이트 중립화(회귀 대상은 내용 판정 축뿐).
import importlib.util
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
CASES = HERE / "rubric_regress_cases.json"
STAMP = HERE / "rubric_regress_stamp.json"

_spec = importlib.util.spec_from_file_location("breaking_judge", HERE / "breaking_judge.py")
_bj = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_bj)

_rspec = importlib.util.spec_from_file_location("regress_lib", HERE / "regress_lib.py")
_rl = importlib.util.module_from_spec(_rspec)
_rspec.loader.exec_module(_rl)

# 스탬프 전용 해시 = RUBRIC + 조립부 소스(regress_lib ⓒ). RUBRIC_VER(라이브 breaking 도장)는 무접촉.
_REGVER = _rl.regress_ver(_bj.RUBRIC, _bj.judge)


def main():
    cases = json.loads(CASES.read_text(encoding="utf-8"))["cases"]
    if "--check" in sys.argv:   # 정적 대조만(LLM 0) — check_refs 게이트와 동일 술어(수동 확인용)
        try:
            st = json.loads(STAMP.read_text(encoding="utf-8"))
        except Exception:
            print(f"❌ 스탬프 없음/파손 — python3 {Path(__file__).name} 실행으로 회귀 도장 필요")
            return 1
        ok = st.get("regress_ver") == _REGVER and st.get("cases") == len(cases)
        print(("✅ 스탬프 = 현행 RUBRIC+조립부" if ok else "❌ RUBRIC/조립부/케이스 변경 후 회귀 미실행")
              + f" (stamp={st.get('regress_ver')} · now={_REGVER})")
        nf = _rl.recent_fails("breaking", _REGVER)
        if nf:
            print(f"⚠ 같은 해시에서 최근 실패 {nf}회 — 원장 regress_runs.jsonl 확인(재실행으로 초록을 만든 건 아닌지).")
        return 0 if ok else 1

    items = [(str(i), f"{c['t']} 〔발행 1시간내〕") for i, c in enumerate(cases)]
    runs = int(os.environ.get("REGRESS_RUNS", _rl.DEFAULT_RUNS))
    print(f"회귀 드라이런 {len(items)}케이스 × {runs}회 다수결 · regress {_REGVER} · 모델 {_bj.MODEL}")
    verdicts, unstable, rcs = _rl.run_multi(lambda: _bj.judge(items), runs)   # judge 가 이미 (판정, rc, err) 3튜플
    if not verdicts:
        print(f"❌ judge 호출 전 회차 실패(rcs={rcs}) — 스탬프 미갱신.")
        _rl.log_run("breaking", _REGVER, len(cases), runs, rcs, [], [], {}, False)
        return 2
    flips, miss = [], []
    for i, c in enumerate(cases):
        v = verdicts.get(str(i))
        if v is None:
            miss.append(c["t"])
        elif ("YES" if v else "NO") != c["expect"]:
            flips.append((c, "YES" if v else "NO"))
    for c, got in flips:
        print(f"  ❌ 뒤집힘: expect {c['expect']} → got {got} | {c['t']} ({c['why']})")
    for t in miss:
        print(f"  ⚠ 응답 누락: {t}")
    if unstable:   # 회차마다 답이 갈린 케이스 = 정답지 자체의 흔들림(판정은 다수결로 이미 내려졌다)
        print(f"  ⚠ 흔들린 케이스 {len(unstable)}건(회차별 값): "
              + " · ".join(f"{k}={v}" for k, v in list(unstable.items())[:8]))
    _fl = [{"t": c["t"][:60], "expect": c["expect"], "got": got} for c, got in flips]
    _rl.log_run("breaking", _REGVER, len(cases), runs, rcs, _fl, [t[:60] for t in miss],
                {k: v for k, v in list(unstable.items())[:20]}, not (flips or miss))
    if flips or miss:
        print(f"❌ 회귀 실패 — 뒤집힘 {len(flips)} · 누락 {len(miss)} / {len(cases)}. RUBRIC을 고치거나, 방침 변경이면 기대값을 사유와 함께 개정하라.")
        print("   ⚠ 이 회차는 원장(regress_runs.jsonl)에 기록됐다 — 재실행으로 초록을 만들어도 실패 이력은 남는다.")
        return 1
    STAMP.write_text(json.dumps({
        "regress_ver": _REGVER, "rubric_ver": _bj.RUBRIC_VER, "cases": len(cases), "runs": runs,
        "ts": datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds"),
    }, ensure_ascii=False, indent=0) + "\n", encoding="utf-8")
    print(f"✅ 회귀 전건 통과 {len(cases)}/{len(cases)} · {runs}회 다수결 — 스탬프 도장(regress {_REGVER})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
