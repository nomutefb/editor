#!/usr/bin/env python3
# digest_guard.py — 다이제스트(queue/*.md) 규격·자수 기계 린트 (비차단 · 분신술② NEW-1 · 260703 · 검증5 정밀화)
#
# 왜: P1 길이 룰(Thread 430·IG 800·자유요약 850~1000)이 모델 '자가 추정'에만 의존 → 실측 괴리 −229~+88자
#     (Thread 상한 초과 4/17건이 "약 430/450" 표기로 통과 = 자가검증 무력화·실측 260702). 지침 3연속 길이
#     교정(v1.18.0/18.1/18.4)이 계측 부재로 계속 샜다 → 저장 직후 실측해 Actions 로그로 가시화.
# 검사(전부 비차단·exit 항상 0): ⚠️급 = 상한 초과(하드 500은 개행 포함 실카운트)·⚡ 혼입·제목 복붙/[속보] 잔존
#     / ℹ️급(정보성) = 과소 활용·자가표기 괴리·분모 드리프트 — 2단 분리로 진짜 신호가 안 묻히게(검증5).
# 카운트 기준 = 개행 제외(분신술② 실측·PROJECT_MEMORY 사례와 정합) · 면책 줄("⚠️ 본문 내용은…")은 지침
#     규정("면책 줄은 글자수 카운트 제외")대로 빼고 센다 · 플랫폼 하드 500 판정만 개행 포함(Threads 실카운트 통설).
# 사용: python3 shared/digest_guard.py <queue/xxx.md>   (analyze.sh·ask.sh가 저장 직후 호출 · 수동 점검 동일)
import os, re, sys

_DISCLAIMER = re.compile(r"^⚠️ 본문 내용은.*$", re.M)   # 편향 가드 면책 한 줄(지침: 카운트 제외)

def _blk(body, name):
    """### [<name> …] 헤더 다음 ```text 코드블록 본문(없으면 None)."""
    m = re.search(r"^###\s*\[" + re.escape(name) + r"[^\]]*\]\s*\n+```text\n(.*?)\n```", body, re.M | re.S)
    return m.group(1) if m else None

def _clen(s):
    return len(_DISCLAIMER.sub("", s).replace("\n", ""))   # 개행·면책 제외 실측

def _clen_hard(s):
    # 플랫폼 하드 상한 판정 = 물리 총량(면책 줄도 실제 게시물에 포함되므로 안 뺌·개행 포함 — 재검증11)
    return len(s)

_QUAL = r"(?:그룹|밴드|가수|배우|아이돌|기업|회사|의원|장관|시장|지사|교수|감독|대표|회장|사장|위원장|청장|서장|총장|주지사|대통령)"
_SUBJ_LESS = re.compile(r"^[^은는이가\n]{0,60}?(?:에서|으로|로)\s+(?:시작됐다|번졌다|불거졌다|비롯됐다|출발했다)")
# 한국 성씨(상위 — 인명 오탐 차단용 · thumb_gen `_subject_name` 4겹 게이트 관례 계승)
_SURNAME = set("김이박최정강조윤장임한오서신권황안송류전홍고문양손배백허유남심노하곽성차주우구원탁진지엄채원천방공현함변염여추도소석선설마길연위표명기반라왕금옥육인맹제모남탄국여")


def derive_check(path):
    """파생 무결성(자유요약 → IG·Thread) 비차단 경고 — 260810 신설.
    ⚠️ 신설 사유 = 이 파이프라인의 검증은 **한 블록 안**만 본다(자수·⚡ 혼입·제목 복붙·자가표기 괴리).
    「자유요약에 있던 것이 파생본에서 사라졌는가」는 축 자체가 없었다 — 그래서 실사고 260810
    (김희철 태극기 건)에서 자유요약 「**그룹 슈퍼주니어의** 김희철」의 소속이 IG·Thread에서
    통소실돼 「김희철이」로 맨몸 등장했는데 규격(자수·📍 골격·⚡ 줄)은 전부 통과했다.
    01_지침 [지칭 260702]가 「자유요약이 정한 축을 IG·Thread가 **그대로 상속**」이라고
    이미 못박은 계약인데 **위반을 잡는 장치가 없었다** = 운영자 눈이 유일한 검출기.
    2방향(누락·날조)은 같은 축의 앞뒤다 — 누락 = 있던 게 사라짐 · 날조 = 없던 게 생김.
    ⚠️ 비차단(경고 전용) — 정당한 축약이 섞이므로 하드면 파이프가 언다."""
    try:
        body = open(path, encoding="utf-8").read()
    except Exception as e:
        print("ℹ️ derive: 읽기 실패 %s" % e)
        return 0
    base = _blk(body, "자유요약")
    if not base:
        return 0
    def _prose(s):
        # ⚡ 출처 줄·면책 줄 제외 — 그 줄의 발행연도(2026)가 전건 위양성을 만든다(첫 실행 실측)
        return "\n".join(l for l in s.split("\n") if not l.lstrip().startswith(("⚡", "ⓔ", "⚠️")))

    base_p = _prose(base)
    derived = {lab: _prose(_blk(body, lab) or "") for lab in ("IG", "Thread")}
    hits = []
    # ① 누락 — 자유요약 「<소속·직함어> <고유명사>의 <인명>」의 소속어가 파생본에서 통소실
    #    (실사고 = 「그룹 슈퍼주니어의 김희철」 → 파생본 「김희철이」 맨몸)
    #    ⚠️ 2겹 가드가 실효 조건(첫 전수 실측 = 179건 중 대부분 위양성이었다):
    #      ⓐ 「의」 필수 — 없으면 `시장`(market)·`대표`(representative)처럼 _QUAL 어휘가
    #        **다른 뜻**으로 쓰인 자리에서 뒤 단어를 인명으로 오독한다(실측 「빠르게」·「체코를」).
    #      ⓑ 성씨 사전 — 인명 첫 글자가 한국 성씨여야 한다(thumb_gen `_subject_name`의
    #        4겹 게이트 관례 계승 · 위양성이 게이트를 죽인다는 이 레포 반복 교훈).
    #      ⓒ 조사 = 주격·주제격만(이/가/은/는/씨) — 인명 첫 등장은 그 자리가 정본이고,
    #        목적격까지 열면 「원인을」(원=성씨) 같은 일반명사가 인명으로 샌다(실측 잔여 1건 봉합).
    for m in re.finditer(_QUAL + r"\s+[가-힣A-Za-z0-9]{2,12}의\s*([가-힣]{2,4})(?=이|가|은|는|씨)", base_p):
        head = re.match(_QUAL, m.group(0)).group(0)
        name = m.group(1)
        if name == head or len(name) < 2 or name[0] not in _SURNAME:
            continue
        for lab, d in derived.items():
            if d and name in d and head not in d:
                hits.append("%s: 「%s」의 소속·직함(%s) 소실 — 자유요약엔 있다([정체성 최후순 보호] 위반)" % (lab, name, head))
    # ② 무주어 개문 — 파생본 첫 칸이 주어 없이 「~에서 시작됐다」류로 열림
    for lab, d in derived.items():
        cells = [l.strip() for l in d.split("\n") if l.strip().startswith(("🔎", "📍"))]
        if cells and _SUBJ_LESS.match(cells[0][1:].strip()):
            hits.append("%s: 첫 칸 무주어 개문 — 「%s…」(무엇이 시작됐는지 주어 없음)" % (lab, cells[0][:34]))
    # ③ 날조 — 파생본에만 있는 4자리 이상 수치(자유요약 미등장 · 산문부 한정)
    #    ⚠️ 2겹 면제가 실효 조건(전수 16건 판독 = 대부분 **정당한 축약**이었다):
    #      ⓐ 연도(19xx·20xx) 제외 — 「2014년이 2026년으로 바뀐 순간」류. 날조가 아니라 시점 서술이다.
    #      ⓑ 반올림 허용 — 자유요약에 **같은 자릿수 · 상위 2자리 동일**한 수가 있으면 축약으로 본다
    #        (실측 오탐 = 7500↔7506 「7500원대」 · 1700↔1,719 · 1,700↔1,708). 파생본은 압축이 본령이라
    #        반올림은 규격 위반이 아니다 — 이걸 안 빼면 축이 「압축했다」를 「날조했다」로 부른다.
    #      ⓒ 헤드(각 블록 첫 줄) 제외 — 헤드는 자유요약 파생이 아니라 Fact·원문 기반의
    #        별도 규격이다(01_지침 [헤드·타이틀 공통 원칙]). 전수 잔여 8건이 전부 헤드였다
    #        (「8500억 과징금」·「훔친 1400편」·「지하 1200m」) = 자유요약에 없는 게 정상.
    base_digits = set(re.findall(r"\d[\d,]*", base_p))
    base_norm = {x.replace(",", "") for x in base_digits}
    for lab, d in derived.items():
        d_body = "\n".join(d.split("\n")[1:]) if d else ""   # ⓒ 헤드 줄 제외
        for n in set(re.findall(r"\d[\d,]{3,}", d_body)):
            nn = n.replace(",", "")
            if nn in base_p.replace(",", ""):
                continue
            if len(nn) == 4 and (nn.startswith("19") or nn.startswith("20")):
                continue                                    # ⓐ 연도
            if any(len(b) == len(nn) and b[:2] == nn[:2] for b in base_norm):
                continue                                    # ⓑ 반올림
            hits.append("%s: 자유요약에 없는 수치 「%s」 등장(날조 의심)" % (lab, n))
    seen, out = set(), []
    for h in hits:
        if h not in seen:
            seen.add(h)
            out.append(h)
    if out:
        print("ℹ️ 파생 무결성 경고 %d건 — %s" % (len(out), os.path.basename(path)))
        for h in out[:8]:
            print("   · " + h)
    return 0


def _claim(body, name):
    """헤더의 자가표기 자수·분모 추출 — '약 460/500자'·'728/800자'·'936자' 대응.
    미치환 플레이스홀더(N/800자)는 claim=None(오파싱 방지·검증5)."""
    hm = re.search(r"^###\s*\[" + re.escape(name) + r"[^\]]*?약?\s*([\d,]+|N)\s*(?:/\s*([\d,]+))?\s*자", body, re.M)
    if not hm:
        return None, None
    c = hm.group(1)
    claim = None if c == "N" else int(c.replace(",", ""))
    denom = int(hm.group(2).replace(",", "")) if hm.group(2) else None
    return claim, denom

def lint(path):
    raw = open(path, encoding="utf-8").read()
    warns, infos = [], []
    fmm = re.search(r"^---\s*$(.*?)^---\s*$", raw, re.M | re.S)
    body = raw[fmm.end():] if fmm else raw
    # 닫는 '---' 누락 회귀 카나리아(260704 실측 '중국인 렌터카' — LLM이 frontmatter 닫는 표식 생략 → 뷰어 메타 raw 노출).
    #   생성측(ask/analyze.sh) awk가 이미 닫는 '---'를 보증하므로 정상 파이프라인에선 안 뜸 → 뜨면 그 awk 회귀 신호.
    #   비차단(lint는 return 0 유지) = 저장은 이미 끝난 시점이라 차단 무의미·자동수정(awk)이 정본 방어. 로그 조기발견용.
    if raw.lstrip().startswith("---") and len(re.findall(r"^---\s*$", raw, re.M)) < 2:
        warns.append("frontmatter 닫는 '---' 누락 — 뷰어 메타 raw 노출 위험(생성측 awk 보증 회귀 의심)")
    title = title_ko = ""
    if fmm:
        tm = re.search(r'^title:\s*"?(.*?)"?\s*$', fmm.group(1), re.M)
        title = (tm.group(1).strip() if tm else "")
        tk = re.search(r'^title_ko:\s*"?(.*?)"?\s*$', fmm.group(1), re.M)
        title_ko = (tk.group(1).strip() if tk else "")
    h1m = re.search(r"^#\s+(.+?)\s*$", body, re.M)
    h1 = (h1m.group(1).strip() if h1m else "")

    # 블록별: 실측 자수(개행·면책 제외) vs 상한/목표선 + 자가표기 괴리 + 분모 드리프트
    # IG 하한 550(지침 목표선 600에서 완충 — 600이면 최근 17건 중 10건 경고 = 늑대소년·검증9 실측 → 550이면 4건).
    for name, lo, hi, hard, denom_std in (("자유요약", 850, 1000, None, None),
                                          ("IG", 550, 800, None, 800),
                                          ("Thread", 370, 430, 500, 430)):
        b = _blk(body, name)
        if b is None:
            infos.append("[{}] 코드블록 미검출 — 골격(### [{} …] + ```text) 확인".format(name, name))
            continue
        n = _clen(b)
        claim, denom = _claim(body, name)
        if hi and n > hi:
            warns.append("[{}] 실측 {}자 > 상한 {}자 (자가표기 {})".format(name, n, hi, claim if claim is not None else "없음"))
        elif lo and n < lo:
            infos.append("[{}] 실측 {}자 < 완충 하한 {}자 = 과소 활용 의심 (자가표기 {})".format(name, n, lo, claim if claim is not None else "없음"))
        if hard and _clen_hard(b) > hard:   # 플랫폼 하드 상한 = 개행 포함 실카운트로 판정(검증5)
            warns.append("[{}] ⛔ 개행 포함 {}자 > 플랫폼 하드 {} — 게시 시 잘림 위험".format(name, _clen_hard(b), hard))
        if claim is not None and abs(claim - n) >= 60:
            infos.append("[{}] 자가표기 {} vs 실측 {} = 괴리 {:+d}자".format(name, claim, n, n - claim))
        if denom_std and denom and denom != denom_std:
            infos.append("[{}] 분모 표기 {} ≠ 현행 상한 {} (구버전 상한 드리프트)".format(name, denom, denom_std))
        if name == "IG" and "🔎" not in b:
            infos.append("[IG] 🔎 리드 마커 없음(골격 누락)")
        if name == "자유요약" and "⚡" in b:
            warns.append("[자유요약] 코드블록 안에 ⚡ 출처 혼입(⚡는 IG·Thread 전용 — 복사 시 딸려 나감)")

    # # 제목 = IG 헤드 역가드(원문·번역 복붙 + 매체 태그) — title_ko(외신 번역)와도 대조(검증5)
    if h1:
        if re.search(r"\[(속보|단독|긴급|종합)\]", h1):
            warns.append("[# 제목] [속보]/[단독] 류 매체 태그 잔존 — IG 헤드 규칙(새로 짓기) 위반")
        # ⚠️ 대조는 선두 토픽 이모지·공백을 무시한 키로 한다(260813 실사고 봉합) — 구판은 원문자 완전일치라
        #    본문 헤드가 「# 🐟 …」처럼 이모지로 열리면(= IG 헤드 골격의 정상 형태) 같은 문장인데도 매번 빠져나갔다.
        #    실측 = 260811~13 위반 11건 전건 미검출(경고 0건) = 이 축이 실질적으로 죽어 있었다.
        #    술어 = 뷰어 _tkey(viewer/index.html 4949행)·build-viewer stripLeadEmoji 와 같은 자
        #    (화면이 「같은 제목」이라 판정하는 기준과 어긋나면 게이트와 증상이 갈린다).
        _k = lambda s: re.sub(r"\s+", "", re.sub(r"^\s*(?:[\U0001F000-\U0001FAFF←-⇿⌀-➿⬀-⯿]️?\s*)+", "", s or ""))
        if (title and _k(h1) == _k(title)) or (title_ko and _k(h1) == _k(title_ko)):
            # 라이브 결과를 그대로 적는다 = 다음 세션이 코드를 거슬러 올라가지 않고 증상을 안다:
            # 뷰어는 원문 제목 줄(.md-srct)을 「title ≠ H1」일 때만 그리므로, 같아지는 순간 기자가 뽑은
            # 직설 제목이 화면에서 사라지고 추상 헤드만 남는다(운영자 260813 「요약 상자 제목만 보면 내용을 모름」).
            warns.append("[# 제목] frontmatter title{}과 동일(선두 이모지 무시) = title 원문 보존 위반 — 뷰어 원문 제목 줄(.md-srct)이 통째로 안 그려진다".format("_ko" if (title_ko and _k(h1) == _k(title_ko)) else ""))

    # 헤드 짝 검출 2축(260817 운영자 「기사 타이틀처럼 후킹이 있으면서도 내용을 총망라 — 너무 추상적이어도 안 된다」 · 비차단):
    # ① 앵커 0 의심 = 헤드가 기자 제목(title/title_ko)과 겹치는 낱말도 숫자도 없다 = 헤드만 읽어서는 누구/무엇의
    #    일인지 모를 공산 — 01_지침 [헤드가 무너지는 두 증상] ⓐ 추상 축의 짝. 휴리스틱(다른 말로 쓴 실명 앵커는 못 알아본다)이라 INFO.
    #    기자 제목에 한글 토큰이 0이면(외신 영문 제목) 판정 유보 = 오탐 차단.
    # ② Thread 헤드 문단형 = 첫 줄 안에 완결 종결 문장 경계('다. ')가 있다 = 본문 문단이 헤드 자리를 차지
    #    (실측 260817 = 80~107자 두세 문장 헤드 실물) — 01_지침 [Thread 헤드] 「한 줄 문장 하나」의 짝.
    _ref_toks = re.findall(r"[가-힣]{2,}", " ".join(x for x in (title, title_ko) if x))
    def _anchor0(head):
        if not (head and _ref_toks):
            return False
        ht = re.findall(r"[가-힣A-Za-z0-9]{2,}", head)
        return not (re.search(r"\d", head) or any(a in b or b in a for a in ht for b in _ref_toks))
    if _anchor0(h1):
        infos.append("[# 제목] 추상 헤드 의심 — 기자 제목과 겹치는 낱말·숫자 0(01_지침 [헤드가 무너지는 두 증상] ⓐ 추상 축)")
    _th_b = _blk(body, "Thread")
    if _th_b:
        _th_head = _th_b.strip().split("\n", 1)[0].strip()
        if re.search(r"다\.\s+\S", _th_head):
            infos.append("[Thread] 헤드 자리에 문단({}자·문장 경계 포함) — [Thread 헤드] 한 줄 계약 위반".format(len(_th_head)))
        elif _anchor0(_th_head):
            infos.append("[Thread] 헤드 추상 의심 — 기자 제목과 겹치는 낱말·숫자 0")

    base = os.path.basename(path)
    if warns or infos:
        print("DIGEST_LINT {} ⚠️{}건 ℹ️{}건 — {}".format("⚠️" if warns else "ℹ️", len(warns), len(infos), base))
        for w in warns:
            print("  ⚠️ " + w)
        for i in infos:
            print("  ℹ️ " + i)
    else:
        print("DIGEST_LINT ✅ 규격·자수 통과 — " + base)
    return 0   # 비차단(경고 전용) — 하드 차단은 오탐 시 파이프라인을 세우므로 안 함(운영자 승인 전)

# ── 분량 가드(SUMMARY_LEN_GUARD · 260705 · 기본 OFF 카나리아) ─────────────────────────────
# 왜: #1552(effort max→high) 후 IG 630→540자·Thread 415→347자 급감(자유요약 무손상 = 압축 단계만 부실 ·
#     진단 = docs/작업이력.md 260705). 보강 임계 = 지침 목표선 하단(IG 600·Thread 390) — lint 완충 550과
#     별개 축(lint = 경고 소음 억제·guard = 재작성 발동, 값 다름 = 의도). 결빈약(자유요약<800) = 면제(지침
#     "짧음의 근거 = 원문 결 부족" 존중). 호출 = shared/summary_repair.sh (ask.sh·analyze.sh 공용).
REPAIR_IG_LO, REPAIR_TH_LO, REPAIR_FREE_MIN = 600, 370, 800
REPAIR_IG_HI, REPAIR_TH_HI = 800, 430        # 상한(01_지침) — 초과도 교정 대상(260810)

def repair_check(path):
    """보강 필요 판정 — 'REPAIR ig=N thread=N free=N' 또는 'OK …'/'SKIP …' 1줄. 항상 exit 0(fail-soft)."""
    raw = open(path, encoding="utf-8").read()
    fmm = re.search(r"^---\s*$(.*?)^---\s*$", raw, re.M | re.S)
    body = raw[fmm.end():] if fmm else raw
    vals = {}
    for n in ("자유요약", "IG", "Thread"):
        b = _blk(body, n)
        if b is None:
            print("SKIP {} 블록 미검출".format(n)); return 0
        vals[n] = _clen(b)
    if vals["자유요약"] < REPAIR_FREE_MIN:
        print("OK 결빈약 면제 ig={} thread={} free={}".format(vals["IG"], vals["Thread"], vals["자유요약"])); return 0
    under = vals["IG"] < REPAIR_IG_LO or vals["Thread"] < REPAIR_TH_LO
    # ⚠️ 초과 축(260810 신설) — 구판은 **미달만** 봤다. 그래서 상한 초과에는 자동 교정 경로가
    #   아예 없었고, 260810 3세대 실측에서 Thread 500자(개행 포함 510)가 그대로 나갔다 =
    #   플랫폼 하드 500 초과 = **게시 시 잘림**. 「짧으면 고치고 길면 방치」는 반쪽 가드다.
    over = vals["IG"] > REPAIR_IG_HI or vals["Thread"] > REPAIR_TH_HI
    tag = "REPAIR over" if over else ("REPAIR under" if under else "OK")
    print("{} ig={} thread={} free={}".format(tag, vals["IG"], vals["Thread"], vals["자유요약"]))
    return 0

def _nums(s):
    return set(re.findall(r"\d{2,}", s.replace(",", "")))   # 2자리+ 숫자 토큰(쉼표 정규화 — '5,000'='5000')

def splice(path, cand_path):
    """보강 후보의 IG/Thread 코드블록 '내용'만 검증 후 원본에 이식(헤더·📊 줄·frontmatter 불변 ·
    헤더 자수 라벨은 실측으로 갱신). 블록별 독립 판정 — 검증 실패 블록 = 원본 유지(fail-soft·항상 exit 0).
    후보 펜스는 ```text·``` 둘 다 허용(평의회4 — 언어태그 누락 변동성 흡수 · 원본은 항상 ```text라 무영향).
    Thread 상한·분모 = 현행 430(v1.19.2 정본) — 구 /500·/450 표기 파일도 보강 성공 시 /430로 정규화(lint 드리프트 교정과 동방향)."""
    raw = open(path, encoding="utf-8").read()
    raw_orig = raw
    cand = open(cand_path, encoding="utf-8").read()
    src_nums = _nums(raw_orig)   # 날조 경량 가드 기준 = 원본 다이제스트 전체(frontmatter·자유요약 포함)
    results = []
    for name, hi, hard, lo in (("IG", 800, None, REPAIR_IG_LO), ("Thread", 430, 500, REPAIR_TH_LO)):
        pat = re.compile(r"(^###\s*\[" + name + r"[^\]]*\]\s*\n+```(?:text)?\n)(.*?)(\n```)", re.M | re.S)
        mc, mt = pat.search(cand), pat.search(raw)
        if not mc or not mt:
            results.append("{}: 블록 미검출(후보 {}·원본 {}) — 유지".format(name, bool(mc), bool(mt))); continue
        new, old = mc.group(2), mt.group(2)
        n_new, n_old = _clen(new), _clen(old)
        why = []
        # 방향 인지 검증(260817) — 구판은 '증가 아님' 단조 검증뿐이라 REPAIR over(260810 신설)가 잘라낸
        #   결과를 전건 기각했다 = 상한 초과 교정이 구조적으로 착지 불가(over 보강이 돌아도 원본 유지 ·
        #   실측 최근 120건 Thread 상한 초과 38%가 그 사각의 증상). 원본이 상한 초과면 '줄어들었는가'로,
        #   그 외엔 종전대로 '늘었는가'로 판정. 과절단 하한 = 보강 발동 하한(REPAIR_*_LO)과 한 값.
        if n_old > hi:
            if n_new >= n_old: why.append("감소 아님 {}→{}".format(n_old, n_new))
            elif n_new < lo: why.append("과절단 {} < 하한 {}".format(n_new, lo))
        elif n_new <= n_old: why.append("증가 아님 {}→{}".format(n_old, n_new))
        if n_new > hi: why.append("상한 {} 초과({})".format(hi, n_new))
        if hard and _clen_hard(new) > hard: why.append("개행 포함 {} > 플랫폼 하드 {}".format(_clen_hard(new), hard))
        if name == "IG" and "🔎" not in new: why.append("🔎 리드 누락")
        if "⚡" not in new and "ⓔ" not in new: why.append("⚡/ⓔ 출처 줄 누락")
        if bool(_DISCLAIMER.search(old)) != bool(_DISCLAIMER.search(new)): why.append("면책 줄 유무 불일치(소실/무단 삽입)")   # 대칭 검증(평의회2 — 역방향 무단 삽입도 차단)
        ofl, nfl = old.strip().split("\n", 1)[0].strip(), new.strip().split("\n", 1)[0].strip()
        if ofl != nfl: why.append("제목 줄 변경")   # 헤드 원문 보존 강제(평의회2·4)
        fab = sorted(x for x in (_nums(new) - _nums(old)) if x not in src_nums)
        if fab: why.append("원본에 없는 숫자 도입({})".format("·".join(fab[:3])))   # 날조 경량 가드(평의회4 — 오탐=원본 유지라 안전)
        if why:
            results.append("{}: 검증 실패({}) — 유지".format(name, " · ".join(why))); continue
        raw = raw[:mt.start(2)] + new + raw[mt.end(2):]
        raw = re.sub(r"^###\s*\[" + name + r"[^\]]*\]", "### [{} — {}/{}자]".format(name, n_new, hi), raw, count=1, flags=re.M)
        results.append("{}: {}→{}자 보강".format(name, n_old, n_new))
    if raw != raw_orig:   # 원자적 쓰기 + 무변경 시 무접촉(평의회2 — truncate 창 제거)
        tmp = path + ".tmp"
        open(tmp, "w", encoding="utf-8").write(raw)
        os.replace(tmp, path)
    print("SPLICE " + " · ".join(results))
    return 0

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용: digest_guard.py [--repair-check|--splice <후보>] <queue/xxx.md>"); sys.exit(0)
    try:
        if sys.argv[1] == "--derive" and len(sys.argv) >= 3:
            sys.exit(derive_check(sys.argv[2]))
        if sys.argv[1] == "--repair-check" and len(sys.argv) >= 3:
            sys.exit(repair_check(sys.argv[2]))
        if sys.argv[1] == "--splice" and len(sys.argv) >= 4:
            sys.exit(splice(sys.argv[2], sys.argv[3]))
        sys.exit(lint(sys.argv[1]))
    except Exception as e:   # 린트·가드 자체 오류가 분석 파이프라인을 깨지 않게(fail-soft)
        print("DIGEST_LINT ⚠️ 실행 실패(무시): {}".format(e)); sys.exit(0)
