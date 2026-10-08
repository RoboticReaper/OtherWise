import {restoreBackup} from './core/backup.js';
// Explicit, offline design preview. Production never falls back to these samples.
import {createState,reduceState,prepareObservation} from './core/index.js';
import {createFocusPreview} from './ui/focus-preview.js';
import {galaxyLoader} from './ui/galaxy-data.js';

const samples=[
  {id:'Gardening',topic:'Gardening',domain:'Nature',description:'Growing plants and understanding the living world around you.'},
  {id:'Botany',topic:'Botany',domain:'Science',description:'How plants grow, adapt and connect with their environment.'},
  {id:'Landscape architecture',topic:'Landscape architecture',domain:'Design',description:'Designing outdoor spaces that bring people and nature together.'},
  {id:'Ecology',topic:'Ecology',domain:'Science',description:'The relationships between living things and the places they share.'},
  {id:'Urban planning',topic:'Urban planning',domain:'Society',description:'How streets, parks and neighborhoods shape everyday life.'},
];
const conceptSamples = ['Pollinator garden','Soil microbiology','Companion planting'].map((topic,index)=>({
  topic,domain:'Biology & nature',description:'Fictional concept for the offline interface preview.',
  discovery:{concept_id:`Q${100+index}`,area_id:'ecology',graph_path:['Ecology',topic],source_url:`https://www.wikidata.org/wiki/Q${100+index}`,level:index+1,exploration_pick:index===0,exploration_target:1,exploration_achieved:1},
}));
let state=createState();
const listeners=new Set();
state=reduceState(state,{type:'ADD_INTEREST',topic:samples[0]});
state=reduceState(state,{type:'EXPLORE',topic:samples[1],parentId:'Gardening'});
state=reduceState(state,{type:'EXPLORE',topic:samples[2],parentId:'Gardening'});
const snapshot=()=>structuredClone(state);
function notify(){for(const listener of listeners)listener(snapshot());return snapshot();}
export async function getState(){return snapshot();}
export async function dispatch(action){
  if(action.type==='ADD_INTEREST' && typeof action.topic==='string')action={...action,topic:samples.find(t=>t.topic.toLowerCase()===action.topic.toLowerCase()) || action.topic};
  const previous=state;state=reduceState(state,action);
  if (['RESET','CLEAR_DERIVED','DELETE_SOURCES','INVALIDATE'].includes(action.type)||['endpoint','accessToken','recommendationOptions'].some(key=>JSON.stringify(previous.settings[key])!==JSON.stringify(state.settings[key]))) invalidateFocus();
  if(['SET_DISCOVERY_FEEDBACK','CLEAR_CONCEPT_FEEDBACK','UNDO_DISCOVERY_FEEDBACK'].includes(action.type) && state.generation!==previous.generation && state.settings.recommendationKind==='specific' && state.discovery.context)return recommend({rerank:true});
  return notify();
}
export async function importBackup(backup,mode='merge'){
  state=restoreBackup(state,backup,mode);invalidateFocus();return notify();
}
export async function importHistory(){
  const observation=await prepareObservation({url:'https://example.org/sample-ecology',title:'Ecology — sample article',lastVisitTime:Date.now()},samples,{salt:state.salt,blockedDomains:[]});
  state=reduceState(state,{type:'INGEST',observations:[observation]});return notify();
}
export async function recommend({rerank=false}={}){
  if(!state.approved.length)throw new Error('Add an interest to try this sample preview.');
  const specific=state.settings.recommendationKind==='specific';
  const context=rerank?state.discovery.context:null;
  const items=(specific?conceptSamples:samples.slice(1)).filter(t=>!state.approved.some(a=>a.topic===t.topic) && !state.discovery.feedback[t.discovery?.concept_id]?.known);
  if(specific)items.sort((a,b)=>Number(state.discovery.feedback[b.discovery.concept_id]?.curious||false)-Number(state.discovery.feedback[a.discovery.concept_id]?.curious||false));
  state=reduceState(state,{type:'RECOMMENDATIONS',generation:state.generation,items:items.map(t=>({...t,nearest_interest:state.focus,zone:'New territory',distance:0.3,boundary_offset:0.04})),...(specific?{discovery:{seed:context?.seed??42,exposures:context?.exposures??state.discovery.exposures,graph_sha256:'0'.repeat(64),rerank}}:{})});
  return notify();
}
export async function search(topic,provider,context){
  // The design preview records a fictional step without opening external sites.
  if(context){const {catalog}=await galaxyLoader.load();const canonical=catalog.find(row=>row.id===topic.id);if(!canonical)throw new Error('Choose a catalog topic.');state=reduceState(state,{type:'EXPLORE_FROM_CATALOG',topic:canonical,parentId:context.source==='focus'?context.centerId:null});}
  else state=reduceState(state,{type:'EXPLORE',topic,parentId:state.focus});return notify();
}
export function subscribe(listener){listeners.add(listener);return ()=>listeners.delete(listener);}
const focusListeners=new Set(),focusPending=new Map();
const focusPreview=createFocusPreview({load:async()=>{
 const [assets,response]=await Promise.all([galaxyLoader.load(),fetch(new URL('./focus-preview.v1.json',import.meta.url),{credentials:'omit',redirect:'error'})]);
 if(!response.ok)throw new Error('Focus recommendations are unavailable in this offline preview.');
 return {...assets,fixture:await response.json()};
}});
function invalidateFocus(){cancelFocus();for(const listener of focusListeners)listener();}
export function subscribeFocusInvalidation(listener){focusListeners.add(listener);return ()=>focusListeners.delete(listener);}
export function cancelFocus(requestId){if(requestId===undefined){for(const pending of focusPending.values())pending.cancel();focusPending.clear();}else{focusPending.get(requestId)?.cancel();focusPending.delete(requestId);}}
export async function requestFocus(topicId,{requestId}={}){
 let cancel;const cancelled=new Promise((_,reject)=>{cancel=()=>reject(new Error('Focus request cancelled.'));});
 const slot={cancel};focusPending.set(requestId,slot);
 try{return await Promise.race([focusPreview.request(topicId,state.settings.recommendationOptions),cancelled]);}
 finally{if(focusPending.get(requestId)===slot)focusPending.delete(requestId);}
}
await recommend();
