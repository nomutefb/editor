#!/bin/bash
# 노뮤트 클라우드 액션 설치(맥) — 구글 드라이브 「내 드라이브/action」 폴더에 두고 더블클릭 1회.
# 더블클릭이 안 열리면(실행 권한이 벗겨졌거나 보안 경고) 터미널을 열고
#   bash 한 칸 띄우고 이 파일을 터미널 창에 끌어다 놓은 뒤 엔터.
# 하는 일: 이 맥을 5분마다 [기사 수집 + 속보 판정 + 경중 채점]이 돌게 하고 상태를 이 폴더에 미러한다.
# 계정이 연결된 어느 맥이든 이 파일 1회 실행이면 운영 서버가 된다.
# 정본 = 저장소 scripts/ (수정은 저장소에서 · 이 파일은 배포 사본)
set -u
cd "$(dirname "$0")" || exit 1
# 이 파일이 놓인 자리를 드라이브 폴더로 본다 — 단 폴더 이름이 action 일 때만.
# (저장소 안에서 바로 실행하는 경우엔 자리를 힌트로 주면 안 된다 → 그때는 본체가 클라우드 폴더를 스스로 찾는다.)
AD=""
[ "$(basename "$PWD")" = "action" ] && AD="$PWD"
echo "=================================================="
echo "  노뮤트 클라우드 액션 설치 - 맥"
echo "  5분마다: 기사 수집 + 속보 판정 + 경중 채점"
echo "  드라이브 폴더: ${AD:-자동 탐색}"
echo "=================================================="
if ! command -v git >/dev/null 2>&1; then
  echo "[멈춤] 깃 도구가 없습니다 — 지금 뜨는 설치 창(명령줄 도구)에서 설치를 마친 뒤 이 파일을 다시 실행하세요."
  xcode-select --install >/dev/null 2>&1 || true
  read -r -p "엔터를 누르면 닫힙니다 " _ || true
  exit 1
fi
if [ ! -d "$HOME/nomute-editor/.git" ]; then
  echo "[받기] 저장소를 받습니다 — 계정을 물으면 muteno, 비밀번호 칸에는 깃허브 토큰을 넣으세요."
  git clone "https://muteno@github.com/muteno/nomute-editor" "$HOME/nomute-editor" || {
    echo "[멈춤] 저장소 받기 실패 — 이 화면을 캡처해서 클로드에게 보여주세요."
    read -r -p "엔터를 누르면 닫힙니다 " _ || true
    exit 1
  }
fi
cd "$HOME/nomute-editor" || exit 1
git pull -q --rebase origin main 2>/dev/null || true
if command -v claude >/dev/null 2>&1; then
  echo "[로그인] 잠시 후 클로드 화면이 열립니다. 로그인 안내가 나오면 브라우저에서 로그인(구독 계정),"
  echo "         입력창이 보이면  /exit  를 입력해 나오세요. 이미 로그인돼 있어도  /exit  만 치면 됩니다."
  read -r -p "엔터를 누르면 진행 " _ || true
  claude || true
fi
NOMUTE_ACTION_HINT="$AD" bash scripts/cloud_action_setup.sh
echo
echo "상태 보기 = 드라이브 action 폴더의 「상태」 폴더 · 키 넣기 = 「노뮤트_열쇠입력.html」 더블클릭"
echo "끄기 = 터미널에서 crontab -e 를 열어 nomute-cloud-action 줄 삭제"
read -r -p "엔터를 누르면 창이 닫힙니다 " _ || true
