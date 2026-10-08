# OtherWise recommendation system — implementation spec

Date: 2026-10-07. Status: approved direction; this written spec is ready for review before implementation planning. No metric-specific proxy champion has been selected. Human trials are optional; the initial personal rubric sanity check is complete, with versioned challenger treatments recorded in the evaluation design.

## Problem Statement

OtherWise should suggest unfamiliar topics with a recognizable connection to the person's interests and a reason to explore them. That goal should be tunable toward deeper exploration of existing interests. The current recommender optimizes an embedding-distance band rather than measured curiosity, and its input and retrieval stages can prevent suitable suggestions from reaching the ranker.

The audit established three distinct problems:

- A name does not reliably identify a meaning. Broad and specific discovery give Fermentation different descriptions; Go can recommend Go (game) as new territory.
- Missing aliases, missing concepts, and premature filtering are different coverage failures. Eight-area routing loses every eligible graph candidate in the Python snake and causal representation learning probes.
- Distance, category membership, and balanced domain counts do not establish personal familiarity, curiosity, or a useful starting point.

The implementation must improve these stages independently and establish which changes help under frozen automated scorecards, with optional user judgments of real curiosity.

## Solution

Build a recommendation pipeline around source-backed concept identities, with context-aware meaning resolution, retrieval across the available inventory, and ranking that balances connectedness, discovery, and variety. Retain graph relationships as an additional retrieval signal and provenance. Compare optional external AI assistance against the local pipeline rather than assuming it improves quality.

Default to unfamiliar, connected discovery. Let the person adjust the discovery goal, use explicitly saved interests as context, and offer a short meaning choice when interpretation remains uncertain. Preserve a local baseline and existing map behavior throughout the experiments.

Deliver in three stages:

| Stage | Deliverable | Exit condition |
|---|---|---|
| 1 | Reproducible benchmark, concept identities, and local retrieval/ranking variants | Structural regressions covered; automatic grades, per-metric scoreboards, and an initial rating packet generated |
| 2 | Source-backed catalog expansion and optional external resolution/reranking challengers | Each treatment measured separately, including errors, latency, and cost |
| 3 | Versioned API and minimal existing-client integration for the selected pipeline | Held-out proxy scorecards support the selected per-goal champions; compatibility and failure handling verified |

Stages are implementation boundaries, not three assumptions of improvement. A challenger can be rejected while the benchmark and identity corrections remain useful.

## User Stories

1. As a person exploring interests, I want unfamiliar but connected suggestions by default, so that I discover something worth exploring.
2. As that person, I want to adjust the discovery goal toward closer exploration, so that the same system supports different intentions.
3. As someone entering an ambiguous phrase, I want my saved interests to provide context and a meaning choice when needed, so that the system follows my intended sense.
4. As someone using a synonym or niche phrase, I want alternate names recognized and unsupported phrases handled honestly, so that missing exact titles do not silently determine my results.
5. As someone who marks a concept known, I want its alternate names excluded too, so that it is not repeatedly presented as a discovery.
6. As someone receiving a specific suggestion, I want its description, source, and connection evidence, so that I can judge why it is relevant and where to start.
7. As someone using the existing extension, I want saved interests, feedback, and map behavior preserved, so that experiments do not disrupt my profile.
8. As someone using a configured external challenger, I want a usable local result when that service fails, so that discovery remains available.
9. As the developer, I want to compare input resolution, retrieval, ranking, and inventory expansion separately, so that I know what caused a measured gain.
10. As an evaluator, I want anonymous, randomized candidate packets with consistent presentation, so that algorithm names and rewritten hooks do not bias judgments.
11. As an evaluator, I want missing ratings distinguished from low ratings, so that incomplete annotation cannot produce a false winner.
12. As the developer, I want held-out quality, failure cases, and measured resource costs, so that I can select a defensible default and retain rollback options.

## Implementation Decisions

### One recommendation boundary

Introduce one versioned recommendation application boundary: a validated request produces a result batch with input resolutions, recommendations, and execution metadata. The experiment runner and the new HTTP adapter call this same boundary. Keep concept indexing, resolver, retrievers, ranker, and external adapters behind it rather than exposing separate public services.

Reuse existing catalog loaders, angular-distance calculations, graph traversal, explicit feedback behavior, and injected model/vector fixtures where their contracts fit. Preserve the original engines as executable baselines. Tests should primarily exercise this application boundary and authenticated HTTP requests.

### Concept identity and inventory

A concept record contains a stable ID, label, description, aliases, language, source identities/revisions, available presentation kinds, and observed graph memberships. Preserve reviewed reading-level annotations without inventing levels for unreviewed concepts.

Use Wikidata IDs where applicable and stable local IDs for authored concepts. Local IDs survive label edits. Alias lookup maps a normalized phrase to a set of IDs. Two distinct concepts may share a label or alias. Several source records for one verified concept may share an ID and retain their own provenance.

Merge identities only through a shared source ID or a reviewed equivalence mapping. Do not merge by matching labels or embedding proximity. Review the Go/Go (game) equivalence and retain separate authored culinary fermentation and metabolic-process meanings unless evidence establishes equivalence. Conflicting descriptions must not overwrite each other based on endpoint or input-list order.

The inventory combines broad topics and graph concepts for resolution. The requested presentation kind determines the final candidate universe: broad topics or specific concepts. Initial comparisons keep that universe fixed. Every returned concept has one identity even when it belongs to several areas.

Version the inventory, alias/equivalence mappings, descriptions, source snapshots, and embedding texts. Public embedding caches include those identities, the exact model revision, and encoding configuration. Different models or source revisions cannot share a cache merely because their model names match.

### Interest interpretation

Resolve each interest independently using its phrase, explicit selected concept ID when present, and the other explicitly saved interests in the same request. Keep separate anchors rather than averaging unrelated interests or competing meanings.

Return one of three states for each interest:

- **Resolved:** a validated explicit meaning choice or an interpretation supported by the resolver's documented policy.
- **Clarification needed:** several plausible meanings remain. Return up to five source-backed choices with labels/descriptions and an option to refine the phrase. Return no recommendation list for that batch; do not silently omit the uncertain interest.
- **Unresolved phrase:** no supported concept mapping exists. Preserve the phrase for semantic/lexical retrieval and mark it unresolved. Do not invent a canonical identity or call it a known concept.

Initially auto-resolve unambiguous exact aliases and explicit choices. Contextual score thresholds must be calibrated on development fixtures with verified intended meanings before enabling automatic contextual selection. Until calibrated, contextual scores order meaning choices; they are not confidence probabilities. An exact label match does not override competing meanings.

The same selected concept receives the same contextual representation in broad and specific requests. A later meaning choice is checked against the inventory version and the offered candidate set recomputed from the request. Stale choices produce a version conflict rather than switching meanings.

### Retrieval and ranking

At the current inventory size, use exact full-dimensional matrix search before considering approximate indexes. Add a local SQLite FTS5/BM25 index over labels, aliases, and descriptions. Lexical-index unavailability must be reported for the affected variant rather than silently turning a hybrid comparison into semantic-only retrieval.

For each resolved interest, retrieve semantic and lexical rankings. The optional graph channel uses existing area routing and verified memberships. Combine rankings using reciprocal rank fusion, initially with equal channel weights and rank constant 60; record both in the experiment manifest. These are initial experiment settings, not validated optimal weights. Keep source paths attached to their actual concepts.

Evaluate eligibility before truncating the retrieval pool, so nearest-neighbor retrieval cannot discard the outward band. The graph channel adds candidates or ranking evidence; it never acts as a mandatory gate for global semantic/lexical retrieval. A graph path remains category provenance, not a prerequisite, difficulty estimate, or proof of personal relevance.

Use separate score components for retrieval relevance, band fit, explicit curiosity, reviewed difficulty fit, and result redundancy. Preserve known-concept exclusions, feedback independence, bounded randomness, and exposure-based exploration reservations. Retrieve globally before applying exposure reservations; do not let exposure preferences invent candidates or bypass eligibility.

The user-facing goal selects connection, connected discovery, deeper exploration, or relevant variety. Connected discovery is the default. Maintain a champion pipeline/configuration for each goal; one configuration may win several. Tune those weights on development data, freeze them before held-out evaluation, and store them in the selected algorithm manifest. Goal changes ranking, not consent, concept identity, known exclusions, or hidden eligibility limits.

Initial variants retain radius 0.28, expansion 0.07, overlap 0.015, diversity 0.20, overlap share 0.20, and zero randomness for comparisons. Goal and distance controls are separate: a closer goal cannot recover candidates the person has explicitly excluded through the distance controls. Adaptive novelty without the hard band is a separately named experiment, never a silent change to existing sliders.

For the new pipeline, global eligibility measures distance to the closest approved interest. Path retrieval uses the selected focus for its upper/lower band and also enforces the lower bound against every approved interest. Classify geometric overlap against every approved interest. Return anchor distance and nearest-interest distance separately. A candidate close to another saved interest cannot be called outside every interest neighborhood merely because it is farther from the focus. These geometric labels still do not assert the person's actual familiarity.

### Controlled variants

| Variant | Change from its comparison baseline |
|---|---|
| V0 | Original graph routing, input lookup, and ranker |
| V1 | V0 with all graph areas available; same input vectors and ranker |
| V2 | V1 with canonical identities, aliases, and sense resolution |
| V3 | V2 with lexical/semantic/optional graph fusion and relevance/discovery/diversity ranking |
| V4a | V3 with externally assisted sense resolution |
| V4b | V3 with external candidate reranking |

Keep broad and specific comparisons separate. For V3, ablate lexical retrieval, graph contribution, and ranking changes independently. Human-confirmed meanings can be used as a separate diagnostic arm, clearly identified as oracle input rather than an automatic resolver result. Only automatic or interactive arms qualify for product comparison.

Run catalog expansion as a separate treatment: hold the pipeline fixed while changing the source-backed inventory, then compare relevant algorithms on both inventory snapshots. Candidate discovery may use external assistance, but inclusion requires a verified source or documented authored provenance, identity/type review, a useful description, and deduplication. An unsupported generated topic or citation cannot enter production results. Failed imports leave the last valid snapshot available. Held-out test inputs cannot be used to tune expansion.

### Optional external assistance

External adapters are explicitly configured challengers. Public benchmark profiles are the first inputs; live default behavior changes only after selection and client integration. The local pipeline works without provider credentials.

Send only the approved interest phrases/context, proposed meanings, and bounded source-backed candidates needed for the selected stage. Preserve the existing boundary around raw browsing titles, URLs, and browser evidence. External processing must be described in the existing recommendation settings when enabled.

For the initial reranking challenger, send at most 30 candidates and at most 20,000 characters of source-backed input, with deterministic truncation recorded in the manifest. Require a permutation of the supplied IDs. Unknown, duplicate, omitted, or malformed IDs invalidate the external ordering. Local eligibility, known exclusions, overlap quotas, and source identities remain authoritative after reranking.

Allow one provider attempt with a maximum 20-second stage deadline. Shorten it to fit the remaining end-to-end request budget, reserving time to return within the client's current 30-second timeout. Provider timeout, refusal, invalid output, or unavailable configuration yields the local result and an explicit fallback status. Do not silently spend additional calls retrying. An ambiguous resolver result stays ambiguous on provider failure; fallback cannot force a meaning.

Record exact provider/model version, prompt digest, latency, usage, and price assumptions for benchmark runs. External models may help inspect textual consistency but may not supply a person's curiosity or familiarity labels.

### API, client, and compatibility

Expose the application boundary through POST /api/recommend/v2, keeping the existing broad, specific, and Focus routes available until a reviewed rollout. Its strict request contract is:

| Field | Meaning and bounds |
|---|---|
| interests | 1–40 records containing a phrase of 1–120 characters and an optional selected concept ID |
| inventory_version | Required when submitting selected concept IDs; must match the active inventory |
| result_kind | broad or specific |
| mode / focus_index | global or path; focus is an index into interests, required for path and null for global |
| goal | connection, discovery, depth, or variety; default discovery |
| limit | Integer in [1,100], default 10 |
| distance/diversity controls | Existing bounded radius, expansion, overlap, diversity, maximum overlap share, and randomness controls |
| expansion_level | Integer in [0,8], default 0; retain the existing explicit expansion increment |
| feedback / exposures | Existing independently validated curiosity/known/difficulty ratings and area exposure counts, default empty |
| seed | Nonnegative integer up to the current API limit, default 42 |

Reject unknown fields, invalid IDs, duplicate input identities, control characters, and nonfinite or incorrectly typed controls. A client cannot supply authoritative concept descriptions or source claims.

The response carries schema version 2, algorithm/inventory/model identities, resolution states, source-backed meaning choices when needed, unique-ID recommendations, and local/external execution status. A valid request returns status ok or clarification_needed with HTTP 200; clarification_needed contains no recommendation list. Invalid input returns 422, stale inventory choices 409, unavailable required local components 503, and bounded-resource rejection 429. Recommendation records include canonical identity, label, description, sources, available graph provenance, and the distances/score components needed to explain the result. Similarity scores are not probabilities; unknown reading levels remain unknown. Keep detailed benchmark timing and costs in experiment artifacts rather than cluttering normal recommendation cards.

Apply existing authentication-before-parsing, CORS, body-size, rate, readiness, concurrency, and sanitized-error behavior to the new route. Cap its body at 1 MiB to support bounded feedback, as the existing specific route does. Bound local inference and external calls separately; release the local compute slot before waiting on a provider. No request content, provider credentials, or persistent personal profile enters server logs or public caches.

Minimal client integration adds the goal control and meaning-choice interaction through the existing interest/recommendation flow. Choosing a meaning is explicit; receiving a recommendation never saves an interest. Preserve generation checks and discard stale responses after changes to interests, endpoint, settings, or inventory.

Keep existing title-based saved interests and feedback readable. Store new canonical associations alongside legacy values; do not rewrite or delete old records automatically. Ambiguous legacy values require a choice. Existing graph QID feedback can map directly when the identity remains valid; unverifiable mappings remain local and visible instead of being guessed.

The existing map and Focus contract retain their pinned catalog, model, 768-dimensional vectors, hashes, and endpoint. Recommendation model experiments use separate identities/caches. A v2 recommendation without a corresponding map node remains available as a card; it does not receive a fabricated position.

### Automated metrics and repeated improvement

No human trial is required for the default implementation or comparison loop. Use the four frozen scorecards in the evaluation design: ConnectionScore@10, DiscoveryScore@10, DepthScore@10, and RelevantDiversity@10. Keep a separate champion per goal, evaluating every system on all tracks and reporting serving latency/cost Pareto trade-offs.

Shared deterministic gates enforce source/identity validity, explicit known exclusions, duplicate identities, verified senses, and request constraints. An independently configured method-blind judge grades C/N/E/A from identical source-backed text. Freeze evaluator model, prompt, rubric, and embedding identities. Cache grades by profile/concept/content/evaluator version. Missing grades make a metric unavailable rather than becoming fabricated dislike.

Required grades use 0–3 scales normalized to [0,1], with connectedness below 2/3 rejected. Unknown accessibility is explicitly neutral 0.5 when background is unavailable. Requested slots form the denominator; missing slots contribute zero. Variety is calculated on passing concepts only. These proxies do not assert observed curiosity or actual personal familiarity.

Those thresholds and formulas define the original rubric-v0 reference. Separately version the pilot-informed challenger treatments in the evaluation design: more concrete E anchors and presentation, a C >= 1/3 treatment requiring an explicit defensible source-backed bridge, concept-scoped familiarity, and credible entry points for challenging material. Compare each treatment independently; do not silently relax the baseline gate, fit weights to the pooled personal sample, or declare a champion from those ratings. Present a specific learning opportunity within familiar fields rather than assuming familiarity excludes an entire field. Generated explanations retain source concept IDs, and changed presentation invalidates content-specific grades.

Check order/format sensitivity, repeated-judge stability, and second-judge agreement on a recorded audit subset. Publish structural diagnostics if no semantic judge is configured. Keep evaluator calls distinct from ranking calls and record their cost separately from serving cost.

Use public ordinary/niche/mixed profiles, ambiguity with and without context, verified intended senses, and known exclusions. Label synthetic persona/background assumptions as fixtures. The 17 audited cases are regression/development data. Split related profile families together into development and sealed held-out batches.

Tune candidate families separately for each scorecard on development cases. Initial local cycles allow five rounds, twenty new configurations per round, and patience of two rounds without a gain of at least 0.01 on any scorecard. Bound external calls by a configured spending/call budget. Change one stage at a time and log attempted configurations and failures.

Freeze ranking weights, prompts, aliases, inventory expansion, and thresholds before nominating finalists. Evaluate the sealed held-out split once per cycle; do not optimize repeatedly against final results. Once those results inform later tuning, move them to history/development and reserve a new final batch. Changing judge/rubric/model/inventory versions creates a new benchmark requiring champion reevaluation.

Persist variant manifests, source/input/grade fingerprints, raw outputs, timing, cross-metric scoreboards, per-goal champions, and the Pareto frontier. Report paired per-profile gains and bootstrap uncertainty over held-out families; these quantify benchmark uncertainty, not user satisfaction. Select an operational champion only with metric improvement, passing integrity gates, acceptable judge/sensitivity checks, and a reviewed resource trade-off. Inconclusive results retain the baseline; cycles do not automatically deploy.

### Initial rubric check and optional human validation

The user authorized a small initial check of 20–30 suggestions across 3–5 personally relevant interest profiles, estimated at 15–30 minutes. That check is complete: a blinded, pooled packet with sourced descriptions was rated on four independent 0–3 dimensions, connectedness, unfamiliarity, curiosity, and accessibility. Sampling spanned candidate methods and omitted their identities. Personal responses and analysis remain in ignored local storage. The check informed evaluator/presentation challenger treatments; it did not establish a statistically best recommender or measure agreement with an independently configured automated judge.

Collect intended meanings before generating the personal packet. Use examples only when the user selects that option. Keep personal profiles/ratings outside public artifacts. Bind each case to its interest profile, concept/source record, content digest, and packet version. Unrated/skipped cases remain unknown. A sparse pool cannot be filled with invented topics.

A single pooled rating is reused across methods only for identical participant/profile/concept/content. Ordinary recommendation requests need no rating form, and subsequent optimization rounds require no repeated participant rating. Later optional spot checks can target changed champions and failures.

Evaluate the pooled alignment pilot through item-level ratings, missing/unknown counts, and concrete rubric disagreements. Five pooled items per profile cannot establish top-ten scores or algorithm champions. Record first-rating context so later learning is not mistaken for unchanged familiarity. The form starts blank, allows “can't judge” and skipping, and sends responses only through the participant's explicit action.

For separately collected complete recommendation lists, human QualifiedDiscovery@10 counts distinct items scoring at least 2 on all four human dimensions and passing integrity checks, divided by ten requested slots. Keep it separate from automated DiscoveryScore; LLM grades cannot manufacture actual curiosity/familiarity. A broader user-benefit study is a separate effort.

## Testing Decisions

Test externally observable behavior through the recommendation boundary and real authenticated API calls. Use injected deterministic models/vectors and provider responses for exact failure cases; use cached real embeddings for separately identified integration probes. Existing geometry, API validation, graph provenance, and independent-feedback tests are the prior art.

Acceptance requires:

1. Go/Go (game) is deduplicated by reviewed identity; culinary and metabolic Fermentation remain consistently distinguishable across presentation kinds.
2. Explicit Python/Java/Mercury senses resolve correctly; bare ambiguous inputs expose uncertainty; stale or forged choices fail without selecting another meaning.
3. An eligible concept outside the eight routed areas remains retrievable in the global arm; increasing graph depth is not presented as expanding this already-reached snapshot.
4. Known exclusions apply across aliases and source paths. Global/path eligibility, actual-result overlap quotas, valid goal choices, seed reproducibility, and exposure reservations survive retrieval and external reranking.
5. Invalid external output or a 20-second timeout gives the recorded local fallback; unresolved ambiguity stays unresolved. Provider tests make no billable calls.
6. Four scorecards use requested-slot denominators, distinct IDs, correct profile/content/evaluator versions, and complete required grade coverage. Tests cover per-metric champions, shared gates, bounded-cycle stopping, grade-cache invalidation, and no held-out tuning. Missing grades cannot produce a winner.
7. Existing API and Focus/map contract tests pass. New-route authentication, body limits, sanitized errors, provider/local concurrency, and public-only caches are exercised through requests.
8. When client integration is implemented, JavaScript state/request tests and focused browser checks verify meaning choice, goal settings, explicit saving, migration, and stale-response handling in side panel and Dashboard.

Every report distinguishes structural gains, proxy gains, and any optional human evidence. A metric-specific champion is best under its named scorecard/benchmark version; numerical tests do not establish universally best interestingness.

## Out of Scope

Map redesign or repacking its vectors; automatic mastery or prerequisite inference; opposing-viewpoint claims; collaborative filtering without interaction data; uploading raw browsing history; accounts or persistent server profiles; wholesale catalog replacement; unbounded live topic generation; production deployment as a side effect of a benchmark run.

## Further Notes

This spec adopts the user's confirmed direction and synthesizes the existing research without another interview. The algorithm variants, external limits, and defaults above are initial implementation choices subject to the stated development/evaluation procedure, not claims of optimality.

- [Domain glossary](../../../CONTEXT.md)
- [Backend audit and reproducible probes](../../recommendation-audit.md)
- [Primary-source research](../../recommendation-research.md)
- [Evaluation rubric and study proposal](../../recommendation-evaluation.md)
- [Saved public results and fingerprints](../../../experiments/recommendation-audit/results.json)

The next artifact is the implementation plan, after review of this written spec. Keep the benchmark, local corrections, optional challengers, and client rollout as ordered work with explicit acceptance checks.
