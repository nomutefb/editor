import {test} from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFileSync} from 'node:fs';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';

// 실효 cross(연예 부착 풀 px · 260929) — 뷰어 누적 진입·병합·랭킹 ↔ 파이썬 사본(daily_health._cum_enter·screen_merge) 동작 패리티.
const ROOT = fileURLToPath(new URL('..', import.meta.url));
const html = readFileSync(new URL('../viewer/index.html', import.meta.url), 'utf8');
const decl = name => {
  const m = html.match(new RegExp('^const ' + name + ' = .*$', 'm'));
  assert.ok(m, name + ' 선언 추출 실패');
  return m[0];
};
const fnSrc = name => {
  const i = html.indexOf('function ' + name + '(');
  assert.ok(i >= 0, name);
  return html.slice(i, html.indexOf('\n}\n', i) + 3);
};
const ctx = {fpScore: c => c._fp || 0, fbJunk: () => false, Math, Date, Set, String};
vm.createContext(ctx);
vm.runInContext([
  'CROSS_MIN', 'POOL_W', 'effCross', 'rankCross', 'FOLLOW_CROSS_MIN', 'FP_STRONG', 'isBreaking', 'followEnters',
  'MERGE_DAMP_RATIO', 'CROSS_POW', 'crossConvex', 'candId', '_normU',
].map(decl).join('\n') + '\n' + fnSrc('mergeDecorate') +
  '\nglobalThis.api = {effCross, rankCross, crossConvex, mergeDecorate, cum: c => effCross(c) >= CROSS_MIN || isBreaking(c) || followEnters(c)};', ctx);
const V = ctx.api;

const CASES = [
  {cross: 7}, {cross: 7, px: 1}, {cross: 7, px: 2}, {cross: 8}, {cross: 6, px: 4},
  {cross: 3, px: 2, report_count: 6}, {cross: 3, px: 1, report_count: 6}, {cross: 4, report_count: 5},
  {cross: 2, breaking: true, grade: 2}, {cross: 2, breaking: true, grade: 1}, {cross: 1, px: 5, report_count: 1},
];
const py = (code, input) => {
  const r = spawnSync('python3', ['-c', 'import sys, json; sys.path.insert(0, "scraper"); import daily_health as D; d = json.load(sys.stdin); ' + code],
    {cwd: ROOT, input: JSON.stringify(input), encoding: 'utf8'});
  assert.equal(r.status, 0, r.stderr);   // seal-ok: node:assert 기본 단언 — shell-build 테스트는 문자열 비교 전용이라 대상 밖
  return JSON.parse(r.stdout);
};

test('누적 진입 = 실효 cross(cross + 0.5×px) — 렌더 필터가 effCross 를 쓰고 파이썬 _cum_enter 와 같은 판정', () => {
  assert.ok(html.includes('(effCross(c) >= CROSS_MIN || isBreaking(c) || followEnters(c) || failRequeued(c) || pickState(c))'), '누적 칼럼 필터 = effCross');
  const js = CASES.map(V.cum);
  assert.deepEqual(js, py('print(json.dumps([D._cum_enter(x) for x in d]))', CASES));
  assert.deepEqual(js, [false, false, true, true, true, true, false, false, true, false, false]);
});

test('병합 카드 px = 형제 최댓값 = daily_health.screen_merge 와 같은 값', () => {
  const a = {url: 'A', cross: 5, px: 1, group_id: 'A'}, b = {url: 'B', cross: 2, px: 2, group_id: 'A'};
  const m = V.mergeDecorate(a, [b]);
  const p = py('print(json.dumps([x for x in D.screen_merge(d) if x["url"] == "A"][0]))', [a, b]);
  assert.equal(m.px, 2);   // seal-ok: node:assert 기본 단언 — shell-build 테스트는 문자열 비교 전용이라 대상 밖
  assert.equal(m.px, p.px);   // seal-ok: node:assert 기본 단언 — shell-build 테스트는 문자열 비교 전용이라 대상 밖
  assert.equal(m.cross, p.cross);   // seal-ok: node:assert 기본 단언 — shell-build 테스트는 문자열 비교 전용이라 대상 밖
  assert.equal(V.cum(m), py('print(json.dumps(D._cum_enter(d)))', p));   // seal-ok: node:assert 기본 단언 — shell-build 테스트는 문자열 비교 전용이라 대상 밖
});

test('병합 카드 lv = 형제 중 가장 센 단계 = daily_health.screen_merge 와 같은 값 · 병합 긴급 판정도 같다', () => {   // 평의회260929-2 #4 — 한쪽만 바뀌면 🚨·계기판이 조용히 갈리던 공백
  const a = {url: 'A', cross: 3, group_id: 'A', breaking: true, grade: 1, lv: {k: 'x', t: 2}}, b = {url: 'B', cross: 2, group_id: 'A', breaking: true, lv: {k: 'x', t: 3, gn: 5}};
  const m = V.mergeDecorate(a, [b]);
  const p = py('print(json.dumps([x for x in D.screen_merge(d) if x["url"] == "A"][0]))', [a, b]);
  assert.deepEqual(m.lv, {k: 'x', t: 3, gn: 5});
  assert.deepEqual(m.lv, p.lv);
  assert.equal(V.cum(m), true);   // seal-ok: node:assert 기본 단언 — shell-build 테스트는 문자열 비교 전용이라 대상 밖
  assert.equal(V.cum(m), py('print(json.dumps(D._cum_enter(d)))', p));   // seal-ok: node:assert 기본 단언 — shell-build 테스트는 문자열 비교 전용이라 대상 밖
  const b2 = {...b, breaking: false}, m2 = V.mergeDecorate(a, [b2]);   // 검증 V3 — 긴급 아닌 형제의 [강]은 병합 카드에 안 옮긴다
  const p2 = py('print(json.dumps([x for x in D.screen_merge(d) if x["url"] == "A"][0]))', [a, b2]);
  assert.deepEqual(m2.lv, {k: 'x', t: 2});
  assert.deepEqual(m2.lv, p2.lv);
});

test('랭킹 = 기존(댐핑) cross · px 무관(연예 가중 0 · 진입에만 쓴다)', () => {
  assert.equal(V.rankCross({cross: 7, px: 4}), 7);   // seal-ok: node:assert 기본 단언 — shell-build 테스트는 문자열 비교 전용이라 대상 밖
  assert.equal(V.rankCross({cross: 20, _rankCross: 16, px: 2}), 16);   // seal-ok: node:assert 기본 단언 — shell-build 테스트는 문자열 비교 전용이라 대상 밖
  assert.equal(V.crossConvex({cross: 7, px: 2}), V.crossConvex({cross: 7}));   // seal-ok: node:assert 기본 단언 — shell-build 테스트는 문자열 비교 전용이라 대상 밖
});

