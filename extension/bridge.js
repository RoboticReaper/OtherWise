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
  const selected=['discover','map','settings'].includes(view)?view:'map';
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
export async function search(topic,provider){return preview?api.search(topic,provider):send({type:'SEARCH',topic,provider});}
export function subscribe(callback){
  if(preview)return api.subscribe(callback);
  if(!globalThis.chrome?.storage)return ()=>{};
  const listener=(changes,area)=>{if(area==='local' && changes.state?.newValue)callback(changes.state.newValue);};
  chrome.storage.onChanged.addListener(listener);
  return ()=>chrome.storage.onChanged.removeListener(listener);
}
