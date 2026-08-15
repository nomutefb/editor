#!/usr/bin/env bash
# 노뮤트 홈(nomute.kr) 재빌드기(260815 코워크) — 깃허브 정지로 CF 자동빌드가 동결된 홈을
# 맥이 시간당 로컬 빌드→wrangler 직접 업로드로 대행한다(nomute-backup_deploy 패턴 미러).
# 구조: 60분 게이트 + mkdir 잠금(30분 회수) + fail-soft(실패해도 틱 정상).
# RSS는 astro 빌드가 빌드 시점에 직접 당긴다(src/lib/feeds.ts) = 데이터 배선 불요.
set -u
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"
MARK="$HOME/.nomute_home_deploy_last"; LOCK="$HOME/.nomute_home_deploy.lock"
REPO="$HOME/nomute_homepage"; ENVF="$HOME/nomute-action/환경변수.txt"
now=$(date +%s)
last=$(cat "$MARK" 2>/dev/null || echo 0)
[ $((now - last)) -lt 3600 ] && exit 0
if ! mkdir "$LOCK" 2>/dev/null; then
  age=$(( now - $(stat -f %m "$LOCK" 2>/dev/null || echo 0) ))
  [ "$age" -lt 1800 ] && exit 0
  rm -rf "$LOCK"; mkdir "$LOCK" 2>/dev/null || exit 0
fi
trap 'rm -rf "$LOCK"' EXIT
get(){ grep "^$1=" "$ENVF" 2>/dev/null | head -1 | cut -d= -f2-; }
export CLOUDFLARE_API_TOKEN="$(get CF_API_TOKEN)" CLOUDFLARE_ACCOUNT_ID="$(get R2_ACCOUNT_ID)"
[ -n "$CLOUDFLARE_API_TOKEN" ] || { echo "[home] $(date '+%H:%M:%S') CF 토큰 없음 — 스킵"; exit 0; }
cd "$REPO" 2>/dev/null || { echo "[home] $(date '+%H:%M:%S') 레포 없음 — 스킵"; exit 0; }
git pull -q --rebase 2>/dev/null || true
[ -d node_modules ] || timeout 420 npm ci --no-audit --no-fund >/dev/null 2>&1 || true
if ! timeout 300 npx astro build >/tmp/nmt_home_build.log 2>&1; then
  echo "[home] $(date '+%H:%M:%S') 빌드 실패 — 직전 유지(로그 /tmp/nmt_home_build.log)"; exit 0
fi
if timeout 180 wrangler pages deploy dist --project-name=nomute --branch=main --commit-dirty=true >/tmp/nmt_home_deploy.log 2>&1; then
  echo "$now" > "$MARK"
  echo "[home] $(date '+%H:%M:%S') nomute.kr 재빌드·배포 완료"
else
  echo "[home] $(date '+%H:%M:%S') 배포 실패 — 직전 유지(로그 /tmp/nmt_home_deploy.log)"
fi
exit 0
