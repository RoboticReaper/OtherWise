// Records the real extension in a separate temporary profile and local API.
// No browsing history, personal profile, or saved credentials are used.
import { chromium } from '/Users/arthurfu/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs';
import { mkdtemp, cp, readFile, writeFile, mkdir } from 'node:fs/promises';
import { spawn } from 'node:child_process';
import { randomBytes } from 'node:crypto';
import { createServer } from 'node:net';
import { resolve } from 'node:path';

const root = '/Users/arthurfu/Documents/OtherWise';
const output = resolve(root, 'outputs/otherwise-promo-production-2026-10-07');
await mkdir(`${output}/product`, { recursive: true });
const port = await new Promise((r,reject) => { const s=createServer();s.on('error',reject);s.listen(0,'127.0.0.1',()=>{const p=s.address().port;s.close(()=>r(p));}); });
const endpoint=`http://127.0.0.1:${port}`;
const token=randomBytes(24).toString('hex');
const api=spawn(`${root}/.venv/bin/python`,['-m','uvicorn','main:app','--host','127.0.0.1','--port',String(port),'--workers','1','--no-access-log'],{cwd:root,env:{...process.env,OTHERWISE_API_TOKEN:token,HF_HUB_OFFLINE:'1'},stdio:'ignore'});
let context;
const report={source:'Current extension source with real cached MPNet backend',seed:'Artificial intelligence',clips:{},screenshots:{}};
try {
  for(let n=0;;n++){
    if(api.exitCode!==null||n>150)throw Error('Local recommendation service did not start.');
    try{if((await fetch(`${endpoint}/health`)).ok)break;}catch{}
    await new Promise(r=>setTimeout(r,1000));
  }
  console.log('Real local recommendation service ready.');
  const extension=await mkdtemp('/tmp/otherwise-film-extension-');
  await cp(`${root}/dist/otherwise-extension`,extension,{recursive:true});
  await cp(`${root}/extension`,extension,{recursive:true,filter:s=>!s.includes('/tests/')&&!s.endsWith('.test.js')});
  const manifest=JSON.parse(await readFile(`${extension}/manifest.json`));
  manifest.host_permissions=['http://127.0.0.1/*'];
  await writeFile(`${extension}/manifest.json`,JSON.stringify(manifest));
  const profile=await mkdtemp('/tmp/otherwise-film-profile-');
  context=await chromium.launchPersistentContext(profile,{
    executablePath:'/Users/arthurfu/Library/Caches/ms-playwright/chromium-1194/chrome-mac/Chromium.app/Contents/MacOS/Chromium',
    headless:true,ignoreDefaultArgs:['--disable-extensions'],
    viewport:{width:1280,height:720},deviceScaleFactor:2,
    args:[`--disable-extensions-except=${extension}`,`--load-extension=${extension}`]
  });
  const worker=context.serviceWorkers()[0]||await context.waitForEvent('serviceworker');
  const videoStarted=Date.now();
  const page=await context.newPage();
  await page.goto(worker.url().replace('background.js','dashboard.html?view=interests'));
  await page.locator('#manual-interest').waitFor();
  if(await page.locator('#welcome-guide').count())await page.locator('[data-guide-action="skip"]').click();
  await page.evaluate(async ({endpoint,token})=>chrome.runtime.sendMessage({type:'ACTION',action:{type:'SET_SETTINGS',patch:{endpoint,accessToken:token,language:'en',tutorialSeen:true}}}),{endpoint,token});
  const begin=Date.now();
  const stamp=()=> (Date.now()-begin)/1000;
  const hold=ms=>page.waitForTimeout(ms);
  const frameDir=await mkdtemp(`${output}/product/frames-`);
  const frames=[];let recording=true;
  const captureFrames=(async()=>{
    while(recording){
      const t=stamp(),path=`${frameDir}/${String(frames.length).padStart(5,'0')}.jpg`;
      await page.screenshot({path,type:'jpeg',quality:95,scale:'css'});
      frames.push({t,path});await new Promise(r=>setTimeout(r,85));
    }
  })();
  const get=()=>page.evaluate(async()=> (await chrome.storage.local.get('state')).state);
  const until=async (fn,timeout=60000)=>{const start=Date.now();while(!await fn()){if(Date.now()-start>timeout)throw Error('Expected product state did not arrive.');await hold(150);}};
  const shot=async name=>{const path=`${output}/product/${name}.png`;await page.screenshot({path});report.screenshots[name]=path;};
  await hold(500);
  const initial=stamp();
  await hold(800);
  await page.locator('#manual-interest').pressSequentially('Artificial intelligence',{delay:65});
  await hold(750);
  await page.locator('#manual-form button[type="submit"]').click();
  await until(async()=> (await get()).approved.length===1);
  await hold(1000);await shot('confirmed-interest');
  await page.getByRole('button',{name:'Discover',exact:true}).click();
  await hold(700);await page.getByRole('button',{name:/Find ideas/}).click();
  const queryStart=stamp();
  await until(async()=> (await get()).recommendations.length>0,90000);
  report.recommendations=(await get()).recommendations.map(r=>({topic:r.topic,domain:r.domain,nearest_interest:r.nearest_interest}));
  const queryEnd=stamp();
  await page.locator('.recommendation-card').first().scrollIntoViewIfNeeded();
  await hold(3200);await shot('real-recommendations');
  report.clips.choose={ranges:[[initial,queryStart],[queryEnd,stamp()]]};
  console.log('Real recommendations captured:',report.recommendations.slice(0,3).map(r=>r.topic).join(', '));
  await page.getByRole('button',{name:'Settings',exact:true}).click();
  await page.locator('#recommendation-advanced summary').click();
  await page.locator('#recommendation-advanced').scrollIntoViewIfNeeded();
  await hold(500);const rangeStart=stamp();
  await hold(800);
  await page.locator('#recommendation-expansion').fill('0.14');
  await hold(1400);await shot('exploration-range');
  await page.locator('#recommendation-expansion').press('Enter');
  await until(async()=> (await get()).settings.recommendationOptions.expansion===0.14);
  await hold(1300);report.clips.range={ranges:[[rangeStart,stamp()]]};
  await page.getByRole('button',{name:'Discover',exact:true}).click();
  // Keep the same real result for the search/save story. Settings invalidate old
  // results by design, so ask the real service for a fresh batch before filming.
  await page.getByRole('button',{name:/Find ideas|Refresh ideas/}).click();
  await until(async()=> (await get()).recommendations.length>0,90000);
  const selected=(await get()).recommendations[0];report.selectedTopic=selected.topic;
  await page.locator('.recommendation-card').first().scrollIntoViewIfNeeded();
  await hold(500);const followStart=stamp();
  await hold(1000);
  const popupPromise=context.waitForEvent('page').catch(()=>null);
  await page.locator('.recommendation-card').first().getByRole('button',{name:/Google/}).click();
  await until(async()=> (await get()).explored.length>0);
  const popup=await popupPromise;if(popup)await popup.close();await page.bringToFront();
  await hold(900);
  await page.locator('.recommendation-card').first().getByRole('button',{name:'+ Save interest',exact:true}).click();
  await until(async()=> (await get()).approved.length===2);
  await hold(1600);await shot('saved-discovery');
  const followMiddle=stamp();
  await page.locator('[data-action="recommend"]').click();
  await until(async()=> (await get()).recommendations.length>0,90000);
  const followNew=stamp();await hold(2200);
  report.clips.follow={ranges:[[followStart,followMiddle],[followNew,stamp()]]};
  await page.getByRole('button',{name:'Map',exact:true}).click();
  await page.waitForFunction(()=>Number(document.querySelector('.galaxy-canvas')?.dataset.zoom)>0);
  await page.locator('[data-galaxy-action="fullscreen"]').click();
  await page.waitForFunction(()=>document.fullscreenElement!==null);
  await hold(900);const mapStart=stamp();await shot('galaxy');
  await hold(1200);await page.locator('.galaxy-search').fill('Artificial intelligence');
  await hold(700);await page.locator('.galaxy-result[data-galaxy-topic="Artificial intelligence"]').click();
  await page.locator('.galaxy-search').fill('');
  await hold(1600);await shot('galaxy-selected');
  await page.locator('[data-galaxy-action="fullscreen"]').click();
  await page.locator('[data-galaxy-action="enter-focus"]').click();
  await page.locator('.focus-root[data-seed-id="Artificial intelligence"]').waitFor();
  await hold(1800);await shot('focus');
  report.clips.map={ranges:[[mapStart,stamp()]]};
  recording=false;await captureFrames;
  let frameList='ffconcat version 1.0\n';
  for(let i=0;i<frames.length;i++)frameList+=`file '${frames[i].path}'\nduration ${i<frames.length-1?frames[i+1].t-frames[i].t:0.15}\n`;
  frameList+=`file '${frames.at(-1).path}'\n`;
  await writeFile(`${frameDir}/frames.ffconcat`,frameList);
  report.rawVideo=`${output}/product/clean-screen-recording.mp4`;
  await new Promise((resolve,reject)=>{
    const proc=spawn('/opt/homebrew/bin/ffmpeg',['-v','error','-y','-f','concat','-safe','0','-i',`${frameDir}/frames.ffconcat`,'-vf','fps=30','-an','-c:v','libx264','-preset','veryfast','-crf','16','-pix_fmt','yuv420p',report.rawVideo],{stdio:'inherit'});
    proc.on('exit',code=>code===0?resolve():reject(Error('Screen recording encoding failed.')));
  });
  report.videoOffsetSeconds=0;
  report.captureMethod='Actual page screenshots sampled during the real operations, encoded at 30fps; no synthetic interface frames.';
  await page.close();
  await writeFile(`${output}/product/capture.json`,JSON.stringify(report,null,2));
  console.log('Saved product recordings and four scene ranges.');
} finally {
  await context?.close();api.kill('SIGTERM');
}
