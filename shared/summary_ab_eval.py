#!/usr/bin/env python3
"""summary_ab_eval.py — 요약 A/B 산출 기계 판정기(로컬 · 러너 산출 docs/reports/ab/<id> 를 읽는다 · 260905 평의회2 루브릭)

  사용: python3 shared/summary_ab_eval.py docs/reports/ab/<id>   → 같은 폴더에 eval.json · EVAL.md · judge/<art>_<pair>.md(심사 패킷)

  판정 3층 중 ①(기계·하드)·①′(기계·비교) 를 여기서 낸다. 도구(digest_guard·fact_guard)는 전부 exit 0 이라 함수 import 로 판정.
  H(하드) = B 각 런 개별 통과 · C(비교) = arm 최악값 대조(반복 2 는 평균을 못 낸다) · I = 정보.
  ⚠ 날조 후보(F1~F3)는 「후보」다 — 확정은 사람/심사자가 원문 대조로(기계는 열거만).
"""
import glob, json, os, re, statistics, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'shared'))
sys.path.insert(0, os.path.join(ROOT, 'apps', 'news'))
import digest_guard as dg   # noqa: E402
import fact_guard as fg     # noqa: E402

SECTIONS = ['## 🧷', '## 📰 Fact', '## 🔎 Inference', '## 🧭', '## 🛠', '## 📦 콘텐츠 초안', '### 💡 이 기사의 시사점']
FM_REQ = ['reader', 'emotion', 'hook', 'thumb_scene', 'thumb_dispatch', 'bias', 'tags']
LEAD_RE = re.compile(r'^\s*(?:\d+월\s*\d+일|\d+일\s|\d+시\s|지난\s*\d+|간밤|어젯밤|오늘\s*(?:새벽|오전|오후))')
GLOSS_RE = re.compile(r'(?:는|은)\s*[^.]{0,40}?(?:하는|되는)\s*(?:제도|절차|조치|단계|경보령|규정)(?:다|이다)|을 뜻한다|를 말한다|이란\s')
PREACH_RE = re.compile(r'(?:해야 한다|필요한 시점이다|묻고 있다|과제로 남았다|숙제다)\.?\s*$')
NOMINAL_RE = re.compile(r'(중|함|것|기|음|예정)\s*$')
XLATE_RE = re.compile(r'에 의해|되어진|결론적으로|시사하는 바가 크다|주목할 만하다|할 때입니다|에 있어|와 관련하여|에 기반하여')
CITE_RE = re.compile(r'\([^()]{1,12}(?:일보|신문|뉴스|경제|방송|통신|TV|NEWS|KBS|MBC|SBS|JTBC|YTN|연합|뉴시스|뉴스1)\)')


def fm_of(t):
    """frontmatter 파싱 — 첫 '---' 줄과 다음 '---' 줄 사이 · 값 안의 '#'(태그·연출 코드)은 주석이 아니다"""
    lines = t.split('\n')
    if not lines or lines[0].strip() != '---':
        return {}, t
    fm, i = {}, 1
    while i < len(lines) and lines[i].strip() != '---':
        m = re.match(r'^([a-z_]+):\s*(.*)$', lines[i])
        if m:
            v = m.group(2).strip()
            if v.startswith('"'):
                j = v.rfind('"')
                v = v[1:j] if j > 0 else v[1:]
            fm[m.group(1)] = v
        i += 1
    return fm, '\n'.join(lines[i + 1:])


def sec(body, head, nxt='\n## '):
    i = body.find(head)
    if i < 0:
        return ''
    j = body.find(nxt, i + len(head))
    return body[i:j if j > 0 else None]


def sentences(txt):
    out = []
    for ln in txt.split('\n'):
        ln = ln.strip()
        if not ln or ln.startswith(('⚡', 'ⓔ', '⚠️', '###', '#')):
            continue
        ln = re.sub(r'^[📍🔎\s]+', '', ln)
        out += [s.strip() for s in re.split(r'(?<=[.!?])\s+', ln) if s.strip()]
    return out


def h1_of(body):
    m = re.search(r'^# (.+)$', body, re.M)
    return m.group(1).strip() if m else ''


def eval_run(path, src_body):
    t = open(path, encoding='utf-8').read()
    fm, body = fm_of(t)
    free, ig, th = dg._blk(body, '자유요약'), dg._blk(body, 'IG'), dg._blk(body, 'Thread')
    fact = sec(body, '## 📰 Fact')
    insight = body.split('### 💡 이 기사의 시사점', 1)[1] if '### 💡 이 기사의 시사점' in body else ''
    draft = '\n'.join(x or '' for x in (free, ig, th)) + '\n' + insight
    allow = (src_body or '') + '\n' + fact
    r = {'file': os.path.basename(path)}
    # ── S 골격 ──
    r['S1_sections'] = sum(1 for s in SECTIONS if s in body)
    r['S2_blocks'] = int(bool(free)) + int(bool(ig)) + int(bool(th))
    r['S3_fm_missing'] = [k for k in FM_REQ if not fm.get(k)]
    r['S3_gver'] = fm.get('guidelines_version', '')
    h1 = h1_of(body)
    r['S4_title_eq_h1'] = (h1.strip() == fm.get('title', '').strip()) if h1 else None
    r['S5_lightning'] = [len(re.findall(r'^[⚡ⓔ] ', x or '', re.M)) for x in (free, ig, th)]
    r['S6_disclaimer'] = [bool(dg._DISCLAIMER.search(x or '')) for x in (ig, th)]
    r['S7_gauge_lines'] = len(re.findall(r'^📊 편향', body, re.M))
    # ── F 사실 무결성(후보 열거) ──
    try:
        r['F1_num_candidates'] = fg.check(allow, draft)
        r['F2_quote_candidates'] = fg.quote_check(allow, draft)
        r['F3_agency'] = fg.agency_check(allow, draft)
    except Exception as e:  # noqa
        r['F_err'] = str(e)
    # derive(소속 소실·무주어 개문·자유요약에 없는 수치)
    try:
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            dg.derive_check(path)
        r['F6_derive'] = [ln.strip() for ln in buf.getvalue().split('\n') if ln.strip().startswith('·')]
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            dg.lint(path)
        r['lint'] = [ln.strip() for ln in buf.getvalue().split('\n') if ln.strip().startswith(('⚠️', 'ℹ️'))]
    except Exception as e:  # noqa
        r['derive_err'] = str(e)
    # ── P 초점 ──
    title_toks = [w for w in re.findall(r'[가-힣]{2,4}', fm.get('title', ''))]
    lead_ig = (ig or '').split('\n')[1] if ig and len(ig.split('\n')) > 1 else ''
    r['P2_title_tok_in_ig_lead'] = any(w in (ig or '') for w in title_toks[:6]) if title_toks else None
    r['P1_abstract_head'] = any('추상' in ln for ln in r.get('lint', []))
    # ── L 분량·골격 ──
    r['L_len'] = {'free': dg._clen(free or ''), 'ig': dg._clen(ig or ''), 'th': dg._clen(th or ''), 'th_hard': len((th or '').strip())}
    r['L_pins'] = {'ig': (ig or '').count('📍'), 'th': (th or '').count('📍'), 'ig_lead': (ig or '').count('🔎')}
    # 하드 = 미달(과소 활용 = 지침이 실패로 규정) · Thread 개행포함 500 초과(게시 잘림). 상한 초과는 라이브 A 도 흔해 비교 축(아래 C)으로.
    r['L1_free_ok'] = r['L_len']['free'] >= 850 or (r['L_len']['free'] < 800 and len(src_body or '') < 1500)
    r['L2_ig_ok'] = r['L_len']['ig'] >= 600
    r['L3_th_ok'] = r['L_len']['th'] >= 370 and r['L_len']['th_hard'] <= 500
    r['L_over'] = {'free': max(0, r['L_len']['free'] - 1000), 'ig': max(0, r['L_len']['ig'] - 800), 'th': max(0, r['L_len']['th'] - 430)}
    r['L4_pins_ok'] = 4 <= r['L_pins']['ig'] <= 6 and 3 <= r['L_pins']['th'] <= 5
    # ── W 문체 ──
    sents = sentences('\n'.join(x or '' for x in (free, ig, th)))
    r['W1_nominal_end'] = [s for s in sents if NOMINAL_RE.search(s) and not re.search(r'다\.?$', s)][:5]
    last_bits = []
    for x in (ig, th):
        pins = [ln for ln in (x or '').split('\n') if ln.strip().startswith('📍')]
        if pins:
            last_bits.append(pins[-1])
    ins_s = sentences(insight)
    if ins_s:
        last_bits.append(ins_s[-1])
    r['W2_preach'] = [b for b in last_bits if PREACH_RE.search(b.strip())]
    r['W3_anira'] = bool(ins_s and re.search(r'가 아니라 .{1,25}(다|이다)\.?\s*$', ins_s[-1]))
    r['W4_date_lead'] = bool(LEAD_RE.search(lead_ig.replace('🔎', '').strip()))
    r['W5_gloss'] = len(GLOSS_RE.findall(ig or ''))
    r['W8_xlate'] = len(XLATE_RE.findall(draft))
    r['W_cite_brackets'] = len(CITE_RE.findall('\n'.join(x or '' for x in (free, ig, th))))
    # ── R 풍부도 ──
    r['R1_fact_bullets'] = len(re.findall(r'^\s*-\s', fact, re.M))
    try:
        r['R2_aug_nums'] = len(fg.check(src_body or '', fact)) if src_body else None
        r['R5_factcov_missing'] = len(fg.coverage(fact, free or ''))
        r['R4_free_num_density'] = len({raw for _, raw, _ in fg.tokens(free or '')}) if hasattr(fg, 'tokens') else None
    except Exception as e:  # noqa
        r['R_err'] = str(e)
    m = re.search(r'^-\s*\**출처\**[:：]\s*(.*)$', fact, re.M)
    r['R3_media'] = len([x for x in re.split(r'[·,/]|\s등', m.group(1)) if x.strip()]) if m else 0
    r['image_sources_n'] = len(fm.get('image_sources', '').split()) if fm.get('image_sources') else 0
    r['url'] = fm.get('url', '')
    r['bias'] = fm.get('bias', '')
    r['tags'] = fm.get('tags', '')
    r['title'] = fm.get('title', '')
    r['h1'] = h1
    # ── H 판정 ──
    hard = []
    if r['S1_sections'] < 7: hard.append('S1 섹션 %d/7' % r['S1_sections'])
    if r['S2_blocks'] < 3: hard.append('S2 코드블록 %d/3' % r['S2_blocks'])
    if r['S3_fm_missing']: hard.append('S3 FM 결측 %s' % r['S3_fm_missing'])
    if r['S4_title_eq_h1']: hard.append('S4 title==H1')
    if r['S5_lightning'] != [0, 1, 1]: hard.append('S5 ⚡ 줄 %s' % r['S5_lightning'])
    if r['S7_gauge_lines'] != 3: hard.append('S7 📊 %d' % r['S7_gauge_lines'])
    if r.get('F3_agency'): hard.append('F3 대리 %s' % r['F3_agency'][:2])
    if any('소속' in x or '무주어' in x or '직함' in x for x in r.get('F6_derive', [])): hard.append('F6 파생 %s' % [x for x in r['F6_derive'] if '수치' not in x][:2])
    if not r['L1_free_ok']: hard.append('L1 자유요약 미달 %d' % r['L_len']['free'])
    if not r['L2_ig_ok']: hard.append('L2 IG 미달 %d' % r['L_len']['ig'])
    if not r['L3_th_ok']: hard.append('L3 Thread 미달/하드 %d(hard %d)' % (r['L_len']['th'], r['L_len']['th_hard']))
    if not r['L4_pins_ok']: hard.append('L4 📍 %s' % r['L_pins'])
    if r['W1_nominal_end']: hard.append('W1 체언종결 %s' % r['W1_nominal_end'][:2])
    if r['W2_preach']: hard.append('W2 훈계착지 %s' % r['W2_preach'][:1])
    if r['W3_anira']: hard.append('W3 아니라 대구')
    if r['W_cite_brackets']: hard.append('W 괄호 매체표기 %d' % r['W_cite_brackets'])
    r['HARD_FAILS'] = hard
    return r


def usage_of(path):
    rows = []
    if os.path.exists(path):
        for ln in open(path, encoding='utf-8'):
            ln = ln.strip()
            if ln:
                try: rows.append(json.loads(ln))
                except Exception: pass
    main = [x for x in rows if x.get('src') == 'analyze']
    rep = [x for x in rows if x.get('src') == 'analyze-repair']
    m = main[-1] if main else {}
    turns = m.get('turns') or 0
    return {
        'dur_s': round((m.get('dur_ms') or 0) / 1000), 'turns': turns, 'in': m.get('in', 0), 'out': m.get('out', 0),
        'cache_r': m.get('cache_r', 0), 'cache_w': m.get('cache_w', 0), 'cost': m.get('cost', 0), 'rc': m.get('rc'),
        'prefix_per_turn': round(((m.get('cache_r', 0) or 0) + (m.get('cache_w', 0) or 0)) / turns) if turns else None,
        'repair_calls': len(rep), 'repair_cost': round(sum(x.get('cost', 0) or 0 for x in rep), 2),
        'repair_dur_s': round(sum(x.get('dur_ms', 0) or 0 for x in rep) / 1000), 'main_calls': len(main),
    }


def judge_packet(art_dir, runs):
    """심사 패킷 = FM 제거(title 만) · 자수 라벨·📊 줄 제거 · 실측 자수 표기(평의회2 ②)"""
    outdir = os.path.join(art_dir, 'judge'); os.makedirs(outdir, exist_ok=True)
    def strip(path):
        t = open(path, encoding='utf-8').read(); fm, body = fm_of(t)
        body = re.sub(r'^### \[(자유요약|IG|Thread)[^\]]*\]', lambda m: '### [%s]' % m.group(1), body, flags=re.M)
        body = re.sub(r'^📊 편향.*$', '', body, flags=re.M)
        keep = []
        for head in ('## 📦 콘텐츠 초안',):
            i = body.find(head); keep.append(body[i:] if i >= 0 else body)
        h1 = h1_of(body)
        lens = {n: dg._clen(dg._blk(body, n) or '') for n in ('자유요약', 'IG', 'Thread')}
        return '원문 제목: %s\n헤드: %s\n실측 자수: 자유요약 %d(목표 850~1000) · IG %d(600~780 · 상한 800) · Thread %d(370~420 · 상한 430)\n\n%s' % (
            fm.get('title', ''), h1, lens['자유요약'], lens['IG'], lens['Thread'], keep[0].strip())
    for tag, path in runs.items():
        open(os.path.join(outdir, tag + '.txt'), 'w', encoding='utf-8').write(strip(path))


def main(d):
    out = {'ab_dir': d, 'articles': []}
    md = ['# 요약 A/B 기계 판정 — %s' % os.path.basename(d.rstrip('/')), '']
    for art_dir in sorted(glob.glob(os.path.join(d, 'art*'))):
        art = os.path.basename(art_dir)
        info = json.load(open(os.path.join(art_dir, 'article.json'), encoding='utf-8')) if os.path.exists(os.path.join(art_dir, 'article.json')) else {}
        src = open(os.path.join(art_dir, 'src_body.txt'), encoding='utf-8').read() if os.path.exists(os.path.join(art_dir, 'src_body.txt')) else ''
        runs = {}
        for md_path in sorted(glob.glob(os.path.join(art_dir, '[ABS][0-9]*.md'))):
            tag = os.path.basename(md_path)[:-3]
            r = eval_run(md_path, src)
            r['usage'] = usage_of(os.path.join(art_dir, tag + '.usage.jsonl'))
            meta = os.path.join(art_dir, tag + '.meta.json')
            r['meta'] = json.load(open(meta, encoding='utf-8')) if os.path.exists(meta) else {}
            log = os.path.join(art_dir, tag + '.log')
            if os.path.exists(log):
                lt = open(log, encoding='utf-8', errors='ignore').read()
                r['repair_fired'] = bool(re.search(r'분량 가드: REPAIR', lt))
                r['pre_repair'] = (re.search(r'REPAIR \w+ ig=(\d+) thread=(\d+)', lt) or [None])
                r['pre_repair'] = {'ig': int(r['pre_repair'].group(1)), 'th': int(r['pre_repair'].group(2))} if r['pre_repair'] else None
                r['gver_log'] = (re.search(r'지침 버전\(summary\): (\w+)', lt) or [None, ''])[1]
                r['account_events'] = len(re.findall(r'🔄|🩺', lt))
            runs[tag] = r
        failed = {os.path.basename(p)[:-11]: open(p, encoding='utf-8', errors='ignore').read()[:400] for p in glob.glob(os.path.join(art_dir, '*.failed.log'))}
        # 비교(C): arm 별 최악값
        def arm(tag): return tag[0]
        groups = {}
        for tag, r in runs.items():
            groups.setdefault(arm(tag), []).append(r)
        comp = {}
        def worst(a, key, fn=min, default=None):
            vals = [fn2 for fn2 in (key(r) for r in groups.get(a, [])) if fn2 is not None]
            return fn(vals) if vals else default
        for a in groups:
            comp[a] = {
                'n': len(groups[a]),
                'fact_bullets_min': worst(a, lambda r: r['R1_fact_bullets']),
                'aug_nums_min': worst(a, lambda r: r.get('R2_aug_nums')),
                'media_min': worst(a, lambda r: r['R3_media']),
                'free_num_density_min': worst(a, lambda r: r.get('R4_free_num_density')),
                'factcov_missing_max': worst(a, lambda r: r.get('R5_factcov_missing'), max),
                'xlate_max': worst(a, lambda r: r['W8_xlate'], max),
                'gloss_max': worst(a, lambda r: r['W5_gloss'], max),
                'date_lead_any': any(r['W4_date_lead'] for r in groups[a]),
                'pre_repair_ig_min': worst(a, lambda r: (r.get('pre_repair') or {}).get('ig')),
                'pre_repair_th_min': worst(a, lambda r: (r.get('pre_repair') or {}).get('th')),
                'turns_min': worst(a, lambda r: r['usage']['turns']),
                'hard_fails': sum(1 for r in groups[a] if r['HARD_FAILS']),
                'num_candidates_max': worst(a, lambda r: len(r.get('F1_num_candidates', [])), max),
                'over_max': worst(a, lambda r: max(r['L_over'].values()), max),
                'quote_candidates_max': worst(a, lambda r: len(r.get('F2_quote_candidates', [])), max),
                'dur_med': statistics.median([r['usage']['dur_s'] for r in groups[a]]) if groups[a] else None,
                'prefix_per_turn_med': statistics.median([r['usage']['prefix_per_turn'] or 0 for r in groups[a]]) if groups[a] else None,
                'cache_w_med': statistics.median([r['usage']['cache_w'] or 0 for r in groups[a]]) if groups[a] else None,
                'cache_r_med': statistics.median([r['usage']['cache_r'] or 0 for r in groups[a]]) if groups[a] else None,
                'out_med': statistics.median([r['usage']['out'] or 0 for r in groups[a]]) if groups[a] else None,
                'cost_med': statistics.median([r['usage']['cost'] or 0 for r in groups[a]]) if groups[a] else None,
                'elapsed_med': statistics.median([r['meta'].get('elapsed_s', 0) for r in groups[a]]) if groups[a] else None,
            }
        cflags = []
        A, B = comp.get('A'), comp.get('B')
        if A and B:
            def chk(cond, msg):
                if cond: cflags.append(msg)
            chk(B['hard_fails'] > 0, 'H 하드 실패 B %d런' % B['hard_fails'])
            chk((B['fact_bullets_min'] or 0) < (A['fact_bullets_min'] or 0) - 1, 'R1 Fact 불릿 B%s < A%s−1' % (B['fact_bullets_min'], A['fact_bullets_min']))
            chk(A['aug_nums_min'] is not None and A['aug_nums_min'] >= 2 and (B['aug_nums_min'] or 0) < 1, 'R2 보강 수치 B%s(A%s)' % (B['aug_nums_min'], A['aug_nums_min']))
            chk((B['media_min'] or 0) < (A['media_min'] or 0) - 1, 'R3 교차매체 B%s < A%s−1' % (B['media_min'], A['media_min']))
            chk(A['free_num_density_min'] and (B['free_num_density_min'] or 0) < 0.8 * A['free_num_density_min'], 'R4 수치밀도 B%s < 0.8·A%s' % (B['free_num_density_min'], A['free_num_density_min']))
            chk((B['factcov_missing_max'] or 0) > (A['factcov_missing_max'] or 0) + 1, 'R5 factcov 누락 B%s > A%s+1' % (B['factcov_missing_max'], A['factcov_missing_max']))
            chk((B['xlate_max'] or 0) > (A['xlate_max'] or 0) + 1, 'W8 번역투 B%s > A%s+1' % (B['xlate_max'], A['xlate_max']))
            chk((B['gloss_max'] or 0) > (A['gloss_max'] or 0), 'W5 용어풀이 B%s > A%s' % (B['gloss_max'], A['gloss_max']))
            chk(B['date_lead_any'] and not A['date_lead_any'], 'W4 날짜 리드 B 만')
            chk(A['pre_repair_ig_min'] and B['pre_repair_ig_min'] and B['pre_repair_ig_min'] < A['pre_repair_ig_min'] - 40, 'L5 재보강 전 IG B%s < A%s−40' % (B['pre_repair_ig_min'], A['pre_repair_ig_min']))
            chk((B['over_max'] or 0) > (A['over_max'] or 0) + 60, 'L 상한 초과 B%s > A%s+60' % (B['over_max'], A['over_max']))
            chk((B['turns_min'] or 0) <= 2 and (A['turns_min'] or 0) >= 4, 'turns B%s ≤2 ∧ A%s ≥4 = 도구 미사용 의심' % (B['turns_min'], A['turns_min']))
            chk((B['num_candidates_max'] or 0) > (A['num_candidates_max'] or 0) + 1, 'F1 수치 후보 B%s > A%s+1(사람 확정 필요)' % (B['num_candidates_max'], A['num_candidates_max']))
        judge_packet(art_dir, {tag: os.path.join(art_dir, tag + '.md') for tag in runs})
        out['articles'].append({'art': art, 'info': info, 'runs': runs, 'compare': comp, 'C_flags': cflags, 'failed': failed})
        # ── 마크다운 ──
        md += ['## %s — %s' % (art, info.get('title', '')), '', '- URL: %s · 본문 %sB · 패턴 %s' % (info.get('url'), info.get('body_bytes'), info.get('pattern')), '']
        md += ['| run | arm | rc | 벽시계 s | 본선 dur s | turns | out tok | cache_w | cache_r | prefix/turn | cost $ | repair | 자유요약/IG/TH | 📍 IG/TH | Fact불릿 | 보강수치 | 매체 | 하드실패 |', '|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|']
        for tag, r in runs.items():
            u = r['usage']; L = r['L_len']; P = r['L_pins']
            md.append('| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %d/%d/%d | %d/%d | %d | %s | %d | %s |' % (
                tag, tag[0], r['meta'].get('rc'), r['meta'].get('elapsed_s'), u['dur_s'], u['turns'], u['out'], u['cache_w'], u['cache_r'], u['prefix_per_turn'], u['cost'],
                ('%d콜 %ss $%s' % (u['repair_calls'], u['repair_dur_s'], u['repair_cost'])) if u['repair_calls'] else '—',
                L['free'], L['ig'], L['th'], P['ig'], P['th'], r['R1_fact_bullets'], r.get('R2_aug_nums'), r['R3_media'], ' · '.join(r['HARD_FAILS']) or '0'))
        md += ['', '**arm 요약(중앙값 · 최악값)**', '', '| arm | n | 본선 dur | 벽시계 | prefix/turn | cache_w | cache_r | out | cost | 하드실패 런 | Fact불릿 min | 보강수치 min | 매체 min | 수치밀도 min | 번역투 max | 재보강전 IG/TH min |', '|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|']
        for a, c in comp.items():
            md.append('| %s | %d | %s | %s | %s | %s | %s | %s | %s | %d | %s | %s | %s | %s | %s | %s/%s |' % (
                a, c['n'], c['dur_med'], c['elapsed_med'], c['prefix_per_turn_med'], c['cache_w_med'], c['cache_r_med'], c['out_med'], c['cost_med'], c['hard_fails'],
                c['fact_bullets_min'], c['aug_nums_min'], c['media_min'], c['free_num_density_min'], c['xlate_max'], c['pre_repair_ig_min'], c['pre_repair_th_min']))
        md += ['', '**C 비교 플래그**: %s' % (' · '.join(cflags) if cflags else '없음'), '']
        for tag, r in runs.items():
            if r['HARD_FAILS'] or r.get('F1_num_candidates') or r.get('F2_quote_candidates') or r.get('F6_derive') or r.get('lint'):
                md += ['<details><summary>%s 상세</summary>' % tag, '']
                if r['HARD_FAILS']: md.append('- 하드: %s' % r['HARD_FAILS'])
                if r.get('F1_num_candidates'): md.append('- 수치 후보(원문+Fact 밖 · 사람 확정): %s' % r['F1_num_candidates'][:8])
                if r.get('F2_quote_candidates'): md.append('- 인용 후보: %s' % r['F2_quote_candidates'][:4])
                if r.get('F6_derive'): md.append('- derive: %s' % r['F6_derive'][:5])
                if r.get('lint'): md.append('- lint: %s' % r['lint'][:6])
                md += ['', '</details>', '']
        if failed:
            md += ['**실패 런**: %s' % list(failed), '']
    json.dump(out, open(os.path.join(d, 'eval.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    open(os.path.join(d, 'EVAL.md'), 'w', encoding='utf-8').write('\n'.join(md))
    print('\n'.join(md))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'docs/reports/ab')
