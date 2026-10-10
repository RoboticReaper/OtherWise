import test from 'node:test';
import assert from 'node:assert/strict';
test('Galaxy bridge uses result replies, forwards only explicit controls and handles service errors',async()=>{
  globalThis.location={search:''};let reply={result:{job_id:'job-1',status:'queued',stage:'queued'}};const sent=[];
  globalThis.chrome={runtime:{id:'a'.repeat(32),sendMessage:async message=>{sent.push(message);return reply;}}};
  try{
    const bridge=await import(`../bridge.js?galaxy=${Date.now()}`),parameters={n_neighbors:12,min_dist:.4,spread:1.5,repulsion_strength:2.5};
    assert.equal((await bridge.requestGalaxyLayout(parameters)).job_id,'job-1');await bridge.pollGalaxyLayout('job-1');
    assert.deepEqual(sent,[{type:'GALAXY_LAYOUT_START',parameters},{type:'GALAXY_LAYOUT_STATUS',jobId:'job-1'}]);
    reply={error:'Service unavailable'};await assert.rejects(bridge.pollGalaxyLayout('job-1'),/unavailable/);
    reply={state:{}};await assert.rejects(bridge.requestGalaxyLayout(parameters),/reconnecting/);
  }finally{delete globalThis.chrome;delete globalThis.location;}
});
test('Galaxy invalidation reaches its subscribers without invalidating Focus; reconnect keeps the subscription',async()=>{
 const event=()=>{const listeners=[];return {addListener:listener=>listeners.push(listener),emit:message=>listeners.forEach(listener=>listener(message))};};
 const ports=[];
 globalThis.location={search:''};
 globalThis.chrome={runtime:{id:'a'.repeat(32),connect:()=>{const port={onMessage:event(),onDisconnect:event()};ports.push(port);return port;},sendMessage:async()=>({result:{job_id:'job-1',status:'queued',stage:'queued'}})}};
 try{
  const bridge=await import(`../bridge.js?galaxy-invalidation=${Date.now()}`);
  let focusInvalidations=0,galaxyInvalidations=0;
  const offFocus=bridge.subscribeFocusInvalidation(()=>focusInvalidations++);
  const offGalaxy=bridge.subscribeGalaxyLayoutInvalidation?.(()=>galaxyInvalidations++) || (()=>{});
  ports[0].onMessage.emit({type:'galaxy-layout-invalidated'});
  assert.equal(galaxyInvalidations,1);assert.equal(focusInvalidations,0);
  ports[0].onMessage.emit({type:'invalidated'});
  assert.equal(focusInvalidations,1);assert.equal(galaxyInvalidations,1);
  ports[0].onDisconnect.emit();assert.equal(galaxyInvalidations,2);
  await bridge.requestGalaxyLayout({n_neighbors:12,min_dist:.4,spread:1.5,repulsion_strength:2.5});
  ports.at(-1).onMessage.emit({type:'galaxy-layout-invalidated'});assert.equal(galaxyInvalidations,3);
  offGalaxy();offFocus();ports.at(-1).onMessage.emit({type:'galaxy-layout-invalidated'});assert.equal(galaxyInvalidations,3);
 }finally{delete globalThis.chrome;delete globalThis.location;}
});
