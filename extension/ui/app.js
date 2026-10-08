import {GALAXY_LAYOUT_DEFAULTS, GALAXY_LAYOUT_BOUNDS, normalizeGalaxyLayoutOptions} from '../core/galaxy-layout-options.js';
import { getState, dispatch, importHistory, recommend, search, subscribe, openDashboard, requestFocus, cancelFocus, subscribeFocusInvalidation, requestGalaxyLayout, pollGalaxyLayout } from '../bridge.js';
import { normalizeLanguage, translate, translateError } from './i18n.js';
import { paginate, PAGE_SIZE, recommendationCursor } from './pagination.js';
import { icon } from './icons.js';
import { createMapWorkspace } from './map-workspace.js';
import { galaxyLoader } from './galaxy-data.js';
import { RECOMMENDATION_DEFAULTS, RECOMMENDATION_BOUNDS, normalizeRecommendationOptions } from '../core/recommendation-options.js';
import {discoveryControls, graphDetails, savedFeedbackView} from './discovery.js';
import {gettingStartedGuide} from './getting-started.js';
const VIEWS = ['interests', 'discover', 'map', 'settings'];
const GUIDE_VIEWS = ['interests', 'discover', 'map'];

const app = document.querySelector('#app');
const params = new URLSearchParams(location.search);
const preview = params.get('preview') === '1';
const dashboard = document.body.classList.contains('dashboard');
const initialView = VIEWS.includes(params.get('view')) ? params.get('view') : 'discover';
const ui = {
  view: initialView, manual: '', days: '30', selected: new Set(), inboxOpen: true, candidatePage: 1, recommendationPage: 1,
  galaxyView: null, settingsDraft: null, settingsDirty: false, settingsSaved: false,
  advancedOptionsOpen: false, openGalaxyLayout: false,
  recommendationId: null, recommendationIndex: 0, recommendationView: dashboard ? 'cards' : 'single',
  openSections: new Set(),
  feedbackOpen: false, feedbackPage: 1, guideOpen: false, guideError: false, guideChecked: false, guideAutomatic: false,
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
    galaxyLayoutOptions: normalizeGalaxyLayoutOptions(settings.galaxyLayoutOptions),
    galaxyShowDomainLabels: settings.galaxyShowDomainLabels !== false, galaxyShowInterestLabels: settings.galaxyShowInterestLabels !== false,
  };
}

function applyState(next) {
  if (!next || typeof next !== 'object') return;
  if (next.lastUpdated !== state?.lastUpdated) {
    ui.recommendationPage = 1; ui.recommendationId = null; ui.recommendationIndex = 0;
  }
  if (state?.salt && state.salt !== next.salt) {
    mapWorkspace?.destroy(); mapWorkspace = null; ui.galaxyView = null;
    ui.feedbackPage = 1; ui.feedbackOpen = false; ui.guideChecked = false;
    ui.recommendationId = null; ui.recommendationIndex = 0;
  }
  state = next;
  ui.loaded = true;
  if (!ui.guideChecked) {
    ui.guideChecked = true;
    ui.guideOpen = !preview && !state.settings.tutorialSeen && !state.onboardingComplete && !state.approved.length;
    ui.guideAutomatic = ui.guideOpen; ui.guideError = false;
  } else if (ui.guideAutomatic && state.settings.tutorialSeen) {
    ui.guideOpen = false; ui.guideAutomatic = false;
  }
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
  const guideVisible = ui.loaded && ui.guideOpen && GUIDE_VIEWS.includes(ui.view);
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
  app.querySelectorAll('[data-disclosure]').forEach(details => {
    details.open ? ui.openSections.add(details.dataset.disclosure) : ui.openSections.delete(details.dataset.disclosure);
  });
  // Keeping the connected ancestor chain preserves browser fullscreen during state updates.
  const mountedMapContainer = app.querySelector('#galaxy-container');
  const retainMap = ui.view === 'map' && ui.loaded && !galaxyError && Boolean(mountedMapContainer && mapWorkspace?.element.isConnected && mapWorkspace.element.parentElement === mountedMapContainer);
  if (mapWorkspace) { mapWorkspace.setActive(ui.view === 'map'); if (!retainMap) mapWorkspace.element.remove(); }
  const error = ui.error || state?.lastError;
  document.documentElement.lang = language();
  document.title = t('title');
  app.setAttribute('aria-busy', String(!ui.loaded));
  const shell = `<div class="app-shell">
    <header class="app-header"><span class="brand">OtherWise<span class="brand-star" aria-hidden="true">✦</span></span>
      <div class="header-tools"><span class="connection-label${error ? ' has-error' : ''}">${text(!ui.loaded ? 'opening' : error ? 'attention' : preview ? 'demo' : 'local')}</span><button type="button" class="settings-button quiet" data-action="view" data-view="settings" data-focus="nav-settings" aria-label="${text('settings')}"${ui.view === 'settings' ? ' aria-current="page"' : ''}>${icon('settings')}</button></div>
    </header>
    <div class="workspace"><nav class="main-nav" aria-label="${text('mainNavigation')}">${['discover','interests','map'].map(view => `<button type="button" data-action="view" data-view="${view}" data-focus="nav-${view}"${ui.view === view ? ' aria-current="page"' : ''}>${icon({discover:'compass',interests:'bookmark',map:'orbit'}[view])}<span>${text(view)}</span></button>`).join('')}${!dashboard ? `<button type="button" class="dashboard-link" data-action="open-dashboard" aria-label="${text('openDashboard')}" title="${text('openDashboard')}"><span>${text('openDashboard')}</span><span aria-hidden="true" class="dashboard-arrow">↗</span></button>` : ''}<div class="nav-footer">${icon('shield')}<span>${text('local')}</span></div></nav><div class="workspace-content">
    ${preview ? `<details class="demo-notice"><summary>${text('demo')}</summary><p>${text('demoNotice')}</p></details>` : ''}
    ${error ? `<div class="error-banner" role="alert"><p><strong>${text('errorHeading')}</strong><br>${escape(translateError(language(), error))}${ui.view !== 'settings' ? `<br>${text('errorHint')}` : ''}</p><button type="button" class="quiet" data-action="clear-error" aria-label="${text('dismissError')}">×</button></div>` : ''}
    <div class="page-layout${guideVisible ? ' has-guide' : ''}"><main id="main-view">${!ui.loaded ? loadingView() : ui.view === 'settings' ? settingsView() : ui.view === 'map' ? mapView() : ui.view === 'interests' ? interestsView() : discoverView()}</main>
    ${guideVisible ? gettingStartedGuide({text,view:ui.view,step:GUIDE_VIEWS.indexOf(ui.view),total:GUIDE_VIEWS.length,busy:busy('guide'),seen:state.settings.tutorialSeen,error:ui.guideError}) : ''}</div>
    </div></div>
    <div class="sr-only" role="status" aria-live="polite">${ui.announcement ? text(ui.announcement) : ''}</div>
  </div>`;
  if (retainMap) refreshMapShell(shell); else app.innerHTML = shell;
  bindEvents();
  if (ui.view === 'map' && ui.loaded) drawMap();
  if (focused?.isConnected && mapWorkspace?.element.contains(focused)) focused.focus({preventScroll:true});
  if (focusKey) {
    let target = [...app.querySelectorAll('[data-focus]')].find(element => element.dataset.focus === focusKey);
    // A boundary button becomes disabled after paging. Keep keyboard focus nearby.
    if (target?.disabled && focusKey.startsWith('candidate-')) target = app.querySelector('.inbox-pagination button:not(:disabled)') || app.querySelector('.candidate-inbox summary');
    if (target?.disabled && focusKey.startsWith('recommendation-page-')) target = app.querySelector('.recommendation-pagination button:not(:disabled)') || app.querySelector('#recommendations-title');
    if (target?.disabled && ['topic-prev','topic-next'].includes(focusKey)) target = app.querySelector('.single-pagination button:not(:disabled)') || app.querySelector('#selected-topic-title');
    if (!target && focusKey === 'open-discover') target = app.querySelector('#recommendations-title');
    if (!target && focusKey === 'open-interests') target = app.querySelector('#manual-interest');
    if (!target && /^(recommendation-dismiss:|topic-row:|topic-more:|search-menu:)/.test(focusKey)) target = app.querySelector('#selected-topic-title') || app.querySelector('#recommendations-title');
    if (!target && focusKey.startsWith('search:')) target = app.querySelector('.topic-search summary') || app.querySelector('#recommendations-title');
    if (target?.closest('details:not([open])') && target.tagName !== 'SUMMARY') target = target.closest('details').querySelector('summary');
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

/** Replace shell siblings, never the ancestors of a mounted map/fullscreen target. */
function refreshMapShell(markup) {
  const template = document.createElement('template');
  template.innerHTML = markup;
  const incoming = template.content;
  const regions = [
    ['.app-header', '.app-shell'], ['.demo-notice', '.workspace-content', '.page-layout'],
    ['.main-nav', '.workspace'], ['.error-banner', '.workspace-content', '.page-layout'],
    ['.welcome-guide', '.page-layout'], ['.app-footer', '.workspace-content'],
    ['.app-shell > .sr-only', '.app-shell'], ['.galaxy-page > .view-heading', '.galaxy-page'],
  ];
  for (const [selector, parentSelector, beforeSelector] of regions) {
    const previous = app.querySelector(selector), next = incoming.querySelector(selector);
    if (previous && next) previous.replaceWith(next);
    else if (previous) previous.remove();
    else if (next) app.querySelector(parentSelector).insertBefore(next, beforeSelector ? app.querySelector(beforeSelector) : null);
  }
  app.querySelector('.page-layout').className = incoming.querySelector('.page-layout').className;
}

function loadingView() {
  return `<section class="empty-state"><h1>${text('headline')}</h1><p>${text('loadingInterests')}</p>${ui.error ? `<button type="button" data-action="reload">${text('retry')}</button>` : ''}</section>`;
}

function interestsView() {
  const approved = arr(state.approved);
  const candidates = arr(state.candidates);
  return `<div class="view-heading"><h1>${text('myInterests')}</h1><p>${text('interestHint')}</p></div>
    <form class="manual-form" id="manual-form"><label class="sr-only" for="manual-interest">${text('addInterest')}</label><input id="manual-interest" data-focus="manual-interest" name="interest" placeholder="${text('interestPlaceholder')}" maxlength="120" value="${escape(ui.manual)}" autocomplete="off"><button class="primary" data-focus="add-interest" type="submit"${disabled(busy('add'))}>${text(busy('add') ? 'saving' : 'add')}</button></form>
    <section class="section saved-interests" aria-labelledby="interests-title"><div class="section-heading"><h2 id="interests-title">${text('savedInterests')}</h2><span class="count">${approved.length}</span></div>${approved.length ? `<div class="interests">${approved.map(topic => `<span class="interest-chip"><span>${escape(topicTitle(topic))}</span><button type="button" data-action="remove" data-id="${escape(topicId(topic))}" aria-label="${text('removeInterest', { topic: topicTitle(topic) })}">×</button></span>`).join('')}</div>` : `<p class="muted small">${text('firstInterest')}</p>`}</section>
    ${approved.length ? `<div class="page-actions"><button type="button" class="primary" data-action="view" data-target-view="discover" data-focus="open-discover">${text('openDiscover')}${icon('arrow')}</button></div>` : ''}
    <details class="disclosure history-review" data-disclosure="history-review"${ui.openSections.has('history-review') ? ' open' : ''}><summary>${text('reviewBrowsing')}<span class="optional-label">${text('optional')}</span></summary><div class="disclosure-body"><p class="muted small">${text('introPrivacy')}</p><div class="import-row"><label class="sr-only" for="history-days">${text('historyPeriod')}</label><select id="history-days" data-focus="history-days"${disabled(busy('import'))}><option value="7"${ui.days === '7' ? ' selected' : ''}>${text('historyDays', { days: 7 })}</option><option value="30"${ui.days === '30' ? ' selected' : ''}>${text('historyDays', { days: 30 })}</option></select><button type="button" data-action="import"${disabled(busy('import'))}>${text(busy('import') ? 'reviewing' : 'reviewBrowsing')}</button></div></div></details>
    ${candidates.length ? inboxView(candidates) : ''}`;
}

function discoverView() {
  const approved = arr(state.approved);
  const items = arr(state.recommendations);
  const cursor = recommendationCursor(items, ui.recommendationId, ui.recommendationIndex);
  ui.recommendationId = cursor.id; ui.recommendationIndex = cursor.index;
  const page = paginate(items, Math.floor(cursor.index / PAGE_SIZE) + 1);
  ui.recommendationPage = page.page;
  const mode = state.settings?.mode || 'path';
  const single = ui.recommendationView === 'single';
  const specific = state.settings?.recommendationKind === 'specific';
  return `<section class="discover-page" aria-labelledby="recommendations-title"><div class="view-heading discover-heading"><div><h1 id="recommendations-title" data-focus="recommendations-title" tabindex="-1">${text('discover')}</h1><p>${text('discoverSubtitle')}</p></div><button type="button" class="refresh-button${items.length ? ' quiet' : ' primary'}" data-action="recommend"${disabled(!approved.length || busy('recommend') || busy('feedback'))}>${icon('refresh')}<span>${text(busy('recommend') || busy('feedback') ? 'finding' : items.length ? 'refreshIdeas' : 'findIdeas')}</span></button></div>
    <div class="discovery-context"><span>${approved.length ? mode === 'path' ? text('startingFrom',{topic:state.focus || topicTitle(approved.at(-1))}) : text('discoverySeeds',{count:approved.length}) : text('firstHelp')}</span><details class="discovery-adjust" data-disclosure="discovery-adjust"${ui.openSections.has('discovery-adjust') ? ' open' : ''}><summary>${text('adjust')}</summary><div class="disclosure-body">${discoveryControls(state,{text})}<label class="field"><span>${text('discoveryMode')}</span><select id="discovery-mode" data-focus="discovery-mode"><option value="path"${mode === 'path' ? ' selected' : ''}>${text('followPath')}</option><option value="global"${mode === 'global' ? ' selected' : ''}>${text('acrossInterests')}</option></select></label><p class="muted small">${mode === 'path' ? text('pathNote', {topic:state.focus || topicTitle(approved.at(-1))}) : text('globalNote')}</p><div class="adjust-actions"><button type="button" class="quiet" data-action="view" data-target-view="interests" data-focus="open-interests">${text('manageInterests')}</button><button type="button" class="quiet" data-action="view" data-view="settings">${text('adjustRecommendations')}</button></div><p class="muted small">${text('recommendationBatchHelp')}</p></div></details></div>
    <div class="discover-viewbar"><div class="view-switch" role="group" aria-label="${text('recommendationLayout')}">${[['cards','browse','grid'],['single','singleView','single']].map(([value,label,symbol]) => `<button type="button" data-action="recommendation-view" data-value="${value}" data-focus="recommendation-view-${value}" aria-pressed="${(value === 'single') === single}">${icon(symbol)}${text(label)}</button>`).join('')}</div>${items.length ? `<span class="muted small">${text('topicCount',{count:items.length})}</span>` : ''}</div>
    ${items.length ? single ? `<div class="single-discovery">${topicDetailView(cursor.topic, true)}<nav class="single-pagination" aria-label="${text('topicNavigation')}"><button type="button" class="quiet" data-action="topic-prev" data-focus="topic-prev"${disabled(cursor.index === 0)}>${icon('chevron')}<span>${text('previous')}</span></button><span role="status">${cursor.index + 1} / ${cursor.total}</span><button type="button" class="quiet" data-action="topic-next" data-focus="topic-next"${disabled(cursor.index === cursor.total - 1)}><span>${text('next')}</span>${icon('chevron')}</button></nav></div>` : `<div class="discovery-workbench"><div class="topic-browser"><nav class="topic-list" aria-label="${text('recommendedTopics')}">${page.items.map(topic => `<button type="button" class="topic-row" data-action="select-topic" data-id="${escape(topicId(topic))}" data-focus="topic-row:${escape(topicId(topic))}"${topicId(topic) === cursor.id ? ' aria-current="true"' : ''}><span class="topic-row-title">${escape(topicTitle(topic))}</span><span class="topic-row-domain">${escape(topic.domain || t('newDirection'))}</span>${icon('chevron')}</button>`).join('')}</nav>${page.pageCount > 1 ? `<nav class="recommendation-pagination" aria-label="${text('recommendationPagination')}"><button type="button" class="quiet" data-action="recommendation-prev" data-focus="recommendation-page-prev"${disabled(page.page === 1)} aria-label="${text('previous')}">${icon('chevron')}</button><span class="page-status" role="status">${page.page} / ${page.pageCount}</span><button type="button" class="quiet" data-action="recommendation-next" data-focus="recommendation-page-next"${disabled(page.page === page.pageCount)} aria-label="${text('next')}">${icon('chevron')}</button></nav>` : ''}</div>${topicDetailView(cursor.topic)}</div>` : `<div class="empty-state"><div class="empty-symbol" aria-hidden="true">✧</div><h2>${text(approved.length ? 'newRoom' : 'smallBeginning')}</h2><p>${text(approved.length ? 'findHelp' : 'firstHelp')}</p>${!approved.length ? `<button type="button" class="primary" data-action="view" data-target-view="interests" data-focus="open-interests">${text('addInterest')}</button>` : ''}</div>`}
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

function descriptionView(topic) {
  const description = topic.description || t('explorePace');
  if (description.length <= 220) return `<p class="topic-description">${escape(description)}</p>`;
  const id = topicId(topic);
  return `<details class="description-details" data-description="${escape(id)}"${ui.expandedDescriptions.has(id) ? ' open' : ''}><summary data-focus="description-${escape(id)}"><span class="description-preview">${escape(description.slice(0, 220).trimEnd())}… </span><span class="description-more">${text('readMore')}</span><span class="description-less">${text('readLess')}</span></summary><p class="topic-description">${escape(description)}</p></details>`;
}

function topicDetailView(topic, single = false) {
  const id = topicId(topic);
  const saved = isApproved(id);
  const graph = graphDetails(topic,{text,escape});
  return `<article class="topic-detail${single ? ' is-single' : ''}" aria-labelledby="selected-topic-title"><div class="topic-detail-copy"><p class="eyebrow">${escape(topic.domain || t('newDirection'))}</p><h2 id="selected-topic-title" data-focus="selected-topic-title" tabindex="-1">${escape(topicTitle(topic))}</h2>${descriptionView(topic)}${topic.nearest_interest ? `<p class="related">${text('connectionFrom', { topic: topic.nearest_interest })}</p>` : ''}</div><div class="topic-actions"><details class="topic-search"><summary class="primary" data-focus="search-menu:${escape(id)}">${icon('search')}<span>${text('searchTopic')}</span>${icon('chevron')}</summary><div class="topic-action-menu" role="group" aria-label="${text('searchWith')}">${searchButtons(topic)}</div></details>${saved ? `<span class="saved-label">${icon('check')}${text('savedCompact')}</span>` : `<button type="button" class="save" data-action="save-topic" data-id="${escape(id)}"${disabled(busy(`save:${id}`))}>${icon('bookmark')}${text('saveCompact')}</button>`}<details class="topic-more"><summary data-focus="topic-more:${escape(id)}" aria-label="${text('moreTopicActions')}">${icon('more')}</summary><div class="topic-action-menu"><button type="button" data-action="dismiss" data-id="${escape(id)}" data-focus="recommendation-dismiss:${escape(id)}">${text('notForMe')}</button></div></details></div>${graph ? `<details class="topic-source" data-disclosure="source:${escape(id)}"${ui.openSections.has(`source:${id}`) ? ' open' : ''}><summary>${text('sourceDetails')}</summary>${graph}</details>` : ''}</article>`;
}

function recommendationOptionField(key, draft) {
  const { min, max, integer } = RECOMMENDATION_BOUNDS[key];
  const id = `recommendation-${key}`;
  return `<label class="field recommendation-option"><span>${text(`option_${key}`)}</span><input id="${id}" name="${key}" data-recommendation-option="${key}" type="number" min="${min}" max="${max}" step="${integer ? '1' : 'any'}" required aria-describedby="${id}-help" data-focus="${id}" value="${escape(draft[key])}"><small id="${id}-help">${text(`optionHelp_${key}`)}</small></label>`;
}

function recommendationSettingsView(draft) {
  return settingsSection('settings-recommendations', 'recommendationSettings', `${recommendationOptionField('limit', draft)}<details id="recommendation-advanced"${ui.advancedOptionsOpen ? ' open' : ''}><summary data-focus="recommendation-advanced-summary">${text('advancedRecommendations')}</summary><p class="muted small">${text('recommendationDistanceHelp')}</p><div class="recommendation-option-grid">${Object.keys(RECOMMENDATION_DEFAULTS).filter(key => key !== 'limit').map(key => recommendationOptionField(key, draft)).join('')}</div></details><p class="muted small">${text('recommendationSettingsHelp')}</p><button type="button" class="quiet" data-action="reset-recommendation-options">${text('resetRecommendationDefaults')}</button>`, 'recommendation-settings');
}

function galaxySettingsView(draft) {
  return settingsSection('settings-galaxy', 'galaxyLayoutSettings', `<p class="muted small">${text('galaxyLayoutSettingsHelp')}</p><div class="recommendation-option-grid">${Object.keys(GALAXY_LAYOUT_DEFAULTS).map(key => {
    const {min,max,integer} = GALAXY_LAYOUT_BOUNDS[key], id = `galaxy-layout-${key}`;
    return `<label class="field recommendation-option"><span>${text(`galaxyOption_${key}`)}</span><input id="${id}" name="${key}" data-galaxy-option="${key}" type="number" min="${min}" max="${max}" step="${integer ? '1' : 'any'}" required aria-describedby="${id}-help" data-focus="${id}" value="${escape(draft.galaxyLayoutOptions[key])}"><small id="${id}-help">${text(`galaxyOptionHelp_${key}`)}</small></label>`;
  }).join('')}</div>${[['galaxyShowDomainLabels','galaxy-show-domain-labels'],['galaxyShowInterestLabels','galaxy-show-interest-labels']].map(([key,id]) => `<label class="toggle-row"><input id="${id}" name="${key}" type="checkbox" data-galaxy-label="${key}" data-focus="${id}"${checked(draft[key])}><span><strong>${text(key)}</strong></span></label>`).join('')}<div class="galaxy-settings-actions"><button type="button" class="quiet" data-action="reset-galaxy-options">${text('restoreGalaxyB')}</button><button type="button" data-action="open-galaxy-layout">${text('openGalaxyLayout')}</button></div><p class="muted small">${text('galaxyLayoutSaveHelp')}</p>`, 'galaxy-settings');
}

function settingsSection(key, title, body, classes = '') {
  return `<details class="settings-group disclosure ${classes}" data-disclosure="${key}"${ui.openSections.has(key) ? ' open' : ''}><summary data-focus="${key}">${text(title)}</summary><div class="disclosure-body">${body}</div></details>`;
}

function searchButtons(topic) {
  const id = topicId(topic);
  return `<button type="button" data-action="search" data-id="${escape(id)}" data-provider="google"${disabled(busy(`search:${id}:google`))}>Google <span aria-hidden="true">↗</span></button><button type="button" data-action="search" data-id="${escape(id)}" data-provider="youtube"${disabled(busy(`search:${id}:youtube`))}>YouTube <span aria-hidden="true">↗</span></button>`;
}

function settingsView() {
  const settings = state.settings || {};
  const draft = ui.settingsDraft || snapshotSettings();
  return `<section class="settings"><div class="view-heading"><h1>${text('settings')}</h1></div>
    <div class="settings-language-row">${languageSelect('settings-language')}</div>
    ${settingsSection('settings-discovery','discovery',`<label class="field"><span>${text('connections')}</span><select id="settings-mode" data-focus="settings-mode" aria-label="${text('connections')}"><option value="path"${settings.mode !== 'global' ? ' selected' : ''}>${text('followLatest')}</option><option value="global"${settings.mode === 'global' ? ' selected' : ''}>${text('exploreAll')}</option></select><small>${text('modeHelp')}</small></label>
    <label class="toggle-row"><input id="browsing-enabled" type="checkbox" aria-label="${text('browsingEnabled')}" aria-describedby="browsing-help" data-focus="browsing-enabled"${checked(settings.browsingEnabled)}${disabled(busy('browsing'))}><span><strong>${text('browsingEnabled')}</strong><small id="browsing-help">${text('browsingHelp')}</small></span></label>
    <label class="toggle-row"><input id="auto-refresh" type="checkbox" aria-label="${text('autoRefresh')}" aria-describedby="refresh-help" data-focus="auto-refresh"${checked(settings.autoRefresh)}${disabled(busy('auto-refresh'))}><span><strong>${text('autoRefresh')}</strong><small id="refresh-help">${text('refreshHelp')}</small></span></label>
    <label class="toggle-row"><input id="galaxy-exploration-mode" type="checkbox" aria-describedby="exploration-mode-help" data-focus="galaxy-exploration-mode"${checked(settings.galaxyExplorationMode)}${disabled(busy('galaxy-exploration'))}><span><strong>${text('galaxyExplorationMode')}</strong><small id="exploration-mode-help">${text('galaxyExplorationHelp')}</small></span></label>`)}
    <form class="settings-form" id="settings-form" novalidate>${recommendationSettingsView(draft.recommendationOptions)}${galaxySettingsView(draft)}${settingsSection('settings-connection','serviceConnection',`<p class="muted small">${text('serviceHelp')}</p><label class="field"><span>${text('serviceAddress')}</span><input id="endpoint" name="endpoint" type="url" aria-label="${text('serviceAddress')}" aria-describedby="endpoint-help" data-focus="endpoint" value="${escape(draft.endpoint)}" placeholder="https://your-demo-address" spellcheck="false" autocomplete="off" required><small id="endpoint-help">${text('endpointHelp')}</small></label><label class="field"><span>${text('teamCode')}</span><input id="access-token" name="accessToken" type="password" aria-label="${text('teamCode')}" aria-describedby="token-help" data-focus="access-token" value="${escape(draft.accessToken)}" placeholder="${text('codePlaceholder')}" autocomplete="off" spellcheck="false"><small id="token-help">${text('codeHelp')}</small></label>`)}
    ${settingsSection('settings-exclusions','excludedWebsites',`<p class="muted small">${text('excludedHelp')}</p><label class="field"><span>${text('domainsToSkip')}</span><textarea id="blocked-domains" name="blockedDomains" aria-label="${text('domainsToSkip')}" aria-describedby="domains-help" data-focus="blocked-domains" spellcheck="false">${escape(draft.blockedDomains)}</textarea><small id="domains-help">${text('domainsHelp')}</small></label>`)}
    <div class="actions"><button class="primary" data-focus="save-settings" type="submit"${disabled(busy('settings'))}>${text(busy('settings') ? 'saving' : 'saveSettings')}</button><span class="muted" role="status">${ui.settingsDirty ? text('unsaved') : ui.settingsSaved ? text('settingsSaved') : ''}</span></div></form>
    ${settingsSection('settings-data','localData',`<p class="muted small">${text('localDataHelp')}</p><div class="data-actions"><button type="button" data-action="clear-derived">${text('clearBrowsing')}</button><button type="button" class="danger" data-action="reset">${text('reset')}</button></div><p class="privacy-note">${text('privacy')}</p>`)}
    ${settingsSection('settings-guide','guideTitle',`<p class="muted small">${text('guideReplayHelp')}</p><button type="button" data-action="open-guide" data-focus="open-guide">${text('showGuide')}</button>`)}</section>`;
}

function mapView() {
  return `<section class="galaxy-page"><div class="view-heading"><h1>${text('map')}</h1><p>${text('galaxyIntro')}</p></div>
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
      presentation: dashboard ? 'dashboard' : 'sidebar', preview, requestFocus, cancelFocus, requestGalaxyLayout, pollGalaxyLayout,
      onGalaxySettings: async patch => {
        const next = await dispatch({type:'SET_SETTINGS',patch});
        if(Object.keys(patch).some(key=>JSON.stringify(next.settings[key])!==JSON.stringify(patch[key]))) throw new Error(next.lastError || 'The Galaxy settings could not be saved.');
        applyState(next); return next;
      },
      onSave: topic => run(`save:${topicId(topic)}`, () => dispatch({type:'ADD_INTEREST', topic}), 'interestSaved'),
      onDismiss: id => run(`dismiss:${id}`, () => dispatch({type:'DISMISS', id}), 'topicDismissed'),
      onCustomFocus: focusMapTopic,
      onSearch: (topic, provider, context) => run(`search:${topicId(topic)}`, () => search(topic, provider, context), 'explorationRecorded'),
      onSettings: () => { navigate('settings'); revealField(document.querySelector('#endpoint')); },
    });
    if (mapWorkspace.element.parentElement !== container) container.append(mapWorkspace.element);
    mapWorkspace.update({state, language: language()});
    mapWorkspace.setActive(true);
    if (ui.openGalaxyLayout) { ui.openGalaxyLayout = false; mapWorkspace.openGalaxyLayoutEditor(); }
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
  if (next && !next.lastError) { navigate('discover'); document.querySelector('#recommendations-title')?.focus(); }
}

function bindEvents() {
  app.querySelectorAll('[data-disclosure]').forEach(details => details.addEventListener('toggle', event => {
    if (!event.target.isConnected) return;
    event.target.open ? ui.openSections.add(event.target.dataset.disclosure) : ui.openSections.delete(event.target.dataset.disclosure);
  }));
  app.querySelectorAll('[data-guide-action]').forEach(button=>button.addEventListener('click',()=>{
    if (busy('guide')) return;
    const action=button.dataset.guideAction;
    if (action==='next' || action==='back') {
      const step=GUIDE_VIEWS.indexOf(ui.view);
      navigate(GUIDE_VIEWS[Math.max(0,Math.min(GUIDE_VIEWS.length-1,step+(action==='next'?1:-1)))]);
      document.getElementById('guide-heading')?.focus({preventScroll:true});
    } else void finishGuide();
  }));
  document.getElementById('recommendation-kind')?.addEventListener('change', event => run('kind', () => dispatch({type:'SET_SETTINGS',patch:{recommendationKind:event.target.value}}), 'kindSaved'));
  document.getElementById('discovery-exploration')?.addEventListener('change', event => run('exploration-share', () => dispatch({type:'SET_SETTINGS',patch:{discoveryExploration:Number(event.target.value)}}), 'shareSaved'));
  document.getElementById('discovery-feedback-panel')?.addEventListener('toggle', event => {if(event.target.isConnected)ui.feedbackOpen=event.target.open;});
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
    const galaxyOption = event.target.dataset.galaxyOption;
    const galaxyLabel = event.target.dataset.galaxyLabel;
    if (galaxyOption) ui.settingsDraft.galaxyLayoutOptions[galaxyOption] = event.target.value;
    else if (galaxyLabel) ui.settingsDraft[galaxyLabel] = event.target.checked;
    else if (option) ui.settingsDraft.recommendationOptions[option] = event.target.value;
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
    revealField(invalid);
    invalid.reportValidity();
    return;
  }
  const draft = structuredClone(ui.settingsDraft);
  const recommendationOptions = Object.fromEntries(Object.entries(draft.recommendationOptions).map(([key, value]) => [key, Number(value)]));
  let galaxyLayoutOptions;
  try { galaxyLayoutOptions = normalizeGalaxyLayoutOptions(Object.fromEntries(Object.entries(draft.galaxyLayoutOptions).map(([key,value])=>[key,Number(value)])),{strict:true}); }
  catch { ui.error = 'Enter valid Galaxy layout settings. Minimum distance must not exceed spread.'; render(); revealField(document.querySelector('#galaxy-layout-min_dist')); return; }
  const domains = [...new Set(draft.blockedDomains.split(/[\n,]+/).map(domain => domain.trim().toLowerCase()).filter(Boolean))];
  if (domains.some(domain => !/^[a-z0-9]+(?:[a-z0-9.-]*[a-z0-9])?$/.test(domain) || domain.includes('..'))) {
    ui.error = 'Enter domain names without https://, paths, or spaces. Use one domain per line.';
    render();
    revealField(document.querySelector('#blocked-domains'));
    return;
  }
  const next = await run('settings', () => dispatch({ type: 'SET_SETTINGS', patch: { endpoint: draft.endpoint.trim(), accessToken: draft.accessToken.trim(), blockedDomains: domains, recommendationOptions, galaxyLayoutOptions, galaxyShowDomainLabels: draft.galaxyShowDomainLabels, galaxyShowInterestLabels: draft.galaxyShowInterestLabels } }), 'settingsSaved');
  if (!next || next.lastError) revealField(document.querySelector('#endpoint'));
  if (next && !next.lastError && JSON.stringify(ui.settingsDraft) === JSON.stringify(draft)) {
    ui.settingsDirty = false;
    ui.settingsSaved = true;
    ui.settingsDraft = snapshotSettings();
    render();
  }
}

function revealField(field) {
  if (!field) return;
  for (let parent = field.parentElement; parent; parent = parent.parentElement) {
    if (parent.tagName !== 'DETAILS') continue;
    parent.open = true;
    if (parent.dataset.disclosure) ui.openSections.add(parent.dataset.disclosure);
    if (parent.id === 'recommendation-advanced') ui.advancedOptionsOpen = true;
  }
  field.focus();
}

function selectRecommendation(index, reveal = false) {
  const cursor = recommendationCursor(state.recommendations, null, index);
  ui.recommendationId = cursor.id; ui.recommendationIndex = cursor.index;
  ui.recommendationPage = Math.floor(cursor.index / PAGE_SIZE) + 1;
  render();
  if (reveal && matchMedia('(max-width: 620px)').matches) {
    document.querySelector('#selected-topic-title')?.focus({preventScroll:true});
    document.querySelector('.topic-detail')?.scrollIntoView({block:'start',behavior:'auto'});
  }
}

async function onAction(event) {
  const button = event.currentTarget;
  const { action, id, provider } = button.dataset;
  if (action === 'open-dashboard') { await run('dashboard', () => openDashboard('discover')); return; }
  if (action === 'retry-galaxy') { galaxyError = false; galaxyAssets = null; galaxyLoader.invalidate(); render(); return; }
  if (action === 'recommendation-view') {
    ui.recommendationView = button.dataset.value === 'single' ? 'single' : 'cards';
    ui.announcement = 'layoutChanged';
    render();
    return;
  }
  if (action === 'select-topic') { selectRecommendation(state.recommendations.findIndex(topic => topicId(topic) === id), true); return; }
  if (action === 'topic-prev' || action === 'topic-next') { selectRecommendation(ui.recommendationIndex + (action === 'topic-next' ? 1 : -1)); return; }
  if (action === 'view') { navigate(button.dataset.view || button.dataset.targetView); return; }
  if (action === 'open-guide') {ui.guideOpen=true;ui.guideAutomatic=false;ui.guideError=false;ui.error=null;navigate('interests');document.getElementById('guide-heading')?.focus({preventScroll:true});return;}
  if (action === 'clear-error') { ui.error = null; if (state?.lastError) await run('clear-error', () => dispatch({ type: 'CLEAR_ERROR' })); else render(); return; }
  if (action === 'reload') { const next = await run('reload', getState); if (next && !unsubscribe) unsubscribe = subscribe(applyState); return; }
  if (action === 'import') { ui.inboxOpen = true; await run('import', () => importHistory(Number(ui.days)), 'importReady'); return; }
  if (action === 'approve') { await run('approve', () => dispatch({ type: 'APPROVE', ids: [...ui.selected] }), 'selectedSaved'); return; }
  if (action === 'candidate-prev' || action === 'candidate-next') {
    ui.candidatePage = paginate(arr(state.candidates), ui.candidatePage + (action === 'candidate-next' ? 1 : -1)).page;
    render(); return;
  }
  if (action === 'recommendation-prev' || action === 'recommendation-next') {
    const page = paginate(arr(state.recommendations), ui.recommendationPage + (action === 'recommendation-next' ? 1 : -1));
    selectRecommendation((page.page - 1) * PAGE_SIZE, true); return;
  }
  if (action === 'open-galaxy-layout') { ui.openGalaxyLayout = true; navigate('map'); return; }
  if (action === 'reset-galaxy-options') {
    ui.settingsDraft.galaxyLayoutOptions = {...GALAXY_LAYOUT_DEFAULTS};
    ui.settingsDirty = true; ui.settingsSaved = false; render(); return;
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
    if(next){render();}return;
  }
  if(action==='clear-feedback'){
    if(!await confirmDialog(t('clearAllFeedback'),t('clearFeedbackDescription'),t('clearAllFeedback')))return;
    const next=await run('feedback',()=>dispatch({type:'CLEAR_DISCOVERY_FEEDBACK'}),'feedbackCleared');
    if(next && !next.lastError){ui.feedbackPage=1;render();}return;
  }
  if (action === 'clear-derived' || action === 'reset') {
    const reset = action === 'reset';
    const confirmed = await confirmDialog(t(reset ? 'startOver' : 'confirmClear'), t(reset ? 'resetDescription' : 'clearDescription'), t(reset ? 'reset' : 'clearBrowsing'));
    if (!confirmed) return;
    const next = await run(action, () => dispatch({ type: reset ? 'RESET' : 'CLEAR_DERIVED' }), reset ? 'resetDone' : 'clearDone');
    if (reset && next && !next.lastError) { mapWorkspace?.destroy(); mapWorkspace = null; ui.manual = ''; ui.settingsDirty = false; ui.settingsSaved = false; ui.settingsDraft = snapshotSettings(); ui.galaxyView = null; ui.selected.clear(); ui.expandedDescriptions.clear(); ui.feedbackPage = 1; ui.candidatePage = 1; ui.recommendationPage = 1; navigate('interests'); }
  }
}

function navigate(view) {
  if (!VIEWS.includes(view)) return;
  ui.view=view;
  if (view==='settings' && !ui.settingsDirty) ui.settingsDraft=snapshotSettings();
  const url=new URL(location.href);url.searchParams.set('view',view);history.replaceState(null,'',url);
  render();window.scrollTo(0,0);
}

async function finishGuide() {
  ui.guideError=false;
  const next=await run('guide',()=>dispatch({type:'SET_SETTINGS',patch:{tutorialSeen:true}}));
  if (!next?.settings?.tutorialSeen) {ui.guideError=true;render();return;}
  ui.guideOpen=false;ui.guideAutomatic=false;
  render();
  document.querySelector(`[data-focus="nav-${ui.view}"]`)?.focus({preventScroll:true});
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
document.addEventListener('click', event => {
  app.querySelectorAll('.topic-search[open], .topic-more[open]').forEach(menu => {
    if (!menu.contains(event.target)) menu.open = false;
  });
});
document.addEventListener('keydown', event => {
  if (event.key !== 'Escape') return;
  const menu = app.querySelector('.topic-search[open], .topic-more[open]');
  if (menu) { menu.open = false; menu.querySelector('summary').focus(); event.preventDefault(); }
});
