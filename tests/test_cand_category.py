# 수집함 묶음 분류·별칭 재판정 회귀(260923 평의회3) — 대표(최초 발행) 피드 섹션 하나가 묶음 분류를 정하고,
#   대표만 바뀐 같은 제목 묶음이 AI 재판정을 다시 타던 것 · 네트워크 0
import importlib.util, json, sys, tempfile, unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scraper"))
_spec = importlib.util.spec_from_file_location("tc_cat", ROOT / "scraper" / "to_candidates.py")
TC = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(TC)
KST = timezone(timedelta(hours=9))


def _iso(h):
    return (datetime.now(timezone.utc) - timedelta(hours=h)).isoformat()


def member(url, cat, pub="블로터"):
    return {"link": url, "title": "차기 한국씨티은행장 김경호", "publisher": pub, "category": cat, "published": _iso(1)}


class ClusterSectionTest(unittest.TestCase):
    def rep(self, cat, members, pick=None):
        return {"category": cat, "cluster_members": members, "breaking_pick": {"url": pick} if pick else None}

    def test_majority_beats_first_publisher_section(self):
        secs = {"a": "테크", "b": "경제", "c": "경제", "d": "경제", "e": ""}
        self.assertEqual(TC.cluster_sec(self.rep("tech", list(secs)), secs), "경제")

    def test_tie_goes_to_pick_then_rep(self):
        secs = {"a": "문화", "b": "사회"}
        self.assertEqual(TC.cluster_sec(self.rep("entertainment", ["a", "b"], pick="b"), secs), "사회")
        self.assertEqual(TC.cluster_sec(self.rep("entertainment", ["a", "b"]), secs), "문화")

    def test_rep_without_section_keeps_keyword_path(self):
        # 대표가 _all_ 이면 종전대로 빈 값 = 키워드·AI 판정 몫(AI 분류 보존 경로 불변)
        self.assertEqual(TC.cluster_sec(self.rep("_all_", ["a", "b"]), {"a": "", "b": "경제"}), "")

    def test_mega_cluster_without_members_uses_rep(self):
        self.assertEqual(TC.cluster_sec(self.rep("society", []), {}), "사회")


class PipelineTest(unittest.TestCase):
    def run_tc(self, arts, existing=None):
        with tempfile.TemporaryDirectory() as d:
            TC.SRC = Path(d) / "articles.json"
            TC.DST = Path(d) / "candidates.json"
            TC.SRC.write_text(json.dumps(arts, ensure_ascii=False), encoding="utf-8")
            TC.DST.write_text(json.dumps(existing or [], ensure_ascii=False), encoding="utf-8")
            TC.main()
            return {c["url"]: c for c in json.loads(TC.DST.read_text(encoding="utf-8"))}

    def test_card_category_follows_member_majority(self):
        rep = {**member("u0", "tech"), "is_cluster_rep": True, "cross_score": 4, "burst": 1, "cluster_size": 4,
               "cluster_members": ["u0", "u1", "u2", "u3"], "breaking_pick": {"url": "u1", "media": "조선일보", "title": "차기 한국씨티은행장 김경호"}}
        arts = [rep, member("u1", "economy", "조선일보"), member("u2", "economy", "서울경제"), member("u3", "economy", "매일경제")]
        self.assertEqual(self.run_tc(arts)["u0"]["cat"], "경제")

    def alias_case(self, pick_title):
        old = {"id": "u9", "url": "u9", "title": "총격 11명 사망 파티장", "cross": 2, "published": _iso(1),
               "first_seen": datetime.now(KST).strftime("%Y-%m-%dT%H:%M:%S%z"), "cluster_members": ["u9", "u1"], "arts": 2,
               "grade_rubric": "g", "breaking_rubric": "b"}
        rep = {"link": "u0", "title": "파티장 총격", "publisher": "연합뉴스", "category": "society", "published": _iso(1.5),
               "is_cluster_rep": True, "cross_score": 3, "burst": 1, "cluster_size": 3, "cluster_members": ["u0", "u1", "u9"],
               "breaking_pick": {"url": "u1", "media": "조선일보", "title": pick_title}}
        return self.run_tc([rep], [old])["u0"]

    def test_alias_with_same_title_keeps_judge_stamps(self):
        out = self.alias_case("총격 11명 사망 파티장")
        self.assertEqual((out.get("grade_rubric"), out.get("breaking_rubric")), ("g", "b"))

    def test_alias_title_change_is_rejudged(self):
        out = self.alias_case("남아공 파티장 총격 11명 사망…용의자 추적")
        self.assertNotIn("grade_rubric", out)
        self.assertNotIn("breaking_rubric", out)


if __name__ == "__main__":
    unittest.main()
