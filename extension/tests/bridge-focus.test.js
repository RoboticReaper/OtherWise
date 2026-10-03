import test from 'node:test';
import assert from 'node:assert/strict';
function event(){const listeners=new Set();return {addListener:fn=>listeners.add(fn),removeListener:fn=>listeners.delete(fn),emit:(...args)=>[...listeners].map(fn=>fn(...args))};}
function rig(){
  const sent=[],ports=[];globalThis.location={search:'',href:'chrome-extension://'+'a'.repeat(32)+'/dashboard.html'};
  globalThis.chrome={runtime:{id:'a'.repeat(32),connect:({name})=>{const port={name,onMessage:event(),onDisconnect:event(),sent:[],postMessage(message){this.sent.push(message);}};ports.push(port);return port;},
    sendMessage:async message=>{sent.push(message);return {state:{schemaVersion:1}};}}};return {sent,ports};
}

test('bridge Focus replies are owner-port scoped, cancellations reject only matching requests and late replies stay ignored',async()=>{
  const r=rig();const bridge=await import(`../bridge.js?focus-bridge=${Date.now()}`);
  let invalidated=0;const unsubscribe=bridge.subscribeFocusInvalidation(()=>invalidated++);
  const first=bridge.requestFocus('Gardening',{requestId:'one'}),firstRejected=assert.rejects(first,/cancel/i);
  assert.equal(r.ports.length,1);assert.equal(r.ports[0].name,'otherwise-focus');
  assert.deepEqual(r.ports[0].sent[0],{type:'request',requestId:'one',topicId:'Gardening'});
  bridge.cancelFocus('one');await firstRejected;
  r.ports[0].onMessage.emit({requestId:'one',result:{seed_id:'stale'}});
  const second=bridge.requestFocus('Botany',{requestId:'two'});
  r.ports[0].onMessage.emit({requestId:'two',result:{seed_id:'Botany'}});assert.equal((await second).seed_id,'Botany');
  const third=bridge.requestFocus('Ecology',{requestId:'three'}),thirdRejected=assert.rejects(third,/invalidat|cancel/i);
  r.ports[0].onMessage.emit({type:'invalidated'});await thirdRejected;assert.equal(invalidated,1);
  unsubscribe();r.ports[0].onMessage.emit({type:'invalidated'});assert.equal(invalidated,1);
  delete globalThis.chrome;delete globalThis.location;
});

test('bridge disconnect settles pending requests and next request reconnects',async()=>{
  const r=rig();const bridge=await import(`../bridge.js?focus-disconnect=${Date.now()}`);
  const first=bridge.requestFocus('Gardening',{requestId:'one'}),rejected=assert.rejects(first,/reconnect|disconnect|Focus/i);
  r.ports[0].onDisconnect.emit();await rejected;
  const second=bridge.requestFocus('Botany',{requestId:'two'});assert.equal(r.ports.length,2);
  r.ports[0].onMessage.emit({requestId:'two',result:{seed_id:'wrong old port'}});
  r.ports[1].onMessage.emit({requestId:'two',result:{seed_id:'Botany'}});assert.equal((await second).seed_id,'Botany');
  delete globalThis.chrome;delete globalThis.location;
});

test('bridge search forwards map context while legacy call shape remains compatible',async()=>{
  const r=rig();const bridge=await import(`../bridge.js?focus-search=${Date.now()}`);
  await bridge.search('Botany','google',{source:'focus',centerId:'Gardening'});
  assert.deepEqual(r.sent[0],{type:'SEARCH',topic:'Botany',provider:'google',context:{source:'focus',centerId:'Gardening'}});
  await bridge.search('Gardening','youtube');assert.deepEqual(r.sent[1],{type:'SEARCH',topic:'Gardening',provider:'youtube'});
  delete globalThis.chrome;delete globalThis.location;
});

test('bridge rejects reused active IDs without replacing the original and disconnect notifies cache invalidation listeners',async()=>{
  const r=rig();const bridge=await import(`../bridge.js?focus-duplicate=${Date.now()}`);let invalidated=0;
  bridge.subscribeFocusInvalidation(()=>invalidated++);
  const original=bridge.requestFocus('Gardening',{requestId:'one'});
  await assert.rejects(bridge.requestFocus('Botany',{requestId:'one'}),/invalid/i);
  assert.equal(r.ports[0].sent.length,1);
  r.ports[0].onMessage.emit({requestId:'one',result:{seed_id:'Gardening'}});assert.equal((await original).seed_id,'Gardening');
  r.ports[0].onDisconnect.emit();assert.equal(invalidated,1);
  delete globalThis.chrome;delete globalThis.location;
});
