#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 회귀 실행기 공통 봉합(260810 · 진단서 §3 「회귀 도장이 이미 거짓말을 하고 있다」) —
# grade_regress.py · rubric_regress.py 두 실행기가 같은 사각 3종을 공유했다. 사본 2벌로 고치면
# 한쪽만 낡는 게 이 레포 최빈 드리프트(check_seal_completeness 가 이름 붙인 「같은 병의 형제」)라
# 정본 1개를 두 실행기가 *참조*한다.
#
# ■ 봉합한 사각 3종(전부 260810 실측 확인)
#  ⓐ n=1 코인플립 — 판정은 같은 입력에도 4.22% 흔들린다(단일 실행끼리 평균 불일치 · 30건 배치).
#     실행기가 한 번만 돌아서 **초록이 나올 때까지 재실행하면 도장이 찍혔다**. 실제로 260810
#     세션에서 grade 회귀가 1차 FAIL → 2차 PASS 로 도장이 갱신됐다(내용 동일·ts만 변경).
#     → k회(기본 3) 실행 후 **케이스별 다수결**로 판정한다. 진단서 실측 = 3회 다수결이 노이즈를
#       4.22% → 3.33% 로 21% 낮춘다. ⚠ 「k회 전건 일치」로 두면 안 된다 — 60케이스 규모에선
#       흔들리는 케이스가 늘 몇 건씩 있어(같은 입력 6회 전건 일치 27/30) 사실상 영구 FAIL 이 된다.
#  ⓑ 실패 기록 소실 — 실패는 화면 출력뿐이라 재실행하면 흔적이 사라졌다. 「빨간 회차가 있었다」를
#     아무도 알 수 없으니 재실행 은폐가 무증상이다.
#     → 성공·실패 **전 회차**를 원장(regress_runs.jsonl)에 남긴다. 도장은 지워도 원장은 남는다.
#  ⓒ 해시가 조립부를 안 본다 — 도장은 RUBRIC **문자열**만 해싱해서(RUBRIC_VER), 프롬프트 조립부
#     (judge() 의 listing 구성)를 바꾸면 해시가 그대로라 **회귀 0회로 라이브에 나갔다**(킬테스트 확인).
#     → 스탬프 전용 해시 = sha256(RUBRIC + judge 소스).
#     ⚠⚠ RUBRIC_VER 자체는 **절대 건드리지 않는다** — 그 값은 candidates.json 에 grade_rubric/
#        breaking_rubric 도장으로 박혀 있어서, 바꾸는 순간 재판정 창(48h) 안 전건이 되살아나 대량
#        재채점 = 과금 폭발이다(평의회 260810 「RUBRIC 변경 → 해시 변경 → 전건 재채점」 경고).
#        그래서 **회귀 스탬프용 해시를 분리**한다 = 조립부 변경은 회귀를 강제하되 라이브 도장은 무접촉.
# CONTRACT: check_grade_regress, check_rubric_regress
import hashlib
import inspect
import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
LEDGER = HERE / "regress_runs.jsonl"
LEDGER_MAX = 400            # 롤링 상한 — 원장은 증거지 아카이브가 아니다
DEFAULT_RUNS = 3            # k회(다수결 표본) · 실측 근거 = 3회 다수결이 노이즈 21% 감소


def regress_ver(rubric, judge_fn):
    """스탬프 전용 해시 = RUBRIC + 조립부 소스. RUBRIC_VER(라이브 도장)와 **다른 값**이어야 한다 —
    조립부만 바꾼 개정이 회귀를 우회하던 사각(ⓒ)을 막으면서 라이브 재채점은 안 건드린다."""
    try:
        src = inspect.getsource(judge_fn)
    except (OSError, TypeError):
        src = ""            # 소스 취득 실패 = 조립부 축 포기(rubric 축만) · 게이트를 죽이진 않는다
    return hashlib.sha256((rubric + "\x00" + src).encode("utf-8")).hexdigest()[:12]


def run_multi(call, runs=DEFAULT_RUNS):
    """call() → (verdict_dict, rc, err) 를 runs 회 실행하고 케이스별 다수결을 낸다.

    반환 = (merged, unstable, rcs)
      merged   : {key: 다수결 값}  — 전 회차 실패면 {}
      unstable : {key: [회차별 값…]} — 회차마다 답이 갈린 케이스(정답지 자체의 흔들림 노출)
      rcs      : 회차별 rc 목록
    ⚠ 한 회차가 실패해도 나머지로 다수결을 낸다(전 회차 실패일 때만 포기) — 호출 실패는 판정
      뒤집힘이 아니라 인프라 사고라, 그걸로 회귀를 FAIL 시키면 원인이 뭉개진다."""
    per, rcs = [], []
    for _ in range(max(1, runs)):
        v, rc, err = call()
        rcs.append(rc)
        if rc == 0 and v:
            per.append(v)
    if not per:
        return {}, {}, rcs
    keys = set()
    for v in per:
        keys |= set(v.keys())
    merged, unstable = {}, {}
    for k in sorted(keys):
        vals = [v[k] for v in per if k in v]
        if not vals:
            continue
        merged[k] = Counter(vals).most_common(1)[0][0]
        if len(set(vals)) > 1:
            unstable[k] = vals
    return merged, unstable, rcs


def log_run(kind, ver, cases, runs, rcs, flips, miss, unstable, passed):
    """성공·실패 **전 회차**를 원장에 남긴다(ⓑ). 도장은 재실행으로 덮이지만 원장은 누적된다.
    ⚠ 기계산출물 = 손편집 금지. 전 경로 fail-soft — 원장 사고가 회귀를 죽이면 안 된다."""
    try:
        rec = {
            "ts": datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds"),
            "kind": kind, "ver": ver, "cases": cases, "runs": runs, "rcs": rcs,
            "flips": flips, "miss": miss, "unstable": unstable, "pass": bool(passed),
        }
        lines = []
        if LEDGER.exists():
            lines = [x for x in LEDGER.read_text(encoding="utf-8").splitlines() if x.strip()]
        lines.append(json.dumps(rec, ensure_ascii=False))
        LEDGER.write_text("\n".join(lines[-LEDGER_MAX:]) + "\n", encoding="utf-8")
    except Exception:
        pass


def recent_fails(kind, ver, limit=6):
    """같은 해시에서 최근 실패 회차 수 — 「초록 나올 때까지 재실행」을 사람 눈에 보이게 한다.
    판정은 안 바꾼다(막지 않는다) · 보이게만 = check_gate_hits·check_component_lock 관례."""
    try:
        if not LEDGER.exists():
            return 0
        n = 0
        for line in LEDGER.read_text(encoding="utf-8").splitlines()[-limit * 4:]:
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("kind") == kind and r.get("ver") == ver and not r.get("pass"):
                n += 1
        return n
    except Exception:
        return 0
