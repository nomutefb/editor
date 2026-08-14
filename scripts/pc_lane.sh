#!/usr/bin/env bash
# PC/맥 2단 안전장치 — 액션 없이 도는 일괄 레인(운영자 260814 "내부 pc나 기기를 통해 돌릴 수 있는 배선을 만들어서 … 풀리더라도 2단으로 갈거임. 안전장치")
# 왜: 260814 GitHub 계정 단위 Actions 정지(CLAUDE.md 🚨 항목)로 판정·분석·제작 레인이 전멸했다.
#   폰 레인(phone_scrape.sh)은 수집만 되살린다 — 이 레인은 수집(폰과 교차)에 더해 **속보 판정·경중 채점·
#   화재 후속 추적·트렌드/재난문자·SNS·채널 수집·감시·요약 제작**까지 이 컴퓨터에서 돌린다.
#   Actions 복구 후에도 유지 = 2단 안전장치(운영자 확정) · 산출 파일이 워크플로와 동일이라 겹쳐 돌아도 충돌 0.
# 실행 환경 = 맥 launchd 5분 / 윈도우 작업 스케줄러 5분(설치 = 노뮤트_클라우드액션_설치.command/.bat) · WSL·리눅스 동일.
#
# ▶ 260814 2차 확장(운영자 «지금 키 값 더 넣어야되는것들 해결해서 깃허브 액션 없이도 정상 가동 모든 웹앱 내 기능이 돌도록 하자»)
#   구판은 수집·판정 2스텝뿐이라 「화면에 뉴스는 늘어나는데 그 밖의 모든 축이 정지」였다. 이번 판은
#   **시계 하나 안에 스테이지 러너**를 두어 워크플로 13종의 주기를 그대로 재현한다(주기 원장 = ~/.nomute_lane_stage).
#   ⚠ 시계를 새로 만들지 않은 이유 = 운영자가 설치를 다시 하지 않아도 되게(«세팅 다 하면 웹앱만 만지고싶음»).
#      launchd 는 앞 회차가 도는 동안 새 회차를 안 띄우므로 긴 회차 = 수집 슬롯 몇 개를 건너뛰는 것뿐이고,
#      폰 레인(30분)이 그동안의 수집 백스톱이다. 대신 **회차 예산**(LANE_BUDGET)으로 폭주를 막는다.
#
# ▷ 값 창작 0 — 각 스테이지의 명령·인자·env 는 대응 워크플로의 사본이다:
#   수집 = scrape.yml「Collect」·「Update 수집함」 / 화재 = scrape.yml「화재 후속 추적」 /
#   판정 = breaking-judge.yml / 트렌드·재난 = sns-trends.yml / SNS = social-scan.yml /
#   채널 = insta-fetch.yml·fb-fetch.yml / 감시 = watchdog.yml / 계측 = metrics-rollup.yml /
#   쿠키 = yt-cookie-health.yml / 요약 = news-analyze.yml·news-ask.yml.
#
# ▷ 이 레인이 **못 하는 것**(되는 척 금지 · 구조적 불가):
#   ⓐ 제작 레인(카드 촬영·영상·음원·이미지 편집) = 뷰어 → Cloudflare 함수 → **workflow_dispatch** 축이라
#      요청 자체가 레포에 안 남는다(원본은 R2 로 직행). 액션이 꺼진 동안은 요청이 접수 시점에 사라진다.
#      ↔ 반대로 **픽·요약요청은 산다** — 그 둘은 함수가 pending/·asks/ 파일을 main 에 직접 쓴다(디스패치는 그 뒤).
#   ⓑ 화면 재배포 = Cloudflare Pages 빌드가 같은 시각부터 정지(실측 260814 = 마지막 성공 빌드 08-13 17:02Z).
#      배포 훅도 죽었다(실측 = "Unable to find a branch with the provided name") → **정적 화면은 동결**이고
#      라이브로 도달하는 건 functions/api 직독 표면(수집함·트렌드·채널)뿐. 요약·카드는 main 에 쌓이고
#      해제되는 순간 한꺼번에 뜬다(유실 0).
# 착지 원장 = ~/.nomute_pc_lane_land (phone_scrape 원장 문법 사본 · 파일만 갈라 둔다 = 두 레인의 막힌 자리 구분).
set -u
_SELF_SUM="$(cksum "$0" 2>/dev/null | cut -d' ' -f1)"   # 자기 갱신 안전의 짝(아래 재시작 블록 · git pull 이 이 파일을 바꾸는 순간을 잡는다)
cd "$HOME/nomute-editor" 2>/dev/null || { echo "레포 없음: ~/nomute-editor — 설치 파일을 먼저 실행"; exit 1; }

LAND="$HOME/.nomute_pc_lane_land"
_land(){ printf '%s|%s|%s\n' "$(date '+%Y-%m-%dT%H:%M:%S')" "$1" "${2:-}" > "$LAND" 2>/dev/null || true; }

# ── 동시 실행 잠금(mkdir = 윈도우 Git-Bash 에 flock 이 없다) — 경중 채점·요약이 콜당 최대 900s 라 5분 주기를 넘길 수 있다.
#    앞 회차가 아직 돌고 있으면 이번 회차는 조용히 물러난다(claude 콜 이중 발사·git 경합 차단) · 90분 넘은 잠금 = 죽은 회차로 보고 회수.
LOCK="$HOME/.nomute_pc_lane.lock"
if ! mkdir "$LOCK" 2>/dev/null; then
  if [ -n "$(find "$LOCK" -maxdepth 0 -mmin +90 2>/dev/null)" ]; then rmdir "$LOCK" 2>/dev/null || true; mkdir "$LOCK" 2>/dev/null || { _land "lock-busy" "회수 직후 경합"; exit 0; }
  else _land "lock-busy" "앞 회차 진행 중(정상)"; exit 0; fi
fi
trap 'rmdir "$LOCK" 2>/dev/null' EXIT

# ── 환경(윈도우 = 파이썬이 python 이름 · 셸 PATH 가 작업 스케줄러에서 빈약) — 설치가 구운 env 를 먼저 읽는다.
[ -f "$HOME/.nomute_pc_env" ] && . "$HOME/.nomute_pc_env"
# ⚠ 260814 실측 봉합(운영자 로그 실물): 한글 윈도우 파이썬은 출력 문자 규격이 cp949 라 수집기가 요약표에
#   이모지(🔥)를 찍는 순간 UnicodeEncodeError 로 넘어진다 — 일(기사 수집·파일 쓰기)은 다 끝내고 **보고서
#   찍다가** 죽어서 매 회차 collect-fail 로 오기록됐다. 파이썬 전 호출을 세계 문자 규격으로 강제한다.
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8
# ⚠ 260814 실측 봉합: 윈도우는 WindowsApps 에 **가짜 python3.exe**(스토어 여는 껍데기)를 심는다 — 구판이
#   python3 을 먼저 찾다 그 껍데기를 집어 수집이 즉사(collect-fail · 화면에 「Python」 한 줄만 남김).
#   → python 우선(실행기가 진짜 설치 폴더를 PATH 맨 앞에 박아줌) + WindowsApps 경로는 후보에서 제외.
PY=""
for _c in python python3; do
  _p="$(command -v "$_c" 2>/dev/null || true)"
  case "$_p" in *WindowsApps*) continue;; esac
  [ -n "$_p" ] && { PY="$_p"; break; }
done
[ -n "$PY" ] || { _land "no-python" "진짜 python 미발견(껍데기 제외) — 설치 파일 재실행"; exit 1; }
git config user.email >/dev/null 2>&1 || { git config user.name "nomute-pc"; git config user.email "nomute-pc@local"; }

# 스테이지 스크립트 다수가 `python3` 를 직접 부른다(워크플로 사본) — 윈도우 가짜 python3 을 피해 진짜 파이썬을
# python3 이름으로 앞세운다(맥·리눅스는 이미 python3 = 무해).
if ! command -v python3 >/dev/null 2>&1 || [ "$(command -v python3)" != "$PY" ]; then
  mkdir -p "$HOME/.nomute_bin" 2>/dev/null || true
  printf '#!/bin/sh\nexec "%s" "$@"\n' "$PY" > "$HOME/.nomute_bin/python3" 2>/dev/null && chmod +x "$HOME/.nomute_bin/python3" 2>/dev/null || true
  PATH="$HOME/.nomute_bin:$PATH"; export PATH
fi

# ── git 착지 자가복구(phone_scrape.sh 정본 블록의 동작 사본 · 창작 0) ─────────
_heal=""
if [ -d .git/rebase-merge ] || [ -d .git/rebase-apply ]; then
  git rebase --abort 2>/dev/null || rm -rf .git/rebase-merge .git/rebase-apply
  _heal="rebase-abort"
fi
if [ -f .git/MERGE_HEAD ]; then git merge --abort 2>/dev/null || rm -f .git/MERGE_HEAD .git/MERGE_MSG; _heal="${_heal:+$_heal+}merge-abort"; fi
if [ -f .git/index.lock ] && [ -n "$(find .git/index.lock -mmin +5 2>/dev/null)" ]; then rm -f .git/index.lock; _heal="${_heal:+$_heal+}stale-lock"; fi
git fetch origin main -q 2>/dev/null || { _land "fetch-fail" "네트워크·인증(회선 사망·로그인 만료)"; exit 0; }
# ⚠ 정렬 전에 **한 번은 밀어본다** — 아래 realign(checkout -B)·pull-heal(reset --hard)은 안 밀린 로컬 커밋을
#   그냥 버린다. 구판은 그 자리에서 앞 회차 요약·판정 산출이 조용히 증발했다(260814 실측 push-fail 다음 회차).
if [ "$(git rev-list --count origin/main..HEAD 2>/dev/null || echo 0)" -gt 0 ]; then
  git push -q origin HEAD:main 2>/dev/null && _heal="${_heal:+$_heal+}late-push"
fi
_unp="$(git rev-list --count origin/main..HEAD 2>/dev/null || echo 0)"
_br="$(git symbolic-ref -q --short HEAD 2>/dev/null || echo '-')"
if [ "$_br" != "main" ] || [ "${_unp:-0}" -ge 3 ]; then
  git checkout -q -B main origin/main 2>/dev/null || true
  _heal="${_heal:+$_heal+}realign(br=$_br,unpushed=$_unp)"
elif ! git pull -q --rebase origin main 2>/dev/null; then
  git rebase --abort 2>/dev/null || true; git reset --hard -q origin/main 2>/dev/null || true
  _heal="${_heal:+$_heal+}pull-heal"
fi
[ -n "$_heal" ] && echo "🔧 git 착지 자가복구: $_heal"

# ⚠⚠ 자기 갱신 안전(같은 병이 phone_scrape·phone_subs 에도 있다 = 형제 전건 봉합) — 이 스크립트는 **자기 자신을
#   바꾸는 git pull 을 자기 실행 도중에** 돌린다. 셸은 파일을 통째로 읽어두지 않고 바이트 위치를 기억하며 조금씩
#   읽으므로, 그 사이 파일 길이가 바뀌면 **남은 절반을 엉뚱한 위치부터 읽어** 문법 오류·반쪽 실행이 난다.
#   → 파일이 바뀌었으면 그 자리에서 새 파일로 다시 시작한다(잠금은 먼저 놓는다 = exec 는 EXIT 덫을 안 부른다).
if [ "${NOMUTE_LANE_REEXEC:-0}" != "1" ]; then
  _sum_now="$(cksum "$0" 2>/dev/null | cut -d' ' -f1)"
  if [ -n "${_SELF_SUM:-}" ] && [ -n "$_sum_now" ] && [ "$_sum_now" != "$_SELF_SUM" ]; then
    echo "♻ 레인 코드가 갱신됐다 — 새 코드로 이번 회차를 다시 시작한다"
    rmdir "$LOCK" 2>/dev/null || true
    NOMUTE_LANE_REEXEC=1 exec bash "$0" "$@"
  fi
fi

# ── 심장박동(운영자 260814 「너가 웹앱 상태 실시간으로 모니터링하고 직접 수선해」) — 이 레인이 돌고 있다는
#    신호를 main 에 남겨 세션이 원격에서 생사를 읽게 한다. 매 회차 커밋 = 하루 수백 개 잡음이라 20분 상한 ·
#    실패 회차도 신호를 남긴다(신호 없음 = 시계 자체가 안 도는 것으로 확정 판독 가능해진다).
BEAT="scraper/obs/pc_lane_beat.json"
_last_beat=$(sed -n 's/.*"epoch":\([0-9]*\).*/\1/p' "$BEAT" 2>/dev/null | head -1); [ -n "$_last_beat" ] || _last_beat=0
if [ $(( $(date +%s) - _last_beat )) -ge 1200 ]; then
  printf '{"epoch":%s,"kst":"%s"}\n' "$(date +%s)" "$(TZ=Asia/Seoul date '+%m-%d %H:%M:%S')" > "$BEAT" 2>/dev/null || true
  git add "$BEAT" 2>/dev/null || true
  git diff --cached --quiet 2>/dev/null || { git commit -q -m "beat(pc): 레인 생존 신호" 2>/dev/null && git push -q origin HEAD:main 2>/dev/null || true; }
fi

# ── 공용 착지 = git_land.sh 위임(정본 1곳 · 사본 0) ────────────────────────────
# ⚠ 260814 실측 봉합: 구판은 자체 4회 루프에서 `git rebase origin/main`을 돌렸는데, 폰 레인과 이 레인이
#   같은 viewer/candidates.json 을 쥐면 리베이스가 충돌로 죽고 → abort → break → **그 회차 산출 전량 폐기**였다
#   (운영자 실물 원장 `2026-08-14T21:35:41|push-fail|4회 소진`). git_land 는 리베이스를 아예 안 쓴다
#   {산출물 스냅샷 → fetch → reset --hard origin/main 재기점 → 재적층 → commit → push · 6회} = 꼬임 자체가 불가.
# ⚠ 전제(그 파일 헤더의 계약) = 인자 경로의 **유일 기록자**여야 한다. 수집함은 폰 레인과 공유지만 누적형
#   스냅샷(다음 회차가 통째로 다시 만든다)이라 재적층이 유실을 만들지 않는다.
# ⚠ PAGES_COALESCE — [CF-Pages-Skip] 접두는 「늦게 떠도 되는 데이터 churn」 전용이고 수집·판정·요약은
#   금지 축이다(CLAUDE.md · check_pages_skip). 그래서 축별로 갈라 부른다: _push = 접두 없음 / _pushd = 접두.
# ⚠⚠ 안 밀린 커밋 보호 — git_land 는 `reset --hard origin/main` 으로 기점을 갈아엎으므로, **아직 원격에
#   안 올라간 로컬 커밋**이 있으면 그걸 통째로 지운다. analyze.sh 는 기사마다 스스로 커밋·푸시하므로
#   그 푸시가 한 번 실패한 상태에서 뒤 스테이지가 착지하면 방금 만든 요약이 조용히 증발한다.
#   → 착지 전에 먼저 밀어보고, 그래도 안 밀렸으면 **이번 착지를 포기**한다(다음 회차가 재시도 = 유실 0).
_gl(){
  if [ "$(git rev-list --count origin/main..HEAD 2>/dev/null || echo 0)" -gt 0 ]; then
    git push -q origin HEAD:main 2>/dev/null || { git fetch -q origin main 2>/dev/null || true; git push -q origin HEAD:main 2>/dev/null || true; }
    if [ "$(git rev-list --count origin/main..HEAD 2>/dev/null || echo 0)" -gt 0 ]; then
      echo "⚠ 안 밀린 로컬 커밋이 남아 이번 착지는 보류(그걸 지우지 않기 위해) — 다음 회차 재시도"; return 1
    fi
  fi
  bash .github/scripts/git_land.sh "$@"
}
_push(){  PAGES_COALESCE=0 _gl "$@" ; }
_pushd(){ _gl "$@" ; }

# ── 파이썬 부품 주문(있으면 즉시 통과 = 설치 0 · 워크플로 `import X || pip install` 관용구의 3단 폴백판) ──
_pipreq(){
  local mod="$1"; shift
  "$PY" -c "import $mod" 2>/dev/null && return 0
  "$PY" -m pip install --quiet "$@" 2>/dev/null \
    || "$PY" -m pip install --user --quiet "$@" 2>/dev/null \
    || "$PY" -m pip install --user --break-system-packages --quiet "$@" 2>/dev/null \
    || { echo "⚠ 부품 설치 실패: $* — 이 스테이지는 건너뜀"; return 1; }
}

# ── 스테이지 주기 원장 + 회차 예산 ────────────────────────────────────────────
# 주기 = 대응 워크플로의 cron 그대로. 예산 = 이 회차가 쓸 수 있는 총 시간(초) — 넘기면 남은 스테이지는
# 다음 회차로 미룬다(주기 원장에 도장을 안 찍으므로 다음 회차가 곧바로 집는다).
LANE_BUDGET="${LANE_BUDGET:-1500}"
STAMP="$HOME/.nomute_lane_stage"; mkdir -p "$STAMP" 2>/dev/null || true
_left(){ echo $(( LANE_BUDGET - SECONDS )); }
_stage(){ # $1=이름 $2=주기(초) $3=최소 예산(초) — 실행할 차례면 rc0
  local now last
  now=$(date +%s); last="$(cat "$STAMP/$1" 2>/dev/null || echo 0)"; case "$last" in ''|*[!0-9]*) last=0;; esac
  [ $(( now - last )) -ge "$2" ] || return 1
  if [ "$(_left)" -lt "$3" ]; then echo "⏭ $1 — 회차 예산 부족(남은 $(_left)s < $3s · 다음 회차)"; return 1; fi
  echo "▶ $1 (경과 ${SECONDS}s)"; return 0
}
_stamp(){ date +%s > "$STAMP/$1" 2>/dev/null || true; }   # 실패해도 찍는다 = 고장난 스테이지가 매 회차를 독점하지 않는다

# ── 스테이지 성적표 — 어느 축이 실제로 일했는지를 **main 에 남긴다**(운영자 260814 «너가 웹앱 상태 실시간으로
#    모니터링하고 직접 수선해»). 로그는 그 컴퓨터에만 남아 원격 세션이 못 읽는다 → 심장박동 파일에 같이 실어
#    보내면 세션이 레포만 보고 「맥에서 재난 수집이 죽었다」를 확정 판독할 수 있다. 실패가 있으면 즉시 커밋한다.
ST=""; ST_BAD=0
_m(){ # $1=이름 $2=rc
  if [ "${2:-0}" = "0" ]; then ST="$ST $1=ok"; else ST="$ST $1=FAIL"; ST_BAD=1; fi
}

# 키 이름 다리 — 운영자 비밀칸 이름이 코드가 읽는 이름과 달라서 워크플로가 폴백으로 이어주던 것(sns-trends.yml env 사본).
export SAFETY_KEY="${KOFIC_NOMUTE_JAENAN:-${SAFETY_KEY:-}}"
export KOBIS_KEY="${KOBIS_KEY:-${KOFIC_NOMUTE_ID:-${KOFIC_NOMUTE:-}}}"
export EX_KEY="${EX_KEY:-${KOFIC_NOMUTE_EX:-}}"

_haveclaude(){ command -v claude >/dev/null 2>&1; }
_noapikey(){ unset ANTHROPIC_API_KEY ANTHROPIC_AUTH_TOKEN 2>/dev/null || true; }   # OAuth를 조용히 덮어쓰는 변수 제거(anthropics/claude-code#34826)

# ── ① 수집(scrape.yml 2스텝 인자 사본) — 폰 16,46분과 교차해 체감 주기를 반으로 ──
"$PY" scraper/knews_scraper.py \
  --categories "${SCRAPE_CATEGORIES:-all}" \
  --out scraper/out \
  --hours "${SCRAPE_HOURS:-24}" \
  --min-cross "${SCRAPE_MIN_CROSS:-2}" \
  --top "${SCRAPE_TOP:-20}" || { _land "collect-fail" "knews_scraper rc≠0(피드·네트워크·의존)"; exit 0; }
"$PY" scraper/to_candidates.py scraper/out/articles.json || { _land "cand-fail" "to_candidates rc≠0"; exit 0; }
"$PY" scraper/snapshot.py >/dev/null 2>&1 || true
cp scraper/out/feed_health_obs.json scraper/obs/feed_health.json 2>/dev/null || true
_push "scrape(pc): 수집함 candidates + 관측 obs 갱신" viewer/candidates.json scraper/obs

# ── ①-b 화재 후속 추적(scrape.yml 「화재 후속 추적」 사본) — 사상자 확인 시 **즉시 폰 알림**.
#    이 축은 화면(정적 빌드)과 무관하게 웹푸시로 바로 닿는다 = 지금 당장 되살아나는 몇 안 되는 기능.
if [ -n "${VAPID_PRIVATE_KEY:-}" ]; then _pipreq pywebpush pywebpush >/dev/null 2>&1 || true; fi
"$PY" scraper/fire_watch.py > /tmp/nm_firewatch.out 2>&1; _m 화재추적 $?
sed -n 's/^PICKED=/화재 큐잉: /p' /tmp/nm_firewatch.out | tail -1
_push "fire-watch: 화재 후속 추적 원장" push/fire_watch.json pending scraper/seen_urls.txt messages

# ── ② 데이터 스테이지(주기 = 각 워크플로 cron 사본) ───────────────────────────
# ②-a 트렌드·재난문자·실검·키워드 알림(sns-trends.yml · 15분 슬롯)
if _stage sns 900 240; then
  # 신선도 게이트(그 워크플로 스텝의 파이썬 한 줄 사본) — 폰 레인이 방금 받아왔으면 이번엔 건너뛴다(중복 수집·IP 차단 회피).
  FRESH=$("$PY" -c "import json,datetime as dt; u=json.load(open('viewer/sns_trends.json'))['updated']; t=dt.datetime.fromisoformat(u); el=(dt.datetime.now(t.tzinfo)-t).total_seconds(); print(1 if 0<=el<1680 else 0)" 2>/dev/null || echo 0)
  if [ "$FRESH" = "1" ]; then
    echo "sns_trends 최근 28분 내 갱신 — 이번 회차 수집 스킵"
  else
    SNS_SUBS="${SNS_SUBS:-1}" SNS_SUBS_BUDGET="${SNS_SUBS_BUDGET:-480}" SNS_REDDIT="${SNS_REDDIT:-1}" \
    SNS_BSKY="${SNS_BSKY:-1}" SNS_SIGNAL="${SNS_SIGNAL:-1}" SNS_XTRENDS="${SNS_XTRENDS:-1}" \
    SNS_HN="${SNS_HN:-1}" SNS_FIN="${SNS_FIN:-1}" \
      timeout 840 "$PY" scraper/sns_trends.py; _m 재난트렌드 $?
  fi
  _pipreq requests requests >/dev/null 2>&1 && { timeout 300 "$PY" scraper/tbs_scraper.py || echo "⚠ tbs 수집 실패 — 직전분 보존"; }
  [ -n "${VAPID_PRIVATE_KEY:-}" ] && { timeout 300 "$PY" .github/scripts/kw_watch.py || true; }
  "$PY" scraper/sns_tr.py || true   # 한글 번역(무키 gtx · 게이트·carry·fail-soft 전부 스크립트 내)
  _pushd "sns-trends: 수집 갱신" viewer/sns_trends.json viewer/tbs_data.json push/kw_sent.json
  if _haveclaude && [ "$(_left)" -ge 300 ]; then
    _noapikey
    bash .github/scripts/sns_brief.sh || true    # 입력 동일 = 스킵(토큰 0) · 실패 = 직전 유지
    bash .github/scripts/sns_sum.sh   || true    # X·스레드 한줄 요약(증분 · 대상 0 = 스킵)
    bash .github/scripts/bsky_brief.sh || true
    _pushd "sns-trends: 브리프·요약 갱신" viewer/sns_trends.json viewer/sns_brief.json
  fi
  _stamp sns
fi

# ②-b 커뮤니티 급상승(social-scan.yml · 30분)
if _stage social 1800 180; then
  _pipreq feedparser feedparser requests pycryptodome >/dev/null 2>&1
  "$PY" scraper/social_burst.py; _m 커뮤니티 $?
  NEW=$("$PY" -c "import json; print(len(json.load(open('scraper/out/social_candidates.json'))))" 2>/dev/null || echo 0)
  if [ "${NEW:-0}" -gt 0 ]; then
    cp scraper/out/social_candidates.json viewer/social_candidates.json
    _pushd "social-scan: SNS 레인 갱신" viewer/social_candidates.json
  else
    echo "⚠ social 수집 0/실패 — 직전분 보존(viewer 미갱신)"   # 워크플로 계약 그대로
  fi
  _stamp social
fi

# ②-c 채널 수집·요약(insta-fetch.yml·fb-fetch.yml · 3시간)
if _stage chan 10800 300; then
  "$PY" .github/scripts/insta_fetch.py; _m 인스타 $?
  "$PY" .github/scripts/fb_fetch.py; _m 페이스북 $?
  "$PY" apps/insta/insta_signals.py    || true
  _pushd "insta: 계정 인사이트 스냅샷 (pc)" apps/insta/data viewer/insta_data.json viewer/insta_covers viewer/fb_data.json messages
  if _haveclaude && [ "$(_left)" -ge 420 ]; then
    _noapikey
    "$PY" .github/scripts/insta_cover_ocr.py || true   # 표지 제목 판독(원장 적중 = 재판독 0)
    "$PY" apps/insta/insta_signals.py || true
    bash .github/scripts/chan_brief.sh || true
    bash .github/scripts/fb_brief.sh   || true
    _pushd "chan: 채널 브리프 갱신 (pc)" apps/insta/data viewer/insta_data.json viewer/chan_brief.json viewer/chan_brief_fb.json viewer/chan_brief_log.jsonl messages
  fi
  _stamp chan
fi

# ②-d 감시(watchdog.yml · 30분)
# ⚠ 폰 알림 기본 OFF — 지금은 「배포 지연」이 **구조적 참**(CF 빌드 정지)이라 매 회차 사실인 경보가 울리는데
#    운영자가 코드로 고칠 자리가 0이다(알림 조치주체 규약 = 조치 불가 알림은 깨우지 않는다). 메시지함 점등·
#    원장 기록은 그대로 = 무증상화 아님. 액션 복구 후 되돌리기 = 환경변수.txt 에 WATCHDOG_NOTIFY=1 한 줄.
if _stage watchdog 1800 180; then
  WATCHDOG_NOTIFY="${WATCHDOG_NOTIFY:-0}" timeout 420 "$PY" scraper/watchdog.py; _m 감시 $?
  "$PY" scraper/brk_misfire.py      || echo "⚠ brk_misfire 스킵"
  "$PY" scraper/grade_fix_report.py || echo "⚠ grade_fix_report 스킵"
  "$PY" scraper/daily_health.py --buried-alert || echo "⚠ 묻힘 감시 스킵"
  _pushd "watchdog: 경보 쿨다운 도장 (pc)" scraper/obs/watchdog_state.json scraper/obs/incidents.jsonl scraper/obs/deploy_obs.jsonl scraper/brk_misfire.json scraper/grade_fix_report.json scraper/grade_fix_reports.jsonl messages
  _stamp watchdog
fi

# ②-e 토큰 계측 롤업(metrics-rollup.yml · 2시간)
if _stage metrics 7200 120; then
  "$PY" shared/token_report.py --prune 3 --write viewer/token-usage.json --quiet; _m 계측 $?
  "$PY" shared/paid_ledger.py --write metrics/paid-usage.json || true
  _pushd "metrics: 토큰 사용 롤업 (pc)" viewer/token-usage.json metrics
  _stamp metrics
fi

# ②-f 유튜브 쿠키 건강검진(yt-cookie-health.yml · 12시간)
if _stage ytcookie 43200 120; then
  "$PY" .github/scripts/yt_cookie_health.py; _m 쿠키검진 $?
  _pushd "yt-cookie: 쿠키 건강 도장 (pc)" messages scraper/obs
  _stamp ytcookie
fi

# ── ③ 판정(breaking-judge.yml 사본 · claude 구독 축) ──────────────────────────
if _haveclaude; then
  nb="$("$PY" .github/scripts/breaking_judge.py --count 2>/dev/null || echo 0)"
  ng="$("$PY" .github/scripts/gate_judge.py --count 2>/dev/null || echo 0)"
  _noapikey
  if [ "${nb:-0}" != "0" ] && [ "$(_left)" -ge 240 ]; then
    BREAKING_MODEL="${BREAKING_MODEL:-claude-opus-5}" "$PY" .github/scripts/breaking_judge.py || _land "judge-b-fail" "breaking_judge rc≠0(로그인·쿼터)"
    _push "AI 판정: 속보 breaking 조기 반영" viewer/candidates.json
  fi
  if [ "${ng:-0}" != "0" ] && [ "$(_left)" -ge 420 ]; then
    GATE_MODEL="${GATE_MODEL:-claude-opus-5}" GATE_EFFORT="${GATE_EFFORT:-max}" \
    GATE_MAX_PER_RUN="${GATE_MAX_PER_RUN:-120}" GATE_REGRADE_QUOTA="${GATE_REGRADE_QUOTA:-20}" \
    GATE_TIMEOUT="${GATE_TIMEOUT:-900}" GATE_CAT_QUOTA="${GATE_CAT_QUOTA:-80}" GATE_SAFE="${GATE_SAFE:-1}" \
    "$PY" .github/scripts/gate_judge.py || _land "judge-g-fail" "gate_judge rc≠0(로그인·쿼터)"
    _push "AI 판정: 속보 breaking · 경중 grade 갱신" viewer/candidates.json metrics
  fi
fi

# ── ④ 요약 제작(news-analyze.yml·news-ask.yml 사본) — **회차의 맨 끝**에 둔다 ──
# ⚠ 자리가 계약이다: analyze.sh 는 기사마다 스스로 커밋·푸시한다(ANALYZE_LAND_EACH). 뒤에 다른 스테이지의
#   git_land(= reset --hard origin/main)가 오면 **아직 안 밀린 요약 커밋을 그대로 지운다**. 그래서 맨 끝.
# ⚠ 자동픽은 기본 끔 = 종전 동작 보존(15분 메트로놈도 analyze=false 였다 · 켜면 교차등장 기사를 자동 분석 = 과금).
#   여기서 소비하는 건 **운영자가 앱에서 누른 픽**(Cloudflare 함수가 pending/ 에 직접 쓴다)과 화재 추적 큐잉분이다.
if _haveclaude && [ "$(_left)" -ge 300 ]; then
  _noapikey
  if [ "${LANE_AUTOPICK:-0}" = "1" ]; then
    "$PY" scraper/to_pending.py || true
    _push "scrape: pending 적재 (RSS 교차등장)" pending scraper/seen_urls.txt
  fi
  _np=$(ls pending/*.txt 2>/dev/null | wc -l | tr -d ' ')
  _na=$(ls asks/*.json  2>/dev/null | wc -l | tr -d ' ')
  if [ "${_np:-0}" != "0" ]; then
    echo "▶ 요약 분석 pending ${_np}건 (남은 예산 $(_left)s)"
    ANALYZE_JOB_DEADLINE="$(( $(_left) - 120 ))" bash .github/scripts/analyze.sh || echo "⚠ 분석 일부 실패(성공분은 이미 착지)"
    [ -n "${VAPID_PRIVATE_KEY:-}" ] && { bash .github/scripts/notify_summary.sh || true; bash .github/scripts/notify_fail.sh || true; }
    _push "analyze: 요약 착지 (pc)" queue pending metrics messages
  fi
  if [ "${_na:-0}" != "0" ] && [ "$(_left)" -ge 300 ]; then
    echo "▶ 요약요청 asks ${_na}건 (남은 예산 $(_left)s)"
    bash .github/scripts/ask.sh || echo "⚠ 요약요청 일부 실패"
    [ -n "${VAPID_PRIVATE_KEY:-}" ] && { bash .github/scripts/notify_summary.sh || true; bash .github/scripts/notify_fail.sh || true; }
    _push "ask: 요약 요청 큐레이션 (pc)" queue asks metrics messages
  fi
  # 카드 프롬프트(텍스트만 · 제미나이 0) — 요약이 새로 생겼을 때만 값이 생긴다.
  if [ "$(_left)" -ge 300 ] && { [ "${_np:-0}" != "0" ] || [ "${_na:-0}" != "0" ]; }; then
    ( unset GDRIVE_SA_JSON GEMINI_API_KEY
      CARD_COV_GUARD="${CARD_COV_GUARD:-1}" CARD_SYS_PROMPT="${CARD_SYS_PROMPT:-1}" \
        bash .github/scripts/cardmake.sh all text ) || echo "⚠ 카드플랜 일부 실패(다이제스트는 보존됨)"
    bash .github/scripts/sweep_stuck.sh || true
    _push "cards: 카드 프롬프트 갱신 (pc)" cards queue metrics
  fi
fi

# ── ⑤ 썸네일 후보(news-analyze.yml thumb 잡 사본 · 제미나이 종량제 + R2) ──────
if [ -n "${GEMINI_API_KEY:-}" ] && [ "$(_left)" -ge 240 ] && _stage thumbs 900 240; then
  _pipreq PIL Pillow >/dev/null 2>&1
  THUMB_MAX_BATCH="${THUMB_MAX_BATCH:-3}" THUMB_SINCE="${THUMB_SINCE:-260703}" THUMB_REF="${THUMB_REF:-1}" \
    "$PY" .github/scripts/thumb_gen.py || echo "⚠ 썸네일 생성 일부 실패(다이제스트·카드는 보존됨)"
  _push "thumbs: AI 썸네일 후보 생성 (pc)" cards
  _stamp thumbs
fi

# ── ⑥ 화면 재배포 신호 — 지금은 죽어 있다(실측 260814 = 훅이 "브랜치를 못 찾는다"고 답한다 = GitHub 연결 끊김).
#    그래도 호출은 남긴다: 연결이 복구되는 순간 이 레인이 곧바로 화면을 다시 굽는다(실패해도 무해).
if [ -n "${CF_DEPLOY_HOOK:-}" ]; then
  curl -fsS -X POST "$CF_DEPLOY_HOOK" -m 20 -o /dev/null 2>/dev/null && echo "화면 재빌드 신호 보냄" || echo "⚠ 화면 재빌드 신호 실패(빌드 연결 끊김 — 정적 화면은 동결 상태)"
fi

SUMM="회차 완료(${SECONDS}s · 판정 b=${nb:-0} g=${ng:-0} · 요약 pending=${_np:-0} ask=${_na:-0}) ·${ST:- 이번 회차 실행 스테이지 없음}"
_land "ok" "$SUMM"
echo "── 스테이지 성적표:${ST:- 없음}"

# ── ⑦ 성적표를 main 에 남긴다 — 로그는 그 컴퓨터에만 있어 원격 세션이 못 읽는다. 실패가 있으면 즉시 커밋해서
#    「맥에서 어느 축이 죽었나」를 레포만 보고 확정 판독할 수 있게 한다(정상 회차는 20분 상한 = 잡음 억제).
_last_beat=$(sed -n 's/.*"epoch":\([0-9]*\).*/\1/p' "$BEAT" 2>/dev/null | head -1); [ -n "$_last_beat" ] || _last_beat=0
if [ "$ST_BAD" = "1" ] || [ $(( $(date +%s) - _last_beat )) -ge 1200 ]; then
  printf '{"epoch":%s,"kst":"%s","host":"%s","secs":%s,"stages":"%s"}\n' \
    "$(date +%s)" "$(TZ=Asia/Seoul date '+%m-%d %H:%M:%S')" "$(hostname 2>/dev/null | cut -d. -f1)" "$SECONDS" "$(printf '%s' "${ST# }" | tr -d '"')" > "$BEAT" 2>/dev/null || true
  git add "$BEAT" 2>/dev/null || true
  git diff --cached --quiet 2>/dev/null || { git commit -q -m "beat(pc): 레인 성적표" 2>/dev/null && git push -q origin HEAD:main 2>/dev/null || true; }
fi
