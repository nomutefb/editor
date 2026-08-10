#!/usr/bin/env bash
# 임시 업로드 원본 청소 — up_src/* 중 **TTL(기본 24시간) 지난 것만** 지운다.
#
# 왜 이 파일이 생겼나(260810 · 운영자 "한번 올린거 바로 휘발시키지말고 냅둬봐 · 한개의 작업본으로 작업을 1개 밖에
#   못하는게 무슨 개떡같은 인터페이스야"):
#   종전에는 워크플로 6개(edit·ly·conv·track·voice·framethumb)가 잡 끝에 `aws s3 rm "$R2_SRC"` 로 **자기가 쓴 원본을
#   그 자리에서 삭제**했다. 러너는 원본을 `aws s3 cp` 로 내려받아 **읽기만** 하는데(수정 0), 삭제 때문에 같은 영상으로
#   두 번째 작업을 걸면 뷰어가 _lastFile 로 **전체 바이트를 처음부터 재업로드**했다(1GB면 1GB 다시 · edit.html 2066행
#   주석이 이미 그 비용을 실측으로 적어두고 있었다 = 일시 실패 케이스만 봉합하고 정상 경로는 그대로였다).
#   비용 비교 = 보관 $0.015/GB·월(1GB 하루 ≈ 0.0005달러) vs 재업로드(운영자 회선 시간 + Class A 34요청/GB)
#   → **보관이 압도적으로 싸다**. 그래서 「즉시 삭제」를 「나이 든 것만 청소」로 바꾼다.
#
# 왜 대시보드 수명규칙이 아니라 스크립트인가:
#   R2는 접두사별 수명규칙을 정식 지원하지만 **대시보드/wrangler 수동 1회 설정**이라 운영자 손이 필요하고,
#   설정 여부를 레포가 알 수 없다(안 걸려 있으면 고아가 영구 잔존 = api/upload.js 9행이 "권장·선택"이라 적어둔 그 구멍).
#   이 스크립트는 잡이 이미 들고 있는 자격증명으로 그 자리에서 청소하므로 **운영자 조치 0**([9] 납품 축).
#   대시보드 규칙을 나중에 걸어도 충돌 없음(둘 다 "나이 든 것만" = 멱등).
#
# 계약:
#   · 대상 = `up_src/` 접두 + 키 문법 검증 통과 + LastModified 가 TTL 이전인 객체만.
#   · 자격증명·버킷 미설정 = 조용히 스킵(rc 0) — 청소 실패가 잡을 죽이면 안 된다(종전 `|| echo` fail-soft 계승).
#   · 삭제 상한 GC_MAX(기본 200) = 폭주 방어. 초과분은 다음 잡이 이어서 치운다.
#   · 시각 비교 = ISO 문자열 앞 19자 사전순(= 시간순). 형식 꼬리(`Z` vs `+00:00`) 차이를 구조적으로 회피.
# 환경변수: R2_BUCKET R2_ACCOUNT_ID AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY · UPSRC_TTL_H(기본 24) · GC_MAX(기본 200)
set -u

HRS="${UPSRC_TTL_H:-24}"
MAX="${GC_MAX:-200}"
case "$HRS" in ''|*[!0-9]*) HRS=24;; esac
case "$MAX" in ''|*[!0-9]*) MAX=200;; esac

[ -n "${R2_BUCKET:-}" ] || { echo "임시 업로드 청소 — 버킷 미설정, 스킵"; exit 0; }
[ -n "${R2_ACCOUNT_ID:-}" ] || { echo "임시 업로드 청소 — 계정 미설정, 스킵"; exit 0; }
[ -n "${AWS_ACCESS_KEY_ID:-}" ] || { echo "임시 업로드 청소 — 키 미설정, 스킵"; exit 0; }
command -v aws >/dev/null 2>&1 || { echo "임시 업로드 청소 — aws 없음, 스킵"; exit 0; }

export AWS_DEFAULT_REGION=auto AWS_REQUEST_CHECKSUM_CALCULATION=when_required AWS_RESPONSE_CHECKSUM_VALIDATION=when_required
EP="https://${R2_ACCOUNT_ID}.r2.cloudflarestorage.com"

CUT="$(date -u -d "${HRS} hours ago" '+%Y-%m-%dT%H:%M:%S' 2>/dev/null || true)"
[ -n "$CUT" ] || { echo "임시 업로드 청소 — 컷오프 계산 실패, 스킵"; exit 0; }

LIST="$(aws s3api list-objects-v2 --bucket "$R2_BUCKET" --prefix 'up_src/' --endpoint-url "$EP" \
  --query 'Contents[].[LastModified,Key]' --output text 2>/dev/null || true)"
[ -n "$LIST" ] && [ "$LIST" != "None" ] || { echo "임시 업로드 청소 — 대상 없음 (컷오프 ${CUT}Z · TTL ${HRS}h)"; exit 0; }

n=0; kept=0
while IFS=$'\t' read -r ts key; do
  [ -n "${key:-}" ] || continue
  case "$key" in up_src/*) ;; *) continue;; esac          # 접두 재확인(종전 스텝 관례 계승)
  case "$key" in *..*|*' '*) continue;; esac              # 경로 탈출·공백 차단
  [ "${ts:0:19}" \< "$CUT" ] || { kept=$((kept+1)); continue; }   # 아직 안 늙음 = 살려둔다(= 재사용 창)
  [ "$n" -lt "$MAX" ] || { echo "임시 업로드 청소 — 상한 ${MAX} 도달, 나머지는 다음 잡에서"; break; }
  aws s3 rm "s3://$R2_BUCKET/$key" --endpoint-url "$EP" --only-show-errors \
    && n=$((n+1)) || echo "청소 실패(무해 — 다음 잡 재시도): $key"
done <<EOF
$LIST
EOF

echo "임시 업로드 청소 — 삭제 ${n}건 · 보존 ${kept}건 (TTL ${HRS}h · 컷오프 ${CUT}Z)"
exit 0
