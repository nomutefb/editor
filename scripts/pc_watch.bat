@echo off
chcp 65001 >nul
title 노뮤트 착지 감시창
"%ProgramFiles%\Git\bin\bash.exe" -lc "cd ~/nomute-editor && git pull -q --rebase origin main; exec bash scripts/pc_watch.sh"
pause
