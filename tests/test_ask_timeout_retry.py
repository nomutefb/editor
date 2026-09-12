"""요약 요청(ask.sh) 시간초과 재시도 정책 · 보정 콜 노력도 회귀(260912).

실제 ask.sh 를 가짜 claude 로 돌려 본선 호출의 --effort 와 계정 토큰을 실측한다(네트워크 0).
계약: 600s 초과(rc=124) = 같은 계정에서 노력도 한 단계 하향 1회 · 두 번째 초과 = 격리(세 번째 호출 없음) ·
사다리 바닥(medium)이면 종전 계정 1회 전환 · 본선 기본 노력도 high · 분량 가드 보정 콜 기본 high.
"""
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ASK_BASE = '2026-09-12-0800-test1'

# 가짜 claude — 호출마다 토큰·인자를 로그에 남기고, 프리플라이트(--effort low)는 산 계정으로 답한다.
# 그 밖의 호출은 FAKE_PLAN(쉼표 구분 · n번째 호출의 rc · 빈값/0 = 성공)대로 종료하거나 다이제스트를 낸다.
FAKE_CLAUDE = r'''#!/usr/bin/env bash
if [ -n "${FAKE_STDIN:-}" ] && ! printf '%s' "$*" | grep -q -- '--effort low'; then
  { printf '<<<CALL>>>\n'; cat; } >> "$FAKE_STDIN"      # 본선 호출의 프롬프트 적재(프리플라이트 제외)
else
  cat > /dev/null
fi
printf '%s\t%s\n' "${CLAUDE_CODE_OAUTH_TOKEN:-}" "$*" >> "$FAKE_LOG"
case " $* " in *" --effort low "*) echo ok; exit 0;; esac
n=$(grep -vc -- '--effort low' "$FAKE_LOG")
rc="$(printf '%s' "${FAKE_PLAN:-}" | tr ',' '\n' | sed -n "${n}p")"
if [ -n "$rc" ] && [ "$rc" != 0 ]; then exit "$rc"; fi
body="$(cat "$FAKE_BODY")"
case " $* " in
  *" --output-format json "*) python3 -c 'import json,sys; print(json.dumps({"result": sys.stdin.read(), "usage": {"input_tokens": 1, "output_tokens": 1}, "num_turns": 1, "duration_ms": 1, "total_cost_usd": 0}))' <<<"$body";;
  *) printf '%s\n' "$body";;
esac
'''

DIGEST = '''---
title: "테스트 제목"
url: ""
---

### [자유요약 — 20/1000자]
```text
테스트 본문이다. 사실 축은 여기 있다.
```

### [IG — 10/800자]
```text
짧은 인스타 본문이다.
```

### [Thread — 10/430자]
```text
짧은 스레드 본문이다.
```
'''


class AskTimeoutRetryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.sb = Path(self.tmp.name) / 'sandbox'
        self.sb.mkdir()
        for name in ('.github', 'shared', 'prompts', 'apps', 'PROJECT_MEMORY.md'):
            (self.sb / name).symlink_to(REPO / name)
        for d in ('asks', 'queue', 'metrics', 'messages', 'settings', 'runner_tmp'):
            (self.sb / d).mkdir()
        subprocess.run(['git', 'init', '-q'], cwd=self.sb, check=True)
        self.bin = self.sb / 'bin'
        self.bin.mkdir()
        fake = self.bin / 'claude'
        fake.write_text(FAKE_CLAUDE)
        fake.chmod(0o755)
        self.log = self.sb / 'fake_claude.log'
        self.body = self.sb / 'fake_body.md'
        self.body.write_text(DIGEST)

    def env(self, plan, **extra):
        env = {k: v for k, v in os.environ.items()
               if k not in ('GITHUB_ACTIONS', 'PIPE_SEARCH_EFFORT', 'SUMMARY_LEN_GUARD', 'SUMMARY_POLISH',
                            'SUMMARY_REPAIR_EFFORT', 'METER_OFF', 'ASK_TIMEOUT')}
        env.update(PATH=f'{self.bin}:{env.get("PATH", "")}', FAKE_LOG=str(self.log), FAKE_PLAN=plan,
                   FAKE_BODY=str(self.body), RUNNER_TEMP=str(self.sb / 'runner_tmp'),
                   CLAUDE_CODE_OAUTH_TOKEN='tok-primary', CLAUDE_CODE_OAUTH_TOKEN_ALT='tok-alt1',
                   CLAUDE_CODE_OAUTH_TOKEN_ALT2='tok-alt2', ASK_SRCIMG='0', ASK_SRCOCR='0', ASK_FAIL_DIAG='0')
        env.update(extra)
        return env

    def run_ask(self, plan, **extra):
        (self.sb / 'asks' / f'{ASK_BASE}.json').write_text(json.dumps({'text': '테스트 요약 요청문', 'images': []}))
        r = subprocess.run(['bash', '.github/scripts/ask.sh'], cwd=self.sb, env=self.env(plan, **extra),
                           text=True, capture_output=True, timeout=300)
        self.assertEqual(r.returncode, 0, r.stdout[-3000:] + r.stderr[-3000:])
        return r.stdout

    def main_calls(self):
        calls = []
        for ln in self.log.read_text().splitlines():
            tok, _, args = ln.partition('\t')
            if '--effort low' in args:
                continue
            argv = args.split()
            calls.append((tok, argv[argv.index('--effort') + 1]))
        return calls

    def test_timeout_retries_once_on_same_account_with_lower_effort(self):
        out = self.run_ask('124')
        self.assertEqual(self.main_calls(), [('tok-primary', 'high'), ('tok-primary', 'medium')])
        self.assertIn('effort medium + 검색 상한 1회로 1회 재시도', out)

    def test_timeout_retry_also_slims_search_budget(self):
        """260912 2차 — 재시도는 노력도만 내리지 않고 **검색 예산**도 1회로 줄인다.

        노력도는 한 번 생각하는 깊이를 줄이지만 예산을 태우는 건 검색 왕복 수다(실사고 = 본문 0자 +
        영문·국문 교차검색). 그래서 첫 콜엔 없고 재시도 콜에만 완화 블록이 실려야 한다(평시 회귀 0).
        """
        stdin_log = self.sb / 'fake_stdin.txt'
        self.run_ask('124', FAKE_STDIN=str(stdin_log))
        calls = [c for c in stdin_log.read_text().split('<<<CALL>>>') if c.strip()]
        self.assertEqual(len(calls), 2, '본선 2콜(첫 시도 + 하향 재시도)')
        self.assertNotIn('검색 상한을 총 1회로 줄인다', calls[0])
        self.assertIn('검색 상한을 총 1회로 줄인다', calls[1])
        self.assertEqual(len(list((self.sb / 'queue').glob('*.md'))), 1)
        self.assertFalse((self.sb / 'asks' / f'{ASK_BASE}.json').exists())

    def test_second_timeout_isolates_without_third_call(self):
        self.run_ask('124,124')
        self.assertEqual(self.main_calls(), [('tok-primary', 'high'), ('tok-primary', 'medium')])
        self.assertEqual(list((self.sb / 'queue').glob('*.md')), [])
        self.assertTrue((self.sb / 'asks' / 'failed' / f'{ASK_BASE}.json').exists())
        self.assertIn('exit_code: 124', (self.sb / 'asks' / 'failed' / f'{ASK_BASE}.log').read_text())

    def test_floor_effort_falls_back_to_account_swap(self):
        self.run_ask('124', PIPE_SEARCH_EFFORT='medium')
        self.assertEqual(self.main_calls(), [('tok-primary', 'medium'), ('tok-alt1', 'medium')])

    def test_effort_ladder(self):
        cmd = 'source shared/claude_transient.sh; for e in max high medium low ""; do printf "%s>%s\\n" "$e" "$(claude_effort_down "$e")"; done'
        r = subprocess.run(['bash', '-c', cmd], cwd=REPO, text=True, capture_output=True, check=True)
        self.assertEqual(r.stdout.split('\n')[:5], ['max>high', 'high>medium', 'medium>medium', 'low>low', '>'])

    def test_repair_call_effort_default_high_and_env_override(self):
        digest = self.sb / 'queue' / 'test-repair.md'
        for expect, extra in (('high', {}), ('max', {'SUMMARY_REPAIR_EFFORT': 'max'})):
            digest.write_text(DIGEST)
            self.log.write_text('')
            cmd = ('source shared/claude_meter.sh; source shared/summary_repair.sh; MODEL=test-model; '
                   'SUMMARY_LEN_GUARD=1 summary_repair queue/test-repair.md ask-repair')
            r = subprocess.run(['bash', '-c', cmd], cwd=self.sb, env=self.env('', **extra), text=True,
                               capture_output=True, timeout=120)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn('REPAIR under', r.stdout)
            self.assertEqual([e for _, e in self.main_calls()], [expect], r.stdout)


if __name__ == '__main__':
    unittest.main()
