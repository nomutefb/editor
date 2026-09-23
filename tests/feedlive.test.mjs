import {test} from 'node:test';
import assert from 'node:assert/strict';
import {onRequestGet, liveRow} from '../functions/api/feedlive.js';

// 빌드 전 새 요약 라이브 서빙(260924 ⑥) — 정적 인덱스에 없는 새 요약만 · 빌드가 따라잡으면 자동 제외 · 토큰 없음 = 빈 목록(종전)
const md = t => `---\ntitle: "${t}"\nurl: "https://x.kr/1"\ndate: "2026-09-24"\nmedia: "JTBC"\n---\n# ${t}\n\n본문 요약`;
function env(files, gen = '2026-09-24T03:00:00Z') {
  return {GH_TOKEN: 't', ASSETS: {fetch: async () => ({json: async () => ({generated: gen, articles: files.map(file => ({file}))})})}};
}
const req = {url: 'https://edit.nomute.kr/api/feedlive'};
function gh(commitFiles, raws) {
  const calls = [];
  globalThis.fetch = async (u) => {
    calls.push(u);
    if (u.includes('/commits?')) return {ok: true, json: async () => Object.keys(commitFiles).map(sha => ({sha}))};
    const m = u.match(/\/commits\/(\w+)$/);
    if (m) return {ok: true, json: async () => ({files: commitFiles[m[1]]})};
    const f = decodeURIComponent(u.split('/contents/queue/')[1].split('?')[0]);
    return raws[f] ? {ok: true, text: async () => raws[f]} : {ok: false};
  };
  return calls;
}

test('정적 인덱스에 없는 새 요약만 행으로 · 이미 빌드된 파일·삭제·queue 밖 = 제외', async () => {
  gh({a1: [{filename: 'queue/260924-0310-new.md', status: 'added'}, {filename: 'queue/260924-0200-old.md', status: 'modified'},
          {filename: 'viewer/candidates.json', status: 'modified'}, {filename: 'queue/260924-0100-gone.md', status: 'removed'}]},
     {'260924-0310-new.md': md('🔥 새 요약 제목')});
  const r = await onRequestGet({env: env(['260924-0200-old.md']), request: req});
  const d = await r.json();
  assert.equal(d.rows.length, 1);
  assert.equal(d.rows[0].file, '260924-0310-new.md');
  assert.equal(d.rows[0].title, '새 요약 제목');   // 선두 이모지 = 빌드와 같은 해석기(shared/article_parse.mjs)
  assert.equal(d.rows[0]._live, 1);
  assert.equal(d.rows[0].has_body, true);
});

test('토큰 없음 = 빈 목록(종전 동작)', async () => {
  const d = await (await onRequestGet({env: {ASSETS: env([]).ASSETS}, request: req})).json();
  assert.deepEqual(d.rows, []);
});

test('빌드가 따라잡으면 행 0', async () => {
  gh({a1: [{filename: 'queue/260924-0310-new.md', status: 'added'}]}, {'260924-0310-new.md': md('x')});
  const d = await (await onRequestGet({env: env(['260924-0310-new.md']), request: req})).json();
  assert.equal(d.rows.length, 0);
});

test('행 필드 = 빌드 행과 같은 이름(뷰어 렌더 계약)', () => {
  const row = liveRow('f.md', md('제목'));
  for (const k of ['file', 'title', 'url', 'date', 'media', 'category', 'breaking', 'cross', 'grade', 'issue', 'rev', 'body']) assert.ok(k in row, k);
});
