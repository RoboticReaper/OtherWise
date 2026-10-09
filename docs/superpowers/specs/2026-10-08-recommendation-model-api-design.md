# Recommendation model API and trajectory design

Approved direction: implement the previously discussed candidates and baselines in the backend, including trajectory-guided expansion. The user specified optional `date` on each interest. This implements runnable models, not a human-study protocol or an expansion-effect claim.

## Contract

Keep existing `/api/recommend`, `/api/discover` and `/api/focus` requests working. Add a model-selected request on `/api/recommend`: `model`, `interests` (or `keywords`), optional controls and inventory version. Interests remain strings or become `{ "phrase": "…", "date": "YYYY-MM-DD", "concept_id": "…" }`; date and concept ID are optional. Also accept timezone-qualified ISO timestamps. Meaning selections require the matching inventory revision. Support repeated dated observations of the same interest, reject invalid dates and ambiguous meanings without guessing, and exclude previously supplied/explicitly known concepts across the entire history.

`GET /api/recommend/models` lists selectable models, roles, configurations and actual readiness. All study candidates use shared source-backed cards and the same catalog snapshot. Expose K-connection, K-literal, V0, V3, semantic-nearest, BM25, seeded random, history-recency and trajectory; retain existing implemented intermediates/ablations as optional controls. V4b is an unconfigured external adapter, not a study candidate or an available external model.

## Algorithms

Preserve raw historical lab V0 and frozen K/V3 configurations. The selected V0/V1 API versions add explicit, versioned serving guards for clarification, chosen meanings and known/duplicate outputs around the historical ranker. The guard version changes algorithm identity; it is a distinct comparator from raw V0. Simple baselines share known/duplicate exclusions and an explicit maximum angular distance of .50, with no original annular eligibility band. Semantic-nearest uses canonical similarity; BM25 ranks actual lexical matches; random samples eligible identities reproducibly.

The history pair shares eligibility, static hybrid retrieval, recency profiles, expansion/diversity scoring and descriptions. Only trajectory adds a direction/velocity score. Group dated observations into semantic strands within angular distance .25, sort by date, aggregate equal-time observations and estimate a recency-weighted tangent velocity. Default half-life: 60 days; forecast: 14 days; maximum angular step: .12. Three distinct dates and a fit score at least .5 are implementation heuristics for using a direction, not validated universal thresholds. Use fixed catalog embeddings, bounded controls and no request-dependent embedding retraining. Undated interests remain static anchors. Sparse, stationary or inconsistent history disables direction with an explicit diagnostic.

Reward connected expansion opportunities through a shared moderate-distance feature and list diversity; never describe these geometric features as measured interest acquisition. `exploration_fraction` tunes the expansion feature. Respect path focus while excluding known interests globally. Report history confidence, strand count, velocity use and fallback status so tests can distinguish an active trajectory from a static result. Serve statelessly and cache only public catalog vectors.

## Verification

Test public lab recommendation calls and authenticated HTTP requests. Verify actual directional preference on a worked geometric fixture, timestamp ordering, independent strands, equal-date and sparse-history fallback, duplicate known exclusions, pure lexical/semantic baselines, seeded reproducibility, cross-thread serving, invalid-input privacy and old request compatibility. Run the complete Python suite and real-model HTTP smoke checks for every selectable model in both result kinds. Smoke checks establish execution/readiness, not expansion effectiveness. Preserve historical benchmark artifacts and unrelated catalog work.
