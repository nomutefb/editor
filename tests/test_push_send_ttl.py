# 웹푸시 발송 옵션 회귀 — ttl=0(지금 아니면 버림) 재발 차단 + 긴급도 헤더 (260921 강훈식 사의 무착 사고)
import importlib.util, os, re, sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / ".github" / "scripts" / "push_send.py"


def _load():
    spec = importlib.util.spec_from_file_location("push_send_mod", SRC)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class PushOptsTest(unittest.TestCase):
    def test_default_ttl_is_breaking_window_not_zero(self):
        os.environ.pop("PUSH_TTL_S", None)
        m = _load()
        self.assertEqual(m.PUSH_TTL_S, m.FAST_MAX_H * 3600)
        self.assertGreater(m.push_opts("brk")["ttl"], 0)

    def test_urgency_by_kind(self):
        m = _load()
        self.assertEqual(m.push_opts("brk")["headers"]["Urgency"], "high")
        self.assertEqual(m.push_opts("iss")["headers"]["Urgency"], "high")
        self.assertEqual(m.push_opts(None)["headers"]["Urgency"], "high")   # 종류 미지정 = 구 경로 = 긴급 취급
        self.assertEqual(m.push_opts("make")["headers"]["Urgency"], "normal")
        self.assertEqual(m.push_opts("test")["headers"]["Urgency"], "normal")

    def test_env_override(self):
        os.environ["PUSH_TTL_S"] = "0"
        try:
            self.assertEqual(_load().PUSH_TTL_S, 0)
        finally:
            os.environ.pop("PUSH_TTL_S", None)

    def test_send_call_uses_push_opts(self):
        src = SRC.read_text(encoding="utf-8")
        calls = re.findall(r"webpush\(subscription_info=.*", src)
        self.assertEqual(len(calls), 1)
        self.assertIn("**push_opts(", calls[0])


if __name__ == "__main__":
    unittest.main()
