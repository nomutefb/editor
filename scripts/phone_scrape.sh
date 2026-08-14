#!/usr/bin/env bash
# 폰(termux)/맥 뉴스 수집 크론 진입점 — Actions 우회 대체 레인(운영자 260814).
#
# ⚠ 신설 사유 = 260814 실사고. GitHub 이 **계정 단위로 Actions 를 껐다**
#   (실측 = POST /actions/workflows/scrape.yml/dispatches → `422 Actions has been disabled for this user.`
#    · 검색 API 는 같은 계정에 `User flagged as spammy` 응답 · 계정 updated_at 2026-08-13T17:06:48Z
#    = 마지막 런 17:05:21Z 직후 = 그 순간 전 워크플로 70종이 동시에 멈췄다).
#   외부 15분 메트로놈(cron-job.org)의 422 26연속·자동 비활성은 **증상**이지 원인이 아니다 —
#   그 잡을 되살려도 dispatch 는 계속 422 다. 계정 제재가 풀리기 전까지 Actions 축은 전부 죽어 있다.
#   그런데 **git push 는 살아 있다**(실측 = 제재 후에도 phone-subs 커밋 17:31~00:02 전건 착지) →
#   수집을 러너 밖으로 옮기면 수집함은 계속 살릴 수 있다. 이 파일이 그 우회 레인이다.
#
# ▷ 범위 = scrape.yml 의 **수집 2스텝만**(knews_scraper → to_candidates → candidates.json 커밋).
#   같은 워크플로의 화재 추적·속보 판정 디스패치·자동분석은 전부 `gh workflow run` 축이라
#   Actions 가 꺼진 동안 구조적으로 불가능하다 — 여기 옮겨 담지 않는다(되는 척 금지).
#   → 살아나는 것 = 수집함(신규 뉴스 유입) · 여전히 죽은 것 = 속보 판정·경중·자동분석·제작 전 레인.
#
# ▷ 라이브 도달 경로 = `functions/api/candidates.js`(GitHub main 직독 · 빌드 우회).
#   Cloudflare Pages 빌드도 같은 시각부터 멈춰 있지만(실측 = 라이브 정적 파일이 17:01 커밋에서 정지)
#   뷰어 수집함은 저 API 로 읽으므로 **main 에 커밋만 착지하면 화면에 뜬다**(실측 = /api/candidates 200 · 최신).
#
# 설치(폰에서 1회 · phone_subs.sh 와 같은 crond 를 쓴다):
#   crontab -e →  16,46 * * * * bash ~/nomute-editor/scripts/phone_scrape.sh >> ~/phone_scrape.log 2>&1
#   ⚠ 분(minute)을 phone_subs(*/30 = :00·:30)와 **어긋나게** 잡는다 — 같은 레포의 git 인덱스를 두 잡이
#     동시에 물면 한쪽이 index.lock 에서 죽는다(아래 자가복구가 회수하지만 그 회차 수집은 헛발).
#   ⚠ 의존 = python3 + feedparser·requests.  pip install feedparser requests  (1회)
#   ⚠ 맥도 동일(레포 클론 경로만 맞춘다).
#
# 되돌리기 = 이 crontab 줄 삭제. Actions 가 복구되면 scrape.yml 이 다시 15분 정본 타이머를 쥔다
#   (두 레인이 겹쳐 돌아도 산출은 같은 파일이라 충돌 0 = 늦게 온 쪽이 rebase 로 정렬된다).
set -e
cd "$(dirname "$0")/.."
# 절전 방지 — phone_subs.sh 와 같은 이유·같은 수단(도즈가 crond 를 재우면 이 스크립트는 아예 실행되지 않는다).
command -v termux-wake-lock >/dev/null 2>&1 && termux-wake-lock >/dev/null 2>&1 || true

# ── git 착지 자가복구 + 착지 원장 ────────────────────────────────────────────
#   phone_subs.sh 정본 블록의 **동작 사본**(창작 0). 원장 파일만 갈라 둔다 = 두 레인의 막힌 자리가
#   서로를 덮어쓰면 어느 쪽이 죽었는지 못 읽는다.
LAND="$HOME/.nomute_phone_scrape_land"
_land(){ printf '%s|%s|%s\n' "$(date '+%Y-%m-%dT%H:%M:%S')" "$1" "${2:-}" > "$LAND" 2>/dev/null || true; }
_heal=""
if [ -d .git/rebase-merge ] || [ -d .git/rebase-apply ]; then
  git rebase --abort 2>/dev/null || rm -rf .git/rebase-merge .git/rebase-apply
  _heal="rebase-abort"
fi
if [ -f .git/MERGE_HEAD ]; then git merge --abort 2>/dev/null || rm -f .git/MERGE_HEAD .git/MERGE_MSG; _heal="${_heal:+$_heal+}merge-abort"; fi
if [ -f .git/index.lock ] && [ -n "$(find .git/index.lock -mmin +5 2>/dev/null)" ]; then rm -f .git/index.lock; _heal="${_heal:+$_heal+}stale-lock"; fi
git fetch origin main -q 2>/dev/null || _land "fetch-fail" "네트워크·인증(회선 사망·토큰 만료)"
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

# ── 수집(scrape.yml 「Collect」·「Update 수집함」 2스텝의 인자 사본 = 값 창작 0) ──
python3 scraper/knews_scraper.py \
  --categories "${SCRAPE_CATEGORIES:-all}" \
  --out scraper/out \
  --hours "${SCRAPE_HOURS:-24}" \
  --min-cross "${SCRAPE_MIN_CROSS:-2}" \
  --top "${SCRAPE_TOP:-20}" || { _land "collect-fail" "knews_scraper rc≠0(피드·네트워크·의존)"; exit 0; }
python3 scraper/to_candidates.py scraper/out/articles.json || { _land "cand-fail" "to_candidates rc≠0"; exit 0; }
# 관측 누적 — 워크플로와 동일하게 비치명(실패해도 수집을 안 깬다).
python3 scraper/snapshot.py >/dev/null 2>&1 || true
cp scraper/out/feed_health_obs.json scraper/obs/feed_health.json 2>/dev/null || true

# ── 착지(명시 경로만 add = 무경로 -A 금지) ──────────────────────────────────
git add viewer/candidates.json scraper/obs 2>/dev/null || { _land "add-fail" "인덱스 잠김·권한"; exit 0; }
git diff --cached --quiet && { _land "ok" "무변동"; exit 0; }
git commit -q -m "scrape(phone): 수집함 candidates + 관측 obs 갱신" 2>/dev/null || { _land "commit-fail" "pre-commit 게이트(check_refs)·훅"; exit 0; }
for i in 1 2 3 4; do
  git push -q origin HEAD:main 2>/dev/null && { _land "ok" "착지"; exit 0; }
  echo "push 재시도 $i"; sleep $((2**i))
  git fetch origin main -q 2>/dev/null || true
  git rebase -q origin/main 2>/dev/null || { git rebase --abort 2>/dev/null || true; break; }
done
_land "push-fail" "4회 소진(non-ff·인증 만료)"
# rc=1 로 끝낸다(phone_subs.sh 계약 동축 = 거짓 성공 금지 · cron 로그·phone_check 가 실패로 읽는다).
echo "push 실패(재시도 소진) — 다음 주기가 origin/main 정렬 후 재수집(수집함은 누적형 = 유실 개념 없음)"
exit 1
