#!/usr/bin/env bash
# 노뮤트 에디터 새 계정 이전기 (260815)
#
# 하는 일 = 지금 작업본을 이력 없이 새 저장소로 통째 밀어넣는다.
#   · 이력(커밋 3만 건·브랜치 수백)을 버린다 = 자동화 규모 흔적이 새 계정에 안 따라간다
#   · 현재 .git 은 지우지 않고 .git_old 로 이름만 바꾼다 = 언제든 되돌릴 수 있다
#   · 파일은 하나도 안 버린다(추적 파일 실측 115MB)
#
# 쓰는 법:
#   bash scripts/새계정_이전.sh https://github.com/<새계정>/<저장소>.git
#   bash scripts/새계정_이전.sh <주소> --시계끄기      # 크론 트리거를 주석 처리한 채로 올린다
#
# 되돌리기:
#   rm -rf .git && mv .git_old .git
set -euo pipefail
cd "$(dirname "$0")/.."

NEW="${1:-}"
OFF=0
[ "${2:-}" = "--시계끄기" ] && OFF=1
if [ -z "$NEW" ]; then
  echo "새 저장소 주소를 인자로 줘야 한다."
  echo "  예) bash scripts/새계정_이전.sh https://github.com/새계정/nomute-editor.git"
  exit 1
fi

echo "▶ 대상 = $NEW"
echo "▶ 현재 원격 = $(git remote get-url origin 2>/dev/null || echo '없음')"

# ── ① 지금 상태를 원래 저장소에 먼저 밀어둔다(유실 방지)
if git remote get-url origin >/dev/null 2>&1; then
  echo "▶ 안전을 위해 현재 브랜치를 원래 원격에 먼저 밀어둔다"
  git push origin HEAD 2>/dev/null || echo "  (원래 원격 푸시 실패 — 계속 진행. .git_old 에 이력은 남는다)"
fi

# ── ② 시계 끄기(선택) = 새 계정에서 70개가 즉시 크론으로 도는 것을 막는다
if [ "$OFF" = "1" ]; then
  echo "▶ 자동 시계를 주석 처리한다(나중에 되살리기 = git revert 한 줄)"
  python3 - <<'PY'
import glob, re, io
n = 0
for f in glob.glob('.github/workflows/*.yml'):
    s = io.open(f, encoding='utf-8').read()
    if not re.search(r'^\s*-?\s*cron:', s, re.M):
        continue
    out, hit = [], False
    for ln in s.split('\n'):
        if re.match(r'^\s*-?\s*cron:', ln) and not ln.lstrip().startswith('#'):
            i = len(ln) - len(ln.lstrip())
            out.append(ln[:i] + '# ' + ln[i:] + '   # 이전-시계정지 260815')
            hit = True
        else:
            out.append(ln)
    if hit:
        io.open(f, 'w', encoding='utf-8').write('\n'.join(out)); n += 1
print(f'  시계 정지 = 워크플로 {n}개')
PY
fi

# ── ③ 이력 버리고 새로 시작
echo "▶ 이력을 .git_old 로 밀어두고 새로 시작한다"
[ -d .git_old ] && { echo "  .git_old 가 이미 있다 — 먼저 치우고 다시 실행해라"; exit 1; }
mv .git .git_old
git init -q
git checkout -q -b main
git add -A
git -c user.name="nomute" -c user.email="nomutefb@pm.me" commit -q -m "노뮤트 에디터 이전(260815) — 이력 없이 현재 상태부터 시작"
git remote add origin "$NEW"

echo "▶ 새 저장소로 밀어넣는다"
for i in 1 2 3 4; do
  git push -u origin main && break
  s=$((2**i)); echo "  실패 — ${s}초 뒤 재시도"; sleep $s
done

echo
echo "✅ 코드 이전 끝. 남은 것:"
echo "   1) 열쇠 38개 · 설정값 31개 넣기 → docs/reports/260815_계정이전_체크리스트.md"
echo "   2) 클라우드플레어에서 배포 연결을 이 저장소로 갈아끼우기"
echo "   3) 새 배포 훅 주소를 CF_DEPLOY_HOOK 에 넣기"
echo "   4) 외부 15분 시계의 대상 주소 바꾸기"
[ "$OFF" = "1" ] && echo "   5) 시계 되살리기 = 이전-시계정지 표시된 줄의 주석 풀기"
echo
echo "되돌리려면: rm -rf .git && mv .git_old .git"
