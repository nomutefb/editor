#!/usr/bin/env bash
# summary_polish.sh — 한국어 윤문(AI 티 제거) 후처리: 요약 산출물의 문체만 별도 1콜로 다듬는다 (ask.sh·analyze.sh 공용 SSOT · 260823)
#
# 왜(운영자 260823): 「이거를 그런식으로 특정 요약하는 기능에 적용해줄래? 단, 프롬프트에는 영향 안주도록.
#     만약 1개 모델이 문구 + 프롬프트까지 한다면, 기능 분리해야해」 — 요약 본선 콜은 내용을, 이 콜은 결만.
#     규칙 원천 = im-not-ai 분류 체계 v2.0(github.com/epoko77-ai/im-not-ai · MIT) 중 **문장 축만** 개작 —
#     이모지·볼드·대시·불릿을 지우는 구조·장식 축(C·J 계열)은 우리 카드의 구조 문법 그 자체라 제외(보존 계약으로 반전).
# 기능 분리 계약: ① 요약 프롬프트(prompts/news-analysis.md) 무접촉 ② 윤문 규칙의 거처 = shared/ko_tone_rules.md 정본(polish-korean.md 는 보존 계약·출력 형식만)
#     ③ 별도 1콜(무도구·safe-mode) ④ 모델·노력도 독립 레버(SUMMARY_POLISH_MODEL/EFFORT · 기본 = 호출측 MODEL + high
#     = 정형 변환 선례 260722 「max 헛사고 회피」) — 나중에 「요약은 A모델·윤문은 B모델」 조합도 env 두 줄.
# 순서 = 요약 → 윤문(이것) → 수선(summary_repair) — 윤문이 분량을 깎아도 뒤의 분량 가드가 실측·보강하는 안전망 순서.
# 260908(운영자 «윤문체는 조건부가 아니라 off로 — 기사체랑 안 맞아 애매») : **기본 OFF 확정 · 조건부(auto) 없음**.
#     규칙 본문은 이 파일·polish-korean.md 에 없다 — 정본 shared/ko_tone_rules.md 의 두 구간(공용 문장축·기사체 상한선 — 대상이 요약 파일이라 카드 전용 윤문 추가축은 제외)을
#     호출 시점에 추출해 붙인다(사본 0 · check_ko_tone_ssot). 검증 6축 = 종전 5축 + ⓕ 격 하락 사전 대조(한자어→고유어 쌍이
#     원문에서 줄고 후보에서 늘면 기각 — 260823 실호출 8쌍이 프롬프트 금지문에만 기대던 것을 기계로 닫음).
# 게이트: SUMMARY_POLISH **기본 OFF**('1'로 켬) — 260823 2차(운영자 «좋다고 하는 부분만 가져와서 녹이자» = 규칙을
#     지침 [한국어 결 — AI 번역투 소거]에 편입해 별도 콜 없이 초고부터 적용 · 콜당 70초·출력 5.7천 토큰 절약).
#     이 콜은 예비 레버로 잔존(지침 편입만으로 부족하면 SUMMARY_POLISH=1 한 줄로 재가동 · 검증 5축 그대로).
#     구 계약(1차 «적용해줄래» = 기본 ON)은 이 개정으로 대체. 전면 fail-soft =
#     콜 실패·검증 실패 = 원본 유지(다이제스트 유실 0) · 재시도·폴오버 없음(1콜 상한 · summary_repair 계약 동문).
# 검증(어느 하나라도 어기면 원본 유지 — 윤문은 좋아야 채택이 아니라 **안전해야 채택**):
#     ⓐ frontmatter 바이트 동일 ⓑ 숫자 나열 다중집합 동일(수치 날조·소실 0) ⓒ 원문 따옴표 인용 전건 보존
#     ⓓ 구조 계수 동일(#헤더 줄 수 · 코드펜스 수) ⓔ 본문 분량 85~110%(하한 미달 = 수선 몫이 아니라 윤문 과절삭 = 기각) ⓕ 격 하락 사전 대조(260908)
# 사용: source 후 summary_polish <queue파일> <METER_SRC 라벨>   (MODEL·claude_meter 는 호출측 환경 상속)

summary_polish() {
  local file="$1" src="${2:-polish}"
  [ "${SUMMARY_POLISH:-0}" = "1" ] || return 0
  [ -f "$file" ] || return 0
  [ -f "prompts/polish-korean.md" ] || { echo "  ✒ 윤문: 규칙 파일 없음(prompts/polish-korean.md) — 스킵"; return 0; }
  local pmodel peff pprompt cand rc tmp why
  pmodel="${SUMMARY_POLISH_MODEL:-$MODEL}"
  peff="${SUMMARY_POLISH_EFFORT:-high}"
  # 규칙 정본 결합(260908) — [공용 문장축]+[기사체 상한선] 두 구간만(요약 프로필 동문 · 윤문 추가축은 카드 전용 = 상한선과 충돌 · 사람용 설명·미채택 절 제외)
  local rules_f="shared/ko_tone_rules.md" rules_txt
  rules_txt="$(awk '/KO-TONE:(COMMON|NEWS-CAP)-START/{f=1;next} /KO-TONE:(COMMON|NEWS-CAP)-END/{f=0} f' "$rules_f" 2>/dev/null)"
  [ -n "${rules_txt//[[:space:]]/}" ] || { echo "  ✒ 윤문: 규칙 정본 없음(shared/ko_tone_rules.md) — 스킵"; return 0; }
  pprompt="$(cat prompts/polish-korean.md)

## 다듬는 것(규칙 정본 = shared/ko_tone_rules.md · 아래 목록이 지목한 무늬만 고친다)
${rules_txt}

[요약 카드 파일 전문]
$(cat "$file")"
  cand="$(printf '%s' "$pprompt" | METER_SRC="$src" METER_REF="$(basename "$file" .md)" METER_MODEL="$pmodel" METER_EFFORT="$peff" claude_meter "${POLISH_TIMEOUT:-480}" \
        --model "$pmodel" \
        --effort "$peff" \
        --safe-mode \
        --disallowedTools "Write,Edit,NotebookEdit,Bash,Task,WebFetch,WebSearch,Read,Glob,Grep" \
        --max-turns 1 \
        2>/dev/null)"
  rc=$?
  if [ $rc -ne 0 ] || [ -z "${cand//[[:space:]]/}" ]; then
    echo "  ✒ 윤문 콜 실패(rc=$rc) — 원본 유지(fail-soft)"; return 0
  fi
  tmp="$(mktemp)"; printf '%s\n' "$cand" > "$tmp"
  # 검증 5축 — 통과 시에만 교체. python 이 기각 사유를 말하고 rc≠0 을 낸다.
  why="$(python3 - "$file" "$tmp" <<'PY'
import re, sys
orig = open(sys.argv[1], encoding='utf-8', errors='replace').read()
cand = open(sys.argv[2], encoding='utf-8', errors='replace').read().strip() + '\n'
# 모델이 전체를 코드펜스로 감쌌으면 벗긴다(랩퍼 방어 · strip_wrap_fence 축의 국소판)
lines = cand.split('\n')
if lines and lines[0].startswith('```'):
    if lines[-1].strip() == '': lines.pop()
    if lines and lines[-1].strip().startswith('```'): lines = lines[1:-1]
    else: lines = lines[1:]
    cand = '\n'.join(lines).strip() + '\n'
def fm(t):
    m = re.match(r'^---\n.*?\n---\n', t, re.S)
    return m.group(0) if m else None
def digits(t): return sorted(re.findall(r'\d+', t))
def quotes(t): return re.findall(r'[“"«][^”"»\n]{2,}[”"»]', t)
def fences(t): return t.count('```')
def hlines(t): return sum(1 for l in t.split('\n') if l.startswith('#'))
if not cand.strip(): print('빈 출력'); sys.exit(1)
fo, fc = fm(orig), fm(cand)
if fo is None or fc != fo: print('frontmatter 불일치'); sys.exit(1)
if digits(orig) != digits(cand): print('숫자 집합 변경'); sys.exit(1)
# 다중집합 대조 = 존재만 보면 같은 인용이 두 번 실린 카드에서 한 번 지워져도 통과한다(260823 킬테스트 실측 구멍)
if sorted(quotes(orig)) != sorted(quotes(cand)): print('인용 변경(횟수 포함)'); sys.exit(1)
if fences(orig) != fences(cand) or hlines(orig) != hlines(cand): print('구조 계수 변경'); sys.exit(1)
bo, bc = len(orig) - len(fo), len(cand) - len(fc)
if not (0.85 * bo <= bc <= 1.10 * bo): print(f'분량 이탈({bc}/{bo})'); sys.exit(1)
# ⓕ 격 하락 사전 대조(260908) — 한자어 기사 어휘가 줄고 그 고유어가 늘면 기사체 격 하락 = 기각(260823 실호출 8쌍 + 확장)
#   고유어 쪽 키는 흔한 어간('같이'·'만들어'·'보냈')을 안 물도록 어형을 좁힌다(260908 리뷰 — 부분열 오기각).
_PAIRS = [('삭제', '지울'), ('삭제', '지웠'), ('담당', '맡은'), ('담당', '맡았'), ('동일', '같은'), ('동일', '같다'), ('유사', '닮았'),
          ('장기간', '오랫동안'), ('발견', '나오지'), ('지원', '돕는'), ('지원', '돕기'), ('포함', '들어간'), ('포함', '들어 있'),
          ('확인', '알아본'), ('발생', '벌어졌'), ('사망', '숨졌'), ('부상', '다쳤'), ('체포', '붙잡'), ('구속', '가뒀'),
          ('제출', '냈다'), ('요청', '부탁'), ('검토', '살펴')]
_drop = [f'{a}→{b}' for a, b in _PAIRS if orig.count(a) > cand.count(a) and cand.count(b) > orig.count(b)]
if _drop: print('격 하락(' + ' · '.join(_drop[:4]) + ')'); sys.exit(1)
open(sys.argv[2], 'w', encoding='utf-8').write(cand)
print('ok')
PY
)" || { echo "  ✒ 윤문 기각(${why}) — 원본 유지"; rm -f "$tmp"; return 0; }
  cp "$tmp" "$file"; rm -f "$tmp"
  echo "  ✒ 윤문 적용(${pmodel} · ${peff}) — 검증 6축 통과"
  return 0
}
