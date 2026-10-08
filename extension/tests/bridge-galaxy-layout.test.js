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
