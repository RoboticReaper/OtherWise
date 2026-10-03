import test from 'node:test';
import assert from 'node:assert/strict';
import {createController, normalizeEndpoint} from '../controller.js';
import {createState} from '../core/index.js';

const now=1770000000000;
const catalog=[{id:'Gardening',topic:'Gardening',domain:'Nature',description:'Growing plants'}, {id:'Botany',topic:'Botany',domain:'Nature',description:'Studying plants'}];
function rig({fetchImpl,historyItems=[],permission=true,endpointPermission=async()=>true,historySearch,initialState,clock=()=>now}={}) {
  let saved=initialState || createState(now); const requests=[]; const opened=[];
  const controller=createController({catalog, clock,
    readState:async()=>structuredClone(saved), writeState:async value=>{saved=structuredClone(value);},
    historySearch:historySearch || (async()=>historyItems), hasHistoryPermission:async()=>permission,
    hasEndpointPermission:endpointPermission,
    fetchImpl:fetchImpl || (async(url,options)=>{requests.push({url,options});return new Response(JSON.stringify({recommendations:[{...catalog[1],nearest_interest:'Gardening',distance:0.31,boundary_offset:0.03,zone:'New territory'}]}),{status:200});}),
    openTab:async url=>{opened.push(url);},
  });
  return {controller,requests,opened,saved:()=>saved};
}
test('import requires history permission and never contacts the recommender',async()=>{
  const r=rig({permission:false});
  await assert.rejects(()=>r.controller.importHistory(30),/permission/i);
  assert.equal(r.requests.length,0);
});
test('local import produces candidates without approving or transmitting them',async()=>{
  const r=rig({historyItems:[{url:'https://example.org/garden',title:'Gardening for beginners',lastVisitTime:now}]});
  const s=await r.controller.importHistory(30);
  assert.ok(s.candidates.some(x=>x.topic==='Gardening'));
  assert.equal(s.approved.length,0); assert.equal(r.requests.length,0);
  assert.equal(JSON.stringify(s).includes('example.org/garden'),false);
  assert.equal(JSON.stringify(s).includes('Gardening for beginners'),false);
});
test('recommendation payload excludes unconfirmed observations and all source metadata',async()=>{
  const r=rig(); await r.controller.dispatch({type:'ADD_INTEREST',topic:catalog[0]});
  await r.controller.dispatch({type:'SET_SETTINGS',patch:{accessToken:'team-secret'}});
  await r.controller.recommend();
  const request=r.requests[0]; const data=JSON.parse(request.options.body);
  assert.deepEqual(Object.keys(data).sort(),['diversity','expansion','expansion_level','focus','keywords','limit','max_overlap_fraction','mode','overlap','radius','randomness']);
  assert.deepEqual(data.keywords,['Gardening']);
  assert.equal(request.options.headers.Authorization,'Bearer team-secret');
  assert.equal(request.options.redirect,'error');
});
test('reset while a recommendation is pending cannot restore the response',async()=>{
  let release; const gate=new Promise(resolve=>release=resolve);
  const r=rig({fetchImpl:async()=>{await gate; return new Response(JSON.stringify({recommendations:[{...catalog[1],distance:0.31}]}));}});
  await r.controller.dispatch({type:'ADD_INTEREST',topic:catalog[0]});
  await r.controller.dispatch({type:'SET_SETTINGS',patch:{accessToken:'team-secret'}});
  const pending=r.controller.recommend();
  await new Promise(resolve=>setTimeout(resolve,10));
  await r.controller.dispatch({type:'RESET'}); release(); await pending;
  const state=await r.controller.getState();
  assert.equal(state.approved.length,0); assert.equal(state.recommendations.length,0);
});
test('search creates an exploration record without approving the recommended topic',async()=>{
  const r=rig(); await r.controller.dispatch({type:'ADD_INTEREST',topic:catalog[0]});
  await r.controller.dispatch({type:'SET_SETTINGS',patch:{accessToken:'team-secret'}});
  await r.controller.recommend();
  const state=await r.controller.search(catalog[1],'youtube');
  assert.equal(state.approved.some(x=>x.topic==='Botany'),false);
  assert.ok(state.explored.some(x=>x.topic==='Botany'));
  assert.equal(r.opened[0],'https://www.youtube.com/results?search_query=Botany');
});
test('a catalog-only Galaxy topic can be searched with canonical text without becoming an interest',async()=>{
  const r=rig();
  const state=await r.controller.search({id:'Botany',topic:'untrusted replacement',description:'modified'},'google');
  assert.equal(r.opened[0],'https://www.google.com/search?q=Botany');
  assert.equal(state.approved.length,0);assert.equal(state.focus,null);
  assert.equal(state.explored[0].id,'Botany');assert.equal(state.explored[0].description,'Studying plants');
  assert.equal(state.explored[0].parentId,null);assert.equal(r.requests.length,0);
  await assert.rejects(()=>r.controller.search({id:'Unknown injected topic'},'google'),/Choose a topic/);
  assert.equal(r.opened.length,1);
});
test('background analysis defaults off and cannot backfill before opt-in',async()=>{
  const r=rig();
  await r.controller.observe([{url:'https://example.org/a',title:'Gardening',lastVisitTime:now}]);
  assert.equal((await r.controller.getState()).candidates.length,0);
  await r.controller.dispatch({type:'SET_SETTINGS',patch:{browsingEnabled:true}});
  await r.controller.observe([{url:'https://example.org/a',title:'Gardening',lastVisitTime:now-1000}]);
  assert.equal((await r.controller.getState()).candidates.length,0);
});
test('public UI cannot inject unapproved recommendations or raw observations',async()=>{
  const r=rig();
  await assert.rejects(()=>r.controller.dispatch({type:'INGEST',observations:[]}),/action/i);
  await assert.rejects(()=>r.controller.dispatch({type:'RECOMMENDATIONS',items:[]}),/action/i);
});
test('remote endpoints must use HTTPS and cannot hide credentials or paths',()=>{
  assert.equal(normalizeEndpoint('http://127.0.0.1:8000/'),'http://127.0.0.1:8000');
  assert.throws(()=>normalizeEndpoint('http://example.org'));
  assert.throws(()=>normalizeEndpoint('https://a:b@example.org'));
  assert.throws(()=>normalizeEndpoint('https://example.org/private?key=x'));
  assert.throws(()=>normalizeEndpoint('http://[::1]:8000'));
});

function deferred(){let resolve;const promise=new Promise(r=>{resolve=r;});return {promise,resolve};}

test('recommendation tuning persists and cancels an old response; dismiss does not send a replacement request',async()=>{
  const sent=deferred(),response=deferred();let signal;
  const r=rig({fetchImpl:async(_url,options)=>{signal=options.signal;sent.resolve();await response.promise;return new Response(JSON.stringify({recommendations:[catalog[1]]}));}});
  await r.controller.dispatch({type:'ADD_INTEREST',topic:catalog[0]});
  await r.controller.dispatch({type:'SET_SETTINGS',patch:{accessToken:'team-secret'}});
  const pending=r.controller.recommend();await sent.promise;
  await r.controller.dispatch({type:'SET_SETTINGS',patch:{recommendationOptions:{limit:40,overlap:.03}}});
  assert.equal(signal.aborted,true);
  response.resolve();await pending;
  assert.equal((await r.controller.getState()).recommendations.length,0);
  const reloaded=rig({initialState:r.saved()});
  await reloaded.controller.recommend();
  const payload=JSON.parse(reloaded.requests[0].options.body);
  assert.equal(payload.limit,40);assert.equal(payload.overlap,.03);
  await reloaded.controller.dispatch({type:'DISMISS',id:'Botany'});
  assert.equal(reloaded.requests.length,1);
  assert.equal((await reloaded.controller.getState()).recommendations.length,0);
});

for(const [preference,initial,value]of [['language','en','zh-CN'],['recommendationView','cards','list']]) {
test(`${preference} preference persists across controller reload without changing recommendation data or payload`,async()=>{
  const r=rig();
  assert.equal((await r.controller.getState()).settings[preference],initial);
  await r.controller.dispatch({type:'ADD_INTEREST',topic:catalog[0]});
  await r.controller.dispatch({type:'SET_SETTINGS',patch:{accessToken:'team-secret',autoRefresh:true}});
  await r.controller.recommend();
  const before=await r.controller.getState(),count=r.requests.length;
  const state=await r.controller.dispatch({type:'SET_SETTINGS',patch:{[preference]:value}});
  assert.equal(state.settings[preference],value);
  assert.equal(state.generation,before.generation);
  assert.deepEqual(state.recommendations,before.recommendations);
  assert.deepEqual(state.approved,before.approved);
  assert.equal(r.requests.length,count);
  const reloaded=rig({initialState:r.saved()});
  assert.equal((await reloaded.controller.getState()).settings[preference],value);
  await reloaded.controller.recommend();
  assert.deepEqual(JSON.parse(reloaded.requests[0].options.body),JSON.parse(r.requests.at(-1).options.body));
});

test(`${preference} switching during an active recommendation keeps the request and its eventual results`,async()=>{
  const sent=deferred(),response=deferred();let signal;
  const r=rig({fetchImpl:async(_url,options)=>{signal=options.signal;sent.resolve();await response.promise;return new Response(JSON.stringify({recommendations:[catalog[1]]}));}});
  await r.controller.dispatch({type:'ADD_INTEREST',topic:catalog[0]});
  await r.controller.dispatch({type:'SET_SETTINGS',patch:{accessToken:'team-secret'}});
  const pending=r.controller.recommend();await sent.promise;
  await r.controller.dispatch({type:'SET_SETTINGS',patch:{[preference]:value}});
  assert.equal(signal.aborted,false);
  response.resolve();const state=await pending;
  assert.equal(state.settings[preference],value);
  assert.equal(state.recommendations[0].topic,'Botany');
});
}

test('legacy and unsupported language preferences fall back to English without removing saved interests',async()=>{
  const initialState=createState(now);delete initialState.settings.language;delete initialState.settings.recommendationView;
  initialState.approved=[catalog[0]];
  const r=rig({initialState});
  assert.equal((await r.controller.getState()).settings.language,'en');
  assert.equal((await r.controller.getState()).settings.recommendationView,'cards');
  const state=await r.controller.dispatch({type:'SET_SETTINGS',patch:{language:'fr',recommendationView:'unrecognized'}});
  assert.equal(state.settings.language,'en');assert.equal(state.settings.recommendationView,'cards');assert.deepEqual(state.approved,[catalog[0]]);
});

for(const action of [{type:'RESET'},{type:'SET_SETTINGS',patch:{browsingEnabled:false}},{type:'REMOVE_INTEREST',id:'Gardening'}]) {
  test(`${action.type} during endpoint permission wait prevents an old profile from being sent`,async()=>{
    const waiting=deferred(), permissionGate=deferred();
    const r=rig({endpointPermission:async()=>{waiting.resolve();return permissionGate.promise;}});
    await r.controller.dispatch({type:'ADD_INTEREST',topic:catalog[0]});
    await r.controller.dispatch({type:'SET_SETTINGS',patch:{accessToken:'team-secret',browsingEnabled:true}});
    const pending=r.controller.recommend(); await waiting.promise;
    await r.controller.dispatch(action); permissionGate.resolve(true); await pending;
    assert.equal(r.requests.length,0); assert.equal((await r.controller.getState()).recommendations.length,0);
  });
}

test('a sent request is aborted when profile changes and its late response cannot restore results',async()=>{
  const sent=deferred(), response=deferred(); let signal;
  const r=rig({fetchImpl:async(_url,options)=>{signal=options.signal;sent.resolve();await response.promise;return new Response(JSON.stringify({recommendations:[catalog[1]]}));}});
  await r.controller.dispatch({type:'ADD_INTEREST',topic:catalog[0]});
  await r.controller.dispatch({type:'SET_SETTINGS',patch:{accessToken:'team-secret'}});
  const pending=r.controller.recommend(); await sent.promise;
  await r.controller.dispatch({type:'REMOVE_INTEREST',id:'Gardening'}); assert.equal(signal.aborted,true);
  response.resolve(); const state=await pending; assert.equal(state.recommendations.length,0); assert.equal(state.lastError,null);
});

test('public focus changes select an approved branch and cannot select an arbitrary topic',async()=>{
  const r=rig(); await r.controller.dispatch({type:'ADD_INTEREST',topic:catalog[0]}); await r.controller.dispatch({type:'ADD_INTEREST',topic:catalog[1]});
  const state=await r.controller.dispatch({type:'SET_FOCUS',id:'Gardening'}); assert.equal(state.focus,'Gardening');
  assert.equal((await r.controller.dispatch({type:'SET_FOCUS',id:'Unknown'})).focus,'Gardening');
});

test('untrusted service exceptions cannot display private URLs, credentials or interest lists',async()=>{
  const r=rig({fetchImpl:async()=>{throw new Error('secret-code https://private.example Gardening');}});
  await r.controller.dispatch({type:'ADD_INTEREST',topic:catalog[0]}); await r.controller.dispatch({type:'SET_SETTINGS',patch:{accessToken:'team-secret'}});
  const state=await r.controller.recommend(); assert.ok(state.lastError);
  assert.equal(/secret-code|private\.example|Gardening/.test(state.lastError),false);
});

test('reconciliation started before pause and resume cannot re-ingest its old read',async()=>{
  const reading=deferred(), items=deferred();
  const r=rig({historySearch:async()=>{reading.resolve();return items.promise;}});
  await r.controller.dispatch({type:'SET_SETTINGS',patch:{browsingEnabled:true}});
  const pending=r.controller.reconcile(); await reading.promise;
  await r.controller.dispatch({type:'SET_SETTINGS',patch:{browsingEnabled:false}});
  await r.controller.dispatch({type:'SET_SETTINGS',patch:{browsingEnabled:true}});
  items.resolve([{url:'https://example.org/a',title:'Gardening',lastVisitTime:now}]);
  await pending; assert.equal((await r.controller.getState()).evidence.length,0);
});

test('initial history import read cannot survive reset while history lookup is pending',async()=>{
  const reading=deferred(), items=deferred(); const r=rig({historySearch:async()=>{reading.resolve();return items.promise;}});
  const pending=r.controller.importHistory(); await reading.promise; await r.controller.dispatch({type:'RESET'});
  items.resolve([{url:'https://example.org/a',title:'Gardening',lastVisitTime:now}]);
  assert.equal((await pending).evidence.length,0);
});

test('idle state reads expire old history-derived data without changing saved interests',async()=>{
  let time=now; const r=rig({clock:()=>time,historyItems:[{url:'https://example.org/a',title:'Gardening',lastVisitTime:now}]});
  await r.controller.importHistory(); await r.controller.dispatch({type:'ADD_INTEREST',topic:catalog[1]});
  time+=31*86400000; const state=await r.controller.getState();
  assert.equal(state.evidence.length,0); assert.equal(state.candidates.length,0); assert.equal(state.approved[0].topic,'Botany'); assert.equal(r.saved().evidence.length,0);
});

test('bridge requests combined history and connection permissions in one user gesture',async()=>{
  const previousChrome=globalThis.chrome, previousLocation=globalThis.location; const requests=[],messages=[];
  globalThis.location=new URL('chrome-extension://fixture/sidepanel.html');
  globalThis.chrome={permissions:{request:async request=>{requests.push(request);return true;}},runtime:{id:'fixture',sendMessage:async message=>{messages.push(message);return {state:createState(now)};}}};
  try {
    const bridge=await import('../bridge.js?permissions-test');
    await bridge.dispatch({type:'SET_SETTINGS',patch:{browsingEnabled:true,endpoint:'https://service.example'}});
    assert.equal(requests.length,1); assert.deepEqual(requests[0],{permissions:['history'],origins:['https://service.example/*']});
    assert.equal(messages.length,1); assert.equal(messages[0].action.patch.browsingEnabled,true);
  } finally {globalThis.chrome=previousChrome;globalThis.location=previousLocation;}
});

test('a pending history deletion cannot modify a reset installation using its old salt',async()=>{
  const r=rig(); await r.controller.dispatch({type:'ADD_INTEREST',topic:catalog[0]});
  const pending=r.controller.removeHistory({urls:Array.from({length:64},(_,i)=>`https://example.org/${i}`)});
  const reset=await r.controller.dispatch({type:'RESET'});
  const final=await pending;
  assert.equal(final.generation,reset.generation); assert.equal(final.salt,reset.salt); assert.deepEqual(final.evidence,[]);
});

test('opening an exploration tab fails safely without echoing the search URL',async()=>{
  const r=rig(); await r.controller.dispatch({type:'ADD_INTEREST',topic:catalog[0]});
  const controller=createController({catalog,readState:async()=>r.saved(),writeState:async()=>{},historySearch:async()=>[],hasHistoryPermission:async()=>true,hasEndpointPermission:async()=>true,openTab:async url=>{throw new Error(url+' private-code');},clock:()=>now});
  await assert.rejects(()=>controller.search(catalog[0],'google'),error=>!error.message.includes('Gardening') && !error.message.includes('private-code') && !error.message.includes('https://'));
});

test('rejected history lookup errors do not expose history contents or service credentials',async()=>{
  const r=rig({historySearch:async()=>{throw new Error('https://private.example team-secret Gardening');}});
  await assert.rejects(()=>r.controller.importHistory(),error=>/history/i.test(error.message) && !/private\.example|team-secret|Gardening/.test(error.message));
});

test('background observations carrying an old generation cannot survive pause and resume',async()=>{
  const r=rig(); const initial=await r.controller.dispatch({type:'SET_SETTINGS',patch:{browsingEnabled:true}});
  await r.controller.dispatch({type:'SET_SETTINGS',patch:{browsingEnabled:false}});
  await r.controller.dispatch({type:'SET_SETTINGS',patch:{browsingEnabled:true}});
  const state=await r.controller.observe([{url:'https://example.org/a',title:'Gardening',lastVisitTime:now}],initial.generation);
  assert.equal(state.evidence.length,0);
});

test('endpoint revocation invalidates a pending send even when automatic refresh was already disabled',async()=>{
  const waiting=deferred(), permission=deferred(); const r=rig({endpointPermission:async()=>{waiting.resolve();return permission.promise;}});
  assert.equal(typeof r.controller.revokeEndpoint,'function');
  await r.controller.dispatch({type:'ADD_INTEREST',topic:catalog[0]});
  const before=await r.controller.dispatch({type:'SET_SETTINGS',patch:{accessToken:'team-secret'}});
  const pending=r.controller.recommend(); await waiting.promise;
  const revoked=await r.controller.revokeEndpoint(); permission.resolve(true); await pending;
  assert.ok(revoked.generation>before.generation); assert.equal(revoked.settings.autoRefresh,false);
  assert.equal(revoked.approved[0].topic,'Gardening'); assert.equal(r.requests.length,0);
});

test('history deletion still removes deleted evidence when a concurrent approval changes generation but retains salt',async()=>{
  const r=rig({historyItems:[{url:'https://example.org/a',title:'Gardening',lastVisitTime:now}]});
  await r.controller.importHistory();
  const deletion=r.controller.removeHistory({urls:['https://example.org/a']});
  const approved=await r.controller.dispatch({type:'ADD_INTEREST',topic:catalog[1]});
  const state=await deletion;
  assert.equal(state.evidence.length,0); assert.equal(state.candidates.length,0); assert.equal(state.approved[0].topic,'Botany');
  assert.ok(state.generation>approved.generation);
});

test('clearing derived data establishes a new analysis boundary so reconciliation cannot restore older visits',async()=>{
  let time=now;
  const r=rig({clock:()=>time,historyItems:[{url:'https://example.org/old',title:'Gardening',lastVisitTime:now}]});
  await r.controller.dispatch({type:'SET_SETTINGS',patch:{browsingEnabled:true}});
  await r.controller.reconcile(); assert.equal((await r.controller.getState()).evidence.length,1);
  time+=1000;
  const cleared=await r.controller.dispatch({type:'CLEAR_DERIVED'});
  assert.equal(cleared.settings.browsingEnabled,true);
  await r.controller.reconcile(); assert.equal((await r.controller.getState()).evidence.length,0);
  assert.equal(cleared.settings.analysisSince,time);
  time+=1000;
  const fresh=await r.controller.observe([{url:'https://example.org/new',title:'Botany',lastVisitTime:time}]);
  assert.deepEqual(fresh.candidates.map(topic=>topic.id),['Botany']); assert.equal(fresh.evidence.length,1);
});

for(const [mode,parent] of [['global','Gardening'],['path','Basketball']]) {
  test(`${mode} exploration links a recommended topic to its actual interest branch`,async()=>{
    const r=rig(); await r.controller.dispatch({type:'ADD_INTEREST',topic:catalog[0]});
    await r.controller.dispatch({type:'ADD_INTEREST',topic:'Basketball'});
    await r.controller.dispatch({type:'SET_SETTINGS',patch:{mode,accessToken:'team-secret'}});
    await r.controller.recommend();
    const state=await r.controller.search(catalog[1],'google');
    assert.equal(state.explored[0].parentId,parent); assert.equal(state.edges[0].from,parent); assert.equal(state.edges[0].to,'Botany');
  });
}
