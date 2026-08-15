@echo off
chcp 65001 >nul
setlocal EnableExtensions
title 노뮤트 클라우드 액션 서버 설치
REM ═════════════════════════════════════════════════════════════════════════
REM  노뮤트 클라우드 액션 서버(운영자 260814 «노뮤트에디터를 돌리는 일괄 액션 서버 · 독립»).
REM  이 파일의 집 = 구글 드라이브 「내 드라이브\action」 폴더.
REM  더블클릭 1번이면 이 컴퓨터가 운영 서버가 된다: 5분마다 [기사 수집 + 속보 판정 + 경중 채점]을
REM  돌리고, 결과 상태를 이 폴더(상태\)에 미러하고, 이 폴더의 환경변수.txt 로 열쇠를 받는다.
REM  드라이브 글자(G: 등)가 바뀌어도 서버가 매 회차 폴더를 스스로 다시 찾는다.
REM  다른 설치물에 기대지 않는 자기완결 설치다(도구·저장소·로그인·5분 시계 전부 여기서).
REM  정본 = 저장소 scripts\ (수정은 저장소에서 · 이 파일은 배포 사본)
REM ═════════════════════════════════════════════════════════════════════════
set "AD=%~dp0"
echo ==================================================
echo   노뮤트 클라우드 액션 서버 설치 - 윈도우
echo   5분마다: 기사 수집 + 속보 판정 + 경중 채점
echo   드라이브 폴더: %AD%
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
echo [1/5] 기본 도구 확인 완료 - 깃 / 파이썬 / 노드

REM ── 2단계: 저장소 받기(처음 1회 · 브라우저 로그인)
if exist "%USERPROFILE%\nomute-editor\.git" goto :have_repo
echo [2/5] 저장소를 받습니다. 브라우저 로그인 창이 뜨면 muteno 계정으로 로그인하세요.
git clone https://nomutefb@github.com/nomutefb/editor "%USERPROFILE%\nomute-editor"
if not exist "%USERPROFILE%\nomute-editor\.git" (
  echo [멈춤] 저장소 받기에 실패했습니다. 이 화면을 캡처해서 클로드에게 보여주세요.
  pause
  exit /b 1
)
:have_repo
echo [2/5] 저장소 확인 완료

REM ── 3단계: 클로드 도구(판정 축 · 구독 로그인)
where claude >nul 2>nul
if errorlevel 1 (
  echo [3/5] 클로드 도구를 설치합니다...
  call npm install -g @anthropic-ai/claude-code
)
where claude >nul 2>nul
if errorlevel 1 (
  echo [중요] 클로드 도구가 방금 설치됐거나 설치에 실패했습니다.
  echo        이 창을 닫고 같은 파일을 한 번 더 더블클릭하세요. 반복되면 화면을 캡처해서 클로드에게.
  pause
  exit /b 0
)
echo.
echo [4/5] 클로드 로그인 단계입니다. 잘 읽고 진행하세요:
echo    1. 잠시 후 클로드 화면이 이 창에 열립니다.
echo    2. 로그인 안내가 나오면 시키는 대로 브라우저에서 로그인하세요. (클로드 구독 계정)
echo    3. 입력창이 보이면  /exit  라고 입력해서 나오세요. 이미 로그인돼 있어도  /exit  만 치면 됩니다.
echo.
pause
call claude

REM ── 4단계: 서버 등록(5분 시계·조용한 실행·드라이브 연결·첫 발사) = 저장소 정본 호출
set "NOMUTE_ACTION_HINT_WIN=%AD%"
set "GITBASH=%ProgramFiles%\Git\bin\bash.exe"
if not exist "%GITBASH%" set "GITBASH=%ProgramFiles(x86)%\Git\bin\bash.exe"
if not exist "%GITBASH%" (
  echo [멈춤] Git-Bash 를 찾지 못했습니다. 이 화면을 캡처해서 클로드에게 보여주세요.
  pause
  exit /b 1
)
echo [5/5] 서버 등록과 첫 발사를 시작합니다...
"%GITBASH%" -lc "cd ~/nomute-editor && git pull -q --rebase origin main; bash scripts/cloud_action_setup.sh"

echo.
echo 위에 [착지 원장]이 ok 로 시작하면 설치 성공입니다. 이후는 5분마다 알아서 돕니다.
echo 상태 보기 = 이 폴더의 "상태" 폴더 · 키 넣기 = 이 폴더의 "노뮤트_열쇠입력.html" 더블클릭
echo 끄기 = 명령프롬프트에서:  schtasks /Delete /F /TN NomuteCloudAction
pause
