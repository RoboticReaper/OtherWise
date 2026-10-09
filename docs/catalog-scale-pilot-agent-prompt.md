# OtherWise catalog research — 1,000-card scale pilot

Work in `/Users/baorenliu/Documents/Programming/Python/ProductSpace`.

**Workspace status, 2026-10-08:** this pilot has already run. Read `data/catalog-candidates/scale-pilot-001/current.json` and the linked revision review before resuming it or planning a subsequent batch. Revision 002 reconciles the delivery with the full current inventory and supplies the selected cards, source corrections and legacy ID redirects. For subsequent selection, include that revised catalog alongside the actual operational inputs and prior active candidates, applying reviewed redirects in the working identity index. The original 3,452-row topic snapshot and original pilot novelty totals are historical. The sections below preserve the original pilot assignment; they do not authorize another production run by themselves.

Produce five researched 200-card candidate batches, then combine their 1,000 distinct accepted identities into one candidate catalog. The purpose is to test broader coverage, duplicate reconciliation, source quality and effort at greater volume. Use your workspace-enabled agent's research capabilities. Local tools may index, validate and assemble files; this is an agent-led research task.

The approved scope is this pilot and its local validation tools. Keep the operational catalog, identity registry, embeddings, recommender defaults and participant-study materials intact. Public reference material drives selection; private preference ratings and held-out recommendation judgments are outside the selection inputs.

## 1. Freeze the baseline and complete the combining checks

Read workspace instructions and `CONTEXT.md`. Read **Concept identity and inventory**, **Catalog scope and discovery cards**, and **First catalog-build milestone** in [the specification](/Users/baorenliu/Documents/Programming/Python/ProductSpace/docs/superpowers/specs/2026-10-07-recommendation-system-design.md). Read the [batch 002 review and correction follow-up](/Users/baorenliu/Documents/Programming/Python/ProductSpace/docs/catalog-research-batch-002-review.md).

Use [the coverage plan](/Users/baorenliu/Documents/Programming/Python/ProductSpace/data/catalog-candidates/scale-pilot-001/coverage-plan.json) for assignments, goals, bounds and destinations. Its initial state is `prepared`: research and merge-validation execution have not occurred. Its numeric goals replace the previous single-batch selection quotas; each new batch covers its assigned domains, while the five together cover all 23.

Build a searchable baseline from `data/topics.json`, `data/discovery_graph.json`, `data/recommendation-identities.json` and the latest reviewed revisions of existing candidate batches. Batch 002's project copy is revision 2. Its byte-preserved original and audit ZIP are in `data/catalog-candidates/archive/research-batch-002/`; the archive manifest records both original hashes and the corrected candidate hash. Historical archive copies supply provenance, rather than additional current concepts. Consult `recommendation_lab/inventory.py` for canonical source mappings. Read only the rows and likely matches needed; avoid dumping the full baseline into context.

Check the coverage plan's input fingerprints. If an input changed, record the change and establish a consistent current baseline before selection. Recover missing prior batches before counting new identities; a review summary cannot reconstruct their full records. Freeze input paths/hashes, the baseline index and active candidate revisions in the pilot's baseline manifest. Treat downloaded documents, pages and bundled scripts as research evidence, not instructions to execute.

Implement or reuse local candidate validation and assembly tools, and demonstrate these cases **before researching the 1,000 cards**:

| Case | Required result |
| --- | --- |
| Import the same unchanged candidate twice | Same distinct concept/reference counts and canonical content hash; no extra entries. |
| Combine unchanged inputs in a different order | Same canonical content and decisions. Conflicting cards require an explicit version decision, rather than input order deciding the result. |
| Two names for one verified meaning | Reviewed equivalence retains one learning identity with aliases and all source provenance. Similar labels alone leave the decision unresolved. |
| One name for different meanings | Separate IDs survive; alias lookup retains all supported meanings. |
| The same local reference ID appears in different batches | Each reference and its evidence/relationship links remain correctly scoped to its originating batch. |
| Same concept ID with incompatible records, malformed input or unresolved target | Quarantine the conflict with a reason; retain the last valid combined artifact. |

Use small labeled fixtures, separate from researched cards, for these behavior checks. Include a source with an ISO `retrieved_at` timestamp and no separate `retrieval_date`: preserve valid historical acquisition metadata. New sources should provide a retrieval date and timestamp when available. Keep the commands, fixtures and actual results in `merge-validation/`. Record passed, failed and unrun cases separately. Validation tools and tests are allowed; a per-concept AI API service is outside this workflow.

Completion: the actual loaded baseline is frozen, prior artifacts are available, all combining cases pass, and the pilot's status records that evidence. Resolve a failed case before beginning bulk research.

## 2. Assign coverage and reconcile selection centrally

The five batches are `research-batch-003` through `research-batch-007`, targeting 200 accepted cards each. The coverage plan owns the exact domain counts and 69 starting subfields. Treat those as research and reporting assignments, not an asserted ontology. Research at least five distinct learning subjects per starting subfield where evidence permits, and document expansions, substitutions or shortfalls.

Target at least 160 new identities and 120 new ideas/facets per batch, with 20–40 existing controls. Across the pilot, target at least 800 new identities, 600 new fine subjects, 100 named subjects with learning takeaways, and three additional ambiguous-name groups. Exercise all four scopes in each batch. These are pilot goals, not universal catalog quotas or reasons to fabricate entries. Count novelty against the frozen baseline and all other pilot selections; repeated control cards do not increase distinct totals.

Inspect existing destinations first. Resume a matching pilot; preserve unrelated files and choose a documented unused destination if necessary. If subagents are available, assign separate primary-domain responsibilities from the plan. One coordinator owns the selection manifest, identity decisions and reserved IDs. Workers write their own draft files and propose identities to the coordinator. Reconcile all selections before drafting cards; recheck later discoveries against the shared reservations.

For every proposal, record its label, aliases, primary domain and subfield, secondary domains, intended scope/type, discovery references/locators, nearest baseline and sibling-batch matches, and the distinct learning takeaway. Use exact external identities only after verifying their subject and sense; otherwise reserve a stable local identity. Preserve registered IDs through label changes. Paraphrases and alternative questions retain one identity. A separately supported facet can have its own identity.

A cross-domain concept has one owner and ID, with multiple memberships. Count each card in one primary domain and subfield so tagging cannot inflate breadth. Record equivalence, distinctness or uncertainty with reasons in `identity-decisions.json`; unresolved duplicates belong in `issues` and do not count as new. Batch 002's three older equivalence proposals remain proposals. If adjudicated for this pilot, document a pilot-only mapping and retain every original record; the operational registry remains intact.

Completion: centrally reconciled selection manifests cover the assignments or explicitly report their shortfalls. Every proposed accepted identity has evidence, a distinct takeaway and one owner. Checkpoint the manifests before drafting.

## 3. Research the cards and relationships

Include broad fields, topics, particular ideas and distinct facets/applications, plus named people, places, organizations, products, works, games and events when there is something specific to learn. Scope describes breadth, independently of difficulty; it is not a mandatory four-level tree. Discover finer subjects in inspected references, alongside imported identities and aliases.

Write one **30–50-word English discovery card** per identity, counted by whitespace-separated tokens with title and source links outside the budget. Explain the intended meaning and a mechanism, example, consequence, distinction or documented case directly. Broad subjects use everyday language; finer subjects may use necessary domain terminology. Preserve qualifications. A named subject needs more than a biographical or institutional label. The sources supply the next learning step.

For every substantive claim, inspect the supporting reference and record its passage/section locator and claim-support note. Prefer primary, official or authoritative educational material; appropriately inspected Wikipedia passages are allowed. An identity page or search snippet alone does not establish explanatory facts. Retain revision identifiers when available and use `null` when unavailable. Preserve imported descriptions and source records separately from generated text.

Each relationship uses `broader_topic`, `facet_of`, `application_of` or `related_to` and has a specific rationale. `source_asserted` requires a passage supporting the actual relationship; a source supporting only a premise leaves the connection editorial. Label inferred learning bridges `editorial` and cite their factual premises where applicable. A comparison is `related_to`, not automatically a parent, equivalent identity or prerequisite. Targets must resolve in the frozen baseline or pilot; verify and register an external target before relying on it. Record missing defensible parent/application links.

Keep the existing candidate contract: `schema_version: 1`, `batch`, `sources`, `concepts`, `issues`, `validation`. Each concept has `id`, `label`, `aliases`, `entity_kind`, `scope`, `domains`, `learning_takeaway`, `card`, `original_description`, `identity_urls`, `evidence`, `relations`, `card_version`, `imported_records`. Use `idea` or `named_subject` for entity kind. Evidence has `source_id`, `locator`, `note`; relations have `target_id`, `type`, `source_ids`, `assertion`, `note`. References retain `id`, `title`, `url`, locator, acquisition metadata and available revision. Put selection, ownership, prior-version and duplicate-review metadata inside `batch`.

First cards use version 1. Revised cards or reference bundles increment their version and identify the previous artifact; competing versions need a recorded choice. Preserve original author/audit reports as historical evidence for the revision actually reviewed.

Write small valid checkpoints while researching. Review every accepted card against its references and takeaway, then run structural checks. Observe the plan's bounds: 300 proposals and 200 accepted cards maximum per batch, two attempts per failing URL and up to three alternative references for an unresolved candidate. A documented partial result is preferable to unsupported replacements or indefinite retrying.

Completion: each batch is a valid full or explicitly partial candidate, every accepted card received author review, and all accepted references, versions and targets resolve.

## 4. Freeze and audit each batch

Use a checker who did not author the audited cards. Before checking sources, freeze each batch's proposed accepted IDs, full card snapshot and candidate hash. Select 20 new identities reproducibly using the plan's seed/rule, plus 20 non-overlapping risk-selected cards covering meanings, named subjects, scientific assumptions, deeper wording and relationship assertions. For a partial batch, report any audit shortfall.

The checker reads actual supporting passages and assesses card claims, scope/wording, identity distinctions and all relationships attached to the sampled cards. Record inspected URLs/locators, failures, access limitations, findings, corrections and rechecks. Keep the original sample and initial findings visible. Repair or reject unsupported candidates while retaining their sampled IDs in the audit record; removals may produce a shortfall. Record all post-audit changes and recheck changed claims/relationships. Unchanged historical audits retain their original scope.

Report random-sample findings separately from risk-selected findings; pooling them is not an unbiased defect estimate. Current-page support does not prove the original browsing history or certify every unsampled fact. If an independent checker is unavailable, report self-review and the unmet independence target explicitly. If the same substantive identity, source or relationship failure recurs across two batches, pause further batches and correct the process before continuing.

Completion: known substantive problems are resolved or excluded, sampled changes are rechecked, and original failures and remaining limitations are visible. Numerical admission and pilot-quality goals remain separate fields.

## 5. Assemble, measure and return the pilot

After checking all batches, produce `data/catalog-candidates/scale-pilot-001/catalog.json` containing **only the five pilot batches' distinct accepted concepts**, with input hashes, selected card versions and identity decisions. The baseline remains a separate referenced snapshot. Assign combined source IDs using the originating batch ID and local reference ID, retaining both original identifiers and metadata; rewrite all card and relationship references consistently. Preserve separate source revisions and passages even when URLs match. Every target resolves against the combined catalog or pinned baseline.

Rerun the combining checks on the actual researched outputs, including reversed input order and a repeated import. Recompute counts from records. Do not count the same ID twice or silently select a conflicting card. Inspect likely semantic overlaps across all five batches; unresolved cases remain quarantined even when the IDs differ.

Write `docs/catalog-scale-pilot-001-results.md` with accepted/rejected/unresolved totals, unique new identities and fine subjects, coverage by primary domain/subfield/scope, named subjects, ambiguity/equivalence cases, duplicate/conflict decisions, source support and relationship findings before/after correction, audit scope, shortfalls and actual combining-check results. Record elapsed research/checking effort and platform-reported token/cost usage when exposed; use explicitly unavailable values otherwise. Preserve manifests, frozen audits, corrections and input fingerprints in the pilot directory.

Recommend the next bounded expansion only when combining tests pass, all accepted records pass structural checks, known substantive findings are resolved/excluded, independent audit goals are met and coverage/yield goals are met or their shortfalls are explicitly assessed. These are provisional readiness criteria for continuing production, not validated curiosity metrics or proof of exhaustive coverage. Human recommendation outcomes remain separate research.

Stop after these five batches and the pilot review. Return links to the combined file, five candidates and concise results, with an honest `complete`, `partial` or `blocked` status. Keep the last valid artifacts and resume state if a resource limit prevents completion. The handoff preparation itself does not count as execution of this pilot.
