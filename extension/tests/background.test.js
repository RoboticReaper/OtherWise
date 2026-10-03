import test from 'node:test';
import assert from 'node:assert/strict';

function event(){
  const listeners=new Set();
  return {addListener:fn=>listeners.add(fn),hasListener:fn=>listeners.has(fn),
    emit:(...args)=>[...listeners].map(fn=>fn(...args)),get size(){return listeners.size;}};
}
const waitFor=async predicate=>{
  for(let n=0;n<80;n++){if(await predicate())return;await new Promise(resolve=>setTimeout(resolve,25));}
  throw new Error('The background event did not update local state.');
};

test('first optional history grant attaches listeners without restarting, and revoke clears derived data',async()=>{
  let stored,historyGranted=false;
  const id='a'.repeat(32),base=`chrome-extension://${id}/`;
  const runtime={id,getURL:path=>base+path,onMessage:event(),onInstalled:event(),onStartup:event()};
  const permissions={onAdded:event(),onRemoved:event(),contains:async query=>query.permissions?.includes('history')?historyGranted:true};
  globalThis.chrome={runtime,permissions,
    storage:{local:{setAccessLevel:async()=>{},get:async()=>({state:stored}),set:async value=>{stored=value.state;}}},
    tabs:{create:async()=>{}},sidePanel:{setPanelBehavior:async()=>{}},
    alarms:{onAlarm:event(),create:async()=>{}},
  };
  const originalFetch=globalThis.fetch;
  globalThis.fetch=async()=>({json:async()=>[{id:'Gardening',topic:'Gardening',domain:'Nature',description:'Growing plants.'}]});
  try{
    await import('../background.js');
    const send=(message,sender={id,url:base+'sidepanel.html'})=>new Promise(resolve=>runtime.onMessage.emit(message,sender,resolve));
    await send({type:'GET_STATE'});
    assert.equal(stored.settings.browsingEnabled,false);
    const denied=await send({type:'GET_STATE'},{id:'another-extension',url:'https://example.org'});
    assert.ok(denied.error);assert.equal(denied.state,undefined);

    const item={url:'https://example.org/gardening',title:'Gardening for beginners',lastVisitTime:Date.now()+100};
    chrome.history={onVisited:event(),onVisitRemoved:event(),search:async()=>[item]};
    historyGranted=true;
    permissions.onAdded.emit({permissions:['history']});
    permissions.onAdded.emit({permissions:['history']});
    assert.equal(chrome.history.onVisited.size,1);
    assert.equal(chrome.history.onVisitRemoved.size,1);
    await send({type:'ACTION',action:{type:'SET_SETTINGS',patch:{browsingEnabled:true}}});
    chrome.history.onVisited.emit(item);
    await waitFor(()=>stored.candidates.length===1);
    assert.equal(stored.candidates[0].topic,'Gardening');
    assert.equal(stored.approved.length,0);
    assert.ok(!JSON.stringify(stored).includes(item.url));

    historyGranted=false;
    permissions.onRemoved.emit({permissions:['history']});
    await waitFor(()=>!stored.settings.browsingEnabled && stored.evidence.length===0);
    assert.equal(stored.candidates.length,0);
  }finally{
    globalThis.fetch=originalFetch;
    delete globalThis.chrome;
  }
});

test('trusted Focus ports isolate same request IDs, cancel on disconnect, broadcast invalidation, and refuse forged actions',async()=>{
  let stored;const requests=[],responses=[];
  const id='b'.repeat(32),base=`chrome-extension://${id}/`;
  const runtime={id,getURL:path=>base+path,onMessage:event(),onConnect:event(),onInstalled:event(),onStartup:event()};
  const permissions={onAdded:event(),onRemoved:event(),contains:async()=>true};
  const identity={catalog_sha256:'a'.repeat(64),model:'MPNet',embedding:{sha256:'b'.repeat(64),dtype:'float64',shape:[2,768]}};
  const topics=[{topic:'Gardening',domain:'Nature',description:'Growing plants.'},{topic:'Botany',domain:'Nature',description:'Studying plants.'}];
  globalThis.chrome={runtime,permissions,storage:{local:{setAccessLevel:async()=>{},get:async()=>({state:stored}),set:async value=>{stored=value.state;}}},
    tabs:{create:async()=>{}},sidePanel:{setPanelBehavior:async()=>{}},alarms:{onAlarm:event(),create:async()=>{}}};
  const originalFetch=globalThis.fetch;
  globalThis.fetch=async(url,options)=>{
    if(String(url).endsWith('catalog.json'))return {json:async()=>topics};
    if(String(url).endsWith('galaxy-layout.json'))return {ok:true,json:async()=>({metadata:identity})};
    requests.push({url,options});await new Promise(resolve=>responses.push(resolve));
    const body=JSON.parse(options.body);
    return new Response(JSON.stringify({schema_version:1,algorithm_version:'catalog-focus-band-v1',seed_id:body.topic_id,
      ...identity,recommendations:[{id:'Botany',...topics[1],nearest_interest:'Gardening',distance:.31,boundary_offset:.03,zone:'New territory'}]}));
  };
  function port(sender={id,url:base+'dashboard.html'},name='otherwise-focus'){
    return {name,sender,onMessage:event(),onDisconnect:event(),posted:[],disconnected:false,
      postMessage(value){this.posted.push(value);},disconnect(){this.disconnected=true;this.onDisconnect.emit();}};
  }
  try{
    await import(`../background.js?focus-ports=${Date.now()}`);
    const send=message=>new Promise(resolve=>runtime.onMessage.emit(message,{id,url:base+'sidepanel.html'},resolve));
    await send({type:'ACTION',action:{type:'SET_SETTINGS',patch:{accessToken:'team-secret'}}});
    const unauthorized=port({id:'foreign',url:base+'dashboard.html'}),incognito=port({id,url:base+'dashboard.html',tab:{incognito:true}}),external=port({id,url:'https://example.org'});
    for(const candidate of [unauthorized,incognito,external]){runtime.onConnect.emit(candidate);assert.equal(candidate.disconnected,true);}
    const a=port(),b=port();runtime.onConnect.emit(a);runtime.onConnect.emit(b);
    a.onMessage.emit({type:'request',requestId:'same',topicId:'Gardening',owner:'forged'});
    await waitFor(()=>a.posted.some(message=>message.error));assert.equal(requests.length,0);a.posted=[];
    a.onMessage.emit({type:'request',requestId:'same',topicId:'Gardening'});
    b.onMessage.emit({type:'request',requestId:'same',topicId:'Gardening'});
    await waitFor(()=>requests.length===2);
    a.disconnect();await waitFor(()=>requests[0].options.signal.aborted);assert.equal(requests[1].options.signal.aborted,false);
    responses[1]();await waitFor(()=>b.posted.some(message=>message.result));
    assert.equal(b.posted[0].requestId,'same');assert.equal(b.posted[0].result.seed_id,'Gardening');assert.equal(a.posted.length,0);
    const forged=await send({type:'ACTION',action:{type:'EXPLORE_FROM_CATALOG',topic:topics[1],parentId:'Gardening'}});
    assert.ok(forged.error);assert.equal(stored.explored.length,0);
    const search=await send({type:'SEARCH',topic:'Botany',provider:'google',context:{source:'focus',centerId:'Gardening'}});
    assert.equal(search.state.explored[0].parentId,'Gardening');assert.equal(search.state.edges[0].from,'Gardening');
    await send({type:'ACTION',action:{type:'RESET'}});
    await waitFor(()=>b.posted.some(message=>message.type==='invalidated'));
    responses[0]();b.disconnect();
  }finally{for(const release of responses)release();globalThis.fetch=originalFetch;delete globalThis.chrome;}
});
