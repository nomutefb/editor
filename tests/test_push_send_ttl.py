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



class PickActionTest(unittest.TestCase):
    """알림 PICK 버튼(운영자 260924) — 긴급·이슈 딥링크에만 싣고, 목적지는 SW가 만든다(주소 중복 0)."""

    def test_breaking_and_issue_carry_pick_button(self):
        import json
        m = _load()
        c = {"event_key": "https://x.kr/1", "url": "https://x.kr/1", "breaking_pick": {"url": "https://y.kr/2"}}
        for kind in ("brk", "iss"):
            d = json.loads(m.payload_of({"title": "News", "body": "b", "url": m.brk_url(c), "kind": kind}))
            self.assertEqual(d["actions"], [{"action": "pick", "title": "PICK"}])
            self.assertTrue(d["url"].startswith("https://edit.nomute.kr/?brk="))
        for msg in ({"title": "t", "body": "b", "url": "/thumb.html#done", "kind": "make"},
                    {"title": "t", "body": "b", "url": "/", "kind": "brk"}):   # 제작완료 · 딥링크 없는 긴급(키 결측) = 버튼 없음
            self.assertNotIn("actions", json.loads(m.payload_of(msg)))



class TrendPickTest(unittest.TestCase):
    """급상승 알림 관련 뉴스 PICK(운영자 260924 ⑦) — 본문 목적지(구글)는 그대로 · PICK 딥링크는 따로 · 절대 주소."""

    def test_notify_with_pick_url(self):
        import json
        m = _load()
        d = json.loads(m.payload_of({"title": "📈 급상승", "body": "b", "url": "https://www.google.com/search?q=x", "kind": "trend",
                                     "pick_url": "/?brk=https%3A%2F%2Fx.kr%2F1"}))
        self.assertEqual(d["url"], "https://www.google.com/search?q=x")
        self.assertTrue(d["pick"].startswith("https://edit.nomute.kr/?brk="))
        self.assertEqual(d["actions"], [{"action": "pick", "title": "PICK"}])
        self.assertNotIn("actions", json.loads(m.payload_of({"title": "t", "body": "b", "url": "https://g/x", "kind": "trend"})))


class ExclusiveCrossGateTest(unittest.TestCase):
    """[단독] = 긴급 축 한 매체 예외(운영자 260924 · 평의회4) — 문턱은 긴급 축 그대로, 매체 수 예외만 추가."""

    def test_exclusive_tag_passes_cross_gate(self):
        m = _load()
        self.assertTrue(m.push_cross_ok({"title": "[단독] 승리 CCTV 입수", "cross": 1}))
        self.assertTrue(m.push_cross_ok({"title": "승리 CCTV", "cross": 1, "breaking_pick": {"title": "[단독] 승리 CCTV"}}))
        self.assertFalse(m.push_cross_ok({"title": "승리 CCTV 입수", "cross": 1}))
        self.assertFalse(m.push_cross_ok({"title": "[상보] 승리 CCTV", "cross": 1}))

    def test_lever_off(self):
        os.environ["PUSH_SOLO_EXC"] = "0"
        try:
            self.assertFalse(_load().push_cross_ok({"title": "[단독] 승리 CCTV 입수", "cross": 1}))
        finally:
            os.environ.pop("PUSH_SOLO_EXC", None)


if __name__ == "__main__":
    unittest.main()
