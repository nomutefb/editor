#!/usr/bin/env bash
# 봇 산출물을 붐비는 main에 '최신 재기점 재적층'으로 착지시키는 공용 커밋·푸시 헬퍼.
# 왜: 종전 관용구 `git pull --rebase -X ours origin main 2>/dev/null || true` + push 4회 재시도는
#     같은 파일을 다른 봇이 먼저 밀면 리베이스가 꼬여(HEAD=origin/main 무적용) 로컬이 뒤처진 채
#     4연속 fetch-first 거부 → push는 '성공'처럼 보여도 원격 내용 no-op만 밀고 우리 산출물이 증발.
#     (실측 260716 insta-fetch run 29539535483: 브리프 생성됨 → push 거부 4회 → 다음주기 재수집 →
#      chan_brief 7/14 정지 3일. 같은 관용구 12개 워크플로 공유 = systemic.)
# 방식: git 조작 전 산출물을 워킹트리에서 스냅샷 → 매 시도 {리베이스 잔여 청소 · fetch · reset --hard
#     origin/main(최신 기점) · 스냅샷 재적층 · commit · push}. 리베이스를 안 써서 꼬임 자체가 불가하고,
#     매 시도가 최신 main의 직계 자식 단일 커밋이라 경쟁에 져도 다음 시도서 재동기 → 결국 착지.
# ⚠ 전제(안전 조건): 인자 경로 = 이 워크플로가 '유일 기록자'여야 한다(타 워크플로가 같은 경로를
#     동시에 쓰면 reset 재적층이 그쪽 변경을 덮을 수 있음). insta 산출물(insta_data·chan_brief·apps/insta/data)·
#     sns 산출물 등은 각 파이프라인 단독 소유라 안전. 공유 원장(append-only)엔 쓰지 말 것.
# 사용: bash .github/scripts/git_land.sh "<커밋 메시지>" <경로 ...>
# rc: 항상 0(fail-soft — 커밋 스텝/후속 스텝 비차단) · 미착지 시 ::warning만.
set -u
MSG="${1:-chore: bot commit}"; shift || true
# ── [CF-Pages-Skip] 코얼레싱(운영자 260803 평의회 5인 · Q1331) — 이 헬퍼를 쓰는 봇 산출물(sns-trends·insta·fb·lucy)은
#    「화면에 수 분 늦게 떠도 되는 데이터 churn」이라 CF Pages 빌드를 커밋마다 돌리지 않는다. [CF-Pages-Skip]은
#    CF **전용** 스킵 접두(GitHub Actions 스킵 토큰 5종[skip ci 등]에 미포함 = push 발화 무손상)이고, 다음 비스킵
#    빌드(scrape 15분 메트로놈·코드·제작 산출)가 브랜치 tip을 통째로 배포하므로 스킵분은 누적 반영된다(유실 0).
#    킬스위치 = repo variable PAGES_COALESCE=0(부재·공백 = ON · LIVE_ROLLBACK 관례 동형) → 접두 생략 = 즉시 원복.
#    ⚠ 스킵 금지 축(stamp·제작 산출·pending·asks·조기 반영·scrape)은 이 헬퍼를 안 쓴다 — 명문 = CLAUDE.md · 게이트 = check_refs check_pages_skip.
if [ "${PAGES_COALESCE:-1}" != "0" ]; then
  case "$MSG" in "[CF-Pages-Skip]"*) ;; *) MSG="[CF-Pages-Skip] $MSG";; esac
fi
PATHS=("$@")
[ "${#PATHS[@]}" -gt 0 ] || { echo "git_land: 대상 경로 없음 — no-op"; exit 0; }
# 실존 경로만 남김(페이블 검증단 260718 격리 실증) — git add는 결측 pathspec이 1개라도 있으면 전체를
# 원자 abort(exit 128 · 스테이징 0)해서 유효 경로 산출물까지 통째 무음 드롭된다(`2>/dev/null || true`는
# 에러 은닉만 = 복구 아님 · fb_data.json 스캐폴드[시크릿 미등록 = 파일 미생성]가 트리거였음).
# 아직 안 태어난 스캐폴드 산출물은 여기서 자연 탈락 → 전 경로 실존 케이스 = 종전 동작 바이트 동일.
LIVE=()
for p in "${PATHS[@]}"; do [ -e "$p" ] && LIVE+=("$p") || echo "git_land: 경로 결측 스킵 — $p"; done
[ "${#LIVE[@]}" -gt 0 ] || { echo "git_land: 실존 대상 0 — no-op"; exit 0; }
PATHS=("${LIVE[@]}")
git config user.name "nomute-bot"
git config user.email "bot@users.noreply.github.com"

# 변동 선판정 — 없으면 조용히 종료(푸시 0)
git add -- "${PATHS[@]}" 2>/dev/null || true
if git diff --cached --quiet 2>/dev/null; then echo "git_land: 변동 없음 — 커밋 생략"; exit 0; fi

# ★ git 조작(fetch/reset --hard) 전에 산출물을 워킹트리에서 스냅샷 — reset가 덮기 전 원본 보존이 핵심.
# ⚠⚠ BASE = 스냅샷을 뜬 시점의 트리(260816 봉합의 판별 술어) — 아래 「남의 착지분 복원」이 이 한 값으로
#     자기 삭제와 남의 삭제를 가른다. 스냅샷 이후 남이 얹은 것은 BASE 에 없고, 우리가 소비해서 지운 것은
#     BASE 에 있다 = 삭제 의도의 유일한 구분점(샌드박스 재현으로 오분류 0 실증).
BASE="$(git rev-parse HEAD 2>/dev/null || echo '')"
SNAP="$(mktemp -d)"
for p in "${PATHS[@]}"; do
  [ -e "$p" ] || continue
  mkdir -p "$SNAP/$(dirname "$p")"
  cp -a "$p" "$SNAP/$p" 2>/dev/null || true
done

pushed=0
for i in 1 2 3 4 5 6; do
  git rebase --abort 2>/dev/null || true      # 잔여 리베이스/머지 상태 청소(멱등)
  git merge --abort 2>/dev/null || true
  if ! git fetch -q origin main 2>/dev/null; then echo "git_land: fetch 실패 — 재시도 $i"; sleep $((i * 2)); continue; fi
  git reset -q --hard origin/main 2>/dev/null || true   # 최신 원격 = 기점(이전 로컬 커밋 폐기 = 충돌 원천 제거)
  # 스냅샷을 최신 main 위에 재적층(경로가 dir이어도 안전하게 교체)
  for p in "${PATHS[@]}"; do
    [ -e "$SNAP/$p" ] || continue
    rm -rf "$p" 2>/dev/null || true
    mkdir -p "$(dirname "$p")"
    cp -a "$SNAP/$p" "$p" 2>/dev/null || true
  done
  git add -- "${PATHS[@]}" 2>/dev/null || true
  # ⚠⚠ 남의 착지분 복원(260816 봉합 · 운영자 「확인해서 머지」 · 별도 모델 교차검증 실증) ─────────────
  #   이 헬퍼의 재적층은 `rm -rf` + `cp -a` 라 **경로 통째 교체**다. 그래서 스냅샷을 뜬 뒤에 남이 그 경로에
  #   얹은 것(픽 파일·알림 슬롯·요약 md·원장 줄)이 **삭제로 스테이징된 채 push 가 성공**한다 = 조용한 삭제.
  #   헤더가 「공유 원장엔 쓰지 말 것」이라 금지를 적어 뒀지만 강제가 0이라 호출부가 조용히 어겨 왔다
  #   (실측 = pc_lane 이 pending·messages·queue·cards·asks·metrics·seen_urls 를 그대로 위임).
  #   ⚠ 술어 = **BASE 에 없던 파일의 삭제 = 남이 얹은 것**(복원) · **BASE 에 있던 삭제 = 우리가 소비한 것**
  #     (유지 — 예: analyze 가 처리한 pending 픽). 이 구분이 없으면 소비 기록이 안 남아 같은 픽이 영구 재분석된다.
  #   ⚠ 호출부를 한 줄도 안 고친다 = 변수 경유·래퍼(`_push`)·신규 호출부까지 유일 관문에서 구조적으로 덮는다
  #     (인자 블록리스트 게이트는 pc_lane 처럼 `"$@"` 로 넘기는 자리를 원리적으로 못 보고, insta-fetch 의
  #      messages 실림을 하드로 요구하는 기존 게이트와도 정면 충돌해 레포가 언다 = 그 안은 폐기했다).
  if [ -n "$BASE" ]; then
    while IFS= read -r gone; do
      [ -n "$gone" ] || continue
      if ! git cat-file -e "$BASE:$gone" 2>/dev/null; then      # BASE 에 없다 = 스냅샷 이후 남이 얹은 것
        mkdir -p "$(dirname "$gone")" 2>/dev/null || true
        if git show "origin/main:$gone" > "$gone" 2>/dev/null; then
          git add -- "$gone" 2>/dev/null || true
          echo "git_land: 남의 착지분 복원 — $gone"
        fi
      fi
    done <<EOF_GONE
$(git diff --cached --name-only --diff-filter=D 2>/dev/null)
EOF_GONE
    # 파일형 append 원장 = 줄 단위 합집합(원격에만 있고 BASE 에도 없던 줄 = 남이 추가한 줄 → 되붙인다).
    #   ⚠ 통째 복원이 아니라 합집합이라 우리 줄도 남는다(양쪽 무손실) · 순서는 원격 우선 + 우리 신규 꼬리.
    while IFS= read -r mod; do
      [ -n "$mod" ] || continue
      [ -f "$mod" ] || continue
      git cat-file -e "$BASE:$mod" 2>/dev/null || continue      # BASE 에 없던 파일은 위 복원 축 소관
      # ⚠⚠ 260817 봉합 — 이 합집합은 **줄이 곧 레코드인 append 원장**에만 성립한다(seen_urls.txt·*.jsonl).
      #   통짜 문서(스냅샷 JSON)에 걸면 원격 사본을 우리 문서 **뒤에 이어붙여** 파일을 깨뜨린다.
      #   실측 사고 = `viewer/candidates.json` 은 `json.dumps` 결과를 **개행 없이 한 줄로** 쓰는데,
      #   `>>` 가 그 뒤에 원격 한 줄을 붙여 `…}][{…` = 배열 2~3개가 이어붙은 파일이 main 에 착지했다
      #   (260817 실측 = 30분 주기로 반복 · 그 상태에서 gate_judge·breaking_judge 는 JSONDecodeError 로 죽고
      #    api/candidates 는 깨진 JSON 을 서빙한다 = 수집함·채점이 동시에 조용히 멈춘다).
      #   판별 = **꼬리 개행**(append 원장은 레코드마다 개행으로 닫는다 · json.dumps 스냅샷은 안 닫는다)
      #   + `*.json` 확장자 배제(2중 안전판 — `viewer/insta_data.json` 처럼 **여러 줄인 스냅샷**도 있어서
      #     「줄이 2개 이상」류 판별로는 못 막는다 = 실측 13,151줄·꼬리 개행 없음).
      case "$mod" in *.json) continue ;; esac
      [ -s "$mod" ] && [ "$(tail -c 1 "$mod" | od -An -c | tr -d ' \n')" = "\\n" ] || continue
      git show "origin/main:$mod" > "$SNAP/.remote" 2>/dev/null || continue
      git show "$BASE:$mod" > "$SNAP/.base" 2>/dev/null || continue
      if comm -23 <(sort -u "$SNAP/.remote") <(sort -u "$SNAP/.base") | grep -q .; then
        comm -23 <(sort -u "$SNAP/.remote") <(sort -u "$SNAP/.base") >> "$mod"
        git add -- "$mod" 2>/dev/null || true
        echo "git_land: 남의 원장 줄 합류 — $mod"
      fi
    done <<EOF_MOD
$(git diff --cached --name-only --diff-filter=M 2>/dev/null)
EOF_MOD
  fi
  if git diff --cached --quiet 2>/dev/null; then echo "git_land: 최신 main과 동일 — 착지 불필요"; pushed=1; break; fi
  git commit -q -m "$MSG" 2>/dev/null || true
  if git push -q origin HEAD:main 2>/dev/null; then echo "git_land: 착지 성공(시도 $i)"; pushed=1; break; fi
  echo "git_land: push 경쟁 — 최신 main 재기점 재시도 $i"; sleep $((i * 2))
done
[ "$pushed" = 1 ] || echo "::warning::git_land: 착지 실패(6회 재기점 소진) — 다음 주기 재수집"
exit 0
