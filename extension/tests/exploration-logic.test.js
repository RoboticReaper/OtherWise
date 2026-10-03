import test from 'node:test';
import assert from 'node:assert/strict';
import {prepareGalaxy} from '../ui/galaxy-logic.js';
import {explorationSets} from '../ui/exploration-logic.js';

const data=prepareGalaxy(['A','B','C','D','E'].map(id=>({id,topic:id,domain:'Science',description:''})),{
 schema_version:1,cache_key:'fixture',metadata:{},domains:[{id:'Science',x:0,y:0}],topics:[
 {id:'A',x:0,y:0,neighbors:[{id:'B',distance:.2}]},
 {id:'B',x:1,y:0,neighbors:[{id:'C',distance:.2}]},
 {id:'C',x:2,y:0,neighbors:[]},
 {id:'D',x:3,y:0,neighbors:[{id:'B',distance:.2},{id:'E',distance:.3}]},
 {id:'E',x:4,y:0,neighbors:[{id:'C',distance:.2}]}]});
const sorted=set=>[...set].sort();

test('lights saved centers, one direct neighbor layer and actual explored IDs only',()=>{
 const state={approved:[{id:'A'}],explored:[{id:'E'}],recommendations:[{id:'C'}],focus:'C',suppressed:['B']};
 const before=structuredClone(state),result=explorationSets(data,state);
 for(const value of Object.values(result))assert.ok(value instanceof Set);
 assert.deepEqual(sorted(result.saved),['A']);assert.deepEqual(sorted(result.nearby),['B']);assert.deepEqual(sorted(result.explored),['E']);
 assert.deepEqual(sorted(result.lit),['A','B','E']);assert.deepEqual(state,before);
});

test('overlapping saved regions survive removals and explored points stay lit independently',()=>{
 const explored=[{id:'E'},{id:'E'}];
 assert.deepEqual(sorted(explorationSets(data,{approved:[{id:'A'},{id:'D'}],explored}).lit),['A','B','D','E']);
 assert.deepEqual(sorted(explorationSets(data,{approved:[{id:'A'}],explored}).lit),['A','B','E']);
 assert.deepEqual(sorted(explorationSets(data,{approved:[{id:'D'}],explored}).lit),['B','D','E']);
 assert.deepEqual(sorted(explorationSets(data,{approved:[],explored}).lit),['E']);
});

test('ignores custom IDs and returns empty region with no interests or actual search history',()=>{
 const result=explorationSets(data,{approved:[{id:'custom'}],explored:[{id:'custom'}],candidates:[{id:'A'}],recommendations:[{id:'B'}]});
 for(const value of Object.values(result))assert.equal(value.size,0);
 assert.deepEqual(sorted(explorationSets(data,{}).lit),[]);
});

test('uses the ten nearest cached distances and does not depend on UMAP coordinate proximity',()=>{
 const ids=Array.from({length:11},(_,i)=>`N${i}`);
 const byId=new Map([['A',{id:'A',neighbors:ids.map((id,i)=>({id,distance:(i+1)/20})).reverse()}],...ids.map(id=>[id,{id,x:0,y:0,neighbors:[]}])]);
 const result=explorationSets({byId},{approved:[{id:'A'}],explored:[]});
 assert.equal(result.nearby.size,10);assert.equal(result.nearby.has('N10'),false);assert.equal(result.nearby.has('N0'),true);
});
