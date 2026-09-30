"""X 구독 = 등록 계정 · X_SUB_H(18h) 창 · 조회수 순(운영자 261001 "구독한 채널 기준 18시간 내, 조회수 순으로 10위까지").
회귀 축: 비로그인 신디케이션이 역대 인기글만 줘서(실측 261001) '0건 아님'으로 RSS 폴백을 건너뛰고 화면이 0~1건으로 굳던 것,
해제한 계정 글이 이월로 남던 것, 계정 쿼터가 조회수 순을 깨던 것, 로그인 실패 사유가 한 덩어리로 뭉치던 것,
폰 env의 옛 X_AUTH_TOKEN으로 홈 IP 로그인 호출이 켜지던 위험."""
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

_ENV = ("X_SUBS_AUTH_TOKEN", "X_SUBS_CT0", "X_AUTH_TOKEN", "X_CT0", "GITHUB_ACTIONS")


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


def _http(code):
    return st.urllib.error.HTTPError("u", code, "x", {}, None)


class XRank(unittest.TestCase):
    def test_window_views_order_and_limit(self):
        items = [_tw("a", "1", 1, 10), _tw("b", "2", 17, 900), _tw("c", "3", 19, 99999), _tw("d", "4", 2, 50)]
        got = st.x_rank(items, limit=10)
        self.assertEqual([t["url"][-1] for t in got], ["2", "4", "1"])   # 19h = 창 밖 · 나머지 = 조회수 내림차순

    def test_pure_views_no_account_quota(self):
        # 계정 쿼터가 있으면 A의 2·3위(80만·70만)가 B의 1천 뷰 뒤로 밀렸다(평의회 261001 재현)
        items = [_tw("A", "1", 1, 900000), _tw("A", "2", 2, 800000), _tw("A", "3", 3, 700000), _tw("B", "4", 1, 1000)]
        self.assertEqual([t["views"] for t in st.x_rank(items)], [900000, 800000, 700000, 1000])

    def test_dedup_by_tweet_id_first_wins(self):
        items = [_tw("kh", "7", 1, 500), dict(_tw("KH", "7", 1, 1), account="kh")]
        got = st.x_rank(items)
        self.assertEqual(len(got), 1)
        self.assertEqual(got[0]["views"], 500)

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

    def test_note_text_kept_raw(self):
        # note 본문은 이스케이프 없이 오고 display_text_range는 legacy 기준 = 적용·복원하면 잘리고 바뀐다(평의회 실측)
        r = {"note_tweet": {"note_tweet_results": {"result": {"text": "M&A &notes 끝까지 긴 글"}}}}
        leg = {"full_text": "M&amp;A 앞부분", "display_text_range": [0, 7]}   # 범위 = 이스케이프 문자열 기준(평의회 실측)
        self.assertEqual(st._x_text(r, leg), "M&A &notes 끝까지 긴 글")
        self.assertEqual(st._x_text({}, leg), "M&A")


class XSubsPaths(unittest.TestCase):
    def setUp(self):
        self._env = {k: os.environ.pop(k) for k in _ENV if k in os.environ}
        self._sleep = mock.patch.object(st.time, "sleep", lambda *_: None)
        self._sleep.start()
        st.XA.update(state="off", stop=False, empty=0, at="")
        st.X_UID.clear()

    def tearDown(self):
        self._sleep.stop()
        for k in _ENV:
            os.environ.pop(k, None)
        os.environ.update(self._env)
        st.XA.update(state="off", stop=False, empty=0, at="")

    def _cookie(self):
        os.environ.update(X_SUBS_AUTH_TOKEN="a", X_SUBS_CT0="b", GITHUB_ACTIONS="true")

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

    def test_login_gates(self):
        os.environ.update(X_AUTH_TOKEN="a", X_CT0="b", GITHUB_ACTIONS="true")
        self.assertIsNone(st._x_auth_hdr())                     # 옛 x_search 쿠키 이름으로는 안 켜진다
        os.environ.update(X_SUBS_AUTH_TOKEN="a", X_SUBS_CT0="b")
        self.assertIn("auth_token=a", st._x_auth_hdr()["Cookie"])
        os.environ.pop("GITHUB_ACTIONS")
        self.assertIsNone(st._x_auth_hdr())                     # 폰(러너 밖) = 쿠키가 있어도 로그인 호출 0
        os.environ["GITHUB_ACTIONS"] = "true"
        st.XA["stop"] = True
        self.assertIsNone(st._x_auth_hdr())                     # 중단 플래그 = 다음 호출(gl)에도 유지

    def _run(self, accs, tl):
        with mock.patch.object(st, "_x_auth_tl", side_effect=tl) as a, \
             mock.patch.object(st, "_get", return_value=_syn_page([_syn_tw("7", 2)])) as g, \
             mock.patch.object(st, "_x_rss", return_value=[]):
            got = st.x_subs(accs)
        return got, [c.args[0] for c in a.call_args_list], g.call_count

    def test_login_ok(self):
        self._cookie()
        got, calls, syn = self._run(["a", "b"], lambda acc, hdr: [_tw(acc, "5" + acc, 1, 700)])
        self.assertEqual((calls, syn, st.XA["state"]), (["a", "b"], 0, "ok"))
        self.assertTrue(st.XA["at"])
        st.x_subs([])   # 러너 gl 빈 목록 호출이 상태를 덮지 않는다
        self.assertEqual(st.XA["state"], "ok")

    def test_401_is_cookie_fail_and_stops(self):
        self._cookie()

        def tl(acc, hdr):
            if acc == "bad":
                raise _http(401)
            return [_tw(acc, "5" + acc, 1, 700)]
        got, calls, syn = self._run(["ok1", "bad", "ok2"], tl)
        self.assertEqual(calls, ["ok1", "bad"])   # 401 뒤 로그인 호출 중단(연타 금지)
        self.assertEqual(syn, 2)                  # bad·ok2 = 신디케이션 폴백
        self.assertEqual(st.XA["state"], "fail")  # 1건 성공 뒤라도 중단 = 부분 실패를 ok로 가리지 않는다
        self.assertEqual(got[0]["views"], 700)
        _, calls2, _ = self._run(["gl1"], tl)     # kr→gl 두 번째 호출도 로그인 재개 없음
        self.assertEqual(calls2, [])

    def test_timeout_and_http_errors_are_err_not_cookie(self):
        for exc in (st.urllib.error.URLError("timed out"), _http(404), _http(429), _http(400)):
            st.XA.update(state="off", stop=False, empty=0, at="")
            self._cookie()

            def tl(acc, hdr, exc=exc):
                raise exc
            _, calls, syn = self._run(["a", "b", "c"], tl)
            self.assertEqual(calls, ["a"], exc)
            self.assertEqual(st.XA["state"], "err", exc)
            self.assertEqual(syn, 3)

    def test_empty_timeline_falls_back_then_stops(self):
        self._cookie()

        def tl(acc, hdr):
            raise st._XAccErr("빈 타임라인")
        _, calls, syn = self._run(["a", "b", "c"], tl)
        self.assertEqual(calls, ["a", "b"])       # 연속 2회 빈 응답 + 성공 0 = 구조 변경 의심 → 중단
        self.assertEqual(syn, 3)
        self.assertEqual(st.XA["state"], "err")

    def test_single_private_account_does_not_stop(self):
        self._cookie()

        def tl(acc, hdr):
            if acc == "priv":
                raise st._XAccErr("빈 타임라인")
            return [_tw(acc, "5" + acc, 1, 10)]
        _, calls, _ = self._run(["a", "priv", "b"], tl)
        self.assertEqual(calls, ["a", "priv", "b"])
        self.assertEqual(st.XA["state"], "ok")

    def test_cookie_never_printed(self):
        self._cookie()
        os.environ["X_SUBS_AUTH_TOKEN"] = "SECRETTOKEN"

        def tl(acc, hdr):
            raise ValueError("Invalid header value b'auth_token=SECRETTOKEN\\n'")
        with mock.patch("sys.stderr") as se:
            self._run(["a"], tl)
        self.assertNotIn("SECRETTOKEN", "".join(str(c) for c in se.write.call_args_list))

    def test_no_cookie_stays_off(self):
        with mock.patch.object(st, "_get", return_value=_syn_page([])), mock.patch.object(st, "_x_rss", return_value=[]):
            st.x_subs(["a"])
        self.assertEqual(st.XA["state"], "off")


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

    def test_uid_cache_skips_lookup(self):
        st.X_UID.clear()
        st.X_UID["kh"] = "42"
        tl = {"data": {"user": {"result": {"timeline_v2": {"timeline": {"instructions": [{"entries": [
            {"content": {"itemContent": {"tweet_results": {"result": self._res("42", "1", 1)}}}}]}]}}}}}}
        with mock.patch.object(st, "_x_gql", return_value=tl) as g:
            got = st._x_auth_tl("KH", {})
        self.assertEqual(g.call_count, 1)   # UserByScreenName 생략 = 타임라인 1콜
        self.assertEqual(len(got), 1)
        st.X_UID.clear()


if __name__ == "__main__":
    unittest.main()
