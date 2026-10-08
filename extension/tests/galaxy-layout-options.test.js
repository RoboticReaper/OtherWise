import test from 'node:test';
import assert from 'node:assert/strict';
import {GALAXY_LAYOUT_DEFAULTS,normalizeGalaxyLayoutOptions} from '../core/galaxy-layout-options.js';
import {createState,reduceState,buildRequest} from '../core/index.js';

test('Galaxy B preferences migrate and partial stored controls normalize safely',()=>{
  assert.deepEqual(normalizeGalaxyLayoutOptions(),{n_neighbors:12,min_dist:.4,spread:1.5,repulsion_strength:2.5});
  assert.deepEqual(normalizeGalaxyLayoutOptions({n_neighbors:20,min_dist:NaN,spread:'2',repulsion_strength:Infinity}),{...GALAXY_LAYOUT_DEFAULTS,n_neighbors:20});
  const state=createState();delete state.settings.galaxyLayoutOptions;
  const next=reduceState(state,{type:'PRUNE'});
  assert.deepEqual(next.settings.galaxyLayoutOptions,GALAXY_LAYOUT_DEFAULTS);
  assert.equal(next.settings.galaxyShowDomainLabels,true);assert.equal(next.settings.galaxyShowInterestLabels,true);
});

test('strict Galaxy controls reject extra, missing, nonnumeric, out of range and conflicting values',()=>{
  for(const patch of [{n_neighbors:4},{n_neighbors:60.5},{min_dist:NaN},{min_dist:1,spread:.5},{repulsion_strength:5},{spread:'2'},{history:['private']}] ){
    assert.throws(()=>normalizeGalaxyLayoutOptions({...GALAXY_LAYOUT_DEFAULTS,...patch},{strict:true}));
  }
  assert.throws(()=>normalizeGalaxyLayoutOptions({n_neighbors:12},{strict:true}));
  assert.deepEqual(normalizeGalaxyLayoutOptions({...GALAXY_LAYOUT_DEFAULTS,n_neighbors:60,min_dist:1,spread:3,repulsion_strength:4},{strict:true}),{n_neighbors:60,min_dist:1,spread:3,repulsion_strength:4});
});

test('layout and label preferences persist without invalidating recommendations or altering payloads',()=>{
  let state=reduceState(createState(),{type:'ADD_INTEREST',topic:'Gardening'});
  state.recommendations=[{id:'Botany',topic:'Botany'}];state.lastUpdated=123;
  const payload=buildRequest(state);
  const next=reduceState(state,{type:'SET_SETTINGS',patch:{galaxyLayoutOptions:{n_neighbors:20},galaxyShowDomainLabels:false,galaxyShowInterestLabels:false}});
  assert.equal(next.generation,state.generation);assert.deepEqual(next.recommendations,state.recommendations);assert.equal(next.lastUpdated,123);
  assert.deepEqual(buildRequest(next),payload);assert.equal(next.settings.galaxyLayoutOptions.n_neighbors,20);
  const bad=reduceState(next,{type:'SET_SETTINGS',patch:{galaxyLayoutOptions:{spread:.5,min_dist:.8}}});
  assert.deepEqual(bad.settings.galaxyLayoutOptions,next.settings.galaxyLayoutOptions);assert.ok(bad.lastError);
});
