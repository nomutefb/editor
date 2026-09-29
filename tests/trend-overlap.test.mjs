import {test} from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFileSync} from 'node:fs';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';

// 실검 키워드 겹침(운영자 260929 «일부 겹쳐도 · 장문형도 키워드의 의미를 내포 · 가점에도 반영») — 뷰어 trIn·snsBuzz 원문 실행 ↔
// 파이썬 사본(scraper/live_signal.hit · .github/scripts/trend_watch.kw_hit) 동작 패리티(사본 0 = 뷰어 원문 추출).
const ROOT = fileURLToPath(new URL('..', import.meta.url));
const html = readFileSync(new URL('../viewer/index.html', import.meta.url), 'utf8');
const block = html.match(/^const trNorm = [\s\S]*?^const snsBuzz = c => \{[\s\S]*?^\};$/m);
assert.ok(block, 'trNorm~snsBuzz 블록 추출 실패');
const ctx = {TRENDS: null};
vm.createContext(ctx);
vm.runInContext(block[0] + '\nglobalThis.api = {trIn, trOverlap, snsBuzz, reset: () => { _buzzKw = null; }};', ctx);
const V = ctx.api;

const CASES = [
  ['닛몰캐쉬', '닛몰캐쉬 데이트폭력'], ['암살자(들)', '암살자들 비판 릴레이'], ['닛몰 캐쉬', '닛몰캐쉬 폭로'],
  ['로제', '새 프로젝트 공개'], ['로제', '로제타석'], ['리센느', '리센느가 컴백'], ['현금', '현금영수증'], ['gpt', '오픈AI GPT 발표'],
];

test('trIn = 한쪽 검색어가 다른 쪽 안에 든다(4자↑ 붙인 본문 · 2~3자 낱말·조사 꼬리) · 파이썬 사본 2곳과 같은 판정', () => {
  const js = CASES.map(([k, t]) => V.trIn(k, t));
  assert.deepEqual(js, [true, true, true, false, false, true, false, true]);
  const r = spawnSync('python3', ['-c', 'import sys, json; sys.path.insert(0, "scraper"); sys.path.insert(0, ".github/scripts"); import live_signal as L, trend_watch as W; d = json.load(sys.stdin); print(json.dumps([[L.hit(k, t) for k, t in d], [W.kw_hit(k, t) for k, t in d]]))'],
    {cwd: ROOT, input: JSON.stringify(CASES), encoding: 'utf8'});
  assert.equal(r.status, 0, r.stderr);   // seal-ok: node:assert 기본 단언
  const [ls, tw] = JSON.parse(r.stdout);
  assert.deepEqual(ls, js);
  assert.deepEqual(tw, js);
  assert.equal(V.trOverlap('닛몰캐쉬 데이트폭력', '닛몰캐쉬'), true);   // 양방향
});

test('대세 가점 = 실검 교차 겹침의 핵심 키워드도(장문형 검색어의 화제) · 낡은 나무위키는 불참', () => {
  const T = fresh => ({gtrends: [{query: '닛몰캐쉬 데이트폭력'}], signal: [{query: '암살자들 비판 릴레이'}], xtrends: [],
    namu: [{query: '닛몰캐쉬'}, {query: '암살자(들)'}], namu_updated: new Date(Date.now() - (fresh ? 0 : 5 * 3600e3)).toISOString()});
  ctx.TRENDS = T(true); V.reset();
  assert.equal(V.snsBuzz({title: '크리에이터 닛몰캐쉬, 폭언·폭행에 비하 논란까지'}), true);
  assert.equal(V.snsBuzz({title: '암살자들 흥행 돌풍'}), true);
  assert.equal(V.snsBuzz({title: '새 프로젝트 공개'}), false);
  ctx.TRENDS = T(false); V.reset();
  assert.equal(V.snsBuzz({title: '크리에이터 닛몰캐쉬, 폭언·폭행에 비하 논란까지'}), false);   // 나무위키 낡음 = 핵심 키워드 없음 → 장문 구절 통째 적중만
  assert.equal(V.snsBuzz({title: '닛몰캐쉬 데이트폭력 인정'}), true);
});
