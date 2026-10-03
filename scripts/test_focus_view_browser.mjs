// Independent real Focus scene: public-style fixture geometry, synthetic state, no app/API.
import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {readFile,mkdir,writeFile} from 'node:fs/promises';
import {resolve,dirname,extname} from 'node:path';
import {fileURLToPath} from 'node:url';
const {chromium}=await import(process.env.OTHERWISE_PLAYWRIGHT_MODULE || 'playwright');
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const output=resolve(root,'.cache/qa/focus');
await mkdir(output,{recursive:true});
const html=`<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><link rel="stylesheet" href="/extension/ui/focus.css"><style>body{margin:0;background:#10141c;color:#eee;font:15px system-ui}#host{max-width:1300px;margin:24px auto;padding:0 16px;box-sizing:border-box}</style></head><body><div id="host"></div><script type="module">
import {createFocusView} from '/extension/ui/focus.js';
import {projectFocus} from '/extension/ui/focus-logic.js';
const topics=Array.from({length:45},(_,i)=>({id:i===0?'Center':'Topic '+i,topic:i===0?'Center':'Topic '+i,description:'Original catalog description '+i+'.',domain:i%2?'Science':'Arts',x:i===0?0:Math.cos(i*.8)*100,y:i===0?0:Math.sin(i*.8)*100,neighbors:[]}));
topics[0].neighbors=topics.slice(1,11).map((t,i)=>({id:t.id,distance:.06+i*.017}));
topics[1].neighbors=[{id:'Center',distance:.06}];
topics[12].x=topics[11].x;topics[12].y=topics[11].y;
window.data={topics,byId:new Map(topics.map(t=>[t.id,t])),domains:[{id:'Arts'},{id:'Science'}]};
window.events=[];window.personal={approved:[],explored:[]};
window.recs=topics.slice(11,43).map((t,i)=>({id:t.id,distance:i<2?.3:.304+i*.001}));
window.local={...projectFocus(data,'Center'),status:'local',requestKey:null};
window.ready={...projectFocus(data,'Center',recs),status:'ready',requestKey:'batch'};
window.mount=(presentation='dashboard',viewState)=>{window.scene?.destroy();window.scene=createFocusView({container:document.querySelector('#host'),data,snapshot:local,state:personal,language:'en',presentation,viewState,onEnterFocus:id=>events.push(['focus',id]),onSave:t=>events.push(['save',t.id]),onDismiss:id=>events.push(['dismiss',id]),onSearch:(t,target,context)=>events.push(['search',t.id,target,context]),onGetIdeas:id=>events.push(['ideas',id]),onBack:()=>events.push(['back'])});};
mount();
</script></body></html>`;
const server=createServer(async(req,res)=>{
  try{
    const path=new URL(req.url,'http://local').pathname;
    if(path==='/'){res.setHeader('Content-Type','text/html');res.end(html);return;}
    if(!path.startsWith('/extension/ui/')){res.writeHead(404);res.end();return;}
    const file=resolve(root,'.'+path);res.setHeader('Content-Type',extname(file)==='.css'?'text/css':'text/javascript');res.end(await readFile(file));
  }catch{res.writeHead(404);res.end();}
});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const base=`http://127.0.0.1:${server.address().port}`;
const errors=[],outbound=[],checks=[];let browser;
try{
  browser=await chromium.launch({executablePath:process.env.OTHERWISE_CHROMIUM || chromium.executablePath(),headless:true});
  const page=await browser.newPage({viewport:{width:1440,height:1050}});
  page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(!r.url().startsWith(base))outbound.push(r.url());});
  await page.addInitScript(()=>{
    const request=window.requestAnimationFrame.bind(window),cancel=window.cancelAnimationFrame.bind(window);
    window.pendingFrames=new Set();window.frameCalls=0;
    window.requestAnimationFrame=cb=>{let id=request(t=>{pendingFrames.delete(id);frameCalls++;cb(t);});pendingFrames.add(id);return id;};
    window.cancelAnimationFrame=id=>{pendingFrames.delete(id);cancel(id);};
  });
  await page.goto(base);await page.waitForFunction(()=>window.scene,null,{timeout:5000});
  async function starDragOutsideRelease(){
    await page.locator('.focus-map').scrollIntoViewIfNeeded();
    const star=await page.locator('[data-focus-star="Topic 10"]').boundingBox();
    const map=await page.locator('.focus-map').boundingBox();
    const selected=await page.locator('.focus-detail').getAttribute('data-selected-id');
    const actions=await page.evaluate(()=>events.length);
    await page.mouse.move(star.x+star.width/2,star.y+star.height/2);
    await page.mouse.down();
    await page.mouse.move(star.x+star.width/2+30,star.y+star.height/2,{steps:4});
    await page.mouse.move(Math.min(map.x+map.width+35,page.viewportSize().width-2),map.y+map.height/2,{steps:5});
    await page.mouse.up();
    const released=await page.evaluate(()=>scene.getViewState().camera);
    await page.mouse.move(map.x+map.width*.25,map.y+map.height*.35,{steps:5});
    const hovered=await page.evaluate(()=>scene.getViewState().camera);
    assert.deepEqual(hovered,released,'Unheld hover after a star-started outside release must not pan the camera');
    await page.waitForTimeout(300);
    assert.equal(await page.locator('.focus-detail').getAttribute('data-selected-id'),selected);
    assert.equal(await page.evaluate(()=>events.length),actions,'Drag must not select or enter a star');
  }
  async function touchStarCaptureTransfer(touch,cdp){
    await touch.locator('[data-focus-action="reset"]').click();
    const target=await touch.locator('[data-focus-star="Topic 10"]').boundingBox();
    const x=target.x+target.width/2,y=target.y+target.height/2;
    await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x,y,id:1}]});
    await cdp.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:x+20,y,id:1}]});
    const first=await touch.evaluate(()=>scene.getViewState().camera.x);
    await cdp.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:x+40,y,id:1}]});
    const second=await touch.evaluate(()=>scene.getViewState().camera.x);
    assert.notEqual(second,first,'Transferring touch capture from a star to the map must not stop a held drag');
    await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
  }
  if(process.env.OTHERWISE_FOCUS_CHECK==='touch-transfer'){
    const touch=await browser.newPage({viewport:{width:390,height:850},hasTouch:true,isMobile:true});
    await touch.goto(base);await touch.waitForFunction(()=>window.scene,null,{timeout:5000});
    const cdp=await touch.context().newCDPSession(touch);await touchStarCaptureTransfer(touch,cdp);
    await touch.evaluate(()=>scene.destroy());await touch.close();await page.evaluate(()=>scene.destroy());
    console.log(JSON.stringify({passed:true,checks:['Touch capture transfers from a star to the map without dropping the held gesture']},null,2));
    await browser.close();browser=null;await new Promise(r=>server.close(r));process.exit(0);
  }
  if(process.env.OTHERWISE_FOCUS_CHECK==='outside-drag'){
    await starDragOutsideRelease();
    await page.evaluate(()=>scene.destroy());assert.equal(await page.evaluate(()=>pendingFrames.size),0);assert.deepEqual(errors,[]);assert.deepEqual(outbound,[]);
    console.log(JSON.stringify({passed:true,checks:['Star-started drag outside release cleans pointer tracking before unheld hover']},null,2));
    await browser.close();browser=null;await new Promise(r=>server.close(r));process.exit(0);
  }
  if(process.env.OTHERWISE_FOCUS_CHECK==='delayed-doubleclick'){
    const star=page.locator('.focus-node[data-focus-id="Topic 10"] [data-focus-star]');
    await star.click();await page.waitForTimeout(330);
    assert.equal(await page.locator('.focus-detail').getAttribute('data-selected-id'),'Topic 10');
    const box=await star.boundingBox();await page.mouse.move(box.x+box.width/2,box.y+box.height/2);
    // Explicit down/up emits exactly the second completed click, not another pair.
    await page.mouse.down({clickCount:2});await page.mouse.up({clickCount:2});await page.waitForTimeout(100);
    assert.deepEqual(await page.evaluate(()=>events.filter(e=>e[0]==='focus')),[['focus','Topic 10']]);
    await page.evaluate(()=>document.querySelector('[data-focus-star="Topic 10"]').dispatchEvent(new MouseEvent('click',{bubbles:true,detail:1})));
    await page.locator('.focus-neighbor-list [data-focus-select="Topic 1"]').click();
    await page.evaluate(()=>{const star=document.querySelector('[data-focus-star="Topic 10"]');star.dispatchEvent(new MouseEvent('click',{bubbles:true,detail:2}));star.dispatchEvent(new MouseEvent('dblclick',{bubbles:true,detail:2}));});
    await page.waitForTimeout(300);
    assert.equal(await page.evaluate(()=>events.filter(e=>e[0]==='focus').length),1,'Explicit list selection must clear the prior star pair');
    await page.evaluate(()=>scene.destroy());assert.equal(await page.evaluate(()=>pendingFrames.size),0);assert.deepEqual(errors,[]);assert.deepEqual(outbound,[]);
    console.log(JSON.stringify({passed:true,checks:['Native same-star double-click after330ms survives automatic detail selection','Explicit list action clears remembered star pair']},null,2));
    await browser.close();browser=null;await new Promise(r=>server.close(r));process.exit(0);
  }
  assert.equal(await page.locator('.focus-node').count(),11);
  assert.equal(await page.locator('.focus-root').getAttribute('data-intro'),'wake');
  assert.deepEqual(await page.evaluate(()=>events),[],'Entry must not perform an action or request');
  await page.waitForTimeout(1250);
  const slit=await page.locator('.focus-node[data-focus-id="Center"] .focus-orb-host').innerHTML();
  await page.waitForFunction(previous=>document.querySelector('.focus-node[data-focus-id="Center"] .focus-orb-host').innerHTML!==previous,slit,{timeout:3000});
  assert.ok(await page.evaluate(()=>pendingFrames.size)<=1,'Only one scene animation loop');
  checks.push('First entry wakes with an animated orb; entry has no callbacks or external requests');
  const camera=()=>page.evaluate(()=>scene.getViewState().camera);
  await page.locator('[data-focus-action="zoom-in"]').click();const before=await camera();
  const oldPositions=await page.locator('.focus-node').evaluateAll(ns=>ns.map(n=>[n.dataset.focusId,n.getAttribute('transform')]));
  await page.evaluate(()=>scene.update({snapshot:ready,state:personal,language:'zh-CN'}));
  assert.deepEqual(await camera(),before);
  const newPositions=await page.locator('.focus-node').evaluateAll(ns=>ns.map(n=>[n.dataset.focusId,n.getAttribute('transform')]));
  for(const [id,position]of oldPositions)assert.equal(newPositions.find(x=>x[0]===id)[1],position);
  assert.equal(await page.locator('.focus-node').count(),43);
  assert.equal(newPositions.find(x=>x[0]==='Topic 11')[1],newPositions.find(x=>x[0]==='Topic 12')[1],'Identical semantic positions must remain identical');
  assert.equal(await page.locator('.focus-candidate-list [data-focus-select]').count(),10);
  assert.equal(await page.locator('.focus-page').innerText(),'第 1 / 4 页 · 32 个候选主题');
  await page.locator('[data-focus-action="next"]').click();await page.locator('[data-focus-action="next"]').click();await page.locator('[data-focus-action="next"]').click();
  assert.equal(await page.locator('.focus-candidate-list [data-focus-select]').count(),2);
  assert.equal(await page.locator('[data-focus-action="next"]').isDisabled(),true);
  await page.locator('[data-focus-action="previous"]').click();
  assert.equal(await page.locator('.focus-candidate-list [data-focus-select]').count(),10);
  checks.push('32 candidates paginate 10 per page; new batch and language preserve camera and existing positions');
  await page.locator('[data-focus-action="previous"]').click();await page.locator('[data-focus-action="previous"]').click();
  await page.locator('.focus-candidate-list [data-focus-select="Topic 11"]').click();
  assert.equal(await page.locator('.focus-description').innerText(),'Original catalog description 11.');
  assert.equal(await page.locator('.focus-detail-distance').innerText(),'0.300000');
  await page.locator('.focus-candidate-list [data-focus-select="Topic 12"]').click();
  assert.equal(await page.locator('.focus-detail').getAttribute('data-selected-id'),'Topic 12');
  await page.locator('[data-focus-action="google"]').click();await page.locator('[data-focus-action="save"]').click();await page.locator('[data-focus-action="dismiss"]').click();
  assert.deepEqual(await page.evaluate(()=>events.slice(-3)),[['search','Topic 12','google',{source:'focus',centerId:'Center'}],['save','Topic 12'],['dismiss','Topic 12']]);
  await page.locator('[data-focus-action="explore"]').click();
  assert.deepEqual(await page.evaluate(()=>events.at(-1)),['focus','Topic 12']);
  await page.locator('[data-focus-action="get-ideas"]').click();assert.deepEqual(await page.evaluate(()=>events.at(-1)),['ideas','Center']);
  await page.locator('.focus-search').fill('Topic 4');await page.locator('.focus-center-results [data-focus-enter="Topic 4"]').click();
  assert.deepEqual(await page.evaluate(()=>events.at(-1)),['focus','Topic 4']);
  checks.push('Overlapping coordinates are independently selectable; original text, true distance and explicit action context retained');
  await page.evaluate(()=>scene.update({snapshot:{...ready,status:'loading'},language:'en'}));
  assert.equal(await page.locator('[data-focus-action="get-ideas"]').isDisabled(),true);
  await page.evaluate(()=>scene.update({snapshot:{...ready,status:'error',error:'Private server detail'}}));
  assert.match(await page.locator('.focus-status').innerText(),/unavailable/);
  assert.doesNotMatch(await page.locator('.focus-root').innerText(),/Private server detail/);
  await page.evaluate(()=>scene.update({snapshot:ready,state:{approved:[data.byId.get('Topic 12')],explored:[]}}));
  assert.equal(await page.locator('[data-focus-action="save"]').isDisabled(),true);
  await page.keyboard.press('Escape');assert.equal(await page.locator('.focus-detail').getAttribute('data-selected-id'),'');
  await page.keyboard.press('Escape');assert.deepEqual(await page.evaluate(()=>events.at(-1)),['back']);
  checks.push('Loading/error/personal updates keep the local scene; Escape closes details before returning');
  const saved=await page.evaluate(()=>scene.getViewState());
  await page.evaluate(v=>mount('dashboard',v),saved);assert.equal(await page.locator('.focus-root').getAttribute('data-intro'),'focus');
  await page.emulateMedia({reducedMotion:'reduce'});
  await page.waitForFunction(()=>document.querySelector('.focus-root').dataset.motion==='reduced');
  assert.equal(await page.evaluate(()=>pendingFrames.size),0);
  assert.equal(await page.locator('.focus-ripple').getAttribute('opacity'),'0');
  assert.equal(await page.locator('.focus-node').count(),11);
  const frozen=await page.locator('.focus-node[data-focus-id="Center"] .focus-orb-host').innerHTML();await page.waitForTimeout(160);assert.equal(await page.locator('.focus-node[data-focus-id="Center"] .focus-orb-host').innerHTML(),frozen);
  await page.emulateMedia({reducedMotion:'no-preference'});await page.waitForTimeout(100);assert.equal(await page.evaluate(()=>pendingFrames.size),1);
  await page.evaluate(()=>scene.setActive(false));assert.equal(await page.evaluate(()=>pendingFrames.size),0);
  const paused=await page.evaluate(()=>frameCalls);await page.waitForTimeout(100);assert.equal(await page.evaluate(()=>frameCalls),paused);
  await page.evaluate(()=>scene.setActive(true));await page.waitForTimeout(60);assert.equal(await page.evaluate(()=>pendingFrames.size),1);
  checks.push('Repeat entry has a short transition; live reduced motion and inactive state pause the sole loop');
  for(const width of [1440,390,320]){
    await page.setViewportSize({width,height:1050});await page.waitForTimeout(100);
    await page.evaluate(()=>scene.update({snapshot:ready,language:'zh-CN'}));
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth),width);
    await page.locator('.focus-candidate-list [data-focus-select]').first().click();
    await page.waitForTimeout(450);
    await page.screenshot({path:resolve(output,`dashboard-${width}.png`),fullPage:true});
    checks.push(`${width}px dashboard keeps usable controls and details without horizontal overflow`);
  }
  await page.evaluate(()=>mount('sidebar',{woken:true}));
  assert.equal(await page.locator('.focus-root').getAttribute('data-presentation'),'sidebar');
  assert.equal(await page.locator('.focus-root').getAttribute('data-intro'),'focus');
  await page.evaluate(()=>scene.update({snapshot:ready}));
  await page.locator('.focus-candidate-list [data-focus-select]').first().focus();await page.keyboard.press('Enter');
  assert.equal(await page.locator('.focus-detail').getAttribute('data-selected-id'),'Topic 11');
  await page.waitForTimeout(450);
  await page.screenshot({path:resolve(output,'sidebar-320.png'),fullPage:true});
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth),320);
  // A physical double-click must cancel delayed selection and enter once.
  await page.locator('.focus-node[data-focus-id="Topic 10"] [data-focus-star]').dblclick();await page.waitForTimeout(300);
  assert.deepEqual(await page.evaluate(()=>events.at(-1)),['focus','Topic 10']);
  assert.equal(await page.locator('.focus-detail').getAttribute('data-selected-id'),'Topic 11');
  // Browsers may emit dblclick after successive clicks on different nearby stars.
  const focusBefore=await page.evaluate(()=>events.filter(e=>e[0]==='focus').length);
  await page.evaluate(()=>{
    const first=document.querySelector('[data-focus-star="Topic 11"]'),second=document.querySelector('[data-focus-star="Topic 12"]');
    first.dispatchEvent(new MouseEvent('click',{bubbles:true,detail:1}));
    second.dispatchEvent(new MouseEvent('click',{bubbles:true,detail:2}));
    second.dispatchEvent(new MouseEvent('dblclick',{bubbles:true,detail:2}));
  });
  await page.waitForTimeout(300);
  assert.equal(await page.evaluate(()=>events.filter(e=>e[0]==='focus').length),focusBefore,'Different stable IDs must not enter Focus');
  checks.push('Native-style double-click after different stable IDs does not change center');
  await starDragOutsideRelease();
  checks.push('Star-started outside drag release leaves camera stable on unheld hover');
  // Hidden documents cancel the loop; restoration does not replay entry.
  await page.evaluate(()=>{Object.defineProperty(document,'hidden',{configurable:true,value:true});document.dispatchEvent(new Event('visibilitychange'));});
  assert.equal(await page.evaluate(()=>pendingFrames.size),0);
  await page.evaluate(()=>{delete document.hidden;document.dispatchEvent(new Event('visibilitychange'));});
  await page.waitForTimeout(50);assert.equal(await page.evaluate(()=>pendingFrames.size),1);
  await page.locator('.focus-map').focus();const beforePan=await camera();await page.keyboard.press('ArrowRight');
  assert.notEqual((await camera()).x,beforePan.x);await page.keyboard.press('Home');assert.equal((await camera()).zoom,1);
  const map=page.locator('.focus-map');await map.scrollIntoViewIfNeeded();const rect=await map.boundingBox();
  const gestureSelection=await page.locator('.focus-detail').getAttribute('data-selected-id');
  await page.mouse.move(rect.x+15,rect.y+150);await page.mouse.down();await page.mouse.move(rect.x+45,rect.y+170,{steps:5});await page.mouse.up();await page.waitForTimeout(300);
  assert.equal(await page.locator('.focus-detail').getAttribute('data-selected-id'),gestureSelection);
  const changed=await page.evaluate(()=>{
    const next={...local,seedId:'Topic 1',nodes:[{...data.byId.get('Topic 1'),x:0,y:0,distance:0,isNeighbor:false,isRecommendation:false},{...data.byId.get('Center'),x:60,y:0,distance:.06,isNeighbor:true,isRecommendation:false}],status:'local'};
    scene.update({snapshot:next});return scene.getViewState();
  });
  assert.equal(changed.seedId,'Topic 1');assert.equal(changed.selected,null);assert.equal(changed.camera.x,0);assert.equal(changed.camera.zoom,1);
  assert.equal(await page.locator('.focus-title').innerText(),'Topic 1');
  assert.equal(await page.locator('.focus-node[data-focus-id="Topic 1"] .focus-orb-host circle').count(),1);
  assert.equal(await page.locator('.focus-node[data-focus-id="Center"] .focus-orb-host circle').count(),0);
  assert.equal(await page.locator('.focus-root').getAttribute('data-intro'),'focus');
  checks.push('Hidden/visible loop lifecycle, keyboard pan/reset, drag without selection and center-specific orb replacement');
  await page.evaluate(()=>scene.destroy());assert.equal(await page.locator('.focus-root').count(),0);
  assert.equal(await page.evaluate(()=>pendingFrames.size),0);
  const touch=await browser.newPage({viewport:{width:390,height:850},hasTouch:true,isMobile:true});
  touch.on('pageerror',e=>errors.push(e.message));touch.on('request',r=>{if(!r.url().startsWith(base))outbound.push(r.url());});
  await touch.goto(base);await touch.waitForFunction(()=>window.scene,null,{timeout:5000});
  assert.equal(await touch.evaluate(()=>matchMedia('(pointer: coarse)').matches),true);
  const touchTarget=await touch.locator('[data-focus-star="Topic 10"]').boundingBox();assert.ok(touchTarget.width>=43.9,'Touch hit area is at least44px');
  const touchMap=touch.locator('.focus-map');await touchMap.scrollIntoViewIfNeeded();const tb=await touchMap.boundingBox(),cx=tb.x+tb.width/2,cy=tb.y+tb.height/2;
  const cdp=await touch.context().newCDPSession(touch);
  await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x:cx-35,y:cy,id:1},{x:cx+35,y:cy,id:2}]});
  await cdp.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:cx-60,y:cy,id:1},{x:cx+60,y:cy,id:2}]});
  await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
  assert.ok(await touch.evaluate(()=>scene.getViewState().camera.zoom)>1);
  assert.equal(await touch.locator('.focus-detail').getAttribute('data-selected-id'),'');
  await touchStarCaptureTransfer(touch,cdp);
  checks.push('Star-to-map touch capture transfer retains held dragging');
  await touch.evaluate(()=>{
    const map=document.querySelector('[data-focus-star="Topic 10"]');
    map.dispatchEvent(new PointerEvent('pointerdown',{pointerId:99,button:0,clientX:20,clientY:200,bubbles:true}));
    map.dispatchEvent(new PointerEvent('pointercancel',{pointerId:99,bubbles:true}));
  }).catch(error=>{throw new Error('Pointer cancellation must be harmless: '+error.message);});
  await touch.evaluate(()=>scene.destroy());await touch.close();
  checks.push('Touch-sized hit targets and actual two-finger pinch preserve selection; pointercancel is harmless');
  assert.deepEqual(errors,[]);assert.deepEqual(outbound,[]);
  checks.push('Sidebar scrollable details, keyboard list selection, double-click arbitration and destruction');
  const result={passed:true,checks};await writeFile(resolve(output,'results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));
}catch(error){console.error(JSON.stringify({pageErrors:errors,checks},null,2));if(browser)for(const p of browser.contexts().flatMap(c=>c.pages()))await p.screenshot({path:resolve(output,'failure.png'),fullPage:true}).catch(()=>{});throw error;}finally{if(browser)await browser.close();await new Promise(r=>server.close(r));}
