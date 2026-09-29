#!/usr/bin/env bash
# 유튜브 숏폼(ys) 맥 표시등 — R2 ys_out/_mac/heartbeat.json 갱신(뷰어 「맥 켜짐/꺼짐」 점등·디밍 원천 · 260928).
# 호출 = nomute_job_worker.sh 매 회차(10초 서브폴) · 여기서 60초 스로틀 → 실제 PUT 은 분당 1회.
# 내용 = {ts, codex: chatgpt|api-key|signed-out|missing, accounts: ChatGPT 로그인된 Codex 계정 수, busy, drv: 드라이버 능력 판}
#   codex 판정 = `codex login status` 출력(ChatGPT 로그인 = "ChatGPT" 문자열) · 계정 = ~/.codex + ~/.codex-* (CODEX_HOME 별 폴더).
#   ⚠ 로그인 파일(auth.json) 내용은 읽지도 보내지도 않는다 — 상태 문자열만 판정.
# 인자: --force = 스로틀 무시(드라이버가 작업 중 busy 갱신에 쓴다) · --busy / --idle = busy 표기 강제.
# bash 3.2 호환(launchd 레인 = /bin/bash 3.2.57 · self_update 문법 게이트) · 전 경로 fail-soft(exit 0).
set -u
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/opt/homebrew/opt/coreutils/libexec/gnubin:/usr/local/bin:/usr/bin:/bin:$PATH"   # gnubin = timeout
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
    if command -v timeout >/dev/null 2>&1; then OUT=$(CODEX_HOME="$D" timeout 15 codex login status 2>&1 | tr 'A-Z' 'a-z')
    else OUT=$(CODEX_HOME="$D" codex login status 2>&1 | tr 'A-Z' 'a-z'); fi   # 15초 상한 = 워커 잠금 안에서 codex 가 멈춰도 다른 잡이 안 막힌다
    case "$OUT" in
      *chatgpt*) N=$((N+1)); STATE="chatgpt";;
      *"api key"*|*api-key*|*apikey*) [ "$STATE" = "signed-out" ] && STATE="api-key";;
    esac
  done
fi
if [ -n "$BUSY_ARG" ]; then BUSY="$BUSY_ARG"
elif [ -n "$(find "$HOME/.nomute_ys_busy" -mmin -65 2>/dev/null)" ]; then BUSY=true   # 65분 넘은 표식 = 죽은 작업의 잔재(드라이버 상한 60분) → 무시
else BUSY=false; fi

DRV=$(sed -n 's/^YS_DRV=\([0-9][0-9]*\).*/\1/p' "$HOME/nomute_ys_driver.sh" 2>/dev/null | head -1)   # 설치된 드라이버의 표지를 읽는다(자기갱신은 파일마다 따로 = 심박만 새 판일 수 있다)
case "$DRV" in ''|*[!0-9]*) DRV=1;; esac
BODY="{\"ts\":$NOW,\"codex\":\"$STATE\",\"accounts\":$N,\"busy\":$BUSY,\"drv\":$DRV}"   # drv = 드라이버 능력(2 = 주인공 시트·첨부 · 400자 · 러너 ys_images 가 읽는다)
TMP="$HOME/.nomute_ys_hb.json"
printf '%s' "$BODY" > "$TMP"
if curl -sS --max-time 20 --aws-sigv4 aws:amz:auto:s3 --user "$AK:$SK" -X PUT \
     -H 'Content-Type: application/json; charset=utf-8' -H 'Cache-Control: no-store' \
     --data-binary "@$TMP" "https://$ACC.r2.cloudflarestorage.com/$BK/ys_out/_mac/heartbeat.json" >/dev/null 2>&1; then
  echo "$NOW" > "$ST"
fi
exit 0
