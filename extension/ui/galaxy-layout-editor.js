import {GALAXY_LAYOUT_DEFAULTS, normalizeGalaxyLayoutOptions} from '../core/galaxy-layout-options.js';

/** An epoch owns every asynchronous completion; reset, leaving and connection edits retire it. */
export function createGalaxyLayoutSession({request, poll, onReady, onChange = () => {}, schedule = (fn,ms) => setTimeout(fn,ms), cancel = id => clearTimeout(id), now = () => Date.now(), timeout = 5 * 60 * 1000}) {
  let epoch = 0, timer = null, destroyed = false, snapshot = {status:'idle',stage:'',error:null};
  const publish = patch => { snapshot = {...snapshot,...patch}; onChange({...snapshot}); };
  function invalidate() { epoch++; if (timer !== null) cancel(timer); timer = null; if (!destroyed) publish({status:'idle',stage:'',error:null}); }
  async function generate(parameters) {
    if (destroyed) return;
    invalidate(); const own = epoch, started = now(); let validated;
    const current = () => !destroyed && epoch === own;
    const fail = error => { if (current()) publish({status:'failed',stage:'',error:error instanceof Error ? error.message : String(error)}); };
    try {
      validated = normalizeGalaxyLayoutOptions(parameters,{strict:true});
      if (typeof request !== 'function' || typeof poll !== 'function') throw new Error('Layout previews need a connected backend.');
      publish({status:'running',stage:'requesting',error:null});
      async function receive(envelope, jobId = null) {
        if (!current()) return;
        if (now()-started > timeout) throw new Error('The layout preview timed out. Try again.');
        if (!envelope || typeof envelope.job_id !== 'string' || !envelope.job_id || jobId && envelope.job_id !== jobId || !['queued','running','ready','failed'].includes(envelope.status)) throw new Error('The backend returned an invalid layout job.');
        if (envelope.status === 'failed') throw new Error(envelope.error || 'The backend could not generate this layout.');
        if (envelope.status === 'ready') { onReady(envelope.result,validated); if (current()) publish({status:'ready',stage:'',error:null}); return; }
        publish({status:envelope.status,stage:typeof envelope.stage === 'string' ? envelope.stage : '',error:null});
        timer = schedule(async()=>{timer=null;if (!current()) return;try { await receive(await poll(envelope.job_id),envelope.job_id); } catch(error) { fail(error); }},3000);
      }
      await receive(await request(validated));
    } catch(error) { fail(error); }
  }
  return {generate,invalidate,getSnapshot:()=>({...snapshot}),destroy(){invalidate();destroyed=true;}};
}

export function createGalaxyLayoutEditor({host,text,getOptions,onGenerate,onReset,onSave,onClose = () => {},available = true}) {
  const panel = document.createElement('section'); panel.className='galaxy-layout-editor';panel.hidden=true;
  panel.setAttribute('aria-label',text('layoutSettings'));
  panel.innerHTML='<div class="galaxy-layout-heading"><h3></h3><button type="button" data-layout-action="close">×</button></div><p class="galaxy-layout-help"></p><div class="galaxy-layout-fields"></div><div class="galaxy-layout-actions"><button type="button" data-layout-action="generate"></button><button type="button" data-layout-action="reset"></button><button type="button" data-layout-action="save"></button></div><p class="galaxy-layout-status" role="status" aria-live="polite"></p>';
  const fields=panel.querySelector('.galaxy-layout-fields'),status=panel.querySelector('.galaxy-layout-status');
  const specs=[['n_neighbors','layoutNeighbors',5,60,1],['min_dist','layoutMinDist',0,1,.05],['spread','layoutSpread',.5,3,.1],['repulsion_strength','layoutRepulsion',.5,4,.1]];
  for(const [key,label,min,max,step] of specs){const row=document.createElement('label'),caption=document.createElement('span'),input=document.createElement('input');caption.dataset.layoutCopy=label;input.type='number';input.min=min;input.max=max;input.step=step;input.name=key;input.required=true;row.append(caption,input);fields.append(row);}
  let snapshot={status:'idle'},saving=false,alive=true;
  const inputValues=()=>{const values={};for(const [key] of specs){const raw=fields.querySelector(`[name="${key}"]`).value;if(!raw.trim())throw new Error(text('layoutRequired'));values[key]=Number(raw);}return normalizeGalaxyLayoutOptions(values,{strict:true});};
  const setValues=options=>{const normalized=normalizeGalaxyLayoutOptions(options);for(const [key] of specs)fields.querySelector(`[name="${key}"]`).value=normalized[key];};
  const showError=error=>{status.textContent=error.message||String(error);status.classList.add('is-error');};
  function copy(){panel.setAttribute('aria-label',text('layoutSettings'));panel.querySelector('h3').textContent=text('layoutSettings');panel.querySelector('[data-layout-action="close"]').setAttribute('aria-label',text('closeLayout'));panel.querySelector('.galaxy-layout-help').textContent=text('layoutHelp');panel.querySelectorAll('[data-layout-copy]').forEach(node=>node.textContent=text(node.dataset.layoutCopy));for(const [action,key] of [['generate','generatePreview'],['reset','restoreB'],['save','saveDefault']])panel.querySelector(`[data-layout-action="${action}"]`).textContent=text(key);render();}
  function renderControls(){if(!alive)return;const busy=['queued','running'].includes(snapshot.status);panel.querySelector('[data-layout-action="generate"]').disabled=!available||saving;panel.querySelector('[data-layout-action="save"]').disabled=busy||saving;panel.setAttribute('aria-busy',String(busy||saving));}
  function render(){if(!alive)return;const busy=['queued','running'].includes(snapshot.status);renderControls();status.classList.toggle('is-error',snapshot.status==='failed');status.textContent=!available?text('layoutOffline'):snapshot.status==='failed'?`${text('layoutFailed')} ${snapshot.error||''}`:busy?`${text('layoutPending')} ${snapshot.stage==='requesting'?text('layoutRequesting'):snapshot.stage==='queued'?text('layoutQueued'):['verifying_source','exact_neighbors'].includes(snapshot.stage)?text('layoutPreparing'):snapshot.stage==='placing_labels'?text('layoutFinishing'):text('layoutProjecting')}`:snapshot.status==='ready'?text('layoutReady'):'';}
  const click=async event=>{const action=event.target.closest('[data-layout-action]')?.dataset.layoutAction;if(!action)return;
    if(action==='close'){panel.hidden=true;onClose();return;}
    if(action==='reset'){onReset();setValues(GALAXY_LAYOUT_DEFAULTS);return;}
    try {const values=inputValues();if(action==='generate')await onGenerate(values);if(action==='save'){saving=true;render();await onSave(values);if(alive){status.classList.remove('is-error');status.textContent=text('layoutSaved');}}}catch(error){if(alive)showError(error);}finally{saving=false;renderControls();}
  };
  panel.addEventListener('click',click);panel.addEventListener('keydown',event=>{if(event.key==='Escape'){event.preventDefault();event.stopPropagation();panel.hidden=true;onClose();}});host.append(panel);setValues(getOptions());copy();
  return {element:panel,open(){setValues(getOptions());panel.hidden=false;copy();fields.querySelector('input').focus({preventScroll:true});},update(next){snapshot=next;render();},copy,destroy(){alive=false;panel.removeEventListener('click',click);panel.remove();}};
}
