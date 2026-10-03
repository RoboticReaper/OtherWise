import {createGalaxyMap} from './galaxy.js';
import {prepareGalaxy} from './galaxy-logic.js';
import {createFocusView} from './focus.js';
import {projectFocus} from './focus-logic.js';
import {createFocusSession} from './focus-session.js';
import {focusRequestKey,focusFailure} from './map-workspace-model.js';
import {workspaceText} from './map-workspace-i18n.js';
import {normalizeRecommendationOptions} from '../core/recommendation-options.js';

/** All navigation, cameras and request results here belong to this window only. */
export function createMapWorkspace({catalog,layout,state,language='en',presentation='dashboard',viewState,requestFocus,cancelFocus,onSave,onDismiss,onSearch,onSettings,onCustomFocus,preview=false}){
 const data=prepareGalaxy(catalog,layout),element=document.createElement('section');element.className='map-workspace';
 element.innerHTML='<nav class="map-switch"><button type="button" data-map-view="galaxy"></button><button type="button" data-map-view="focus"></button><button type="button" data-map-action="refresh" hidden></button></nav><p class="map-preview-note" hidden></p><div class="map-focus-guidance" role="status" hidden><p></p><button type="button" data-map-action="settings"></button></div><div class="map-galaxy-host"></div><div class="map-focus-host" hidden></div>';
 const $=s=>element.querySelector(s),galaxyHost=$('.map-galaxy-host'),focusHost=$('.map-focus-host');
 let active=true,destroyed=false,subview=viewState?.view==='focus'?'focus':'galaxy',center=data.byId.has(viewState?.centerId)?viewState.centerId:null,focusView,epoch=0;
 let connection=connectionState(state),salt=state?.salt;
 const session=createFocusSession({request:requestFocus,cancel:cancelFocus,onChange:()=>renderFocus()});
 const galaxy=createGalaxyMap({container:galaxyHost,catalog,layout,state,language,viewState:viewState?.galaxy,onSave,onFocus:onCustomFocus,onEnterFocus:enterFocus,onSearch:(topic,provider)=>onSearch?.(topic,provider,data.byId.has(topic.id)?{source:'galaxy'}:undefined)});
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
  if(subview==='focus'&&!focusView){const current=session.getSnapshot();focusView=createFocusView({container:focusHost,data,snapshot:{...current,...projectFocus(data,center,current.envelope?.recommendations||[],state.suppressed||[])},state,language,presentation,viewState:viewState?.focus,onEnterFocus:enterFocus,onSave,onDismiss,onSearch,onGetIdeas:()=>session.load(),onBack:()=>switchView('galaxy')});}
  galaxy.setActive(active&&subview==='galaxy');focusView?.setActive(active&&subview==='focus');renderFocus();
 }
 function enterFocus(id){if(!data.byId.has(id))return;center=id;subview='focus';sync();}
 function switchView(view){if(view==='focus'&&!center){const selected=galaxy.getViewState().selected;center=data.byId.has(selected)?selected:data.byId.has(state.focus)?state.focus:null;}subview=view;sync();}
 const click=event=>{const button=event.target.closest('button');if(!button)return;if(button.dataset.mapView)switchView(button.dataset.mapView);if(button.dataset.mapAction==='settings')onSettings?.();if(button.dataset.mapAction==='refresh')void session.load({refresh:true});};
 element.addEventListener('click',click);sync();
 return {element,
  update(patch={}){if(destroyed)return;if(patch.state){const next=connectionState(patch.state),reset=salt!==patch.state.salt;const changed=next.endpoint!==connection.endpoint||next.token!==connection.token||next.options!==connection.options;state=patch.state;connection=next;salt=state.salt;if(changed||reset){epoch++;session.invalidate();}if(reset){center=null;subview='galaxy';focusView?.destroy();focusView=null;}}if(patch.language!==undefined)language=patch.language;galaxy.update({state,language});sync();},
  setActive(value){if(destroyed||active===Boolean(value))return;active=Boolean(value);sync();},
  getViewState(){return {view:subview,centerId:center,galaxy:galaxy.getViewState(),focus:focusView?.getViewState()||null};},
  invalidateFocus(){if(destroyed)return;epoch++;session.invalidate();selectSession();},
  destroy(){if(destroyed)return;destroyed=true;session.destroy();galaxy.destroy();focusView?.destroy();element.removeEventListener('click',click);element.remove();},
 };
}
