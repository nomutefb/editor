"""구글 뉴스 검색이미지 레인 회귀(운영자 260925 «요약이 완료된 이후에 이미지를 찾게» · «구글 검색만»).

네트워크 0·LLM 0 — gnews_search 의 순수 파서·검색어 사다리·필터를 고정 응답으로 판정하고,
thumb_gen.gnews_topup 이 게이트 OFF·실패 때 기존 결과를 그대로 두는지(fail-soft) 본다.
정본 = .github/scripts/gnews_search.py · .github/scripts/thumb_gen.py gnews_topup/_gn_ready."""
import datetime as dt
import importlib
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault('GEMINI_API_KEY', 'test-noop')   # thumb_gen 모듈 상단 no-op 분기 회피(호출 0)
sys.path.insert(0, str(ROOT / '.github' / 'scripts'))
gn = importlib.import_module('gnews_search')
tg = importlib.import_module('thumb_gen')

KST = dt.timezone(dt.timedelta(hours=9))
NOW = dt.datetime(2026, 9, 25, 12, tzinfo=KST).timestamp()


def _item(title, gid, source, pub='Thu, 25 Sep 2026 01:00:00 GMT'):
    return ('<item><title>{}</title><link>https://news.google.com/rss/articles/{}?oc=5</link>'
            '<pubDate>{}</pubDate><source url="{}">{}</source></item>').format(title, gid, pub, source, source)


RSS = '<rss><channel>' + ''.join([
    _item('소주 섞은 분유 먹이고 강제추행까지…친부 징역 7년 - 뉴시스', 'A1', 'https://mobile.newsis.com'),
    _item('[속보] 소주 분유 친부 징역 7년', 'A2', 'https://www.flash.co.kr'),
    _item('소주 탄 분유 아빠 항소 - 서울신문', 'A3', 'https://amp.seoul.co.kr'),
    _item('소주 분유 사건 또 다른 기사 - 뉴시스', 'A4', 'https://mobile.newsis.com'),
    _item('아빠 징역형 불복 스포츠 - 네이트', 'A5', 'https://sports.news.nate.com'),
    _item('소주 분유 옛 사건 - 옛매체', 'A6', 'https://old.example.com', pub='Mon, 01 Sep 2025 01:00:00 GMT'),
    _item('소주 분유 친부 로이터 - Reuters', 'A7', 'https://www.reuters.com'),
]) + '</channel></rss>'
DECODED = {'A1': 'https://mobile.newsis.com/view.html?ar_id=1', 'A3': 'https://amp.seoul.co.kr/seoul/2',
           'A4': 'https://www.newsis.com/view/?id=4', 'A5': 'https://sports.news.nate.com/view/5',
           'A6': 'https://old.example.com/6', 'A7': 'https://www.reuters.com/7', 'A2': 'https://www.flash.co.kr/2'}
BATCH = (')]}\'\n\n[["wrb.fr","Fbv4je","[\\"garturlres\\",\\"@URL@\\",1]",null,null,null,"generic"],'
         '["di",23],["af.httprm",23,"-848",1]]')


def fake_http(calls=None):
    last = {}

    def http(url, data=None, headers=None, timeout=12):
        if calls is not None:
            calls.append(url)
        if '/rss/search' in url:
            return RSS
        if '/rss/articles/' in url:
            last['gid'] = url.rsplit('/', 1)[1]
            return '<c-wiz><div data-n-a-sg="SIG" data-n-a-ts="1700"></div></c-wiz>'
        if 'batchexecute' in url and last.get('gid') in DECODED and last['gid'] in data.decode():
            return BATCH.replace('@URL@', DECODED[last['gid']])
        return ''
    return http


MD_DOMESTIC = '''---
title: "‘소주 분유’ 먹이고 친딸 성추행한 아빠…징역형에 ‘불복’"
title_ko: ""
date: "2026-09-25"
image_query: "창원지법 밀양지원 소주 분유 아동학대"
image_query_en: ""
image_sources: ""
---
'''
MD_FOREIGN = '''---
title: "Xi skips BRICS dinner"
title_ko: "브릭스 만찬, 시진핑 대신 왕이가 갔다…\\"건강 이상설\\""
date: "2026-09-20"
image_query: "시진핑 브릭스 정상회의"
image_query_en: "Xi Jinping BRICS summit New Delhi Wang Yi"
---
'''


class ParserTest(unittest.TestCase):
    def test_parse_rss_fields_and_pub(self):
        items = gn.parse_rss(RSS)
        self.assertEqual(len(items), 7)
        self.assertEqual(items[0]['link'], 'https://news.google.com/rss/articles/A1?oc=5')
        self.assertEqual(items[0]['source'], 'https://mobile.newsis.com')
        self.assertGreater(items[0]['pub'], 0)
        self.assertEqual(gn.parse_rss(''), [])
        self.assertEqual(gn.parse_rss(None), [])

    def test_article_id_and_sig(self):
        self.assertEqual(gn.article_id('https://news.google.com/rss/articles/CBMiXyz_-1?oc=5'), 'CBMiXyz_-1')
        self.assertEqual(gn.article_id('https://example.com/x'), '')
        self.assertEqual(gn.extract_sig('<div data-n-a-sg="S" data-n-a-ts="123">'), ('S', '123'))
        self.assertIsNone(gn.extract_sig('<div>no sig</div>'))

    def test_parse_batch_real_shape(self):
        self.assertEqual(gn.parse_batch(BATCH.replace('@URL@', 'https://www.donga.com/news/1')), 'https://www.donga.com/news/1')
        self.assertEqual(gn.parse_batch(''), '')
        self.assertEqual(gn.parse_batch(')]}\'\n\n[["di",23]]'), '')
        self.assertEqual(gn.parse_batch('garbage'), '')

    def test_batch_body_carries_id_ts_sig(self):
        b = gn.batch_body('GID', '1700', 'SIG').decode()
        self.assertIn('Fbv4je', b)
        for token in ('GID', '1700', 'SIG'):
            self.assertIn(token, b)


class QueryTest(unittest.TestCase):
    def test_domestic_ladder_iq_then_title(self):
        qs = gn.build_queries(MD_DOMESTIC)
        self.assertEqual(qs[0], ('창원지법 밀양지원 소주 분유', 'ko'))            # 4어절 컷(길수록 0건)
        self.assertEqual(qs[-1], ('창원지법 밀양지원 소주', 'ko'))                # 마지막 = 앞 3어절로 넓힘
        self.assertEqual(qs[1][1], 'ko')
        self.assertNotIn('‘', qs[1][0])
        self.assertTrue(all(lang == 'ko' for _, lang in qs))

    def test_foreign_ladder_english_first_and_backslash_clean(self):
        qs = gn.build_queries(MD_FOREIGN)
        self.assertEqual(qs[0], ('Xi Jinping BRICS summit New Delhi', 'en'))    # 영문 6어절 컷
        self.assertEqual(qs[1], ('시진핑 브릭스 정상회의', 'ko'))
        self.assertNotIn('\\', qs[2][0])          # frontmatter 이스케이프(\") 잔재 제거
        self.assertIn('건강 이상설', qs[2][0])      # title_ko 우선

    def test_non_latin_english_query_is_skipped(self):
        md = '---\nimage_query: "이시바 사임"\nimage_query_en: "石破茂 辞任 東京"\n---\n'
        self.assertEqual([l for _, l in gn.build_queries(md)], ['ko'])
        self.assertFalse(gn.relevant('石破茂 辞任 東京', '전혀 무관한 기사', 'en'))   # 대조 어절 0 = 무관 취급

    def test_example_value_and_empty(self):
        self.assertEqual(gn.build_queries('---\nimage_query: "삼성전자 반도체 평택공장"\n---\n'), [])
        self.assertEqual(gn.build_queries(''), [])

    def test_clean_query_strips_flash_and_caps_words(self):
        self.assertEqual(gn.clean_query('[속보] 한강 “대교” 붕괴'), '한강 대교 붕괴')
        self.assertEqual(len(gn.clean_query(' '.join('w%d' % i for i in range(30))).split()), 12)

    def test_relevance(self):
        self.assertTrue(gn.relevant('창원지법 밀양지원 소주 분유 아동학대', '소주 섞은 분유 먹이고 강제추행까지'))
        self.assertFalse(gn.relevant('소주 분유 먹이고 친딸 성추행한 아빠 징역형에 불복', '아빠 복귀전 스포츠'))
        self.assertTrue(gn.relevant('Xi Jinping BRICS summit New Delhi Wang Yi', 'Xi skips BRICS dinner, Wang Yi attends', 'en'))
        self.assertFalse(gn.relevant('Xi Jinping BRICS summit New Delhi Wang Yi', "Xi Jinping's trip to U.S. marks first state visit", 'en'))

    def test_relevance_prefix_stopwords_headtags(self):
        self.assertTrue(gn.relevant('시진핑 브릭스 정상회의', '시진핑, 브릭스에 AI협력 제안 - 연합뉴스'))          # 조사 흡수
        self.assertTrue(gn.relevant('Lake Tanganyika boat capsize Kalemie', 'Dozens dead as ship capsizes in Lake Tanganyika', 'en'))
        self.assertFalse(gn.relevant('US airstrike Iran Strait of Hormuz', 'Oil tanker traffic resumes through Strait of Hormuz', 'en'))
        self.assertFalse(gn.relevant('단독 해외 출장마다 배우자 동행 숨긴 선관위', '[단독] 선관위 다른 사건 인사 논란'))
        self.assertEqual(gn.clean_query('[단독][포토] 한강 대교'), '한강 대교')
        self.assertEqual(gn.norm_title('소주 분유 아빠…징역형 불복 - 다음'), '소주 분유 아빠 징역형 불복')

    def test_ref_ts_uses_article_date(self):
        self.assertAlmostEqual(gn.ref_ts(MD_DOMESTIC), NOW, delta=1)
        self.assertEqual(gn.ref_ts('---\ndate: ""\n---'), 0)


class SearchTest(unittest.TestCase):
    def test_filters_dedupe_block_age_flash_relevance(self):
        calls = []
        urls = gn.search_urls([('소주 분유 친부', 'ko')], exclude=['https://amp.seoul.co.kr/seoul/2'], limit=10,
                              http=fake_http(calls), pause=0, now_ts=NOW)
        self.assertEqual(urls, ['https://mobile.newsis.com/view.html?ar_id=1'])
        # A2 속보 · A3 제외 URL · A4 같은 매체 · A5 무관 · A6 옛 사건 · A7 차단 매체 = 해제 요청조차 안 보낸 것도 있다
        self.assertFalse(any('/rss/articles/A2' in c for c in calls))
        self.assertFalse(any('/rss/articles/A6' in c for c in calls))
        self.assertFalse(any('/rss/articles/A7' in c for c in calls))

    def test_portal_and_same_title_copies_skipped(self):
        rss = '<rss>' + _item('소주 분유 친부 원문 제목 - 다음', 'A1', 'https://v.daum.net') \
            + _item('소주 분유 친부 원문 제목 - 서울신문', 'A3', 'https://amp.seoul.co.kr') \
            + _item('소주 분유 친부 다른 각도 - 뉴시스', 'A4', 'https://www.newsis.com') + '</rss>'
        base = fake_http()

        def http(url, data=None, headers=None, timeout=12):
            return rss if '/rss/search' in url else base(url, data, headers, timeout)
        gn._RSS_CACHE.clear()
        urls = gn.search_urls([('소주 분유 친부 사본', 'ko')], http=http, pause=0, now_ts=NOW,
                              self_titles=['소주 분유 친부 원문 제목'])
        self.assertEqual(urls, ['https://www.newsis.com/view/?id=4'])   # 포털 사본·원문과 같은 제목(전재) 제외
        gn._RSS_CACHE.clear()

    def test_limit_and_network_failure_is_empty(self):
        self.assertEqual(len(gn.search_urls([('소주 분유 친부', 'ko')], limit=1, http=fake_http(), pause=0, now_ts=NOW)), 1)
        gn._RSS_CACHE.clear()
        self.assertEqual(gn.search_urls([('다른 검색어', 'ko')], http=lambda *a, **k: '', pause=0), [])

    def test_unsafe_decoded_url_rejected(self):
        self.assertEqual(gn.parse_batch(BATCH.replace('@URL@', 'https://ex.com/a\\n::error::x')), '')
        self.assertEqual(gn.parse_batch(BATCH.replace('@URL@', 'https://ex.com/a b')), '')

    def test_consecutive_decode_failures_stop(self):
        calls = []

        def http(url, data=None, headers=None, timeout=12):
            calls.append(url)
            return RSS if '/rss/search' in url else ''
        gn._RSS_CACHE.clear()
        self.assertEqual(gn.search_urls([('소주 분유 친부 다른', 'ko')], http=http, pause=0, now_ts=NOW), [])
        self.assertLessEqual(sum('/rss/articles/' in c for c in calls), 3)

    def test_blocked_stats(self):
        with patch.dict(gn.STATS, {'ok': 0, 'fail': 3}):
            self.assertTrue(gn.blocked())
        with patch.dict(gn.STATS, {'ok': 1, 'fail': 3}):
            self.assertFalse(gn.blocked())
        with patch.dict(gn.STATS, {'ok': 0, 'fail': 0}):
            self.assertFalse(gn.blocked())

    def test_gate_env(self):
        with patch.dict(os.environ, {'GNEWS_IMG': '0'}):
            self.assertFalse(gn.enabled())
        with patch.dict(os.environ, {'GNEWS_IMG': '1'}):
            self.assertTrue(gn.enabled())


class ThumbLaneTest(unittest.TestCase):
    def setUp(self):
        fd, self.md = tempfile.mkstemp(suffix='.md')
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(MD_DOMESTIC)

    def tearDown(self):
        os.remove(self.md)

    def test_gate_off_keeps_cand_and_ready_false(self):
        cand = [{'src': 'https://i/a.jpg', 'link': 'https://a', 'label': ''}]
        with patch.dict(os.environ, {'GNEWS_IMG': '0'}):
            self.assertEqual(tg.gnews_topup(self.md, list(cand)), cand)
            self.assertFalse(tg._gn_ready(self.md))
        with patch.dict(os.environ, {'GNEWS_IMG': '1'}):
            self.assertTrue(tg._gn_ready(self.md))

    def test_topup_merges_dedupes_and_labels(self):
        cand = [{'src': 'https://i/a.jpg', 'link': 'https://a', 'label': ''}]
        more = [{'src': 'https://i/a.jpg', 'link': 'https://b', 'label': ''},
                {'src': 'https://i/c.jpg', 'link': 'https://c', 'label': ''}]
        with patch.dict(os.environ, {'GNEWS_IMG': '1'}), \
                patch.object(gn, 'search_urls', return_value=['https://b', 'https://c']) as su, \
                patch.object(tg, '_url_ok', return_value=True), \
                patch.object(tg, 'fetch_article_images', return_value=more):
            out = tg.gnews_topup(self.md, list(cand), exclude=['https://a'])
        self.assertEqual([c['src'] for c in out], ['https://i/a.jpg', 'https://i/c.jpg'])
        self.assertEqual(out[1]['label'], '유사')
        self.assertIn('https://a', su.call_args.kwargs['exclude'])

    def test_full_cand_skips_search_and_errors_are_soft(self):
        full = [{'src': 'https://i/%d.jpg' % i, 'link': 'https://l%d' % i, 'label': ''} for i in range(7)]
        with patch.object(gn, 'search_urls') as su:
            self.assertEqual(tg.gnews_topup(self.md, list(full)), full)
            su.assert_not_called()
        with patch.dict(os.environ, {'GNEWS_IMG': '1'}), patch.object(gn, 'search_urls', side_effect=RuntimeError('boom')):
            self.assertEqual(tg.gnews_topup(self.md, []), [])


if __name__ == '__main__':
    unittest.main()
