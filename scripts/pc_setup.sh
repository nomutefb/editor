#!/usr/bin/env bash
# PC 레인 마무리 설치(윈도우 Git-Bash 전용) — pc_setup.bat 뒷단계의 셸 몫.
# 왜 분리(260814 실측): cmd 배치는 \" 를 이스케이프가 아니라 따옴표 상태 토글로 읽어서, 안쪽 따옴표가 있는
#   복잡한 -lc 한 줄이 첫 설치에서 조용히 부서졌다(증상 = ~/nomute_pc_run.sh 미생성 · 로그 파일 0 · 에러 표시 0).
#   → 복잡한 건 전부 이 파일이 맡고, 배치에는 「안쪽 따옴표 없는 -lc 한 줄」만 남긴다(구조 봉합 = 같은 함정 재발 0).
# 하는 일: ① 실행기(절대경로 PATH) 굽기 ② 조용한 실행 vbs 굽기 ③ 15분 작업 스케줄러 등록 ④ 첫 발사 직접 실행 + 결과 표시.
set -u
cd "$HOME" || exit 1

PY=""
for _c in python python3; do
  _p="$(command -v "$_c" 2>/dev/null || true)"
  case "$_p" in *WindowsApps*) continue;; esac   # 윈도우 가짜 파이썬 껍데기 제외(pc_lane.sh 동축)
  [ -n "$_p" ] && { PY="$_p"; break; }
done
CL="$(command -v claude 2>/dev/null || true)"
[ -n "$PY" ] || { echo "❌ 진짜 파이썬을 못 찾음 — pc_setup.bat 를 다시 더블클릭"; exit 1; }
pd="$(dirname "$PY")"; cdir=""; [ -n "$CL" ] && cdir="$(dirname "$CL")"
{ echo '#!/usr/bin/env bash'
  echo "export PATH=\"$pd${cdir:+:$cdir}:\$PATH\""
  echo 'exec ~/nomute-editor/scripts/pc_lane.sh'
} > "$HOME/nomute_pc_run.sh"
chmod +x "$HOME/nomute_pc_run.sh"
echo "① 실행기 준비 완료 (파이썬=$pd${cdir:+ · 클로드=$cdir})"

# 조용한 실행기 — 작업 스케줄러가 검은 창 없이 레인을 돌리게 하는 한 줄짜리 vbs.
BASHWIN="$(cygpath -w /usr/bin/bash 2>/dev/null || echo 'C:\Program Files\Git\bin\bash.exe')"
cat > "$HOME/nomute_pc_lane.vbs" <<EOF
CreateObject("WScript.Shell").Run """$BASHWIN"" -lc ""~/nomute_pc_run.sh >> ~/pc_lane.log 2>&1""", 0, False
EOF
echo "② 조용한 실행기 준비 완료"

VBSWIN="$(cygpath -w "$HOME/nomute_pc_lane.vbs" 2>/dev/null || true)"
# ⚠ 260814 실측 봉합 2종: ⓐ Git-Bash 는 /Create 같은 슬래시 옵션을 경로로 착각해 바꿔친다(MSYS 경로 변환)
#   → 변환 끄기 2중(MSYS_NO_PATHCONV + MSYS2_ARG_CONV_EXCL) ⓑ 구판은 에러를 >/dev/null 로 삼켜
#   「실패」만 남고 사유가 소실됐다(이 레포가 반복 겪은 관측 소실 축) → 사유를 받아서 화면에 그대로 낸다.
ERR="$(MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' schtasks.exe /Create /F /SC MINUTE /MO 5 /TN NomutePcLane /TR "wscript.exe \"$VBSWIN\"" 2>&1)"
if [ $? -eq 0 ]; then
  echo "③ 5분 시계 등록 완료"
else
  echo "❌ 5분 시계 등록 실패 — 사유: $ERR"
  echo "   (이 화면을 캡처해서 클로드에게)"; exit 1
fi

echo "④ 첫 발사를 지금 이 창에서 직접 돌린다 — 수집 몇 분 + 판정 몇 분이 걸릴 수 있다. 글자가 올라가는 동안 창을 닫지 말 것…"
bash "$HOME/nomute_pc_run.sh"
echo
echo "── 착지 원장 ──"
cat "$HOME/.nomute_pc_lane_land" 2>/dev/null || echo "기록 없음"
echo "── 로그 꼬리 ──"
tail -n 6 "$HOME/pc_lane.log" 2>/dev/null || true
echo "끝 — 착지 원장이 ok 로 시작하면 성공. 이후는 5분 시계가 알아서 돈다."
