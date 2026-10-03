import test from 'node:test';
import assert from 'node:assert/strict';
import {focusIdentity, buildFocusRequest, validateFocusResponse} from '../core/focus-contract.js';

const metadata = {catalog_sha256:'a'.repeat(64), model:'sentence-transformers/all-mpnet-base-v2', embedding:{identity:'source-only',sha256:'b'.repeat(64),dtype:'float64',shape:[4,768]}};
const catalog = new Map(['A','B','C','D'].map(id => [id,{id,topic:`Raw ${id}`,domain:'Original domain',description:'Raw <literal> description'}]));
const identity = () => ({catalog_sha256:metadata.catalog_sha256,model:metadata.model,embedding:{sha256:metadata.embedding.sha256,dtype:'float64',shape:[4,768]}});
const request = () => ({topic_id:'A',...identity(),limit:10,radius:.28,expansion:.07,overlap:.015,diversity:.2,max_overlap_fraction:.2,randomness:.03});
const row = (id='B',distance=.3) => ({id,topic:'server title',domain:'server domain',description:'server description',nearest_interest:'A',distance,boundary_offset:distance-.28,zone:'New territory'});
const envelope = () => ({schema_version:1,algorithm_version:'catalog-focus-band-v1',seed_id:'A',...identity(),recommendations:[row()]});

test('extracts original metadata identity without leaking source-only embedding identity', () => {
  const result = focusIdentity(metadata);
  assert.deepEqual(result,identity());
  result.embedding.shape[0] = 99;
  assert.equal(metadata.embedding.shape[0],4);
  for (const mutate of [m=>delete m.catalog_sha256,m=>m.catalog_sha256='bad',m=>m.catalog_sha256='a'.repeat(64)+'\n',m=>m.model='',m=>delete m.embedding.sha256,m=>m.embedding.dtype='',m=>m.embedding.shape=[4,767],m=>m.embedding.shape=[0,768]]) {
    const bad=structuredClone(metadata); mutate(bad); assert.throws(()=>focusIdentity(bad));
  }
});

test('builds a catalog ID request with exactly seven numeric options and no profile data', () => {
  const options={limit:2,radius:.4,expansion:.1,overlap:.02,diversity:.3,max_overlap_fraction:.1,randomness:0};
  const result=buildFocusRequest('A',identity(),options,catalog);
  assert.deepEqual(result,{topic_id:'A',...identity(),...options});
  assert.deepEqual(buildFocusRequest('A',identity(),{},catalog),request());
  for (const options of [{keywords:['private']},{history:['private']},{limit:0},{limit:1.1},{radius:NaN},{expansion:Infinity},{max_overlap_fraction:1},{randomness:'0.1'}]) assert.throws(()=>buildFocusRequest('A',identity(),options,catalog));
  assert.throws(()=>buildFocusRequest('unknown',identity(),{},catalog));
  assert.throws(()=>buildFocusRequest('A',{...identity(),profile:'private'},{},catalog));
  const extra=identity(); extra.embedding.identity='source-only';
  assert.throws(()=>buildFocusRequest('A',extra,{},catalog));
});

test('validates whole envelope and replaces service text with unmodified local catalog text', () => {
  const raw=envelope(), before=structuredClone(raw);
  const result=validateFocusResponse(raw,request(),catalog);
  assert.deepEqual(result.recommendations[0],{...row(),...catalog.get('B')});
  assert.deepEqual(raw,before);
  assert.notEqual(result,raw);
  assert.equal(validateFocusResponse({...envelope(),recommendations:[]},request(),catalog).recommendations.length,0);
});

test('rejects every identity mismatch and malformed whole envelope', () => {
  const changes=[
    x=>x.schema_version=2,x=>x.algorithm_version='layout-version',x=>x.seed_id='wrong',
    x=>x.catalog_sha256='c'.repeat(64),x=>x.model='other-model',x=>x.embedding.sha256='c'.repeat(64),
    x=>x.embedding.dtype='float32',x=>x.embedding.shape=[5,768],x=>x.embedding.shape=[4,767],
    x=>x.embedding.identity='unapproved',x=>x.extra=true,x=>delete x.seed_id,x=>x.recommendations=null,
    x=>x.recommendations.push(row()),x=>x.recommendations[0].id='unknown',x=>x.recommendations[0].id='A',
    x=>x.recommendations[0].nearest_interest='Raw A',x=>x.recommendations[0].distance=NaN,
    x=>delete x.recommendations[0].distance,x=>x.recommendations[0].distance=-.1,
    x=>x.recommendations[0].distance=1.1,x=>x.recommendations[0].distance=.264,
    x=>x.recommendations[0].distance=.351,x=>x.recommendations[0].extra=true,
    x=>delete x.recommendations[0].topic,x=>x.recommendations[0].boundary_offset=Infinity,
    x=>x.recommendations[0].zone='invented',x=>x.recommendations[0].boundary_offset=.2,
  ];
  for(const change of changes){const raw=envelope();change(raw);assert.throws(()=>validateFocusResponse(raw,request(),catalog));}
  const limited={...request(),limit:1};
  assert.throws(()=>validateFocusResponse({...envelope(),recommendations:[row('B'),row('C')]},limited,catalog));
  assert.throws(()=>validateFocusResponse(null,request(),catalog));
});

test('accepts band boundary rounding within 1e-6 but never relaxes absolute distance limits', () => {
  for(const distance of [.265-.0000009,.35+.0000009]) assert.equal(validateFocusResponse({...envelope(),recommendations:[row('B',distance)]},request(),catalog).recommendations[0].distance,distance);
  for(const distance of [.265-.0000011,.35+.0000011]) assert.throws(()=>validateFocusResponse({...envelope(),recommendations:[row('B',distance)]},request(),catalog));
  for(const distance of [-.0000001,1.0000001]) assert.throws(()=>validateFocusResponse({...envelope(),recommendations:[row('B',distance)]},{...request(),radius:0,expansion:1},catalog));
});

test('rejects malformed request envelopes before using their limits or band',()=>{
 for(const change of [x=>delete x.limit,x=>x.limit=NaN,x=>x.radius=-1,x=>x.history=[],x=>x.topic_id='unknown',x=>x.embedding.shape=[4,0]]){
  const bad=request();change(bad);assert.throws(()=>validateFocusResponse(envelope(),bad,catalog));
 }
 const raw=envelope();raw.recommendations.push({...row('C'),distance:NaN});
 assert.throws(()=>validateFocusResponse(raw,request(),catalog));
});

test('accepts both existing zones and clones accepted identity data',()=>{
 const raw=envelope();raw.recommendations[0].zone='Familiar overlap';
 raw.recommendations[0].boundary_offset+=.0000009;
 const result=validateFocusResponse(raw,request(),catalog);
 assert.equal(result.recommendations[0].zone,'Familiar overlap');
 result.embedding.shape[0]=99;assert.equal(raw.embedding.shape[0],4);
});
