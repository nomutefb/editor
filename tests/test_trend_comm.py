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
        self._orig = (T.SNS, T.SOCIAL, T.MIN_VOL, T.COMM_MIN_VOL, T.SOCIAL_FETCH)
        T.SNS, T.SOCIAL, T.MIN_VOL, T.COMM_MIN_VOL = self.d / "s.json", self.d / "c.json", 15000, 10000
        T.SOCIAL_FETCH = False   # CI(GITHUB_ACTIONS)에서도 원격 최신본이 아니라 이 테스트 파일을 읽게

    def tearDown(self):
        T.SNS, T.SOCIAL, T.MIN_VOL, T.COMM_MIN_VOL, T.SOCIAL_FETCH = self._orig

    def run_hot(self, gt, social):
        T.SNS.write_text(json.dumps({"gtrends": gt}, ensure_ascii=False), encoding="utf-8")
        T.SOCIAL.write_text(json.dumps(social, ensure_ascii=False), encoding="utf-8")
        return T.hot()

    def test_comm_match_lowers_line(self):
        out = self.run_hot([{"query": "닛몰캐쉬", "vol": 10000}], [{"title": "현재 난리난 닛몰캐쉬 전여친 폭로 ㄷㄷ.JPG"}])
        self.assertIn("닛몰캐쉬", out)
        self.assertIn("커뮤니티", out["닛몰캐쉬"][3])

    def test_no_comm_keeps_15k(self):
        self.assertEqual(self.run_hot([{"query": "닛몰캐쉬", "vol": 10000}], [{"title": "다른 글"}]), {})

    def test_below_comm_line(self):
        self.assertEqual(self.run_hot([{"query": "닛몰캐쉬", "vol": 5000}], [{"title": "닛몰캐쉬 폭로"}]), {})

    def test_short_word_needs_token(self):   # 짧은 말은 낱말·조사 꼬리 일치만(kw_hit) — substring 오탐 차단
        self.assertEqual(self.run_hot([{"query": "로제", "vol": 10000}], [{"title": "새 프로젝트 공개"}]), {})

    def test_broken_social_file_is_soft(self):
        T.SNS.write_text(json.dumps({"gtrends": [{"query": "닛몰캐쉬", "vol": 16000}]}), encoding="utf-8")
        T.SOCIAL.write_text("{깨짐", encoding="utf-8")
        self.assertIn("닛몰캐쉬", T.hot())   # 커뮤니티 파일이 깨져도 1.5만 선은 그대로 산다

