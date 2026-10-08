import test from 'node:test';
import assert from 'node:assert/strict';
import {paginate,PAGE_SIZE} from '../ui/pagination.js';
import * as navigation from '../ui/pagination.js';
import {dictionaries,translate,translateError,normalizeLanguage} from '../ui/i18n.js';

test('a long inbox is partitioned without losing or duplicating topics',()=>{
  const topics=Array.from({length:103},(_,i)=>({id:`Topic ${i+1}`}));
  const first=paginate(topics,1);assert.equal(PAGE_SIZE,10);
  assert.deepEqual(first,{items:topics.slice(0,10),page:1,pageCount:11,total:103,start:1,end:10});
  const pages=Array.from({length:first.pageCount},(_,i)=>paginate(topics,i+1).items).flat();
  assert.deepEqual(pages,topics);
  assert.deepEqual(paginate(topics,11).items,topics.slice(100));
});

test('removing the final page clamps to available topics and an empty inbox has an honest range',()=>{
  const topics=Array.from({length:20},(_,i)=>({id:String(i)}));
  const page=paginate(topics,3);assert.equal(page.page,2);assert.equal(page.start,11);assert.equal(page.end,20);
  assert.deepEqual(paginate([],10),{items:[],page:1,pageCount:1,total:0,start:0,end:0});
});

test('recommendation selection follows the same topic when the batch is reordered',()=>{
  const topics=[{id:'Botany'},{id:'Ecology'},{id:'Urban planning'}];
  assert.deepEqual(navigation.recommendationCursor?.(topics,'Ecology',0),{id:'Ecology',index:1,topic:{id:'Ecology'},total:3});
  assert.deepEqual(navigation.recommendationCursor?.([topics[1],topics[2],topics[0]],'Ecology',1),{id:'Ecology',index:0,topic:{id:'Ecology'},total:3});
});

test('hiding the current recommendation advances into its position and clamps at the end',()=>{
  assert.deepEqual(navigation.recommendationCursor?.([{id:'Botany'},{id:'Urban planning'}],'Ecology',1),{id:'Urban planning',index:1,topic:{id:'Urban planning'},total:2});
  assert.deepEqual(navigation.recommendationCursor?.([{id:'Botany'}],'Urban planning',2),{id:'Botany',index:0,topic:{id:'Botany'},total:1});
  assert.deepEqual(navigation.recommendationCursor?.([],null,12),{id:null,index:0,topic:null,total:0});
});

test('every English UI message has Chinese text with the same interpolation values',()=>{
  assert.deepEqual(Object.keys(dictionaries.en).sort(),Object.keys(dictionaries['zh-CN']).sort());
  const values=text=>[...text.matchAll(/\{([\w]+)\}/g)].map(match=>match[1]).sort();
  for(const [key,message]of Object.entries(dictionaries.en)){
    assert.equal(typeof dictionaries['zh-CN'][key],'string',key);
    assert.ok(dictionaries['zh-CN'][key].trim(),key);
    assert.deepEqual(values(dictionaries['zh-CN'][key]),values(message),key);
  }
  assert.equal(normalizeLanguage('zh-CN'),'zh-CN');assert.equal(normalizeLanguage('unknown'),'en');
});

test('safe errors localize while arbitrary subject text is kept literal',()=>{
  const english='Add your team access code in Settings to connect.';
  assert.notEqual(translateError('zh-CN',english),english);
  assert.equal(translateError('en',english),english);
  assert.equal(translateError('zh-CN','Gardening in Design'),'Gardening in Design');
  const topic='Research in Design <x>';
  assert.ok(translate('zh-CN','connectionFrom',{topic}).includes(topic));
  assert.ok(translate('en','connectionFrom',{topic}).includes(topic));
});
