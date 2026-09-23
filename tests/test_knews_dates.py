# 국내 RSS 날짜 표기 회귀(260923) — 표준 파서가 못 읽어 세계일보·파이낸셜뉴스 기사 14%가 발행시각 없이 들어오고,
#   노컷뉴스는 dc:date 0001년 자리표시를 발행으로 읽어 전 기사가 24h 창 밖(= 죽은 피드)으로 보이던 것 · 네트워크 0
import importlib.util, sys, types, unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scraper"))
for _name in ("feedparser", "requests"):
    try:
        __import__(_name)
    except ImportError:
        sys.modules[_name] = types.ModuleType(_name)
_spec = importlib.util.spec_from_file_location("knews_dates", ROOT / "scraper" / "knews_scraper.py")
K = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(K)
UTC = timezone.utc


class RawDateTest(unittest.TestCase):
    def test_no_space_after_comma(self):   # 세계일보·파이낸셜뉴스
        self.assertEqual(K.parse_time({"published": "Wed,23 Sep 2026 21:00:00 +0900"}), datetime(2026, 9, 23, 12, 0, tzinfo=UTC))

    def test_numeric_month_and_placeholder_year(self):   # 노컷뉴스
        e = {"published": "Wed, 23 09 2026 21:14:11 +0900", "updated_parsed": (1, 1, 1, 0, 0, 0, 0, 1, 0)}
        self.assertEqual(K.parse_time(e), datetime(2026, 9, 23, 12, 14, 11, tzinfo=UTC))

    def test_compact_and_missing_timezone(self):
        self.assertEqual(K.parse_time({"published": "20260923213257+0900"}), datetime(2026, 9, 23, 12, 32, 57, tzinfo=UTC))
        self.assertEqual(K.parse_time({"published": "Wed,23 Sep 2026 21:00"}), datetime(2026, 9, 23, 21, 0, tzinfo=UTC))   # 시간대 없음 = UTC(표준 파서와 같은 해석 · -9h 는 호스트 보정 몫)
        self.assertEqual(K.parse_time({"published": "Wed,23 Sep 2026 21:00:00 +09:00"}), datetime(2026, 9, 23, 12, 0, tzinfo=UTC))
        self.assertIsNone(K.parse_time({"published": "Wed,23 Sep 2026 21:00:00 +9900"}))

    def test_published_beats_updated(self):
        e = {"published": "Wed,23 Sep 2026 09:00:00 +0900", "updated_parsed": (2026, 9, 23, 12, 0, 0, 2, 266, 0)}
        self.assertEqual(K.parse_time(e), datetime(2026, 9, 23, 0, 0, tzinfo=UTC))


@unittest.skipIf(isinstance(sys.modules.get("feedparser"), types.ModuleType) and not hasattr(sys.modules["feedparser"], "parse"),
                 "feedparser 미설치(CI) — 실제 파서 경로는 수집 러너에서만")
class ThroughFeedparserTest(unittest.TestCase):
    """평의회3-1: 손으로 만든 dict 만 쓰면 표준 파서의 날짜만 남기는 절단(압축형 → 자정)을 못 잡는다."""

    def parse(self, pub):
        import feedparser
        xml = "<rss><channel><item><title>t</title><link>http://x/1</link><pubDate>%s</pubDate></item></channel></rss>" % pub
        return K.parse_time(feedparser.parse(xml).entries[0])

    def test_real_feedparser_path(self):
        self.assertEqual(self.parse("20260923213257+0900"), datetime(2026, 9, 23, 12, 32, 57, tzinfo=UTC))
        self.assertEqual(self.parse("Wed,23 Sep 2026 21:00:00 +0900"), datetime(2026, 9, 23, 12, 0, tzinfo=UTC))
        self.assertEqual(self.parse("Wed, 23 Sep 2026 21:00:00 +0900"), datetime(2026, 9, 23, 12, 0, tzinfo=UTC))   # 정상 표기 = 종전 그대로
        self.assertEqual(self.parse("Wed, 23 09 2026 21:14:11 +0900"), datetime(2026, 9, 23, 12, 14, 11, tzinfo=UTC))

    def test_standard_parse_wins_and_garbage_is_none(self):
        self.assertEqual(K.parse_time({"published_parsed": (2026, 9, 23, 3, 4, 5, 2, 266, 0), "published": "Wed,23 Sep 2026 21:00:00 +0900"}),
                         datetime(2026, 9, 23, 3, 4, 5, tzinfo=UTC))
        self.assertIsNone(K.parse_time({"published": "어제 오후"}))
        self.assertIsNone(K.parse_time({"published": "Mon, 01 Jan 0001 00:00:00 GMT"}))


if __name__ == "__main__":
    unittest.main()
