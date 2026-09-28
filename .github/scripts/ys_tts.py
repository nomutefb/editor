#!/usr/bin/env python3
"""유튜브 숏폼(ys) 나레이션 — 장면 vo → 문장 단위 합성 → 장면별 wav + 자막 타이밍.

  ys_tts.py <plan.json> <outdir> edge|eleven     → outdir/s{i}.wav · outdir/timing.json
  ys_tts.py --voices <out.json>                   → ElevenLabs 계정 목소리 목록(뷰어 선택지 · R2 ys_out/_voices.json)

문장마다 따로 합성해 길이를 재고 이어 붙인다 = 자막 타이밍이 엔진의 경계 이벤트에 의존하지 않는다
(edge 한국어는 WordBoundary 없음 = mg_tts 실측 · ElevenLabs 는 엔진이 달라도 같은 계약).
화면 자막 = 원문 문장(숫자 그대로) · 소리 = mg_tts.speakable(숫자·단위 한글 전개) — 문장 수는 둘이 같다(문장부호 보존).
eleven 실패(키 부재·쿼터·목소리 없음) = 장면 단위로 edge 자동 강하 + timing.json notes 에 사유 기록(무음 강하 금지).
"""
import asyncio
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mg_tts import speakable   # noqa: E402  숫자·단위 한글 전개 정본(모션그래픽 나레이션과 같은 규칙)

EDGE_VOICE = os.environ.get('YS_EDGE_VOICE', 'ko-KR-SunHiNeural')
EDGE_RATE = os.environ.get('YS_EDGE_RATE', '+10%')   # 숏폼 호흡(기본 속도 실측 4.4~5.4자/초 = 느림)
EL_MODEL = os.environ.get('YS_EL_MODEL', 'eleven_multilingual_v2')   # 한국어 지원(공식 모델 문서 · 260928 확인)
EL_VOICE = os.environ.get('YS_EL_VOICE', '').strip()
EL_KEY = (os.environ.get('ELEVENLABS_API_KEY') or '').strip()
GAP = 0.14   # 문장 사이 숨(초)
SENT_RE = re.compile(r'(?<=[.!?…。])\s+')


def sentences(text):
    return [s.strip() for s in SENT_RE.split(text.strip()) if s.strip()]


def probe(path):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(path)],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


async def _edge(text, path):
    import edge_tts
    proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy') or None
    c = edge_tts.Communicate(text, EDGE_VOICE, rate=EDGE_RATE, proxy=proxy)
    buf = bytearray()
    async for ch in c.stream():
        if ch['type'] == 'audio':
            buf += ch['data']
    if not buf:
        raise RuntimeError('edge 오디오 0바이트')
    Path(path).write_bytes(bytes(buf))


def _el_req(url, body=None):
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None,
                                 headers={'xi-api-key': EL_KEY, 'content-type': 'application/json', 'accept': '*/*'},
                                 method='POST' if body is not None else 'GET')
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read()


_voice_cache = {}


def el_voice():
    """목소리 = 레포 변수 YS_EL_VOICE(id) 우선 → 계정 목소리 중 한국어 남성 → 한국어 → 첫 목소리. 못 고르면 RuntimeError."""
    if EL_VOICE:
        if 'name' not in _voice_cache and EL_KEY:
            try:   # 이름은 표시용(결과 화면 「고른 목소리」) — 실패해도 합성은 id 로 진행
                _voice_cache['name'] = str(json.loads(_el_req(f'https://api.elevenlabs.io/v1/voices/{EL_VOICE}')).get('name', ''))
            except Exception:
                _voice_cache['name'] = ''
        return EL_VOICE
    if 'v' in _voice_cache:
        return _voice_cache['v']
    vs = json.loads(_el_req('https://api.elevenlabs.io/v1/voices')).get('voices') or []
    def kor(v):
        lab = json.dumps(v.get('labels') or {}, ensure_ascii=False).lower() + ' ' + str(v.get('name', '')).lower()
        return any(t in lab for t in ('korean', '"ko"', '한국')) or str(v.get('name', '')).startswith('KO ')
    def male(v):
        return str((v.get('labels') or {}).get('gender', '')).lower() == 'male'
    # 기본 = 한국어 남성(운영자 260928 «기본은 남성 · 영상 보고 AI가 바꿈» — AI가 못 고른 경우의 자리) → 한국어 → 첫 목소리
    pick = next((v for v in vs if kor(v) and male(v)), None) or next((v for v in vs if kor(v)), None) or (vs[0] if vs else None)
    if not pick:
        raise RuntimeError('ElevenLabs 계정에 목소리가 없음')
    _voice_cache['v'] = pick['voice_id']
    _voice_cache['name'] = str(pick.get('name', ''))
    print(f"ElevenLabs 목소리: {pick.get('name', '')} ({'한국어 표지' if kor(pick) else '첫 목소리 폴백'})")
    return pick['voice_id']


def _eleven(text, path):
    if not EL_KEY:
        raise RuntimeError('ELEVENLABS_API_KEY 없음')
    audio = _el_req(f'https://api.elevenlabs.io/v1/text-to-speech/{el_voice()}?output_format=mp3_44100_128',
                    {'text': text, 'model_id': EL_MODEL})
    if len(audio) < 512:
        raise RuntimeError('ElevenLabs 오디오 비정상')
    Path(path).write_bytes(audio)


def synth(text, path, engine):
    if engine == 'eleven':
        _eleven(text, path)
    else:
        asyncio.run(_edge(text, path))


def scene_audio(i, vo, outdir, engine):
    """장면 1개 = 문장별 합성 → GAP 무음으로 이어 붙인 wav + 문장 타이밍. 반환 (wav, [(a,z,원문)], 실제 엔진)."""
    sents = sentences(vo)
    parts, times, t, used = [], [], 0.0, engine
    for j, s in enumerate(sents):
        p = Path(outdir) / f's{i}_{j}.mp3'
        try:
            synth(speakable(s), p, used)
        except Exception as e:
            if used != 'eleven':
                raise
            print(f'::warning::ElevenLabs 합성 실패(장면 {i + 1}) — 무료 음성으로 강하: {str(e)[:120]}')
            used = 'edge'
            synth(speakable(s), p, used)
        d = probe(p)
        if d <= 0:
            raise RuntimeError(f'장면 {i + 1} 문장 {j + 1} 길이 0')
        times.append((round(t, 3), round(t + d, 3), s))
        parts.append(p)
        t += d + GAP
    wav = Path(outdir) / f's{i}.wav'
    args = ['ffmpeg', '-v', 'error', '-y']
    for p in parts:
        args += ['-i', str(p)]
    chain = ''.join(f'[{k}:a]aresample=44100,aformat=channel_layouts=mono,apad=pad_dur={GAP}[a{k}];' for k in range(len(parts)))
    chain += ''.join(f'[a{k}]' for k in range(len(parts))) + f'concat=n={len(parts)}:v=0:a=1[out]'
    subprocess.run(args + ['-filter_complex', chain, '-map', '[out]', '-ac', '1', '-ar', '44100', str(wav)], check=True)
    return wav, times, used


def dump_voices(path):
    """계정 목소리 목록 → 뷰어 목소리 선택지(운영자 260928 «음성 임의 선택») — 이름·id·표지·미리듣기만(키·설정 0)."""
    vs = json.loads(_el_req('https://api.elevenlabs.io/v1/voices')).get('voices') or []
    out = []
    for v in vs:
        lab = v.get('labels') or {}
        out.append({'id': v.get('voice_id', ''), 'name': str(v.get('name', ''))[:40], 'cat': v.get('category', ''),
                    'lang': str(lab.get('language') or lab.get('accent') or '')[:20], 'gender': str(lab.get('gender') or '')[:10],
                    'desc': str(lab.get('description') or lab.get('use_case') or lab.get('use case') or '')[:40],
                    'preview': v.get('preview_url') or ''})
    out = [o for o in out if re.fullmatch(r'[A-Za-z0-9]{16,32}', o['id'])]
    out.sort(key=lambda o: (0 if ('ko' in o['lang'].lower() or 'korean' in o['lang'].lower()) else 1, o['cat'] != 'cloned', o['name']))
    json.dump({'ts': int(__import__('time').time()), 'voices': out}, open(path, 'w', encoding='utf-8'), ensure_ascii=False)
    print(f'목소리 목록 {len(out)}개 → {path}')
    return 0


def main(argv):
    if len(argv) == 3 and argv[1] == '--voices':
        return dump_voices(argv[2])
    if len(argv) < 4:
        print(__doc__, file=sys.stderr)
        return 2
    plan = json.load(open(argv[1], encoding='utf-8'))
    outdir = Path(argv[2]); outdir.mkdir(parents=True, exist_ok=True)
    engine = 'eleven' if argv[3] == 'eleven' else 'edge'
    scenes, notes, used_all = [], [], set()
    n = len(plan['scenes'])
    for i, sc in enumerate(plan['scenes']):
        wav, times, used = scene_audio(i, sc['vo'], outdir, engine)
        used_all.add(used)
        scenes.append({'i': i, 'wav': str(wav), 'dur': round(probe(wav), 3), 'sents': times})
        if os.environ.get('YS_ID'):
            subprocess.run([sys.executable, str(Path(__file__).with_name('ys_progress.py')), os.environ['YS_ID'],
                            'voice', 'run', f'장면 {i + 1}/{n}', f'p={(i + 1) / n:.3f}'], check=False)
    if engine == 'eleven' and 'edge' in used_all:
        notes.append('고급 음성(ElevenLabs)이 일부 장면에서 실패해 무료 음성으로 대체했어.')
    doc = {'voice_id': (EL_VOICE or _voice_cache.get('v', '')) if 'eleven' in used_all else '',
           'voice_name': _voice_cache.get('name', '') if 'eleven' in used_all else ('무료 음성(' + EDGE_VOICE + ')'),
           'engine': 'eleven' if used_all == {'eleven'} else ('mixed' if len(used_all) > 1 else 'edge'),
           'scenes': scenes, 'total': round(sum(s['dur'] for s in scenes), 2), 'notes': notes}
    json.dump(doc, open(outdir / 'timing.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f"나레이션 {len(scenes)}장면 · {doc['total']}초 · 엔진 {doc['engine']}")
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
