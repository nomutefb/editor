# CAP 컷 순서 = 화면 노출 기준 4단(260923) — 포화 날 두 칼럼 어디에도 안 보이는 발행 4~6h 저cross 건을 누적 노출분보다 먼저 자른다.
import contextlib, importlib.util, io, json, os, sys, tempfile, unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TC = ROOT / "scraper" / "to_candidates.py"
KST = timezone(timedelta(hours=9))
sys.path.insert(0, str(ROOT / "scraper"))


def _load(env=None):
    env = env or {}
    old = {k: os.environ.get(k) for k in env}
    os.environ.update(env)
    try:
        spec = importlib.util.spec_from_file_location("tc_cap_tier", TC)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    finally:
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def _iso(h_ago):
    return (datetime.now(timezone.utc) - timedelta(hours=h_ago)).isoformat()


def _kst(h_ago):
    return (datetime.now(KST) - timedelta(hours=h_ago)).strftime("%Y-%m-%dT%H:%M:%S%z")


def ent(url, cross=2, pub_h=10.0, rc=1, **kw):
    e = {"id": url, "url": url, "title": f"사건 {url}", "cross": cross, "published": _iso(pub_h),
         "first_seen": _kst(pub_h), "last_report": _kst(0.3), "report_count": rc, "arts": cross,
         "cluster_members": [url], "event_key": url}
    e.update(kw)
    return e


class CapTierTest(unittest.TestCase):
    def run_tc(self, existing, env=None, patch=None):
        m = _load(env)
        if patch:
            patch(m)
        with tempfile.TemporaryDirectory() as d:
            m.SRC = Path(d) / "articles.json"
            m.DST = Path(d) / "candidates.json"
            m.SRC.write_text("[]", encoding="utf-8")
            m.DST.write_text(json.dumps(existing, ensure_ascii=False), encoding="utf-8")
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                m.main()
            out = json.loads(m.DST.read_text(encoding="utf-8"))
        return [c["url"] for c in out], buf.getvalue()

    def base(self):
        return [ent("fresh", cross=2, pub_h=1),            # 신규 칼럼(<4h)
                ent("mid", cross=5, pub_h=5),              # 발행 5h · cross<8 · rc 1 = 두 칼럼 어디에도 안 보임
                ent("cum", cross=9, pub_h=10)]             # 누적 칼럼(≥4h ∧ cross≥8)

    def test_invisible_4to6h_cut_before_cumulative(self):
        kept, log = self.run_tc(self.base(), env={"CAND_CAP": "2"})
        self.assertEqual(set(kept), {"fresh", "cum"})
        self.assertIn("비노출 4~6h 신선 컷 1건", log)
        self.assertNotIn("누적급", log)

    def test_rollback_lever_restores_old_order(self):
        kept, log = self.run_tc(self.base(), env={"CAND_CAP": "2", "CAND_CUT_VISIBLE": "0"})
        self.assertEqual(set(kept), {"fresh", "mid"})   # 종전 = 6h 신선 1군이 cross 9 를 밀어냄
        self.assertIn("⚠️ 누적급(cross≥8) 컷 1건", log)
        self.assertIn("⚠️ 누적 자격 컷 1건", log)       # 계기판은 레버와 무관하게 누적 자격 컷을 센다
        self.assertIn("컷 순서=종전 2군(레버 OFF)", log)

    def test_rollback_keeps_old_sort_key_order(self):
        # 레버 OFF = 종전 정렬 키(fresh_tier, cross, published) 그대로 — 출력 순서까지 같다
        pool = self.base() + [ent("x7", cross=7, pub_h=12), ent("fol", cross=4, pub_h=9, rc=6), ent("brk", cross=2, pub_h=30, breaking=True, grade=1)]
        kept, _ = self.run_tc(pool, env={"CAND_CUT_VISIBLE": "0"})
        self.assertEqual(kept, ["mid", "fresh", "brk", "cum", "x7", "fol"])
        kept, _ = self.run_tc(pool)
        self.assertEqual(kept, ["fresh", "brk", "cum", "fol", "mid", "x7"])   # 신규: 3단(신선·긴급) → 2단(누적 자격) → 1단(4~6h) → 0단

    def test_follow_enters_mirror_outranks_higher_cross_invisible(self):
        pool = [ent("fresh", pub_h=1), ent("fol", cross=4, pub_h=9, rc=6), ent("x7", cross=7, pub_h=9, rc=2)]
        kept, _ = self.run_tc(pool, env={"CAND_CAP": "2"})
        self.assertEqual(set(kept), {"fresh", "fol"})
        kept, _ = self.run_tc(pool, env={"CAND_CAP": "2", "CAND_CUT_VISIBLE": "0"})
        self.assertEqual(set(kept), {"fresh", "x7"})

    def test_merged_group_siblings_kept_together(self):
        # 화면은 같은 group_id 형제를 접고 cross 를 합산(5+3=8) → 누적 진입. 형제 하나만 잘려도 앵커가 칼럼에서 빠진다.
        pool = [ent("a", cross=5, pub_h=10, group_id="a"), ent("b", cross=3, pub_h=10, group_id="a"),
                ent("x7", cross=7, pub_h=10)]
        kept, _ = self.run_tc(pool, env={"CAND_CAP": "2"})
        self.assertEqual(set(kept), {"a", "b"})

    def test_fresh_under_4h_never_displaced_by_cumulative(self):
        pool = [ent(f"f{i}", cross=2, pub_h=0.5 + i) for i in range(3)] + [ent(f"c{i}", cross=12, pub_h=10) for i in range(3)]
        kept, _ = self.run_tc(pool, env={"CAND_CAP": "3"})
        self.assertEqual(set(kept), {"f0", "f1", "f2"})

    def test_breaking_and_solo_seat_stay_top(self):
        pool = [ent("brk", cross=2, pub_h=30, breaking=True, grade=1),   # 확정 긴급 도장 = 종전처럼 무조건 최상단
                ent("solo", cross=1, pub_h=0.5, solo=1, title="[속보] 단독 1보"),
                ent("cum", cross=9, pub_h=10)]
        kept, _ = self.run_tc(pool, env={"CAND_CAP": "2"})
        self.assertEqual(set(kept), {"brk", "solo"})

    def test_fresh_keep_h_lever_still_applies(self):
        pool = [ent("fresh", pub_h=1), ent("p35", cross=3, pub_h=3.5), ent("cum", cross=9, pub_h=10)]
        kept, _ = self.run_tc(pool, env={"CAND_CAP": "2"})
        self.assertEqual(set(kept), {"fresh", "p35"})                # 기본 6h: 3.5h 는 신규 칼럼 공급분(3단)
        kept, _ = self.run_tc(pool, env={"CAND_CAP": "2", "CAND_FRESH_KEEP_H": "3"})
        self.assertEqual(set(kept), {"fresh", "cum"})                 # 레버 3h: 3.5h 보호 해제
        kept, _ = self.run_tc(self.base(), env={"CAND_CAP": "2", "CAND_FRESH_KEEP_H": "8"})
        self.assertEqual(set(kept), {"fresh", "cum"})                 # 창을 넓혀도 4h+ 비노출은 누적 뒤

    def test_byte_budget_trims_invisible_first(self):
        pool = self.base()
        size = len(json.dumps([pool[0], pool[2]], ensure_ascii=False).encode("utf-8"))
        kept, log = self.run_tc(pool, env={"CAND_MAX_BYTES": str(size + 40)})
        self.assertEqual(set(kept), {"fresh", "cum"})
        self.assertIn("트림 1건", log)
        self.assertIn("비노출 4~6h 신선 컷 1건", log)

    def test_mirror_import_failure_falls_back_to_old_order(self):
        def broken(m):
            m._cum_enter = None
            m.screen_merge = None
        kept, log = self.run_tc(self.base(), env={"CAND_CAP": "2"}, patch=broken)
        self.assertEqual(set(kept), {"fresh", "mid"})
        self.assertIn("누적 미러 부재·실패", log)

    def test_mirror_runtime_failure_falls_back_to_old_order(self):
        # 평의회7 260924: 미러 **런타임** 예외(이상 필드 등)가 수집함 갱신 전체를 멈추면 안 된다 = 종전 순서로
        def boom(m):
            def bad(kept):
                raise TypeError("unhashable")
            m.cum_visible_ids = bad
        kept, log = self.run_tc(self.base(), env={"CAND_CAP": "2"}, patch=boom)
        self.assertEqual(set(kept), {"fresh", "mid"})
        self.assertIn("누적 미러 부재·실패", log)

    def test_imports_single_python_mirror(self):
        # followEnters 파이썬 사본은 daily_health._cum_enter 한 벌(패리티 게이트 대상) — 새 사본을 만들지 않는다
        m = _load()
        import daily_health
        self.assertIs(m._cum_enter, daily_health._cum_enter)
        self.assertIs(m.screen_merge, daily_health.screen_merge)


if __name__ == "__main__":
    unittest.main()
