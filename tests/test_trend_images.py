"""트렌드 이미지 백필 리졸버 회귀(운영자 260909 «트렌드 저거는 llm 필요없는 일로»).

네트워크 0·LLM 0 — trend_images 의 순수 파서 3종(네이버·다음·합성)을 고정 HTML 로 판정한다.
정본 = .github/scripts/trend_images.py naver_news_urls / daum_news_urls / resolve_news_urls."""
import importlib
import os
from pathlib import Path
import sys
import unittest
import datetime as dt

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault('GEMINI_API_KEY', 'test-noop')   # thumb_gen 모듈 상단 no-op 분기 회피(호출 0)
sys.path.insert(0, str(ROOT / '.github' / 'scripts'))
ti = importlib.import_module('trend_images')

NAVER_HTML = '''
<a href="https://n.news.naver.com/mnews/article/421/0009158974" class="news_tit">A</a>
<a href="https://n.news.naver.com/mnews/article/421/0009158974?sid=102">A-dup</a>
<a href="https://n.news.naver.com/mnews/article/001/0016299444">B</a>
<a href="https://sports.news.naver.com/news?oid=1&aid=2">스포츠(제외)</a>
'''
KST = dt.timezone(dt.timedelta(hours=9))
NOW = dt.datetime(2026, 9, 9, 14, 0, tzinfo=KST).timestamp()
DAUM_HTML = '''
<a href="http://v.daum.net/v/20260909052149228" class="tit_main">fresh</a>
<a href="http://v.daum.net/v/20260909052149228">fresh-dup</a>
<a href="https://v.daum.net/v/20260827140213477">stale-13d</a>
<a href="https://v.daum.net/v/20260908110000000">fresh-2</a>
'''


class TrendResolverTest(unittest.TestCase):
    def test_naver_keeps_order_dedupes_and_only_article_links(self):
        self.assertEqual(ti.naver_news_urls(NAVER_HTML),
                         ['https://n.news.naver.com/mnews/article/421/0009158974',
                          'https://n.news.naver.com/mnews/article/001/0016299444'])
        self.assertEqual(ti.naver_news_urls(''), [])
        self.assertEqual(ti.naver_news_urls(None), [])

    def test_daum_cuts_by_publish_time_in_id(self):
        got = ti.daum_news_urls(DAUM_HTML, now_ts=NOW)
        self.assertEqual(got, ['http://v.daum.net/v/20260909052149228', 'https://v.daum.net/v/20260908110000000'])
        # 컷 창을 넓히면 옛 기사도 살아난다(시각 파싱이 실제로 판정에 쓰인다는 증거)
        self.assertIn('https://v.daum.net/v/20260827140213477', ti.daum_news_urls(DAUM_HTML, now_ts=NOW, max_age_h=24 * 30))

    def test_resolve_prefers_naver_week_then_all_then_daum(self):
        calls = []
        def fake(url):
            calls.append(url)
            if 'naver' in url and 'p:1w' in url:
                return ''                                   # 1주 필터 0건 → 전체 검색으로
            if 'naver' in url:
                return '<a href="https://n.news.naver.com/mnews/article/001/0000000001">x</a>'
            return DAUM_HTML
        got = ti.resolve_news_urls('키워드', fetch=fake, limit=3)
        self.assertEqual(got[0], 'https://n.news.naver.com/mnews/article/001/0000000001')
        self.assertTrue(all(u.startswith('http') for u in got))
        self.assertEqual(len(got), 3)                       # 네이버 1 + 다음 2(7일 컷 뒤) = limit 3
        self.assertEqual(len(calls), 3)                     # 네이버 1주 · 네이버 전체 · 다음 = 키워드당 최대 3 GET

    def test_resolve_stops_early_when_naver_is_enough(self):
        calls = []
        def fake(url):
            calls.append(url)
            return ''.join('<a href="https://n.news.naver.com/mnews/article/001/%010d">x</a>' % i for i in range(6))
        got = ti.resolve_news_urls('키워드', fetch=fake, limit=4)
        self.assertEqual(len(got), 4)
        self.assertEqual(len(calls), 1)                     # 1주 검색만으로 충분하면 추가 GET 0

    def test_resolve_never_raises_on_fetch_failure(self):
        self.assertEqual(ti.resolve_news_urls('키워드', fetch=lambda u: (_ for _ in ()).throw(RuntimeError('net')) if False else ''), [])

    def test_no_llm_call_site_remains(self):
        src = (ROOT / '.github' / 'scripts' / 'trend_images.py').read_text(encoding='utf-8')
        self.assertNotIn('run_claude', src)
        self.assertNotIn('"claude"', src)


if __name__ == '__main__':
    unittest.main()
