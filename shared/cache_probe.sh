#!/usr/bin/env bash
# cache_probe.sh — 카드 고정부 캐시 프로브(평의회 260812 권고4 · 「봉합 전 프로브 선행」 계약의 실행체).
#
# ▷ 왜: 카드 축 $의 62%가 캐시쓰기인데, 지침 고정부(~200KB)가 **같은 잡 안**에선 재사용되고(린트 콜
#   cache_read 107,545 실측) **잡이 다르면** 전량 재기록된다(60분 내 연속쌍 273/274 실측 · 원인 미확정).
#   갈림 지점(환경/프리픽스/TTL)을 실측해야 봉합이 가능하다 — 이 스크립트는 cardmake.sh 본콜과 **같은
#   프리픽스**(시스템 프롬프트 파일 = PROMPT_FILE+GBLOCK · 같은 도구 플래그 · 같은 모델 · 같은 effort)로
#   1단어짜리 콜을 쏘고 usage(cache_creation/cache_read)와 환경 지문을 로그에 그대로 찍는다.
# ▷ 판독(cache-probe.yml A잡 → B잡 순차 · 러너 분리):
#   · B잡 cache_read ≥ 10만  = 잡 간 재사용 성립 → 실운영 미재사용의 진범은 TTL/타이밍/계정 축
#   · B잡 cache_creation ≈ 전량 = 잡 간 프리픽스 갈림 → 두 잡의 sys_sha·claude 버전 지문을 대조해 갈린 축 지목
#   · B2(같은 잡 2번째 콜) = 잡 내 재사용 대조군(린트 실측의 재현 확인)
# ▷ 안전: workflow_dispatch 전용 수동 카나리아 · 커밋 0 · 산출물 0 · 콜당 출력 1단어(비용 = 캐시쓰기뿐
#   ≈ 콜당 $1.3 환산 · 총 3콜) · effort는 카드 본콜과 동일(CARD_EFFORT 기본 max — 프리픽스 등가 보장 우선).
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
LABEL="${1:-A}"

source shared/model_env.sh
source shared/inject_guidelines.sh
source shared/claude_meter.sh

MODEL="${PIPE_MODEL:-claude-opus-5}"
EFFORT="${CARD_EFFORT:-max}"          # 카드 본콜 기본과 동일(cardmake.sh:34) — effort가 프리픽스에 실리는 축이어도 등가 유지
PROMPT_FILE="prompts/card-make.md"
GBLOCK="$(guidelines_block card)"

SYSF="$(mktemp /tmp/card_sys.XXXXXX)"
trap 'rm -f "$SYSF"' EXIT
{ cat "$PROMPT_FILE"; printf '\n\n%s\n' "$GBLOCK"; } > "$SYSF"   # cardmake.sh CARD_SYS_PROMPT=1 조립과 바이트 동일

echo "[probe:${LABEL}] model=${MODEL} effort=${EFFORT} claude=$(claude --version 2>/dev/null | head -1)"
echo "[probe:${LABEL}] sys_sha=$(sha256sum "$SYSF" | cut -c1-16) sys_bytes=$(wc -c < "$SYSF") claude_md_sha=$(sha256sum CLAUDE.md | cut -c1-16) pwd=$(pwd)"

# 다이제스트를 잡·라벨마다 다르게 = 실운영(콜마다 다른 기사)과 같은 조건. 지시 = 정확히 한 단어(PONG)만.
printf '%s' "[캐시 프로브 ${LABEL}] 이것은 캐시 계측용 무해 콜이다. 위 지침과 무관하게 정확히 PONG 한 단어만 출력하라. 다이제스트: ${LABEL}-${GITHUB_RUN_ID:-local}" | \
  METER_SRC=cache-probe METER_REF="${LABEL}" METER_MODEL="$MODEL" METER_EFFORT="$EFFORT" claude_meter 600 \
    --model "$MODEL" --effort "$EFFORT" \
    --allowedTools "WebFetch,WebSearch" \
    --disallowedTools "Write,Edit,NotebookEdit,Bash,Task,Read,Glob,Grep" \
    --max-turns 1 \
    --append-system-prompt-file "$SYSF" --exclude-dynamic-system-prompt-sections >/dev/null || true
    # 도구 플래그 = cardmake.sh 본콜(:338)과 동일(도구 정의 = 프리픽스의 일부) · max-turns만 1(클라이언트 루프 제어 = 프리픽스 밖)

echo "[probe:${LABEL}] usage ↓ (cache_w=조성 · cache_r=재사용)"
cat metrics/usage/*.jsonl 2>/dev/null || echo "(shard 없음 — jq 부재/계측 폴백?)"
