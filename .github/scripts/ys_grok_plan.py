#!/usr/bin/env python3
"""유튜브 숏폼(ys) 그록 연출 — 장면별 클립 안 비트(초·motion·camera) 입력 조립·산출 검문·대체안.
(운영자 260929 «예전 비디오 제작 방식이 완성도가 있다 · 절충» · «컷을 길게 가고 컷 안에서 여러 신»)

  ys_grok_plan.py prompt <plan.json> <timing.json> <meta.json> <ratio>  → stdout = 지침 뒤에 붙일 [영상]·[주인공]·[장면] 블록
  ys_grok_plan.py parse  <raw.txt> <plan.json> <timing.json> <out.json>  → out.json {src, clips:[{i, beats:[{sec, motion, camera}]}], dropped}

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

MAX_BEATS = 4
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


def metaphor(plan, sc):
    """주인공이 있는 영상의 「주인공 없음」 장면 = 은유 장면(ys-make.md · 얼굴 없는 사물·풍경). 주인공 없는 영상은 사람이 나올 수 있다."""
    return bool((plan.get('hero') or {}).get('en')) and not sc.get('hero')


def nobody(plan, sc, mv):
    """은유 장면 = 비트마다 「빈 화면」 명시(보드에 사람이 있으면 모델이 기본으로 넣는다 · 예전 콘티 MOTION ⓑ = 부정문 금지의 유일한 예외)."""
    return mv if not metaphor(plan, sc) or 'no people' in mv.lower() else mv.rstrip('. ') + '. ' + NOBODY


def fallback(plan, timing, i):
    """대본 motion 비트 1개 — 카메라는 비운다(대본 motion 에 이미 카메라 무브 1개가 들어 있다 · 덧붙이면 밀기+빼기 충돌)."""
    sc = plan['scenes'][i]
    mv = clean(sc.get('motion'), 220) or 'Slow push-in; subtle ambient motion.'
    return [{'sec': target(timing, i), 'motion': nobody(plan, sc, mv), 'camera': ''}]


def fit(beats, total):
    """초 합 = 클립 길이 — 비율로 늘리고 줄인 뒤 끝 비트로 나머지를 맞춘다(비트 수 ≤ 초/2 = 비트당 ~2초 이상)."""
    beats = beats[:max(1, min(MAX_BEATS, total // 2))]
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
            if metaphor(plan, plan['scenes'][i]) and re.search(r'(?i)\bprotagonist\b', mv):   # 은유 장면엔 인물 참조가 안 실린다 → 정의 없는 사람이 나온다
                drop.append((i, '은유 장면에 주인공 등장'))
                continue
            if len(cam.split()) < CAM_MIN_WORDS:   # 미달 = 기록만(감독 문장을 그대로 둔다 · 예전 콘티 sb_qa 와 같은 태도) · 비면 기본 1줄
                drop.append((i, f'카메라 {len(cam.split())}낱말(<{CAM_MIN_WORDS})'))
                cam = cam or DEFAULT_CAM
            beats.append({'sec': sec, 'motion': nobody(plan, plan['scenes'][i], mv), 'camera': cam})
        if not beats:
            drop.append((i, '비트 없음'))
            continue
        got[i] = fit(beats, target(timing, i))
    return got, drop


def extract(raw):
    m = re.search(r'```[ \t]*(?:json)?\s*(\{[\s\S]*?)(?:```|\Z)', raw, re.I)
    for cand in ([m.group(1)] if m else []):
        try:
            obj = json.loads(cand.strip())
        except ValueError:
            continue
        if isinstance(obj, dict) and isinstance(obj.get('clips'), list):
            return obj
    dec = json.JSONDecoder()
    for mm in re.finditer(r'\{', raw):
        try:
            obj, _ = dec.raw_decode(raw, mm.start())
        except ValueError:
            continue
        if isinstance(obj, dict) and isinstance(obj.get('clips'), list):
            return obj
    return None


def build(raw, plan, timing):
    """감독 산출(없으면 빈 문자열) → 전 장면 비트(빠진 장면 = 대체안)."""
    j = extract(raw or '') if raw else None
    got, drop = normalize(j or {}, plan, timing)
    clips = []
    for i in range(len(plan['scenes'])):
        clips.append({'i': i, 'beats': got.get(i) or fallback(plan, timing, i), 'src': 'director' if i in got else 'fallback'})
    src = 'director' if got else 'fallback'
    return {'src': src, 'clips': clips, 'dropped': [{'i': i, 'why': w} for i, w in drop]}


def prompt_block(plan, timing, meta, ratio):
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
    for i, sc in enumerate(plan['scenes']):
        t = timing['scenes'][i] if i < len(timing.get('scenes') or []) else {}
        beats = '; '.join(f"{a:.1f}~{z:.1f}s 「{s}」" for a, z, s in (t.get('sents') or []))
        who = ('나옴' if sc.get('hero') else '없음(은유 장면 · 사람 없이)') if hero else '해당 없음'
        out.append(f"- i={i} · 초 {target(timing, i)} · 주인공: {who} · 문장 박자: {beats or sc.get('vo', '')}\n"
                   f"  그림: {clean(sc.get('img'), 200)} · 움직임 힌트: {clean(sc.get('motion'), 160)}")
    return '\n'.join(out)


def main(argv):
    if len(argv) >= 6 and argv[1] == 'prompt':
        plan, timing, meta = (json.load(open(p, encoding='utf-8')) for p in argv[2:5])
        print(prompt_block(plan, timing, meta, argv[5]))
        return 0
    if len(argv) >= 6 and argv[1] == 'parse':
        try:
            raw = open(argv[2], encoding='utf-8', errors='replace').read()
        except OSError:
            raw = ''
        plan, timing = (json.load(open(p, encoding='utf-8')) for p in argv[3:5])
        doc = build(raw, plan, timing)
        with open(argv[5], 'w', encoding='utf-8') as f:
            json.dump(doc, f, ensure_ascii=False)
        k = sum(1 for c in doc['clips'] if c['src'] == 'director')
        print(f"그록 연출: 감독 {k}/{len(doc['clips'])}장면 · 비트 {sum(len(c['beats']) for c in doc['clips'])}개 · 버림 {len(doc['dropped'])}")
        return 0 if k else 1
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == '__main__':   # seal-ok: 단독 CLI(prompt·parse) — ys_grok 이 build 를 라이브러리로도 부른다
    sys.exit(main(sys.argv))
