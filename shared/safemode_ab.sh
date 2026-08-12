#!/usr/bin/env bash
# safemode_ab.sh — 지침문서(CLAUDE.md) 스킵 A/B 실측(운영자 260812 「지침 스킵 비교 실험 해봐 · 품질이 줄어들면
#   $30급이어도 안 하는 게 맞음」 · 평의회 260812 조건부④의 승격 관문).
#
# ▷ 무엇: 같은 기사(스템)의 큐레이션 다이제스트로 카드 본콜을 2발 쏜다 — A = 현행(지침문서 적재) · B = --safe-mode
#   (지침문서 미적재). 프롬프트·모델·effort·도구·시스템 고정부(카드 프롬프트+지침 = SYS 파일) 전부 동일, 차이는
#   스킵 플래그 하나 = 순수 대조. 근거 = 캐시 프로브 run 31550098261(콜마다 ~11.6만tok 재기록 = CLAUDE.md+동적부).
# ▷ 안전: 산출은 /tmp에만(cards/ 무접촉 · 커밋 0 · 라이브 덱 무접촉) · workflow_dispatch 전용 · 비용 ≈ 카드 2세트.
# ▷ 판정 재료(로그로 전부): ① card_gate lint(물리 규격) ② card_gate coverage(알맹이 회수) ③ 카드 수 ④ 덱 전문
#   ⑤ usage(cache_w 낙폭 = 스킵의 비용 효과). 채택 판정은 정독 대조 몫 — 품질 하락이면 기각이 운영자 계약.
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
STEM="${1:?usage: safemode_ab.sh <stem>}"
q="queue/${STEM}.md"
[ -f "$q" ] || { echo "::error::큐 파일 없음: $q"; exit 1; }

source shared/model_env.sh
source shared/inject_guidelines.sh
source shared/claude_meter.sh

MODEL="${PIPE_MODEL:-claude-opus-5}"
EFFORT="${CARD_EFFORT:-max}"          # 카드 본콜 기본과 동일(운영자 260812 「카드 = 최대 노력도 맞음」 확정)
PROMPT_FILE="prompts/card-make.md"
GBLOCK="$(guidelines_block card)"
SYSF="$(mktemp /tmp/card_sys.XXXXXX)"
trap 'rm -f "$SYSF"' EXIT
{ cat "$PROMPT_FILE"; printf '\n\n%s\n' "$GBLOCK"; } > "$SYSF"   # cardmake.sh CARD_SYS_PROMPT=1 조립과 바이트 동일

# 다이제스트 = cardmake.sh 본콜 fp(SYS 모드)와 동일 문면(disp_note는 기사별 선택 요소라 양팔 공통 생략 = 공정 대조)
fp="[큐레이션 다이제스트 — 이 기사로 카드뉴스 MD를 만든다]
$(cat "$q")"

echo "대상 = $STEM · 다이제스트 $(wc -c < "$q")B · 고정부 $(wc -c < "$SYSF")B · 모델 $MODEL · effort $EFFORT"

run_arm() {
  local label="$1" mode="${2:-off}"
  local extra=()
  if [ "$mode" = "safe" ]; then extra=(--safe-mode); fi
  echo "══ [$label] 발사(safe=$mode)"
  local out rc
  out="$(printf '%s' "$fp" | METER_SRC=ab-card METER_REF="${STEM}-${label}" METER_MODEL="$MODEL" METER_EFFORT="$EFFORT" claude_meter 1500 \
        --model "$MODEL" --effort "$EFFORT" \
        --allowedTools "WebFetch,WebSearch" \
        --disallowedTools "Write,Edit,NotebookEdit,Bash,Task,Read,Glob,Grep" \
        --max-turns 40 \
        --append-system-prompt-file "$SYSF" --exclude-dynamic-system-prompt-sections \
        "${extra[@]}" 2> "/tmp/ab_${label}.err")"
  rc=$?
  printf '%s\n' "$out" | sed -n '/^#/,$p' > "/tmp/ab_${label}.md"
  local n lint lrc cov
  n="$(grep -c '^### \[카드' "/tmp/ab_${label}.md" || true)"
  lint="$(python3 .github/scripts/card_gate.py lint "/tmp/ab_${label}.md" 2>&1)"; lrc=$?
  cov="$(python3 .github/scripts/card_gate.py coverage "$q" "/tmp/ab_${label}.md" 2>&1)" || true
  echo "── [$label] rc=$rc · 카드수=$n · lint_rc=$lrc"
  echo "── [$label] lint ↓";     printf '%s\n' "$lint" | sed 's/^/   /'
  echo "── [$label] coverage ↓"; printf '%s\n' "$cov"  | sed 's/^/   /'
  echo "── [$label] stderr(head) ↓"; head -3 "/tmp/ab_${label}.err" 2>/dev/null | sed 's/^/   /'
  echo "── [$label] 덱 전문 ↓";  sed 's/^/   /' "/tmp/ab_${label}.md"
}

run_arm "A_current" off
run_arm "B_skip" safe

echo "══ usage(비용 축 — B의 cache_w 낙폭 = 스킵 효과) ↓"
cat metrics/usage/*.jsonl 2>/dev/null | grep 'ab-card' || echo "(계측 없음)"
