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
        """윗변 = 어센트선 · 아랫변 = 디센트 + pad 를 pad/2 보더 + pad/2 그림자로(단일 합성) — 260812 기하 보존."""
        a = ly_burn.build_ass(SEG, 540, 960, dict(BOX, hi=True))
        box = text_of([l for l in dialogues(a) if layer(l) == 0][0])
        fs = max(18, int(960 * 0.05))
        half = ly_burn.ass_px(fs * 0.16 / 2.0)
        self.assertIn("{\\ybord%s\\xshad0\\yshad%s\\3a&HFF&\\1a&HFF&}" % (half, half), box)

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
        self.assertIn('csp_out = ["-colorspace", sub_tag] if ass else []', src)
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


def _box_profile(raw, w=540, h=960):
    """(열별 박스 윗변 y, 이중 합성 픽셀 수, 박스 픽셀 수) — 배경 회색(128) 위 반투명 박스 44% = 71(1중) · 40(2중)."""
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
                if r < 55:
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
        for t in (0.1, 0.9, 1.7):
            top, dbl, box = _box_profile(_render(p, t))
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


if __name__ == '__main__':
    unittest.main()
