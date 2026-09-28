#!/usr/bin/env python3
"""유튜브 숏폼(ys) 장면 그림 — 맥 Codex 레인에 잡을 걸고 결과를 기다린다(러너 쪽 짝 = scripts/mac/nomute_ys_driver.sh).

  ys_images.py <id> <plan.json> <outdir>   → outdir/s{i}.png (받은 만큼) + outdir/img.json {used, note}

흐름: ① 맥 표시등(ys_out/_mac/heartbeat.json) 확인 — 없음·180초 초과·Codex 미로그인 = 즉시 포기(기다리지 않는다)
      ② R2 queue/ysimg/<id>.json 착지(맥 잡워커가 10초 안에 집는다 · 본 큐와 분리)
      ③ ys_img/<id>/ 를 15초마다 확인 → 진행률 게시 · done.json 이 오면 끝 · YS_IMG_WAIT(기본 900초) 초과 = 잡 회수 후 포기
      ④ 받은 그림만 내려받는다 — 모자란 장면은 렌더가 글자 화면으로 채운다(영상은 항상 나온다).
전 경로 rc 0 — 그림은 선택 품질 축이라 제작을 멈추지 않는다(대신 사유를 img.json note 로 화면에 남긴다 · 무음 강하 금지).
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

WAIT = int(os.environ.get('YS_IMG_WAIT', '900'))
PICK = int(os.environ.get('YS_IMG_PICK', '150'))   # 이 안에 맥이 잡을 안 집으면(다른 잡에 잠김) 회수하고 바로 강하 = 900초 헛대기 0
STALE = 180
STYLE = os.environ.get('YS_IMG_STYLE', 'cinematic minimal illustration, soft light, dark background, teal accent, no text, no letters, no logos')


def aws(*args, capture=True):
    env = dict(os.environ, AWS_DEFAULT_REGION='auto', AWS_REQUEST_CHECKSUM_CALCULATION='when_required',
               AWS_RESPONSE_CHECKSUM_VALIDATION='when_required')
    ep = f"https://{os.environ.get('R2_ACCOUNT_ID', '')}.r2.cloudflarestorage.com"
    return subprocess.run(['aws', *args, '--endpoint-url', ep], capture_output=capture, text=True, env=env)


def s3(key):
    return f"s3://{os.environ.get('R2_BUCKET', '')}/{key}"


def progress(id_, st, note='', p=None):
    a = [sys.executable, str(Path(__file__).with_name('ys_progress.py')), id_, 'img', st, note]
    if p is not None:
        a.append(f'p={p:.3f}')
    subprocess.run(a, check=False)


def clean(p):
    """그림 묘사 = 신뢰 불가 입력(전사 → 모델 산출) → 영문 인쇄 문자만 · 프롬프트 표지 제거 · 한 줄 · 300자(맥 드라이버와 같은 규칙 = 이중 방어)."""
    p = re.sub(r'(?i)\b(begin|end)\s+prompt\b', ' ', str(p or ''))
    p = re.sub(r"[^A-Za-z0-9 ,.;:()'/-]+", ' ', p)
    return re.sub(r'\s+', ' ', p).strip()[:300]


def mac_state():
    r = aws('s3', 'cp', s3('ys_out/_mac/heartbeat.json'), '-')
    if r.returncode != 0 and 'NoSuchKey' not in (r.stderr or '') and '404' not in (r.stderr or ''):
        return 'err', '저장소에서 맥 신호를 못 읽음'   # 저장소 장애 ≠ 맥 꺼짐(원인 분리)
    if r.returncode != 0 or not r.stdout.strip():
        return 'off', '맥 신호 없음'
    try:
        hb = json.loads(r.stdout)
    except ValueError:
        return 'off', '맥 신호 해석 실패'
    age = int(time.time()) - int(hb.get('ts') or 0)
    if age > STALE:
        return 'off', f'맥 신호가 {age // 60}분 전에 끊김'
    if hb.get('codex') != 'chatgpt':
        return 'nologin', 'Codex ChatGPT 로그인 필요'
    return 'on', f"맥 켜짐 · 계정 {hb.get('accounts', 0)}개"


def done(outdir, used, note, total=0):
    json.dump({'used': used, 'total': total, 'note': note}, open(Path(outdir) / 'img.json', 'w', encoding='utf-8'), ensure_ascii=False)
    print(f'장면 그림 {used}장 · {note}')
    return 0


def main(argv):
    if len(argv) < 4:
        print(__doc__, file=sys.stderr)
        return 2
    id_, plan = argv[1], json.load(open(argv[2], encoding='utf-8'))
    outdir = Path(argv[3]); outdir.mkdir(parents=True, exist_ok=True)
    if not os.environ.get('R2_BUCKET'):
        progress(id_, 'skip', '저장소 미설정')
        return done(outdir, 0, '저장소(R2) 미설정 — 모션 그래픽으로 만들었어.')
    st, why = mac_state()
    total = len(plan['scenes'])
    if st != 'on':
        progress(id_, 'skip', why)
        head = {'off': '맥이 꺼져 있어서', 'nologin': '맥 Codex가 ChatGPT로 로그인돼 있지 않아서', 'err': '저장소에서 맥 신호를 못 읽어서'}[st]
        msg = (f'{head} 첫 프레임 그림 0/{total}장. (' + why + ')') if os.environ.get('YS_IMG') == 'grok' \
            else f'{head} 모션 그래픽으로 만들었어. (' + why + ')'   # 그록 = 사실(첫 그림 수)만 · 최종 결과 문구는 ys_grok 몫
        return done(outdir, 0, msg, total)
    # 방향 = 영상 비율 그대로(운영자 260928 «GPT 도 화면 전체 · 처음부터 9:16 으로 제작») — 9:16 = 세로 2:3 · 16:9 = 가로 3:2
    #   세로 구도 = 주인공을 위 2/3 에 · 아래 1/5 은 차분하게(자막 자리) — 그림이 곧 화면 전체라 자막과 겹치지 않게
    orient = 'portrait' if os.environ.get('YS_RATIO', '9:16') == '9:16' else 'landscape'
    frame = 'subject in upper two thirds, calm lower fifth' if orient == 'portrait' else 'calm lower fifth'
    room = 300 - len(frame) - len(STYLE) - 4   # 300자 상한(clean·맥 드라이버 동값) 안에서 화풍·「no text」 꼬리가 잘리지 않게 장면 묘사를 먼저 줄인다
    scenes = [{'i': i, 'prompt': clean(f"{clean(sc.get('img') or sc.get('head'))[:room].rstrip()}. {frame}. {STYLE}")}
              for i, sc in enumerate(plan['scenes']) if clean(sc.get('img') or sc.get('head'))]
    job = {'kind': 'ysimg', 'id': id_, 'ts': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
           'deadline': int(time.time()) + WAIT, 'orient': orient, 'scenes': scenes}
    with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False, encoding='utf-8') as f:
        json.dump(job, f, ensure_ascii=False)
    qkey = f'queue/ysimg/{id_}.json'   # 전용 접두(맥 워커가 본 큐보다 먼저 1잡씩 집는다 · 본 큐 적체와 무관)
    if aws('s3', 'cp', f.name, s3(qkey), '--content-type', 'application/json').returncode != 0:
        progress(id_, 'skip', '맥 작업 접수 실패')
        return done(outdir, 0, '맥에 그림 작업을 넘기지 못해 모션 그래픽으로 만들었어.', total)
    progress(id_, 'run', f'{why} · 0/{len(scenes)}', 0.0)
    t0, got, fin, picked, note0 = time.time(), set(), False, False, ''
    while time.time() - t0 < WAIT:
        time.sleep(15)
        r = aws('s3', 'ls', s3(f'ys_img/{id_}/'))
        names = {ln.split()[-1] for ln in (r.stdout or '').splitlines() if ln.strip()}
        got = {n for n in names if n.startswith('s') and n.endswith('.png')}
        progress(id_, 'run', f'장면 그림 {len(got)}/{len(scenes)}', len(got) / max(1, len(scenes)))
        if 'done.json' in names:
            fin = True
            break
        if not picked:
            picked = aws('s3', 'ls', s3(qkey)).returncode != 0   # 큐 파일이 사라짐 = 맥이 집었다
            if not picked and time.time() - t0 > PICK:
                note0 = f'맥이 다른 작업 중이라 {PICK // 60}분 안에 그림 작업을 못 집었어 — '
                break
    if not fin:
        aws('s3', 'rm', s3(qkey))   # 아직 안 집힌 잡 회수 = 늦게 도는 맥이 쓸데없이 구독 한도를 쓰지 않게(집힌 뒤면 맥이 마감 시각에 스스로 멈춘다)
    else:
        rj = aws('s3', 'cp', s3(f'ys_img/{id_}/done.json'), '-')
        try:
            note0 = str(json.loads(rj.stdout or '{}').get('notes') or '')[:80]
            note0 = note0 + ' — ' if note0 else ''
        except ValueError:
            note0 = ''
    for n in sorted(got):
        aws('s3', 'cp', s3(f'ys_img/{id_}/{n}'), str(outdir / n))
    used = len([p for p in outdir.glob('s*.png') if p.stat().st_size > 2048])
    if fin and used == total:
        progress(id_, 'done', f'장면 그림 {used}장')
        return done(outdir, used, f'장면 그림 {used}장(맥 Codex)', total)
    note = note0 + (f'맥이 {WAIT // 60}분 안에 끝내지 못해 ' if not fin and not note0 else '') + f'그림 {used}/{total}장만 받았어 — 나머지 장면은 모션 그래픽.'
    progress(id_, 'done', f'장면 그림 {used}/{total}')
    return done(outdir, used, note, total)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
