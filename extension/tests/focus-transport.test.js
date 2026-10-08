import test from 'node:test';
import assert from 'node:assert/strict';
import {createFocusTransport} from '../focus-transport.js';
import {RECOMMENDATION_DEFAULTS} from '../core/recommendation-options.js';

const catalog=['Gardening','Botany','Ecology'].map(topic=>({topic,domain:'Nature',description:`Original ${topic}.`}));
const identity={catalog_sha256:'a'.repeat(64),model:'MPNet',embedding:{sha256:'b'.repeat(64),dtype:'float64',shape:[3,768]}};
function deferred(){let resolve;const promise=new Promise(r=>{resolve=r;});return {promise,resolve};}
function envelope(body){
  const {catalog_sha256,model,embedding}=body;
  const id=body.topic_id==='Gardening'?'Botany':'Gardening',distance=body.radius+body.expansion/2;
  return {schema_version:1,algorithm_version:'catalog-focus-band-v1',seed_id:body.topic_id,catalog_sha256,model,embedding,
    recommendations:[{id,topic:'Untrusted text',domain:'Untrusted domain',description:'Untrusted description',
      nearest_interest:body.topic_id,distance,boundary_offset:distance-body.radius,zone:'New territory'}]};
}
function rig({permission=async()=>true,loadIdentity=async()=>identity,fetchImpl}={}){
  let connection={endpoint:'https://service.example',accessToken:'team-secret',epoch:0};
  const requests=[];
  const transport=createFocusTransport({catalog,loadIdentity,getConnection:()=>({...connection}),
    hasEndpointPermission:permission,fetchImpl:fetchImpl || (async(url,options)=>{
      requests.push({url,options});return new Response(JSON.stringify(envelope(JSON.parse(options.body))));
    })});
  return {transport,requests,setConnection:patch=>{connection={...connection,...patch};}};
}
const request=(transport,owner={},patch={})=>transport.request(owner,{requestId:'same-id',topicId:'Gardening',options:{},...patch});

test('Focus supports local requests without a code but still requires codes remotely',async()=>{
  const r=rig();r.setConnection({endpoint:'http://127.0.0.1:8000',accessToken:''});
  assert.equal((await request(r.transport)).seed_id,'Gardening');
  assert.equal(r.requests[0].options.headers.Authorization,undefined);
  r.setConnection({endpoint:'https://service.example'});
  await assert.rejects(request(r.transport),/access code/);assert.equal(r.requests.length,1);
});

// Removing the explicit-request boundary would upload before this assertion.
test('Focus initialization and invalidation alone never load data or upload',async()=>{
  let loaded=0,checked=0,sent=0;
  const r=rig({loadIdentity:async()=>{loaded++;return identity;},permission:async()=>{checked++;return true;},fetchImpl:async()=>{sent++;}});
  r.transport.invalidate();
  await Promise.resolve();
  assert.equal(loaded,0);assert.equal(checked,0);assert.equal(sent,0);
});

test('Focus request sends only canonical seed identity and seven current controls, with local text authority',async()=>{
  const r=rig();const result=await request(r.transport,{}, {options:{limit:5,randomness:0}});
  const {url,options}=r.requests[0],body=JSON.parse(options.body);
  assert.equal(url,'https://service.example/api/focus');
  assert.deepEqual(Object.keys(body).sort(),['topic_id','catalog_sha256','model','embedding',...Object.keys(RECOMMENDATION_DEFAULTS)].sort());
  assert.equal(body.limit,5);assert.equal(body.randomness,0);assert.equal(body.keywords,undefined);
  assert.equal(options.headers.Authorization,'Bearer team-secret');
  assert.equal(options.credentials,'omit');assert.equal(options.redirect,'error');
  assert.equal(result.recommendations[0].topic,'Botany');assert.equal(result.recommendations[0].description,'Original Botany.');
});

test('every explicit Focus request can resample and transport does not cache results',async()=>{
  const r=rig(),owner={};await request(r.transport,owner);await request(r.transport,owner,{requestId:'next'});
  assert.equal(r.requests.length,2);
});

test('same requestId in two owners stays isolated when one cancels',async()=>{
  const sent=deferred(),responses=[],signals=[];
  const r=rig({fetchImpl:async(_url,options)=>{const gate=deferred();responses.push({gate,body:JSON.parse(options.body)});signals.push(options.signal);if(signals.length===2)sent.resolve();await gate.promise;return new Response(JSON.stringify(envelope(JSON.parse(options.body))));}});
  const a={},b={};const first=request(r.transport,a),firstRejected=assert.rejects(first,/cancel/i);const second=request(r.transport,b);
  await sent.promise;r.transport.cancel(a,'same-id');
  assert.equal(signals[0].aborted,true);assert.equal(signals[1].aborted,false);
  await firstRejected;responses[1].gate.resolve();assert.equal((await second).seed_id,'Gardening');responses[0].gate.resolve();
});

test('mismatched cancellation keeps the current owner request; new request cancels only its predecessor',async()=>{
  const sent=deferred(),gate=deferred();let signal;
  const r=rig({fetchImpl:async(_url,options)=>{signal=options.signal;sent.resolve();await gate.promise;return new Response(JSON.stringify(envelope(JSON.parse(options.body))));}});
  const owner={},pending=request(r.transport,owner);await sent.promise;
  r.transport.cancel(owner,'another-id');assert.equal(signal.aborted,false);
  r.transport.cancel(owner);await assert.rejects(pending,/cancel/i);gate.resolve();
});

test('invalidate during an asynchronous permission check prevents upload and broadcasts once',async()=>{
  const checking=deferred(),permission=deferred();const r=rig({permission:()=>{checking.resolve();return permission.promise;}});
  let invalidated=0;const unsubscribe=r.transport.subscribeInvalidation(()=>invalidated++);
  const pending=request(r.transport),rejected=assert.rejects(pending,/cancel|invalidat/i);await checking.promise;
  r.transport.invalidate();await rejected;permission.resolve(true);await new Promise(resolve=>setImmediate(resolve));
  assert.equal(r.requests.length,0);assert.equal(invalidated,1);unsubscribe();r.transport.invalidate();assert.equal(invalidated,1);
});

test('permission is rechecked after receipt and revoked responses never return',async()=>{
  let granted=true;const sent=deferred(),response=deferred();
  const r=rig({permission:async()=>granted,fetchImpl:async(_url,options)=>{sent.resolve();await response.promise;return new Response(JSON.stringify(envelope(JSON.parse(options.body))));}});
  const pending=request(r.transport);await sent.promise;granted=false;response.resolve();
  await assert.rejects(pending,/permission|permitted|allow|cancel|invalidat/i);
});

for(const patch of [{epoch:1},{endpoint:'https://changed.example'},{accessToken:'changed-secret'}]){
  test(`connection change before permission completes prevents stale upload: ${Object.keys(patch)[0]}`,async()=>{
    const checking=deferred(),permission=deferred();const r=rig({permission:()=>{checking.resolve();return permission.promise;}});
    const pending=request(r.transport),rejected=assert.rejects(pending,/cancel|invalidat|change/i);
    await checking.promise;r.setConnection(patch);permission.resolve(true);await rejected;assert.equal(r.requests.length,0);
  });
}

test('30 second timeout settles even when permission check ignores abort',async t=>{
  t.mock.timers.enable({apis:['setTimeout']});
  const checking=deferred(),permission=deferred();const r=rig({permission:()=>{checking.resolve();return permission.promise;}});
  const pending=request(r.transport),rejected=assert.rejects(pending,/too long|time/i);await checking.promise;
  t.mock.timers.tick(30000);await rejected;permission.resolve(true);assert.equal(r.requests.length,0);
});

test('invalid input rejects before network and errors never echo supplied secrets',async()=>{
  const r=rig();
  for(const patch of [{topicId:'private unknown'},{requestId:''},{requestId:4},{requestId:'x'.repeat(121)},{options:{history:['private phrase']}},{options:{radius:NaN}}]){
    await assert.rejects(request(r.transport,{},patch),error=>!error.message.includes('private'));
  }
  assert.equal(r.requests.length,0);
});

test('oversized and identity-conflicting responses are rejected whole',async()=>{
  for(const fetchImpl of [async()=>new Response('x'.repeat(150001)),async(_url,options)=>new Response(JSON.stringify({...envelope(JSON.parse(options.body)),catalog_sha256:'c'.repeat(64)}))]){
    const r=rig({fetchImpl});await assert.rejects(request(r.transport),/too large|invalid|match|Focus/i);
  }
});

test('service error details are never forwarded to caller',async()=>{
  const r=rig({fetchImpl:async()=>new Response('private model credential',{status:503})});
  await assert.rejects(request(r.transport),error=>!error.message.includes('private') && /service|model|Focus/i.test(error.message));
});
