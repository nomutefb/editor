# [단독] 한 매체 긴급 푸시 — main() 종단(평의회4-7 260924: 술어 단위 테스트만으로는 발송 경로에서 빠져도 못 잡는다)
#   네트워크 0 · pywebpush·VAPID·AI 사건중복 스텁 · 원장·후보는 임시 폴더
import datetime as dt, importlib.util, json, os, sys, tempfile, types, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KST = dt.timezone(dt.timedelta(hours=9))
SENT = []


def _iso(h):
    return (dt.datetime.now(KST) - dt.timedelta(hours=h)).strftime("%Y-%m-%dT%H:%M:%S%z")


def _cand(title, breaking=True, grade=2, cross=1, pub_h=0.3):
    u = "https://news.jtbc.co.kr/article/NB1"
    return {"id": u, "url": u, "event_key": u, "title": title, "media": "JTBC", "cat": "사회", "cross": cross, "solo": 1,
            "published": _iso(pub_h), "first_seen": _iso(0.2), "breaking": breaking, "grade": grade,
            "cluster_members": [u], "breaking_pick": {"url": u, "media": "JTBC", "title": title}}


class ExclusiveBreakingPushTest(unittest.TestCase):
    def run_main(self, cands, env=None):
        fake = types.ModuleType("pywebpush")
        class WebPushException(Exception):
            pass
        fake.WebPushException = WebPushException
        fake.webpush = lambda subscription_info, data, **kw: SENT.append(json.loads(data))
        sys.modules["pywebpush"] = fake
        SENT.clear()
        env = {"VAPID_PRIVATE_KEY": "x", **(env or {})}
        old = {k: os.environ.get(k) for k in env}
        os.environ.update(env)
        argv, sys.argv = sys.argv, ["push_send.py"]
        try:
            spec = importlib.util.spec_from_file_location("ps_main", ROOT / ".github" / "scripts" / "push_send.py")
            m = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(m)
            with tempfile.TemporaryDirectory() as d:
                d = Path(d)
                m.SUBS, m.SENT, m.CAND, m.SENT_EV = d / "subs.json", d / "sent.json", d / "cands.json", d / "ev.json"
                m.SUBS.write_text(json.dumps([{"endpoint": "https://push.example/1", "keys": {}}]))
                m.CAND.write_text(json.dumps(cands, ensure_ascii=False))
                m.vapid_pem = lambda k: "/dev/null"
                m._ai_same_event = lambda t, pool: None
                m.main()
        finally:
            sys.argv = argv
            for k, v in old.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
        return list(SENT)

    def test_single_outlet_exclusive_breaking_pushes_with_pick(self):
        out = self.run_main([_cand("[단독] '소주병 집어든' 승리, 말리는 일행…당시 CCTV 입수")])
        self.assertEqual(len(out), 1)
        self.assertTrue(out[0]["body"].startswith("(긴급)"))
        self.assertEqual(out[0]["actions"], [{"action": "pick", "title": "PICK"}])

    def test_lever_off_keeps_old_cross_gate(self):
        self.assertEqual(self.run_main([_cand("[단독] 승리 CCTV 입수")], env={"PUSH_SOLO_EXC": "0"}), [])

    def test_exclusive_not_breaking_does_not_push(self):
        self.assertEqual(self.run_main([_cand("[단독] 승리 CCTV 입수", breaking=False, grade=3)]), [])   # 별도 「(단독)」 축 없음(긴급 판정이 문턱)

    def test_untagged_single_outlet_still_waits(self):
        self.assertEqual(self.run_main([_cand("승리 CCTV 입수")]), [])

    def test_stale_publish_blocked(self):
        self.assertEqual(self.run_main([_cand("[단독] 승리 CCTV 입수", pub_h=20)]), [])   # 재수집 뒷북 = 긴급 축 발행 창(PUSH_PUB_MAX_H)


if __name__ == "__main__":
    unittest.main()
