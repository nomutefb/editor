# 급상승 커뮤니티 일치선(운영자 260929 «커뮤니티에서 실명이 일치하면 1만») — 닛몰캐쉬 사례 재현 · 네트워크 0
import importlib.util, json, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("trend_watch_c", ROOT / ".github" / "scripts" / "trend_watch.py")
T = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(T)


class CommLineTest(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
        self._orig = (T.SNS, T.SOCIAL, T.MIN_VOL, T.COMM_MIN_VOL, T.SOCIAL_FETCH, T.LEDGER, T.CANDS)
        T.CANDS = self.d / "cands.json"
        T.SNS, T.SOCIAL, T.MIN_VOL, T.COMM_MIN_VOL = self.d / "s.json", self.d / "c.json", 15000, 10000
        T.SOCIAL_FETCH = False   # CI(GITHUB_ACTIONS)에서도 원격 최신본이 아니라 이 테스트 파일을 읽게

    def tearDown(self):
        T.SNS, T.SOCIAL, T.MIN_VOL, T.COMM_MIN_VOL, T.SOCIAL_FETCH, T.LEDGER, T.CANDS = self._orig

    def run_hot(self, gt, social):
        T.SNS.write_text(json.dumps({"gtrends": gt}, ensure_ascii=False), encoding="utf-8")
        T.SOCIAL.write_text(json.dumps(social, ensure_ascii=False), encoding="utf-8")
        return T.hot()

    def test_comm_match_lowers_line(self):
        out = self.run_hot([{"query": "닛몰캐쉬", "vol": 10000}], [{"title": "현재 난리난 닛몰캐쉬 전여친 폭로 ㄷㄷ.JPG", "burst": 16.15}])
        self.assertIn("닛몰캐쉬", out)
        self.assertIn("커뮤니티", out["닛몰캐쉬"][3])

    def test_no_comm_keeps_15k(self):
        self.assertEqual(self.run_hot([{"query": "닛몰캐쉬", "vol": 10000}], [{"title": "다른 글", "burst": 20}]), {})

    def test_below_comm_line(self):
        self.assertEqual(self.run_hot([{"query": "닛몰캐쉬", "vol": 5000}], [{"title": "닛몰캐쉬 폭로", "burst": 20}]), {})

    def test_two_char_word_keeps_15k(self):   # 2자 말 = 커뮤니티 선 비대상(「삼성」·「살인」 = 다른 사건 일반명사 오탐 · 평의회260929 #2)
        self.assertEqual(self.run_hot([{"query": "삼성", "vol": 10000}], [{"title": "삼성 냉장고 성에 제거법", "burst": 20}]), {})

    def test_offscreen_community_row_ignored(self):   # 화면 하한(SOC_MIN 10 · 표시값 반올림) 미달 행으로는 선을 안 낮춘다
        self.assertEqual(self.run_hot([{"query": "닛몰캐쉬", "vol": 10000}], [{"title": "닛몰캐쉬 폭로", "burst": 9.94}]), {})
        self.assertIn("닛몰캐쉬", self.run_hot([{"query": "닛몰캐쉬", "vol": 10000}], [{"title": "닛몰캐쉬 폭로", "burst": 9.95}]))

    def test_quiet_period_still_sends(self):   # 원장 파일이 있으면 도장이 전부 만료돼도 첫 회차 아님(구판 = 평시 영구 침묵 루프)
        import time
        T.LEDGER = self.d / "sent.json"
        T.LEDGER.write_text(json.dumps({"old": {"first": int(time.time()) - 90000, "q": "old"}}), encoding="utf-8")
        T.SNS.write_text(json.dumps({"gtrends": [{"query": "닛몰캐쉬", "vol": 20000}]}, ensure_ascii=False), encoding="utf-8")
        T.SOCIAL.write_text("[]", encoding="utf-8")
        sent = []
        orig = (T.send, T.DRY)
        T.send, T.DRY = (lambda *a, **k: sent.append(a[0]) or True), False
        try:
            T.main()
        finally:
            T.send, T.DRY = orig
        self.assertEqual(sent, ["닛몰캐쉬"])
        self.assertNotIn("seed", json.loads(T.LEDGER.read_text(encoding="utf-8"))[T.key("닛몰캐쉬")])

    def test_broken_social_file_is_soft(self):
        T.SNS.write_text(json.dumps({"gtrends": [{"query": "닛몰캐쉬", "vol": 16000}]}), encoding="utf-8")
        T.SOCIAL.write_text("{깨짐", encoding="utf-8")
        self.assertIn("닛몰캐쉬", T.hot())   # 커뮤니티 파일이 깨져도 1.5만 선은 그대로 산다

