#!/usr/bin/env bash
# 유튜브 받기 자가치유 래퍼 — 쿠키가 죽었을 때 **쿠키를 빼고** 다시 시도한다.
#
# 왜(260811 실사고): 미디어 요약(nb) 자료화가 "유튜브 봇 인증 요구 — YT_COOKIES 갱신해줘"로 죽었다.
#   그런데 같은 URL(watch?v=I7qW4WbKCAk)을 **쿠키 없이** 돌리면 rc=0으로 정상 취득된다(실측).
#   즉 실패 원인이 「쿠키가 없어서」가 아니라 「죽은 쿠키를 붙여서」였다 — 유튜브는 무효 세션 쿠키가
#   실린 요청을 봇 검문으로 떨군다(익명 요청은 통과시키면서).
#   원장 push/yt_cookie_health.json 실측 = 260808~0811 내내 쿠키 사망(0810 23:31 잠깐 회복 → 0811 11:07 재사망)
#   → 화면은 나흘째 "쿠키 갱신해줘"만 반복했고, 운영자가 실제로 갈아도 반나절 만에 또 죽었다.
#   쿠키 재발급은 이미 실패가 확정된 처방이라, 코드가 스스로 회수하는 길을 낸다.
#
# 4단 사다리(앞 단이 실패해야 다음 단):
#   ① 쿠키 + 기본 클라이언트     ← 종전 1차(쿠키가 살아있을 때 가장 잘 된다)
#   ② 쿠키 + 대체 클라이언트     ← 종전 2차(nsig·서명 챌린지 우회 · 260723 자가치유)
#   ③ 무쿠키 + 기본 클라이언트   ← 신설(죽은 쿠키가 원인인 경우를 여기서 회수)
#   ④ 무쿠키 + 대체 클라이언트   ← 신설(③ + 서명 챌린지가 겹친 경우)
#   ⚠ ③④는 쿠키가 실제로 실렸을 때만 돈다(무쿠키 운영이면 ①②와 같은 명령이라 헛돈다).
#
# 관측(이 레포가 반복해 겪은 「사유가 지워지는 병」 봉합 — 스레드 [1차 실측]·틱톡 _e1·스모크 사유 0자와 같은 축):
#   ⚠ 종전 nb 래퍼는 stderr를 파일로만 삼키고 분류 문구만 남겨서, **유튜브가 실제로 뭐라 했는지가
#     Actions 로그 어디에도 안 남았다**. 그래서 이번 사고도 "봇 인증"이라는 우리 분류만 보였고
#     원문은 확인할 길이 없었다(nb-make 120행 주석의 260723 오진 판례와 같은 자리).
#   → 전 단계 실패 시 원문 꼬리를 로그 그룹으로 찍는다(과금 0 · 네트워크 0).
#
# 계약: stdout = yt-dlp 출력 그대로(호출부가 `> file` 로 받는다) · 진행 메시지는 전부 stderr.
#   입력 = 환경변수 YT_COOKIES(있으면 쿠키 파일 생성) · YTDLP_ERR(오류 누적 경로) · YTDLP_LABEL(로그 라벨).
#   rc = 0(어느 단이든 성공) / 1(4단 전부 실패).
set -u

ERRF="${YTDLP_ERR:-/tmp/ytdlp_err.txt}"
CKF="${YTDLP_CK:-/tmp/ytdlp_ck.txt}"
LABEL="${YTDLP_LABEL:-yt-dlp}"
ALT='youtube:player_client=tv,mweb,web_safari,default'

: > "$ERRF"

CK=""
if [ -n "${YT_COOKIES:-}" ]; then
  printf '%s\n' "$YT_COOKIES" > "$CKF"
  CK="--cookies $CKF"
fi

ok() {   # 성공 보고는 stderr 로만(stdout 오염 = 호출부 JSON 파싱 붕괴)
  echo "::warning::${LABEL} 성공(${1})" >&2
}

# ① 쿠키 + 기본
python3 -m yt_dlp --socket-timeout 30 $CK "$@" 2>>"$ERRF" && exit 0
echo "::warning::${LABEL} 1차 실패 — 대체 클라이언트로 재시도" >&2

# ② 쿠키 + 대체 클라이언트
python3 -m yt_dlp --socket-timeout 30 $CK --extractor-args "$ALT" "$@" 2>>"$ERRF" && { ok "대체 클라이언트"; exit 0; }

if [ -n "$CK" ]; then
  echo "::warning::${LABEL} 2차 실패 — 쿠키를 빼고 재시도(죽은 쿠키가 원인인 경우 회수)" >&2
  # ③ 무쿠키 + 기본
  python3 -m yt_dlp --socket-timeout 30 "$@" 2>>"$ERRF" && { ok "쿠키 없이"; exit 0; }
  # ④ 무쿠키 + 대체 클라이언트
  python3 -m yt_dlp --socket-timeout 30 --extractor-args "$ALT" "$@" 2>>"$ERRF" && { ok "쿠키 없이·대체 클라이언트"; exit 0; }
fi

# 전 단계 실패 — 원문을 로그에 남긴다(분류 문구만 남기면 다음 세션이 또 추측으로 메운다)
{
  echo "::group::${LABEL} yt-dlp 원문 오류(마지막 2000자)"
  tail -c 2000 "$ERRF"
  echo "::endgroup::"
} >&2
exit 1
