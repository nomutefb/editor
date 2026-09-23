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

    def test_korean_rule_unchanged(self):
        self.assertTrue(same("강훈식 비서실장 사의 표명…이 대통령 수용 여부 주목", "[속보] 강훈식 비서실장 사의 표명"))
        self.assertEqual(K.tokenize("[속보] 이재명 대통령 AI 기본법 서명"), {"이재명", "대통령", "ai", "기본법", "서명"})


if __name__ == "__main__":
    unittest.main()
