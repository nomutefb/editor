"""경중 채점(.github/scripts/gate_judge.py) 재채점 사다리 회귀 — 룰북 개정 재채점 직후 사다리가 같은 제목을 한 번 더
부르던 중복(260925 후보 스냅샷 계산 = 391건 중 176건)을 막고, 첫 채점과 이후 cross 성장 시 사다리는 종전대로 도는지 고정한다.
judge 는 가짜로 바꿔 끼운다(LLM 0)."""
import importlib.util
import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

_P = Path(__file__).resolve().parents[1] / ".github" / "scripts" / "gate_judge.py"


def _load():
    spec = importlib.util.spec_from_file_location("gate_judge_ladder_test", _P)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


G = _load()
_NOW = (datetime.now(timezone(timedelta(hours=9))) - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S%z")


def _cand(i, cross, **kw):
    c = {"id": f"https://example.com/{i}", "url": f"https://example.com/{i}", "title": f"사건 제목 {i}",
         "cat": "사회", "cross": cross, "first_seen": _NOW}
    c.update(kw)
    return c


class RegradeLadder(unittest.TestCase):
    def _run(self, cands):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "candidates.json"
            p.write_text(json.dumps(cands, ensure_ascii=False), encoding="utf-8")
            old = (G.CAND, G.judge, G._write)
            G.CAND = p
            G.judge = lambda items: ({k: 2 for k, _ in items}, {k: "사회" for k, _ in items}, {}, 0, "")
            G._write = lambda cs: p.write_text(json.dumps(cs, ensure_ascii=False), encoding="utf-8")
            try:
                G.main()
            finally:
                G.CAND, G.judge, G._write = old
            return {c["id"]: c for c in json.loads(p.read_text(encoding="utf-8"))}

    def test_rubric_rejudge_consumes_ladder(self):
        old = {"grade": 1, "grade_rubric": "oldrubric", "regraded": "oldrubric", "regraded_mid": "oldrubric"}
        out = self._run([_cand("full", 9, **old), _cand("mid", 7, **old), _cand("low", 4, **old)])
        full, mid, low = out["https://example.com/full"], out["https://example.com/mid"], out["https://example.com/low"]
        for c in (full, mid, low):
            self.assertEqual(c["grade_rubric"], G.RUBRIC_VER)
        self.assertEqual((full.get("regraded"), full.get("regraded_mid")), (G.RUBRIC_VER, G.RUBRIC_VER))
        self.assertFalse(G.regrade_due(full))          # 막 새 rubric 으로 매긴 cross 9 = 사다리 재콜 없음
        self.assertEqual(mid.get("regraded_mid"), G.RUBRIC_VER)
        self.assertNotEqual(mid.get("regraded"), G.RUBRIC_VER)
        self.assertFalse(G.regrade_due(mid))
        mid["cross"] = 9
        self.assertTrue(G.regrade_due(mid))            # 이후 8+ 로 자라면 사다리는 종전대로 1회
        self.assertNotEqual(low.get("regraded_mid"), G.RUBRIC_VER)
        low["cross"] = 6
        self.assertTrue(G.regrade_due(low))            # 사다리 단 밑에서 재채점된 건은 자라면 종전대로

    def test_first_grading_keeps_ladder(self):
        out = self._run([_cand("new", 9)])
        c = out["https://example.com/new"]
        self.assertEqual(c["grade"], 2)
        self.assertNotEqual(c.get("regraded"), G.RUBRIC_VER)
        self.assertTrue(G.regrade_due(c))              # 첫 채점은 무접촉 = 다음 런 사다리 1회(기존 동작)


if __name__ == "__main__":
    unittest.main()
