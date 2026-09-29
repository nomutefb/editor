// 편집 발사 추가 옵션(functions/api/edit.js cleanXtr) — 배경 빼기 통합(운영자 260929 «키잉·크로마키 하나로») 옛 설정 이관(네트워크 0).
import test from 'node:test';
import assert from 'node:assert/strict';
import { cleanXtr } from '../functions/api/edit.js';

test('구 키잉 = 배경 빼기 · 구 키잉 페더(kfe) = 부드럽게(bgfe)', () => {
  assert.deepEqual(cleanXtr({ keying: true, kfe: 5 }), { bgrm: true, bgfe: 5 });
});

test('구 크로마키 = 배경 빼기 · 색·강도 노브는 버린다(러너가 스크린 색을 잰다)', () => {
  assert.deepEqual(cleanXtr({ chroma: true, ckcolor: 'blue', cksim: 18, ckchoke: 2, ckfe: 3 }), { bgrm: true });
});

test('새 축 = bgrm·bgfe 그대로 · 범위 밖 부드럽게 = 자름', () => {
  assert.deepEqual(cleanXtr({ bgrm: true, bgfe: 99 }), { bgrm: true, bgfe: 40 });
  assert.deepEqual(cleanXtr({ bgrm: true, bgfe: 3, kfe: 9 }), { bgrm: true, bgfe: 3 });   // 둘 다 오면 새 키 우선
});

test('켠 축이 없으면 null(끈 구 키잉·크로마키 = 배경 빼기 아님)', () => {
  assert.equal(cleanXtr({ keying: false, chroma: false, kfe: 4 }), null);   // seal-ok: node:assert 기본 단언
  assert.equal(cleanXtr(null), null);   // seal-ok: node:assert 기본 단언
  assert.equal(cleanXtr([true]), null);   // seal-ok: node:assert 기본 단언
});

test('가림 축은 종전 그대로(모양·크기·이름표)', () => {
  assert.deepEqual(cleanXtr({ pinset: true, shape: 'rect', size: 130, names: { 1: '가', x: '나' }, colors: { 1: '#ff0000', 2: 'red' } }),
    { pinset: true, shape: 'rect', size: 130, names: { 1: '가' }, colors: { 1: '#ff0000' } });
});
