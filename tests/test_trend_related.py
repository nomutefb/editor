# 급상승 알림 관련 뉴스 매칭(운영자 260924 ⑦ SNS·뉴스 따로 놀던 것) — 뷰어 snsBuzz 규칙 사본 · 24h 창 · 교차 큰 것 · 네트워크 0
import importlib.util, unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("trend_watch_t", ROOT / ".github" / "scripts" / "trend_watch.py")
T = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(T)
NOW = datetime(2026, 9, 24, 3, 0, tzinfo=timezone.utc)


def c(u, title, cross, h):
    return {"url": u, "event_key": u, "title": title, "cross": cross, "first_seen": (NOW - timedelta(hours=h)).isoformat()}


class RelatedTest(unittest.TestCase):
    def test_short_keyword_needs_word_or_josa(self):
        self.assertTrue(T.kw_hit("승리", "[단독] '소주병 집어든' 승리, 말리는 일행"))
        self.assertTrue(T.kw_hit("승리", "승리가 소주병 들고 위협"))
        self.assertFalse(T.kw_hit("로제", "새 프로젝트 공개"))            # 짧은 말 substring 오탐 차단

    def test_long_keyword_substring(self):
        self.assertTrue(T.kw_hit("버닝썬 승리", "버닝썬 승리 CCTV 공개"))

    def test_picks_biggest_fresh(self):
        cands = [c("a", "승리 소주병 위협 CCTV", 2, 1), c("b", "승리 측 입장문", 5, 3), c("old", "승리 옛 사건", 9, 30)]
        self.assertEqual(T.related("승리", cands, NOW)["url"], "b")
        self.assertIsNone(T.related("없는말", cands, NOW))

    def test_pick_url(self):
        u = T.pick_url({"url": "https://x.kr/1", "event_key": "https://x.kr/1", "breaking_pick": {"url": "https://y.kr/2"}})
        self.assertEqual(u, "/?brk=https%3A%2F%2Fx.kr%2F1&bl=https%3A%2F%2Fy.kr%2F2")


if __name__ == "__main__":
    unittest.main()
