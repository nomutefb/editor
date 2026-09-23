#!/usr/bin/env node
// ═══════════════════════════════════════════════════════════════════════════════
// smoke_scraplive.js — 수집함 라이브 반영 · 알림 PICK 딥링크 상비 스모크 (운영자 260924 「추천 순서대로 ㄱㄱ」)
//
// 담당 표면(변경 시 커밋 전 rc=0): viewer-src/33-openQueue.part scrapAutoRefresh·loadCandidates(quiet) ·
//   viewer-src/35-applyAutoGroups.part renderScrap no-anim · viewer-src/48-renderPinSlots.part openBreakingDeepLink·pickFromPush
//
// 무엇을 검증하나:
//   A1 라이브 폴(1분)이 받은 새 후보가 탭 이동 없이 목록에 뜬다(종전 = quiet 폴이라 탭을 옮겨야 보였다)
//   A2 손대는 중(방금 탭)이면 반영을 미룬다(누르려던 카드가 밀리는 오탭 차단) → A3 손 뗀 뒤 반영
//   P1 /?brk=키&act=pick = api/pick 1발 · 카드 Picking… · act 쿼리 제거(새로고침 재발사 차단)
//   P2 act 없는 본문 탭 = 픽 0발(종전 분기 불변)
//   C1 페이지 에러 0
// 원커맨드:  node shared/smoke_scraplive.js   (종료코드 0 = 전부 PASS)
// 리스크 통제: 네트워크 0(api·후보 전부 route 스텁) · 라이브 데이터 무관(합성 후보) · 포트대 8940~8944.
// ═══════════════════════════════════════════════════════════════════════════════
'use strict';   // seal-ok: 브라우저 스모크 표준 하네스(smoke_chan 계승) — 브라우저 비기동 형제(thumbapi·sbflow·favtab)는 비대상
const path = require('path');
const fs = require('fs');
const os = require('os');
const { spawn, execSync } = require('child_process');   // seal-ok: 브라우저 스모크 표준 하네스(smoke_chan 계승) — 브라우저 비기동 형제(thumbapi·sbflow·favtab)는 비대상

const ROOT = path.resolve(__dirname, '..');   // seal-ok: 브라우저 스모크 표준 하네스(smoke_chan 계승) — thumbapi·sbflow 는 브라우저 비기동 스모크라 비대상
const VIEWER = path.join(ROOT, 'viewer');   // seal-ok: 브라우저 스모크 표준 하네스(smoke_chan 계승) — thumbapi·sbflow 는 브라우저 비기동 스모크라 비대상

function loadPlaywright() {
  try { return require('playwright-core'); } catch (_) {}   // seal-ok: 브라우저 스모크 표준 하네스(smoke_chan 계승) — 브라우저 비기동 형제(thumbapi·sbflow·favtab)는 비대상
  const cache = path.join(os.tmpdir(), 'nomute-smoke-deps');   // seal-ok: 브라우저 스모크 표준 하네스(smoke_chan 계승) — 브라우저 비기동 형제(thumbapi·sbflow·favtab)는 비대상
  const mod = path.join(cache, 'node_modules', 'playwright-core');   // seal-ok: 브라우저 스모크 표준 하네스(smoke_chan 계승) — 브라우저 비기동 형제(thumbapi·sbflow·favtab)는 비대상
  if (!fs.existsSync(mod)) {   // seal-ok: 브라우저 스모크 표준 하네스(smoke_chan 계승) — 브라우저 비기동 형제(thumbapi·sbflow·favtab)는 비대상
    console.log('· playwright-core 미설치 → 임시 캐시 설치(1회): ' + cache);
    fs.mkdirSync(cache, { recursive: true });
    execSync('npm i --prefix "' + cache + '" playwright-core --no-audit --no-fund --loglevel=error', { stdio: 'inherit' });   // seal-ok: 브라우저 스모크 표준 하네스(smoke_chan 계승) — 브라우저 비기동 형제(thumbapi·sbflow·favtab)는 비대상
  }
  return require(mod);
}

function chromiumPath() {   // seal-ok: 브라우저 스모크 표준 하네스(smoke_chan 계승) — 브라우저 비기동 형제(thumbapi·sbflow·favtab)는 비대상
  const cands = [process.env.CHROMIUM_PATH, '/opt/pw-browsers/chromium'];   // seal-ok: 브라우저 스모크 표준 하네스(smoke_chan 계승) — thumbapi·sbflow 는 브라우저 비기동 스모크라 비대상
  try { cands.push(execSync('which chromium chromium-browser google-chrome 2>/dev/null | head -1').toString().trim()); } catch (_) {}   // seal-ok: 브라우저 스모크 표준 하네스(smoke_chan 계승) — 브라우저 비기동 형제(thumbapi·sbflow·favtab)는 비대상
  for (const c of cands) { if (c && fs.existsSync(c)) return c; }   // seal-ok: 브라우저 스모크 표준 하네스(smoke_chan 계승) — 브라우저 비기동 형제(thumbapi·sbflow·favtab)는 비대상
  throw new Error('크로미엄 실행 파일을 못 찾음 — CHROMIUM_PATH env로 지정해라');   // seal-ok: 브라우저 스모크 표준 하네스(smoke_chan 계승) — thumbapi·sbflow 는 브라우저 비기동 스모크라 비대상
}

async function startServer() {
  for (let port = 8940; port < 8945; port++) {
    const srv = spawn('python3', ['-m', 'http.server', String(port), '-d', VIEWER], { stdio: 'ignore' });   // seal-ok: 브라우저 스모크 표준 하네스(smoke_chan 계승) — thumbapi·sbflow 는 브라우저 비기동 스모크라 비대상
    const ok = await new Promise(res => {   // seal-ok: 브라우저 스모크 표준 하네스(smoke_chan 계승) — thumbapi·sbflow 는 브라우저 비기동 스모크라 비대상
      let done = false;
      srv.on('exit', () => { if (!done) { done = true; res(false); } });
      setTimeout(async () => {   // seal-ok: 브라우저 스모크 표준 하네스(smoke_chan 계승) — 브라우저 비기동 형제(thumbapi·sbflow·favtab)는 비대상
        if (done) return;
        try { const r = await fetch('http://127.0.0.1:' + port + '/index.html', { method: 'HEAD' }); done = true; res(r.ok); }   // seal-ok: 브라우저 스모크 표준 하네스(smoke_chan 계승) — thumbapi·sbflow 는 브라우저 비기동 스모크라 비대상
        catch (_) { done = true; try { srv.kill(); } catch (e) {} res(false); }
      }, 700);
    });
    if (ok) return { srv, port };
    try { srv.kill(); } catch (_) {}
  }
  throw new Error('정적 서버 기동 실패(8940~8944 전부 불가)');   // seal-ok: 브라우저 스모크 표준 하네스(smoke_chan 계승) — thumbapi·sbflow 는 브라우저 비기동 스모크라 비대상
}

const now = Date.now(), iso = h => new Date(now - h * 3600e3).toISOString();
const mk = (i, t, h, cross, extra = {}) => ({ id: 'https://x.kr/' + i, url: 'https://x.kr/' + i, event_key: 'https://x.kr/' + i, title: t, media: '연합뉴스', cat: '사회', cross,
  published: iso(h), first_seen: iso(h), arts: cross, cluster_members: ['https://x.kr/' + i], ...extra });

(async () => {
  const R = [], errs = [];
  const ok = (n, c, d) => { R.push({ n, c: !!c, d: d || '' }); console.log((c ? 'PASS' : 'FAIL') + ' | ' + n + (d ? ' | ' + d : '')); };
  let srv = null, browser = null;
  try {
    const { chromium } = loadPlaywright();
    const s = await startServer(); srv = s.srv;
    browser = await chromium.launch({ executablePath: chromiumPath() });   // seal-ok: 브라우저 스모크 표준 하네스(smoke_chan 계승) — 브라우저 비기동 형제(thumbapi·sbflow·favtab)는 비대상
    const base = [mk(1, '국회 본회의 예산안 처리 협상', 1.2, 5), mk(2, '서울 지하철 파업 예고…노사 막판 교섭', 2.0, 4)];
    let data = base; const picks = [];
    const ctx = await browser.newContext({ viewport: { width: 390, height: 844 } });
    await ctx.route('**/*', route => {
      const u = new URL(route.request().url());
      if (u.pathname.endsWith('/api/candidates') || u.pathname.endsWith('/candidates.json')) return route.fulfill({ json: data });
      if (u.pathname.endsWith('/api/pick')) { picks.push(route.request().postDataJSON()); return route.fulfill({ json: { ok: true } }); }
      if (u.pathname.includes('/api/')) return route.fulfill({ json: {} });
      if (u.hostname !== '127.0.0.1' && u.hostname !== 'localhost') return route.fulfill({ status: 204, body: '' });   // seal-ok: 브라우저 스모크 표준 하네스(smoke_chan 계승) — thumbapi·sbflow 는 브라우저 비기동 스모크라 비대상
      return route.continue();
    });
    const page = await ctx.newPage();   // seal-ok: 브라우저 스모크 표준 하네스(smoke_chan 계승) — 브라우저 비기동 형제(thumbapi·sbflow·favtab)는 비대상
    page.on('pageerror', e => errs.push(String(e.message || e).slice(0, 160)));
    const titles = () => page.evaluate(() => [...document.querySelectorAll('#scrapList .sc-item .sc-title a')].map(a => a.textContent));   // seal-ok: 브라우저 스모크 표준 하네스(smoke_chan 계승) — 브라우저 비기동 형제(thumbapi·sbflow·favtab)는 비대상

    // ── A: 라이브 반영 ──
    await page.goto('http://127.0.0.1:' + s.port + '/?nosw=1&tab=scrap');   // seal-ok: 브라우저 스모크 표준 하네스(smoke_chan 계승) — thumbapi·sbflow 는 브라우저 비기동 스모크라 비대상
    await page.waitForFunction(() => document.querySelectorAll('#scrapList .sc-item').length >= 2, null, { timeout: 15000 });
    data = [mk(3, '[속보] 경기 남부 공장 화재…대응 2단계 발령', 0.1, 3, { breaking: true, grade: 3 }), ...base];
    await page.evaluate(() => { _scLastInput = 0; livePoll(); });   // seal-ok: 브라우저 스모크 표준 하네스(smoke_chan 계승) — 브라우저 비기동 형제(thumbapi·sbflow·favtab)는 비대상
    await page.waitForTimeout(2500);
    const t1 = await titles();
    ok('A1 라이브 폴 새 후보 = 탭 이동 없이 목록 반영', t1.some(x => x.includes('공장 화재')), t1.length + '건');
    data = [mk(4, '[속보] 인천공항 활주로 일시 폐쇄', 0.05, 2, { breaking: true, grade: 2 }), ...data];
    await page.mouse.move(200, 700); await page.mouse.down(); await page.mouse.up();
    await page.evaluate(() => livePoll());   // seal-ok: 브라우저 스모크 표준 하네스(smoke_chan 계승) — 브라우저 비기동 형제(thumbapi·sbflow·favtab)는 비대상
    await page.waitForTimeout(1500);
    ok('A2 손대는 중 = 반영 보류(오탭 차단)', !(await titles()).some(x => x.includes('인천공항')));
    await page.waitForTimeout(7500);
    ok('A3 손 뗀 뒤 = 반영', (await titles()).some(x => x.includes('인천공항')));

    // ── P: 알림 PICK 딥링크 ──
    const key = 'https://x.kr/3';
    await page.goto('http://127.0.0.1:' + s.port + '/?nosw=1&brk=' + encodeURIComponent(key) + '&bl=' + encodeURIComponent(key) + '&act=pick');   // seal-ok: 브라우저 스모크 표준 하네스(smoke_chan 계승) — thumbapi·sbflow 는 브라우저 비기동 스모크라 비대상
    await page.waitForFunction(() => document.querySelector('#scrapList .sc-item .sc-got.picking, #scrapList .sc-item .sc-got.firing, #scrapList .sc-item .sc-got.okdone'), null, { timeout: 15000 }).catch(() => {});
    await page.waitForTimeout(800);
    const st = await page.evaluate(() => ({ q: location.search, got: [...document.querySelectorAll('#scrapList .sc-item')].filter(x => x.querySelector('.sc-got')).map(x => x.dataset.cid) }));   // seal-ok: 브라우저 스모크 표준 하네스(smoke_chan 계승) — 브라우저 비기동 형제(thumbapi·sbflow·favtab)는 비대상
    ok('P1 act=pick = api/pick 1발 · 그 카드 픽 진행 · act 쿼리 제거', picks.length === 1 && picks[0].url === key && st.got.includes(key) && !/act=/.test(st.q), `picks=${picks.length} got=${st.got.join(',')} q=${st.q}`);
    picks.length = 0;
    const p2 = await ctx.newPage();   // seal-ok: 브라우저 스모크 표준 하네스(smoke_chan 계승) — 브라우저 비기동 형제(thumbapi·sbflow·favtab)는 비대상
    p2.on('pageerror', e => errs.push(String(e.message || e).slice(0, 160)));
    await p2.goto('http://127.0.0.1:' + s.port + '/?nosw=1&brk=' + encodeURIComponent('https://x.kr/1') + '&bl=' + encodeURIComponent('https://x.kr/1'));   // seal-ok: 브라우저 스모크 표준 하네스(smoke_chan 계승) — thumbapi·sbflow 는 브라우저 비기동 스모크라 비대상
    await p2.waitForTimeout(3500);
    ok('P2 본문 탭(act 없음) = 픽 0발(종전 분기 불변)', picks.length === 0, 'picks=' + picks.length);
    ok('C1 페이지 에러 0', errs.length === 0, errs.length ? errs.slice(0, 3).join(' · ') : '콘솔 pageerror 0건');
  } catch (e) {
    R.push({ n: 'ABORT', c: false, d: String(e.message).slice(0, 200) });
    console.log('ABORT | ' + String(e.message).slice(0, 200));
  } finally {
    if (browser) { try { await browser.close(); } catch (_) {} }
    if (srv) { try { srv.kill(); } catch (_) {} }
  }
  const fail = R.filter(r => !r.c).length;
  console.log('── 스모크 ' + (R.length - fail) + '/' + R.length + (fail ? ' — FAIL ' + fail + '건' : ' 전부 PASS') + ' (서버 종료됨)');
  process.exit(fail ? 1 : 0);
})();
