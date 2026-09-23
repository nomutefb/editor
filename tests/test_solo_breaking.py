# 속보 1보 단독 입장 회귀 — 교차 2매체 게이트가 [속보] 태그 판별보다 먼저 걸려 1보가 두 번째 매체까지 안 뜨던 지연(260923)
import importlib.util, json, os, re, sys, tempfile, unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TC = ROOT / "scraper" / "to_candidates.py"
PS = ROOT / ".github" / "scripts" / "push_send.py"
VIEW = ROOT / "viewer-src" / "35-applyAutoGroups.part"
KST = timezone(timedelta(hours=9))
sys.path.insert(0, str(ROOT / "scraper"))


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _iso(h_ago):
    return (datetime.now(timezone.utc) - timedelta(hours=h_ago)).isoformat()


def _kst(h_ago):
    return (datetime.now(KST) - timedelta(hours=h_ago)).strftime("%Y-%m-%dT%H:%M:%S%z")


def art(url, title, cross=1, pub_h=0.2, members=None, media="연합뉴스"):
    members = members or [url]
    return {"link": url, "title": title, "publisher": media, "category": "society", "published": _iso(pub_h),
            "is_cluster_rep": True, "cross_score": cross, "burst": cross, "cluster_size": len(members),
            "cluster_members": sorted(members), "breaking_pick": {"url": url, "media": media, "title": title}}


class ToCandidatesSoloTest(unittest.TestCase):
    def run_tc(self, arts, existing=None, env=None):
        env = env or {}
        old = {k: os.environ.get(k) for k in env}
        os.environ.update(env)
        try:
            m = _load(TC, "tc_mod")
        finally:
            for k, v in old.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
        with tempfile.TemporaryDirectory() as d:
            m.SRC = Path(d) / "articles.json"
            m.DST = Path(d) / "candidates.json"
            m.SRC.write_text(json.dumps(arts, ensure_ascii=False), encoding="utf-8")
            m.DST.write_text(json.dumps(existing or [], ensure_ascii=False), encoding="utf-8")
            m.main()
            return {c["url"]: c for c in json.loads(m.DST.read_text(encoding="utf-8"))}

    def test_tagged_single_outlet_enters_as_breaking_candidate(self):
        out = self.run_tc([art("u1", "[속보] 남아공 더반서 총격…11명 사망")])
        self.assertIn("u1", out)
        self.assertEqual(out["u1"]["cross"], 1)
        self.assertTrue(out["u1"]["breaking_candidate"])

    def test_newsis_suffix_1bo_counts_as_tag(self):
        self.assertIn("u1", self.run_tc([art("u1", "삼척 계곡서 2명 실종…구조대 출동(1보)")]))

    def test_untagged_single_outlet_still_waits(self):
        self.assertEqual(self.run_tc([art("u1", "남아공 더반서 총격…11명 사망")]), {})

    def test_stale_tagged_single_outlet_not_admitted(self):
        self.assertEqual(self.run_tc([art("u1", "[속보] 옛 사건", pub_h=8)]), {})

    def test_future_skewed_publish_uses_first_seen(self):
        out = self.run_tc([art("u1", "[속보] 프레시안 시각 오기록", pub_h=-9)])
        self.assertIn("u1", out)

    def test_absorbed_into_new_cluster_inherits_history(self):
        first = _kst(0.4)
        solo = {"id": "u1", "url": "u1", "title": "[속보] 1보", "cross": 1, "published": _iso(0.5),
                "first_seen": first, "event_key": "u1", "breaking": True, "breaking_rubric": "x",
                "cluster_members": ["u1"], "arts": 1}
        out = self.run_tc([art("u0", "총격 11명 사망", cross=2, pub_h=0.6, members=["u0", "u1"], media="조선일보")], [solo])
        self.assertNotIn("u1", out)
        self.assertEqual(out["u0"]["first_seen"], first)
        self.assertEqual(out["u0"]["event_key"], "u1")        # 푸시 dedup 키 승계 = 같은 사건 재발송 차단
        self.assertNotIn("breaking_rubric", out["u0"])        # 새 제목으로 재판정

    def test_absorbed_into_existing_cluster_is_removed(self):
        solo = {"id": "u1", "url": "u1", "title": "[속보] 1보", "cross": 1, "published": _iso(0.5),
                "first_seen": _kst(0.4), "cluster_members": ["u1"], "arts": 1}
        old = {"id": "u0", "url": "u0", "title": "총격", "cross": 2, "published": _iso(0.6),
               "first_seen": _kst(0.5), "cluster_members": ["u0", "u9"], "arts": 2}
        out = self.run_tc([art("u0", "총격 11명 사망", cross=3, pub_h=0.6, members=["u0", "u1", "u9"])], [solo, old])
        self.assertEqual(set(out), {"u0"})

    def test_unconfirmed_solo_expires_but_confirmed_breaking_stays(self):
        base = {"cross": 1, "published": _iso(7), "first_seen": _kst(7), "cluster_members": ["x"], "arts": 1}
        out = self.run_tc([], [{**base, "id": "a", "url": "a", "title": "[속보] a"},
                               {**base, "id": "b", "url": "b", "title": "[속보] b", "breaking": True}])
        self.assertEqual(set(out), {"b"})

    def test_rollback_lever(self):
        existing = [{"id": "a", "url": "a", "title": "[속보] a", "cross": 1, "published": _iso(0.5),
                     "first_seen": _kst(0.4), "cluster_members": ["a"], "arts": 1}]
        out = self.run_tc([art("u1", "[속보] 새 1보")], existing, env={"CAND_SOLO_TAG": "0"})
        self.assertEqual(out, {})

    def test_multi_outlet_entry_does_not_regress_to_one(self):
        old = {"id": "u1", "url": "u1", "title": "[속보] a", "cross": 2, "published": _iso(0.5),
               "first_seen": _kst(0.4), "cluster_members": ["u1", "u2"], "arts": 2}
        out = self.run_tc([art("u1", "[속보] a", cross=1)], [old])
        self.assertEqual(out["u1"]["cross"], 2)


class PushSoloTest(unittest.TestCase):
    def test_push_cross_gate(self):
        os.environ.pop("PUSH_SOLO_TAG", None)
        m = _load(PS, "ps_mod")
        self.assertTrue(m.push_cross_ok({"cross": 2, "title": "총격"}))
        self.assertTrue(m.push_cross_ok({"cross": 1, "title": "[속보] 총격"}))
        self.assertFalse(m.push_cross_ok({"cross": 1, "title": "총격"}))
        self.assertFalse(m.push_cross_ok({"cross": 0, "title": "[속보] 총격"}))

    def test_push_rollback_lever(self):
        os.environ["PUSH_SOLO_TAG"] = "0"
        try:
            self.assertFalse(_load(PS, "ps_mod2").push_cross_ok({"cross": 1, "title": "[속보] 총격"}))
        finally:
            os.environ.pop("PUSH_SOLO_TAG", None)


class TagParityTest(unittest.TestCase):
    def test_viewer_regex_matches_python_ssot(self):
        from brk_tag import BREAKING_TAG
        m = re.search(r"const BRK_TAG_RE = /(.+?)/;", VIEW.read_text(encoding="utf-8"))
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), BREAKING_TAG.pattern)


if __name__ == "__main__":
    unittest.main()
