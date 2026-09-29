#!/usr/bin/env python3
"""유튜브 숏폼(ys) 그록 연출 — 장면별 클립 안 비트(초·motion·camera) 입력 조립·산출 검문·대체안.
(운영자 260929 «예전 비디오 제작 방식이 완성도가 있다 · 절충» · «컷을 길게 가고 컷 안에서 여러 신»
 · «라이브러리는 도서관 · 색인으로 구상 → 고른 것만 참조 · 그게 효과적이라고 판단하는 감독 알고리즘이 중요»)

감독 = 2콜: ① 구상(prompts/ys-grok-pick.md) = [연출 색인]만 보고 비트를 나누고 비트마다 기법 번호 + 이유
            ② 쓰기(prompts/ys-grok.md) = [감독 구상] + 고른 번호의 도서관 원문(ys_lib.fetch)만 보고 motion·camera 문장
  ys_grok_plan.py pick-prompt <plan.json> <timing.json> <meta.json> <ratio>     → stdout = 구상 콜 입력([영상]·[주인공]·[장면] + [연출 색인])
  ys_grok_plan.py pick-parse  <raw.txt> <plan.json> <timing.json> <pick.json>   → pick.json {src, scenes:[{i, role, emotion, cd, beats:[{sec, ids, why}]}], lib}
  ys_grok_plan.py prompt <plan.json> <timing.json> <meta.json> <ratio> [pick.json] → stdout = 쓰기 콜 입력([장면] + [감독 구상] + [고른 번호 원문] · 구상 없음 = [연출 색인])
  ys_grok_plan.py parse  <raw.txt> <plan.json> <timing.json> <out.json> [pick.json] → out.json {src, clips:[{i, beats:[{sec, motion, camera, ids}]}], dropped, pick_src, lib}

예전 콘티 레인(grok_sb_video.vid_prompt)의 문법을 옮긴다: 한 클립 안 비트 = 시각표(`0-3s: …`) · 비트마다 MOTION + CAMERA(4요소).
검문 = 신뢰 불가 산출 → 영문 인쇄 문자만 · 길이 상한 · 비주얼 부정문 제거 · 초 합 = 클립 길이.
감독 콜이 죽거나 장면이 깨지면 그 장면은 대본의 motion 으로 비트 1개(대체안 = fallback) — 그록 발사는 멈추지 않는다.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ys_grok import seconds_for  # noqa: E402
import ys_lib  # noqa: E402  연출 도서관(색인 · 원문 꺼내기 · 번호 감사)
from ys_plan import empty_frame  # noqa: E402  빈 화면 판정 단일 원천(피사체 · 사람 없는 상황 · 옛 판 = 주인공 없는 장면)

MAX_BEATS = 4
FETCH_CAP = 90   # 쓰기 콜 원문 상한(번호 ≈ 440B · 90개 ≈ 40KB) — 넘치면 원문 블록에 생략 표시 + lib.fetch_cut 기록
CAM_MIN_WORDS = 9          # 예전 콘티 실측 하한(sb_qa CAM_MIN_WORDS 와 같은 값) — 미달 = 경고만(버리지 않는다)
# 비주얼 부정문 = 그록 정본(prompts/grok-make.md)이 금지 — 부정어가 그 대상을 부른다
#   부정어 **바로 뒤 명사구만** 지운다(「no longer hides the letters」·「without a word」 같은 멀쩡한 동작은 살린다 · 평의회 260929 재현)
NEG_RE = re.compile(r'(?i)[,;]?\s*\b(?:no|without(?:\s+any)?|avoid(?:ing)?)\s+(?:(?:visible|on-screen|onscreen|readable|burned-in)\s+)?'
                    r'(?:text|captions?|subtitles?|logos?|lettering|watermarks?|typography)\b(?:\s+(?:on\s+screen|anywhere|in\s+frame))?')
DEFAULT_CAM = 'medium shot at eye-level, 35mm lens, deep focus, slow push-in'   # 감독이 카메라를 비웠을 때만(조명·인물 무관 1줄 · 평의회 260929)
NOBODY = 'No people in frame.'


def clean(s, cap):
    s = str(s or '').translate({0x2019: "'", 0x2018: "'", 0x201c: ' ', 0x201d: ' ', 0x2014: ', ', 0x2013: '-'})
    s = re.sub(r"[^A-Za-z0-9 ,.;:()'/-]+", ' ', s)
    s = re.sub(r'\s+([,.;:])', r'\1', re.sub(r'\s+', ' ', NEG_RE.sub('', s))).strip(' ,;').lstrip('. ')
    if len(s) > cap:   # 낱말 경계에서 자른다(꼬리 문구가 반 토막 나지 않게)
        s = s[:cap].rsplit(' ', 1)[0]
    return s.strip(' ,;')


def target(timing, i):
    t = timing['scenes'][i] if i < len(timing.get('scenes') or []) else {}
    return seconds_for(t.get('dur'))


def absent(plan, sc):
    """주인공이 있는 영상의 「주인공 없음」 장면 — 이 장면 비트에 주인공이 나오면 안 된다(인물 참조가 안 실린다 = 정의 없는 사람)."""
    return bool((plan.get('hero') or {}).get('en')) and not sc.get('hero')


def metaphor(plan, sc):
    """빈 화면 장면(피사체 · 사람 없는 상황 · 옛 판 은유 장면) — ys_plan.empty_frame 단일 원천."""
    return empty_frame(plan, sc)


def nobody(plan, sc, mv):
    """빈 화면 장면 = 비트마다 「빈 화면」 명시(보드에 사람이 있으면 모델이 기본으로 넣는다 · 예전 콘티 MOTION ⓑ = 부정문 금지의 유일한 예외)."""
    return mv if not metaphor(plan, sc) or 'no people' in mv.lower() else mv.rstrip('. ') + '. ' + NOBODY


def fallback(plan, timing, i):
    """대본 motion 비트 1개 — 카메라는 비운다(대본 motion 에 이미 카메라 무브 1개가 들어 있다 · 덧붙이면 밀기+빼기 충돌)."""
    sc = plan['scenes'][i]
    mv = clean(sc.get('motion'), 220) or 'Slow push-in; subtle ambient motion.'
    return [{'sec': target(timing, i), 'motion': nobody(plan, sc, mv), 'camera': ''}]


def fit(beats, total):
    """초 합 = 클립 길이 — 비율로 늘리고 줄인 뒤 끝 비트로 나머지를 맞춘다(비트 수 ≤ 초/2 = 비트당 ~2초 이상)."""
    n = max(1, min(MAX_BEATS, total // 2))
    if len(beats) > n:   # 넘치는 비트 = 가운데를 버리고 끝 비트는 남긴다(마지막 장면의 여운 비트가 사라지지 않게 · 평의회 260929)
        beats = beats[:n - 1] + [beats[-1]] if n >= 2 else beats[:1]
    s = sum(b['sec'] for b in beats)
    if s != total:
        for b in beats:
            b['sec'] = max(1, round(b['sec'] * total / s))
        while sum(b['sec'] for b in beats) > total and any(b['sec'] > 1 for b in beats):
            max(beats, key=lambda b: b['sec'])['sec'] -= 1
        beats[-1]['sec'] += total - sum(b['sec'] for b in beats)
    return beats


def normalize(j, plan, timing):
    """검문 → {i: beats} · 버린 사유 목록. 계약 위반 장면은 대체안(fallback)으로."""
    n = len(plan['scenes'])
    got, drop = {}, []
    clips = j.get('clips') if isinstance(j, dict) else None
    for c in (clips if isinstance(clips, list) else [])[:40]:
        if not isinstance(c, dict):
            continue
        try:
            i = int(c.get('i'))
        except (TypeError, ValueError):
            continue
        if not 0 <= i < n or i in got:
            continue
        beats, raw_beats = [], c.get('beats')
        for b in (raw_beats if isinstance(raw_beats, list) else [])[:MAX_BEATS]:
            if not isinstance(b, dict):
                continue
            try:
                sec = max(1, min(15, int(round(float(b.get('sec'))))))
            except (TypeError, ValueError, OverflowError):
                continue
            mv, cam = clean(b.get('motion'), 220), clean(b.get('camera'), 200)
            if len(mv) < 8:
                continue
            if absent(plan, plan['scenes'][i]) and re.search(r'(?i)\bprotagonist\b', mv):   # 주인공 없는 장면엔 인물 참조가 안 실린다 → 정의 없는 사람이 나온다
                drop.append((i, '주인공 없는 장면에 주인공 등장'))
                continue
            if len(cam.split()) < CAM_MIN_WORDS:   # 미달 = 기록만(감독 문장을 그대로 둔다 · 예전 콘티 sb_qa 와 같은 태도) · 비면 기본 1줄
                drop.append((i, f'카메라 {len(cam.split())}낱말(<{CAM_MIN_WORDS})'))
                cam = cam or DEFAULT_CAM
            ids, bad = ys_lib.audit(b.get('ids'), 'director')
            beats.append({'sec': sec, 'motion': nobody(plan, plan['scenes'][i], mv), 'camera': cam, 'ids': ids})
            if bad:
                drop.append((i, '색인 밖 번호 ' + ','.join(bad[:4])))   # 지어낸 번호 = 기록만(비트는 쓴다 · 번호는 버린다)
        if not beats:
            drop.append((i, '비트 없음'))
            continue
        got[i] = fit(beats, target(timing, i))
    return got, drop


def extract(raw):
    return extract_key(raw, 'clips')


def extract_key(raw, key):
    """산출에서 key(list)를 가진 첫 JSON 객체 — 코드펜스 우선 · 없으면 raw_decode 훑기."""
    m = re.search(r'```[ \t]*(?:json)?\s*(\{[\s\S]*?)(?:```|\Z)', raw, re.I)
    for cand in ([m.group(1)] if m else []):
        try:
            obj = json.loads(cand.strip())
        except ValueError:
            continue
        if isinstance(obj, dict) and isinstance(obj.get(key), list):
            return obj
    dec = json.JSONDecoder()
    for mm in re.finditer(r'\{', raw):
        try:
            obj, _ = dec.raw_decode(raw, mm.start())
        except ValueError:
            continue
        if isinstance(obj, dict) and isinstance(obj.get(key), list):
            return obj
    return None


def build(raw, plan, timing, pick=None):
    """감독 산출(없으면 빈 문자열) → 전 장면 비트(빠진 장면 = 대체안) + 구상 성패·번호 감사."""
    j = extract(raw or '') if raw else None
    got, drop = normalize(j or {}, plan, timing)
    clips = []
    for i in range(len(plan['scenes'])):
        clips.append({'i': i, 'beats': got.get(i) or fallback(plan, timing, i), 'src': 'director' if i in got else 'fallback'})
    src = 'director' if got else 'fallback'
    cited = sum(len(b.get('ids') or []) for c in clips for b in c['beats'])
    made_up = sum(1 for _i, w in drop if w.startswith('색인 밖 번호'))
    doc = {'src': src, 'clips': clips, 'dropped': [{'i': i, 'why': w} for i, w in drop],
           'lib': {'cited': cited, 'made_up_beats': made_up}}
    if pick:
        doc['pick_src'] = pick.get('src', 'none')
        doc['lib']['picked'] = (pick.get('lib') or {}).get('cited', 0)
        doc['lib']['fetch_cut'] = max(0, len([x for x in pick_ids(pick) if x in ys_lib.offered('director')]) - FETCH_CAP)
        doc['pick'] = [{'i': sc['i'], 'role': sc.get('role', ''), 'emotion': sc.get('emotion', ''), 'cd': sc.get('cd', ''),
                        'beats': [{'sec': b['sec'], 'ids': b['ids'], 'why': b.get('why', '')} for b in sc['beats']]}
                       for sc in pick.get('scenes') or []]
    return doc


def _why(s, cap=80):
    """구상 이유 = 한국어 한 줄(쓰기 콜에 그대로 간다 · 신뢰 불가 산출) → 제어 문자·코드펜스·줄바꿈 제거 · 길이 상한."""
    s = re.sub(r'[\x00-\x1f`<>{}\[\]]+', ' ', str(s or ''))
    return re.sub(r'\s+', ' ', s).strip()[:cap]


def parse_pick(raw, plan, timing):
    """구상 산출 → {src, scenes:[{i, role, emotion, cd, beats:[{sec, ids, why}]}], lib} (없음·깨짐 = src none · 쓰기 콜이 색인으로 대신한다)."""
    j = extract_key(raw or '', 'scenes') if raw else None
    n, out, bad = len(plan['scenes']), [], 0
    seen = set()
    for sc in (j.get('scenes') if isinstance(j, dict) and isinstance(j.get('scenes'), list) else [])[:40]:
        if not isinstance(sc, dict):
            continue
        try:
            i = int(sc.get('i'))
        except (TypeError, ValueError):
            continue
        if not 0 <= i < n or i in seen:
            continue
        beats = []
        for b in (sc.get('beats') if isinstance(sc.get('beats'), list) else [])[:MAX_BEATS]:
            if not isinstance(b, dict):
                continue
            try:
                sec = max(1, min(15, int(round(float(b.get('sec'))))))
            except (TypeError, ValueError, OverflowError):
                continue
            ids, made_up = ys_lib.audit(b.get('ids'), 'director')
            bad += len(made_up)
            if ids:
                beats.append({'sec': sec, 'ids': ids, 'why': _why(b.get('why'))})
        if not beats:
            continue
        seen.add(i)
        cd = str(sc.get('cd') or '').strip()
        out.append({'i': i, 'role': _why(sc.get('role'), 12), 'emotion': _why(sc.get('emotion'), 16),
                    'cd': cd if cd.startswith('CD-') and cd in ys_lib.offered('director') else '', 'beats': fit(beats, target(timing, i))})
    out.sort(key=lambda x: x['i'])
    return {'src': 'director' if out else 'none', 'scenes': out,
            'lib': {'cited': sum(len(b['ids']) for sc in out for b in sc['beats']), 'made_up': bad}}


def pick_ids(pick):
    got = []
    for sc in (pick or {}).get('scenes') or []:
        for x in [sc.get('cd')] + [y for b in sc['beats'] for y in b['ids']]:
            if x and x not in got:
                got.append(x)
    return got


def prompt_block(plan, timing, meta, ratio):
    """[영상]·[주인공]·[자막 띠]·[장면] — 구상 콜·쓰기 콜 공통(장면 유형·주인공·화면 사람·대본 번호 · 문장 박자)."""
    import os
    hero = (plan.get('hero') or {}).get('en', '')
    try:
        cap = max(10, min(90, int(os.environ.get('YS_CAP') or 65)))
    except ValueError:
        cap = 65
    out = [f"[영상] 제목: {meta.get('title', '')} · 채널: {meta.get('channel', '')} · 숏폼 제목: {plan.get('short_title') or plan.get('title', '')} · 화면 {ratio}",
           f"[주인공] {hero}" if hero else '[주인공] 없음(고정 주인공 없이 · 사람이 나오면 식별 특징으로 부른다)',
           f"[자막 띠] 화면 높이 {cap}% 부근(±8%)에 나레이션 자막이 얹힌다 — 얼굴·손·핵심 동작은 그 띠 밖에 두는 구도로",
           '[장면]']
    kname = {'person': '인물', 'subject': '피사체', 'situation': '상황'}
    for i, sc in enumerate(plan['scenes']):
        t = timing['scenes'][i] if i < len(timing.get('scenes') or []) else {}
        beats = '; '.join(f"{a:.1f}~{z:.1f}s 「{s}」" for a, z, s in (t.get('sents') or []))
        who = ('나옴' if sc.get('hero') else '없음(주인공 없이)') if hero else '해당 없음'
        room = '빈 화면(사람 없이)' if metaphor(plan, sc) else ('다른 사람' if not sc.get('hero') and sc.get('people') == 'others' else '')
        extra = (f" · 유형: {kname[sc['kind']]}" if sc.get('kind') in kname else '') + (f" · 화면: {room}" if room else '') \
            + (f" · 대본 번호: {' / '.join(ys_lib.names(sc['ids'], 'scene'))}" if sc.get('ids') else '')   # 번호 + 이름(감독 색인에 없는 서랍이라 뜻을 같이 건넨다)
        out.append(f"- i={i} · 초 {target(timing, i)} · 주인공: {who}{extra} · 문장 박자: {beats or sc.get('vo', '')}\n"
                   f"  그림: {clean(sc.get('img'), 200)} · 움직임 힌트: {clean(sc.get('motion'), 160)}")
    return '\n'.join(out)


def pick_prompt(plan, timing, meta, ratio):
    """구상 콜 입력 = 공통 블록 + [연출 색인](번호·이름·언제 효과적인지만)."""
    return prompt_block(plan, timing, meta, ratio) + '\n\n' + ys_lib.index('director')


def write_prompt(plan, timing, meta, ratio, pick=None):
    """쓰기 콜 입력 = 공통 블록 + [감독 구상] + 고른 번호의 도서관 원문(구상 없음 = [연출 색인]으로 스스로 고른다)."""
    out = [prompt_block(plan, timing, meta, ratio)]
    if pick and pick.get('scenes'):
        lines = ['[감독 구상] (비트 나누기·기법 번호·이유 — 이 번호의 방법은 아래 [고른 번호 원문])']
        for sc in pick['scenes']:
            lines.append(f"- i={sc['i']} · 역할 {sc.get('role', '')} · 정서 {sc.get('emotion', '')}" + (f" · 배정표 {sc['cd']}" if sc.get('cd') else ''))
            lines.extend(f"  · {b['sec']}초: {' '.join(b['ids'])} — {b.get('why', '')}" for b in sc['beats'])
        out.append('\n'.join(lines))
        raw = ys_lib.fetch(pick_ids(pick), 'director', cap=FETCH_CAP)
        out.append(raw or ys_lib.index('director'))   # 구상이 있으면 고른 번호 원문만(색인 없음 = 운영자 «그것만 참조해서 용량을 줄인다» · 번호는 구상이 정했다)
    else:
        out.append(ys_lib.index('director'))
    return '\n\n'.join(x for x in out if x)


def _load(path):
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def main(argv):
    if len(argv) >= 6 and argv[1] in ('prompt', 'pick-prompt'):
        plan, timing, meta = (json.load(open(p, encoding='utf-8')) for p in argv[2:5])
        if argv[1] == 'pick-prompt':
            print(pick_prompt(plan, timing, meta, argv[5]))
        else:
            print(write_prompt(plan, timing, meta, argv[5], _load(argv[6]) if len(argv) >= 7 else None))
        return 0
    if len(argv) >= 6 and argv[1] in ('parse', 'pick-parse'):
        try:
            raw = open(argv[2], encoding='utf-8', errors='replace').read()
        except OSError:
            raw = ''
        plan, timing = (json.load(open(p, encoding='utf-8')) for p in argv[3:5])
        if argv[1] == 'pick-parse':
            pk = parse_pick(raw, plan, timing)
            with open(argv[5], 'w', encoding='utf-8') as f:
                json.dump(pk, f, ensure_ascii=False)
            print(f"그록 감독 구상: {len(pk['scenes'])}/{len(plan['scenes'])}장면 · 비트 {sum(len(s['beats']) for s in pk['scenes'])}개 · "
                  f"번호 {pk['lib']['cited']}개 · 색인 밖 {pk['lib']['made_up']}")
            return 0 if pk['scenes'] else 1
        doc = build(raw, plan, timing, (_load(argv[6]) or {'src': 'none', 'scenes': []}) if len(argv) >= 7 else None)   # 구상 파일 없음 = 구상 실패로 기록
        with open(argv[5], 'w', encoding='utf-8') as f:
            json.dump(doc, f, ensure_ascii=False)
        k = sum(1 for c in doc['clips'] if c['src'] == 'director')
        print(f"그록 연출: 감독 {k}/{len(doc['clips'])}장면 · 비트 {sum(len(c['beats']) for c in doc['clips'])}개 · 버림 {len(doc['dropped'])} · "
              f"구상 {doc.get('pick_src', '-')} · 번호 {doc['lib']['cited']}")
        return 0 if k else 1
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == '__main__':   # seal-ok: 단독 CLI(prompt·parse) — ys_grok 이 build 를 라이브러리로도 부른다
    sys.exit(main(sys.argv))
