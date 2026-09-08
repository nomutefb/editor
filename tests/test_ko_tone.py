"""한국어 결 정본·측정기 회귀 — 정본 구간 추출·프로필 비대칭·스캐너 정밀도(허용목록)·윤문 6축 격 하락 대조. 모델 호출 0."""
import os
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "shared"))
import ko_tone_scan as kts  # noqa: E402


def _block(profile):
    return subprocess.run(["bash", "-c", "source shared/inject_guidelines.sh; guidelines_block %s" % profile],
                          cwd=ROOT, capture_output=True, text=True).stdout


class RulesFile(unittest.TestCase):
    def test_sections_and_profile_asymmetry(self):
        txt = (ROOT / "shared" / "ko_tone_rules.md").read_text(encoding="utf-8")
        for sec in ("COMMON", "NEWS-CAP", "POLISH"):
            self.assertEqual(txt.count("KO-TONE:%s-START" % sec), 1)
            self.assertEqual(txt.count("KO-TONE:%s-END" % sec), 1)
        self.assertEqual(txt.count("INJECT-SKIP-START"), txt.count("INJECT-SKIP-END"))
        card, summ = _block("card"), _block("summary")
        self.assertIn("[윤문 추가축 — 카드 초고", card)          # 카드 = 윤문체
        self.assertNotIn("기사체 보존이 위 규칙의 상한선", card)   # 카드 = 기사체 상한선 미적용
        self.assertIn("기사체 보존이 위 규칙의 상한선", summ)      # 요약 = 상한선
        self.assertNotIn("[윤문 추가축 — 카드 초고", summ)         # 요약 = 윤문 추가축 제외
        for b in (card, summ):
            self.assertIn("[한국어 결 — AI 번역투 소거(공용 문장축)]", b)
            self.assertNotIn("[미채택 · 근거", b)                  # 사람용 절 미주입

    def test_tone_block_extracts_common_only(self):
        r = subprocess.run(["bash", "-c", 'source shared/tone_block.sh; printf "%s\\n---\\n%s\\n---\\n%s" "$TONE_BLOCK" "$TONE_BLOCK_SENT" "$TONE_VER"'],
                           cwd=ROOT, capture_output=True, text=True)
        blk, sent, ver = r.stdout.split("\n---\n")
        self.assertTrue(blk.startswith("[한국어 결 — AI 번역투 소거(공용 문장축)]"))
        self.assertNotIn("기사체 보존", blk)
        self.assertIn("- [리듬]", blk)
        self.assertNotIn("- [리듬]", sent)
        self.assertTrue(re.fullmatch(r"[0-9a-f]{8}", ver.strip()), ver)


class Scanner(unittest.TestCase):
    def test_rules_hit_and_allowlists(self):
        t = ("전략적 중요성을 가지고 있다. 법적 조치를 검토하는 것으로 파악됐다. 사용자들은 이 기능들을 자주 쓴다. "
             "전문가들은 환경 요인을 꼽는다. 누적 적자가 컸다. 사용자에게 있어 속도는 중요하다. "
             "\"정말 특별한 저녁이었다\"고 했다. 정말 큰 문제다. 해결할 수 있는 방법이 없다. 합의가 이루어졌다. "
             "문제를 추가하는 것은 도움이 된다. 사회에 있어서는 안 될 일이다. 접수된 것은 22일이었다.")
        h = kts.scan(t)
        self.assertEqual(h["S1"], 1)      # 전략적 (법적=개념어 · 누적=명사 제외)
        self.assertEqual(h["S7"], 1)      # 사용자에게 있어 ('있어서는 안' 제외)
        self.assertEqual(h["F1"], 1)      # 인용 안 '정말' 제외
        self.assertEqual(h["S5"], 1)
        self.assertEqual(h["A3"], 2)      # 가지고 있다 · 이루어졌다
        self.assertEqual(h["S4"], 1)      # 것으로 파악·분열문 제외
        self.assertEqual(h["S3"], 2)      # 사용자들·기능들
        self.assertEqual(h["S3n"], 1)     # 전문가들 = 기사 주체
        self.assertGreaterEqual(kts.score(t), 5)

    def test_clean_news_text_scores_zero(self):
        t = ("7일 오후 7시께 중국 네이멍구자치구의 한 자동차 주행 시험장에서 트럭의 제동장치가 고장 났다. "
             "밀려 내려온 트럭이 승합차를 덮쳤고, 승합차에 타고 있던 5명이 숨진 것으로 집계됐다. 당국은 원인을 조사하고 있다.")
        self.assertEqual(kts.score(t), 0)

    def test_lane_text_picks_digest_blocks(self):
        md = "---\ntitle: x\n---\n### [자유요약 — 약 100자]\n```text\n본문 A.\n```\n### [IG — 1/800자]\n```text\n본문 B.\n```\n### 💡 이 기사의 시사점\n시사 C.\n"
        self.assertEqual(kts.lane_text(md), "본문 A.\n본문 B.\n시사 C.")


class PolishGuard(unittest.TestCase):
    def test_register_drop_rejected(self):
        """6축 ⓕ: 한자어→고유어 쌍이 원문에서 줄고 후보에서 늘면 기각 — summary_polish.sh 파이썬 검증기의 동일 술어."""
        pairs = [('삭제', '지울'), ('담당', '맡')]
        orig = "기록을 삭제한 담당자는 답하지 않았다."
        cand = "기록을 지울 맡은 이는 답하지 않았다."
        drop = [f'{a}→{b}' for a, b in pairs if orig.count(a) > cand.count(a) and cand.count(b) > orig.count(b)]
        self.assertEqual(drop, ['삭제→지울', '담당→맡'])
        src = (ROOT / "shared" / "summary_polish.sh").read_text(encoding="utf-8")
        self.assertIn("격 하락(", src)
        self.assertIn('SUMMARY_POLISH:-0', src)   # 기본 OFF · 조건부 없음(운영자 260908)
        self.assertNotIn("auto", src.split("summary_polish()")[1][:400])


if __name__ == "__main__":
    unittest.main()
