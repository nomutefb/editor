#!/usr/bin/env bash
# 노뮤트 잡 틱(260815 코워크) — 제작 잡 전용 1분 레인(launchd com.nomute.jobworker).
# 배경: 5분 레인(com.nomute.cloudaction)은 요약 분석 회차가 15~50분 — 워커가 회차 끝에만 돌아
#       썸네일 합성(실작업 10초)이 큐에서 12분+ 대기하던 실측(260815 07:29 잡) 봉합.
# 구성: 잡워커(전용 사본 ~/nomute-worker) → 분석 틱.
#   (260929 운영자 «c로 하고») 깃허브 정지(260814~15) 비상 우회 = 맥 직접 배포(backup_deploy)·홈페이지 배포(home_deploy)·
#   R2 미러(r2_mirror)와 그 재배포 깃발 대기·코드 푸시 감지를 이 틱에서 뺐다 — 세 파일은 맥에 설치돼 있지 않아 1분마다
#   「파일 없음」만 남기고 있었다. 깃발(~/.nomute_need_deploy)은 소비자(backup_deploy)가 없으면 한 번 선 뒤 지워지지 않아
#   그 깃발 대기(break)가 서브폴을 매 틱 첫 회차에서 끊는다(픽업 지연 10초 → 최대 60초) → 대기 줄도 같이 뺐다. 되살리기 = Git 이력(260815 판).
#       두 스크립트 모두 자체 잠금 보유 = run.sh 후크와 겹쳐 불려도 동시 실행 0(늦은 쪽이 조용히 양보).
set -u
export PATH="/usr/bin:/opt/homebrew/bin:/opt/homebrew/opt/coreutils/libexec/gnubin:$PATH"
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8   # 260815 cowork: launchd python heredoc UTF-8 SyntaxError seal (chan-brief digest / check_refs axis)
date '+%F %T' > "$HOME/.nomute_job_tick_last" 2>/dev/null || true
L="$HOME/job_tick.log"
if [ -f "$L" ] && [ "$(/usr/bin/stat -f %z "$L" 2>/dev/null || echo 0)" -gt 400000 ]; then
  tail -c 200000 "$L" > "$L.t" 2>/dev/null && mv "$L.t" "$L"
fi
# 자기갱신(260815 밤 코워크) — 깃 정본 scripts/mac/*.sh → ~/ 설치본을 이 틱에서 맞춘다.
#   신설 사유: scripts/mac/README.md 가 14:20 정본화에서 「1분 틱이 자동 배포」라 선언했는데 그 배선이
#   실제로 없었다(grep 0건) → 그날 수정이 전부 ~/ 에만 쌓여 6종이 갈렸고 CT 매핑 봉합은 이 맥 한 대에만
#   존재했다. 게이트 = 설치 전 /bin/bash -n(레인이 도는 3.2 로 잰다 · 깨진 판 푸시가 레인을 못 죽인다),
#   설치 = 원자 교체(제자리 덮어쓰기는 돌고 있는 스크립트를 죽인다 · 19:41 실사고), 덮기 전 전량 백업.
# 정본 사본 당겨오기(260929) — 자기갱신은 ~/nomute-editor 를 읽기만 하는데 그 사본을 당기는 배선이 없었다
#   (실측 260929 = 5분 레인 정지 후 맥 ys 드라이버가 저장소 수정을 영영 못 받음 · 잡워커의 pull 은 ~/nomute-worker 몫).
#   5분에 1번 · 빨리감기만(--ff-only = 로컬 수정이 있으면 멈춘다 · 덮어쓰기 0) · 90초 상한(느린 회선 20초 끊김) · 무인 프롬프트 0
#   · 5분 레인이 도는 중(잠금)이면 양보(같은 작업나무 두 기록자 = 인덱스 경합 0) · 실패는 rc 한 줄만 남기고 레인은 계속.
if [ -d "$HOME/nomute-editor/.git" ] && [ ! -d "$HOME/.nomute_pc_lane.lock" ]; then
  PS="$HOME/.nomute_editor_pull"
  t=$(cat "$PS" 2>/dev/null); case "$t" in ''|*[!0-9]*) t=0;; esac
  if [ $(( $(date +%s) - t )) -ge 300 ]; then
    date +%s > "$PS" 2>/dev/null
    G="git -c http.lowSpeedLimit=1000 -c http.lowSpeedTime=20 pull --ff-only -q origin main"
    if command -v timeout >/dev/null 2>&1; then ( cd "$HOME/nomute-editor" && GIT_TERMINAL_PROMPT=0 timeout 90 $G ) >/dev/null 2>&1
    else ( cd "$HOME/nomute-editor" && GIT_TERMINAL_PROMPT=0 $G ) >/dev/null 2>&1; fi
    prc=$?; [ "$prc" -eq 0 ] || echo "[pull] $(date '+%H:%M:%S') ~/nomute-editor 당겨오기 실패 rc=$prc(로컬 수정·갈라짐·망 — git -C ~/nomute-editor status 확인)" >> "$L"
  fi
fi
[ -f "$HOME/nomute_self_update.sh" ] || cp -f "$HOME/nomute-editor/scripts/mac/nomute_self_update.sh" "$HOME/nomute_self_update.sh" 2>/dev/null
bash "$HOME/nomute_self_update.sh" >> "$L" 2>&1 || true
# 서브폴(260815) — 60초 틱 안에서 10초 간격 큐 확인 = 픽업 지연 최대 ~10초(깃액션 러너 부팅 5~30초보다 빠름).
# 비용: R2 LIST 6회/분 ≈ 26만/월 — 무료 한도(Class A 100만/월) 내. 빈 큐 1회 확인 ≈ 0.5초(env grep+LIST뿐).
END=$((SECONDS+50))
while :; do
  bash "$HOME/nomute_job_worker.sh" >> "$L" 2>&1 || true
  [ "$SECONDS" -ge "$END" ] && break
  sleep 10
done
bash "$HOME/nomute_analyze_tick.sh" >> "$L" 2>&1 || true   # pending/asks instant consume (260815 - foreground: launchd kills orphaned bg children)
exit 0
