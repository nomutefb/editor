#!/usr/bin/env bash
# homepage_migrate.sh — 노뮤트 홈(nomute.kr) 저장소를 새 계정으로 옮기는 1발(운영자 맥에서 실행)
#
# 왜 별도 스크립트인가: `scripts/migrate_account.sh` 는 이 저장소(에디터) 전용 옛 값이 코드에
#   박혀 있어(OLD_REPO=muteno/nomute-editor 등) 홈 저장소에는 그대로 못 쓴다. 반대로 복제 자체는
#   `scripts/clone_to_new_account.sh` 가 이미 정본이라 여기서 다시 짜지 않고 그대로 위임한다(사본 0).
#
# 무엇을 하나:
#   ① 옛/새 저장소 접근 확인  ② 통째 복제(정본 위임)  ③ 새 저장소 안에 남은 옛 값 전수 스캔
#   ④ 계정·저장소 이름만 선택 치환  ⑤ 사람이 화면에서 해야 하는 것(배포·외부 시계) 체크리스트
#
# 무엇을 안 하나(일부러):
#   · 주소류(배포 주소·보관함 주소) 자동 치환 안 한다. 홈 저장소의 어느 주소가 살아 있어야 하는지는
#     사람이 봐야 하고, 옛 보관함 복사가 끝나기 전에 주소를 갈면 지난 결과물이 전건 깨진 그림이 된다
#     (260816 에디터 이관 실측 = 순서가 계약이었다). 스캔해서 자리만 보여주고 판단은 사람이 한다.
#
# 사용:
#   bash scripts/homepage_migrate.sh
#   bash scripts/homepage_migrate.sh muteno/nomute_homepage nomutefb/homepage
set -uo pipefail

OLD=${1:-}
NEW=${2:-}
HERE="$(cd "$(dirname "$0")" && pwd)"

hr()  { printf '%s\n' '────────────────────────────────────────'; }
say() { printf '%s\n' "$*"; }

hr; say '🏠 홈 저장소 계정 이관'; hr
[ -z "$OLD" ] && read -rp '  옛 저장소 (주인/이름) [muteno/nomute_homepage] : ' OLD
[ -z "$NEW" ] && read -rp '  새 저장소 (주인/이름) [nomutefb/homepage]      : ' NEW
OLD=${OLD:-muteno/nomute_homepage}
NEW=${NEW:-nomutefb/homepage}
case "$OLD" in */*) : ;; *) say '❌ 옛 저장소를 주인/이름 형태로 넣어라'; exit 1 ;; esac
case "$NEW" in */*) : ;; *) say '❌ 새 저장소를 주인/이름 형태로 넣어라'; exit 1 ;; esac
OLD_OWNER=${OLD%%/*}; OLD_NAME=${OLD#*/}
NEW_OWNER=${NEW%%/*}
say ''

# ── ① 접근 확인 ────────────────────────────────────────────────────────────
hr; say '① 접근 확인'; hr
if ! git ls-remote "https://github.com/$OLD" >/dev/null 2>&1; then
  say "❌ 옛 저장소에 접근이 안 된다 — $OLD"
  say '   이 컴퓨터가 그 계정으로 로그인돼 있는지 먼저 봐라.'
  exit 1
fi
say "✅ 옛 저장소 읽힘 — $OLD"
if ! git ls-remote "https://github.com/$NEW" >/dev/null 2>&1; then
  say "❌ 새 저장소가 아직 없거나 권한이 없다 — $NEW"
  say '   새 계정에 같은 이름으로 **빈** 저장소를 먼저 만들어라(읽어보기 파일도 넣지 마라).'
  exit 1
fi
say "✅ 새 저장소 읽힘 — $NEW"
say ''

# ── ② 통째 복제(정본 위임 · 사본 0) ────────────────────────────────────────
hr; say '② 통째 복제'; hr
if [ ! -f "$HERE/clone_to_new_account.sh" ]; then
  say "❌ 복제 정본이 없다 — $HERE/clone_to_new_account.sh"
  exit 1
fi
if ! bash "$HERE/clone_to_new_account.sh" "$OLD" "$NEW"; then
  say '❌ 복제 실패 — 위 사유를 보고 고쳐라. 여기서 멈춘다.'
  exit 1
fi
say ''

# ── ③ 새 저장소 안 옛 값 스캔 ─────────────────────────────────────────────
WORK="${TMPDIR:-/tmp}/nomute_home_mig_$$"
cleanup() { [ -n "${WORK:-}" ] && rm -rf "$WORK"; }
trap cleanup EXIT

hr; say '③ 새 저장소 안에 남은 옛 값 찾기'; hr
if ! git clone -q "https://github.com/$NEW" "$WORK"; then
  say '❌ 새 저장소를 못 받았다.'; exit 1
fi
cd "$WORK" || exit 1

# 스냅샷·기록·의존물은 대상 밖(그때 있었던 일이라 갈아끼우면 역사가 거짓이 된다)
# ⚠ `:!_versions/**` 표기 금지 — 밑줄을 pathspec magic 으로 오해해 목록이 통째로 0이 되고
#   「전 항목 0건 = 깨끗함」처럼 보인다(260815 실측 = 가장 조용한 실패). 반드시 `:(exclude)`.
EXCLUDES=(':(exclude)node_modules/**' ':(exclude)dist/**' ':(exclude)_versions/**'
          ':(exclude)docs/**' ':(exclude)CLAUDE.md' ':(exclude)AGENTS.md')

# ⚠ `git ls-files` 는 한글·특수문자 이름을 따옴표로 감싸 출력한다 → `-z` 로 받아야 실제 경로가 나온다
#   (260815 실측 = 1차 실행에서 한글 이름 3개가 조용히 빠졌다).
scan() {   # $1 = 찾을 문자열 · $2 = 라벨
  local hits=0
  while IFS= read -r -d '' p; do
    [ -f "$p" ] || continue
    grep -Iq . "$p" 2>/dev/null || continue
    if grep -Fq -- "$1" "$p" 2>/dev/null; then
      grep -Fn -- "$1" "$p" | head -3 | while IFS= read -r ln; do
        printf '    %s:%s\n' "$p" "${ln%%:*}"
      done
      hits=$((hits+1))
    fi
  done < <(git ls-files -z -- . "${EXCLUDES[@]}" 2>/dev/null)
  printf '  %s → %s개 파일\n' "$2" "$hits"
}

say '  (스냅샷·의존물 폴더는 대상 밖)'
say ''
say "  ▸ 옛 저장소 이름"
scan "$OLD" '옛 저장소 이름'
say "  ▸ 옛 계정 이름"
scan "$OLD_OWNER" '옛 계정 이름'
say '  ▸ 옛 보관함 주소(있으면)'
scan 'pub-83f8cf3892ae44c38bebf1805c954508.r2.dev' '옛 보관함 주소'
say ''

# ── ④ 이름만 치환(주소는 사람 판단) ───────────────────────────────────────
hr; say '④ 저장소·계정 이름 갈아끼우기'; hr
say '  주소류는 안 건드린다(위 스캔 결과를 보고 사람이 판단).'
read -rp '  저장소·계정 이름만 지금 바꿀까? [y/N] : ' DOIT
case "$DOIT" in
  y|Y)
    n=0
    while IFS= read -r -d '' p; do
      [ -f "$p" ] || continue
      grep -Iq . "$p" 2>/dev/null || continue
      grep -Fq -- "$OLD" "$p" 2>/dev/null || continue
      python3 - "$p" "$OLD" "$NEW" <<'PY' || exit 1
import io,sys
p,old,new = sys.argv[1],sys.argv[2],sys.argv[3]
s = io.open(p,encoding='utf-8',errors='surrogateescape').read()
io.open(p,'w',encoding='utf-8',errors='surrogateescape').write(s.replace(old,new))
PY
      n=$((n+1))
    done < <(git ls-files -z -- . "${EXCLUDES[@]}" 2>/dev/null)
    say "  ✅ $n개 파일 고쳤다."
    # ⚠ 커밋 메시지에 백틱을 넣으면 셸이 명령 치환을 해서 죽는다 → 파일로 넘긴다(260815 실측).
    printf '%s\n' '계정 이관: 저장소 이름 갈아끼우기' > /tmp/nomute_home_mig_msg.txt
    git add -A
    git commit -q -F /tmp/nomute_home_mig_msg.txt || say '  (바뀐 게 없어 커밋 안 함)'
    if git push -q origin HEAD; then say '  ✅ 새 저장소에 올렸다.'; else say '  ❌ 올리기 실패 — 권한을 봐라.'; fi
    ;;
  *) say '  → 건너뜀. 위 스캔 결과만 참고해라.' ;;
esac
say ''

# ── ⑤ 사람이 화면에서 해야 하는 것 ────────────────────────────────────────
hr; say '⑤ 남은 것 — 화면에서 사람이 한다'; hr
cat <<EOS
  [배포 = 클라우드플레어]
   1. 새 계정에서 화면 프로젝트를 새로 만든다.
      ⚠ 만들기 버튼이 엉뚱한 제품으로 샌다. **출력 폴더 칸이 보이는 쪽**이 맞는 제품이다.
   2. 새 저장소를 연결하고 빌드 설정을 넣는다.
        빌드 명령  : npx astro build
        출력 폴더  : dist
      (맥 대행 배포기가 지금 그대로 굽고 있는 값이다 — scripts/mac/nomute_home_deploy.sh)
   3. 배포 주소는 **이름으로 유추하지 마라**. 이름이 겹치면 뒤에 식별자가 붙는다.
      배포 화면의 도메인 표기가 유일한 정본이다.
   4. 주소 nomute.kr 붙이기 = **이름표 하나만** 새 배포로 보낸다.
      ⚠ 도메인 통째 이전은 누르지 마라 — 다른 화면까지 딸려간다.
      ⚠ 도메인과 배포가 다른 계정이면 구름 표시(프록시)를 꺼야 한다.
   5. 옛 배포는 지우지 마라. 며칠 새 쪽이 실제로 도는 걸 보고 나중에 정리한다.

  [외부 시계 = 크론잡]
   6. 잡 목록에서 주소에 다음이 들어간 것을 찾는다 : $OLD
      그 자리를 $NEW 로 바꾸고, 열쇠(토큰)도 새 계정 것으로 바꾼다.
      ⚠ 새 저장소의 자동 작업이 켜지기 전에 시계를 켜면 실패가 쌓여 잡이 스스로 꺼진다.
      순서 = 자동 작업 확인 먼저, 시계 켜기 나중.

  [이 저장소(에디터) 안에 남은 자리 3곳]
   7. scripts/mac/nomute_home_deploy.sh
        코드는 그대로 둬도 된다(폴더 이름만 보고 도는 구조).
        맥에서 ~/nomute_homepage 폴더의 원격 주소만 새 저장소로 바꾼다 :
          cd ~/nomute_homepage && git remote set-url origin https://github.com/$NEW
        그리고 ~/nomute-action/환경변수.txt 의 클라우드 열쇠·계정값이 새 계정 것인지 본다.
   8. .github/workflows/kit-fanout.yml  — 전파 대상 목록의 주인이 옛 계정으로 박혀 있다.
   9. .github/workflows/claude-sync.yml — 전파 대상 줄도 같다.
      (8·9는 이 저장소를 고치는 일이라 다음 세션이 코드로 한다)
EOS
hr
exit 0
