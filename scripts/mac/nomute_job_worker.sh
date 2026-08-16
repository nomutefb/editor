#!/usr/bin/env bash
# 노뮤트 R2 잡 워커 v1(260815 코워크) — 뷰어 제작 요청(R2 queue/jobs/)을 맥에서 실제 실행.
# v1 구현 kind = genimg(사진 제작 · Image Studio) — imggen.yml 스텝 사본(값 창작 0):
#   GENIMG_STEM/OPTS/FREE env → .github/scripts/gen_image.py → git add cards metrics viewer/gen_out → 착지.
#   옵션 정밀검증은 gen_image.py가 이중으로 한다(함수 화이트리스트와 동일 집합) — 워커는 원문 전달만.
# 미구현 kind = 큐에 남긴다(다음 확장에서 처리 · 유실 0). 실패 잡 = queue/failed/ 로 이동.
set -u
export PATH="$HOME/nomute-pybin:/usr/bin:/opt/homebrew/bin:/opt/homebrew/opt/coreutils/libexec/gnubin:$PATH"   # nomute-pybin = bare pip 심(시스템 py3.9 · 브루 PEP668 회피 — 260815)
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8
export NOMUTE_MAC_LANE=1   # .githooks 봇 면제(260815) — 잡 커밋·푸시가 사람 세션 원장 위반(check_refs ❌)에 물려 죽지 않게(CI 러너 제외와 동축)
ENVF="$HOME/nomute-action/환경변수.txt"; REPO="${NOMUTE_WORKER_REPO:-$HOME/nomute-worker}"
# 워커 전용 저장소 사본(260815) — 5분 레인(~/nomute-editor)과 작업나무 분리 = git 인덱스/오토스태시 충돌 0.
# 잠금 — 전용 1분 틱 + run.sh 후크가 같은 워커를 불러도 동시 실행 방지(좀비 잠금 40분 후 회수).
LK="$HOME/.nomute_worker.lock"
if ! mkdir "$LK" 2>/dev/null; then
  A=$(/usr/bin/stat -f %m "$LK" 2>/dev/null || echo 0); N=$(date +%s)
  { [ $((N-A)) -gt 2400 ] && rmdir "$LK" 2>/dev/null && mkdir "$LK" 2>/dev/null; } || exit 0
fi
trap 'rmdir "$LK" 2>/dev/null' EXIT
get(){ grep "^$1=" "$ENVF" 2>/dev/null | head -1 | cut -d= -f2-; }
ACC="$(get R2_ACCOUNT_ID)"; AK="$(get R2_ACCESS_KEY_ID)"; SK="$(get R2_SECRET_ACCESS_KEY)"; BK="$(get R2_BUCKET)"
[ -n "$ACC" ] && [ -n "$AK" ] || exit 0
B="https://$ACC.r2.cloudflarestorage.com/$BK"
S3(){ curl -sS --max-time 60 --aws-sigv4 aws:amz:auto:s3 --user "$AK:$SK" "$@"; }
KEYS=$(S3 "$B?list-type=2&prefix=queue/jobs/" 2>/dev/null | grep -o '<Key>[^<]*</Key>' | sed 's/<Key>//;s/<\/Key>//' | head -6)
[ -n "$KEYS" ] || exit 0
# 키 주입(환경변수.txt 평문 KEY=VAL 전량 — genimg 축 = GEMINI·R2·OPENAI 폴백)
set -a
while IFS= read -r ln; do
  case "$ln" in ''|'#'*) continue;; esac
  case "$ln" in *=*) k="${ln%%=*}"; case "$k" in *[!A-Za-z0-9_]*) continue;; esac; export "$ln" 2>/dev/null || true;; esac
done < "$ENVF"
set +a
unset ANTHROPIC_API_KEY ANTHROPIC_AUTH_TOKEN 2>/dev/null || true
export NOMUTE_FONT_PATH="$HOME/nomute-assets/fonts/NotoSansCJK-Bold.ttc"   # 합성기 폰트(맥 로컬 · card_news env-우선 짝)
# 합성 의존성 자가복구(cv2 = card_news import 블록 전체를 좌우 · 없으면 폰트/PIL까지 None으로 떨어져 합성 무음실패)
python3 -c "import cv2" 2>/dev/null || pip3 install --quiet --user opencv-python-headless >/dev/null 2>&1 || true
python3 -c "import mediapipe" 2>/dev/null || pip3 install --quiet --user mediapipe >/dev/null 2>&1 || true   # 썸네일 AI 합성 후처리(nomute_compose) 의존 — 미설치 실측 260815 13:24 실패 봉합
[ -s "$NOMUTE_FONT_PATH" ] || curl -sL -o "$NOMUTE_FONT_PATH" https://raw.githubusercontent.com/notofonts/noto-cjk/main/Sans/OTC/NotoSansCJK-Bold.ttc 2>/dev/null || true
cd "$REPO" || exit 0
git pull --rebase --autostash -X ours -q origin main 2>/dev/null || true   # 잡 있을 때만 도달 — 최신 정본 코드로 렌더
done_n=0
for K in $KEYS; do
  [ "$done_n" -ge 4 ] && break   # 회차당 4잡 상한(thumb 합성은 초 단위라 여유)
  J="/tmp/nomute_job.json"; S3 "$B/$K" -o "$J" 2>/dev/null || continue
  KIND=$(python3 -c "import json;print(json.load(open('$J')).get('kind',''))" 2>/dev/null || echo '')
  PRE_HEAD=$(git rev-parse HEAD 2>/dev/null || echo '')   # [live] 짝 — 잡 전후 diff로 산출만 골라 R2 즉시 게시
  case "$KIND" in
    genimg)
      eval "$(python3 - "$J" <<'PY'
import json,sys,shlex,re
j=json.load(open(sys.argv[1])); b=json.loads(j.get('body') or '{}')
free = (b.get('free') is True)
stem = 'free' if free else str(b.get('file') or '').strip()
stem = re.sub(r'\.md$','',stem)[:120]
ok = bool(re.fullmatch(r'[A-Za-z0-9._-]+', stem)) and '..' not in stem
opts = b.get('opts')
if not isinstance(opts, dict): opts = {}
opts_q = shlex.quote(json.dumps(opts, ensure_ascii=False))
out = []
out.append('GJ_OK=' + ('1' if ok else '0'))
out.append('GJ_STEM=' + shlex.quote(stem))
out.append('GJ_FREE=' + ('1' if free else '0'))
out.append('GJ_OPTS=' + opts_q)
print('\n'.join(out))
PY
)"
      if [ "${GJ_OK:-0}" != "1" ]; then
        S3 -X PUT "$B/queue/failed/$(basename "$K")" --data-binary "@$J" >/dev/null 2>&1; S3 -X DELETE "$B/$K" >/dev/null 2>&1
        echo "[job] $(date '+%H:%M:%S') genimg 부적격 stem — failed/ 이동"; continue
      fi
      echo "[job] $(date '+%H:%M:%S') genimg 시작 stem=$GJ_STEM free=$GJ_FREE"
      if GENIMG_STEM="$GJ_STEM" GENIMG_OPTS="$GJ_OPTS" GENIMG_FREE="$GJ_FREE" timeout 900 python3 .github/scripts/gen_image.py; then
        for f in cards metrics viewer/gen_out; do [ -e "$f" ] && git add "$f" 2>/dev/null; done
        if ! git diff --cached --quiet 2>/dev/null; then
          # ⚠ 260816 봉합 — 구판은 `pull --rebase -X ours` 였다. 리베이스에서 ours = **upstream** 이라
          #   충돌 시 우리 산출이 버려진 채 push 가 성공한다(무음 `|| true` 라 실패도 안 보인다).
          #   → git_land 위임 = 리베이스를 안 쓰고(꼬임 0) **남의 착지분을 BASE 대조로 복원**한다(같은 날 봉합).
          #   PAGES_COALESCE=0 = 제작 산출은 코얼레싱 금지 축이라 접두를 끈다(pc_lane `_push` 문법 사본).
          git reset -q HEAD -- . 2>/dev/null || true
          PAGES_COALESCE=0 bash .github/scripts/git_land.sh "imggen: $GJ_STEM (맥 잡워커)" cards metrics viewer/gen_out 2>/dev/null || true
        fi
        S3 -X DELETE "$B/$K" >/dev/null 2>&1
        touch "$HOME/.nomute_need_deploy"
        done_n=$((done_n+1)); echo "[job] $(date '+%H:%M:%S') genimg 완료 stem=$GJ_STEM"
      else
        S3 -X PUT "$B/queue/failed/$(basename "$K")" --data-binary "@$J" >/dev/null 2>&1; S3 -X DELETE "$B/$K" >/dev/null 2>&1
        echo "[job] $(date '+%H:%M:%S') genimg 실패 stem=$GJ_STEM — failed/ 이동(로그 위)"
      fi;;
    compose)
      OUT_INFO=$(python3 - "$J" <<'PY'
import json,sys,base64,re,os,datetime,random
j=json.load(open(sys.argv[1])); b=json.loads(j.get('body') or '{}')
lines=[str(s or '')[:200] for s in (b.get('lines') or []) if str(s or '').strip()][:12]
b64=str(b.get('imageB64') or '')
m=re.match(r'^data:[^;,]*;base64,(.+)$', b64)
if m: b64=m.group(1)
if not lines or not b64: print('ERR 입력 부족'); sys.exit(3)
try: raw=base64.b64decode(b64)
except Exception: print('ERR b64 디코드'); sys.exit(3)
ext='.jpg' if raw[:2]==b'\xff\xd8' else '.png' if raw[:4]==b'\x89PNG' else ('.webp' if raw[:4]==b'RIFF' and raw[8:12]==b'WEBP' else '')
if not ext: print('ERR 포맷(JPG/PNG/WEBP)'); sys.exit(3)
kst=datetime.datetime.utcnow()+datetime.timedelta(hours=9)
iid=kst.strftime('%y%m%d%H%M%S')+'-'+('%04x'%random.randrange(16**4))
os.makedirs(f'uploads/{iid}',exist_ok=True); img=f'uploads/{iid}/src{ext}'
open(img,'wb').write(raw)
os.makedirs(f'viewer/comp_out/{iid}',exist_ok=True); out=f'viewer/comp_out/{iid}/card.jpg'
sys.path.insert(0,'apps/comp')
from card_news import generate
if not generate(img, lines, out): print('ERR generate 실패'); sys.exit(2)
size=str(b.get('size') or 'FHD')
try:
    sys.path.insert(0,'.github/scripts')
    from img_sizes import SIZE_SHORT as S
    from PIL import Image
    t=S.get(size,1080); im=Image.open(out); c=min(im.size)
    if t!=1080 and c!=t:
        r=t/float(c); im.resize((max(1,round(im.width*r)),max(1,round(im.height*r))),Image.LANCZOS).convert('RGB').save(out,'JPEG',quality=95,subsampling=0,optimize=True)
except Exception as e: print('경고 res-snap 실패:', e)
src=b.get('src')
if src: open(f'viewer/comp_out/{iid}/_src.json','w',encoding='utf-8').write(json.dumps(src,ensure_ascii=False))
print('ID='+iid)
PY
)
      rc=$?
      CJ_ID=$(printf '%s\n' "$OUT_INFO" | grep '^ID=' | cut -d= -f2)
      if [ "$rc" -eq 0 ] && [ -n "$CJ_ID" ]; then
        # ⚠ 260816 봉합 — 구판 `pull --rebase -X ours` 는 리베이스에서 ours = upstream 이라 충돌 시
        #   우리 산출이 버려진 채 push 가 성공한다(무음 `|| true`). git_land 는 리베이스를 안 쓰고
        #   남의 착지분을 BASE 대조로 복원한다 · PAGES_COALESCE=0 = 제작 산출 = 코얼레싱 금지 축.
        PAGES_COALESCE=0 bash .github/scripts/git_land.sh "comp: $CJ_ID 합성 출력(맥 잡워커)" "viewer/comp_out/$CJ_ID" "uploads/$CJ_ID" 2>/dev/null || true
        S3 -X DELETE "$B/$K" >/dev/null 2>&1
        touch "$HOME/.nomute_need_deploy"
        done_n=$((done_n+1)); echo "[job] $(date '+%H:%M:%S') compose 완료 id=$CJ_ID"
      else
        printf '%s\n' "$OUT_INFO" | head -2
        S3 -X PUT "$B/queue/failed/$(basename "$K")" --data-binary "@$J" >/dev/null 2>&1; S3 -X DELETE "$B/$K" >/dev/null 2>&1
        echo "[job] $(date '+%H:%M:%S') compose 실패 — failed/ 이동"
      fi;;
    thumb)
      bash "$HOME/nomute_thumb_driver.sh" "$J"; drc=$?
      if [ "$drc" -eq 0 ]; then
        S3 -X DELETE "$B/$K" >/dev/null 2>&1
        touch "$HOME/.nomute_need_deploy"
        done_n=$((done_n+1)); echo "[job] $(date '+%H:%M:%S') thumb 완료 ($K)"
      elif [ "$drc" -eq 9 ]; then
        S3 -X DELETE "$B/$K" >/dev/null 2>&1
        echo "[job] $(date '+%H:%M:%S') thumb 구식 잡 → 함수 재접수(새 형식 큐로)"
      else
        S3 -X PUT "$B/queue/failed/$(basename "$K")" --data-binary "@$J" >/dev/null 2>&1; S3 -X DELETE "$B/$K" >/dev/null 2>&1
        echo "[job] $(date '+%H:%M:%S') thumb 실패 — failed/ 이동"
      fi;;
    edit)
      timeout 6300 bash "$HOME/nomute_edit_driver.sh" "$J"; erc=$?
      if [ "$erc" -eq 0 ]; then
        S3 -X DELETE "$B/$K" >/dev/null 2>&1
        done_n=$((done_n+1)); echo "[job] $(date '+%H:%M:%S') edit 완료 ($K)"
      elif [ "$erc" -eq 9 ]; then
        S3 -X DELETE "$B/$K" >/dev/null 2>&1
        echo "[job] $(date '+%H:%M:%S') edit 구식 잡 → 함수 재접수(신형 큐로)"
      elif [ "$erc" -eq 7 ]; then
        echo "[job] $(date '+%H:%M:%S') edit 환경 준비중(libass 빌드) — 큐 보존"
      else
        S3 -X PUT "$B/queue/failed/$(basename "$K")" --data-binary "@$J" >/dev/null 2>&1; S3 -X DELETE "$B/$K" >/dev/null 2>&1
        echo "[job] $(date '+%H:%M:%S') edit 실패 rc=$erc — failed/ 이동(뷰어엔 error.log 표시)"
      fi;;
    vidl|conv|moreimg|imgedit|thumbredo|resize|upscale|framethumb|make-cards|revise|revise-cards|tr|nb|k|sb|ly|song|track|voice)
      case "$KIND" in sb|track|voice) WTMO=6300;; *) WTMO=3600;; esac   # 촬영 폴링·모델 렌더·학습 = 장주기(edit 6300 동형)
      timeout "$WTMO" bash "$HOME/nomute_wf_driver.sh" "$KIND" "$J"; wrc=$?
      if [ "$wrc" -eq 0 ]; then
        S3 -X DELETE "$B/$K" >/dev/null 2>&1
        case "$KIND" in conv|moreimg|thumbredo|resize|upscale|framethumb|make-cards|revise|revise-cards|tr|nb|k|sb|ly|song|voice) touch "$HOME/.nomute_need_deploy";; esac   # Pages 정적 폴링 축 = 배포로 표시(vidl=api/vidlout · imgedit=R2 · track=api/track 라이브라 불요)
        done_n=$((done_n+1)); echo "[job] $(date '+%H:%M:%S') $KIND 완료 ($K)"
      elif [ "$wrc" -eq 9 ]; then
        S3 -X DELETE "$B/$K" >/dev/null 2>&1
        echo "[job] $(date '+%H:%M:%S') $KIND 구식 잡 → 함수 재접수(신형 큐로)"
      elif [ "$wrc" -eq 7 ]; then
        echo "[job] $(date '+%H:%M:%S') $KIND 환경 준비중 — 큐 보존(다음 틱 재시도)"
      else
        S3 -X PUT "$B/queue/failed/$(basename "$K")" --data-binary "@$J" >/dev/null 2>&1; S3 -X DELETE "$B/$K" >/dev/null 2>&1
        echo "[job] $(date '+%H:%M:%S') $KIND 실패 rc=$wrc — failed/ 이동(뷰어엔 error.log 표시)"
      fi;;
    *) : ;;   # 미구현 kind — 큐 보존(다음 확장)
  esac
  # [live] 산출 R2 즉시 게시(260815 3차) — 배포(≈40초+틱) 대기 없이 화면 반영(functions/*/[[path]].js R2 우선 서빙 짝).
  #   잡이 민 커밋 범위의 viewer/* 파일을 같은 키(viewer/ 접두 제거)로 PUT · 20MB 상한 · 실패 = 조용히 통과(정적 폴백 생존).
  POST_HEAD=$(git rev-parse HEAD 2>/dev/null || echo '')
  if [ -n "$PRE_HEAD" ] && [ -n "$POST_HEAD" ] && [ "$POST_HEAD" != "$PRE_HEAD" ]; then
    ln=0
    while IFS= read -r f; do
      [ -f "$f" ] || continue
      sz=$(/usr/bin/stat -f %z "$f" 2>/dev/null || echo 0); [ "$sz" -gt 20000000 ] && continue
      NMT_CT=$(case "${f##*.}" in (jpg|jpeg) echo image/jpeg;; (png) echo image/png;; (webp) echo image/webp;; (gif) echo image/gif;; (svg) echo "image/svg+xml";; (json) echo application/json;; (mp4|m4v) echo video/mp4;; (mov) echo video/quicktime;; (webm) echo video/webm;; (mp3) echo audio/mpeg;; (m4a) echo audio/mp4;; (wav) echo audio/wav;; (vtt|srt|txt|md) echo "text/plain; charset=utf-8";; (html) echo "text/html; charset=utf-8";; (css) echo text/css;; (js) echo text/javascript;; (*) echo application/octet-stream;; esac)   # CT 매핑(260815 코워크: 무CT PUT = x-www-form-urlencoded로 저장돼 api/dl 415 · 다운로드 0.02KB 사고 봉합)
      S3 -X PUT "$B/${f#viewer/}" -H "Content-Type: $NMT_CT" --data-binary "@$f" >/dev/null 2>&1 && ln=$((ln+1))
    done <<EOF_LIVE
$(git diff --name-only "$PRE_HEAD" "$POST_HEAD" 2>/dev/null | grep -E "^viewer/" | head -80)
EOF_LIVE
    [ "$ln" -gt 0 ] && echo "[live] $(date '+%H:%M:%S') $KIND 산출 R2 게시 ${ln}건(배포 대기 0)"
  fi
done
exit 0
