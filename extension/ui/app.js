import { getState, dispatch, importHistory, recommend, search, subscribe } from '../bridge.js';

const app = document.querySelector('#app');
const preview = new URLSearchParams(location.search).get('preview') === '1';
const ui = {
  view: 'discover', manual: '', days: '30', selected: new Set(), inboxOpen: true,
  mapSelection: null, settingsDraft: null, settingsDirty: false, settingsSaved: false,
  pending: new Set(), error: null, announcement: '', loaded: false,
};
let state = null;
let mapObserver;
let unsubscribe;

const escape = value => String(value ?? '').replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]));
const arr = value => Array.isArray(value) ? value : [];
const topicId = topic => topic?.id || topic?.topic || '';
const topicTitle = topic => topic?.topic || topic?.id || '';
const busy = key => ui.pending.has(key);
const disabled = value => value ? ' disabled' : '';
const checked = value => value ? ' checked' : '';
const getTopic = id => [...arr(state?.approved), ...arr(state?.recommendations), ...arr(state?.explored), ...arr(state?.candidates)].find(topic => topicId(topic) === id);
const isApproved = id => arr(state?.approved).some(topic => topicId(topic) === id);

function snapshotSettings() {
  const settings = state?.settings || {};
  return {
    endpoint: settings.endpoint || 'http://127.0.0.1:8000', accessToken: settings.accessToken || '',
    blockedDomains: arr(settings.blockedDomains).join('\n'),
  };
}

function applyState(next) {
  if (!next || typeof next !== 'object') return;
  state = next;
  ui.loaded = true;
  const candidates = new Set(arr(state.candidates).map(topicId));
  ui.selected = new Set([...ui.selected].filter(id => candidates.has(id)));
  if (!ui.settingsDirty) ui.settingsDraft = snapshotSettings();
  render();
}

async function run(key, operation, announcement) {
  if (busy(key)) return;
  ui.pending.add(key);
  ui.error = null;
  render();
  try {
    const next = await operation();
    if (next) applyState(next);
    if (announcement && !next?.lastError) ui.announcement = announcement;
    return next;
  } catch (error) {
    ui.error = error?.message || 'Something went wrong. Please try again.';
  } finally {
    ui.pending.delete(key);
    render();
  }
}

function render() {
  const focused = document.activeElement;
  const focusKey = focused?.dataset?.focus;
  const selection = focused && 'selectionStart' in focused ? [focused.selectionStart, focused.selectionEnd] : null;
  mapObserver?.disconnect();
  const error = ui.error || state?.lastError;
  app.setAttribute('aria-busy', String(!ui.loaded));
  app.innerHTML = `<div class="app-shell">
    <header class="app-header"><span class="brand">OtherWise<span class="brand-star" aria-hidden="true">✦</span></span>
      <span class="connection-label${error ? ' has-error' : ''}">${!ui.loaded ? 'Opening…' : error ? 'Needs attention' : preview ? 'Demo preview' : 'Saved on this device'}</span>
    </header>
    ${preview ? '<div class="demo-notice"><strong>Demo preview</strong> · These are sample interests and exploration paths. This preview does not read your browser history.</div>' : ''}
    <nav class="main-nav" aria-label="Main navigation">${[['discover', 'Discover'], ['map', 'Map'], ['settings', 'Settings']].map(([view, label]) => `<button type="button" data-action="view" data-view="${view}" data-focus="nav-${view}"${ui.view === view ? ' aria-current="page"' : ''}>${label}</button>`).join('')}</nav>
    ${error ? `<div class="error-banner" role="alert"><p><strong>Couldn’t finish that.</strong><br>${escape(error)}${ui.view !== 'settings' ? '<br>Check the service connection in Settings, then try again.' : ''}</p><button type="button" class="quiet" data-action="clear-error" aria-label="Dismiss error">×</button></div>` : ''}
    <main id="main-view">${!ui.loaded ? loadingView() : ui.view === 'settings' ? settingsView() : ui.view === 'map' ? mapView() : discoverView()}</main>
    <footer class="app-footer">A search is a step into a subject. Save an interest when it feels like yours.</footer>
    <div class="sr-only" role="status" aria-live="polite">${escape(ui.announcement)}</div>
  </div>`;
  bindEvents();
  if (ui.view === 'map' && ui.loaded) drawMap();
  if (focusKey) {
    const target = [...app.querySelectorAll('[data-focus]')].find(element => element.dataset.focus === focusKey);
    if (target) {
      target.focus({ preventScroll: true });
      if (selection && typeof target.setSelectionRange === 'function' && target.type !== 'number') {
        try { target.setSelectionRange(...selection); } catch { /* A non-text input has no selection. */ }
      }
    }
  }
}

function loadingView() {
  return `<section class="empty-state"><h1>Your world, a little wider.</h1><p>Opening your saved interests…</p>${ui.error ? '<button type="button" data-action="reload">Try again</button>' : ''}</section>`;
}

function discoverView() {
  const approved = arr(state.approved);
  const candidates = arr(state.candidates);
  const items = arr(state.recommendations);
  const mode = state.settings?.mode || 'path';
  return `<section class="hero"><span class="little-star" aria-hidden="true">✧</span><p class="eyebrow">Follow your curiosity</p><h1>Your world,<br>a little wider.</h1><p>Start with what you love. Find a nearby subject you might never have thought to explore.</p></section>
    ${!approved.length && !arr(state.baseline).length ? `<div class="intro"><p><strong>A small beginning is enough.</strong> Add an interest, or review topics found in your recent Chrome visits.</p><p class="small">Browsing topics stay on this device until you confirm them. Only your saved interest names are shared with the recommendation service.</p></div>` : ''}
    <form class="manual-form" id="manual-form"><label class="sr-only" for="manual-interest">Add an interest</label><input id="manual-interest" data-focus="manual-interest" name="interest" placeholder="An interest, a subject, a curiosity…" maxlength="120" value="${escape(ui.manual)}" autocomplete="off"><button class="primary" data-focus="add-interest" type="submit"${disabled(busy('add'))}>${busy('add') ? 'Saving…' : 'Add'}</button></form>
    <div class="import-row"><button type="button" data-action="import"${disabled(busy('import'))}>${busy('import') ? 'Reviewing visits…' : 'Review recent browsing'}</button><label class="sr-only" for="history-days">History review period</label><select id="history-days" data-focus="history-days"${disabled(busy('import'))}><option value="7"${ui.days === '7' ? ' selected' : ''}>Past 7 days</option><option value="30"${ui.days === '30' ? ' selected' : ''}>Past 30 days</option></select></div>
    ${candidates.length ? inboxView(candidates) : ''}
    <section class="section" aria-labelledby="interests-title"><div class="section-heading"><h2 id="interests-title">Your interests</h2>${approved.length ? '<span class="muted small">Saved by you</span>' : ''}</div>${approved.length ? `<div class="interests">${approved.map(topic => `<span class="interest-chip"><span>${escape(topicTitle(topic))}</span><button type="button" data-action="remove" data-id="${escape(topicId(topic))}" aria-label="Remove ${escape(topicTitle(topic))} from interests">×</button></span>`).join('')}</div>` : '<p class="muted small">Your first saved interest will be your starting point.</p>'}</section>
    <section class="section" aria-labelledby="recommendations-title"><div class="section-heading"><h2 id="recommendations-title">A little beyond</h2></div>
    <div class="discovery-toolbar"><label class="sr-only" for="discovery-mode">Discovery mode</label><select id="discovery-mode" data-focus="discovery-mode"><option value="path"${mode === 'path' ? ' selected' : ''}>Follow a path</option><option value="global"${mode === 'global' ? ' selected' : ''}>Explore across interests</option></select><button type="button" data-action="recommend"${disabled(!approved.length || busy('recommend'))}>${busy('recommend') ? 'Finding subjects…' : items.length ? 'Refresh ideas' : 'Find ideas'} <span aria-hidden="true">↗</span></button></div>
    ${approved.length ? `<p class="focus-note">${mode === 'path' ? `Starting near <strong>${escape(state.focus || topicTitle(approved.at(-1)))}</strong>. Your most recently saved interest guides this path.` : 'Drawing from all your saved interests. The range grows only when you confirm a new interest.'}</p>` : ''}
    ${items.length ? `<div class="recommendations">${items.map(cardView).join('')}</div>` : `<div class="empty-state"><div class="empty-symbol" aria-hidden="true">✧</div><h3>${approved.length ? 'There’s room for something new.' : 'A beginning, not a blank page.'}</h3><p>${approved.length ? 'Find ideas around your interests. If the service is unavailable, your saved interests and map are still here.' : 'Save an interest above. Your first discoveries will appear here.'}</p></div>`}
    ${state.lastUpdated ? `<p class="last-updated">Ideas updated ${escape(formatTime(state.lastUpdated))}</p>` : ''}</section>`;
}

function inboxView(candidates) {
  return `<details class="candidate-inbox"${ui.inboxOpen ? ' open' : ''}><summary data-focus="inbox-summary">Waiting for your say <span class="count">${candidates.length} ${candidates.length === 1 ? 'topic' : 'topics'}</span></summary><p class="helper muted small">A visit can mean many things. Choose only the subjects you want to save as interests.</p><div>${candidates.map(topic => `<div class="candidate-row"><label><input type="checkbox" data-candidate="${escape(topicId(topic))}" data-focus="candidate-${escape(topicId(topic))}"${checked(ui.selected.has(topicId(topic)))}><span class="candidate-copy"><span class="topic">${escape(topicTitle(topic))}</span><span class="domain">${escape(topic.domain || 'Other subjects')} · Found in local browsing</span></span></label><button class="quiet" type="button" data-action="dismiss" data-id="${escape(topicId(topic))}" aria-label="Dismiss ${escape(topicTitle(topic))}">Dismiss</button></div>`).join('')}</div><div class="inbox-actions"><button class="primary" type="button" data-action="approve"${disabled(!ui.selected.size || busy('approve'))}>${busy('approve') ? 'Saving…' : `Save selected${ui.selected.size ? ` (${ui.selected.size})` : ''}`}</button><button class="quiet" type="button" data-action="select-all">${ui.selected.size === candidates.length ? 'Clear selection' : 'Select all'}</button></div></details>`;
}

function cardView(topic) {
  const id = topicId(topic);
  const saved = isApproved(id);
  return `<article class="recommendation-card"><p class="eyebrow">${escape(topic.domain || 'A new direction')}</p><h3>${escape(topicTitle(topic))}</h3><p>${escape(topic.description || 'A subject to explore at your own pace.')}</p>${topic.nearest_interest ? `<div class="related">A connection from ${escape(topic.nearest_interest)}</div>` : ''}<div class="card-search">${searchButtons(topic)}</div><div class="card-feedback">${saved ? '<span class="saved-label">Saved to your interests</span>' : `<button type="button" class="save" data-action="save-topic" data-id="${escape(id)}"${disabled(busy(`save:${id}`))}>+ Save interest</button>`}<button type="button" class="quiet" data-action="dismiss" data-id="${escape(id)}">Not for me</button></div></article>`;
}

function searchButtons(topic) {
  const id = topicId(topic);
  return `<button type="button" data-action="search" data-id="${escape(id)}" data-provider="google"${disabled(busy(`search:${id}:google`))}>Google <span aria-hidden="true">↗</span></button><button type="button" data-action="search" data-id="${escape(id)}" data-provider="youtube"${disabled(busy(`search:${id}:youtube`))}>YouTube <span aria-hidden="true">↗</span></button>`;
}

function settingsView() {
  const settings = state.settings || {};
  const draft = ui.settingsDraft || snapshotSettings();
  return `<section class="settings"><div class="view-heading"><p class="eyebrow">Make it yours</p><h1>A little intention.</h1><p>You choose what becomes an interest, when to find new ideas, and what stays out of browsing review.</p></div>
    <section class="settings-group"><h2>Discovery</h2><label class="field"><span>How ideas connect</span><select id="settings-mode" data-focus="settings-mode" aria-label="How ideas connect"><option value="path"${settings.mode !== 'global' ? ' selected' : ''}>Follow the latest saved interest</option><option value="global"${settings.mode === 'global' ? ' selected' : ''}>Explore across all saved interests</option></select><small>Saving a new interest changes the direction. Searching a subject records exploration.</small></label>
    <label class="toggle-row"><input id="browsing-enabled" type="checkbox" aria-label="Review new browsing locally" aria-describedby="browsing-help" data-focus="browsing-enabled"${checked(settings.browsingEnabled)}${disabled(busy('browsing'))}><span><strong>Review new browsing locally</strong><small id="browsing-help">Find candidate topics from new Chrome visits, including YouTube. You still confirm every new interest. Turning this off stops new review; paused visits are not reviewed later.</small></span></label>
    <label class="toggle-row"><input id="auto-refresh" type="checkbox" aria-label="Refresh ideas when interests change" aria-describedby="refresh-help" data-focus="auto-refresh"${checked(settings.autoRefresh)}${disabled(busy('auto-refresh'))}><span><strong>Refresh ideas when interests change</strong><small id="refresh-help">Automatically ask the service for ideas after you change your saved interests. This is separate from browsing review.</small></span></label></section>
    <form class="settings-form" id="settings-form"><section class="settings-group"><h2>Service connection</h2><p class="muted small">For the shared demo, use the address and team access code provided by your host.</p><label class="field"><span>Service address</span><input id="endpoint" name="endpoint" type="url" aria-label="Service address" aria-describedby="endpoint-help" data-focus="endpoint" value="${escape(draft.endpoint)}" placeholder="https://your-demo-address" spellcheck="false" autocomplete="off" required><small id="endpoint-help">Use an HTTPS address, or the local service on this computer.</small></label><label class="field"><span>Team access code</span><input id="access-token" name="accessToken" type="password" aria-label="Team access code" aria-describedby="token-help" data-focus="access-token" value="${escape(draft.accessToken)}" placeholder="Enter the team access code" autocomplete="off" spellcheck="false"><small id="token-help">Stored on this device. It is sent only to your configured recommendation service.</small></label></section>
    <section class="settings-group"><h2>Excluded websites</h2><p class="muted small">Visits to these domains are skipped. Include a domain such as mail.example.com, one per line. Subdomains are included.</p><label class="field"><span>Domains to skip</span><textarea id="blocked-domains" name="blockedDomains" aria-label="Domains to skip" aria-describedby="domains-help" data-focus="blocked-domains" spellcheck="false">${escape(draft.blockedDomains)}</textarea><small id="domains-help">Exclusions help reduce sensitive data collection, but cannot identify every sensitive topic.</small></label></section>
    <div class="actions"><button class="primary" data-focus="save-settings" type="submit"${disabled(busy('settings'))}>${busy('settings') ? 'Saving…' : 'Save settings'}</button><span class="muted" role="status">${ui.settingsDirty ? 'You have unsaved changes.' : ui.settingsSaved ? 'Settings saved.' : ''}</span></div></form>
    <section class="settings-group"><h2>Your local data</h2><p class="muted small">Clear browsing-derived topics while keeping the interests you saved and the paths you explored, or start over completely.</p><div class="data-actions"><button type="button" data-action="clear-derived">Clear browsing data</button><button type="button" class="danger" data-action="reset">Reset OtherWise</button></div></section>
    <p class="privacy-note">Raw visit titles and addresses stay local. Only saved interest names and discovery preferences reach the service; the service and tunnel also receive network information. No account-wide YouTube history is imported.</p></section>`;
}

function mapView() {
  const topics = mapTopics();
  const selected = topics.find(topic => topicId(topic) === ui.mapSelection);
  return `<section><div class="view-heading"><p class="eyebrow">Your curiosity, connected</p><h1>A world taking shape.</h1><p>Saved interests give you a starting point. Subjects you search through OtherWise show where you’ve ventured.</p></div>
    <div class="map-legend" aria-label="Map legend"><span><i class="legend-dot baseline" aria-hidden="true"></i>Starting interest</span><span><i class="legend-dot" aria-hidden="true"></i>Saved interest</span><span><i class="legend-dot explored" aria-hidden="true"></i>Explored</span></div>
    ${topics.length ? '<div class="map-surface" id="map-surface"></div><p class="muted small map-helper">Choose a subject to explore it. Lines follow searches you made through OtherWise.</p>' : '<div class="empty-state"><div class="empty-symbol" aria-hidden="true">✧</div><h3>Your first point is waiting.</h3><p>Save an interest in Discover. Search a suggested subject to begin a path on your map.</p><button type="button" data-action="view" data-view="discover">Start in Discover</button></div>'}
    <div class="map-detail" aria-live="polite">${selected ? `<p class="eyebrow">${escape(selected.domain || 'Other subjects')} · ${isApproved(topicId(selected)) ? 'Saved interest' : 'Explored subject'}</p><h3>${escape(topicTitle(selected))}</h3><p>${escape(selected.description || 'Follow this subject a little further.')}</p><div class="card-search">${searchButtons(selected)}${isApproved(topicId(selected)) ? `<button type="button" data-action="set-focus" data-id="${escape(topicId(selected))}"${disabled(busy('focus'))}>Explore from here</button>` : `<button type="button" data-action="save-topic" data-id="${escape(topicId(selected))}">+ Save interest</button>`}</div>` : topics.length ? '<p>Every point is an interest you saved or a subject you chose to search. Exploration does not imply expertise.</p>' : ''}</div></section>`;
}

function mapTopics() {
  const topics = new Map();
  arr(state?.explored).forEach(topic => topics.set(topicId(topic), topic));
  arr(state?.approved).forEach(topic => topics.set(topicId(topic), topic));
  return [...topics.values()];
}

function drawMap() {
  const surface = document.querySelector('#map-surface');
  if (!surface) return;
  let lastWidth = 0;
  const draw = () => {
    const width = Math.max(260, surface.clientWidth);
    if (width === lastWidth) return;
    lastWidth = width;
    const columns = width > 760 ? 3 : width > 500 ? 2 : 1;
    const columnWidth = width / columns;
    const groups = new Map();
    mapTopics().forEach(topic => { const domain = topic.domain || 'Other subjects'; if (!groups.has(domain)) groups.set(domain, []); groups.get(domain).push(topic); });
    const domains = [...groups];
    const positions = new Map();
    const blocks = [];
    let top = 24;
    for (let row = 0; row < domains.length; row += columns) {
      const rowGroups = domains.slice(row, row + columns);
      const rowHeight = Math.max(...rowGroups.map(([, topics]) => 58 + topics.length * 59));
      rowGroups.forEach(([domain, topics], column) => {
        const left = column * columnWidth + 23;
        const maxDomainChars = Math.max(18, Math.floor((columnWidth - 46) / 6.5));
        const domainLabel = domain.length > maxDomainChars ? `${domain.slice(0, maxDomainChars - 1)}…` : domain;
        blocks.push(`<text class="domain-label" x="${left}" y="${top + 9}" aria-label="${escape(domain)}"><title>${escape(domain)}</title>${escape(domainLabel.toUpperCase())}</text><path class="domain-line" d="M ${left} ${top + 22} H ${left + columnWidth - 46}"/>`);
        topics.forEach((topic, index) => positions.set(topicId(topic), { x: left + 13, y: top + 57 + index * 59, topic }));
      });
      top += rowHeight;
    }
    const edges = arr(state.edges).filter(edge => positions.has(edge.from) && positions.has(edge.to)).map(edge => {
      const from = positions.get(edge.from), to = positions.get(edge.to);
      const curve = Math.min(from.x, to.x) - 18;
      if (Math.abs(from.y - to.y) < 1) return `<path class="map-edge" d="M ${from.x} ${from.y} C ${from.x} ${from.y + 32}, ${to.x} ${to.y + 32}, ${to.x} ${to.y}"/>`;
      return `<path class="map-edge" d="M ${from.x} ${from.y} C ${curve} ${from.y}, ${curve} ${to.y}, ${to.x} ${to.y}"/>`;
    }).join('');
    const baseline = new Set(arr(state.baseline));
    const nodes = [...positions].map(([id, { x, y, topic }]) => {
      const approved = isApproved(id);
      const lines = wrapLabel(topicTitle(topic), Math.max(18, Math.floor((columnWidth - 92) / 6.2)));
      return `<g class="map-node${approved ? '' : ' is-explored'}${ui.mapSelection === id ? ' selected' : ''}" data-map-id="${escape(id)}" data-focus="map-${escape(id)}" tabindex="0" role="button" aria-label="${escape(topicTitle(topic))}, ${approved ? 'saved interest' : 'explored subject'}" aria-pressed="${ui.mapSelection === id}"><title>${escape(topicTitle(topic))}</title>${baseline.has(id) && approved ? `<circle class="baseline-ring" cx="${x}" cy="${y}" r="11"/>` : ''}<circle cx="${x}" cy="${y}" r="6"/><circle class="focus-ring" cx="${x}" cy="${y}" r="15"/><text x="${x + 24}" y="${y + (lines.length > 1 ? -2 : 4)}">${lines.map((line, index) => `<tspan x="${x + 24}" dy="${index ? 16 : 0}">${escape(line)}</tspan>`).join('')}</text></g>`;
    }).join('');
    surface.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${top + 4}" role="group" aria-label="Your interests and exploration paths, grouped by knowledge domain">${blocks.join('')}${edges}${nodes}</svg>`;
    surface.querySelectorAll('[data-map-id]').forEach(node => {
      const choose = () => { ui.mapSelection = node.dataset.mapId; const key = ui.mapSelection; render(); const target = [...document.querySelectorAll('[data-map-id]')].find(element => element.dataset.mapId === key); target?.focus({ preventScroll: true }); };
      node.addEventListener('click', choose);
      node.addEventListener('keydown', event => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); choose(); } });
    });
  };
  draw();
  mapObserver = new ResizeObserver(draw);
  mapObserver.observe(surface);
}

function wrapLabel(title, maxChars) {
  const words = title.split(/\s+/);
  const lines = [''];
  for (const word of words) {
    const current = lines.at(-1);
    if (current && `${current} ${word}`.length > maxChars) lines.push(word);
    else lines[lines.length - 1] = current ? `${current} ${word}` : word;
  }
  if (lines.length > 2) return [lines[0], `${lines.slice(1).join(' ').slice(0, Math.max(8, maxChars - 1))}…`];
  return lines.map(line => line.length > maxChars ? `${line.slice(0, maxChars - 1)}…` : line);
}

function bindEvents() {
  app.querySelectorAll('[data-action]').forEach(button => {
    const { action, id = '', provider = '', view = '' } = button.dataset;
    if (!button.dataset.focus) button.dataset.focus = `${action}:${id}:${provider}:${view}`;
    button.addEventListener('click', onAction);
  });
  document.querySelector('#manual-interest')?.addEventListener('input', event => { ui.manual = event.target.value; });
  document.querySelector('#manual-form')?.addEventListener('submit', async event => {
    event.preventDefault();
    const topic = ui.manual.trim();
    if (!topic) { document.querySelector('#manual-interest')?.focus(); return; }
    const next = await run('add', () => dispatch({ type: 'ADD_INTEREST', topic }), 'Interest saved.');
    if (next && !next.lastError && ui.manual.trim() === topic) { ui.manual = ''; render(); document.querySelector('#manual-interest')?.focus(); }
  });
  document.querySelector('#history-days')?.addEventListener('change', event => { ui.days = event.target.value; });
  app.querySelector('.candidate-inbox')?.addEventListener('toggle', event => { ui.inboxOpen = event.target.open; });
  app.querySelectorAll('[data-candidate]').forEach(input => input.addEventListener('change', event => { const id = event.target.dataset.candidate; event.target.checked ? ui.selected.add(id) : ui.selected.delete(id); render(); }));
  for (const id of ['discovery-mode', 'settings-mode']) document.getElementById(id)?.addEventListener('change', event => run('mode', () => dispatch({ type: 'SET_SETTINGS', patch: { mode: event.target.value } }), 'Discovery mode saved.'));
  document.getElementById('browsing-enabled')?.addEventListener('change', event => run('browsing', () => dispatch({ type: 'SET_SETTINGS', patch: { browsingEnabled: event.target.checked } }), 'Browsing review preference saved.'));
  document.getElementById('auto-refresh')?.addEventListener('change', event => run('auto-refresh', () => dispatch({ type: 'SET_SETTINGS', patch: { autoRefresh: event.target.checked } }), 'Refresh preference saved.'));
  app.querySelectorAll('#settings-form input, #settings-form textarea').forEach(input => input.addEventListener('input', event => {
    ui.settingsDraft[event.target.name] = event.target.value;
    ui.settingsDirty = true;
    ui.settingsSaved = false;
    const status = document.querySelector('.settings-form .actions [role="status"]');
    if (status) status.textContent = 'You have unsaved changes.';
  }));
  document.querySelector('#settings-form')?.addEventListener('submit', saveSettings);
}

async function saveSettings(event) {
  event.preventDefault();
  const draft = { ...ui.settingsDraft };
  const domains = [...new Set(draft.blockedDomains.split(/[\n,]+/).map(domain => domain.trim().toLowerCase()).filter(Boolean))];
  if (domains.some(domain => !/^[a-z0-9]+(?:[a-z0-9.-]*[a-z0-9])?$/.test(domain) || domain.includes('..'))) {
    ui.error = 'Enter domain names without https://, paths, or spaces. Use one domain per line.';
    render();
    document.querySelector('#blocked-domains')?.focus();
    return;
  }
  const next = await run('settings', () => dispatch({ type: 'SET_SETTINGS', patch: { endpoint: draft.endpoint.trim(), accessToken: draft.accessToken.trim(), blockedDomains: domains } }), 'Settings saved.');
  if (next && !next.lastError && JSON.stringify(ui.settingsDraft) === JSON.stringify(draft)) {
    ui.settingsDirty = false;
    ui.settingsSaved = true;
    ui.settingsDraft = snapshotSettings();
    render();
  }
}

async function onAction(event) {
  const button = event.currentTarget;
  const { action, id, provider } = button.dataset;
  if (action === 'view') { ui.view = button.dataset.view; if (ui.view === 'settings' && !ui.settingsDirty) ui.settingsDraft = snapshotSettings(); render(); return; }
  if (action === 'clear-error') { ui.error = null; if (state?.lastError) await run('clear-error', () => dispatch({ type: 'CLEAR_ERROR' })); else render(); return; }
  if (action === 'reload') { const next = await run('reload', getState); if (next && !unsubscribe) unsubscribe = subscribe(applyState); return; }
  if (action === 'import') { ui.inboxOpen = true; await run('import', () => importHistory(Number(ui.days)), 'Recent browsing is ready to review.'); return; }
  if (action === 'approve') { await run('approve', () => dispatch({ type: 'APPROVE', ids: [...ui.selected] }), 'Selected interests saved.'); return; }
  if (action === 'select-all') { ui.selected = ui.selected.size === arr(state.candidates).length ? new Set() : new Set(arr(state.candidates).map(topicId)); render(); return; }
  if (action === 'remove') { await run(`remove:${id}`, () => dispatch({ type: 'REMOVE_INTEREST', id }), 'Interest removed.'); return; }
  if (action === 'dismiss') { await run(`dismiss:${id}`, () => dispatch({ type: 'DISMISS', id }), 'Topic dismissed.'); return; }
  if (action === 'save-topic') { const topic = getTopic(id); if (topic) await run(`save:${id}`, () => dispatch({ type: 'ADD_INTEREST', topic }), 'Interest saved.'); return; }
  if (action === 'set-focus') {
    const next = await run('focus', async () => {
      const focused = await dispatch({ type: 'SET_FOCUS', id });
      if (focused?.lastError || focused?.settings?.mode === 'path') return focused;
      return dispatch({ type: 'SET_SETTINGS', patch: { mode: 'path' } });
    }, 'Your starting interest has changed.');
    if (next && !next.lastError) { ui.view = 'discover'; render(); document.querySelector('#discovery-mode')?.focus(); }
    return;
  }
  if (action === 'search') { const topic = getTopic(id); if (topic) await run(`search:${id}:${provider}`, () => search(topic, provider), 'Exploration recorded.'); return; }
  if (action === 'recommend') { await run('recommend', recommend, 'New ideas are ready.'); return; }
  if (action === 'clear-derived' || action === 'reset') {
    const reset = action === 'reset';
    const confirmed = await confirmDialog(reset ? 'Start over?' : 'Clear browsing data?', reset ? 'This removes your saved interests, browsing topics, exploration paths, and connection settings from this device. This cannot be undone.' : 'This removes topics and evidence found in browsing review. Your saved interests and OtherWise exploration paths stay here.', reset ? 'Reset OtherWise' : 'Clear browsing data');
    if (!confirmed) return;
    const next = await run(action, () => dispatch({ type: reset ? 'RESET' : 'CLEAR_DERIVED' }), reset ? 'OtherWise has been reset.' : 'Browsing data cleared.');
    if (reset && next && !next.lastError) { ui.manual = ''; ui.settingsDirty = false; ui.settingsSaved = false; ui.settingsDraft = snapshotSettings(); ui.mapSelection = null; ui.selected.clear(); ui.view = 'discover'; render(); }
  }
}

function confirmDialog(title, description, label) {
  return new Promise(resolve => {
    const dialog = document.createElement('dialog');
    dialog.setAttribute('aria-labelledby', 'confirmation-title');
    dialog.setAttribute('aria-describedby', 'confirmation-description');
    dialog.innerHTML = `<h2 id="confirmation-title">${escape(title)}</h2><p id="confirmation-description">${escape(description)}</p><div class="dialog-actions"><button type="button" data-choice="cancel" autofocus>Keep my data</button><button type="button" class="danger" data-choice="confirm">${escape(label)}</button></div>`;
    document.body.append(dialog);
    dialog.addEventListener('cancel', event => { event.preventDefault(); dialog.close('cancel'); });
    dialog.querySelectorAll('[data-choice]').forEach(button => button.addEventListener('click', () => dialog.close(button.dataset.choice)));
    dialog.addEventListener('close', () => { const result = dialog.returnValue === 'confirm'; dialog.remove(); resolve(result); }, { once: true });
    dialog.showModal();
  });
}

function formatTime(timestamp) {
  const date = new Date(timestamp);
  return Number.isNaN(date.getTime()) ? 'recently' : date.toLocaleString(undefined, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' });
}

try {
  applyState(await getState());
  unsubscribe = subscribe(applyState);
} catch (error) {
  ui.error = error?.message || 'Could not open your saved interests. Please try again.';
  render();
}
window.addEventListener('pagehide', () => { if (typeof unsubscribe === 'function') unsubscribe(); mapObserver?.disconnect(); });
