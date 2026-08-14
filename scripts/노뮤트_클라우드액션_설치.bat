@echo off
chcp 65001 >nul
setlocal EnableExtensions
title 노뮤트 클라우드 액션 설치
REM ═════════════════════════════════════════════════════════════════════════
REM  이 파일의 집 = 구글 드라이브 「내 드라이브\action」 폴더(운영자 260814).
REM  하는 일: 이 컴퓨터를 5분마다 [기사 수집 + 속보 판정 + 경중 채점]이 돌게 만들고,
REM  결과 상태를 이 폴더(상태\)에 미러한다. 드라이브 글자(G: 등)가 바뀌어도
REM  프로그램이 매 회차 폴더를 스스로 다시 찾는다 — 이 파일은 설치/수리(더블클릭)만 맡는다.
REM  계정이 연결된 어느 컴퓨터든 이 파일 더블클릭 1회면 운영 서버가 된다.
REM  정본 = 저장소 scripts\ (수정은 저장소에서 · 이 파일은 배포 사본)
REM ═════════════════════════════════════════════════════════════════════════
set "AD=%~dp0"
echo ==================================================
echo   노뮤트 클라우드 액션 설치 - 윈도우
echo   5분마다: 기사 수집 + 속보 판정 + 경중 채점
echo   드라이브 폴더: %AD%
echo ==================================================
echo.

REM ── 1단계: 깃 도구(저장소를 받는 데 필요한 최소) — 나머지 도구는 저장소의 기본 설치가 맡는다
where git >nul 2>nul
if errorlevel 1 goto :need_git
goto :have_git
:need_git
where winget >nul 2>nul
if errorlevel 1 (
  echo [멈춤] 이 윈도우에 winget 이 없습니다. 마이크로소프트 스토어에서 "앱 설치 관리자"를 설치한 뒤 다시 더블클릭하세요.
  pause
  exit /b 1
)
echo [설치] 깃 도구를 설치합니다...
winget install --id Git.Git -e --silent --accept-source-agreements --accept-package-agreements
echo [중요] 도구를 방금 설치했습니다. 이 창을 닫고 같은 파일을 한 번 더 더블클릭하세요.
pause
exit /b 0
:have_git

REM ── 2단계: 저장소 받기(처음 1회 · 브라우저 로그인)
if exist "%USERPROFILE%\nomute-editor\.git" goto :have_repo
echo [받기] 저장소를 받습니다. 브라우저 로그인 창이 뜨면 muteno 계정으로 로그인하세요.
git clone https://muteno@github.com/muteno/nomute-editor "%USERPROFILE%\nomute-editor"
if not exist "%USERPROFILE%\nomute-editor\.git" (
  echo [멈춤] 저장소 받기에 실패했습니다. 이 화면을 캡처해서 클로드에게 보여주세요.
  pause
  exit /b 1
)
:have_repo

REM ── 3단계: 기본 설치 = 기존 PC 설치 정본을 그대로 부른다 - 도구·클로드 로그인·5분 시계·첫 발사
call "%USERPROFILE%\nomute-editor\scripts\pc_setup.bat"

REM ── 4단계: 방금 도구를 새로 깔았으면 이 창은 새 경로를 모른다 → 한 번 더 더블클릭 안내
set MISS=0
where python >nul 2>nul
if errorlevel 1 set MISS=1
where node >nul 2>nul
if errorlevel 1 set MISS=1
where claude >nul 2>nul
if errorlevel 1 set MISS=1
if "%MISS%"=="1" (
  echo [중요] 도구가 방금 새로 설치됐습니다. 이 창을 닫고 같은 파일을 한 번 더 더블클릭하세요.
  pause
  exit /b 0
)

REM ── 5단계: 5분 시계의 종점을 클라우드 겉옷으로 교체 - 드라이브 상태 미러 + 환경변수 읽기
set "NOMUTE_ACTION_HINT_WIN=%AD%"
set "GITBASH=%ProgramFiles%\Git\bin\bash.exe"
if not exist "%GITBASH%" set "GITBASH=%ProgramFiles(x86)%\Git\bin\bash.exe"
if not exist "%GITBASH%" (
  echo [멈춤] Git-Bash 를 찾지 못했습니다. 이 화면을 캡처해서 클로드에게 보여주세요.
  pause
  exit /b 1
)
"%GITBASH%" -lc "cd ~/nomute-editor && git pull -q --rebase origin main; bash scripts/cloud_action_setup.sh"

echo.
echo 위에 [착지 원장]이 ok 로 시작하면 설치 성공입니다. 이후는 5분마다 알아서 돕니다.
echo 상태 보기 = 이 폴더의 "상태" 폴더 · 키 넣는 곳 = 이 폴더의 환경변수.txt
echo 끄기 = 명령프롬프트에서:  schtasks /Delete /F /TN NomutePcLane
pause
