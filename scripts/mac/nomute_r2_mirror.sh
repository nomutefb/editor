#!/usr/bin/env bash
# 노뮤트 R2 미러 — 2단 백업 1탄(260814 코워크 세션): 화면 데이터 JSON을 회차마다 R2 live/ 에 올린다.
# 왜: 깃허브 제재로 화면 데이터 경로(raw·contents API·CF 빌드)가 전부 죽어도 R2는 산다(키 실측 200).
#     백업 화면(CF Direct Upload 판)이 live/ 를 직독하면 깃허브 없이 화면이 산다.
# 방식: 핵심 JSON 3종 + 매니페스트. 내용 변화 없으면 스킵(md5 스탬프) = 회차당 호출 최소.
set -u
ENVF="$HOME/nomute-action/환경변수.txt"
REPO="$HOME/nomute-editor"
get(){ grep "^$1=" "$ENVF" 2>/dev/null | head -1 | cut -d= -f2-; }
ACC="$(get R2_ACCOUNT_ID)"; AK="$(get R2_ACCESS_KEY_ID)"; SK="$(get R2_SECRET_ACCESS_KEY)"; BK="$(get R2_BUCKET)"
[ -n "$ACC" ] && [ -n "$AK" ] && [ -n "$SK" ] && [ -n "$BK" ] || { echo "[r2] 키 없음 - 스킵"; exit 0; }
ST="$HOME/.nomute_r2mirror"; mkdir -p "$ST"
up=0; skip=0; fail=0; ts="$(TZ=Asia/Seoul date '+%Y-%m-%dT%H:%M:%S')"
for f in viewer/candidates.json viewer/sns_trends.json viewer/sns_brief.json; do
  p="$REPO/$f"; [ -f "$p" ] || continue
  n="$(basename "$f")"
  h="$(md5 -q "$p" 2>/dev/null || md5sum "$p" | cut -d' ' -f1)"
  if [ "$h" = "$(cat "$ST/$n.md5" 2>/dev/null)" ]; then skip=$((skip+1)); continue; fi
  code="$(curl -sS -o /dev/null -w '%{http_code}' --max-time 60 --aws-sigv4 aws:amz:auto:s3 \
    --user "$AK:$SK" -T "$p" -H 'Content-Type: application/json' \
    "https://$ACC.r2.cloudflarestorage.com/$BK/live/$n")"
  if [ "$code" = "200" ]; then echo "$h" > "$ST/$n.md5"; up=$((up+1)); else fail=$((fail+1)); echo "[r2] $n http $code"; fi
done
# 매니페스트(신선도 표지 — 백업 화면·감시가 이 시각으로 신선도를 판단)
if [ "$up" -gt 0 ] || [ ! -f "$ST/manifest.done" ]; then
  mf="$ST/manifest.json"
  printf '{"updated":"%s","files":["candidates.json","sns_trends.json","sns_brief.json"]}\n' "$ts" > "$mf"
  curl -sS -o /dev/null --max-time 30 --aws-sigv4 aws:amz:auto:s3 --user "$AK:$SK" -T "$mf" \
    -H 'Content-Type: application/json' \
    "https://$ACC.r2.cloudflarestorage.com/$BK/live/manifest.json" && touch "$ST/manifest.done" || true
fi
echo "[r2] $ts up=$up skip=$skip fail=$fail"
