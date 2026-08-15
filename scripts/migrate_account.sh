#!/usr/bin/env bash
# migrate_account.sh — 계정·저장소 이관 갈아끼우기 1발
#
# 왜 스크립트인가: 이관에서 갈아끼울 자리가 흩어져 있고(260815 실측 = 레포이름 52파일·도메인 18파일·
# 보관함 주소 4자리·알림 공개키 2자리) 한 자리만 빠뜨려도 그 기능만 조용히 죽는다.
#   · 레포이름 누락 → 그 API 하나만 옛 계정으로 발사(404) = 화면은 멀쩡, 그 버튼만 무동작
#   · 보관함 주소 누락 → 옛 결과물 전건 깨진 그림
#   · 알림 공개키를 한쪽만 바꿈 → 화면과 백그라운드 일꾼의 짝이 깨져 폰 알림 통째 사망
# → 손 치환 금지. 이 스크립트가 전수 치환하고 잔여 0을 사후 대조한다.
#
# 사용:
#   bash scripts/migrate_account.sh                 # 대화형(값을 물어본다)
#   bash scripts/migrate_account.sh --dry-run       # 바꿀 자리만 세어보고 실제로는 안 건드림
#
# 안전:
#   · 스냅샷·산출물 폴더는 대상 밖(_versions·docs·cards·published·node_modules·.git)
#     = 그때 있었던 일의 기록이라 갈아끼우면 역사가 거짓이 된다.
#   · CLAUDE.md·AGENTS.md 도 대상 밖(사고 기록에 옛 이름이 그대로 남아야 다음 세션이 추적한다).
#   · 치환 후 잔여 개수를 다시 세서 0이 아니면 rc≠0 으로 멈춘다(성공을 실패로/실패를 성공으로 오판 금지).
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1

DRY=0
[ "${1:-}" = "--dry-run" ] && DRY=1

# ── 옛 값(현행 실측 · 260815) ─────────────────────────────────────────────
OLD_REPO='muteno/nomute-editor'
OLD_OWNER='muteno'
OLD_R2HOST='pub-83f8cf3892ae44c38bebf1805c954508.r2.dev'
OLD_PAGES='nomute-editor.pages.dev'
OLD_DOMAIN='apps.nomute.kr'
OLD_VAPID='BORNTh3cNd05vsxi2fZ-BykxM0NwKGTvIETz81g757RVFL6cDu29aAv5I7uit0WbGOmiZ4hlyMOEvb8B2HptU-I'

# 대상 밖(스냅샷·기록·의존물)
# ⚠ `:!_versions/**` 형태는 쓰지 마라 — 밑줄로 시작하는 이름을 pathspec magic 으로 오해해
#   `fatal: Unimplemented pathspec magic '_'` 로 목록이 통째로 0이 된다(260815 실측 = 첫 판이
#   전 항목 0건을 내고 「깨끗함」처럼 보였다 = 가장 조용한 실패). 반드시 `:(exclude)` 표기.
EXCLUDES=(':(exclude)_versions/**' ':(exclude)docs/**' ':(exclude)cards/**'
          ':(exclude)published/**' ':(exclude)node_modules/**'
          ':(exclude)CLAUDE.md' ':(exclude)AGENTS.md'
          ':(exclude)scripts/migrate_account.sh' ':(exclude)*.jsonl')

say() { printf '%s\n' "$*"; }
hr()  { printf '%s\n' '────────────────────────────────────────'; }

# 대상 파일 목록(추적 파일만 · 이진 제외)
files() { git ls-files -z -- . "${EXCLUDES[@]}" 2>/dev/null; }

count_of() {   # $1 = 찾을 문자열 → 그 문자열이 든 파일 수와 총 건수
  local n f=0 t=0
  while IFS= read -r -d '' p; do
    [ -f "$p" ] || continue
    grep -Iq . "$p" 2>/dev/null || continue          # 이진 파일 배제
    n=$(grep -Fo -- "$1" "$p" 2>/dev/null | wc -l | tr -d ' ')
    [ "${n:-0}" -gt 0 ] && { f=$((f+1)); t=$((t+n)); }
  done < <(files)
  printf '%s %s' "$f" "$t"
}

subst() {      # $1 = 옛값 · $2 = 새값
  local changed=0
  while IFS= read -r -d '' p; do
    [ -f "$p" ] || continue
    grep -Iq . "$p" 2>/dev/null || continue
    grep -Fq -- "$1" "$p" 2>/dev/null || continue
    python3 - "$p" "$1" "$2" <<'PY' || return 1
import io,sys
p,old,new = sys.argv[1],sys.argv[2],sys.argv[3]
s = io.open(p,encoding='utf-8',errors='surrogateescape').read()
io.open(p,'w',encoding='utf-8',errors='surrogateescape').write(s.replace(old,new))
PY
    changed=$((changed+1))
  done < <(files)
  printf '%s' "$changed"
}

hr; say '📦 계정·저장소 이관 갈아끼우기'; hr
say '지금 박혀 있는 옛 값과 그 개수부터 센다.'; say ''
for pair in "레포이름|$OLD_REPO" "보관함주소|$OLD_R2HOST" "화면주소|$OLD_PAGES" "도메인|$OLD_DOMAIN" "알림공개키|$OLD_VAPID"; do
  lbl=${pair%%|*}; val=${pair#*|}
  read -r nf nt < <(count_of "$val")
  printf '  %-10s %3s개 파일 · %4s건\n' "$lbl" "$nf" "$nt"
done
say ''

if [ "$DRY" = "1" ]; then say '(--dry-run 이라 여기까지. 실제 치환은 인자 없이 다시 실행)'; exit 0; fi

hr; say '새 값을 넣어라. 비워두고 엔터 = 그 항목은 안 바꾼다.'; hr
read -rp "  새 계정/저장소 (예: newacct/nomute-editor) : " NEW_REPO
read -rp "  새 보관함 공개 주소 (pub-xxxx.r2.dev)      : " NEW_R2HOST
read -rp "  새 화면 주소 (xxxx.pages.dev)              : " NEW_PAGES
read -rp "  새 도메인 (안 바꾸면 엔터)                 : " NEW_DOMAIN
read -rp "  새 알림 서명 공개키 (안 바꾸면 엔터)       : " NEW_VAPID
say ''

# 새 보관함 주소는 호스트만 받는다(앞에 https:// 를 붙여 오면 잘라낸다 = 이중 접두 사고 차단)
NEW_R2HOST=${NEW_R2HOST#https://}; NEW_R2HOST=${NEW_R2HOST#http://}; NEW_R2HOST=${NEW_R2HOST%/}
NEW_PAGES=${NEW_PAGES#https://};   NEW_PAGES=${NEW_PAGES#http://};   NEW_PAGES=${NEW_PAGES%/}
NEW_DOMAIN=${NEW_DOMAIN#https://}; NEW_DOMAIN=${NEW_DOMAIN#http://}; NEW_DOMAIN=${NEW_DOMAIN%/}

rc=0
do_one() {     # $1 = 라벨 · $2 = 옛값 · $3 = 새값
  local lbl=$1 old=$2 new=$3
  [ -z "$new" ] && { printf '  %-10s 건너뜀\n' "$lbl"; return 0; }
  [ "$old" = "$new" ] && { printf '  %-10s 값 같음 · 건너뜀\n' "$lbl"; return 0; }
  local n; n=$(subst "$old" "$new")
  local rf rt; read -r rf rt < <(count_of "$old")
  if [ "${rt:-0}" -ne 0 ]; then
    printf '  %-10s ❌ %s개 파일 고쳤는데 잔여 %s건 (대상 밖이거나 치환 실패)\n' "$lbl" "$n" "$rt"; rc=1
  else
    printf '  %-10s ✅ %s개 파일 · 잔여 0\n' "$lbl" "$n"
  fi
}

# ⚠ 보관함 주소는 과거 결과물 기록 파일에도 박혀 있다(260815 실측 = 693파일·1012건 =
#   viewer/sb_out·track_out·gen_out 등 지난 제작물의 그림·영상 주소). 주소만 바꾸고 옛 보관함
#   내용을 새 보관함에 **같은 경로로** 안 옮겨두면 그 순간 과거 결과물이 전건 깨진 그림이 된다.
#   → 복사 완료를 사람이 확정하기 전에는 이 항목을 안 건드린다(되는 척 금지).
if [ -n "$NEW_R2HOST" ]; then
  say ''
  say '⚠ 보관함 주소는 지난 제작물 기록 693개 파일에도 박혀 있다.'
  say '  옛 보관함 내용을 새 보관함에 같은 경로로 이미 복사해 뒀나?'
  say '  (아직이면 n — 주소는 그대로 두고 나머지만 바꾼다)'
  read -rp '  복사 끝났음? [y/N] : ' R2READY
  case "$R2READY" in
    y|Y) : ;;
    *) say '  → 보관함 주소는 건너뛴다. 복사 끝난 뒤 이 스크립트를 다시 돌려라.'; NEW_R2HOST='' ;;
  esac
  say ''
fi

hr; say '갈아끼우는 중'; hr
do_one '레포이름'   "$OLD_REPO"    "$NEW_REPO"
# 계정 단독(설치 파일의 clone 주소 = https://muteno@github.com/...)은 레포이름 치환 뒤 남은 자리만
if [ -n "$NEW_REPO" ]; then
  NEW_OWNER=${NEW_REPO%%/*}
  do_one '계정단독' "https://${OLD_OWNER}@github.com" "https://${NEW_OWNER}@github.com"
fi
do_one '보관함주소' "$OLD_R2HOST"  "$NEW_R2HOST"
do_one '화면주소'   "$OLD_PAGES"   "$NEW_PAGES"
do_one '도메인'     "$OLD_DOMAIN"  "$NEW_DOMAIN"
do_one '알림공개키' "$OLD_VAPID"   "$NEW_VAPID"
say ''

hr; say '검문 돌린다'; hr
if python3 shared/check_refs.py; then say '✅ 검문 통과'; else say '❌ 검문 실패 — 위 사유를 고치고 다시'; rc=1; fi

say ''
hr
if [ "$rc" -eq 0 ]; then
  say '✅ 갈아끼우기 끝. 아직 커밋은 안 했다.'
  say '   확인 = git diff --stat'
  say '   커밋 = git add -A && git commit -m "계정 이관: 배선 갈아끼우기"'
else
  say '❌ 남은 자리가 있다. 커밋하지 마라.'
  say '   확인 = bash scripts/migrate_account.sh --dry-run'
fi
hr
exit "$rc"
