import {createController} from './controller.js';

const catalogPromise=fetch(chrome.runtime.getURL('catalog.json')).then(r=>r.json());
const controllerPromise=catalogPromise.then(async catalog=>{
  await chrome.storage.local.setAccessLevel({accessLevel:'TRUSTED_CONTEXTS'});
  return createController({catalog,
    loadIdentity:async()=>{
      const response=await fetch(chrome.runtime.getURL('galaxy-layout.json'),{credentials:'omit',redirect:'error'});
      if(!response.ok)throw new Error('Galaxy assets are unavailable.');
      return (await response.json()).metadata;
    },
    readState:async()=> (await chrome.storage.local.get('state')).state,
    writeState:async state=>chrome.storage.local.set({state}),
    historySearch:query=>chrome.history.search(query),
    hasHistoryPermission:()=>chrome.permissions.contains({permissions:['history']}),
    hasEndpointPermission:endpoint=>chrome.permissions.contains({origins:[`${endpoint}/*`]}),
    openTab:url=>chrome.tabs.create({url}),
  });
});

function isOwnPage(sender){
  return sender?.id===chrome.runtime.id && typeof sender.url==='string' && sender.url.startsWith(chrome.runtime.getURL('')) && !sender.tab?.incognito;
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
      case 'SEARCH':return c.search(message.topic,message.provider,message.context);
      default:throw new Error('Unsupported request.');
    }
  })().then(state=>sendResponse({state}),error=>sendResponse({error:error.message || 'OtherWise could not complete that action.'}));
  return true;
});

function validFocusMessage(message){
  if(!message || typeof message!=='object' || Array.isArray(message))return false;
  const validId=value=>typeof value==='string' && value.length>0 && value.length<=120;
  if(message.type==='request')return Object.keys(message).length===3 && validId(message.requestId) && typeof message.topicId==='string' && message.topicId.length>0;
  if(message.type==='cancel')return Object.keys(message).length===(Object.hasOwn(message,'requestId')?2:1) && (!Object.hasOwn(message,'requestId') || validId(message.requestId));
  return false;
}
chrome.runtime.onConnect?.addListener(port=>{
  if(port.name!=='otherwise-focus' || !isOwnPage(port.sender)){port.disconnect();return;}
  let disconnected=false,unsubscribe=()=>{};
  const post=message=>{if(!disconnected){try{port.postMessage(message);}catch{/* Closed windows have no reply target. */}}};
  port.onDisconnect.addListener(()=>{
    disconnected=true;unsubscribe();
    void controllerPromise.then(c=>c.cancelFocus(port)).catch(()=>{});
  });
  void controllerPromise.then(c=>{
    if(disconnected)return;
    unsubscribe=c.subscribeFocusInvalidation(()=>post({type:'invalidated'}));
  }).catch(()=>{});
  port.onMessage.addListener(message=>{
    if(disconnected)return;
    if(!validFocusMessage(message)){
      post({...(typeof message?.requestId==='string' && message.requestId.length<=120?{requestId:message.requestId}:{}),error:'Invalid Focus request.'});
      return;
    }
    void controllerPromise.then(async c=>{
      if(disconnected)return;
      if(message.type==='cancel'){c.cancelFocus(port,message.requestId);return;}
      try {
        const result=await c.focusRecommendations(port,{requestId:message.requestId,topicId:message.topicId});
        post({requestId:message.requestId,result});
      }catch(error){post({requestId:message.requestId,error:error.message || 'The Focus request could not be completed.'});}
    }).catch(()=>post({requestId:message.requestId,error:'The Focus service is unavailable.'}));
  });
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
