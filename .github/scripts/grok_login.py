#!/usr/bin/env python3
"""그록 다시 로그인 — 러너가 로그인 주소를 띄우고, 운영자가 승인하면 갱신 열쇠를 **비밀칸에 바로** 넣는다.
(운영자 260928 «토큰 받아서 손으로 옮기는 과정을 버튼 하나로» · 판정기 shared/grok_oauth_probe.py 의 로그인 절차 계승)

  grok_login.py <id>     env: R2_ACCOUNT_ID·R2_BUCKET·AWS_* (주소 게시) · XAI_SECRET_PAT(=GH_TOKEN · 비밀칸 쓰기 권한)
                              GROK_LOGIN_SECRET(넣을 비밀칸 이름 · 기본 XAI_SECRET_PAT = 이관 때 운영자가 정한 이름)

흐름: ① 인증 서버 발견 문서 → ② 1회용 로그인 코드 발급 → ③ 주소·코드를 R2 grok_login/<id>.json 에만 게시
      (⚠ 이 레포는 공개 = Actions 로그도 공개 → 주소·코드·열쇠를 로그에 찍지 않는다)
      → ④ 승인 대기(최대 15분) → ⑤ 모델 목록 1회로 자격 확인 → ⑥ 갱신 열쇠를 봉인해 비밀칸에 저장 → R2 에 완료 표시.
열쇠 자체는 어디에도 출력·기록하지 않는다(비밀칸 봉인 저장 한 곳뿐).
"""
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'shared'))
import grok_api  # noqa: E402  비밀칸 봉인 저장(_persist_secret) SSOT
import grok_oauth_probe as probe  # noqa: E402  발견 문서·클라이언트·범위·요청기 SSOT(프록시 CA 포함)

WAIT_MAX = 900   # 승인 대기 상한(코드 수명과 같거나 짧게)


def post(id_, doc):
    """R2 grok_login/<id>.json 에 상태 게시(공개 주소 · 캐시 금지). 실패해도 로그인 자체는 계속한다."""
    bucket, acc = os.environ.get('R2_BUCKET'), os.environ.get('R2_ACCOUNT_ID')
    if not bucket or not acc:
        print('::warning::R2 설정 없음 — 상태 게시 생략')
        return
    doc = {'id': id_, 'updated': int(time.time()), **doc}
    try:
        subprocess.run(['aws', 's3', 'cp', '-', f's3://{bucket}/grok_login/{id_}.json',
                        '--content-type', 'application/json; charset=utf-8', '--cache-control', 'no-store',
                        '--endpoint-url', f'https://{acc}.r2.cloudflarestorage.com', '--only-show-errors'],
                       input=json.dumps(doc, ensure_ascii=False).encode(), check=True, timeout=60,
                       env={**os.environ, 'AWS_DEFAULT_REGION': 'auto', 'AWS_REQUEST_CHECKSUM_CALCULATION': 'when_required'})
    except Exception as e:  # noqa: BLE001
        print(f'::warning::상태 게시 실패({type(e).__name__})')


def fail(id_, why):
    print(f'::error::그록 로그인 실패 — {why}')
    post(id_, {'state': 'fail', 'why': why})
    return 1


def main(argv):
    if len(argv) < 2 or not argv[1].replace('-', '').isalnum():
        print(__doc__, file=sys.stderr)
        return 2
    id_ = argv[1]
    name = os.environ.get('GROK_LOGIN_SECRET') or 'XAI_SECRET_PAT'
    post(id_, {'state': 'start'})

    code, txt, doc = probe._req(probe.DISCOVERY, timeout=30)
    if code != 200 or not doc or not doc.get('device_authorization_endpoint') or not doc.get('token_endpoint'):
        return fail(id_, f'그록 인증 서버 정보를 못 받았어(HTTP {code}) — 잠시 후 다시.')
    code, txt, dev = probe._req(doc['device_authorization_endpoint'], data={'client_id': probe.CLIENT_ID, 'scope': probe.SCOPE}, timeout=30)
    if code != 200 or not dev or not dev.get('user_code') or not dev.get('device_code'):
        return fail(id_, f'로그인 코드 발급이 거절됐어(HTTP {code}).')
    url = dev.get('verification_uri_complete') or dev.get('verification_uri')
    interval = int(dev.get('interval') or 5)
    life = min(WAIT_MAX, int(dev.get('expires_in') or WAIT_MAX))
    post(id_, {'state': 'wait', 'url': url, 'code': dev['user_code'], 'expires': int(time.time()) + life})
    print(f'로그인 주소 게시 완료(R2 grok_login/{id_}.json · 제한 {life // 60}분) — 주소·코드는 공개 로그에 찍지 않는다')
    sys.stdout.flush()

    deadline, tokens, waited = time.time() + life, None, 0
    while time.time() < deadline:
        time.sleep(interval)
        waited += interval
        code, txt, tk = probe._req(doc['token_endpoint'], data={
            'client_id': probe.CLIENT_ID, 'device_code': dev['device_code'],
            'grant_type': 'urn:ietf:params:oauth:grant-type:device_code'}, timeout=30)
        err = (tk or {}).get('error')
        if code == 200 and tk and tk.get('access_token') and tk.get('refresh_token'):
            tokens = tk
            break
        if err == 'authorization_pending':
            if waited % 60 < interval:
                print(f'  … 승인 기다리는 중 ({waited}초)')
                sys.stdout.flush()
            continue
        if err == 'slow_down':
            interval += 5
            continue
        if err in ('expired_token', 'access_denied'):
            return fail(id_, '승인이 끝나기 전에 코드가 만료되거나 거절됐어 — 다시 눌러줘.' if err == 'expired_token' else '승인 화면에서 거절됐어.')
    if not tokens:
        return fail(id_, f'{life // 60}분 안에 승인이 안 됐어 — 다시 눌러줘.')

    # 자격 확인 = 모델 목록 1회(요금·추론 0) — 로그인은 됐는데 이 계정에 API 통로가 없으면 여기서 갈린다
    code, txt, ml = probe._req(f'{probe.API_BASE}/models', headers={'Authorization': 'Bearer ' + tokens['access_token']}, method='GET', timeout=40)
    if code in (401, 403):
        return fail(id_, f'로그인은 됐지만 이 계정엔 그록 API 통로가 없어(HTTP {code}) — X Premium+ 또는 SuperGrok 계정인지 확인해줘.')
    n_models = len((ml or {}).get('data') or []) if isinstance(ml, dict) else 0

    if not grok_api._persist_secret(tokens['refresh_token'], name):
        return fail(id_, f'새 열쇠를 비밀칸({name})에 저장하지 못했어 — 비밀칸 쓰기 권한(GH_TOKEN)을 확인해줘.')
    post(id_, {'state': 'done', 'secret': name, 'models': n_models})
    print(f'✅ 그록 로그인 완료 — 새 갱신 열쇠를 비밀칸 {name} 에 봉인 저장(모델 {n_models}개 확인)')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
