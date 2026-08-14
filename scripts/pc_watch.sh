#!/usr/bin/env bash
# 착지 감시창 — main 에 뭐가 들어오는지 30초마다 갱신해 보여준다(운영자 260814 「들어가는거 모니터링 창이 하나 있어야할듯」).
# 실행 = scripts/pc_watch.bat 더블클릭(윈도우) · 맥/리눅스 = bash scripts/pc_watch.sh · 종료 = 창 닫기.
# 시각은 전부 KST 로 통일해 표시한다(커밋마다 시간대가 달라 섞어 보이면 읽는 사람이 헷갈린다).
cd "$HOME/nomute-editor" 2>/dev/null || cd "$(dirname "$0")/.." || exit 1
while :; do
  git fetch origin main -q 2>/dev/null
  clear 2>/dev/null || printf '\033c'
  echo "══════ 노뮤트 착지 감시창 · $(TZ=Asia/Seoul date '+%m-%d %H:%M:%S') KST · 30초마다 갱신 ══════"
  echo
  TZ=Asia/Seoul git log origin/main -18 --date=format-local:'%m-%d %H:%M' --pretty=format:'%cd  %s' 2>/dev/null \
    | sed -e 's/scrape(phone):.*/📱 폰 기사 수집 착지/' \
          -e 's/scrape(pc):.*/🖥 PC 기사 수집 착지/' \
          -e 's/phone-subs:.*/📱 폰 구독·레딧·재난 착지/' \
          -e 's/AI 판정:.*/🧠 속보·경중 판정 착지/' \
          -e 's/thumb upload.*/🖼 카드 업로드 착지/'
  echo
  h(){ git log origin/main --since='60 minutes ago' --oneline 2>/dev/null | grep -c "$1"; }
  echo "── 최근 1시간: 폰수집 $(h 'scrape(phone)')건 · PC수집 $(h 'scrape(pc)')건 · 구독 $(h 'phone-subs')건 · 판정 $(h 'AI 판정')건"
  echo "   (판정·PC수집이 0에 머물면 PC 레인 확인 필요 · 창 닫으면 감시만 꺼질 뿐 레인은 계속 돈다)"
  sleep 30
done
