// Optional integration check: npm install --no-save playwright && npx playwright install chromium
const {chromium}=await import(process.env.OTHERWISE_PLAYWRIGHT_MODULE || 'playwright');
import {mkdtemp,cp,readFile,writeFile,mkdir} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {resolve,dirname} from 'node:path';
import {spawn} from 'node:child_process';
import {randomBytes} from 'node:crypto';
import {createServer} from 'node:net';
import assert from 'node:assert/strict';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
await mkdir(`${root}/.cache/qa`,{recursive:true});
const port=await new Promise(resolve=>{const server=createServer();server.listen(0,'127.0.0.1',()=>{const port=server.address().port;server.close(()=>resolve(port));});});
const endpoint=`http://127.0.0.1:${port}`;
const token=randomBytes(24).toString('hex');
const api=spawn(`${root}/.venv/bin/python`,['-m','uvicorn','main:app','--host','127.0.0.1','--port',String(port),'--workers','1','--no-access-log'],{cwd:root,env:{...process.env,OTHERWISE_API_TOKEN:token,HF_HUB_OFFLINE:'1'},stdio:'ignore'});
let context;
try{
 for(let attempt=0;;attempt++){
   if(api.exitCode!==null || attempt>=120)throw new Error('The real API failed to become ready; install dependencies and cache MPNet first.');
   try{if((await fetch(`${endpoint}/health`)).ok)break;}catch{}
   await new Promise(resolve=>setTimeout(resolve,1000));
 }
const testExt=await mkdtemp('/tmp/otherwise-test-extension-');
await cp(`${root}/dist/otherwise-extension`,testExt,{recursive:true});
const manifest=JSON.parse(await readFile(`${testExt}/manifest.json`));
manifest.permissions.push('history');manifest.optional_permissions=[];
manifest.host_permissions=['http://127.0.0.1/*'];
await writeFile(`${testExt}/manifest.json`,JSON.stringify(manifest));
const profile=await mkdtemp('/tmp/otherwise-runtime-profile-');
context=await chromium.launchPersistentContext(profile,{executablePath:process.env.OTHERWISE_CHROMIUM || chromium.executablePath(),headless:true,ignoreDefaultArgs:['--disable-extensions'],viewport:{width:390,height:850},args:[`--disable-extensions-except=${testExt}`,`--load-extension=${testExt}`]});
const errors=[],requests=[],focusRequests=[],focusStatuses=[],discoveryRequests=[];
context.on('response',r=>{if(r.url().endsWith('/api/focus'))focusStatuses.push(r.status());});
context.on('request',r=>{if(r.url().endsWith('/api/discover'))discoveryRequests.push(JSON.parse(r.postData()));if(r.url().endsWith('/api/recommend'))requests.push(JSON.parse(r.postData()));if(r.url().endsWith('/api/focus'))focusRequests.push({body:JSON.parse(r.postData()),headers:r.headers()});});
await context.route('https://**/*',r=>r.fulfill({contentType:'text/html',body:`<!doctype html><title>${new URL(r.request().url()).searchParams.get('title')||'Synthetic search fixture'}</title><p>Isolated browser test fixture.</p>`}));
let page;
const get=()=>page.evaluate(async()=> (await chrome.storage.local.get('state')).state);
async function until(fn,ms=12000){const start=Date.now();for(;;){if(await fn())return;if(Date.now()-start>ms)throw new Error('State did not reach expected condition');await new Promise(r=>setTimeout(r,100));}}
async function visit(title,path=title){const p=await context.newPage();await p.goto(`https://example.org/${encodeURIComponent(path)}?title=${encodeURIComponent(title)}`);await p.waitForFunction(t=>document.title===t,title);await p.close();}
 const worker=context.serviceWorkers()[0]||await context.waitForEvent('serviceworker');
 page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
 await page.goto(worker.url().replace('background.js','sidepanel.html'));
 await page.locator('#manual-interest').waitFor();
 await page.locator('#welcome-guide').waitFor();await page.locator('[data-guide-action="skip"]').click();await page.locator('#welcome-guide').waitFor({state:'detached'});
 await until(async()=>!!(await get()));
 assert.equal((await get()).settings.browsingEnabled,false);
 assert.equal((await get()).settings.autoRefresh,false);
 await visit('Gardening and Botany for beginners');
 await visit('NBA Basketball explained','basketball');
 assert.equal((await get()).candidates.length,0);
 await page.getByRole('button',{name:'Review recent browsing',exact:true}).click();
 await until(async()=> (await get()).candidates.some(t=>t.id==='Gardening'));
 let state=await get();assert.equal(state.approved.length,0);assert.equal(requests.length,0);
 assert.ok(state.evidence.length>=2);assert.ok(!JSON.stringify(state).includes('https://example.org/'));
 await page.locator('[data-candidate="Gardening"]').check();
 await page.getByRole('button',{name:'Save selected (1)',exact:true}).click();
 await until(async()=> (await get()).approved.length===1);
 assert.deepEqual((await get()).baseline,['Gardening']);
 await page.getByRole('button',{name:'Settings',exact:true}).click();
 await page.getByLabel('Service address',{exact:true}).fill(endpoint);
 await page.getByLabel('Team access code',{exact:true}).fill(token);
 await page.getByRole('button',{name:'Save settings',exact:true}).click();
 await until(async()=> (await get()).settings.endpoint===endpoint);
 await page.getByRole('button',{name:'Discover',exact:true}).click();
 await page.getByRole('button',{name:/Find ideas/}).click();
 await until(async()=> (await get()).recommendations.length>0,45000);
 assert.equal(requests.length,1);assert.deepEqual(requests[0],{keywords:['Gardening'],mode:'path',focus:'Gardening',expansion_level:0,limit:10,radius:.28,expansion:.07,overlap:.015,diversity:.2,max_overlap_fraction:.2,randomness:.03});
 assert.equal((await get()).recommendations.length,10);
 await page.screenshot({path:`${root}/.cache/qa/runtime-discover.png`,fullPage:true});
 const first=(await get()).recommendations[0];
 await page.locator('.recommendation-card').first().getByRole('button',{name:/Google/}).click();
 await until(async()=> (await get()).explored.length===1);
 state=await get();assert.equal(state.approved.length,1);assert.equal(state.focus,'Gardening');assert.equal(state.edges[0].to,first.id);
 await page.locator('.recommendation-card').first().getByRole('button',{name:'+ Save interest',exact:true}).click();
 await until(async()=> (await get()).approved.length===2);
 assert.equal((await get()).focus,first.id);
 await page.getByRole('button',{name:'Map',exact:true}).click();
 await page.locator('.galaxy-search').fill('Gardening');
 await page.locator('.galaxy-result[data-galaxy-topic="Gardening"]').click();
 await page.locator('[data-galaxy-action="enter-focus"]').click();
 await page.locator('.focus-root[data-seed-id="Gardening"]').waitFor();
 assert.equal((await get()).focus,first.id);assert.equal(focusRequests.length,0);
 const beforeFocus=await get();
 await page.locator('[data-focus-action="get-ideas"]').click();
 await until(async()=>await page.locator('.focus-candidate-list [data-focus-select]').count()>0,45000);
 assert.equal(focusRequests.length,1);assert.equal(focusRequests[0].body.topic_id,'Gardening');
 assert.equal(focusRequests[0].headers.authorization,`Bearer ${token}`);
 assert.deepEqual(Object.keys(focusRequests[0].body).sort(),['topic_id','catalog_sha256','model','embedding','limit','radius','expansion','overlap','diversity','max_overlap_fraction','randomness'].sort());
 const afterFocus=await get();for(const key of ['approved','focus','recommendations','lastUpdated','generation'])assert.deepEqual(afterFocus[key],beforeFocus[key]);
 await page.locator('[data-focus-action="back"]').click();await page.locator('[data-map-view="focus"]').click();await page.locator('[data-focus-action="get-ideas"]').click();assert.equal(focusRequests.length,1);
 await page.locator('[data-map-action="refresh"]').click();await until(async()=>focusRequests.length===2&&!(await page.locator('[data-map-action="refresh"]').isDisabled()),45000);
 const dash=await context.newPage();dash.on('pageerror',e=>errors.push(e.message));await dash.goto(worker.url().replace('background.js','dashboard.html'));
 await dash.locator('.galaxy-search').fill('Computer science');await dash.locator('.galaxy-result[data-galaxy-topic="Computer science"]').click();await dash.locator('[data-galaxy-action="enter-focus"]').click();
 const recommendPromise=page.evaluate(async()=>{const bridge=await import('./bridge.js');return bridge.recommend();});
 await Promise.all([page.locator('[data-map-action="refresh"]').click(),dash.locator('[data-focus-action="get-ideas"]').click(),recommendPromise]);
 await until(async()=>focusRequests.length===4&&focusStatuses.length===4&&!(await dash.locator('[data-focus-action="get-ideas"]').isDisabled())&&!(await page.locator('[data-map-action="refresh"]').isDisabled()),45000);
 assert.ok(focusStatuses.slice(2).every(status=>status===200||status===429),'Shared service may be busy; owners must complete independently');
 assert.equal((await get()).lastError,null);
 if(!await dash.locator('.focus-candidate-list [data-focus-select]').count()){
  await dash.locator('[data-focus-action="get-ideas"]').click();await until(async()=>await dash.locator('.focus-candidate-list [data-focus-select]').count()>0,45000);assert.equal(focusStatuses.at(-1),200);
 }
 await page.locator('[data-map-action="refresh"]').click();await until(async()=>!(await page.locator('[data-map-action="refresh"]').isDisabled()),45000);assert.equal(focusStatuses.at(-1),200);
 assert.equal(await page.locator('.focus-root').getAttribute('data-seed-id'),'Gardening');assert.equal(await dash.locator('.focus-root').getAttribute('data-seed-id'),'Computer science');
 assert.equal((await get()).lastError,null);await dash.close();
 const patch=patch=>page.evaluate(async patch=>chrome.runtime.sendMessage({type:'ACTION',action:{type:'SET_SETTINGS',patch}}),patch);
 await patch({accessToken:'invalid-synthetic-token'});await page.locator('[data-focus-action="get-ideas"]').click();await page.locator('.map-focus-guidance:not([hidden])').waitFor();
 assert.match(await page.locator('.map-focus-guidance').innerText(),/access code/);assert.equal((await get()).lastError,null);
 await patch({accessToken:token,recommendationOptions:{limit:5}});await page.locator('[data-focus-action="get-ideas"]').click();
 await until(async()=>focusRequests.at(-1)?.body.limit===5&&await page.locator('.focus-candidate-list [data-focus-select]').count()>0,45000);
 assert.ok(await page.locator('.focus-candidate-list [data-focus-select]').count()<=5);
 await patch({recommendationOptions:{limit:10}});
 assert.equal((await fetch(`${endpoint}/api/focus`,{method:'POST',headers:{'Content-Type':'application/json',Authorization:'Bearer invalid'},body:JSON.stringify(focusRequests[0].body)})).status,401);
 assert.equal((await fetch(`${endpoint}/api/focus`,{method:'POST',headers:{'Content-Type':'application/json',Authorization:`Bearer ${token}`},body:JSON.stringify({...focusRequests[0].body,model:'stale-version'})})).status,409);
 await page.screenshot({path:`${root}/.cache/qa/runtime-focus.png`,fullPage:true});
 // Existing Discover focus action still changes its saved-interest focus explicitly.
 await page.locator('[data-view="discover"]').click();await page.evaluate(()=>chrome.runtime.sendMessage({type:'ACTION',action:{type:'SET_FOCUS',id:'Gardening'}}));await until(async()=> (await get()).focus==='Gardening');
 // The specific interface calls the real cached MPNet graph service.
 await page.locator('#recommendation-kind').selectOption('specific');
 await until(async()=> (await get()).settings.recommendationKind==='specific');
 await page.locator('[data-action="recommend"]').click();
 await until(async()=> (await get()).recommendations.some(r=>r.discovery),45000);
 const graphBefore=await get(),concept=graphBefore.recommendations[0].discovery;
 assert.equal(discoveryRequests.length,1);assert.deepEqual(discoveryRequests[0].feedback,[]);
 assert.equal(await page.locator('.recommendation-card .graph-feedback').count(),0);
 assert.match(await page.locator('.graph-details a').first().getAttribute('href'),/^https:\/\/(www.wikidata.org|en.wikipedia.org)\/wiki\//);
 // Seed a pre-existing explicit rating through the trusted controller to verify
 // compatibility; cards no longer provide a feedback-entry form.
 await page.evaluate(async conceptId=>chrome.runtime.sendMessage({type:'ACTION',action:{type:'SET_DISCOVERY_FEEDBACK',conceptId,curious:false,known:true,difficulty:'none'}}),concept.concept_id);
 await until(async()=> (await get()).discovery.feedback[concept.concept_id]?.known && discoveryRequests.length===2 && (await get()).recommendations.length>0,45000);
 const graphAfter=await get();assert.deepEqual(graphAfter.approved,graphBefore.approved);
 assert.ok(!graphAfter.recommendations.some(r=>r.discovery.concept_id===concept.concept_id));
 assert.equal(discoveryRequests[1].seed,discoveryRequests[0].seed);assert.deepEqual(discoveryRequests[1].exposures,discoveryRequests[0].exposures);
 await page.screenshot({path:`${root}/.cache/qa/runtime-specific.png`,fullPage:true});
 await page.locator('[data-action="undo-feedback"]').click();
 await until(async()=> !(await get()).discovery.feedback[concept.concept_id] && (await get()).recommendations.some(r=>r.discovery.concept_id===concept.concept_id),45000);
 await page.locator('#recommendation-kind').selectOption('broad');await until(async()=> (await get()).settings.recommendationKind==='broad');
 await page.getByRole('button',{name:'Settings',exact:true}).click();
 await page.locator('#browsing-enabled').check();
 await until(async()=> (await get()).settings.browsingEnabled);
 await visit('Ecology connections','ecology-new');
 await until(async()=> (await get()).candidates.some(t=>t.id==='Ecology'));
 await page.locator('#browsing-enabled').uncheck();
 await until(async()=> !(await get()).settings.browsingEnabled);
 await visit('Urban planning possibilities','pause-urban');
 await new Promise(r=>setTimeout(r,1500));
 await page.locator('#browsing-enabled').check();
 await until(async()=> (await get()).settings.browsingEnabled);
 assert.ok(!(await get()).candidates.some(t=>t.id==='Urban planning'));
 await page.evaluate(()=>chrome.history.deleteAll());
 await until(async()=> (await get()).evidence.length===0);
 assert.equal((await get()).approved.length,2);assert.equal((await get()).explored.length,1);
  await page.getByRole('button',{name:'Reset OtherWise',exact:true}).click();
 await page.getByRole('dialog').getByRole('button',{name:'Reset OtherWise',exact:true}).click();
 await until(async()=> (await get()).approved.length===0);
 state=await get();assert.equal(state.explored.length,0);assert.equal(state.evidence.length,0);assert.equal(state.settings.browsingEnabled,false);assert.equal(state.settings.accessToken,'');
 assert.equal(errors.length,0,errors.join('\n'));
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
 console.log(JSON.stringify({passed:true,checks:['optional-defaults','local-history-import','approval-only-payload','real-model-10-topics','search-not-interest','explicit-save','temporary-map-focus','real-focus-authenticated-api','focus-cache-refresh','parallel-independent-focus-discover','focus-token-options-invalidation','focus-api-auth-version-conflict','formal-discover-focus','real-graph-api-source-feedback-rerank-undo','live-local-analysis','pause-no-backfill','history-delete-preserves-explicit','reset','no-console-errors','no-horizontal-overflow'],requests:requests.length,focusRequests:focusRequests.length,discoveryRequests:discoveryRequests.length,syntheticOnly:true,permissionPrompt:'test-only manifest pregrants; native prompt not automated'},null,2));
}finally{
 if(context)await context.close();
 if(api.exitCode===null){api.kill('SIGTERM');await Promise.race([new Promise(resolve=>api.once('exit',resolve)),new Promise(resolve=>setTimeout(resolve,5000))]);if(api.exitCode===null)api.kill('SIGKILL');}
}
