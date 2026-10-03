// Explicit, offline design preview. Production never falls back to these samples.
import {createState,reduceState,prepareObservation} from './core/index.js';

const samples=[
  {id:'Gardening',topic:'Gardening',domain:'Nature',description:'Growing plants and understanding the living world around you.'},
  {id:'Botany',topic:'Botany',domain:'Science',description:'How plants grow, adapt and connect with their environment.'},
  {id:'Landscape architecture',topic:'Landscape architecture',domain:'Design',description:'Designing outdoor spaces that bring people and nature together.'},
  {id:'Ecology',topic:'Ecology',domain:'Science',description:'The relationships between living things and the places they share.'},
  {id:'Urban planning',topic:'Urban planning',domain:'Society',description:'How streets, parks and neighborhoods shape everyday life.'},
];
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
  state=reduceState(state,action);return notify();
}
export async function importHistory(){
  const observation=await prepareObservation({url:'https://example.org/sample-ecology',title:'Ecology — sample article',lastVisitTime:Date.now()},samples,{salt:state.salt,blockedDomains:[]});
  state=reduceState(state,{type:'INGEST',observations:[observation]});return notify();
}
export async function recommend(){
  if(!state.approved.length)throw new Error('Add an interest to try this sample preview.');
  state=reduceState(state,{type:'RECOMMENDATIONS',generation:state.generation,items:samples.slice(1).filter(t=>!state.approved.some(a=>a.id===t.id)).map(t=>({...t,nearest_interest:state.focus,zone:'New territory',distance:0.3,boundary_offset:0.04}))});
  return notify();
}
export async function search(topic,provider){
  // The design preview records a fictional step without opening external sites.
  state=reduceState(state,{type:'EXPLORE',topic,parentId:state.focus});return notify();
}
export function subscribe(listener){listeners.add(listener);return ()=>listeners.delete(listener);}
await recommend();
