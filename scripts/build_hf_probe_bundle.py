#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
# build_hf_probe_bundle.py — hf_probe.ps1 을 '더블클릭 .bat' 하나로 묶는 생성기
#   (운영자 260810 — 파이썬 판을 준 첫 시도가 윈도우에서 그대로 헛돌았다:
#    실행 폴더에 파일이 없었고 `python3` 가 아무것도 안 했다 = 첫 실행 장애를 코드로 흡수 · [9-3])
#
# 왜 base64로 싣냐 = cmd 는 .bat 을 OEM 코드페이지(한국어 949)로 읽는다. 판정기 본문에 한글이
#   들어 있어서 그대로 실으면 반드시 깨진다. base64 는 A-Za-z0-9+/= 뿐이라 어떤 코드페이지에서도
#   바이트가 보존된다 → 복원 후 UTF-8 BOM 그대로. (정본 = build_drive_move_bundle.py 문법 계승)
#
# 정본과 다른 점 = **설치가 아니라 1회 실행**이다. 시작프로그램 등록 0 · 남는 것 0 ·
#   임시 파일은 실행 후 지운다(판정기는 상주물이 아니다).
#
# 산출물 = scripts/노뮤트_그록자격_확인.bat  ← 기계산출물. 손편집 금지.
#   값을 바꾸려면 grok_probe.ps1 을 고치고 이 스크립트를 다시 돌린다.
#
# 사용:  python3 scripts/build_hf_probe_bundle.py          (생성)
#        python3 scripts/build_hf_probe_bundle.py --check  (레포 산출물이 최신인지 · rc=1이면 낡음)
# ═══════════════════════════════════════════════════════════════════════════════
import base64
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "scripts" / "hf_probe.ps1"
OUT = ROOT / "scripts" / "노뮤트_힉스필드자격_확인.bat"

LINE = 76  # base64 한 줄 길이 — cmd 의 8191자 한 줄 한계에 한참 못 미치게 짧게 끊는다


def build() -> str:
    raw = SRC.read_bytes()
    if not raw.startswith(b"\xef\xbb\xbf"):
        sys.exit(f"FAIL: {SRC} 에 UTF-8 BOM 이 없다 — 한글이 깨진다. 먼저 BOM 을 붙여라.")
    b64 = base64.b64encode(raw).decode("ascii")
    chunks = [b64[i:i + LINE] for i in range(0, len(b64), LINE)]

    head = r"""@echo off
REM ===========================================================================
REM  nomute - Higgsfield entitlement probe : DOUBLE-CLICK, RUN ONCE
REM
REM  What it does: opens the Higgsfield device-code login in your browser, then
REM  exchanges your approval for a refresh token the CI runner can use, and
REM  verifies it with one free validate call. Spends NO credits.
REM
REM  Installs nothing. Registers nothing. Nothing is left running.
REM  Results are written to your Desktop.
REM
REM  GENERATED FILE - do not edit by hand.
REM  Source of truth: scripts/hf_probe.ps1
REM  Regenerate     : python3 scripts/build_hf_probe_bundle.py
REM ===========================================================================
setlocal
chcp 65001 >nul 2>&1
set "NM=%TEMP%\nomute_hf"
if not exist "%NM%" mkdir "%NM%"
set "B64=%NM%\_probe.b64"
if exist "%B64%" del "%B64%"

echo.
echo   Unpacking...
"""

    body = ['>> "%B64%" echo ' + c for c in chunks]

    tail = r"""
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
  "$t=[IO.File]::ReadAllText($env:B64); [IO.File]::WriteAllBytes((Join-Path $env:NM 'hf_probe.ps1'), [Convert]::FromBase64String(($t -replace '\s','')))"
if errorlevel 1 goto :fail
del "%B64%" >nul 2>&1

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%NM%\hf_probe.ps1"
set "RC=%ERRORLEVEL%"

del "%NM%\hf_probe.ps1" >nul 2>&1
rmdir "%NM%" >nul 2>&1
exit /b %RC%

:fail
echo.
echo   UNPACK FAILED - please send the lines above.
echo.
pause
exit /b 1
"""
    return head + "\n".join(body) + tail


def main() -> int:
    text = build().replace("\r\n", "\n").replace("\n", "\r\n")
    data = text.encode("ascii")  # 비ASCII가 섞이면 여기서 터진다 = 코드페이지 사고 사전 차단

    if "--check" in sys.argv:
        if not OUT.exists() or OUT.read_bytes() != data:
            print(f"⚠️ 낡음 — {OUT.name} 재생성 필요: python3 scripts/build_hf_probe_bundle.py")
            return 1
        print(f"✅ {OUT.name} = hf_probe.ps1 최신 반영")
        return 0

    OUT.write_bytes(data)
    print(f"✅ 생성 — {OUT.relative_to(ROOT)}  ({len(data):,} bytes · 원본 {SRC.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
