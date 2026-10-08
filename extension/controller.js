import {restoreBackup} from './core/backup.js';
import {createGalaxyLayoutTransport} from './galaxy-layout-transport.js';
import {createState,reduceState,prepareObservation,hashUrl,buildRequest,isAllowedUrl} from './core/index.js';
import {createFocusTransport} from './focus-transport.js';
import {cleanDiscoveryMetadata} from './core/discovery.js';
import {normalizeEndpoint,hasServiceConnection,connectionHeaders} from './core/connection.js';
export {normalizeEndpoint} from './core/connection.js';

const FEEDBACK_ACTIONS=new Set(['SET_DISCOVERY_FEEDBACK','CLEAR_CONCEPT_FEEDBACK','UNDO_DISCOVERY_FEEDBACK']);
const PUBLIC_ACTIONS=new Set(['APPROVE','ADD_INTEREST','REMOVE_INTEREST','REMOVE_INTERESTS','UNDO_REMOVE_INTERESTS','CLEAR_INTEREST_UNDO','DISMISS','SET_SETTINGS','SET_FOCUS','CLEAR_DERIVED','RESET','CLEAR_ERROR',...FEEDBACK_ACTIONS,'CLEAR_DISCOVERY_FEEDBACK']);
const SETTING_KEYS=new Set(['browsingEnabled','autoRefresh','mode','endpoint','accessToken','blockedDomains','language','recommendationView','galaxyExplorationMode','galaxyLayoutOptions','galaxyShowDomainLabels','galaxyShowInterestLabels','recommendationOptions','recommendationKind','discoveryExploration','tutorialSeen','soundEffectsEnabled','soundEffectsVolume']);
const MAX_HISTORY=5000;
class SafeError extends Error {}

function cleanRecommendations(value, specific = false) {
  if(!Array.isArray(value) || value.length>100) throw new SafeError('The service returned an invalid recommendation list.');
  return value.map(row=>{
    if(!row || typeof row.topic!=='string' || !row.topic.trim() || row.topic.length>120 || typeof row.domain!=='string' || row.domain.length>120 || typeof row.description!=='string' || row.description.length>3000) throw new SafeError('The service returned an invalid topic.');
    let discovery;
    if(specific){try{discovery=cleanDiscoveryMetadata(row.discovery);}catch{throw new SafeError('The service returned an invalid graph concept.');}}
    return {id:row.topic,topic:row.topic,domain:row.domain,description:row.description,...(discovery?{discovery}:{}),
      nearest_interest:typeof row.nearest_interest==='string'?row.nearest_interest:'',
      distance:Number.isFinite(row.distance)?row.distance:null,
      boundary_offset:Number.isFinite(row.boundary_offset)?row.boundary_offset:null,
      zone:row.zone==='Familiar overlap'?'Familiar overlap':'New territory'};
  });
}

export function createController({catalog,readState,writeState,historySearch,hasHistoryPermission,hasEndpointPermission,fetchImpl=fetch,openTab,loadIdentity,clock=Date.now}) {
  let state; let queue=Promise.resolve(); let activeRequest=null; let focusEpoch=0; let galaxyEpoch=0; const pendingFocus=new Map();
  let identityPromise;
  const readGalaxyIdentity=()=>identityPromise ||= (async()=>{
    if(loadIdentity)return loadIdentity();
    const response=await fetchImpl(new URL('./galaxy-layout.json',import.meta.url),{credentials:'omit',redirect:'error'});
    if(!response.ok)throw new Error('Galaxy assets are unavailable.');
    return (await response.json()).metadata;
  })().catch(error=>{identityPromise=null;throw error;});
  const focusTransport=createFocusTransport({catalog,fetchImpl,hasEndpointPermission,loadIdentity:readGalaxyIdentity,
    getConnection:()=>({endpoint:normalizeEndpoint(state.settings.endpoint),accessToken:state.settings.accessToken,epoch:focusEpoch}),
  });
  const galaxyTransport=createGalaxyLayoutTransport({catalog,fetchImpl,hasEndpointPermission,loadIdentity:readGalaxyIdentity,
    getConnection:()=>({endpoint:normalizeEndpoint(state.settings.endpoint),accessToken:state.settings.accessToken,epoch:galaxyEpoch}),
  });
  const galaxyConnectionKey=s=>JSON.stringify([s.settings.endpoint,s.settings.accessToken]);
  function invalidateFocus(){focusEpoch++;for(const pending of pendingFocus.values())pending.cancelled=true;pendingFocus.clear();focusTransport.invalidate();}
  const focusConnectionKey=s=>JSON.stringify([s.settings.endpoint,s.settings.accessToken,s.settings.recommendationOptions]);
  const initialized=(async()=>{
    const stored=await readState();
    state=stored?.schemaVersion===1?reduceState(stored,{type:'PRUNE'},clock()):createState(clock());
    if(!stored || JSON.stringify(stored)!==JSON.stringify(state)) await writeState(state);
  })();
  const serial=fn=>{const result=queue.then(async()=>{await initialized;return fn();});queue=result.catch(()=>{});return result;};
  const snapshot=()=>structuredClone(state);
  function cancelRequest(){activeRequest?.abort();activeRequest=null;}
  async function commit(action){
    return persist(reduceState(state,action,clock()),action.type);
  }
  async function persist(next,type){
    const before=state;
    await writeState(next);
    if(['RESET','CLEAR_DERIVED','DELETE_SOURCES','INVALIDATE','IMPORT_BACKUP'].includes(type) || galaxyConnectionKey(next)!==galaxyConnectionKey(before)){galaxyEpoch++;galaxyTransport.invalidate();}
    if(next.generation!==before.generation) cancelRequest();
    if(['RESET','CLEAR_DERIVED','DELETE_SOURCES','INVALIDATE','IMPORT_BACKUP'].includes(type) || focusConnectionKey(next)!==focusConnectionKey(before)) invalidateFocus();
    state=next;return snapshot();
  }
  const importBackup=(backup,mode)=>serial(()=>persist(restoreBackup(state,backup,mode,clock()),'IMPORT_BACKUP'));
  const getState=()=>serial(async()=>{
    const next=reduceState(state,{type:'PRUNE'},clock());
    if(JSON.stringify(next)!==JSON.stringify(state)){state=next;await writeState(state);}
    return snapshot();
  });
  const requestKey=s=>s.approved.length?JSON.stringify(buildRequest(s)):'';
  async function dispatch(action){
    if(!action || !PUBLIC_ACTIONS.has(action.type)) throw new Error('Unsupported action.');
    let permissionGeneration=null;
    if(action.type==='SET_SETTINGS') {
      if(!action.patch || Object.keys(action.patch).some(k=>!SETTING_KEYS.has(k))) throw new Error('Unsupported setting.');
      if('endpoint' in action.patch) action={...action,patch:{...action.patch,endpoint:normalizeEndpoint(action.patch.endpoint)}};
      if(action.patch.browsingEnabled) {
        permissionGeneration=(await getState()).generation;
        let allowed;try {allowed=await hasHistoryPermission();} catch {throw new SafeError('Could not check history permission. Try again.');}
        if(!allowed) throw new SafeError('Allow history access before enabling local browsing analysis.');
      }
    }
    if(action.type==='ADD_INTEREST' && typeof action.topic==='string'){
      const match=catalog.find(t=>t.topic.toLowerCase()===action.topic.trim().toLowerCase());
      if(match) action={...action,topic:match};
    }
    const result=await serial(async()=>{
      const before=snapshot();
      if(permissionGeneration!==null && state.generation!==permissionGeneration)return {before,after:before};
      await commit(action);
      if(action.type==='SET_SETTINGS' && 'blockedDomains' in action.patch){
        const hashes=state.evidence.filter(e=>!isAllowedUrl(`https://${e.host}/`,state.settings.blockedDomains)).map(e=>e.sourceHash);
        if(hashes.length) await commit({type:'DELETE_SOURCES',hashes,all:false});
      }
      return {before,after:snapshot()};
    });
    if(FEEDBACK_ACTIONS.has(action.type) && result.after.generation !== result.before.generation && result.after.settings.recommendationKind === 'specific' && result.after.discovery.context && result.after.approved.length && hasServiceConnection(result.after.settings)){
      return recommend({rerank:true});
    }
    if(!FEEDBACK_ACTIONS.has(action.type) && action.type !== 'CLEAR_DISCOVERY_FEEDBACK' && result.after.settings.autoRefresh && result.after.approved.length && hasServiceConnection(result.after.settings) && (requestKey(result.before)!==requestKey(result.after) || !result.before.settings.autoRefresh)) {
      void recommend().catch(()=>{});
    }
    return result.after;
  }
  async function makeObservations(items,current){
    const endpointHost=(()=>{try{return new URL(current.settings.endpoint).hostname;}catch{return '';}})();
    const blockedDomains=[...current.settings.blockedDomains,endpointHost].filter(Boolean);
    const observations=[];
    for(const item of items.slice(0,MAX_HISTORY)){
      const observation=await prepareObservation(item,catalog,{salt:current.salt,blockedDomains},clock());
      if(observation) observations.push(observation);
    }
    return observations;
  }
  async function importHistory(days=30){
    const current=await getState();
    if(![7,30,90].includes(days)) throw new SafeError('Choose a 7, 30 or 90 day import.');
    try {
      if(!await hasHistoryPermission()) throw new SafeError('History permission is required to import.');
      if((await getState()).generation!==current.generation)return getState();
      const items=await historySearch({text:'',startTime:clock()-days*86400000,maxResults:MAX_HISTORY});
      const observations=await makeObservations(items,current);
      if(!await hasHistoryPermission()) return getState();
      return await serial(async()=>state.generation===current.generation?commit({type:'INGEST',observations,generation:current.generation}):snapshot());
    } catch(error) {throw error instanceof SafeError?error:new SafeError('Could not read browser history. Please try again.');}
  }
  async function observeAtGeneration(items,current){
    if(!current.settings.browsingEnabled || !await hasHistoryPermission()) return current;
    const recent=items.filter(item=>Number(item.lastVisitTime)>=current.settings.analysisSince);
    const observations=await makeObservations(recent,current);
    if(!await hasHistoryPermission()) return getState();
    return serial(async()=>state.settings.browsingEnabled && state.generation===current.generation?commit({type:'INGEST',observations,generation:current.generation}):snapshot());
  }
  async function observe(items,expectedGeneration){
    try {
      const current=await getState();
      if(expectedGeneration!==undefined && expectedGeneration!==current.generation)return current;
      return await observeAtGeneration(items,current);
    }
    catch {throw new SafeError('Could not analyze recent browsing. Please try again.');}
  }
  async function reconcile(){
    const current=await getState();
    try {
      if(!current.settings.browsingEnabled || !await hasHistoryPermission()) return current;
      const startTime=Math.max(current.settings.analysisSince,clock()-30*86400000);
      const items=await historySearch({text:'',startTime,maxResults:MAX_HISTORY});
      return await observeAtGeneration(items,current);
    } catch {throw new SafeError('Could not analyze recent browsing. Please try again.');}
  }
  async function removeHistory({urls=[],allHistory=false}){
    const current=await getState();
    const hashes=allHistory?[]:await Promise.all(urls.map(url=>hashUrl(url,current.salt)));
    return serial(()=>state.salt===current.salt?commit({type:'DELETE_SOURCES',hashes,all:allHistory}):snapshot());
  }
  async function revokeHistory(){
    return serial(async()=>{await commit({type:'SET_SETTINGS',patch:{browsingEnabled:false}});return commit({type:'CLEAR_DERIVED'});});
  }
  async function revokeEndpoint(){
    return serial(async()=>{
      await commit({type:'SET_SETTINGS',patch:{autoRefresh:false}});
      return commit({type:'INVALIDATE'});
    });
  }
  async function recommend({rerank=false}={}){
    const current=await getState();
    const payload=buildRequest(current);
    const specific=current.settings.recommendationKind==='specific';
    if(specific){
      const context=rerank?current.discovery.context:null;
      payload.seed=context?.seed ?? (globalThis.crypto.getRandomValues(new Uint32Array(1))[0] % 2**31);
      if(context)payload.exposures=structuredClone(context.exposures);
    }
    const endpoint=normalizeEndpoint(current.settings.endpoint);
    if(!hasServiceConnection(current.settings)) throw new Error('Add your team access code in Settings to connect.');
    let controller=null, timer=null;
    try{
      if(!await hasEndpointPermission(endpoint)) throw new SafeError('Save the connection in Settings to allow this service.');
      // The generation check and fetch invocation are one serialized operation.
      // No asynchronous permission/write gap can send a deleted profile.
      const started=await serial(()=>{
        if(state.generation!==current.generation)return null;
        cancelRequest();controller=new AbortController();activeRequest=controller;
        timer=setTimeout(()=>controller.abort(),30000);
        return {response:fetchImpl(`${endpoint}${specific?'/api/discover':'/api/recommend'}`,{
          method:'POST',headers:connectionHeaders(current.settings),
          body:JSON.stringify(payload),credentials:'omit',redirect:'error',signal:controller.signal,
        })};
      });
      if(!started)return getState();
      const response=await started.response;
      if(!response.ok){
        const messages={401:'The team access code was not accepted. Check Settings.',403:'This connection is not permitted.',404:'Update the recommendation service to use specific concepts.',422:specific?'Review your interests or clear outdated concept feedback and try again.':'Review your approved interests and try again.',429:'The service is busy. Try again shortly.',503:'The recommendation model is warming up. Try again shortly.'};
        throw new SafeError(messages[response.status] || 'The service could not complete this request. Try again.');
      }
      const raw=await response.text(); if(raw.length>150000) throw new SafeError('The service response was too large.');
      const result=JSON.parse(raw);const items=cleanRecommendations(result.recommendations,specific);
      if(specific && (result.seed!==payload.seed || !/^[a-f0-9]{64}$/.test(result.graph_sha256 || '') || new Set(items.map(r=>r.discovery.concept_id)).size!==items.length)) throw new SafeError('The service returned an invalid graph concept.');
      if(!await hasEndpointPermission(endpoint)) return getState();
      return await serial(async()=>{
        if(state.generation!==current.generation || controller.signal.aborted) return snapshot();
        return commit({type:'RECOMMENDATIONS',items,generation:current.generation,...(specific?{discovery:{seed:payload.seed,exposures:payload.exposures,graph_sha256:result.graph_sha256,rerank}}:{})});
      });
    }catch(error){
      return await serial(async()=>{
        if(state.generation!==current.generation || controller?.signal.aborted && activeRequest!==controller) return snapshot();
        const message=error?.name==='AbortError'?'The service took too long. Your local data is safe; try again.':error instanceof SafeError?error.message:error instanceof TypeError?'Cannot reach the service. Check the connection or try again later.':'Could not refresh recommendations. Please try again.';
        await commit({type:'ERROR',message,generation:current.generation}); return snapshot();
      });
    }finally{clearTimeout(timer);if(activeRequest===controller) activeRequest=null;}
  }
  async function search(topic,provider='google',context){
    if(!['google','youtube'].includes(provider)) throw new Error('Choose Google or YouTube.');
    const current=await getState();
    const id=typeof topic==='string'?topic:topic?.id || topic?.topic;
    let catalogParent=null;
    if(context!==undefined){
      if(!context || typeof context!=='object' || Array.isArray(context) ||
          (context.source==='galaxy' ? Object.keys(context).length!==1 :
           context.source==='focus' ? Object.keys(context).length!==2 || !Object.hasOwn(context,'centerId') : true)) {
        throw new SafeError('Choose a valid map search context.');
      }
      if(context.source==='focus'){
        const center=catalog.find(row=>row.topic===context.centerId);
        if(!center)throw new SafeError('Choose a catalog topic as the Focus center.');
        catalogParent=center.topic;
      }
    }
    // The whole Galaxy exposes public catalog topics before they are recommended.
    // Trust the packaged record, not the caller's supplied title or description.
    const found=context!==undefined?catalog.find(t=>t.topic===id):
      [...current.recommendations,...(current.recommendationBatch?.items || []),...current.approved,...current.explored].find(t=>t.id===id || t.topic===id)
      || catalog.find(t=>t.id===id || t.topic===id);
    if(!found) throw new Error('Choose a topic from your recommendations or map.');
    const query=encodeURIComponent(found.topic);
    const url=provider==='youtube'?`https://www.youtube.com/results?search_query=${query}`:`https://www.google.com/search?q=${query}`;
    const batch=current.recommendationBatch;
    const fromBatch=batch?.items.some(item=>item.id===found.id);
    const recommended=fromBatch || current.recommendations.some(item=>item.id===found.id);
    const nearestApproved=current.approved.some(item=>item.id===found.nearest_interest);
    const mode=fromBatch?batch.mode:current.settings.mode;
    const focus=fromBatch?batch.focus:current.focus;
    const parentId=mode==='global' && recommended && nearestApproved?found.nearest_interest:focus;
    try {await openTab(url);} catch {throw new SafeError('Could not open the search. Please try again.');}
    return serial(()=>state.generation===current.generation?commit({type:context===undefined?'EXPLORE':'EXPLORE_FROM_CATALOG',topic:found,parentId:context===undefined?parentId:catalogParent}):snapshot());
  }
  async function focusRecommendations(owner,{requestId,topicId}){
    cancelFocus(owner);
    const pending={requestId,cancelled:false};pendingFocus.set(owner,pending);
    try {
      const started=await serial(()=>{
        if(pending.cancelled || pendingFocus.get(owner)!==pending)throw new SafeError('Focus request cancelled.');
        return {promise:focusTransport.request(owner,{requestId,topicId,options:state.settings.recommendationOptions})};
      });
      return await started.promise;
    } finally {if(pendingFocus.get(owner)===pending)pendingFocus.delete(owner);}
  }
  function cancelFocus(owner,requestId){
    const pending=pendingFocus.get(owner);
    if(pending && (requestId===undefined || pending.requestId===requestId)){pending.cancelled=true;pendingFocus.delete(owner);}
    focusTransport.cancel(owner,requestId);
  }
  const startGalaxyLayout=parameters=>serial(()=>({promise:galaxyTransport.start(parameters)})).then(started=>started.promise);
  const getGalaxyLayoutJob=jobId=>serial(()=>({promise:galaxyTransport.status(jobId)})).then(started=>started.promise);
  const subscribeFocusInvalidation=listener=>focusTransport.subscribeInvalidation(listener);
  return {getState,dispatch,importBackup,importHistory,observe,reconcile,removeHistory,revokeHistory,revokeEndpoint,recommend,search,
    focusRecommendations,cancelFocus,subscribeFocusInvalidation,startGalaxyLayout,getGalaxyLayoutJob};
}
