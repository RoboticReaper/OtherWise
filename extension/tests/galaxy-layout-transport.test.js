import test from 'node:test';
import assert from 'node:assert/strict';
import {createGalaxyLayoutTransport} from '../galaxy-layout-transport.js';
import {GALAXY_LAYOUT_DEFAULTS as parameters} from '../core/galaxy-layout-options.js';
const catalog=['Gardening','Botany'].map(topic=>({topic,domain:'Nature'}));
const identity={catalog_sha256:'a'.repeat(64),model:'MPNet',embedding:{sha256:'b'.repeat(64),dtype:'float64',shape:[2,768]}};
const result=()=>({schema_version:1,cache_key:'c'.repeat(64),...identity,parameters:{...parameters},topics:catalog.map((t,i)=>({id:t.topic,x:i,y:i})),domains:[{id:'Nature',x:0,y:0}]});
function deferred(){let resolve;return {promise:new Promise(r=>resolve=r),resolve:()=>resolve()};}
function rig({permission=async()=>true,fetchImpl,loadIdentity=async()=>identity}={}){
 let connection={endpoint:'https://service.example',accessToken:'secret-code',epoch:0};const requests=[];
 const transport=createGalaxyLayoutTransport({catalog,loadIdentity,getConnection:()=>({...connection}),hasEndpointPermission:permission,
 fetchImpl:fetchImpl || (async(url,options)=>{requests.push({url,options});return new Response(JSON.stringify(options.method==='POST'?{job_id:'job-1',status:'queued',stage:'queued'}:{job_id:'job-1',status:'ready',stage:'ready',result:result()}));})});
 return {transport,requests,change:patch=>{connection={...connection,...patch};}};
}
test('local Galaxy layout start and polling work without a code; remote still needs one',async()=>{
 const r=rig();r.change({endpoint:'http://localhost:8000',accessToken:''});
 const job=await r.transport.start(parameters);assert.equal((await r.transport.status(job.job_id)).status,'ready');
 for(const {options} of r.requests)assert.equal(options.headers.Authorization,undefined);
 r.change({endpoint:'https://service.example'});await assert.rejects(r.transport.start(parameters),/access code/);
 assert.equal(r.requests.length,2);
});
test('Galaxy start uploads only public identity and four controls; poll uses bounded authenticated GET',async()=>{
 const r=rig();const job=await r.transport.start(parameters);assert.equal(job.status,'queued');
 assert.deepEqual(JSON.parse(r.requests[0].options.body),{...identity,parameters});
 assert.equal(r.requests[0].options.headers.Authorization,'Bearer secret-code');assert.equal(r.requests[0].options.credentials,'omit');assert.equal(r.requests[0].options.redirect,'error');
 const ready=await r.transport.status(job.job_id);assert.equal(ready.result.topics.length,2);assert.equal(r.requests[1].url,'https://service.example/api/galaxy-layout/job-1');assert.equal(r.requests[1].options.method,'GET');assert.equal(r.requests[1].options.body,undefined);
});
test('invalid controls and unsafe job IDs reject before network',async()=>{
 const r=rig();await assert.rejects(r.transport.start({...parameters,history:['private']}));
 await assert.rejects(r.transport.status('../secrets'));
 assert.equal(r.requests.length,0);
});
test('invalidated jobs cannot resume polling with unchanged connection settings; a new preview can reuse the job ID',async()=>{
 const r=rig();await r.transport.start(parameters);r.transport.invalidate();
 await assert.rejects(r.transport.status('job-1'),/invalidat|no longer active/i);
 assert.equal(r.requests.length,1);
 const restarted=await r.transport.start(parameters);
 assert.equal((await r.transport.status(restarted.job_id)).status,'ready');
 assert.equal(r.requests.length,3);
});
test('Galaxy rejects complete result for missing/duplicate IDs, nonfinite geometry, controls and identity mismatch',async()=>{
 for(const mutate of [x=>x.topics.pop(),x=>x.topics[1].id=x.topics[0].id,x=>x.topics[0].x='1',x=>x.domains[0].id='Other',x=>x.catalog_sha256='d'.repeat(64),x=>x.parameters.min_dist=.5]){
  const r=rig({fetchImpl:async(_url,options)=>{const x=result();mutate(x);return new Response(JSON.stringify(options.method==='POST'?{job_id:'job-1',status:'queued',stage:'queued'}:{job_id:'job-1',status:'ready',stage:'ready',result:x}));}});
  await r.transport.start(parameters);await assert.rejects(r.transport.status('job-1'),/invalid|match/i);
 }
});
test('connection and permission changes invalidate existing jobs and late requests',async()=>{
 const gate=deferred(),sent=deferred();const r=rig({permission:async()=>{sent.resolve();await gate.promise;return true;}});
 const pending=r.transport.start(parameters),reject=assert.rejects(pending,/cancel|change|invalidat/i);
 await sent.promise;r.change({accessToken:'new'});gate.resolve();await reject;assert.equal(r.requests.length,0);
 const q=rig();await q.transport.start(parameters);q.transport.invalidate();q.change({accessToken:''});await assert.rejects(q.transport.status('job-1'));assert.equal(q.requests.length,1);
 let granted=true;const p=rig({permission:async()=>granted});await p.transport.start(parameters);granted=false;await assert.rejects(p.transport.status('job-1'),/allow|permission|cancel/i);
});
test('timeout settles even if a permission check ignores abort and server details stay private',async t=>{
 t.mock.timers.enable({apis:['setTimeout']});const gate=deferred(),checking=deferred();const r=rig({permission:()=>{checking.resolve();return gate.promise;}});
 const pending=r.transport.start(parameters),reject=assert.rejects(pending,/too long/i);await checking.promise;t.mock.timers.tick(30000);await reject;gate.resolve();
 const q=rig({fetchImpl:async()=>new Response('private secret details',{status:503})});await assert.rejects(q.transport.start(parameters),e=>/service|dependencies|layout/i.test(e.message) && !e.message.includes('private'));
});
