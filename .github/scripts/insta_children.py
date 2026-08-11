#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""인스타 캐러셀 낱장(children) 백필 — 페이지네이션 + children field expansion · LLM 0콜 · stdlib only.

배경(운영자 260811 "낱장 조회하고 기존거 더 꺼내자, 카드뉴스 손보려고함"): 카드뉴스(묶음 게시물)의
2페이지~N페이지(하단 본문 4줄 카드)는 Graph 목록 콜 기본 필드에 없고, 공개 커버 경로(/p/<code>/media/)와
임베드 문서도 표지(1장째)만 준다(실측 260811 — 임베드 HTML엔 낱장 데이터 자체가 안 실림). 유일한 축 =
토큰으로 children 확장을 실어오는 것. insta_backfill.py의 목록 페이지네이션 문법을 그대로 계승하되
insights 확장 대신 children{...} 확장을 싣는다(낱개 /{media-id}/children 490여 콜 대신 ~20콜).

산출: apps/insta/data/media_children.json {fetched_kst, n_media, n_carousels,
      media:[{id,permalink,timestamp,media_type,children:[{id,media_type,media_url,thumbnail_url}]}]}
      — 낱장이 실제로 있는 묶음(CAROUSEL_ALBUM)만 저장(파일 슬림 · media_url = 수집 시점 CDN URL이라
      oe= 만료가 있다 → 소비는 수집 직후가 정본, 만료분은 재발사로 갱신).
게이트: IG_ACCESS_TOKEN 미등록 = no-op exit 0(시크릿 게이트 스캐폴드 관례 = insta_backfill 계승).
발사 = insta-fetch.yml workflow_dispatch(children=true). 커밋 = 기존 1차 커밋 스텝(apps/insta/data 통째)에 편승.
fail-soft: 페이지 실패 = 그 지점까지 저장(백필 관례) · children 결손 노드 = 건너뜀(오류 아님).
"""
import datetime
import json
import os
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
MAX_PAGES = int(os.environ.get('CHILDREN_MAX_PAGES', '60'))   # 50개/페이지 × 60 = 3,000개 상한(백필 동값)
PAGE_SLEEP = float(os.environ.get('CHILDREN_SLEEP', '1.0'))   # 콜 간 여유(레이트 보수 · 백필 동값)

FIELDS = ('id,media_type,timestamp,permalink,'
          'children{id,media_type,media_url,thumbnail_url}')


def get(url):
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            return json.load(r), None
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read().decode('utf-8', 'replace'))
        except Exception:
            body = {}
        return None, f"{e.code}: {(body.get('error') or {}).get('message', 'HTTP error')}"
    except Exception as e:
        return None, str(e)


def main():
    if not TOK:
        print('IG_ACCESS_TOKEN 미등록 — no-op(스캐폴드)')
        return 0
    url = (f'{BASE}/{UID}/media?' +
           urllib.parse.urlencode({'fields': FIELDS, 'limit': 50, 'access_token': TOK}))
    media, pages, err_last = [], 0, None
    while url and pages < MAX_PAGES:
        j, err = get(url)
        if err or not j:
            err_last = err
            print(f'페이지 {pages + 1} 실패: {err} — 그 지점까지 저장(fail-soft)')
            break
        for m in (j.get('data') or []):
            ch = ((m.get('children') or {}).get('data')) or []
            if not ch:
                continue   # 낱장 없는 노드(단일 사진·영상) = 저장 제외(파일 슬림)
            media.append({
                'id': m.get('id'),
                'media_type': m.get('media_type'),
                'timestamp': m.get('timestamp'),
                'permalink': m.get('permalink'),
                'children': [{
                    'id': c.get('id'),
                    'media_type': c.get('media_type'),
                    'media_url': c.get('media_url'),
                    'thumbnail_url': c.get('thumbnail_url'),
                } for c in ch],
            })
        pages += 1
        url = ((j.get('paging') or {}).get('next'))
        if url:
            time.sleep(PAGE_SLEEP)
    os.makedirs(OUT, exist_ok=True)
    out = {
        'fetched_kst': datetime.datetime.now(KST).isoformat(timespec='seconds'),
        'pages': pages,
        'n_carousels': len(media),
        'n_children': sum(len(m['children']) for m in media),
        'err_last': err_last,
        'media': media,
    }
    with open(f'{OUT}/media_children.json', 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f'낱장 백필: 묶음 {len(media)}건 · 낱장 {out["n_children"]}장 · {pages}페이지')
    return 0


if __name__ == '__main__':
    sys.exit(main())
