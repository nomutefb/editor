#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""인스타 직결 수집 — Meta Instagram API(Instagram Login 경로) · LLM 0콜 · stdlib only(설치 0).

게이트: IG_ACCESS_TOKEN 미등록 = no-op exit 0 (시크릿 게이트 스캐폴드 관례 = thumb_gen GEMINI 계승).
산출: apps/insta/data/{insights_daily.jsonl(append·일별 계정지표) · media_latest.json(최근 25개+개별 인사이트)
      · audience.json(인구통계·활동시간대) · token_meta.json(토큰 해시꼬리+최초 관측일 — 원문 저장 절대 금지)}
정본 = apps/insta/00_지침_컨설턴트_인스타_v1.md §1-2·§2-0 · 세팅/재발급 = docs/인스타_직결_세팅.md
주의: 지표명은 Meta가 개폐함(예: impressions→views 이관) → insights()가 묶음 실패 시 낱개 폴백으로
      살아있는 지표만 수집하고 죽은 지표는 dropped에 기록(전건 실패 방지 · 미래 개폐 자가 적응).
스탬프 = KST(§표기표준 d) · API 원본 타임스탬프(UTC)는 원문 보존.
"""
import datetime
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

TOK = os.environ.get('IG_ACCESS_TOKEN', '').strip()
UID = os.environ.get('IG_USER_ID', '').strip() or 'me'
BASE = os.environ.get('IG_API_BASE', 'https://graph.instagram.com').rstrip('/')
OUT = 'apps/insta/data'
KST = ZoneInfo('Asia/Seoul')


def now_kst():
    return datetime.datetime.now(KST).isoformat(timespec='seconds')


_SHORTCODE_RE = re.compile(r'instagram\.com/(?:p|reel|reels|tv)/([A-Za-z0-9_-]+)')


def _public_cover(permalink):
    """인스타 **공개** 커버 경로로 커버 회수(운영자 260803 "빈칸을 최대한 없애는 방향") — '' = 못 얻음.
    `/p/<shortcode>/media/?size=l`은 로그인 없이 커버 CDN URL로 302 리다이렉트한다(실측 260803: 정상 릴스
    10건 전부 실제 이미지 · 커버 자산이 없는 2건만 `static.cdninstagram.com/rsrc.php/null.jpg` 플레이스홀더).
    Graph가 thumbnail_url을 무성 생략해도 이 경로엔 남아있는 회차가 있어 **독립 소스**로서 값이 있다.
    비인증·토큰 무관 · 결손 릴스에만 1콜 · 타임아웃 10s · 어떤 실패도 '' (fail-soft = 종전 동작)."""
    mo = _SHORTCODE_RE.search(permalink or '')
    if not mo:
        return ''
    url = f'https://www.instagram.com/p/{mo.group(1)}/media/?size=l'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (compatible; nomute-editor/1.0)'})
        with urllib.request.urlopen(req, timeout=10) as r:
            final = r.geturl()
            ctype = (r.headers.get('Content-Type') or '')
        if 'null.jpg' in final or not ctype.startswith('image/'):
            return ''   # 플레이스홀더·비이미지 = 자산 부재
        return final
    except Exception:
        return ''


def _embed_alive(permalink):
    """게시물 임베드 생사 프로브(운영자 260810 "이렇게 에러가 될 경우는 아예 링크를 하지마") → True/False/None(보류).
    인스타는 특정 게시물을 **비로그인 공개 표면 전체**에서 내린다(실측 260810: 같은 IP·같은 순간에 형제 릴스는
    shortcode_media 페이로드 정상 · Dbu6GxQzLjM만 「Instagram 방문」 에러 셸 — /p/·/embed/captioned/ 대안 경로 전멸
    + 공개 커버도 null.jpg 종착 = 260803 커버 결손과 같은 가족). 그 게시물을 뷰어 인앱 팝업이 iframe으로 열면
    인스타 서버의 에러 카드만 그려지므로, 수집 시점에 생사를 도장 찍어 뷰어가 링크 자체를 떼게 한다.
    판정 = 임베드 HTML에 미디어 페이로드 마커 실존(3종 OR = 인스타 마크업 개편 시 오탐 완충 · 실측 260810 =
    정상본 3마커 전부 실림·사망본 전부 0). UA = 실측에 쓴 iOS 사파리(봇 UA는 별도 셸 변형 위험 · _public_cover는
    리다이렉트 종착만 봐서 봇 UA 무방하지만 이 프로브는 본문 마커를 읽는다). 예외·소형 응답 = None = 무도장(fail-open)."""
    mo = _SHORTCODE_RE.search(permalink or '')
    if not mo:
        return None
    url = f'https://www.instagram.com/p/{mo.group(1)}/embed/'
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1',
            'Accept-Language': 'ko-KR,ko;q=0.9'})
        with urllib.request.urlopen(req, timeout=10) as r:
            body = r.read(400000).decode('utf-8', 'replace')
    except Exception:
        return None   # 네트워크·HTTP 실패 = 판정 보류 — 링크 유지(종전 동작)가 안전측
    if ('shortcode_media' in body) or ('EmbedFrame' in body) or ('WatchOnInstagram' in body):
        return True
    if len(body) < 8000:
        return None   # 비정상 소형 응답(차단·챌린지 페이지류) = 보류
    return False


def api(path, **params):
    """1콜 → (json|None, err|None). 네트워크 op 타임아웃 20s(§인프라 b — 무한 행 금지)."""
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
        return None, f"{e.code}/{err.get('code')}: {err.get('message', 'HTTP error')}"
    except Exception as e:
        return None, str(e)


def _bd_empty(bd):
    """분해(breakdowns)가 **알맹이 없는 껍데기**인가 = 결과 칸이 통째로 비었나.
    ⚠ 260811 실사고의 진범 판별자 — Meta는 아직 집계가 안 끝난 기간을 물으면 200에 이런 걸 준다:
       [{"dimension_keys": ["follow_type"]}]   ← 이름만 있고 results 배열 자체가 없다.
    구판은 이 리스트가 truthy라는 이유로 '값을 받았다'로 읽었고, 그래서 260719~260811 사이
    **1,009회 전건이 빈손인데 dropped 경보가 0회**였다(화면 취소 선은 284일 내내 비어 있었다).
    = 이 레포가 반복해 겪은 '관측이 지워지는 병'과 같은 축."""
    if not isinstance(bd, list) or not bd:
        return True
    return not any((b or {}).get('results') for b in bd)


def parse_ins(j):
    """insights 응답 → {지표명: 값}. total_value·시계열 values 양식 모두 원형 보존.
    ⚠ 빈 껍데기 분해는 **획득으로 치지 않는다**(키를 안 만든다) → insights()의 낱개 재시도로 넘어가고,
      그래도 없으면 dropped에 실려 경보가 된다. 조용한 죽음을 가시 경보로 바꾸는 자리."""
    out = {}
    for it in (j or {}).get('data', []):
        name = it.get('name')
        if not name:
            continue
        if 'total_value' in it:
            tv = it['total_value']
            bd, val = tv.get('breakdowns'), tv.get('value')
            if bd is not None and not _bd_empty(bd):
                out[name] = bd
            elif val is not None:
                out[name] = val
            # 둘 다 없거나 껍데기 = 미획득(키 생성 안 함) = 낱개 재시도 → dropped 경보
        elif it.get('values'):
            vals = it['values']
            out[name] = vals if len(vals) > 1 else vals[0].get('value')
    return out


def insights(path, metrics, **params):
    """지표 묶음 조회 — 묶음 실패 OR 묶음 성공이어도 응답 누락분은 낱개 폴백. 반환 = (수집분, 드랍 목록).
    ⚠ Meta는 metric_type별 미지원 지표를 200 응답에서 '무성 생략'한다(260717 실측: 계정 time_series가
    reach만 주고 views·profile_views 등은 조용히 빠뜨림 → 종전 로직은 묶음 200이면 dropped 0으로 통과 →
    daily_series views가 5일간 None인데 아무 경보 없이 방치됨). 교정 = 요청했는데 응답에 없는 지표는 낱개
    재시도(솔로로는 될 수도) → 그래도 없으면 dropped에 명시 = 조용한 누락을 가시 경보로. (미래 개폐 자가 적응.)"""
    j, err = api(path, metric=','.join(metrics), **params)
    got = parse_ins(j) if j is not None else {}
    dropped = []
    for m in [x for x in metrics if x not in got]:   # 묶음에 빠진 지표(실패 = 전부 · 부분 = 누락분)만 낱개 재시도
        j1, e1 = api(path, metric=m, **params)
        g1 = parse_ins(j1) if j1 is not None else {}
        if m in g1:
            got.update(g1)
        else:
            dropped.append(f'{m} ({e1 or "200-응답미포함"})')
    return got, dropped


def main():
    if not TOK:
        print('no-op — IG_ACCESS_TOKEN 미등록(직결 세팅 전 스캐폴드 · 라이브 무영향). 세팅 = docs/인스타_직결_세팅.md')
        return 0
    os.makedirs(OUT, exist_ok=True)

    prof, err = api(UID, fields='id,username,name,account_type,followers_count,follows_count,media_count')
    if prof is None:
        print(f'::error::프로필 조회 실패 — {err} · 토큰 만료(60일)/권한 의심 → docs/인스타_직결_세팅.md §6 재발급')
        return 1
    uid = prof.get('id') or UID

    acc, drop1 = insights(
        f'{uid}/insights',
        ['views', 'reach', 'profile_views', 'accounts_engaged', 'total_interactions',
         'likes', 'comments', 'shares', 'saves', 'replies'],
        period='day', metric_type='total_value')
    day0 = datetime.datetime.now(KST).replace(hour=0, minute=0, second=0, microsecond=0)
    now_ep0 = int(datetime.datetime.now(KST).timestamp())
    # 신규 팔로우 일별 = 창 명시(운영자 260811 실사고 봉합) — 구판은 무인자 호출이라 Meta가 **최근 2일 버킷만**
    # 주는데 그 2일이 집계 미완결이라 **전부 0**이었다(실측: 뷰어 일별 신규가 8/04~8/11 전건 0 · 창을 30일로
    # 명시하니 81·105·47·90·62·127로 멀쩡히 나온다). 260809에 접속 실측(online_followers)이 똑같은 병을
    # 창 명시로 고쳤는데 이 지표는 안 따라왔다 = 「같은 병의 형제를 놓친」 축(check_seal_completeness 겨냥 모양).
    fc, _ = insights(f'{uid}/insights', ['follower_count'], period='day',
                     since=str(now_ep0 - 30 * 86400), until=str(now_ep0))
    # 팔로우/취소 분해(운영자 260719 Q171 · 260811 재봉합) — 취소 = 게시물별로는 API에 아예 없고 이 계정 일별이 유일 원천.
    # ⚠ 260811 실측으로 진범 확정 = **창 위치**. 이 지표는 집계가 48시간 지연돼 어제·당일을 물으면 200에
    #   빈 껍데기(`[{"dimension_keys":["follow_type"]}]`)만 온다 → 구판은 어제 하루창만 물어서 260719 이후
    #   **1,009회 전건 빈손**이었고 껍데기가 성공으로 통과해 경보도 0회였다(뷰어 취소 선 284일 결측).
    #   실호출 실측: 1일 전 빈손 · 2일 전 127/74 · 3일 전 62/47 · 30일 전 264/94 · 90일 전 45/84 · **180일 전 193/56**
    #   = 지연 경계 48h · 보관 경계는 최소 180일(문서상 90일보다 길다 · 그 너머는 미확인).
    # → 하루창을 **원장에 누적**한다(통창은 합계만 줘서 일별로 못 쪼갠다 = 하루창 반복이 유일한 길).
    #   매 런 = 결측일만 최대 FOLLOW_MAX_CALL콜(있는 날은 안 묻는다 = 하트비트 30분 런에도 평시 0~2콜) ·
    #   소급 = 환경변수 IG_FOLLOW_BACKFILL 일수(1회성 · 180이면 180콜). online_ledger.json 누적 관용구 계승.
    # ⚠⚠ 창은 **KST 자정 기준**이다. 이게 실측으로 확정된 유일한 정답이다.
    #   경위 = Meta 응답의 end_time이 전건 `T07:00:00+0000`(=16:00 KST)라, 평의회 1번이 "인스타의 하루는
    #   자정이 아니라 오후 4시에 끊기니 창도 07:00 UTC에 맞춰야 한다"고 판단했고 그대로 한 회차를 돌렸다.
    #   **실호출 결과 그 정렬이 틀렸다** — 178일을 회수해 기존 실측과 대조하니 전건 과대였다:
    #     날짜        follower_count   KST자정창   07:00Z창
    #     2026-08-04        81            81         263
    #     2026-08-07        90            90         137
    #     2026-08-08        62            62         152
    #     2026-08-09       127           127         189
    #   KST 자정 창은 follower_count와 **3/3 정확 일치**하고(7일 통창 합 512도 일별 합 512와 일치),
    #   07:00Z 창은 4/4 전건 과대다. Meta는 since/until을 받으면 그 범위에 걸치는 버킷을 알아서 고르는데,
    #   경계에 정확히 맞춘 창이 오히려 인접 버킷까지 물어 이중 계상되는 것으로 보인다(원인은 **미확인**).
    #   → **실측이 이긴다.** 창 = KST 자정, 라벨 = 창 시작 날짜(= follower_count end_time 날짜와 같은 축).
    #   ⚠ 다만 평의회 1번의 관찰 자체는 유효하다 — 그 버킷의 실제 시간 범위는 16시~16시이므로,
    #     **게시물을 이 날짜에 귀속시킬 때는** 16시 경계를 따져야 한다(그건 판정 단계 몫 · 수집은 라벨만 맞춘다).
    FOLLOW_LAG = 3            # 집계 지연(일) — 이 날짜 이후는 물어도 빈손이라 요청 자체를 안 한다.
    #   실측 지연은 48시간(어제=빈손·2일 전부터 값)인데 **3으로 잡는다** = 경계에 딱 붙이면 아직 안 익은 날을
    #   매 런 물어 빈손을 받고, 그 빈손이 새 경보 문법(_bd_empty)에 걸려 **정당한 지연이 매 런 빨간불**이 된다
    #   (평의회 6번 경고 — 그 빨간불은 다음 세션이 "껍데기 판정이 과하다"며 봉합을 되돌리는 압력이 된다).
    FOLLOW_KEEP = 400         # 원장 보관 일수(online_ledger 동값)
    FOLLOW_MAX_CALL = 8       # 평시 런 1회 상한(결측 자가치유 속도 · 소급은 아래 환경변수로 별도)
    # 원장 판번호 — 창 정렬·값 의미가 바뀌면 올린다. 다르면 **통째로 버리고 재수집**한다.
    # ⚠ 이게 없으면 잘못 채워진 회차가 영영 산다(원장은 "있는 날짜는 안 묻는다"가 규칙이라 자가 교정이 안 된다).
    #   실제로 260811에 07:00 UTC 정렬로 178일을 채웠다가 전건 과대(81→263 등)로 폐기했다 = 판번호 2의 사유.
    FLED_VER = 2
    fled_p = f'{OUT}/follow_ledger.json'
    try:
        fled = json.load(open(fled_p, encoding='utf-8'))
        assert isinstance(fled, dict)
    except Exception:
        fled = {}
    if fled.get('_ver') != FLED_VER:
        if fled:
            print(f'[팔로우/취소] 원장 판번호 불일치({fled.get("_ver")}→{FLED_VER}) — {len(fled)}건 폐기 후 재수집')
        fled = {'_ver': FLED_VER}
    try:
        back = max(0, int(os.environ.get('IG_FOLLOW_BACKFILL', '0') or 0))
    except ValueError:
        back = 0
    span = max(back, FOLLOW_LAG + FOLLOW_MAX_CALL)
    cap = back if back else FOLLOW_MAX_CALL
    want = []
    for k in range(FOLLOW_LAG, span + 1):
        # 창 = [day0−k일, day0−(k−1)일] KST · 라벨 = 창 시작 날짜(실측상 follower_count end_time 날짜와 일치)
        dd = (day0 - datetime.timedelta(days=k)).date().isoformat()
        if dd not in fled:
            want.append((k, dd))
        if len(want) >= cap:
            break
    drop4, fu_new = [], 0
    for k, dd in want:
        g, dr = insights(f'{uid}/insights', ['follows_and_unfollows'],
                         period='day', metric_type='total_value', breakdown='follow_type',
                         since=str(int((day0 - datetime.timedelta(days=k)).timestamp())),
                         until=str(int((day0 - datetime.timedelta(days=k - 1)).timestamp())))
        raw = g.get('follows_and_unfollows')
        if raw is None:
            # 지연 경계 부근(FOLLOW_LAG+1일 이내)의 빈손은 **정당한 미완결**이라 경보로 안 올린다.
            # 그보다 오래된 날짜가 빈손이면 그건 진짜 결손이므로 dropped에 실어 보이게 한다.
            if k > FOLLOW_LAG + 1:
                drop4 += [f'{x} [{dd}]' for x in dr]
            continue
        rec = {}
        for br in (raw if isinstance(raw, list) else []):
            for res in (br.get('results') or []):
                dv = ' '.join(str(x) for x in (res.get('dimension_values') or [])).upper()
                # ⚠ 값 이름은 FOLLOWER / NON_FOLLOWER / UNKNOWN 이다(실측). 'UNFOLLOW' 같은 낱말은 안 온다 —
                #   구 소비 코드가 'UNFOLLOW' 부분일치로 취소를 찾다가 못 찾고, 그 다음 조건 'FOLLOW'에
                #   **NON_FOLLOWER가 걸려 신규로 둔갑**하던 자리다(값이 왔어도 취소가 신규로 새는 이중 결함).
                if dv == 'NON_FOLLOWER':
                    rec['u'] = res.get('value')
                elif dv == 'FOLLOWER':
                    rec['f'] = res.get('value')
                elif dv:
                    rec[dv.lower()] = res.get('value')
        if rec:
            fled[dd] = rec
            fu_new += 1
    if fled:
        _days = sorted(k2 for k2 in fled if k2 != '_ver')
        for k2 in _days[:-FOLLOW_KEEP]:
            fled.pop(k2, None)
        try:
            with open(fled_p, 'w', encoding='utf-8') as f:
                json.dump(fled, f, ensure_ascii=False, sort_keys=True)
        except Exception as e:
            print(f'follow_ledger 적재 실패(비치명): {e}')
    print(f'[팔로우/취소] 원장 {len(fled) - 1}일치 · 이번 회차 신규 {fu_new}일 · 요청 {len(want)}건'
          + (f' · 소급 {back}일 모드' if back else ''))
    # 접속 실측 = 최근 30일 창 명시(운영자 260809 "제대로 받아오게끔 조치해줘" — 실측 사고 = 8/8·8/9 빈 회신에
    # 원장이 8/7에서 정지·7일 고정). ⚠ 무인자 호출은 Meta가 **최근 ~2일 버킷만** 준다 → 공회신이 3일 이상 이어지면
    # 그 사이 날짜는 영영 복구 불가(다음 런도 다시 최근 2일만 본다 = 구멍이 원장에 영구히 남고 요일 표본이 요일당
    # 1일에 갇힌다 = 요일 노란선이 일자로 죽는 진짜 원인). online_followers 보관창 = 최근 30일(Meta) → 창을 명시해
    # 결측일을 소급 회수 = 바로 아래 일별 time_series '지난 3일 창 = 결측일 자가치유' 관용구 계승(창작 0).
    # 창 회신이 전부 빈 값이면 종전 무인자 호출로 폴백 = 회귀 0(fail-soft).
    now_ep = int(datetime.datetime.now(KST).timestamp())
    onl, _ = insights(f'{uid}/insights', ['online_followers'], period='lifetime',
                      since=str(now_ep - 30 * 86400), until=str(now_ep))
    _ob = onl.get('online_followers')
    if not any(isinstance((b or {}).get('value'), dict) and (b or {}).get('value')
               for b in (_ob if isinstance(_ob, list) else [])):
        onl2, _ = insights(f'{uid}/insights', ['online_followers'], period='lifetime')
        if onl2.get('online_followers'):
            onl = onl2
    # 일별 버킷(time_series · 운영자 260713 일일 추이) — since/until 명시 = 진짜 달력일 배열.
    # 지난 3일 창 = 결측일 자가치유 · 미지원 지표 = insights() 낱개 폴백이 dropped 기록 = fail-soft(기존 수집 무접촉).
    ts, drop3 = insights(
        f'{uid}/insights',
        ['views', 'reach', 'profile_views', 'accounts_engaged', 'total_interactions'],
        period='day', metric_type='time_series', since=str(now_ep - 3 * 86400), until=str(now_ep))

    demo, drop2 = {}, []
    for br in ('age,gender', 'country', 'city'):
        d, dr = insights(f'{uid}/insights', ['follower_demographics'], period='lifetime',
                         metric_type='total_value', timeframe='this_month', breakdown=br)
        if d.get('follower_demographics') is not None:
            demo[br] = d['follower_demographics']
        drop2 += dr

    media, merr = api(f'{uid}/media',
                      fields='id,caption,media_type,media_product_type,timestamp,permalink,like_count,comments_count,media_url,thumbnail_url',
                      limit='25')
    items = []
    for m in (media or {}).get('data', []):
        mm = dict(m)
        if isinstance(mm.get('caption'), str):
            mm['caption'] = mm['caption'][:120]
        # 릴스 커버 회수(운영자 260718) — /media 목록 응답이 일부 릴스의 thumbnail_url을 무성 생략(실측 2/25).
        # 누락 시 media_url은 mp4 스트림뿐이라 뷰어 <img>가 깨져 '최근 게시물' 타일이 조용히 사라짐 →
        # 미디어 노드 직접 재조회로 커버 복구(빠진 것만 · 대개 0~2콜) · 그래도 없으면 무접촉(fail-soft).
        if not mm.get('thumbnail_url') and (m.get('media_type') == 'VIDEO' or m.get('media_product_type') == 'REELS'):
            tj, _terr = api(m['id'], fields='thumbnail_url')
            if tj and tj.get('thumbnail_url'):
                mm['thumbnail_url'] = tj['thumbnail_url']
            else:
                # 2차 = **인스타 공개 커버 경로**(운영자 260803 "빈칸을 최대한 없애는 방향") — Graph가 둘 다 빈손인
                # 릴스도 공개 permalink 경로엔 커버가 살아있는 경우가 있다(260803 실측 = 결손 아닌 릴스 10건 전부
                # 이 경로로 정상 CDN 이미지 · 자산 자체가 없는 2건만 null.jpg). 토큰 불요·결손건만 1콜(평시 0~2).
                # 채택 조건 = 리다이렉트 종착이 **CDN 이미지**(null.jpg 플레이스홀더 = 자산 부재 = 버림).
                pub = _public_cover(m.get('permalink'))
                if pub:
                    mm['thumbnail_url'] = pub
                    mm['thumb_src'] = 'pub'   # 출처 표식(운영자 260803 카운터) — 편입 뒤엔 thumbnail_url과 구분이 안 되므로
                    #                           여기서만 남길 수 있다. 어느 층이 실제로 일하는지 = insta_signals가 집계.
        base = ['views', 'reach', 'likes', 'comments', 'saved', 'shares', 'total_interactions']
        if m.get('media_product_type') == 'REELS':
            base += ['ig_reels_avg_watch_time', 'ig_reels_video_view_total_time']
        else:
            # 게시물이 데려온 신규 팔로우·프로필 방문(운영자 260811 "게시물당 팔로워 취소가 중요하다" —
            # 취소는 게시물별로 API에 아예 없고, 그 목적("어떤 게시물이 결이 안 맞나")에 실제로 답하는 건
            # 이 두 값이다. 실측 = 신규 48·26명 · 방문 292·270회 · 도달 1만당 신규가 0.3~1.7로 5.7배 갈린다).
            # ⚠ 릴스 제외는 취향이 아니라 API 제약이다 — 실호출 실측에서 릴스는 전건 400을 준다:
            #   "The Media Insights API does not support the follows metric for this media product type."
            #   묶음에 그냥 넣으면 릴스마다 묶음이 통째로 실패하고 insights()가 지표를 낱개로 다시 물어
            #   **회차당 요청이 25→100회대로 뛴다**(평의회 7번 지적) → 형식으로 갈라 애초에 안 묻는다.
            # ⚠ 이 채널은 피드 491 : 릴스 493이라 이 축은 구조적으로 **게시물의 절반만** 덮는다.
            #   릴스 쪽 대체 축은 별건(시청 유지·이탈률) = 미착수. 덮지 못하는 절반을 덮은 척하지 않는다.
            base += ['follows', 'profile_visits']
        mi, _ = insights(f"{m['id']}/insights", base)
        mm['insights'] = mi
        items.append(mm)

    # 임베드 생사 도장(운영자 260810 "이렇게 에러가 될 경우는 아예 링크를 하지마") — 최근 12개(= 뷰어 타일 표본)만.
    # 사망 확정분만 embed_dead=1 · 판정 불가(None) = 무도장 = 뷰어 종전 링크(fail-open).
    # ⚠ 전멸 가드 = 프로브 성립분이 전건 사망이면 게시물 축이 아니라 환경 축(로그인월·러너 IP 차단·마크업 개편)
    #   → 전건 무도장. 멀쩡한 채널의 타일 12개 링크를 한 방에 다 떼는 오탐이 이 층의 최대 리스크라 그 방향만 구조로 막는다.
    _prb = _dead = 0
    for mm in items[:12]:
        _st = _embed_alive(mm.get('permalink'))
        if _st is None:
            continue
        _prb += 1
        if not _st:
            mm['embed_dead'] = 1
            _dead += 1
        time.sleep(.3)   # 12콜 연사 완화(공개 커버 프로브 0~2콜 대비 콜 수가 많다)
    if _prb and _dead == _prb:
        for mm in items[:12]:
            mm.pop('embed_dead', None)
        print(f'[embed] 프로브 전멸({_dead}/{_prb}) = 환경 축 판정 → 전건 무도장(fail-open)')
    elif _dead:
        print(f'[embed] 임베드 사망 도장 {_dead}/{_prb}건')

    stamp = now_kst()
    dropped = drop1 + drop2 + drop3 + drop4
    with open(f'{OUT}/insights_daily.jsonl', 'a', encoding='utf-8') as f:
        f.write(json.dumps({'fetched_kst': stamp, 'profile': prof, 'account_day': acc,
                            'follower_count_series': fc.get('follower_count'),
                            # 팔로우/취소는 이제 날짜별 원장(follow_ledger.json)이 정본이다 — 여기엔 회차 요약만 남긴다.
                            # 구판은 '어제 하루창 원본'을 매 회차 통째로 박았는데 그 창이 항상 빈손이라 1,009줄이 껍데기였다.
                            'follows_led': {'days': len(fled) - 1, 'new': fu_new,
                                            'last': (max((k2 for k2 in fled if k2 != '_ver'), default=None))},
                            'account_daily': ts,
                            'dropped': dropped}, ensure_ascii=False) + '\n')
    with open(f'{OUT}/media_latest.json', 'w', encoding='utf-8') as f:
        json.dump({'fetched_kst': stamp, 'media_error': merr, 'media': items}, f, ensure_ascii=False, indent=1)
    with open(f'{OUT}/audience.json', 'w', encoding='utf-8') as f:
        json.dump({'fetched_kst': stamp, 'follower_demographics': demo,
                   'online_followers': onl.get('online_followers')}, f, ensure_ascii=False, indent=1)

    # 접속 실측 원장(운영자 260803 "내 팔로워 접속 실측 붙이면 매우 좋을듯" — 뷰어 실측 곡선·요일 축적의 원천) —
    # online_followers 일버킷(시각 = PT 로컬 · 판정 260803 insta_signals._pt_kst_shift — 원문 그대로 보존, KST 변환 = 분석기 몫)을 날짜 키로 병합 누적. audience.json은 매 런 덮어써 최신 ~2일뿐이라
    # 누적 없인 요일별 실측이 영영 불가. 원문 보존(KST 변환 = 분석기 몫) · 같은 날 재수집 = 최신 덮음 · 400일 컷(비대 방지) · 실패 = 종전 산출 무피해.
    try:
        led_p = f'{OUT}/online_ledger.json'
        try:
            led = json.load(open(led_p, encoding='utf-8'))
            assert isinstance(led, dict)
        except Exception:
            led = {}
        raw_onl = onl.get('online_followers')
        for b in (raw_onl if isinstance(raw_onl, list) else []):
            v, et = (b or {}).get('value'), ((b or {}).get('end_time') or '')[:10]
            if isinstance(v, dict) and v and len(et) == 10:
                led[et] = v
        if led:
            for k in sorted(led)[:-400]:
                led.pop(k, None)
            with open(led_p, 'w', encoding='utf-8') as f:
                json.dump(led, f, ensure_ascii=False)
    except Exception as e:
        print(f'online_ledger 적재 실패(비치명 · 곡선은 audience 스냅샷 폴백): {e}')

    # 토큰 나이 경보 — 장수명 토큰 60일 만료 · 50일부터 warning (원문 대신 sha256 꼬리만 저장)
    meta_p = f'{OUT}/token_meta.json'
    tid = hashlib.sha256(TOK.encode()).hexdigest()[:12]
    try:
        meta = json.load(open(meta_p, encoding='utf-8'))
    except Exception:
        meta = {}
    if meta.get('token_hash') != tid:
        meta = {'token_hash': tid, 'first_seen_kst': stamp}
        with open(meta_p, 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False)
    else:
        age = (datetime.datetime.now(KST) - datetime.datetime.fromisoformat(meta['first_seen_kst'])).days
        if age >= 50:
            print(f'::warning::IG 토큰 관측 {age}일 경과(만료 60일) — 세팅 가이드 §6 재발급 권장')

    print(f"OK — @{prof.get('username')} 팔로워 {prof.get('followers_count')} · "
          f"계정지표 {len(acc)}종 · 미디어 {len(items)}건 · 드랍 {len(dropped)}종{' · ' + '; '.join(dropped[:3]) if dropped else ''}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
