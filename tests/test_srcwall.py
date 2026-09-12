"""출처 봇월(cupid.js) 통과 · 본문 전문 주입 · 재시도 검색 완화 회귀(260912).

사고 fail-2026-09-12-0926 = 이슈링크 커뮤니티 글 전송 → 수확기가 챌린지 껍데기를 받아 본문 0자 →
모델이 제목만으로 검색하다 600s 를 두 번 초과(21분 실패). 계약 4축을 네트워크 0 으로 실측한다:
  ① 챌린지 감지·복호는 shared/cupid_wall.py 정본 1곳(사본 금지)
  ② 수확기는 챌린지를 만나면 쿠키를 붙여 재요청하고, 통과 본문·최종 주소를 산출에 담는다
  ③ 주입 전문은 fetch_article.sh 본문 선별 정본(한글 20자 미만 줄 버림·중복 제거·40줄)을 따른다
  ④ ask.sh 타임아웃 재시도는 노력도만 내리지 않고 검색 상한 1회 블록을 프롬프트에 덧붙인다
"""
import http.server
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'shared'))
sys.path.insert(0, str(REPO / '.github' / 'scripts'))

import cupid_wall          # noqa: E402
import ask_srcimg          # noqa: E402

KEY = bytes(range(16))
IV = bytes(range(16, 32))
SECRET = bytes(range(32, 48))     # 복호 결과 = 쿠키 값의 원본 평문


def _cipher_hex():
    """챌린지 페이지에 박히는 c(암호문) — 평문 SECRET 을 KEY/IV 로 CBC 암호화한 1블록."""
    from Crypto.Cipher import AES
    return AES.new(KEY, AES.MODE_CBC, IV).encrypt(SECRET).hex()


def _challenge_html():
    return ('<html><body><script>'
            'a=toNumbers("%s"), b=toNumbers("%s"), c=toNumbers("%s");'
            '</script></body></html>' % (KEY.hex(), IV.hex(), _cipher_hex()))


# 통과 페이지 — 본문 줄(한글 20자 이상) + 내비 잔해(짧은 줄) + 중복 줄을 섞어 선별 계약을 실측한다.
PASS_HTML = ('<html><head><title>t</title></head><body>'
             '<div>로그인</div><div>회원가입</div><div>정치</div><div>야구</div>'
             '<p>유가족이 추도식에 참석하지 말아달라고 기자회견까지 했는데 논란이 커졌다.</p>'
             '<p>희생자 이름을 호명하는 순간 포착된 시장의 태도가 문제로 지목되고 있다.</p>'
             '<p>희생자 이름을 호명하는 순간 포착된 시장의 태도가 문제로 지목되고 있다.</p>'
             '<p>현재 미국 주요 매체에 기사까지 뜨면서 크게 논란이 되고 있는 상황이다.</p>'
             '</body></html>')


class _Wall(http.server.BaseHTTPRequestHandler):
    """cupid 봇월 재현 — 쿠키 없으면 챌린지, 쿠키+ckattempt 면 본문. /go/* 는 통과 뒤 302."""
    hits = []

    def do_GET(self):                                      # noqa: N802
        cookie = self.headers.get('Cookie') or ''
        ok = cupid_wall.COOKIE_NAME in cookie and 'ckattempt' in self.path
        _Wall.hits.append((self.path, bool(cookie)))
        if ok and self.path.startswith('/go/'):
            self.send_response(302)
            self.send_header('Location', '/real?ckattempt=1')
            self.end_headers()
            return
        body = (PASS_HTML if ok or self.path.startswith('/real') else _challenge_html()).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):                             # noqa: A003
        pass


class CupidWallCanonTests(unittest.TestCase):
    def test_detect_and_decrypt(self):
        html = _challenge_html()
        self.assertTrue(cupid_wall.is_challenge(html))
        self.assertFalse(cupid_wall.is_challenge(PASS_HTML))
        self.assertEqual(cupid_wall.cookie_for(html), SECRET.hex())   # 1블록 CBC 복호 = 원 평문

    def test_host_gate(self):
        self.assertTrue(cupid_wall.is_wall_host('www.issuelink.co.kr'))
        self.assertTrue(cupid_wall.is_wall_host('issuelink.co.kr:443'))
        self.assertFalse(cupid_wall.is_wall_host('mlbpark.donga.com'))

    def test_why_failed_splits_causes(self):
        self.assertIn('파싱 실패', cupid_wall.why_failed('<html>본문</html>'))
        self.assertEqual(cupid_wall.why_failed(_challenge_html()), 'cupid 복호 실패')  # 설치된 환경 기준

    def test_no_duplicate_regex_in_callers(self):
        """정본 1곳 — 호출부가 챌린지 정규식·AES 복호 사본을 다시 들고 있으면 드리프트가 재발한다."""
        for rel in ('scraper/social_burst.py', '.github/scripts/ask_srcimg.py'):
            src = (REPO / rel).read_text(encoding='utf-8')
            self.assertNotIn('toNumbers("([0-9a-fA-F]+)', src, rel)
            self.assertNotIn('MODE_CBC', src, rel)


class HarvestWallTests(unittest.TestCase):
    """수확기 실주행 — 로컬 봇월 서버로 통과·전문·최종 주소를 실측(외부 네트워크 0)."""

    @classmethod
    def setUpClass(cls):
        cls.srv = http.server.HTTPServer(('127.0.0.1', 0), _Wall)
        cls.port = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        # 봇월 호스트 판정을 테스트 서버로 유도(정본 목록 자체는 무접촉 — 실사이트 계약 보존)
        cls._hosts = cupid_wall.WALL_HOSTS
        cupid_wall.WALL_HOSTS = ('127.0.0.1',)
        # SSRF 가드는 사설 IP 를 차단한다(프로덕션 계약 = 무접촉) → 루프백 테스트 동안만 통과시킨다.
        cls._guard = ask_srcimg._blocked_host
        ask_srcimg._blocked_host = lambda h: False

    @classmethod
    def tearDownClass(cls):
        cupid_wall.WALL_HOSTS = cls._hosts
        ask_srcimg._blocked_host = cls._guard
        cls.srv.shutdown()
        cls.srv.server_close()

    def _harvest(self, path):
        with tempfile.TemporaryDirectory() as d:
            return ask_srcimg.harvest('http://127.0.0.1:%d%s' % (self.port, path), d, max_n=1)

    def test_pass_and_inject(self):
        res = self._harvest('/post/1')
        self.assertEqual(res['wall'], 'cupid 봇월 통과')
        self.assertGreater(res['text_len'], 100, res['why'])
        self.assertIn('유가족이 추도식에', res['text'])
        self.assertNotIn('회원가입', res['text'])                  # 내비 잔해 = 한글 20자 미만 줄 버림
        self.assertEqual(res['text'].count('희생자 이름을'), 1)    # 중복 줄 제거
        self.assertLessEqual(len(res['text']), ask_srcimg.WALL_TEXT_MAX)

    def test_redirect_final_url(self):
        """/go/<id> = 통과 뒤 실제 글로 302 — 본선이 봇월 주소가 아니라 그 주소를 열게 해야 한다."""
        res = self._harvest('/go/118643772')
        self.assertIn('/real', res['final'])
        self.assertIn('유가족이 추도식에', res['text'])

    def test_no_wall_no_injection(self):
        """봇월 축이 아니면 전문 주입 0 = 평범한 기사 경로는 종전 동작 그대로(회귀 0)."""
        cupid_wall.WALL_HOSTS = ('example.invalid',)
        try:
            res = self._harvest('/real')
        finally:
            cupid_wall.WALL_HOSTS = ('127.0.0.1',)
        self.assertEqual(res['wall'], '')
        self.assertEqual(res['text'], '')

    def test_missing_dependency_is_failsoft(self):
        """pycryptodome 미설치 = 통과 불가지만 사유를 명시하고 rc=0(구 동작 = 조용한 0자)."""
        real = cupid_wall.cookie_for
        cupid_wall.cookie_for = lambda t: None
        try:
            res = self._harvest('/post/1')
        finally:
            cupid_wall.cookie_for = real
        self.assertTrue(res['ok'])
        self.assertIn('cupid', res['wall'])
        self.assertEqual(res['text'], '')


class FailProbeWallTests(unittest.TestCase):
    """자동진단서(ask_fail_probe) — 수확기 내부 반환 계약 변경이 조용히 깨뜨리던 자리(260912 실측).

    probe() 는 `si._get_page()` 를 직접 언패킹한다. ask.sh 는 이 호출을 `|| true` 로 감싸므로
    언패킹이 깨지면 **오류 없이 진단서만 사라진다**(실패 알림은 정상 발송 = 아무도 모른다).
    그래서 반환 개수·봇월 판정을 실주행으로 고정한다.
    """

    @classmethod
    def setUpClass(cls):
        cls.srv = http.server.HTTPServer(('127.0.0.1', 0), _Wall)
        cls.port = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls._hosts, cupid_wall.WALL_HOSTS = cupid_wall.WALL_HOSTS, ('127.0.0.1',)
        cls._guard, ask_srcimg._blocked_host = ask_srcimg._blocked_host, (lambda h: False)

    @classmethod
    def tearDownClass(cls):
        cupid_wall.WALL_HOSTS = cls._hosts
        ask_srcimg._blocked_host = cls._guard
        cls.srv.shutdown()
        cls.srv.server_close()

    def test_probe_unpacks_and_reports_wall(self):
        import ask_fail_probe
        p = ask_fail_probe.probe('http://127.0.0.1:%d/post/1' % self.port)
        self.assertTrue(p['fetched'])
        self.assertEqual(p['wall'], 'cupid 봇월 통과')
        self.assertGreater(p['ko'], 50)
        self.assertIn('봇월은 통과했다', ask_fail_probe._verdict(p, 'http://x'))

    def test_verdict_separates_wall_from_shell(self):
        """봇월 막힘을 '새 셸 문법 의심'으로 적으면 다음 세션이 엉뚱한 자리를 판다(실사고 오안내)."""
        import ask_fail_probe
        blocked = {'fetched': True, 'bytes': 797, 'ko': 0, 'shell': True, 'final': '',
                   'wall': 'pycryptodome 미설치 — cupid 우회 불가'}
        v = ask_fail_probe._verdict(blocked, 'http://x')
        self.assertIn('봇월', v)
        self.assertNotIn('새 셸 문법', v)


class DenseTextCanonTests(unittest.TestCase):
    def test_line_cap(self):
        long_line = '한글이스무자이상되는줄을만들어서본문으로인정받게한다 %d'
        txt = '\n'.join(long_line % i for i in range(ask_srcimg.DENSE_LINES + 10))
        self.assertEqual(len(ask_srcimg.dense_text(txt).split('\n')), ask_srcimg.DENSE_LINES)

    def test_canon_values_match_fetch_article(self):
        """상한 값은 fetch_article.sh 정본 계승 — 한쪽만 바뀌면 두 경로 산출이 갈린다."""
        fa = (REPO / '.github' / 'scripts' / 'fetch_article.sh').read_text(encoding='utf-8')
        self.assertIn('keep[:40]', fa)
        self.assertEqual(ask_srcimg.DENSE_LINES, 40)
        self.assertIn('res[:6000]', fa)
        self.assertEqual(ask_srcimg.WALL_TEXT_MAX, 6000)


class AskPromptWiringTests(unittest.TestCase):
    """ask.sh 배선 — 주입 블록이 프롬프트에 실리고, 재시도가 검색 상한을 함께 줄이는지."""

    ASK = (REPO / '.github' / 'scripts' / 'ask.sh').read_text(encoding='utf-8')

    def test_srctext_block_in_prompt(self):
        self.assertIn('${SRCTEXT_BLOCK}', self.ASK)
        self.assertIn('SRCTEXT_BLOCK=""', self.ASK)           # set -u 안전 선언
        self.assertIn('이 본문이 곧 원문이다', self.ASK)

    def test_retry_slims_search_budget(self):
        self.assertIn('${prompt}${_slim}', self.ASK)
        self.assertIn('_slim="$_slim_txt"', self.ASK)
        self.assertIn('검색 상한을 총 1회로 줄인다', self.ASK)
        self.assertIn('ASK_RETRY_SLIM', self.ASK)             # 킬스위치

    def test_timeout_notice_no_longer_claims_nothing_to_fix(self):
        """구판 오안내 소거 — 타임아웃 조치문의 「코드가 고칠 자리는 없어」는 실사고에서 틀렸다."""
        seg = self.ASK.split('timeout)')[-1].split(';;')[0]
        self.assertNotIn('코드가 고칠 자리는 없어', seg)
        self.assertIn('출처 사이트 차단', seg)

    def test_workflow_installs_dependency(self):
        wf = (REPO / '.github' / 'workflows' / 'news-ask.yml').read_text(encoding='utf-8')
        self.assertIn('pycryptodome', wf)


if __name__ == '__main__':
    unittest.main()
