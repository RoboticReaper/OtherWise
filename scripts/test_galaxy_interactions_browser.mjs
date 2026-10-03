// Isolated component regression: real packaged Galaxy, synthetic personal state, no app/controller.
const {chromium} = await import(process.env.OTHERWISE_PLAYWRIGHT_MODULE || 'playwright');
import {mkdtemp, rm, readFile, mkdir} from 'node:fs/promises';
import {createServer} from 'node:http';
import {tmpdir} from 'node:os';
import {resolve, dirname, extname} from 'node:path';
import {fileURLToPath} from 'node:url';
import assert from 'node:assert/strict';
import {prepareGalaxy, worldToScreen} from '../extension/ui/galaxy-logic.js';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const packaged = resolve(root, 'dist/otherwise-extension');
const output = resolve(root, '.cache/qa/galaxy-interactions');
const catalog = ['A','B','C','D','E','F','O','P'].map(id => ({id,topic:`Topic ${id}`,domain:['B','E','F'].includes(id)?'Y':'X',description:`Original description ${id}`}));
const coords = {A:[-4,1],B:[4,1],C:[0,1],D:[-2,-1],E:[2,-1],F:[0,-3],O:[-3,3],P:[-3,3]};
const neighbors = {A:['C','D'],B:['C','E'],C:['F']};
const layout = {schema_version:1,cache_key:'isolated-fixture',metadata:{},domains:[{id:'X',x:-2,y:0},{id:'Y',x:2,y:0}],topics:catalog.map(({id})=>({id,x:coords[id][0],y:coords[id][1],neighbors:(neighbors[id]||[]).map((id,i)=>({id,distance:.1+i*.01}))}))};
const data = prepareGalaxy(catalog, layout), original = JSON.stringify(layout);
const initial = {approved:[],baseline:['A'],recommendations:[catalog[5]],explored:[],edges:[],settings:{galaxyExplorationMode:true}};
const html = `<!doctype html><meta charset="utf-8"><link rel="stylesheet" href="/ui/galaxy.css"><style>body{margin:20px;background:#0a1422;color:#eee}button,input,select{font:inherit;color:inherit;background:#142538;border:1px solid #526777;border-radius:6px}#map{max-width:1200px}button{cursor:pointer} [hidden]{display:none!important}</style><div id="map"></div><script type="module">
import {createGalaxyMap} from '/ui/galaxy.js';
window.catalog=${JSON.stringify(catalog)};window.layout=${JSON.stringify(layout)};window.state=${JSON.stringify(initial)};window.entered=[];window.saved=[];
// Observe real canvas painting, not a production-only testing API.
window.paint=[];let arc=null;
const proto=CanvasRenderingContext2D.prototype;
for(const name of ['clearRect','arc','fill','stroke']){const original=proto[name];proto[name]=function(...args){if(this.canvas.classList.contains('galaxy-canvas')){if(name==='clearRect')window.paint=[];if(name==='arc')arc=args;if((name==='fill'||name==='stroke')&&arc)window.paint.push({kind:name,x:arc[0],y:arc[1],r:arc[2],color:this[name==='fill'?'fillStyle':'strokeStyle'],alpha:this.globalAlpha});}return original.apply(this,args)}}
window.map=createGalaxyMap({container:document.querySelector('#map'),catalog,layout,state,onEnterFocus:id=>entered.push(id),onSave:topic=>saved.push(topic.id)});
window.createAdjacentMap=separation=>{const adjacent=structuredClone(layout);if(separation){adjacent.topics.find(t=>t.id==='A').x=-separation/2;adjacent.topics.find(t=>t.id==='C').x=separation/2;adjacent.topics.find(t=>t.id==='D').x=-4;}return createGalaxyMap({container:document.querySelector('#map'),catalog,layout:separation?adjacent:layout,state,onEnterFocus:id=>entered.push(id),onSave:topic=>saved.push(topic.id),viewState:{camera:{x:0,y:1,zoom:1}}});};
window.change=patch=>{state={...state,...patch};map.update({state})};
</script>`;
const server = createServer(async (request,response)=>{
  try {
    const path = new URL(request.url,'http://localhost').pathname;
    if(path==='/'){response.setHeader('content-type','text/html');response.end(html);return;}
    const file=resolve(packaged, `.${path}`);
    if(!file.startsWith(packaged+'/')){response.writeHead(403).end();return;}
    response.setHeader('content-type',extname(file)==='.js'?'text/javascript':'text/css');response.end(await readFile(path==='/ui/galaxy.js' && process.env.OTHERWISE_GALAXY_MODULE || file));
  } catch {response.writeHead(404).end();}
});
await mkdir(output,{recursive:true});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const profile=await mkdtemp(resolve(tmpdir(),'otherwise-interactions-'));
let context;const errors=[],failures=[],checks=[];
const settle=page=>page.waitForTimeout(340);
const ready=page=>page.waitForFunction(()=>Number(document.querySelector('.galaxy-canvas')?.dataset.zoom)>0);
const selected=page=>page.locator('.galaxy-detail').getAttribute('data-selected-id');
const camera=page=>page.evaluate(()=>map.getViewState().camera);
async function position(page,id){const box=await page.locator('.galaxy-canvas').boundingBox();return {...worldToScreen(data.byId.get(id),await camera(page),box,data.bounds),box};}
async function clickStar(page,id,{double=false,offset=0}={}){const p=await position(page,id);await page.mouse[double?'dblclick':'click'](p.box.x+p.x+offset,p.box.y+p.y);await settle(page);}
async function fill(page,id){const p=await position(page,id);return page.evaluate(({x,y})=>paint.find(p=>p.kind==='fill'&&Math.abs(p.x-x)<.01&&Math.abs(p.y-y)<.01),p);}
async function change(page,patch){await page.evaluate(patch=>change(patch),patch);await page.waitForTimeout(40);}
async function check(name,fn){try{await fn();checks.push(name);}catch(error){failures.push({name,message:error.message});}}
try{
  context=await chromium.launchPersistentContext(profile,{executablePath:process.env.OTHERWISE_CHROMIUM||chromium.executablePath(),headless:true,viewport:{width:1440,height:1050},args:['--proxy-server=http://127.0.0.1:9']});
  await context.route('**/*',route=>new URL(route.request().url()).hostname==='127.0.0.1'?route.continue():route.abort());
  const page=await context.newPage();page.setDefaultTimeout(1500);page.on('pageerror',error=>errors.push(error.message));
  await page.goto(`http://127.0.0.1:${server.address().port}/`);await ready(page);
  await check('initial exploration mode paints unsaved/recommended stars gray',async()=>{assert.equal((await fill(page,'F')).color,'#79838e');assert.equal((await fill(page,'A')).color,'#79838e');});
  await check('single gray click only opens details after 250ms, keeps neighbors gray',async()=>{
    const p=await position(page,'A');await page.mouse.click(p.box.x+p.x,p.box.y+p.y);assert.equal(await selected(page),null);await settle(page);assert.equal(await selected(page),'A');assert.equal((await fill(page,'C')).color,'#79838e');assert.deepEqual(await page.evaluate(()=>entered),[]);
  });
  await check('all catalog details have immediate Explore',async()=>{await page.locator('[data-galaxy-action="enter-focus"]').click();assert.deepEqual(await page.evaluate(()=>entered),['A']);});
  await check('filtered-out stars remain clickable',async()=>{await page.locator('.galaxy-domain').selectOption('Y');await page.waitForTimeout(40);await clickStar(page,'A');assert.equal(await selected(page),'A');});
  await check('saved union retains overlapping neighbors on removal and never recursively lights F',async()=>{
    await change(page,{approved:[catalog[0],catalog[1]],explored:[catalog[3]]});
    for(const id of ['A','B','C','D','E'])assert.notEqual((await fill(page,id)).color,'#79838e');assert.equal((await fill(page,'F')).color,'#79838e');
    await change(page,{approved:[catalog[1]]});assert.equal((await fill(page,'A')).color,'#79838e');assert.notEqual((await fill(page,'C')).color,'#79838e');assert.notEqual((await fill(page,'D')).color,'#79838e');
  });
  await check('toggle/language/save/remove preserve world coordinates and view camera',async()=>{
    const before=await camera(page);await change(page,{settings:{galaxyExplorationMode:false}});assert.notEqual((await fill(page,'F')).color,'#79838e');
    await change(page,{settings:{galaxyExplorationMode:true}});await page.evaluate(()=>map.update({language:'zh-CN'}));await page.waitForTimeout(40);
    assert.deepEqual(await camera(page),before);assert.equal(await page.evaluate(()=>JSON.stringify(layout)),original);
  });
  await check('actual browser doubleclick enters once without delayed selection',async()=>{
    await page.locator('[data-galaxy-action="close-details"]').click();await page.evaluate(()=>entered=[]);await clickStar(page,'B',{double:true});assert.deepEqual(await page.evaluate(()=>entered),['B']);assert.equal(await selected(page),null);
  });
  await check('native doubleclick across adjacent unique stars opens details without entering Focus',async()=>{
    // Exact 25px separation, with two unique hits only 3px apart (inside Chromium's doubleclick tolerance).
    const box=await page.locator('.galaxy-canvas').boundingBox(),separation=25/(Math.min(box.width/8,box.height/6)*.82);
    await page.evaluate(separation=>{map.destroy();entered=[];window.nativeDoubleClicks=0;window.releaseEvents=0;map=createAdjacentMap(separation);const canvas=document.querySelector('.galaxy-canvas');canvas.addEventListener('pointerup',()=>releaseEvents++);canvas.addEventListener('dblclick',()=>nativeDoubleClicks++);},separation);await ready(page);
    const adjacentBox=await page.locator('.galaxy-canvas').boundingBox(),x=adjacentBox.x+adjacentBox.width/2,y=adjacentBox.y+adjacentBox.height/2;
    const painted=await page.evaluate(()=>paint.filter(p=>p.kind==='fill'&&Math.abs(p.y-document.querySelector('.galaxy-canvas').getBoundingClientRect().height/2)<.001).map(p=>p.x).sort((a,b)=>a-b));
    assert.ok(painted.some((value,i)=>i>0&&Math.abs(value-painted[i-1]-25)<.001),'The two painted centers must be exactly 25px apart');
    await page.mouse.click(x-1.5,y);await page.mouse.move(x+1.5,y);await page.mouse.down({clickCount:2});await page.mouse.up({clickCount:2});await settle(page);
    const observed={releases:await page.evaluate(()=>releaseEvents),native:await page.evaluate(()=>nativeDoubleClicks),entered:await page.evaluate(()=>entered),selected:await selected(page)};
    await page.evaluate(()=>{map.destroy();map=createAdjacentMap();});await ready(page);
    assert.equal(observed.releases,2,'There must be exactly two actual valid release cycles');assert.equal(observed.native,1,'Chromium must produce the real native doubleclick');assert.deepEqual(observed.entered,[]);assert.equal(observed.selected,'C');
  });
  await check('24px mouse and 44px touch hit targets',async()=>{await clickStar(page,'B',{offset:11});assert.equal(await selected(page),'B');
    if(await page.locator('[data-galaxy-action="close-details"]').count())await page.locator('[data-galaxy-action="close-details"]').click();const p=await position(page,'A');const cdp=await context.newCDPSession(page);await cdp.send('Emulation.setTouchEmulationEnabled',{enabled:true,maxTouchPoints:2});
    await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x:p.box.x+p.x+21,y:p.box.y+p.y,id:1}]});await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});await settle(page);assert.equal(await selected(page),'A');await cdp.detach();
  });
  await check('overlapping stars expose a stable keyboard candidate list',async()=>{await clickStar(page,'O');assert.deepEqual(await page.locator('.galaxy-candidates [data-galaxy-topic]').evaluateAll(nodes=>nodes.map(node=>node.dataset.galaxyTopic)),['O','P']);const candidate=page.locator('.galaxy-candidates [data-galaxy-topic="P"]');await candidate.focus();await page.keyboard.press('Enter');assert.equal(await selected(page),'P');});
  await check('drag, pinch, pointercancel, and pause cancel pending selection',async()=>{
    if(await page.locator('[data-galaxy-action="close-details"]').count())await page.locator('[data-galaxy-action="close-details"]').click();const p=await position(page,'A');await page.mouse.move(p.box.x+p.x,p.box.y+p.y);await page.mouse.down();await page.mouse.move(p.box.x+p.x+30,p.box.y+p.y+20,{steps:4});await page.mouse.up();await settle(page);assert.equal(await selected(page),null);
    const cdp=await context.newCDPSession(page);await cdp.send('Emulation.setTouchEmulationEnabled',{enabled:true,maxTouchPoints:2});const box=await page.locator('.galaxy-canvas').boundingBox(),x=box.x+box.width/2,y=box.y+box.height/2;
    await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x:x-30,y,id:1},{x:x+30,y,id:2}]});await cdp.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:x-60,y,id:1},{x:x+60,y,id:2}]});await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});await settle(page);assert.equal(await selected(page),null);await cdp.detach();
    const canceled=await position(page,'B'),cancelSession=await context.newCDPSession(page);await cancelSession.send('Emulation.setTouchEmulationEnabled',{enabled:true,maxTouchPoints:2});await cancelSession.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x:canceled.box.x+canceled.x,y:canceled.box.y+canceled.y,id:1}]});await cancelSession.send('Input.dispatchTouchEvent',{type:'touchCancel',touchPoints:[]});await settle(page);assert.equal(await selected(page),null);await cancelSession.detach();
    const next=await position(page,'B');await page.mouse.click(next.box.x+next.x,next.box.y+next.y);await page.evaluate(()=>map.setActive(false));await settle(page);assert.equal(await selected(page),null);await page.evaluate(()=>map.setActive(true));
  });
  await check('only newly lit saved-interest differences receive waves; initial/toggle/language/search updates never replay',async()=>{
    await page.locator('[data-galaxy-action="reset"]').click();await page.waitForTimeout(40);
    await change(page,{approved:[],explored:[],settings:{galaxyExplorationMode:true}});await page.waitForTimeout(700);
    const rings=()=>page.evaluate(()=>paint.filter(p=>p.kind==='stroke'&&p.r>12).map(({x,y})=>({x,y})));
    assert.deepEqual(await rings(),[]);
    await change(page,{approved:[catalog[0]]});await page.waitForTimeout(150);
    const expectedA=await Promise.all(['A','C','D'].map(async id=>{const p=await position(page,id);return {x:p.x,y:p.y}}));assert.deepEqual(await rings(),expectedA);
    await page.waitForTimeout(700);await change(page,{approved:[catalog[0],catalog[1]]});await page.waitForTimeout(150);
    const expectedB=await Promise.all(['B','E'].map(async id=>{const p=await position(page,id);return {x:p.x,y:p.y}}));assert.deepEqual(await rings(),expectedB);
    await page.waitForTimeout(700);await page.evaluate(()=>map.update({language:'en'}));await change(page,{explored:[catalog[5]]});assert.deepEqual(await rings(),[]);
    await change(page,{settings:{galaxyExplorationMode:false}});await change(page,{settings:{galaxyExplorationMode:true}});assert.deepEqual(await rings(),[]);
    const pointsBefore=await Promise.all(catalog.map(async ({id})=>{const p=await fill(page,id);return {id,x:p.x,y:p.y}}));
    await change(page,{approved:[]});const pointsAfter=await Promise.all(catalog.map(async ({id})=>{const p=await fill(page,id);return {id,x:p.x,y:p.y}}));assert.deepEqual(pointsAfter,pointsBefore);
  });
  await check('explicit search selection cancels pending canvas details',async()=>{
    if(await page.locator('[data-galaxy-action="close-details"]').count())await page.locator('[data-galaxy-action="close-details"]').click();const p=await position(page,'A');await page.mouse.click(p.box.x+p.x,p.box.y+p.y);
    await page.locator('.galaxy-search').fill('Topic B');await page.locator('.galaxy-search').press('Enter');assert.equal(await selected(page),'B');await settle(page);assert.equal(await selected(page),'B');
  });
  await check('starting a new held pointer gesture cancels a pending click',async()=>{
    if(await page.locator('[data-galaxy-action="close-details"]').count())await page.locator('[data-galaxy-action="close-details"]').click();const p=await position(page,'B');await page.mouse.click(p.box.x+p.x,p.box.y+p.y);await page.mouse.down();try {await settle(page);assert.equal(await selected(page),null);} finally {await page.mouse.move(p.box.x+p.x+30,p.box.y+p.y);await page.mouse.up();}
  });
  await check('keyboard star list has an Escape return path',async()=>{
    const canvas=page.locator('.galaxy-canvas');await canvas.focus();await page.keyboard.press('Enter');assert.ok(await page.locator('.galaxy-candidates').isVisible());await page.keyboard.press('Escape');assert.equal(await page.locator('.galaxy-candidates').isVisible(),false);assert.equal(await canvas.evaluate(c=>c===document.activeElement),true);
  });
  await check('runtime reduced motion stops wave painting and active lifecycle resumes',async()=>{await page.emulateMedia({reducedMotion:'reduce'});await change(page,{approved:[catalog[0],catalog[1]]});await page.waitForTimeout(80);const strokes=await page.evaluate(()=>paint.filter(p=>p.kind==='stroke'&&p.r>12));assert.deepEqual(strokes,[]);await page.emulateMedia({reducedMotion:'no-preference'});});
  await page.screenshot({path:resolve(output,'desktop.png'),fullPage:true});
  await page.setViewportSize({width:390,height:1000});await page.waitForTimeout(80);assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth),390);await page.screenshot({path:resolve(output,'narrow.png'),fullPage:true});
  assert.deepEqual(errors,[]);console.log(JSON.stringify({checks,failures,errors},null,2));assert.deepEqual(failures,[]);
}finally{await context?.close();await new Promise(resolve=>server.close(resolve));await rm(profile,{recursive:true,force:true});}
