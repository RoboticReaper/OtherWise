import test from 'node:test';
import assert from 'node:assert/strict';
import {createState, reduceState, buildRequest} from '../core/index.js';

test('sound preferences start quiet and old installs receive safe defaults', () => {
  const initial = createState();
  assert.equal(initial.settings.soundEffectsEnabled, false);
  assert.equal(initial.settings.soundEffectsVolume, .2);
  delete initial.settings.soundEffectsEnabled;
  delete initial.settings.soundEffectsVolume;
  const migrated = reduceState(initial, {type: 'PRUNE'});
  assert.equal(migrated.settings.soundEffectsEnabled, false);
  assert.equal(migrated.settings.soundEffectsVolume, .2);
});

test('sound preferences persist without invalidating recommendations or entering a service payload', () => {
  let state = reduceState(createState(), {type: 'ADD_INTEREST', topic: 'Gardening'});
  state = reduceState(state, {type: 'RECOMMENDATIONS', generation: state.generation, items: [{topic: 'Botany'}]});
  const before = state;
  state = reduceState(state, {type: 'SET_SETTINGS', patch: {soundEffectsEnabled: true, soundEffectsVolume: .65}});
  assert.equal(state.settings.soundEffectsEnabled, true);
  assert.equal(state.settings.soundEffectsVolume, .65);
  assert.equal(state.generation, before.generation);
  assert.deepEqual(state.recommendations, before.recommendations);
  assert.deepEqual(buildRequest(state), buildRequest(before));
  for (const value of [-1, 1.01, NaN, Infinity, '0.5', null]) {
    const next = reduceState(state, {type: 'SET_SETTINGS', patch: {soundEffectsVolume: value, soundEffectsEnabled: 'true'}});
    assert.equal(next.settings.soundEffectsVolume, .65);
    assert.equal(next.settings.soundEffectsEnabled, true);
  }
  const muted = reduceState(state, {type: 'SET_SETTINGS', patch: {soundEffectsVolume: 0, soundEffectsEnabled: false}});
  assert.equal(muted.settings.soundEffectsVolume, 0);
  assert.equal(muted.settings.soundEffectsEnabled, false);
});
