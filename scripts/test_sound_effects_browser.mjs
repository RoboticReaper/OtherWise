// Real packaged extension, native audio, temporary profile and fictional saved interests.
import assert from 'node:assert/strict';
import {mkdtemp, rm, mkdir, writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {resolve, dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
const {chromium} = await import(process.env.OTHERWISE_PLAYWRIGHT_MODULE || 'playwright');
const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const output = resolve(root, '.cache/qa/sound-effects');
const extension = resolve(root, 'dist/otherwise-extension');
const profile = await mkdtemp(resolve(tmpdir(), 'otherwise-sounds-'));
const errors = [], outbound = [], checks = [];
let context;
try {
  context = await chromium.launchPersistentContext(profile, {
    executablePath: process.env.OTHERWISE_CHROMIUM || chromium.executablePath(),
    headless: true, ignoreDefaultArgs: ['--disable-extensions'], viewport: {width: 1280, height: 1000},
    args: [`--disable-extensions-except=${extension}`, `--load-extension=${extension}`],
  });
  context.on('request', request => {if (/^https?:/.test(request.url())) outbound.push(request.url());});
  await context.addInitScript(() => {
    window.soundCalls = []; window.soundPlaying = []; window.soundMedia = [];
    const original = HTMLMediaElement.prototype.play;
    HTMLMediaElement.prototype.play = function () {
      window.soundCalls.push({src: this.src, volume: this.volume});
      window.soundMedia.push(this);
      this.addEventListener('playing', () => window.soundPlaying.push(this.src), {once: true});
      return original.call(this);
    };
  });
  const worker = context.serviceWorkers()[0] || await context.waitForEvent('serviceworker');
  const base = worker.url().replace('background.js', '');
  const open = async (view, {preview = true, surface = 'dashboard'} = {}) => {
    const page = await context.newPage(); page.on('pageerror', error => errors.push(error.message));
    await page.goto(`${base}${surface}.html?${preview ? 'preview=1&' : ''}view=${view}`); await page.bringToFront();
    await page.locator('[data-focus="nav-settings"]').waitFor(); return page;
  };
  const dispatch = (page, action) => page.evaluate(async action => (await import('./dev-preview.js')).dispatch(action), action);
  const sounds = page => page.evaluate(() => window.soundCalls);
  const add = async (page, topic) => {
    await page.locator('#manual-interest').fill(topic); await page.locator('#manual-form button').click();
    await page.waitForFunction(topic => [...document.querySelectorAll('.saved-interest-row')].some(row => row.textContent.includes(topic)), topic);
  };
  const page = await open('settings');
  await page.locator('[data-disclosure="settings-sound"] > summary').click();
  assert.equal(await page.locator('#sound-effects-enabled').isChecked(), false);
  assert.equal(await page.locator('#sound-effects-volume').inputValue(), '20');
  for (const kind of ['save', 'explore', 'bloom']) {
    await page.locator(`[data-action="preview-sound"][data-sound="${kind}"]`).click();
    await page.waitForFunction(kind => window.soundPlaying.some(src => src.endsWith(`/${kind}.wav`)), kind);
  }
  assert.equal((await sounds(page)).length, 3);
  checks.push('All three packaged WAV files decode and play natively through explicit previews while automatic sounds are off');
  await page.locator('#sound-effects-enabled').check();
  await page.locator('#sound-effects-volume').evaluate(input => {
    input.value = '40'; input.dispatchEvent(new Event('input', {bubbles: true})); input.dispatchEvent(new Event('change', {bubbles: true}));
  });
  await page.waitForFunction(async () => (await import('./dev-preview.js')).getState().then(state => state.settings.soundEffectsVolume === .4));
  await page.locator('#settings-language').selectOption('zh-CN');
  assert.match(await page.locator('[data-disclosure="settings-sound"]').innerText(), /音效/);
  await page.locator('#settings-language').selectOption('en');
  await page.locator('[data-focus="nav-interests"]').click();
  await add(page, 'A saved sound fixture');
  await page.waitForFunction(() => window.soundPlaying.filter(src => src.endsWith('/save.wav')).length === 2);
  assert.equal((await sounds(page)).at(-1).volume, .4);
  await add(page, 'Another saved sound fixture');
  assert.equal((await sounds(page)).length, 4, 'Rapid saves stay quiet and previews do not start the automatic cooldown');
  await page.waitForTimeout(2_100);
  await add(page, 'A later saved sound fixture');
  await page.waitForFunction(() => window.soundPlaying.filter(src => src.endsWith('/save.wav')).length === 3);
  assert.equal((await sounds(page)).length, 5, 'A new save plays again after the short cooldown');
  checks.push('Settings localize and persist across navigation; new saves play at the chosen volume after two seconds while rapid saves stay quiet');

  const map = await open('map');
  await dispatch(map, {type: 'SET_SETTINGS', patch: {soundEffectsEnabled: true, galaxyExplorationMode: true}});
  await map.locator('.galaxy-search').waitFor();
  const select = async (target, topic) => {
    await target.locator('.galaxy-search').fill(topic);
    await target.locator('.galaxy-result-list button').filter({hasText: topic}).first().click();
    await target.locator('[data-galaxy-action="enter-focus"]').waitFor();
  };
  await select(map, 'Gardening');
  assert.equal((await sounds(map)).length, 0, 'Selecting/searching a map star is silent');
  await map.locator('[data-galaxy-action="enter-focus"]').click();
  await map.waitForFunction(() => window.soundPlaying.some(src => src.endsWith('/explore.wav')));
  assert.ok(Number(await map.locator('.focus-ripple').getAttribute('opacity')) > 0, 'The expanding ripple accompanies Explore audio');
  await map.locator('[data-focus-action="back"]').click();
  assert.equal(await map.evaluate(() => window.soundMedia.at(-1).paused), true, 'Back to Galaxy immediately stops the Explore sound');
  await map.locator('[data-galaxy-action="enter-focus"]').click();
  await map.waitForTimeout(600);
  assert.equal((await sounds(map)).length, 1, 'Rapid Focus re-entry stays quiet during the short cooldown');
  await map.locator('[data-focus-action="back"]').click();
  await map.waitForTimeout(2_100);
  await map.locator('[data-galaxy-action="enter-focus"]').click();
  await map.waitForFunction(() => window.soundPlaying.filter(src => src.endsWith('/explore.wav')).length === 2);
  assert.ok(Number(await map.locator('.focus-ripple').getAttribute('opacity')) > 0, 'Repeated entry replays the ripple alongside Explore audio');
  await mkdir(output, {recursive: true});
  await map.locator('.focus-stage').screenshot({path: resolve(output, 'repeat-entry-ripple.png')});
  await map.locator('[data-focus-action="back"]').click();
  checks.push('Entering Focus pairs the expanding ripple with Explore; the same domain replays both after two seconds while rapid re-entry and star selection stay quiet');

  const bloom = await open('map');
  await dispatch(bloom, {type: 'SET_SETTINGS', patch: {soundEffectsEnabled: true, galaxyExplorationMode: true}});
  await bloom.locator('.galaxy-search').waitFor();
  const newNeighborhood = () => bloom.evaluate(async () => {
    const {galaxyLoader} = await import('./ui/galaxy-data.js');
    const {explorationSets} = await import('./ui/exploration-logic.js');
    const {getState} = await import('./dev-preview.js');
    const {catalog, layout} = await galaxyLoader.load(), state = await getState();
    const data = {byId: new Map(layout.topics.map(topic => [topic.id, topic]))};
    const lights = explorationSets(data, state).lit;
    const point = layout.topics.find(point => !lights.has(point.id) && point.neighbors.filter(neighbor => !lights.has(neighbor.id)).length >= 5);
    return catalog.find(topic => topic.id === point.id).topic;
  });
  await select(bloom, await newNeighborhood());
  await bloom.locator('[data-galaxy-action="save"]').click();
  await bloom.waitForFunction(() => window.soundPlaying.some(src => src.endsWith('/bloom.wav')));
  assert.equal((await sounds(bloom)).length, 1, 'Bloom replaces rather than accompanies Save');
  await bloom.waitForTimeout(2_100);
  await select(bloom, await newNeighborhood());
  await bloom.locator('[data-galaxy-action="save"]').click();
  await bloom.waitForFunction(() => window.soundPlaying.filter(src => src.endsWith('/bloom.wav')).length === 2);
  assert.equal((await sounds(bloom)).length, 2, 'Bloom can repeat for another new neighborhood in the same window');
  assert.equal((await sounds(page)).length, 5);
  assert.equal((await sounds(map)).length, 2, 'Other windows never echo a save');
  checks.push('Saving each genuinely new Galaxy neighborhood plays only Bloom after two seconds; other open windows never echo the action');

  await page.bringToFront();
  await dispatch(bloom, {type: 'ADD_INTEREST', topic: 'A background update'});
  assert.equal((await sounds(bloom)).length, 2, 'Background/state-only updates stay silent');
  await page.locator('[data-focus="nav-settings"]').click();
  if (await page.locator('[data-disclosure="settings-sound"]').getAttribute('open') === null) await page.locator('[data-disclosure="settings-sound"] > summary').click();
  await page.locator('#sound-effects-enabled').uncheck();
  await page.locator('[data-focus="nav-interests"]').click();
  await add(page, 'A silent sound fixture');
  assert.equal((await sounds(page)).length, 5);
  checks.push('Muting and background updates stay silent without replay');

  const side = await open('settings', {preview: false, surface: 'sidepanel'});
  const dashboard = await open('settings', {preview: false});
  for (const target of [side, dashboard]) {
    await target.locator('[data-disclosure="settings-sound"] > summary').click();
    assert.equal(await target.locator('#sound-effects-enabled').isChecked(), false);
  }
  await side.bringToFront(); await side.locator('#sound-effects-enabled').check();
  await dashboard.waitForFunction(() => document.querySelector('#sound-effects-enabled')?.checked === true);
  await side.locator('#sound-effects-volume').evaluate(input => {
    input.value = '35'; input.dispatchEvent(new Event('input', {bubbles: true})); input.dispatchEvent(new Event('change', {bubbles: true}));
  });
  await dashboard.waitForFunction(() => document.querySelector('#sound-effects-volume')?.value === '35');
  await side.locator('[data-focus="nav-interests"]').click();
  await add(side, 'A real storage sound fixture');
  await side.waitForFunction(() => window.soundPlaying.some(src => src.endsWith('/save.wav')));
  assert.equal((await sounds(side)).at(-1).volume, .35);
  assert.equal((await sounds(dashboard)).length, 0, 'Real storage subscriptions never echo the originating window');
  await side.reload(); await side.locator('[data-focus="nav-settings"]').click();
  await side.locator('[data-disclosure="settings-sound"] > summary').click();
  assert.equal(await side.locator('#sound-effects-enabled').isChecked(), true);
  assert.equal(await side.locator('#sound-effects-volume').inputValue(), '35');
  checks.push('Real Chrome storage shares sound preferences between side panel and Dashboard, survives reload and never echoes Save in the subscribed window');

  await side.evaluate(() => {
    const original = chrome.runtime.sendMessage.bind(chrome.runtime);
    chrome.runtime.sendMessage = (message, ...args) => {
      if (message.type === 'ACTION' && message.action.type === 'ADD_INTEREST' && message.action.topic.startsWith('Deferred sound fixture')) {
        return new Promise(resolve => {window.releaseSoundSave = async () => resolve(await original(message, ...args));});
      }
      return original(message, ...args);
    };
  });
  for (const mode of ['navigation', 'blur']) {
    await side.locator('[data-focus="nav-interests"]').click();
    const topic = `Deferred sound fixture ${mode}`;
    await side.locator('#manual-interest').fill(topic); await side.locator('#manual-form button').click();
    await side.waitForFunction(() => typeof window.releaseSoundSave === 'function');
    if (mode === 'navigation') {
      await side.locator('[data-focus="nav-settings"]').click(); await side.locator('[data-focus="nav-interests"]').click();
    } else {await dashboard.bringToFront(); await side.bringToFront();}
    await side.evaluate(async () => {const release = window.releaseSoundSave; window.releaseSoundSave = null; await release();});
    await side.waitForFunction(topic => [...document.querySelectorAll('.saved-interest-row')].some(row => row.textContent.includes(topic)), topic);
    assert.equal((await sounds(side)).length, 0, 'A delayed save must not replay after leaving and returning');
  }
  checks.push('Deferred real saves remain successful but silent after page navigation or blur/refocus');

  await side.locator('[data-focus="nav-settings"]').click();
  if (await side.locator('[data-disclosure="settings-sound"]').getAttribute('open') === null) await side.locator('[data-disclosure="settings-sound"] > summary').click();
  await side.setViewportSize({width: 390, height: 850});
  await side.locator('#settings-language').selectOption('zh-CN');
  assert.equal(await side.evaluate(() => document.documentElement.scrollWidth), 390, 'Sound settings fit a narrow side panel');
  await mkdir(output, {recursive: true});
  await side.screenshot({path: resolve(output, 'settings-mobile.png'), fullPage: true});
  checks.push('Chinese sound controls and previews fit a 390px side panel without horizontal overflow');
  assert.deepEqual(errors, []); assert.deepEqual(outbound, []);
  await page.locator('[data-focus="nav-settings"]').click();
  await page.screenshot({path: resolve(output, 'settings.png'), fullPage: true});
  await writeFile(resolve(output, 'results.json'), JSON.stringify({checks, errors, outbound}, null, 2));
  console.log(JSON.stringify({checks, errors, outbound}, null, 2));
} finally {
  await context?.close(); await rm(profile, {recursive: true, force: true});
}
