import {test} from 'node:test';
import assert from 'node:assert/strict';
import {mergeItems} from '../functions/_settings-merge.js';
import {onRequestGet as jobs} from '../functions/api/jobs.js';
import {onRequestPost as save, onRequestGet as read} from '../functions/api/settings.js';

const memo = (id, text) => ({id, ts: 1, text});
test('independent stale additions survive; retry is idempotent', () => {
  const base = [memo('a', 'original')];
  const phone = [...base, memo('phone', 'phone')];
  const pc = [...base, memo('pc', 'pc')];
  const result = mergeItems(phone, base, pc, 200);
  assert.deepEqual(new Set(result.map(x => x.id)), new Set(['a', 'phone', 'pc']));
  assert.deepEqual(mergeItems(result, base, pc, 200), result);
});
test('edit conflict and delete/edit conflict never overwrite current data', () => {
  const base = [memo('a', 'original')], current = [memo('a', 'phone')];
  assert.throws(() => mergeItems(current, base, [memo('a', 'pc')], 200));
  assert.throws(() => mergeItems(current, base, [], 200));
  assert.deepEqual(current, [memo('a', 'phone')]);
});
test('deletion preserves unrelated additions and capacity rejects without truncation', () => {
  const a = memo('a', 'a'), b = memo('b', 'b');
  assert.deepEqual(mergeItems([a, b], [a], [], 200), [b]);
  assert.throws(() => mergeItems([a], [], [b], 1));
});
test('independent fields of one keyword merge', () => {
  const base = [{id: 'kw', ts: 1, kw: 'news', hit: 0, done: false}];
  assert.deepEqual(mergeItems([{...base[0], hit: 10}], base, [{...base[0], done: true}], 40), [{...base[0], hit: 10, done: true}]);
});
test('temporary object or body read failures do not delete live jobs', async () => {
  for (const fail of ['get', 'body']) {
    const deleted = [];
    const response = await jobs({env:{R2:{
      list: async () => ({objects:[{key:'jobs/live/thumb-one.json', uploaded:new Date()}]}),
      get: async () => { if(fail === 'get') throw Error('temporary'); return {text:async()=>{throw Error('temporary stream');}}; },
      delete: async key => deleted.push(key),
    }}});
    assert.deepEqual(deleted, []);
    assert.equal((await response.json()).reason, 'partial-read');
  }
});
test('expired jobs are still removed and healthy jobs remain visible', async () => {
  const deleted = [];
  const response = await jobs({env:{R2:{
    list: async () => ({objects:[{key:'old', uploaded:new Date(0)},{key:'new',uploaded:new Date()}]}),
    get: async key => ({text:async()=>JSON.stringify({id:key,t0:key==='old'?1:Date.now()})}),
    delete: async key => deleted.push(key),
  }}});
  assert.deepEqual(deleted, ['old']);
  assert.equal((await response.json()).items[0].id, 'new');
});
test('API recomputes merge after SHA conflict and refuses malformed stored data', async () => {
  const original = globalThis.fetch;
  let state = {memos:[memo('a', 'a')]}, puts = 0;
  globalThis.fetch = async (_url, options={}) => {
    if(options.method !== 'PUT') return new Response(JSON.stringify({sha:String(puts),content:Buffer.from(JSON.stringify(state)).toString('base64')}));
    puts++;
    if(puts === 1) {state.memos.push(memo('phone', 'phone')); return new Response('{}',{status:409});}
    state = JSON.parse(Buffer.from(JSON.parse(options.body).content,'base64').toString());
    return new Response('{}');
  };
  const request = (body) => new Request('https://edit.nomute.kr/api/settings',{method:'POST',headers:{origin:'https://edit.nomute.kr','content-type':'application/json'},body:JSON.stringify(body)});
  try {
    const r = await save({env:{GH_TOKEN:'test'},request:request({base:{memos:[memo('a','a')]},patch:{memos:[memo('a','a'),memo('pc','pc')]}})});
    assert.equal(r.status,200);
    assert.deepEqual(new Set(state.memos.map(x=>x.id)),new Set(['a','phone','pc']));
    assert.equal((await save({env:{GH_TOKEN:'test'},request:request({patch:{memos:[]}})})).status,409);
    globalThis.fetch = async () => new Response(JSON.stringify({sha:'x',content:Buffer.from('{broken').toString('base64')}));
    assert.equal((await save({env:{GH_TOKEN:'test'},request:request({patch:{genImgOn:false}})})).status,502);
    globalThis.fetch = async () => new Response('{broken');
    assert.equal((await read({env:{GH_TOKEN:'test'}})).status,502);
  } finally {globalThis.fetch = original;}
});
