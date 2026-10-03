import {createController} from './controller.js';

const catalogPromise=fetch(chrome.runtime.getURL('catalog.json')).then(r=>r.json());
const controllerPromise=catalogPromise.then(async catalog=>{
  await chrome.storage.local.setAccessLevel({accessLevel:'TRUSTED_CONTEXTS'});
  return createController({catalog,
    readState:async()=> (await chrome.storage.local.get('state')).state,
    writeState:async state=>chrome.storage.local.set({state}),
    historySearch:query=>chrome.history.search(query),
    hasHistoryPermission:()=>chrome.permissions.contains({permissions:['history']}),
    hasEndpointPermission:endpoint=>chrome.permissions.contains({origins:[`${endpoint}/*`]}),
    openTab:url=>chrome.tabs.create({url}),
  });
});

function isOwnPage(sender){
  return sender.id===chrome.runtime.id && typeof sender.url==='string' && sender.url.startsWith(chrome.runtime.getURL('')) && !sender.tab?.incognito;
}
chrome.runtime.onMessage.addListener((message,sender,sendResponse)=>{
  if(!isOwnPage(sender)){sendResponse({error:'This request is not permitted.'});return false;}
  (async()=>{
    const c=await controllerPromise;
    switch(message?.type){
      case 'GET_STATE':return c.getState();
      case 'ACTION':return c.dispatch(message.action);
      case 'IMPORT_HISTORY':return c.importHistory(message.days);
      case 'RECOMMEND':return c.recommend();
      case 'SEARCH':return c.search(message.topic,message.provider);
      default:throw new Error('Unsupported request.');
    }
  })().then(state=>sendResponse({state}),error=>sendResponse({error:error.message || 'OtherWise could not complete that action.'}));
  return true;
});

function onVisited(item){
  // Re-read the saved title after navigation. Missing/stale titles are retried by the alarm.
  setTimeout(()=>controllerPromise.then(async c=>{
    const state=await c.getState();
    if(!state.settings.browsingEnabled || !await chrome.permissions.contains({permissions:['history']}))return;
    const items=await chrome.history.search({text:item.url || '',startTime:state.settings.analysisSince,maxResults:20});
    await c.observe(items.filter(candidate=>candidate.url===item.url),state.generation);
  }).catch(()=>{}),1200);
}
function onVisitRemoved(event){void controllerPromise.then(c=>c.removeHistory(event)).catch(()=>{});}
function registerHistoryListeners(){
  // Optional APIs can be absent until the user grants access in the side panel.
  if(!chrome.history)return;
  if(!chrome.history.onVisited.hasListener(onVisited))chrome.history.onVisited.addListener(onVisited);
  if(!chrome.history.onVisitRemoved.hasListener(onVisitRemoved))chrome.history.onVisitRemoved.addListener(onVisitRemoved);
}
registerHistoryListeners();
chrome.permissions.onAdded.addListener(permissions=>{
  if(permissions.permissions?.includes('history'))registerHistoryListeners();
});
chrome.permissions.onRemoved.addListener(permissions=>{
  if(permissions.permissions?.includes('history'))void controllerPromise.then(c=>c.revokeHistory()).catch(()=>{});
  if(permissions.origins?.length)void controllerPromise.then(c=>c.revokeEndpoint()).catch(()=>{});
});
chrome.alarms.onAlarm.addListener(alarm=>{if(alarm.name==='otherwise-reconcile')void controllerPromise.then(c=>c.reconcile()).catch(()=>{});});
async function initialize(){
  await chrome.sidePanel.setPanelBehavior({openPanelOnActionClick:true});
  await chrome.alarms.create('otherwise-reconcile',{periodInMinutes:1});
  const c=await controllerPromise;
  if(!await chrome.permissions.contains({permissions:['history']}))await c.revokeHistory();
}
chrome.runtime.onInstalled.addListener(()=>{void initialize();});
chrome.runtime.onStartup.addListener(()=>{void initialize();});
