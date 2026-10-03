// Real packaged application, isolated profile and synthetic personal state.
const {chromium}=await import(process.env.OTHERWISE_PLAYWRIGHT_MODULE||'playwright');
import {mkdtemp,mkdir,rm,writeFile} from 'node:fs/promises';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import assert from 'node:assert/strict';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),profile=await mkdtemp('/tmp/otherwise-map-workspace-');
const output=resolve(root,'.cache/qa/map-workspace');await mkdir(output,{recursive:true});
let context;const errors=[],outbound=[],checks=[];
try{
 context=await chromium.launchPersistentContext(profile,{executablePath:process.env.OTHERWISE_CHROMIUM||chromium.executablePath(),headless:true,ignoreDefaultArgs:['--disable-extensions'],viewport:{width:1440,height:1000},args:[`--disable-extensions-except=${root}/dist/otherwise-extension`,`--load-extension=${root}/dist/otherwise-extension`]});
 context.on('request',r=>{if(/^https?:/.test(r.url()))outbound.push(r.url());});
 context.on('page',p=>p.on('pageerror',e=>errors.push(e.message)));
 const worker=context.serviceWorkers()[0]||await context.waitForEvent('serviceworker'),base=worker.url().replace('background.js','');
 const page=await context.newPage();await page.goto(base+'dashboard.html');await page.locator('.galaxy-canvas').waitFor();
 await page.locator('[data-map-view="focus"]').click({timeout:3000});await page.locator('.focus-search').waitFor();
 assert.equal(await page.locator('.galaxy-page > .view-heading').isVisible(),false,'Focus should reclaim the redundant Galaxy hero space');
 assert.equal(await page.locator('.focus-root').getAttribute('data-seed-id'),'');
 await page.locator('.focus-search').fill('Gardening');await page.locator('[data-focus-enter="Gardening"]').click();
 assert.equal(await page.locator('.focus-root').getAttribute('data-seed-id'),'Gardening');assert.equal(await page.locator('.focus-neighbor-list button').count(),10);assert.deepEqual(outbound,[]);
 const state=()=>page.evaluate(async()=>(await chrome.storage.local.get('state')).state);
 assert.equal((await state()).approved.length,0);assert.equal((await state()).focus,null);
 await page.locator('[data-focus-action="get-ideas"]').click();await page.locator('.map-focus-guidance:not([hidden])').waitFor();assert.match(await page.locator('.map-focus-guidance').innerText(),/Settings/);assert.deepEqual(outbound,[]);
 await page.locator('[data-map-action="settings"]').click();await page.locator('#endpoint').waitFor();
 await page.locator('[data-view="map"]').click();assert.equal(await page.locator('.focus-root').getAttribute('data-seed-id'),'Gardening');
 await page.locator('[data-focus-action="back"]').click();await page.locator('.galaxy-search').fill('Computer science');await page.locator('[data-galaxy-topic="Computer science"].galaxy-result').click();
 await page.locator('[data-galaxy-action="zoom-in"]').click();
 const camera=()=>page.locator('.galaxy-canvas').evaluate(c=>[c.dataset.centerX,c.dataset.centerY,c.dataset.zoom]);const before=await camera();
 await page.evaluate(()=>window.retainedGalaxy=document.querySelector('.galaxy-canvas'));
 await page.locator('[data-galaxy-action="enter-focus"]').click();await page.locator('.focus-root[data-seed-id="Computer science"]').waitFor();
 await page.locator('[data-focus-action="zoom-in"]').click();const focusZoom=await page.locator('.focus-map').getAttribute('data-zoom');
 await page.locator('#ui-language').selectOption('zh-CN');assert.equal(await page.locator('.focus-map').getAttribute('data-zoom'),focusZoom);
 await page.locator('[data-view="discover"]').click();await page.locator('[data-view="map"]').click();assert.equal(await page.locator('.focus-map').getAttribute('data-zoom'),focusZoom);
 await page.locator('[data-focus-action="back"]').click();assert.deepEqual(await camera(),before);assert.equal(await page.evaluate(()=>window.retainedGalaxy===document.querySelector('.galaxy-canvas')),true);
 await page.locator('[data-map-view="focus"]').click();assert.equal(await page.locator('.focus-root').getAttribute('data-seed-id'),'Computer science');
 const side=await context.newPage();await side.goto(base+'sidepanel.html?view=map');await side.locator('.galaxy-canvas').waitFor();assert.equal(await side.locator('.map-workspace').getAttribute('data-view'),'galaxy');
 await side.locator('.galaxy-search').fill('Gardening');await side.locator('[data-galaxy-topic="Gardening"].galaxy-result').click();await side.locator('[data-galaxy-action="enter-focus"]').click();
 assert.equal(await page.locator('.focus-root').getAttribute('data-seed-id'),'Computer science');
 await side.locator('.focus-neighbor-list button').first().click();await side.locator('[data-focus-action="save"]').click();
 await page.waitForFunction(async()=>((await chrome.storage.local.get('state')).state.approved.length)===1);
 assert.equal(await side.locator('.focus-root').getAttribute('data-seed-id'),'Gardening');assert.equal(await page.locator('.focus-root').getAttribute('data-seed-id'),'Computer science');
 checks.push('zero-upload entry, empty chooser, unconfigured guidance, retained DOM/cameras, temporary centers independent across windows and saved-interest synchronization');
 await page.locator('[data-view="settings"]').click();await page.locator('#galaxy-exploration-mode').check();await side.waitForFunction(async()=>((await chrome.storage.local.get('state')).state.settings.galaxyExplorationMode)===true);
 await page.locator('[data-view="map"]').click();
 await page.locator('.focus-search').fill('');
 for(const width of [1440,390,320]){await page.setViewportSize({width,height:1000});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth),width);await page.screenshot({path:resolve(output,`focus-${width}.png`),fullPage:true});}
 checks.push('exploration setting persists and Focus fits desktop and narrow views');
 const keyboardPage=await context.newPage();await keyboardPage.goto(base+'dashboard.html');await keyboardPage.locator('.galaxy-canvas').waitFor();
 // A rejected, unmatched double-click must not leave a stale transition origin.
 await keyboardPage.locator('.galaxy-canvas').focus();await keyboardPage.locator('.galaxy-canvas').dispatchEvent('dblclick');
 assert.equal(await keyboardPage.locator('.map-workspace').getAttribute('data-view'),'galaxy');
 await keyboardPage.locator('[data-map-view="focus"]').focus();await keyboardPage.keyboard.press('Enter');
 assert.equal(await keyboardPage.locator('[data-map-view="focus"]').evaluate(node=>document.activeElement===node),true,'A visible view-switch control keeps focus on entry');
 await keyboardPage.locator('[data-focus-action="back"]').focus();await keyboardPage.keyboard.press('Enter');
 assert.equal(await keyboardPage.locator('.galaxy-canvas').evaluate(node=>document.activeElement===node),true,'Back falls back to Galaxy canvas when no detail control initiated entry');
 await keyboardPage.locator('.galaxy-search').fill('Computer science');await keyboardPage.locator('.galaxy-result[data-galaxy-topic="Computer science"]').click();
 const explore=keyboardPage.locator('[data-galaxy-action="enter-focus"]');await explore.focus();await keyboardPage.keyboard.press('Enter');
 assert.equal(await keyboardPage.locator('.focus-root').evaluate(node=>node.contains(document.activeElement)&&document.activeElement.getClientRects().length>0),true,'Keyboard Explore must transfer focus out of the hidden Galaxy');
 await keyboardPage.locator('.focus-search').focus();await keyboardPage.evaluate(()=>chrome.runtime.sendMessage({type:'ACTION',action:{type:'SET_SETTINGS',patch:{language:'en'}}}));
 await keyboardPage.waitForFunction(()=>document.documentElement.lang==='en');
 assert.equal(await keyboardPage.locator('.focus-search').evaluate(node=>document.activeElement===node),true,'Routine state updates must not steal focus');
 await keyboardPage.locator('[data-focus-action="back"]').focus();await keyboardPage.keyboard.press('Enter');
 assert.equal(await explore.evaluate(node=>document.activeElement===node),true,'Keyboard Back restores the initiating Explore control after its DOM was refreshed');
 await keyboardPage.keyboard.press('Enter');await keyboardPage.locator('.focus-map').focus();await keyboardPage.keyboard.press('Escape');
 assert.equal(await explore.evaluate(node=>document.activeElement===node),true,'Escape restores the initiating Galaxy control');
 await keyboardPage.close();checks.push('keyboard Explore enters visible Focus controls; Back/Escape restore initiator or canvas, and routine updates preserve focus');
 const preview=await context.newPage();await preview.goto(base+'dashboard.html?preview=1');await preview.locator('.galaxy-canvas').waitFor();
 await preview.locator('[data-map-view="focus"]').click();await preview.locator('[data-focus-action="get-ideas"]').click();await preview.locator('.focus-candidate-list [data-focus-select]').first().waitFor();
 const records=await preview.evaluate(async()=> (await (await fetch('./focus-preview.v1.json')).json()).batches.find(b=>b.request.topic_id==='Gardening').envelope.recommendations);
 const candidateIds=await preview.locator('.focus-candidate-list [data-focus-select]').evaluateAll(nodes=>nodes.map(n=>n.dataset.focusSelect));assert.deepEqual(new Set(candidateIds),new Set(records.map(r=>r.id)));
 await preview.locator('.focus-candidate-list [data-focus-select]').first().click();const dismissed=await preview.locator('.focus-detail').getAttribute('data-selected-id');await preview.locator('[data-focus-action="dismiss"]').click();
 assert.equal(await preview.locator(`.focus-candidate-list [data-focus-select="${dismissed}"]`).count(),0);await preview.locator('[data-map-action="refresh"]').click();assert.equal(await preview.locator(`.focus-candidate-list [data-focus-select="${dismissed}"]`).count(),0);
 assert.equal(await preview.locator('.focus-root').getAttribute('data-seed-id'),'Gardening');
 checks.push('offline public fixture produces real candidates; dismissal remains suppressed after recorded refresh');
 // External request boundary alone is substituted; real workspace/scene/copy remain mounted.
 for(const [message,expected]of [['The Focus request took too long. Try again.','超时'],['The service and Galaxy data do not match. Update the data before trying again.','版本'],['This connection is not permitted.','授权'],['private server text','暂不可用']]){
  await preview.evaluate(async message=>{window.guidanceWorkspace?.destroy();const {createMapWorkspace}=await import('./ui/map-workspace.js');const {catalog,layout}=await(await import('./ui/galaxy-data.js')).galaxyLoader.load();const state=await(await import('./dev-preview.js')).getState();window.guidanceWorkspace=createMapWorkspace({catalog,layout,state,language:'zh-CN',requestFocus:async()=>{throw new Error(message);},onSettings:()=>{}});document.body.replaceChildren(window.guidanceWorkspace.element);},message);
  await preview.locator('[data-map-view="focus"]').click();await preview.locator('[data-focus-action="get-ideas"]').click();await preview.locator('.map-focus-guidance:not([hidden])').waitFor();assert.ok((await preview.locator('.map-focus-guidance').innerText()).includes(expected));assert.ok(!(await preview.locator('.map-focus-guidance').innerText()).includes('private server text'));assert.equal(await preview.locator('[data-map-action="settings"]').isVisible(),true);assert.equal(await preview.locator('.focus-neighbor-list button').count(),10);
 }
 checks.push('localized timeout/version/permission/unavailable guidance preserves local neighbors and Settings entry without echoing unknown text');
 assert.deepEqual(errors,[]);assert.deepEqual(outbound,[]);
 await writeFile(resolve(output,'results.json'),JSON.stringify({checks,errors,outbound},null,2));console.log(JSON.stringify({passed:true,checks},null,2));
}finally{await context?.close();await rm(profile,{recursive:true,force:true});}
