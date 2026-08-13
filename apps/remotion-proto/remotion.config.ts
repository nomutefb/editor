// 레모션 렌더 설정 — 크로미엄은 폴백 해석기로 찾는다(리터럴 고정 금지 = check_smoke_chromium_path 계약 계승:
// env → /opt/pw-browsers → which · 전부 실존 검사 · 못 찾으면 null = 레모션이 자체 헤드리스 셸을 내려받는다 = 러너 폴백).
import {existsSync} from 'node:fs';
import {execSync} from 'node:child_process';
import {Config} from '@remotion/cli/config';

function chromiumPath(): string | null {
  // ⚠ 헤드리스 셸이 1순위 — 신형 크로미엄 본체(141+)는 구형 헤드리스가 제거돼 레모션 기동이 거부된다(260813 실측:
  //   "Old Headless mode has been removed"). 본체 경로(/opt/pw-browsers/chromium)는 그래서 후보에서 뺐다.
  const cands = [
    process.env.CHROMIUM_PATH,
    '/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell',
  ];
  for (const c of cands) if (c && existsSync(c)) return c;
  try {
    const glob = execSync(
      'ls -d /opt/pw-browsers/chromium_headless_shell-*/chrome-linux/headless_shell 2>/dev/null || true',
    ).toString().split('\n').map((s) => s.trim()).filter(Boolean)[0];
    if (glob && existsSync(glob)) return glob;
  } catch { /* 폴백 = null */ }
  return null;   // null = 레모션 관리 다운로드(깃허브 러너 폴백)
}

const bx = chromiumPath();
if (bx) Config.setBrowserExecutable(bx);
Config.setVideoImageFormat('jpeg');
Config.setOverwriteOutput(true);
