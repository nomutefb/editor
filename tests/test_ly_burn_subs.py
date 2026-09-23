#!/usr/bin/env python3
"""ly_burn 자막 합성 회귀 3축(운영자 260913 지시 · run 34744684907 실측 봉합).

① 강조 박스 안정 — 「강조 들어갈 때마다 배경이 조금씩 튀어나온다」: 강조 어절 뒤 `{\\r}`(스타일 전체 리셋)이 줄 선두 박스 태그를
   풀어 박스 윗변이 어절마다 계단졌고, libass 가 색·크기 태그마다 런을 쪼개 반투명 박스에 줄무늬·부풀기가 생겼다.
   → box 모양 = 박스 레이어(layer 0 · 글자 투명 · 태그 0 · 조각당 1개) + 글자 레이어(layer 1 · \\bord0\\shad0) · 강조 복귀 = \\1c 글자색.
② 자막 색 정합 — 「이미지 강조색(그린 #0FFD02)이 아니라 더 어두운 색」: ffmpeg 6.1 `ass` 필터가 자막 RGB→YUV 를 BT.601 고정 변환
   → BT.709/2020 재생에서 (0,216,0) 으로 어두워짐. → 자막 합성만 원본 매트릭스로 RGB 왕복(ass_chain) + -colorspace 태그.
③ 해상도 — 「HD 로 강제 다운그레이드」: 결측 = 자막 단독 폭 1080 캡 / 편집 축 긴 변 1920 캡 · 'src' 도 0 이 거짓이라 같은 캡.
   → 결측 = QHD 이하 원본 유지(4K급만 1920) · 'src' = 무캡.
검사: ASS 산출 구조(의존성 0) + ffmpeg 실렌더(있을 때만 · 박스 윤곽 프레임 간 불변·단일 합성 · 그린 709 복원).
"""
import inspect
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, '.github', 'scripts'))
sys.path.insert(0, os.path.join(ROOT, 'shared'))
os.environ.setdefault('OPTS', '{}')
import ly_burn  # noqa: E402

WORDS = ["Alpha", "beta", "gamma", "delta", "epsilon"]
SEG = [{"s": 0.0, "e": 2.0, "ko": " ".join(WORDS),
        "w": [{"s": i * 0.4, "e": (i + 1) * 0.4, "t": w} for i, w in enumerate(WORDS)]}]
SEG_DUAL = [dict(SEG[0], src="the box stays put")]
BOX = {"shtype": "box", "bg": 44, "pad": 0.16, "size": 0.05}


def dialogues(ass):
    return [l for l in ass.splitlines() if l.startswith("Dialogue:")]


def text_of(line):
    return line.split(",", 9)[9]


def main_part(line):
    return text_of(line).split("\\N{\\fs")[0].split("\\N{\\r}")[0]   # 원문(dual) 줄 앞까지 = 본선(한글) 부분


def layer(line):
    return int(line.split(",", 1)[0].split(":")[1])


class BoxLayers(unittest.TestCase):
    def test_highlight_never_resets_style(self):
        """강조 어절 뒤 \\r 금지 — 줄 선두 태그(박스·글로우)가 풀리던 자리(260913 실사고 원인)."""
        for opts in ({"hi": True}, {"pop": True}, {"karaoke": False, "keyword": True}):
            a = ly_burn.build_ass([dict(SEG[0], ko="Alpha *beta* gamma")], 540, 960, dict(BOX, **opts))
            for l in dialogues(a):
                self.assertNotIn("\\r", main_part(l), l)
            self.assertIn("{\\1c&HFFFFFF&}", a, "강조 뒤 복귀는 글자색 \\1c 슬롯")

    def test_box_mode_splits_box_and_text_layers(self):
        a = ly_burn.build_ass(SEG, 540, 960, dict(BOX, hi=True))
        ev = dialogues(a)
        l0 = [l for l in ev if layer(l) == 0]
        l1 = [l for l in ev if layer(l) == 1]
        self.assertEqual(len(l0), 1, "박스 레이어 = 조각당 1개(강조 창 전부를 덮는 한 장)")
        self.assertEqual(len(l1), len(WORDS), "글자 레이어 = 어절 창마다")
        box = text_of(l0[0])
        self.assertIn("\\3a&HFF&\\1a&HFF&", box, "박스 레이어 = 박스·글자 투명 → 그림자(=박스)만 보인다")
        self.assertIn("\\ybord", box)
        self.assertIn("\\yshad", box)
        for tag in ("\\1c", "\\fscx", "\\kf", "\\bord0"):
            self.assertNotIn(tag, box, "박스 레이어엔 색·크기·타이밍 태그 0 = libass 런 1개 = 박스 1장")
        for l in l1:
            self.assertTrue(text_of(l).startswith("{\\bord0\\shad0}"), "글자 레이어 = 박스·그림자 없음")
        # 시간 범위: 박스 = 글자 창 전체 [첫 시작, 마지막 끝]
        self.assertEqual(l0[0].split(",")[1], l1[0].split(",")[1])
        self.assertEqual(l0[0].split(",")[2], l1[-1].split(",")[2])
        # 배치 동일: 같은 MarginV · 같은 어절
        self.assertEqual(l0[0].split(",")[7], l1[0].split(",")[7])
        for w in WORDS:
            self.assertIn(w, box)

    def test_half_pad_shadow_geometry(self):
        """박스 = pad/2 보더 박스(투명)의 그림자(단일 합성) · 높이 fs×(1+pad) · 그림자 오프셋 = 글자 크기 × BOX_K(한글 잉크 가운데 · 260923)."""
        fs = max(18, int(960 * 0.05))
        half = ly_burn.ass_px(fs * 0.16 / 2.0)
        for font in ("gothic", "pretendard", "jua"):
            a = ly_burn.build_ass(SEG, 540, 960, dict(BOX, hi=True, font=font))
            box = text_of([l for l in dialogues(a) if layer(l) == 0][0])
            dy = ly_burn._shad_y(fs * ly_burn.BOX_K[font])
            self.assertIn("{\\ybord%s\\xshad0\\yshad%s\\3a&HFF&\\1a&HFF&}" % (half, dy), box, font)
        a = ly_burn.build_ass(SEG, 540, 960, dict(BOX, hi=True, font="nope"))
        self.assertIn("\\yshad%s\\3a" % ly_burn._shad_y(fs * ly_burn.BOX_K["gothic"]), a, "미지 폰트 = 고딕 폴백(스타일 Fontname 과 같은 규칙)")

    def test_shadow_offset_never_zero(self):
        """libass 는 그림자 오프셋 (0,0) 이면 그림자를 안 그린다(실측 260923 = 박스 증발) → 0 으로 반올림되면 0.1."""
        for v in (0.0, 0.04, -0.04, -0.0):
            self.assertEqual(ly_burn._shad_y(v), 0.1)
        self.assertEqual(ly_burn._shad_y(-3.75), -3.8, "음수(위로) 그대로")
        self.assertEqual(ly_burn._shad_y(3.6), 3.6)
        a = ly_burn.build_ass(SEG, 540, 960, dict(BOX, pad=0.0, font="pretendard"))
        self.assertNotIn("\\yshad0\\", a.replace("\\yshad0.", "x"), "오프셋 0 태그 금지")

    def test_multiline_box_keeps_seams_and_shifts_together(self):
        """여러 줄 = 앞 줄 [어센트, 디센트] 상자 그림자(dy − pad/2) + 끝 줄 pad/2 보더 그림자(dy) · 박스(\\3a)는 끝까지 투명."""
        long_ko = "가나다라 마바사아 자차카타 파하가나 다라마바 사아자차 카타파하"
        fs = max(18, int(960 * 0.05))
        half = ly_burn.ass_px(fs * 0.16 / 2.0)
        a = ly_burn.build_ass([{"s": 0.0, "e": 2.0, "ko": long_ko}], 540, 960, dict(BOX, karaoke=False, font="pretendard"))
        box = text_of([l for l in dialogues(a) if layer(l) == 0][0])
        self.assertIn("\\N", box, "검사 전제 = 2줄 이상")
        m_fs = fs
        for tag in box.split("}"):
            if "\\fs" in tag:
                m_fs = int(tag.split("\\fs")[1].split("\\")[0])
        dy = m_fs * ly_burn.BOX_K["pretendard"]
        self.assertIn("{\\ybord0\\yshad%s}" % ly_burn._shad_y(dy - half), box)
        self.assertIn("\\N{\\ybord%s\\yshad%s}" % (half, ly_burn._shad_y(dy)), box)
        self.assertEqual(box.count("\\3a&H"), 1, "박스 투명(\\3a&HFF&) 한 번뿐 = 박스 자체는 어느 줄에서도 안 보인다(그림자만)")

    def test_box_k_matches_fonts_and_viewer(self):
        """BOX_K = 러너 폰트 집합과 같은 키 · 뷰어 FONT_PV.bk 와 같은 값(미리보기 = 같은 산식)."""
        import re
        self.assertEqual(set(ly_burn.BOX_K), set(ly_burn.FONT_FAMILY))
        html = open(os.path.join(ROOT, 'viewer', 'edit.html'), encoding='utf-8').read()
        pv = dict((k, float(v)) for k, v in re.findall(r"\n  (\w+):\{lbl:'[^']*',lh:[0-9.]+,dsc:[0-9.]+,bk:(-?[0-9.]+),", html))
        entries = re.findall(r"\n  (\w+):\{lbl:", html)
        self.assertGreaterEqual(len(pv), 9, pv)
        self.assertEqual(sorted(pv), sorted(entries), "FONT_PV 모든 항목 = {lbl,lh,dsc,bk,…} 순서로 세 값 보유(빠지면 미리보기가 lh 1·bk 0 으로 조용히 틀어진다)")
        for k, v in pv.items():
            self.assertIn(k, ly_burn.BOX_K, k)
            self.assertAlmostEqual(v, ly_burn.BOX_K[k], places=4, msg=k)

    def test_viewer_line_metrics_match_repo_fonts(self):
        """FONT_PV.lh·dsc = 러너 폰트 파일의 OS/2 윈 수치(레포 동봉 5종 = 의존성 0 · struct 파싱)."""
        import re
        import struct
        html = open(os.path.join(ROOT, 'viewer', 'edit.html'), encoding='utf-8').read()
        pv = dict((k, (float(a), float(b))) for k, a, b in re.findall(r"\n  (\w+):\{lbl:'[^']*',lh:([0-9.]+),dsc:([0-9.]+),", html))
        files = {"pretendard": "Pretendard-Bold.otf", "paper": "Paperlogy-5Medium.ttf", "plex": "IBMPlexSansKR-Bold.ttf",
                 "jua": "Jua-Regular.ttf", "gowun": "GowunDodum-Regular.ttf"}
        self.assertEqual(set(files), set(ly_burn.REPO_FONT_KEYS), "레포 동봉 폰트를 늘리면 여기 파일명도 1줄(= lh·dsc 대조 대상)")
        for k, fn in files.items():
            with open(os.path.join(ROOT, 'assets', 'fonts', 'subs', fn), 'rb') as fh:
                data = fh.read()
            n = struct.unpack('>H', data[4:6])[0]
            tab = {data[12 + 16 * i:16 + 16 * i].decode('latin-1'): struct.unpack('>I', data[20 + 16 * i:24 + 16 * i])[0] for i in range(n)}
            upem = struct.unpack('>H', data[tab['head'] + 18:tab['head'] + 20])[0]
            wa, wd = struct.unpack('>HH', data[tab['OS/2'] + 74:tab['OS/2'] + 78])
            self.assertAlmostEqual(pv[k][0], (wa + wd) / upem, places=3, msg=k + " lh")
            self.assertAlmostEqual(pv[k][1], wd / (wa + wd), places=3, msg=k + " dsc")

    def test_generator_reproduces_repo_values(self):
        """BOX_K·FONT_PV = shared/sub_font_metrics.py 출력(생성 코드 = 정본) — fontTools·폰트 파일이 있는 환경에서만(CI 밖 = 건너뜀)."""
        try:
            import fontTools  # noqa: F401
        except ImportError:
            self.skipTest('fontTools 없음(개발용 생성기)')
        sys.path.insert(0, os.path.join(ROOT, 'shared'))
        import sub_font_metrics
        import contextlib
        import io
        with contextlib.redirect_stdout(io.StringIO()) as out:
            rc = sub_font_metrics.main(['--check'])
        self.assertEqual(rc, 0, out.getvalue())

    def test_pop_scale_only_in_text_layer(self):
        a = ly_burn.build_ass(SEG, 540, 960, dict(BOX, pop=True))
        ev = dialogues(a)
        self.assertTrue(all("\\fscx" in text_of(l) for l in ev if layer(l) == 1), "팝 = 글자 레이어에만 크기 튐")
        self.assertFalse(any("\\fscx" in text_of(l) for l in ev if layer(l) == 0), "박스는 부풀지 않는다")

    def test_karaoke_box_layers(self):
        a = ly_burn.build_ass(SEG, 540, 960, dict(BOX, karaoke=True))
        ev = dialogues(a)
        self.assertEqual([layer(l) for l in ev], [1, 0])
        self.assertIn("\\kf", text_of(ev[0]))
        self.assertNotIn("\\kf", text_of(ev[1]))

    def test_glow_goes_to_box_layer_only(self):
        a = ly_burn.build_ass(SEG, 540, 960, dict(BOX, hi=True, glow=50))
        ev = dialogues(a)
        self.assertTrue(all("\\blur" in text_of(l) for l in ev if layer(l) == 0))
        self.assertFalse(any("\\blur" in text_of(l) for l in ev if layer(l) == 1), "보더 0 글자에 \\blur 를 붙이면 글리프가 흐려진다")

    def test_dual_ghost_keeps_layout_and_hides_source_box(self):
        a = ly_burn.build_ass(SEG_DUAL, 540, 960, dict(BOX, hi=True, lang="dual", dual_small=0.5, dual_gap=0.18))
        ev = dialogues(a)
        box = text_of([l for l in ev if layer(l) == 0][0])
        txt = text_of([l for l in ev if layer(l) == 1][0])
        self.assertEqual(box.count("\\N"), txt.count("\\N"), "박스 레이어 = 같은 줄 수(배치 동일)")
        self.assertIn("{\\1a&HFF&\\3a&HFF&\\4a&HFF&}the box stays put", box, "원문 줄은 박스 레이어에서 전부 투명(원문 박스는 글자 레이어 1회)")
        self.assertIn("{\\shad1}{\\blur0}{\\1a&H00&}{\\3a&H00&}{\\4a&H60&}the box stays put", txt)

    def test_non_box_shapes_unchanged_single_layer(self):
        for sh in ("stroke", "shadow", "none"):
            a = ly_burn.build_ass(SEG, 540, 960, {"shtype": sh, "bg": 0, "size": 0.05, "hi": True})
            ev = dialogues(a)
            self.assertEqual(len(ev), len(WORDS))
            self.assertTrue(all(layer(l) == 0 for l in ev), sh)
            self.assertFalse(any("\\bord0\\shad0" in text_of(l) for l in ev), sh)


class SubColorChain(unittest.TestCase):
    def test_sub_matrix_follows_source_tag_or_hd_default(self):
        self.assertEqual(ly_burn.sub_matrix("bt709", "tv", 1080, 1920), ("bt709", "tv", "bt709"))
        self.assertEqual(ly_burn.sub_matrix("bt2020nc", "tv", 1440, 2560), ("bt2020", "tv", "bt2020nc"), "HLG 폰 원본 = 2020 매트릭스 왕복 · 태그 원본 그대로")
        self.assertEqual(ly_burn.sub_matrix("", "", 1080, 1920), ("bt709", "tv", "bt709"), "미지 HD = 709")
        self.assertEqual(ly_burn.sub_matrix("", "", 640, 480), ("smpte170m", "tv", "smpte170m"), "미지 SD = 601")
        self.assertEqual(ly_burn.sub_matrix("bt709", "pc", 1280, 720)[1], "pc")

    def test_ass_chain_round_trips_with_same_matrix(self):
        c = ly_burn.ass_chain("/tmp/x.ass", "bt2020", "tv")
        self.assertTrue(c.startswith("scale=in_color_matrix=bt2020:in_range=tv:"))
        self.assertIn(",format=gbrp,ass=/tmp/x.ass,scale=out_color_matrix=bt2020:out_range=tv:", c)
        self.assertTrue(c.endswith(",format=yuv420p"))

    def test_cut_filter_uses_chain(self):
        fc = ly_burn.cut_filter([(0.0, 1.0)], False, "scale=1080:1920", "/tmp/x.ass", ass_vf=ly_burn.ass_chain("/tmp/x.ass"))
        self.assertIn("scale=1080:1920,scale=in_color_matrix=bt709", fc)
        self.assertIn("ass=/tmp/x.ass,scale=out_color_matrix=bt709", fc)
        self.assertIn("ass=/tmp/x.ass[vo]", ly_burn.cut_filter([(0.0, 1.0)], False, "", "/tmp/x.ass"), "ass_vf 결측 = 종전 직결")

    def test_run_wires_chain_and_colorspace_tag(self):
        src = inspect.getsource(ly_burn.run)
        self.assertIn("ass_vf = ass_chain(ass_path, sub_m, sub_r)", src)
        self.assertIn('csp_out = (["-colorspace", sub_tag] if (ass or sdrf) else [])', src)
        self.assertNotIn('"ass={}".format(ass_path) if ass else ""', src, "번인 -vf 는 왕복 체인만(601 직결 금지)")
        self.assertIn("format=rgba", src, "오버레이 webm 캔버스 = RGBA")


class ResolutionCap(unittest.TestCase):
    def test_default_cap_keeps_up_to_qhd(self):
        self.assertEqual(ly_burn.default_cap(1440, 2560), 0, "폰 QHD = 원본 유지")
        self.assertEqual(ly_burn.default_cap(2560, 1440), 0)
        self.assertEqual(ly_burn.default_cap(1920, 1080), 0, "가로 FHD = 종전 1080×608 강등 금지")
        self.assertEqual(ly_burn.default_cap(1080, 1920), 0)
        self.assertEqual(ly_burn.default_cap(3840, 2160), 1920, "4K급만 종전대로 1920")
        self.assertEqual(ly_burn.default_cap(2160, 3840), 1920)

    def test_run_has_no_width_1080_cap_and_honours_src(self):
        src = inspect.getsource(ly_burn.run)
        self.assertNotIn("if tw > 1080", src, "자막 단독 경로 폭 1080 캡 폐지")
        self.assertIn('vid_src = _res_key == "src"', src)
        self.assertIn("cap = 0 if vid_src else default_cap(cw, ch)", src)
        self.assertIn("cap = vid_res if vid_res else (0 if vid_src else default_cap(cw, ch))", src)
        self.assertNotIn("dict(_RES_LADDER, src=0).get", src, "'src' 를 0 으로 두면 `or None` 에서 결측과 합쳐진다(구 결함 코드형)")


def _render(ass_path, t, w=540, h=960):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi",
                          "-i", "color=c=gray:s={}x{}:r=30:d=2,format=yuv420p".format(w, h),   # d=2 = SEG 전체(0~2s) 커버
                          "-vf", "ass={}".format(ass_path), "-ss", str(t), "-frames:v", "1",
                          "-pix_fmt", "rgb24", "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
    return raw


def _ink_mask(raw, w=540, h=960):
    """글자(흰·강조색) 잉크와 그 1px 둘레 — 밝거나 색이 있는 픽셀(회색 배경 128 제외)."""
    ink = set()
    for y in range(h // 2, h):
        row = raw[y * w * 3:(y + 1) * w * 3]
        for x in range(w):
            r, g, b = row[3 * x], row[3 * x + 1], row[3 * x + 2]
            if (r, g, b) != (128, 128, 128) and (r >= 120 or abs(r - g) >= 4 or abs(g - b) >= 4):
                ink.update((x + dx, y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1))
    return ink


def _box_profile(raw, w=540, h=960, mask=frozenset()):
    """(열별 박스 윗변 y, 이중 합성 픽셀 수, 박스 픽셀 수) — 배경 회색(128) 위 반투명 박스 44% = 71(1중) · 40(2중).
    mask = 이중 합성 집계에서 뺄 자리(전 프레임 글자 잉크 합집합 · 260923) — 박스 중심 보정으로 줄 이음새가 글자 가장자리와 겹치면 그 안티에일리어싱 픽셀이
    강조 색(흰↔그린)에 따라 어두운 회색으로 잡혔다 안 잡혔다 했다(실측 540×960: 이음새 행 2픽셀 · 박스 자체는 프레임 간 동일). 프레임 공통 마스크라 비교가 공정하다."""
    top, dbl, box = {}, 0, 0
    for y in range(h // 2, h):
        row = raw[y * w * 3:(y + 1) * w * 3]
        for x in range(w):
            r, g, b = row[3 * x], row[3 * x + 1], row[3 * x + 2]
            if (r, g, b) == (128, 128, 128):
                continue
            top.setdefault(x, y)
            if abs(r - g) < 4 and abs(g - b) < 4 and r < 120:
                box += 1
                if r < 55 and (x, y) not in mask:
                    dbl += 1
    return top, dbl, box


@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('fc-match'), 'ffmpeg/fontconfig 없음')
class BoxRender(unittest.TestCase):
    def test_box_outline_stable_across_highlight_frames(self):
        d = tempfile.mkdtemp()
        p = os.path.join(d, 't.ass')
        with open(p, 'w', encoding='utf-8') as f:
            f.write(ly_burn.build_ass(SEG, 540, 960, dict(BOX, hi=True)))
        profiles, dbls, boxes = [], [], []
        raws = [_render(p, t) for t in (0.1, 0.9, 1.7)]
        mask = set().union(*(_ink_mask(r) for r in raws))
        for raw in raws:
            top, dbl, box = _box_profile(raw, mask=mask)
            profiles.append(top); dbls.append(dbl); boxes.append(box)
        if not profiles[0]:
            self.skipTest('libass 가 쓸 폰트가 없는 환경(렌더 픽셀 0) — 구조 검사는 위 BoxLayers 가 담당')
        self.assertEqual(profiles[0], profiles[1], '강조 어절이 바뀌어도 박스 윗변은 열마다 동일해야 한다(260913 계단 재발 금지)')
        self.assertEqual(profiles[1], profiles[2])
        self.assertEqual(len(set(dbls)), 1, '강조 위치에 따라 진해지는 자리가 있으면 안 된다(런 경계 줄무늬 재발 금지): %r' % (dbls,))
        # 2줄 텍스트 = 줄 경계 반올림 1행(pad/2 그림자 3.8+3.8 vs 7.7)만 허용 — 런 경계 줄무늬·박스+그림자 전면 겹침(구 24~69%)은 이 상한을 크게 넘는다
        self.assertLess(dbls[0], boxes[0] * 0.02, '반투명 박스 이중 합성 픽셀 %d / 박스 %d' % (dbls[0], boxes[0]))


@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'ffmpeg 없음')
class SubColorRender(unittest.TestCase):
    ASS = ("[Script Info]\nScriptType: v4.00+\nPlayResX: 320\nPlayResY: 240\n\n[V4+ Styles]\n"
           "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
           "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
           "Style: g,Sans,20,&H0002FD0F,&H0002FD0F,&H0002FD0F,&H0002FD0F,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1\n\n[Events]\n"
           "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
           "Dialogue: 0,0:00:00.00,0:00:01.00,g,,0,0,0,,{\\an7\\pos(40,40)\\p1}m 0 0 l 200 0 200 120 0 120{\\p0}\n")   # 벡터 사각형 = 폰트 불요

    def _burn(self, d, vf, extra):
        src = os.path.join(d, 's.mp4')
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=gray:s=320x240:r=30:d=0.5,format=yuv420p",
                        "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-c:v", "libx264", "-crf", "10", src], check=True)
        out = os.path.join(d, 'o.mp4')
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vf", vf, "-c:v", "libx264", "-crf", "10", "-pix_fmt", "yuv420p"] + extra + [out], check=True)
        raw = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", out, "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "yuv444p", "-"], capture_output=True, check=True).stdout
        W, H = 320, 240
        x, y = 140, 100
        Y, U, V = raw[y * W + x], raw[W * H + y * W + x], raw[2 * W * H + y * W + x]
        yp, cb, cr = (Y - 16) / 219 * 255, (U - 128) / 224 * 255, (V - 128) / 224 * 255
        rgb709 = (yp + 1.5748 * cr, yp - 0.1873 * cb - 0.4681 * cr, yp + 1.8556 * cb)   # 재생기(BT.709 태그) 복원값
        tag = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=color_space", "-of", "csv=p=0", out],
                             capture_output=True, text=True).stdout.strip()
        return tuple(int(max(0, min(255, round(c)))) for c in rgb709), tag

    def test_green_survives_709_playback(self):
        d = tempfile.mkdtemp()
        p = os.path.join(d, 't.ass')
        with open(p, 'w', encoding='utf-8') as f:
            f.write(self.ASS)
        m, r, tag = ly_burn.sub_matrix("bt709", "tv", 320, 240)
        rgb, tag_out = self._burn(d, ly_burn.ass_chain(p, m, r), ["-colorspace", tag])
        for got, want in zip(rgb, (15, 253, 2)):
            self.assertLessEqual(abs(got - want), 6, "콘텐츠 그린 #0FFD02 가 709 재생에서 %r 로 복원돼야 한다" % (rgb,))
        self.assertEqual(tag_out, "bt709", "출력 매트릭스 태그 동봉")
        # 종전 직결(ass=)은 ffmpeg 6.x 에서만 601 고정이라 어두운 그린(≈216)이 재현된다(실사고 재현 = 이 검사의 분별력 증명) —
        #   7.0 부터는 vf_subtitles 가 입력 색공간을 따르므로 직결도 맞게 나온다 → 그 환경에선 이 대조를 건너뛴다(왕복 체인은 어느 버전에서도 정합).
        ver = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True).stdout.split("\n")[0]
        major = int((ver.split("version", 1)[1].strip().split(".")[0] or "0").lstrip("n") or 0) if "version" in ver else 0
        if 0 < major < 7:
            legacy, _ = self._burn(d, "ass={}".format(p), [])
            self.assertLess(legacy[1], 230, "구 경로는 6.x 에서 그린이 어두워져야(≈216) 이 검사가 의미 있다: %r" % (legacy,))



class SdrChain(unittest.TestCase):
    """편집기 「SDR 변환」(운영자 260913 제안 승인) — HDR 판별·체인 모양·run 배선."""
    def test_hdr_kind(self):
        self.assertEqual(ly_burn.hdr_kind("arib-std-b67", "bt2020"), "HLG")
        self.assertEqual(ly_burn.hdr_kind("smpte2084", "bt2020"), "PQ")
        self.assertIsNone(ly_burn.hdr_kind("bt709", "bt709"))
        self.assertIsNone(ly_burn.hdr_kind("", "bt2020"), "원색만 2020 = 추측 금지(변환 생략 note)")

    def test_sdr_chain_shapes(self):
        c = ly_burn.sdr_chain("HLG", "tv", "bt2020nc")
        self.assertTrue(c.startswith("setparams=colorspace=bt2020nc:color_primaries=bt2020:color_trc=arib-std-b67:range=tv,"
                                     "zscale=t=linear:npl=1000,format=gbrpf32le,exposure=exposure=2.3,"),
                        "HLG = 프로브값 도장(태그 의존 금지) + 1000nit 선형 + 203nit→백색 노출: " + c)
        self.assertIn("zscale=p=bt709,tonemap=tonemap=mobius:param=0.75:desat=0:peak=4.926,", c)
        self.assertTrue(c.endswith("zscale=t=bt709:m=bt709:r=tv,format=yuv420p"))
        self.assertTrue(ly_burn.sdr_chain("PQ").startswith("setparams=colorspace=bt2020nc:color_primaries=bt2020:color_trc=smpte2084:range=tv,"
                                                           "zscale=t=linear:npl=203,format=gbrpf32le,zscale=p=bt709"), "PQ = 절대휘도 203nit 스케일(노출 불요)")
        self.assertIn("setparams=colorspace=bt2020c:color_primaries=bt2020:color_trc=arib-std-b67:range=pc,", ly_burn.sdr_chain("HLG", "pc", "bt2020c"), "레인지·CL 매트릭스는 프로브값 추종")
        self.assertEqual(ly_burn.sdr_chain(None), "")

    def test_run_wiring(self):
        src = inspect.getsource(ly_burn.run)
        for frag in ('sdr_on = bool(opts.get("vid_sdr"))', 'sdrf = sdr_chain(hdr_k, _rng, _csp) if sdr_on else ""',
                     'sub_m, sub_r, sub_tag = "bt709", "tv", "bt709"', '"-color_primaries", "bt709", "-color_trc", "bt709"',
                     'padf, sarf, sdrf]', 'or sdr_on)', 'SDR 변환 생략'):
            self.assertIn(frag, src, frag)
        self.assertIn("vid_sdr", ly_burn.EDIT_KEYS, "재입히기 승계 대상")


@unittest.skipUnless(shutil.which('ffmpeg'), 'ffmpeg 없음')
class SdrRender(unittest.TestCase):
    def test_hlg_to_sdr_keeps_midtones_and_white(self):
        """합성 HLG(확산 백색 = 75% 신호) → sdr_chain → 중간톤·백색 복원 + 1000nit 하이라이트는 흰색(표준 hable 레시피의 12% 어두워짐 재발 금지)."""
        flt = subprocess.run(['ffmpeg', '-hide_banner', '-filters'], capture_output=True, text=True).stdout
        if 'zscale' not in flt or 'tonemap' not in flt or 'exposure' not in flt:
            self.skipTest('zscale/tonemap/exposure 필터 없음')
        d = tempfile.mkdtemp()
        hlg = os.path.join(d, 'hlg.mp4')
        # SDR 회색(0x808080) 바탕 + 왼쪽 위 SDR 백색 패치 → 선형 ×0.203 → HLG · 오른쪽 위 = 선형 1.0(=1000nit) 패치
        mk = ("drawbox=x=8:y=8:w=40:h=30:c=white@1:t=fill,setparams=colorspace=bt709:color_primaries=bt709:color_trc=bt709:range=tv,zscale=t=linear:npl=100,format=gbrpf32le,exposure=exposure=-2.3,"
              "drawbox=x=112:y=8:w=40:h=30:c=white@1:t=fill,zscale=p=bt2020,zscale=t=arib-std-b67:m=2020_ncl:r=tv:npl=1000,format=yuv420p10le")
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'color=c=0x808080:s=160x120:r=10:d=0.3,format=yuv420p',
                        '-vf', mk, '-c:v', 'libx264', '-crf', '8', '-pix_fmt', 'yuv420p10le',
                        '-colorspace', 'bt2020nc', '-color_primaries', 'bt2020', '-color_trc', 'arib-std-b67', hlg], check=True)
        out = os.path.join(d, 'sdr.mp4')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', hlg, '-vf', ly_burn.sdr_chain('HLG'), '-c:v', 'libx264', '-crf', '8',
                        '-pix_fmt', 'yuv420p', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', out], check=True)
        raw = subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', out, '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'gray', '-'],
                             capture_output=True, check=True).stdout
        W = 160
        gray, white, hi = raw[80 * W + 80], raw[20 * W + 28], raw[20 * W + 132]
        self.assertLessEqual(abs(gray - 126), 5, '중간 회색(0x808080 → Y126)이 그대로 돌아와야 한다: %d' % gray)
        self.assertGreaterEqual(white, 215, 'SDR 백색 패치는 백색 근처로(≈222): %d' % white)
        self.assertGreaterEqual(hi, 228, '1000nit 하이라이트는 흰색으로 정착(회색 뭉개짐 금지): %d' % hi)
        tag = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=color_space,color_transfer,color_primaries',
                              '-of', 'csv=p=0', out], capture_output=True, text=True).stdout.strip()
        self.assertEqual(tag, 'bt709,bt709,bt709')


if __name__ == '__main__':
    unittest.main()
