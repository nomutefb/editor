# 속보 1보 단독 입장 회귀 — 교차 2매체 게이트가 [속보] 태그 판별보다 먼저 걸려 1보가 두 번째 매체까지 안 뜨던 지연(260923)
import importlib.util, json, os, re, sys, tempfile, unittest
from unittest import mock
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TC = ROOT / "scraper" / "to_candidates.py"
PS = ROOT / ".github" / "scripts" / "push_send.py"
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
        solo = {"id": "u1", "url": "u1", "title": "[속보] 1보", "cross": 1, "solo": 1, "published": _iso(0.5),
                "first_seen": first, "event_key": "u1", "breaking_rubric": "x", "group_id": "g1",
                "cluster_members": ["u1"], "arts": 1}
        out = self.run_tc([art("u0", "총격 11명 사망", cross=2, pub_h=0.6, members=["u0", "u1"], media="조선일보")], [solo])
        self.assertNotIn("u1", out)
        self.assertEqual(out["u0"]["first_seen"], first)
        self.assertEqual(out["u0"]["event_key"], "u1")        # 푸시 dedup 키 승계 = 같은 사건 재발송 차단
        self.assertNotIn("breaking_rubric", out["u0"])        # 새 제목으로 재판정
        self.assertNotIn("group_id", out["u0"])               # 단독의 묶기 도장은 안 물려줌
        self.assertNotIn("solo", out["u0"])                   # 다매체가 되면 표식 해제

    def test_absorbed_into_existing_cluster_is_removed(self):
        solo = {"id": "u1", "url": "u1", "title": "[속보] 1보", "cross": 1, "solo": 1, "published": _iso(0.5),
                "first_seen": _kst(0.4), "cluster_members": ["u1"], "arts": 1}
        old = {"id": "u0", "url": "u0", "title": "총격", "cross": 2, "published": _iso(0.6),
               "first_seen": _kst(0.5), "cluster_members": ["u0", "u9"], "arts": 2}
        out = self.run_tc([art("u0", "총격 11명 사망", cross=3, pub_h=0.6, members=["u0", "u1", "u9"])], [solo, old])
        self.assertEqual(set(out), {"u0"})

    def test_unconfirmed_solo_expires_but_confirmed_breaking_stays(self):
        base = {"cross": 1, "solo": 1, "published": _iso(7), "first_seen": _kst(7), "cluster_members": ["x"], "arts": 1}
        out = self.run_tc([], [{**base, "id": "a", "url": "a", "title": "[속보] a"},
                               {**base, "id": "b", "url": "b", "title": "[속보] b", "breaking": True}])
        self.assertEqual(set(out), {"b"})

    def test_graded_solo_kept_until_badge_window_then_expires(self):
        # 평의회4 #1: 채점된 단독을 6h 에 지우면 피드 빌드가 제목만 보고 ⚡이슈를 거꾸로 켠다 → 24h 보존
        # 평의회4 #2: 긴급 도장이 있어도 경중 0·1 이면 긴급 아님(뷰어 isBreaking) → 영구 보존 대상 아님
        def e(u, h, **kw):
            return {"id": u, "url": u, "title": "[속보] " + u, "cross": 1, "solo": 1, "published": _iso(h),
                    "first_seen": _kst(h), "cluster_members": [u], "arts": 1, **kw}
        out = self.run_tc([], [e("g7", 7, grade=1), e("g25", 25, grade=1), e("b1", 25, breaking=True, grade=1),
                               e("b3", 25, breaking=True, grade=3)])
        self.assertEqual(set(out), {"g7", "b3"})

    def test_rollback_lever(self):
        existing = [{"id": "a", "url": "a", "title": "[속보] a", "cross": 1, "solo": 1, "published": _iso(0.5),
                     "first_seen": _kst(0.4), "cluster_members": ["a"], "arts": 1}]
        out = self.run_tc([art("u1", "[속보] 새 1보")], existing, env={"CAND_SOLO_TAG": "0"})
        self.assertEqual(out, {})

    def test_solo_flag_set_on_admission(self):
        self.assertEqual(self.run_tc([art("u1", "[속보] 1보")])["u1"].get("solo"), 1)

    def test_member_of_existing_multi_outlet_card_is_not_readmitted_as_solo(self):
        # 평의회1 #1: 대표 기사(x)가 RSS 창에서 빠진 회차 = 남은 멤버 a 가 [속보] 단독으로 떠도 기존 다매체 후보 X 를 흡수·폐기하면 안 된다
        x = {"id": "x", "url": "x", "title": "총격", "cross": 2, "published": _iso(0.5), "first_seen": _kst(0.4),
             "last_report": _kst(0.4), "cluster_members": ["a", "b", "x"], "arts": 3}
        out = self.run_tc([art("a", "[속보] 총격 11명 사망", members=["a", "b"])], [x])
        self.assertEqual(set(out), {"x"})
        self.assertEqual(out["x"]["cross"], 2)

    def test_confirmed_breaking_solo_is_not_swept_into_existing_cluster(self):
        # 평의회1 #2·평의회2 #1: 이미 🚨(푸시 나갔을 수 있음)인 단독은 회수 안 함
        solo = {"id": "u1", "url": "u1", "title": "[속보] 1보", "cross": 1, "solo": 1, "published": _iso(0.5),
                "first_seen": _kst(0.4), "cluster_members": ["u1"], "arts": 1, "breaking": True, "grade": 3}
        old = {"id": "u0", "url": "u0", "title": "총격", "cross": 2, "published": _iso(0.6),
               "first_seen": _kst(0.5), "cluster_members": ["u0", "u9"], "arts": 2}
        out = self.run_tc([art("u0", "총격 11명 사망", cross=3, pub_h=0.6, members=["u0", "u1", "u9"])], [solo, old])
        self.assertEqual(set(out), {"u0", "u1"})
        self.assertTrue(out["u1"]["breaking"])

    def test_earliest_solo_is_inherited(self):
        a = {"id": "a", "url": "a", "title": "[속보] a", "cross": 1, "solo": 1, "published": _iso(0.5),
             "first_seen": _kst(0.3), "event_key": "a", "cluster_members": ["a"], "arts": 1}
        z = {"id": "z", "url": "z", "title": "[속보] z", "cross": 1, "solo": 1, "published": _iso(0.6),
             "first_seen": _kst(0.5), "event_key": "z", "cluster_members": ["z"], "arts": 1}
        out = self.run_tc([art("m", "총격", cross=3, pub_h=0.7, members=["a", "m", "z"])], [a, z])
        self.assertEqual(out["m"]["event_key"], "z")

    def test_solo_protected_seats_are_capped(self):
        # 평의회6: CAP 상시 포화 → 1군 단독 = 2군 1건 밀어냄. 좌석 상한 넘는 단독은 꼬리로 가서 먼저 잘린다
        old = [{"id": f"o{i}", "url": f"o{i}", "title": f"기사{i}", "cross": 2, "published": _iso(20), "first_seen": _kst(20),
                "last_report": _kst(1), "cluster_members": [f"o{i}", f"p{i}"], "arts": 2} for i in range(3)]
        solos = [art(f"s{i}", f"[속보] 서로 다른 사건 {i}호 발생", pub_h=0.1 * (i + 1)) for i in range(3)]
        out = self.run_tc(solos, old, env={"CAND_SOLO_T1_MAX": "1", "CAND_CAP": "4"})
        self.assertEqual(sum(1 for u in out if u.startswith("s")), 1)   # 1석만 보호 · 나머지 단독은 컷
        self.assertEqual(sum(1 for u in out if u.startswith("o")), 3)   # 다매체 후보는 안 밀려남

    def test_far_future_publish_not_admitted(self):
        self.assertEqual(self.run_tc([art("u1", "[속보] 쓰레기 시각", pub_h=-48)]), {})

    def test_rollback_does_not_touch_multi_outlet_entries(self):
        # 평의회1 #6: 레버 OFF 가 단독 표식 없는 다매체 엔트리를 지우면 안 된다
        o = {"id": "o", "url": "o", "title": "기사", "cross": 2, "published": _iso(7), "first_seen": _kst(7),
             "last_report": _kst(1), "cluster_members": ["o", "p"], "arts": 2}
        self.assertEqual(set(self.run_tc([], [o], env={"CAND_SOLO_TAG": "0", "CAND_MIN_CROSS": "3"})), {"o"})

    def test_multi_outlet_entry_does_not_regress_to_one(self):
        old = {"id": "u1", "url": "u1", "title": "[속보] a", "cross": 2, "published": _iso(0.5),
               "first_seen": _kst(0.4), "cluster_members": ["u1", "u2"], "arts": 2}
        out = self.run_tc([art("u1", "[속보] a", cross=1)], [old])
        self.assertEqual(out["u1"]["cross"], 2)


class PushSoloTest(unittest.TestCase):
    @mock.patch.dict(os.environ, {}, clear=False)
    def test_push_cross_gate(self):
        os.environ.pop("PUSH_SOLO_TAG", None)
        m = _load(PS, "ps_mod")
        self.assertTrue(m.push_cross_ok({"cross": 2, "title": "총격"}))
        self.assertTrue(m.push_cross_ok({"cross": 1, "title": "[속보] 총격"}))
        self.assertFalse(m.push_cross_ok({"cross": 1, "title": "총격"}))
        self.assertFalse(m.push_cross_ok({"cross": 0, "title": "[속보] 총격"}))

    def test_sangbo_is_not_a_first_report_for_push(self):
        m = _load(PS, "ps_mod3")
        self.assertFalse(m.push_cross_ok({"cross": 1, "title": "[상보] 총격 사망자 늘어"}))
        self.assertTrue(m.push_cross_ok({"cross": 1, "title": "삼척 계곡서 2명 실종(1보)"}))

    def test_push_send_imports_without_scraper_dir(self):
        # 평의회3 blocker: 완료 알림 12레인은 scraper/ 없는 희소 체크아웃 — 모듈 로드가 깨지면 알림이 조용히 사라진다
        import shutil, subprocess
        with tempfile.TemporaryDirectory() as d:
            dst = Path(d) / ".github" / "scripts"
            dst.mkdir(parents=True)
            shutil.copy(PS, dst / "push_send.py")
            code = ("import importlib.util as u; s=u.spec_from_file_location('p', %r); m=u.module_from_spec(s); "
                    "s.loader.exec_module(m); print(m.push_cross_ok({'cross': 1, 'title': '[속보] x'}))") % str(dst / "push_send.py")
            r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=d)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(r.stdout.strip(), "False")   # 태그 정본 못 읽음 = 종전 규칙(다매체만)

    @mock.patch.dict(os.environ, {"PUSH_SOLO_TAG": "0"})
    def test_push_rollback_lever(self):
        self.assertFalse(_load(PS, "ps_mod2").push_cross_ok({"cross": 1, "title": "[속보] 총격"}))


if __name__ == "__main__":
    unittest.main()
