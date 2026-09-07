"""A/B 평가가 단신의 편집 예외와 사실·상한 검사를 구분하는지 검증한다."""
import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("summary_ab_eval", ROOT / "shared/summary_ab_eval.py")
EVALUATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EVALUATOR)

SOURCE = "우체국은 새 창구를 연다. 이용 요금은 100원이다."


def digest(meta='', free=None, ig=None, th=None):
    free = SOURCE if free is None else free
    ig = '📮 우체국에 새 창구가 생긴다\n\n🔎 우체국이 새 창구를 연다.\n\n📍 이용 요금은 100원이다.\n\n⚡ 시험매체 / 2026.09.07.' if ig is None else ig
    th = '우체국 새 창구의 이용 요금은 100원이다\n\n📍 우체국이 새 창구를 연다.\n\n⚡ 시험매체 / 2026.09.07.' if th is None else th
    return f'''---
{meta}title: "우체국 창구 개설"
reader: "창구 이용자"
emotion: "관심"
hook: "새 창구"
thumb_scene: "창구"
thumb_dispatch: "AG-01 LGT01"
bias: "N/A"
tags: "해당 없음"
---
# 📮 우체국에 새 창구가 생긴다
## 🧷 분류
정보
## 📰 Fact
- {SOURCE}
## 🔎 Inference
추론 없음.
## 🧭 다각도
추가 쟁점 없음.
## 🛠 활용
안내
## 📦 콘텐츠 초안
### [자유요약 — 약 N자]
```text
{free}
```
📊 편향: N/A
### [IG — 약 N/800자]
```text
{ig}
```
📊 편향: N/A
### [Thread — 약 N/430자]
```text
{th}
```
📊 편향: N/A
### 💡 이 기사의 시사점
새 창구의 이용 요금은 100원이다.
'''


BRIEF = 'summary_mode: "brief_complete"\nsummary_reason: "완결 본문에서 개설과 이용 요금을 모두 반영했다."\n'


class SummaryAbQualityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'B1.md'

    def evaluate(self, text, source=SOURCE):
        self.path.write_text(text, encoding='utf-8')
        return EVALUATOR.eval_run(str(self.path), source)

    def test_explicit_brief_waives_only_length_and_pin_minimums(self):
        result = self.evaluate(digest(BRIEF))
        self.assertTrue(result['L_brief_exception'])
        self.assertEqual(result['summary_mode'], 'brief_complete')
        self.assertTrue(all(result[k] for k in ('L1_free_ok', 'L2_ig_ok', 'L3_th_ok', 'L4_pins_ok')))
        self.assertEqual(result['HARD_FAILS'], [])

    def test_short_source_or_missing_source_does_not_grant_exception(self):
        for source in (SOURCE, ''):
            with self.subTest(source=source):
                result = self.evaluate(digest(), source)
                self.assertFalse(result['L_brief_exception'])
                self.assertFalse(any(result[k] for k in ('L1_free_ok', 'L2_ig_ok', 'L3_th_ok', 'L4_pins_ok')))

    def test_invalid_or_unsubstantiated_mode_retains_standard_gates(self):
        for meta in ('summary_mode: "brief_complete"\n',
                     BRIEF + 'summary_mode: "standard"\n',
                     BRIEF.replace('brief_complete', 'brief')):
            with self.subTest(meta=meta):
                result = self.evaluate(digest(meta))
                self.assertFalse(result['L_brief_exception'])
                self.assertFalse(result['L2_ig_ok'])

    def test_empty_prose_does_not_pass_as_brief(self):
        for changes in ({'free': ''}, {'ig': '제목\n⚡ 시험매체 / 2026.09.07.'},
                        {'th': '제목\n⚡ 시험매체 / 2026.09.07.'}):
            with self.subTest(changes=changes):
                result = self.evaluate(digest(BRIEF, **changes))
                self.assertFalse(result['L_brief_exception'])
                self.assertTrue(result['HARD_FAILS'])

    def test_brief_preserves_upper_bounds_and_fact_candidates(self):
        th = '우체국의 요금 안내\n\n📍 이용 요금은 9000원이다. ' + '안내 내용을 전했다. ' * 60 + '\n\n⚡ 시험매체 / 2026.09.07.'
        ig = '📮 우체국의 요금 안내\n\n🔎 우체국이 새 창구를 연다.\n\n' + '\n\n'.join(['📍 이용 요금은 100원이다.'] * 7) + '\n\n⚡ 시험매체 / 2026.09.07.'
        result = self.evaluate(digest(BRIEF, ig=ig, th=th))
        self.assertTrue(result['L_brief_exception'])
        self.assertFalse(result['L3_th_ok'])
        self.assertFalse(result['L4_pins_ok'])
        self.assertGreater(result['L_over']['th'], 0)
        self.assertTrue(result['F1_num_candidates'])
        self.assertTrue(any(f.startswith('L3 ') for f in result['HARD_FAILS']))

    def test_brief_does_not_hide_fact_coverage_gaps(self):
        result = self.evaluate(digest(BRIEF, free='우체국이 새 창구를 연다.'))
        self.assertTrue(result['L_brief_exception'])
        self.assertGreater(result['R5_factcov_missing'], 0)

    def test_standard_thresholds_still_apply(self):
        free = '우체국은 새 창구를 연다. ' * 60
        ig = '📮 우체국 창구 소식\n🔎 우체국이 새 창구를 연다.\n' + '\n'.join(['📍 ' + '새 창구를 안내했다. ' * 13] * 4)
        th = '우체국 창구 소식\n' + '\n'.join(['📍 ' + '새 창구를 안내했다. ' * 10] * 3)
        result = self.evaluate(digest(free=free, ig=ig, th=th))
        self.assertFalse(result['L_brief_exception'])
        self.assertTrue(all(result[k] for k in ('L1_free_ok', 'L2_ig_ok', 'L3_th_ok', 'L4_pins_ok')))

    def test_judge_packet_explains_exception_without_certifying_quality(self):
        self.evaluate(digest(BRIEF))
        EVALUATOR.judge_packet(self.temp.name, {'B1': str(self.path)})
        packet = (Path(self.temp.name) / 'judge/B1.txt').read_text(encoding='utf-8')
        self.assertIn('편집 판단·사실 검증 완료 인증 아님', packet)
        self.assertIn('상한 430', packet)
        self.assertNotIn('목표 850~1000', packet)
        self.evaluate(digest())
        EVALUATOR.judge_packet(self.temp.name, {'A1': str(self.path)})
        packet = (Path(self.temp.name) / 'judge/A1.txt').read_text(encoding='utf-8')
        self.assertIn('목표 850~1000', packet)


if __name__ == '__main__':
    unittest.main()
