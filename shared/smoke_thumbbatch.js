'use strict';
/* ═══════════════════════════════════════════════════════════════════════════════
 * smoke_thumbbatch.js — 이미지 스튜디오 **묶음 발사(헤더+자막) ↔ 기기 간 동기** 상비 스모크
 *   (운영자 260913 «헤더 제작 칸에 텍스트가 있고 오버레이 제작칸에도 텍스트가 있는데, 생성을 누르면 릴스로 둘다
 *    생성이 되어야 되는데, 오버레이만 생성되는 버그»)
 *
 * ▷ 왜 신설: 한 번의 「생성」이 헤더·자막 **요청 2개**로 나가면 서버는 작업 id를 2개 발급한다. 구판 dispatchBatch는
 *   첫 id(헤더)만 thid로 들고 영속 슬롯(pendPut)도 안 넣어서, 기기 간 진행 동기(nm-jobs sync · /api/jobs)가 오버레이 id를
 *   「이 화면에 없는 작업」으로 읽고 **오버레이만 담긴 중복 잡**을 하나 더 세웠다 — 그 중복 잡이 먼저 끝나며 「최근 제작」
 *   스냅샷·이력을 오버레이 단독으로 덮어썼다(서버 산출은 둘 다 정상 = 러너 로그로는 절대 안 보이는 축).
 *   기존 스모크(jobsq)는 영상 5탭의 「2건 동시 생존」만 재고, 「한 발사 = id N개」 축은 없었다.
 *
 * 판정(폰 430 · 실렌더 · 네트워크 발사 0 = 목 API가 id를 발급하고 지연 뒤 산출을 놓는다 = 러너·과금 무접촉)
 *   B1 같은 기기 = 발사 뒤 동기(nmJobs.sync)가 돌아도 **잡 행 1개**(중복 0) · 슬롯 1개가 형제 id 2개(thids)를 쥔다
 *   B2 같은 기기 = 완료 후 「2/2장」 · 최근 제작(nomute_thumb_last) 2장 · 로컬 이력 2건(중복 0) · 서버 done 통보 = 두 id 전부
 *   B3 새로고침(발사 뒤 화면 이탈) = 영속 슬롯에서 **한 잡(0/2장)** 으로 재개 → 완료 2/2장
 *   B4 다른 기기(빈 저장소) = 서버 원장의 형제 2건(같은 bid)이 **한 잡**으로 합류(0/2장 · 이름표 합성) → 완료 2/2장
 *
 * 원커맨드:  node shared/smoke_thumbbatch.js        (종료코드 0 = 전부 PASS)
 * 담당 표면: viewer/thumb.html(dispatchBatch·pollJob·pendPut/pendCut·restorePending) · viewer/nm-jobs.js(sync thids·absorb·bid)
 *           · functions/_middleware.js putLive(bid·bi) · functions/api/thumb.js(bid·bi 에코 — 목 API가 그 계약을 미러)
 * ═══════════════════════════════════════════════════════════════════════════════ */
const path = require('path');
const fs = require('fs');
const os = require('os');
const http = require('http');
const { execSync } = require('child_process');
const ROOT = path.resolve(__dirname, '..');
const VIEWER = path.join(ROOT, 'viewer');
const PORT = 8931;   // 자기 포트대(형제 스모크와 분리 · smoke_all 병렬 무충돌)
const HDR_MS = 9000, OV_MS = 5000;   // 산출 도착(오버레이가 먼저 = 실사고 조건)

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
  const cands = [process.env.CHROMIUM_PATH, '/opt/pw-browsers/chromium'];   // seal-ok: 형제 smoke_thumbapi.js 는 브라우저 미기동(함수 모듈 직접 import) = 크로미엄 경로 비대상
  try { cands.push(execSync('which chromium chromium-browser google-chrome 2>/dev/null | head -1').toString().trim()); } catch (_) {}
  for (const c of cands) { if (c && fs.existsSync(c)) return c; }
  throw new Error('chromium 실행 파일을 찾지 못함(CHROMIUM_PATH 지정)');   // seal-ok: 형제 smoke_thumbapi.js 는 브라우저 미기동 = 크로미엄 경로 비대상(위 줄과 같은 사유)
}
const MIME = { html: 'text/html', js: 'text/javascript', css: 'text/css', json: 'application/json', woff2: 'font/woff2', png: 'image/png', webp: 'image/webp', svg: 'image/svg+xml', jpg: 'image/jpeg' };
const PNG1 = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=', 'base64');

// ── 목 API(functions/api/thumb.js · _middleware putLive · api/jobs 계약 미러 — 응답 모양만, 발사 0) ──
const live = {}, done = {}, srcs = {}, dones = [];
const kst = () => new Date(Date.now() + 9 * 3600e3).toISOString().replace(/[^0-9]/g, '').slice(2, 14);
const rid = () => Math.random().toString(16).slice(2, 8);
function readBody(q) { return new Promise(res => { let b = ''; q.on('data', c => b += c); q.on('end', () => res(b)); }); }
function json(r, o, s = 200) { r.writeHead(s, { 'content-type': 'application/json', 'cache-control': 'no-store' }); r.end(JSON.stringify(o)); }
function seedLive(id, mode, lbl, bid, bi, base) {   // 서버 원장 레코드(putLive 문법) + 지연 산출
  const outs = mode === 'header' ? [{ path: `${base}/thumb_out/${id}/box.jpg`, label: '흰칸' }] : [{ path: `${base}/thumb_out/${id}/opa60.png`, label: 'OPA60' }];
  live[id] = { kind: 'thumb', id, t0: Date.now(), out: outs[0].path, outs, lbl, bid, bi };
  setTimeout(() => { done[id] = outs.map(o => [o.path.split('/').pop(), o.path]); }, mode === 'header' ? HDR_MS : OV_MS);
  return outs;
}
function serve() {
  return new Promise((res, rej) => {
    const s = http.createServer(async (q, r) => {
      const u = new URL(q.url, 'http://x'); const base = 'http://127.0.0.1:' + PORT;
      if (u.pathname === '/api/thumb' && q.method === 'POST') {
        const body = JSON.parse(await readBody(q) || '{}'); const p = body.params || {}; const id = kst() + '-' + rid();
        const mode = (body.app === '2' && p.mode === 'header') ? 'header' : 'overlay';
        const lbl = (body.src && body.src.lbl) || '', bid = (body.src && body.src.bid) || undefined, bi = (body.src && body.src.bi != null) ? body.src.bi : undefined;
        srcs[id] = body.src || null;
        const outs = seedLive(id, mode, lbl, bid, bi, base);
        return json(r, { ok: true, id, out: outs[0].path, outs, ...(lbl ? { lbl } : {}), ...(bid ? { bid } : {}), ...(bi != null ? { bi } : {}) });
      }
      if (u.pathname === '/api/thumb' && q.method === 'GET') {
        if (u.searchParams.get('recent') != null) return json(r, { ids: Object.keys(done).sort().reverse() });
        const mid = u.searchParams.get('meta'), sid = u.searchParams.get('src');
        if (mid) return done[mid] ? json(r, done[mid]) : json(r, { pending: true }, 404);
        if (sid) return (done[sid] && srcs[sid]) ? json(r, srcs[sid]) : json(r, { pending: true }, 404);
        return json(r, { error: 'bad' }, 400);
      }
      if (u.pathname === '/api/jobs' && q.method === 'GET') return json(r, { items: Object.values(live).sort((a, b) => b.t0 - a.t0) });
      if (u.pathname === '/api/jobs' && q.method === 'POST') { const b = JSON.parse(await readBody(q) || '{}'); (b.done || []).forEach(d => { const id = typeof d === 'string' ? d : d && d.id; dones.push(id); delete live[id]; }); return json(r, { ok: true }); }
      if (u.pathname === '/api/spellcheck') { const b = JSON.parse(await readBody(q) || '{}'); return json(r, { ok: true, corrected: b.texts || [], corrections: (b.texts || []).map(() => []) }); }
      if (u.pathname.startsWith('/api/')) return json(r, { ok: true, items: [], ids: [] });
      const m = u.pathname.match(/^\/thumb_out\/([^/]+)\/([^/]+)$/);
      if (m) { if (done[m[1]]) { r.writeHead(200, { 'content-type': m[2].endsWith('.jpg') ? 'image/jpeg' : 'image/png', 'cache-control': 'no-store' }); r.end(PNG1); } else { r.writeHead(404); r.end(); } return; }
      if (u.pathname === '/thumb-hist.json') return json(r, []);
      const p = path.join(VIEWER, decodeURIComponent(u.pathname).replace(/^\/+/, '') || 'index.html');
      fs.readFile(p, (e, b) => { if (e) { r.writeHead(404); r.end(); return; } r.writeHead(200, { 'content-type': MIME[path.extname(p).slice(1)] || 'application/octet-stream' }); r.end(b); });
    });
    s.on('error', rej); s.listen(PORT, '127.0.0.1', () => res(s));
  });
}

const state = page => page.evaluate(() => ({   // 화면 상태 = 잡 행·슬롯·최근 제작·이력(전부 사용자 눈에 닿는 축)
  rows: [...document.querySelectorAll('#jobs .job')].map(r => r.textContent.replace(/\s+/g, ' ').trim()),
  pend: (() => { try { return JSON.parse(localStorage.getItem('nm_thumb_pend') || '[]').map(p => ({ id: p.id, thids: p.thids || null, outs: (p.outs || []).length, remote: !!p._remote })); } catch (e) { return []; } })(),
  last: (() => { try { const v = JSON.parse(localStorage.getItem('nomute_thumb_last') || 'null'); return v && v.items ? v.items.map(i => i.url.split('/').pop()) : null; } catch (e) { return null; } })(),
  hist: (() => { try { return JSON.parse(localStorage.getItem('nomute_thumb_hist') || '[]').map(e => String(e.url || '').split('/').pop().split('?')[0]); } catch (e) { return []; } })(),
}));
const until = async (page, ms, pred) => { const t0 = Date.now(); let st; while (Date.now() - t0 < ms) { st = await state(page); if (pred(st)) return st; await page.waitForTimeout(400); } return st; };

(async () => {
  const srv = await serve();
  const { chromium } = loadPlaywright();
  const browser = await chromium.launch({ executablePath: chromiumPath(), args: ['--no-sandbox'] });
  const base = `http://127.0.0.1:${PORT}`;
  const results = []; const ok = (name, cond, why) => { results.push([name, !!cond, why || '']); console.log((cond ? 'PASS' : 'FAIL') + ' | ' + name + (cond ? '' : ' | ' + why)); };
  const errs = [];
  const fire = async (page) => {   // 헤더+자막 채우고 「생성」 — 맞춤법 목(오타 0) → 곧장 배치 발사
    await page.fill('#cSub', '부제 테스트'); await page.fill('#cTitle', '제목 테스트'); await page.fill('#cLines', '*강조* 자막 한 줄');
    await page.waitForTimeout(200); await page.click('#go'); await page.waitForTimeout(1200);
  };
  const open = async (ctx) => { const page = await ctx.newPage(); page.on('pageerror', e => errs.push(e.message)); await page.goto(base + '/thumb.html', { waitUntil: 'load' }); await page.waitForSelector('#go'); await page.waitForTimeout(600); return page; };

  // ── B1·B2 같은 기기: 발사 → 동기 → 완료 ──
  {
    const ctx = await browser.newContext({ viewport: { width: 430, height: 900 }, deviceScaleFactor: 2 });
    const page = await open(ctx);
    await fire(page);
    let st = await state(page);
    ok('B1-0 발사 = 잡 행 1개(0/2장)', st.rows.length === 1 && /0\/2장/.test(st.rows[0]), JSON.stringify(st.rows));
    ok('B1-1 발사 = 영속 슬롯 1개가 형제 id 2개(thids)', st.pend.length === 1 && Array.isArray(st.pend[0].thids) && st.pend[0].thids.length === 2, JSON.stringify(st.pend));
    await page.evaluate(() => window.nmJobs && nmJobs.sync()); await page.waitForTimeout(900);   // 기기 간 동기 강제(실제 = 20s 주기 + 복귀)
    st = await state(page);
    ok('B1-2 동기 뒤에도 잡 행 1개(오버레이 중복 잡 0)', st.rows.length === 1, JSON.stringify(st.rows));
    ok('B1-3 동기 뒤에도 슬롯 1개(형제 낱개 슬롯 흡수)', st.pend.length === 1, JSON.stringify(st.pend));
    st = await until(page, 20000, s => s.rows.length && /2\/2장/.test(s.rows[0]) && s.last && s.last.length === 2);
    await page.evaluate(() => window.nmJobs && nmJobs.sync()); await page.waitForTimeout(900);   // 완료 뒤 동기 = 끝난 형제를 「제작중」으로 되살리지 않는다
    st = await state(page);
    ok('B2-0 완료 = 「2/2장」 잡 행 1개', st.rows.length === 1 && /2\/2장/.test(st.rows[0]), JSON.stringify(st.rows));
    ok('B2-1 최근 제작 스냅샷 = 2장(헤더+자막)', st.last && st.last.length === 2 && st.last.some(f => f === 'box.jpg') && st.last.some(f => /^opa\d+\.png$/.test(f)), JSON.stringify(st.last));
    ok('B2-2 로컬 이력 = 2건(중복 0)', st.hist.length === 2, JSON.stringify(st.hist));
    ok('B2-3 서버 done 통보 = 두 id 전부', dones.length >= 2 && new Set(dones).size >= 2 && Object.keys(live).length === 0, JSON.stringify({ dones, live: Object.keys(live) }));
    ok('B2-4 슬롯 0(완료 정리)', st.pend.length === 0, JSON.stringify(st.pend));
    await ctx.close();
  }
  // ── B3 새로고침 재개: 발사 직후 화면 이탈 → 슬롯에서 한 잡으로 ──
  {
    const ctx = await browser.newContext({ viewport: { width: 430, height: 900 }, deviceScaleFactor: 2 });
    const page = await open(ctx);
    await fire(page);
    await page.reload({ waitUntil: 'load' }); await page.waitForSelector('#go'); await page.waitForTimeout(900);
    let st = await state(page);
    ok('B3-0 새로고침 = 한 잡(0/2장)으로 재개', st.rows.length === 1 && /0\/2장|1\/2장/.test(st.rows[0]), JSON.stringify(st.rows));
    st = await until(page, 20000, s => s.rows.length && /2\/2장/.test(s.rows[0]));
    ok('B3-1 재개 잡 완료 = 2/2장 · 슬롯 0', st.rows.length === 1 && /2\/2장/.test(st.rows[0]) && st.pend.length === 0, JSON.stringify({ rows: st.rows, pend: st.pend }));
    await ctx.close();
  }
  // ── B4 다른 기기: 빈 저장소 + 서버 원장 형제 2건(같은 bid) ──
  {
    const bid = 'smokebid-' + rid(); const h = kst() + '-' + rid(), o = kst() + '-' + rid();
    seedLive(h, 'header', '릴스 헤더', bid, 0, base); seedLive(o, 'overlay', '릴스 OPA60', bid, 1, base);
    const ctx = await browser.newContext({ viewport: { width: 430, height: 900 }, deviceScaleFactor: 2 });
    const page = await open(ctx);
    await page.evaluate(() => window.nmJobs && nmJobs.sync()); await page.waitForTimeout(1200);
    let st = await state(page);
    ok('B4-0 다른 기기 = 형제 2건이 한 잡(0/2장)으로 합류', st.rows.length === 1 && /0\/2장|1\/2장/.test(st.rows[0]), JSON.stringify(st.rows));
    ok('B4-1 합류 이름표 = 발사 기기와 같은 얼굴(헤더·오버레이(60) = 「릴스 헤더·자막(OPA60)」 분해)', st.rows.length === 1 && /헤더·(오버레이|OVL)\((OPA)?60\)/.test(st.rows[0]), JSON.stringify(st.rows));
    st = await until(page, 20000, s => s.rows.length && /2\/2장/.test(s.rows[0]));
    ok('B4-2 합류 잡 완료 = 2/2장 · 최근 제작 2장', st.rows.length === 1 && /2\/2장/.test(st.rows[0]) && st.last && st.last.length === 2, JSON.stringify({ rows: st.rows, last: st.last }));
    await ctx.close();
  }
  ok('E0 pageerror 0', errs.length === 0, errs.join(' | ').slice(0, 300));
  await browser.close(); srv.close();
  const fail = results.filter(r => !r[1]).length;
  console.log(fail ? `── smoke_thumbbatch FAIL ${fail}/${results.length}` : `── smoke_thumbbatch ${results.length}/${results.length} 전부 PASS`);
  process.exit(fail ? 1 : 0);
})().catch(e => { console.log('FAIL | 스모크 자체 예외: ' + (e && e.stack || e)); process.exit(1); });
