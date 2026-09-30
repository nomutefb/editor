"""X 구독 = 등록 계정 · X_SUB_H(18h) 창 · 조회수 순(운영자 261001 "구독한 채널 기준 18시간 내, 조회수 순으로 10위까지").
회귀 축: 비로그인 신디케이션이 역대 인기글만 줘서(실측 261001) '0건 아님'으로 RSS 폴백을 건너뛰고 화면이 0~1건으로 굳던 것,
해제한 계정 글이 이월로 남던 것, 폰 env의 옛 X_AUTH_TOKEN으로 로그인 호출이 머지만으로 켜지던 위험."""
import json
import os
import sys
import unittest
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scraper"))
import sns_trends as st  # noqa: E402


def _ago(h):
    return format_datetime(datetime.now(timezone.utc) - timedelta(hours=h))


def _tw(acc, tid, h, views=0):
    return {"account": acc, "text": "t" + tid, "views": views, "likes": 0, "time": _ago(h),
            "url": "https://x.com/%s/status/%s" % (acc, tid)}


def _syn_page(tweets):
    data = {"props": {"pageProps": {"timeline": {"entries": [{"content": {"tweet": t}} for t in tweets]}}}}
    return '<script id="__NEXT_DATA__" type="application/json">%s</script>' % json.dumps(data)


def _syn_tw(tid, h):
    return {"id_str": tid, "full_text": "old " + tid, "favorite_count": 5, "created_at": _ago(h)}


class XRank(unittest.TestCase):
    def test_window_views_order_and_limit(self):
        items = [_tw("a", "1", 1, 10), _tw("b", "2", 17, 900), _tw("c", "3", 19, 99999), _tw("d", "4", 2, 50)]
        got = st.x_rank(items, limit=10)
        self.assertEqual([t["url"][-1] for t in got], ["2", "4", "1"])   # 19h = 창 밖 · 나머지 = 조회수 내림차순

    def test_unregistered_account_dropped(self):
        items = [_tw("MarioNawfal", "1", 1, 999), _tw("kyunghyang", "2", 1, 5)]
        got = st.x_rank(items, accounts=["kyunghyang"])
        self.assertEqual([t["account"] for t in got], ["kyunghyang"])

    def test_views_unknown_falls_back_to_newest(self):
        got = st.x_rank([_tw("a", "1", 5), _tw("b", "2", 1)])
        self.assertEqual([t["url"][-1] for t in got], ["2", "1"])

    def test_limit_cuts(self):
        items = [_tw("a%d" % i, str(i), 1, i) for i in range(40)]
        self.assertEqual(len(st.x_rank(items, limit=30)), 30)


    def test_body_unescapes_entities(self):
        self.assertEqual(st._x_body("EBS &lt;딩동댕&gt; &amp; https://t.co/ab12", None), "EBS <딩동댕> &")


class XSubsPaths(unittest.TestCase):
    def setUp(self):
        self._env = {k: os.environ.pop(k) for k in ("X_SUBS_AUTH_TOKEN", "X_SUBS_CT0", "X_AUTH_TOKEN", "X_CT0") if k in os.environ}
        self._sleep = mock.patch.object(st.time, "sleep", lambda *_: None)
        self._sleep.start()
        st.X_AUTH_STATE = "off"

    def tearDown(self):
        self._sleep.stop()
        for k in ("X_SUBS_AUTH_TOKEN", "X_SUBS_CT0", "X_AUTH_TOKEN", "X_CT0"):
            os.environ.pop(k, None)
        os.environ.update(self._env)

    def test_old_only_syndication_triggers_rss(self):
        rss = [dict(_tw("kh", "9", 2), _tid="9")]
        with mock.patch.object(st, "_get", return_value=_syn_page([_syn_tw("1", 24 * 400)])), \
             mock.patch.object(st, "_x_rss", return_value=rss) as r:
            got = st.x_subs(["kh"])
        r.assert_called_once()
        self.assertEqual([t["url"] for t in got], ["https://x.com/kh/status/9"])

    def test_fresh_syndication_skips_rss(self):
        with mock.patch.object(st, "_get", return_value=_syn_page([_syn_tw("1", 3)])), \
             mock.patch.object(st, "_x_rss", return_value=[]) as r:
            got = st.x_subs(["kh"])
        r.assert_not_called()
        self.assertEqual(len(got), 1)

    def test_legacy_search_cookie_does_not_enable_login(self):
        os.environ["X_AUTH_TOKEN"], os.environ["X_CT0"] = "a", "b"
        self.assertIsNone(st._x_auth_hdr())
        os.environ["X_SUBS_AUTH_TOKEN"], os.environ["X_SUBS_CT0"] = "a", "b"
        self.assertIn("auth_token=a", st._x_auth_hdr()["Cookie"])

    def test_login_path_used_and_401_falls_back(self):
        os.environ["X_SUBS_AUTH_TOKEN"], os.environ["X_SUBS_CT0"] = "a", "b"
        calls = []

        def fake_tl(acc, hdr):
            calls.append(acc)
            if acc == "bad":
                raise st.urllib.error.HTTPError("u", 401, "x", {}, None)
            return [_tw(acc, "5", 1, 700)]
        with mock.patch.object(st, "_x_auth_tl", side_effect=fake_tl), \
             mock.patch.object(st, "_get", return_value=_syn_page([_syn_tw("7", 2)])) as g, \
             mock.patch.object(st, "_x_rss", return_value=[]):
            got = st.x_subs(["ok1", "bad", "ok2"])
        self.assertEqual(calls, ["ok1", "bad"])   # 401 뒤엔 로그인 호출 중단(연타 금지)
        self.assertEqual(g.call_count, 2)          # bad·ok2 = 신디케이션 폴백
        self.assertEqual(got[0]["views"], 700)
        self.assertEqual(st.X_AUTH_STATE, "ok")
        st.x_subs([])   # 러너 gl 빈 목록 호출이 ok를 덮지 않는다
        self.assertEqual(st.X_AUTH_STATE, "ok")

    def test_login_all_blocked_reports_fail(self):
        os.environ["X_SUBS_AUTH_TOKEN"], os.environ["X_SUBS_CT0"] = "a", "b"
        with mock.patch.object(st, "_x_auth_tl", side_effect=st.urllib.error.HTTPError("u", 403, "x", {}, None)), \
             mock.patch.object(st, "_get", return_value=_syn_page([])), mock.patch.object(st, "_x_rss", return_value=[]):
            self.assertEqual(st.x_subs(["a", "b"]), [])
        self.assertEqual(st.X_AUTH_STATE, "fail")

    def test_no_cookie_stays_off(self):
        with mock.patch.object(st, "_get", return_value=_syn_page([])), mock.patch.object(st, "_x_rss", return_value=[]):
            st.x_subs(["a"])
        self.assertEqual(st.X_AUTH_STATE, "off")


class XTimelineParse(unittest.TestCase):
    def _res(self, uid, tid, h, rt=False, typ="Tweet"):
        leg = {"id_str": tid, "user_id_str": uid, "created_at": _ago(h), "full_text": ("RT @z: x" if rt else "hi " + tid),
               "favorite_count": 1, "retweet_count": 0, "reply_count": 0}
        r = {"__typename": "Tweet", "rest_id": tid, "legacy": leg, "views": {"count": "123"},
             "core": {"user_results": {"result": {"legacy": {"name": "N"}}}}}
        return {"__typename": "TweetWithVisibilityResults", "tweet": r} if typ == "vis" else r

    def test_only_own_non_retweet_top_level(self):
        own = self._res("42", "1", 1)
        own["quoted_status_result"] = {"result": self._res("99", "2", 1)}   # 인용된 남의 글 = 재귀로 들어오면 안 됨
        ents = [{"content": {"itemContent": {"tweet_results": {"result": own}}}},
                {"content": {"itemContent": {"tweet_results": {"result": self._res("42", "3", 1, rt=True)}}}},
                {"content": {"items": [{"item": {"itemContent": {"tweet_results": {"result": self._res("42", "4", 2, typ="vis")}}}}]}},
                {"content": {"itemContent": {"tweet_results": {"result": self._res("77", "5", 1)}}}}]
        resp = {"data": {"user": {"result": {"timeline_v2": {"timeline": {"instructions": [
            {"type": "TimelineAddEntries", "entries": ents},
            {"type": "TimelinePinEntry", "entry": {"content": {"itemContent": {"tweet_results": {"result": self._res("42", "6", 900)}}}}}]}}}}}}
        got = st._x_tl_items(resp, "acc", "42")
        self.assertEqual(sorted(t["url"].rsplit("/", 1)[-1] for t in got), ["1", "4", "6"])
        self.assertTrue(all(t["views"] == 123 and t["name"] == "N" for t in got))


if __name__ == "__main__":
    unittest.main()
