import {createState,reduceState,prepareObservation,hashUrl,buildRequest,isAllowedUrl} from './core/index.js';

const PUBLIC_ACTIONS=new Set(['APPROVE','ADD_INTEREST','REMOVE_INTEREST','DISMISS','SET_SETTINGS','SET_FOCUS','CLEAR_DERIVED','RESET','CLEAR_ERROR']);
const SETTING_KEYS=new Set(['browsingEnabled','autoRefresh','mode','endpoint','accessToken','blockedDomains','language','recommendationView']);
const MAX_HISTORY=5000;
class SafeError extends Error {}

export function normalizeEndpoint(value) {
  let u;
  try {u=new URL(String(value).trim());} catch {throw new SafeError('Enter a valid service address.');}
  if(u.username || u.password || u.search || u.hash || (u.pathname && u.pathname!=='/')) throw new SafeError('Use only the service address, without a path or credentials.');
  if(u.protocol!=='https:' && !(u.protocol==='http:' && ['127.0.0.1','localhost'].includes(u.hostname))) throw new SafeError('Use HTTPS, or a local development address.');
  return u.origin;
}

function cleanRecommendations(value) {
  if(!Array.isArray(value) || value.length>100) throw new SafeError('The service returned an invalid recommendation list.');
  return value.map(row=>{
    if(!row || typeof row.topic!=='string' || !row.topic.trim() || row.topic.length>120 || typeof row.domain!=='string' || row.domain.length>120 || typeof row.description!=='string' || row.description.length>3000) throw new SafeError('The service returned an invalid topic.');
    return {id:row.topic,topic:row.topic,domain:row.domain,description:row.description,
      nearest_interest:typeof row.nearest_interest==='string'?row.nearest_interest:'',
      distance:Number.isFinite(row.distance)?row.distance:null,
      boundary_offset:Number.isFinite(row.boundary_offset)?row.boundary_offset:null,
      zone:row.zone==='Familiar overlap'?'Familiar overlap':'New territory'};
  });
}

export function createController({catalog,readState,writeState,historySearch,hasHistoryPermission,hasEndpointPermission,fetchImpl=fetch,openTab,clock=Date.now}) {
  let state; let queue=Promise.resolve(); let activeRequest=null;
  const initialized=(async()=>{
    const stored=await readState();
    state=stored?.schemaVersion===1?reduceState(stored,{type:'PRUNE'},clock()):createState(clock());
    if(!stored || JSON.stringify(stored)!==JSON.stringify(state)) await writeState(state);
  })();
  const serial=fn=>{const result=queue.then(async()=>{await initialized;return fn();});queue=result.catch(()=>{});return result;};
  const snapshot=()=>structuredClone(state);
  function cancelRequest(){activeRequest?.abort();activeRequest=null;}
  async function commit(action){
    const before=state;
    const next=reduceState(state,action,clock());
    if(next.generation!==before.generation) cancelRequest();
    state=next;await writeState(state);return snapshot();
  }
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
    if(result.after.settings.autoRefresh && result.after.approved.length && result.after.settings.accessToken && (requestKey(result.before)!==requestKey(result.after) || !result.before.settings.autoRefresh)) {
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
  async function recommend(){
    const current=await getState();
    const payload=buildRequest(current);
    const endpoint=normalizeEndpoint(current.settings.endpoint);
    if(!current.settings.accessToken) throw new Error('Add your team access code in Settings to connect.');
    let controller=null, timer=null;
    try{
      if(!await hasEndpointPermission(endpoint)) throw new SafeError('Save the connection in Settings to allow this service.');
      // The generation check and fetch invocation are one serialized operation.
      // No asynchronous permission/write gap can send a deleted profile.
      const started=await serial(()=>{
        if(state.generation!==current.generation)return null;
        cancelRequest();controller=new AbortController();activeRequest=controller;
        timer=setTimeout(()=>controller.abort(),30000);
        return {response:fetchImpl(`${endpoint}/api/recommend`,{
          method:'POST',headers:{'Content-Type':'application/json',Authorization:`Bearer ${current.settings.accessToken}`},
          body:JSON.stringify(payload),credentials:'omit',redirect:'error',signal:controller.signal,
        })};
      });
      if(!started)return getState();
      const response=await started.response;
      if(!response.ok){
        const messages={401:'The team access code was not accepted. Check Settings.',403:'This connection is not permitted.',422:'Review your approved interests and try again.',429:'The service is busy. Try again shortly.',503:'The recommendation model is warming up. Try again shortly.'};
        throw new SafeError(messages[response.status] || 'The service could not complete this request. Try again.');
      }
      const raw=await response.text(); if(raw.length>150000) throw new SafeError('The service response was too large.');
      const result=JSON.parse(raw);const items=cleanRecommendations(result.recommendations);
      if(!await hasEndpointPermission(endpoint)) return getState();
      return await serial(async()=>{
        if(state.generation!==current.generation || controller.signal.aborted) return snapshot();
        return commit({type:'RECOMMENDATIONS',items,generation:current.generation});
      });
    }catch(error){
      return await serial(async()=>{
        if(state.generation!==current.generation || controller?.signal.aborted && activeRequest!==controller) return snapshot();
        const message=error?.name==='AbortError'?'The service took too long. Your local data is safe; try again.':error instanceof SafeError?error.message:error instanceof TypeError?'Cannot reach the service. Check the connection or try again later.':'Could not refresh recommendations. Please try again.';
        await commit({type:'ERROR',message,generation:current.generation}); return snapshot();
      });
    }finally{clearTimeout(timer);if(activeRequest===controller) activeRequest=null;}
  }
  async function search(topic,provider='google'){
    if(!['google','youtube'].includes(provider)) throw new Error('Choose Google or YouTube.');
    const current=await getState();
    const id=typeof topic==='string'?topic:topic?.id || topic?.topic;
    const found=[...current.recommendations,...current.approved,...current.explored].find(t=>t.id===id || t.topic===id);
    if(!found) throw new Error('Choose a topic from your recommendations or map.');
    const query=encodeURIComponent(found.topic);
    const url=provider==='youtube'?`https://www.youtube.com/results?search_query=${query}`:`https://www.google.com/search?q=${query}`;
    const recommended=current.recommendations.some(item=>item.id===found.id);
    const nearestApproved=current.approved.some(item=>item.id===found.nearest_interest);
    const parentId=current.settings.mode==='global' && recommended && nearestApproved?found.nearest_interest:current.focus;
    try {await openTab(url);} catch {throw new SafeError('Could not open the search. Please try again.');}
    return serial(()=>state.generation===current.generation?commit({type:'EXPLORE',topic:found,parentId}):snapshot());
  }
  return {getState,dispatch,importHistory,observe,reconcile,removeHistory,revokeHistory,revokeEndpoint,recommend,search};
}
