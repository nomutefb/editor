#!/usr/bin/env bash
# 이야기 입력(env STORY) → claude -p(헤드리스, 감독 모델 스위치 · storyboard-v1 스킬 런타임 Read)
#   → 텍스트 콘티 md → viewer/sb_out/<id>/board.md. 인증 = CLAUDE_CODE_OAUTH_TOKEN(구독 OAuth·무료, kmake와 동일).
# 감독 모델 = env DIRECTOR(opus|fable) → --model 매핑(2축 분리 설계 · apps/storyboard/260714_설계확정_2축분리_v1.md).
# 워크플로가 커밋·push(kmake와 동일 가드 패턴). 실패 = error.log + exit 1(잡 빨갛게).
set -uo pipefail
ROOT="$(git rev-parse --show-toplevel)"; cd "$ROOT"
PROMPT_FILE="prompts/sb-make.md"
source "$ROOT/shared/model_env.sh"   # 모델 단일 원천(PIPE_MODEL — 감독 미지정 폴백)
case "${DIRECTOR:-}" in
  opus) MODEL="claude-opus-5" ;;    # 감독 = 오퍼스 5(정적·감성·가성비)
  fable) MODEL="claude-fable-5" ;;    # 감독 = 페이블 5(역동·서사·재생성 절약)
  *) MODEL="$PIPE_MODEL" ;;
esac
source "$ROOT/shared/claude_transient.sh"  # is_quota()/claude_failover()/is_transient() SSOT — 쿼터 한도 시 4계정 자동 로테이션·일시 과부하 재시도(kmake와 통일·§📰)
source "$ROOT/shared/claude_meter.sh"   # claude_meter() SSOT — claude -p 토큰 사용량 계측(metrics shard)
INLINE_TRIES="${INLINE_TRIES:-4}"   # 쿼터 폴오버(서브1→서브2→서브3)·일시 과부하 인라인 재시도(kmake와 동일)
ID="${1:?usage: sbmake.sh <id> (STORY=env)}"
OUTDIR="viewer/sb_out/${ID}"; mkdir -p "$OUTDIR"

[ -n "${STORY:-}" ] || { echo "::error::STORY(이야기 입력) 비어있음"; echo "exit: 빈 입력" > "$OUTDIR/error.log"; exit 1; }

# ⚠ **무엇을 소재로 짰는지 산출에 박제한다**(운영자 260813 「소스를 어떤거를 썼는지 검증이 안됨」).
#   구판은 이야기 입력이 발사 인자로만 존재해서, 콘티가 나온 뒤엔 **무슨 소재로 짠 건지 확인할
#   길이 아예 없었다**(발사 화면을 닫으면 끝). 콘티가 소재를 배반해도 대조할 원본이 없다는 뜻이라
#   「제대로 돌았나」를 사람이 기억으로 판정하게 된다 = 이 레포가 반복해 데인 관측 소실.
printf '%s' "${STORY}" > "$OUTDIR/source.md"
echo "소재 박제 ✓ $OUTDIR/source.md ($(wc -c < "$OUTDIR/source.md") bytes)"

# 📷 참조 사진(운영자 260817 「콘티에 참조할 사진도 넣을 수 있게」) — 서버(api/sb.js)가 이야기 말미에
#   [참조 사진: 주소…] 표식으로 태워 보낸다(발사 입력 10칸 만석 = 칸 신설 불가 · [설정:] 마커 관례).
#   콘티 폴더에 photo_N.jpg 로 내려받아 ⓐ 감독이 Read 로 실물을 보고 ⓑ 인물 시트(k_refgen)가 얼굴
#   정본으로 싣는다. ⚠ 번호 = 표식 안 순번 그대로(실패 장은 건너뛰되 번호를 안 당긴다 — 당기면
#   감독의 (사진 N) 라벨이 다른 사진을 가리킨다). 커밋 전 정리 = 워크플로 몫(R2 가 정본) · fail-soft.
PHOTO_LINE="$(printf '%s' "${STORY}" | grep -o '\[참조 사진:[^]]*\]' | head -1 || true)"
PHOTO_GOT=0
if [ -n "$PHOTO_LINE" ]; then
  PHOTO_IDX=0
  for u in $(printf '%s' "$PHOTO_LINE" | sed 's/^\[참조 사진:[[:space:]]*//; s/\]$//'); do
    PHOTO_IDX=$((PHOTO_IDX+1)); [ "$PHOTO_IDX" -gt 3 ] && break
    case "$u" in
      https://*) ;;
      *) echo "::warning::참조 사진 ${PHOTO_IDX}번 주소 형식 아님(건너뜀)"; continue ;;
    esac
    if curl -fsS --max-time 30 "$u" -o "$OUTDIR/photo_${PHOTO_IDX}.jpg"; then
      PHOTO_GOT=$((PHOTO_GOT+1))
    else
      rm -f "$OUTDIR/photo_${PHOTO_IDX}.jpg"
      echo "::warning::참조 사진 ${PHOTO_IDX}번 내려받기 실패(그 장만 빼고 진행)"
    fi
  done
  echo "참조 사진 ${PHOTO_GOT}장 내려받음 → $OUTDIR/photo_*.jpg"
fi

# 지침 프리플라이트 — sb-make.md가 Read시키는 스킬 파일 실존 확인(리네임 시 무성 실패 → 명시 실패 · kmake 프리플라이트 패턴 계승)
for REF_PAT in '\.claude/skills/storyboard-v1/SKILL\.md' '\.claude/skills/master-sheet-v2/SKILL\.md'; do
  GUIDE_REF="$(grep -om1 "$REF_PAT" "$PROMPT_FILE" | head -1 || true)"
  if [ -z "$GUIDE_REF" ]; then
    echo "::error::sb-make.md에 스킬 참조 소실: $REF_PAT (경로 리네임이 패턴을 벗어남?)"
    echo "sb-make.md 참조 소실: $REF_PAT — 프리플라이트 패턴·참조 경로 동시 확인 필요" > "$OUTDIR/error.log"; exit 1
  fi
  REF_FILE="${GUIDE_REF//\\/}"
  if [ ! -f "$REF_FILE" ]; then
    echo "::error::참조 파일 부재: $REF_FILE (sb-make.md 참조 경로 확인 — 스킬 이식 누락?)"
    echo "참조 파일 부재: $REF_FILE — .claude/skills 스킬 5종 이식 상태 확인 필요" > "$OUTDIR/error.log"; exit 1
  fi
done

# 고정부(프롬프트) → 가변부(이야기). stdin 전달 = ARG_MAX 회피(kmake와 동일).
prompt="$(cat "$PROMPT_FILE")
${STORY}"

# 변형 모드(운영자 260714 5차): BASE = 이전 콘티 경로(api/sb.js 화이트리스트 통과분) → 전문 동봉(클로드·GPT 양 레인 공통 = 인라인 통일)
if [ -n "${BASE:-}" ] && [ -f "viewer/${BASE}" ]; then
  prompt="${prompt}

[변형 모드 — 아래 이전 콘티가 기준이다. 이야기 입력의 변경 지시만 반영하고 나머지(캐릭터 락·구조·유지 컷)는 보존하라. 전체 재창작 금지 · 바뀐 컷에 📌 표기]
=== 이전 콘티(기준) ===
$(cat "viewer/${BASE}")"
elif [ -n "${BASE:-}" ]; then
  echo "::warning::변형 기준 콘티 부재(viewer/${BASE}) — 신규 설계로 진행"
fi

# 📷 참조 사진 열람 지시(위 내려받기 블록의 짝) — 파일이 실제로 있을 때만 붙인다(없는 파일을
#   열라는 지시 = 감독이 헛걸음하고, 있는데 지시가 없으면 감독이 실물을 영영 안 본다 = 양쪽 다 사고).
if [ "${PHOTO_GOT:-0}" -gt 0 ]; then
  prompt="${prompt}

[참조 사진 안내 — 운영자가 붙인 실물 사진이 ${OUTDIR}/photo_N.jpg 로 내려받아져 있다(N = 표식 순번). Read 도구가 있으면 각 사진을 실제로 열어 인물·물건 묘사를 실물 기준으로 쓰고, 🖼 레퍼런스 절 해당 인물 라벨에 (사진 N) 을 붙여라. Read 도구가 없는 레인은 열람만 생략하고 라벨 표기는 하라]"
fi

if [ "${DIRECTOR:-}" = "gpt" ]; then
  # ── GPT 감독 레인(운영자 260714 "지피티도 가능하게") — OpenAI API 직호출(구독 OAuth 없음 = API 키 종량 · 설계확정 §0-2) ──
  [ -n "${OPENAI_API_KEY:-}" ] || { echo "::error::OPENAI_API_KEY 시크릿 미등록 — GPT 감독 발사 불가"; echo "GPT 감독: OPENAI_API_KEY 시크릿 미등록 — 레포 Settings→Actions secrets에 등록 필요" > "$OUTDIR/error.log"; exit 1; }
  # GPT는 파일시스템 Read 불가 → 스킬 전문 인라인(프리플라이트가 실존 보장 · 합 ~17KB = 토큰 부담 미미)
  prompt="${prompt}

[GPT 레인 특례 — 파일 Read 불가: 아래 인라인 전문이 절차 1·2의 그 파일들이다. Read 시도 없이 이 본문을 정본으로 따르라]
=== .claude/skills/storyboard-v1/SKILL.md 전문 ===
$(cat .claude/skills/storyboard-v1/SKILL.md)
=== .claude/skills/master-sheet-v2/SKILL.md 전문 ===
$(cat .claude/skills/master-sheet-v2/SKILL.md)"
  out="$(printf '%s' "$prompt" | OPENAI_MODEL="${OPENAI_MODEL:-gpt-5.6-sol}" python3 .github/scripts/sb_gpt.py 2> "${OUTDIR}/stderr.log")"
  rc=$?
else
# 허용 도구 = Read/Glob/Grep(스킬 런타임 로드) + WebFetch/WebSearch(리서치).
# Write/Edit/Bash/Task 불허 = 헤드리스 무중단(kmake와 동일).
inline_delay=15
_to_tried=0   # 타임아웃(rc=124) 계정 강제전환 1회 제한(kmake 패턴 계승)
SB_MODEL_FB="${SB_MODEL_FB:-claude-opus-5}"; _mfb=0; _eff=high   # Fable 실패/전용토큰 소진 → Opus high 1회 폴백(운영자 260726 전면 high · 260722 · DIRECTOR=opus면 미발동)
for attempt in $(seq 1 "$INLINE_TRIES"); do
  out="$(printf '%s' "$prompt" | METER_SRC=sb METER_REF="$ID" METER_MODEL="$MODEL" METER_EFFORT="$_eff" claude_meter 900 \
        --model "$MODEL" \
        --effort "$_eff" \
        --allowedTools "Read,Glob,Grep,WebFetch,WebSearch" \
        --disallowedTools "Write,Edit,NotebookEdit,Bash,Task" \
        --max-turns 40 \
        2> "${OUTDIR}/stderr.log")"
  rc=$?
  if { [ $rc -eq 0 ] && [ -n "${out// }" ] && grep -qm1 '^#' <<<"$out"; } || grep -qm1 '^SBMAKE_FAILED' <<<"$out"; then
    break
  fi
  if [ $rc -eq 124 ] && [ "$_to_tried" = "0" ] && claude_failover_force; then _to_tried=1; continue; fi   # 900s 타임아웃 = 계정 강제 1회 전환(kmake 동일)
  if claude_failover "$out$(cat "${OUTDIR}/stderr.log" 2>/dev/null)"; then continue; fi   # 쿼터 한도 → 대체 계정 전환(SSOT)
  if [ "$attempt" -lt "$INLINE_TRIES" ] && is_transient "$out$(cat "${OUTDIR}/stderr.log" 2>/dev/null)"; then
    echo "  ⏳ API 일시 과부하 추정(인라인 ${attempt}/${INLINE_TRIES}, rc=$rc) — ${inline_delay}s 후 재시도"
    sleep "$inline_delay"; inline_delay=$((inline_delay * 2)); continue
  fi
  if [ "$_mfb" = 0 ] && [ "$MODEL" != "$SB_MODEL_FB" ] && [ "$attempt" -lt "$INLINE_TRIES" ]; then   # 쿼터·5xx 아닌 실패(Fable 형식이탈/거절/전용토큰 소진) → Opus max 1회 폴백(운영자 260722 · DIRECTOR=opus면 미발동)
    _mfb=1; MODEL="$SB_MODEL_FB"; _eff=high; echo "  ⏳ 모델 폴백 → ${MODEL} high (Fable 실패/소진 추정 · 1회 한정)"; continue
  fi
  break
done
fi   # ── 감독 분기 끝(gpt = OpenAI 직호출 / 클로드 = 구독 OAuth + 폴오버 SSOT) ──

# 실패 판정: 비정상 종료 / 빈 출력 / 실패 신호 / '#' 제목 부재 (kmake 동일 · 감독 무관 공통)
if [ $rc -ne 0 ] || [ -z "${out// }" ] || grep -qm1 '^SBMAKE_FAILED' <<<"$out" || ! grep -qm1 '^#' <<<"$out"; then
  {
    echo "exit_code: $rc"
    echo "---- stderr ----"; cat "${OUTDIR}/stderr.log" 2>/dev/null
    echo "---- stdout(head) ----"; printf '%s\n' "$out" | head -n 20
  } > "${OUTDIR}/error.log"
  echo "::error::스토리보드 생성 실패 (rc=$rc)"
  exit 1
fi

# 모델 사족 방어 — 첫 '#'(제목)부터 저장.
printf '%s\n' "$out" | sed -n '/^#/,$p' > "${OUTDIR}/board.md"
rm -f "${OUTDIR}/stderr.log"
echo "성공 → ${OUTDIR}/board.md ($(wc -c < "${OUTDIR}/board.md") bytes)"
