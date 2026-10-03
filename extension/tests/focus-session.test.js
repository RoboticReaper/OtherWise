import test from 'node:test';
import assert from 'node:assert/strict';
import {createFocusSession} from '../ui/focus-session.js';
const envelope=seed_id=>({seed_id,recommendations:[]});
test('selection is local, same-key reuse avoids uploads, explicit refresh resamples',async()=>{
 const sent=[];const session=createFocusSession({request:async(id,options)=>{sent.push([id,options.requestId]);return envelope(id);}});
 session.select('A','A');assert.equal(sent.length,0);await session.load();
 session.select('B','B');session.select('A','A');await session.load();assert.equal(sent.length,1);
 await session.load({refresh:true});assert.equal(sent.length,2);assert.notEqual(sent[0][1],sent[1][1]);assert.equal(typeof sent[0][1],'string');
});
test('late responses cannot overwrite selection or reenter invalidated cache; IDs never restart',async()=>{
 const pending=[],cancelled=[];const session=createFocusSession({request:(id,{requestId})=>new Promise(resolve=>pending.push({id,requestId,resolve})),cancel:id=>cancelled.push(id)});
 session.select('A','A');const old=session.load();session.select('B','B');pending[0].resolve(envelope('A'));await old;
 assert.equal(session.getSnapshot().seedId,'B');assert.equal(session.getSnapshot().envelope,null);
 const newer=session.load();session.invalidate();pending[1].resolve(envelope('B'));await newer;assert.equal(session.getSnapshot().status,'local');
 const latest=session.load();pending[2].resolve(envelope('B'));await latest;assert.equal(new Set(pending.map(p=>p.requestId)).size,3);assert.equal(cancelled.length,2);
});
test('LRU is bounded to twenty, cache hits retain recently used entries',async()=>{
 let calls=0;const session=createFocusSession({request:async id=>{calls++;return envelope(id);}});
 for(let i=0;i<20;i++){session.select(String(i),String(i));await session.load();}
 session.select('0','0');await session.load();session.select('20','20');await session.load();session.select('0','0');await session.load();assert.equal(calls,21);
 session.select('1','1');await session.load();assert.equal(calls,22);
});
test('separate windows keep independent caches, invalidation clears all and destroy ignores completions',async()=>{
 let calls=0;const request=async id=>{calls++;return envelope(id);};const a=createFocusSession({request}),b=createFocusSession({request});
 a.select('A','A');b.select('A','A');await a.load();await b.load();assert.equal(calls,2);
 a.invalidate();await a.load();await b.load();assert.equal(calls,3);a.destroy();await a.load();assert.equal(calls,3);
});
test('failure stays local and recoverable, and leaving cancels pending work without clearing other cache',async()=>{
 let fails=true;const session=createFocusSession({request:async id=>{if(fails)throw new Error('safe message');return envelope(id);}});
 session.select('A','A');await session.load();assert.equal(session.getSnapshot().status,'error');assert.equal(session.getSnapshot().envelope,null);
 fails=false;await session.load();session.select(null,null);session.select('A','A');assert.equal(session.getSnapshot().status,'ready');
});
test('recreated sessions cannot reuse an old bridge request ID after reset',async()=>{
 const ids=[];const request=async(id,{requestId})=>{ids.push(requestId);return envelope(id);};
 const first=createFocusSession({request});first.select('A','A');await first.load();first.destroy();
 const next=createFocusSession({request});next.select('B','B');await next.load();assert.ok(Number(ids[1])>Number(ids[0]));
});
