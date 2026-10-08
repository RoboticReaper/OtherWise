import test from 'node:test';
import assert from 'node:assert/strict';
import {createState, reduceState} from '../core/index.js';
import {createBackup, parseBackup, restoreBackup} from '../core/backup.js';
const now = 1770000000000;
const interest = topic => ({type:'ADD_INTEREST', topic});

test('portable backup round trips saved data and preferences without credentials or browsing evidence', () => {
  let source = reduceState(createState(now), interest('Gardening'), now);
  source = reduceState(source, {type:'EXPLORE',topic:'Botany',parentId:'Gardening'}, now);
  source.settings.accessToken = 'secret-token'; source.settings.endpoint = 'https://private.example';
  source.settings.language = 'zh-CN'; source.settings.browsingEnabled = true;
  source.evidence = [{host:'private.example',sourceHash:'secret-hash'}];
  const backup = createBackup(source, now);
  assert.doesNotMatch(JSON.stringify(backup), /secret-token|private.example|secret-hash|accessToken|browsingEnabled/);
  const target = createState(now); target.settings.accessToken = 'local-token';
  const restored = restoreBackup(target, parseBackup(JSON.stringify(backup)), 'replace', now);
  assert.deepEqual(restored.approved, source.approved);
  assert.deepEqual(restored.explored, source.explored);
  assert.deepEqual(restored.edges, source.edges);
  assert.equal(restored.settings.language, 'zh-CN');
  assert.equal(restored.settings.accessToken, 'local-token');
  assert.equal(restored.settings.browsingEnabled, false);
  assert.equal(restored.salt, target.salt);
  assert.equal(restored.generation, target.generation + 1);
  assert.deepEqual(restored.recommendations, []);
});

test('merge is repeatable, preserves local preferences and ratings, and rejects overflow without changing current data', () => {
  let local = reduceState(createState(now), interest('Gardening'), now);
  let remote = reduceState(createState(now), interest('Botany'), now);
  remote.settings.language = 'zh-CN';
  local.discovery.feedback.Q1 = {area_id:'plants',topic:'Plant cells',curious:true,known:false,difficulty:'none'};
  remote.discovery.feedback.Q1 = {area_id:'plants',topic:'Plant cells',curious:false,known:true,difficulty:'too_basic'};
  const backup = createBackup(remote, now);
  const merged = restoreBackup(local, backup, 'merge', now);
  assert.deepEqual(merged.approved.map(row => row.id), ['Gardening','Botany']);
  assert.equal(merged.settings.language, 'en');
  assert.equal(merged.discovery.feedback.Q1.curious, true);
  assert.deepEqual(restoreBackup(merged, backup, 'merge', now).approved, merged.approved);
  for (let i = 0; i < 39; i++) local = reduceState(local, interest(`Interest ${i}`), now);
  const before = structuredClone(local);
  assert.throws(() => restoreBackup(local, backup, 'merge', now), /40 saved interests/);
  assert.deepEqual(local, before);
});

test('rejects malformed, oversized, future and credential-bearing files rather than partially restoring', () => {
  const good = createBackup(reduceState(createState(now), interest('Gardening'), now), now);
  assert.throws(() => parseBackup('{broken'), /valid OtherWise backup/);
  assert.throws(() => parseBackup(' '.repeat(5 * 1024 * 1024 + 1)), /5 MB/);
  for (const mutate of [
    b => b.version = 999,
    b => b.data.preferences.accessToken = 'untrusted',
    b => b.data.preferences.soundEffectsVolume = 4,
    b => b.data.preferences.recommendationOptions = {},
    b => b.data.approved[0].topic = 'javascript:alert(1)',
    b => b.data.approved[0].id = 'A different ID',
    b => b.data.discovery.feedback.Q1 = {area_id:'plants',topic:'Cells',curious:'yes',known:false,difficulty:'none'},
    b => b.data.explored = null,
    b => b.data.baseline = ['missing'],
  ]) {
    const bad = structuredClone(good); mutate(bad);
    assert.throws(() => parseBackup(JSON.stringify(bad)));
  }
  assert.equal(parseBackup('\uFEFF' + JSON.stringify(good)).data.approved[0].id, 'Gardening');
});

test('merging an exported exploration record does not duplicate it when field order differs', () => {
  let current = reduceState(createState(now), interest('Gardening'), now);
  current = reduceState(current,{type:'EXPLORE',topic:'Botany',parentId:'Gardening'},now);
  const restored = restoreBackup(current,createBackup(current,now),'merge',now);
  assert.equal(restored.explored.length,1);
  assert.equal(restored.edges.length,1);
});

test('the restore boundary rejects oversized objects even if no file parser is used', () => {
  const backup = createBackup(createState(now),now);
  backup.data.explored = Array.from({length:10000},(_,i)=>({id:'Botany',topic:'Botany',domain:'Nature',description:'a'.repeat(500),parentId:null,at:now+i}));
  assert.throws(()=>restoreBackup(createState(now),backup,'replace',now),/5 MB/);
});

test('restored website exclusions remove matching browsing evidence and candidates', () => {
  const local = createState(now);
  local.evidence = [{sourceHash:'fixture',host:'example.org',seenAt:now,topicIds:['Botany'],source:'Chrome'}];
  local.candidates = [{id:'Botany',topic:'Botany',domain:'Nature',description:''}];
  const source = createState(now);source.settings.blockedDomains.push('example.org');
  const restored = restoreBackup(local,createBackup(source,now),'replace',now);
  assert.deepEqual(restored.evidence,[]);
  assert.deepEqual(restored.candidates,[]);
});
