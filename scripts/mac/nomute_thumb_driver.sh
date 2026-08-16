#!/usr/bin/env bash
# 노뮤트 thumb 잡 실행기(260815) — thumb-make.yml 「Render」 스텝(정본)을 그대로 추출·실행(값 창작 0).
# 호출 = nomute_job_worker.sh(키 env 주입 상태). rc: 0=완료 · 9=구식 잡 재접수 · 그 외=실패.
set -u
J="$1"; REPO="${NOMUTE_WORKER_REPO:-$HOME/nomute-worker}"; cd "$REPO" || exit 1
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8
PREP=$(python3 - "$J" <<'PY'
import json,sys,base64,os,re,shlex
j=json.load(open(sys.argv[1]))
if not j.get('id'):
    print('MODE=repost')
    open('/tmp/thumb_repost.json','w',encoding='utf-8').write(j.get('body') or '{}')
    sys.exit(0)
iid=j['id']; app=str(j.get('app') or ''); params=j.get('params') or {}
img=j.get('imgPath') or ''; src=j.get('srcJson') or ''
b=j.get('body') or {}
if isinstance(b,str):
    try: b=json.loads(b)
    except Exception: b={}
if img:
    b64=str(b.get('imageB64') or '')
    m=re.match(r'^data:[^;,]*;base64,(.+)$', b64)
    if m: b64=m.group(1)
    if not b64: print('MODE=err'); sys.exit(0)
    os.makedirs(os.path.dirname(img), exist_ok=True)
    open(img,'wb').write(base64.b64decode(b64))
print('MODE=run')
print('T_APP='+shlex.quote(app)); print('T_ID='+shlex.quote(iid))
print('T_IMAGE='+shlex.quote(img)); print('T_SRC='+shlex.quote(src))
open('/tmp/thumb_params.json','w',encoding='utf-8').write(json.dumps(params,ensure_ascii=False))
PY
) || exit 1
eval "$PREP"
if [ "${MODE:-}" = "repost" ]; then
  # 260816 계정 이관 잔재 봉합: 옛 화면 apps.nomute.kr 은 옛 계정 배포 = 재접수 잡이 옛 저장소로 새서 이 레인에 영영 안 돌아온다(레버 = LIVE_BASE · live-smoke.yml 문법 사본)
  curl -s --max-time 40 -X POST "${LIVE_BASE:-https://edit.nomute.kr}/api/thumb" \
    -H 'Content-Type: application/json' --data @/tmp/thumb_repost.json >/dev/null 2>&1
  exit 9
fi
[ "${MODE:-}" = "run" ] || { echo "thumb 준비 실패(이미지 결측 등)"; exit 1; }
python3 - <<'PY' || exit 1
import yaml
d=yaml.safe_load(open('.github/workflows/thumb-make.yml',encoding='utf-8'))
steps=list(d['jobs'].values())[0]['steps']
st=next(s for s in steps if s.get('name')=='Render')
open('/tmp/thumb_render.py','w',encoding='utf-8').write(st['run'])
print('Render 스텝 추출 OK', len(st['run']), 'chars')
PY
APP="$T_APP" IN_ID="$T_ID" IMAGE="$T_IMAGE" PARAMS="$(cat /tmp/thumb_params.json)" SRC_JSON="$T_SRC" \
  timeout 700 python3 /tmp/thumb_render.py || exit 1
if [ -n "$T_SRC" ]; then mkdir -p "viewer/thumb_out/$T_ID"; printf '%s' "$T_SRC" > "viewer/thumb_out/$T_ID/_src.json"; fi
# ⚠ 260816 봉합 — 구판 `pull --rebase -X ours` 는 리베이스에서 ours = upstream 이라 충돌 시 우리 산출이
#   버려진 채 push 가 성공했다(무음 `|| true` 라 실패도 안 보인다). git_land 는 리베이스를 안 쓰고(꼬임 0)
#   남의 착지분을 BASE 대조로 복원한다(같은 날 봉합) · 경로별 개별 처리도 그 헬퍼가 한다(Q980 계승 유지).
#   PAGES_COALESCE=0 = 제작 산출은 코얼레싱 금지 축이라 접두를 끈다(pc_lane `_push` 문법 사본).
PAGES_COALESCE=0 bash .github/scripts/git_land.sh "thumb: $T_ID 산출(맥 잡워커)" "uploads/$T_ID" "viewer/thumb_out/$T_ID" 2>/dev/null || true
exit 0
