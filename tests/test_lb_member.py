"""최신 국면 멤버(lb) 2행 판정 축 — 회귀 사례(260913 용혜인 자진사퇴 묻힘).

정본 = scraper/lb_member.py(선택) · scraper/to_candidates.carry_lb(캐리·스왑 고정) · .github/scripts/breaking_judge.py(_stamp·build_rows·apply_lb).
네트워크·claude 호출 0. knews_scraper 는 feedparser 의존이라 tokenize 는 정본과 같은 규칙의 거울을 주입한다.
"""
import importlib.util
import json
import re
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scraper"))
from lb_member import pick_lb, LB_TAG  # noqa: E402
import to_candidates as TC  # noqa: E402

_STOP = {"속보", "단독", "종합", "포토", "영상", "인터뷰", "오늘", "내일", "오전", "오후", "기자", "그래픽", "사진",
         "코멘트", "전망", "관련", "현장", "이것", "그것", "공식", "전체", "주요", "기사"}


def tok(title):   # knews_scraper.tokenize 거울(머리표 제거 · 한글2+/영문2+/숫자2+ · 불용어)
    t = re.sub(r"\[[^\]]*\]", " ", title or "")
    return {x for x in re.findall(r"[가-힣]{2,}|[A-Za-z]{2,}|[0-9]{2,}", t) if x not in _STOP}


PRIO = ["조선일보", "동아일보", "연합뉴스", "MBC"]


def rank(pub):
    return PRIO.index(pub) if pub in PRIO else len(PRIO)


def art(title, link, pub, when):
    return {"title": title, "link": link, "publisher": pub, "published": when.isoformat()}


T0 = datetime(2026, 9, 13, 1, 36, tzinfo=timezone.utc)   # 10:36 KST 예고 1보


def _judge():
    spec = importlib.util.spec_from_file_location("bj_test", REPO / ".github" / "scripts" / "breaking_judge.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class PickLb(unittest.TestCase):
    def cluster(self):
        arts = [
            art("[속보] 용혜인 후보자, 오전 11시 30분 국회 기자회견", "https://yna/1", "연합뉴스", T0),          # 0 rep
            art("용혜인 후보자, 오전 11시 30분 국회 기자회견", "https://chosun/1", "조선일보", T0 + timedelta(minutes=3)),  # 1 pick(메이저 최초)
            art("[속보] 용혜인 후보자, 오전 11시 30분 국회 기자회견", "https://sbs/1", "SBS", T0 + timedelta(minutes=5)),  # 2 같은 국면 재탕(부분집합)
            art("[속보] 용혜인 성평등부 장관후보자 자진사퇴‥여당서 결단 의사 전달받아", "https://mbc/1", "MBC", T0 + timedelta(minutes=61)),  # 3 발생 1보
            art("[속보] 용혜인, 성평등부 장관 후보자직 자진 사퇴", "https://yna/2", "연합뉴스", T0 + timedelta(minutes=64)),  # 4 후속
            art("[속보] 김승원 후보자, 국회 청문회 증인 채택 수용", "https://yna/3", "연합뉴스", T0 + timedelta(minutes=66)),   # 5 다른 인물(직함·국회만 공유)
            art("용혜인 장관후보자 사퇴…여야 반응", "https://khan/1", "경향신문", T0 + timedelta(minutes=70)),   # 6 태그 없음
        ]
        return arts

    def test_incident_picks_first_tagged_member(self):
        arts = self.cluster()
        lb = pick_lb(list(range(len(arts))), arts, 0, 1, tok, rank, now=T0 + timedelta(minutes=75))
        self.assertIsNotNone(lb)
        self.assertEqual(lb["u"], "https://mbc/1")            # 창 안 최초 [속보] · 대표와 「용혜인」 공유
        self.assertTrue(lb["t"].startswith("[속보] 용혜인 성평등부"))
        self.assertEqual(lb["m"], "MBC")
        self.assertLessEqual(len(lb["t"]), 80)

    def test_sticky_when_later_tagged_members_arrive(self):
        arts = self.cluster()
        arts.append(art("[2보] 용혜인 사퇴…의원직은 유지", "https://yna/4", "연합뉴스", T0 + timedelta(minutes=80)))
        lb = pick_lb(list(range(len(arts))), arts, 0, 1, tok, rank, now=T0 + timedelta(minutes=85))
        self.assertEqual(lb["u"], "https://mbc/1")            # 최초 선택 유지(끈적임 → 재판정 창당 1회)

    def test_other_person_only_title_words_is_not_linked(self):
        arts = self.cluster()
        others = [arts[0], arts[1], arts[5]]                   # 김승원 [속보]만 남김 — {후보자, 국회} 는 연결 공통어라 제외 → 링크 0
        lb = pick_lb(list(range(len(others))), others, 0, 1, tok, rank, now=T0 + timedelta(minutes=75))
        self.assertIsNone(lb)

    def test_untagged_and_subset_and_self_are_skipped(self):
        arts = self.cluster()
        subset = [arts[0], arts[1], arts[2], arts[6]]          # 재탕(부분집합)·태그 없음·대표·픽만
        lb = pick_lb(list(range(len(subset))), subset, 0, 1, tok, rank, now=T0 + timedelta(minutes=75))
        self.assertIsNone(lb)

    def test_stale_cluster_emits_nothing(self):
        arts = self.cluster()
        lb = pick_lb(list(range(len(arts))), arts, 0, 1, tok, rank, now=T0 + timedelta(hours=5))
        self.assertIsNone(lb)                                   # 최신 발행이 2h+ 전 = 묵은 사건에 필드 안 얹음

    def test_window_is_relative_to_newest_published(self):
        arts = self.cluster()
        arts.append(art("[속보] 용혜인 후임 인선 착수", "https://yna/9", "연합뉴스", T0 + timedelta(minutes=200)))
        lb = pick_lb(list(range(len(arts))), arts, 0, 1, tok, rank, now=T0 + timedelta(minutes=205))
        self.assertEqual(lb["u"], "https://yna/9")            # 최신 발행 기준 60분 창 → 옛 사퇴 1보는 창 밖

    def test_tag_regex(self):
        for t in ("[속보] x", "[1보] x", "[상보] x", "[긴급] x", "[ 속보 ] x"):
            self.assertTrue(LB_TAG.search(t), t)
        for t in ("속보 x", "[단독] x", "[포토] x"):
            self.assertFalse(LB_TAG.search(t), t)


class CarryLb(unittest.TestCase):
    NOW = datetime(2026, 9, 13, 12, 0, tzinfo=timezone(timedelta(hours=9)))

    def test_new_lb_from_scraper_wins(self):
        prev = {"url": "u", "title": "예고", "lb": {"t": "옛", "u": "o", "p": "2026-09-13T01:00:00+00:00"}}
        c = {"url": "u", "title": "예고", "lb": {"t": "새", "u": "n", "p": "2026-09-13T02:40:00+00:00"}}
        e = TC.carry_lb(prev, c, {**prev, **c}, self.NOW)
        self.assertEqual(e["lb"]["t"], "새")

    def test_missing_lb_kept_within_keep_window_then_dropped(self):
        fresh_p = (self.NOW - timedelta(hours=1)).isoformat()
        prev = {"url": "u", "title": "예고", "lb": {"t": "x", "u": "o", "p": fresh_p}}
        c = {"url": "u", "title": "예고"}
        e = TC.carry_lb(prev, c, {**prev, **c}, self.NOW)
        self.assertIn("lb", e)                                  # 발행 1h = LB_KEEP_H(2h) 안 → 유지
        prev["lb"]["p"] = (self.NOW - timedelta(hours=3)).isoformat()
        e = TC.carry_lb(prev, c, {**prev, **c}, self.NOW)
        self.assertNotIn("lb", e)                               # 2h+ → 제거(예산 · 대표 제목만으로 1회 재판정)

    def test_swapped_entry_keeps_member_title_and_lb(self):
        prev = {"url": "u", "title": "[속보] 용혜인 장관후보자 자진사퇴", "media": "MBC", "published": "2026-09-13T02:37:00+00:00",
                "breaking_pick": {"url": "https://mbc/1", "media": "MBC", "title": "[속보] 용혜인 장관후보자 자진사퇴"},
                "lby": 1, "lb": {"t": "[속보] 용혜인 장관후보자 자진사퇴", "u": "https://mbc/1", "p": "2026-09-13T02:37:00+00:00", "m": "MBC"},
                "breaking": True}
        c = {"url": "u", "title": "용혜인 후보자, 오전 11시 30분 국회 기자회견", "media": "조선일보", "published": "2026-09-13T01:36:00+00:00",
             "breaking_pick": {"url": "https://chosun/1", "media": "조선일보", "title": "용혜인 후보자, 오전 11시 30분 국회 기자회견"}}
        e = TC.carry_lb(prev, c, {**prev, **c}, self.NOW + timedelta(hours=6))
        self.assertEqual(e["title"], prev["title"])             # 스크래퍼 픽(예고)이 되돌리지 못한다
        self.assertEqual(e["breaking_pick"]["url"], "https://mbc/1")
        self.assertEqual(e["published"], prev["published"])
        self.assertEqual(e.get("lby"), 1)
        self.assertIn("lb", e)                                  # 스왑건 lb 는 시한 무관 유지(도장 안정 = 강등 경로 없음)


class JudgeRows(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bj = _judge()

    def test_stamp_unchanged_without_lb_and_changes_with_lb(self):
        bj = self.bj
        c = {"title": "용혜인 후보자, 오전 11시 30분 국회 기자회견"}
        legacy = __import__("hashlib").sha256((bj.RUBRIC_VER + "\n" + c["title"]).encode("utf-8")).hexdigest()[:12]
        self.assertEqual(bj._stamp(c), legacy)                  # lb 없는 엔트리 = 종전 도장 그대로(재판정 폭풍 0)
        c["lb"] = {"t": "[속보] 용혜인 장관후보자 자진사퇴"}
        self.assertNotEqual(bj._stamp(c), legacy)
        self.assertEqual(len(bj._stamp(c)), 12)

    def test_build_rows_adds_independent_lb_row(self):
        bj = self.bj
        pending = [{"title": "A 예고", "published": "2026-09-13T01:36:00+00:00", "lb": {"t": "[속보] A 발생", "p": "2026-09-13T02:37:00+00:00"}},
                   {"title": "B 단독", "published": ""}]
        rows = bj.build_rows(pending)
        self.assertEqual([(r[2], r[3]) for r in rows], [(0, "rep"), (0, "lb"), (1, "rep")])
        self.assertTrue(rows[1][1].startswith("[속보] A 발생 〔"))   # lb 행 = 멤버 제목 + 자기 발행 라벨
        self.assertEqual([r[0] for r in rows], [0, 1, 2])

    def test_apply_shadow_keeps_rep_verdict_only(self):
        bj = self.bj
        c = {"title": "예고", "breaking": False, "grade": 1, "grade_rubric": "x", "lb": {"t": "[속보] 발생", "u": "https://m/1", "m": "MBC", "p": "2026-09-13T02:37:00+00:00"}}
        v, swapped, flipped = bj.apply_lb(c, False, True, live=False)
        self.assertFalse(v); self.assertFalse(swapped); self.assertFalse(flipped)
        self.assertEqual(c["title"], "예고"); self.assertEqual(c["grade_rubric"], "x")

    def test_apply_live_swaps_and_regrades_once(self):
        bj = self.bj
        c = {"title": "예고", "media": "조선일보", "published": "2026-09-13T01:36:00+00:00", "breaking": False, "grade": 1, "grade_rubric": "x",
             "breaking_pick": {"url": "https://c/1", "media": "조선일보", "title": "예고"},
             "lb": {"t": "[속보] 발생", "u": "https://m/1", "m": "MBC", "p": "2026-09-13T02:37:00+00:00"}}
        v, swapped, flipped = bj.apply_lb(c, False, True, live=True)
        self.assertTrue(v and swapped and flipped)
        self.assertEqual(c["title"], "[속보] 발생")
        self.assertEqual(c["breaking_pick"]["url"], "https://m/1")
        self.assertEqual(c["published"], "2026-09-13T02:37:00+00:00")   # 멤버가 더 새로움 → 발행 갱신(푸시·자동픽 창)
        self.assertEqual(c.get("lby"), 1)
        self.assertNotIn("grade_rubric", c)                     # D2: 첫 뒤집힘 = 경중 1회 재채점
        # 이미 breaking 인 엔트리에 다시 lb YES = 뒤집힘 아님 → 재채점 안 함
        c["grade_rubric"] = "y"
        v, swapped, flipped = bj.apply_lb(c, False, True, live=True)
        self.assertTrue(v and swapped); self.assertFalse(flipped); self.assertEqual(c["grade_rubric"], "y")

    def test_apply_live_rep_yes_is_untouched(self):
        bj = self.bj
        c = {"title": "[속보] 1보", "breaking": False, "lb": {"t": "[상보] 갱신", "u": "https://m/2", "m": "MBC", "p": ""}}
        v, swapped, flipped = bj.apply_lb(c, True, False, live=True)
        self.assertTrue(v); self.assertFalse(swapped); self.assertEqual(c["title"], "[속보] 1보")
        v, swapped, flipped = bj.apply_lb(c, True, True, live=True)
        self.assertTrue(v); self.assertFalse(swapped)           # 대표 행이 이미 YES 면 스왑 없음(종전 동작)


if __name__ == "__main__":
    unittest.main()
