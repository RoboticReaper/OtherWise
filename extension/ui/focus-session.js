let windowSequence=0;

/** Sole per-window recommendation cache. Selection never invokes request. */
export function createFocusSession({request,cancel=()=>{},onChange=()=>{},maxEntries=20}) {
  const cache=new Map(),capacity=Math.max(1,Math.min(20,Number.isInteger(maxEntries)?maxEntries:20));
  let active=null,destroyed=false,snapshot={seedId:null,requestKey:null,status:'local',error:null,envelope:null};
  const getSnapshot=()=>({...snapshot});
  const emit=()=>{if(!destroyed)onChange(getSnapshot());};
  function stop(){const previous=active;active=null;if(previous)cancel(previous.id);}
  function cached(key){if(!cache.has(key))return null;const value=cache.get(key);cache.delete(key);cache.set(key,value);return value;}
  function select(seedId,requestKey){
    if(destroyed||snapshot.seedId===seedId&&snapshot.requestKey===requestKey)return;
    stop();const envelope=seedId&&requestKey?cached(requestKey):null;
    snapshot={seedId,requestKey,status:envelope?'ready':'local',error:null,envelope};emit();
  }
  function load({refresh=false}={}){
    if(destroyed||!snapshot.seedId||!snapshot.requestKey)return Promise.resolve(getSnapshot());
    if(active)return active.promise;
    if(!refresh&&snapshot.envelope)return Promise.resolve(getSnapshot());
    const slot={id:String(++windowSequence),seedId:snapshot.seedId,key:snapshot.requestKey};active=slot;
    snapshot={...snapshot,status:'loading',error:null};emit();
    // Invoke synchronously so cancellation can always target the registered request ID.
    let result;try{result=request(slot.seedId,{requestId:slot.id});}catch(error){result=Promise.reject(error);}
    slot.promise=Promise.resolve(result).then(envelope=>{
      if(destroyed||active!==slot)return getSnapshot();
      cache.delete(slot.key);cache.set(slot.key,envelope);while(cache.size>capacity)cache.delete(cache.keys().next().value);
      snapshot={...snapshot,status:'ready',error:null,envelope};return getSnapshot();
    },error=>{
      if(destroyed||active!==slot)return getSnapshot();
      snapshot={...snapshot,status:'error',error:typeof error?.message==='string'?error.message:'',envelope:snapshot.envelope};return getSnapshot();
    }).finally(()=>{if(active===slot){active=null;emit();}});
    return slot.promise;
  }
  function invalidate(){if(destroyed)return;stop();cache.clear();snapshot={...snapshot,status:'local',error:null,envelope:null};emit();}
  function destroy(){if(destroyed)return;destroyed=true;stop();cache.clear();}
  return {select,load,invalidate,getSnapshot,destroy};
}
