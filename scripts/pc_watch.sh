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
          -e 's/thumb upload.*/🖼 카드 업로드 착지/' \
          -e 's/.*sns-trends:.*/🌏 실검·재난문자·트렌드 착지/' \
          -e 's/.*social-scan:.*/💬 커뮤니티 급상승 착지/' \
          -e 's/.*fire-watch:.*/🔥 화재 후속 추적 착지/' \
          -e 's/.*\(insta\|chan\):.*/📸 채널 수집·요약 착지/' \
          -e 's/.*watchdog:.*/🛡 감시 도장 착지/' \
          -e 's/.*metrics:.*/📊 토큰 계측 착지/' \
          -e 's/analyze:.*/📝 뉴스 요약 착지/' \
          -e 's/ask:.*/📝 요약 요청 착지/' \
          -e 's/cards:.*/🎞 카드 프롬프트 착지/' \
          -e 's/thumbs:.*/🖼 썸네일 후보 착지/'
  echo
  h(){ git log origin/main --since='60 minutes ago' --oneline 2>/dev/null | grep -c "$1"; }
  echo "── 최근 1시간: 폰수집 $(h 'scrape(phone)')건 · PC수집 $(h 'scrape(pc)')건 · 구독 $(h 'phone-subs')건 · 판정 $(h 'AI 판정')건 · 요약 $(h 'analyze:')건"
  echo "   (판정·PC수집이 0에 머물면 PC 레인 확인 필요 · 창 닫으면 감시만 꺼질 뿐 레인은 계속 돈다)"
  # 이 컴퓨터의 레인 상태 — 착지 원장 + 스테이지 주기 원장(언제 마지막으로 돌았나). 다른 컴퓨터 것은 안 보인다.
  echo
  echo "── 이 컴퓨터 레인: $(cat "$HOME/.nomute_pc_lane_land" 2>/dev/null || echo '기록 없음')"
  if [ -d "$HOME/.nomute_lane_stage" ]; then
    _now=$(date +%s); _out=""
    for _f in "$HOME/.nomute_lane_stage"/*; do
      [ -f "$_f" ] || continue
      _v="$(cat "$_f" 2>/dev/null)"; case "$_v" in ''|*[!0-9]*) continue;; esac
      _out="$_out $(basename "$_f")=$(( (_now - _v) / 60 ))분전"
    done
    [ -n "$_out" ] && echo "   스테이지 마지막 실행:$_out"
  fi
  sleep 30
done
