import test from 'node:test';
import assert from 'node:assert/strict';
import {createState,reduceState,buildRequest} from '../core/index.js';
import {createController} from '../controller.js';
import {discoverySession} from '../ui/discovery-session.js';
import {recommendationCursor} from '../ui/pagination.js';

const now=1800000000000;
const topic=name=>({id:name,topic:name,domain:'Nature',description:`About ${name}`});
const fixture=()=>{
  let state=reduceState(createState(now),{type:'ADD_INTEREST',topic:topic('Gardening')},now);
  state=reduceState(state,{type:'RECOMMENDATIONS',generation:state.generation,items:[topic('Botany'),topic('Ecology'),topic('Urban planning')]},now);
  return state;
};

test('saving with auto refresh off preserves the trusted batch while invalidating stale requests',()=>{
  const before=fixture();
  const saved=reduceState(before,{type:'ADD_INTEREST',topic:topic('Botany')},now+1);
  assert.equal(saved.settings.autoRefresh,false);
  assert.ok(saved.generation>before.generation);
  assert.deepEqual(saved.recommendations,[]);
  assert.deepEqual(saved.recommendationBatch?.items.map(row=>row.id),['Botany','Ecology','Urban planning']);
  assert.equal(saved.recommendationBatch.focus,'Gardening');
  assert.equal(saved.recommendationBatch.updatedAt,now);
  assert.equal(saved.focus,'Botany');
  const stale=reduceState(saved,{type:'RECOMMENDATIONS',generation:before.generation,items:[topic('Stale response')]},now+2);
  assert.deepEqual(stale.recommendationBatch,saved.recommendationBatch);
  assert.equal('recommendationBatch' in buildRequest(saved),false);
  assert.equal(JSON.stringify(buildRequest(saved)).includes('Ecology'),false);
});

test('dismissing a retained topic removes it and hard invalidations clear the retained batch',()=>{
  const saved=reduceState(fixture(),{type:'ADD_INTEREST',topic:topic('Botany')},now+1);
  const dismissed=reduceState(saved,{type:'DISMISS',id:'Ecology'},now+2);
  assert.deepEqual(dismissed.recommendationBatch?.items.map(row=>row.id),['Botany','Urban planning']);
  for(const action of [{type:'RESET'},{type:'CLEAR_DERIVED'},{type:'REMOVE_INTEREST',id:'Gardening'},{type:'SET_SETTINGS',patch:{mode:'global'}},{type:'SET_SETTINGS',patch:{endpoint:'https://example.org'}},{type:'DELETE_SOURCES',all:true}]){
    assert.equal(reduceState(saved,action,now+3).recommendationBatch,null,action.type);
  }
});

test('retained noncatalog recommendations remain searchable without accepting forged text or auto-refreshing',async()=>{
  let stored=fixture();const requests=[],opened=[];
  stored=reduceState(stored,{type:'SET_SETTINGS',patch:{recommendationKind:'specific',mode:'global'}},now);
  const ecology={...topic('Ecology'),nearest_interest:'Gardening',discovery:{concept_id:'Q12',area_id:'ecology',graph_path:['Gardening','Ecology'],source_url:'https://www.wikidata.org/wiki/Q12',level:2,exploration_pick:true,exploration_target:1,exploration_achieved:1}};
  stored=reduceState(stored,{type:'RECOMMENDATIONS',generation:stored.generation,items:[topic('Botany'),ecology,topic('Urban planning')]},now);
  const make=()=>createController({catalog:[topic('Gardening')],clock:()=>now,
    readState:async()=>structuredClone(stored),writeState:async next=>{stored=structuredClone(next);},
    historySearch:async()=>[],hasHistoryPermission:async()=>false,hasEndpointPermission:async()=>true,
    fetchImpl:async(...args)=>{requests.push(args);throw new Error('Unexpected automatic request');},openTab:async url=>opened.push(url)});
  const controller=make();
  await controller.dispatch({type:'ADD_INTEREST',topic:topic('Botany')});
  // A service-worker restart must not break actions on the still-open page.
  const afterRestart=make();
  const searched=await afterRestart.search({id:'Ecology',topic:'forged title'},'google');
  assert.deepEqual(opened,['https://www.google.com/search?q=Ecology']);
  assert.equal(searched.explored.at(-1).topic,'Ecology');
  assert.equal(searched.explored.at(-1).discovery.concept_id,'Q12');
  assert.equal(searched.explored.at(-1).parentId,'Gardening');
  assert.equal(requests.length,0);
  await afterRestart.dispatch({type:'ADD_INTEREST',topic:topic('Ecology')});
  assert.equal((await afterRestart.getState()).approved.length,3);
});

test('retained path recommendations keep their original search lineage across multiple Saves',async()=>{
  let stored=fixture();const opened=[];
  const controller=createController({catalog:[topic('Gardening')],clock:()=>now,
    readState:async()=>structuredClone(stored),writeState:async next=>{stored=structuredClone(next);},
    historySearch:async()=>[],hasHistoryPermission:async()=>false,hasEndpointPermission:async()=>true,
    fetchImpl:async()=>{throw new Error('Unexpected automatic request');},openTab:async url=>opened.push(url)});
  await controller.dispatch({type:'ADD_INTEREST',topic:topic('Botany')});
  const first=await controller.search('Ecology');
  assert.equal(first.focus,'Botany');
  assert.equal(first.explored.at(-1).parentId,'Gardening');
  await controller.dispatch({type:'ADD_INTEREST',topic:topic('Ecology')});
  const second=await controller.search('Urban planning');
  assert.equal(second.focus,'Ecology');
  assert.equal(second.explored.at(-1).parentId,'Gardening');
  assert.equal(opened.length,2);
});

for(const autoRefresh of [false,true]) {
  test(`an open Discover session retains batch, position and provenance after Save (autoRefresh=${autoRefresh})`,()=>{
    const before=fixture();before.settings.autoRefresh=autoRefresh;
    const initial=discoverySession(null,before,true);
    const saved=reduceState(before,{type:'ADD_INTEREST',topic:topic('Botany')},now+1);
    const kept=discoverySession(initial,saved,true);
    assert.deepEqual(kept.items,initial.items);
    assert.equal(kept.token,initial.token);
    assert.equal(kept.focus,'Gardening');assert.equal(kept.seedCount,1);assert.equal(kept.updatedAt,now);
    assert.equal(recommendationCursor(kept.items,'Ecology',1).index,1);
    const twice=reduceState(saved,{type:'ADD_INTEREST',topic:topic('Ecology')},now+2);
    assert.equal(discoverySession(kept,twice,true).items.length,3);
  });
}

test('leaving Discover and reloading expire retained results without reviving them on reentry',()=>{
  const before=fixture();const opened=discoverySession(null,before,true);
  const saved=reduceState(before,{type:'ADD_INTEREST',topic:topic('Botany')},now+1);
  assert.equal(discoverySession(opened,saved,false),null);
  assert.equal(discoverySession(null,saved,true),null);
  const reloaded=reduceState(JSON.parse(JSON.stringify(saved)),{type:'PRUNE'},now+2);
  assert.equal(discoverySession(null,reloaded,true),null);
});

test('fresh and empty responses replace retained results even with equal update timestamps',()=>{
  const before=fixture();const opened=discoverySession(null,before,true);
  const saved=reduceState(before,{type:'ADD_INTEREST',topic:topic('Botany')},now+1);
  const fresh=reduceState(saved,{type:'RECOMMENDATIONS',generation:saved.generation,items:[topic('Fresh idea')]},now);
  const replaced=discoverySession(opened,fresh,true);
  assert.deepEqual(replaced.items.map(row=>row.id),['Fresh idea']);assert.notEqual(replaced.token,opened.token);
  const empty=reduceState(fresh,{type:'RECOMMENDATIONS',generation:fresh.generation,items:[]},now);
  assert.deepEqual(discoverySession(replaced,empty,true).items,[]);
  assert.notEqual(empty.recommendationBatch.token,fresh.recommendationBatch.token);
});

test('legacy current results migrate once, including an update time of zero',()=>{
  const legacy=fixture();delete legacy.recommendationBatch;legacy.lastUpdated=0;
  const migrated=reduceState(legacy,{type:'PRUNE'},now);
  const visible=discoverySession(null,migrated,true);
  assert.equal(visible.items.length,3);assert.equal(visible.updatedAt,0);
  assert.equal(reduceState(migrated,{type:'PRUNE'},now).recommendationBatch.token,visible.token);
});

test('enabled automatic refresh replaces the retained batch only when its response arrives',async()=>{
  let stored=fixture();stored.settings.autoRefresh=true;
  let start,release,finish;
  const started=new Promise(resolve=>{start=resolve;});
  const response=new Promise(resolve=>{release=resolve;});
  const written=new Promise(resolve=>{finish=resolve;});
  const requests=[];
  const controller=createController({catalog:[topic('Gardening')],clock:()=>now,
    readState:async()=>structuredClone(stored),writeState:async next=>{stored=structuredClone(next);if(next.recommendations[0]?.id==='Fresh idea')finish();},
    historySearch:async()=>[],hasHistoryPermission:async()=>false,hasEndpointPermission:async()=>true,
    fetchImpl:async(_url,options)=>{requests.push(JSON.parse(options.body));start();await response;return new Response(JSON.stringify({recommendations:[topic('Fresh idea')]}));},openTab:async()=>{}});
  const opened=discoverySession(null,stored,true);
  const saved=await controller.dispatch({type:'ADD_INTEREST',topic:topic('Botany')});
  assert.equal(discoverySession(opened,saved,true).items.length,3);
  await started;
  assert.deepEqual(requests[0].keywords,['Gardening','Botany']);
  assert.equal('recommendationBatch' in requests[0],false);
  release();await written;
  const fresh=discoverySession(opened,await controller.getState(),true);
  assert.deepEqual(fresh.items.map(row=>row.id),['Fresh idea']);
  assert.notEqual(fresh.token,opened.token);
});
