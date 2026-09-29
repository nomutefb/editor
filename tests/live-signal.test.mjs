import {test} from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFileSync} from 'node:fs';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';

// 확산 [강](lv.t≥3 · scraper/live_signal.py · 260929) — 뷰어 isBreaking·feedBrk ↔ 파이썬 사본(daily_health._brk_on · to_candidates._urgent ·
// push_send.is_breaking[미채점 보류만 추가]) 동작 패리티. 뷰어 원문을 그대로 추출해 실행한다(사본 0).
const ROOT = fileURLToPath(new URL('..', import.meta.url));
const html = readFileSync(new URL('../viewer/index.html', import.meta.url), 'utf8');
const decl = name => {
  const m = html.match(new RegExp('^const ' + name + ' = .*$', 'm'));
  assert.ok(m, name + ' 선언 추출 실패');
  return m[0];
};
const ctx = {};
vm.createContext(ctx);
vm.runInContext([decl('isBreaking'), decl('feedBrk')].join('\n') + '\nglobalThis.api = {isBreaking, feedBrk};', ctx);
const V = ctx.api;

const CASES = [
  {breaking: true, grade: 2}, {breaking: true, grade: 1}, {breaking: true, grade: null}, {breaking: false, grade: 3},
  {breaking: true, grade: 1, lv: {t: 3}}, {breaking: true, grade: 1, lv: {t: 2}}, {breaking: true, grade: 0, lv: {t: 3}},
  {breaking: true, grade: null, lv: {t: 3}}, {breaking: false, grade: 1, lv: {t: 3}}, {breaking: true, grade: 3, lv: {t: 1}},
];
const py = code => {
  const r = spawnSync('python3', ['-c', 'import sys, json; sys.path.insert(0, "scraper"); sys.path.insert(0, ".github/scripts"); d = json.load(sys.stdin); ' + code],
    {cwd: ROOT, input: JSON.stringify(CASES), encoding: 'utf8'});
  assert.equal(r.status, 0, r.stderr);   // seal-ok: node:assert 기본 단언 — shell-build 테스트는 문자열 비교 전용이라 대상 밖
  return JSON.parse(r.stdout);
};

test('isBreaking = 확산 [강]이면 경중 무관 긴급 · 파이썬 사본 3곳과 같은 판정', () => {
  const js = CASES.map(V.isBreaking);
  assert.deepEqual(js, [true, false, true, false, true, false, true, true, false, true]);
  assert.deepEqual(js, py('import daily_health as D; print(json.dumps([D._brk_on(x) for x in d]))'));
  assert.deepEqual(js, py('import to_candidates as T; print(json.dumps([T._urgent(x) for x in d]))'));
  const push = py('import importlib.util as u; s = u.spec_from_file_location("ps", ".github/scripts/push_send.py"); m = u.module_from_spec(s); s.loader.exec_module(m); print(json.dumps([m.is_breaking(x) for x in d]))');
  assert.deepEqual(push, CASES.map((c, i) => js[i] && c.grade != null));   // 푸시 = 같은 술어 + 미채점 보류(비가역 보수)
});

test('피드 feedBrk = lvt 패스스루로 같은 술어', () => {
  assert.equal(V.feedBrk({breaking: true, grade: 1, lvt: 3}), true);   // seal-ok: node:assert 기본 단언 — shell-build 테스트는 문자열 비교 전용이라 대상 밖
  assert.equal(V.feedBrk({breaking: true, grade: 1}), false);   // seal-ok: node:assert 기본 단언 — shell-build 테스트는 문자열 비교 전용이라 대상 밖
  assert.equal(V.feedBrk({breaking: true, grade: 0, lvt: 3}), true);   // seal-ok: node:assert 기본 단언 — shell-build 테스트는 문자열 비교 전용이라 대상 밖
  const bv = readFileSync(new URL('../build-viewer.mjs', import.meta.url), 'utf8');
  assert.ok(bv.includes('(c.grade == null || c.grade >= 2 || lvt >= 3)'), 'build-viewer BRK = 같은 술어');
  assert.ok(bv.includes('lvt: LVT.get('), 'build-viewer lvt 패스스루');
});
