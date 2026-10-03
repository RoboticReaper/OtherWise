import {RECOMMENDATION_DEFAULTS, normalizeRecommendationOptions, validRecommendationOptions} from './recommendation-options.js';

export const FOCUS_SCHEMA_VERSION = 1;
export const FOCUS_ALGORITHM_VERSION = 'catalog-focus-band-v1';
const IDENTITY_KEYS = ['catalog_sha256', 'model', 'embedding'];
const EMBEDDING_KEYS = ['sha256', 'dtype', 'shape'];
const OPTION_KEYS = Object.keys(RECOMMENDATION_DEFAULTS);
const REQUEST_KEYS = ['topic_id', ...IDENTITY_KEYS, ...OPTION_KEYS];
const ENVELOPE_KEYS = ['schema_version', 'algorithm_version', 'seed_id', ...IDENTITY_KEYS, 'recommendations'];
const RECOMMENDATION_KEYS = ['id', 'topic', 'domain', 'description', 'nearest_interest', 'distance', 'boundary_offset', 'zone'];
const TOLERANCE = 1e-6;
const object = value => value !== null && typeof value === 'object' && !Array.isArray(value);
const text = value => typeof value === 'string' && value.length > 0;
const hash = value => typeof value === 'string' && /^[a-f0-9]{64}$/.test(value);
const invalid = () => { throw new Error('The Focus data is invalid or does not match the topic catalog.'); };
const exactKeys = (value, keys) => object(value) && Object.keys(value).length === keys.length && keys.every(key => Object.hasOwn(value, key));

function copyIdentity(value, strict = true) {
  if (!object(value) || (strict && !exactKeys(value, IDENTITY_KEYS)) ||
      !hash(value.catalog_sha256) || !text(value.model) || !object(value.embedding)) invalid();
  const embedding = value.embedding;
  if ((strict && !exactKeys(embedding, EMBEDDING_KEYS)) || !hash(embedding.sha256) || !text(embedding.dtype) ||
      !Array.isArray(embedding.shape) || embedding.shape.length !== 2 ||
      !Number.isSafeInteger(embedding.shape[0]) || embedding.shape[0] <= 0 || embedding.shape[1] !== 768) invalid();
  return {catalog_sha256: value.catalog_sha256, model: value.model,
    embedding: {sha256: embedding.sha256, dtype: embedding.dtype, shape: [...embedding.shape]}};
}

/** Extract original asset identity; source metadata has additional layout fields. */
export function focusIdentity(metadata) {
  return copyIdentity(metadata, false);
}

/** Fixed wire allowlist: no interests, history, profile, or source-only identity. */
export function buildFocusRequest(seedId, identity, options = {}, catalogById) {
  if (!text(seedId) || !catalogById?.has(seedId) || !validRecommendationOptions(options)) invalid();
  return {topic_id: seedId, ...copyIdentity(identity), ...normalizeRecommendationOptions(options)};
}

function requestIdentity(request, catalogById) {
  if (!exactKeys(request, REQUEST_KEYS)) invalid();
  const identity = copyIdentity(Object.fromEntries(IDENTITY_KEYS.map(key => [key, request[key]])));
  const options = Object.fromEntries(OPTION_KEYS.map(key => [key, request[key]]));
  if (!text(request.topic_id) || !catalogById?.has(request.topic_id) || !validRecommendationOptions(options)) invalid();
  return identity;
}

/** Validate all rows before returning any drawable result; trust local text only. */
export function validateFocusResponse(raw, request, catalogById) {
  const expected = requestIdentity(request, catalogById);
  if (!exactKeys(raw, ENVELOPE_KEYS) || raw.schema_version !== FOCUS_SCHEMA_VERSION ||
      raw.algorithm_version !== FOCUS_ALGORITHM_VERSION || raw.seed_id !== request.topic_id ||
      !Array.isArray(raw.recommendations) || raw.recommendations.length > request.limit) invalid();
  const identity = copyIdentity(Object.fromEntries(IDENTITY_KEYS.map(key => [key, raw[key]])));
  if (identity.catalog_sha256 !== expected.catalog_sha256 || identity.model !== expected.model ||
      identity.embedding.sha256 !== expected.embedding.sha256 || identity.embedding.dtype !== expected.embedding.dtype ||
      identity.embedding.shape.some((value, index) => value !== expected.embedding.shape[index])) invalid();
  const seen = new Set();
  const lower = Math.max(0, request.radius - request.overlap), upper = Math.min(1, request.radius + request.expansion);
  const recommendations = raw.recommendations.map(row => {
    if (!exactKeys(row, RECOMMENDATION_KEYS) || !text(row.id) || !catalogById.has(row.id) ||
        row.id === request.topic_id || seen.has(row.id) || row.nearest_interest !== request.topic_id ||
        typeof row.topic !== 'string' || typeof row.domain !== 'string' || typeof row.description !== 'string' ||
        !Number.isFinite(row.distance) || row.distance < 0 || row.distance > 1 ||
        row.distance < lower - TOLERANCE || row.distance > upper + TOLERANCE ||
        !Number.isFinite(row.boundary_offset) || Math.abs(row.boundary_offset - (row.distance - request.radius)) > TOLERANCE ||
        !['New territory', 'Familiar overlap'].includes(row.zone)) invalid();
    seen.add(row.id);
    const topic = catalogById.get(row.id);
    return {...row, topic: topic.topic, domain: topic.domain, description: topic.description};
  });
  return {schema_version: FOCUS_SCHEMA_VERSION, algorithm_version: FOCUS_ALGORITHM_VERSION,
    seed_id: request.topic_id, ...identity, recommendations};
}
