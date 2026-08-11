#!/data/data/com.termux/files/usr/bin/sh
# 드라이브싱크 자가진단 + v1.6 설치 1발 (운영자 260811 "계속 실패하는데 이유를 모르겠네")
#
# ▷ 폰 Termux에서 한 줄:
#     curl -fsSL https://raw.githubusercontent.com/muteno/nomute-editor/main/docs/drivesync-fix.sh | sh
#
# ▷ 하는 일 = 3단(전부 읽기 전용 진단 뒤 설치 · 파일 삭제·장부 리셋 0)
#   ① 지금 왜 실패하는지 그 자리에서 출력(버전·마지막 실행·연결 생사·로그의 진짜 실패 줄·미도착 파일·저장공간)
#   ② 다운싱크 v1.6 설치(사유 동봉 + 실패 파일 실측 지목 + 부분 성공 정산 + 10회 격리)
#   ③ 디바운스 풀고 1회 실행 → 밀린 배치를 그 자리에서 정산
#
# ▷ 안전: SEEN·파일 삭제 0 · rclone 설정 무접촉 · 실패해도 종전 동작 그대로(스크립트만 갈아끼움).
# ▷ 끄는 법: 종전 v1.5로 되돌리려면 `git -C ~/nomute-editor show <구커밋>:docs/drive-gallery-sync.sh` 로 덮어쓰기.
SYNC="$HOME/.termux/tasker/drive-gallery-sync.sh"
LOG="$HOME/.drivesync.log"
SEEN="$HOME/.drivesync.seen"
NEW="$HOME/.drivesync.new"
MISS="$HOME/.drivesync.miss"
STUCK="$HOME/.drivesync.stuck"
LOCAL="/sdcard/Pictures/DriveSync"
URL="https://raw.githubusercontent.com/muteno/nomute-editor/main/docs/drive-gallery-sync.sh"

echo "══════════ ① 지금 상태 ══════════"
printf '설치된 판 : %s\n' "$(cat "$HOME/.drivesync.ver" 2>/dev/null || echo '표기 없음(v1.3 이하)')"
if [ -f "$HOME/.drivesync.last" ]; then
  printf '마지막 실행: %s분 전\n' "$(( ($(date +%s) - $(cat "$HOME/.drivesync.last")) / 60 ))"
else
  printf '마지막 실행: 기록 없음(Tasker가 안 쏘는 중일 수 있다)\n'
fi
printf '이번 배치  : %s건 대기\n' "$(wc -l < "$NEW" 2>/dev/null | tr -d ' ' || echo 0)"

echo "── 드라이브 연결(목록 조회) ──"
if rclone lsf --contimeout 15s --timeout 60s gdrive: >/dev/null 2>&1; then
  echo "  ✅ 연결·인증 정상 → 범인은 받기(copy) 한 자리"
else
  echo "  ❌ 목록 조회부터 실패 = 인증·회선 축 → rclone config reconnect gdrive:"
fi

echo "── 로그가 말하는 진짜 실패 사유(최근 5줄) ──"
grep -E 'ERROR|Failed to copy|Fatal error' "$LOG" 2>/dev/null | tail -5 | sed 's|^|  |'
[ -s "$LOG" ] || echo "  (로그 없음)"
grep -qE 'ERROR|Failed to copy|Fatal error' "$LOG" 2>/dev/null || echo "  (실패 줄 없음 — 로그 꼬리: $(tail -1 "$LOG" 2>/dev/null))"

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
[ -s "$STUCK" ] && { echo "── 격리된 파일(10회 실패) ──"; tail -5 "$STUCK" | sed 's|^|  |'; }

echo "── 저장 공간 ──"
df -h /sdcard 2>/dev/null | tail -1 | sed 's|^|  |'

echo ""
echo "══════════ ② v1.6 설치 ══════════"
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
echo "══════════ ③ 지금 한 번 돌린다 ══════════"
rm -f "$HOME/.drivesync.last"
sh "$SYNC"
echo "  실행 끝 · 남은 배치: $(wc -l < "$NEW" 2>/dev/null | tr -d ' ' || echo 0)건 / 못 받은 것: $(wc -l < "$MISS" 2>/dev/null | tr -d ' ' || echo 0)건"
echo ""
echo "이제부터 실패 알림은 **진짜 실패한 파일 이름 + rclone 사유**를 둘째 줄에 달고 온다."
echo "장부: $SEEN · 로그: $LOG · 격리: $STUCK"
exit 0
