#!/data/data/com.termux/files/usr/bin/sh
# 드라이브 → 갤러리 다운싱크 (v1.6 · 정본 실물 — 문서 미러 = 드라이브싱크 플레이북 §1)
# 설치(폰 한 줄): curl -fsSL https://raw.githubusercontent.com/muteno/nomute-editor/main/docs/drive-gallery-sync.sh -o ~/.termux/tasker/drive-gallery-sync.sh && chmod +x ~/.termux/tasker/drive-gallery-sync.sh
#
# ── v1.6 (2026-08-11) = 「계속 실패」 4중 봉합 ─────────────────────────────────
# 실사고 260811 22:39 = 「드라이브싱크 실패 ⚠️ / [10:39 PM] 2026-08-11 21 19 06.jpg 외 10건」이
#   3분 틱마다 무한 반복. 목록 조회(lsf)는 성공했으니 인증·회선은 산 상태 = copy 분기 실패인데,
#   운영자에게 도달한 정보가 「파일명 하나」뿐이라 원인 판별이 원리적으로 불가능했다. 구조 결함 4종:
#   ⓐ **사유가 알림에 0자** — rclone이 뱉은 실패 이유는 $LOG 안에만 있고 알림엔 한 글자도 안 실린다.
#      (= watchdog 스모크 경보 봉합과 같은 축 = 「경보는 사유를 갖고 나간다」)
#   ⓑ **지목한 파일이 범인이 아니다** — 구판 DF=`head -1 "$NEW"` = 이번 배치 **첫 줄**이라
#      11건 중 뒤쪽 1건이 실패해도 무관한 첫 파일 이름이 뜬다 = 진단을 반대로 몬다.
#   ⓒ **부분 성공이 통째로 버려진다** — rclone은 1건만 실패해도 rc≠0이라 성공한 10건까지
#      SEEN 미등록 → 다음 틱이 같은 11건을 통째 재시도 → **영구 루프**(= "계속 실패"의 실체).
#   ⓓ **영구 실패 파일 격리 0** — 원격에서 사라진 파일·안드로이드가 못 쓰는 파일명이 하나 끼면
#      그 배치는 영원히 rc≠0이라 알림이 죽을 때까지 3분마다 울린다.
#   → ⓐ 이번 실행분 로그에서 사유를 뽑아 알림 둘째 줄에 싣는다(**fail-closed 3단 사다리** =
#        ERROR 줄 → 로그 꼬리 줄 → 「미확인」 명시 · 빈 사유로 나가는 경로 0)
#     ⓑ 실패 파일 = 「로컬에 안 떨어진 것」 **실측**(rclone 로그 형식 의존 0)
#     ⓒ 도착분만 SEEN 등록 → 배치가 매 틱 쪼그라들고 남는 건 진짜 못 받은 것뿐
#     ⓓ 같은 파일 STUCK_N회 연속 실패 = 격리(SEEN 등록 + `~/.drivesync.stuck` 원장 + 알림에 이름 명시)
#   ⚠ SEEN 등록은 여전히 **실제 도착을 확인한 뒤에만** 한다(260702·260719 SEEN 오염 교훈 = 낙관 기록 0).
#   ⚠ 격리는 **조용한 실종이 아니다** — 알림이 그 파일 이름을 대고 원장에 사유까지 남긴다.
#      되살리려면 `~/.drivesync.seen`에서 그 줄을 지운다(문서 §6).
REMOTE="gdrive:Shared"
LOCAL="/sdcard/Pictures/DriveSync"
SEEN="$HOME/.drivesync.seen"
NOW="$HOME/.drivesync.now"
NEW="$HOME/.drivesync.new"
MISS="$HOME/.drivesync.miss"
LOG="$HOME/.drivesync.log"
STAMP="$HOME/.drivesync.last"
FAILC="$HOME/.drivesync.lsffail"
CPFAIL="$HOME/.drivesync.copyfail"
STUCK="$HOME/.drivesync.stuck"
STUCK_N=10
VER="v1.6"
T=$(date +%s)
if [ -f "$STAMP" ] && [ $((T - $(cat "$STAMP"))) -lt 120 ]; then exit 0; fi
echo "$T" > "$STAMP"
echo "$VER" > "$HOME/.drivesync.ver"
mkdir -p "$LOCAL"; touch "$SEEN"
[ -s "$SEEN" ] || echo "__init__" > "$SEEN"
if ! rclone lsf -R --files-only --contimeout 15s --timeout 60s --exclude "*.app/**" "$REMOTE" > "$NOW" 2>>"$LOG"; then
  N=$(($(cat "$FAILC" 2>/dev/null || echo 0) + 1)); echo "$N" > "$FAILC"
  if [ "$N" -ge 3 ]; then
    termux-notification --id drivesync-fail -t "드라이브싱크 실패 ⚠️" \
      -c "$(TZ='Asia/Seoul' date '+[%I:%M %p]') 드라이브 연결 실패 ${N}회 연속" 2>/dev/null || true
  fi
  exit 1
fi
rm -f "$FAILC"
awk 'FNR==NR{s[$0]=1;next} !($0 in s)' "$SEEN" "$NOW" > "$NEW"
if [ -s "$NEW" ]; then
  LOGSZ=0
  [ -f "$LOG" ] && LOGSZ=$(wc -c < "$LOG" 2>/dev/null | tr -d ' ')
  [ -n "$LOGSZ" ] || LOGSZ=0
  if rclone copy "$REMOTE" "$LOCAL" --files-from "$NEW" --inplace \
      --contimeout 15s --timeout 60s --transfers 4 --log-file "$LOG" --log-level INFO; then
    cat "$NEW" >> "$SEEN"
    rm -f "$CPFAIL"
  else
    # ⓒ 부분 성공 정산 — 로컬에 실제로 떨어진 것만 장부에 넣고, 안 온 것만 다음 틱 재시도
    : > "$MISS"
    while IFS= read -r f; do
      [ -n "$f" ] || continue
      if [ -s "$LOCAL/$f" ]; then
        printf '%s\n' "$f" >> "$SEEN"
      else
        printf '%s\n' "$f" >> "$MISS"
      fi
    done < "$NEW"
    DN=$(wc -l < "$MISS" 2>/dev/null | tr -d ' ')
    [ -n "$DN" ] || DN=0
    if [ "$DN" -gt 0 ]; then
      # ⓐ 사유 = 이번 실행분 로그 꼬리(fail-closed 3단 · 빈 사유로 나가는 경로 0)
      TL=$(tail -c "+$((LOGSZ + 1))" "$LOG" 2>/dev/null)
      RSN=$(printf '%s\n' "$TL" | grep -m1 -E 'ERROR|Failed to copy|Fatal error' | sed 's|^[0-9][0-9/:. -]*||')
      [ -z "$RSN" ] && RSN=$(printf '%s\n' "$TL" | grep -v '^[[:space:]]*$' | tail -1 | sed 's|^[0-9][0-9/:. -]*||')
      [ -z "$RSN" ] && RSN="사유 미확인 — 로그: ~/.drivesync.log"
      RSN=$(printf '%s' "$RSN" | cut -c1-160)
      # ⓑ 실패 파일 = 안 온 것 실측(배치 첫 줄 아님) + 같은 파일 연속 회차
      DF=$(head -1 "$MISS")
      N=1
      if [ -f "$CPFAIL" ]; then
        OF=$(sed -n 1p "$CPFAIL")
        OC=$(sed -n 2p "$CPFAIL")
        [ "$OF" = "$DF" ] && N=$(( ${OC:-0} + 1 ))
      fi
      printf '%s\n%s\n' "$DF" "$N" > "$CPFAIL"
      if [ "$N" -ge "$STUCK_N" ]; then
        # ⓓ 격리 — 이 한 파일이 배치 전체를 영원히 물고 있는 상태를 끊는다(이름·사유는 남긴다)
        printf '%s\t%s\t%s\n' "$(TZ='Asia/Seoul' date '+%F %T')" "$DF" "$RSN" >> "$STUCK"
        printf '%s\n' "$DF" >> "$SEEN"
        rm -f "$CPFAIL"
        DM="$DF — ${STUCK_N}회 실패로 건너뜀(목록 ~/.drivesync.stuck)"
      else
        DM="$DF"
        [ "$DN" -gt 1 ] && DM="$DF 외 $((DN - 1))건"
        [ "$N" -gt 1 ] && DM="$DM · ${N}회째"
      fi
      termux-notification --id drivesync-fail -t "드라이브싱크 실패 ⚠️" \
        -c "$(TZ='Asia/Seoul' date '+[%I:%M %p]') $DM
$RSN" 2>/dev/null || true
    else
      # 파일은 전부 도착했는데 rc만 실패 = 사용자에겐 결손 0 → 알림 대신 로그에만(가짜 빨강 방지)
      rm -f "$CPFAIL"
      echo "$(TZ='Asia/Seoul' date '+%F %T') NOTE: rclone rc!=0 but all files landed" >> "$LOG"
    fi
  fi
  termux-media-scan -r "$LOCAL"
fi
[ -x "$HOME/.termux/tasker/drive-camera-up.sh" ] && sh "$HOME/.termux/tasker/drive-camera-up.sh"
exit 0
