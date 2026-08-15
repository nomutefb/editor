#!/usr/bin/env bash
# 노뮤트 edit 잡 실행기(260815 코워크) — edit-make.yml 스텝(정본)을 이름으로 추출해 그대로 실행(값 창작 0).
# 호출 = nomute_job_worker.sh(키 env 주입 상태). rc: 0=완료 · 9=구식 잡 재접수 · 7=환경 준비중(큐 보존) · 그 외=실패.
# 스킵 대상(맥 환경): Checkout/Node·Python 셋업/캐시(상시 준비) · 배포 게이트(뷰어가 R2 직폴링 = 불요·8분 낭비 방지)
#   · xtr 트래킹(v1 미지원 — 워크플로도 continue-on-error 축이라 편집본은 산다 · note 로그).
set -u
J="$1"; REPO="${NOMUTE_WORKER_REPO:-$HOME/nomute-worker}"; cd "$REPO" || exit 1
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8
W=".github/workflows/edit-make.yml"

# ── 잡 파싱: 신형 {inputs:{...}} = 실행 · 구형(미들웨어 {body}) = /api/edit 재접수(신형 큐로 재발급)
PREP=$(python3 - "$J" <<'PY'
import json,sys,shlex
j=json.load(open(sys.argv[1]))
ins=j.get('inputs')
if not (isinstance(ins,dict) and ins.get('id')):
    open('/tmp/edit_repost.json','w',encoding='utf-8').write(j.get('body') or '{}')
    print('MODE=repost'); sys.exit(0)
print('MODE=run')
# opts 정규화(콤팩트 재직렬화) — 게이트가 '"burn":true' 부분일치라 공백 유입 시 전 스텝 미발동(실측 260815 셀프테스트)
try: ins['opts']=json.dumps(json.loads(ins.get('opts') or '{}'),ensure_ascii=False,separators=(',',':'))
except Exception: pass
for k in ('id','url','file','up_branch','r2_src','opts'):
    print('E_'+k.upper()+'='+shlex.quote(str(ins.get(k) or '')))
PY
) || exit 1
eval "$PREP"
if [ "${MODE:-}" = repost ]; then
  curl -s --max-time 40 -X POST https://apps.nomute.kr/api/edit -H 'Content-Type: application/json' --data @/tmp/edit_repost.json >/dev/null 2>&1
  exit 9
fi

# ── env 준비(워크플로 job/step env 동형) ────────────────────────────────
export IN_ID="$E_ID" OPTS="$E_OPTS"
export GITHUB_ENV=/tmp/edit_ghenv.txt; : > "$GITHUB_ENV"
srcenv(){ [ -s "$GITHUB_ENV" ] && { set -a; . "$GITHUB_ENV"; set +a; }; return 0; }
has(){ case "$OPTS" in *"$1"*) return 0;; *) return 1;; esac; }
STT_ON=0; for f in '"burn":true' '"cut":true' '"clip":true' '"cutfill":true' '"take":true' '"cutscan":true'; do has "$f" && STT_ON=1; done
# 자막 번인 = libass 필수 — 풀빌드 ffmpeg 준비 전이면 큐 보존(rc7 · 유실 0)
if has '"burn":true' && ! ffmpeg -hide_banner -filters 2>/dev/null | grep -q " ass  *"; then
  echo "[edit] ffmpeg libass 미준비 — 잡 큐 보존(다음 틱 재시도)"; exit 7
fi
# claude 계정 토큰 사슬(워크플로 account=MUTENO 기본과 동형 매핑) — 키 없으면 키체인 로그인 사용
if [ -n "${CLAUDE_CODE_OAUTH_TOKEN_MUTENO:-}" ]; then
  export CLAUDE_CODE_OAUTH_TOKEN="$CLAUDE_CODE_OAUTH_TOKEN_MUTENO"
  export CLAUDE_CODE_OAUTH_TOKEN_ALT="${CLAUDE_CODE_OAUTH_TOKEN_NOMUTEFB:-}"
  export CLAUDE_CODE_OAUTH_TOKEN_ALT2="${CLAUDE_CODE_OAUTH_TOKEN_EMS1130G:-}"
  export CLAUDE_CODE_OAUTH_TOKEN_ALT3="${CLAUDE_CODE_OAUTH_TOKEN_EMS1130M:-}"
fi
export ACTIVE_ACCOUNT="${ACTIVE_ACCOUNT:-MUTENO}"
export AWS_ACCESS_KEY_ID="${R2_ACCESS_KEY_ID:-}" AWS_SECRET_ACCESS_KEY="${R2_SECRET_ACCESS_KEY:-}"
export YT_COOKIES="${YT_T2_COOKIES:-}" YT_COOKIES_NAME=YT_T2_COOKIES
export YT_COOKIES_2="${YT_T_COOKIES:-}" YT_COOKIES_2_NAME=YT_T_COOKIES

# ── 정본 스텝 추출·실행기 — 이름 접두 일치로 run 블록을 꺼내 bash 실행 → GITHUB_ENV 반영
runstep(){
  python3 - "$1" > /tmp/edit_step.sh <<'PY' || { echo "[edit] 스텝 추출 실패: $1"; return 3; }
import yaml,sys
d=yaml.safe_load(open('.github/workflows/edit-make.yml',encoding='utf-8'))
for s in list(d['jobs'].values())[0]['steps']:
    n=s.get('name') or ''
    if n.startswith(sys.argv[1]) and s.get('run'):
        sys.stdout.write(s['run']); sys.exit(0)
sys.exit(3)
PY
  bash /tmp/edit_step.sh; local rc=$?
  srcenv
  return $rc
}

# ── 본 실행(워크플로 스텝 게이트 동형 번역) ─────────────────────────────
FAILED=0
if [ -n "$E_URL" ]; then
  export URL="$E_URL"
  if has '"vid_res":"src"'; then export YTF='bv*[height<=2160]+ba[ext=m4a]/bv*[height<=2160]+ba/b'
  else export YTF='bv*[height<=1920]+ba[ext=m4a]/bv*[height<=1920]+ba/b'; fi
  PATH="$HOME/nomute-pyw:$PATH" runstep '소스 확보 (URL)' || FAILED=1   # yt-dlp 최신판 심(260815 · 구판 403 실측)
elif [ -n "$E_R2_SRC" ]; then
  export R2_SRC="$E_R2_SRC" R2_ACCOUNT_ID="${R2_ACCOUNT_ID:-}" R2_BUCKET="${R2_BUCKET:-}"
  runstep '소스 확보 (R2 직업로드' || FAILED=1
elif [ -n "$E_FILE" ]; then
  export FILE="$E_FILE" UP_BRANCH="$E_UP_BRANCH"
  runstep '소스 확보 (업로드 파일)' || FAILED=1
else
  echo "영상 입력이 없어 — URL이나 파일을 넣어줘." > /tmp/edit_err.txt; FAILED=1
fi
[ "$FAILED" = 0 ] && { runstep '길이 선게이트' || FAILED=1; }
if [ "$FAILED" = 0 ] && [ "$STT_ON" = 1 ]; then runstep 'STT (' || FAILED=1; fi
if [ "$FAILED" = 0 ] && has '"burn":true' && ! has '"clip":true'; then runstep '자막 의역' || FAILED=1; fi
if [ "$FAILED" = 0 ] && has '"clip":true'; then runstep '클리퍼 구간픽' || FAILED=1; fi
if [ "$FAILED" = 0 ] && has '"take":true' && ! has '"clip":true'; then runstep '테이크 감지' || true; fi
if [ "$FAILED" = 0 ] && has '"cutscan":true' && ! has '"clip":true'; then runstep '컷 미리보기 스캔' || FAILED=1; fi
if [ "$FAILED" = 0 ] && { has '"clip":true' || has '"cutscan":true'; } && [ -z "$E_URL" ]; then runstep '클리퍼·컷스캔 원본 보관' || true; fi
if [ "$FAILED" = 0 ] && { has '"clip":true' || has '"cutscan":true'; }; then runstep '스캔 산출 R2 즉시 게시' || true; fi
if [ "$FAILED" = 0 ] && has '"bgm":true'; then runstep 'Demucs 설치' || true; fi
if [ "$FAILED" = 0 ] && ! has '"clip":true' && ! has '"cutscan":true'; then
  has '"xtr"' && echo "[edit] 자동 가림(xtr) — 맥 v1 미지원 스킵(편집·자막은 정상 진행)"
  runstep '컴포즈' || FAILED=1
fi
if [ "$FAILED" = 1 ]; then runstep '실패 기록' || true; fi
export BRANCH=main
runstep 'Commit output' || true
if [ -n "$E_UP_BRANCH" ]; then export UP_BRANCH="$E_UP_BRANCH"; runstep '업로드 브랜치 정리' || true; fi
runstep '임시 업로드 청소' || true
runstep '편집 완료 푸시' || true
[ "$FAILED" = 1 ] && exit 1
exit 0
