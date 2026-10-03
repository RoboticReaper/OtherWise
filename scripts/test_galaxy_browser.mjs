// Real packaged catalog, isolated extension profile, synthetic personal state only.
const {chromium} = await import(process.env.OTHERWISE_PLAYWRIGHT_MODULE || 'playwright');
import {mkdtemp, mkdir, rm, readFile, writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {resolve, dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import assert from 'node:assert/strict';
import {prepareGalaxy, worldToScreen} from '../extension/ui/galaxy-logic.js';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const extension = resolve(root, 'dist/otherwise-extension');
const output = resolve(root, '.cache/qa/galaxy');
await mkdir(output, {recursive:true});
const catalog = JSON.parse(await readFile(resolve(extension,'catalog.json')));
const layout = JSON.parse(await readFile(resolve(extension,'galaxy-layout.json')));
const data = prepareGalaxy(catalog, layout);
const profile = await mkdtemp(resolve(tmpdir(), 'otherwise-galaxy-'));
const errors = [], outbound = [], checks = [];
let context;
const pause = () => new Promise(resolve => setTimeout(resolve, 80));
async function until(fn) { for(let i=0;i<100;i++){ if(await fn())return; await pause(); } throw new Error('Expected Galaxy state did not arrive.'); }
const mapReady = page => page.waitForFunction(() => Number(document.querySelector('.galaxy-canvas')?.dataset.zoom) > 0);
const camera = page => page.locator('.galaxy-canvas').evaluate(c => ({x:Number(c.dataset.centerX),y:Number(c.dataset.centerY),zoom:Number(c.dataset.zoom)}));
const get = page => page.evaluate(async () => (await chrome.storage.local.get('state')).state);
const action = (page, value) => page.evaluate(async action => {
  const response=await chrome.runtime.sendMessage({type:'ACTION',action});
  if(response.error || !response.state)throw new Error(response.error || 'Missing state');
  return response;
}, value);
async function select(page, keyword) {
  await page.locator('.galaxy-search').fill(keyword);
  await page.locator(`.galaxy-result[data-galaxy-topic="${keyword}"]`).click();
  await until(async()=>await page.locator('.galaxy-root').getAttribute('data-selected-id')===keyword);
}
async function gestures(page, width) {
  await page.setViewportSize({width,height:1000});
  await page.locator('[data-galaxy-action="reset"]').click(); await pause();
  const canvas=page.locator('.galaxy-canvas');
  await canvas.scrollIntoViewIfNeeded();
  const start=await camera(page);
  await page.locator('[data-galaxy-action="zoom-in"]').click();
  await until(async()=> (await camera(page)).zoom>start.zoom);
  await canvas.hover();await page.mouse.wheel(0,-180);
  await until(async()=> (await camera(page)).zoom>start.zoom*1.3);
  const before=await camera(page),box=await canvas.boundingBox();
  const selected=await page.locator('.galaxy-root').getAttribute('data-selected-id');
  await page.mouse.move(box.x+box.width*.5,box.y+box.height*.45);
  await page.mouse.down();await page.mouse.move(box.x+box.width*.5+38,box.y+box.height*.45+22,{steps:5});await page.mouse.up();
  await until(async()=> (await camera(page)).x!==before.x);
  assert.equal(await page.locator('.galaxy-root').getAttribute('data-selected-id'),selected,'Drag must not select a star');
  await canvas.focus();const beforeKeyboard=await camera(page);await page.keyboard.press('ArrowRight');
  await until(async()=> (await camera(page)).x!==beforeKeyboard.x);
  await page.keyboard.press('+');await until(async()=> (await camera(page)).zoom>beforeKeyboard.zoom);
  await page.keyboard.press('Home');await until(async()=> (await camera(page)).zoom===1);
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth),width);
  assert.ok((await canvas.boundingBox()).width<=width);
  checks.push(`${width}px zoom buttons, pointer wheel, drag without selection, keyboard pan/zoom/reset, no horizontal overflow`);
}
try {
  context = await chromium.launchPersistentContext(profile, {
    executablePath:process.env.OTHERWISE_CHROMIUM || chromium.executablePath(),
    headless:true,ignoreDefaultArgs:['--disable-extensions'],viewport:{width:1440,height:1000},
    args:[`--disable-extensions-except=${extension}`,`--load-extension=${extension}`,'--proxy-server=http://127.0.0.1:9'],
  });
  context.on('page',page=>page.on('pageerror',error=>errors.push(error.message)));
  context.on('request',request=>{if(/^https?:/.test(request.url()))outbound.push(request.url());});
  await context.route('https://www.google.com/**',route=>route.fulfill({contentType:'text/html',body:'<!doctype html><title>Synthetic search result</title><p>Isolated search fixture.</p>'}));
  const worker=context.serviceWorkers()[0] || await context.waitForEvent('serviceworker');
  const base=worker.url().replace('background.js','');
  const side=await context.newPage();await side.goto(base+'sidepanel.html');await side.locator('#welcome-guide').waitFor();await side.locator('[data-guide-action="skip"]').click();await side.locator('#welcome-guide').waitFor({state:'detached'});
  await side.locator('[data-view="map"]').click();await mapReady(side);
  assert.equal(await side.locator('.galaxy-root').getAttribute('data-topic-count'),String(catalog.length));
  assert.equal((await get(side)).approved.length,0);
  assert.equal(await side.evaluate(()=>chrome.permissions.contains({permissions:['history']})),false);
  checks.push(`All ${catalog.length} real catalog topics visible before saving, without history permission`);

  const opened=context.waitForEvent('page');await side.locator('[data-action="open-dashboard"]').click();
  const dash=await opened;await dash.waitForLoadState();await mapReady(dash);
  assert.equal(new URL(dash.url()).pathname,'/dashboard.html');
  await action(side,{type:'ADD_INTEREST',topic:catalog.find(t=>t.id==='Computer science')});
  await action(side,{type:'ADD_INTEREST',topic:catalog.find(t=>t.id==='Artificial intelligence')});
  await select(dash,'psychology');
  assert.equal((await get(dash)).focus,'Artificial intelligence');
  assert.equal((await get(dash)).approved.length,2);
  const psychology=catalog.find(t=>t.id==='psychology');
  assert.equal(await dash.locator('.galaxy-description').innerText(),psychology.description);
  const expected=data.byId.get('psychology').neighbors;
  assert.deepEqual(await dash.locator('.galaxy-neighbors [data-galaxy-topic]').evaluateAll(nodes=>nodes.map(n=>n.dataset.galaxyTopic)),expected.map(n=>n.id));
  assert.deepEqual(await dash.locator('.galaxy-distance').allTextContents(),expected.map(n=>n.distance.toFixed(3)));
  const searching=context.waitForEvent('page');await dash.locator('[data-galaxy-action="google"]').click();
  const searchTab=await searching;
  await until(()=>searchTab.url().startsWith('https://www.google.com/search'));
  assert.equal(searchTab.url(),'https://www.google.com/search?q=psychology');
  await until(async()=> (await get(side)).explored.some(t=>t.id==='psychology'));
  assert.equal((await get(side)).approved.length,2);await searchTab.close();
  checks.push('Catalog-only Google search opens the canonical query and records exploration without saving; browser uses a closed loopback proxy');
  const beforeLanguage=await camera(dash);
  await dash.locator('#ui-language').selectOption('zh-CN');
  await until(async()=>await side.locator('#ui-language').inputValue()==='zh-CN');
  await mapReady(dash);assert.deepEqual(await camera(dash),beforeLanguage);
  assert.equal(await dash.locator('.galaxy-search').inputValue(),'psychology');
  assert.equal(await dash.locator('.galaxy-description').innerText(),psychology.description);
  await dash.locator('[data-galaxy-action="save"]').click();
  await until(async()=> (await get(side)).approved.length===3);
  assert.equal((await get(side)).focus,'psychology');
  checks.push('Real original descriptions/ten high-dimensional neighbors; selection is not saving; explicit save and language propagate across tabs');

  await select(dash,'Computer science');
  await dash.locator('[data-galaxy-action="enter-focus"]').click();
  await dash.locator('.focus-root[data-seed-id="Computer science"]').waitFor();
  assert.equal((await get(side)).focus,'psychology');
  await dash.locator('[data-focus-action="back"]').click();await mapReady(dash);
  // Formal Discover focus remains an explicit saved-interest action.
  await dash.locator('[data-view="discover"]').click();
  await action(dash,{type:'SET_FOCUS',id:'Computer science'});
  await dash.waitForFunction(()=>document.querySelector('.focus-note')?.textContent.includes('Computer science'));
  assert.equal((await get(side)).focus,'Computer science');
  await dash.locator('[data-view="map"]').click();await mapReady(dash);
  for(const width of [1440,390,320]) {
    await gestures(dash,width);
    await dash.locator('.galaxy-domain').selectOption(psychology.domain);await pause();
    assert.equal(await dash.locator('.galaxy-root').getAttribute('data-domain'),psychology.domain);
    assert.match(await dash.locator('.galaxy-count').innerText(),new RegExp(String(catalog.filter(t=>t.domain===psychology.domain).length)));
    await dash.locator('.galaxy-search').fill('pSyChOlOgY');
    await dash.locator('.galaxy-search').press('Enter');await pause();
    assert.equal(await dash.locator('.galaxy-detail').getAttribute('data-selected-id'),'psychology');
    assert.equal(await dash.evaluate(()=>document.documentElement.scrollWidth),width);
    assert.ok(await dash.locator('.galaxy-result-list').evaluate(e=>e.clientHeight<=240),'Search results must not push the map down without bound');
    await dash.locator('.galaxy-toolbar').scrollIntoViewIfNeeded();
    await dash.screenshot({path:resolve(output,`dashboard-${width}-zh.png`),fullPage:true});
    await dash.locator('.galaxy-neighbors [data-galaxy-topic]').first().click();await pause();
    assert.equal(await dash.locator('.galaxy-detail').getAttribute('data-selected-id'),expected[0].id);
    checks.push(`${width}px domain filter, case-insensitive search/Enter, neighbor selection and original text`);
  }

  // Actual pointer selection uses the same immutable world coordinates that were packaged.
  await dash.setViewportSize({width:1440,height:1000});
  await dash.locator('[data-galaxy-action="reset"]').click();await pause();
  const canvas=dash.locator('.galaxy-canvas');await canvas.scrollIntoViewIfNeeded();
  const box=await canvas.boundingBox(),cam=await camera(dash);
  const candidate=data.topics.map(t=>({...worldToScreen(t,cam,box,data.bounds),id:t.id})).find(t=>t.x>40&&t.x<box.width-40&&t.y>70&&t.y<box.height-100);
  await dash.mouse.click(box.x+candidate.x,box.y+candidate.y);
  await until(async()=>await dash.locator('.galaxy-root').getAttribute('data-selected-id')===candidate.id || await dash.locator('.galaxy-candidate-list button').count()>0);
  if(await dash.locator('.galaxy-root').getAttribute('data-selected-id')!==candidate.id)await dash.locator(`.galaxy-candidate-list [data-galaxy-topic="${candidate.id}"]`).click();
  await until(async()=>await dash.locator('.galaxy-root').getAttribute('data-selected-id')===candidate.id);
  assert.equal(await dash.locator('.galaxy-root').getAttribute('data-selected-id'),candidate.id);
  assert.equal((await get(dash)).approved.length,3);
  const stable=await dash.evaluate(async()=>JSON.stringify(await (await fetch('./galaxy-layout.json')).json()));
  await dash.reload();await mapReady(dash);
  assert.equal(await dash.evaluate(async()=>JSON.stringify(await (await fetch('./galaxy-layout.json')).json())),stable);
  checks.push('Pointer hits canonical topic; reload retains exact packaged coordinates and personal data');

  await action(side,{type:'ADD_INTEREST',topic:{id:'My custom hobby',topic:'My custom hobby',domain:'Personal',description:'Synthetic custom interest'}});
  await until(async()=>await dash.locator('.galaxy-custom [data-galaxy-topic="My custom hobby"]').count()===1);
  await dash.locator('.galaxy-custom [data-galaxy-topic="My custom hobby"]').click();
  assert.equal(await dash.locator('.galaxy-neighbors').count(),0);
  assert.match(await dash.locator('.galaxy-custom-note').innerText(),/目录/);
  await dash.locator('[data-galaxy-action="focus"]').click();await dash.locator('#discovery-mode').waitFor();
  assert.equal((await get(dash)).focus,'My custom hobby');
  await dash.locator('[data-view="map"]').click();await mapReady(dash);
  const customSearch=context.waitForEvent('page',{timeout:5000});await dash.locator('[data-galaxy-action="google"]').click();
  const customTab=await customSearch;await until(()=>customTab.url().startsWith('https://www.google.com/search'));
  assert.equal(new URL(customTab.url()).searchParams.get('q'),'My custom hobby');await customTab.close();
  await until(async()=>(await get(side)).explored.some(t=>t.id==='My custom hobby'));
  checks.push('Custom interest remains usable without fabricated catalog coordinates/neighbors');
  await side.setViewportSize({width:390,height:850});await mapReady(side);
  await gestures(side,390);await select(side,'psychology');
  await side.screenshot({path:resolve(output,'sidepanel-390.png'),fullPage:true});

  // Real Chromium touch events exercise the two-pointer pinch path.
  const touch=await context.newPage();await touch.setViewportSize({width:390,height:850});
  const cdp=await context.newCDPSession(touch);
  await cdp.send('Emulation.setTouchEmulationEnabled',{enabled:true,maxTouchPoints:2});
  await touch.goto(base+'dashboard.html');await mapReady(touch);
  await touch.locator('.galaxy-canvas').scrollIntoViewIfNeeded();
  const tb=await touch.locator('.galaxy-canvas').boundingBox(),cx=tb.x+tb.width/2,cy=tb.y+tb.height/2;
  await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x:cx-35,y:cy,id:1},{x:cx+35,y:cy,id:2}]});
  await cdp.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:cx-65,y:cy,id:1},{x:cx+65,y:cy,id:2}]});
  await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
  await until(async()=> (await camera(touch)).zoom>1);
  assert.equal(await touch.locator('.galaxy-root').getAttribute('data-selected-id'),'');
  checks.push('Chromium two-finger pinch zooms without accidental selection');
  // Only explicit sample mode accepts internal recommendation fixtures.
  const preview=await context.newPage();await preview.goto(base+'dashboard.html?preview=1');await mapReady(preview);
  await preview.evaluate(async topic=>{
    const api=await import('./dev-preview.js');
    await api.dispatch({type:'RECOMMENDATIONS',generation:(await api.getState()).generation,items:[topic]});
  },psychology);
  await select(preview,'psychology');
  assert.match(await preview.locator('.galaxy-statuses').innerText(),/Recommendation/);
  assert.equal((await get(dash)).approved.length,4,'Explicit preview cannot alter the real extension profile');
  checks.push('Recommendation overlay verified with an explicitly isolated preview fixture');
  assert.deepEqual(errors,[]);assert.ok(outbound.every(url=>{const parsed=new URL(url);return parsed.origin==='https://www.google.com'&&parsed.pathname==='/search'&&['psychology','My custom hobby'].includes(parsed.searchParams.get('q'))&&[...parsed.searchParams.keys()].length===1;}));
  checks.push('No page errors or API requests; external access blocked by the isolated browser proxy');
  const result={passed:true,catalogTopics:catalog.length,cacheKey:layout.cache_key,checks};
  await writeFile(resolve(output,'results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));
} catch(error) {
  if(context)for(const [index,page] of context.pages().entries()) {
    await page.screenshot({path:resolve(output,`failure-${index}.png`),fullPage:true}).catch(()=>{});
    console.error(JSON.stringify({url:page.url(),diagnostic:await page.evaluate(()=>({query:document.querySelector('.galaxy-search')?.value,results:document.querySelector('.galaxy-results')?.textContent,error:document.querySelector('.error-banner')?.textContent,mapError:document.querySelector('#galaxy-container')?.innerText?.slice(0,1000)})).catch(()=>null)}));
  }
  throw error;
} finally {
  if(context)await context.close();
  await rm(profile,{recursive:true,force:true});
}
