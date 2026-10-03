import {prepareGalaxy, restoreViewState, searchTopics, topicsInDomain, defaultCamera, worldToScreen, zoomAt, panCamera, hitTest, clampCamera} from './galaxy-logic.js';
import {galaxyText} from './galaxy-i18n.js';

const COLORS = ['#8cafec', '#89ccb0', '#efae98', '#c7a4ee', '#d6cd8d', '#a2c7d9', '#da9fbb', '#93b9a0', '#ddbc91', '#a5a5d9', '#72c7c7', '#d1a587', '#c4beae', '#9daed0', '#c8abc8', '#7fc39c', '#a1c0f0', '#d5b073', '#a9ba85', '#d1a2a2', '#85bed5', '#bfa9df', '#bdbd93'];
const array = value => Array.isArray(value) ? value : [];
const element = (tag, text, className) => {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
};
function button(text, action, topic, className) {
  const node = element('button', text, className);
  node.type = 'button';
  if (action) node.dataset.galaxyAction = action;
  if (topic) node.dataset.galaxyTopic = topic;
  return node;
}

/** A local-only view. All product mutations occur through explicit callbacks. */
export function createGalaxyMap({container, catalog, layout, state = {}, language = 'en', onSave, onFocus, onSearch, viewState}) {
  const data = prepareGalaxy(catalog, layout);
  const customTopics = () => array(state.approved).filter(topic => !data.byId.has(topic.id));
  let view = restoreViewState(viewState, data, customTopics().map(topic => topic.id));
  let destroyed = false, frame = 0, viewport = {width: 0, height: 0}, hits = [], hovered = null;
  let saved = new Set(), baseline = new Set(), recommended = new Set(), explored = new Set();
  let actionError = false;
  const pending = new Set(), pointers = new Map(), cleanups = [];
  const domainColors = new Map(data.domains.map((domain, index) => [domain.id, COLORS[index % COLORS.length]]));
  const t = (key, values) => galaxyText(language, key, values);
  const root = element('div', undefined, 'galaxy-root');
  root.dataset.topicCount = String(data.topics.length);
  root.innerHTML = `<div class="galaxy-toolbar">
    <label class="galaxy-search-field"><span data-galaxy-copy="search"></span><input type="search" class="galaxy-search" maxlength="200" autocomplete="off" spellcheck="false" data-focus="galaxy-search"></label>
    <label class="galaxy-domain-field"><span data-galaxy-copy="domain"></span><select class="galaxy-domain" data-focus="galaxy-domain"></select></label>
  </div>
  <div class="galaxy-results" hidden><div class="galaxy-results-heading"><span class="galaxy-result-count" role="status"></span><button type="button" data-galaxy-action="clear-search" data-galaxy-copy="clearSearch"></button></div><div class="galaxy-result-list"></div></div>
  <div class="galaxy-body"><div class="galaxy-visual">
    <div class="galaxy-surface"><canvas class="galaxy-canvas" tabindex="0" role="img" data-focus="galaxy-canvas"></canvas>
      <div class="galaxy-map-caption" aria-hidden="true"><span class="galaxy-count"></span><span class="galaxy-filter-caption"></span></div>
      <div class="galaxy-controls"><button type="button" data-galaxy-action="zoom-out">−</button><output class="galaxy-zoom"></output><button type="button" data-galaxy-action="zoom-in">+</button><button type="button" data-galaxy-action="reset" data-galaxy-copy="reset"></button></div>
      <div class="galaxy-tooltip" hidden></div>
    </div>
    <p class="galaxy-gesture-help" data-galaxy-copy="gestures"></p>
    <div class="galaxy-legend"></div>
    <details class="galaxy-domain-key"><summary data-galaxy-copy="subjectColors"></summary><div class="galaxy-domain-colors"></div></details>
    <p class="galaxy-geometry-note" data-galaxy-copy="geometryNote"></p>
    <section class="galaxy-custom" hidden></section>
  </div><aside class="galaxy-detail" aria-label="Topic details"></aside></div>
  <div class="galaxy-announcement galaxy-sr-only" role="status" aria-live="polite"></div>`;
  container.replaceChildren(root);
  const $ = selector => root.querySelector(selector);
  const canvas = $('.galaxy-canvas'), search = $('.galaxy-search'), domainSelect = $('.galaxy-domain');
  const context = canvas.getContext('2d');
  if (!context) { root.remove(); throw new Error('The Galaxy canvas is unavailable.'); }
  const on = (target, event, handler, options) => {
    target.addEventListener(event, handler, options);
    cleanups.push(() => target.removeEventListener(event, handler, options));
  };
  const point = topic => worldToScreen(topic, view.camera, viewport, data.bounds);
  const visible = position => position.x >= -12 && position.x <= viewport.width + 12 && position.y >= -12 && position.y <= viewport.height + 12;
  const topicFor = id => data.byId.get(id) || customTopics().find(topic => topic.id === id);

  function refreshPersonalState() {
    saved = new Set(array(state.approved).map(topic => topic.id));
    baseline = new Set(array(state.baseline));
    recommended = new Set(array(state.recommendations).map(topic => topic.id));
    explored = new Set(array(state.explored).map(topic => topic.id));
    if (view.selected && !topicFor(view.selected)) view.selected = null;
  }

  function setCopy() {
    root.lang = language === 'zh-CN' ? 'zh-CN' : 'en';
    root.querySelectorAll('[data-galaxy-copy]').forEach(node => { node.textContent = t(node.dataset.galaxyCopy); });
    search.placeholder = t('searchPlaceholder');
    search.value = view.query;
    canvas.setAttribute('aria-label', t('canvas'));
    canvas.title = t('keyboard');
    $('.galaxy-detail').setAttribute('aria-label', t('neighbors'));
    for (const [action, key] of [['zoom-in', 'zoomIn'], ['zoom-out', 'zoomOut']]) {
      const node = $(`[data-galaxy-action="${action}"]`);
      node.setAttribute('aria-label', t(key)); node.title = t(key);
    }
    domainSelect.replaceChildren();
    const all = element('option', t('allDomains')); all.value = ''; domainSelect.append(all);
    data.domains.forEach(domain => { const option = element('option', domain.id); option.value = domain.id; domainSelect.append(option); });
    domainSelect.value = view.domain || '';
    $('.galaxy-results').setAttribute('aria-label', t('results'));
    const legend = $('.galaxy-legend'); legend.replaceChildren(); legend.setAttribute('aria-label', t('legend'));
    for (const [kind, label] of [['starting', 'starting'], ['saved', 'saved'], ['focus', 'currentFocus'], ['recommended', 'recommended'], ['trail', 'explorationLinks'], ['neighbor', 'nearbyLinks']]) {
      const item = element('span', undefined, 'galaxy-legend-item');
      const marker = element('i', undefined, `galaxy-marker galaxy-marker-${kind}`); marker.setAttribute('aria-hidden', 'true');
      item.append(marker, document.createTextNode(t(label))); legend.append(item);
    }
    const colors = $('.galaxy-domain-colors'); colors.replaceChildren();
    data.domains.forEach(domain => {
      const item = element('span'), swatch = element('i'); swatch.style.backgroundColor = domainColors.get(domain.id);
      swatch.setAttribute('aria-hidden', 'true'); item.append(swatch, document.createTextNode(domain.id)); colors.append(item);
    });
    renderResults(); renderDetails(); renderCustom(); scheduleDraw();
  }

  function renderResults() {
    const results = $('.galaxy-results'), list = $('.galaxy-result-list');
    results.hidden = !view.query.trim(); list.replaceChildren();
    if (results.hidden) return;
    const matches = searchTopics(data, view.query, view.domain);
    $('.galaxy-result-count').textContent = t('resultCount', {count: matches.length});
    if (!matches.length) list.append(element('p', t('noResults'), 'galaxy-muted'));
    matches.forEach(topic => {
      const item = button(undefined, 'select', topic.id, 'galaxy-result');
      item.append(element('span', topic.topic), element('small', topic.domain));
      item.setAttribute('aria-pressed', String(topic.id === view.selected)); list.append(item);
    });
  }

  function renderCustom() {
    const section = $('.galaxy-custom'), topics = customTopics();
    section.hidden = !topics.length; section.replaceChildren();
    if (!topics.length) return;
    section.append(element('h3', t('customTitle')), element('p', t('customHelp'), 'galaxy-muted'));
    const list = element('div', undefined, 'galaxy-custom-list');
    topics.forEach(topic => { const item = button(topic.topic, 'select', topic.id); item.setAttribute('aria-pressed', String(topic.id === view.selected)); list.append(item); });
    section.append(list);
  }

  function renderDetails() {
    const panel = $('.galaxy-detail'), topic = topicFor(view.selected);
    panel.replaceChildren(); delete panel.dataset.selectedId;
    if (!topic) {
      panel.classList.add('galaxy-detail-empty');
      const ornament = element('span', '✧', 'galaxy-detail-star'); ornament.setAttribute('aria-hidden', 'true');
      panel.append(ornament, element('h2', t('selectTitle')), element('p', t('selectHelp')), element('p', t('selectNote'), 'galaxy-muted'));
      return;
    }
    panel.classList.remove('galaxy-detail-empty'); panel.dataset.selectedId = topic.id;
    const heading = element('div', undefined, 'galaxy-detail-heading');
    const eyebrow = element('p', topic.domain || '', 'galaxy-eyebrow');
    const close = button('×', 'close-details', null, 'galaxy-close'); close.setAttribute('aria-label', t('closeDetails'));
    heading.append(eyebrow, close);
    const title = element('h2', topic.topic); title.tabIndex = -1;
    const statuses = element('div', undefined, 'galaxy-statuses');
    const labels = [baseline.has(topic.id) && 'starting', saved.has(topic.id) && 'saved', state.focus === topic.id && 'currentFocus', recommended.has(topic.id) && 'recommended', explored.has(topic.id) && 'explored'].filter(Boolean);
    labels.forEach(key => statuses.append(element('span', t(key), 'galaxy-status')));
    panel.append(heading, title, statuses, element('p', topic.description || t('noDescription'), 'galaxy-description'));
    const actions = element('div', undefined, 'galaxy-detail-actions');
    if (!saved.has(topic.id)) {
      const save = button(t(pending.has('save') ? 'saving' : 'save'), 'save', topic.id, 'primary'); save.disabled = pending.has('save') || typeof onSave !== 'function'; actions.append(save);
    } else {
      const focus = button(t('focus'), 'focus', topic.id, 'primary');
      focus.disabled = pending.has('focus') || typeof onFocus !== 'function'; actions.append(focus);
    }
    const google = button('Google ↗', 'google', topic.id), youtube = button('YouTube ↗', 'youtube', topic.id);
    google.setAttribute('aria-label', t('google')); youtube.setAttribute('aria-label', t('youtube'));
    google.disabled = pending.has('google') || typeof onSearch !== 'function'; youtube.disabled = pending.has('youtube') || typeof onSearch !== 'function';
    actions.append(google, youtube); panel.append(actions);
    if (actionError) { const error = element('p', t('actionError'), 'galaxy-action-error'); error.setAttribute('role', 'alert'); panel.append(error); }
    if (!data.byId.has(topic.id)) { panel.append(element('p', t('customDetail'), 'galaxy-custom-note')); return; }
    const neighbors = element('section', undefined, 'galaxy-neighbors');
    neighbors.append(element('h3', t('neighbors')), element('p', t('neighborHelp'), 'galaxy-muted'));
    const list = element('ol');
    topic.neighbors.slice(0, 10).forEach(neighbor => {
      const related = data.byId.get(neighbor.id), item = element('li'), select = button(undefined, 'select', related.id);
      select.append(element('span', related.topic), element('span', neighbor.distance.toFixed(3), 'galaxy-distance'));
      select.setAttribute('aria-label', `${related.topic}, ${t('distance')} ${neighbor.distance.toFixed(3)}`);
      item.append(select); list.append(item);
    });
    neighbors.append(list); panel.append(neighbors);
  }

  function select(id, moveCamera = true) {
    const topic = topicFor(id); if (!topic) return;
    view.selected = id; actionError = false;
    if (data.byId.has(id)) {
      if (view.domain && topic.domain !== view.domain) { view.domain = null; domainSelect.value = ''; }
      if (moveCamera) view.camera = clampCamera({x: topic.x, y: topic.y, zoom: Math.max(2.4, view.camera.zoom)}, data.bounds);
    }
    $('.galaxy-announcement').textContent = t('selectedAnnouncement', {topic: topic.topic});
    renderResults(); renderDetails(); renderCustom(); scheduleDraw();
  }

  function reset() {
    view.camera = defaultCamera(data.bounds); view.domain = null; view.query = '';
    search.value = ''; domainSelect.value = ''; hovered = null; $('.galaxy-tooltip').hidden = true;
    renderResults(); scheduleDraw();
  }

  async function invoke(action, id) {
    const topic = topicFor(id);
    if (!topic || pending.has(action)) return;
    const callback = action === 'save' ? onSave : action === 'focus' ? onFocus : onSearch;
    if (typeof callback !== 'function' || action === 'focus' && !saved.has(id)) return;
    pending.add(action); actionError = false; renderDetails();
    try {
      if (action === 'focus') await callback(id);
      else if (action === 'save') await callback({id: topic.id, topic: topic.topic, domain: topic.domain, description: topic.description});
      else await callback({id: topic.id, topic: topic.topic, domain: topic.domain, description: topic.description}, action);
    } catch { actionError = true; }
    finally { pending.delete(action); if (!destroyed) renderDetails(); }
  }

  function scheduleDraw() {
    if (!destroyed && !frame) frame = requestAnimationFrame(() => { frame = 0; draw(); });
  }

  function draw() {
    if (destroyed || !viewport.width || !viewport.height) return;
    const c = context, {width: w, height: h} = viewport;
    const ratio = Math.min(window.devicePixelRatio || 1, 2);
    c.setTransform(ratio, 0, 0, ratio, 0, 0); c.clearRect(0, 0, w, h);
    // Decorative distant stars never represent catalog topics or receive hit targets.
    for (let i = 0; i < 120; i++) {
      const x = ((i * 137.507) % 1000) / 1000 * w, y = ((i * 239.117) % 1000) / 1000 * h;
      c.fillStyle = i % 8 ? '#b8cddd20' : '#dde7e744'; c.fillRect(x, y, i % 8 ? .8 : 1.3, i % 8 ? .8 : 1.3);
    }
    const positions = new Map(data.topics.map(topic => [topic.id, point(topic)]));
    for (const domain of data.domains) {
      if (view.domain && domain.id !== view.domain) continue;
      const p = point(domain); if (!visible(p)) continue;
      const radius = Math.min(w, h) * .2;
      const glow = c.createRadialGradient(p.x, p.y, 0, p.x, p.y, radius);
      glow.addColorStop(0, `${domainColors.get(domain.id)}0b`); glow.addColorStop(1, `${domainColors.get(domain.id)}00`);
      c.fillStyle = glow; c.fillRect(p.x - radius, p.y - radius, radius * 2, radius * 2);
    }
    const link = (fromId, toId, neighbor = false) => {
      const a = positions.get(fromId), b = positions.get(toId);
      if (!a || !b || !visible(a) && !visible(b)) return;
      if (view.domain && (data.byId.get(fromId).domain !== view.domain || data.byId.get(toId).domain !== view.domain)) return;
      c.lineWidth = neighbor ? 1 : 1.5; c.strokeStyle = neighbor ? '#a5bee877' : '#d7c99aaa';
      c.setLineDash(neighbor ? [3, 5] : []); c.beginPath(); c.moveTo(a.x, a.y);
      if (neighbor) c.lineTo(b.x, b.y);
      else { const curve = Math.min(45, Math.hypot(a.x - b.x, a.y - b.y) * .18); c.quadraticCurveTo((a.x + b.x) / 2 + curve, (a.y + b.y) / 2 - curve, b.x, b.y); }
      c.stroke(); c.setLineDash([]);
    };
    array(state.edges).forEach(edge => link(edge.from, edge.to));
    const selected = data.byId.get(view.selected), related = new Set(selected?.neighbors.slice(0, 10).map(neighbor => neighbor.id) || []);
    if (selected) selected.neighbors.slice(0, 10).forEach(neighbor => link(selected.id, neighbor.id, true));
    hits = [];
    for (const topic of data.topics) {
      const p = positions.get(topic.id); if (!visible(p)) continue;
      const match = !view.domain || topic.domain === view.domain;
      const isSelected = topic.id === view.selected, isFocus = topic.id === state.focus;
      const personal = saved.has(topic.id) || recommended.has(topic.id) || explored.has(topic.id);
      c.globalAlpha = match ? isSelected || isFocus || personal || related.has(topic.id) ? 1 : .72 : .065;
      const radius = isSelected ? 5.7 : isFocus ? 5 : personal ? 3.5 : related.has(topic.id) ? 3 : Math.min(2.7, 1.7 + view.camera.zoom * .12);
      c.fillStyle = domainColors.get(topic.domain);
      if (match && (isSelected || isFocus || personal)) { c.shadowColor = c.fillStyle; c.shadowBlur = isSelected ? 15 : 9; }
      c.beginPath(); c.arc(p.x, p.y, radius, 0, Math.PI * 2); c.fill(); c.shadowBlur = 0;
      if (match && (saved.has(topic.id) || isSelected || isFocus || recommended.has(topic.id))) {
        c.strokeStyle = isSelected ? '#f0ecdf' : isFocus ? '#d7c99a' : saved.has(topic.id) ? '#bccfc5' : '#c3b1dd';
        c.lineWidth = isSelected || isFocus ? 1.7 : 1;
        c.setLineDash(recommended.has(topic.id) && !saved.has(topic.id) && !isSelected ? [2, 2] : []);
        c.beginPath(); c.arc(p.x, p.y, radius + (isFocus ? 4 : 2.5), 0, Math.PI * 2); c.stroke(); c.setLineDash([]);
      }
      if (match && baseline.has(topic.id)) { c.strokeStyle = '#f0ecdf'; c.lineWidth = 1.2; c.beginPath(); c.moveTo(p.x - 2, p.y); c.lineTo(p.x + 2, p.y); c.moveTo(p.x, p.y - 2); c.lineTo(p.x, p.y + 2); c.stroke(); }
      if (match) hits.push({id: topic.id, x: p.x, y: p.y});
    }
    c.globalAlpha = 1;
    const boxes = [];
    function label(text, position, color, major = false) {
      if (!visible(position) || position.y < 50 || position.y > h - 55) return;
      c.font = `${major ? '500' : '400'} ${major ? 12 : 11}px -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif`;
      const maxWidth = Math.min(w - 30, major ? 235 : 190); let title = text;
      while (c.measureText(title).width > maxWidth && title.length > 3) title = title.slice(0, -2);
      if (title !== text) title = title.slice(0, -1) + '…';
      const width = c.measureText(title).width;
      for (const offset of [-14, 23, -35, 44]) {
        const x = Math.max(9, Math.min(w - width - 9, position.x + 10)), y = position.y + offset;
        const box = {x: x - 5, y: y - 13, width: width + 10, height: 20};
        if (box.y < 46 || y > h - 52 || boxes.some(b => box.x < b.x + b.width + 4 && box.x + box.width + 4 > b.x && box.y < b.y + b.height + 3 && box.y + box.height + 3 > b.y)) continue;
        boxes.push(box); c.fillStyle = '#0b1523df'; c.fillRect(box.x, box.y, box.width, box.height); c.fillStyle = color; c.fillText(title, x, y); return;
      }
    }
    const priorityIds = [...new Set([view.selected, state.focus, hovered, ...saved, ...recommended])];
    for (const id of priorityIds.slice(0, w < 450 ? 7 : 16)) {
      const topic = data.byId.get(id);
      if (topic && (!view.domain || topic.domain === view.domain)) label(topic.topic, positions.get(id), id === view.selected ? '#f0ecdf' : '#d6e2df', true);
    }
    const labelDomains = view.domain ? data.domains.filter(domain => domain.id === view.domain) : data.domains;
    let domainLabels = 0;
    for (const domain of labelDomains) {
      if (domainLabels >= (w < 450 ? 5 : 11)) break;
      const before = boxes.length; label(domain.id, point(domain), domainColors.get(domain.id));
      if (before !== boxes.length) domainLabels++;
    }
    $('.galaxy-count').textContent = t('count', {count: topicsInDomain(data, view.domain).length.toLocaleString(language)});
    $('.galaxy-filter-caption').textContent = view.domain || t('allDomains');
    $('.galaxy-zoom').textContent = `${Math.round(view.camera.zoom * 100)}%`;
    canvas.dataset.zoom = String(view.camera.zoom); canvas.dataset.centerX = String(view.camera.x); canvas.dataset.centerY = String(view.camera.y);
    root.dataset.domain = view.domain || ''; root.dataset.selectedId = view.selected || '';
  }

  function resize() {
    if (destroyed) return;
    const rect = canvas.getBoundingClientRect(); viewport = {width: rect.width, height: rect.height};
    const ratio = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.round(rect.width * ratio); canvas.height = Math.round(rect.height * ratio);
    scheduleDraw();
  }
  function localPointer(event) {
    const rect = canvas.getBoundingClientRect(); return {x: event.clientX - rect.left, y: event.clientY - rect.top};
  }
  function zoom(factor, pointer = {x: viewport.width / 2, y: viewport.height / 2}) {
    view.camera = zoomAt(view.camera, factor, pointer, viewport, data.bounds); scheduleDraw();
  }
  function showHover(pointer) {
    const id = hitTest(hits, pointer, 10), tooltip = $('.galaxy-tooltip');
    if (hovered !== id) { hovered = id; scheduleDraw(); }
    canvas.style.cursor = id ? 'pointer' : 'grab'; tooltip.hidden = !id;
    if (id) {
      tooltip.textContent = data.byId.get(id).topic;
      tooltip.style.left = `${Math.max(8, Math.min(viewport.width - 205, pointer.x + 14))}px`;
      tooltip.style.top = `${Math.max(8, Math.min(viewport.height - 85, pointer.y + 14))}px`;
    }
  }
  on(root, 'click', event => {
    const target = event.target.closest('button[data-galaxy-action]'); if (!target || !root.contains(target)) return;
    const action = target.dataset.galaxyAction, id = target.dataset.galaxyTopic;
    if (action === 'select') { select(id); $('.galaxy-detail h2')?.focus({preventScroll: true}); }
    else if (action === 'reset') reset();
    else if (action === 'zoom-in') zoom(1.3);
    else if (action === 'zoom-out') zoom(1 / 1.3);
    else if (action === 'clear-search') { view.query = ''; search.value = ''; renderResults(); search.focus(); }
    else if (action === 'close-details') { view.selected = null; renderDetails(); renderResults(); renderCustom(); scheduleDraw(); }
    else invoke(action, id);
  });
  on(search, 'input', () => { view.query = search.value; renderResults(); });
  on(search, 'keydown', event => {
    if (event.key === 'Escape') { view.query = ''; search.value = ''; renderResults(); }
    if (event.key === 'ArrowDown') { const first = $('.galaxy-result'); if (first) { event.preventDefault(); first.focus(); } }
    if (event.key === 'Enter') { const first = searchTopics(data, view.query, view.domain, 1)[0]; if (first) { event.preventDefault(); select(first.id); } }
  });
  on(domainSelect, 'change', () => {
    view.domain = domainSelect.value || null;
    const selected = data.byId.get(view.selected); if (selected && view.domain && selected.domain !== view.domain) view.selected = null;
    renderResults(); renderDetails(); scheduleDraw();
  });
  on(canvas, 'wheel', event => {
    event.preventDefault(); const delta = event.deltaY * (event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? viewport.height : 1);
    zoom(Math.exp(-Math.max(-500, Math.min(500, delta)) * .0015), localPointer(event));
  }, {passive: false});
  on(canvas, 'keydown', event => {
    if (['+', '=', '-', '_', 'Home', 'ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Escape'].includes(event.key)) event.preventDefault();
    const step = event.shiftKey ? 90 : 36;
    if (event.key === '+' || event.key === '=') zoom(1.25);
    else if (event.key === '-' || event.key === '_') zoom(.8);
    else if (event.key === 'Home') reset();
    else if (event.key === 'Escape') { view.selected = null; renderDetails(); scheduleDraw(); }
    else if (event.key.startsWith('Arrow')) {
      view.camera = panCamera(view.camera, event.key === 'ArrowLeft' ? step : event.key === 'ArrowRight' ? -step : 0, event.key === 'ArrowUp' ? step : event.key === 'ArrowDown' ? -step : 0, viewport, data.bounds); scheduleDraw();
    }
  });
  on(canvas, 'pointerdown', event => {
    if (event.button !== 0) return;
    const position = localPointer(event); pointers.set(event.pointerId, {...position, start: position, moved: false});
    if (pointers.size > 1) pointers.forEach(pointer => { pointer.moved = true; });
    canvas.setPointerCapture(event.pointerId); canvas.style.cursor = 'grabbing'; $('.galaxy-tooltip').hidden = true;
  });
  on(canvas, 'pointermove', event => {
    const current = pointers.get(event.pointerId), next = localPointer(event);
    if (!current) { if (event.pointerType !== 'touch') showHover(next); return; }
    const before = [...pointers.values()].map(pointer => ({...pointer}));
    const moved = current.moved || Math.hypot(next.x - current.start.x, next.y - current.start.y) > 5;
    pointers.set(event.pointerId, {...current, ...next, moved});
    if (pointers.size === 1 && moved) view.camera = panCamera(view.camera, next.x - current.x, next.y - current.y, viewport, data.bounds);
    else if (pointers.size === 2) {
      const after = [...pointers.values()];
      const mid = pair => ({x: (pair[0].x + pair[1].x) / 2, y: (pair[0].y + pair[1].y) / 2});
      const distance = pair => Math.hypot(pair[0].x - pair[1].x, pair[0].y - pair[1].y);
      const a = mid(before), b = mid(after), previousDistance = distance(before);
      if (previousDistance > 1) view.camera = zoomAt(view.camera, distance(after) / previousDistance, a, viewport, data.bounds);
      view.camera = panCamera(view.camera, b.x - a.x, b.y - a.y, viewport, data.bounds);
    }
    scheduleDraw();
  });
  const release = (event, cancel = false) => {
    const pointer = pointers.get(event.pointerId); if (!pointer) return;
    pointers.delete(event.pointerId);
    if (canvas.hasPointerCapture(event.pointerId)) canvas.releasePointerCapture(event.pointerId);
    if (!cancel && !pointer.moved && !pointers.size) { const id = hitTest(hits, localPointer(event), event.pointerType === 'touch' ? 20 : 12); if (id) select(id, false); }
    canvas.style.cursor = pointers.size ? 'grabbing' : 'grab';
  };
  on(canvas, 'pointerup', event => release(event));
  on(canvas, 'pointercancel', event => release(event, true));
  on(canvas, 'lostpointercapture', event => { pointers.delete(event.pointerId); });
  on(canvas, 'pointerleave', () => { hovered = null; $('.galaxy-tooltip').hidden = true; scheduleDraw(); });
  const observer = new ResizeObserver(resize); observer.observe(canvas);
  on(window, 'resize', resize);
  refreshPersonalState(); setCopy(); resize();

  return {
    update(patch = {}) {
      if (destroyed) return;
      if (patch.state !== undefined) state = patch.state;
      if (patch.language !== undefined) language = patch.language;
      refreshPersonalState(); setCopy();
    },
    getViewState() { return {...view, camera: {...view.camera}}; },
    destroy() {
      if (destroyed) return;
      destroyed = true; observer.disconnect(); cleanups.forEach(cleanup => cleanup());
      for (const id of pointers.keys()) if (canvas.hasPointerCapture(id)) canvas.releasePointerCapture(id);
      pointers.clear(); if (frame) cancelAnimationFrame(frame); root.remove();
    },
  };
}
