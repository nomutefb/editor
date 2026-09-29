# 나무위키 실시간 검색 순위(sns_trends.namu_rank · 폰 전용) — 응답 형식 두 갈래 수용 · 실패 = [] · 네트워크 0
import importlib.util, unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("sns_trends_n", ROOT / "scraper" / "sns_trends.py")
S = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(S)


class _R:
    def __init__(self, b):
        self.b = b

    def read(self):
        return self.b


class NamuRank(unittest.TestCase):
    def run_with(self, body):
        with patch.object(S.urllib.request, "urlopen", lambda *a, **k: _R(body)):
            return S.namu_rank()

    def test_string_list(self):
        self.assertEqual(self.run_with('["닛몰캐쉬", "황정민"]'.encode()), [{"query": "닛몰캐쉬", "rank": 1}, {"query": "황정민", "rank": 2}])

    def test_object_list(self):
        self.assertEqual(self.run_with('[{"keyword": "닛몰캐쉬"}]'.encode()), [{"query": "닛몰캐쉬", "rank": 1}])

    def test_failure_is_empty(self):
        def boom(*a, **k):
            raise OSError("403")
        with patch.object(S.urllib.request, "urlopen", boom):
            self.assertEqual(S.namu_rank(), [])
