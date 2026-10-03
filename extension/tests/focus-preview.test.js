import test from 'node:test';import assert from 'node:assert/strict';import {readFile} from 'node:fs/promises';
import {createFocusPreview} from '../ui/focus-preview.js';
const fixture=JSON.parse(await readFile(new URL('../focus-preview.v1.json',import.meta.url)));
const topics=JSON.parse(await readFile(new URL('../../data/topics.json',import.meta.url))).map(t=>({...t,id:t.topic}));
const layout=JSON.parse(await readFile(new URL('../../data/galaxy-layout.json',import.meta.url)));
test('offline Focus uses real provenance-checked public envelopes and canonical text only',async()=>{
 const calls=[];const preview=createFocusPreview({load:async()=>{calls.push('load');return {fixture,catalog:topics,layout};}});
 assert.equal(calls.length,0);const result=await preview.request('Gardening',{});assert.equal(result.seed_id,'Gardening');assert.ok(result.recommendations.length>0);assert.ok(result.recommendations.every(r=>r.distance!==.3));
 assert.equal(result.catalog_sha256,layout.metadata.catalog_sha256);assert.equal(result.recommendations[0].description,topics.find(t=>t.id===result.recommendations[0].id).description);
 await assert.rejects(preview.request('Botany',{}));await assert.rejects(preview.request('Gardening',{limit:20}));
});
test('stale preview identity cannot become drawable data',async()=>{
 const changed=structuredClone(fixture);changed.batches[0].envelope.model='wrong';
 const preview=createFocusPreview({load:async()=>({fixture:changed,catalog:topics,layout})});await assert.rejects(preview.request('Gardening',{}));
});
