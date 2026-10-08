import test from 'node:test';
import assert from 'node:assert/strict';
import {savedInterestPage, togglePageSelection} from '../ui/saved-interests.js';
import {createState, reduceState} from '../core/index.js';

const now = 1_800_000_000_000;
const apply = (state, type, fields = {}) => reduceState(state, {type, ...fields}, now);
const topics = Array.from({length:20}, (_,i) => ({id:`Topic ${i + 1}`, topic:`Topic ${i + 1}`}));
const saved = (...names) => names.reduce((state, topic) => apply(state, 'ADD_INTEREST', {topic}), createState(now));

test('saved interests stay bounded in desktop and sidepanel without losing items', () => {
  for (const [desktop, size] of [[true,8], [false,6]]) {
    const first = savedInterestPage(topics, '', 1, desktop);
    assert.equal(first.items.length, size);
    const all = Array.from({length:first.pageCount}, (_,i) => savedInterestPage(topics, '', i + 1, desktop).items).flat();
    assert.deepEqual(all, topics);
    assert.equal(savedInterestPage(topics, '', 99, desktop).end, 20);
  }
});

test('search matches normalized title words and pagination clamps after filtering or deletion', () => {
  const list = [...topics, {id:'France',topic:'History of France'}, {id:'wide',topic:'Ａｓｉａ'}];
  assert.deepEqual(savedInterestPage(list, '  FRANCE history ', 3, false).items.map(x=>x.id), ['France']);
  assert.equal(savedInterestPage(list, 'asia', 1, true).items[0].id, 'wide');
  const empty = savedInterestPage(list, 'unmatched', 3, false);
  assert.deepEqual([empty.start,empty.end,empty.total,empty.page], [0,0,0,1]);
  assert.equal(savedInterestPage(topics.slice(0,8), '', 3, true).page, 1);
});

test('selecting a visible page preserves selections on other pages and filtering', () => {
  const page = savedInterestPage(topics, '', 2, false).items;
  const previous = new Set(['Topic 1']);
  const selected = togglePageSelection(previous, page);
  assert.equal(selected.size, 7);
  assert.deepEqual([...previous], ['Topic 1']);
  assert.deepEqual([...togglePageSelection(selected, page)], ['Topic 1']);
  const filtered = savedInterestPage(topics, '20', 1, false).items;
  assert.equal(togglePageSelection(selected, filtered).size, 8);
});

test('bulk removal is one profile change, suppresses all removed topics and can be undone exactly', () => {
  const before = saved('Gardening','Botany','Ecology','Architecture');
  before.baseline = ['Gardening','Botany','Ecology'];
  before.settings.mode = 'global'; before.settings.globalLevel = 3;
  const removed = apply(before, 'REMOVE_INTERESTS', {ids:['Botany','Architecture','missing','Botany']});
  assert.deepEqual(removed.approved.map(x=>x.id), ['Gardening','Ecology']);
  assert.deepEqual(removed.baseline, ['Gardening','Ecology']);
  assert.equal(removed.focus, 'Ecology');
  assert.equal(removed.generation, before.generation + 1);
  assert.deepEqual(removed.suppressed, ['Botany','Architecture']);
  assert.deepEqual(before.approved.map(x=>x.id), ['Gardening','Botany','Ecology','Architecture']);
  const restored = apply(removed, 'UNDO_REMOVE_INTERESTS', {token:removed.interestUndo.token});
  assert.deepEqual(restored.approved, before.approved);
  assert.deepEqual(restored.baseline, before.baseline);
  assert.equal(restored.focus, before.focus);
  assert.equal(restored.settings.globalLevel, 3);
  assert.deepEqual(restored.suppressed, []);
  assert.equal(restored.interestUndo, null);
  assert.equal(restored.generation, removed.generation + 1);
});

test('undo never restores an older removal or revives deleted data after reset or a new addition', () => {
  let state = saved('Gardening','Botany','Ecology');
  state = apply(state, 'REMOVE_INTEREST', {id:'Botany'});
  const oldToken = state.interestUndo?.token;
  assert.ok(oldToken);
  state = apply(state, 'REMOVE_INTERESTS', {ids:['Ecology']});
  assert.deepEqual(apply(state, 'UNDO_REMOVE_INTERESTS', {token:oldToken}).approved, state.approved);
  const currentToken = state.interestUndo.token;
  const reset = apply(state, 'RESET');
  assert.deepEqual(apply(reset, 'UNDO_REMOVE_INTERESTS', {token:currentToken}).approved, []);
  const added = apply(state, 'ADD_INTEREST', {topic:'Art'});
  assert.equal(added.interestUndo, null);
  assert.deepEqual(apply(added, 'UNDO_REMOVE_INTERESTS', {token:currentToken}).approved, added.approved);
});

test('undo preserves a later focus choice and invalidates stale recommendation responses', () => {
  const before = saved('Gardening','Botany','Ecology');
  let state = apply(before, 'REMOVE_INTERESTS', {ids:['Ecology']});
  const generation = state.generation;
  const token = state.interestUndo.token;
  state = apply(state, 'SET_FOCUS', {id:'Gardening'});
  state = apply(state, 'UNDO_REMOVE_INTERESTS', {token});
  assert.equal(state.focus, 'Gardening');
  state = apply(state, 'RECOMMENDATIONS', {generation,items:[{topic:'Stale'}]});
  assert.deepEqual(state.recommendations, []);
});

test('no matching removal is a no-op and clearing Undo only clears that receipt', () => {
  let state = saved('Gardening','Botany');
  assert.equal(apply(state, 'REMOVE_INTERESTS', {ids:['unknown']}).generation, state.generation);
  state = apply(state, 'REMOVE_INTERESTS', {ids:['Botany']});
  const cleared = apply(state, 'CLEAR_INTEREST_UNDO', {token:state.interestUndo.token});
  assert.equal(cleared.interestUndo, null);
  assert.deepEqual(cleared.approved, state.approved);
});


test('Undo respects an explicit focus choice even when it returns to the removal fallback', () => {
  let state = apply(saved('Gardening','Botany','Ecology'), 'REMOVE_INTERESTS', {ids:['Ecology']});
  const token = state.interestUndo.token;
  state = apply(state, 'SET_FOCUS', {id:'Gardening'});
  state = apply(state, 'SET_FOCUS', {id:'Botany'});
  assert.equal(apply(state, 'UNDO_REMOVE_INTERESTS', {token}).focus, 'Botany');
  let same = apply(saved('Gardening','Botany','Ecology'), 'REMOVE_INTERESTS', {ids:['Ecology']});
  const sameToken = same.interestUndo.token;
  same = apply(same, 'SET_FOCUS', {id:'Botany'});
  assert.equal(apply(same, 'UNDO_REMOVE_INTERESTS', {token:sameToken}).focus, 'Botany');
});
