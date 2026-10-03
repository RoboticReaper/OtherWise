// Numeric recommendation controls only; no history or hidden topics belong here.
export const RECOMMENDATION_DEFAULTS = Object.freeze({
  limit: 10, radius: .28, expansion: .07, overlap: .015,
  diversity: .20, max_overlap_fraction: .20, randomness: .03,
});

export const RECOMMENDATION_BOUNDS = Object.freeze(Object.fromEntries(
  Object.keys(RECOMMENDATION_DEFAULTS).map(key => [key, Object.freeze(
    key === 'limit' ? {min: 1, max: 100, integer: true} : {min: 0, max: key === 'max_overlap_fraction' ? .95 : 1}
  )]),
));

function validValue(key, value) {
  const bounds = RECOMMENDATION_BOUNDS[key];
  return Object.hasOwn(RECOMMENDATION_BOUNDS, key) && typeof value === 'number' && Number.isFinite(value) &&
    value >= bounds.min && value <= bounds.max && (!bounds.integer || Number.isInteger(value));
}

export function validRecommendationOptions(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value) &&
    Object.entries(value).every(([key, option]) => validValue(key, option));
}

// Older or damaged local storage falls back per field. The wire always has a fixed allowlist.
export function normalizeRecommendationOptions(value) {
  return Object.fromEntries(Object.entries(RECOMMENDATION_DEFAULTS).map(([key, fallback]) =>
    [key, validValue(key, value?.[key]) ? value[key] : fallback]));
}
