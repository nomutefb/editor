# X 트렌드 파서(sns_trends.x_trends) — trends24 첫 시간대 순위 목록만 읽는다(운영자 260929 · 구판은 `<li><a` 패턴이라
# 순위 목록(`<li><span><a>`)을 한 줄도 못 잡고 아래 통계 칸의 장기 체류 광고어만 읽었다 · 네트워크 0)
import importlib.util, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("sns_trends_x", ROOT / "scraper" / "sns_trends.py")
S = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(S)

PAGE = (
    '<div class=list-container><h3 class=title data-timestamp=1790653455.8>Tue</h3>'
    '<ol class=trend-card__list><li><span class=trend-name><a href="https://twitter.com/search?q=a" class=trend-link>닛몰캐쉬</a></span></li>'
    '<li><span class=trend-name><a href="https://twitter.com/search?q=b" class=trend-link>오하욘사</a></span></li></ol></div>'
    '<div class=list-container><h3 class=title data-timestamp=1790650128.4>Tue</h3>'
    '<ol class=trend-card__list><li><span class=trend-name><a href="#">지난시간말</a></span></li></ol></div>'
    '<section id=stats><ul><li><a href="#">콰삭모짜킹</a></li><li><a href="#">덴티스테</a></li></ul></section>'
)


class XTrendsParse(unittest.TestCase):
    def setUp(self):
        self._get = S._get

    def tearDown(self):
        S._get = self._get

    def test_reads_first_hourly_list_in_rank_order(self):
        S._get = lambda url, *a, **k: PAGE
        self.assertEqual([x["query"] for x in S.x_trends()], ["닛몰캐쉬", "오하욘사"])

    def test_no_list_goes_to_getdaytrends_not_stats(self):
        # 순위 목록이 없으면 trends24 통계 칸(광고어)으로 돌아가지 않고 getdaytrends 로 넘어간다(평의회260929 #3)
        S._get = lambda url, *a, **k: ('<section id=stats><ul><li><a href="#">콰삭모짜킹</a></li></ul></section>' if "trends24" in url
                                       else '<a class="string" href="#">닛몰캐쉬</a><a class="string" href="#">A &amp; B</a>')
        self.assertEqual([x["query"] for x in S.x_trends()], ["닛몰캐쉬", "A & B"])

    def test_single_quoted_and_multi_class_list(self):
        for attr in ("class='trend-card__list'", 'class="x trend-card__list"'):
            S._get = lambda url, *a, attr=attr, **k: f'<ol {attr}><li><span><a href="#">닛몰캐쉬</a></span></li></ol><ul><li><a>광고</a></li></ul>'
            self.assertEqual([x["query"] for x in S.x_trends()], ["닛몰캐쉬"], attr)
