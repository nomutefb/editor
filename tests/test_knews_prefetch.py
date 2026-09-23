# 수집기 호스트 병렬 수집·시각 보정 회귀 — 네트워크 0(fetch_feed 스텁) · CI 는 feedparser/requests 미설치라 빈 모듈로 대체
import importlib.util, sys, threading, time, types, unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
KN = ROOT / "scraper" / "knews_scraper.py"
sys.path.insert(0, str(ROOT / "scraper"))
for _name in ("feedparser", "requests"):
    try:
        __import__(_name)
    except ImportError:
        sys.modules[_name] = types.ModuleType(_name)


def _load():
    spec = importlib.util.spec_from_file_location("knews_mod", KN)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


FEEDS = [{"publisher": p, "title": str(i), "categories": "_all_", "url": f"https://{h}/rss/{i}.xml"}
         for i, (p, h) in enumerate([("A", "a.kr"), ("B", "b.kr"), ("A", "a.kr"), ("C", "c.kr"), ("B", "b.kr"), ("A", "a.kr")])]


class PrefetchTest(unittest.TestCase):
    def run_prefetch(self, workers):
        m = _load()
        m.FEED_DELAY = 0.02
        m.FETCH_HOSTS = workers
        calls, lock = [], threading.Lock()

        def fake(feed):
            t0 = time.monotonic()
            time.sleep(0.03)
            with lock:
                calls.append((feed["url"].split("/")[2], t0, time.monotonic()))
            return "P:" + feed["url"]
        with mock.patch.object(m, "fetch_feed", fake):
            out = m.prefetch(FEEDS)
        return out, calls

    def test_output_keeps_feeds_csv_order(self):
        out, _ = self.run_prefetch(16)
        self.assertEqual(out, ["P:" + f["url"] for f in FEEDS])

    def test_same_host_never_overlaps(self):
        _, calls = self.run_prefetch(16)
        by_host = {}
        for h, s, e in calls:
            by_host.setdefault(h, []).append((s, e))
        for h, spans in by_host.items():
            spans.sort()
            for (s1, e1), (s2, _) in zip(spans, spans[1:]):
                self.assertGreaterEqual(s2, e1, f"{h} 동시 요청 = 서버 매너 위반")

    def test_different_hosts_run_concurrently(self):
        _, calls = self.run_prefetch(16)
        first = {}
        for h, s, _ in calls:
            first[h] = min(first.get(h, s), s)
        self.assertLess(max(first.values()) - min(first.values()), 0.03)   # 세 호스트 첫 요청이 거의 동시에 출발

    def test_single_worker_is_serial(self):
        _, calls = self.run_prefetch(1)
        spans = sorted((s, e) for _, s, e in calls)
        for (s1, e1), (s2, _) in zip(spans, spans[1:]):
            self.assertGreaterEqual(s2, e1)


class KstSkewTest(unittest.TestCase):
    """평의회7: 한국시각을 +00:00 으로 박는 CMS → 기사가 9h 미래 → 대표 선정·burst 어긋남 + 단독 1보 만료 후 재입장(9h 늦은 푸시)."""

    def entries(self, *hours_from_now):
        now = datetime.now(timezone.utc)
        return types.SimpleNamespace(entries=[{"t": now + timedelta(hours=h)} for h in hours_from_now])

    def test_host_with_future_items_is_shifted_whole(self):
        m = _load()
        m.parse_time = lambda e: e["t"]
        now = datetime.now(timezone.utc)
        feeds = [{"url": "https://skew.kr/a.xml"}, {"url": "https://skew.kr/b.xml"}, {"url": "https://ok.kr/a.xml"}]
        parsed = [self.entries(8.5, 3), self.entries(-2), self.entries(-0.5, -3)]
        hosts = m.kst_skew_hosts(feeds, parsed, now)
        self.assertEqual(hosts, {"skew.kr"})                      # 같은 서버 다른 피드(b)도 함께 보정 대상
        fixed = m.fix_time(now - timedelta(hours=2), True, now)   # b 피드의 과거 항목도 -9h
        self.assertAlmostEqual((now - fixed).total_seconds() / 3600, 11, places=3)
        self.assertEqual(m.fix_time(now - timedelta(hours=2), False, now), now - timedelta(hours=2))

    def test_garbage_future_becomes_unknown_time(self):
        m = _load()
        now = datetime.now(timezone.utc)
        self.assertIsNone(m.fix_time(now + timedelta(days=30), False, now))
        self.assertIsNone(m.fix_time(now + timedelta(hours=12), True, now))

    def test_small_clock_drift_is_not_a_skew(self):
        m = _load()
        m.parse_time = lambda e: e["t"]
        now = datetime.now(timezone.utc)
        self.assertEqual(m.kst_skew_hosts([{"url": "https://ok.kr/a.xml"}], [self.entries(0.05, -1)], now), set())

    @mock.patch.dict("os.environ", {"KNEWS_KST_FIX": "0"})
    def test_rollback_lever(self):
        m = _load()
        m.parse_time = lambda e: e["t"]
        now = datetime.now(timezone.utc)
        self.assertEqual(m.kst_skew_hosts([{"url": "https://skew.kr/a.xml"}], [self.entries(8.5)], now), set())


if __name__ == "__main__":
    unittest.main()
