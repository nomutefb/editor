@echo off
chcp 65001 >nul
setlocal EnableExtensions
title 노뮤트 PC 안전장치 설치
echo ==================================================
echo   노뮤트 PC 안전장치 설치 (1탄)
echo   이 PC가 15분마다: 기사 수집 + 속보 판정 + 경중 채점
echo ==================================================
echo.

REM ── 1단계: 기본 도구 — 없으면 설치하고 "다시 더블클릭" 안내(설치 직후엔 이 창이 새 경로를 몰라서 2번 나눠 간다)
set NEED=0
where winget >nul 2>nul
if errorlevel 1 (
  echo [멈춤] 이 윈도우에 winget 이 없습니다. 마이크로소프트 스토어에서 "앱 설치 관리자"를 설치한 뒤 다시 더블클릭하세요.
  pause
  exit /b 1
)
where git >nul 2>nul
if errorlevel 1 (
  echo [설치] 깃 도구를 설치합니다...
  winget install --id Git.Git -e --silent --accept-source-agreements --accept-package-agreements
  set NEED=1
)
where python >nul 2>nul
if errorlevel 1 (
  echo [설치] 파이썬을 설치합니다...
  winget install --id Python.Python.3.12 -e --silent --accept-source-agreements --accept-package-agreements
  set NEED=1
)
where node >nul 2>nul
if errorlevel 1 (
  echo [설치] 노드를 설치합니다...
  winget install --id OpenJS.NodeJS.LTS -e --silent --accept-source-agreements --accept-package-agreements
  set NEED=1
)
if "%NEED%"=="1" (
  echo.
  echo [중요] 도구를 방금 새로 설치했습니다.
  echo        이 창을 닫고, 같은 파일을 한 번 더 더블클릭해 주세요. 그러면 다음 단계로 넘어갑니다.
  pause
  exit /b 0
)
echo [1/6] 기본 도구 확인 완료 (깃 / 파이썬 / 노드)

REM ── 2단계: 클로드 도구
where claude >nul 2>nul
if errorlevel 1 (
  echo [2/6] 클로드 도구를 설치합니다...
  call npm install -g @anthropic-ai/claude-code
)
where claude >nul 2>nul
if errorlevel 1 (
  echo [멈춤] 클로드 도구 설치가 안 됐습니다. 이 화면을 캡처해서 클로드에게 보여주세요.
  pause
  exit /b 1
)
echo [2/6] 클로드 도구 확인 완료

echo [3/6] 파이썬 부품 설치...
python -m pip install --quiet feedparser requests

REM ── 4단계: 저장소 받기(브라우저 로그인 1회)
if exist "%USERPROFILE%\nomute-editor\.git" (
  echo [4/6] 저장소 이미 있음 — 통과
) else (
  echo [4/6] 저장소를 받습니다. 브라우저 로그인 창이 뜨면 muteno 계정으로 로그인하세요.
  git clone https://muteno@github.com/muteno/nomute-editor "%USERPROFILE%\nomute-editor"
)
if not exist "%USERPROFILE%\nomute-editor\.git" (
  echo [멈춤] 저장소 받기에 실패했습니다. 이 화면을 캡처해서 클로드에게 보여주세요.
  pause
  exit /b 1
)

set "GITBASH=%ProgramFiles%\Git\bin\bash.exe"
if not exist "%GITBASH%" set "GITBASH=%ProgramFiles(x86)%\Git\bin\bash.exe"
if not exist "%GITBASH%" (
  echo [멈춤] Git-Bash 를 찾지 못했습니다. 이 화면을 캡처해서 클로드에게 보여주세요.
  pause
  exit /b 1
)

REM ── 실행기 굽기: 작업 스케줄러가 여는 셸은 경로를 모를 수 있어 파이썬·클로드 실제 경로를 절대경로로 박는다
"%GITBASH%" -lc "pd=$(dirname \"$(command -v python 2>/dev/null || echo /na)\"); cdir=$(dirname \"$(command -v claude 2>/dev/null || echo /na)\"); { echo '#!/usr/bin/env bash'; echo \"export PATH=\\\"$pd:$cdir:\$PATH\\\"\"; echo 'exec ~/nomute-editor/scripts/pc_lane.sh'; } > ~/nomute_pc_run.sh; chmod +x ~/nomute_pc_run.sh; echo 실행기-준비완료"

REM ── 5단계: 클로드 로그인(구독 계정 1회)
echo.
echo [5/6] 클로드 로그인 단계입니다. 잘 읽고 진행하세요:
echo    1. 잠시 후 클로드 화면이 이 창에 열립니다.
echo    2. 로그인 안내가 나오면 시키는 대로 브라우저에서 로그인하세요. (클로드 구독 계정)
echo    3. 로그인이 끝나 입력창이 보이면  /exit  라고 입력해서 나오세요.
echo    4. 이미 로그인돼 있으면 바로  /exit  만 입력하면 됩니다.
echo.
pause
call claude

REM ── 6단계: 15분 시계 등록(창 안 뜨는 조용한 실행) + 첫 발사
> "%USERPROFILE%\nomute_pc_lane.vbs" echo CreateObject("WScript.Shell").Run """%GITBASH%"" -lc ""~/nomute_pc_run.sh ^>^> ~/pc_lane.log 2^>^&1""", 0, False
schtasks /Create /F /SC MINUTE /MO 15 /TN "NomutePcLane" /TR "wscript.exe \"%USERPROFILE%\nomute_pc_lane.vbs\"" >nul
if errorlevel 1 (
  echo [멈춤] 15분 시계 등록에 실패했습니다. 이 화면을 캡처해서 클로드에게 보여주세요.
  pause
  exit /b 1
)
echo [6/6] 15분 시계 등록 완료 — 첫 발사를 지금 시작합니다. 수집과 판정에 1~3분 걸립니다...
schtasks /Run /TN "NomutePcLane" >nul
timeout /t 150 /nobreak >nul
echo.
echo ── 첫 발사 결과 ──────────────────────────────────
"%GITBASH%" -lc "echo '착지 원장:'; cat ~/.nomute_pc_lane_land 2>/dev/null || echo '아직 기록 없음 - 몇 분 뒤 pc_lane.log 확인'; echo; echo '최근 로그:'; tail -n 8 ~/pc_lane.log 2>/dev/null"
echo ──────────────────────────────────────────────────
echo.
echo 위에 ok 로 시작하는 줄이 보이면 설치 성공입니다. 이 창은 닫아도 됩니다.
echo 뭔가 이상하면 이 화면을 캡처해서 클로드에게 보여주세요.
pause
