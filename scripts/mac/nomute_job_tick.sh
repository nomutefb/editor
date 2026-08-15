#!/usr/bin/env bash
# 노뮤트 잡 틱(260815 코워크) — 제작 잡 전용 1분 레인(launchd com.nomute.jobworker).
# 배경: 5분 레인(com.nomute.cloudaction)은 요약 분석 회차가 15~50분 — 워커가 회차 끝에만 돌아
#       썸네일 합성(실작업 10초)이 큐에서 12분+ 대기하던 실측(260815 07:29 잡) 봉합.
# 구성: 잡워커(전용 사본 ~/nomute-worker) → 재배포기(사본 나무 기준).
#       두 스크립트 모두 자체 잠금 보유 = run.sh 후크와 겹쳐 불려도 동시 실행 0(늦은 쪽이 조용히 양보).
set -u
export PATH="/usr/bin:/opt/homebrew/bin:/opt/homebrew/opt/coreutils/libexec/gnubin:$PATH"
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8   # 260815 cowork: launchd python heredoc UTF-8 SyntaxError seal (chan-brief digest / check_refs axis)
date '+%F %T' > "$HOME/.nomute_job_tick_last" 2>/dev/null || true
L="$HOME/job_tick.log"
if [ -f "$L" ] && [ "$(/usr/bin/stat -f %z "$L" 2>/dev/null || echo 0)" -gt 400000 ]; then
  tail -c 200000 "$L" > "$L.t" 2>/dev/null && mv "$L.t" "$L"
fi
# 서브폴(260815) — 60초 틱 안에서 10초 간격 큐 확인 = 픽업 지연 최대 ~10초(깃액션 러너 부팅 5~30초보다 빠름).
# 비용: R2 LIST 6회/분 ≈ 26만/월 — 무료 한도(Class A 100만/월) 내. 빈 큐 1회 확인 ≈ 0.5초(env grep+LIST뿐).
END=$((SECONDS+50))
while :; do
  bash "$HOME/nomute_job_worker.sh" >> "$L" 2>&1 || true
  # 잡이 재배포 깃발을 세웠으면 서브폴 꼬리(최대 50초)를 기다리지 말고 즉시 배포로 — 접수→화면 지연 단축(260815 2차).
  [ -f "$HOME/.nomute_need_deploy" ] && break
  [ "$SECONDS" -ge "$END" ] && break
  sleep 10
done
# R2 미러도 1분 레인에 편승(260815) — 수집(candidates)이 회차 끝(최장 50분)이 아니라 스크랩 착지 직후 화면에 반영.
# md5 스탬프라 변화 없으면 업로드 0 · 무변화 회차(up=0 fail=0)는 로그도 남기지 않는다.
MO=$(bash "$HOME/nomute_r2_mirror.sh" 2>&1) || true
case "$MO" in *"up=0 skip="*"fail=0"*) : ;; *) printf '%s\n' "$MO" >> "$L" ;; esac
# 코드 푸시 실시간 반영(260815 2차 코워크) — 원격 main 머리 이동 감지 → 화면 자산(코드) 변경분이면 재배포 깃발.
#   봇 데이터 커밋(수집·판정·산출)은 기존 축(미러·잡 깃발·run.sh 후크)이 처리 = 여기선 코드 경로만 본다.
#   비용: git ls-remote 1회/분 · 머리 이동 시에만 fetch+diff. 스팬 diff 실패(얕은 경계) = fail-open 배포(무해).
CH="$HOME/.nomute_code_head"
RH=$(cd "$HOME/nomute-worker" && git ls-remote -q origin main 2>/dev/null | cut -f1)
if [ -n "$RH" ]; then
  LH=$(cat "$CH" 2>/dev/null || echo "")
  if [ "$RH" != "$LH" ]; then
    if [ -n "$LH" ]; then
      D=$(cd "$HOME/nomute-worker" && git fetch -q origin main 2>/dev/null; git diff --name-only "$LH" "$RH" 2>/dev/null); drc=$?
      if [ "$drc" -ne 0 ] || printf '%s\n' "$D" | grep -qE '^functions/|^_headers$|^_redirects$|^package\.json$|^wrangler\.toml$|^viewer/[^/]+\.(html|js|css)$'; then
        touch "$HOME/.nomute_need_deploy"
        echo "[code] $(date '+%H:%M:%S') 코드 푸시 감지(${LH:0:9}..${RH:0:9}) → 재배포 깃발" >> "$L"
      fi
    fi
    echo "$RH" > "$CH"
  fi
fi
NOMUTE_DEPLOY_REPO="$HOME/nomute-worker" bash "$HOME/nomute_backup_deploy.sh" >> "$L" 2>&1 || true
bash "$HOME/nomute_home_deploy.sh" >> "$L" 2>&1 || true   # nomute.kr hourly rebuild (260815 cowork)
( bash "$HOME/nomute_analyze_tick.sh" >> "$L" 2>&1 & )   # pending/asks instant consume (260815 cowork - summary queue delay seal)
exit 0
