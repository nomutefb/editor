#!/usr/bin/env bash
# 유튜브 숏폼(ys) 맥 표시등 — R2 ys_out/_mac/heartbeat.json 갱신(뷰어 「맥 켜짐/꺼짐」 점등·디밍 원천 · 260928).
# 호출 = nomute_job_worker.sh 매 회차(10초 서브폴) · 여기서 60초 스로틀 → 실제 PUT 은 분당 1회.
# 내용 = {ts, codex: chatgpt|api-key|signed-out|missing, accounts: ChatGPT 로그인된 Codex 계정 수, busy}
#   codex 판정 = `codex login status` 출력(ChatGPT 로그인 = "ChatGPT" 문자열) · 계정 = ~/.codex + ~/.codex-* (CODEX_HOME 별 폴더).
#   ⚠ 로그인 파일(auth.json) 내용은 읽지도 보내지도 않는다 — 상태 문자열만 판정.
# 인자: --force = 스로틀 무시(드라이버가 작업 중 busy 갱신에 쓴다) · --busy / --idle = busy 표기 강제.
# bash 3.2 호환(launchd 레인 = /bin/bash 3.2.57 · self_update 문법 게이트) · 전 경로 fail-soft(exit 0).
set -u
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"
ENVF="$HOME/nomute-action/환경변수.txt"
ST="$HOME/.nomute_ys_hb_last"
FORCE=0; BUSY_ARG=""
for a in "$@"; do
  case "$a" in --force) FORCE=1;; --busy) BUSY_ARG=true;; --idle) BUSY_ARG=false;; esac
done
NOW=$(date +%s)
if [ "$FORCE" != 1 ] && [ -f "$ST" ]; then
  LAST=$(cat "$ST" 2>/dev/null || echo 0)
  case "$LAST" in ''|*[!0-9]*) LAST=0;; esac
  [ $((NOW-LAST)) -lt 60 ] && exit 0
fi
get(){ grep "^$1=" "$ENVF" 2>/dev/null | head -1 | cut -d= -f2-; }
ACC="$(get R2_ACCOUNT_ID)"; AK="$(get R2_ACCESS_KEY_ID)"; SK="$(get R2_SECRET_ACCESS_KEY)"; BK="$(get R2_BUCKET)"
[ -n "$ACC" ] && [ -n "$AK" ] && [ -n "$BK" ] || exit 0

STATE="missing"; N=0
if command -v codex >/dev/null 2>&1; then
  STATE="signed-out"
  for D in "$HOME/.codex" "$HOME"/.codex-*; do
    [ -d "$D" ] || continue
    OUT=$(CODEX_HOME="$D" codex login status 2>&1 | tr 'A-Z' 'a-z')
    case "$OUT" in
      *chatgpt*) N=$((N+1)); STATE="chatgpt";;
      *"api key"*|*api-key*|*apikey*) [ "$STATE" = "signed-out" ] && STATE="api-key";;
    esac
  done
fi
if [ -n "$BUSY_ARG" ]; then BUSY="$BUSY_ARG"
elif [ -f "$HOME/.nomute_ys_busy" ]; then BUSY=true
else BUSY=false; fi

BODY="{\"ts\":$NOW,\"codex\":\"$STATE\",\"accounts\":$N,\"busy\":$BUSY}"
TMP="$HOME/.nomute_ys_hb.json"
printf '%s' "$BODY" > "$TMP"
if curl -sS --max-time 20 --aws-sigv4 aws:amz:auto:s3 --user "$AK:$SK" -X PUT \
     -H 'Content-Type: application/json; charset=utf-8' -H 'Cache-Control: no-store' \
     --data-binary "@$TMP" "https://$ACC.r2.cloudflarestorage.com/$BK/ys_out/_mac/heartbeat.json" >/dev/null 2>&1; then
  echo "$NOW" > "$ST"
fi
exit 0
