import {test} from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFileSync} from 'node:fs';
const html = readFileSync(new URL('../viewer/index.html', import.meta.url), 'utf8');
const source = html.slice(html.indexOf('const SET_CACHE ='), html.indexOf('// ── 화면 잠금'));
const turn = () => new Promise(resolve => setImmediate(resolve));
function client(fetch, storage = new Map()) {
  const events = {}, notices = [];
  const context = {
    fetch, console, setTimeout, clearTimeout, Blob, URL,
    localStorage: {getItem:k=>storage.get(k) || null, setItem:(k,v)=>storage.set(k,v)},
    document: {hidden:false, addEventListener:(n,f)=>events[n]=f, getElementById:()=>null},
    window: {addEventListener:(n,f)=>events[n]=f},
    miniToast: text=>notices.push(text),
  };
  vm.createContext(context);
  vm.runInContext(source + '\nglobalThis.api = {saveSettings, loadSettings, events: null, state:()=>NM_SET, dirty:()=>_setDirty, queued:()=>_setQueue.length};', context);
  return {...context.api, events, notices, storage};
}
const response = settings => new Response(JSON.stringify({settings}));
test('rapid saves are serialized and old responses cannot revert later edits', async () => {
  const releases = [], bodies = [];
  const c = client((_url, options) => new Promise(resolve => {bodies.push(JSON.parse(options.body)); releases.push(resolve);}));
  const one = c.saveSettings({genImgOn:false});
  const two = c.saveSettings({kwAlertOn:true});
  assert.equal(releases.length,1);
  releases[0](response({genImgOn:false,kwAlertOn:false})); await turn();
  assert.equal(c.state().kwAlertOn,true);
  assert.equal(releases.length,2);
  releases[1](response({genImgOn:false,kwAlertOn:true}));
  assert.equal(await one,true); assert.equal(await two,true);
  assert.equal(c.dirty(),false);
});
test('failed writes survive a reload and retry from the same base', async () => {
  const c = client(async()=>{throw Error('offline');});
  assert.equal(await c.saveSettings({memos:[{id:'one',ts:1,text:'keep me'}]}),false);
  assert.equal(c.queued(),1); assert.equal(c.notices.length,1);
  let body;
  const restored = client(async(_u,o)=>{body=JSON.parse(o.body);return response({memos:body.patch.memos});},c.storage);
  await restored.loadSettings();
  assert.equal(restored.queued(),0);
  assert.equal(restored.state().memos[0].text,'keep me');
  assert.deepEqual(body.base.memos,[]);
});
test('a GET begun before a save cannot overwrite the completed save', async () => {
  let release;
  const c = client((_u,o)=>o.method==='POST'?Promise.resolve(response({genImgOn:false})):new Promise(r=>release=r));
  const load = c.loadSettings();
  await c.saveSettings({genImgOn:false});
  release(new Response(JSON.stringify({lockOn:true,genImgOn:true,exists:true})));
  await load;
  assert.equal(c.state().genImgOn,false);
});
test('transient 409 keeps all edits; semantic conflict preserves the full recovery record', async () => {
  for (const semantic of [false,true]) {
    let release;
    const c = client((_u,o)=>o.method==='POST'?new Promise(r=>release=r):Promise.resolve(new Response('{}')));
    const one = c.saveSettings({memos:[{id:'one',ts:1,text:'first'}]});
    const two = c.saveSettings({memos:[{id:'one',ts:1,text:'first'},{id:'two',ts:2,text:'second'}]});
    release(new Response(JSON.stringify({error:'conflict',...(semantic?{code:'settings-conflict'}:{})}),{status:409}));
    await Promise.all([one,two]);
    if(semantic) {
      const recovery=JSON.parse(c.storage.get('nm_settings_conflict'));
      assert.equal(recovery.queue.length,2);
      assert.equal(recovery.settings.memos[1].text,'second');
    } else assert.equal(c.queued(),2);
  }
});
