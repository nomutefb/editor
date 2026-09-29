"""배경 빼기 통합(운영자 260929 «키잉·크로마키 하나로 · 5번» + «B 진짜 투명 재생기») — 행동 검사.
경로 고르기·옛 설정 이관 = 표준 라이브러리만(CI 상시) · 스크린 판별·섞기 합성 = cv2 있을 때 · 스택 미리보기 = ffmpeg 있을 때."""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github' / 'scripts'))
sys.path.insert(0, str(ROOT / 'apps' / 'track'))
import edit_track  # noqa: E402

HAS_CV = importlib.util.find_spec('cv2') is not None and importlib.util.find_spec('numpy') is not None
HAS_FF = bool(shutil.which('ffmpeg') and shutil.which('ffprobe'))


class Route(unittest.TestCase):
    SCR = {'kind': 'green', 'color': '#65DC08', 'frac': 0.99}

    def test_screen_with_person_mixes(self):
        self.assertEqual(edit_track.bgrm_route(self.SCR, 1, 6.0), ('keying', None))

    def test_screen_without_person_is_color_only_with_reason(self):
        m, why = edit_track.bgrm_route(self.SCR, 0, 6.0)
        self.assertEqual(m, 'chroma')
        self.assertIn('색으로만', why)

    def test_screen_too_long_is_color_only(self):
        m, why = edit_track.bgrm_route(self.SCR, 2, 200.0)
        self.assertEqual(m, 'chroma')
        self.assertIn('90초', why)

    def test_no_screen_person_is_ai(self):
        self.assertEqual(edit_track.bgrm_route(None, 3, 30.0), ('keying', None))

    def test_no_screen_too_long_is_honest_skip(self):
        m, why = edit_track.bgrm_route(None, 3, 120.0)
        self.assertIsNone(m)
        self.assertIn('잘라서', why)

    def test_no_screen_no_person_is_honest_skip(self):
        m, why = edit_track.bgrm_route(None, 0, 6.0)
        self.assertIsNone(m)
        self.assertIn('사람을 못 찾아서', why)

    def test_cap_edge_is_inclusive(self):   # 90초 + 1초 여유(track_keying 캡과 같은 판정)
        self.assertEqual(edit_track.bgrm_route(None, 1, 91.0)[0], 'keying')
        self.assertIsNone(edit_track.bgrm_route(None, 1, 91.5)[0])


class CapParity(unittest.TestCase):
    def test_key_max_sec_same_in_runner_and_engine(self):   # 러너 길 고르기와 엔진 거절이 같은 캡이어야(어긋나면 keying 으로 보냈다가 엔진이 거절)
        import re
        eng = (ROOT / 'apps' / 'track' / 'track_keying.py').read_text(encoding='utf-8')
        m = re.search(r'^KEY_MAX_SEC = (\d+)', eng, re.M)
        self.assertIsNotNone(m)
        self.assertEqual(int(m.group(1)), edit_track.KEY_MAX_SEC)


class LegacyOpts(unittest.TestCase):
    def test_old_keying_and_chroma_become_bgrm(self):
        for x in ({'keying': True}, {'chroma': True, 'ckcolor': 'green'}, {'bgrm': True}):
            on, _ = edit_track.norm_xtr({'xtr': x})
            self.assertTrue(on['bgrm'], x)
            self.assertNotIn('keying', on)
            self.assertNotIn('chroma', on)

    def test_nothing_on_is_none(self):
        self.assertIsNone(edit_track.norm_xtr({'xtr': {'keying': False, 'chroma': False}}))

    def test_mosaic_alone_does_not_turn_bgrm(self):
        on, _ = edit_track.norm_xtr({'xtr': {'mosaic': True}})
        self.assertFalse(on['bgrm'])


def _write_video(path, frames, fps=10):
    import cv2
    h, w = frames[0].shape[:2]
    vw = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))
    for f in frames:
        vw.write(f)
    vw.release()


@unittest.skipUnless(HAS_CV, 'cv2·numpy 없음')
class Screen(unittest.TestCase):
    def _clip(self, bg, person=(40, 40, 40), bottom=None, grad=None, vignette=0.0):
        import numpy as np
        fr = []
        for k in range(12):
            f = np.zeros((180, 320, 3), np.uint8)
            f[:] = bg
            if grad is not None:   # 위→아래 하늘 그라데이션(BGR 두 끝)
                a, b = np.array(grad[0], float), np.array(grad[1], float)
                for y in range(180):
                    f[y] = (a + (b - a) * y / 179).astype(np.uint8)
            if bottom is not None:
                f[120:] = bottom
            if vignette:   # 가장자리로 갈수록 어둡게(조명이 가운데만 센 촬영)
                yy, xx = np.mgrid[0:180, 0:320]
                r = np.sqrt(((xx - 160) / 160.0) ** 2 + ((yy - 90) / 90.0) ** 2) / np.sqrt(2)
                f = (f * (1 - vignette * r)[..., None]).astype(np.uint8)
            f[40:180, 120 + k:200 + k] = person
            fr.append(f)
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d, True)
        p = Path(d) / 'c.mp4'
        _write_video(p, fr)
        return p

    def test_green_screen(self):
        import track_chroma as tc
        r = tc.detect_screen(str(self._clip((40, 200, 90))))   # BGR = 초록 스크린(조명으로 살짝 푸름)
        self.assertIsNotNone(r)
        self.assertEqual(r['kind'], 'green')
        rr, gg, bb = (int(r['color'][i:i + 2], 16) for i in (1, 3, 5))
        self.assertTrue(gg > rr + 60 and gg > bb + 60, r)   # 실제 스크린 색(#00FF00 고정이 아님)

    def test_blue_screen(self):
        import track_chroma as tc
        r = tc.detect_screen(str(self._clip((220, 90, 20))))
        self.assertIsNotNone(r)
        self.assertEqual(r['kind'], 'blue')

    def test_gray_wall_is_not_screen(self):
        import track_chroma as tc
        self.assertIsNone(tc.detect_screen(str(self._clip((128, 128, 128)))))

    def test_grass_floor_only_is_not_screen(self):   # 아래 변은 몸통·바닥 자리라 판별에서 뺀다(잔디 바닥 = 스크린 아님)
        import track_chroma as tc
        self.assertIsNone(tc.detect_screen(str(self._clip((150, 140, 130), bottom=(40, 200, 90)))))

    def test_unreadable_is_none(self):
        import track_chroma as tc
        self.assertIsNone(tc.detect_screen('/nonexistent/x.mp4'))

    def test_sky_over_ground_is_not_blue_screen(self):   # 평의회 260929 실측 = 하늘·물이 파랑 스크린으로 오판 → 사람 옷이 빠졌다
        import track_chroma as tc
        self.assertIsNone(tc.detect_screen(str(self._clip((0, 0, 0), grad=((230, 110, 40), (235, 170, 120)), bottom=(60, 90, 110)))))

    def test_dim_edged_green_screen_keeps_key_gentle(self):   # 가장자리가 어두운 진짜 스크린 = 인정하되 강도를 낮춘다(흰 셔츠 보호)
        import track_chroma as tc
        r = tc.detect_screen(str(self._clip((64, 177, 0), vignette=0.35)))
        if r is not None:   # 너무 어두우면 None(AI 단독)도 안전 — 인정했다면 강도가 기본보다 낮거나 같아야 한다
            self.assertEqual(r['kind'], 'green')
            self.assertLessEqual(r['sim'], 0.15)

    def test_key_strength_never_reaches_neutral_or_skin(self):   # 판정된 키로 회색·피부가 절대 안 빠진다(거리 > 강도 + 경계 혼합)
        import track_chroma as tc
        for color in ('#65DC08', '#00B140', '#007526', '#002B7C', '#3BB271', '#8AC85B', '#278900'):
            sim = tc.screen_similarity(color)
            if sim is None:
                continue
            rgb = tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))
            for pix in ((128, 128, 128), (255, 255, 255), (20, 20, 20)) + tc.SCREEN_SKIN:
                self.assertGreater(tc._chroma_dist(rgb, pix), sim + 0.05, (color, pix))

    def test_washed_out_keys_are_refused(self):   # 회색·피부와 가까운 스크린 색 = 안전하게 못 뺀다 = 스크린 아님
        import track_chroma as tc
        for color in ('#5C85C0', '#449E4E', '#76B2D5'):
            self.assertIsNone(tc.screen_similarity(color), color)


@unittest.skipUnless(HAS_CV, 'cv2·numpy 없음')
class Mix(unittest.TestCase):
    def setUp(self):
        try:
            import track_keying  # noqa: F401 — thumb_gen·audio_norm 까지 따라온다
        except Exception as e:   # noqa: BLE001
            self.skipTest('track_keying import 불가: %s' % e)

    def test_outside_person_zone_is_transparent_even_if_chroma_keeps(self):
        import numpy as np
        import track_keying as tk
        ai = np.zeros((200, 200), np.uint8)
        ai[60:140, 60:140] = 255
        chroma = np.full((200, 200), 255, np.uint8)   # 크로마가 못 뺀 스탠드·주름(전부 불투명이라 가정)
        a = tk.mix_apply(tk.mix_zone(ai, 21), chroma)
        self.assertEqual(int(a[5, 5]), 0)          # 사람 영역 밖 = 무조건 투명(가비지 매트)
        self.assertEqual(int(a[100, 100]), 255)    # 사람 안 = 크로마 그대로

    def test_inside_zone_green_gap_is_removed(self):   # 260929 실측 사고 축 = 팔·몸 사이 틈의 초록이 도로 살던 판 차단
        import numpy as np
        import track_keying as tk
        ai = np.zeros((200, 200), np.uint8)
        ai[40:160, 40:160] = 255                   # AI가 틈까지 몸으로 잡았다
        chroma = np.full((200, 200), 255, np.uint8)
        chroma[90:110, 90:110] = 0                 # 그 틈 = 초록 스크린
        a = tk.mix_apply(tk.mix_zone(ai, 21), chroma)
        self.assertEqual(int(a[100, 100]), 0)

    def test_probe_flags_key_eating_the_body(self):   # 안전장치 = 크로마가 몸 안쪽을 빼면(옷 색 = 키 색) 손실이 크게 잡힌다
        import numpy as np
        import track_keying as tk
        ai = np.zeros((200, 200), np.uint8)
        ai[40:160, 60:140] = 255
        good = np.where(ai > 0, 255, 0).astype(np.uint8)   # 진짜 스크린 = 몸은 남고 둘레는 빠진다
        loss, band = tk.mix_probe(ai, good, 11, 31)
        self.assertLessEqual(loss, tk.MIX_CORE_LOSS_MAX)
        self.assertGreaterEqual(band, tk.MIX_BAND_MIN)
        bad = np.zeros((200, 200), np.uint8)               # 오판 = 몸까지 빠진다
        loss, band = tk.mix_probe(ai, bad, 11, 31)
        self.assertGreater(loss, tk.MIX_CORE_LOSS_MAX)
        halo = np.full((200, 200), 255, np.uint8)          # 둘레 배경이 스크린이 아니다 = 띠가 안 빠진다(후광)
        loss, band = tk.mix_probe(ai, halo, 11, 31)
        self.assertLess(band, tk.MIX_BAND_MIN)

    def test_probe_ignores_tiny_person(self):
        import numpy as np
        import track_keying as tk
        ai = np.zeros((200, 200), np.uint8)
        ai[100:102, 100:102] = 255
        self.assertIsNone(tk.mix_probe(ai, ai, 11, 31))

    def test_zone_reaches_hair_margin(self):   # 팽창 폭 안의 잔경계(머리카락)는 크로마 몫으로 남는다
        import numpy as np
        import track_keying as tk
        ai = np.zeros((200, 200), np.uint8)
        ai[60:140, 60:140] = 255
        chroma = np.zeros((200, 200), np.uint8)
        chroma[52:60, 90:110] = 200                # AI 마스크 바로 위 8px 머리카락(반투명)
        a = tk.mix_apply(tk.mix_zone(ai, 21), chroma)
        self.assertGreater(int(a[56, 100]), 150)


@unittest.skipUnless(HAS_FF, 'ffmpeg 없음')
class Stacked(unittest.TestCase):
    def test_stacked_layout_and_alpha(self):
        d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d, True)
        src = d / 'm.mov'
        # 알파 마스터 모사: 왼쪽 절반 불투명 · 오른쪽 절반 투명(640×360 · 1초)
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'color=c=red:s=640x360:d=1:r=10',
                        '-vf', "format=yuva444p,geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='if(lt(X,320),255,0)'",
                        '-c:v', 'prores_ks', '-profile:v', '4444', '-pix_fmt', 'yuva444p10le', str(src)], check=True)
        res = edit_track.make_stacked(str(src), str(d / 's.mp4'))
        self.assertIsNotNone(res)
        out, w, h = res
        self.assertEqual((w, h), (640, 360))
        pr = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height,codec_name',
                             '-of', 'json', out], capture_output=True, text=True, check=True)
        st = json.loads(pr.stdout)['streams'][0]
        self.assertEqual((st['codec_name'], st['width'], st['height']), ('h264', 640, 720))   # 위 = 색 · 아래 = 알파(세로 2배)

        def yavg(crop):
            r = subprocess.run(['ffmpeg', '-v', 'error', '-i', out, '-vf', crop + ',signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-',
                                '-frames:v', '1', '-f', 'null', '-'], capture_output=True, text=True)
            return float(r.stdout.split('YAVG=')[1].split()[0])
        self.assertTrue(225 < yavg('crop=300:340:10:370') < 240)   # 아래 절반 왼쪽 = 불투명 = 제한 범위 흰(235) — 0~255 그대로면 브라우저가 잘라 반투명이 뭉개진다
        self.assertTrue(10 < yavg('crop=300:340:330:370') < 22)    # 아래 절반 오른쪽 = 투명 = 제한 범위 검정(16)

    def test_broken_master_is_none(self):
        d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d, True)
        bad = d / 'bad.mov'
        bad.write_bytes(b'not a video')
        self.assertIsNone(edit_track.make_stacked(str(bad), str(d / 's.mp4')))


if __name__ == '__main__':
    unittest.main()
