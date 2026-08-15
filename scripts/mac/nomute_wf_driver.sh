#!/usr/bin/env bash
# 노뮤트 범용 워크플로 잡 실행기(260815 코워크) — kind별 정본 yml 스텝을 이름으로 추출·실행(edit 드라이버 문법 계승 · 값 창작 0).
# 사용: nomute_wf_driver.sh <kind> <job.json>  · rc: 0=완료 · 9=구식 잡 재접수 · 그 외=실패
set -u
KIND="$1"; J="$2"; REPO="${NOMUTE_WORKER_REPO:-$HOME/nomute-worker}"; cd "$REPO" || exit 1
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8
case "$KIND" in
  vidl) W=".github/workflows/vidl-make.yml"; API=vidl;;
  conv) W=".github/workflows/conv-make.yml"; API=conv;;
  moreimg) W=".github/workflows/moreimg.yml"; API=moreimg;;
  imgedit) W=".github/workflows/imgedit-make.yml"; API=imgedit;;
  thumbredo) W=".github/workflows/thumb-redo.yml"; API=thumbredo;;
  resize) W=".github/workflows/img-resize.yml"; API=resize;;
  upscale) W=".github/workflows/img-upscale.yml"; API=upscale;;
  framethumb) W=".github/workflows/framethumb-make.yml"; API=framethumb;;
  make-cards) W=".github/workflows/card-make.yml"; API=make-cards;;
  revise) W=".github/workflows/news-revise.yml"; API=revise;;
  revise-cards) W=".github/workflows/cards-revise.yml"; API=revise-cards;;
  tr) W=".github/workflows/tr-auto.yml"; API=tr;;
  nb) W=".github/workflows/nb-make.yml"; API=nb;;
  k) W=".github/workflows/k-make.yml"; API=k;;
  sb) W=".github/workflows/sb-make.yml"; API=sb;;
  ly) W=".github/workflows/ly-make.yml"; API=ly;;
  song) W=".github/workflows/song-make.yml"; API=song;;
  track) W=".github/workflows/track-make.yml"; API=track;;
  voice) W=".github/workflows/voice-make.yml"; API=voice;;
  *) echo "[wf] 미지원 kind=$KIND"; exit 3;;
esac
PREP=$(python3 - "$J" <<'PY'
import json,sys,shlex
j=json.load(open(sys.argv[1]))
ins=j.get('inputs')
if not (isinstance(ins,dict) and ins.get('id')):
    open('/tmp/wf_repost.json','w',encoding='utf-8').write(j.get('body') or '{}')
    print('MODE=repost'); sys.exit(0)
print('MODE=run')
if 'opts' in ins:
    try: ins['opts']=json.dumps(json.loads(ins.get('opts') or '{}'),ensure_ascii=False,separators=(',',':'))
    except Exception: pass
for k,v in ins.items():
    if isinstance(v,(str,int,float)): print('I_'+k.upper().replace('-','_')+'='+shlex.quote(str(v)))
PY
) || exit 1
eval "$PREP"
[ -n "${I_OPTS:-}" ] || I_OPTS="{}"   # 260815 코워크: bash ${X:-{}}는 첫 }에서 닫혀 값 있으면 잉여 } 부착(framethumb Extra data 실측) — 가드로 대체
if [ "${MODE:-}" = repost ]; then
  curl -s --max-time 40 -X POST "https://apps.nomute.kr/api/$API" -H 'Content-Type: application/json' --data @/tmp/wf_repost.json >/dev/null 2>&1
  exit 9
fi

export GITHUB_ENV=/tmp/wf_ghenv.txt; : > "$GITHUB_ENV"
srcenv(){ [ -s "$GITHUB_ENV" ] && { set -a; . "$GITHUB_ENV"; set +a; }; return 0; }

wf_land(){ # 'Commit results'가 GH 템플릿 잔존으로 거부될 때의 동형 폴백(값 창작 0: yml add 경로·메시지 그대로, ${{ inputs.id }}→$I_ID 치환만) — 260815 코워크
  local msg="$1"; shift; local staged=0
  for p in "$@"; do [ -e "$p" ] && git add "$p" 2>/dev/null && staged=1; done
  [ "$staged" = 1 ] || return 0
  git diff --cached --quiet 2>/dev/null && return 0
  git commit -q -m "$msg" 2>/dev/null || return 0
  for _i in 1 2 3 4; do
    git push -q origin HEAD:main 2>/dev/null && { echo "[wf] 폴백 착지: $msg"; return 0; }
    git fetch -q --deepen=50 origin main 2>/dev/null; git pull --rebase --autostash -X ours -q origin main 2>/dev/null
  done
  echo "[wf] 폴백 착지 실패(다음 편승 대기): $msg"; return 0
}

runstep(){
  python3 - "$W" "$1" > /tmp/wf_step.sh <<'PY' || { echo "[wf] 스텝 추출 실패: $1"; return 3; }
import yaml,sys
d=yaml.safe_load(open(sys.argv[1],encoding='utf-8'))
for s in list(d['jobs'].values())[0]['steps']:
    n=s.get('name') or ''
    if n.startswith(sys.argv[2]) and s.get('run'):
        sys.stdout.write(s['run']); sys.exit(0)
sys.exit(3)
PY
  if grep -q '\${{' /tmp/wf_step.sh; then echo "[wf] 스텝에 GH 템플릿 잔존 — 실행 불가: $1"; return 4; fi
  bash /tmp/wf_step.sh; local rc=$?
  srcenv
  return $rc
}
export AWS_ACCESS_KEY_ID="${R2_ACCESS_KEY_ID:-}" AWS_SECRET_ACCESS_KEY="${R2_SECRET_ACCESS_KEY:-}"
# 회전 열쇠 로컬 되쓰기 셔틀(260815) — 그록/힉스필드 갱신 열쇠를 깃 비밀값 대신 드라이브 정본+캐시에 되쓴다(shared/grok_api._persist_secret 로컬 분기)
export NOMUTE_SECRET_FILE="$HOME/Library/CloudStorage/GoogleDrive-ems1130g@gmail.com/내 드라이브/action/환경변수.txt"
export NOMUTE_SECRET_FILE_2="$HOME/nomute-action/환경변수.txt"
# claude 계정 토큰 사슬(워크플로 account=MUTENO 기본 동형) — 키 없으면 맥 키체인 로그인 사용
if [ -n "${CLAUDE_CODE_OAUTH_TOKEN_MUTENO:-}" ]; then
  export CLAUDE_CODE_OAUTH_TOKEN="$CLAUDE_CODE_OAUTH_TOKEN_MUTENO"
  export CLAUDE_CODE_OAUTH_TOKEN_ALT="${CLAUDE_CODE_OAUTH_TOKEN_NOMUTEFB:-}"
  export CLAUDE_CODE_OAUTH_TOKEN_ALT2="${CLAUDE_CODE_OAUTH_TOKEN_EMS1130G:-}"
  export CLAUDE_CODE_OAUTH_TOKEN_ALT3="${CLAUDE_CODE_OAUTH_TOKEN_MUTENONA:-}"
fi
export ACTIVE_ACCOUNT="${ACTIVE_ACCOUNT:-MUTENO}"
FAILED=0
case "$KIND" in
vidl)
  export IN_ID="$I_ID" IN_URL="${I_URL:-}" IN_MODE="${I_MODE:-both}" IN_Q="${I_Q:-best}"
  export YT_COOKIES="${YT_T2_COOKIES:-}" YT_COOKIES_2="${YT_T_COOKIES:-}"
  export RUN_ID="mac-$(date +%H%M%S)" BRANCH=main PAGES_COALESCE="${PAGES_COALESCE:-}"
  # yt-dlp 축 = 최신판 필수(구판 = 유튜브 SABR/403 실측 260815) → 스코프 심(brew py3.14 + yt-dlp 최신)
  PATH="$HOME/nomute-pyw:$PATH" runstep '받기 (' || FAILED=1
  [ "$FAILED" = 1 ] && { runstep '실패 기록' || true; }
  runstep 'Commit output' || true
  [ "$FAILED" = 0 ] && { runstep '완료 알림' || true; }
  ;;
conv)
  export IN_ID="$I_ID" CONV_OPTS="$I_OPTS" BRANCH=main
  export YT_COOKIES="${YT_T2_COOKIES:-}" YT_COOKIES_NAME=YT_T2_COOKIES
  export YT_COOKIES_2="${YT_T_COOKIES:-}" YT_COOKIES_2_NAME=YT_T_COOKIES
  if [ -n "${I_URL:-}" ]; then export URL="$I_URL"; PATH="$HOME/nomute-pyw:$PATH" runstep '소스 확보 (URL)' || FAILED=1
  elif [ -n "${I_R2_SRC:-}" ]; then export R2_SRC="$I_R2_SRC"; runstep '소스 확보 (R2 직업로드' || FAILED=1
  elif [ -n "${I_FILE:-}" ]; then export FILE="$I_FILE" UP_BRANCH="${I_UP_BRANCH:-}"; runstep '소스 확보 (업로드 파일)' || FAILED=1
  else echo "영상 입력이 없어 — URL이나 파일을 넣어줘." > /tmp/conv_err.txt; FAILED=1; fi
  [ "$FAILED" = 0 ] && { runstep '변환 (' || FAILED=1; }
  [ "$FAILED" = 1 ] && { runstep '실패 기록' || true; }
  runstep 'Commit output' || true
  if [ -n "${I_UP_BRANCH:-}" ]; then export UP_BRANCH="$I_UP_BRANCH"; runstep '업로드 브랜치 정리' || true; fi
  runstep '임시 업로드 청소' || true
  [ "$FAILED" = 0 ] && { runstep '변환 완료 푸시' || true; }
  ;;
moreimg)
  export MOREIMG_STEM="${I_STEM:-}" MOREIMG_WANT="${I_WANT:-}" MOREIMG_ROUND="" GH_TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
  runstep 'Find more images' || FAILED=1
  runstep 'Commit results' || true
  [ "$FAILED" = 0 ] && { runstep '미달 시 다음 라운드 발사' || true; }   # 깃허브 죽어있으면 무해 실패(부활 시 라운드 복원)
  ;;
imgedit)
  export IN_ID="$I_ID" BRANCH=main IMG_MODE="${I_MODE:-render}"
  if [ "${I_MODE:-}" = analyze ]; then
    export FILE="${I_FILE:-}" UP_BRANCH="${I_UP_BRANCH:-}"
    runstep '소스 확보 (analyze' || FAILED=1
    [ "$FAILED" = 0 ] && { runstep '피사체 검출' || FAILED=1; }
  else
    export RENDER="${I_RENDER:-}"
    runstep '모자이크 렌더' || FAILED=1
  fi
  [ "$FAILED" = 1 ] && { runstep '실패 기록' || true; }
  runstep 'Commit output' || true
  if [ -n "${I_UP_BRANCH:-}" ]; then export UP_BRANCH="$I_UP_BRANCH"; runstep '업로드 브랜치 정리' || true; fi
  ;;
thumbredo)
  export ARTICLE="${I_ARTICLE:-}" SID="${I_SID:-}" WISH="${I_WISH:-}" THUMB_GATE="${THUMB_GATE:-}" THUMB_REF="${THUMB_REF:-}" CF_DEPLOY_HOOK=""
  runstep 'AI 썸네일 재생성' || FAILED=1
  runstep 'Commit' || true
  wf_land "imgedit: $I_ID 출력(맥 잡워커)" "viewer/imgedit_out/$I_ID"   # 템플릿 거부 폴백(260815)
  ;;
resize)
  export RESIZE_ID="$I_ID" RESIZE_SRC="${I_SRC:-}" RESIZE_OPTS="$I_OPTS"
  export RESIZE_IMG_MODEL="${RESIZE_IMG_MODEL:-}" RESIZE_JUDGE_MODEL="${RESIZE_JUDGE_MODEL:-}" RESIZE_SEED="${RESIZE_SEED:-}" RESIZE_TRIES="${RESIZE_TRIES:-}" RESIZE_KEEP_REJ="${RESIZE_KEEP_REJ:-}"
  runstep 'Resize' || FAILED=1
  runstep 'Commit results' || true
  wf_land "resize: 비율 재구성 산출 ($I_ID) (맥 잡워커)" viewer/gen_out/   # 템플릿 거부 폴백(260815)
  ;;
upscale)
  export UPSCALE_ID="$I_ID" UPSCALE_SRC="${I_SRC:-}" UPSCALE_OPTS="$I_OPTS"
  runstep 'Upscale' || FAILED=1
  runstep 'Commit results' || true
  wf_land "upscale: 화질↑ 산출 ($I_ID) (맥 잡워커)" viewer/gen_out/   # 템플릿 거부 폴백(260815)
  ;;
framethumb)
  export FT_ID="$I_ID" FT_OPTS="$I_OPTS" BRANCH=main
  export YT_COOKIES="${YT_T2_COOKIES:-}" YT_COOKIES_NAME=YT_T2_COOKIES
  export YT_COOKIES_2="${YT_T_COOKIES:-}" YT_COOKIES_2_NAME=YT_T_COOKIES
  if [ -n "${I_URL:-}" ]; then export URL="$I_URL"; PATH="$HOME/nomute-pyw:$PATH" runstep '소스 확보 (URL)' || FAILED=1
  elif [ -n "${I_R2_SRC:-}" ]; then export R2_SRC="$I_R2_SRC"; runstep '소스 확보 (R2 직업로드' || FAILED=1
  elif [ -n "${I_FILE:-}" ]; then export FILE="$I_FILE" UP_BRANCH="${I_UP_BRANCH:-}"; runstep '소스 확보 (업로드 파일)' || FAILED=1
  else echo "영상 입력이 없어" > /tmp/ft_err.txt; FAILED=1; fi
  [ "$FAILED" = 0 ] && { runstep '체인 실행' || FAILED=1; }
  runstep '결과 커밋' || true
  wf_land "framethumb: $I_ID 산출(맥 잡워커)" "viewer/ft_out/$I_ID"   # 커밋 불발 폴백(260815)
  if [ -n "${I_UP_BRANCH:-}" ]; then export UP_BRANCH="$I_UP_BRANCH"; runstep '업로드 브랜치 정리' || true; fi
  runstep '임시 업로드 청소' || true
  ;;
make-cards)
  export TARGET="${I_ARTICLE:-}" MODE="${I_MODE:-full}" CARD_N="${I_CARD:-}" EDIT_TEXT="${I_TEXT:-}" EDIT_WISH="${I_WISH:-}" EDIT_SYNC="${I_SYNC:-}" EDIT_SCENE_PATH="${I_SCENE:-}"
  export CARD_COV_GUARD="${CARD_COV_GUARD:-1}" CARD_SYS_PROMPT="${CARD_SYS_PROMPT:-1}"
  runstep 'Install deps' || true   # 상비 환경이면 즉시 통과(멱등)
  runstep 'Make cards' || FAILED=1   # scene 선확보 스텝은 GH 템플릿 잔존 → 스킵(맥 풀클론+pull = scene 이미 로컬)
  ;;
revise)
  export FILE="${I_FILE:-}" INSTRUCTION="${I_INSTRUCTION:-}" BRANCH=main
  export VIEWER_BASE="${VIEWER_BASE:-}" NOTIFY_TITLE="${NOTIFY_TITLE:-}" NOTIFY_BODY_SUFFIX="${NOTIFY_BODY_SUFFIX:-}" NOTIFY_TAG_PREFIX="${NOTIFY_TAG_PREFIX:-}"
  runstep 'Revise IG/Thread' || FAILED=1
  runstep 'Commit result' || true
  [ "$FAILED" = 0 ] && { runstep '수정 완료 웹푸시' || true; }
  ;;
revise-cards)
  export FILE="${I_FILE:-}" INSTRUCTION="${I_INSTRUCTION:-}" BRANCH=main
  export VIEWER_BASE="${VIEWER_BASE:-}" NOTIFY_TITLE="${NOTIFY_TITLE:-}" NOTIFY_BODY_SUFFIX="${NOTIFY_BODY_SUFFIX:-}" NOTIFY_TAG_PREFIX="${NOTIFY_TAG_PREFIX:-}"
  runstep 'Revise cards.md' || FAILED=1
  runstep 'Commit result' || true
  [ "$FAILED" = 0 ] && { runstep '카드 수정 완료 웹푸시' || true; }
  ;;
tr)
  export IN_ID="$I_ID" LINES="${I_LINES:-}" CTX="${I_CTX:-}" BRANCH=main
  if [ -n "${I_IMGKEY:-}" ]; then export R2_SRC="$I_IMGKEY" AWS_DEFAULT_REGION=auto; runstep 'Fetch source photo' || true; fi
  runstep 'Make tr plan' || FAILED=1
  runstep 'Commit output' || true
  ;;
nb)
  export IN_ID="$I_ID" BRANCH=main NB_MAX_SEC="${NB_MAX_SEC:-14400}" NB_STT_MAX_SEC="${NB_STT_MAX_SEC:-3600}" NB_LIST_MAX="${NB_LIST_MAX:-200}"
  case "${I_MODE:-url}" in
    text) export NB_TEXT="${I_TEXT:-}" NB_TITLE="${I_TITLE:-}" NB_KIND="${I_KIND:-}"; runstep '텍스트 소스 수용' || FAILED=1;;
    file) export NB_FILE="${I_FILE:-}" R2_SRC="${I_R2_SRC:-}"
          runstep '파일 소스 회수' || FAILED=1
          [ "$FAILED" = 0 ] && { runstep '파일 STT' || FAILED=1; };;
    *)    export URL="${I_URL:-}" YT_COOKIES="${YT_T2_COOKIES:-}" YT_COOKIES_NAME=YT_T2_COOKIES YT_COOKIES_2="${YT_T_COOKIES:-}" YT_COOKIES_2_NAME=YT_T_COOKIES
          PATH="$HOME/nomute-pyw:$PATH" runstep '메타·자막 추출' || FAILED=1
          if [ "$FAILED" = 0 ] && [ "${NB_NEED_STT:-}" = 1 ]; then PATH="$HOME/nomute-pyw:$PATH" runstep 'STT (오디오만' || FAILED=1; fi;;
  esac
  export NB_ASK="${I_ASK:-}"
  if [ "$FAILED" = 0 ] && [ "${NB_LIST:-}" != 1 ]; then runstep '자료 노트 생성' || FAILED=1; fi
  [ "$FAILED" = 1 ] && { runstep '실패 기록' || true; }
  runstep 'Commit output' || true
  ;;
k)
  export IN_ID="$I_ID" SCENE="${I_SCENE:-}" BRANCH=main
  runstep 'Make k prompt' || FAILED=1
  if [ "$FAILED" = 0 ] && [ "${I_REFIMAGE:-false}" = "true" ]; then runstep 'Reference image' || FAILED=1; fi
  runstep 'Commit output' || true
  ;;
sb)
  export IN_ID="$I_ID" STORY="${I_STORY:-}" DIRECTOR="${I_DIRECTOR:-fable}" BASE="${I_BASE:-}" BRANCH=main
  export OPENAI_MODEL="${OPENAI_MODEL:-}" REFGEN_PREFIX=sb_out REFGEN_ASPECT="9:16"
  SB_SHOOT="${I_SHOOT:-grok}"
  if [ -z "$STORY" ] && [ -n "$BASE" ]; then runstep 'Reuse storyboard' || FAILED=1
  else runstep 'Make storyboard' || FAILED=1; fi
  # Storyboard audit — 정본 run에 ${{ inputs.id }} 경로 2개 → 동형 번역(치환만 · 구조 동일)
  if [ "$FAILED" = 0 ]; then
    MD="viewer/sb_out/${IN_ID}/board.md"
    if [ -s "$MD" ]; then python3 .github/scripts/sb_audit.py "$MD" "viewer/sb_out/${IN_ID}" || FAILED=1
    else echo "콘티 검증: 미시도(board.md 없음)"; fi
  fi
  if [ "$FAILED" = 0 ] && [ "${I_REFIMAGE:-true}" != "false" ]; then runstep 'Reference images' || FAILED=1; fi
  if [ "$FAILED" = 0 ] && [ "$SB_SHOOT" = motion ] && [ -z "$STORY" ] && [ -n "$BASE" ]; then
    bash apps/mg/setup.sh || FAILED=1   # runner-setup 동형(apt 축 = 맥 상비 → setup.sh 단일출처)
    [ "$FAILED" = 0 ] && { runstep 'Motion render' || FAILED=1; }
  fi
  case "$SB_SHOOT" in grok|seedance*) [ "$FAILED" = 0 ] && { runstep 'Storyboard sheet' || FAILED=1; };; esac
  if [ "$FAILED" = 0 ] && [ -z "$STORY" ] && [ -n "$BASE" ]; then
    export GROK_SOUND="${I_SOUND:-1}" GROK_SB_CUT_MAX="${I_CUTMAX:-}"
    if [ "$SB_SHOOT" = grok ]; then
      export XAI_TOKEN_STORE="$HOME/nomute-action/grok_token.json"   # runner.temp 동형(맥=지속 캐시)
      runstep 'Grok video' || FAILED=1
    fi
    case "$SB_SHOOT" in seedance*)
      export SB_LANE=seedance SD_RES="${I_RES:-}" SB_COST_CAP="${SB_COST_CAP:-400}" SD_POLL_MAX_SEC=3000
      SD_PRESET=A; [ "$SB_SHOOT" = seedance20 ] && SD_PRESET=B; export SD_PRESET
      SD_SHOT_SEC=""; [ "$SB_SHOOT" = seedance5 ] && SD_SHOT_SEC=5; export SD_SHOT_SEC
      runstep 'Seedance video' || FAILED=1;;
    esac
  fi
  runstep 'Commit output' || true
  ;;
ly)
  export IN_ID="$I_ID" OPTS="${I_OPTS:-}" BRANCH=main AWS_DEFAULT_REGION=auto
  LY_SRC_ON=0; { [ -n "${I_URL:-}" ] || [ -n "${I_FILE:-}" ] || [ -n "${I_R2_SRC:-}" ]; } && LY_SRC_ON=1
  # ffmpeg+한글폰트 스텝(우분투 apt) = 맥 상비(탭 풀빌드+Noto) — libass만 확인 · 미비 = 큐 보존(edit rc7 동형)
  if [ "${I_REBURN:-0}" = "1" ] || [ "$LY_SRC_ON" = 1 ]; then
    ffmpeg -hide_banner -filters 2>/dev/null | grep -q " ass " || { echo "[wf] ffmpeg libass 미준비 — 큐 보존"; exit 7; }
  fi
  if [ "${I_REBURN:-0}" = "1" ]; then
    runstep '재합성 소스 회수' || FAILED=1
    if [ "$FAILED" = 0 ] && [ -n "${I_SUBS:-}" ]; then export SUBS="$I_SUBS"; runstep '편집 자막 반영' || FAILED=1; fi
    [ "$FAILED" = 0 ] && { runstep '자막 번인' || true; }   # 정본 continue-on-error:true 동형
    runstep '번인 기록 백필' || true
  else
    export SUBS="${I_SUBS:-}" LY_STT_PRECISION="${I_STT_PREC:-}" LY_STT_ENGINE="${LY_STT_ENGINE:-}" LY_STT_MAX_SEC="${LY_STT_MAX_SEC:-}"
    if [ -n "${I_URL:-}" ]; then export URL="$I_URL"; PATH="$HOME/nomute-pyw:$PATH" runstep 'STT (영상 URL' || FAILED=1
    elif [ -n "${I_R2_SRC:-}" ]; then export R2_SRC="$I_R2_SRC"
      runstep 'R2 소스 회수' || FAILED=1
      [ "$FAILED" = 0 ] && { runstep 'STT (업로드 파일' || FAILED=1; }
    elif [ -n "${I_FILE:-}" ]; then export FILE="$I_FILE" UP_BRANCH="${I_UP_BRANCH:-}"; runstep 'STT (업로드 파일' || FAILED=1
    fi
    if [ "$FAILED" = 0 ] && [ "${I_EARLY_SEGS:-0}" = "1" ] && [ "$LY_SRC_ON" = 1 ]; then runstep '조기 segments.json 커밋' || FAILED=1; fi
    if [ "$FAILED" = 0 ] && [ "$LY_SRC_ON" = 1 ]; then case "$OPTS" in *'"lang":"src"'*) runstep '원문 패스트패스' || FAILED=1;; esac; fi
    if [ "$FAILED" = 0 ] && [ "${LY_FASTPATH:-}" != "1" ]; then
      export LY_MODEL="${LY_MODEL:-}" LY_EFFORT="${LY_EFFORT:-}"
      runstep 'Make ly subtitles' || FAILED=1
    fi
    if [ "$FAILED" = 0 ] && [ -n "${LY_VIDEO:-}" ]; then runstep '조기 subs 커밋' || FAILED=1; fi
    # Demucs 설치(bgm+burn) — 미설치면 ly_burn 원본 소리 폴백(edit 드라이버 동형 · || true)
    if [ "$FAILED" = 0 ] && [ -n "${LY_VIDEO:-}" ] && [ "${LY_NOBURN:-}" != "1" ]; then
      case "$OPTS" in *'"bgm":true'*) case "$OPTS" in *'"burn":true'*) runstep 'Demucs 설치' || true;; esac;; esac
    fi
    if [ "$FAILED" = 0 ] && [ "$LY_SRC_ON" = 1 ]; then runstep '조기 교정본 픽업' || FAILED=1; fi
    if [ "$LY_SRC_ON" = 1 ]; then
      [ "$FAILED" = 0 ] && { runstep '자막 번인' || true; }   # 정본 continue-on-error:true 동형
      runstep '번인 기록 백필' || true
    fi
  fi
  [ "$FAILED" = 1 ] && { runstep '실패 기록' || true; }
  runstep 'Commit output' || true
  if [ -n "${I_UP_BRANCH:-}" ]; then export UP_BRANCH="$I_UP_BRANCH"; runstep '업로드 브랜치 정리' || true; fi
  runstep '임시 업로드 청소' || true
  ;;
song)
  export IN_ID="$I_ID" MODE="${I_MODE:-suno}" GENRE="${I_GENRE:-자동}" EXPRESS="${I_EXPRESS:-자동}" MOOD="${I_MOOD:-자동}" THEME="${I_THEME:-자동}" STORY="${I_STORY:-}" PICK="${I_PICK:-}" OPTS="${I_OPTS:-}" BRANCH=main
  runstep '텍스트 생성' || FAILED=1
  if [ "$FAILED" = 0 ] && [ "$MODE" = lyria ]; then export SONG_ID="$I_ID"; runstep '구글 곡 생성' || FAILED=1; fi
  [ "$FAILED" = 1 ] && { runstep '실패 기록' || true; }
  # Commit output — 정본 run에 ${{ inputs.mode }} 1개 잔존 → 동형 번역($MODE 치환 · 구조 동일 · push 실패 = 경고 후 잔존(타 kind Commit 스텝 || true 관례))
  if [ -n "$IN_ID" ]; then case "$IN_ID" in *[!0-9a-f-]*) echo "잘못된 id — 커밋 스킵";; *)
    git config user.name "nomute-bot"; git config user.email "bot@nomute.local"
    git add "viewer/song_out/${IN_ID}" 2>/dev/null || true
    git add metrics 2>/dev/null || true
    if git commit -q -m "song: ${IN_ID} 음원 출력(${MODE})"; then
      pushed=0
      for i in 1 2 3 4 5; do
        git fetch --deepen=100 origin main 2>/dev/null || true
        if git fetch origin "$BRANCH" && git rebase "origin/$BRANCH" && git push origin "HEAD:$BRANCH"; then pushed=1; break; fi
        git rebase --abort 2>/dev/null || true; sleep $((i*3))
      done
      [ "$pushed" = 1 ] || echo "[wf] song push 5회 실패 — 로컬 커밋 잔존(다음 잡 pull이 봉합)"
    else echo "커밋할 것 없음"; fi;;
  esac; fi
  # 배포 게이트 스텝 = 스킵(need_deploy 깃발이 재배포) · 완료 푸시 = 정본 always()&&lyria 동형
  [ "$MODE" = lyria ] && { runstep '완료 푸시' || true; }
  ;;
track)
  export IN_ID="$I_ID" TRACK_MODE="${I_MODE:-analyze}" BRANCH=main
  runstep 'mode 가드' || FAILED=1
  # TRACK_HEAVY = job env 식 동형 번역(render && render에 keying|maskfx)
  TRACK_HEAVY=""; if [ "$TRACK_MODE" = render ]; then case "${I_RENDER:-}" in *keying*|*maskfx*) TRACK_HEAVY=1;; esac; fi
  export TRACK_HEAVY
  # 트래킹 환경 = runner-setup 동형(apt 축 = 맥 상비 → setup.sh 단일출처 · 모델 캐시 ~/.cache/nomute-track)
  [ "$FAILED" = 0 ] && { bash apps/track/setup.sh || FAILED=1; }
  if [ "$FAILED" = 0 ] && [ "$TRACK_MODE" = analyze ]; then
    if [ -n "${I_URL:-}" ]; then export URL="$I_URL"; PATH="$HOME/nomute-pyw:$PATH" runstep '소스 확보 (analyze · URL' || FAILED=1
    elif [ -n "${I_FILE:-}" ] || [ -n "${I_R2_SRC:-}" ]; then
      export FILE="${I_FILE:-}" UP_BRANCH="${I_UP_BRANCH:-}" R2_SRC="${I_R2_SRC:-}" AWS_DEFAULT_REGION=auto
      runstep '소스 확보 (analyze · 업로드' || FAILED=1
    fi
    [ "$FAILED" = 0 ] && { runstep '인물 분석' || FAILED=1; }
    if [ "$FAILED" = 0 ] && [ "${I_CAP:-1}" = "1" ]; then
      runstep '조기 tracks.json 커밋' || true   # 정본 continue-on-error:true 동형
      export TRACK_CAP=1
      runstep '카드 캡션' || true               # 정본 continue-on-error:true 동형(fail-soft)
    fi
  fi
  if [ "$FAILED" = 0 ] && [ "$TRACK_MODE" = render ]; then export RENDER="${I_RENDER:-}"; runstep '렌더' || FAILED=1; fi
  [ "$FAILED" = 1 ] && { runstep '실패 기록' || true; }
  runstep 'Commit output' || true
  # 배포 게이트 스텝 = 스킵(track_out = api/track 라이브 서빙) · 완료 푸시 = 정본 always() 동형
  runstep '트래킹 완료 푸시' || true
  if [ -n "${I_UP_BRANCH:-}" ]; then export UP_BRANCH="$I_UP_BRANCH"; runstep '업로드 브랜치 정리' || true; fi
  runstep '임시 업로드 청소' || true
  ;;
voice)
  export IN_ID="$I_ID" VC_MODE="${I_MODE:-train}" BRANCH=main
  if [ "$VC_MODE" = train ]; then
    # 준비 스텝(우분투 apt+리눅스 torch 핀) = 맥 동형: ffmpeg·zip 상비 + torch/demucs/soundfile 확인 — 미비 = 큐 보존(rc7)
    command -v ffmpeg >/dev/null 2>&1 && command -v zip >/dev/null 2>&1 || { echo "[wf] voice: ffmpeg/zip 미비 — 큐 보존"; exit 7; }
    python3 -c "import torch, demucs, soundfile" 2>/dev/null || { echo "[wf] voice: torch/demucs 미준비 — 큐 보존(다음 틱 재시도)"; exit 7; }
    export FILE="${I_FILE:-}" UP_BRANCH="${I_UP_BRANCH:-}" CONSENT="${I_CONSENT:-}" R2_SRC="${I_R2_SRC:-}" AWS_DEFAULT_REGION=auto
    runstep '소스 확보 (train' || FAILED=1
    [ "$FAILED" = 0 ] && { runstep '데이터셋 제작' || FAILED=1; }
  fi
  export VC_NAME="${I_NAME:-}" VC_SRC="${I_SRC:-}" VC_VID="${I_VID:-}"
  [ "$FAILED" = 0 ] && { runstep 'Replicate 실행' || FAILED=1; }
  [ "$FAILED" = 1 ] && { runstep '실패 기록' || true; }
  runstep 'Commit output' || true
  # 배포 게이트 스텝 = 스킵(need_deploy 깃발이 재배포) · 완료 푸시 = 정본 always() 동형
  runstep '완료 푸시' || true
  if [ -n "${I_UP_BRANCH:-}" ]; then export UP_BRANCH="$I_UP_BRANCH"; runstep '업로드 브랜치 정리' || true; fi
  runstep '임시 업로드 청소' || true
  ;;
esac
[ "$FAILED" = 1 ] && exit 1
exit 0
