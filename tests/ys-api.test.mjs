// 유튜브 숏폼 발사 API(functions/api/ys.js) — 주소 화이트리스트·옵션 자르기(네트워크 0).
import test from 'node:test';
import assert from 'node:assert/strict';
import { YT_RE, OPTS, cleanOpts, onRequestPost } from '../functions/api/ys.js';

test('유튜브 영상 주소만 통과', () => {
  for (const u of ['https://youtu.be/cACzvgJ3z3E?si=gwP0dOV7W2M6Orqg', 'https://www.youtube.com/watch?v=cACzvgJ3z3E',
    'https://m.youtube.com/watch?feature=share&v=cACzvgJ3z3E', 'https://www.youtube.com/shorts/cACzvgJ3z3E']) assert.ok(YT_RE.test(u), u);
  for (const u of ['http://youtu.be/cACzvgJ3z3E', 'https://www.youtube.com/@channel', 'https://evil.com/watch?v=cACzvgJ3z3E',
    'https://youtu.be/short', 'https://www.youtube.com/playlist?list=PL123']) assert.ok(!YT_RE.test(u), u);
});

test('옵션 = 화이트리스트 밖이면 첫 값(기본)', () => {
  assert.deepEqual(cleanOpts({ opts: { voice: 'edge', stt: 'subs', img: 'grok', len: '90', font: 'barun', ratio: '16:9', subbg: 'off', subop: '40', el_voice: 'AbCdEfGhIjKlMnOpQrSt' } }),
    { voice: 'edge', stt: 'subs', img: 'grok', len: '90', font: 'barun', ratio: '16:9', subbg: 'off', subop: '40', el_voice: 'AbCdEfGhIjKlMnOpQrSt' });
  // 기본 = 60초·고급·정밀·맥 그림·9:16·자막 배경 켬 100%(운영자 260928) · 옛 최상위 모양 하위호환 · 범위 밖 불투명도는 자름
  assert.deepEqual(cleanOpts({ voice: 'x', img: '../', len: 30, font: 'jua', subop: 250, el_voice: 'bad id' }),
    { voice: 'eleven', stt: 'scribe', img: 'codex', len: '60', font: 'pretendard', ratio: '9:16', subbg: 'on', subop: '100', el_voice: '' });
  assert.deepEqual(OPTS.font, ['pretendard', 'gothic', 'barun']);
  assert.deepEqual(OPTS.img, ['codex', 'motion', 'depth', 'grok']);   // 장면 화면 4방식(운영자 260928)
  assert.equal(cleanOpts({ opts: { img: 'none' } }).img, 'motion');   // 옛 글자 화면 = 모션 그래픽 승계   // seal-ok: node:assert 기본 단언 — shell-build 테스트는 문자열 비교 전용이라 대상 밖
});

test('잘못된 주소 = 400 + 한국어 사유(발사 전 차단)', async () => {
  const req = new Request('https://x/api/ys', { method: 'POST', body: JSON.stringify({ url: 'https://evil.com/?v=cACzvgJ3z3E' }) });
  const r = await onRequestPost({ request: req, env: { GH_TOKEN: 't' } });
  assert.equal(r.status, 400);   // seal-ok: node:assert 기본 단언 — shell-build 테스트는 문자열 비교 전용이라 대상 밖
  const j = await r.json();
  assert.equal(j.ok, false);   // seal-ok: node:assert 기본 단언 — shell-build 테스트는 문자열 비교 전용이라 대상 밖
  assert.match(j.error, /유튜브 영상 주소/);
});
