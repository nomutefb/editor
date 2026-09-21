"""속보 판정 후처리 게이트(.github/scripts/brk_gates.py) 회귀 — 260907~0917 실측 제목이 정답지.
루브릭 본문의 X 예시(스위스 버스 5명·프랑스 열차 44명 부상)가 O로 나오던 구멍을 코드가 막는지 고정한다."""
import importlib.util
import os
import unittest
from pathlib import Path

_P = Path(__file__).resolve().parents[1] / ".github" / "scripts" / "brk_gates.py"


def _load():
    spec = importlib.util.spec_from_file_location("brk_gates", _P)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


G = _load()


class CasualtyCounts(unittest.TestCase):
    def test_korean_numbers(self):
        self.assertEqual(G.casualty_counts("멕시코 종교축제서 폭죽 폭발 참사…10명 숨지고 64명 부상")[:2], (10, 64))
        self.assertEqual(G.casualty_counts("필리핀 여객선 화재 사망자 35명으로 늘어…54명 실종 추정")[0], 35)
        self.assertEqual(G.casualty_counts("필리핀 여객선 화재 사망자 35명으로 늘어…54명 실종 추정")[2], 54)
        self.assertEqual(G.casualty_counts("'네팔·중국 대홍수' 사망·실종자 7천 명 넘어")[3], 7000)
        self.assertEqual(G.casualty_counts("부산 감천항서 선박 가스 누출로 2명 심정지")[0], None)   # 심정지 ≠ 사망

    def test_english_numbers(self):
        self.assertEqual(G.casualty_counts("Twenty-five dead after fire on cargo ship in eastern China")[0], 25)
        self.assertEqual(G.casualty_counts("Gaza building collapse kills 16, traps dozens under rubble")[0], 16)
        self.assertEqual(G.casualty_counts("At least 21 killed after Israeli-hit building in Gaza City collapses")[0], 21)
        self.assertEqual(G.casualty_counts("Passenger train derails in France leaving at least 44 injured")[1], 44)
        self.assertEqual(G.casualty_counts("Several dead, dozens missing after ferry fire in Philippines")[0], None)


class CasualtyGate(unittest.TestCase):
    def x(self, t, cat=None):
        self.assertIsNotNone(G.casualty_gate(t, cat), t)

    def o(self, t, cat=None):
        self.assertIsNone(G.casualty_gate(t, cat), t)

    def test_foreign_rubric_examples(self):
        self.x("스위스 알프스서 네덜란드 관광버스 전복…5명 사망·40명 부상", "국제")   # 루브릭 본문 X 예시
        self.x("Passenger train derails in France leaving at least 44 injured")
        self.x("인도 뉴델리 대학생 하숙 건물 붕괴…5명 사망·수십명 매몰", "국제")
        self.x("Five killed in Miami plane crash were in two vehicles on ground")
        self.x("Several dead, dozens missing after ferry fire in Philippines")
        self.x("인니 화산 분화 취재 나선 사진기자 5명, 순다해협서 실종", "국제")

    def test_foreign_pass(self):
        self.o("멕시코 종교축제서 폭죽 폭발 참사…10명 숨지고 64명 부상", "국제")
        self.o("칠레 남부 노인 요양원에서 불 나 16명 사망", "국제")
        self.o("Fire at nursing home in Chile kills 16 residents")
        self.o("필리핀 여객선 화재 사망자 35명으로 늘어…54명 실종 추정", "국제")
        self.o("이스라엘, 또 레바논 남부 공습…어린이 등 최소 12명 사망", "국제")   # 🌐 군사 10명↑
        self.o("내전 돈줄 된 수단 금광 또 붕괴…최소 60명 사망", "국제")
        self.o("'네팔·중국 대홍수' 사망·실종자 7천 명 넘어…신원 확인 난항", "국제")   # 합산 표기 대형
        self.o("'네팔·중국 대홍수' 사망·실종자 7천 명 넘어…신원 확인 난항")           # cat 없어도 통과

    def test_domestic(self):
        self.x("김해 근린생활시설서 불…40대 남성 심정지 이송", "사회")
        self.x("한밤중 인천 용현동 주택서 불…주민 2명 연기흡입", "사회")
        self.x("경북대 기숙사서 충전 중 휴대전화 화재… 학생 200명 대피", "사회")
        self.x("[속보] 부산 감천항서 선박 가스 누출로 2명 심정지", "사회")
        self.x("서울 성동구 일대 아파트 2시간 정전…승강기 갇힘 사고도", "사회")
        self.o("서울 공장 화재로 3명 사망…소방당국 조사", "사회")   # 루브릭 O 예시

    def test_out_of_scope(self):
        self.o("사우디·후티, 홍해 일대서 사실상 전면전... 500명 사망, 2만명 피란", "국제")   # 전면전 = 규모 자명
        self.o("인도네시아 자카르타 북쪽 바다 규모 6.6 지진", "국제")                    # 🌏 규모 규칙 축
        self.o("남아공 여성안전 '빨간불'…한 도시서 두 달 새 7명 피살", "국제")            # 대인 강력범죄 축
        self.o("‘화재 참사’ 대전 안전공업...손주환 대표 등 구속영장 기각", "사회")        # 사법 어휘 = ③ 담당
        self.o("‘오송참사’ 부실공사 책임자들, 최고 금고 2년", "사회")
        self.o("하이브 팬플랫폼 불법 접근 논란", "사회")   # '불법'의 불 ≠ 화재


class CelebGate(unittest.TestCase):
    def test_romance_status_x(self):
        for t in ["지상렬♥신보람 결별설…은지원 \"헤어진 거냐\"", "‘3살 연상 사업가♥’ 티아라 류화영, 결혼 소감 밝혔다",
                  "조병규, 13년 소속사 떠나 군대 간다..\"카투사 탈락, 육군 생각 중\"", "고수, BH엔터와 15년 동행 마무리…\"새로운 출발 응원\"",
                  "송혜교, 파리서 남자 지인과 데이트…어깨에 살포시", "백진희 “예비신랑=재력가 아닌 평범한 직장인”",
                  "톰 홀랜드♥젠데이아, 결혼했다더니 말장난?…측근 “거짓말, 아직 안 해”"]:
            self.assertIsNotNone(G.celeb_gate(t), t)

    def test_incident_pass(self):
        for t in ["'이혼 빚 딛고 화가로 복귀' 낸시랭, 새벽 만취운전 경찰 적발", "‘화상·피폭·차별’ 넘은 타격왕 장훈 별세",
                  "방송·사업 잘나가던 유명 女진행자 ‘마약 혐의’ 사형 선고", "○○ 그룹 해체 공식화", "배우 ○○ 고속도로 사고 중상"]:
            self.assertIsNone(G.celeb_gate(t), t)


class JudicialGate(unittest.TestCase):
    def test_procedural_x(self):
        for t in ["[속보] 경찰, 비위 의혹 김병기 의원 구속영장 신청 결정", "‘화재 참사’ 대전 안전공업...손주환 대표 등 구속영장 기각",
                  "'방첩사 블랙리스트' 여인형 재판 시작", "'윤석열 비화폰 삭제' 박종준 전 경호처장 2심서 징역 3년 구형…다음 달 14일 선고",
                  "'가족 조합' 김승원·'12억 관사' 추미애, 경찰 수사 본격화", "檢, ‘1.3억 쪼개기 후원’ 강선우·김경 추가 기소",
                  "김수현 ‘미성년자 그루밍 의혹’ 종결 수순…검찰, 재수사 없이 ‘불송치’ 판단 유지",
                  "'이종섭 호주도피' 윤석열 오늘 1심 선고…특검, 징역 5년 구형"]:
            self.assertIsNotNone(G.judicial_gate(t, 3), t)

    def test_verdict_x(self):   # 운영자 260921 «항소심 선고 이런 관련된거는 다 긴급 안오게» — 결과(선고·판결)도 X
        for t in ["[속보] ‘이종섭 도피 의혹’ 윤석열, 1심 무죄", "‘특수부대 기밀 누설’ 문상호 前정보사령관 1심서 무죄",
                  "3세 원아 12명 114차례 학대… 어린이집 교사 2명 1심서 법정 구속",
                  "[속보] 법원 “‘연락사무소 폭파’ 北, 정부에 446억원 배상해야”",
                  "'오송참사 부실 제방' 1심 법정최고형 금호건설·감리사 항소",
                  "‘계엄 문건’ 김용현, 항소심서 징역 5년 선고", "대법원, 김건희 상고 기각…징역 2년 확정",
                  "[속보] 윤석열 내란 혐의 2심 선고…무기징역"]:
            self.assertIsNotNone(G.judicial_gate(t, 3), t)
            self.assertIsNotNone(G.judicial_gate(t, 20), t)   # 매체가 몰려도 X(cross 통과 폐지)

    def test_exceptions_pass(self):
        for t in ["뜨거운 물 붓고 폭행해 친딸 살해 40대 女가수, 사형 구형",   # 사형 예외 = 구형이어도 O(260831)
                  "방글라데시 법원, 반정부 시위 유혈 진압한 전 장관 등 7명 사형 판결",
                  "[속보] 헌재, 윤석열 대통령 탄핵 인용…파면 선고"]:   # 탄핵 = 정치 사태 축
            self.assertIsNone(G.judicial_gate(t, 3), t)

    def test_mass_coverage_still_x(self):
        t = "선관위 특검, 중앙·지방선관위 등 9개소 압수수색"
        self.assertIsNotNone(G.judicial_gate(t, 3))
        self.assertIsNotNone(G.judicial_gate(t, 12))   # 구판 「매체 몰림 = 통과」 폐지(260921)


class Switch(unittest.TestCase):
    def test_gate_reason_order_and_killswitch(self):
        self.assertTrue(G.gate_reason("스위스 알프스서 관광버스 전복…5명 사망·40명 부상", "국제", 2).startswith("해외"))
        self.assertIsNone(G.gate_reason("칠레 남부 노인 요양원에서 불 나 16명 사망", "국제", 2))
        os.environ["BRK_GATES"] = "0"
        try:
            self.assertIsNone(_load().gate_reason("지상렬♥신보람 결별설", "문화", 2))   # 킬스위치 = 전 축 OFF
        finally:
            os.environ.pop("BRK_GATES", None)


if __name__ == "__main__":
    unittest.main()
