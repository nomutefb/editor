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
        self.assertTrue(ys_grok.prompt_for(s, False, 'Korean man, grey hoodie').startswith('The protagonist is Korean man'))
        self.assertNotIn('protagonist is', ys_grok.prompt_for({**s, 'hero': False}, False, 'Korean man'))
        i2v = ys_grok.prompt_for(s, True, 'Korean man')
        self.assertNotIn('Korean man', i2v)                                               # 첫 프레임이 얼굴을 쥐었다 = 움직임만
        self.assertIn('first frame', i2v)


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
