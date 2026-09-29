"""확산 신호 수집함 반영(scraper/live_seed.py) 회귀 — 첨부(익명 대표 포함)·입장·구글 뉴스 씨앗·이관(중복 푸시 0)·[강] 동결·예산 ·
판정기(도장·꼬리표·--count)·게이트 면제·푸시 문턱 짝. 운영자 260929 닛몰캐쉬 실사고."""
import importlib.util
import io
import json
import os
import contextlib
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scraper"))
sys.path.insert(0, str(ROOT / ".github" / "scripts"))
import live_signal as L  # noqa: E402
import live_seed as S  # noqa: E402

L.GN_PAUSE_S = 0   # 시험 = 구글 뉴스 예의 대기 없음(주입 fetch)

KST = timezone(timedelta(hours=9))
FIX = ROOT / "tests" / "fixtures" / "live"


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


PS = _load(ROOT / ".github" / "scripts" / "push_send.py", "push_send_lv")
BG = _load(ROOT / ".github" / "scripts" / "brk_gates.py", "brk_gates_lv")


def ep(s):
    return datetime.strptime(s, "%Y-%m-%d %H:%M").replace(tzinfo=KST).timestamp()


def iso(t):
    return datetime.fromtimestamp(t, KST).strftime("%Y-%m-%dT%H:%M:%S%z")


def utc(t):
    return datetime.fromtimestamp(t, timezone.utc).isoformat()


def snap(t, comms, x=()):
    upd = datetime.fromtimestamp(t, KST)
    return {"tbs": {"updated": upd.strftime("%Y-%m-%d %H:%M"),
                    "communities": [{"id": f"c{i}", "posts": [{"title": ti} for ti in ts]} for i, ts in enumerate(comms)]},
            "sns": {"updated": upd.isoformat(), "xtrends": [{"query": q} for q in x]}, "social": []}


def cand(url, title, t, cross=2, **kw):
    c = {"id": url, "url": url, "title": title, "media": "매체", "cat": "문화", "cross": cross, "published": utc(t - 600),
         "first_seen": iso(t), "event_key": url, "cluster_members": [url], "breaking_pick": {"url": url, "media": "매체", "title": title}}
    c.update(kw)
    return c


ARMED = snap(ep("2026-09-29 09:37"), [["유튜버 닛몰캐쉬 폭로 나온듯"], ["닛몰캐쉬 전여친 폭로"], ["닛몰캐쉬 녹취록"], ["닛몰캐쉬 채널"]],
             x=["닛몰캐쉬"])


def armed_state():
    st = L.new_state()
    t = ep("2026-09-29 09:37")
    L.update(st, ARMED, t + 60)
    return st


class Attach(unittest.TestCase):
    def test_named_title_gets_lv(self):
        st, t = armed_state(), ep("2026-09-29 09:46")
        cs = [cand("u1", "닛몰캐쉬, 사생활 논란", t), cand("u2", "다른 기사", t)]
        out, S_ = S.run(cs, [], ARMED, st, t, net=False)
        lv = {c["url"]: c.get("lv") for c in out}
        self.assertEqual(lv["u1"]["k"], "닛몰캐쉬")
        self.assertEqual(lv["u1"]["t"], 2)
        self.assertIsNone(lv["u2"])

    def test_anonymous_rep_matched_by_member_title(self):
        st, t = armed_state(), ep("2026-09-29 10:34")
        rep = cand("tvr", "유명 유튜버, 전 연인 폭로에 채널 삭제", t, cluster_members=["tvr", "khan"])
        arts = [{"link": "khan", "title": "[단독] ‘BTS 댄서’ 닛몰캐쉬, 사생활 논란"}, {"link": "tvr", "title": rep["title"]}]
        out, _ = S.run([rep], arts, ARMED, st, t, net=False)
        self.assertEqual(out[0]["lv"]["k"], "닛몰캐쉬")   # A7 = 익명 대표도 멤버 실명으로 잡힌다

    def test_community_only_not_attached(self):
        st, t = L.new_state(), ep("2026-09-29 09:37")
        s = snap(t, [["닛몰캐쉬 폭로"]] * 3)
        out, _ = S.run([cand("u1", "닛몰캐쉬 사생활", t)], [], s, st, t + 60, net=False)
        self.assertNotIn("lv", out[0])                     # t1 커뮤니티 한 갈래 = 붙이지 않는다

    def test_old_candidate_not_attached(self):
        st, t = armed_state(), ep("2026-09-29 09:46")
        old = cand("u1", "닛몰캐쉬 옛 기사", t - 20 * 3600)
        out, _ = S.run([old], [], ARMED, st, t, net=False)
        self.assertNotIn("lv", out[0])

    def test_strong_lv_frozen(self):
        st, t = L.new_state(), ep("2026-09-29 15:00")
        c = cand("u1", "닛몰캐쉬, 사과문", t, lv={"k": "닛몰캐쉬", "t": 3, "gn": 7})
        out, _ = S.run([c], [], {"tbs": {}, "sns": {}, "social": []}, st, t, net=False)
        self.assertEqual(out[0]["lv"]["t"], 3)             # 신호가 꺼져도 [강]은 내리지 않는다(도장 불변)
        c2 = cand("u2", "닛몰캐쉬, 근황", t, lv={"k": "닛몰캐쉬", "t": 2})
        out2, _ = S.run([c2], [], {"tbs": {}, "sns": {}, "social": []}, L.new_state(), t, net=False)
        self.assertNotIn("lv", out2[0])                    # [중]은 신호가 꺼지면 내린다


class Admit(unittest.TestCase):
    def test_single_outlet_cluster_admitted_as_solo(self):
        st, t = armed_state(), ep("2026-09-29 09:46")
        a = {"link": "khan", "title": "[단독] ‘BTS 댄서’ 닛몰캐쉬, 사생활 논란", "publisher": "스포츠경향", "category": "entertainment",
             "published": utc(t - 1200), "is_cluster_rep": True, "cross_score": 1, "cluster_size": 1, "burst": 1,
             "cluster_members": ["khan"], "breaking_pick": {"url": "khan", "media": "스포츠경향", "title": "[단독] ‘BTS 댄서’ 닛몰캐쉬, 사생활 논란"}}
        out, stat = S.run([cand("x", "무관", t)], [a], ARMED, st, t, net=False)
        e = next(c for c in out if c["url"] == "khan")
        self.assertEqual(stat["adm"], 1)
        self.assertEqual((e["solo"], e["cross"], e["breaking_candidate"], e["lv"]["t"]), (1, 1, True, 2))
        self.assertEqual(e["event_key"], "khan")

    def test_not_admitted_when_candidate_exists(self):
        st, t = armed_state(), ep("2026-09-29 09:46")
        a = {"link": "khan", "title": "닛몰캐쉬 단독", "is_cluster_rep": True, "cross_score": 1, "published": utc(t - 600),
             "cluster_members": ["khan"]}
        out, stat = S.run([cand("u1", "닛몰캐쉬 폭로", t)], [a], ARMED, st, t, net=False)
        self.assertEqual(stat["adm"], 0)


def strong_state(t):
    """무장(09:37) + 구글 뉴스 확인(10:31) 상태 — 픽스처 xml 의 그 시각까지 발행분."""
    import gnews_search as G
    st = armed_state()
    items = [i for i in G.parse_rss((FIX / "gn_nimol.xml").read_text(encoding="utf-8")) if i["pub"] <= t]
    xml = "".join('<item><title>%s</title><link>%s</link><pubDate>%s</pubDate><source url="%s">%s</source></item>'
                  % (i["title"], i["link"], datetime.fromtimestamp(i["pub"], timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT"),
                     i["source"], i["sname"]) for i in items)
    return st, (lambda q: xml)


class Seed(unittest.TestCase):
    def test_gn_confirmed_without_feed_creates_seed(self):
        t = ep("2026-09-29 10:31")
        st, fetch = strong_state(t)
        out, stat = S.run([cand("x", "무관", t)], [], ARMED, st, t, gn_fetch=fetch, gn_decode=lambda l: "https://www.ggilbo.com/news/1")
        seed = next(c for c in out if c.get("seed"))
        self.assertEqual(stat["seed"], 1)
        self.assertEqual(seed["media"], "금강일보")
        self.assertIn("닛몰캐쉬", seed["title"])
        self.assertEqual(seed["url"], "https://www.ggilbo.com/news/1")   # 원문 해제 성공 = 원문
        self.assertEqual(seed["event_key"], seed["url"])
        self.assertEqual((seed["cross"], seed["solo"], seed["breaking_candidate"], seed["lv"]["t"]), (1, 1, True, 3))
        self.assertGreaterEqual(seed["lv"]["gn"], 3)
        # 같은 회차 재실행(폰·러너 두 레인) = 씨앗 중복 0
        out2, stat2 = S.run(out, [], ARMED, st, t + 60, gn_fetch=fetch, gn_decode=lambda l: "")
        self.assertEqual(stat2["seed"], 0)
        self.assertEqual(sum(1 for c in out2 if c.get("seed")), 1)

    def test_decode_failure_keeps_gn_link(self):
        t = ep("2026-09-29 10:31")
        st, fetch = strong_state(t)
        out, _ = S.run([], [], ARMED, st, t, gn_fetch=fetch, gn_decode=lambda l: "")
        seed = next(c for c in out if c.get("seed"))
        self.assertTrue(seed["url"].startswith("https://news.google.com/rss/articles/"))

    def test_decode_retry_rewrites_url_keeps_event_key(self):   # 평의회 #6 — 해제 실패 = 다음 회차 재시도(상한 3) · 성공 시 링크만 원문
        t = ep("2026-09-29 10:31")
        st, fetch = strong_state(t)
        tries = []
        out, _ = S.run([], [], ARMED, st, t, gn_fetch=fetch, gn_decode=lambda l: tries.append(l) or "")
        seed = next(c for c in out if c.get("seed"))
        gl = seed["url"]
        out2, stat = S.run(out, [], ARMED, st, t + 900, gn_fetch=fetch, gn_decode=lambda l: tries.append(l) or "https://www.ggilbo.com/news/1")
        s2 = next(c for c in out2 if c.get("seed"))
        self.assertEqual((stat.get("reurl"), s2["url"], s2["breaking_pick"]["url"]), (1, "https://www.ggilbo.com/news/1", "https://www.ggilbo.com/news/1"))
        self.assertEqual((s2["event_key"], s2["id"]), (gl, gl))   # 푸시 원장 첫 키·id 불변
        self.assertEqual(len(tries), 2)
        out3, _ = S.run(out2, [], ARMED, st, t + 1800, gn_fetch=fetch, gn_decode=lambda l: tries.append(l) or "x")
        self.assertEqual(len(tries), 2)                            # 성공 뒤 재시도 0

    def test_decode_gives_up_after_cap(self):
        t = ep("2026-09-29 10:31")
        st, fetch = strong_state(t)
        tries = []
        dec = lambda l: tries.append(l) or ""   # noqa: E731
        out, _ = S.run([], [], ARMED, st, t, gn_fetch=fetch, gn_decode=dec)
        for i in range(1, 5):
            out, _ = S.run(out, [], ARMED, st, t + 900 * i, gn_fetch=fetch, gn_decode=dec)
        self.assertEqual(len(tries), L.GN_DEC_TRY)

    def test_home_lane_no_google(self):   # pc·폰(LIVE_GN_MAX_Q=0) = 검색·해제 0회(가정 IP 보호)
        t = ep("2026-09-29 10:31")
        st, _ = strong_state(t)
        calls = []
        old = L.GN_MAX_Q
        L.GN_MAX_Q = 0
        try:
            S.run([], [], ARMED, st, t, gn_fetch=lambda q: calls.append(q) or "")
        finally:
            L.GN_MAX_Q = old
        self.assertEqual(calls, [])

    def test_supersede_moves_state_and_blocks_double_push(self):
        t = ep("2026-09-29 10:31")
        st, fetch = strong_state(t)
        out, _ = S.run([], [], ARMED, st, t, gn_fetch=fetch, gn_decode=lambda l: "https://www.ggilbo.com/news/1")
        seed = next(c for c in out if c.get("seed"))
        # 판정기가 씨앗을 긴급·경중 2로 확정 → 푸시가 나갔다(원장 = 씨앗 dedup 키)
        seed.update({"breaking": True, "breaking_rubric": "stampseed", "grade": 2, "grade_rubric": "gr"})
        self.assertTrue(PS.is_breaking(seed) and PS.push_cross_ok(seed))
        sent = set(PS.dedup_keys(seed))
        # 15분 뒤 우리 피드에 실후보(익명 대표 · 이름은 멤버 제목) — 씨앗 이관
        t2 = t + 900
        real = cand("tvr", "유명 유튜버, 전 연인 폭로에 채널 삭제", t2, cross=1, cluster_members=["tvr", "khan"])
        arts = [{"link": "khan", "title": "[단독] 닛몰캐쉬, 사생활 논란"}]
        out2, stat = S.run(out + [real], arts, ARMED, st, t2, gn_fetch=fetch, gn_decode=lambda l: "")
        self.assertEqual(stat["sup"], 1)
        self.assertFalse(any(c.get("seed") for c in out2))
        r = next(c for c in out2 if c["url"] == "tvr")
        self.assertEqual(r["event_key"], seed["url"])       # 푸시 원장 첫 키 승계
        self.assertTrue(r["breaking"])
        self.assertEqual(r["breaking_rubric"], "stampseed")   # 이관(제목 지문이 달라 판정기가 1회 재판정)
        self.assertEqual((r["grade"], r["first_seen"]), (2, seed["first_seen"]))
        self.assertEqual(r["lv"]["t"], 3)
        self.assertTrue(PS.is_breaking(r) and PS.push_cross_ok(r))
        self.assertTrue(any(k in sent for k in PS.dedup_keys(r)))   # = push_send 가 「이미 보냄」으로 건너뛴다

    def test_resurrected_seed_reabsorbed(self):
        t = ep("2026-09-29 10:31")
        st, fetch = strong_state(t)
        out, _ = S.run([], [], ARMED, st, t, gn_fetch=fetch, gn_decode=lambda l: "https://www.ggilbo.com/news/1")
        seed = dict(next(c for c in out if c.get("seed")))
        real = cand("tvr", "닛몰캐쉬 폭로 확산", t + 900, cross=3)
        out2, _ = S.run(out + [real], [], ARMED, st, t + 900, gn_fetch=fetch, gn_decode=lambda l: "")
        # 판정 레인의 옛 사본 착지로 씨앗이 되살아났다
        out3, stat = S.run(out2 + [seed], [], ARMED, st, t + 1800, gn_fetch=fetch, gn_decode=lambda l: "")
        self.assertEqual(stat["sup"], 1)
        self.assertEqual(sum(1 for c in out3 if c.get("seed")), 0)


class Related(unittest.TestCase):   # 포함 관계 이름 씨앗 중복 차단(260929 리플레이 = 사회인·사회인야구 동시 [강])
    def test_contained_names(self):
        self.assertTrue(S._related("사회인야구", {}, "사회인", {}))
        self.assertTrue(S._related("사회인", {}, "사회인야구", {}))
        self.assertFalse(S._related("닛몰캐쉬", {}, "사회인", {}))
        self.assertFalse(S._related("김건우", {}, "김건", {}))   # 2자 = 우연 포함 차단


def _strong(st, k, now, e0, d=None):
    """구글 뉴스로 확인된 [강] 이름(무장 50분 전 · 확인 1분 전) — 평의회3 재현 도우미."""
    st["k"][k] = dict({"f": {"C": int(now - 300), "X": int(now - 300)}, "m": {"c": 4, "x": 1}, "a": int(now - 3000),
                       "cf": int(now - 60), "cs": "g"}, **({"d": d} if d else {}))
    st["gn"][k] = {"at": int(now - 60), "n": 4, "nov": 1, "e": e0}


EMPTY = {"tbs": {}, "sns": {}, "social": []}


class DupPush(unittest.TestCase):   # 평의회3 260929 — 같은 사건 2발 경로(씨앗 수명주기 × 푸시 원장)
    def test_related_names_make_one_seed(self):
        now = ep("2026-09-29 10:31")
        st = L.new_state()
        _strong(st, "닛몰캐쉬", now, {"p": int(now - 5000), "t": "닛몰캐쉬, 채널 삭제", "m": "금강일보", "l": "https://news.google.com/rss/articles/A"})
        _strong(st, "닛몰캐쉬데이트폭력", now, {"p": int(now - 3000), "t": "닛몰캐쉬 데이트폭력 의혹", "m": "뉴스1",
                                        "l": "https://news.google.com/rss/articles/B"}, d="닛몰캐쉬 데이트폭력")
        out, stat = S.run([], [], EMPTY, st, now, net=False, gn_decode=lambda l: l.replace("news.google.com/rss/articles", "o.kr"))
        self.assertEqual((stat["seed"], sum(1 for c in out if c.get("seed"))), (1, 1))
        out2, stat2 = S.run(out, [], EMPTY, st, now + 900, net=False, gn_decode=lambda l: "")
        self.assertEqual(stat2["seed"], 0)

    def test_ours_confirm_vetoed_by_google_not_novel(self):   # #7-2 — 구글 뉴스가 「무장 전 보도 있음」이면 우리 cross≥3 로도 [강] 안 됨
        t = ep("2026-09-29 09:46")
        st = armed_state()
        st["gn"]["닛몰캐쉬"] = {"at": int(t - 60), "n": 5, "nov": 0}
        S.run([cand("u1", "닛몰캐쉬 폭로 확산", t, cross=5)], [], ARMED, st, t, net=False)
        self.assertNotIn("cf", st["k"]["닛몰캐쉬"])
        st2 = armed_state()
        S.run([cand("u1", "닛몰캐쉬 폭로 확산", t, cross=5)], [], ARMED, st2, t, net=False)
        self.assertEqual(st2["k"]["닛몰캐쉬"].get("cs"), "o")

    def test_superseded_seed_not_recreated_when_real_drops(self):   # #7-8 — 실후보가 단독 좌석에서 잠시 빠져도 씨앗 재생성 0
        now = ep("2026-09-29 10:31")
        st = L.new_state()
        _strong(st, "닛몰캐쉬", now, {"p": int(now - 5000), "t": "닛몰캐쉬, 채널 삭제", "m": "금강일보", "l": "https://g/A"})
        out, _ = S.run([], [], EMPTY, st, now, net=False, gn_decode=lambda l: "")
        out2, stat = S.run(out + [cand("khan", "닛몰캐쉬 폭로 확산", now + 900, cross=1)], [], EMPTY, st, now + 900, net=False, gn_decode=lambda l: "")
        self.assertEqual(stat["sup"], 1)
        _, stat3 = S.run([c for c in out2 if c["url"] != "khan"], [], EMPTY, st, now + 1800, net=False, gn_decode=lambda l: "")
        self.assertEqual(stat3["seed"], 0)

    def test_pick_prefers_mainstream_over_sticky_solo(self):   # #7-9 — 지난번 첨부 유지 가점보다 본류(cross≥3) 우선
        t = ep("2026-09-29 11:31")
        solo, main = cand("s", "닛몰캐쉬 웹드라마 공개 재검토", t, cross=1), cand("m", "닛몰캐쉬 폭로 파문", t, cross=5)
        self.assertEqual(S._pick([(2, solo), (2, main)], {"u": "s"})["url"], "m")
        self.assertEqual(S._pick([(2, solo), (2, cand("m2", "닛몰캐쉬 근황", t, cross=2))], {"u": "s"})["url"], "m2")   # V7 — 다매체(cross≥2) 우선
        anon = cand("tvr", "유명 유튜버, 전 연인 폭로에 채널 삭제", t, cross=5)
        self.assertEqual(S._pick([(2, dict(solo, solo=1)), (1, anon)], {"u": "s"})["url"], "tvr")   # 익명 다매체 대표(멤버 실명) > 자기 제목 적중 [단독]

    def test_runner_backfills_supersede_ledger(self):   # V4 — 폰이 한 이관(씨앗 키 승계)을 러너가 sup 에 역기록
        now = ep("2026-09-29 10:46")
        st = L.new_state()
        st["sd"]["닛몰캐쉬"] = {"u": "https://g/1", "at": int(now - 900), "ek": "https://g/1"}
        S.run([cand("khan", "무관 제목", now, event_key="https://g/1")], [], EMPTY, st, now, net=False)
        self.assertEqual(st["sup"]["https://g/1"]["u"], "khan")

    def test_ro_lane_skips_on_stale_runner_state(self):   # V4 — 러너 정지(상태 3h↑ 낡음) = 읽기 전용 레인은 수집함을 안 건드린다
        import time as _t
        with tempfile.TemporaryDirectory() as d:
            stp, cp = Path(d) / "live_state.json", Path(d) / "candidates.json"
            st = L.new_state()
            st["tl"] = [int((_t.time() - 5 * 3600) // 60)]
            L.save_state(st, stp)
            cp.write_text("[]", encoding="utf-8")
            old = (L.STATE, S.CAND, L.STATE_RO, L.ON, sys.argv)
            L.STATE, S.CAND, L.STATE_RO, L.ON, sys.argv = stp, cp, True, True, ["live_seed.py", str(Path(d) / "none.json")]
            buf = io.StringIO()
            try:
                with contextlib.redirect_stdout(buf):
                    self.assertEqual(S.main(), 0)
            finally:
                L.STATE, S.CAND, L.STATE_RO, L.ON, sys.argv = old
            self.assertIn("생략", buf.getvalue())
            self.assertEqual(cp.read_text(encoding="utf-8"), "[]")

    def test_supersede_keeps_sent_seed_key(self):
        a = {"url": "A", "event_key": "A", "breaking": True, "seed": "gn"}
        b = {"url": "B", "event_key": "B", "seed": "gn"}
        r = {"url": "R", "event_key": "R"}
        S.supersede(a, r)
        S.supersede(b, r)                               # 나중 씨앗(NO)이 먼저 나간 씨앗 키를 지우지 않는다
        self.assertEqual(r["event_key"], "A")
        r2 = {"url": "R", "event_key": "R"}
        S.supersede(b, r2)
        S.supersede(a, r2)                              # 순서 반대 = 긴급으로 나간 씨앗 키가 이긴다
        self.assertEqual(r2["event_key"], "A")

    def test_readmitted_real_relinks_seed_key(self):
        now = ep("2026-09-29 10:31")
        st = L.new_state()
        st["sup"] = {"https://g/1": {"u": "khan", "at": int(now - 900)}}
        out, _ = S.run([cand("khan", "무관 제목", now)], [], EMPTY, st, now, net=False)
        self.assertEqual(out[0]["event_key"], "https://g/1")

    def test_cleaned_seed_not_recreated(self):   # 판정 NO 로 정리된 씨앗 = 재생성·재판정 0(평의회3)
        now = ep("2026-09-29 10:31")
        st = L.new_state()
        _strong(st, "닛몰캐쉬", now, {"p": int(now - 5000), "t": "[단독] 닛몰캐쉬, 채널 삭제", "m": "금강일보", "l": "https://g/A"})
        out, stat = S.run([], [], EMPTY, st, now, net=False, gn_decode=lambda l: "")
        self.assertEqual(stat["seed"], 1)
        next(c for c in out if c.get("seed")).update(breaking=False, breaking_rubric="st", grade=1, grade_rubric="gr")
        out, _ = S.run(out, [], EMPTY, st, now + 900, net=False, gn_decode=lambda l: "")   # 판정 결과가 장부에 적힌다
        _, stat2 = S.run([c for c in out if not c.get("seed")], [], EMPTY, st, now + 1800, net=False, gn_decode=lambda l: "")
        self.assertEqual(stat2["seed"], 0)

    def test_lost_seed_restored_with_verdict(self):   # 레인 덮어쓰기로 빠진 씨앗 = 처음 시각·판정·채점 그대로 복원(평의회260929-2 #5)
        now = ep("2026-09-29 10:31")
        st = L.new_state()
        _strong(st, "닛몰캐쉬", now, {"p": int(now - 5000), "t": "닛몰캐쉬, 채널 삭제", "m": "금강일보", "l": "https://g/A"})
        out, _ = S.run([], [], EMPTY, st, now, net=False, gn_decode=lambda l: "")
        sd0 = next(c for c in out if c.get("seed"))
        sd0.update(breaking=True, breaking_rubric="st", grade=2, grade_rubric="gr")
        out, _ = S.run(out, [], EMPTY, st, now + 900, net=False, gn_decode=lambda l: "")
        out2, stat = S.run([c for c in out if not c.get("seed")], [], EMPTY, st, now + 1800, net=False, gn_decode=lambda l: "")
        r = next(c for c in out2 if c.get("seed"))
        self.assertEqual(stat["seed"], 1)
        self.assertEqual((r["first_seen"], r["breaking"], r["breaking_rubric"], r["grade"], r["grade_rubric"]),
                         (sd0["first_seen"], True, "st", 2, "gr"))

    def test_seed_skips_stale_story_in_our_ledger(self):
        now = ep("2026-09-29 10:31")
        st = L.new_state()
        _strong(st, "닛몰캐쉬", now, {"p": int(now - 5000), "t": "닛몰캐쉬, 채널 삭제", "m": "금강일보", "l": "https://g/A"})
        old = [{"first_seen": iso(now - 3000 - 10 * 3600), "title": "닛몰캐쉬 전 연인 폭로 파문"}]
        _, stat = S.run([], [], EMPTY, st, now, net=False, gn_decode=lambda l: "", events=old)
        self.assertEqual(stat["seed"], 0)

    def test_feed_merge_drops_seed_flag(self):
        T = S.T
        now = datetime.now(KST).timestamp()
        seed = {"id": "U", "url": "U", "title": "닛몰캐쉬 폭로", "cross": 1, "solo": 1, "seed": "gn", "event_key": "U",
                "published": utc(now - 1800), "first_seen": iso(now - 1800), "cluster_members": [], "arts": 1}
        rep = {"link": "U", "title": "닛몰캐쉬 폭로", "publisher": "금강일보", "category": "", "published": utc(now - 1800),
               "is_cluster_rep": True, "cross_score": 3, "burst": 0, "cluster_size": 3, "cluster_members": ["U", "V", "W"],
               "breaking_pick": {"url": "U", "media": "금강일보", "title": "닛몰캐쉬 폭로"}}
        o_src, o_dst = T.SRC, T.DST
        try:
            with tempfile.TemporaryDirectory() as d:
                T.SRC, T.DST = Path(d) / "a.json", Path(d) / "c.json"
                T.SRC.write_text(json.dumps([rep], ensure_ascii=False), encoding="utf-8")
                T.DST.write_text(json.dumps([seed], ensure_ascii=False), encoding="utf-8")
                with contextlib.redirect_stdout(io.StringIO()):
                    T.main()
                out = {c["url"]: c for c in json.loads(T.DST.read_text(encoding="utf-8"))}
        finally:
            T.SRC, T.DST = o_src, o_dst
        self.assertNotIn("seed", out["U"])
        self.assertEqual(out["U"]["event_key"], "U")

    def test_dedup_keys_carry_url_and_episode(self):
        c = {"url": "R", "event_key": "SEED", "title": "t", "lv": {"k": "닛몰 캐쉬", "t": 3, "a": "2026-09-29T09:46:00+0900"}}
        ks = PS.dedup_keys(c)
        self.assertEqual(ks[0], "SEED")                 # 첫 키(푸시 tag) 불변
        self.assertIn("R", ks)
        self.assertIn("lv:닛몰캐쉬@2026-09-29T09:46:00+0900", ks)
        self.assertFalse(any(k.startswith("lv:") for k in PS.dedup_keys(dict(c, lv=dict(c["lv"], t=2)))))   # [중] = 에피소드 키 없음

    def test_keep_strong_takes_stronger_numbers(self):
        old = {"k": "닛몰캐쉬", "t": 3, "f": "CX", "c": 4, "x": 1, "gn": 7, "a": "A0"}
        new = {"k": "닛몰캐쉬", "t": 2, "f": "G", "c": 2, "x": 5, "g": 20000, "a": "A1"}
        self.assertEqual(S._keep_strong(old, new), {"k": "닛몰캐쉬", "t": 3, "f": "CXG", "c": 4, "x": 1, "g": 20000, "gn": 7, "a": "A0"})


class Guards(unittest.TestCase):   # 검증 V8 뮤테이션 생존 가드 — 한 줄 되돌리면 실패해야 하는 것들
    def test_relight_only_ungraded_or_breaking(self):   # 경중 0·1 채점 NO 한 매체 lv 엔트리 = 재점등 0(260924 계약)
        t = ep("2026-09-29 09:46")
        st = armed_state()
        g1 = cand("u1", "닛몰캐쉬 폭로", t, cross=1, solo=1, grade=1, breaking=False)
        out, _ = S.run([g1], [], ARMED, st, t, net=False)
        self.assertEqual(out[0]["lv"]["t"], 2)
        self.assertFalse(out[0].get("breaking_candidate"))              # 채점 NO(경중 1) = 재점등 0
        g0 = cand("u2", "닛몰캐쉬 근황", t, cross=1, solo=1)
        out, _ = S.run([g0], [], ARMED, armed_state(), t, net=False)
        self.assertTrue(out[0].get("breaking_candidate"))               # 채점 전 = 재점등(판정·채점 대상)

    def test_ro_lane_does_not_save_state(self):
        import time as _t
        with tempfile.TemporaryDirectory() as d:
            stp, cp = Path(d) / "live_state.json", Path(d) / "candidates.json"
            st = L.new_state()
            st["tl"] = [int(_t.time() // 60)]
            L.save_state(st, stp)
            before = stp.read_bytes()
            cp.write_text("[]", encoding="utf-8")
            old = (L.STATE, S.CAND, L.STATE_RO, L.ON, sys.argv)
            L.STATE, S.CAND, L.STATE_RO, L.ON, sys.argv = stp, cp, True, True, ["live_seed.py", str(Path(d) / "none.json")]
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    S.main()
            finally:
                L.STATE, S.CAND, L.STATE_RO, L.ON, sys.argv = old
            self.assertEqual(stp.read_bytes(), before)

    def test_kill_switch_file_push_and_judge(self):
        c = {"breaking": True, "grade": 1, "cross": 1, "title": "t", "lv": {"k": "x", "t": 3}}
        self.assertTrue(PS.is_breaking(c) and PS.push_cross_ok(c))
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "scraper").mkdir()
            (Path(d) / "scraper" / "live_signal.off").write_text("", encoding="utf-8")
            old = PS.ROOT
            PS.ROOT = Path(d)
            try:
                self.assertFalse(PS.is_breaking(c))
                self.assertFalse(PS.push_cross_ok(c))
            finally:
                PS.ROOT = old
        bj = _load(ROOT / ".github" / "scripts" / "breaking_judge.py", "bj_off")
        bj._LIVE_OFF = True
        self.assertEqual(bj._lv_t(c), 0)

    def test_kill_switch_file_strips_lv_in_to_candidates(self):
        T = S.T
        now = datetime.now(KST).timestamp()
        prev = {"id": "U", "url": "U", "title": "닛몰캐쉬 폭로", "cross": 3, "event_key": "U", "lv": {"k": "닛몰캐쉬", "t": 3},
                "published": utc(now - 1800), "first_seen": iso(now - 1800), "cluster_members": ["U", "V", "W"], "arts": 3}
        rep = {"link": "U", "title": "닛몰캐쉬 폭로", "publisher": "매체", "category": "", "published": utc(now - 1800),
               "is_cluster_rep": True, "cross_score": 3, "burst": 0, "cluster_size": 3, "cluster_members": ["U", "V", "W"],
               "breaking_pick": {"url": "U", "media": "매체", "title": "닛몰캐쉬 폭로"}}
        o = (T.SRC, T.DST, T._LIVE_OFF)
        try:
            with tempfile.TemporaryDirectory() as d:
                for off, want in ((False, True), (True, False)):
                    T.SRC, T.DST, T._LIVE_OFF = Path(d) / "a.json", Path(d) / "c.json", off
                    T.SRC.write_text(json.dumps([rep], ensure_ascii=False), encoding="utf-8")
                    T.DST.write_text(json.dumps([prev], ensure_ascii=False), encoding="utf-8")
                    with contextlib.redirect_stdout(io.StringIO()):
                        T.main()
                    out = {c["url"]: c for c in json.loads(T.DST.read_text(encoding="utf-8"))}
                    self.assertEqual("lv" in out["U"], want)
        finally:
            T.SRC, T.DST, T._LIVE_OFF = o

    def test_no_decode_after_google_failure(self):   # glive — 이 회차 구글 실패 있음 = 원문 해제도 쉰다(네트워크 0)
        import gnews_search as G
        t = ep("2026-09-29 10:31")
        st, fetch = strong_state(t)
        calls = []
        old = (G.STATS.get("fail"), G.decode)
        G.STATS["fail"], G.decode = 1, (lambda link, http=None: calls.append(link) or "")
        try:
            S.run([], [], ARMED, st, t, gn_fetch=fetch)
        finally:
            G.STATS["fail"], G.decode = old
        self.assertEqual(calls, [])

    def test_ro_created_seed_recorded_by_runner(self):   # V8 — 폰이 만든 씨앗도 러너 장부(sd)에 첫 기록
        now = ep("2026-09-29 10:31")
        st = L.new_state()
        _strong(st, "닛몰캐쉬", now, {"p": int(now - 5000), "t": "닛몰캐쉬, 채널 삭제", "m": "금강일보", "l": "https://g/A"})
        seed = S._seed_entry("닛몰캐쉬", st["k"]["닛몰캐쉬"], st["gn"]["닛몰캐쉬"], now - 900)
        seed["lv"] = L.lv_of(st, "닛몰캐쉬", now)
        seed.update(breaking=False, breaking_rubric="NO", grade=1)
        S.run([seed], [], EMPTY, st, now, net=False, gn_decode=lambda l: "")
        self.assertEqual((st["sd"]["닛몰캐쉬"]["u"], st["sd"]["닛몰캐쉬"]["breaking_rubric"]), ("https://g/A", "NO"))


class PushMain(unittest.TestCase):   # push_send.main 실제 실행(웹푸시·AI 스텁) — 강·약 키 · 에피소드 AI 필수 · 강 키 적중 원장 기록(검증 V1·V8)
    def round(self, cands, sent=None, events=None, ai="none", state=None):
        import types
        from datetime import datetime as _dt
        now_iso = _dt.now(KST).isoformat(timespec="seconds")
        log = []
        pw = types.ModuleType("pywebpush")

        class WPE(Exception):
            pass
        pw.webpush, pw.WebPushException = (lambda subscription_info, data, **kw: log.append(json.loads(data)["body"])), WPE

        def fake_ai(title, pool):
            if not pool:
                PS._AI_LAST["ok"] = True
                return None
            PS._AI_LAST["ok"] = ai != "fail"
            return 0 if ai == "same" else None
        with tempfile.TemporaryDirectory() as d:
            D = Path(d)
            (D / "subs.json").write_text(json.dumps([{"endpoint": "https://push/x", "keys": {}}]), encoding="utf-8")
            (D / "sent.json").write_text(json.dumps({k: now_iso for k in (sent or [])}), encoding="utf-8")
            (D / "ev.json").write_text(json.dumps([dict(e, ts=now_iso) for e in (events or [])], ensure_ascii=False), encoding="utf-8")
            (D / "cand.json").write_text(json.dumps(cands, ensure_ascii=False), encoding="utf-8")
            (D / "state.json").write_text(json.dumps(state or {}, ensure_ascii=False), encoding="utf-8")
            keep = {n: getattr(PS, n) for n in ("SUBS", "SENT", "CAND", "SENT_EV", "LIVE_STATE", "vapid_pem", "notif_icon", "_ai_same_event", "ISS_PUSH")}
            old_mod, old_argv, old_env = sys.modules.get("pywebpush"), sys.argv, os.environ.get("VAPID_PRIVATE_KEY")
            PS.SUBS, PS.SENT, PS.CAND, PS.SENT_EV, PS.LIVE_STATE = D / "subs.json", D / "sent.json", D / "cand.json", D / "ev.json", D / "state.json"
            PS.vapid_pem, PS.notif_icon, PS._ai_same_event, PS.ISS_PUSH = (lambda raw: "/dev/null"), (lambda k, t: ""), fake_ai, False
            sys.modules["pywebpush"], sys.argv, os.environ["VAPID_PRIVATE_KEY"] = pw, ["push_send.py"], "x"
            try:
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    PS.main()
            finally:
                for n, v in keep.items():
                    setattr(PS, n, v)
                sys.argv = old_argv
                if old_mod is None:
                    sys.modules.pop("pywebpush", None)
                else:
                    sys.modules["pywebpush"] = old_mod
                if old_env is None:
                    os.environ.pop("VAPID_PRIVATE_KEY", None)
                else:
                    os.environ["VAPID_PRIVATE_KEY"] = old_env
            return log, set(json.loads((D / "sent.json").read_text(encoding="utf-8")))

    def brk(self, url, title, **kw):
        now = int(datetime.now(KST).timestamp())
        c = {"url": url, "id": url, "event_key": url, "title": title, "breaking": True, "grade": 2, "cross": 3,
             "published": utc(now - 900), "first_seen": iso(now - 900), "cluster_members": [url]}
        c.update(kw)
        return c

    def test_strong_key_hit_records_url(self):
        log, sent = self.round([self.brk("R", "닛몰캐쉬 사생활 논란", event_key="SEED")], sent=["SEED"])
        self.assertEqual(log, [])
        self.assertIn("R", sent)                                             # 씨앗 키 승계 실후보의 자기 url 이 원장에

    def test_title_hash_hit_records_nothing_else(self):
        c = self.brk("B", "北 동해상 탄도미사일 발사")
        tkey = [k for k in PS.dedup_keys(c) if k.startswith("t:")][0]
        log, sent = self.round([c], sent=[tkey])
        self.assertEqual(log, [])
        self.assertNotIn("B", sent)                                          # 해시 충돌 = 별개 사건일 수 있다 → url 안 적음

    def test_episode_key_needs_ai(self):
        a = "2026-09-29T09:46:00+0900"
        c = self.brk("B", "[속보] 하이브 본사 압수수색", lv={"k": "하이브", "t": 3, "a": a})
        ep_key = "lv:하이브@" + a
        ev = [{"title": "하이브 방시혁 의장 입장문", "k": "brk"}]
        self.assertEqual(len(self.round([c], sent=[ep_key], events=ev, ai="none")[0]), 1)   # AI = 다른 사건 → 발송
        self.assertEqual(len(self.round([c], sent=[ep_key], events=ev, ai="fail")[0]), 1)   # AI 실패 = 발송(fail-open · 운영자 260929)
        self.assertEqual(self.round([c], sent=[ep_key], events=ev, ai="same")[0], [])      # AI = 같은 사건 → 억제

    def test_seed_ai_fail_sends(self):   # 운영자 260929 «중복 확인하는 ai가 고장나면 또 보내야지» — 씨앗도 fail-open(구판 = 영구 보류)
        c = self.brk("https://g/A", "크리에이터 닛몰캐쉬, 폭언·폭행에 비하 논란까지", seed="gn", lv={"k": "닛몰캐쉬", "t": 3, "a": "2026-09-29T09:46:00+0900"})
        ev = [{"title": "北 동해상 탄도미사일 발사", "k": "brk"}]
        self.assertEqual(len(self.round([c], events=ev, ai="fail")[0]), 1)
        self.assertEqual(self.round([c], events=ev, ai="same")[0], [])       # 심판이 같은 사건이라 하면 억제는 그대로

    def test_fail_open_ledger_blocks_next_round(self):   # 평의회260929-3 D#5 — 1회차 AI 실패로 나간 씨앗의 키가 원장에 남아 2회차엔 0발(이관 실후보 포함)
        a = "2026-09-29T09:46:00+0900"
        seed = self.brk("https://g/A", "크리에이터 닛몰캐쉬, 폭언·폭행에 비하 논란까지", seed="gn", lv={"k": "닛몰캐쉬", "t": 3, "a": a})
        ev = [{"title": "北 동해상 탄도미사일 발사", "k": "brk"}]
        log1, sent1 = self.round([seed], events=ev, ai="fail")
        self.assertEqual(len(log1), 1)
        self.assertIn("https://g/A", sent1)
        self.assertIn("lv:닛몰캐쉬@" + a, sent1)
        ev2 = ev + [{"title": seed["title"], "k": "brk"}]
        self.assertEqual(self.round([seed], sent=sorted(sent1), events=ev2, ai="fail")[0], [])        # 같은 씨앗 = 강한 키
        real = self.brk("https://r/1", "닛몰캐쉬 데이트폭력 폭로 파문", event_key="https://g/A", lv={"k": "닛몰캐쉬", "t": 3, "a": a})
        self.assertEqual(self.round([real], sent=sorted(sent1), events=ev2, ai="fail")[0], [])        # 이관 실후보 = 씨앗 키 승계

    def test_episode_hit_without_pool_sends(self):   # 평의회260929-3 G#6·D#4 — 에피소드 키는 있는데 비교 목록이 비었다 = 확인 불가 → 발송(fail-open · 로그)
        a = "2026-09-29T09:46:00+0900"
        c = self.brk("B", "[속보] 하이브 본사 압수수색", lv={"k": "하이브", "t": 3, "a": a})
        self.assertEqual(len(self.round([c], sent=["lv:하이브@" + a], events=[], ai="none")[0]), 1)


    def test_surged_name_blocks_later_urgent(self):   # 운영자 260929 «한번 긴급뜬건 다음에 긴급으로 안떠야» — 급등 알림 뒤 같은 이름 기사 = 0발(4h 창)
        import time as _t
        now = int(_t.time())
        st = {"sgx": {"닛몰캐쉬": [now - 600, "유튜버 닛몰캐쉬 폭로 나온듯"]}}
        c = self.brk("https://r/1", "크리에이터 닛몰캐쉬, 폭언·폭행에 비하 논란까지", lv={"k": "닛몰캐쉬", "t": 3, "a": "2026-09-29T09:46:00+0900"})
        log, sent = self.round([c], state=st)
        self.assertEqual(log, [])
        self.assertIn("https://r/1", sent)                                   # 억제 도장 = 다음 회차 재평가 0
        other = self.brk("https://r/2", "BTS 댄서 출신 유튜버 사생활 논란")     # 이름이 달라도 같은 사건 = 급등 글 제목과 사건중복 심판
        self.assertEqual(self.round([other], state=st, ai="same")[0], [])
        self.assertEqual(len(self.round([other], state={}, ai="same")[0]), 1)   # 급등 없음 = 비교 목록 0 = 종전대로 발송
        sib = self.brk("https://r/3", "닛몰캐쉬 측 법적 대응 입장")          # 확산 꼬리표 없는 형제 기사도 제목에 이름 = 같은 사건(평의회 D#3)
        self.assertEqual(self.round([sib], state=st, ai="none")[0], [])
        old = {"sgx": {"닛몰캐쉬": [now - 5 * 3600, "유튜버 닛몰캐쉬 폭로 나온듯"]}}   # 4h 창 밖 = 같은 이름이라도 심판이 가른다(별개 사건 가능)
        self.assertEqual(len(self.round([c], state=old, ai="none")[0]), 1)
        self.assertEqual(self.round([c], state=old, ai="same")[0], [])
        os.environ["LIVE_SURGE"] = "0"                                       # 끄기 = 억제도 함께 꺼진다
        try:
            self.assertEqual(len(self.round([c], state=st, ai="none")[0]), 1)
        finally:
            os.environ.pop("LIVE_SURGE", None)


def surge_snap(t, comms, x=()):
    """comms = [[(제목, 댓글수)…] 커뮤니티별] — 급등 원문 고르기용(주소·댓글 포함)."""
    upd = datetime.fromtimestamp(t, KST)
    return {"tbs": {"updated": upd.strftime("%Y-%m-%d %H:%M"),
                    "communities": [{"id": f"c{i}", "name": f"커뮤{i}",
                                     "posts": [{"title": ti, "comment": cm, "url": f"https://c{i}/{j}"} for j, (ti, cm) in enumerate(ts)]}
                                    for i, ts in enumerate(comms)]},
            "sns": {"updated": upd.isoformat(), "xtrends": [{"query": q} for q in x]}, "social": []}


FOUR = [[("유튜버 닛몰캐쉬 폭로 나온듯", 40)], [("닛몰캐쉬 전여친 폭로", 90)], [("닛몰캐쉬 녹취록", 10)], [("닛몰캐쉬 채널", 5)]]


class Surge(unittest.TestCase):   # 급등 = 무장 ∧ 커뮤니티 1곳 이하 → 4곳↑(60분 안) · 운영자 260929 «닛몰캐쉬 필수 · 최대한 빠르게»
    def ep2(self, first, second, x=("닛몰캐쉬",), st=None):
        st = st or L.new_state()
        t0, t1 = ep("2026-09-29 09:05"), ep("2026-09-29 09:37")
        L.update(st, surge_snap(t0, first), t0 + 60)
        L.update(st, surge_snap(t1, second, x), t1 + 60)
        return st["k"].get("닛몰캐쉬") or {}

    def test_one_to_four_armed(self):
        e = self.ep2([[("유튜버 닛몰캐쉬 폭로 나온듯", 3)], [("다른 글", 1)]], FOUR)
        self.assertTrue(e.get("sg"))
        self.assertEqual((e["sp"]["u"], e["sp"]["c"]), ("https://c1/0", 4))   # 댓글 가장 많은 글 · 4곳

    def test_gradual_no(self):
        self.assertFalse(self.ep2([[("닛몰캐쉬 근황", 1)], [("닛몰캐쉬 방송", 1)]], FOUR).get("sg"))   # 2곳 → 4곳 = 느린 확산

    def test_three_no(self):
        self.assertFalse(self.ep2([], FOUR[:3]).get("sg"))

    def test_unarmed_no(self):
        self.assertFalse(self.ep2([], FOUR, x=()).get("sg"))                 # 커뮤니티 한 갈래뿐 = 무장 아님

    def test_chronic_no(self):
        st = L.new_state()
        b = str(int((ep("2026-09-28 09:00")) // L.BUCKET_S))
        st["tb"], st["hi"] = {b: 20}, {"닛몰캐쉬": {b: 10}}                  # 지난 72h 스냅샷 절반에 2곳↑ = 만성어
        self.assertFalse(self.ep2([], FOUR, st=st).get("sg"))

    def test_read_only_lane_no(self):
        old = L.STATE_RO
        L.STATE_RO = True
        try:
            self.assertFalse(self.ep2([], FOUR).get("sg"))
        finally:
            L.STATE_RO = old

    def test_filtered_name_already_spread_no(self):   # 이름 거르개가 버리는 말(「뿌요뿌요」 = 동사 꼬리 요)이 이미 5곳에 퍼져 있었다 = 급등 아님(평의회 A#1)
        st = L.new_state()
        t0, t1 = ep("2026-09-24 20:06"), ep("2026-09-24 20:41")
        five = [[("오늘자 뿌요뿌요 한일전", 3)] for _ in range(5)]
        L.update(st, surge_snap(t0, five), t0 + 60)
        L.update(st, surge_snap(t1, five + [[("뿌요뿌요 하이라이트", 9)]] * 2, ("뿌요뿌요",)), t1 + 60)
        self.assertFalse((st["k"].get("뿌요뿌요") or {}).get("sg"))

    def test_late_arming_same_snapshot(self):   # 1→4 스냅샷 다음 회차(같은 스냅샷 재독)에 트렌드가 붙어도 판정한다(평의회 A#2)
        st = L.new_state()
        t0, t1 = ep("2026-09-29 09:05"), ep("2026-09-29 09:37")
        L.update(st, surge_snap(t0, [[("유튜버 닛몰캐쉬 폭로 나온듯", 3)]]), t0 + 60)
        s1 = surge_snap(t1, FOUR)
        L.update(st, s1, t1 + 60)
        self.assertFalse((st["k"].get("닛몰캐쉬") or {}).get("sg"))       # 커뮤니티 한 갈래 = 무장 전
        later = t1 + 17 * 60
        s2 = dict(s1, sns={"updated": datetime.fromtimestamp(later, KST).isoformat(), "xtrends": [{"query": "닛몰캐쉬"}]})
        L.update(st, s2, later)
        self.assertTrue(st["k"]["닛몰캐쉬"].get("sg"))

    def test_post_match_like_count(self):   # 글 고르기 = 곳수와 같은 셈(「쯔양처럼·쯔양으로·쯔양까지」 · 평의회 A#4)
        st = L.new_state()
        t0, t1 = ep("2026-09-21 17:05"), ep("2026-09-21 17:37")
        L.update(st, surge_snap(t0, []), t0 + 60)
        four = [[("쯔양처럼 먹방", 5)], [("쯔양으로 난리", 50)], [("쯔양까지 수익 중단", 9)], [("쯔양 근황", 1)]]
        L.update(st, surge_snap(t1, four, ("쯔양",)), t1 + 60)
        sp = (st["k"].get("쯔양") or {}).get("sp") or {}
        self.assertEqual((sp.get("c"), sp.get("u")), (4, "https://c1/0"))

    def test_collection_gap_no_stale_baseline(self):   # 수집 공백 120분 넘음 = 비교할 회차 없음(평의회 B · 착지 실패 반복 발송 상한)
        st = L.new_state()
        t0, t1 = ep("2026-09-29 06:00"), ep("2026-09-29 09:37")
        L.update(st, surge_snap(t0, [[("닛몰캐쉬 근황", 1)]]), t0 + 60)
        L.update(st, surge_snap(t1, FOUR, ("닛몰캐쉬",)), t1 + 60)
        self.assertFalse((st["k"].get("닛몰캐쉬") or {}).get("sg"))

    def test_no_burst_on_first_deploy(self):   # 급등 기록(c2)이 없던 옛 상태 = 첫 회차엔 비교 원료가 없다 → 판정 안 함
        st = L.new_state()
        t0 = ep("2026-09-29 09:05")
        L.update(st, surge_snap(t0, []), t0 + 60)
        st.pop("c2s", None)
        st["c2"] = {}
        t1 = ep("2026-09-29 09:37")
        L.update(st, surge_snap(t1, FOUR, ("닛몰캐쉬",)), t1 + 60)
        self.assertFalse((st["k"].get("닛몰캐쉬") or {}).get("sg"))

    def test_once_per_episode(self):
        st = L.new_state()
        e = self.ep2([], FOUR, st=st)
        sg = e["sg"]
        t2 = ep("2026-09-29 10:05")
        L.update(st, surge_snap(t2, FOUR + [[("닛몰캐쉬 정리", 1)]] * 3, ("닛몰캐쉬",)), t2 + 60)
        self.assertEqual(st["k"]["닛몰캐쉬"]["sg"], sg)


class SurgePush(unittest.TestCase):   # push_send --surge = 알림 → 요약 요청 · 기록은 건마다 저장 · 긴급이 먼저 나간 이름은 생략
    def run_surge(self, st, cands=(), events=(), sent=None, subs=True, ask_fail=False):
        import types
        from datetime import datetime as _dt
        log = []
        pw = types.ModuleType("pywebpush")

        class WPE(Exception):
            pass
        pw.webpush, pw.WebPushException = (lambda subscription_info, data, **kw: log.append(json.loads(data))), WPE
        now_iso = _dt.now(KST).isoformat(timespec="seconds")
        with tempfile.TemporaryDirectory() as d:
            D = Path(d)
            (D / "state.json").write_text(json.dumps(st, ensure_ascii=False), encoding="utf-8")
            (D / "subs.json").write_text(json.dumps([{"endpoint": "https://push/x"}] if subs else []), encoding="utf-8")
            (D / "sent.json").write_text(json.dumps(sent or {}), encoding="utf-8")
            (D / "ev.json").write_text(json.dumps([dict(e, ts=now_iso) for e in events], ensure_ascii=False), encoding="utf-8")
            (D / "cand.json").write_text(json.dumps(list(cands), ensure_ascii=False), encoding="utf-8")
            if ask_fail:
                (D / "asks").write_text("not a dir", encoding="utf-8")
            keep = {n: getattr(PS, n) for n in ("LIVE_STATE", "ASKS", "ROOT", "SUBS", "SENT", "SENT_EV", "CAND", "vapid_pem", "notif_icon")}
            PS.LIVE_STATE, PS.ASKS, PS.ROOT, PS.SUBS, PS.SENT, PS.SENT_EV, PS.CAND = (D / "state.json", D / "asks", D, D / "subs.json",
                                                                                     D / "sent.json", D / "ev.json", D / "cand.json")
            PS.vapid_pem, PS.notif_icon = (lambda raw: "/dev/null"), (lambda k, t: "")
            old_mod, old_env = sys.modules.get("pywebpush"), os.environ.get("VAPID_PRIVATE_KEY")
            sys.modules["pywebpush"], os.environ["VAPID_PRIVATE_KEY"] = pw, "x"
            out = io.StringIO()
            try:
                with contextlib.redirect_stdout(out):
                    PS.surge_run()
            finally:
                for n, v in keep.items():
                    setattr(PS, n, v)
                if old_mod is None:
                    sys.modules.pop("pywebpush", None)
                else:
                    sys.modules["pywebpush"] = old_mod
                if old_env is None:
                    os.environ.pop("VAPID_PRIVATE_KEY", None)
                else:
                    os.environ["VAPID_PRIVATE_KEY"] = old_env
            asks = [json.loads((D / ln[len("ASK_FILE="):]).read_text(encoding="utf-8"))
                    for ln in out.getvalue().splitlines() if ln.startswith("ASK_FILE=")]
            return log, json.loads((D / "state.json").read_text(encoding="utf-8")), asks, out.getvalue()

    def fresh(self, **ep):
        import time as _t
        e = {"sg": int(_t.time()) - 60, "sp": {"u": "https://fm/1", "t": "유튜버 닛몰캐쉬 폭로 나온듯", "m": "에펨", "c": 4}}
        e.update(ep)
        return {"k": {"닛몰캐쉬": e}}

    def test_surges_window_and_switch(self):
        now = 10_000
        st = {"k": {"a": {"sg": now - 100, "sp": {"u": "https://x/1"}}, "b": {"sg": now - 100, "ss": now - 50, "sp": {"u": "https://x/2"}},
                    "c": {"sg": now - PS.SURGE_MAX_S - 1, "sp": {"u": "https://x/3"}}, "d": {"sg": now - 100},
                    "e": {"sg": now - 100, "sp": {"u": "javascript:alert(1)"}}}}
        self.assertEqual([k for k, _ in PS.surges(st, now)], ["a"])         # 보낸 것·1시간 지난 것·원문 없는 것·주소 아닌 것 = 제외
        os.environ["LIVE_SURGE"] = "0"
        try:
            self.assertEqual(PS.surges(st, now), [])
        finally:
            os.environ.pop("LIVE_SURGE", None)

    def test_push_first_then_ask_when_news(self):
        log, st, asks, _ = self.run_surge(self.fresh())
        self.assertEqual(len(log), 1)
        self.assertTrue(log[0]["body"].startswith("(긴급) 유튜버 닛몰캐쉬 폭로 나온듯"))
        self.assertEqual(log[0]["url"], "https://fm/1")                      # 본문 탭 = 그 커뮤니티 글
        ep_ = st["k"]["닛몰캐쉬"]
        self.assertTrue(ep_.get("ss") and "닛몰캐쉬" in st["sgx"])
        self.assertEqual(asks, [])                                          # 기사 없음 = 요약 요청 대기
        news = [cand("https://r/1", "크리에이터 닛몰캐쉬, 폭언·폭행에 비하 논란까지", ep("2026-09-29 10:16"))]
        log2, st2, asks2, _ = self.run_surge(st, cands=news)
        self.assertEqual(log2, [])                                          # 알림은 한 번
        self.assertEqual(len(asks2), 1)
        self.assertEqual((asks2[0]["srcUrl"], asks2[0]["link"], asks2[0]["preset"]["noai"]), ("https://fm/1", "", 1))   # SNS 카드 「전송」과 같은 요청
        self.assertTrue(st2["k"]["닛몰캐쉬"].get("sa"))
        self.assertEqual(self.run_surge(st2, cands=news)[2], [])            # 요청도 한 번

    def test_ask_after_hour_without_news(self):
        import time as _t
        st = self.fresh(ss=int(_t.time()) - PS.SURGE_ASK_S - 1)
        self.assertEqual(len(self.run_surge(st)[2]), 1)

    def test_already_urgent_name_skips(self):   # 뉴스 긴급이 먼저 나간 뒤 급등 = 다시 안 울림(평의회 B·C·H)
        log, st, asks, _ = self.run_surge(self.fresh(), events=[{"title": "크리에이터 닛몰캐쉬, 폭언·폭행에 비하 논란까지", "k": "brk"}])
        self.assertEqual((log, asks), ([], []))
        self.assertTrue(st["k"]["닛몰캐쉬"].get("ss") and st["k"]["닛몰캐쉬"].get("sa"))
        self.assertEqual(len(self.run_surge(self.fresh(), events=[{"title": "닛몰캐쉬 관련 이슈", "k": "iss"}])[0]), 1)   # 이슈 알림은 긴급 아님

    def test_same_name_resurge_skips(self):   # 에피소드가 끝난 뒤 같은 이름이 48h 안에 다시 급등 = 다시 안 울림(평의회 D#2)
        import time as _t
        st = self.fresh()
        st["sgx"] = {"닛몰캐쉬": [int(_t.time()) - 13 * 3600, "유튜버 닛몰캐쉬 폭로 나온듯"]}
        log, st2, asks, _ = self.run_surge(st)
        self.assertEqual((log, asks), ([], []))
        self.assertTrue(st2["k"]["닛몰캐쉬"].get("ss"))

    def test_same_post_two_names_once(self):   # 같은 글을 고른 두 이름(「25사단」·「지뢰」 · 「심수봉」·「김다현」) = 알림 1발(평의회 G 재생)
        import time as _t
        sp = {"u": "https://fm/9", "t": "[속보] 25사단서 DMZ 작전 중 중상자 발생…지뢰 추정", "c": 4}
        st = {"k": {"25사단": {"sg": int(_t.time()) - 60, "sp": dict(sp)}, "지뢰": {"sg": int(_t.time()) - 60, "sp": dict(sp)}}}
        log, st2, _, _ = self.run_surge(st)
        self.assertEqual(len(log), 1)
        self.assertTrue(all(e.get("ss") for e in st2["k"].values()))
        st3 = {"k": {"김다현": {"sg": int(_t.time()) - 60, "sp": dict(sp)}, "심수봉": {"sg": 1, "ss": 1, "sp": dict(sp)}}}
        self.assertEqual(self.run_surge(st3)[0], [])                         # 다음 회차에 같은 글로 뜬 이름도 생략

    def test_no_subscribers_retries(self):
        log, st, _, out = self.run_surge(self.fresh(), subs=False)
        self.assertEqual(log, [])
        self.assertFalse(st["k"]["닛몰캐쉬"].get("ss"))                       # 다음 회차 재시도
        self.assertIn("::warning::", out)

    def test_ask_failure_keeps_sent_mark(self):   # 요약 요청이 죽어도 보낸 표시는 남는다 = 같은 알림 재발송 0(평의회 C·H)
        import time as _t
        log, st, asks, out = self.run_surge(self.fresh(ss=int(_t.time()) - PS.SURGE_ASK_S - 1, sg=int(_t.time()) - 4000), ask_fail=True)
        self.assertEqual(asks, [])
        self.assertIn("::warning::", out)
        self.assertFalse(st["k"]["닛몰캐쉬"].get("sa"))                       # 다음 회차 재시도
        log, st, asks, out = self.run_surge(self.fresh(), ask_fail=True)
        self.assertEqual(len(log), 1)
        self.assertTrue(st["k"]["닛몰캐쉬"].get("ss"))


class Budget(unittest.TestCase):
    def test_trim_protects_lv(self):
        cs = [{"url": f"u{i}", "title": "x" * 200} for i in range(10)]
        cs[-1]["lv"] = {"k": "a", "t": 3}
        blob, cut = S.fit_budget(cs, 1200)
        self.assertLessEqual(len(blob.encode("utf-8")), 1200)
        self.assertTrue(any(c.get("lv") for c in cs))
        self.assertGreater(cut, 0)


class Gates(unittest.TestCase):
    def test_strong_opens_celeb_and_investigation(self):
        self.assertIsNotNone(BG.gate_reason("배우 ○○, 열애 인정"))
        self.assertIsNone(BG.gate_reason("배우 ○○, 열애 인정", live=3))
        self.assertIsNone(BG.gate_reason("유튜버 ○○ 전 연인 고소…경찰 수사 착수", live=3))      # [강] 연예 = 수사 단계 개방(운영자 260929 «고소 수사도 열어»)
        self.assertIsNotNone(BG.gate_reason("유튜버 ○○, 항소심서 징역 3년 선고", live=3))       # 재판 단계 = 그대로(운영자 260921)
        self.assertIsNotNone(BG.gate_reason("유튜버 ○○ 촬영장 화재로 2명 사망", live=3))   # 인명 문턱은 그대로
        self.assertIsNotNone(BG.gate_reason("배우 ○○, 열애 인정", live=2))                 # [중] = 면제 없음


class Push(unittest.TestCase):
    def test_is_breaking_grade1_needs_strong(self):
        base = {"breaking": True, "grade": 1}
        self.assertFalse(PS.is_breaking(base))
        self.assertTrue(PS.is_breaking(dict(base, lv={"t": 3})))
        self.assertFalse(PS.is_breaking(dict(base, lv={"t": 2})))
        self.assertFalse(PS.is_breaking({"breaking": True, "grade": None, "lv": {"t": 3}}))   # 미채점 보류 불변
        self.assertFalse(PS.is_breaking({"breaking": True, "grade": 0, "lv": {"t": 3}}))   # [강]이어도 경중 0 = 보류(두 번째 AI 층 유지 · 검증 V3·V7)

    def test_cross_by_outside_outlets(self):
        self.assertFalse(PS.push_cross_ok({"cross": 1, "title": "닛몰캐쉬 폭로"}))
        self.assertFalse(PS.push_cross_ok({"cross": 1, "title": "닛몰캐쉬 폭로", "lv": {"t": 2, "gn": 3}}))   # [중]+gn≥3 = 새 사건 확인 거절(재점화) · 평의회260929-2
        self.assertTrue(PS.push_cross_ok({"cross": 1, "title": "닛몰캐쉬 폭로", "lv": {"t": 3}}))


class Judge(unittest.TestCase):
    def setUp(self):
        self.bj = _load(ROOT / ".github" / "scripts" / "breaking_judge.py", "bj_lv")

    def test_rows_tail_and_stamp(self):
        c = {"title": "유명 유튜버, 데이트폭력 의혹", "published": "",
             "lv": {"k": "닛몰캐쉬", "t": 3, "c": 4, "x": 1, "gn": 7}}
        rows = self.bj.build_rows([c])
        self.assertEqual(rows[0][1], "유명 유튜버, 데이트폭력 의혹 〔확산 강 «닛몰캐쉬»: 커뮤니티 4곳 동시 · 엑스 트렌드 1위 · 언론 7곳〕 〔발행시각 미상〕")
        plain = {"title": c["title"]}
        self.assertNotEqual(self.bj._stamp(c), self.bj._stamp(plain))               # [강] = 1회 재판정
        self.assertEqual(self.bj._stamp(dict(c, lv={"k": "닛몰캐쉬", "t": 2})), self.bj._stamp(plain))   # [중] = 도장 불변
        self.assertEqual(self.bj._stamp(c), self.bj._stamp(dict(c, lv=dict(c["lv"], c=9, x=3))))      # 수치 변화 = 재판정 0

    def test_no_lv3_stamp_without_tail(self):   # 평의회1 #10 — 꼬리표 모듈 import 실패 = lv3 안 접음(복구 뒤 [강] 꼬리표로 1회 재판정)
        c = {"title": "유명 유튜버, 데이트폭력 의혹", "lv": {"k": "닛몰캐쉬", "t": 3, "c": 4}}
        with_tail = self.bj._stamp(c)
        old = self.bj._live_tail
        self.bj._live_tail = None
        try:
            self.assertEqual(self.bj._stamp(c), self.bj._stamp({"title": c["title"]}))
        finally:
            self.bj._live_tail = old
        self.assertNotEqual(with_tail, self.bj._stamp({"title": c["title"]}))

    def test_rubric_ver_is_base_only(self):
        import hashlib
        self.assertIn("📡", self.bj.RUBRIC)
        self.assertEqual(self.bj.RUBRIC_VER, hashlib.sha256(self.bj._RUBRIC_BASE.encode("utf-8")).hexdigest()[:12])

    def test_count_matches_needs_judging(self):
        now = datetime.now(KST)
        fs = now.strftime("%Y-%m-%dT%H:%M:%S%z")
        c1 = {"url": "a", "title": "t1", "first_seen": fs, "lv": {"k": "x", "t": 3}}
        c1["breaking_rubric"] = self.bj._stamp({"title": "t1"})     # [강] 붙기 전 도장 = 재판정 대상
        c2 = {"url": "b", "title": "t2", "first_seen": fs}
        c2["breaking_rubric"] = self.bj._stamp(c2)
        c3 = {"url": "c", "title": "t3", "first_seen": fs, "lv": {"k": "y", "t": 3}}
        c3["breaking_rubric"] = self.bj._stamp(c3)
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "candidates.json"
            p.write_text(json.dumps([c1, c2, c3], ensure_ascii=False), encoding="utf-8")
            self.bj.CAND = p
            buf = io.StringIO()
            old = sys.argv
            sys.argv = ["breaking_judge.py", "--count"]
            try:
                with contextlib.redirect_stdout(buf):
                    self.bj.main()
            finally:
                sys.argv = old
        self.assertEqual(buf.getvalue().strip(), "1")
        self.assertEqual([c["url"] for c in (c1, c2, c3) if self.bj.needs_judging(c)], ["a"])


if __name__ == "__main__":
    unittest.main()
