#!/usr/bin/env bash
# summary_ab.sh — 뉴스 요약 파이프 A/B 실측 드라이버(러너 전용 · summary-ab.yml 이 부른다)
#
# ▷ 무엇: 같은 기사를 조건별로 여러 번 요약해 산출물·로그·토큰 계측을 한 폴더에 모은다.
#   조건(arm) = A(기준 SHA · 라이브 그대로) · S(기준 SHA + ANALYZE_SAFE_MODE=1 = 지침문서 스킵만) · B(대상 SHA · 그 트리의 기본값 그대로).
#   실행 트리 = 한 sparse 트리에서 SHA 만 갈아 끼운다(평의회1 260905: worktree 2개 = sparse 비대칭·CLAUDE.md 이중주입·trust 키 불일치).
#   각 arm 은 그 트리의 `.github/scripts/analyze.sh` 를 **그대로** 실행한다(모델·노력도·도구·타임아웃 = 그 트리 값 = 라이브와 동일 조건).
# ▷ 안전: ANALYZE_LAND_EACH=0(건별 푸시 0) · 이 스크립트는 git push 를 하지 않는다(커밋·푸시는 워크플로 스텝 · 대상 = 실행 브랜치 · main 금지).
#   산출은 $AB_STAGE(트리 밖)에 모은다 = SHA 스왑·clean 에서 살아남는다. metrics shard 는 복사만(레포 metrics/ 에 add 금지 = 롤업 오염 차단).
# ▷ 입력(env): AB_ID · BASE_SHA · HEAD_SHA · ARTICLES(줄마다 `stem|pattern` · pattern = A/B/S 문자열 · 예 ABABS) · AB_STAGE(선택)
#   + analyze.sh 가 읽는 라이브 env(CLAUDE_CODE_OAUTH_TOKEN* · SUMMARY_LEN_GUARD · PREFLIGHT_TIMEOUT …)는 워크플로가 그대로 넘긴다.
# ▷ pending 파일 = 픽 레인 규격 그대로(pick.yml `# title:`·`# alt:`·`# ekey:`·`# body:`) + `# force: 1`(같은 지침 버전 중복 관문 통과 · analyze.sh 209행)
#   본문은 기사당 1회만 러너에서 선취득해 전 arm 에 같은 바이트로 동봉(fetch 분산 소거 · 900B 미만이면 미동봉 = URL 단독 arm = 대체매체 분기 검증).
set -uo pipefail
ROOT="$(git rev-parse --show-toplevel)"; cd "$ROOT"
AB_ID="${AB_ID:?AB_ID 필요}"; BASE_SHA="${BASE_SHA:?BASE_SHA 필요}"; HEAD_SHA="${HEAD_SHA:?HEAD_SHA 필요}"
STAGE="${AB_STAGE:-${RUNNER_TEMP:-/tmp}/ab_stage}"; mkdir -p "$STAGE"
[ "${GITHUB_REF_NAME:-}" != "main" ] || { echo "::error::main 에서 실행 금지(결과 커밋 대상 = 실행 브랜치)"; exit 1; }
[ -n "${ARTICLES:-}" ] || { echo "::error::ARTICLES 비어 있음"; exit 1; }

git fetch -q --depth=1 origin "$BASE_SHA" "$HEAD_SHA" 2>&1 | tail -1 || true
git cat-file -e "${BASE_SHA}^{commit}" 2>/dev/null || { echo "::error::BASE_SHA 조회 실패: $BASE_SHA"; exit 1; }
git cat-file -e "${HEAD_SHA}^{commit}" 2>/dev/null || { echo "::error::HEAD_SHA 조회 실패: $HEAD_SHA"; exit 1; }

# 트리 초기화 + SHA 스왑(산출·pending·messages·metrics 잔여물 전부 걷어낸다 — 다음 arm 이 앞 arm 의 파일을 보면 안 된다)
swap_tree() {
  local sha="$1"
  git checkout -q -- . 2>/dev/null || true
  git clean -fdq -- queue pending messages metrics 2>/dev/null || true
  git checkout -q "$sha" 2>&1 | tail -1 || { echo "::error::checkout 실패: $sha"; return 1; }
  echo "  트리 = $(git rev-parse --short HEAD)"
}

fm_val() { grep -m1 "^$2:" "$1" | sed -E "s/^$2:[[:space:]]*\"?//; s/\"?[[:space:]]*$//" | tr -d '\r'; }

printf '{"ab_id":"%s","base_sha":"%s","head_sha":"%s","runner":"%s","started":"%s"}\n' \
  "$AB_ID" "$BASE_SHA" "$HEAD_SHA" "${RUNNER_OS:-?}" "$(TZ=Asia/Seoul date +%FT%T%:z)" > "$STAGE/meta.json"
printf '%s\n' "$ARTICLES" > "$STAGE/articles.txt"

aidx=0
while IFS='|' read -r stem pattern; do
  stem="${stem//[[:space:]]/}"; pattern="${pattern//[[:space:]]/}"
  [ -n "$stem" ] && [ -n "$pattern" ] || continue
  aidx=$((aidx+1)); art="art${aidx}"; mkdir -p "$STAGE/$art"
  swap_tree "$HEAD_SHA" >/dev/null || exit 1
  q="queue/${stem}.md"
  [ -f "$q" ] || { echo "::error::큐 파일 없음: $q"; continue; }
  url="$(fm_val "$q" url)"; title="$(fm_val "$q" title)"; alt="$(fm_val "$q" alt_urls)"; ekey="$(fm_val "$q" event_key)"
  echo "::group::[$art] $stem · $url"
  body="$(timeout 90 bash .github/scripts/fetch_article.sh "$url" 2>/dev/null | head -c 20000 || true)"
  blen="$(printf %s "$body" | wc -c | tr -d ' ')"
  if [ "${blen:-0}" -ge 900 ]; then printf '%s\n' "$body" > "$STAGE/$art/src_body.txt"; echo "  본문 선취득 ${blen}B → 전 arm 동봉"; else body=""; echo "  본문 선취득 ${blen:-0}B(<900) → 미동봉 = URL 단독(대체매체 분기)"; fi
  printf '{"stem":"%s","url":"%s","title":%s,"alt_urls":"%s","event_key":"%s","body_bytes":%s,"pattern":"%s"}\n' \
    "$stem" "$url" "$(printf '%s' "$title" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')" "$alt" "$ekey" "${blen:-0}" "$pattern" > "$STAGE/$art/article.json"
  k=0
  while [ $k -lt ${#pattern} ]; do
    arm="${pattern:$k:1}"; k=$((k+1)); tag="${arm}${k}"
    case "$arm" in A|S) sha="$BASE_SHA";; B) sha="$HEAD_SHA";; *) echo "::warning::미지 arm '$arm' 스킵"; continue;; esac
    echo "── [$art/$tag] arm=$arm sha=${sha:0:8}"
    swap_tree "$sha" || exit 1
    base="$(TZ=Asia/Seoul date +%y%m%d-%H%M%S)-ab${aidx}${tag}"
    mkdir -p pending
    {
      printf '%s\n' "$url"
      [ -n "$title" ] && printf '# title: %s\n' "$title"
      [ -n "$alt" ] && printf '# alt: %s\n' "$alt"
      [ -n "$ekey" ] && printf '# ekey: %s\n' "$ekey"
      printf '# force: 1\n'
      if [ -n "$body" ]; then printf '# body:\n%s\n' "$body"; fi
    } > "pending/${base}.txt"
    extra=()
    [ "$arm" = "S" ] && extra=(ANALYZE_SAFE_MODE=1)
    t0=$(date +%s)
    env ANALYZE_LAND_EACH=0 IMG_SPLIT="${IMG_SPLIT:-1}" "${extra[@]}" bash .github/scripts/analyze.sh > "$STAGE/$art/${tag}.log" 2>&1
    rc=$?; t1=$(date +%s)
    # 산출 회수 = 이 arm 이 만들거나 덮어쓴 queue 파일(force 재생성 = 기존 스템 덮어쓰기)
    out_md="$(git status --porcelain -- queue | awk '{print $2}' | head -1)"
    if [ -n "$out_md" ] && [ -f "$out_md" ]; then cp "$out_md" "$STAGE/$art/${tag}.md"; else echo "  ⚠ 산출 없음(rc=$rc)"; fi
    [ -f "pending/failed/${base}.log" ] && cp "pending/failed/${base}.log" "$STAGE/$art/${tag}.failed.log"
    cat metrics/usage/*.jsonl 2>/dev/null | grep -F "\"ref\":\"${base}\"" > "$STAGE/$art/${tag}.usage.jsonl" || true
    # REGEN_TARGET 기준 재보강 계측 행은 ref=스템이라 별도 회수(analyze-repair)
    cat metrics/usage/*.jsonl 2>/dev/null | grep -F '"src":"analyze-repair"' >> "$STAGE/$art/${tag}.usage.jsonl" || true
    swaps="$(grep -cE '🔄|🩺' "$STAGE/$art/${tag}.log" 2>/dev/null || echo 0)"
    printf '{"tag":"%s","arm":"%s","sha":"%s","base":"%s","rc":%s,"t0":%s,"t1":%s,"elapsed_s":%s,"out":"%s","account_events":%s,"env":"%s"}\n' \
      "$tag" "$arm" "$sha" "$base" "$rc" "$t0" "$t1" "$((t1-t0))" "${out_md:-}" "${swaps:-0}" "${extra[*]:-}" > "$STAGE/$art/${tag}.meta.json"
    echo "  rc=$rc · $((t1-t0))s · out=${out_md:-없음} · 계정이벤트=${swaps:-0}"
  done
  echo "::endgroup::"
done < "$STAGE/articles.txt"

swap_tree "$HEAD_SHA" >/dev/null || true
printf '{"finished":"%s"}\n' "$(TZ=Asia/Seoul date +%FT%T%:z)" > "$STAGE/done.json"
echo "완료 → $STAGE"
