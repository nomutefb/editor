"""속보 판정 후처리 게이트(.github/scripts/brk_gates.py) 회귀 — 260907~0917 실측 제목이 정답지.
루브릭 본문의 X 예시(스위스 버스 5명·프랑스 열차 44명 부상)가 O로 나오던 구멍을 코드가 막는지 고정한다."""
import importlib.util
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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

    def test_cumulative_deaths_are_not_current_casualties(self):
        for t in ["가자 공습 누적 사망자 6만 명 넘어",
                  "올해 산업재해로 500명 사망", "올 들어 교통사고 사망자 100명",
                  "최근 3년간 화재로 300명 사망", "개전 이후 사망자 1만 명",
                  "공습 사망자 1만 명으로 누적 집계", "사망자 누적 100명", "올해 교통사고…100명 사망",
                  "누적 집계 오늘 100명 사망",
                  "Gaza death toll passes 60,000 since war began",
                  "Airstrikes have killed 1,000 people so far",
                  "Floods killed 300 people since the new year",
                  "Floods killed 300 people this year"]:
            with self.subTest(title=t):
                self.assertEqual(G.casualty_counts(t)[0], None)

    def test_mixed_current_and_cumulative_counts(self):
        for t, expected in [
            ("서울 공장 화재 1명 사망…올해 누적 사망자 100명", 1),
            ("올해 누적 사망자 100명…서울 공장 화재로 3명 사망", 3),
            ("공습으로 2명 추가 사망해 누적 사망자 100명", 2),
            ("공습으로 12명 사망해 누적 100명", 12),
            ("누적 사망자 100명, 오늘 공습으로 12명 사망", 12),
            ("누적 사망자 100명 가운데 오늘 공습으로 12명 사망", 12),
            ("누적 사망자 100명 가운데 공습으로 12명 추가 사망", 12),
            ("Airstrike kills 2; cumulative death toll reaches 1,000", 2),
            ("Since war began 1,000 killed; new airstrike kills 12", 12),
        ]:
            with self.subTest(title=t):
                self.assertEqual(G.casualty_counts(t)[0], expected)

    def test_current_incident_total_and_other_numbers_survive(self):
        self.assertEqual(G.casualty_counts("여객선 화재 사망자 35명으로 늘어…54명 실종 추정"),
                         (35, None, 54, None))
        self.assertEqual(G.casualty_counts("Fire death toll rises to 10"), (10, None, None, None))
        self.assertEqual(G.casualty_counts("올해 첫 공장 화재로 3명 사망"), (3, None, None, None))
        self.assertEqual(G.casualty_counts("누적 강수량 300㎜…홍수로 12명 사망"), (12, None, None, None))
        self.assertEqual(G.casualty_counts("누적 강수량 300㎜ 홍수로 12명 사망"), (12, None, None, None))

    def test_aggregate_combined_counts_cannot_bypass_gate(self):
        self.assertEqual(G.casualty_counts("올해 홍수 사망·실종자 7천 명"), (None, None, None, None))
        self.assertEqual(G.casualty_counts("전쟁 이후 누적 사망자 100명·부상자 500명·실종자 200명"),
                         (None, None, None, None))


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

    def test_cumulative_counts_never_satisfy_threshold(self):
        self.x("올해 산업재해 사망자 500명", "사회")
        self.x("가자 공습 누적 사망자 6만 명", "국제")
        self.x("전쟁 발발 이후 사망자 1만 명", "국제")
        self.x("올해 홍수 사망·실종자 7천 명", "국제")
        self.x("서울 공장 화재 1명 사망…올해 누적 사망자 100명", "사회")
        self.x("공습으로 2명 추가 사망해 누적 사망자 100명", "국제")
        self.x("Airstrike kills 2; cumulative death toll reaches 1,000")

    def test_current_count_still_controls_threshold(self):
        self.o("올해 누적 사망자 100명…서울 공장 화재로 3명 사망", "사회")
        self.o("누적 사망자 100명, 오늘 공습으로 12명 사망", "국제")
        self.o("Since war began 1,000 killed; new airstrike kills 12")
        self.o("누적 사망자 100명…오늘 열차 탈선 50명 부상", "국제")
        self.o("누적 사망자 100명…오늘 여객선 침몰 150명 실종", "국제")

    def test_out_of_scope(self):
        self.o("사우디·후티, 홍해 일대서 사실상 전면전... 500명 사망, 2만명 피란", "국제")   # 전면전 = 규모 자명
        self.o("인도네시아 자카르타 북쪽 바다 규모 6.6 지진", "국제")                    # 🌏 규모 규칙 축
        self.o("일가족 살해 후 도주…2명 사망", "사회")                                  # 국내 대인 강력범죄 = 피해자 수 축(루브릭 🔪)
        self.o("‘화재 참사’ 대전 안전공업...손주환 대표 등 구속영장 기각", "사회")        # 사법 어휘 = ③ 담당
        self.o("‘오송참사’ 부실공사 책임자들, 최고 금고 2년", "사회")
        self.o("하이브 팬플랫폼 불법 접근 논란", "사회")   # '불법'의 불 ≠ 화재


class ForeignCrimeUnified(unittest.TestCase):   # 운영자 260930 «해외 같은 경우 10명 이상 사망으로 통일» — 해외 범죄·테러 = 해외 사고 문턱
    def test_below_threshold_x(self):
        for t, cat in [("Somali pirates killed five crew members on hijacked tanker, officials say", "국제"),   # 260930 실발송
                       ("소말리아 해적, 납치 유조선 선원 5명 살해", "국제"), ("파리 카페 테러로 2명 사망", "국제"),
                       ("美 총기 난사 3명 사망·20명 부상", "국제"), ("남아공 여성안전 '빨간불'…한 도시서 두 달 새 7명 피살", "국제"),
                       ("폴란드 수도원서 우크라인 흉기 난동…5명 사상", "국제")]:   # 「N명 사상」 = 합산(평의회260930 실데이터)
            r = G.casualty_gate(t, cat)
            self.assertIsNotNone(r, t)
            self.assertIn("범죄·테러", r)

    def test_threshold_or_out_of_scope_pass(self):
        for t, cat in [("나이지리아 무장괴한 총격에 12명 사망", "국제"), ("Gunmen kill 12 villagers in Nigeria", "국제"),
                       ("테러범 총기 난사 5명 사망·60명 부상", "국제"),        # 부상 50↑ = 해외 문턱 충족(각 독립)
                       ("[속보] 이스라엘 行 항공기, 납치 신호 발신", "국제"),  # 피해 수 미상 진행형 = 루브릭 판정(260930 운영자 ㅇㅋ)
                       ("Gunman opens fire at Texas mall", "국제"),
                       ("필리핀서 한국인 관광객 피살", "국제"),               # 한국 직접영향 = 🌐 종전
                       ("주택가서 모녀 흉기에 숨진 채 발견", "사회")]:         # 국내 = 피해자 수 축
            self.assertIsNone(G.casualty_gate(t, cat), t)

    def test_count_parsing_pass(self):   # 평의회260930 — 수를 제대로 읽거나 못 읽으면 판정기로(수 미상 오차단 0)
        for t in ["사망자 12명 부상자 20명…美 총격", "美 총격 사망 12명 부상 20명", "총격 사상자 60명",   # 사상자 = 사망+부상 → 59↑면 한 문턱은 반드시 넘는다
                  "수십 명 사망·8명 부상…나이지리아 총격", "Dozens killed, 8 injured in Nigeria gunmen attack"]:
            self.assertIsNone(G.casualty_gate(t, "국제"), t)

    def test_domestic_axis_and_hold_pass(self):   # 한인 피해·국내 장소 = 국내 축 · 요인 저격·전쟁 개시·진압(가해자 사살) = 종전 판정
        for t, cat in [("LA서 한인 2명 피살", "국제"), ("소말리아 해적, 한국 선원 2명 살해", "국제"), ("주한미군 총기 난사로 2명 사망", "국제"),
                       ("Gunman kills 2 in Seoul subway station", "국제"), ("서울 지하철역서 흉기 피격…2명 사망", "사회"),
                       ("Two killed in Seoul subway stabbing", "사회"), ("트럼프 유세 중 총격…청중 1명 사망", "국제"),
                       ("하마스 무장대원 침투…민간인 납치·5명 사망", "국제"), ("[속보] 모스크바 공연장 인질극 진압…테러범 5명 사살", "국제"),
                       ("Police kill 3 gunmen after hostage siege at mall", "국제"), ("살인적 폭염에 인도서 8명 사망", "국제")]:
            self.assertIsNone(G.casualty_gate(t, cat), t)

    def test_new_crime_words_keep_old_accident_axis(self):   # 260930 신설 범죄어가 사고·군사 판정을 풀지 않는다(평의회260930 재현)
        for t, cat in [("해적선 놀이기구 추락 사고 2명 사망", "사회"), ("해적 피습 화물선 침몰", "국제"),
                       ("이스라엘군 가자 난민촌 공습…하마스 \"학살\" 규탄", "국제"), ("이스라엘군, 공습으로 하마스 대원 12명 사살", "국제")]:
            self.assertIsNotNone(G.casualty_gate(t, cat), t)

    def test_kill_count_crime_only(self):   # 「N명 피살」은 범죄 축에서만 센다 = 유명인 ⑤·국내 사법 축 무접촉
        self.assertIsNone(G.casualty_counts("교수 등 2명 피살…경찰 수사 착수")[0])
        self.assertEqual(G.casualty_counts("사망자 12명 부상자 20명…美 총격")[:2], (12, 20))
        self.assertEqual(G.casualty_counts("5명 사망 12명 부상 버스 추락")[:2], (5, 12))   # B#8 유지

    def test_accident_unchanged(self):
        self.assertIsNotNone(G.casualty_gate("Floods kill dozens in Nepal", "국제"))   # 사고 수 미상 = 종전대로 X


class CelebGate(unittest.TestCase):
    def test_romance_status_x(self):
        for t in ["조병규, 13년 소속사 떠나 군대 간다..\"카투사 탈락, 육군 생각 중\"", "고수, BH엔터와 15년 동행 마무리…\"새로운 출발 응원\"",
                  "송혜교, 파리서 남자 지인과 데이트…어깨에 살포시", "백진희 “예비신랑=재력가 아닌 평범한 직장인”",
                  "'박수홍♥' 김다예, '90kg→52kg' 2년만에 부산행", "라이즈, 11월 3일 컴백 확정",   # 명단 인물이어도 근황·컴백·♥ 표기 = X
                  "톰 홀랜드♥젠데이아, 결혼했다더니 말장난?…측근 “거짓말, 아직 안 해”"]:
            self.assertIsNotNone(G.celeb_gate(t), t)

    def test_major_roster_defers_to_rubric(self):
        # 운영자 260929 A2 — 메이저급 참조 명단 인물은 ② 축을 건너뛴다(루브릭 🎤 «메이저급 연예인 혼인·사건 예외»가 판정)
        for t in ["지상렬♥신보람 결별설…은지원 \"헤어진 거냐\"", "‘3살 연상 사업가♥’ 티아라 류화영, 결혼 소감 밝혔다",
                  "아이유·이종석, 4년 열애 끝 결별", "지민이 열애 인정", "한예리, 신생 기획사와 전속계약 체결"]:
            self.assertIsNone(G.celeb_gate(t), t)
        self.assertIsNotNone(G.celeb_gate("신인 배우 김아무개 열애설"))          # 명단 밖 = 종전대로 X
        self.assertIsNotNone(G.celeb_gate("비 오는 날 결혼식 하객 패션"))        # 1자 이름은 일치 판정 제외

    def test_dating_violence_is_incident(self):
        # 운영자 260929 A1 — 닛몰캐쉬 실측 제목: `데이트` 가 데이트폭력에 걸려 판정기 YES 를 X 로 확정할 자리
        for t in ["닛몰캐쉬, 데이트폭력·비하발언 폭로 터졌다…전 여친 녹취록 공개 '확산' [Oh!쎈 이슈]",
                  "'잘자요 아가씨' 닛몰캐쉬, 데이트 폭력 인정 \"주장 대부분 사실\" [공식입장]",
                  "아이돌 ○○, 성추행 혐의…소속사 \"법적 대응\"", "배우 ○○ 소속사 \"불법촬영 의혹 사실무근\""]:
            self.assertIsNone(G.celeb_gate(t), t)
        self.assertIsNotNone(G.celeb_gate("신인 배우 김아무개, 한강 데이트 포착"))   # 연애 데이트는 종전대로 X

    def test_gossip_stays_closed(self):
        # 평의회260929 #3 실측 — 폭로·하차·조직폭력배 가십이 통과어로 다시 열리지 않는다(260917 타이트닝 보존)
        for t in ["한혜진, '8살 연하' ♥기성용 분량 욕심 폭로 \"유튜브 자기 분량 체크해\"",
                  "박보검♥신예은 로맨스 결국 못 본다…'밤 여행자' 편성 불발에 나란히 하차",
                  "'두 번 이혼' 박원숙 \"전남편 빚 때문에 방송국에 조직폭력배 찾아와\""]:
            self.assertIsNotNone(G.celeb_gate(t), t)

    def test_roster_match_precision(self):
        # 평의회260929 #4 — 2자 이름은 주어 자리만 · 3자↑ 는 낱말 중간 부분일치 제외
        self.assertIsNone(G.major_in("'서프라이즈' 같네..'재혼 황후', 베일 벗을수록"))   # 라이즈 ⊂ 서프라이즈
        self.assertIsNone(G.major_in("결혼식 지연 논란…하객 불만"))                       # 지연 = 일반명사 자리
        self.assertEqual(G.major_in("지민이 열애 인정"), "지민")                           # 첫 낱말 + 조사 꼬리
        self.assertEqual(G.major_in("수영, 열애 인정"), "수영")                             # 뒤 쉼표 = 주어 자리


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
        for t in ["뜨거운 물 붓고 폭행해 친딸 살해 40대 女가수, 사형 구형",   # 사형 예외 = 구형 1보(260831 · 260930 구형만)
                  "여고생 살해 장윤기에 ‘사형’ 구형···검찰 “각종 궤변·거짓 주장, 재범 위험”",
                  "檢 \"사형 선고해 달라\"…장윤기 결심공판", "장윤기 1심 결심공판…검찰 사형 구형",
                  "항소심서도 사형 구형…檢 \"반성 없어\"", "檢, 주범 사형·공범 무기징역 구형",
                  "檢, 장윤기 사형 구형…선고는 다음 달 20일", "檢, 장윤기 사형 구형…다음 달 20일 선고",   # 뒷날 선고 안내 = 구형 기사
                  "檢, ○○ 사형 구형…선고 11월 14일", "檢 \"○○ 사형 선고 해달라\"", "\"○○ 사형에 처해달라\"…결심공판",
                  "무죄 주장 ○○에 검찰 사형 구형", "1심서 사형 선고받은 ○○, 항소심서도 사형 구형", "집행유예 기간 중 살인 ○○에 사형 구형",
                  "Prosecutors seek death penalty for Buffalo shooter",
                  "[속보] 헌재, 윤석열 대통령 탄핵 인용…파면 선고"]:   # 탄핵 = 정치 사태 축
            self.assertIsNone(G.judicial_gate(t, 3), t)

    def test_death_ambiguous_deferred_to_judge(self):   # 「구형」이 적힌 선고 되짚기 = 제목으로 못 가른다(평의회260930) → 게이트 밖 = 판정기 _OP260930_RULE
        for t in ["장윤기 1심 무기징역…檢 사형 구형했지만", "'모텔 약물 연쇄살인' 김소영 1심 선고…檢, 사형 구형"]:
            self.assertIsNone(G.judicial_gate(t, 3), t)

    def test_death_sentence_not_demand_x(self):   # 운영자 260930 «선고든 예고든 구형이 된 게 아니면 다 제외»
        for t in ["검찰 “사형 선고해달라”…‘여고생 살해범’ 장윤기 오늘 1심 선고",   # 260930 06:32 실발송(선고 예고)
                  "방글라데시 법원, 반정부 시위 유혈 진압한 전 장관 등 7명 사형 판결", "법원, 장윤기에 사형 선고",
                  "장윤기 사형 선고 앞두고…유족 \"엄벌\"", "사형 구형 장윤기, 오늘 선고", "장윤기, 사형 구형 이어 오늘 운명의 날",
                  "장윤기 오늘 결심공판…검찰 사형 구형 예정", "장윤기 30일 1심 선고…사형 판결 나올까", "日 법원, 교토애니 방화범에 사형",
                  "美 배심원단, 버펄로 총격범 사형 평결", "Bangladesh court sentences Hasina to death"]:
            self.assertIsNotNone(G.judicial_gate(t, 3), t)

    def test_mass_coverage_still_x(self):
        t = "선관위 특검, 중앙·지방선관위 등 9개소 압수수색"
        self.assertIsNotNone(G.judicial_gate(t, 3))
        self.assertIsNotNone(G.judicial_gate(t, 12))   # 구판 「매체 몰림 = 통과」 폐지(260921)

    def test_filming_set_is_not_warrant(self):   # 「촬영장」 ⊃ 「영장」 오인(260929) — 사고는 인명 문턱으로, 사법 축 아님
        self.assertIsNone(G.judicial_gate("드라마 촬영장 화재…배우들 긴급 대피", 3))
        self.assertIsNone(G.gate_reason("드라마 촬영장 화재로 5명 사망"))
        self.assertTrue(G.gate_reason("드라마 촬영장 화재로 2명 사망").startswith("국내"))
        self.assertIsNotNone(G.judicial_gate("○○ 구속영장 청구", 3))


class LiveTier(unittest.TestCase):   # 확산 [강](lv.t≥3 · 260929 A9) = 연예 관계·지위 축만 면제 · 인명 문턱·사법 축 유지
    def test_strong_skips_celeb_only(self):
        self.assertIsNone(G.gate_reason("배우 ○○·가수 ○○ 열애설", "문화", 2, 3))
        self.assertIsNotNone(G.gate_reason("배우 ○○·가수 ○○ 열애설", "문화", 2, 2))   # [중] = 면제 없음
        self.assertIsNotNone(G.gate_reason("가수 ○○, 신곡 들고 컴백", "문화", 2, 3))     # 콘텐츠 축 = [강]이어도 X
        self.assertTrue(G.gate_reason("유튜버 ○○ 탄 차량 사고로 2명 사망", live=3).startswith("국내"))
        self.assertIsNone(G.gate_reason("닛몰캐쉬, 데이트폭력·비하발언 폭로 터졌다…전 여친 녹취록 공개", "문화", 1, 3))   # 목표 사례 = 면제 없이도 통과

    def test_evidence_and_episode_words(self):   # V6 — 「증거」 한 낱말 = 사법 아님 · 「피소」 = 사법 · 「에피소드」 ≠ 피소
        self.assertIsNone(G.gate_reason("닛몰캐쉬 전 여친 «증거 있다»…녹취 공개", "문화", 3, 3))
        self.assertIsNone(G.gate_reason("상상력이 증거가 될 순 없어", "문화", 3, 0))
        self.assertIsNotNone(G.gate_reason("北 증거인멸 정황", "정치", 3, 0))
        self.assertIsNotNone(G.gate_reason("검찰, ○○ 증거 조작 의혹", "사회", 3, 0))
        self.assertIsNotNone(G.gate_reason("유튜버 ○○, 전 여자친구에 피소", "문화", 3, 0))       # 피소 = 사법(확산 없음)
        self.assertIsNone(G.gate_reason("유튜버 ○○, 전 여자친구에 피소", "문화", 3, 3))          # [강] 연예 = 수사 단계 개방(운영자 260929)
        self.assertIsNotNone(G.gate_reason("가수 ○○ 결혼 에피소드 공개", "문화", 3, 0))       # 에피소드 = 연예 통과어 아님 → 연예 축 X
        self.assertIsNone(G.gate_reason("예능 에피소드 화제", "문화", 3, 0))                   # 에피소드 = 사법어 아님

    def test_strong_celeb_scope_entertainment_only(self):   # V7 — [강] 관계·지위 완화 = 연예·문화 인물만 · V3 — 시점 부사 관계어 = 콘텐츠
        self.assertIsNotNone(G.gate_reason("손흥민 선수 결혼 발표", "스포츠", 5, 3))
        self.assertIsNotNone(G.gate_reason("○○ 의원 결혼", "정치", 3, 3))
        self.assertIsNone(G.gate_reason("배우 ○○, 비연예인과 결혼 발표", "문화", 3, 3))
        self.assertIsNone(G.gate_reason("유튜버 ○○ 열애 인정", "사회", 3, 3))
        for t in ("가수 ○○, 결혼 3년 만에 임신", "배우 ○○, 결혼 앞두고 웨딩 화보 공개", "배우 ○○, 이혼 후 근황 공개", "가수 ○○, 입대 앞두고 마지막 콘서트"):
            self.assertIsNotNone(G.gate_reason(t, "문화", 3, 3), t)
        self.assertIsNone(G.gate_reason("배우 ○○, 결혼 3년 만에 파경", "문화", 3, 3))

    def test_strong_opens_investigation_only(self):   # 운영자 260929 «고소 수사도 열어» — [강] 연예 = 수사 단계만 · 재판 단계는 260921 그대로 · 공직 = 그대로
        self.assertIsNone(G.gate_reason("유튜버 ○○ 전 여친 폭행 고소…경찰 수사", live=3))
        self.assertIsNone(G.gate_reason("유튜버 ○○ 구속영장 신청…증거인멸 우려", live=3))
        self.assertIsNotNone(G.gate_reason("유튜버 ○○ 전 여친 폭행 고소…경찰 수사", live=2))    # [중] = 종전
        self.assertIsNotNone(G.gate_reason("유튜버 ○○ 재판 넘겨져…첫 공판", live=3))            # 재판 단계 = 그대로
        self.assertIsNotNone(G.gate_reason("유튜버 ○○ 1심서 징역형 집행유예", live=3))
        self.assertIsNotNone(G.gate_reason("○○ 전 장관 고소…경찰 수사", "정치", 5, 3))           # 공직 = 개방 대상 아님
        self.assertIsNotNone(G.gate_reason("가수 ○○, 항소심서 징역 3년 선고", "문화", 11, 3))
        self.assertIsNotNone(G.gate_reason("○○ 전 장관, 항소심서 징역 2년 선고", "정치", 12, 3))
        self.assertIsNotNone(G.gate_reason("○○ 의원 뇌물 혐의 구속영장 청구", "사회", 5, 3))
        self.assertIsNone(G.gate_reason("수영장 붕괴로 5명 사망", "사회", 3, 3))       # 「수영장」 ≠ 영장

    def test_sweep_keeps_live_backed_verdict(self):
        j = JudgeIntegration()
        result = j.run_judge([
            {"title": "배우 ○○·가수 ○○ 열애설", "cat": "문화", "breaking": True, "lv": {"k": "○○", "t": 3}},
            {"title": "배우 ○○·가수 ○○ 열애설", "cat": "문화", "breaking": True},
        ], pending=False)
        self.assertEqual([c["breaking"] for c in result], [True, False])   # 소급 스윕 = 확산 [강] 근거 판정을 뒤집지 않는다


class Switch(unittest.TestCase):
    def test_gate_reason_order_and_killswitch(self):
        self.assertTrue(G.gate_reason("스위스 알프스서 관광버스 전복…5명 사망·40명 부상", "국제", 2).startswith("해외"))
        self.assertIsNone(G.gate_reason("칠레 남부 노인 요양원에서 불 나 16명 사망", "국제", 2))
        os.environ["BRK_GATES"] = "0"
        try:
            self.assertIsNone(_load().gate_reason("지상렬♥신보람 결별설", "문화", 2))   # 킬스위치 = 전 축 OFF
        finally:
            os.environ.pop("BRK_GATES", None)


class JudgeIntegration(unittest.TestCase):
    """AI의 YES, 기확정 데이터, 최신 멤버 스왑 모두 동일한 누적 제외 규칙을 적용한다."""
    def run_judge(self, cands, pending=True, live=False):
        spec = importlib.util.spec_from_file_location("cumulative_judge", _P.with_name("breaking_judge.py"))
        bj = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(bj)
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "candidates.json"
            path.write_text(json.dumps(cands), encoding="utf-8")
            with patch.object(bj, "CAND", path), patch.object(bj, "LB_LIVE", live), \
                 patch.object(bj, "needs_judging", return_value=pending), \
                 patch.object(bj, "judge", side_effect=lambda items: ({k: True for k, _ in items}, 0, "")), \
                 patch.object(bj, "_shadow_log"), patch.object(sys, "argv", ["breaking_judge.py"]), \
                 contextlib.redirect_stdout(io.StringIO()):
                bj.main()
            return json.loads(path.read_text(encoding="utf-8"))

    def test_model_yes_is_overridden_only_for_aggregate(self):
        result = self.run_judge([
            {"title": "올해 산업재해 사망자 500명", "cat": "사회"},
            {"title": "서울 공장 화재 3명 사망…올해 누적 사망자 100명", "cat": "사회"},
        ])
        self.assertEqual([c["breaking"] for c in result], [False, True])

    def test_existing_breaking_is_demoted_without_model_call(self):
        result = self.run_judge([
            {"title": "공습 누적 사망자 1만 명", "cat": "국제", "breaking": True},
        ], pending=False)
        self.assertFalse(result[0]["breaking"])

    def test_latest_member_cannot_reintroduce_cumulative_count(self):
        result = self.run_judge([
            {"title": "가자 공습 2명 사망", "cat": "국제",
             "lb": {"t": "가자 공습 누적 사망자 1만 명", "u": "https://example.test/latest"}},
        ], live=True)
        self.assertFalse(result[0]["breaking"])




class NotableDeath(unittest.TestCase):   # 운영자 260929 «사망자수는 불특정 다수일때만이야» — 유명인 개인 사망 = ① 인명 문턱 밖(⑤)
    def test_notable_single_death_skips_casualty(self):
        self.assertIsNone(G.gate_reason("배우 ○○ 교통사고로 사망", "문화"))
        self.assertIsNone(G.gate_reason("前 국가대표 ○○, 등산 중 추락사", "스포츠"))
        self.assertIsNone(G.gate_reason("○○ 전 장관, 자택 화재로 숨져", "사회"))
        self.assertIsNone(G.gate_reason("○○ 교통사고로 숨져", "사회", 3, 3))                     # [강] = 유명인 신호
        self.assertIsNone(G.gate_reason("'국민 MC' ○○, 교통사고로 사망…향년 58세", "문화"))       # MC·향년 = 특정 개인 신호

    def test_anonymous_or_multi_or_nonfatal_keeps_casualty(self):
        self.assertIsNotNone(G.gate_reason("30대 남성 교통사고로 숨져", "사회"))                   # 유명인 신호 없음
        self.assertIsNotNone(G.gate_reason("관광버스 추락 2명 사망", "사회"))
        self.assertIsNotNone(G.gate_reason("유튜버 ○○ 촬영장 화재로 2명 사망", "문화", 3, 3))     # 확정 사망 2명↑ 명시 = 다수 피해
        self.assertIsNotNone(G.gate_reason("가수 ○○ 교통사고로 중상", "문화"))                   # 사망 아님
        self.assertIsNotNone(G.gate_reason("치과의원 화재로 1명 사망", "사회"))                   # 의원 ≠ 치과의원

    def test_roster_adds_chungha(self):   # 운영자 260929 «연예인 맞어» — 청하 = 메이저급 명단(2자 = 주어 자리만)
        self.assertEqual(G.major_in("청하, 3년간 함께했던 박재범 품 떠난다…모어비전 전속계약 종료"), "청하")
        self.assertIsNone(G.gate_reason("청하, 3년간 함께했던 박재범 품 떠난다…모어비전 전속계약 종료", "문화"))
        self.assertIsNone(G.major_in("요청하다 거절당해 결별"))


class Council260929_3(unittest.TestCase):   # 평의회260929-3 재현 사례 고정(A·B·E·F·G)
    def test_entertainment_scope(self):
        self.assertIsNone(G.gate_reason("닛몰캐쉬, 전 여친에 피소…경찰 수사 착수", "사회", 3, 3))   # 연예인 사법 기사 = 분류 사회
        self.assertIsNone(G.gate_reason("영화감독 ○○ 성추행 피소", "문화", 3, 3))                  # 영화감독 ≠ 체육 감독
        self.assertIsNone(G.gate_reason("배우 ○○, 배우자 폭행 혐의 입건", "문화", 3, 3))
        self.assertIsNotNone(G.gate_reason("축구선수 ○○ 성폭행 혐의 피소", "문화", 3, 3))         # 체육 = 개방 대상 아님
        self.assertIsNotNone(G.gate_reason("투수 ○○ 폭행 혐의 입건", "문화", 3, 3))
        self.assertIsNone(G.gate_reason("청하, 폭행 혐의로 경찰 입건", "사회", 3, 3))              # 명단 인물(2자 주어 자리) · 분류 사회
        self.assertIsNone(G.gate_reason("닛몰캐쉬, 데이트폭력 혐의로 경찰 입건", "사회", 3, 3))

    def test_live_strong_yes_cases_pass_gate(self):   # 평의회260929-3 H#1 — 회귀 원장의 〔확산 강〕 YES 사례는 운영 게이트도 통과해야 한다(분류 문화·사회·None)
        import json, pathlib
        cs = json.loads((pathlib.Path(__file__).resolve().parents[1] / ".github/scripts/rubric_regress_cases.json").read_text(encoding="utf-8"))["cases"]
        yes = [c["t"] for c in cs if c["expect"] == "YES" and "〔확산 강" in c["t"]]
        self.assertGreater(len(yes), 3)
        for t in yes:
            for cat in ("문화", "사회", None):
                self.assertIsNone(G.gate_reason(t, cat, 3, 3), (t, cat))

    def test_investigation_words(self):
        self.assertIsNone(G.gate_reason("유튜버 ○○, 마약 혐의 재판에 넘겨져", None, 3, 3))         # 재판에 넘겨 = 기소
        self.assertIsNotNone(G.gate_reason("배우 ○○ 항고소송", "문화", 3, 3))                      # 소송은 재판 단계
        self.assertIsNone(G.gate_reason("고소영, 블랙핑크 로제에게 선물 받았다", "문화", 3, 0))    # 고소영 ≠ 고소

    def test_notable_context_and_partial_words(self):
        for t in ["이 대통령, 공장 화재 사망자 애도", "정몽원 HL그룹 회장, 평택공장 사망사고 유족에 사과",
                  "배우 ○○ 운영 카페 화재로 직원 숨져", "배우 ○○ 부친, 교통사고로 별세", "수영 배우던 초등생 익사",
                  "전시회장 붕괴 1명 사망", "물류센터 화재 사망사고…관리감독 부실", "가을 산행 중 60대 추락사",
                  "포항 청하·송라 산불로 주민 1명 숨져"]:
            self.assertIsNotNone(G.gate_reason(t, "사회"), t)
        self.assertIsNotNone(G.gate_reason("유튜버 ○○ 촬영장 화재로 스태프 1명 사망", "문화", 3, 3))
        self.assertIsNotNone(G.gate_reason("태국 관광버스 추락…사고 사망자 발생", "국제", 3, 3))   # [강]만으로는 유명인 아님

    def test_notable_death_words(self):
        for t in ["○○ 전 대통령, 교통사고로 서거", "가수 ○○, 교통사고로 작고", "국민MC ○○, 교통사고로 사망",
                  "배우 ○○ 피살…경찰 수사 착수", "Actor X dies in car crash"]:
            self.assertIsNone(G.gate_reason(t, "사회"), t)
        self.assertIsNotNone(G.gate_reason("작고 귀여운 강아지 교통사고 사망", "사회"))

    def test_dead_then_injured_count(self):   # B#8 기존 결함 — 「5명 사망 12명 부상」의 사망 = 5
        self.assertEqual(G.casualty_counts("스위스 버스 전복 5명 사망 12명 부상")[:2], (5, 12))
        self.assertIsNotNone(G.gate_reason("스위스 버스 전복 5명 사망 12명 부상", "국제"))


if __name__ == "__main__":
    unittest.main()
