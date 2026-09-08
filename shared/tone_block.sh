# tone_block.sh — 한국어 결(AI 번역투 소거) 공용 블록 (source 전용 · 260823 신설 · 260908 정본 추출로 개편)
#
# 왜(운영자 260823 «ai요약 sns 요약에도 아까 그 말투를 녹여줄래»): 뉴스 축은 에디터 지침 주입(inject_guidelines)으로
#   규칙이 닿는데 SNS 요약 4레인(커뮤 브리프 sns_brief · 한줄 요약 sns_sum · 채널 브리프 chan_brief/fb_brief)은 지침을
#   안 물고 각자 인라인 프롬프트라 그 규칙이 안 닿는다. 문장을 벌로 복사하면 서로 낡으므로 한 벌을 넷이 참조한다.
# 260908 개편(감사 실측 = 세 사본[01·이 파일·polish-korean]이 이미 드리프트): 규칙 본문을 여기 두지 않고
#   **정본 shared/ko_tone_rules.md 의 [공용 문장축] 구간(KO-TONE:COMMON 마커 사이)을 source 시점에 추출**한다.
#   ⓐ TONE_BLOCK      = 공용 문장축 전체(리듬 줄 포함)
#   ⓑ TONE_BLOCK_SENT = 리듬 줄(`- [리듬]` 접두) 제외본 — 한 문장 레인(sns_sum 45자)·짧은 산출에 쓴다.
#   ⓒ TONE_VER        = TONE_BLOCK 의 sha256 8자 · export — 각 레인 캐시 키(PVER)에 결합해 규칙 개정 = 자동 재생성
#      (구판은 PVER+데이터만 해시라 규칙을 고쳐도 화면이 안 바뀌었다 · 260908 감사 R4).
# 계약: **문장의 결만** — 각 레인의 고유 말투 지시(친근 소식통 톤·인사 문법·이모지·형식·팬픽 변주)가 항상 우선이고
#   이 블록은 못 이긴다. 기사체 상한선(한자어 보존)은 뉴스 축 전용이라 여기 없다(정본의 NEWS-CAP 구간은 추출 대상 밖).
# 게이트 = check_refs.check_ko_tone_ssot(정본 실존 · 소비자 source · 규칙 본문 사본 0).

_TB_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
_TB_FILE="$_TB_ROOT/shared/ko_tone_rules.md"
if [ -f "$_TB_FILE" ]; then
  TONE_BLOCK="$(awk '/KO-TONE:COMMON-START/{f=1;next} /KO-TONE:COMMON-END/{f=0} f' "$_TB_FILE")"
else
  echo "::warning::shared/ko_tone_rules.md 없음 — TONE_BLOCK 비어 있음(체크아웃 목록에 shared 확인)" >&2
  TONE_BLOCK=''
fi
TONE_BLOCK_SENT="$(printf '%s\n' "$TONE_BLOCK" | grep -v '^- \[리듬\]')"
TONE_VER="$(printf '%s' "$TONE_BLOCK" | sha256sum | cut -c1-8)"
export TONE_VER
