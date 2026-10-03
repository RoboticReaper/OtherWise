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
