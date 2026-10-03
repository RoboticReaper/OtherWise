import test from 'node:test';
import assert from 'node:assert/strict';
import {createStarActivation} from '../ui/star-activation.js';

function fixture() {
  let now = 0, next = 0;
  const timers = new Map(), selected = [], entered = [];
  const activation = createStarActivation({
    onSelect: id => selected.push(id), onEnterFocus: id => entered.push(id),
    schedule: (callback, delay) => { const id = ++next; timers.set(id, {callback, time: now + delay}); return id; },
    cancelTimer: id => timers.delete(id),
  });
  return {activation, selected, entered, tick(ms) {
    now += ms;
    for (const [id, timer] of [...timers]) if (timer.time <= now) { timers.delete(id); timer.callback(); }
  }};
}

test('a single activation opens details after the cancelable 250ms window', () => {
  const {activation, selected, tick} = fixture();
  activation.click('A'); tick(249); assert.deepEqual(selected, []);
  tick(1); assert.deepEqual(selected, ['A']); tick(300); assert.deepEqual(selected, ['A']);
});

test('double activation cancels details and enters the same star once', () => {
  const {activation, selected, entered, tick} = fixture();
  activation.click('A'); tick(100); activation.click('A'); activation.doubleClick('A'); tick(300);
  assert.deepEqual(selected, []); assert.deepEqual(entered, ['A']);
});

test('cancel and destroy prevent pending details and post-destroy actions', () => {
  const {activation, selected, entered, tick} = fixture();
  activation.click('B'); activation.cancel(); tick(300); assert.deepEqual(selected, []);
  activation.click('C'); activation.destroy(); tick(300);
  activation.click('D'); activation.doubleClick('D'); tick(300);
  assert.deepEqual(selected, []); assert.deepEqual(entered, []);
});

test('changing stars replaces the pending selection without entering either', () => {
  const {activation, selected, entered, tick} = fixture();
  activation.click('A'); tick(100); activation.click('B'); tick(249);
  assert.deepEqual(selected, []); tick(1);
  assert.deepEqual(selected, ['B']); assert.deepEqual(entered, []);
});
