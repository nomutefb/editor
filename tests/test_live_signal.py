"""확산 신호(scraper/live_signal.py) 회귀 — 토큰·불용어·갈래·만성어·단계·구글 뉴스 확인(픽스처) · 9/29 닛몰캐쉬 실스냅샷 재현.
운영자 260929 «닛몰캐쉬 같은 기사가 원체 빨리 들어오고 긴급으로 뜰 수 있는지» — 명성 대신 분포 증거(A4/A5)."""
import gzip
import json
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scraper"))
sys.path.insert(0, str(ROOT / ".github" / "scripts"))
import live_signal as L  # noqa: E402
import gnews_search as G  # noqa: E402

KST = timezone(timedelta(hours=9))
FIX = ROOT / "tests" / "fixtures" / "live"


def ep(s):
    return datetime.strptime(s, "%Y-%m-%d %H:%M").replace(tzinfo=KST).timestamp()


def snap(t, comms, x=(), g=(), social=(), namu=None, namu_t=None):
    """합성 스냅샷 — comms = [[제목…], …](커뮤니티별) · x·g = 검색어 목록."""
    upd = datetime.fromtimestamp(t, KST)
    sns = {"updated": upd.isoformat(), "xtrends": [{"query": q} for q in x],
           "gtrends": [{"query": q, "vol": 10000} for q in g]}
    if namu is not None:
        sns["namu"] = [{"query": q, "rank": i + 1} for i, q in enumerate(namu)]
        sns["namu_updated"] = datetime.fromtimestamp(namu_t or t, KST).isoformat()
    return {"tbs": {"updated": upd.strftime("%Y-%m-%d %H:%M"),
                    "communities": [{"id": f"c{i}", "posts": [{"title": ti} for ti in ts]} for i, ts in enumerate(comms)]},
            "sns": sns, "social": list(social)}


class Tokens(unittest.TestCase):
    def test_name_kept_generic_dropped(self):
        t = L.tokens("[싱갤] 유튜버 닛몰캐쉬 동영상 내리고 런")
        self.assertIn("닛몰캐쉬", t)
        self.assertNotIn("유튜버", t)
        self.assertNotIn("싱갤", t)               # 머리표 제거

    def test_josa_tail_stripped(self):
        self.assertIn("닛몰캐쉬", L.tokens("현재 난리난 닛몰캐쉬가 폭로당함"))
        self.assertNotIn("난리난", L.tokens("현재 난리난 닛몰캐쉬가 폭로당함"))
        self.assertNotIn("유튜버가", L.tokens("유튜버가 또 사고침"))   # 불용어 + 조사 = 원형도 버림

    def test_spaced_name_joined(self):
        self.assertIn("닛몰캐쉬", L.tokens("닛몰 캐쉬 전여친 폭로 정리"))

    def test_verbish_and_short_latin_dropped(self):
        t = L.tokens("때문에 보고 충격적인 AI MZ vs 논란인")
        self.assertFalse(t & {"때문에", "때문", "보고", "충격적인", "ai", "mz", "vs", "논란인"})

    def test_hit_semantics_copy_of_kw_hit(self):
        self.assertFalse(L.hit("로제", "프로젝트 공개"))     # 짧은 말 = 낱말·조사 꼬리만
        self.assertTrue(L.hit("로제", "로제가 밝혔다"))
        self.assertTrue(L.hit("닛몰캐쉬", "닛몰 캐쉬 폭로"))  # 4자↑ = 공백 무시 포함
        self.assertFalse(L.hit("보고", "시험보고서"))


class Families(unittest.TestCase):
    def test_comm_and_x_unify(self):
        t = ep("2026-09-29 09:37")
        s = snap(t, [["유튜버 닛몰캐쉬 폭로 나온듯"], ["닛몰캐쉬 전여친 폭로 ㄷㄷ"], ["닛몰캐쉬 녹취록"], ["다른 글"]],
                 x=["콰삭모짜킹", "닛몰캐쉬", "시험 보고"])
        obs, meta = L.observe(s, t + 60)
        self.assertEqual(obs["닛몰캐쉬"]["C"], 3)
        self.assertEqual(obs["닛몰캐쉬"]["X"], 2)
        self.assertNotIn("X", obs.get("보고", {}))       # 「시험 보고」의 「보고」 = 우연 일치 차단

    def test_multiword_trend_contains_name(self):
        t = ep("2026-09-29 11:08")
        s = snap(t, [["닛몰캐쉬 사과문"], ["닛몰캐쉬 근황"], ["닛몰캐쉬 채널 삭제"]], g=["닛몰캐쉬 데이트폭력"])
        obs, _ = L.observe(s, t + 60)
        self.assertEqual(obs["닛몰캐쉬"]["G"], (1, 10000))

    def test_generic_phrase_trend_ignored(self):
        t = ep("2026-09-24 17:40")
        s = snap(t, [["법적 대응 예고"], ["법적 대응 한다네"], ["법적 대응 ㄷㄷ"]], x=["법적 대응", "추석 연휴"])
        obs, _ = L.observe(s, t + 60)
        self.assertNotIn("법적대응", obs)
        self.assertNotIn("추석연휴", obs)

    def test_stale_snapshot_no_trend_family(self):
        t = ep("2026-09-29 09:37")
        obs, meta = L.observe(snap(t, [["닛몰캐쉬"]] * 3, x=["닛몰캐쉬"]), t + 3 * 3600)
        self.assertNotIn("X", obs.get("닛몰캐쉬", {}))   # 트렌드 스냅샷 3h 정체 = 관측 없음
        self.assertFalse(meta["tbs_fresh"])

    def test_namu_family_and_staleness(self):
        t = ep("2026-09-29 10:00")
        fresh = L.observe(snap(t, [], namu=["닛몰캐쉬"], namu_t=t - 1800), t)[0]
        stale = L.observe(snap(t, [], namu=["닛몰캐쉬"], namu_t=t - 3 * 3600), t)[0]
        self.assertEqual(fresh["닛몰캐쉬"]["N"], 1)
        self.assertNotIn("닛몰캐쉬", stale)


class Tiers(unittest.TestCase):
    def test_single_family_t1_two_families_t2(self):
        st, t = L.new_state(), ep("2026-09-29 09:37")
        L.update(st, snap(t, [["닛몰캐쉬 폭로"]] * 3), t + 60)
        self.assertEqual(L.tier(st["k"]["닛몰캐쉬"], t + 60), 1)
        L.update(st, snap(t + 900, [["닛몰캐쉬 폭로"]] * 3, x=["닛몰캐쉬"]), t + 960)
        e = st["k"]["닛몰캐쉬"]
        self.assertEqual(L.tier(e, t + 960), 2)
        self.assertEqual(e["a"], int(t + 960))
        self.assertEqual(L.active(e, t + 960), "CX")

    def test_idle_episode_expires(self):
        st, t = L.new_state(), ep("2026-09-29 09:37")
        L.update(st, snap(t, [["닛몰캐쉬 폭로"]] * 3, x=["닛몰캐쉬"]), t + 60)
        L.update(st, {"tbs": {}, "sns": {}, "social": []}, t + 13 * 3600)
        self.assertNotIn("닛몰캐쉬", st["k"])

    def test_chronic_token_not_comm(self):
        st, t0 = L.new_state(), ep("2026-09-28 00:00")
        for i in range(24):   # 24시간 내내 3곳에 뜬 말 = 만성(최근 6h 제외 창에 표본 18개 · 전부 2곳↑)
            t = t0 + i * 3600
            L.update(st, snap(t, [["손흥민 골"], ["손흥민 경기"], ["손흥민 근황"]]), t + 60)
        now = t0 + 24 * 3600
        self.assertTrue(L.chronic(st, "손흥민", now))
        before = st["k"]["손흥민"]["f"].get("C")
        L.update(st, snap(now, [["손흥민 골"], ["손흥민 경기"], ["손흥민 근황"]], x=["손흥민"]), now + 60)
        self.assertEqual(st["k"]["손흥민"]["f"].get("C"), before)   # 만성어 = 이번 3곳 동시는 C 갈래로 안 센다
        self.assertIn("X", st["k"]["손흥민"]["f"])

    def test_snapshot_reread_not_double_counted(self):
        st, t = L.new_state(), ep("2026-09-29 09:37")
        s = snap(t, [["닛몰캐쉬"], ["닛몰캐쉬"]])
        L.update(st, s, t + 60)
        L.update(st, s, t + 960)
        self.assertEqual(sum(st["tb"].values()), 1)
        self.assertEqual(sum(st["hi"]["닛몰캐쉬"].values()), 1)

    def test_ours_confirm_needs_novelty(self):
        e = {"a": int(ep("2026-09-24 21:46")), "f": {}}
        old = [{"first_seen": "2026-09-24T12:00:00+0900", "cross": 2}]
        new = [{"first_seen": "2026-09-24T21:30:00+0900", "cross": 5}]
        self.assertFalse(L.confirm_ours(dict(e), new, e["a"] + 60, old))   # 무장 3h 전보다 이른 보도 = 묵은 사건
        e2 = dict(e)
        self.assertTrue(L.confirm_ours(e2, new, e["a"] + 60))
        self.assertEqual((e2["cs"], L.tier(dict(e2, f={"C": e["a"]}), e["a"] + 60)), ("o", 3))

    def test_strong_decays_after_keep_window(self):
        a = int(ep("2026-09-29 09:46"))
        e = {"a": a, "cf": a + 2700, "f": {"C": a}}
        self.assertEqual(L.tier(e, a + 3600), 3)
        self.assertEqual(L.tier(e, a + 2700 + 25 * 3600), 2)


class GoogleNews(unittest.TestCase):
    ITEMS = G.parse_rss((FIX / "gn_nimol.xml").read_text(encoding="utf-8"))

    def test_fixture_parses(self):
        self.assertGreaterEqual(len(self.ITEMS), 10)

    def test_three_outlets_by_1031(self):
        armed = ep("2026-09-29 09:46")
        n2, nov2, first = L.gn_count([i for i in self.ITEMS if i["pub"] <= ep("2026-09-29 10:31")], "닛몰캐쉬",
                                     ep("2026-09-29 10:31"), armed)
        self.assertGreaterEqual(n2, 3)
        self.assertTrue(nov2)
        self.assertEqual(first["m"], "금강일보")
        self.assertIn("닛몰캐쉬", first["t"])

    def test_before_1021_less_than_three(self):
        t = ep("2026-09-29 10:16")
        n, _, _ = L.gn_count([i for i in self.ITEMS if i["pub"] <= t], "닛몰캐쉬", t, ep("2026-09-29 09:46"))
        self.assertLess(n, 3)

    def test_stale_story_not_novel(self):
        armed = ep("2026-09-29 20:00")   # 오전 보도가 무장 3h 전보다 이르다 = 재점화
        _, nov, _ = L.gn_count(self.ITEMS, "닛몰캐쉬", armed + 60, armed)
        self.assertFalse(nov)

    def test_poll_budget_cache_and_confirm(self):
        st, t = L.new_state(), ep("2026-09-29 10:31")
        for k in ("닛몰캐쉬", "가나다라", "마바사아"):
            st["k"][k] = {"d": k, "f": {"C": int(t), "X": int(t)}, "m": {}, "a": int(t - 2700)}
        calls = []
        xml = (FIX / "gn_nimol.xml").read_text(encoding="utf-8")

        def fetch(q):
            calls.append(q)
            return xml if q == "닛몰캐쉬" else "<rss></rss>"
        n = L.gn_poll(st, L.gn_candidates(st, t), t, fetch=fetch, pause=0, max_q=2)
        self.assertEqual(n, 2)
        n2 = L.gn_poll(st, L.gn_candidates(st, t + 60), t + 60, fetch=fetch, pause=0, max_q=6)
        self.assertEqual(n2, 1)                         # 10분 캐시 = 이미 본 이름은 다시 안 묻는다
        # 픽스처는 미래 기사까지 담고 있어 여기서는 확인 여부만 본다(개수·novel 판정은 위 gn_count 시각 필터 시험)
        self.assertIn("닛몰캐쉬", st["gn"])

    def test_failed_fetch_not_cached(self):
        st, t = L.new_state(), ep("2026-09-29 10:31")
        st["k"]["닛몰캐쉬"] = {"d": "닛몰캐쉬", "f": {"C": int(t), "X": int(t)}, "m": {}, "a": int(t - 600)}
        L.gn_poll(st, ["닛몰캐쉬"], t, fetch=lambda q: "", pause=0)
        self.assertNotIn("닛몰캐쉬", st["gn"])

    def test_no_poll_after_window(self):
        st, t = L.new_state(), ep("2026-09-29 20:00")
        st["k"]["닛몰캐쉬"] = {"d": "닛몰캐쉬", "f": {"C": int(t)}, "m": {}, "a": int(t - 7 * 3600)}
        self.assertEqual(L.gn_poll(st, ["닛몰캐쉬"], t, fetch=lambda q: "<rss></rss>", pause=0), 0)


class Tail(unittest.TestCase):
    def test_tail_format(self):
        lv = {"k": "닛몰캐쉬", "t": 3, "c": 4, "x": 1, "g": 10000, "n": 2, "gn": 7}
        self.assertEqual(L.tail(lv), "〔확산 강 «닛몰캐쉬»: 커뮤니티 4곳 동시 · X 1위 · 구글 급상승 1만 · 나무위키 2위 · 언론 7곳〕")
        self.assertEqual(L.tail({"k": "○○", "t": 2, "x": 3}), "〔확산 중 «○○»: X 3위〕")
        self.assertEqual(L.tail({}), "")

    def test_lv_of_omits_missing(self):
        st, t = L.new_state(), ep("2026-09-29 09:37")
        L.update(st, snap(t, [["닛몰캐쉬 폭로"]] * 4, x=["닛몰캐쉬"]), t + 60)
        lv = L.lv_of(st, "닛몰캐쉬", t + 60)
        self.assertEqual({k: lv[k] for k in ("k", "t", "f", "c", "x")}, {"k": "닛몰캐쉬", "t": 2, "f": "CX", "c": 4, "x": 1})
        self.assertNotIn("g", lv)
        self.assertNotIn("gn", lv)


class Replay0929(unittest.TestCase):
    """9/29 실스냅샷(git 이력 추출 · 제목만 · 제목 사전 번호로 압축한 픽스처) — 09:05 미무장 → 09:37 무장(C+X) → 구글 뉴스 10:31 = [강]."""
    D = json.loads(gzip.decompress((FIX / "nimol_0929.json.gz").read_bytes()).decode("utf-8"))

    def snaps(self):
        for s in self.D["snaps"]:
            tbs = {"updated": s["tbs"]["updated"],
                   "communities": [{"id": cm["id"], "posts": [{"title": self.D["titles"][i]} for i in cm["p"]]}
                                   for cm in s["tbs"]["communities"]]}
            yield s["label"], s["t"], {"tbs": tbs, "sns": s["sns"], "social": s["social"]}

    def test_timeline(self):
        st = L.new_state()
        tiers = {}
        for label, now, snap_ in self.snaps():
            L.update(st, snap_, now)
            tiers[label] = L.tier(st["k"].get("닛몰캐쉬"), now)
        self.assertLess(tiers["0905"], 2)
        self.assertEqual(tiers["0937"], 2)
        e = st["k"]["닛몰캐쉬"]
        self.assertIn("C", L.active(e, e["a"]))
        self.assertIn("X", L.active(e, e["a"]))
        items = G.parse_rss((FIX / "gn_nimol.xml").read_text(encoding="utf-8"))
        t1031 = ep("2026-09-29 10:31")

        def fetch(q):   # 그 시각까지 발행분만 = 미래 누설 0
            vis = [i for i in items if i["pub"] <= t1031]
            return "".join('<item><title>%s</title><link>%s</link><pubDate>%s</pubDate><source url="%s">%s</source></item>'
                           % (i["title"], i["link"], datetime.fromtimestamp(i["pub"], timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT"),
                              i["source"], i["sname"]) for i in vis)
        L.gn_poll(st, L.gn_candidates(st, t1031), t1031, fetch=fetch, pause=0)
        self.assertEqual(L.tier(st["k"]["닛몰캐쉬"], t1031), 3)
        self.assertEqual(st["k"]["닛몰캐쉬"]["cs"], "g")


if __name__ == "__main__":
    unittest.main()
