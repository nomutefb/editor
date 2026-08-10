#!/usr/bin/env node
// ═══════════════════════════════════════════════════════════════════════════════
// smoke_editattach.js — 영상 편집 '두 영상 연속 제작' 실흐름 스모크(운영자 260810 "추가 옵션이 1번 영상에 귀속되어 선택 불가")
//
// ⚠ 신설 사유 = 260810 a41f6764(영상별 칸 분리)의 검증이 **가짜 데이터 직호출**이라 실흐름(진짜 첨부 → 발사 → 재첨부)이
//   한 번도 안 밟혔고, 운영자 실사용에서 "하나도 반영 안 됨"이 났다. 이 스모크는 그 순서를 실이벤트로 그대로 밟는다:
//   ① 영상A 첨부(실 #file change + DataTransfer) → ② 트래킹 ON(실 클릭) → 인물 분석 → 얼굴 3명 ③ 이름 배정
//   ④ 생성(발사 1 · 페이로드 실측) → ⑤ 영상B 첨부 → **칸 전환 실측**(등장인물 비워지고 B 분석 자동 발사 · A 칸은 보관)
//   ⑥ B에서 모자이크 선택 가능 ⑦ 발사 2 = B 키 + B 옵션만(A 이름 미혼입) + 작업 1 폴 생존(병렬)
//   + 이중 업로드 0(트래킹 켠 채 첨부 시 분석이 첨부 업로드를 재사용하는가 — 가짜 데이터로는 원리적으로 안 보이는 축)
//   + 주소 소스 우선 칸(파일 붙인 채 주소를 걸면 칸이 주소를 따라가는가 = 발사 페이로드 2167행과 같은 우선순위)
//
// 원커맨드: node shared/smoke_editattach.js            (rc 0 = 전부 PASS)
// 킬테스트: node shared/smoke_editattach.js --viewer=<구판 사본 디렉터리>   → 구판이면 칸 전환·이중 업로드 축이 FAIL로 검출
// 서버 = 정적 http.server + Playwright 라우트로 api 스텁(발사 0 · 러너·과금 무접촉 · smoke_jobsq 원칙 동축)
// 포트대: 8876~8880 (형제 스모크와 분리) · 스샷 = $SHOT_DIR 또는 시스템 임시폴더(레포 무접촉)
// ═══════════════════════════════════════════════════════════════════════════════
'use strict';
const path = require('path');
const fs = require('fs');
const os = require('os');
const { spawn, execSync } = require('child_process');
const ROOT = path.resolve(__dirname, '..');
const VIEWER = (process.argv.find(a => a.startsWith('--viewer=')) || '').slice(9) || path.join(ROOT, 'viewer');
const SHOT_DIR = process.env.SHOT_DIR || path.join(os.tmpdir(), 'nm-editattach');
const SHOT_TAG = (process.argv.find(a => a.startsWith('--tag=')) || '').slice(6) || 'after';

function loadPlaywright() {
  try { return require('playwright-core'); } catch (_) {}
  const cache = path.join(os.tmpdir(), 'nomute-smoke-deps');
  const mod = path.join(cache, 'node_modules', 'playwright-core');
  if (!fs.existsSync(mod)) {
    console.log('· playwright-core 미설치 → 임시 캐시 설치(1회): ' + cache);
    fs.mkdirSync(cache, { recursive: true });
    execSync('npm i --prefix "' + cache + '" playwright-core --no-audit --no-fund --loglevel=error', { stdio: 'inherit' });
  }
  return require(mod);
}
function chromiumPath() {
  const cands = [process.env.CHROMIUM_PATH, '/opt/pw-browsers/chromium'];
  try { cands.push(execSync('which chromium chromium-browser google-chrome 2>/dev/null | head -1').toString().trim()); } catch (_) {}
  for (const c of cands) { if (c && fs.existsSync(c)) return c; }
  throw new Error('크로미엄 실행 파일을 못 찾음 — CHROMIUM_PATH env로 지정해라');
}
async function startServer() {
  for (let port = 8876; port < 8881; port++) {
    const srv = spawn('python3', ['-m', 'http.server', String(port), '-d', VIEWER], { stdio: 'ignore' });
    const ok = await new Promise(res => {
      let done = false;
      srv.on('exit', () => { if (!done) { done = true; res(false); } });
      setTimeout(async () => {
        if (done) return;
        try { const r = await fetch('http://127.0.0.1:' + port + '/edit.html', { method: 'HEAD' }); done = true; res(r.ok); }
        catch (_) { done = true; try { srv.kill(); } catch (e) {} res(false); }
      }, 700);
    });
    if (ok) return { srv, port };
  }
  throw new Error('로컬 서버 기동 실패(8876~8880)');
}

const R = [];
function chk(name, pass, detail) { R.push({ name, pass }); console.log((pass ? 'PASS' : 'FAIL') + ' | ' + name + ' | ' + detail); }
const J = o => { try { return JSON.stringify(o); } catch (_) { return String(o); } };

(async () => {
  const pw = loadPlaywright();
  const { srv, port } = await startServer();
  const br = await pw.chromium.launch({ executablePath: chromiumPath(), args: ['--no-sandbox'] });
  const upCreate = {};              // 파일명 → 업로드 시작 횟수(이중 업로드 검출기)
  const editPayloads = [];          // 발사 페이로드 실측
  let trackN = 0; const trackReq = [];
  try {
    const pg = await br.newPage({ viewport: { width: 1280, height: 1000 } });
    const errs = []; pg.on('pageerror', e => errs.push(String(e).slice(0, 120)));
    const JPG1 = Buffer.from('/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/wAALCAABAAEBAREA/8QAFAABAAAAAAAAAAAAAAAAAAAACf/EABQQAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQEAAD8AKp//2Q==', 'base64');
    await pg.route('**/api/upload*', async rt => {
      const req = rt.request();
      if (req.method() === 'GET') return rt.fulfill({ status: 200, contentType: 'application/json', body: '{"ok":true}' });
      if (req.method() === 'PUT') { await new Promise(r => setTimeout(r, 900)); return rt.fulfill({ status: 200, contentType: 'application/json', body: '{"etag":"e1"}' }); }
      let b = {}; try { b = JSON.parse(req.postData() || '{}'); } catch (_) {}
      if (b.action === 'create') { upCreate[b.name] = (upCreate[b.name] || 0) + 1; return rt.fulfill({ status: 200, contentType: 'application/json', body: J({ key: 'up_src/smk-' + b.name, uploadId: 'u1', part: 33554432 }) }); }
      if (b.action === 'complete') return rt.fulfill({ status: 200, contentType: 'application/json', body: '{"ok":true,"size":1}' });
      return rt.fulfill({ status: 200, contentType: 'application/json', body: '{"ok":true}' });
    });
    await pg.route('**/api/track*', async rt => {
      const req = rt.request(); const u = new URL(req.url());
      if (req.method() === 'POST') { trackN++; let b = {}; try { b = JSON.parse(req.postData() || '{}'); } catch (_) {} trackReq.push({ id: 'tk' + trackN, r2key: b.r2key || '', url: b.url || '' }); return rt.fulfill({ status: 200, contentType: 'application/json', body: J({ id: 'tk' + trackN }) }); }
      const f = u.searchParams.get('f'), id = u.searchParams.get('id') || '';
      if (f === 'tracks') {
        const n = id === 'tk1' ? 3 : 2;   // 영상A = 3명 · 영상B = 2명(목록이 실제로 갈리는지 개수로 확인)
        const people = Array.from({ length: n }, (_, i) => ({ pid: i + 1, crop: 'crops/p' + (i + 1) + '.jpg', first: 0, dur: 3 }));
        return rt.fulfill({ status: 200, contentType: 'application/json', body: J({ people, meta: { made: 'm1' } }) });
      }
      if (f === 'crop') return rt.fulfill({ status: 200, contentType: 'image/jpeg', body: JPG1 });
      return rt.fulfill({ status: 404, contentType: 'text/plain', body: 'x' });
    });
    await pg.route('**/api/edit*', async rt => {
      const req = rt.request();
      if (req.method() === 'POST') { let b = {}; try { b = JSON.parse(req.postData() || '{}'); } catch (_) {} editPayloads.push(b); return rt.fulfill({ status: 200, contentType: 'application/json', body: J({ id: 'j' + editPayloads.length }) }); }
      return rt.fulfill({ status: 404, contentType: 'text/plain', body: 'x' });
    });
    await pg.route('**/manifest.json*', rt => rt.fulfill({ status: 200, contentType: 'application/json', body: '{}' }));

    await pg.goto('http://127.0.0.1:' + port + '/edit.html', { waitUntil: 'load', timeout: 30000 });
    await pg.waitForSelector('#xtrsec [data-xo="pinset"]', { timeout: 15000 });
    await pg.evaluate(() => { try { localStorage.clear(); } catch (_) {} });

    const attach = name => pg.evaluate(async nm => {
      const cv = document.createElement('canvas'); cv.width = 320; cv.height = 240;
      const cx = cv.getContext('2d'); let hue = 0;
      const tick = setInterval(() => { cx.fillStyle = 'hsl(' + ((hue += 40) % 360) + ',60%,50%)'; cx.fillRect(0, 0, 320, 240); }, 60);
      const rec = new MediaRecorder(cv.captureStream(12), { mimeType: 'video/webm' });
      const parts = []; rec.ondataavailable = e => parts.push(e.data);
      const fin = new Promise(r => { rec.onstop = r; });
      rec.start(); await new Promise(r => setTimeout(r, nm === 'vidA.webm' ? 700 : 1200)); rec.stop(); await fin; clearInterval(tick);
      const f = new File([new Blob(parts, { type: 'video/webm' })], nm, { type: 'video/webm' });
      const dt = new DataTransfer(); dt.items.add(f);
      const inp = document.getElementById('file'); inp.files = dt.files;
      inp.dispatchEvent(new Event('change'));
    }, name);

    // ① 영상A 첨부 → 칸이 A로 선다
    await attach('vidA.webm');
    const aKey = await pg.waitForFunction(() => (typeof XTR_SRC !== 'undefined') && XTR_SRC.indexOf('f:vidA.webm') === 0, null, { timeout: 8000 }).then(() => true).catch(() => false);
    chk('E1 영상A 첨부 = A 칸', aKey, aKey ? 'XTR_SRC=f:vidA…' : '칸 미전환(구판 = 소스별 칸 자체가 없음)');

    // ② 트래킹 ON(실 클릭) → 인물 분석 → 얼굴 3명 · 첨부 업로드 재사용(이중 업로드 0)
    await pg.click('#xtrsec [data-xo="pinset"]');
    const facesA = await pg.waitForFunction(() => document.querySelectorAll('#xtrsec .xface').length === 3, null, { timeout: 20000 }).then(() => true).catch(() => false);
    chk('E2 트래킹 ON = A 인물 3명', facesA, 'xface=' + await pg.evaluate(() => document.querySelectorAll('#xtrsec .xface').length));
    chk('E3 이중 업로드 0(A)', (upCreate['vidA.webm'] || 0) === 1, 'vidA 업로드 시작 ' + (upCreate['vidA.webm'] || 0) + '회(분석이 첨부 업로드를 기다려 재사용해야 1회)');
    chk('E3b 분석 페이로드 = A 업로드 키', trackReq.length >= 1 && /vidA/.test(trackReq[0].r2key), J(trackReq[0] || {}));

    // ③ 이름 배정(입력 + 얼굴 탭)
    await pg.fill('#xtrsec .nmin[data-gn="0"]', '철수');
    await pg.click('#xtrsec .xface[data-pid="1"]');

    // ④ 발사 1 — 페이로드 실측(A 키 · 트래킹 · 이름)
    await pg.waitForFunction(() => (typeof _uploading !== 'undefined') && !_uploading && (typeof FILE_R2 !== 'undefined') && !!FILE_R2, null, { timeout: 15000 });
    await pg.click('#editGo');
    await pg.waitForFunction(() => (typeof EDIT_ID !== 'undefined') && EDIT_ID === 'j1', null, { timeout: 10000 }).catch(() => {});
    const p1 = editPayloads[0] || {};
    chk('E4 발사1 = A 키 + 트래킹 + 이름', /vidA/.test(p1.r2key || '') && !!(p1.opts && p1.opts.xtr && p1.opts.xtr.pinset) && J(p1).includes('철수'), 'r2key=' + (p1.r2key || '') + ' · names=' + J((p1.opts && p1.opts.xtr && p1.opts.xtr.names) || null));

    // ⑤ 영상B 첨부(작업1 제작 중) — 칸 전환 = 등장인물 비움 + 이름 새 칸 + A 칸 보관
    await attach('vidB.webm');
    const bKey = await pg.waitForFunction(() => (typeof XTR_SRC !== 'undefined') && XTR_SRC.indexOf('f:vidB.webm') === 0, null, { timeout: 8000 }).then(() => true).catch(() => false);
    const fresh = bKey ? await pg.evaluate(() => ({ faces: XTR_FACES.length, name: (document.querySelector('#xtrsec .nmin[data-gn="0"]') || { value: 'x' }).value })) : { faces: -1, name: 'x' };
    chk('E5 영상B 첨부 = B 칸으로 전환(등장인물 비움·이름 새 칸)', bKey && fresh.faces === 0 && fresh.name === '', bKey ? ('faces=' + fresh.faces + ' · name="' + fresh.name + '"') : '칸 미전환 = A 목록 잔류(운영자 실사고 증상)');
    if (!bKey) { try { fs.mkdirSync(SHOT_DIR, { recursive: true }); await pg.locator('#xtrsec').screenshot({ path: path.join(SHOT_DIR, 'before.png') }); console.log('· 스샷: ' + path.join(SHOT_DIR, 'before.png')); } catch (_) {} }
    const facesB = await pg.waitForFunction(() => document.querySelectorAll('#xtrsec .xface').length === 2, null, { timeout: 25000 }).then(() => true).catch(() => false);
    chk('E6 B 인물 자동 분석 = 2명(재분석 자동)', facesB, 'xface=' + await pg.evaluate(() => document.querySelectorAll('#xtrsec .xface').length) + ' (구판 = 목록이 안 비어 재분석이 영영 안 걸림)');
    chk('E7 이중 업로드 0(B)', (upCreate['vidB.webm'] || 0) === 1, 'vidB 업로드 시작 ' + (upCreate['vidB.webm'] || 0) + '회');
    const aBox = await pg.evaluate(() => { try { const all = JSON.parse(localStorage.getItem('nm_xtr_src') || '{}'); const k = Object.keys(all).find(x => x.indexOf('f:vidA.webm') === 0); return k ? { f: (all[k].f || []).length, nm: (all[k].g || [{}])[0].name || '' } : null; } catch (e) { return null; } });
    chk('E8 A 칸 보관(얼굴 3·이름 유지)', !!aBox && aBox.f === 3 && aBox.nm === '철수', J(aBox));
    try { fs.mkdirSync(SHOT_DIR, { recursive: true }); await pg.locator('#xtrsec').screenshot({ path: path.join(SHOT_DIR, SHOT_TAG + '.png') }); console.log('· 스샷: ' + path.join(SHOT_DIR, SHOT_TAG + '.png')); } catch (_) {}

    // ⑥ B에서 추가 옵션 선택 자유(모자이크 ON = 게이지 카드)
    await pg.click('#xtrsec [data-xo="mosaic"]');
    const mosaicOn = await pg.evaluate(() => (typeof XTR !== 'undefined') && XTR.mosaic === true && !!document.querySelector('#xtrsec [data-xg="size"]'));
    chk('E9 B에서 모자이크 선택 가능', mosaicOn, 'XTR.mosaic + 크기 게이지 렌더');

    // ⑦ 발사 2 — B 키 + B 옵션만(A 이름 미혼입) · 작업1 폴 생존(병렬 2건)
    await pg.waitForFunction(() => (typeof _uploading !== 'undefined') && !_uploading && (typeof FILE_R2 !== 'undefined') && /vidB/.test(FILE_R2), null, { timeout: 15000 });
    await pg.click('#editGo');
    await pg.waitForFunction(() => (typeof EDIT_ID !== 'undefined') && EDIT_ID === 'j2', null, { timeout: 10000 }).catch(() => {});
    const p2 = editPayloads[1] || {};
    chk('E10 발사2 = B 키 + 모자이크 · A 이름 미혼입', /vidB/.test(p2.r2key || '') && !!(p2.opts && p2.opts.xtr && p2.opts.xtr.mosaic) && !J(p2).includes('철수'), 'r2key=' + (p2.r2key || ''));
    const jobs = await pg.evaluate(() => { try { return { n: nmJobs.list('nm_edit_pend').length, j1: nmJobs.busy('nm_edit_pend', 'j1') }; } catch (e) { return { n: -1, j1: false }; } });
    chk('E11 병렬 생존 = 작업 2건 + 작업1 폴 유지', jobs.n === 2 && jobs.j1 === true, J(jobs));

    // ⑧ 주소 소스 = 칸도 주소 우선(발사 페이로드와 같은 우선순위)
    await pg.evaluate(() => { const u = document.getElementById('url'); u.value = 'https://example.com/v3.mp4'; u.dispatchEvent(new Event('input')); });
    await pg.click('#xtrsec [data-xo="mosaic"]');   // 아무 상호작용 = 다시 그리기 → 칸 재판정
    const uKey = await pg.evaluate(() => (typeof XTR_SRC !== 'undefined') && XTR_SRC === 'u:https://example.com/v3.mp4');
    chk('E12 주소를 걸면 칸도 주소를 따른다', uKey, await pg.evaluate(() => (typeof XTR_SRC !== 'undefined') ? XTR_SRC : '(구판 = 칸 없음)'));

    chk('E13 페이지 에러 0', errs.length === 0, errs.length ? errs.join(' · ') : '0');
    try { await pg.close(); } catch (_) {}
  } catch (e) {
    chk('실행', false, 'ABORT | ' + String(e).slice(0, 160));
  } finally {
    try { await br.close(); } catch (_) {}
    try { srv.kill(); } catch (_) {}
  }
  const fail = R.filter(x => !x.pass).length;
  console.log('── editattach 스모크 ' + (R.length - fail) + '/' + R.length + (fail ? ' — FAIL ' + fail + '건' : ' 전부 PASS') + ' (서버 종료됨)');
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error('SMOKE 크래시:', e); process.exit(1); });
