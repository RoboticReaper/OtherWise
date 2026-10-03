import test from 'node:test';
import assert from 'node:assert/strict';
import {createGalaxyLoader} from '../ui/galaxy-data.js';

test('public Galaxy assets load once across concurrent views, with no user state or service request',async()=>{
  const calls=[];
  const loader=createGalaxyLoader({fetchImpl:async(url,options)=>{
    calls.push({url:String(url),options});
    return {ok:true,json:async()=>String(url).endsWith('catalog.json')?[{id:'Gardening'}]:{schema_version:1}};
  }});
  const [a,b]=await Promise.all([loader.load(),loader.load()]);
  assert.equal(a,b);assert.equal(calls.length,2);
  assert.deepEqual(a.catalog,[{id:'Gardening'}]);assert.equal(a.layout.schema_version,1);
  assert.ok(calls.every(call=>call.options.credentials==='omit'&&call.options.redirect==='error'));
  await loader.load();assert.equal(calls.length,2);
});

test('a failed static asset request can retry and never echoes the response',async()=>{
  let failure=true;
  const loader=createGalaxyLoader({fetchImpl:async()=>{
    if(failure)throw new Error('private user input');
    return {ok:true,json:async()=>({})};
  }});
  await assert.rejects(loader.load(),error=>!error.message.includes('private user input'));
  failure=false;await loader.load();
});

test('invalidated parsed assets are fetched again for a user retry',async()=>{
  let calls=0;
  const loader=createGalaxyLoader({fetchImpl:async()=>({ok:true,json:async()=>++calls})});
  const old=await loader.load();loader.invalidate();
  const fresh=await loader.load();assert.equal(calls,4);assert.notDeepEqual(fresh,old);
});

test('dashboard opens a trusted extension page without requesting history or uploading profile data',async()=>{
  const oldChrome=globalThis.chrome,oldLocation=globalThis.location,opened=[];
  globalThis.location=new URL('chrome-extension://fixture/sidepanel.html');
  globalThis.chrome={runtime:{id:'fixture',getURL:path=>'chrome-extension://fixture/'+path},tabs:{create:async opts=>opened.push(opts)}};
  try{
    const {openDashboard}=await import('../bridge.js?dashboard-test');
    await openDashboard('map');await openDashboard('https://external.example');await openDashboard('interests');
    assert.deepEqual(opened,[{url:'chrome-extension://fixture/dashboard.html?view=map'},{url:'chrome-extension://fixture/dashboard.html?view=map'},{url:'chrome-extension://fixture/dashboard.html?view=interests'}]);
  }finally{globalThis.chrome=oldChrome;globalThis.location=oldLocation;}
});
