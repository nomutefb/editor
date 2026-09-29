// 산출 라이브 서빙(functions/_r2live.js) 구간 요청 — 아이폰 사파리는 영상을 206 구간 응답으로만 재생한다(운영자 260929 «B 진짜 투명 재생기»).
// 계약 = Range 있음 → 206 + content-range · Range 없음 → 종전 그대로 200 전량(R2 에 구간 옵션 안 넘김) · R2 이상 = 정적 폴백.
import test from 'node:test';
import assert from 'node:assert/strict';
import { r2live } from '../functions/_r2live.js';

const SIZE = 1000;
function ctx(range, { throws = false, got = [] } = {}) {
  const headers = new Headers(range ? { range } : {});
  return {
    request: new Request('https://x/ly_out/260929999901-a1b2c3/preview_stacked.mp4?v=1', { headers }),
    params: { path: ['260929999901-a1b2c3', 'preview_stacked.mp4'] },
    env: {
      ASSETS: { fetch: async () => new Response('static', { status: 200, headers: { 'x-from': 'assets' } }) },
      R2: {
        get: async (key, opt) => {
          got.push({ key, opt });
          if (throws) throw new Error('InvalidRange');
          const h = opt && opt.range;
          let range;
          if (h) {   // Workers R2 가 Range 헤더를 풀어 주는 모양 모사(offset/length · suffix)
            const m = /bytes=(\d*)-(\d*)/.exec(h.get('range'));
            if (m[1] === '') range = { suffix: +m[2] };
            else range = m[2] === '' ? { offset: +m[1] } : { offset: +m[1], length: +m[2] - +m[1] + 1 };
          }
          return { size: SIZE, range, body: 'x' };
        },
      },
    },
  };
}

test('Range 없음 = 200 전량 · R2 에 구간 옵션 미전달(종전 그대로)', async () => {
  const got = [];
  const r = await r2live('ly_out', ctx('', { got }));
  assert.equal(r.status, 200);   // seal-ok: node:assert 기본 단언
  assert.equal(got[0].key, 'ly_out/260929999901-a1b2c3/preview_stacked.mp4');   // seal-ok: node:assert 기본 단언
  assert.equal(got[0].opt, undefined);   // seal-ok: node:assert 기본 단언
  assert.equal(r.headers.get('content-type'), 'video/mp4');   // seal-ok: node:assert 기본 단언
  assert.equal(r.headers.get('content-range'), null);   // seal-ok: node:assert 기본 단언
});

test('아이폰 첫 탐색 bytes=0-1 = 206 · 0-1/전체', async () => {
  const r = await r2live('ly_out', ctx('bytes=0-1'));
  assert.equal(r.status, 206);   // seal-ok: node:assert 기본 단언
  assert.equal(r.headers.get('content-range'), 'bytes 0-1/1000');   // seal-ok: node:assert 기본 단언
  assert.equal(r.headers.get('content-length'), '2');   // seal-ok: node:assert 기본 단언
  assert.equal(r.headers.get('accept-ranges'), 'bytes');   // seal-ok: node:assert 기본 단언
});

test('열린 구간 bytes=500- = 끝까지', async () => {
  const r = await r2live('ly_out', ctx('bytes=500-'));
  assert.equal(r.status, 206);   // seal-ok: node:assert 기본 단언
  assert.equal(r.headers.get('content-range'), 'bytes 500-999/1000');   // seal-ok: node:assert 기본 단언
});

test('꼬리 구간 bytes=-100 = 마지막 100바이트', async () => {
  const r = await r2live('ly_out', ctx('bytes=-100'));
  assert.equal(r.status, 206);   // seal-ok: node:assert 기본 단언
  assert.equal(r.headers.get('content-range'), 'bytes 900-999/1000');   // seal-ok: node:assert 기본 단언
});

test('R2 가 구간을 거절(범위 밖) = 정적 폴백(악화 0)', async () => {
  const r = await r2live('ly_out', ctx('bytes=5000-6000', { throws: true }));
  assert.equal(r.headers.get('x-from'), 'assets');   // seal-ok: node:assert 기본 단언
});

test('경로 탈출 = R2 조회 없이 정적', async () => {
  const got = [];
  const c = ctx('bytes=0-1', { got });
  c.params = { path: ['..', 'secret'] };
  const r = await r2live('ly_out', c);
  assert.equal(r.headers.get('x-from'), 'assets');   // seal-ok: node:assert 기본 단언
  assert.equal(got.length, 0);   // seal-ok: node:assert 기본 단언
});
