#!/usr/bin/env bash
# PC 2단 안전장치 1탄 — 수집 + 속보/경중 판정 레인(운영자 260814 "내부 pc나 기기를 통해 돌릴 수 있는 배선을 만들어서 … 풀리더라도 2단으로 갈거임. 안전장치")
# 왜: 260814 GitHub 계정 단위 Actions 정지(CLAUDE.md 🚨 항목)로 판정·분석·제작 레인이 전멸했다.
#   폰 레인(phone_scrape.sh)은 수집만 되살린다 — 이 레인은 수집(폰과 교차)에 더해 **속보 판정·경중 채점**까지 PC 에서 돌린다.
#   Actions 복구 후에도 유지 = 2단 안전장치(운영자 확정) · 산출 파일이 워크플로와 동일(candidates.json·metrics)이라 겹쳐 돌아도 충돌 0.
# 실행 환경 = 윈도우 Git-Bash(작업 스케줄러 5분(운영자 260814 «5분마다 도는 게 맞는 것 같은데» — PC 자체 시계라 외부 제약 0 · 판정 비용 불변{도장 캐시가 기사당 1회를 보장} · 겹침 = mkdir 잠금이 거른다 · ⚠ Actions 복구 후 배포 공장 부하 재검토 각주) · 설치 = scripts/pc_setup.bat 더블클릭 1회) · WSL/리눅스에서도 그대로 돈다.
# 정본 관계(값 창작 0): 수집 2스텝 = scrape.yml 「Collect」·「Update 수집함」 인자 사본(phone_scrape.sh 동문) ·
#   판정 = breaking-judge.yml 스텝 사본(BREAKING_MODEL·GATE_* env = 그 파일 260810 정본값 그대로).
# v1 이 안 하는 것(이유 명기 = 조용한 반쪽 금지):
#   ⓐ 긴급 웹푸시 — VAPID 키가 GitHub Secrets 전용이라 PC 에 없다(화면 배지·경중 정렬은 판정만으로 산다)
#   ⓑ 자동픽·자동분석 — GEMINI_API_KEY·R2 키 동일 사유(요약 제작은 Actions 복구 대기)
#   ⓒ 사건 묶기(group_judge) — 정본이 카나리아 OFF(GROUP_ON 미설정)라 그대로 둔다.
# 착지 원장 = ~/.nomute_pc_lane_land (phone_scrape 원장 문법 사본 · 파일만 갈라 둔다 = 두 레인의 막힌 자리 구분).
set -u
cd "$HOME/nomute-editor" 2>/dev/null || { echo "레포 없음: ~/nomute-editor — pc_setup.bat 를 먼저 실행"; exit 1; }

LAND="$HOME/.nomute_pc_lane_land"
_land(){ printf '%s|%s|%s\n' "$(date '+%Y-%m-%dT%H:%M:%S')" "$1" "${2:-}" > "$LAND" 2>/dev/null || true; }

# ── 동시 실행 잠금(mkdir = 윈도우 Git-Bash 에 flock 이 없다) — 경중 채점이 콜당 최대 900s 라 5분 주기를 넘길 수 있다.
#    앞 회차가 아직 채점 중이면 이번 회차는 조용히 물러난다(claude 콜 이중 발사·git 경합 차단) · 90분 넘은 잠금 = 죽은 회차로 보고 회수.
LOCK="$HOME/.nomute_pc_lane.lock"
if ! mkdir "$LOCK" 2>/dev/null; then
  if [ -n "$(find "$LOCK" -maxdepth 0 -mmin +90 2>/dev/null)" ]; then rmdir "$LOCK" 2>/dev/null || true; mkdir "$LOCK" 2>/dev/null || { _land "lock-busy" "회수 직후 경합"; exit 0; }
  else _land "lock-busy" "앞 회차 진행 중(정상)"; exit 0; fi
fi
trap 'rmdir "$LOCK" 2>/dev/null' EXIT

# ── 환경(윈도우 = 파이썬이 python 이름 · 셸 PATH 가 작업 스케줄러에서 빈약) — pc_setup.bat 가 구운 env 를 먼저 읽는다.
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
[ -n "$PY" ] || { _land "no-python" "진짜 python 미발견(껍데기 제외) — pc_setup.bat 재실행"; exit 1; }
git config user.email >/dev/null 2>&1 || { git config user.name "nomute-pc"; git config user.email "nomute-pc@local"; }

# ── git 착지 자가복구(phone_scrape.sh 정본 블록의 동작 사본 · 창작 0) ─────────
_heal=""
if [ -d .git/rebase-merge ] || [ -d .git/rebase-apply ]; then
  git rebase --abort 2>/dev/null || rm -rf .git/rebase-merge .git/rebase-apply
  _heal="rebase-abort"
fi
if [ -f .git/MERGE_HEAD ]; then git merge --abort 2>/dev/null || rm -f .git/MERGE_HEAD .git/MERGE_MSG; _heal="${_heal:+$_heal+}merge-abort"; fi
if [ -f .git/index.lock ] && [ -n "$(find .git/index.lock -mmin +5 2>/dev/null)" ]; then rm -f .git/index.lock; _heal="${_heal:+$_heal+}stale-lock"; fi
git fetch origin main -q 2>/dev/null || { _land "fetch-fail" "네트워크·인증(회선 사망·로그인 만료)"; exit 0; }
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

# ── 공용 착지 함수(명시 경로만 add · 새 커밋만 = --amend 금지 계약) ──────────
_push(){ # $1=커밋 메시지 · $2…=add 경로들 · 무변동 = 조용히 0 · 경로별 개별 add(metrics 처럼 아직 없는 경로가 전체를 못 죽이게 = 판정 yml 「|| true」 문법 사본)
  local msg="$1"; shift
  for _p in "$@"; do git add "$_p" 2>/dev/null || true; done
  git diff --cached --quiet && return 0
  git commit -q -m "$msg" 2>/dev/null || { _land "commit-fail" "훅·정체"; return 1; }
  for i in 1 2 3 4; do
    git push -q origin HEAD:main 2>/dev/null && return 0
    sleep $((2**i)); git fetch origin main -q 2>/dev/null || true
    git rebase -q origin/main 2>/dev/null || { git rebase --abort 2>/dev/null || true; break; }
  done
  _land "push-fail" "4회 소진(non-ff·인증 만료)"; return 1
}

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
_push "scrape(pc): 수집함 candidates + 관측 obs 갱신" viewer/candidates.json scraper/obs || exit 0

# ── ② 판정(breaking-judge.yml 사본 · claude 구독 축) — 미로그인·미설치면 수집만 하고 물러난다(fail-soft) ──
command -v claude >/dev/null 2>&1 || { _land "ok" "수집 착지 · 판정 생략(claude 미설치)"; exit 0; }
nb="$("$PY" .github/scripts/breaking_judge.py --count 2>/dev/null || echo 0)"
ng="$("$PY" .github/scripts/gate_judge.py --count 2>/dev/null || echo 0)"
if [ "${nb:-0}" = "0" ] && [ "${ng:-0}" = "0" ]; then _land "ok" "수집 착지 · 판정 대기 0건"; exit 0; fi
unset ANTHROPIC_API_KEY ANTHROPIC_AUTH_TOKEN 2>/dev/null || true

if [ "${nb:-0}" != "0" ]; then
  BREAKING_MODEL="${BREAKING_MODEL:-claude-opus-5}" "$PY" .github/scripts/breaking_judge.py || _land "judge-b-fail" "breaking_judge rc≠0(로그인·쿼터)"
  _push "AI 판정: 속보 breaking 조기 반영" viewer/candidates.json || true
fi
if [ "${ng:-0}" != "0" ]; then
  GATE_MODEL="${GATE_MODEL:-claude-opus-5}" GATE_EFFORT="${GATE_EFFORT:-max}" \
  GATE_MAX_PER_RUN="${GATE_MAX_PER_RUN:-120}" GATE_REGRADE_QUOTA="${GATE_REGRADE_QUOTA:-20}" \
  GATE_TIMEOUT="${GATE_TIMEOUT:-900}" GATE_CAT_QUOTA="${GATE_CAT_QUOTA:-80}" GATE_SAFE="${GATE_SAFE:-1}" \
  "$PY" .github/scripts/gate_judge.py || _land "judge-g-fail" "gate_judge rc≠0(로그인·쿼터)"
fi
_push "AI 판정: 속보 breaking · 경중 grade 갱신" viewer/candidates.json metrics || exit 0
_land "ok" "수집+판정 착지(b=$nb g=$ng)"
