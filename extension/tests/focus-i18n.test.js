import test from 'node:test';
import assert from 'node:assert/strict';
import {focusDictionaries, focusText} from '../ui/focus-i18n.js';

// Missing translated controls would leave a keyboard user without an action label.
test('Focus controls have complete nonempty English and Chinese labels', () => {
  const keys = ['back','center','chooseCenter','searchPlaceholder','reset','zoomIn','zoomOut','getIdeas',
    'disclosure','local','loading','ready','error','empty','neighbors','candidates','distance','geometry',
    'save','saved','saving','dismiss','explore','google','youtube','closeDetails','previous','next','page',
    'selectionHelp','canvas','current','actionError','selected','domain'];
  assert.deepEqual(Object.keys(focusDictionaries.en).sort(), keys.sort());
  assert.deepEqual(Object.keys(focusDictionaries['zh-CN']).sort(), keys.sort());
  for (const lang of ['en','zh-CN']) for (const key of keys) {
    assert.equal(typeof focusText(lang,key), 'string');
    assert.ok(focusText(lang,key).length > 0);
    assert.notEqual(focusText(lang,key),key);
  }
});

test('interface localization preserves original canonical topic text', () => {
  const topic = 'Computer science & <Original>';
  assert.equal(focusText('zh-CN','selected',{topic}), '已选择 Computer science & <Original>。');
  assert.equal(focusText('en','selected',{topic}), 'Selected Computer science & <Original>.');
  assert.equal(focusText('unknown','selected',{topic}), 'Selected Computer science & <Original>.');
  assert.equal(focusText('en','page',{page:2,pages:4,count:32}), 'Page 2 of 4 · 32 candidates');
});
