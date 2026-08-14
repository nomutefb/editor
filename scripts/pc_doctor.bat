@echo off
chcp 65001 >nul
title 노뮤트 PC 레인 종합 진단
"%ProgramFiles%\Git\bin\bash.exe" -lc "cd ~/nomute-editor 2>/dev/null && git pull -q --rebase origin main 2>/dev/null; bash scripts/pc_doctor.sh"
echo.
echo 위 화면이 전부입니다. 문제 줄이 있으면 그 줄에 고치는 법이 같이 적혀 있습니다.
pause
