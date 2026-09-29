// 산출 라이브 서빙(functions/_r2live.js) 구간 요청 — 아이폰 사파리는 영상을 206 구간 응답으로만 재생한다(운영자 260929 «B 진짜 투명 재생기»).
// 계약 = 단일 구간 → 206 + content-range · Range 없음·못 푸는 헤더 → 종전 그대로 200 전량 · 범위 밖 → 416 · R2 이상 = 정적 폴백.
// R2 가짜 = workerd 실측 모양(평의회 260929): Range 를 안 줘도 o.range 는 {offset:0,length:size} 로 늘 채워지고, suffix 도 {offset,length} 로 풀려 온다.
import test from 'node:test';
import assert from 'node:assert/strict';
import { r2live, parseRange } from '../functions/_r2live.js';

function ctx(range, { size = 1000, got = [], missing = false } = {}) {
  const headers = new Headers(range ? { range } : {});
  return {
    request: new Request('https://x/ly_out/260929999901-a1b2c3/preview_stacked.mp4?v=1', { headers }),
    params: { path: ['260929999901-a1b2c3', 'preview_stacked.mp4'] },
    env: {
      ASSETS: { fetch: async () => new Response('static', { status: 200, headers: { 'x-from': 'assets' } }) },
      R2: {
        head: async () => (missing ? null : { size }),
        get: async (key, opt) => {
          got.push({ key, opt });
          if (missing) return null;
          const r = opt && opt.range;
          let range = { offset: 0, length: size };
          if (r) {
            const off = 'suffix' in r ? Math.max(0, size - r.suffix) : r.offset;
            if (off >= size && size > 0) throw new Error('InvalidRange');
            const len = 'suffix' in r ? size - off : ('length' in r ? Math.min(r.length, size - off) : size - off);
            range = { offset: off, length: len };
          }
          return { size, range, body: 'x' };
        },
      },
    },
  };
}

test('구간 파서 = 단일 구간만(여러 구간·형식 이상 = null)', () => {
  assert.deepEqual(parseRange('bytes=0-1'), { offset: 0, length: 2 });
  assert.deepEqual(parseRange('bytes=500-'), { offset: 500 });
  assert.deepEqual(parseRange('bytes=-100'), { suffix: 100 });
  for (const h of ['bytes=0-1,5-6', 'bytes=abc', 'items=0-1', 'bytes=5-2', 'bytes=-0', '']) assert.equal(parseRange(h), null, h);   // seal-ok: node:assert 기본 단언
});

test('Range 없음 = 200 전량 · R2 가 range 를 채워 줘도 206 으로 바꾸지 않는다(JSON 폴링 무접촉)', async () => {
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

test('열린 구간 bytes=500- = 끝까지 · 넘치는 끝 = 잘라서', async () => {
  const a = await r2live('ly_out', ctx('bytes=500-'));
  assert.equal(a.headers.get('content-range'), 'bytes 500-999/1000');   // seal-ok: node:assert 기본 단언
  const b = await r2live('ly_out', ctx('bytes=900-99999'));
  assert.equal(b.headers.get('content-range'), 'bytes 900-999/1000');   // seal-ok: node:assert 기본 단언
});

test('꼬리 구간 bytes=-100 = 마지막 100바이트(R2 가 offset/length 로 풀어 줘도)', async () => {
  const r = await r2live('ly_out', ctx('bytes=-100'));
  assert.equal(r.status, 206);   // seal-ok: node:assert 기본 단언
  assert.equal(r.headers.get('content-range'), 'bytes 900-999/1000');   // seal-ok: node:assert 기본 단언
});

test('여러 구간·형식 이상 = Range 무시하고 200 전량(R2 에 구간 안 넘김)', async () => {
  for (const h of ['bytes=0-1,5-6', 'bytes=abc', 'bytes=5-2']) {
    const got = [];
    const r = await r2live('ly_out', ctx(h, { got }));
    assert.equal(r.status, 200, h);   // seal-ok: node:assert 기본 단언
    assert.equal(got[0].opt, undefined, h);   // seal-ok: node:assert 기본 단언
  }
});

test('범위 밖 = 416 · bytes */전체(정적 SPA 폴백으로 새지 않는다)', async () => {
  const r = await r2live('ly_out', ctx('bytes=5000-6000'));
  assert.equal(r.status, 416);   // seal-ok: node:assert 기본 단언
  assert.equal(r.headers.get('content-range'), 'bytes */1000');   // seal-ok: node:assert 기본 단언
});

test('0바이트 객체 + Range = 200(0--1 같은 깨진 헤더 금지)', async () => {
  const r = await r2live('ly_out', ctx('bytes=0-1', { size: 0 }));
  assert.equal(r.status, 200);   // seal-ok: node:assert 기본 단언
  assert.equal(r.headers.get('content-range'), null);   // seal-ok: node:assert 기본 단언
});

test('R2 미스 = 정적 폴백(악화 0)', async () => {
  const r = await r2live('ly_out', ctx('bytes=0-1', { missing: true }));
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
