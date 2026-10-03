import {normalizeEndpoint} from '../controller.js';
import {focusIdentity,FOCUS_SCHEMA_VERSION,FOCUS_ALGORITHM_VERSION} from '../core/focus-contract.js';
import {normalizeRecommendationOptions} from '../core/recommendation-options.js';
export function focusRequestKey({endpoint,epoch,identity,seedId,options}){
 let normalized='';try{normalized=normalizeEndpoint(endpoint);}catch{/* Invalid connection is handled only on explicit request. */}
 return JSON.stringify([normalized,epoch,FOCUS_SCHEMA_VERSION,FOCUS_ALGORITHM_VERSION,focusIdentity(identity),seedId,normalizeRecommendationOptions(options)]);
}
export function focusFailure(message){
 const known={
  'Add your connection and team access code in Settings.':'unconfigured',
  'The team access code was not accepted. Check Settings.':'permission',
  'Save the connection in Settings to allow this service.':'permission',
  'This connection is not permitted.':'permission',
  'The Focus request took too long. Try again.':'timeout',
  'The service and Galaxy data do not match. Update the data before trying again.':'version',
  'Focus recommendations are unavailable in this offline preview.':'preview',
 };
 return Object.hasOwn(known,message)?known[message]:'unavailable';
}
