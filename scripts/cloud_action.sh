#!/usr/bin/env bash
# 클라우드 액션 서버 본체 — 구글 드라이브 「내 드라이브/action」 폴더를 우체통 삼아 노뮤트에디터의
#   일괄 액션(기사 수집 + 속보 판정 + 경중 채점)을 5분마다 돌린다(운영자 260814 «git 액션 대체 기능을
#   클라우드 폴더에 · 항시 돌게 · 윈도우/맥 둘 다 · G: 는 변화할 수 있고 계정값 = ems1130g@gmail.com ·
#   노뮤트에디터를 돌리는 일괄 액션 서버 = 독립 제품» · 요구사항 Q1482~Q1487).
# 실행 엔진은 새로 만들지 않는다 — 실제 일은 이 저장소의 수집·판정·채점 실행기(pc_lane.sh)를 그대로 실행(사본 0).
# 이 파일의 몫 3가지:
#   ① 드라이브 action 폴더를 **매 회차 다시 찾는다** — 윈도우는 드라이브 글자 전수 스캔(G: 고정 금지 =
#      운영자 «변화할 수 있고»), 맥은 CloudStorage 마운트(폴더 이름에 계정값이 그대로 들어간다).
#      폴더 이름은 한국어/영어 두 판(내 드라이브·My Drive)을 다 본다. 다중 계정 마운트면 계정.txt 대조 우선.
#   ② 그 폴더의 환경변수.txt 를 읽어 export — 키 값 이관 계약(운영자 260814 «키 값이 필요한 건 내가 따로
#      환경변수로 주면 저장해주셈»)의 착지 슬롯. 지금은 비어 있어도 되고, 키가 오면 이 파일로 들어와
#      드라이브 동기화로 전 기기에 퍼진다. ⚠ source 가 아니라 줄 파싱 = 드라이브 파일의 잡줄이 코드로
#      돌지 않는다 + 메모장 CR(\r) 제거 + 겉따옴표 한 겹 벗김(메모장 저장 사고 흡수).
#   ③ 실행 결과(착지 원장·로그 꼬리)를 그 폴더에 **기기별 파일**로 미러 — 어느 기기(폰 드라이브 앱 포함)에서도
#      상태가 보인다. 파일명을 기기별로 가르는 이유 = 두 PC 가 같은 파일을 쓰면 드라이브 동기화 충돌 사본이 생긴다.
# 전 경로 fail-soft: 드라이브 폴더를 못 찾아도 레인은 돈다(수집이 드라이브 유무에 안 죽는다 · 로그만 로컬 잔류).
# 강제 게이트 = check_cloud_action_chain(shared/check_refs.py) · 설치 = 노뮤트_클라우드액션_설치.bat(윈도우)/.command(맥).
set -u
ACCOUNT="ems1130g@gmail.com"   # 드라이브 계정(운영자 260814 확정값) — 맥 마운트 경로·계정.txt 대조에 쓴다. 정본 1곳(설치 뒷단은 여기서 추출).

_scan_dirs(){ # action 폴더 후보를 위에서부터 낸다(계정 일치 우선순위는 find_action 이 정한다)
  case "$(uname -s)" in
    Darwin)
      # 계정 일치 구글 드라이브 먼저 → 그다음 클라우드 폴더 전수(원드라이브·드롭박스·아이클라우드 포함).
      # ⚠ 운영자가 「원드라이브에 있다」고 할 수도 있다(260814) — 어느 클라우드든 action 폴더면 찾는다.
      for base in "$HOME/Library/CloudStorage/GoogleDrive-$ACCOUNT" "$HOME/Library/CloudStorage"/* \
                  "$HOME/Google Drive" "$HOME/OneDrive" "$HOME"/OneDrive* "$HOME/Dropbox" \
                  "$HOME/Library/Mobile Documents/com~apple~CloudDocs"; do
        [ -d "$base" ] || continue
        [ -d "$base/action" ] && printf '%s\n' "$base/action"
        for mid in "내 드라이브" "My Drive" "문서" "Documents"; do
          [ -d "$base/$mid/action" ] && printf '%s\n' "$base/$mid/action"
        done
      done ;;
    *)
      # 윈도우 Git-Bash — 드라이브 글자 전수 스캔(G: 이 어디로 옮겨가도 산다)
      for l in g h i j k l m n o p q r s t u v w x y z c d e f a b; do
        for mid in "내 드라이브" "My Drive"; do
          [ -d "/$l/$mid/action" ] && printf '%s\n' "/$l/$mid/action"
        done
      done ;;
  esac
  return 0
}

find_action(){
  if [ -n "${NOMUTE_ACTION_DIR:-}" ] && [ -d "${NOMUTE_ACTION_DIR:-}" ]; then printf '%s\n' "$NOMUTE_ACTION_DIR"; return 0; fi
  local first="" d ac
  while IFS= read -r d; do
    [ -n "$d" ] || continue
    [ -z "$first" ] && first="$d"
    ac="$(head -c 120 "$d/계정.txt" 2>/dev/null | tr -d ' \r\n')"
    [ "$ac" = "$ACCOUNT" ] && { printf '%s\n' "$d"; return 0; }
  done < <(_scan_dirs)
  [ -n "$first" ] && { printf '%s\n' "$first"; return 0; }
  return 1
}

# --find = 탐색 결과만 출력(설치 뒷단이 쓴다 · 레인은 안 돈다)
if [ "${1:-}" = "--find" ]; then find_action; exit $?; fi

AD="$(find_action || true)"

# ② 환경변수 주입(키 착지 슬롯 · 없으면 그냥 지나간다 = fail-soft)
if [ -n "$AD" ] && [ -f "$AD/환경변수.txt" ]; then
  while IFS= read -r ln || [ -n "$ln" ]; do
    ln="${ln%$'\r'}"
    case "$ln" in ''|'#'*) continue ;; esac
    case "$ln" in
      [A-Za-z_]*=*)
        k="${ln%%=*}"; v="${ln#*=}"
        case "$v" in
          \"*\") v="${v#\"}"; v="${v%\"}" ;;
          "'"*"'") v="${v#\'}"; v="${v%\'}" ;;
        esac
        # 이름_B64= : 여러 줄 값(유튜브 쿠키·서비스 계정 문서)을 열쇠 입력 페이지가 한 줄로 접은 것 —
        # 여기서 도로 편다(윈도우 = -d · 맥 구판 = -D 폴백). 못 펴면 그 값만 버린다(fail-soft).
        case "$k" in
          *_B64)
            dv="$(printf '%s' "$v" | base64 -d 2>/dev/null || printf '%s' "$v" | base64 -D 2>/dev/null)" || dv=""
            [ -n "$dv" ] && export "${k%_B64}=$dv" 2>/dev/null || true ;;
          *) export "$k=$v" 2>/dev/null || true ;;
        esac ;;
    esac
  done < "$AD/환경변수.txt"
fi

HN="$(hostname 2>/dev/null || echo pc)"; HN="${HN%%.*}"

# 여러 기기가 「운영 서버」로 동시에 켜져 있을 때(운영자 260814 «계정이 연결되면 그 pc가 자동으로 운영 서버»)
# 같은 5분 눈금에 같이 출발하는 걸 흩는다 — 산출은 같아 충돌 0(rebase 정렬)이지만 판정 이중 발사 확률을 줄인다.
# NOMUTE_NO_JITTER=1 = 지터 생략(설치 첫 발사·수동 확인용 — 시계 회차는 항상 지터를 탄다).
[ -n "${NOMUTE_NO_JITTER:-}" ] || sleep $((RANDOM % 40)) 2>/dev/null || true

# ③ 레인 실행(몸통 정본 = pc_lane.sh — 수집·판정·채점·잠금·git 착지 전부 그 파일 소관)
bash "$HOME/nomute-editor/scripts/pc_lane.sh"
RC=$?

# ④ 상태 미러(기기별 파일 = 드라이브 동기화 충돌 0)
if [ -n "$AD" ] && [ -d "$AD" ]; then
  mkdir -p "$AD/상태" "$AD/logs" 2>/dev/null || true
  {
    echo "기기: $HN ($(uname -s))"
    echo "마지막 회차: $(TZ=Asia/Seoul date '+%Y-%m-%d %H:%M:%S') KST  (5분마다 갱신되면 정상)"
    echo "착지 원장: $(cat "$HOME/.nomute_pc_lane_land" 2>/dev/null || echo '기록 없음')"
    echo "회차 종료코드: $RC (0 = 정상)"
  } > "$AD/상태/$HN.txt" 2>/dev/null || true
  for L in "$HOME/pc_lane.log" "$HOME/cloud_action.log"; do
    [ -f "$L" ] && { tail -n 200 "$L" > "$AD/logs/${HN}_최근로그.txt" 2>/dev/null || true; break; }
  done
fi

# ⑤ 로컬 로그 비대 방지(시계가 >> 로 무한 누적 — 2MB 넘으면 꼬리 4000줄만 남긴다)
for L in "$HOME/pc_lane.log" "$HOME/cloud_action.log"; do
  [ -f "$L" ] || continue
  if [ "$(wc -c < "$L" 2>/dev/null || echo 0)" -gt 2000000 ]; then
    tail -n 4000 "$L" > "$L.t" 2>/dev/null && mv "$L.t" "$L" 2>/dev/null || true
  fi
done
exit $RC
