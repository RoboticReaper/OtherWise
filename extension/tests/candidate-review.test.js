import test from 'node:test';
import assert from 'node:assert/strict';
import {candidateReviewPage, reviewPanelHeight} from '../ui/candidate-review.js';
import {togglePageSelection} from '../ui/saved-interests.js';

const topics = count => Array.from({length:count}, (_, i) => ({id:`topic-${i+1}`, topic:`Topic ${i+1}`}));

for (const [desktop, size] of [[false,5],[true,8]]) {
  test(`306 review topics stay reachable in bounded ${size}-item pages`, () => {
    const all = topics(306);
    const first = candidateReviewPage(all,1,desktop);
    assert.equal(first.items.length,size);
    const pages = Array.from({length:first.pageCount}, (_,i) => candidateReviewPage(all,i+1,desktop));
    assert.ok(pages.every(page => page.items.length <= size));
    assert.deepEqual(pages.flatMap(page => page.items),all);
    assert.equal(pages.at(-1).end,306);
  });
}

test('dismissal clamps the last page and an empty inbox has an honest zero range', () => {
  assert.equal(candidateReviewPage(topics(20),5).page,4);
  assert.deepEqual(candidateReviewPage([],9),{items:[],page:1,pageCount:1,total:0,start:0,end:0});
});

test('selecting and clearing a review page retains selection on other pages', () => {
  const all = topics(306);
  let selected = new Set(['topic-1']);
  selected = togglePageSelection(selected,candidateReviewPage(all,2).items);
  assert.deepEqual([...selected],['topic-1','topic-6','topic-7','topic-8','topic-9','topic-10']);
  selected = togglePageSelection(selected,candidateReviewPage(all,2).items);
  assert.deepEqual([...selected],['topic-1']);
});

test('review workspace fits the remaining viewport and limits very tall windows', () => {
  assert.equal(reviewPanelHeight(900,230),642);
  assert.equal(reviewPanelHeight(850,300),522);
  assert.equal(reviewPanelHeight(600,350),260);
  assert.equal(reviewPanelHeight(1400,200),680);
});
