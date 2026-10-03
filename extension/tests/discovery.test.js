import test from 'node:test';
import assert from 'node:assert/strict';
import {createState,reduceState,buildRequest} from '../core/index.js';
import {createController} from '../controller.js';

const row={id:'Concrete idea',topic:'Concrete idea',domain:'Science',description:'A public idea.',nearest_interest:'Gardening',distance:.32,boundary_offset:.04,zone:'New territory',discovery:{concept_id:'Q12',area_id:'ecology',graph_path:['Ecology','Concrete idea'],source_url:'https://www.wikidata.org/wiki/Q12',level:2,exploration_pick:true,exploration_target:1,exploration_achieved:1}};
function base(){let s=createState();s=reduceState(s,{type:'ADD_INTEREST',topic:'Gardening'});return reduceState(s,{type:'SET_SETTINGS',patch:{recommendationKind:'specific',accessToken:'test-token'}});}
function batch(s){return reduceState(s,{type:'RECOMMENDATIONS',generation:s.generation,items:[row],discovery:{seed:42,exposures:{},graph_sha256:'a'.repeat(64),rerank:false}});}

test('specific batches preserve canonical graph IDs, source paths and exposure counts',()=>{
 const s=batch(base());assert.deepEqual(s.recommendations[0].discovery.graph_path,['Ecology','Concrete idea']);
 assert.equal(s.recommendations[0].id,'Concrete idea');assert.equal(s.discovery.exposures.ecology,1);
});
test('explicit known feedback hides a concept without changing approved interests and can be undone after reload',()=>{
 let s=batch(base());const before=s.approved;
 s=reduceState(s,{type:'SET_DISCOVERY_FEEDBACK',conceptId:'Q12',curious:true,known:true,difficulty:'too_hard'});
 assert.equal(s.discovery.feedback.Q12.known,true);assert.deepEqual(s.approved,before);assert.equal(s.recommendations.length,0);
 assert.equal(buildRequest(s).feedback[0].difficulty,'too_hard');
 s=reduceState(JSON.parse(JSON.stringify(s)),{type:'UNDO_DISCOVERY_FEEDBACK'});
 assert.deepEqual(buildRequest(s).feedback,[]);assert.equal(s.discovery.undo,null);
});
test('broad mode sends no feedback; switching modes preserves saved feedback and reset removes it',()=>{
 let s=batch(base());s=reduceState(s,{type:'SET_DISCOVERY_FEEDBACK',conceptId:'Q12',curious:true,known:false,difficulty:'none'});
 s=reduceState(s,{type:'SET_SETTINGS',patch:{recommendationKind:'broad'}});
 assert.equal(Object.hasOwn(buildRequest(s),'feedback'),false);assert.ok(s.discovery.feedback.Q12);
 s=reduceState(s,{type:'RESET'});assert.deepEqual(s.discovery.feedback,{});assert.equal(s.settings.recommendationKind,'broad');
});
test('feedback from an unshown concept is rejected and clear does not restore stale results',()=>{
 let s=batch(base());s=reduceState(s,{type:'SET_DISCOVERY_FEEDBACK',conceptId:'Q999',curious:true,known:false,difficulty:'none'});
 assert.deepEqual(s.discovery.feedback,{});
 s=reduceState(s,{type:'SET_DISCOVERY_FEEDBACK',conceptId:'Q12',curious:true,known:false,difficulty:'none'});
 const old=s.generation;s=reduceState(s,{type:'CLEAR_DISCOVERY_FEEDBACK'});
 assert.deepEqual(s.discovery.feedback,{});assert.deepEqual(s.discovery.exposures,{});
 assert.equal(reduceState(s,{type:'RECOMMENDATIONS',generation:old,items:[row]}).recommendations.length,0);
});
test('request profile strips display metadata, browsing evidence and undo state',()=>{
 let s=batch(base());s=reduceState(s,{type:'SET_DISCOVERY_FEEDBACK',conceptId:'Q12',curious:true,known:false,difficulty:'none'});
 const data=buildRequest(s);assert.deepEqual(data.feedback,[{concept_id:'Q12',area_id:'ecology',curious:true,known:false,difficulty:'none'}]);
 assert.deepEqual(data.exposures,{ecology:1});assert.equal(JSON.stringify(data).includes('wikidata'),false);
});

function rig({permission=async()=>true,fetcher,write}={}){
 let saved=base();const requests=[];
 const controller=createController({catalog:[],readState:async()=>saved,writeState:async s=>{if(write)await write(s);saved=structuredClone(s);},hasHistoryPermission:async()=>false,hasEndpointPermission:permission,historySearch:async()=>[],openTab:async()=>{},fetchImpl:fetcher|| (async(url,options)=>{requests.push({url,options});const data=JSON.parse(options.body);return new Response(JSON.stringify({recommendations:[row],seed:data.seed,graph_sha256:'a'.repeat(64)}));})});
 return {controller,requests};
}
test('specific requests use authenticated graph route and feedback save reranks with unchanged seed and exposure snapshot',async()=>{
 const r=rig();let s=await r.controller.recommend();assert.equal(r.requests[0].url,'http://127.0.0.1:8000/api/discover');
 const seed=JSON.parse(r.requests[0].options.body).seed;
 s=await r.controller.dispatch({type:'SET_DISCOVERY_FEEDBACK',conceptId:'Q12',curious:true,known:false,difficulty:'none'});
 assert.equal(r.requests.length,2);const second=JSON.parse(r.requests[1].options.body);
 assert.equal(second.seed,seed);assert.deepEqual(second.exposures,{});assert.equal(s.discovery.exposures.ecology,1);
 assert.equal(r.requests[1].options.headers.Authorization,'Bearer test-token');
});
test('clearing feedback while permission is pending prevents transmission of the old profile',async()=>{
 let unblock,entered;const wait=new Promise(r=>unblock=r);const checking=new Promise(r=>entered=r);let calls=0;
 const r=rig({permission:async()=>{if(++calls===1){entered();await wait;}return true;}});
 const pending=r.controller.recommend();await checking;await r.controller.dispatch({type:'CLEAR_DISCOVERY_FEEDBACK'});unblock();await pending;
 assert.equal(r.requests.length,0);
});
test('a storage failure does not commit feedback or send an unsaved rating',async()=>{
 let fail=false;const r=rig({write:async()=>{if(fail)throw new Error('full storage');}});await r.controller.recommend();fail=true;
 await assert.rejects(r.controller.dispatch({type:'SET_DISCOVERY_FEEDBACK',conceptId:'Q12',curious:true,known:false,difficulty:'none'}));
 assert.deepEqual((await r.controller.getState()).discovery.feedback,{});assert.equal(r.requests.length,1);
});
test('long public concept titles can be saved explicitly and dismissed across refreshes',()=>{
 const long={...row,topic:'A'.repeat(89)};
 let s=reduceState(base(),{type:'RECOMMENDATIONS',generation:base().generation,items:[long],discovery:{seed:42,exposures:{},graph_sha256:'a'.repeat(64)}});
 const saved=reduceState(s,{type:'ADD_INTEREST',topic:s.recommendations[0]});
 assert.equal(buildRequest(saved).keywords.includes('A'.repeat(89)),true);
 s=reduceState(s,{type:'DISMISS',id:long.topic});
 s=reduceState(s,{type:'RECOMMENDATIONS',generation:s.generation,items:[long]});
 assert.equal(s.recommendations.length,0);
});
test('offline specific preview supports concept feedback and excludes known concepts',async()=>{
 const preview=await import('../dev-preview.js');
 await preview.dispatch({type:'SET_SETTINGS',patch:{recommendationKind:'specific'}});
 let s=await preview.recommend();assert.ok(s.recommendations[0].discovery);
 const id=s.recommendations[0].discovery.concept_id;
 s=await preview.dispatch({type:'SET_DISCOVERY_FEEDBACK',conceptId:id,curious:true,known:true,difficulty:'none'});
 assert.ok(s.discovery.feedback[id].known);assert.equal(s.recommendations.some(r=>r.discovery?.concept_id===id),false);
});
