#!/usr/bin/env bash
# 노뮤트 R2 픽 큐 스위퍼(260815 코워크) — 뷰어 픽이 깃허브 쓰기 전멸 시 R2 queue/picks/ 에 착지한 것을
# 레인이 먹는 pending/ 으로 옮겨 커밋한다. (CF 쪽 반절 = functions/api/pick.js fail-soft 사다리)
set -u
ENVF="$HOME/nomute-action/환경변수.txt"
REPO="$HOME/nomute-editor"
get(){ grep "^$1=" "$ENVF" 2>/dev/null | head -1 | cut -d= -f2-; }
ACC="$(get R2_ACCOUNT_ID)"; AK="$(get R2_ACCESS_KEY_ID)"; SK="$(get R2_SECRET_ACCESS_KEY)"; BK="$(get R2_BUCKET)"
[ -n "$ACC" ] && [ -n "$AK" ] && [ -n "$SK" ] && [ -n "$BK" ] || exit 0
B="https://$ACC.r2.cloudflarestorage.com/$BK"
KEYS=$(curl -sS --max-time 30 --aws-sigv4 aws:amz:auto:s3 --user "$AK:$SK" \
  "$B?list-type=2&prefix=queue/picks/" 2>/dev/null | grep -o '<Key>[^<]*</Key>' | sed 's/<Key>//;s/<\/Key>//')
[ -n "$KEYS" ] || exit 0
cd "$REPO" || exit 0
n=0
for k in $KEYS; do
  f="pending/$(basename "$k")"
  curl -sS --max-time 30 --aws-sigv4 aws:amz:auto:s3 --user "$AK:$SK" "$B/$k" -o "$f" 2>/dev/null || continue
  [ -s "$f" ] || { rm -f "$f"; continue; }
  git add "$f" 2>/dev/null || continue
  n=$((n+1))
  curl -sS -o /dev/null --max-time 30 --aws-sigv4 aws:amz:auto:s3 --user "$AK:$SK" -X DELETE "$B/$k" 2>/dev/null || true
done
[ "$n" -gt 0 ] || exit 0
git commit -q -m "pick: R2 큐 → pending 착지 ${n}건(맥 스위퍼)" 2>/dev/null || exit 0
git push -q origin HEAD:main 2>/dev/null || true
echo "[pickq] $(date '+%H:%M:%S') 픽 착지 ${n}건"
