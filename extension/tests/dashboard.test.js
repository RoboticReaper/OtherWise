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


test('dashboard waits for its tab before closing the side panel in that same window',async()=>{
  const oldChrome=globalThis.chrome,oldLocation=globalThis.location,calls=[];
  let finishOpening;
  globalThis.location=new URL('chrome-extension://fixture/sidepanel.html');
  globalThis.chrome={runtime:{id:'fixture',getURL:path=>'chrome-extension://fixture/'+path},
    tabs:{create:opts=>{calls.push({type:'open',...opts});return new Promise(resolve=>{finishOpening=resolve;});}},
    sidePanel:{close:async opts=>{calls.push({type:'close',...opts});}}};
  try{
    const {openDashboard}=await import('../bridge.js?dashboard-close-order');
    const opening=openDashboard('discover');
    assert.deepEqual(calls,[{type:'open',url:'chrome-extension://fixture/dashboard.html?view=discover'}]);
    finishOpening({id:40,windowId:7});await opening;
    assert.deepEqual(calls,[{type:'open',url:'chrome-extension://fixture/dashboard.html?view=discover'},{type:'close',windowId:7}]);
  }finally{globalThis.chrome=oldChrome;globalThis.location=oldLocation;}
});

test('failed dashboard opening leaves the original side panel available',async()=>{
  const oldChrome=globalThis.chrome,oldLocation=globalThis.location;
  let closed=0;
  globalThis.location=new URL('chrome-extension://fixture/sidepanel.html');
  globalThis.chrome={runtime:{id:'fixture',getURL:path=>'chrome-extension://fixture/'+path},
    tabs:{create:async()=>{throw new Error('Tab creation failed');}},sidePanel:{close:async()=>{closed++;}}};
  try{
    const {openDashboard}=await import('../bridge.js?dashboard-close-open-failure');
    await assert.rejects(openDashboard('discover'),/Could not open the dashboard/);
    assert.equal(closed,0);
  }finally{globalThis.chrome=oldChrome;globalThis.location=oldLocation;}
});

test('unsupported or failed panel closing still opens the dashboard once',async()=>{
  const oldChrome=globalThis.chrome,oldLocation=globalThis.location;
  let opened=0,closed=0;
  globalThis.location=new URL('chrome-extension://fixture/sidepanel.html');
  globalThis.chrome={runtime:{id:'fixture',getURL:path=>'chrome-extension://fixture/'+path},
    tabs:{create:async()=>{opened++;return {id:40,windowId:7};}},sidePanel:{}};
  try{
    const {openDashboard}=await import('../bridge.js?dashboard-close-compatibility');
    await openDashboard('discover');assert.equal(opened,1);
    chrome.sidePanel.close=async opts=>{assert.deepEqual(opts,{windowId:7});closed++;throw new Error('Panel close unavailable');};
    await openDashboard('discover');assert.equal(opened,2);assert.equal(closed,1);
  }finally{globalThis.chrome=oldChrome;globalThis.location=oldLocation;}
});
