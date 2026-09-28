#!/usr/bin/env python3
"""유튜브 숏폼(ys) 장면 영상 — 그록(grok-imagine-video) 장면 1개 = 클립 1개(운영자 260928 «화면 구성 3방식 · 그록 = 9:16 전면»).

  ys_grok.py <id> <plan.json> <timing.json> <img_dir> <outdir> <ratio 9:16|16:9>
  → outdir/s{i}.mp4(소리 트랙 제거) + outdir/vid.json {used, total, note, cost_usd}

설계(260928 조사 · 15초×4 연장 체인 비채택 = 장면 경계와 어긋나고 순차라 느리고 이을수록 화질이 떨어진다):
  · 장면 경계 = 나레이션 문단 경계 → 장면마다 독립 클립 + 컷이 가장 자연스럽다.
  · 첫 프레임 = img_dir/s{i}.png(맥 GPT 세로 그림)이 있으면 고정(image) → 장면 사이 화풍이 같은 그림 엔진으로 묶인다.
    없으면(맥 꺼짐) 글→영상(비율 지정) — 화면에 강하 사유를 남긴다.
  · 길이 = 장면 나레이션 + 0.5초 올림(1~15초) · 모자라면 렌더가 1.15배 이내 늦춤 + 마지막 프레임 멈춤.
  · 3발 동시 · 실패 장면만 1회 재시도(실패 호출 = 청구 0) · 검열·자격 실패 = 재시도 안 함.
  · 자격 = shared/grok_api.fresh_token(회전형 리프레시 · 되쓰기 = 그 모듈 몫) · 워크플로가 nm-grok-key 줄에 세운다(콘티 레인과 같은 줄).
전 경로 rc 0 — 못 만든 장면은 렌더가 그림·모션 그래픽으로 채운다(영상은 항상 나온다 · 사유는 note 로 화면까지).
"""
import json
import math
import os
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'shared'))
PAD = 0.5
MAX_SEC = 15
PAR = int(os.environ.get('YS_GROK_PAR', '3'))
STYLE = os.environ.get('YS_VID_STYLE', 'cinematic minimal look, soft light, dark background, teal accent, no text, no captions, no logos')


def progress(id_, st, note='', p=None):
    a = [sys.executable, str(Path(__file__).with_name('ys_progress.py')), id_, 'vid', st, note]
    if p is not None:
        a.append(f'p={p:.3f}')
    subprocess.run(a, check=False)


def seconds_for(dur):
    return max(1, min(MAX_SEC, int(math.ceil(float(dur or 0) + PAD))))


def prompt_for(sc, has_image):
    motion = (sc.get('motion') or '').strip()
    if has_image:   # 첫 프레임이 구도·화풍을 이미 쥐었다 = 움직임만(구도 재서술은 그림과 싸운다)
        return f"{motion or 'Slow push-in; subtle ambient motion.'} {STYLE}"
    return f"{(sc.get('img') or sc.get('head') or '').strip()}. {motion} {STYLE}".strip()


def strip_audio(src, dst):
    """그록 자체 소리 = 버린다(나레이션·자막은 우리가 덮는다) · 영상 트랙은 재인코딩 없이."""
    r = subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', str(src), '-an', '-c:v', 'copy', str(dst)], capture_output=True, text=True)
    return r.returncode == 0 and Path(dst).exists() and Path(dst).stat().st_size > 10240


def main(argv):
    if len(argv) < 7:
        print(__doc__, file=sys.stderr)
        return 2
    id_, plan, timing = argv[1], json.load(open(argv[2], encoding='utf-8')), json.load(open(argv[3], encoding='utf-8'))
    img_dir, out, ratio = Path(argv[4]), Path(argv[5]), argv[6] if argv[6] in ('9:16', '16:9') else '9:16'
    out.mkdir(parents=True, exist_ok=True)
    scenes = plan['scenes']
    total = len(scenes)

    def done(used, note, cost=0.0):
        json.dump({'used': used, 'total': total, 'note': note, 'cost_usd': round(cost, 3)},
                  open(out / 'vid.json', 'w', encoding='utf-8'), ensure_ascii=False)
        print(f'장면 영상 {used}/{total} · {note}')
        return 0

    if not os.environ.get('XAI_REFRESH_TOKEN'):
        progress(id_, 'skip', '그록 자격 미등록')
        return done(0, '그록 자격(XAI_REFRESH_TOKEN)이 등록돼 있지 않아 그림·모션 그래픽으로 만들었어 — 관리자 설정이 필요해.')
    try:
        import grok_api
        tok = grok_api.fresh_token()
    except Exception as e:  # noqa: BLE001  자격 죽음 = 설정 문제(사람이 다시 로그인) · 외부 장애와 문구를 가른다
        why = str(e)[:120]
        progress(id_, 'skip', '그록 자격 실패')
        return done(0, f'그록 로그인이 풀려 그림·모션 그래픽으로 만들었어 — 관리자가 그록 자격을 다시 등록해야 해. ({why})')

    first_frames = sum(1 for i in range(total) if (img_dir / f's{i}.png').exists())
    progress(id_, 'run', f'그록 {total}장면 발사' + (f' · 첫 그림 {first_frames}장' if first_frames else ' · 글→영상'), 0.02)
    state = {'ok': 0, 'fin': 0}
    costs, fails = [], []

    def one(i):
        sc = scenes[i]
        img = img_dir / f's{i}.png'
        image = img.read_bytes() if img.exists() and img.stat().st_size > 2048 else None
        sec = seconds_for(timing['scenes'][i].get('dur'))
        last = ''
        for attempt in range(2):
            try:
                rid = grok_api.start_video(prompt_for(sc, bool(image)), token=tok, ratio=ratio, image=image, seconds=sec)
                v = grok_api.wait_video(rid, token=tok)
                raw = grok_api.fetch(v['url'])
                with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
                    f.write(raw)
                if not strip_audio(f.name, out / f's{i}.mp4'):
                    raise RuntimeError('받은 영상 파일이 깨졌어')
                costs.append(float(v.get('cost_usd') or 0))
                state['ok'] += 1
                return
            except Exception as e:  # noqa: BLE001
                last = str(e)[:100]
                where = getattr(e, 'where', '')
                if where in ('video-moderated', 'auth') or getattr(e, 'dead_auth', False):
                    break   # 검열·자격 = 같은 요청으로 안 바뀐다
                time.sleep(4)
        fails.append((i, last))

    def tick(fut):
        state['fin'] += 1
        progress(id_, 'run', f'장면 영상 {state["ok"]}/{total}', state['fin'] / total)

    with ThreadPoolExecutor(max_workers=PAR) as ex:
        futs = [ex.submit(one, i) for i in range(total)]
        for f in futs:
            f.add_done_callback(tick)
        for f in futs:
            f.result()
    used = state['ok']
    cost = sum(costs)
    if used == total:
        progress(id_, 'done', f'장면 영상 {used}장면')
        return done(used, f'그록 영상 {used}장면' + ('' if first_frames else ' · 맥이 꺼져 있어 첫 그림 없이 글→영상으로 만들었어'), cost)
    fails.sort()
    why = '; '.join(f'장면 {i + 1}: {w}' for i, w in fails[:3])
    progress(id_, 'done', f'장면 영상 {used}/{total}')
    return done(used, f'그록 영상 {used}/{total}장면만 받았어 — 나머지는 그림·모션 그래픽으로 채웠어. ({why})', cost)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
