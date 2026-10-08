// Isolated Chrome profile and local API: no personal browser state is used.
const {chromium} = await import(process.env.OTHERWISE_PLAYWRIGHT_MODULE || 'playwright');
import {mkdtemp, cp, readFile, writeFile, mkdir, rm} from 'node:fs/promises';
import {spawn} from 'node:child_process';
import {createServer} from 'node:net';
import {once} from 'node:events';
import {resolve, dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {tmpdir} from 'node:os';
import assert from 'node:assert/strict';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const temporary = await mkdtemp(resolve(tmpdir(), 'otherwise-local-'));
const extension = resolve(temporary, 'extension');
const output = resolve(root, '.cache/qa/local-connection');
await mkdir(output, {recursive: true});
await cp(resolve(root, 'dist/otherwise-extension'), extension, {recursive: true});
const manifest = JSON.parse(await readFile(resolve(extension, 'manifest.json')));
// Pregrant loopback in this test profile so Chrome needs no interactive dialog.
manifest.host_permissions = ['http://127.0.0.1/*', 'http://localhost/*'];
await writeFile(resolve(extension, 'manifest.json'), JSON.stringify(manifest));
const listener = createServer();
await new Promise(resolve => listener.listen(0, '127.0.0.1', resolve));
const port = listener.address().port;
await new Promise(resolve => listener.close(resolve));
const endpoint = `http://127.0.0.1:${port}`;
let context, api;
const errors = [], requests = [];
async function startApi() {
  api = spawn(resolve(root, '.venv/bin/python'), ['-m', 'uvicorn', 'main:app', '--host', '127.0.0.1', '--port', String(port), '--workers', '1', '--no-access-log'],
    {cwd: root, env: {...process.env, OTHERWISE_LOCAL_MODE: '1', OTHERWISE_API_TOKEN: 'isolated-launcher-probe', HF_HUB_OFFLINE: '1'}, stdio: 'ignore'});
  await until(async () => {
    if (api.exitCode !== null) throw new Error('The isolated local API stopped during startup.');
    try { return (await fetch(`${endpoint}/health`)).ok; } catch { return false; }
  }, 120000);
}
async function stopApi() {
  if (api && api.exitCode === null) { const stopped = once(api, 'exit'); api.kill('SIGTERM'); await stopped; }
}
async function until(predicate, timeout = 12000) {
  const started = Date.now();
  while (!await predicate()) {
    if (Date.now() - started > timeout) throw new Error('Local connection did not reach the expected state.');
    await new Promise(resolve => setTimeout(resolve, 100));
  }
}
try {
  context = await chromium.launchPersistentContext(resolve(temporary, 'profile'), {
    executablePath: process.env.OTHERWISE_CHROMIUM || chromium.executablePath(), headless: true,
    ignoreDefaultArgs: ['--disable-extensions'], viewport: {width: 390, height: 850},
    args: [`--disable-extensions-except=${extension}`, `--load-extension=${extension}`],
  });
  context.on('request', request => { if (request.url().startsWith(endpoint + '/api/')) requests.push({url: request.url(), headers: request.headers()}); });
  const worker = context.serviceWorkers()[0] || await context.waitForEvent('serviceworker');
  const page = await context.newPage();page.on('pageerror', error => errors.push(error.message));
  await page.goto(worker.url().replace('background.js', 'sidepanel.html?view=settings'));
  await page.locator('#settings-form').waitFor();
  const patch = patch => page.evaluate(async patch => chrome.runtime.sendMessage({type: 'ACTION', action: {type: 'SET_SETTINGS', patch}}), patch);
  const get = () => page.evaluate(async () => (await chrome.storage.local.get('state')).state);
  await patch({endpoint: 'https://old-demo.example', accessToken: 'stale-test-code'});
  const connection = page.locator('[data-disclosure="settings-connection"]');
  await connection.locator(':scope > summary').click();
  assert.equal(await page.getByRole('button', {name: 'Connect local service', exact: true}).count(), 1);
  await page.locator('[data-disclosure="settings-exclusions"] > summary').click();
  await page.locator('#blocked-domains').fill('draft.example');
  await page.getByRole('button', {name: 'Connect local service', exact: true}).click();
  await until(async () => (await get()).settings.endpoint === 'http://127.0.0.1:8000' && (await get()).settings.accessToken === '');
  assert.equal(await page.locator('#endpoint').inputValue(), 'http://127.0.0.1:8000');
  assert.equal(await page.locator('#access-token').inputValue(), '');
  assert.equal(await page.locator('#blocked-domains').inputValue(), 'draft.example', 'Other settings drafts survive the shortcut');
  assert.ok(!(await get()).settings.blockedDomains.includes('draft.example'), 'Shortcut saves only the connection');
  await page.reload();await page.locator('#settings-form').waitFor();
  assert.equal((await get()).settings.endpoint, 'http://127.0.0.1:8000');
  await page.locator('#settings-language').selectOption('zh-CN');
  await page.locator('[data-disclosure="settings-connection"] > summary').click();
  assert.equal(await page.getByRole('button', {name: '连接本机服务', exact: true}).count(), 1);
  await page.screenshot({path: resolve(output, 'local-settings-390.png'), fullPage: true});
  await page.locator('#settings-language').selectOption('en');
  await patch({endpoint}); // Isolate this run from any service already using 8000.
  await page.evaluate(() => chrome.runtime.sendMessage({type: 'ACTION', action: {type: 'ADD_INTEREST', topic: 'Gardening'}}));
  await startApi();
  const recommend = kind => page.evaluate(async kind => {
    const bridge = await import('./bridge.js');
    await bridge.dispatch({type: 'SET_SETTINGS', patch: {recommendationKind: kind}});
    return bridge.recommend();
  }, kind);
  for (const kind of ['broad', 'specific']) {
    const state = await recommend(kind);assert.equal(state.lastError, null);assert.ok(state.recommendations.length > 0);
  }
  const focus = await page.evaluate(async () => (await import('./bridge.js')).requestFocus('Gardening', {requestId: 'local-focus'}));
  assert.equal(focus.seed_id, 'Gardening');assert.ok(focus.recommendations.length > 0);
  // Authentication reaches layout validation and polling without starting a costly map computation.
  const layoutStatuses = await page.evaluate(async endpoint => Promise.all([
    fetch(`${endpoint}/api/galaxy-layout`, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: '{}'}).then(response => response.status),
    fetch(`${endpoint}/api/galaxy-layout/missing`).then(response => response.status),
  ]), endpoint);
  assert.deepEqual(layoutStatuses, [422, 404]);
  await stopApi();await startApi();
  await page.reload();await page.locator('#settings-form').waitFor();
  assert.equal((await get()).settings.accessToken, '');
  const afterRestart = await recommend('broad');assert.equal(afterRestart.lastError, null);assert.ok(afterRestart.recommendations.length > 0);
  assert.ok(requests.some(request => request.url.endsWith('/api/recommend')));
  assert.ok(requests.some(request => request.url.endsWith('/api/discover')));
  assert.ok(requests.some(request => request.url.endsWith('/api/focus')));
  assert.ok(requests.every(request => !request.headers.authorization), 'Local features send no access code');
  assert.deepEqual(errors, []);
  console.log('Local shortcut, saved drafts, bilingual UI, real Discover/Focus, layout authentication and API restart passed.');
} finally {
  await context?.close();await stopApi();await rm(temporary, {recursive: true, force: true});
}
