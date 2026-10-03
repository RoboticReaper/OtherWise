import {OrbCore,ORB_UNITS} from './focus-orb.js';
import {createStarLayers,drawBackground} from './focus-stars.js';
import {focusText} from './focus-i18n.js';
import {paginate} from './pagination.js';
import {createStarActivation} from './star-activation.js';

// Same sorted-domain palette as Galaxy. Geometry is supplied exclusively by projectFocus.
const COLORS=['#8cafec','#89ccb0','#efae98','#c7a4ee','#d6cd8d','#a2c7d9','#da9fbb','#93b9a0','#ddbc91','#a5a5d9','#72c7c7','#d1a587','#c4beae','#9daed0','#c8abc8','#7fc39c','#a1c0f0','#d5b073','#a9ba85','#d1a2a2','#85bed5','#bfa9df','#bdbd93'];
const NS='http://www.w3.org/2000/svg',array=value=>Array.isArray(value)?value:[];
let instance=0;
function element(tag,text,className){const node=document.createElement(tag);if(text!==undefined)node.textContent=text;if(className)node.className=className;return node;}
function svgElement(tag,attrs,parent){const node=document.createElementNS(NS,tag);for(const [key,value]of Object.entries(attrs))node.setAttribute(key,String(value));parent.append(node);return node;}
function button(text,action){const node=element('button',text);node.type='button';node.dataset.focusAction=action;return node;}
const boundedZoom=value=>Math.max(.5,Math.min(8,value));

/** Independent scene: no requests, storage, personal-state mutation or coordinate generation. */
export function createFocusView({container,data,snapshot={seedId:null,nodes:[],status:'local'},state={},language='en',presentation='dashboard',viewState,onEnterFocus,onSave,onDismiss,onSearch,onGetIdeas,onBack}){
  const compact=presentation==='sidebar',prefix=`otherwise-focus-${++instance}`;
  const colors=new Map(data.domains.map((domain,index)=>[domain.id,COLORS[index%COLORS.length]]));
  let destroyed=false,active=true,frame=0,lastTime=0,time=0,age=0,selected=viewState?.seedId===snapshot.seedId?viewState?.selected:null;
  let page=viewState?.seedId===snapshot.seedId?viewState?.page||1:1,actionError=false,hovered=null,parX=0,parY=0;
  const reducedQuery=matchMedia('(prefers-reduced-motion: reduce)'),coarse=matchMedia('(pointer: coarse)');
  let reduced=reducedQuery.matches,intro=!compact&&!viewState?.woken?'wake':'focus',viewport={width:1,height:1};
  const initialCamera=()=>({x:0,y:0,zoom:1,extent:Math.max(380,...array(snapshot.nodes).map(n=>Math.hypot(n.x,n.y)*1.18))});
  let camera=initialCamera();
  if(viewState?.seedId===snapshot.seedId&&viewState.camera){
    const c=viewState.camera;
    camera={x:Number.isFinite(c.x)?c.x:0,y:Number.isFinite(c.y)?c.y:0,zoom:boundedZoom(Number.isFinite(c.zoom)?c.zoom:1),extent:Number.isFinite(c.extent)&&c.extent>0?c.extent:camera.extent};
  }
  const root=element('section',undefined,'focus-root');root.dataset.presentation=compact?'sidebar':'dashboard';root.dataset.intro=intro;
  root.innerHTML=`<header class="focus-header"><button type="button" data-focus-action="back" data-focus-copy="back"></button><div class="focus-heading"><span class="focus-eyebrow" data-focus-copy="center"></span><h2 class="focus-title"></h2></div><button type="button" data-focus-action="get-ideas" data-focus-copy="getIdeas"></button></header>
    <div class="focus-center-picker"><label class="focus-search-label"><span data-focus-copy="chooseCenter"></span><input class="focus-search" type="search" maxlength="200" autocomplete="off" spellcheck="false"></label><div class="focus-center-results" hidden></div></div>
    <p class="focus-disclosure" data-focus-copy="disclosure"></p><p class="focus-status" role="status" aria-live="polite"></p>
    <div class="focus-body"><div class="focus-visual"><div class="focus-stage"><canvas class="focus-background" aria-hidden="true"></canvas><svg class="focus-map" tabindex="0" role="group"><defs></defs><g class="focus-world"><g class="focus-rings"></g><g class="focus-links"></g><circle class="focus-ripple" opacity="0" fill="none"/><g class="focus-node-layer"></g></g></svg><div class="focus-map-controls"><button type="button" data-focus-action="zoom-out">−</button><button type="button" data-focus-action="zoom-in">+</button><button type="button" data-focus-action="reset" data-focus-copy="reset"></button></div><div class="focus-map-key"><span class="focus-key-neighbor" data-focus-copy="neighbors"></span><span class="focus-key-candidate" data-focus-copy="candidates"></span></div></div>
    <p class="focus-selection-help" data-focus-copy="selectionHelp"></p><p class="focus-geometry" data-focus-copy="geometry"></p></div><aside class="focus-detail" data-selected-id=""></aside></div>
    <div class="focus-lists"><section class="focus-neighbors"><h3 data-focus-copy="neighbors"></h3><div class="focus-neighbor-list"></div></section><section class="focus-candidates"><h3 data-focus-copy="candidates"></h3><div class="focus-candidate-list"></div><nav class="focus-pagination"><button type="button" data-focus-action="previous" data-focus-copy="previous"></button><output class="focus-page"></output><button type="button" data-focus-action="next" data-focus-copy="next"></button></nav></section></div>
    <p class="focus-action-error" role="alert" hidden></p><div class="focus-announcement focus-sr-only" role="status" aria-live="polite"></div>`;
  container.replaceChildren(root);
  const $=selector=>root.querySelector(selector),map=$('.focus-map'),canvas=$('.focus-background'),ctx=canvas.getContext('2d');
  if(!ctx){root.remove();throw new Error('Focus canvas is unavailable.');}
  const world=$('.focus-world'),nodeLayer=$('.focus-node-layer'),defs=$('defs'),ripple=$('.focus-ripple');
  const layers=createStarLayers(compact),records=new Map(),pending=new Set(),pointers=new Map(),cleanups=[];
  let pointerStart=null,gestureMoved=false,lastClick=null,doubleId=null;
  const t=(key,values)=>focusText(language,key,values),nodeFor=id=>array(snapshot.nodes).find(node=>node.id===id),topicFor=id=>data.byId.get(id);
  const colorFor=node=>colors.get(node.domain)||COLORS[0];
  const scale=()=>Math.min(viewport.width,viewport.height)/(2*camera.extent)*camera.zoom;
  const screen=node=>({x:viewport.width/2+(node.x-camera.x)*scale(),y:viewport.height/2-(node.y-camera.y)*scale()});
  const on=(target,event,handler,options)=>{target.addEventListener(event,handler,options);cleanups.push(()=>target.removeEventListener(event,handler,options));};
  const activation=createStarActivation({onSelect:id=>select(id,true),onEnterFocus:id=>runAction('explore',id)});

  function focusMap(){map.focus({preventScroll:true});}
  function clearClickSequence(){activation.cancel();lastClick=null;doubleId=null;}
  function select(id,preserveClicks=false){
    if(destroyed||!nodeFor(id))return;
    if(preserveClicks)activation.cancel();else clearClickSequence();selected=id;actionError=false;root.dataset.selectedId=id;
    $('.focus-announcement').textContent=t('selected',{topic:topicFor(id).topic});renderDetails();paint();
  }
  function refreshCopy(){
    const focused=document.activeElement,hadFocus=root.contains(focused);
    const focusKey=['focusAction','focusSelect','focusEnter','focusStar'].find(key=>focused?.dataset?.[key]);
    const focusValue=focusKey?focused.dataset[focusKey]:null;
    root.lang=language==='zh-CN'?'zh-CN':'en';root.dataset.seedId=snapshot.seedId||'';root.dataset.selectedId=selected||'';
    root.querySelectorAll('[data-focus-copy]').forEach(node=>{node.textContent=t(node.dataset.focusCopy);});
    $('.focus-title').textContent=topicFor(snapshot.seedId)?.topic||t('chooseCenter');
    $('.focus-search').placeholder=t('searchPlaceholder');map.setAttribute('aria-label',t('canvas'));
    for(const [action,key]of [['zoom-in','zoomIn'],['zoom-out','zoomOut']])$(`[data-focus-action="${action}"]`).setAttribute('aria-label',t(key));
    const getIdeas=$('[data-focus-action="get-ideas"]');getIdeas.disabled=!snapshot.seedId||snapshot.status==='loading'||pending.has('get-ideas')||typeof onGetIdeas!=='function';
    const candidates=array(snapshot.nodes).filter(n=>n.isRecommendation);
    const status=snapshot.status==='ready'&&!candidates.length?'empty':snapshot.status;
    $('.focus-status').textContent=t(['local','loading','ready','error','empty'].includes(status)?status:'local');
    $('.focus-action-error').hidden=!actionError;$('.focus-action-error').textContent=t('actionError');
    renderSearch();renderLists();renderDetails();renderNodes();paint();
    if(hadFocus&&!root.contains(document.activeElement)){
      const target=focusKey?[...root.querySelectorAll('button,[data-focus-star]')].find(node=>node.dataset[focusKey]===focusValue&&!node.disabled):null;
      (target||map).focus({preventScroll:true});
    }
  }
  function renderSearch(){
    const query=$('.focus-search').value.trim().toLocaleLowerCase(),results=$('.focus-center-results');results.replaceChildren();results.hidden=!query;
    if(!query)return;
    const words=query.split(/\s+/);
    const matches=data.topics.filter(topic=>words.every(word=>`${topic.topic} ${topic.domain} ${topic.description}`.toLocaleLowerCase().includes(word)))
      .sort((a,b)=>Number(b.topic.toLocaleLowerCase()===query)-Number(a.topic.toLocaleLowerCase()===query)||a.topic.localeCompare(b.topic)).slice(0,12);
    for(const topic of matches){const item=element('button',topic.topic,'focus-center-result');item.type='button';item.dataset.focusEnter=topic.id;item.disabled=typeof onEnterFocus!=='function';results.append(item);}
  }
  function topicRow(node){
    const item=element('button',undefined,'focus-topic-row');item.type='button';item.dataset.focusSelect=node.id;
    item.style.setProperty('--topic-color',colorFor(node));
    const title=element('span',topicFor(node.id).topic,'focus-list-title'),distance=element('span',node.distance.toFixed(3),'focus-list-distance');
    distance.setAttribute('aria-label',`${t('distance')}: ${node.distance.toFixed(6)}`);
    const marker=element('i',undefined,'focus-list-marker');marker.setAttribute('aria-hidden','true');
    item.append(marker,title,distance);return item;
  }
  function renderLists(){
    const neighbors=$('.focus-neighbor-list'),candidates=$('.focus-candidate-list');neighbors.replaceChildren();candidates.replaceChildren();
    array(snapshot.nodes).filter(n=>n.isNeighbor).forEach(n=>neighbors.append(topicRow(n)));
    const batch=paginate(array(snapshot.nodes).filter(n=>n.isRecommendation),page);page=batch.page;
    batch.items.forEach(n=>candidates.append(topicRow(n)));
    if(!batch.total)candidates.append(element('p',t(snapshot.status==='ready'?'empty':'local'),'focus-muted'));
    $('.focus-page').textContent=t('page',{page:batch.page,pages:batch.pageCount,count:batch.total});
    $('[data-focus-action="previous"]').disabled=batch.page<=1;$('[data-focus-action="next"]').disabled=batch.page>=batch.pageCount;
  }
  function renderDetails(){
    const detail=$('.focus-detail'),node=nodeFor(selected),topic=topicFor(selected),focused=document.activeElement;
    const restore=detail.contains(focused)?focused?.dataset.focusAction:null;
    detail.replaceChildren();detail.dataset.selectedId=node?.id||'';
    if(!node||!topic){detail.append(element('p',t('selectionHelp'),'focus-muted'));return;}
    const heading=element('div',undefined,'focus-detail-heading'),close=button('×','close-details');close.setAttribute('aria-label',t('closeDetails'));
    heading.append(element('h3',topic.topic),close);detail.append(heading,element('p',topic.domain,'focus-domain'));
    const tags=element('div',undefined,'focus-tags');
    for(const key of [node.id===snapshot.seedId?'current':null,node.isNeighbor?'neighbors':null,node.isRecommendation?'candidates':null].filter(Boolean))tags.append(element('span',t(key)));
    detail.append(tags,element('p',topic.description,'focus-description'));
    const metric=element('div',undefined,'focus-distance-metric');metric.append(element('span',t('distance')),element('strong',node.distance.toFixed(6),'focus-detail-distance'));detail.append(metric);
    const actions=element('div',undefined,'focus-detail-actions'),saved=array(state.approved).some(item=>item.id===node.id);
    const save=button(t(saved?'saved':pending.has('save')?'saving':'save'),'save');save.className='focus-primary';save.disabled=saved||pending.has('save')||typeof onSave!=='function';
    const explore=button(t('explore'),'explore');explore.disabled=node.id===snapshot.seedId||pending.has('explore')||typeof onEnterFocus!=='function';actions.append(save,explore);
    for(const action of ['google','youtube']){const search=button(t(action),action);search.disabled=pending.has(action)||typeof onSearch!=='function';actions.append(search);}
    if(node.isRecommendation){const dismiss=button(t('dismiss'),'dismiss');dismiss.disabled=pending.has('dismiss')||typeof onDismiss!=='function';actions.append(dismiss);}
    detail.append(actions);
    if(restore)detail.querySelector(`[data-focus-action="${restore}"]`)?.focus({preventScroll:true});
  }
  function renderNodes(){
    const ids=new Set(array(snapshot.nodes).map(n=>n.id));
    for(const [id,record]of records)if(!ids.has(id)){record.orb?.destroy();record.group.remove();records.delete(id);}
    for(const node of array(snapshot.nodes)){
      let record=records.get(node.id);
      if(!record){
        const group=svgElement('g',{class:'focus-node','data-focus-id':node.id},nodeLayer);
        const halo=svgElement('circle',{class:'focus-node-halo',fill:'none'},group);
        const body=svgElement('circle',{class:'focus-node-body'},group);
        const glint=svgElement('circle',{class:'focus-node-glint',fill:'#f6f2e7'},group);
        const host=svgElement('g',{class:'focus-orb-host'},group);
        const label=svgElement('text',{class:'focus-node-label','text-anchor':'middle'},group);label.textContent=topicFor(node.id).topic;
        const hit=svgElement('circle',{'data-focus-star':node.id,fill:'transparent',tabindex:0,role:'button',class:'focus-node-hit'},group);
        const title=svgElement('title',{},hit);title.textContent=topicFor(node.id).topic;
        record={group,halo,body,glint,host,label,hit,born:time};
        records.set(node.id,record);
      }
      if(node.id===snapshot.seedId&&!record.orb)record.orb=new OrbCore(record.host,defs,{idPrefix:`${prefix}-orb`,color:colorFor(node)});
      if(node.id!==snapshot.seedId&&record.orb){record.orb.destroy();record.orb=null;}
      record.group.setAttribute('transform',`translate(${node.x} ${-node.y})`);
      record.group.dataset.recommendation=String(node.isRecommendation);record.group.dataset.neighbor=String(node.isNeighbor);
      record.hit.setAttribute('aria-label',`${topicFor(node.id).topic} · ${t(node.id===snapshot.seedId?'current':node.isRecommendation?'candidates':'neighbors')} · ${node.distance.toFixed(6)}`);
    }
  }
  function renderRings(s){
    const rings=$('.focus-rings');rings.replaceChildren();
    for(const distance of [.1,.2,.3]){
      svgElement('circle',{r:1000*distance,class:'focus-distance-ring',fill:'none'},rings);
      const label=svgElement('text',{x:8/s,y:-distance*1000-7/s,'font-size':10/s,class:'focus-ring-label'},rings);label.textContent=distance.toFixed(2);
    }
  }
  function paint(dt=0){
    if(destroyed)return;
    const s=scale(),cx=viewport.width/2-camera.x*s,cy=viewport.height/2+camera.y*s;
    root.dataset.motion=reduced?'reduced':'full';map.dataset.zoom=String(camera.zoom);
    world.setAttribute('transform',`translate(${cx} ${cy}) scale(${s})`);
    renderRings(s);
    const links=$('.focus-links');links.replaceChildren();
    const labels=[],saved=new Set(array(state.approved).map(t=>t.id)),explored=new Set(array(state.explored).map(t=>t.id));
    const duration=intro==='wake'?1.1:compact?.18:.35,arrival=reduced?1:Math.min(1,age/duration);
    const waveAge=age-.2,waveRadius=Math.max(0,waveAge)*camera.extent*1.9;
    let wave=null;
    if(!reduced&&intro==='wake'&&waveAge>0&&waveAge<1.2){
      const strength=Math.max(0,1-waveAge/1.2);ripple.setAttribute('r',String(waveRadius));ripple.setAttribute('stroke-width',String(1.5/s));ripple.setAttribute('opacity',String(strength*.6));
      wave={rx:waveRadius*s,ry:waveRadius*s,strength:strength*.42};
    }else ripple.setAttribute('opacity','0');
    drawBackground(ctx,{...viewport,scale:s,camX:camera.x,camY:camera.y,cx,cy,parX,parY},{time,motion:!reduced},layers,wave);
    for(const node of array(snapshot.nodes)){
      const record=records.get(node.id);if(!record)continue;
      const isCenter=node.id===snapshot.seedId,isSelected=node.id===selected,isHovered=node.id===hovered;
      const radius=(isCenter?23:node.isRecommendation?8:6)/s;
      record.body.setAttribute('r',String(radius));record.body.setAttribute('fill',colorFor(node));record.body.hidden=isCenter;
      record.body.style.display=isCenter?'none':'';record.glint.style.display=isCenter?'none':'';
      record.glint.setAttribute('r',String(2/s));const a=Math.atan2(-node.y,-node.x);record.glint.setAttribute('cx',String(Math.cos(a)*2/s));record.glint.setAttribute('cy',String(-Math.sin(a)*2/s));record.glint.setAttribute('opacity','.45');
      record.halo.setAttribute('r',String(radius+(isCenter?7:5)/s));record.halo.setAttribute('stroke',colorFor(node));record.halo.setAttribute('stroke-width',String((isSelected?2:1)/s));
      record.halo.setAttribute('opacity',String(isSelected||isCenter||saved.has(node.id)?1:node.isRecommendation?.65:explored.has(node.id)?.75:0));
      record.halo.setAttribute('stroke-dasharray',node.isRecommendation&&!isSelected?`${2/s} ${3/s}`:'none');
      record.group.classList.toggle('is-selected',isSelected);record.group.classList.toggle('is-saved',saved.has(node.id));record.group.classList.toggle('is-explored',explored.has(node.id));
      record.hit.setAttribute('r',String((coarse.matches?22:14)/s));record.hit.setAttribute('aria-pressed',String(isSelected));
      record.host.setAttribute('transform',`scale(${23/(ORB_UNITS*s)})`);
      const fade=reduced?1:Math.min(1,(time-record.born)/.4);record.group.setAttribute('opacity',String(isCenter||isSelected?1:Math.min(arrival,fade)));
      const p=screen(node),labelWidth=Math.min(160,topicFor(node.id).topic.length*6.5);
      const box={x:p.x-labelWidth/2,y:p.y+15,width:labelWidth,height:14};
      const overlap=labels.some(b=>box.x<b.x+b.width+8&&box.x+box.width+8>b.x&&box.y<b.y+b.height+4&&box.y+box.height+4>b.y);
      const visible=isCenter||isSelected||isHovered||!overlap;
      record.label.setAttribute('y',String((isCenter?43:24)/s));record.label.setAttribute('font-size',String((isCenter?13:11)/s));
      record.label.style.display=visible?'':'none';record.label.textContent=topicFor(node.id).topic.length>25?topicFor(node.id).topic.slice(0,24)+'…':topicFor(node.id).topic;
      if(visible)labels.push(box);
      if(isSelected&& !isCenter)svgElement('line',{x1:0,y1:0,x2:node.x,y2:-node.y,class:'focus-selected-link','stroke-width':1/s},links);
      if(record.orb){
        let orbState=isSelected?'reading':hovered===node.id?'greet':hovered?'look':'idle';
        if(!reduced&&intro==='wake'&&age<.2)orbState='whole';else if(!reduced&&intro==='wake'&&age<.7)orbState='release';
        const target=nodeFor(hovered);if(target)record.orb.setLook(Math.atan2(-target.y,target.x)*180/Math.PI);
        record.orb.setState(orbState);record.orb.setSqueeze(!reduced&&intro==='wake'&&age<.2?1-.15*(age/.2):1);
        record.orb.update(reduced?0:dt,reduced);
      }
    }
  }
  function tick(timestamp){
    frame=0;if(destroyed||!active||document.hidden||reduced)return;
    const dt=lastTime?Math.min((timestamp-lastTime)/1000,.05):0;lastTime=timestamp;time+=dt;age+=dt;paint(dt);frame=requestAnimationFrame(tick);
  }
  function syncAnimation(){
    if(frame){cancelAnimationFrame(frame);frame=0;}lastTime=0;
    paint();if(!destroyed&&active&&!document.hidden&&!reduced)frame=requestAnimationFrame(tick);
  }
  function resize(){
    if(destroyed)return;
    const rect=map.getBoundingClientRect();viewport={width:Math.max(1,rect.width),height:Math.max(1,rect.height)};
    const ratio=Math.min(devicePixelRatio||1,2);canvas.width=Math.round(viewport.width*ratio);canvas.height=Math.round(viewport.height*ratio);
    ctx.setTransform(ratio,0,0,ratio,0,0);map.setAttribute('viewBox',`0 0 ${viewport.width} ${viewport.height}`);paint();
  }
  function reset(){camera=initialCamera();paint();}
  function zoom(factor,point={x:viewport.width/2,y:viewport.height/2}){
    const old=scale(),wx=camera.x+(point.x-viewport.width/2)/old,wy=camera.y-(point.y-viewport.height/2)/old;
    camera.zoom=boundedZoom(camera.zoom*factor);const next=scale();camera.x=wx-(point.x-viewport.width/2)/next;camera.y=wy+(point.y-viewport.height/2)/next;paint();
  }
  async function runAction(action,id=selected){
    if(destroyed||pending.has(action))return;
    clearClickSequence();
    const topic=topicFor(id),node=nodeFor(id);
    let callback,args;
    if(action==='back'){callback=onBack;args=[];}
    else if(action==='get-ideas'){if(snapshot.status==='loading'||!snapshot.seedId)return;callback=onGetIdeas;args=[snapshot.seedId];}
    else if(action==='explore'){if(!topic||id===snapshot.seedId)return;callback=onEnterFocus;args=[id];}
    else if(action==='save'){if(!topic||array(state.approved).some(t=>t.id===id))return;callback=onSave;args=[topic];}
    else if(action==='dismiss'){if(!node?.isRecommendation)return;callback=onDismiss;args=[id];}
    else if(action==='google'||action==='youtube'){if(!topic)return;callback=onSearch;args=[topic,action,{source:'focus',centerId:snapshot.seedId}];}
    if(typeof callback!=='function')return;
    pending.add(action);actionError=false;refreshCopy();
    try{await callback(...args);}catch{actionError=true;}finally{pending.delete(action);if(!destroyed)refreshCopy();}
  }
  on(root,'click',event=>{
    const enter=event.target.closest('[data-focus-enter]');if(enter){runAction('explore',enter.dataset.focusEnter);return;}
    const selectButton=event.target.closest('[data-focus-select]');if(selectButton){select(selectButton.dataset.focusSelect);return;}
    const action=event.target.closest('[data-focus-action]')?.dataset.focusAction;
    if(action)clearClickSequence();
    if(action==='reset')reset();else if(action==='zoom-in')zoom(1.25);else if(action==='zoom-out')zoom(.8);
    else if(action==='previous'||action==='next'){page+=action==='next'?1:-1;renderLists();}
    else if(action==='close-details'){selected=null;root.dataset.selectedId='';renderDetails();paint();focusMap();}
    else if(action)runAction(action);
  });
  on($('.focus-search'),'input',()=>{clearClickSequence();renderSearch();});
  on(map,'click',event=>{
    if(gestureMoved){lastClick=null;doubleId=null;return;}
    const id=event.target.closest('[data-focus-star]')?.dataset.focusStar;
    if(!id){lastClick=null;doubleId=null;return;}
    doubleId=lastClick?.id===id&&event.detail>=2&&event.detail%2===0?id:null;
    lastClick={id,time:event.timeStamp};activation.click(id);
  });
  on(map,'dblclick',event=>{if(gestureMoved)return;const id=event.target.closest('[data-focus-star]')?.dataset.focusStar;if(id&&doubleId===id){event.preventDefault();lastClick=null;doubleId=null;activation.doubleClick(id);}});
  on(map,'pointerover',event=>{hovered=event.target.closest('[data-focus-star]')?.dataset.focusStar||null;paint();});
  on(map,'pointerleave',()=>{hovered=null;parX=0;parY=0;paint();});
  const localPoint=event=>{const rect=map.getBoundingClientRect();return{x:event.clientX-rect.left,y:event.clientY-rect.top};};
  on(map,'pointerdown',event=>{
    if(event.button!==0)return;activation.cancel();gestureMoved=false;const p=localPoint(event);pointers.set(event.pointerId,p);
    pointerStart={...p};if(!event.target.closest('[data-focus-star]'))map.setPointerCapture(event.pointerId);
  });
  on(map,'pointermove',event=>{
    const p=localPoint(event);parX=(p.x/viewport.width-.5)*2;parY=(p.y/viewport.height-.5)*2;
    if(!pointers.has(event.pointerId)){paint();return;}
    const before=pointers.get(event.pointerId),other=[...pointers].find(([id])=>id!==event.pointerId)?.[1];
    if(other){const a=Math.hypot(before.x-other.x,before.y-other.y),b=Math.hypot(p.x-other.x,p.y-other.y);if(a>1)zoom(b/a,{x:(p.x+other.x)/2,y:(p.y+other.y)/2});gestureMoved=true;}
    else if(gestureMoved||Math.hypot(p.x-pointerStart.x,p.y-pointerStart.y)>5){camera.x-=(p.x-before.x)/scale();camera.y+=(p.y-before.y)/scale();gestureMoved=true;lastClick=null;doubleId=null;activation.cancel();}
    pointers.set(event.pointerId,p);paint();
  });
  const endPointer=event=>{pointers.delete(event.pointerId);if(map.hasPointerCapture(event.pointerId))map.releasePointerCapture(event.pointerId);if(event.type==='pointercancel'){gestureMoved=true;lastClick=null;doubleId=null;activation.cancel();}};
  on(map,'pointerup',endPointer);on(map,'pointercancel',endPointer);
  on(map,'wheel',event=>{event.preventDefault();clearClickSequence();zoom(Math.exp(-event.deltaY*.0015),localPoint(event));},{passive:false});
  on(root,'keydown',event=>{
    if(event.key==='Escape'){event.preventDefault();clearClickSequence();if(selected){selected=null;root.dataset.selectedId='';renderDetails();paint();focusMap();}else runAction('back');return;}
    const hit=event.target.closest('[data-focus-star]');
    if(hit&&(event.key==='Enter'||event.key===' ')){event.preventDefault();select(hit.dataset.focusStar);return;}
    if(event.target!==map)return;
    const step=35/scale();
    if(event.key==='ArrowLeft')camera.x-=step;else if(event.key==='ArrowRight')camera.x+=step;
    else if(event.key==='ArrowUp')camera.y+=step;else if(event.key==='ArrowDown')camera.y-=step;
    else if(event.key==='+'||event.key==='=')zoom(1.25);else if(event.key==='-')zoom(.8);else if(event.key==='Home')reset();else return;
    event.preventDefault();clearClickSequence();paint();
  });
  on(document,'visibilitychange',()=>{if(document.hidden){activation.cancel();lastClick=null;doubleId=null;}syncAnimation();});
  on(reducedQuery,'change',()=>{reduced=reducedQuery.matches;syncAnimation();});on(coarse,'change',()=>paint());
  const observer=new ResizeObserver(resize);observer.observe($('.focus-stage'));
  selected=nodeFor(selected)?selected:null;renderNodes();refreshCopy();resize();syncAnimation();
  return {
    update(next={}){
      if(destroyed)return;
      if(next.snapshot){
        const changed=next.snapshot.seedId!==snapshot.seedId;snapshot=next.snapshot;
        if(changed){activation.cancel();lastClick=null;doubleId=null;selected=null;page=1;camera=initialCamera();age=0;intro='focus';root.dataset.intro=intro;hovered=null;}
        if(!nodeFor(selected))selected=null;
      }
      if(next.state!==undefined)state=next.state;if(next.language!==undefined)language=next.language;refreshCopy();
    },
    getViewState(){return{seedId:snapshot.seedId,selected,camera:{...camera},page,woken:true};},
    setActive(value){if(destroyed)return;active=Boolean(value);if(!active){activation.cancel();lastClick=null;doubleId=null;pointers.clear();}syncAnimation();},
    destroy(){if(destroyed)return;destroyed=true;if(frame)cancelAnimationFrame(frame);frame=0;activation.destroy();observer.disconnect();cleanups.forEach(cleanup=>cleanup());records.forEach(record=>record.orb?.destroy());records.clear();root.remove();},
  };
}
