#!/usr/bin/env bash
# 노뮤트 pending 즉시 소비 레인(260815 코워크) — 요약 대기열 지연 봉합.
# 배경: 5분 레인의 요약 스테이지(④)는 회차 맨 끝 + 잔여예산≥300s 조건이라, 무거운 판정 회차(23분)에선
#       로그 없이 무음 스킵 → paste/pick 소비가 여유 회차까지 실측 8~97분 대기(260815 밤 실측).
# 해법: 1분 틱 편승 — pending/asks 감지 시 정본 .github/scripts/analyze.sh·ask.sh 를 그대로 실행(값 창작 0).
# 가드: ① pgrep analyze.sh/ask.sh 실행 중 = 양보(5분 레인 요약과 경합 0) ② mkdir 잠금(60분 회수)
set -u
export PATH="$HOME/nomute-pybin:/usr/bin:/opt/homebrew/bin:/opt/homebrew/opt/coreutils/libexec/gnubin:$PATH"
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8 NOMUTE_MAC_LANE=1
LK="$HOME/.nomute_analyze_tick.lock"
REPO="${NOMUTE_WORKER_REPO:-$HOME/nomute-worker}"
ENVF="$HOME/nomute-action/환경변수.txt"
pgrep -f "scripts/analyze.sh|scripts/ask.sh" >/dev/null 2>&1 && exit 0
if ! mkdir "$LK" 2>/dev/null; then
  A=$(/usr/bin/stat -f %m "$LK" 2>/dev/null || echo 0); N=$(date +%s)
  { [ $((N-A)) -gt 3600 ] && rmdir "$LK" 2>/dev/null && mkdir "$LK" 2>/dev/null; } || exit 0
fi
trap 'rmdir "$LK" 2>/dev/null' EXIT
command -v claude >/dev/null 2>&1 || exit 0
cd "$REPO" || exit 0
git pull --rebase --autostash -X ours -q origin main 2>/dev/null || true
NP=$(ls pending/*.txt 2>/dev/null | wc -l | tr -d ' ')
NA=$(ls asks/*.json 2>/dev/null | wc -l | tr -d ' ')
[ "${NP:-0}" = "0" ] && [ "${NA:-0}" = "0" ] && exit 0
set -a
while IFS= read -r ln; do
  case "$ln" in ''|'#'*) continue;; esac
  case "$ln" in *=*) k="${ln%%=*}"; case "$k" in *[!A-Za-z0-9_]*) continue;; esac; export "$ln" 2>/dev/null || true;; esac
done < "$ENVF"
set +a
unset ANTHROPIC_API_KEY ANTHROPIC_AUTH_TOKEN 2>/dev/null || true
if [ "${NP:-0}" != "0" ]; then
  echo "[pend] $(date '+%H:%M:%S') pending ${NP}건 — 즉시 소비 시작(틱 편승)"
  ANALYZE_JOB_DEADLINE=2400 bash .github/scripts/analyze.sh || echo "[pend] 분석 일부 실패(성공분 착지·실패 격리)"
fi
if [ "${NA:-0}" != "0" ]; then
  echo "[pend] $(date '+%H:%M:%S') asks ${NA}건 — 즉시 소비"
  bash .github/scripts/ask.sh || echo "[pend] ask 일부 실패"
fi
[ -n "${VAPID_PRIVATE_KEY:-}" ] && { bash .github/scripts/notify_summary.sh || true; bash .github/scripts/notify_fail.sh || true; }
echo "[pend] $(date '+%H:%M:%S') 소비 회차 종료"
exit 0
