#!/data/data/com.termux/files/usr/bin/sh
# 갤러리 → 드라이브 역방향 업로드 (v1.3 · 정본 실물 — 문서 미러 = 드라이브싱크 플레이북 §1-b)
# 설치(폰 한 줄): curl -fsSL https://raw.githubusercontent.com/muteno/nomute-editor/main/docs/drive-camera-up.sh -o ~/.termux/tasker/drive-camera-up.sh && chmod +x ~/.termux/tasker/drive-camera-up.sh
# ── 알림 문구 칸(운영자 조정 — 타이틀은 이 두 변수 · 내용 문구는 아래 -c 줄) ──
T_BASE="갤러리 업로드 기준선 설정 ✅"
T_UPFAIL="업로드 실패"
# ── 동기화 제외 칸(운영자 260811 "저런 압축파일은 동기화 안되게 조치해도됨 · 양방향 모두") ──
#   묶음 파일은 갤러리에 갈 이유가 0이고, 실제로 260811 사고의 진범이 드라이브 웹의
#   「여러 개 한꺼번에 받기」 산출물 `drive-download-*.zip`이었다(256M 초과 → 갈래받기 발동).
#   ⚠ **셸 축으로 거른다**(rclone `--exclude` 아님) = `--files-from` 목록을 주는 순간 rclone 필터는
#   우회되므로 목록을 만드는 자리에서 빼야 양쪽 다 확실하다.
#   ⚠ 짝 = `drive-gallery-sync.sh`의 `EXC_RE` **동값 유지**(한쪽만 고치면 반대 방향이 조용히 샌다).
#   늘리려면 이 한 줄에 확장자만 추가(대소문자는 -i가 흡수).
EXC_RE='\.(zip|rar|7z|tar|gz|tgz|bz2|xz|zst|iso|dmg|apk|exe)$'
REMOTE_BASE="gdrive:Shared"
SRCS="/sdcard/DCIM/Camera /sdcard/DCIM/Screenshots /sdcard/Pictures/Screenshots"
WIFI_ONLY=0
UPSEEN="$HOME/.driveup.seen"
DSEEN="$HOME/.drivesync.seen"
UNOW="$HOME/.driveup.now"
UNEW="$HOME/.driveup.new"
LOG="$HOME/.driveup.log"
STAMP="$HOME/.driveup.last"
LOCK="$HOME/.driveup.lock"
T=$(date +%s)
if [ -f "$STAMP" ] && [ $((T - $(cat "$STAMP"))) -lt 120 ]; then exit 0; fi
echo "$T" > "$STAMP"
if ! mkdir "$LOCK" 2>/dev/null; then
  A=$((T - $(stat -c %Y "$LOCK" 2>/dev/null || echo 0)))
  [ "$A" -lt 7200 ] && exit 0
  rmdir "$LOCK" 2>/dev/null; mkdir "$LOCK" 2>/dev/null || exit 0
fi
trap 'rmdir "$LOCK" 2>/dev/null' EXIT
: > "$UNOW"
for SRC in $SRCS; do
  [ -d "$SRC" ] || continue
  ls "$SRC" | while IFS= read -r f; do
    [ -f "$SRC/$f" ] && printf '%s\n' "$SRC/$f"
  done >> "$UNOW"
done
grep -viE "$EXC_RE" "$UNOW" > "$UNOW.f" 2>/dev/null; mv "$UNOW.f" "$UNOW"   # 묶음 파일 제외(위 제외 칸)
[ -s "$UNOW" ] || exit 0
if [ ! -s "$UPSEEN" ]; then
  cp "$UNOW" "$UPSEEN"
  termux-notification --id driveup -t "$T_BASE" \
    -c "지금부터 새로 생기는 사진·영상만 드라이브로 올라감" 2>/dev/null || true
  exit 0
fi
awk 'FNR==NR{s[$0]=1;next} !($0 in s)' "$UPSEEN" "$UNOW" > "$UNEW"
[ -s "$UNEW" ] || exit 0
if [ "$WIFI_ONLY" = 1 ]; then
  termux-wifi-connectioninfo 2>/dev/null | grep -q '"supplicant_state": "COMPLETED"' || exit 0
fi
FAIL=0
FAILN=0
FAILF=""
for SRC in $SRCS; do
  [ -d "$SRC" ] || continue
  grep "^$SRC/" "$UNEW" | sed "s|^$SRC/||" > "$UNEW.d"
  [ -s "$UNEW.d" ] || continue
  cat "$UNEW.d" >> "$DSEEN"
  if rclone copy "$SRC" "$REMOTE_BASE" --files-from "$UNEW.d" --inplace \
      --transfers 2 --log-file "$LOG" --log-level INFO; then
    sed "s|^|$SRC/|" "$UNEW.d" >> "$UPSEEN"
  else
    FAIL=1
    FAILN=$((FAILN + $(wc -l < "$UNEW.d")))
    [ -z "$FAILF" ] && FAILF=$(head -1 "$UNEW.d")
  fi
done
if [ "$FAIL" = 1 ]; then
  FM="$FAILF"
  [ "$FAILN" -gt 1 ] && FM="$FAILF 외 $((FAILN-1))건"
  termux-notification --id driveup-fail -t "$T_UPFAIL" \
    -c "$(TZ='Asia/Seoul' date '+[%I:%M %p]') $FM" 2>/dev/null || true
fi
exit 0
