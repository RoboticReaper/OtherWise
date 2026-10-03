import { getState, dispatch, importHistory, recommend, search, subscribe, openDashboard, requestFocus, cancelFocus, subscribeFocusInvalidation } from '../bridge.js';
import { normalizeLanguage, translate, translateError } from './i18n.js';
import { paginate } from './pagination.js';
import { createMapWorkspace } from './map-workspace.js';
import { galaxyLoader } from './galaxy-data.js';
import { RECOMMENDATION_DEFAULTS, RECOMMENDATION_BOUNDS, normalizeRecommendationOptions } from '../core/recommendation-options.js';
import {discoveryControls, graphDetails, feedbackForm, savedFeedbackView} from './discovery.js';

const app = document.querySelector('#app');
const params = new URLSearchParams(location.search);
const preview = params.get('preview') === '1';
const dashboard = document.body.classList.contains('dashboard');
const initialView = ['discover', 'map', 'settings'].includes(params.get('view')) ? params.get('view') : dashboard ? 'map' : 'discover';
const ui = {
  view: initialView, manual: '', days: '30', selected: new Set(), inboxOpen: true, candidatePage: 1, recommendationPage: 1,
  galaxyView: null, settingsDraft: null, settingsDirty: false, settingsSaved: false,
  advancedOptionsOpen: false,
  feedbackDrafts: new Map(), feedbackOpen: false, feedbackPage: 1,
  pending: new Set(), expandedDescriptions: new Set(), error: null, announcement: '', loaded: false,
};
let state = null;
let mapWorkspace;
let unsubscribeFocus;
let galaxyAssets;
let galaxyLoading = false;
let galaxyError = false;
let unsubscribe;
let preferenceSequence = 0;

const escape = value => String(value ?? '').replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]));
const arr = value => Array.isArray(value) ? value : [];
const topicId = topic => topic?.id || topic?.topic || '';
const topicTitle = topic => topic?.topic || topic?.id || '';
const busy = key => ui.pending.has(key);
const disabled = value => value ? ' disabled' : '';
const checked = value => value ? ' checked' : '';
const getTopic = id => [...arr(state?.approved), ...arr(state?.recommendations), ...arr(state?.explored), ...arr(state?.candidates)].find(topic => topicId(topic) === id);
const isApproved = id => arr(state?.approved).some(topic => topicId(topic) === id);
const language = () => normalizeLanguage(state?.settings?.language);
const t = (key, values) => translate(language(), key, values);
const text = (key, values) => escape(t(key, values));
const candidatePage = () => paginate(arr(state?.candidates), ui.candidatePage);

function snapshotSettings() {
  const settings = state?.settings || {};
  return {
    endpoint: settings.endpoint || 'http://127.0.0.1:8000', accessToken: settings.accessToken || '',
    blockedDomains: arr(settings.blockedDomains).join('\n'),
    recommendationOptions: normalizeRecommendationOptions(settings.recommendationOptions),
  };
}

function applyState(next) {
  if (!next || typeof next !== 'object') return;
  if (next.lastUpdated !== state?.lastUpdated) ui.recommendationPage = 1;
  if (state?.salt && state.salt !== next.salt) {
    mapWorkspace?.destroy(); mapWorkspace = null; ui.galaxyView = null;
    ui.feedbackDrafts.clear(); ui.feedbackPage = 1; ui.feedbackOpen = false;
  }
  state = next;
  ui.loaded = true;
  const candidates = new Set(arr(state.candidates).map(topicId));
  ui.selected = new Set([...ui.selected].filter(id => candidates.has(id)));
  ui.candidatePage = candidatePage().page;
  ui.recommendationPage = paginate(arr(state.recommendations), ui.recommendationPage).page;
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

function languageSelect(id) {
  return `<label class="language-control" for="${id}"><span>Language / 语言</span><select id="${id}" data-language data-focus="${id}" aria-label="Language / 语言"><option value="en"${language() === 'en' ? ' selected' : ''}>English</option><option value="zh-CN"${language() === 'zh-CN' ? ' selected' : ''}>简体中文</option></select></label>`;
}

function render() {
  const focused = document.activeElement;
  const focusKey = focused?.dataset?.focus;
  const selection = focused && 'selectionStart' in focused ? [focused.selectionStart, focused.selectionEnd] : null;
  const recommendationIds = new Set(arr(state?.recommendations).map(topicId));
  ui.expandedDescriptions = new Set([...ui.expandedDescriptions].filter(id => recommendationIds.has(id)));
  // Native toggle events are queued; capture the live state before replacing the DOM.
  app.querySelectorAll('[data-description]').forEach(details => {
    const id = details.dataset.description;
    if (!details.isConnected || !recommendationIds.has(id)) return;
    details.open ? ui.expandedDescriptions.add(id) : ui.expandedDescriptions.delete(id);
  });
  const advancedOptions = app.querySelector('#recommendation-advanced');
  if (advancedOptions?.isConnected) ui.advancedOptionsOpen = advancedOptions.open;
  if (mapWorkspace) { mapWorkspace.setActive(ui.view === 'map'); mapWorkspace.element.remove(); }
  const error = ui.error || state?.lastError;
  document.documentElement.lang = language();
  document.title = t('title');
  app.setAttribute('aria-busy', String(!ui.loaded));
  app.innerHTML = `<div class="app-shell">
    <header class="app-header"><span class="brand">OtherWise<span class="brand-star" aria-hidden="true">✦</span></span>
      <div class="header-tools">${languageSelect('ui-language')}<span class="connection-label${error ? ' has-error' : ''}">${text(!ui.loaded ? 'opening' : error ? 'attention' : preview ? 'demo' : 'local')}</span></div>
    </header>
    ${preview ? `<div class="demo-notice"><strong>${text('demo')}</strong> · ${text('demoNotice')}</div>` : ''}
    <div class="workspace"><nav class="main-nav" aria-label="${text('mainNavigation')}">${['discover', 'map', 'settings'].map(view => `<button type="button" data-action="view" data-view="${view}" data-focus="nav-${view}"${ui.view === view ? ' aria-current="page"' : ''}>${text(view)}</button>`).join('')}${!dashboard ? `<button type="button" class="dashboard-link" data-action="open-dashboard">${text('openDashboard')} ↗</button>` : ''}</nav><div class="workspace-content">
    ${error ? `<div class="error-banner" role="alert"><p><strong>${text('errorHeading')}</strong><br>${escape(translateError(language(), error))}${ui.view !== 'settings' ? `<br>${text('errorHint')}` : ''}</p><button type="button" class="quiet" data-action="clear-error" aria-label="${text('dismissError')}">×</button></div>` : ''}
    <main id="main-view">${!ui.loaded ? loadingView() : ui.view === 'settings' ? settingsView() : ui.view === 'map' ? mapView() : discoverView()}</main>
    <footer class="app-footer">${text('footer')}</footer></div></div>
    <div class="sr-only" role="status" aria-live="polite">${ui.announcement ? text(ui.announcement) : ''}</div>
  </div>`;
  bindEvents();
  if (ui.view === 'map' && ui.loaded) drawMap();
  if (focused?.isConnected && mapWorkspace?.element.contains(focused)) focused.focus({preventScroll:true});
  if (focusKey) {
    let target = [...app.querySelectorAll('[data-focus]')].find(element => element.dataset.focus === focusKey);
    // A boundary button becomes disabled after paging. Keep keyboard focus nearby.
    if (target?.disabled && focusKey.startsWith('candidate-')) target = app.querySelector('.inbox-pagination button:not(:disabled)') || app.querySelector('.candidate-inbox summary');
    if (target?.disabled && focusKey.startsWith('recommendation-page-')) target = app.querySelector('.recommendation-pagination button:not(:disabled)') || app.querySelector('#recommendations-title');
    if (!target && focusKey.startsWith('recommendation-dismiss:')) target = app.querySelector('.recommendation-card [data-action="dismiss"]') || app.querySelector('#recommendations-title');
    if (!target && (focusKey.startsWith('graph-') || focusKey.startsWith('undo-feedback:') || focusKey.startsWith('clear-concept-feedback:'))) target = app.querySelector('#recommendations-title');
    if (!target && (focusKey.startsWith('candidate-') || focusKey.startsWith('dismiss:'))) target = app.querySelector('.candidate-inbox summary');
    if (target) {
      target.focus({ preventScroll: true });
      if (selection && typeof target.setSelectionRange === 'function' && target.type !== 'number') {
        try { target.setSelectionRange(...selection); } catch { /* A non-text input has no selection. */ }
      }
    }
  }
}

function loadingView() {
  return `<section class="empty-state"><h1>${text('headline')}</h1><p>${text('loadingInterests')}</p>${ui.error ? `<button type="button" data-action="reload">${text('retry')}</button>` : ''}</section>`;
}

function discoverView() {
  const approved = arr(state.approved);
  const candidates = arr(state.candidates);
  const items = arr(state.recommendations);
  const page = paginate(items, ui.recommendationPage);
  ui.recommendationPage = page.page;
  const mode = state.settings?.mode || 'path';
  const listView = state.settings?.recommendationView === 'list';
  const specific = state.settings?.recommendationKind === 'specific';
  return `<section class="hero"><span class="little-star" aria-hidden="true">✧</span><p class="eyebrow">${text('curiosity')}</p><h1>${text('headlineFirst')}<br>${text('headlineSecond')}</h1><p>${text('heroDescription')}</p></section>
    ${!approved.length && !arr(state.baseline).length ? `<div class="intro"><p><strong>${text('smallBeginning')}</strong> ${text('intro')}</p><p class="small">${text('introPrivacy')}</p></div>` : ''}
    <form class="manual-form" id="manual-form"><label class="sr-only" for="manual-interest">${text('addInterest')}</label><input id="manual-interest" data-focus="manual-interest" name="interest" placeholder="${text('interestPlaceholder')}" aria-describedby="interest-language-help" maxlength="120" value="${escape(ui.manual)}" autocomplete="off"><button class="primary" data-focus="add-interest" type="submit"${disabled(busy('add'))}>${text(busy('add') ? 'saving' : 'add')}</button></form>
    <p class="language-note" id="interest-language-help">${text('languageScope')}</p>
    <div class="import-row"><button type="button" data-action="import"${disabled(busy('import'))}>${text(busy('import') ? 'reviewing' : 'reviewBrowsing')}</button><label class="sr-only" for="history-days">${text('historyPeriod')}</label><select id="history-days" data-focus="history-days"${disabled(busy('import'))}><option value="7"${ui.days === '7' ? ' selected' : ''}>${text('historyDays', { days: 7 })}</option><option value="30"${ui.days === '30' ? ' selected' : ''}>${text('historyDays', { days: 30 })}</option></select></div>
    ${candidates.length ? inboxView(candidates) : ''}
    <section class="section" aria-labelledby="interests-title"><div class="section-heading"><h2 id="interests-title">${text('yourInterests')}</h2>${approved.length ? `<span class="muted small">${text('savedByYou')}</span>` : ''}</div>${approved.length ? `<div class="interests">${approved.map(topic => `<span class="interest-chip"><span>${escape(topicTitle(topic))}</span><button type="button" data-action="remove" data-id="${escape(topicId(topic))}" aria-label="${text('removeInterest', { topic: topicTitle(topic) })}">×</button></span>`).join('')}</div>` : `<p class="muted small">${text('firstInterest')}</p>`}</section>
    <section class="section" aria-labelledby="recommendations-title"><div class="section-heading"><h2 id="recommendations-title" tabindex="-1">${text('beyond')}</h2><div class="view-switch" role="group" aria-label="${text('recommendationLayout')}">${['cards', 'list'].map(value => `<button type="button" data-action="recommendation-view" data-value="${value}" data-focus="recommendation-view-${value}" aria-pressed="${(value === 'list') === listView}">${text(value)}</button>`).join('')}</div></div>
    ${discoveryControls(state,{text})}<div class="discovery-toolbar"><label class="sr-only" for="discovery-mode">${text('discoveryMode')}</label><select id="discovery-mode" data-focus="discovery-mode"><option value="path"${mode === 'path' ? ' selected' : ''}>${text('followPath')}</option><option value="global"${mode === 'global' ? ' selected' : ''}>${text('acrossInterests')}</option></select><button type="button" data-action="recommend"${disabled(!approved.length || busy('recommend') || busy('feedback'))}>${text(busy('recommend') || busy('feedback') ? 'finding' : items.length ? 'refreshIdeas' : 'findIdeas')} <span aria-hidden="true">↗</span></button></div>
    ${approved.length ? `<p class="focus-note">${mode === 'path' ? text('pathNote', { topic: state.focus || topicTitle(approved.at(-1)) }) : text('globalNote')}</p>` : ''}
    ${state.lastUpdated ? `<div class="recommendation-batch"><p class="recommendation-range">${text('recommendationRange', page)}</p><p>${text('recommendationBatchHelp')}</p><button type="button" class="quiet" data-action="view" data-view="settings">${text('adjustRecommendations')}</button></div>` : ''}
    ${items.length ? `<div class="recommendations${listView ? ' is-list' : ''}">${page.items.map(topic => cardView(topic, listView)).join('')}</div>${page.pageCount > 1 ? `<nav class="recommendation-pagination" aria-label="${text('recommendationPagination')}"><button type="button" data-action="recommendation-prev" data-focus="recommendation-page-prev"${disabled(page.page === 1)}>${text('previous')}</button><span class="page-status" role="status">${text('page', { page: page.page, pages: page.pageCount })}</span><button type="button" data-action="recommendation-next" data-focus="recommendation-page-next"${disabled(page.page === page.pageCount)}>${text('next')}</button></nav>` : ''}` : `<div class="empty-state"><div class="empty-symbol" aria-hidden="true">✧</div><h3>${text(approved.length ? 'newRoom' : 'firstPage')}</h3><p>${text(approved.length ? 'findHelp' : 'firstHelp')}</p></div>`}
    ${specific && items.length ? `<p class="concept-reserve">${text('reservationCount',{achieved:items[0].discovery?.exploration_achieved||0,target:items[0].discovery?.exploration_target||0})}</p>` : ''}
    ${specific && state.lastUpdated && !items.length ? `<p class="muted small">${text('specificEmpty')}</p>` : ''}
    ${specific ? savedFeedbackView(state,ui.feedbackPage,ui.feedbackOpen,{text,escape,busy:busy('feedback')}) : ''}
    ${state.lastUpdated ? `<p class="last-updated">${text('updated', { time: formatTime(state.lastUpdated) })}</p>` : ''}</section>`;
}

function inboxView(candidates) {
  const page = paginate(candidates, ui.candidatePage);
  ui.candidatePage = page.page;
  const allOnPageSelected = page.items.length > 0 && page.items.every(topic => ui.selected.has(topicId(topic)));
  return `<details class="candidate-inbox"${ui.inboxOpen ? ' open' : ''}><summary data-focus="inbox-summary">${text('inbox')} <span class="count">${text(candidates.length === 1 ? 'oneTopic' : 'topicCount', { count: candidates.length })}</span></summary>
    <p class="helper muted small">${text('inboxHelp')}</p><p class="candidate-range muted small">${text('range', page)}</p>
    <div class="candidate-list">${page.items.map(topic => `<div class="candidate-row"><label><input type="checkbox" data-candidate="${escape(topicId(topic))}" data-focus="candidate-${escape(topicId(topic))}"${checked(ui.selected.has(topicId(topic)))}><span class="candidate-copy"><span class="topic">${escape(topicTitle(topic))}</span><span class="domain">${escape(topic.domain || t('otherSubjects'))} · ${text('localBrowsing')}</span></span></label><button class="quiet" type="button" data-action="dismiss" data-id="${escape(topicId(topic))}" aria-label="${text('dismissTopic', { topic: topicTitle(topic) })}">${text('dismiss')}</button></div>`).join('')}</div>
    <nav class="inbox-pagination" aria-label="${text('candidatePagination')}"><button type="button" data-action="candidate-prev" data-focus="candidate-prev"${disabled(page.page === 1)}>${text('previous')}</button><span class="page-status" role="status">${text('page', { page: page.page, pages: page.pageCount })}</span><button type="button" data-action="candidate-next" data-focus="candidate-next"${disabled(page.page === page.pageCount)}>${text('next')}</button></nav>
    <p class="selection-count muted small">${text('selectionCount', { count: ui.selected.size })}</p>
    <div class="inbox-actions"><button class="primary" type="button" data-action="approve"${disabled(!ui.selected.size || busy('approve'))}>${busy('approve') ? text('saving') : text('saveSelected', { count: ui.selected.size })}</button><button class="quiet" type="button" data-action="select-all">${text(allOnPageSelected ? 'clearPage' : 'selectPage')}</button></div></details>`;
}

function descriptionView(topic, listView) {
  const description = topic.description || t('explorePace');
  if (!listView || description.length <= 110) return `<p class="topic-description">${escape(description)}</p>`;
  const id = topicId(topic);
  return `<details class="description-details" data-description="${escape(id)}"${ui.expandedDescriptions.has(id) ? ' open' : ''}><summary data-focus="description-${escape(id)}"><span class="description-preview">${escape(description.slice(0, 110).trimEnd())}… </span><span class="description-more">${text('readMore')}</span><span class="description-less">${text('readLess')}</span></summary><p class="topic-description">${escape(description)}</p></details>`;
}

function cardView(topic, listView = false) {
  const id = topicId(topic);
  const saved = isApproved(id);
  return `<article class="recommendation-card"><div class="recommendation-content"><div class="recommendation-heading"><p class="eyebrow">${escape(topic.domain || t('newDirection'))}</p><h3>${escape(topicTitle(topic))}</h3></div>${descriptionView(topic, listView)}${topic.nearest_interest ? `<div class="related">${text('connectionFrom', { topic: topic.nearest_interest })}</div>` : ''}${graphDetails(topic,{text,escape})}</div><div class="recommendation-actions"><div class="card-search">${searchButtons(topic)}</div><div class="card-feedback">${saved ? `<span class="saved-label">${text('savedLabel')}</span>` : `<button type="button" class="save" data-action="save-topic" data-id="${escape(id)}"${disabled(busy(`save:${id}`))}>${text('saveInterest')}</button>`}<button type="button" class="quiet" data-action="dismiss" data-id="${escape(id)}" data-focus="recommendation-dismiss:${escape(id)}">${text('notForMe')}</button></div>${feedbackForm(topic,state,ui.feedbackDrafts.get(topic.discovery?.concept_id),{text,escape,busy:busy('feedback')})}</div></article>`;
}

function recommendationOptionField(key, draft) {
  const { min, max, integer } = RECOMMENDATION_BOUNDS[key];
  const id = `recommendation-${key}`;
  return `<label class="field recommendation-option"><span>${text(`option_${key}`)} <code>${escape(key)}</code></span><input id="${id}" name="${key}" data-recommendation-option="${key}" type="number" min="${min}" max="${max}" step="${integer ? '1' : 'any'}" required aria-describedby="${id}-help" data-focus="${id}" value="${escape(draft[key])}"><small id="${id}-help">${text(`optionHelp_${key}`)}</small></label>`;
}

function recommendationSettingsView(draft) {
  return `<section class="settings-group recommendation-settings"><h2>${text('recommendationSettings')}</h2><p class="muted small">${text('recommendationSettingsHelp')}</p>${recommendationOptionField('limit', draft)}<details id="recommendation-advanced"${ui.advancedOptionsOpen ? ' open' : ''}><summary data-focus="recommendation-advanced-summary">${text('advancedRecommendations')}</summary><p class="muted small">${text('recommendationDistanceHelp')}</p><div class="recommendation-option-grid">${Object.keys(RECOMMENDATION_DEFAULTS).filter(key => key !== 'limit').map(key => recommendationOptionField(key, draft)).join('')}</div></details><button type="button" class="quiet" data-action="reset-recommendation-options">${text('resetRecommendationDefaults')}</button></section>`;
}

function searchButtons(topic) {
  const id = topicId(topic);
  return `<button type="button" data-action="search" data-id="${escape(id)}" data-provider="google"${disabled(busy(`search:${id}:google`))}>Google <span aria-hidden="true">↗</span></button><button type="button" data-action="search" data-id="${escape(id)}" data-provider="youtube"${disabled(busy(`search:${id}:youtube`))}>YouTube <span aria-hidden="true">↗</span></button>`;
}

function settingsView() {
  const settings = state.settings || {};
  const draft = ui.settingsDraft || snapshotSettings();
  return `<section class="settings"><div class="view-heading"><p class="eyebrow">${text('makeYours')}</p><h1>${text('intention')}</h1><p>${text('settingsIntro')}</p></div>
    <section class="settings-group"><h2>${text('interfaceLanguage')}</h2>${languageSelect('settings-language')}<p class="language-note">${text('languageScope')}</p></section>
    <section class="settings-group"><h2>${text('discovery')}</h2><label class="field"><span>${text('connections')}</span><select id="settings-mode" data-focus="settings-mode" aria-label="${text('connections')}"><option value="path"${settings.mode !== 'global' ? ' selected' : ''}>${text('followLatest')}</option><option value="global"${settings.mode === 'global' ? ' selected' : ''}>${text('exploreAll')}</option></select><small>${text('modeHelp')}</small></label>
    <label class="toggle-row"><input id="browsing-enabled" type="checkbox" aria-label="${text('browsingEnabled')}" aria-describedby="browsing-help" data-focus="browsing-enabled"${checked(settings.browsingEnabled)}${disabled(busy('browsing'))}><span><strong>${text('browsingEnabled')}</strong><small id="browsing-help">${text('browsingHelp')}</small></span></label>
    <label class="toggle-row"><input id="auto-refresh" type="checkbox" aria-label="${text('autoRefresh')}" aria-describedby="refresh-help" data-focus="auto-refresh"${checked(settings.autoRefresh)}${disabled(busy('auto-refresh'))}><span><strong>${text('autoRefresh')}</strong><small id="refresh-help">${text('refreshHelp')}</small></span></label>
    <label class="toggle-row"><input id="galaxy-exploration-mode" type="checkbox" aria-describedby="exploration-mode-help" data-focus="galaxy-exploration-mode"${checked(settings.galaxyExplorationMode)}${disabled(busy('galaxy-exploration'))}><span><strong>${text('galaxyExplorationMode')}</strong><small id="exploration-mode-help">${text('galaxyExplorationHelp')}</small></span></label></section>
    <form class="settings-form" id="settings-form" novalidate>${recommendationSettingsView(draft.recommendationOptions)}<section class="settings-group"><h2>${text('serviceConnection')}</h2><p class="muted small">${text('serviceHelp')}</p><label class="field"><span>${text('serviceAddress')}</span><input id="endpoint" name="endpoint" type="url" aria-label="${text('serviceAddress')}" aria-describedby="endpoint-help" data-focus="endpoint" value="${escape(draft.endpoint)}" placeholder="https://your-demo-address" spellcheck="false" autocomplete="off" required><small id="endpoint-help">${text('endpointHelp')}</small></label><label class="field"><span>${text('teamCode')}</span><input id="access-token" name="accessToken" type="password" aria-label="${text('teamCode')}" aria-describedby="token-help" data-focus="access-token" value="${escape(draft.accessToken)}" placeholder="${text('codePlaceholder')}" autocomplete="off" spellcheck="false"><small id="token-help">${text('codeHelp')}</small></label></section>
    <section class="settings-group"><h2>${text('excludedWebsites')}</h2><p class="muted small">${text('excludedHelp')}</p><label class="field"><span>${text('domainsToSkip')}</span><textarea id="blocked-domains" name="blockedDomains" aria-label="${text('domainsToSkip')}" aria-describedby="domains-help" data-focus="blocked-domains" spellcheck="false">${escape(draft.blockedDomains)}</textarea><small id="domains-help">${text('domainsHelp')}</small></label></section>
    <div class="actions"><button class="primary" data-focus="save-settings" type="submit"${disabled(busy('settings'))}>${text(busy('settings') ? 'saving' : 'saveSettings')}</button><span class="muted" role="status">${ui.settingsDirty ? text('unsaved') : ui.settingsSaved ? text('settingsSaved') : ''}</span></div></form>
    <section class="settings-group"><h2>${text('localData')}</h2><p class="muted small">${text('localDataHelp')}</p><div class="data-actions"><button type="button" data-action="clear-derived">${text('clearBrowsing')}</button><button type="button" class="danger" data-action="reset">${text('reset')}</button></div></section>
    <p class="privacy-note">${text('privacy')}</p></section>`;
}

function mapView() {
  return `<section class="galaxy-page"><div class="view-heading"><p class="eyebrow">${text('mapEyebrow')}</p><h1>${text('galaxyHeading')}</h1><p>${text('galaxyIntro')}</p></div>
    <div id="galaxy-container">${galaxyError ? `<div class="empty-state" role="alert"><p>${text('galaxyUnavailable')}</p><button type="button" data-action="retry-galaxy">${text('retry')}</button></div>` : !galaxyAssets ? `<p class="muted" role="status">${text('galaxyLoading')}</p>` : ''}</div></section>`;
}

function drawMap() {
  const container = document.querySelector('#galaxy-container');
  if (!container || galaxyError) return;
  if (!galaxyAssets) {
    if (!galaxyLoading) {
      galaxyLoading = true;
      galaxyLoader.load().then(assets => { galaxyAssets = assets; }).catch(() => { galaxyError = true; }).finally(() => {
        galaxyLoading = false;
        if (ui.view === 'map') render();
      });
    }
    return;
  }
  try {
    if (!mapWorkspace) mapWorkspace = createMapWorkspace({ ...galaxyAssets, state, language: language(), viewState: ui.galaxyView,
      presentation: dashboard ? 'dashboard' : 'sidebar', preview, requestFocus, cancelFocus,
      onSave: topic => run(`save:${topicId(topic)}`, () => dispatch({type:'ADD_INTEREST', topic}), 'interestSaved'),
      onDismiss: id => run(`dismiss:${id}`, () => dispatch({type:'DISMISS', id}), 'topicDismissed'),
      onCustomFocus: focusMapTopic,
      onSearch: (topic, provider, context) => run(`search:${topicId(topic)}`, () => search(topic, provider, context), 'explorationRecorded'),
      onSettings: () => { ui.view = 'settings'; render(); document.querySelector('#endpoint')?.focus(); },
    });
    container.append(mapWorkspace.element);
    mapWorkspace.update({state, language: language()});
    mapWorkspace.setActive(true);
  } catch {
    galaxyError = true;
    render();
  }
}

async function focusMapTopic(id) {
  const next = await run('focus', async () => {
    const focused = await dispatch({type:'SET_FOCUS', id});
    if (focused?.lastError || focused?.settings?.mode === 'path') return focused;
    return dispatch({type:'SET_SETTINGS', patch:{mode:'path'}});
  }, 'focusChanged');
  if (next && !next.lastError) { ui.view = 'discover'; render(); document.querySelector('#discovery-mode')?.focus(); }
}

function bindEvents() {
  document.getElementById('recommendation-kind')?.addEventListener('change', event => run('kind', () => dispatch({type:'SET_SETTINGS',patch:{recommendationKind:event.target.value}}), 'kindSaved'));
  document.getElementById('discovery-exploration')?.addEventListener('change', event => run('exploration-share', () => dispatch({type:'SET_SETTINGS',patch:{discoveryExploration:Number(event.target.value)}}), 'shareSaved'));
  document.getElementById('discovery-feedback-panel')?.addEventListener('toggle', event => {if(event.target.isConnected)ui.feedbackOpen=event.target.open;});
  app.querySelectorAll('[data-graph-feedback]').forEach(form => {
    const read = () => ({curious:form.elements.curious.checked,known:form.elements.known.checked,difficulty:form.elements.difficulty.value});
    form.addEventListener('change', () => ui.feedbackDrafts.set(form.dataset.graphFeedback,read()));
    form.addEventListener('submit', async event => {
      event.preventDefault();const conceptId=form.dataset.graphFeedback;
      const next = await run('feedback', () => dispatch({type:'SET_DISCOVERY_FEEDBACK',conceptId,...read()}), 'feedbackSaved');
      if(next && !next.lastError){ui.feedbackDrafts.delete(conceptId);render();}
    });
  });
  app.querySelectorAll('[data-language]').forEach(select => select.addEventListener('change', event => {
    const nextLanguage = normalizeLanguage(event.target.value);
    void run(`language:${++preferenceSequence}`, () => dispatch({ type: 'SET_SETTINGS', patch: { language: nextLanguage } }), 'languageSaved');
  }));
  app.querySelectorAll('[data-description]').forEach(details => details.addEventListener('toggle', event => {
    // Ignore queued toggle events from a detached render.
    if (!event.target.isConnected) return;
    const id = event.target.dataset.description;
    event.target.open ? ui.expandedDescriptions.add(id) : ui.expandedDescriptions.delete(id);
  }));
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
    const next = await run('add', () => dispatch({ type: 'ADD_INTEREST', topic }), 'interestSaved');
    if (next && !next.lastError && ui.manual.trim() === topic) { ui.manual = ''; render(); document.querySelector('#manual-interest')?.focus(); }
  });
  document.querySelector('#history-days')?.addEventListener('change', event => { ui.days = event.target.value; });
  app.querySelector('.candidate-inbox')?.addEventListener('toggle', event => { if (event.target.isConnected) ui.inboxOpen = event.target.open; });
  app.querySelector('#recommendation-advanced')?.addEventListener('toggle', event => { if (event.target.isConnected) ui.advancedOptionsOpen = event.target.open; });
  app.querySelectorAll('[data-candidate]').forEach(input => input.addEventListener('change', event => { const id = event.target.dataset.candidate; event.target.checked ? ui.selected.add(id) : ui.selected.delete(id); render(); }));
  for (const id of ['discovery-mode', 'settings-mode']) document.getElementById(id)?.addEventListener('change', event => run('mode', () => dispatch({ type: 'SET_SETTINGS', patch: { mode: event.target.value } }), 'modeSaved'));
  document.getElementById('browsing-enabled')?.addEventListener('change', event => run('browsing', () => dispatch({ type: 'SET_SETTINGS', patch: { browsingEnabled: event.target.checked } }), 'browsingSaved'));
  document.getElementById('galaxy-exploration-mode')?.addEventListener('change', event => run('galaxy-exploration', () => dispatch({ type: 'SET_SETTINGS', patch: { galaxyExplorationMode: event.target.checked } }), 'explorationModeSaved'));
  document.getElementById('auto-refresh')?.addEventListener('change', event => run('auto-refresh', () => dispatch({ type: 'SET_SETTINGS', patch: { autoRefresh: event.target.checked } }), 'refreshSaved'));
  app.querySelectorAll('#settings-form input, #settings-form textarea').forEach(input => input.addEventListener('input', event => {
    const option = event.target.dataset.recommendationOption;
    if (option) ui.settingsDraft.recommendationOptions[option] = event.target.value;
    else ui.settingsDraft[event.target.name] = event.target.value;
    ui.settingsDirty = true;
    ui.settingsSaved = false;
    const status = document.querySelector('.settings-form .actions [role="status"]');
    if (status) status.textContent = t('unsaved');
  }));
  document.querySelector('#settings-form')?.addEventListener('submit', saveSettings);
}

async function saveSettings(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const invalid = [...form.querySelectorAll('input, textarea')].find(input => !input.checkValidity());
  if (invalid) {
    const details = invalid.closest('details');
    if (details) { details.open = true; ui.advancedOptionsOpen = true; }
    invalid.reportValidity();
    invalid.focus();
    return;
  }
  const draft = structuredClone(ui.settingsDraft);
  const recommendationOptions = Object.fromEntries(Object.entries(draft.recommendationOptions).map(([key, value]) => [key, Number(value)]));
  const domains = [...new Set(draft.blockedDomains.split(/[\n,]+/).map(domain => domain.trim().toLowerCase()).filter(Boolean))];
  if (domains.some(domain => !/^[a-z0-9]+(?:[a-z0-9.-]*[a-z0-9])?$/.test(domain) || domain.includes('..'))) {
    ui.error = 'Enter domain names without https://, paths, or spaces. Use one domain per line.';
    render();
    document.querySelector('#blocked-domains')?.focus();
    return;
  }
  const next = await run('settings', () => dispatch({ type: 'SET_SETTINGS', patch: { endpoint: draft.endpoint.trim(), accessToken: draft.accessToken.trim(), blockedDomains: domains, recommendationOptions } }), 'settingsSaved');
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
  if (action === 'open-dashboard') { await run('dashboard', () => openDashboard('map')); return; }
  if (action === 'retry-galaxy') { galaxyError = false; galaxyAssets = null; galaxyLoader.invalidate(); render(); return; }
  if (action === 'recommendation-view') {
    const recommendationView = button.dataset.value;
    await run(`recommendation-view:${++preferenceSequence}`, () => dispatch({ type: 'SET_SETTINGS', patch: { recommendationView } }), 'layoutSaved');
    return;
  }
  if (action === 'view') { ui.view = button.dataset.view; if (ui.view === 'settings' && !ui.settingsDirty) ui.settingsDraft = snapshotSettings(); render(); return; }
  if (action === 'clear-error') { ui.error = null; if (state?.lastError) await run('clear-error', () => dispatch({ type: 'CLEAR_ERROR' })); else render(); return; }
  if (action === 'reload') { const next = await run('reload', getState); if (next && !unsubscribe) unsubscribe = subscribe(applyState); return; }
  if (action === 'import') { ui.inboxOpen = true; await run('import', () => importHistory(Number(ui.days)), 'importReady'); return; }
  if (action === 'approve') { await run('approve', () => dispatch({ type: 'APPROVE', ids: [...ui.selected] }), 'selectedSaved'); return; }
  if (action === 'candidate-prev' || action === 'candidate-next') {
    ui.candidatePage = paginate(arr(state.candidates), ui.candidatePage + (action === 'candidate-next' ? 1 : -1)).page;
    render(); return;
  }
  if (action === 'recommendation-prev' || action === 'recommendation-next') {
    ui.recommendationPage = paginate(arr(state.recommendations), ui.recommendationPage + (action === 'recommendation-next' ? 1 : -1)).page;
    render(); return;
  }
  if (action === 'reset-recommendation-options') {
    ui.settingsDraft.recommendationOptions = { ...RECOMMENDATION_DEFAULTS };
    ui.settingsDirty = true;
    ui.settingsSaved = false;
    render(); return;
  }
  if (action === 'select-all') {
    const ids = candidatePage().items.map(topicId);
    const clearPage = ids.every(candidate => ui.selected.has(candidate));
    ids.forEach(candidate => clearPage ? ui.selected.delete(candidate) : ui.selected.add(candidate));
    render(); return;
  }
  if (action === 'remove') { await run(`remove:${id}`, () => dispatch({ type: 'REMOVE_INTEREST', id }), 'interestRemoved'); return; }
  if (action === 'dismiss') { await run(`dismiss:${id}`, () => dispatch({ type: 'DISMISS', id }), 'topicDismissed'); return; }
  if (action === 'save-topic') { const topic = getTopic(id); if (topic) await run(`save:${id}`, () => dispatch({ type: 'ADD_INTEREST', topic }), 'interestSaved'); return; }
  if (action === 'set-focus') { await focusMapTopic(id); return; }
  if (action === 'search') { const topic = getTopic(id); if (topic) await run(`search:${id}:${provider}`, () => search(topic, provider), 'explorationRecorded'); return; }
  if (action === 'recommend') { await run('recommend', recommend, 'ideasReady'); return; }
  if (action === 'feedback-prev' || action === 'feedback-next') { ui.feedbackPage=paginate(Object.entries(state.discovery.feedback),ui.feedbackPage+(action==='feedback-next'?1:-1)).page;render();return; }
  if (action === 'undo-feedback' || action === 'clear-concept-feedback') {
    const next=await run('feedback',()=>dispatch(action==='undo-feedback'?{type:'UNDO_DISCOVERY_FEEDBACK'}:{type:'CLEAR_CONCEPT_FEEDBACK',conceptId:button.dataset.conceptId}),'feedbackChanged');
    if(next){ui.feedbackDrafts.clear();render();}return;
  }
  if(action==='clear-feedback'){
    if(!await confirmDialog(t('clearAllFeedback'),t('clearFeedbackDescription'),t('clearAllFeedback')))return;
    const next=await run('feedback',()=>dispatch({type:'CLEAR_DISCOVERY_FEEDBACK'}),'feedbackCleared');
    if(next && !next.lastError){ui.feedbackDrafts.clear();ui.feedbackPage=1;render();}return;
  }
  if (action === 'clear-derived' || action === 'reset') {
    const reset = action === 'reset';
    const confirmed = await confirmDialog(t(reset ? 'startOver' : 'confirmClear'), t(reset ? 'resetDescription' : 'clearDescription'), t(reset ? 'reset' : 'clearBrowsing'));
    if (!confirmed) return;
    const next = await run(action, () => dispatch({ type: reset ? 'RESET' : 'CLEAR_DERIVED' }), reset ? 'resetDone' : 'clearDone');
    if (reset && next && !next.lastError) { mapWorkspace?.destroy(); mapWorkspace = null; ui.manual = ''; ui.settingsDirty = false; ui.settingsSaved = false; ui.settingsDraft = snapshotSettings(); ui.galaxyView = null; ui.selected.clear(); ui.expandedDescriptions.clear(); ui.feedbackDrafts.clear(); ui.feedbackPage = 1; ui.candidatePage = 1; ui.recommendationPage = 1; ui.view = 'discover'; render(); }
  }
}

function confirmDialog(title, description, label) {
  return new Promise(resolve => {
    const dialog = document.createElement('dialog');
    dialog.setAttribute('aria-labelledby', 'confirmation-title');
    dialog.setAttribute('aria-describedby', 'confirmation-description');
    dialog.innerHTML = `<h2 id="confirmation-title">${escape(title)}</h2><p id="confirmation-description">${escape(description)}</p><div class="dialog-actions"><button type="button" data-choice="cancel" autofocus>${text('keepData')}</button><button type="button" class="danger" data-choice="confirm">${escape(label)}</button></div>`;
    document.body.append(dialog);
    dialog.addEventListener('cancel', event => { event.preventDefault(); dialog.close('cancel'); });
    dialog.querySelectorAll('[data-choice]').forEach(button => button.addEventListener('click', () => dialog.close(button.dataset.choice)));
    dialog.addEventListener('close', () => { const result = dialog.returnValue === 'confirm'; dialog.remove(); resolve(result); }, { once: true });
    dialog.showModal();
  });
}

function formatTime(timestamp) {
  const date = new Date(timestamp);
  return Number.isNaN(date.getTime()) ? t('recently') : date.toLocaleString(language(), { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' });
}

try {
  applyState(await getState());
  unsubscribe = subscribe(applyState);
  unsubscribeFocus = subscribeFocusInvalidation(() => mapWorkspace?.invalidateFocus());
} catch (error) {
  ui.error = error?.message || 'Could not open your saved interests. Please try again.';
  render();
}
window.addEventListener('pagehide', () => { unsubscribe?.(); unsubscribeFocus?.(); mapWorkspace?.destroy(); });
