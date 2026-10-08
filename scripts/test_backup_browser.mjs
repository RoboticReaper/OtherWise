// Uses a temporary Chrome profile and fictional interests only.
const {chromium} = await import(process.env.OTHERWISE_PLAYWRIGHT_MODULE || 'playwright');
import {mkdtemp,mkdir,rm,readFile,writeFile} from 'node:fs/promises';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {tmpdir} from 'node:os';
import assert from 'node:assert/strict';
const root = resolve(dirname(fileURLToPath(import.meta.url)),'..');
const output = resolve(root,'.cache/qa/backup'); await mkdir(output,{recursive:true});
const profile = await mkdtemp(resolve(tmpdir(),'otherwise-backup-'));
const extension = resolve(root,'dist/otherwise-extension');
let context;
const errors = [], outbound = [], checks = [];
try {
  context = await chromium.launchPersistentContext(profile,{
    executablePath:process.env.OTHERWISE_CHROMIUM || chromium.executablePath(),headless:true,
    ignoreDefaultArgs:['--disable-extensions'],viewport:{width:390,height:850},acceptDownloads:true,
    args:[`--disable-extensions-except=${extension}`,`--load-extension=${extension}`],
  });
  context.on('request',request=>{if (/^https?:/.test(request.url())) outbound.push(request.url());});
  const worker = context.serviceWorkers()[0] || await context.waitForEvent('serviceworker');
  const page = await context.newPage();page.on('pageerror',error=>errors.push(error.message));
  await page.goto(worker.url().replace('background.js','sidepanel.html?view=settings'));
  await page.locator('[data-focus="settings-backup"]').click();
  const action = action => page.evaluate(action=>chrome.runtime.sendMessage({type:'ACTION',action}),action);
  const state = () => page.evaluate(async()=> (await chrome.storage.local.get('state')).state);
  await action({type:'ADD_INTEREST',topic:'Gardening'});
  await action({type:'SET_SETTINGS',patch:{accessToken:'fictional-secret',language:'en'}});
  const downloadPromise = page.waitForEvent('download');
  await page.locator('[data-action="backup-export"]').click();
  const download = await downloadPromise;
  assert.match(download.suggestedFilename(),/^OtherWise-backup-.*\.json$/);
  const raw = await readFile(await download.path(),'utf8'); const backup = JSON.parse(raw);
  assert.deepEqual(backup.data.approved.map(row=>row.id),['Gardening']);
  assert.doesNotMatch(raw,/fictional-secret|accessToken|endpoint|evidence/);
  checks.push('Real JSON download includes saved interests and excludes credentials and browsing evidence');
  const choose = raw => page.locator('#backup-file').setInputFiles({name:'backup.json',mimeType:'application/json',buffer:Buffer.from(raw)});
  await action({type:'REMOVE_INTEREST',id:'Gardening'});
  await action({type:'ADD_INTEREST',topic:'Botany'});
  await choose(raw);await page.locator('.backup-dialog').waitFor();
  assert.equal(await page.locator('.backup-dialog dd').first().innerText(),'1');
  assert.equal(await page.locator('[name="backup-mode"][value="merge"]').isChecked(),true);
  await page.locator('.backup-dialog [type="submit"]').click();
  await page.locator('.backup-dialog').waitFor({state:'detached'});
  assert.deepEqual((await state()).approved.map(row=>row.id),['Botany','Gardening']);
  await choose(raw);await page.locator('.backup-dialog [type="submit"]').click();
  await page.locator('.backup-dialog').waitFor({state:'detached'});
  assert.equal((await state()).approved.length,2);
  await page.reload();await page.locator('[data-focus="settings-backup"]').click();
  assert.equal((await state()).approved.length,2);
  checks.push('Merge, duplicate import and persistence work through the production background service');
  const before = await state();
  await choose('{invalid');await page.locator('.error-banner').waitFor();
  assert.deepEqual(await state(),before);
  await choose(raw);await page.locator('[name="backup-mode"][value="replace"]').check();
  assert.equal(await page.locator('.backup-dialog [type="submit"]').isDisabled(),true);
  await page.locator('[data-backup-cancel]').click();
  assert.deepEqual(await state(),before);
  checks.push('Invalid files and cancelled replacement leave persisted state unchanged');
  backup.data.preferences.language = 'zh-CN';
  await choose(JSON.stringify(backup));await page.locator('[name="backup-mode"][value="replace"]').check();
  await page.locator('#backup-ack').check();
  await page.locator('.backup-dialog [type="submit"]').click();
  await page.locator('.backup-dialog').waitFor({state:'detached'});
  assert.deepEqual((await state()).approved.map(row=>row.id),['Gardening']);
  assert.equal((await state()).settings.accessToken,'fictional-secret');
  assert.equal((await state()).settings.language,'zh-CN');
  assert.equal(await page.evaluate(()=>chrome.permissions.contains({permissions:['history']})),false);
  assert.equal((await state()).settings.browsingEnabled,false);
  checks.push('Confirmed replacement restores preferences, keeps local credentials and requests no browsing permission');
  await choose(raw);await page.locator('.backup-dialog').waitFor();
  for (const width of [390,320,1100]) {
    await page.setViewportSize({width,height:850});
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth),width);
    assert.equal(await page.locator('.backup-dialog').evaluate(el=>el.scrollWidth <= el.clientWidth),true);
    await page.screenshot({path:resolve(output,`${width}-review-zh.png`)});
  }
  await page.keyboard.press('Escape');
  assert.equal(await page.locator('[data-action="backup-import"]').evaluate(el=>el===document.activeElement),true);
  await page.setViewportSize({width:390,height:850});
  const connection = page.locator('[data-disclosure="settings-connection"]');
  await connection.locator(':scope > summary').click();
  await page.locator('#endpoint').fill('http://127.0.0.1:8765');
  assert.equal(await page.locator('[data-action="backup-import"]').isDisabled(),true);
  checks.push('Chinese dialog fits 320/390/1100px, Escape restores keyboard focus, and unsaved settings block import');
  assert.deepEqual(errors,[]);assert.deepEqual(outbound,[]);
  await writeFile(resolve(output,'results.json'),JSON.stringify({passed:true,checks},null,2));
  console.log(JSON.stringify({passed:true,checks},null,2));
} finally {
  if (context) await context.close();
  await rm(profile,{recursive:true,force:true});
}
