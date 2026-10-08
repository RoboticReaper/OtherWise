import test from 'node:test';
import assert from 'node:assert/strict';
import {createController} from '../controller.js';
import {createState, reduceState} from '../core/index.js';

test('the real controller accepts and reloads sound settings without permission or service calls', async () => {
  let stored = reduceState(createState(), {type: 'ADD_INTEREST', topic: 'Gardening'});
  stored.settings.autoRefresh = true;
  let externalCalls = 0;
  const create = () => createController({catalog: [], readState: async () => stored,
    writeState: async state => {stored = state;},
    hasHistoryPermission: async () => {externalCalls++; return false;},
    hasEndpointPermission: async () => {externalCalls++; return false;},
    fetchImpl: async () => {externalCalls++; throw new Error('Sound preferences must stay local');},
  });
  const controller = create(), before = await controller.getState();
  const enabled = await controller.dispatch({type: 'SET_SETTINGS', patch: {soundEffectsEnabled: true, soundEffectsVolume: .4}});
  assert.equal(enabled.settings.soundEffectsEnabled, true);
  assert.equal(enabled.settings.soundEffectsVolume, .4);
  assert.equal(enabled.generation, before.generation);
  const reloaded = await create().getState();
  assert.equal(reloaded.settings.soundEffectsEnabled, true);
  assert.equal(reloaded.settings.soundEffectsVolume, .4);
  await controller.dispatch({type: 'SET_SETTINGS', patch: {soundEffectsEnabled: false}});
  assert.equal((await controller.getState()).settings.soundEffectsEnabled, false);
  assert.equal(externalCalls, 0);
});
