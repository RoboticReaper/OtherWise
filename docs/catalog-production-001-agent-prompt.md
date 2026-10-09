# OtherWise catalog production 001 — research instructions

Workspace: `/Users/baorenliu/Documents/Programming/Python/ProductSpace`.
Production directory: `data/catalog-candidates/catalog-production-001/`.
Read `CONTEXT.md`, the catalog sections of `docs/superpowers/specs/2026-10-07-recommendation-system-design.md`, the production plan, `production-policy.json` and your assigned `eligible-identities.json`.

The authorized milestone is 5,000 first cards, with a 200-card validation checkpoint followed by 24 further batches. Work only on the particular batch and domain directory assigned by the coordinator. Preserve existing cards. Do not make per-concept AI API calls, import operational data, modify another researcher's files, or create a human study.

## Selection

Use your frozen eligible canonical IDs. They have no prior researched card. Verify the intended source subject rather than assuming a Wikidata label or original description proves the explanation. Prefer specific ideas and meaningful applications, with balanced domain coverage and all four scopes. Include named subjects with a distinct learning takeaway; proper names on methods/theorems do not alone make them named subjects.

Inspect a primary, official or authoritative educational passage for each proposed learning takeaway. Existing sources may support several concepts when each is covered by an inspected passage and source-wide quotation/summary limits are observed. Preserve each inspection's source title, URL, locator, inspection method and available revision/acquisition metadata. Search snippets and identity links alone cannot substantiate a discovery card.

Write `proposals.json`: `schema_version: 1`, `assignment`, `baseline_index_sha256`, `proposals`, `issues`, `sources_inspected`. Each proposal has `id`, `label`, `aliases`, `primary_domain`, `primary_subfield`, `entity_kind`, `scope`, `learning_takeaway`, `identity_reason`, `discovery_evidence` (URL, locator, support note and inspection mode), `proposed_parent` (or null), and `limits`. Select only assigned eligible IDs. Record ambiguity rather than conflating meanings; a different formulation of the same subject is not a new identity. Modest alternatives are allowed within 300 proposals for the whole batch.

Stop selection for coordinator reservations. Draft only `approved-selection.json` IDs. For an unresolved identity/source, use a researched alternative from the eligible list or report a shortfall; never invent evidence to fill the count.

## Drafting after reservations

Use the established candidate schema: top-level `schema_version: 1`, `batch`, `sources`, `concepts`, `issues`, `validation`. The shard ID is `research-batch-NNN-<assignment>`. Batch metadata records the baseline and global selection hashes, revision, target, language, acquisition limits and ownership/subfields.

Each concept has `id`, `label`, `aliases`, `entity_kind`, `scope`, `domains`, `learning_takeaway`, `card`, `original_description`, `identity_urls`, `evidence`, `relations`, `card_version: 1`, and `imported_records`. Read the exact original description and imported records from the frozen baseline. No previous card is revised. The primary domain goes first.

**Every newly written card body is at most 25 whitespace-separated words.** Titles and sources are outside this limit. Explain its meaning and one concrete mechanism, consequence, distinction or example. Retain necessary assumptions or qualifications. Choose fewer claims rather than dropping conditions. Broad fields use everyday language; finer ideas may use useful domain terms. Avoid generic category labels, inflated promises and context-free trivia. The source supplies further learning.

Each `evidence` item has `source_id`, `locator`, `note`. Each source has a unique `id`, `title`, `url`, `locator`, revision (null if unavailable), valid ISO `retrieved_at`/local inspection metadata with an honest time basis, actual `inspection_mode`, and the retrieved source's word limit. Keep a separate `sources-inspected.json` and `source-word-budgets.json` accounting for all derived prose, including card, takeaway and substantive notes. A source's summary limit applies across all cards in the shard and across shared sources in the combined batch; companion representations of one source share a budget.

Relations have `target_id`, `type` (`broader_topic`, `facet_of`, `application_of`, `related_to`), `source_ids`, `assertion` (`source_asserted` or `editorial`), and `note`. Targets must exist in the pinned inventory/reservations and differ from the source. Evidence must support the actual relation. Source context, an ingredient, a use setting or a comparison does not automatically establish an application parent. Seek supported parent/application links for fine-scope cards, record gaps instead of inventing them.

Write valid checkpoints, complete `author-review.json` keyed by ID, and cited `research-notes.md`. Author-check every substantive card claim, intended meaning, distinct learning takeaway, scope-appropriate wording and attached relation against inspected passages. Preserve actual failures and alternatives. Bound URL attempts to two, then at most three alternative sources before recording an unresolved issue.

## Independent acceptance

The coordinator freezes candidate bytes and then chooses 20 deterministic random and 20 disjoint risk cards. Reviewers who did not author the sampled cards inspect substantive evidence, clarity under the short limit and every attached relation. They retain initial findings separately from repair rechecks. Recurring/source-shared problems expand the audit. Structural checks do not certify unsampled facts or human interestingness.

Accepted count means distinct previously undescribed identities with complete cards that passed the applicable acceptance gate. Report named/scope/graph shortfalls, access failures and unknown usage honestly. Return concise summaries and paths; do not print the entire catalog or claim comprehensive coverage.
