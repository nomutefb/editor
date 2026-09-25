"""픽 요약(analyze.sh) 시간초과 재시도 사다리 회귀(260925 · ask.sh 260912 사다리 이식분).

실제 analyze.sh 를 가짜 claude 로 돌려 본선 호출의 --effort·계정 토큰·재시도 프롬프트를 실측한다(네트워크 0).
계약: 900s 초과(rc=124) = 같은 계정에서 노력도 한 단계 하향 + 검색 1회 조건으로 1회 재시도 · 두 번째 초과 = 격리 ·
사다리 바닥(medium)이면 종전 계정 1회 전환 · 재시도 조건 블록은 인용 데이터 끝 표지와 함께 재시도 콜에만 실린다.
하네스 = tests/test_ask_timeout_retry.py 의 가짜 claude·샌드박스 문법을 그대로 쓴다.
"""
import os
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_ask_timeout_retry as base  # noqa: E402

PASTE = 'paste:0123456789ab\n# body:\n' + ('창원지법 밀양지원 형사1부는 25일 친족관계에 의한 강제추행 등 혐의로 기소된 40대에게 징역 7년을 선고했다. ' * 12) + '\n'
PBASE = '260925-170125-99999'


class AnalyzeTimeoutRetryTests(base.AskTimeoutRetryTests.__mro__[0]):
    """ask 하네스의 setUp·env·main_calls 를 상속하고 실행 대상만 analyze.sh 로 바꾼다."""

    def setUp(self):
        super().setUp()
        (self.sb / 'pending').mkdir(exist_ok=True)

    def run_analyze(self, plan, **extra):
        (self.sb / 'pending' / f'{PBASE}.txt').write_text(PASTE, encoding='utf-8')
        env = self.env(plan, ANALYZE_CLAIM='0', ANALYZE_LAND_EACH='0', ANALYZE_TIMEOUT='900', **extra)
        env.pop('ANALYZE_RETRY_SLIM', None)
        command = ['bash', '.github/scripts/analyze.sh']
        if os.name == 'nt':
            command = ['bash', '-c', 'export PATH="$(cygpath -u "$FAKE_BIN"):$PATH"; exec bash .github/scripts/analyze.sh']
        r = subprocess.run(command, cwd=self.sb, env=env, text=True, encoding='utf-8', errors='replace', capture_output=True, timeout=300)
        self.assertEqual(r.returncode, 0, r.stdout[-3000:] + r.stderr[-3000:])
        return r.stdout

    # ask 전용 케이스는 이 클래스에서 끈다(상속으로 딸려 오는 것 차단)
    test_timeout_retries_once_on_same_account_with_lower_effort = None
    test_timeout_retry_also_slims_search_budget = None
    test_second_timeout_isolates_without_third_call = None
    test_floor_effort_falls_back_to_account_swap = None
    test_effort_ladder = None
    test_repair_call_effort_default_high_and_env_override = None

    def test_analyze_timeout_lowers_effort_on_same_account_with_slim(self):
        stdin_log = self.sb / 'fake_stdin.txt'
        out = self.run_analyze('124', FAKE_STDIN=str(stdin_log))
        self.assertEqual(self.main_calls(), [('tok-primary', 'high'), ('tok-primary', 'medium')])
        self.assertIn('effort medium + 검색 1회로 1회 재시도', out)
        calls = [c for c in stdin_log.read_text().split('<<<CALL>>>') if c.strip()]
        self.assertEqual(len(calls), 2)
        self.assertNotIn('검색 상한을 총 1회로 줄인다', calls[0])
        self.assertIn('인용 데이터(사전 추출 본문 등) 끝', calls[1])
        self.assertIn('검색 상한을 총 1회로 줄인다', calls[1])
        self.assertEqual(len(list((self.sb / 'queue').glob('*.md'))), 1)

    def test_analyze_second_timeout_has_no_third_call(self):
        self.run_analyze('124,124')
        self.assertEqual(self.main_calls(), [('tok-primary', 'high'), ('tok-primary', 'medium')])
        self.assertEqual(list((self.sb / 'queue').glob('*.md')), [])

    def test_analyze_floor_effort_falls_back_to_account_swap(self):
        self.run_analyze('124', PIPE_SEARCH_EFFORT='medium')
        self.assertEqual(self.main_calls(), [('tok-primary', 'medium'), ('tok-alt1', 'medium')])


if __name__ == '__main__':
    unittest.main()
