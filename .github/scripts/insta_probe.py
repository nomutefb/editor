#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""인스타 팔로워 취소(언팔) 지표 실호출 진단기 — 읽기 전용·커밋 0·LLM 0콜·stdlib only.

발단(운영자 260811) = "팔로워 증감만 알고 실제 유입을 모른다 — 취소 수를 API로 받아올 수 있나".
실측 사고 = `insta_fetch`가 260719부터 `follows_and_unfollows`를 요청해 왔는데 원장 1,033줄 중
**1,009줄 전건이 빈 껍데기**(`[{"dimension_keys":["follow_type"]}]` = results 배열 자체가 없음)였고,
`parse_ins`가 breakdowns를 truthy로 읽어 **성공으로 통과**시켜 dropped 경보가 0회였다(조용한 죽음).
결과 = 뷰어 취소 라인이 284일 전건 결측 · 같은 창의 `follower_count`도 최근 전건 0.

이 스크립트는 **원인을 가른다** — 왜 빈손인지는 요청 조합을 갈아끼워 실호출해야만 확정된다.
산출 = 표준출력 진단표뿐(파일 쓰기 0 · 커밋 0). 토큰은 어떤 경로로도 출력하지 않는다.
"""
import datetime
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

TOK = os.environ.get('IG_ACCESS_TOKEN', '').strip()
UID = os.environ.get('IG_USER_ID', '').strip() or 'me'
BASE = os.environ.get('IG_API_BASE', 'https://graph.instagram.com').rstrip('/')
KST = ZoneInfo('Asia/Seoul')


def api(path, **params):
    """1콜 → (json|None, err|None). 토큰은 URL에만 실리고 출력 경로엔 절대 안 나간다."""
    q = {**params, 'access_token': TOK}
    url = f'{BASE}/{path}?' + urllib.parse.urlencode(q)
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            return json.load(r), None
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read().decode('utf-8', 'replace'))
        except Exception:
            body = {}
        err = (body.get('error') or {})
        return None, f"HTTP {e.code} / code {err.get('code')} / sub {err.get('subcode')}: {err.get('message', '')}"
    except Exception as e:
        return None, f'{type(e).__name__}: {e}'


def show(label, path, **params):
    """조합 1건 실호출 → 라벨·보낸 인자·응답 원문(또는 에러 전문) 출력. 반환 = 응답 json|None."""
    j, err = api(path, **params)
    sent = ' '.join(f'{k}={v}' for k, v in params.items())
    print(f'\n── [{label}]\n   보낸 인자: {sent}')
    if err:
        print(f'   ✗ 에러: {err}')
        return None
    txt = json.dumps(j, ensure_ascii=False)
    print(f'   ✓ 응답({len(txt)}자): {txt[:1400]}')
    return j


def epoch(dt):
    return str(int(dt.timestamp()))


def main():
    if not TOK:
        print('no-op — IG_ACCESS_TOKEN 미등록(진단 불가). 러너 시크릿 확인.')
        return 0

    prof, err = api(UID, fields='id,username,account_type,followers_count,media_count')
    if prof is None:
        print(f'::error::프로필 조회 실패 — {err}')
        return 1
    uid = prof.get('id') or UID
    print('═══ 계정 ═══')
    print(f"   @{prof.get('username')} · 유형 {prof.get('account_type')} · "
          f"팔로워 {prof.get('followers_count')} · 게시물 {prof.get('media_count')}")
    print('   ※ 100 팔로워 미만 제한 해당 없음(문서상 follows_and_unfollows·follower_count 최소 조건)')

    d0 = datetime.datetime.now(KST).replace(hour=0, minute=0, second=0, microsecond=0)
    ins = f'{uid}/insights'

    print('\n\n═══ ① 팔로우/취소 분해 — 요청 조합별 실호출 ═══')
    # A = 현행 insta_fetch 조합 그대로(재현 = 빈 껍데기가 코드 탓인지 조합 탓인지 가른다)
    show('A 현행 조합(어제 00:00~오늘 00:00 KST)', ins,
         metric='follows_and_unfollows', period='day', metric_type='total_value',
         breakdown='follow_type', since=epoch(d0 - datetime.timedelta(days=1)), until=epoch(d0))
    # B = 창 없이(Meta 기본창) — since/until 명시가 원인인지
    show('B 창 없음(Meta 기본창)', ins,
         metric='follows_and_unfollows', period='day', metric_type='total_value', breakdown='follow_type')
    # C = 3일 전 창 — 데이터 처리 지연(문서상 최대 48h)이 원인인지
    show('C 3일 전 하루창', ins,
         metric='follows_and_unfollows', period='day', metric_type='total_value', breakdown='follow_type',
         since=epoch(d0 - datetime.timedelta(days=3)), until=epoch(d0 - datetime.timedelta(days=2)))
    # D = 최근 7일 통창 — 하루창이 너무 좁아 빈 것인지
    show('D 최근 7일 통창', ins,
         metric='follows_and_unfollows', period='day', metric_type='total_value', breakdown='follow_type',
         since=epoch(d0 - datetime.timedelta(days=7)), until=epoch(d0))
    # E = breakdown 없이 — 분해 인자가 결과를 죽이는지(총합이라도 오면 취소 축만 막힌 것)
    show('E breakdown 없음(총합만)', ins,
         metric='follows_and_unfollows', period='day', metric_type='total_value',
         since=epoch(d0 - datetime.timedelta(days=7)), until=epoch(d0))

    print('\n\n═══ ② 신규 팔로우 수(follower_count) — 최근 전건 0의 진위 ═══')
    show('F 최근 7일', ins, metric='follower_count', period='day',
         since=epoch(d0 - datetime.timedelta(days=7)), until=epoch(d0))
    show('G 창 없음', ins, metric='follower_count', period='day')

    print('\n\n═══ ③ 게시물당 팔로워 — 미디어 지표 존재 여부 ═══')
    print('   ※ 미지원 지표는 Meta가 에러 본문에 **지원 지표 전체 목록**을 실어준다 = 문서보다 정확한 실측.')
    media, merr = api(f'{uid}/media', fields='id,media_product_type,timestamp,permalink', limit='3')
    mlist = (media or {}).get('data', [])
    if not mlist:
        print(f'   ✗ 미디어 목록 조회 실패 — {merr}')
    for m in mlist[:2]:
        mid, mpt = m.get('id'), m.get('media_product_type')
        print(f'\n   ▸ 대상 게시물: {mpt} · {m.get("timestamp")} · {m.get("permalink")}')
        # 낱개 요청 = 미지원 지표를 에러로 드러낸다(묶음이면 하나만 죽어도 전건 실패라 원인이 뭉갠다)
        for metric in ('follows', 'profile_visits', 'profile_activity', 'navigation', 'total_interactions'):
            show(f'{metric} @ {mpt}', f'{mid}/insights', metric=metric)
        # 일부러 없는 지표 1발 = 그 계정·그 미디어 유형이 실제로 허용하는 **전체 목록** 수확
        show(f'지원목록 수확(의도적 오류) @ {mpt}', f'{mid}/insights', metric='__nomute_probe__')

    print('\n\n═══ ④ 계정 지표 지원목록 수확(의도적 오류) ═══')
    print('   ※ 덤 — 현행 수집이 views·profile_views·accounts_engaged·total_interactions를')
    print('     "200 응답 미포함"으로 드랍 중이라 그 축의 정답도 이 목록에 같이 실린다.')
    show('계정 지원목록', ins, metric='__nomute_probe__', period='day', metric_type='total_value')

    print('\n\n═══ ⑤ 소급 경계 — 며칠 전까지 값이 오는가(설계를 가르는 축) ═══')
    print('   ※ 왜 = 게시물별 이탈 판정은 표본이 생명이다. 90일치를 지금 회수할 수 있으면 설계가 통째로 달라진다.')
    print('     지연 경계(앞쪽)와 보관 경계(뒤쪽)를 하루창으로 훑어 실측한다 — 문서 추정이 아니라 실호출.')
    for d in (1, 2, 3, 4, 7, 14, 30, 60, 89, 90, 120, 180):
        j, err = api(ins, metric='follows_and_unfollows', period='day', metric_type='total_value',
                     breakdown='follow_type',
                     since=epoch(d0 - datetime.timedelta(days=d)),
                     until=epoch(d0 - datetime.timedelta(days=d - 1)))
        if err:
            print(f'   {d:3d}일 전: ✗ {err[:110]}')
            continue
        res = (((j or {}).get('data') or [{}])[0].get('total_value') or {}).get('breakdowns') or [{}]
        rows = res[0].get('results') or []
        if not rows:
            print(f'   {d:3d}일 전: 빈손(results 없음)')
        else:
            got = {' '.join(str(x) for x in (r.get('dimension_values') or [])): r.get('value') for r in rows}
            print(f'   {d:3d}일 전: {got}')

    print('\n\n═══ ⑥ 게시물당 신규 = 나이 편향 실측(누적값 함정) ═══')
    print('   ※ 왜 = follows는 period=lifetime 누적이다. 오래된 게시물일수록 크다면 최근 것과 같은 자로 못 잰다.')
    print('     게시 시각이 다른 표본을 나란히 찍어 나이와 값의 관계를 눈으로 본다(판정은 평의회 몫).')
    med2, _ = api(f'{uid}/media', fields='id,media_product_type,timestamp,permalink', limit='25')
    ml = (med2 or {}).get('data', [])
    for m in ml[:12]:
        j, err = api(f"{m['id']}/insights", metric='follows,profile_visits,reach,views')
        if err:
            print(f"   {m.get('timestamp')} {m.get('media_product_type'):5s} ✗ {err[:80]}")
            continue
        g = {x.get('name'): ((x.get('values') or [{}])[0].get('value')) for x in (j or {}).get('data', [])}
        fw, rc = g.get('follows'), g.get('reach')
        rate = f'{fw / rc * 10000:.1f}' if (isinstance(fw, int) and isinstance(rc, int) and rc) else '—'
        print(f"   {m.get('timestamp')} {str(m.get('media_product_type')):5s} "
              f"신규{str(fw):>5s} 방문{str(g.get('profile_visits')):>6s} 도달{str(rc):>8s} 조회{str(g.get('views')):>8s} "
              f"· 도달1만당 신규 {rate}")

    print('\n\n═══ 진단 끝 — 판독 기준 ═══')
    print('   · A~E 중 results가 실린 조합이 있으면 → 취소 수는 받아올 수 있고 현행 조합이 틀린 것.')
    print('   · A~E 전건 빈손인데 에러도 없으면 → Meta가 이 계정에 해당 분해를 안 주는 것(계정·권한 축).')
    print('   · ③에서 follows가 정상 응답하면 → 게시물당 팔로워 배선 가능(운영자 1순위 요구).')
    return 0


if __name__ == '__main__':
    sys.exit(main())
