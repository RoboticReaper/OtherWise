// Graph identities stay separate from title-based interest and Galaxy IDs.
export const isConceptId = value => typeof value === 'string' && /^Q\d+$/.test(value) && value.length <= 120;
export const isAreaId = value => typeof value === 'string' && /^[a-zA-Z0-9_-]{1,120}$/.test(value);
export const validRating = value => value && typeof value.curious === 'boolean' && typeof value.known === 'boolean' && ['none', 'too_basic', 'too_hard'].includes(value.difficulty);

export function cleanDiscoveryMetadata(value) {
  const text = s => typeof s === 'string' && s.length > 0 && s.length <= 240 && !/[\x00-\x1f\x7f]/.test(s);
  if (!value || !isConceptId(value.concept_id) || !isAreaId(value.area_id) ||
      !Array.isArray(value.graph_path) || !value.graph_path.length || value.graph_path.length > 8 || !value.graph_path.every(text) ||
      ![null, 1, 2, 3].includes(value.level) || typeof value.exploration_pick !== 'boolean' ||
      ![value.exploration_target, value.exploration_achieved].every(n => Number.isInteger(n) && n >= 0 && n <= 100) ||
      value.exploration_achieved > value.exploration_target) throw new Error('Invalid graph concept metadata.');
  let source = '';
  if (value.source_url) {
    const url = new URL(value.source_url);
    if (url.protocol !== 'https:' || url.username || url.password ||
        !['www.wikidata.org', 'wikidata.org', 'en.wikipedia.org'].includes(url.hostname) || !url.pathname.startsWith('/wiki/')) throw new Error('Invalid graph source.');
    source = url.href;
  }
  return {concept_id:value.concept_id, area_id:value.area_id, graph_path:[...value.graph_path], source_url:source,
    level:value.level, exploration_pick:value.exploration_pick, exploration_target:value.exploration_target, exploration_achieved:value.exploration_achieved};
}

export function createDiscoveryState() { return {feedback:{}, exposures:{}, undo:null, context:null}; }

export function normalizeDiscovery(value) {
  const next = createDiscoveryState();
  if (!value || typeof value !== 'object') return next;
  for (const [id, rating] of Object.entries(value.feedback || {}).slice(0, 4000)) {
    if (isConceptId(id) && validRating(rating) && isAreaId(rating.area_id)) next.feedback[id] = {...rating};
  }
  for (const [area, count] of Object.entries(value.exposures || {}).slice(0, 100)) {
    if (isAreaId(area) && Number.isInteger(count) && count >= 0 && count <= 1e9) next.exposures[area] = count;
  }
  if (value.undo && isConceptId(value.undo.conceptId) && (value.undo.previous === null || validRating(value.undo.previous))) next.undo = structuredClone(value.undo);
  if (value.context && Number.isInteger(value.context.seed) && value.context.seed >= 0 && value.context.seed <= 2**31-1) next.context = structuredClone(value.context);
  return next;
}

export function discoveryPayload(state) {
  const discovery = normalizeDiscovery(state.discovery);
  return {feedback:Object.entries(discovery.feedback).map(([concept_id, r]) => ({concept_id,area_id:r.area_id,curious:r.curious,known:r.known,difficulty:r.difficulty})),
    exposures:{...discovery.exposures}, seed:42,
    exploration_fraction:state.settings.discoveryExploration ?? .3};
}
