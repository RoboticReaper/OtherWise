import test from 'node:test';
import assert from 'node:assert/strict';
import {summarizeInterests} from '../ui/interest-overview.js';

const topic=(id,domain='Nature',at)=>({id,topic:id,domain,...(at===undefined?{}:{at})});

test('overview counts actual interests and keeps custom keywords out of subject-area totals',()=>{
  const result=summarizeInterests({approved:[topic('Gardening'),topic('Botany'),topic('Painting','Art'),topic('My idea','Custom')]});
  assert.equal(result.savedCount,4);assert.equal(result.domainCount,2);assert.equal(result.unclassifiedCount,1);
  assert.deepEqual(result.domains,[{name:'Nature',count:2},{name:'Art',count:1}]);
});

test('recent exploration shows the latest occurrence of each topic in time order',()=>{
  const explored=[topic('Ecology','Nature',10),topic('Botany','Nature',40),topic('Ecology','Nature',50),topic('Art','Art',30),topic('Music','Music',20)];
  const state={approved:[],explored};const before=structuredClone(state);
  const result=summarizeInterests(state);
  assert.equal(result.exploredCount,4);
  assert.deepEqual(result.recent.map(row=>[row.id,row.at]),[['Ecology',50],['Botany',40],['Art',30]]);
  assert.deepEqual(state,before);
});

test('overview bounds subject rows while reporting all classified and unclassified interests',()=>{
  const result=summarizeInterests({approved:[topic('a','A'),topic('b','B'),topic('c','C'),topic('d','D'),topic('e','E'),topic('f',''),topic('g','Custom')]});
  assert.equal(result.savedCount,7);assert.equal(result.domainCount,5);assert.equal(result.domains.length,4);
  assert.equal(result.otherClassifiedCount,1);assert.equal(result.unclassifiedCount,2);
});

test('empty, malformed and duplicate records do not inflate the overview',()=>{
  assert.deepEqual(summarizeInterests(null),{savedCount:0,domainCount:0,unclassifiedCount:0,domains:[],otherClassifiedCount:0,exploredCount:0,recent:[]});
  const result=summarizeInterests({approved:[null,{},topic('Botany'),topic('Botany')],explored:[null,{},topic('Ecology','Nature',0)]});
  assert.equal(result.savedCount,1);assert.equal(result.exploredCount,1);assert.equal(result.recent[0].at,0);
});

test('overview recomputes after local changes and does not reuse removed topics',()=>{
  const state={approved:[topic('Botany')],explored:[topic('Ecology','Nature',1)]};
  assert.equal(summarizeInterests(state).savedCount,1);
  state.approved=[];state.explored=[];
  assert.equal(summarizeInterests(state).savedCount,0);assert.deepEqual(summarizeInterests(state).recent,[]);
});
