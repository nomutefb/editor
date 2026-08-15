#!/usr/bin/env bash
# 노뮤트 화면 재배포기(260815 개정) — CF 깃빌드 동결 대체: 로컬 빌드 → wrangler 직접 업로드(정본 nomute-editor).
# 발화 조건: ① 제작 산출 직후(~/.nomute_need_deploy 깃발 · 잡워커가 세움) = 즉시
#           ② 수집함(candidates) 변화 = 10분 스로틀
# 실패해도 레인 무영향(fail-soft). 백업 프로젝트(nomute-backup)는 대기 축으로 유지.
set -u
export PATH="/usr/bin:/opt/homebrew/bin:$PATH"
ENVF="$HOME/nomute-action/환경변수.txt"; REPO="${NOMUTE_DEPLOY_REPO:-$HOME/nomute-editor}"; ST="$HOME/.nomute_deploy_state"
# 잠금(260815) — 1분 잡 틱 + run.sh 후크 동시 호출 방지(좀비 잠금 15분 후 회수)
LK="$HOME/.nomute_deploy.lock"
if ! mkdir "$LK" 2>/dev/null; then
  A=$(/usr/bin/stat -f %m "$LK" 2>/dev/null || echo 0); N0=$(date +%s)
  { [ $((N0-A)) -gt 900 ] && rmdir "$LK" 2>/dev/null && mkdir "$LK" 2>/dev/null; } || exit 0
fi
trap 'rmdir "$LK" 2>/dev/null' EXIT
mkdir -p "$ST" 2>/dev/null || true
TOK=$(grep '^CF_API_TOKEN=' "$ENVF" 2>/dev/null | cut -d= -f2-)
ACC=$(grep '^R2_ACCOUNT_ID=' "$ENVF" 2>/dev/null | cut -d= -f2-)
[ -n "$TOK" ] && [ -n "$ACC" ] || exit 0
FLAG=0; [ -f "$HOME/.nomute_need_deploy" ] && FLAG=1
H=$(md5 -q "$REPO/viewer/candidates.json" 2>/dev/null || echo x)
LAST=$(cat "$ST/cand.md5" 2>/dev/null || echo '')
NOW=$(date +%s); LT=$(cat "$ST/last.ts" 2>/dev/null || echo 0)
if [ "$FLAG" = "0" ]; then
  [ "$H" = "$LAST" ] && exit 0
  [ $((NOW-LT)) -lt 600 ] && exit 0
fi
cd "$REPO" || exit 0
# 배포 직전 원격 최신 반영(260815) — 잡워커 사본이 밀어둔 산출(gen_out 등)이 빠진 나무로 덮어쓰는 강등 방지
git pull --rebase --autostash -X ours -q origin main 2>/dev/null || true
H=$(md5 -q "$REPO/viewer/candidates.json" 2>/dev/null || echo x)
node build-viewer.mjs >/dev/null 2>&1 || true
if CLOUDFLARE_API_TOKEN="$TOK" CLOUDFLARE_ACCOUNT_ID="$ACC" \
   wrangler pages deploy viewer --project-name=nomute-editor --branch=main --commit-dirty=true >/dev/null 2>&1; then
  echo "$H" > "$ST/cand.md5"; echo "$NOW" > "$ST/last.ts"; rm -f "$HOME/.nomute_need_deploy"
  echo "[deploy] $(date '+%H:%M:%S') 화면 재배포 완료(flag=$FLAG)"
else
  echo "[deploy] $(date '+%H:%M:%S') 재배포 실패 — 다음 회차 재시도"
fi
