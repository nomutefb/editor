#!/usr/bin/env bash
# 레인 원격 검문 — 「걷은 걸 **어느 저장소로** 보내는가」 한 축의 정본 1곳(사본 금지).
#
# ⚠ 신설 사유 = 260816 실사고. 계정 이관(260816) 뒤 폰(Termux) 클론만 옛 저장소를 그대로 보고 있었고,
#   그 상태에서 **모든 진단이 초록이었다** — crond 살아있음 · 수집 성공 · git 착지 성공 · push 성공.
#   실제로 성공한 게 맞다(옛 저장소로). 다만 화면(edit.nomute.kr)이 읽는 곳은 새 저장소라
#   폰이 걷은 것은 화면에 한 건도 안 떴다. 실측 = 새 저장소 main 에 `(phone)` 커밋 0건,
#   같은 기간 PC 레인 `(pc)` 커밋은 정상 착지. 증상이 「아무 일도 안 일어남」 하나뿐이라
#   운영자 눈이 유일한 검출기였다(insta-thumb-miss·brk_misfire 동축).
#   기존 자가복구는 리베이스 중단·인덱스 잠김·미푸시 적체까지 전부 보는데
#   **주소가 맞는지는 축 자체가 없었다** → 이 파일이 그 축이다.
#
# 쓰는 곳 = 레인 스크립트가 `. scripts/lane_origin.sh` 로 읽어 쓴다(폰 phone_scrape·phone_subs · 진단기 phone_check).
# 값 정본 = 아래 두 줄. 저장소가 또 옮겨가면 여기만 고친다.
NOMUTE_ORIGIN_SLUG="nomutefb/editor"
NOMUTE_ORIGIN_URL="https://nomutefb@github.com/nomutefb/editor"

# 인증 대기로 크론이 멈추는 것 방지 — 자격이 없으면 **물어보지 말고 즉시 실패**해야
# 다음 회차가 정상적으로 돌아온다(물어보면 크론 잡이 입력을 기다리며 영영 붙들려 있는다).
export GIT_TERMINAL_PROMPT=0

# 지금 origin 주소에서 주인/이름만 뽑는다(https·ssh·.git 꼬리 전부 같은 값으로 수렴).
lane_origin_slug(){
  local u
  u="$(git remote get-url origin 2>/dev/null || true)"
  u="${u%.git}"
  u="${u#*github.com}"
  u="${u#:}"
  u="${u#/}"
  printf '%s' "$u"
}

# 검문 = 다른 저장소를 보고 있으면 정본으로 갈아끼운다.
#   0 = 이미 정본  ·  1 = 갈아끼웠다(옛 주소는 $LANE_ORIGIN_WAS)  ·  2 = 갈아끼우기 실패
# ⚠ 자격(토큰)은 건드리지 않는다 — 주소만 고친다. 새 계정 토큰이 없으면 푸시가 실패하고
#   그 사유가 착지 원장에 남는다(거짓 성공 금지).
lane_origin_check(){
  LANE_ORIGIN_WAS="$(lane_origin_slug)"
  [ -z "$LANE_ORIGIN_WAS" ] && return 0                     # 원격이 없다 = 이 축의 대상 아님
  [ "$LANE_ORIGIN_WAS" = "$NOMUTE_ORIGIN_SLUG" ] && return 0
  git remote set-url origin "$NOMUTE_ORIGIN_URL" 2>/dev/null || return 2
  return 1
}
