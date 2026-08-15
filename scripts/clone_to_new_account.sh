#!/usr/bin/env bash
# clone_to_new_account.sh — 옛 저장소를 새 계정 저장소로 통째 복제(운영자 컴퓨터에서 1회 실행)
#
# 왜 사람 컴퓨터인가: 클로드 세션은 프록시가 인가한 저장소에만 자격증명을 준다(260815 실측 =
#   `remote: access denied by the git proxy: nomutefb/editor is not in this session's authorized
#    repository set` · 403). 주인이 다른 저장소는 세션 소스로 못 붙여서 세션에서는 구조적으로 불가.
#   → 두 저장소 모두에 로그인돼 있는 사람 컴퓨터가 유일한 경로.
#
# 무엇을 옮기나: 지난 기록 전량(모든 가지·태그·커밋). 요청·논의 기록은 git 밖이라 안 따라온다.
#
# 사용:
#   bash clone_to_new_account.sh                       # 대화형
#   bash clone_to_new_account.sh nomutefb/editor nomutefb/editor
set -uo pipefail

OLD=${1:-}
NEW=${2:-}

hr() { printf '%s\n' '────────────────────────────────────────'; }

hr; echo '📦 저장소 통째 복제'; hr
[ -z "$OLD" ] && read -rp '  옛 저장소 (주인/이름) : ' OLD
[ -z "$NEW" ] && read -rp '  새 저장소 (주인/이름) : ' NEW
echo

case "$OLD" in */*) : ;; *) echo "❌ 옛 저장소를 주인/이름 형태로 넣어라 (예: nomutefb/editor)"; exit 1 ;; esac
case "$NEW" in */*) : ;; *) echo "❌ 새 저장소를 주인/이름 형태로 넣어라 (예: nomutefb/editor)"; exit 1 ;; esac

WORK="${TMPDIR:-/tmp}/nomute_clone_$$"
cleanup() { [ -n "${WORK:-}" ] && rm -rf "$WORK"; }
trap cleanup EXIT

echo "  옛 저장소 → $OLD"
echo "  새 저장소 → $NEW"
echo "  임시 폴더 → $WORK"
echo

# ① 새 저장소가 비어 있는지 먼저 본다 — 안 비었으면 --mirror 가 상대 기록을 지운다.
hr; echo '① 새 저장소 상태 확인'; hr
NEWREFS=$(git ls-remote "https://github.com/$NEW" 2>&1)
if [ $? -ne 0 ]; then
  echo "❌ 새 저장소에 접근이 안 된다:"
  echo "$NEWREFS" | head -3
  echo
  echo "   확인할 것 = 저장소가 실제로 있나 · 초대를 수락했나 · 이 컴퓨터가 그 계정으로 로그인돼 있나"
  exit 1
fi
if [ -n "$NEWREFS" ]; then
  echo "⚠ 새 저장소가 비어 있지 않다. 지금 들어 있는 것:"
  echo "$NEWREFS" | head -5
  echo
  echo "  이대로 진행하면 위 내용이 **지워지고** 옛 저장소 것으로 덮인다."
  read -rp '  덮어써도 되나? [y/N] : ' OK
  case "$OK" in y|Y) : ;; *) echo '  → 중단. 새 저장소를 비우거나 다른 이름으로 만들어라.'; exit 1 ;; esac
else
  echo '✅ 비어 있음 — 그대로 진행'
fi
echo

# ② 옛 저장소를 통째로 받는다(작업본 없이 기록만 = mirror).
hr; echo '② 옛 저장소 받는 중 (크다 · 몇 분 걸린다)'; hr
if ! git clone --mirror "https://github.com/$OLD" "$WORK"; then
  echo "❌ 옛 저장소를 못 받았다. 이 컴퓨터가 그 계정으로 로그인돼 있나 확인해라."
  exit 1
fi
echo

# ③ 새 저장소로 통째로 민다.
hr; echo '③ 새 저장소로 미는 중'; hr
cd "$WORK" || exit 1
if ! git push --mirror "https://github.com/$NEW"; then
  echo
  echo "❌ 밀기 실패. 흔한 사유 ="
  echo "   · 새 계정에 쓰기 권한이 없다(초대 수락 여부·권한이 Write 이상인지)"
  echo "   · 옛 계정에 제재가 걸려 밀기가 막혔다"
  exit 1
fi
echo

# ④ 사후 대조 — 민 게 실제로 도착했나(성공을 실패로/실패를 성공으로 오판 금지).
hr; echo '④ 도착 확인'; hr
OLD_N=$(git ls-remote "https://github.com/$OLD" 2>/dev/null | wc -l | tr -d ' ')
NEW_N=$(git ls-remote "https://github.com/$NEW" 2>/dev/null | wc -l | tr -d ' ')
echo "  옛 저장소 가지·태그 = $OLD_N"
echo "  새 저장소 가지·태그 = $NEW_N"
echo
if [ "${NEW_N:-0}" -gt 0 ] && [ "${NEW_N:-0}" -ge "${OLD_N:-0}" ]; then
  hr; echo '✅ 복제 끝.'
  echo "   새 저장소 = https://github.com/$NEW"
  echo '   다음 = 새 저장소를 받아서 `bash scripts/migrate_account.sh` 로 배선 갈아끼우기'
  hr
  exit 0
else
  hr; echo '❌ 도착한 게 모자란다 — 위 숫자를 비교해라.'; hr
  exit 1
fi
