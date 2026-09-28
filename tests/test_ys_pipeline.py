"""유튜브 숏폼(ys) 파이프 — 형식 게이트·진행률·자막 분할·그림 강하·문체 구간 격리(LLM·네트워크 0)."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github' / 'scripts'))
import ys_plan  # noqa: E402
import ys_progress  # noqa: E402


def _raw(n_scenes=6, report_len=600, **over):
    j = {
        'title': '애쓸수록 꼬이는 이유', 'one': '쥔 손을 펴야 풀린다', 'short_title': '애쓸수록 꼬인다',
        'report_md': '# 제목\n' + '가' * report_len,
        'fixes': [{'from': '영력의 법칙', 'to': '노력 역전의 법칙', 'why': '쿠에'}],
        'verify': ['널빤지 예시 출처'],
        'infographic': {'kicker': '노력 역전', 'title': '애쓸수록 꼬이는 인생,\n쥔 손을 펴야 풀린다', 'accent': '쥔 손을 펴야',
                        'panels': [{'no': '01', 'kick': 'k', 'head': '의지는 상상을\n이기지 못한다', 'body': 'b', 'src': 's'}],
                        'table': {'title': '', 'cols': ['a', 'b'], 'rows': [['1', '2', '3']]}},
        'scenes': [{'tag': f'{i}', 'big': '큰 글자', 'head': '보조', 'chips': ['칩'], 'vo': '나레이션 문장이에요.', 'img': 'a fist'}
                   for i in range(n_scenes)],
    }
    j.update(over)
    return j


class Plan(unittest.TestCase):
    def test_extract_json_fence_raw_and_missing(self):
        j = _raw()
        self.assertEqual(ys_plan.extract_json('설명\n```json\n' + json.dumps(j, ensure_ascii=False) + '\n```')['title'], j['title'])
        self.assertEqual(ys_plan.extract_json('앞말 ' + json.dumps(j, ensure_ascii=False) + ' 뒷말')['title'], j['title'])
        self.assertIsNone(ys_plan.extract_json('JSON 없음 {"a":1}'))

    def test_normalize_gates(self):
        with self.assertRaises(ValueError):
            ys_plan.normalize(_raw(report_len=10), 60)      # 보고서 너무 짧음 = 소리나는 실패
        with self.assertRaises(ValueError):
            ys_plan.normalize(_raw(n_scenes=2), 60)         # 장면 부족
        plan, report = ys_plan.normalize(_raw(), 60)
        self.assertEqual(len(plan['scenes']), 6)
        self.assertTrue(report.startswith('# 제목'))
        self.assertEqual(plan['infographic']['accent'], '쥔 손을 펴야')   # 제목 안에 있는 강조만 살린다
        self.assertEqual(plan['infographic']['table']['rows'], [['1', '2']])   # 열 수에 맞춰 자름
        bad = ys_plan.normalize(_raw(infographic={'title': 'X', 'accent': '없는말'}), 60)[0]
        self.assertEqual(bad['infographic']['accent'], '')

    def test_ai_voice_pick_only_from_candidates(self):
        good = 'AbCdEfGhIjKlMnOpQrSt'
        p1, _ = ys_plan.normalize(_raw(voice_id=good, voice_why='차분한 톤'), 60, [good])
        self.assertEqual((p1['voice_id'], p1['voice_why']), (good, '차분한 톤'))
        p2, _ = ys_plan.normalize(_raw(voice_id='ZZZZZZZZZZZZZZZZZZZZ'), 60, [good])   # 후보 밖 = 환각 → 버림
        self.assertNotIn('voice_id', p2)
        blk = ys_plan.voices_block([{'id': good, 'name': 'KO 민준', 'gender': 'male', 'lang': 'ko', 'desc': '차분'}, {'id': 'bad'}])
        self.assertIn(good, blk)
        self.assertNotIn('| bad', blk)
        self.assertEqual(ys_plan.voices_block([]), '')

    def test_lines_cap_keeps_one_break(self):
        self.assertEqual(ys_plan._lines('가\n나\n다', 10), '가\n나 다')

    def test_prompt_block_budget_and_cut(self):
        meta = {'title': 't', 'channel': 'c', 'uploaded': '2026-09-27', 'dur': 936}
        tr = {'src': 'subs-auto', 'rows': [{'s': 0, 't': '문장'}, {'s': 65, 't': '다음'}]}
        b = ys_plan.prompt_block(meta, tr, 60)
        self.assertIn('장면 6~7개', b)
        self.assertIn('나레이션 총량 ≈ 300자', b)
        self.assertIn('[01:05] 다음', b)
        self.assertIn('자동 생성 자막', b)
        old = ys_plan.LLM_MAX
        try:
            ys_plan.LLM_MAX = 12
            self.assertIn('절단', ys_plan.prompt_block(meta, {'rows': [{'s': i, 't': '가나다라'} for i in range(9)]}, 45))
        finally:
            ys_plan.LLM_MAX = old


class Progress(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.old = ys_progress.LOCAL
        ys_progress.LOCAL = os.path.join(self.tmp, 'p.json')
        self.env = {k: os.environ.pop(k) for k in ('R2_BUCKET', 'R2_ACCOUNT_ID') if k in os.environ}

    def tearDown(self):
        ys_progress.LOCAL = self.old
        os.environ.update(self.env)

    def doc(self):
        with open(ys_progress.LOCAL, encoding='utf-8') as f:
            return json.load(f)

    def test_flow_and_pct(self):
        ys_progress.main(['x', 'id1', 'init', 'img=none'])
        d = self.doc()
        self.assertEqual([s['k'] for s in d['steps']], ['meta', 'stt', 'plan', 'voice', 'img', 'render', 'upload'])
        self.assertEqual(d['steps'][4]['st'], 'skip')                     # 그림 없음 = 분모에서 빠짐
        ys_progress.main(['x', 'id1', 'meta', 'done', '15분 36초'])
        ys_progress.main(['x', 'id1', 'stt', 'done'])
        ys_progress.main(['x', 'id1', 'plan', 'run', '쓰는 중', 'p=0.5'])
        d = self.doc()
        self.assertEqual(d['pct'], round(100 * (5 + 15 + 15) / 85))       # 가중 = 완료 20 + 진행 절반 15 / 85
        self.assertEqual(d['steps'][2]['note'], '쓰는 중')
        ys_progress.main(['x', 'id1', 'fail', '인사이트 정리 실패'])
        d = self.doc()
        self.assertEqual((d['state'], d['steps'][2]['st']), ('fail', 'fail'))
        self.assertLess(d['pct'], 100)

    def test_finish_is_100(self):
        ys_progress.main(['x', 'id2', 'init', 'img=codex'])
        ys_progress.main(['x', 'id2', 'finish'])
        d = self.doc()
        self.assertEqual((d['state'], d['pct']), ('done', 100))
        self.assertTrue(all(s['st'] == 'done' for s in d['steps']))


class RenderHelpers(unittest.TestCase):
    def test_split_caption(self):
        import ys_render
        text = '장자 속 백정 포정은 칼을 억지로 밀어 넣지 않았어요 수십 년 익힌 손이 빈틈을 따라갔죠'
        parts = ys_render.split_caption(text, 1.0, 9.0)
        self.assertGreater(len(parts), 1)
        self.assertTrue(all(len(t) <= ys_render.CAP_MAX for _a, _z, t in parts))
        self.assertEqual(' '.join(t for _a, _z, t in parts), text)
        self.assertEqual((parts[0][0], parts[-1][1]), (1.0, 9.0))
        self.assertTrue(all(a < z for a, z, _t in parts))
        self.assertEqual(ys_render.split_caption('짧은 문장', 0, 1), [(0, 1, '짧은 문장')])

    def test_fit_caps(self):
        import ys_render
        self.assertEqual(ys_render.fit('가나', 150), 150)
        self.assertLess(ys_render.fit('가' * 12, 150), 150)

    def test_fonts_are_the_three_keys(self):
        import ys_render
        self.assertEqual(set(ys_render.FONTS), {'pretendard', 'gothic', 'barun'})


class Tts(unittest.TestCase):
    def test_sentences(self):
        import ys_tts
        self.assertEqual(ys_tts.sentences('그럼 힘을 빼면 될까요? 어깨는 다시 굳어요. 끝'), ['그럼 힘을 빼면 될까요?', '어깨는 다시 굳어요.', '끝'])


class Images(unittest.TestCase):
    def test_no_r2_falls_back_to_text(self):
        d = tempfile.mkdtemp()
        plan = os.path.join(d, 'plan.json')
        json.dump({'scenes': [{'img': 'a', 'head': 'h'}]}, open(plan, 'w'))
        env = {k: v for k, v in os.environ.items() if k not in ('R2_BUCKET', 'R2_ACCOUNT_ID')}
        env['PYTHONPATH'] = str(ROOT / '.github' / 'scripts')
        r = subprocess.run([sys.executable, str(ROOT / '.github/scripts/ys_images.py'), 'idx', plan, os.path.join(d, 'img')],
                           capture_output=True, text=True, env=env, cwd=d)
        self.assertEqual(r.returncode, 0, r.stderr)
        j = json.load(open(os.path.join(d, 'img', 'img.json'), encoding='utf-8'))
        self.assertEqual(j['used'], 0)
        self.assertIn('글자 화면', j['note'])


class ToneIsolation(unittest.TestCase):
    """ys 전용 문체 구간(im-not-ai v2.8)은 ys_make.sh 만 읽는다 — 뉴스 요약·카드·SNS 주입엔 새지 않는다."""

    def test_ys_block_extracted_and_isolated(self):
        rules = (ROOT / 'shared' / 'ko_tone_rules.md').read_text(encoding='utf-8')
        s, e = rules.find('KO-TONE:YS-START'), rules.find('KO-TONE:YS-END')
        self.assertTrue(0 < s < e)
        block = rules[s:e]
        self.assertIn('단정으로 바꾸거나', block)
        before = rules.rfind('INJECT-SKIP-START', 0, s)
        self.assertNotIn('profile=', rules[before:rules.find('-->', before)])   # 프로필 무관 전면 스킵
        self.assertLess(rules.find('INJECT-SKIP-END', e), rules.find('\n', rules.find('INJECT-SKIP-END', e)) + 1)
        r = subprocess.run(['bash', '-c', 'source shared/tone_block.sh; printf "%s" "$TONE_BLOCK"'], cwd=ROOT,
                           capture_output=True, text=True)
        self.assertNotIn('유튜브 숏폼', r.stdout)
        self.assertIn('KO-TONE:YS', (ROOT / '.github/scripts/ys_make.sh').read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
