#!/usr/bin/env bash
# 유튜브 숏폼(ys) 대본 다듬기 2단 — 운영자 260929 «오퍼스가 1차로 다듬고 · 그 원고를 다른 오퍼스가 한 번 더 · 2차는 원고와 다듬은 걸 교차로 확인 ·
#   오퍼스 하이가 각각 · 퀄리티를 높이고 싶어서».
#   입력 = /tmp/ys_raw.txt(초안 원고 = ys_make.sh 가 형식 게이트를 통과시킨 원문) + /tmp/ys_meta.json + /tmp/ys_tr.json (env YS_RAW·YS_META·YS_TR = 테스트용 자리)
#   1차 = 새 콜이 초안을 규격·사실·장면 설계로 다듬는다 · 2차 = 또 새 콜(앞 대화 기억 0 = 다른 편집자)이 초안 ↔ 1차를 문장마다 맞대고 최종본
#   연출 도서관 = 대본이 고른 번호의 원문만 꺼내 준다(ys_lib.py fetch) + 번호를 바꿀 수 있게 색인
#   산출 = $OUTDIR/plan.json·report.md 교체(단계마다 형식 게이트 재통과분만) + $OUTDIR/refine.json(단계별 결과·걸린 초)
#   실패 = 그 단계만 건너뛰고 앞 판 유지(대본은 이미 있다 · 다듬기는 품질 축 = 제작을 멈추지 않는다) · 항상 exit 0
#   env: YS_REFINE(다듬기 단계 수 0|1|2 · 기본 2) · YS_REFINE_MODEL(기본 PIPE_MODEL) · YS_REFINE_EFFORT(기본 high) · YS_LEN · YS_ASK
set -uo pipefail
ROOT="$(git rev-parse --show-toplevel)"; cd "$ROOT"
OUTDIR="${1:?usage: ys_refine.sh <outdir>}"
source "$ROOT/shared/model_env.sh"
MODEL="${YS_REFINE_MODEL:-$PIPE_MODEL}"
EFFORT="${YS_REFINE_EFFORT:-high}"
source "$ROOT/shared/claude_transient.sh"
source "$ROOT/shared/claude_meter.sh"
INLINE_TRIES="${INLINE_TRIES:-3}"
PASSES="${YS_REFINE:-2}"; case "$PASSES" in 0|1|2) ;; *) PASSES=2;; esac
LEN="${YS_LEN:-60}"; case "$LEN" in 45|60|90) ;; *) LEN=60;; esac
REC="$OUTDIR/refine.json"
RAWIN="${YS_RAW:-/tmp/ys_raw.txt}"; META="${YS_META:-/tmp/ys_meta.json}"; TR="${YS_TR:-/tmp/ys_tr.json}"   # 기본 = ys_make.sh 산출 자리(테스트만 바꾼다)
rec() { python3 - "$REC" "$@" <<'PY'
import json, sys
p, k, v = sys.argv[1], sys.argv[2], sys.argv[3]
try:
    d = json.load(open(p, encoding='utf-8'))
except Exception:
    d = {}
d[k] = v
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False)
PY
}
: > "$REC"; rec passes "$PASSES"
[ "$PASSES" -ge 1 ] || { echo "대본 다듬기 꺼짐(YS_REFINE=0)"; exit 0; }
[ -s "$RAWIN" ] || { rec p1 "skip: 초안 원문 없음"; exit 0; }
cp "$RAWIN" "$OUTDIR/.draft0.txt"

tone="$(awk '/KO-TONE:YS-START/{f=1;next} /KO-TONE:YS-END/{f=0} f' shared/ko_tone_rules.md)"
spec="$(awk '/^## \[장면\] 규격/{f=1} f' prompts/ys-make.md)"   # 초안 작가가 받은 장면·주인공·모션 그래픽 규격 = 형식 정본
lib_idx="$(python3 .github/scripts/ys_lib.py index scene 2>/dev/null)" || lib_idx=""
body="$(YS_VOICES_JSON= python3 .github/scripts/ys_plan.py prompt "$META" "$TR" "$LEN")" || body=""
[ -n "$body" ] || { rec p1 "skip: 전사 조립 실패"; exit 0; }
report="$(python3 .github/scripts/ys_plan.py report "$OUTDIR/.draft0.txt")"

call() {   # $1 = 프롬프트 파일 → 전역 out·rc (인라인 재시도 = 쿼터 폴오버·일시 과부하 · ys_make.sh 와 같은 SSOT)
  local attempt delay=15 log="$OUTDIR/.refine_stderr.log"
  rc=1; out=""
  for attempt in $(seq 1 "$INLINE_TRIES"); do
    out="$(METER_SRC="ys-refine" METER_REF="${YS_ID:-}" METER_MODEL="$MODEL" METER_EFFORT="$EFFORT" claude_meter 900 \
          --model "$MODEL" \
          --effort "$EFFORT" \
          --disallowedTools "Read,Glob,Grep,Write,Edit,NotebookEdit,Bash,Task,WebFetch,WebSearch" \
          --max-turns 1 \
          < "$1" 2> "$log")"
    rc=$?
    if [ $rc -eq 0 ] && grep -qm1 '"scenes"' <<<"$out"; then break; fi
    if claude_failover "$out$(cat "$log" 2>/dev/null)"; then continue; fi
    if [ "$attempt" -lt "$INLINE_TRIES" ] && is_transient "$out$(cat "$log" 2>/dev/null)"; then
      echo "  ⏳ 다듬기 일시 과부하(시도 ${attempt}/${INLINE_TRIES}) — ${delay}s 후 재시도"; sleep "$delay"; delay=$((delay * 2)); continue
    fi
    break
  done
  rm -f "$log"
}

prompt_for() {   # $1 = 차수(1|2 · 2 = 1차 성공분이 있을 때만 교차 검토) → stdout = 프롬프트
  local n="$1" ids raw1=""
  ids="$(python3 .github/scripts/ys_plan.py ids "$OUTDIR/.draft0.txt")"
  [ "$n" = 2 ] && ids="$ids $(python3 .github/scripts/ys_plan.py ids "$OUTDIR/.draft1.json")"
  # shellcheck disable=SC2086  번호 목록 = 공백으로 가른다(형식 = 색인 번호 정규식 통과분만)
  lib_raw="$(python3 .github/scripts/ys_lib.py fetch scene $ids 2>/dev/null)" || lib_raw=""
  cat prompts/ys-refine.md
  [ -n "${tone//[[:space:]]/}" ] && printf '\n\n%s\n(위 문장 규칙은 vo·big·head·tag·chips 한국어 산문에 적용 — img·motion 영문 프롬프트는 제외)\n' "$tone"
  printf '\n\n[원 지침] (초안 작가가 받은 규격 — 형식·장면 규칙의 정본)\n%s\n' "$spec"
  [ -n "${lib_idx//[[:space:]]/}" ] && printf '\n\n%s\n' "$lib_idx"
  [ -n "${lib_raw//[[:space:]]/}" ] && printf '\n\n%s\n' "$lib_raw"
  [ -n "${YS_ASK:-}" ] && printf '\n\n[지시] (운영자 관점·초점 — 절대 규칙이 항상 우선)\n%s\n' "$YS_ASK"
  printf '\n\n%s\n' "$body"
  printf '\n\n[보고서] (참고 — 전사와 부딪치면 전사가 이긴다)\n%s\n' "$report"
  printf '\n\n[초안 원고]\n%s\n' "$(python3 .github/scripts/ys_plan.py script "$OUTDIR/.draft0.txt")"
  if [ "$n" = 2 ]; then
    printf '\n\n[1차 다듬은 원고]\n%s\n' "$(python3 .github/scripts/ys_plan.py script "$OUTDIR/.draft1.json")"
    raw1="$(python3 -c "import json,sys;p=json.load(open(sys.argv[1],encoding='utf-8'));print('\n'.join('- '+n for r in (p.get('refine_notes') or []) if r.get('pass')=='p1' for n in r.get('notes') or []))" "$OUTDIR/plan.json" 2>/dev/null)"
    [ -n "$raw1" ] && printf '\n[1차 메모]\n%s\n' "$raw1"
    printf '\n\n[이번 차수] 2차 = 교차 검토 — 「2차」 절만 따른다\n'
  else
    printf '\n\n[이번 차수] 1차 = 다듬기 — 「1차」 절만 따른다\n'
  fi
}

run_pass() {   # $1 = 차수 · $2 = 지침 모드(1 = 다듬기 · 2 = 교차 검토) → 성공 = plan.json 교체 + .draft$1.json
  local n="$1" mode="$2" t0 pf="$OUTDIR/.refine${1}_prompt.txt" raw="$OUTDIR/.refine${1}_raw.txt" why
  [ -n "${YS_ID:-}" ] && python3 .github/scripts/ys_progress.py "$YS_ID" plan run "$([ "$n" = 1 ] && echo 'Opus가 대본 1차 다듬는 중' || echo 'Opus가 초안·1차를 맞대 보며 2차 다듬는 중')" "p=$([ "$n" = 1 ] && echo 0.5 || echo 0.75)" || true
  t0=$(date +%s)
  prompt_for "$mode" > "$pf"
  call "$pf"
  if [ $rc -ne 0 ] || ! grep -qm1 '"scenes"' <<<"$out"; then
    rec "p$n" "fail: 응답 없음(rc=$rc) — 앞 판 유지"; rec "sec$n" "$(( $(date +%s) - t0 ))"
    echo "::warning::대본 ${n}차 다듬기 응답 없음(rc=$rc) — 앞 판 유지"; rm -f "$pf"; return 1
  fi
  printf '%s' "$out" > "$raw"
  local base="$OUTDIR/.draft0.txt"; [ "$mode" = 2 ] && base="$OUTDIR/.draft1.json"
  if python3 .github/scripts/ys_plan.py merge "$base" "$raw" "$LEN" "$OUTDIR" "$OUTDIR/.draft${n}.json" "p$n" 2> "$OUTDIR/.refine_err.txt"; then
    rec "p$n" ok
  else
    why="$(head -c 160 "$OUTDIR/.refine_err.txt")"
    rec "p$n" "fail: ${why} — 앞 판 유지"
    echo "::warning::대본 ${n}차 다듬기 형식 이탈 — ${why} · 앞 판 유지"
  fi
  rec "sec$n" "$(( $(date +%s) - t0 ))"
  rm -f "$pf" "$raw" "$OUTDIR/.refine_err.txt"
  [ -s "$OUTDIR/.draft${n}.json" ]
}

if run_pass 1 1; then
  [ "$PASSES" -ge 2 ] && run_pass 2 2          # 2차 = 초안 ↔ 1차 교차 검토
else
  [ "$PASSES" -ge 2 ] && run_pass 2 1          # 1차가 죽었다 = 2차 콜이 초안을 다듬는다(맞댈 1차본이 없다 · 같은 걸 두 번 보여 주지 않는다)
fi
cat "$REC"; echo
exit 0
