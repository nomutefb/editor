"""확산 신호 수집함 반영(scraper/live_seed.py) 회귀 — 첨부(익명 대표 포함)·입장·구글 뉴스 씨앗·이관(중복 푸시 0)·[강] 동결·예산 ·
판정기(도장·꼬리표·--count)·게이트 면제·푸시 문턱 짝. 운영자 260929 닛몰캐쉬 실사고."""
import importlib.util
import io
import json
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


class Budget(unittest.TestCase):
    def test_trim_protects_lv(self):
        cs = [{"url": f"u{i}", "title": "x" * 200} for i in range(10)]
        cs[-1]["lv"] = {"k": "a", "t": 3}
        blob, cut = S.fit_budget(cs, 1200)
        self.assertLessEqual(len(blob.encode("utf-8")), 1200)
        self.assertTrue(any(c.get("lv") for c in cs))
        self.assertGreater(cut, 0)


class Gates(unittest.TestCase):
    def test_strong_skips_celeb_and_judicial_only(self):
        self.assertIsNotNone(BG.gate_reason("배우 ○○, 열애 인정"))
        self.assertIsNone(BG.gate_reason("배우 ○○, 열애 인정", live=3))
        self.assertIsNotNone(BG.gate_reason("유튜버 ○○ 전 연인 고소…경찰 수사 착수"))
        self.assertIsNone(BG.gate_reason("유튜버 ○○ 전 연인 고소…경찰 수사 착수", live=3))
        self.assertIsNotNone(BG.gate_reason("유튜버 ○○ 촬영장 화재로 2명 사망", live=3))   # 인명 문턱은 그대로
        self.assertIsNotNone(BG.gate_reason("배우 ○○, 열애 인정", live=2))                 # [중] = 면제 없음


class Push(unittest.TestCase):
    def test_is_breaking_grade1_needs_strong(self):
        base = {"breaking": True, "grade": 1}
        self.assertFalse(PS.is_breaking(base))
        self.assertTrue(PS.is_breaking(dict(base, lv={"t": 3})))
        self.assertFalse(PS.is_breaking(dict(base, lv={"t": 2})))
        self.assertFalse(PS.is_breaking({"breaking": True, "grade": None, "lv": {"t": 3}}))   # 미채점 보류 불변
        self.assertFalse(PS.is_breaking({"breaking": True, "grade": 0, "lv": {"t": 3}}))

    def test_cross_by_outside_outlets(self):
        self.assertFalse(PS.push_cross_ok({"cross": 1, "title": "닛몰캐쉬 폭로"}))
        self.assertTrue(PS.push_cross_ok({"cross": 1, "title": "닛몰캐쉬 폭로", "lv": {"t": 2, "gn": 3}}))
        self.assertTrue(PS.push_cross_ok({"cross": 1, "title": "닛몰캐쉬 폭로", "lv": {"t": 3}}))


class Judge(unittest.TestCase):
    def setUp(self):
        self.bj = _load(ROOT / ".github" / "scripts" / "breaking_judge.py", "bj_lv")

    def test_rows_tail_and_stamp(self):
        c = {"title": "유명 유튜버, 데이트폭력 의혹", "published": "",
             "lv": {"k": "닛몰캐쉬", "t": 3, "c": 4, "x": 1, "gn": 7}}
        rows = self.bj.build_rows([c])
        self.assertEqual(rows[0][1], "유명 유튜버, 데이트폭력 의혹 〔확산 강 «닛몰캐쉬»: 커뮤니티 4곳 동시 · X 1위 · 언론 7곳〕 〔발행시각 미상〕")
        plain = {"title": c["title"]}
        self.assertNotEqual(self.bj._stamp(c), self.bj._stamp(plain))               # [강] = 1회 재판정
        self.assertEqual(self.bj._stamp(dict(c, lv={"k": "닛몰캐쉬", "t": 2})), self.bj._stamp(plain))   # [중] = 도장 불변
        self.assertEqual(self.bj._stamp(c), self.bj._stamp(dict(c, lv=dict(c["lv"], c=9, x=3))))      # 수치 변화 = 재판정 0

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
