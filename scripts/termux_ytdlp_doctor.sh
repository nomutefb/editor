#!/data/data/com.termux/files/usr/bin/bash
# 노뮤트 · 폰(termux) 유튜브 받기 자가진단 + 자동수리
#   사용법:  bash termux_ytdlp_doctor.sh [영상주소]
#   주소 생략 = 기본 검사용 주소로 진단만.
#
# 하는 일(순서가 곧 진단 순서 = 위에서부터 원인이 걸러진다)
#   ① yt-dlp 실물·버전 확인 → 30일 넘게 낡았으면 그 자리에서 최신으로 갱신
#   ② 자바스크립트 실행기(node) 확인 → 없으면 설치, 있는데 yt-dlp가 못 찾으면 경로를 직접 물려준다
#      ⚠ 실측(260819 클라우드) = `--js-runtimes node` 만 주면 "실행기를 못 찾겠다"가 그대로 뜨고,
#         `node:<경로>` 로 경로까지 줘야 비로소 잡힌다. 이 파일은 항상 경로까지 물려준다.
#   ③ 실제로 받아본다 → 실패하면 오류 문구로 원인을 갈라 다음 할 일을 한국어로 지목
#   ④ 쿠키 파일이 옆에 있으면(cookies.txt) 자동으로 물려서 한 번 더 시도
#
# 되돌리기: 이 파일은 yt-dlp 갱신과 node 설치 말고는 폰을 안 건드린다.
# 기록: 마지막 실행 로그 = ~/.nomute_ytdlp_doctor.log
set -u
LOG="$HOME/.nomute_ytdlp_doctor.log"
: > "$LOG"
say(){ printf '%s\n' "$*" | tee -a "$LOG"; }
run(){ "$@" >>"$LOG" 2>&1; }

URL="${1:-https://youtube.com/shorts/kjyF23AtpI8}"
say "=== 노뮤트 폰 유튜브 받기 진단 ==="
say "대상 주소: $URL"
say ""

# ── ① yt-dlp 실물·버전 ────────────────────────────────────────────────
YTD=""
if command -v yt-dlp >/dev/null 2>&1; then YTD="yt-dlp"
elif python3 -c "import yt_dlp" >/dev/null 2>&1; then YTD="python3 -m yt_dlp"
fi

if [ -z "$YTD" ]; then
  say "① 받기 도구가 폰에 아예 없다 → 지금 깐다"
  pkg install -y python 2>&1 | tail -2 | tee -a "$LOG"
  pip install -U yt-dlp 2>&1 | tail -3 | tee -a "$LOG"
  command -v yt-dlp >/dev/null 2>&1 && YTD="yt-dlp" || YTD="python3 -m yt_dlp"
else
  VER="$($YTD --version 2>/dev/null | head -1)"
  say "① 받기 도구 있음 · 버전 $VER"
  # 버전 문자열이 곧 날짜다(2026.07.04 꼴). 30일 넘게 낡았으면 갱신.
  VD="$(printf '%s' "$VER" | tr -d '\r' | sed 's/\./-/g' | cut -c1-10)"
  OLD=1
  if command -v date >/dev/null 2>&1; then
    NOW=$(date +%s); THEN=$(date -d "$VD" +%s 2>/dev/null || echo 0)
    [ "$THEN" -gt 0 ] && [ $(( (NOW-THEN)/86400 )) -lt 30 ] && OLD=0
  fi
  if [ "$OLD" = "1" ]; then
    say "   → 낡았다(또는 날짜를 못 읽었다). 최신으로 갱신한다"
    pip install -U yt-dlp 2>&1 | tail -3 | tee -a "$LOG"
    NEW="$($YTD --version 2>/dev/null | head -1)"
    if [ "$NEW" = "$VER" ]; then
      say "   갱신해도 $NEW 그대로 = 이게 지금 나온 것 중 가장 최신이다(문제 아님)"
    else
      say "   갱신됨: $VER → $NEW"
    fi
  else
    say "   → 충분히 최신이다"
  fi
fi
say ""

# ── ② 자바스크립트 실행기 ──────────────────────────────────────────────
say "② 자바스크립트 실행기 확인"
JSARG=()
NODEBIN="$(command -v node 2>/dev/null || true)"
if [ -z "$NODEBIN" ]; then
  say "   없다 → 지금 깐다 (유튜브가 요즘 이걸 요구한다)"
  pkg install -y nodejs-lts 2>&1 | tail -3 | tee -a "$LOG" || pkg install -y nodejs 2>&1 | tail -3 | tee -a "$LOG"
  NODEBIN="$(command -v node 2>/dev/null || true)"
fi
if [ -n "$NODEBIN" ]; then
  say "   실행기 있음 · $NODEBIN ($(node --version 2>/dev/null))"
  JSARG=(--js-runtimes "node:$NODEBIN")
  say "   → 경로까지 물려준다 (이름만 주면 못 찾는 판이 실재한다)"
else
  say "   ⚠ 실행기 설치 실패 — 유튜브 일부 화질이 통째로 안 잡힐 수 있다"
fi
say ""

# ── ③ 실제로 받아본다 ─────────────────────────────────────────────────
COOK=()
for c in ./cookies.txt "$HOME/cookies.txt" "$HOME/storage/downloads/cookies.txt"; do
  [ -f "$c" ] && { COOK=(--cookies "$c"); say "④ 쿠키 파일 발견: $c (같이 물린다)"; break; }
done

say "③ 실제로 받아본다 (화질 목록만 조회 = 용량 0)"
OUT="$( $YTD --no-cache-dir --socket-timeout 30 \
        ${JSARG[@]+"${JSARG[@]}"} ${COOK[@]+"${COOK[@]}"} \
        --remote-components ejs:github -F "$URL" 2>&1 )"
printf '%s\n' "$OUT" >> "$LOG"
say ""

case "$OUT" in
  *"not a bot"*|*"Sign in to confirm"*)
      say "판정 ▶ 유튜브가 이 폰을 '사람인지 확인'으로 막았다."
      say "   할 일 = 유튜브 로그인 쿠키를 파일로 뽑아 이 폴더에 cookies.txt 로 두고 다시 실행."
      say "   (크롬 확장 'Get cookies.txt LOCALLY' 로 youtube.com 에서 내보내면 된다)"
      say "   ⚠ 도구 버전·실행기 문제가 아니다 — 갱신을 아무리 해도 안 풀린다." ;;
  *"Requested format is not available"*|*"Only images are available"*|*"nsig extraction failed"*|*"n challenge"*)
      say "판정 ▶ 유튜브 잠금(n챌린지)을 못 풀었다 = 자바스크립트 실행기 축."
      say "   할 일 = pkg install nodejs-lts 하고 이 파일을 다시 실행." ;;
  *"HTTP Error 429"*)
      say "판정 ▶ 유튜브가 이 회선에 '너무 잦다'(429)를 냈다."
      say "   할 일 = 와이파이↔데이터를 바꿔 회선을 갈고 10분 뒤 다시. 그래도면 쿠키를 물려라." ;;
  *"Unsupported URL"*|*"Unable to extract"*)
      say "판정 ▶ 도구가 유튜브 구조 변경을 아직 못 따라갔다 = 버전 축."
      say "   할 일 = pip install -U --pre yt-dlp (야간판까지 당겨온다) 후 재실행." ;;
  *"format code"*|*"video only"*|*"audio only"*)
      say "판정 ▶ 정상이다. 화질 목록이 나왔다 = 받기가 된다."
      say "   실제 받기 = $YTD ${JSARG[*]-} -f 'bv*+ba[ext=m4a]/bv*+ba/b' '$URL'"
      say "   (편집 프로그램에 소리까지 물리려면 위 m4a 형태를 그대로 쓸 것)" ;;
  *)  say "판정 ▶ 처음 보는 형태다. 아래 원문을 그대로 클로드에게 넘겨라."
      say "── 원문 꼬리 ──"; printf '%s\n' "$OUT" | tail -12 | tee -a "$LOG" ;;
esac

say ""
say "전체 기록: $LOG"
