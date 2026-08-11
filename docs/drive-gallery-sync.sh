#!/data/data/com.termux/files/usr/bin/sh
# 드라이브 → 갤러리 다운싱크 (v1.9 · 정본 실물 — 문서 미러 = 드라이브싱크 플레이북 §1)
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
# ── v1.7 (2026-08-11) = 진범 봉합 · 큰 파일 갈래받기 비활성 ────────────────────
# v1.6이 사유를 싣자마자 로그가 진범을 그대로 뱉었다(운영자 실행 실측):
#   drive-download-20260811T121058Z-1-001.zip: Failed to copy:
#   multi-thread copy: failed to find object after copy: object not found
# ▷ 무슨 일인가 = rclone은 `--multi-thread-cutoff`(기본 **256M**)를 넘는 파일만 여러 갈래로
#   쪼개 동시에 받는다. 다 쓴 뒤 대상 객체를 다시 조회해 검증하는데, 안드로이드 `/sdcard`는
#   FUSE 에뮬레이트 계층이라 방금 쓴 파일의 즉시 조회가 어긋나 `object not found`로 죽는다.
# ▷ **「말짱한데 갑자기」의 정체** = 코드·설정·인증 전부 무변경이고 **입력이 바뀐 것**이다.
#   평소 사진·영상은 그 문턱 아래라 단일 스트림 경로로 조용히 잘 돌았고, 드라이브 웹의
#   「여러 개 한꺼번에 받기」 산출물(drive-download-*.zip)이 Shared에 올라온 순간
#   **그 파일 하나에만** 다른 코드 경로가 켜졌다 → 그날부터 배치 전체가 rc≠0.
# ▷ 처방 = `--multi-thread-streams 0`(공식 문서 = "Set to 0 to disable multi thread transfers").
#   ⚠ 대안 폐기 = `--multi-thread-cutoff` 상향은 문턱만 미루는 미봉이고(더 큰 파일에서 재발),
#   `--transfers`는 **파일 병렬 수**라 이 축과 무관하다(줄여도 갈래받기는 그대로 켜진다).
#   ⚠ 속도 손해 = 원격에서 큰 파일 하나를 받는 속도만 낮아진다. 폰 회선에선 체감 0에 가깝고,
#   「안 받아지는 것」보다 「조금 느린 것」이 싸다.
# ⚠ SEEN 오염 동반 점검 = 이 사고가 난 회차에 rclone이 최종 rc=0을 반환했다면 v1.5가 그 zip을
#   장부에 넣어버렸을 수 있다(= 영영 안 받아진다 · 260702·260719와 같은 병) →
#   회수는 `docs/drivesync-fix.sh`가 로그의 실패 파일명을 실측해 자동으로 한다.
# ── v1.9 (2026-08-11) = 자가 갱신 · 붙여넣기 깨짐을 코드가 흡수한다 ──────────────
# 실사고 = v1.8 배포를 폰에 넣으려고 준 curl 한 줄이 **터미널 붙여넣기 신호문자에 깨졌다**
#   (`~ $ [200~curl … | sh~` → `No command sh~ found` · 260719에 스크립트가 빈 파일로 깎였던
#   그 사고와 같은 축). 같은 명령이 직전 실행에선 멀쩡했으니 재현이 불확실하고,
#   **사람 손 붙여넣기를 배포 경로로 두는 한 이 사고는 계속 난다** = 코드로 흡수할 자리.
# ▷ 동작 = 하루 1회, 정본 raw를 받아 3중 검문(크기>0 · 첫 줄 `#!` · 마지막 줄 `exit 0`)을
#   통과하고 **내용이 실제로 다를 때만** 제자리 교체. 다음 틱(3분)부터 새 판이 돈다.
#   ⚠ 그 자리에서 `exec` 재실행은 안 한다 — 방금 찍은 120초 디바운스에 걸려 어차피 즉시
#   종료라 이득이 0이고, 교체 직후 재실행은 「반쯤 바뀐 상태로 도는」 창을 만든다.
# ▷ 알림 = 갱신됐을 때 1장(`--id drivesync-up`). ⚠ 조용한 코드 교체는 금지 — 폰에서 도는
#   코드가 언제 바뀌었는지 운영자가 모르면 안 된다.
# ▷ 킬스위치 = `DS_SELFUP=0`(환경변수). 끄면 종전 동작 100%.
# ⚠ 신뢰 모델은 **종전과 동일**(curl 한 줄 설치가 이미 같은 원천을 믿는다) — 늘어난 건
#   「사람이 매번 붙여넣느냐」 하나뿐이다. 실패는 전부 fail-soft(받기 실패·검문 탈락 =
#   종전 스크립트 그대로 · 동기화 무손상).
SELF_URL="https://raw.githubusercontent.com/muteno/nomute-editor/main/docs/drive-gallery-sync.sh"
SELFUP="$HOME/.drivesync.selfup"
SELFUP_SEC=86400
# ── 동기화 제외 칸(운영자 260811 "저런 압축파일은 동기화 안되게 조치해도됨 · 양방향 모두") ──
#   묶음 파일은 갤러리에 갈 이유가 0이고, 실제로 260811 사고의 진범이 드라이브 웹의
#   「여러 개 한꺼번에 받기」 산출물 `drive-download-*.zip`이었다(256M 초과 → 갈래받기 발동).
#   ⚠ **셸 축으로 거른다**(rclone `--exclude` 아님) = `--files-from` 목록을 주는 순간 rclone 필터는
#   우회되므로 목록을 만드는 자리에서 빼야 양쪽 다 확실하다.
#   ⚠ 짝 = `drive-camera-up.sh`의 `EXC_RE` **동값 유지**(한쪽만 고치면 반대 방향이 조용히 샌다).
#   늘리려면 이 한 줄에 확장자만 추가(대소문자는 -i가 흡수).
EXC_RE='\.(zip|rar|7z|tar|gz|tgz|bz2|xz|zst|iso|dmg|apk|exe)$'
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
VER="v1.9"
T=$(date +%s)
if [ -f "$STAMP" ] && [ $((T - $(cat "$STAMP"))) -lt 120 ]; then exit 0; fi
echo "$T" > "$STAMP"
echo "$VER" > "$HOME/.drivesync.ver"
# ── 자가 갱신(하루 1회 · 3중 검문 · fail-soft · 위 v1.9 칸) ──
if [ "${DS_SELFUP:-1}" = 1 ] && [ -n "${0:-}" ] && [ -f "$0" ]; then
  LU=$(cat "$SELFUP" 2>/dev/null || echo 0)
  case "$LU" in *[!0-9]*|"") LU=0 ;; esac
  if [ $((T - LU)) -gt "$SELFUP_SEC" ]; then
    echo "$T" > "$SELFUP"
    if curl -fsSL --max-time 30 "$SELF_URL" -o "$0.new" 2>/dev/null \
       && [ -s "$0.new" ] \
       && head -1 "$0.new" | grep -q '^#!' \
       && [ "$(tail -1 "$0.new")" = "exit 0" ]; then
      if ! cmp -s "$0.new" "$0"; then
        NV=$(grep -m1 '^VER=' "$0.new" | cut -d'"' -f2)
        mv "$0.new" "$0" && chmod +x "$0"
        termux-notification --id drivesync-up -t "드라이브싱크 갱신됨" \
          -c "$(TZ='Asia/Seoul' date '+[%I:%M %p]') $VER → ${NV:-새 판} · 다음 회차부터 적용" 2>/dev/null || true
      fi
    fi
    rm -f "$0.new"
  fi
fi
mkdir -p "$LOCAL"; touch "$SEEN"
[ -s "$SEEN" ] || echo "__init__" > "$SEEN"
if ! rclone lsf -R --files-only --contimeout 15s --timeout 60s --exclude "*.app/**" "$REMOTE" > "$NOW.raw" 2>>"$LOG"; then
  N=$(($(cat "$FAILC" 2>/dev/null || echo 0) + 1)); echo "$N" > "$FAILC"
  if [ "$N" -ge 3 ]; then
    termux-notification --id drivesync-fail -t "드라이브싱크 실패 ⚠️" \
      -c "$(TZ='Asia/Seoul' date '+[%I:%M %p]') 드라이브 연결 실패 ${N}회 연속" 2>/dev/null || true
  fi
  exit 1
fi
rm -f "$FAILC"
grep -viE "$EXC_RE" "$NOW.raw" > "$NOW"   # 묶음 파일 제외(위 제외 칸)
awk 'FNR==NR{s[$0]=1;next} !($0 in s)' "$SEEN" "$NOW" > "$NEW"
if [ -s "$NEW" ]; then
  LOGSZ=0
  [ -f "$LOG" ] && LOGSZ=$(wc -c < "$LOG" 2>/dev/null | tr -d ' ')
  [ -n "$LOGSZ" ] || LOGSZ=0
  if rclone copy "$REMOTE" "$LOCAL" --files-from "$NEW" --inplace --multi-thread-streams 0 \
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
