#!/usr/bin/env bash
# 유튜브 숏폼(ys) — 전사 → claude 1콜(인사이트 보고서 + 인포그래픽 문안 + 숏폼 장면 JSON) (운영자 260928 · 기존 레인과 독립)
#   전사 = /tmp/ys_tr.json(nb_sub.py 산출 포맷) · 메타 = /tmp/ys_meta.json · 산출 = $OUTDIR/{plan.json,report.md}
#   문체 = shared/ko_tone_rules.md 의 ys 전용 구간(KO-TONE:YS · im-not-ai v2.8) — 뉴스 요약·카드 구간은 읽지 않는다.
#   인증 = 구독 OAuth · 폴오버 SSOT = nbmake.sh 동일 계약. 실패 = $OUTDIR/error.log + exit 1.
#   env: YS_ASK(운영자 지시·선택) · YS_LEN(목표 초 45|60|90)
set -uo pipefail
ROOT="$(git rev-parse --show-toplevel)"; cd "$ROOT"
source "$ROOT/shared/model_env.sh"   # 모델 단일 원천(PIPE_MODEL — 생성/창작 = opus 유지)
MODEL="${YS_MODEL:-$PIPE_MODEL}"
YS_EFFORT="${YS_EFFORT:-high}"
source "$ROOT/shared/claude_transient.sh"  # is_quota()/claude_failover()/is_transient() SSOT — 4계정 로테이션
source "$ROOT/shared/claude_meter.sh"      # claude_meter() SSOT — 토큰 계측
INLINE_TRIES="${INLINE_TRIES:-4}"
OUTDIR="${1:?usage: ys_make.sh <outdir>}"; mkdir -p "$OUTDIR"
LEN="${YS_LEN:-60}"; case "$LEN" in 45|60|90) ;; *) LEN=60;; esac

[ -s /tmp/ys_meta.json ] || { echo "영상 정보를 못 읽었어 — 링크를 확인해줘." > "$OUTDIR/error.log"; exit 1; }
[ -s /tmp/ys_tr.json ]   || { echo "자막·받아쓰기 결과가 없어 — 자막 없는 영상이면 '정밀 받아쓰기'로 다시 해줘." > "$OUTDIR/error.log"; exit 1; }

body="$(python3 .github/scripts/ys_plan.py prompt /tmp/ys_meta.json /tmp/ys_tr.json "$LEN")" \
  || { echo "전사 조립 실패 — 다시 시도해줘." > "$OUTDIR/error.log"; exit 1; }
tone="$(awk '/KO-TONE:YS-START/{f=1;next} /KO-TONE:YS-END/{f=0} f' shared/ko_tone_rules.md)"
[ -n "${tone//[[:space:]]/}" ] || echo "::warning::문체 정본 ys 구간 부재 — 문체 규칙 없이 진행"
prompt="$(cat prompts/ys-make.md)"
[ -n "${tone//[[:space:]]/}" ] && prompt="$prompt

${tone}
(위 문장 규칙은 report_md·장면 vo·인포그래픽 문안 산문에 적용 — 인용·고유 표기·img 영문 프롬프트는 제외)"
[ -n "${YS_ASK:-}" ] && prompt="$prompt

[지시] (운영자 관점·초점 — 절대 규칙이 항상 우선)
${YS_ASK}"
prompt="$prompt

${body}"

MARK='"scenes"'
call_claude() {   # 인라인 재시도(쿼터 폴오버·일시 과부하) = 전역 out·rc 갱신
  local attempt inline_delay=15
  rc=1; out=""
  for attempt in $(seq 1 "$INLINE_TRIES"); do
    out="$(printf '%s' "$prompt" | METER_SRC="ys-make" METER_REF="${YS_ID:-}" METER_MODEL="$MODEL" METER_EFFORT="$YS_EFFORT" claude_meter 900 \
          --model "$MODEL" \
          --effort "$YS_EFFORT" \
          --disallowedTools "Read,Glob,Grep,Write,Edit,NotebookEdit,Bash,Task,WebFetch,WebSearch" \
          --max-turns 1 \
          2> "${OUTDIR}/stderr.log")"
    rc=$?
    if [ $rc -eq 0 ] && [ -n "${out// }" ] && { grep -qm1 "$MARK" <<<"$out" || grep -qm1 '^TRANSCRIPT_FAILED' <<<"$out"; }; then
      break
    fi
    if claude_failover "$out$(cat "${OUTDIR}/stderr.log" 2>/dev/null)"; then continue; fi   # 쿼터 한도 → 대체 계정(SSOT)
    if [ "$attempt" -lt "$INLINE_TRIES" ] && is_transient "$out$(cat "${OUTDIR}/stderr.log" 2>/dev/null)"; then
      echo "  ⏳ API 일시 과부하 추정(인라인 ${attempt}/${INLINE_TRIES}, rc=$rc) — ${inline_delay}s 후 재시도"
      sleep "$inline_delay"; inline_delay=$((inline_delay * 2)); continue
    fi
    break
  done
}

# 형식 이탈(보고서 칸 비움 등) = 사유를 붙여 1회만 다시 쓰게 한다(260928 실측 = 같은 영상·같은 지침에서 확률적 이탈 1/2).
for fmt in 1 2; do
  call_claude
  if grep -qm1 '^TRANSCRIPT_FAILED' <<<"$out"; then   # 모델의 정직한 실패 선언 = 그대로 표면화(날조 방지)
    printf '%s\n' "$out" | grep -m1 '^TRANSCRIPT_FAILED' | sed 's/^TRANSCRIPT_FAILED: *//' | sed 's/^/전사로 내용을 파악하지 못했어 — /' > "$OUTDIR/error.log"
    rm -f "${OUTDIR}/stderr.log"; exit 1
  fi
  if [ $rc -ne 0 ] || [ -z "${out// }" ] || ! grep -qm1 "$MARK" <<<"$out"; then
    echo "인사이트 정리(Claude)가 실패했어 — 잠시 후 다시 해줘. (rc=$rc)" > "$OUTDIR/error.log"
    { echo "---- stderr ----"; cat "${OUTDIR}/stderr.log" 2>/dev/null; echo "---- stdout(head) ----"; printf '%s\n' "$out" | head -n 10; } >&2
    rm -f "${OUTDIR}/stderr.log"; exit 1
  fi
  rm -f "${OUTDIR}/stderr.log"
  printf '%s' "$out" > /tmp/ys_raw.txt
  python3 .github/scripts/ys_plan.py parse /tmp/ys_raw.txt "$LEN" "$OUTDIR" 2> /tmp/ys_parse_err.txt && break
  why="$(head -c 160 /tmp/ys_parse_err.txt)"
  echo "::warning::인사이트 정리 형식 이탈(${fmt}/2) — ${why} · 앞머리: $(head -c 200 /tmp/ys_raw.txt | tr '\n' ' ')"
  if [ "$fmt" -ge 2 ]; then
    echo "인사이트 정리 결과 형식이 깨졌어 — 다시 해줘. (${why:0:120})" > "$OUTDIR/error.log"; exit 1
  fi
  prompt="$prompt

[형식 교정] 직전 출력이 형식 검사에 걸렸다: ${why}
위 「출력 = JSON 하나만」 규격대로 다시 낸다 — 보고서 전문은 반드시 report_md 문자열 안에(줄바꿈 = \\n) 넣고, JSON 밖에 글을 쓰지 않는다."
done
