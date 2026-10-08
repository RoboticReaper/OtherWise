import test from 'node:test';
import assert from 'node:assert/strict';
import {createSoundEffects} from '../ui/sound-effects.js';

const interest = id => ({id, topic: id});
const state = (ids = [], explored = []) => ({salt: 'same-install', approved: ids.map(interest), explored: explored.map(interest), settings: {galaxyExplorationMode: true}});
const expansion = count => ({byId: new Map([
  ['Old', {...interest('Old'), neighbors: []}],
  ['New', {...interest('New'), neighbors: Array.from({length: count}, (_, i) => ({id: `Neighbor ${i}`, distance: .1 + i * .01}))}],
  ...Array.from({length: count}, (_, i) => [`Neighbor ${i}`, {...interest(`Neighbor ${i}`), neighbors: []}]),
])});

function fixture() {
  let now = 0, active = true, currentFocus = 'A', pending;
  const settings = {soundEffectsEnabled: true, soundEffectsVolume: .2};
  const played = [], audio = [];
  const sounds = createSoundEffects({
    getSettings: () => settings, clock: () => now, isActive: () => active,
    isCurrentFocus: id => currentFocus === id,
    schedule: callback => (pending = callback), cancel: timer => {if (timer === pending) pending = null;},
    createAudio: url => {
      const media = {src: String(url), volume: 1, paused: false,
        play() {played.push({src: this.src, volume: this.volume}); return Promise.resolve();},
        pause() {this.paused = true;},
      };
      audio.push(media); return media;
    },
  });
  return {sounds, settings, played, audio, time: value => {now = value;}, active: value => {active = value;},
    focus: id => {currentFocus = id;},
    flush: async () => {const callback = pending; pending = null; callback?.(); await Promise.resolve();},
  };
}

test('Save uses the supplied 1 sound only after a genuinely new successful save', async () => {
  const f = fixture();
  assert.equal(await f.sounds.saved(state(), state(['Old'])), 'save');
  assert.match(f.played[0].src, /\/assets\/sounds\/save\.wav$/);
  assert.equal(f.played[0].volume, .2);
  f.time(60_000);
  assert.equal(await f.sounds.saved(state(['Old']), state(['Old'])), null);
  assert.equal(await f.sounds.saved(state(), {...state(['New']), lastError: 'Save failed'}), null);
  assert.equal(await f.sounds.saved(state(), {...state(['New']), salt: 'reset-install'}), null);
  assert.equal(f.played.length, 1);
});

test('disabled, zero-volume and background actions are dropped without later replay', async () => {
  const f = fixture();
  f.settings.soundEffectsEnabled = false;
  assert.equal(await f.sounds.saved(state(), state(['Old'])), null);
  f.settings.soundEffectsEnabled = true; f.settings.soundEffectsVolume = 0;
  assert.equal(await f.sounds.saved(state(), state(['Old'])), null);
  f.settings.soundEffectsVolume = .2; f.active(false);
  assert.equal(await f.sounds.saved(state(), state(['Old'])), null);
  f.active(true); f.time(60_000);
  assert.equal(f.played.length, 0);
  assert.equal(await f.sounds.saved(state(), state(['Old'])), 'save');
});

test('rapid and batch saves produce one sound, with a shared two-second Save/Bloom cooldown', async () => {
  const f = fixture();
  await f.sounds.saved(state(), state(['Old', 'Batch two', 'Batch three']));
  f.time(1_999);
  assert.equal(await f.sounds.saved(state(['Old']), state(['Old', 'New']), {data: expansion(4), mapVisible: true}), null);
  f.time(2_000);
  assert.equal(await f.sounds.saved(state(['Old']), state(['Old', 'New']), {data: expansion(4), mapVisible: true}), 'bloom');
  assert.equal(f.played.length, 2);
});

test('Bloom replaces Save for each newly lit neighborhood after the short cooldown', async () => {
  const f = fixture();
  const data = expansion(4);
  data.byId.set('Next', {...interest('Next'), neighbors: Array.from({length: 4}, (_, i) => ({id: `Next neighbor ${i}`, distance: .1 + i * .01}))});
  for (let i = 0; i < 4; i++) data.byId.set(`Next neighbor ${i}`, {...interest(`Next neighbor ${i}`), neighbors: []});
  const options = {data, mapVisible: true};
  assert.equal(await f.sounds.saved(state(['Old']), state(['Old', 'New']), options), 'bloom');
  assert.match(f.played[0].src, /\/assets\/sounds\/bloom\.wav$/);
  f.time(2_000);
  assert.equal(await f.sounds.saved(state(['Old', 'New']), state(['Old', 'New', 'Next']), options), 'bloom');
  assert.equal(f.played.length, 2);
});

test('Bloom excludes overlap and already explored lights, and requires visible exploration mode', async () => {
  for (const [before, after, options] of [
    [state(['Old']), state(['Old', 'New']), {data: expansion(3), mapVisible: true}],
    [state(['Old'], ['Neighbor 0']), state(['Old', 'New'], ['Neighbor 0']), {data: expansion(4), mapVisible: true}],
    [state(['Old']), state(['Old', 'New']), {data: expansion(4), mapVisible: false}],
    [state(['Old']), {...state(['Old', 'New']), settings: {galaxyExplorationMode: false}}, {data: expansion(4), mapVisible: true}],
  ]) {
    const f = fixture();
    assert.equal(await f.sounds.saved(before, after, options), 'save');
  }
  const data = expansion(4);
  data.byId.get('Old').neighbors = [{id: 'Neighbor 0', distance: .1}];
  assert.equal(await fixture().sounds.saved(state(['Old']), state(['Old', 'New']), {data, mapVisible: true}), 'save');
});

test('Explore settles before playing and can repeat within the same domain after two seconds', async () => {
  const f = fixture();
  f.sounds.enterFocus({id: 'A', domain: 'Science'});
  assert.equal(f.played.length, 0);
  await f.flush(); assert.match(f.played[0].src, /\/assets\/sounds\/explore\.wav$/);
  f.time(1_999); f.focus('B'); f.sounds.enterFocus({id: 'B', domain: 'Science'}); await f.flush();
  assert.equal(f.played.length, 1);
  f.time(2_000); f.sounds.enterFocus({id: 'B', domain: 'Science'}); await f.flush();
  assert.equal(f.played.length, 2);
  f.time(4_000); f.focus('A'); f.sounds.enterFocus({id: 'A', domain: 'Science'}); await f.flush();
  assert.equal(f.played.length, 3);
});

test('rapid focus changes, navigation and loss of focus cancel pending Explore sounds', async () => {
  const f = fixture();
  f.sounds.enterFocus({id: 'A', domain: 'Science'});
  f.focus('B'); f.sounds.enterFocus({id: 'B', domain: 'Arts'}); await f.flush();
  assert.equal(f.played.length, 1);
  f.time(90_000); f.focus('C'); f.sounds.enterFocus({id: 'C', domain: 'Nature'});
  f.sounds.stop(); await f.flush(); assert.equal(f.played.length, 1);
  f.sounds.enterFocus({id: 'C', domain: 'Nature'}); f.focus(null); await f.flush(); assert.equal(f.played.length, 1);
  f.focus('C'); f.sounds.enterFocus({id: 'C', domain: 'Nature'}); f.active(false); await f.flush(); assert.equal(f.played.length, 1);
});

test('all event sounds share only a two-second gap, without a rolling event limit', async () => {
  const f = fixture();
  await f.sounds.saved(state(), state(['Old']));
  f.time(1_999); f.sounds.enterFocus({id: 'A', domain: 'Science'}); await f.flush();
  assert.equal(f.played.length, 1);
  f.time(2_000); f.sounds.enterFocus({id: 'A', domain: 'Science'}); await f.flush();
  assert.equal(f.played.length, 2);
  f.time(3_999); assert.equal(await f.sounds.saved(state(['Old']), state(['Old', 'New'])), null);
  f.time(4_000); assert.equal(await f.sounds.saved(state(['Old']), state(['Old', 'New'])), 'save');
  assert.equal(f.played.length, 3);
  f.time(6_000); f.focus('B'); f.sounds.enterFocus({id: 'B', domain: 'Science'}); await f.flush();
  assert.equal(f.played.length, 4);
  f.time(8_000); assert.equal(await f.sounds.saved(state(['Old', 'New']), state(['Old', 'New', 'Third'])), 'save');
  f.time(10_000); f.focus('A'); f.sounds.enterFocus({id: 'A', domain: 'Science'}); await f.flush();
  assert.equal(f.played.length, 6);
});

test('explicit previews work while opted out, never overlap and do not start the automatic cooldown', async () => {
  const f = fixture(); f.settings.soundEffectsEnabled = false;
  assert.equal(await f.sounds.preview('save'), 'save');
  assert.equal(await f.sounds.preview('explore'), 'explore');
  assert.equal(f.audio[0].paused, true);
  assert.equal(await f.sounds.preview('unknown'), null);
  f.settings.soundEffectsEnabled = true;
  assert.equal(await f.sounds.saved(state(), state(['Old'])), 'save');
  f.settings.soundEffectsEnabled = false; f.sounds.syncSettings();
  assert.equal(f.audio.at(-1).paused, true);
});

test('audio failure stays silent and never rejects the successful save', async () => {
  for (const createAudio of [() => {throw new Error('Unavailable');}, () => ({play: () => Promise.reject(new Error('Autoplay blocked')), pause() {}})]) {
    const sounds = createSoundEffects({getSettings: () => ({soundEffectsEnabled: true, soundEffectsVolume: .2}), isActive: () => true, createAudio});
    assert.equal(await sounds.saved(state(), state(['Old'])), null);
  }
});

test('a save completing after navigation, blur or mute is discarded even after returning', async () => {
  const f = fixture(), actionToken = f.sounds.captureAction();
  f.sounds.stop(); f.active(false); f.active(true);
  assert.equal(await f.sounds.saved(state(), state(['Old']), {actionToken}), null);
  assert.equal(f.played.length, 0);
  assert.equal(await f.sounds.saved(state(), state(['Old']), {actionToken: f.sounds.captureAction()}), 'save');
});

test('changing the Focus center immediately stops previous audio before a new delayed entry', async () => {
  const f = fixture();
  f.sounds.enterFocus({id: 'A', domain: 'Science'}); await f.flush();
  assert.equal(f.audio[0].paused, false);
  f.focus('B'); f.sounds.enterFocus({id: 'B', domain: 'Arts'});
  assert.equal(f.audio[0].paused, true);
  await f.flush(); assert.equal(f.played.length, 1);
});
