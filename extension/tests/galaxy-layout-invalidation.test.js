import test from 'node:test';
import assert from 'node:assert/strict';
import {createController} from '../controller.js';
import {createState} from '../core/index.js';
import {createBackup} from '../core/backup.js';
import {GALAXY_LAYOUT_DEFAULTS as parameters} from '../core/galaxy-layout-options.js';
import {createGalaxyLayoutSession} from '../ui/galaxy-layout-editor.js';

const now=1770000000000;
const catalog=['Gardening','Botany'].map(topic=>({topic,domain:'Nature',description:''}));
const identity={catalog_sha256:'a'.repeat(64),model:'MPNet',embedding:{sha256:'b'.repeat(64),dtype:'float64',shape:[2,768]}};
function deferred(){let resolve;return {promise:new Promise(r=>resolve=r),resolve:value=>resolve(value)};}
function rig({holdPoll=false}={}){
 let stored=createState(now),failWrite=false,ready=0;
 const requests=[],timers=[],pollStarted=deferred(),pollResponse=deferred();
 const controller=createController({catalog,clock:()=>now,loadIdentity:async()=>identity,
  readState:async()=>structuredClone(stored),writeState:async next=>{if(failWrite)throw new Error('Storage full');stored=structuredClone(next);},
  hasHistoryPermission:async()=>false,hasEndpointPermission:async()=>true,
  fetchImpl:async(_url,options)=>{
   requests.push(options.method);
   if(options.method==='GET' && holdPoll){pollStarted.resolve(options.signal);await pollResponse.promise;}
   return new Response(JSON.stringify(options.method==='POST'?{job_id:'job-1',status:'queued',stage:'queued'}:
    {job_id:'job-1',status:'ready',stage:'ready',result:{schema_version:1,cache_key:'c'.repeat(64),...identity,parameters,
     topics:catalog.map((row,i)=>({id:row.topic,x:i,y:i})),domains:[{id:'Nature',x:0,y:0}]}}));
  },
 });
 const session=createGalaxyLayoutSession({request:controller.startGalaxyLayout,poll:controller.getGalaxyLayoutJob,
  onReady:()=>ready++,now:()=>now,schedule:callback=>{const timer={callback,cancelled:false};timers.push(timer);return timer;},cancel:timer=>{timer.cancelled=true;},
 });
 // The session represents a Map window; imports happen in another window.
 const unsubscribe=controller.subscribeGalaxyLayoutInvalidation(()=>session.invalidate());
 return {controller,session,requests,timers,pollStarted:pollStarted.promise,releasePoll:pollResponse.resolve,
  ready:()=>ready,failWrite:()=>{failWrite=true;},close:()=>{unsubscribe();session.destroy();}};
}

for(const mode of ['merge','replace'])test(`${mode} backup import stops another window's Galaxy polling before old results can apply`,async()=>{
 const r=rig();
 try{
  await r.session.generate(parameters);const oldTimer=r.timers.at(-1);
  await r.controller.importBackup(createBackup(await r.controller.getState(),now),mode);
  await oldTimer.callback();
  assert.equal(r.ready(),0);
  assert.equal(r.session.getSnapshot().status,'idle');
  assert.equal(oldTimer.cancelled,true);
  assert.deepEqual(r.requests,['POST']);
  await r.session.generate(parameters);await r.timers.at(-1).callback();
  assert.equal(r.ready(),1);assert.equal(r.session.getSnapshot().status,'ready');
  assert.deepEqual(r.requests,['POST','POST','GET']);
 }finally{r.close();}
});

test("clearing derived data stops another window's scheduled Galaxy poll",async()=>{
 const r=rig();
 try{
  await r.session.generate(parameters);const oldTimer=r.timers.at(-1);
  await r.controller.dispatch({type:'CLEAR_DERIVED'});await oldTimer.callback();
  assert.equal(r.ready(),0);assert.equal(r.session.getSnapshot().status,'idle');
  assert.deepEqual(r.requests,['POST']);
 }finally{r.close();}
});

for(const operation of ['merge','replace','clear'])test(`${operation} discards a Galaxy response already in flight`,async()=>{
 const r=rig({holdPoll:true});
 try{
  await r.session.generate(parameters);
  const polling=r.timers.at(-1).callback(),signal=await r.pollStarted;
  if(operation==='clear')await r.controller.dispatch({type:'CLEAR_DERIVED'});
  else await r.controller.importBackup(createBackup(await r.controller.getState(),now),operation);
  assert.equal(signal.aborted,true);
  // Return the old geometry even if the service ignores cancellation.
  r.releasePoll();await polling;
  assert.equal(r.ready(),0);assert.equal(r.session.getSnapshot().status,'idle');
  assert.equal(r.timers.length,1);assert.deepEqual(r.requests,['POST','GET']);
 }finally{r.releasePoll();r.close();}
});

test('failed backup persistence keeps the original Galaxy preview active',async()=>{
 const r=rig();
 try{
  await r.session.generate(parameters);
  const backup=createBackup(await r.controller.getState(),now);r.failWrite();
  await assert.rejects(r.controller.importBackup(backup,'replace'),/Storage full/);
  assert.equal(r.session.getSnapshot().status,'queued');assert.equal(r.timers.at(-1).cancelled,false);
  await r.timers.at(-1).callback();assert.equal(r.ready(),1);
  assert.equal(r.session.getSnapshot().status,'ready');assert.deepEqual(r.requests,['POST','GET']);
 }finally{r.close();}
});
