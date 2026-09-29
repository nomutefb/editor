#!/usr/bin/env bash
# 유튜브 숏폼(ys) 그록 연출 감독 — 장면별 클립 안 비트(초·MOTION·CAMERA) claude 1콜(운영자 260929 «예전 비디오 제작 방식과 절충»).
#   입력 = $OUTDIR/plan.json + $OUTDIR/audio/timing.json(문장 박자) + /tmp/ys_meta.json · 산출 = $OUTDIR/grokplan.json
#   워크플로가 **배경**으로 띄운다(맥 그림 대기와 겹쳐 시간 0 추가) → 끝나면 $OUTDIR/grokplan.done(성공·실패 무관 · 그록 스텝이 기다리는 신호).
#   모델 = PIPE_MODEL(오퍼스 5.5 · shared/model_env.sh 정본) · 노력 = high · 인증·폴오버 = ys_motion.sh 와 같은 SSOT 계약.
#   실패 = 전 장면 대체안(대본 motion 비트 1개) — 그록 발사는 멈추지 않는다.
set -uo pipefail
ROOT="$(git rev-parse --show-toplevel)"; cd "$ROOT"
OUTDIR="${1:?usage: ys_grok_plan.sh <outdir> <ratio>}"
RATIO="${2:-9:16}"
trap 'touch "$OUTDIR/grokplan.done"' EXIT
source "$ROOT/shared/model_env.sh"
MODEL="${YS_GROK_PLAN_MODEL:-$PIPE_MODEL}"
EFFORT="${YS_GROK_PLAN_EFFORT:-high}"
source "$ROOT/shared/claude_transient.sh"
source "$ROOT/shared/claude_meter.sh"
INLINE_TRIES="${INLINE_TRIES:-3}"
MARK='"clips"'
RAW="$OUTDIR/.grokplan_raw.txt"; : > "$RAW"
body="$(python3 .github/scripts/ys_grok_plan.py prompt "$OUTDIR/plan.json" "$OUTDIR/audio/timing.json" /tmp/ys_meta.json "$RATIO")" || body=""
if [ -n "$body" ]; then
  prompt="$(cat prompts/ys-grok.md)

${body}"
  log="$OUTDIR/.grokplan_stderr.log"; delay=15
  for attempt in $(seq 1 "$INLINE_TRIES"); do
    out="$(printf '%s' "$prompt" | METER_SRC="ys-grok" METER_REF="${YS_ID:-}" METER_MODEL="$MODEL" METER_EFFORT="$EFFORT" claude_meter 600 \
          --model "$MODEL" \
          --effort "$EFFORT" \
          --disallowedTools "Read,Glob,Grep,Write,Edit,NotebookEdit,Bash,Task,WebFetch,WebSearch" \
          --max-turns 1 \
          2> "$log")"
    rc=$?
    if [ $rc -eq 0 ] && grep -qm1 "$MARK" <<<"$out"; then printf '%s' "$out" > "$RAW"; break; fi
    if claude_failover "$out$(cat "$log" 2>/dev/null)"; then continue; fi
    if [ "$attempt" -lt "$INLINE_TRIES" ] && is_transient "$out$(cat "$log" 2>/dev/null)"; then
      echo "  ⏳ 그록 연출 일시 과부하(시도 ${attempt}/${INLINE_TRIES}) — ${delay}s 후 재시도"; sleep "$delay"; delay=$((delay * 2)); continue
    fi
    echo "  그록 연출 응답 없음(rc=$rc) — 대본 움직임으로 대체"
    break
  done
  rm -f "$log"
fi
python3 .github/scripts/ys_grok_plan.py parse "$RAW" "$OUTDIR/plan.json" "$OUTDIR/audio/timing.json" "$OUTDIR/grokplan.json"
prc=$?
rm -f "$RAW"
exit $prc
