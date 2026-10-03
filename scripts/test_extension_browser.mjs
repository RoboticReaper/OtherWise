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
const errors=[],requests=[];
context.on('request',r=>{if(r.url().endsWith('/api/recommend'))requests.push(JSON.parse(r.postData()));});
await context.route('https://**/*',r=>r.fulfill({contentType:'text/html',body:`<!doctype html><title>${new URL(r.request().url()).searchParams.get('title')||'Synthetic search fixture'}</title><p>Isolated browser test fixture.</p>`}));
let page;
const get=()=>page.evaluate(async()=> (await chrome.storage.local.get('state')).state);
async function until(fn,ms=12000){const start=Date.now();for(;;){if(await fn())return;if(Date.now()-start>ms)throw new Error('State did not reach expected condition');await new Promise(r=>setTimeout(r,100));}}
async function visit(title,path=title){const p=await context.newPage();await p.goto(`https://example.org/${encodeURIComponent(path)}?title=${encodeURIComponent(title)}`);await p.waitForFunction(t=>document.title===t,title);await p.close();}
 const worker=context.serviceWorkers()[0]||await context.waitForEvent('serviceworker');
 page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
 await page.goto(worker.url().replace('background.js','sidepanel.html'));
 await page.locator('#manual-interest').waitFor();
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
 await page.getByRole('button',{name:'Explore from here',exact:true}).click();
 await until(async()=> (await get()).focus==='Gardening');
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
 console.log(JSON.stringify({passed:true,checks:['optional-defaults','local-history-import','approval-only-payload','real-model-10-topics','search-not-interest','explicit-save','switch-map-focus','live-local-analysis','pause-no-backfill','history-delete-preserves-explicit','reset','no-console-errors','no-horizontal-overflow'],requests:requests.length,syntheticOnly:true,permissionPrompt:'test-only manifest pregrants; native prompt not automated'},null,2));
}finally{
 if(context)await context.close();
 if(api.exitCode===null){api.kill('SIGTERM');await Promise.race([new Promise(resolve=>api.once('exit',resolve)),new Promise(resolve=>setTimeout(resolve,5000))]);if(api.exitCode===null)api.kill('SIGKILL');}
}
