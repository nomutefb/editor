"""File readers must close handles on success and malformed input."""
import contextlib
import gc
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import warnings

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "shared"))
sys.path.insert(0, str(ROOT / "scraper"))
import check_refs
import sns_trends


class ResourceLifecycle(unittest.TestCase):
    @contextlib.contextmanager
    def no_resource_warnings(self):
        with warnings.catch_warnings(record=True) as seen:
            warnings.simplefilter("always", ResourceWarning)
            yield
            gc.collect()
        self.assertEqual([str(w.message) for w in seen
                          if issubclass(w.category, ResourceWarning)], [])

    def test_trail_discovery_closes_files_including_decode_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            viewer = Path(folder) / "viewer"
            viewer.mkdir()
            (viewer / "rail.html").write_text('<div class="trail">한글</div>', encoding="utf-8")
            (viewer / "plain.html").write_text("plain", encoding="utf-8")
            (viewer / "broken.html").write_bytes(b"\xff")
            with patch.object(check_refs, "ROOT", folder), self.no_resource_warnings():
                self.assertEqual(check_refs._trail_surfaces(), ("viewer/rail.html",))

    def test_accounts_close_file_before_json_error_fallback(self):
        with tempfile.TemporaryDirectory() as folder:
            account_file = Path(folder) / "accounts.json"
            account_file.write_text('{"x":', encoding="utf-8")
            previous = set(sns_trends.SUB_OFF)
            try:
                with patch.object(sns_trends, "ACC", str(account_file)), \
                     contextlib.redirect_stderr(io.StringIO()), self.no_resource_warnings():
                    accounts, regions = sns_trends._load_accounts()
                    self.assertTrue(all(not v for v in accounts.values()))
                    self.assertTrue(all(not v for v in regions.values()))
            finally:
                sns_trends.SUB_OFF.clear()
                sns_trends.SUB_OFF.update(previous)


if __name__ == "__main__":
    unittest.main()
