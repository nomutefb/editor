# Access 서비스 토큰 비밀값 정규화 회귀 — Cloudflare 복사 버튼이 헤더 줄째(`CF-Access-Client-Id: …`)로 복사해
# 비밀값에 앞말이 붙어 들어가면 Access가 거부했다(260925 live-smoke #192 ACCESS=denied · 토큰 '마지막 확인' 공란).
import os, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "shared"))
import access_token as at  # noqa: E402

ID, SECRET = "0123abcd.access", "a" * 64
MOD = ROOT / "shared" / "access_token.py"


def _shell(env_extra, script):
    env = {k: v for k, v in os.environ.items() if not k.startswith("CF_ACCESS_") and k != "GITHUB_ACTIONS"}
    env.update(env_extra)
    return subprocess.run(["bash", "-c", f'eval "$(python3 {MOD} --shell)"; {script}'],
                          capture_output=True, text=True, env=env, timeout=30)


class NormalizeTest(unittest.TestCase):
    def check(self, raw_id, raw_sec, fix):
        cid, sec, fixes = at.normalize(raw_id, raw_sec)
        self.assertEqual((cid, sec), (ID, SECRET))
        self.assertEqual(fixes, fix)

    def test_bare_values_untouched(self):
        self.check(ID, SECRET, set())

    def test_header_prefix_from_copy_button(self):
        self.check(f"CF-Access-Client-Id: {ID}", f"CF-Access-Client-Secret: {SECRET}", {"prefix"})

    def test_lowercase_header_quotes_crlf(self):
        self.check(f'  cf-access-client-id:"{ID}"\r\n', f"'{SECRET}'\n", {"prefix", "space"})

    def test_swapped_values(self):
        self.check(SECRET, ID, {"swap"})

    def test_swapped_header_lines(self):
        self.check(f"CF-Access-Client-Secret: {SECRET}", f"CF-Access-Client-Id: {ID}", {"prefix"})

    def test_both_header_lines_in_one_secret(self):
        blob = f"CF-Access-Client-Id: {ID}\nCF-Access-Client-Secret: {SECRET}"
        self.check(blob, blob, {"prefix"})

    def test_other_label_prefix(self):
        self.check(f"Client ID: {ID}", f"Client Secret: {SECRET}", {"prefix"})

    def test_headers_need_both(self):
        self.assertEqual(at.headers({"CF_ACCESS_CLIENT_ID": ID}), {})
        self.assertEqual(at.headers({}), {})
        self.assertEqual(at.headers({"CF_ACCESS_CLIENT_ID": f"CF-Access-Client-Id: {ID}", "CF_ACCESS_CLIENT_SECRET": SECRET}),
                         {"CF-Access-Client-Id": ID, "CF-Access-Client-Secret": SECRET})

    def test_shape_never_leaks_values(self):
        s = at.shape({"CF_ACCESS_CLIENT_ID": f"CF-Access-Client-Id: {ID}", "CF_ACCESS_CLIENT_SECRET": SECRET})
        self.assertNotIn(ID, s)
        self.assertNotIn(SECRET, s)
        self.assertIn("id_suffix=ok", s)
        self.assertIn("secret_len=64", s)
        self.assertIn("fixed=prefix", s)


class ShellTest(unittest.TestCase):
    def test_eval_strips_prefix(self):
        r = _shell({"CF_ACCESS_CLIENT_ID": f"CF-Access-Client-Id: {ID}", "CF_ACCESS_CLIENT_SECRET": f"CF-Access-Client-Secret: {SECRET}\n"},
                   'printf "%s|%s" "$CF_ACCESS_CLIENT_ID" "$CF_ACCESS_CLIENT_SECRET"')
        self.assertEqual(r.stdout, f"{ID}|{SECRET}", r.stderr)

    def test_masks_changed_values_only_in_actions(self):
        r = _shell({"GITHUB_ACTIONS": "true", "CF_ACCESS_CLIENT_ID": f"CF-Access-Client-Id: {ID}", "CF_ACCESS_CLIENT_SECRET": SECRET}, "true")
        self.assertIn(f"::add-mask::{ID}", r.stdout)            # 부분 문자열 = 자동 마스킹 밖 → 명시 마스킹
        self.assertNotIn(f"::add-mask::{SECRET}", r.stdout)     # 원값 그대로 = 이미 비밀값 마스킹

    def test_no_token_no_output(self):
        r = _shell({}, 'printf "[%s]" "${CF_ACCESS_CLIENT_ID-unset}"')
        self.assertEqual(r.stdout, "[unset]")                   # 미설정 판정(notoken) 유지

    def test_eval_is_injection_safe(self):
        with tempfile.TemporaryDirectory() as d:
            probe = Path(d) / "pwned"
            r = _shell({"CF_ACCESS_CLIENT_ID": f"$(touch {probe})", "CF_ACCESS_CLIENT_SECRET": f"`touch {probe}`;x"}, "true")
            self.assertFalse(probe.exists(), r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
