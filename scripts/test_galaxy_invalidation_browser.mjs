// Real extension windows, temporary profile and a fictional loopback layout service.
const {chromium}=await import(process.env.OTHERWISE_PLAYWRIGHT_MODULE || 'playwright');
import {createServer} from 'node:http';
import {mkdtemp,cp,readFile,writeFile,rm} from 'node:fs/promises';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {tmpdir} from 'node:os';
import assert from 'node:assert/strict';

const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const temporary=await mkdtemp(resolve(tmpdir(),'otherwise-galaxy-invalidation-'));
const extension=resolve(temporary,'extension');
await cp(resolve(root,'dist/otherwise-extension'),extension,{recursive:true});
const manifest=JSON.parse(await readFile(resolve(extension,'manifest.json')));
manifest.host_permissions=['http://127.0.0.1/*'];
await writeFile(resolve(extension,'manifest.json'),JSON.stringify(manifest));
const layout=JSON.parse(await readFile(resolve(extension,'galaxy-layout.json')));
const {catalog_sha256,model,embedding}=layout.metadata;
let ready=false,cacheKey='d'.repeat(64),parameters,context;
const requests=[],errors=[],checks=[];
const server=createServer(async(request,response)=>{
 requests.push(request.method);
 if(request.method==='POST'){
  let body='';for await(const chunk of request)body+=chunk;
  parameters=JSON.parse(body).parameters;
 }
 response.setHeader('Content-Type','application/json');
 response.end(JSON.stringify(ready?{job_id:'shared-job',status:'ready',stage:'ready',result:{
  schema_version:1,cache_key:cacheKey,catalog_sha256,model,embedding,parameters,
  topics:layout.topics.map(({id,x,y})=>({id,x:x+.01,y:y+.01})),domains:layout.domains,
 }}:{job_id:'shared-job',status:'queued',stage:'queued'}));
});
try{
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const endpoint=`http://127.0.0.1:${server.address().port}`;
 context=await chromium.launchPersistentContext(resolve(temporary,'profile'),{
  executablePath:process.env.OTHERWISE_CHROMIUM || chromium.executablePath(),headless:true,
  ignoreDefaultArgs:['--disable-extensions'],viewport:{width:1100,height:850},
  args:[`--disable-extensions-except=${extension}`,`--load-extension=${extension}`],
 });
 const worker=context.serviceWorkers()[0] || await context.waitForEvent('serviceworker');
 const base=worker.url().replace('background.js','');
 const settings=await context.newPage();settings.on('pageerror',error=>errors.push(error.message));
 await settings.goto(base+'sidepanel.html?view=settings');await settings.locator('#settings-form').waitFor();
 await settings.evaluate(endpoint=>chrome.runtime.sendMessage({type:'ACTION',action:{type:'SET_SETTINGS',patch:{endpoint}}}),endpoint);
 const dashboard=await context.newPage();dashboard.on('pageerror',error=>errors.push(error.message));
 await dashboard.goto(base+'dashboard.html?view=map');await dashboard.locator('.galaxy-root').waitFor();
 await dashboard.locator('[data-galaxy-action="layout"]').click();
 const backup=await settings.evaluate(async()=>{
  const {createBackup}=await import('./core/backup.js');
  const {state}=await chrome.runtime.sendMessage({type:'GET_STATE'});return createBackup(state);
 });
 for(const [index,mode] of ['merge','replace','clear'].entries()){
  ready=false;cacheKey=['d','e','f'][index].repeat(64);
  const beforeKey=await dashboard.locator('.galaxy-root').getAttribute('data-layout-cache-key');
  const beforePolls=requests.filter(method=>method==='GET').length;
  await dashboard.locator('[data-layout-action="generate"]').click();
  await dashboard.waitForFunction(()=>document.querySelector('.galaxy-root')?.dataset.layoutStatus==='queued');
  ready=true;
  const restored=await settings.evaluate(({backup,mode})=>chrome.runtime.sendMessage(mode==='clear'
   ?{type:'ACTION',action:{type:'CLEAR_DERIVED'}}:{type:'IMPORT_BACKUP',backup,mode}),{backup,mode});
  assert.equal(restored.error,undefined);
  // Wait past the actual three-second poll interval to catch uncancelled timers.
  await new Promise(resolve=>setTimeout(resolve,3300));
  assert.equal(await dashboard.locator('.galaxy-root').getAttribute('data-layout-status'),'idle');
  assert.equal(requests.filter(method=>method==='GET').length,beforePolls);
  assert.equal(await dashboard.locator('.galaxy-root').getAttribute('data-layout-cache-key'),beforeKey);
  await dashboard.locator('[data-layout-action="generate"]').click();
  await dashboard.waitForFunction(cacheKey=>document.querySelector('.galaxy-root')?.dataset.layoutCacheKey===cacheKey,cacheKey);
  checks.push(`${mode}: another window cancels old polling; fresh preview can reuse the same backend job`);
 }
 assert.deepEqual(errors,[]);console.log(JSON.stringify({passed:true,checks},null,2));
}finally{
 await context?.close();server.closeAllConnections();await new Promise(resolve=>server.close(resolve));
 await rm(temporary,{recursive:true,force:true});
}
