#!/usr/bin/env python3
"""유튜브 숏폼(ys) 완성작 누적 — R2 ys_out/_hist.json 앞쪽에 이번 결과를 끼운다(최신 우선 · 최대 60).

  ys_hist.py <result.json>

뷰어 「완성작」 썸네일 그리드가 /ys_out/_hist.json(r2live)을 읽는다 = 기기·브라우저 무관 같은 목록(운영자 260928 «R2 우선»).
깃 커밋 누적 대신 R2 한 파일 — 결과 json 은 viewer/ys_out/<id>/result.json 에도 남으니 목록이 깨져도 원본은 산다.
한계: 읽기-수정-쓰기라 동시 완료 2건이 같은 몇 초 안에 쓰면 한쪽이 목록에서 빠질 수 있다(원본 result.json 은 남음 ·
쓰기 직전에 읽어 경합 창을 수 초로 줄임 · 발사 레이트리밋 3이라 실사용 위험 낮음).
fail-soft: 실패 = ::warning:: 1줄(완성 영상 자체는 이미 올라가 있다).
"""
import json
import os
import subprocess
import sys
import tempfile
import time

KEY = 'ys_out/_hist.json'
CAP = 60


def aws(*args):
    env = dict(os.environ, AWS_DEFAULT_REGION='auto', AWS_REQUEST_CHECKSUM_CALCULATION='when_required',
               AWS_RESPONSE_CHECKSUM_VALIDATION='when_required')
    return subprocess.run(['aws', *args, '--endpoint-url', f"https://{os.environ.get('R2_ACCOUNT_ID', '')}.r2.cloudflarestorage.com"],
                          capture_output=True, text=True, env=env)


def read_items():
    """기존 목록 → list · 아직 없음(첫 완성작) = [] · 그 밖의 읽기 실패·깨진 JSON = None(= 쓰지 않는다).
    일시 장애 한 번에 빈 목록으로 덮으면 최대 59편이 모든 기기에서 사라진다 → 없을 때만 새로 만든다 · 읽기는 3번 시도."""
    for k in range(3):
        r = aws('s3', 'cp', f"s3://{os.environ['R2_BUCKET']}/{KEY}", '-')
        err = (r.stderr or '')
        if r.returncode != 0 and ('NoSuchKey' in err or '(404)' in err or 'Not Found' in err):
            return []
        if r.returncode == 0:
            try:
                items = json.loads(r.stdout or '').get('items')
            except ValueError:
                return None
            return [x for x in (items or []) if isinstance(x, dict) and x.get('id')] if isinstance(items, list) else None
        time.sleep(2 * (k + 1))
    return None


def entry(res):
    keys = ('id', 'generated', 'title', 'short_title', 'channel', 'src_title', 'src_url', 'poster', 'video', 'infographic',
            'report', 'dur', 'ratio', 'voice_name')
    e = {k: res.get(k) for k in keys if res.get(k) not in (None, '')}
    e['ts'] = e.pop('generated', '')
    return e


def merge(items, new):
    out = [new] + [x for x in items if x.get('id') != new.get('id')]
    return out[:CAP]


def main(argv):
    if len(argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    if not os.environ.get('R2_BUCKET'):
        print('::warning::R2 미설정 — 완성작 목록 생략')
        return 0
    res = json.load(open(argv[1], encoding='utf-8'))
    if res.get('error') or not res.get('video'):
        return 0
    new = entry(res)
    cur = read_items()
    if cur is None:
        print('::warning::완성작 목록을 읽지 못해 이번엔 갱신하지 않음(덮어쓰기 유실 방지 · 영상은 정상)')
        return 0
    items = merge(cur, new)   # 쓰기 직전에 읽어 합친다(경합 창 = 이 두 줄 사이 수 초)
    with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False, encoding='utf-8') as f:
        json.dump({'items': items}, f, ensure_ascii=False, separators=(',', ':'))
    r = aws('s3', 'cp', f.name, f"s3://{os.environ['R2_BUCKET']}/{KEY}", '--content-type', 'application/json; charset=utf-8',
            '--cache-control', 'no-store', '--only-show-errors')
    if r.returncode != 0:
        print(f'::warning::완성작 목록 게시 실패 — {r.stderr.strip()[:160]}')
        return 0
    print(f'완성작 목록 {len(items)}편(최신 = {new.get("id")})')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
