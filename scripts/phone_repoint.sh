#!/usr/bin/env bash
# 폰(Termux)·맥 수집 레인을 **새 저장소로 옮기는 1회용** — 260816 계정 이관 뒤처리.
#
# ▷ 왜 = 계정 이관(260816)으로 정본 저장소가 nomutefb/editor 로 바뀌었는데
#   폰 클론만 옛 저장소를 그대로 보고 있었다. 그 상태에서 수집·커밋·푸시가 **전부 성공**한다
#   (옛 곳으로 잘 간다) → 진단서도 전 항목 초록. 다만 화면이 읽는 곳은 새 저장소라
#   폰이 걷은 것은 화면에 **한 건도 안 뜬다**. 실측 = 새 저장소 main 에 (phone) 커밋 0건.
#   폰은 옛 저장소에서 코드를 받으므로 이 고침이 폰에 저절로 도착할 길이 없다
#   → 폰에서 딱 한 번 이 파일을 돌려야 한다(그 뒤부터는 새 저장소에서 코드도 같이 받는다).
#
# ▷ 쓰는 법(폰 Termux 한 줄):
#     bash ~/nomute-editor/scripts/phone_repoint.sh
#   수집은 돌리지 말고 주소만 바꾸려면:  bash ~/nomute-editor/scripts/phone_repoint.sh --no-run
#
# ▷ 하는 일 = ① 보내는 곳을 새 저장소로 바꾼다 ② 접속·자격을 실제로 시험한다
#   (자격이 없으면 토큰을 한 번 물어보고 폰에 저장한다) ③ 새 저장소 최신으로 맞춘다
#   ④ 수집을 한 번 돌려 **정말 새 저장소에 꽂히는지 눈으로 확인**시킨다.
#
# ▷ 두 번 돌려도 안전하다(이미 새 저장소면 ①을 건너뛴다).
# ▷ 크론은 손대지 않는다 — 폴더 이름(~/nomute-editor)이 그대로라 등록해 둔 줄이 계속 유효하다.
set -u

NEW_SLUG="nomutefb/editor"
NEW_URL="https://nomutefb@github.com/nomutefb/editor"
NEW_USER="nomutefb"
RUN=1; [ "${1:-}" = "--no-run" ] && RUN=0
export GIT_TERMINAL_PROMPT=0

ok(){ printf '  ✅ %s\n' "$*"; }
no(){ printf '  ❌ %s\n' "$*"; }
hm(){ printf '  ⚠  %s\n' "$*"; }

echo "▶ 폰 수집 레인 이사 — $(date '+%Y-%m-%d %H:%M:%S')"
echo

# ── 0) 저장소 폴더 찾기 ─────────────────────────────────────────────────────
REPO=""
_try="$(cd "$(dirname "$0")/.." 2>/dev/null && pwd || true)"
for c in "$_try" "$HOME/nomute-editor" "$HOME/editor" "$HOME/storage/shared/nomute-editor"; do
  [ -n "$c" ] && [ -d "$c/.git" ] && { REPO="$c"; break; }
done
if [ -z "$REPO" ]; then
  no "저장소 폴더를 못 찾았다 — 폰에서 아래로 새로 받고 다시 실행해라"
  echo "     git clone $NEW_URL ~/nomute-editor"
  exit 1
fi
cd "$REPO" || exit 1
ok "저장소 폴더 = $REPO"

# ── 1) 보내는 곳 바꾸기 ─────────────────────────────────────────────────────
_slug(){ local u; u="$(git remote get-url origin 2>/dev/null || true)"; u="${u%.git}"; u="${u#*github.com}"; u="${u#:}"; u="${u#/}"; printf '%s' "$u"; }
BEFORE="$(_slug)"
echo
echo "① 보내는 곳"
echo "     전: ${BEFORE:-(없음)}"
if [ "$BEFORE" = "$NEW_SLUG" ]; then
  ok "이미 정본이다 — 바꿀 것 없음"
else
  git remote set-url origin "$NEW_URL" || { no "주소 바꾸기 실패(권한·잠김)"; exit 1; }
  ok "바꿨다"
fi
echo "     후: $(_slug)"

# ── 2) 접속·자격 시험(안 되면 토큰을 한 번만 물어본다) ──────────────────────
echo
echo "② 접속·자격"
_probe(){ timeout 30 git ls-remote origin -h refs/heads/main >/dev/null 2>&1; }
if _probe; then
  ok "새 저장소 접속 정상 — 토큰 입력 불필요"
else
  hm "새 계정 자격이 폰에 없다(옛 계정 토큰으로는 새 저장소에 못 쓴다)"
  echo "     깃허브 nomutefb 계정의 토큰(classic · repo 권한)을 한 번만 넣어라."
  echo "     화면에 안 보이게 입력된다. 그냥 엔터 = 건너뛰기(주소만 바뀐 채로 끝난다)."
  printf '     토큰: '
  TOK=""; read -r -s TOK || true; echo
  if [ -z "$TOK" ]; then
    no "토큰 없이 끝냈다 — 수집은 돌아도 **올라가지는 않는다**. 토큰 만든 뒤 이 파일을 다시 실행해라."
    exit 1
  fi
  CF="$HOME/.git-credentials"
  touch "$CF" 2>/dev/null || true
  chmod 600 "$CF" 2>/dev/null || true
  # 같은 계정 줄이 이미 있으면 새 값으로 갈아끼운다(옛 계정 줄은 그대로 둔다 = 옛 저장소도 계속 열린다).
  if [ -s "$CF" ]; then grep -v "https://${NEW_USER}:" "$CF" > "$CF.tmp" 2>/dev/null && mv "$CF.tmp" "$CF"; fi
  printf 'https://%s:%s@github.com\n' "$NEW_USER" "$TOK" >> "$CF"
  chmod 600 "$CF" 2>/dev/null || true
  git config --global credential.helper store
  TOK=""
  if _probe; then
    ok "토큰 저장 완료 — 접속 정상"
  else
    no "토큰을 넣었는데도 접속이 안 된다 → 토큰 권한(repo)·계정(nomutefb)·오타를 확인해라"
    exit 1
  fi
fi

# ── 3) 새 저장소 최신으로 맞추기 ────────────────────────────────────────────
echo
echo "③ 코드·데이터 맞추기"
git fetch -q origin main 2>/dev/null || { no "받기 실패(네트워크)"; exit 1; }
_unp="$(git rev-list --count origin/main..HEAD 2>/dev/null || echo 0)"
[ "${_unp:-0}" -gt 0 ] && hm "옛 저장소 기준 로컬 커밋 ${_unp}개는 버린다(수집물은 30분마다 다시 만들어지는 값이라 손실 없음)"
git checkout -q -B main origin/main 2>/dev/null || true
git reset --hard -q origin/main 2>/dev/null || true
ok "새 저장소 최신에 맞췄다 — $(git log -1 --format='%h %s' 2>/dev/null | cut -c1-60)"

# ── 4) 진짜 꽂히는지 한 번 돌려서 확인 ──────────────────────────────────────
if [ "$RUN" = 0 ]; then
  echo; echo "④ 수집 실행은 건너뛴다(--no-run)"; echo; echo "끝. 다음 크론 주기부터 새 저장소로 간다."; exit 0
fi
echo
echo "④ 수집 1회 실행(몇 분 걸린다 · 기다려라)"
_before_head="$(git rev-parse origin/main 2>/dev/null || true)"
echo "   ─ 구독 수집(SNS)"
bash scripts/phone_subs.sh 2>&1 | tail -5 | sed 's/^/     /' || true
echo "   ─ 뉴스 수집"
bash scripts/phone_scrape.sh 2>&1 | tail -5 | sed 's/^/     /' || true

echo
echo "⑤ 착지 확인"
for f in "$HOME/.nomute_phone_land" "$HOME/.nomute_phone_scrape_land"; do
  [ -f "$f" ] && echo "     $(basename "$f"): $(cat "$f" 2>/dev/null)"
done
git fetch -q origin main 2>/dev/null || true
if [ "$(git rev-parse origin/main 2>/dev/null || true)" != "$_before_head" ]; then
  ok "새 저장소 main 이 움직였다 = 꽂혔다"
  git log origin/main -3 --format='       %h %ad %s' --date=format:'%m-%d %H:%M' 2>/dev/null
else
  hm "새 저장소 main 이 그대로다 — 걷을 새 내용이 없었거나(무변동) 올리기가 막혔다. 위 착지 줄의 사유를 봐라."
fi
echo
echo "끝. 다음부터는 크론이 알아서 새 저장소로 보낸다(폴더·크론 줄 그대로)."
