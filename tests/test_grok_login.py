"""그록 다시 로그인(grok_login.py) — 승인 대기 → 비밀칸 저장 흐름 · 열쇠·코드가 공개 로그에 새지 않는지."""
import contextlib
import io
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github' / 'scripts'))
sys.path.insert(0, str(ROOT / 'shared'))
import grok_login  # noqa: E402

RT = 'rt-SECRET-refresh-0123456789'
UC = 'ABCD-EFGH'


def fake_req(seq):
    """발견 문서 → 코드 발급 → (대기 응답들) → 토큰 → 모델 목록 순서로 돌려주는 가짜 요청기."""
    it = iter(seq)

    def _req(url, **kw):
        return next(it)
    return _req


DISC = (200, '', {'device_authorization_endpoint': 'https://a/dev', 'token_endpoint': 'https://a/tok'})
DEV = (200, '', {'user_code': UC, 'device_code': 'dc-1', 'verification_uri_complete': 'https://x/device?c=' + UC, 'interval': 0, 'expires_in': 60})
PENDING = (400, '', {'error': 'authorization_pending'})
TOK = (200, '', {'access_token': 'at-1', 'refresh_token': RT})
MODELS = (200, '', {'data': [{'id': 'grok-4.3'}]})


class GrokLogin(unittest.TestCase):
    def run_main(self, seq, persist=True):
        posts = []
        out = io.StringIO()
        with mock.patch.object(grok_login.probe, '_req', fake_req(seq)), \
             mock.patch.object(grok_login, 'post', lambda id_, doc: posts.append(doc)), \
             mock.patch.object(grok_login.grok_api, '_persist_secret', return_value=persist) as ps, \
             mock.patch.object(grok_login.time, 'sleep', lambda s: None), \
             contextlib.redirect_stdout(out):
            rc = grok_login.main(['grok_login.py', '260928220000-abc123'])
        return rc, posts, ps, out.getvalue()

    def test_approve_then_store(self):
        rc, posts, ps, log = self.run_main([DISC, DEV, PENDING, PENDING, TOK, MODELS])
        self.assertEqual(rc, 0)
        ps.assert_called_once_with(RT, 'XAI_SECRET_PAT')                        # 이관 칸에 저장
        self.assertEqual([p['state'] for p in posts], ['start', 'wait', 'done'])
        self.assertEqual(posts[1]['code'], UC)                                       # 주소·코드 = R2 게시분에만
        for leak in (RT, UC, 'at-1', 'dc-1'):
            self.assertNotIn(leak, log)                                              # 공개 로그에 새지 않는다

    def test_denied_and_no_api_tier(self):
        rc, posts, ps, _ = self.run_main([DISC, DEV, (400, '', {'error': 'access_denied'})])
        self.assertEqual((rc, posts[-1]['state']), (1, 'fail'))
        ps.assert_not_called()
        rc, posts, ps, _ = self.run_main([DISC, DEV, TOK, (403, 'no', None)])
        self.assertEqual(rc, 1)
        self.assertIn('Premium+', posts[-1]['why'])
        ps.assert_not_called()                                                       # 통로 없는 계정 열쇠는 저장하지 않는다

    def test_store_failure_is_reported(self):
        rc, posts, _, _ = self.run_main([DISC, DEV, TOK, MODELS], persist=False)
        self.assertEqual((rc, posts[-1]['state']), (1, 'fail'))


if __name__ == '__main__':
    unittest.main()
