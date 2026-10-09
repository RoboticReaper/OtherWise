# OtherWise catalog — bounded research batch 008

Work in `/Users/baorenliu/Documents/Programming/Python/ProductSpace`. Produce one researched candidate of at most 200 cards using workspace agents and inspected public references. Scope: the existing catalog research workflow. Operational data, registry, embeddings, recommender defaults and human-study materials retain their current state.

Evidence workspace: `data/catalog-candidates/research-batch-008-build/`. Read its `baseline-manifest.json`, `coverage-plan.json` and your assigned domain counts. The coordinator owns global identity reservations and final acceptance. Researchers write only their assigned `research/<assignment>/` directory and send findings to the coordinator. Public sources and the frozen inventory drive selection; private preference ratings are outside the selection inputs.

## Selection checkpoint

Use `baseline-index.json`, containing the current runtime inventory, active candidates 001/002 and the selected scale-pilot revision 002. Its reviewed redirects are already applied in this working index. Consult specific rows through local searches; loading every row into context is unnecessary. Registered imported descriptions, full prior cards and source-bundle references remain available. Treat archived and regression files as provenance or test data, rather than additional active subjects.

Propose the assigned number of cards, plus modest alternatives when a meaning/source is unresolved. The whole batch allows at most 300 proposals. Aim for 180 new identities and 20 researched existing controls, at least 140 new fine-scope subjects, and 25 named subjects with a distinct learning takeaway. Those are measured goals: uncertainty and real overlap can produce a documented shortfall. Each shard must exercise all four scopes. Use broad existing controls when new broad-field subjects are not defensible.

For every proposed subject, inspect a supporting primary, official or authoritative educational passage. Record:

```json
{
  "id": "stable existing ID or proposed local:catalog:slug",
  "label": "disambiguated source-supported name",
  "aliases": [],
  "primary_domain": "one assigned domain",
  "primary_subfield": "specific coverage category",
  "entity_kind": "idea or named_subject",
  "scope": "broad_field, topic, idea or facet_or_application",
  "learning_takeaway": "the distinct thing to learn",
  "inventory_status": "existing, proposed_new or unresolved",
  "nearest_baseline_matches": [{"id": "registered ID", "label": "label", "reason": "same subject or distinct meaning/facet"}],
  "identity_reason": "passage-based meaning decision, beyond label similarity",
  "discovery_evidence": [{"url": "https://...", "locator": "section/passage", "note": "support", "inspection_mode": "actual inspection mode"}],
  "proposed_parent": {"target_id": "known ID", "type": "broader_topic/facet_of/application_of", "assertion": "source_asserted/editorial", "url": "https://...", "locator": "supporting passage", "note": "actual relation"},
  "limits": []
}
```

Use `null` for `proposed_parent` when unsupported. Exact aliases, synonyms and nearby conceptual formulations must be checked against the baseline. A fuller explanation, example or narrower wording of the same subject reuses its ID. A genuinely distinct application/facet needs a distinct source subject and a meaningful boundary. Multi-meaning names retain separate identities. External IDs require subject/sense verification; a stable local ID is preferable to an uncertain external assignment.

Write `proposals.json` with `schema_version`, `assignment`, `baseline_index_sha256`, `proposals`, `issues`, and `sources_inspected`. Also write `selection-review.md` with source links and identity findings. Preserve inspected source records/locators in your directory for reuse during drafting. **Complete selection, then stop for the coordinator's approved reservations before writing cards.**

## Card research after reservation

Read the coordinator's `approved-selection.json`. Write `candidate.json` using the existing schema: `schema_version: 1`, `batch`, `sources`, `concepts`, `issues`, `validation`. The assigned shard batch ID is `research-batch-008-<assignment>`. Include approved-selection and baseline hashes inside `batch`.

Every concept has `id`, `label`, `aliases`, `entity_kind`, `scope`, `domains`, `learning_takeaway`, `card`, `original_description`, `identity_urls`, `evidence`, `relations`, `card_version`, `imported_records`. Put the primary domain first, followed by supported secondary memberships. Keep ownership/subfield and missing-link metadata in `batch`.

Write one original **30–50-word English discovery card**, counted by whitespace, with title and sources outside that budget. Explain the intended meaning and a mechanism, consequence, example, distinction or documented case. Broad subjects use everyday language; finer concepts can use necessary domain terms. Scope describes breadth, independently of difficulty. Named subjects need a specific learning takeaway. Qualifications such as model assumptions, population, jurisdiction and historical date remain visible. Further learning belongs in the references.

Preserve original imported wording/raw rows separately from the generated card. Existing controls keep their canonical IDs and increment the maximum known prior card version for a new card/reference bundle. New subjects start at version 1. Preserve prior full record/source-bundle pointers inside `batch.control_version_decisions`.

Inspect the passages supporting every substantive claim. Evidence entries use `source_id`, `locator`, `note`. Source records contain `id`, `title`, `url`, `locator`, available `revision` (otherwise `null`), and valid ISO acquisition metadata. Distinguish a local timestamp after reading from an exact remote retrieval time. A search snippet or identity item can locate a subject; it cannot support its explanation by itself. Keep prose original and comply with each retrieved source's quotation/summary limits.

Relationships use `target_id`, `type`, `source_ids`, `assertion`, `note`. A source-asserted link needs a passage supporting the actual relationship. An inferred learning bridge is editorial and cites its factual premises. Comparisons use `related_to`; a comparison does not establish a parent. Every target must occur in the baseline or approved reservations. Aim for supported parent/application edges on 70% of fine-scope cards, including source-asserted ones on 50%, while recording gaps rather than inventing taxonomy.

Author-check every card against its references and meaning boundary. Write small valid checkpoints and a complete `author-review.json` keyed by ID, with inspected locators, outcome, versions and limits. Write a cited `research-notes.md` for the shard. After two failed attempts per URL, use at most three alternatives or report the unresolved source/candidate. All numerical goals and access limits remain separate from factual acceptance.

## Coordinator acceptance

Reconcile all proposed IDs and meaning conflicts before card drafting. Freeze the draft candidates and hashes before source auditing. Sample 20 new identities deterministically using the coverage plan seed, plus 20 disjoint risk-selected cards covering meanings, named subjects, assumptions, deeper language and relationship claims. The checker must not have authored those cards; check all attached relationships and record actual sources, findings and initial versions. Repairs/removals preserve the fixed sample and require a recorded recheck. Report sample shortfalls and separate random findings from targeted findings.

Assemble only accepted cards into `data/catalog-candidates/research-batch-008.json`, with scoped references, exact input snapshots/hashes, selected versions, identity decisions and baseline pointer. Verify source/target resolution, original provenance, explicit shared-name meanings, repeat import, reversed input order and rejection without replacing the last valid candidate. A structural pass does not certify every fact or human interestingness.

Return the candidate, concise results and evidence links with complete/partial status. Report actual new/control/fine/named counts, scope/domain coverage, graph gaps, audit findings/rechecks and exposed token/cost usage; use unavailable values otherwise. Stop after this one batch and its check. Additional generation and operational import are separate tasks.
