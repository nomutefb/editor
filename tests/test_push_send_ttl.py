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



class ExclusivePushTest(unittest.TestCase):
    """[단독] 대형 알림(운영자 260924 «승리 CCTV 같은 건 항상 먼저 알림») — 경중 3 · 매체 수 무관 · 긴급 축과 2중 발송 0."""

    def test_predicate(self):
        m = _load()
        base = {"title": "[단독] '소주병 집어든' 승리…당시 CCTV 입수", "cross": 1, "grade": 3}
        self.assertTrue(m.is_exclusive(base))
        self.assertFalse(m.is_exclusive({**base, "grade": 2}))                        # 경중 3 미만 = 화면만
        self.assertFalse(m.is_exclusive({**base, "grade": None}))                     # 미채점 = 보류(비가역 보수)
        self.assertFalse(m.is_exclusive({**base, "title": "승리 CCTV 입수"}))          # 태그 없음
        self.assertFalse(m.is_exclusive({**base, "breaking": True, "cross": 3}))      # 긴급 축이 부를 건 = 제외
        self.assertTrue(m.is_exclusive({**base, "breaking": True, "cross": 1}))       # 한 매체 긴급 [단독] = 긴급 축 cross 문턱에 막히므로 여기서
        self.assertTrue(m.is_exclusive({**base, "title": "승리 CCTV", "breaking_pick": {"title": "[단독] 승리 CCTV"}}))

    def test_kill_switch(self):
        os.environ["EXC_PUSH"] = "0"
        try:
            self.assertFalse(_load().is_exclusive({"title": "[단독] x", "cross": 1, "grade": 3}))
        finally:
            os.environ.pop("EXC_PUSH", None)


if __name__ == "__main__":
    unittest.main()
