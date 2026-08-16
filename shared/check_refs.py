#!/usr/bin/env python3
"""노뮤트 플랫폼 — 참조·버전 정합 점검 (수정 모드 ③ 커밋 전 실행).

v1.15.2류 사본 드리프트(파일 rename 후 참조 미갱신·파일명↔내부 버전 불일치)를
사람 눈 대신 기계로 잡는다. 통과 = exit 0 / 실패 = exit 1 + 목록.

검사 2종:
  1) 경로 참조 실존 — md 문서(라우터·SKILL·앱 지침·메모리·README)의 백틱 참조 중
     레포 경로 꼴(`apps/...`·`shared/...`·`.claude/...`·`_산출/...` + 확장자,
     또는 앱 문서 안의 `NN_*.md` 상대 참조)이 실제로 존재하는지.
     (글롭 `*`·플레이스홀더 `{}`·`<>`·공백 포함 표기는 검사 제외 = 오탐 방지.)
  2) 파일명↔내부 버전 일치 — apps/ 의 `*_v<버전>.md` 파일명 버전 토큰이
     1행 헤더의 버전 토큰과 정확히 같은지 (예: 00_지침_v2.5.md ↔ "... v2.5").

사용: python3 shared/check_refs.py   (레포 어디서 실행해도 됨)
"""

import ast
import bisect
import os
import re
import datetime
import sys
import glob
import base64
import json
import shutil
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 훅 자동 활성화(260725) — clone·기기마다 `git config core.hooksPath .githooks`를 손으로 치는 걸
# 잊으면 게이트가 "조용히 미실행"되고 통과한 줄 착각한다. 실행기가 스스로 켠다(최초 1회).
# ⚠️ CI 러너 제외(260728) — 이 자동 활성화가 러너에도 훅을 붙여, *사람 세션이 남긴* 원장 Q번호 중복이
#   뉴스요약 파이프라인의 산출물 커밋(queue/·asks/)을 pre-commit 거부로 죽였다(실측 260727 3연속:
#   Q902·Q970 중복 → 요약은 성공했는데 commit rc=1 → 다이제스트 통째 유실·ask는 영원히 대기열 잔류).
#   봇 커밋은 데이터 산출물뿐이라 원장·코드 무접촉 = 게이트 대상이 아니다(check-refs.yml 헤더의 선언 그대로).
#   CI 축 커버리지 = ledger-gate.yml(PR) + check-refs.yml(PR + 원장 push) 이 그대로 담당 → 손실 0.
if os.path.isdir(os.path.join(ROOT, '.githooks')) and not os.environ.get('GITHUB_ACTIONS'):
    try:
        import subprocess as _sp
        if not _sp.run(['git', 'config', 'core.hooksPath'], cwd=ROOT,
                       capture_output=True, text=True).stdout.strip():
            _sp.run(['git', 'config', 'core.hooksPath', '.githooks'], cwd=ROOT, capture_output=True)
            print('🔧 core.hooksPath=.githooks 자동 설정(최초 1회 · pre-commit·pre-push 게이트 활성화)')
        # 실행권한 자동 복구(260802) — git은 **실행 불가 훅을 조용히 건너뛴다**(에러도 안 낸다).
        #   훅 파일이 있는데 +x가 빠진 상태 = 게이트가 "있는 줄 알았는데 한 번도 안 돈" 최악의 사각
        #   (자동 활성화가 막으려던 「조용한 미실행」과 정확히 같은 사고 · 아카이브 전개·복사 시 흔히 벗겨진다).
        for _h in ('pre-commit', 'pre-push'):
            _hp = os.path.join(ROOT, '.githooks', _h)
            if os.path.isfile(_hp) and not os.access(_hp, os.X_OK):
                os.chmod(_hp, os.stat(_hp).st_mode | 0o111)
                print('🔧 .githooks/%s 실행권한 복구(+x) — git은 실행 불가 훅을 조용히 건너뛴다' % _h)
    except Exception:
        pass


# 검사 대상 md (백업 폴더 _versions 제외)
SCAN_GLOBS = ('*.md', 'apps/**/*.md', '.claude/skills/**/*.md', 'prompts/**/*.md')   # prompts/ = 라이브 파이프라인 프롬프트(ly-make 등)의 지침 실명 참조도 게이트(승번 리네임 시 dangling 무탐 차단 · 평의회5·10 260709)
# 루트 기준 경로 참조로 보는 접두사 + 확장자
PATH_PREFIX = re.compile(r'^(?:apps|shared|\.claude|_산출)/')
PATH_EXT = re.compile(r'\.(?:md|py|sh|png)$')
# 앱 문서 내부의 형제 파일 참조 (NN_으로 시작하는 .md — 예: 01_지침_*.md 실명 참조)
SIBLING = re.compile(r'^\d{2}_[^/]+\.md$')
# 백틱 스팬 / 버전 토큰
BACKTICK = re.compile(r'`([^`\n]+)`')
VTOKEN = re.compile(r'v\d+(?:\.\d+)*')
# 검사 제외(플레이스홀더·글롭·예시)
SKIP_CHARS = set('*{}<>… ')


def md_files():
    seen = []
    for g in SCAN_GLOBS:
        for p in glob.glob(os.path.join(ROOT, g), recursive=True):
            if os.path.relpath(p, ROOT).startswith('_versions'):
                continue
            seen.append(p)
    return sorted(set(seen))


def check_paths():
    fails = []
    for md in md_files():
        rel_md = os.path.relpath(md, ROOT)
        if rel_md.startswith('_versions'):
            continue
        try:
            text = open(md, encoding='utf-8').read()
        except OSError:
            continue
        for span in BACKTICK.findall(text):
            cand = span.strip().lstrip('./')
            if not cand or any(c in SKIP_CHARS for c in cand):
                continue
            if PATH_PREFIX.match(cand) and PATH_EXT.search(cand):
                if not os.path.exists(os.path.join(ROOT, cand)):
                    fails.append('%s → `%s` 없음 (루트 기준)' % (rel_md, cand))
            elif SIBLING.match(cand):
                if not os.path.exists(os.path.join(os.path.dirname(md), cand)):
                    fails.append('%s → `%s` 없음 (같은 폴더 기준)' % (rel_md, cand))
    return fails


def check_versions():
    fails = []
    for p in glob.glob(os.path.join(ROOT, 'apps', '**', '*_v*.md'), recursive=True):
        rel = os.path.relpath(p, ROOT)
        name_tok = VTOKEN.findall(os.path.basename(p))
        if not name_tok:
            continue
        try:
            head = open(p, encoding='utf-8').readline()
        except OSError:
            continue
        head_toks = VTOKEN.findall(head)
        if name_tok[-1] not in head_toks:
            fails.append('%s → 파일명 %s ≠ 1행 헤더 %s' %
                         (rel, name_tok[-1], (head_toks or ['버전 없음'])))
    return fails


# ── 디자인시스템 토큰 게이트 (분신술 D5 · 260620) ──────────────────────────────
# 값 SSOT = viewer/index.html :root. 신규/수정 CSS는 raw hex/blur/accent-rgba 대신 var() 토큰을 써야 한다(§🎨).
# WARN-only(커밋 차단 안 함) = 점진 강제: 기존은 봐주되 raw가 *늘면* 커밋 전(수정 모드 ③)에 눈에 띈다.
# raw를 토큰으로 줄였으면 baseline도 그만큼 낮춰 재발 방지(드리프트는 늘 때만 잡힘).
# baseline = `:root` SSOT 블록 제외한 현재 raw 카운트(=드리프트는 *늘 때만* 잡힘). 260620 실측.
_DESIGN_BASELINE = {
    'viewer/index.html': {'accent_raw': 78, 'blur': 143, 'hex': 144, 'accent_hex': 32, 'green_wash': 0, 'legacy_green': 0},   # blur151→143 = 도크 유리 폐지(운영자 260802 4차 "미리보기 화면 항상 가려지게" — AI 생성 리드 .geni-lead backdrop blur(--blur-l)+webkit −2 · 바탕 알파 .72→1 불투명 = 스크롤 본문 비침 차단) + 선존 슬랙 −6 실측 조임(§🎨 관례).   # hex142→144 = 레딧 텍스트 게시물 폴백 커버(.tcard-cov.noc.rdfb · 운영자 260729 "텍스트 없는 레딧 게시물은 레딧 이미지를 썸네일로 · 채도 0"): 판 배경 676767(레딧 오렌지 FF4500의 Rec.709 루마 = '채도 0' 지시의 산출값) + 워드마크 순백 fff(§🎨 '순수 흑/백 정당 raw' 선례) — 커버 이미지 내부 색 = index :root 의미색 축 아님(팔레트 예외 · 발행 콘텐츠색과 동축)이라 var() 불가.   # blur147→151 = 채널 요약 대시보드(운영자 260713 "3번 트렌드 느낌·1,2,3메뉴와 일맥상통"): .ch-card 실크 글래스 backdrop blur(12px)+webkit +2(= .soc-item 원문 계승 복사 · 12px 토큰 부재 = 메뉴3 실크 정본값 그대로·신규 창작 0) + 차트 툴팁(.ch-tip) backdrop var(--blur-s)+webkit +2(토큰·raw 아님 — 카운터는 토큰 blur(도 세는 특성).   # blur145→147 = 최상위 단위 접기 헤더(.tgroup-h) 글래스 필 backdrop var(--blur-s)+webkit(토큰·raw 아님 · 운영자 260712 "접기+글래스+도형 얹힘").   # blur140→145 = 트렌드 대시보드 3단(운영자 260712 — 앨범 스택 복귀/더보기 필·모달 세로 항행): .tstk-bk/.tstk-seg/.tsk-more/.tv-nv 글래스 backdrop var(--blur-s)+webkit(전부 토큰·raw 아님 · .sc-tg 필 계승) — 카운터는 토큰 blur(도 세는 특성.   # hex144→145 = 인앱 임베드 뷰어(#trviewdlg .tv-body) 레터박스 #000 — 플레이어 배경 순수 흑 관례(track/conv/edit vstage #000 선례·§🎨 순수 흑/백 정당 raw · 260711).   # hex143→144 = 이미지 위 오버레이 불투명 플레이트 개편(운영자 260709 "아예 불투명·잘 보이는 게 우선" · 검정 .20/.24/.32 반투명 3단 폐지): 발행본 SUMMARY_TPL 이미지 저장(.nm-imdl)만 문서 html,body 배경 동값(0b0d0c) 복사 +1[자기완결 템플릿 = var() 불가 = §핵심명령 3-c 값 복사 계승 · 라이브 index/thumb 플레이트는 전부 var(--bg) 토큰 = 순증 0].   # hex142→143 = OS 스플래시→앱 배경 교차 베일(#bootveil) 색 #192730 = manifest background_color 실측 사본(CSS가 manifest를 못 읽어 var() 불가 = meta theme-color #192129와 동일 예외·§핵심명령 3-a OS 강제 · 운영자 260707 "배경만 이어오고 페이드 교차").   # blur139→140 = 검색 중앙 오버레이(#sovl) 전환(운영자 260706 5차 플레이그라운드 확정 답장): 구 .topsearch input raw blur(7px)×2 제거 −2 · .sov-bg 딤블러 blur(3px)×2 +2(운영자 확정 갱신값 — 근접토큰 --blur-s 8px과 확연히 달라 raw 유지·입력 미포함 형제 레이어 = flicker 안전) · closeSearch JS q.blur() +1(리터럴 카운트 특성·디자인 blur 아님) = 순증 +1.   # hex143→142 = .bgfx 최하층 순검정 #000 폴백 → 토큰 오션 워시(--bias-l2/l1-rgb + --bg) 대체(부팅 검은화면 수정 · §🎨 "raw 줄이면 baseline 낮춰" · 260706 3차 9).   # blur137→139 = 잠금 PIN 슬롯 글래스 플레이트(.lk-slotwrap) backdrop var(--blur-m)+webkit +2(토큰·raw 아님 · 운영자 260706 3차 f "글래스모피즘만" · 시안 = --bias-l1 토큰). --glass 미배선 WARN = 선존(정의 삭제 = :root 기틀 변경이라 보류·운영자 확인 대기).   # accent83→81 = 옛 아바타 hasmsg 링 raw rgba(0,238,210) 2개 삭제(기어 토큰형 대체·사문 회수 ratchet·평의회4 260706).   # blur134→137 = 잠금화면 리디자인(운영자 260706 플레이그라운드 확정 조합): .lockscr 딤블러 backdrop var(--blur-s)+webkit +2 · 해제 블러아웃 keyframes filter var(--blur-m) +1 = 전부 토큰·raw 아님.   # blur132→134 = 리더(#dlg::backdrop) 강프로스트 backdrop var(--blur-l)+webkit +2(토큰·raw 아님·정적 = 타이핑 무관 · 운영자 260705 "리더 배경 움직임 유지+살짝 다크" — 본체 불투명 스택 폐기·프로스트 승격).   # 260705 3차(메뉴 탭색 폐지): hex147→143 = 탭 글로우/검색 오버라이드·COL·SNS 레인 시안 raw 제거(전 탭 강조색 통일·운영자).   # 260705 main 흡수머지: blur134→132(잠금화면 lockscr backdrop 제거분·#1674) · hex147 유지 = main의 SNS 시안 6곳 var(--naver) 토큰화를 raw #0cd0f7로 재고정(naver=그린 이동이라 토큰 유지 시 SNS 그린 오염·픽셀은 #1674 이전과 동일) + 스플래시 폰트/점모션 신규분 상쇄 실측.   # 260705 페이블 검토 이행: hex148→147 = .gauge 시작 raw #5AFFE6→var(--accent-bright) 토큰화(이중관리 회수).   # 260705 후속: hex152→148 = 프로필 탭색 오버라이드 폐지(−4·#9becff×2 등)+stale 주석 hex 정리 − COL.sns 시안 raw +1(#0cd0f7 = SNS 표면 전용·--info 그린 이동 재배선 사유) 순감.   # 260705 팔레트 개편(코어 #00EED2 터쿼이즈·전 raw 1:1 값 스왑=순증 0): accent84→83(.scrap-col.black 테두리 rgba→var 토큰화 −1) · hex163→152(선존 슬랙 실측 ratchet — 스왑은 1:1이라 무증감). # 감사 배치2(260704): accent91→84 = focus 링 6곳(.bar/.sc-memo-in/.ed-wish/.dlg-h/.fb-comment/.seg) rgba(15,253,2)→rgba(var(--accent-rgb)) 토큰화·.ed-wish glow .18→.08. // 감사8인 배치1(260704): blur136→134(.iobtn-edge base 오버레이 blur 제거=editdlg/pastedlg/slide-fb 클립 flicker 차단·.askclip 동형·−2) · hex178→163(.ovc/.ed-chip 유사빨강 #ff5d5d×4·#ff7a7a×2→var(--danger) 통일 −6 + 선존 slack ratchet) · accent93→91(slack).   # green_wash 3→0 = .qflash·.failmenu·.dlgtop 크롬 변종(24,40,29) 무채화 완료(운영자 260704 승인). 신규 초록 워시 유입 하드차단.   # blur138→136 = #askdlg 클립버튼(.askclip) 오버레이 blur14 제거(webkit+표준 −2 · 입력칸 위 떠서 타이핑마다 텍스트 재샘플 번쩍 방지 = revdlg .iobtn-edge{none} 미러·분신술10 260704). blur142→138 = 모달 셸 컨테이너 backdrop-filter 전면 제거(base dialog blur30 −2 + #tooldlg blur34 −2 = −4 · 프로스트는 ::backdrop blur7+헤더 띠 --blur-l 전담 · textarea든 모달도 flicker 안전 = 예외0 통일·오류 안 나는 기본값·운영자 260704 A+B "같은 레벨 통일·논외=감염"). blur140→142 = 뉴스요약 입력(#askdlg) 셸 헤더 X줄 띠 backdrop var(--blur-l)+webkit +2(토큰·raw 아님·영상 .tool-h 계승 · 컨테이너 blur는 textarea 감싸 260701 타이핑 재샘플 번쩍 재발원이라 뺌=재샘플0 안전판 · 분신술 10인 만장 · 260704). blur138→140 = PIN 입력(#pindlg .pin-head) 셸 헤더 글래스 띠 backdrop var(--blur-l)+webkit +2(토큰·raw 아님·메시지함 .mh 계승·미반영0·260704). blur132→138 = 모달 셸 통일(.msgpop .mh·.pmenu-h·.qpop .qh 헤더 글래스 띠 backdrop var(--blur-l)+webkit 각 +2 = +6·토큰·raw 아님·영상 .tool-h 헤더값 계승·editdlg/askhead는 border/bg만이라 blur 0·260704). accent97→93·blur134→132·hex180→178 = yeta(말벗 제타·캐릭터챗) 전체 삭제로 raw 회수(#yetadlg CSS·:root --bubble/--yeta-bg 토큰·.yeta-pick blur(26px)×2 제거 = §🎨 "raw 줄이면 baseline 낮춰"·260704). # hex172→180 = 전광판(마퀴펫) 글자색 프리셋 raw hex 5종(코럴#c85c5c·레몬#d8ff3d·블루#4aa3ff·핑크#ff6ba9·크림#f0e8d8)+accent fallback = 색이 의미(글자색 선택지)라 §🎨 raw 예외·accent(네온그린)는 getComputedStyle(--accent) raw0(마퀴 canvas 렌더 260704). # hex173→172 = yeta 무대 tint 폴백 #7c5cfc 제거→--bubble-me getComputedStyle 직독(동값 raw 복붙 회수 = 이중관리 해소·§🎨 ratchet·운영자 승인·260703). blur132→134 = ▲복원 개수배지(.tr-count) 글래스모피즘 backdrop var(--blur-m)+webkit +2(토큰·raw 아님·운영자 260703 '거의 투명 원 안 강조색 숫자만'). blur129→132 = 하단 네비(.bnav) 글래스 복원 backdrop var(--blur-l)+webkit +2 + 가운데 FAB(.bnav-fab) 반투명 글래스화 backdrop var(--blur-l)+webkit +2 − 옛 'blur(26px) 제거' 주석 −1 = 순증 +3(토큰·raw 아님 · 운영자 260703 "글래스 최대한 살려·가시성 확보됨·FAB도 투명하게 흐름 잇기" → 260701 jank 제거를 실측 트레이드오프로 복원 · accent는 var 토큰이라 accent_raw 순증 0). # hex163→173 = 발행본(SUMMARY_TPL 자기완결 HTML) 검색 헤더(제목검색·K검색·한/영)·키워드 칩·이미지별 저장·영문 제목 신설 → CSP가 외부 CSS 차단이라 var() 불가 = 순수 raw hex 필수(§🎨 self-contained 예외·accent는 #0FFD02 hex만·rgba(15,253,2) 순증 0·운영자 요청 260703). // accent_raw 109→97 = 하단바(.bnav/.bnav-fab/활성 인디케이터)·탑버튼(.totop) 무채색화로 초록 raw 12개 제거(§🎨 "raw 줄이면 baseline도 낮춰"·260703). hex176→163 = 마퀴펫 v2 롤백(운영자 260703 — 원본 pet.webp가 50프레임 '공 드리블+헤딩' 애니였음·재인코딩이 애니를 죽인 실사고) → 스티커 테두리 #000×12+공 테두리 #000×1 제거 = §🎨 ratchet 복원. // hex163→175 = 마퀴 펫 글자 스티커 테두리(12방향 text-shadow 링 #000 ×12 — 순수 흑 의도적 raw·§🎨 아웃라인 원칙 '순수 흑/백만'·토큰 부재·260703). // blur128→129 = 마퀴 펫 v2 간판(.pm-sign) 글래스 backdrop var(--blur-s)+webkit +2 − 옛 산책 펫 CSS 정리 −1 = 순증 +1(토큰·raw 아님·260703). // hex 160→163 = 선존 드리프트 실측 reconcile(yeta v2·v3 페르소나/버블 hex — 발행본 픽토그램·ic-share 작업은 var() 토큰만이라 순증 0 · 주석 PR번호 '#NNNN'은 4자리 hex 오탐이라 'PR NNNN' 표기·260703). // hex 158→160 = 선존 드리프트 실측 reconcile(origin/main 이미 160 = 이전 세션이 hex +2 하고 baseline 미상향 · 발행본 어포던스는 rgba(255,255,255,…)라 hex 카운트 무관·260703). // hex 161→158 = #ff5b4a→var(--danger)(348) 토큰화分 + 선존 slack 실측까지 ratchet(§🎨 "raw 줄이면 baseline 낮춰"·260630). // STAGE1 조임(분신술10·260628): accent 122→109·hex 167→161 = 헐렁 baseline 실측까지(raw 되살아나는 구멍 차단). //   # blur126→128 = 뉴스요약 사진첨부(.askattach) 글래스 backdrop var(--blur-s) +2(토큰·raw 아님·혼자 flat이라 '따로놀던' 것 형제 .iobtn/.sbtn과 통일·운영자 260628) // accent_raw 105→123 요약본 스포티파이→노뮤트 / mkbtn 글래스 +1 / blur90→92 요약본 제목복사 글래스 / 92→90 #editdlg backdrop 제거(main 260621) / +2 요약헤더 .dlbox 글래스 알약 var(--blur-m)(260621) / 124→122 대기열 .qgo·.qb-succ accent rgba→var(--accent-rgb) 토큰화(260622) / blur 92→100 = 당겨서새로고침 #ptr 글래스 var(--blur-s) +2(토큰·raw 아님) + 기존 누적분 흡수(260623) / 100→102 = 수정중 .rev-hint 글래스 var(--blur-s) 복원(260623) / 102→104 = 뉴스요약 .askclip 하단걸침 2A 글래스 var(--blur-s) +2(토큰·복붙버튼 일괄통일·260625) / blur 104→106 = 수집함 병합박스(.mergebox) 글래스 backdrop var(--blur-m) +2(토큰·raw 아님·병합기능·260625) / blur 106→110·hex 168→167 = 병합 바 중립칩 재설계(초록알약 1표면→글래스 칩+별도 X+기준칩 3표면 var(--blur-s)·토큰·raw 아님) + #0c0c0c 제거(빈 mb-n display:none)(260625) / blur 110→112 = 병합 해제 확인 팝오버(.unmerge-go) 글래스 backdrop var(--blur-s) +2(토큰·raw 아님·260626) / blur 112→114 = 라디얼 제작메뉴 자막생성 도구 탭(.tooltab) 글래스 backdrop var(--blur-m) +2(토큰·raw 아님·thumb .tab 계승·260626) / blur 114→116 = 수정/요약 전송버튼(.asksend) 글래스 통일 backdrop var(--blur-s) +2(토큰·raw 아님·.mkbtn 정본 계승·머지시 main 114 기준 +2·260627) / blur 116→120 = 입력칸 복사/붙여넣기/지우개·되돌리기(.iobtn·.iobtn-edge) 이미지 제작 attachCopyPaste 이식 backdrop var(--blur-s)·var(--blur-m) +4(토큰·raw 아님·#revText·#crevText·260627) / blur 120→122 = 뉴스요약 최소화 선택 picker(.min-pick) 글래스 backdrop var(--blur-l) +2(토큰·raw 아님·260627) / blur 122→124 = main 실측 124 lag 흡수(선존 +2) · 필터 오버레이(.filterpop) token var(--blur-l) +2 와 옛 토글(.tk) raw 8px −2 상쇄 = 순증 0(raw→token 교체·옛 카테고리 칩바→필터 버튼 오버레이·260628) / blur124→126 = 붙여넣기 폴백 모달(.pastefb::backdrop) var(--blur-s) +2(토큰·raw 아님·통일 기틀·260628) // accent_hex 32 = 요약본 SUMMARY_TPL 독립문서(viewer :root 없음→var() 불가·의도적 raw)+JS 상수 — hex 표기 우회 봉합·늘면 차단(260703 재실측·발행본 검색헤더 반영).
    'viewer/thumb.html': {'accent_raw': 0, 'blur': 48, 'hex': 22, 'accent_hex': 0, 'green_wash': 0, 'legacy_green': 1},   # hex21→22 = 첨부 사진 배치 굽기(cpBake) 캔버스 여백 #000 — 축소 시 남는 여백을 산출 캔버스에 칠하는 값이고 미리보기 `.cpprev-stage{background:#000}` 산출 배경 관례의 동일값 사본이다(§🎨 순수 흑/백 정당 raw · index hex144→145 레터박스 #000 선례). CSS가 아니라 canvas 2D 컨텍스트라 var() 도달 0 = 토큰 불가.   # blur50→48 = 도크 유리 폐지(운영자 260802 4차 "미리보기 화면 항상 가려지게 — 불투명도가 들어가 뒤가 보임" — .topdock[data-lay="edit"] backdrop blur(--blur-l)+webkit −2 · 바탕 알파 .72→1 불투명 = 스크롤 본문 비침 차단 · 2셸 도크 파리티 동반{tr·edit·sb·k·song·vd·index 리드} = C2 1종 유지).   # blur46→50 = 선존 슬랙 실측 reconcile(코너 옵션 레일 260801 머지분 backdrop var(--blur-s)+webkit +2 등 · 이전 세션 미상향 · 260802 옵션 이주 커밋은 blur 순증 0 = 실측 동수) — §🎨 실측 조임 관례.   # blur43→45 = 진행중 제작 타일(.wip · 운영자 260723 Q469 — 진행 표시를 결과 자리로 이주) 대기 스크림(.wscrim) backdrop blur(var(--blur-backdrop))+webkit +2(토큰·raw 아님 — 카운터는 토큰 blur(도 세는 특성 · edit .wscrim 문법 이식·프로스트만 근접 토큰 계승).   # hex17→19 = 3탭 재편(운영자 260718 "카드 생성|편집|AI 생성 + 선택 요약 스트립"): 선택 요약 스트립(.optstrip) 배경 #000 = 미리보기 스테이지(.cpprev-stage) 전경색 동일값 계승(운영자 "미리보기 전경 컬러와 같은 도형") + 도크 편집 스테이지(.cpprev-box #iePrev) 필러 #121212 = .cpprev-box 동일값(스포티파이 블랙) — 둘 다 기존 정본 값 사본(창작 0 · thumb 무토큰 표면 관례).   # hex14→17·legacy_green0→1 = 합성 미리보기(운영자 260712): 필러박스 '스포티파이 블랙'(18,18,18 운영자 지정·thumb 무토큰 표면) + 스테이지 순흑(track 레터박스 #000 선례) + 자막 강조 CPV_GREEN = 콘텐츠 산출물 색 미러(PIL GREEN·§핵심명령 3-b-1 콘텐츠 축 = UI 재유입 아님·track legacy_green 1 선례 계승).   # blur41→43 = 전체 다운로드 버튼 통이식 — .sbtn 베이스(index 정본 사본) backdrop var(--blur-s)+webkit +2(토큰·raw 아님·운영자 260705 "통으로 이식"·옛 .jsave 자체 구현 폐기).   # 260705 후속: hex15→14 = go2 그라데 raw→var(--warn) 토큰화.   # 260705: blur43→41 선존 슬랙 실측 ratchet(팔레트 스왑은 blur 무관). # 감사 배치3(260704): hex32→15 = err빨강(#ff5d5d/#ff7a7a/#ff8a8a/#ff9b9b/#ffb4b4/#ff9aa0·rgba(255,77/90/120)) → var(--danger)[신설] 통일 + 뜬회색 #cfd2d7/#e8eaed → --mut/--fg + :root amber/arm/warn → 라임(accent-4). # green_wash 2→0 = .cfm·.abdlg 초록 워시 무채화 완료(운영자 260704 승인·thumb 무채톤 rgba(30,32,35)/(14,15,17))   # hex34→32 = 선존 슬랙 실측 ratchet(운영자 승인 260703·새 raw 잠입 틈 차단·STAGE 관례). STAGE1: hex 35→34 실측조임.   # blur39→41 = 빠른메뉴 코어 위 '-' 최소화(#rfab .rmin) 글래스 backdrop blur+webkit = 형제 .rc 코어 외형 계승(blur14 saturate1.3·thumb엔 blur토큰 없어 raw·창 최소화 엄지존·260627). accent rgba 토큰화 완료(--accent-rgb·260621). blur41→43 = 이미지 슬롯(.covimg) 글래스모피즘 backdrop blur+webkit(플레이트 색 제거·픽토 accent 50% · thumb엔 blur토큰 없어 raw·260626). blur43→39 = .covimg 글래스 제거(전경 완전 제거→픽토만·−2) + 상단 3탭 글자화(.tab 글래스 제거·−2)(운영자 260626). blur/hex는 thumb 독자팔레트라 잔존(후속). hex…→28 = .go.err 미입력 빨강(#ff7a7a·#ff5d5d) · hex28→27 = 흰 체크 #fff 제거. hex29→30 = 개별 변형 다운로드(.jvar-dl.dlbtn) 도형제거·픽토그램 흰색 #fff = 좌측 라벨(.jvar #fff)과 색 일치 목적(--fg #e9eaec≠#fff라 토큰화 불가·의도적 raw·260626). hex27→29 = 썸네일 통합 오버레이 포맷색(.ovfmt.post 시안 #1fd6ee · .ovfmt.reels 레몬 #e7ff2e · 후속 토큰화·260624). hex31→29 = /3 저작권 단일토글 전환으로 중복 .cpfmt 시안/레몬 hex 2개 제거(.ovfmt 계승=중복 회수 · §🎨 "raw 줄이면 baseline도 낮춰라" · 분신술7·8·260625). blur32→34 = 저작권 복사칩(.cref-kw 글래스) · blur34→36 = 축약 체크 = 수집함 확인토글(.sc-tg.ack) 글래스 박스 계승(backdrop blur·−→✓ 모프·accent는 var(--accent-rgb) 토큰·260622). blur36→38 = #rfab .rc 빠른메뉴 코어를 수정 연필 FAB(.rev-fab) 글래스 외형 계승(backdrop blur+webkit·thumb엔 blur토큰 없어 raw·260622). blur38→40 = 통합모드 OPA 롤러(260624) → blur40→38 = OPA 롤러 제거·섹션 헤더 인라인 조절 전환(글래스 팝업 폐지·blur 2개 감소·260624). blur38→39 = 축약어 등록 다이얼로그(.abdlg) cfm 글래스 계승(thumb엔 blur토큰 없어 raw·260624). blur39→41 = .iobtn-edge G1 글래스모피즘 backdrop blur13+saturate(복붙버튼 통일·thumb엔 blur토큰 없어 raw·260625). blur41→43·hex30→35 = 붙여넣기 폴백 모달(.pastefb dialog) 신설 — backdrop blur(4px) webkit+표준 +2(thumb엔 blur토큰 없어 raw) + 박스 배경 그라데이션·메시지/입력/버튼 색(#14160f·#0c0f0c·#cfd2d7·#e8eaed = 기존 모달 배경·보조텍스트 패턴 복제·적합 토큰 부재) +5(통일 기틀·readText 막힌 환경 폴백·운영자 260628).   # hex19→21·blur45→46 = 진짜예요 헤더 **강조 골드레몬(운영자 260730 "**로 하면 강조 … 노란색 가까운 색"): CPV_GOLD 미러 상수 주석의 값 표기 1(= nomute_jinjja.HDR_EMPH 255,225,61 미러 · 콘텐츠 산출물 색 축 = UI 재유입 아님 · CPV_BLUE/CPV_GREEN 선례) + 선존 슬랙 실측 reconcile(hex 1·blur 1 = 이전 세션 순증분 미상향 · §🎨 실측 조임 관례 · blur는 JS `.blur(` 리터럴 카운트 특성).
    # ▼ 도구 파일 게이트 편입(분신술 9·10 P0 — 옛 사각지대: 닫기/최소화 버그가 난 파일군이 무방비였음). accent_raw=0 = ly/k 토큰화 완료(--accent-rgb·260628), 늘면 즉시 잡힘. (합성 탭 comp.html은 260710 진입로·파일 폐지 = 게이트 대상서 제거)
    'viewer/conv.html': {'accent_raw': 0, 'blur': 4, 'hex': 3, 'accent_hex': 0, 'green_wash': 0, 'legacy_green': 0},   # hex2→3 = 미리보기 유닛 이식(운영자 260722 영상 스튜디오 정형화 — cpprev-box 필러 #121212 = edit/thumb 정본 동값 사본 · 창작 0 · edit hex8→9 이식과 동일 사유) · 변환 탭 신설 편입(신규 뷰어 게이트 사각 봉합 관례 · 260710). blur4 = .urlclip 글래스 backdrop+webkit(track 계승) 2 + 대기 스크림(.wscrim) blur(5px) 운영자 픽 webkit+표준 2(track과 동일 값·baseline 사유 동일) — 위치 미리보기 .scrub은 track 값(.88 무블러) 계승으로 blur 0(평의회9 정정: 구 blur(8px) 신규분 회수). hex4 = 입력 bg #0e0f11×2 + vstage #000×2(track 관행 내).
    'viewer/song.html': {'accent_raw': 0, 'blur': 9, 'hex': 3, 'accent_hex': 0, 'green_wash': 0, 'legacy_green': 0},   # blur8→9 = 옵션 카드 이주(운영자 260803 5차 "다른 비디오 스튜디오와 동일하게 옵션 탭")에서 「직접 입력」 확정 시 JS `inp.blur()` 1건 = 소프트 키보드 내림(카운터가 JS `.blur(` 리터럴도 세는 특성 · 디자인 blur 아님 · 신규 CSS blur 0 — ly blur14→15 선례 동일 사유).   # 음원 탭 신설 편입(관례 · 260712). blur8 = .cpy(conv .urlclip 계승) 2 + .histbtn 2 + .hpop(msgpop 계승) 2 + 선택자 팝업 .selpop blur16(thumb .platpop 정본 계승 — 도형 나열 폐지 개편) 2. hex3 = #0e0f11 2(전역 input·.rbox) + :root --line 1(.selin 재선언은 전역 상속으로 제거 · 260713 이미지 기틀 정렬).   # hex0→3 = 영상 5탭 미리보기 통일(운영자 260803 "카드 제작 부분과 동일하게") — 쉘 필러 #121212 = thumb `.cpprev-box` 정본 동값 사본 + 사유 주석 표기(주석 hex 계수 특성 · edit hex8→9 선례 동일 사유 · 창작 0).
    'viewer/nb.html': {'accent_raw': 0, 'blur': 6, 'hex': 0, 'accent_hex': 0, 'green_wash': 0, 'legacy_green': 0},   # 자료화 뷰어 편입(260713 실측 seed — 평의회 F2/O6 발견: 신설 뷰어 미등재 = check_design 완전 사각. 이 카운트에서 늘면 잡힘 · 여타 게이트(autocomplete·soremeori 등) 편입은 위반 선정리 후 후속·glob fail-closed 구조 전환은 다이어트 PR에서).
    'viewer/sb.html': {'accent_raw': 0, 'blur': 12, 'hex': 4, 'accent_hex': 0, 'green_wash': 0, 'legacy_green': 0},   # blur12→10 = 도크 유리 폐지 미러(운영자 260802 4차 — .topdock backdrop blur(--blur-l)+webkit −2 · 알파 .72→1 · thumb 정본 동반).   # 콘티(스토리보드) 뷰어 편입(260717 실측 seed — 평의회 8인 arch 발견: 260714 신설분 미등재 = nb와 동일 사각 재발). blur12 = k.html 바이트 계승 사본분(iobtn류 13px/14px saturate 글래스 + var(--blur-s) 토큰 blur도 세는 카운터 특성 · 신규 창작 0) · hex1 = :root 밖 잔존 1(k 계승). 여타 게이트(autocomplete·soremeori 등) 편입은 nb 관례대로 위반 선정리 후 후속.   # blur10→12·hex1→4 = 미리보기 액자 **부활**(운영자 260803 "모든 메뉴의 미리보기 부분을 카드 제작과 동일하게" — Q1159 폐지분 개정): 코너 레일 캡슐 backdrop var(--blur-s)+webkit +2(토큰·raw 아님 = 카운터가 토큰 blur(도 세는 특성) + 쉘 필러 #121212·사유 주석 표기(thumb `.cpprev-box` 정본 동값 사본 · 창작 0).
    'viewer/tr.html': {'accent_raw': 0, 'blur': 7, 'hex': 10, 'accent_hex': 0, 'green_wash': 0, 'legacy_green': 0},   # blur4→7 = 코너 옵션 레일 이식(운영자 260802 "모든 페이지에 해당 미리보기 똑같이") — .trail 캡슐 글래스 backdrop var(--blur-s)+webkit +2(토큰·raw 아님 · 카운터는 토큰 blur(도 세는 특성) + 선존 슬랙 1 reconcile(§🎨 실측 조임 관례).   # hex9→10 = 빈 미리보기 4:5 무대(.cpv-empty) 순수 흑 배경 1(thumb .cpprev-stage.post 정본 동값 사본 — 카드 생성·편집 탭과 동일 세로 액자·양옆 스포티파이 블랙 레터박스 · 운영자 260723 "번역만 튄다" 교정 · §🎨 순수 흑 정당 raw · 창작 0). hex8→9 = 옵션부 편집 탭 정합(운영자 260721 "번역부 = 편집 탭 디자인") — 도크 요약 스트립 .optstrip background 순수 흑 1(thumb .optstrip 정본 exact 사본 · 미리보기 전경색 동일값 · §🎨 순수 흑 정당 raw). hex5→8 = 번역카드 v2 재편(band 반전 박스·미리보기 스테이지 콘텐츠 색축 추가 — 캔버스/발행 렌더 raw = var() 불가 · TR_* 동일 축 · 운영자 260721 4:5 기본+노토산스 확정 시 정렬). hex3→5 = 자동 마커 번역 오버레이 칩 색 2(OV_TEXT #f4f7f4·OV_EMPH #8dff6a — 운영자 승인 시안 dsp_ov3 그대로·캔버스 렌더 콘텐츠 색 = TR_GREEN 동일 축·Q274 260720).   # 번역카드 뷰어 신설 편입(신규 뷰어 게이트 사각 봉합 관례 · [4-1] · 260720). blur4 = .scnclip+.jbt 글래스 backdrop+webkit 각 2(k .scnclip 계승 사본분 — blur13 픽셀 패리티·신규 창작 0). hex3 = JS 콘텐츠 산출물 색 상수 TR_BLACK #000·TR_WHITE #fff·TR_GREEN(디스패치풍 발행 콘텐츠 색 — 캔버스 렌더라 var() 불가 = §핵심명령 3-b-1 축·track PALETTE 선례·UI 재유입 금지).
    'viewer/edit.html': {'accent_raw': 0, 'blur': 11, 'hex': 10, 'accent_hex': 0, 'green_wash': 0, 'legacy_green': 0},   # accent_hex1→0·legacy_green1→0 = 이름표 미리보기 팔레트 제거로 **회수**(운영자 260810 "트래킹 미리보기 없어도됨" · §🎨 「raw 줄면 baseline도 낮춰」 래칫 — 남겨두면 같은 raw가 조용히 재유입된다). (구 사유) accent_hex0→1·legacy_green0→1 = 핀셋 이름표 미리보기 팔레트(`PIN_PALETTE` · 운영자 260809 "아이디어 배선")가 러너 `apps/track/track_render.py` PALETTE **12색 바이트 사본**이다 — 이건 UI 색이 아니라 **러너가 영상에 굽는 산출물 색**이고, 토큰으로 바꾸면 그 순간 러너와 갈려 미리보기가 거짓말을 한다(= 이 미리보기의 존재 이유가 소멸 · thumb legacy_green:1 「콘텐츠 산출물 색 미러 = UI 재유입 아님」 선례 동축 · §핵심명령 3-b-1). 드리프트 차단 = `check_pinset_parity` 하드게이트가 py↔js 목록을 순서까지 대조한다(첫 배선이 실제로 8색 임의 목록으로 갈렸다가 그 게이트에 잡혔다).   # blur9→11 = 색 축 배지(.swax) 글래스 필 backdrop var(--blur-s)+webkit +2(토큰·raw 아님 — 카운터가 토큰 `blur(`도 세는 특성 · index `.sc-tg` 정본 값 사본 = 창작 0 · 운영자 260804 "글래스모피즘 도형 안에 색이 들어가게").   # hex9→10 = 빈 상태 16:9 기본 영역 스테이지(.cpv-empty .cpv-stage) 순흑 배경 1 = thumb .cpprev-stage 정본 동값 사본(운영자 260724 "영상은 16:9 기본 영역 · 검정하고 스포티파이 블랙 구분" — 매트 #121212 안 순흑 프레임)·창작 0.   # hex8→9 = 미리보기 유닛 이식(운영자 260722 "이미지 스튜디오 미리보기 동일하게" — thumb .cpprev-box 필러 #121212 정본 동값 사본 = 창작 0 · CII 「합성 미리보기 쉘」 사다리).   # hex7→8 = 선택 요약 스트립(.optstrip) 배경 순흑 1(운영자 260718 이미지→비디오 스튜디오 정합 — thumb .optstrip 정본 동값 사본 = 창작 0 · thumb hex17→19 스트립 편입과 동일 사유).   # hex5→7·blur11→9 = 미리보기 쉘 정본 통이식(운영자 260716 "자막(편집)도 동일하게" — CII 「합성 미리보기 쉘」 행 계승): .pvsec 액자 mat #121212(스포티파이 블랙 · thumb 필러 동일값 = 창작 아님) 규칙 1 + 사유 주석 표기 1(주석 hex 계수 특성 · ly PR번호 오탐 선례) · blur −2 = 구 stuck 글래스 필 폐지(mat 불투명이 커버 전담 = §🎨 "raw 줄면 baseline도 낮춰" 래칫).   # (구) blur9→11 = PREVIEW 고정 라벨 글래스 필(.pvsec.stuck .fl) backdrop var(--blur-m)+webkit +2(토큰·raw 아님 · thumb .platpop 무채 톤 계승 · 운영자 260712 3차 "예타 상단처럼 글래스모피즘 도형") — 260716 폐지로 회수.   # 편집기 탭 신설 편입(신규 뷰어 게이트 사각 봉합 관례 · 260710). blur4 = .urlclip 글래스 backdrop+webkit 2 + 대기 스크림(.wscrim) blur(5px) webkit+표준 2 = conv와 동수·전부 계승(신규 창작 0). hex4 = 입력 bg #0e0f11×2(URL·구간) + vstage #000×2 = conv 관행 내. +blur4·hex2 = 자막 편집기 이식(배치 B-2 260711 — ly.html 원문 CSS 그대로 = 창작 0·ly에서 검증된 값 복사 계승: .code 배경 #0e0f11·pre 색 #eef7f0 + 편집기 글래스 blur). hex6→8 = 자막 음영 색 선택지 OC_DEF의 순수 흑 #000·백 #fff 리터럴 2(콘텐츠 산출물 색 상수 = §핵심명령 3-b-1 · '순수 흑/백만' 마퀴 스티커 테두리 선례 — 그린·핑크·블루·레몬·레드는 :root 계승 var()라 순증 0 · 260711). blur8→9 = PREVIEW 여백(블러) 질감 연출(.pvbg) filter var(--blur-s) +1(토큰·raw 아님 · filter라 webkit 불요 · 운영자 260712 "블러일 때 옆 연출").
    'viewer/ly.html': {'accent_raw': 0, 'blur': 20, 'hex': 18, 'accent_hex': 0, 'green_wash': 0, 'legacy_green': 0},   # blur16→20·hex19→18 = 소스부 개편(운영자 260717 Q11 — 첨부 확정: 소머리 우측 픽토 2 + 제작본 팝업 + 미리보기 쉘): .lypop 컨테이너+헤더 띠(.mh) backdrop var(--blur-l)+webkit 각 +2 = +4(전부 토큰·raw 아님 — index .qpop 대기열 창 동형 계승·카운터는 토큰 blur(도 세는 특성) · hex = 신규 +3{쉘 mat #121212 ×2 + 사유 주석 표기 1 — edit.html .pvsec 260716 통이식 동일 값·CII 「합성 미리보기 쉘」 행 계승·창작 아님}에도 실측 18 = 선존 슬랙 −4 회수(§🎨 실측 조임 관례 · 260717).   # hex16→22 = 배선평의회 미러 반영(260711) +6 = 순흑백 폴백만{color-mix var(--lypv-oc,#000) 4곳 + 미러 set '#000' 1 + .pv-src var(--lypv-fg,#fff) 1 — OC_DEF 선례 · 콘텐츠색은 전부 var()}.   # hex12→16 = 3분류 배선(운영자 260711): :root 콘텐츠 견본 3(--accent-6·--bias-l2·--warn = index 값 계승·edit 동형) + 강조/글자색 미러 _CC 순수 흑백 리터럴(#fff·#000 = OC_DEF 선례 · 콘텐츠 5색은 var() = 순증 0). # hex11→12 = PR번호 주석 `#1807` 2건이 hex 정규식 오탐(색 아님 · #1807 병합 세션이 baseline 미조정 = 선존 드리프트 260707 실측 — main 자체가 12였음). blur15→16 = 조기 전사 인계 직전 활성 칩 커밋의 JS a.blur() 1건(LY-EARLY 편집 유실 0 · 평의회3 — 동일 리터럴 카운트 특성·디자인 blur 아님·신규 CSS 0). blur14→15 = 자막 상세 편집기 칩 Enter 확정의 JS chip.blur() 호출 1건('blur(' 리터럴 카운트 특성 — 디자인 blur 아님·신규 CSS blur 0·신규 hex 0 = 편집기 색 전부 var()·260706). # 감사 배치3(260704): err빨강→var(--danger)[신설]·뜬회색#cfd2d7→--mut. # blur12→14·hex14→16 = 붙여넣기 폴백 모달(.pastefb) 신설 — backdrop blur(4px) webkit+표준 +2(ly엔 blur토큰 없어 raw) + 박스 배경 그라데이션 #14160f·#0c0f0c +2(기존 모달 배경 패턴·통일 기틀·운영자 260628)
    'viewer/k.html': {'accent_raw': 0, 'blur': 14, 'hex': 4, 'accent_hex': 0, 'green_wash': 0, 'legacy_green': 0},   # blur12→14 = 예시 칩(.seed 탭-투-필) 글래스 backdrop var(--blur-s)+webkit +2(토큰·raw 아님 · .sc-tg 글래스 필 계승 · 운영자 배치 승인 260708 — 빈 입력칸 예문 채움 전용·자동 발사 0)   # hex1→4 = 영상 5탭 미리보기 통일(운영자 260803) — 쉘 필러 #121212 = thumb `.cpprev-box` 정본 동값 사본 + 사유 주석 표기(창작 0 · song·sb 동일 사유).
    'viewer/track.html': {'accent_raw': 0, 'blur': 5, 'hex': 21, 'accent_hex': 1, 'green_wash': 0, 'legacy_green': 1},   # hex15→21 = edit .topdock 영상 미리보기 이식(운영자 260718 "트래킹도 영상 미리보기·영상 편집이랑 동일하게"): 상단 도크 mat #121212 + 하단 페이드 rgba(18,18,18)×2 + .trkpv/.trkpv video 레터박스 #000×2 = edit .topdock/.pvstage 정본 미러(§🎨 순수 흑·스포티파이 블랙 정당 raw·토큰 부재). 트래킹 실연결 편입(평의회6 상 — 신규 뷰어 게이트 사각 봉합·260708). accent_hex1·legacy_green1 = JS PALETTE 인물색 배열(track_render.py PALETTE와 1:1 짝 = 산출물 색 상수·§핵심명령 3-b-1 정당 raw — 카드색≠영상색 드리프트 방지가 목적이라 var() 불가). blur3→5 = 렌더 대기 미리보기 스크림(.wscrim) blur(5px) webkit+표준 +2(운영자 픽 260710 — 플레이그라운드 p2 선택값 답장 = 승인 갱신 · 근접토큰 --blur-s 8px과 확연히 달라 raw 유지 = index #sovl 딤블러 선례). 기존 blur3 = .urlclip 글래스 backdrop+webkit(ly 계승) + .ftype 1. hex17 = PALETTE 12 + 입력 bg #0e0f11×2 + filmstage #0a1a0d + vstage #000×2(ly 팔레트 계승 관행 내).
}
_ROOT_BLOCK = re.compile(r':root\s*\{.*?\}', re.S)

# viewer :root 정의 토큰 중 var() 한 번도 안 쓰는 것 = 죽은 토큰 후보. 단 디자인시스템 어휘는
# 점진 이관(기존 raw→토큰) 중이라 '미리 선언·아직 미배선'이 의도된 게 다수(§🎨). → 현 미배선
# 집합을 baseline 으로 고정하고 그 *밖*의 새 미배선만 경고(드리프트는 늘 때만 = 새 죽은토큰 차단). 260621.
_FWD_UNUSED = {
    '--accent-2', '--amber-rgb', '--blur-backdrop', '--blur-l', '--blur-m', '--blur-s',
    '--blur-xl', '--btn', '--btn-xs', '--danger-rgb', '--dur-fast', '--ease', '--fg-2',
    '--fs-body', '--fs-display', '--fs-h1', '--fs-h2', '--fs-h3', '--fs-label', '--fs-xs',
    '--fw-b', '--fw-x', '--lh-base', '--on-arm', '--r-l', '--r-m', '--r-pill', '--sp-1', '--sp-2',
    '--sp-3', '--sp-4', '--warn',
    '--press-pico',   # 픽토온리 눌림 = thumb/ly/k의 rmin/file가 씀(index엔 .55 픽토 버튼 없음) = forward-declared(260628)
    # accent-N 값 SSOT(운영자 260704 정립) — 의미토큰(danger/warn/arm/thumb/hist-accent/info)이 :root 별칭으로 참조 = 컴포넌트 직접 미배선이 의도(값 단일정본 패턴·§🎨).
    '--accent-2-rgb', '--accent-3', '--accent-4', '--accent-4-rgb',
    # 칩 글자 흰색화(운영자 260704)로 컴포넌트 직접참조 사라짐 — 값은 -rgb변주·별칭(bias-l1/info)으로 계속 사용(값 SSOT 패턴)
    '--accent-5', '--naver',
    # 260705 팔레트 개편: 약진보(lean-l)·오션 배경이 accent-5→bias-l1로 재배선(accent-5=형광그린 이동)되며 -rgb 직접소비 소멸 — 별칭 체인(--info-rgb/--naver-rgb=var(--accent-5-rgb)) 어휘 보존 = forward-unused.
    '--accent-5-rgb', '--naver-rgb',
    '--info-rgb',   # 260705 후속: COL.sns(당겨새로고침 링)가 --info→SNS 시안 raw 재배선되며 마지막 직접소비 소멸 — 별칭 체인 어휘 보존.
}
# --on-arm(arm 채움 위 글자색) = .revsend.confirm 채움 그라데 → 표준 플랫 arm 전환(260622)으로 현재 미배선.
# 정의는 보존(--arm/--arm-rgb 짝 · 향후 채움형 arm 컴포넌트용 어휘) → forward-unused 처리(§🎨).

def _new_dead_tokens(rel='viewer/index.html'):
    """viewer :root 정의 토큰 중 var() 미사용 & baseline 밖 = 새 죽은 토큰(접두사 오탐 가드)."""
    try:
        s = open(os.path.join(ROOT, rel), encoding='utf-8').read()
    except Exception:
        return []
    m = _ROOT_BLOCK.search(s)
    if not m:
        return []
    names = set(re.findall(r'(--[a-z0-9-]+)\s*:', m.group(0)))
    body = _ROOT_BLOCK.sub('', s, count=1)   # :root 정의부 제외 = 실사용만
    return [n for n in sorted(names)
            if n not in _FWD_UNUSED
            and not re.search(r'var\(\s*' + re.escape(n) + r'(?![\w-])', body)]

# ── viewer 인라인 JS 구문 게이트 (분신술 V2/V4 · 260620) ──────────────────────────
# ── 뷰어 목록 SSOT(평의회 게이트 갭 ② — Q169) ─────────────────────────────
# 색 baseline·JS구문·아이콘·자동완성·X문자·tokens_link·소머리 게이트가 각자 튜플을 하드코딩해 서로
# 드리프트하던 것(nb/sb가 색 baseline엔 있는데 JS 게이트엔 없던 실증 = Q165 봉합)의 재발 차단 —
# 신설 뷰어 = 이 상수에만 추가하면 전 게이트 동반 편입.
# 명시 면제(암묵 사각 금지 · Q165 §4 스코프 결정): viewer/tokens.html = 자체 :root 독립(index 주석
#   '자체 :root라 무관' 명시 · 내부 데이터뷰) · viewer/enneagram/* = 자기완결 이식 앱(자체 팔레트·README)
#   — baseline 강제 = 팔레트 예외 침해라 게이트 제외. 재편입 = 운영자 지시로만.
VIEWERS_ALL = ('viewer/index.html', 'viewer/thumb.html', 'viewer/ly.html', 'viewer/k.html', 'viewer/track.html', 'viewer/conv.html', 'viewer/edit.html', 'viewer/song.html', 'viewer/nb.html', 'viewer/sb.html', 'viewer/lucy.html')
VIEWERS_TOOLS = tuple(v for v in VIEWERS_ALL if v != 'viewer/index.html')   # index 제외 게이트용(index = 값 SSOT 본체)

# 머지 가산·복붙 중복 등으로 viewer 인라인 <script>에 SyntaxError(예: let 재선언)가 들어가면
# 브라우저가 스크립트 전체를 평가 안 함 = 뷰어 전면 사망. node로 *구문만* 검사해 커밋 전 차단(하드 게이트).
# node 없으면 스킵(로컬·CI 환경차 흡수).
_SCRIPT_RE = re.compile(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>', re.S)

def check_viewer_js():
    node = shutil.which('node')
    if not node:
        print('⚠️ viewer JS 구문검사 스킵(node 없음)'); return 0
    rc = 0
    for rel in VIEWERS_ALL:   # Q165 nb·sb 편입 → Q169 뷰어 목록 SSOT 상수화
        try:
            html = open(os.path.join(ROOT, rel), encoding='utf-8').read()
        except Exception:
            continue
        js = '\n;\n'.join(_SCRIPT_RE.findall(html))
        if not js.strip():
            continue
        tmp = None
        try:
            with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf-8') as f:
                f.write(js); tmp = f.name
            r = subprocess.run([node, '--check', tmp], capture_output=True, text=True, timeout=30)
        finally:
            if tmp and os.path.exists(tmp):
                os.remove(tmp)
        if r.returncode != 0:
            errs = [x for x in (r.stderr or '').splitlines() if 'Error' in x]
            print('❌ viewer JS 구문 오류 — %s: %s' % (rel, errs[0] if errs else 'syntax error'))
            rc = 1
        else:
            print('✅ viewer JS 구문 OK — %s' % rel)
    return rc

def check_functions_js():
    """Pages Functions(ESM) 구문 하드 게이트 — functions/*.js 하나라도 SyntaxError면 wrangler 번들이
    통째로 실패해 *배포 전체 전멸*(라이브가 옛 판에 동결). 실측 사고: 260706 #1725가 functions/api/ly.js
    닫는 괄호 유실 → 11:31부터 전 빌드 Build failed·라이브 동결(운영자 '반영 안 됨' 신고로 발견).
    viewer 게이트는 인라인 <script>만 봐서 이 구멍을 못 잡았음 → 별도 스윕. ESM(export)이라 .mjs 임시
    복사로 node --check(ESM 모드) 파싱."""
    node = shutil.which('node')
    if not node:
        print('⚠️ functions JS 구문검사 스킵(node 없음)'); return 0
    rc = 0; n = 0
    fdir = os.path.join(ROOT, 'functions')
    if not os.path.isdir(fdir):
        return 0
    for dirpath, _dirs, files in os.walk(fdir):
        for fn in sorted(files):
            if not fn.endswith('.js'):
                continue
            p = os.path.join(dirpath, fn); rel = os.path.relpath(p, ROOT); n += 1
            tmp = None
            try:
                with tempfile.NamedTemporaryFile('w', suffix='.mjs', delete=False, encoding='utf-8') as f:
                    f.write(open(p, encoding='utf-8').read()); tmp = f.name
                r = subprocess.run([node, '--check', tmp], capture_output=True, text=True, timeout=30)
            finally:
                if tmp and os.path.exists(tmp):
                    os.remove(tmp)
            if r.returncode != 0:
                errs = [x for x in (r.stderr or '').splitlines() if 'Error' in x]
                print('❌ functions JS 구문 오류 — %s: %s' % (rel, errs[0] if errs else 'syntax error'))
                rc = 1
    if rc == 0 and n:
        print('✅ functions JS 구문 OK — Pages Functions %d파일(ESM) 파싱 통과' % n)
    return rc

_ICON_DECL_RE = re.compile(r'^const ([A-Z0-9_]+_SVG) = ', re.M)
def check_icon_ssot():
    """공유 아이콘 SSOT 하드 게이트(운영자 260628 '하나 바꾸면 다 바뀜').
    nm-svg.js가 정의한 공유 아이콘을 뷰어가 다시 인라인 const로 선언하면(=섀도잉·드리프트 부활) rc=1.
    각 뷰어가 공유 아이콘을 *쓰면서* nm-svg.js를 로드 안 하면(런타임 ReferenceError) rc=1."""
    nm = os.path.join(ROOT, 'viewer/nm-svg.js')
    if not os.path.exists(nm):
        print('⚠️ nm-svg.js 없음 — 아이콘 SSOT 게이트 스킵'); return 0
    shared = set(_ICON_DECL_RE.findall(open(nm, encoding='utf-8').read()))
    if not shared:
        print('⚠️ nm-svg.js에 공유 상수 0 — 게이트 스킵'); return 0
    rc = 0
    for rel in VIEWERS_ALL:   # Q165 nb·sb 편입 → Q169 뷰어 목록 SSOT 상수화
        try:
            html = open(os.path.join(ROOT, rel), encoding='utf-8').read()
        except Exception:
            continue
        loads = 'nm-svg.js' in html
        inlined = set(_ICON_DECL_RE.findall(html)) & shared
        if inlined:
            print('❌ 아이콘 SSOT 위반 — %s가 공유 아이콘을 인라인 재선언(섀도잉): %s → nm-svg.js만 두고 제거'
                  % (rel, ', '.join(sorted(inlined)))); rc = 1
        used = {c for c in shared if (c in html) and not loads}
        if used and not loads:
            print('❌ 아이콘 SSOT 위반 — %s가 공유 아이콘(%s)을 쓰는데 nm-svg.js 미로드 → <script src="nm-svg.js"> 추가'
                  % (rel, ', '.join(sorted(used))[:60])); rc = 1
    if rc == 0:
        print('✅ 아이콘 SSOT 정합 — 공유 아이콘 %d개 단일정본(nm-svg.js)·인라인 재선언 0' % len(shared))
    return rc

def check_design():
    # accent_raw = 차단(rc=1) 승격(운영자 ③b·STAGE1·260628). 단일 정확패턴 `rgba(0,238,210`(260705 팔레트 개편 — 코어 #0FFD02→#00EED2 터쿼이즈 전환·패턴 동행)라 오탐 0,
    #   index 빼고 전부 0(thumb/ly/k/comp) → 새 raw 강조색 박기 구조적 차단. 봇 무영향(check-refs.yml=PR전용·봇은 데이터JSON만 직푸시·A7 실측).
    # hex/blur/죽은토큰 = WARN 유지(의도적 raw·토큰글래스 +2 누적이라 차단하면 정당작업 막힘).
    warns, hard = [], []
    for rel, base in _DESIGN_BASELINE.items():
        try:
            s = open(os.path.join(ROOT, rel), encoding='utf-8').read()
        except Exception:
            continue
        s = _ROOT_BLOCK.sub('', s, count=1)   # :root = 토큰 SSOT 정의 자리 → 카운트 제외(D5 화이트리스트)
        cnt = {'accent_raw': s.count('rgba(0,238,210'), 'blur': s.count('blur('),
               'hex': len(re.findall(r'#[0-9a-fA-F]{3,8}\b', s)),
               'accent_hex': s.lower().count('#00eed2'),   # 강조색 hex 표기 우회 봉합(rgba만 세던 구멍·분신술 감사·260702 · 260705 코어 터쿼이즈 전환 동행)
               'green_wash': s.count('rgba(27,44,32') + s.count('rgba(24,40,29'),
               'legacy_green': s.count('rgba(15,253,2') + s.lower().count('#0ffd02')}   # 구 코어 그린 재유입 금지(260705 터쿼이즈 전환 — :root의 accent-5 정본 정의는 _ROOT_BLOCK 제외라 미계수 · 컴포넌트 raw는 var(--accent-5[-rgb])로 · 평의회4 봉합) · 자기완결 템플릿(SUMMARY_TPL)에 accent-5 raw가 정말 필요해지면 관례대로 사유 기입 후 baseline 조정   # 초록 시그니처 워시(27,44,32=발행모달·dialog base main #1567 무채화 완료 + 24,40,29=크롬변종 .qflash·.failmenu·.dlgtop) = accent도 hex도 아닌 임의 rgba라 게이트 사각지대였음 → var(--modal-glass) 강제·차단(재검증5 완결성 봉합·분신술10 260704)
        for k, b in base.items():
            if cnt[k] > b:
                msg = '%s: raw %s %d > baseline %d → var() 토큰으로(§🎨)' % (rel, k, cnt[k], b)
                (hard if k in ('accent_raw', 'accent_hex', 'green_wash', 'legacy_green') else warns).append(msg)
    for n in _new_dead_tokens():   # 새로 추가됐는데 var() 미배선인 토큰(죽은 토큰) — 배선하거나 정의 삭제
        warns.append('viewer/index.html: 토큰 %s 정의됐으나 var() 미사용 → 배선하거나 정의 삭제(§🎨)' % n)
    if hard:
        print('❌ 디자인 토큰 게이트(차단) — raw 강조색(rgba(0,238,210)·#00EED2) 또는 초록 워시(rgba(27,44,32·24,40,29) 증가 = var(--accent)/var(--modal-glass) 토큰으로(요약본 템플릿 등 의도적 raw는 baseline 사유 기록 후 조정):')
        for w in hard:
            print('  -', w)
    if warns:
        print('⚠️ 디자인 토큰 게이트(비차단): raw 값 증가 감지 —')
        for w in warns:
            print('  -', w)
    if not hard and not warns:
        print('✅ 디자인 토큰 게이트 — raw 값 baseline 이내(신규 미토큰 없음).')
    return 1 if hard else 0   # accent_raw·accent_hex만 차단, hex/blur/죽은토큰은 WARN


# ── 팔레트 핀 게이트 (운영자 260723 Q463 후속 "색 토큰 미리 잡아놓기") ──────────────────
# 도구 뷰어는 색을 inline :root로 *복사*(§🎨 STAGE3 = 색은 뷰어별 정체성이라 tokens.css 제외).
# 복사본 중 공유 팔레트 accent/의미색(--accent*·--hist*·--danger*·--warn·--amber* 등)은 index 동값이어야
# 하는데 복사라 드리프트 가능 — 260723 실사고: index만 --accent-2 라임→골드 바꿔 도구 뷰어 3곳(썸네일·
# 편집·가사) 접기 삼각형이 라임 잔존. 이 게이트 = 각 뷰어 공유 팔레트를 index 해결값과 대조 → 하드 차단.
# 툴톤(--bg/--pan/--line*/--fg/--mut/--glass*/--modal*/--thumb)은 의도적 뷰어별([16] 차분한 툴톤 재색칠 금지)이라 제외.
# 규칙 정본(단일 진입점) = 디자인기틀/디자인기틀_SSOT.md §0-2·§5 · CLAUDE.md [15]·[16][4] · 전파 짝 = build_design_mirror.py STAGE4(sync_viewer_palette).
_PALETTE_TONE = {'--bg', '--pan', '--line', '--line2', '--fg', '--mut', '--glass2', '--thumb',
                 '--modal-glass', '--modal-glass-anchor', '--modal-head-bg', '--modal-tabs-bg'}
_COLOR_VAL = re.compile(r'^(#[0-9A-Fa-f]{3,8}|rgba?\([^)]*\)|\d[\d,\s.]*)$')


def _root_tokens(rel):
    """뷰어의 모든 :root 블록에서 {name: value}(첫 정의 우선). :root{} 안만 = JS `--x:` 오탐 배제."""
    s = open(os.path.join(ROOT, rel), encoding='utf-8').read()
    d = {}
    for mo in _ROOT_BLOCK.finditer(s):
        for m in re.finditer(r'(--[a-z0-9-]+)\s*:\s*([^;]+);', mo.group(0)):
            n, v = m.group(1), m.group(2).strip()
            if n not in d:
                d[n] = v
    return d


def _resolve(val, table, depth=0):
    """var(--x) 체인을 table로 해결(최대 6단) → 정규화(공백 제거·소문자)."""
    m = re.fullmatch(r'var\((--[a-z0-9-]+)\)', val.strip())
    if m and depth < 6 and m.group(1) in table:
        return _resolve(table[m.group(1)], table, depth + 1)
    return val.strip().replace(' ', '').lower()


def check_palette_sync():
    idx = _root_tokens('viewer/index.html')
    drift = []
    for vf in VIEWERS_TOOLS:
        vc = _root_tokens(vf)
        for n, v in vc.items():
            if n in _PALETTE_TONE or n not in idx:
                continue
            iv = _resolve(idx[n], idx)
            if not _COLOR_VAL.match(iv):   # index 해결값이 단순 색(hex/rgb)인 토큰만 = 구조·중첩var 제외
                continue
            if iv != _resolve(v, idx):
                drift.append(f'{vf} {n}={v} ≠ index {idx[n]}(→{iv})')
    if drift:
        print('❌ 팔레트 핀 게이트 — 도구 뷰어 공유 팔레트가 index와 드리프트(inline 복사 = index 동값 필수 · 툴톤 제외 · 260723 Q463):')
        for d in drift[:24]:
            print('   -', d)
        return 1
    print(f'✅ 팔레트 핀 게이트 — {len(VIEWERS_TOOLS)}뷰어 공유 팔레트 accent/의미색 = index 동값(툴톤 제외 · 드리프트 0).')
    return 0


# 주입 지침 소스에 '----- ... -----' 형태 본문 줄 금지 (R6 가드 · 260624).
# inject_guidelines.sh 의 guidelines_version() 은 해시 입력에서 경로헤더('^----- path -----$')를 제외해
#   파일 rename 에도 같은 버전을 내(불필요 재생성 방지). 그런데 *주입 지침 본문*에 같은 형태의 줄이 있으면
#   그 줄도 해시에서 빠져 → 그 줄만 편집해도 버전이 안 바뀜 = 조용한 드리프트(이 시스템이 막으려는 바로 그것).
#   현재 0건. 이 게이트로 미래에 그런 줄이 들어오는 걸 차단(분신술 8인 권고 260624).
_DIVIDER_RE = re.compile(r'^----- .+ -----\s*$')
_INJECT_GLOBS = ('apps/news/00_에디터_뉴스_운영.md', 'apps/news/01_지침_에디터_뉴스_*.md',
                 'apps/news/02_라이브러리_이미지_*.md', 'PROJECT_MEMORY.md')


def check_inject_dividers():
    fails = []
    for g in _INJECT_GLOBS:
        for path in glob.glob(os.path.join(ROOT, g)):
            try:
                with open(path, encoding='utf-8') as fh:
                    for n, line in enumerate(fh, 1):
                        if _DIVIDER_RE.match(line):
                            rel = os.path.relpath(path, ROOT)
                            fails.append("주입 지침 본문에 '----- ... -----' 줄(%s:%d) — R6 해시서 제외돼 드리프트 미탐 위험. 다른 표기로 바꿔라." % (rel, n))
            except Exception:
                continue
    return fails


def check_inject_markers():
    """주입 지침 파일의 <!-- INJECT-SKIP-START/END --> 마커 짝 균형(260624 단일화 가드).
    START 가 END 없이 열리면 awk 가 EOF까지 통째로 주입에서 누락 = 조용한 드리프트(이 시스템이 막는 것).
    파일별 START 수 == END 수 가 아니면 실패."""
    fails = []
    for g in _INJECT_GLOBS:
        for path in glob.glob(os.path.join(ROOT, g)):
            try:
                txt = open(path, encoding='utf-8').read()
            except Exception:
                continue
            s, e = txt.count('INJECT-SKIP-START'), txt.count('INJECT-SKIP-END')
            if s != e:
                fails.append("INJECT-SKIP 마커 불균형(%s: START %d ≠ END %d) — 미종결 마커는 그 뒤 주입 내용을 통째 누락시킴." % (os.path.relpath(path, ROOT), s, e))
    return fails


def check_sens_vocab():
    """민감 통제어휘 미러 정합 — 드리프트 하드 게이트(260625 분신술 10인).
    정본 SSOT = prompts/news-analysis.md `tags:` 줄 '동일 통제어휘:'. viewer SENS_PROTECT 집합 일치 + DRUG_RE(viewer↔build-viewer) 바이트 동일 강제.
    (이 게이트 부재가 5↔7 드리프트·'장면 검열 없음' stale의 구조적 원인 — 기계로 닫음.)"""
    def _rd(p):
        try:
            return open(os.path.join(ROOT, p), encoding='utf-8').read()
        except Exception:
            return ''
    rc = 0
    prompt, viewer, bv = _rd('prompts/news-analysis.md'), _rd('viewer/index.html'), _rd('build-viewer.mjs')
    seg = prompt.split('동일 통제어휘:', 1)[1].split('(', 1)[0] if '동일 통제어휘:' in prompt else ''
    ssot = set(re.findall(r'#[가-힣·]+', seg))
    mv = re.search(r"const SENS_PROTECT\s*=\s*\[([^\]]+)\]", viewer)
    sp = set(re.findall(r'#[가-힣·]+', mv.group(1))) if mv else set()
    if not ssot or not sp:
        print('⚠️ 민감 통제어휘 추출 실패 — prompts SSOT/viewer SENS_PROTECT 패턴 확인(게이트 무력)')
    elif ssot != sp:
        print('❌ 민감 통제어휘 불일치 — prompts SSOT %s ≠ viewer SENS_PROTECT %s' % (sorted(ssot), sorted(sp)))
        rc = 1
    az = _rd('.github/scripts/analyze.sh')
    def _drug(s, pat):
        m = re.search(pat, s)
        return frozenset(re.findall(r'[가-힣]+', m.group(1))) if m else None
    drug = {
        'viewer': _drug(viewer, r'DRUG_RE\s*=\s*/([^/\n]+)/'),
        'build-viewer': _drug(bv, r'DRUG_RE\s*=\s*/([^/\n]+)/'),
        'analyze.sh': _drug(az, r"grep -qE '([^']*펜타닐[^']*)'"),   # #마약 백스톱 shell 어휘
    }
    present = {k: v for k, v in drug.items() if v}
    if len(set(present.values())) > 1:
        print('❌ DRUG 어휘 불일치(따로 놀기) — ' + ' / '.join('%s:%s' % (k, sorted(v)) for k, v in present.items()))
        rc = 1
    if rc == 0 and ssot and sp:
        print('✅ 민감 통제어휘 미러 정합 — 통제어휘 %d개·SENS_PROTECT 일치·DRUG 어휘 %d곳 동일' % (len(ssot), len(present)))
    return rc


def check_curation_constants():
    """큐레이션 랭킹 상수(viewer) ↔ docs/curation-algorithm.md §★ 정본값 정합 하드게이트.
    #1135식 stale-PR 자기-revert·코드↔문서 드리프트를 CI가 즉시 차단(260628 13인 감사 C8).
    viewer 리터럴(CROSS_POW·FOLLOW_W·BREAKING_RANK_BOOST·GRADE_W grade0 floor)을 §★ 인용값과 대조."""
    rc = 0
    try:
        v = open(os.path.join(ROOT, 'viewer', 'index.html'), encoding='utf-8').read()
        d = open(os.path.join(ROOT, 'docs', 'curation-algorithm.md'), encoding='utf-8').read()
    except Exception as e:
        print('⚠️ check_curation_constants 스킵(파일):', e); return 0
    star = next((ln for ln in d.splitlines() if '누적 랭킹' in ln and 'cross^' in ln), '')
    if not star:
        print('⚠️ check_curation_constants 스킵(§★ 랭킹식 줄 못 찾음)'); return 0
    def vcode(pat):
        m = re.search(pat, v); return m.group(1) if m else None
    def vdoc(pat):
        m = re.search(pat, star); return m.group(1) if m else None
    checks = [
        ('CROSS_POW',           vcode(r'const CROSS_POW\s*=\s*([\d.]+)'),           vdoc(r'cross\^([\d.]+)')),
        ('FOLLOW_W',            vcode(r'const FOLLOW_W\s*=\s*([\d.]+)'),            vdoc(r'FW([\d.]+)')),
        ('BREAKING_RANK_BOOST', vcode(r'const BREAKING_RANK_BOOST\s*=\s*([\d.]+)'), vdoc(r'isBreaking\?([\d.]+)')),
        ('ACC_T_HALF',          vcode(r'const ACC_T_HALF\s*=\s*([\d.]+)'),          vdoc(r'timeAcc\((\d+(?:\.\d+)?)·')),
        ('ACC_T_POW',           vcode(r'ACC_T_POW\s*=\s*([\d.]+)'),                 vdoc(r'timeAcc\([\d.]+·([\d.]+)\)')),
        ('GRADE_W.grade0',      vcode(r'GRADE_W\s*=\s*\{\s*0:\s*([\d.]+)'),         vdoc(r'gradeW\{0:([\d.]+)')),
        ('GRADE_W.grade1',      vcode(r'GRADE_W\s*=\s*\{[^}]*?1:\s*([\d.]+)'),      vdoc(r'gradeW\{[^}]*?1:([\d.]+)')),
        ('GRADE_W.grade2',      vcode(r'GRADE_W\s*=\s*\{[^}]*?2:\s*([\d.]+)'),      vdoc(r'gradeW\{[^}]*?2:([\d.]+)')),
        ('GRADE_W.grade3',      vcode(r'GRADE_W\s*=\s*\{[^}]*?3:\s*([\d.]+)'),      vdoc(r'gradeW\{[^}]*?3:([\d.]+)')),
    ]
    bad = []
    for name, code_v, doc_v in checks:
        if code_v is None or doc_v is None:
            bad.append('%s: 추출실패(code=%s·doc=%s)' % (name, code_v, doc_v)); continue
        if float(code_v) != float(doc_v):
            bad.append('%s: viewer=%s ≠ §★문서=%s (코드↔문서 드리프트/자기-revert 의심)' % (name, code_v, doc_v))
    # FRESH_KEEP_H(scraper/to_candidates.py) ↔ §신규 레인 아사 봉합 "기본 Nh" 정합(평의회9 260716) — 신설 상수가 기계 대조 사각이 되지 않게 같은 게이트에 편입(스크레이퍼 상수 1호).
    try:
        s = open(os.path.join(ROOT, 'scraper', 'to_candidates.py'), encoding='utf-8').read()
        code_f = re.search(r'CAND_FRESH_KEEP_H",\s*"(\d+)"', s)
        doc_f = re.search(r'FRESH_KEEP_H`\(기본 (\d+)h', d)
        if code_f and doc_f:
            if float(code_f.group(1)) != float(doc_f.group(1)):
                bad.append('FRESH_KEEP_H: scraper=%s ≠ §신규레인 문서=%s (코드↔문서 드리프트)' % (code_f.group(1), doc_f.group(1)))
        else:
            bad.append('FRESH_KEEP_H: 추출실패(code=%s·doc=%s)' % (bool(code_f), bool(doc_f)))
    except Exception as e:
        print('⚠️ FRESH_KEEP_H 대조 스킵(파일):', e)
    # FRESH_CROSS_W(viewer fastScore 신규 칼럼 cross 항 · 260803 평의회 8인) ↔ §4 신규 정렬 문서 정합 —
    # 신설 상수가 기계 대조 사각이 되지 않게 같은 게이트에 편입(FRESH_KEEP_H 선례 · 문서 리터럴은 §4
    # 「FRESH_CROSS_W(값)」 한 곳으로 수렴[★ 랭킹 요약줄은 탈리터럴 = 이중 리터럴 드리프트 원천 차단]).
    code_c = re.search(r'const FRESH_CROSS_W\s*=\s*([\d.]+)', v)
    doc_c = re.search(r'FRESH_CROSS_W\(([\d.]+)\)', d)
    if code_c and doc_c:
        if float(code_c.group(1)) != float(doc_c.group(1)):
            bad.append('FRESH_CROSS_W: viewer=%s ≠ §4문서=%s (코드↔문서 드리프트/자기-revert 의심)' % (code_c.group(1), doc_c.group(1)))
    else:
        bad.append('FRESH_CROSS_W: 추출실패(code=%s·doc=%s)' % (bool(code_c), bool(doc_c)))
    if bad:
        print('❌ 큐레이션 상수↔문서 정합 실패(C8 게이트):')
        for b in bad: print('  -', b)
        rc = 1
    else:
        print('✅ 큐레이션 상수↔문서 정합 — CROSS_POW·FOLLOW_W·BOOST·ACC_T·GRADE_W·FRESH_CROSS_W 전체 = 문서 일치.')
    return rc


def check_fast_max_h_parity():
    """FAST_MAX_H 크로스랭귀지 패리티(260710 · 검증6R FP-C로 분리) — viewer "단일출처" 주장과 달리
    auto_pick_breaking.py에 값 사본 존재(칼럼 경계·자동픽 나이 게이트가 갈리면 배지↔자동픽 불일치 · 사본
    유지 = 파이썬이 viewer를 못 읽어서·값만 기계 대조). check_curation_constants 안에 두면 §★ 줄 리워딩의
    조기 return(문서 의존)이 이 코드↔코드 검사까지 조용히 꺼버려 독립 함수로 분리. fail-closed."""
    try:
        v = open(os.path.join(ROOT, 'viewer', 'index.html'), encoding='utf-8').read()
        ap = open(os.path.join(ROOT, 'scraper', 'auto_pick_breaking.py'), encoding='utf-8').read()
    except Exception as e:
        print('❌ check_fast_max_h_parity 파일 읽기 실패(fail-closed):', e); return 1
    mv = re.search(r'const FAST_MAX_H\s*=\s*(\d+)', v)
    mp = re.search(r'^FAST_MAX_H\s*=\s*(\d+)', ap, re.M)
    if not mv or not mp:
        print('❌ FAST_MAX_H 선언 추출 실패(viewer=%s·auto_pick=%s) — 선언 형태 변경 시 이 게이트도 갱신' % (bool(mv), bool(mp))); return 1
    if mv.group(1) != mp.group(1):
        print('❌ FAST_MAX_H 크로스랭귀지 드리프트: viewer=%s ≠ auto_pick_breaking.py=%s (칼럼 경계↔자동픽 나이 게이트 불일치)' % (mv.group(1), mp.group(1))); return 1
    print('✅ FAST_MAX_H 패리티 — viewer(%s) = auto_pick_breaking.py(%s) 크로스랭귀지 동일.' % (mv.group(1), mp.group(1)))
    return 0


def check_follow_enters_parity():
    """followEnters(누적 보조진입) 크로스랭귀지 패리티(260805 8인 평의회 · FAST_MAX_H 패리티와 동형) —
    viewer 술어의 파이썬 사본이 scraper/daily_health.py `_cum_enter` 에 있다(파이썬이 viewer 를 못 읽어서).
    값이 갈리면 "화면엔 떴는데 묻힘 계기판은 여전히 묻혔다고 보고"하는 **무증상 드리프트**가 된다 — 계기판이
    거짓말을 시작하는 순간 §1 자동감시가 죽는데 화면은 멀쩡해서 아무도 모른다. ⚠️ 구판은 같은 술어가
    daily_health 안에만 손복사 3벌(_dominance·긴급부스트 신선창·묻힘 계측)이었고 패리티 게이트가 없었다 =
    뷰어만 고치면 조용히 갈라지던 사각(260805 실측 발견). 추출 실패 = fail-closed."""
    try:
        v = open(os.path.join(ROOT, 'viewer', 'index.html'), encoding='utf-8').read()
        dh = open(os.path.join(ROOT, 'scraper', 'daily_health.py'), encoding='utf-8').read()
    except Exception as e:
        print('❌ check_follow_enters_parity 파일 읽기 실패(fail-closed):', e); return 1
    m_cr = re.search(r'FOLLOW_CROSS_MIN\s*=\s*(\d+)', v)
    m_rc = re.search(r'FOLLOW_RC_MIN\s*=\s*(\d+)', v)
    m_fn = re.search(r'def _cum_enter\(x\):.*?\n\n', dh, re.S)
    if not (m_cr and m_rc and m_fn):
        print('❌ followEnters 상수/미러 추출 실패(cross=%s·rc=%s·_cum_enter=%s) — 선언 형태 변경 시 이 게이트도 갱신'
              % (bool(m_cr), bool(m_rc), bool(m_fn))); return 1
    p_cr = re.search(r'\(x\.get\("cross"\) or 0\) >= (\d+) and rc >= (\d+)', m_fn.group(0))
    if not p_cr:
        print('❌ _cum_enter 술어 추출 실패(daily_health.py) — followEnters 미러 형태가 바뀌었다'); return 1
    want, got = (m_cr.group(1), m_rc.group(1)), (p_cr.group(1), p_cr.group(2))
    if want != got:
        print('❌ followEnters 크로스랭귀지 드리프트: viewer(cross≥%s·rc≥%s) ≠ daily_health _cum_enter(cross≥%s·rc≥%s)'
              % (want + got)); return 1
    print('✅ followEnters 패리티 — viewer(cross≥%s ∧ rc≥%s) = daily_health _cum_enter 동일.' % want)
    return 0


# ── 시간축 계약 픽스처(고정·상대시각) — 케이스별 (라벨, published 오프셋h, first_seen 오프셋h, report_count, 기대 채택원) ──
# 라이브 candidates.json 미사용 = 판정 결정성 확보(스크래퍼 자동커밋 데이터로 코드 게이트가 오발하면 안 됨).
_SCTS_CASES = [
    ('늦수집 옛기사(Q522 회귀축)', -27, -3, 1, 'pub'),    # 어제 기사를 오늘 처음 수집 → 발행나이 유지 = 신규칼럼 진입 금지
    ('정상 발행→수집 지연', -2, -1.5, 1, 'pub'),
    ('미래 오기록(260618 가드)', +2, -1, 1, 'fs'),
    ('역전 + 연속보도(260630 예외)', -10, -12, 8, 'pub'),
    ('역전 + rc낮음(§★ 보수성)', -10, -12, 1, 'fs'),
]


def check_sc_ts_contract():
    """수집함 시간축(scTs) 계약 상비 게이트(운영자 260725 한 수 · Q522 회귀 실물발) — 나이 판정은 신규↔누적
    칼럼 분배·랭킹 감쇠·배지 소멸선의 공통 입력이라 여기가 틀어지면 화면 전체가 조용히 뒤집힌다(실측: 과거튐
    6h 가드가 어제 기사 439/800을 회춘 → 신규 4h칼럼 오염 40건·누적 상위 20/20 점유. 카드 표기는 published
    원본이라 "1일 3시간 전"인데 자리는 최상단 = 코드를 열어야만 보이는 회귀였고 반나절 방치됐다).
    검사 = viewer/index.html의 `scTs`를 **원본 그대로 추출해 node로 실행**(파이썬 재현 0 = 게이트 자신이
    드리프트원이 되는 것 차단 · check_fast_max_h_parity의 '값만 대조'보다 한 단계 위 = 동작 대조) + 고정
    픽스처 5조 판정(_SCTS_CASES). ①이 Q522 회귀축 = 늦수집 옛기사가 발행나이를 유지해 FAST_MAX_H 밖에
    남는가. ②~⑤는 기존 계약(정상 지연·미래 오기록 가드·연속보도 rc 예외·보수성) 동결.
    node 없으면 스킵(로컬·CI 환경차 흡수 · check_viewer_js 관례) · 추출 실패·파일 부재 = fail-closed."""
    node = shutil.which('node')
    if not node:
        print('⚠️ scTs 계약 게이트 스킵(node 없음)'); return 0
    try:
        v = open(os.path.join(ROOT, 'viewer', 'index.html'), encoding='utf-8').read()
    except Exception as e:
        print('❌ check_sc_ts_contract 파일 읽기 실패(fail-closed):', e); return 1
    m_fn = re.search(r'const scTs = c => \{.*?\n\};', v, re.S)
    m_rc = re.search(r'FOLLOW_RC_MIN\s*=\s*(\d+)', v)
    m_fh = re.search(r'const FAST_MAX_H\s*=\s*(\d+)', v)
    if not (m_fn and m_rc and m_fh):
        print('❌ scTs/상수 추출 실패(scTs=%s·FOLLOW_RC_MIN=%s·FAST_MAX_H=%s) — 선언 형태 변경 시 이 게이트도 갱신'
              % (bool(m_fn), bool(m_rc), bool(m_fh))); return 1
    js = (
        'const FOLLOW_RC_MIN = %s, FAST_MAX_H = %s;\n' % (m_rc.group(1), m_fh.group(1))
        + m_fn.group(0) + '\n'
        + 'const H = 3600000, now = Date.now();\n'
        + 'const CASES = %s;\n' % json.dumps([list(c) for c in _SCTS_CASES], ensure_ascii=False)
        + 'const out = CASES.map(([label, ph, fh, rc, want]) => {\n'
        + '  const pub = new Date(now + ph * H).toISOString(), fs = new Date(now + fh * H).toISOString();\n'
        + '  const got = scTs({ published: pub, first_seen: fs, report_count: rc });\n'
        + '  const src = got === Date.parse(pub) ? "pub" : (got === Date.parse(fs) ? "fs" : "other");\n'
        + '  return { label, want, src, ok: src === want, ageH: (now - got) / H, fast: (now - got) < FAST_MAX_H * H };\n'
        + '});\n'
        + 'console.log(JSON.stringify(out));\n'
    )
    tmp = os.path.join(ROOT, '.sc_ts_gate.tmp.mjs')
    try:
        with open(tmp, 'w', encoding='utf-8') as f:
            f.write(js)
        r = subprocess.run([node, tmp], capture_output=True, text=True, timeout=30)
    except Exception as e:
        print('❌ scTs 계약 실행 실패(fail-closed):', e); return 1
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass
    if r.returncode != 0:
        print('❌ scTs 계약 실행 오류(fail-closed):', (r.stderr or '').strip()[:300]); return 1
    try:
        res = json.loads(r.stdout)
    except Exception as e:
        print('❌ scTs 계약 결과 파싱 실패(fail-closed):', e); return 1
    bad = [x for x in res if not x['ok']]
    # Q522 회귀축 재확인 — 늦수집 옛기사(27h)가 신규 칼럼(FAST_MAX_H)에 들어가면 그 자체로 차단
    leak = [x for x in res if x['label'].startswith('늦수집') and x['fast']]
    if bad or leak:
        print('❌ 수집함 시간축(scTs) 계약 위반 — 신규↔누적 분배·랭킹 감쇠가 뒤집힌다(Q522 재발):')
        for x in bad:
            print('   - %s: 기대 %s · 실제 %s (산정나이 %.1fh)' % (x['label'], x['want'], x['src'], x['ageH']))
        for x in leak:
            print('   - %s: 산정나이 %.1fh < FAST_MAX_H(%s) = 어제 기사가 신규 칼럼 점유' % (x['label'], x['ageH'], m_fh.group(1)))
        return 1
    print('✅ 수집함 시간축 계약 — scTs 실행 대조 %d조 전건 통과(늦수집 옛기사 %.0fh = 신규 칼럼 밖 · 미래가드·rc예외·보수성 동결).'
          % (len(res), next(x['ageH'] for x in res if x['label'].startswith('늦수집'))))
    return 0


def check_shell_cache_parity():
    """SW 셸 캐시명 viewer/index.html(applyShellUpdate caches.open) ↔ viewer/sw.js(SHELL_CACHE) 패리티
    (260717 평의회 1·9 — 캐시 계약 리터럴이 두 파일에 복제된 유일 지점. sw.js만 v2로 버전업하면 페이지 put이
    activate가 지우는 죽은 캐시에 쓰고 형제 키 갱신도 무효 = '두 곳 동시 갱신' 주석 규율을 커밋 시점 기계
    게이트로 승격). index에 다른 용도 caches.open이 생기면 이 게이트가 fail = 그때 축 분리 갱신. fail-closed."""
    try:
        v = open(os.path.join(ROOT, 'viewer', 'index.html'), encoding='utf-8').read()
        sw = open(os.path.join(ROOT, 'viewer', 'sw.js'), encoding='utf-8').read()
    except Exception as e:
        print('❌ check_shell_cache_parity 파일 읽기 실패(fail-closed):', e); return 1
    ms = re.search(r"const SHELL_CACHE\s*=\s*'([^']+)'", sw)
    mv = re.findall(r"caches\.open\('([^']+)'\)", v)
    if not ms or not mv:
        print('❌ 셸캐시 리터럴 추출 실패(sw.js=%s·viewer=%s곳) — 선언 형태 변경 시 이 게이트도 갱신' % (bool(ms), len(mv))); return 1
    bad = [x for x in mv if x != ms.group(1)]
    if bad:
        print('❌ 셸캐시명 드리프트: viewer caches.open %s ≠ sw.js SHELL_CACHE %r (두 곳 동시 갱신 계약 위반 — 죽은 캐시 쓰기)' % (bad, ms.group(1))); return 1
    print('✅ 셸캐시 패리티 — viewer caches.open(%d곳) = sw.js SHELL_CACHE %r 동일.' % (len(mv), ms.group(1)))
    return 0


def check_thumb_chain():
    """최근 게시물 커버 회수 체인 게이트(운영자 260803 "이번 문제 안일어나게 하면 더 좋을듯" — 260718 '무성 생략 2/25'가
    260803 '2/12'로 **재발**한 축의 구조 봉합). 결손이 조용한 이유 = 커버가 없어도 캡션 타일이 그럴듯해 보여
    아무도 회귀를 못 본다 → 정적 하드게이트로 못박는다.
    서버 3층(apps/insta/insta_signals.py `_thumb_src`) = ① thumbnail_url ② FB 크로스포스트(`_fb_cover_for`)
    ③ 마지막 성공 커버 원장(`thumb_cache.json` · 만료 인지 `_url_alive`) 전부 생존 + 원장 write-back 존재.
    뷰어 1층(viewer/index.html) = 커버 로드 실패가 **타일 소멸(display:none)이 아니라** 캡션 타일 강등(`chThFail`).
    구 문법(parentNode.style.display='none')이 되살아나면 12칸 그리드에 구멍이 남으므로 그 리터럴 자체를 금지한다."""
    sp = os.path.join(ROOT, 'apps', 'insta', 'insta_signals.py')
    vp = os.path.join(ROOT, 'viewer', 'index.html')
    fp = os.path.join(ROOT, '.github', 'scripts', 'insta_fetch.py')
    try:
        s = open(sp, encoding='utf-8').read()
        v = open(vp, encoding='utf-8').read()
        f = open(fp, encoding='utf-8').read()
    except Exception as e:
        print('❌ check_thumb_chain 읽기 실패(fail-closed):', e); return 1
    miss = []
    for tok, why in (('def _public_cover(', '②-a 인스타 공개 커버 경로 프로브(수집기 · 260803)'),
                     ("mm['thumbnail_url'] = pub", '②-a 프로브 결과 편입'),
                     ('null.jpg', '②-a 플레이스홀더 판별(오탐 커버 차단)')):
        if tok not in f:
            miss.append('insta_fetch.py: %s (%s)' % (tok, why))
    for tok, why in (('_fb_cover_for(m)', '② FB 크로스포스트 폴백 호출'),
                     ('thumb_cache.json', '③ 마지막 성공 커버 원장 경로'),
                     ('_url_alive(', '③ 만료 인지(깨진 이미지 송출 차단)'),
                     ("cache[str(m['id'])]", '③ 원장 write-back(다음 회차 방어선)')):
        if tok not in s:
            miss.append('insta_signals.py: %s (%s)' % (tok, why))
    # ── 소유층(260810 재발 봉합) = 유일하게 **만료가 없는** 방어선 ──
    # ⚠ 왜 게이트인가: 원장(③)은 남의 CDN URL을 저장하는데 그 URL엔 `oe=` 만료가 박혀 온다 — 260810 실측
    #   = 03:32 저장분의 만료가 04:44(수명 1h12m)이고 만료 URL 실호출은 403. 이 워크플로 캐던스가 3h라
    #   **원장은 다음 회차에 이미 죽어 있다** = 「한 번 성공하면 안 빈다」가 원리적으로 불가능했고, 그래서
    #   260718 → 260803 → 260810으로 같은 결손이 세 번 재발했다. 소유층이 그 고리를 끊는 유일한 축이라
    #   한 조각만 빠져도 재발이 **조용히** 복원된다(화면은 캡션 타일이라 멀쩡해 보인다 = 이 체인의 상시 사각).
    # ⚠ 커밋 배선이 특히 조용하다 = 러너가 바이트를 받아 굽기까지 정상 성공하고 rc=0인데, 커밋이 안 되면
    #   다음 체크아웃에서 증발해 화면엔 404. 로그·산출 어디에도 증상이 없어 정적 강제가 유일한 검출기다.
    for tok, why in (('def _cover_own(', '④ 커버 바이트 소유(만료 없는 방어선)'),
                     ("b'\\xff\\xd8\\xff'", '④ JPEG 매직바이트 판정(못 그리는 파일 굽기 차단)'),
                     ("return own, 'own'", '④ 소유 바이트 채택 분기(원장 만료 회차의 마지막 방어)'),
                     ("ent['f'] = own", '④ 원장에 소유 경로 기록(다음 회차 진입점)')):
        if tok not in s:
            miss.append('insta_signals.py: %s (%s)' % (tok, why))
    yp = os.path.join(ROOT, '.github', 'workflows', 'insta-fetch.yml')
    try:
        y = open(yp, encoding='utf-8').read()
    except Exception as e:
        print('❌ check_thumb_chain insta-fetch.yml 읽기 실패(fail-closed):', e); return 1
    land = [ln for ln in y.splitlines() if 'git_land.sh' in ln and not ln.lstrip().startswith('#')]
    if not land:
        miss.append('insta-fetch.yml: git_land 착지 줄(산출 커밋 경로) 소실')
    for ln in land:
        if 'viewer/insta_data.json' in ln and 'viewer/insta_covers' not in ln:
            miss.append('insta-fetch.yml: git_land 인자에 viewer/insta_covers 누락 '
                        '(④ 소유 커버가 커밋 안 됨 = 다음 체크아웃에서 증발 · 화면 404)')
    if 'function chThFail(' not in v:
        miss.append('index.html: chThFail (커버 실패 = 캡션 타일 강등)')
    if "'/media/?size=l'" not in v:
        miss.append('index.html: chThFail 공개 커버 경로 1회 재시도(만료 URL 화면 회수 · 260803)')
    if 'len(near) == 1' not in s:
        miss.append('insta_signals.py: FB 시각 ±3분 유일후보 매칭(캡션 재작성 크로스포스트 회수 · 260803)')
    # 회수 출처 카운터 + 결손 연속회차 알림(운영자 260803 "아이디어 ㄱ") — 화면은 캡션 타일이라 멀쩡해 보여서
    # '조용히 나빠지는 것'이 이 구조의 마지막 사각이었다. 집계·스트릭·알림 3점이 다 살아있어야 그 사각이 닫힌다.
    for tok, why in (("'thumb_src': vdoc_thumb_src", '출처 집계를 뷰어 데이터에 굽기'),
                     ("meta['none_streak']", '결손 연속회차 누적(1회성 딸꾹질과 구분)'),
                     ("'insta-thumb-miss'", '2회 연속 결손 = 운영자 알림(해소 시 clear)'),
                     ('[다음 확인 순서]', '알림 = 인수인계 진단서(다른 세션이 받아 바로 고치게 · 260803)'),
                     ('[막힌 게시물] ', '알림에 막힌 permalink 동봉(재현 진입점)'),
                     ('[재현] python3 apps/insta/insta_signals.py', '알림에 재현 명령 동봉')):
        if tok not in s:
            miss.append('insta_signals.py: %s (%s)' % (tok, why))
    # SNS 카드 커버 폴백(운영자 260803 "sns 모두 적용") — 커버 로드 실패가 img를 숨겨 카드에 빈 구멍을 내던 축.
    # 정본 = 레딧 폴백(.tcard-cov.noc.rdfb) 무채 워드마크 · 강등 = tcCovFail. 구 숨김 문법 부활 = 차단.
    if 'window.tcCovFail' not in v:
        miss.append('index.html: tcCovFail (SNS 카드 커버 실패 = 워드마크 폴백 강등)')
    for cls in ('ytfb', 'tkfb', 'igfb', 'thfb', 'xfb', 'rdfb'):
        if ('.noc.%s' % cls) not in v or ("nocls: '%s'" % cls) not in v:
            miss.append('index.html: %s 폴백 커버 정의·배선(플랫폼 하나가 조용히 빠짐)' % cls)
    for l in v.splitlines():
        if ('covImg' in l or 'xcard-cv' in l) and "onerror=" in l and "style.display='none'" in l:
            miss.append('index.html: SNS 카드 커버 onerror 구 숨김 문법 부활 — 카드 빈 구멍 축')
    if "mm['thumb_src'] = 'pub'" not in f:
        miss.append("insta_fetch.py: 공개경로 회수분 출처 표식(편입 뒤엔 thumbnail_url과 구분 불가)")
    try:
        wf = open(os.path.join(ROOT, '.github', 'workflows', 'insta-fetch.yml'), encoding='utf-8').read()
    except Exception:
        wf = ''
    for line in [l for l in wf.splitlines() if 'git_land.sh "insta: 계정 인사이트' in l]:
        if ' messages' not in line:
            miss.append('insta-fetch.yml: git_land 인자에 messages 누락 — 알림 파일이 커밋 안 돼 화면에 못 뜬다')
    # 스코프 = .ch-th 타일 템플릿 줄만(다른 컴포넌트의 display:none 은닉은 정당 — 예: X 카드 대표 이미지 .xcard-cv는
    # 카드 **안** 부속이라 숨겨도 그리드에 구멍이 안 난다. 여기서 금지하는 건 그리드 셀 자신이 사라지는 축 하나).
    tile = [l for l in v.splitlines() if 'class="ch-th"' in l]
    if not tile:
        miss.append('index.html: .ch-th 타일 템플릿 0줄 추출(선언 형태 변경 = 게이트 갱신 필요 · fail-closed)')
    for l in tile:
        if 'chThFail(this)' not in l:
            miss.append('index.html: .ch-th 타일 onerror가 chThFail(this)가 아님 — 구멍 축')
        if "style.display='none'" in l:
            miss.append("index.html: .ch-th 타일에 구 onerror(display:none) 부활 — 그리드 구멍 축")
    if miss:
        print('❌ 커버 회수 체인 게이트 — 다음이 끊겼다(최근 게시물 빈 칸 재발 축):')
        for m in miss:
            print('   · ' + m)
        return 1
    print('✅ 커버 회수 체인 게이트 — 수집 2층(Graph 재조회·공개 커버 경로) + 산출 3층(API·FB 크로스포스트[캡션∨시각유일]·성공 원장+만료 인지) + 뷰어 2층(공개경로 재시도·캡션 강등) + 출처 카운터·진단서 알림 + SNS 6플랫폼 워드마크 폴백 생존.')
    return 0


def check_idle_timer_guard():
    """유휴 타이머 가드 게이트 — C16(런타임)의 정적 짝(운영자 260807 "정적 짝 게이트도 ㄱㄱ").

    계약 = 「셸(viewer/index.html)의 `setInterval` 콜백이 DOM을 쓰는데 **영원히 돈다면**,
           가시성·모달 가드(`document.hidden`/`visibilityState`/`isComposingModalOpen()`/`.open`)를 동반한다」

    ⚠ 신설 사유 = `smoke_studioshell` C16은 **런타임**이라 「그날 실제로 돈 것」만 잡는다 — 조건이 안 맞아
    측정 창에서 잠자던 타이머는 그냥 통과한다. 260807 실사고(금융 전광판 5초 인터벌이 화면에 안 보이는
    DOM[실측 0×0px]을 계속 갈아끼움)의 구조적 원인은 **형제는 가드를 갖는데 자기만 안 가진 것**이었고
    (10줄 아래 `_tu`가 그 가드를 보유 · 260727 시계 봉합에도 안 따라왔다), 그건 **정적으로 보이는 모양**이다.
    런타임(C16) + 정적(이 게이트) 두 겹이라야 새 타이머가 조용히 빠질 구멍이 사라진다.

    ⚠ 스코프 = `viewer/index.html` **단독**. 도구 뷰어(thumb·tr·edit…)는 iframe으로 모달 **안**에 뜬다 =
    운영자가 실제로 보고 있는 화면이라 판정 대상이 아니다(C16의 「모달 안은 비대상」과 같은 경계).

    ⚠ **유한 수명 면제가 실효 조건**(위양성 3겹 중 핵심 · 260807 실측으로 정한 경계) — 술어를
    「DOM 쓰기 ∧ 무가드」로만 두면 현행 4건이 걸리는데 **전건 판독 결과 위양성**이었다:
      · `iv`(13970) `++n > 40` = 자기 해제·최대 10초  · `fr._er`(15261) `++n > 180` = 최대 18초
      · `_tvPoll`(13944) `Date.now() - t0 > 420e3` = 예산 상한 보유
    전부 **사용자가 시작한 작업의 유한 수명 타이머**다(작업이 끝나면 사라진다). 금융 티커와의 결정적
    차이가 바로 이 축이고 — 그쪽 `clearInterval`은 「DOM에서 사라졌을 때」뿐이라 **화면이 살아있는 한 영원**이다.
    → 횟수 상한(`++n >`)·경과 상한(`Date.now() - t0 >`) 표식을 가진 콜백은 면제한다.

    ⚠ **면책표 없이 하드 0** — 술어를 좁힌 뒤 남은 유일 잔여였던 `_tvTick`(영상 받기 진행 표시)은
    baseline에 박지 않고 **가드를 실제로 넣어 해소**했다(경과가 t0 기준 산식이라 스킵분은 복귀 즉시
    정확히 따라잡는다 = 표시 손실 0). 부채 원장 증가 0.

    ⚠ 주석 줄 제외(주석 처리 우회 차단) · 정적(렌더·LLM·네트워크 0)."""
    path = os.path.join(ROOT, 'viewer', 'index.html')
    try:
        src = open(path, encoding='utf-8').read()
    except Exception as e:
        print('❌ check_idle_timer_guard 읽기 실패(fail-closed):', e); return 1
    lines = src.split('\n')
    WRITE = re.compile(r'\.(innerHTML|outerHTML|textContent|innerText|className|classList|setAttribute|'
                       r'removeAttribute|append|appendChild|replaceChildren|prepend|insertAdjacentHTML)\b'
                       r'|\.style\.|\.hidden\s*=')
    GUARD = re.compile(r'document\.hidden|visibilityState|isComposingModalOpen|\.open\b|_trRotVis')
    FINITE = re.compile(r'\+\+\w+\s*>|\w+\+\+\s*>|Date\.now\(\)\s*-\s*\w+\s*>')   # 유한 수명 표식
    bad = []
    for m in re.finditer(r'setInterval\s*\(', src):
        ln = src[:m.start()].count('\n') + 1
        head = lines[ln - 1].strip()
        if head.startswith('//') or head.startswith('*'):
            continue                                            # 주석 줄 = 비대상
        i = m.end() - 1; depth = 0; j = i
        while j < len(src):                                     # 괄호 균형으로 인자 본문 절취
            if src[j] == '(': depth += 1
            elif src[j] == ')':
                depth -= 1
                if depth == 0: break
            j += 1
        body = src[i:j + 1]
        if WRITE.search(body) and not GUARD.search(body) and not FINITE.search(body):
            bad.append((ln, head[:70]))
    if bad:
        print('❌ 유휴 타이머 가드 게이트 — 모달 뒤 DOM을 만지는 영구 타이머에 가시성·모달 가드가 없다:')
        for ln, h in bad:
            print(f'   · viewer/index.html:{ln} — {h}')
        print('   → 형제 타이머 정본 계승 = `if (document.visibilityState !== \'visible\' || isComposingModalOpen()) return;`'
              ' (스킵분은 다음 틱 따라잡음 · #13447 유지보수 규칙) · 유한 수명 작업 타이머면 횟수·경과 상한을 콜백에 둔다.')
        return 1
    print('✅ 유휴 타이머 가드 게이트 — 셸 영구 타이머 전건 가드 보유(유한 수명 작업 타이머는 면제 · 면책표 없음 · C16 런타임 축의 정적 짝).')
    return 0


def check_boot_bg_parity():
    """OS 스플래시→앱 배경 연속 3값 정합 게이트(운영자 260805 승인 "아이디어도 진행하구").

    계약 = ⓐ `#bootveil`(첫 페인트가 이어받는 단색 베일) 배경 == manifest `background_color`
           ⓑ index `meta[name=theme-color]` == manifest `theme_color`
    ⓐ의 근거는 그 선언 자신의 주석이다 — "manifest background_color 단색을 첫 페인트가 그대로 이어받고".

    ⚠ 신설 사유 = **CSS·meta가 manifest를 못 읽어 var() 도달이 0**이라, 같은 색이 세 파일에 손으로 복사돼
    있다(viewer/manifest.json · index `#bootveil` · index `meta[theme-color]`). 한쪽만 고치면 나머지가
    조용히 낡는데, 증상이 「스플래시에서 앱으로 넘어올 때 색이 한 번 튄다」뿐이라 눈으로 잡기 어렵다.
    기존 게이트는 전부 다른 축을 본다 — check_design은 토큰 raw **개수**, 팔레트 핀은 **뷰어 간** 동값,
    거울 정합은 :root ↔ base.css → 「OS가 그리는 색과 우리가 그리는 색이 같은가」는 축 자체가 없었다.

    ⚠ ⓐ는 하드 0 금지 = 260805 실측이 **이미 어긋나 있다**(manifest #000000 vs bootveil #070a12).
    해소는 둘 중 어느 값으로 통일하느냐 = 색 결정 = [4-3] 운영자 승인 대기 사항이라 WARN으로 띄워
    잊히는 것만 막는다(승인 후 값 통일 → 하드 승격 후보). ⓑ는 현행 일치라 하드."""
    import json as _json
    try:
        mf = _json.load(open(os.path.join(ROOT, 'viewer', 'manifest.json'), encoding='utf-8'))
        idx = open(os.path.join(ROOT, 'viewer', 'index.html'), encoding='utf-8').read()
    except Exception as e:
        print('❌ check_boot_bg_parity 추출 실패(fail-closed):', e); return 1
    m_bg = (mf.get('background_color') or '').strip().lower()
    m_th = (mf.get('theme_color') or '').strip().lower()
    veil = re.search(r'#bootveil\s*\{[^}]*?background:\s*(#[0-9a-fA-F]{3,8})', idx)
    meta = re.search(r'<meta\s+name="theme-color"\s+content="(#[0-9a-fA-F]{3,8})"', idx)
    if not veil or not meta:
        print('❌ 부팅 배경 정합 게이트 — 앵커 소실(#bootveil 배경 %s · meta theme-color %s) = 선언 형태가 바뀌었다. 게이트를 현행화하라(fail-closed).'
              % ('발견' if veil else '실종', '발견' if meta else '실종')); return 1
    v_bg, v_th = veil.group(1).lower(), meta.group(1).lower()
    if v_th != m_th:
        print('❌ 부팅 배경 정합 — meta[theme-color] %s ≠ manifest theme_color %s. 상태바 색이 갈렸다(같은 값 손복사 = 한쪽만 고친 흔적).' % (v_th, m_th)); return 1
    if v_bg != m_bg:
        print('⚠️ 부팅 배경 정합(WARN·비차단) — #bootveil %s ≠ manifest background_color %s.' % (v_bg, m_bg))
        print('   · 계약(주석 자신의 선언) = 베일은 OS 스플래시 단색을 그대로 이어받는다 → 지금은 스플래시→앱 전환에 색 점프가 있다.')
        print('   · 해소 = 둘 중 어느 값으로 통일할지 = 색 결정 = 운영자 승인 사항([4-3]). 승인 시 값 통일 후 이 축을 하드로 올린다.')
        return 0
    print('✅ 부팅 배경 정합 게이트 — 스플래시→앱 3값 동일(background %s · theme %s · 베일 %s).' % (m_bg, m_th, v_bg))
    return 0


def check_shell_put_integrity():
    """셸캐시 put 절단 검문 의무 게이트(260802 '상단만 렌더' **재발** 실사고 — 1차 봉합이 sw.js put에만 </html>
    꼬리 검문을 달고, index.html applyShellUpdate의 페이지측 put은 무검문으로 남아 '탭하면 반영' 중 전송 절단이
    잘린 셸을 두 키(/·/index.html)에 동시에 꽂았다. 같은 리터럴이 파일 두 곳에 복제된 축 = 패리티 게이트와 동형).
    규칙 = 셸 캐시에 닿는 모든 `.put(` 호출은 상행 15줄 안에 intact 술어 리터럴(`/<\\/html>`)을 동반해야 한다.
    검출 = `caches.open('<셸명>')`/`caches.open(SHELL_CACHE)` 상행 25줄 근접 휴리스틱(PREF 캐시·IDB put 비대상).
    put 지점 0곳 추출 = 게이트 자멸(선언 형태 변경) 방지 fail-closed."""
    try:
        sw = open(os.path.join(ROOT, 'viewer', 'sw.js'), encoding='utf-8').read()
        shell = re.search(r"const SHELL_CACHE\s*=\s*'([^']+)'", sw).group(1)
    except Exception as e:
        print('❌ check_shell_put_integrity 추출 실패(fail-closed):', e); return 1
    targets = [os.path.join('viewer', 'sw.js')]
    vdir = os.path.join(ROOT, 'viewer')
    for f in sorted(os.listdir(vdir)):
        if f.endswith('.html'):
            targets.append(os.path.join('viewer', f))
    total, bad = 0, []
    for rel in targets:
        try:
            lines = open(os.path.join(ROOT, rel), encoding='utf-8').read().splitlines()
        except Exception:
            continue
        ctx = [i for i, l in enumerate(lines) if ("caches.open('%s')" % shell) in l or 'caches.open(SHELL_CACHE)' in l]
        if not ctx:
            continue
        for i, l in enumerate(lines):
            if '.put(' not in l or not any(0 <= i - c <= 25 for c in ctx):
                continue   # 셸 캐시 컨텍스트(상행 25줄) 밖 put = 다른 저장소(PREF·IDB) = 비대상
            total += 1
            if '<\\/html>' not in '\n'.join(lines[max(0, i - 15):i + 1]):
                bad.append('%s:%d' % (rel, i + 1))
    if bad:
        print('❌ 셸캐시 put 절단 검문 누락(260802 재발 축): %s — put 상행 15줄 안에 꼬리 술어 /<\\/html>\\s*$/ 검문을 달아라(잘린 셸 캐시 주입 = 기기 감금).' % ', '.join(bad)); return 1
    if total == 0:
        print('❌ 셸캐시 put 지점 0곳 추출 — 선언·호출 형태 변경 시 이 게이트도 갱신(fail-closed)'); return 1
    print('✅ 셸캐시 put 절단 검문 — %d지점 전부 intact 술어 동반(무검문 put 0).' % total)
    return 0


def check_workflow_amend():
    """워크플로 결과 커밋 `--amend` 금지 게이트(운영자 260803 6-4 승인 — filltest 동시 3발사 실사고의 구조 봉합).
    사고 구조 = 러너 결과 커밋 재시도 루프에서 `pull --rebase -X ours`가 자기 커밋을 'already upstream'으로
    드랍하면 `git commit --amend`가 직전 커밋(= **남의 푸시된 커밋**)을 개서 → non-ff 영구 거절 4연패 = 산출 유실
    (런 30779914067 실측 · 원조 imggen은 새-커밋 방식으로 안전했는데 사본 계보(resize→upscale)가 --amend로
    개악된 복제 사고 = 셸캐시 put 1차 봉합이 사본을 놓쳐 재발한 축과 동형). 러너 커밋은 전부 push 재시도 루프와
    함께 살므로 워크플로 안 `git commit --amend`는 **전면 금지**(현행 0건 = 베이스라인 청정 · 재병합 = 새 커밋
    `git diff --cached --quiet || git commit -m …`). 합법 예외가 생기면 사유와 함께 면책 목록을 신설하라(_BASE 관례)."""
    wdir = os.path.join(ROOT, '.github', 'workflows')
    try:
        files = sorted(f for f in os.listdir(wdir) if f.endswith(('.yml', '.yaml')))
    except Exception as e:
        print('❌ check_workflow_amend 디렉터리 읽기 실패(fail-closed):', e); return 1
    if not files:
        print('❌ check_workflow_amend 워크플로 0건 — 경로 확인(fail-closed)'); return 1
    rx = re.compile(r'git\s+commit\b[^\n]*--amend')
    bad = []
    for f in files:
        try:
            lines = open(os.path.join(wdir, f), encoding='utf-8').read().splitlines()
        except Exception as e:
            print('❌ check_workflow_amend 읽기 실패(fail-closed): %s — %s' % (f, e)); return 1
        for i, l in enumerate(lines, 1):
            if rx.search(l) and not l.lstrip().startswith('#'):   # 주석(사고 각주) = 비대상 · 실행줄만
                bad.append('%s:%d' % (f, i))
    if bad:
        print('❌ 워크플로 --amend 금지(260803 실측 = 자기 커밋 드랍 시 남의 푸시 커밋 개서 → non-ff 영구거절 = 산출 유실):')
        for b in bad:
            print('   -', b, '→ 재병합은 새 커밋으로(`git diff --cached --quiet || git commit -m …` · imggen 원조 패턴)')
        return 1
    print('✅ 워크플로 --amend 금지 게이트 — %d개 워크플로에 실행줄 --amend 0건(재병합 = 새 커밋 계약 유지).' % len(files))
    return 0


def check_push_send_checkout():
    """완료 푸시를 쏘는 워크플로는 구독자 명단·알림 아이콘을 **체크아웃 목록에 갖는다**(260816 실사고 봉합).
    CONTRACT: check_push_send_checkout

    ⚠ 진범 = 260728 「체크아웃 다이어트」가 sparse-checkout을 도입하면서 `push/`를 목록에 안 넣었다.
    `push_send.py`는 `push/subscriptions.json`(구독 기기)을 읽는데 러너 디스크에 그 파일이 아예 없으니
    `jload(SUBS, [])`가 기본값 빈 배열을 돌려주고 **「구독자 없음 — 발송 생략」으로 정상 종료(rc=0)**한다.
    → 제작은 성공하고 스텝도 초록인데 **푸시만 한 통도 안 나간다**(실측 260816 run 31933687078 로그).
    피해 범위 = 카드 제작·영상 편집·AI 이미지·음원·보이스·변환·트래킹 **7레인**(속보 breaking-judge와
    영상 받기 vidl-make만 `push`를 갖고 있어 살아 있었다 = 「형제는 가진 걸 자기만 안 가진」 이 레포 최빈 축).

    ⚠ 신설 사유 = 기존 게이트가 전부 다른 축이다 — `check_workflow_yaml` = 문법 · `check_workflow_amend` =
    커밋 방식 · `check_paths` = 경로 실존 · `smoke_*` = 화면 렌더 → 「푸시가 **실제로 나갈 수 있는 상태인가**」는
    축 자체가 없었고, 러너가 초록으로 끝나고 화면 증상도 0이라 **운영자 눈이 유일한 검출기였다**
    (insta-thumb-miss·brk_misfire 동축). 새 제작 레인이 생기면 같은 자리에서 또 조용히 빠진다.

    술어 = 「실행줄에서 `push_send.py`를 호출 ∧ `sparse-checkout:` 사용 → 그 목록에 `push`(구독자 명단)와
    `assets/brand`(알림 아이콘 번들 `notif_dataurl.json`) 두 경로 보유」.
    ⚠ 아이콘도 **하드**인 이유(260816 2차 · 운영자 「속보 알림 아이콘도 같이 붙여줘」) = 번들이 없으면
    `notif_icon()`이 None을 뱉어 페이로드 `icon`이 빈 문자열이 되고, 그러면 폰 SW가 `kind`로 **주소**를 조립해
    받아오는 구 경로로 되돌아간다 — 그 방식은 260727에 이미 실패로 판정된 축이다(주석 원문 = 「payload에 아이콘
    *주소*를 주면 폰이 그 이미지를 받아오지 못해(Access 벽·미배포 404) 안드로이드가 사이트 첫 글자 'A' 폴백을
    그린다 · data URL = 네트워크 요청 0 = 그 벽과 무관하게 항상 그려진다」). 즉 아이콘 누락은 「조금 흐린 알림」이
    아니라 **폐기된 경로로의 조용한 회귀**이고, 주소가 그날 열려 있으면 증상이 안 보여 더 늦게 발견된다
    (260816 실측 = 그 URL이 HTTP 200이라 속보 아이콘이 나오는 것처럼 보였다 = 위장된 정상).
    전체 체크아웃(sparse 미사용) 워크플로는 대상 밖 = 이미 다 받는다. 주석 줄 제외(주석 처리 우회 차단).
    정적 · 렌더·LLM·네트워크 0 · **면책표 없이 하드 0**(부채 원장 증가 0 · 현행 11레인 전건 보유)."""
    wdir = os.path.join(ROOT, '.github', 'workflows')
    try:
        files = sorted(f for f in os.listdir(wdir) if f.endswith(('.yml', '.yaml')))
    except Exception as e:
        print('❌ check_push_send_checkout 디렉터리 읽기 실패(fail-closed):', e); return 1
    # ⚠ 발송기를 **직접** 부르는 워크플로만 세면 안 된다(260816 3차 실측 = 이 게이트 자신의 구멍).
    #   요약 완료 알림은 `notify_summary.sh`, 실패 알림은 `notify_fail.sh`, 화재 추적은 `fire_watch.py`처럼
    #   **중간 스크립트를 거쳐** 발송기를 부르는 레인이 실재하고, 그쪽이 오히려 다수다(실측 6종 경유 · 5레인 누락).
    #   1차 판(`push_send.py` 문자열 직접 매치)은 그 5레인을 통째로 스코프 밖에 두고 「전건 정상」이라 보고했다
    #   = 게이트가 있는데 못 보는 자리 = 이 레포가 반복해 겪는 「손 목록 드리프트」의 게이트판.
    #   → 발송기를 부르는 스크립트 집합을 **먼저 자동 수집**하고, 워크플로가 그중 하나라도 실행하면 대상에 넣는다.
    senders = set()
    for sd in ('.github/scripts', 'shared', 'scraper'):
        sdir = os.path.join(ROOT, sd)
        for dp, _dn, fn in os.walk(sdir):
            if '__pycache__' in dp:
                continue
            for name in fn:
                if not name.endswith(('.sh', '.py')) or name in ('push_send.py', 'check_refs.py', 'build_notif_icons.py'):
                    continue
                try:
                    sl = open(os.path.join(dp, name), encoding='utf-8').read().splitlines()
                except Exception:
                    continue
                if any('push_send.py' in l and not l.lstrip().startswith('#') for l in sl):
                    senders.add(name)
    bad, noicon, seen = [], [], 0
    for f in files:
        try:
            lines = open(os.path.join(wdir, f), encoding='utf-8').read().splitlines()
        except Exception as e:
            print('❌ check_push_send_checkout 읽기 실패(fail-closed): %s — %s' % (f, e)); return 1
        live = [l for l in lines if not l.lstrip().startswith('#')]
        if not (any('push_send.py' in l for l in live) or any(s in l for s in senders for l in live)):
            continue
        seen += 1
        for i, l in enumerate(lines):
            if not re.match(r'^\s*sparse-checkout:\s*\|', l) or l.lstrip().startswith('#'):
                continue
            body, base = [], None
            for cur in lines[i + 1:]:
                if not cur.strip():
                    break
                ind = len(cur) - len(cur.lstrip())
                if base is None:
                    base = ind
                if ind < base:
                    break
                body.append(cur.strip())
            if 'push' not in body:
                bad.append('%s:%d' % (f, i + 1))
            if not any(b == 'assets/brand' or b.startswith('assets/brand/') for b in body):
                noicon.append('%s:%d' % (f, i + 1))
            break
    if seen < 5:
        print('❌ check_push_send_checkout 대상 %d건 — 시그니처 드리프트 의심(fail-closed · 하한 5)' % seen); return 1
    if bad:
        print('❌ 완료 푸시 레인이 구독자 명단을 체크아웃하지 않는다(260816 실사고 = 「구독자 없음」으로 조용히 발송 생략 · 스텝은 초록):')
        for b in bad:
            print('   -', b, '→ sparse-checkout 목록에 `push` 한 줄 추가(정본 = vidl-make)')
    if noicon:
        print('❌ 완료 푸시 레인이 알림 아이콘 번들을 체크아웃하지 않는다(260727 폐기 경로 = 주소 폴백으로 조용한 회귀):')
        for b in noicon:
            print('   -', b, '→ sparse-checkout 목록에 `assets/brand` 한 줄 추가(정본 = vidl-make)')
    if bad or noicon:
        return 1
    print('✅ 완료 푸시 체크아웃 게이트 — %d개 발송 레인 전건 구독자 명단 + 아이콘 번들 보유(조용한 발송 생략·주소 폴백 회귀 0).' % seen)
    return 0


def check_push_abs_url():
    """알림 딥링크는 **절대 주소로** 나간다(260816 3차 실사고 봉합 · 운영자 「알림이 다 구 주소로 가는거 같은데」).

    ⚠ 진범 = 상대경로 + 폰 SW의 origin. `viewer/sw.js notificationclick`이 `new URL(raw, self.location.origin)`
    으로 이동 주소를 만드는데 그 origin은 **그 구독이 등록된 화면**이다. 계정 이관(260816) 전에 등록된 구독은
    전부 옛 화면 것이라(실측 = 5대 전건 26-06-19~26-07-21 = 이관 26일 전), `/?a=…`·`/thumb.html?done=…` 같은
    상대경로가 옛 화면 주소에 붙어 **알림을 눌러도 옛 화면으로 갔다**. 옛 화면은 8월 13일 배포에 멈춰 있어
    오늘 고친 것이 하나도 안 보인다 = 알림은 정상으로 뜨는데 목적지만 틀린 형태.
    ⚠ **옛 화면 SW는 코드로 못 고친다** — 그 화면이 새 저장소 커밋을 배포받지 않으므로 이미 폰에 깔린 SW가
    그대로 산다 → **서버가 절대 주소를 실어 보내는 것**만이 유효한 수단이다(절대 주소면 `new URL`이 base를
    무시한다 = 어느 화면 SW가 받아도 정본 화면으로 간다).
    ⚠ 신설 사유 = 기존 게이트가 전부 다른 축이다 — `check_canon_host` = 코드가 **부르는** 주소(스킴 붙은
    절대 주소만 · 상대경로는 술어상 대상 밖이라 이 사고를 원리적으로 못 본다) · `check_push_send_checkout` =
    푸시가 **나갈 수 있는가** · `smoke_*` = 화면 렌더 → 「알림이 **어느 화면으로 데려가는가**」는 축 자체가
    없었고, 운영자가 알림을 눌러봐야만 보였다(insta-thumb-miss·brk_misfire 동축).
    술어 3축 = ① 절대화 함수 실존(스킴 보유 시 그대로 = 이중 접두 0) ② payload 조립의 url이 그 함수 경유
    ③ `LIVE_BASE` 레버 보유(도메인이 또 바뀌어도 손잡이 1개 = `check_canon_host` 처방 관용구 계승).
    정적 · 렌더·LLM·네트워크 0 · **면책표 없이 하드 0**."""
    p = os.path.join(ROOT, '.github', 'scripts', 'push_send.py')
    try:
        src = open(p, encoding='utf-8').read()
    except Exception as e:
        print('❌ check_push_abs_url 읽기 실패(fail-closed):', e); return 1
    code = [l for l in src.splitlines() if not l.lstrip().startswith('#')]
    body = '\n'.join(code)
    bad = []
    if not re.search(r'def\s+abs_url\s*\(', body):
        bad.append('절대화 함수 abs_url 부재 — 알림이 폰 SW origin(= 그 구독이 등록된 화면)을 따라간다')
    if not re.search(r'startswith\(\s*[\'"]https://[\'"]\s*\)', body):
        bad.append('abs_url 스킴 판정 부재 — 이미 절대 주소인 호출부에 접두가 두 번 붙는다')
    if not re.search(r'"url"\s*:\s*abs_url\(', body):
        bad.append('payload 조립의 url이 abs_url 경유가 아니다 — 상대경로가 그대로 나간다(진범 그 자체)')
    if not re.search(r'LIVE_BASE\s*=\s*\(?\s*os\.environ\.get\(\s*[\'"]LIVE_BASE[\'"]', body):
        bad.append('LIVE_BASE 레버 부재 — 도메인 교체 시 코드를 다시 뒤져야 한다')
    if bad:
        print('❌ 알림 딥링크 절대 주소 게이트(260816 실사고 = 알림을 눌러도 옛 화면으로 갔다):')
        for b in bad:
            print('   -', b)
        print('   처방 = push_send.abs_url()로 감싸고 기준은 LIVE_BASE(기본 https://%s).' % _CANON_HOST)
        return 1
    print('✅ 알림 딥링크 절대 주소 게이트 — 전 알림이 정본 화면 절대 주소로 나간다(옛 화면 SW가 받아도 목적지 정본).')
    return 0


def _shell_literal_leak(src):
    """다중라인 큰따옴표 리터럴이 **중간에서 조기 종료**되는 지점을 bash 인용 문맥 그대로 훑어 찾는다.
    반환 = [(변수명, 행번호, 문맥)] · 최상위 dq 안에서만 판정하고 `$(…)`·heredoc·작은따옴표는 통째 스킵
    (그 안은 셸 문법이 아니거나 자체 인용 규칙이라 세면 위양성이 터진다 — 실측: 치환 내부 괄호 불균형을
    깊이로만 세던 1차 스캐너가 awk `'…'`·`python3 -c "…"` 7건을 오검출)."""
    def skip_sq(s, i):                      # ' … '  (bash 작은따옴표 = 이스케이프 없음)
        j = s.find("'", i + 1)
        return len(s) if j < 0 else j + 1

    def skip_dq(s, i):                      # " … "  (중첩 $(…) 가능)
        i += 1
        while i < len(s):
            c = s[i]
            if c == '\\': i += 2; continue
            if c == '"': return i + 1
            if c == '$' and s[i+1:i+2] == '(': i = skip_sub(s, i + 1); continue
            i += 1
        return len(s)

    def skip_sub(s, i):                     # $( … )  — 내부 인용·heredoc 인식(괄호 오세기 차단)
        i += 1; depth = 1
        while i < len(s) and depth:
            c = s[i]
            if c == '\\': i += 2; continue
            if c == "'": i = skip_sq(s, i); continue
            if c == '"': i = skip_dq(s, i); continue
            hd = re.match(r"<<-?\s*'?([A-Za-z_][A-Za-z0-9_]*)'?", s[i:])
            if hd:
                end = re.search(r'^\s*%s\s*$' % re.escape(hd.group(1)), s[i:], re.M)
                if end: i += end.end(); continue
            if c == '(': depth += 1
            elif c == ')': depth -= 1
            i += 1
        return i

    def skip_brace(s, i):                   # ${ … }  — 중첩 따옴표·중괄호 포함(파라미터 확장 트림 관용구)
        i += 2; depth = 1
        while i < len(s) and depth:
            c = s[i]
            if c == '\\': i += 2; continue
            if c == '"': i = skip_dq(s, i); continue
            if c == "'": i = skip_sq(s, i); continue
            if c == '{': depth += 1
            elif c == '}': depth -= 1
            i += 1
        return i

    hits = []
    # ⚠ 줄 **선두** 할당만 보면 뚫린다 — `case "$p" in *h24*) BLOCK="…` 처럼 줄 중간에서 시작하는
    #   다중라인 리터럴도 같은 사고를 낸다(킬테스트 실측: 프리셋 블록에 심은 위반을 선두 한정판이 놓쳤다).
    for m in re.finditer(r'(?:^|[\s;&|)])([A-Za-z_][A-Za-z0-9_]*)\+?="', src, re.M):
        i, dq, leak, start_ln = m.end(), True, None, src.count('\n', 0, m.end()) + 1
        nl_seen = False
        while i < len(src):
            c = src[i]
            if c == '\\': i += 2; continue
            if c == '\n':
                if not dq: break            # 문자열 밖에서 줄이 끝났다 = 할당 종료
                nl_seen = True; i += 1; continue
            if dq and c == '$' and src[i+1:i+2] == '(': i = skip_sub(src, i + 1); continue
            if dq and c == '$' and src[i+1:i+2] == '{': i = skip_brace(src, i); continue
            if c == '"':
                dq = not dq; i += 1
                if not dq:                  # 문자열이 닫혔다 — 뒤에 뭐가 오는지가 정상/사고를 가른다
                    j = i
                    while j < len(src) and src[j] in ' \t': j += 1
                    tail = src[j:j + 64]
                    # 정상 관용구 = ⓐ 구분자·개행으로 끝 ⓑ 줄연속 `\` ⓒ **다음 할당**
                    #   (`METER_SRC=ask METER_REF="$base" METER_MODEL="$MODEL" …` env-프리픽스 체인 ·
                    #    실측 70건 전부 이 형태 = 여기서 안 갈라내면 게이트가 레포를 통째로 얼린다).
                    #   사고는 닫힌 뒤가 **맨 텍스트**다(`…제목 = "이런걸` → `재능이라고 …`).
                    if (j >= len(src) or src[j] in '\n;|&)\\'
                            or re.match(r'[A-Za-z_][A-Za-z0-9_]*\+?=', tail)):
                        break               # 정상 종료 = 이 할당 끝
                    # ⓓ 한 줄 안에서 열고 닫힌 뒤 ASCII 명령어가 오는 것 = env-프리픽스 체인의 **종점**
                    #   (`… METER_EFFORT="$_eff" claude_meter 600 \`) = 정상. 리터럴이 **여러 줄에 걸친 뒤**
                    #   중간에서 닫히는 것만이 프롬프트 본문이 샌 사고다(실측 10건이 전부 이 종점 형태).
                    if not nl_seen and re.match(r'[A-Za-z_][A-Za-z0-9_./-]*(\s|$)', tail):
                        break
                    if leak is None:
                        leak = (src.count('\n', 0, i) + 1,
                                src[max(0, i - 45):i + 45].replace('\n', '⏎'))
                continue
            if not dq and c in ';|&': break  # 문자열 밖 구분자 = 할당 끝
            i += 1
        # 다중라인 리터럴일 때만 위반 — 한 줄 할당의 문자열 이어붙이기(`a="x"y`)는 정상 관용구다.
        if leak and (src.count('\n', 0, i) + 1) > start_ln:
            hits.append((m.group(1), leak[0], leak[1]))
    return hits


def check_prompt_literal_quoting():
    """다중라인 프롬프트 리터럴 = 인용 무결성 의무(하드 · 260805 실사고 `fail-2026-08-04-{1528,2211}` 봉합).
    사고 = ask.sh 프롬프트 1-3) 블록에 **이스케이프 안 된 큰따옴표**가 들어갔다(`제목 = "이런걸 …"`).
    첫 `"` 가 `prompt="` 를 닫아 뒤 텍스트가 셸 토큰이 되고(`재능이라고: command not found`), `prompt=…` 는
    그 명령의 **환경변수 프리픽스**로 흡수돼 변수 자체가 안 잡힌다 → `set -u` unbound → claude -p 에 **빈
    stdin** → "Input must be provided…" = 요약 요청 **전건 100% 실패**(요청 내용과 무관한 고정 리터럴이라
    입력을 뭘 넣어도 죽는다). ⚠ 이 사고가 조용한 이유 = **문법적으로 완전히 유효**하다 — `bash -n` 통과,
    커밋 게이트 전건 통과, 화면엔 「내용 분석 결함(입력이 비었거나 불충분)」이라 **입력 탓으로 보인다**.
    실제로 260804 세션은 이 문구를 믿고 엉뚱한 축(네이버 프레임 셸)을 봉합했고 진범은 6시간 더 살았다.
    같은 줄에서 백틱은 `\\``로 이스케이프돼 있었다 = 사람 눈이 따옴표만 놓치는 축(기계 검사가 유일한 해).
    판정 = `_shell_literal_leak`(bash 인용 문맥 정적 훑기 · 렌더·LLM·네트워크 0) · 스코프 = 파이프라인
    셸 전수 자동 발견(새 스크립트가 조용히 빠질 수 없다) · 면책 없음 = 현재 위반 0."""
    import glob as _g
    files = sorted(_g.glob(os.path.join(ROOT, '.github', 'scripts', '*.sh'))
                   + _g.glob(os.path.join(ROOT, 'shared', '*.sh')))
    if not files:
        print('❌ check_prompt_literal_quoting 대상 셸 0건 — 경로 확인(fail-closed)'); return 1
    bad = []
    for f in files:
        try:
            src = open(f, encoding='utf-8').read()
        except Exception as e:
            print('❌ check_prompt_literal_quoting 읽기 실패(fail-closed): %s — %s' % (f, e)); return 1
        for var, ln, ctx in _shell_literal_leak(src):
            bad.append((os.path.relpath(f, ROOT), ln, var, ctx))
    if bad:
        print('❌ 프롬프트 리터럴 인용 무결성 — 다중라인 문자열이 중간에서 닫혀 본문이 셸 토큰으로 샌다 %d건'
              '(= 변수 미할당 → claude 빈 stdin → 그 경로 요청 전건 실패):' % len(bad))
        for f, ln, var, ctx in bad:
            print('   · %s:%d  변수 %s' % (f, ln, var))
            print('     …%s…' % ctx)
            print('     → 본문 속 큰따옴표는 \\" 로 이스케이프(같은 블록의 백틱 \\` 관례와 동축)')
        return 1
    print('✅ 프롬프트 리터럴 인용 무결성 — 셸 %d개 다중라인 리터럴 조기 종료 0건(빈 stdin 사고 봉인).' % len(files))
    return 0


# [CF-Pages-Skip] 코얼레싱 허용 표면(운영자 260803 페이블 5인 평의회 · Q1331) — 여기 등재된 파일만 접두를 배선할 수 있다.
#   원리 = 「화면에 수 분 늦게 떠도 되는 데이터 churn」 커밋만 CF 빌드를 스킵(다음 비스킵 빌드가 tip 통째 배포 = 누적·유실 0).
#   ⚠ 금지 축(여기 없는 파일 = 전부): stamp-version(:14 skip 금지 명문 = BUILD_STAMP·live-smoke 수렴 축) ·
#     제작 산출(cards·thumb·edit·conv·voice·song·track = 'Cloudflare Pages' 체크런 완료 게이트 5종이 붙는다) ·
#     news-analyze·news-ask(queue/asks = notify_summary 240s 배포 대기 축) · scrape(15분 메트로놈 = 스킵분 신선도 바닥) ·
#     auto-pick·조기 반영(운영자 체감 즉시축). 확장 = 사유와 함께 이 목록에 1줄(평의회② 260803: 토큰은
#     [CF-Pages-Skip]만 — [CI Skip]류는 GitHub [ci skip]과 충돌 위험 = push 발화 사망).
_PAGES_SKIP_ALLOW = {
    os.path.join('.github', 'scripts', 'git_land.sh'),        # 공용 헬퍼(sns-trends·insta·fb·lucy 4워크플로) — 접두 로직 정본
    os.path.join('.github', 'workflows', 'sns-trends.yml'),   # ↓ 4개 = git_land 호출자: 접두 실배선은 헬퍼 안 · 이 파일들엔 킬스위치 env 주석 리터럴만
    os.path.join('.github', 'workflows', 'insta-fetch.yml'),
    os.path.join('.github', 'workflows', 'fb-fetch.yml'),
    os.path.join('.github', 'workflows', 'lucy-threads.yml'),
    os.path.join('.github', 'workflows', 'social-scan.yml'),
    os.path.join('.github', 'workflows', 'breaking-judge.yml'),  # 경중 grade 갱신 커밋만(조기 반영·auto-pick 줄 금지 = 아래 부정 검사)
    os.path.join('.github', 'workflows', 'metrics-rollup.yml'),
    os.path.join('.github', 'workflows', 'watchdog.yml'),
    os.path.join('.github', 'workflows', 'rate.yml'),
    os.path.join('.github', 'workflows', 'run-steps-ledger.yml'),   # 스텝 소요 원장(260808) — 착지물 = scraper/obs/run_steps.jsonl(뷰어 표면 아님 = Pages 무관 churn)
    # 쿠키 생사 감시(260804) — 착지물 = push/ 원장 + messages/ 알림. insta-fetch와 **같은 모양**(하루 2회 봇 churn +
    #   알림)이라 같은 판정: 화면에 수 분 늦게 떠도 되는 축이다(쿠키는 ~2주 주기로 죽고 운영자는 알림함을 안 놓친다).
    #   ⚠ viewer/*.json 착지 0 = 짝 게이트(check_coalesce_pair) 대상 아님 — 라이브 서빙 짝이 필요한 화면 표면을 안 만든다.
    os.path.join('.github', 'workflows', 'yt-cookie-health.yml'),
    # 받기 결과(260804) — 뷰어가 api/vidlout(빌드 우회 라이브 서빙)로 직접 읽으므로 빌드 불요 = 짝 조건 충족.
    #   받기 1건 = 최대 3판 = 커밋 3개가 CF 풀빌드 큐를 먹어 **코드 배포를 밀어내던** 축을 제거(같은 날 실측 20~40분 지연).
    #   ⚠ viewer/*.json 최상위 착지 0(중첩 vidl_out/<id>/) = check_coalesce_pair 자동발견 대상 아님 — 짝은 api/vidlout.js가 이미 담당.
    os.path.join('.github', 'workflows', 'vidl-make.yml'),
}


def check_pages_skip():
    """[CF-Pages-Skip] 오배선 차단 게이트(운영자 260803 평의회 · Q1331) — 접두가 금지 축(도장·제작 산출·뉴스 큐·메트로놈)에
    번지면 배포 보증(체크런 게이트 5종)·BUILD_STAMP 수렴·요약 알림 240s 대기가 조용히 죽는다. 판정 3축:
    ① 접두 리터럴은 _PAGES_SKIP_ALLOW 등재 파일에만 ② git_land.sh엔 킬스위치 가드(PAGES_COALESCE)가 실존
    ③ breaking-judge 안에서 접두 변수(PFX)가 금지 커밋 줄(조기 반영·auto-pick·발송 원장)에 안 붙음."""
    lit = '[CF-Pages-Skip'
    bad = []
    scan_dirs = [os.path.join(ROOT, '.github', 'workflows'), os.path.join(ROOT, '.github', 'scripts')]
    seen_allow = set()
    for d in scan_dirs:
        try:
            names = sorted(os.listdir(d))
        except Exception as e:
            print('❌ check_pages_skip 디렉터리 읽기 실패(fail-closed):', e); return 1
        for n in names:
            p = os.path.join(d, n)
            if not os.path.isfile(p):
                continue
            try:
                txt = open(p, encoding='utf-8').read()
            except Exception:
                continue
            rel = os.path.relpath(p, ROOT)
            if lit in txt:
                if rel in _PAGES_SKIP_ALLOW:
                    seen_allow.add(rel)
                else:
                    bad.append(rel + ' → 접두 금지 표면(허용 = _PAGES_SKIP_ALLOW 등재 + 사유)')
    # ② 헬퍼 가드 실존 — 접두는 항상 킬스위치(PAGES_COALESCE=0) 뒤에 있어야 한다(무조건 접두 = 롤백 1줄 계약 파기)
    gl = os.path.join(ROOT, '.github', 'scripts', 'git_land.sh')
    try:
        gtxt = open(gl, encoding='utf-8').read()
        if lit in gtxt and 'PAGES_COALESCE' not in gtxt:
            bad.append('git_land.sh → 접두에 킬스위치(PAGES_COALESCE) 가드 부재')
    except Exception as e:
        print('❌ check_pages_skip git_land.sh 읽기 실패(fail-closed):', e); return 1
    # ③ breaking-judge 금지 줄 부정 검사 — PFX 변수가 즉시축 커밋에 번지면 조용한 지연(운영자 체감 직격)
    bj = os.path.join(ROOT, '.github', 'workflows', 'breaking-judge.yml')
    try:
        for i, l in enumerate(open(bj, encoding='utf-8').read().splitlines(), 1):
            if 'git commit' in l and '${PFX}' in l and ('조기 반영' in l or 'auto-pick' in l or '발송 원장' in l):
                bad.append('breaking-judge.yml:%d → 즉시축 커밋에 접두 금지(경중 grade 갱신만 허용)' % i)
    except Exception as e:
        print('❌ check_pages_skip breaking-judge 읽기 실패(fail-closed):', e); return 1
    if bad:
        print('❌ [CF-Pages-Skip] 오배선(평의회 260803 — 도장·제작·뉴스 큐에 번지면 배포 보증·수렴·알림이 조용히 죽는다):')
        for b in bad:
            print('   -', b)
        return 1
    print('✅ [CF-Pages-Skip] 코얼레싱 게이트 — 허용 표면 %d/%d 배선 · 금지 표면 잔존 0 · 킬스위치 가드 실존.'
          % (len(seen_allow), len(_PAGES_SKIP_ALLOW)))
    return 0


def check_coalesce_pair():
    """[CF-Pages-Skip] **짝** 게이트(운영자 260803 6-4 승인 · Q1343 실사고의 기계화) — 코얼레싱의 반대 방향을 본다.
    check_pages_skip이 「접두를 어디에 달아도 되나(배선 방향)」를 지킨다면, 이 게이트는 「접두를 단 워크플로가
    착지시키는 **화면 데이터**에 라이브 서빙(빌드 우회 api)이 있나(짝 방향)」를 지킨다.
    ── 왜(실사고 260803) ── 코얼레싱은 옳은 조치지만, 스킵된 커밋의 산출물이 **정적 파일로만 서빙되면** 그 화면은
    무관한 다른 커밋이 빌드를 물 때까지 갱신이 멈춘다 = **조용한 정지**. 실측 = `viewer/tbs_data.json`(국내 커뮤니티
    21개 = 키워드 알림 국내 감시축)이 정확히 그 상태였다 — 같은 파일이 260720~26 폰 크론 사망으로 "6일간 빈 채 감시"를
    이미 겪은 재발 축(sns-trends.yml 헤더 박제)이라 눈으로 못 잡으면 또 조용히 죽는다.
    ── 판정(전부 자동 발견 = 손 목록 0) ──
    ① 코얼레싱 워크플로(_PAGES_SKIP_ALLOW ∩ workflows)의 `git_land.sh` 호출줄에서 `viewer/*.json` 인자를 뽑고
    ② 그중 **뷰어가 실제로 fetch하는 것**만 화면 표면으로 채택(내부 상태 파일은 자연 제외 = 위양성 0)
    ③ 그 표면이 `functions/api/*.js` 어딘가에서 `viewer/<이름>.json`으로 서빙되는지 대조 → 없으면 rc=1.
    확장할 때 이 게이트가 저절로 따라온다(코얼레싱 대상 1개 추가 = 짝 배선 강제)."""
    wdir = os.path.join(ROOT, '.github', 'workflows')
    vdir = os.path.join(ROOT, 'viewer')
    fdir = os.path.join(ROOT, 'functions', 'api')
    for d in (wdir, vdir, fdir):
        if not os.path.isdir(d):
            print('❌ check_coalesce_pair 경로 없음(fail-closed):', d); return 1
    # ① 코얼레싱 워크플로가 git_land로 착지시키는 viewer/*.json
    landed = {}
    for rel in sorted(_PAGES_SKIP_ALLOW):
        if not rel.startswith(os.path.join('.github', 'workflows')):
            continue
        p = os.path.join(ROOT, rel)
        try:
            txt = open(p, encoding='utf-8').read()
        except Exception:
            continue   # 파일 부재 = check_pages_skip 관할(중복 실패 안 냄)
        for line in txt.splitlines():
            if 'git_land.sh' not in line or line.lstrip().startswith('#'):
                continue
            for m in re.finditer(r'viewer/([A-Za-z0-9_\-]+)\.json', line):
                landed.setdefault(m.group(1) + '.json', set()).add(os.path.basename(rel))
    if not landed:
        print('✅ [CF-Pages-Skip] 짝 게이트 — 코얼레싱 워크플로의 viewer JSON 착지 0건(대상 없음).'); return 0
    # ② 뷰어가 실제로 fetch하는 표면만 채택(내부 상태 파일 제외 = 자동)
    vtxt = ''
    for n in sorted(os.listdir(vdir)):
        if n.endswith('.html'):
            try:
                vtxt += open(os.path.join(vdir, n), encoding='utf-8').read()
            except Exception:
                pass
    if not vtxt:
        print('❌ check_coalesce_pair 뷰어 HTML 읽기 실패(fail-closed)'); return 1
    # ③ functions/api 서빙 대조
    # ⚠ 주석은 걷어낸다 — 안 그러면 **서빙을 지워도 주석에 남은 경로**가 게이트를 통과시킨다(260803 신설 당일 자기시험 실측:
    #   FILES 1행을 주석 처리했는데 rc=0으로 새어나감 = 게이트가 있으나 마나였던 상태). `(?<!:)//` = `https://` 보호.
    atxt = ''
    for n in sorted(os.listdir(fdir)):
        if n.endswith('.js'):
            try:
                raw = open(os.path.join(fdir, n), encoding='utf-8').read()
            except Exception:
                continue
            atxt += '\n'.join(re.sub(r'(?<!:)//.*$', '', l) for l in raw.splitlines())
    # ③-0 **라우터 도달성**(260803 평의회 8인 중 6인 독립 지목 P0의 기계화) — FILES 화이트리스트에 키를 늘려도
    #   key 산출식이 하드코딩 삼항(`get('f') === 'brief' ? 'brief' : 'trends'`)이면 새 키가 **도달 불가 사문**이 되고,
    #   요청은 조용히 기본 파일을 200으로 받는다 → 엉뚱한 파일이 소비자 유효성 검사를 통과해 **정적 폴백까지 차단**(빈 코퍼스 확정).
    #   구 게이트는 문자열 등재만 봐서 그 죽은 라우트를 '서빙 보유'로 인증했다 = 게이트가 사고를 승인한 축.
    #   계약 = FILES류 맵을 가진 api 파일은 **실조회**(`hasOwnProperty` 또는 `FILES[` 인덱싱)로 라우팅해야 한다.
    _dead_route = False
    bad = []
    for n in sorted(os.listdir(fdir)):
        if not n.endswith('.js'):
            continue
        try:
            raw = open(os.path.join(fdir, n), encoding='utf-8').read()
        except Exception:
            continue
        code = '\n'.join(re.sub(r'(?<!:)//.*$', '', l) for l in raw.splitlines())
        m = re.search(r'const\s+FILES\s*=\s*\{(.*?)\n\}', code, re.S)
        if not m:
            continue
        keys = set(re.findall(r'^\s*([A-Za-z_][A-Za-z0-9_]*)\s*:', m.group(1), re.M))
        if len(keys) <= 1:
            continue
        if not re.search(r'hasOwnProperty\.call\(\s*FILES|FILES\s*\[', code):
            bad.append('%s → FILES 키 %d개인데 라우터가 실조회가 아님(하드코딩 분기 = 새 키 도달 불가 사문 · 260803 P0)' % (n, len(keys)))
            _dead_route = True
    surf = []
    for name, wfs in sorted(landed.items()):
        # 표면 판정 = **인용 리터럴**(`'<파일>'` / `'<파일>?…'`)이 뷰어에 있는가.
        #   ⚠ `fetch(` 직전 매칭으로 하면 **자기무력화**한다 — 이 게이트가 시킨 처방(api 우선 → 정적 폴백 루프)을 적용하는 순간
        #   URL이 배열 원소가 되어 `fetch(u)` 형태로 바뀌고, 그러면 그 표면이 감시망에서 사라져 **나중에 서빙을 지워도 통과**한다
        #   (260803 신설 당일 실측: 처방 적용 후 탐지 3종 → 1종으로 붕괴). 인용 리터럴 기준은 루프·배열·템플릿 전부 커버하고,
        #   산문 주석의 맨 파일명(앞이 공백·`/`)은 인용부호가 없어 자연 제외 = 위양성 억제.
        if not re.search(r'''['"`]''' + re.escape(name) + r'''[?'"`&]''', vtxt):
            continue   # 화면이 안 읽는 내부 산출물 = 비대상(자동 제외)
        surf.append(name)
        if _dead_route:
            continue   # 라우터가 죽어 있으면 아래 등재 검사는 무의미(위에서 이미 실패 처리)
        if not re.search(r'''['"`]viewer/''' + re.escape(name) + r'''['"`]''', atxt):   # 인용 리터럴만 인정(FILES 등재 형태 · 산문 언급 불인정)
            bad.append('%s (착지: %s) → 라이브 서빙 없음 = 코얼레싱 스킵 시 화면 갱신 정지'
                       % (name, ','.join(sorted(wfs))))
    if bad:
        print('❌ [CF-Pages-Skip] 짝 부재(260803 실사고 = tbs_data 국내 감시축 조용한 정지) — 코얼레싱 대상은 라이브 서빙이 필수:')
        for b in bad:
            print('   -', b)
        print('   처방 = functions/api/<축>.js FILES 화이트리스트에 1행 + 뷰어 로더를 api 우선 → 정적 폴백으로(정본 = functions/api/candidates.js·trends.js)')
        return 1
    print('✅ [CF-Pages-Skip] 짝 게이트 — 코얼레싱 착지 화면 표면 %d종(%s) 전부 라이브 서빙 보유.'
          % (len(surf), ', '.join(surf)))
    return 0


_CATKW_BUCKETS = ('국제', '경제', '문화', '테크', '정치', '사회')


def _parse_cat_kw(text):
    """CAT_KW={...} 블록 → 버킷별 토큰집합 (py 큰따옴표·js 작은따옴표 공용·//·# 주석 제거)."""
    m = re.search(r'CAT_KW\s*=\s*\{(.*?)\n\s*\}\s*;?', text, re.S)
    if not m:
        return None
    body = re.sub(r'//[^\n]*', '', m.group(1))
    body = re.sub(r'#[^\n]*', '', body)
    out = {}
    for b in _CATKW_BUCKETS:
        bm = re.search(r'(?:"%s"|%s)\s*:\s*\[(.*?)\]' % (b, b), body, re.S)
        out[b] = set(re.findall(r"""['"]([^'"]+)['"]""", bm.group(1))) if bm else set()
    return out


def check_cat_kw():
    """CAT_KW 카테고리 키워드사전 py(to_candidates.py) ↔ js(viewer/index.html) 정합 하드게이트.
    수동 미러라 매 세션 드리프트(같은 단어가 두 엔진서 다른/없는 버킷)가 누적 — 분류 오분류 재발의
    근본(260628 C9 분신술 10인). 버킷별 토큰집합 일치 + 버킷충돌(같은 토큰·다른 버킷) 둘 다 검사."""
    rc = 0
    try:
        py = open(os.path.join(ROOT, 'scraper', 'to_candidates.py'), encoding='utf-8').read()
        js = open(os.path.join(ROOT, 'viewer', 'index.html'), encoding='utf-8').read()
    except Exception as e:
        print('⚠️ check_cat_kw 스킵(파일):', e); return 0
    P = _parse_cat_kw(py); J = _parse_cat_kw(js)
    if P is None or J is None:
        print('⚠️ check_cat_kw 스킵(CAT_KW 블록 못 찾음 — py=%s·js=%s)' % (P is not None, J is not None)); return 0
    bad = []
    for b in _CATKW_BUCKETS:
        onlyP, onlyJ = P[b] - J[b], J[b] - P[b]
        if onlyP: bad.append('[%s] py에만: %s' % (b, ', '.join(sorted(onlyP))))
        if onlyJ: bad.append('[%s] js에만: %s' % (b, ', '.join(sorted(onlyJ))))
    pmap, jmap = {}, {}
    for b in _CATKW_BUCKETS:
        for t in P[b]: pmap.setdefault(t, set()).add(b)
        for t in J[b]: jmap.setdefault(t, set()).add(b)
    for t in set(pmap) & set(jmap):
        if pmap[t] != jmap[t]:
            bad.append("버킷충돌 '%s': py=%s js=%s" % (t, sorted(pmap[t]), sorted(jmap[t])))
    if bad:
        print('❌ CAT_KW py↔js 드리프트(C9 게이트 — 키워드 한쪽만 고침=분류 오분류 근본):')
        for b in bad: print('  -', b)
        rc = 1
    else:
        print('✅ CAT_KW py↔js 정합 — 6버킷 토큰집합 일치·버킷충돌 0.')
    return rc


_ISS_REGEX_NAMES = ('BJ_CRASH', 'BJ_MKT', 'BJ_HEAD', 'BJ_PR')

def check_issue_badge_parity():
    """⚡이슈 배지 게이트 viewer(issCross) ↔ build-viewer(issEligible) 규칙 동일 하드게이트(260702 · 10인 검증7).
    배지 규칙이 두 파일에 이중 구현(수집함=렌더타임·피드=빌드타임)이라 한쪽만 고치면 수집함↔피드 배지
    드리프트 — 주석 계약을 기계로 강제(check_cat_kw 선례). 검사: ISS_CROSS_MIN 값 + BJ_* 4종 정규식
    바이트 동일 + grade3 우회(`=== 3`·cross 8) 마커 양쪽 존재 + badgeJunk 조합식(!BJ_CRASH 면제 포함)
    + issGrade null 관용(== null 유지 — strict ≥2 회귀 차단) 대조(분신술 10인 감사 확장·260710).
    ⚠️ fail-closed: 파일을 못 읽으면 통과 아닌 실패(게이트가 조용히 무력화되던 fail-open 봉합·260710)."""
    rc = 0
    try:
        js = open(os.path.join(ROOT, 'viewer', 'index.html'), encoding='utf-8').read()
        bv = open(os.path.join(ROOT, 'build-viewer.mjs'), encoding='utf-8').read()
    except Exception as e:
        print('❌ check_issue_badge_parity 파일 읽기 실패(fail-closed — 게이트 무력화 방지):', e); return 1
    bad = []
    def _iss_min(src, tag):
        m = re.search(r'const ISS_CROSS_MIN = (\d+);', src)
        if not m: bad.append('%s: ISS_CROSS_MIN 선언 못 찾음' % tag); return None
        return m.group(1)
    a, b = _iss_min(js, 'viewer'), _iss_min(bv, 'build-viewer')
    if a and b and a != b: bad.append('ISS_CROSS_MIN 불일치: viewer=%s build-viewer=%s' % (a, b))
    for name in _ISS_REGEX_NAMES:
        ma = re.search(r'const %s = /(.+?)/;' % name, js)
        mb = re.search(r'const %s = /(.+?)/;' % name, bv)
        if not ma or not mb:
            bad.append('%s 정규식 선언 못 찾음(viewer=%s·build=%s)' % (name, bool(ma), bool(mb))); continue
        if ma.group(1) != mb.group(1):
            bad.append('%s 정규식 드리프트:\n      viewer: /%s/\n      build : /%s/' % (name, ma.group(1), mb.group(1)))
    for src, tag in ((js, 'viewer issCross'), (bv, 'build-viewer issEligible')):
        line = re.search(r'const issCross = .+|return \(cr >= ISS_CROSS_MIN.+', src)
        if not line or '=== 3' not in line.group(0) or '>= 8' not in line.group(0):
            bad.append('%s: grade3 우회(=== 3 · cross>=8) 마커 부재/드리프트' % tag)
    # badgeJunk 조합식 대조(260710) — 정규식 4종이 바이트 동일해도 조합((MKT && !CRASH) || HEAD || PR)이
    # 한쪽만 바뀌면(예: !BJ_CRASH 면제 삭제) 기존 검사는 초록 = 사각. 불리언 식 자체를 추출해 대조.
    mj = re.search(r"const badgeJunk = c => \{ const t = c\.title \|\| ''; return (.+?); \};", js)
    mb = re.search(r'const badgeJunk = t => (.+?);', bv)
    if not mj or not mb:
        bad.append('badgeJunk 조합식 추출 실패(viewer=%s·build=%s) — 선언 형태 변경 시 이 게이트도 갱신' % (bool(mj), bool(mb)))
    elif mj.group(1) != mb.group(1):
        bad.append('badgeJunk 조합식 드리프트:\n      viewer: %s\n      build : %s' % (mj.group(1), mb.group(1)))
    # issGrade null 관용 대조(260710) — 뷰어 주석 "strict ≥2 금지" 계약의 기계 강제(한쪽만 strict로 바꾸면 배지 드리프트).
    if not re.search(r'const issGrade = c => c\.grade == null \|\| c\.grade >= 2;', js):
        bad.append('viewer issGrade: null 관용식(c.grade == null || c.grade >= 2) 부재/변형 — strict 회귀 의심')
    if not re.search(r'g == null \|\| g >= 2', bv):
        bad.append('build-viewer issEligible: null 관용식(g == null || g >= 2) 부재/변형 — strict 회귀 의심')
    if bad:
        print('❌ 이슈 배지 게이트 viewer↔build-viewer 드리프트(한쪽만 수정 = 수집함↔피드 배지 불일치):')
        for x in bad: print('  -', x)
        rc = 1
    else:
        print('✅ 이슈 배지 패리티 — ISS_CROSS_MIN·BJ_* 4종 정규식·grade3 우회 = viewer↔build-viewer 동일.')
    return rc


_FORCE_PAIR_NAMES = (   # to_candidates.py ↔ viewer/index.html articleCat "바이트 동기" 주석 계약 전수(260704 기계 승격)
    'POL_FORCE_RE', 'CULTURE_FORCE_RE', 'INTL_FORCE_RE', 'STOCK_FORCE_RE', 'POL_TITLE_RE',
    'CRIME_OVERRIDE_RE', 'JUDICIAL_OVERRIDE_RE', 'AMBIG_ARTIST_RE', 'MUSIC_CTX_RE',
    'ECON_CTX_RE', 'ENT_NAME_RE', 'ECON_HINT_RE', 'LOCALGOV_RE', 'POL_DISPUTE_RE',
    'POL_OVERRIDE_RE', 'SPORTS_MEDIA_RE', 'OSEN_RE')

def check_force_parity():
    """카테고리 강마커·오버라이드 정규식 py(to_candidates) ↔ js(viewer articleCat) 바이트 동기 하드게이트(260704).
    17쌍 전부 주석으로만 '바이트 동기' 계약이던 것을 기계로 강제(check_cat_kw C9·issue_badge 선례) —
    한쪽만 고치면 수집 데이터(cat)와 화면 라벨(articleCat)이 갈라져 오분류가 화면·데이터 따로 남(송성문 MLB 국제 오분류 교정 260704 계기)."""
    rc = 0
    try:
        py = open(os.path.join(ROOT, 'scraper', 'to_candidates.py'), encoding='utf-8').read()
        js = open(os.path.join(ROOT, 'viewer', 'index.html'), encoding='utf-8').read()
    except Exception as e:
        print('⚠️ check_force_parity 스킵(파일):', e); return 0
    bad = []
    for name in _FORCE_PAIR_NAMES:
        mp = re.search(r'%s = re\.compile\(r"(.+?)"[,)]' % name, py)
        mj = re.search(r'const %s = /(.+?)/[a-z]*;' % name, js)
        if not mp or not mj:
            bad.append('%s 선언 못 찾음(py=%s·js=%s)' % (name, bool(mp), bool(mj))); continue
        if mp.group(1) != mj.group(1):
            bad.append('%s 드리프트: py %d자 ↔ js %d자' % (name, len(mp.group(1)), len(mj.group(1))))
    if bad:
        print('❌ 강마커 py↔js 드리프트(한쪽만 수정 = 데이터 cat ↔ 화면 articleCat 불일치):')
        for x in bad: print('  -', x)
        rc = 1
    else:
        print('✅ 강마커 패리티 — FORCE·오버라이드 17쌍 py↔js 바이트 동일.')
    return rc


def check_k_models():
    """/k 모델·설정 3면 패리티 하드게이트(개편 P1 · 260710 스키마 v2). 모델 id와 설정 축·칩 값이
    {viewer/k.html K_MODELS·K_VALS ↔ functions/api/k.js K_MODELS·K_SET ↔ apps/k/01_모델프로필_영상엔진.md 절}
    3곳에 이중·삼중 구현 — 한쪽만 고치면 api 화이트리스트가 칩 값을 *조용히* 버려 설정 무시(무성 유실)
    또는 프로필 없는 모델로 분기(k-make 오동작). check_issue_badge_parity 선례의 /k판.
    ⚠️ 파싱 포맷 규약(감사8): 모델 id = 소문자 영숫자만 · 프로필 절 헤더 = `## <id> —`(em-dash — 하이픈도 허용) ·
    k.html `const K_VALS = {…\\n};`(닫기 0칸)·api `const K_SET = {…\\n  };`(닫기 2칸) 리터럴 구조 유지 ·
    칩 값에 `]`·작은따옴표 금지(정규식 절단). 구조를 리팩터하면 이 게이트 정규식도 동반 갱신."""
    rc = 0
    try:
        kh = open(os.path.join(ROOT, 'viewer', 'k.html'), encoding='utf-8').read()
        aj = open(os.path.join(ROOT, 'functions', 'api', 'k.js'), encoding='utf-8').read()
        pf = open(os.path.join(ROOT, 'apps', 'k', '01_모델프로필_영상엔진.md'), encoding='utf-8').read()
    except Exception as e:
        # fail-closed(감사7·8): 이 3파일은 /k 모델 분기의 하드 의존 — 부재/리네임 = 게이트 무성 무력화가 아니라 커밋 차단
        print('❌ /k 모델·설정 패리티: 필수 파일 못 엶(부재/리네임?) —', e); return 1
    bad = []
    # 모델 id 3면: k.html {id:'…'} · api ['…',…] · 프로필 '## id —'
    m_html = set(re.findall(r"\{ id: '([a-z0-9]+)'", kh))
    m_api_m = re.search(r"const K_MODELS = \[([^\]]*)\]", aj)
    m_api = set(re.findall(r"'([a-z0-9]+)'", m_api_m.group(1))) if m_api_m else set()
    m_doc = set(re.findall(r"^## ([a-z0-9]+) [—-]", pf, re.M))
    if not (m_html and m_api and m_doc):
        bad.append('모델 선언 못 찾음(k.html=%d·api=%d·프로필=%d)' % (len(m_html), len(m_api), len(m_doc)))
    elif not (m_html == m_api == m_doc):
        bad.append('모델 id 드리프트: k.html=%s · api=%s · 프로필=%s' % (sorted(m_html), sorted(m_api), sorted(m_doc)))
    # 설정 축·칩 2면: k.html K_VALS ↔ api K_SET (문자 하나만 달라도 api가 그 칩 값을 무성 폐기)
    m_vals = re.search(r"const K_VALS = \{(.*?)\n\};", kh, re.S)
    ax_html = {k: re.findall(r"'([^']+)'", vals) for k, vals in re.findall(r"'([^']+)': \[([^\]]*)\]", m_vals.group(1))} if m_vals else {}
    m_set = re.search(r"const K_SET = \{(.*?)\n  \};", aj, re.S)
    ax_api = {k: re.findall(r"'([^']+)'", vals) for k, vals in re.findall(r"'([^']+)': \[([^\]]*)\]", m_set.group(1))} if m_set else {}
    if not ax_html or not ax_api:
        bad.append('설정 축 선언 못 찾음(k.html=%d·api=%d)' % (len(ax_html), len(ax_api)))
    elif ax_html != ax_api:
        keys = set(ax_html) | set(ax_api)
        for k in sorted(keys):
            if ax_html.get(k) != ax_api.get(k):
                bad.append('축 [%s] 드리프트: k.html=%s · api=%s' % (k, ax_html.get(k), ax_api.get(k)))
    if bad:
        print('❌ /k 모델·설정 패리티 게이트:')
        for b in bad: print('   -', b)
        rc = 1
    else:
        print('✅ /k 모델·설정 패리티 — 모델 id 3면(k.html·api·프로필)·축/칩 2면 동일(%d모델·%d축).' % (len(m_html), len(ax_html)))
    return rc


_INPUT_RE = re.compile(r'<input\b[^>]*>', re.I)
_AC_NEED = ('autocomplete', 'autocapitalize', 'autocorrect', 'spellcheck')

def check_autocomplete():
    """평문 텍스트 입력칸 = OS 자동완성 끔 4종 세트 하드 게이트(§🎨 · 운영자 260628).
    편집가능 <input type=text|search>가 autocomplete/autocapitalize/autocorrect/spellcheck 중 하나라도
    빠지면 rc=1 → 모바일 OS가 🔑비번·💳카드·📍주소 자동완성 바를 붙여 입력 번잡(운영자 실측 = 썸네일 '부제').
    제외: readonly/disabled/hidden(표시 전용 = 자동완성 대상 아님)·기타 type."""
    rc = 0
    for rel in VIEWERS_ALL:   # Q169 뷰어 목록 SSOT 상수화 — nb·sb 동반 편입
        try:
            s = open(os.path.join(ROOT, rel), encoding='utf-8').read()
        except Exception:
            continue
        for m in _INPUT_RE.finditer(s):
            tag = m.group(0)
            tl = tag.lower()
            tm = re.search(r'type\s*=\s*["\']?(\w+)', tl)
            typ = tm.group(1) if tm else 'text'   # type 생략 = text
            if typ not in ('text', 'search'):
                continue
            if 'readonly' in tl or 'disabled' in tl:
                continue
            miss = [n for n in _AC_NEED if n not in tl]
            if miss:
                ln = s[:m.start()].count('\n') + 1
                print('❌ 자동완성 4종 누락 — %s:%d (%s 빠짐) → autocomplete/autocapitalize/autocorrect/spellcheck off 추가(§🎨)'
                      % (rel, ln, '·'.join(miss)))
                rc = 1
    if rc == 0:
        print('✅ 자동완성 게이트 — 편집가능 text/search 입력칸 전부 OS 자동완성 끔 4종 세트.')
    return rc


# ── URL 입력칸 placeholder 단일 문법 게이트(CII 「URL 입력칸」 행 · 운영자 260801 "예시 문구 없어도 될듯") ──
#   type=url 입력칸의 placeholder는 `https://…` 하나로 고정. 뒤에 안내 산문을 붙이면(구 askLink
#   "https://… — 기사면 원문으로, 영상·음성이면 전사해서 활용" 류) 빈 칸이 설명문으로 붐빈다 = §🎨 e 위반.
#   부연 = title 툴팁 / 판정·상태 = 입력 후 상태줄(#askLinkSt·#dgSelRow)이 낸다.
#   면책 = 도먼트(hidden) 행이라 라이브 0인 칸만. 신규 면책은 사유와 함께 여기 1줄(산탄 금지).
_URL_PH = 'https://…'
_URL_PH_EXEMPT = {
    ('viewer/edit.html', 'url'),   # .srcwrap 도먼트(운영자 260728 "Contents 하위 없애줘" · hidden) = 화면 미노출 + 「≤2GB」 상한 고지가 딴 데 없음
}

# ── 「모든 텍스트 입력창 = 클립」 공식 게이트(운영자 260803 "모든 텍스트 입력창에는 (복사·붙여넣기·지우개가)
#   붙어있어야돼 · 공식처럼가야함") ─────────────────────────────────────────────────────────────
#   부품 정본 = viewer/nm-clip.js(+nm-clip.css) — 상속 = 뷰어 head 2줄 · 신규 칸 = attachCopyPaste(el, true) 1줄.
#   이 게이트가 없으면 새 입력칸이 조용히 클립 없이 태어난다(260803 실측 = 전수 감사 51칸 중 30칸 누락 · 음원
#   탭은 6칸 전멸이었다). 표면·문법이 갈려도(attachCopyPaste / .scnclip / .urlclip 3문법 병존) 배선 흔적으로 본다.
#   면제 = ⓐ 숫자칩(값 선택 UI · 생김새가 칩이라 클립 비대상) ⓑ PIN(잠금 입력) 뿐 — 늘리려면 사유와 함께 1줄.
_CLIP_EXEMPT_CLS = ('geni-ar-in', 'rsz-ar-in', 'opa-in', 'pin-in-h')   # N:N 비율칩·OPA 값칩·PIN 칸
_CLIP_EXEMPT_ID = {
    ('viewer/index.html', 'pinInput'),   # 발행본 잠금 PIN 표시칸(readonly = 붙여넣기 대상 아님)
    ('viewer/index.html', 'pubPin'),     # 발행본 PIN 입력(숫자 키패드 · 클립보드 경유 = 잠금 취지에 반함)
}
_CLIP_WIRE = ('attachCopyPaste', 'scnclip', 'urlclip', 'askclip', 'iobtn')
_TA_RE = re.compile(r'<textarea\b[^>]*>', re.I)

def _clip_wired(s, rel, tag, pos, ident, cls):
    """이 입력칸에 클립이 배선돼 있나 — 3문법 공통 판정.
       ① 선언 직후 400자 안 클립 버튼 마크업(.scnclip/.urlclip 형제 문법)
       ② id가 클립 배선 줄에 등장(attachCopyPaste($('#id')) · 배열 forEach 리터럴)
       ③ id가 없으면 부모 래퍼 class 토큰이 클립 배선 줄에 등장(k .dialwrap textarea 선택자 부착)"""
    near = s[pos:pos + 400]
    if any(w in near for w in ('scnclip', 'urlclip', 'askclip', 'iobtn')):
        return True
    for ln in s.split('\n'):
        if not any(w in ln for w in _CLIP_WIRE):
            continue
        if ident and ("'" + ident + "'" in ln or '"' + ident + '"' in ln or '#' + ident in ln):
            return True
        if not ident:
            head = s[max(0, pos - 300):pos]
            for tok in re.findall(r'class="([^"]+)"', head):
                for t in tok.split():
                    if len(t) > 3 and t in ln:
                        return True
    return False

def check_clip_coverage():
    rc = 0
    n_ok = n_ex = 0
    for rel in VIEWERS_ALL + ('viewer/tr.html',):
        try:
            s = open(os.path.join(ROOT, rel), encoding='utf-8').read()
        except Exception:
            continue
        decls = [(m.start(), m.group(0), 'input') for m in _INPUT_RE.finditer(s)]
        decls += [(m.start(), m.group(0), 'textarea') for m in _TA_RE.finditer(s)]
        for pos, tag, kind in decls:
            # 정적 HTML 선언만 대상 — <script> 안 문자열(템플릿 리터럴로 그리는 동적 칸)은 제외한다.
            #   ⚠ 안 빼면 클립 부품 자신의 폴백 입력칸(.pastefb-ta)까지 잡아 「클립에 클립을 붙여라」가 된다(260803 실측).
            #   동적 생성 칸은 생성부에서 attachCopyPaste를 부르는 게 계약(정적 스캔 밖 = 별도 축).
            if s.rfind('<script', 0, pos) > s.rfind('</script>', 0, pos):
                continue
            tl = tag.lower()
            if kind == 'input':
                tm = re.search(r'type\s*=\s*["\']?(\w+)', tl)
                typ = tm.group(1) if tm else 'text'
                if typ not in ('text', 'url', 'search'):
                    continue
            im = re.search(r'\bid\s*=\s*["\']([^"\']+)', tag)
            ident = im.group(1) if im else ''
            cm = re.search(r'\bclass\s*=\s*["\']([^"\']*)', tag)
            cls = cm.group(1) if cm else ''
            if any(c in cls for c in _CLIP_EXEMPT_CLS) or (rel, ident) in _CLIP_EXEMPT_ID:
                n_ex += 1
                continue
            if _clip_wired(s, rel, tag, pos, ident, cls):
                n_ok += 1
                continue
            ln = s[:pos].count('\n') + 1
            print('❌ 텍스트 입력칸에 클립 없음 — %s:%d <%s%s> → attachCopyPaste(el, true) 부착'
                  '(부품 = nm-clip.js/css 2줄 상속 · 운영자 260803 "모든 텍스트 입력창에 · 공식처럼")'
                  % (rel, ln, kind, (' #' + ident) if ident else ''))
            rc = 1
    if rc == 0:
        print('✅ 입력칸 클립 게이트 — 텍스트 입력칸 %d개 전부 클립 보유(면제 %d = 숫자칩·PIN · 부품 SSOT = nm-clip.js/css).' % (n_ok, n_ex))
    return rc


# ── 스튜디오 텍스트 입력칸 정본 게이트(운영자 260804 "게이트 ㄱㄱ") ─────────────────────────────
#   ⚠ 신설 사유 = 같은 칸이 **하루에 세 번** 갈렸다(활자 → 박스 → 창 크기). 셋 다 정적 게이트를 그냥 통과했고
#   운영자 눈이 유일한 검출기였다 — 기존 게이트는 「클립이 붙었나」(check_clip_coverage)·「자동완성을 껐나」
#   (check_autocomplete)만 보고 **「그 칸이 정본 활자·박스·창 크기로 태어났나」는 축 자체가 없었다**.
#   계약 3축:
#     ⓐ 값 동일성  — 정본 원천(thumb.html 입력칸 블록) ↔ SSOT(nm-input.css `.nmin`) 가 축별로 같은 값.
#                     ⚠ min-height만 예외 = SSOT는 **3줄 정본**(thumb `.covrow textarea` 104)을 쓴다(운영자 260804
#                       "1줄 아니면 3줄임") — 그래서 thumb 전역 96이 아니라 covrow 104와 대조한다.
#     ⓑ 배선       — 스튜디오 텍스트칸이 `.nmin` 보유(tr = 문서 전체가 스튜디오 폼 = 전수 · 셸(index)은 계약 id만).
#                     + 여러 줄 칸에 구 칩 문법(`.geni-in`) 부활 금지 = 260804 드리프트의 그 모양.
#     ⓒ 높이 재선언 0 — `.nmin` 셀렉터에 height/min-height 재선언 금지 + `.nmin` textarea의 rows는 3(1줄 아니면 3줄).
#   면제 = check_clip_coverage와 같은 경계(_CLIP_EXEMPT_CLS 숫자칩·PIN) 재사용 = 손 목록 이중화 0.
_INCANON_SSOT = 'viewer/nm-input.css'
_INCANON_SRC = 'viewer/thumb.html'
_INCANON_WIRED = ('viewer/tr.html', 'viewer/index.html')
_INCANON_IDS = {   # 셸 문서(뉴스 앱 동거)라 전수 스캔이 부적격한 표면의 계약 칸 — 늘리려면 사유와 함께 1줄
    ('viewer/index.html', 'geniWish'),   # AI 생성 「내용」 = 260804 활자·박스·창 3연속 드리프트의 그 칸
}
_INCANON_KEYS = ('width', 'padding', 'background', 'border', 'border-radius', 'color', 'font', 'font-size')


def _css_decls(block):
    """CSS 블록 본문 → {속성: 값} — 주석 제거 후 최상위 세미콜론 분해(값 안 rgba(…) 콤마 무해)."""
    body = re.sub(r'/\*.*?\*/', '', block, flags=re.S)
    out = {}
    for d in body.split(';'):
        if ':' not in d:
            continue
        k, v = d.split(':', 1)
        out[k.strip().lower()] = ' '.join(v.split())
    return out


def _rule_body(css, selector):
    """선언 순서상 **첫** 매치 규칙의 본문(정본 블록은 파일당 1개 = 첫 매치로 충분).
    ⚠ 주석을 **먼저** 걷는다 — 이 레포 주석은 `.covrow textarea{min-height:104px}` 처럼 중괄호를 인용해서
      안 걷으면 규칙 경계가 통째로 어긋난다(260804 실측 = 첫 구현이 정본 블록을 못 찾았다)."""
    flat = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    for m in re.finditer(r'([^{}]+)\{([^{}]*)\}', flat):
        if selector in [x.strip() for x in m.group(1).split(',')]:
            return m.group(2)
    return None


def _nmin_rules(s):
    """`.nmin`을 품은 CSS 규칙 → [(선택자, 본문, 시작offset)] · 구 정규식의 **동치 치환**.

    ⚠ 왜 정규식을 걷어냈나(운영자 260804 「아이디어 ㄱㄱ」 = 게이트 시간 최적화):
      구판 `([^{}\\n]*\\.nmin[^{}]*)\\{([^{}]*)\\}` 는 1.85MB `viewer/index.html`에서 **17.9초**를 썼다
      (게이트 77개 총 37.5초 중 **48.9%가 이 한 줄**). 원인 = `[^{}\\n]*`가 매 위치에서 줄 끝까지 먹고
      `.nmin`을 찾아 되짚는 백트래킹 — 파일이 커질수록 제곱으로 는다.
      치환 = `.nmin` **리터럴 스캔을 먼저** 돌려 후보를 O(매치수)로 줄이고 각 후보에서만 규칙 경계를 판정한다.
      의미는 구판과 동일하게 맞췄다 = ⓐ `.nmin`↔`{` 사이에 `}` 없음(첫 `{`라 `{`도 없음)
      ⓑ 본문에 `{` 없음 ⓒ 선택자 시작 = `.nmin`에서 뒤로 `{`·`}`·개행 만날 때까지 ⓓ 같은 `{`는 1회(비중첩).
      실증 = 10파일(index·tr·thumb·edit·sb·k·song·vd·ly·nm-input.css) 구↔신 결과 **튜플 단위 전건 동일**,
      17.927s → 0.002s.
    """
    out, seen = [], set()
    i = s.find('.nmin')
    while i != -1:
        j = s.find('{', i)
        if j != -1 and j not in seen and '}' not in s[i + 5:j]:
            k = s.find('}', j + 1)
            if k != -1 and '{' not in s[j + 1:k]:
                p = i
                while p > 0 and s[p - 1] not in '{}\n':
                    p -= 1
                seen.add(j)
                out.append((s[p:j], s[j + 1:k], p))
        i = s.find('.nmin', i + 5)
    return out


def check_input_canon():
    rc = 0
    try:
        ssot = open(os.path.join(ROOT, _INCANON_SSOT), encoding='utf-8').read()
        src = open(os.path.join(ROOT, _INCANON_SRC), encoding='utf-8').read()
    except Exception as e:
        print('❌ 스튜디오 입력칸 정본 게이트 — 정본/SSOT 파일 열기 실패:', e)
        return 1

    # ⓐ 값 동일성 — 정본 원천 블록 ↔ SSOT `.nmin`
    # 앵커 = `input[type=number]` — 같은 파일의 활자 상속 강제 블록(`button, input, textarea, select {…}`)이
    # 문서 앞쪽에 있어 `select`로 잡으면 그 빈 블록이 첫 매치로 걸린다(260804 실측). 이 앵커는 정본 블록에만 있다.
    src_box = _rule_body(src, 'input[type=number]')
    ssot_box = _rule_body(ssot, '.nmin')
    if src_box is None or ssot_box is None:
        print('❌ 스튜디오 입력칸 정본 게이트 — 정본 블록(thumb `…, select {`) 또는 SSOT `.nmin {` 규칙을 못 찾음(셀렉터가 바뀌었으면 이 게이트도 같이 고쳐라).')
        return 1
    a, b = _css_decls(src_box), _css_decls(ssot_box)
    for k in _INCANON_KEYS:
        av, bv = a.get(k), b.get(k)
        if k == 'padding' and av and bv and bv.startswith('var(--sp-2)') and av == '12px':
            continue   # 동값 토큰 치환(디자인 게이트가 raw 12px를 금지 = var(--sp-2) 강제) — 값 동일
        if av != bv:
            print('❌ 스튜디오 입력칸 정본 게이트 ⓐ 값 드리프트 — `%s`: 정본(%s) `%s` ≠ SSOT(%s) `%s`'
                  % (k, _INCANON_SRC, av, _INCANON_SSOT, bv))
            rc = 1
    # 3줄 창 크기 = thumb `.covrow textarea` 정본과 대조(전역 96 아님 = 1줄/3줄 계약)
    h3_src = _css_decls(_rule_body(src, '.covrow textarea') or '').get('min-height')
    h3_ssot = _css_decls(_rule_body(ssot, 'textarea.nmin') or '').get('min-height')
    if not h3_src or h3_src != h3_ssot:
        print('❌ 스튜디오 입력칸 정본 게이트 ⓐ 3줄 창 크기 드리프트 — 정본 `.covrow textarea` min-height=%s ≠ SSOT `textarea.nmin` min-height=%s'
              % (h3_src, h3_ssot))
        rc = 1

    # ⓑ 배선 + ⓒ 높이 재선언 0
    n_ok = n_ex = 0
    for rel in _INCANON_WIRED:
        try:
            s = open(os.path.join(ROOT, rel), encoding='utf-8').read()
        except Exception:
            continue
        if not re.search(r'<link[^>]+href="nm-input\.css"', s):   # 문자열 언급이 아니라 **실제 link 태그** — 주석에 파일명만 적혀도 통과하던 구멍(260804 킬테스트 검출)
            print('❌ 스튜디오 입력칸 정본 게이트 ⓑ — %s 가 SSOT를 상속 안 함 → head에 <link rel="stylesheet" href="nm-input.css">' % rel)
            rc = 1
        full = rel == 'viewer/tr.html'   # 도구 문서 = 문서 전체가 스튜디오 폼 = 전수 · 셸(index) = 계약 id만
        decls = [(m.start(), m.group(0), 'input') for m in _INPUT_RE.finditer(s)]
        decls += [(m.start(), m.group(0), 'textarea') for m in _TA_RE.finditer(s)]
        for pos, tag, kind in decls:
            if s.rfind('<script', 0, pos) > s.rfind('</script>', 0, pos):
                continue   # <script> 안 템플릿 문자열 = 정적 칸 아님(clip 게이트 동축)
            tl = tag.lower()
            if kind == 'input':
                tm = re.search(r'type\s*=\s*["\']?(\w+)', tl)
                if (tm.group(1) if tm else 'text') not in ('text', 'url', 'search'):
                    continue
            im = re.search(r'\bid\s*=\s*["\']([^"\']+)', tag)
            ident = im.group(1) if im else ''
            cm = re.search(r'\bclass\s*=\s*["\']([^"\']*)', tag)
            cls = (cm.group(1) if cm else '').split()
            ln = s[:pos].count('\n') + 1
            if kind == 'textarea' and 'geni-in' in cls:
                print('❌ 스튜디오 입력칸 정본 게이트 ⓑ 구 칩 문법 부활 — %s:%d <textarea%s> 가 `.geni-in`(13px/700 칩 축)을 씀 → `.nmin`으로'
                      % (rel, ln, (' #' + ident) if ident else ''))
                rc = 1
                continue
            if not (full or (rel, ident) in _INCANON_IDS):
                continue
            if any(c in ' '.join(cls) for c in _CLIP_EXEMPT_CLS) or (rel, ident) in _CLIP_EXEMPT_ID:
                n_ex += 1
                continue
            if 'nmin' not in cls:
                print('❌ 스튜디오 입력칸 정본 게이트 ⓑ — %s:%d <%s%s> 에 class="nmin" 없음(정본 활자·박스·창 크기 미상속 · SSOT = %s)'
                      % (rel, ln, kind, (' #' + ident) if ident else '', _INCANON_SSOT))
                rc = 1
                continue
            rm = re.search(r'\brows\s*=\s*["\']?(\d+)', tag)
            if kind == 'textarea' and rm and rm.group(1) != '3':
                print('❌ 스튜디오 입력칸 정본 게이트 ⓒ — %s:%d <textarea%s rows=%s> = 계약 위반(1줄 아니면 3줄 · 운영자 260804) → rows="3"'
                      % (rel, ln, (' #' + ident) if ident else '', rm.group(1)))
                rc = 1
                continue
            n_ok += 1
        # ⓒ `.nmin` 스코프 높이 재선언 0(표면 인라인이 SSOT 창 크기를 되돌리는 것 차단)
        for sel, body, off in _nmin_rules(s):   # 구 정규식 동치 치환(17.9s → 0.002s · _nmin_rules 주석 참조)
            d = _css_decls(body)
            hit = [k for k in ('height', 'min-height', 'max-height') if k in d]
            if hit:
                print('❌ 스튜디오 입력칸 정본 게이트 ⓒ 높이 재선언 — %s:%d `%s` 에 %s(창 크기는 SSOT 전담 = 1줄/3줄 고정)'
                      % (rel, s.count('\n', 0, off) + 1, sel.strip(), '·'.join(hit)))
                rc = 1
    if rc == 0:
        print('✅ 스튜디오 입력칸 정본 게이트 — 정본↔SSOT 값 %d축 + 3줄 창(%s) 동일 · 배선 칸 %d개 `.nmin` 보유(면제 %d) · 높이 재선언 0 · 구 칩 문법 0.'
              % (len(_INCANON_KEYS), h3_ssot, n_ok, n_ex))
    return rc


def check_url_placeholder():
    rc = 0
    for rel in VIEWERS_ALL:
        try:
            s = open(os.path.join(ROOT, rel), encoding='utf-8').read()
        except Exception:
            continue
        for m in _INPUT_RE.finditer(s):
            tag = m.group(0)
            if not re.search(r'type\s*=\s*["\']?url', tag, re.I):
                continue
            pm = re.search(r'placeholder\s*=\s*"([^"]*)"', tag)
            if not pm:
                continue
            im = re.search(r'\bid\s*=\s*"([^"]*)"', tag)
            if (rel, im.group(1) if im else '') in _URL_PH_EXEMPT:
                continue
            if pm.group(1) != _URL_PH:
                ln = s[:m.start()].count('\n') + 1
                print('❌ URL 입력칸 placeholder 이탈 — %s:%d "%s" → "%s" 단일 문법(설명은 title 툴팁·판정은 상태줄 · CII 「URL 입력칸」)'
                      % (rel, ln, pm.group(1), _URL_PH))
                rc = 1
    if rc == 0:
        print('✅ URL 입력칸 게이트 — type=url placeholder 전부 "%s" 단일 문법(안내 산문 0 · 면책 %d).' % (_URL_PH, len(_URL_PH_EXEMPT)))
    return rc


# render-text × (닫기/삭제 버튼이 SVG 아닌 문자 ×/✕ 사용) = 드리프트(§🎨 닫기=SVG X-path 단일 권장).
# 컴포넌트 컨텍스트(aria-label 닫기·삭제 류 또는 close/del/x 클래스)이고 *내용이 ×문자 하나뿐*일 때만 잡아
# 치수 텍스트('1080×1350')·JS 문자열 오탐 0. WARN(점진 통일 — thumb 등 병렬작업 파일이라 비차단).
_XSET = '×✕⨯╳✖'
_XEL_RE = re.compile(r'<(button|a|span|div|i)\b([^>]*)>\s*([' + _XSET + r'])\s*</\1>', re.I)
_XCTX_RE = re.compile(r'aria-label\s*=\s*["\'][^"\']*(닫기|닫음|삭제|취소|제거|지우)|class\s*=\s*["\'][^"\']*(tool-x|dlg-x|-x\b|close|abdel|del|btn-x)', re.I)

def check_x_char():
    warns = []
    for rel in VIEWERS_ALL:   # Q169 뷰어 목록 SSOT 상수화 — nb·sb 동반 편입
        try:
            s = open(os.path.join(ROOT, rel), encoding='utf-8').read()
        except Exception:
            continue
        s2 = re.sub(r'<!--.*?-->', '', s, flags=re.S)   # 주석 제거(오탐 차단)
        for m in _XEL_RE.finditer(s2):
            if _XCTX_RE.search(m.group(2)):
                ln = s2[:m.start()].count('\n') + 1
                warns.append('%s:%d <%s> 닫기/삭제 = 문자 「%s」 → SVG X-path(§🎨 닫기=SVG 단일 권장)'
                             % (rel, ln, m.group(1), m.group(3)))
    if warns:
        print('⚠️ 닫기/삭제 × 문자 게이트(비차단) — SVG로 통일 권장:')
        for w in warns:
            print('  -', w)
    else:
        print('✅ 닫기/삭제 × 문자 게이트 — 문자 ×/✕ 닫기버튼 0(전부 SVG).')
    return 0   # WARN-only(병렬작업 파일 비차단)


def check_tokens_link():
    """공유 구조토큰 tokens.css 배선 하드게이트(§🎨 STAGE3·분신술7·260628).
    도구 뷰어들(코드 튜플이 정본 · comp 폐지 260710 = 평의회 Q165 표기 정정)이 viewer/tokens.css를 <link>로 로드하는지 검증 — 미링크면 신규 컴포넌트가
    var(--r-m 등) 구조토큰을 못 써 raw로 새거나(드리프트), 옛 링크가 깨지면 침묵(check_paths가 HTML <link>
    미검증)이라 여기서 잡는다. tokens.css 파일 부재면 게이트 무력(아직 미생성=스킵)."""
    if not os.path.exists(os.path.join(ROOT, 'viewer', 'tokens.css')):
        print('⚠️ tokens.css 없음 — 구조토큰 링크 게이트 스킵'); return 0
    rc = 0
    for rel in VIEWERS_TOOLS:   # Q169 뷰어 목록 SSOT 상수화 — nb·sb 동반 편입(둘 다 tokens.css 링크 실측)
        try:
            html = open(os.path.join(ROOT, rel), encoding='utf-8').read()
        except Exception:
            continue
        if not re.search(r'<link[^>]+href=["\']tokens\.css["\']', html):
            print('❌ 구조토큰 링크 누락 — %s가 tokens.css를 <link> 안 함 → <head>에 <link rel=stylesheet href=tokens.css> 추가(§🎨 STAGE3)' % rel)
            rc = 1
    if rc == 0:
        print('✅ 구조토큰 링크 — 도구 뷰어 전부 tokens.css 로드(목록 = VIEWERS_TOOLS).')
    return rc


_VAR_USE_NOFB = re.compile(r'var\(\s*(--[A-Za-z0-9-]+)\s*\)')   # 폴백 없는 참조만(콤마 = 미매치)
_VAR_DEF_ANY = re.compile(r'(--[A-Za-z0-9-]+)\s*:')             # CSS 선언·인라인 style·JS 문자열 내 정의 초집합
_VAR_DEF_SETP = re.compile(r'''setProperty\(\s*['"](--[A-Za-z0-9-]+)['"]''')


def check_dangling_var():
    """댕글링 var() 하드게이트(평의회 Q165 게이트 갭 ① → Q169 신설).
    뷰어가 자기 파일(+링크한 tokens.css) 어디에도 정의 없는 토큰을 폴백 없이 var() 참조하면
    그 선언은 IACVT로 통째 무효 = 승인된 디자인이 소리 없이 투명·무보더 렌더(ly 앵커팝 실증 260718).
    check_design(raw값 축)·_new_dead_tokens(index 미사용 축)가 못 보던 제3축. 정의 수집 =
    `--x:` 선언 초집합 + setProperty('--x') — var(--x, 폴백)은 대상 아님(폴백이 안전망).
    iframe 문서 경계로 커스텀 프로퍼티 상속 없음 전제."""
    rc = 0
    try:
        tkp = os.path.join(ROOT, 'viewer', 'tokens.css')
        _strip = lambda t: re.sub(r'/\*.*?\*/', '', t, flags=re.S)   # 블록 주석 제거 후 수집(주석 속 '--x:'를 정의로 오인해 실깨짐을 가리는 틈 봉합 · W-A 노트 → Q176) — // 라인 주석은 URL(http://) 오폭 위험이라 보존, defs·uses 동일 스트립본이라 정합
        tk_defs = set(_VAR_DEF_ANY.findall(_strip(open(tkp, encoding='utf-8').read()))) if os.path.exists(tkp) else set()
        for rel in VIEWERS_ALL:
            try:
                s = _strip(open(os.path.join(ROOT, rel), encoding='utf-8').read())
            except Exception:
                continue
            defs = set(_VAR_DEF_ANY.findall(s)) | set(_VAR_DEF_SETP.findall(s))
            if 'tokens.css' in s:
                defs |= tk_defs
            for name in sorted(set(_VAR_USE_NOFB.findall(s)) - defs):
                print('❌ 댕글링 var(): %s 가 %s 를 폴백 없이 참조하는데 정의가 없음(자기 파일·tokens.css) → 토큰 추가(정본값 계승) 또는 폴백 인자(Q169)' % (rel, name))
                rc = 1
        if rc == 0:
            print('✅ 댕글링 var() 게이트 — 미정의 무폴백 참조 0(10뷰어).')
    except Exception as e:
        print('⚠️ 댕글링 var() 게이트 스킵:', e); return 0
    return rc


def check_soremeori():
    """소머리(구분자 •) 표준 강제 — 텍스트 흰색(--fg)·블릿 형광(--accent)·토큰 굵기(§📐·운영자 260629).
    회색(--mut) 소머리·블릿 없는 소머리·리터럴 굵기 재발을 차단(옛 흰색600 인라인 드리프트 방지).
    정본 = 뉴스 index .cref-lbl/p.lbl(정본도 게이트 = 리터럴 재드리프트 차단·감사 260704 사각 제거). 대상 = label.fl(thumb/k/ly/track/conv) + thumb .csec/.hist-bul.
    .gospec(명세 readout)은 소머리 아님 = 검사 제외."""
    rc = 0
    # 정본(index) 소머리 = .cref-lbl(텍스트 흰색800) + ::before/p.lbl::before(형광 블릿700) — 정본도 검사(옛 '무변경 정본' 사각지대 제거: 감사서 리터럴 13/800 드리프트 발견 → 토큰화 후 게이트로 고정)
    try:
        idx = open(os.path.join(ROOT, 'viewer', 'index.html'), encoding='utf-8').read()
        ml = re.search(r'\.cref-lbl\s*\{([^}]*)\}', idx)
        if not ml or 'var(--fg)' not in ml.group(1) or 'var(--fw-x)' not in ml.group(1):
            print('❌ 소머리 게이트 — index .cref-lbl 텍스트가 흰색(--fg)·800(--fw-x) 토큰 아님(리터럴 재드리프트·§📐 정본)'); rc = 1
        mlb = re.search(r'\.cref-lbl::before\s*\{([^}]*)\}', idx)
        if not mlb or 'var(--accent)' not in mlb.group(1) or 'var(--fw-b)' not in mlb.group(1):
            print('❌ 소머리 게이트 — index .cref-lbl::before 블릿이 형광(--accent)·700(--fw-b) 토큰 아님(§📐 정본)'); rc = 1
        mpb = re.search(r'p\.lbl::before\s*\{([^}]*)\}', idx)
        if not mpb or 'var(--accent)' not in mpb.group(1) or 'var(--fw-b)' not in mpb.group(1):
            print('❌ 소머리 게이트 — index #cardsec p.lbl::before 블릿이 형광(--accent)·700(--fw-b) 토큰 아님(§📐 정본)'); rc = 1
    except Exception:
        pass
    # 블록 소머리 label.fl = 텍스트 흰색(--fg)·800(--fw-x) + ::before 형광(--accent)·700(--fw-b)
    for rel in VIEWERS_TOOLS:   # Q169 뷰어 목록 SSOT 상수화(구 순서 thumb·k·ly… = 동일 집합) — nb·sb 동반 편입
        try:
            css = open(os.path.join(ROOT, rel), encoding='utf-8').read()
        except Exception:
            continue
        m = re.search(r'label\.fl\s*\{([^}]*)\}', css)
        if not m:
            print('❌ 소머리 게이트 — %s에 label.fl 규칙 없음(소머리 = 흰색800+형광블릿·§📐)' % rel); rc = 1; continue
        if 'var(--fg)' not in m.group(1) or 'var(--fw-x)' not in m.group(1):
            print('❌ 소머리 게이트 — %s label.fl 텍스트가 흰색(--fg)·800(--fw-x) 아님(회색/리터럴 금지·§📐)' % rel); rc = 1
        mb = re.search(r'label\.fl::before\s*\{([^}]*)\}', css)
        if not mb or 'var(--accent)' not in mb.group(1) or 'var(--fw-b)' not in mb.group(1):
            print('❌ 소머리 게이트 — %s label.fl::before 블릿이 형광(--accent)·700(--fw-b) 아님(블릿 누락/색오류·§📐)' % rel); rc = 1
    # flex 소머리 thumb .csec = 텍스트 흰색800 + ::before 형광700 · .hist-bul = 특수 보라
    try:
        t = open(os.path.join(ROOT, 'viewer', 'thumb.html'), encoding='utf-8').read()
        mc = re.search(r'\.csec\s*\{([^}]*)\}', t)
        if not mc or 'var(--fg)' not in mc.group(1) or 'var(--fw-x)' not in mc.group(1):
            print('❌ 소머리 게이트 — thumb .csec 텍스트가 흰색(--fg)·800(--fw-x) 아님(§📐)'); rc = 1
        mcb = re.search(r'\.csec::before\s*\{([^}]*)\}', t)
        if not mcb or 'var(--accent)' not in mcb.group(1) or 'var(--fw-b)' not in mcb.group(1):
            print('❌ 소머리 게이트 — thumb .csec::before 블릿이 형광(--accent)·700(--fw-b) 아님(§📐)'); rc = 1
        # .hist-bul 정본 = nm-hist.css(운영자 260802 일맥상통 — thumb 인라인 → 공유 링크 SSOT 승격 · tr.html 동승) · 파일 소실 = t_hist '' = 게이트 실패(정본 증발 검출)
        try:
            t_hist = open(os.path.join(ROOT, 'viewer', 'nm-hist.css'), encoding='utf-8').read()
        except OSError:
            t_hist = ''
        mh = re.search(r'\.hist-bul\s*\{([^}]*)\}', t + t_hist)
        if not mh or 'var(--hist-accent)' not in mh.group(1):
            print('❌ 소머리 게이트 — .hist-bul 특수 블릿이 이력색(--hist-accent) 아님(§📐 특수 · 정본 = viewer/nm-hist.css)'); rc = 1
        # 토글(.ovfmt/.onoff) 붙는 .csec 행높이 상쇄 = 토글 세로패딩(3px·탭영역)이 flex 행 키워 첫 소머리 • 내려앉는 것 차단(§📐 첫 블릿 화면선·운영자 260629 저작권탭 교정)
        mn = re.search(r'\.csec \.ovfmt\s*,\s*\.csec \.onoff\s*\{([^}]*)\}', t)
        nb = mn.group(1) if mn else ''
        if not mn or not (('margin-top:-' in nb and 'margin-bottom:-' in nb) or 'margin-block:-' in nb):
            print('❌ 소머리 게이트 — thumb .csec 토글(.ovfmt/.onoff) 행높이 상쇄(margin-block:-3px) 누락 → 토글 붙은 첫 소머리 • 내려앉음 재발(§📐 첫 블릿 화면선)'); rc = 1
    except Exception:
        pass
    if rc == 0:
        print('✅ 소머리 게이트 — 6뷰어 소머리 텍스트 흰색·블릿 형광(특수 보라)·토큰 일치(§📐).')
    return rc


def check_claude_failover():
    """모든 Claude 호출 스크립트는 폴오버 SSOT를 경유 — 계정 로테이션 통일(운영자 260629·§📰).
    자체 쿼터 정규식·자체 폴오버 금지: 한 곳만 stale돼도 전건 실패(260629 'weekly limit' 미인식 실측 = 폴오버 누락·요약/카드 전건 failed).
    스캔 범위 = .github/scripts/ + scraper/(둘 다 실제 claude 호출처 — auto_pick_breaking.py가 scraper에 있음 · 분신술10 발견).
    호출 신호 = 비-주석 라인의 claude_meter / run_claude( / 'claude -p'(주석·docstring 멘션은 제외 = ly_stt·token_report 오탐 차단 → run_claude는 *호출* `(` 요구).
    경유 = claude_failover(셸 SSOT 호출) 또는 claude_py/run_claude(파이썬 SSOT = is_quota+failover 내장)."""
    rc = 0
    miss = []
    INVOKE = re.compile(r'''^(?!\s*#).*(claude_meter|run_claude\(|claude -p|["']claude["']\s*,\s*["']-p["'])''', re.M)   # 실제(비-주석) Claude 호출 + 리스트형 raw subprocess(["claude","-p"…]) 우회 탐지(운영자 260718 "전사 폴오버" — trend_images·more_images가 리스트형으로 게이트 우회→주계정 쿼터 즉사 실측 봉합) · run_claude는 호출`(`만(import·docstring 제외)
    COMPLY = re.compile(r'claude_failover|claude_py|run_claude')                     # 셸=claude_failover 호출 / 파이썬=claude_py(run_claude) SSOT 경유
    # 스캔 범위 = 파이프라인 스크립트 2곳(의도) — shared/는 미스캔: shared/summary_repair.sh 의 보강 콜은
    #   1콜 상한·fail-soft(실패=원본 유지)라 폴오버 불요 = 문서화된 예외(평의회3 260705). shared/에 폴오버가
    #   필요한 claude 호출을 새로 넣으면 이 범위에 'shared'를 추가할 것.
    for d in ('.github/scripts', 'scraper'):
        sdir = os.path.join(ROOT, d)
        try:
            names = sorted(n for n in os.listdir(sdir) if n.endswith(('.sh', '.py')))
        except Exception:
            continue
        for n in names:
            try:
                txt = open(os.path.join(sdir, n), encoding='utf-8').read()
            except Exception:
                continue
            if not INVOKE.search(txt):
                continue
            if not COMPLY.search(txt):
                miss.append(d + '/' + n)
    if miss:
        print('❌ claude 폴오버 게이트 — Claude 호출인데 폴오버 SSOT(claude_failover/claude_py) 미경유: %s · 자체 쿼터처리 금지(계정 로테이션 통일·§📰)' % ', '.join(miss))
        rc = 1
    else:
        print('✅ claude 폴오버 게이트 — 전 Claude 호출처(.github/scripts+scraper)가 폴오버 SSOT 경유(주간한도 시 4계정 자동 로테이션 통일·§📰).')
    return rc


def check_judge_bare():
    """judge(gate_judge·breaking_judge)는 라이브·구독 OAuth 전용 파이프라인 → --bare 금지, --safe-mode만.
    ⚠️ 진짜 원인(260701 실측 정정): --bare는 OAuth를 안 읽는다(CLI 2.1.197 --help 명시 "Anthropic auth is
    strictly ANTHROPIC_API_KEY or apiKeyHelper — OAuth and keychain are never read"). 이 레포는 구독 OAuth 전용
    (종량제 키 없음 · 워크플로가 ANTHROPIC_API_KEY도 unset)이라 judge에 --bare면 *인증부터* rc=1 즉사 = #1264(260630)
    사고의 진짜 원인. (당시 'MultiEdit matches no known tool' stderr는 *비치명 노이즈* — normal/safe 모드에서도 뜨고 rc=0,
    MultiEdit은 CLI 2.1.197에 아예 없는 도구일 뿐. 도구충돌은 원인 아니었음·실측 260701.)
    ∴ CLAUDE.md 로드 스킵(cache_w 절감)이 필요하면 반드시 --safe-mode(Auth·built-in 도구·permissions 정상 유지).
    게이트: judge 스크립트가 '--bare'를 emit(코드경로)하면 rc=1 · 생성경로(claude_meter·more_images)도 --bare 기본 ON이면 rc=1(OAuth 즉사).
    정본 = CLAUDE.md §📰 + docs/인계_bare도구충돌_judge복구_프로세스개선.md."""
    rc = 0
    bad = []

    def _read(p):
        try:
            return open(os.path.join(ROOT, p), encoding='utf-8').read()
        except Exception:
            return ''

    # judge(py): '--bare' emit(코드경로)면 = OAuth 인증 즉사. 주석 속 설명('--safe-mode: … --bare 아님')은 따옴표 없어 미매칭.
    for n in ('gate_judge.py', 'breaking_judge.py'):
        txt = _read('.github/scripts/' + n)
        if re.search(r'"--bare"', txt):
            bad.append('%s (judge에 --bare emit = OAuth 안 읽어 인증 즉사 → --safe-mode 사용)' % n)

    # 생성경로: --bare 기본 ON(claude_meter :-1 / more_images "1")이면 = OAuth 즉사(현재 롤백 OFF면 통과)
    if re.search(r'CLAUDE_BARE:-1', _read('shared/claude_meter.sh')):
        bad.append('claude_meter.sh (CLAUDE_BARE 기본 ON = 생성경로 --bare = OAuth 즉사)')
    if re.search(r'CLAUDE_BARE"\s*,\s*"1"', _read('.github/scripts/more_images.py')):
        bad.append('more_images.py (CLAUDE_BARE 기본 ON = --bare = OAuth 즉사)')

    if bad:
        print('❌ judge/파이프라인 --bare 게이트 — OAuth 전용 레포에 --bare(OAuth 안 읽음=인증 즉사·260701 사고 진짜원인): %s → --safe-mode로 교체(CLAUDE.md 로드 스킵 + Auth·도구 정상 · 정본 CLAUDE.md §📰)' % ', '.join(bad))
        rc = 1
    else:
        print('✅ judge/파이프라인 --bare 게이트 — judge는 --safe-mode(OAuth 정상)·생성경로 --bare 기본 OFF(260701 사고 재발방지).')
    return rc


def check_playground():
    """플레이그라운드 템플릿 게이트(하드 · 실행 계약 5 · §플레이그라운드 0-1 · 260713).
    대상 = data-pg-template 스탬프가 있는 파일만(레거시 48개 소급 실패 방지 — git 날짜 소실이라 스탬프 스코핑이 유일 경로 · 평의회 O7).
    검증 = 구성 5요소 마커 · near() 계승판정 · 재렌더 scrollTop 보존(스크롤 튕김 = 운영자 반복 실측 260712) · 자유 hex 피커 금지 · 현행 비교 기준."""
    import glob as _g
    hard = []
    soft = []
    targets = sorted(_g.glob('docs/reports/*플레이그라운드*.html'))
    if os.path.exists('shared/playground_template.html'):
        targets.append('shared/playground_template.html')
    for p in targets:
        try:
            with open(p, encoding='utf-8') as f:
                s = f.read()
        except Exception:
            continue
        if 'data-pg-template' not in s:
            continue
        for m in ('data-pg-preview', 'data-pg-baseline', 'data-pg-presets', 'data-pg-copy', 'data-pg-note'):
            if m not in s:
                hard.append('%s: %s 누락(구성 5요소)' % (p, m))
        if 'near(' not in s:
            hard.append('%s: near() 계승판정 미배선' % p)
        if re.search(r'data-pg-preview[\s\S]{0,8000}\.innerHTML\s*=', s) and 'scrollTop' not in s:
            hard.append('%s: 미리보기 재렌더 scrollTop 보존 없음(스크롤 튕김 · §플레이그라운드)' % p)
        if 'type="color"' in s:
            hard.append('%s: 자유 hex 피커 금지(팔레트 폐쇄 셀렉트만 · 포터블 §7-2-3)' % p)
        if '현행' not in s:
            hard.append('%s: 현행 비교 기준 없음(기본값 = 현행 실측)' % p)
        # ⑥ 미리보기 고정(운영자 260801 · 포터블 §3-1 ⑥) — 콘솔이 길어지면 조작 중 미리보기가 화면 밖으로 나간다.
        #   PC sticky + **폰 티어(≤900px) sticky** 둘 다 있어야 계약 성립(PC만이면 flex-wrap 후 그대로 스크롤 아웃).
        #   동결 골격 = 하드(우리가 통제) · 개별 시안 = WARN(스탬프 23종 소급 실패 방지 · 신규는 골격 복사라 자동 충족).
        _fix = ('position:sticky' in s) and re.search(r'@media[^{]*max-width:\s*9\d\dpx[\s\S]{0,600}?position:sticky', s)
        if not _fix:
            if p.startswith('shared/'):
                hard.append('%s: ⑥ 미리보기 고정 누락(PC sticky + 폰 티어 sticky 둘 다 · 포터블 §3-1)' % p)
            else:
                soft.append('%s: ⑥ 미리보기 고정 미확인(폰 티어 sticky 없음 — 신규 시안은 골격 복사로 자동 충족)' % p)
    if hard:
        print('❌ 플레이그라운드 게이트 %d건:' % len(hard))
        for h in hard:
            print('  -', h)
        return 1
    if soft:
        print('⚠️ 플레이그라운드 게이트(WARN·비차단) %d건 — 신설 축(⑥ 미리보기 고정 · 260801) 소급 미충족:' % len(soft))
        for h in soft:
            print('  -', h)
    print('✅ 플레이그라운드 게이트 — 템플릿 세대(data-pg-template) 5요소+⑥고정·near·스크롤 보존 확인')
    return 0


def check_candidates_size():
    """viewer/candidates.json 크기 가드(WARN-only·260714) — 3000개(3.45MB)로 비대해져 라이브 서빙
    api/candidates(GitHub contents 1MB 한도·Cloudflare 함수 부담)가 빈 [](HTTP 200)을 뱉어 뷰어가
    수집함을 통째로 비우던 사고. CAP(to_candidates CAND_CAP)로 감량하되, 슬금슬금 다시 1MB를
    넘으면 커밋 전 눈에 띄게. WARN-only = candidates.json은 scrape 자동커밋이라 rc=1이면 자동화가 깨짐."""
    p = os.path.join(ROOT, 'viewer', 'candidates.json')
    try:
        sz = os.path.getsize(p)
    except OSError:
        return 0
    if sz > 1024 * 1024:
        print('⚠️ candidates.json %.2fMB > 1MB — api/candidates 서빙 실패(빈 [] 반환)로 수집함 텅빔 위험. CAND_CAP 낮춰 감량 권장(260714).' % (sz / 1048576))
    return 0   # WARN-only


def check_conflict_markers():
    """병합 충돌 마커 잔존 게이트(평의회⑧ 260717 — #2368이 큐 원장에 마커 3줄 남긴 실사고 재발 방지).
    docs/*.md·CLAUDE.md·viewer/*.html에서 줄머리 '<<<<<<< '/'>>>>>>> ' 검출(정의적 마커만 — ======= 단독은 정상 문서와 충돌 가능해 제외)."""
    import glob as _g
    bad = []
    l7, r7 = '<' * 7 + ' ', '>' * 7 + ' '
    targets = _g.glob(os.path.join(ROOT, 'docs', '*.md')) + _g.glob(os.path.join(ROOT, 'viewer', '*.html')) + [os.path.join(ROOT, 'CLAUDE.md')]
    for path in targets:
        try:
            with open(path, encoding='utf-8') as f:
                for i, ln in enumerate(f, 1):
                    if ln.startswith(l7) or ln.startswith(r7):
                        bad.append('%s:%d 병합 충돌 마커 잔존 — 양측 내용 보존 후 마커만 제거하라' % (os.path.relpath(path, ROOT), i))
        except Exception:
            pass
    return bad


# 원장 Q번호 역사 중복 베이스라인(260717 게이트 신설 시점 실측 — 세션 갈래별 번호가 병존하던 시절 유산 면책).
# 규약(운영자 260717 승인 "게이트 ㄱ"): 이후 신규 부여 = 파일 전체 최대 Q+1(전역 유일). 중복이 '늘 때만' rc=1(래칫 —
# 디자인 토큰 baseline 관용구). 정당 사유(중복 행 정리 등)로 재베이스라인 시 아래를 게이트 파서 실측값으로 갱신 + 사유 기록.
# 재베이스라인 260717 15:35(사유): 게이트 신설과 같은 날 병렬 세션들의 경합 행(Q13~17)이 신설 실측 *이후* main에 합류 —
#   전부 머지 박제분(타 세션 행 무접촉 원칙상 리넘버 불가)이라 파서 실측값으로 면책 승계. 본 세션 신규 행 = Q33~35 유일 확인.
# 재베이스라인 260717 16:25(사유): Q39 ×2 — 두 타 세션 행(드롭 계승 · 표 정리 보고)이 같은 번호로 이미 각자 main 머지 완료 =
#   박제분 면책 승계(origin/main 자체가 ×2 실측 · 본 세션 신규 행 = Q41 유일 · 다음 부여 = Q42).
# 재베이스라인 260717 23:40(사유): Q91 ×2 — 두 타 세션 머지분(요구사항 프로토콜 [1]~[15] 등재 #2458 · 22:05 규칙 주입 요약)이
#   각자 main 머지 완료 = origin/main 자체가 ×2 실측(재부여 불가[양쪽 박제]라 면책 승계 · 본 세션 신규 행 = Q104 유일 · 다음 부여 = Q105).
# 재베이스라인 260726 09:5x(사유): Q560 ×2 — insta-geo-demo(구 Q559 재부여)·smoke-qrow-parity 두 타 세션 행이 각자 main 머지 완료 =
#   origin/main 자체가 ×2 실측(재부여 불가[양쪽 박제] · 본 세션 신규 행 = Q561[claudemd-first-line] 유일 · 다음 부여 = Q562).
#   같은 날 이 경합이 4회 연속(Q556→558→560) = 손 재부여 왕복이 규칙 실패 신호라, 이 커밋에서 --fix-qnum(자동 재부여) +
#   check-refs.yml push 트리거(main 무검사 사각 봉합)를 함께 넣는다 — 면책 승계가 늘어나는 근본 원인은 'main이 게이트를 안 받는 것'이었다.
# 재베이스라인 260726 10:1x(사유): Q562 ×2 — insta-geo-demo(구 Q559→Q560→Q562 3연속 재부여)와 qnum-race-machine(#2998)이
#   각자 main 머지 완료 = origin/main 자체가 ×2 실측(재부여 불가[양쪽 박제] · --fix-qnum이 무접촉 판정 + 이 승계를 안내한 첫 실전 사례).
#   본 세션 신규 행 = Q564 유일 · 다음 부여 = Q565.
# 재베이스라인 260728 18:0x(사유): Q1012 ×2 — model-selection-immediate-apply(Q1007 부분 회수분)와
#   image-edit-mosaic-check가 각자 main 머지 완료 = origin/main 자체가 ×2 실측(양쪽 박제 = 재부여 불가).
#   --fix-qnum이 "무접촉 판정 + 승계 안내"를 반환 = 선례와 동일 문법으로 승계.
#   본 세션 신규 행 = Q1014(만능 다운로더 v6.2 최고화질 봉합) 유일 · 다음 부여 = Q1015.
# 재베이스라인 260728 18:2x(사유): Q1007 ×2 · Q1013 ×2 — 세션 작업 중 타 세션이 같은 번호를 각자 main에 머지해
#   origin/main 자체가 ×2 실측(양쪽 박제 = 재부여 불가). --fix-qnum이 내 행만 Q1013 → Q1014로 자동 재부여하고
#   나머지는 "무접촉 판정 + 승계 안내"를 반환 = 선례와 동일 문법으로 승계.
# 1107(260729) = 같은 축 재발 — claude/recent-image-edit-button-c8bq4u 진행중 마커 + claude/ai-summary-divider-split-i2yhse 완료 행이
#   둘 다 origin/main 박제라 재부여 불가(내 행은 Q1109로 이미 유일 · main 원장만으로 대조해도 rc=1 = 선재 실패 실측). 위 문법 그대로 승계.
_QDUP_BASE = {1: 45, 2: 23, 3: 20, 4: 20, 5: 17, 6: 16, 7: 15, 8: 11, 9: 10, 10: 8,   # 1~5 각+1 = 재베이스라인 260803 12:4x(같은 세션 image-studio-preview-sizing-qewbep — 훅 기계 캡처가 영상 원본비 턴 Q01~Q05를 자동 등재 · 같은 낮은 번호대 origin/main 다수 박제 = --fix-qnum 「재부여 불가(양쪽 머지)」 → 관례 면책 승계 · 박제 행 무접촉)
# 1·2 각+1 = 재베이스라인 260810 09:5x(산출 사슬 재감사 세션 ig-thread-spec-correction-uie0fi — 훅 기계 캡처가 이 세션 Q01·Q02를 자동 등재했는데 같은 번호대가 origin/main에 이미 박제 = --fix-qnum 「재부여 불가(양쪽 머지)」 판정 → 관례(260802·260803 선례)대로 면책 승계 · 박제 행 무접촉)
# 1~10 각+1 = 재베이스라인 260802 22:2x(미리보기 통일 세션 image-studio-preview-sizing-qewbep — 훅 기계 캡처가 이 세션 Q01~Q10을 자동 등재했는데 같은 낮은 번호대가 origin/main에 이미 다수 박제 = --fix-qnum 「재부여 불가(양쪽 머지)」 판정 → 관례(1107·1072 선례)대로 면책 승계 · 박제 행 무접촉)
 11: 6, 12: 6, 13: 5, 14: 3, 15: 2, 16: 3, 17: 2, 18: 2, 19: 2, 23: 2, 39: 2, 43: 2, 49: 2, 63: 2, 64: 2, 91: 2, 132: 2, 135: 2, 136: 2, 142: 2, 156: 2, 161: 2, 163: 2, 171: 2, 183: 2, 255: 2, 256: 2, 271: 2, 272: 2, 289: 2, 290: 2, 291: 2, 292: 2, 306: 2, 307: 2, 308: 2, 309: 3, 310: 3, 322: 2, 323: 2, 324: 2, 355: 2, 356: 2, 369: 2, 372: 2, 376: 2, 388: 2, 457: 2, 560: 2, 562: 2, 569: 2, 574: 2, 575: 2, 591: 2, 607: 2, 611: 2, 613: 2, 614: 4, 621: 2, 623: 2, 633: 2, 656: 2, 670: 2, 681: 2, 682: 2, 687: 2, 688: 2, 902: 2, 912: 2, 918: 2, 928: 2, 930: 2, 933: 3, 934: 3, 935: 2, 936: 2, 937: 2, 938: 2, 939: 2, 942: 2, 946: 2, 950: 2, 957: 2, 961: 2, 968: 2, 970: 2, 973: 2, 977: 3, 982: 2, 991: 2, 1003: 2, 1007: 2, 1012: 2, 1016: 2, 1051: 2, 1052: 2, 1053: 2, 1056: 2, 1058: 2, 1072: 2, 1107: 2}   # 1107:2 = 재베이스라인 260729 18:2x(이미지 스튜디오 선택자 세션 image-studio-selector-frame-lvfrit — Q1107을 **타 세션 두 곳이 양쪽 다 origin/main에 박제**[수정버튼 행 recent-image-edit-button-c8bq4u + 채널요약 판분리 행 ai-summary-divider-split-i2yhse] = 재부여 불가[박제 행 무접촉 원칙 · 1072·1058·1053 선례] · 내 행은 경합 3연속(Q1099→1102→1105→1107)을 피해 **Q1109/Q1110으로 자진 이동 완료** = 내 신규 중복 0 · `--fix-qnum` 판정 = 「미처리 Q1107 — 재부여 불가(양쪽 머지)」)   # 1072:2 = 재베이스라인 260729 13:5x(커뮤니티 인앱 창 세션 domestic-community-inapp-window-wx6vc9 — Q1072를 **내 행(헤더 보강·EUC-KR·지연이미지 #3292)과 타 세션 행이 양쪽 다 origin/main에 박제** = 재부여 불가[내 행을 옮기면 이미 머지된 PR·커밋의 [Q.NN] 1:1 참조가 깨진다 · 1058·1053·1016 선례] · `--fix-qnum` = 「미처리 Q1072 — 재부여 불가(양쪽 머지)」 + 내 신규 행 Q1073 자동 부여 · **박제 행 무접촉**)   # 1058:2 = 재베이스라인 260729 09:4x(커뮤니티 인앱 창 세션 domestic-community-inapp-window-wx6vc9 — Q1058을 **내 행(cembed 다크·폭맞춤 프록시 #3279)과 타 세션 행이 양쪽 다 origin/main에 박제** = 재부여 불가[내 행을 옮기면 이미 머지된 PR 본문·커밋의 [Q.NN] 1:1 참조가 깨진다 · 1053·1016·1012 선례] · `--fix-qnum` = 「미처리 Q1058 — 재부여 불가(양쪽 머지)」 + 내 신규 행 Q1060 자동 부여 · **박제 행 무접촉**)   # 1056:2 = 재베이스라인 260729 08:5x(TOP 스택 확장 복원 세션 realtime-top10-refresh-layout-kbjkmm — Q1056이 **타 세션 두 행**[AI 생성 요약바 강조·탭 전환 · 국내 커뮤니티 인앱 배선 domestic-community-inapp-window-wx6vc9]으로 origin/main에 양쪽 박제 = 재부여 불가[1053 좌측 선례와 동일 · 내 행 아님] · `--fix-qnum` = 「미처리 Q1053 · Q1056」 확인 + 내 행 Q1053→Q1057 자동 재부여 완료 · **박제 행 무접촉** · 이 세션 신규 행 = Q1057[TOP 스택 11위+ 확장 복원] = 파일 최대+1 유일)   # 1053:2 = 재베이스라인 260729 08:4x(국내 커뮤니티 인앱 배선 세션 domestic-community-inapp-window-wx6vc9 — Q1053이 **타 세션 두 행**[대기열 비활성 ↗ 취소 #3270 · 키워드 세션 갈래]으로 origin/main에 양쪽 박제 = 재부여 불가[1051·1052 좌측 선례와 동일] · `--fix-qnum` = 내 행 Q1053→Q1054 자동 재부여 + 「미처리 — 재부여 불가(양쪽 머지)」 확인 · **박제 행 무접촉** · 이 세션 신규 행 = Q1056[국내 커뮤니티 인앱 창] = 파일 최대+1 유일)   # 1051:2·1052:2 = 재베이스라인 260729 08:2x(키워드 알림 세션 keyword-notification-check-ysbb8c — Q1051·Q1052를 **내 행과 타 세션 행이 양쪽 다 origin/main에 박제**[내 행 = 키워드 알림 진단·개선 · 타 세션 = 영상 스튜디오 편집/자막 탭 · 이미지 스튜디오 카드 톤] = 재부여 불가[내 행을 옮기면 이미 머지된 커밋 메시지·PR 본문의 [Q.NN] 1:1 참조가 깨진다 · 1016·1012·1007 선례] · `--fix-qnum` = 「미처리 Q1051 · Q1052 — 재부여 불가(양쪽 머지)」 실행 확인 · **원장 파일 무접촉** · ⓘ 별건으로 리베이스가 만든 Q1052 블록 자기중복 1건은 면책이 아니라 원장에서 제거[main 정본으로 교체] · 이 세션 신규 행 = Q1054[SNS 전 소스 감시 편입] = 파일 최대+1 유일)   # 1016:2 = 재베이스라인 260728 19:5x(비디오 스튜디오 편집 탭 재편 세션 video-studio-ui-refinement-nhazzg — Q1016이 **타 세션 두 행**[favicon-loading-animation-9j1uhb · video-studio-subtitle-preview-bokwno]으로 origin/main에 이미 양쪽 박제 = 재부여 불가[내 행이 아니라 옮기면 [Q.NN] 1:1 참조가 깨진다 · 1012·1007·1003 선례] · `--fix-qnum` = 「미처리 — 재부여 불가(양쪽 머지)」 · **원장 파일 무접촉** · 이 세션 신규 행 = Q1022~Q1035[편집 탭 재편 14행] = 파일 최대+1부터 연번 = 유일)   # 1003:2 = 재베이스라인 260728 16:3x(자막 문장복원·편집 일원화 세션 subtitle-sentence-segmentation-r5y0q7 — Q1003이 **타 세션 두 행**[urgent-auto-summary-issue-hdwqtb 진행중 · news-summary-card-prompt-button-ifc5te]으로 origin/main에 이미 양쪽 박제 = 재부여 불가[내 행이 아니라 옮기면 [Q.NN] 1:1 참조가 깨진다 · 991·982·977 선례] · `--fix-qnum` = 「미처리 Q1003 — 재부여 불가(양쪽 머지)」 실행 확인 · **원장 파일 무접촉** · 이 세션 신규 행 = Q1005[경과시간 00분 00초 표기+토큰 부기] = 파일 최대+1 유일)   # 991:2 = 재베이스라인 260728 13:2x(ly 자막 미리보기 세션 · video-studio-subtitle-preview-bokwno — Q991이 **타 세션 두 행**[subtitle-sentence-segmentation-r5y0q7 · image-studio-concurrent-output-vajcl9]으로 origin/main에 이미 양쪽 박제 = 재부여 불가[내 행이 아니라 옮기면 [Q.NN] 1:1 참조가 깨진다 · 982·977·973 선례] · `--fix-qnum` = 「미처리 Q991 — 재부여 불가(양쪽 머지)」 실행 확인 · **원장 파일 무접촉** · 이 세션 신규 행 = Q992[라이브 영상 부착 단일 이벤트 봉합] = 파일 최대+1 유일)   # 982:2 = 재베이스라인 260728 05:1x(요약요청 산출물 유실 봉합 세션 — Q982가 **타 세션 두 행**[youtube-popular-content-limit-ezxeer · news-summary-bug-3zt35v]으로 origin/main에 이미 양쪽 박제 = 재부여 불가[내 행이 아니라 옮기면 [Q.NN] 1:1 참조가 깨진다 · 977·973·970 선례] = 면책 승계만 · 이 세션 신규 행 = Q983[CI 러너 pre-commit 게이트 분리] = 파일 최대+1 · 앞서 Q981→Q982→Q983 으로 --fix-qnum 2회 밀린 건이라 경합 실황 그 자체)   # ⟨양쪽 보존 260728 04:5x⟩ 같은 977:3 승계를 두 세션이 각자 등재 = **키 합집합 동일**(값 충돌 0)이라 상대 판을 그대로 두고 이 세션(컷편집 리뷰 hml2kf)의 실측 근거만 덧붙인다 — 규약 「양쪽 사유 주석 전량 보존」 · 운영자 260728 "둘다 살리면서 머지해줘". 내 실측: 직전 커밋(#3212 · 977:2)이 머지되는 사이 **세 번째 타 세션 행**[news-summary-ai-image-toggle-5fqive · 큐 5293행]이 같은 번호로 추가 박제 = ×3 · `grep -c '^- ✅ Q977(video-cut'` = **0**(내 행 아님 재확인) · `--fix-qnum` 여전히 「미처리 Q977 — origin/main에 이미 박제된 타 세션 행이라 재부여 불가(양쪽 머지)」 · 그래서 값만 2→3, **원장 파일 무접촉** · 이 세션 신규 행 = Q974·Q975[컷편집 강화 5종 · 필러 강도 3단].   # 977:3 = 재베이스라인 260728 04:4x(같은 세션 창에서 타 세션 3번째 행이 Q977로 추가 착지 = 전부 타 세션 박제 · 재부여 불가 · 면책 승계만 · 내 행 = Q979 유일)   # 977:2 = 재베이스라인 260728 04:3x(픽 502 재발방지 ②③ 세션 — Q977이 **타 세션 두 행**[요약단축-3차-소넷사진로봇-병렬 · cardnews-line-limit-review-d8od84]으로 origin/main에 이미 양쪽 박제 = 재부여 불가[내 행이 아니라 옮기면 [Q.NN] 1:1 참조가 깨진다 · 973·970·968 선례] = 면책 승계만 · 이 세션 신규 행 = Q979[시체 런 감지 + 실패 사유 유실 봉합] = 파일 최대+1)   # 973:2 = 재베이스라인 260728 04:1x(워크플로 YAML 게이트 세션 — Q973이 **타 세션 두 행**[요약단축-2묶음-건별착지-스윕창 · news-summary-ai-image-toggle-5fqive]으로 origin/main에 이미 양쪽 박제 = 재부여 불가[내 행이 아니라 옮기면 [Q.NN] 1:1 참조가 깨진다 · 970·968·961 선례] = 면책 승계만 · 이 세션 신규 행 = Q976[워크플로 YAML 게이트 · 구 Q974가 동시 세션 경합에 밀려 재부여] = 파일 최대+1)   # 970:2 = 재베이스라인 260728 03:5x(요약단축 평의회 세션 — Q970이 **타 세션 두 행**[컷편집 리뷰 hml2kf · 극화 해부학 g0ctla]으로 origin/main에 이미 양쪽 박제 = `--fix-qnum` "재부여 불가" 반환[내 행이 아니라 옮기면 [Q.NN] 1:1 참조가 깨진다 · 968·961·957 선례] = 면책 승계만 · 이 세션 신규 행 = Q971[요약단축 평의회 1묶음] = 파일 최대+1 자가 부여)   # 968:2 = 재베이스라인 260727 03:4x(극화 해부학 세션 — Q968이 **타 세션 두 행**[직접입력 UI · 컷편집 리뷰]으로 origin/main에 이미 양쪽 박제 = 빈 트리에서도 rc=1 실측 = `--fix-qnum` 무접촉 = 면책 승계만[961·957·950·946 선례] · 이 세션 신규 행 = Q970[극화 해부학·개연성 락] = 파일 최대+1 자가 부여)   # 961:2 = 재베이스라인 260727 22:5x(레딧 대분류 승격 세션 — Q961이 **타 세션 두 행**[파비콘 회전 · 상대 세션]으로 origin/main에 이미 양쪽 박제 = `--fix-qnum` "재부여 불가" 반환[내 행이 아니라 옮기면 [Q.NN] 1:1 참조가 깨진다 · 957·950·946 선례] = 면책 승계만 · 이 세션 신규 행 = Q962[레딧 대분류 5번 승격] = 파일 최대+1 자가 부여)   # ⟨머지 260727 22:4x⟩ 동시 세션이 같은 줄을 각자 늘려 충돌 → **키 합집합**으로 병합(어느 한쪽을 취하면 상대 면책이 소실 = 다음 커밋이 그 번호로 rc=1 · 선례 = 260727 21:5x·20:2x 머지 주석). 아래는 양쪽 사유 주석 전량 보존.   # 957:2 = 재베이스라인 260727 22:3x(내 직전 행[음원 마스터링 2단]과 타 세션 행이 같은 분에 각자 Q957로 머지 = **양쪽 다 origin/main 박제 → 재부여 불가**[내 행도 이미 박제라 옮기면 [Q.NN] 참조가 깨진다] = 면책 승계만[946·942·939 선례] · 이 세션 신규 행 = Q958[생성 게이지 2축] = 파일 최대+1)   # 957:2 = 재베이스라인 260727 22:2x(알림 종류별 로고 세션 — 타 세션 **두 곳**[음원 마스터링 2단 · 영상스튜디오 프레임 불투명판]이 서로 같은 번호로 origin/main 박제 · **둘 다 내 행이 아니라 재부여 불가**[옮기면 [Q.NN] 1:1 참조가 깨진다 · 950·942·939 선례] = 면책 승계만 · 이 세션 신규 행 = Q959[파일 최대+1 자가 부여] 유일)   # ⟨머지 260727 21:5x⟩ 동시 세션이 같은 줄을 각자 늘려 충돌 → **키 합집합**으로 병합(어느 한쪽을 취하면 상대 면책이 소실 = 다음 커밋이 그 번호로 rc=1 · 선례 = 260727 20:2x·19:3x 머지 주석). 아래는 양쪽 사유 주석 전량 보존.   # 942:2·946:2 = 재베이스라인 260727 21:3x(둘 다 origin/main 박제된 **타 세션 행** — 942 = 레고 기본 엔진 반전 vs 파비콘 알림 카테고라이징이 같은 번호로 착지 · 946 = 루시봇 관리화면 vs 파비콘 알림 검증이 동일 · `--fix-qnum`이 "재부여 불가"로 반환[내 행이 아니라 옮기면 [Q.NN] 참조가 깨진다] = 면책 승계만[939·936·934 선례] · 이 세션 신규 행 = Q948[음원 마스터링 이식] = 파일 최대+1 자가 부여)   # 950:2 = 재베이스라인 260727 21:5x(화면번쩍임 세션 — 크론이 분 단위로 main을 밀어 리베이스가 4회 반복되는 사이 타 세션 「한 수 회수」 행이 Q950으로 먼저 박제 · 내 행[화면-번쩍임-스튜디오-가드누락]도 #3174 머지로 동시 박제 = **양쪽 머지 → --fix-qnum 재부여 불가**[옮기면 [Q.NN] 1:1 참조가 깨진다 · 939 선례] = 면책 승계만 · 다음 부여 = 파일 최대+1)   # 942·946:2 = 재베이스라인 260727 21:4x(루시봇 화면 세션 — 동시 세션이 같은 번호를 먼저 main 박제 · 재부여 불가[양쪽 머지 · 611 선례] · 본 세션 신규 행 = --fix-qnum이 Q948로 재부여[루시봇화면-메뉴4골격복사] 유일 · 다음 부여 = 파일 최대+1)   # ⟨머지 260727 21:4x⟩ 동시 세션이 **같은 키(942·946)를 각자 추가** → 키 합집합 = 동일(증가 0) · 규약대로 양쪽 사유 주석 전량 보존. 화면번쩍임 세션 사유 = 운영자가 동일 축 작업을 다수 세션에 병렬 배포 → Q942[레고 엔진 반전 ↔ favicon-notification]·Q946[루시봇 관리화면 ↔ favicon 알림 5종]이 각자 origin/main 박제 ×2 실측 · **둘 다 내 행이 아니라 재부여 불가**[--fix-qnum 「미처리 · 양쪽 머지」 판정] = 면책 승계만[939·936·934 선례]   # 937:2·938:2 = 재베이스라인 260727 20:5x(운영자가 동일 지시[한 수 되돌리기·정리]를 다수 세션에 동시 배포 → 같은 작업이 여러 원장 행으로 겹쳐 착지 · origin/main 박제 = 재부여 불가 · **내 행이 아님**[본 세션 = Q940] = 면책 승계만)   # 939:2 = 재베이스라인 260727 21:0x(내 행['(다시)' 표식 되돌림]과 타 세션 행이 같은 분에 각자 Q939로 머지 = **양쪽 다 origin/main 박제 → 재부여 불가**[ⓑ 무접촉 원칙 · 내 행도 이미 박제라 옮기면 [Q.NN] 참조가 깨진다] = 면책 승계만[936·934·928 선례] · 이 세션 신규 행 0 · 다음 부여 = 파일 최대+1)   # 936:2 = 재베이스라인 260727 20:5x(타 세션 2행 — 프롬프트 생성 버튼 무반응 봉합[큐 4822행]과 notification-handling 원상복구[4875행]가 각자 origin/main 박제 ×2 실측 · **둘 다 내 행이 아니라 재부여 불가** = 면책 승계만[934·928·918 선례] · 본 세션 신규 행 = Q937['(다시)' 표식 되돌림 — 내 행이라 Q934→Q935→Q937 자가 재부여] · 다음 부여 = 파일 최대+1)   # ⟨머지 260727 20:3x⟩ 동시 세션 충돌 → 키 합집합 병합(내 단독 = [930] · 타 세션 단독 = []). 양쪽 사유 주석 전량 보존.   # 930:2·933:2·934:3 = 재베이스라인 260727 20:2x(타 세션 행들이 origin/main 박제 — 내 신규 행은 --fix-qnum이 Q930→Q935 이동 완료 · 잔여 중복은 전부 타 세션 박제라 재부여 불가 = 면책 승계만[928·918·912 선례] · 다음 부여 = 파일 최대+1)   # ⟨머지 260727 20:2x⟩ 동시 세션 충돌 → 키 합집합 병합(내 단독 = [] · 타 세션 단독 = []). 양쪽 사유 주석 전량 보존.   # ⟨머지 260727 19:3x⟩ 동시 세션이 같은 줄을 각자 늘려 충돌 → **키 합집합**으로 병합(어느 한쪽을 취하면 상대 면책이 소실 = 다음 커밋이 그 번호로 rc=1 · 선례 = 260727 17:2x 머지 주석). 아래는 양쪽 사유 주석 전량 보존.   # 933:3·935:2 = 재베이스라인 260727 21:0x(운영자가 동일 지시[한 수 되돌리기]를 다수 세션에 동시 배포 → 같은 작업이 여러 원장 행으로 겹쳐 착지 · 전부 origin/main 박제 = 재부여 불가 · **내 행이 아님**[본 세션 = Q931] = 면책 승계만)   # 928:2 = 재베이스라인 260727 20:0x(타 세션 2행 — 카드 생성 버튼 대기열 이징 스크롤[큐 4838행]과 헤더 지구본 회전 철거+파비콘 스핀 봉합[큐 4845행]이 각자 origin/main 박제 ×2 실측 · **둘 다 내 행이 아니라 재부여 불가** = 면책 승계만[918·912·687 선례] · 본 세션 신규 행 = Q930[돋보기 가로 잉크중심 정렬] · 다음 부여 = 파일 최대+1)   # 918:2 = 재베이스라인 260727 19:0x(타 세션 2행 — news-alert-download-7aliu6[큐 4767행]과 헤더-돋보기80%-잉크중심가로정렬[4774행]이 각자 origin/main 박제 ×2 실측 · **둘 다 내 행이 아니라 재부여 불가** = 면책 승계만[912·687·682 선례] · 본 세션 신규 행 = Q920~Q926[이미지 스튜디오 UI 6건]은 --fix-qnum이 전부 옆 번호로 이동 완료 · 다음 부여 = 파일 최대+1)   # 912:2 = 재베이스라인 260727 18:4x(타 세션 2행 — notification-handling-kh13gj[큐 4701행]과 훅-신선도경고-끝단재고지[4720행]가 각자 origin/main 박제 ×2 실측 · **둘 다 내 행이 아니라 재부여 불가** = 면책 승계만[687·682·670 선례] · 본 세션 신규 행 = Q913[진행 신호 4종 확장] 유일 · 다음 부여 = 파일 최대+1)   # ⟨머지 260727 17:2x⟩ 동시 세션이 같은 줄을 각자 늘려 충돌 → **키 합집합**으로 병합(어느 한쪽을 취하면 상대 면책이 소실 = 다음 커밋이 그 번호로 rc=1). 내 세션 단독 추가 = [] · 타 세션 단독 추가 = [688, 902]. 아래는 양쪽 사유 주석 전량 보존.   # 687:2 = 재베이스라인 260727 15:5x(타 세션 다수가 Q687을 동시 선점 — origin/main 실측 'Q687' 7회 · 게이트 계수 대상(`^- ✅ Q687·`) 2행이 각자 박제 · **둘 다 내 행이 아니라 재부여 불가** = 면책 승계만[682·670·656 선례] · 본 세션 신규 행 = Q902[파비콘 스핀 iframe 관통] 유일 · 다음 부여 = 파일 최대+1)   # 682:2 = 재베이스라인 260727 15:2x(타 세션 2행 — 알림 큰 아이콘 12안 플레이그라운드[큐 4502행 · 착수 중 Q679에서 개번]과 레딧-알림-기어경보[4525행]가 각자 origin/main 박제 ×2 실측 · **둘 다 내 행이 아니라 재부여 불가** = 면책 승계만[670·656·633 선례] · 본 세션 신규 행 = Q685[파비콘 스핀 배선 고도화] 유일 · 다음 부여 = 파일 최대+1)   # 681:2 = 재베이스라인 260727 15:1x(구조토큰 커버리지 게이트 세션 Q681[큐 4347행]과 레딧-403-RSS폴백 세션 Q681[큐 4516행]이 각자 origin/main 박제 ×2 실측[git show origin/main 계수 = 2] · 재부여 불가[양쪽 머지 · 670·656 선례] · --fix-qnum 자진 반려 = 면책 승계만 · 본 세션 신규 행 = Q684[미리보기 OPA 2장 좌/우 비교 · 구 Q678이 동시 세션 경합에 밀려 재부여] 유일 · 다음 부여 = 파일 최대+1)   # 670:2 = 재베이스라인 260727 14:4x(파비콘 스핀 배선 세션 Q670[본 세션 · PR #3085 머지분 · 구 Q662가 동시 세션 경합에 밀려 재부여한 것]과 타 세션 Q670["이거 다시 재시도 버튼 눌러도 작동을 안…"]이 각자 origin/main 박제 ×2 실측 · 재부여 불가[양쪽 머지 · 656·633 선례] · 본 세션 신규 행 = Q676[스핀 64px 경량화·fps 독립축 · 구 Q672가 재차 경합에 밀려 재부여] 유일 · 다음 부여 = 파일 최대+1)   # 656:2 = 재베이스라인 260727 12:5x(틱톡 하한 3만 세션 Q656[큐 4347행]과 유튜브 썸네일 회색판 봉합 세션 Q656[큐 4357행 · PR #3081]이 각자 origin/main 박제 ×2 실측 · 재부여 불가[양쪽 머지 · 633 선례] · --fix-qnum 자진 반려 = 면책 승계만 · 본 세션 신규 행 = Q661[파비콘 애니메이션 가능성 확인·플레이그라운드] 유일 · 다음 부여 = 파일 최대+1). ⚠ --fix-qnum이 타 세션 박제 행 Q657을 Q662로 재부여한 것을 손으로 원복함 = 도구 무접촉 판정이 forced-update 직후 스테일 base로 오작동한 사례(도구 수정은 별건 · 여기선 기록만)   # 633:2 = 재베이스라인 260727 08:2x(타 세션 Q633 2행[알림 상태바 배지·영상 예상시간]이 각자 origin/main 박제 ×2 실측 · --fix-qnum 자진 반려[양쪽 머지] = 면책 승계만[171·376·621·623 선례] · 본 세션 신규 행 = Q636[웹푸시 실발송 확인·관측 신설] 유일)   # Q01~Q12 +1 = 재베이스라인 260727 04:5x(운영자 12문단 지시를 UserPromptSubmit 훅 multi_intent가 `### 🧵 훅 기계 캡처` 블록으로 원장에 자동 append → 그 안 국소번호 Q01~Q12가 각 1 증가 · 원장 규칙 5 = 기계 캡처 국소번호는 스텁·개번 비대상[원문 보존] = 면책 승계만 · 본 세션 신규 행 = Q628 유일)   # 623:2 = 재베이스라인 260727 04:3x(본 세션 Q623[키워드 알림 작동 복구·PR #3065 머지분]과 타 세션 Q623이 각자 origin/main 박제 ×2 실측 · --fix-qnum 자진 반려["타 세션 행이라 재부여 불가(양쪽 머지)"] = 면책 승계만[171·376·621 선례] · 본 세션 신규 행 = Q626[키워드 알림 5열·기어 점등·웹푸시] 유일 = 중복 아님 · 다음 부여 = 파일 최대+1)   # 4:17·6:14·7:13·621:2 = 재베이스라인 260727 03:4x~03:5x(전부 origin/main 박제 · --fix-qnum 자진 반려[타 세션 행 = 양쪽 머지] = 면책 승계만[171·376 선례] · Q04·Q06·Q07 = 훅 기계 캡처 국소번호[원장 규칙 5 = 스텁·개번 비대상] 증가분 · Q621 ×2 = fb-demo-manual-asof[큐 4137행]·스튜디오 폼요소 활자[4143행] · 본 세션 신규 행 = Q623[키워드 알림 작동 복구·보라 전환 · 구 Q622가 #3064 활자 조용사 게이트 선점에 밀려 --fix-qnum 재부여] 유일 · 다음 부여 = 파일 최대+1)   # 4:17·621:2 = 재베이스라인 260727 03:4x(둘 다 origin/main 박제 실측 · --fix-qnum이 "타 세션 행이라 재부여 불가[양쪽 머지]"로 자진 반려 = 면책 승계만[171·376 선례] · Q621 ×2 = fb-demo-manual-asof 세션[큐 4137행]·스튜디오 폼요소 활자 세션[4143행] · Q04 = 훅 기계 캡처 국소번호 증가분 · 본 세션 신규 행 = Q622[키워드 알림 작동 복구·보라 전환] 유일 = 중복 아님 · 다음 부여 = 파일 최대+1)   # 613:2·614:4 = 재베이스라인 260727 02:2x(전부 origin/main 박제 실측[grep -c 'Q613'=2 · 'Q614'=4] · Q614 4행 = 스튜디오옵션바셸[큐 4050]·「진짜예요」템플릿[4057 = PR #3025 머지분]·insta-subs-cookie-wiring[4092 · Q611→614 재부여]·외 1 · 재부여 불가[전부 머지 · 611 선례] · 본 세션 신규 행 = 없음[Q614 행은 이미 머지된 내 것] = 면책 승계만[171·376 선례])   # 611:2 = 재베이스라인 260726 23:0x(X 큐레이션 카드 세션 Q611[큐 4040행]과 타 세션 Q611이 각자 main 박제 ×2 실측[origin/main grep -c 'Q611' = 2] · 재부여 불가[양쪽 머지 · 607 선례] · 본 세션 신규 행 = Q614[--fix-qnum 자동 재부여 · 진짜예요 템플릿 · 구 Q612가 타 세션 선점에 밀림] 유일 · 다음 부여 = Q615). ⚠ 612는 엔트리 미등재 — 내 행을 Q614로 재부여한 뒤 origin/main 실측 1(타 세션 단독)이라 중복 아님 = 356 선례의 "실측 1 = 엔트리 해제[번호 재사용 사각 차단]" 준수   # 614:2 = 재베이스라인 260726 23:4x(「진짜예요」 템플릿 세션 Q614[큐 4057행]와 insta-subs-cookie-wiring 세션 Q614[큐 4092행 · 구 Q611 재부여]가 각자 main 박제 ×2 실측[origin/main grep -c 'Q614' = 2] · 재부여 불가[양쪽 머지 · 611 선례] · 본 세션 신규 행 = Q616[폰 알림 로고 구판 잔존 봉합] 유일 · 다음 부여 = 파일 최대+1)   # 611:2 = 재베이스라인 260726 23:0x(타 세션 Q611 ×2가 origin/main 박제 · 재부여 불가[양쪽 머지 · 591 선례] · 본 세션 이번 커밋 = 원장 신규 Q행 0[Q613 기존 항목에 후속 불릿만 append] · 다음 부여 = 파일 최대+1)   # 591·607:2 = 재베이스라인 260726 22:5x(루시 스레드 자동운영 세션이 커밋 직전 파일 최대 590+1로 Q591을 잡았으나 동시 세션이 먼저 main 박제 · Q607도 타 세션 ×2 선존 · 둘 다 재부여 불가[양쪽 머지 · 575 선례] · 본 세션 신규 행 = --fix-qnum이 Q613으로 재부여[루시-스레드-자동운영-배선] 유일 · 다음 부여 = 파일 최대+1)   # 574·575:2 = 재베이스라인 260726 17:3x(라디얼스크림 세션 Q574[큐 3888행]와 트렌드 블릿제거 세션 Q574[큐 3909행] · 요약요청 옵션바 세션 Q575[큐 3901행 · 구 Q574를 #3012 선점에 밀려 개번]와 틱톡 KR이월 세션 Q575[큐 3912행]가 각자 main 박제 ×2 실측[origin/main grep -c '^- ✅ Q574'·'^- ✅ Q575' = 각 2] · 재부여 불가[전부 머지 · 569 선례] · 본 세션 신규 행 = Q579[헤더 우상단 픽토 부팅 점프 제거 · 구 Q575 → 3중 경합 재부여] 유일 · 다음 부여 = Q580)   # 569:2 = 재베이스라인 260726 14:0x(imgedit-cutout 세션 Q569[큐 16행 🔧 누끼]와 smoke-flaky-retry 세션 Q569[큐 3864행 ✅]가 각자 main 박제 ×2 실측[origin/main 파서 계수 = 2] · 재부여 불가[양쪽 머지] · 본 세션 신규 행 = Q572[자막 STT large-v3 승격] 유일 · 다음 부여 = Q573)   # 457:2 = 재베이스라인 260723(동시 세션 5선점 중 'Q457 ·' 포맷 2행[레거시피드병합-9czop4·favicon-7x21au]이 각자 main 박제 = 재부여 불가[양쪽 머지] · 나머지 3행 instagram·sync-media(파렌포맷)·내 Q457~461(range)은 게이트 정규식 비매치 · 다음 부여 = 파일 최대+1)   # 388:2 = 재베이스라인 260721 18:2x(틱톡 403 봉합 세션 Q388[구 Q376 재부여 · #2727 · 큐 2470행]과 반갈 분할선 세션 Q388[구 Q372 재부여 · #2728 · 큐 2570행]이 재부여까지 같은 번호에 착지[369·372 이중 경합과 같은 날 3연속] · 각자 main 박제 ×2 실측[origin/main grep -c '^- ✅ Q388' = 2] · 재부여 불가[양쪽 머지] · 다음 부여 = Q389)   # 376:2 = 재베이스라인 260721 14:27(금융 종목펜 큐잉 세션 Q376[#2731 9707ca2d · 큐 16행 ⬜ "종목 우측 펜"]과 채널요약 목업 세션 Q376[#2732 · 큐 2468행 ✅ "sns 지표 목업"]이 각자 main 박제 ×2 실측[origin/main grep -c = 2] · 재부여 불가[양쪽 머지 · 171 선례] · 본 세션 = 원장 무접촉 커밋[X 구독 24h 필터]이 게이트에 걸려 면책 승계만 · 다음 부여 = Q377)   # 372:2 = 재베이스라인 260721 12:5x(이중 경합 — 본 세션[수집 기사 직접 읽기 · #2723]과 구성 UI 세션[구 Q365 재부여 · 큐 2408행]이 재부여까지 같은 번호 착지·각자 main 박제 ×2 실측[origin/main grep -c = 2] · 재부여 불가[양쪽 머지 · 356 선례] · 다음 부여 = Q374)   # 369:2 = 재베이스라인 260721 12:4x(두 타 세션이 Q369에 경합 착지·각자 main 박제 ×2 실측[origin/main grep -c = 2] · 재부여 불가[양쪽 머지] · 본 세션 신규 행 = Q372[수집 기사 직접 읽기] 유일 · 다음 부여 = Q373)   # 356:2 = 재베이스라인 260721 11:0x(이중 경합 — 번역카드 세션[구 Q352 가부여 → Q356 재부여 · #2707 큐 2351행]과 금융 2x2 세션[구 Q352 → Q356 자진 재부여 · 큐 2326행]이 재부여까지 같은 번호에 착지·각자 main 박제 ×2 실측[origin/main grep -c = 2] · 재부여 불가[양쪽 머지 · 255/256 이중 경합 선례] · 구 352:2 면책[10:5x 본 세션 기입]은 금융 세션 자진 재부여로 실측 1 = 엔트리 해제[번호 재사용 사각 차단] · 다음 부여 = Q358)   # 322~324:2 = 재베이스라인 260720 23:1x(발사 매트릭스 세션 Q322~323[버튼 논리 점검·배치 라벨 정합 · 큐 2012·2015행]·SNS 트렌드 세션 Q322~324[X 반응 구분·기간 토글·한국 라벨 제거 · 큐 2154·2155·2158행]·모바일 도넛 세션 Q324[큐 2190행]가 각자 main 박제 ×2 실측[origin/main grep -c = 각 2] · 재부여 불가[전부 머지] · 본 세션 신규 행 = Q328[AI 생성 리드 = 도크·스트립 점등 파리티] 유일 · 다음 부여 = Q329)   # 306~308:2·309~310:3 = 재베이스라인 260720 22:5x(도넛·레일 세션이 Q306~310을 #2681로 선착 머지 → #2682에서 자진 Q311~315 재부여로 비웠으나, 그 사이 타 세션들[좌상단 시각 Q309·오늘의베스트 Q310 등]이 같은 번호로 각자 main 박제 ×2~×3 실측[origin/main grep -c = 2/2/2/3/3] · 재부여 불가[전부 머지] · 본 세션 신규 행 = Q324[모바일 도넛 교대] 유일 · 다음 부여 = Q325)   # 292:2 = 재베이스라인 260720 20:3x(평의회 후속수리 세션 Q292[큐 1954행 · 구 Q287→Q289 2차 재부여]와 독트린 이식 승인 세션 Q292[큐 1993행 · "머지해주셈"]가 각자 main 박제 ×2 실측[origin/main grep -c = 2] · 재부여 불가[양쪽 머지] · 본 세션 신규 행 = Q295[좌측 -3 통일] 유일·무관 · 다음 부여 = Q296) ·290·291:2 = 재베이스라인 260720 20:1x(Q290 = 팔로워대시 세션[큐 16행]·로딩픽토 세션[큐 1945행] · Q291 = dots로더 세션[큐 1949행]·생성독트린 세션[큐 1972행]이 각자 main 박제 ×2 실측[origin/main grep -c = 2] · 재부여 불가[양쪽 머지] · 본 세션 신규 행 = Q293[구 Q290 좌측 미세조정 → 3중 경합 재부여 · left -2.5·플레이그라운드] 유일 · 다음 부여 = Q294) · 289:2 = 재베이스라인 260720 20:0x(평의회 후속수리 세션 Q289[구 Q287 재부여 · 큐 1941행]과 아이콘 전환 세션 Q289[큐 1953행 · 19:46]가 각자 main 박제 ×2 실측[스테이시 후 grep -c = 2 = origin/main 자체 중복] · 재부여 불가[양쪽 머지] · 본 세션 신규 행 = Q291[생성 독트린 조문화 · 구 Q290 → 타 세션 재선점에 밀려 재부여] · 다음 부여 = Q292) · 271·272:2 = 재베이스라인 260720 15:2x(TOP편차 세션 Q271·Q272[큐 1790·1793행 — 구 Q01·Q02 스텁을 타 세션 Q263~264 선점에 밀려 재부여한 박제 · PR #2626]와 드라이브싱크 세션 Q271~Q272[훅캡처 게이트 지시 개번 · #2636]가 각자 main 박제 ×2 실측[origin/main grep -c = 2] · 재부여 불가[양쪽 머지] · 본 세션 신규 행 = Q273[구 훅캡처 Q01~12 → Q271 경합 재부여] 유일 · 다음 부여 = Q274) · 255·256:2 = 재베이스라인 260720 10:5x(정렬 스윕 세션 Q255[구 Q252 재부여]·Q256[한수 스모크]과 타 세션 Q255[구 Q258 재부여]·Q256이 각자 main 박제 ×2 실측[origin/main grep -c = 2] — 두 세션이 경합 재부여까지 같은 번호에 착지한 이중 경합 · 재부여 불가[양쪽 머지] · 본 세션 신규 행 = Q260[구 Q257 스텁 경합 재부여] 유일 · 다음 부여 = Q261) · 183:2 = 재베이스라인 260719 17:4x(07/18 4분할 스윕 세션 Q183[큐 1137행]과 채널 반응 유닛 세션 Q183[큐 1357행 · PR 2561]이 각자 main 박제 ×2 실측 · 재부여 불가[양쪽 머지] · 본 세션 신규 행 = Q184[Q183 경합 재부여] · 다음 부여 = Q185) · 171:2 = 재베이스라인 260719 16:17(한수 집행 승인 세션 Q171[1305행]과 가계정 쿠키 세션 Q171[1312행]이 각자 main 박제 ×2 실측 · 재부여 불가[양쪽 머지] · 본 세션 = 원장 무접촉 커밋[fb 진단 로깅]이 게이트에 걸려 면책 승계만) · 163:2 = 재베이스라인 260718 23:44(#2534 페북 30분 크론 Q163과 웹앱 전반 품질 세션 Q163이 각자 main 박제 ×2 실측[큐 1227·1235행] · 재부여 불가[양쪽 머지] · 본 세션 신규 행 = Q164 유일 · 다음 부여 = Q165) · 156:2 = 재베이스라인 260718 19:16(폰알람·채널분석 세션과 비디오 스튜디오 디자인 세션이 각자 main 박제 ×2 실측 · 재부여 불가[양쪽 머지] · 본 세션 신규 행 = Q159[Q155 경합 재부여] · 다음 부여 = Q160) · 142:2 = 재베이스라인 260718 18:35(#2505 핫픽스 리넘버 Q142[전사 폴오버]와 #2503 편집디자인 Q142가 각자 main 박제 ×2 실측[origin/main grep -c = 2] · 재부여 불가[양쪽 머지] · 본 세션 신규 행 = Q154 유일 · 다음 부여 = Q155) · 135·136:2 = 재베이스라인 260718 17:44(각 번호를 두 타 세션이 각자 main 박제 ×2 실측 · 재부여 불가[양쪽 머지] · 본 세션 신규 행 = Q147 유일 · 다음 부여 = Q148) · 132:2 = 재베이스라인 260718 16:30(Q132 ×2 — #2495 전사폴오버·#2496 옵션카드가 각자 진짜 main d8099fa에 머지 완료 = 박제 ×2 실측 · 재부여 불가[양쪽 박제] · 본 세션 신규 행 = Q133 · 다음 부여 = Q134 · 로컬 origin/main 스테일(2dde7be) 실측 오도 주의) · 43·49·63·64 :2 = 260717 병렬 머지 병존(각 번호를 두 세션이 각자 부여·둘 다 main 실재 = 갈래 유산 · 재부여 불가[양쪽 머지 완료]라 면책 기록 · 43=스크림#2422+편집알림 / 49=평의회분신술+PAT후속 / 63·64=동시 세션 원장 경합 · 91=요구사항 프로토콜#2458+22:05 규칙주입 동시 부여) · 161:2 = 재베이스라인 260718 23:09(규칙 6 머지와 같은 창의 과도기 경합 — #2514 세션 Q161과 타 세션 Q161이 각자 main 박제 ×2 실측 · 재부여 불가[양쪽 머지] · 신규칙 시행 전 착수 세션의 구규칙 마지막 충돌로 기록)   # 306·307·308:2 · 309·310:3 = 재베이스라인 260720 22:1x(트렌드 대분류 시각집약 세션 — 구글/시그널 실검·프로필 유닛개편(#2682 Q316~320) 등 타 세션 Q306~310이 각자 main 박제[origin/main grep -c: 309=3·310=3 실측] · 재부여 불가[전부 머지] · 본 세션 신규 행 = Q321[트렌드 시각 좌상단 집약] 유일·무관 · 다음 부여 = Q322) · 292:2 = 재베이스라인 260720 20:3x(평의회 후속수리 세션 Q292[큐 1954행 · 구 Q287→Q289 2차 재부여]와 독트린 이식 승인 세션 Q292[큐 1993행 · "머지해주셈"]가 각자 main 박제 ×2 실측[origin/main grep -c = 2] · 재부여 불가[양쪽 머지] · 본 세션 신규 행 = Q295[좌측 -3 통일] 유일·무관 · 다음 부여 = Q296) ·290·291:2 = 재베이스라인 260720 20:1x(Q290 = 팔로워대시 세션[큐 16행]·로딩픽토 세션[큐 1945행] · Q291 = dots로더 세션[큐 1949행]·생성독트린 세션[큐 1972행]이 각자 main 박제 ×2 실측[origin/main grep -c = 2] · 재부여 불가[양쪽 머지] · 본 세션 신규 행 = Q293[구 Q290 좌측 미세조정 → 3중 경합 재부여 · left -2.5·플레이그라운드] 유일 · 다음 부여 = Q294) · 289:2 = 재베이스라인 260720 20:0x(평의회 후속수리 세션 Q289[구 Q287 재부여 · 큐 1941행]과 아이콘 전환 세션 Q289[큐 1953행 · 19:46]가 각자 main 박제 ×2 실측[스테이시 후 grep -c = 2 = origin/main 자체 중복] · 재부여 불가[양쪽 머지] · 본 세션 신규 행 = Q291[생성 독트린 조문화 · 구 Q290 → 타 세션 재선점에 밀려 재부여] · 다음 부여 = Q292) · 271·272:2 = 재베이스라인 260720 15:2x(TOP편차 세션 Q271·Q272[큐 1790·1793행 — 구 Q01·Q02 스텁을 타 세션 Q263~264 선점에 밀려 재부여한 박제 · PR #2626]와 드라이브싱크 세션 Q271~Q272[훅캡처 게이트 지시 개번 · #2636]가 각자 main 박제 ×2 실측[origin/main grep -c = 2] · 재부여 불가[양쪽 머지] · 본 세션 신규 행 = Q273[구 훅캡처 Q01~12 → Q271 경합 재부여] 유일 · 다음 부여 = Q274) · 255·256:2 = 재베이스라인 260720 10:5x(정렬 스윕 세션 Q255[구 Q252 재부여]·Q256[한수 스모크]과 타 세션 Q255[구 Q258 재부여]·Q256이 각자 main 박제 ×2 실측[origin/main grep -c = 2] — 두 세션이 경합 재부여까지 같은 번호에 착지한 이중 경합 · 재부여 불가[양쪽 머지] · 본 세션 신규 행 = Q260[구 Q257 스텁 경합 재부여] 유일 · 다음 부여 = Q261) · 183:2 = 재베이스라인 260719 17:4x(07/18 4분할 스윕 세션 Q183[큐 1137행]과 채널 반응 유닛 세션 Q183[큐 1357행 · PR 2561]이 각자 main 박제 ×2 실측 · 재부여 불가[양쪽 머지] · 본 세션 신규 행 = Q184[Q183 경합 재부여] · 다음 부여 = Q185) · 171:2 = 재베이스라인 260719 16:17(한수 집행 승인 세션 Q171[1305행]과 가계정 쿠키 세션 Q171[1312행]이 각자 main 박제 ×2 실측 · 재부여 불가[양쪽 머지] · 본 세션 = 원장 무접촉 커밋[fb 진단 로깅]이 게이트에 걸려 면책 승계만) · 163:2 = 재베이스라인 260718 23:44(#2534 페북 30분 크론 Q163과 웹앱 전반 품질 세션 Q163이 각자 main 박제 ×2 실측[큐 1227·1235행] · 재부여 불가[양쪽 머지] · 본 세션 신규 행 = Q164 유일 · 다음 부여 = Q165) · 156:2 = 재베이스라인 260718 19:16(폰알람·채널분석 세션과 비디오 스튜디오 디자인 세션이 각자 main 박제 ×2 실측 · 재부여 불가[양쪽 머지] · 본 세션 신규 행 = Q159[Q155 경합 재부여] · 다음 부여 = Q160) · 142:2 = 재베이스라인 260718 18:35(#2505 핫픽스 리넘버 Q142[전사 폴오버]와 #2503 편집디자인 Q142가 각자 main 박제 ×2 실측[origin/main grep -c = 2] · 재부여 불가[양쪽 머지] · 본 세션 신규 행 = Q154 유일 · 다음 부여 = Q155) · 135·136:2 = 재베이스라인 260718 17:44(각 번호를 두 타 세션이 각자 main 박제 ×2 실측 · 재부여 불가[양쪽 머지] · 본 세션 신규 행 = Q147 유일 · 다음 부여 = Q148) · 132:2 = 재베이스라인 260718 16:30(Q132 ×2 — #2495 전사폴오버·#2496 옵션카드가 각자 진짜 main d8099fa에 머지 완료 = 박제 ×2 실측 · 재부여 불가[양쪽 박제] · 본 세션 신규 행 = Q133 · 다음 부여 = Q134 · 로컬 origin/main 스테일(2dde7be) 실측 오도 주의) · 43·49·63·64 :2 = 260717 병렬 머지 병존(각 번호를 두 세션이 각자 부여·둘 다 main 실재 = 갈래 유산 · 재부여 불가[양쪽 머지 완료]라 면책 기록 · 43=스크림#2422+편집알림 / 49=평의회분신술+PAT후속 / 63·64=동시 세션 원장 경합 · 91=요구사항 프로토콜#2458+22:05 규칙주입 동시 부여) · 161:2 = 재베이스라인 260718 23:09(규칙 6 머지와 같은 창의 과도기 경합 — #2514 세션 Q161과 타 세션 Q161이 각자 main 박제 ×2 실측 · 재부여 불가[양쪽 머지] · 신규칙 시행 전 착수 세션의 구규칙 마지막 충돌로 기록)   # 902:2 = 재베이스라인 260727 16:0x(theme_color 3면 시안 세션 Q902와 타 세션 Q902가 각자 main 박제 ×2 실측[origin/main grep -c "^- ✅ Q902" = 2] · 재부여 불가[양쪽 머지 · 676 선례] · 본 세션 신규 행 = Q903[--fix-qnum 재부여] 유일 · 다음 부여 = 파일 최대+1)   # 687:2·688:2 = 재베이스라인 260727 15:5x(원장·게이트 핫스팟 연속 레이스 — 링크원장 세션 Q687[#3107]·smoke_preview C10 세션 Q687[#3110], Q688도 동형으로 각자 origin/main 박제 ×2 실측 · --fix-qnum 자진 반려["타 세션 행이라 재부여 불가(양쪽 머지)"] = 면책 승계만[670·656·633 선례] · 본 세션 신규 행 = Q689[히스토리 칸 인계 일반화 · Q676→688→689 3연속 재부여] 유일 = 중복 아님 · 다음 부여 = 파일 최대+1)   # ⟨양쪽 보존 260727 18:5x⟩ 같은 Q912 면책을 두 세션이 각자 등재 = **키 합집합 동일**(79종 · 값 충돌 0)이라 어느 쪽을 취해도 면책 소실 0 → main 판을 취하고 이 세션의 실측 근거만 덧붙인다: 알림처리 Q912[큐 4700행]·훅-신선도경고 Q912[4719행] 각자 박제 ×2를 `git show origin/main:docs/요구사항_큐.md | grep -c '^- ✅ Q912'` = 2로 확인 · 본 세션 신규 행 = Q913(창 기준 중앙 하드게이트 = smoke_popup C8·C9).   # 918:2 = 재베이스라인 260727 19:2x(타 세션 2행 — news-alert-download-7aliu6[큐 4767행]과 헤더-돋보기80%-잉크중심가로정렬[4774행]이 각자 origin/main 박제 ×2 실측[git diff origin/main 신규 + 라인에 Q918 0건 = 내 행 아님] · **둘 다 내 행이 아니라 재부여 불가** = 면책 승계만[912·902·687 선례] · 본 세션 신규 행 = Q920[AI 생성 발사 후 폼 존속 · 구 Q914가 동시 세션 경합에 밀려 재부여] 유일 · 다음 부여 = 파일 최대+1)   # 933:2·934:3 = 재베이스라인 260727 20:3x(20개 세션 동시 가동 중 타 세션들이 같은 번호를 각자 박제 — `git show origin/main:docs/요구사항_큐.md | grep -cE '^- ✅ Q933'` = 2 · Q934 = 3 실측 · **전부 내 행이 아니라 재부여 불가**[양쪽 머지 · 912·902·687 선례] · `--fix-qnum` 자진 반려 = 면책 승계만 · 본 세션 신규 행 = Q935[한 수 채택분 전량 되돌림] 유일 · 다음 부여 = 파일 최대+1)   # ⟨머지 260727 22:3x⟩ 동시 세션이 같은 줄을 각자 늘려 충돌 → **키 합집합**으로 병합(선례 = 21:5x·21:4x 머지 주석) · 아래는 이쪽(요약요청 원본한정) 사유 전량 보존.   # 957:2 = 재베이스라인 260727 22:3x(요약요청 원본한정 세션 — 마스터링 2단[매크로+10밴드 EQ]·영상스튜디오 불투명판 승격 두 타 세션 행이 각자 Q957로 **origin/main 박제** ×2 실측 · 둘 다 내 행이 아니라 --fix-qnum 「미처리 · 양쪽 머지」 판정 = 재부여하면 [Q.NN] 1:1 참조가 깨진다 → 면책 승계만[950·942·939 선례] · 본 세션 신규 행 = --fix-qnum이 Q959로 재부여[요약요청 토글 확인] + Q958[원본 한정 신설] · 다음 부여 = 파일 최대+1)   # 961:2 = 재베이스라인 260727 22:4x(X 카드 사진·키워드·여백 세션 — 타 세션 **두 곳**[파비콘 로딩 애니 · 생성 게이지 2축]이 서로 같은 번호로 origin/main 박제 · **둘 다 내 행이 아니라 재부여 불가**[옮기면 [Q.NN] 1:1 참조가 깨진다 · 957·950·942 선례] = 면책 승계만 · 이 세션 신규 행 = Q962[X 인용·답글 사진 수집] = --fix-qnum 자동 재부여[Q960→Q962] 유일)   # ⟨머지 260727 22:5x⟩ 동시 세션이 같은 줄을 각자 늘려 충돌 → **키 합집합**으로 병합(어느 한쪽을 취하면 상대 면책이 소실 · 선례 = 260727 22:4x·21:5x 머지 주석).   # ⟨머지 260727 04:1x⟩ 동시 세션이 같은 줄을 각자 늘려 충돌 → **키 합집합**으로 병합(선례 문법 — 어느 한쪽을 취하면 상대 면책이 소실 = 다음 커밋이 그 번호로 rc=1). 양쪽 사유 주석 보존.   # ⟨머지 260728 04:5x⟩ 동시 세션이 같은 줄을 각자 늘려 충돌 → **키 합집합**(값은 큰 쪽)으로 병합 = 어느 한쪽을 취하면 상대 면책이 소실(선례 = 260727 22:5x·21:5x 머지 주석). 양쪽 사유 주석 전량 보존.   # 977:2 = 재베이스라인 260728 04:2x(컷편집 리뷰 hml2kf 세션 — Q977이 **타 세션 두 행**[요약단축-3차-소넷사진로봇-병렬 · claude/cardnews-line-limit-review-d8od84]으로 origin/main에 이미 양쪽 박제 = `--fix-qnum` 「미처리 Q977 — origin/main에 이미 박제된 타 세션 행이라 재부여 불가(양쪽 머지)」 실측 반환 = 면책 승계만[973·970·968·961 선례] · 이 세션 신규 행 = Q974·Q975[컷편집 강화 5종 · 필러 강도 3단] · 원장 파일 무접촉)   # 973:2 = 재베이스라인 260728 04:1x(워크플로 YAML 게이트 세션 — Q973이 **타 세션 두 행**[요약단축-2묶음-건별착지-스윕창 · news-summary-ai-image-toggle-5fqive]으로 origin/main에 이미 양쪽 박제 = 재부여 불가[내 행이 아니라 옮기면 [Q.NN] 1:1 참조가 깨진다 · 970·968·961 선례] = 면책 승계만 · 이 세션 신규 행 = Q976[워크플로 YAML 게이트 · 구 Q974가 동시 세션 경합에 밀려 재부여] = 파일 최대+1)   # 970:2 = 재베이스라인 260728 03:5x(요약단축 평의회 세션 — Q970이 **타 세션 두 행**[컷편집 리뷰 hml2kf · 극화 해부학 g0ctla]으로 origin/main에 이미 양쪽 박제 = `--fix-qnum` "재부여 불가" 반환[내 행이 아니라 옮기면 [Q.NN] 1:1 참조가 깨진다 · 968·961·957 선례] = 면책 승계만 · 이 세션 신규 행 = Q971[요약단축 평의회 1묶음] = 파일 최대+1 자가 부여)   # 968:2 = 재베이스라인 260727 03:4x(극화 해부학 세션 — Q968이 **타 세션 두 행**[직접입력 UI · 컷편집 리뷰]으로 origin/main에 이미 양쪽 박제 = 빈 트리에서도 rc=1 실측 = `--fix-qnum` 무접촉 = 면책 승계만[961·957·950·946 선례] · 이 세션 신규 행 = Q970[극화 해부학·개연성 락] = 파일 최대+1 자가 부여)   # 961:2 = 재베이스라인 260727 22:5x(레딧 대분류 승격 세션 — Q961이 **타 세션 두 행**[파비콘 회전 · 상대 세션]으로 origin/main에 이미 양쪽 박제 = `--fix-qnum` "재부여 불가" 반환[내 행이 아니라 옮기면 [Q.NN] 1:1 참조가 깨진다 · 957·950·946 선례] = 면책 승계만 · 이 세션 신규 행 = Q962[레딧 대분류 5번 승격] = 파일 최대+1 자가 부여)   # ⟨머지 260727 22:4x⟩ 동시 세션이 같은 줄을 각자 늘려 충돌 → **키 합집합**으로 병합(어느 한쪽을 취하면 상대 면책이 소실 = 다음 커밋이 그 번호로 rc=1 · 선례 = 260727 21:5x·20:2x 머지 주석). 아래는 양쪽 사유 주석 전량 보존.   # 957:2 = 재베이스라인 260727 22:3x(내 직전 행[음원 마스터링 2단]과 타 세션 행이 같은 분에 각자 Q957로 머지 = **양쪽 다 origin/main 박제 → 재부여 불가**[내 행도 이미 박제라 옮기면 [Q.NN] 참조가 깨진다] = 면책 승계만[946·942·939 선례] · 이 세션 신규 행 = Q958[생성 게이지 2축] = 파일 최대+1)   # 957:2 = 재베이스라인 260727 22:2x(알림 종류별 로고 세션 — 타 세션 **두 곳**[음원 마스터링 2단 · 영상스튜디오 프레임 불투명판]이 서로 같은 번호로 origin/main 박제 · **둘 다 내 행이 아니라 재부여 불가**[옮기면 [Q.NN] 1:1 참조가 깨진다 · 950·942·939 선례] = 면책 승계만 · 이 세션 신규 행 = Q959[파일 최대+1 자가 부여] 유일)   # ⟨머지 260727 21:5x⟩ 동시 세션이 같은 줄을 각자 늘려 충돌 → **키 합집합**으로 병합(어느 한쪽을 취하면 상대 면책이 소실 = 다음 커밋이 그 번호로 rc=1 · 선례 = 260727 20:2x·19:3x 머지 주석). 아래는 양쪽 사유 주석 전량 보존.   # 942:2·946:2 = 재베이스라인 260727 21:3x(둘 다 origin/main 박제된 **타 세션 행** — 942 = 레고 기본 엔진 반전 vs 파비콘 알림 카테고라이징이 같은 번호로 착지 · 946 = 루시봇 관리화면 vs 파비콘 알림 검증이 동일 · `--fix-qnum`이 "재부여 불가"로 반환[내 행이 아니라 옮기면 [Q.NN] 참조가 깨진다] = 면책 승계만[939·936·934 선례] · 이 세션 신규 행 = Q948[음원 마스터링 이식] = 파일 최대+1 자가 부여)   # 950:2 = 재베이스라인 260727 21:5x(화면번쩍임 세션 — 크론이 분 단위로 main을 밀어 리베이스가 4회 반복되는 사이 타 세션 「한 수 회수」 행이 Q950으로 먼저 박제 · 내 행[화면-번쩍임-스튜디오-가드누락]도 #3174 머지로 동시 박제 = **양쪽 머지 → --fix-qnum 재부여 불가**[옮기면 [Q.NN] 1:1 참조가 깨진다 · 939 선례] = 면책 승계만 · 다음 부여 = 파일 최대+1)   # 942·946:2 = 재베이스라인 260727 21:4x(루시봇 화면 세션 — 동시 세션이 같은 번호를 먼저 main 박제 · 재부여 불가[양쪽 머지 · 611 선례] · 본 세션 신규 행 = --fix-qnum이 Q948로 재부여[루시봇화면-메뉴4골격복사] 유일 · 다음 부여 = 파일 최대+1)   # ⟨머지 260727 21:4x⟩ 동시 세션이 **같은 키(942·946)를 각자 추가** → 키 합집합 = 동일(증가 0) · 규약대로 양쪽 사유 주석 전량 보존. 화면번쩍임 세션 사유 = 운영자가 동일 축 작업을 다수 세션에 병렬 배포 → Q942[레고 엔진 반전 ↔ favicon-notification]·Q946[루시봇 관리화면 ↔ favicon 알림 5종]이 각자 origin/main 박제 ×2 실측 · **둘 다 내 행이 아니라 재부여 불가**[--fix-qnum 「미처리 · 양쪽 머지」 판정] = 면책 승계만[939·936·934 선례]   # 937:2·938:2 = 재베이스라인 260727 20:5x(운영자가 동일 지시[한 수 되돌리기·정리]를 다수 세션에 동시 배포 → 같은 작업이 여러 원장 행으로 겹쳐 착지 · origin/main 박제 = 재부여 불가 · **내 행이 아님**[본 세션 = Q940] = 면책 승계만)   # 939:2 = 재베이스라인 260727 21:0x(내 행['(다시)' 표식 되돌림]과 타 세션 행이 같은 분에 각자 Q939로 머지 = **양쪽 다 origin/main 박제 → 재부여 불가**[ⓑ 무접촉 원칙 · 내 행도 이미 박제라 옮기면 [Q.NN] 참조가 깨진다] = 면책 승계만[936·934·928 선례] · 이 세션 신규 행 0 · 다음 부여 = 파일 최대+1)   # 936:2 = 재베이스라인 260727 20:5x(타 세션 2행 — 프롬프트 생성 버튼 무반응 봉합[큐 4822행]과 notification-handling 원상복구[4875행]가 각자 origin/main 박제 ×2 실측 · **둘 다 내 행이 아니라 재부여 불가** = 면책 승계만[934·928·918 선례] · 본 세션 신규 행 = Q937['(다시)' 표식 되돌림 — 내 행이라 Q934→Q935→Q937 자가 재부여] · 다음 부여 = 파일 최대+1)   # ⟨머지 260727 20:3x⟩ 동시 세션 충돌 → 키 합집합 병합(내 단독 = [930] · 타 세션 단독 = []). 양쪽 사유 주석 전량 보존.   # 930:2·933:2·934:3 = 재베이스라인 260727 20:2x(타 세션 행들이 origin/main 박제 — 내 신규 행은 --fix-qnum이 Q930→Q935 이동 완료 · 잔여 중복은 전부 타 세션 박제라 재부여 불가 = 면책 승계만[928·918·912 선례] · 다음 부여 = 파일 최대+1)   # ⟨머지 260727 20:2x⟩ 동시 세션 충돌 → 키 합집합 병합(내 단독 = [] · 타 세션 단독 = []). 양쪽 사유 주석 전량 보존.   # ⟨머지 260727 19:3x⟩ 동시 세션이 같은 줄을 각자 늘려 충돌 → **키 합집합**으로 병합(어느 한쪽을 취하면 상대 면책이 소실 = 다음 커밋이 그 번호로 rc=1 · 선례 = 260727 17:2x 머지 주석). 아래는 양쪽 사유 주석 전량 보존.   # 933:3·935:2 = 재베이스라인 260727 21:0x(운영자가 동일 지시[한 수 되돌리기]를 다수 세션에 동시 배포 → 같은 작업이 여러 원장 행으로 겹쳐 착지 · 전부 origin/main 박제 = 재부여 불가 · **내 행이 아님**[본 세션 = Q931] = 면책 승계만)   # 928:2 = 재베이스라인 260727 20:0x(타 세션 2행 — 카드 생성 버튼 대기열 이징 스크롤[큐 4838행]과 헤더 지구본 회전 철거+파비콘 스핀 봉합[큐 4845행]이 각자 origin/main 박제 ×2 실측 · **둘 다 내 행이 아니라 재부여 불가** = 면책 승계만[918·912·687 선례] · 본 세션 신규 행 = Q930[돋보기 가로 잉크중심 정렬] · 다음 부여 = 파일 최대+1)   # 918:2 = 재베이스라인 260727 19:0x(타 세션 2행 — news-alert-download-7aliu6[큐 4767행]과 헤더-돋보기80%-잉크중심가로정렬[4774행]이 각자 origin/main 박제 ×2 실측 · **둘 다 내 행이 아니라 재부여 불가** = 면책 승계만[912·687·682 선례] · 본 세션 신규 행 = Q920~Q926[이미지 스튜디오 UI 6건]은 --fix-qnum이 전부 옆 번호로 이동 완료 · 다음 부여 = 파일 최대+1)   # 912:2 = 재베이스라인 260727 18:4x(타 세션 2행 — notification-handling-kh13gj[큐 4701행]과 훅-신선도경고-끝단재고지[4720행]가 각자 origin/main 박제 ×2 실측 · **둘 다 내 행이 아니라 재부여 불가** = 면책 승계만[687·682·670 선례] · 본 세션 신규 행 = Q913[진행 신호 4종 확장] 유일 · 다음 부여 = 파일 최대+1)   # ⟨머지 260727 17:2x⟩ 동시 세션이 같은 줄을 각자 늘려 충돌 → **키 합집합**으로 병합(어느 한쪽을 취하면 상대 면책이 소실 = 다음 커밋이 그 번호로 rc=1). 내 세션 단독 추가 = [] · 타 세션 단독 추가 = [688, 902]. 아래는 양쪽 사유 주석 전량 보존.   # 687:2 = 재베이스라인 260727 15:5x(타 세션 다수가 Q687을 동시 선점 — origin/main 실측 'Q687' 7회 · 게이트 계수 대상(`^- ✅ Q687·`) 2행이 각자 박제 · **둘 다 내 행이 아니라 재부여 불가** = 면책 승계만[682·670·656 선례] · 본 세션 신규 행 = Q902[파비콘 스핀 iframe 관통] 유일 · 다음 부여 = 파일 최대+1)   # 682:2 = 재베이스라인 260727 15:2x(타 세션 2행 — 알림 큰 아이콘 12안 플레이그라운드[큐 4502행 · 착수 중 Q679에서 개번]과 레딧-알림-기어경보[4525행]가 각자 origin/main 박제 ×2 실측 · **둘 다 내 행이 아니라 재부여 불가** = 면책 승계만[670·656·633 선례] · 본 세션 신규 행 = Q685[파비콘 스핀 배선 고도화] 유일 · 다음 부여 = 파일 최대+1)   # 681:2 = 재베이스라인 260727 15:1x(구조토큰 커버리지 게이트 세션 Q681[큐 4347행]과 레딧-403-RSS폴백 세션 Q681[큐 4516행]이 각자 origin/main 박제 ×2 실측[git show origin/main 계수 = 2] · 재부여 불가[양쪽 머지 · 670·656 선례] · --fix-qnum 자진 반려 = 면책 승계만 · 본 세션 신규 행 = Q684[미리보기 OPA 2장 좌/우 비교 · 구 Q678이 동시 세션 경합에 밀려 재부여] 유일 · 다음 부여 = 파일 최대+1)   # 670:2 = 재베이스라인 260727 14:4x(파비콘 스핀 배선 세션 Q670[본 세션 · PR #3085 머지분 · 구 Q662가 동시 세션 경합에 밀려 재부여한 것]과 타 세션 Q670["이거 다시 재시도 버튼 눌러도 작동을 안…"]이 각자 origin/main 박제 ×2 실측 · 재부여 불가[양쪽 머지 · 656·633 선례] · 본 세션 신규 행 = Q676[스핀 64px 경량화·fps 독립축 · 구 Q672가 재차 경합에 밀려 재부여] 유일 · 다음 부여 = 파일 최대+1)   # 656:2 = 재베이스라인 260727 12:5x(틱톡 하한 3만 세션 Q656[큐 4347행]과 유튜브 썸네일 회색판 봉합 세션 Q656[큐 4357행 · PR #3081]이 각자 origin/main 박제 ×2 실측 · 재부여 불가[양쪽 머지 · 633 선례] · --fix-qnum 자진 반려 = 면책 승계만 · 본 세션 신규 행 = Q661[파비콘 애니메이션 가능성 확인·플레이그라운드] 유일 · 다음 부여 = 파일 최대+1). ⚠ --fix-qnum이 타 세션 박제 행 Q657을 Q662로 재부여한 것을 손으로 원복함 = 도구 무접촉 판정이 forced-update 직후 스테일 base로 오작동한 사례(도구 수정은 별건 · 여기선 기록만)   # 633:2 = 재베이스라인 260727 08:2x(타 세션 Q633 2행[알림 상태바 배지·영상 예상시간]이 각자 origin/main 박제 ×2 실측 · --fix-qnum 자진 반려[양쪽 머지] = 면책 승계만[171·376·621·623 선례] · 본 세션 신규 행 = Q636[웹푸시 실발송 확인·관측 신설] 유일)   # Q01~Q12 +1 = 재베이스라인 260727 04:5x(운영자 12문단 지시를 UserPromptSubmit 훅 multi_intent가 `### 🧵 훅 기계 캡처` 블록으로 원장에 자동 append → 그 안 국소번호 Q01~Q12가 각 1 증가 · 원장 규칙 5 = 기계 캡처 국소번호는 스텁·개번 비대상[원문 보존] = 면책 승계만 · 본 세션 신규 행 = Q628 유일)   # 623:2 = 재베이스라인 260727 04:3x(본 세션 Q623[키워드 알림 작동 복구·PR #3065 머지분]과 타 세션 Q623이 각자 origin/main 박제 ×2 실측 · --fix-qnum 자진 반려["타 세션 행이라 재부여 불가(양쪽 머지)"] = 면책 승계만[171·376·621 선례] · 본 세션 신규 행 = Q626[키워드 알림 5열·기어 점등·웹푸시] 유일 = 중복 아님 · 다음 부여 = 파일 최대+1)   # 4:17·6:14·7:13·621:2 = 재베이스라인 260727 03:4x~03:5x(전부 origin/main 박제 · --fix-qnum 자진 반려[타 세션 행 = 양쪽 머지] = 면책 승계만[171·376 선례] · Q04·Q06·Q07 = 훅 기계 캡처 국소번호[원장 규칙 5 = 스텁·개번 비대상] 증가분 · Q621 ×2 = fb-demo-manual-asof[큐 4137행]·스튜디오 폼요소 활자[4143행] · 본 세션 신규 행 = Q623[키워드 알림 작동 복구·보라 전환 · 구 Q622가 #3064 활자 조용사 게이트 선점에 밀려 --fix-qnum 재부여] 유일 · 다음 부여 = 파일 최대+1)   # 4:17·621:2 = 재베이스라인 260727 03:4x(둘 다 origin/main 박제 실측 · --fix-qnum이 "타 세션 행이라 재부여 불가[양쪽 머지]"로 자진 반려 = 면책 승계만[171·376 선례] · Q621 ×2 = fb-demo-manual-asof 세션[큐 4137행]·스튜디오 폼요소 활자 세션[4143행] · Q04 = 훅 기계 캡처 국소번호 증가분 · 본 세션 신규 행 = Q622[키워드 알림 작동 복구·보라 전환] 유일 = 중복 아님 · 다음 부여 = 파일 최대+1)   # 613:2·614:4 = 재베이스라인 260727 02:2x(전부 origin/main 박제 실측[grep -c 'Q613'=2 · 'Q614'=4] · Q614 4행 = 스튜디오옵션바셸[큐 4050]·「진짜예요」템플릿[4057 = PR #3025 머지분]·insta-subs-cookie-wiring[4092 · Q611→614 재부여]·외 1 · 재부여 불가[전부 머지 · 611 선례] · 본 세션 신규 행 = 없음[Q614 행은 이미 머지된 내 것] = 면책 승계만[171·376 선례])   # 611:2 = 재베이스라인 260726 23:0x(X 큐레이션 카드 세션 Q611[큐 4040행]과 타 세션 Q611이 각자 main 박제 ×2 실측[origin/main grep -c 'Q611' = 2] · 재부여 불가[양쪽 머지 · 607 선례] · 본 세션 신규 행 = Q614[--fix-qnum 자동 재부여 · 진짜예요 템플릿 · 구 Q612가 타 세션 선점에 밀림] 유일 · 다음 부여 = Q615). ⚠ 612는 엔트리 미등재 — 내 행을 Q614로 재부여한 뒤 origin/main 실측 1(타 세션 단독)이라 중복 아님 = 356 선례의 "실측 1 = 엔트리 해제[번호 재사용 사각 차단]" 준수   # 614:2 = 재베이스라인 260726 23:4x(「진짜예요」 템플릿 세션 Q614[큐 4057행]와 insta-subs-cookie-wiring 세션 Q614[큐 4092행 · 구 Q611 재부여]가 각자 main 박제 ×2 실측[origin/main grep -c 'Q614' = 2] · 재부여 불가[양쪽 머지 · 611 선례] · 본 세션 신규 행 = Q616[폰 알림 로고 구판 잔존 봉합] 유일 · 다음 부여 = 파일 최대+1)   # 611:2 = 재베이스라인 260726 23:0x(타 세션 Q611 ×2가 origin/main 박제 · 재부여 불가[양쪽 머지 · 591 선례] · 본 세션 이번 커밋 = 원장 신규 Q행 0[Q613 기존 항목에 후속 불릿만 append] · 다음 부여 = 파일 최대+1)   # 591·607:2 = 재베이스라인 260726 22:5x(루시 스레드 자동운영 세션이 커밋 직전 파일 최대 590+1로 Q591을 잡았으나 동시 세션이 먼저 main 박제 · Q607도 타 세션 ×2 선존 · 둘 다 재부여 불가[양쪽 머지 · 575 선례] · 본 세션 신규 행 = --fix-qnum이 Q613으로 재부여[루시-스레드-자동운영-배선] 유일 · 다음 부여 = 파일 최대+1)   # 574·575:2 = 재베이스라인 260726 17:3x(라디얼스크림 세션 Q574[큐 3888행]와 트렌드 블릿제거 세션 Q574[큐 3909행] · 요약요청 옵션바 세션 Q575[큐 3901행 · 구 Q574를 #3012 선점에 밀려 개번]와 틱톡 KR이월 세션 Q575[큐 3912행]가 각자 main 박제 ×2 실측[origin/main grep -c '^- ✅ Q574'·'^- ✅ Q575' = 각 2] · 재부여 불가[전부 머지 · 569 선례] · 본 세션 신규 행 = Q579[헤더 우상단 픽토 부팅 점프 제거 · 구 Q575 → 3중 경합 재부여] 유일 · 다음 부여 = Q580)   # 569:2 = 재베이스라인 260726 14:0x(imgedit-cutout 세션 Q569[큐 16행 🔧 누끼]와 smoke-flaky-retry 세션 Q569[큐 3864행 ✅]가 각자 main 박제 ×2 실측[origin/main 파서 계수 = 2] · 재부여 불가[양쪽 머지] · 본 세션 신규 행 = Q572[자막 STT large-v3 승격] 유일 · 다음 부여 = Q573)   # 457:2 = 재베이스라인 260723(동시 세션 5선점 중 'Q457 ·' 포맷 2행[레거시피드병합-9czop4·favicon-7x21au]이 각자 main 박제 = 재부여 불가[양쪽 머지] · 나머지 3행 instagram·sync-media(파렌포맷)·내 Q457~461(range)은 게이트 정규식 비매치 · 다음 부여 = 파일 최대+1)   # 388:2 = 재베이스라인 260721 18:2x(틱톡 403 봉합 세션 Q388[구 Q376 재부여 · #2727 · 큐 2470행]과 반갈 분할선 세션 Q388[구 Q372 재부여 · #2728 · 큐 2570행]이 재부여까지 같은 번호에 착지[369·372 이중 경합과 같은 날 3연속] · 각자 main 박제 ×2 실측[origin/main grep -c '^- ✅ Q388' = 2] · 재부여 불가[양쪽 머지] · 다음 부여 = Q389)   # 376:2 = 재베이스라인 260721 14:27(금융 종목펜 큐잉 세션 Q376[#2731 9707ca2d · 큐 16행 ⬜ "종목 우측 펜"]과 채널요약 목업 세션 Q376[#2732 · 큐 2468행 ✅ "sns 지표 목업"]이 각자 main 박제 ×2 실측[origin/main grep -c = 2] · 재부여 불가[양쪽 머지 · 171 선례] · 본 세션 = 원장 무접촉 커밋[X 구독 24h 필터]이 게이트에 걸려 면책 승계만 · 다음 부여 = Q377)   # 372:2 = 재베이스라인 260721 12:5x(이중 경합 — 본 세션[수집 기사 직접 읽기 · #2723]과 구성 UI 세션[구 Q365 재부여 · 큐 2408행]이 재부여까지 같은 번호 착지·각자 main 박제 ×2 실측[origin/main grep -c = 2] · 재부여 불가[양쪽 머지 · 356 선례] · 다음 부여 = Q374)   # 369:2 = 재베이스라인 260721 12:4x(두 타 세션이 Q369에 경합 착지·각자 main 박제 ×2 실측[origin/main grep -c = 2] · 재부여 불가[양쪽 머지] · 본 세션 신규 행 = Q372[수집 기사 직접 읽기] 유일 · 다음 부여 = Q373)   # 356:2 = 재베이스라인 260721 11:0x(이중 경합 — 번역카드 세션[구 Q352 가부여 → Q356 재부여 · #2707 큐 2351행]과 금융 2x2 세션[구 Q352 → Q356 자진 재부여 · 큐 2326행]이 재부여까지 같은 번호에 착지·각자 main 박제 ×2 실측[origin/main grep -c = 2] · 재부여 불가[양쪽 머지 · 255/256 이중 경합 선례] · 구 352:2 면책[10:5x 본 세션 기입]은 금융 세션 자진 재부여로 실측 1 = 엔트리 해제[번호 재사용 사각 차단] · 다음 부여 = Q358)   # 322~324:2 = 재베이스라인 260720 23:1x(발사 매트릭스 세션 Q322~323[버튼 논리 점검·배치 라벨 정합 · 큐 2012·2015행]·SNS 트렌드 세션 Q322~324[X 반응 구분·기간 토글·한국 라벨 제거 · 큐 2154·2155·2158행]·모바일 도넛 세션 Q324[큐 2190행]가 각자 main 박제 ×2 실측[origin/main grep -c = 각 2] · 재부여 불가[전부 머지] · 본 세션 신규 행 = Q328[AI 생성 리드 = 도크·스트립 점등 파리티] 유일 · 다음 부여 = Q329)   # 306~308:2·309~310:3 = 재베이스라인 260720 22:5x(도넛·레일 세션이 Q306~310을 #2681로 선착 머지 → #2682에서 자진 Q311~315 재부여로 비웠으나, 그 사이 타 세션들[좌상단 시각 Q309·오늘의베스트 Q310 등]이 같은 번호로 각자 main 박제 ×2~×3 실측[origin/main grep -c = 2/2/2/3/3] · 재부여 불가[전부 머지] · 본 세션 신규 행 = Q324[모바일 도넛 교대] 유일 · 다음 부여 = Q325)   # 292:2 = 재베이스라인 260720 20:3x(평의회 후속수리 세션 Q292[큐 1954행 · 구 Q287→Q289 2차 재부여]와 독트린 이식 승인 세션 Q292[큐 1993행 · "머지해주셈"]가 각자 main 박제 ×2 실측[origin/main grep -c = 2] · 재부여 불가[양쪽 머지] · 본 세션 신규 행 = Q295[좌측 -3 통일] 유일·무관 · 다음 부여 = Q296) ·290·291:2 = 재베이스라인 260720 20:1x(Q290 = 팔로워대시 세션[큐 16행]·로딩픽토 세션[큐 1945행] · Q291 = dots로더 세션[큐 1949행]·생성독트린 세션[큐 1972행]이 각자 main 박제 ×2 실측[origin/main grep -c = 2] · 재부여 불가[양쪽 머지] · 본 세션 신규 행 = Q293[구 Q290 좌측 미세조정 → 3중 경합 재부여 · left -2.5·플레이그라운드] 유일 · 다음 부여 = Q294) · 289:2 = 재베이스라인 260720 20:0x(평의회 후속수리 세션 Q289[구 Q287 재부여 · 큐 1941행]과 아이콘 전환 세션 Q289[큐 1953행 · 19:46]가 각자 main 박제 ×2 실측[스테이시 후 grep -c = 2 = origin/main 자체 중복] · 재부여 불가[양쪽 머지] · 본 세션 신규 행 = Q291[생성 독트린 조문화 · 구 Q290 → 타 세션 재선점에 밀려 재부여] · 다음 부여 = Q292) · 271·272:2 = 재베이스라인 260720 15:2x(TOP편차 세션 Q271·Q272[큐 1790·1793행 — 구 Q01·Q02 스텁을 타 세션 Q263~264 선점에 밀려 재부여한 박제 · PR #2626]와 드라이브싱크 세션 Q271~Q272[훅캡처 게이트 지시 개번 · #2636]가 각자 main 박제 ×2 실측[origin/main grep -c = 2] · 재부여 불가[양쪽 머지] · 본 세션 신규 행 = Q273[구 훅캡처 Q01~12 → Q271 경합 재부여] 유일 · 다음 부여 = Q274) · 255·256:2 = 재베이스라인 260720 10:5x(정렬 스윕 세션 Q255[구 Q252 재부여]·Q256[한수 스모크]과 타 세션 Q255[구 Q258 재부여]·Q256이 각자 main 박제 ×2 실측[origin/main grep -c = 2] — 두 세션이 경합 재부여까지 같은 번호에 착지한 이중 경합 · 재부여 불가[양쪽 머지] · 본 세션 신규 행 = Q260[구 Q257 스텁 경합 재부여] 유일 · 다음 부여 = Q261) · 183:2 = 재베이스라인 260719 17:4x(07/18 4분할 스윕 세션 Q183[큐 1137행]과 채널 반응 유닛 세션 Q183[큐 1357행 · PR 2561]이 각자 main 박제 ×2 실측 · 재부여 불가[양쪽 머지] · 본 세션 신규 행 = Q184[Q183 경합 재부여] · 다음 부여 = Q185) · 171:2 = 재베이스라인 260719 16:17(한수 집행 승인 세션 Q171[1305행]과 가계정 쿠키 세션 Q171[1312행]이 각자 main 박제 ×2 실측 · 재부여 불가[양쪽 머지] · 본 세션 = 원장 무접촉 커밋[fb 진단 로깅]이 게이트에 걸려 면책 승계만) · 163:2 = 재베이스라인 260718 23:44(#2534 페북 30분 크론 Q163과 웹앱 전반 품질 세션 Q163이 각자 main 박제 ×2 실측[큐 1227·1235행] · 재부여 불가[양쪽 머지] · 본 세션 신규 행 = Q164 유일 · 다음 부여 = Q165) · 156:2 = 재베이스라인 260718 19:16(폰알람·채널분석 세션과 비디오 스튜디오 디자인 세션이 각자 main 박제 ×2 실측 · 재부여 불가[양쪽 머지] · 본 세션 신규 행 = Q159[Q155 경합 재부여] · 다음 부여 = Q160) · 142:2 = 재베이스라인 260718 18:35(#2505 핫픽스 리넘버 Q142[전사 폴오버]와 #2503 편집디자인 Q142가 각자 main 박제 ×2 실측[origin/main grep -c = 2] · 재부여 불가[양쪽 머지] · 본 세션 신규 행 = Q154 유일 · 다음 부여 = Q155) · 135·136:2 = 재베이스라인 260718 17:44(각 번호를 두 타 세션이 각자 main 박제 ×2 실측 · 재부여 불가[양쪽 머지] · 본 세션 신규 행 = Q147 유일 · 다음 부여 = Q148) · 132:2 = 재베이스라인 260718 16:30(Q132 ×2 — #2495 전사폴오버·#2496 옵션카드가 각자 진짜 main d8099fa에 머지 완료 = 박제 ×2 실측 · 재부여 불가[양쪽 박제] · 본 세션 신규 행 = Q133 · 다음 부여 = Q134 · 로컬 origin/main 스테일(2dde7be) 실측 오도 주의) · 43·49·63·64 :2 = 260717 병렬 머지 병존(각 번호를 두 세션이 각자 부여·둘 다 main 실재 = 갈래 유산 · 재부여 불가[양쪽 머지 완료]라 면책 기록 · 43=스크림#2422+편집알림 / 49=평의회분신술+PAT후속 / 63·64=동시 세션 원장 경합 · 91=요구사항 프로토콜#2458+22:05 규칙주입 동시 부여) · 161:2 = 재베이스라인 260718 23:09(규칙 6 머지와 같은 창의 과도기 경합 — #2514 세션 Q161과 타 세션 Q161이 각자 main 박제 ×2 실측 · 재부여 불가[양쪽 머지] · 신규칙 시행 전 착수 세션의 구규칙 마지막 충돌로 기록)   # 306·307·308:2 · 309·310:3 = 재베이스라인 260720 22:1x(트렌드 대분류 시각집약 세션 — 구글/시그널 실검·프로필 유닛개편(#2682 Q316~320) 등 타 세션 Q306~310이 각자 main 박제[origin/main grep -c: 309=3·310=3 실측] · 재부여 불가[전부 머지] · 본 세션 신규 행 = Q321[트렌드 시각 좌상단 집약] 유일·무관 · 다음 부여 = Q322) · 292:2 = 재베이스라인 260720 20:3x(평의회 후속수리 세션 Q292[큐 1954행 · 구 Q287→Q289 2차 재부여]와 독트린 이식 승인 세션 Q292[큐 1993행 · "머지해주셈"]가 각자 main 박제 ×2 실측[origin/main grep -c = 2] · 재부여 불가[양쪽 머지] · 본 세션 신규 행 = Q295[좌측 -3 통일] 유일·무관 · 다음 부여 = Q296) ·290·291:2 = 재베이스라인 260720 20:1x(Q290 = 팔로워대시 세션[큐 16행]·로딩픽토 세션[큐 1945행] · Q291 = dots로더 세션[큐 1949행]·생성독트린 세션[큐 1972행]이 각자 main 박제 ×2 실측[origin/main grep -c = 2] · 재부여 불가[양쪽 머지] · 본 세션 신규 행 = Q293[구 Q290 좌측 미세조정 → 3중 경합 재부여 · left -2.5·플레이그라운드] 유일 · 다음 부여 = Q294) · 289:2 = 재베이스라인 260720 20:0x(평의회 후속수리 세션 Q289[구 Q287 재부여 · 큐 1941행]과 아이콘 전환 세션 Q289[큐 1953행 · 19:46]가 각자 main 박제 ×2 실측[스테이시 후 grep -c = 2 = origin/main 자체 중복] · 재부여 불가[양쪽 머지] · 본 세션 신규 행 = Q291[생성 독트린 조문화 · 구 Q290 → 타 세션 재선점에 밀려 재부여] · 다음 부여 = Q292) · 271·272:2 = 재베이스라인 260720 15:2x(TOP편차 세션 Q271·Q272[큐 1790·1793행 — 구 Q01·Q02 스텁을 타 세션 Q263~264 선점에 밀려 재부여한 박제 · PR #2626]와 드라이브싱크 세션 Q271~Q272[훅캡처 게이트 지시 개번 · #2636]가 각자 main 박제 ×2 실측[origin/main grep -c = 2] · 재부여 불가[양쪽 머지] · 본 세션 신규 행 = Q273[구 훅캡처 Q01~12 → Q271 경합 재부여] 유일 · 다음 부여 = Q274) · 255·256:2 = 재베이스라인 260720 10:5x(정렬 스윕 세션 Q255[구 Q252 재부여]·Q256[한수 스모크]과 타 세션 Q255[구 Q258 재부여]·Q256이 각자 main 박제 ×2 실측[origin/main grep -c = 2] — 두 세션이 경합 재부여까지 같은 번호에 착지한 이중 경합 · 재부여 불가[양쪽 머지] · 본 세션 신규 행 = Q260[구 Q257 스텁 경합 재부여] 유일 · 다음 부여 = Q261) · 183:2 = 재베이스라인 260719 17:4x(07/18 4분할 스윕 세션 Q183[큐 1137행]과 채널 반응 유닛 세션 Q183[큐 1357행 · PR 2561]이 각자 main 박제 ×2 실측 · 재부여 불가[양쪽 머지] · 본 세션 신규 행 = Q184[Q183 경합 재부여] · 다음 부여 = Q185) · 171:2 = 재베이스라인 260719 16:17(한수 집행 승인 세션 Q171[1305행]과 가계정 쿠키 세션 Q171[1312행]이 각자 main 박제 ×2 실측 · 재부여 불가[양쪽 머지] · 본 세션 = 원장 무접촉 커밋[fb 진단 로깅]이 게이트에 걸려 면책 승계만) · 163:2 = 재베이스라인 260718 23:44(#2534 페북 30분 크론 Q163과 웹앱 전반 품질 세션 Q163이 각자 main 박제 ×2 실측[큐 1227·1235행] · 재부여 불가[양쪽 머지] · 본 세션 신규 행 = Q164 유일 · 다음 부여 = Q165) · 156:2 = 재베이스라인 260718 19:16(폰알람·채널분석 세션과 비디오 스튜디오 디자인 세션이 각자 main 박제 ×2 실측 · 재부여 불가[양쪽 머지] · 본 세션 신규 행 = Q159[Q155 경합 재부여] · 다음 부여 = Q160) · 142:2 = 재베이스라인 260718 18:35(#2505 핫픽스 리넘버 Q142[전사 폴오버]와 #2503 편집디자인 Q142가 각자 main 박제 ×2 실측[origin/main grep -c = 2] · 재부여 불가[양쪽 머지] · 본 세션 신규 행 = Q154 유일 · 다음 부여 = Q155) · 135·136:2 = 재베이스라인 260718 17:44(각 번호를 두 타 세션이 각자 main 박제 ×2 실측 · 재부여 불가[양쪽 머지] · 본 세션 신규 행 = Q147 유일 · 다음 부여 = Q148) · 132:2 = 재베이스라인 260718 16:30(Q132 ×2 — #2495 전사폴오버·#2496 옵션카드가 각자 진짜 main d8099fa에 머지 완료 = 박제 ×2 실측 · 재부여 불가[양쪽 박제] · 본 세션 신규 행 = Q133 · 다음 부여 = Q134 · 로컬 origin/main 스테일(2dde7be) 실측 오도 주의) · 43·49·63·64 :2 = 260717 병렬 머지 병존(각 번호를 두 세션이 각자 부여·둘 다 main 실재 = 갈래 유산 · 재부여 불가[양쪽 머지 완료]라 면책 기록 · 43=스크림#2422+편집알림 / 49=평의회분신술+PAT후속 / 63·64=동시 세션 원장 경합 · 91=요구사항 프로토콜#2458+22:05 규칙주입 동시 부여) · 161:2 = 재베이스라인 260718 23:09(규칙 6 머지와 같은 창의 과도기 경합 — #2514 세션 Q161과 타 세션 Q161이 각자 main 박제 ×2 실측 · 재부여 불가[양쪽 머지] · 신규칙 시행 전 착수 세션의 구규칙 마지막 충돌로 기록)   # 902:2 = 재베이스라인 260727 16:0x(theme_color 3면 시안 세션 Q902와 타 세션 Q902가 각자 main 박제 ×2 실측[origin/main grep -c "^- ✅ Q902" = 2] · 재부여 불가[양쪽 머지 · 676 선례] · 본 세션 신규 행 = Q903[--fix-qnum 재부여] 유일 · 다음 부여 = 파일 최대+1)   # 687:2·688:2 = 재베이스라인 260727 15:5x(원장·게이트 핫스팟 연속 레이스 — 링크원장 세션 Q687[#3107]·smoke_preview C10 세션 Q687[#3110], Q688도 동형으로 각자 origin/main 박제 ×2 실측 · --fix-qnum 자진 반려["타 세션 행이라 재부여 불가(양쪽 머지)"] = 면책 승계만[670·656·633 선례] · 본 세션 신규 행 = Q689[히스토리 칸 인계 일반화 · Q676→688→689 3연속 재부여] 유일 = 중복 아님 · 다음 부여 = 파일 최대+1)   # ⟨양쪽 보존 260727 18:5x⟩ 같은 Q912 면책을 두 세션이 각자 등재 = **키 합집합 동일**(79종 · 값 충돌 0)이라 어느 쪽을 취해도 면책 소실 0 → main 판을 취하고 이 세션의 실측 근거만 덧붙인다: 알림처리 Q912[큐 4700행]·훅-신선도경고 Q912[4719행] 각자 박제 ×2를 `git show origin/main:docs/요구사항_큐.md | grep -c '^- ✅ Q912'` = 2로 확인 · 본 세션 신규 행 = Q913(창 기준 중앙 하드게이트 = smoke_popup C8·C9).   # 918:2 = 재베이스라인 260727 19:2x(타 세션 2행 — news-alert-download-7aliu6[큐 4767행]과 헤더-돋보기80%-잉크중심가로정렬[4774행]이 각자 origin/main 박제 ×2 실측[git diff origin/main 신규 + 라인에 Q918 0건 = 내 행 아님] · **둘 다 내 행이 아니라 재부여 불가** = 면책 승계만[912·902·687 선례] · 본 세션 신규 행 = Q920[AI 생성 발사 후 폼 존속 · 구 Q914가 동시 세션 경합에 밀려 재부여] 유일 · 다음 부여 = 파일 최대+1)   # 933:2·934:3 = 재베이스라인 260727 20:3x(20개 세션 동시 가동 중 타 세션들이 같은 번호를 각자 박제 — `git show origin/main:docs/요구사항_큐.md | grep -cE '^- ✅ Q933'` = 2 · Q934 = 3 실측 · **전부 내 행이 아니라 재부여 불가**[양쪽 머지 · 912·902·687 선례] · `--fix-qnum` 자진 반려 = 면책 승계만 · 본 세션 신규 행 = Q935[한 수 채택분 전량 되돌림] 유일 · 다음 부여 = 파일 최대+1)   # ⟨머지 260727 22:3x⟩ 동시 세션이 같은 줄을 각자 늘려 충돌 → **키 합집합**으로 병합(선례 = 21:5x·21:4x 머지 주석) · 아래는 이쪽(요약요청 원본한정) 사유 전량 보존.   # 957:2 = 재베이스라인 260727 22:3x(요약요청 원본한정 세션 — 마스터링 2단[매크로+10밴드 EQ]·영상스튜디오 불투명판 승격 두 타 세션 행이 각자 Q957로 **origin/main 박제** ×2 실측 · 둘 다 내 행이 아니라 --fix-qnum 「미처리 · 양쪽 머지」 판정 = 재부여하면 [Q.NN] 1:1 참조가 깨진다 → 면책 승계만[950·942·939 선례] · 본 세션 신규 행 = --fix-qnum이 Q959로 재부여[요약요청 토글 확인] + Q958[원본 한정 신설] · 다음 부여 = 파일 최대+1)   # 961:2 = 재베이스라인 260727 22:4x(X 카드 사진·키워드·여백 세션 — 타 세션 **두 곳**[파비콘 로딩 애니 · 생성 게이지 2축]이 서로 같은 번호로 origin/main 박제 · **둘 다 내 행이 아니라 재부여 불가**[옮기면 [Q.NN] 1:1 참조가 깨진다 · 957·950·942 선례] = 면책 승계만 · 이 세션 신규 행 = Q962[X 인용·답글 사진 수집] = --fix-qnum 자동 재부여[Q960→Q962] 유일)   # ⟨머지 260727 22:5x⟩ 동시 세션이 같은 줄을 각자 늘려 충돌 → **키 합집합**으로 병합(어느 한쪽을 취하면 상대 면책이 소실 · 선례 = 260727 22:4x·21:5x 머지 주석).   # ⟨머지 260727 04:1x⟩ 동시 세션이 같은 줄을 각자 늘려 충돌 → **키 합집합**으로 병합(선례 문법 — 어느 한쪽을 취하면 상대 면책이 소실 = 다음 커밋이 그 번호로 rc=1). 양쪽 사유 주석 보존.   # ⟨머지 260728 04:1x⟩ 동시 세션이 같은 줄을 각자 늘려 충돌 → **키 합집합**으로 병합 = 값 충돌 0·키 증가 0(양쪽 다 973:2에 도달)이라 main 판을 취하고 이 세션(컷편집 리뷰 hml2kf)의 실측 근거만 보존: `--fix-qnum`이 「미처리 Q973 — origin/main에 이미 박제된 타 세션 행이라 재부여 불가(양쪽 머지)」 반환 → 손 재부여를 시도했다가 원복하고 면책 승계로 전환(남의 번호를 옮기면 그 세션의 [Q.NN] 1:1 참조가 끊긴다 · 970·968·961·957 선례) · 원장 파일 diff 0줄 · 이 세션 신규 행 = Q974·Q975.


def check_workflow_yaml():
    """워크플로 YAML 유효성 게이트(260728 Q976 · 운영자 지시 "재발 안 하게").

    실사고(260728): pick.yml 에 `- name: 본문 선-fetch (# body: 동봉 …)` 가 들어갔다. 무따옴표 스칼라 값
    안의 `: `(콜론+공백)는 YAML 문법상 매핑 구분자 → **그 줄이 아니라 파일 전체가 무효**가 된다. 무효
    워크플로는 GitHub 이 `workflow_dispatch` 를 거절하고, 그 거절이 `functions/api/pick.js` 를 타고
    뷰어에 `HTTP 502`로 떴다 = 뉴스 픽 전면 불능 4시간. 그동안 게이트 44개·CI·훅 전부 못 잡았다
    (`check_refs` 에 워크플로 문법 검사가 **0개**였다 = 이 게이트 이전의 사각).

    검사 = ① `.github/workflows/*.yml|yaml` 전수 파싱(파서 있으면 = 권위 판정 · 오탐 0)
          ② 파싱본 구조 = 최상위 dict + `jobs` + 트리거(`on`) 존재(빈 파일·들여쓰기 붕괴 조기 검출)
          ③ 파서가 없는 환경 = 오늘의 사고 유형만 잡는 경량 스캔(무따옴표 값 안 `: `) — **WARN-only**
             (정규식은 블록 스칼라 안 셸 한 줄을 오탐할 수 있어 차단은 파서가 있을 때만 = 오탐 차단 금지 원칙).
    ①②는 하드(rc=1) — 워크플로가 죽으면 파이프라인이 조용히 멈추므로 커밋 자체를 막는 게 맞다."""
    import glob as _g
    bad = []
    files = sorted(_g.glob(os.path.join(ROOT, '.github', 'workflows', '*.yml'))
                   + _g.glob(os.path.join(ROOT, '.github', 'workflows', '*.yaml')))
    if not files:
        return bad
    try:
        import yaml as _yaml
    except Exception:
        _yaml = None
    warn = []
    for p in files:
        rel = os.path.relpath(p, ROOT)
        try:
            src = open(p, encoding='utf-8').read()
        except Exception as e:
            bad.append('%s 읽기 실패 — %s' % (rel, e))
            continue
        if _yaml is not None:
            try:
                doc = _yaml.safe_load(src)
            except Exception as e:
                bad.append('%s YAML 파싱 실패 = 워크플로 전체 무효(GitHub이 dispatch 거절) — %s'
                           % (rel, ' '.join(str(e).split())[:200]))
                continue
            if not isinstance(doc, dict):
                bad.append('%s 최상위가 매핑이 아님(빈 파일·들여쓰기 붕괴)' % rel)
                continue
            if 'jobs' not in doc:
                bad.append('%s `jobs:` 없음 — 잡 0개 = startup_failure 시체 런만 쌓인다' % rel)
            if 'on' not in doc and True not in doc:   # YAML 1.1은 무따옴표 on 을 불리언 True 로 읽는다
                bad.append('%s 트리거(`on:`) 없음 — 아무도 못 깨우는 워크플로' % rel)
        else:
            for i, ln in enumerate(src.split('\n'), 1):
                m = re.match(r'^\s*(?:-\s+)?([A-Za-z_][\w-]*):\s+(\S.*)$', ln)
                if not m:
                    continue
                val = re.split(r'(?:^|\s)#', ' ' + m.group(2))[0].strip()   # YAML 주석(공백+#)만 제거 — `(#` 는 값의 일부
                if val[:1] in ('"', "'", '|', '>', '{', '[', '&', '*', '!'):
                    continue
                if ': ' in val or val.endswith(':'):
                    warn.append('%s:%d `%s:` 값에 무따옴표 `: ` — 따옴표로 감싸라(파서 미설치라 경고만)'
                                % (rel, i, m.group(1)))
    if _yaml is None:
        print('⚠️ 워크플로 YAML 게이트 = 경량 스캔(PyYAML 미설치 — 파서 있는 환경/CI가 권위 판정):')
        for w in warn[:10]:
            print('   -', w)
        if not warn:
            print('   · 의심 줄 0')
    elif not bad:
        print('✅ 워크플로 YAML 게이트 — %d개 전수 파싱 통과(jobs·트리거 보유 · 260728 pick.yml 전면 불능 재발 차단).' % len(files))
    return bad


def check_git_idiom():
    """봇커밋 git 관용구 게이트(260728 Q981 · 운영자 지시 "재발 안하게 조치").

    실사고(260727~28 Q980 · sns_brief/수집 8h 무음 정지): ① 1차 커밋 `git add A B C`에 미존재 경로
    (push/kw_sent.json = 발송이 있어야 생성)가 1개 끼자 git add가 **전체를 원자 abort**(스테이징 0 =
    "변동 없음" 위장 · `2>/dev/null || true`가 은폐) ② 그 탓에 미커밋 잔여(tbs_data.json)가 dirty로 남아
    push 거부 후 구조용 `git pull --rebase`가 "You have unstaged changes"로 즉사(역시 은폐) → 재시도
    전패 → 30분마다 초록불인 채 전량 유실. git_land.sh(260718)는 같은 지뢰를 실존 필터로 이미 봉합했으나
    지식이 헬퍼 1곳에만 있고 인라인 관용구 27곳엔 강제가 없던 것이 재발 구조 → 이 게이트가 전 파일 강제.

    검사(.github/workflows/*.yml|yaml + .github/scripts/*.sh · 주석부 제거 후):
      ① `git pull --rebase` = `--autostash` 필수(미커밋 잔여가 있어도 구조 경로 생존).
      ② 한 줄 다중 pathspec(2개↑) `git add` + 은폐(`2>/dev/null`·`|| true`) 금지 — 처방 = 파일별
         `for f in …; do if [ -e "$f" ]; then git add "$f"; fi; done` 또는 git_land.sh 경유.
         단일 pathspec 은폐 add = 줄별 독립(무산 파급 없음 = 기존 관용구 허용) · 배열 확장(`[@]`) =
         정적 카운트 불가 스킵(git_land.sh가 실존 필터 보유 정본).
      ③ 러너 훅 격리 불변식(260728 Q983 추가) — 봇 커밋이 pre-commit(check_refs 전체 게이트)을 타면,
         *사람 세션이 남긴* 원장 Q번호 중복 하나가 뉴스요약 파이프라인을 죽인다. 실사고 260727 3연속
         (Q902·Q970): ask.sh가 요약을 다 만들어 `성공 → queue/…md` 까지 찍은 뒤 Commit 스텝의 git commit이
         훅 rc=1로 거부 → `shell: bash -e` 즉사 → **완성된 다이제스트 통째 유실**, asks/ 원본만 남아 대기열에
         영구 '실패'. 봉합 = 러너에 훅을 아예 안 붙이기(2겹). 이 축은 그 2겹이 조용히 되돌려지는 것을 막는다:
           ⓐ `.githooks/pre-commit`에 GITHUB_ACTIONS 가드 존재
           ⓑ `shared/check_refs.py` 훅 자동활성화에 GITHUB_ACTIONS 제외 존재
           ⓒ 워크플로·스크립트가 `git config core.hooksPath`를 켜지 않음(러너 재부착 차단)
         ⚠️ 사람 clone의 훅 강제(260702 원설계)는 무접촉 — CI 축 게이트는 ledger-gate.yml(PR)·
         check-refs.yml(PR + 원장 push)이 그대로 담당하므로 커버리지 손실 0."""
    import glob as _g
    bad = []
    files = sorted(_g.glob(os.path.join(ROOT, '.github', 'workflows', '*.yml'))
                   + _g.glob(os.path.join(ROOT, '.github', 'workflows', '*.yaml'))
                   + _g.glob(os.path.join(ROOT, '.github', 'scripts', '*.sh')))
    n_pull = 0
    for p in files:
        rel = os.path.relpath(p, ROOT)
        try:
            lines = open(p, encoding='utf-8').read().split('\n')
        except Exception as e:
            bad.append('%s 읽기 실패 — %s' % (rel, e))
            continue
        for i, ln in enumerate(lines, 1):
            s = ln.strip()
            if s.startswith('#'):
                continue
            code = re.split(r'\s+#', s, 1)[0]   # 행끝 주석 제거(주석 속 관용구 인용 = 오탐 차단)
            if 'git pull --rebase' in code:
                n_pull += 1
                if '--autostash' not in code:
                    bad.append('%s:%d `git pull --rebase`에 --autostash 없음 — dirty tree면 rebase 즉사 = push 재시도 전패·산출물 무음 유실(Q980 8h 정지) → `git pull --rebase --autostash`' % (rel, i))
            m = re.search(r'\bgit add\s+(.+)$', code)
            if m and ('2>/dev/null' in code or '|| true' in code):
                tail = re.split(r'\s*(?:&&|\|\||;)\s*', m.group(1))[0]   # 후속 체인 절단
                toks = [t for t in tail.split() if t and not t.startswith('-') and '>' not in t and t != 'true']
                if any('[@]' in t for t in toks):
                    continue
                if len(toks) >= 2:
                    bad.append('%s:%d 한 줄 다중 pathspec `git add` + 은폐 — 결측 경로 1개면 전체 원자 abort = 스테이징 0 무음(Q980) → 파일별 `if [ -e "$f" ]` add 루프나 git_land.sh로' % (rel, i))
            if 'git config' in code and 'core.hooksPath' in code:
                bad.append('%s:%d 러너에서 `git config core.hooksPath` 설정 — 봇 커밋이 pre-commit(check_refs 전량)을 타면 *사람 세션이 남긴* 원장 Q번호 중복 하나가 파이프라인을 죽인다(260727 3연속 · 완성 요약 유실) → 이 줄을 지워라(사람 clone 훅은 check_refs가 자동 활성화)' % (rel, i))
    # ③ 러너 훅 격리 불변식 — 봉합 2겹이 조용히 사라지면 그 자리에서 rc=1(재발 봉인 · 상세 = docstring ③)
    # ⚠️ 검출은 **정규식**으로 — 평문 needle을 쓰면 이 게이트 코드 안의 리터럴이 스스로를 만족시켜(self-match)
    #    정작 진짜 가드가 지워져도 초록으로 통과한다(자기참조 함정).
    _inv = [
        ('.githooks/pre-commit', r'GITHUB' + r'_ACTIONS',
         '봇 커밋 통과 가드가 사라졌다 — `[ -n "$GITHUB_ACTIONS" ] && exit 0` 복원'),
        ('shared/check_refs.py',
         r"os\.path\.isdir\(os\.path\.join\(ROOT, '\.githooks'\)\)\s+and\s+not\s+os\.environ\.get\(",
         '훅 자동활성화의 CI 제외가 사라졌다 — 러너에 hooksPath가 다시 붙는다(파이프라인 커밋이 훅에 걸려 산출물 유실) → 자동활성화 조건에 CI 제외 복원'),
    ]
    for rel, pat, fix in _inv:
        p = os.path.join(ROOT, rel)
        try:
            body = open(p, encoding='utf-8').read()
        except Exception as e:
            bad.append('%s 읽기 실패 — %s' % (rel, e))
            continue
        if not re.search(pat, body):
            bad.append('%s 러너 훅 격리 불변식 깨짐: %s' % (rel, fix))
    if not bad:
        print('✅ 봇커밋 git 관용구 게이트 — %d파일 스캔 · pull--rebase %d줄 전부 --autostash · 다중 pathspec 은폐 add 0(Q980 8h 무음유실 재발 차단) · 러너 훅 격리 불변식 3종 생존(Q983 요약 유실 재발 차단).' % (len(files), n_pull))
    return bad


def check_qledger_unique():
    """지시 원장(docs/요구사항_큐.md) Q번호 유일성 게이트(운영자 260717 Q29 승인 — 동시 세션이 각자 '다음 번호'를
    추측 부여 → 같은 번호 경합 = 완료 보고 [Q.NN]↔원장 1:1 참조(CLAUDE.md [6]) 모호. 260717 실사고: Q24 이중 부여
    → 머지 후에야 발견 → 교정 커밋 2회). 행 규격 = 줄머리 '- <상태> QNN·' 또는 'QNN~MM·'(범위 전개). 역사적 중복
    (Q01×41 등 = 갈래 병존 유산)은 _QDUP_BASE 면책 · 그 밖의/그 이상 중복 = rc=1 + 파일 최대+1 재부여 안내.
    ⚠️ 커밋 전 로컬 파일 검사라 '남의 세션이 이미 main에 올린 번호'는 최신 main에서 브랜치를 새로 딴 상태에서만 보임
    — 확정(커밋) 직전 fetch+재기점이 짝이다(260718 규칙 6: 착수 중 = Q?? 스텁 → 커밋 직전 파일 최대+1 확정).
    면책 30종(260718 기준) 이후 _QDUP_BASE 증가 = 규칙 실패 신호(평의회 위원6 기준선). fail-closed(원장 못 읽으면 차단)."""
    try:
        lines = open(os.path.join(ROOT, 'docs', '요구사항_큐.md'), encoding='utf-8').read().splitlines()
    except Exception as e:
        print('❌ check_qledger_unique 원장 읽기 실패(fail-closed):', e); return 1
    # (260718 경합 소멸 · 운영자 승인) 착수 중 임시 행 = 'Q??(세션 꼬리표)·' 스텁 — 커밋 전 파일 최대+1 실번호로 확정 필수.
    # 스텁 잔존 커밋 = 미확정 번호가 main에 박제되는 사고라 차단(세칙 = 큐 헤더 규칙 6 · 확정 직전 fetch+재기점 규약과 짝).
    stubs = [ln[:60] for ln in lines if re.match(r'^- [^Q]{0,4}Q\?\?', ln)]
    if stubs:
        print('❌ 원장 Q?? 스텁 미확정 %d행 — 커밋 전 파일 최대+1 실번호로 확정하라(경합 소멸 규칙 · 큐 헤더 규칙 6): %s\n   자동 = python3 shared/check_refs.py --fix-qnum (스텁 확정 + 내 신규 행 재부여 · 박제 행 무접촉 · git fetch 먼저)' % (len(stubs), stubs[0]))
        return 1
    rx = re.compile(r'^- [^Q]{0,4}Q(\d+)(?:~(\d+))?(?:\([^)]*\))?·')   # (?:\(…\))? = 경합 재부여 주석형 'QNN(구 QMM …)·' 허용(260719 — 구판은 이 행을 아예 못 세서 최대·중복 계산 누락 = 재부여 번호가 무방비로 재발급될 틈 · 새 번호로 계수하고 괄호 안 구번호는 해제된 번호라 미계수가 정답)
    cnt = {}
    for ln in lines:
        m = rx.match(ln)
        if not m:
            continue
        a, b = int(m.group(1)), int(m.group(2)) if m.group(2) else int(m.group(1))
        for n in range(a, b + 1):
            cnt[n] = cnt.get(n, 0) + 1
    if not cnt:
        print('❌ 원장 Q행 0건 파싱 — 행 규격 변경 시 이 게이트 정규식도 갱신(fail-closed)'); return 1
    over = {n: c for n, c in cnt.items() if c > _QDUP_BASE.get(n, 1)}
    nxt = max(cnt) + 1
    if over:
        print('❌ 원장 Q번호 신규 중복(동시 세션 번호 경합): %s → 내 행만 Q%d(파일 최대+1)로 재부여하라(타 세션 행 무접촉 · [Q.NN] 1:1 참조 보전 · 신규칙: 착수 중이면 Q?? 스텁 유지 → 커밋 직전 확정)\n   자동 = python3 shared/check_refs.py --fix-qnum (origin/main 대비 내 신규 행만 재부여 · 박제 행 무접촉 · git fetch 먼저)'
              % (' · '.join('Q%02d ×%d(면책 %d)' % (n, c, _QDUP_BASE.get(n, 1)) for n, c in sorted(over.items())), nxt))
        return 1
    print('✅ 원장 Q번호 유일성 — 신규 중복 0(역사 중복 %d종 면책 · 현재 최대 Q%d · 다음 부여 = Q%d).' % (len(_QDUP_BASE), max(cnt), nxt))
    return 0


def fix_qnum_reassign():
    """`--fix-qnum` = 원장 Q번호 경합 자동 해소(운영자 260726 승인 — 같은 날 4연속[Q556→558→560] 손 왕복이 규칙 실패 신호).
    ① `Q??` 스텁을 파일 최대+1로 확정(큐 헤더 규칙 6 — 확정이 공짜여야 세션이 스텁을 쓰고, 그래야 경합이 **애초에** 안 난다)
    ② origin/main 대비 **이 브랜치가 새로 추가한 행만** 파일 최대+1로 순차 재부여한다. 안전축 3개:
      ⓐ base(origin/main 원장)를 못 읽으면 **no-op**(fetch 안 된 상태에서 남의 행을 건드리느니 아무것도 안 한다)
      ⓑ base에 이미 있는 행 = 타 세션 main 박제 = **절대 무접촉**(번호를 바꾸면 [Q.NN] 1:1 참조가 깨진다 · 58종 면책이 그 증거)
      ⓒ 양쪽 박제라 재부여 불가한 건은 고치지 않고 rc=1 + `_QDUP_BASE` 면책 승계로 안내(관례 = 사유 주석 필수)
    범위형(QNN~MM)은 자동 대상 밖 — 전개 폭이 참조와 얽혀 손으로 판단해야 한다."""
    path = os.path.join(ROOT, 'docs', '요구사항_큐.md')
    try:
        base = subprocess.run(['git', 'show', 'origin/main:docs/요구사항_큐.md'],
                              cwd=ROOT, capture_output=True, text=True, timeout=30)
        if base.returncode != 0:
            print('⚠️ --fix-qnum no-op — origin/main 원장을 못 읽었다(git fetch origin main 먼저):', base.stderr.strip()[:120])
            return 1
    except Exception as e:
        print('⚠️ --fix-qnum no-op — git 실행 실패:', e)
        return 1
    base_lines = set(base.stdout.splitlines())
    try:
        raw = open(path, encoding='utf-8').read()
    except Exception as e:
        print('❌ --fix-qnum 원장 읽기 실패:', e)
        return 1
    lines = raw.splitlines()
    rx = re.compile(r'^- [^Q]{0,4}Q(\d+)(?:~(\d+))?(?:\([^)]*\))?·')   # check_qledger_unique와 동일 규격(바뀌면 양쪽 같이 고친다)
    cnt = {}
    for ln in lines:
        m = rx.match(ln)
        if not m:
            continue
        a, b = int(m.group(1)), int(m.group(2)) if m.group(2) else int(m.group(1))
        for n in range(a, b + 1):
            cnt[n] = cnt.get(n, 0) + 1
    if not cnt:
        print('❌ --fix-qnum 원장 Q행 0건 파싱 — 행 규격 확인(fail-closed)')
        return 1
    over = {n: c for n, c in cnt.items() if c > _QDUP_BASE.get(n, 1)}
    nxt = max(cnt) + 1
    changed, stuck, stubbed = [], [], []
    # ① Q?? 스텁 확정(큐 헤더 규칙 6 = 착수 중 스텁 → 커밋 직전 실번호). 이 확정이 **공짜여야** 세션이 스텁을 쓰고,
    #    스텁을 쓰면 '착수 시점에 남과 같은 번호를 집는' 경합 자체가 안 난다 — push 트리거는 발견을 앞당길 뿐 예방은 못 한다.
    rx_stub = re.compile(r'^- [^Q]{0,4}Q\?\?')
    for i, ln in enumerate(lines):
        if rx_stub.match(ln):
            lines[i] = ln.replace('Q??', 'Q%d' % nxt, 1)
            stubbed.append(nxt)
            nxt += 1
    # ② 신규 중복 재부여(이 브랜치가 새로 넣은 행만)
    for i, ln in enumerate(lines):
        m = rx.match(ln)
        if not m or m.group(2):        # 범위형 = 수동
            continue
        n = int(m.group(1))
        if n not in over:
            continue
        if ln in base_lines:           # 타 세션 박제 — 무접촉(ⓑ)
            stuck.append(n)
            continue
        lines[i] = ln.replace('Q%d' % n, 'Q%d' % nxt, 1)
        changed.append((n, nxt))
        nxt += 1
    if not (stubbed or changed or stuck):
        print('✅ --fix-qnum 할 일 없음 — Q?? 스텁 0 · 신규 중복 0(현재 최대 Q%d · 다음 부여 = Q%d).' % (max(cnt), max(cnt) + 1))
        return 0
    if stubbed or changed:
        open(path, 'w', encoding='utf-8').write('\n'.join(lines) + ('\n' if raw.endswith('\n') else ''))
        for n in stubbed:
            print('🔧 --fix-qnum 스텁 확정 Q?? → Q%d (착수 중 스텁 → 커밋 직전 실번호 · 큐 헤더 규칙 6)' % n)
        for a, b in changed:
            print('🔧 --fix-qnum 재부여 Q%d → Q%d (origin/main에 없는 = 이 브랜치 신규 행만)' % (a, b))
        print('   ⚠ 그 항목 본문이 구 번호를 참조하면 손으로 맞춰라([Q.NN] 1:1 참조 보전).')
    if stuck:
        print('⚠️ --fix-qnum 미처리 %s — origin/main에 이미 박제된 타 세션 행이라 재부여 불가(양쪽 머지).'
              % ' · '.join('Q%d' % n for n in sorted(set(stuck))))
        print('   → 관례대로 _QDUP_BASE 면책 승계 + 사유 주석(58종 선례와 같은 문법).')
        return 1
    return 0


def check_anchor_liveness():
    """기틀 문서 → 문서 한정(§) 앵커 생존 게이트(운영자 260718 Q146 승인 "차단되고 영향 100% 없음 증명").
    사고 부류 = CLAUDE.md 개편(260701 이모지 섹션 해체) 때 그걸 가리키던 기틀 문서들이 안 따라와 죽은 앵커 잔존
    (Q146 감사서 수동 발견 11건) → 재발을 커밋 단계 자동 차단. 스코프 = 아래 화이트리스트 기틀 문서 안에서
    '문서명 §토큰' 꼴(50자 내 근접)의 **문서 한정 참조만** — 맨몸 §🎨 k 류(앱 지침 섹션 인용)·원장/이력(append-only
    역사)은 비대상 = 오탐 0 설계. 역사 서술 줄(해체·폐지·(구)·구 §·구 `)은 스킵(의도된 잔존 = Q146 관례).
    생존 판정 = 대상 문서에 '§토큰' 실존 or (숫자 토큰) '## N.' 헤딩 실존 or (2자+ 비숫자 토큰) 본문 실존 ·
    자기 파일 참조 = 스킵(참조 줄 자신이 매칭되는 순환 차단). fail-closed(화이트리스트 파일 못 읽으면 차단)."""
    FILES = ['CLAUDE.md', '디자인기틀/디자인기틀_SSOT.md', '디자인기틀/CII_컴포넌트계승인덱스.md',
             '디자인기틀/플레이그라운드_포터블.md', 'docs/실행계약_전문.md',
             '디자인기틀/구성도/00_가이드북_버튼인터랙션.html', '디자인기틀/구성도/00_가이드북_버튼인터랙션.md', '디자인기틀/구성도/진행 결과 상태.html']
    DOCMAP = {'CLAUDE.md': 'CLAUDE.md', '디자인기틀_SSOT.md': '디자인기틀/디자인기틀_SSOT.md',
              'CII_컴포넌트계승인덱스.md': '디자인기틀/CII_컴포넌트계승인덱스.md',
              '플레이그라운드_포터블.md': '디자인기틀/플레이그라운드_포터블.md', '실행계약_전문.md': 'docs/실행계약_전문.md'}
    HIST = re.compile(r'해체|폐지|\(구\)|구 §|구 `')
    REF = re.compile(r'(CLAUDE\.md|디자인기틀_SSOT\.md|CII_컴포넌트계승인덱스\.md|플레이그라운드_포터블\.md|실행계약_전문\.md)[^§\n]{0,50}§([^\s·,)\]<>*`|]{1,20})')
    texts = {}
    try:
        for p in set(FILES) | set(DOCMAP.values()):
            texts[p] = open(os.path.join(ROOT, p), encoding='utf-8').read()
    except Exception as e:
        print('❌ check_anchor_liveness 기틀 파일 읽기 실패(fail-closed):', e); return 1
    bad = []
    for src in FILES:
        for i, ln in enumerate(texts[src].splitlines(), 1):
            if HIST.search(ln): continue
            for m in REF.finditer(ln):
                tgt = DOCMAP[m.group(1)]
                if tgt == src: continue
                tok, body = m.group(2), texts[tgt]
                ok = ('§' + tok) in body
                if not ok and re.fullmatch(r'[0-9][0-9\-]*', tok):
                    ok = re.search(r'^#+\s*%s[.\s)]' % re.escape(tok.split('-')[0]), body, re.M) is not None
                if not ok and len(tok) >= 2 and not tok.isdigit():
                    ok = tok in body
                if not ok: bad.append('%s:%d → %s §%s' % (src, i, m.group(1), tok))
    if bad:
        print('❌ 기틀 앵커 생존 게이트 — 죽은 문서 한정 앵커(대상 문서에 §토큰 부재 · 역사 서술이면 줄에 해체/폐지/(구) 명기):')
        for b in bad: print('   ·', b)
        return 1
    print('✅ 기틀 앵커 생존 게이트 — 문서 한정 § 참조 전건 도달 가능(화이트리스트 %d파일 · 역사 서술 스킵).' % len(FILES))
    return 0


def check_html_charset():
    # HTML 전달물 charset 게이트(하드) — docs/**/*.html 첫 1024B 안 <meta charset> 필수(CLAUDE.md [7] 운영자 260720).
    # 근거: 폰 로컬(file://) 열람은 서버 인코딩 헤더가 없어 무선언 = 한글 깨짐 · 브라우저 prescan 창 = 정확히 첫 1024바이트라 창 기준 실측(창 밖 선언 = 연극 차단 · 평의회 8인 260720).
    rc = 0; bad = []
    for p in glob.glob(os.path.join(ROOT, 'docs', '**', '*.html'), recursive=True):
        try:
            with open(p, 'rb') as fh:
                head = fh.read(1024)
        except OSError:
            continue
        if b'charset' not in head.lower():
            bad.append(os.path.relpath(p, ROOT)); rc = 1
    if bad:
        print('❌ HTML charset 게이트 — 첫 1KB 안 <meta charset="utf-8"> 없음 %d건(폰 열람 깨짐): %s' % (len(bad), ', '.join(bad[:5])))
    else:
        print('✅ HTML charset 게이트 — docs HTML 전량 첫 1KB 안 선언(폰 로컬 열람 한글 안전).')
    return rc



def check_fp_parity():
    """지문(fp) 축 패리티 하드게이트(260720 평의회C M3 — 수동 미러 3면 감시).
    ① CROSS_RE(py) ↔ FP_CROSS_RE(js) 패턴 문자열 동일 ② fp_dict.json ↔ fp_culture_dict.json 파싱 동일
    ③ persons 정규화 상한(÷10 캡) py↔js 동일. 미러 드리프트 = 시운전(py)과 라이브(js) 점수 괴리 사고원."""
    rc = 0
    try:
        v = open(os.path.join(ROOT, 'viewer', 'index.html'), encoding='utf-8').read()
        g = open(os.path.join(ROOT, 'scraper', 'fp_culture_dict.py'), encoding='utf-8').read()
    except Exception as e:
        print('⚠️ check_fp_parity 스킵(파일):', e); return 0
    m1 = re.search(r'const FP_CROSS_RE = /(.+?)/;', v)
    m2 = re.search(r"CROSS_RE = re\.compile\(r'(.+?)'\)", g)
    if not m1 or not m2 or m1.group(1) != m2.group(1):
        print('❌ fp 크로스어 패리티 — viewer FP_CROSS_RE ≠ scraper CROSS_RE (문자열 동일 유지 필수)'); rc = 1
    try:
        import json as _json
        a = _json.load(open(os.path.join(ROOT, 'viewer', 'fp_dict.json'), encoding='utf-8'))
        b = _json.load(open(os.path.join(ROOT, 'apps', 'insta', 'data', 'fp_culture_dict.json'), encoding='utf-8'))
        if a != b:
            print('❌ fp 사전 사본 불일치 — viewer/fp_dict.json ≠ apps/insta/data/fp_culture_dict.json (python3 scraper/fp_culture_dict.py 재실행으로 동기)'); rc = 1
    except Exception as e:
        print('⚠️ check_fp_parity 사전 파싱 스킵:', e)
    cj = re.search(r'Math\.min\(p / 10, ([\d.]+)\)', v)
    cp = re.search(r'\) for t in ts\) / 10, ([\d.]+)\)', g)
    if cj and cp and float(cj.group(1)) != float(cp.group(1)):
        print(f'❌ fp persons 상한 불일치 — js {cj.group(1)} ≠ py {cp.group(1)}'); rc = 1
    if rc == 0:
        print('✅ fp 지문축 패리티 — 크로스어·사전 사본·persons 상한 py↔js 동일')
    return rc


# ── 발사(생성) 버튼 규격 게이트 (운영자 260720 "생성 버튼은 통일 · 그냥 기존 걸 따라해라 · 모조품 만들지 마" 한 수 실체화) ──
#   스튜디오 launch 버튼 = Image Studio 사다리 정본(r-m 11·sp-1 6·fs-label 13 · PR 2518 §3③ 전 스튜디오 형상 사인오프 · 정본 = edit #editGo).
#   신규/변경 발사 버튼이 이 규격을 벗어나면(=모조품) rc=1로 커밋 차단. 신규 발사 버튼 편입 = 아래 _LAUNCH_BTNS 레지스트리에 selector 1줄 추가.
#   ⚙ 왜 '공용 클래스' 아닌 게이트인가(운영자 한 수 원문 = "공용 한 클래스로 승격"): 뷰어별 <style> 자립 구조라 8뷰어가 .go를 각자 정의 =
#      '진짜 전역 공용 클래스'가 물리적으로 없다(tokens.css = 구조토큰 거울·컴포넌트 불가). 클래스만으론 '붙이는 걸 잊으면' 모조품 부활 →
#      게이트가 커밋서 규격 이탈을 차단해야 비로소 '원천 봉쇄'(상시·우회 불가). 값은 이미 통일(PR 2518)이라 이 게이트가 그 상태를 동결·수호한다.
_LAUNCH_SPEC = ('border-radius:var(--r-m)', 'padding:var(--sp-1)', 'font-size:var(--fs-label)')   # 생성 규격 3속성(사다리 정본 값)
_LAUNCH_BTNS = {   # 스튜디오 발사 버튼 레지스트리(selector → 규격 강제 대상) · 신규 발사 버튼 = 여기 1줄 추가로 편입
    'viewer/thumb.html': ['#go'],
    'viewer/nb.html':    ['#go'],
    'viewer/tr.html':    ['#go'],
    'viewer/k.html':     ['#go'],
    'viewer/ly.html':    ['#go'],
    'viewer/edit.html':  ['#editGo', '.xtr .xgo'],
    'viewer/track.html': ['#analyze'],
    'viewer/song.html':  ['#optGo', '#sunoGo', '#lyriaGo', '#vApply'],
    'viewer/vd.html':    ['.go'],   # 큐영상 발사(id 규칙 없음 = 클래스 등재 · 260802 7차 — 미등재 탓에 height:var(--btn) 34 드리프트가 게이트 밖에 있었다)
    'viewer/sb.html':    ['.go'],   # 콘티 발사(동축 편입 260802 7차)
}
_CSS_RULE = re.compile(r'^([^\n{}]*?)\{([^{}]*)\}', re.M)   # 단일레벨 CSS 규칙(prelude{body}) — 발사 규칙은 전부 한 줄

def check_launch_spec():
    rc = 0; n = 0
    for rel, sels in _LAUNCH_BTNS.items():
        try:
            css = open(os.path.join(ROOT, rel), encoding='utf-8').read()
        except Exception:
            continue
        css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)   # 주석 제거(주석 속 셀렉터 오탐 차단)
        for sel in sels:
            n += 1
            body = ''
            for m in _CSS_RULE.finditer(css):
                if sel in [p.strip() for p in m.group(1).split(',')]:   # 그룹 셀렉터(콤마)도 토큰 일치로 포착
                    body += m.group(2)
            body_ns = re.sub(r'\s+', '', body)   # 공백 정규화(`padding: var` 표기차 흡수)
            if not body:
                print('❌ 발사버튼 규격 게이트 — %s의 「%s」 규칙 미발견(레지스트리 오등록? selector 확인)' % (rel, sel)); rc = 1; continue
            miss = [p for p in _LAUNCH_SPEC if p not in body_ns]
            if miss:
                print('❌ 발사버튼 규격 이탈(모조품) — %s 「%s」 누락: %s → 생성 규격(r-m·sp-1·fs-label · #editGo 정본) 계승하라'
                      % (rel, sel, ', '.join(miss))); rc = 1
    if rc == 0:
        print('✅ 발사버튼 규격 게이트 — 스튜디오 발사 버튼 %d개 전부 생성 규격(r-m·sp-1·fs-label) 계승(모조품 0 · 신규 편입 = _LAUNCH_BTNS).' % n)
    return rc


# ── 이미지 스튜디오 도크 규격 게이트(운영자 260723 "AFTER로 일괄 통일 · 저 규격 벗어나면 안됨") ──
#   AFTER 규격(정본 = thumb 편집 탭 도크) 2속성 동결:
#   ① 리드백 요약 스트립(#editSpec·#trSpec) 값 = 기본값 mut·변경값만 accent → 정적 HTML에 `gs-v.on` 하드코딩 금지
#      (기본값 강조 = tr 260721 이탈 선례: 부팅 시 전 값 청록 = 편집 탭과 색 불일치 · 정본 문법 = updateGoSpec가 비기본값만 .on 토글).
#   ② 생성 버튼(#go) = 입력(사진) 없다고 disabled 금지 → 정적 `disabled` 속성 금지(상시 활성 full opacity·빈 클릭=사진 첨부 = thumb !CIMG.b64→cFile.click).
#   범위 = 이미지 스튜디오(thumb·tr)만 · 토글형(#goSpec `gs-tog` ON)은 상태반영이라 대상 아님(리드백 N택1만) ·
#   AI 생성(index #geniGo)은 텍스트 프롬프트 사전-disabled 어포던스(운영자 260721)라 별개 축 = 비대상.
#   신규 편입 = 아래 _DOCK_* 레지스트리에 1줄 추가. 등재 = CII §도크(발사 버튼 행 인접).
_DOCK_READBACK_STRIPS = {   # file → [리드백 스트립 div id](정적 콘텐츠·값=기본 mut)
    'viewer/thumb.html': ['editSpec'],
    'viewer/tr.html':    ['trSpec'],
    'viewer/vd.html':    ['spec'],       # 큐영상 도크 편입(260802) — 정적 내용 0·리드백은 syncSpec 단독 생성
}
_DOCK_ACTIVE_BTNS = {   # file → [상시 활성 발사 버튼 id](입력-disabled 금지)
    'viewer/thumb.html': ['go'],
    'viewer/tr.html':    ['go'],
    'viewer/vd.html':    ['go'],         # 큐영상 발사 = 상시 활성(0건 클릭 = shake 안내)
}

def check_imgstudio_dock_spec():
    rc = 0; ns = 0; nb = 0
    for rel, ids in _DOCK_READBACK_STRIPS.items():
        try:
            html = open(os.path.join(ROOT, rel), encoding='utf-8').read()
        except Exception:
            continue
        for sid in ids:
            ns += 1
            m = re.search(r'id="%s"[^>]*>(.*?)</div>' % re.escape(sid), html, re.S)
            if not m:
                print('❌ 이미지 스튜디오 도크 규격 — %s #%s 리드백 스트립 미발견(레지스트리 확인)' % (rel, sid)); rc = 1; continue
            bad = [c for c in re.findall(r'class="([^"]*)"', m.group(1)) if re.search(r'\bgs-v\b', c) and re.search(r'\bon\b', c)]
            if bad:
                print('❌ 이미지 스튜디오 도크 규격 이탈 — %s #%s 값에 정적 .on %d개 = 기본값 강조 금지(기본 mut·변경만 accent = updateGoSpec 정본 문법 · 부팅 색이 편집 탭과 불일치)' % (rel, sid, len(bad))); rc = 1
    for rel, ids in _DOCK_ACTIVE_BTNS.items():
        try:
            html = open(os.path.join(ROOT, rel), encoding='utf-8').read()
        except Exception:
            continue
        for bid in ids:
            nb += 1
            m = re.search(r'<button[^>]*\bid="%s"[^>]*>' % re.escape(bid), html)
            if not m:
                print('❌ 이미지 스튜디오 도크 규격 — %s #%s 생성 버튼 미발견' % (rel, bid)); rc = 1; continue
            if re.search(r'\bdisabled\b', m.group(0)):
                print('❌ 이미지 스튜디오 도크 규격 이탈 — %s #%s 생성 버튼 정적 disabled = 입력 없다고 비활성 금지(상시 활성·빈 클릭=첨부 = thumb #go 정본)' % (rel, bid)); rc = 1
    if rc == 0:
        print('✅ 이미지 스튜디오 도크 규격 게이트 — 리드백 스트립 %d개 값 기본 mut(정적 .on 0)·생성 버튼 %d개 상시 활성(정적 disabled 0) = AFTER 규격 동결(정본 = thumb #editSpec·#go · 신규 편입 = _DOCK_*).' % (ns, nb))
    return rc


# ── 코너 옵션 레일 사본 동일성 게이트 (운영자 260802 "아이디어대루" 승인 · 발사버튼 게이트 `_LAUNCH_BTNS` 문법 그대로) ──
#   왜 = 미리보기 코너 옵션 레일(CII 「미리보기 코너 옵션 레일」)은 3표면(thumb·tr·index)에 걸쳐 있는데,
#   thumb·tr은 **별도 문서**라 index 인라인 CSS를 상속받지 못하고 tokens.css는 구조토큰 거울 전용(컴포넌트 불가 · 아래 1541 동문)이라
#   **CSS 값 사본**이 유일한 길이다. 사본은 한 표면만 고치고 나머지를 잊는 순간 조용히 갈라진다(= 라이브가 표면마다 다른 얼굴).
#   클래스 승격으로는 못 막는다(뷰어별 <style> 자립 구조) → 발사버튼 게이트와 동일하게 **커밋에서 이탈을 차단**한다.
#   범위 = 캡슐(.trail) · 값 칩 그룹(.trail-v) · 값 칩(.gs-v) 3축. 신규 표면 편입 = 아래 레지스트리에 1줄 추가.
#   ⚠ .trail-v 축은 smoke_parity C3(카드 생성 #optStrip ↔ AI 생성 #geniSum 크로스-파일 등가)의 전제이기도 하다 —
#     `border:0`으로 지우면 borderColor가 표면별 currentColor로 갈라져 파리티가 깨진다(그래서 1px transparent 동결).
_TRAIL_AXES = (   # (축 이름, 셀렉터 후보[바디 합산], 동결 선언[공백 제거 표기])
    ('캡슐(.trail)', ('.trail', '.cpprev-box .trail', '.monwrap .trail'),
     ('border-radius:var(--r-s)', 'border:1pxsolidrgba(255,255,255,.14)',
      'background:rgba(8,15,11,.54)', 'backdrop-filter:blur(var(--blur-s))', '-webkit-backdrop-filter:blur(var(--blur-s))')),
    ('값 칩 그룹(.trail-v)', ('.cpprev-box .trail-v', '.monwrap .trail-v'),
     ('background:transparent', 'border:1pxsolidtransparent', 'border-radius:0', 'font-size:10.5px', 'line-height:1')),
    ('값 칩(.gs-v)', ('.cpprev-box .trail-v .gs-v', '.monwrap .trail-v .gs-v'),
     ('height:22px', 'border-radius:var(--r-l)', 'color:var(--mut)', 'font-size:10.5px', 'font-weight:var(--fw-x)',
      'text-align:center')),   # 중앙정렬(운영자 260802 6차 "중앙정렬로 할게" — 구 좌측정렬 지시 개정) · 'text-align:center'는 'text-align:left'와 문자열이 갈려 드리프트 검출 가능(place-items는 'center start'가 'center'를 부분문자열로 포함 = 판별 불가라 비동결)
    # ⭐ 픽토 글리프 축(운영자 260802 "픽토그램이 네비게이션 안에 들어갔을 때의 기준 크기가 없는듯 · 설정해줘") —
    #   구조: 레일 버튼은 어디나 22×22인데 **그 안 글리프 크기는 표면마다 제각각**이었다(thumb·tr·index만 12px 규칙 보유 /
    #   edit·k·song·vd는 규칙 자체가 없어 SVG 고유·상속 크기로 렌더 · 게다가 버튼 클래스마다[.trail-i·.cpv-tool·.histbtn]
    #   svg 규칙을 따로 심는 방식이라 새 픽토를 넣을 때마다 사각이 재생산됐다). 계약 = **레일 안 모든 svg = 12×12** 한 줄.
    ('픽토 글리프(.trail svg)', ('.cpprev .trail svg', '.cpprev-box .trail svg', '.pvsec .trail svg',
                                '.monwrap .trail svg', '.geni-prev .trail svg'),
     ('width:12px', 'height:12px')),
    ('픽토 버튼(.trail-i)', ('.trail-i', '.cpprev .trail-i', '.pvsec .trail-i', '.monwrap .trail-i', '.geni-prev .trail-i'),
     ('width:22px', 'height:22px')),   # 버튼 박스 = 22×22 — 글리프 12와 짝(둘이 같이 있어야 「네비 레일 픽토 기준 크기」가 성립)
)
# ── 빈 캡슐 소거 술어(운영자 260802 "옵션으로 사용할 내용이 없으면 확대 아래에 아무것도 안 뜨게") ──
#   도구 묶음(.trail-g) **직계** 버튼도 없고 값 칩(.trail-v)도 없으면 옵션 캡슐을 통째 은닉.
#   ⚠ 구 술어 `:not(:has(button:not([hidden])))`는 숨은 옵션 컬럼 안의 ‹›·체브론까지 세어 빈 유리조각이 상주했다(실측 260802).
#   프리픽스(.cpprev / .geni-prev / .pvsec / .monwrap)·id(#cpRail / #geniRail)는 표면마다 달라 **술어 문자열만** 잰다.
_TRAIL_EMPTY_PRED = ':not(:has(.trail-g>button:not([hidden]))):not(:has(.trail-v:not(.none))){display:none'
#   thumb만 정밀 술어(be9856f 260802 — 사진 도구가 .trail-g 직계 button이 아니라 .cpv-tool이고, 숨은 옵션 컬럼의 ‹›까지
#   세어 6px 껍데기가 상주[실측 rails[1].w=6] → 판정을 「보이는 도구·보이는 값 그룹」으로 좁힌 표면별 정본).
#   게이트가 이 개정을 미추적해 main 적색이던 드리프트 봉합(260802) — 타 표면 = 직계 button 정본 유지.
_TRAIL_EMPTY_PRED_BY = {'viewer/thumb.html': ':not(:has(.trail-g.cpv-tool:not([hidden]))):not(:has(.trail-v:not(.none))){display:none'}
_TRAIL_SURFACES_DECL = ('viewer/thumb.html', 'viewer/tr.html', 'viewer/index.html',
                        'viewer/edit.html', 'viewer/k.html', 'viewer/song.html', 'viewer/vd.html')


def _trail_surfaces():
    """레일 보유 표면 = **자동 발견**(운영자 260802 "항상 이미지 스튜디오나 영상 스튜디오는 저 로직을 따르게 만드셈 죽는 한이 있더라도").
    구조 = 손으로 관리하는 레지스트리는 **새 스튜디오 탭이 생기면 조용히 빠진다**(260802 실측: edit·k·song·vd가
    「비슷하게 생긴」 상태로 몇 세대를 지났다). 그래서 등재 여부가 아니라 **마크업 사실**로 대상을 정한다 —
    `viewer/*.html` 중 `class="trail`(레일 캡슐)을 가진 파일은 **전부** 이 게이트를 받는다.
    선언 목록(_TRAIL_SURFACES_DECL)은 사라진 표면을 잡는 역방향 안전망으로만 남긴다."""
    found = []
    for path in sorted(glob.glob(os.path.join(ROOT, 'viewer', '*.html'))):
        rel = 'viewer/' + os.path.basename(path)
        try:
            html = open(path, encoding='utf-8').read()
        except Exception:
            continue
        if re.search(r'class="trail[ "]|class="trail\b', html):
            found.append(rel)
    return tuple(found)


_TRAIL_SURFACES = _trail_surfaces()   # 레일 보유 표면(신규 = 여기 1줄) — 260802 영상 스튜디오 4탭 편입(운영자 "영상도 동일하게해줘" · 콘티 sb는 미리보기 액자 자체가 없어[Q1159 폐지] 비대상)
#   ⚠ vd(큐영상)만 앵커가 `.monwrap`(프로그램 모니터 래퍼 — 모니터 안은 renderMon()의 `mon.innerHTML=`이 통째로 갈아치워 레일이 지워진다) — 셸 클래스가 다를 뿐 레일 규격은 동일하므로 위 축의 셀렉터 후보에 `.mon …`을 같이 넣어 한 게이트로 잰다.


# ── 자간(tracking) 측정 기준 단일화 게이트 (운영자 260802 "잴 때 항상 한개의 기준에 따라서 짓던지, 두개의 기준에 다 맞추던지 하자") ──
#   계약 = ① 판정 자 = **advance 하나**(뷰어 = measureText().width · 서버 오버레이 = draw_t `getbbox(ch)[2]-[0]` ≈ advance 반올림
#   · 서버 헤더 = reels2 `font.getlength`) ② 한도 상수 = 서버 SPECS·limit·floor와 py↔js 동일.
#   ⚠ 오진 교정(운영자 260802 3차 "자간이 무한정 줄어서") — 2차 게이트는 "서버 draw_t = 잉크폭 전진"을 전제로 뷰어에
#   actualBoundingBox(진짜 잉크 · 공백 0)를 강제했으나 PIL 실측 반증: 단일 글자 getbbox 폭 = advance 반올림(공백 17.7→18 ·
#   '가' 71.8→72)이고, 자간을 실제로 정하는 fit_tracking measure(렌더 알파 bbox)도 Σadv ±4px('신림 상가에서 화재' 611 vs 610).
#   잉크 강제가 미리보기 공백 실종·자간 무한 압착의 진범이라 advance로 원복 — 이 게이트는 그 재발(잉크 축 회귀)을 막는다.
def check_track_parity():
    """자간 판정 = advance 단일 기준 + 한도 상수 py↔js 동일(운영자 260802 3차). 이탈 = rc=1."""
    rc = 0
    try:
        js = open(os.path.join(ROOT, 'viewer', 'thumb.html'), encoding='utf-8').read()
        yml = open(os.path.join(ROOT, '.github', 'workflows', 'thumb-make.yml'), encoding='utf-8').read()
        ov = open(os.path.join(ROOT, 'apps', 'thumbnail', 'nomute_overlay.py'), encoding='utf-8').read()
    except Exception as e:
        print('❌ 자간 기준 게이트 — 파일 열기 실패: %s' % e); return 1
    if 'measureText' not in js:
        print('❌ 자간 기준 게이트 — 뷰어가 measureText(advance)를 안 쓴다 = 서버 자(draw_t getbbox ≈ advance)와 다른 자'); rc = 1
    # 축별 자(basis) 선언 = 서버 렌더러와 1:1 — 오버레이(draw_t getbbox ≈ advance)·헤더(reels2 getlength) 전부 adv
    BASIS = {'post': 'adv', 'reels': 'adv', 'jjpost': 'adv', 'jjreels': 'adv'}
    for ax, want_b in BASIS.items():
        m = re.search(r"%s:\s*\{[^}]*basis:\s*'(\w+)'" % ax, js)
        if not m or m.group(1) != want_b:
            print("❌ 자간 기준 게이트 — TRK.%s basis=%s ≠ 서버 축(%s · 오버레이 = draw_t getbbox ≈ advance · 잉크 축 회귀 = 공백 실종 미리보기 재발)" % (ax, m.group(1) if m else '없음', want_b)); rc = 1
    for ax in ('sub', 'title', 'jinjja'):
        m = re.search(r"%s:\s*\{[^}]*basis:\s*'(\w+)'" % ax, js)
        if not m or m.group(1) != 'adv':
            print("❌ 자간 기준 게이트 — HDR.%s basis=%s ≠ 서버 축(adv · 헤더 = reels2 font.getlength)" % (ax, m.group(1) if m else '없음')); rc = 1
    try:
        r2 = open(os.path.join(ROOT, 'apps', 'thumbnail', 'nomute_reels2.py'), encoding='utf-8').read()
        if 'getlength' not in r2:
            print('❌ 자간 기준 게이트 — nomute_reels2가 getlength(advance) 축을 안 쓴다 = 헤더 basis 선언(adv)과 어긋남'); rc = 1
    except Exception:
        pass
    jj = ''
    try:
        jj = open(os.path.join(ROOT, 'apps', 'thumbnail', 'nomute_jinjja.py'), encoding='utf-8').read()
    except Exception:
        pass
    if jj and 'getbbox' not in jj:
        print('❌ 자간 기준 게이트 — nomute_jinjja 오버레이 폭이 draw_t와 같은 자(getbbox ≈ advance)가 아니다 = jj* 축 어긋남'); rc = 1
    if re.search(r"880 초과|자간 -45로도 안 들어감", js):
        print('❌ 자간 기준 게이트 — 힌트 문구에 한도·하한이 하드코딩됐다(규격 변경 시 표기만 옛말로 남는다) → spec 산출로 바꿔라'); rc = 1
    want = {'post': {'limit': 920, 'floor': -45, 'fs': 76, 'tr': 0},
            'reels': {'limit': 844, 'floor': -30, 'fs': 78, 'tr': -1}}
    for fmt, w in want.items():
        m = re.search(r'"%s":\s*\{[^}]*?"fs":(-?\d+)[^}]*?"tr":(-?\d+)' % fmt, ov, re.S)
        if not m:
            print('❌ 자간 기준 게이트 — nomute_overlay SPECS[%s] fs/tr 파싱 실패' % fmt); rc = 1; continue
        if int(m.group(1)) != w['fs'] or int(m.group(2)) != w['tr']:
            print('❌ 자간 기준 게이트 — SPECS[%s] fs/tr(%s/%s) ≠ 뷰어 TRK(%s/%s)' % (fmt, m.group(1), m.group(2), w['fs'], w['tr'])); rc = 1
        j = re.search(r"%s:\s*\{[^}]*fs:\s*(-?\d+)[^}]*limit:\s*(-?\d+)[^}]*start:\s*(-?\d+)[^}]*floor:\s*(-?\d+)" % fmt, js)
        if not j:
            print('❌ 자간 기준 게이트 — 뷰어 TRK.%s 파싱 실패' % fmt); rc = 1; continue
        if (int(j.group(1)), int(j.group(2)), int(j.group(3)), int(j.group(4))) != (w['fs'], w['limit'], w['tr'], w['floor']):
            print('❌ 자간 기준 게이트 — 뷰어 TRK.%s(fs%s/limit%s/start%s/floor%s) ≠ 서버 정본(%s/%s/%s/%s)'
                  % (fmt, j.group(1), j.group(2), j.group(3), j.group(4), w['fs'], w['limit'], w['tr'], w['floor'])); rc = 1
    if ('limit = 920 if fmt' not in yml) or ('floor = -45 if fmt' not in yml):
        print('❌ 자간 기준 게이트 — thumb-make.yml fit_tracking 한도(920/-45) 표기 이탈 = 3면 동기 깨짐'); rc = 1
    # ── ③ 미리보기 렌더 = 절단 통과분 강제(운영자 260807 3차 "입력 불가인 거는 아예 출력 안 되게 · 출력이 텍스트 끊김과 동일하게 동기화") ──
    #   계약 = 「자간을 그리는 미리보기 줄」은 **원문이 아니라 절단 함수(ovFit/hdrFit) 통과분**을 렌더한다
    #          = 입력 차단(_rowOverAfter)이 허용하는 글자 수 ≡ 화면에 보이는 글자 수(1:1 동기).
    #   ⚠ 신설 사유 = 260807에 이 축이 **세 세대**를 거쳤는데(유출 → 상자 클립[반 글자 잔여] → 글자 절단) 전부
    #     운영자 눈이 유일한 검출기였다. 기존 축은 전부 **다른 것**을 본다 — ①은 폭 재는 **자**, ②는 한도 **상수**,
    #     `smoke_*`는 **렌더된 그림** → 「렌더가 **어떤 텍스트**를 먹는가」는 축 자체가 없었다.
    #     현재 5줄(헤더 진짜예요 1 · 헤더 부제/제목 2 · 오버레이 진짜예요 1 · 오버레이 노뮤트 1)을 손으로 맞춰둔 상태라
    #     새 자간 축(새 템플릿·새 포맷)이 생기면 조용히 원문 렌더로 빠질 수 있다 = 레일·클립 SSOT가 겪은 그 축.
    #   판정 = 원문 식별자(lines·csub·ctitle)가 **내용 슬롯**에 직접 나타나면 FAIL(절단분 변수명은 자유 = 리네임 허용).
    #   ⚠ 자간 없는 `.cpv`(카드뉴스 = card_news.py가 tracking 미적용)는 대상 밖 = letter-spacing 보유 줄만 고른다.
    _fit_defs = [n for n in ('function ovFit(', 'function hdrFit(', 'function _fitPrefix(', 'function _cutToFit(', 'function _inkScan(') if n not in js]
    if _fit_defs:
        print('❌ 자간 기준 게이트 — 절단 함수 소실: %s (미리보기가 원문을 그대로 그리게 된다)' % ', '.join(_fit_defs)); rc = 1
    # 절단분 식별자 = ovFit/hdrFit/_fitPrefix 반환을 받는 이름(리네임 자유 · 이름을 박제하지 않는다)
    _fit_names = set(re.findall(r'([A-Za-z_$][\w$]*)\s*=\s*[^;\n]*?(?:ovFit|hdrFit|_fitPrefix)\s*\(', js))   # 다중 선언자(const a = f(), b = f()) 포함
    _fit_names |= set(re.findall(r'([A-Za-z_$][\w$]*)\s*=\s*(?:lines|[A-Za-z_$][\w$]*)\.map\([^)]*?(?:ovFit|hdrFit)\s*\(', js))
    _RAW_SRC = ('lines', 'csub', 'ctitle')
    # ⚠ 줄 단위가 아니라 **구간**으로 본다(평의회7 우회 B2 = 내용 슬롯만 다음 줄로 내리면 한 줄 스캔을 빠져나갔다)
    _lines_js = js.split('\n')
    _trk_rows = []
    for _i, _ln in enumerate(_lines_js):
        if not re.search(r'class="cpv[" ]', _ln) or _ln.lstrip().startswith('//'):
            continue   # ⚠ 정확 토큰 = `class="cpv"` 또는 `class="cpv …"` — 구판 접두 매칭은 cpv-bg·cpv-band·cpv-scrim까지 먹었다(첫 실행 실측 위양성)
        _reg = _ln                                       # 구간 = 그 줄부터 </div>까지(내용 슬롯만 다음 줄로 내리는 우회 B2 흡수)
        for _k in range(_i + 1, min(_i + 4, len(_lines_js))):
            if '</div>' in _reg:
                break
            _reg += '\n' + _lines_js[_k]
        if '</div>' in _reg:
            _reg = _reg.split('</div>')[0] + '</div>'
        if 'letter-spacing:${(' not in _reg and 'letter-spacing:${' not in _reg:
            continue                                     # 자간 없는 .cpv(카드뉴스 = tracking 미적용) = 대상 밖
        _trk_rows.append((_i + 1, _reg))
    _TRK_ROWS_MIN = 5   # 하한 고정 = 시그니처 드리프트·줄 소실이 「위반 0」으로 거짓 통과하는 것 차단(fail-closed)
    if len(_trk_rows) < _TRK_ROWS_MIN:
        print('❌ 자간 기준 게이트 — 자간 렌더 구간 %d개 < 하한 %d(시그니처 드리프트 또는 축 소실 = 판정 불능)'
              % (len(_trk_rows), _TRK_ROWS_MIN)); rc = 1
    for _ln, _row in _trk_rows:
        _body = _row.split('">', 1)[1] if '">' in _row else _row   # 내용 슬롯 = 스타일 속성이 닫힌 뒤
        _raw = [t for t in _RAW_SRC if re.search(r'\b%s\b' % t, _body)]
        if _raw:
            print('❌ 자간 기준 게이트 — thumb.html:%d 미리보기가 **원문**(%s)을 그대로 그린다 = 입력 차단 한도와 화면이 어긋난다 '
                  '→ ovFit()/hdrFit() 통과분을 렌더해라(운영자 260807 "입력 불가인 거는 아예 출력 안 되게")' % (_ln, '·'.join(_raw))); rc = 1
            continue
        # ⭐ 양성 축(평의회7 우회 B1·B4·B6 봉합) — 「원문 이름이 없다」로는 부족하다:
        #   중간 변수 세탁(`const x = lines`)·데코이 줄·호출 제거가 전부 그 술어를 빠져나갔다(우회 7종 실증).
        #   → 내용 슬롯이 **절단 함수 반환을 받은 이름**을 실제로 쓰는지 본다(이름 자체는 자유 = 리네임 허용).
        if not any(re.search(r'\b%s\b' % re.escape(_n), _body) for _n in _fit_names):
            print('❌ 자간 기준 게이트 — thumb.html:%d 자간 렌더가 절단 통과분을 안 쓴다(ovFit/hdrFit 반환 식별자 0) '
                  '→ 원문 세탁·데코이·호출 누락 중 하나다' % _ln); rc = 1
    if rc == 0:
        print('✅ 자간 기준 게이트 — 축별 자 선언 7개(전부 advance = 서버 draw_t getbbox·getlength와 1:1) · 한도 3면(TRK·SPECS·워크플로) 동일 · 표기 하드코딩 0 · 미리보기 자간 렌더 %d줄 전건 절단 통과분(원문 직렌더 0 · 절단 식별자 실사용 확인).' % len(_trk_rows))
    return rc


def check_result_rail_parity():
    """결과 레일 = 5탭 한 세트(운영자 260806 "왜 저게 계속 따로노는지 모르겟으유" · "정본에 정립해봣자 나중에 또 저렇게 따로노는거 아님?").

    ⚠ 신설 사유 = 260806 하루에 이 레일이 **세 번** 갈라졌고 **전부 운영자 눈이 유일한 검출기**였다:
      ⓐ 「결과」가 결론형 줄(thumb 3탭) vs 썸네일형 타일(tr·index 2탭)로 갈림
      ⓑ AI 생성 판만 타일 배경 투명(`var(--pan)` 미정의 = 선언 통무효)
      ⓒ 번역·AI 생성엔 요약 줄 자체가 없음(nm-job.css 링크 부재) + 연필이 absolute로 떠 상태줄에 겹침
    기존 게이트가 전부 다른 축이다 — `check_trail_spec` = **코너 레일** · `check_design` = 토큰 raw **개수** ·
    `smoke_studioshell` = 도크·잉크·픽토 **부품** → 「결과 레일이 같은 부품 세트를 갖는가」는 축 자체가 없었다.

    판정 = 정적(렌더·LLM·네트워크 0) · 표면 **자동 발견**(결과 레일 시그니처 보유 뷰어 = 새 탭이 조용히 못 빠진다) ·
    **면책표 없이 하드 0**(현행 위반 0). 4부품 = ① nm-hist.css 링크(타일 정본) ② nm-job.css 링크(요약 줄 정본)
    ③ `class="jobs"` 요약 줄 컨테이너 ④ `class="hist-grid"` 타일 그리드.
    """
    import glob as _g, os as _os, re as _re
    rc = 0
    """판정 = 표면마다 (정적 세트) ∨ (nm-rail.js 부품 상속) — 운영자 260806 평의회4가 우회 8종을 실증해 재작성한 3차 구현.
    1차 = 전역 토큰 존재 → 킬테스트 전건 미검출(죽은 게이트). 2차 = 문자 거리(WIN) → 여전히 8종 우회:
      A 시그니처 1글자 드리프트(클래스 순서·공백·추가)로 표면이 조용히 스코프 밖 B `data-scope="cap"`이 주석·문자열에만 있어도 통과
      C HTML 주석으로 감싸면 전 축 통과(형제 게이트는 전부 주석을 턴다 = 이 게이트만 관례 이탈) D 무관한 패널의 `class="jobs"`가 미끼
      E 영상 표면 손 목록이라 새 탭이 조용히 빠짐 F link href 실존 미검사 G `<template>` 격리 H **정적↔상속 이관이 위양성으로 막힘**(이 레포가 실제로 한 일)
    3차 = ⓐ 주석·template 제거 후 판정 ⓑ 클래스 토큰 집합 ⓒ script 태그 **안**에서 src∧data-scope 동시 ⓓ 문자 거리 폐기 → **형제 인접**(사이에 여는 태그 0)
      ⓔ 표면 자동발견 + **하한 고정**(이미지 3·영상 5 = 1개씩 빠지는 드리프트에 fail-closed) ⓕ link href 파일 실존."""
    IMG_MIN, CAP_MIN = 3, 5   # 하한 = 현행 표면 수(1개씩 조용히 빠지는 드리프트 차단 · 신설 표면은 이 값을 올린다)
    def _strip(t):   # 주석·template = 런타임 미도달 = 판정 전 제거(형제 게이트 관례 계승)
        t = _re.sub(r'<!--.*?-->', '', t, flags=_re.S)
        return _re.sub(r'<template[^>]*>.*?</template>', '', t, flags=_re.S)
    def _links(t):
        return set(_re.findall(r'<link[^>]+href="([^"]+)"', t))
    def _rail_tag(t):   # nm-rail.js script 태그 **자신** 안에서 src·data-scope 동시 판정(bare substring 우회 차단)
        for tag in _re.findall(r'<script[^>]*>', t):
            if _re.search(r'src="nm-rail\.js"', tag):
                m = _re.search(r'data-scope="([a-z]+)"', tag)
                return m.group(1) if m else ''
        return None
    def _has_static_set(t):
        """결과 헤더 → 요약 줄 → 타일이 **형제로 인접**한가(문자 거리 아님)."""
        head = None
        for m in _re.finditer(r'<button[^>]*class="([^"]*)"[^>]*>', t):
            cls = set(m.group(1).split())
            if {'hist-h', 'car-h'} <= cls: head = m.end(); break
        if head is None:
            m = _re.search(r'<button[^>]*id="geniResH"[^>]*>', t)
            if m: head = m.end()
        if head is None: return None   # 결과 헤더 없음 = 이 표면은 정적 세트가 아니다
        g = _re.search(r'<div[^>]*class="hist-grid"', t[head:])
        if not g: return '결과 본문에 타일 그리드 .hist-grid 없음'
        gpos = head + g.start()
        js = list(_re.finditer(r'<div[^>]*class="jobs"', t[head:gpos]))
        if not js: return '타일 위에 요약 줄 컨테이너 .jobs 없음(결과 = 줄+타일 한 세트)'
        between = t[head + js[-1].end():gpos]
        if _re.search(r'<(?!/)[a-zA-Z]', _re.sub(r'<div[^>]*class="hist-empty"[^>]*>.*?</div>', '', between, flags=_re.S)):
            return '요약 줄과 타일 사이에 다른 블록이 끼어 세트가 갈라짐'
        return ''
    surfaces, bad = [], []
    for f in sorted(_g.glob(_os.path.join(ROOT, 'viewer', '*.html'))):
        name = _os.path.basename(f)
        try:
            raw = open(f, encoding='utf-8').read()
        except Exception:
            continue
        t = _strip(raw)
        scope = _rail_tag(t)
        static = _has_static_set(t)
        if scope is None and static is None:
            continue   # 결과 레일과 무관한 표면
        surfaces.append((name, 'cap' if scope == 'cap' else ('img-static' if static is not None and scope is None else (scope or 'img'))))
        miss = []
        need = ['nm-hist.css'] + (['nm-job.css'] if True else [])
        lk = _links(t)
        for href in need:
            if href not in lk: miss.append(href + ' 링크')
            elif not _os.path.exists(_os.path.join(ROOT, 'viewer', href)): miss.append(href + ' 파일 실존 0')
        if scope is not None:
            if scope not in ('img', 'cap'): miss.append('data-scope 미지정/미인식(사진↔영상 격리 선언 = script 태그 안 data-scope="img|cap")')
        elif static:
            miss.append(static)
        if miss: bad.append(name + ': ' + ' · '.join(miss))
    n_img = sum(1 for _, k in surfaces if k != 'cap')
    n_cap = sum(1 for _, k in surfaces if k == 'cap')
    if n_img < IMG_MIN: bad.append('이미지 결과 레일 표면 %d < 하한 %d(시그니처 드리프트로 조용히 빠진 표면 = fail-closed)' % (n_img, IMG_MIN))
    if n_cap < CAP_MIN: bad.append('영상 결과 레일 표면 %d < 하한 %d(상속 누락 = fail-closed)' % (n_cap, CAP_MIN))
    if bad:
        print('❌ 결과 레일 세트 게이트 — 부품 누락(결과 = 요약 줄 + 개별 썸네일 한 세트 · 260806):')
        for x in bad: print('   · ' + x)
        rc = 1
    else:
        print('✅ 결과 레일 세트 게이트 — 이미지 %d표면(정적 세트) + 영상 %d표면(nm-rail.js 상속) 전건 보유 · 주석·template 제외 · 형제 인접 판정 · 하한 고정.' % (n_img, n_cap))
    return rc


_CAP_LAND_EXEMPT = {   # 결과 레일을 상속하되 「완료 적재」가 정당하게 없는 표면 — 늘리려면 사유 1줄(값 사본 복귀의 뒷문이 되면 게이트가 죽는다)
    'viewer/k.html': '프롬프팅 = 산출이 텍스트(프롬프트 문자열)라 썸네일 타일에 그릴 그림이 0 — 무리 적재 = 깨진 타일(CLAUDE.md 「완료 적재 = 파일 산출 탭만」)',
}


def check_cap_rail_land():
    """영상 스튜디오 완료 적재 = **화면 주인·강등 양쪽**(하드 · 운영자 260810 "방금 1개를 제작하고, 추가로 뭐 하나 더 제작하면 방금거가 유실된다").

    ⚠ 신설 사유 = 260810 실측에서 **다섯 탭 중 셋이 반쪽만 적재**하고 있었고 셋 다 화면 증상이 없었다:
      ⓐ 편집 = 강등분(bgLand·pollEditBg)엔 있는데 **화면 주인 완료(showResult)에 없다** → 정상 제작분이 이력에 한 건도 안 쌓임.
         그 자리를 메우라고 260806에 넣은 1줄은 `renderResult` 안에 있었는데 그 함수 스코프에 없는 `fresh`·`outPath`
         (둘 다 lyResult의 파라미터)를 참조해 **매 호출 ReferenceError**였고 감싼 try/catch가 통째로 삼켰다(콘솔 에러 0).
      ⓑ 음원 = 강등분만 적재(포커스 완료 누락) ⓒ 콘티 = 포커스만 적재(강등 누락 = 뒤에서 끝난 콘티 영영 미착지).
    증상은 셋 다 「방금 만든 게 사라짐」 하나뿐이라 **운영자 눈이 유일한 검출기**였다(insta-thumb-miss·brk_misfire 동축).

    기존 게이트는 전부 다른 축 — `check_result_rail_parity` = 레일 **부품**이 섰는가 · `check_nm_jobs` = 작업 **슬롯**이
    안 덮이는가 · `smoke_*` = 화면 **렌더** → 「끝난 작업이 그 레일에 **실제로 얹히는가**」는 축 자체가 없었다.

    판정 = 정적(렌더·LLM·네트워크 0) · 표면 **자동 발견**(`data-scope="cap"` 상속 뷰어 = 새 탭이 조용히 못 빠진다) ·
    주석 줄 제외 · 표면 하한 고정(fail-closed) · **면책표 없이 하드 0**.
    2축 = ① 대상 전건이 완료 착지 호출을 보유 ② 화면 주인 판정(`!_m`·`!mine()`)으로 갈리는 표면은
    **그 분기 안**과 **분기 밖** 양쪽에 착지가 있다(= 위 ⓐⓑⓒ 세 실사고의 술어 그대로).
    """
    import glob as _g, re as _re
    rc = 0
    CAP_MIN = 5   # 하한 = 현행 영상 탭 수(상속이 조용히 빠지면 fail-closed · 신설 탭은 이 값을 올린다)
    LAND = _re.compile(r'nmRail\.add\s*\(|(?<!function )\b[A-Za-z_$][\w$]*Land\s*\(')   # 착지 = 직접 적재 ∨ 착지 헬퍼 호출(sbLand·bgLand — 함수 **정의** 줄은 lookbehind로 제외)
    DEMOTE = _re.compile(r'!\s*_m\b|!\s*mine\s*\(\s*\)')   # 강등 분기 = 「지금은 내가 화면 주인이 아니다」 판정
    surfaces, bad = [], []
    for p in sorted(_g.glob('viewer/*.html')):
        try: t = open(p, encoding='utf-8').read()
        except Exception: continue
        tag = ''
        for s in _re.findall(r'<script[^>]*>', t):
            if _re.search(r'src="nm-rail\.js"', s):
                m = _re.search(r'data-scope="([a-z]+)"', s); tag = m.group(1) if m else ''
                break
        if tag != 'cap': continue
        surfaces.append(p)
        if p in _CAP_LAND_EXEMPT: continue
        code = [('' if ln.strip().startswith('//') else ln.split('//')[0]) for ln in t.split('\n')]   # 주석 줄·꼬리 주석 제거(주석 처리 우회 차단) · 인덱스는 원본과 1:1 유지
        if not any(LAND.search(ln) for ln in code):
            bad.append('%s = 완료 착지(nmRail.add·<이름>Land) 0줄 — 이 탭 제작분은 결과·이전 제작 레일에 영영 안 쌓인다' % p)
            continue
        """② 축 = **함수 범위 안**에서 본다(운영자 260810 실사고의 구조 그대로).
        ⚠ 「파일 어딘가에 분기 밖 착지가 있으면 통과」로 두면 **진범을 못 잡는다** — 편집은 강등 전용 폴(pollEditBg)에도
           착지가 있어서 화면 주인 완료(showResult)의 착지를 지워도 파일 단위로는 멀쩡해 보였다(첫 판 킬테스트 K1 미검출 = 죽은 게이트).
           → 「착지를 가진 강등 분기」가 있는 **그 함수**의, 그 줄 **이후**에도 착지가 있어야 한다(직접 ∨ 거기서 호출한 함수가 보유 = 1단계 추적). """
        starts = [i for i, ln in enumerate(code) if _re.match(r'\s{0,2}(async\s+)?function\s+\w+|\s{0,2}(const|let|var)\s+\w+\s*=\s*(async\s*)?(\(|function)', ln)]
        def _rng(i):   # i가 속한 최상위 함수 범위
            s = max([x for x in starts if x <= i] or [0])
            nxt = [x for x in starts if x > i]
            return s, (nxt[0] if nxt else len(code))
        def _fn_has_land(name):   # 이름의 정의부에 착지가 있는가(1단계 추적)
            for i, ln in enumerate(code):
                if _re.match(r'\s{0,2}(async\s+)?function\s+%s\s*\(|\s{0,2}(const|let|var)\s+%s\s*=' % (name, name), ln):
                    s, e = _rng(i)
                    if any(LAND.search(x) for x in code[s:e]): return True
            return False
        for i, ln in enumerate(code):
            if not (DEMOTE.search(ln) and LAND.search(ln)): continue   # 기준 = 「강등 착지를 실제로 가진 줄」(착지 없는 `if(!_m) return;` 류 = 타임아웃·실패 경로 = 무관)
            s, e = _rng(i)
            after = code[i + 1:e]
            ok = any(LAND.search(x) for x in after)
            if not ok:
                """1단계 추적 = **완료 페이로드(d)를 넘겨받는 호출만**(`showResult(d, …)`·`showLyria(d, …)`).
                ⚠ 호출 이름을 전부 추적하면 게이트가 죽는다 — 같은 함수 안의 형제 헬퍼(bgLand·stop 등)가 착지를 갖고 있어서
                   **진범을 지운 판까지 통과**했다(첫 판 킬테스트 K1·K2 미검출 실측). 완료를 넘겨받는 놈만이 착지의 정당한 대리인이다."""
                calls = set(_re.findall(r'\b([A-Za-z_$][\w$]*)\s*\(\s*d\s*[,)]', ' '.join(after)))
                ok = any(_fn_has_land(c) for c in calls)
            if not ok:
                bad.append('%s:%d = 강등분만 착지 — 같은 완료 분기의 **화면 주인 경로**엔 착지가 없다(260810 ⓐ 편집·ⓑ 음원 실사고: 정상 제작분이 한 건도 안 쌓였다)' % (p, i + 1))
        """거울 축 = 포커스만 착지(강등분이 영영 미착지 = ⓒ 콘티 실사고). 판정 단위 = **함수**다.
        ⚠ 줄 단위로 「착지 없이 return 하는 강등 분기」를 세면 **실패 경로가 통째로 위양성**이 된다(실측 4건 =
           error.log 분기의 `if(!_m){ … return; }` — 실패엔 얹을 산출이 애초에 0이다). 완료를 다루는 함수(= 착지를 가진 함수)가
           강등 분기를 가졌다면 그 함수 안에 **착지를 가진 강등 줄이 최소 1개** 있어야 한다, 로 좁힌다."""
        seen_fn = set()
        for i, ln in enumerate(code):
            if not DEMOTE.search(ln): continue
            s, e = _rng(i)
            if s in seen_fn: continue
            seen_fn.add(s)
            body = code[s:e]
            if not any(LAND.search(x) for x in body): continue          # 착지를 안 하는 함수(실패 전용·판정 전용) = 무관
            if any(DEMOTE.search(x) and LAND.search(x) for x in body): continue   # 강등 착지 보유 = 정합
            bad.append('%s:%d = 완료를 다루는 함수인데 **강등 분기에 착지가 없다** — 뒤에서 끝난 작업이 이력에 영영 미착지(260810 ⓒ 콘티 실사고)' % (p, s + 1))
    if len(surfaces) < CAP_MIN:
        bad.append('영상 결과 레일 상속 표면 %d < 하한 %d(상속이 조용히 빠짐 = fail-closed)' % (len(surfaces), CAP_MIN))
    if bad:
        print('❌ 영상 완료 적재 게이트 — 반쪽 적재(끝난 작업이 결과 레일에 안 얹힌다 · 260810):')
        for x in bad: print('   · ' + x)
        rc = 1
    else:
        print('✅ 영상 완료 적재 게이트 — %d표면(면제 %d) 화면 주인·강등 양쪽 착지 보유 · 주석 줄 제외 · 하한 고정.' % (len(surfaces), len(_CAP_LAND_EXEMPT)))
    return rc


def check_trail_spec():
    """미리보기 코너 옵션 레일 사본 동일성 게이트(운영자 260802).
    3표면의 레일 캡슐·값 칩 규격이 정본 값에서 이탈하면 rc=1. 등재 = CII 「미리보기 코너 옵션 레일」 행."""
    rc = 0; n = 0
    for rel in _TRAIL_SURFACES:
        try:
            css = open(os.path.join(ROOT, rel), encoding='utf-8').read()
        except Exception:
            continue
        css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)   # 주석 제거(주석 속 셀렉터·값 오탐 차단 · check_launch_spec 동문)
        for ax, sels, spec in _TRAIL_AXES:
            body = ''
            for m in _CSS_RULE.finditer(css):
                if any(sel in [p.strip() for p in m.group(1).split(',')] for sel in sels):
                    body += m.group(2)
            if not body:
                print('❌ 코너 레일 게이트 — %s에 「%s」 규칙 미발견(레일 미보유 표면이면 _TRAIL_SURFACES에서 빼라)' % (rel, ax)); rc = 1; continue
            n += 1
            body_ns = re.sub(r'\s+', '', body)
            miss = [d for d in spec if d not in body_ns]
            if miss:
                print('❌ 코너 레일 사본 드리프트 — %s 「%s」 누락: %s → 정본(CII 「미리보기 코너 옵션 레일」) 값 그대로 계승하라'
                      % (rel, ax, ', '.join(miss))); rc = 1
        pred = _TRAIL_EMPTY_PRED_BY.get(rel, _TRAIL_EMPTY_PRED)   # 빈 캡슐 소거 술어(표면별 정본 · 프리픽스·id는 자유)
        if pred not in re.sub(r'\s+', '', css):
            print('❌ 코너 레일 게이트 — %s 빈 캡슐 소거 술어 미보유/이탈 → `…%s` 그대로 계승하라'
                  % (rel, pred)); rc = 1
    if rc == 0:
        print('✅ 코너 레일 게이트 — %d표면 × %d축 사본 동일(캡슐·값 칩 그룹·값 칩 · 한 표면만 고치고 잊는 드리프트 차단 · 신규 편입 = _TRAIL_SURFACES).'
              % (len(_TRAIL_SURFACES), len(_TRAIL_AXES)))
    return rc


# ── 미리보기 중앙 = 업로드 픽토 1개 게이트 (운영자 260802 "그 가운데는 무조건 사진첩만 있는거임 · 텍스트랑 같이 있는거 없어") ──
#   왜 = 이 규칙은 **탭마다 재발하기 딱 좋은 종류**다. 260721 AI 생성에 「글|사진 반갈 듀오」가 들어갔고 tr이 그걸 통계승해
#   두 표면이 같이 어긋났다(260802 원복). 표면이 늘 때마다 중앙에 버튼을 하나 더 붙이는 유혹은 계속 생기는데,
#   스모크는 AI 생성 한 탭(smoke_parity C5b)만 잰다 → 나머지 표면은 무방비. 그래서 커밋 단계에서 전 뷰어를 센다.
#   계약 = 빈 상태 무대(.cpv-empty) 안 진입 버튼(.cpv-photobtn)은 **최대 1개**(사진·영상·파일 업로드 그 하나).
#   0개 = 정당(k·song = 중앙이 대기 문구라 버튼 없음). 텍스트·참고자료 등 나머지 진입점 = 코너 옵션 레일(CII 해당 행).
#   ⚠ JS 문자열로 그리는 빈 상태(thumb `st.innerHTML = '<div class="cpv-empty">…'`)도 같은 정규식에 걸린다 = 사각 0.


def check_prev_center():
    """미리보기 빈 상태 중앙 = 업로드 픽토 단독 게이트(운영자 260802).
    .cpv-empty 블록 안 .cpv-photobtn이 2개 이상이면 rc=1. 등재 = CII 「합성 미리보기 쉘」 행."""
    import glob as _g
    rc = 0; n = 0; surf = 0
    for fp in sorted(_g.glob(os.path.join(ROOT, 'viewer', '*.html'))):
        rel = os.path.relpath(fp, ROOT)
        try:
            html = open(fp, encoding='utf-8').read()
        except Exception:
            continue
        hit = False
        for m in re.finditer(r'<div class="cpv-empty"', html):   # 블록 = div 깊이 카운터로 정확히 닫는다(정규식 게으른 매칭은 중첩에서 샌다)
            i = m.start(); d = 0; j = i; blk = ''
            while j < len(html):
                t = html.find('<', j)
                if t < 0:
                    break
                if html.startswith('<div', t):
                    d += 1
                elif html.startswith('</div', t):
                    d -= 1
                    if d == 0:
                        blk = html[i:t]; break
                j = t + 4
            if not blk:
                continue
            hit = True; n += 1
            cnt = len(re.findall(r'class="[^"]*cpv-photobtn', blk))
            if cnt > 1:
                print('❌ 미리보기 중앙 게이트 — %s 빈 상태 무대에 진입 버튼 %d개 = 중앙은 업로드 하나뿐(운영자 260802). '
                      '나머지 진입점은 코너 옵션 레일로 빼라(CII 「미리보기 코너 옵션 레일」)' % (rel, cnt)); rc = 1
        if hit:
            surf += 1
    if rc == 0:
        print('✅ 미리보기 중앙 게이트 — 빈 상태 무대 %d개(%d표면) 전부 진입 버튼 ≤1(중앙 = 업로드 단독 · 텍스트·참고 진입점은 코너 레일).' % (n, surf))
    return rc


_ONOFF_BASE = {   # 파일별 기존 정당 사용 스냅샷(260803) — 증가 = FAIL · 축소 지향(해소되면 그 자리에서 줄여라)
    'viewer/thumb.html': 1,   # 안내문 값 순환(#guideTog = OFF/모드 라벨 다값 — 이진 아님 · 운영자 260803 비대상 유보)
    'viewer/index.html': 4,   # 설정 행 토글 4종(원격 ·잠금 lockOnBtn · 이미지생성 genImgOnBtn · 키워드알림 kwAlertBtn) — 스튜디오 밖 · 후속 전환 TODO
    'viewer/k.html': 1,       # 발사 페이로드 set['웹툰']='ON/OFF' = 서버 계약(표시 아님 · 무접촉)
}


# 진입 어휘 = document(+속성 체인) 계열 · $ / $$ — 평의회3 실측 우회 18수법 중 14건이 이 확장으로 닫힌다
_GENI_ENTRY_RE = re.compile(
    r"""(?:(?:window\s*\.\s*)?document(?:\s*\.\s*\w+)*\s*\.\s*(?:querySelector(?:All)?|getElementsByClassName|evaluate)|\$\$?)\s*\(\s*(['"`])(.*?)\1""",
    re.S)
_GENI_SCOPE_BASE = frozenset()   # 면책 스냅샷 = 비어 있음(260803 6차 전수 정리 완료) — 늘리려면 사유를 여기 주석에 남긴다


def check_geni_scope():
    """geni 어휘 전역 질의 금지 게이트(운영자 260803 6차 "게이트 ㄱㄱ" · 평의회3 지적 반영 2차).

    ⚠ 신설 사유 = **같은 함정에 하루 세 번** 걸렸다. 설정▸다운로드 창(`#dlgrab`)이 AI 생성 폼(`#genidlg`)의
    문법을 통째 계승해서 `.geni-body`·`.geni-histfold` 같은 클래스를 **공유**한다. 게다가 그 폼은 홈이 둘이다
    (팝업 `#genidlg` ↔ 스튜디오 이식 `#geniHost` · geniMount가 노드를 통째 옮긴다). 그래서 전역 질의는
    **문서순 첫 매치 = 남의 창**을 물 수 있고, 이식 중에는 구조적으로 그렇게 된다(#geniHost가 #dlgrab보다 뒤).
      · 실사고1 = `geniOutPlace` 전역 `.geni-body` → 폰 1단에서 결과 레일이 다운로드 창 안으로 이사해 화면 소멸
        (rect 0×0 · offsetParent null · **콘솔 에러 0 = 완전 무증상** · 그 창이 본문 재구축하면 노드 영구 소멸).
      · 실사고2 = `geniInit` 전역 `.geni-histfold` → 남의 창 폴드에 핸들러 덧바인딩(CDP 리스너 0→1 · 증상 잠복).
      · 잠복3 = 문서 말미 `cscrollAttach(document.querySelector('.geni-body'))`(260803 6차 id 앵커로 선봉합).
    사후 실증 = 사고 시점 커밋 3개에 이 게이트를 돌리면 rc=1로 **3건 전부 지목**된다(평의회3 D축 · 사후 장식 아님).

    판정(평의회3 A축 반영 = 「호출자 매칭」 → **「셀렉터 기준 + 앵커 화이트리스트」로 역전**):
      대상 = viewer/*.html + viewer/*.js 안, document(속성 체인 포함)·$·$$ 계열 호출의 셀렉터 리터럴(작은·큰·백틱).
      셀렉터를 콤마로 쪼갠 **각 항**이 `geni-` 어휘를 담고 있으면, 그 항은 **`#`(id 앵커)로 시작**해야 한다. 아니면 FAIL.
      (id는 문서 유일이라 「어느 창의 것인가」 애매성이 소멸 = 사고의 정체를 정확히 겨눈다. id 화이트리스트로 더 좁히면
      정당한 고유 id[`#geniGauges .geni-gg`·`#geniColorGauges .geni-gg`]까지 막힌다 = 실측 위양성 2건이라 폐기.) (구판은 「`.geni-`로 시작만 안 하면 통과」라 `dialog .geni-body`·
      `div.geni-body`·`#x, .geni-body`·`[class*=geni-]`·`document.body.querySelector`·백틱·getElementsByClassName이
      전부 빠져나갔다 — 특히 `dialog .geni-body`는 #genidlg·#dlgrab **둘 다 <dialog>**라 사고와 100% 동일하다.)
      스코프 호출(`geniRoot().querySelector`·`h.querySelector`)은 진입 어휘가 아니라 자연 통과 = 권장 문법.
      주석 줄(`//`·`*` 시작)은 제외 = 문서·금지예시가 자기 자신을 잡는 위양성 차단(평의회3 B1).
    남은 한계(정직) = **변수 경유**(`const s='.geni-body'; qs(s)`)는 정적으로 못 잡는다(평의회3 A축 잔여 1건).
    비용 = 정적 문자열 검사 76ms(평의회3 실측 = check_refs 전체의 0.4~0.6%) · 렌더·LLM·네트워크 0.
    """
    import glob as _g
    bad = []
    files = sorted(_g.glob(os.path.join(ROOT, 'viewer', '*.html')) + _g.glob(os.path.join(ROOT, 'viewer', '*.js')))
    for fp in files:
        rel = os.path.relpath(fp, ROOT)
        try:
            src = open(fp, encoding='utf-8').read()
        except Exception:
            continue
        for m in _GENI_ENTRY_RE.finditer(src):
            sel = m.group(2)
            if 'geni-' not in sel:
                continue
            ln = src.count('\n', 0, m.start()) + 1
            line = src.split('\n')[ln - 1].strip()
            if line.startswith('//') or line.startswith('*') or line.startswith('/*'):
                continue          # 주석 안 예시 = 위양성(평의회3 B1)
            for part in sel.split(','):
                part = part.strip()
                if 'geni-' not in part:
                    continue
                if part.startswith('#'):
                    continue          # **id 앵커면 통과** — id는 문서 유일이라 「어느 창의 것인가」 애매성이 사라진다(사고의 정체 = 문서순 첫 매치).
                                      # ⚠ 화이트리스트(#genidlg·#geniHost·#geniOut·#dlgrab)로 좁히면 정당한 고유 id(#geniGauges .geni-gg 등)까지 막는다 = 실측 위양성 2건 → 규칙은 「#로 시작」.
                key = rel + '::' + part
                if key in _GENI_SCOPE_BASE:
                    continue
                bad.append('%s:%d  %s' % (rel, ln, part))
    if bad:
        print('❌ geni 전역 질의 게이트 — geni 어휘는 #genidlg·#geniHost·#dlgrab이 공유한다(전역 질의 = 남의 창을 문다 · 260803 6차 실사고 2건 + 잠복 1건):')
        for b in sorted(set(bad)):
            print('   -', b, '→ id 앵커(`#genidlg .geni-…` 처럼 `#`로 시작) 또는 스코프 호출(`geniRoot().querySelector`·`h.querySelector`)로 고쳐라.')
        return 1
    print('✅ geni 전역 질의 게이트 — viewer html·js 전 표면 0건(폼 두 홈 ↔ 다운로드 창 어휘 공유 사고 재발 차단).')
    return 0


def check_onoff_literal():
    """이진 토글 ON/OFF 리터럴 금지 게이트(운영자 260803 "off 이런거는 on off로 하는게 아니라 기능 워딩이 점등하냐 안하냐로 onoff").
    정본 = thumb #cnTog(260718 '라벨 자체 점등') — 260803에 전 스튜디오 확산 완료. 이 게이트는 재발(새 탭·새 옵션이 구 문법 부활)을 커밋 시점에 차단한다.
    축 = ⓐ 마크업: aria-pressed 요소의 표시 텍스트가 정확히 ON/OFF ⓑ JS: `? 'ON' : 'OFF'`류 이진 텍스트 세팅(값 순환 다값 맵·비 ON/OFF 라벨은 자연 비대상).
    면책 = _ONOFF_BASE(파일별 스냅샷 · 초과분만 FAIL = raw baseline 문법 동문)."""
    import glob as _g
    rc = 0; total = 0
    for fp in sorted(_g.glob(os.path.join(ROOT, 'viewer', '*.html'))):
        rel = os.path.relpath(fp, ROOT)
        try:
            html = open(fp, encoding='utf-8').read()
        except Exception:
            continue
        n = len(re.findall(r'<[^>]*aria-pressed[^>]*>\s*(?:ON|OFF)\s*<', html)) \
            + len(re.findall(r"\?\s*'(?:ON|OFF)'\s*:\s*'(?:ON|OFF)'", html))
        total += n
        base = _ONOFF_BASE.get(rel, 0)
        if n > base:
            print('❌ ON/OFF 리터럴 게이트 — %s에 이진 ON/OFF 표기 %d건(> 면책 %d) = 워드 토글 정본 위반(기능 워딩 자체 점등 · thumb #cnTog · 운영자 260803). '
                  '정당 사유(페이로드·다값 순환)면 _ONOFF_BASE에 사유와 함께 등재하라' % (rel, n, base)); rc = 1
    if rc == 0:
        print('✅ ON/OFF 리터럴 게이트 — 이진 토글 표기 잔존 %d건 전부 면책분(페이로드·다값 순환·설정 TODO) · 신규 0(워드 점등 정본 유지).' % total)
    return rc


# ── 값축 거처 게이트 (운영자 260804 "idea go" — 그날 컷 편집 지적의 기계화) ──────────────────────
# 왜: 컷 편집 「강도」(4택1)가 비율·해상도와 **같은 성격의 축인데 다른 문법**으로 그려지고 있었다 —
#   비율·해상도는 헤더 우측 칩 나열(hdChips), 컷만 헤더 **아래** 별도 행(segs) = 한 스택 안 두 문법.
#   기존 게이트가 하나도 못 잡은 이유 = 전부 「값이 정본과 같은가」를 보는데 이건 **같은 축을 어디에 그리는가**라
#   축 자체가 레포에 없었다. 260728 Q10에서 비율·해상도를 헤더 칩으로 통일할 때 컷만 빠진 채 6일 잠복했고,
#   결국 운영자가 눈으로 찾아 지적해야 발견됐다 — 사람이 짚어야 아는 구조를 없앤다(smoke_hitzone 신설 동기와 같은 축).
# 계약 = 「카드 헤더가 담당하는 **다값** 축은 헤더 우측 칩(hdChips)으로만 그린다」.
# 위양성 통제 3겹(이 게이트의 전부 — 잘못 울면 아무도 안 본다):
#   ⓐ 스코프 = **살아있는 카드 렌더 경로만** 자동 발견(cardHtml 본문 + 그 안에서 `body=XXX()`로 불리는 함수).
#      도먼트 시트(prm())에 남은 구 문법 사본 7건은 스코프 밖 = 도먼트 보존 관례와 충돌 0.
#   ⓑ 대상 = **다값 축만**(CYC 길이 ≥3). 이진 OFF/ON은 워드 점등이 정본이라 애초에 칩 나열 대상이 아니고,
#      그 축은 check_onoff_literal이 전담한다 — 섞으면 「hdChips로 고쳐라」가 오답이 된다.
#   ⓒ 대상 축 = CARDAX 값 ∪ 스코프 내 hdChips 축(= 카드 **헤더**가 그리는 축)에 한정. fit(방식)처럼
#      「헤더는 이미 비율 칩이 차지 → 방식은 아래 구획」이 정본인 축은 자연히 빠진다(260712 3차 동급 위계 계약 보존).
# 자동 발견 = 이 문법을 쓰는 뷰어(cardHtml ∧ hdChips 보유) 전부 · 새 body 함수도 스코프에 자동 편입 = 손 목록 0.
# 면책표 없음 = 현재 위반 0. 정당 예외가 실증되면 그때 _AXHOME_BASE를 신설하고 사유를 남긴다(부채는 안 만들고 시작한다).
def _js_fnbody(src, name):
    """`function <name>(...) { … }` 본문을 중괄호 균형으로 잘라낸다(정규식 한 방으로는 중첩을 못 센다)."""
    m = re.search(r'(?m)^\s*function\s+' + re.escape(name) + r'\s*\([^)]*\)\s*\{', src)
    if not m:
        return ''
    i = m.end() - 1
    depth = 0
    for j in range(i, len(src)):
        if src[j] == '{':
            depth += 1
        elif src[j] == '}':
            depth -= 1
            if depth == 0:
                return src[i:j + 1]
    return src[i:]


def check_axis_chip_home():
    """다값 카드 헤더 축은 헤더 우측 칩(hdChips) 단일 문법 — 본문 행(segs) 혼용이면 rc=1."""
    import glob as _g
    rc = 0; n_surf = 0; axes_all = []
    for fp in sorted(_g.glob(os.path.join(ROOT, 'viewer', '*.html'))):
        rel = os.path.relpath(fp, ROOT)
        try:
            src = open(fp, encoding='utf-8').read()
        except Exception:
            continue
        if 'function cardHtml(' not in src or 'hdChips' not in src:
            continue   # 이 문법을 쓰는 표면만(자동 발견 — 새 스튜디오 탭이 같은 골격을 쓰면 자동 편입)
        n_surf += 1
        scope = _js_fnbody(src, 'cardHtml')
        for callee in sorted(set(re.findall(r'body\s*=\s*([A-Za-z_$][\w$]*)\s*\(', scope))):
            scope += '\n' + _js_fnbody(src, callee)   # 카드 본문 렌더 함수(cutBody·trimBody …) = 같은 렌더 경로
        scope = re.sub(r'/\*.*?\*/', '', scope, flags=re.S)
        scope = re.sub(r'(?m)^\s*//.*$', '', scope)   # 주석 속 예시 코드 오탐 차단
        mc = re.search(r'const\s+CYC\s*=\s*\{(.*?)\};', src, re.S)
        multi = {ax for ax, vals in re.findall(r"(\w+)\s*:\s*\[([^\]]*)\]", mc.group(1) if mc else '')
                 if len(re.findall(r"'[^']*'", vals)) >= 3}   # 다값 축(3값 이상) — 이진 OFF/ON = 워드 점등 축이라 대상 아님(check_onoff_literal 전담)
        cardax = set()
        m = re.search(r'const\s+CARDAX\s*=\s*\{([^}]*)\}', src)
        if m:
            cardax = set(re.findall(r":\s*'([^']+)'", m.group(1)))
        head = (set(re.findall(r"hdChips\(\s*'([^']+)'", scope)) | cardax) & multi
        axes_all += sorted(head)
        for ax in sorted(set(re.findall(r"segs\(\s*'([^']+)'", scope)) & head):
            print('❌ 값축 거처 게이트 — %s: 카드 헤더 축 「%s」를 본문 행(segs)으로 그린다 = 비율·해상도(hdChips)와 두 문법 혼용. '
                  '헤더 우측 칩으로 통일하라(정본 = cardHtml의 hdChips 호출 · 값·순서·data-p 배선은 그대로 옮기면 된다 — 둘 다 같은 pc()라 핸들러 무접촉)' % (rel, ax)); rc = 1
    if rc == 0:
        print('✅ 값축 거처 게이트 — 다값 카드 헤더 축 %d개(%s · %d표면) 전부 헤더 우측 칩 단일 문법(본문 행 혼용 0 · 도먼트 시트는 스코프 밖).'
              % (len(axes_all), '·'.join(axes_all) or '없음', n_surf))
    return rc


# ── 정본 규칙 상속 대조 게이트 (운영자 260803 "아이디어 진행" — 오늘 두 사고의 **공통 뿌리** 봉합) ──────────
# 왜: 260803에 같은 뿌리로 사고가 두 번 났고, 방향만 반대였다.
#   ⓐ `.gs-v` = 정본 버튼 스킨을 입으면서 **cursor(어포던스)까지 따라와** 「눌러도 아무 일 없는 자리」 6건
#   ⓑ `.trail-i` = 정본 히트패드 `::after{inset:-6px -4px}`가 **안 따라와** 영상 셸 히트존이 이미지의 2.4배 좁음
#   둘 다 「정본 컴포넌트를 다른 표면에 옮길 때 **규칙 세트의 일부만 따라온 것**」이다.
#   기존 `check_trail_spec`은 5축(캡슐 색·radius·글리프 12·버튼 22 …) **값**을 대조하는데,
#   히트패드 `::after`는 그 축 목록에 없어서 오늘까지 아무도 못 잡았다 — 축을 사람이 하나씩 추가하는 방식의 구조적 사각.
#   → **선언 이름 집합 자체를 자동 대조**한다. 정본에 있는 선언이 표면에 없으면 FAIL = 축 관리가 필요 없다.
# 대조에서 빼는 것 = **어포던스 선언**(cursor·tap-highlight). CII 「스킨은 계승, 어포던스는 비계승」 계약 그대로 —
#   같은 부품이라도 표면에 따라 진짜 토글일 수도 리드백일 수도 있어 cursor는 **일괄 상속 대상이 아니다**(260803 ⓐ의 교훈).
#   그 축은 check_affordance_inherit(정적) + smoke_hitzone H3(런타임)가 이미 전담한다.
# 값이 아니라 **존재 여부**만 본다 = 스코프별 색·크기 정당 차이에 위양성 0.
_DECL_PARTS = ('.trail-i', '.trail-v', '.trail-g', '.trail-div', '.gs-v')   # 레일 부품 = §3-5 「무조건 상속」 대상
_DECL_SKIP = {'cursor', '-webkit-tap-highlight-color'}                      # 어포던스 = 비계승(위 계약)
_DECL_BASE = {}   # 면책 = '파일::부품::의사요소' → 그 시점 누락 선언 집합(정당 사유는 주석으로)


def _decl_rules(src, tail):
    """<style> 안에서 `<스코프> <부품><의사요소?>`로 끝나는 규칙의 선언 **이름** 집합."""
    css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', src, re.S))
    out = {}
    for sels, body in re.findall(r'([^{}]+)\{([^{}]*)\}', css):
        for sel in sels.split(','):
            sel = sel.strip()
            m = re.search(re.escape(tail) + r'(::[a-z-]+|:[a-z-]+)?\s*$', sel)
            if not m:
                continue
            props = {p.split(':')[0].strip() for p in body.split(';') if ':' in p}
            out.setdefault(m.group(1) or '', set()).update(props - _DECL_SKIP)
    return out


def check_trail_decl_parity():
    """레일 부품의 **정본 선언 집합**이 전 표면에 상속됐는지 대조(값 아님·존재 여부).
    정본 = viewer/index.html · 표면 = `class="trail` 보유 파일 자동 발견(check_trail_spec 동축 = 새 탭이 조용히 못 빠진다)."""
    import glob as _g
    try:
        base_src = open(os.path.join(ROOT, 'viewer', 'index.html'), encoding='utf-8').read()
    except Exception:
        print('⚠️ 정본 규칙 상속 대조 — index.html 미독출(스킵)')
        return 0
    surf = []
    for fp in sorted(_g.glob(os.path.join(ROOT, 'viewer', '*.html'))):
        if fp.endswith('index.html'):
            continue
        try:
            s = open(fp, encoding='utf-8').read()
        except Exception:
            continue
        if 'class="trail' in s:
            surf.append((os.path.relpath(fp, ROOT), s))
    rc = 0
    checked = 0
    for part in _DECL_PARTS:
        base = _decl_rules(base_src, part)
        if not base:
            continue
        for rel, s in surf:
            got = _decl_rules(s, part)
            if not got:
                continue          # 그 표면이 이 부품을 안 쓴다 = 대상 아님
            checked += 1
            for pseudo, props in base.items():
                miss = props - got.get(pseudo, set())
                exempt = _DECL_BASE.get('%s::%s::%s' % (rel, part, pseudo or '-'), set())
                miss -= set(exempt)
                if not miss:
                    continue
                tag = part + (pseudo or '')
                print('❌ 정본 규칙 상속 대조 — %s의 `%s`에 정본 선언 누락: %s. '
                      '정본(viewer/index.html)에는 있고 이 표면에는 없다 = 스킨만 옮기고 규칙 일부가 안 따라온 것'
                      '(260803 실사고 = `.trail-i::after` 히트패드 누락으로 영상 셸 히트존이 이미지의 2.4배 좁았다). '
                      '정당한 차이면 _DECL_BASE에 사유와 함께 등재하라' % (rel, tag, sorted(miss)))
                rc = 1
    if rc == 0:
        print('✅ 정본 규칙 상속 대조 — 레일 부품 %d조합 전건 정본 선언 상속(어포던스 선언은 비계승 계약이라 대조 제외).' % checked)
    return rc


# ── 어포던스 비계승 게이트 (운영자 260803 "응 붙여줘" — 「스킨은 계승, 어포던스는 비계승」의 정적 몫) ──────────────
# 왜: 260803 실사고 6건의 뿌리 = 리드백 칩 `.gs-v`가 정본 `.trail-i`(진짜 버튼) **외형을 스킨으로 입으면서
#   `cursor:pointer`까지 통째로 딸려온 것**. 외형 계승은 이 레포의 정본 방식이고 맞다 — 그런데 「이건 눌린다」는
#   **신호**까지 복사되면 손가락 커서가 뜨는데 아무 일도 안 일어난다(tr 「40」·콘티 「2K」·큐영상 「0건」 …
#   sb·k·song·vd는 .gs-tog가 0개 = 스트립 전체가 거짓말이었다).
# 런타임 짝 = smoke_hitzone.js H3. 이 정적 게이트는 그 **앞단**이다 — 커밋에서 막으면 브라우저까지 안 간다.
# 판정: 뷰어 <style> 안에서 `cursor:pointer`를 선언하는 규칙의 **마지막 컴파운드 클래스**를 뽑아,
#   그 클래스를 실제로 달고 있는 HTML 요소가 하나라도 「컨트롤 마커 0」이면 위반.
#   컨트롤 마커 = button/a/label/summary/input/select 태그 · role="button" · onclick · tabindex · data-*(위임 훅).
#   → 셀렉터가 태그 컨트롤이거나(button:hover 등) role을 이미 포함하면 애초에 대상 아님 = 위양성 차단.
_AFFORD_MARK = re.compile(r'\brole\s*=\s*"button"|\bonclick=|\btabindex=|\bdata-[a-z-]+\s*=')
_AFFORD_CTRL_TAG = ('button', 'a', 'label', 'summary', 'input', 'select', 'textarea')
_AFFORD_BASE = {   # 파일별 선존 스냅샷 = **260803 실측값**(추측 금지 — 코드로 세서 박았다) · 초과만 FAIL · 축소 지향
    # ⚠ 이 숫자는 「전부 버그」가 아니다. 이 게이트는 정적 근사라 **위임으로 실제 반응하는 노드**도 함께 센다
    #   (예 edit `.hd`·`.clip`·`.lytab` = document 클릭 위임이 처리 · index `.card`·`.chip`·`.seg` 동축).
    #   정적으로는 위임 대상 셀렉터를 알 수 없으므로 그 판별은 런타임 짝(smoke_hitzone H3)이 맡고,
    #   여기서는 **새로 늘어나는 것만** 막는다 = 「스킨 복사할 때 cursor까지 딸려오는」 재발 차단이 이 게이트의 몫.
    #   줄이는 법 = 위임 노드에 role/data-* 마커를 달아 의도를 표면화하거나, 장식이면 cursor를 걷는다.
    'viewer/edit.html': 5,
    'viewer/index.html': 11,
    'viewer/k.html': 1,
    'viewer/ly.html': 2,
    'viewer/thumb.html': 1,
    'viewer/tr.html': 1,
    'viewer/vd.html': 2,
}


def check_affordance_inherit():
    """어포던스 비계승 게이트 — cursor:pointer가 「누를 수 없는 노드」에 걸려 있는지 정적 검출.
    스킨 계승(외형)은 정본이고 권장이다. 다만 cursor·press 같은 **어포던스 신호**는 role/핸들러가 있는 노드에만 붙어야 한다.
    면책 = _AFFORD_BASE(파일별 스냅샷 · 초과분만 FAIL = raw baseline 문법 동문). 런타임 짝 = smoke_hitzone.js H3."""
    import glob as _g
    rc = 0
    tot = 0
    for fp in sorted(_g.glob(os.path.join(ROOT, 'viewer', '*.html'))):
        rel = os.path.relpath(fp, ROOT)
        try:
            src = open(fp, encoding='utf-8').read()
        except Exception:
            continue
        # <style> 블록만(인라인 style 속성·JS 문자열 제외)
        css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', src, re.S))
        if not css:
            continue
        bad = set()
        for sels, body in re.findall(r'([^{}]+)\{([^{}]*)\}', css):
            if not re.search(r'cursor\s*:\s*pointer', body):
                continue
            for sel in sels.split(','):
                sel = sel.strip()
                if not sel or sel.startswith('@') or sel.startswith('%'):
                    continue
                if 'role="button"' in sel or 'role=button' in sel:
                    continue
                last = re.split(r'[ >+~]', sel.strip())[-1]        # 마지막 컴파운드 = 규칙이 실제로 칠하는 노드
                last = last.split(':')[0]                          # :hover/:active 등 상태 제거
                if not last or last.startswith('['):
                    continue
                tag = re.match(r'^[a-zA-Z]+', last)
                if tag and tag.group(0).lower() in _AFFORD_CTRL_TAG:
                    continue                                        # 태그 자체가 컨트롤 = 대상 아님
                cls = re.findall(r'\.([A-Za-z0-9_-]+)', last)
                if not cls:
                    continue
                key = cls[-1]
                # 그 클래스를 단 요소를 HTML에서 전수 확인 — 하나라도 마커가 없으면 「거짓 어포던스」 후보
                hits = re.findall(r'<([a-zA-Z]+)([^>]*\bclass\s*=\s*"[^"]*\b%s\b[^"]*"[^>]*)>' % re.escape(key), src)
                if not hits:
                    continue                                        # 동적 생성 = 정적으로 못 본다(런타임 H3 몫)
                # JS가 그 클래스를 **선택자로 잡고 있으면** 배선된 것으로 본다(위임·동적 생성 = 정적으로 마커가 안 보이는 정상 경로).
                #   실측 260803 = vd `.monseek`(진행선 시크바)은 JS가 만들고 그 자리에서 핸들러를 붙인다 = 진짜 눌린다 → 위양성이었다.
                #   반증은 유지된다 — JS가 아예 안 잡는 순수 장식 클래스는 그대로 FAIL(주입 테스트로 확인).
                if re.search(r"""['"`]\.%s['"` ,)\]]""" % re.escape(key), src):
                    continue
                for t, attrs in hits:
                    if t.lower() in _AFFORD_CTRL_TAG:
                        continue
                    if _AFFORD_MARK.search(attrs):
                        continue
                    bad.add(key)
                    break
        tot += len(bad)
        base = _AFFORD_BASE.get(rel, 0)
        if len(bad) > base:
            print('❌ 어포던스 비계승 게이트 — %s에서 cursor:pointer가 「누를 수 없는 노드」에 걸린 클래스 %d종(> 면책 %d): %s. '
                  '스킨 계승 시 cursor·press는 비계승 = role/핸들러 있는 노드에만(CII 「미리보기 코너 옵션 레일」 · 운영자 260803). '
                  '위임으로 실제 반응한다면 그 노드에 data-* 마커나 role을 달아 의도를 표면화하라'
                  % (rel, len(bad), base, ', '.join('.' + b for b in sorted(bad))))
            rc = 1
    if rc == 0:
        print('✅ 어포던스 비계승 게이트 — cursor:pointer가 마커 없는 노드에 걸린 클래스 %d종 전부 면책분 · 신규 0(스킨은 계승·어포던스는 비계승).' % tot)
    return rc


# ── 부채 래칫 게이트 (운영자 260803 "ㄱㄱ" — 「면책표가 조용히 비대해지는」 축의 기계화) ───────────────
# 왜: 이 레포의 게이트는 전부 면책표(baseline)를 안고 산다 — 그래야 신규 회귀만 잡고 레포가 안 얼기 때문이다.
#   그런데 면책표는 **한 방향으로만 자란다**: 새 위반을 등재하는 건 1줄이고, 해소분을 지우는 건 아무도 안 한다.
#   시간이 지나면 「알고 동결한 부채」가 「원래 그런 것」으로 굳는다(260802 INK_BASE `{편집:2.6}` 회수 사례 = 사람이 우연히 발견).
#   → 표별 항목 수를 원장에 굽고 **늘면 커밋 차단 · 줄면 낮추라고 알린다**. 줄이는 건 자유, 늘리는 건 사유 필수.
# 발견 = 자동(shared/check_refs.py · shared/smoke_*.js에서 `*_BASE`/`*_EXEMPT` 리터럴을 훑는다) — 새 면책표가 조용히 안 낀다.
# 원장 = shared/debt_ledger.json(기계산출물 · 손편집 금지 · 갱신 = `python3 shared/check_refs.py --debt-sync`).
_DEBT_LEDGER = os.path.join(ROOT, 'shared', 'debt_ledger.json')
_DEBT_SYM = re.compile(r'^(?:const\s+)?(_?[A-Z][A-Z0-9_]*(?:BASE|EXEMPT)[A-Z0-9_]*)\s*=\s*(new Set\(|set\(|[\[{])', re.M)


def _debt_scan():
    """면책표별 항목 수를 센다. 반환 = {'파일::심볼': 개수}."""
    import glob as _g
    out = {}
    files = [os.path.join(ROOT, 'shared', 'check_refs.py')] + sorted(_g.glob(os.path.join(ROOT, 'shared', 'smoke_*.js')))
    for fp in files:
        rel = os.path.relpath(fp, ROOT)
        try:
            src = open(fp, encoding='utf-8').read()
        except Exception:
            continue
        for m in _DEBT_SYM.finditer(src):
            sym, opener = m.group(1), m.group(2)
            i = m.end() - 1
            if opener in ('new Set(', 'set('):
                nxt = src[m.end():m.end() + 40].lstrip()
                if nxt[:1] == ')':
                    out['%s::%s' % (rel, sym)] = 0   # `new Set()` = 빈 면책표(구 코드는 '[' 를 파일 뒤쪽에서 찾아 남의 리터럴을 셌다 · 260803 실측 DOCK_EXEMPT 0→2 오측)
                    continue
                i = src.find('[', m.end() - 1)
                if i < 0:
                    continue
            op = src[i]
            cl = {'{': '}', '[': ']'}[op]
            depth, j, instr, q = 0, i, False, ''
            while j < len(src):
                c = src[j]
                if instr:
                    if c == '\\':
                        j += 2; continue
                    if c == q:
                        instr = False
                elif c in '"\'`':
                    instr, q = True, c
                elif c == op:
                    depth += 1
                elif c == cl:
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            body = src[i + 1:j]
            # 항목 수 = **최상위 depth 콤마 기준**(dict·set·list·튜플키 전부 동일 규칙 · 문자열/주석 안 콤마 제외).
            #   ⚠ 260803 실측 = 구 「'키':」 패턴 카운트는 set(_CLIP_EXEMPT_ID 튜플 2건)·정수키 dict(_QDUP_BASE 100+건)를
            #     전부 0으로 셌다 = 래칫이 「부채 없음」이라 거짓말할 뻔했다. 부정확한 게이트는 게이트가 아니다.
            n, dep, k, instr, q, py = 0, 0, 0, False, '', fp.endswith('.py')
            while k < len(body):
                c = body[k]
                if instr:
                    if c == '\\':
                        k += 2; continue
                    if c == q:
                        instr = False
                elif c in ('"', "'", '`'):
                    instr, q = True, c
                elif py and c == '#':
                    k2 = body.find('\n', k); k = len(body) if k2 < 0 else k2; continue
                elif (not py) and c == '/' and k + 1 < len(body) and body[k + 1] == '/':
                    k2 = body.find('\n', k); k = len(body) if k2 < 0 else k2; continue
                elif (not py) and c == '/' and k + 1 < len(body) and body[k + 1] == '*':
                    k2 = body.find('*/', k); k = len(body) if k2 < 0 else k2 + 2; continue
                elif c in '{[(':
                    dep += 1
                elif c in '}])':
                    dep -= 1
                elif c == ',' and dep == 0:
                    n += 1
                k += 1
            stripped = re.sub(r'(?m)(#|//).*$', '', body).strip()
            if not stripped:
                n = 0                       # 주석·공백만 = 빈 리터럴
            elif not stripped.endswith(','):
                n += 1                      # 트레일링 콤마 없음 = 마지막 항목 미계수분 보정
            out['%s::%s' % (rel, sym)] = n
    return out


def check_debt_ratchet(sync=False):
    """부채 래칫 — 면책표 총량이 원장보다 **늘면 FAIL**(줄면 낮추라고 알린다).
    미해결 부채(원인 미규명·판단 대기)는 원장 open_items에 사람 말로 남긴다 = 잊히지 않게."""
    cur = _debt_scan()
    tot = sum(cur.values())
    try:
        led = json.load(open(_DEBT_LEDGER, encoding='utf-8'))
    except Exception:
        led = {'tables': {}, 'open_items': []}
    old = led.get('tables', {})
    if sync:
        led['tables'] = cur
        led['total'] = tot
        with open(_DEBT_LEDGER, 'w', encoding='utf-8') as f:
            json.dump(led, f, ensure_ascii=False, indent=2)
            f.write('\n')
        print('· 부채 원장 동기 — 총 %d건(%d표)' % (tot, len(cur)))
        return 0
    up = [(k, old.get(k, 0), v) for k, v in sorted(cur.items()) if v > old.get(k, 0)]
    dn = [(k, old[k], cur.get(k, 0)) for k in sorted(old) if cur.get(k, 0) < old[k]]
    if up:
        print('❌ 부채 래칫 — 면책표가 늘었다(%d표 · 총 %d → %d). 늘리는 건 사유 필수:' % (len(up), sum(old.values()), tot))
        for k, a, b in up:
            print('   · %s  %d → %d' % (k, a, b))
        print('   정당한 등재면 커밋 메시지에 사유를 쓰고 `python3 shared/check_refs.py --debt-sync`로 원장을 올려라(그 diff가 곧 승인 기록).')
        return 1
    if dn:
        print('✅ 부채 래칫 — 총 %d건(원장 %d · **%d건 해소**). `--debt-sync`로 원장을 낮춰라: %s'
              % (tot, sum(old.values()), sum(old.values()) - tot, ', '.join('%s %d→%d' % (k, a, b) for k, a, b in dn)))
        return 0
    items = led.get('open_items', [])
    print('✅ 부채 래칫 — 면책 총 %d건(%d표) 원장과 동일 · 증가 0 · 미해결 부채 %d건 추적 중(원장 open_items).' % (tot, len(cur), len(items)))
    for it in items:
        print('   ◦ %s' % it)
    return 0


# ── 모델 표시명 SSOT 게이트 (운영자 260803 5차 "아이디어도 배선해줘" — 표기 드리프트 8종 실사고[Q1285]의 구조 봉합) ──
# 사전 = viewer/nm-models.js(window.NM_MODELS · 정식 표기 단일정본 · sb/k는 런타임 참조). 두 축:
#   ⓐ 음차·변형 래칫 — viewer/*.html·functions/api/*.js에서 음차(클링·시댄스·페이블·오퍼스·제미나이·수노)와
#      변형 표기(Kling 3.0[비Omni]·GPT 5.6[비Sol]·Seedance 2.5[운영자 260803 "2.0이 맞고"]·Gemini 3.1 flash 소문자/Flash image)를
#      세어 파일별 베이스라인 **초과만** FAIL(주석의 운영자 원문 인용·역사 서술 = 선존 면책 · raw baseline 문법 동문 · 줄었으면 그만큼 낮춰라).
#   ⓑ 리터럴 표면 동기(하드) — 서버는 뷰어 자산을 import 못 하므로(api/sb.js DIRECTOR_NM) + 정적 HTML 라벨(k .eng)·
#      index GENI_ENG_ICO가 사전 값과 문자 단위 동일해야 통과 · sb/k엔 <script src="nm-models.js"> 로드 줄 실존.
_MODEL_NM_RE = re.compile(r'클링|시댄스|페이블|오퍼스|제미나이|수노|Kling 3\.0(?! Omni)|GPT 5\.6(?! Sol)|Seedance 2\.5|Gemini 3\.1 [Ff]lash [Ii]mage|Gemini 3\.1 flash')
_MODEL_NM_KEYS = ('fable', 'opus', 'gpt', 'kling', 'veo', 'seedance', 'motion', 'gemini', 'gpt_image', 'suno', 'lyria')
_MODEL_NM_BASE = {   # 파일별 선존 표기 스냅샷(260803 실측 — 전부 주석·운영자 원문 인용 · 가시 문자열은 Q1285에서 소거 완료) · 줄면 그만큼 낮춰라(래칫)
    'functions/api/k.js': 2,        # 클링(지침 파일명·주석)
    'functions/api/moreimg.js': 1,  # 제미나이(주석)
    'functions/api/revise-cards.js': 1,  # 제미나이(주석)
    'functions/api/sb.js': 2,       # 시댄스·클링(주석)
    'functions/api/song.js': 1,     # 수노(주석)
    'functions/api/submit.js': 1,   # 제미나이(주석)
    'viewer/edit.html': 1,          # 페이블(검증 크레딧 주석)
    'viewer/index.html': 35,        # 제미나이·페이블 등(주석 다수) + Gemini 3.1 Flash image 1 = 발행 산출물 원표기(운영자 260622 승인 · 15247)
    'viewer/k.html': 2,             # 클링(운영자 원문 인용 주석)
    'viewer/sb.html': 25,           # 페이블·오퍼스·클링·시댄스·GPT 5.6(역사 서술 주석)
    'viewer/song.html': 5,          # 수노(주석)
    'viewer/thumb.html': 4,         # 제미나이·페이블(주석)
    'viewer/vd.html': 2,            # 페이블·GPT 5.6(주석)
}


def check_model_names():
    """모델 표시명 SSOT 게이트(운영자 260803 5차) — 위 주석 참조. rc=1 = 커밋 차단."""
    import glob as _g
    rc = 0
    # 0) 사전 파싱(fail-closed — 사전이 깨지면 뷰어 모델 라벨이 통째로 undefined)
    try:
        nm_src = open(os.path.join(ROOT, 'viewer', 'nm-models.js'), encoding='utf-8').read()
    except Exception as e:
        print('❌ 모델 표시명 SSOT — viewer/nm-models.js 못 엶(부재/리네임 = sb·k 모델 라벨 전면 사망):', e); return 1
    nm = dict(re.findall(r"^\s*([a-z_0-9]+): '([^']*)'", nm_src, re.M))
    miss = [k for k in _MODEL_NM_KEYS if not nm.get(k)]
    if miss:
        print('❌ 모델 표시명 SSOT — 사전 필수 키 누락/빈 값:', miss); return 1
    # ⓐ 음차·변형 래칫
    for fp in sorted(_g.glob(os.path.join(ROOT, 'viewer', '*.html')) + _g.glob(os.path.join(ROOT, 'functions', 'api', '*.js'))):
        rel = os.path.relpath(fp, ROOT)
        try:
            txt = open(fp, encoding='utf-8').read()
        except Exception:
            continue
        n = len(_MODEL_NM_RE.findall(txt))
        base = _MODEL_NM_BASE.get(rel, 0)
        if n > base:
            hits = sorted(set(_MODEL_NM_RE.findall(txt)))
            print('❌ 모델 표시명 SSOT — %s에 음차·변형 표기 %d건(> 면책 %d) · 검출 = %s → 정식 표기(NM_MODELS 사전 값)로 쓰라. '
                  '주석 인용 등 정당 사유면 _MODEL_NM_BASE[%r] 상향 + 사유(운영자 260803 "모델명 항상 통일")' % (rel, n, base, hits, rel)); rc = 1
    # ⓑ 리터럴 표면 동기(하드)
    try:
        sbj = open(os.path.join(ROOT, 'functions', 'api', 'sb.js'), encoding='utf-8').read()
        m = re.search(r"const DIRECTOR_NM = \{ fable: '([^']+)', opus: '([^']+)', gpt: '([^']+)' \}", sbj)
        if not m:
            print('❌ 모델 표시명 SSOT — api/sb.js DIRECTOR_NM 리터럴 못 찾음(구조 재포맷 시 이 게이트 정규식 동반 갱신)'); rc = 1
        elif (m.group(1), m.group(2), m.group(3)) != (nm['fable'], nm['opus'], nm['gpt']):
            print('❌ 모델 표시명 SSOT — api/sb.js DIRECTOR_NM ≠ 사전: %s vs %s(서버는 사전 import 불가 = 손 동기 · 사전 값으로 맞춰라)'
                  % (m.groups(), (nm['fable'], nm['opus'], nm['gpt']))); rc = 1
        idx = open(os.path.join(ROOT, 'viewer', 'index.html'), encoding='utf-8').read()
        m2 = re.search(r"const GENI_ENG_ICO = \{ gemini: \['([^']+)'[^\]]*\], gpt: \['([^']+)'", idx)
        if not m2:
            print('❌ 모델 표시명 SSOT — index GENI_ENG_ICO 리터럴 못 찾음(재포맷 시 정규식 동반 갱신)'); rc = 1
        elif (m2.group(1), m2.group(2)) != (nm['gemini'], nm['gpt_image']):
            print('❌ 모델 표시명 SSOT — index GENI_ENG_ICO ≠ 사전: %s vs %s' % (m2.groups(), (nm['gemini'], nm['gpt_image']))); rc = 1
        for rel, pat, what in (('viewer/sb.html', r'src="nm-models\.js"', '사전 로드 줄'),
                               ('viewer/k.html', r'src="nm-models\.js"', '사전 로드 줄')):
            t = open(os.path.join(ROOT, rel), encoding='utf-8').read()
            if not re.search(pat, t):
                print('❌ 모델 표시명 SSOT — %s에 %s 없음(NM_MODELS 참조가 미로드 = 라벨 undefined)' % (rel, what)); rc = 1
        kh = open(os.path.join(ROOT, 'viewer', 'k.html'), encoding='utf-8').read()
        m3 = re.search(r'<span class="eng">([^<]+)</span>', kh)
        if m3 and m3.group(1) != nm['gemini']:
            print('❌ 모델 표시명 SSOT — k 참조 라벨(.eng) %r ≠ 사전 %r' % (m3.group(1), nm['gemini'])); rc = 1
    except Exception as e:
        print('❌ 모델 표시명 SSOT — 동기 대조 실패(필수 파일 부재?):', e); rc = 1
    if rc == 0:
        print('✅ 모델 표시명 SSOT — 사전 %d키 · 음차·변형 = 전부 면책분(주석 인용) · 서버/index/k 리터럴 동기 · sb/k 사전 로드 ✓.' % len(nm))
    return rc


def check_twocol_breakpoint():
    """스튜디오 결과 레일 2단 분기점 = 표면 간 한 값 게이트(운영자 260802 "일단 머지해주셈" 승인분).
    왜 = thumb만 1100→900 하향(260802 2차)되고 영상 4탭 사본은 1100에 남아, 운영자 PC 실폭(900~1100 구간)에서
    이미지 2단 · 영상 1단으로 갈라졌다(260802 이미지↔영상 전후비교 실측 = 1000px에서 thumb 475+475 vs edit/song grid none).
    기존 실측기 전부의 사각 — smoke_studioshell은 1280(둘 다 2단인 폭)에서 재고 preview_shot은 430(둘 다 1단)이라
    이 드리프트는 어느 게이트에도 안 걸리고 통과했다. 렌더 0 정적 검사로 커밋 시점에 차단한다.
    대상 = 자동발견: viewer/*.html 중 2단 시그니처(`span 99` = 결과 칼럼 grid-row 문법)를 품은 @media(min-width) 블록 전부
    (현재 thumb·tr·edit·sb·k·song 6표면 — vd 큐영상은 C안 패널 도킹 워크스페이스라 2단 자체가 없어 자연 비대상)."""
    import glob as _g
    vals = {}
    for fp in sorted(_g.glob(os.path.join(ROOT, 'viewer', '*.html'))):
        rel = os.path.relpath(fp, ROOT)
        try:
            html = open(fp, encoding='utf-8').read()
        except Exception:
            continue
        for m in re.finditer(r'@media\s*\(min-width:(\d+)px\)\s*\{', html):
            i = m.end(); d = 1; j = i   # 블록 = 중괄호 깊이 카운터(중첩 규칙 안전 · check_prev_center 깊이 카운터 동문)
            while j < len(html) and d:
                c = html[j]
                if c == '{':
                    d += 1
                elif c == '}':
                    d -= 1
                j += 1
            if 'span 99' in html[i:j]:
                vals.setdefault(rel, set()).add(int(m.group(1)))
    flat = sorted({v for s in vals.values() for v in s})
    if len(flat) > 1:
        print('❌ 2단 분기점 게이트 — 스튜디오 표면 간 분기점이 갈렸다: %s → 정본 = 한 값(thumb 기준 · 한 표면만 고치고 잊는 드리프트 = 260802 실사고)'
              % (' · '.join('%s=%s' % (r, ','.join(map(str, sorted(s)))) for r, s in sorted(vals.items()))))
        return 1
    print('✅ 2단 분기점 게이트 — %d표면 전부 min-width:%spx 한 값(결과 레일 2단 시그니처 자동발견).'
          % (len(vals), flat[0] if flat else '?'))
    return 0


# ── 레이아웃 유발 transition 래칫 (운영자 260804 impeccable 평의회 8/8 · 선별이식 ①) ──
#   왜 = `transition:width|height|padding|margin`은 프레임마다 리플로를 강제한다(= 잰크). 이 레포는 「덜컹」을
#   여러 번 겪었고(260716 도크 마진 -18 "덜컹 원천 소멸" · 260803 스크롤 중 -2px = smoke_studioshell C10)
#   그때마다 **정지·스크롤 위치**만 재는 축을 늘렸다 — 「transition이 재생되는 **중간 프레임**」은 어느 게이트도 안 본다.
#   C10은 스크롤 후 정착 위치를, C7은 창 크기를, C9는 정지 세로축을 잰다. 셋 다 애니메이션 **끝난 뒤**의 그림이다.
#   외부 대조 = pbakaus/impeccable `cli/engine/rules/checks.mjs` `layout-transition`(warn) 룰의 속성 집합을
#   그대로 채택(width·height·padding·margin + min/max 변종) — 임계값 창작 0 · 그쪽 디텍터·훅·커맨드는 미도입
#   (평의회 실측 = 59룰 통째 적용 시 경고 690건 중 574건[83.2%]이 글래스·글로우 등 **이 레포 정본**이라 위양성).
#   ⚠ 하드 0 금지 = 래칫 — 현행 7건은 전부 아코디언(max-height)·모프(width) 정본이라 제거 = [4] 창작금지 충돌.
#   면책 `_LAYOUT_TRANS_BASE` = 파일별 스냅샷(초과만 FAIL · 줄면 낮추라고 알린다 = raw baseline 문법 동문).
#   표면 자동 발견(`viewer/*.html`+`viewer/*.css`) = 새 뷰어가 조용히 빠질 수 없다.
_LT_DECL = re.compile(r'transition(?:-property)?\s*:\s*([^;{}"\'<>]+)')
_LT_PROP = re.compile(r'\b(?:max-|min-)?(?:width|height|padding|margin)\b')
_LAYOUT_TRANS_BASE = {   # 260804 실측 스냅샷 — 전부 선존 아코디언·모프(신규 반입 0). 청산하면 그만큼 낮춰라(래칫).
    'viewer/edit.html': 1,    # .pvsec 레일 앵커 --pvw 폭 모프
    'viewer/index.html': 4,   # .pmenu-sub 아코디언 · .tgroup-h 하단 간격 · 큐 행 height/margin/padding · .qrow-out 퇴장
    'viewer/thumb.html': 2,   # .cpprev-box 편집 레이 폭 모프 · .cartrack 트랙
}


def check_layout_transition():
    """레이아웃 유발 transition 래칫(위 주석 참조). rc=1 = 커밋 차단."""
    import glob as _g
    cur, det = {}, {}
    for fp in sorted(_g.glob(os.path.join(ROOT, 'viewer', '*.html')) + _g.glob(os.path.join(ROOT, 'viewer', '*.css'))):
        rel = os.path.relpath(fp, ROOT).replace(os.sep, '/')
        try:
            txt = open(fp, encoding='utf-8').read()
        except Exception:
            continue
        lines = txt.splitlines()
        for m in _LT_DECL.finditer(txt):
            if not _LT_PROP.search(m.group(1)):
                continue
            ln = txt.count('\n', 0, m.start()) + 1
            head = lines[ln - 1].lstrip() if ln <= len(lines) else ''
            if head.startswith(('//', '*', '/*')):   # 주석 줄 = 서술 · 비대상
                continue
            cur[rel] = cur.get(rel, 0) + 1
            det.setdefault(rel, []).append(ln)
    up = [(k, _LAYOUT_TRANS_BASE.get(k, 0), v) for k, v in sorted(cur.items()) if v > _LAYOUT_TRANS_BASE.get(k, 0)]
    if up:
        print('❌ 레이아웃 유발 transition 래칫 — 새 잰크 선언(width/height/padding/margin 전이 = 프레임마다 리플로):')
        for k, a, b in up:
            print('   · %s  %d → %d  (줄 %s)' % (k, a, b, ','.join(map(str, det.get(k, [])))))
        print('   고쳐라 = transform/opacity 전이로 바꾸거나(합성 전용 = 리플로 0), 정본상 불가피하면')
        print('   운영자 승인 후 _LAYOUT_TRANS_BASE 갱신 + 사유 주석(raw baseline 문법 동문).')
        return 1
    dn = [(k, _LAYOUT_TRANS_BASE[k], cur.get(k, 0)) for k in sorted(_LAYOUT_TRANS_BASE) if cur.get(k, 0) < _LAYOUT_TRANS_BASE[k]]
    if dn:
        print('✅ 레이아웃 유발 transition 래칫 — 총 %d건 · **%d건 청산**. _LAYOUT_TRANS_BASE를 낮춰라: %s'
              % (sum(cur.values()), sum(a - b for _, a, b in dn),
                 ', '.join('%s %d→%d' % (k, a, b) for k, a, b in dn)))
        return 0
    print('✅ 레이아웃 유발 transition 래칫 — %d표면 총 %d건 = 면책 스냅샷과 동일(신규 잰크 0 · 자동발견).'
          % (len(cur), sum(cur.values())))
    return 0


# ── @keyframes 중복 정의 게이트 (평의회 260804 4·5·8번 · 하드 0) ──────────────
#   왜 = CSS Animations L1 §2 = **같은 이름이 두 번 선언되면 뒤엣것이 앞엣것을 통째로 대체**한다(병합 아님·부분 오버라이드 아님).
#   즉 중복은 「무해한 사본」이 아니라 **앞 선언을 조용히 삭제하는 문장**이다.
#   실사고 = viewer/index.html `popOut` 2벌 — 414행(살아있는 .pmenu·#lockpop·.qpop 퇴장 정본) vs 1418행(**260710에 폐지된
#   .filterpop 잔해** · 요소 0건·closeFilterPop = no-op 스텁). 캐스케이드 승자가 **1418** = 죽은 컴포넌트의 사본이 살아있는
#   팝업 3종의 모션을 지배했다. 값이 동값이라 6주간 무증상 → 정본(414)을 고쳐도 화면 무변, 죽은 사본을 건드리면 무관해 보이는
#   팝업 3개가 동시에 갈리는 최악의 추적난도. 기존 게이트 사각 = check_design(토큰 **값**)·check_layout_transition(전이 **속성**)
#   ·smoke_*(애니가 **끝난 그림**)는 전부 다른 축이라 「같은 이름이 두 번 선언됐는가」는 축 자체가 없었다.
#   판정 = 정적(렌더·LLM 0) · 표면 자동발견(viewer/*.html + viewer/*.css = 새 뷰어가 조용히 못 빠진다) · 면책표 없이 **하드 0**.
#   ⚠ 스코프 = HTML은 <style> 블록 안만(화이트리스트). @keyframes의 유효한 거처가 <style>/.css뿐이라 블랙리스트보다 좁고 안전하다.
#     단 <script> 안에서 문자열로 조립하는 리포트 HTML('<style>'+…+'</style>')이 실재하므로(index 알림 리포트) script 구간에
#     걸친 <style>은 배제한다 — check_clip_coverage가 <script> 템플릿 문자열을 배제한 그 원칙의 계승.
#   ⚠ .js 비대상 = nm-loader.js처럼 **런타임 주입이 곧 SSOT**인 부품이 있다(@keyframes nmldBounce). 그건 중복 선언이 아니라
#     단일정본 배포다 — 섞으면 SSOT를 벌주는 오답이 된다.
#   ⚠ 파일 간 동명(goFill×10·gdots×8 등 17종)은 **대상 아님** — 뷰어는 각각 독립 문서고 tokens.css는 구조토큰 거울 전용이라
#     @keyframes를 공유할 물리적 수단이 없다. 크로스파일로 세면 60건+ 위양성으로 레포가 언다.
_KF_STYLE = re.compile(r'<style\b[^>]*>(.*?)</style\s*>', re.S | re.I)
_KF_SCRIPT = re.compile(r'<script\b.*?</script\s*>', re.S | re.I)
_KF_DECL = re.compile(r'@(?:-webkit-|-moz-|-o-)?keyframes\s+("[^"]+"|\'[^\']+\'|[A-Za-z_-][\w-]*)')
_KEYFRAMES_DUP_BASE = {}   # 표면별 **초과** 선언 수 = 비어 있음(전수 청정 = 하드 0). 늘리려면 운영자 승인 + 사유 주석 + --debt-sync


def _kf_regions(rel, src):
    """@keyframes가 살 수 있는 구간만 (시작줄offset, 텍스트)로 잘라 준다.
    .css = 파일 전체 · .html = <script> 밖 <style> 블록만.
    ⚠ HTML 주석(<!--…-->)을 파일 전역에 먼저 지우면 안 된다 — 실측(260804) = CSS 주석 제거가 HTML 주석의 닫는 `-->`를
      지워 `<!--`가 3,600줄 뒤 엉뚱한 `-->`와 짝지어 index.html 45~3692행이 통째로 blank 처리됐고, popOut 2건이 **둘 다
      사라져 「중복 0」으로 거짓 통과**했다. 구간을 먼저 자르면 이 교차오염이 구조적으로 불가능하다."""
    if rel.endswith('.css'):
        return [(0, src)]
    spans = [(m.start(), m.end()) for m in _KF_SCRIPT.finditer(src)]
    out = []
    for m in _KF_STYLE.finditer(src):
        if any(a <= m.start(1) < b for a, b in spans):
            continue   # <script> 안에서 문자열로 조립되는 리포트 HTML = 정적 스타일 아님
        out.append((src.count('\n', 0, m.start(1)), m.group(1)))
    return out


def check_comment_seam():
    """CSS 주석 이음매 하드 0 — 「주석 안에서 새 주석이 열리는가 · 주석 밖에서 닫히는가」.

    ⚠ 신설 사유(운영자 260807 «아이디어도 적용하고» · 같은 날 실사고 2건의 기계화) = 이 레포는 규칙 뒤에
      **여러 줄에 걸친 미종료 주석**이 붙는 관례라, 개정 사유를 「줄 끝」에 붙이면 그 `*/`가 **선행 주석을
      조기 종료**시켜 남은 주석 본문이 라이브 CSS로 새어 나온다. 실측 = ⓐ song `:where(#optGo)` 테두리
      정본이 먹혀 .2 → .15 ⓑ edit `.pvfire` 블록이 깨져 히트슬롭 소멸(보이는 버튼 30px인데 위 5px가 남의 것).
      **중괄호 균형·주석 개수 균형·`bash -n`급 문법 검사가 전부 통과**하는 무증상 사고고, 그날은 런타임
      스모크(C6·C7)가 우연히 그 자리를 덮고 있어서 잡혔다 — 스모크가 안 덮는 자리에서 나면 그냥 라이브로 나간다.
      기존 게이트는 전부 다른 축이다(`check_design` = 토큰 값 · `check_keyframes_dup` = 이름 중복 ·
      `check_css_dead_state` = 특이도) → 「주석이 앞 주석을 조기 종료했는가」는 축 자체가 없었다.

    판정 = 정적(렌더·LLM·네트워크 0) · 표면 자동발견(`viewer/*.html`+`viewer/*.css`) ·
      구간 선분리(`_kf_regions`) = HTML 주석 교차오염 구조 차단(그 계약 계승) · **면책표 없이 하드 0**.
    ⚠ 문자열 리터럴 안의 `/*`는 대상 밖 — CSS 값에 들어가는 `url("…/*…")`·`content:"/*"` 오탐 차단(따옴표 추적).
    CONTRACT: check_comment_seam
    """
    import glob as _g
    bad = []
    for fp in sorted(_g.glob(os.path.join(ROOT, 'viewer', '*.html')) + _g.glob(os.path.join(ROOT, 'viewer', '*.css'))):
        rel = os.path.relpath(fp, ROOT).replace(os.sep, '/')
        try:
            with open(fp, encoding='utf-8') as _f:
                src = _f.read()
        except (OSError, UnicodeDecodeError):
            continue   # ⚠ 예외를 넓게 잡지 마라 — 첫 판이 `io.open`(check_refs는 io 미import)이라 NameError가 통째로 삼켜져
                       #    전 파일 스킵 = **항상 PASS하는 죽은 게이트**가 됐다(킬테스트가 잡았다 · 260807 실측).
        for off, region in _kf_regions(rel, src):
            i, n, incom, quote = 0, len(region), False, ''
            while i < n:
                c = region[i]
                if incom:
                    if c == '*' and region[i + 1:i + 2] == '/':
                        incom = False; i += 2; continue
                    if c == '/' and region[i + 1:i + 2] == '*':
                        bad.append('%s:%d 주석 안에서 새 주석이 열린다(= 앞 주석이 이 자리에서 조기 종료된다)'
                                   % (rel, off + region.count('\n', 0, i) + 1))
                        i += 2; continue
                    i += 1; continue
                if quote:
                    if c == '\\':
                        i += 2; continue
                    if c == quote:
                        quote = ''
                    i += 1; continue
                if c in '"\'':
                    quote = c; i += 1; continue
                if c == '/' and region[i + 1:i + 2] == '*':
                    incom = True; i += 2; continue
                if c == '*' and region[i + 1:i + 2] == '/':
                    bad.append('%s:%d 주석 밖에서 `*/`가 닫힌다(= 짝 없는 종료)'
                               % (rel, off + region.count('\n', 0, i) + 1))
                    i += 2; continue
                i += 1
    if bad:
        print('\u274c CSS 주석 이음매 게이트(차단) — 주석이 앞 주석을 조기 종료했다(무증상 · 남은 본문이 라이브 CSS로 샌다):')
        for b in bad[:12]:
            print('  - ' + b)
        print('  처방 = 개정 사유 주석의 거처는 **규칙 닫는 중괄호 직후 · 다음 주석 열기 전**(줄 끝 금지).')
        return 1
    print('\u2705 CSS 주석 이음매 게이트 — 중첩 열기·짝 없는 닫기 0(줄 끝 사유 주석이 앞 주석을 조기 종료하는 무증상 사고 차단).')
    return 0


def check_keyframes_dup():
    """@keyframes 중복 정의 하드 0(위 주석 참조). rc=1 = 커밋 차단."""
    import glob as _g
    cur, det = {}, {}
    for fp in sorted(_g.glob(os.path.join(ROOT, 'viewer', '*.html')) + _g.glob(os.path.join(ROOT, 'viewer', '*.css'))):
        rel = os.path.relpath(fp, ROOT).replace(os.sep, '/')
        try:
            src = open(fp, encoding='utf-8').read()
        except Exception:
            continue
        seen = {}
        for off, region in _kf_regions(rel, src):
            # 주석은 **줄 수를 보존하며** 공백화 = 보고 줄번호가 안 밀린다(_debt_scan 관례 동문)
            clean = re.sub(r'/\*.*?\*/', lambda m: re.sub(r'[^\n]', ' ', m.group(0)), region, flags=re.S)
            for m in _KF_DECL.finditer(clean):
                seen.setdefault(m.group(1).strip('"\''), []).append(off + clean.count('\n', 0, m.start()) + 1)
        for name, lns in seen.items():
            if len(lns) > 1:
                cur[rel] = cur.get(rel, 0) + len(lns) - 1
                det.setdefault(rel, []).append('%s×%d(줄 %s)' % (name, len(lns), ','.join(map(str, lns))))
    up = [(k, _KEYFRAMES_DUP_BASE.get(k, 0), v) for k, v in sorted(cur.items()) if v > _KEYFRAMES_DUP_BASE.get(k, 0)]
    if up:
        print('❌ @keyframes 중복 정의 — 같은 이름 재선언 = 앞 선언이 **통째로 죽는다**(CSS Animations L1 §2 · 병합 아님):')
        for k, a, b in up:
            print('   · %s  %d → %d  %s' % (k, a, b, ' / '.join(det.get(k, []))))
        print('   고쳐라 = 이름 하나에 선언 하나로 합쳐라(값이 같으면 뒤엣것 삭제 · 다르면 이름을 갈라라).')
        print('   정본상 불가피하면 운영자 승인 후 _KEYFRAMES_DUP_BASE 갱신 + 사유 주석 + `--debt-sync`(raw baseline 문법 동문).')
        return 1
    dn = [(k, _KEYFRAMES_DUP_BASE[k], cur.get(k, 0)) for k in sorted(_KEYFRAMES_DUP_BASE) if cur.get(k, 0) < _KEYFRAMES_DUP_BASE[k]]
    if dn:
        print('✅ @keyframes 중복 래칫 — **%d건 청산**. _KEYFRAMES_DUP_BASE를 낮춰라: %s'
              % (sum(a - b for _, a, b in dn), ', '.join('%s %d→%d' % (k, a, b) for k, a, b in dn)))
        return 0
    print('✅ @keyframes 중복 정의 0 — viewer 전 표면(html <style> + css) 자동발견 · 이름당 선언 1개.')
    return 0


# ── 죽은 상태 오버라이드 = 특이도 패배 게이트 (운영자 260806 승인 "아이디어 해결 ㄱ") ──────────────────
#   왜 = 이 레포는 오버라이드의 의도를 **주석으로** 설명하는 관례인데, 주석엔 강제력이 0이라 「이긴다고 적힌 쪽이
#     실제로는 특이도로 지는」 상태가 조용히 생긴다. 실사고 2건(260806 실측 · CDP 캐스케이드 순서로 확정):
#       ⓐ `viewer/thumb.html` 260731 주석 = 「.dropping 강조 링은 border-color 오버라이드라 **그대로 살아 있음**」
#          → 거짓. `.cpprev-box.dropping`(0,2,0) < `.topdock[data-lay="edit"] .cpprev-box`(0,3,0)라
#            도크 안 첨부 드래그오버 링이 **한 번도 안 보였다**(실측 computed = rgba(0,0,0,0)).
#       ⓑ 같은 파일 `#go { border-color:.08 }`(1,0,0)이 발사 버튼의 **모든** 클래스 오버라이드를 눌러 죽였다 —
#          `.go.err`(빨강)·`.okdone`(초록)·`.rszbusy`·`.spell-arm` 4상태 + **운영자 260731 12차 「너무 옅음」
#          지시로 넣은 도크 `.2`**까지 전멸(HEAD CDP 캐스케이드 최강 = #go .08 = 6일간 지시 미발효).
#   ⚠ 신설 사유 = 기존 게이트가 전부 다른 축이다 — `check_design` = raw **개수** · 팔레트 핀 = 뷰어 **간** 동값 ·
#     `check_keyframes_dup` = **이름** 중복 · `smoke_*` = **애니 끝난 그림** → 「같은 속성을 두 규칙이 다투는데
#     상태 쪽이 지는가」는 축 자체가 없었다. 증상도 안 보인다(그냥 상태가 안 뜰 뿐) = 운영자 눈이 유일한 검출기.
#   판정 = 정적(렌더·LLM·네트워크 0) · 표면 자동발견(`viewer/*.html` <style> + `viewer/*.css`).
#     술어 = 「기저+상태」 단일 복합선택자 B가, **B와 같은 요소를 잡는** 더 센 규칙 C에게 같은 속성을 빼앗긴다.
#   위양성 4겹(실측으로 31 → 21 → 11 → 7까지 좁힌 경계):
#     ⓐ **상태는 JS 토글분만** — `classList.add/remove/toggle('x')`로 실제 켜지는 클래스만 상태로 본다(정적 변종 제외).
#     ⓑ **구조자(rescue) 인식** — 상태를 되살리는 더 센 규칙이 있으면 살아 있다(이게 없으면 위 ⓐ의 **수리 자체**가
#        위반으로 잡힌다 = 게이트가 봉합을 막는 자기모순 · 실측 10건이 이 겹에서 걸러졌다).
#     ⓒ **상태-대-상태 면제** — 경쟁자가 자기도 JS 토글 상태면(오류 상태가 모든 상태를 덮는 `.pin-slots.bad` 등)
#        의도적 우선순위다(실측 10건). 잡는 건 **구조·문맥이 상태를 덮는** 경우뿐.
#     ⓓ **at-블록 밖만** — `@media` 안 오버라이드는 정당한 거처라 스코프 밖 · 의사요소 상자 vs 요소 상자 비교 제외 ·
#        경쟁자 최우측에 id·속성·의사가 붙으면 매칭 집합이 갈리므로 제외(보수적).
#   ⚠ **하드 0 금지** = 현행 7건(index 4 · k 3)은 전건 **미검증**이다 — 실제 사망인지 의도된 문맥 우선인지 케이스별
#     판독이 필요하고, 그 판독 없이 baseline에 박으면 「알고 동결한 부채」가 「원래 그런 것」으로 굳는다(부채 래칫이
#     막으려는 바로 그 병). → 래칫 = **늘면 차단 · 줄면 낮추라고 알린다** + 원장 open_items에 사람 말로 남긴다.
_CSS_DEAD_STATE_BASE = {'viewer/index.html': 3, 'viewer/k.html': 3}   # 260806 실측 스냅샷(미검증 = 판독 후 축소 대상 · 늘리려면 사유 + --debt-sync)
#   index 3 = `.fin-chg.up`[color] · `.nm-toast:not(.show)`[pointer-events] · `.qrow.qrow-out`[animation]
#   k 3     = `.axrow.kax`[margin-top] ×3(경쟁자 = `#go + .axrow` 형제결합 2벌 + `.ogrid > #axes > .axrow`)
#   ⚠ thumb 4건(`.go.err`·`.okdone`·`.rszbusy`·`.spell-arm`)은 260806에 **실제로 수리**해서 표에 없다 = 하드 0 유지분.

_CSS_COMBI = re.compile(r'\s*[>+~]\s*|\s+')
_CSS_TOK = re.compile(r'(::?[a-zA-Z-]+(?:\([^)]*\))?)|(\[[^\]]*\])|(\.[-\w]+)|(#[-\w]+)|([-\w]+)|(\*)')
_CSS_DECL_P = re.compile(r'(?:^|;)\s*([-a-zA-Z]+)\s*:', re.M)
_CSS_TOGGLE = re.compile(r"""classList\s*\.\s*(?:add|remove|toggle)\s*\(\s*['"]([-\w]+)['"]""")


def _css_spec(sel):
    """(a,b,c) 특이도 — `:where()`는 0 기여(실측 확인: 크로미엄 141 정상 준수)."""
    a = b = c = 0
    for m in _CSS_TOK.finditer(sel):
        ps, at, cl, idd, tag, _st = m.groups()
        if ps:
            if ps.startswith('::'):
                c += 1
            elif ps.startswith(':where('):
                pass
            elif ps.startswith((':not(', ':is(', ':has(')):
                inner = ps[ps.index('(') + 1:-1]
                best = max((_css_spec(s) for s in inner.split(',') if s.strip()), default=(0, 0, 0))
                a, b, c = a + best[0], b + best[1], c + best[2]
            else:
                b += 1
        elif at:
            b += 1
        elif cl:
            b += 1
        elif idd:
            a += 1
        elif tag:
            c += 1
    return (a, b, c)


def _css_compounds(sel):
    """복합선택자 리스트 — 각 원소 = {'cls':set,'id':bool,'attr':bool,'pseudo':bool}"""
    out = []
    for p in [x for x in _CSS_COMBI.split(sel.strip()) if x]:
        cur = {'cls': set(), 'id': False, 'ids': set(), 'attr': False, 'pseudo': False}
        for m in _CSS_TOK.finditer(p):
            ps, at, cl, idd, _tag, _st = m.groups()
            if ps:
                if ps.startswith('::'):
                    continue
                if ps.startswith((':not(', ':is(', ':where(')):
                    for s in ps[ps.index('(') + 1:-1].split(','):
                        cur['cls'] |= {'.' + x for x in re.findall(r'\.([-\w]+)', s)}
                else:
                    cur['pseudo'] = True
            elif at:
                cur['attr'] = True
            elif cl:
                cur['cls'].add(cl)
            elif idd:
                cur['id'] = True
                cur['ids'].add(idd[1:])
        out.append(cur)
    return out


def _css_top_rules(text):
    """depth 0 규칙만 (selector, decls, line0) — at-블록 내부는 스코프 밖([4]ⓓ)."""
    out, i, n, depth, buf = [], 0, len(text), 0, ''
    while i < n:
        ch = text[i]
        if ch == '{':
            sel = buf.strip()
            if depth == 0 and sel.startswith('@'):
                depth, buf = 1, ''
                i += 1
                continue
            if depth == 0:
                j, d = i + 1, 1
                while j < n and d:
                    if text[j] == '{':
                        d += 1
                    elif text[j] == '}':
                        d -= 1
                    j += 1
                out.append((sel, text[i + 1:j - 1], text.count('\n', 0, i)))
                buf, i = '', j
                continue
            depth += 1
        elif ch == '}':
            depth = max(0, depth - 1)
            buf = ''
        else:
            buf += ch
        i += 1
    return out


def check_css_dead_state():
    """죽은 상태 오버라이드 래칫(위 주석 참조). 늘면 rc=1 = 커밋 차단."""
    import glob as _g
    cur, det = {}, {}
    for fp in sorted(_g.glob(os.path.join(ROOT, 'viewer', '*.html')) + _g.glob(os.path.join(ROOT, 'viewer', '*.css'))):
        rel = os.path.relpath(fp, ROOT).replace(os.sep, '/')
        try:
            src = open(fp, encoding='utf-8').read()
        except Exception:
            continue
        toggled = set(_CSS_TOGGLE.findall(src))
        idcls = {}   # id → 그 요소가 실제로 든 클래스 집합(정적 마크업 실측) — `#go`처럼 **id 기저가 클래스 상태를
        #              눌러 죽이는** 축을 잡기 위한 유일한 수단(CSS만 봐선 `#go`와 `.go.err`가 같은 요소인지 알 수 없다).
        #              ⚠ 실사고의 절반이 이 형태였고(운영자 260731 「너무 옅음」 .2 + 발사 4상태를 #go .08이 전멸),
        #                킬테스트 K1이 「id 경쟁자 보수적 제외」로는 그 진범을 못 잡는다는 걸 실측으로 드러냈다.
        for tm in re.finditer(r'<[a-zA-Z][^>]*>', src):
            tag = tm.group(0)
            im = re.search(r'\sid\s*=\s*["\']([-\w]+)["\']', tag)
            cm = re.search(r'\sclass\s*=\s*["\']([^"\']*)["\']', tag)
            if im and cm:
                idcls.setdefault(im.group(1), set()).update('.' + x for x in cm.group(1).split() if x)
        rules = []
        for off, region in _kf_regions(rel, src):   # 구간 선분리 = HTML/CSS 주석 교차오염 구조 차단(_kf_regions 계약 계승)
            clean = re.sub(r'/\*.*?\*/', lambda m: re.sub(r'[^\n]', ' ', m.group(0)), region, flags=re.S)
            for sel, decls, ln in _css_top_rules(clean):
                if not sel or sel.startswith('@'):
                    continue
                P = {m.group(1).lower() for m in _CSS_DECL_P.finditer(decls)}
                if not P:
                    continue
                for one in sel.split(','):
                    one = one.strip()
                    if one:
                        rules.append({'sel': one, 'spec': _css_spec(one), 'cp': _css_compounds(one),
                                      'p': P, 'ln': off + ln + 1})
        seen = set()
        for b in rules:
            if len(b['cp']) != 1:
                continue                       # 「기저+상태」 단일 복합선택자만
            bc = b['cp'][0]
            if len(bc['cls']) < 2:
                continue
            for c in rules:
                if c is b or c['sel'] == b['sel'] or c['spec'] <= b['spec']:
                    continue
                rc_ = c['cp'][-1]
                rcls, rid_ok = rc_['cls'], rc_['id']
                idsub = False
                if rc_['id'] and len(rc_['ids']) == 1 and not rc_['cls'] and not rc_['attr'] and not rc_['pseudo']:
                    rcls = idcls.get(next(iter(rc_['ids'])), set())   # `#go` → 그 요소가 실제로 든 클래스({.go,.pvfire}…)
                    rid_ok, idsub = False, True
                # ⚠ 부분집합 **방향** = id 치환일 땐 뒤집힌다(260806 실측 구멍) — `#go` 요소가 `.pvfire` 같은 **여분 클래스**를
                #   들면 `rcls ⊆ B` 는 거짓이 돼 진짜 경쟁자를 놓친다(vd 큐영상이 그렇게 빠져나갔다).
                #   맞는 술어 = 「B의 **기저**(상태 클래스를 뺀 나머지)가 그 요소에 실제로 붙어 있는가」.
                ok = ((bc['cls'] - {'.' + t for t in toggled}) <= rcls) if idsub else (rcls <= bc['cls'])
                if not rcls or not ok or rid_ok or rc_['attr'] or rc_['pseudo']:
                    continue                   # 같은 요소를 잡아야 · 최우측 속성·의사 = 매칭 집합 갈림(제외)
                if ('::' in c['sel']) != ('::' in b['sel']):
                    continue                   # 의사요소 상자 vs 요소 상자
                shared = b['p'] & c['p']
                if not shared:
                    continue
                bstate = ({x.lstrip('.') for x in bc['cls']} & toggled) if idsub else {x.lstrip('.') for x in (bc['cls'] - rcls)}
                if not (bstate & toggled):
                    continue                   # 상태 = JS 토글분만
                cstate = set()
                for cc in c['cp']:
                    cstate |= {x.lstrip('.') for x in cc['cls']}
                if (cstate - {x.lstrip('.') for x in bc['cls']}) & toggled:
                    continue                   # 상태-대-상태 = 의도적 우선순위(면제)
                if any(r is not b and r is not c and (r['p'] & shared) and bc['cls'] <= r['cp'][-1]['cls']
                       and r['spec'] > c['spec'] for r in rules):
                    continue                   # 구조자(rescue) = 상태를 되살리는 더 센 규칙이 있다
                k = (b['sel'], c['sel'], tuple(sorted(shared)))
                if k in seen:
                    continue
                seen.add(k)
                cur[rel] = cur.get(rel, 0) + 1
                det.setdefault(rel, []).append('%s(%d행 %s) ←패배← %s(%d행 %s) [%s]'
                                               % (b['sel'], b['ln'], b['spec'], c['sel'], c['ln'], c['spec'],
                                                  ','.join(sorted(shared))))
    up = [(k, _CSS_DEAD_STATE_BASE.get(k, 0), v) for k, v in sorted(cur.items()) if v > _CSS_DEAD_STATE_BASE.get(k, 0)]
    if up:
        print('❌ 죽은 상태 오버라이드 — 상태 규칙이 더 센 규칙에 눌려 **화면에 절대 안 나타난다**(증상 = 상태가 안 뜰 뿐 = 눈으로 못 잡는다):')
        for k, a, b_ in up:
            print('   · %s  %d → %d' % (k, a, b_))
            for d in det.get(k, []):
                print('       %s' % d)
        print('   고쳐라 = ⓐ 이긴 쪽의 그 속성 선언을 없애라(값이 동값이면 순손실 0) ⓑ 문맥 규칙이면 `:where()`로 특이도를 낮춰 상태가 이기게 하라')
        print('           ⓒ 그 상태만 되살릴 더 센 규칙을 추가하라(구조자 = 게이트가 인식한다).')
        return 1
    dn = [(k, _CSS_DEAD_STATE_BASE[k], cur.get(k, 0)) for k in sorted(_CSS_DEAD_STATE_BASE) if cur.get(k, 0) < _CSS_DEAD_STATE_BASE[k]]
    if dn:
        print('✅ 죽은 상태 오버라이드 래칫 — **%d건 청산**. _CSS_DEAD_STATE_BASE를 낮춰라: %s'
              % (sum(a - b_ for _, a, b_ in dn), ', '.join('%s %d→%d' % (k, a, b_) for k, a, b_ in dn)))
        return 0
    print('✅ 죽은 상태 오버라이드 래칫 — 총 %d건 = 면책 스냅샷과 동일(신규 사망 0 · 상태-대-상태·구조자·@블록 제외 · 미검증 %d건은 원장 추적)'
          % (sum(cur.values()), sum(_CSS_DEAD_STATE_BASE.values())))
    return 0


# ── 앵커 메뉴 문법 = 한 벌 게이트 (운영자 260805 승인 "아이디어 ㄱ") ──
#   왜 = 같은 결의 메뉴 3종(설정 #linkpop · 스튜디오 헤더 메뉴 .tool-menupop · PASS 사유 .sc-rsn)이 값을 **각자 베껴 쓰고** 있었다.
#     정본이 바뀌면 나머지가 조용히 낡는데 증상이 「어느 창 하나만 좀 달라 보임」뿐이라 눈으로만 잡혔다 — 실제로 260805 실측 시점의
#     PASS 사유 창은 혼자 다른 문법(테두리 칩 12/700 · 닫기 X 20px 원형 · radius 12 · 폭 가변)으로 갈라진 채 살아 있었고,
#     기존 게이트는 전부 다른 축이다(check_design = raw **개수** 래칫 · 팔레트 핀 = 뷰어 **간** 동값 · smoke_winnav = 모달 헤더 기하)
#     → 「같은 결의 메뉴가 한 벌인가」는 축 자체가 없었다.
#   판정 = 정적(렌더·LLM·네트워크 0) · **면책표 없이 하드 0**(현행 위반 0):
#     ① 두 SSOT 그룹 셀렉터가 실존 — 앵커 소실(그룹 해체·이름 변경) = fail-closed
#     ② 각 멤버가 **자기 단독 규칙**에서 SSOT 축을 재선언 0(재선언 = 갈라지는 첫걸음이자 유일한 기계 검출점)
#   ⚠ 스코프 = 멤버의 **정확한 단독 규칙**(`sel {`)만 — `:hover`·`.up`·`.inp` 같은 변형과 미디어쿼리 안 오버라이드는 대상 밖
#     (위치·상태·색 오버라이드는 각 표면 고유 권한 = 이 게이트가 얼리면 안 되는 축).
#   ⚠ 정규식 = 리터럴 find 선행(1.85MB index.html에서 여는-괄호-앞 와일드카드 금지 = CLAUDE.md 성능 계약).
_ANCHOR_MENU_SHELL_SEL = '#linkpop, .tool-menupop'   # ⚠ `.sc-rsn` 이탈(운영자 260806 창 분류) = 이 그룹은 「메뉴 선택 토글」 계열 전용{설정 · 이미지 스튜디오 메뉴} · PASS 사유 창은 「결과·선택지를 주는 창」 계열(대기열 문법)로 이관
_ANCHOR_MENU_ITEM_SEL = '#linkpop .lp-btn, .tool-menupop button'   # 동상
_ANCHOR_MENU_SHELL_AXES = ('width', 'min-width', 'max-width', 'padding', 'gap', 'border-radius')
_ANCHOR_MENU_ITEM_AXES = ('font-size', 'font-weight', 'padding', 'border-radius', 'background', 'border')


def _anchor_menu_block(src, sel):
    """`sel {` 단독 규칙 본문을 리터럴로 찾아 반환(없으면 None) — 그룹 규칙(앞에 `, `)은 제외."""
    needle = sel + ' {'
    at = 0
    while True:
        i = src.find(needle, at)
        if i < 0:
            return None
        # 단독 규칙 = 그 줄에서 셀렉터 앞이 **들여쓰기 공백뿐**일 때만.
        # ⚠ 들여쓰기를 안 보고 직전 1글자만 검사하면(`prev in '\n{}'`) 이 레포의 2칸 인덴트 CSS에서 **전건 미검출**이 된다
        #   (킬테스트 K1·K2 실측 = 재선언을 심었는데 rc=0 통과) · 그룹 멤버(`…, .sc-rsn {`)·복합(`.x .sc-rsn {`)은 앞에 글자가 남아 자동 제외.
        ls = src.rfind('\n', 0, i) + 1
        if src[ls:i].strip():
            at = i + 1
            continue
        j = src.find('}', i)
        return src[i + len(needle):j] if j > 0 else ''


# ── 공용 부품 CSS SSOT 게이트 (운영자 260807 "다른 모든 공간에도 이와 동일하게") ──
#   왜 = nm-clip.css(클립 4문법)와 같은 축. 260807 전수 스캔 실측 = **3파일 이상에 값이 완전히 같은 사본**으로
#   흩어진 규칙이 83종·387개였다. 그 중 **전역·원자 규칙 5종(59규칙)** 을 nm-shared.css로 승격했다.
#   ⚠ 왜 5종만인가 = **CSS 캐스케이드는 규칙을 옮기는 순간 전역 재배치된다**. 83종을 한꺼번에 올렸더니
#   회차마다 새 불일치가 났다(`.pvsec` height 261→522 · `.geni-opt.on` 700→800 · edit `.cpv-tool` transition).
#   부품 가족은 **하나씩** 이관하고 매번 computed 대조하는 수밖에 없다(클립이 그 방식이었다).
#   ⚠ noscript 안 <style>은 **대상 밖** — 「JS가 죽었을 때만」이라는 조건부 정본이라 공용 SSOT로 올리면
#   정상 상태에서도 적용된다(260807 실사고 = 스크롤바 폴백 10px이 되살아나 260726 "스크롤 없애" 계약 위반 ·
#   computed 대조는 의사요소를 못 재서 **못 잡는 사각**이었고 스크롤바 실폭 측정으로만 검출됐다).
#   판정 = 정적 · 3축 = ① 정본 파일·규칙 실존(fail-closed) ② 승격 규칙의 뷰어 인라인 재선언 0 ③ link 실존.
def _decl_set(body):
    b = re.sub(r'/\*.*?\*/', ' ', body or '', flags=re.S)
    return frozenset(d.strip() for d in b.split(';') if d.strip())


_SHARED_CSS = 'viewer/nm-shared.css'
def _shared_sels(css):
    """정본 파일에서 승격된 셀렉터를 **자동 발견**한다.
    ⚠ 손 목록이면 새 승격이 게이트에 조용히 안 실린다 — 이 레포가 반복해 겪은 병(손 레지스트리 드리프트).
      css_hoist.py 가 규칙을 덧붙이면 이 게이트가 **다음 실행부터 자동으로** 그 셀렉터를 지킨다."""
    return [m.group(1).strip() for m in re.finditer(r'(?m)^([^\s@/][^{\n]*?) \{', css)]




def check_shared_canon():
    """공용 부품 CSS = nm-shared.css 단일정본 참조. rc=1 = 커밋 차단."""
    path = os.path.join(ROOT, _SHARED_CSS)
    if not os.path.exists(path):
        print('❌ 공용 CSS SSOT 게이트 — 정본 %s 가 없다.' % _SHARED_CSS)
        return 1
    css = open(path, encoding='utf-8').read()
    sels = _shared_sels(css)
    if len(sels) < 5:
        print('❌ 공용 CSS SSOT 게이트 — 정본 규칙이 %d종뿐이다(사본 시대로 회귀 · 하한 5).' % len(sels))
        return 1
    bad = []
    if bad:
        print('❌ 공용 CSS SSOT 게이트 — 정본에서 규칙이 사라졌다(사본 시대로 회귀):')
        for b in bad:
            print('   · ' + b)
        return 1
    # 승격분이 뷰어 인라인으로 되돌아왔는가(noscript 폴백은 조건부 정본 = 대상 밖)
    dup, nolink = [], []
    for p in sorted(glob.glob(os.path.join(ROOT, 'viewer', '*.html'))):
        rel = os.path.relpath(p, ROOT).replace(os.sep, '/')
        src = open(p, encoding='utf-8').read()
        body = re.sub(r'<noscript[^>]*>.*?</noscript>', ' ', src, flags=re.S)
        # ⚠ 단독 규칙 판정 — bare substring이면 `#geniOut::-webkit-scrollbar {` 가
        #   `::-webkit-scrollbar {` 로 잡혀 위양성이 난다(첫 실행 실측 · _anchor_menu_block 문법 계승).
        # ⚠ **값이 SSOT와 같을 때만** 사본이다 — 값이 다른 인라인은 그 표면의 정당한 고유 선언이다
        #   (실측 = index `button, input, textarea, select` 는 12표면 동값 그룹에 애초에 안 들어간 별값).
        hit = []
        for sel in sels:
            b = _anchor_menu_block(body, sel)
            if b is None:
                continue
            if _decl_set(b) == _decl_set(_anchor_menu_block(css, sel) or ''):
                hit.append(sel)
        if hit:
            dup.append('%s — %s' % (rel, ' / '.join(h[:44] for h in hit)))
        if 'href="nm-shared.css"' not in src and hit:
            nolink.append(rel)
    if dup:
        print('❌ 공용 CSS 사본 부활 — 값은 %s 에만 둔다(운영자 260807 "정본1개를 참조해서 불러오는 개념"):' % _SHARED_CSS)
        for d in dup:
            print('   · ' + d)
        print('   고쳐라 = 인라인 규칙을 지우고 <link rel="stylesheet" href="nm-shared.css"> 1줄로 상속받아라.')
        return 1
    print('✅ 공용 CSS SSOT 게이트 — %s 규칙 %d종 단일 원천(자동 발견) · 뷰어 인라인 사본 0(noscript 폴백 = 조건부 정본 = 대상 밖).'
          % (_SHARED_CSS, len(sels)))
    return 0


# ── 클립 4문법 SSOT 게이트 (운영자 260807 "정본1개를 참조해서 불러오는 개념으로 쓰셈") ──
#   왜 = 같은 클립 부품이 **접두만 달리해 4벌로 복사**돼 있었다(`.iobtn-edge` 이미지·요약 / `.scnclip` tr·sb·k·vd /
#   `.urlclip` ly·track·conv / `.askclip` index). 값이 같으니 무해해 보이지만 한 곳을 고치면 나머지가 조용히 낡는다 —
#   260807 실측에서 이미 세 축이 갈라져 있었다{z-index 2↔5 · transition 3갈래(raw .15s ↔ 토큰) · tap-highlight 유무}
#   + **tr만 backdrop-filter 잔류**(나머지 8표면은 260701 "타이핑마다 번쩍" 계약으로 전부 제거된 상태 = 계약 위반이
#   6주 무증상). 운영자 표현 = "원래는 해놓고 몰랐어" — 사람 눈이 유일한 검출기였다.
#   ⚠ 기존 게이트는 전부 다른 축이다 — `check_clip_coverage` = **클립이 붙었나**(존재) · `check_design` = raw **개수** ·
#   팔레트 핀 = 뷰어 **간 색** 동값 → 「같은 부품이 **한 원천에서 오는가**」는 축 자체가 없었다.
#   판정 = 정적(렌더·LLM·네트워크 0) · 3축 = ① 그룹 셀렉터 실존(해체·개명 = fail-closed) ② 클립 문법 보유 뷰어의
#   nm-clip.css link 실존 ③ 각 뷰어 **단독 규칙**에서 SSOT 축 재선언 0.
#   ⚠ 면제는 **구조적 사유가 있는 것만** — 늘리려면 사유 1줄 동반(값 사본 복귀의 뒷문이 되면 이 게이트가 죽는다).
_CLIP_CANON_SEL = '.iobtn-edge, .scnclip, .urlclip, .askclip'
_CLIP_CANON_MEMBERS = ('.iobtn-edge', '.scnclip', '.urlclip', '.askclip')
_CLIP_CANON_AXES = ('width', 'height', 'border-radius', 'background', 'color', 'opacity', 'z-index',
                    'box-shadow', 'transition', 'cursor', 'display', 'place-items', 'padding', 'position')
_CLIP_CANON_EXEMPT = {
    ('viewer/index.html', '.askclip'):
        '`.sbtn`과 합성되는 유일 표면 — head link SSOT가 **같은 특이도**의 인라인 `.sbtn`에게 캐스케이드로 진다'
        '(260807 실측 = 인라인 제거 시 width/height 26→34·radius 50%→10px 등 10축 붕괴). 특이도 재설계 = 별건.',
    ('viewer/edit.html', '.urlclip'):
        '칸 **안** 세로중앙 배치(top:50% · right:12) = 상단 걸침 계열과 다른 문법 — 옮기면 URL 글자를 덮는다.',
    ('viewer/thumb.html', '.iobtn-edge'):
        '`.iobtn` 베이스가 raw판(9px·.15s)↔토큰판(--r-s·--dur)으로 갈려 **값 정리가 선행 조건** — 미이관(다음 단계).',
}


def check_clip_canon():
    """클립 4문법 = 한 벌(nm-clip.css 단일정본 참조). rc=1 = 커밋 차단."""
    bad = []
    css_rel = 'viewer/nm-clip.css'
    css_path = os.path.join(ROOT, css_rel)
    if not os.path.exists(css_path):
        print('❌ 클립 SSOT 게이트 — 정본 %s 가 없다.' % css_rel)
        return 1
    css = open(css_path, encoding='utf-8').read()
    # ① 그룹 셀렉터 실존
    if _CLIP_CANON_SEL + ' {' not in css:
        bad.append('SSOT 그룹 소실 — `%s` 셀렉터가 %s 에 없다(그룹 해체·이름 변경 = 4문법이 다시 갈라진다).'
                   % (_CLIP_CANON_SEL, css_rel))
    # ②·③ 표면 자동 발견
    for path in sorted(glob.glob(os.path.join(ROOT, 'viewer', '*.html'))):
        rel = os.path.relpath(path, ROOT).replace(os.sep, '/')
        src = open(path, encoding='utf-8').read()
        owns = [m for m in _CLIP_CANON_MEMBERS if m + ' ' in src or m + '"' in src or m + "'" in src]
        if not owns:
            continue
        declares = [m for m in owns if _anchor_menu_block(src, m) is not None]
        if declares and 'href="nm-clip.css"' not in src:
            bad.append('%s — 클립 문법 %s 를 쓰면서 `nm-clip.css` link이 없다(사본으로 사는 중).'
                       % (rel, '·'.join(declares)))
        for m in declares:
            if (rel, m) in _CLIP_CANON_EXEMPT:
                continue
            body = _anchor_menu_block(src, m)
            clean = re.sub(r'/\*.*?\*/', ' ', body, flags=re.S)
            hit = [a for a in _CLIP_CANON_AXES if re.search(r'(?:^|;)\s*' + re.escape(a) + r'\s*:', clean)]
            if hit:
                bad.append('%s `%s` 단독 규칙이 SSOT 축 재선언 — %s (정본은 %s 그룹 하나뿐이어야 한다).'
                           % (rel, m, ', '.join(hit), css_rel))
    if bad:
        print('❌ 클립 4문법 갈라짐 — 같은 부품은 **정본 1개를 참조**한다(운영자 260807 "정본1개를 참조해서 불러오는 개념"):')
        for b in bad:
            print('   · ' + b)
        print('   고쳐라 = 값은 `%s` 그룹에만 두고, 각 뷰어는 <link rel="stylesheet" href="nm-clip.css"> 1줄 + 표면 고유 오버라이드만.' % _CLIP_CANON_SEL)
        return 1
    print('✅ 클립 4문법 SSOT 게이트 — %s 단일 원천 · 사본 재선언 0(면제 %d = 구조적 사유 명문).'
          % (_CLIP_CANON_SEL, len(_CLIP_CANON_EXEMPT)))
    return 0


def check_anchor_menu_canon():
    """앵커 메뉴 문법 = 한 벌(위 주석). rc=1 = 커밋 차단."""
    rel = 'viewer/index.html'
    src = open(os.path.join(ROOT, rel), encoding='utf-8').read()
    bad = []
    for sel, label in ((_ANCHOR_MENU_SHELL_SEL, '셸 기하'), (_ANCHOR_MENU_ITEM_SEL, '항목 행')):
        if sel + ' {' not in src and sel + ' {\n' not in src and (sel + ' {') not in src.replace('\n  ', ' '):
            bad.append('SSOT 그룹 소실 — `%s`(%s) 셀렉터가 없다(그룹 해체·이름 변경 = 세 표면이 다시 갈라진다)' % (sel, label))
    members = [(s.strip(), _ANCHOR_MENU_SHELL_AXES, '셸') for s in _ANCHOR_MENU_SHELL_SEL.split(',')] + \
              [(s.strip(), _ANCHOR_MENU_ITEM_AXES, '항목') for s in _ANCHOR_MENU_ITEM_SEL.split(',')]
    for sel, axes, kind in members:
        body = _anchor_menu_block(src, sel)
        if body is None:
            continue   # 단독 규칙이 없는 게 정상(전량 그룹 위임) = 가장 깨끗한 상태
        clean = re.sub(r'/\*.*?\*/', ' ', body, flags=re.S)
        hit = [a for a in axes if re.search(r'(?:^|;)\s*' + re.escape(a) + r'\s*:', clean)]
        if hit:
            bad.append('`%s` 단독 규칙이 SSOT 축 재선언 — %s (%s 그룹이 유일 원천이어야 한다)' % (sel, ', '.join(hit), kind))
    if bad:
        print('❌ 앵커 메뉴 문법 갈라짐 — 설정 메뉴·스튜디오 헤더 메뉴·PASS 사유 창은 **한 벌**이다(운영자 260805):')
        for b in bad:
            print('   · ' + b)
        print('   고쳐라 = 값은 `%s` / `%s` 그룹에만 두고, 각 표면엔 위치·모션·상태 오버라이드만 남겨라.' % (_ANCHOR_MENU_SHELL_SEL, _ANCHOR_MENU_ITEM_SEL))
        print('   새 앵커 메뉴 = 두 그룹에 셀렉터 1개씩 추가(유리는 252행 「앵커 팝업 셸 글래스」 그룹 동반).')
        return 1
    print('✅ 앵커 메뉴 문법 게이트 — 3표면(설정·스튜디오 헤더 메뉴·PASS 사유) 셸 기하·항목 행 단일 원천 · 멤버 개별 재선언 0.')
    return 0


# ── 컴포넌트 작업 락 게이트 (운영자 260802 "머지하셈" 승인분 · WARN·비차단) ──
#   왜 = 260802 하루에 **같은 컴포넌트를 두 세션이 동시에 갈아엎는 사고가 3번**(코너 레일: 창 안 우상단 → 창 밖 우측 → 2단).
#   뒤에 온 쪽은 매번 리베이스 충돌을 만나 통째로 재작업했다 — 낭비된 시간이 이 게이트 만드는 시간보다 길었다.
#   충돌 자체는 못 막지만(세션끼리 서로를 모른다) **착수 30초 만에 알아채는 것**은 막을 수 있다.
#   계약 = `docs/locks/*.md`(shared/lock.py take/release)에 「누가·언제부터·어느 파일」을 남기고,
#   내가 만진 파일이 **남의 살아있는 락**과 겹치면 커밋 직전에 눈앞에 띄운다.
#   ⚠ 하드 차단 안 함 = 해제를 잊은 세션 하나가 레포를 얼리면 락 파일이 곧 사고원 → TTL(기본 90분) 자동 만료로 유령 락은 스스로 사라진다.


def check_component_lock():
    """컴포넌트 작업 락 겹침 알림(운영자 260802 · WARN·비차단). 등재 = CLAUDE.md 이 레포 전용 절."""
    try:
        sys.path.insert(0, os.path.join(ROOT, 'shared'))
        import lock as _lock
    except Exception as e:
        print('⚠️ 컴포넌트 락 게이트 스킵(모듈):', e); return 0
    locks = _lock.live()
    if not locks:
        print('✅ 컴포넌트 락 게이트 — 살아있는 락 0(병렬 세션 충돌 감시 대기 · 착수 선언 = python3 shared/lock.py take).')
        return 0
    changed = set()
    for cmd in ('git diff --name-only origin/main...HEAD', 'git diff --name-only', 'git diff --name-only --cached'):
        try:
            changed |= {l.strip() for l in os.popen(cmd).read().splitlines() if l.strip()}
        except Exception:
            pass
    me = _lock.session_id()
    hits = []
    for lk in locks:
        if lk['session'] == me:
            continue   # 내 락 = 조용(내가 잡은 걸 나한테 알릴 이유 없다)
        import fnmatch
        ov = sorted({c for c in changed for f in lk['files'] if c == f or fnmatch.fnmatch(c, f)})
        if ov:
            hits.append((lk, ov))
    if not hits:
        print('✅ 컴포넌트 락 게이트 — 살아있는 락 %d개 · 내 변경분과 겹침 0(병렬 재작업 위험 없음).' % len(locks))
        return 0
    print('⚠️ 컴포넌트 락 게이트(WARN·비차단) — 남이 잡고 있는 파일을 만졌다(병렬 재작업 사고 축 · 260802 3회):')
    for lk, ov in hits:
        age = int((datetime.datetime.now(_lock.KST) - lk['since']).total_seconds() / 60)
        print('   🔒 「%s」 = %s가 %d분 전부터 · 겹친 파일: %s' % (lk['name'], lk['session'], age, ', '.join(ov)))
    print('   → 착수 전 그 세션 결과를 먼저 확인하거나(리베이스 충돌·통째 재작업 예방), 내 작업도 락으로 선언하라: python3 shared/lock.py take "<컴포넌트>" <파일…>')
    return 0


def check_label_fill():
    """콘텐츠 라벨색(cat-*·bias-*) 솔리드 배경 필 금지 게이트(운영자 260721 Q345 · 평의회 Q329 채택 ④ = 감사 R5 절제축).
    취지 = 카테고리/편향색은 '라벨'(텍스트·도트·저알파 워시·게이지)이지 '기능 신호'(칩·버튼 솔리드 필)가 아니다 —
    한 hex의 다축 겸직(#FFE13D = warn·arm·cat-eco 등)은 운영자 의도적 값공유(무접촉)이므로, 오독은 '불투명 필 승격' 순간에만 생긴다.
    허용 = rgba(var(--cat-X-rgb), a) 저알파 워시 · gradient( 전계열(게이지 = 색이 곧 데이터) · color/border/text = 자유. 차단 = background(-color)에 비-rgb 토큰 직참조.
    현행 위반 0 실측(260721) = 렌더 무변 순수 규칙 게이트. fail-closed 아님(뷰어 못 읽으면 스킵 보고)."""
    import glob as _g
    rx = re.compile(r'background(?:-color)?\s*:[^;{}]*var\(--(?:cat|bias)-(?!\w+-rgb)[\w-]+\)')
    grad = re.compile(r'gradient\(')   # 게이지·워시 그라데 = 색이 곧 데이터(정당) — 솔리드 필 선언만 겨냥(260721 자가검증: index 2834 편향 게이지 바 오탐 적출)
    bad = []
    for fp in sorted(_g.glob(os.path.join(ROOT, 'viewer', '*.html'))):
        try:
            for i, ln in enumerate(open(fp, encoding='utf-8'), 1):
                if rx.search(ln) and not grad.search(ln):
                    bad.append('%s:%d %s' % (os.path.basename(fp), i, ln.strip()[:80]))
        except Exception as e:
            print('⚠️ check_label_fill 스킵(%s): %s' % (os.path.basename(fp), e)); return 0
    if bad:
        print('❌ 라벨색 솔리드 필 %d건 — cat-*/bias-*는 텍스트·도트·저알파 워시만(불투명 배경 필 = 기능색 오독 · rgba(var(--X-rgb),a)로 강등하라):' % len(bad))
        for b in bad[:6]:
            print('   ·', b)
        return 1
    print('✅ 라벨색 필 게이트 — cat-*/bias-* 솔리드 배경 필 0(라벨 지위 유지 · 저알파 워시·게이지 허용).')
    return 0


def check_loader_ssot():
    """로딩 표기 SSOT 게이트(운영자 260723 Q461 — "전역 앱 세션에서 정해진 로딩만 쓰도록").
    정본 = viewer/nm-loader.js window.nmLoader(type,label[,opts]) · **그래픽 1종(통통 튀는 도트3 · 운영자 260731 단일화)**·라벨 4개(Now loading/Thinking/Solving/Prompting = data-orb 의미 라벨).
    규칙 = 새 로더는 nmLoader만. raw 3점 로더(`gdots"><i>` 마크업)가 nmLoader 폴백이 아닌 채로 baseline 초과 = 차단(신규 raw 재발 방지·기존 잔량은 점진 감축 래칫).
    raw 로더 = ① gdots 3점(`gdots"><i>`) ② 구 팩토리 도트(`class="nmld"` · SPIN_SVG 포함) — **하드락 baseline 0(운영자 260723 Q463 "한 수" = 전 뷰어 orb 통일 완료 · 신규 raw = 전면 금지)**. tokens.html = 토큰 레퍼런스 페이지(nm-loader 미로드·데모)라 스코프 제외. fail-closed 아님(뷰어 못 읽으면 스킵)."""
    import glob as _g
    BASELINE = 0   # 260723 Q463 하드락 — 전 뷰어 로더 orb 배선 완료(gdots·nmld 0) · nmLoader 폴백은 같은 줄이라 미계수 · 신규 raw = 즉시 차단
    raw = []
    try:
        for fp in sorted(_g.glob(os.path.join(ROOT, 'viewer', '*.html'))):
            if os.path.basename(fp) == 'tokens.html':   # 토큰 레퍼런스 데모(nm-loader 미로드) = 라이브 로더 아님 · 스코프 밖
                continue
            for i, ln in enumerate(open(fp, encoding='utf-8'), 1):
                if 'gdots"><i>' in ln and 'nmLoader' not in ln and '@keyframes' not in ln and '.gdots' not in ln:
                    raw.append('%s:%d gdots' % (os.path.basename(fp), i))
                if 'class="nmld"' in ln and '.nmld' not in ln.split('class="nmld"')[0][-3:]:
                    raw.append('%s:%d nmld' % (os.path.basename(fp), i))
    except Exception as e:
        print('⚠️ check_loader_ssot 스킵:', e); return 0
    if len(raw) > BASELINE:
        print('❌ 로딩 SSOT 하드락 — raw 로더(gdots·nmld) %d > 0 · 새 로딩 표기 = window.nmLoader(type,label)만(nm-loader.js · type=thinking|solving|prompting):' % len(raw))
        for r in raw[:8]:
            print('   ·', r)
        return 1
    print('✅ 로딩 SSOT 하드락 — raw 로더(gdots·nmld) 0(전 뷰어 orb 단일 · 신규 = window.nmLoader 강제).')
    return 0




# ── 모델 ID 드리프트 게이트 (운영자 260725 한 수 · 정본 = shared/models.json) ──
# 모델 ID가 20+ 호출처에 리터럴로 흩어져 있어 승격(260725 Opus 4.8→5 = 22곳 실측)마다 전수 grep = 빠뜨림.
# 런타임 결합(호출처가 json을 읽게)은 Cloudflare Functions·정적 뷰어에 파일 접근이 없어 불가 → 「정본 1곳 +
# 기계 치환(shared/apply_models.py) + 이 게이트」 3점. 치환기가 놓친 한 곳을 여기서 커밋 차단한다.
_MODEL_ID_RE = re.compile(r'claude-[a-z]+-[0-9][0-9a-z.-]*')
_MODEL_NAME_GUARD = '(?![인명])'   # `Opus 5인/5명`(인원) = 모델명 아님 — apply_models.py NAME_GUARD와 동일 규약


def _model_registry():
    with open(os.path.join(ROOT, 'shared', 'models.json'), encoding='utf-8') as f:
        return json.load(f)


def _model_scan_files(reg):
    drop = set()
    for g in reg['scan']['exclude']:
        drop |= {os.path.abspath(p) for p in glob.glob(os.path.join(ROOT, g), recursive=True)}
    out = []
    for g in reg['scan']['include']:
        for p in glob.glob(os.path.join(ROOT, g), recursive=True):
            ap = os.path.abspath(p)
            if os.path.isfile(ap) and ap not in drop and not any(ap.startswith(d + os.sep) for d in drop):
                out.append(ap)
    return sorted(set(out))


def check_model_ids():
    """모델 ID·표시명 드리프트 하드게이트(운영자 260725 한 수 · 정본 = `shared/models.json`).
    ① 스캔 경로의 모든 `claude-*` 리터럴이 정본 등재 ID인지 — 오타(`claude-opus5`)·미등재 모델 차단.
    ② 정본 `retired`(구세대 ID·표시명)가 한 톨도 안 남았는지 — 승격 때 '한 곳 빠뜨림' 봉쇄(이 게이트의 본체).
    승격법 = `python3 shared/apply_models.py <티어> <새ID> "<새 표시명>" "<새 한글명>"` → 이 게이트로 검산 → 커밋.
    ⚠️ 표시명 검사는 `Opus 5인/5명`(인원 표기)을 (?![인명]) 가드로 제외 — 인원은 '명'으로 써라(모델명과 붙어 읽힌다).
    스캔 범위·제외(원장·보고서·동결본·산출물)도 models.json `scan`이 정본 = 여기 하드코딩 없음."""
    try:
        reg = _model_registry()
    except Exception as e:
        print('❌ 모델 ID 게이트: shared/models.json 못 읽음(부재/문법?) —', e); return 1   # fail-closed = 정본 소실 무성 무력화 차단
    ids = {t['id'] for t in reg['tiers'].values()}
    retired = [(r, re.compile(re.escape(r) + (_MODEL_NAME_GUARD if not r.startswith('claude-') else '')))
               for r in reg.get('retired', [])]
    # 벤더(비-Claude · 종량제) = 표시명 없이 ID만 · family 정규식으로 '그 계열의 다른 버전이 섞였나'를 본다
    vendors = [(k, v['id'], re.compile(v['family']), set(v.get('allow', [])))
               for k, v in reg.get('vendors', {}).items() if v.get('family')]
    bad = []
    for path in _model_scan_files(reg):
        try:
            src = open(path, encoding='utf-8').read()
        except (OSError, UnicodeDecodeError):
            continue
        rel = os.path.relpath(path, ROOT)
        for lit in sorted(set(_MODEL_ID_RE.findall(src))):
            if lit not in ids:
                bad.append('%s: 미등재 모델 ID `%s` (정본 = %s)' % (rel, lit, ' · '.join(sorted(ids))))
        for key, vid, rx, allow in vendors:
            for lit in sorted(set(rx.findall(src))):
                if lit != vid and lit not in allow:
                    bad.append('%s: 벤더[%s] 계열 드리프트 `%s` — 정본 `%s`%s (종량제 = ID 어긋나면 실패·오과금)'
                               % (rel, key, lit, vid, (' · 허용 알리아스 %s' % ' '.join(sorted(allow))) if allow else ''))
        for raw, rx in retired:
            n = len(rx.findall(src))
            if n:
                bad.append('%s: 구세대 표기 `%s` %d곳 잔존 — `python3 shared/apply_models.py` 재실행 or 수동 교체' % (rel, raw, n))
    if bad:
        print('❌ 모델 ID 게이트 — 정본(shared/models.json) 드리프트:')
        for b in bad: print('   -', b)
        return 1
    print('✅ 모델 ID 게이트 — %d티어(%s) + 벤더 %d종(%s) 정본 일치 · 구세대 %d종 잔존 0(스캔 %d파일 · 승격 = apply_models.py).'
          % (len(ids), ' · '.join(t['id'] for t in reg['tiers'].values()), len(vendors),
             ' · '.join(k for k, *_ in vendors), len(retired), len(_model_scan_files(reg))))
    return 0




# ── 게이트 문서화 메타 게이트 (운영자 260723 Q468 "게이트 문서화 강제 = 만들어놓고 안 봄 구조 차단") ──
# 모든 게이트(def check_*)가 정본 문서에 *이름으로* 등재됐는지 대조 → 미등재 신규 게이트 = rc=1 차단.
# = 색 전파 골격(STAGE4·check_palette_sync)의 SSOT 인덱스 완전성 소프트룰("새 기틀 = 인덱스 행 추가 · 누락
# = 규칙2 위반" = 디자인기틀_SSOT.md 서문 · 기계 강제 아님이라던 그것)의 기계화. 정본 = CLAUDE.md + 디자인
# SSOT + 규칙·큐레이션 정본 문서(로그류 큐/이력 제외). 기존 미등재 = _GATE_DOC_BASELINE 면책(품질 유지 =
# 대량 소급 문서화 강제 안 함 · 신규만 래칫 · 베이스라인 = 소급 문서화 TODO·축소 지향). 자기 자신
# (check_gate_docs)도 대상 = SSOT §6·CLAUDE.md [15] 등재(자기참조 정합).
_GATE_DOC_CANON = ('CLAUDE.md', '디자인기틀/디자인기틀_SSOT.md', '디자인기틀/CII_컴포넌트계승인덱스.md',
                   'docs/라우터_법령전문.md', 'docs/실행계약_전문.md', '디자인기틀/플레이그라운드_포터블.md',
                   'docs/curation-algorithm.md', 'docs/curation-rubric.md')
_GATE_DOC_BASELINE = frozenset({   # 260723 스냅샷 = 소급 문서화 대상(신규 추가 = 문서화 회피라 지양 · diff 가시 · 축소 지향)
    'check_paths', 'check_versions', 'check_viewer_js', 'check_functions_js', 'check_inject_dividers',
    'check_inject_markers', 'check_sens_vocab', 'check_fast_max_h_parity', 'check_shell_cache_parity',
    'check_tokens_link', 'check_dangling_var', 'check_candidates_size', 'check_conflict_markers',
    'check_qledger_unique', 'check_anchor_liveness', 'check_html_charset', 'check_fp_parity', 'check_label_fill'})


# ── 정본 커버리지 역방향 게이트 (운영자 260725 한 수 · check_gate_docs의 반대 방향) ──
# check_gate_docs = "게이트가 문서에 등재됐나"(게이트 → 문서). 그 역방향이 비어 있었다: **문서가 "이게 정본"이라
# 선언한 축 중 기계 게이트가 없는 것**. 이 레포는 같은 사고를 4번 겪고서야 게이트를 붙였다(색=팔레트 · 로딩=nmLoader ·
# 탭 캐시=_headers · 모델=models.json) — 전부 "정본 선언은 있는데 기계는 없던" 구간이다. 다음 사각을 사고 전에
# 목록으로 뽑는 게 이 게이트의 일. 산문(.md)은 기계 대조 대상이 아니라 제외(코드·데이터·워크플로만).
_SSOT_DECL = re.compile(r'(?:정본|SSOT)\s*=\s*`([^`\n]+)`')
_SSOT_EXT = ('.js', '.py', '.sh', '.css', '.html', '.json', '.yml', '.mjs', '.ts')
_SSOT_BASELINE = frozenset({   # 260725 스냅샷 = 게이트 미보유 정본 축(축소 지향 · 신규 추가 = 사각 방치라 지양 · diff 가시)
    '.github/actions/runner-setup/action.yml',   # 러너 부팅 계약(파이썬·노드·캐시 키) — 깨지면 전 파이프 실패
    '.github/scripts/group_judge.py',            # 사건 동일성 AI 판정 · RUBRIC 해시 축
    '.github/scripts/push_send.py',              # 푸시 발송 게이트(grade·dedup)
    '.github/scripts/thumb_gen.py',              # 썸네일 렌더 = gemini_image 정본(모델 ID는 check_model_ids가 봄 · 계약은 미보유)
    'functions/api/seen.js',                     # 계정 축(✓ack·seen) 정본 = CLAUDE.md [4] 등재
    'scraper/daily_health.py',                   # 일일 건강 계기판(OUT·배지·독점)
    'scraper/to_pending.py',                     # 후보→대기 승격 계약
    'shared/attach.py'})                         # 첨부 파이프 정본


_SSOT_SKIPDIR = {'.git', 'node_modules', '_versions', 'metrics', 'cards', 'dist'}


def _ssot_resolve(p):
    """문서 표기(`thumb-make.yml` 처럼 파일명만 쓴 것)를 레포 실경로로 해석 — 유일 해석만 채택(모호·부재 = None).
    ⚠️ glob('**') 금지: 파이썬 글롭은 숨김 디렉터리를 안 본다 → `.github/` 아래(워크플로·스크립트 = 파이프라인 전부)가
    통째로 안 잡히는 사각이 된다(신설 때 실측: thumb-make.yml·gate_judge.py가 조용히 누락). os.walk로 직접 훑는다."""
    if os.path.exists(os.path.join(ROOT, p)):
        return p
    base, hits = os.path.basename(p), []
    for cur, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in _SSOT_SKIPDIR]
        if base in files:
            hits.append(os.path.relpath(os.path.join(cur, base), ROOT))
    return hits[0] if len(hits) == 1 else None




def check_ssot_coverage():
    """정본 커버리지 역방향 게이트(운영자 260725 한 수 · `check_gate_docs`의 반대 방향).
    정본 문서가 「정본 = `<코드/데이터/워크플로 파일>`」로 **선언**한 축 중 `check_refs.py`가 손대지 않는 것 =
    '선언만 있고 기계는 없는' 사각 → 신규는 rc=1 차단, 기존은 `_SSOT_BASELINE` 면책(축소 지향 · 대량 소급 강제 안 함).
    왜: 이 레포의 게이트 4종(팔레트·로더·탭 캐시·모델 ID)이 전부 *사고 후에* 붙었고, 사고 전 상태는 매번 똑같이
    「문서엔 정본 선언 있음 + 기계 없음」이었다. 그 상태를 사고 전에 목록으로 뽑는 게 이 게이트다.
    ⚠️ 산문(.md) 정본은 기계 대조 대상이 아니라 제외 · 게이트를 새로 못 붙일 축은 베이스라인 추가(= diff로 가시화)."""
    src = open(os.path.join(ROOT, 'shared', 'check_refs.py'), encoding='utf-8').read()
    # ⚠️ 베이스라인 리터럴은 대조에서 뺀다 — 안 빼면 면책 목록에 적힌 경로가 스스로 '게이트가 언급함'이 되어
    #    영원히 초록으로 보이는 자기무력화가 된다(신설 첫 런 실측 = 미보유 9축이 0으로 둔갑).
    src = re.sub(r'_SSOT_BASELINE = frozenset\(\{.*?\}\)', '', src, flags=re.S)
    decl = {}
    for d in _GATE_DOC_CANON:
        p = os.path.join(ROOT, d)
        if not os.path.exists(p):
            continue
        for m in _SSOT_DECL.finditer(open(p, encoding='utf-8').read()):
            raw = m.group(1).strip().split()[0].rstrip('·,)')
            if not (raw.endswith(_SSOT_EXT) or os.path.basename(raw) == '_headers'):
                continue
            rel = _ssot_resolve(raw)
            if rel:
                decl.setdefault(rel, set()).add(d)
    # '게이트가 손댄다' = check_refs.py 본문이 그 경로나 파일명을 언급(경로 조립 관용구가 basename이라 둘 다 본다)
    bare = [p for p in sorted(decl) if p not in src and os.path.basename(p) not in src]
    new = [p for p in bare if p not in _SSOT_BASELINE]
    if new:
        print('❌ 정본 커버리지 — 새로 선언된 정본 축에 기계 게이트가 없다("선언만 있고 기계는 없음" = 사고 전 상태):')
        for p in new:
            print('   -', p, '← 선언:', ' '.join(sorted(decl[p])), '→ 게이트를 만들거나 _SSOT_BASELINE에 사유와 함께 추가하라')
        return 1
    print('✅ 정본 커버리지 — 선언된 정본 %d축 중 게이트 보유 %d · 미보유 %d(전부 260725 베이스라인 · 신규 사각 0 · 축소 지향).'
          % (len(decl), len(decl) - len(bare), len(bare)))
    return 0



# ── 활자 조용사(silent-fail) 게이트 2종 (운영자 260727 한 수 채택 — 같은 유형이 3회 머지 동안 미검출된 실사고 재발방지) ──
# 왜 하드인가: 둘 다 "브라우저가 조용히 버리거나 안 물려줘서" 눈에는 '미묘하게 다름'으로만 보인다 → 리뷰·스샷으로 안 잡힌다.
_FORM_FONT_SURFACES = ('viewer/index.html', 'viewer/thumb.html', 'viewer/tr.html')   # 이미지 스튜디오 3표면(신규 편입 = 이 튜플에 1줄)
_FORM_FONT_RE = re.compile(r'button\s*,\s*input\s*,\s*textarea\s*,\s*select\s*\{[^}]*font-family\s*:\s*inherit[^}]*letter-spacing\s*:\s*inherit', re.S)
_FONT_SHORTHAND_RE = re.compile(r'(?<![-a-zA-Z])font\s*:\s*([^;{}]*\binherit\b[^;{}]*);')   # 값 안에 inherit 등장 → 아래에서 '단독 inherit(합법)'만 통과


def _strip_css_comments(t):
    return re.sub(r'/\*.*?\*/', ' ', t, flags=re.S)


_DRIVE_BAT_LINE = re.compile(r'^>> "%B64%" echo (\S+)\s*$', re.M)


# 운영자 PC 배포 번들 = (라벨, ps1 정본, 산출 .bat, 재생성기) — 새 번들을 만들면 여기 1줄만 추가한다.
#   260804 편입 = 스레드 플러그인 갱신기(같은 사고를 그대로 반복했다 — 한글을 .bat에 직접 실어 cp949에서
#   파싱이 무너졌고 운영자 화면에 "'fined'은(는) 내부 또는 외부 명령이 아닙니다"가 줄줄이 떴다).
_PC_BUNDLES = (
    ('드라이브 이동', 'drive_move_watch.ps1', '노뮤트_구글드라이브_자동이동_설치.bat', 'build_drive_move_bundle.py'),
    ('스레드 플러그인', 'threads_plugin_update.ps1', '노뮤트_스레드플러그인_갱신.bat', 'build_threads_plugin_bundle.py'),
)


def check_drive_move_bundle():
    """운영자 PC 배포 번들(더블클릭 .bat) ↔ ps1 정본 드리프트 차단(운영자 260801 · CLAUDE.md [9-1 납품]).
    각 .bat = ps1 전체를 base64로 실은 기계산출물이자 **운영자가 실제로 더블클릭하는 라이브 표면**.
    ps1만 고치고 재생성을 잊으면 머지는 초록인데 운영자 PC에는 옛 코드가 깔린다(조용한 라이브 낡음).
    base64로 싣는 이유 = cmd는 .bat을 OEM 코드페이지(949)로 읽어 한글이 깨진다 → 페이로드는 ASCII여야 한다.
    대상 = _PC_BUNDLES(새 번들 = 1줄 추가 · 손 목록이지만 짝이 안 맞으면 곧바로 rc=1이라 조용히 못 빠진다)."""
    rc = 0
    for label, ps1n, batn, gen in _PC_BUNDLES:
        ps1 = os.path.join(ROOT, 'scripts', ps1n)
        bat = os.path.join(ROOT, 'scripts', batn)
        if not os.path.exists(ps1) and not os.path.exists(bat):
            print('✅ %s 번들 게이트 — 대상 없음(스킵).' % label)
            continue
        if not (os.path.exists(ps1) and os.path.exists(bat)):
            print('❌ %s 번들 게이트 — 짝이 안 맞는다(ps1 존재=%s · bat 존재=%s · 둘은 한 세트다).'
                  % (label, os.path.exists(ps1), os.path.exists(bat)))
            rc = 1
            continue
        try:
            txt = open(bat, 'rb').read().decode('ascii')
        except UnicodeDecodeError:
            print('❌ %s 번들 게이트 — .bat에 비ASCII 바이트(cmd OEM 949에서 깨진다) → 재생성하라.' % label)
            rc = 1
            continue
        try:
            payload = base64.b64decode(''.join(_DRIVE_BAT_LINE.findall(txt)), validate=True)
        except Exception as e:
            print('❌ %s 번들 게이트 — base64 페이로드 복원 실패(%s) → 재생성하라.' % (label, e))
            rc = 1
            continue
        want = open(ps1, 'rb').read()
        if payload != want:
            print('❌ %s 번들 게이트 — .bat 안 페이로드 ≠ scripts/%s (운영자 PC에 옛 코드가 깔린다)'
                  ' → `python3 scripts/%s` 로 재생성하라.' % (label, ps1n, gen))
            rc = 1
            continue
        if not want.startswith(b'\xef\xbb\xbf'):
            print('❌ %s 번들 게이트 — ps1에 UTF-8 BOM 없음 → 한글이 깨진다.' % label)
            rc = 1
            continue
        print('✅ %s 번들 게이트 — .bat 페이로드 = %s 바이트 동일(%d B · .bat 전량 ASCII · UTF-8 BOM 보존).'
              % (label, ps1n, len(want)))
    return rc


def check_font_shorthand():
    """`font:` 축약형 안 `inherit` 금지(운영자 260727 실사고 재발방지).
    CSS 문법상 `inherit`은 `font` 축약형의 family 자리에 올 수 없다 → **선언 전체가 무효** → 그 요소가 body 활자를
    조용히 상속한다(260727 실측: 옵션 칩이 13px/700 대신 15px/400으로 렌더 · 3회 머지 동안 미검출).
    교정 정본 = `font-family:inherit; font-size:…; font-weight:…` 분해형(viewer/sb.html `.geni-opt`)."""
    bad = []
    for rel in sorted(glob.glob(os.path.join(ROOT, 'viewer', '*.html'))):
        txt = _strip_css_comments(open(rel, encoding='utf-8').read())
        for m in _FONT_SHORTHAND_RE.finditer(txt):
            val = m.group(1).strip()
            if val == 'inherit':
                continue   # `font:inherit` 단독 = 합법(전역 키워드가 축약 전체에 적용) · 무효는 다른 값과 섞였을 때뿐
            bad.append((os.path.relpath(rel, ROOT), txt[:m.start()].count('\n') + 1, m.group(0)[:70]))
    if bad:
        print('❌ 활자 무효축약 게이트 — `font:` 축약형 안 `inherit`(=선언 전체 무효 · 조용한 body 상속):')
        for f, ln, frag in bad:
            print('   - %s:%d  %s → `font-family:inherit; font-size:…; font-weight:…` 분해형으로(정본 = sb.html .geni-opt)' % (f, ln, frag))
        return 1
    print('✅ 활자 무효축약 게이트 — `font:` 축약 안 inherit 0(무효 선언으로 인한 조용한 활자 드리프트 차단).')
    return 0


def check_form_font_inherit():
    """폼 요소 활자 계승 리셋 존재(운영자 260727 "같은 형태에 있는 애들은 다 같아야함").
    `button/input/textarea/select`는 UA 기본이 font-family·letter-spacing **상속을 끊는다** → 같은 카드에서 라벨은
    자간 −.2px인데 칩(button)만 normal, 미스타일 input은 Arial로 렌더(260727 실측). 각 표면이 리셋 1줄을 갖는지 확인."""
    miss = []
    for rel in _FORM_FONT_SURFACES:
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            miss.append((rel, '파일 없음')); continue
        src = open(p, encoding='utf-8').read()
        # 260807 = 이 규칙이 nm-shared.css 공용 SSOT로 승격됐다 → **link 상속도 보유로 인정**한다.
        #   (인라인만 인정하면 SSOT 이관 자체를 게이트가 막는 자기모순 = check_clip_canon 선례와 동축)
        if 'href="nm-shared.css"' in src and _FORM_FONT_RE.search(
                open(os.path.join(ROOT, 'viewer', 'nm-shared.css'), encoding='utf-8').read()):
            continue
        if not _FORM_FONT_RE.search(src):
            miss.append((rel, '리셋 규칙 없음'))
    if miss:
        print('❌ 폼 활자 계승 게이트 — 상속 리셋 누락(UA 기본이 글꼴·자간 상속을 끊어 같은 부품끼리 갈린다):')
        for rel, why in miss:
            print('   - %s (%s) → `button, input, textarea, select { font-family:inherit; letter-spacing:inherit; }` 1줄(값 신설 0)' % (rel, why))
        return 1
    print('✅ 폼 활자 계승 게이트 — 이미지 스튜디오 %d표면 전부 상속 리셋 보유(칩·버튼·입력 활자 = 문서 활자 계승).' % len(_FORM_FONT_SURFACES))
    return 0



def check_branch_freshness():
    """브랜치 신선도 WARN(운영자 260727 재발방지 — 260726 평행 구현 사고: 착수 전 fetch를 안 해
    동시 세션이 main에 이미 넣은 변경을 모르고 같은 파일을 다시 만들었다 → 충돌·중복·배포 도장 회귀).
    내가 이 브랜치에서 건드린 파일을, merge-base 이후 main도 건드렸으면 경고한다(비차단 = 오탐 관용)."""
    try:
        import subprocess
        def sh(*a):
            return subprocess.run(a, cwd=ROOT, capture_output=True, text=True, timeout=20).stdout.strip()
        base = sh('git', 'merge-base', 'HEAD', 'origin/main')
        if not base:
            print('⚠️ 브랜치 신선도(WARN) — origin/main 참조 없음(fetch 전) → `git fetch origin main` 먼저.'); return 0
        mine = set(filter(None, sh('git', 'diff', '--name-only', base + '..HEAD').split('\n')))
        mine |= set(filter(None, sh('git', 'diff', '--name-only').split('\n')))
        theirs = set(filter(None, sh('git', 'diff', '--name-only', base + '..origin/main').split('\n')))
        both = sorted(f for f in (mine & theirs) if f.endswith(('.html', '.js', '.py', '.css')))
        if both:
            print('⚠️ 브랜치 신선도(WARN·비차단) — 내가 만진 파일을 main도 그 사이 바꿨다(평행 구현·충돌 위험):')
            for f in both[:8]:
                print('   -', f, '→ 커밋 전 `git fetch origin main && git rebase origin/main`로 최신 위에서 재확인(260726 사고 재발방지)')
        else:
            print('✅ 브랜치 신선도 — 내가 만진 파일과 main의 신규 변경 교집합 0(평행 구현 위험 없음).')
    except Exception as e:
        print('⚠️ 브랜치 신선도(WARN) — 판정 생략:', e)
    return 0


def _js_code_part(ln):
    """JS 한 줄에서 **코드부만** 남긴다(줄 끝 주석·인라인 블록 주석 제거 · `https://`의 // 는 보존).
    이 레포는 규칙·선언 뒤에 개정 사유를 길게 붙이는 관례라, 심볼 부활 검사에 주석부가 섞이면 처방문 자신이 위반으로 잡힌다."""
    t = re.sub(r'/\*.*?\*/', ' ', ln)
    m = re.search(r'(?<!:)//', t)
    if m:
        t = t[:m.start()]
    return t


def check_nm_jobs():
    """여러 작업 동시 추적 게이트(운영자 260810 "동시에 2가지 작업을 큐잉하면 첫번째거를 두번째꺼가 덮어씌워져") —
    `viewer/nm-jobs.js` SSOT(슬롯 다중화 + 폴 레지스트리)를 스튜디오 5탭이 상속하는지, 그리고 **구판 단일 슬롯 문법이
    되살아나지 않는지** 정적 강제. ⚠ 신설 사유 = 이 사고의 두 원인은 전부 「한 개만 든다」는 **코드 모양**이었다 —
    ⓐ 재개 슬롯을 `localStorage.setItem(PEND_KEY, …)`로 직접 덮어쓰기 ⓑ 폴 중단 핸들 전역 1개(`_curStop`).
    둘 다 화면 증상이 「아무 일도 안 일어남」뿐이라 렌더 스모크·정적 문자열 게이트가 전부 통과했고 운영자 눈이
    유일한 검출기였다. 런타임 짝 = `shared/smoke_jobsq.js`(2건 동시 생존 실렌더) — 정적·런타임 두 겹이라야
    새 탭이 조용히 빠질 구멍이 없다(check_nm_sync 자동발견 관례 계승 · 면책표 없이 하드 0)."""
    core = ['edit.html', 'sb.html', 'k.html', 'song.html', 'vd.html']   # 영상 스튜디오 5탭 = 큐잉 표면
    vdir = os.path.join(ROOT, 'viewer')
    bad = []
    mp = os.path.join(vdir, 'nm-jobs.js')
    if not os.path.exists(mp):
        print('❌ 동시 작업 추적 게이트 — viewer/nm-jobs.js 부재(SSOT 소실)')
        return 1
    msrc = open(mp, encoding='utf-8').read()
    for lit in ('add:', 'list:', 'drop:', 'hold:', 'free:', 'count:', 'window.nmJobs'):
        if lit not in msrc:
            bad.append('nm-jobs.js 골격 소실: ' + lit)
    if 'if (POLL[k]) return false;' not in msrc:
        bad.append('nm-jobs.js — 같은 id 중복 폴 차단 술어 소실')
    if 'stopAll(' in msrc.split('hold: function')[-1].split('free:')[0]:
        bad.append('nm-jobs.js — hold()가 남의 폴을 끊는다(구판 _curStop 회귀 = 병렬 파괴)')
    for f in core:
        p2 = os.path.join(vdir, f)
        if not os.path.exists(p2):
            bad.append(f + ' 부재(고정 표면)')
            continue
        src = open(p2, encoding='utf-8').read()
        if 'src="nm-jobs.js"' not in src:
            bad.append(f + ' — nm-jobs.js 미상속')
        # ⚠ **여러 줄 블록 주석을 먼저 지운다**(길이 보존 공백 마스킹 = css_hoist 관례) — 줄 단위로만 보면 블록 주석
        #   가운데 줄엔 `/*`도 `//`도 없어 그 안의 구판 심볼 인용이 위반으로 잡힌다(첫 실행 실측 = 이 봉합의 설명 주석 자신).
        src = re.sub(r'/\*.*?\*/', lambda m: re.sub(r'[^\n]', ' ', m.group(0)), src, flags=re.S)
        for ln in src.split('\n'):
            t = _js_code_part(ln).strip()   # ⚠ 주석부는 잘라낸다 — 이 봉합의 개정 사유 주석이 구판 심볼을 **인용**하므로(줄 끝 주석 포함) 줄 선두만 보면 자기 처방문에 걸린다(첫 실행 실측)
            if not t:
                continue
            if 'localStorage.setItem(PEND_KEY' in t:
                bad.append(f + ' — 구판 단일 슬롯 직접 저장 부활(setItem(PEND_KEY…) = 뒤 발사가 앞 작업을 덮는다)')
            if '_curStop' in t:
                bad.append(f + ' — 구판 전역 폴 중단 핸들(_curStop) 부활 = 뒤 폴이 앞 폴을 죽인다')
    if bad:
        print('❌ 동시 작업 추적 게이트 — 상속 누락·구판 회귀:')
        for b in sorted(set(bad)):
            print('   -', b)
        return 1
    print('✅ 동시 작업 추적 게이트 — 영상 스튜디오 5탭 전부 nm-jobs.js 상속 · 구판 단일 슬롯/전역 폴 중단 부활 0 · 모듈 골격 intact.')
    return 0


def check_nm_sync():
    """동기화 생명선 상속 게이트(운영자 260803 4차 "다른 스튜디오 탭에도 전부 상속") — `viewer/nm-sync.js` SSOT(복귀 자동 재동기 ·
    로그인 만료 자가치유 · 새 배포 자동 리로드)를 스튜디오 전 탭이 `<script src="nm-sync.js">`로 상속하는지 정적 강제.
    표면 = 고정 7(thumb·tr·edit·sb·k·song·vd) + 자동 발견(`window.nmRefresh` 훅 보유 = 동기화 생태계 참여 선언 → 상속 의무 —
    새 탭이 조용히 빠질 수 없다 · check_trail_spec 자동발견 동축). 모듈 자체도 3축 골격(manifest 프로브 · /?nosw=1 재진입 ·
    HEAD ETag 대조)을 잃으면 FAIL = 속을 비우는 조용한 무력화 차단."""
    core = ['thumb.html', 'tr.html', 'edit.html', 'sb.html', 'k.html', 'song.html', 'vd.html']
    vdir = os.path.join(ROOT, 'viewer')
    bad = []
    try:
        msrc = open(os.path.join(vdir, 'nm-sync.js'), encoding='utf-8').read()
    except Exception:
        print('❌ 동기화 생명선 게이트 — viewer/nm-sync.js 부재(SSOT 소실)')
        return 1
    for lit in ('/manifest.json', '/?nosw=1', "method: 'HEAD'"):
        if lit not in msrc:
            bad.append('nm-sync.js 골격 소실: ' + lit)
    surf = set(core)
    for f in os.listdir(vdir):
        if f.endswith('.html'):
            try:
                if 'window.nmRefresh' in open(os.path.join(vdir, f), encoding='utf-8').read():
                    surf.add(f)
            except Exception:
                continue
    for f in sorted(surf):
        p = os.path.join(vdir, f)
        if not os.path.exists(p):
            bad.append(f + ' 부재(고정 표면)')
            continue
        if 'src="nm-sync.js"' not in open(p, encoding='utf-8').read():
            bad.append(f + ' — nm-sync.js 미상속')
    if bad:
        print('❌ 동기화 생명선 게이트 — 상속 누락/골격 소실:')
        for b in bad:
            print('   -', b)
        return 1
    print('✅ 동기화 생명선 게이트 — %d표면 전부 nm-sync.js 상속(고정 7 + nmRefresh 자동발견) · 모듈 3축 골격 intact.' % len(surf))
    return 0


def check_brk_misfire_chain():
    """긴급 오발 신고 폐루프 게이트(하드 · 운영자 260803 4차 "누적될 때 활용을 안 하면 소용이 없다").
    체인 = 뷰어 배지 롱프레스 신고 → /api/rate(reason 예약키 brkno) → rate.yml 스텝 → brk_misfire.py → msg.py.
    한 층만 빠져도 **신고가 조용히 사라지는**(적재는 되는데 아무도 안 읽는) 죽은 원장이 되므로 층별 심볼 생존을
    정적으로 강제한다(네트워크·LLM 0). ⚠️ 예약키는 4곳이 같은 문자열이어야 한다 — 뷰어 송신·소비기 필터 상수.
    ⚠️ rate.yml inputs 는 GitHub 상한 10개 = 신규 입력 추가 금지(11번째 = 디스패치 400 = 평점 레일 전체 사망)."""
    v = os.path.join(ROOT, 'viewer', 'index.html')
    s = os.path.join(ROOT, 'scraper', 'brk_misfire.py')
    y = os.path.join(ROOT, '.github', 'workflows', 'rate.yml')
    bad = []
    try:
        vt = open(v, encoding='utf-8').read()
        st = open(s, encoding='utf-8').read()
        yt = open(y, encoding='utf-8').read()
    except Exception as e:
        print('❌ 긴급 오발 신고 체인 게이트 — 파일 열기 실패: %s' % e)
        return 1
    if "function brkNotUrgent" not in vt or "reason: 'brkno'" not in vt:
        bad.append('뷰어 송신 결손 — viewer/index.html brkNotUrgent()/reason:\'brkno\'')
    if "'.sc-badge.brk'" not in vt or 'brkClaimBadge(' not in vt:
        bad.append('뷰어 배지 롱프레스 배선 결손 — .sc-badge.brk 훅')
    if "'.urg.brk'" not in vt:   # 피드 표면 — 한쪽만 달면 똑같이 생긴 '긴급'을 다른 화면에서 눌렀을 때 무반응(배지 패리티와 동축)
        bad.append('피드 배지 배선 결손 — .urg.brk(수집함만 달면 운영자가 신고했다고 믿는데 데이터 0)')
    if 'REASON_KEY = "brkno"' not in st:
        bad.append('소비기 예약키 불일치 — scraper/brk_misfire.py REASON_KEY')
    if 'MSG_PY' not in st or 'shared' not in st:
        bad.append('소비기 알림 경로 결손 — msg.py 호출')
    if "'brkno'" not in open(os.path.join(ROOT, 'build-viewer.mjs'), encoding='utf-8').read():
        bad.append('트리아지 제외 결손 — build-viewer.mjs 가 brkno 행을 최신행 승리에서 안 뺀다(확인✓ 소실→긴급 재토스트)')
    # ⚠️ 실행줄만 인정 — 평문 substring 이면 `# python3 scraper/brk_misfire.py` 처럼 **주석 처리해도 통과**한다
    #    (check_refs 자신이 1585행에서 "평문 needle = self-match 함정"이라 명시한 패턴).
    if not _has_exec_line(yt, 'python3 scraper/brk_misfire.py'):
        bad.append('워크플로 소비 스텝 결손 — .github/workflows/rate.yml 실행줄')
    if 'git add -A messages' not in yt or 'git add scraper/brk_misfire.json' not in yt:
        bad.append('워크플로 커밋 결손 — messages/·원장이 커밋 안 되면 알림이 배포에 안 실린다')
    if 'brk_misfire.py' not in open(os.path.join(ROOT, '.github', 'workflows', 'watchdog.yml'), encoding='utf-8').read():
        bad.append('TTL 상시 갱신 결손 — watchdog.yml(운영자가 별점을 안 누르면 알림이 24h 뒤 조용히 소멸)')
    # inputs 상한(10) 초과 방지 — 초과 시 dispatch 자체가 400(평점·신고 레일 동시 사망)
    m = re.search(r'workflow_dispatch:\s*\n\s*inputs:\s*\n((?:\s{6,}\S.*\n|\s*\n)+?)\s{0,4}concurrency:', yt)
    n_in = len(re.findall(r'^\s{6}(\w+):\s*$', m.group(1), re.M)) if m else -1
    if n_in > 10:
        bad.append('rate.yml workflow_dispatch inputs %d개 > GitHub 상한 10 — 디스패치 400 확정' % n_in)
    if bad:
        print('❌ 긴급 오발 신고 체인 게이트 — 층 결손 %d건(신고가 조용히 죽는다):' % len(bad))
        for b in bad:
            print('   ·', b)
        return 1
    print('✅ 긴급 오발 신고 체인 게이트 — 뷰어 신고·예약키·워크플로 스텝·소비기·알림 5층 생존(rate.yml inputs %d/10).' % n_in)
    return 0


_VOTE_ICONS = ('THUMBUP_SVG', 'THUMBDOWN_SVG')
# 👍/👎 투표 = 한 벌(운영자 260805 "고정으로 박아줘 다른데서 만들면 참조하도록"). 계약 전문 = CII 「👍/👎 선호 투표」 행.
# CONTRACT: check_vote_btn_canon


def check_vote_btn_canon():
    """👍/👎 선호 투표 부품 = 한 벌 계승(하드 · 운영자 260805 "고정으로 박아줘 다른데서 만들면 참조하도록").

    계약 = **새 투표 버튼은 정본을 입고 상태 클래스만 얹는다** — 클래스 `.fbup`/`.fbdown` · 아이콘 상수
    `THUMBUP_SVG`/`THUMBDOWN_SVG` · 점등 `.sbtn.voted` · 취소 arm `.thumb-arm`/`disarmThumb`.
    ⚠ 신설 사유 = 이 부품은 260629 카드뉴스에서 확립돼 260805 썸네일 슬롯이 **사본 0으로 계승**했는데,
      그 계승이 성립한 건 순전히 세션이 정본을 찾아본 덕이었다 — 기존 게이트 중 어느 것도 「투표 버튼이
      정본을 입었는가」를 안 본다(`check_launch_spec`=발사 버튼 · `check_trail_spec`=레일 · `check_icon_ssot`
      =공유 아이콘 파일). 다음 표면이 `<button class="likebtn">👍</button>` 로 만들어도 무경보였다.
      운영자가 「모조품 만들지 마」를 발사 버튼에서 게이트로 봉쇄한 것과 같은 축(클래스는 붙이길 잊으면
      부활하지만 게이트는 우회 불가).
    판정 3축(정적 · 렌더·LLM·네트워크 0 · **면책표 없이 하드 0**) =
      ① 정본 생존 — 아이콘 상수 정의 · `.sbtn.voted` · `.thumb-arm` · `disarmThumb` 가 index 에 실재.
      ② 이모지 금지 — 투표 버튼 안에 `👍`/`👎` 문자 렌더 0(§🔒3-1 표지판성 도형 = SVG · 문자 글리프는
         폰트 의존 편심이라 원/박스 정중앙에서 어긋난다).
      ③ 모조 클래스 금지 — 투표를 뜻하는 새 클래스(`like`/`upvote`/`thumbsup` 류)가 버튼에 붙으면 FAIL
         (정본은 `.fbup`/`.fbdown` 두 이름뿐).
    ⚠ 스코프 = `viewer/*.html` 자동 발견(새 뷰어가 조용히 못 빠진다) · 주석 줄·`<script>` 안 정규식 리터럴은
      비대상(`check_clip_coverage` 템플릿 배제 선례)."""
    idx = os.path.join(ROOT, 'viewer', 'index.html')
    try:
        it = open(idx, encoding='utf-8').read()
    except Exception as e:
        print('❌ 투표 부품 게이트 — viewer/index.html 열기 실패(fail-closed): %s' % e)
        return 1
    bad = []
    # ① 정본 생존 — 하나라도 사라지면 계승할 원본이 없어진다(그 순간 다음 표면은 재설계로 간다).
    for sym in _VOTE_ICONS:
        if ('const %s' % sym) not in it:
            bad.append('아이콘 정본 결손 — index %s 상수(계승할 원본 소실)' % sym)
    if '.sbtn.voted' not in it:
        bad.append('점등 정본 결손 — .sbtn.voted(투표 상태색이 표면마다 재창작된다)')
    if '.thumb-arm' not in it or 'function disarmThumb' not in it:
        bad.append('취소 arm 정본 결손 — .thumb-arm/disarmThumb(2탭 취소 문법 · 팝업 확인창 부활 위험)')
    # ②③ 표면 자동 발견 — 투표 버튼 마크업이 정본 문법을 벗어났는가.
    vote_cls = re.compile(r'class="[^"]*\b(like|likebtn|upvote|downvote|thumbsup|thumbsdown|vote-?up|vote-?down)\b')
    for path in sorted(glob.glob(os.path.join(ROOT, 'viewer', '*.html'))):
        name = os.path.basename(path)
        try:
            t = open(path, encoding='utf-8').read()
        except Exception:
            continue
        for i, ln in enumerate(t.split('\n'), 1):
            st = ln.strip()
            if st.startswith('//') or st.startswith('/*') or st.startswith('*') or st.startswith('<!--'):
                continue
            if ('fbup' in ln or 'fbdown' in ln) and ('👍' in ln or '👎' in ln):
                bad.append('%s:%d 이모지 렌더 — 투표 픽토는 SVG 상수만(§🔒3-1)' % (name, i))
            m = vote_cls.search(ln)
            if m and '<button' in ln:
                bad.append('%s:%d 모조 투표 클래스 「%s」 — 정본 = .fbup/.fbdown 계승(CII 「👍/👎 선호 투표」)'
                           % (name, i, m.group(1)))
    if bad:
        print('❌ 투표 부품 게이트 — 정본 이탈 %d건:' % len(bad))
        for b in bad[:10]:
            print('   ·', b)
        print('   → 계약 전문 = 디자인기틀/CII_컴포넌트계승인덱스.md 「👍/👎 선호 투표」 행(재설계 금지·계승).')
        return 1
    print('✅ 투표 부품 게이트 — 정본 4심볼 생존 · 이모지 렌더 0 · 모조 클래스 0(전 뷰어 자동발견).')
    return 0


def check_cloud_action_chain():
    """클라우드 액션 서버(구글 드라이브 「내 드라이브/action」 = git 액션 대체 · 운영자 260814 Q1482~Q1487 =
    «노뮤트에디터를 돌리는 일괄 액션 서버 · 독립 제품») 층 생존.
    한 층만 빠져도 화면 증상 0으로 조용히 죽는다 — 본체가 실행기를 안 부르면 시계는 도는데 수집·판정만 소실,
    드라이브 스캔 한 이름이 빠지면 글자 바뀐 날부터 미러·환경변수만 소실, 접기(_B64) 한쪽만 살면 여러 줄
    열쇠(쿠키)가 조용히 깨진 채 주입(전부 로그 정상·에러 0 = insta-thumb-miss 동축) → 정적 층별 생존 강제 ·
    면책표 없이 하드 0. 축 = ① 본체(cloud_action.sh): 실행기 pc_lane.sh 호출 + 드라이브 두 이름 스캔 +
    계정값(맥 마운트 경로 실값) + 환경변수.txt 주입 + _B64 펴기 + --find ② 설치 뒷단(cloud_action_setup.sh):
    자기 시계(윈도우 NomuteCloudAction · 맥 crontab 마커) + 실행기 종점 + 열쇠 입력 페이지 배포 + 슬롯 씨앗 +
    계정값 사본 0 ③ 윈도우 설치 bat 자기완결(저장소 받기·클로드 로그인·뒷단) ④ 맥 command: 뒷단 호출
    ⑤ 실행기 실존 ⑥ 열쇠 입력 페이지: _B64 접기 보유(본체 펴기와 짝 — 한쪽만 고치면 여러 줄 열쇠 전멸)."""
    rc = 0
    wrap = os.path.join(ROOT, 'scripts', 'cloud_action.sh')
    setup = os.path.join(ROOT, 'scripts', 'cloud_action_setup.sh')
    bat = os.path.join(ROOT, 'scripts', '노뮤트_클라우드액션_설치.bat')
    cmdf = os.path.join(ROOT, 'scripts', '노뮤트_클라우드액션_설치.command')
    lane = os.path.join(ROOT, 'scripts', 'pc_lane.sh')
    keyhtml = os.path.join(ROOT, 'scripts', '노뮤트_열쇠입력.html')
    for p in (wrap, setup, bat, cmdf, lane, keyhtml):
        if not os.path.exists(p):
            print('❌ [cloud-action] 파일 소실: %s' % os.path.relpath(p, ROOT)); rc = 1
    if rc:
        return rc
    def _rd(p):
        with open(p, encoding='utf-8', errors='replace') as f:
            return f.read()
    w, s, b, c, h = _rd(wrap), _rd(setup), _rd(bat), _rd(cmdf), _rd(keyhtml)

    def _bat_exec(text, needle):
        # 배치의 주석은 REM — 주석 처리 우회 차단(_has_exec_line 의 배치판 · 킬테스트가 잡은 구멍의 짝)
        for ln in text.split('\n'):
            st = ln.strip()
            if st and not st.upper().startswith('REM') and needle in st:
                return True
        return False
    for cond, msg in (
        # ⚠ 전부 실행줄 판정(_has_exec_line) — 머리 주석에 같은 낱말이 살아 있어서 bare substring 은
        #   코드를 지워도 통과한다(킬테스트 K3 실측 = 「My Drive」 스캔을 지웠는데 주석이 면죄부).
        (_has_exec_line(w, 'pc_lane.sh'), 'cloud_action.sh 가 몸통(pc_lane.sh)을 실행하지 않는다'),
        (_has_exec_line(w, '내 드라이브') and _has_exec_line(w, 'My Drive'), 'cloud_action.sh 드라이브 폴더 두 이름(내 드라이브/My Drive) 스캔 소실'),
        (_has_exec_line(w, 'ems1130g@gmail.com'), 'cloud_action.sh 계정값 소실 — 맥 마운트 경로·다중 계정 대조 축'),
        (_has_exec_line(w, '환경변수.txt'), 'cloud_action.sh 환경변수 주입(키 착지 슬롯) 소실'),
        (_has_exec_line(w, '--find'), 'cloud_action.sh --find 모드 소실(설치 뒷단이 쓴다)'),
        (_has_exec_line(w, '*_B64)') and _has_exec_line(w, 'base64'), 'cloud_action.sh 여러 줄 열쇠 펴기(*_B64 분기) 소실 — 열쇠 입력 페이지 접기와 짝'),
        (_has_exec_line(s, 'cloud_action.sh'), 'cloud_action_setup.sh 가 시계 종점을 서버 본체(cloud_action.sh)에 안 태운다'),
        (_has_exec_line(s, 'nomute-cloud-action') and _has_exec_line(s, 'crontab'), 'cloud_action_setup.sh 맥 crontab 등록(마커 nomute-cloud-action) 소실'),
        (_has_exec_line(s, 'NomuteCloudAction'), 'cloud_action_setup.sh 윈도우 5분 시계(NomuteCloudAction) 등록 소실'),
        (_has_exec_line(s, '환경변수.txt'), 'cloud_action_setup.sh 키 착지 슬롯(환경변수.txt) 씨앗 소실'),
        (_has_exec_line(s, '노뮤트_열쇠입력.html'), 'cloud_action_setup.sh 열쇠 입력 페이지 배포(복사) 소실'),
        (_bat_exec(b, 'git clone'), '설치 bat 자기완결 결손 — 저장소 받기(git clone) 소실'),
        (_bat_exec(b, 'call claude'), '설치 bat 자기완결 결손 — 클로드 로그인 단계 소실(판정 축이 조용히 죽는다)'),
        (_bat_exec(b, 'cloud_action_setup.sh'), '설치 bat 가 설치 뒷단(cloud_action_setup.sh)을 부르지 않는다'),
        (_has_exec_line(c, 'cloud_action_setup.sh'), '설치 command 가 설치 뒷단(cloud_action_setup.sh)을 부르지 않는다'),
        ('_B64=' in h and '환경변수.txt' in h, '열쇠 입력 페이지의 접기(_B64)·저장 이름(환경변수.txt) 소실'),
    ):
        if not cond:
            print(f'❌ [cloud-action] {msg}'); rc = 1
    # 계정값 사본 0 — 설치 뒷단은 겉옷 정본에서 추출해야 한다(두 곳에 적으면 조용히 갈린다)
    if 'ems1130g' in s:
        print('❌ [cloud-action] cloud_action_setup.sh 에 계정값 리터럴 — 정본은 cloud_action.sh ACCOUNT 1곳(추출해 쓴다)'); rc = 1
    return rc


def check_secret_coverage_chain():
    """빈 칸 점검 레인 5층 생존(운영자 260816 «응 해줘» · 계정 이관 후속).
    CONTRACT: check_secret_coverage_chain

    ⚠ 신설 사유 = **이 레인은 한 층만 빠져도 초록으로 끝나면서 아무것도 안 본다.** 등록분을 넘기는 두 줄
    (toJSON) 중 하나만 빠져도 스크립트는 그 종류를 「대조 불가」로 조용히 건너뛰고 rc 0 으로 끝난다 —
    로그는 정상이고 알림도 안 뜨니 「빈 칸 0개」와 「안 본 것」이 화면에서 구분이 안 된다. 그게 정확히
    이 레인이 막으려는 병(비어 있는 칸은 터지기 전까지 증상이 0)의 재현이라 자기 자신부터 게이트가 필요하다.
    기존 게이트는 전부 다른 축 — check_workflow_yaml = 문법 · check_paths = 경로 실존 ·
    check_smoke_obs_chain = 스모크 경보가 사유를 갖고 나가는가 → 「저장소가 쓰는 이름이 실제로 등록됐는가」
    를 보는 레인 자신의 생존은 축이 없었다.

    5축(정적 · 렌더·LLM·네트워크 0 · 면책표 없이 하드 0):
      ① 정본 스크립트 실존 + 골격 심볼(scan_refs·registered·MSG_ID)
      ② 워크플로가 등록분 **두 종류 다** 주입(ALL_SECRETS ∧ ALL_VARS · 한쪽만이면 그 종류가 조용히 미점검)
      ③ 정본 스크립트 실행줄 배선
      ④ 알림 착지 스텝(없으면 러너에서 알림이 증발 = 260816 insta 실사고와 같은 축)
      ⑤ 값 무출력 계약 = 스크립트가 등록분 원문(ALL_SECRETS/ALL_VARS)을 print 하지 않는다
         (⚠ 이 한 줄이 무너지면 점검 도구 자신이 토큰 유출 경로가 된다 = 가장 비싼 회귀)
    """
    import re as _re
    p_py = os.path.join(ROOT, '.github', 'scripts', 'secret_coverage.py')
    p_yml = os.path.join(ROOT, '.github', 'workflows', 'secret-coverage.yml')
    bad = []
    if not os.path.exists(p_py):
        print('❌ 빈 칸 점검 게이트 — 정본 .github/scripts/secret_coverage.py 없음(fail-closed)'); return 1
    if not os.path.exists(p_yml):
        print('❌ 빈 칸 점검 게이트 — 레인 .github/workflows/secret-coverage.yml 없음(fail-closed)'); return 1
    py = open(p_py, encoding='utf-8').read()
    yml = open(p_yml, encoding='utf-8').read()
    # 주석 줄 제외 = 처방문·사고 기록이 배선으로 오인되는 것 차단(check_nm_jobs 관례 계승).
    py_code = '\n'.join(l for l in py.splitlines() if not l.lstrip().startswith('#'))
    yml_code = '\n'.join(l for l in yml.splitlines() if not l.lstrip().startswith('#'))
    for sym in ('def scan_refs', 'def registered', 'MSG_ID'):                      # ①
        if sym not in py_code:
            bad.append(f'정본 골격 심볼 소실: {sym}')
    for inj in ('ALL_SECRETS: ${{ toJSON(secrets) }}', 'ALL_VARS: ${{ toJSON(vars) }}'):   # ②
        if inj not in yml_code:
            bad.append(f'등록분 주입 누락: {inj.split(":")[0]}(그 종류가 조용히 미점검된다)')
    if not _has_exec_line(yml_code, 'secret_coverage.py'):                          # ③
        bad.append('정본 스크립트 실행줄 미배선')
    if 'git_land.sh' not in yml_code or 'messages' not in yml_code:                 # ④
        bad.append('알림 착지 스텝 미배선(러너에서 알림 증발 = 260816 insta 실사고 동축)')
    # ⑤ ⚠ 술어 함정(첫 실행 실측 봉합) = 「print 줄에 ALL_SECRETS 라는 글자가 있나」로 두면
    #    안내 문구(`print('no-op — 등록분 미주입(ALL_SECRETS/ALL_VARS)…')`)가 그대로 위반으로 잡힌다
    #    = 이름을 **말하는 것**과 값을 **찍는 것**을 못 가르는 술어. 값에 닿는 길은 환경변수 읽기뿐이므로
    #    문자열 리터럴을 지운 뒤 남은 코드에서 판정한다(주석 속 예시도 같이 무해해진다).
    for leak in _re.findall(r'print\s*\([^\n]*', py_code):                          # ⑤
        bare = _re.sub(r'"[^"]*"|\'[^\']*\'', '', leak)
        if 'environ' in bare or 'ALL_SECRETS' in bare or 'ALL_VARS' in bare:
            bad.append('값 무출력 계약 위반 — 등록분 원문을 출력하는 줄이 있다(토큰 유출 경로)')
            break
    if bad:
        print('❌ 빈 칸 점검 레인 — 층 결손:')
        for b in bad:
            print('   ·', b)
        return 1
    print('✅ 빈 칸 점검 레인 — 정본·주입 2종·실행·착지·값 무출력 전건 생존(비밀칸·변수 등록 전수 대조).')
    return 0


# ── 화면 주소 정본 ──────────────────────────────────────────────────────────────
_CANON_HOST = 'edit.nomute.kr'          # 260816 계정 이관 정본(CLAUDE.md 레포 전용 절 「지금 정본 4종」 ⓑ)
_OLD_HOSTS = ('apps.nomute.kr',)        # 옛 화면 — 되돌릴 여지로 살려는 두되 코드가 부르면 안 된다
# ── 착지 침묵(초록인데 결과물이 없다) ──────────────────────────────────────────
# 260816 실사고 = stamp-version 이 push 4회 전부 실패했는데 warning 만 남기고 rc 0(초록)으로 끝났다.
# 도장이 main 에 없으니 라이브 도장이 트리거 SHA 로 바뀔 방법이 구조적으로 없고, 그 배포의 라이브 검문은
# 12분 대기 후 반드시 「배포 미수렴」으로 적색이 된다(run 31936404895 = 도장 미착지인데 success →
# run 31936404904 = 그 여파로 검문 적색). 원인이 검문 쪽으로 보여 세션 하나가 통째로 오진했다.
_LAND_RECOVER = ('다음', '회수', '합류', '재판정', '덮', '재수집', '스윕')   # 「유실돼도 **누가** 되돌리는지」를 말한 소진 메시지 = 의도적 fail-soft
# ⚠ '재시도' 는 회수 어휘가 아니다(첫 실행 실측 봉합) — 소진 문구가 하필 「push 실패(재시도 소진)」이라
#    그 낱말을 넣으면 **회수가 끝났다는 말이 회수 약속으로 읽혀** 진짜 조용한 유실 4건이 통째로 통과한다.
_LAND_BASE = {   # 260816 실측 스냅샷 — 회수 경로도 실패 표기도 없이 조용히 끝나는 인라인 착지. 해소하면 그만큼 낮춰라(래칫).
    'imggen.yml': 1,              # 이미지 제작 결과(그림은 R2 직행이라 살지만 완료 신호가 유실되면 화면이 '제작중'에 멈춘다)
    'moreimg.yml': 1,             # 보충 이미지 결과(동축)
    'thumb-redo.yml': 1,          # 썸네일 수정 결과 + 소원 원장
    'news-analyze.yml': 1,        # cards 썸네일(git 이 유일 경로)
    'news-ask.yml': 1,            # cards 썸네일(동축)
    'framethumb-make.yml': 1,     # viewer/ft_out(git 이 유일 경로 = 유실 = 산출 소멸)
    'tiktok-canary.yml': 1,       # sns_trends 관측치(데이터 churn = 다음 회차가 덮지만 그 말을 안 한다)
    'tiktok-subs-canary.yml': 1,  # 동축
}
# ── 착지 내용 소실(올라갔는데 우리 변경이 빈 경우) ────────────────────────────
# ⚠ `git pull --rebase … -X ours` 는 **의미가 반전된다** — 리베이스는 upstream 위에 내 커밋을 다시 얹으므로
#   리베이스 중 ours = **upstream(origin/main)** 이고 theirs = 내 커밋이다. 즉 `-X ours` 는 충돌 시
#   **우리 산출 헝크를 버리고** 원격을 채택하는데 **push 는 성공**한다 = 실패 여부로는 원리적으로 못 보는 유실.
#   이 함정은 저장소가 이미 알고 있다(watchdog.yml 주석 「-X ours = upstream 우선 의미 반전 함정」 ·
#   git_land.sh 헤더 「리베이스가 꼬여 no-op 만 밀고 산출물이 증발」 · 260716 브리프 3일 정지 실사고).
_XOURS_AWARE = ('드랍', '의미 반전', '원격 승', '재병합', 'theirs')   # 그 자리에서 위험을 **인지하고 대처를 적었다**
_XOURS_BASE = {   # 260816 실측 스냅샷 — `-X ours` 인데 드랍 대처가 없는 착지. 해소하면 그만큼 낮춰라(래칫).
    'breaking-judge.yml': 1,       # 자동픽 = pending + seen_urls(append-only) 착지
    'feedback.yml': 1,             # feedback/ (건별 파일 = 충돌 가능성 낮음 · 미판독)
    'moreimg.yml': 1,              # 보충 이미지 결과 파일
    'pick.yml': 1,                 # 운영자 픽 = pending + seen_urls(append-only)
    'rate.yml': 1,                 # ratings·thumb_votes = append-only 원장 = 충돌 시 우리 줄 유실
    'scrape.yml': 3,               # candidates 스냅샷 · 화재 추적 원장 · pending 적재
    'social-scan.yml': 1,          # SNS 레인 스냅샷(다음 30분 회차가 덮는다)
    'tiktok-canary.yml': 1,        # sns_trends = **다른 워크플로도 쓰는 파일** = 충돌 실재
    'tiktok-subs-canary.yml': 1,   # 동축
}


def check_land_xours():
    """착지 내용 소실 래칫 = 「올라갔는데 우리 변경이 빈 경우」(운영자 260816 「ㄱㄱ」 · 페이블 교차검증 지적 ⓒ).
    CONTRACT: check_land_xours

    ⚠ 신설 사유 = **짝 게이트 `check_land_silence` 가 원리적으로 못 보는 축**이다. 그쪽은 「착지에 실패했는데
      초록으로 끝나는가」를 보는데, 여기서는 **push 가 실제로 성공한다** — 다만 그 커밋 안에 우리 산출이 없다.
      리베이스에서 ours/theirs 의미가 뒤집히는 게 원인이라 코드만 봐서는 옳아 보이고, 화면 증상도 0이다
      (실사고 = 260716 insta 브리프 3일 정지 · git_land.sh 헤더가 그 사고를 「no-op 만 밀고 산출물 증발」로 기록).

    술어 = 「main 착지 스텝이 `-X ours` 를 쓰는데, 그 자리에서 **드랍을 인지한 대처**를 안 적었다」.
    ⚠ **획일적 금지가 아니라 인지 요구인 것이 실효 조건** = `-X theirs` 로 뒤집는 건 만능이 아니다.
      그쪽은 **남의 최신 변경을 우리 옛 값으로 조용히 덮는다**(이 저장소도 그 위험을 알아 `news-analyze.yml`
      은 concurrency 그룹으로 직렬화해 「-X theirs 무경고 덮어쓰기」를 막고 있다). 자리마다 옳은 처방이
      다르므로 게이트는 **「알고 골랐는가」**까지만 본다 — 대처 3형 = ⓐ 임시본 재병합(imggen·img-resize·
      img-upscale 실측 정본) ⓑ `-X theirs` 전환 ⓒ 그 자리 주석에 드랍이 무해한 사유 명시.
    ⚠ **하드 0 금지 = 래칫** = 현행 11곳은 전건 미판독이다(append-only 원장은 우리 줄이 그대로 유실되고,
      통째 스냅샷은 다음 회차가 덮어 회복될 수 있는데 그 구분이 아직 실측되지 않았다) — 늘면 차단, 줄면 낮춰라.
    ⚠ 스코프 = `.github/workflows/*.yml` 자동 발견 · 주석 줄 제외 · 정적(렌더·LLM·네트워크 0)."""
    import re as _re
    try:
        import yaml as _yaml
    except Exception:  # noqa: BLE001
        print('⚠️ 착지 내용 소실 래칫 — pyyaml 없음(fail-soft 스킵)'); return 0
    wf_dir = os.path.join(ROOT, '.github', 'workflows')
    if not os.path.isdir(wf_dir):
        print('❌ 착지 내용 소실 래칫 — 워크플로 폴더 없음(fail-closed)'); return 1
    push_re = _re.compile(r'git push[^\n]*(?:HEAD:main|origin main)')
    now, detail = {}, []
    for fn in sorted(os.listdir(wf_dir)):
        if not fn.endswith(('.yml', '.yaml')):
            continue
        try:
            d = _yaml.safe_load(open(os.path.join(wf_dir, fn), encoding='utf-8'))
        except Exception:  # noqa: BLE001
            continue
        for job in (d.get('jobs') or {}).values():
            for st in (job.get('steps') or []):
                run = st.get('run')
                if not run:
                    continue
                code = '\n'.join(l for l in run.splitlines() if not l.lstrip().startswith('#'))
                if '-X ours' not in code or not push_re.search(code):
                    continue
                # ⚠ 대처 판정은 **주석까지 포함한 원문**에서 본다 — 처방이 주석으로 적히는 게 이 레포 관례라
                #    코드부만 보면 「사유를 적어 대처한 자리」가 통째로 위반이 된다(check_land_silence 와
                #    반대 방향의 스코프 = 그쪽은 주석 위장을 막아야 했고 여기는 주석이 곧 대처다).
                if any(w in run for w in _XOURS_AWARE):
                    continue
                now[fn] = now.get(fn, 0) + 1
                detail.append('%s · %s' % (fn, (st.get('name') or '(이름 없음)')[:30]))
    over = {k: v for k, v in now.items() if v > _XOURS_BASE.get(k, 0)}
    if over:
        print('❌ 착지 내용 소실 래칫 — `-X ours` 착지가 늘었다(push 는 성공하는데 우리 변경이 버려질 수 있다):')
        for k in sorted(over):
            print('   · %s: %d건 > 면책 %d건' % (k, over[k], _XOURS_BASE.get(k, 0)))
        for d0 in detail[:10]:
            print('     -', d0)
        print('   → 리베이스에서 ours = **upstream** 이다(의미 반전) — 충돌 시 우리 헝크가 버려지는데 push 는 성공한다.')
        print('   → 처방 3형 = ⓐ 임시본 재병합(imggen 계열 정본) ⓑ `-X theirs` 전환(단 남의 최신을 덮을 위험 동반) ⓒ 그 자리에 드랍이 무해한 사유를 적어라.')
        return 1
    gone = {k: v for k, v in _XOURS_BASE.items() if now.get(k, 0) < v}
    if gone:
        print('✅ 착지 내용 소실 래칫 — 해소분 %d파일 → _XOURS_BASE 를 그 자리에서 낮춰라: %s'
              % (len(gone), ', '.join('%s %d→%d' % (k, v, now.get(k, 0)) for k, v in sorted(gone.items()))))
        return 0
    print('✅ 착지 내용 소실 래칫 — 대처 없는 `-X ours` 착지 %d건 = 면책 스냅샷과 동일(증가 0 · 대처 3형[재병합·theirs 전환·사유 명시] 인정).'
          % sum(now.values()))
    return 0





def check_land_silence():
    """착지 침묵 래칫 = 「본선에 올리는 데 실패했는데 초록으로 끝나는」 자리를 센다(운영자 260816 「조치해줘」).
    CONTRACT: check_land_silence

    ⚠ 신설 사유 = **이 레포 게이트 120개가 전부 「최종 상태가 옳은가」만 본다** — 정적 문자열·화면 렌더·값 대조.
      「작업이 성공이라고 말하는데 결과물이 실제로 본선에 있는가」는 축 자체가 없었다. 그 틈에서 260816 하루에
      같은 모양이 세 번 났다(검문이 옛 화면을 봄 · 봉합이 형제를 빼먹음 · 도장 착지가 4회 전부 죽음) —
      셋 다 **화면 증상 0 · 로그는 초록**이라 운영자 눈이 유일한 검출기였다(insta-thumb-miss·brk_misfire 동축).

    술어 = 「워크플로 스텝이 **인라인으로** main 에 직접 푸시하는데, 재시도 소진 뒤
      ⓐ 실패로 끝내지도(rc≠0) ⓑ 회수 경로를 말하지도 않는다」 → 조용한 유실.
    ⚠ **인라인만 대상인 것이 실효 조건** = `git_land.sh` 위임은 그 헬퍼 헤더가 「rc: 항상 0(fail-soft)」를
      **명문으로 선언**한 축이다(데이터 churn = 다음 회차가 재수집). 직접 푸시 루프를 손으로 짰다는 건
      「이 산출물은 내가 책임진다」는 뜻이라 성격이 다르다 — 그 둘은 이미 코드 모양으로 갈려 있으므로
      손 목록 없이 구조적으로 나뉜다(손 목록은 새 워크플로가 조용히 빠진다 = 이 레포 최빈 드리프트).
    ⚠ **회수 경로 면제** = 소진 메시지가 「다음 회차에 합류」·「다음 런이 재판정」처럼 **누가 되돌리는지**를
      말하면 의도적 fail-soft 다(실측 4건 = breaking-judge 최종 커밋 회수 · live-smoke 원장 재판정 ·
      pending-sweep 다음 스윕 · run-steps-ledger 다음 회차 합류). 말하지 않으면 유실이 그냥 사라진다.
    ⚠ **하드 0 금지 = 래칫이 정확한 형태** = 현행 8건은 전건 **미판독**이다. 케이스별로 보지 않고 하드로 올리면
      「알고 동결한 부채」가 「원래 그런 것」으로 굳거나(baseline 남용) 레포가 언다 — check_layout_transition·
      check_css_dead_state 선례. **늘면 차단 · 줄면 낮추라고 알린다**(새 워크플로가 조용히 빠질 수 없다 = 목적).
    ⚠ 스코프 = `.github/workflows/*.yml` 자동 발견 · 주석 줄 제외 · 정적(렌더·LLM·네트워크 0)."""
    import re as _re
    try:
        import yaml as _yaml
    except Exception:  # noqa: BLE001
        print('⚠️ 착지 침묵 래칫 — pyyaml 없음(fail-soft 스킵)'); return 0
    wf_dir = os.path.join(ROOT, '.github', 'workflows')
    if not os.path.isdir(wf_dir):
        print('❌ 착지 침묵 래칫 — 워크플로 폴더 없음(fail-closed)'); return 1
    push_re = _re.compile(r'git push[^\n]*(?:HEAD:main|origin main)')
    now, detail = {}, []
    for fn in sorted(os.listdir(wf_dir)):
        if not fn.endswith(('.yml', '.yaml')):
            continue
        try:
            d = _yaml.safe_load(open(os.path.join(wf_dir, fn), encoding='utf-8'))
        except Exception:  # noqa: BLE001
            continue
        for job in (d.get('jobs') or {}).values():
            for st in (job.get('steps') or []):
                run = st.get('run')
                if not run:
                    continue
                code = '\n'.join(l for l in run.splitlines() if not l.lstrip().startswith('#'))
                # ⚠ 위임 판정은 **실행줄**로 본다(4차 봉합 · 페이블 교차검증) — 단순 포함으로 두면
                #   `PFX=… # 정본 = git_land.sh 헤더` 같은 **줄 끝 주석**이 면죄부가 된다(실측 진범 =
                #   social-scan.yml = 루프 뒤가 통째로 비어 판정도 경고도 0인데 그 주석 하나로 통과했다).
                if _has_exec_line(code, 'git_land.sh'):   # 위임 = fail-soft 계약 명문 축 = 대상 밖
                    continue
                if not push_re.search(code):
                    continue
                # ⚠⚠ 판정도 **루프가 끝난 뒤**에서만 본다(260816 2차 봉합 · 페이블 교차검증이 잡은 구멍) —
                #    코드 전체에서 `exit 1` 을 찾으면 **그 스텝의 다른 분기** 판정이 착지 판정으로 오인된다.
                #    실측 진범 = pick.yml 착지 루프(100~105)는 4회 다 실패해도 경고조차 없이 그냥 다음 줄로
                #    떨어지는데, 11줄 아래 111행의 `exit 1` 은 **디스패치 실패** 판정이라 착지와 무관하다.
                #    첫 판은 그 줄을 보고 통과시켰다 = 회수 어휘 함정과 정확히 같은 축(범위를 안 좁힌 것).
                #    ⚠⚠ 그리고 「루프 뒤」는 **마지막 done 뒤가 아니라 그 푸시 루프의 done 뒤**다(3차 봉합) —
                #    pick.yml 은 착지 루프 다음에 **디스패치 루프**가 또 있어서 마지막 done 으로 자르면
                #    그 디스패치 판정(`exit 1`)이 다시 착지 판정으로 오인된다(2차 봉합이 같은 자리에서 또 샜다).
                #    → 푸시가 있는 자리부터 그 루프의 첫 `done` 을 찾고, 다음 루프가 열리기 전까지만 본다.
                m = push_re.search(code)
                seg = code[m.end():] if m else code
                d = _re.search(r'^\s*done\b', seg, _re.M)
                tail = seg[d.end():] if d else seg
                #    ⚠ 다음 루프 판정은 **줄 머리로 두면 안 된다**(3차 봉합 실측) — pick.yml 은
                #    `ok=0; for i in 1 2 3; do` 처럼 같은 줄에 대입을 먼저 쓰므로 `^\s*for` 가 못 잡는다.
                nxt = _re.search(r'\b(?:for|while)\b[^\n]*\bdo\b', tail)
                if nxt:
                    tail = tail[:nxt.start()]
                if _re.search(r'exit\s+1', tail):    # 소진 뒤 실패를 실패로 낸다 = 통과
                    continue
                # ⚠ 회수 판정도 같은 범위(루프 뒤) — 루프 **안**의 「push 재시도 $i」는 회수 경로가 아니라
                #    그냥 다음 라운드 표시인데, 전체 코드에서 어휘만 찾으면 그 한 줄이 면죄부가 돼
                #    진짜 조용한 유실 4건이 통째로 통과했다(첫 실행 실측 봉합).
                if any(w in tail for w in _LAND_RECOVER):   # 소진 뒤 「누가 되돌리는지」를 말한다 = 의도적 fail-soft
                    continue
                now[fn] = now.get(fn, 0) + 1
                detail.append('%s · %s' % (fn, (st.get('name') or '(이름 없음)')[:30]))
    over = {k: v for k, v in now.items() if v > _LAND_BASE.get(k, 0)}
    if over:
        print('❌ 착지 침묵 래칫 — 본선 착지에 실패해도 초록으로 끝나는 자리가 늘었다(조용한 유실):')
        for k in sorted(over):
            print('   · %s: %d건 > 면책 %d건' % (k, over[k], _LAND_BASE.get(k, 0)))
        for d0 in detail[:10]:
            print('     -', d0)
        print('   → 처방 = 재시도 소진 시 `exit 1`(실패를 실패로 낸다) 또는 소진 메시지에 **누가 회수하는지**를 적어라.')
        print('   → 데이터 churn 이라 다음 회차가 덮는 축이면 git_land.sh 위임이 정본이다(그쪽은 fail-soft 계약 명문).')
        return 1
    gone = {k: v for k, v in _LAND_BASE.items() if now.get(k, 0) < v}
    if gone:
        print('✅ 착지 침묵 래칫 — 해소분 %d파일 → _LAND_BASE 를 그 자리에서 낮춰라(남겨두면 같은 회귀가 조용히 재통과): %s'
              % (len(gone), ', '.join('%s %d→%d' % (k, v, now.get(k, 0)) for k, v in sorted(gone.items()))))
        return 0
    print('✅ 착지 침묵 래칫 — 조용한 유실 %d건 = 면책 스냅샷과 동일(증가 0 · 인라인 착지만 대상 · git_land 위임은 fail-soft 계약 축).'
          % sum(now.values()))
    return 0



_CANON_EXT = ('.py', '.js', '.mjs', '.sh', '.command', '.yml', '.yaml', '.html', '.css', '.bat', '.ps1')
_CANON_SKIP_DIRS = ('_versions/', 'docs/', 'cards/', '.claude/', 'queue/', 'scraper/obs/')


def _canon_mask_comments(text, ext):
    """주석 구간을 길이 보존 공백으로 지운다 — 인덱스가 원본과 1:1 유지돼야 행 번호가 안 어긋난다
    (css_hoist 「길이 보존 공백 마스킹」 관례 계승 · 260807 실측에서 이 보존을 깨면 제거 범위가 밀렸다)."""
    import re as _re

    def blank(m):
        return _re.sub(r'[^\n]', ' ', m.group(0))

    if ext == '.html':
        text = _re.sub(r'<!--[\s\S]*?-->', blank, text)
        text = _re.sub(r'/\*[\s\S]*?\*/', blank, text)
        text = _re.sub(r'(?<!:)//[^\n]*', blank, text)
    elif ext in ('.js', '.mjs', '.css'):
        text = _re.sub(r'/\*[\s\S]*?\*/', blank, text)
        if ext != '.css':
            text = _re.sub(r'(?<!:)//[^\n]*', blank, text)
    elif ext in ('.py', '.sh', '.command', '.yml', '.yaml', '.ps1'):
        text = _re.sub(r'#[^\n]*', blank, text)
    elif ext == '.bat':
        text = _re.sub(r'(?im)^[ \t]*(?:rem|::)[^\n]*', blank, text)
    return text


def check_canon_host():
    """화면 주소 정본 = 코드가 옛 화면을 직접 부르지 않는다(운영자 260816 「게이트 ㄱㄱ」).
    CONTRACT: check_canon_host

    ⚠ 신설 사유 = **260816 계정 이관에서 화면만 새 주소로 갔고, 그 화면을 부르는 코드는 여러 곳이
    따라오지 않았는데 전부 화면 증상이 0이었다.** 실사고 2종 =
      ⓐ 배포 검문(live-smoke)이 옛 화면 도장을 읽어 코드 푸시마다 「배포 미수렴」 거짓 실패
         (실측 260815 23:40 · 260816 04:26 · 07:00 3연속 적색 · 검문 자신은 그 판에서도 전부 초록이었다
          = 화면은 멀쩡한데 **보는 곳이 틀린** 사고라 로그만 봐서는 원인이 안 보인다).
      ⓑ 그 봉합 커밋(961d3826)이 **형제 4곳을 빼먹었다** — 맥 잡 실행기 3종은 옛 화면으로 작업을
         재접수해 그 잡이 옛 계정 저장소로 새고(증상 = 아무 일도 안 일어남), 공유 미리보기 그림
         2줄은 옛 화면에서 끌어와 옛 계정 정리 시점에 카톡·X 미리보기가 통째로 깨질 예정이었다
         (양쪽 200 실측이라 지금은 무증상 = 터지기 전까지 아무도 모른다).
    기존 게이트는 전부 다른 축 — check_paths = 경로 실존 · check_workflow_yaml = 문법 ·
    check_seal_completeness = 「같은 병의 형제」인데 **WARN 이라 ⓑ를 못 막았다** · smoke_* = 화면 렌더
    → 「코드가 부르는 우리 화면 주소가 정본인가」는 축 자체가 없었고 운영자 눈이 유일한 검출기였다
    (insta-thumb-miss·brk_misfire 동축).

    술어 = **스킴이 붙은 절대 주소만** 위반(https://apps.nomute.kr).
      ⚠ 이 한 줄이 실효 조건 = 스킴 유무가 「부르는 곳」과 「비교하는 곳」을 정확히 가른다.
        스킴 없는 호스트 문자열은 전부 **옛 화면을 살려두려고 일부러 남긴 것**이라 대상 밖 —
        요청 출처 허용 목록(functions/api/*.js originOk 5곳) · 서비스워커 CANON_HOSTS ·
        배포 환경변수 폴백(functions/_middleware.js) · 이관 도구 상수(scripts/migrate_account.sh).
        손 면책 목록을 들면 새 파일이 조용히 빠지는데(이 레포가 반복해 겪은 드리프트) 이 술어는
        구조적으로 갈리므로 **면책표가 아예 없다** = 부채 원장 증가 0.

    판정 = 정적(렌더·LLM·네트워크 0) · 표면 자동 발견(git ls-files = 새 파일이 조용히 못 빠진다) ·
      주석 마스킹(사고 기록의 거처 = 주석 · 길이 보존이라 행 번호 정확) · **면책표 없이 하드 0**.
    ⚠ 스코프 밖 = _versions·docs·cards·.claude(스냅샷·산출 자산) · queue·scraper/obs(기계산출물) ·
      shared/check_refs.py 자신(처방문의 「수정 전」 예시가 곧 위반 문자열 = check_ytdlp_aac 선례).
    """
    import re as _re
    import subprocess as _sp
    try:
        out = _sp.run(['git', 'ls-files', '-z'], cwd=ROOT, capture_output=True, text=True, timeout=60)
        files = [f for f in out.stdout.split('\0') if f]
    except Exception as e:
        print('⚠️ 화면 주소 정본 게이트 — 파일 목록을 못 얻었다(fail-soft):', e); return 0
    pat = _re.compile(r'https?://(?:%s)' % '|'.join(_re.escape(h) for h in _OLD_HOSTS))
    bad = []
    for rel in files:
        if not rel.endswith(_CANON_EXT):
            continue
        if any(rel.startswith(d) for d in _CANON_SKIP_DIRS):
            continue
        if rel.replace('\\', '/') == 'shared/check_refs.py':
            continue
        ap = os.path.join(ROOT, rel)
        try:
            raw = open(ap, encoding='utf-8', errors='replace').read()
        except Exception:
            continue
        if not pat.search(raw):
            continue
        ext = os.path.splitext(rel)[1].lower()
        masked = _canon_mask_comments(raw, ext)
        for m in pat.finditer(masked):
            ln = masked.count('\n', 0, m.start()) + 1
            bad.append('%s:%d — %s' % (rel, ln, m.group(0)))
    if bad:
        print('❌ 화면 주소 정본 게이트 — 코드가 옛 화면을 직접 부른다(정본 = %s):' % _CANON_HOST)
        for b in bad[:20]:
            print('   ·', b)
        if len(bad) > 20:
            print('   · … 외 %d건' % (len(bad) - 20))
        print('   처방 = 새 주소로 바꾸되 갈아끼울 손잡이를 둔다(셸 = "${LIVE_BASE:-https://%s}" · 파이썬 = os.environ.get("LIVE_BASE") or "https://%s").' % (_CANON_HOST, _CANON_HOST))
        print('   ⚠ 호스트 **비교**(요청 출처 허용 목록·CANON_HOSTS·환경변수 폴백·이관 도구 상수)는 스킴이 없으므로 이 게이트 대상이 아니다 — 그건 그대로 둬라.')
        return 1
    print('✅ 화면 주소 정본 게이트 — 코드가 부르는 화면 주소 전건 %s(옛 화면 절대주소 0 · 호스트 비교는 대상 밖 · 면책표 없음).' % _CANON_HOST)
    return 0



def check_pc_lane_stages():
    """액션 대체 레인의 스테이지 생존(운영자 260814 «깃허브 액션 없이도 정상 가동 모든 웹앱 내 기능이 돌도록»).
    ⚠ 신설 사유 = **한 스테이지가 빠져도 화면 증상이 0이다** — 레인은 매 회차 초록으로 끝나고 수집함도 계속
    늘어나는데, 빠진 축(재난문자·트렌드·SNS·채널·감시·계측·요약)만 조용히 정지한다. 260814 이전 레인이 정확히
    그 상태였고(수집·판정 2스텝뿐) 운영자 눈이 유일한 검출기였다(insta-thumb-miss·brk_misfire 동축).
    기존 게이트는 전부 다른 축 — check_cloud_action_chain = **시계·드라이브·열쇠 배선**(레인 바깥 껍데기) ·
    check_workflow_amend·check_pages_skip = 워크플로 축 → 「그 레인이 **무슨 일을 하는가**」는 축이 없었다.
    정적 · 렌더·LLM·네트워크 0 · 면책표 없이 하드 0. 축 =
    ① 착지 = git_land 위임(구판 자체 리베이스 루프 부활 차단 — 260814 실측 push-fail 의 진범)
    ② 형제 전건 -X theirs(phone_scrape·phone_subs — 하나만 고치면 나머지가 조용히 낡는다 = 이 레포 최빈 사고)
    ③ 안 밀린 커밋 보호(git_land 의 reset --hard 가 방금 만든 요약을 지우는 자리 = 가장 비싼 조용한 유실)
    ④ 스테이지 실행줄 실존 8종 ⑤ 요약 스테이지가 데이터 스테이지보다 **뒤**(자리가 계약 = ③의 짝)."""
    rc = 0
    paths = {k: os.path.join(ROOT, 'scripts', v) for k, v in (
        ('lane', 'pc_lane.sh'), ('ph', 'phone_scrape.sh'), ('ps', 'phone_subs.sh'))}
    txt = {}
    for k, p in paths.items():
        if not os.path.exists(p):
            print('❌ [pc-lane] 파일 소실: %s' % os.path.relpath(p, ROOT)); return 1
        with open(p, encoding='utf-8', errors='replace') as f:
            txt[k] = f.read()
    lane = txt['lane']
    # ① 착지 위임 + 구판 부활 차단
    if not _has_exec_line(lane, 'git_land.sh'):
        print('❌ [pc-lane] 착지가 git_land.sh 위임이 아니다 — 자체 리베이스 루프는 폰 레인과 같은 파일을 물면 그 회차 산출을 통째로 버린다(260814 실측)'); rc = 1
    # ② 세 레인 전건 -X theirs(형제 봉합) + ③ 안 밀린 커밋 보호
    for k, nm in (('ph', 'phone_scrape.sh'), ('ps', 'phone_subs.sh')):
        if not _has_exec_line(txt[k], 'rebase -q -X theirs origin/main'):
            print('❌ [pc-lane] %s 리베이스 충돌 봉합(-X theirs) 소실 — 같은 병의 형제를 한쪽만 고치면 그쪽만 조용히 낡는다' % nm); rc = 1
    # ⚠ 판정은 **착지 함수 몸통 안**에서 본다 — 파일 어딘가에 같은 문자열이 있으면 통과하게 두면 자가복구
    #   블록의 `rev-list` 한 줄이 면죄부가 된다(킬테스트 K3 실측 = 보호를 통째로 지웠는데 rc=0 으로 통과).
    _body, _in = [], False
    for ln in lane.split('\n'):
        if not _in and ln.startswith('_gl(){'):
            _in = True; _body.append(ln); continue
        if _in:
            if ln.startswith('}'):
                break
            _body.append(ln)
    _body = '\n'.join(_body)
    if not (_body and 'rev-list --count origin/main..HEAD' in _body and 'return 1' in _body):
        print('❌ [pc-lane] 안 밀린 커밋 보호 소실 — git_land 의 reset --hard 가 방금 만든 요약 커밋을 지운다(착지 함수 _gl 몸통 축)'); rc = 1
    # ③-b 자기 갱신 안전 — 세 레인 전건이 **자기 자신을 바꾸는 git pull 을 자기 실행 도중**에 돌린다.
    #   셸은 파일 바이트 위치를 기억하며 조금씩 읽으므로 길이가 바뀌면 남은 절반을 엉뚱한 자리부터 읽는다
    #   (= 문법 오류·반쪽 실행 · 레인이 커질수록 확률이 오른다) → 재시작 블록이 형제 전건에 있어야 한다.
    for k, nm in (('lane', 'pc_lane.sh'), ('ph', 'phone_scrape.sh'), ('ps', 'phone_subs.sh')):
        if not (_has_exec_line(txt[k], '_SELF_SUM') and _has_exec_line(txt[k], 'NOMUTE_LANE_REEXEC=1 exec bash')):
            print('❌ [pc-lane] %s 자기 갱신 안전(재시작 블록) 소실 — git pull 이 실행 중인 자기 파일을 바꾸면 남은 절반이 깨진다' % nm); rc = 1
    # ④ 스테이지 실행줄(대응 워크플로 = 주석에 명기) — 이름이 아니라 **실제로 부르는 실행기**로 판정한다
    stages = (
        ('재난·트렌드(sns-trends)', 'scraper/sns_trends.py'),
        ('키워드 폰 알림(sns-trends)', 'kw_watch.py'),
        ('화재 후속 추적(scrape)', 'scraper/fire_watch.py'),
        ('커뮤니티 급상승(social-scan)', 'scraper/social_burst.py'),
        ('채널 수집(insta-fetch·fb-fetch)', 'insta_fetch.py'),
        ('감시(watchdog)', 'scraper/watchdog.py'),
        ('토큰 계측(metrics-rollup)', 'shared/token_report.py'),
        ('쿠키 검진(yt-cookie-health)', 'yt_cookie_health.py'),
        ('요약 분석(news-analyze)', 'analyze.sh'),
        ('요약요청(news-ask)', 'ask.sh'),
        ('썸네일(news-analyze thumb)', 'thumb_gen.py'),
    )
    for nm, needle in stages:
        if not _has_exec_line(lane, needle):
            print('❌ [pc-lane] 스테이지 소실: %s — 레인은 초록으로 끝나는데 그 축만 조용히 정지한다' % nm); rc = 1
    # ⑤ 자리가 계약 — 요약(analyze.sh)은 데이터 스테이지 뒤에 온다(앞에 두면 뒤 착지의 reset --hard 사정권)
    def _pos(needle):
        for i, ln in enumerate(lane.split('\n')):
            st = ln.strip()
            if st and not st.startswith('#') and needle in st.split('#')[0]:
                return i
        return -1
    p_an, p_wd = _pos('analyze.sh'), _pos('scraper/watchdog.py')
    if p_an >= 0 and p_wd >= 0 and p_an < p_wd:
        print('❌ [pc-lane] 요약(analyze.sh)이 데이터 스테이지보다 앞에 있다 — 뒤 착지의 reset --hard 가 아직 안 밀린 요약 커밋을 지운다(자리가 계약)'); rc = 1
    if rc == 0:
        print('✅ [pc-lane] 액션 대체 레인 — 착지 위임·형제 -X theirs·커밋 보호·스테이지 11종·요약 자리 전건 생존.')
    return rc


def _has_exec_line(text, needle):
    """`needle` 이 **주석이 아닌 실행줄**에 있는가. 평문 substring 은 `# python3 x.py` 처럼 주석 처리해도
    통과한다(check_refs 자신이 명시한 self-match 함정).
    ⚠️ `^[ \\t]*(?!#)[^\\n]*needle` 정규식도 **못 막는다** — `[ \\t]*` 가 들여쓰기를 한 칸 덜 먹고 백트래킹하면
       `(?!#)` 가 공백에서 통과하고 `[^\\n]*` 가 `# ` 를 삼켜 그대로 매치된다(260805 킬테스트 K1 실측 —
       기존 brk_misfire·srcimg 게이트가 전부 이 구멍을 갖고 있었다). 줄 단위 판정만이 확실하다."""
    for ln in text.split('\n'):
        st = ln.strip()
        if st and not st.startswith('#') and needle in st.split('#')[0]:
            return True
    return False


def check_grade_fix_chain():
    """grade 수기 교정 폐루프 게이트(하드 · 운영자 260807 "어긋났을 때 고칠 수 있게 · 12시간마다 고쳐진 것만 기록" —
    check_thumb_vote_chain의 짝). 교정은 두 방식으로 조용히 죽는다: ⓐ 적재는 되는데 커밋 줄이 없어 다음 체크아웃서
    증발 ⓑ 쌓이는데 아무도 안 읽는 죽은 원장. 화면은 둘 다 멀쩡해 보인다(칩이 눌리고 초록이 켜진다) → 5층 정적 생존 강제.
    체인: 뷰어 .sc-grade 칩 → askGrade → postRate(action='grade') → rate.yml → rate_record.py(grade 분기)
    → scraper/grade_votes.jsonl → grade_fix_report.py(12h 스윕 · rate.yml+watchdog 동행) → grade_fix_reports.jsonl 내부 축적(260808 알림 제거)."""
    rc = 0
    try:
        vw = open(os.path.join(ROOT, 'viewer', 'index.html'), encoding='utf-8').read()
        rr = open(os.path.join(ROOT, '.github', 'scripts', 'rate_record.py'), encoding='utf-8').read()
        ry = open(os.path.join(ROOT, '.github', 'workflows', 'rate.yml'), encoding='utf-8').read()
        wd = open(os.path.join(ROOT, '.github', 'workflows', 'watchdog.yml'), encoding='utf-8').read()
        rp = open(os.path.join(ROOT, 'scraper', 'grade_fix_report.py'), encoding='utf-8').read()
    except Exception as e:
        print('❌ grade 교정 체인 게이트 — 층 파일 결손:', e)
        return 1
    checks = [
        ('① 뷰어 grade 칩', all(k in vw for k in ('class="sc-grade', 'function askGrade', "action: 'grade'", 'GFIX_KEY'))),
        ('② rate_record grade 분기', '"grade"' in rr and 'grade_votes.jsonl' in rr),
        ('③ rate.yml 원장 커밋+소비', _has_exec_line(ry, 'git add scraper/grade_votes.jsonl') and _has_exec_line(ry, 'scraper/grade_fix_report.py')),
        ('④ watchdog 12h 주기 보장', _has_exec_line(wd, 'scraper/grade_fix_report.py') and _has_exec_line(wd, 'git add scraper/grade_fix_report.json')),
        ('⑤ 소비기 골격(주기·축적·커서)', all(k in rp for k in ('SWEEP_H', 'grade_fix_reports.jsonl', '"seen"', 'build_round'))),   # 260808 개정 = 알림 발화 축 제거 → 내부 축적 원장(REPORTS) 실존이 생존 조건
    ]
    for name, ok in checks:
        if not ok:
            print('❌ grade 교정 체인 게이트 — %s 결손(한 층만 빠져도 교정이 조용히 죽는 원장이 된다)' % name)
            rc = 1
    if rc == 0:
        print('✅ grade 교정 체인 게이트 — 5층(뷰어 칩→분기→커밋→12h 스윕→내부 축적) 전 층 생존.')
    return rc
_SEAL_SKIP_DIR = ('_versions/', 'docs/', 'cards/', '.claude/', 'node_modules/', 'scraper/obs/')
_SEAL_SKIP_FILE = ('shared/check_refs.py',)   # 자기참조(이 게이트의 처방문·정규식이 곧 심볼로 읽힌다 · check_ytdlp_aac 선례)
_SEAL_EXT = ('.py', '.js', '.sh', '.mjs')     # 텍스트 소스만(html = 1.85MB 셸이 섞여 심볼 잡음이 크다 · 축소 지향)
_SEAL_FAM_MIN = 5          # 가족이 이만큼은 돼야 「다수가 쓰는 문법」이라는 말이 성립
# ⚠ 260816 하드 승격(운영자 「ㄱㄱ」) — 구판 값은 0.70/3(WARN)이었다. 그 폭이 넓어 정당한 단독 도입이
#   섞이니 차단으로 못 올렸고, **그래서 260816 계정 이관의 반쪽 봉합 5곳을 경고만 하고 통과시켰다.**
#   실측(최근 60커밋 재생 · 그 커밋 시점 트리로 대조) = 0.70/3 은 2건인데 **전건 위양성**(`int(` 같은
#   내장 함수가 가족 대다수에 있으니 자동으로 다수결을 통과한다) · 0.90/2 는 **0건** · 0.95/1 도 0건.
#   좁혀도 진짜는 잡는다 = 260807 크로미엄 사고 재현에서 여전히 검출(가족 29 · 미보유 2 · 비율 0.93).
_SEAL_HAVE_RATIO = 0.90    # 가족의 이 비율 이상이 이미 가졌으면 = 사실상 표준 문법
_SEAL_MISS_MAX = 2         # 미보유가 이보다 많으면 = 아직 이관 중인 문법(=봉합 누락이 아니다) → 침묵
_SEAL_OK = 'seal-ok'       # 탈출구 = 그 줄에 사유와 함께 달면 그 줄 심볼은 비대상(`q-ok` 관례 계승)
_SEAL_SYM_CAP = 40         # 파일당 심볼 상한(성능 · 대형 diff 폭주 차단)


def _seal_family(rel, tracked):
    """이 파일의 '형제 집합' = 같은 디렉터리·같은 확장자 · 접두(`smoke_`)를 공유하면 그 부분집합으로 좁힌다."""
    d, base = os.path.dirname(rel), os.path.basename(rel)
    ext = os.path.splitext(base)[1]
    same = [f for f in tracked if os.path.dirname(f) == d and f.endswith(ext) and f != rel]
    if '_' in base:
        pre = base.split('_')[0] + '_'
        sub = [f for f in same if os.path.basename(f).startswith(pre)]
        if len(sub) + 1 >= _SEAL_FAM_MIN:
            return sub, d + '/' + pre + '*' + ext
    return same, d + '/*' + ext


def _seal_symbols(added):
    """추가된 줄에서 '공유 문법이 될 수 있는 것'만 뽑는다 = 함수 호출 · 대문자 상수 · 문자열 리터럴 앞조각."""
    syms = set()
    for ln in added:
        s = ln.strip()
        if not s or s.startswith(('#', '//', '*', '/*')):
            continue   # 주석 줄 = 비대상(주석 처리 우회·처방문 인용 차단)
        if _SEAL_OK in s:
            continue   # 정당한 단독 도입 = 그 줄에 사유와 함께 표식(하드 승격의 탈출구 · 260816)
        for m in re.finditer(r'\b([A-Za-z_][A-Za-z0-9_]{2,})\s*\(', s):
            syms.add(m.group(1) + '(')
        for m in re.finditer(r'\b([A-Z][A-Z0-9_]{3,})\b', s):
            syms.add(m.group(1))
        for m in re.finditer(r'''(['"])((?:\\.|(?!\1).){8,120})\1''', s):
            frag = re.sub(r'\\[nt]', ' ', m.group(2)).strip()[:14].strip()
            if len(frag) >= 8:
                syms.add(frag)
    return syms


def check_seal_completeness():
    """봉합 완결성(WARN·비차단 · 운영자 260808 "idea go") — **「같은 병의 형제를 놓쳤나」를 커밋 그 자리에서 센다.**

    ⚠️ 신설 사유 = **260808 하루에 같은 모양의 사고가 두 건 드러났고, 둘 다 봉합 커밋이 형제를 빼먹은 것이었다.**
       ⓐ 260807 크로미엄 경로 봉합이 `smoke_wip` 한 종만 고쳤다 — 그 커밋 주석은 「형제 23종은 전부 which
          폴백 보유 = **이 한 종만** 갈렸다」고 단언했지만 실측은 2종(`smoke_photoflow` 잔여)이라, 봉합
          **다음** 나이틀리도 그대로 붉었다(8일 연속 실패의 마지막 하루가 순전히 이것 때문이었다).
       ⓑ 260728 알림 조치주체 봉합이 `wd-phone` 한 종만 고쳤다 — `yt-cookie-dead`·`fire-*` 생산자는
          안 따라와, 코드로 못 고치는 건과 완료 보고가 「클로드가 볼 일」 칸에 6주간 앉아 진짜 코드 건을 가렸다.
    ⚠️ **이 레포 게이트 102개가 전부 「최종 상태가 옳은가」만 본다** — 정적 문자열·화면 렌더·값 대조 →
       「**방금 한 수정이 완결됐는가**」는 축 자체가 없었다. 그래서 반쪽 봉합이 rc=0으로 통과하고,
       남은 절반은 다음 사고가 터질 때까지 무증상으로 산다(insta-thumb-miss·brk_misfire 동축).

    술어 = 「이번 커밋이 파일 F에 심볼 S를 **추가**했는데, F의 형제 가족 중 **압도적 다수**(≥70%)가 S를
       이미 갖고 있고 **소수**(≤3)만 없다」 → 그 소수를 이름으로 지목한다. 어제 이 게이트가 있었다면
       wip 봉합 커밋이 곧바로 「같은 문법 미보유: shared/smoke_photoflow.js」를 띄웠고 오늘 이 세션은 필요 없었다.
    ⚠️ **다수결이 실효 조건** = 「먼저 고친 쪽이 소수」인 시점엔 그게 표준인지 기계가 알 방법이 없다
       (260728 당시 👉 보유는 1종뿐 = 정당하게 침묵). 표준이 굳은 **뒤에** 새 형제가 빠지면 그때 잡는다.
    ⚠️ **WARN·비차단이 정확한 역할** = 정당한 단독 도입(그 파일에만 필요한 헬퍼)이 섞이므로 하드면 레포가
       언다(check_component_lock·check_gate_hits 선례). 판정은 사람이 하고, 게이트는 **보이게만** 한다.
    ⚠️ 전 경로 fail-soft — git 없음·초기 커밋·diff 실패가 게이트를 못 죽인다."""
    try:
        staged = subprocess.run(['git', 'diff', '--cached', '--name-only', '--diff-filter=ACM'],
                                cwd=ROOT, capture_output=True, text=True, timeout=30)
        if staged.returncode != 0:
            return 0
        files = [f for f in (staged.stdout or '').splitlines()
                 if f.endswith(_SEAL_EXT) and f not in _SEAL_SKIP_FILE
                 and not any(f.startswith(d) for d in _SEAL_SKIP_DIR)]
        if not files:
            return 0
        tracked = [f for f in subprocess.run(['git', 'ls-files'], cwd=ROOT, capture_output=True,
                                             text=True, timeout=60).stdout.splitlines()
                   if f.endswith(_SEAL_EXT) and f not in _SEAL_SKIP_FILE
                   and not any(f.startswith(d) for d in _SEAL_SKIP_DIR)]
    except Exception:  # noqa: BLE001
        return 0
    cache, hits = {}, []
    for rel in files[:20]:
        try:
            d = subprocess.run(['git', 'diff', '--cached', '-U0', '--', rel],
                               cwd=ROOT, capture_output=True, text=True, timeout=30).stdout
        except Exception:  # noqa: BLE001
            continue
        added = [ln[1:] for ln in d.splitlines() if ln.startswith('+') and not ln.startswith('+++')]
        if not added:
            continue
        fam, label = _seal_family(rel, tracked)
        if len(fam) + 1 < _SEAL_FAM_MIN:
            continue
        for sym in sorted(_seal_symbols(added))[:_SEAL_SYM_CAP]:
            probe = sym[:-1] + '(' if sym.endswith('(') else sym
            miss, have = [], 0
            for f in fam:
                if f not in cache:
                    try:
                        cache[f] = open(os.path.join(ROOT, f), encoding='utf-8', errors='replace').read()
                    except OSError:
                        cache[f] = ''
                if probe in cache[f]:
                    have += 1
                else:
                    miss.append(f)
            if not miss or len(miss) > _SEAL_MISS_MAX:
                continue
            if have / float(len(fam)) >= _SEAL_HAVE_RATIO:
                hits.append((rel, sym, label, len(fam), miss))
    if hits:
        print('❌ 봉합 완결성 — 이번 커밋이 넣은 문법을 **형제 일부가 아직 안 가졌다**(반쪽 봉합):')
        for rel, sym, label, n, miss in hits[:8]:
            print('   · %s 에 `%s` 추가 — 가족 %s(%d) 중 미보유 %d: %s'
                  % (rel, sym, label, n, len(miss), ', '.join(miss)))
        print('   → 같은 병이면 **이 커밋 안에서** 같이 고쳐라(260807 크로미엄 1/2 · 260728 조치문 1/3 · 260816 이관 3/8 = 반쪽 봉합이 전부 다음 사고가 됐다).')
        print('   → 정당한 단독 도입이면 그 줄에 `%s: <사유>` 표식을 달아라(그 줄 심볼은 비대상).' % _SEAL_OK)
        return 1
    return 0


def check_thumb_merge_canvas():
    """저작권·안내문 합성 = 산출물 크기로 캔버스를 정한다(하드 · 260812 실사고 봉합).

    계약 2축:
      ① 합성 레이어 포맷은 `params.fmt` **추측이 아니라** 산출물 실측 크기에서 역산한다.
      ② 안내문(guide)은 저작권과 **독립**이다(운영자 260712 "서로의 온오프 관계없이") —
         서버가 guide 를 copyright 블록 **안쪽**에서 읽으면 저작권 OFF 시 통째로 버려진다.

    ⚠️ 실사고 = 노뮤트 릴스 오버레이는 프론트가 fmt 를 안 보내고 서버가 'post' 로 채워 보내는데,
       렌더는 `generate('reels')` **고정**이라 산출물이 9:16 으로 나온다. 구판 합성은 `params.fmt`(=post)
       로 4:5 레이어를 만들어 크기가 어긋났고, 그 자리의 `continue` 가 **저작권·안내문을 통째로 건너뛰었다**
       (실측 run 31579366367 = PARAMS 에 copyright 가 실렸는데 산출물 상단 화소 0 · 경고는 러너 로그에만).
       260728 에 진짜예요(jinjja) 축을 고치려 넣은 「params.fmt 우선」이 노뮤트 축을 정확히 반대로 깨뜨린 것.
    ⚠️ 신설 사유 = 기존 게이트는 전부 다른 축 — `check_image_format` = 포맷·품질 · `check_thumb_redo_append`
       = 수정 누적 · `smoke_*` = 화면 렌더 → 「만든 레이어가 산출물에 실제로 얹히는가」는 축 자체가 없었다.
       증상이 「그냥 저작권이 안 보임」뿐이고 러너는 success 로 끝나서 운영자 눈이 유일한 검출기였다.
    정적 · 렌더·LLM·네트워크 0 · **면책표 없이 하드 0**.
    """
    bad = []
    wf = os.path.join(ROOT, '.github', 'workflows', 'thumb-make.yml')
    api = os.path.join(ROOT, 'functions', 'api', 'thumb.js')
    for p in (wf, api):
        if not os.path.exists(p):
            bad.append(f'{os.path.relpath(p, ROOT)}: 파일 없음(앵커 소실 = fail-closed)')
    if not bad:
        w = open(wf, encoding='utf-8').read()
        seg = w[w.find("_cr = params.get('copyright')"):]
        seg = seg[:seg.find('MERGED copyright')] if 'MERGED copyright' in seg else seg[:6000]
        code = '\n'.join(ln.split('#', 1)[0] for ln in seg.splitlines())   # 주석 제외(사고 기록의 거처)
        # ⚠ 「SPECS 라는 낱말이 있나」로 두면 import 줄만 남고 매핑이 비어도 통과한다(킬테스트 K3 실측 봉합)
        #   → 실제 역산 표현식(SPECS 순회로 크기→포맷 표를 만든다)과 그 표를 **산출물 크기로 조회**하는 줄을 함께 본다.
        if not re.search(r"\{\s*\(\s*\w+\[k\]\[.w.\]\s*\*\s*\w+\s*,\s*\w+\[k\]\[.h.\]\s*\*\s*\w+\s*\)\s*:\s*k\s+for\s+k\s+in\s+", code):
            bad.append('thumb-make.yml 합성 블록: 산출물 크기 역산표(SPECS 순회)가 없다 — params.fmt 추측으로 되돌아갔다')
        if not re.search(r'\(\s*base\.size\s*\)', code):
            bad.append('thumb-make.yml 합성 블록: 레이어를 `base.size`(산출물 실측 크기)로 고르지 않는다')
        if re.search(r'fmtc\s*=\s*params\.get\(.fmt.\)', code):
            bad.append('thumb-make.yml 합성 블록: 구판 `fmtc = params.get(\'fmt\')` 부활 — 노뮤트 릴스에서 4:5 레이어가 만들어져 통째로 스킵된다')
        # ② 안내문 독립 — guide 를 읽는 줄이 copyright 조건 블록 안쪽이면 저작권 OFF 시 유실
        a = open(api, encoding='utf-8').read()
        m = re.search(r'^(\s*)if \(p\.copyright && typeof p\.copyright', a, re.M)
        g = re.search(r'^(\s*)const guide = cleanLines\(p\.guide\)', a, re.M)
        if not g:
            bad.append('api/thumb.js: 안내문(guide) 수신 줄이 사라졌다')
        elif m and len(g.group(1)) > len(m.group(1)):
            bad.append('api/thumb.js: 안내문이 copyright 조건 안쪽에서 읽힌다 — 저작권 OFF면 안내문이 통째로 버려진다(260712 독립 계약 위반)')
    if bad:
        print('❌ 썸네일 합성 캔버스 — 저작권·안내문이 산출물에 안 얹힌다(260812 실사고 축):')
        for b in bad:
            print('   -', b)
        return 1
    print('✅ 썸네일 합성 캔버스 — 레이어 크기 = 산출물 역산 · 안내문은 저작권과 독립.')
    return 0


def check_orig_title_restore():
    """요약 제목 = 기자가 뽑은 원문이 화면까지 살아 온다(하드 · 260813 실사고 봉합).

    계약 = 「frontmatter `title` 은 기사 제목 **원문 전용**이고, 본문 `# 헤드`(후킹)와 같은 문장이 되면 안 된다」
       (정본 = prompts/news-analysis.md 38행 · 260703 3층 구분: 원문=title · 후킹=본문 헤드 · 번역=title_ko).

    ⚠️ 실사고 = 260811 밤부터 산출이 이 계약을 깨고 `title` 에 후킹 헤드를 그대로 넣었다(실측 11건 —
       260811 1건 · 260812 8/13 · 260813 2/2 · 그 전 600여 건은 0건). 수집기는 원문 제목을 정상 전달했다
       (예 「정부, 폭염에 수산물 최대 50% 할인·재난지원금 332억원 투입」 ↔ 산출 title 「바다는 식힐 수 없어서,
       죽기 전에 팔라고 한다」) = 원료는 프롬프트까지 도달했고 산출에서만 덮였다.
    ⚠️ 비용 = 뷰어 모달은 원문 제목 줄(`.md-srct`)을 「title ≠ H1」일 때만 그린다(viewer/index.html 4948행 ·
       옛 분석분의 제목 2줄 중복을 지우려고 260805 에 넣은 정당한 가드) → 두 값이 같아지는 순간 그 가드가
       정상 동작해 **기자 제목 줄이 통째로 안 그려진다**. 화면에 남는 건 추상 헤드 하나뿐이라 요약 상자만
       봐서는 무슨 사건인지 알 수 없다(운영자 260813 «요약된 박스 제목만 보면 무슨 내용인지를 모름»).
    ⚠️ 신설 사유 = 기존 게이트는 전부 다른 축이다 — `check_style_ratchet` = 본문 **문체**(리드 날짜·용어 풀이) ·
       `check_rubric_regress`·`check_grade_regress` = **판정** 룰북 · `smoke_*` = 화면 렌더 → 「제목 필드가
       제 몫을 하는가」는 축 자체가 없었다. 짝 검출기인 digest_guard 의 대조도 **원문자 완전일치**라
       본문 헤드가 이모지로 열리면(= IG 헤드 골격의 정상 형태) 전건 빠져나갔다(실측 11건 경고 0건) =
       탐지기가 있는데 죽어 있었다. 결국 운영자 눈이 유일한 검출기였다(insta-thumb-miss·brk_misfire 동축).
    판정 4축 · 정적 · 렌더·LLM·네트워크 0 · **면책표 없이 하드 0**(부채 원장 증가 0).
    """
    bad = []
    rs = os.path.join(ROOT, '.github', 'scripts', 'restore_orig_title.py')
    an = os.path.join(ROOT, '.github', 'scripts', 'analyze.sh')
    dg = os.path.join(ROOT, 'shared', 'digest_guard.py')
    pr = os.path.join(ROOT, 'prompts', 'news-analysis.md')
    for p in (rs, an, dg, pr):
        if not os.path.isfile(p):
            bad.append('파일 없음: ' + os.path.relpath(p, ROOT))
    if bad:
        print('❌ 원문 제목 복원 체인 —', ' / '.join(bad))
        return 1
    rt = open(rs, encoding='utf-8').read()
    at = open(an, encoding='utf-8').read()
    dt = open(dg, encoding='utf-8').read()
    pt = open(pr, encoding='utf-8').read()

    # ① 복원 도장이 analyze 산출 경로에 **실행줄로** 배선(주석 처리 우회 차단 = _has_exec_line 계승).
    if not _has_exec_line(at, 'restore_orig_title.py'):
        bad.append('① analyze.sh 가 restore_orig_title.py 를 실행줄로 안 부른다 = 복원 층 사망')
    # ①-b 원료 가드 — title_hint 없이 부르면 빈 문자열로 덮을 위험(스크립트가 막지만 호출부도 같은 계약).
    if 'title_hint' not in at.split('restore_orig_title.py')[0][-600:]:
        bad.append('①-b 복원 호출이 수집기 원문 제목(title_hint) 가드 안에 있지 않다')

    # ② 복원 술어 = 「위반 서명일 때만 손댄다」 + 선두 이모지 무시 대조(계약 준수 산출 무접촉이 실효 조건).
    if 'def key' not in rt or '_LEAD_EMOJI' not in rt:
        bad.append('② restore_orig_title.py 에 선두 이모지 무시 비교키가 없다')
    if '계약 준수' not in rt:
        bad.append('② restore_orig_title.py 가 계약 준수 산출을 무주입으로 빠져나가지 않는다(전건 덮어쓰기 위험)')

    # ③ 짝 검출기 = digest_guard 대조가 이모지 무시 키여야 한다(구판 원문자 완전일치 부활 = 탐지기 사망).
    if 'h1 == title' in dt or 'h1 == title_ko' in dt:
        bad.append('③ digest_guard 가 구판 원문자 완전일치 대조로 되돌아갔다 = 이모지 헤드 전건 미검출')
    if '_k(h1) == _k(title)' not in dt:
        bad.append('③ digest_guard 에 이모지 무시 키 대조가 없다')

    # ④ 프롬프트 계약 문구 — 「본문 헤드와 같은 문장을 title 에 쓰지 마라」가 사라지면 모델 쪽 유인이 되살아난다.
    if '본문 `# {제목}`과 같은 문장을 여기 쓰지 마라' not in pt:
        bad.append('④ prompts/news-analysis.md 에 title↔본문 헤드 동일 금지 계약이 없다')

    if bad:
        print('❌ 원문 제목 복원 체인 —', ' / '.join(bad))
        return 1
    print('✅ 원문 제목 복원 — 후킹 헤드가 title 을 덮으면 수집기 원문으로 되돌린다(짝 검출기 이모지 구멍 봉합).')
    return 0


# 운영자에게 「어느 칸을 갈지」 말하는 표면 = 칸 이름이 필수(면책표 아님 = 대상 목록).
#   ⚠ 이름을 안 쓰는 표면(vidl-make·yt-cookie-whoami = 자기 문구에 칸을 안 말한다)은 여기 없다 —
#     늘릴 땐 「그 표면이 운영자에게 칸을 지시하는가」로 판정한다.
_YTCK_NAME_REQ = {os.path.join('.github', 'workflows', 'yt-cookie-health.yml')}
_YTCK_LITERAL_FREE = {os.path.join('.github', 'scripts', 'yt_cookie_health.py')}


def check_yt_cookie_slot_name():
    """유튜브 쿠키 = 알림이 말하는 칸 이름이 실제 배선과 같다(하드 · 260812 실사고 봉합).

    계약 = 「운영자에게 **어느 칸을 갈지** 말하는 문구는 그 칸 이름을 코드에 손으로 적지 않고,
       워크플로가 알려준 `<슬롯>_NAME` 을 그대로 쓴다」. 문법 정본 = `.github/scripts/ytdlp_try.sh`
       (운영자 260812 «죽은 쿠키인지 안 죽은 쿠키인지 먼저 확인하고 · 대명사 쓰지 말고 명시»).

    ⚠️ 실사고 = 배선은 `YT_COOKIES(1번) ← YT_T2_COOKIES` / `YT_COOKIES_2(2번) ← YT_T_COOKIES` 인데
       감시기 알림 문구는 `1번→YT_T_COOKIES · 2번→YT_T2_COOKIES` 로 **정확히 반대**를 지시했다.
       실측 260812 11:24 = 알림은 「2번 죽음 → YT_T2_COOKIES 를 갈아라」인데 같은 시각 받기 레일 진단은
       「YT_T2_COOKIES = 살아있음 · YT_T_COOKIES = 죽음」 — 두 시스템이 같은 상태를 정반대로 말했다.
       비용 = 운영자가 **살아있는 칸을 갈고** 죽은 칸은 그대로 둬서 경고가 영영 안 꺼진다(실제로 그렇게 됐다).
    ⚠️ 신설 사유 = 260812 지시가 받기 레일 8종에만 적용되고 **감시기는 안 따라왔는데 아무 게이트도 안 울렸다**
       (`check_seal_completeness` 가 겨눈 「같은 병의 형제」 축 · 그쪽은 WARN이라 차단하지 못한다).
       기존 게이트는 전부 다른 축 — `check_paths` = 경로 실존 · `check_workflow_yaml` = 문법 · `smoke_*` = 화면 렌더
       → 「알림이 **맞는 칸 이름**을 말하는가」는 축 자체가 없었고, 증상이 「갈아도 경고가 안 꺼짐」뿐이라
       운영자 눈이 유일한 검출기였다(insta-thumb-miss·brk_misfire 동축).

    판정 3축(정적 · 렌더·LLM·네트워크 0 · 면책표 없이 하드 0):
      ① `<슬롯>_NAME` 이 있으면 그 값 == 그 슬롯이 실제로 받는 secrets 이름(짝 뒤집힘 차단 · 현행 8워크플로 정합)
      ② 알림·진단문을 내보내는 표면(`_YTCK_NAME_REQ`)은 `<슬롯>_NAME` 보유 필수
         (빠지면 폴백이 env 이름 `YT_COOKIES` 로 말해서 운영자가 어느 칸인지 못 찾는다)
      ③ 그 표면의 스크립트 **코드부**에 시크릿 이름 리터럴 0(주석은 제외 = 사고 기록의 거처)
         — 손으로 적는 순간 다시 갈린다 = 이번 사고의 진범 그 자체.
    """
    import glob as _g
    bad = []
    sec_re = re.compile(r'^\s*(YT_COOKIES(?:_[23])?):\s*\$\{\{\s*secrets\.([A-Za-z0-9_]+)\s*\}\}', re.M)
    nm_re = re.compile(r'^\s*(YT_COOKIES(?:_[23])?)_NAME:\s*([A-Za-z0-9_]+)', re.M)
    for f in sorted(_g.glob(os.path.join(ROOT, '.github', 'workflows', '*.yml'))):
        rel = os.path.relpath(f, ROOT)
        txt = open(f, encoding='utf-8').read()
        pairs = sec_re.findall(txt)
        if not pairs:
            continue
        names = dict(nm_re.findall(txt))
        for var, sec in pairs:
            got = names.get(var)
            if got is not None and got != sec:          # ① 짝 뒤집힘
                bad.append(f'{rel}: {var} ← secrets.{sec} 인데 {var}_NAME={got} (알림이 반대 칸을 지시한다)')
            elif got is None and rel in _YTCK_NAME_REQ:  # ② 알림 표면인데 이름 미지정
                bad.append(f'{rel}: {var}_NAME 없음 — 알림이 저장소 칸을 env 이름으로 말하게 된다')
    for rel in sorted(_YTCK_LITERAL_FREE):              # ③ 코드부 하드코딩 0
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            bad.append(f'{rel}: 파일 없음(앵커 소실 = fail-closed)')
            continue
        src = open(p, encoding='utf-8').read()
        # 독스트링·삼중따옴표 블록 = 설명문(사고 기록의 거처) → **길이 보존 공백 마스킹**(줄 번호가 안 어긋난다).
        #   ⚠ 이 마스킹이 없으면 봉합 주석 자신이 위반으로 잡힌다(첫 실행 실측 = 4건 위양성).
        src = re.sub(r'("""|\'\'\')(?:.|\n)*?\1',
                     lambda m: re.sub(r'[^\n]', ' ', m.group(0)), src)
        for i, ln in enumerate(src.splitlines(), 1):
            code = ln.split('#', 1)[0]                  # 줄 주석 제외(처방문의 거처)
            if re.search(r'\bYT_T2?_COOKIES\b', code):
                bad.append(f'{rel}:{i}: 코드에 시크릿 이름을 손으로 적었다 → kan(<슬롯>) 경유로 바꿔라')
    if bad:
        print('❌ 유튜브 쿠키 칸 이름 정합 — 알림이 「갈아야 할 칸」을 틀리게 말한다(260812 실사고 축):')
        for b in bad:
            print('   -', b)
        return 1
    print('✅ 유튜브 쿠키 칸 이름 정합 — 슬롯↔시크릿 짝 전건 일치 · 알림 표면 이름 보유 · 코드 하드코딩 0.')
    return 0


def check_smoke_chromium_path():
    """스모크 크로미엄 경로 = 폴백 해석기 경유(하드 · 260808 실사고 봉합 · check_smoke_obs_chain 의 짝).

    계약 = 「`shared/smoke_*.js` 가 브라우저를 띄울 때 `executablePath` 에 **리터럴 경로를 박지 않는다**」
       = 정본 해석기 `chromiumPath()`(env → /opt/pw-browsers → `which` 폴백) 를 경유한다.

    ⚠️ 신설 사유 = **260807 봉합이 같은 병을 앓던 두 종 중 한 종만 고쳤고, 아무 게이트도 안 울렸다.**
       그 커밋 주석은 「형제 23종은 전부 which 폴백 보유 = 이 한 종만 갈렸다」고 단언했는데 **실측은 2종**
       (`smoke_wip` ∧ `smoke_photoflow`)이었다 → 봉합 **다음** 나이틀리(런 31211705342 · 260808 04:29 KST)도
       `smoke_photoflow=1` 로 그대로 붉었고, 운영자는 8일째 「UI 스모크 FAIL」 알림을 또 받았다.
    ⚠️ 짝 게이트 `check_smoke_obs_chain` 은 **경보가 사유를 갖고 나가는가**만 본다(관측 축) —
       「그 스모크가 러너에서 **뜨기는 하는가**」는 축 자체가 없었다. 그래서 실행 환경 축의 회귀는
       나이틀리가 붉어진 뒤 사람이 로그를 열어야만 보였다(insta-thumb-miss·brk_misfire 동축).
    판정 = 정적(렌더·LLM·네트워크 0) · 표면 자동 발견(새 스모크가 조용히 못 빠진다) · 주석 줄 제외
       (주석 처리 우회 차단 · check_thumb_redo_append 관용구) · **면책표 없이 하드 0**(부채 원장 증가 0)."""
    bad = []
    for p in sorted(glob.glob(os.path.join(ROOT, 'shared', 'smoke_*.js'))):
        rel = os.path.relpath(p, ROOT)
        try:
            src = open(p, encoding='utf-8').read()
        except OSError:
            continue
        for i, ln in enumerate(src.splitlines(), 1):
            if ln.lstrip().startswith('//'):
                continue   # 주석 줄 = 비대상(처방문·구판 인용이 곧 위반으로 읽히는 자기참조 차단)
            m = re.search(r'''executablePath\s*:\s*['"]([^'"]+)['"]''', ln)
            if m:
                bad.append('%s:%d  executablePath:%r = 리터럴 경로(폴백 0)' % (rel, i, m.group(1)))
        # ②축 = 해석기 **몸통** 정합(260809 실사고 봉합 · 위 ①축의 사각).
        #   ⚠ 260808 봉합은 「executablePath 에 리터럴을 박았나」= **호출부**만 봤다. 그런데 실패는
        #     `chromiumPath()` 라는 **정본 이름을 그대로 달고** 다시 났다 — 몸통이 `return cands.find(Boolean)`
        #     이라 존재 검사 없이 첫 truthy(= '/opt/pw-browsers/chromium')를 그대로 뱉는 사본이었다.
        #     호출부는 정본과 글자 하나 안 다르고(`executablePath: chromiumPath()`), 로컬엔 그 경로가
        #     실재해 **로컬 PASS·러너만 FAIL** → 게이트·사람 눈 양쪽의 사각(260809 실측 = smoke_rank·smoke_favtab
        #     2종 · 나이틀리 런 31236664571 `smoke_rank=1`). = 「같은 병의 형제」가 아니라 **같은 병의 변종**.
        #   술어 = chromiumPath() 를 정의하면 그 몸통은 후보를 **실존 검사**한다(정본 = shared/smoke_parity.js).
        mb = re.search(r'function\s+chromiumPath\s*\([^)]*\)\s*\{(.*?)\n\}', src, re.S)
        if mb:
            body = '\n'.join(x for x in mb.group(1).splitlines() if not x.lstrip().startswith('//'))
            if 'existsSync' not in body:
                bad.append('%s  chromiumPath() 몸통에 실존 검사 0 = 리터럴을 그대로 반환(로컬 PASS·러너 FAIL)' % rel)
    if bad:
        print('❌ 스모크 크로미엄 경로 게이트 — 리터럴 경로 하드코딩(러너에 그 경로가 없으면 매 나이틀리 확정 실패):')
        for b in bad:
            print('   -', b)
        print('   → 처방: `chromiumPath()` 정본 사본(shared/smoke_parity.js)을 이식하고 '
              'executablePath: chromiumPath() 로 바꿔라 — env → /opt/pw-browsers → which 순 폴백.')
        return 1
    print('✅ 스모크 크로미엄 경로 게이트 — smoke_*.js 전건 폴백 해석기 경유(리터럴 하드코딩 0).')
    return 0


def _edit_track_phase_ok(wf, et):
    """자동 가림 2단계 계약 = 「픽셀에 굽는 계열(모자이크·핀셋)은 자막보다 **먼저**」(운영자 260809
    "모자이크가 자막 위로 올라가버려서 자막이 가려져").
    ⚠ 이 축이 없으면 스텝을 한 줄만 옮겨도 구판 사고가 그대로 되살아나는데 **화면은 멀쩡히 산출이 나온다**
      (모자이크도 자막도 다 보인다 — 겹친 순서만 틀렸을 뿐이라 rc·로그로는 안 잡힌다) = 운영자 눈이 유일한 검출기.
    판정 = ⓐ 러너가 phase 인자를 갈라 받는다 ⓑ 워크플로에 pre·post 두 실행줄이 있다
           ⓒ **pre 스텝이 컴포즈보다 앞** ⓓ post는 컴포즈보다 뒤 ⓔ pre 산출이 EDIT_SRC로 이어진다."""
    if not ('"pre", "post"' in et and 'edit_track_pre.txt' in et):
        return False
    i_pre = wf.find('"$EDIT_SRC" pre')
    i_cmp = wf.find('python3 .github/scripts/ly_burn.py')   # ⚠ 실행줄로 특정 — 그냥 'ly_burn.py'면 **파일 상단 설명 주석**이 먼저 잡혀 순서 비교가 통째로 무의미해진다(실측)
    i_post = wf.find('"$SRC_IN" post')
    if min(i_pre, i_cmp, i_post) < 0:
        return False
    if not (i_pre < i_cmp < i_post):   # 순서가 뒤집히면 자막이 다시 가려진다
        return False
    return 'EDIT_SRC=$NEWSRC' in wf


def _pinset_parity_removed():
    """(260810 제거) 핀셋 이름표 규격 py↔js 대조 게이트 — 운영자 "트래킹 미리보기 없어도됨".
    이 게이트의 존재 이유는 **뷰어 미리보기가 러너 렌더와 같은 값인가**였다. 미리보기를 걷어내면서 뷰어 쪽 사본
    (`PIN_SPEC`·`PIN_PALETTE`)도 같이 나갔으므로 대조할 짝이 없다 = 규격 정본이 러너 한 곳뿐 = 갈릴 여지 0.
    ⚠ 미리보기를 되살리면 이 게이트도 **같은 커밋에** 되살린다(한쪽만 되살아나면 그날부터 미리보기가 조용히 거짓말을 한다).
    """
    return 0

def check_grok_sb_chain():
    """콘티 그록 레인 = 5층 생존(운영자 260811 「진행해보자」).

    계약 = 「촬영=grok 을 고르면 컷마다 그림→영상이 실제로 나온다」. 그 흐름이 지나는 층 =
    뷰어 칩 → 서버 화이트리스트 → 워크플로 스텝 → 러너 → 감독 지침. **한 층만 빠져도
    조용히 죽는다** — 화면은 멀쩡히 칩이 눌리고 콘티까지 정상으로 나오는데 영상만 안 생긴다.
    이 레포가 반복해 겪은 축이라(insta-thumb-miss·brk_misfire·nm-jobs 동축) 층별 생존을 못박는다.

    ⚠ 기존 게이트는 전부 다른 축이다 — `check_model_names` = 표시명 문자 동기 ·
      `check_k_models` = k 레인 값 3면 동기 · `smoke_*` = 화면 렌더 → 「그록 레인이 끝까지
      이어져 있는가」는 축 자체가 없었다.

    ⚠ 소리 축을 같이 본다 = 운영자 확정 옵션인데 층이 4개(뷰어→서버→워크플로→러너)라
      중간 한 곳만 빠지면 **스위치가 무동작**이 된다(정본 §4-1 = 끄기의 확실한 수단은
      산출 트랙 제거뿐이라 그 호출까지 검사).

    정적 · 렌더·LLM·네트워크 0 · 면책표 없이 하드 0.
    """
    rc = 0
    def _t(path):
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                return f.read()
        except OSError:
            return ""

    # ① 뷰어 = 촬영 칩 + 표시명 사전
    vt, nm = _t("viewer/sb.html"), _t("viewer/nm-models.js")
    if "id: 'grok'" not in vt:
        print("❌ 그록 콘티 레인 — viewer/sb.html SB_SHOOTS 에 grok 칩이 없다(촬영 선택 불가)"); rc = 1
    if "grok:" not in nm:
        print("❌ 그록 콘티 레인 — viewer/nm-models.js 에 grok 표시명이 없다(칩 라벨 undefined)"); rc = 1

    # ② 서버 = 화이트리스트 + 소리 전달(둘 다 없으면 폼 값이 러너까지 못 간다)
    sv = _t("functions/api/sb.js")
    if "'grok'" not in sv:
        print("❌ 그록 콘티 레인 — functions/api/sb.js SB_SHOOTS 에 grok 이 없다(발사 거절)"); rc = 1
    for needle, why in (("const sound", "소리 값 파싱"), ("shoot, sound,", "소리 값 워크플로 전달")):
        if needle not in sv:
            print("❌ 그록 콘티 레인 — functions/api/sb.js 에 {} 가 없다(소리 스위치 무동작)".format(why)); rc = 1

    # ③ 워크플로 = 스텝 + 입력 + 자격 시크릿
    wf = _t(".github/workflows/sb-make.yml")
    # ⚠ 선택지 목록 축(260811 실사고) = 설명·스텝이 다 맞아도 options 에 없으면 GitHub 이
    #   422 로 거절한다. 설명 문자열만 보던 첫 판이 이걸 그대로 통과시켰다.
    mo = re.search(r"^      shoot:\n(?:.*\n)*?        options:\n((?:          - \S+\n)+)", wf, re.M)
    opts = re.findall(r"- (\S+)", mo.group(1)) if mo else []
    if "grok" not in opts:
        print("❌ 그록 콘티 레인 — sb-make.yml shoot 선택지에 grok 이 없다(발사가 422 로 거절된다 · 현재 {})".format(opts)); rc = 1
    if "kling" in opts:
        print("❌ 그록 콘티 레인 — sb-make.yml shoot 선택지에 kling 잔여(제거 확정분 회귀)"); rc = 1
    for needle, why in (("name: Grok video", "영상 스텝"),
                        ("grok_sb_video.py", "러너 호출"),
                        ("shoot == 'grok'", "레인 게이트"),
                        ("sound:", "소리 입력"),
                        ("XAI_REFRESH_TOKEN", "구독 자격"),
                        ("GROK_SOUND", "소리 전달"),
                        ("name: Storyboard sheet", "콘티 시트 스텝"),
                        ("sb_sheet.py", "시트 러너 호출")):
        if needle not in wf:
            print("❌ 그록 콘티 레인 — sb-make.yml 에 {} 가 없다({})".format(why, needle)); rc = 1

    # ④ 러너 = 골격(한 축만 빠져도 조용히 다른 동작이 된다)
    rn = _t(".github/scripts/grok_sb_video.py")
    for needle, why in (("def cuts_of", "컷 파서"),
                        ("def vid_prompt", "영상 프롬프트 조립"),
                        ("def strip_audio", "소리 끄기(산출 트랙 제거)"),
                        ("strip_audio(local)", "소리 끄기 실호출"),
                        ("LANE.fresh_token", "자격 갱신·저장(회전 대응 · 통로 계약 경유)"),
                        ("refs=payload or None", "참조 그림 실어 보내기(컷 수와 무관)"),
                        ("def refs_of", "참조 목록 파서"),
                        ("seconds=c[\"sec\"]", "컷 길이 = 콘티 값")):
        if needle not in rn:
            print("❌ 그록 콘티 레인 — grok_sb_video.py 에 {} 가 없다({})".format(why, needle)); rc = 1
    # ⚠ 컷 길이 = **10초 고정**(운영자 260812 「고정임 더 짧을수도 없고」) — 구판은 콘티가 적은
    #   값을 그대로 썼고 그 컷 수 규칙이 종이 콘티용이라 1.2초 조각이 열두 개 나왔다(260811 실측).
    #   그래서 이 축은 260812 에 **뒤집혔다**: 구 게이트(고정 상수 금지)를 회수하고 고정을 강제한다.
    # ⚠ **영상 1편 = 10초 고정 · 컷은 그 안의 카메라 전환**(운영자 260812). 구판은 둘을 겸하게 해
    #   컷 하나가 곧 호출 하나였고, 종이 콘티 칸 수를 그대로 받아 1.2초 조각이 열두 개 나왔다.
    if "CUT_SEC" not in rn or "def group_shots" not in rn:
        print("❌ 그록 콘티 레인 — 10초 묶기(group_shots·CUT_SEC)가 없다 = 컷 하나가 곧 호출 하나가 된다"); rc = 1
    if "shots = group_shots(cuts)" not in rn:
        print("❌ 그록 콘티 레인 — 발사 단위가 영상 편이 아니다(컷을 그대로 쏜다)"); rc = 1
    if '"{}-{}s: {}".format' not in rn:
        print("❌ 그록 콘티 레인 — 묶음 안 컷에 시각을 안 붙인다(한 편 안 전환이 안 선다)"); rc = 1
    # ⚠ ffmpeg = 러너 기본 이미지에 **없다**(260812 실측) — 없으면 완본 이어붙이기와 소리 끄기가
    #   둘 다 조용히 걸린다. 소리 쪽이 더 비싸다(꺼달라고 했는데 실린 채 나간다).
    _gv = wf.split("name: Grok video", 1)[-1]
    if "ffmpeg" not in _gv.split("name: Commit output", 1)[0]:
        print("❌ 그록 콘티 레인 — 영상 스텝이 ffmpeg 을 안 깐다(완본·소리 끄기가 조용히 걸린다)"); rc = 1
    if "sbCutN = s => Math.max(1, Math.round(s / SB_LEN_STEP))" not in vt:
        print("❌ 그록 콘티 레인 — 뷰어 편수 산식이 길이÷10 이 아니다(구 종이 콘티 밴드 잔존)"); rc = 1

    # ⑥ 260811 첫 실호출 실측 봉합 2종 — 둘 다 빠져도 영상은 나온다(= 조용히 나빠진다)
    for needle, why in (("def ref_ids", "참조 슬롯 정체 묶기(대명사 뒤바뀜 차단 · 실측 컷7)"),
                        ("REF_CAP", "참조 장수 상한(운영자 260811 = 2 기본·3 이유 있을 때·4 금지)"),
                        ("ref_reason", "장수 사유 기록(3장을 쓴 이유가 산출에 남는다)")):
        if needle not in rn:
            print("❌ 그록 콘티 레인 — grok_sb_video.py 에 {} 가 없다({})".format(why, needle)); rc = 1
    # 정체 문장은 **동작 문장보다 앞**에 서야 한다(자기회귀 = 뒤에 두면 대명사가 가리킬 대상이 없다)
    _vp = rn.split("def vid_prompt", 1)[-1].split("\ndef ", 1)[0]
    if _vp and _vp.find("parts.extend(ids") > _vp.find('c["camera"]'):
        print("❌ 그록 콘티 레인 — 등장 인물표가 동작 문장 뒤에 있다(앞에 와야 대명사가 묶인다)"); rc = 1
    # ⑥-b 콘티 시트도 참조 한 장(운영자 260814 「콘티시트를 왜 참조를 안해? 그것도 참조로 넣어」)
    #   ⚠ 이 축은 **빠져도 영상이 정상으로 나온다** — 편 사이 흐름만 조용히 흔들린다(운영자 눈이 유일한 검출기).
    #   ⚠ 시트는 그림 참조 상한(REF_CAP) **밖**이라야 한다 = 시트가 인물·장소 슬롯을 밀어내면 사고다.
    for needle, why in (("def sheet_slots", "시트 참조 슬롯 파서"),
                        ("SHEET_CLAUSE = ", "시트 정체 문장(설계도지 장면이 아니다)"),
                        ("CONTI_CLAUSE = ", "스케치 판 전용 정체 문장(스토리보드 문구 재사용 = 거짓 정체)"),
                        ("live-action footage", "완성본은 실사라는 **긍정문** 고지(부정문 단독은 그 낱말을 오히려 심는다)"),
                        ("slots.extend(sheets)", "설계 판이 편마다 실린다"),
                        ("def cap_refs", "상한은 만든 장수가 아니라 한 편에 실리는 장수에 건다"),
                        ("sheets = sheet_slots(out_dir)", "설계 판을 실제로 **부른다**(함수만 남기고 호출을 죽이면 조용히 0장)")):
        if not _has_exec_line(rn, needle):
            print("❌ 그록 콘티 레인 — grok_sb_video.py 에 {} 가 없다({})".format(why, needle)); rc = 1
    _ss = rn.split("def sheet_slots", 1)[-1].split("\ndef ", 1)[0]
    if _ss and "sheet.json" not in _ss:
        print("❌ 그록 콘티 레인 — 시트 참조가 sheet.json 을 안 읽는다(주소를 어디서 얻나)"); rc = 1
    if _ss and ('"bg": False' not in _ss or '"night": False' not in _ss):
        print("❌ 그록 콘티 레인 — 시트 슬롯이 시간대 필터를 탄다(밤 편에서 시트가 빠진다)"); rc = 1
    # 시트 합류는 ref_slots(그림 상한 컷) **뒤**여야 한다 — 앞이면 시트가 인물·장소를 밀어낸다
    if rn.find("slots.extend(sheets)") < rn.find("slots = ref_slots("):
        print("❌ 그록 콘티 레인 — 시트가 그림 참조보다 먼저 슬롯에 든다(인물·장소가 상한에 밀린다)"); rc = 1

    # ⑥-c 참조 판 = 견본 모방(운영자 260814 견본 다섯 장 실측 · 「잘 만든 걸 모티프로」 = 창작 금지)
    #   ⚠ 이 축들은 **빠져도 그림은 나온다** — 시트가 견본과 조금씩 달라질 뿐이라 운영자 눈이 유일한 검출기다.
    kg = _t(".github/scripts/k_refgen.py")
    for needle, why in (("TURN_SPECS", "다각도 시트 문법표(사람·제품·주요 장소)"),
                        ("def sheet_kind", "라벨로 시트 여부를 가른다(전부 시트면 값이 배로 든다)"),
                        ("def ref_labels", "라벨 파서 단일정본(그림 굽는 쪽과 슬롯 세는 쪽이 같은 순서)"),
                        ("정면(FRONT)", "큰 정면 칸(견본 다섯 장 전건 보유)"),
                        ("달리기(RUN)", "달리기 칸(견본 보유 · 동작 정보를 인물 쪽에서 준다)")):
        if not _has_exec_line(kg, needle):
            print("❌ 그록 콘티 레인 — k_refgen.py 에 {} 가 없다({})".format(why, needle)); rc = 1
    # ⚠ 뒷모습 금지는 **사람 칸만**이다 — 제품 시트의 후면은 master-sheet-v2 PRODUCT 정본 칸이라 정당하다
    _person = kg.split('"person": (', 1)[-1].split('"product":', 1)[0]
    if "BACK" in _person:
        print("❌ 그록 콘티 레인 — 인물 시트에 뒷모습 칸이 있다(견본 다섯 장 전부 없다 · 패널 6 초과)"); rc = 1
    ss = _t(".github/scripts/sb_sheet.py")
    for needle, why in (("def continuity_of", "연속성 규칙 한 줄(칸끼리 방향·자리를 잡는 뼈대)"),
                        ("def times_of", "칸마다 시작·끝 시각(견본 실측)"),
                        ("def _real_line", "대사는 있는 칸에만(견본 실측 = 빈 대사 줄 안 찍는다)"),
                        ("Draw EXACTLY", "칸 수를 콘티 컷 수로 못 박는다(빈칸을 모델이 채우면 없는 컷이 생긴다)")):
        if not _has_exec_line(ss, needle):
            print("❌ 그록 콘티 레인 — sb_sheet.py 에 {} 가 없다({})".format(why, needle)); rc = 1
    if "연속성:" not in _t("prompts/sb-make.md"):
        print("❌ 그록 콘티 레인 — 감독 지침에 연속성 한 줄 계약이 없다(시트가 뼈대 없이 굽힌다)"); rc = 1

    # ⑥-d 정본 함수 재판정(평의회 260814 5번 = 「문자열 실존만 보면 값 흐름만 끊어도 전건 통과」)
    #   ⚠ 실측 우회 5종이 전부 rc=0 이었다 = 호출 무력화 · 킬스위치 극성 반전 · 슬롯 재절단 ·
    #     bg 오염 · 생산자 키 개명. 다섯 다 화면·로그 증상 0이라 정적 문자열로는 구조적으로 못 잡는다.
    #   → 이 레포 관례(`check_disaster_landmark_sign`·`check_thumb_prompt_sanity`)대로 **함수를 불러**
    #     가짜 입력으로 조립한 결과의 술어를 본다(렌더·LLM·네트워크·발사 0 · 과금 0).
    try:
        import importlib, tempfile, sys as _sys
        # ⚠ 캐시 무효화 — 같은 크기로 같은 초에 고친 파일은 옛 바이트코드가 그대로 읽힌다
        #   (이 축 첫 실행에서 실제로 그 함정을 밟아 게이트가 옛 코드를 판정했다).
        importlib.invalidate_caches()
        _sp = os.path.join(ROOT, ".github", "scripts")
        if _sp not in _sys.path:
            _sys.path.insert(0, _sp)
        os.environ.setdefault("SB_LANE", "seedance")
        _kr = importlib.import_module("k_refgen")
        _gv = importlib.import_module("grok_sb_video")
        _sb = importlib.import_module("sb_sheet")
    except Exception as e:  # noqa: BLE001
        # ⚠ PASS 와 합치지 않는다 — 관측이 지워지면 다음 세션이 추측으로 메운다(이 레포 반복 교훈).
        print("⏭ 그록 콘티 레인 ⑥-d 재판정 SKIP(모듈 적재 실패 = 환경 축): {}".format(str(e)[:120]))
    else:
        _panels = sum(w in _kr.TURN_SPECS.get("person", "") for w in ("FRONT", "SIDE", "FULL BODY", "EXPRESSION"))
        if _panels < 4:
            print("❌ 그록 콘티 레인 — 인물 시트가 낱장으로 회귀(칸 {}개 · 4면 미만)".format(_panels)); rc = 1
        if not _kr.sheet_kind("인물") or _kr.sheet_kind("배경"):
            print("❌ 그록 콘티 레인 — 라벨 판정이 뒤집혔다(인물이 낱장이거나 배경이 시트로 굽힌다)"); rc = 1
        if [l for l, _ in _kr.ref_pairs("## 🖼 레퍼런스\n① 인물: 남\n```text\nman\n```\n② 배경: 카페\n③ 인물: 여\n```text\nwoman\n```\n")] != ["인물", "인물"]:
            print("❌ 그록 콘티 레인 — 라벨↔블록 짝짓기가 밀린다(블록 없는 라벨 하나에 뒤가 통째로 밀림)"); rc = 1
        _d = tempfile.mkdtemp()
        # ⚠ with 로 닫는다 — 안 닫으면 버퍼가 안 비워져 바로 뒤 읽기가 빈 파일을 보고
        #   게이트가 **무작위로 빨개진다**(이 게이트 첫 실행에서 실제로 그랬다 = 가짜 빨강 공장).
        with open(os.path.join(_d, "sheet.json"), "w", encoding="utf-8") as _f:
            json.dump({"url": "https://x/s.jpg", "conti": "https://x/c.jpg", "cuts": 9}, _f)
        _got = _gv.sheet_slots(_d) or []
        # ⚠ 가짜 파일만 읽으면 **생산자가 키를 개명해도** 게이트는 모른다(평의회 A5 실측 = rc=0).
        #   그래서 굽는 쪽이 실제로 그 칸에 쓰는지 원문에서 같이 본다.
        for _k in ('d["url"]', 'd[kind]'):
            if _k not in ss:
                print("❌ 그록 콘티 레인 — sb_sheet 가 {} 칸에 안 쓴다(읽는 쪽과 키가 갈렸다)".format(_k)); rc = 1
        if len(_got) != 2:
            print("❌ 그록 콘티 레인 — 설계 판이 {}장만 실린다(스토리보드·스케치 두 장이라야 한다)".format(len(_got))); rc = 1
        elif any(x.get("bg") is not False or not x.get("sheet") for x in _got):
            print("❌ 그록 콘티 레인 — 설계 판 슬롯이 배경 필터를 탄다(밤 편에서 빠진다)"); rc = 1
        _cuts = [{"action": "A", "desc": "", "camera": "C", "motion": "M", "sec": 2, "dialogue": ""} for _ in range(9)]
        _b, _c = _sb.sheet_prompt("# t\n", _cuts), _sb.conti_prompt("# t\n", _cuts)
        _gb, _gc = re.search(r"grid (\d+)x(\d+)", _b, re.I), re.search(r"[Gg]rid (\d+)x(\d+)", _c)
        if not _gb or not _gc or _gb.groups() != _gc.groups():
            print("❌ 그록 콘티 레인 — 스케치 판 격자가 스토리보드와 안 맞는다(칸 순서가 어긋난다)"); rc = 1
        if "NO color" not in _c or "pencil" not in _c.lower():
            print("❌ 그록 콘티 레인 — 스케치 판이 채색 그림으로 회귀(연필선 계약 소실)"); rc = 1
        if "TIME:" not in _b:
            print("❌ 그록 콘티 레인 — 스토리보드 칸에 시각이 안 찍힌다(견본 실측 축)"); rc = 1

    # ⑦ 값 원장 = 벤더 세 곳이 각자 적고 화면이 합쳐 읽는다(한 곳만 빠져도 금액이 조용히 작아진다)
    for path, needle, why in (
            (".github/scripts/sb_cost.py", "def add", "값 원장 정본"),
            (".github/scripts/grok_sb_video.py", "sc.add(out_dir, LANE.NAME", "영상 값 적재(통로 이름)"),
            # ⚠ 칸 이름은 판마다 갈린다(board=sheet · conti=conti) → 변수 경유가 정본이라 호출만 본다
            (".github/scripts/sb_sheet.py", "sc.add(out_dir, engine, _kind", "시트 값 적재(엔진 무관)"),
            (".github/scripts/k_refgen.py", '"gemini", "ref"', "참조 그림 값 적재"),
            ("viewer/sb.html", "cost.json", "화면이 원장을 읽는다"),
            ("viewer/sb.html", 'id="sndTg"', "소리 스위치(서버·러너는 받는데 화면에만 없던 축)"),
            ("viewer/sb.html", "sound: (sbShoot === 'grok')", "소리 값이 발사 페이로드에 실린다"),
            ("viewer/sb.html", "nmRail.add({ url: abs(c.video)", "만든 영상이 이전 제작에 착지한다"),
            (".github/scripts/grok_sb_video.py", "def stitch", "조각을 한 편으로 이어붙인다(외부 호출 0)"),
            (".github/scripts/grok_sb_video.py", 'c.get("sfx")', "컷이 적은 소리를 프롬프트에 싣는다"),
            ("viewer/sb.html", "v.full", "완본이 화면 맨 앞에 선다"),
            ("prompts/sb-make.md", "SFX:", "감독 SFX 규약")):
        if needle not in _t(path):
            print("❌ 그록 콘티 레인 — {} 가 없다({} · {})".format(why, path, needle)); rc = 1
    # ⑨ 260812 실사고 3축 봉합 — 셋 다 빠져도 영상은 나온다(= 조용히 나빠진다 · 운영자 눈이 유일한 검출기)
    #   ⓐ **참조를 주소로 보내면 xAI 가 우리 저장소를 내려받는다** = 남의 회선 딸꾹질 하나에 한 편이 통째로
    #      죽는다(실측 `image_download_interrupted` · 같은 그림으로 다른 편은 성공 = 그림·주소 정상).
    #      바이트로 실으면 그 다운로드 자체가 사라진다 = 실패 종류의 구조적 소멸.
    #   ⓑ **실패한 그 편만 1회 재시도**(운영자 260812) — 구판 「재시도 0」의 전제(다시 쏘면 돈이 또 나간다)는
    #      실측으로 틀렸다(실패 호출은 청구 0). 성공한 편은 손대지 않는다.
    #   ⓒ **재시도까지 실패하면 웹앱 알림** — 구판은 사유가 `video.json` 안에만 있어 화면 증상이 0이었다
    #      (20초가 나오면 「짧게 나왔나 보다」로 보인다 = 조용히 나빠지는 축).
    #   ⚠ 판정은 **여는 괄호까지** 본다 — bare substring 이면 `def ref_send_OFF` 같은 개명이 그대로
    #      통과한다(첫 킬테스트가 그 구멍을 자기적발했다 · `check_stt_engine_chain` 이 겪은 것과 같은 함정).
    for needle, why in (("REF_EMBED =", "바이트 전송 롤백 레버"),
                        ("RETRY_ONCE =", "실패한 그 편만 1회 재시도"),
                        ("if attempt == 1 and RETRY_ONCE", "재시도 실분기(상수만 있고 안 도는 것 차단)"),
                        ("def notify(", "재시도 초과 실패 = 웹앱 알림"),
                        # ⚠ 재시도 여부로 갈린 2문구가 계약이다(260813 실사고) — 하나로 합치면 재시도한 적
                        #    없는 건에도 「두 번 해봤다」고 단언해 운영자가 다시 쏘기를 포기한다(조치를 막는 거짓말).
                        ("VID_TODO_RETRIED =", "조치주체 규약 👉 문단 · 재시도한 건(없으면 「클로드가 볼 일」로 오분류)"),
                        ("VID_TODO_ONCE =", "조치주체 규약 👉 문단 · 재시도 안 한 건(고정 문구로 합치면 거짓 안내)"),
                        ('if r.get("fail_body")', "창구 회신 원문 동봉(요약만 실으면 우리 파서 결함이 벤더 거절로 오독된다)"),
                        ("notify(stem, items)", "알림 실호출"),
                        ("def pick_refs(", "편마다 시간대에 맞는 배경 참조(밤 컷이 해질녘으로 나온 축)"),
                        ("def is_night(", "밤 축 판정")):
        if needle not in rn:
            print("❌ 그록 콘티 레인 — grok_sb_video.py 에 {} 가 없다({})".format(why, needle)); rc = 1
    # 알림은 **커밋돼야** 화면에 뜬다(messages/ = 빌드 입력) — 한 줄만 빠져도 알림이 러너와 함께 증발한다.
    if "git add messages" not in wf or "\n            messages" not in wf:
        print("❌ 그록 콘티 레인 — sb-make.yml 이 messages/ 를 체크아웃·커밋 안 한다(알림이 러너와 함께 사라진다)"); rc = 1
    if "sb-video-fail-" not in _t("viewer/index.html"):
        print("❌ 그록 콘티 레인 — 뷰어 _rptSrc 에 영상 실패 알림 출처 분기가 없다(리포트가 거짓 상류를 준다)"); rc = 1
    # ⑩ 통로 계약(설계 M3 §2·§3 · 260812) — 러너는 벤더를 직접 부르지 않는다.
    #   ⚠ 왜 하드인가 = 벤더 결합이 직접 5지점 + 간접 10곳으로 흩어져 있던 상태로 두 번째 통로를
    #     붙이면 **한 곳만 빠져도 조용히 다른 동작**이 된다(이 레포 최빈 미러 드리프트 축).
    ln_t, lg_t = _t("shared/lane.py"), _t("shared/lane_grok.py")
    if "class LaneError" not in ln_t or "def pick(" not in ln_t:
        print("❌ 그록 콘티 레인 — shared/lane.py 계약 골격(LaneError·pick)이 없다"); rc = 1
    # ⚠ **등록된 통로를 전부 본다**(손 목록 금지 · 260812 페이블 검증에서 이 게이트가 그록만 보고
    #   시댄스는 한 줄도 안 보던 것이 잡혔다 = 「같은 병의 형제 누락」 축). 새 통로가 LANES 에
    #   등록되면 그 순간부터 같은 계약으로 검사된다 — 조용히 빠질 자리가 없다.
    _lanes = re.findall(r'^\s*"[a-z0-9_]+"\s*:\s*"(lane_[a-z0-9_]+)"', ln_t, re.M)
    if len(_lanes) < 1:
        print("❌ 그록 콘티 레인 — lane.py LANES 등록표를 못 읽었다(자동 발견 실패 = fail-closed)"); rc = 1
    for _mod in _lanes:
        _lt = _t("shared/{}.py".format(_mod))
        if not _lt:
            print("❌ 그록 콘티 레인 — 등록된 통로 shared/{}.py 가 없다".format(_mod)); rc = 1
            continue
        for k in ("NAME", "SHOT_SEC", "SEC_MAX", "RATIOS", "REF_CAP_TECH", "EMBED_MAX",
                  "FAIL_COSTS", "COST_KIND"):
            if k + " =" not in _lt:
                print("❌ 그록 콘티 레인 — 통로 상수 {} 가 {}.py 에 없다(러너가 벤더 값을 직접 들게 된다)"
                      .format(k, _mod)); rc = 1
        for f in ("fresh_token", "refs_payload", "start", "wait", "fetch", "classify",
                  "ref_lock_clause", "ref_id_clause", "sound_clause", "estimate", "too_big"):
            if "def {}(".format(f) not in _lt:
                print("❌ 그록 콘티 레인 — 통로 함수 {}() 가 {}.py 에 없다".format(f, _mod)); rc = 1
    # ⑩-b **상수는 선언이 아니라 배선이다**(260812 페이블 검증 치명 2건) — 두 상수 다 「선언만 있고
    #   읽는 곳 0」이었다. ⓐ COST_KIND 미배선 = 크레딧이 달러 칸에 적혀 화면이 「청구 $195」라고
    #   그것도 실측인 척 말한다 ⓑ FAIL_COSTS 미배선 = 「실패는 공짜」라는 **그록 실측**이 환불
    #   미확인 통로에 그대로 적용돼 이중 청구가 된다(재시도의 주 고객이 「실패로 보이지만 제출은
    #   성공」한 경우라 환불과 무관하게 성공 두 발 값이 나간다).
    for needle, why in (("LANE.FAIL_COSTS is False", "재시도가 실패분 청구 여부를 읽는다"),
                        ("unit=LANE.COST_KIND", "값 원장이 단위를 통로에서 받는다"),
                        ('LANE.COST_KIND == "credit"', "화면·산출 문구가 단위를 가른다"),
                        ("LANE.estimate(", "발사 전 견적 검문(무검문 대량 발사 차단)"),
                        ('rec["job"]', "작업 번호 기록(나간 값의 영수증 = 회수 수단)"),
                        ("LANE.ref_id_clause(", "참조 지목 문법을 통로에서 받는다")):
        if needle not in rn:
            print("❌ 그록 콘티 레인 — grok_sb_video.py 에 {} 가 없다({})".format(why, needle)); rc = 1
    if "unit" not in _t(".github/scripts/sb_cost.py") or 'row["cr" if unit' not in _t(".github/scripts/sb_cost.py"):
        print("❌ 그록 콘티 레인 — 값 원장이 달러·크레딧을 한 칸에 섞는다(환산율 미확인인데 합산 = 거짓 금액)"); rc = 1
    # 벤더 프롬프트 문법이 러너에 되살아나는 것 차단(통로가 일부러 뺀 문법이 러너에서 부활)
    # ⚠ **코드부만 본다** — 이 문법이 왜 통로로 갔는지 설명하는 주석·독스트링은 사고 기록의
    #   거처다(그걸 위반으로 세면 게이트가 자기 처방문을 잡는다 = 첫 실행 자기적발).
    _rn_code = [l for l in _aac_strip_py_docstrings(rn) if not l.strip().startswith("#")]
    if any("<IMAGE_" in l for l in _rn_code):
        print("❌ 그록 콘티 레인 — 러너에 그록 슬롯 문법(<IMAGE_n>)이 박혀 있다(통로 훅 우회)"); rc = 1
    # ⑩-c **빈 값과 없는 값을 같게 다루지 마라**(260812 실사고) — 발사 폼이 「안 정함」을 빈 글자로
    #   보내는데 `os.environ.get("X", "12")` 는 **빈 글자를 그대로 돌려준다**(없을 때만 기본값). 그
    #   빈 글자가 숫자 변환에 들어가면 러너가 첫 줄에서 죽고, 그 줄은 함수 밖이라 fail-soft 그물에도
    #   안 걸린다 = 콘티·참조 그림은 다 나오고 **영상만 0편**(화면 증상은 「그냥 안 나옴」 하나뿐).
    for _p in ["shared/{}.py".format(m) for m in _lanes] + [".github/scripts/grok_sb_video.py"]:
        for _ln in _t(_p).splitlines():
            if re.search(r'int\(os\.environ\.get\(\s*["\'][^"\']+["\']\s*,', _ln) and not _ln.strip().startswith("#"):
                print("❌ 그록 콘티 레인 — 빈 값이 숫자 변환으로 새는 줄({}): {}".format(_p, _ln.strip()[:80]))
                print("   · 「빈 값이면 기본값」으로 = os.environ.get(\"X\") or \"12\"")
                rc = 1
    # ⑩-d **회전 열쇠를 쓰는 워크플로는 한 줄로 선다**(260812 실사고 + 8렌즈 검증) — 이 열쇠들은
    #   쓸 때마다 새것으로 바뀌고 옛것이 죽는다. 두 판이 겹치면 창구가 도난으로 보고 **사슬을
    #   통째로 무효화**하고, 그 뒤로는 사람이 브라우저로 다시 로그인해야만 산다.
    #   ⚠ 러너 안 파일 잠금은 **러너 사이를 못 건넌다**(판마다 새 기계 · 저장소 비밀값은 값 읽기
    #     자체가 불가하고 되쓰기만 된다) → 순서를 워크플로 층에서 세우는 것이 유일한 구조 해다.
    #   자동 발견 = 그 비밀값을 env 로 받는 워크플로 전부(새 워크플로가 조용히 빠질 자리가 없다).
    import glob as _g4
    for _wf in sorted(_g4.glob(os.path.join(ROOT, ".github", "workflows", "*.yml"))):
        _wt = _t(os.path.relpath(_wf, ROOT))
        _keys = [k for k in ("XAI_REFRESH_TOKEN", "HIGGSFIELD_REFRESH_TOKEN")
                 if re.search(r"^\s*[A-Z_]+:\s*\$\{\{\s*secrets\." + k, _wt, re.M)]
        if not _keys:
            continue
        _grp = re.search(r"^concurrency:\s*\n\s+group:\s*(.+)$", _wt, re.M)
        if not _grp:
            print("❌ 그록 콘티 레인 — {} 가 회전 열쇠({})를 쓰는데 순서를 안 세운다"
                  "(두 판이 겹치면 열쇠 사슬이 통째로 죽는다)".format(os.path.basename(_wf), ", ".join(_keys)))
            rc = 1
        elif "-key" not in _grp.group(1):
            print("❌ 그록 콘티 레인 — {} 의 순서 그룹이 열쇠 축이 아니다: {}"
                  .format(os.path.basename(_wf), _grp.group(1).strip()[:70]))
            rc = 1
    # 되쓰기 실패는 **알림으로 나간다**(실패해도 런이 초록이라 다음 판이 확정으로 죽던 자리)
    _gk = _t("shared/grok_api.py")
    if "def _persist_alarm(" not in _gk or "👉" not in _gk:
        print("❌ 그록 콘티 레인 — 열쇠 되쓰기 실패 알림이 없다(런은 초록인데 다음 발사가 죽는다)"); rc = 1
    if "if not _persist_secret(rt)" not in _gk:
        print("❌ 그록 콘티 레인 — 되쓰기 결과를 버린다(실패가 어디에도 안 남는다)"); rc = 1
    # ⑩-e **관측 3종**(운영자 260813 「각 파이프라인이 제대로 돌고있는지 검증이 안되네」) —
    #   ⓐ 무엇을 소재로 짰나 ⓑ 인용한 연출 모듈이 실재하나 ⓒ 창구로 나간 문장이 무엇이었나.
    #   셋 다 없어도 콘티는 나오고 영상도 나온다 = 지워져도 화면 증상이 0이라, 다음 세션이
    #   추측으로 메우게 된다(이 레포가 반복해 데인 자리).
    if 'printf \'%s\' "${STORY}" > "$OUTDIR/source.md"' not in _t(".github/scripts/sbmake.sh"):
        print("❌ 그록 콘티 레인 — 이야기 소재를 산출에 안 남긴다(무엇으로 짰는지 확인 불가)"); rc = 1
    if "def cited(" not in _t(".github/scripts/sb_audit.py"):
        print("❌ 그록 콘티 레인 — 콘티 검증기(.github/scripts/sb_audit.py)가 없다"); rc = 1
    if "sb_audit.py" not in wf:
        print("❌ 그록 콘티 레인 — 워크플로에 콘티 검증 스텝이 없다(지어낸 모듈이 통과한다)"); rc = 1
    if 'rec["prompt"] = pr' not in rn:
        print("❌ 그록 콘티 레인 — 창구로 나간 문장을 산출에 안 남긴다(왜 그렇게 그렸는지 추론만 남는다)"); rc = 1
    # 자격은 **편마다** 새로 받는다(열쇠 수명 < 한 편 대기 시간이면 뒤쪽 편이 자격 축으로 죽는다)
    _loop = rn.split("for c in shots:", 1)[-1]
    if "LANE.fresh_token()" not in _loop:
        print("❌ 그록 콘티 레인 — 편마다 자격을 갱신하지 않는다(긴 대기에서 열쇠가 먼저 죽는다)"); rc = 1
    # 러너가 벤더를 **직접** 부르면 계약이 뚫린 것이다(주석 줄 제외 = 사고 기록의 거처)
    _vend = [l for l in rn.splitlines()
             if ("gk." in l or "grok_api" in l) and not l.strip().startswith("#")]
    if _vend:
        print("❌ 그록 콘티 레인 — 러너가 벤더를 직접 부른다(통로 계약 우회 · %d줄):" % len(_vend)); rc = 1
        for l in _vend[:3]:
            print("   ·", l.strip()[:90])
    # 러너 분기는 예외 **3속성**으로만 갈린다(벤더 필드 직독 = 통로 갈아끼우면 조용히 무력화)
    for bad, why in (("e.tier_blocked", "자격 축을 벤더 필드로 직독"),
                     ("e.dead_auth", "자격 축을 벤더 필드로 직독"),
                     ("_retryable(e)", "재시도 술어를 러너가 들고 있다")):
        if bad in rn:
            print("❌ 그록 콘티 레인 — 러너가 {}(통로 무관 3속성으로 갈려야 한다 · {})".format(why, bad)); rc = 1

    # ⚠ 비율 = 콘티가 선언하는데 러너가 안 읽던 축(260812 발견) — 참조 그림은 세로로 굽고
    #   영상만 가로로 나가던 상태였다. 쇼츠(세로)가 산출 규격이면 그대로 사고다.
    for needle, why in (("def ratio_of(", "콘티 선언 비율 판독"),
                        ("ratio = ratio_of(md)", "비율 실판독"),
                        ('"ratio": ratio', "발사 비율 전달")):
        if needle not in rn:
            print("❌ 그록 콘티 레인 — grok_sb_video.py 에 {} 가 없다({} · 콘티가 세로라 적어도 가로로 나간다)".format(why, needle)); rc = 1
    if "배경(밤)" not in _t("prompts/sb-make.md"):
        print("❌ 그록 콘티 레인 — 콘티 규약에 밤 배경 참조 축이 없다(밤 컷이 참조 시간대에 끌려간다)"); rc = 1

    # ⑧ 열쇠 회전 = 러너 밖으로 살려 보내는 배선(없으면 두 번째 발사가 죽는다 · 260811 실사고)
    if "_persist_secret" not in _t("shared/grok_api.py"):
        print("❌ 그록 콘티 레인 — 갱신 열쇠 되쓰기(_persist_secret)가 없다 = 한 번만 쏠 수 있다"); rc = 1
    if "XAI_SECRET_PAT" not in wf:
        print("❌ 그록 콘티 레인 — 워크플로가 XAI_SECRET_PAT 을 안 넘긴다(되쓰기가 배선만 있고 못 돈다)"); rc = 1

    # ⚠ 연출 라이브러리(카메라 각도·수사학 54챕터)를 콘티가 훑는가 — 프롬프팅 탭과 뉴스 썸네일은
    #   쓰는데 **콘티 경로만 안 봤다**(260812 실측). 배선이 빠져도 콘티는 멀쩡히 나오므로
    #   조용히 낡는 축이다(운영자 눈이 유일한 검출기 = 이 레포 반복 사고).
    _sb = _t("prompts/sb-make.md")
    for needle, why in (("apps/k/library/00_module_index.tsv", "라이브러리 인덱스 진입점"),
                        ("전체 로드 금지", "통Read 차단(54챕터 1.8MB)"),
                        ("13_style_news_canon", "뉴스 비평 축 지목")):
        if needle not in _sb:
            print("❌ 그록 콘티 레인 — sb-make.md 에 {} 가 없다({})".format(why, needle)); rc = 1
    # ⚠ 입력 2칸(요약·지시) — 둘 다 비면 발사가 막혀야 하고, 둘 중 하나만 와도 콘티는 나와야 한다.
    #   한 축만 빠져도 화면은 멀쩡하다(칸은 보이고 버튼도 눌린다) → 정적 생존으로 강제한다.
    for needle, why in (('id="sumTx"', "요약 입력칸"),
                        ('id="sumPull"', "기사 요약 끌어오기"),
                        ("articles.json", "요약 출처(분석 완료 기사 목록)"),
                        ("function sbFireGate", "둘 다 비면 발사 잠금"),
                        ("[기사 요약 — 참고 자료]", "요약·지시 구분 표기")):
        if needle not in vt:
            print("❌ 그록 콘티 레인 — sb.html 에 {} 가 없다({})".format(why, needle)); rc = 1
    if "[기사 요약 — 참고 자료]" not in _sb:
        print("❌ 그록 콘티 레인 — sb-make.md 가 입력 2칸 구조를 모른다(요약을 지시로 읽는다)"); rc = 1

    if not os.path.exists("apps/k/library/00_module_index.tsv"):
        print("❌ 그록 콘티 레인 — 라이브러리 인덱스 파일이 없다(경로 리네임?)"); rc = 1

    if "MOTION 3계약" not in _t("prompts/sb-make.md"):
        print("❌ 그록 콘티 레인 — sb-make.md 에 MOTION 3계약이 없다(대명사·무인 컷·세트 조각)"); rc = 1

    # ④-b **각을 먼저 잡는 절차**(운영자 260813 「페이블이 아무 것도 없는 제로베이스에서도 그렇게
    #   생각하도록」) — 라이브러리는 방대한데 전부 **컷 단위 도구**라 「작품 하나를 무슨 구조로
    #   비꿀 것인가」는 기댈 데가 없었고, 입력이 각을 안 주면 콘티가 **기사 삽화**로 떨어졌다.
    #   ⚠ 왜 게이트인가 = 지침만 고치고 검사를 안 두면 지켜졌는지 아무도 모른다. 그리고 이 축은
    #     빠져도 콘티가 멀쩡히 나온다(그냥 밋밋해질 뿐) = 운영자 눈이 유일한 검출기가 된다.
    _cs_tsv = "apps/k/library/48_commentary_structures.tsv"
    if not os.path.exists(_cs_tsv):
        print("❌ 그록 콘티 레인 — 논평 구조 표가 없다({})".format(_cs_tsv)); rc = 1
    else:
        _cs_ids = {ln.split("\t", 1)[0].strip() for ln in _t(_cs_tsv).splitlines()[1:] if ln.strip()}
        if len([i for i in _cs_ids if i.startswith("CS-")]) < 3:
            print("❌ 그록 콘티 레인 — 논평 구조 표가 사실상 비었다(CS 항목 3개 미만 = 고를 게 없다)"); rc = 1
        if "48_commentary_structures" not in _t("apps/k/library/00_module_index.tsv"):
            print("❌ 그록 콘티 레인 — 논평 구조 표가 라이브러리 인덱스에 미등재(감독이 못 찾는다)"); rc = 1
    for needle, why in (("모순 한 쌍", "0-a 모순 쌍 추출"),
                        ("48_commentary_structures", "0-b 구조 표 지목"),
                        ("논평 구조:", "0-c 고른 이유 남기기"),
                        ("그림으로 옮긴 것에 지나지", "0-d 자기검문")):
        if needle not in _sb:
            print("❌ 그록 콘티 레인 — sb-make.md 에 {} 가 없다({})".format(why, needle)); rc = 1
    # ④-c **없는 작업을 기다리지 않는다**(운영자 260813 「재발하지 않게 해 줘」).
    #   실사고 = 발사 회신에서 집은 번호가 창구에 없는 값이었는데(회신이 글로 오면 번호 파서가
    #   글 속 아무 UUID 나 집는다) 러너가 그걸 모르고 상한까지 기다렸다(실측 50분). 그동안
    #   로그·산출은 「큐가 밀린 상태다」라고 말했다 — **증상과 원인이 정반대인 오진**이라
    #   다음 세션이 큐 탓을 하며 또 기다린다. 값은 안 나갔는데 시간만 통째로 태운다.
    #   ⚠ 왜 게이트인가 = 세 부품 중 하나만 빠져도 **화면 증상이 0이다**(그냥 오래 기다릴 뿐).
    _ls = _t("shared/lane_seedance.py")
    _gv = _t(".github/scripts/grok_sb_video.py")
    for needle, why, where, txt in (
            ("def alive(", "접수 실존 확인 함수", "lane_seedance.py", _ls),
            ("def _status_of(", "상태 읽는 자 한 벌(기계값·글자 표 공용)", "lane_seedance.py", _ls),
            ("cols[2]", "표에서 **그 작업 줄의 상태 칸**만 읽기(집계 숫자를 상태로 읽던 오작동 봉합)", "lane_seedance.py", _ls),
            ("LANE.alive(", "기다리기 전 접수 확인 호출", "grok_sb_video.py", _gv)):
        if needle not in txt:
            print("❌ 그록 콘티 레인 — {} 에 {} 가 없다({})".format(where, why, needle)); rc = 1
    # ④-e **촬영은 2차에서만 돈다**(운영자 260813 「생성 버튼은 총 2번」).
    #   ⚠ 구판은 1차 전송에서도 영상까지 쐈다 — 콘티를 보기도 전에 값이 나갔다(30초면 195 크레딧).
    #     운영자가 정한 순서의 **앞쪽 절반이 배선에서 통째로 빠져 있었다**(화면엔 버튼이 둘인데
    #     서버·워크플로는 한 번에 끝까지 갔다 = 화면과 실제가 다른 가장 비싼 어긋남).
    #   ⚠ 표식은 이미 있는 값으로 읽는다(손입력 칸 10/10 소진) — 이야기가 비고 기준 콘티가
    #     있으면 2차. 같은 술어를 「콘티 재사용」 스텝이 이미 쓴다(자 두 벌 금지).
    _wf = _t(".github/workflows/sb-make.yml")
    import re as _re
    for _nm in ("Grok video", "Seedance video", "Motion render"):
        _i = _wf.find("- name: {}".format(_nm))
        if _i < 0:
            print("❌ 그록 콘티 레인 — sb-make.yml 에 「{}」 스텝이 없다".format(_nm)); rc = 1; continue
        _seg = _wf[_i:_i + 900]
        _m = _re.search(r"^\s*if:\s*(.+)$", _seg, _re.M)
        _cond = _m.group(1) if _m else ""
        if "inputs.story == ''" not in _cond or "inputs.base != ''" not in _cond:
            print("❌ 그록 콘티 레인 — 「{}」 가 1차에서도 돈다(2차 표식 없음 · 지금 조건 = {})"
                  .format(_nm, _cond[:90])); rc = 1

    # ④-f **참조 그림 전달 실패는 방식을 갈아탄다**(260814 실측 = 폐버스 1편이 두 번 다 그 자리).
    #   창구가 「우리 그림을 못 받았다」고 답하면 같은 방식으로 다시 쏴도 같은 자리에서 또 끊긴다.
    #   몸집 거절이 「바이트 → 주소」로 갈아타는 것과 **거울**이라, 짝이 없으면 회선이 한 번
    #   흔들린 편은 영영 못 살린다. ⚠ 화면 증상은 「그 편만 없음」이라 원인이 안 보인다.
    for _mod2 in _lanes:   # 등록된 통로 전부(손 목록 금지 = 위 자동 발견 재사용)
        if "def ref_unfetched(" not in _t("shared/{}.py".format(_mod2)):
            print("❌ 그록 콘티 레인 — shared/{}.py 에 ref_unfetched( 가 없다(통로 무관 계약)".format(_mod2)); rc = 1
    if "LANE.ref_unfetched(" not in _gv:
        print("❌ 그록 콘티 레인 — 러너가 참조 전달 실패로 방식을 안 갈아탄다(몸집 거절의 거울이 없다)"); rc = 1
    if "buf.tell() > EMBED_MAX" not in _t("shared/lane_grok.py"):
        print("❌ 그록 콘티 레인 — 참조를 줄인 뒤 크기를 다시 안 잰다(줄여도 넘는 그림을 그대로 싣는다)"); rc = 1

    # ④-d **창구의 되물음에 답을 쥐고 있어야 한다**(260813 실사고 · 회신 원문 실측).
    #   창구는 발사 대신 「이 프리셋 어때요」로 되물을 수 있다(`Submitted 0/1 … declined_preset_id=…`).
    #   사람이 보고 있으면 「아니요」를 누르는 자리인데 러너엔 사람이 없어서, 구판은 그 되물음을
    #   성공으로 읽고 없는 작업을 상한까지 기다렸다 — 값도 산출도 0인데 로그는 「큐 대기」였다.
    #   ⚠ `use_unlim` 명시와 **같은 축**이다: 사람 없는 통로는 되물음마다 답이 미리 있어야 한다.
    for needle, why in (("_declined_preset", "프리셋 되물음 판정"),
                        ("declined_preset_id", "사양 인자 전달"),
                        ("submitted 0/", "실패 회신에서 번호 줍기 금지")):
        if needle not in _ls:
            print("❌ 그록 콘티 레인 — lane_seedance.py 에 {} 가 없다({})".format(why, needle)); rc = 1

    # 순서도 계약이다 — 확인이 기다리기 **뒤**에 있으면 50분을 그대로 기다린 다음에 안다.
    if "LANE.alive(" in _gv and "LANE.wait(" in _gv and _gv.index("LANE.alive(") > _gv.index("LANE.wait("):
        print("❌ 그록 콘티 레인 — 접수 확인이 기다리기보다 뒤에 있다(기다린 뒤에 알면 의미가 없다)"); rc = 1

    _au = _t(".github/scripts/sb_audit.py")
    for needle, why in ("_CS_LINE", "논평 구조 줄 판정"), ("def structure", "구조 실재 대조"), ('"structure_id"', "산출 박제"):
        if needle not in _au:
            print("❌ 그록 콘티 레인 — sb_audit.py 에 {} 가 없다({})".format(why, needle)); rc = 1

    # ⑤ 감독 지침 = MOTION(영어 동작 줄) 규약. 빠지면 프롬프트가 한국어로 나간다.
    sh = _t(".github/scripts/sb_sheet.py")
    for needle, why in (("def sheet_prompt", "시트 프롬프트 조립"),
                        ("gi.openai_image", "GPT Image 호출(1순위)"),
                        ("tg.gemini_image", "제미나이 폴백(2순위 · 260811 실측 = OPENAI 키 없으면 시트 0장)"),
                        ("from grok_sb_video import cuts_of", "컷 파서 단일정본(사본 0)")):
        if needle not in sh:
            print("❌ 그록 콘티 레인 — sb_sheet.py 에 {} 가 없다({})".format(why, needle)); rc = 1
    # 폴백이 살아 있어도 워크플로가 열쇠를 안 넘기면 그 자리에서 죽는다(같은 병의 짝)
    if "GEMINI_API_KEY" not in wf.split("name: Storyboard sheet", 1)[-1].split("name: Grok video", 1)[0]:
        print("❌ 그록 콘티 레인 — 시트 스텝이 GEMINI_API_KEY 를 안 받는다(폴백이 배선만 있고 못 돈다)"); rc = 1

    if "MOTION:" not in _t("prompts/sb-make.md"):
        print("❌ 그록 콘티 레인 — prompts/sb-make.md 에 MOTION 규약이 없다(영상 프롬프트가 한국어로 나간다)"); rc = 1

    if rc == 0:
        print("✅ 그록 콘티 레인 — 5층 생존(뷰어 칩·서버 전달·워크플로 스텝·러너 골격·감독 MOTION 규약) · 소리 4층 정합.")
    return rc


def check_edit_track_chain():
    """편집 생성 = 자동 가림·키잉·크로마키 게이트(하드 · 운영자 260808 "모자이크 누르고 옵션 선택한 다음에 생성 누르면
    트래킹해서 모자이크까지 자동으로"). ⚠ 신설 사유 = **이 축은 화면이 멀쩡한 채로 조용히 죽는다** — 260808 이전 상태가
    정확히 그랬다: 편집 폼의 추가 옵션(모자이크·키잉·크로마키)은 토글이 켜지고 세부 게이지까지 그려지는데 발사 페이로드엔
    안 실려서, 생성을 눌러도 **아무 일도 안 일어났다**(오류도 안 뜬다 = 운영자 눈이 유일한 검출기). 층이 4개라 어느 하나만
    빠져도 같은 무증상 사고로 되돌아간다 = 정적 층별 생존 강제.
    체인: 뷰어 xtrOpts()→buildOpts o.xtr → api/edit.js 화이트리스트(+발사 게이트 유효 인정) → edit_track.py → edit-make.yml 2스텝.
    ⑤ = 크로마키 강도 단위 회귀 차단(실측 사고 = 뷰어 1~50%를 0.01~0.5로 클램프해 전 구간 0.5 = 화면 전체 소거)."""
    rc = 0
    try:
        vw = open(os.path.join(ROOT, 'viewer', 'edit.html'), encoding='utf-8').read()
        ae = open(os.path.join(ROOT, 'functions', 'api', 'edit.js'), encoding='utf-8').read()
        at = open(os.path.join(ROOT, 'functions', 'api', 'track.js'), encoding='utf-8').read()
        et = open(os.path.join(ROOT, '.github', 'scripts', 'edit_track.py'), encoding='utf-8').read()
        wf = open(os.path.join(ROOT, '.github', 'workflows', 'edit-make.yml'), encoding='utf-8').read()
        lb = open(os.path.join(ROOT, '.github', 'scripts', 'ly_burn.py'), encoding='utf-8').read()
    except Exception as e:
        print('❌ 편집 자동 가림 체인 게이트 — 층 파일 결손:', e)
        return 1
    checks = [
        ('① 뷰어 송신', 'function xtrOpts(' in vw and 'o.xtr=xo' in vw and '!xtrOpts()' in vw),   # 셋째 = **뷰어 발사 게이트**가 xtr 단독을 유효로 인정(빠지면 ORDER 검사에서 "처리를 하나는 넣어줘"로 막혀 서버에 도달조차 못 한다 — 실측 260808: 서버 게이트만 고치고 이걸 빠뜨려 주 시나리오가 통째로 거절됐다)
        ('② api 화이트리스트', 'opts.xtr = xt' in ae and '!opts.xtr' in ae),   # 후자 = 서버 발사 게이트의 같은 축(①과 한 쌍 — 한쪽만 고치면 여기서 막히거나 저기서 400)
        ('③ 러너 스크립트 골격', all(k in et for k in ('def norm_xtr', 'LOCAL_OUT', 'track_analyze.py', 'track_render.py', 'ly_out'))),
        ('④ 워크플로 배선', _has_exec_line(wf, '.github/scripts/edit_track.py') and 'apps/track' in wf and 'ly_final_path.txt' in wf
            and 'EDIT_SRC' in wf.split('edit_track.py')[0].rsplit('자동 가림 적용', 1)[-1]),   # 원본 폴백 = 실효 조건(가림만 켜면 편집 축이 0이라 ly_burn이 합성물을 안 만든다 → 폴백이 없으면 그 자리에서 조용히 스킵 = 주 시나리오 무동작)
        ('⑤ 컴포즈 산출 도장', 'ly_final_path.txt' in lb),   # 후속 스텝의 입력 앵커 — 빠지면 폴백 경로 추정에 의존(음량 통일 분기로 경로가 갈린다)
        ('⑥ 크로마 강도 단위', 'o.similarity > 1' in at),   # 구판 직접 클램프 부활 = 크로마키 전면 무동작 회귀
        ('⑦ pre/post 2단계 + 순서', _edit_track_phase_ok(wf, et)),   # 픽셀 번인은 자막보다 **먼저** — 아래 헬퍼가 스텝 순서까지 본다
    ]
    for name, ok in checks:
        if not ok:
            print('❌ 편집 자동 가림 체인 게이트 — %s 결손(한 층만 빠져도 옵션이 켜지는데 생성엔 아무 일이 안 생긴다)' % name)
            rc = 1
    if rc == 0:
        print('✅ 편집 자동 가림 체인 게이트 — 6축(뷰어 송신→api→러너→워크플로→산출 도장→크로마 단위) 전 층 생존.')
    return rc
def check_smoke_obs_chain():
    """UI 스모크 관측·알림 체인 게이트(하드 · 운영자 260807 "알림 메세지에 그 내용이 쌓이게 ·
    웹앱 푸쉬알림까지는 안오게 · 다운로드해서 클코에 전달하면 개선할 수 있도록").

    ⚠️ 신설 사유 = **사유 0자 경보가 8일 연속 무증상으로 살았다**(260731~0807 실측 · 나이틀리 런
       8건 전건 failure). 구판 smoke-nightly.yml 은 `grep -E '^❌' smoke.log` 로 실패 사유를 뽑았는데
       **스모크 24종 중 15종이 ❌ 를 한 번도 안 쓰고** smoke_all 요약줄도 `──` 로 시작해 매치가 0이었다
       → 산출물이 {"rc":1,"fail":""} 가 되고 watchdog ⑥ 이 그 빈 칸을 그대로 발화해
       「UI 스모크 FAIL(rc=1) —  」만 나갔다. **감지는 정확했는데 무엇이 실패했는지가 어디에도 없어서**
       운영자가 조치할 수 없었다 = 이 레포가 반복해 겪은 「관측이 구조적으로 지워지는 병」과 같은 축
       (스레드 `[1차 실측]` · 틱톡 `_e1` · 요약실패 `_fk=code`).
    기존 게이트는 전부 다른 축이다 — check_refs 계열 = 정적 **문자열·경로 실존** · smoke_* = **화면 렌더**
       → 「경보가 **사유를 갖고 나가는가**」는 축 자체가 없었다.

    4축 = ① 나이틀리가 정본 파서를 실행줄로 호출(구판 `^❌` grep 부활 = 차단)
          ② **정본 함수 재판정** — smoke_obs.summarize 를 import 해 rc≠0 4케이스에서 사유가
             0자가 아님을 실제로 확인(사전·정규식 사본 0 · 네트워크·LLM·렌더 0)
          ③ watchdog 진단서·메시지함 점등 배선(_smoke_report + wd-smoke set/clear)
          ④ 웹푸시 면제 배선(PUSH_EXEMPT 에 smoke ∧ due 계산이 그것을 참조) — 면제가 조용히 풀리면
             운영자가 다시 조치 불가 푸시를 받는다."""
    y = os.path.join(ROOT, '.github', 'workflows', 'smoke-nightly.yml')
    o = os.path.join(ROOT, '.github', 'scripts', 'smoke_obs.py')
    w = os.path.join(ROOT, 'scraper', 'watchdog.py')
    bad = []
    try:
        yt = open(y, encoding='utf-8').read()
        wt = open(w, encoding='utf-8').read()
        if not os.path.exists(o):
            raise FileNotFoundError(o)
    except Exception as e:   # noqa: BLE001 — 앵커 파일 소실 = fail-closed
        print(f"❌ [smoke-obs] 체인 파일 읽기 실패: {e}")
        return 1
    # ① 나이틀리 배선 + 구판 문법 부활 차단
    if not _has_exec_line(yt, 'smoke_obs.py'):
        bad.append('smoke-nightly.yml 이 .github/scripts/smoke_obs.py 를 실행줄로 호출하지 않는다(사유 추출 정본 미배선)')
    if _has_exec_line(yt, "grep -E '^❌'"):
        bad.append("smoke-nightly.yml 에 구판 사유 추출(grep -E '^❌') 부활 — 스모크 24종 중 15종이 ❌ 를 안 써 사유가 빈다")
    # ② 정본 함수 재판정 — 어떤 실패 입력에도 사유 0자가 나오면 안 된다(fail-closed 계약)
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location('_smoke_obs_gate', o)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        cases = [
            ('빈 로그', ''),
            ('요약줄만', '── smoke_all FAIL ( a=1 ) · [*] = 1차 병렬 FAIL'),
            ('사유 없는 블록', '════ a (rc=1) ════\n\n── smoke_all FAIL ( a=1 )'),
            ('전 종목 rc=0인데 rc≠0', '════ a (rc=0) ════\nok'),
        ]
        for name, log in cases:
            jobs, failed, flaky, details = m.parse(log)
            why = m.summarize(1, jobs, failed, flaky, details, log)
            if not str(why).strip():
                bad.append(f'smoke_obs.summarize 가 「{name}」 입력에서 사유 0자 반환 — 빈 사유 금지 계약 위반')
    except Exception as e:   # noqa: BLE001
        bad.append(f'smoke_obs 재판정 실패({type(e).__name__}: {e}) — 파서 정본 손상')
    # ③ 진단서·메시지함 점등
    if 'def _smoke_report(' not in wt:
        bad.append('watchdog.py 에 _smoke_report(진단서 본문) 정의 없음 — 메시지함이 한 줄만 받는다')
    if not _has_exec_line(wt, "'wd-smoke'") and not _has_exec_line(wt, '"wd-smoke"'):
        bad.append('watchdog.py 가 메시지함 슬롯 wd-smoke 를 점등/해제하지 않는다')
    if not _has_exec_line(wt, '_smoke_report('):
        bad.append('watchdog.py 점등부가 _smoke_report 를 쓰지 않는다 — 진단서가 아니라 한 줄만 나간다')
    # ④ 웹푸시 면제(운영자 260807) — 면제가 풀리면 조치 불가 푸시가 되살아난다
    if not re.search(r"PUSH_EXEMPT\s*=\s*\{[^}]*['\"]smoke['\"]", wt):
        bad.append("watchdog.py PUSH_EXEMPT 에 'smoke' 없음 — UI 스모크가 다시 웹푸시를 탄다")
    if 'PUSH_EXEMPT' not in (re.search(r'due\s*=\s*\{.*?\}', wt, re.S).group(0) if re.search(r'due\s*=\s*\{.*?\}', wt, re.S) else ''):
        bad.append('watchdog.py due(웹푸시 대상) 계산이 PUSH_EXEMPT 를 참조하지 않는다 — 면제 사문화')
    if bad:
        print('❌ [smoke-obs] UI 스모크 관측·알림 체인 결손:')
        for b in bad:
            print(f'   · {b}')
        return 1
    print('✅ [smoke-obs] 스모크 사유 기록·진단서 점등·푸시 면제 체인 정상')
    return 0


def check_stt_engine_chain():
    """STT 엔진 교체 계약 게이트(하드 · 운영자 260808 "위험 점검 다 반영" · 평의회 8인 후속).

    260808에 STT 기본 엔진을 로컬 large-v3 → ElevenLabs Scribe v2(+폴백)로 바꾸며 **손으로 복사한 계약이
    10군데 넘게** 생겼다(5워크플로 env 2줄 · prefetch 게이트 · 폴백 · 캐시 키 · 폰트 검문 · sparse 전제).
    ⚠️ 이 축은 전부 **주석으로만** 선언돼 있었다 = 이 레포가 반복해 겪은 「강제 없는 선언은 조용히 낡는다」
       (check_contract_anchors 가 이름 붙인 병). 그리고 한 층만 빠져도 **화면은 멀쩡한 채** 이렇게 죽는다:
         ⓐ env 2줄 누락 → 그 파이프만 조용히 whisper 로 돈다(느려질 뿐 산출은 나온다)
         ⓑ prefetch 게이트 누락 → 매 런 3.1GB 신규 다운(= 최적화의 정반대 · 260808 실사고 news-ask)
         ⓒ 폴백 try 제거 → 벤더 스키마 한 번 흔들리면 자막 파이프 전체 사망
         ⓓ 캐시 키 엔진 축 제거 → 구 whisper 전사 재사용 = 승격 무효 + 킬스위치가 거짓말
         ⓔ 폰트 검문 완화 → libass 가 에러 없이 두부(□)로 굽는다
         ⓕ 무경로 `git add -A` 유입 → sparse-checkout 잡이 cone 밖 1만 파일을 삭제 커밋한다
    판정 = 정적(렌더·LLM·네트워크 0) · 면책표 없이 하드 0."""
    bad = []
    wf = os.path.join(ROOT, '.github', 'workflows')

    def _read(fp):   # ⚠ 전역 헬퍼가 아니라 지역 정의 — 이 파일의 _read 는 다른 게이트 안에 갇혀 있다(실측)
        try:
            with open(fp, encoding='utf-8') as f:
                return f.read()
        except OSError:
            return ''

    # ① STT 5경로가 키·엔진 env 를 보유 (누락 = 그 파이프만 조용히 whisper)
    for name in ('ly-make.yml', 'edit-make.yml', 'nb-make.yml', 'news-ask.yml', 'vidl-make.yml'):
        t = _read(os.path.join(wf, name))
        # ⚠ bare substring 금지(킬테스트 자기적발) — `ELEVENLABS_API_KEY_X` 같은 개명이 그대로 통과했다.
        #   YAML 키 형태(`이름:`)로 못박는다.
        if 'ELEVENLABS_API_KEY:' not in t or 'LY_STT_ENGINE:' not in t:
            bad.append('%s: STT env 2줄(ELEVENLABS_API_KEY·LY_STT_ENGINE) 누락' % name)

    # ② apps/ly/setup.sh 호출부는 prefetch 를 명시한다(runner-setup 주입 ∨ 자체 판정)
    #    ⚠ 260808 실사고 = ask_link_stt.sh 가 runner-setup 밖에서 재호출해 기본값 true 로 떨어졌다.
    for rel in ('.github/scripts/ask_link_stt.sh',):
        t = _read(os.path.join(ROOT, *rel.split('/')))
        if 'apps/ly/setup.sh' in t and 'LY_WHISPER_PREFETCH=' not in t:
            bad.append('%s: setup.sh 호출에 LY_WHISPER_PREFETCH 미명시(매 런 3.1GB 신규 다운)' % rel)
    act = _read(os.path.join(ROOT, '.github', 'actions', 'runner-setup', 'action.yml'))
    if 'LY_WHISPER_PREFETCH:' not in act:
        bad.append('runner-setup/action.yml: whisper 입력을 setup.sh 로 주입하는 줄 소실')
    setup = _read(os.path.join(ROOT, 'apps', 'ly', 'setup.sh'))
    if 'LY_WHISPER_PREFETCH:-' not in setup:
        bad.append('apps/ly/setup.sh: prefetch 게이트 소실(캐시 없이 3.1GB 다운)')

    # ③ 폴백 계약 = 조립 예외까지 감싼다 + 폴백 사유가 표면화된다 + 언어 추측 폴백은 부활 금지
    st = _read(os.path.join(ROOT, '.github', 'scripts', 'ly_stt.py'))
    for sym, why in (('def _fb(', '폴백 사유 표면화 함수'),
                     ('except Exception as _e:', '조립 예외 폴백(파이프 사망 차단)'),
                     ('_load_whisper', 'large-v3 폴백 경로')):
        if sym not in st:
            bad.append('ly_stt.py: %s 소실 — %s' % (sym, why))
    if '_L3.get(c, c[:2])' in st:
        bad.append('ly_stt.py: 언어 앞2자 추측 폴백 부활(jav→ja 자바어=일본어 오진 = 자막 어절 전부 붙음)')

    # ④ STT 캐시 키가 엔진을 담는다(구 whisper 전사 재사용·킬스위치 거짓 차단)
    cc = _read(os.path.join(ROOT, '.github', 'scripts', 'stt_cache.py'))
    if 'def _engine_tag(' not in cc or 'scribe_v2' not in cc:   # ⚠ 정의 형태로 판정(개명 통과 차단)
        bad.append('stt_cache.py: 캐시 키 엔진 축 소실(승격 무효 + 킬스위치 거짓)')

    # ⑤ 번인 폰트 하드게이트 = noto ∧ nanum 둘 다(한쪽만 보면 style=nanum/pen 이 두부로 샌다)
    ly = _read(os.path.join(wf, 'ly-make.yml'))
    if ly.count('noto sans cjk') < 2 or 'grep -qi "nanum"' not in ly:
        bad.append('ly-make.yml: 번인 폰트 검문(noto ∧ nanum) 완화 — 두부(□) 번인 위험')

    # ⑥ sparse-checkout 안전 전제 = 무경로 `git add -A` / `git add .` 0건
    #    (경로 지정형 `git add -A messages` 는 정상 — cone 밖을 건드리지 않는다)
    import re as _re
    pat = _re.compile(r'^\s*git add\s+(-A|\.)\s*(?:$|[#;&|])')
    for d in (wf, os.path.join(ROOT, '.github', 'scripts')):
        for fn in sorted(os.listdir(d)) if os.path.isdir(d) else []:
            if not fn.endswith(('.yml', '.yaml', '.sh')):
                continue
            for i, ln in enumerate(_read(os.path.join(d, fn)).split('\n'), 1):
                if ln.lstrip().startswith('#'):
                    continue
                if pat.search(ln):
                    bad.append('%s:%d 무경로 `git add %s` — sparse-checkout 잡이 cone 밖을 삭제 커밋한다'
                               % (fn, i, '-A' if '-A' in ln else '.'))
    if bad:
        print('❌ STT 엔진 계약 게이트:')
        for b in bad:
            print('   · %s' % b)
        return 1
    print('✅ STT 엔진 계약 게이트 — 5경로 env · prefetch 게이트 · 폴백 3심볼 · 캐시 엔진축 · 폰트 2중검문 · 무경로 add 0.')
    return 0


def check_thumb_vote_chain():
    """AI 썸네일 화풍 투표 폐루프 게이트(하드 · 운영자 260805 "그게 남게끔 해서 나중에 한번 보자" → "ㄱㄱ").

    체인 = 뷰어 슬롯 👍/👎 → /api/rate(action='thumb' · reason 예약키 '<up|down|clear>:<sid>') → rate.yml 스텝
           → rate_record.py 분기(별도 원장) → thumb_vote_report.py → msg.py → 뷰어 알림메시지.
    ⚠️ 한 층만 빠져도 **투표가 조용히 죽는다** — 그것도 두 가지 서로 다른 방식으로:
      ⓐ 적재는 되는데 커밋이 안 됨(= 다음 체크아웃에서 증발) — 260805 첫 판이 실제로 이 상태였다.
      ⓑ 쌓이는데 아무도 안 읽음(= 죽은 원장) — brk_misfire 가 정확히 그 사고를 막으려고 생긴 축이다.
    화면은 둘 다 멀쩡해 보인다(버튼이 눌리고 초록이 켜진다) → 정적 층별 생존 강제가 유일한 검출기.

    ⚠️ rate.yml inputs 는 GitHub 상한 10개 = 신규 입력 추가 금지(11번째 = 디스패치 400 = 평점 레일 전체
       사망) → 그래서 전용 필드 없이 action/reason 예약키로 태운다. 그 계약도 여기서 함께 지킨다."""
    v = os.path.join(ROOT, 'viewer', 'index.html')
    rr = os.path.join(ROOT, '.github', 'scripts', 'rate_record.py')
    rp = os.path.join(ROOT, 'scraper', 'thumb_vote_report.py')
    y = os.path.join(ROOT, '.github', 'workflows', 'rate.yml')
    bad = []
    try:
        vt = open(v, encoding='utf-8').read()
        rt = open(rr, encoding='utf-8').read()
        pt = open(rp, encoding='utf-8').read()
        yt = open(y, encoding='utf-8').read()
    except Exception as e:
        print('❌ 썸네일 투표 체인 게이트 — 파일 열기 실패(fail-closed): %s' % e)
        return 1
    # ① 뷰어 송신 — 버튼·상태·전송 3점. 버튼만 있고 전송이 없으면 눌러도 아무 데도 안 간다(초록만 켜진다).
    if 'thVoteWire(' not in vt or 'function thVoteSend' not in vt:
        bad.append('뷰어 투표 배선 결손 — viewer/index.html thVoteWire()/thVoteSend()')
    if "action: 'thumb'" not in vt:
        bad.append("뷰어 송신 예약키 결손 — postRate action:'thumb'(없으면 기사 평점으로 잘못 적재)")
    if "class=\"sbtn fbup\"" not in vt or "class=\"sbtn fbdown\"" not in vt:
        bad.append('투표 버튼 결손 — 슬롯 액션행 .fbup/.fbdown(카드뉴스 투표 정본 계승분)')
    # ② 러너 분기 — 여기가 없으면 썸네일 표가 기사 취향 원장(ratings.jsonl)에 섞여 자동픽 학습을 오염시킨다.
    if 'THUMB_LEDGER' not in rt or 'thumb_votes.jsonl' not in rt:
        bad.append('러너 분기 결손 — rate_record.py THUMB_LEDGER(썸네일 표가 기사 취향 원장에 섞인다)')
    if 'up|down|clear' not in rt:
        bad.append('러너 예약키 파싱 결손 — reason 형식 검증(형식불량이 그대로 적재된다)')
    # ③ 소비기 — 쌓이기만 하고 아무도 안 읽는 죽은 원장 차단(brk_misfire 와 같은 축).
    if 'MSG_ID_BASE' not in pt or 'MSG_PY' not in pt:
        bad.append('소비기 알림 경로 결손 — thumb_vote_report.py msg.py 호출')
    if 'fresh = [v for v in votes if' not in pt or '"seen": sorted(seen)' not in pt:
        bad.append('라운드 소비 결손 — 누적형이면 같은 결론이 매 라운드 재발화(스팸) + 최근 경향이 묻힌다')
    # ④ 워크플로 — 실행줄만 인정(평문 substring 이면 주석 처리해도 통과 = check_refs 자신이 명시한 함정).
    if not _has_exec_line(yt, 'python3 scraper/thumb_vote_report.py'):
        bad.append('워크플로 소비 스텝 결손 — rate.yml 실행줄(투표가 쌓이기만 하고 리포트가 안 뜬다)')
    # ⑤ 커밋 — 260805 실사고 축. 적재는 되는데 add 가 없어 다음 체크아웃에서 조용히 증발한다.
    for path, why in (('scraper/thumb_votes.jsonl', '투표 원장'), ('scraper/thumb_vote_report.json', '처리 원장')):
        if not _has_exec_line(yt, 'git add ' + path):
            bad.append('워크플로 커밋 결손 — %s(%s)가 커밋 안 되면 다음 체크아웃에서 증발' % (path, why))
    if bad:
        print('❌ 썸네일 투표 체인 게이트 — 층 결손 %d건(투표가 조용히 죽는다):' % len(bad))
        for b in bad:
            print('   ·', b)
        return 1
    print('✅ 썸네일 투표 체인 게이트 — 뷰어 송신·러너 분기·소비기·워크플로 스텝·원장 커밋 5층 생존.')
    return 0


def check_img_upsize():
    """검색 이미지 화질 승격 체인 게이트(하드 · 운영자 260810 "고화질을 가져오게 · 최소 세로 720p 이상").

    매체 og:image 는 SNS 카드용 **축소판**인 경우가 많다(실측 260810 = 헤럴드 og `_T1` 300×200 인데
    같은 CDN 에 `_R` 1280×853 원본이 그대로 있다 · 스포츠Q `/thumbnail/…_v150` 300×200 ↔ `/photo/…` 600×400 ·
    파이낸셜 `_l` 800×584 ↔ 접미사 제거 3165×2313). 우리 파이프는 받은 바이트를 **그대로** R2 에 올리므로
    (압축·축소 0) 화질의 유일한 결정 지점이 '어느 URL 을 집었나' 한 축이고, 카드 산출물은 짧은변 1440
    (thumb-make RES-SNAP)이라 300×200 배경은 **5배 업샘플**로 뭉갠다.

    ⚠️ 신설 사유 = **이 축은 조용히 죽는데 화면 증상이 0이다.** `_best_variant` 호출 한 줄만 빠져도
       파이프는 정상 동작하고 로그도 정상이며 이미지도 나온다 — 다만 화질이 종전으로 되돌아갈 뿐이라
       **운영자 눈이 유일한 검출기**가 된다(insta-thumb-miss·brk_misfire 동축). 기존 게이트는 전부
       다른 축이다 — `check_image_format` = 포맷·품질(q90) · `check_thumb_redo_append` = 수정 누적 ·
       `smoke_*` = 화면 렌더 → 「가져온 이미지가 그 사진의 **가장 큰 판인가**」는 축 자체가 없었다.

    판정 3축(정적 · 렌더·LLM·네트워크 0 · **면책표 없이 하드 0** · 주석 줄 제외 = 주석 처리 우회 차단):
      ① 승격 3부품 실존(`_upsize_urls` 후보 생성 · `_dim_probe` 실측 · `_best_variant` 채택)
      ② `fetch_article_images` **안**에서 `_best_variant` 실호출 — 대표 경로·관련 경로 **둘 다**
         (한쪽만 걸면 나머지 경로가 조용히 종전 화질로 남는다 = 이 레포 최빈 미러 드리프트)
      ③ 720 문턱이 `img_sizes` SSOT 경유 — 리터럴 재창작 금지([4-3] 값 창작 0 · AI생성·편집과 같은 사다리)
    """
    tg = os.path.join(ROOT, '.github', 'scripts', 'thumb_gen.py')
    try:
        t = open(tg, encoding='utf-8').read()
    except Exception as e:
        print('❌ 화질 승격 게이트 — 파일 읽기 실패:', e)
        return 1
    live = [ln for ln in t.splitlines() if ln.strip() and not ln.strip().startswith('#')]
    body = '\n'.join(live)
    bad = []

    # ① 승격·컷 4부품 실존
    for sym in ('def _upsize_urls(', 'def _dim_probe(', 'def _best_variant(', 'def _hq_cut('):
        if sym not in body:
            bad.append('승격·컷 부품 소실: {} — og:image 축소판을 그대로 쓰게 된다'.format(sym.replace('def ', '').rstrip('(')))

    # ② fetch_article_images 안 두 경로 모두 승격·컷 실호출
    m = re.search(r'^def fetch_article_images\(', body, re.M)
    if not m:
        bad.append('fetch_article_images 정의 소실 — 승격 배선 지점 자체가 사라졌다')
    else:
        nxt = re.search(r'^def \w+\(', body[m.end():], re.M)
        fn = body[m.start(): m.end() + (nxt.start() if nxt else len(body))]
        for sym, why in (('_best_variant(', '종전 화질로 남는다'), ('_hq_cut(', '720 미달이 그대로 수집된다')):
            n = fn.count(sym)
            if n < 2:
                bad.append('fetch_article_images 안 {} 호출 {}회(필요 2 = 대표 경로 + 관련소스 경로) — '
                           '한쪽만 걸면 나머지 경로가 조용히 {}'.format(sym.rstrip('('), n, why))
        # ⓑ 컷으로 후보가 반감하므로 훑는 범위 확대가 짝 계약 — 15 로 되돌리면 컷이 곧 장수 감소가 된다
        if '_REL_SCAN' not in fn:
            bad.append('관련소스 훑는 범위가 _REL_SCAN 경유가 아니다 — 720 컷 뒤 채택률 반감을 못 흡수해 장수가 준다')

    # ②-b 보충 체인 생존 — 컷으로 빈 자리를 메우는 유일한 수단(끊기면 컷이 곧 영구 결손)
    if 'thumb_topup.txt' not in body:
        bad.append('보충 대상 마커(thumb_topup.txt) 소실 — 화질 컷으로 빈 자리를 다시 검색해 채울 경로가 없다')

    # ②-c 보충 **다회전** 체인(운영자 260810 5차) — 1회 보충으로는 자리가 안 찬다(문턱 도입 뒤 후보 절반이
    #     화질에서 잘린다). 라운드 예약(스크립트) ↔ 재발사(워크플로) 두 짝 중 하나만 빠져도 조용히 1회로 되돌아간다.
    mi = os.path.join(ROOT, '.github', 'scripts', 'more_images.py')
    yml = os.path.join(ROOT, '.github', 'workflows', 'moreimg.yml')
    try:
        mt = '\n'.join(l for l in open(mi, encoding='utf-8').read().splitlines()
                       if l.strip() and not l.strip().startswith('#'))
        yt = open(yml, encoding='utf-8').read()
    except Exception as e:
        bad.append('보충 라운드 체인 파일 읽기 실패: {}'.format(str(e)[:50]))
    else:
        if 'def _again(' not in mt or 'moreimg_again.txt' not in mt:
            bad.append('more_images 라운드 예약(_again·moreimg_again.txt) 소실 — 보충이 1회로 되돌아간다')
        if 'MAX_ROUND' not in mt or 'MOREIMG_ROUND' not in mt:
            bad.append('보충 라운드 상한·세대(MAX_ROUND·MOREIMG_ROUND) 소실 — 정지 조건이 없으면 무한 발사')
        if 'moreimg_again.txt' not in yt or 'workflows/moreimg.yml/dispatches' not in yt:
            bad.append('moreimg.yml 다음 라운드 재발사 스텝 소실 — 예약만 되고 아무도 안 쏜다')
        if 'round:' not in yt:
            bad.append('moreimg.yml round 입력 소실 — 세대가 안 실려 라운드 상한이 영영 1에 머문다')

    # ③ 수집 문턱 = img_sizes SSOT 경유(값은 운영자가 바꾼다 — 게이트는 '한 곳에서 오는가'만 본다)
    if 'from img_sizes import COLLECT_MIN_H' not in body or '_MIN_H' not in body:
        bad.append('수집 문턱이 img_sizes.COLLECT_MIN_H 경유가 아니다 — 리터럴 재창작 = 문턱 드리프트')
    try:
        sys.path.insert(0, os.path.join(ROOT, '.github', 'scripts'))
        import img_sizes as _isz
        if not isinstance(getattr(_isz, 'COLLECT_MIN_H', None), int):
            bad.append('img_sizes.COLLECT_MIN_H 소실 — 수집 문턱 SSOT 자체가 없다')
    except Exception as e:
        bad.append('img_sizes import 실패({}) — 수집 문턱 SSOT 도달 불가'.format(str(e)[:40]))

    if bad:
        print('❌ 검색 이미지 화질 승격 체인 — {}건'.format(len(bad)))
        for b in bad:
            print('   ·', b)
        return 1
    return 0


def check_thumb_redo_append():
    """썸네일 '수정 = 덮어쓰기 아닌 +1 슬롯' 체인 게이트(하드 · 운영자 260807 "수정하면 원래 이미지는
    계속 보이게하고 수정된 이미지가 +1개로 생기는 개념이여야 되거든? 1/2 2/2 면 1/3 2/3 3/3").

    구판 = 연필 '수정'이 gen.json 에서 그 sid 를 **지우고** 같은 R2 키(gen-<sid>)에 **덮어썼다**
      → 원본 바이트가 영구 소멸하고 슬롯 수가 화풍 수(2)에 영영 고정됐다(1/2 2/2 가 계속 1/2 2/2).
      원본이 더 나았어도 되돌릴 방법이 0이었다.
    신판 = 파생 sid `<base>_rN`(photo_r2…)로 **새 슬롯을 추가**한다 → R2 키가 자연 분리돼 원본 무접촉.

    ⚠️ 신설 사유 = 이 체인은 **세 층 중 하나만 빠져도 조용히 죽는데, 셋 다 증상이 다르고 셋 다 화면은
       멀쩡해 보인다**:
      ⓐ `process_one` 파생 보존이 빠지면 — 그 루프는 STYLES 만 순회하며 gen.json 을 **재조립**하므로
         파생 sid 가 리스트에 안 실려 **다음 실행에서 소리 없이 사라진다**(thumb_gen 78행이 명시한
         '자동 드롭'). 수정 직후엔 멀쩡히 보이다가 며칠 뒤 혼자 없어진다 = 최고 추적난도.
      ⓑ `thumbredo.js` 화이트리스트가 숫자를 막으면 — sid 가 '' 로 떨어져 **전 화풍 재생성**이 된다
         (Gemini 재과금 2배). 새 그림이 나오니 오작동으로 안 보인다.
      ⓒ 뷰어 완료 판정이 구판(원본 img ?v= 변화)이면 — 이제 원본은 안 바뀌므로 **10분 타임아웃까지
         완료를 못 낸다**(제작중 슬롯 잔류 + '지연됐을 수 있어' 토스트).
    기존 게이트는 전부 다른 축이다(`check_image_format` = 포맷·품질 · `check_thumb_vote_chain` = 투표 층 ·
    `smoke_*` = 화면 렌더) → 「수정이 덮어쓰기인가 누적인가」는 축 자체가 없었다.

    판정 = 정적(렌더·LLM·네트워크 0) · **면책표 없이 하드 0** · 주석 줄 제외(주석 처리 우회 차단).
    """
    tg = os.path.join(ROOT, '.github', 'scripts', 'thumb_gen.py')
    api = os.path.join(ROOT, 'functions', 'api', 'thumbredo.js')
    v = os.path.join(ROOT, 'viewer', 'index.html')
    bad = []
    try:
        gt = open(tg, encoding='utf-8').read()
        at = open(api, encoding='utf-8').read()
        vt = open(v, encoding='utf-8').read()
    except Exception as e:
        print('❌ 썸네일 수정 누적 게이트 — 파일 읽기 실패:', e)
        return 1

    def _live(text, needle, cmt):
        """주석 줄을 뺀 실행줄에 needle 이 있나(평문 substring 이면 주석 처리로 조용히 우회된다)."""
        for ln in text.splitlines():
            s = ln.strip()
            if not s or s.startswith(cmt):
                continue
            if needle in s:
                return True
        return False

    # ① 러너 — 파생 sid 문법 3종 + 보존 루프 + process_one 인자.
    for needle, why in (
            ('def _base_sid(', '파생→베이스 정규화(라벨·특칙·투표 집계 공용)'),
            ('def _is_redo_sid(', '파생 판별(보존 대상 식별)'),
            ('def _next_redo_sid(', '다음 세대 sid 할당'),
            ('_is_redo_sid(_s)', 'STYLES 밖 파생 보존 — 없으면 다음 실행에서 수정본이 조용히 드롭'),
            ('def process_one(md, stem, redo_new', '파생 발사 인자')):
        if not _live(gt, needle, '#'):
            bad.append('러너 결손 — thumb_gen.py `%s` (%s)' % (needle, why))
    # ①-b 구판 파괴 문법 부활 차단 = 이 게이트의 핵심(원본을 지우면 +1 개념이 통째로 무너진다).
    if _live(gt, '!= redo_sid', '#'):
        bad.append('러너 구판 부활 — gen.json 에서 원본 sid 를 제거하는 필터(`!= redo_sid`)가 되살아났다')

    # ② API — sid 화이트리스트가 숫자를 허용해야 파생 sid(photo_r2)가 통과한다.
    if not _live(at, '[a-z0-9_]', '//'):
        bad.append('API 결손 — thumbredo.js sid 화이트리스트가 숫자 불허(파생 sid 거절 → sid="" → 전 화풍 재과금)')

    # ③ 뷰어 — 대기 슬롯 배선 + 완료 판정이 '장수' 축.
    for needle, why in (
            ('function thumbBaseSid(', '파생→베이스 정규화(러너 미러)'),
            ('function genGenCount(', '그 화풍 계열 장수 = 완료 판정 기준'),
            ('function thumbRedoPendList(', '대기 슬롯 수'),
            ('_pendH', '트랙 끝 제작중 슬롯 마크업'),
            ('genGenCount(a, base) > rec.snap[base]', '완료 판정 = +1장 도착(구판 img ?v= 축이면 영영 미완료)')):
        if not _live(vt, needle, '//'):
            bad.append('뷰어 결손 — index.html `%s` (%s)' % (needle, why))

    if bad:
        print('❌ 썸네일 수정 누적 게이트 — 층 결손 %d건(수정본이 조용히 사라지거나 재과금된다):' % len(bad))
        for b in bad:
            print('   ·', b)
        return 1
    print('✅ 썸네일 수정 누적 게이트 — 파생 sid 3종·보존 루프·API 화이트리스트·뷰어 대기슬롯/완료판정 생존(원본 무접촉).')
    return 0


# 요약 요청 첨부 사진 판독 하한 — 값 원천 = 260812 실측(재현 = 폰 기사 스크롤 캡처 1080×{3000,5700,9000}을
#   뷰어와 같은 산식으로 압축한 뒤 **실제로 판독**):
#     세로 3000 → 461×1280(본문 15.4px) 또렷 · 5700 → 243×1280(8.1px) 읽힘 · 9000 → 154×1280(5.1px) 읽히나 흐림.
#   ⚠ 면책표(baseline) 아님 = 단일 임계 상수(부채 원장 증가 0 · `RENDER_BUDGET` 선례). 낮추려면 같은 실측을
#   다시 떠서 판독을 확인하고 이 주석의 근거를 갱신한다(값만 내리는 개정 = 이 게이트가 막으려는 바로 그 회귀).
_ASKIMG_MIN_SIDE = 1280   # 긴 변 픽셀 하한
_ASKIMG_MIN_Q = 0.6       # JPEG 화질 하한(0~1)


def check_ask_img_legible():
    """요약 요청에 붙인 사진 = 글자가 읽히는 크기로 나간다(하드 · 운영자 260812 "지금 된 부분을 앞으로 나올 수 있게 반영").

    발단 = 운영자가 세로로 아주 긴 기사 캡처를 요약 요청에 붙이며 물었다 — "글자 못 읽을 만큼 압축돼서
    왜곡될까봐". 실측 결과 **지금은 읽힌다**(위 상수 주석의 3케이스 실판독). 이 게이트는 그 「지금 되는
    상태」를 앞으로도 나오게 고정한다.

    ⚠ 신설 사유 = **이 축은 나빠져도 화면이 멀쩡하다.** 압축은 첨부 순간에 끝나고 화면엔 축소된 미리보기와
      용량(KB)만 뜨므로, 누가 토큰을 아끼려고 긴 변이나 화질을 낮춰도 첨부 UI는 똑같이 동작한다. 증상은
      **한참 뒤 요약 품질**로만 나타나고(숫자 오독·본문 누락), 그건 원인이 사진인지 기사인지 모델인지
      구분이 안 된다 = 운영자 눈조차 검출기가 못 되는 자리.
    ⚠ 기존 게이트는 전부 다른 축이다 — `check_ask_srcimg_chain` = 그림이 **실리는가**(층 생존) ·
      `check_image_format` = **산출물** 포맷·품질(이건 산출물이 아니라 모델 입력이라 `q-ok` 면제 대상) ·
      `smoke_*` = 화면 렌더 → 「그 입력이 **읽히는 크기인가**」는 축 자체가 없었다.

    판정 = 정적(렌더·LLM·네트워크 0) · 면책표 없이 하드 0 · 3축:
      ① 압축 함수 기본값이 하한 이상          ② 요약요청 호출부가 그 하한 밑으로 인자를 덮어쓰지 않음
      ③ 서버가 받은 바이트를 그대로 저장(재압축 0 = 뷰어 하한이 곧 최종 화질이라는 전제의 성립 조건)
    ⚠ ②가 실효 조건 = 기본값만 보면 `compressImg(f, 640, 0.4)` 한 줄로 조용히 우회된다(기본값은 그대로인데
      실제로 나가는 사진만 나빠진다 = 정적 게이트의 전형적 사각).
    """
    v = os.path.join(ROOT, 'viewer', 'index.html')
    a = os.path.join(ROOT, '.github', 'scripts', 'ask.sh')
    bad = []
    try:
        vt = open(v, encoding='utf-8').read()
        at = open(a, encoding='utf-8').read()
    except Exception as e:
        print('❌ 요약요청 첨부 판독 게이트 — 파일 열기 실패: %s' % e)
        return 1

    # ① 압축 함수 기본값(앵커 소실 = fail-closed — 함수가 개명·해체되면 하한이 어디에도 없다)
    m = re.search(r'async\s+function\s+compressImg\s*\(\s*file\s*,\s*max\s*=\s*([0-9]+)\s*,\s*q\s*=\s*([0-9.]+)\s*\)', vt)
    if not m:
        bad.append('뷰어 압축 함수(compressImg) 선언을 못 찾음 — 앵커 소실 fail-closed(개명했으면 이 게이트도 같이 옮긴다)')
    else:
        side, q = int(m.group(1)), float(m.group(2))
        if side < _ASKIMG_MIN_SIDE:
            bad.append('첨부 사진 긴 변 기본값 %dpx < 하한 %dpx — 세로로 긴 기사 캡처의 가로가 그만큼 더 좁아져 글자가 뭉개진다'
                       % (side, _ASKIMG_MIN_SIDE))
        if q < _ASKIMG_MIN_Q:
            bad.append('첨부 사진 화질 기본값 %s < 하한 %s — 작은 글자는 화질을 내리는 순간 먼저 무너진다'
                       % (q, _ASKIMG_MIN_Q))

    # ② 요약요청 호출부가 하한 밑으로 덮어쓰지 않는가(기본값 우회 차단)
    ca = re.search(r'function\s+addAskImages\s*\([^)]*\)\s*\{(.*?)\n\}', vt, re.S)
    if not ca:
        bad.append('요약요청 첨부 경로(addAskImages)를 못 찾음 — 앵커 소실 fail-closed')
    else:
        body = ca.group(1)
        if 'compressImg(' not in body:
            bad.append('요약요청 첨부 경로가 압축 함수를 안 부른다 — 원본이 그대로 나가거나(용량 폭발) 다른 산식으로 갈렸다')
        for call in re.findall(r'compressImg\(([^)]*)\)', body):
            args = [x.strip() for x in call.split(',')]
            if len(args) >= 2 and re.fullmatch(r'[0-9]+', args[1]) and int(args[1]) < _ASKIMG_MIN_SIDE:
                bad.append('요약요청 호출부가 긴 변을 %s px로 덮어씀 < 하한 %d — 기본값은 그대로라 조용히 우회된다'
                           % (args[1], _ASKIMG_MIN_SIDE))
            if len(args) >= 3 and re.fullmatch(r'[0-9.]+', args[2]) and float(args[2]) < _ASKIMG_MIN_Q:
                bad.append('요약요청 호출부가 화질을 %s 로 덮어씀 < 하한 %s — 기본값은 그대로라 조용히 우회된다'
                           % (args[2], _ASKIMG_MIN_Q))

    # ③ 서버 = 받은 바이트 그대로 저장(재압축 0). 이게 깨지면 ①②의 하한이 최종 화질을 뜻하지 않게 된다.
    save = [ln for ln in at.splitlines() if 'img-' in ln and 'write' in ln and not ln.lstrip().startswith('#')]
    if not save:
        bad.append('서버 첨부 저장 줄을 못 찾음 — 앵커 소실 fail-closed(요약 파이프가 첨부 사진을 파일로 안 굽는다)')
    elif not any('b64decode' in ln for ln in save):
        bad.append('서버가 받은 바이트를 그대로 안 쓴다(디코드 후 재인코딩 의심) — 뷰어 하한이 최종 화질을 보장하지 못한다')

    if bad:
        print('❌ 요약요청 첨부 판독 — %d건' % len(bad))
        for b in bad:
            print('   · %s' % b)
        print('   · 계약 = 붙인 사진의 글자가 요약 모델에 읽히는 크기로 간다(긴 변 ≥%d · 화질 ≥%s · 서버 재압축 0).'
              % (_ASKIMG_MIN_SIDE, _ASKIMG_MIN_Q))
        print('   · 이 축은 나빠져도 첨부 화면이 똑같이 동작한다 — 증상은 한참 뒤 요약 품질로만 나온다.')
        return 1
    print('✅ 요약요청 첨부 판독 — 긴 변 %dpx · 화질 %s · 서버 재압축 0(260812 실측 = 세로 9000 캡처도 판독 가능).'
          % (_ASKIMG_MIN_SIDE, _ASKIMG_MIN_Q))
    return 0


def check_ask_srcimg_chain():
    """출처 글 본문 이미지 수확 체인 게이트(하드 · 운영자 260804 "확인해줘" → 사고 fail-2026-08-04-0239-297it).

    사고 실측 = SNS 카드 「전송」으로 보낸 보배드림 글이 ANALYSIS_FAILED. 원인은 '사이트를 못 읽어서'도
    '내용을 긁고도 뜻을 몰라서'도 아니었다 — **본문이 이미지 2장뿐이라 읽을 글이 0자**였고(페이지는 정상
    취득), 제목("이런걸 재능이라고 하는구나")은 고유명사가 0이라 기사 유추 폴백도 공회전했다.
    봉합 = 파이프에 **이미 있던 멀티모달 레일**(asks images[] → workdir/img-*.jpg → 프롬프트 '첨부 캡처')에
    출처 글의 본문 그림을 태우는 수확 층 1개 추가(신규 분석 로직 0).

    체인 = ask.sh 출처 URL 선정 → ask_srcimg.py 수확 → 프롬프트 🖼 블록 → 1-3 폴백 지시.
    한 층만 빠져도 **그림이 조용히 안 실린 채 요약이 돌아** 같은 실패가 그대로 재발한다(로그엔 아무 흔적도
    안 남는다 = 가장 조용한 실패) → 층별 심볼 생존을 정적으로 강제(네트워크·LLM·렌더 0).
    ⚠️ UA 2단은 장식이 아니다 — 실측상 모바일 UA 단독이면 그 사이트가 http 200 에 3,566B 껍데기를 준다
    (본문 0 = 수확 0 = 사고 재현). 데스크톱 1순위 + 껍데기 시 교대가 이 체인의 실효 조건이라 함께 지킨다."""
    a = os.path.join(ROOT, '.github', 'scripts', 'ask.sh')
    p = os.path.join(ROOT, '.github', 'scripts', 'ask_srcimg.py')
    o = os.path.join(ROOT, '.github', 'scripts', 'ask_srcocr.py')
    bad = []
    try:
        at = open(a, encoding='utf-8').read()
        pt = open(p, encoding='utf-8').read()
        ot = open(o, encoding='utf-8').read()
    except Exception as e:
        print('❌ 출처 본문 이미지 수확 체인 게이트 — 파일 열기 실패: %s' % e)
        return 1
    # ① ask.sh — 출처 URL 선정(srcUrl 우선 → 요청문 첫 URL 폴백)
    if "get('srcUrl')" not in at:
        bad.append("ask.sh 출처 URL 결손 — srcUrl 필드를 안 읽는다(SNS 카드 전송이 보내는 유일한 글 주소)")
    if 'https?://' not in at or 'NM_T' not in at:
        bad.append('ask.sh 요청문 URL 폴백 결손 — srcUrl 없는 구 클라·직접 붙여넣기 요청이 수확에서 빠진다')
    # ② 실행줄(주석 처리로 통과하는 평문 substring 함정 차단 = brk_misfire 게이트와 동축).
    #    ⚠️ 줄 **선두**만 `(?!#)`로 보는 관용구는 여기서 뚫린다 — 이 호출은 `_sj="$(timeout … python3 …)"`
    #    처럼 줄 중간에 있어서, 호출 바로 앞에만 `#`를 붙여도 줄 선두는 여전히 `_sj=`라 통과한다
    #    (킬테스트 실측: 주석 처리했는데 게이트가 ✅). → 호출 **앞쪽 전체**에 `#`가 없을 것으로 강화.
    if not re.search(r'^[^\n#]*python3 \.github/scripts/ask_srcimg\.py', at, re.M):
        bad.append('ask.sh 수확 실행줄 결손 — ask_srcimg.py 호출(주석 처리 포함)')
    # ③ 프롬프트 주입 — 수확만 하고 프롬프트에 안 실으면 파일만 굴러다니고 모델은 못 본다(무증상 사각)
    if '${SRCIMG_BLOCK}' not in at or 'SRCIMG_BLOCK="[' not in at:
        bad.append('ask.sh 프롬프트 주입 결손 — SRCIMG_BLOCK 미조립·미삽입(그림을 받아놓고 안 보여준다)')
    if 'workdir"/src-*' not in at:
        bad.append('ask.sh 수확물 수집 결손 — src-* 글롭(수확기 산출 접두와 불일치면 항상 0장)')
    # ④ 수확기 골격
    for sym, why in (('def harvest(', '수확 진입점'), ('def px_size(', '실측 픽셀 필터'),
                     ('UA_DESK', '데스크톱 UA 1순위'), ('def _get_page(', 'UA 교대 재시도'),
                     ('PX_MIN', '썸네일 컷 하한'), ('def _blocked_host(', 'SSRF 호스트 가드')):
        if sym not in pt:
            bad.append('ask_srcimg.py %s 결손(%s)' % (why, sym))
    if 'UA_MOB' not in pt or 'SHELL_BYTES' not in pt:
        bad.append('ask_srcimg.py UA 2단 결손 — 봇차단 껍데기(실측 3,566B) 검출·교대가 없으면 수확 0')
    # ⑤ 프롬프트 지시 — 그림을 줘도 '기사 못 찾으면 실패'로 끝나면 사고가 그대로 재발한다
    if '1-3)' not in at:
        bad.append("ask.sh 프롬프트 1-3 폴백 결손 — '본문이 그림뿐일 때' 순서 지시(제목 검색 공회전 차단)")
    # ⑥ OCR 층(운영자 260804 2차) — 그림 '첨부'만으론 본선이 여는지가 확률 축이고, 열어도 프롬프트 1)의
    #    보강 모드(「요청문에 전문이 있으면」)에 안 물린다 → 문자열을 확정적으로 뽑아 전사문과 같은 지위로
    #    실어야 기존 뉴스 요약 로직에 연결된다. 이 층이 빠지면 조용히 1차 동작(첨부만)으로 퇴행한다.
    if not re.search(r'^[^\n#]*python3 \.github/scripts/ask_srcocr\.py', at, re.M):
        bad.append('ask.sh OCR 실행줄 결손 — ask_srcocr.py 호출(주석 처리 포함)')
    if '추출문:' not in at or '곧 원문이다' not in at:
        bad.append("ask.sh OCR 전문 주입 결손 — 추출문이 '원문' 지위로 안 실리면 보강 모드에 안 물린다")
    # ⑥-b 일괄 축(운영자 260804 3차 "sns 안에 있는 내용이 **일괄로** 뉴스 요약에 들어가는 소스로") —
    #    2차 배선은 OCR 이 수확분(src-*) 안쪽 if 에 갇혀 **뷰어 직접 첨부 캡처(img-*)가 빠져** 있었다
    #    = 같은 그림이 어느 입구로 들어왔느냐에 따라 동작이 갈리던 구멍. 두 접두를 한 배열에 모으는 줄이
    #    이 계약의 실체라 여기서 못박는다(한쪽이 빠지면 그 입구만 조용히 구 동작으로 퇴행 = 무증상).
    m = re.search(r'^\s*ocrimgs=\(\)\s*\n\s*for im in ([^;\n]+); do', at, re.M)
    globs = m.group(1) if m else ''
    if 'img-' not in globs or 'src-' not in globs:
        bad.append('ask.sh OCR 일괄 축 결손 — 첨부 캡처(img-*)와 수확분(src-*)이 한 배열(ocrimgs)에 안 모인다'
                   '(입구별 동작 분기 = 한쪽만 조용히 구 동작)')
    if not re.search(r'^\s*(?!#)[^\n]*ask_srcocr\.py "\$\{ocrimgs\[@\]\}"', at, re.M):
        bad.append('ask.sh OCR 입력 결손 — 일괄 배열(ocrimgs)이 아니라 부분 집합만 OCR 에 넘긴다')
    if 'from claude_py import run_claude' not in ot:
        bad.append('ask_srcocr.py 폴오버 SSOT 미경유 — claude_py.run_claude(자체 쿼터처리 금지 계약)')
    if "'--allowedTools', 'Read'" not in ot:
        bad.append('ask_srcocr.py Read 권한 결손 — 이미지를 못 연다(추출 항상 0)')
    if 'def ocr(' not in ot:
        bad.append('ask_srcocr.py 추출 진입점 결손(def ocr)')
    # ⑦ 프레임 셸 해제(260805 · 사고 fail-2026-08-04-1528-idagw = 네이버 블로그) — blog.naver.com 류는
    #    본문을 iframe(mainFrame→PostView)·JS 리다이렉트 뒤에 숨겨 **UA 2단으로도 껍데기만 온다**
    #    (실측 2,859B/184B → 해제 후 257,516B·한글 5,495자·본문 이미지 5장). 이 층이 빠지면 프레임 매체
    #    전체(네이버 블로그가 대표)가 '페이지는 열리는데 읽을 게 0자' → ANALYSIS_FAILED 로 그대로 회귀.
    #    축 3개 전부 지켜야 한다: 수확기 해제(이미지·OCR), 본선 주소 전달(텍스트 본문), 분석기 텍스트 추출.
    for sym, why in (('def _frame_target(', '프레임 해제기'), ("res['final']", '해제 주소 보고(final)'),
                     ("== '--resolve'", '링크 레일 공용 해제 모드')):
        if sym not in pt:
            bad.append('ask_srcimg.py 프레임 셸 해제 결손(%s — %s)' % (why, sym))
    if 'FRAMEURL_BLOCK="[' not in at or '${FRAMEURL_BLOCK}' not in at:
        bad.append('ask.sh 해제 주소 주입 결손 — FRAMEURL_BLOCK 미조립·미삽입(해제해 놓고 본선은 여전히 껍데기를 연다)')
    if '--resolve' not in at:
        bad.append('ask.sh 링크 레일 해제 결손 — 같은 URL 이 링크칸으로 들어오면 그 입구만 사고 재발(입구별 분기 금지)')
    fa = os.path.join(ROOT, '.github', 'scripts', 'fetch_article.sh')
    try:
        fat = open(fa, encoding='utf-8').read()
    except Exception:
        fat = ''
    if 'mainFrame' not in fat or 'location(?:' not in fat:
        bad.append('fetch_article.sh 프레임 셸 해제 결손 — 분석기 텍스트 축이 iframe 셸을 본문으로 오인(한글 0자 = 빈 출력)')
    # ⑧ 실패 자동진단서(운영자 260805 "자동진단서 ㄱ") — 실패 알림이 「입력이 비었거나 불충분」 한 줄로만
    #    나가면 다음 세션이 매번 원인 실측부터 다시 한다(260804 사고 2건 실측). 실패 순간 URL 재실측 동봉 +
    #    같은 도메인 14일 2회 재발 = 인수인계 진단서 승격. 이 층이 빠지면 알림이 조용히 구판(한 줄)으로 퇴행.
    fp_ = os.path.join(ROOT, '.github', 'scripts', 'ask_fail_probe.py')
    try:
        fpt = open(fp_, encoding='utf-8').read()
    except Exception:
        fpt = ''
    for sym, why in (('import ask_srcimg', '취득·해제 정본 재사용(별도 fetch 창작 금지)'),
                     ('def probe(', '실측 진입점'), ('def handover(', '인수인계 진단서'),
                     ('fail_ledger.jsonl', '재발 원장'), ('LEDGER_MAX', '원장 롤링 상한')):
        if sym not in fpt:
            bad.append('ask_fail_probe.py 결손(%s — %s)' % (sym, why))
    if not re.search(r'^[^\n#]*python3 \.github/scripts/ask_fail_probe\.py', at, re.M):
        bad.append('ask.sh 자동진단 실행줄 결손 — ask_fail_probe.py 호출(주석 처리 포함)')
    if '_diag' not in at:
        bad.append('ask.sh 진단 동봉 결손 — 진단을 뽑아놓고 실패 알림 본문(_fbody)에 안 싣는다')
    # ⑧-b 코드 결함 축(운영자 260805 "아이디어 ㄱㄱ") — 진단서가 붙어도 **분류가 source 로 남으면** 알림이
    #    여전히 「입력이 비었거나 불충분」이라 사람을 입력·소스 축으로 몰고, 진단서도 그 축으로 읽힌다
    #    (260805 실사고 = URL 은 멀쩡한데 prompt 변수가 안 잡혀 죽은 건인데 다음 세션이 6시간 오진).
    #    술어 = rc≠0 ∧ 출력 0 = 모델이 답한 적이 없다. 두 경로(ask·analyze) 동시 보유가 계약 — 한쪽만
    #    고치면 나머지 경로가 조용히 구 문구로 남는다(가장 흔한 미러 드리프트).
    try:
        _ant = open(os.path.join(ROOT, '.github', 'scripts', 'analyze.sh'), encoding='utf-8').read()
    except Exception:
        _ant = ''
    for _p, _t in (('ask.sh', at), ('analyze.sh', _ant)):
        if not re.search(r'_fk=\"?code\"?', _t):
            bad.append('%s 코드 결함 축 결손 — 파이프라인 사고가 「내용/소스 결함」으로 오표기된다' % _p)
    if bad:
        print('❌ 출처 본문 이미지 수확 체인 게이트 — 층 결손 %d건(그림이 조용히 안 실린다):' % len(bad))
        for b in bad:
            print('   ·', b)
        return 1
    print('✅ 출처 본문 이미지 수확 체인 — URL 선정·수확기·UA 2단·OCR 추출·전문 주입·1-3 폴백·프레임 해제·실패 자동진단 8층 생존.')
    return 0


def check_subs_author_scope():
    """구독 수집 = 작성자 검문 의무(하드 · 운영자 260804 "내가 구독한 애들이 아닌데").
    260804 실사고 = '스레드 - 구독' 20건이 **등록한 적 없는 계정**으로 통째 채워짐(등록 5계정 0건).
    구조 = threads_subs()의 walk()가 응답 안 **모든** 포스트 노드를 걷는데, 게스트 응답은 프로필 주인 글만
    담지만(260804 실측 = 등록 5계정 37건 전건 본인) 로그인 상태(THREADS_COOKIE)·로그인월 리다이렉트
    응답에는 **추천(For you) 피드**가 같이 실린다 → 무검문 채집 = 남의 알고리즘 피드가 '구독'을 차지.
    X·인스타·틱톡은 항목의 account 를 요청 계정으로 못박아 구조적으로 불가능했고, 스레드만 노드의
    username 을 신뢰해서 갈렸다. 정적만으로 잡히는 이유 = 검문 유무가 코드 한 줄의 존재 문제(렌더·LLM 0).
    ⚠ 도장 축도 같이 지킨다 — 구판은 `posts` 유무로 _sok 을 찍어 추천 피드만 걷힌 회차를 got 5/5
      '전건 성공'으로 보고했다(화면은 남의 글, 게이트는 무경보 = 가장 조용한 실패)."""
    p = os.path.join(ROOT, 'scraper', 'sns_trends.py')
    try:
        t = open(p, encoding='utf-8').read()
    except Exception as e:
        print('❌ 구독 작성자 검문 게이트 — 읽기 실패(fail-closed):', e)
        return 1
    m = re.search(r'\ndef threads_subs\(.*?\n(?=\n[A-Za-z_]|\ndef )', t, re.S)
    body = m.group(0) if m else ''
    bad = []
    if not body:
        bad.append('threads_subs() 함수를 못 찾음 — 게이트가 검사할 대상 소실(개명했으면 이 게이트도 같이 고쳐라)')
    else:
        if not re.search(r'username[^\n]*\)\s*\.strip\(\)', body) or '!= _me' not in body:
            bad.append('작성자 검문 결손 — threads_subs()가 요청 계정과 작성자를 대조하지 않는다(추천 피드가 구독을 차지)')
        if re.search(r'get\("username"\)\)?\s*or\s+acc', body):
            bad.append('구판 폴백 부활 — username 결측 노드를 요청 계정 글로 단정(`or acc`) = 검문 우회')
        if 'if _mine:' not in body or '_sok("threads"' not in body:
            bad.append('성공 도장 축 결손 — _sok 은 **본인 글 확보**가 기준(posts 유무 기준 구판 = got 5/5 거짓 보고)')
    # 2차 방어 = 러너 채택 지점 화이트리스트(폰이 구 파서로 돌아도 러너가 거른다)
    if not re.search(r'k2 == "threads"', t) or 'acc.get("threads")' not in t:
        bad.append('폰 채택 화이트리스트 결손 — 폰 구버전 파서 산출이 무검문 채택된다(sns_trends.py main 채택 루프)')
    # 3차 = 이월(carry) 화이트리스트 — 스레드는 러너 미수집이라 채택분이 전건 폐기되면 carry 가 직전 오염분을 되살린다
    if not re.search(r'def carry\(k\):', t) or not re.search(r'if k == "threads"', t):
        bad.append('이월 화이트리스트 결손 — carry(k)가 직전 오염분을 되살린다(추천 피드가 화면에 영구 잔류)')
    if bad:
        print('❌ 구독 작성자 검문 게이트 — 결손 %d건(구독 칸에 남의 알고리즘 피드가 들어온다):' % len(bad))
        for b in bad:
            print('   ·', b)
        return 1
    print('✅ 구독 작성자 검문 게이트 — 스레드 작성자 대조·본인글 기준 도장·폰 채택 화이트리스트 3층 생존.')
    return 0


# ⑭-e 랜드마크 즉시 긴급알림 = 발신 기관 서명 오탐 차단(하드 · 260805 실사고 봉합).
#   실사고 = 「석남동 쿠팡물류센터 화재 관련 … 도로차단은 **유지**되오니 우회하시기 바랍니다. [서해구청]」이
#   기기 긴급알림으로 발사(07:03). 신규 발생도 아닌 **교통 후속 안내**였고, 랜드마크로 판정된 「서해구청」은
#   본문의 건물이 아니라 **문자 말미 발신 기관 서명**이었다. 한국 재난문자는 관례상 전건이 «[○○구청]»으로
#   닫히므로 무검문 판정 = 지자체 발신 화재 문자 **전건** 긴급알림 = ⑭-e 취지("작아도 전국 뉴스가 되는 곳")의 정반대.
#   ⚠ 신설 사유 = 기존 게이트가 이 축을 하나도 안 봤다 — check_refs 계열은 전부 **정적 문자열·심볼 존재**를 보고,
#     smoke_* 는 **화면 렌더**를 본다. 「판정 함수가 실제로 무엇을 잡는가」는 축 자체가 없었다. 그래서 오탐이
#     ⓐ 기기 긴급알림 ⓑ fire_watch 「랜드마크=30」 하드 HI 승격(3시간 추적) ⓒ 자동 픽 후보까지 연쇄하는 동안
#     **어떤 게이트도 울리지 않았고**, 운영자 눈이 유일한 검출기였다(insta-thumb-miss·brk_misfire와 같은 축).
#   판정 = 정본 함수를 그대로 import 해 케이스 재판정(사전 복제 0 = 드리프트 0 · 네트워크·LLM·렌더 0).
#   면책표 없음 = 전건 하드(현행 위반 0 = 부채 원장 증가 0).
_DIS_LM_CASES = (
    # (본문, 기대 lm, 축 이름) — 기대 ''  = 미발동(오탐이면 안 되는 것) · 기대 값 = 반드시 잡혀야 하는 정본
    ('석남동 쿠팡물류센터 화재 관련 안전문제로 봉수대로 양방향 도로차단은 유지되오니 우회하시기 바랍니다. [서해구청]', '', '실사고 원본(말미 서명)'),
    ('현재 폭염 경보 발효 중, 정전으로 일시대피 중인 주민들께서는 안전한 장소로 이동하세요.[계양구청]', '', '공백 없는 서명'),
    ('오늘 21:35 충남(아산) 호우경보. 위험지역 출입 금지, 대피권고를 받으면 즉시 대피하세요. [행정안전부]', '', '목록어(DIS_LANDMARK)도 서명 안이면 미발동'),
    ('정전 복구 완료. 전력 사용 자제 바랍니다. [한국전력] [행정안전부]', '', '연속 서명 반복 제거'),
    ('시청역 3번 출구 인근 화재 발생. [중구청]', '', '`(?!역)` 오탐컷 보존'),
    ('숭례문 화재 발생, 인근 주민은 즉시 대피하세요. [서울시청]', '숭례문', '본문 랜드마크 = 서명이 있어도 잡힌다(놓침 0)'),
    ('강남구청 청사에서 화재가 발생했습니다. 우회하세요. [강남구청]', '강남구청', '본문 공공기관 청사 사고 = 잡힌다'),
    ('롯데월드타워 화재 신고 접수, 대피 중입니다.', '롯데월드타워', '서명 없는 문자 = 종전 동작 불변'),
)


def check_rpt_origin_coverage():
    """알림 리포트 출처표 = 뷰어 생산 알림 전건 커버(하드 · 260805 실사고 봉합).
    실사고 = 화재 알림(`sys:fire:`) 진단에서 리포트가 「만든 곳 = 서버 발행 메시지 · 판정 소스 =
    messages/sys:fire:….json · 상류 = scraper/msg.py」를 줬는데 **셋 다 틀렸다** — 그 알림은 뷰어
    fireMsgs()가 만들고, 지목된 파일은 **존재조차 하지 않는다**. 원인 = `_rptSrc()`에 그 접두 분기가
    없어 마지막 폴백(서버 발행 메시지)으로 떨어진 것. 리포트의 계약이 "세션이 파일을 바로 열게 하는 값"이라
    **없는 값보다 틀린 값이 더 비싸다** — 세션이 messages/ 를 뒤지다 진단이 늦었다(실측).
    구조적 원인 = 알림 생산자는 늘어나는데 출처표 분기는 손으로 따라가야 한다 = 조용히 갈라진다.
    판정 = 생산자 id 리터럴(`id: 'sys:…'`) 자동 발견 ↔ `_rptSrc` 분기(`startsWith('sys:…')`) 접두 대조.
    정적 · 렌더·LLM 0 · 면책표 없이 하드 0(현행 위반 0)."""
    p = os.path.join(ROOT, 'viewer', 'index.html')
    if not os.path.exists(p):
        print('❌ 리포트 출처표 게이트 — viewer/index.html 없음(fail-closed).')
        return 1
    src = open(p, encoding='utf-8').read()
    prods = sorted(set(re.findall(r"id:\s*'(sys:[^']*)'", src)))
    branches = sorted(set(re.findall(r"startsWith\('(sys:[^']*)'\)", src)))
    if not prods:
        print('❌ 리포트 출처표 게이트 — sys: 알림 생산자 0건(탐지 실패 = 게이트 무력화 · fail-closed).')
        return 1
    # 커버 = 분기가 생산자의 접두이거나 그 반대(생산자 'sys:src:reddit:' ↔ 분기 'sys:src:reddit:' 같은 세분화 허용)
    bad = [x for x in prods if not any(x.startswith(b) or b.startswith(x) for b in branches)]
    if bad:
        print('❌ 리포트 출처표 게이트 — 출처 분기 없는 알림 %d종(리포트가 세션에게 거짓 경로를 준다):' % len(bad))
        for b in bad:
            print('   ·', b, '→ _rptSrc() 에 분기 추가(만든 곳·판정 소스·상류 · 가능하면 cmd 재현 1줄)')
        return 1
    print('✅ 리포트 출처표 게이트 — 뷰어 생산 알림 %d종 전건 _rptSrc 분기 보유(폴백 오귀속 0).' % len(prods))
    return 0


# ── 요약 실패 알림 = 조치 주체를 말한다(👉 문단) = check_fail_msg_todo ─────────────────────────
# CONTRACT: check_fail_msg_todo
# 계약 = 「실패 사유 4분류(`_fk`) 중 **운영자 조치 3종**(timeout·congest·source)은 👉 문단을 달고,
#         **코드 축**(code)은 안 단다」.
# ⚠ 신설 사유 = 같은 병이 이 레포에서 **세 번** 재발했고 매번 생산자 한 종만 고쳐졌다 —
#   260728 `wd-phone` → 260808 `yt_cookie_health`·`fire_watch` → 260812 `insta_signals`.
#   요약 실패 알림(analyze·ask 두 경로)은 세 번 다 안 따라왔고, 260813 리포트에서 '클로드가 볼 일'
#   칸에 앉은 유일한 건이 바로 이 알림이었다(실제 조치 = 운영자가 기사를 다시 보내기 = 코드 축 0).
#   비용 = 조치 불요 건이 같은 칸의 **진짜 코드 결함**을 가린다.
# ⚠ 기존 게이트는 전부 다른 축 — `check_rpt_origin_coverage` = 알림이 **어디서 왔나**(출처표) ·
#   `check_seal_completeness` = 「같은 병의 형제」인데 **WARN**이라 이 재발을 세 번 다 못 막았다 ·
#   `check_ask_srcimg_chain` = 층 생존 → 「알림이 **누가 조치할 일인지** 말하는가」는 축 자체가 없었다.
# ⚠ 판정 술어는 **뷰어에서 읽는다**(사본 0) — `_RPT_CC_RE`·auto 판정 정규식을 손으로 옮겨 적으면
#   뷰어가 술어를 바꾼 날 게이트만 옛 기준으로 남는다(260812 쿠키 칸 이름 실사고와 같은 축).
# 정적 · 렌더·LLM·네트워크 0 · 면책표 없이 하드 0.
_FAILMSG_OP_KINDS = ('timeout', 'congest', 'source')   # 운영자 조치 3종 · code = 규약상 👉 없음(cc 유지)


def check_fail_msg_todo():
    idx = os.path.join(ROOT, 'viewer', 'index.html')
    if not os.path.exists(idx):
        print('❌ 실패알림 조치주체 게이트 — viewer/index.html 없음(판정 술어 원천 부재).')
        return 1
    vt = open(idx, encoding='utf-8', errors='ignore').read()
    m_cc = re.search(r'_RPT_CC_RE\s*=\s*/([^/\n]+)/', vt)
    m_auto = re.search(r'test\(todo\)\s*\?\s*.auto.\s*:', vt) and re.search(r'/(\^없[^/\n]*)/\.test\(todo\)', vt)
    if not m_cc or not m_auto:
        print('❌ 실패알림 조치주체 게이트 — 뷰어 _rptWho 판정 술어를 못 읽었다(앵커 소실 = fail-closed).')
        return 1
    cc_re, auto_re = re.compile(m_cc.group(1)), re.compile(m_auto.group(1))
    # 표면 자동 발견 = `_fk` 4분류를 가진 실패 알림 생산자(새 경로가 조용히 못 빠진다 · 스냅샷 제외)
    surf = [p for p in sorted(glob.glob(os.path.join(ROOT, '.github', 'scripts', '*.sh')))
            if '_versions' not in p and _has_exec_line(open(p, encoding='utf-8', errors='ignore').read(), '_fk=')]
    if len(surf) < 2:
        print('❌ 실패알림 조치주체 게이트 — 생산자 %d종(하한 2 · 탐지 실패 = 게이트 무력화 · fail-closed).' % len(surf))
        return 1
    bad = []
    for p in surf:
        rel, txt = os.path.relpath(p, ROOT), open(p, encoding='utf-8', errors='ignore').read()
        todo_lines = [ln for ln in txt.split('\n')
                      if '👉' in ln and ln.strip() and not ln.strip().startswith('#')]
        for kind in _FAILMSG_OP_KINDS:
            hit = [ln for ln in todo_lines if re.match(r'\s*%s\)' % kind, ln)]
            if not hit:
                bad.append('%s · %s 분기에 👉 문단 미배선 → 리포트가 「클로드가 볼 일」로 오분류' % (rel, kind))
                continue
            # 문구 재판정 = 뷰어 술어 그대로(op 여야 한다 · cc = 코드 칸 오귀속 · auto = 조치 필요한데 대기로 밀림)
            body = hit[0].split('👉', 1)[1].replace('네가 할 일:', '', 1).strip().strip("'\"; ")
            if auto_re.search(body):
                bad.append('%s · %s 문구가 「없어요/없음」으로 열려 자동 복구 대기로 튄다(운영자 조치가 묻힘)' % (rel, kind))
            elif cc_re.search(body):
                bad.append('%s · %s 문구에 「%s」가 있어 클로드 칸으로 튄다' % (rel, kind, cc_re.pattern))
        if any(re.match(r'\s*code\)', ln) for ln in todo_lines):
            bad.append('%s · code 분기에 👉 부착 — 규약 「원인이 코드 축이면 👉를 안 붙인다」 위반'
                       '(진짜 코드 결함이 운영자 칸으로 밀려 무증상이 된다)' % rel)
    if bad:
        print('❌ 실패알림 조치주체 게이트 — %d건:' % len(bad))
        for b in bad:
            print('   ·', b)
        return 1
    print('✅ 실패알림 조치주체 게이트 — 생산자 %d종 × 운영자 조치 3분류 전건 👉 보유(code 축 미부착 유지).' % len(surf))
    return 0


def check_disaster_landmark_sign():
    p = os.path.join(ROOT, 'scraper', 'sns_trends.py')
    if not os.path.exists(p):
        print('❌ 랜드마크 서명 게이트 — scraper/sns_trends.py 없음(fail-closed).')
        return 1
    src = open(p, encoding='utf-8').read()
    bad = []
    # ① 서명 컷 심볼 실존 — 지워지면 오탐이 통째로 부활한다(주석만 남고 코드가 사라지는 회귀 차단).
    for sym in ('DIS_SIGN_RE', '_dis_body'):
        if src.count(sym) < 2:   # 정의 1 + 사용 1 이상
            bad.append('%s 정의·사용 결손(서명 컷이 배선에서 빠짐)' % sym)
    if not re.search(r'def disaster_landmark\([^)]*\):(?:\s*"""(?:.|\n)*?""")?\s*\n\s*t = _dis_body\(', src):
        bad.append('disaster_landmark()가 _dis_body()를 통과하지 않음(원문 그대로 판정 = 서명 오탐 부활)')
    # ② 정본 함수 실측 재판정 — 심볼이 살아 있어도 '무엇을 잡는가'가 갈리면 소용없다.
    try:
        import importlib.util as _ilu   # check_rubric_regress 관용구 계승(지연 import = 게이트 밖 부담 0)
        spec = _ilu.spec_from_file_location('sns_trends_lm_gate', p)
        mod = _ilu.module_from_spec(spec)
        spec.loader.exec_module(mod)
        for text, exp, why in _DIS_LM_CASES:
            got = mod.disaster_landmark(text)
            if got != exp:
                bad.append('판정 어긋남[%s] 기대=%r 실제=%r' % (why, exp, got))
    except Exception as e:  # noqa: BLE001
        bad.append('정본 함수 로드/판정 실패(%s: %s)' % (type(e).__name__, e))
    if bad:
        print('❌ 랜드마크 서명 게이트 — 결손 %d건(재난문자 발신 서명이 즉시 긴급알림을 오발한다):' % len(bad))
        for b in bad:
            print('   ·', b)
        print('   → 정본 = scraper/sns_trends.py DIS_SIGN_RE·_dis_body (말미 «[○○구청]» 서명은 판정 대상 아님).')
        return 1
    print('✅ 랜드마크 서명 게이트 — 발신 서명 컷 생존 · 정본 재판정 %d케이스 전건 일치.' % len(_DIS_LM_CASES))
    return 0


def check_disaster_lm_stale():
    """⑭-e 랜드마크 판정 = **박제 필드** → 코드 봉합만으론 화면이 안 낫는다(260805 2차 실사고 봉합).
    실측 = 서명 오탐 봉합(10363a4)이 09:37 KST 에 main 에 착지했는데도, 07:03 에 이미 구워진 항목이
    `viewer/sns_trends.json` 에 lm="서해구청" 으로 살아남아 **10:20 알림 리포트에 그대로 재등장**했다.
    구조 = lm 은 수집 시점 1회 계산해 항목에 박는다(`"lm": disaster_landmark(msg)` · 생산자 2곳) →
    fireMsgs() 는 매 렌더 그 **저장값**을 다시 읽는다 → 판정 코드를 고쳐도 이미 구워진 데이터는 옛 판정을
    들고 남고 TTL 12h 동안 유령 경보가 재점등된다. 즉 **코드 봉합 ≠ 라이브 봉합**([7-2] 와 같은 축).
    ⚠ 신설 사유 = 짝 게이트 check_disaster_landmark_sign 은 정본 함수를 케이스로 재판정해 「코드가 옳은가」만
      본다. 「라이브 데이터에 구판 판정이 남아 있는가」는 축 자체가 없었고, 그래서 봉합 세션이 코드만 고치고
      완료로 닫아도 아무 게이트가 안 울렸다(운영자가 리포트를 열어야만 발견 = insta-thumb-miss 와 같은 축).
    판정 2축 =
      ① 뷰어 2층 검문 실존 = **하드**. 서버가 준 lm 이 «말미 발신 서명을 걷어낸 본문»에 실제로 있는지 소비
         지점에서 한 번 더 본다(사전 복제 0 = 형태 규칙 1줄). 지워지면 박제 유령이 통째로 부활한다.
      ② 라이브 데이터 재판정 불일치 = **WARN(비차단)**. 왜 하드가 아닌가 = ⓐ 판정 코드를 고치는 **바로 그 커밋**에서
         반드시 불일치가 뜬다(데이터는 아직 옛 판정) → 하드면 게이트가 봉합 자체를 막는 자기모순 ⓑ 데이터는 봇
         소유라 세션이 커밋으로 못 씻는다(기계산출물 손편집 금지) ⓒ ①이 살아 있으면 불일치는 화면에 안 뜬다
         = 무해. 그래서 「씻길 때까지 보이게」가 정확한 역할(check_component_lock WARN 선례 계승).
    정적 · 렌더·LLM·네트워크 0 · 면책표 없음."""
    bad = []
    v = os.path.join(ROOT, 'viewer', 'index.html')
    if not os.path.exists(v):
        print('❌ 랜드마크 박제 게이트 — viewer/index.html 없음(fail-closed).')
        return 1
    src = open(v, encoding='utf-8').read()
    # ① 뷰어 2층 검문 실존(하드) — 심볼 + fireMsgs 본문 배선 둘 다. 심볼만 남고 배선이 빠지면 무력화된다.
    for sym in ('DIS_SIGN_TAIL', 'function disBody('):
        if sym not in src:
            bad.append('뷰어 2층 검문 심볼 결손(%s) — 박제된 구판 lm 이 그대로 기기 긴급알림이 된다' % sym)
    m = re.search(r'function fireMsgs\(\)\s*\{', src)
    if not m:
        bad.append('fireMsgs() 탐지 실패(fail-closed = 게이트 무력화 방지)')
    elif 'disBody(' not in src[m.end():m.end() + 1200]:
        bad.append('fireMsgs() 가 disBody() 검문을 통과하지 않음(2층 방어 미배선 = 데이터가 더러우면 화면이 운다)')
    if bad:
        print('❌ 랜드마크 박제 게이트 — 결손 %d건(구판 판정이 박힌 데이터가 그대로 경보가 된다):' % len(bad))
        for b in bad:
            print('   ·', b)
        print('   → 정본 = viewer/index.html fireMsgs() 의 disBody(tx).includes(d.lm) 검문 1줄.')
        return 1
    # ② 라이브 데이터 재판정(WARN) — 저장된 lm 과 현행 정본 판정이 갈린 항목을 세어 보여준다.
    stale = []
    try:
        import importlib.util as _ilu
        p = os.path.join(ROOT, 'scraper', 'sns_trends.py')
        jp = os.path.join(ROOT, 'viewer', 'sns_trends.json')
        if os.path.exists(p) and os.path.exists(jp):
            spec = _ilu.spec_from_file_location('sns_trends_lm_stale', p)
            mod = _ilu.module_from_spec(spec)
            spec.loader.exec_module(mod)
            with open(jp, encoding='utf-8') as f:
                for it in (json.load(f).get('disaster') or []):
                    got = mod.disaster_landmark(it.get('text') or '')
                    if (it.get('lm') or '') != got:
                        stale.append((it.get('lm') or '', got, (it.get('time') or '')[:16]))
    except Exception as e:  # noqa: BLE001
        print('   · (참고) 라이브 재판정 스킵(%s: %s)' % (type(e).__name__, e))
    if stale:
        print('⚠ 랜드마크 박제 잔류 %d건 — 저장 lm ≠ 현행 판정(다음 수집 회차가 씻는다 · 그때까지 ①이 화면을 막는다):' % len(stale))
        for old, new, t in stale[:5]:
            print('   · %s 저장=%r → 현행=%r' % (t, old, new))
        print('   → 손편집 금지(기계산출물). 씻김 = 다음 sns-trends 회차 · 화면 = 뷰어 2층 검문이 이미 차단.')
    print('✅ 랜드마크 박제 게이트 — 뷰어 2층 검문 생존(심볼+fireMsgs 배선) · 라이브 잔류 %d건.' % len(stale))
    return 0


def _regress_ver(mod):
    """회귀 스탬프 전용 해시 = RUBRIC + judge 조립부 소스(정본 = .github/scripts/regress_lib.regress_ver).
    ⚠ 260810 실사고 = 두 게이트가 RUBRIC **문자열**만 해싱해서(mod.RUBRIC_VER) 프롬프트 *조립부*를
    바꾸면 해시가 그대로라 **회귀 0회로 라이브에 나갔다**(킬테스트 = 형제 배선 심고 110게이트 rc=0).
    ⚠ mod.RUBRIC_VER 자체는 건드리지 않는다 — 그 값은 candidates.json 도장이라 바꾸면 재판정 창
    안 전건이 되살아나 대량 재채점 = 과금 폭발이다. 그래서 **스탬프용 해시만 분리**한다.
    정본 재사용(사본 0) — 정본 로드 실패 시 rubric 축만으로 fail-soft(게이트를 죽이진 않는다)."""
    import importlib.util as _ilu
    try:
        rp = os.path.join(ROOT, '.github', 'scripts', 'regress_lib.py')
        sp = _ilu.spec_from_file_location('regress_lib_gate', rp)
        rl = _ilu.module_from_spec(sp)
        sp.loader.exec_module(rl)
        return rl.regress_ver(mod.RUBRIC, mod.judge)
    except Exception:
        return None


def check_rubric_regress():
    """루브릭 회귀 게이트(하드 · 운영자 260803 승인 — «대구 40.1도» 오발 봉합의 재발 방지 축).
    breaking_judge RUBRIC(속보 YES/NO 판정 프롬프트)이 바뀌면 과거 실측 판정 케이스(rubric_regress_cases.json ·
    실발송/실픽 이력 기반)를 드라이런 재판정해 정답 뒤집힘을 확인해야 커밋이 열린다 —
    통과 도장 = rubric_regress_stamp.json(rubric_ver). 이 게이트 자체는 정적 해시 대조뿐(네트워크·LLM 0) ·
    LLM 1콜은 `python3 .github/scripts/rubric_regress.py` 실행 시점에만. RUBRIC 무변경 커밋 = 도장 유효 = 무비용 통과."""
    import importlib.util as _ilu
    bj_p = os.path.join(ROOT, '.github', 'scripts', 'breaking_judge.py')
    st_p = os.path.join(ROOT, '.github', 'scripts', 'rubric_regress_stamp.json')
    cs_p = os.path.join(ROOT, '.github', 'scripts', 'rubric_regress_cases.json')
    spec = _ilu.spec_from_file_location('breaking_judge_gate', bj_p)
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    try:
        cases = json.loads(open(cs_p, encoding='utf-8').read())['cases']
        assert cases and all(c.get('t') and c.get('expect') in ('YES', 'NO') for c in cases)
    except Exception as e:
        print('❌ 루브릭 회귀 게이트 — 케이스 원장 파손/누락(%s): %s' % (os.path.basename(cs_p), e))
        return 1
    try:
        st = json.loads(open(st_p, encoding='utf-8').read())
    except Exception:
        st = {}
    # ⚠️ 케이스 **개수**도 함께 본다(평의회2 260803 실측 지적) — rubric_ver 만 보면 「케이스만 추가하고 회귀는
    # 안 돌린 커밋」이 조용히 통과했다가, 나중에 RUBRIC 을 한 글자 건드린 **다른 세션**이 그 미검증 케이스의
    # 뒤집힘으로 스탬프를 못 찍어 영구 rc=1 에 갇힌다(자기가 안 심은 지뢰를 밟는 구조). 스탬프는 이미 cases 를 굽는다.
    # 조립부 해시 축 승격 완료(260810) — 짝인 check_grade_regress와 동일 축.
    # ⚠ 승격이 막혀 있던 사유(모스크바 건)는 해소됐다: 「러 모스크바 시내 카페 폭발 3명 사망·
    # 15명 부상」이 🌐 해외 군사 게이트에 걸려 NO 로 떨어지던 건인데, 실측해 보니 그 게이트의
    # 열거는 **군사충돌**(공습·폭격·미사일·드론·포격)이라 민간 카페 폭발은 애초에 대상이 아니었고
    # 모델이 「러시아 = 전쟁 중」으로 읽어 군사충돌로 분류한 것이었다. 운영자 260810 판단
    # 「긴급이 맞음」에 따라 RUBRIC 에 **민간 대상 폭발·테러는 이 게이트 미적용** 예외를 명문화
    # (🔪 게이트의 「사고성은 그대로 O」 문법 계승 · 교전 지역 공습발 폭발은 🌐 유지 = 전쟁 피로 축 보존).
    _rv = _regress_ver(mod)
    _want = _rv or mod.RUBRIC_VER          # 정본 로드 실패 = 구 축으로 fail-soft
    _got = st.get('regress_ver') if _rv else st.get('rubric_ver')
    if _got != _want or st.get('cases') != len(cases):
        print('❌ 루브릭 회귀 게이트 — RUBRIC/조립부/케이스 변경 후 회귀 미실행(과거 정답 뒤집힘 미확인 = 커밋 차단).')
        print('   → python3 .github/scripts/rubric_regress.py 실행(케이스 %d건 × 3회 다수결·전건 통과 시 도장) 후 스탬프 함께 커밋.' % len(cases))
        print('   (stamp=%s · now=%s)' % (_got, _want))
        return 1
    print('✅ 루브릭 회귀 게이트 — RUBRIC+조립부 %s = 회귀 도장 일치(케이스 %d건 · 판정 뒤집힘 확인 완료분).' % (_want, len(cases)))
    return 0


_STYLE_BASE = {           # 260810 실측 스냅샷(queue 최근 60건) — 늘면 WARN · 줄면 낮추라고 알린다
    'lead_date': 35.0,    # IG 🔎 리드가 날짜·시각으로 열림 (21/60)
    'gloss': 1.7,         # 용어 풀이 문장 「~는 …하는 제도다」 (1/60)
    'preach': 0.0,        # 마지막 📍이 훈계로 닫힘 (0/60)
    'claim_p90': 136,     # 자수 표기 vs 실측 오차 p90 (블록 156개)
}
_STYLE_N = 60             # 표본 = queue 최근 N건


def check_style_ratchet():
    """요약 문체 회귀 래칫(WARN·비차단 · 운영자 260810 "ㄱㄱ" · 평의회 6 설계안 1안).
    ⚠️ 신설 사유 = **이 레포 게이트 105개 중 요약 문체를 보는 축이 0개였다.** 그래서
    260801 규칙 신설도·260810 제거도·260704 effort 하향도 전부 **무검증으로 라이브에 나갔다**
    (260704 회귀는 IG 617→537 = −13%였는데 21일간 아무도 안 울렸고 digest_guard 주석에만 남았다).
    운영자가 실제로 불만을 말한 축인데 회귀 하네스가 breaking·grade 룰북에만 있었다.
    ⚠️ **정답지를 「좋은 글」이 아니라 「실패 모드」로 잡는 게 실효 조건** — 「이 리드가 좋은가」는
    답이 여럿이라 정답 라벨이 원리적으로 불가능하지만, 「이 리드가 날짜로 여는가」는 답이 하나다.
    260810 커밋이 겨눈 축 전부가 그 형태다(날짜 리드·용어 풀이·훈계 착지 = 전부 금지형).
    ⚠️ **하드 금지** = 문체는 오탐이 구조적이다(속보·재난은 날짜 리드가 정본 예외 · 평의회 3 실측 =
    재난 층 43.9% vs 그 외 11.5%). 하드면 레포가 언다 → 래칫이 유일한 정합 형태
    (check_gate_hits·check_component_lock 선례). 판정은 사람이 하고 게이트는 보이게만 한다.
    ⚠️ claim_gap 축 = 평의회 8 발견 — 모델 자가 자수 표기가 **전건 한 방향**(미달을 합격으로 위장)으로
    어긋난다(260810 실측 최대 290자). 「N/800」이 규격 준수의 증거가 아니라 미달을 가리는 표지가 된다.
    정적 · 렌더·LLM·네트워크 0."""
    qd = os.path.join(ROOT, 'queue')
    if not os.path.isdir(qd):
        return 0
    files = sorted(f for f in os.listdir(qd) if f.endswith('.md'))[-_STYLE_N:]
    if len(files) < 20:
        print("⏳ 문체 래칫 — 표본 %d건(<20) = 판정 유예." % len(files))
        return 0
    lead_re = re.compile(r'^\s*(?:\d+월\s*\d+일|\d+일\s|\d+시\s|지난\s*\d+|간밤|어젯밤|오늘\s*(?:새벽|오전|오후))')
    gloss_re = re.compile(r'(?:는|은)\s*[^.]{0,40}?(?:하는|되는)\s*(?:제도|절차|조치|단계|경보령|규정)(?:다|이다)|을 뜻한다|를 말한다|이란\s')
    preach_re = re.compile(r'(?:해야 한다|필요한 시점이다|묻고 있다|과제로 남았다|숙제다)\.?\s*$')

    def _blk(t, lab):
        m = re.search(r'### \[' + lab + r'[^\]]*\]\s*```text\n(.*?)```', t, re.S)
        return m.group(1).strip() if m else None

    n = lead = gloss = preach = 0
    gaps = []
    for fn in files:
        try:
            t = open(os.path.join(qd, fn), encoding='utf-8').read()
        except Exception:
            continue
        ig = _blk(t, 'IG')
        if not ig:
            continue
        n += 1
        lines = [l for l in ig.split('\n') if l.strip()]
        ld = next((l for l in lines if l.lstrip().startswith('🔎')), None)
        if ld and lead_re.match(ld.lstrip()[1:].strip()):
            lead += 1
        if gloss_re.search(ig):
            gloss += 1
        ps = [l for l in lines if l.lstrip().startswith('📍')]
        if ps and preach_re.search(ps[-1].strip()):
            preach += 1
        for lab in ('IG', 'Thread', '자유요약'):
            b = _blk(t, lab)
            cm = re.search(r'### \[' + lab + r' — 약 (\d+)', t)
            if b and cm:
                gaps.append(abs(int(cm.group(1)) - len(b)))
    if n < 20:
        print("⏳ 문체 래칫 — IG 블록 보유 %d건(<20) = 판정 유예." % n)
        return 0
    gaps.sort()
    cur = {
        'lead_date': round(lead / n * 100, 1),
        'gloss': round(gloss / n * 100, 1),
        'preach': round(preach / n * 100, 1),
        'claim_p90': gaps[int(len(gaps) * 0.9)] if gaps else 0,
    }
    up = [(k, _STYLE_BASE[k], v) for k, v in cur.items() if v > _STYLE_BASE[k]]
    down = [(k, _STYLE_BASE[k], v) for k, v in cur.items() if v < _STYLE_BASE[k]]
    if up:
        print("⚠️ 문체 래칫(WARN·비차단) — 금지형 술어 발생률 증가(표본 %d건):" % n)
        for k, b, v in up:
            print("   · %s: %s → %s (기준 초과 · 지침 개정이 의도한 방향인지 확인)" % (k, b, v))
    if down:
        print("✅ 문체 래칫 — 개선분 %d축(%s) → 해소분은 _STYLE_BASE를 그 자리에서 낮춰라(남겨두면 같은 회귀가 조용히 재통과)."
              % (len(down), ' · '.join("%s %s→%s" % (k, b, v) for k, b, v in down)))
    if not up and not down:
        print("✅ 문체 래칫 — 4축 전건 스냅샷 동일(표본 %d건 · 신규 회귀 0)." % n)
    return 0


def check_grade_regress():
    """grade 룰북 회귀 게이트(하드 · 운영자 260807 "전부 반영" — 평의회 8인 · check_rubric_regress[breaking 전용]의 짝).
    gate_judge RUBRIC(경중 0~3 채점 프롬프트)이 바뀌면 운영자 수기 재채점 정답지(grade_regress_cases.json ·
    260807 ~58행)를 드라이런 재채점해 정답 뒤집힘 0을 확인해야 커밋이 열린다 —
    통과 도장 = grade_regress_stamp.json(rubric_ver·cases). 게이트 자체는 정적 해시 대조뿐(네트워크·LLM 0) ·
    LLM 1콜은 `python3 .github/scripts/grade_regress.py` 실행 시점에만. RUBRIC 무변경 커밋 = 도장 유효 = 무비용 통과.
    ⚠️ 신설 사유 = breaking 룰북엔 이 보호가 있는데 grade 룰북은 무게이트였다(오채점 = 운영자 "큐레이션 의미가 사라짐")."""
    import importlib.util as _ilu
    gj_p = os.path.join(ROOT, '.github', 'scripts', 'gate_judge.py')
    st_p = os.path.join(ROOT, '.github', 'scripts', 'grade_regress_stamp.json')
    cs_p = os.path.join(ROOT, '.github', 'scripts', 'grade_regress_cases.json')
    spec = _ilu.spec_from_file_location('gate_judge_gate', gj_p)
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    try:
        cases = json.loads(open(cs_p, encoding='utf-8').read())['cases']
        assert cases and all(c.get('t') and c.get('expect') in (0, 1, 2, 3) for c in cases)
    except Exception as e:
        print('❌ grade 회귀 게이트 — 케이스 원장 파손/누락(%s): %s' % (os.path.basename(cs_p), e))
        return 1
    try:
        st = json.loads(open(st_p, encoding='utf-8').read())
    except Exception:
        st = {}
    # 케이스 **개수**도 함께 본다(check_rubric_regress 평의회2 260803 교훈 계승) — ver만 보면 「케이스만 추가하고
    # 회귀는 안 돌린 커밋」이 통과했다가 다음 RUBRIC 개정 세션이 미검증 케이스의 뒤집힘으로 영구 rc=1에 갇힌다.
    _rv = _regress_ver(mod)
    _want = _rv or mod.RUBRIC_VER          # 정본 로드 실패 = 구 축으로 fail-soft
    _got = st.get('regress_ver') if _rv else st.get('rubric_ver')
    if _got != _want or st.get('cases') != len(cases):
        print('❌ grade 회귀 게이트 — RUBRIC/조립부/케이스 변경 후 회귀 미실행(운영자 정답지 뒤집힘 미확인 = 커밋 차단).')
        print('   → python3 .github/scripts/grade_regress.py 실행(케이스 %d건 × 3회 다수결·전건 통과 시 도장) 후 스탬프 함께 커밋.' % len(cases))
        print('   (stamp=%s · now=%s)' % (_got, _want))
        return 1
    print('✅ grade 회귀 게이트 — RUBRIC+조립부 %s = 회귀 도장 일치(케이스 %d건 · 운영자 260807 정답지 뒤집힘 확인 완료분).' % (_want, len(cases)))
    return 0


def check_gate_docs():
    src = open(os.path.join(ROOT, 'shared', 'check_refs.py'), encoding='utf-8').read()
    gates = re.findall(r'^def (check_[a-z_]+)\(', src, re.M)
    canon = ''
    for d in _GATE_DOC_CANON:
        p = os.path.join(ROOT, d)
        if os.path.exists(p):
            canon += open(p, encoding='utf-8').read()
    missing = [g for g in gates if g not in canon and g not in _GATE_DOC_BASELINE]
    if missing:
        print('❌ 게이트 문서화 메타 게이트 — 신규 게이트가 정본 문서 미등재("만들어놓고 안 봄" 차단 · 260723 Q468):')
        for g in missing:
            print('   -', g, '→ 정본 문서(SSOT §6 디자인 / docs curation / CLAUDE.md)에 이름 등재하라(순수 인프라면 _GATE_DOC_BASELINE 추가 + 사유 = diff로 가시화).')
        return 1
    undoc = sum(1 for g in gates if g not in canon)
    print('✅ 게이트 문서화 메타 게이트 — %d게이트 = 정본 등재 %d · 베이스라인 면책 %d(신규 미등재 0 · 소급 TODO = 베이스라인 축소).'
          % (len(gates), len(gates) - undoc, undoc))
    return 0


def check_ssot_linkage():
    """공유 부품 SSOT 링크 연결성 게이트(WARN·비차단 · 운영자 260723 Q466 · 디자인기틀 §0-17 5축 등재의 얕은 기계 보조).
    `viewer/nm-*.js`(공유 부품 관례) 각 파일이 발견 체인 3축(디자인기틀_SSOT.md · CII · CLAUDE.md)에 모두 언급되나 얕게 대조.
    미링크 = 고아 SSOT 후보 WARN(하드차단 아님 = 오탐 관용·연결성 강화 전용 · 기틀 문서 무증축 = 게이트는 코드에만)."""
    import glob as _g
    idx = ['디자인기틀/디자인기틀_SSOT.md', '디자인기틀/CII_컴포넌트계승인덱스.md', 'CLAUDE.md']
    txt = {}
    for d in idx:
        try:
            txt[d] = open(os.path.join(ROOT, d), encoding='utf-8').read()
        except Exception:
            txt[d] = ''
    parts = sorted(_g.glob(os.path.join(ROOT, 'viewer', 'nm-*.js')))
    orphans = []
    for fp in parts:
        name = os.path.basename(fp)
        miss = [os.path.basename(d) for d in idx if name not in txt[d]]
        if miss:
            orphans.append('%s → 미링크: %s' % (name, ', '.join(miss)))
    if orphans:
        print('⚠️ SSOT 링크 게이트(WARN·비차단) — 공유 부품이 발견 체인 미등재(§0-17 5축·고아 후보 · 등재 = 디자인기틀 §0/§1·CII·CLAUDE [15]):')
        for o in orphans:
            print('   ·', o)
        return 0
    print('✅ SSOT 링크 게이트 — 공유 부품(nm-*.js %d) 전건 발견 체인(디자인기틀·CII·CLAUDE) 링크됨.' % len(parts))
    return 0




def check_tabs_headers():
    """도구 스튜디오 탭 src(.html)의 _headers no-cache 등재 게이트(운영자 260724 한 수 · 순수 인프라 · SSOT §6 등재).
    index.html THUMB_TABS·CAP_TABS·ASK_TABS의 모든 스튜디오 /x.html이 viewer/_headers에 /x·/x.html 두 경로
    no-cache로 등재됐는지 대조 — 신설 스튜디오가 캐시 계약을 빠뜨리면(tr 260721·song/nb/sb 과거 드리프트 선례)
    새 배포가 하드새로고침 없이 반영 안 되던 사각을 커밋 단계서 차단(게이트 문서화 메타 게이트와 동일 철학 = '만들고 등재 안 함' 봉쇄)."""
    idx = open(os.path.join(ROOT, 'viewer', 'index.html'), encoding='utf-8').read()
    hdr = open(os.path.join(ROOT, 'viewer', '_headers'), encoding='utf-8').read()
    srcs = set()
    for m in re.finditer(r'const (?:THUMB_TABS|CAP_TABS|ASK_TABS)\s*=\s*(\[.*?\]);', idx, re.S):
        srcs.update(re.findall(r"src:\s*'/([a-z0-9_-]+)\.html'", m.group(1)))
    if not srcs:
        print('⚠️ 탭 헤더 게이트 — 탭 배열 파싱 0(THUMB_TABS/CAP_TABS/ASK_TABS 구조 변동?) = 스킵(비차단).')
        return 0
    missing = []
    for name in sorted(srcs):
        for route in ('/%s.html' % name, '/%s' % name):
            if not re.search(r'^%s\n[ \t]*Cache-Control:[ \t]*no-cache' % re.escape(route), hdr, re.M):
                missing.append(route)
    if missing:
        print('❌ 탭 헤더 게이트 — 스튜디오 탭 src가 _headers no-cache 미등재(새 배포 미반영 위험 · tr·song/nb/sb 드리프트 선례 · 운영자 260724):')
        for r in missing:
            print('   -', r, '→ viewer/_headers에 "%s" + 다음 줄 "  Cache-Control: no-cache" 등재(형제 /thumb.html 계약 계승).' % r)
        return 1
    # ── 부품 축(운영자 260810 "모든 웹앱이 동시에 개선되어야해 · 안고쳤으면 버그인거임") ──
    # ⚠ 실사고 = 화면(html)만 등재돼 있고 **그 화면이 물고 있는 공유 부품(nm-*.js/css)은 10종이 미등재**였다.
    #   결과 = 새 배포가 화면에만 반영되고 부품은 옛 판 잔류 → "고쳤다는데 그대로"(운영자 눈이 유일한 검출기).
    #   특히 nm-sync.js = 새 배포 자동 반영 담당 부품 자신이 미등재 = 갱신기가 자기를 못 갱신하는 상태였다.
    #   ⚠ 구판은 **탭 src(.html)만** 봐서 이 축이 통째로 사각이었다 — 부품은 뷰어가 늘 때마다 조용히 늘고,
    #   등재는 손 목록이라 새 부품이 매번 빠진다(sb 260718·tr 260723·vd 260802에 이은 같은 드리프트 4회째).
    # 판정 = 표면 자동 발견(viewer/*.html이 실제로 참조하는 nm-* 부품 = 손 레지스트리 0) · 리터럴 `nm-` 앵커 스캔.
    parts, users = set(), {}
    for vp in sorted(glob.glob(os.path.join(ROOT, 'viewer', '*.html'))):
        try:
            vt = open(vp, encoding='utf-8').read()
        except Exception:
            continue
        for p in re.findall(r'(?:src|href)="(nm-[a-z0-9_-]+\.(?:js|css))"', vt):
            parts.add(p)
            users.setdefault(p, set()).add(os.path.basename(vp))
    pmiss = [p for p in sorted(parts)
             if not re.search(r'^/%s\n[ \t]*Cache-Control:[ \t]*no-cache' % re.escape(p), hdr, re.M)]
    if pmiss:
        print('❌ 탭 헤더 게이트(부품 축) — 뷰어가 물고 있는 공유 부품이 _headers no-cache 미등재'
              ' = 새 배포가 화면에만 반영되고 부품은 옛 판 잔류(운영자 260810):')
        for p in pmiss:
            print('   - /%s (쓰는 화면 %d개: %s) → viewer/_headers에 "/%s" + 다음 줄 "  Cache-Control: no-cache"'
                  % (p, len(users[p]), ', '.join(sorted(users[p])[:4]), p))
        return 1
    print('✅ 탭 헤더 게이트 — 스튜디오 탭 src %d개 + 공유 부품 %d종 전부 _headers no-cache 등재'
          '(.html+clean 두 경로 · 부품 = 뷰어 참조 자동 발견 · 캐시 계약 정합).' % (len(srcs), len(parts)))
    return 0


_AAC_SEL_RE = re.compile(r'bv\*[^\s"\'`]*')   # 리터럴 `bv*` 앵커 = O(매치수) · 여는-괄호-앞 와일드카드 금지 규율 준수
_AAC_SKIP_MARK = ('--skip-download', '--print')   # 미디어를 0바이트도 안 받는 호출 = 병합 없음 = 축 비대상
_AAC_EXT = ('.yml', '.yaml', '.py', '.sh', '.bat', '.command', '.js', '.mjs', '.ps1')
_AAC_SKIP_DIR = ('_versions/', 'docs/reports/', 'published/', 'node_modules/')


def _aac_strip_py_docstrings(src):
    """파이썬 독스트링을 줄 단위로 비운다(ast = 구조적 판정 = 손 면책표 0).
    사고 설명이 코드처럼 읽히는 것을 막는다(예: nomute_threads.py 정렬 관례 설명이 `-f "bv*+ba/b/best"`를 인용)."""
    lines = src.split('\n')
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return lines   # 파싱 불가 = 독스트링 비우기만 생략(판정 자체는 계속 = fail-closed 방향)
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        b = getattr(node, 'body', None)
        if not b or not isinstance(b[0], ast.Expr) or not isinstance(b[0].value, ast.Constant):
            continue
        if not isinstance(b[0].value.value, str):
            continue
        for i in range(b[0].lineno - 1, min(b[0].end_lineno, len(lines))):
            lines[i] = ''
    return lines


def _aac_units(rel, src):
    """(첫줄번호, 판정텍스트) 목록 — 주석 제거 + 파이썬 암묵 문자열 연결(줄바꿈으로 쪼갠 셀렉터) 병합.
    병합이 없으면 `f"bv*+ba[ext=m4a]/"` / `f"bv*+ba/b/best"` 2줄 분할이 둘째 줄만 보고 위양성이 된다."""
    py = rel.endswith('.py')
    lines = _aac_strip_py_docstrings(src) if py else src.split('\n')
    out = []
    for i, ln in enumerate(lines):
        s = ln.strip()
        su = s.upper()
        if s.startswith('#') or s.startswith('//') or s.startswith('*') or su.startswith('REM ') or su.startswith('::'):
            continue   # 주석 줄 = 비대상(구조적 면책 · 손 목록 0)
        if py and out and out[-1][0] - 1 + out[-1][1] == i and re.match(r'^[rbfRBF]{0,2}["\']', s) \
                and re.search(r'["\']\s*$', lines[i - 1].rstrip()):
            out[-1] = (out[-1][0], out[-1][1] + 1, out[-1][2].rstrip()[:-1] + s[s.index(s.lstrip('rbfRBF')[0]) + 1:])
            continue   # 암묵 연결 = 앞 리터럴의 닫는 따옴표와 이 줄의 여는 따옴표를 지워 한 문자열로 잇는다
        out.append((i + 1, 1, ln))
    return [(n, t) for n, _c, t in out]


def check_thumb_prompt_sanity():
    """뉴스 픽 AI 썸네일 = **발사 프롬프트 자기모순 0**(하드 · 운영자 260805 "아이디어 ㄱㄱ").

    ⚠ 신설 사유 = 이 레포 게이트는 **정적 문자열**(check_refs 계열)이거나 **화면 렌더**(smoke_*)뿐이라
      「러너가 실제로 조립해 발사하는 프롬프트가 스스로 모순인가」는 축 자체가 없었다. 그 사각에서
      260805 실측 5축이 잠복했다(표본 = cards/*/thumbs/prompts.json 236건 = 실제 발사분 재판독):
        ① CAMERA 자기모순 6%  — 한 줄 안에서 "front-on … symmetrical" ∧ "not a flat head-on"
        ② EXPRESSION 시선 중복 10% — CAMERA가 이미 말한 응시를 EM 코드가 재지시 → 표정 축이 밀림
        ③ MOOD 메타어 59%     — emotion frontmatter의 집필 지시어('N순위'·'포지셔닝')가 값에 그대로
        ④ SUBJECT 문장 통째 98% — 「얼굴을 그려라」 자리에 한줄요약 전문 = 제2의 장면이 SCENE과 경합
        ⑤ SCENE 위계 부재     — 연출 줄 6~8개가 각자 장면을 암시하면 모델이 '평균'을 그린다
      운영자에게는 「이미지가 별로다」로만 보여서 원인 판별이 사람 눈에만 의존했다(insta-thumb-miss·
      brk_misfire 와 같은 축 = 조용히 나빠지는 것을 숫자로 드러낸다).

    판정 = **정본 함수 재판정**(check_disaster_landmark_sign 문법 계승) — thumb_gen.build_prompt 를
    import 해 대표 케이스로 실제 조립하고 모순 술어를 센다. 사전·정규식 사본 0(정본 1곳 계약 유지) ·
    네트워크·LLM·렌더 0 · **면책표 없이 하드 0**(현행 위반 0 = 부채 원장 증가 0).
    ⚠ 케이스는 **라이브러리 실코드(AG/LGT/SG/EM TSV)** 를 그대로 태운다 — 새 연출 코드가 들어와도
      같은 술어로 재판정되므로, 「메뉴만 늘리고 조립을 안 본」 회귀가 커밋 시점에 걸린다.
    ⚠ 짝 축(WARN) = 이미 구워진 prompts.json 재판독. 그건 **기계산출물·과거 발사분**이라 세션이 커밋으로
      못 씻는다 → 하드로 두면 봉합 커밋 자신이 막히는 자기모순(check_disaster_lm_stale ② 선례) →
      「씻길 때까지 보이게」가 정확한 역할. 새 픽이 돌면 자연 감소한다.
    """
    tg_dir = os.path.join(ROOT, '.github', 'scripts')
    tg_path = os.path.join(tg_dir, 'thumb_gen.py')
    if not os.path.exists(tg_path):
        print('❌ 썸네일 프롬프트 게이트 — .github/scripts/thumb_gen.py 없음(fail-closed).')
        return 1
    os.environ.setdefault('GEMINI_API_KEY', 'gate-noop')   # 모듈 상단 no-op 분기 회피(호출 0 = 과금 0)
    sys.path.insert(0, tg_dir)
    try:
        import importlib
        tg = importlib.import_module('thumb_gen')
        importlib.reload(tg)
    except Exception as e:
        print('❌ 썸네일 프롬프트 게이트 — thumb_gen import 실패(fail-closed): %s' % e)
        return 1
    finally:
        if sys.path and sys.path[0] == tg_dir:
            sys.path.pop(0)

    # 대표 케이스 = 실측 사고를 그대로 재현하는 축들(정면 AG · 응시 EM · 메타어 emotion · 문장 lead).
    SCENE = '굳은 눈으로 단상에서 발언하는 50대 남성, 그 앞줄에 고개를 숙인 제복 차림 간부들, 흰 형광등 아래 오전.'
    LEAD = ('이재명 대통령이 8월 5일 청와대 영빈관에서 외교·국방·통일·보훈부 업무보고를 받으며 '
            '외교·안보의 정쟁화를 지적하고, 정부와 여당을 향해 결과로 책임지라고 주문했다.')
    # ⚠️ 케이스는 **실측 사용 빈도 상위 코드**로 짠다 — 첫 판에서 임의 AG 코드를 골랐더니 그 코드들이
    #    애초에 정면 어휘를 안 실어 ①② 술어가 한 번도 발동하지 않았고, 킬테스트 K1(조건부 제거 = 사고 원복)이
    #    **그대로 통과**했다(게이트가 있으나 안 잡는 상태). 정면축 정본 = AG-08(큐 실측 3위·35건)·EM-12(응시).
    CASES = [   # (dispatch, emotion)
        ('AG-08 LGT05 SG-07 EM-12', '미묘한 냉소 1순위'),          # 정면 AG + 응시 EM + 메타어(실사고 재현)
        ('AG-08 LGT02 EM-08', '분노와 허탈감이 1순위 — 스크롤이 멎는 지점'),
        ('AG-01 LGT02 SG-09', '비통함 1순위'),                      # 최다 사용(눈높이) — 위양성 대조축
        ('AG-18 LGT08 DF-07 GST-03', '억울함'),                     # 부감·거리 지정 = 병기 억제 경로
        ('', ''),                                                   # dispatch 무지정(화풍 기본 폴백)
    ]
    # 모순 술어 — 전부 「같은 프롬프트 안에서 서로를 무효화하는 두 문장」만 잡는다(문체 취향 판정 0).
    FRONT = re.compile(r'front[- ]?on|head[- ]?on|straight[- ]?on|symmetr|frontal', re.I)
    GAZE = re.compile(r'(?:in)?to the camera|eye contact', re.I)
    META = re.compile(r'순위|포지셔닝|독자|스크롤')
    bad = []
    for disp, emo in CASES:
        for sid, _label, look, cam_default in tg.STYLES:
            like = sid in ('webtoon', 'watercolor')
            p = tg.build_prompt(look, cam_default, SCENE, disp, '', hook='화두 한 마디', emotion=emo,
                                foreign=False, cam_lock=(sid == 'watercolor'),
                                light_mod=tg._LIGHT_MOD.get(sid, ''), likeness=like,
                                subject=(tg._subject_name(LEAD) if like else ''))
            L = p.split('\n')
            tag = '%s/[%s]' % (sid, disp or '무지정')
            cam = next((x for x in L if x.startswith('CAMERA:')), '')
            # ① 정면을 지시하면서 같은 줄에서 정면을 금지 = 모델이 둘을 평균내 어중간한 각도로 도망간다
            if 'not a flat head-on' in cam and FRONT.search(cam.split(', a frozen split-second')[0]):
                bad.append('%s CAMERA 자기모순(정면 지시 ∧ 정면 금지 동시)' % tag)
            exp = next((x for x in L if x.startswith('EXPRESSION')), '')
            # ② CAMERA가 이미 응시를 지시했는데 EXPRESSION이 또 응시 = 같은 지시 2회 → 표정 축이 밀린다
            if exp and GAZE.search(exp) and FRONT.search(cam):
                bad.append('%s EXPRESSION 시선 중복(CAMERA와 같은 지시 2회)' % tag)
            mood = next((x for x in L if x.startswith('MOOD')), '')
            # ③ 감정 자리에 집필 메타어 = 이미지 모델엔 순수 노이즈(라벨이 'emotion'이라 더 헷갈린다)
            if mood and META.search(mood):
                bad.append('%s MOOD 메타어 누출(%s)' % (tag, mood.split('): ', 1)[-1][:30]))
            subj = next((x for x in L if x.startswith('SUBJECT')), '')
            # ④ 얼굴 지시 자리에 문장 = 그 문장의 장소·시각이 제2의 장면으로 SCENE과 싸운다
            if subj and len(subj.split('): ', 1)[-1]) > 35:
                bad.append('%s SUBJECT가 인명 아닌 문장(%d자)' % (tag, len(subj.split('): ', 1)[-1])))
            # ⑤ SCENE 위계 = 아래 연출 줄이 전부 '어떻게'만 말한다는 못박음. 빠지면 장면 경합이 부활한다
            if tg.SCENE_PRIME not in p:
                bad.append('%s SCENE 위계줄(SCENE_PRIME) 누락' % tag)
    if bad:
        print('❌ 썸네일 프롬프트 자기모순 게이트 — %d건:' % len(bad))
        for b in bad[:14]:
            print('   ·', b)
        print('   → 정본 = .github/scripts/thumb_gen.py build_prompt(모순은 «지시 vs 금지» 두 문장 중 하나를 조건부로).')
        return 1
    print('✅ 썸네일 프롬프트 자기모순 게이트 — 케이스 %d × 화풍 %d 전건 5술어 청정(정본 함수 재판정 · LLM 0).'
          % (len(CASES), len(tg.STYLES)))

    # ── 짝 축(WARN·비차단) — 이미 구워진 발사분에 구판 모순이 남아 있는가(데이터는 세션이 못 씻는다) ──
    stale, seen = {}, 0
    for pf in sorted(glob.glob(os.path.join(ROOT, 'cards', '*', 'thumbs', 'prompts.json')))[-120:]:
        try:
            recs = json.load(open(pf, encoding='utf-8'))
        except Exception:
            continue
        if not isinstance(recs, dict):
            continue
        seen += 1
        for _sid, p in recs.items():
            if not isinstance(p, str):
                continue
            L = p.split('\n')
            cam = next((x for x in L if x.startswith('CAMERA:')), '')
            mood = next((x for x in L if x.startswith('MOOD')), '')
            subj = next((x for x in L if x.startswith('SUBJECT')), '')
            exp = next((x for x in L if x.startswith('EXPRESSION')), '')
            if 'not a flat head-on' in cam and FRONT.search(cam.split(', a frozen split-second')[0]):
                stale['CAMERA 자기모순'] = stale.get('CAMERA 자기모순', 0) + 1
            if exp and GAZE.search(exp) and FRONT.search(cam):
                stale['EXPRESSION 시선 중복'] = stale.get('EXPRESSION 시선 중복', 0) + 1
            if mood and META.search(mood):
                stale['MOOD 메타어'] = stale.get('MOOD 메타어', 0) + 1
            if subj and len(subj.split('): ', 1)[-1]) > 35:
                stale['SUBJECT 문장 통째'] = stale.get('SUBJECT 문장 통째', 0) + 1
    if stale:
        print('⚠️ 구 발사분 잔류(WARN·비차단) — 최근 %d기사에 구판 모순이 남아 있다: %s'
              % (seen, ' · '.join('%s %d' % kv for kv in sorted(stale.items()))))
        print('   · 데이터는 기계산출물이라 커밋으로 못 씻는다 — 새 픽이 돌면 자연 감소 · 옛 기사는 뷰어 「다시 만들기」.')
    elif seen:
        print('✅ 구 발사분 잔류 0 — 최근 %d기사 전건 청정.' % seen)
    return 0


def check_ytdlp_aac():
    """yt-dlp 오디오 코덱 = AAC 강제(하드 · 운영자 260805 "유튜브를 편집가능한 자료까지 받아오게").
    계약 = **병합 셀렉터의 알몸 `ba` 앞에는 반드시 `ba[ext=m4a]` 사본이 선다.**
    ⚠ 신설 사유 = 전형적인 조용한 실패 — 2단이 겹쳐야 터진다.
      ⓐ yt-dlp 기본 acodec 우선순위가 opus > aac 라 `ba`가 유튜브 251(Opus)을 140(AAC)보다 먼저 집는다.
      ⓑ `--merge-output-format mp4`를 주면 `_utils.get_compatible_ext()`가 allow_mkv=False가 되어
         mp4가 Opus와 비호환인 걸 알면서도 mp4를 반환한다(옵션이 없으면 mkv로 떨어져 즉시 눈치챈다).
      → 어도비 지원 오디오 목록에 Opus가 없어 **임포트는 되는데 오디오 트랙만 조용히 무시**된다.
         팟플·VLC·인스타 업로드는 멀쩡하고 에러도 안 뜬다 = 운영자 눈이 유일한 검출기였다.
    기존 게이트가 못 잡는 이유 = 전부 다른 축이다(check_workflow_yaml = 문법 · check_paths = 경로 실존 ·
      smoke_* = 화면 렌더) → 「받은 파일이 편집 툴에 물리는가」는 축 자체가 없었다.
    판정 = 정적(렌더·LLM·네트워크 0) · 표면 자동 발견(git ls-files 중 `bv*`∧`+ba` 보유 = 새 호출부가
      조용히 못 빠진다) · **면책표 없이 하드 0** — 예외 2종은 구조적이다(주석·독스트링 / `--skip-download`·`--print`
      = 미디어를 0바이트도 안 받는 호출). ⚠ 처방으로 `-S "acodec:aac"`를 쓰지 마라(실측 = acodec 정렬이 res를
      앞질러 format 18[640x360] 통합포맷이 이겨 화질이 통째로 망가진다) · `--postprocessor-args "Merger:-c:a aac"`도
      금지(이미 AAC인 것까지 매번 재인코딩)."""
    bad = []
    try:
        tracked = subprocess.run(['git', 'ls-files'], cwd=ROOT, capture_output=True,
                                 text=True, timeout=60).stdout.split('\n')
    except Exception as e:
        print('⚠️ yt-dlp AAC 게이트 — git ls-files 실패:', e)
        return 0
    for rel in tracked:
        if rel == 'shared/check_refs.py':
            continue   # 자기참조 차단 — 위 처방문의 「수정 전」 예시가 곧 위반 문자열이다(check_clip_coverage 템플릿 배제 선례). 판정자는 yt-dlp를 호출하지 않는다 = 호출부 아님
        if not rel.endswith(_AAC_EXT) or any(rel.startswith(d) or ('/' + d) in rel for d in _AAC_SKIP_DIR):
            continue
        p = os.path.join(ROOT, rel)
        try:
            src = open(p, encoding='utf-8', errors='replace').read()   # .bat = CP949 · 셀렉터는 전부 ASCII라 무손실
        except OSError:
            continue
        if 'bv*' not in src or '+ba' not in src:
            continue
        for lineno, text in _aac_units(rel, src):
            if '+ba' not in text or any(m in text for m in _AAC_SKIP_MARK):
                continue
            for m in _AAC_SEL_RE.finditer(text):
                sel = m.group(0)
                if '+ba' not in sel:
                    continue
                # 판정 = **가지 단위**. `/`로 쪼갠 각 가지 중 알몸 `+ba`를 쓰는 가지는, 자기와 글자가 같고
                # `+ba`만 `+ba[ext=m4a]`인 쌍둥이 가지가 **앞에** 서 있어야 한다.
                # ⚠ 「어딘가 앞에 m4a가 있으면 통과」로 두면 안 된다 — 실측 킬테스트에서
                #   `bv*[h<=1080][ext=mp4]+ba[ext=m4a]/b[…]/bv*[h<=1080]+ba/b[h<=1080]` 같은
                #   **다른 가지**의 m4a가 3번 가지의 알몸 ba를 가려 미검출이 났다(위 가지는 mp4 비디오가
                #   없으면 통째로 실패하고 3번 가지가 실제 착지점이 된다 = 그 자리가 Opus).
                br = sel.split('/')
                for k, b in enumerate(br):
                    i = b.find('+ba')
                    if i < 0 or b[i + 3:i + 4] == '[':
                        continue   # 알몸 아님(= `+ba[ext=…]`) 또는 오디오 병합 없는 가지
                    twin = b[:i] + '+ba[ext=m4a]' + b[i + 3:]
                    if twin not in br[:k]:
                        bad.append((rel, lineno, sel, b, twin))
                        break
    if bad:
        print('❌ yt-dlp 오디오 코덱 게이트 — 알몸 `ba`(=Opus 확정) 병합 가지 %d건:' % len(bad))
        for rel, lineno, sel, b, twin in bad:
            print('   - %s:%d' % (rel, lineno))
            print('       셀렉터 = %s' % sel[:200])
            print('       알몸 가지 = %s   →   그 앞에 `%s` 를 세워라' % (b, twin))
        print('   ⚠ -S "acodec:aac" 금지(acodec 정렬이 res를 앞질러 저화질 통합포맷이 이긴다) ·')
        print('     --postprocessor-args "Merger:-c:a aac" 금지(이미 AAC인 것까지 매번 재인코딩).')
        return 1
    print('✅ yt-dlp 오디오 코덱 게이트 — 병합 셀렉터 전건 AAC 우선(알몸 ba 0 · 면책표 없음).')
    return 0


# ── 이미지 산출 포맷 게이트(운영자 260805 "아이디어 ㄱ" · 260805 JPG q90 통일의 짝) ───────────────
# 투명/무손실이 정당 사유인 축 = PNG 허용. 그 외 산출은 JPEG q90 단일.
_IMGFMT_SKIP_DIR = ('_versions/', 'docs/', '.claude/', 'node_modules/', 'cards/', 'queue/', 'asks/')
_IMGFMT_SKIP_FILE = ('shared/check_refs.py',)   # 자기참조(처방문 예시 문자열이 곧 위반) — check_ytdlp_aac 선례
# PNG가 정당한 사유 어휘(호출 줄 + 상행 8줄 안 어디든) — 「왜 투명·무손실이어야 하나」의 코드 근접 명문화.
_IMGFMT_PNG_OK = ('rgba', 'alpha', '투명', 'overlay', '오버레이', 'cutout', '누끼',
                  'mask', '마스크', 'clipboard', '클립보드', 'clipboarditem',
                  'icon', '아이콘', 'favicon', '무손실', 'lossless', '도먼트', 'dormant')
_IMGFMT_QOK = 'q-ok:'   # 산출물이 아닌 인코딩(화면 장식·LLM 첨부 압축 등) 면제 마커 — CSS raw-ok/reuse-ok 관례 계승
# ⚠ 부정문 무효화 — 「투명 영역이 **없다**」처럼 같은 어휘가 반대 뜻으로 쓰인 줄은 사유로 안 친다.
#    (킬테스트 K4 실측 = tr.html JPG 전환 주석 "번역 카드는 투명 영역이 없다"가 PNG 사유로 통과하던 구멍)
_IMGFMT_NEG = ('없다', '없음', '없어', '아니', '아님', '불필요', '금지', '대신', 'not ', 'no alpha')


def _imgfmt_args(src, open_paren):
    """여는 괄호 위치 → 균형 닫힘까지의 인자 텍스트(상한 400자 · 멀티라인 호출 대응).
    ⚠ 정규식 `[^)]*` 류를 쓰지 않는 이유 = viewer/index.html 1.85MB에서 매 위치 되짚기가
    게이트 전체 시간을 먹는다(260804 실측 = 그런 규칙 한 줄이 17.9s)."""
    depth, out = 0, []
    for i in range(open_paren, min(len(src), open_paren + 400)):
        c = src[i]
        if c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0:
                break
        out.append(c)
    return ''.join(out[1:])


def _imgfmt_has_reason(lines, lineno):
    """호출 줄 + 상행 5줄 안에 PNG 정당 사유가 **긍정문으로** 있는가.
    ⚠ 줄 단위로 본다 — 마커 어휘가 있어도 그 줄에 부정어가 함께 있으면 무효(킬테스트 K4 봉합)."""
    for ln in lines[max(0, lineno - 5):lineno + 1]:
        low = ln.lower()
        if any(m in low for m in _IMGFMT_PNG_OK) and not any(n in low for n in _IMGFMT_NEG):
            return True
    return False


def _imgfmt_is_comment(line, col):
    """호출 키워드가 주석 안인가(py `#` · js `//` · 블록 주석 이어지는 ` * `).
    ⚠ 킬테스트 K7 봉합 = 주석 속 예시 코드(`cv2.imencode('.png', x)`)를 위반으로 세던 구멍.
       `//` 판정은 앞에 `:`가 붙은 `https://`를 배제한다."""
    head = line[:col]
    if '#' in head:
        return True
    if re.search(r'(?<!:)//', head):
        return True
    return line.lstrip().startswith(('*', '/*'))


def _imgfmt_qval(txt, fname, src):
    """인자 텍스트에서 JPEG 품질값 추출 → (값, 원문) · 못 찾으면 (None, 원문).
    변수 경유(`quality=q` · `TR_JPGQ`)는 같은 파일에서 기본값/할당을 1회 추적한다(정적 한계 = 못 찾으면 fail-open)."""
    m = re.search(r'quality\s*=\s*(\d+)', txt) or re.search(r'IMWRITE_JPEG_QUALITY\s*,\s*(\d+)', txt)
    if m:
        return int(m.group(1)), m.group(0)
    m = re.search(r"image/jpeg'\s*,\s*([0-9.]+)", txt) or re.search(r'image/jpeg"\s*,\s*([0-9.]+)', txt)
    if m:
        return round(float(m.group(1)) * 100), m.group(0)
    # 변수 경유 — 이름을 뽑아 같은 파일의 기본값/할당에서 실값을 찾는다
    v = (re.search(r'quality\s*=\s*([A-Za-z_][\w.]*)', txt)
         or re.search(r'IMWRITE_JPEG_QUALITY\s*,\s*([A-Za-z_][\w.]*)', txt)
         or re.search(r"image/jpeg['\"]\s*,\s*([A-Za-z_][\w.]*)", txt))
    if v:
        name = re.escape(v.group(1).split('.')[-1])
        d = (re.search(r'\b%s\s*=\s*([0-9.]+)' % name, src)          # def f(..., q=90) / const X = 0.9
             or re.search(r'\b%s\s*=\s*([0-9.]+)\s*[,;)]' % name, src))
        if d:
            n = float(d.group(1))
            return (round(n * 100) if n <= 1 else int(n)), '%s=%s' % (v.group(1), d.group(1))
    return None, txt[:60]


def check_image_format():
    """이미지 산출 포맷 게이트(하드 · 운영자 260805 "아이디어 ㄱ" — 같은 날 JPG q90 통일의 짝).

    계약 2축:
      ⓐ **PNG로 굽는 곳은 왜 그래야 하는지가 코드 옆에 있어야 한다.** 투명(알파)·무손실(바이너리 마스크)·
         API 제약(ClipboardItem은 image/png만 안정)·아이콘 같은 정당 사유 어휘가 호출 줄 상행 5줄 안에 없으면 FAIL.
         ⚠ 어휘가 **부정문**으로 쓰인 줄은 사유로 안 친다(「투명 영역이 없다」 = JPG 쪽 설명 · 킬테스트 K4 실측 봉합).
      ⓑ **JPEG 인코딩 품질은 90 단일.** 산출이 아닌 인코딩(화면 장식 블러·LLM 첨부 압축)은 줄에 `q-ok: 사유`를 단다.

    ⚠ 신설 사유 = **「산출 포맷」이라는 축을 보는 게이트가 하나도 없었다.** 260805 전수 실측:
      · `thumb_gen.py`가 R2 키를 항상 `.png`로 굽는데 실물은 Gemini가 준 JPEG = **거짓 확장자가 6주 넘게 무증상**
        (Content-Type은 매직바이트로 맞게 나가서 화면이 멀쩡했다 = 운영자 눈에도 안 보였다).
      · JPEG 품질이 90·92·94·95 **4갈래**로 갈렸다 — `gen_image.py` 주석이 260710에 이미 "전 JPEG 저장 경로
        통일"을 선언해 놓고 다른 파일들이 안 따라온 것.
      · 이 게이트의 **첫 실행이 곧바로 `apps/track/track_analyze.py` q82 2건을 잡았다** — 260805 손 전수감사가
        `quality=`·`jpg_bytes` 어휘만 훑어 `cv2.IMWRITE_JPEG_QUALITY, 82`를 통째로 놓친 자리다(사람 눈의 한계 실증).
    기존 게이트가 전부 다른 축이다 — `check_refs` 계열 = 정적 **문자열·경로 실존**, `smoke_*` = **화면 렌더**,
    `check_ytdlp_aac` = **받는 쪽** 코덱. 「우리가 굽는 바이트가 무슨 포맷·무슨 품질인가」는 축 자체가 없었다.

    판정 = 정적(렌더·LLM·네트워크 0) · 표면 자동 발견(`git ls-files` — 새 생성기가 조용히 못 빠진다) ·
           **면책표 없이 하드 0**(현행 위반 0 = 부채 원장 증가 0).
    ⚠ 스코프 밖(구조적) = `_versions/`(과거 스냅샷 보존) · `docs/`·`cards/`(산출·보고 자산) · `.claude/` ·
       `shared/smoke_*`·`*shot*`(테스트 하네스가 굽는 프로브 이미지는 산출물이 아니다) · `shared/check_refs.py` 자신.
    ⚠ 남는 한계 = 변수 경유 품질값은 같은 파일 1회 추적까지만(다른 모듈에서 import한 상수는 못 따라간다) =
       **fail-open**(못 찾으면 통과) — 위양성으로 레포를 얼리는 것보다 놓치는 쪽이 싸다(insta-thumb-miss 동축)."""
    import subprocess as _sp
    try:
        files = _sp.run(['git', 'ls-files'], cwd=ROOT, capture_output=True, text=True, timeout=60).stdout.split('\n')
    except Exception:
        print('⚠️ 이미지 산출 포맷 게이트 — git ls-files 실패(스킵)')
        return 0
    png_bad, jpg_bad, seen = [], [], 0
    for rel in files:
        if not rel or rel.startswith(_IMGFMT_SKIP_DIR) or rel in _IMGFMT_SKIP_FILE:
            continue
        base = os.path.basename(rel)
        if rel.startswith('shared/') and (base.startswith('smoke_') or 'shot' in base):
            continue
        if not rel.endswith(('.py', '.js', '.mjs', '.html')):
            continue
        p = os.path.join(ROOT, rel)
        try:
            src = open(p, encoding='utf-8').read()
        except Exception:
            continue
        if not any(k in src for k in ('toBlob(', 'toDataURL(', '.save(', 'imencode(', 'imwrite(')):
            continue   # 리터럴 선행 컷 = 1.85MB 파일도 O(매치수)로만 돈다
        lines = src.split('\n')
        # 줄 시작 오프셋 → 오프셋에서 줄번호 역산(bisect)
        offs, acc = [], 0
        for ln in lines:
            offs.append(acc); acc += len(ln) + 1
        for kw in ('toBlob(', 'toDataURL(', '.save(', 'imencode(', 'imwrite('):
            i = src.find(kw)
            while i != -1:
                op = i + len(kw) - 1
                args = _imgfmt_args(src, op)
                lo = bisect.bisect_right(offs, i) - 1
                line = lines[lo]
                if _imgfmt_is_comment(line, i - offs[lo]):
                    i = src.find(kw, i + 1); continue   # 주석 속 예시 코드 = 무대상(K7)
                low = args.lower()
                is_png = ("'image/png'" in low or '"image/png"' in low
                          or re.search(r'["\']png["\']', low) or re.search(r'\.png["\']', low))
                is_jpg = ("image/jpeg" in low or re.search(r'["\']jpe?g["\']', low)
                          or re.search(r'\.jpe?g["\']', low) or 'imwrite_jpeg_quality' in low)
                if is_png and not is_jpg:
                    seen += 1
                    if not _imgfmt_has_reason(lines, lo):
                        png_bad.append((rel, lo + 1, line.strip()[:150]))
                elif is_jpg:
                    seen += 1
                    if _IMGFMT_QOK not in line:
                        q, raw = _imgfmt_qval(args, rel, src)
                        if q is not None and q != 90:
                            jpg_bad.append((rel, lo + 1, q, raw[:60], line.strip()[:130]))
                i = src.find(kw, i + 1)
    if png_bad or jpg_bad:
        print('❌ 이미지 산출 포맷 게이트 — 위반 %d건(PNG 사유 없음 %d · JPEG 비-q90 %d):'
              % (len(png_bad) + len(jpg_bad), len(png_bad), len(jpg_bad)))
        for rel, lineno, line in png_bad:
            print('   - [PNG 사유 없음] %s:%d' % (rel, lineno))
            print('       %s' % line)
            print('       → 투명·무손실이 필요하면 그 사유를 호출 상행 8줄 안에 쓴다(어휘: 투명·RGBA·마스크·오버레이·누끼·클립보드·아이콘·무손실).')
            print('         필요 없으면 JPEG q90으로 굽는다(운영자 260805 계약).')
        for rel, lineno, q, raw, line in jpg_bad:
            print('   - [JPEG 비-q90] %s:%d — 실측 q%s (%s)' % (rel, lineno, q, raw))
            print('       %s' % line)
            print('       → q90으로 맞추거나, 산출물이 아니면 그 줄에 `q-ok: 사유` 마커를 단다.')
        return 1
    print('✅ 이미지 산출 포맷 게이트 — 인코딩 호출 %d건 전건 정합(PNG = 투명·무손실 사유 명문 · JPEG = q90 단일 · 면책표 없음).' % seen)
    return 0

# ── 계약 앵커 게이트(운영자 260805 "머지 ㄱ" · check_image_format의 짝) ────────────────────────
# 문법 = 주석에 `CONTRACT: <게이트명>` → 그 계약을 강제하는 게이트가 실존하고 러너에 배선돼 있어야 한다.
# ⚠ 다중 이름 구분자는 `,` **하나뿐**이다 — `·`를 허용했더니 이 레포의 일반 구분자(`CONTRACT: check_x · q90 = …`)를
#    먹어 뒤 낱말까지 게이트 이름으로 읽었다(첫 실행 실측 = `q90`을 고아 앵커로 오검출). 앵커 뒤 산문은 `·`·`—`로 잇는다.
_CONTRACT_RE = re.compile(r'CONTRACT:\s*(check_[A-Za-z_0-9]+(?:\s*,\s*check_[A-Za-z_0-9]+)*)')
_CONTRACT_SKIP_DIR = ('_versions/', 'docs/', '.claude/', 'node_modules/', 'cards/', 'queue/', 'asks/')
_CONTRACT_SKIP_FILE = ('shared/check_refs.py',)   # 자기참조 = 처방문·정규식 자신이 곧 앵커로 읽힌다(check_ytdlp_aac 선례)


def check_contract_anchors():
    """계약 앵커 게이트(하드 · 운영자 260805 "머지 ㄱ" — `check_image_format`의 짝).

    ⚠ 신설 사유 = **이 레포의 계약은 주석으로 선언되는데, 주석엔 강제력이 0이라 조용히 낡는다.**
      실사고(260805 실측) = `gen_image.py`가 260710에 「전 JPEG 저장 경로 통일」이라고 **주석으로 선언**해
      놓고 `resize_image`(92)·`upscale_image`(94)·`recompose_card`(95)·`card_news`(95)·`img_mosaic`(92)가
      **6주 동안 아무도 안 따라왔다**. 선언은 있었고 위반도 있었는데 **그 사이를 잇는 것이 없었다** —
      운영자가 "모두 jpg 90으로" 라고 말해줄 때까지 아무도 안 울렸다.
      이 레포엔 그런 선언형 주석이 수백 개다(260710·260716·260802…) — **지금 어느 게 살아있고 어느 게
      죽었는지 기계로 아는 방법이 없다.** 이 게이트가 그 다리다.

    계약 2축:
      ① **앵커 → 게이트 실존·배선.** 어디든 주석에 `CONTRACT: <이름>`을 달면 그 이름의 게이트가
         `shared/check_refs.py`에 정의돼 있고 **러너에 배선**돼 있어야 한다. 없으면 FAIL
         = 「강제 장치 없는 계약 선언」을 구조적으로 못 만든다. 게이트를 지우면 그 앵커들이 고아로 뜬다.
      ② **게이트 → 배선.** 정의만 되고 한 번도 호출 안 되는 게이트 = 「만들어놓고 안 돎」 → FAIL.
         ⚠ 짝 게이트 `check_gate_docs`는 **문서 등재**만 본다(이름이 CLAUDE.md에 적혔나) — 「그래서
         실제로 도는가」는 축 자체가 없었다. 문서에만 있고 안 도는 게이트 = 가장 비싼 거짓 안심.

    판정 = 정적(렌더·LLM·네트워크 0) · 표면 자동 발견(`git ls-files`) · **면책표 없이 하드 0**
           (260805 실측 = 앵커 6건 전건 유효 · 미배선 게이트 0건 · 부채 원장 증가 0).
    ⚠ 스코프 밖(구조적) = `_versions/`·`docs/`·`cards/`·`.claude/`(스냅샷·보고 자산) ·
       `shared/check_refs.py` 자신(처방문·정규식 리터럴이 곧 앵커로 읽힌다 = `check_ytdlp_aac` 선례) ·
       **`.md` 전량**(문서의 처방문 예시가 곧 앵커 — 첫 실행이 CLAUDE.md의 `CONTRACT: check_x · …`
       설명문을 고아 앵커로 검출했다 · 앵커의 거처는 강제할 코드 옆이고 문서 축은 `check_gate_docs` 전담).
    ⚠ 남는 한계 = 앵커를 **안 다는 것**은 못 막는다(주석 문법 채택은 자발) — 이 게이트가 막는 건
       「달아놓고 강제가 없는 것」과 「강제가 사라졌는데 선언만 남은 것」이다. 씨앗 = 6주 드리프트가
       실제로 났던 그 줄들부터(gen_image·thumb_gen·tr·card_news·img_mosaic·yt-dlp)."""
    import subprocess as _sp
    gsrc = open(os.path.join(ROOT, 'shared', 'check_refs.py'), encoding='utf-8').read()
    defined = set(re.findall(r'^def (check_[a-z_0-9]+)\(', gsrc, re.M))
    wired = {g for g in defined if re.search(r'(?<!def )\b%s\s*\(' % re.escape(g), gsrc)}

    # ② 게이트 → 배선(정의만 되고 안 도는 게이트 = 거짓 안심)
    fails = []
    for g in sorted(defined - wired):
        fails.append(('미배선 게이트', 'shared/check_refs.py', 0, g,
                      '정의만 있고 호출 0건 — 러너(main)에 `if %s() != 0: rc = 1` 로 배선하라(문서에만 있고 안 도는 게이트 = 거짓 안심).' % g))

    # ① 앵커 → 게이트 실존·배선
    try:
        files = _sp.run(['git', 'ls-files'], cwd=ROOT, capture_output=True, text=True, timeout=60).stdout.split('\n')
    except Exception:
        print('⚠️ 계약 앵커 게이트 — git ls-files 실패(스킵)')
        return 0
    anchors = 0
    for rel in files:
        if not rel or rel.startswith(_CONTRACT_SKIP_DIR) or rel in _CONTRACT_SKIP_FILE:
            continue
        if not rel.endswith(('.py', '.js', '.mjs', '.html', '.sh', '.yml')):
            continue   # ⚠ `.md` 비대상(구조적) = 문서의 **처방문 예시**가 곧 앵커로 읽힌다(첫 실행 실측 =
            #    CLAUDE.md에 쓴 `CONTRACT: check_x · …` 설명문을 고아 앵커로 검출) · 앵커의 거처는
            #    **강제할 코드 옆**이고 문서 축은 짝 게이트 `check_gate_docs`가 전담한다(check_refs.py
            #    자기참조 배제와 동축 · check_ytdlp_aac 선례).
        if False:
            continue
        p = os.path.join(ROOT, rel)
        try:
            src = open(p, encoding='utf-8').read()
        except Exception:
            continue
        if 'CONTRACT:' not in src:
            continue   # 리터럴 선행 컷 = 1.85MB 파일도 O(매치수)
        lines = src.split('\n')
        for lineno, ln in enumerate(lines, 1):
            m = _CONTRACT_RE.search(ln)
            if not m:
                continue
            for name in re.split(r'\s*,\s*', m.group(1)):
                anchors += 1
                if name not in defined:
                    fails.append(('고아 앵커', rel, lineno, name,
                                  '이 이름의 게이트가 shared/check_refs.py 에 없다 — 게이트를 만들거나(계약을 실제로 강제) 앵커를 지워라(계약 폐기).'))
                elif name not in wired:
                    fails.append(('죽은 앵커', rel, lineno, name,
                                  '게이트는 있는데 러너에 배선이 없다 = 선언만 있고 안 돈다 — main에 배선하라.'))
    if fails:
        print('❌ 계약 앵커 게이트 — 위반 %d건(강제 없는 계약 선언 차단):' % len(fails))
        for kind, rel, lineno, name, why in fails:
            print('   - [%s] %s%s — `%s`' % (kind, rel, (':%d' % lineno) if lineno else '', name))
            print('       %s' % why)
        return 1
    print('✅ 계약 앵커 게이트 — CONTRACT 앵커 %d건 전건 유효(게이트 실존 ∧ 러너 배선) · 미배선 게이트 0 · 정의 %d개 전부 가동(면책표 없음).'
          % (anchors, len(defined)))
    return 0

# ── 게이트 실효성 원장(운영자 260805 "돌리고 머지 ㄱㄱ" · check_contract_anchors의 짝) ──────────
# 계약 = 게이트가 rc≠0을 낸 순간은 반드시 원장에 1줄 적재된다(계측 없는 게이트 금지 = _gate_hits_install이 자동 보장).
# ⚠ 여기에 `CONTRACT:` 앵커를 안 다는 이유 = check_refs.py 자신은 앵커 스코프 밖(자기참조 배제)이라 달아도 안 세어진다 = 죽은 장식.
_GATE_HITS_PATH = 'shared/gate_hits.jsonl'
_GATE_HITS_CAP = 2000        # 롤링 상한(초과분 = 오래된 줄부터 버림 · fail_ledger 400줄 관례 계승·게이트는 표본이 성기다)
_GATE_HITS_MIN_DAYS = 90     # 관측 기간이 이보다 짧으면 「미발화」를 보고하지 않는다(원장 신설 직후 전건 미발화 = 잡음)


def _gate_hits_on():
    return os.environ.get('GATE_HITS', '').strip() != '0'   # 킬스위치 = GATE_HITS=0


def _gate_hits_append(rec):
    """원장 1줄 적재(전 경로 fail-soft — 계측이 게이트를 절대 못 죽인다)."""
    try:
        p = os.path.join(ROOT, _GATE_HITS_PATH)
        rows = []
        if os.path.exists(p):
            with open(p, encoding='utf-8') as f:
                rows = [ln for ln in f.read().split('\n') if ln.strip()]
        if not rows:
            rows = [json.dumps({'_meta': {
                'since': datetime.datetime.now().astimezone().isoformat(timespec='seconds'),
                'note': '기계산출물 — 손편집 금지(생성 = shared/check_refs.py _gate_hits_append)'}},
                ensure_ascii=False)]
        rows.append(json.dumps(rec, ensure_ascii=False))
        if len(rows) > _GATE_HITS_CAP:                      # 롤링 — _meta(첫 줄)는 항상 보존
            rows = rows[:1] + rows[-(_GATE_HITS_CAP - 1):]
        with open(p, 'w', encoding='utf-8') as f:
            f.write('\n'.join(rows) + '\n')
    except Exception:
        pass


def _gate_hits_read():
    """원장 → (since datetime|None, {게이트명: 발화횟수}) · 손상 줄은 건너뛴다(fail-soft)."""
    since, hits = None, {}
    try:
        p = os.path.join(ROOT, _GATE_HITS_PATH)
        if not os.path.exists(p):
            return None, {}
        for ln in open(p, encoding='utf-8'):
            ln = ln.strip()
            if not ln:
                continue
            try:
                o = json.loads(ln)
            except Exception:
                continue
            if '_meta' in o:
                try:
                    since = datetime.datetime.fromisoformat(o['_meta'].get('since', ''))
                except Exception:
                    since = None
            elif o.get('gate'):
                hits[o['gate']] = hits.get(o['gate'], 0) + 1
    except Exception:
        return None, {}
    return since, hits


def _gate_hits_probe(name, fn):
    """게이트 1개를 계측 래퍼로 감싼다 — rc≠0이면 원장에 1줄."""
    import functools

    @functools.wraps(fn)
    def _w(*a, **kw):
        # ⚠ **게이트 자신이 깨지면 그건 통과가 아니다**(260814 실측 자기적발) — 호출부는 게이트를
        #   try 로 감싸 「⚠️ … 스킵」만 찍고 넘어간다(레포를 얼리지 않으려는 정당한 설계). 그런데
        #   그 줄이 ✅ 백 줄 사이에 섞여서, 이 세션은 **없는 이름을 참조해 죽은 게이트를 통과로 읽었다**
        #   (킬테스트 3종이 전부 무검출인데 rc=0). 「안 도는 게이트」가 가장 비싼 거짓 안심이라
        #   여기서 ❌ 모양으로 한 줄 더 찍는다 — 판정은 안 바꾼다(rc 무접촉 = 얼리지 않는다).
        try:
            rc = fn(*a, **kw)
        except Exception as _e:   # noqa: BLE001
            print('❌ 게이트가 죽었다(판정 아님 · 게이트 자체 결함) — {}: {}'.format(name, str(_e)[:180]))
            raise
        try:
            if rc and _gate_hits_on():
                _gate_hits_append({'gate': name, 'rc': int(rc),
                                   'ts': datetime.datetime.now().astimezone().isoformat(timespec='seconds')})
        except Exception:
            pass
        return rc
    return _w


def _gate_hits_install():
    """전 `check_*` 함수를 계측 래퍼로 치환.

    ⚠ **호출부를 한 줄도 안 고친다**는 게 이 방식의 요점 — 러너의 `if check_x() != 0: rc = 1` 이 85번
    반복되는 구조라 손으로 감싸면 diff가 85곳이고, 새 게이트가 계측을 빼먹는 게 기본값이 된다
    (= 「계측 안 붙은 게이트」가 조용히 생기는 축 = 이 원장이 막으려는 것과 같은 병).
    globals() 치환이라 **새로 추가되는 게이트도 자동으로 계측에 편입**된다.
    ⚠ 소스 텍스트를 읽는 게이트(`check_gate_docs`·`check_contract_anchors`)는 `def` 선언을 정규식으로
       보므로 래핑과 무관(functools.wraps로 __name__도 보존)."""
    g = globals()
    for n in [k for k in list(g) if k.startswith('check_') and callable(g[k])]:
        if not getattr(g[n], '_gh_wrapped', False):
            w = _gate_hits_probe(n, g[n])
            w._gh_wrapped = True
            g[n] = w


def check_gate_hits():
    """게이트 실효성 원장(WARN·비차단 · 운영자 260805 "돌리고 머지 ㄱㄱ" · `check_contract_anchors`의 짝).

    ⚠ 신설 사유 = **85개 게이트가 도는데 「어느 게이트가 실제로 무언가를 잡은 적이 있는지」를 아무도 모른다.**
      260805 하루만 봐도 `check_image_format`은 켜자마자 track q82 2건을, `check_contract_anchors`는 자기
      설계 오류 2건을 잡았다 — 반면 **한 번도 아무것도 못 잡은 게이트**가 몇 개인지는 미확인이었다.
      그런 게이트는 ⓐ 진짜 청정한 축이거나 ⓑ **판정이 헐거워 아무것도 안 걸리는 죽은 게이트**인데,
      계측이 없으면 둘을 구분할 방법이 없다 = 게이트 수가 늘수록 pre-commit만 느려지고 안심은 가짜가 된다
      (`check_gate_docs` = 문서에 적혔나 · `check_contract_anchors` = 배선됐나 · 이 게이트 = **일을 하나**).

    동작 = 전 게이트를 자동 래핑해 rc≠0 순간을 `shared/gate_hits.jsonl`에 1줄 적재 → 관측 90일이 넘으면
           그동안 **0회 발화한 게이트 목록**을 커밋 출력에 띄운다(줄이는 근거 = 부채 래칫 "줄이는 건 자유" 동축).
    ⚠ **WARN·비차단**이 정확한 역할 — 미발화가 곧 결함은 아니다(청정한 축일 수 있다). 하드로 두면
       레포가 언다(`check_component_lock`·`check_disaster_lm_stale` ② 선례).
    ⚠ 관측 90일(_GATE_HITS_MIN_DAYS) 미만이면 미발화를 **보고하지 않는다** — 원장 신설 직후엔 전건이 미발화라 그대로 띄우면
       「85개 전부 죽었다」는 거짓 신호가 된다(정직한 유예).
    킬스위치 = `GATE_HITS=0` · 전 경로 fail-soft(계측 실패가 게이트를 못 죽인다) ·
    원장 = **기계산출물 손편집 금지**(값 변경 = 이 코드를 고쳐 다음 실행이 재생성)."""
    if not _gate_hits_on():
        print('⏸️ 게이트 실효성 원장 — 킬스위치(GATE_HITS=0)로 비활성.')
        return 0
    gsrc = open(os.path.join(ROOT, 'shared', 'check_refs.py'), encoding='utf-8').read()
    gates = set(re.findall(r'^def (check_[a-z_0-9]+)\(', gsrc, re.M))
    since, hits = _gate_hits_read()
    fired = sum(hits.values())
    if since is None:
        # ⚠ **여기서 원장을 실제로 만든다** — 안 만들면 `since`가 영영 안 박혀 관측이 시작조차 안 된다
        #    (발화가 있어야만 파일이 생기는 구판 = 매 실행 "관측 시작"만 찍고 90일 카운트가 0에서 멈춘다 · 260805 실측 봉합).
        _gate_hits_append({'gate': '_bootstrap', 'rc': 0,
                           'ts': datetime.datetime.now().astimezone().isoformat(timespec='seconds')})
        print('⏳ 게이트 실효성 원장 — 관측 시작(원장 신설 · 발화 0건) · %d일 후부터 미발화 게이트를 보고한다.'
              % _GATE_HITS_MIN_DAYS)
        return 0
    days = (datetime.datetime.now().astimezone() - since).days
    if days < _GATE_HITS_MIN_DAYS:
        print('⏳ 게이트 실효성 원장 — 관측 %d일차 · 발화 %d건(게이트 %d종) · %d일차부터 미발화 목록 보고.'
              % (days, fired, len(hits), _GATE_HITS_MIN_DAYS))
        return 0
    idle = sorted(g for g in gates if g not in hits)
    if idle:
        print('⚠️ 게이트 실효성 원장(WARN·비차단) — 관측 %d일간 **0회 발화** 게이트 %d개/%d:'
              % (days, len(idle), len(gates)))
        for g in idle:
            print('   ·', g)
        print('   → 각각 ⓐ 진짜 청정한 축인가 ⓑ 판정이 헐거워 아무것도 안 걸리는가 를 킬테스트로 재검증하라.')
        print('     ⓑ면 판정을 조이거나 접는다 = pre-commit 시간의 근거 있는 감량(부채 래칫 "줄이는 건 자유" 동축).')
        return 0
    print('✅ 게이트 실효성 원장 — 관측 %d일간 %d게이트 전부 최소 1회 발화(발화 %d건 · 죽은 게이트 0).'
          % (days, len(gates), fired))
    return 0

def check_brief_lib():
    """채널 요약 지식 라이브러리 층 생존(하드 · 운영자 260808 "매번 판단이 그때그때 참고 지식이 없어서 새로 시작하는 것 같다 ·
    채널 요약의 라이브러리가 있으면 좋을듯 · 쌓이면 경쟁력" — 정본 = `apps/insta/brief_lib.py`).

    ⚠️ 신설 사유 = **이 축은 두 가지 서로 다른 방식으로 조용히 죽는데 화면은 둘 다 멀쩡해 보인다**
      ⓐ 아카이브는 쌓이는데 아무도 안 읽음 — 260808 실측 이전 상태가 정확히 그랬다:
         `viewer/chan_brief_log.jsonl` 24회차·215KB가 git 추적으로 살아 있는데 소비처가 0이었고,
         프롬프트에 들어가는 건 직전 1회차 앞 **1500자**(전문 4,187자의 36%)뿐이라 [3개월]·[전체]·[총론]이 통째로 증발.
         브리프는 매일 정상 생성되니 **아무도 눈치 못 챈다** — 운영자가 "매번 새로 시작하는 것 같다"고 말할 때까지.
      ⓑ 호출은 사는데 프롬프트에 안 실림 — 셸이 `LIB_BLOCK`을 만들고도 `${LIB_BLOCK}`을 PROMPT에서 빼면
         라이브러리는 **매 회차 정상 실행되고 정상 폐기**된다(rc0 · 로그 정상 · 무증상).
      기존 게이트는 전부 다른 축이다 — `check_algo_ledger` = 회차 원장의 **수치** 불변식 ·
      `check_gate_docs`/`check_contract_anchors` = 게이트 자신의 등재·배선 → 「과거 회차의 *판단*이
      다음 판단에 실제로 실리는가」는 축 자체가 없었다(brk_misfire·thumb_votes가 막으려던 죽은 원장과 동축).

    4축 = ① 정본 모듈 실존 + 핵심 심볼 + 금지 심볼 부재(네트워크·LLM·외부 프로세스 0 = 브리프 잡 예산 보호 ·
    `check_algo_ledger` ① 관례 계승) ② 두 셸(IG·FB)이 **실행줄에서** 라이브러리를 호출 ③ 그 산출이
    **PROMPT 안에 실제로 실림**(ⓑ 봉합 = 이 게이트의 실효 조건) ④ 구판 절단 문법 부활 차단.
    ⚠️ IG·FB **양쪽 동시 강제** — 한쪽만 고치면 나머지가 조용히 구판으로 남는 게 이 레포의 가장 흔한 미러 드리프트다.
    정적 · 렌더·LLM·네트워크 0 · **면책표 없이 하드 0**(현행 위반 0 = 부채 원장 증가 0)."""
    fails = []

    def _read(rel):
        try:
            return open(os.path.join(ROOT, rel), encoding='utf-8').read()
        except Exception:
            return ''

    MOD = 'apps/insta/brief_lib.py'
    src = _read(MOD)
    if not src:
        fails.append('정본 모듈 부재: %s — 지식 라이브러리가 통째로 사라졌다(fail-closed)' % MOD)
    else:
        for sym in ('def build_block', 'def analyze', 'def axis_of', 'def identity', 'def arrows', 'LOGS',
                    'def load_posts', 'def outcomes', 'LEDGER_GLOB', 'RIPE_H', 'def stalled', 'def viewcard', 'def trendctx'):
            if sym not in src:
                fails.append('%s: 핵심 심볼 「%s」 소실 — 라이브러리 골격이 깨졌다' % (MOD, sym))
        # ⚠ 구문 검사 = 실효 조건 — 셸 배선이 `2>/dev/null || true` fail-soft라 **구문 오류가 그대로 빈 블록**이 된다
        #   (260808 실측 = ⑤ 층 작업 중 IndentationError가 났는데 셸 경로에선 rc0·무출력으로 조용히 통과했다).
        #   fail-soft는 「원장이 부족할 때」를 위한 것이지 「코드가 깨졌을 때」를 덮으라고 있는 게 아니다.
        try:
            compile(src, MOD, 'exec')
        except SyntaxError as e:
            fails.append('%s: 구문 오류 %s행 「%s」 — 셸 fail-soft가 이걸 조용한 빈 블록으로 삼킨다' % (MOD, e.lineno, e.msg))
        for ban in ('import urllib', 'import requests', 'import socket', 'import subprocess',
                    'http.client', 'os.system(', 'import anthropic', 'from anthropic'):
            if _has_exec_line(src, ban):
                fails.append('%s: 금지 심볼 「%s」 — 이 모듈은 네트워크·LLM·외부 프로세스 0 계약이다'
                             '(브리프 잡 벽시계 예산 안에서 도는 전제)' % (MOD, ban))
        # 로그 경로 정합 — 라이브러리가 읽는 파일과 셸이 쓰는 파일이 갈리면 영원히 빈 블록(무증상)
        for log in ('viewer/chan_brief_log.jsonl', 'viewer/chan_brief_fb_log.jsonl'):
            if log not in src:
                fails.append('%s: 아카이브 경로 「%s」 미참조 — 원료를 못 읽는다' % (MOD, log))
    for sh, scope, log in (('.github/scripts/chan_brief.sh', 'ig', 'viewer/chan_brief_log.jsonl'),
                           ('.github/scripts/fb_brief.sh', 'fb', 'viewer/chan_brief_fb_log.jsonl')):
        s = _read(sh)
        if not s:
            fails.append('%s: 파일 부재' % sh)
            continue
        if not _has_exec_line(s, 'brief_lib.py'):
            fails.append('%s: 라이브러리 호출 소실 — 아카이브가 다시 「쌓이는데 아무도 안 읽는 원장」이 된다' % sh)
        if ('--scope %s' % scope) not in s:
            fails.append('%s: 스코프 인자(--scope %s) 불일치 — 남의 채널 원장을 읽는다' % (sh, scope))
        # ③ 실효 조건 — 호출만 살고 프롬프트에서 빠지면 매 회차 정상 실행되고 정상 폐기된다(무증상)
        head, _, tail = s.partition('PROMPT="')
        if not tail:
            fails.append('%s: PROMPT 앵커 소실 — 주입 지점을 판정할 수 없다(fail-closed)' % sh)
        elif '${LIB_BLOCK}' not in tail:
            fails.append('%s: PROMPT에 ${LIB_BLOCK} 미주입 — 라이브러리를 만들어놓고 안 쓴다'
                         '(호출은 살아 있어 rc0·로그 정상 = 가장 조용한 죽음)' % sh)
        # ⑥ 정체 축 계약(운영자 260808 3차) — 라이브러리가 「반복했는데 안 옮겨진 축」을 짚어줘도
        #   프롬프트가 그걸 오늘의 행동으로 바꾸라고 요구하지 않으면 모델은 같은 방침을 또 적는다
        #   (260808 실측 = 07-30~31 제안 4건 전건 실행 ▼ · ②에 「릴스 올리자 ×4회」가 그렇게 쌓였다).
        #   블록만 있고 계약이 없으면 = 정보를 보여주고 아무것도 안 시키는 것 = 반복 고리가 그대로 돈다.
        # ⑦ 총론 디테일 계약(운영자 260808 5차) — 구판 「수치 나열 금지」가 게시물 실명·근거를 통째로 빼게 만들어
        #   총론이 정체성 선언문만 남았다(운영자 실측 "남의 인스타 뒤지는 느낌"). 계약이 빠지면 그 얇음이 그대로 재발한다.
        elif '임팩트 문단(필수)' not in tail:
            fails.append('%s: PROMPT에 총론 임팩트 문단 계약 소실 — 총론이 다시 게시물 실명·근거 없는 선언문으로 얇아진다' % sh)
        elif '오늘의 행동 한 개' not in tail:
            fails.append('%s: PROMPT에 ⑥ 정체 축 → 오늘의 행동 계약 소실 — 반복만 하고 안 옮겨지던 고리가 되살아난다' % sh)
        if log not in s:
            fails.append('%s: 아카이브 적재 경로 「%s」 소실 — 다음 회차 원료가 안 쌓인다' % (sh, log))
        # ⑦ 화면 배송 축 = **폐지**(운영자 260809 "판단 이력 같은 경우는 내가 볼 필요는 없음 · AI 요약을 진행하는 프로그램이 체킹하면 됨").
        #   260808 4차의 doc['lib']·뷰어 libCard 하드 3종을 걷었다 — 라이브러리의 값은 **프롬프트에 실리는 것**이지 화면에 뜨는 게 아니다.
        #   ⚠ 그 축이 사라져도 LIB_BLOCK 주입(위 ③)이 하드로 남아 있어 「쌓이는데 아무도 안 읽는」 원래의 죽음은 그대로 막힌다.
        # ④ 구판 = 직전 1회차 text 앞 1500자(전문의 36% · [3개월]·[전체]·[총론] 증발) 부활 차단
        if _has_exec_line(s, '[:1500]'):
            fails.append('%s: 구판 절단 문법 「[:1500]」 부활 — 총론·전체가 다시 증발한다' % sh)
        if _has_exec_line(s, 'PREV_BLOCK'):
            fails.append('%s: 구판 PREV_BLOCK 부활 — 라이브러리로 대체된 축이다' % sh)
    # ⑧ 저장 블록 정의-사용 대조(260809 실사고 봉합 — **이 게이트를 만든 그 커밋이 낸 사고**).
    # 사고 = 판단 이력 배송을 걷으면서 `_libcard = None` ~ `if _libcard: doc['lib']` 사이에 끼어 있던
    #   **`doc = {...}` 정의를 같이 지웠다** → 두 브리프 다 `NameError: name 'doc' is not defined`로 저장 직전에 죽었다.
    # ⚠ 왜 아무도 안 울렸나 = 세 겹이 전부 이 자리를 못 본다:
    #   ⓐ `bash -n` = 셸 문법만 본다(heredoc 안 파이썬은 그냥 문자열) ⓑ 정적 문자열 게이트 = 심볼 **존재**만 본다
    #   ⓒ 셸 마지막 줄이 `echo "chan-brief: 갱신 완료($SHA)"` = **파이썬이 죽어도 찍히는 거짓 성공 로그**
    #      (실측 = 런 31308318206 로그에 「갱신 완료」가 정상 출력됐는데 chan_brief.json은 안 바뀌었다).
    #   → 워크플로는 success로 끝나고 화면은 직전 브리프가 남아 멀쩡해 보인다 = 이 레포가 반복해 겪은 무증상 죽음.
    # 술어 = 「`json.dump(X, open(...))`로 저장하는 이름 X가 **같은 heredoc 안에서 할당**되는가」.
    # compile()로는 못 잡는다(구문은 완전히 유효한 런타임 NameError) — 정의-사용 대조가 이 사고 클래스의 정확한 축이다.
    for sh in ('.github/scripts/chan_brief.sh', '.github/scripts/fb_brief.sh'):
        s = _read(sh)
        if not s:
            continue
        for blk in re.findall(r"<<'PY'\n(.*?)\nPY\n", s, re.S):
            for nm in set(re.findall(r'json\.dump\(\s*([A-Za-z_]\w*)\s*,', blk)):
                if not re.search(r'^\s*%s\s*=' % re.escape(nm), blk, re.M):
                    fails.append('%s: 저장 블록이 미정의 이름 「%s」를 json.dump 한다 — 런타임 NameError로 '
                                 '브리프가 저장 직전에 죽는데 셸 echo는 「갱신 완료」를 찍는다(무증상)' % (sh, nm))

    # [3일] 실황 계약(운영자 260809 "수박 겉핥기 · 게시물 하나하나의 디테일 · 너무 돌려 말하니 유의미한 인사이트가 안 나온다").
    # ⚠ 진범은 두 겹이었고 둘 다 이 게이트가 안 보던 자리다 — ⓐ 데이터: 일별 조회(views)가 최근 30일 전건 결측 + follows 말미 0-fill이라
    #   짧은 창을 말할 근거가 0칸이었다(모델이 스냅샷 하나로 사흘을 논하다 "아직 하루가 안 찼으니" 류로 뭉갤 수밖에 없었다)
    #   ⓑ 계약: [3일]이 「3~4줄」로 묶여 있어 두껍게 쓰는 게 규칙 위반이었다(총론이 얇았던 260808 5차와 **같은 병** = 계약 자신이 시켰다).
    # → 살아있는 축(도달·팔로워 순증감)과 게시 리듬 대비를 다이제스트에 싣고, 계약을 실황 중계로 바꾼다. 셋 다 빠지면 그 얇음이 그대로 재발한다.
    for sh in ('.github/scripts/chan_brief.sh',):   # IG 전용 = 이 축의 원료(daily_series·post_refs)가 IG 수집에만 있다(FB는 조인 원료 없음 = ⑤ 성패 대조와 같은 경계)
        s = _read(sh)
        if not s:
            continue
        if '게시 리듬 ↔ 반응 실측' not in s:
            fails.append('%s: [게시 리듬 ↔ 반응 실측] 소실 — 「올리던 리듬이 끊겨서 멈춰 있다」를 말할 근거가 사라진다' % sh)
        if 'follower_net' not in s:
            fails.append('%s: 팔로워 순증감(follower_net) 미탑재 — 계정 축이 꺼져도 팔로워는 유지된다는 걸 말할 데이터가 없다' % sh)
        _p = s[s.find('PROMPT="'):] if 'PROMPT="' in s else ''
        if '실황 중계' not in _p:
            fails.append('%s: PROMPT에 [3일] 실황 중계 계약 소실 — 짧은 창이 다시 3~4줄 겉핥기로 돌아간다' % sh)
        if '완곡어법 금지' not in _p:
            fails.append('%s: PROMPT에 완곡어법 금지 계약 소실 — 원인을 알면서 돌려 말하던 문체가 되살아난다' % sh)
        # 260809 2차(운영자 "배선 ㄱㄱ") — [3일]에서 실증된 문법을 [7일]·[28일]로 확장한 축.
        # ⚠ [28일]은 근거 블록이 실효 조건이다: 없으면 모델이 30일 줄을 **손으로 세서** 주 단위를 만든다
        #   (260809 첫 산출이 실제로 그랬다 — 「서른 날 중 열엿새」가 실측 16일과 맞긴 했지만 그건 운이지 계약이 아니다).
        if '주 단위 리듬' not in s:
            fails.append('%s: [주 단위 리듬(최근 4주)] 블록 소실 — [28일]이 다시 30일 줄을 손으로 세게 된다(오산·누락 무검출)' % sh)
        if '한 장씩' not in _p:
            fails.append('%s: PROMPT에 [7일] 게시물 개별 판정 계약 소실 — 그 창이 다시 4~6줄 겉핥기로 돌아간다' % sh)
        if '주 대 주로 읽어라' not in _p:
            fails.append('%s: PROMPT에 [28일] 주 대 주 대조 계약 소실 — 주 단위 블록을 실어놓고 안 쓰게 된다' % sh)
        # 260809 3차(운영자 "게시물 얘기할 땐 이탤릭체 골드 링크 참조 · 포인트는 볼드 · 정말 중요한 건 강조색").
        # ⚠ 링크는 **데이터 + 계약 + 뷰어 부착** 세 층이 다 살아야 화면에 뜬다 — 한 층만 빠져도 그냥 평범한 텍스트가 되고(무증상) 운영자 눈이 유일한 검출기가 된다.
        if '· 링크 {x.get(' not in s:
            fails.append('%s: 게시물 줄 permalink 미탑재 — 모델이 걸 링크 자체가 데이터에 없다' % sh)
        if '링크로 건다' not in _p:
            fails.append('%s: PROMPT에 게시물 링크 참조 계약 소실 — 게시물이 다시 맨 텍스트로만 언급된다' % sh)
        if '2층(볼드)은' not in _p:
            fails.append('%s: PROMPT에 강조 밀도 계약 소실 — 볼드 1~2개짜리 밋밋한 판으로 되돌아간다' % sh)
        if '기 대 기로' not in _p:
            fails.append('%s: PROMPT에 [3개월] 기 대 기 리듬 계약 소실 — 사다리가 그 창에서 끊긴다' % sh)
        if "링크 {x.get('permalink')" not in s.split('post_refs')[0][-400:] and 'post_refs' in s and '} 링크 {' not in s:
            fails.append('%s: 일별 「올린 것」 칸 permalink 미탑재 — [28일]이 전환점 게시물을 링크로 못 건다' % sh)
    v = _read('viewer/index.html')
    if v:
        # 인앱 팝업(운영자 260809 "링크가 창 위에 팝업 · 다른 앱이나 웹 창으로 전환 안 되게") — 3층 중 하나만 빠져도
        # 링크는 여전히 눌리지만 **앱 밖으로 튀어나간다**(에러 0·화면 정상 = 무증상 회귀 · 운영자 눈이 유일한 검출기).
        for sym, why in (("openIgPost", '게시물 팝업 진입점'),
                         ("a.tbrief-ref, a.ch-th", '브리프 참조·타일 12칸 클릭 위임'),
                         ("instagram.com/p/' + m[1] + '/embed/", 'trEmbed 피드 게시물 임베드')):
            if sym not in v:
                fails.append('viewer/index.html: 인앱 팝업 심볼 「%s」(%s) 소실 — 링크가 다시 앱 밖 새 탭으로 나간다' % (sym, why))
    if fails:
        print('❌ 채널 요약 지식 라이브러리 결손 %d건 — 과거 회차의 판단이 다음 판단에 안 실린다:' % len(fails))
        for f in fails:
            print('   ·', f)
        print('   → 정본 = apps/insta/brief_lib.py · 배선 = chan_brief.sh/fb_brief.sh의 LIB_BLOCK → PROMPT.')
        return 1
    print('✅ 채널 요약 지식 라이브러리 — 정본 1 + 2셸(IG·FB) 호출·주입·적재 전 층 생존.')
    return 0

def check_cover_title_chain():
    """게시물 이름 = 표지에 박힌 제목(하드 · 운영자 260812 "기사 인트로 첫줄보다, 오버레이가 가장 정확한 내용이거든").

    [무엇을 고친 축인가]
      채널 요약이 «…» 로 게시물을 지목할 때 쓰던 이름 = `first_line(caption)` = **인스타 글의 첫 줄**인데,
      노뮤트는 카드에 박는 제목과 글 첫 줄을 **각각 따로 쓴다**. 소유 커버 실판독 2건(260812):
        글 첫줄 「🚨 엿새 만에 다시 쐈다, 이번에도 북은 말이 없다」 ↔ 카드 「북한, 엿새 만에 '또 쐈다' || 동쪽 방향 미상 발사체 발사」
        글 첫줄 「🚇 열차는 서지 않았다…전장연 71차 출근길 시위」 ↔ 카드 「"우리를 가두지 마십시오" || 전장연, 매주 출근길 시위 진행」
      → 요약이 **화면에 뜬 적 없는 문장**을 게시물 이름이라고 불렀고, 운영자는 그 이름으로 어느 카드가
        터졌는지 판단한다 = 판단의 입력 자체가 어긋나 있었다.

    ⚠ 신설 사유 = **이 체인은 조용히 죽는데 화면 증상이 0이다.** 판독 스텝이 빠지거나 소비처가 한 곳만
      구판으로 돌아가도 요약은 정상 생성되고 게시물 이름도 정상으로 보인다(글 첫 줄이니까) — 그냥 **덜
      정확한 이름**으로 되돌아갈 뿐이라 로그·에러 어디에도 안 남고 운영자 눈이 유일한 검출기가 된다
      (insta-thumb-miss·brk_misfire 동축). 기존 게이트는 전부 다른 축이다 — `check_brief_lib` = 과거 회차가
      프롬프트에 실리는가 · `check_algo_ledger` = 원장 불변식 · `check_thumb_chain` = 커버 **이미지**가
      화면에 뜨는가 → 「그 커버에 **적힌 글자**가 이름이 되는가」는 축 자체가 없었다.

    판정 4축(정적 · 렌더·LLM·네트워크 0 · 면책표 없이 하드 0):
      ① 판독기 골격 — 소유 커버 경로·원장 경로·폴오버 SSOT 경유·재판독 차단(원장 적중 스킵)
      ② 소비 3표면 — 신호계산(부착) · 채널 브리프(지목 줄) · 지식 라이브러리(터진 게시물)
      ③ 워크플로 — 판독 스텝 + **브리프보다 앞** 순서(뒤면 그 회차 요약엔 안 실린다 = 무증상 1회차 지연)
      ④ 원장 착지 — `apps/insta/data` 커밋 인자(빠지면 매 회차 전량 재판독 = 비용이 조용히 는다)
    """
    def _read(rel):
        try:
            return open(os.path.join(ROOT, rel), encoding='utf-8').read()
        except Exception:
            return ''

    fails = []
    OCR = '.github/scripts/insta_cover_ocr.py'
    s = _read(OCR)
    if not s:
        fails.append('%s 부재 — 표지 제목 판독기가 통째로 없다(요약 이름이 글 첫 줄로 영구 회귀)' % OCR)
    else:
        for sym, why in (('viewer', '소유 커버 폴더 경유 = 다운로드·네트워크 0'),
                         ('insta_covers', '소유 커버 폴더 경유 = 다운로드·네트워크 0'),
                         ('cover_titles.json', '원장 = 영속층(커버 파일은 12칸 롤링으로 삭제된다)'),
                         ('run_claude', '폴오버·계측 SSOT 경유(자체 쿼터처리 금지 계약)')):
            if sym not in s:
                fails.append('%s: 심볼 「%s」 소실 — %s' % (OCR, sym, why))
        if 'mid not in led' not in s:
            fails.append('%s: 원장 적중 스킵 술어 소실 — 매 회차 전량 재판독으로 비용이 조용히 는다' % OCR)
        if not re.search(r'^\s*#', s, re.M) or 'fail-soft' not in s:
            fails.append('%s: fail-soft 계약 표기 소실 — 판독 실패가 수집·요약 파이프를 죽일 수 있다' % OCR)

    sig = _read('apps/insta/insta_signals.py')
    if sig:
        if 'def cover_title(' not in sig:
            fails.append('apps/insta/insta_signals.py: cover_title() 소실 — 원장을 읽는 곳이 없어 이름이 안 바뀐다')
        # 부착 3자리(enrich=posts 축 · post_refs 수집 · post_refs 배송) — 하나만 빠져도 그 칸만 조용히 구판으로 남는다.
        if sig.count("cover_title(") < 3:
            fails.append('apps/insta/insta_signals.py: ovt 부착 자리 부족(%d/3 — enrich·post_refs 수집·배송) '
                         '— 빠진 칸만 글 첫 줄로 남아 요약이 표면마다 다른 이름을 쓴다' % sig.count("cover_title("))
        if "'ovt'" not in sig:
            fails.append('apps/insta/insta_signals.py: ovt 키 소실 — 소비처가 읽을 필드가 없다')
        # 분류 축 무접촉 = 과거 게시물 전건 재라벨 방지(성장 3기·주제 비중 시계열 보호).
        for bad in ('naming_style(cover_title', 'category(cover_title', 'naming_features(cover_title'):
            if bad in sig:
                fails.append('apps/insta/insta_signals.py: 분류 입력을 표지 제목으로 갈아끼웠다(%s) — 과거 게시물 '
                             '전건이 다른 라벨로 재계산돼 요약이 읽는 시계열이 통째로 갈린다(표시 축 전용 계약 위반)' % bad)

    cb = _read('.github/scripts/chan_brief.sh')
    if cb and "x.get('ovt')" not in cb:
        fails.append(".github/scripts/chan_brief.sh: 일별 「올린 것」 칸이 ovt 를 안 쓴다 — 요약이 다시 글 첫 줄로 게시물을 지목한다")
    bl = _read('apps/insta/brief_lib.py')
    if bl and "p.get('ovt')" not in bl:
        fails.append("apps/insta/brief_lib.py: 터진 게시물 이름이 ovt 를 안 쓴다 — 총론 임팩트 문단이 화면에 없는 제목을 부른다")
    al = _read('.github/scripts/algo_ledger.py')
    if al and "'ovt'" not in al:
        fails.append(".github/scripts/algo_ledger.py: 원장에 ovt 미탑재 — 회차가 지나면 그 시점 표지 제목을 영영 복원 못 한다")

    yml = _read('.github/workflows/insta-fetch.yml')
    if yml:
        if 'insta_cover_ocr.py' not in yml:
            fails.append('.github/workflows/insta-fetch.yml: 판독 스텝 미배선 — 원장이 영영 안 자란다(새 게시물 전건 구판 이름)')
        else:
            # ⚠ 순서는 **실행줄**로 잰다 — 이 워크플로는 머리 주석·입력 설명에 chan_brief.sh 를 여러 번 언급해서
            #   단순 첫 매치로 재면 배선이 정상인데도 「브리프 뒤」로 오판한다(첫 실행 실측 봉합).
            _m_ocr = re.search(r'^\s*(?:run:|-)?[^\n]*python3\s+\.github/scripts/insta_cover_ocr\.py', yml, re.M)
            _m_br = re.search(r'^\s*(?:run:)?\s*bash\s+\.github/scripts/chan_brief\.sh', yml, re.M)
            i_ocr = _m_ocr.start() if _m_ocr else yml.find('insta_cover_ocr.py')
            i_brief = _m_br.start() if _m_br else -1
            if i_brief >= 0 and i_ocr > i_brief:
                fails.append('.github/workflows/insta-fetch.yml: 판독 스텝이 채널 브리프 **뒤** — 그 회차 요약엔 새 제목이 '
                             '안 실린다(항상 한 회차 늦게 반영 = 무증상 지연)')
            # 판독 뒤 신호 재계산이 없으면 원장은 자라는데 insta_data.json 엔 안 실린다(가장 조용한 죽음).
            tail = yml[i_ocr:i_ocr + 400]
            if 'insta_signals.py' not in tail:
                fails.append('.github/workflows/insta-fetch.yml: 판독 직후 신호 재계산 누락 — 원장은 자라는데 브리프가 '
                             '읽는 파일엔 새 이름이 안 실린다(에러 0·요약 정상 = 무증상)')
        if not re.search(r'git_land\.sh[^\n]*apps/insta/data', yml):
            fails.append('.github/workflows/insta-fetch.yml: git_land 인자에 apps/insta/data 누락 — 원장이 커밋 안 돼 '
                         '매 회차 전량 재판독(비용이 조용히 는다)')
    if fails:
        print('❌ 표지 제목 체인 결손 %d건 — 요약이 화면에 뜬 적 없는 문장으로 게시물을 지목한다:' % len(fails))
        for f in fails:
            print('   ·', f)
        print('   → 정본 = .github/scripts/insta_cover_ocr.py · 원장 = apps/insta/data/cover_titles.json '
              '· 소비 = insta_signals(ovt) → chan_brief/brief_lib.')
        return 1
    print('✅ 표지 제목 체인 — 판독기·원장·부착 3자리·소비 3표면·워크플로 순서 전 층 생존.')
    return 0


def check_algo_ledger():
    """알고리즘 인사이트 회차 원장 불변식(하드 · 운영자 260802 · 평의회 합의 — 정본 = `.github/scripts/algo_ledger.py` ·
    집계 = `apps/insta/algo_insight.py` · 원장 = apps/insta/data/algo_runs/**).
    ① 작성기·집계기 금지 심볼 부재(urllib/requests/http.client/socket/subprocess/os.system/anthropic SDK)
       = 「네트워크 0 · LLM 0콜 · 외부 프로세스 0 · 초 단위」의 기계 보증(브리프 잡 50분 예산 보호).
    ② insta-fetch.yml 원장 스텝에 timeout-minutes · continue-on-error · `|| true` 3중 fail-soft 존재
       = 원장이 어떤 죽음으로도 수집·브리프 커밋을 못 막는다.
    ③ 원장 기록자 유일성 — `apps/insta/data`를 만지는 워크플로 = insta-fetch.yml 단독. 다중 기록자 =
       git_land reset 재적층이 남의 append-only 줄을 무음 소실(git_land.sh §전제 · 260802 실측 재현)."""
    fails = []
    _BAN = ('import urllib', 'import requests', 'import socket', 'import subprocess',
            'http.client', 'os.system(', 'import anthropic', 'from anthropic')
    for rel in ('.github/scripts/algo_ledger.py', 'apps/insta/algo_insight.py'):
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            continue   # 스캐폴드 이전 = 무대상(게이트가 도입을 강제하진 않음)
        src = open(p, encoding='utf-8').read()
        for b in _BAN:
            if b in src:
                fails.append('원장 금지 심볼: %s 에 `%s` — 네트워크·LLM·외부 프로세스 0 계약 위반' % (rel, b))
    wf = os.path.join(ROOT, '.github/workflows/insta-fetch.yml')
    if os.path.exists(os.path.join(ROOT, '.github/scripts/algo_ledger.py')) and os.path.exists(wf):
        lines = open(wf, encoding='utf-8').read().splitlines()
        idx = [i for i, ln in enumerate(lines) if 'algo_ledger.py' in ln]
        if not idx:
            fails.append('원장 스텝 부재: insta-fetch.yml 에 algo_ledger.py 호출이 없다(작성기만 있고 배선 0)')
        else:
            blk = '\n'.join(lines[max(0, idx[0] - 20):idx[0] + 2])
            for need in ('timeout-minutes', 'continue-on-error: true', '|| true'):
                if need not in blk:
                    fails.append('원장 스텝 fail-soft 결손: insta-fetch.yml algo_ledger 스텝에 `%s` 없음(3중 가드 필수)' % need)
        owners = []
        for f in os.listdir(os.path.join(ROOT, '.github/workflows')):
            if not f.endswith('.yml'):
                continue
            if 'apps/insta/data' in open(os.path.join(ROOT, '.github/workflows', f), encoding='utf-8').read():
                owners.append(f)
        if sorted(owners) != ['insta-fetch.yml']:
            fails.append('원장 기록자 유일성 위반: apps/insta/data 를 만지는 워크플로 = %s (insta-fetch.yml 단독이어야 함)' % owners)
    if fails:
        print('❌ 회차 원장 게이트 %d건:' % len(fails))
        for f in fails:
            print('  -', f)
        return 1
    print('✅ 회차 원장 게이트 — 금지 심볼 0 · 스텝 3중 fail-soft · 기록자 단독.')
    return 0


def main():
    _gate_hits_install()   # 전 check_* 자동 계측(호출부 0줄 수정 · 새 게이트도 자동 편입 — check_gate_hits 참조)
    fails = check_paths() + check_versions() + check_inject_dividers() + check_inject_markers() + check_conflict_markers() + check_workflow_yaml() + check_git_idiom()
    rc = 0
    if fails:
        print('❌ check_refs 실패 %d건:' % len(fails))
        for f in fails:
            print('  -', f)
        rc = 1
    else:
        print('✅ check_refs 통과 — 경로 참조 실존·파일명↔내부 버전 일치.')
    # /k 라이브러리 SSOT↔유닛 정합(통합본에서 유닛 재생성 = 현재 유닛 동일?) — 드리프트 게이트
    try:
        import build_library
        if build_library.check() != 0:
            rc = 1
    except Exception as e:
        print('⚠️ build_library check 스킵:', e)
    try:
        if check_viewer_js() != 0:   # viewer 인라인 JS 구문(하드 게이트 — SyntaxError=뷰어 전면 사망)
            rc = 1
    except Exception as e:
        print('⚠️ check_viewer_js 스킵:', e)
    try:
        if check_functions_js() != 0:   # Pages Functions 구문(하드 게이트 — 한 파일 SyntaxError=배포 전체 전멸·260706 ly.js 사고)
            rc = 1
    except Exception as e:
        print('⚠️ check_functions_js 스킵:', e)
    try:
        if check_icon_ssot() != 0:   # 공유 아이콘 SSOT(하드 게이트 — 인라인 재선언·미로드=드리프트 부활 차단·260628)
            rc = 1
    except Exception as e:
        print('⚠️ check_icon_ssot 스킵:', e)
    try:
        if check_model_names() != 0:   # 모델 표시명 SSOT(하드 — 음차·변형 래칫 + 사전↔리터럴 표면 동기 · 운영자 260803 5차)
            rc = 1
    except Exception as e:
        print('⚠️ check_model_names 스킵:', e)
    try:
        import build_design_mirror   # 디자인 거울 정합: 디자인기틀/구성도/base.css = viewer :root (하드 게이트·§🎨 ⓐ)
        if build_design_mirror.check() != 0:
            rc = 1
    except Exception as e:
        print('⚠️ 디자인 거울 check 스킵:', e)
    try:
        if check_design() != 0:   # accent_raw 차단(rc=1·운영자 ③b STAGE1) · hex/blur/죽은토큰은 내부 WARN
            rc = 1
    except Exception as e:
        print('⚠️ check_design 스킵:', e)
    try:
        if check_launch_spec() != 0:   # 발사(생성) 버튼 규격 통일 하드게이트(운영자 260720 "생성 버튼 통일·모조품 차단" 한 수 — 신규 발사 버튼 규격 이탈 차단)
            rc = 1
    except Exception as e:
        print('⚠️ check_launch_spec 스킵:', e)
    try:
        if check_imgstudio_dock_spec() != 0:   # 이미지 스튜디오 도크 규격 동결(운영자 260723 "AFTER로 일괄 통일·저 규격 벗어나면 안됨" — 리드백 스트립 기본 mut·생성 버튼 상시 활성)
            rc = 1
    except Exception as e:
        print('⚠️ 이미지 스튜디오 도크 규격 게이트 스킵:', e)
    try:
        if check_track_parity() != 0:   # 자간 판정 기준 단일화(운영자 260802 3차 — 뷰어 advance = 서버 draw_t 자 · 한도 3면 동일)
            rc = 1
    except Exception as e:
        print('⚠️ 자간 기준 게이트 스킵:', e)
    try:
        if check_result_rail_parity() != 0:   # 결과 레일 = 5탭 한 세트(운영자 260806 — 요약 줄+썸네일 부품 세트가 표면마다 갈라지던 축)
            rc = 1
        if check_cap_rail_land() != 0:   # 영상 완료 적재 = 화면 주인·강등 양쪽(운영자 260810 — 끝난 작업이 결과 레일에 안 얹혀 「방금거가 유실」되던 축)
            rc = 1
        if check_trail_spec() != 0:   # 미리보기 코너 옵션 레일 사본 동일성(운영자 260802 — thumb·tr·index 3표면 값 사본이 갈라지는 조용한 드리프트 차단)
            rc = 1
    except Exception as e:
        print('⚠️ 코너 레일 게이트 스킵:', e)
    try:
        check_component_lock()   # 병렬 세션 컴포넌트 락 겹침 알림(운영자 260802 · WARN·비차단 = rc 미반영)
    except Exception as e:
        print('⚠️ 컴포넌트 락 게이트 스킵:', e)
    try:
        if check_algo_ledger() != 0:   # 회차 원장 불변식(운영자 260802 — 네트워크·LLM 0 · 3중 fail-soft · 기록자 단독)
            rc = 1
    except Exception as e:
        print('⚠️ 회차 원장 게이트 스킵:', e)
    try:
        if check_cover_title_chain() != 0:   # 게시물 이름 = 표지에 박힌 제목(운영자 260812 — 요약이 「글 첫 줄」로 게시물을 지목해 화면에 뜬 적 없는 문장을 이름이라 부르던 축 · 한 층만 빠져도 조용히 구판 이름으로 회귀)
            rc = 1
    except Exception as e:
        print('⚠️ 표지 제목 체인 게이트 스킵:', e)
    try:
        if check_brief_lib() != 0:   # 채널 요약 지식 라이브러리(운영자 260808 — 아카이브 24회차가 쌓이는데 프롬프트엔 직전 1회차 1500자[전문의 36%]만 실려 [3개월]·[전체]·[총론]이 매 회차 증발하던 축 · 「호출은 사는데 프롬프트에서 빠지는」 무증상 죽음까지 봉합)
            rc = 1
    except Exception as e:
        print('⚠️ 지식 라이브러리 게이트 스킵:', e)
    try:
        if check_thumb_prompt_sanity() != 0:   # 뉴스 픽 AI 썸네일 = 발사 프롬프트 자기모순 0(운영자 260805 — 「지시 vs 금지」가 한 줄에 공존해 그림이 평균으로 도망가던 축 · 정본 함수 재판정)
            rc = 1
        check_gate_hits()   # 게이트 실효성 원장(WARN·비차단 · rc 미반영 = component_lock 관례) — 「어느 게이트가 실제로 일을 하나」 축(운영자 260805 "돌리고 머지 ㄱㄱ" · 짝 check_gate_docs=문서 등재 · check_contract_anchors=배선 · 이건 발화)
        if check_contract_anchors() != 0:   # 계약 앵커 = 「강제 없는 선언」 차단(운영자 260805 — gen_image가 260710에 "전 JPEG 저장 경로 통일"을 주석으로 선언해 놓고 5파일이 6주간 안 따라온 실사고의 구조적 봉합 · 짝 check_gate_docs는 문서 등재만 보고 「실제로 도는가」는 축 자체가 없었다)
            rc = 1
        if check_image_format() != 0:   # 이미지 산출 포맷 = 투명(PNG)/그 외(JPG q90) 2갈래(운영자 260805 "아이디어 ㄱ" — thumb_gen이 키를 .png로 굽는데 실물은 JPEG였던 거짓 확장자 6주 무증상 + 품질 4갈래 드리프트를 사람 눈이 유일한 검출기로 두던 축의 기계화 · 첫 실행이 track_analyze q82 2건을 즉시 검출)
            rc = 1
        if check_ytdlp_aac() != 0:   # 다운로드 오디오 코덱 = AAC 강제(운영자 260805 — 알몸 ba = Opus가 mp4에 들어가 프리미어가 오디오 트랙을 조용히 무시하던 축 봉합)
            rc = 1
    except Exception as e:
        print('⚠️ yt-dlp AAC 게이트 스킵:', e)
    try:
        if check_rubric_regress() != 0:   # 루브릭 회귀 도장(운영자 260803 — breaking RUBRIC 개정 = 과거 실측 판정 드라이런 통과 도장 필수 · 게이트 자체는 정적 해시 대조 = LLM 0)
            rc = 1
    except Exception as e:
        print('⚠️ 루브릭 회귀 게이트 스킵:', e)
    try:
        if check_grade_regress() != 0:   # grade 회귀 도장(운영자 260807 — gate_judge RUBRIC 개정 = 운영자 재채점 정답지 드라이런 통과 도장 필수 · 게이트 자체는 정적 해시 대조 = LLM 0)
            rc = 1
    except Exception as e:
        print('⚠️ grade 회귀 게이트 스킵:', e)
    try:
        check_style_ratchet()   # 요약 문체 회귀 래칫(운영자 260810 · 평의회 6 — 게이트 105개 중 요약 문체 축이 0개였다 · WARN 비차단 = rc 무영향)
    except Exception as e:
        print('⚠️ 문체 래칫 스킵:', e)
    try:
        if check_brk_misfire_chain() != 0:   # 긴급 오발 신고 폐루프(운영자 260803 4차 — 신고가 쌓이기만 하고 안 읽히는 죽은 원장 차단)
            rc = 1
    except Exception as e:
        print('⚠️ 긴급 오발 신고 체인 게이트 스킵:', e)
    try:
        if check_vote_btn_canon() != 0:   # 👍/👎 투표 부품 = 한 벌 계승(운영자 260805 "고정으로 박아줘 다른데서 만들면 참조하도록" · 계약 전문 = CII 「👍/👎 선호 투표」 행)
            rc = 1
        if check_thumb_redo_append() != 0:   # 썸네일 '수정 = +1 슬롯'(운영자 260807 "1/2 2/2 면 1/3 2/3 3/3" — 구판은 원본을 지우고 같은 R2 키에 덮어써 되돌릴 방법이 0이었다 · 파생 보존이 빠지면 수정본이 며칠 뒤 혼자 사라진다)
            rc = 1
        if check_grade_fix_chain() != 0:   # grade 수기 교정 폐루프(운영자 260807 — 12h 스윕 기록 체인 5층 생존 강제)
            rc = 1
        if check_img_upsize() != 0:   # 검색 이미지 화질 승격(운영자 260810 "최소 세로 720p 이상" — 매체 og:image 는 축소판인 경우가 많고 같은 CDN 에 원본이 그대로 있다 · 호출 한 줄만 빠져도 화면 증상 0으로 화질만 종전 복귀)
            rc = 1
        if check_yt_cookie_slot_name() != 0:   # 유튜브 쿠키 알림이 「갈아야 할 칸」을 맞게 말하는가(260812 실사고 — 알림과 받기 진단이 같은 상태를 정반대로 말해 운영자가 살아있는 칸을 갈았다)
            rc = 1
        if check_thumb_merge_canvas() != 0:   # 저작권·안내문이 사진에 실제로 얹히는가(260812 실사고 — 레이어를 params.fmt로 만들어 크기가 어긋나면 러너가 조용히 건너뛴다 · 화면 증상 = 그냥 안 보임)
            rc = 1
        if check_orig_title_restore() != 0:   # 요약 제목 = 기자가 뽑은 원문이 화면까지 오는가(260813 실사고 — title이 후킹 헤드로 덮이면 뷰어 원문 제목 줄이 통째로 사라진다 · 화면 증상 = 추상 헤드 하나만 남음)
            rc = 1
    except Exception as e:
        print('⚠️ grade 교정 체인 게이트 스킵:', e)
    try:
        if check_smoke_obs_chain() != 0:   # UI 스모크 경보가 사유를 갖고 나가는가(운영자 260807 — 사유 0자 경보가 8일 연속 무증상으로 살아 운영자가 조치할 수 없던 실사고 봉합 · 웹푸시 면제·메시지함 진단서 점등 동반 강제)
            rc = 1
        if check_smoke_chromium_path() != 0:   # 그 스모크가 러너에서 뜨기는 하는가(260808 — 260807 봉합이 같은 병 2종 중 1종만 고쳐 다음 나이틀리도 그대로 붉었는데 아무 게이트도 안 울린 축)
            rc = 1
        if check_seal_completeness() != 0:   # 봉합 완결성(하드 · 260816 승격 — 구판 WARN 은 260816 이관 반쪽 봉합 5곳을 경고만 하고 통과시켰다 · 문턱 0.90/2 실측 위양성 0 · 탈출구 = `seal-ok: 사유`)
            rc = 1
        if check_stt_engine_chain() != 0:   # STT 엔진 교체 계약(260808 · 평의회 8인 후속) — 층 하나가 빠져도 화면은 멀쩡한 채 조용히 죽는 축
            rc = 1
        if check_grok_sb_chain() != 0:   # 콘티 그록 레인(운영자 260811) — 한 층만 빠져도 칩은 눌리고 콘티도 나오는데 영상만 조용히 안 생긴다
            rc = 1
        if check_edit_track_chain() != 0:   # 편집 생성 = 자동 가림·키잉·크로마키(운영자 260808) — 구판은 옵션이 켜지는데 생성엔 아무 일도 안 생겼다(무증상 = 운영자 눈이 유일한 검출기)
            rc = 1
        if check_thumb_vote_chain() != 0:   # 썸네일 화풍 투표 폐루프(운영자 260805 — 적재는 되는데 커밋이 없어 증발하거나, 쌓이는데 아무도 안 읽는 죽은 원장이 되는 두 축을 함께 막는다)
            rc = 1
        if check_ask_srcimg_chain() != 0:   # 출처 글 본문 이미지 수확(운영자 260804 — 본문이 그림뿐인 커뮤니티 글이 '읽을 글 0'으로 ANALYSIS_FAILED 되던 축 봉합 · 층 빠지면 무증상 재발)
            rc = 1
        if check_ask_img_legible() != 0:   # 요약요청에 붙인 사진이 읽히는 크기로 나가는가(운영자 260812 — 나빠져도 첨부 화면은 멀쩡하고 증상은 한참 뒤 요약 품질로만 나오는 축)
            rc = 1
    except Exception as e:
        print('⚠️ 출처 본문 이미지 수확 체인 게이트 스킵:', e)
    try:
        if check_prev_center() != 0:   # 미리보기 빈 상태 중앙 = 업로드 픽토 단독(운영자 260802 — 표면마다 재발하는 '중앙에 버튼 하나 더' 차단)
            rc = 1
    except Exception as e:
        print('⚠️ 미리보기 중앙 게이트 스킵:', e)
    try:
        if check_twocol_breakpoint() != 0:   # 결과 레일 2단 분기점 표면 간 한 값(운영자 260802 — 이미지만 900 하향·영상 1100 잔류가 실측기 사각[스모크 1280·폰 430]을 그냥 통과한 사고 봉합 · 렌더 0 정적)
            rc = 1
    except Exception as e:
        print('⚠️ 2단 분기점 게이트 스킵:', e)
    try:
        if check_layout_transition() != 0:   # 레이아웃 유발 transition 래칫(운영자 260804 impeccable 평의회 선별이식 ① — 기존 축은 전부 애니메이션 '끝난 뒤'만 재서 재생 중 리플로가 사각 · 임계 = impeccable layout-transition 속성 집합 채택 = 값 창작 0)
            rc = 1
    except Exception as e:
        print('⚠️ 잰크 전이 게이트 스킵:', e)
    try:
        if check_keyframes_dup() != 0:   # @keyframes 중복 정의 0(평의회 260804 4·5·8번 — 재선언은 앞 선언을 통째로 대체한다[CSS Animations L1 §2] · 실사고 = 260710에 폐지된 .filterpop 잔해 popOut 사본이 살아있는 팝업 3종의 퇴장 모션을 지배 · 동값이라 6주 무증상)
            rc = 1
        if check_comment_seam() != 0:   # CSS 주석 이음매 0(운영자 260807 «아이디어도 적용하고» — 줄 끝 사유 주석의 `*/`가 선행 미종료 주석을 조기 종료시켜 남은 본문이 라이브 CSS로 새던 무증상 사고 · 실측 2건 = song 발사 테두리 .2→.15 · edit 히트슬롭 소멸)
            rc = 1
    except Exception as e:
        print('⚠️ @keyframes 중복 게이트 스킵:', e)
    try:
        if check_css_dead_state() != 0:   # 죽은 상태 오버라이드(운영자 260806 "아이디어 해결 ㄱ" — 주석은 「살아 있다」는데 특이도로 지는 상태 · 실사고 = .dropping 링 6일 실명 + #go .08이 발사 4상태 + 운영자 260731 「너무 옅음」 .2 지시까지 눌러 죽임 · 기존 게이트는 raw 개수·이름 중복·애니 끝난 그림 축이라 「상태가 캐스케이드에서 지는가」가 사각)
            rc = 1
    except Exception as e:
        print('⚠️ 죽은 상태 오버라이드 게이트 스킵:', e)
    try:
        if check_shared_canon() != 0:   # 공용 부품 CSS = 정본 1개 참조(운영자 260807 "다른 모든 공간에도 이와 동일하게" — 3파일+ 완전동값 사본 83종 중 전역·원자 5종 승격 · 나머지는 캐스케이드 전역 재배치 때문에 가족 단위 순차 이관 필요)
            rc = 1
        if check_clip_canon() != 0:   # 클립 4문법 = 정본 1개 참조(운영자 260807 "정본1개를 참조해서 불러오는 개념으로 쓰셈" — 접두만 다른 사본 4벌이 z-index·transition·tap-highlight·backdrop-filter 4축으로 이미 갈라져 있던 것의 기계화 · 기존 클립 게이트는 「붙었나」만 봐서 「한 원천에서 오는가」가 사각)
            rc = 1
        if check_anchor_menu_canon() != 0:   # 앵커 메뉴 문법 = 한 벌(운영자 260805 "아이디어 ㄱ" — 설정·스튜디오 헤더 메뉴·PASS 사유 3표면이 값을 각자 베껴 쓰다 PASS 창만 혼자 다른 문법으로 갈라진 실사고의 기계화 · 기존 게이트는 raw 개수·뷰어 간 동값·모달 헤더 기하 축이라 「같은 결의 메뉴가 한 벌인가」가 사각)
            rc = 1
    except Exception as e:
        print('⚠️ 앵커 메뉴 문법 게이트 스킵:', e)
    try:
        if check_debt_ratchet() != 0:   # 면책표 총량 래칫(운영자 260803 — 「알고 동결한 부채」가 「원래 그런 것」으로 굳는 축 차단 · 줄이면 자유·늘리면 사유+--debt-sync)
            rc = 1
        if check_trail_decl_parity() != 0:   # 정본 규칙 상속 대조(운영자 260803 — 축을 사람이 추가하는 방식의 사각 제거 · 히트패드 `::after` 누락이 그 사각에서 2.4배 드리프트를 만들었다)
            rc = 1
        if check_affordance_inherit() != 0:   # 스킨 계승 시 어포던스(cursor·press) 비계승(운영자 260803 — 리드백 칩이 버튼 스킨과 함께 손가락 커서까지 물려받아 「눌러도 아무 일 없는 자리」가 6건 실재했다 · 런타임 짝 = smoke_hitzone H3)
            rc = 1
        if check_geni_scope() != 0:   # geni 어휘 전역 질의 금지(운영자 260803 6차 "게이트 ㄱㄱ" — 폼 두 홈(#genidlg↔#geniHost) ↔ 다운로드 창(#dlgrab)이 클래스를 공유해 전역 질의가 남의 창을 문다 · 실사고 2건{폰 레일 소멸·핸들러 덧바인딩} + 잠복 1건)
            rc = 1
        if check_onoff_literal() != 0:   # 이진 토글 ON/OFF 리터럴 금지(운영자 260803 "기능 워딩이 점등하냐 안하냐로 onoff" — cnTog 워드 점등 정본의 재발 차단 · 면책 = _ONOFF_BASE 스냅샷)
            rc = 1
    except Exception as e:
        print('⚠️ ON/OFF 리터럴 게이트 스킵:', e)
    try:
        if check_axis_chip_home() != 0:   # 값축 거처(운영자 260804 "idea go" — 다값 카드 헤더 축은 헤더 우측 칩 단일 문법 · 컷 편집이 6일 잠복했던 「한 스택 두 문법」 재발 차단)
            rc = 1
    except Exception as e:
        print('⚠️ 값축 거처 게이트 스킵:', e)
    try:
        if check_nm_jobs() != 0:   # 여러 작업 동시 추적(운영자 260810 — 5탭 nm-jobs.js 상속 + 구판 단일 슬롯·전역 폴 중단 부활 차단)
            rc = 1
    except Exception as e:
        print('⚠️ 동시 작업 추적 게이트 스킵:', e)
    try:
        if check_nm_sync() != 0:   # 동기화 생명선 상속(운영자 260803 4차 — 스튜디오 전 탭 nm-sync.js 상속 + 모듈 3축 골격 · nmRefresh 자동발견)
            rc = 1
    except Exception as e:
        print('⚠️ 동기화 생명선 게이트 스킵:', e)
    try:
        if check_label_fill() != 0:   # 콘텐츠 라벨색(cat/bias) 솔리드 필 금지(평의회 Q329 ④ — 기능색 오독 차단 · 저알파 워시 허용)
            rc = 1
    except Exception as e:
        print('⚠️ 발사버튼 규격 게이트 스킵:', e)
    try:
        if check_html_charset() != 0:   # docs HTML 첫 1KB <meta charset> 필수(하드 게이트 — 폰 로컬 열람 한글 깨짐 · [7] 260720)
            rc = 1
    except Exception as e:
        print('⚠️ HTML charset 게이트 스킵:', e)
    try:
        if check_tabs_headers() != 0:   # 도구 스튜디오 탭 src의 _headers no-cache 등재(하드 게이트 — 신설 스튜디오 캐시 계약 누락 차단 · tr/song/nb/sb 드리프트 선례 · 운영자 260724 한 수)
            rc = 1
    except Exception as e:
        print('⚠️ 탭 헤더 게이트 스킵:', e)
    try:
        check_candidates_size()   # candidates.json 크기 WARN(1MB↑ = api/candidates 빈[] 서빙실패로 수집함 텅빔 위험·260714)
    except Exception as e:
        print('⚠️ candidates 크기 check 스킵:', e)
    try:
        if check_sens_vocab() != 0:   # 민감 통제어휘 미러 정합(하드 게이트 — 5↔7 드리프트·DRUG_RE 따로놀기 차단·260625)
            rc = 1
    except Exception as e:
        print('⚠️ 민감 통제어휘 check 스킵:', e)
    try:
        if check_claude_failover() != 0:   # claude -p 호출 = 폴오버 SSOT 경유 통일(자체 쿼터처리·따로놀기 차단 · 260629 weekly한도 전건실패)
            rc = 1
    except Exception as e:
        print('⚠️ claude 폴오버 게이트 스킵:', e)
    try:
        if check_judge_bare() != 0:   # judge = OAuth 전용 → --bare 금지(OAuth 안 읽어 인증 즉사 = 260701 사고 진짜원인) · --safe-mode만 · 생성경로 --bare 기본 ON도 차단
            rc = 1
    except Exception as e:
        print('⚠️ --bare 도구충돌 게이트 스킵:', e)
    try:
        if check_fast_max_h_parity() != 0:   # FAST_MAX_H viewer↔auto_pick 크로스랭귀지 패리티(하드 게이트·fail-closed·260710)
            rc = 1
    except Exception as e:
        print('❌ check_fast_max_h_parity 예외(fail-closed):', e); rc = 1
    try:
        if check_follow_enters_parity() != 0:   # followEnters viewer↔daily_health 크로스랭귀지 패리티(하드 게이트·fail-closed·260805) — 갈리면 묻힘 계기판이 조용히 거짓 보고
            rc = 1
    except Exception as e:
        print('❌ check_follow_enters_parity 예외(fail-closed):', e); rc = 1
    try:
        if check_sc_ts_contract() != 0:   # scTs 시간축 계약 실행 대조(하드 게이트·fail-closed — 나이 판정 뒤집힘 = 신규↔누적 분배·랭킹 붕괴·260725 Q522 회귀발)
            rc = 1
    except Exception as e:
        print('❌ check_sc_ts_contract 예외(fail-closed):', e); rc = 1
    try:
        if check_shell_cache_parity() != 0:   # SW 셸 캐시명 viewer↔sw.js 패리티(하드 게이트 — 한쪽만 버전업 = 죽은 캐시 쓰기·260717 평의회 1·9)
            rc = 1
    except Exception as e:
        print('❌ check_shell_cache_parity 예외(fail-closed):', e); rc = 1
    try:
        if check_thumb_chain() != 0:   # 최근 게시물 커버 회수 체인(하드 게이트 — 260718 '무성 생략 2/25'가 260803 '2/12'로 재발한 축 · 서버 3층 + 뷰어 강등 1층)
            rc = 1
    except Exception as e:
        print('❌ check_thumb_chain 예외(fail-closed):', e); rc = 1
    try:
        if check_subs_author_scope() != 0:   # 구독 = 작성자 검문 의무(하드 게이트 — 260804 실사고: 스레드 구독 20건이 등록 0계정 = 추천 피드 강탈)
            rc = 1
    except Exception as e:
        print('❌ check_subs_author_scope 예외(fail-closed):', e); rc = 1
    try:
        if check_disaster_landmark_sign() != 0:   # ⑭-e 랜드마크 = 발신 서명 오탐 차단(하드 게이트 — 260805 실사고: 「[서해구청]」 서명이 교통 후속 안내를 기기 긴급알림으로 발사)
            rc = 1
    except Exception as e:
        print('❌ check_disaster_landmark_sign 예외(fail-closed):', e); rc = 1
    try:
        if check_disaster_lm_stale() != 0:   # ⑭-e 랜드마크 = 박제 필드 2층 방어(하드 게이트 — 260805 2차: 코드 봉합 09:37 착지 후에도 07:03 구운 lm이 데이터에 살아남아 10:20 리포트 재등장)
            rc = 1
    except Exception as e:
        print('❌ check_disaster_lm_stale 예외(fail-closed):', e); rc = 1
    try:
        if check_rpt_origin_coverage() != 0:   # 알림 리포트 출처표 = 뷰어 생산 알림 전건 커버(하드 게이트 — 260805 실사고: sys:fire: 분기 누락으로 리포트가 없는 파일 messages/sys:fire:….json을 지목)
            rc = 1
    except Exception as e:
        print('❌ check_rpt_origin_coverage 예외(fail-closed):', e); rc = 1
    try:
        if check_fail_msg_todo() != 0:   # 요약 실패 알림 = 조치 주체를 말한다(하드 — 260813 실사고: 👉 미부착으로 운영자 조치 3분류가 전건 '클로드가 볼 일' 칸에 앉아 진짜 코드 건을 가렸다)
            rc = 1
    except Exception as e:
        print('❌ check_fail_msg_todo 예외(fail-closed):', e); rc = 1
    try:
        if check_shell_put_integrity() != 0:   # 셸캐시 put = 절단 검문(</html> 꼬리) 의무(하드 게이트 — 260802 재발: sw.js만 검문·페이지측 put 무검문 = 절단 셸 재주입)
            rc = 1
    except Exception as e:
        print('❌ check_shell_put_integrity 예외(fail-closed):', e); rc = 1
    try:
        if check_idle_timer_guard() != 0:   # 유휴 타이머 가드(C16 런타임 축의 정적 짝 · 260807 — 모달 뒤 DOM을 만지는 영구 타이머는 가시성·모달 가드 동반 · 형제는 갖는데 자기만 안 가진 사고가 6주 잠복했다)
            rc = 1
        if check_boot_bg_parity() != 0:   # 스플래시→앱 배경 3값 정합(theme는 하드·background는 WARN — CSS가 manifest를 못 읽어 손복사인 축 · 260805 실측 불일치)
            rc = 1
    except Exception as e:
        print('❌ check_boot_bg_parity 예외(fail-closed):', e); rc = 1
    try:
        if check_workflow_amend() != 0:   # 워크플로 결과 커밋 --amend 금지(하드 게이트 — 260803 실측: 자기 커밋 드랍 시 남의 푸시 커밋 개서 = non-ff 영구거절·산출 유실)
            rc = 1
    except Exception as e:
        print('❌ check_workflow_amend 예외(fail-closed):', e); rc = 1
    try:
        if check_push_send_checkout() != 0:   # 완료 푸시 레인의 구독자 명단 체크아웃(하드 게이트 — 260816 실측: sparse에 push/ 누락 시 「구독자 없음」으로 조용히 발송 생략·스텝은 초록·7레인 동시 사망)
            rc = 1
    except Exception as e:
        print('❌ check_push_send_checkout 예외(fail-closed):', e); rc = 1
    try:
        if check_push_abs_url() != 0:   # 알림 딥링크 절대 주소(하드 게이트 — 260816 실측: 상대경로가 폰 SW의 origin을 따라가 옛 화면으로 데려갔다·옛 SW는 코드로 못 고친다)
            rc = 1
    except Exception as e:
        print('❌ check_push_abs_url 예외(fail-closed):', e); rc = 1
    try:
        if check_prompt_literal_quoting() != 0:   # 다중라인 프롬프트 리터럴 인용 무결성(하드 게이트 — 260805 실측: 미이스케이프 " 하나가 prompt 변수를 통째로 삼켜 요약 요청 전건 실패·문법은 유효라 bash -n 무통과)
            rc = 1
    except Exception as e:
        print('❌ check_prompt_literal_quoting 예외(fail-closed):', e); rc = 1
    try:
        if check_pages_skip() != 0:   # [CF-Pages-Skip] 오배선 차단(하드 게이트 — 260803 평의회: 도장·제작·뉴스 큐에 번지면 배포 보증·수렴·알림 조용히 사망)
            rc = 1
    except Exception as e:
        print('❌ check_pages_skip 예외(fail-closed):', e); rc = 1
    try:
        if check_coalesce_pair() != 0:   # [CF-Pages-Skip] **짝** 강제(하드 게이트 — 260803 실사고: 코얼레싱 스킵 + 라이브 서빙 부재 = tbs_data 국내 감시축 조용한 정지)
            rc = 1
    except Exception as e:
        print('❌ check_coalesce_pair 예외(fail-closed):', e); rc = 1
    try:
        if check_curation_constants() != 0:   # 큐레이션 랭킹 상수↔§★ 문서 정합(하드 게이트 — #1135식 자기-revert·드리프트 차단·260628 감사 C8)
            rc = 1
    except Exception as e:
        print('⚠️ check_curation_constants 스킵:', e)
    try:
        if check_fp_parity() != 0:   # 지문축 py↔js 미러 패리티(260720 평의회C M3 — fp 트라이어드 무가드 사각 봉합)
            rc = 1
    except Exception as e:
        print('⚠️ check_fp_parity 스킵:', e)
    try:
        if check_cat_kw() != 0:   # CAT_KW 카테고리 키워드사전 py↔js 정합(하드 게이트 — 키워드 한쪽만 고침=분류 오분류 근본·260628 C9)
            rc = 1
    except Exception as e:
        print('⚠️ check_cat_kw 스킵:', e)
    try:
        if check_issue_badge_parity() != 0:   # ⚡이슈 배지 게이트 viewer↔build-viewer 규칙 동일(하드 게이트 — 한쪽만 수정=수집함↔피드 배지 드리프트·260702 10인 검증7)
            rc = 1
    except Exception as e:
        print('❌ check_issue_badge_parity 예외(fail-closed — 게이트 무력화 방지·260710):', e); rc = 1
    try:
        if check_force_parity() != 0:   # 카테고리 강마커·오버라이드 17쌍 py↔js 바이트 동기(하드 게이트 — 한쪽만 수정=데이터↔화면 분류 드리프트·260704)
            rc = 1
    except Exception as e:
        print('⚠️ check_force_parity 스킵:', e)
    try:
        if check_k_models() != 0:   # /k 모델·설정 3면 패리티(하드 게이트 — 한쪽만 수정=칩 값 무성 유실·프로필 없는 분기·260709 개편 P1)
            rc = 1
    except Exception as e:
        print('⚠️ check_k_models 스킵:', e)
    try:
        if check_autocomplete() != 0:   # 평문 텍스트칸 OS 자동완성 끔 4종(하드 게이트 — 자동완성 바 재발 차단·STAGE1b·260628)
            rc = 1
        if check_clip_coverage() != 0:   # 모든 텍스트 입력칸 = 클립(복사·붙여넣기·지우개) 보유(하드 게이트 · 운영자 260803 "공식처럼가야함" — 새 칸이 조용히 빠지는 것 차단)
            rc = 1
        if check_input_canon() != 0:   # 스튜디오 입력칸 = 정본 활자·박스·창 크기(하드 게이트 · 운영자 260804 "게이트 ㄱㄱ" — 활자→박스→창 크기 3연속 드리프트의 기계화)
            rc = 1
    except Exception as e:
        print('⚠️ check_autocomplete 스킵:', e)
    try:
        if check_url_placeholder() != 0:   # URL 입력칸 placeholder = "https://…" 단일 문법(하드 게이트 — 안내 산문 재유입 차단·CII 「URL 입력칸」·260801)
            rc = 1
    except Exception as e:
        print('⚠️ check_url_placeholder 스킵:', e)
    try:
        check_x_char()   # 닫기/삭제 × 문자 → SVG 권장(WARN-only·병렬작업 파일 비차단)
    except Exception as e:
        print('⚠️ check_x_char 스킵:', e)
    try:
        if check_tokens_link() != 0:   # 공유 구조토큰 tokens.css 4뷰어 링크(하드 게이트·§🎨 STAGE3·260628)
            rc = 1
    except Exception as e:
        print('⚠️ check_tokens_link 스킵:', e)
    try:
        if check_dangling_var() != 0:   # 댕글링 var() = 미정의 토큰 무폴백 참조(하드 — IACVT 무효 렌더 차단·평의회 갭① Q169)
            rc = 1
    except Exception as e:
        print('⚠️ check_dangling_var 스킵:', e)
    try:
        if check_palette_sync() != 0:   # 팔레트 핀 게이트 — 도구 뷰어 공유 팔레트 accent/의미색 = index 동값(하드 — inline 색 복사 드리프트 차단 · 운영자 260723 Q463 "색 토큰 미리 잡아놓기")
            rc = 1
    except Exception as e:
        print('❌ check_palette_sync 예외(fail-closed):', e); rc = 1
    try:
        if check_soremeori() != 0:   # 소머리(구분자 •) 텍스트 흰색·블릿 형광·토큰(하드 게이트 — 회색/무블릿/리터럴 재발 차단·§📐·260629)
            rc = 1
    except Exception as e:
        print('⚠️ check_soremeori 스킵:', e)
    try:
        if check_playground() != 0:   # 플레이그라운드 템플릿 5요소·near·스크롤보존(하드 — 골격 재작성 편차 차단·§플레이그라운드 0-1·260713)
            rc = 1
    except Exception as e:
        print('⚠️ check_playground 스킵:', e)
    try:
        if check_anchor_liveness() != 0:   # 기틀 앵커 생존(하드 게이트 — CLAUDE.md 개편 시 기틀 문서의 죽은 § 앵커 잔존 자동 차단 · 운영자 260718 Q146 승인)
            rc = 1
        if check_qledger_unique() != 0:   # 원장 Q번호 유일성(하드 게이트 — 동시 세션 번호 경합 = [Q.NN] 1:1 참조 모호 · 신규 중복만 래칫 차단 · 운영자 260717 승인)
            rc = 1
    except Exception as e:
        print('❌ check_qledger_unique 예외(fail-closed — 게이트 무력화 방지):', e); rc = 1
    try:
        if check_loader_ssot() != 0:   # 로딩 표기 SSOT(하드 게이트 — 새 로더 = window.nmLoader만·raw gdots 신설 차단 · 운영자 260723 Q461 "정해진 로딩만")
            rc = 1
    except Exception as e:
        print('⚠️ check_loader_ssot 스킵:', e)
    try:
        if check_model_ids() != 0:   # 모델 ID 드리프트(하드 — 승격 시 '한 곳 빠뜨림' 봉쇄 · 정본 shared/models.json · 승격기 = apply_models.py · 운영자 260725 한 수)
            rc = 1
    except Exception as e:
        print('❌ check_model_ids 예외(fail-closed):', e); rc = 1
    try:
        if check_ssot_coverage() != 0:   # 정본 커버리지 역방향(하드 — 문서가 정본이라 선언했는데 기계가 없는 사각 = 신규만 차단 · 운영자 260725 한 수)
            rc = 1
    except Exception as e:
        print('❌ check_ssot_coverage 예외(fail-closed):', e); rc = 1
    try:
        if check_drive_move_bundle() != 0:   # 배포 번들 드리프트(하드 — ps1만 고치고 재생성 잊으면 운영자 PC에 옛 코드 · CLAUDE.md [9-1])
            rc = 1
    except Exception as e:
        print('❌ check_drive_move_bundle 예외(fail-closed):', e); rc = 1
    try:
        if check_cloud_action_chain() != 0:   # 클라우드 액션 레인(하드 — 드라이브 action 폴더 = git 액션 대체 · 한 층 소실 = 조용한 반쪽 · 260814)
            rc = 1
    except Exception as e:
        print('❌ check_cloud_action_chain 예외(fail-closed):', e); rc = 1
    try:
        if check_pc_lane_stages() != 0:   # 액션 대체 레인 스테이지(하드 — 한 축이 빠져도 레인은 초록 = 조용한 정지 · 260814)
            rc = 1
    except Exception as e:
        print('❌ check_pc_lane_stages 예외(fail-closed):', e); rc = 1
    try:
        if check_secret_coverage_chain() != 0:   # 빈 칸 점검 레인(하드 — 한 층만 빠져도 레인은 초록인데 빈 칸을 영영 못 본다 · 260816)
            rc = 1
    except Exception as e:
        print('❌ check_secret_coverage_chain 예외(fail-closed):', e); rc = 1
    try:
        if check_land_xours() != 0:   # 착지 내용 소실 래칫(260816 — push 는 성공하는데 우리 변경이 버려지는 축 · `-X ours` 의미 반전 · check_land_silence 가 원리적으로 못 보는 짝)
            rc = 1
    except Exception as e:
        print('❌ check_land_xours 예외(fail-closed):', e); rc = 1
    try:
        if check_land_silence() != 0:   # 착지 침묵 래칫(260816 — 「본선에 올리는 데 실패했는데 초록으로 끝나는」 자리 · 도장 실사고 축의 일반화 · 인라인 착지만 대상)
            rc = 1
    except Exception as e:
        print('❌ check_land_silence 예외(fail-closed):', e); rc = 1
    try:
        if check_canon_host() != 0:   # 화면 주소 정본(하드 — 코드가 옛 화면을 부르면 화면 증상 0으로 조용히 죽는다 · 260816 계정 이관 후속)
            rc = 1
    except Exception as e:
        print('❌ check_canon_host 예외(fail-closed):', e); rc = 1
    try:
        if check_font_shorthand() != 0:   # 활자 무효축약(하드 — `font:` 축약 안 inherit = 선언 전체 무효 · 조용한 상속 드리프트)
            rc = 1
    except Exception as e:
        print('❌ check_font_shorthand 예외(fail-closed):', e); rc = 1
    try:
        if check_form_font_inherit() != 0:   # 폼 활자 계승(하드 — UA 기본이 끊는 글꼴·자간 상속을 리셋으로 복구했는지)
            rc = 1
    except Exception as e:
        print('❌ check_form_font_inherit 예외(fail-closed):', e); rc = 1
    try:
        check_branch_freshness()   # 브랜치 신선도(WARN — 평행 구현 사고 재발방지 · 260727)
    except Exception as e:
        print('⚠️ check_branch_freshness 생략:', e)
    try:
        if check_gate_docs() != 0:   # 게이트 문서화 메타 게이트(하드 — 모든 def check_*가 정본 문서 등재됐는지 · "만들어놓고 안 봄" 구조 차단 · 운영자 260723 Q468)
            rc = 1
    except Exception as e:
        print('❌ check_gate_docs 예외(fail-closed):', e); rc = 1
    try:
        check_ssot_linkage()   # 공유 부품 SSOT 링크 연결성(WARN·비차단 — nm-*.js가 발견 체인 3축 미등재 = 고아 후보 경보 · §0-17 5축의 얕은 기계 보조 · 운영자 260723 Q466)
    except Exception as e:
        print('⚠️ check_ssot_linkage 스킵:', e)
    return rc


if __name__ == '__main__':
    if '--debt-sync' in sys.argv:
        sys.exit(check_debt_ratchet(sync=True))
    if '--fix-qnum' in sys.argv:   # 원장 번호 경합 자동 재부여(이 브랜치 신규 행만) — 게이트 본체는 안 돌린다
        sys.exit(fix_qnum_reassign())
    sys.exit(main())
