#!/usr/bin/env node
// ═══════════════════════════════════════════════════════════════════════════════
// smoke_caprail.js — 영상 스튜디오 결과·이전 제작 레일 실측 스모크
//   (운영자 260810 "비디오 스튜디오 이전 제작이 안떠 · 방금 1개를 제작하고, 추가로 뭐 하나 더 제작하면 방금거가 유실된다
//    · 계속 이슈가 되는거니까 너가 코드로 검증하셈 · 전에 제작한건 이전 제작에 남아있어야하고, 제작 중인거는 그위 결과에 큐잉되어 들어가야해 순차적으로")
//
// ⚠ 신설 사유 = 이 레일이 **세 가지로 조용히 죽었고 화면 증상이 전부 「아무것도 없음」 하나**였다:
//   ⓐ 영상 산출(mp4)을 `<img>`로 그려 디코드 실패 → 구 onerror가 「죽은 슬롯」으로 읽고 타일을 지웠다.
//      저장소엔 2건인데 화면은 「아직 제작한 게 없습니다」(실측 260810 = 결과 0·이전 0·store 2 · 콘솔 에러 0).
//   ⓑ 완료 적재가 반쪽 — 편집·음원은 화면 주인 완료가, 콘티는 강등분이 레일에 안 얹혔다.
//   ⓒ 지난 제작 1건을 결과 칸이 끌어올려(followNewest) 이전 제작에서 빼앗았다.
// 기존 스모크 25종은 전부 「화면이 어떻게 그려졌나」(기하·잉크·부품)를 잰다 — 「끝난 작업이 목록에 남는가」는 축 자체가 없었고
// 운영자 눈이 유일한 검출기였다(insta-thumb-miss·brk_misfire 동축).
//
// 판정 5축(폰 430 실렌더 · **발사 0** = 가짜 데이터만 심는다 = 러너·과금 무접촉):
//   C1 영상 타일 생존   — mp4 항목이 타일로 남는다(ⓐ의 기계화)
//   C2 이전 제작 보존   — 지난 세션 완료분은 「이전 제작」에 남고 결과 칸이 안 빼앗는다(ⓒ)
//   C3 완료 착지        — 화면 주인 완료(edit showResult)가 레일에 얹힌다(ⓑ)
//   C4 진행 중 큐       — 슬롯이 결과 칸에 잡 행으로 서고 **최신이 맨 위**(옛날 게 아래 · 260811 개정)
//   C5 연속 제작 무유실 — 2건 연속 완료가 둘 다 남는다(= 운영자가 말한 "방금거가 유실된다" 그 자체)
//   C6 진행 중 행 진입  — 그 행을 누르면 **그 작업의 제작 화면**이 뜬다(운영자 260811 "결과 표시되는 박스를 눌렀을때 나오는 화면으로 들어가야")
//   C7 이력 칸 하나     — 「이전 제작」과 뜻이 같은 별도 머리(구 「작업 내역」)가 없다(운영자 260811 "작업 내역은 > 이전 제작이랑 같은 의미")
//   ⚠ C6·C7 신설 사유 = 셋 다 **화면 증상이 조용하다** — 행이 안 눌려도 아무 일이 안 일어나고(에러 0),
//     이력 칸이 둘로 갈려도 각각은 멀쩡해 보인다(위 칸은 늘 「(0) 아직 제작한 게 없습니다」). 운영자 눈이 유일한 검출기였다.
// ═══════════════════════════════════════════════════════════════════════════════
const { spawn, execSync } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const VIEWER = path.join(ROOT, 'viewer');

function loadPlaywright() {   // 정본 = shared/smoke_parity.js(형제 25종 공통) — ⚠ 첫 판이 `require('playwright')` 였고 **smoke_all 병렬에서만** 죽었다(단독 실행은 NODE_PATH가 있어 통과 = 가장 헷갈리는 실패). 형제가 다 가진 문법을 새 스모크만 안 가지면 조용히 빠진다(check_seal_completeness 축).
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
const { chromium } = loadPlaywright();
const TABS = [
  { f: 'edit.html', name: '편집' },
  { f: 'sb.html', name: '콘티' },
  { f: 'k.html', name: '프롬프팅' },
  { f: 'song.html', name: '음원' },
  { f: 'vd.html', name: '큐영상' },
];
const CAP_KEY = 'nomute_cap_hist';

function chromiumPath() {   // 정본 = shared/smoke_parity.js(env → /opt/pw-browsers → which · **실존 검사** 필수 = check_smoke_chromium_path 계약)
  const cands = [process.env.CHROMIUM_PATH, '/opt/pw-browsers/chromium'];
  try { cands.push(execSync('which chromium chromium-browser google-chrome 2>/dev/null | head -1').toString().trim()); } catch (_) {}
  for (const c of cands) { if (c && fs.existsSync(c)) return c; }
  throw new Error('크로미엄 실행 파일을 못 찾음 — CHROMIUM_PATH env로 지정해라');
}
async function startServer() {
  for (let port = 8841; port < 8846; port++) {   // 8841~ = 형제 스모크 포트 대역 다음 슬롯(무충돌)
    const srv = spawn('python3', ['-m', 'http.server', String(port), '-d', VIEWER], { stdio: 'ignore' });
    const ok = await new Promise(res => {
      let done = false;
      srv.on('exit', () => { if (!done) { done = true; res(false); } });
      setTimeout(async () => {
        if (done) return;
        try { const r = await fetch(`http://127.0.0.1:${port}/edit.html`); done = true; res(r.ok); }
        catch (_) { done = true; res(false); }
      }, 700);
    });
    if (ok) return { srv, base: `http://127.0.0.1:${port}/` };
    try { srv.kill(); } catch (_) {}
  }
  throw new Error('로컬 서버 기동 실패(8841~8845)');
}

/* 영상 2건은 **가짜 응답으로 준다**(page.route) — ⓐ축은 「진짜 미디어 바이트가 img 디코드에 실패」해야 재현되는데
   (없는 주소는 네트워크 오류라 다른 경로를 탄다 = 가짜 통과), 그렇다고 `viewer/` 에 임시 파일을 쓰면
   **같은 디렉터리를 서빙하는 형제 스모크가 병렬로 도는 중**에 파일이 생겼다 사라진다 → 라우트 가로채기가 유일하게 안전하다. */
const PROBE = ['_caprail_a.mp4', '_caprail_b.mp4'];
const FAKE_MP4 = Buffer.alloc(24 * 1024, 7);

const fails = [];
const okv = [];
function chk(cond, id, msg) { if (cond) okv.push(id); else fails.push(`${id} | ${msg}`); }

(async () => {
  const { srv, base } = await startServer();
  let browser;
  try {
    browser = await chromium.launch({ executablePath: chromiumPath() });
    const ctx = await browser.newContext({ viewport: { width: 430, height: 900 } });
    await ctx.route('**/_caprail_*.mp4*', r => r.fulfill({ status: 200, contentType: 'video/mp4', body: FAKE_MP4 }));   // 영상 바이트 = 여기서 준다(디스크 무접촉 = 병렬 안전)

    // ── C1·C2 = 지난 세션 완료분(mp4 2건)을 심고 5탭을 연다 ────────────────────
    const past = (b) => [
      { url: b + PROBE[0], poster: '', cap: '편집', dlname: 'a.mp4', ts: Date.now() - 7200e3 },
      { url: b + PROBE[1], poster: '', cap: '콘티', dlname: 'b.mp4', ts: Date.now() - 3600e3 },
    ];
    for (const t of TABS) {
      const page = await ctx.newPage();
      await page.addInitScript(([k, seed]) => { localStorage.setItem(k, JSON.stringify(seed)); }, [CAP_KEY, past(base)]);
      await page.goto(base + t.f, { waitUntil: 'domcontentloaded' });
      await page.waitForTimeout(1600);   // 미디어 로드 실패가 도착할 시간(구판은 이 창에서 타일이 지워졌다)
      await page.evaluate(() => { const h = document.querySelector('[id$="PrevH"]'); if (h) h.click(); });   // 「이전 제작」은 기본 접힘 = 운영자가 실제로 여는 동작을 그대로 한다(접힌 채 재면 rect 0 = 가짜 빨강)
      await page.waitForTimeout(500);
      const r = await page.evaluate(() => {
        const vis = (e) => !!(e && e.getClientRects().length);
        const prevG = document.querySelector('[id$="PrevGrid"]');
        const resG = document.querySelector('[id$="ResGrid"]');
        return {
          rail: !!document.querySelector('.nm-rail'),
          prevTiles: prevG ? [...prevG.querySelectorAll('.hist-it')].filter(vis).length : -1,
          resTiles: resG ? [...resG.querySelectorAll('.hist-it')].filter(vis).length : -1,
          store: JSON.parse(localStorage.getItem('nomute_cap_hist') || '[]').length,
          media: document.querySelectorAll('.hist-thumb video').length,
        };
      });
      chk(r.rail, `C1 ${t.name}`, '결과 레일이 안 섰다(nm-rail 상속 누락)');
      chk(r.prevTiles === 2, `C1 ${t.name} 타일`, `영상 타일 소멸 — 이전 제작 ${r.prevTiles}개(기대 2 · 저장소 ${r.store}건) = mp4를 img로 그려 onerror가 지운 축`);
      chk(r.media >= 2, `C1 ${t.name} 미디어`, `영상 항목이 <video>로 안 그려졌다(${r.media}개)`);
      chk(r.resTiles === 0, `C2 ${t.name}`, `지난 제작분을 결과 칸이 빼앗았다(결과 ${r.resTiles}개 · 기대 0 = 전부 이전 제작)`);
      await page.close();
    }

    // ── C3·C5 = 편집 완료(화면 주인 경로)가 레일에 얹히고, 연속 2건이 둘 다 남는가 ──
    {
      const page = await ctx.newPage();
      await page.goto(base + 'edit.html', { waitUntil: 'domcontentloaded' });
      await page.waitForTimeout(900);
      const r = await page.evaluate(([b, f1, f2]) => {
        localStorage.removeItem('nomute_cap_hist');
        const out = {};
        try { showResult({ url: b + f1, ts: new Date().toISOString() }, 12); } catch (e) { out.e1 = String(e.message).slice(0, 90); }
        out.after1 = JSON.parse(localStorage.getItem('nomute_cap_hist') || '[]').length;
        try { showResult({ url: b + f2, ts: new Date().toISOString() }, 9); } catch (e) { out.e2 = String(e.message).slice(0, 90); }
        out.after2 = JSON.parse(localStorage.getItem('nomute_cap_hist') || '[]').length;
        return out;
      }, [base, PROBE[0], PROBE[1]]);
      await page.waitForTimeout(1200);
      const tiles = await page.evaluate(() => {
        const g = document.querySelector('[id$="ResGrid"]');
        return g ? [...g.querySelectorAll('.hist-it')].filter(e => e.getClientRects().length).length : -1;
      });
      chk(r.after1 === 1, 'C3 편집 착지', `화면 주인 완료가 레일에 안 얹혔다(적재 ${r.after1}건 · 기대 1)${r.e1 ? ' · ' + r.e1 : ''}`);
      chk(r.after2 === 2, 'C5 연속 무유실', `두 번째 제작이 첫 번째를 덮었다(적재 ${r.after2}건 · 기대 2)${r.e2 ? ' · ' + r.e2 : ''}`);
      chk(tiles === 2, 'C5 타일', `결과 타일 ${tiles}개(기대 2) — 적재는 됐는데 화면에서 사라진 축`);
      await page.close();
    }

    // ── C4 = 진행 중 슬롯이 결과 칸에 발사 순서대로 선다 ──────────────────────
    for (const t of [{ f: 'edit.html', k: 'nm_edit_pend', name: '편집' }, { f: 'song.html', k: 'nm_song_pend', name: '음원' }]) {
      const page = await ctx.newPage();
      await page.goto(base + t.f, { waitUntil: 'domcontentloaded' });
      await page.waitForTimeout(900);
      const r = await page.evaluate((key) => {
        localStorage.removeItem('nomute_cap_hist');
        nmJobs.drop(key);
        nmJobs.add(key, { id: 'J-first', t0: Date.now() - 40000, lbl: '먼저 건 작업' });
        nmJobs.add(key, { id: 'J-second', t0: Date.now() - 5000, lbl: '나중 건 작업' });
        const host = document.querySelector('[id$="ResJobs"]');
        const rows = host ? [...host.querySelectorAll('.job:not(.done)')] : [];
        return {
          rows: rows.length,
          order: rows.map(x => (x.querySelector('.jlab') || {}).textContent || ''),
          running: rows.every(x => /제작중/.test(x.textContent || '')),
          cnt: (document.querySelector('[id$="ResCnt"]') || {}).textContent,
          emptyHidden: !!(document.querySelector('[id$="ResEmpty"]') || {}).hidden,
        };
      }, t.k);
      chk(r.rows === 2, `C4 ${t.name}`, `진행 중 큐 행 ${r.rows}개(기대 2) — 제작 중인 작업이 결과 칸에 안 뜬다`);
      chk(r.order[0] === '나중 건 작업', `C4 ${t.name} 순서`, `큐 순서가 최신 먼저가 아니다 — 옛날 게 위로 올라왔다(${JSON.stringify(r.order)})`);   // 최신이 맨 위·옛날 게 아래(운영자 260811 "옛날거가 더 아래쪽에 배치되어야 함") — 바로 아래 완료 타일도 최신 먼저라 한 칸이 같은 방향으로 읽힌다(구 260810 판정 = 발사 순 오름차순)
      chk(r.running, `C4 ${t.name} 상태`, '진행 중 행에 「제작중」 표기가 없다');
      chk(r.emptyHidden, `C4 ${t.name} 빈안내`, '제작 중인데 「아직 제작한 게 없습니다」가 떠 있다');
      await page.close();
    }

    // ── C6·C7 = 진행 중 행 탭이 그 작업의 제작 화면을 열고, 이력 칸은 하나다 ──────
    {
      const page = await ctx.newPage();
      await page.goto(base + 'edit.html', { waitUntil: 'domcontentloaded' });
      await page.waitForTimeout(600);
      /* ⚠ 슬롯을 비우고 **다시 연다** = 재개 폴이 미리 켜 둔 제작 화면을 지운다(첫 판 실측 함정 —
         앞 축이 남긴 슬롯을 이 페이지가 재개해 화면이 이미 떠 있었고, 훅을 죽인 킬테스트에서도 「진입」이 통과했다). */
      await page.evaluate(() => { try { nmJobs.drop('nm_edit_pend'); } catch (e) {} localStorage.removeItem('nomute_cap_hist'); });
      await page.reload({ waitUntil: 'domcontentloaded' });
      await page.waitForTimeout(900);
      const r = await page.evaluate(() => {
        const pre = !!document.querySelector('#vwrap .scanline');
        nmJobs.add('nm_edit_pend', { id: 'J-old', t0: Date.now() - 111000, lbl: '편집 중' });
        nmJobs.add('nm_edit_pend', { id: 'J-new', t0: Date.now() - 14000, lbl: '편집 중' });
        const rows = [...document.querySelectorAll('[id$="ResJobs"] .job:not(.done)')];
        const out = { pre: pre, rows: rows.length, hook: typeof window.nmJobOpen === 'function', role: rows.map(x => x.getAttribute('role')).join(',') };
        if (rows[1]) rows[1].click();   // **아래 행 = 옛날 작업** = 지금 화면 주인이 아닌 쪽(= 화면 주인 전환이 진짜로 일어나는지 재는 자리)
        return out;
      });
      await page.waitForTimeout(700);
      const st = await page.evaluate(() => ({
        stage: !!document.querySelector('#vwrap .scanline'),
        shown: !document.getElementById('vwrap').hidden,
        elapsed: (document.querySelector('#vwrap .wcorner') || {}).textContent || '',
        heads: [...document.querySelectorAll('button')].map(b => (b.textContent || '').replace(/\s+/g, ' ').trim()).filter(t => /작업 내역|이전 제작/.test(t)),
      }));
      chk(r.hook, 'C6 훅', '문서가 window.nmJobOpen을 안 준다 = 진행 중 행이 눌릴 곳이 없다');
      chk(r.role === 'button,button', 'C6 어포던스', `진행 중 행이 눌리는 모양이 아니다(role=${r.role})`);
      chk(!r.pre, 'C6 기저', '측정 시작부터 제작 화면이 떠 있다 = 이 축이 「눌러서 열렸다」를 못 가른다(가짜 통과 방지)');
      chk(st.stage && st.shown, 'C6 진입', '진행 중 행을 눌렀는데 그 작업의 제작 화면(대기 스테이지)이 안 뜬다');
      chk(/1분 5\d초 경과/.test(st.elapsed), 'C6 그 작업', `제작 화면이 **누른 그 작업**의 경과를 안 보여준다(코너 "${st.elapsed}" · 기대 = 1분 5x초 = 눌린 옛날 작업)`);
      chk(st.heads.length === 1 && /이전 제작/.test(st.heads[0]), 'C7 이력 칸', `이력 머리가 ${st.heads.length}개 — 같은 뜻의 칸이 갈렸다(${JSON.stringify(st.heads)})`);
      await page.close();
    }
    await ctx.close();
  } catch (e) {
    fails.push('ABORT | ' + String(e && e.message || e).slice(0, 200));
  } finally {
    if (browser) { try { await browser.close(); } catch (_) {} }
    try { srv.kill(); } catch (_) {}
  }

  console.log('── smoke_caprail — 영상 결과·이전 제작 레일(폰 430 · 발사 0)');
  if (!fails.length) {
    console.log(`✅ smoke_caprail PASS — ${okv.length}축 통과(영상 타일 생존 · 이전 제작 보존 · 완료 착지 · 진행 중 큐 · 연속 무유실)`);
    process.exit(0);
  }
  console.log(`❌ smoke_caprail FAIL ${fails.length}건`);
  for (const f of fails) console.log('   · ' + f);
  process.exit(1);
})();
