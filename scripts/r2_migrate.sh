#!/usr/bin/env bash
# r2_migrate.sh — 옛 보관함 → 새 보관함 통째 복사(운영자 컴퓨터에서 1회 실행)
#
# 왜 rclone 인가: 계정이 다르면 `aws s3 sync` 로는 못 옮긴다 — 그 명령은 출발지·도착지 주소를
#   한 번에 못 받아서 「받았다가 다시 올리기」 2단계가 되고, 디스크에 전량이 한 번 내려앉는다.
#   rclone 은 두 계정을 동시에 물고 서버 대 서버로 흘려보낸다(디스크 경유 0 · 이어받기 지원).
#
# 왜 스크립트인가: 이 복사는 **다른 모든 갈아끼우기보다 먼저** 끝나야 한다.
#   지난 제작물 693개 기록 파일이 옛 보관함 주소를 가리키므로, 복사 없이 주소만 바꾸면
#   과거 결과물이 전건 깨진 그림이 된다(260815 실측).
#
# 사용:
#   bash r2_migrate.sh            # 대화형(값을 물어본다)
#   bash r2_migrate.sh --check    # 설치·연결만 확인하고 복사는 안 함
#   bash r2_migrate.sh --resume   # 끊긴 복사 이어서(같은 값 다시 입력)
set -uo pipefail

MODE=${1:-}
CFG="${TMPDIR:-/tmp}/nomute_r2_rclone_$$.conf"
cleanup() { [ -f "$CFG" ] && rm -f "$CFG"; }
trap cleanup EXIT

hr() { printf '%s\n' '────────────────────────────────────────'; }
hr; echo '📦 보관함 통째 복사 (옛 계정 → 새 계정)'; hr

# ── ① rclone 설치 확인 ────────────────────────────────────────────────
if ! command -v rclone >/dev/null 2>&1; then
  echo '❌ rclone 이 없다. 먼저 깔아라.'
  echo
  echo '  맥  : brew install rclone'
  echo '  (brew 가 없으면) : curl https://rclone.org/install.sh | sudo bash'
  echo '  윈도 : winget install Rclone.Rclone'
  echo
  exit 1
fi
echo "✅ rclone $(rclone version 2>/dev/null | head -1 | awk '{print $2}')"
echo

# ── ② 값 받기 ────────────────────────────────────────────────────────
hr; echo '옛 보관함 (지금 쓰는 것)'; hr
read -rp '  계정 번호(32자리)      : ' OLD_ACC
read -rp '  접근 열쇠 아이디       : ' OLD_KEY
read -rsp '  접근 열쇠 비밀값       : ' OLD_SEC; echo
read -rp '  버킷 이름              : ' OLD_BKT
echo
hr; echo '새 보관함 (방금 만든 것)'; hr
read -rp '  계정 번호(32자리)      : ' NEW_ACC
read -rp '  접근 열쇠 아이디       : ' NEW_KEY
read -rsp '  접근 열쇠 비밀값       : ' NEW_SEC; echo
read -rp '  버킷 이름              : ' NEW_BKT
echo

for v in OLD_ACC OLD_KEY OLD_SEC OLD_BKT NEW_ACC NEW_KEY NEW_SEC NEW_BKT; do
  eval "val=\${$v}"
  [ -z "$val" ] && { echo "❌ $v 가 비었다."; exit 1; }
done
if [ "$OLD_ACC" = "$NEW_ACC" ] && [ "$OLD_BKT" = "$NEW_BKT" ]; then
  echo '❌ 옛 것과 새 것이 완전히 같다 — 값을 잘못 넣었다.'; exit 1
fi

# ── ③ 설정 파일(임시 · 끝나면 지워진다) ────────────────────────────────
umask 077
cat > "$CFG" <<CONF
[old]
type = s3
provider = Cloudflare
access_key_id = $OLD_KEY
secret_access_key = $OLD_SEC
endpoint = https://$OLD_ACC.r2.cloudflarestorage.com
region = auto
no_check_bucket = true

[new]
type = s3
provider = Cloudflare
access_key_id = $NEW_KEY
secret_access_key = $NEW_SEC
endpoint = https://$NEW_ACC.r2.cloudflarestorage.com
region = auto
no_check_bucket = true
CONF

RC="rclone --config $CFG"

# ── ④ 양쪽 연결 실측(복사 시작 전에 확인 — 반쯤 가다 죽는 것보다 싸다) ──
hr; echo '연결 확인'; hr
if ! $RC lsd "old:$OLD_BKT" >/dev/null 2>&1 && ! $RC ls "old:$OLD_BKT" --max-depth 1 >/dev/null 2>&1; then
  echo '❌ 옛 보관함에 못 붙는다 — 계정 번호·열쇠·버킷 이름을 확인해라.'
  $RC ls "old:$OLD_BKT" --max-depth 1 2>&1 | head -3
  exit 1
fi
echo '✅ 옛 보관함 연결됨'
if ! $RC lsd "new:$NEW_BKT" >/dev/null 2>&1 && ! $RC ls "new:$NEW_BKT" --max-depth 1 >/dev/null 2>&1; then
  echo '❌ 새 보관함에 못 붙는다 — 버킷을 만들었는지·권한이 Object Read & Write 인지 확인해라.'
  $RC ls "new:$NEW_BKT" --max-depth 1 2>&1 | head -3
  exit 1
fi
echo '✅ 새 보관함 연결됨'
echo

# ── ⑤ 규모 실측 ──────────────────────────────────────────────────────
hr; echo '옮길 양 재는 중 (파일이 많으면 몇 분 걸린다)'; hr
SRC_INFO=$($RC size "old:$OLD_BKT" 2>&1)
echo "$SRC_INFO"
echo
DST_INFO=$($RC size "new:$NEW_BKT" 2>&1)
echo "새 보관함 현재: $(echo "$DST_INFO" | tr '\n' ' ')"
echo

if [ "$MODE" = "--check" ]; then
  hr; echo '(--check 라 여기까지. 실제 복사는 인자 없이 다시 실행)'; hr; exit 0
fi

read -rp '  복사를 시작할까? [y/N] : ' OK
case "$OK" in y|Y) : ;; *) echo '  → 중단.'; exit 0 ;; esac
echo

# ── ⑥ 복사 ───────────────────────────────────────────────────────────
# copy = 도착지에만 있는 파일을 안 지운다(sync 는 지운다 = 사고 시 복구 불가) → copy 로 간다.
# 이어받기 = 같은 명령을 다시 돌리면 이미 간 파일은 건너뛴다(크기·시각 대조).
hr; echo '복사 중 — 창을 닫지 마라. 끊기면 같은 명령을 다시 돌리면 이어서 간다.'; hr
$RC copy "old:$OLD_BKT" "new:$NEW_BKT" \
  --transfers 16 --checkers 32 \
  --s3-upload-concurrency 8 \
  --retries 5 --low-level-retries 20 \
  --progress --stats 10s
RC_CODE=$?
echo

# ── ⑦ 사후 대조 — 실제로 다 갔나(성공을 실패로/실패를 성공으로 오판 금지) ──
hr; echo '도착 확인'; hr
SRC_N=$($RC size "old:$OLD_BKT" 2>/dev/null | grep -oE '[0-9]+ objects' | grep -oE '[0-9]+')
DST_N=$($RC size "new:$NEW_BKT" 2>/dev/null | grep -oE '[0-9]+ objects' | grep -oE '[0-9]+')
echo "  옛 보관함 파일 수 = ${SRC_N:-?}"
echo "  새 보관함 파일 수 = ${DST_N:-?}"
echo

if [ "${RC_CODE:-1}" -eq 0 ] && [ -n "${SRC_N:-}" ] && [ -n "${DST_N:-}" ] && [ "$DST_N" -ge "$SRC_N" ]; then
  hr
  echo '✅ 복사 끝.'
  echo '   다음 = 새 보관함 공개 주소를 손에 쥐고 배선 갈아끼우기'
  echo '          (지난 제작물 693개 기록이 그 주소를 가리킨다)'
  hr
  exit 0
else
  hr
  echo '❌ 아직 덜 갔다.'
  echo '   같은 명령을 다시 돌려라 — 이미 간 파일은 건너뛰고 남은 것만 이어서 간다.'
  echo "   (rclone 종료코드 = ${RC_CODE})"
  hr
  exit 1
fi
