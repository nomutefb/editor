"""Exercise the real extraction script offline; clipping must never look complete."""
import html
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / '.github/scripts/fetch_article.sh'
NOTICE = '[원문 추출 일부 생략]'


class ArticleExcerptTests(unittest.TestCase):
    def extract(self, paragraphs):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture = root / 'article.html'
            fixture.write_text('<html><head><title>Fixture</title></head><body>'
                               + ''.join('<p>' + html.escape(p) + '</p>' for p in paragraphs)
                               + '</body></html>', encoding='utf-8')
            curl = root / 'curl'
            curl.write_text('''#!/usr/bin/env python3
import os
from pathlib import Path
import sys
args = sys.argv[1:]
Path(args[args.index('-D') + 1]).write_text('Content-Type: text/html; charset=utf-8\\r\\n')
Path(args[args.index('-o') + 1]).write_bytes(Path(os.environ['ARTICLE_FIXTURE']).read_bytes())
with open(os.environ['ARTICLE_FETCH_LOG'], 'a') as log:
    log.write('fetch\\n')
''', encoding='utf-8')
            curl.chmod(0o755)
            calls = root / 'fetch.log'
            env = dict(os.environ, PATH=str(root) + os.pathsep + os.environ['PATH'],
                       ARTICLE_FIXTURE=str(fixture), ARTICLE_FETCH_LOG=str(calls))
            result = subprocess.run(['bash', str(SCRIPT), 'https://fixture.invalid/story'],
                                    env=env, text=True, capture_output=True, timeout=10, check=True)
            self.assertEqual(calls.read_text(), 'fetch\n', 'No extra source requests are needed')
            return result.stdout

    def expected(self, paragraphs):
        # Tag stripping leaves the short page title on the first body line in the existing extractor.
        return '제목: Fixture\n본문:\nFixture ' + '\n'.join(paragraphs)

    def test_complete_article_is_unchanged(self):
        paragraphs = [('오늘 확인된 사실과 당사자 설명을 기사에 그대로 전달한다. ' * 5).strip(),
                      ('앞선 주장에 대한 반론과 아직 확정되지 않은 조건도 함께 알린다. ' * 5).strip()]
        self.assertEqual(self.extract(paragraphs), self.expected(paragraphs) + '\n')

    def test_more_than_forty_lines_marks_omission_without_changing_selection(self):
        paragraphs = [f'{i:02d}번 사실에 관하여 확인된 내용을 독자에게 구체적으로 전달한다.' for i in range(41)]
        output = self.extract(paragraphs)
        excerpt, notice = output.split('\n\n' + NOTICE)
        self.assertEqual(excerpt, self.expected(paragraphs[:40]))
        self.assertNotIn(paragraphs[40], output)
        self.assertIn('본문 40줄', notice)
        self.assertNotIn('6,000자', notice)
        self.assertIn('원문이 짧거나 끝났다는 뜻이 아니며', notice)
        self.assertIn('원문 확인이 필요함', notice)

    def test_more_than_six_thousand_characters_marks_omission(self):
        paragraphs = ['기사에 실린 확인된 내용을 원문 순서대로 전달한다. ' * 250]
        output = self.extract(paragraphs)
        excerpt, notice = output.split('\n\n' + NOTICE)
        self.assertEqual(excerpt, self.expected(paragraphs)[:6000])
        self.assertEqual(len(excerpt), 6000)
        self.assertIn('6,000자', notice)
        self.assertNotIn('본문 40줄', notice)

    def test_exact_limits_are_not_reported_as_clipping(self):
        paragraphs = [f'{i:02d}번 사실에 관하여 확인된 내용을 독자에게 구체적으로 전달한다.' for i in range(40)]
        self.assertEqual(self.extract(paragraphs), self.expected(paragraphs) + '\n')
        prefix_length = len(self.expected(['']))
        paragraphs = ['가' * (6000 - prefix_length)]
        self.assertEqual(len(self.expected(paragraphs)), 6000)
        self.assertEqual(self.extract(paragraphs), self.expected(paragraphs) + '\n')

    def test_both_limits_reported_with_one_notice(self):
        paragraphs = [f'{i:02d}번 ' + '확인된 기사 내용을 전달한다. ' * 20 for i in range(41)]
        output = self.extract(paragraphs)
        self.assertEqual(output.count(NOTICE), 1)
        self.assertIn('본문 40줄, 6,000자', output)

    def test_thin_body_remains_empty_for_existing_fallback(self):
        self.assertEqual(self.extract(['짧은 안내 문구만 있다.']), '')


if __name__ == '__main__':
    unittest.main()
