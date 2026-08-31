#!/data/data/com.termux/files/usr/bin/sh
# 드라이브싱크 자가진단 + 최신판 설치 1발 (운영자 260811 "계속 실패하는데 이유를 모르겠네")
#
# ▷ 폰 Termux에서 한 줄:
#     curl -fsSL https://raw.githubusercontent.com/nomutefb/editor/main/docs/drivesync-fix.sh | sh
#
# ▷ 하는 일 = 4단(읽기 전용 진단 → 장부 회수 → 설치 → 1회 실행)
#   ① 지금 왜 실패하는지 그 자리에서 출력(설치된 판·마지막 실행·연결 생사·받아오기 프로그램 판
#      · 로그의 진짜 실패 줄 · 배치에서 못 받은 파일 · 격리 원장 · 저장 공간)
#   ② **장부 오염 회수** — 로그가 실패했다고 적은 파일이 로컬에 없는데 장부엔 「받았다」로
#      들어가 있으면 영영 안 온다(260702·260719와 같은 병) → 그 줄만 장부에서 빼서 다시 받게 한다
#   ③ 최신판 설치   ④ 디바운스 풀고 1회 실행 → 밀린 배치·회수분 정산
#
# ▷ 안전: 사진·영상 삭제 0 · rclone 설정 무접촉 · 장부는 손대기 전 `.bak`으로 통째 복사 ·
#   회수 대상은 **로그가 이름을 댄 파일에 한정**(전량 리셋 = 재다운로드 폭탄이라 절대 안 한다) ·
#   내려받기 실패 시 종전 스크립트 그대로(악화 경로 0).
SYNC="$HOME/.termux/tasker/drive-gallery-sync.sh"
LOG="$HOME/.drivesync.log"
SEEN="$HOME/.drivesync.seen"
NEW="$HOME/.drivesync.new"
MISS="$HOME/.drivesync.miss"
STUCK="$HOME/.drivesync.stuck"
TMPD="$HOME/.drivesync.fixtmp"
LOCAL="/sdcard/Pictures/DriveSync"
URL="https://raw.githubusercontent.com/nomutefb/editor/main/docs/drive-gallery-sync.sh"

# 파일이 없어도 셸 에러를 안 내는 줄 세기(구판 `wc -l < 없는파일` = sh: cannot open 실측 봉합)
cnt(){ [ -f "$1" ] && wc -l < "$1" 2>/dev/null | tr -d ' ' || echo 0; }

echo "══════════ ① 지금 상태 ══════════"
printf '설치된 판 : %s\n' "$(cat "$HOME/.drivesync.ver" 2>/dev/null || echo '표기 없음(v1.3 이하)')"
printf '받아오기  : %s\n' "$(rclone version 2>/dev/null | head -1 || echo '없음')"
if [ -f "$HOME/.drivesync.last" ]; then
  printf '마지막 실행: %s분 전\n' "$(( ($(date +%s) - $(cat "$HOME/.drivesync.last")) / 60 ))"
else
  printf '마지막 실행: 기록 없음(Tasker가 안 쏘는 중일 수 있다)\n'
fi
printf '이번 배치  : %s건 대기\n' "$(cnt "$NEW")"

# ── 코드가 어느 저장소를 보고 있나(260831 신설) ────────────────────────────────
#   실사고 = 260816 계정 이관 뒤 폰에 깔린 판이 **옛 저장소 raw**를 그대로 들고 있었다.
#   그 주소는 계정 제재로 전 파일 404 → 하루 1회 자가 갱신이 매번 조용히 실패한다
#   (fail-soft라 동기화 자체는 돌아서 **증상이 0** = 폰만 옛 코드에 영영 갇힌다).
#   ⚠ 아래가 「옛 주소」로 나오면 이 진단기 ③이 그 자리에서 새 판으로 덮어 해소된다.
SU=$(grep -m1 '^SELF_URL=' "$SYNC" 2>/dev/null | cut -d'"' -f2)
case "$SU" in
  *nomutefb/editor*) printf '코드 출처  : ✅ 새 저장소\n' ;;
  "")                printf '코드 출처  : ? 표기 없음(v1.8 이하 = 자가 갱신 자체가 없는 판)\n' ;;
  *)                 printf '코드 출처  : ❌ 옛 저장소(404) — 자가 갱신이 매번 실패해 왔다\n             %s\n' "$SU" ;;
esac

echo "── 드라이브 연결(목록 조회) ──"
#   ⚠ 한 번만 재면 「연결 실패」까지밖에 못 말한다 — 260831 실사고가 정확히 그 자리였다
#   (인증·회선은 멀쩡한데 **나가는 길**만 죽어서, 그냥 재면 인증 축으로 오진한다).
#   → 그냥 한 번 · 예전 주소로 한 번, 두 갈래로 재서 원인을 이름으로 가른다.
ls_ok(){ rclone lsf $1 --contimeout 15s --timeout 60s gdrive: >/dev/null 2>&1; }
if ls_ok ""; then
  echo "  ✅ 연결·인증 정상 → 범인은 받기 한 자리"
elif ls_ok "--bind 0.0.0.0"; then
  echo "  ⚠ 새 주소 길이 막혔다(예전 주소로는 붙는다) = 회선이 주는 길이 바뀐 것."
  echo "     이 진단기 ③이 그 길을 고정한 판으로 덮어 그 자리에서 해소된다."
else
  echo "  ❌ 두 길 다 실패 = 인증·회선 축 → rclone config reconnect gdrive:"
fi

echo "── 로그가 말하는 진짜 실패 사유(최근 5줄) ──"
if grep -qE 'ERROR|Failed to copy|Fatal error' "$LOG" 2>/dev/null; then
  grep -E 'ERROR|Failed to copy|Fatal error' "$LOG" 2>/dev/null | tail -5 | sed 's|^|  |'
else
  echo "  (실패 줄 없음 — 로그 꼬리: $(tail -1 "$LOG" 2>/dev/null))"
fi

echo "── 배치에서 실제로 못 받은 파일 ──"
if [ -s "$NEW" ]; then
  n=0
  while IFS= read -r f; do
    [ -n "$f" ] || continue
    [ -s "$LOCAL/$f" ] || { echo "  ✗ $f"; n=$((n + 1)); }
  done < "$NEW"
  [ "$n" = 0 ] && echo "  (전부 도착 — 배치는 다음 실행에 정리된다)" || echo "  → 못 받은 것 ${n}건"
else
  echo "  (대기 배치 없음)"
fi
[ -s "$STUCK" ] && { echo "── 격리된 파일(연속 실패) ──"; tail -5 "$STUCK" | sed 's|^|  |'; }

echo "── 저장 공간 ──"
df -h /sdcard 2>/dev/null | tail -1 | sed 's|^|  |'

echo ""
echo "══════════ ② 장부 오염 회수 ══════════"
# 로그가 「실패」라고 적은 파일 이름만 뽑는다(전량 리셋 금지 = 재다운로드 폭탄 차단)
rm -rf "$TMPD"; mkdir -p "$TMPD"
grep -E 'Failed to copy' "$LOG" 2>/dev/null \
  | sed -n 's|^[0-9/: ]*ERROR *: *\(.*\): Failed to copy:.*|\1|p' \
  | sed '/^$/d' | sort -u > "$TMPD/failed"
FN=$(cnt "$TMPD/failed")
if [ "$FN" = 0 ]; then
  echo "  (로그에 실패로 적힌 파일 없음 — 회수할 것 0)"
else
  : > "$TMPD/orphan"
  while IFS= read -r f; do
    [ -n "$f" ] || continue
    # 로컬에 없는데 장부엔 「받았다」로 들어가 있으면 = 영영 안 오는 상태
    if [ ! -s "$LOCAL/$f" ] && grep -qxF "$f" "$SEEN" 2>/dev/null; then
      printf '%s\n' "$f" >> "$TMPD/orphan"
    fi
  done < "$TMPD/failed"
  ON=$(cnt "$TMPD/orphan")
  if [ "$ON" = 0 ]; then
    echo "  ✅ 오염 0 — 실패했던 파일 ${FN}건은 이미 받아졌거나 재시도 대기 중"
  else
    cp "$SEEN" "$SEEN.bak" 2>/dev/null
    cp "$SEEN" "$TMPD/seen.in"
    # ⚠ 재작성 = awk 대조(이 파이프라인의 정본 관용구 = drive-gallery-sync.sh 의 SEEN↔NOW 대조와 같은 문법).
    #   구판 `grep -vxF -f`는 260811 실환경에서 **결과를 통째로 비웠다**(스텁에선 통과 · 폰에서 실패
    #   = 안전장치가 회수를 건너뛰고 원본을 지켰다). grep 구현차에 기대지 않는 문법으로 교체한다.
    IN=$(cnt "$TMPD/seen.in")
    awk 'FNR==NR{o[$0]=1;next} !($0 in o)' "$TMPD/orphan" "$TMPD/seen.in" > "$TMPD/seen.out" 2>/dev/null
    OUT=$(cnt "$TMPD/seen.out")
    # ⚠ 안전 검문 = 「줄 수」가 아니라 「무엇이 지워졌나」로 본다(260831 실사고 봉합).
    #   구판은 빠진 **줄 수** ≤ 오염 건수를 요구했는데, 장부는 같은 파일이 여러 줄 들어갈 수 있다
    #   (매 회차 배치가 통째로 덧붙는 구조라 재시도분이 중복으로 쌓인다) → 58건을 빼는데 111줄이
    #   빠지는 것이 **정상**인데 구판은 그걸 이상으로 읽고 영구히 건너뛰었다.
    #   실측 260831 = 장부 15617줄 → 15506줄(−111)이 예상(−58)과 안 맞는다며 3회 연속 회수 거부
    #   = 그 58건이 로컬에 없는데 장부엔 「받았다」로 남아 **영영 안 받아지는 상태로 고정**.
    #   ▷ 새 술어 = 지워진 줄을 실제로 뽑아서 ⓐ 전부 오염 목록에 있는 이름이고 ⓑ 그 고유 이름 수가
    #     오염 건수와 같고 ⓒ 남은 장부가 비지 않았을 때만 통과. 중복 줄은 몇 벌이든 허용한다.
    #     통째 삭제(awk 실패)는 ⓑ에서 걸린다 = 260811 폭탄 차단 계약 그대로 유지.
    awk 'FNR==NR{o[$0]=1;next} ($0 in o)' "$TMPD/orphan" "$TMPD/seen.in" > "$TMPD/removed" 2>/dev/null
    RM=$(cnt "$TMPD/removed")
    RMU=$(sort -u "$TMPD/removed" 2>/dev/null | sed '/^$/d' | wc -l | tr -d ' ')
    [ -n "$RMU" ] || RMU=0
    if [ "$OUT" -gt 0 ] && [ "$RM" -gt 0 ] && [ "$RM" = "$((IN - OUT))" ] && [ "$RMU" = "$ON" ]; then
      mv "$TMPD/seen.out" "$SEEN"
      echo "  ♻ ${ON}건을 장부에서 빼서 다시 받게 했다(장부 ${IN}→${OUT}줄 · 백업 = $SEEN.bak):"
      [ "$RM" -gt "$ON" ] && echo "     (같은 파일이 장부에 여러 번 적혀 있어 ${RM}줄이 빠졌다 — 정상)"
      sed 's|^|     · |' "$TMPD/orphan"
    else
      echo "  ⚠ 회수 건너뜀 — 지워질 줄 ${RM}(고유 ${RMU}) 이 오염 ${ON}건과 안 맞는다. 원본 그대로 둔다."
    fi
  fi
fi

echo ""
echo "══════════ ③ 최신판 설치 ══════════"
mkdir -p "$HOME/.termux/tasker"
if curl -fsSL "$URL" -o "$SYNC.tmp" && [ -s "$SYNC.tmp" ] && head -1 "$SYNC.tmp" | grep -q '^#!'; then
  mv "$SYNC.tmp" "$SYNC"; chmod +x "$SYNC"
  echo "  ✅ 설치 완료 → $(grep -m1 '^VER=' "$SYNC")"
else
  rm -f "$SYNC.tmp"
  echo "  ❌ 내려받기 실패 — 종전 스크립트 그대로 살아 있다(악화 0). 회선 확인 후 다시."
  exit 1
fi

echo ""
echo "══════════ ④ 지금 한 번 돌린다 ══════════"
# 다음 번엔 긴 주소를 다시 붙여넣지 않아도 되게 이 진단기를 폰에 남긴다
# (260811 실사고 = 붙여넣기 신호문자가 `[200~curl … | sh~`로 명령을 깨뜨렸다 · 짧을수록 안전)
# ⚠ 제자리 덮어쓰기 금지 = 임시본 → mv(260831 실사고 봉합).
#   실사고 = `sh ~/dsfix` 로 돌리는 중에 이 줄이 **실행 중인 그 파일 자신**을 제자리에서 덮어썼다.
#   셸은 스크립트를 통째로 안 읽고 바이트 자리를 들고 이어 읽으므로, 내용이 그 자리에서 바뀌면
#   남은 부분을 문장 중간부터 읽는다 → `158: Syntax error: Unterminated quoted string`.
#   ⚠ 확정 증거 = 실행 중이던 판은 **150줄**인데 오류가 난 줄은 **158** = 그 파일에 없는 줄이고,
#     새로 받은 판이 157줄이다(양쪽 다 문법 검사 통과 = 코드 결함이 아니라 갈아치우기 사고).
#   ▷ mv 는 이름만 바꿔 다는 것이라 원래 알맹이가 그대로 살아 있다 → 돌던 셸은 끝까지 옛 판을
#     읽고, 다음 실행부터 새 판이 돈다. 정본 문법 = drive-gallery-sync.sh 자가 갱신($0.new → mv).
curl -fsSL --max-time 30 "https://raw.githubusercontent.com/nomutefb/editor/main/docs/drivesync-fix.sh" -o "$HOME/dsfix.new" 2>/dev/null \
  && [ -s "$HOME/dsfix.new" ] && head -1 "$HOME/dsfix.new" | grep -q '^#!' \
  && [ "$(tail -1 "$HOME/dsfix.new")" = "exit 0" ] \
  && { mv "$HOME/dsfix.new" "$HOME/dsfix"; chmod +x "$HOME/dsfix"; echo "  ℹ 다음부터는 짧게:  sh ~/dsfix"; }
rm -f "$HOME/dsfix.new"
rm -f "$HOME/.drivesync.last"
sh "$SYNC"
echo "  실행 끝 · 남은 배치: $(cnt "$NEW")건 / 못 받은 것: $(cnt "$MISS")건"
rm -rf "$TMPD"
echo ""
echo "이제부터 실패 알림은 진짜 실패한 파일 이름과 사유를 둘째 줄에 달고 온다."
echo "장부: $SEEN · 로그: $LOG · 격리: $STUCK"
exit 0
