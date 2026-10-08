// Real extension windows, isolated profile, loopback fixture service; no user data.
import {createServer} from 'node:http';
import {mkdtemp,mkdir,rm,writeFile,cp,readFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import assert from 'node:assert/strict';
const {chromium}=await import(process.env.OTHERWISE_PLAYWRIGHT_MODULE || 'playwright');
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const output=resolve(root,'.cache/qa/discovery');await mkdir(output,{recursive:true});
const profile=await mkdtemp(resolve(tmpdir(),'otherwise-discovery-browser-'));
const extension=await mkdtemp(resolve(tmpdir(),'otherwise-discovery-extension-'));
await cp(resolve(root,'dist/otherwise-extension'),extension,{recursive:true});
const manifest=JSON.parse(await readFile(resolve(extension,'manifest.json')));manifest.host_permissions=['http://127.0.0.1/*'];await writeFile(resolve(extension,'manifest.json'),JSON.stringify(manifest));
const records=[],errors=[],checks=[];let context,fail=false;
const openSection=async(page,key)=>{const node=page.locator(`[data-disclosure="${key}"]`);if(await node.getAttribute('open')===null)await node.locator(':scope > summary').click();};
const setLanguage=async(page,value)=>{await page.locator('[data-focus="nav-settings"]').click();await page.locator('#settings-language').selectOption(value);await page.waitForFunction(value=>document.documentElement.lang===value,value);await page.locator('[data-view="discover"]').click();};
async function until(check,ms=12000){const start=Date.now();while(!await check()){if(Date.now()-start>ms)throw new Error('State did not reach expected condition');await new Promise(r=>setTimeout(r,50));}}
const fixtures=['Pollinator garden','Soil microbiology','Companion planting'].map((topic,i)=>({id:topic,topic,domain:'Biology & nature',description:'Fictional public concept used for interface testing.',nearest_interest:'Gardening',distance:.32,boundary_offset:.04,zone:'New territory',discovery:{concept_id:`Q${100+i}`,area_id:'ecology',graph_path:['Ecology',topic],source_url:`https://www.wikidata.org/wiki/Q${100+i}`,level:i+1,exploration_pick:i===0,exploration_target:1,exploration_achieved:1}}));
const server=createServer(async(req,res)=>{
 let raw='';for await(const chunk of req)raw+=chunk;
 if(req.method!=='POST'||req.url!=='/api/discover'){res.writeHead(404).end();return;}
 const data=JSON.parse(raw);records.push(data);
 assert.equal(req.headers.authorization,'Bearer fictional-test-token');
 res.setHeader('Content-Type','application/json');
 if(fail){res.writeHead(503).end('{}');return;}
 const ratings=new Map(data.feedback.map(r=>[r.concept_id,r]));
 const rows=fixtures.filter(r=>!ratings.get(r.discovery.concept_id)?.known).sort((a,b)=>Number(ratings.get(b.discovery.concept_id)?.curious||false)-Number(ratings.get(a.discovery.concept_id)?.curious||false));
 res.end(JSON.stringify({recommendations:rows,seed:data.seed,graph_sha256:'a'.repeat(64)}));
});
try{
 await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const endpoint=`http://127.0.0.1:${server.address().port}`;
 context=await chromium.launchPersistentContext(profile,{executablePath:process.env.OTHERWISE_CHROMIUM||chromium.executablePath(),headless:true,ignoreDefaultArgs:['--disable-extensions'],viewport:{width:390,height:1000},args:[`--disable-extensions-except=${extension}`,`--load-extension=${extension}`]});
 const worker=context.serviceWorkers()[0]||await context.waitForEvent('serviceworker');
 const base=worker.url().replace('background.js','');
 const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
 await page.goto(base+'sidepanel.html?view=interests');

 await page.locator('#welcome-guide').waitFor();await page.locator('[data-guide-action="skip"]').click();await page.locator('#welcome-guide').waitFor({state:'detached'});
 assert.equal(records.length,0);checks.push('first-run guide can be skipped without requests');
 await page.locator('#manual-interest').waitFor({timeout:5000});
 await page.locator('#manual-interest').fill('Gardening');await page.locator('#manual-form button').click();
 await until(async()=>await page.evaluate(async()=> (await chrome.storage.local.get('state')).state.approved.length===1));
 await page.locator('[data-focus="nav-settings"]').click();await openSection(page,'settings-connection');await page.locator('#endpoint').fill(endpoint);await page.locator('#access-token').fill('fictional-test-token');await page.locator('#settings-form [type="submit"]').click();
 try{await until(async()=>await page.evaluate(async endpoint=>{const s=(await chrome.storage.local.get('state')).state;return s.settings.endpoint===endpoint && s.settings.accessToken==='fictional-test-token';},endpoint));}
 catch(error){console.log('Settings failed:',await page.locator('body').innerText());throw error;}
 await page.locator('[data-view="discover"]').click();await openSection(page,'discovery-adjust');await page.locator('#recommendation-kind').selectOption('specific');
 await until(async()=>await page.evaluate(async()=> (await chrome.storage.local.get('state')).state.settings.recommendationKind==='specific'));
 await page.locator('[data-action="recommend"]').click();
 try{await page.locator('.topic-detail').filter({hasText:'Pollinator garden'}).waitFor({timeout:5000});}
 catch(error){console.log(JSON.stringify({body:await page.locator('body').innerText(),records,errors},null,2));throw error;}
 assert.equal(records.length,1);assert.deepEqual(records[0].keywords,['Gardening']);assert.deepEqual(records[0].feedback,[]);
 const state=()=>page.evaluate(async()=> (await chrome.storage.local.get('state')).state);
 const before=await state();
 assert.equal(await page.locator('.topic-detail .graph-feedback').count(),0);
 assert.equal(await page.locator('.topic-detail [name="curious"], .topic-detail [name="known"], .topic-detail [name="difficulty"], .topic-detail [type="submit"]').count(),0);
 checks.push('topic details omit the entire feedback form and its controls');
 const rating=action=>page.evaluate(async action=>chrome.runtime.sendMessage({type:'ACTION',action}),action);
 // Exercise compatibility with existing explicit ratings via the controller,
 // without introducing replacement feedback-entry controls.
 await rating({type:'SET_DISCOVERY_FEEDBACK',conceptId:'Q100',curious:true,known:true,difficulty:'too_hard'});
 await until(async()=>await page.evaluate(async()=> (await chrome.storage.local.get('state')).state.discovery.feedback.Q100?.known===true));
 await until(async()=>!await page.locator('.topic-detail').filter({hasText:'Pollinator garden'}).count());
 assert.deepEqual((await state()).approved,before.approved);assert.equal(records[1].seed,records[0].seed);assert.deepEqual(records[1].exposures,records[0].exposures);
 checks.push('explicit curiosity/known/difficulty feedback persists, hides known concepts and reranks the same seed without approving interests');
 const dashboard=await context.newPage();dashboard.on('pageerror',e=>errors.push(e.message));await dashboard.goto(base+'dashboard.html?view=discover');
 assert.equal(await dashboard.locator('#recommendation-kind').inputValue(),'specific');
 await dashboard.locator('[data-action="undo-feedback"]').click();await page.locator('.topic-detail').filter({hasText:'Pollinator garden'}).waitFor();
 await until(async()=>Object.keys((await state()).discovery.feedback).length===0);assert.deepEqual((await state()).discovery.feedback,{});
 checks.push('sidebar and dashboard synchronize feedback; undo survives a new window');
 await setLanguage(page,'zh-CN');await page.locator('.topic-source > summary').click();
 await page.waitForFunction(()=>document.documentElement.lang==='zh-CN');
 assert.equal(await page.locator('.topic-detail .graph-feedback').count(),0);assert.match(await page.locator('.graph-path').first().innerText(),/Ecology/);
 fail=true;await rating({type:'SET_DISCOVERY_FEEDBACK',conceptId:'Q101',curious:true,known:false,difficulty:'none'});await page.locator('.error-banner').waitFor();
 assert.equal((await state()).discovery.feedback.Q101.curious,true);assert.equal((await state()).recommendations.length,0);
 fail=false;await page.locator('[data-action="recommend"]').click();await page.locator('.topic-detail').first().waitFor();
 checks.push('language changes preserve source text and keep card feedback absent; service failures keep saved ratings and recover on refresh');
 for(const width of [1440,390,320]){
  await page.setViewportSize({width,height:1000});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth),width);
  await page.screenshot({path:resolve(output,`specific-${width}.png`),fullPage:true});
 }
 checks.push('specific controls, source paths and simplified topic details fit desktop, 390px and 320px');
 await page.locator('[data-action="recommendation-view"][data-value="single"]').click();await page.locator('.single-discovery').waitFor();assert.equal(await page.locator('.topic-detail .graph-feedback').count(),0);await page.screenshot({path:resolve(output,'specific-list-320.png'),fullPage:true});
 checks.push('one-at-a-time view also omits all card feedback content');
 await page.reload();await page.locator('[data-action="undo-feedback"]').waitFor();assert.equal((await state()).discovery.feedback.Q101.curious,true);
 await openSection(page,'discovery-adjust');await page.locator('#recommendation-kind').selectOption('broad');await until(async()=>(await state()).settings.recommendationKind==='broad');assert.ok((await state()).discovery.feedback.Q101);
 await page.locator('[data-view="map"]').click();await page.locator('.galaxy-canvas').waitFor();await page.locator('[data-map-view="focus"]').click();await page.locator('.focus-root').waitFor();
 checks.push('saved feedback survives reload and broad-mode switching; Galaxy and Focus remain available');
 await page.locator('[data-view="discover"]').click();await openSection(page,'discovery-adjust');await page.locator('#recommendation-kind').selectOption('specific');await until(async()=>(await state()).settings.recommendationKind==='specific');await page.locator('#discovery-feedback-panel').evaluate(n=>n.open=true);
 await page.locator('[data-action="clear-feedback"]').click();await page.locator('dialog [data-choice="confirm"]').click();
 await until(async()=>!Object.keys((await state()).discovery.feedback).length && !Object.keys((await state()).discovery.exposures).length);assert.deepEqual((await state()).discovery.feedback,{});assert.deepEqual((await state()).discovery.exposures,{});assert.deepEqual((await state()).approved,before.approved);
 await page.locator('[data-action="recommend"]').click();await until(async()=>(await state()).recommendations.some(topic=>topic.topic==='Companion planting'));
 await dashboard.evaluate(async()=>chrome.runtime.sendMessage({type:'ACTION',action:{type:'RESET'}}));
 await until(async()=>!(await state()).approved.length);
 await page.locator('#welcome-guide').waitFor();await page.locator('[data-guide-action="skip"]').click();await page.locator('#welcome-guide').waitFor({state:'detached'});
 await dashboard.evaluate(async()=>{await chrome.runtime.sendMessage({type:'ACTION',action:{type:'ADD_INTEREST',topic:'Gardening'}});});
 await dashboard.evaluate(async endpoint=>chrome.runtime.sendMessage({type:'ACTION',action:{type:'SET_SETTINGS',patch:{endpoint,accessToken:'fictional-test-token',recommendationKind:'specific'}}}),endpoint);
 await page.locator('[data-action="recommend"]').click();await until(async()=>(await state()).recommendations.some(topic=>topic.topic==='Companion planting'));assert.equal(await page.locator('.topic-detail .graph-feedback').count(),0);assert.deepEqual((await state()).discovery.feedback,{});
 checks.push('reset in another window keeps the simplified topic details and clears existing ratings');
 assert.ok(records.every(r=>!JSON.stringify(r).includes('wikidata')&&!Object.hasOwn(r,'history')));
 assert.deepEqual(errors,[]);checks.push('clear removes feedback and exposure counts while retaining interests; requests contain no source URLs/history');
 await writeFile(resolve(output,'results.json'),JSON.stringify({checks,errors,requests:records.length},null,2));
 console.log(JSON.stringify({checks,errors,requests:records.length,output},null,2));
}finally{await context?.close();server.close();await rm(profile,{recursive:true,force:true});await rm(extension,{recursive:true,force:true});}
