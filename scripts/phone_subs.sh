#!/usr/bin/env bash
# 폰(termux)/맥 구독 수집 크론 진입점(운영자 260712 "ㄱ") — X·인스타·스레드를 수집해 main에 직푸시.
# 기존 기사 공유 경로(termux-share·queue-handler)와 완전 분리(산출 = viewer/sns_subs_phone.json 한 파일).
# 설치(폰에서 1회):
#   pkg install python cronie termux-services termux-api && sv-enable crond
#   crontab -e →  */30 * * * * bash ~/nomute-editor/scripts/phone_subs.sh >> ~/phone_subs.log 2>&1
#   (레포 클론 경로가 다르면 위 경로만 맞춰줘 · 안드로이드 설정 > 배터리 > Termux 제한 없음)
#   ⚠ 야간 정지 방지 3층(운영자 260727) — 아래 termux-wake-lock은 ③층이고, ①②는 폰에서 1회 손으로 해야 한다:
#     ① Termux:API 앱 설치(F-Droid · `pkg install termux-api`는 CLI만 깔린다 = 앱이 없으면 웨이크락 무동작)
#     ② 안드 설정 > 배터리 > Termux = '제한 없음'(도즈가 앱 자체를 죽이는 축 · 웨이크락으로 못 막는다)
#     ③ 이 스크립트의 termux-wake-lock(아래) = CPU 재우기 방지 · 셋 다 있어야 새벽에 안 끊긴다
# 맥 설치(1회 · 운영자 260712 "맥에서 크롬 통해 접근" — 스레드는 가정 IP가 유일 공급원):
#   레포 클론 후  crontab -e →  */30 * * * * bash ~/nomute-editor/scripts/phone_subs.sh >> ~/phone_subs.log 2>&1
#   (macOS 기본 python3·git으로 동작 = 추가 패키지 0 · 크롬 로그인과 무관한 게스트 HTML 파싱이라 브라우저 불요)
set -e
_SELF_SUM="$(cksum "$0" 2>/dev/null | cut -d' ' -f1 || true)"   # 자기 갱신 안전의 짝(아래 재시작 블록)
cd "$(dirname "$0")/.."
# 절전 방지(운영자 260727 "폰 안 쓰는 시간대에도 살아있게 해야되겠는데") — 안드로이드 도즈가 crond를 재우면
# 이 스크립트는 **아예 실행되지 않는다**(260727 판례: 00:32~02:25 2시간 공백 = 스레드·인스타가 그동안 굶음).
# termux-wake-lock = CPU 웨이크락 획득 후 **의도적으로 해제 안 함**(다음 30분 주기까지 crond 생존 = 야간 연속성).
#   해제하면 즉시 도즈로 복귀 = 같은 공백 재발이라 trap 해제를 안 건다. 배터리 소모 증가는 감수(운영자 선택).
#   ⚠ 요구: `pkg install termux-api` + Termux:API 앱. 미설치·맥 = 조용히 건너뜀(fail-soft = 종전 동작 불변).
command -v termux-wake-lock >/dev/null 2>&1 && termux-wake-lock >/dev/null 2>&1 || true
# 폰 로컬 시크릿(git 밖 · cron은 .bashrc 미로드라 여기서 source) — 재난문자 등 키 필요 소스용.
# 1회 설정(폰):  echo "export SAFETY_KEY='발급받은_재난문자_서비스키'" > ~/.nomute_phone_env
# 부계 세션쿠키(선택 · Meta 로그인월 우회 — 무인증은 러너·컨테이너·폰 전부 429 실측 260726):
#   echo 'export THREADS_COOKIE="sessionid=…; ds_user_id=…"' >> ~/.nomute_phone_env
#   echo 'export INSTA_COOKIE="sessionid=…; ds_user_id=…; csrftoken=…"' >> ~/.nomute_phone_env   # 운영자 260726 · 미설정 = 게스트(종전 동작)
#   echo 'export INSTA_UA="chrome://version 의 사용자 에이전트 전체 문자열"' >> ~/.nomute_phone_env   # 쿠키 발급 브라우저 UA 고정(260729 「useragent mismatch」 — 메타가 세션을 발급 UA에 묶는다 · 쿠키와 짝 필수)
#   echo 'export THREADS_UA="위와 같은 UA 문자열"' >> ~/.nomute_phone_env   # ⚠ 스레드도 **같은 메타 정책** — 260729 봉합이 인스타에만 이식돼 스레드는 쿠키가 매번 무소득이었다(260805 실측 5계정 전건) · THREADS_COOKIE와 **한 쌍**으로 넣어라(하나만 갈면 또 어긋난다 · 쿠키·UA는 같은 브라우저에서 같이 뽑는다)
#   ⚠ 반드시 부계로(자동화 감지 밴 리스크 = 본계 금지) · 이 파일은 git 밖 = 레포 커밋 0
#   ▶ 잘 들어오는지 폰에서 바로 확인:  bash scripts/insta_check.sh   (쿠키·쿨다운 상태 + 실제 1콜 진단 · 운영자 260731)
# 보안 가드(평의회 260723 #6) — env(쿠키·키 평문 집결)가 600 아니면 강제(termux -c / Mac -f 분기) · 전체 쿠키jar 유출 사고 재발 봉인
[ -f "$HOME/.nomute_phone_env" ] && { [ "$(stat -c %a "$HOME/.nomute_phone_env" 2>/dev/null || stat -f %A "$HOME/.nomute_phone_env" 2>/dev/null)" = 600 ] || chmod 600 "$HOME/.nomute_phone_env"; . "$HOME/.nomute_phone_env"; }
# ── git 착지 자가복구 + 착지 원장(운영자 260806 "수집을 매번 고치는데 왜 재발하냐" · 8인 평의회) ────
#  ⚠ 신설 사유 = 260806 실사고 — crond ✅(pid 28097 생존) · 손으로 돌리니 수집도 ✅(insta 23·threads 18·
#    tiktok 24·reddit 12)인데 산출물만 **31시간 9분 정지**(= 30분 주기 62회 헛발). 고장 지점이 크론도
#    수집도 아닌 **그 사이의 git 착지**인데 이 스크립트엔 착지 복구가 **한 줄도 없었다**(실측) → 한 번
#    눌어붙으면 매 회차가 같은 자리에서 죽고 사람이 폰을 열기 전엔 안 풀린다. 260805 봉합은 진단
#    (phone_check ⑥)만 늘리고 복구는 안 만들었다 = 운영자 지적 "이미 소 잃고 외양간 고치는 거임".
#  ▷ 원칙 = **산출물은 30분마다 재생성되는 휘발성 = 로컬 커밋을 지킬 이유가 0** → 막히면 붙들지 말고
#    origin/main 으로 정렬하고 다시 걷는다(하단 "유실 개념 없음" 주석과 동축 · 데이터 손실 0).
#  ▷ 착지 원장은 **git 밖**($HOME)이라 착지가 막혀도 쓰인다 — 다음 회차 python 이 읽어 산출물
#    `_cover.landing` 에 실어보낸다 → watchdog 이 "크론 확인해" 대신 **막힌 자리 이름**을 말한다
#    (= 레포에 "파일 나이" 1비트만 도착하던 관측 구멍 봉합 · 평의회6 판정 BLIND 92).
LAND="$HOME/.nomute_phone_land"
_land(){ printf '%s|%s|%s\n' "$(date '+%Y-%m-%dT%H:%M:%S')" "$1" "${2:-}" > "$LAND" 2>/dev/null || true; }
_heal=""
# 원격 검문(260816 실사고 봉합) — 걷은 걸 **어느 저장소로** 보내는지가 여태 축 자체로 없었다.
#   계정 이관 뒤 폰만 옛 저장소를 보고 있었고 그동안 모든 진단이 초록이었다(옛 곳으로 실제 성공했으니까).
#   화면이 읽는 곳은 새 저장소라 폰이 걷은 건 한 건도 화면에 안 떴다. 정본·사유 = scripts/lane_origin.sh
. scripts/lane_origin.sh 2>/dev/null || true
if command -v lane_origin_check >/dev/null 2>&1; then
  _oc=0; lane_origin_check || _oc=$?
  if [ "$_oc" = 1 ]; then
    echo "🔀 보내는 곳이 정본이 아니었다 → 갈아끼웠다: $LANE_ORIGIN_WAS → $NOMUTE_ORIGIN_SLUG"
    _heal="origin-fix($LANE_ORIGIN_WAS→$NOMUTE_ORIGIN_SLUG)"
  elif [ "$_oc" = 2 ]; then
    _land "origin-fail" "원격 주소를 정본으로 못 바꿨다(권한·잠김)"
  fi
fi
#  ⚠ abort 실패 폴백 = 킬테스트 K2 실측 봉합 — 잔류가 **껍데기**(프로세스가 중간에 죽어 메타가 불완전)면
#    `git rebase --abort` 자체가 rc≠0로 실패하고 디렉터리가 그대로 남는다 = 자가복구가 통째로 무력해진다.
#    (K1 실측 = 정상 중단은 abort로 풀림 · K2 실측 = 껍데기는 abort 실패 후 잔류 → 강제 제거가 유일한 해)
if [ -d .git/rebase-merge ] || [ -d .git/rebase-apply ]; then
  git rebase --abort 2>/dev/null || rm -rf .git/rebase-merge .git/rebase-apply
  _heal="rebase-abort"
fi
if [ -f .git/MERGE_HEAD ]; then git merge --abort 2>/dev/null || rm -f .git/MERGE_HEAD .git/MERGE_MSG; _heal="${_heal:+$_heal+}merge-abort"; fi
# stale index.lock = 5분↑ 된 것만 — 진짜 실행 중인 git 은 안 건드린다(크론 주기 30분이라 5분이면 충분)
if [ -f .git/index.lock ] && [ -n "$(find .git/index.lock -mmin +5 2>/dev/null)" ]; then rm -f .git/index.lock; _heal="${_heal:+$_heal+}stale-lock"; fi
git fetch origin main -q 2>/dev/null || _land "fetch-fail" "네트워크·인증(회선 사망·토큰 만료)"
_unp="$(git rev-list --count origin/main..HEAD 2>/dev/null || echo 0)"
_br="$(git symbolic-ref -q --short HEAD 2>/dev/null || echo '-')"
if [ "$_br" != "main" ] || [ "${_unp:-0}" -ge 3 ]; then
  git checkout -q -B main origin/main 2>/dev/null || true   # detached·3회↑ 적체 = 정상 rebase로 못 푸는 상태
  _heal="${_heal:+$_heal+}realign(br=$_br,unpushed=$_unp)"
elif ! git pull -q --rebase origin main 2>/dev/null; then   # 최신 계정 목록(sns_accounts.json) 동기
  git rebase --abort 2>/dev/null || true; git reset --hard -q origin/main 2>/dev/null || true
  _heal="${_heal:+$_heal+}pull-heal"
fi
[ -n "$_heal" ] && echo "🔧 git 착지 자가복구: $_heal"

# ⚠⚠ 자기 갱신 안전(pc_lane.sh 정본 블록의 사본 = 같은 병의 형제 전건) — 이 스크립트는 자기 자신을 바꾸는
#   git pull 을 자기 실행 도중에 돌린다. 셸은 파일을 바이트 위치를 기억하며 조금씩 읽으므로 그 사이 길이가
#   바뀌면 남은 절반을 엉뚱한 위치부터 읽어 문법 오류·반쪽 실행이 난다 → 바뀌었으면 새 파일로 다시 시작.
if [ "${NOMUTE_LANE_REEXEC:-0}" != "1" ]; then
  _sum_now="$(cksum "$0" 2>/dev/null | cut -d' ' -f1 || true)"
  if [ -n "${_SELF_SUM:-}" ] && [ -n "$_sum_now" ] && [ "$_sum_now" != "$_SELF_SUM" ]; then
    echo "♻ 레인 코드가 갱신됐다 — 새 코드로 이번 회차를 다시 시작한다"
    NOMUTE_LANE_REEXEC=1 exec bash "$0" "$@"
  fi
fi

python3 scripts/phone_subs.py || { _land "collect-fail" "python rc≠0(쿠키·429·네트워크)"; exit 0; }
# ⚠ 원장 동반 착지(260809 실사고 봉합 · 관측 구멍 3세대) — `push/threads_ck.jsonl` 은 260806에
#   「러너 로그는 흘러가서 소실된다 → 원장에 쌓으면 회차 분포가 곧 판별기가 된다」는 근거로 신설됐는데,
#   그 원장을 **커밋하는 줄이 없어서** 폰 로컬에만 쌓이고 세션에는 영영 도달하지 않았다(실측 = 레포에 파일 0).
#   결과 = 주석은 "사람이 아무것도 안 해도 시간이 답을 만든다"고 단언하는데 실제로는 답이 배달될 경로가 없다
#   = 1세대(폴백이 사유를 가로챔)·2세대(로그 소실)와 **같은 병의 3세대**. 명시 경로만 add(무경로 -A 금지 = STT ⓕ).
git add viewer/sns_subs_phone.json 2>/dev/null || { _land "add-fail" "인덱스 잠김·권한"; exit 0; }
[ -f push/threads_ck.jsonl ] && git add push/threads_ck.jsonl 2>/dev/null || true
git diff --cached --quiet && { _land "ok" "무변동"; exit 0; }   # 변동 없음 = 무커밋
git commit -q -m "phone-subs: 구독·레딧·재난문자 폰 수집" 2>/dev/null || { _land "commit-fail" "pre-commit 게이트(check_refs)·훅"; exit 0; }
for i in 1 2 3 4; do
  git push -q origin HEAD:main 2>/dev/null && { _land "ok" "착지"; exit 0; }
  echo "push 재시도 $i"; sleep $((2**i))
  git fetch origin main -q 2>/dev/null || true
  # -X theirs = 리베이스에서 **이쪽 커밋 우선**(구독·트렌드 산출은 회차마다 통째로 다시 만드는 스냅샷이라 이게 정답).
  # ⚠ 260814 실측 봉합: 무옵션이면 같은 파일을 쥔 다른 레인과 충돌해 그 회차 수집이 통째로 버려졌다(형제 전건 봉합).
  git rebase -q -X theirs origin/main 2>/dev/null || { git rebase --abort 2>/dev/null || true; break; }   # 그래도 못 붙으면 놓는다(다음 회차 realign 회수)
done
_land "push-fail" "4회 소진(non-ff·인증 만료)"
# ⚠ rc=1 로 끝낸다(구판은 rc=0 = **거짓 성공** — cron·phone_check ⑦ 이 정상 종료로 읽어 실패가 안 보였다)
echo "push 실패(재시도 소진) — 다음 주기가 origin/main 정렬 후 재수집(트렌드는 30분 뒤 재수집 = 유실 개념 없음)"
exit 1
