#!/usr/bin/env python3
"""ly_burn.poster_jpg 회귀 — 포스터는 **바이트**로 나와야 R2에 올라간다(260913 실측 봉합).

왜: thumb_gen.to_jpg90 은 (bytes, ext, content_type) 3튜플을 돌려주는데 poster_jpg 가 튜플째 반환해
    r2_upload 가 「a bytes-like object is required, not 'tuple'」 로 매 런 실패했다(run 34736090066 컴포즈 로그).
    fail-soft 경고 한 줄뿐이라 260810 도입 이래 video.json 에 poster 가 실린 적이 없었다 = 편집기 작업 내역 타일이
    썸네일 대신 영상 본체를 받던 낭비(운영자 260810 «폰이 뜨거워») 가 봉합된 적이 없던 것.
검사: ffmpeg 로 1초짜리 무음 색상 mp4를 만들어 poster_jpg 를 실호출 → bytes + JPEG 매직(PIL 있을 때) 또는 PNG 매직(PIL 없을 때 fail-soft).
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, '.github', 'scripts'))


@unittest.skipUnless(shutil.which('ffmpeg'), 'ffmpeg 없음')
class PosterBytes(unittest.TestCase):
    def test_poster_is_bytes(self):
        import ly_burn
        d = tempfile.mkdtemp()
        mp4 = os.path.join(d, 't.mp4')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'color=c=red:s=64x64:d=1', '-pix_fmt', 'yuv420p', mp4], check=True)
        out = ly_burn.poster_jpg(open(mp4, 'rb').read())
        self.assertIsInstance(out, bytes, 'poster_jpg 는 bytes 를 돌려줘야 r2_upload 가 받는다(튜플 = 260913 실사고)')
        self.assertTrue(out[:3] == b'\xff\xd8\xff' or out[:4] == b'\x89PNG', '이미지 바이트가 아니다: %r' % out[:8])
        try:
            import PIL  # noqa: F401
            self.assertEqual(out[:3], b'\xff\xd8\xff', 'PIL 이 있으면 JPEG q90 정규화가 돼야 한다')
        except ImportError:
            pass


if __name__ == '__main__':
    unittest.main()
