import {createGalaxyMap} from './galaxy.js';
import {prepareGalaxy} from './galaxy-logic.js';
import {createFocusView} from './focus.js';
import {projectFocus} from './focus-logic.js';
import {createFocusSession} from './focus-session.js';
import {focusRequestKey,focusFailure} from './map-workspace-model.js';
import {workspaceText} from './map-workspace-i18n.js';
import {normalizeRecommendationOptions} from '../core/recommendation-options.js';

/** All navigation, cameras and request results here belong to this window only. */
export function createMapWorkspace({catalog,layout,state,language='en',presentation='dashboard',viewState,requestFocus,cancelFocus,onSave,onExplore,onDismiss,onSearch,onSettings,onCustomFocus,preview=false,requestGalaxyLayout,pollGalaxyLayout,onGalaxySettings}){
 const data=prepareGalaxy(catalog,layout),element=document.createElement('section');element.className='map-workspace';
 const save=typeof onSave==='function'?topic=>onSave(topic,{data}):undefined;
 element.innerHTML='<nav class="map-switch"><button type="button" data-map-view="galaxy"></button><button type="button" data-map-view="focus"></button><button type="button" data-map-action="refresh" hidden></button></nav><p class="map-preview-note" hidden></p><div class="map-focus-guidance" role="status" hidden><p></p><button type="button" data-map-action="settings"></button></div><div class="map-galaxy-host"></div><div class="map-focus-host" hidden></div>';
 const $=s=>element.querySelector(s),galaxyHost=$('.map-galaxy-host'),focusHost=$('.map-focus-host');
 let active=true,destroyed=false,subview=viewState?.view==='focus'?'focus':'galaxy',center=data.byId.has(viewState?.centerId)?viewState.centerId:null,focusView,epoch=0;
 let connection=connectionState(state),salt=state?.salt;
 let returnControl=null,entryControl=null,entryFocus=null,entryExpiry=0;
 const session=createFocusSession({request:requestFocus,cancel:cancelFocus,onChange:()=>renderFocus()});
 const galaxy=createGalaxyMap({requestGalaxyLayout,pollGalaxyLayout,onGalaxySettings,container:galaxyHost,catalog,layout,state,language,viewState:viewState?.galaxy,onSave:save,onFocus:onCustomFocus,onEnterFocus:enterFocus,onSearch:(topic,provider)=>onSearch?.(topic,provider,data.byId.has(topic.id)?{source:'galaxy'}:undefined)});
 function connectionState(value){const s=value?.settings||{};return {endpoint:s.endpoint||'',token:s.accessToken||'',options:JSON.stringify(normalizeRecommendationOptions(s.recommendationOptions))};}
 function key(){return center?focusRequestKey({endpoint:state.settings?.endpoint,epoch,identity:layout.metadata,seedId:center,options:state.settings?.recommendationOptions}):null;}
 function selectSession(){const snapshot=session.getSnapshot();const seedId=active&&subview==='focus'?center:null,requestKey=seedId?key():null;if(snapshot.seedId!==seedId||snapshot.requestKey!==requestKey)session.select(seedId,requestKey);}
 function renderFocus(){
  if(destroyed)return;
  const current=session.getSnapshot(),snapshot={...current,...projectFocus(data,center,current.seedId===center?current.envelope?.recommendations||[]:[],state.suppressed||[])};
  if(focusView&&active&&subview==='focus')focusView.update({snapshot,state,language});
  const error=subview==='focus'&&current.status==='error';$('.map-focus-guidance').hidden=!error;
  if(error)$('.map-focus-guidance p').textContent=workspaceText(language,focusFailure(current.error));
  const refresh=$('[data-map-action="refresh"]');refresh.hidden=subview!=='focus'||!current.envelope;refresh.disabled=current.status==='loading';
 }
 function sync(){
  if(destroyed)return;element.dataset.view=subview;
  for(const name of ['galaxy','focus']){const button=$(`[data-map-view="${name}"]`);button.textContent=workspaceText(language,name);button.setAttribute('aria-pressed',String(subview===name));}
  $('.map-switch').setAttribute('aria-label',workspaceText(language,'views'));
  $('[data-map-action="refresh"]').textContent=workspaceText(language,'refresh');$('[data-map-action="settings"]').textContent=workspaceText(language,'settings');$('[data-map-action="settings"]').hidden=typeof onSettings!=='function';
  $('.map-preview-note').hidden=!preview||subview!=='focus';$('.map-preview-note').textContent=workspaceText(language,'previewNote');
  galaxyHost.hidden=subview!=='galaxy';focusHost.hidden=subview!=='focus';
  selectSession();
  if(subview==='focus'&&!focusView){const current=session.getSnapshot();focusView=createFocusView({container:focusHost,data,snapshot:{...current,...projectFocus(data,center,current.envelope?.recommendations||[],state.suppressed||[])},state,language,presentation,viewState:viewState?.focus,onEnterFocus:enterFocus,onSave:save,onDismiss,onSearch,onGetIdeas:()=>session.load(),onBack:()=>switchView('galaxy',true)});}
  galaxy.setActive(active&&subview==='galaxy');focusView?.setActive(active&&subview==='focus');renderFocus();
 }
 // Galaxy may replace its detail button before invoking onEnterFocus. Capture the
 // initiating control first, and retain a descriptor to find its later replacement.
 function describeControl(node){return {node,action:node?.dataset?.galaxyAction,topic:node?.dataset?.galaxyTopic};}
 function captureEntry(event){
  const target=event.target.closest?.('[data-galaxy-action="enter-focus"],.galaxy-canvas');
  if(subview!=='galaxy'||!target||!galaxyHost.contains(target))return;
  if(event.type!=='dblclick'&&target.dataset.galaxyAction!=='enter-focus')return;
  const captured=describeControl(target);entryControl=captured;entryFocus=document.activeElement;
  // Keep the origin through native capture/bubble listeners, but not a later input.
  clearTimeout(entryExpiry);entryExpiry=setTimeout(()=>{entryExpiry=0;if(entryControl===captured){entryControl=null;entryFocus=null;}},0);
 }
 function available(node){return Boolean(node?.isConnected&&!node.disabled&&!node.closest('[hidden]')&&node.getClientRects().length);}
 function restoreGalaxyFocus(){
  let target=returnControl?.node;
  if(!available(target)&&returnControl?.action)target=[...galaxyHost.querySelectorAll('[data-galaxy-action]')].find(node=>node.dataset.galaxyAction===returnControl.action&&node.dataset.galaxyTopic===returnControl.topic&&available(node));
  if(!available(target))target=galaxyHost.querySelector('.galaxy-canvas');
  target?.focus({preventScroll:true});
 }
 function transition(view,restore=false){
  const previous=subview;let oldFocus=document.activeElement;
  if(previous!==view)onExplore?.(null);
  if(previous==='galaxy'&&view==='focus'){
   oldFocus=entryFocus||oldFocus;
   returnControl=entryControl||(galaxyHost.contains(oldFocus)?describeControl(oldFocus):null);
   clearTimeout(entryExpiry);entryExpiry=0;entryControl=null;entryFocus=null;
  }
  subview=view;sync();
  if(previous===view||!active)return;
  if(view==='focus'&&oldFocus&&oldFocus!==document.body&&!available(oldFocus))focusHost.querySelector('[data-focus-action="back"]')?.focus({preventScroll:true});
  if(view==='galaxy'&&(restore||focusHost.contains(oldFocus)&&!available(oldFocus)))restoreGalaxyFocus();
 }
 function enterFocus(id){if(!data.byId.has(id))return;const changed=center!==id||subview!=='focus';center=id;transition('focus');if(changed&&active){focusView?.replayEntry();onExplore?.(data.byId.get(id));}}
 function switchView(view,restore=false){if(view==='focus'){if(!center){const selected=galaxy.getViewState().selected;center=data.byId.has(selected)?selected:data.byId.has(state.focus)?state.focus:null;}if(center){enterFocus(center);return;}}transition(view,restore);}
 const click=event=>{const button=event.target.closest('button');if(!button)return;if(button.dataset.mapView)switchView(button.dataset.mapView);if(button.dataset.mapAction==='settings')onSettings?.();if(button.dataset.mapAction==='refresh')void session.load({refresh:true});};
 element.addEventListener('click',captureEntry,true);element.addEventListener('dblclick',captureEntry,true);element.addEventListener('click',click);sync();
 return {element,
  update(patch={}){if(destroyed)return;if(patch.state){const next=connectionState(patch.state),reset=salt!==patch.state.salt;const changed=next.endpoint!==connection.endpoint||next.token!==connection.token||next.options!==connection.options;state=patch.state;connection=next;salt=state.salt;if(changed||reset){epoch++;session.invalidate();}if(reset){center=null;subview='galaxy';focusView?.destroy();focusView=null;}}if(patch.language!==undefined)language=patch.language;galaxy.update({state,language});sync();},
  setActive(value){if(destroyed||active===Boolean(value))return;active=Boolean(value);sync();},
  getViewState(){return {view:subview,centerId:center,galaxy:galaxy.getViewState(),focus:focusView?.getViewState()||null};},
  openGalaxyLayoutEditor(){if(destroyed)return;switchView('galaxy');galaxy.openLayoutEditor();},
  invalidateFocus(){if(destroyed)return;epoch++;session.invalidate();selectSession();},
  destroy(){if(destroyed)return;destroyed=true;clearTimeout(entryExpiry);session.destroy();galaxy.destroy();focusView?.destroy();element.removeEventListener('click',captureEntry,true);element.removeEventListener('dblclick',captureEntry,true);element.removeEventListener('click',click);element.remove();},
 };
}
