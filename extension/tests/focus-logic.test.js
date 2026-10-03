import test from 'node:test';
import assert from 'node:assert/strict';
import {prepareGalaxy} from '../ui/galaxy-logic.js';
import {projectFocus} from '../ui/focus-logic.js';

const fixture=()=>prepareGalaxy(['A','B','C','D','E'].map(id=>({id,topic:`Raw ${id}`,domain:'Science',description:'Original <raw>'})),{
 schema_version:1,cache_key:'fixture',metadata:{},domains:[{id:'Science',x:0,y:0}],topics:[
  {id:'A',x:2,y:1,neighbors:[{id:'B',distance:.2},{id:'C',distance:.3}]},
  {id:'B',x:2,y:3,neighbors:[]},{id:'C',x:2,y:1,neighbors:[]},
  {id:'D',x:0,y:1,neighbors:[]},{id:'E',x:2,y:1,neighbors:[]} ]});
const candidate=(id,distance)=>({id,distance,topic:'service text',description:'service description'});

test('projects fixed semantic radii with the center at zero and world coordinate direction',()=>{
 const data=fixture(),result=projectFocus(data,'A',[candidate('D',.4)]);
 const seed=result.nodes.find(n=>n.id==='A'),b=result.nodes.find(n=>n.id==='B'),d=result.nodes.find(n=>n.id==='D');
 assert.equal(result.seedId,'A'); assert.equal(seed.x,0);assert.equal(seed.y,0);assert.equal(seed.distance,0);
 assert.ok(Math.abs(b.x)<1e-9);assert.equal(b.y,200);assert.ok(Math.abs(d.x+400)<1e-9);assert.ok(Math.abs(d.y)<1e-9);
 for(const point of result.nodes) assert.ok(Math.abs(Math.hypot(point.x,point.y)-1000*point.distance)<1e-9);
 assert.equal(d.topic,'Raw D');assert.equal(d.description,'Original <raw>');
});

test('deduplicates neighbor candidates and keeps cached distances stable across recommendation batches',()=>{
 const data=fixture(),before=structuredClone(data),b=candidate('B',.2000001),c=candidate('C',.3),d=candidate('D',.4);
 const first=projectFocus(data,'A',[b]),second=projectFocus(data,'A',[c,b]);
 assert.deepEqual(first.nodes.find(n=>n.id==='B'),second.nodes.find(n=>n.id==='B'));
 const result=projectFocus(data,'A',[b,b,d,d,candidate('A',0),candidate('unknown',.4)]);
 assert.deepEqual(result.nodes.map(n=>n.id).sort(),['A','B','C','D']);
 assert.equal(result.nodes.find(n=>n.id==='B').distance,.2);
 assert.equal(result.nodes.find(n=>n.id==='B').isNeighbor,true);assert.equal(result.nodes.find(n=>n.id==='B').isRecommendation,true);
 assert.deepEqual(data,before);
});

test('coincident global positions have deterministic ID angles independent of order, language or viewport',()=>{
 const data=fixture(),recommendations=[candidate('D',.4),candidate('E',.5)];
 const first=projectFocus(data,'A',recommendations);
 const reordered={...data,topics:[...data.topics].reverse(),byId:new Map([...data.byId].reverse()),language:'zh',viewport:{width:320,height:700}};
 reordered.byId.set('A',{...reordered.byId.get('A'),neighbors:[...reordered.byId.get('A').neighbors].reverse()});
 assert.deepEqual(projectFocus(reordered,'A',[...recommendations].reverse()),first);
 const c=first.nodes.find(n=>n.id==='C'),e=first.nodes.find(n=>n.id==='E');
 assert.ok(Number.isFinite(c.x)&&Number.isFinite(c.y));
 assert.notEqual(Math.atan2(c.y,c.x),Math.atan2(e.y,e.x));
});

test('suppressed filters candidate role without hiding center or local neighbor context',()=>{
 const data=fixture(),result=projectFocus(data,'A',[candidate('B',.2),candidate('D',.4)],['A','B','D']);
 assert.deepEqual(result.nodes.map(n=>n.id).sort(),['A','B','C']);
 assert.equal(result.nodes.find(n=>n.id==='B').isNeighbor,true);assert.equal(result.nodes.find(n=>n.id==='B').isRecommendation,false);
});

test('unknown custom centers and candidates never get invented coordinates or distance',()=>{
 const data=fixture();
 assert.deepEqual(projectFocus(data,null),{seedId:null,nodes:[]});
 assert.throws(()=>projectFocus(data,'custom'));
 const result=projectFocus(data,'A',[null,undefined,candidate('unknown',.4),candidate('D',NaN),{id:'E'}]);
 assert.deepEqual(result.nodes.map(n=>n.id).sort(),['A','B','C']);
});
