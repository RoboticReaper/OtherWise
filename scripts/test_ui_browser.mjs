// Optional UI regression checks. Only temporary profiles and fictional topics are used.
const {chromium}=await import(process.env.OTHERWISE_PLAYWRIGHT_MODULE || 'playwright');
import {mkdtemp,mkdir,rm,writeFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {resolve,dirname} from 'node:path';
import {tmpdir} from 'node:os';
import assert from 'node:assert/strict';

const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const output=resolve(root,'.cache/qa/ui-preferences');await mkdir(output,{recursive:true});
const profile=await mkdtemp(resolve(tmpdir(),'otherwise-ui-'));
const extension=resolve(root,'dist/otherwise-extension');
let context;const checks=[],errors=[],outbound=[];
try{
  context=await chromium.launchPersistentContext(profile,{
    executablePath:process.env.OTHERWISE_CHROMIUM || chromium.executablePath(),
    headless:true,ignoreDefaultArgs:['--disable-extensions'],viewport:{width:390,height:850},
    args:[`--disable-extensions-except=${extension}`,`--load-extension=${extension}`],
  });
  context.on('request',request=>{if(/^https?:/.test(request.url()))outbound.push(request.url());});
  const worker=context.serviceWorkers()[0]||await context.waitForEvent('serviceworker');
  const base=worker.url().replace('background.js','sidepanel.html');
  const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
  await page.goto(base+'?preview=1');await page.locator('#ui-language').waitFor();
  const previewAction=action=>page.evaluate(async action=>{const api=await import('./dev-preview.js');return api.dispatch(action);},action);
  const getPreview=()=>page.evaluate(async()=> (await import('./dev-preview.js')).getState());
  const seed=async count=>{
    const topics=Array.from({length:count},(_,i)=>({id:`Topic ${String(i+1).padStart(3,'0')}`,topic:`Topic ${String(i+1).padStart(3,'0')}`,domain:'Fixture field',description:'An English topic description.'}));
    const seenAt=Date.now();
    await previewAction({type:'INGEST',observations:topics.map(topic=>({sourceHash:`fixture-${topic.id}`,host:'example.org',seenAt,source:'Chrome',topicIds:[topic.id],topics:[topic]}))});
  };
  const rows=page.locator('.candidate-row');
  const next=page.locator('[data-action="candidate-next"]');
  const previous=page.locator('[data-action="candidate-prev"]');
  await seed(103);
  assert.equal(await rows.count(),10);assert.equal(await previous.isDisabled(),true);
  assert.match(await page.locator('.page-status').innerText(),/1.*11/);
  await page.locator('[data-candidate="Topic 001"]').check();
  await next.click();
  await page.locator('[data-candidate="Topic 011"]').check();
  await page.locator('[data-action="select-all"]').click();
  assert.equal(await rows.locator('input:checked').count(),10);
  assert.match(await page.locator('.selection-count').innerText(),/11/);
  await previous.click();assert.equal(await page.locator('[data-candidate="Topic 001"]').isChecked(),true);
  assert.equal(await rows.locator('input:checked').count(),1);
  checks.push('103 candidates paginated; page selection does not select hidden pages');

  await page.locator('#manual-interest').fill('Gardening in Design');
  await page.locator('#manual-interest').evaluate(input=>{input.focus();input.setSelectionRange(4,9);});
  await previewAction({type:'SET_SETTINGS',patch:{language:'zh-CN'}});
  assert.equal(await page.locator('html').getAttribute('lang'),'zh-CN');
  assert.equal(await page.locator('#manual-interest').inputValue(),'Gardening in Design');
  assert.deepEqual(await page.locator('#manual-interest').evaluate(input=>[document.activeElement===input,input.selectionStart,input.selectionEnd]),[true,4,9]);
  assert.match(await page.locator('#interest-language-help').innerText(),/推荐系统不支持中文/);
  assert.match(await rows.first().innerText(),/Topic 001/);
  assert.match(await rows.first().innerText(),/Fixture field/);
  assert.match(await page.locator('.selection-count').innerText(),/11/);
  await page.locator('[data-view="settings"]').click();
  await page.locator('#endpoint').fill('https://example.org');
  await page.locator('#access-token').fill('fictional-unsaved-code');
  await page.locator('#blocked-domains').fill('example.org\nexample.net');
  await page.locator('#ui-language').selectOption('en');
  assert.equal(await page.locator('#endpoint').inputValue(),'https://example.org');
  assert.equal(await page.locator('#access-token').inputValue(),'fictional-unsaved-code');
  assert.equal(await page.locator('#blocked-domains').inputValue(),'example.org\nexample.net');
  assert.match(await page.locator('#settings-form').innerText(),/unsaved/);
  checks.push('language switching preserves selection, literal topics, input focus/caret and dirty settings');

  await page.locator('[data-view="discover"]').click();
  await page.locator('[data-action="approve"]').click();
  assert.equal((await getPreview()).approved.length,12);
  assert.equal((await getPreview()).candidates.length,92);
  assert.match(await page.locator('.selection-count').innerText(),/0/);
  await previewAction({type:'RESET'});await seed(21);
  await next.click();await next.click();assert.equal(await rows.count(),1);
  await rows.first().locator('[data-action="dismiss"]').click();
  assert.equal(await rows.count(),10);assert.equal(await next.isDisabled(),true);
  assert.match(await page.locator('.page-status').innerText(),/2.*2/);
  checks.push('cross-page save confirms the selected total; removing final page clamps safely');

  await previewAction({type:'ADD_INTEREST',topic:{id:'Gardening',topic:'Gardening',domain:'Nature',description:'Growing plants.'}});
  await page.locator('[data-action="recommend"]').click();
  const recommended=await getPreview();
  await previewAction({type:'RECOMMENDATIONS',generation:recommended.generation,items:recommended.recommendations.map((topic,index)=>index===0?{...topic,description:'How plants grow, adapt and connect with their environment. A longer English description explains plant structure, life cycles, ecosystems, and how people study the natural world.'}:topic)});
  for(const width of [390,1100]){
    await page.setViewportSize({width,height:850});
    await page.locator('#ui-language').selectOption('zh-CN');
    await page.locator('[data-action="recommendation-view"][data-value="cards"]').click();
    const cardsHeight=await page.locator('.recommendations').evaluate(element=>element.getBoundingClientRect().height);
    const count=await page.locator('.recommendation-card').count();
    await page.locator('[data-action="recommendation-view"][data-value="list"]').click();
    assert.equal(await page.locator('.recommendations.is-list').count(),1);
    assert.equal(await page.locator('.recommendation-card').count(),count);
    const listHeight=await page.locator('.recommendations').evaluate(element=>element.getBoundingClientRect().height);
    assert.ok(listHeight<cardsHeight,`${width}px list ${listHeight} must be shorter than cards ${cardsHeight}`);
    const first=page.locator('.recommendation-card').first();
    assert.match(await first.innerText(),/Botany/);
    for(const provider of ['google','youtube'])assert.equal(await first.locator(`[data-action="search"][data-provider="${provider}"]`).isVisible(),true);
    assert.equal(await first.locator('[data-action="save-topic"]').isVisible(),true);
    assert.equal(await first.locator('[data-action="dismiss"]').isVisible(),true);
    await first.locator('details summary').click();
    assert.match(await first.innerText(),/How plants grow, adapt/);
    await page.locator('#ui-language').selectOption('en');
    assert.equal(await first.locator('details').getAttribute('open')!==null,true);
    await first.locator('details summary').click();
    await page.locator('#ui-language').selectOption('zh-CN');
    assert.equal(await first.locator('details').getAttribute('open'),null,'Closing a description must survive an immediate language change');
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth),width);
    await page.locator('#recommendations-title').scrollIntoViewIfNeeded();
    await page.screenshot({path:resolve(output,`${width}-list-zh.png`)});
    await page.locator('.candidate-inbox').scrollIntoViewIfNeeded();
    await page.screenshot({path:resolve(output,`${width}-pagination-zh.png`)});
    checks.push(`${width}px list saves space and retains details/actions; Chinese layout fits`);
  }

  const actual=await context.newPage();actual.on('pageerror',e=>errors.push(e.message));
  await actual.goto(base);await actual.locator('#ui-language').waitFor();
  await actual.locator('#manual-interest').fill('Gardening');await actual.locator('#manual-form button').click();
  await actual.locator('#ui-language').selectOption('zh-CN');
  await actual.locator('[data-action="recommendation-view"][data-value="list"]').click();
  await actual.waitForFunction(async()=>{const state=(await chrome.storage.local.get('state')).state;return state.settings.language==='zh-CN' && state.settings.recommendationView==='list';});
  await actual.reload();await actual.locator('#ui-language').waitFor();
  assert.equal(await actual.locator('#ui-language').inputValue(),'zh-CN');
  assert.equal(await actual.locator('[data-action="recommendation-view"][data-value="list"]').getAttribute('aria-pressed'),'true');
  const state=await actual.evaluate(async()=> (await chrome.storage.local.get('state')).state);
  assert.deepEqual(state.approved.map(topic=>topic.topic),['Gardening']);
  assert.equal((await actual.evaluate(()=>chrome.permissions.contains({permissions:['history']}))),false);
  checks.push('production Chrome storage keeps language/list preferences after reload without history permission');
  assert.deepEqual(errors,[]);assert.deepEqual(outbound,[]);
  checks.push('no browser errors or external network requests');
  await writeFile(resolve(output,'results.json'),JSON.stringify({passed:true,checks},null,2));
  console.log(JSON.stringify({passed:true,checks},null,2));
}finally{
  if(context)await context.close();
  await rm(profile,{recursive:true,force:true});
}
