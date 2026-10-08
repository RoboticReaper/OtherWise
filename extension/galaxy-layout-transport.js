import {focusIdentity} from './core/focus-contract.js';
import {normalizeGalaxyLayoutOptions} from './core/galaxy-layout-options.js';
import {hasServiceConnection,connectionHeaders} from './core/connection.js';

class LayoutError extends Error {}
const validJobId=value=>typeof value==='string' && /^[A-Za-z0-9_-]{1,120}$/.test(value);
const object=value=>value!==null && typeof value==='object' && !Array.isArray(value);
const exact=(value,keys)=>object(value) && Object.keys(value).length===keys.length && keys.every(key=>Object.hasOwn(value,key));
const stages=new Set(['queued','verifying_source','exact_neighbors','projecting','placing_labels','ready','failed']);
const invalid=()=>{throw new LayoutError('The Galaxy layout data is invalid or does not match the topic catalog.');};
const connectionKey=value=>JSON.stringify([value.endpoint,value.accessToken,value.epoch]);

/** Public geometry only. Each request is bounded; the page owns job polling. */
export function createGalaxyLayoutTransport({catalog,loadIdentity,getConnection,hasEndpointPermission,fetchImpl=fetch}) {
  const topicIds=new Set(catalog.map(row=>row.topic)),domainIds=new Set(catalog.map(row=>row.domain));
  const active=new Set(),jobs=new Map();let revision=0;
  function invalidate(){revision++;jobs.clear();for(const controller of active)controller.abort(new LayoutError('Galaxy layout request cancelled because the connection changed.'));}
  function geometry(rows,ids){
    if(!Array.isArray(rows) || rows.length!==ids.size)invalid();
    const seen=new Set();
    return rows.map(row=>{
      if(!exact(row,['id','x','y']) || !ids.has(row.id) || seen.has(row.id) || !Number.isFinite(row.x) || !Number.isFinite(row.y))invalid();
      seen.add(row.id);return {id:row.id,x:row.x,y:row.y};
    });
  }
  function validate(raw,identity,parameters,jobId){
    if(!object(raw) || !validJobId(raw.job_id) || (jobId && raw.job_id!==jobId) || !['queued','running','ready','failed'].includes(raw.status) || !stages.has(raw.stage) ||
      Object.keys(raw).some(key=>!['job_id','status','stage','result','error'].includes(key)))invalid();
    const envelope={job_id:raw.job_id,status:raw.status,stage:raw.stage};
    if(raw.status==='failed')return {...envelope,error:'The Galaxy layout could not be generated. Check that the service has its numerical dependencies and try again.'};
    if(raw.status!=='ready'){if(raw.result!==undefined)invalid();return envelope;}
    const result=raw.result;
    if(!exact(result,['schema_version','cache_key','catalog_sha256','model','embedding','parameters','topics','domains']) || result.schema_version!==1 || !/^[a-f0-9]{64}$/.test(result.cache_key || ''))invalid();
    let source,controls;
    try{source=focusIdentity(result);controls=normalizeGalaxyLayoutOptions(result.parameters,{strict:true});}catch{invalid();}
    if(JSON.stringify(source)!==JSON.stringify(identity) || parameters && JSON.stringify(controls)!==JSON.stringify(parameters))invalid();
    return {...envelope,result:{schema_version:1,cache_key:result.cache_key,...source,parameters:controls,topics:geometry(result.topics,topicIds),domains:geometry(result.domains,domainIds)}};
  }
  async function request(method,parameters,jobId){
    const controller=new AbortController(),startedRevision=revision;active.add(controller);
    let abortListener;
    const aborted=new Promise((_,reject)=>{abortListener=()=>reject(controller.signal.reason);});
    controller.signal.addEventListener('abort',abortListener,{once:true});
    const timer=setTimeout(()=>controller.abort(new LayoutError('The Galaxy layout request took too long. Try again.')),30000);
    try{
      const connection=getConnection();
      if(!hasServiceConnection(connection) || !Number.isSafeInteger(connection.epoch) || connection.epoch<0)throw new LayoutError('Add your connection and team access code in Settings.');
      const key=connectionKey(connection);
      const assertCurrent=()=>{
        if(controller.signal.aborted || revision!==startedRevision || connectionKey(getConnection())!==key)throw new LayoutError('Galaxy layout request cancelled because the connection changed.');
      };
      const checkPermission=async()=>{const permitted=await hasEndpointPermission(connection.endpoint);assertCurrent();if(!permitted){invalidate();throw new LayoutError('Save the connection in Settings to allow this service.');}};
      const computation=(async()=>{
        const identity=focusIdentity(await loadIdentity());assertCurrent();
        if(identity.embedding.shape[0]!==topicIds.size)invalid();
        const known=jobId?jobs.get(jobId):null;
        if(known && known.connection!==key)throw new LayoutError('Galaxy layout job invalidated because the connection changed.');
        await checkPermission();assertCurrent();
        const response=await fetchImpl(`${connection.endpoint}/api/galaxy-layout${jobId?`/${encodeURIComponent(jobId)}`:''}`,{
          method,headers:connectionHeaders(connection),
          ...(parameters?{body:JSON.stringify({...identity,parameters})}:{}),credentials:'omit',redirect:'error',signal:controller.signal,
        });assertCurrent();
        if(!response.ok){
          const messages={401:'The team access code was not accepted. Check Settings.',403:'This connection is not permitted.',404:'Update the service or generate a new Galaxy preview.',409:'The service and Galaxy data do not match. Update the data before trying again.',422:'The Galaxy layout settings were not accepted.',429:'A Galaxy layout is already being generated. Try again shortly.',503:'Galaxy layout is unavailable. Check that the service has its numerical dependencies.'};
          throw new LayoutError(messages[response.status] || 'The service could not complete the Galaxy layout request.');
        }
        const raw=await response.text();assertCurrent();if(raw.length>12000000)throw new LayoutError('The Galaxy layout service response was too large.');
        const envelope=validate(JSON.parse(raw),identity,parameters || known?.parameters,jobId);
        await checkPermission();assertCurrent();
        if(method==='POST'){
          jobs.set(envelope.job_id,{parameters,connection:key});
          if(jobs.size>32)jobs.delete(jobs.keys().next().value);
        }
        return envelope;
      })();
      return await Promise.race([computation,aborted]);
    }catch(error){
      if(controller.signal.aborted)throw controller.signal.reason;
      throw error instanceof LayoutError?error:new LayoutError('The Galaxy layout data is unavailable or invalid. Check the connection and try again.');
    }finally{clearTimeout(timer);controller.signal.removeEventListener('abort',abortListener);active.delete(controller);}
  }
  function start(raw){
    let parameters;try{parameters=normalizeGalaxyLayoutOptions(raw,{strict:true});}catch{return Promise.reject(new LayoutError('Enter valid Galaxy layout settings. Minimum distance must not exceed spread.'));}
    return request('POST',parameters);
  }
  function status(jobId){if(!validJobId(jobId))return Promise.reject(new LayoutError('Invalid Galaxy layout job.'));return request('GET',null,jobId);}
  return {start,status,invalidate};
}
