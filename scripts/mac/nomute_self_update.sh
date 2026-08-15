#!/usr/bin/env bash
# 맥 실행기 자기갱신 v2(260815 밤 코워크) — 깃 정본 scripts/mac/*.sh → ~/ 설치본.
#
# 신설 사유: scripts/mac/README.md 가 14:20 정본화에서 「1분 틱이 감지해 ~/에 자동 배포」라 선언했는데
#   그 배선이 실제로 없었다(grep -rn "scripts/mac" 홈·레포 전 스크립트 0건) → 그날 수정이 전부 ~/ 에만
#   쌓여 6종이 갈렸고 CT 매핑 봉합은 이 맥 한 대에만 존재했다(깃 재설치 시 소멸).
#
# ⚠⚠ v1 이 라이브 수정을 파괴했다(22:17:40 실사고 · 이 파일의 존재 이유보다 중요한 교훈).
#   v1 술어 = 「깃 ≠ 홈 이면 깃으로 덮는다」. 그 순간 다른 세션이 ~/nomute_wf_driver.sh 에 막 넣은
#   wf_land 폴백(14줄 + 호출 4곳)이 60초 만에 증발했다. 백업(계약 ③)이 없었으면 영구 소실이었다.
#   → v2 술어 = 「**깃 파일이 지난번 이후 바뀌었을 때만** 설치한다」.
#      깃이 그대로면 홈이 뭐가 됐든 손대지 않는다 = 라이브 핫픽스가 살아남는다.
#      깃에 새 판이 올라오면 그때 이긴다 = README 가 약속한 배포는 그대로 성립한다.
#
# 계약 6개(하나라도 빠지면 이 스크립트가 레인을 벽돌로 만들거나 남의 작업을 지운다):
#   ① 도장 술어 — 깃 파일 md5 가 지난 설치 때와 같으면 **완전 무시**. 홈과 달라도 안 건드린다.
#   ② 첫 관측 무설치 — 도장이 없는 파일은 도장만 찍고 설치하지 않는다(도입 순간 라이브 덮어쓰기 방지).
#      단 홈에 파일 자체가 없으면 설치한다(신규 배포는 정상 경로).
#   ③ 문법 게이트 — 설치 전 /bin/bash -n. 레인은 launchd plist(/bin/bash -lc)+PATH 순서 때문에
#      bash 3.2.57 로 돈다. homebrew 5.3·zsh 로 재면 3.2 전용 파싱 사고를 통과시킨다.
#   ④ 원자 설치 — 같은 디렉터리 .staged → mv. 제자리 덮어쓰기는 돌고 있는 스크립트를 죽인다
#      (bash 는 바이트 오프셋 지연 읽기 · 260815 19:41 회차 사망 · 22:17 job_tick 사망 둘 다 이것).
#   ⑤ 덮기 전 백업 — ~/.nomute_selfupd_backup 에 전량 보관(최근 40개 회전). v1 사고를 이게 구했다.
#   ⑥ 전 경로 fail-soft — 무슨 일이 있어도 exit 0.
#
# 관측: 드리프트(깃≠홈이지만 도장이 같아 안 건드린 것)는 ~/.nomute_selfupd_drift 에 매 회차 갱신.
#       로그 도배 없이 「지금 갈려 있는 게 뭔지」가 항상 한 파일에 남는다.
# SELFUPD_DRY=1 = 판정만. SELFUPD_ADOPT=1 = 전 파일 도장만 찍고 종료(도입/재동기용).
set -u

SRC="$HOME/nomute-editor/scripts/mac"
L="${SELFUPD_LOG:-$HOME/job_tick.log}"
BK="$HOME/.nomute_selfupd_backup"
ST="$HOME/.nomute_selfupd_stamp"
DF="$HOME/.nomute_selfupd_drift"
LK="$HOME/.nomute_selfupd.lock"
DRY="${SELFUPD_DRY:-0}"; ADOPT="${SELFUPD_ADOPT:-0}"
say(){ printf '[selfupd] %s %s\n' "$(date '+%H:%M:%S')" "$1" >> "$L" 2>/dev/null || true; }
md5of(){ /sbin/md5 -q "$1" 2>/dev/null || md5sum "$1" 2>/dev/null | cut -d' ' -f1; }

[ -d "$SRC" ] || exit 0

if ! mkdir "$LK" 2>/dev/null; then
  A=$(/usr/bin/stat -f %m "$LK" 2>/dev/null || echo 0); N=$(date +%s)
  if [ "$A" -gt 0 ] && [ $((N-A)) -gt 600 ]; then
    rmdir "$LK" 2>/dev/null; mkdir "$LK" 2>/dev/null || exit 0; say "유령 락 회수"
  else exit 0; fi
fi
trap 'rmdir "$LK" 2>/dev/null || true' EXIT

mkdir -p "$ST" 2>/dev/null || true
[ "$DRY" = 1 ] || mkdir -p "$BK" 2>/dev/null || true

ok=0; rej=0; names=""; drift=""
for f in "$SRC"/*.sh; do
  [ -f "$f" ] || continue
  b=$(basename "$f"); h="$HOME/$b"
  cur=$(md5of "$f"); [ -n "$cur" ] || continue
  seen=$(cat "$ST/$b" 2>/dev/null || echo "")

  if [ "$ADOPT" = 1 ]; then printf '%s' "$cur" > "$ST/$b" 2>/dev/null; ok=$((ok+1)); continue; fi

  # ② 첫 관측 = 도장만(홈에 실물이 있으면). 홈에 없으면 신규 배포로 진행.
  if [ -z "$seen" ] && [ -f "$h" ]; then
    [ "$DRY" = 1 ] || printf '%s' "$cur" > "$ST/$b" 2>/dev/null
    cmp -s "$f" "$h" 2>/dev/null || drift="$drift $b"
    continue
  fi

  # ① 깃이 안 바뀌었으면 홈이 뭐가 됐든 무시 — 라이브 핫픽스 보호
  if [ "$cur" = "$seen" ]; then
    cmp -s "$f" "$h" 2>/dev/null || drift="$drift $b"
    continue
  fi

  cmp -s "$f" "$h" 2>/dev/null && { [ "$DRY" = 1 ] || printf '%s' "$cur" > "$ST/$b" 2>/dev/null; continue; }

  # ③ 문법 게이트
  if ! /bin/bash -n "$f" 2>/dev/null; then
    say "거부: $b — /bin/bash -n 실패(깨진 판 배포 차단 · 홈 설치본 유지 · 도장 미갱신)"
    rej=$((rej+1)); continue
  fi

  if [ "$DRY" = 1 ]; then
    say "DRY 설치 예정: $b ($(cat "$h" 2>/dev/null | wc -c | tr -d ' ')B -> $(wc -c <"$f" | tr -d ' ')B)"
    ok=$((ok+1)); names="$names $b"; continue
  fi

  [ -f "$h" ] && cp -p "$h" "$BK/$b.$(date '+%y%m%d%H%M%S')" 2>/dev/null   # ⑤
  cp -f "$f" "$h.staged" 2>/dev/null || { say "실패: $b (스테이징)"; rej=$((rej+1)); continue; }
  chmod 755 "$h.staged" 2>/dev/null
  if mv -f "$h.staged" "$h" 2>/dev/null; then                              # ④
    printf '%s' "$cur" > "$ST/$b" 2>/dev/null
    ok=$((ok+1)); names="$names $b"
  else
    rm -f "$h.staged" 2>/dev/null; say "실패: $b (원자 교체)"; rej=$((rej+1))
  fi
done

if [ "$DRY" != 1 ] && [ "$ADOPT" != 1 ]; then
  if [ -n "$drift" ]; then
    { date '+%F %T'; echo "깃≠홈 이지만 깃이 안 바뀌어 미개입(홈 우선 · 라이브 수정 보호):"
      for x in $drift; do echo "  - $x"; done
      echo "깃을 이기게 하려면: 그 파일을 scripts/mac 에 커밋하거나  echo '' > ~/.nomute_selfupd_stamp/<이름>"
    } > "$DF" 2>/dev/null
  else
    : > "$DF" 2>/dev/null
  fi
  [ -d "$BK" ] && ls -t "$BK" 2>/dev/null | tail -n +41 | while IFS= read -r o; do rm -f "$BK/$o" 2>/dev/null; done
fi

[ "$ADOPT" = 1 ] && say "도장 채택 ${ok}종(설치 0 · 도입/재동기 모드)"
[ "$ok" -gt 0 ] && [ "$ADOPT" != 1 ] && say "갱신 ${ok}종 —${names}"
[ "$rej" -gt 0 ] && say "거부/실패 ${rej}종 — 다음 틱 재시도"
exit 0
