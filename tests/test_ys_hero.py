"""영상마다 새 주인공(운영자 260929 «c 영상마다 새로») — 러너 잡 → 맥 드라이버 전 구간 행동 검사(네트워크·Codex 0).
평의회(260929) = 문자열 유무 검사는 배선 돌연변이 8종을 하나도 못 잡았다 → 실제로 돌려서 순서·첨부·방향·꼬리를 단언한다."""
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github' / 'scripts'))
import ys_grok  # noqa: E402
import ys_images  # noqa: E402
import ys_plan  # noqa: E402

ID = '260929123456-abcdef'
LONG = 'the protagonist lying awake in bed at 3am, phone glowing on the pillow, rain streaking the dark window, crumpled bills on the desk, ' * 3
DRIVER = ROOT / 'scripts/mac/nomute_ys_driver.sh'


def sc(h):
    return {'vo': '나레이션 문장입니다 충분히 길게', 'img': LONG, 'hero': h}


RAW = {'report_md': '# 보고서\n' + '본문 ' * 200, 'scenes': [sc(True), sc(False), sc(True), sc(True), sc(True)]}
HERO = {'en': 'Korean man in his late 20s, grey hoodie, messy black hair', 'why': 'x'}


def job_for(plan, drv=2):
    """ys_images.main 을 가짜 R2 로 돌려 맥에 걸리는 잡 JSON 을 그대로 잡는다."""
    cap = {}

    def aws(*a, capture=True):
        if a[:2] == ('s3', 'cp') and 'queue/ysimg/' in a[3]:
            with open(a[2], encoding='utf-8') as f:
                cap['job'] = json.load(f)
        return subprocess.CompletedProcess(a, 0, 'done.json\n' if a[1] == 'ls' else '{}', '')
    d = tempfile.mkdtemp()
    p = os.path.join(d, 'plan.json')
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(plan, f, ensure_ascii=False)
    with mock.patch.object(ys_images, 'aws', aws), mock.patch.object(ys_images, 'mac_state', lambda: ('on', 'ok', drv)), \
            mock.patch.object(ys_images, 'progress', lambda *a, **k: None), mock.patch.object(ys_images.time, 'sleep', lambda s: None), \
            mock.patch.dict(os.environ, {'R2_BUCKET': 'b', 'YS_RATIO': '9:16'}):
        ys_images.main(['x', ID, p, os.path.join(d, 'img')])
    return cap['job']


def driver_parse(job):
    """맥 드라이버의 내장 파이썬(<<'PY' … PY)을 그대로 떼어 잡 JSON 으로 돌리고 bash eval 로 되읽는다 → {변수: 값}."""
    py = DRIVER.read_text(encoding='utf-8').split("<<'PY'\n", 1)[1].split('\nPY\n', 1)[0]
    with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as f:
        json.dump(job, f)
    out = subprocess.run([sys.executable, '-', f.name], input=py, capture_output=True, text=True, check=True).stdout
    r = subprocess.run(['bash', '-c', out + '\nfor v in YI_HERO YI_N YI_H0 YI_H1 YI_H2; do printf "%s=%s\\n" "$v" "${!v-}"; done'],
                       capture_output=True, text=True, check=True).stdout
    return dict(ln.split('=', 1) for ln in r.splitlines())


FAKE_CODEX = r'''#!/usr/bin/env python3
import json, os, sys
a = sys.argv[1:]
if a[:2] == ['login', 'status']:
    print('Logged in using ChatGPT'); sys.exit(0)
p = sys.stdin.read(); L = p.splitlines()
out = L[L.index('Save exactly one final PNG to this absolute path:') + 1]
img = [x for x in a if x.startswith('--image=')]
end = p.index('\nEND PROMPT ')
fail_ref = os.environ.get('FAKE_FAIL_REF') == '1' and img
open(os.environ['FAKE_LOG'], 'a').write(json.dumps({
    'img': img, 'ref_ok': all(os.path.isfile(x.split('=', 1)[1]) for x in img),
    'ref_named': bool(img) and ('referenced_image_paths [' + img[0].split('=', 1)[1] + ']') in p,
    'portrait': 'Portrait orientation' in p, 'sheet': 'reference sheet of ONE' in p,
    'desc': 'The protagonist is: Korean man' in p, 'tail': p[:end].rstrip().endswith('no logos'),
    'marker': p.count('BEGIN PROMPT ') == 1 and p[p.index('BEGIN PROMPT ') + 13:].split('\n', 1)[0] == p[end + 12:].split('\n', 1)[0]}) + '\n')
if fail_ref:
    sys.exit(1)
open(out, 'wb').write(b'\x89PNG\r\n\x1a\n' + b'\0' * 4000)
'''


def run_driver(job, **env_extra):
    home = Path(tempfile.mkdtemp())
    b = home / '.local/bin'
    b.mkdir(parents=True)
    (home / '.codex').mkdir()
    (home / 'nomute-action').mkdir()
    (home / 'nomute-action/환경변수.txt').write_text('R2_ACCOUNT_ID=a\nR2_ACCESS_KEY_ID=k\nR2_SECRET_ACCESS_KEY=s\nR2_BUCKET=b\n', encoding='utf-8')
    (b / 'codex').write_text(FAKE_CODEX)
    (b / 'curl').write_text('#!/bin/sh\necho "$@" >> "$FAKE_CURL"\n')
    for f in ('codex', 'curl'):
        os.chmod(b / f, 0o755)
    jf = home / 'job.json'
    jf.write_text(json.dumps(job))
    env = dict(os.environ, HOME=str(home), FAKE_LOG=str(home / 'c.log'), FAKE_CURL=str(home / 'u.log'), **env_extra)
    r = subprocess.run(['bash', str(DRIVER), str(jf)], env=env, capture_output=True, text=True, timeout=120)
    calls = [json.loads(ln) for ln in open(home / 'c.log')] if (home / 'c.log').exists() else []
    puts = (home / 'u.log').read_text() if (home / 'u.log').exists() else ''
    return r, calls, puts


class HeroJob(unittest.TestCase):
    def test_runner_job_and_mac_parse(self):
        plan, _ = ys_plan.normalize({**RAW, 'hero': HERO}, 45)
        job = job_for(plan)
        self.assertTrue(job['hero'].startswith('Korean man'))
        self.assertEqual([s['hero'] for s in job['scenes']], [True, False, True, True, True])
        self.assertIn('Korean webtoon', job['style'])
        self.assertTrue(all(s['prompt'].endswith('no logos') for s in job['scenes']))   # 화풍·글자 금지 꼬리 생존(400자 상한)
        v = driver_parse(job)
        self.assertTrue(v['YI_HERO'].startswith('Korean man'))
        self.assertEqual((v['YI_N'], v['YI_H0'], v['YI_H1'], v['YI_H2']), ('5', '1', '0', '1'))

    def test_old_mac_driver_gets_no_hero(self):
        plan, _ = ys_plan.normalize({**RAW, 'hero': HERO}, 45)
        job = job_for(plan, drv=1)   # 새 드라이버를 아직 못 받은 맥 = 주인공 없이 종전 잡(300자 안에 꼬리)
        self.assertEqual(job['hero'], '')
        self.assertFalse(any(s['hero'] for s in job['scenes']))
        self.assertTrue(all(len(s['prompt']) <= 300 and s['prompt'].endswith('no logos') for s in job['scenes']))
        self.assertFalse(any(re.search(r'(?i)\bthe protagonist\b', s['prompt']) for s in job['scenes']))

    def test_old_plan_without_hero_is_unchanged(self):
        old = {'scenes': [{'img': 'a fist', 'head': 'h'}, {'img': 'sand', 'head': 'h'}]}   # 구판 plan.json(hero 키 전무)
        job = job_for(old)
        self.assertEqual(job['hero'], '')
        self.assertFalse(any(s['hero'] for s in job['scenes']))
        v = driver_parse({k: job[k] for k in ('id', 'scenes')})                          # 구판 잡(hero·style 키 없음)
        self.assertEqual((v['YI_HERO'], v['YI_H0'], v['YI_H1']), ('', '0', '0'))

    def test_hero_injection_is_inert(self):
        mark = Path(tempfile.mkdtemp()) / 'hx'
        job = {'id': ID, 'hero': f"man'; touch {mark}; echo '$(id)`id`", 'scenes': [{'i': 0, 'prompt': 'p', 'hero': True}]}
        v = driver_parse(job)
        self.assertFalse(mark.exists())
        self.assertNotRegex(v['YI_HERO'], r"[$`]")


class HeroDriver(unittest.TestCase):
    """드라이버 전 구간(가짜 codex·curl) — 시트 먼저(잡 방향) → 주인공 장면만 참조 첨부 · 표지 난수 · 꼬리 생존."""

    def job(self):
        plan, _ = ys_plan.normalize({**RAW, 'hero': HERO}, 45)
        return job_for(plan)

    def test_sheet_then_reference_only_on_hero_scenes(self):
        r, calls, puts = run_driver(self.job())
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual([(c['sheet'], c['portrait'], bool(c['img']), c['desc']) for c in calls],
                         [(True, True, False, False)] + [(False, True, h, h) for h in (True, False, True, True, True)])
        self.assertTrue(all(c['ref_ok'] and c['ref_named'] for c in calls if c['img']), '첨부 파일이 ws 안에 있고 도구 인자로 명시돼야 함')
        self.assertTrue(all(c['tail'] for c in calls[1:]), '장면 프롬프트 끝 「no logos」 잘림')
        self.assertTrue(all(c['marker'] for c in calls), '묘사 표지 = 같은 난수 한 쌍')
        self.assertIn('/ys_img/%s/hero.png' % ID, puts)                                  # 시트 게시 = 그록 참조 모드 몫
        self.assertEqual(len(re.findall(r'/ys_img/%s/s\d\.png' % ID, puts)), 5)
        self.assertIn('그림 5장 · 실패 0', r.stdout)

    def test_no_sheet_when_time_is_short(self):
        job = self.job()
        job['deadline'] = int(__import__('time').time()) + 600   # 5장 + 시트 = 900초 몫 > 남은 600초 → 시트 생략
        r, calls, _ = run_driver(job)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse(any(c['sheet'] for c in calls))
        self.assertFalse(any(c['img'] for c in calls))
        self.assertEqual(len(calls), 5)

    def test_reference_failure_retries_without_it(self):
        r, calls, puts = run_driver(self.job(), FAKE_FAIL_REF='1')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(len(re.findall(r'/ys_img/%s/s\d\.png' % ID, puts)), 5)   # 첨부가 막혀도 장면은 전부 나온다
        hero_calls = [c for c in calls[1:] if c['desc']]
        self.assertTrue(any(not c['img'] for c in hero_calls))


class HeroGrokPrompt(unittest.TestCase):
    def test_t2v_defines_the_protagonist(self):
        s = {'img': 'the protagonist at a desk', 'motion': 'slow push-in', 'hero': True}
        self.assertTrue(ys_grok.prompt_for(s, 't2v', 'Korean man, grey hoodie').startswith('The protagonist is Korean man'))
        self.assertNotIn('protagonist is', ys_grok.prompt_for({**s, 'hero': False}, 't2v', 'Korean man'))
        i2v = ys_grok.prompt_for(s, 'i2v', 'Korean man')
        self.assertNotIn('Korean man', i2v)                                               # 첫 프레임이 얼굴을 쥐었다 = 움직임만
        self.assertIn('first frame', i2v)

    def test_r2v_ids_lock_and_timeline(self):
        s = {'img': 'the protagonist at a desk at night', 'hero': True}
        beats = [{'sec': 3, 'motion': 'The protagonist looks up from the desk', 'camera': 'close-up, 85mm portrait lens, shallow depth of field, warm lamp light'},
                 {'sec': 5, 'motion': 'The protagonist stands and walks to the window', 'camera': 'wide shot, 24mm lens, slow pull back, blue hour light'}]
        p = ys_grok.prompt_for(s, 'r2v', 'Korean man, grey hoodie', beats, 2, ('hero', 'board'))
        self.assertIn('<IMAGE_0> shows the protagonist, Korean man, grey hoodie', p)
        self.assertIn('<IMAGE_1> shows the director', p)
        self.assertIn('this clip is panel 3', p)
        self.assertIn('identical to <IMAGE_0>', p)
        self.assertIn('0-3s: The protagonist looks up', p)
        self.assertIn('3-8s: The protagonist stands', p)
        p2 = ys_grok.prompt_for({'img': 'a knotted rope'}, 'r2v', '', beats[:1], 0, ('board',))
        self.assertIn('<IMAGE_0> shows the director', p2)
        self.assertNotIn('identical to', p2)                                              # 스토리보드는 잠그지 않는다
        self.assertNotIn('0-3s', p2)                                                      # 비트 1개 = 눈금 없음

    def test_no_visual_negatives_in_video_prompts(self):
        s = {'img': 'a rope', 'motion': 'the rope tightens', 'hero': False}
        for mode, kinds in (('r2v', ('board',)), ('i2v', ()), ('t2v', ())):
            p = ys_grok.prompt_for(s, mode, '', None, 0, kinds).lower()
            self.assertNotRegex(p, r'\bno (text|captions?|logos?)\b', mode)


class GrokPlan(unittest.TestCase):
    """그록 연출 감독 산출 검문 — 초 합 = 클립 길이 · 부정문 제거 · 짧은 카메라 교체 · 빠진 장면 = 대본 움직임."""
    PLAN = {'hero': {'en': 'Korean man, grey hoodie'}, 'scenes': [{'img': 'the protagonist at a desk', 'motion': 'The protagonist sighs', 'hero': True},
                       {'img': 'a knotted rope', 'motion': 'The rope tightens slowly', 'hero': False}]}
    TIMING = {'scenes': [{'dur': 7.2}, {'dur': 4.1}]}

    def test_director_beats_fit_and_clean(self):
        import ys_grok_plan as gp
        raw = json.dumps({'clips': [{'i': 0, 'beats': [
            {'sec': 5, 'motion': 'The protagonist looks up, no text on screen', 'camera': 'close-up, 85mm portrait lens, shallow depth of field, warm lamp light, slow push-in'},
            {'sec': 5, 'motion': 'The protagonist stands', 'camera': 'wide'}]}]})
        doc = gp.build('noise ' + raw + ' trailing', self.PLAN, self.TIMING)
        c0, c1 = doc['clips']
        self.assertEqual((c0['src'], c1['src']), ('director', 'fallback'))
        self.assertEqual(sum(b['sec'] for b in c0['beats']), ys_grok.seconds_for(7.2))   # 10초 요청 → 8초 클립에 맞춤
        self.assertNotIn('no text', c0['beats'][0]['motion'])
        self.assertEqual(c0['beats'][1]['camera'], 'wide')                                # 짧은 카메라 = 기록만(감독 문장 유지)
        self.assertTrue(any('카메라 1낱말' in d['why'] for d in doc['dropped']))
        self.assertEqual(sum(b['sec'] for b in c1['beats']), ys_grok.seconds_for(4.1))
        self.assertTrue(c1['beats'][0]['motion'].endswith('No people in frame.'))        # 주인공 없는 장면 = 빈 화면 명시

    def test_broken_output_is_all_fallback(self):
        import ys_grok_plan as gp
        doc = gp.build('not json at all', self.PLAN, self.TIMING)
        self.assertEqual(doc['src'], 'fallback')
        self.assertEqual(len(doc['clips']), 2)

    def test_fit_edges(self):
        import ys_grok_plan as gp
        b = gp.fit([{'sec': 1}, {'sec': 1}, {'sec': 1}, {'sec': 1}], 2)
        self.assertEqual([x['sec'] for x in b], [2])                                    # 비트 수 ≤ 초/2
        b = gp.fit([{'sec': 2}, {'sec': 2}, {'sec': 2}, {'sec': 2}], 7)
        self.assertEqual((len(b), sum(x['sec'] for x in b)), (3, 7))
        b = gp.fit([{'sec': 9}, {'sec': 1}], 15)
        self.assertEqual(sum(x['sec'] for x in b), 15)
        self.assertTrue(all(x['sec'] >= 1 for x in b))


class GrokPlanRules(unittest.TestCase):
    """평의회 260929 봉합분 — 부정문 필터가 멀쩡한 동작을 안 지운다 · 은유 장면 규칙은 주인공 있는 영상만 · 이상 값에 안 죽는다."""

    def test_neg_filter_keeps_actions(self):
        import ys_grok_plan as gp
        self.assertEqual(gp.clean('The protagonist no longer hides the letters and walks out.', 220), 'The protagonist no longer hides the letters and walks out.')
        self.assertEqual(gp.clean('stands without a word and walks away.', 220), 'stands without a word and walks away.')
        self.assertEqual(gp.clean('rain falls, no captions on screen, wind blows', 220), 'rain falls, wind blows')
        self.assertEqual(gp.clean('No text. The protagonist sprints', 220), 'The protagonist sprints')
        self.assertEqual(gp.clean('protagonist\u2019s hand \u2014 trembling', 220), "protagonist's hand, trembling")
        self.assertEqual(gp.clean('aaa bbbb cccc', 9), 'aaa bbbb')                     # 낱말 경계 자르기

    def test_nobody_only_for_metaphor_scenes(self):
        import ys_grok_plan as gp
        t = {'scenes': [{'dur': 5}]}
        no_hero = {'scenes': [{'img': 'a person rubs eyes', 'motion': 'a person rubs eyes; slow push-in', 'hero': False}]}
        self.assertNotIn('No people', gp.build('', no_hero, t)['clips'][0]['beats'][0]['motion'])   # 주인공 없는 영상 = 사람이 나올 수 있다
        with_hero = {'hero': {'en': 'Korean man'}, 'scenes': [{'img': 'a rope', 'motion': 'the rope tightens', 'hero': False}]}
        b = gp.build('', with_hero, t)['clips'][0]['beats'][0]
        self.assertTrue(b['motion'].endswith('No people in frame.'))
        self.assertEqual(b['camera'], '')                                                 # 대체안 = 대본 motion 의 카메라만(덧붙임 0)

    def test_weird_director_output_does_not_crash(self):
        import ys_grok_plan as gp
        t = {'scenes': [{'dur': 5}]}
        plan = {'hero': {'en': 'Korean man'}, 'scenes': [{'img': 'a rope', 'motion': 'the rope tightens', 'hero': False}]}
        for raw in ('{"clips": [{"i": 0, "beats": [{"sec": 1e999, "motion": "the rope snaps apart", "camera": "macro"}]}]}',
                    '{"clips": {"i": 0}}', '{"clips": [{"i": 0, "beats": {"sec": 3}}]}', '```json\n{"note": 1}\n```'):
            doc = gp.build(raw, plan, t)
            self.assertEqual(len(doc['clips']), 1, raw)
        raw = json.dumps({'clips': [{'i': 0, 'beats': [{'sec': 5, 'motion': 'The protagonist pulls the rope', 'camera': 'macro insert shot, shallow depth of field, rim light, locked-off'}]}]})
        self.assertEqual(gp.build(raw, plan, t)['clips'][0]['src'], 'fallback')          # 은유 장면에 주인공 = 버림


class GrokFallbacks(unittest.TestCase):
    """참조 요청이 거절되면 글→영상으로 · 첫 프레임 모드는 대본 움직임만 · 보드를 못 받은 판의 사유 = 맥 꺼짐 아님."""

    def run_main(self, files, start=None, plan_hero=True):
        import types
        d = Path(tempfile.mkdtemp())
        img, vid = d / 'img', d / 'vid'
        img.mkdir()
        png = b'\x89PNG\r\n\x1a\n' + b'\0' * 4000
        for n, body in files.items():
            (img / n).write_bytes(png if body is None else body)
        plan = {'scenes': [{'img': 'close-up of the protagonist at a desk', 'motion': 'The protagonist sighs; slow push-in', 'hero': True},
                           {'img': 'a knotted rope', 'motion': 'The rope tightens', 'hero': False}]}
        if plan_hero:
            plan['hero'] = {'en': 'Korean man, grey hoodie'}
        (d / 'plan.json').write_text(json.dumps(plan))
        (d / 'timing.json').write_text(json.dumps({'scenes': [{'dur': 7.2}, {'dur': 4.1}]}))
        sent = []

        def start_video(prompt, **k):
            sent.append(dict(k, prompt=prompt))
            if start:
                start(prompt, k)
            return f'r{len(sent)}'
        fake = types.SimpleNamespace(fresh_token=lambda: 'tok', start_video=start_video,
                                     wait_video=lambda rid, **k: {'url': 'u', 'cost_usd': 1.0}, fetch=lambda url: b'mp4')
        with mock.patch.dict(sys.modules, {'grok_api': fake}), mock.patch.object(ys_grok, 'progress', lambda *a, **k: None), \
                mock.patch.object(ys_grok, 'strip_audio', lambda a, b: Path(b).write_bytes(b'x' * 20000) > 0), \
                mock.patch.object(ys_grok.time, 'sleep', lambda s: None), mock.patch.dict(os.environ, {'XAI_REFRESH_TOKEN': 't'}):
            ys_grok.main(['x', ID, str(d / 'plan.json'), str(d / 'timing.json'), str(img), str(vid), '9:16'])
        return sent, json.loads((vid / 'vid.json').read_text(encoding='utf-8'))

    def test_rejected_refs_fall_back_to_t2v(self):
        class Rej(Exception):
            where = 'video-start'

        def start(prompt, k):
            if k.get('refs'):
                raise Rej('400 bad reference')
        sent, v = self.run_main({'board.png': None, 'hero.png': None}, start)
        self.assertEqual(v['used'], 2)
        self.assertEqual(v['modes'], {'t2v': 2})
        t2v = [x for x in sent if not x.get('refs')]
        self.assertTrue(any(x['prompt'].startswith('The protagonist is Korean man') for x in t2v))
        self.assertLessEqual(sum(1 for x in sent if x.get('refs')), 3)                  # 거절 칸은 공용 표지 = 같은 거절 반복 0
        self.assertIn('400 bad reference', v['ref_err'])                                  # 첫 거절 사유가 남는다

    def test_rejected_bytes_retry_as_public_url(self):
        class Rej(Exception):
            where = 'video-start'

        def start(prompt, k):   # 본문 적재(바이트) = 몸집 거절 · 공개 주소 = 통과(예전 콘티 레인 바이트↔주소 전환)
            if k.get('refs') and not all(isinstance(x, str) for x in k['refs']):
                raise Rej('413 payload too large')
        with mock.patch.dict(os.environ, {'R2_PUBLIC_BASE': 'https://pub.example'}):
            sent, v = self.run_main({'board.png': None, 'hero.png': None}, start)
        self.assertEqual((v['used'], v['modes']), (2, {'r2v': 2}))
        self.assertEqual(set(v['ref_how'].values()), {'url'})
        url_refs = [x['refs'] for x in sent if x.get('refs') and isinstance(x['refs'][0], str)]
        self.assertIn(['https://pub.example/ys_img/%s/hero.png' % ID, 'https://pub.example/ys_img/%s/board.png' % ID], url_refs)

    def test_two_refs_rejected_then_hero_only(self):
        class Rej(Exception):
            where = 'video-start'

        def start(prompt, k):   # 두 장 = 거절 · 한 장 = 통과
            if k.get('refs') and len(k['refs']) > 1:
                raise Rej('400 too many references')
        sent, v = self.run_main({'board.png': None, 'hero.png': None}, start)
        self.assertEqual(v['modes'], {'r2v': 2})
        self.assertEqual(v['ref_how'].get('0'), 'bytes·1장')

    def test_i2v_uses_script_motion_only(self):
        sent, v = self.run_main({'s0.png': None, 's1.png': None})
        self.assertEqual(v['modes'], {'i2v': 2})
        p0 = next(x['prompt'] for x in sent if 'sighs' in x['prompt'])
        self.assertTrue(p0.startswith('The protagonist sighs; slow push-in.'))
        self.assertNotIn('0-', p0)

    def test_board_failed_note_is_not_mac_off(self):
        sent, v = self.run_main({'img.json': json.dumps({'used': 0, 'note': 'x', 'board': True}).encode()})
        self.assertIn('스토리보드를 못 받아', v['note'])
        self.assertNotIn('맥이 꺼져', v['note'])

    def test_hero_only_refs_and_lever(self):
        sent, v = self.run_main({'hero.png': None})
        self.assertEqual(v['modes'], {'r2v': 1, 't2v': 1})                                # 캐릭터 보드만 있어도 주인공 장면은 참조 모드
        with mock.patch.dict(os.environ, {'YS_GROK_REF': '0'}):
            sent, v = self.run_main({'hero.png': None, 'board.png': None})
        self.assertNotIn('r2v', v['modes'])                                               # A/B 레버 = 참조 모드 끔


class GrokBoard(unittest.TestCase):
    """그록 = 장면 그림 N장 대신 캐릭터 보드 + 스토리보드 1장(drv 3 맥) → 드라이버가 보드 2장만 그려 게시."""

    def job(self, drv=3):
        plan, _ = ys_plan.normalize({**RAW, 'hero': HERO}, 45)
        with mock.patch.dict(os.environ, {'YS_IMG': 'grok'}):
            return job_for(plan, drv)

    def test_runner_board_job(self):
        j = self.job()
        self.assertEqual(j['scenes'], [])
        self.assertTrue(j['hero'].startswith('Korean man'))
        self.assertEqual(j['board_orient'], 'portrait')                                   # 세로 영상 = 세로 시트 3열(세로 칸이 물리적으로 들어간다)
        self.assertIn('exactly 5 tall vertical panels', j['board'])
        self.assertIn('3 columns by 2 rows, the last row has only 2 panels', j['board'])
        self.assertIn('The protagonist in every panel where they appear: Korean man', j['board'])
        self.assertIn('Panel 5:', j['board'])
        self.assertLessEqual(len(j['board']), 1800)
        self.assertTrue(self.job(drv=2)['scenes'])                                        # 옛 맥 = 종전 장면 그림

    def test_driver_draws_sheet_then_board(self):
        r, calls, puts = run_driver(self.job())
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual([(c['sheet'], bool(c['img']), c['portrait']) for c in calls], [(True, False, True), (False, True, True)])
        self.assertTrue(calls[1]['desc'])                                                  # 보드에도 주인공 글 정의(시트 첨부가 빠져도 같은 사람)
        self.assertTrue(calls[1]['ref_ok'] and calls[1]['ref_named'])
        self.assertIn('/ys_img/%s/board.png' % ID, puts)
        self.assertIn('/ys_img/%s/hero.png' % ID, puts)
        self.assertFalse(re.search(r'/ys_img/%s/s\d\.png' % ID, puts))


class GrokRun(unittest.TestCase):
    """ys_grok.main 전 구간(가짜 그록) — 보드가 있으면 참조 모드 · 주인공 장면만 인물 참조 · 비율 명시 · 비트 시각표."""

    def test_main_uses_boards_and_beats(self):
        import types
        d = Path(tempfile.mkdtemp())
        img, vid = d / 'img', d / 'vid'
        img.mkdir()
        png = b'\x89PNG\r\n\x1a\n' + b'\0' * 4000
        (img / 'board.png').write_bytes(png)
        (img / 'hero.png').write_bytes(png)
        plan = {'hero': {'en': 'Korean man, grey hoodie'}, 'scenes': [
            {'img': 'the protagonist at a desk', 'motion': 'The protagonist sighs', 'hero': True},
            {'img': 'a knotted rope', 'motion': 'The rope tightens', 'hero': False}]}
        timing = {'scenes': [{'dur': 7.2, 'sents': []}, {'dur': 4.1, 'sents': []}]}
        (d / 'plan.json').write_text(json.dumps(plan))
        (d / 'timing.json').write_text(json.dumps(timing))
        (d / 'grokplan.json').write_text(json.dumps({'src': 'director', 'clips': [
            {'i': 0, 'beats': [{'sec': 3, 'motion': 'The protagonist looks up', 'camera': 'close-up'}, {'sec': 5, 'motion': 'The protagonist stands', 'camera': 'wide'}]},
            {'i': 1, 'beats': [{'sec': 5, 'motion': 'The rope tightens. No people in frame.', 'camera': 'macro'}]}]}))
        sent = []
        fake = types.SimpleNamespace(
            fresh_token=lambda: 'tok',
            start_video=lambda prompt, **k: sent.append(dict(k, prompt=prompt)) or f'r{len(sent)}',
            wait_video=lambda rid, **k: {'url': 'u', 'cost_usd': 1.0},
            fetch=lambda url: b'mp4')
        with mock.patch.dict(sys.modules, {'grok_api': fake}), mock.patch.object(ys_grok, 'progress', lambda *a, **k: None), \
                mock.patch.object(ys_grok, 'strip_audio', lambda a, b: Path(b).write_bytes(b'x' * 20000) > 0), \
                mock.patch.dict(os.environ, {'XAI_REFRESH_TOKEN': 't'}):
            rc = ys_grok.main(['x', ID, str(d / 'plan.json'), str(d / 'timing.json'), str(img), str(vid), '9:16'])
        self.assertEqual(rc, 0)
        by = {('rope' in x['prompt']): x for x in sent}
        self.assertEqual(len(sent), 2)
        self.assertEqual(len(by[False]['refs']), 2)                                         # 주인공 장면 = 캐릭터 보드 + 스토리보드
        self.assertEqual(len(by[True]['refs']), 1)                                          # 은유 장면 = 스토리보드만
        self.assertTrue(all(x['image'] is None and x['ratio'] == '9:16' for x in sent))     # 참조 모드 = 첫 프레임 없음 · 비율 명시
        self.assertIn('0-3s: The protagonist looks up', by[False]['prompt'])
        self.assertEqual(by[False]['seconds'], 8)
        v = json.loads((vid / 'vid.json').read_text(encoding='utf-8'))
        self.assertEqual((v['used'], v['modes'], v['plan_src']), (2, {'r2v': 2}, 'director'))


class GrokSecretBlocks(unittest.TestCase):
    """ys-make·sb-make 의 그록 자격 칸 가르기 = 같은 규칙(운영자 260929 «영상 제작기랑 지금 만드는 거 둘 다»)."""

    @staticmethod
    def block(wf):
        s = (ROOT / '.github/workflows' / wf).read_text(encoding='utf-8')
        a = s.index('case "$XAI_MOVED" in')
        b = s.index('unset XAI_MOVED', a)
        return '\n'.join(ln.split('   #')[0].strip() for ln in s[a:b].splitlines() if ln.strip())

    def test_blocks_identical(self):
        self.assertEqual(self.block('ys-make.yml'), self.block('sb-make.yml'))

    def test_classification(self):
        body = self.block('ys-make.yml') + '\necho "R=${XAI_REFRESH_TOKEN:-} P=${XAI_SECRET_PAT:-} N=${XAI_SECRET_NAME:-}"'
        cases = [  # (이관 칸, 기존 그록 칸, GH_TOKEN) → 기대
            ('', '', '', 'R= P= N='),
            ('xai-refresh-abc', '', '', 'R=xai-refresh-abc P= N=XAI_SECRET_PAT'),
            ('xai-refresh-abc', 'old', 'gh', 'R=old P=gh N='),
            ('ghp_123', '', '', 'R= P=ghp_123 N='),
            ('github_pat_1', 'old', 'gh', 'R=old P=gh N='),
            ('xai-refresh-abc', '', 'gh', 'R=xai-refresh-abc P=gh N=XAI_SECRET_PAT'),
        ]
        for moved, old, pat, want in cases:
            env = {'PATH': os.environ['PATH'], 'XAI_MOVED': moved, 'XAI_REFRESH_TOKEN': old, 'XAI_SECRET_PAT': pat}
            out = subprocess.run(['bash', '-c', body], env=env, capture_output=True, text=True).stdout.strip().splitlines()[-1]
            self.assertEqual(out, want, (moved, old, pat))


# ── 평의회 G8(260929) 돌연변이 봉합 — 배선(경로·심박 표지·배경 감독·러너 내려받기·보드 참조문·재시도) ──
HB = ROOT / 'scripts/mac/nomute_ys_heartbeat.sh'
WF = ROOT / '.github/workflows/ys-make.yml'
PNG = b'\x89PNG\r\n\x1a\n'
HERO_B, BOARD_B, S_B = PNG + b'H' * 4000, PNG + b'B' * 4000, PNG + b'S' * 4000
PLAN2 = {'hero': {'en': 'Korean man, grey hoodie'}, 'scenes': [
    {'img': 'the protagonist at a desk', 'motion': 'The protagonist sighs', 'hero': True},
    {'img': 'a knotted rope', 'motion': 'The rope tightens', 'hero': False}]}
GP2 = {'src': 'director', 'clips': [
    {'i': 0, 'beats': [{'sec': 3, 'motion': 'The protagonist looks up', 'camera': 'close-up'}, {'sec': 5, 'motion': 'The protagonist stands', 'camera': 'wide'}]},
    {'i': 1, 'beats': [{'sec': 5, 'motion': 'The rope tightens. No people in frame.', 'camera': 'macro'}]}]}


def run_grok_main(plan, *, files, grokplan=None, env=None, bg=False, on_sleep=None):
    """ys_grok.main 을 워크플로 배치(plan.json · audio/timing.json · grokplan.json 이 plan 옆)로 돌린다(가짜 그록)."""
    import types
    d = Path(tempfile.mkdtemp())
    img, vid = d / 'img', d / 'vid'
    img.mkdir()
    (d / 'audio').mkdir()
    for name, data in files.items():
        if isinstance(data, Path):
            (img / name).symlink_to(data)
        else:
            (img / name).write_bytes(data)
    timing = {'scenes': [{'dur': 7.2, 'sents': []}, {'dur': 4.1, 'sents': []}][:len(plan['scenes'])]}
    (d / 'plan.json').write_text(json.dumps(plan))
    (d / 'audio' / 'timing.json').write_text(json.dumps(timing))
    if grokplan is not None:
        (d / 'grokplan.json').write_text(json.dumps(grokplan))
    if bg:
        (d / 'grokplan.bg').touch()
    sent, sleeps = [], []

    def start_video(prompt, **k):
        if k.get('image') and k.get('refs'):
            raise AssertionError('image 와 refs 동시 발사(grok_api 공식 제약)')
        sent.append(dict(k, prompt=prompt))
        return f'r{len(sent)}'

    def sleep(sec):
        sleeps.append(sec)
        if on_sleep:
            on_sleep(d)
    fake = types.SimpleNamespace(fresh_token=lambda: 'tok', start_video=start_video,
                                 wait_video=lambda rid, **k: {'url': 'u', 'cost_usd': 1.0}, fetch=lambda url: b'mp4')
    with mock.patch.dict(sys.modules, {'grok_api': fake}), mock.patch.object(ys_grok, 'progress', lambda *a, **k: None), \
            mock.patch.object(ys_grok, 'strip_audio', lambda a, b: Path(b).write_bytes(b'x' * 20000) > 0), \
            mock.patch.object(ys_grok.time, 'sleep', sleep), mock.patch.dict(os.environ, {'XAI_REFRESH_TOKEN': 't', **(env or {})}):
        rc = ys_grok.main(['x', ID, str(d / 'plan.json'), str(d / 'audio' / 'timing.json'), str(img), str(vid), '9:16'])
    return rc, sent, json.loads((vid / 'vid.json').read_text(encoding='utf-8')), sleeps


class G8Run(unittest.TestCase):
    def test_refs_bytes_order_panel_and_no_first_frame(self):
        rc, sent, v, _ = run_grok_main(PLAN2, files={'hero.png': HERO_B, 'board.png': BOARD_B, 's0.png': S_B, 's1.png': S_B},
                                       grokplan=GP2, env={'R2_PUBLIC_BASE': 'https://pub.example'})
        self.assertEqual(rc, 0)
        by = {('rope' in x['prompt']): x for x in sent}
        self.assertEqual(by[False]['refs'], [HERO_B, BOARD_B])          # <IMAGE_0> = 캐릭터 보드 · <IMAGE_1> = 스토리보드 · 바이트 그대로
        self.assertEqual(by[True]['refs'], [BOARD_B])
        self.assertTrue(all(x['image'] is None for x in sent))
        self.assertIn('<IMAGE_0> shows the protagonist', by[False]['prompt'])
        self.assertIn('<IMAGE_1> shows the director', by[False]['prompt'])
        self.assertIn('<IMAGE_0> shows the director', by[True]['prompt'])
        self.assertIn('this clip is panel 1 (', by[False]['prompt'])
        self.assertIn('this clip is panel 2 (', by[True]['prompt'])
        self.assertEqual(v['plan_src'], 'director')                       # timing 이 audio/ 에 있어도 plan 옆 grokplan.json

    def test_no_hero_definition_drops_hero_ref(self):
        _, sent, _, _ = run_grok_main({**PLAN2, 'hero': {}}, files={'hero.png': HERO_B, 'board.png': BOARD_B}, grokplan=GP2)
        self.assertEqual([x['refs'] for x in sent], [[BOARD_B], [BOARD_B]])

    def test_hero_only_without_board(self):
        _, sent, v, _ = run_grok_main(PLAN2, files={'hero.png': HERO_B}, grokplan=GP2)
        by = {('rope' in x['prompt']): x for x in sent}
        self.assertEqual(by[False]['refs'], [HERO_B])                     # 주인공 장면 = 캐릭터 보드만으로 참조
        self.assertIsNone(by[True]['refs'])                                # 은유 장면 = 글→영상
        self.assertEqual(v['modes'], {'r2v': 1, 't2v': 1})

    def test_symlink_ref_ignored(self):
        tgt = Path(tempfile.mkdtemp()) / 'secret.png'
        tgt.write_bytes(HERO_B)
        _, sent, _, _ = run_grok_main(PLAN2, files={'hero.png': tgt, 'board.png': BOARD_B}, grokplan=GP2)
        self.assertTrue(all(x['refs'] == [BOARD_B] for x in sent))

    def test_short_grokplan_falls_back(self):
        _, _, v, _ = run_grok_main(PLAN2, files={'board.png': BOARD_B}, grokplan={'src': 'director', 'clips': GP2['clips'][:1]})
        self.assertEqual(v['plan_src'], 'fallback')

    def test_waits_for_background_director_only_when_launched(self):
        def land(d):
            (d / 'grokplan.json').write_text(json.dumps(GP2))
            (d / 'grokplan.done').touch()
        _, _, v, sleeps = run_grok_main(PLAN2, files={'board.png': BOARD_B}, bg=True, on_sleep=land)
        self.assertEqual(v['plan_src'], 'director')                       # 배경 감독이 끝날 때까지 기다렸다 쓴다
        self.assertTrue(sleeps)
        _, _, v, sleeps = run_grok_main(PLAN2, files={'board.png': BOARD_B})
        self.assertEqual((v['plan_src'], [s for s in sleeps if s == 5]), ('fallback', []))   # 표지 없음 = 기다리지 않는다


class G8Plan(unittest.TestCase):
    def test_fit_property(self):
        import itertools
        import ys_grok_plan as gp
        for total in range(1, 16):
            for secs in itertools.product((1, 2, 3, 7, 10), repeat=3):
                b = gp.fit([{'sec': x} for x in secs], total)
                self.assertEqual(sum(x['sec'] for x in b), total, (secs, total))
                self.assertTrue(all(x['sec'] >= 1 for x in b), (secs, total, b))
                self.assertLessEqual(len(b), max(1, min(gp.MAX_BEATS, total // 2)))

    def test_all_negation_forms_are_stripped(self):
        import ys_grok_plan as gp
        for x in ('The rope tightens, no text on screen', 'The rope tightens without any captions',
                  'The rope tightens; avoid logos anywhere', 'no watermark. The rope tightens', 'The rope tightens, no visible subtitles'):
            self.assertNotRegex(gp.clean(x, 220).lower(), r'\b(text|captions?|logos?|subtitles?|watermarks?)\b', x)

    def test_prompt_block_hero_flags(self):
        import ys_grok_plan as gp
        timing = {'scenes': [{'dur': 7.2, 'sents': [(0, 3.1, 'a')]}, {'dur': 4.1}]}
        b = gp.prompt_block(PLAN2, timing, {'title': 't'}, '9:16')
        self.assertRegex(b, r'i=0 · 초 8 · 주인공: 나옴')
        self.assertRegex(b, r'i=1 · 초 5 · 주인공: 없음')
        self.assertIn('[자막 띠] 화면 높이 65%', b)
        b2 = gp.prompt_block({**PLAN2, 'hero': {}}, timing, {}, '9:16')
        self.assertNotIn('주인공: 나옴', b2)
        self.assertIn('[주인공] 없음', b2)


class G8Board(unittest.TestCase):
    def test_board_prompt_grid_and_count(self):
        for n in range(1, 13):
            for orient in ('portrait', 'landscape'):
                plan = {'scenes': [{'img': f'scene number {k} with a long description ' * 6, 'hero': False} for k in range(n)]}
                b = ys_images.board_prompt(plan, '', orient)['board']
                self.assertRegex(b, rf'exactly {n} (tall vertical|wide horizontal) panels in reading order')
                c, r = map(int, re.search(r'(\d+) columns? by (\d+) rows?', b).groups())
                self.assertGreaterEqual(c * r, n)
                self.assertLess(c * r - n, c)                                   # 마지막 줄이 비지 않는다
                if c * r != n:
                    self.assertIn(f'the last row has only {n - c * (r - 1)} panel', b)
                self.assertEqual(len(re.findall(r'\bPanel \d+:', b)), n)
                self.assertTrue(b.endswith('no speech bubbles') and len(b) <= 1800)

    def test_mac_reads_full_board(self):
        plan, _ = ys_plan.normalize({**RAW, 'hero': HERO}, 45)
        with mock.patch.dict(os.environ, {'YS_IMG': 'grok'}):
            j = job_for(plan, 3)
        py = DRIVER.read_text(encoding='utf-8').split("<<'PY'\n", 1)[1].split('\nPY\n', 1)[0]
        with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as f:
            json.dump(j, f)
        out = subprocess.run([sys.executable, '-', f.name], input=py, capture_output=True, text=True, check=True).stdout
        r = subprocess.run(['bash', '-c', out + '\nprintf "%s\\n%s" "$YI_BOR" "$YI_BOARD"'], capture_output=True, text=True, check=True).stdout
        bor, board = r.split('\n', 1)
        self.assertEqual((bor, board), (j['board_orient'], j['board']))

    def _job(self):
        plan, _ = ys_plan.normalize({**RAW, 'hero': HERO}, 45)
        with mock.patch.dict(os.environ, {'YS_IMG': 'grok'}):
            return job_for(plan, 3)

    def test_board_uses_board_refline(self):
        fc = FAKE_CODEX.replace("'marker':", "'board_ref': 'Follow the panel layout of the description' in p, 'no_panels': 'no panels, grid' in p, 'marker':")
        with mock.patch.dict(globals(), {'FAKE_CODEX': fc}):
            r, calls, _ = run_driver(self._job())
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(calls[1]['board_ref'] and not calls[1]['no_panels'])   # 스토리보드에 「칸 금지」가 가면 칸이 사라진다

    def test_board_ref_failure_retries_without_ref(self):
        r, calls, puts = run_driver(self._job(), FAKE_FAIL_REF='1')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(puts.count('/ys_img/%s/board.png' % ID), 1)
        self.assertFalse(calls[-1]['img'])

    def test_runner_downloads_hero_and_board_only(self):
        plan, _ = ys_plan.normalize({**RAW, 'hero': HERO}, 45)
        d = Path(tempfile.mkdtemp())
        (d / 'plan.json').write_text(json.dumps(plan, ensure_ascii=False), encoding='utf-8')

        def aws(*a, capture=True):
            if a[:2] == ('s3', 'ls'):
                return subprocess.CompletedProcess(a, 0, 'x 1 hero.png\nx 1 board.png\nx 1 s0.png\nx 1 done.json\n', '')
            if a[:2] == ('s3', 'cp') and a[2].endswith('.png'):
                Path(a[3]).write_bytes(PNG + b'\0' * 4000)
            return subprocess.CompletedProcess(a, 0, '{}', '')
        with mock.patch.object(ys_images, 'aws', aws), mock.patch.object(ys_images, 'mac_state', lambda: ('on', 'ok', 3)), \
                mock.patch.object(ys_images, 'progress', lambda *a, **k: None), mock.patch.object(ys_images.time, 'sleep', lambda s: None), \
                mock.patch.dict(os.environ, {'R2_BUCKET': 'b', 'YS_RATIO': '9:16', 'YS_IMG': 'grok'}):
            ys_images.main(['x', ID, str(d / 'plan.json'), str(d / 'img')])
        self.assertEqual(sorted(p.name for p in (d / 'img').glob('*.png')), ['board.png', 'hero.png'])
        j = json.loads((d / 'img' / 'img.json').read_text(encoding='utf-8'))
        self.assertEqual((j['used'], j.get('board')), (0, True))
        self.assertIn('캐릭터 보드', j['note'])

    def test_lever_off_keeps_scene_stills(self):
        plan, _ = ys_plan.normalize({**RAW, 'hero': HERO}, 45)
        with mock.patch.dict(os.environ, {'YS_IMG': 'grok', 'YS_GROK_REF': '0'}):
            self.assertNotIn('board', job_for(plan, 3))
        with mock.patch.dict(os.environ, {'YS_IMG': 'grok', 'YS_GROK_ON': 'false'}):
            self.assertNotIn('board', job_for(plan, 3))                     # 그록 스텝이 안 도는 판 = 보드 안 그림


class G8Wiring(unittest.TestCase):
    def test_heartbeat_advertises_board_capable_driver(self):
        home = Path(tempfile.mkdtemp())
        b = home / '.local/bin'
        b.mkdir(parents=True)
        (home / '.codex').mkdir()
        (home / 'nomute-action').mkdir()
        (home / 'nomute-action/환경변수.txt').write_text('R2_ACCOUNT_ID=a\nR2_ACCESS_KEY_ID=k\nR2_SECRET_ACCESS_KEY=s\nR2_BUCKET=b\n', encoding='utf-8')
        (b / 'codex').write_text('#!/bin/sh\necho "Logged in using ChatGPT"\n')
        (b / 'curl').write_text('#!/bin/sh\nexit 0\n')
        for f in ('codex', 'curl'):
            os.chmod(b / f, 0o755)
        (home / 'nomute_ys_driver.sh').write_text(DRIVER.read_text(encoding='utf-8'), encoding='utf-8')
        subprocess.run(['bash', str(HB), '--force'], env=dict(os.environ, HOME=str(home)), check=True, timeout=60)
        hb = json.loads((home / '.nomute_ys_hb.json').read_text())
        import time as _t
        with mock.patch.object(ys_images, 'aws', lambda *a, **k: subprocess.CompletedProcess(a, 0, json.dumps({**hb, 'ts': int(_t.time())}), '')):
            st, _, drv = ys_images.mac_state()
        self.assertEqual((st, drv), ('on', 3))
        plan, _ = ys_plan.normalize({**RAW, 'hero': HERO}, 45)
        with mock.patch.dict(os.environ, {'YS_IMG': 'grok'}):
            self.assertIn('board', job_for(plan, drv))                    # 설치된 드라이버 표지 → 심박 → 러너 = 보드 잡

    def test_plan_script_always_signals_done(self):
        d = Path(tempfile.mkdtemp())
        (d / 'audio').mkdir()
        (d / 'plan.json').write_text(json.dumps(PLAN2))
        (d / 'audio/timing.json').write_text(json.dumps({'scenes': [{'dur': 7.2}, {'dur': 4.1}]}))
        b = d / 'bin'
        b.mkdir()
        (b / 'claude').write_text('#!/bin/sh\necho "boom" >&2\nexit 1\n')
        os.chmod(b / 'claude', 0o755)
        r = subprocess.run(['bash', str(ROOT / '.github/scripts/ys_grok_plan.sh'), str(d), '9:16'], cwd=ROOT, capture_output=True, text=True,
                           env=dict(os.environ, PATH=f'{b}:{os.environ["PATH"]}', INLINE_TRIES='1'), timeout=120)
        self.assertTrue((d / 'grokplan.done').exists(), r.stdout + r.stderr)
        self.assertEqual(json.loads((d / 'grokplan.json').read_text())['src'], 'fallback')
        self.assertNotEqual(r.returncode, 0)

    def test_workflow_director_wiring(self):
        wf = WF.read_text(encoding='utf-8')
        steps = re.split(r'\n      - name: ', wf)
        di = next(i for i, x in enumerate(steps) if 'ys_grok_plan.sh' in x)
        ii = next(i for i, x in enumerate(steps) if 'ys_images.py' in x)
        vi = next(i for i, x in enumerate(steps) if 'ys_grok.py' in x)
        self.assertLess(di, ii)
        self.assertLess(ii, vi)
        d = steps[di]
        self.assertLess(d.index('touch /tmp/ys/grokplan.bg'), d.index('nohup bash .github/scripts/ys_grok_plan.sh'))
        self.assertRegex(d, r'nohup bash \.github/scripts/ys_grok_plan\.sh /tmp/ys "\$YS_RATIO" .*&\n')
        cond = re.search(r"if: (\$\{\{.*?\}\})", steps[vi]).group(1)
        self.assertIn(cond, d)                                              # 감독·그록 스텝 조건 동일

    def test_grok_img_budget(self):
        import ys_progress
        self.assertLess(ys_progress.budgets(img='grok', ln=90)['img'], ys_progress.budgets(img='codex', ln=90)['img'])

