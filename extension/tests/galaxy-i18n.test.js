import test from 'node:test';
import assert from 'node:assert/strict';
import {galaxyDictionaries, galaxyText} from '../ui/galaxy-i18n.js';

test('Galaxy controls have matching translations and preserve literal topic interpolation', () => {
  assert.deepEqual(Object.keys(galaxyDictionaries.en).sort(), Object.keys(galaxyDictionaries['zh-CN']).sort());
  const fields = text => [...text.matchAll(/\{(\w+)\}/g)].map(match => match[1]).sort();
  for (const [key, message] of Object.entries(galaxyDictionaries.en)) {
    assert.ok(galaxyDictionaries['zh-CN'][key].trim());
    assert.deepEqual(fields(message), fields(galaxyDictionaries['zh-CN'][key]));
  }
  assert.ok(galaxyText('zh-CN', 'selectedAnnouncement', {topic: 'Literal <A&B>'}).includes('Literal <A&B>'));
  assert.equal(galaxyText('unknown', 'search'), galaxyDictionaries.en.search);
});
