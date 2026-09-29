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
    def _clip(self, bg, person=(40, 40, 40), bottom=None):
        import numpy as np
        fr = []
        for k in range(12):
            f = np.zeros((180, 320, 3), np.uint8)
            f[:] = bg
            if bottom is not None:
                f[120:] = bottom
            f[40:180, 120 + k:200 + k] = person
            fr.append(f)
        d = tempfile.mkdtemp()
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
        self.assertGreater(yavg('crop=300:340:10:370'), 230)   # 아래 절반 왼쪽 = 불투명(밝음)
        self.assertLess(yavg('crop=300:340:330:370'), 20)      # 아래 절반 오른쪽 = 투명(어두움)

    def test_broken_master_is_none(self):
        d = Path(tempfile.mkdtemp())
        bad = d / 'bad.mov'
        bad.write_bytes(b'not a video')
        self.assertIsNone(edit_track.make_stacked(str(bad), str(d / 's.mp4')))


if __name__ == '__main__':
    unittest.main()
