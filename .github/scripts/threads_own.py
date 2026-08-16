#!/usr/bin/env python3
# 노뮤트 **본계정** 스레드 지표 수집 — Meta Threads API(graph.threads.net) · stdlib only · 시크릿 미등록 = no-op(rc 0)
# (운영자 260816 "스레드 구독자도 ig 아래에 표기하고, 관련 내용도 녹여내고싶은데 · 참고용이면 되긴하는데 거기도 1.6만명이라 지표가 있으면 좋긴해")
#
# ⚠⚠ 계정 3종이 서로 **다른 계정**이다 — 섞으면 화면에 남의 숫자가 뜬다(260816 실측 확인분):
#   · TH_ACCESS_TOKEN        = 노뮤트 **본계정**(= 이 파일이 쓰는 유일한 열쇠 · 인스타 @no_mute 의 스레드)
#   · THREADS_ACCESS_TOKEN   = **루시**(가상인물) 계정 = 자동 발행·답글 축(threads_api.py 전용 · 무접촉)
#   · THREADS_COOKIE         = 또 다른 수집용 계정 = 남 계정 훑기(sns_trends 축 · 무접촉)
#   이 파일은 TH_ACCESS_TOKEN 만 읽는다. 폴백으로 다른 열쇠를 집으면 **루시 팔로워가 노뮤트 화면에 뜬다** = 금지.
#
# 왜 별도 파일인가 = threads_api.py 는 「발행·답글」 축이고 이건 「지표 수집」 축이다. 한 파일에 넣으면
#   루시 열쇠와 노뮤트 열쇠가 같은 모듈 전역(TOK)을 공유해 위 3종 혼입이 구조적으로 가능해진다.
#
# 산출 = apps/insta/data/threads_own.json (기계산출물 · 손편집 금지)
#   { generated_kst, profile{id,username,followers_count,...}, posts[...], insights{...}, dropped[...] }
#
# ⚠ **낱개 폴백이 계약**(insta_fetch.py 관례 계승) — Meta 는 지표를 예고 없이 개폐한다. 지표 하나가 죽었다고
#   수집 전체를 실패로 끝내면 팔로워까지 같이 잃는다 → 죽은 지표는 dropped 에 이름만 남기고 나머지는 살린다.
#
# ⚠ 스레드는 인스타보다 **얕다**(공식 API 한계) — 저장·도달·팔로워 유입 경로가 아예 없다.
#   없는 지표를 추정으로 채우지 않는다(§[1] 정직). 못 받은 건 dropped 에 남아 화면·요약이 그대로 읽는다.
#
# ⚠ 미완(260816) = 이 파일은 **1단계(수집)** 뿐이다. 화면 표기(인스타 팔로워 아래)·채널 요약 녹이기는
#   실호출로 「무엇이 실제로 받아지는지」를 확인한 뒤 붙인다(받는 지표가 확정돼야 화면·요약 문구가 정해진다).
#   그 배선이 끝나면 층 생존 게이트를 신설하고 여기에 CONTRACT 앵커를 단다.
import json, os, sys, datetime, urllib.request, urllib.error, urllib.parse

TOK = os.environ.get('TH_ACCESS_TOKEN', '').strip()
G = 'https://graph.threads.net/v1.0'
OUT = 'apps/insta/data/threads_own.json'
KST = datetime.timezone(datetime.timedelta(hours=9))   # 시각 = KST 강제(§D4 · naive now 금지)
POST_N = int(os.environ.get('TH_POST_N', '25'))        # 최근 게시물 표본(반응 평균용 · 과다 호출 차단)


def _now():
    return datetime.datetime.now(KST)


def api(path, **params):
    """Graph 호출 — 에러 본문을 예외 메시지로 승격(threads_api.py api() 관용구 미러 ·
    "HTTP 400"만으론 권한 누락 vs 토큰 만료 진단 불가)."""
    params['access_token'] = TOK
    qs = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    try:
        with urllib.request.urlopen(f'{G}/{path}?{qs}', timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            err = (json.loads(e.read().decode('utf-8', 'replace')).get('error') or {})
            code, msg = err.get('code'), err.get('message', 'HTTP error')[:200]
            if code == 190:
                raise RuntimeError(f'토큰 만료·무효(code 190) — 시크릿 TH_ACCESS_TOKEN 재발급 필요: {msg}') from None
            raise RuntimeError(f'{e.code}/{code}: {msg}') from None
        except RuntimeError:
            raise
        except Exception:
            raise RuntimeError(f'{e.code}: HTTP error(본문 파싱 불가)') from None


def _total(metric_row):
    """threads_insights 응답 한 줄에서 값 하나를 꺼낸다 — total_value 형과 values[] 형 둘 다 온다
    (Meta 가 지표마다 다른 모양을 준다 · 실측 대응 · 못 읽으면 None = dropped 로 간다)."""
    tv = metric_row.get('total_value')
    if isinstance(tv, dict) and tv.get('value') is not None:
        return tv.get('value')
    vals = metric_row.get('values')
    if isinstance(vals, list) and vals:
        v = vals[-1]
        if isinstance(v, dict):
            return v.get('value')
    return None


def main():
    if not TOK:
        print('threads-own: TH_ACCESS_TOKEN 미등록 — 스킵(no-op 스캐폴드)')
        return 0

    out = {'generated_kst': _now().isoformat(timespec='seconds'), 'dropped': []}

    # ① 계정 신원 — 이것만은 필수(실패 = 뒤 전부 무의미하므로 여기서만 rc=1)
    try:
        prof = api('me', fields='id,username,name,threads_profile_picture_url,threads_biography')
    except Exception as e:
        print(f'::error::스레드 본계정 조회 실패 — {e} · 열쇠 칸 = TH_ACCESS_TOKEN(루시 THREADS_ACCESS_TOKEN 과 다른 계정이다)', file=sys.stderr)
        return 1
    uid = str(prof.get('id') or '').strip()
    if not uid:
        print('::error::스레드 본계정 id 해석 실패 — 응답에 id 없음', file=sys.stderr)
        return 1
    out['profile'] = {k: prof.get(k) for k in ('id', 'username', 'name', 'threads_biography') if prof.get(k)}

    # ② 계정 지표 — 낱개 폴백(하나씩 따로 물어 죽은 지표만 버린다 · 묶어 물으면 하나 때문에 전건 실패)
    for m in ('followers_count', 'views', 'likes', 'replies', 'reposts', 'quotes'):
        try:
            d = api(f'{uid}/threads_insights', metric=m)
            rows = d.get('data') or []
            v = _total(rows[0]) if rows else None
            if v is None:
                out['dropped'].append(m)
            else:
                out['profile' if m == 'followers_count' else 'insights'] = {
                    **out.get('profile' if m == 'followers_count' else 'insights', {}), m: v}
        except Exception as e:
            out['dropped'].append(f'{m}({e})')

    # ②-b 30일 창 조회수 — 화면 타일 정본 축(운영자 260816 "스레드 팔로워 / 30일 누적 조회수 / 일 평균 조회")
    # ⚠ **기간을 못박아 묻는 게 계약**이다 — since/until 없이 물으면 Meta 가 어느 구간을 주는지 응답에 안 적혀 온다
    #   (260816 실측 = 조회 11,263인데 좋아요 15 = 두 지표의 창이 서로 다르다는 정황). 창을 모르는 숫자를
    #   화면에 「조회 N」으로 적으면 그 표기 자체가 거짓말이 된다 → 창을 우리가 정해서 묻고, 창을 같이 적는다.
    # 일 평균 = 누적 ÷ 실제 창 일수(내림 아님 = 반올림 1자리 · 화면이 그대로 읽는다).
    try:
        until = int(_now().timestamp())
        since = until - 30 * 86400
        d = api(f'{uid}/threads_insights', metric='views', since=since, until=until)
        rows = d.get('data') or []
        v = _total(rows[0]) if rows else None
        if v is None:
            out['dropped'].append('views_30d')
        else:
            out['views_30d'] = v
            out['views_per_day'] = round(v / 30, 1)
            out['window_days'] = 30
    except Exception as e:
        out['dropped'].append(f'views_30d({e})')

    # ③ 최근 게시물 — 반응 평균의 원료 + 30일 창 실패 시 화면 3번째 타일의 폴백(운영자 260816 "안되면 가장 최근 게시물")
    try:
        d = api('me/threads', fields='id,media_type,text,permalink,timestamp', limit=POST_N)
        posts = []
        for p in (d.get('data') or []):
            t = (p.get('text') or '').strip().replace('\n', ' ')
            posts.append({'id': p.get('id'), 'type': p.get('media_type'),
                          'text': t[:120], 'permalink': p.get('permalink'), 'ts': p.get('timestamp')})
        out['posts'] = posts
        out['media_count'] = len(posts)
    except Exception as e:
        out['dropped'].append(f'posts({e})')
        out['posts'] = []

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
        f.write('\n')

    fol = (out.get('profile') or {}).get('followers_count')
    print(f'threads-own: @{out["profile"].get("username","?")} · 팔로워 {fol if fol is not None else "미상"} · '
          f'게시물 표본 {len(out.get("posts") or [])} · 못 받은 지표 {len(out["dropped"])}')
    if out['dropped']:
        print(f'  dropped = {out["dropped"]}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
