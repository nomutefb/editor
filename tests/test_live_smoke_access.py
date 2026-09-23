# 라이브 검문 × Cloudflare Access 벽 회귀 — 토큰 미설정 = 판정 보류(notoken) · 토큰 거부 = denied · 토큰 통과 = 전 축 헤더 동승
# (260923 운영자: 코드 푸시마다 「라이브 검문 실패(비코드축) · Access 로그인 페이지가 옴」 경보가 폰에 반복)
import http.server, os, subprocess, sys, threading, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SMOKE = ROOT / "shared" / "live_smoke.py"
ACCESS_PAGE = (b"<!DOCTYPE html><html><head><title>Sign in \xe3\x83\xbb Cloudflare Access</title></head>"
               b"<body><form action=\"https://x.cloudflareaccess.com/cdn-cgi/access/login\"></form></body></html>")
ID, SECRET = "test-id.access", "test-secret"


def _serve(accept_token):
    # accept_token=True → 올바른 두 헤더가 있을 때만 레포 실물을 내줌(없으면 로그인 화면) · False → 항상 로그인 화면(토큰 거부)
    seen = []

    class H(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):
            path = self.path.split("?")[0]
            authed = (self.headers.get("CF-Access-Client-Id") == ID
                      and self.headers.get("CF-Access-Client-Secret") == SECRET)
            seen.append((path, authed))
            body = ACCESS_PAGE
            if accept_token and authed:
                if path == "/":
                    body = (ROOT / "viewer" / "index.html").read_bytes()
                elif path == "/articles.json":
                    body = b'{"articles":[{"file":"a.md"}]}'
                else:
                    fp = ROOT / "viewer" / path.lstrip("/")
                    body = fp.read_bytes() if fp.is_file() else b""
            self.send_response(200)
            self.end_headers()
            self.wfile.write(body)

    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, seen


def _run(base, token):
    env = {k: v for k, v in os.environ.items() if not k.startswith("CF_ACCESS_")}
    if token:
        env.update(CF_ACCESS_CLIENT_ID=ID, CF_ACCESS_CLIENT_SECRET=SECRET)
    r = subprocess.run([sys.executable, str(SMOKE), "--base", base], capture_output=True, text=True, env=env, timeout=120)
    mark = next((l for l in r.stdout.splitlines() if l.startswith("MARK ")), "")
    return r.returncode, mark, r.stdout


class LiveSmokeAccessTest(unittest.TestCase):
    def test_no_token_is_hold_not_code_fail(self):
        srv, _ = _serve(accept_token=True)
        try:
            rc, mark, out = _run(f"http://127.0.0.1:{srv.server_port}", token=False)
        finally:
            srv.shutdown(); srv.server_close()
        self.assertEqual(rc, 1, out)                      # 통과 아님(rc만 보는 소비자에게 거짓 녹색 금지)
        self.assertIn("ACCESS=notoken", mark)             # 워크플로가 중립 스킵(알림·원장·롤백 생략)으로 받는 신호
        self.assertIn("CODEFAIL=0", mark)                 # 롤백 카운터 무가산

    def test_rejected_token_is_denied_alert(self):
        srv, seen = _serve(accept_token=False)
        try:
            rc, mark, out = _run(f"http://127.0.0.1:{srv.server_port}", token=True)
        finally:
            srv.shutdown(); srv.server_close()
        self.assertEqual(rc, 1, out)
        self.assertIn("ACCESS=denied", mark)              # 토큰을 싣고도 막힘 = 설정 오류 = 알림 유지
        self.assertIn("CODEFAIL=0", mark)
        self.assertTrue(seen and seen[0][1], "토큰 헤더가 요청에 실리지 않음")

    def test_valid_token_rides_every_fetch(self):
        srv, seen = _serve(accept_token=True)
        try:
            rc, mark, out = _run(f"http://127.0.0.1:{srv.server_port}", token=True)
        finally:
            srv.shutdown(); srv.server_close()
        self.assertNotIn("ACCESS=", mark, out)
        self.assertEqual(rc, 0, out)                      # 벽 통과 = C1~C4 전문 검문 복귀
        self.assertIn("VERIFIED=full", mark)
        self.assertTrue(seen and all(a for _, a in seen), f"토큰 없이 나간 요청: {[p for p, a in seen if not a]}")


if __name__ == "__main__":
    unittest.main()
