#!/usr/bin/env bash
# 유튜브 숏폼(ys) 그록 연출 감독 — 장면별 클립 안 비트(초·MOTION·CAMERA) claude 2콜(운영자 260929 «예전 비디오 제작 방식과 절충»
#   · «라이브러리는 도서관 · 색인으로 구상하고 고른 것만 참조 · 그게 효과적이라고 판단하는 감독 알고리즘이 중요»).
#   ① 구상 = prompts/ys-grok-pick.md + [연출 색인] → 비트마다 기법 번호·이유($OUTDIR/grokpick.json)
#   ② 쓰기 = prompts/ys-grok.md + [감독 구상] + 고른 번호의 도서관 원문만 → motion·camera 문장
#   구상이 죽으면 쓰기 콜이 색인을 보고 스스로 고른다(예전 1콜과 같은 모양) · YS_GROK_PICK=0 = 구상 끔(A/B 레버)
#   입력 = $OUTDIR/plan.json + $OUTDIR/audio/timing.json(문장 박자) + /tmp/ys_meta.json(env YS_META = 테스트용 자리 · ys_refine.sh 동문) · 산출 = $OUTDIR/grokplan.json
#   워크플로가 **배경**으로 띄운다(맥 그림 대기와 겹쳐 시간 0 추가) → 끝나면 $OUTDIR/grokplan.done(성공·실패 무관 · 그록 스텝이 기다리는 신호).
#   모델 = PIPE_MODEL(오퍼스 5.5 · shared/model_env.sh 정본) · 노력 = high · 인증·폴오버 = ys_motion.sh 와 같은 SSOT 계약.
#   실패 = 전 장면 대체안(대본 motion 비트 1개) — 그록 발사는 멈추지 않는다.
set -uo pipefail
ROOT="$(git rev-parse --show-toplevel)"; cd "$ROOT"
OUTDIR="${1:?usage: ys_grok_plan.sh <outdir> <ratio>}"
RATIO="${2:-9:16}"
META="${YS_META:-/tmp/ys_meta.json}"   # 기본 = 워크플로 산출 자리(테스트만 바꾼다 — 러너 /tmp 잔재에 기대면 CI 에서만 죽는다)
trap 'touch "$OUTDIR/grokplan.done"' EXIT
source "$ROOT/shared/model_env.sh"
MODEL="${YS_GROK_PLAN_MODEL:-$PIPE_MODEL}"
EFFORT="${YS_GROK_PLAN_EFFORT:-high}"
source "$ROOT/shared/claude_transient.sh"
source "$ROOT/shared/claude_meter.sh"
INLINE_TRIES="${INLINE_TRIES:-3}"
PICK="$OUTDIR/grokpick.json"; rm -f "$PICK"
RAW="$OUTDIR/.grokplan_raw.txt"; : > "$RAW"
RAWP="$OUTDIR/.grokpick_raw.txt"; : > "$RAWP"

call() {   # $1 = 지침 파일 · $2 = 입력 블록 · $3 = 성공 표지 · $4 = 산출 파일 · $5 = 이름 → 성공 = $4 에 원문
  local prompt="$(cat "$1")

$2" log="$OUTDIR/.grokplan_stderr.log" delay=15 attempt out rc
  for attempt in $(seq 1 "$INLINE_TRIES"); do
    out="$(printf '%s' "$prompt" | METER_SRC="ys-grok" METER_REF="${YS_ID:-}" METER_MODEL="$MODEL" METER_EFFORT="$EFFORT" claude_meter 600 \
          --model "$MODEL" \
          --effort "$EFFORT" \
          --disallowedTools "Read,Glob,Grep,Write,Edit,NotebookEdit,Bash,Task,WebFetch,WebSearch" \
          --max-turns 1 \
          2> "$log")"
    rc=$?
    if [ $rc -eq 0 ] && grep -qm1 "$3" <<<"$out"; then printf '%s' "$out" > "$4"; rm -f "$log"; return 0; fi
    if claude_failover "$out$(cat "$log" 2>/dev/null)"; then continue; fi
    if [ "$attempt" -lt "$INLINE_TRIES" ] && is_transient "$out$(cat "$log" 2>/dev/null)"; then
      echo "  ⏳ 그록 ${5} 일시 과부하(시도 ${attempt}/${INLINE_TRIES}) — ${delay}s 후 재시도"; sleep "$delay"; delay=$((delay * 2)); continue
    fi
    echo "  그록 ${5} 응답 없음(rc=$rc)"
    break
  done
  rm -f "$log"
  return 1
}

# ① 구상 — 색인만 보고 비트·번호·이유(실패 = 쓰기 콜이 색인으로 대신)
if [ "${YS_GROK_PICK:-1}" != 0 ]; then
  pbody="$(python3 .github/scripts/ys_grok_plan.py pick-prompt "$OUTDIR/plan.json" "$OUTDIR/audio/timing.json" "$META" "$RATIO")" || pbody=""
  if [ -n "$pbody" ] && call prompts/ys-grok-pick.md "$pbody" '"scenes"' "$RAWP" 구상; then
    python3 .github/scripts/ys_grok_plan.py pick-parse "$RAWP" "$OUTDIR/plan.json" "$OUTDIR/audio/timing.json" "$PICK" || echo "  구상 산출이 비었다 — 쓰기 콜이 색인으로 고른다"
  fi
fi
rm -f "$RAWP"
# ② 쓰기 — 구상 + 고른 번호 원문만(구상 없음 = 색인)
body="$(python3 .github/scripts/ys_grok_plan.py prompt "$OUTDIR/plan.json" "$OUTDIR/audio/timing.json" "$META" "$RATIO" "$PICK")" || body=""
if [ -n "$body" ]; then
  call prompts/ys-grok.md "$body" '"clips"' "$RAW" 쓰기 || echo "  대본 움직임으로 대체"
fi
python3 .github/scripts/ys_grok_plan.py parse "$RAW" "$OUTDIR/plan.json" "$OUTDIR/audio/timing.json" "$OUTDIR/grokplan.json" "$PICK"
prc=$?
rm -f "$RAW"
exit $prc
