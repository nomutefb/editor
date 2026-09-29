# 자동픽(유료 자동분석) 연예 관계·지위 제외 — 260929 게이트 ② 완화(메이저 명단 관계 소식 → 판정기)로 새로 열린 과금 경로 보존 차단
import datetime as dt
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scraper"))
import auto_pick_breaking as A  # noqa: E402


def cand(title):
    now = dt.datetime.now(A.KST).strftime("%Y-%m-%dT%H:%M:%S%z")
    return {"breaking": True, "grade": 3, "cross": 5, "first_seen": now, "title": title}


class AutopickCeleb(unittest.TestCase):
    def test_relationship_excluded(self):
        self.assertFalse(A.eligible(cand("아이유·이종석, 4년 열애 끝 결별")))
        self.assertFalse(A.eligible(cand("한예리, 신생 기획사와 전속계약 체결")))

    def test_incident_kept(self):
        self.assertTrue(A.eligible(cand("닛몰캐쉬, 데이트폭력·비하발언 폭로 터졌다")))
        self.assertTrue(A.eligible(cand("공장 화재로 5명 사망")))

    def test_lever_opens(self):
        old = A.CELEB_OK
        try:
            A.CELEB_OK = True
            self.assertTrue(A.eligible(cand("아이유·이종석, 4년 열애 끝 결별")))
        finally:
            A.CELEB_OK = old
