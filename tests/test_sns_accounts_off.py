"""구독 끄기(숨김) 플래그 — viewer/sns_accounts.json `<plat>.off=true` 는 목록을 보존한 채 0계정으로 취급된다.
수집·정체(stale)·커버 알림·화면 섹션이 전부 `acc[plat]` 빈 목록 게이트를 타므로, 로더 한 곳만 검증하면 축이 닫힌다."""
import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scraper"))
import sns_trends as st  # noqa: E402


class SnsAccountsOff(unittest.TestCase):
    def _load(self, data):
        fd, p = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f)
        old = st.ACC
        st.ACC = p
        try:
            return st._load_accounts()
        finally:
            st.ACC = old
            os.unlink(p)

    def test_off_platform_yields_no_accounts_but_keeps_others(self):
        acc, reg = self._load({"insta": {"kr": ["a1", "b2"], "gl": ["c3"], "off": True},
                               "x": {"kr": ["x1"], "gl": []}})
        self.assertEqual(acc["insta"], [])
        self.assertEqual(reg["insta"], {})
        self.assertEqual(acc["x"], ["x1"])
        self.assertEqual(st.SUB_OFF, {"insta"})

    def test_off_false_or_missing_is_normal(self):
        acc, _ = self._load({"insta": {"kr": ["a1"], "gl": [], "off": False}, "x": {"kr": ["x1"], "gl": []}})
        self.assertEqual(acc["insta"], ["a1"])
        self.assertEqual(st.SUB_OFF, set())

    def test_off_resets_between_loads(self):
        self._load({"insta": {"kr": ["a1"], "gl": [], "off": True}})
        self.assertEqual(st.SUB_OFF, {"insta"})
        self._load({"insta": {"kr": ["a1"], "gl": []}})
        self.assertEqual(st.SUB_OFF, set())

    def test_live_registry_insta_is_off(self):
        acc, _ = st._load_accounts()
        self.assertEqual(acc["insta"], [], "운영자 260913 지시 = 인스타 구독 숨김")
        raw = json.load(open(st.ACC, encoding="utf-8"))
        self.assertTrue(raw["insta"]["kr"], "목록은 삭제가 아니라 보존")


if __name__ == "__main__":
    unittest.main()
