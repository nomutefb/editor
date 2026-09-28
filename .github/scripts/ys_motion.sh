#!/usr/bin/env bash
# 유튜브 숏폼(ys) 모션 디자이너 — 장면별 모션 그래픽 코드 claude 1콜(운영자 260928 «LLM 이 들어가야 품질이 오르면 opus 5.5 high»).
#   입력 = $OUTDIR/plan.json + $OUTDIR/audio/timing.json(문장 박자) + /tmp/ys_meta.json · 산출 = $OUTDIR/motion.json
#   장면 ≤4개씩 병렬 콜(ys_motion.py chunks) · YS_MOTION_ONLY = 맡을 장면(맥·그록 대체분 · 비면 전부)
#   모델 = PIPE_MODEL(오퍼스 5.5 · shared/model_env.sh 정본) · 노력 = high · 인증·폴오버 = ys_make.sh 와 같은 SSOT 계약.
#   실패 = rc 1 + $OUTDIR/motion_err.txt(사유 한 줄) — 워크플로는 멈추지 않고 렌더가 기본 도식(ys_mg)으로 채운다.
set -uo pipefail
ROOT="$(git rev-parse --show-toplevel)"; cd "$ROOT"
source "$ROOT/shared/model_env.sh"
MODEL="${YS_MOTION_MODEL:-$PIPE_MODEL}"
EFFORT="${YS_MOTION_EFFORT:-high}"
source "$ROOT/shared/claude_transient.sh"
source "$ROOT/shared/claude_meter.sh"
INLINE_TRIES="${INLINE_TRIES:-3}"
OUTDIR="${1:?usage: ys_motion.sh <outdir> <ratio>}"
RATIO="${2:-9:16}"
N="$(python3 -c "import json;print(len(json.load(open('$OUTDIR/plan.json'))['scenes']))")" || N=0
[ "$N" -gt 0 ] || { echo "대본 장면이 없어" > "$OUTDIR/motion_err.txt"; exit 1; }

# 병렬 분할(260928 실측 = 7장면 1콜 667초 · 90초 영상이면 20분 상한에 닿는다) → 장면 ≤4개씩 동시에 콜 · 조각별 실패는 그 장면만 기본 도식.
mapfile -t CHUNKS < <(python3 .github/scripts/ys_motion.py chunks "$N" 4)
[ "${#CHUNKS[@]}" -gt 0 ] || { echo "모션 디자인 대상 장면이 없어" > "$OUTDIR/motion_err.txt"; exit 1; }
MARK='"scenes"'

run_chunk() {   # $1 = 조각 번호 · $2 = 장면 번호 목록 → $OUTDIR/.mraw_$1.txt (실패 = 빈 파일 없음 + .merr_$1.txt)
  local k="$1" ids="$2" body prompt out rc attempt delay=15 log="$OUTDIR/.mstderr_$1.log"
  body="$(YS_MOTION_ONLY="$ids" python3 .github/scripts/ys_motion.py prompt "$OUTDIR/plan.json" "$OUTDIR/audio/timing.json" /tmp/ys_meta.json "$RATIO")" \
    || { echo "입력 조립 실패" > "$OUTDIR/.merr_$k.txt"; return 1; }
  prompt="$(cat prompts/ys-motion.md)

${body}"
  rc=1; out=""
  for attempt in $(seq 1 "$INLINE_TRIES"); do
    out="$(printf '%s' "$prompt" | METER_SRC="ys-motion" METER_REF="${YS_ID:-}" METER_MODEL="$MODEL" METER_EFFORT="$EFFORT" claude_meter 1200 \
          --model "$MODEL" \
          --effort "$EFFORT" \
          --disallowedTools "Read,Glob,Grep,Write,Edit,NotebookEdit,Bash,Task,WebFetch,WebSearch" \
          --max-turns 1 \
          2> "$log")"
    rc=$?
    if [ $rc -eq 0 ] && grep -qm1 "$MARK" <<<"$out"; then break; fi
    if claude_failover "$out$(cat "$log" 2>/dev/null)"; then continue; fi
    if [ "$attempt" -lt "$INLINE_TRIES" ] && is_transient "$out$(cat "$log" 2>/dev/null)"; then
      echo "  ⏳ 모션 디자인 조각 $k 일시 과부하(시도 ${attempt}/${INLINE_TRIES}) — ${delay}s 후 재시도"; sleep "$delay"; delay=$((delay * 2)); continue
    fi
    break
  done
  rm -f "$log"
  if [ $rc -ne 0 ] || ! grep -qm1 "$MARK" <<<"$out"; then
    echo "응답 없음(rc=$rc)" > "$OUTDIR/.merr_$k.txt"; return 1
  fi
  printf '%s' "$out" > "$OUTDIR/.mraw_$k.txt"
}

pids=()
for k in "${!CHUNKS[@]}"; do
  echo "  모션 디자인 조각 $((k + 1))/${#CHUNKS[@]} = 장면 ${CHUNKS[$k]}"
  run_chunk "$k" "${CHUNKS[$k]}" & pids+=($!)
  sleep 2   # 동시 기동 순간 몰림 완화
done
for p in "${pids[@]}"; do wait "$p" || true; done

raws="$(ls "$OUTDIR"/.mraw_*.txt 2>/dev/null | paste -sd, -)"
errs="$(cat "$OUTDIR"/.merr_*.txt 2>/dev/null | sort -u | paste -sd' ' -)"
if [ -z "$raws" ]; then
  echo "모션 디자인(Claude)이 응답하지 않았어(${errs:-원인 미상}) — 기본 도식으로 만들었어." > "$OUTDIR/motion_err.txt"
  rm -f "$OUTDIR"/.mraw_*.txt "$OUTDIR"/.merr_*.txt; exit 1
fi
python3 .github/scripts/ys_motion.py parse "$raws" "$OUTDIR" "$N" 2> /tmp/ys_motion_parse.txt; prc=$?
rm -f "$OUTDIR"/.mraw_*.txt "$OUTDIR"/.merr_*.txt
if [ $prc -ne 0 ]; then
  echo "모션 디자인 결과 형식이 깨졌어 — 기본 도식으로 만들었어. ($(head -c 100 /tmp/ys_motion_parse.txt))" > "$OUTDIR/motion_err.txt"; exit 1
fi
[ -n "$errs" ] && echo "모션 디자인 일부 조각 실패(${errs}) — 그 장면은 기본 도식으로 만들었어." > "$OUTDIR/motion_err.txt"
exit 0
