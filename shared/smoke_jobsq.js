'use strict';
/* ═══════════════════════════════════════════════════════════════════════════════
 * smoke_jobsq.js — 영상 스튜디오 **동시 큐잉** 축(운영자 260810 "동시에 2가지 작업을 큐잉하면
 *   첫번째거를 두번째꺼가 덮어씌워져 · 동시에 병렬로 진행되는게 가장 좋고")
 *
 * ⚠ 신설 사유 = **이 레포 스모크 25종이 전부 「화면이 어떻게 그려졌나」를 잰다**(기하·잉크·색·부품·렌더 예산).
 *   「작업을 두 개 걸면 둘 다 살아 있나」는 축 자체가 없었고, 그 틈에서 스튜디오 5탭이 전부 **작업 1개만**
 *   추적하고 있었다 — 재개 슬롯(localStorage)이 객체 1개라 뒤 발사가 앞 발사를 덮고, 폴 중단 핸들(`_curStop`)이
 *   전역 1개라 뒤 폴이 앞 폴을 그 자리에서 죽였다. 러너는 정상 완료하는데 화면만 그 결과를 영영 안 본다
 *   = 화면 증상이 「아무 일도 안 일어남」뿐이라 운영자 눈이 유일한 검출기였다(insta-thumb-miss·brk_misfire 동축).
 *
 * 판정 8축(폰 430 · 실렌더 · 네트워크 발사 0 = 가짜 id로 폴만 띄운다 = 러너·과금 무접촉)
 *   J1 편집 = 구판 단일 슬롯(객체)을 배열 1개로 승격해 재개(이관 시점 진행분 유실 0)
 *   J2 편집 = 2건 연달아 큐잉 → **둘 다 폴 생존**(이 세션의 본 과제)
 *   J3 편집 = 화면 주인 = 나중 작업(앞 작업은 강등 = 남의 진행 화면을 안 덮는다)
 *   J4 편집 = 같은 작업 중복 폴 차단(재개 ↔ 발사 겹침)
 *   J5 편집 = 재개가 진행분 **전건**(구판은 최신 1건만 이어받았다)
 *   J6 음원 = 2건 동시 큐잉 생존 + 화면 주인 이동
 *   J7 콘티·프롬프팅 = 2건 동시 폴 생존
 *   J8 큐영상 = 진행 중 렌더 전건 재개(구판 `.find()` 단건)
 *
 * ⚠ 서버 동시 상한(functions/api/_rate.js rateGate cap=3)은 이 축의 대상이 아니다 — 그건 워크플로별 발사 제한이고,
 *   여기서 재는 건 「화면이 몇 개를 들고 있나」다. 서버가 3개를 받아주는데 화면이 1개만 들면 나머지가 유실된다.
 * ═══════════════════════════════════════════════════════════════════════════════ */
const path = require('path');
const fs = require('fs');
const os = require('os');
const http = require('http');
const { execSync } = require('child_process');
const ROOT = path.resolve(__dirname, '..');
const VIEWER = path.join(ROOT, 'viewer');

function loadPlaywright() {
  try { return require('playwright-core'); } catch (_) {}
  try { return require(path.join(ROOT, 'node_modules', 'playwright')); } catch (_) {}
  const cache = path.join(os.tmpdir(), 'nomute-smoke-deps');
  const mod = path.join(cache, 'node_modules', 'playwright-core');
  if (!fs.existsSync(mod)) {
    console.log('· playwright-core 미설치 → 임시 캐시 설치(1회): ' + cache);
    fs.mkdirSync(cache, { recursive: true });
    execSync('npm --prefix ' + cache + ' i playwright-core --no-save --silent', { stdio: 'inherit' });
  }
  return require(mod);
}
function chromiumPath() {   // 정본 해석기(shared/smoke_parity.js) 사본 — 후보를 **실존 검사**한다(check_smoke_chromium_path 계약)
  const cands = [process.env.CHROMIUM_PATH, '/opt/pw-browsers/chromium'];
  try { cands.push(execSync('which chromium chromium-browser google-chrome 2>/dev/null | head -1').toString().trim()); } catch (_) {}
  for (const c of cands) { if (c && fs.existsSync(c)) return c; }
  throw new Error('chromium 실행 파일을 찾지 못함(CHROMIUM_PATH 지정)');
}
const MIME = { html: 'text/html', js: 'text/javascript', css: 'text/css', json: 'application/json', woff2: 'font/woff2', png: 'image/png', webp: 'image/webp', svg: 'image/svg+xml' };
function serve(port) {
  return new Promise((res, rej) => {
    const s = http.createServer((q, r) => {
      const p = path.join(VIEWER, decodeURIComponent(q.url.split('?')[0]).replace(/^\/+/, '') || 'index.html');
      fs.readFile(p, (e, b) => { if (e) { r.writeHead(404); r.end(); return; } r.writeHead(200, { 'content-type': MIME[path.extname(p).slice(1)] || 'application/octet-stream' }); r.end(b); });
    });
    s.on('error', rej); s.listen(port, '127.0.0.1', () => res(s));
  });
}
let PASS = 0, FAIL = 0;
const ck = (n, ok, d) => { console.log((ok ? '✅' : '❌') + ' [큐] ' + n + ' — ' + d); ok ? PASS++ : FAIL++; };

async function open(browser, port, file, init) {
  const pg = await browser.newPage({ viewport: { width: 430, height: 900 }, deviceScaleFactor: 2 });
  if (init) await pg.addInitScript(init);
  await pg.goto('http://127.0.0.1:' + port + '/' + file, { waitUntil: 'domcontentloaded', timeout: 25000 });
  await pg.waitForTimeout(900);
  return pg;
}

(async () => {
  let srv = null, port = 0;
  for (let p = 8851; p < 8856; p++) { try { srv = await serve(p); port = p; break; } catch (_) {} }   // 8851~ = 형제 스모크 포트대 다음 슬롯(무충돌)
  if (!srv) { console.log('ABORT | 정적 서버 기동 실패(8851~8855)'); process.exit(1); }
  const { chromium } = loadPlaywright();
  const browser = await chromium.launch({ executablePath: chromiumPath(), args: ['--no-sandbox'] });
  try {
    // ── J1 구판 단일 슬롯 승격 + 재개
    {
      const pg = await open(browser, port, 'edit.html', () => localStorage.setItem('nm_edit_pend', JSON.stringify({ id: '260810120000-aaaaaa', t0: Date.now(), lbl: '편집 중' })));
      const r = await pg.evaluate(() => ({ n: nmJobs.list('nm_edit_pend').length, polls: nmJobs.count('nm_edit_pend'), id: (nmJobs.list('nm_edit_pend')[0] || {}).id }));
      ck('J1 편집 구판 단일 슬롯 승격·재개', r.n === 1 && r.polls === 1 && r.id === '260810120000-aaaaaa', JSON.stringify(r));
      await pg.close();
    }
    // ── J2·J3 2건 동시 큐잉 = 둘 다 생존 · 화면 주인은 나중 것
    {
      const pg = await open(browser, port, 'edit.html');
      const r = await pg.evaluate(() => {
        const A = '260810130000-a11111', B = '260810130500-b22222', t = Date.now();
        pendSet({ id: A, t0: t, lbl: '편집 중' }); pollEdit(A, t, t - 90000, '편집 중', '');
        pendSet({ id: B, t0: t, lbl: '편집 중' }); pollEdit(B, t, t - 90000, '편집 중', '');
        return { slots: nmJobs.list('nm_edit_pend').length, polls: nmJobs.count('nm_edit_pend'), a: nmJobs.busy('nm_edit_pend', A), b: nmJobs.busy('nm_edit_pend', B), owner: EDIT_ID };
      });
      ck('J2 편집 2건 동시 큐잉 = 첫 작업 생존', r.polls === 2 && r.a && r.b && r.slots === 2, JSON.stringify(r));
      ck('J3 편집 화면 주인 = 나중 작업', r.owner === '260810130500-b22222', 'EDIT_ID=' + r.owner);
      await pg.close();
    }
    // ── J4 같은 작업 중복 폴 차단
    {
      const pg = await open(browser, port, 'edit.html');
      const r = await pg.evaluate(() => { const A = '260810140000-c33333', t = Date.now(); pollEdit(A, t, t - 90000, '편집 중', ''); pollEdit(A, t, t - 90000, '편집 중', ''); return nmJobs.count('nm_edit_pend'); });
      ck('J4 편집 같은 작업 중복 폴 차단', r === 1, 'polls=' + r);
      await pg.close();
    }
    /* ── J5 재개 = 진행분 전건 · 대기 화면은 **접힌 채**로 시작하고 레일 행 탭으로만 펼친다
       (운영자 260816 "박스 누르면 제작중인 스캐닝이 뜨고" · 구 계약 = 「대기 화면은 최신 1건 자동 노출」)
       ⚠ 축을 지운 게 아니라 **뒤집고 한 겹 더 얹었다** — 구판은 `wrap===true`(자동 노출)를 요구했는데,
         그 자동 노출이 결과 창을 상시 점유해서 제작 중엔 과거 제작물을 여는 길이 통째로 막혀 있었다
         (edit.html nmJobShow 의 `_polling` 차단줄 = 그 점유의 부작용 · 같은 커밋에서 해제).
         그래서 여기선 ⓐ 처음엔 안 뜬다 ⓑ nmJobOpen 을 부르면 뜬다 **둘 다** 본다 = 무증상화 0
         (ⓑ가 없으면 「그냥 안 뜬다」로 퇴화해도 초록이라 계약이 죽는다). */
    {
      const pg = await open(browser, port, 'edit.html', () => {
        const t = Date.now();
        localStorage.setItem('nm_edit_pend', JSON.stringify([{ id: '260810150500-e55555', t0: t, lbl: '편집 중' }, { id: '260810150000-d44444', t0: t, lbl: '편집 중' }]));
      });
      const r = await pg.evaluate(() => ({ polls: nmJobs.count('nm_edit_pend'), owner: EDIT_ID, wrap: !document.querySelector('#vwrap').hidden }));
      const opened = await pg.evaluate(async () => {          // 레일 행 탭 = 그 작업의 스캐닝 화면을 펼치는 유일 경로
        try { window.nmJobOpen('260810150500-e55555'); } catch (e) { return 'throw:' + e.message; }
        await new Promise(r => setTimeout(r, 260));
        const vw = document.querySelector('#vwrap');
        return { shown: !vw.hidden, hasScan: !!vw.querySelector('.scanline') };   // 스캔라인 = 대기 스테이지 실물(빈 창 노출을 통과로 오판하지 않는다)
      });
      ck('J5 편집 재개 = 진행분 전건 · 대기 화면 접힘 → 행 탭으로 펼침',
        r.polls === 2 && r.owner === '260810150500-e55555' && !r.wrap && opened && opened.shown === true && opened.hasScan === true,
        JSON.stringify(r) + ' → 탭 후 ' + JSON.stringify(opened));
      await pg.close();
    }
    // ── J6 음원
    {
      const pg = await open(browser, port, 'song.html');
      const r = await pg.evaluate(() => {
        const A = '260810160000-f66666', B = '260810160500-g77777', t = Date.now();
        pendSet({ id: A, mode: 'suno', t0: t }); pollSong(A, 'suno', t, t - 90000, null);
        pendSet({ id: B, mode: 'suno', t0: t }); pollSong(B, 'suno', t, t - 90000, null);
        return { polls: nmJobs.count('nm_song_pend'), slots: nmJobs.list('nm_song_pend').length, owner: FOCUS_ID };
      });
      ck('J6 음원 2건 동시 큐잉', r.polls === 2 && r.slots === 2 && r.owner === '260810160500-g77777', JSON.stringify(r));
      await pg.close();
    }
    // ── J7 콘티·프롬프팅
    {
      const pg = await open(browser, port, 'sb.html');
      const r = await pg.evaluate(() => { poll('sb_out/aaa/board.md', 'aaa'); poll('sb_out/bbb/board.md', 'bbb'); return { polls: nmJobs.count('sb_jobs'), owner: FOCUS_JOB }; });
      ck('J7a 콘티 2건 동시 폴', r.polls === 2 && r.owner === 'bbb', JSON.stringify(r));
      await pg.close();
      const pk = await open(browser, port, 'k.html');
      const rk = await pk.evaluate(() => { poll('k_out/aaa/prompt.md', null); poll('k_out/bbb/prompt.md', null); return { polls: nmJobs.count('k_polls'), owner: FOCUS_OUT }; });
      ck('J7b 프롬프팅 2건 동시 폴', rk.polls === 2 && rk.owner === 'k_out/bbb/prompt.md', JSON.stringify(rk));
      await pk.close();
    }
    // ── J8 큐영상
    {
      const pg = await open(browser, port, 'vd.html', () => localStorage.setItem('vd_jobs', JSON.stringify([
        { id: 'v1', out: 'vd_out/v1/video.json', n: 1, status: 'run' }, { id: 'v2', out: 'vd_out/v2/video.json', n: 1, status: 'run' }])));
      await pg.waitForTimeout(600);
      const r = await pg.evaluate(() => nmJobs.count('vd_jobs'));
      ck('J8 큐영상 진행분 전건 재개', r === 2, 'polls=' + r);
      await pg.close();
    }
  } catch (e) {
    console.log('ABORT | ' + String((e && e.message) || e));
    FAIL++;
  } finally {
    try { await browser.close(); } catch (_) {}
    try { srv.close(); } catch (_) {}
  }
  console.log('── smoke_jobsq ' + (FAIL ? 'FAIL ' + FAIL + '건' : 'PASS') + ' (통과 ' + PASS + ')');
  process.exit(FAIL ? 1 : 0);
})();
