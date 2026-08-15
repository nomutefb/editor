#!/usr/bin/env bash
# 노뮤트 클라우드 액션 실행기(맥) — 260814 밤 확장판(코워크 세션 작성).
# 문제: launchd(백그라운드) bash 는 ~/Library/CloudStorage(구글 드라이브) 접근이 macOS 프라이버시(TCC)에
#       막힌다(실측 = cloud_action.log line 87/110/112 「Operation not permitted」 28회 · 260814 22:00 지속).
#       → 시계 회차는 환경변수(키) 주입·상태 미러가 전부 빠진 채 돌았다.
# 조치: 로컬 우체통 ~/nomute-action 캐시.
#   ① 드라이브가 읽히면 정본→캐시 갱신 · 직접 읽기가 막히면 zsh 대리(cp) 시도
#      (같은 맥의 com.local.gdrive-autosync = launchd+zsh 가 드라이브 쓰기 성공해 온 실측 — zsh 만 TCC 승인 가능성).
#   ② 레인은 항상 캐시(NOMUTE_ACTION_DIR)로 돈다 — 캐시가 한 번 씨앗되면 키 주입이 회차마다 보장.
#   ③ 회차 후 상태·로그를 드라이브로 미러(직접 → zsh 대리 → 포기 · 실패해도 레인은 정상 = fail-soft).
# 정본 스크립트(scripts/cloud_action.sh)는 손대지 않는다 — 이 파일은 설치 산출물(레포 밖).
export PATH="/usr/bin:/opt/homebrew/bin:/opt/homebrew/opt/coreutils/libexec/gnubin:$PATH"
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8   # 260815 cowork: launchd python heredoc UTF-8 SyntaxError seal (chan-brief digest / check_refs axis)
# ↑ gnubin = GNU coreutils(timeout 등). 맥에 timeout 이 없어 재난트렌드·감시 스테이지가
#   FAIL127(command not found)로 죽던 것 실측 봉합(260815 코워크). /usr/bin 뒤라 시스템 도구는 안 가림.
DRIVE_AD="/Users/hwang/Library/CloudStorage/GoogleDrive-ems1130g@gmail.com/내 드라이브/action"
LOCAL_AD="$HOME/nomute-action"
mkdir -p "$LOCAL_AD/상태" "$LOCAL_AD/logs" 2>/dev/null || true

_pull=skip
if head -c 1 "$DRIVE_AD/환경변수.txt" >/dev/null 2>&1; then
  cp -f "$DRIVE_AD/환경변수.txt" "$LOCAL_AD/" 2>/dev/null && _pull=direct
  cp -f "$DRIVE_AD/계정.txt" "$LOCAL_AD/" 2>/dev/null || true
elif /bin/zsh -c "cp -f '$DRIVE_AD/환경변수.txt' '$LOCAL_AD/' && cp -f '$DRIVE_AD/계정.txt' '$LOCAL_AD/'" 2>/dev/null; then
  _pull=zsh
fi
echo "[run] $(date '+%H:%M:%S') env-sync=$_pull cache-keys=$(grep -c '^[A-Za-z_]*=' "$LOCAL_AD/환경변수.txt" 2>/dev/null || echo 0)"

# R2 픽 큐 스위퍼(260815) — 뷰어 픽의 R2 착지분을 pending/ 으로 커밋(레인 시작 전 = 이번 회차가 바로 분석)
bash "$HOME/nomute_r2_queue.sh" >> "$HOME/r2_mirror.log" 2>&1 || true

export NOMUTE_ACTION_DIR="$LOCAL_AD"
bash "$HOME/nomute-editor/scripts/cloud_action.sh"
rc=$?

_push=skip
if cp -f "$LOCAL_AD/상태/"*.txt "$DRIVE_AD/상태/" 2>/dev/null; then _push=direct
elif /bin/zsh -c "cp -f '$LOCAL_AD/상태/'*.txt '$DRIVE_AD/상태/'" 2>/dev/null; then _push=zsh
fi
cp -f "$LOCAL_AD/logs/"*.txt "$DRIVE_AD/logs/" 2>/dev/null \
  || /bin/zsh -c "cp -f '$LOCAL_AD/logs/'*.txt '$DRIVE_AD/logs/'" 2>/dev/null || true
echo "[run] $(date '+%H:%M:%S') mirror=$_push rc=$rc"
# 2단 백업 1탄(260814) — 화면 JSON을 R2 live/ 로 미러(깃허브 무풍 데이터 통로 · 실패해도 레인 정상)
bash "$HOME/nomute_r2_mirror.sh" >> "$HOME/r2_mirror.log" 2>&1 || true
# 잡 워커(260815) — 뷰어 제작 요청(R2 queue/jobs/) 실행: v1 = genimg(사진)·compose(합성) · 회차당 2잡
bash "$HOME/nomute_job_worker.sh" >> "$HOME/r2_mirror.log" 2>&1 || true
# 화면 재배포기(260815 개정) — 제작 산출 깃발 즉시 or 수집함 변화 10분 스로틀 · 정본 nomute-editor 직접 업로드
bash "$HOME/nomute_backup_deploy.sh" >> "$HOME/r2_mirror.log" 2>&1 || true
if [ "$(wc -c < "$HOME/r2_mirror.log" 2>/dev/null || echo 0)" -gt 500000 ]; then
  tail -n 500 "$HOME/r2_mirror.log" > "$HOME/r2_mirror.log.t" 2>/dev/null && mv "$HOME/r2_mirror.log.t" "$HOME/r2_mirror.log" 2>/dev/null || true
fi
exit $rc
