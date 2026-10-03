import {cleanDiscoveryMetadata} from '../core/discovery.js';
import {paginate} from './pagination.js';

export function discoveryControls(state, {text}) {
  const specific = state.settings.recommendationKind === 'specific';
  return `<div class="concept-controls"><label for="recommendation-kind">${text('recommendationKind')}</label><select id="recommendation-kind" data-focus="recommendation-kind"><option value="broad"${!specific?' selected':''}>${text('broadTopics')}</option><option value="specific"${specific?' selected':''}>${text('specificConcepts')}</option></select></div>${specific ? `<p class="concept-privacy">${text('specificPrivacy')}</p><label class="concept-exploration" for="discovery-exploration"><span>${text('lessSeenShare')}</span><select id="discovery-exploration" data-focus="discovery-exploration">${Array.from({length:11},(_,i)=>`<option value="${i/10}"${Math.abs(state.settings.discoveryExploration-i/10)<.001?' selected':''}>${i*10}%</option>`).join('')}</select></label><p class="muted small">${text('lessSeenHelp')}</p>` : ''}`;
}

export function graphDetails(topic, {text,escape}) {
  if (!topic.discovery) return '';
  let data;try { data = cleanDiscoveryMetadata(topic.discovery); } catch { return ''; }
  return `<div class="graph-details"><p class="graph-path">${escape(data.graph_path.join(' → '))}</p><p class="graph-level">${text(`readingLevel_${data.level??'unknown'}`)}${data.exploration_pick ? ` · ${text('reservedIdea')}`:''}</p><p class="muted small">${text('levelNote')}</p>${data.source_url?`<a href="${escape(data.source_url)}" target="_blank" rel="noopener noreferrer">${text('conceptSource')} ↗</a>`:''}</div>`;
}

export function savedFeedbackView(state, pageNumber, open, {text,escape,busy}) {
  const entries = Object.entries(state.discovery.feedback);
  const page = paginate(entries, pageNumber);
  const disabled = busy ? ' disabled' : '';
  return `<section class="feedback-tools"><div class="feedback-undo"><button type="button" data-action="undo-feedback"${!state.discovery.undo || busy?' disabled':''}>${text('undoFeedback')}</button><p class="muted small">${text('feedbackLocal')}</p></div><details id="discovery-feedback-panel"${open?' open':''}><summary data-focus="feedback-panel">${text('savedConceptFeedback',{count:entries.length})}</summary><p class="muted small">${text('feedbackEditHelp')}</p>${entries.length?`<ul class="saved-feedback-list">${page.items.map(([id,r])=>`<li><div><strong>${escape(r.topic||id)}</strong><p class="muted small">${[r.curious?text('curiousFeedback'):'',r.known?text('knownFeedback'):'',r.difficulty!=='none'?text(`difficulty_${r.difficulty}`):''].filter(Boolean).join(' · ') || text('difficulty_none')}</p></div><button type="button" class="quiet" data-action="clear-concept-feedback" data-concept-id="${escape(id)}"${disabled}>${text('clearRating')}</button></li>`).join('')}</ul>${page.pageCount>1?`<nav class="inbox-pagination" aria-label="${text('feedbackPagination')}"><button type="button" data-action="feedback-prev"${page.page===1||busy?' disabled':''}>${text('previous')}</button><span>${text('page',{page:page.page,pages:page.pageCount})}</span><button type="button" data-action="feedback-next"${page.page===page.pageCount||busy?' disabled':''}>${text('next')}</button></nav>`:''}`:`<p class="muted">${text('noConceptFeedback')}</p>`}<button type="button" class="quiet" data-action="clear-feedback"${(!entries.length && !Object.keys(state.discovery.exposures).length) || busy?' disabled':''}>${text('clearAllFeedback')}</button></details></section>`;
}
