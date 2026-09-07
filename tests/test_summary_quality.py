"""Exercise summary repair boundaries with complete digest/candidate files, without model calls."""
import contextlib
import io
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "shared"))
import digest_guard as dg
import fact_guard as fg


def post(size, facts="", title="소식을 전했다", source="⚡ 매체 / 2026.09.07."):
    prefix = title + "\n🔎 " + facts
    suffix = "\n" + source
    # Length padding is only fixture data; it keeps the real assertions on the repair boundaries.
    return prefix + "가" * (size - dg._clen(prefix + suffix)) + suffix


def digest(free, ig, thread, fields="", extra=""):
    return ("---\ntitle: 원문 제목\n" + fields + "---\n" + extra +
            "\n### [자유요약]\n```text\n" + free + "\n```\n" +
            "\n### [IG — 800/800자]\n```text\n" + ig + "\n```\n" +
            "\n### [Thread — 430/430자]\n```text\n" + thread + "\n```\n")


BRIEF = 'summary_mode: brief_complete\nsummary_reason: "전문 확인 후 발표 내용과 당사자 입장을 모두 담음"\n'


class SummaryRepairTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path = Path(tmp.name) / "digest.md"
        self.candidate = Path(tmp.name) / "candidate.md"

    def check(self, raw):
        self.path.write_text(raw, encoding="utf-8")
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            dg.repair_check(str(self.path))
        return output.getvalue()

    def splice(self, raw, candidate):
        self.path.write_text(raw, encoding="utf-8")
        self.candidate.write_text(candidate, encoding="utf-8")
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            dg.splice(str(self.path), str(self.candidate))
        return self.path.read_text(encoding="utf-8"), output.getvalue()

    def test_short_output_alone_does_not_certify_complete_source(self):
        raw = digest("당사자가 결혼을 발표했다.", post(150), post(100))
        self.assertIn("REPAIR under", self.check(raw))
        self.assertFalse(dg._brief_complete(raw))

    def test_explicit_brief_waives_lower_targets_and_lint_only(self):
        raw = digest("당사자가 결혼을 발표했다.", post(150), post(100), BRIEF)
        self.assertTrue(dg._brief_complete(raw))
        self.assertTrue(self.check(raw).startswith("OK "))
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            dg.lint(str(self.path))
        self.assertNotIn("완충 하한", output.getvalue())

    def test_invalid_or_ambiguous_brief_defaults_to_standard(self):
        for fields in (
            "summary_mode: brief_complete\n",
            'summary_mode: brief_complete\nsummary_reason: ""\n',
            "summary_mode: brief_complete\nsummary_reason: null\n",
            "summary_mode: brief_complete\nsummary_reason: >\n  짧은 기사\n",
            'summary_mode: brief_complete\nsummary_reason: "한 줄\\n다음 줄"\n',
            BRIEF + "summary_mode: standard\n",
            BRIEF + "summary_reason: 다른 이유\n",
            BRIEF.replace("brief_complete", "brief"),
        ):
            with self.subTest(fields=fields):
                raw = digest("당사자가 결혼을 발표했다.", post(150), post(100), fields)
                self.assertFalse(dg._brief_complete(raw))
                self.assertIn("REPAIR under", self.check(raw))

    def test_body_metadata_and_empty_blocks_cannot_request_brief(self):
        raw = digest("발표 내용을 담았다.", post(150), post(100), extra=BRIEF)
        self.assertIn("REPAIR under", self.check(raw))
        for free, ig, thread in (("", post(150), post(100)),
                                 ("발표 내용을 담았다.", "제목\n⚡ 매체", post(100))):
            with self.subTest(free=free, ig=ig):
                self.assertFalse(dg._brief_complete(digest(free, ig, thread, BRIEF)))

    def test_quoted_frontmatter_allows_yaml_comments_and_preserves_hash_in_value(self):
        for fields in (
            'summary_mode: "brief_complete" # 단문 예외\nsummary_reason: "전문 # 확인 완료" # 근거\n',
            "summary_mode: 'brief_complete' # 단문 예외\nsummary_reason: '전문 # 확인 완료' # 근거\n",
        ):
            with self.subTest(fields=fields):
                raw = digest("발표 내용을 담았다.", post(150), post(100), fields)
                self.assertTrue(dg._brief_complete(raw))
                self.assertEqual(dg._frontmatter_scalar(raw, "summary_reason"), "전문 # 확인 완료")
                self.assertTrue(self.check(raw).startswith("OK "))

    def test_quoted_frontmatter_rejects_suffix_other_than_separated_comment(self):
        for value in ('"brief_complete" extra', '"brief_complete"#comment',
                      "'brief_complete' extra", "'brief_complete'#comment"):
            with self.subTest(value=value):
                fields = "summary_mode: " + value + '\nsummary_reason: "전문 확인"\n'
                raw = digest("발표 내용을 담았다.", post(150), post(100), fields)
                self.assertFalse(dg._brief_complete(raw))
                self.assertIn("REPAIR under", self.check(raw))

    def test_short_summary_never_waives_overflow(self):
        for fields in ("", BRIEF):
            for ig, th, target in ((post(801), post(400), "IG:over"),
                                   (post(650), post(510), "Thread:over")):
                with self.subTest(fields=fields, target=target):
                    result = self.check(digest("발표 내용이다.", ig, th, fields))
                    self.assertIn("REPAIR over", result)
                    self.assertIn(target, result)

    def test_newline_only_hard_overflow_can_be_repaired_without_growing_text(self):
        ig, th = post(650), post(400)
        overflowing = th.replace("\n", "\n" * 70)
        self.assertEqual(dg._clen(overflowing), 400)
        self.assertGreater(dg._clen_hard(overflowing), 500)
        raw = digest("가" * 900, ig, overflowing)
        self.assertIn("Thread:over", self.check(raw))
        result, log = self.splice(raw, digest("ignored", post(700), th))
        self.assertEqual(dg._blk(result, "Thread"), th, log)
        self.assertEqual(dg._blk(result, "IG"), ig, log)

    def test_repairing_one_underlength_block_preserves_healthy_sibling(self):
        ig, th = post(650), post(300)
        raw = digest("가" * 900, ig, th)
        candidate = digest("ignored", post(720), post(400))
        result, log = self.splice(raw, candidate)
        self.assertEqual(dg._blk(result, "IG"), ig, log)
        self.assertEqual(dg._blk(result, "Thread"), post(400), log)

    def test_brief_overflow_can_shrink_below_standard_target(self):
        raw = digest("당사자가 소식을 발표했다.", post(810), post(100), BRIEF)
        candidate = digest("ignored", post(150), post(120))
        result, log = self.splice(raw, candidate)
        self.assertEqual(dg._blk(result, "IG"), post(150), log)
        self.assertEqual(dg._blk(result, "Thread"), post(100), log)
        self.assertTrue(self.check(result).startswith("OK "))

    def test_brief_still_rejects_empty_body_or_candidate_overflow(self):
        raw = digest("당사자가 소식을 발표했다.", post(850), post(100), BRIEF)
        for invalid in ("소식을 전했다\n🔎\n⚡ 매체 / 2026.09.07.", post(810)):
            with self.subTest(candidate=invalid[:30]):
                result, log = self.splice(raw, digest("ignored", invalid, post(100)))
                self.assertEqual(result, raw, log)

    def test_single_digit_invention_and_existing_unsupported_body_are_rejected(self):
        for old_facts in ("", "7명이었다."):
            with self.subTest(old_facts=old_facts):
                raw = digest("단체방 구성원은 6명이었다." + "가" * 900,
                             post(500, old_facts), post(400))
                result, log = self.splice(raw, digest("ignored", post(650, "7명이었다."), post(400)))
                self.assertEqual(result, raw, log)
                self.assertIn("자유요약 본문에 없는 수치(7)", log)

    def test_supported_single_digit_can_be_added(self):
        raw = digest("단체방 구성원은 6명이었다." + "가" * 900, post(500), post(400))
        candidate = post(650, "단체방 구성원은 6명이었다.")
        result, log = self.splice(raw, digest("ignored", candidate, post(400)))
        self.assertEqual(dg._blk(result, "IG"), candidate, log)

    def test_only_free_summary_prose_can_ground_candidate_numbers(self):
        old_ig = post(500, title="88번 소식을 전했다")
        raw = digest("가" * 900 + "\n⚡ 매체 / 6일",
                     old_ig, post(400, "42명이었다."),
                     "id: 9\n", "## Fact\n99명이었다.\n")
        for number in ("9", "99", "2026", "88", "42", "6"):
            with self.subTest(number=number):
                candidate = post(650, number + "명이었다.", title="88번 소식을 전했다")
                result, log = self.splice(raw, digest("ignored", candidate, post(400)))
                self.assertEqual(result, raw, log)
                self.assertIn("자유요약 본문에 없는 수치", log)

    def test_unchanged_title_and_source_numbers_remain_allowed(self):
        old_ig = post(500, title="9일 전한 소식")
        new_ig = post(650, title="9일 전한 소식")
        raw = digest("가" * 900, old_ig, post(400))
        result, log = self.splice(raw, digest("ignored", new_ig, post(400)))
        self.assertEqual(dg._blk(result, "IG"), new_ig, log)

    def test_korean_numeric_scale_is_normalized_and_wrong_scale_rejected(self):
        for source, supported, invented in (
            ("예산은 1조2000억원이다.", "예산은 1.2조원이다.", "예산은 1.2억원이다."),
            ("지원금은 1만5000원이다.", "지원금은 15,000원이다.", "지원금은 15만원이다."),
        ):
            with self.subTest(source=source):
                raw = digest(source + "가" * 900, post(500), post(400))
                accepted = post(650, supported)
                result, log = self.splice(raw, digest("ignored", accepted, post(400)))
                self.assertEqual(dg._blk(result, "IG"), accepted, log)
                result, log = self.splice(raw, digest("ignored", post(650, invented), post(400)))
                self.assertEqual(result, raw, log)

    def test_title_source_and_disclaimer_are_preserved(self):
        raw = digest("가" * 900, post(500), post(400))
        for candidate in (post(650, title="바뀐 제목"),
                          post(650, source="⚡ 다른 매체 / 2026.09.07."),
                          post(650, "⚠️ 본문 내용은 면책한다.\n"),
                          post(650).replace("\n🔎", "\n⚠️ 본문 내용은 면책한다.\n🔎")):
            with self.subTest(candidate=candidate[:40]):
                result, log = self.splice(raw, digest("ignored", candidate, post(400)))
                self.assertEqual(result, raw, log)

    def test_standard_overflow_does_not_accept_overcut(self):
        raw = digest("가" * 900, post(850), post(400))
        result, log = self.splice(raw, digest("ignored", post(150), post(400)))
        self.assertEqual(result, raw, log)
        self.assertIn("과절단", log)

    def test_url_ids_and_dates_are_not_numerical_evidence(self):
        source = "구성원은 6명이다. [보도](https://example.test/2026/777?id=23)."
        self.assertEqual(fg.check(source, "구성원은 6명이다."), [])
        for value in ("2026", "777", "23"):
            with self.subTest(value=value):
                self.assertEqual(fg.check(source, value + "명이다."), [value])

    def test_url_ids_do_not_create_missing_numbers(self):
        summary = "구성원은 6명이다. https://example.test/news/999?id=24"
        cards = "구성원은 6명이다. [출처](https://example.test/news/778)"
        self.assertEqual(fg.coverage(summary, cards), [])
        self.assertEqual(fg.check(summary, cards), [])
        self.assertEqual(fg.coverage(summary, "구성원이 있었다."), ["6"])

    def test_markdown_labels_and_counts_around_bare_urls_remain_evidence(self):
        source = "[6명의 구성원](https://example.test/999). 2명 https://example.test/888 (3명)."
        self.assertEqual([v for v, _, _ in fg.tokens(source)], [6, 2, 3])
        self.assertEqual(fg.check(source, "6명, 2명, 3명이다."), [])


if __name__ == "__main__":
    unittest.main()
