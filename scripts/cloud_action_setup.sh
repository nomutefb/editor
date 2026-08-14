#!/usr/bin/env bash
# 클라우드 액션 서버 설치 뒷단(운영자 260814 «노뮤트에디터를 돌리는 일괄 액션 서버 · 독립» · Q1482~Q1487).
# 설치 파일(bat/command)이 도구·저장소·클로드 로그인을 마친 뒤 이 파일이 서버를 등록한다:
#   ① 드라이브 action 폴더 연결(계정.txt·환경변수.txt 씨앗·열쇠 입력 페이지 복사)
#   ② 실행기 ~/nomute_cloud_run.sh(도구 절대경로를 박아 시계 환경에서도 산다)
#   ③ 5분 시계 = 윈도우 작업 스케줄러(NomuteCloudAction · 조용한 실행 vbs) / 맥 crontab(마커 nomute-cloud-action)
#   ④ 첫 발사 + 착지 원장·드라이브 상태 표시.
# 다른 설치물에 기대지 않는다 — 같은 컴퓨터에 옛 5분 시계(NomutePcLane)가 있으면 이 서버로 대체(제거·안내).
# 시계 등록 문법(조용한 vbs·MSYS 변환 끄기 2중·사유 표시)은 이 레포 실측 봉합 문법을 그대로 계승한다.
set -u
cd "$HOME/nomute-editor" 2>/dev/null || { echo "❌ 저장소 없음: ~/nomute-editor — 설치 파일(bat/command)을 먼저 실행"; exit 1; }

# 계정값은 서버 본체 정본에서 뽑는다(값 사본 0 — 두 곳에 적으면 조용히 갈린다 · check_cloud_action_chain 강제)
ACCOUNT="$(sed -n 's/^ACCOUNT="\([^"]*\)".*/\1/p' scripts/cloud_action.sh | head -1)"

# ── ① 드라이브 폴더: 설치 파일이 준 힌트(자기 폴더) 우선 · 없으면 본체의 스캔(--find)으로
AD=""
if [ -n "${NOMUTE_ACTION_HINT_WIN:-}" ]; then AD="$(cygpath -u "$NOMUTE_ACTION_HINT_WIN" 2>/dev/null || true)"; fi
[ -z "$AD" ] && AD="${NOMUTE_ACTION_HINT:-}"
[ -n "$AD" ] && AD="${AD%/}"
if [ -z "$AD" ] || [ ! -d "$AD" ]; then AD="$(bash scripts/cloud_action.sh --find 2>/dev/null || true)"; fi
if [ -n "$AD" ] && [ -d "$AD" ]; then
  mkdir -p "$AD/상태" "$AD/logs" 2>/dev/null || true
  printf '%s\n' "$ACCOUNT" > "$AD/계정.txt" 2>/dev/null || true
  # 열쇠 입력 페이지(오타 없는 열쇠 저장 UI) — 설치 때마다 최신본으로 갱신
  cp -f "scripts/노뮤트_열쇠입력.html" "$AD/노뮤트_열쇠입력.html" 2>/dev/null || true
  if [ ! -f "$AD/환경변수.txt" ]; then
    cat > "$AD/환경변수.txt" <<'EOF'
# 노뮤트 클라우드 액션 — 환경변수(키 값) 착지 슬롯.
# ⚠ 손편집보다 「노뮤트_열쇠입력.html」(같은 폴더)을 더블클릭해 채우는 걸 권장 — 오타 축 소멸.
# 여기 적은 값은 드라이브 동기화로 모든 기기에 퍼지고, 5분 서버가 매 회차 읽어서 주입한다.
# 형식: 이름=값 (한 줄 하나 · # 줄은 설명 · 이름_B64= 는 여러 줄 값을 한 줄로 접은 것 = 서버가 도로 편다)
# ⚠ 이 파일은 구글 계정에 로그인한 사람이면 읽을 수 있다 — 드라이브 계정 보안이 곧 열쇠 보안이다.
#
# ── 지금 없어도 도는 것(이미 동작): 기사 수집 · 속보 판정 · 경중 채점(컴퓨터의 클로드 로그인 사용)
# ── 아래는 깃허브 비밀칸(Secrets)에 있던 열쇠 전체 목록 — 값이 오면 해당 레인을 붙일 수 있다.
#    (GITHUB_TOKEN 은 목록에서 뺐다 — 컴퓨터의 깃 로그인이 그 역할을 대신한다)
#
# [산출물 저장소 R2 — 카드·이미지·영상 업로드 축]
#R2_ACCOUNT_ID=
#R2_ACCESS_KEY_ID=
#R2_SECRET_ACCESS_KEY=
#R2_BUCKET=
#R2_PUBLIC_BASE=
# [이미지 생성 — 카드 제작·리사이즈]
#GEMINI_API_KEY=
# [받아쓰기 STT — 자막·영상 요약]
#ELEVENLABS_API_KEY=
# [긴급 웹푸시 — 폰 알림]
#VAPID_PRIVATE_KEY=
#VAPID_SUBJECT=
# [유튜브 쿠키 2칸 — 영상·자막 받기 · 여러 줄 = 열쇠 입력 페이지로]
#YT_T_COOKIES=
#YT_T2_COOKIES=
# [SNS 수집 토큰]
#IG_ACCESS_TOKEN=
#FB_PAGE_TOKEN=
#FB_ACCESS_TOKEN=
#THREADS_ACCESS_TOKEN=
# [화면 재배포 훅 — 클라우드플레어]
#CF_DEPLOY_HOOK=
# [기타 제작·검색 축]
#OPENAI_API_KEY=
#OPENAI_API_KEY_NOMUTE=
#XAI_SECRET_PAT=
#XAI_REFRESH_TOKEN=
#HIGGSFIELD_REFRESH_TOKEN=
#NAVER_CLIENT_ID=
#NAVER_CLIENT_SECRET=
#YOUTUBE_API_KEY=
#REPLICATE_API_TOKEN=
#SAFETY_KEY=
#KIT_SYNC_TOKEN=
#GH_VARS_TOKEN=
#KOFIC_NOMUTE=
#KOFIC_NOMUTE_ID=
#KOFIC_NOMUTE_EX=
#KOFIC_NOMUTE_JAENAN=
#GDRIVE_SA_JSON=
# [클로드 구독 토큰 4칸 — 러너 폴오버용(컴퓨터에선 로컬 로그인이 우선이라 보통 불필요)]
#CLAUDE_CODE_OAUTH_TOKEN_EMS1130G=
#CLAUDE_CODE_OAUTH_TOKEN_MUTENO=
#CLAUDE_CODE_OAUTH_TOKEN_MUTENONA=
#CLAUDE_CODE_OAUTH_TOKEN_NOMUTEFB=
#
# [수집 조절값(선택)]  예) SCRAPE_TOP=20
EOF
  fi
  echo "① 드라이브 폴더 연결: $AD (열쇠 입력 페이지·환경변수 슬롯 준비됨)"
else
  echo "⚠ 드라이브 action 폴더를 못 찾았다 — 서버는 로컬로만 돈다(드라이브 데스크톱 앱 설치·동기화 뒤 이 설치를 재실행하면 붙는다)"
fi

# ── 파이썬·클로드 위치(윈도우 가짜 파이썬 껍데기 제외 = 이 레포 실측 봉합 문법 계승)
PY=""
for _c in python python3; do
  _p="$(command -v "$_c" 2>/dev/null || true)"
  case "$_p" in *WindowsApps*) continue;; esac
  [ -n "$_p" ] && { PY="$_p"; break; }
done
[ -n "$PY" ] || { echo "❌ 진짜 파이썬을 못 찾음 — 설치 파일을 처음부터 다시"; exit 1; }
"$PY" -m pip install --quiet feedparser requests 2>/dev/null \
  || "$PY" -m pip install --user --quiet feedparser requests 2>/dev/null \
  || "$PY" -m pip install --user --break-system-packages --quiet feedparser requests 2>/dev/null \
  || echo "⚠ 파이썬 부품(feedparser·requests) 설치 실패 — 수집이 안 돌면 이 화면을 클로드에게"
command -v claude >/dev/null 2>&1 || { command -v npm >/dev/null 2>&1 && npm install -g @anthropic-ai/claude-code >/dev/null 2>&1 || true; }
command -v claude >/dev/null 2>&1 || echo "⚠ 클로드 도구 없음 — 수집만 돌고 판정은 생략된다(설치 파일 재실행으로 붙는다)"
CL="$(command -v claude 2>/dev/null || true)"
pd="$(dirname "$PY")"; cdir=""; [ -n "$CL" ] && cdir="$(dirname "$CL")"

# ── ② 실행기(도구 절대경로 — 시계 환경은 PATH 가 빈약하다)
{ echo '#!/usr/bin/env bash'
  echo "export PATH=\"$pd${cdir:+:$cdir}:\$PATH\""
  echo 'exec ~/nomute-editor/scripts/cloud_action.sh'
} > "$HOME/nomute_cloud_run.sh"
chmod +x "$HOME/nomute_cloud_run.sh"
echo "② 실행기 준비 완료 (파이썬=$pd${cdir:+ · 클로드=$cdir})"

# ── ③ 5분 시계
case "$(uname -s)" in
  Darwin)
    if ( crontab -l 2>/dev/null | grep -v 'nomute-cloud-action' ; echo "*/5 * * * * /bin/bash $HOME/nomute_cloud_run.sh >> $HOME/cloud_action.log 2>&1 # nomute-cloud-action" ) | crontab - ; then
      echo "③ 5분 시계 등록 완료(crontab · 표식 = nomute-cloud-action)"
    else
      echo "❌ crontab 등록 실패 — 이 화면을 클로드에게"; exit 1
    fi
    echo "⚠ 맥 참고: 5분이 지나도 드라이브 상태 파일이 안 갱신되면 시스템 설정 → 개인정보 보호 및 보안 → 전체 디스크 접근에 cron 을 추가"
    ;;
  *)
    # 윈도우 — 조용한 실행 vbs + 작업 스케줄러. 슬래시 옵션 경로 변환 끄기 2중 + 실패 사유 표시(관측 소실 금지).
    BASHWIN="$(cygpath -w /usr/bin/bash 2>/dev/null || echo 'C:\Program Files\Git\bin\bash.exe')"
    cat > "$HOME/nomute_cloud.vbs" <<EOF
CreateObject("WScript.Shell").Run """$BASHWIN"" -lc ""~/nomute_cloud_run.sh >> ~/cloud_action.log 2>&1""", 0, False
EOF
    VBSWIN="$(cygpath -w "$HOME/nomute_cloud.vbs" 2>/dev/null || true)"
    ERR="$(MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' schtasks.exe /Create /F /SC MINUTE /MO 5 /TN NomuteCloudAction /TR "wscript.exe \"$VBSWIN\"" 2>&1)"
    if [ $? -eq 0 ]; then
      echo "③ 5분 시계 등록 완료(NomuteCloudAction)"
    else
      echo "❌ 5분 시계 등록 실패 — 사유: $ERR"
      echo "   (이 화면을 캡처해서 클로드에게)"; exit 1
    fi
    # 옛 5분 시계가 남아 있으면 이 서버로 대체한다(같은 일을 두 시계가 돌면 판정 호출만 겹친다)
    if MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' schtasks.exe /Query /TN NomutePcLane >/dev/null 2>&1; then
      MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' schtasks.exe /Delete /F /TN NomutePcLane >/dev/null 2>&1 \
        && echo "③-b 이전 5분 시계(NomutePcLane)를 이 서버로 대체(제거)했다"
    fi
    ;;
esac

# ── ④ 첫 발사
echo "④ 첫 발사를 지금 이 창에서 돌린다 — 수집 몇 분 + 판정 몇 분이 걸릴 수 있다. 창을 닫지 말 것…"
NOMUTE_NO_JITTER=1 bash "$HOME/nomute_cloud_run.sh"
echo
echo "── 착지 원장 ──"
cat "$HOME/.nomute_pc_lane_land" 2>/dev/null || echo "기록 없음"
HN="$(hostname 2>/dev/null || echo pc)"; HN="${HN%%.*}"
if [ -n "$AD" ] && [ -f "$AD/상태/$HN.txt" ]; then
  echo "── 드라이브 상태 파일(어느 기기에서든 보인다) ──"
  cat "$AD/상태/$HN.txt"
fi
echo "끝 — 착지 원장이 ok 로 시작하면 성공. 이후는 5분 시계가 알아서 돈다."
