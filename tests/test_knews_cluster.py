# 영문 제목 클러스터링 회귀(260923) — 영문 기능어로 무관 외신이 묶이고, 화제어(Trump·US·Iran) 사슬로 덩어리가 되던 것 · 네트워크 0
import importlib.util, sys, types, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KN = ROOT / "scraper" / "knews_scraper.py"
sys.path.insert(0, str(ROOT / "scraper"))
for _name in ("feedparser", "requests"):
    try:
        __import__(_name)
    except ImportError:
        sys.modules[_name] = types.ModuleType(_name)


def _load():
    spec = importlib.util.spec_from_file_location("knews_cl", KN)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


K = _load()


def same(a, b):
    return K.same_topic(K.tokenize(a), K.tokenize(b))


class EnglishClusterTest(unittest.TestCase):
    def test_function_words_do_not_link_unrelated_stories(self):
        self.assertFalse(same("Streeting confirms annual £120m payments to Mauritius is on track",
                              "Pakistan’s latest Trump bet is on drone firm already sanctioned to the hilt"))
        self.assertFalse(same("What's at stake when Trump and Xi meet in the US?",
                              "Trump defends actions in Iran and Venezuela in UN General Assembly address"))

    def test_topic_words_alone_do_not_chain(self):
        self.assertFalse(same("US to build two military bases in Greenland under new deal with Denmark",
                              "US and Iran hold first talks since June after Trump's 'annihilation' threat"))
        self.assertFalse(same("AI takes centre stage at UN General Assembly",
                              "Paris: Cézanne takes centre stage at Paris’ Grand Palais"))

    def test_same_event_across_outlets_still_merges(self):
        self.assertTrue(same("Sri Lanka Convicts 15 in Easter 2019 Bomb Attacks",
                             "Sri Lanka court convicts 15 men over deadly Easter Sunday bombings"))   # 제목식 대문자 ↔ 소문자
        self.assertTrue(same("At least 11 dead in mass shooting at house party in South Africa",
                             "At least 11 people killed in South Africa township shooting"))
        self.assertTrue(same("Hurricane Polo intensifies into rare category 5 storm off the coast of Mexico",
                             "Hurricane Polo churns off Mexico"))   # 짧은 제목 = 3개 겹침 ∧ 자카드 0.3

    def test_korean_clustering_unchanged_except_lowercase(self):
        self.assertTrue(same("강훈식 비서실장 사의 표명…이 대통령 수용 여부 주목", "[속보] 강훈식 비서실장 사의 표명"))
        self.assertEqual(K.tokenize("[속보] 이재명 대통령 AI 기본법 서명"), {"이재명", "대통령", "ai", "기본법", "서명"})

    def test_all_caps_acronyms_are_not_function_words(self):
        # 평의회2-2 F3: WHO·IT 같은 약어가 기능어(who·it)로 지워지던 것
        self.assertIn("who", K.tokenize("WHO, 엠폭스 국제 비상사태 선언"))
        self.assertIn("it", K.tokenize("IT 업계 감원 칼바람"))
        self.assertNotIn("who", K.tokenize("Who is running the country now"))
        self.assertIn("at", K.tokenize("aT, 하반기 신입직원 66명 공개채용"))   # 한글 제목 속 영문은 기능어 필터 비대상(평의회2-1)

    def test_dotted_acronyms_normalized(self):
        self.assertIn("us", K.tokenize("Trump Set to Sign Deal on U.S. Presence in Greenland"))
        self.assertIn("un", K.tokenize("U.N. Live Updates: Iran’s President to Address World Leaders"))

    def test_stock_phrases_do_not_link(self):
        # 평의회2-1: "for the first time since" 로 무관 외신이 4개 겹침 경로를 탔다
        self.assertFalse(same("Trump meets US-backed Venezuelan president for first time since Maduro seized",
                              "Live: Pezeshkian set to address UN for the first time since US strikes"))


def _arts(*pairs, title="남아공 총격 11명 사망 파티장"):
    out = []
    for i, (u, p, *src) in enumerate(pairs):
        a = {"title": title, "link": u, "publisher": p, "published": "2026-09-23T07:2%d:00+00:00" % i}
        if src:
            a["src"] = src[0]
        out.append(a)
    return out


class CrossAliasTest(unittest.TestCase):
    def test_rebroadcast_counts_once_but_sister_newsroom_counts(self):
        # 평의회2-5: 연합뉴스TV(연합 재송출)가 교차 +1 을 부풀리던 것
        # 평의회3-7: MBN↔매경은 같은 그룹이어도 같은 제목 0건 = 별개 보도국 → 따로 센다
        arts = _arts(("a", "연합뉴스"), ("b", "연합뉴스TV"), ("c", "MBN"), ("d", "매일경제"))
        K.score_crosspost(arts)
        self.assertEqual({a["cross_score"] for a in arts}, {3})

    def test_chosun_reprint_counts_as_original_newsroom(self):
        # 평의회3-7: 조선일보 연예 피드 = OSEN 80·스포츠조선 15·뉴시스 5(author 칸) — 원 보도국으로 센다
        arts = _arts(("a", "스포츠조선"), ("b", "조선일보", "스포츠조선"), ("c", "조선일보", "OSEN"), ("d", "뉴시스"), ("e", "조선일보", "뉴시스"))
        K.score_crosspost(arts)
        self.assertEqual({a["cross_score"] for a in arts}, {3})   # 스포츠조선 · OSEN · 뉴시스
        self.assertEqual({a["burst"] for a in arts}, {3})

    def test_reprint_source_is_exact_author_on_listed_feed_only(self):
        self.assertEqual(K._reprint_src("조선일보", " OSEN "), "OSEN")
        self.assertIsNone(K._reprint_src("조선일보", "Rosen"))           # 부분 일치 = 영문 인명 오인
        self.assertIsNone(K._reprint_src("조선일보", "김경필 기자"))
        self.assertIsNone(K._reprint_src("NYT", "OSEN"))
        self.assertIsNone(K._reprint_src("조선일보", None))

    def test_collect_stamps_src_from_author(self):
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
        feeds = [{"publisher": "조선일보", "title": "연예", "categories": "entertainment", "url": "https://c.kr/e.xml"}]
        parsed = [types.SimpleNamespace(entries=[
            {"title": "가수 A 컴백", "link": "https://c.kr/1", "published": now, "author": "OSEN"},
            {"title": "배우 B 수상", "link": "https://c.kr/2", "published": now, "author": "김기자"}])]
        from unittest import mock
        with mock.patch.object(K, "prefetch", lambda f: parsed):
            arts, _ = K.collect(feeds, 24)
        self.assertEqual([a.get("src") for a in arts], ["OSEN", None])
        self.assertEqual({a["publisher"] for a in arts}, {"조선일보"})   # 표시·링크는 피드 이름 그대로

    def test_strip_tags_drops_bom(self):
        self.assertEqual(K.strip_tags("\ufeff콜라겐 다음은"), "콜라겐 다음은")

    def test_gossip_stock_phrase_does_not_link(self):
        # 평의회3-3: {sns, 알고, 보니} 만 겹친 사회 단독과 연예 기사가 한 사건이 되던 것
        self.assertFalse(same("[단독] '한우 싸게' SNS 광고…알고 보니 '가짜 계정'",
                              "송혜교 SNS에 올린 김치…알고 보니 '박솔미 김치'"))


class GroupJudgeEnglishTest(unittest.TestCase):
    """평의회2-2 F2: 묶기 판정의 부분어 보강(3개 겹침)이 영문 쌍을 다시 붙여 정본 문턱을 무효로 만들던 것."""

    def test_event_score_does_not_rescue_english_pairs(self):
        spec = importlib.util.spec_from_file_location("gj", ROOT / ".github" / "scripts" / "group_judge.py")
        gj = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gj)
        tok, st = gj._get_matcher()
        a = tok("Trump defends actions in Iran and Venezuela in UN General Assembly address")
        b = tok("Iran's president tells UN Trump strikes were illegal under international law")
        self.assertEqual(gj._event_score(a, b, st), 0)
        ka, kb = tok("강훈식 비서실장 사의 표명"), tok("[속보] 강훈식 비서실장 사의 표명")
        self.assertEqual(gj._event_score(ka, kb, st), 3)

    def test_group_judge_uses_canonical_matcher_without_feedparser(self):
        # 평의회2-2 F1: feedparser 없는 판정 레인이 폴백 미러로 떨어져 수집 레인과 다른 규칙으로 묶던 것
        import subprocess
        code = ("import sys; sys.modules['feedparser']=None; sys.modules['requests']=None; "
                "import importlib.util as u; s=u.spec_from_file_location('g', %r); m=u.module_from_spec(s); s.loader.exec_module(m); "
                "t,st=m._get_matcher(); print(st.__module__)") % str(ROOT / ".github" / "scripts" / "group_judge.py")
        r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=str(ROOT))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), "knews_scraper")


if __name__ == "__main__":
    unittest.main()
