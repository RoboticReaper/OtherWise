import {focusIdentity,buildFocusRequest,validateFocusResponse} from '../core/focus-contract.js';
import {normalizeRecommendationOptions} from '../core/recommendation-options.js';
const unavailable=()=>new Error('Focus recommendations are unavailable in this offline preview.');
/** The preview opens a recorded public batch; never sends a service request. */
export function createFocusPreview({load}){
 let assets;
 return {async request(seedId,options){
  assets ||= load();const {fixture,catalog,layout}=await assets;
  if(fixture?.fixture_version!==1||fixture.provenance?.kind!=='recorded-public-catalog-focus')throw unavailable();
  const identity=focusIdentity(layout.metadata),byId=new Map(catalog.map(topic=>[topic.id,topic]));
  if(JSON.stringify(focusIdentity(fixture.provenance.identity))!==JSON.stringify(identity))throw unavailable();
  const request=buildFocusRequest(seedId,identity,normalizeRecommendationOptions(options),byId);
  const batch=fixture.batches?.find(batch=>batch.request.topic_id===seedId&&JSON.stringify(normalizeRecommendationOptions(batch.request))===JSON.stringify(normalizeRecommendationOptions(options)));
  if(!batch)throw unavailable();return validateFocusResponse(batch.envelope,request,byId);
 }};
}
