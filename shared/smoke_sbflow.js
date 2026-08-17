// smoke_sbflow.js — 콘티 화면 **발사 경로 실주행**(누르지 않고 누른 것과 같은 자리를 잰다).
//
// ⚠ 왜 신설했나(260814) = 이 레포 스모크 27종이 전부 「화면이 어떻게 그려졌나」를 잰다.
//   「채우고 눌렀을 때 서버로 **무엇이 나가나**」는 축 자체가 없었고, 그래서 웹앱 경로는
//   운영자가 직접 눌러 보기 전까지 아무도 확인한 적이 없었다.
// ⚠ 첫 실행이 곧바로 실사고를 잡았다 — 기사 고르기 창 마크업이 스크립트보다 **뒤**에 있어
//   손잡이를 못 잡았고, **버튼을 눌러도 아무 일도 안 일어났다**(콘솔 에러 0 = 무증상).
//   화면 렌더 검사로는 절대 안 걸린다(요소는 멀쩡히 있다 · 안 열릴 뿐).
// ⚠ 액션이 꺼져도 도는 검사다(260814 계정 정지 실측) — 서버는 가로채고 발사는 0이라
//   깃허브·창구·과금에 한 글자도 안 닿는다. 기계가 멈춘 동안 유일하게 남는 확인 수단.
//
// 실행 = node shared/smoke_sbflow.js (smoke_all 자동발견 동행)
const { execSync, spawn } = require('child_process');
const fs = require('fs'), path = require('path'), os = require('os');
function lp() { try { return require('playwright-core'); } catch (_) {} return require(path.join(os.tmpdir(), 'nomute-smoke-deps', 'node_modules', 'playwright-core')); }
const { chromium } = lp();
function chromiumPath() {
  const c = [process.env.CHROMIUM_PATH, '/opt/pw-browsers/chromium'];
  try { c.push(execSync('which chromium chromium-browser google-chrome 2>/dev/null | head -1').toString().trim()); } catch (_) {}
  for (const x of c) if (x && fs.existsSync(x)) return x;
  throw new Error('크로미엄 없음');
}
const F1 = '260814-0900-probe-aaaaaaaaaa.md', F2 = '260813-0800-probe-bbbbbbbbbb.md';
const FREE = '이것은 자유요약 본문이다. 폐버스 논란은 청년 주거난의 해법으로 제시됐다가 하루를 못 넘기고 철회됐다.';
const ARTICLES = { articles: [
  { file: F1, title: '새 기사 제목 — 가장 최근에 요약된 것', has_body: true, rev: 1 },
  { file: F2, title: '옛 기사 제목 — 먼저 요약된 것', has_body: true, rev: 1 },
] };
const DETAIL = (t) => ({ body: '# ' + t + '\n\n## 🧷 한줄 요약\n한 줄짜리 요약이다.\n\n## 📦 콘텐츠 초안\n\n### [자유요약 — 약 900자]\n```text\n' + FREE + '\n```\n📊 편향: 6/10\n\n### [IG — 약 740/800자]\n```text\n인스타 요약은 가져오면 안 된다.\n```\n' });

let bad = 0;
const ok = (c, msg, got) => { console.log((c ? '✅ ' : '❌ ') + msg + (got === undefined ? '' : ' | ' + got)); if (!c) bad++; };

(async () => {
  const srv = spawn('python3', ['-m', 'http.server', '8896', '-d', 'viewer'], { stdio: 'ignore' });
  await new Promise(r => setTimeout(r, 900));
  const b = await chromium.launch({ executablePath: chromiumPath() });
  const pg = await b.newPage({ viewport: { width: 430, height: 900 } });
  const errs = []; pg.on('pageerror', e => errs.push(e.message));
  let sent = null;

  await pg.route('**/articles.json*', r => r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(ARTICLES) }));
  await pg.route('**/detail/*.json*', r => {
    const f = decodeURIComponent(r.request().url()).includes(F1) ? '새 기사' : '옛 기사';
    r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(DETAIL(f)) });
  });
  await pg.route('**/api/sb', r => { sent = JSON.parse(r.request().postData() || '{}'); r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ ok: true, id: '260814-test', out: 'sb_out/260814-test/board.md' }) }); });
  await pg.route('**/sb_out/**', r => r.fulfill({ status: 404, body: '' }));

  await pg.goto('http://127.0.0.1:8896/sb.html', { waitUntil: 'domcontentloaded' });
  await pg.waitForTimeout(1400);

  // ── ① 둘 다 비면 발사가 막히는가
  const gate0 = await pg.evaluate(() => { const g = document.querySelector('#go'); return { dis: !!g.disabled, tip: g.title || '' }; });   // seal-ok: 브라우저 실렌더 문법 — 미보유 형제(favtab·thumbapi)는 브라우저를 안 띄우는 축이라 정당 부재
  ok(gate0.dis, '① 둘 다 비면 생성이 잠긴다', 'disabled=' + gate0.dis);

  // ── ② 기사 고르기 → 제목 탭 → 자유요약이 자료 참조로
  await pg.click('#sumPull');
  await pg.waitForTimeout(700);
  const rows = await pg.evaluate(() => [...document.querySelectorAll('#artList .artrow')].map(r => ({ no: r.querySelector('.qt').textContent, t: r.querySelector('.qmain').textContent })));   // seal-ok: 브라우저 실렌더 문법 — 미보유 형제(favtab·thumbapi)는 브라우저를 안 띄우는 축이라 정당 부재
  ok(rows.length === 2, '② 목록이 뜬다', JSON.stringify(rows));
  ok(rows[0] && rows[0].t.startsWith('새 기사'), '② 최신이 위', rows[0] && rows[0].t.slice(0, 12));
  ok(rows[0] && rows[0].no === '2' && rows[1] && rows[1].no === '1', '② 번호 = 요약된 차례(먼저 요약된 것이 1)', rows.map(r => r.no).join(','));
  await pg.click('#artList .artrow');
  await pg.waitForTimeout(900);
  const got = await pg.evaluate(() => ({ v: (document.querySelector('#sumTx') || {}).value || '', open: !document.querySelector('#artPop').hidden }));   // seal-ok: 브라우저 실렌더 문법 — 미보유 형제(favtab·thumbapi)는 브라우저를 안 띄우는 축이라 정당 부재
  ok(got.v.includes('이것은 자유요약 본문이다'), '② 자유요약이 자료 참조에 들어온다', got.v.slice(0, 28) + '…');
  ok(!got.v.includes('인스타 요약'), '② 인스타 요약은 안 딸려온다');
  ok(!got.v.includes('한 줄짜리 요약'), '② 한줄 요약도 안 딸려온다');
  ok(!got.v.includes('```'), '② 울타리(백틱)가 안 섞인다');
  ok(!got.v.includes('편향'), '② 편향 줄이 안 섞인다');
  ok(!got.open, '② 고르면 창이 닫힌다');

  // ── ③ 자료만 있어도 발사가 열리는가
  const gate1 = await pg.evaluate(() => !document.querySelector('#go').disabled);   // seal-ok: 브라우저 실렌더 문법 — 미보유 형제(favtab·thumbapi)는 브라우저를 안 띄우는 축이라 정당 부재
  ok(gate1, '③ 자료만 있어도 생성이 열린다');

  // ── ④ 연출 목적 + 화풍/화질 + 참조 사진 붙여 1차 전송
  // 사진 = 실제 파일 선택기 경유(운영자 260817 「콘티에 참조할 사진」) — 1×1 jpeg 실물 바이트
  const TINY_JPEG = Buffer.from('/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/wAALCAABAAEBAREA/8QAFAABAAAAAAAAAAAAAAAAAAAACf/EABQQAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQEAAD8AVN//2Q==', 'base64');
  await pg.setInputFiles('#pvFile', { name: 'probe.jpg', mimeType: 'image/jpeg', buffer: TINY_JPEG });
  await pg.waitForTimeout(700);
  await pg.evaluate(() => {   // seal-ok: 브라우저 실렌더 문법 — 미보유 형제(favtab·thumbapi)는 브라우저를 안 띄우는 축이라 정당 부재
    const t = document.querySelector('#scene'); t.value = '폐버스 제안을 우아하게 비판한다';
    t.dispatchEvent(new Event('input', { bubbles: true }));
    const sty = [...document.querySelectorAll('#sbStyle .geni-opt')].find(b => b.textContent.trim() === '실사'); if (sty) sty.click();
  });
  await pg.waitForTimeout(400);
  await pg.evaluate(() => { const s = [...document.querySelectorAll('#sbSub .geni-opt')].find(b => b.textContent.trim() === '흑백'); if (s) s.click(); });   // seal-ok: 브라우저 실렌더 문법 — 미보유 형제(favtab·thumbapi)는 브라우저를 안 띄우는 축이라 정당 부재
  await pg.waitForTimeout(400);
  await pg.click('#go');
  await pg.waitForTimeout(900);
  ok(!!sent, '④ 1차 전송이 서버로 나간다');
  if (sent) {
    const st = sent.story || '', set = sent.set || {};
    ok(st.includes('[지시]') && st.includes('우아하게 비판'), '④ 연출 목적이 지시 절로', st.slice(0, 24) + '…');
    ok(st.includes('[기사 요약 — 참고 자료]') && st.includes('자유요약 본문'), '④ 자료가 참고 자료 절로');
    ok(st.indexOf('[지시]') < st.indexOf('[기사 요약'), '④ 지시가 먼저(길이 절단에 안 잘리게)');
    ok(set['화풍'] === '실사', '④ 화풍이 실린다', set['화풍']);
    ok(set['세부 화풍'] === '흑백', '④ 세부 화풍이 실린다', set['세부 화풍']);
    ok(!!set['화질'] && !!set['비율'] && !!set['길이'], '④ 화질·비율·길이가 실린다', JSON.stringify({ q: set['화질'], r: set['비율'], l: set['길이'] }));
    ok(!sent.shootOnly && !sent.base, '④ 1차는 촬영 표식이 없다(콘티만)', 'shootOnly=' + sent.shootOnly + ' base=' + (sent.base || ''));
    ok(!!sent.shoot, '④ 촬영 칸도 같이 간다', sent.shoot);
    const ph = Array.isArray(sent.photos) ? sent.photos : [];
    ok(ph.length === 1 && String(ph[0]).startsWith('data:image/jpeg'), '④ 참조 사진이 jpeg 로 동봉된다(운영자 260817)', ph.length + '장');
  }

  // ── ⑤ 촬영 칸을 바꾸면 화질이 아래로만 내려앉는가(위로 튀면 값이 다섯 배)
  const clamp = await pg.evaluate(() => {   // seal-ok: 브라우저 실렌더 문법 — 미보유 형제(favtab·thumbapi)는 브라우저를 안 띄우는 축이라 정당 부재
    const pick = nm => { const b = [...document.querySelectorAll('#sgrid button')].find(x => x.textContent.trim() === nm); if (b) b.click(); };
    const cur = () => [...document.querySelectorAll('#axQ .geni-opt')].filter(b => b.classList.contains('on') || b.classList.contains('qro')).map(b => b.textContent.trim())[0];
    pick('2.0'); const two = [...document.querySelectorAll('#axQ .geni-opt')].map(b => b.textContent.trim());
    const hi = [...document.querySelectorAll('#axQ .geni-opt')].find(b => b.textContent.trim() === '4K'); if (hi) hi.click();
    const after4k = cur();
    pick('Grok'); const g = cur();
    pick('2.0'); const back = cur();
    return { two, after4k, g, back };
  });
  ok(clamp.two.join(',') === '720p,FHD,4K', '⑤ 2.0 화질 = 720p·FHD·4K(2K 없음)', clamp.two.join(','));
  ok(clamp.g === '720p', '⑤ 그록으로 바꾸면 720p', clamp.g);
  ok(clamp.back !== '4K', '⑤ 되돌아와도 4K로 안 튄다(값 다섯 배 방지)', clamp.back);

  // ── ⑦ 결과 구획 = • 스토리보드 / • 주요 인물(운영자 260817 「블릿으로 각각 사진을 띄워주셈」)
  //    표본 = 인물 슬롯 1(성공) + 배경 슬롯 1(null — 260817 계약상 안 굽는 슬롯 = 실패 칩 없이 조용히 생략)
  await pg.route('**/sheet.json*', r => r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ url: 'https://x.invalid/sheet.jpg', cuts: 9, engine: 'gemini' }) }));
  await pg.route('**/video.json*', r => r.fulfill({ status: 404, body: '' }));
  await pg.route('**/ref.json*', r => r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ urls: ['https://x.invalid/p1.jpg', null] }) }));
  const MD7 = '# 표본 콘티\n\n## ⚙️ 설계 요약\n의도: 표본\n\n## 🖼 레퍼런스\n① 인물(사진 1): 남자\n```text\nman\n```\n② 배경: 골목\n```text\nalley\n```\n';
  const sheet = await pg.evaluate(async md => {   // seal-ok: 브라우저 실렌더 문법 — 미보유 형제(favtab·thumbapi)는 브라우저를 안 띄우는 축이라 정당 부재
    const box = document.createElement('div'); document.body.appendChild(box);
    await window.renderOut(md, box, 'sb_out/260814-test/board.md');
    const heads = [...box.querySelectorAll('.geni-sechead .cref-lbl')].map(x => x.textContent.trim());
    const refs = [...box.querySelectorAll('.ref')];
    return { heads: heads.join(','),
             firstCap: refs[0] ? (refs[0].querySelector('.cap') || {}).textContent || '' : '',
             firstImg: refs[0] ? !!refs[0].querySelector('img[data-ix="sheet"]') : false,
             personCap: refs[1] ? (refs[1].querySelector('.cap') || {}).textContent || '' : '',
             miss: box.querySelectorAll('.refmiss').length,
             shown: (typeof SHOWN === 'string') ? SHOWN : '(없음)' };
  }, MD7).catch(e => ({ err: String(e.message).slice(0, 120) }));
  ok(!sheet.err, '⑦ 결과 렌더가 돈다', sheet.err || '');
  ok(sheet.firstImg, '⑦ 스토리보드 시트가 결과부 맨 앞에 뜬다');
  ok((sheet.firstCap || '').includes('스토리보드'), '⑦ 캡션이 스토리보드라고 말한다', sheet.firstCap);
  ok((sheet.heads || '').includes('스토리보드') && sheet.heads.includes('주요 인물'), '⑦ 블릿 구획 둘(스토리보드·주요 인물)', sheet.heads);
  ok((sheet.personCap || '').includes('인물'), '⑦ 인물 시트가 라벨 캡션으로 뜬다', sheet.personCap);
  ok(sheet.miss === 0, '⑦ 배경 null 슬롯 = 실패 칩 없이 생략(260817 계약)', 'miss=' + sheet.miss);
  ok(sheet.shown === 'sb_out/260814-test/board.md', '⑦ 결과가 뜨면 2차 표식이 선다', sheet.shown);

  // ── ⑧ 생성 버튼 이원 모드(운영자 260817 「제작 버튼은 다시 생성 버튼이 대체」)
  //    결과가 떠 있는 상태(⑦) → 생성 = 2차(촬영 표식) · 입력을 고치면 → 생성 = 1차(콘티).
  //    ⚠ ④의 폴이 아직 살아 있어 첫 탭은 재확인 경고다(계약 동작) — 두 탭으로 확정한다.
  sent = null;
  await pg.click('#go'); await pg.waitForTimeout(200); await pg.click('#go');
  await pg.waitForTimeout(900);
  ok(!!sent && sent.shootOnly === true && sent.base === 'sb_out/260814-test/board.md' && sent.story === '',
     '⑧ 결과가 떠 있으면 생성 = 2차(그 콘티로 촬영)', sent ? ('base=' + sent.base) : '전송 없음');
  sent = null;
  await pg.evaluate(() => { const t = document.querySelector('#scene'); t.value = '다른 각으로 다시'; t.dispatchEvent(new Event('input', { bubbles: true })); });   // seal-ok: 브라우저 실렌더 문법 — 미보유 형제(favtab·thumbapi)는 브라우저를 안 띄우는 축이라 정당 부재
  await pg.waitForTimeout(200);
  await pg.click('#go'); await pg.waitForTimeout(200); await pg.click('#go');
  await pg.waitForTimeout(900);
  ok(!!sent && !sent.shootOnly && (sent.story || '').includes('다른 각으로 다시'),
     '⑧ 입력을 고치면 생성 = 1차(새 콘티)', sent ? ('shootOnly=' + sent.shootOnly) : '전송 없음');

  ok(errs.length === 0, '⑥ 페이지 에러 0', errs.slice(0, 2).join(' | '));
  await b.close(); try { srv.kill(); } catch (e) {}
  console.log(bad ? '── 판정 FAIL ' + bad + '건' : '── 판정 PASS (발사 경로 전건)');
  process.exit(bad ? 1 : 0);
})();
