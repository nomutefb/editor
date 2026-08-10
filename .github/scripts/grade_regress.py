#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# grade 룰북 회귀 실행기(운영자 260807 "전부 반영" · rubric_regress.py[breaking 전용] 문법 계승) —
# gate_judge RUBRIC(경중 0~3 채점 프롬프트) 개정 시 운영자 수기 재채점 정답지(grade_regress_cases.json ·
# 260807 ~58행 = 평의회 8인 검증분)를 드라이런 재채점해 정답 뒤집힘이 0이어야 스탬프가 찍힌다.
# 전부 통과 = grade_regress_stamp.json 에 RUBRIC 해시 도장 → check_refs.check_grade_regress 하드게이트가
# 「RUBRIC 변경 후 회귀 미실행」 커밋을 차단(정적 대조 = 게이트 자체는 네트워크·LLM 0 · LLM은 이 실행기 1콜뿐).
# 실패 = 스탬프 미갱신 + 뒤집힌 케이스 목록 출력 — RUBRIC을 고치든 기대값을 사유와 함께 바꾸든 사람이 결정.
# ⚠️ 신설 사유 = breaking 룰북엔 회귀 게이트가 있는데 grade 룰북은 무게이트였다(평의회 260807 구현 렌즈 실측) —
#    운영자 260807 "잘못 매기면 큐레이션 의미가 사라지고 잘못된 걸 요약하는 비용이 허수가 됨"의 기계화.
# CONTRACT: check_grade_regress
import importlib.util
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
CASES = HERE / "grade_regress_cases.json"
STAMP = HERE / "grade_regress_stamp.json"

_spec = importlib.util.spec_from_file_location("gate_judge", HERE / "gate_judge.py")
_gj = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_gj)

_rspec = importlib.util.spec_from_file_location("regress_lib", HERE / "regress_lib.py")
_rl = importlib.util.module_from_spec(_rspec)
_rspec.loader.exec_module(_rl)

# 스탬프 전용 해시 = RUBRIC + 조립부 소스(regress_lib ⓒ). RUBRIC_VER(라이브 grade_rubric 도장)는
# 무접촉 — 그걸 바꾸면 재판정 창 안 전건이 되살아나 대량 재채점이 된다.
_REGVER = _rl.regress_ver(_gj.RUBRIC, _gj.judge)


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
        nf = _rl.recent_fails("grade", _REGVER)
        if nf:
            print(f"⚠ 같은 해시에서 최근 실패 {nf}회 — 원장 regress_runs.jsonl 확인(재실행으로 초록을 만든 건 아닌지).")
        return 0 if ok else 1

    items = [(str(i), c["t"]) for i, c in enumerate(cases)]
    runs = int(os.environ.get("REGRESS_RUNS", _rl.DEFAULT_RUNS))
    print(f"grade 회귀 드라이런 {len(items)}케이스 × {runs}회 다수결 · regress {_REGVER} · 모델 {_gj.MODEL}")
    def _call():                     # judge 5튜플 → run_multi 계약(판정, rc, err)로 어댑트
        g, _c, _t, rc, err = _gj.judge(items)
        return g, rc, err
    grades, unstable, rcs = _rl.run_multi(_call, runs)
    if not grades:
        print(f"❌ judge 호출 전 회차 실패(rcs={rcs}) — 스탬프 미갱신.")
        _rl.log_run("grade", _REGVER, len(cases), runs, rcs, [], [], {}, False)
        return 2
    flips, miss = [], []
    for i, c in enumerate(cases):
        v = grades.get(str(i))
        if v is None:
            miss.append(c["t"])
        elif v != c["expect"]:
            flips.append((c, v))
    for c, got in flips:
        print(f"  ❌ 뒤집힘: expect {c['expect']} → got {got} | {c['t']} ({c['why']})")
    for t in miss:
        print(f"  ⚠ 응답 누락: {t}")
    if unstable:   # 회차마다 답이 갈린 케이스 = 정답지 자체의 흔들림(판정은 다수결로 이미 내려졌다)
        print(f"  ⚠ 흔들린 케이스 {len(unstable)}건(회차별 값): "
              + " · ".join(f"{k}={v}" for k, v in list(unstable.items())[:8]))
    _fl = [{"t": c["t"][:60], "expect": c["expect"], "got": got} for c, got in flips]
    _rl.log_run("grade", _REGVER, len(cases), runs, rcs, _fl, [t[:60] for t in miss],
                {k: v for k, v in list(unstable.items())[:20]}, not (flips or miss))
    if flips or miss:
        print(f"❌ 회귀 실패 — 뒤집힘 {len(flips)} · 누락 {len(miss)} / {len(cases)}. RUBRIC을 고치거나, 방침 변경이면 기대값을 사유와 함께 개정하라.")
        print("   ⚠ 이 회차는 원장(regress_runs.jsonl)에 기록됐다 — 재실행으로 초록을 만들어도 실패 이력은 남는다.")
        return 1
    STAMP.write_text(json.dumps({
        "regress_ver": _REGVER, "rubric_ver": _gj.RUBRIC_VER, "cases": len(cases), "runs": runs,
        "ts": datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds"),
    }, ensure_ascii=False, indent=0) + "\n", encoding="utf-8")
    print(f"✅ 회귀 전건 통과 {len(cases)}/{len(cases)} · {runs}회 다수결 — 스탬프 도장(regress {_REGVER})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
