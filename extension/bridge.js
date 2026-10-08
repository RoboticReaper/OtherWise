import {normalizeEndpoint} from './controller.js';

const preview=new URLSearchParams(location.search).get('preview')==='1';
const api=preview?await import('./dev-preview.js'):null;
async function send(message){
  if(!globalThis.chrome?.runtime?.id)throw new Error('Open OtherWise from your Chrome extensions.');
  const response=await chrome.runtime.sendMessage(message);
  if(response?.error)throw new Error(response.error);
  if(!response?.state)throw new Error('OtherWise is reconnecting. Reopen the side panel.');
  return response.state;
}
async function requestHistory(){
  let granted;
  try {granted=await chrome.permissions.request({permissions:['history']});}
  catch {throw new Error('Could not enable history access. Please try again.');}
  if(!granted)throw new Error('History access was not enabled. You can still add interests manually.');
}
export async function getState(){return preview?api.getState():send({type:'GET_STATE'});}
export async function openDashboard(view='map'){
  const selected=['interests','discover','map','settings'].includes(view)?view:'map';
  if(preview){
    const url=new URL(`dashboard.html?preview=1&view=${selected}`,location.href);
    globalThis.open(url.href,'_blank','noopener,noreferrer');
    return;
  }
  if(!globalThis.chrome?.runtime?.id)throw new Error('Open OtherWise from your Chrome extensions.');
  try{await chrome.tabs.create({url:chrome.runtime.getURL(`dashboard.html?view=${selected}`)});}
  catch{throw new Error('Could not open the dashboard. Try again.');}
}
export async function dispatch(action){
  if(preview)return api.dispatch(action);
  if(action.type==='SET_SETTINGS'){
    const permissionRequest={};
    if(action.patch?.browsingEnabled)permissionRequest.permissions=['history'];
    if(action.patch?.endpoint){
      const endpoint=normalizeEndpoint(action.patch.endpoint);
      permissionRequest.origins=[`${endpoint}/*`];
      action={...action,patch:{...action.patch,endpoint}};
    }
    if(Object.keys(permissionRequest).length){
      let granted;
      try {granted=await chrome.permissions.request(permissionRequest);}
      catch {throw new Error('Could not enable access. Please try saving Settings again.');}
      if(!granted)throw new Error('The requested access was not enabled. You can still add interests manually.');
    }
  }
  return send({type:'ACTION',action});
}
export async function importHistory(days=30){if(preview)return api.importHistory(days);await requestHistory();return send({type:'IMPORT_HISTORY',days});}
export async function recommend(){return preview?api.recommend():send({type:'RECOMMEND'});}
export async function search(topic,provider,context){return preview?api.search(topic,provider,context):send({type:'SEARCH',topic,provider,...(context===undefined?{}:{context})});}
export function subscribe(callback){
  if(preview)return api.subscribe(callback);
  if(!globalThis.chrome?.storage)return ()=>{};
  const listener=(changes,area)=>{if(area==='local' && changes.state?.newValue)callback(changes.state.newValue);};
  chrome.storage.onChanged.addListener(listener);
  return ()=>chrome.storage.onChanged.removeListener(listener);
}


let focusPort=null;
const pendingFocus=new Map(),focusInvalidationListeners=new Set();
const validFocusId=value=>typeof value==='string' && value.length>0 && value.length<=120;
function rejectFocus(requestId,message){
  const pending=pendingFocus.get(requestId);
  if(!pending)return;
  pendingFocus.delete(requestId);clearTimeout(pending.timer);pending.reject(new Error(message));
}
function invalidateFocusBridge(message){
  for(const requestId of pendingFocus.keys())rejectFocus(requestId,message);
  for(const listener of focusInvalidationListeners){try{listener();}catch{/* Keep other subscribers responsive. */}}
}
function connectFocus(){
  if(focusPort)return focusPort;
  if(!globalThis.chrome?.runtime?.id)throw new Error('Open OtherWise from your Chrome extensions.');
  const port=chrome.runtime.connect({name:'otherwise-focus'});focusPort=port;
  port.onMessage.addListener(message=>{
    if(focusPort!==port)return;
    if(message?.type==='invalidated'){invalidateFocusBridge('Focus request invalidated.');return;}
    const pending=pendingFocus.get(message?.requestId);
    if(!pending)return;
    if(typeof message.error==='string'){rejectFocus(message.requestId,message.error);return;}
    if(!message.result)return;
    pendingFocus.delete(message.requestId);clearTimeout(pending.timer);pending.resolve(message.result);
  });
  port.onDisconnect.addListener(()=>{
    if(focusPort!==port)return;
    focusPort=null;invalidateFocusBridge('Focus disconnected. Reconnect and try again.');
  });
  return port;
}
export function requestFocus(topicId,{requestId}={}){
  if(preview)return typeof api.requestFocus==='function'?api.requestFocus(topicId,{requestId}):Promise.reject(new Error('Focus recommendations are unavailable in this offline preview.'));
  if(!validFocusId(requestId) || typeof topicId!=='string' || !topicId || pendingFocus.has(requestId))return Promise.reject(new Error('Invalid Focus request.'));
  let port;
  try{port=connectFocus();}catch{return Promise.reject(new Error('Focus is reconnecting. Reopen the panel and try again.'));}
  return new Promise((resolve,reject)=>{
    const timer=setTimeout(()=>{
      rejectFocus(requestId,'The Focus request took too long. Try again.');
      try{port.postMessage({type:'cancel',requestId});}catch{/* Reconnection is handled by the port. */}
    },30000);
    pendingFocus.set(requestId,{resolve,reject,timer});
    try{port.postMessage({type:'request',requestId,topicId});}
    catch{rejectFocus(requestId,'Focus is reconnecting. Reopen the panel and try again.');}
  });
}
export function cancelFocus(requestId){
  if(preview){api.cancelFocus?.(requestId);return;}
  if(requestId!==undefined && !validFocusId(requestId))return;
  if(requestId===undefined){for(const id of pendingFocus.keys())rejectFocus(id,'Focus request cancelled.');}
  else rejectFocus(requestId,'Focus request cancelled.');
  try{focusPort?.postMessage({type:'cancel',...(requestId===undefined?{}:{requestId})});}catch{/* Closed windows have no active owner. */}
}
export function subscribeFocusInvalidation(listener){
  if(preview)return api.subscribeFocusInvalidation?.(listener) || (()=>{});
  focusInvalidationListeners.add(listener);
  // A local Port receives permission/settings invalidation; this performs no fetch.
  try{connectFocus();}catch{/* Request-time errors give the user a recoverable message. */}
  return ()=>focusInvalidationListeners.delete(listener);
}

async function sendGalaxyLayout(message){
  if(preview)throw new Error('Connect the extension to its service to generate a Galaxy preview. The packaged Galaxy is available offline.');
  if(!globalThis.chrome?.runtime?.id)throw new Error('Open OtherWise from your Chrome extensions.');
  const response=await chrome.runtime.sendMessage(message);
  if(response?.error)throw new Error(response.error);
  if(!response?.result)throw new Error('Galaxy layout is reconnecting. Reopen the panel and try again.');
  return response.result;
}
export const requestGalaxyLayout=parameters=>sendGalaxyLayout({type:'GALAXY_LAYOUT_START',parameters});
export const pollGalaxyLayout=jobId=>sendGalaxyLayout({type:'GALAXY_LAYOUT_STATUS',jobId});
