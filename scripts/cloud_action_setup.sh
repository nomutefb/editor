#!/usr/bin/env bash
# 클라우드 액션 레인 설치 뒷단 — OS 를 갈라 「5분 시계」의 종점을 cloud_action.sh(겉옷)로 태운다(운영자 260814).
# 윈도우 = pc_setup.sh 가 이미 등록한 5분 시계(NomutePcLane + 조용한 실행 vbs)를 그대로 두고, 시계가 부르는
#   ~/nomute_pc_run.sh 의 종점만 pc_lane.sh → cloud_action.sh 로 바꾼다(시계 이중 등록 0 · schtasks 사본 0).
#   ⚠ 이후 pc_setup.bat 를 단독으로 다시 돌리면 종점이 pc_lane 으로 되돌아간다(클라우드 미러만 빠질 뿐
#     수집·판정은 그대로 돈다) — 다시 붙이려면 클라우드 설치 파일을 재더블클릭.
# 맥   = 실행기 ~/nomute_cloud_run.sh + crontab 5분 줄(phone_subs.sh 맥 설치 선례 문법 · 마커 주석으로 중복 차단).
# 공통 = 드라이브 action 폴더에 계정.txt(스캔 대조용)·환경변수.txt(키 착지 슬롯)·상태/logs 씨앗을 심고 첫 발사.
set -u
cd "$HOME/nomute-editor" 2>/dev/null || { echo "❌ 레포 없음: ~/nomute-editor — 설치 파일(bat/command)을 먼저 실행"; exit 1; }

# 계정값은 겉옷 정본에서 뽑는다(값 사본 0 — 두 곳에 적으면 조용히 갈린다 · check_cloud_action_chain 강제)
ACCOUNT="$(sed -n 's/^ACCOUNT="\([^"]*\)".*/\1/p' scripts/cloud_action.sh | head -1)"

# 드라이브 폴더: 설치 파일이 준 힌트(자기 폴더) 우선 · 없으면 겉옷의 스캔(--find)으로
AD=""
if [ -n "${NOMUTE_ACTION_HINT_WIN:-}" ]; then AD="$(cygpath -u "$NOMUTE_ACTION_HINT_WIN" 2>/dev/null || true)"; fi
[ -z "$AD" ] && AD="${NOMUTE_ACTION_HINT:-}"
[ -n "$AD" ] && AD="${AD%/}"
if [ -z "$AD" ] || [ ! -d "$AD" ]; then AD="$(bash scripts/cloud_action.sh --find 2>/dev/null || true)"; fi
if [ -n "$AD" ] && [ -d "$AD" ]; then
  mkdir -p "$AD/상태" "$AD/logs" 2>/dev/null || true
  printf '%s\n' "$ACCOUNT" > "$AD/계정.txt" 2>/dev/null || true
  if [ ! -f "$AD/환경변수.txt" ]; then
    cat > "$AD/환경변수.txt" <<'EOF'
# 노뮤트 클라우드 액션 — 환경변수(키 값) 착지 슬롯.
# 여기 적은 값은 드라이브 동기화로 모든 기기에 퍼지고, 5분 레인이 매 회차 읽어서 주입한다.
# 쓰는 법: 값을 넣고 그 줄 맨 앞의 # 를 지우면 다음 회차부터 켜진다.  형식 = 이름=값 (한 줄 하나)
# ⚠ 이 파일은 구글 계정에 로그인한 사람이면 읽을 수 있다 — 키를 넣는 순간 드라이브 계정 보안이 곧 키 보안이다.
#
# ── 지금 없어도 도는 것(이미 동작): 기사 수집 · 속보 판정 · 경중 채점(컴퓨터의 클로드 로그인 사용)
# ── 아래는 깃허브 비밀칸(Secrets)에 있던 열쇠 전체 목록 — 값이 오면 해당 레인을 이 컴퓨터에 붙일 수 있다.
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
# [유튜브 쿠키 2칸 — 영상·자막 받기]
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
  echo "드라이브 폴더 연결: $AD"
else
  echo "⚠ 드라이브 action 폴더를 못 찾았다 — 레인은 로컬로만 돈다(드라이브 데스크톱 앱 설치·동기화 뒤 이 설치를 재실행하면 붙는다)"
fi

case "$(uname -s)" in
  Darwin)
    PY="$(command -v python3 2>/dev/null || command -v python 2>/dev/null || true)"
    [ -n "$PY" ] || { echo "❌ 파이썬 없음 — python.org 에서 설치 후 재실행"; exit 1; }
    "$PY" -m pip install --quiet feedparser requests 2>/dev/null \
      || "$PY" -m pip install --user --quiet feedparser requests 2>/dev/null \
      || "$PY" -m pip install --user --break-system-packages --quiet feedparser requests 2>/dev/null \
      || echo "⚠ 파이썬 부품(feedparser·requests) 설치 실패 — 수집이 안 돌면 이 화면을 클로드에게"
    command -v claude >/dev/null 2>&1 || { command -v npm >/dev/null 2>&1 && npm install -g @anthropic-ai/claude-code >/dev/null 2>&1 || true; }
    command -v claude >/dev/null 2>&1 || echo "⚠ 클로드 도구 없음 — 수집만 돌고 판정은 생략된다(노드+npm 설치 후 재실행하면 붙는다)"
    pd="$(dirname "$PY")"; cdir=""; command -v claude >/dev/null 2>&1 && cdir="$(dirname "$(command -v claude)")"
    { echo '#!/usr/bin/env bash'
      echo "export PATH=\"$pd${cdir:+:$cdir}:\$PATH\""
      echo 'exec ~/nomute-editor/scripts/cloud_action.sh'
    } > "$HOME/nomute_cloud_run.sh"
    chmod +x "$HOME/nomute_cloud_run.sh"
    if ( crontab -l 2>/dev/null | grep -v 'nomute-cloud-action' ; echo "*/5 * * * * /bin/bash $HOME/nomute_cloud_run.sh >> $HOME/cloud_action.log 2>&1 # nomute-cloud-action" ) | crontab - ; then
      echo "① 5분 시계 등록 완료(crontab · 표식 = nomute-cloud-action)"
    else
      echo "❌ crontab 등록 실패 — 이 화면을 클로드에게"; exit 1
    fi
    echo "⚠ 맥 참고: 5분이 지나도 드라이브 상태 파일이 안 갱신되면 시스템 설정 → 개인정보 보호 및 보안 → 전체 디스크 접근에 cron 을 추가"
    RUN="$HOME/nomute_cloud_run.sh"
    ;;
  *)
    # 윈도우 Git-Bash — 5분 시계·vbs 등록은 pc_setup.sh 소관(이중 등록 금지). 여기선 존재 확인 + 종점 교체만.
    [ -f "$HOME/nomute_pc_lane.vbs" ] || { echo "❌ 5분 시계 부품(vbs)이 없다 — 설치 bat 를 처음부터 다시(기본 설치 단계 미완)"; exit 1; }
    MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' schtasks.exe /Query /TN NomutePcLane >/dev/null 2>&1 \
      || { echo "❌ 5분 시계(NomutePcLane)가 등록돼 있지 않다 — 설치 bat 를 처음부터 다시"; exit 1; }
    # 실행기 재작성 = pc_setup.sh ① 블록의 동작 사본(창작 0 · 가짜 파이썬 껍데기 제외 동일) — 종점만 다르다.
    PY=""
    for _c in python python3; do
      _p="$(command -v "$_c" 2>/dev/null || true)"
      case "$_p" in *WindowsApps*) continue;; esac
      [ -n "$_p" ] && { PY="$_p"; break; }
    done
    [ -n "$PY" ] || { echo "❌ 진짜 파이썬을 못 찾음 — 설치 bat 를 처음부터 다시"; exit 1; }
    CL="$(command -v claude 2>/dev/null || true)"
    pd="$(dirname "$PY")"; cdir=""; [ -n "$CL" ] && cdir="$(dirname "$CL")"
    { echo '#!/usr/bin/env bash'
      echo "export PATH=\"$pd${cdir:+:$cdir}:\$PATH\""
      echo 'exec ~/nomute-editor/scripts/cloud_action.sh'
    } > "$HOME/nomute_pc_run.sh"
    chmod +x "$HOME/nomute_pc_run.sh"
    echo "① 5분 시계 종점 교체 완료: pc_lane → cloud_action(겉옷 경유 · 몸통 동일)"
    RUN="$HOME/nomute_pc_run.sh"
    ;;
esac

echo "② 첫 발사를 지금 이 창에서 돌린다 — 수집 몇 분 + 판정 몇 분이 걸릴 수 있다. 창을 닫지 말 것…"
NOMUTE_NO_JITTER=1 bash "$RUN"
echo
echo "── 착지 원장 ──"
cat "$HOME/.nomute_pc_lane_land" 2>/dev/null || echo "기록 없음"
HN="$(hostname 2>/dev/null || echo pc)"; HN="${HN%%.*}"
if [ -n "$AD" ] && [ -f "$AD/상태/$HN.txt" ]; then
  echo "── 드라이브 상태 파일(어느 기기에서든 보인다) ──"
  cat "$AD/상태/$HN.txt"
fi
echo "끝 — 착지 원장이 ok 로 시작하면 성공. 이후는 5분 시계가 알아서 돈다."
