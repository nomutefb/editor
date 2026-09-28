#!/usr/bin/env python3
"""유튜브 숏폼(ys) 진행 기록기 — 단계 상태를 progress.json 에 쓰고 R2(ys_out/<id>/progress.json)에 즉시 게시.

  ys_progress.py <id> init [img=codex|motion|grok] [stt=] [voice=] [len=]
  ys_progress.py <id> <step> run|done|skip|fail [note] [p=0.0~1.0]
  ys_progress.py <id> finish            (state=done · pct=100)
  ys_progress.py <id> fail "<사유>"      (진행 중 단계 fail + state=fail + error)

뷰어는 /ys_out/<id>/progress.json 을 5초 폴링한다(functions/ys_out = r2live · R2 미스 = 정적 폴백).
게시는 fail-soft — R2 실패가 제작을 멈추지 않는다(대신 ::warning:: 1줄로 표면화 · 무음 금지).
"""
import json
import os
import subprocess
import sys
import time

STEPS = [('meta', '영상 정보 확인', 5), ('stt', '받아쓰기', 15), ('plan', '인사이트 정리', 30),
         ('voice', '목소리 입히기', 15), ('img', '장면 그림', 12), ('vid', '장면 영상', 12), ('mgd', '모션 디자인', 10), ('render', '영상 만들기', 15), ('upload', '올리기', 5)]
KEYS = [k for k, _l, _w in STEPS]
LOCAL = '/tmp/ys_progress.json'


def budgets(img='codex', stt='scribe', voice='eleven', ln=60, dur=0):
    """단계별 예산(초) — 러너 환경 준비 시간을 그 단계에 포함한 추정치(운영자 260928 «세부 시간·총 시간·예산 표시»).
    근거: 로컬 실측(렌더 71초 영상 ≈ 90초 · edge 합성 장면당 ≈ 5초) + 러너 준비(claude 설치 ≈ 40초 · 렌더 환경 ≈ 60~90초).
    예산은 약속이 아니라 눈금이다 — 넘기면 화면이 경과 숫자만 경고 톤으로 바꾼다."""
    ln = int(ln or 60)
    scenes = {45: 5, 60: 7, 90: 9}.get(ln, 7)
    return {
        'meta': 90,
        'stt': int(90 + 0.06 * dur) if stt == 'scribe' else 40,
        'plan': 180,
        'voice': int(40 + ln) if voice == 'eleven' else int(30 + 0.6 * ln),
        'img': 70 * scenes if img in ('codex', 'depth', 'grok') else 0,   # 맥 Codex 한 장씩(그록 = 첫 프레임용 세로 그림)
        'vid': 90 + 60 * -(-scenes // 3) if img == 'grok' else 0,   # 그록 장면 영상 = 3발 동시 · 한 판 ≈ 1분(실측 전 추정)
        'mgd': 240 if img == 'motion' else 0,   # Opus 5.5 high 모션 디자이너 1콜(장면 코드) — 맥·그록 대체 때는 그 단계가 스스로 켠다
        'render': int(120 + 1.5 * ln) + {'motion': int(60 + 3 * ln), 'depth': int(60 + 1.5 * ln), 'grok': 60}.get(img, 0),   # 모션 = 장면당 프레임 캡처 · 입체 = 깊이 추정+워핑(≈ 실시간 1.3배) · 그록 = 영상 합성
        'upload': 20,
    }


def apply_budget(doc):
    b = budgets(**doc.get('opts', {}))
    tot = 0
    for st in doc['steps']:
        st['budget'] = b.get(st['k'], 0)
        if st['st'] != 'skip':
            tot += st['budget']
    doc['budget_total'] = tot


def pct(doc):
    """단계 가중 진행률 — skip 단계는 분모에서 빠진다 · 진행 중 단계는 p(0~1)만큼 · 완료 = 100."""
    if doc.get('state') == 'done':
        return 100
    tot = got = 0.0
    for (k, _l, w), st in zip(STEPS, doc['steps']):
        if st['st'] == 'skip':
            continue
        tot += w
        if st['st'] == 'done':
            got += w
        elif st['st'] in ('run', 'fail'):
            got += w * max(0.0, min(1.0, float(st.get('p') or 0)))
    return int(min(99, round(100 * got / tot))) if tot else 0


def load(id_):
    try:
        with open(LOCAL, encoding='utf-8') as f:
            d = json.load(f)
        if d.get('id') == id_:
            return d
    except Exception:
        pass
    now = int(time.time())
    return {'id': id_, 't0': now, 'updated': now, 'state': 'run', 'pct': 0,
            'steps': [{'k': k, 'label': l, 'st': 'wait'} for k, l, _w in STEPS]}


def publish(doc):
    if 'opts' in doc:
        apply_budget(doc)   # 중간에 건너뛴 단계(맥 꺼짐 = 그림 skip)는 총 예산에서 빠진다
    doc['updated'] = int(time.time())
    doc['pct'] = pct(doc)
    tmp = LOCAL + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(doc, f, ensure_ascii=False, separators=(',', ':'))
    os.replace(tmp, LOCAL)
    bucket, acc = os.environ.get('R2_BUCKET', ''), os.environ.get('R2_ACCOUNT_ID', '')
    if not bucket or not acc:
        return
    env = dict(os.environ, AWS_DEFAULT_REGION='auto', AWS_REQUEST_CHECKSUM_CALCULATION='when_required',
               AWS_RESPONSE_CHECKSUM_VALIDATION='when_required')
    r = subprocess.run(['aws', 's3', 'cp', LOCAL, f"s3://{bucket}/ys_out/{doc['id']}/progress.json",
                        '--content-type', 'application/json; charset=utf-8', '--cache-control', 'no-store',
                        '--endpoint-url', f'https://{acc}.r2.cloudflarestorage.com', '--only-show-errors'],
                       capture_output=True, text=True, env=env)
    if r.returncode != 0:
        print(f'::warning::진행 게시 실패(제작은 계속) — {r.stderr.strip()[:160]}')


def main(argv):
    # 바이트 절단된 한글(서로게이트 이스케이프)이 섞여도 utf-8 로 쓸 수 있게 = 실패 기록 단계가 여기서 죽지 않는다
    argv = [a.encode('utf-8', 'surrogateescape').decode('utf-8', 'replace') for a in argv]
    if len(argv) < 3:
        print(__doc__, file=sys.stderr)
        return 2
    id_, cmd = argv[1], argv[2]
    doc = load(id_)
    now = int(time.time())
    if cmd == 'init':
        doc = load('')
        doc['id'] = id_
        kv = dict(a.split('=', 1) for a in argv[3:] if '=' in a)
        img = kv.get('img', 'motion')
        img = 'motion' if img == 'none' else img
        doc['opts'] = {'img': img, 'stt': kv.get('stt', 'subs'), 'voice': kv.get('voice', 'edge'),
                       'ln': int(kv.get('len', '60') or 60) if str(kv.get('len', '60')).isdigit() else 60, 'dur': 0}
        if img == 'motion':
            doc['steps'][KEYS.index('img')]['st'] = 'skip'
        if img != 'grok':
            doc['steps'][KEYS.index('vid')]['st'] = 'skip'
        if img != 'motion':   # GPT·입체·그록 = 대체가 필요할 때만 모션 디자인 단계가 run 으로 스스로 켠다
            doc['steps'][KEYS.index('mgd')]['st'] = 'skip'
        apply_budget(doc)
    elif cmd == 'budget':   # 영상 길이를 안 뒤(meta) 받아쓰기 예산 재계산
        kv = dict(a.split('=', 1) for a in argv[3:] if '=' in a)
        try:
            doc.setdefault('opts', {})['dur'] = int(kv.get('dur', '0'))
        except ValueError:
            pass
        apply_budget(doc)
    elif cmd == 'finish':
        doc['state'] = 'done'
        for st in doc['steps']:
            if st['st'] in ('wait', 'run'):
                st['st'], st['t1'] = 'done', now
    elif cmd == 'fail':
        doc['state'] = 'fail'
        doc['error'] = (argv[3] if len(argv) > 3 else '제작 실패')[:300]
        for st in doc['steps']:
            if st['st'] == 'run':
                st['st'], st['t1'], st['note'] = 'fail', now, doc['error'][:80]
    elif cmd in KEYS:
        st = doc['steps'][KEYS.index(cmd)]
        new = argv[3] if len(argv) > 3 else 'run'
        if new not in ('run', 'done', 'skip', 'fail'):
            print(f'알 수 없는 상태: {new}', file=sys.stderr)
            return 2
        if new == 'run' and st['st'] != 'run':
            st['t0'] = now
        if new in ('done', 'skip', 'fail'):
            st['t1'] = now
            st.pop('p', None)
        st['st'] = new
        for a in argv[4:]:
            if a.startswith('p='):
                try:
                    st['p'] = round(float(a[2:]), 3)
                except ValueError:
                    pass
            elif a:
                st['note'] = a[:80]
    else:
        print(f'알 수 없는 명령: {cmd}', file=sys.stderr)
        return 2
    publish(doc)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
