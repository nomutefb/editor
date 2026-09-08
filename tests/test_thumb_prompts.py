"""4화풍 썸네일 프롬프트 합성기 회귀(운영자 260908 "기사만 주면 네 개 · 라이브러리 최대 활용 · 풍자적이되 거부감 없이 · 기존 배치 고려").

Gemini·R2·네트워크 0 — thumb_gen.compose_all 을 임시 queue md 로 실제 조립해 계약을 판정한다.
정본 = .github/scripts/thumb_gen.py compose_prompt (process_one 과 --dry 가 같은 함수를 탄다)."""
import importlib
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault('GEMINI_API_KEY', 'test-noop')   # 모듈 상단 no-op 분기 회피(호출 0)
sys.path.insert(0, str(ROOT / '.github' / 'scripts'))
tg = importlib.import_module('thumb_gen')

FM = '''---
title: "원문 제목"
url: "https://example.invalid/a"
tags: "{tags}"
image_query: "저출산세 딩크 비혼 논쟁"
image_query_en: "{en}"
emotion: "{emotion}"
hook: "{hook}"
thumb_scene: "{scene}"
thumb_dispatch: "{dispatch}"
satire_target: "{target}"
thumb_metaphor: "{metaphor}"
---

# 🍼 후킹 헤드

## 🧷 한줄 요약
{lead}

### 💡 이 기사의 시사점
{insight}
'''
BASE = dict(tags='해당 없음', en='', emotion='어이없음과 억울함이 동시에 맺힌다', hook='낳지 않을 자유에 세금을 매기자는 말',
            scene='형광등 아래 아파트 거실 식탁, 30대 여성이 세금 고지서를 쥔 채 굳은 얼굴로 화면 밖을 응시하는 저녁',
            dispatch='AG-01 LGT12 SG-08 EM-10', target='', metaphor='',
            lead='커뮤니티 글쓴이가 딩크·비혼자에게 저출산세를 걷자고 주장해 찬반이 갈렸다.',
            insight='세금은 감정이 아니라 제도의 문제다. 비용 분담은 제도가 답해야 할 질문이지 개인끼리 다툴 논쟁이 아니다.')


def compose(**over):
    kw = dict(BASE, **over)
    with tempfile.TemporaryDirectory() as d:
        md = Path(d) / '260908-0000-test.md'
        md.write_text(FM.format(**kw), encoding='utf-8')
        return tg.compose_all(str(md))


class ThumbPromptTests(unittest.TestCase):
    def test_four_styles_complete_and_distinct(self):
        prompts, parsed = compose()
        self.assertEqual(list(prompts), ['photo', 'webtoon', 'watercolor', 'cartoon'])
        for sid, p in prompts.items():
            self.assertIn('STYLE: ', p, sid)
            self.assertIn('LAYOUT (a caption block will later cover', p, sid)   # 기존 썸네일 배치(하단 자막 존)
            self.assertTrue(len(p) > 800, sid)
        self.assertEqual(len({p for p in prompts.values()}), 4, '4화풍이 서로 달라야 한다')
        for sid in ('photo', 'webtoon', 'watercolor'):
            self.assertIn(tg.SCENE_PRIME, prompts[sid], sid)
        self.assertIn('MOMENT (this style', prompts['watercolor'])
        self.assertIn('MOMENT (this style', prompts['webtoon'])
        self.assertNotIn('MOMENT (this style', prompts['photo'])
        self.assertIn('extreme close-up', prompts['watercolor'].split('CAMERA: ')[1].split('\n')[0])   # cam_lock
        self.assertIn(tg.GOVERNING_SATIRE, prompts['cartoon'])
        self.assertIn(tg.CARTOON_TEXT_RULES, prompts['cartoon'])
        self.assertIn(tg.LAYOUT_CARTOON, prompts['cartoon'])

    def test_style_canon_from_library(self):
        prompts, _ = compose()
        lib = tg._load_lib()
        self.assertIn(lib['NST-B'], prompts['webtoon'])       # 극화 = 13_style_news_canon 런타임 병기
        self.assertIn(lib['NST-A'], prompts['watercolor'])

    def test_satire_caps_and_target(self):
        prompts, _ = compose()   # 공인 없음 · 권력어 없음 → 수위 2 → 만평 2·극화 2·수채·포토 1
        self.assertIn('SATIRE (measured): the target is the claim or policy idea named in HOOK', prompts['cartoon'])
        self.assertIn('SATIRE (measured)', prompts['webtoon'])
        self.assertIn('IRONY (gentle', prompts['photo'])
        self.assertIn('IRONY (gentle', prompts['watercolor'])
        prompts, _ = compose(target='자유에 값을 매기는 발상', insight='정부의 저출산 대책 공백이 개인을 서로의 채권자로 만들었다')
        self.assertIn('SATIRE: the target is 자유에 값을 매기는 발상', prompts['cartoon'])   # 권력어(정부) → 3 · 만평만 3
        self.assertIn('SATIRE (measured): the target is 자유에 값을 매기는 발상', prompts['webtoon'])
        self.assertIn('IRONY (gentle', prompts['photo'])

    def test_sensitive_tags_disable_satire(self):
        prompts, _ = compose(tags='#재난참사 #추모')
        for sid, p in prompts.items():
            self.assertIn('TONE: no satire', p, sid)
            self.assertNotIn('SATIRE', p.replace('GOVERNING_SATIRE', ''), sid)

    def test_dispatch_fallback_from_curation_table(self):
        prompts, parsed = compose(dispatch='', emotion='비통함과 상실감이 1순위')
        self.assertTrue(parsed['dispatch_fallback'].startswith('S08'), parsed['dispatch_fallback'])   # 16 CD-01 첫 대안
        self.assertIn('LIGHT: ', prompts['photo'])
        _, parsed2 = compose(dispatch='', emotion='')
        self.assertEqual(parsed2['dispatch_fallback'], '')   # 매치 0 = 화풍 기본 폴백(종전 동작)

    def test_korean_props_from_library(self):
        prompts, _ = compose(scene='국회 본회의장에서 굳은 얼굴로 표결 버튼을 누르는 50대 남성 의원, 흐린 오후')
        lib = tg._load_lib()
        self.assertIn('PROPS & SETTING', prompts['photo'])
        self.assertIn(lib['KR-14'], prompts['photo'])
        prompts, _ = compose(scene='부적절한 발언을 한 40대 남성이 고개를 숙인 저녁')
        self.assertNotIn(lib['KR-32'], prompts['photo'])   # '부적'(2자) 오탐 차단

    def test_cartoon_metaphor_and_structure(self):
        prompts, _ = compose(metaphor='거대한 저울 한쪽에 텅 빈 유모차, 다른 쪽에 세금 고지서 뭉치')
        self.assertIn('METAPHOR (the visual substitution', prompts['cartoon'])
        self.assertNotIn(tg.CARTOON_DEVICES, prompts['cartoon'])
        self.assertIn('STAGING (adapt this motif to the metaphor', prompts['cartoon'])   # SG-08(dispatch) 계승
        prompts, _ = compose(insight='정부의 위선이 드러났다 — 말과 행동이 다르다')
        self.assertIn(tg.CARTOON_DEVICES, prompts['cartoon'])
        self.assertIn('DEVICE (commentary structure to lean on): Two-Faced Duality', prompts['cartoon'])   # 48 CS-07

    def test_sanity_predicates_and_determinism(self):
        a, _ = compose(); b, _ = compose()
        self.assertEqual(a, b)
        for sid, p in a.items():
            cam = next((x for x in p.split('\n') if x.startswith('CAMERA:')), '')
            self.assertTrue(cam, sid)
            self.assertNotIn('순위', next((x for x in p.split('\n') if x.startswith('MOOD')), ''), sid)
            self.assertNotIn('REFERENCE FACE', p, sid)   # 참조 얼굴은 process_one 이 극화·수채에만 프리픽스

    def test_dry_run_cli(self):
        import subprocess
        with tempfile.TemporaryDirectory() as d:
            md = Path(d) / '260908-0000-cli.md'
            md.write_text(FM.format(**BASE), encoding='utf-8')
            out = Path(d) / 'p.json'
            r = subprocess.run([sys.executable, str(ROOT / '.github/scripts/thumb_gen.py'), '--dry', str(md), '--json', str(out)],
                               capture_output=True, text=True, timeout=60, env=dict(os.environ, GEMINI_API_KEY=''))
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn('=== cartoon (시사만평)', r.stdout)
            self.assertTrue(out.exists())


if __name__ == '__main__':
    unittest.main()
