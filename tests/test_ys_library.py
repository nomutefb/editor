"""유튜브 숏폼(ys) 연출 도서관 · 장면 유형 · 대본 다듬기 2단 · 감독 2콜(운영자 260929) — 실제로 돌려서 단언한다(네트워크·모델 0).

  «라이브러리는 도서관 · 색인으로 구상 → 고른 것만 참조 · 그게 효과적이라고 판단하는 감독 알고리즘이 중요»
  «오퍼스가 1차로 다듬고 · 다른 오퍼스가 원고와 다듬은 걸 교차로 확인하며 2차 · 오퍼스 하이가 각각»
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github' / 'scripts'))
import ys_grok_plan as gp  # noqa: E402
import ys_images  # noqa: E402
import ys_lib  # noqa: E402
import ys_plan  # noqa: E402

WF = ROOT / '.github/workflows/ys-make.yml'


def scene(kind, hero, img, ids=(), people='none', vo='나레이션 문장입니다 충분히 길게 씁니다'):
    return {'tag': 't', 'big': 'b', 'head': 'h', 'vo': vo, 'img': img, 'motion': 'slow push-in', 'kind': kind, 'hero': hero,
            'people': people, 'ids': list(ids)}


DRAFT = {'title': '제목', 'one': '한 줄', 'report_md': '# 보고서\n' + '본문 ' * 200, 'short_title': '숏폼',
         'hero': {'en': 'Korean man in his late 20s, grey hoodie, messy black hair', 'why': 'x'},
         'scenes': [scene('person', True, 'the protagonist frozen over a phone at 2am', ['EM-17', 'CD-06']),
                    scene('subject', True, 'an hourglass cracking on a bare desk', ['VR-17', 'ZZ-99']),
                    scene('situation', False, 'one monitor glowing in a dark office', ['SG-09'], people='others'),
                    scene('situation', False, 'a coat on an empty chair at night', ['SG-09']),
                    scene('person', True, 'the protagonist exhales, shoulders dropping', ['DF-30'])]}


class Library(unittest.TestCase):
    """도서관 = 색인(번호·이름·언제)만 보이고, 고른 번호의 원문만 꺼낸다."""

    def test_index_is_small_and_has_no_method_text(self):
        for kind, cap in (('scene', 20000), ('director', 26000)):
            idx = ys_lib.index(kind)
            self.assertTrue(idx.startswith('['), kind)
            self.assertLess(len(idx.encode()), cap, kind)                          # 색인 = 작다(도서관 전체 ≈ 860KB)
            self.assertNotIn('Gemini용 삽입 지시문', idx)                           # 방법 원문은 색인에 없다
        d = ys_lib.index('director')
        self.assertIn('S07 미디엄 클로즈업 — ', d)
        self.assertIn('CD-06 긴박·공포', d)                                         # 정서 배정표 = 감독 출발점
        for bad in ('S10 ', 'S12 ', 'M14 ', 'AN-23 ', 'AN-34 ', 'CD-10 '):           # 얼굴 초근접·크래시 줌·립싱크·돌아서기·미성년 표
            self.assertNotIn('\n' + bad, d, bad)
        self.assertNotIn('\nSG-01 ', ys_lib.index('scene'))                        # 칸 분할

    def test_fetch_only_picked_and_offered(self):
        raw = ys_lib.fetch(['M50', 'S07', 'M50', 'S10', 'ZZ-1'], 'director')
        heads = re.findall(r'^■ (\S+)', raw, re.M)
        self.assertEqual(heads, ['M50', 'S07'])                                    # 고른 순서 · 중복 1번 · 색인 밖(S10·지어낸 번호) 제외
        self.assertIn('영상 삽입 지시문: camera pushes in almost imperceptibly', raw)
        self.assertIn('추천 조합', raw)
        self.assertNotIn('GPT Image', raw)
        self.assertEqual(ys_lib.fetch([], 'director'), '')

    def test_fetch_hygiene(self):
        self.assertEqual(ys_lib.clean_en('he crouches low, no camera movement, cinematic look, she stops'),
                         "the subject crouches low, the subject stops")
        raw = ys_lib.fetch(['M01'], 'director')
        self.assertNotRegex(raw.split('영상 삽입 지시문')[1].split('\n')[0], r'(?i)no camera movement')

    def test_audit(self):
        self.assertEqual(ys_lib.audit(['EM-03', 'S07', 'ZZ-99', 'foo', 'EM-03', 'DF-02'], 'scene'), (['EM-03', 'DF-02'], ['S07', 'ZZ-99']))
        self.assertEqual(ys_lib.audit('EM-03', 'scene'), ([], []))                  # 목록 아님 = 빈 값(죽지 않는다)

    def test_missing_library_is_fail_soft(self):
        r = subprocess.run([sys.executable, str(ROOT / '.github/scripts/ys_lib.py'), 'index', 'director'], capture_output=True, text=True,
                           env=dict(os.environ, YS_LIB_DIR='/nonexistent'))
        self.assertEqual((r.returncode, r.stdout.strip()), (0, ''))


class SceneKinds(unittest.TestCase):
    """장면 유형(인물·피사체·상황) 정규화 · 빈 화면 판정 단일 원천."""

    def test_normalize_kinds_people_ids(self):
        plan, _ = ys_plan.normalize(json.loads(json.dumps(DRAFT)), 45)
        s = plan['scenes']
        self.assertEqual([x['kind'] for x in s], ['person', 'subject', 'situation', 'situation', 'person'])
        self.assertFalse(s[1]['hero'])                                               # 피사체 = 주인공 표시 떼어냄
        self.assertEqual(s[1]['ids'], ['VR-17'])
        self.assertEqual(s[1]['ids_bad'], ['ZZ-99'])                                 # 지어낸 번호 = 감사 기록
        self.assertEqual((s[2]['people'], s[3]['people']), ('others', 'none'))
        self.assertEqual(plan['kinds'], 'P2 S1 S2')
        self.assertEqual(plan['lib'], {'cited': 6, 'made_up': 1})

    def test_empty_frame(self):
        plan, _ = ys_plan.normalize(json.loads(json.dumps(DRAFT)), 45)
        self.assertEqual([ys_plan.empty_frame(plan, x) for x in plan['scenes']], [False, True, False, True, False])
        old = {'hero': {'en': 'x'}, 'scenes': [{'hero': True}, {'hero': False}]}      # 유형 없는 옛 판 = 주인공 없는 장면만 빈 화면
        self.assertEqual([ys_plan.empty_frame(old, x) for x in old['scenes']], [False, True])
        self.assertFalse(ys_plan.empty_frame({'scenes': []}, {'hero': False}))       # 주인공 없는 영상의 옛 판 = 사람이 나올 수 있다

    def test_legacy_output_without_kind(self):
        raw = json.loads(json.dumps(DRAFT))
        for x in raw['scenes']:
            x.pop('kind'), x.pop('ids'), x.pop('people')
        plan, _ = ys_plan.normalize(raw, 45)
        self.assertEqual([x['kind'] for x in plan['scenes']], ['person', 'person', 'subject', 'subject', 'person'])

    def test_board_marks_empty_panels(self):
        plan, _ = ys_plan.normalize(json.loads(json.dumps(DRAFT)), 45)
        b = ys_images.board_prompt(plan, plan['hero']['en'], 'portrait')['board']
        self.assertIn('Panel 2: empty of people, an hourglass', b)
        self.assertIn('Panel 3: one monitor', b)                                     # 다른 사람이 나오는 상황 = 표시 없음
        self.assertIn('Panel 4: empty of people, a coat', b)


class Merge(unittest.TestCase):
    """다듬은 대본 합치기 — 통과분만 교체 · 이탈 = 앞 판 무접촉 · 목소리 유지."""

    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
        (self.d / 'base.txt').write_text('noise ' + json.dumps(DRAFT, ensure_ascii=False), encoding='utf-8')
        plan, report = ys_plan.normalize(json.loads(json.dumps(DRAFT)), 45)
        plan['voice_id'], plan['voice_why'] = 'abcdefghijklmnop1234', '차분'
        ys_plan.write_out(str(self.d), plan, report)

    def test_merge_ok(self):
        ref = {'short_title': '다듬은 제목', 'scenes': [dict(x, vo=x['vo'] + ' 다듬음') for x in DRAFT['scenes']], 'notes': ['s1 · 훅'], 'report_md': 'IGNORED'}
        (self.d / 'r.txt').write_text(json.dumps(ref, ensure_ascii=False), encoding='utf-8')
        rc = ys_plan.merge(str(self.d / 'base.txt'), str(self.d / 'r.txt'), 45, str(self.d), str(self.d / 'full.json'), 'p1')
        self.assertEqual(rc, 0)
        p = json.loads((self.d / 'plan.json').read_text())
        self.assertEqual((p['short_title'], p['refine'], p['voice_id']), ('다듬은 제목', 'p1', 'abcdefghijklmnop1234'))
        self.assertTrue(p['scenes'][0]['vo'].endswith('다듬음'))
        self.assertEqual(p['refine_notes'], [{'pass': 'p1', 'notes': ['s1 · 훅']}])
        self.assertTrue((self.d / 'report.md').read_text().startswith('# 보고서'))    # 보고서 = 초안 그대로
        self.assertEqual(json.loads((self.d / 'full.json').read_text())['report_md'], DRAFT['report_md'])

    def test_merge_bad_keeps_previous(self):
        before = (self.d / 'plan.json').read_text()
        for bad in ('not json', json.dumps({'scenes': [scene('person', True, 'x')]}), json.dumps({'notes': []})):
            (self.d / 'r.txt').write_text(bad, encoding='utf-8')
            rc = ys_plan.merge(str(self.d / 'base.txt'), str(self.d / 'r.txt'), 45, str(self.d), str(self.d / 'full.json'), 'p1')
            self.assertEqual(rc, 1, bad[:30])
            self.assertEqual((self.d / 'plan.json').read_text(), before)
        self.assertFalse((self.d / 'full.json').exists())


def fake_claude(d, script):
    """가짜 claude — stdin 프롬프트를 파일로 남기고 script(파이썬 본문)가 정한 응답을 낸다."""
    b = d / 'bin'
    b.mkdir(exist_ok=True)
    (b / 'fake.py').write_text('import sys, json, os\nP = sys.stdin.read()\nn = len(os.listdir(sys.argv[1]))\n'
                               'open(os.path.join(sys.argv[1], f"{n:02d}.txt"), "w").write(P)\n' + script, encoding='utf-8')
    (d / 'calls').mkdir(exist_ok=True)
    (b / 'claude').write_text(f'#!/bin/sh\nexec {sys.executable} {b / "fake.py"} {d / "calls"}\n')
    os.chmod(b / 'claude', 0o755)
    return b


class Refine(unittest.TestCase):
    """대본 다듬기 2단 — 1차 = 초안 + 고른 번호 원문 · 2차 = 새 콜이 초안 ↔ 1차 교차 · 실패 단계 = 앞 판 유지."""

    def run_refine(self, script, passes='2'):
        d = Path(tempfile.mkdtemp())
        out = d / 'ys'
        out.mkdir()
        (d / 'raw.txt').write_text(json.dumps(DRAFT, ensure_ascii=False), encoding='utf-8')
        (d / 'meta.json').write_text(json.dumps({'title': '영상', 'channel': '채널', 'dur': 600}), encoding='utf-8')
        (d / 'tr.json').write_text(json.dumps({'src': 'subs', 'rows': [{'s': 0, 't': '전사 한 줄'}]}), encoding='utf-8')
        plan, report = ys_plan.normalize(json.loads(json.dumps(DRAFT)), 45)
        ys_plan.write_out(str(out), plan, report)
        b = fake_claude(d, script)
        env = dict(os.environ, PATH=f'{b}:{os.environ["PATH"]}', INLINE_TRIES='1', YS_REFINE=passes, YS_LEN='45', METER_OFF='1',
                   YS_RAW=str(d / 'raw.txt'), YS_META=str(d / 'meta.json'), YS_TR=str(d / 'tr.json'), YS_ID='')
        r = subprocess.run(['bash', str(ROOT / '.github/scripts/ys_refine.sh'), str(out)], cwd=ROOT, capture_output=True, text=True, env=env, timeout=120)
        calls = [p.read_text() for p in sorted((d / 'calls').iterdir())]
        rec = json.loads((out / 'refine.json').read_text())
        return r, calls, rec, json.loads((out / 'plan.json').read_text())

    OK = ('mark = "2차" if "[이번 차수] 2차" in P else "1차"\n'
          'j = json.loads(P.split("[초안 원고]\\n", 1)[1].split("\\n\\n[", 1)[0])\n'
          'for s in j["scenes"]:\n    s["vo"] = s["vo"] + " " + mark\n'
          'j["notes"] = [mark + " 메모"]\nprint(json.dumps(j, ensure_ascii=False))\n')

    def test_two_passes(self):
        r, calls, rec, plan = self.run_refine(self.OK)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual((rec['p1'], rec['p2']), ('ok', 'ok'), r.stdout + r.stderr)
        self.assertEqual(len(calls), 2)
        c1, c2 = calls
        self.assertIn('[이번 차수] 1차', c1)
        self.assertNotIn('\n\n[1차 다듬은 원고]\n', c1)                             # 블록 머리(지침 본문 속 이름 언급과 구분)
        for x in ('■ EM-17', '■ CD-06', '■ SG-09', '■ DF-30', '[장면 색인]', '[원 지침]', '## [장면] 규격', '[전사]', '[보고서]'):
            self.assertIn(x, c1, x)                                                  # 초안이 고른 번호의 원문 + 색인 + 규격 + 전사
        self.assertNotIn('■ ZZ-99', c1)
        self.assertNotIn('[나레이션 목소리 후보]', c1)
        self.assertIn('[이번 차수] 2차', c2)
        self.assertIn('\n\n[1차 다듬은 원고]\n', c2)
        self.assertIn('[1차 메모]\n- 1차 메모', c2)                                                # 1차 편집자의 메모를 2차가 본다
        self.assertIn(' 1차"', c2.split('\n\n[1차 다듬은 원고]\n')[1])                      # 2차 = 1차본을 받는다
        self.assertEqual(plan['refine'], 'p2')
        self.assertTrue(plan['scenes'][0]['vo'].endswith(' 2차'))                      # 2차는 초안을 다시 다듬었다(이 가짜 기준)
        self.assertEqual([n['pass'] for n in plan['refine_notes']], ['p1', 'p2'])

    def test_pass1_dies_pass2_refines_draft(self):
        script = 'import sys\nif len(os.listdir(sys.argv[1])) == 1:\n    print("boom", file=sys.stderr); sys.exit(1)\n' + self.OK
        r, calls, rec, plan = self.run_refine(script)
        self.assertTrue(rec['p1'].startswith('fail'), rec)
        self.assertEqual(rec['p2'], 'ok')
        self.assertIn('[이번 차수] 1차', calls[1])                                    # 맞댈 1차본이 없다 = 2차 콜이 초안을 다듬는다
        self.assertEqual(plan['refine'], 'p2')

    def test_all_fail_keeps_draft(self):
        r, calls, rec, plan = self.run_refine('import sys\nsys.exit(1)\n')
        self.assertEqual(r.returncode, 0)
        self.assertTrue(rec['p1'].startswith('fail') and rec['p2'].startswith('fail'), rec)
        self.assertNotIn('refine', plan)
        self.assertEqual(plan['scenes'][0]['vo'], DRAFT['scenes'][0]['vo'])

    def test_off_lever(self):
        r, calls, rec, plan = self.run_refine(self.OK, passes='0')
        self.assertEqual((calls, rec.get('p1')), ([], None))


class DirectorPick(unittest.TestCase):
    """감독 2콜 — 구상(색인만) → 고른 번호 원문만 쓰기 콜에 · 구상 실패 = 색인으로 대신."""
    TIMING = {'scenes': [{'dur': 7.2, 'sents': [(0, 3.1, 'a'), (3.1, 7.2, 'b')]}, {'dur': 4.1}, {'dur': 5}, {'dur': 5}, {'dur': 5}]}

    def plan(self):
        return ys_plan.normalize(json.loads(json.dumps(DRAFT)), 45)[0]

    def test_pick_parse_and_write_prompt(self):
        plan = self.plan()
        raw = json.dumps({'scenes': [{'i': 0, 'role': '훅', 'emotion': '불안', 'cd': 'CD-06', 'beats': [
            {'sec': 4, 'ids': ['S07', 'M50', 'ZZ-10'], 'why': '좁혀 오는 불안'}, {'sec': 4, 'ids': ['S13', 'M20'], 'why': '손 인서트 <script>'}]},
            {'i': 9, 'beats': [{'sec': 3, 'ids': ['S01']}]}, {'i': 1, 'beats': [{'sec': 3, 'ids': ['ZZ-20', 'not-an-id']}]}]})
        pk = gp.parse_pick('앞말 ' + raw, plan, self.TIMING)
        self.assertEqual(pk['src'], 'director')
        self.assertEqual([s['i'] for s in pk['scenes']], [0])                        # 범위 밖·번호 전부 가짜인 장면 = 버림
        b = pk['scenes'][0]['beats']
        self.assertEqual(sum(x['sec'] for x in b), 8)                                # 초 합 = 클립 길이
        self.assertEqual(b[0]['ids'], ['S07', 'M50'])
        self.assertNotIn('<', b[1]['why'])
        self.assertEqual(pk['lib'], {'cited': 4, 'made_up': 2})
        w = gp.write_prompt(plan, self.TIMING, {}, '9:16', pk)
        self.assertIn('[감독 구상]', w)
        self.assertIn('4초: S07 M50 — 좁혀 오는 불안', w)
        self.assertEqual(re.findall(r'^■ (\S+)', w, re.M), ['CD-06', 'S07', 'M50', 'S13', 'M20'])   # 원문 = 고른 번호만
        self.assertIn('[연출 색인]', w)                                                # 번호를 바꿀 때만 쓰는 색인

    def test_pick_failed_uses_index(self):
        plan = self.plan()
        pk = gp.parse_pick('not json', plan, self.TIMING)
        self.assertEqual((pk['src'], pk['scenes']), ('none', []))
        w = gp.write_prompt(plan, self.TIMING, {}, '9:16', pk)
        self.assertNotIn('[감독 구상]', w)
        self.assertNotIn('\n■ ', w)
        self.assertIn('[연출 색인]', w)

    def test_prompt_block_kinds(self):
        b = gp.prompt_block(self.plan(), self.TIMING, {}, '9:16')
        self.assertRegex(b, r'i=0 · 초 8 · 주인공: 나옴 · 유형: 인물 · 대본 번호: EM-17 CD-06')
        self.assertRegex(b, r'i=1 · 초 5 · 주인공: 없음\(주인공 없이\) · 유형: 피사체 · 화면: 빈 화면')
        self.assertRegex(b, r'i=2 · .* 유형: 상황 · 화면: 다른 사람')
        self.assertRegex(b, r'i=3 · .* 유형: 상황 · 화면: 빈 화면')
        self.assertIn('[연출 색인]', gp.pick_prompt(self.plan(), self.TIMING, {}, '9:16'))

    def test_beats_by_kind(self):
        plan = self.plan()
        raw = json.dumps({'clips': [
            {'i': 1, 'beats': [{'sec': 5, 'motion': 'the sand slips through the neck', 'camera': 'macro insert, 100mm macro lens, shallow depth, cold dawn light', 'ids': ['S19', 'L13', 'XX-90']}]},
            {'i': 2, 'beats': [{'sec': 5, 'motion': 'an office worker in a navy suit walks past the lit monitor', 'camera': 'wide shot, 24mm lens, eye-level, dim blue office light, slow pan'}]},
            {'i': 3, 'beats': [{'sec': 5, 'motion': 'The protagonist picks up the coat', 'camera': 'wide shot, 24mm lens, eye-level, dim blue office light, slow pan'}]}]})
        doc = gp.build(raw, plan, self.TIMING, {'src': 'none', 'scenes': []})
        c = {x['i']: x for x in doc['clips']}
        self.assertTrue(c[1]['beats'][0]['motion'].endswith('No people in frame.'))   # 피사체 = 빈 화면
        self.assertEqual(c[1]['beats'][0]['ids'], ['S19', 'L13'])
        self.assertNotIn('No people', c[2]['beats'][0]['motion'])                     # 다른 사람이 나오는 상황 = 빈 화면 아님
        self.assertEqual(c[3]['src'], 'fallback')                                     # 주인공 없는 장면에 주인공 = 버림
        self.assertTrue(any('색인 밖 번호 XX-90' in d['why'] for d in doc['dropped']))
        self.assertEqual((doc['pick_src'], doc['lib']['cited']), ('none', 2))

    def test_runner_two_calls(self):
        d = Path(tempfile.mkdtemp())
        (d / 'audio').mkdir()
        (d / 'plan.json').write_text(json.dumps(self.plan(), ensure_ascii=False))
        (d / 'audio/timing.json').write_text(json.dumps(self.TIMING))
        script = ('if "[연출 색인]" in P and "[감독 구상]" not in P and "구상" in P.split("\\n", 1)[0]:\n'
                  '    print(json.dumps({"scenes": [{"i": 0, "role": "훅", "emotion": "불안", "cd": "CD-06", "beats": [{"sec": 8, "ids": ["S07", "M50"], "why": "불안"}]}]}))\n'
                  'else:\n'
                  '    print(json.dumps({"clips": [{"i": 0, "beats": [{"sec": 8, "motion": "The protagonist grips the phone", "camera": "medium close-up, 85mm portrait lens, eye-level, cold phone glow, micro push-in", "ids": ["S07", "M50"]}]}]}))\n')
        b = fake_claude(d, script)
        r = subprocess.run(['bash', str(ROOT / '.github/scripts/ys_grok_plan.sh'), str(d), '9:16'], cwd=ROOT, capture_output=True, text=True,
                           env=dict(os.environ, PATH=f'{b}:{os.environ["PATH"]}', INLINE_TRIES='1', METER_OFF='1'), timeout=120)
        self.assertTrue((d / 'grokplan.done').exists(), r.stdout + r.stderr)
        calls = [p.read_text() for p in sorted((d / 'calls').iterdir())]
        self.assertEqual(len(calls), 2, r.stdout + r.stderr)
        self.assertTrue(calls[0].startswith('# 유튜브 숏폼(ys) — 그록 감독 구상'))
        self.assertNotIn('\n■ ', calls[0])                                             # 구상 = 원문 없이 색인만
        self.assertIn('[감독 구상]', calls[1])
        self.assertEqual(re.findall(r'^■ (\S+)', calls[1], re.M), ['CD-06', 'S07', 'M50'])
        doc = json.loads((d / 'grokplan.json').read_text())
        self.assertEqual((doc['pick_src'], doc['clips'][0]['src'], doc['clips'][0]['beats'][0]['ids']), ('director', 'director', ['S07', 'M50']))
        self.assertEqual(doc['pick'][0]['cd'], 'CD-06')

    def test_runner_pick_lever_off(self):
        d = Path(tempfile.mkdtemp())
        (d / 'audio').mkdir()
        (d / 'plan.json').write_text(json.dumps(self.plan(), ensure_ascii=False))
        (d / 'audio/timing.json').write_text(json.dumps(self.TIMING))
        b = fake_claude(d, 'print("{}")\n')
        subprocess.run(['bash', str(ROOT / '.github/scripts/ys_grok_plan.sh'), str(d), '9:16'], cwd=ROOT, capture_output=True, text=True,
                       env=dict(os.environ, PATH=f'{b}:{os.environ["PATH"]}', INLINE_TRIES='1', METER_OFF='1', YS_GROK_PICK='0'), timeout=120)
        calls = [p.read_text() for p in sorted((d / 'calls').iterdir())]
        self.assertEqual(len(calls), 1)                                                # 구상 끔 = 쓰기 1콜(색인으로 스스로 고른다)
        self.assertIn('[연출 색인]', calls[0])
        self.assertEqual(json.loads((d / 'grokplan.json').read_text())['pick_src'], 'none')


class Wiring(unittest.TestCase):
    def test_workflow_refine_after_draft(self):
        wf = WF.read_text(encoding='utf-8')
        st = next(x for x in re.split(r'\n      - name: ', wf) if 'ys_make.sh' in x)
        self.assertLess(st.index('bash .github/scripts/ys_make.sh /tmp/ys'), st.index('bash .github/scripts/ys_refine.sh /tmp/ys'))
        self.assertIn("YS_REFINE: ${{ vars.YS_REFINE || '2' }}", st)
        self.assertIn('ys_refine.sh /tmp/ys || echo', st)                           # 다듬기 실패가 제작을 멈추지 않는다
        self.assertIn("'refine': plan.get('refine', '')", wf)
        self.assertIn("'grok_pick': gp.get('pick_src', '')", wf)

    def test_make_prompt_gets_index(self):
        s = (ROOT / '.github/scripts/ys_make.sh').read_text(encoding='utf-8')
        self.assertIn('ys_lib.py index scene', s)
        m = (ROOT / 'prompts/ys-make.md').read_text(encoding='utf-8')
        self.assertIn('[장면 색인]', m)
        self.assertIn('"kind": "person|subject|situation"', m)
        for p in ('prompts/ys-grok.md', 'prompts/ys-grok-pick.md', 'prompts/ys-refine.md'):
            self.assertNotRegex((ROOT / p).read_text(encoding='utf-8'), r'(?m)^- (샷|렌즈·심도|높이·각도·무브|빛·분위기): ', p)   # 손으로 옮긴 어휘 곳간 0(도서관 인라인 금지)


if __name__ == '__main__':
    unittest.main()
