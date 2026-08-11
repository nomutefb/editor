#!/usr/bin/env bash
# 유튜브 받기 자가치유 래퍼 — 가진 쿠키를 **전부** 돌려보고, 그래도 안 되면 쿠키를 빼고 시도한다.
#
# 왜(260811 실사고 · 러너 실측 2회로 확정): 미디어 요약(nb) 자료화가
#   "유튜브 봇 인증 요구 — YT_COOKIES 갱신해줘"로 죽었다. 실측으로 두 가지가 갈렸다.
#   ⓐ 이 컨테이너에서 **쿠키 없이** 같은 URL이 rc=0으로 취득된다 → 「쿠키가 없어서」가 아니다.
#   ⓑ 러너에서 쿠키를 빼고 재시도해도 **같은 벽**이었다(run 31490030593 원문 4회 전건
#      `Sign in to confirm you're not a bot`) → GitHub 러너 IP가 유튜브에 봇으로 찍힌 상태다.
#   → 러너에서는 **살아있는 쿠키가 사실상 필수**인데, 종전 배선은 레일마다 **쿠키를 딱 한 벌만** 봤다.
#
# ⚠ 그 「한 벌」이 이 레포에서 갈려 있었다(260804 다운로더 이관의 잔여):
#     · 미디어 요약·요약 링크 전사·영상 받기 7레일 = 구 시크릿 YT_COOKIES
#     · 다운로더(vidl)·쿠키 건강검진        = 신 시크릿 YT_T_COOKIES / YT_T2_COOKIES
#   건강검진은 **신 쪽만** 본다 → 구 쿠키는 죽어도 아무도 안 울리고, 운영자가 신 쿠키를 새로 갈아도
#   미디어 요약은 여전히 구 쿠키만 보고 죽는다(= 갈아도 안 고쳐지는 상태).
#   → 여기서 **가진 쿠키를 전부 순서대로** 시도한다. 한 벌이라도 살아 있으면 그걸로 통과한다.
#
# 사다리(앞 단이 실패해야 다음 단 · 쿠키 슬롯은 값이 실제로 있는 것만 돈다):
#   쿠키1 기본 → 쿠키1 대체 → 쿠키2 기본 → 쿠키2 대체 → 쿠키3 기본 → 쿠키3 대체
#   → 무쿠키 기본 → 무쿠키 대체
#   「대체」 = --extractor-args player_client=tv,mweb,web_safari,default (nsig·서명 챌린지 우회 · 260723)
#   ⚠ 무쿠키 2단은 쿠키가 실제로 실렸을 때만 돈다(무쿠키 운영이면 앞 단과 같은 명령이라 헛돈다).
#
# 관측(이 레포가 반복해 겪은 「사유가 지워지는 병」 봉합 — 스레드 [1차 실측]·틱톡 _e1·스모크 사유 0자 동축):
#   ⚠ 종전 nb 래퍼는 stderr를 파일로만 삼키고 분류 문구만 남겨서 **유튜브가 실제로 뭐라 했는지가
#     Actions 로그 어디에도 안 남았다**. 그래서 이번 사고도 우리 분류("봇 인증")만 보였고, 그게 맞는지
#     틀린지 확인할 길이 0이었다(nb-make 120행의 260723 오진 판례와 같은 자리).
#   → 전 단계 실패 시 원문 꼬리를 로그 그룹으로 찍는다. 이 한 줄이 260811 진단을 확정시켰다.
#
# 계약: stdout = yt-dlp 출력 그대로(호출부가 `> file` 로 받는다) · 진행 메시지는 전부 stderr.
#   입력 = YT_COOKIES / YT_COOKIES_2 / YT_COOKIES_3(쿠키 본문 · 빈 슬롯은 건너뛴다)
#          YTDLP_ERR(오류 누적 경로) · YTDLP_LABEL(로그 라벨)
#   rc = 0(어느 단이든 성공) / 1(전 단 실패).
set -u

ERRF="${YTDLP_ERR:-/tmp/ytdlp_err.txt}"
CKDIR="${YTDLP_CKDIR:-/tmp/ytdlp_ck}"
LABEL="${YTDLP_LABEL:-yt-dlp}"
ALT='youtube:player_client=tv,mweb,web_safari,default'

: > "$ERRF"
mkdir -p "$CKDIR"
TMPOUT="$CKDIR/out.$$"                       # 단별 stdout 임시 받이(성공분만 최종 stdout으로 흘린다)
trap 'rm -f "$TMPOUT"' EXIT

# 쿠키 슬롯 수집 — 값이 실제로 있는 것만(빈 시크릿은 조용히 건너뛴다)
CK_ARGS=()
CK_NAMES=()
slot=0
for var in YT_COOKIES YT_COOKIES_2 YT_COOKIES_3; do
  val="${!var:-}"   # bash 간접 확장 — eval 금지(쿠키 본문에 따옴표·개행·백틱이 들어오면 그 자리에서 실행된다)
  [ -n "$val" ] || continue
  slot=$((slot + 1))
  f="$CKDIR/ck$slot.txt"
  printf '%s\n' "$val" > "$f"
  CK_ARGS+=("--cookies $f")
  CK_NAMES+=("$var")
done

attempt() {   # $1=사람이 읽을 단 이름  $2=쿠키 인자(빈 문자열이면 무쿠키)  나머지=yt-dlp 인자
  local name="$1" ck="$2"; shift 2
  # ⚠ 각 시도의 stdout은 임시 파일로 받고 **성공한 단의 것만** 내보낸다(260811 실사고 봉합).
  #   호출부는 래퍼 전체를 `> 결과파일` 로 받으므로, 실패한 단이 뱉은 부분 출력이 그대로 앞에 쌓이면
  #   성공분과 겹쳐 「JSON이 두 벌」이 된다(실측 = 3단에서 성공했는데 파싱이 `Extra data: line 2 column 1`
  #   으로 죽었다 · run 31496617671). 종전 인라인 판은 시도마다 `> "$out"` 으로 **덮어써서** 이 문제가
  #   구조적으로 없었는데, 래퍼로 옮기며 누적으로 바뀐 것 = 이관이 만든 회귀다.
  : > "$TMPOUT"
  # shellcheck disable=SC2086 — $ck 는 "--cookies <경로>" 두 토큰으로 갈려야 한다(따옴표 금지)
  python3 -m yt_dlp --socket-timeout 30 $ck "$@" > "$TMPOUT" 2>>"$ERRF" && {
    cat "$TMPOUT"
    echo "::warning::${LABEL} 성공(${name})" >&2
    return 0
  }
  echo "::warning::${LABEL} 실패(${name})" >&2
  return 1
}

i=0
while [ "$i" -lt "${#CK_ARGS[@]}" ]; do
  nm="${CK_NAMES[$i]}"
  attempt "$nm" "${CK_ARGS[$i]}" "$@" && exit 0
  attempt "$nm·대체 클라이언트" "${CK_ARGS[$i]} --extractor-args $ALT" "$@" && exit 0
  i=$((i + 1))
done

if [ "${#CK_ARGS[@]}" -gt 0 ]; then
  echo "::warning::${LABEL} 쿠키 ${#CK_ARGS[@]}벌 전부 실패 — 쿠키를 빼고 재시도" >&2
fi
attempt "쿠키 없이" "" "$@" && exit 0
attempt "쿠키 없이·대체 클라이언트" "--extractor-args $ALT" "$@" && exit 0

# 전 단계 실패 — 원문을 로그에 남긴다(분류 문구만 남기면 다음 세션이 또 추측으로 메운다)
{
  echo "::group::${LABEL} yt-dlp 원문 오류(마지막 2000자)"
  tail -c 2000 "$ERRF"
  echo "::endgroup::"
} >&2
exit 1
