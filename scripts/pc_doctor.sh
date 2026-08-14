#!/usr/bin/env bash
# PC 레인 종합 진단·자가수리기(운영자 260814 「설계를 완벽히 해서 한꺼번에 줘 · 4번 해서 안 됐으니 믿을 수가 없음」)
#
# 왜 이 파일이 있나 = 260814 실패의 구조적 원인은 「한 층 고치고 → 운영자에게 돌려보라 → 다음 층 발견」의
#   4회 왕복이었다. 세션이 윈도우를 직접 못 봐서 **한 화면에 한 층씩만** 보였기 때문이다.
#   → 이 진단기는 알려진 전 층 + 미확인 후보를 **한 번에 전수 점검**하고, 고칠 수 있는 건 그 자리에서 고치고,
#     못 고치는 건 사유를 한국어로 적어 한 장으로 낸다. 왕복 0회가 설계 목표다.
#
# 실행(운영자) = scripts/pc_doctor.bat 더블클릭 · 또는 Git-Bash 에서 bash scripts/pc_doctor.sh
# 안전 = 읽기·환경 점검이 기본 · 수리는 되돌릴 수 있는 것만(시계 재등록·실행기 재생성) · git 이력 무접촉.
#
# 점검 층(260814 실측 이력 = ①~④ 는 실제로 터진 것, ⑤~⑫ 는 아직 안 겪었지만 같은 계열의 후보):
#   ① 저장소 실존·최신 ② 진짜 파이썬(가짜 껍데기 배제) ③ 파이썬 부품(feedparser·requests)
#   ④ 문자 규격(cp949 이모지 사망) ⑤ 클로드 도구·로그인 ⑥ 실행기 파일 ⑦ 조용한 실행기
#   ⑧ 작업 스케줄러 등록·주기·마지막 결과 ⑨ 잠금 잔여물 ⑩ git 원격 인증 ⑪ 디스크·쓰기 권한
#   ⑫ 레인 실주행(수집→판정→착지) 전 구간
set -u
OK=0; NG=0; FIX=0
_p(){ printf '%s\n' "$*"; }
_ok(){ OK=$((OK+1)); _p "  [정상] $*"; }
_ng(){ NG=$((NG+1)); _p "  [문제] $*"; }
_fx(){ FIX=$((FIX+1)); _p "  [수리] $*"; }

_p "══════════════════════════════════════════════════════════"
_p " 노뮤트 PC 레인 종합 진단  ·  $(TZ=Asia/Seoul date '+%m-%d %H:%M:%S') KST"
_p "══════════════════════════════════════════════════════════"

# ── ① 저장소 ────────────────────────────────────────────────
_p ""; _p "① 저장소"
REPO="$HOME/nomute-editor"
if [ -d "$REPO/.git" ]; then
  cd "$REPO" || exit 1
  _ok "위치 $REPO"
  if git fetch origin main -q 2>/dev/null; then
    _ok "저장소 연결(내려받기 성공)"
    git pull -q --rebase origin main 2>/dev/null && _fx "최신 코드로 갱신" || _ng "최신 갱신 실패 — 로컬에 안 올린 변경이 있을 수 있다"
  else
    _ng "저장소 연결 실패 — 인터넷 또는 깃 로그인 만료(고치는 법: 아무 폴더에서 git clone 을 한 번 해보고 로그인 창이 뜨면 muteno 로 로그인)"
  fi
else
  _ng "저장소 없음 — pc_setup.bat 를 먼저 더블클릭"; _p ""; _p "진단 중단(저장소가 있어야 나머지를 볼 수 있다)"; exit 1
fi

# ── ② 진짜 파이썬 ───────────────────────────────────────────
_p ""; _p "② 파이썬"
PY=""
for _c in python python3; do
  _q="$(command -v "$_c" 2>/dev/null || true)"
  case "$_q" in *WindowsApps*) continue;; esac
  [ -n "$_q" ] && { PY="$_q"; break; }
done
if [ -n "$PY" ]; then
  _ok "실행기 $PY ($("$PY" -c 'import sys;print(sys.version.split()[0])' 2>/dev/null || echo 판 미상))"
else
  _ng "진짜 파이썬 없음(윈도우 가짜 껍데기만 잡힘) — 고치는 법: pc_setup.bat 재실행, 또는 python.org 에서 설치 후 재실행"
fi

# ── ③ 파이썬 부품 ───────────────────────────────────────────
_p ""; _p "③ 파이썬 부품"
if [ -n "$PY" ]; then
  for m in feedparser requests; do
    if "$PY" -c "import $m" >/dev/null 2>&1; then _ok "$m 설치됨"
    else
      _p "  … $m 없음 → 지금 설치 시도"
      if "$PY" -m pip install --quiet "$m" >/dev/null 2>&1; then _fx "$m 설치 완료"
      else _ng "$m 설치 실패 — 고치는 법: 명령창에서  python -m pip install $m"; fi
    fi
  done
else _ng "파이썬이 없어 부품 점검 불가"; fi

# ── ④ 문자 규격(cp949 사망 축) ──────────────────────────────
_p ""; _p "④ 문자 규격"
if [ -n "$PY" ]; then
  if PYTHONUTF8=1 PYTHONIOENCODING=utf-8 "$PY" -c 'print("\U0001f525 테스트")' >/dev/null 2>&1; then
    _ok "이모지·한글 출력 가능(레인이 규격을 강제한다)"
  else
    _ng "규격 강제로도 출력 실패 — 파이썬 판이 매우 낡았을 수 있다(3.7 이상 필요)"
  fi
  "$PY" -c 'print("\U0001f525")' >/dev/null 2>&1 || _p "       (참고: 규격 강제 없이는 실제로 죽는다 = 260814 진범 확인)"
fi

# ── ⑤ 클로드 도구 ───────────────────────────────────────────
_p ""; _p "⑤ 판정 도구(클로드)"
CL="$(command -v claude 2>/dev/null || true)"
if [ -n "$CL" ]; then
  _ok "설치됨 $CL"
  if [ -f "$HOME/.claude/.credentials.json" ] || [ -d "$HOME/.claude" ]; then _ok "로그인 흔적 있음"
  else _ng "로그인 안 됨 — 고치는 법: 명령창에서  claude  실행 후 로그인, 끝나면 /exit"; fi
else
  _ng "클로드 도구 없음 — 판정·채점은 건너뛰고 수집만 돈다(고치는 법: npm install -g @anthropic-ai/claude-code)"
fi

# ── ⑥⑦ 실행기·조용한 실행기 ────────────────────────────────
_p ""; _p "⑥⑦ 실행기"
RUN="$HOME/nomute_pc_run.sh"; VBS="$HOME/nomute_pc_lane.vbs"
if [ -s "$RUN" ] && grep -q pc_lane.sh "$RUN" 2>/dev/null; then _ok "실행기 있음"
else
  pd=""; [ -n "$PY" ] && pd="$(dirname "$PY")"; cd2=""; [ -n "$CL" ] && cd2="$(dirname "$CL")"
  { echo '#!/usr/bin/env bash'; echo "export PATH=\"$pd${cd2:+:$cd2}:\$PATH\""; echo 'exec ~/nomute-editor/scripts/pc_lane.sh'; } > "$RUN"
  chmod +x "$RUN"; _fx "실행기 재생성"
fi
BASHWIN="$(cygpath -w /usr/bin/bash 2>/dev/null || echo 'C:\Program Files\Git\bin\bash.exe')"
if [ -s "$VBS" ]; then _ok "조용한 실행기 있음"
else
  printf 'CreateObject("WScript.Shell").Run """%s"" -lc ""~/nomute_pc_run.sh >> ~/pc_lane.log 2>&1""", 0, False\n' "$BASHWIN" > "$VBS"
  _fx "조용한 실행기 재생성"
fi

# ── ⑧ 작업 스케줄러 ─────────────────────────────────────────
_p ""; _p "⑧ 5분 시계"
if command -v schtasks.exe >/dev/null 2>&1; then
  Q="$(MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' schtasks.exe /Query /TN NomutePcLane /V /FO LIST 2>/dev/null)"
  if [ -n "$Q" ]; then
    _ok "등록됨"
    printf '%s\n' "$Q" | sed -n 's/^\(마지막 실행 시간\|Last Run Time\)[[:space:]]*:[[:space:]]*/       마지막 실행: /p' | head -1
    printf '%s\n' "$Q" | sed -n 's/^\(마지막 결과\|Last Result\)[[:space:]]*:[[:space:]]*/       마지막 결과: /p' | head -1
    printf '%s\n' "$Q" | sed -n 's/^\(다음 실행 시간\|Next Run Time\)[[:space:]]*:[[:space:]]*/       다음 실행: /p' | head -1
    if printf '%s\n' "$Q" | grep -qE '(반복: 매|Repeat: Every).*(, 5분|, 5 min)'; then _ok "주기 5분"
    else
      VBSWIN="$(cygpath -w "$VBS" 2>/dev/null || echo "$VBS")"
      if MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' schtasks.exe /Create /F /SC MINUTE /MO 5 /TN NomutePcLane /TR "wscript.exe \"$VBSWIN\"" >/dev/null 2>&1; then _fx "주기를 5분으로 재등록"
      else _ng "주기 재등록 실패 — 고치는 법: 이 창을 관리자 권한으로 다시 열고 재실행"; fi
    fi
  else
    VBSWIN="$(cygpath -w "$VBS" 2>/dev/null || echo "$VBS")"
    if MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' schtasks.exe /Create /F /SC MINUTE /MO 5 /TN NomutePcLane /TR "wscript.exe \"$VBSWIN\"" >/dev/null 2>&1; then _fx "시계 신규 등록(5분)"
    else _ng "시계 등록 실패 — 고치는 법: 관리자 권한 명령창에서 재실행"; fi
  fi
else _ng "윈도우 작업 스케줄러를 못 찾음(이 기계가 윈도우가 아닐 수 있다)"; fi

# ── ⑨ 잠금 잔여물 ───────────────────────────────────────────
_p ""; _p "⑨ 잠금"
LOCK="$HOME/.nomute_pc_lane.lock"
if [ -d "$LOCK" ]; then
  if [ -n "$(find "$LOCK" -maxdepth 0 -mmin +90 2>/dev/null)" ]; then rmdir "$LOCK" 2>/dev/null && _fx "죽은 잠금 회수(90분 초과)"
  else _ok "앞 회차가 실행 중(정상 · 이번 진단은 실주행을 건너뛴다)"; SKIP_RUN=1; fi
else _ok "잠금 없음"; fi

# ── ⑩ 원격 인증 ─────────────────────────────────────────────
_p ""; _p "⑩ 저장소 쓰기 권한"
if git ls-remote --exit-code origin >/dev/null 2>&1; then _ok "원격 접근 가능"
else _ng "원격 접근 불가 — 깃 로그인 만료 가능(고치는 법: 명령창에서 git push 를 한 번 해보고 로그인 창에 muteno 로 로그인)"; fi

# ── ⑪ 디스크·쓰기 ───────────────────────────────────────────
_p ""; _p "⑪ 쓰기 권한"
if touch "$HOME/.nomute_pc_wtest" 2>/dev/null; then rm -f "$HOME/.nomute_pc_wtest"; _ok "홈 폴더 쓰기 가능"
else _ng "홈 폴더에 파일을 못 쓴다 — 보안 프로그램·권한 문제"; fi
if touch "$REPO/.wtest" 2>/dev/null; then rm -f "$REPO/.wtest"; _ok "저장소 폴더 쓰기 가능"
else _ng "저장소 폴더에 파일을 못 쓴다"; fi

# ── ⑫ 실주행 ────────────────────────────────────────────────
_p ""; _p "⑫ 실제 한 바퀴(수집 → 판정 → 착지)"
if [ "${SKIP_RUN:-0}" = "1" ]; then
  _p "  건너뜀 — 앞 회차가 지금 돌고 있다"
elif [ -z "$PY" ]; then
  _p "  건너뜀 — 파이썬이 없어 돌릴 수 없다"
else
  _p "  … 수집 몇 분 + 판정 몇 분이 걸릴 수 있다. 기다려라."
  bash "$REPO/scripts/pc_lane.sh" > "$HOME/pc_doctor_run.log" 2>&1
  RC=$?
  LAND="$(cat "$HOME/.nomute_pc_lane_land" 2>/dev/null || echo '기록 없음')"
  _p "  결과 기록: $LAND"
  case "$LAND" in
    *"|ok|"*) _ok "한 바퀴 성공" ;;
    *collect-fail*) _ng "수집 단계 실패 — 아래 마지막 로그 참조" ;;
    *judge*)        _ng "판정 단계 실패 — 클로드 로그인·쿼터 확인" ;;
    *push-fail*)    _ng "저장소 올리기 실패 — 인증·충돌" ;;
    *lock-busy*)    _p "  [보류] 앞 회차 진행 중이라 이번 바퀴는 물러났다(정상)" ;;
    *)              _ng "미상 결과(rc=$RC)" ;;
  esac
  _p "  ── 마지막 로그 12줄 ──"
  tail -n 12 "$HOME/pc_doctor_run.log" 2>/dev/null | sed 's/^/    /'
fi

# ── 총평 ────────────────────────────────────────────────────
_p ""
_p "══════════════════════════════════════════════════════════"
_p " 정상 $OK · 수리 $FIX · 문제 $NG"
if [ "$NG" = "0" ]; then
  _p " → 남은 문제 없음. 이제 5분마다 알아서 돈다."
else
  _p " → 위의 [문제] 줄에 고치는 법이 같이 적혀 있다."
  _p "   그래도 막히면 이 화면 전체를 캡처해서 클로드에게 주면 된다."
fi
_p "══════════════════════════════════════════════════════════"
