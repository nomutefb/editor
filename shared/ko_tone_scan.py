#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ko_tone_scan.py — 한국어 결(AI 번역투·Sunny 7) 측정기 (정본 = shared/ko_tone_rules.md 규칙 ID 1:1 · 260908).

왜: 260908 감사에서 히트 수 기반 정규식(S1 '-적'·S3 '들'·S4 '것')의 사람 판정 정밀도가 7%/7%/0%로 실측됐다 —
  '누적·목적·국적'을 '-적'으로, '받아들이'를 '들'로, '~것으로 파악됐다'(보도 관용)를 '것'으로 셌다. 여기서는
  ⓐ 직접 인용 안을 마스킹하고 ⓑ 명사 사전·보도 관용·집단 주체 허용목록으로 거른 뒤 ⓒ 규칙(rule)과 관측(obs)을
  분리해 센다. 점수(--score)는 규칙 축만 더한 문서당 정수 — 임계 판정은 소비자 몫(A/B W9 · card_gate TONE ℹ️).
260908 리뷰 반영(queue 28건 실측: 점수의 ~80%가 정본이 '유지'로 적은 용례): 정본이 "연발·한 문장 3회+"로 적은 규칙은
  건당이 아니라 초과분만 센다 — S1(-적 한 문장 3회+ · 개념어 '법률·사·공' 추가) · H1(문두 접속사 연속 문장) ·
  I1(형식명사 종결 연속 + '라는 점에 있다') · G1(이중 완곡 건당 + 보인다/판단된다 2회째부터 · "~고 했다" 귀속 발화 제외).
  S4 는 보도 관용·분열문("중요한 것은 속도다")·인용 사고("~이라는 것")를 뺀다. 레인 = summary(기본) | card —
  카드는 윤문체(정본 [윤문 추가축])라 S2·S3·S6 도 규칙으로 더한다(rule_ids(lane)).
  ⚠ 여전히 근사 측정기다: 판정 근거로 쓸 땐 반드시 표본을 사람이 다시 본다(히트 수 단독 판정 금지).

사용:
  python3 shared/ko_tone_scan.py --score [--lane card] <queue.md|cards.md|.txt>   → 정수 1개(규칙 축 합)
  python3 shared/ko_tone_scan.py --json  [--lane card] <파일…>                     → 파일별 {id: count} JSON
  printf '%s' "$text" | python3 shared/ko_tone_scan.py --score -                    → stdin 텍스트
라이브러리: scan(text) → {id: count} · score(text, lane) → int · rule_ids(lane) · mask_quotes · strip_html_comments · lane_text(md).
"""
import json
import re
import sys

# ── 정규식 사전 ─────────────────────────────────────────────────────────────
# '-적' 접미가 아닌 명사(…적 = 단어 자체) — Sunny-1 오탐 차단(260908 실측: 누적·목적·국적·지적·실적).
JEOK_NOUN = ('누적', '목적', '국적', '지적', '실적', '표적', '추적', '흔적', '면적', '성적', '업적', '유적', '선적',
             '기적', '궤적', '필적', '족적', '행적', '이적', '사적지', '유적지', '문적', '적적', '만적', '피적')
# 개념·법률·제도 용어(Sunny-1 유지 조건) — 세지 않는다. '법률·사·공'(법률적·사적·공적)은 260908 리뷰 실측 추가.
JEOK_CONCEPT = ('법', '법률', '정치', '구체', '공식', '사회', '경제', '국제', '군사', '과학', '기술', '제도', '역사', '문화',
                '의학', '행정', '사법', '민사', '형사', '재정', '외교', '안보', '기본', '전국', '지역', '사', '공',
                '개인', '공공', '민간', '실질', '명목', '잠정', '한시', '영구', '독점', '배타', '일반', '표준')
# 집단 주체(요약 축 기사 관용) — S3 관측을 '기사 주체'와 '그 외'로 나눈다.
DEUL_SUBJECT = ('전문가', '관계자', '당국자', '의원', '주민', '시민', '피해자', '유족', '누리꾼', '경찰', '사람', '학생',
                '선수', '팬', '직원', '기자', '업체', '노동자', '근로자', '교사', '학부모', '환자', '이용자', '소비자',
                '투자자', '주주', '당사자', '가족', '아이', '어른', '청년', '노인', '여성', '남성', '군인', '병사')
DEUL_VERB_FALSE = ('받아들', '아들', '이들', '그들', '저들', '우리들', '너희들', '자네들', '만들', '들들', '흔들', '떠들',
                   '내들', '드들', '거들', '뒤들', '들이들')
# 보도 관용(Sunny-4 유지) — '~것으로 + 보도동사'
REPORT_VERB = r'(?:파악|알려|전해|보|집계|추정|확인|나타|분석|전망|관측|풀이|해석|평가|여겨|기록|조사)'

RULES = [   # (id, label, regex|None, kind)  kind = rule(전 레인 규칙) | card(카드 레인만 규칙 · 요약은 관측) | obs(관측)
    ('A1', '이중 피동·에 의해', re.compile(r'에 의해|되어진|되어졌|되어지'), 'rule'),
    ('A2', '~에 대해/와 관련/기반/통해', re.compile(r'에 대해(?:서)?(?=[ ,.]|$)|[와과] 관련(?:해|하여|된)|에 기반하여|[를을] 통해'), 'rule'),
    ('A3', '가지고 있다·이루어지다', re.compile(r'가지고 있|이루어지|이루어졌'), 'rule'),
    ('A4', '~할 수 있다(3회+부터)', re.compile(r'수 있다'), 'rule'),
    ('D1', 'AI 관용구', re.compile(r'결론적으로|시사하는 바|주목할 만|할 때입니다'), 'rule'),
    ('G1', '이중 완곡(건당) + 보인다/판단된다 2회째부터(귀속 발화 제외)', None, 'rule'),
    ('H1', '문두 접속사 연속 문장', None, 'rule'),
    ('I1', '형식명사 종결 연속 + 라는 점에 있다', None, 'rule'),
    ('F1', '정도부사(인용 밖)', re.compile(r'(?:^|\s)(?:매우|정말|굉장히|아주|너무나) '), 'rule'),
    ('S5', '완충 있는', re.compile(r'할 수 있는 [가-힣]+'), 'rule'),
    ('S7', '에(게) 있어', re.compile(r'[가-힣]+에(?:게)? 있어(?!서는 안)'), 'rule'),
    ('S1', '-적 한 문장 3회+ 초과분(명사·개념어 제외)', None, 'rule'),
    ('S4', '의존명사 것(보도 관용·분열문·인용 사고 제외)', re.compile(r'(?:하는|한|할|된|되는) 것(?:은|이|을|으로|도)(?=[\s,.]|$)'), 'rule'),
    ('R1', '종결어미 3연속', None, 'rule'),
    ('S2', '의 겹침', re.compile(r'[가-힣]+의 [가-힣]+의 [가-힣]+'), 'card'),
    ('S3', '들(기사 주체 제외)', re.compile(r'([가-힣]{2,5})들(?:은|이|을|의|에게|도|과|와|만|께)(?=[\s,.]|$)'), 'card'),
    ('S6', '있었다 패딩', re.compile(r'(?:발생|진행|변화|증가|감소|논의|검토|조사|발표|보도|충돌|사고|지연|중단)(?:이|가) 있었다'), 'card'),
    ('S1n', '-적 총 건수(허용목록 제외 · 관측)', None, 'obs'),
    ('S3n', '들(기사 주체 = 관용)', None, 'obs'),
    ('E2', '-고 있다', re.compile(r'고 있(?:다|었다|으며|고|는)'), 'obs'),
    ('C11', '연결어미 뒤 쉼표', re.compile(r'(?:고|며|면서|는데|지만|으나), '), 'obs'),
]
JEOK_RE = re.compile(r'([가-힣]{1,4})적(?:으로|인|이다|이며|이고|일|이었다)?(?=[\s,.!?·)]|$)')
CONJ_RE = re.compile(r'^(?:또한|따라서|즉|나아가|아울러|한편|그리고|그러나|하지만)[ ,]')
NOMEND_RE = re.compile(r'(?:것이다|다는 뜻이다|라는 의미다|필요가 있다)[.!?"”’)\s]*$')
POINT_RE = re.compile(r'라는 점에 있다')
HEDGE_RE = re.compile(r'(?:것으로 보인다|로 판단된다)(?!고 (?:했|말했|밝혔|전했|설명했|덧붙였|봤|본다))')
DOUBLE_HEDGE_RE = re.compile(r'가능성이 있을 수')
VERBISH_RE = re.compile(r'(?:한다|된다|있다|없다|했다|됐다|않는다|않았다|린다|난다|진다|겠다)\s*$')
QUOTE_RE = re.compile(r'[“"«][^”"»\n]{2,}[”"»]|‘[^’\n]{2,}’')
COMMENT_RE = re.compile(r'<!--[\s\S]*?-->')
FREE_RE = re.compile(r'###\s*\[자유요약[^\]]*\]\s*\n+```text\n([\s\S]*?)```')
IG_RE = re.compile(r'###\s*\[IG[^\]]*\]\s*\n+```text\n([\s\S]*?)```')
TH_RE = re.compile(r'###\s*\[Thread[^\]]*\]\s*\n+```text\n([\s\S]*?)```')
INSIGHT_RE = re.compile(r'###\s*💡[^\n]*\n([\s\S]*?)(?=\n###|\n##|\Z)')
CARD_TEXT_RE = re.compile(r'\*\*텍스트\*\*\s*\n+```[a-zA-Z]*\n([\s\S]*?)```')


def mask_quotes(text):
    """직접 인용 내부를 같은 길이의 공백으로 — 인용은 발언 원문이라 측정 대상이 아니다(260908 실측: 정도부사 12건 중 9건이 인용 안)."""
    return QUOTE_RE.sub(lambda m: ' ' * len(m.group(0)), text)


def strip_html_comments(text):
    """HTML 주석 제거 — 수정 지시 로그 같은 메타는 본문이 아니다(260908 리뷰: 시사점 꼬리로 섞이던 축)."""
    return COMMENT_RE.sub('', text)


def _drop_head(blk):
    """Thread 블록 첫 줄(헤드 = 라임 장치 · 정본 [기사체 상한선] 예외)은 측정 밖."""
    lines = blk.strip('\n').split('\n')
    return '\n'.join(lines[1:]) if len(lines) > 1 else ''


def lane_text(md):
    """측정 대상 본문 — queue 다이제스트면 자유요약+IG+Thread(헤드 제외)+시사점, cards.md면 카드 텍스트, 그 외 전문."""
    md = strip_html_comments(md)
    parts = []
    if '### [카드' in md and '**텍스트**' in md:
        parts = CARD_TEXT_RE.findall(md)
    else:
        for rx in (FREE_RE, IG_RE, TH_RE, INSIGHT_RE):
            m = rx.search(md)
            if m:
                parts.append(_drop_head(m.group(1)) if rx is TH_RE else m.group(1))
    return '\n'.join(p.strip() for p in parts) if parts else md


def _sentences(text):
    out = []
    for ln in text.split('\n'):
        ln = re.sub(r'^[📍🔎\s*]+', '', ln.strip())
        if not ln or ln.startswith(('⚡', 'ⓔ', '#', '📊')):
            continue
        out.extend(s.strip() for s in re.split(r'(?<=[.!?])\s+', ln) if s.strip())
    return out


def _endings_run(sents):
    """같은 2자 종결(어미)이 3문장 연속인 지점 수."""
    ends = [re.sub(r'[.!?"”’)\s*]+$', '', s)[-2:] for s in sents]
    run, n = 1, 0
    for a, b in zip(ends, ends[1:]):
        run = run + 1 if a and a == b else 1
        if run == 3:
            n += 1
    return n


def _jeok_hits(s):
    n = 0
    for m in JEOK_RE.finditer(s):
        stem = m.group(1)
        if (stem + '적') in JEOK_NOUN or any((stem + '적').endswith(x) for x in JEOK_NOUN if len(x) >= 2 and stem.endswith(x[:-1])):
            continue
        if stem in JEOK_CONCEPT:
            continue
        n += 1
    return n


def _is_cleft(rem):
    """'~것은/것이' 뒤가 명사 서술('속도다'·'차 모씨다'·'22일이었다')이면 분열문 = 정본 유지 조건."""
    rem = re.split(r'[.!?\n]', rem, 1)[0].strip()
    return bool(rem) and rem.endswith('다') and not VERBISH_RE.search(rem)


def _pairs(flags):
    return sum(1 for a, b in zip(flags, flags[1:]) if a and b)


def scan(text):
    """{규칙ID: count} — 인용 마스킹 후 측정. 규칙 축(rule·card)과 관측 축(obs)을 모두 낸다."""
    t = mask_quotes(text)
    sents = _sentences(t)
    out = {}
    for rid, _lab, rx, _kind in RULES:
        if rid == 'S1':
            per = [_jeok_hits(s) for s in sents]
            out['S1'] = sum(max(0, c - 2) for c in per)   # 한 문장 3회+ 초과분만(정본 Sunny-1)
            out['S1n'] = sum(per)
        elif rid == 'S3':
            n_other, n_subj = 0, 0
            for m in rx.finditer(t):
                stem = m.group(1)
                if any(stem.endswith(v) or stem == v for v in DEUL_VERB_FALSE):
                    continue
                if any(stem.endswith(s) for s in DEUL_SUBJECT):
                    n_subj += 1
                else:
                    n_other += 1
            out['S3'] = n_other
            out['S3n'] = n_subj
        elif rid == 'S4':
            n = 0
            for m in rx.finditer(t):
                tail = t[m.end():m.end() + 12]
                if m.group(0).endswith('으로') and re.match(r'\s*' + REPORT_VERB, tail):
                    continue                       # ~것으로 파악됐다 = 보도 관용
                if re.match(r'\s*\d', tail):
                    continue                       # 분열문 '것은 22일'
                if m.group(0).endswith(('것은', '것이')) and _is_cleft(t[m.end():]):
                    continue                       # 분열문 '중요한 것은 속도다'
                n += 1
            out['S4'] = n
        elif rid == 'G1':
            out['G1'] = len(DOUBLE_HEDGE_RE.findall(t)) + max(0, len(HEDGE_RE.findall(t)) - 1)
        elif rid == 'H1':
            out['H1'] = _pairs([bool(CONJ_RE.match(s)) for s in sents])
        elif rid == 'I1':
            out['I1'] = len(POINT_RE.findall(t)) + _pairs([bool(NOMEND_RE.search(s)) for s in sents])
        elif rid == 'R1':
            out['R1'] = _endings_run(sents)
        elif rx is None:
            continue                               # S1n·S3n 은 위에서 채웠다
        else:
            out[rid] = len(rx.findall(t))
    return out


def rule_ids(lane='summary'):
    """레인별 규칙 축 ID — summary = rule · card = rule + card(S2·S3·S6 = 카드는 윤문체)."""
    return tuple(rid for rid, _l, _rx, kind in RULES if kind == 'rule' or (lane == 'card' and kind == 'card'))


def score(text, lane='summary'):
    """규칙 축 합 — A4(수 있다)는 3회째부터, 나머지는 건당 1(연발 규칙은 scan 이 이미 초과분만 낸다)."""
    s = scan(text)
    total = 0
    for rid in rule_ids(lane):
        v = s.get(rid, 0)
        if rid == 'A4':
            v = max(0, v - 2)
        total += v
    return total


def report(text, lane='summary'):
    """(문자 수, scan dict, score) — JSON 출력용."""
    return {'chars': len(text), 'hits': scan(text), 'score': score(text, lane), 'lane': lane}


def _read(path):
    if path == '-':
        return sys.stdin.read()
    return open(path, encoding='utf-8', errors='replace').read()


def main(argv):
    lane = 'summary'
    if '--lane' in argv:
        i = argv.index('--lane')
        lane = argv[i + 1] if i + 1 < len(argv) else 'summary'
        argv = argv[:i] + argv[i + 2:]
    if len(argv) < 2 or argv[0] not in ('--score', '--json') or lane not in ('summary', 'card'):
        print(__doc__)
        return 2
    mode, files = argv[0], argv[1:]
    if mode == '--score':
        print(score(lane_text(_read(files[0])), lane))
        return 0
    out = {}
    for f in files:
        out[f] = report(lane_text(_read(f)), lane)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
