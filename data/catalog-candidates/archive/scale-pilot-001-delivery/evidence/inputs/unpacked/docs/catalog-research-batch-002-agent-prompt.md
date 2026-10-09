# OtherWise catalog research — validation batch 002

Work in `/Users/baorenliu/Documents/Programming/Python/ProductSpace`.

Research and return **200 source-supported discovery cards** for the next catalog validation batch. This run should test discovery of additional specific learning subjects, improve descriptions and graph justifications, and detect duplicate meanings. You own research, identity reconciliation, writing, and validation. Local scripts may help search and validate files; the work is an agent-led research task.

## 1. Establish the baseline

Before selecting candidates, read workspace instructions, `CONTEXT.md`, and these sections of `docs/superpowers/specs/2026-10-07-recommendation-system-design.md`: **Concept identity and inventory**, **Catalog scope and discovery cards**, and **First catalog-build milestone**.

Read `docs/catalog-research-batch-001-source-review.md` and inspect `data/catalog-candidates/research-batch-001.json`. The first batch passed structural checks; 32 sampled cards had no substantive source-support findings. However, 177 of its 200 identities already existed, and 106 relations had generic explanations. These are the gaps this batch should address. The source sample does not certify every first-batch fact.

Use `data/topics.json`, `data/discovery_graph.json`, `data/recommendation-identities.json`, and all existing candidate batches as the identity baseline. Consult `recommendation_lab/inventory.py` and `recommendation_lab/README.md` for current identity mappings. Record input fingerprints and generation settings. Keep previous artifacts, operational catalogs, identity registries, embeddings, and recommender behavior intact; return proposed changes in this candidate artifact.

OtherWise aims to broaden what people come to care about. This is a general catalog task across fields. Use public subject material for selection; private preference ratings and held-out recommendation judgments are outside the selection inputs. Catalog quality alone does not demonstrate curiosity or sustained interest expansion.

## 2. Select and reconcile the learning subjects

Record a selection manifest before drafting, then track accepted, rejected, and unresolved candidates and subsequent changes.

For a complete 200-card batch, target:

- **At least 160 new learning identities** absent from both the current inventory and previous candidate batches after duplicate review.
- **At least 120 of those new identities** at `idea` or `facet_or_application` scope.
- **20–40 existing identities** as validation controls, including broad subjects, ambiguous meanings, and some first-batch concepts whose graph explanations need improvement.
- Representation of all **23 first-batch seed domains** and all four scopes. New identities should span at least **15 primary domains**; assign one primary domain per manifest entry so cross-domain tagging cannot inflate this count.
- At least **20 named subjects** with distinct learning takeaways, and **three ambiguous-name groups** containing multiple verified meanings. At least two groups should differ from those exercised in batch 001.

These targets deliberately stress extraction; they are not universal catalog quotas. Return a documented shortfall if supported candidates cannot satisfy them. Acceptance depends on evidence, not filling counts.

Discover ideas through inspected article sections, textbooks, technical documentation, research, museum material, and other subject references. Seek identifiable mechanisms, methods, phenomena, strategies, distinctions, or documented applications. Include people, places, organizations, products, works, games, and events when their sources establish something concrete to learn. Existing importer title deduplication, entity exclusions, and domain caps are sampling policies, not admission requirements.

For each candidate, complete these decisions before drafting:

1. **Identity:** search the baseline using names, aliases, source IDs, and descriptions; investigate likely overlaps by meaning. Reuse a verified canonical ID. Verify a new external identity against the exact subject and sense, or assign a stable local ID if no exact external identity is established. A missing QID does not disqualify an otherwise supported concept.
2. **Distinctness:** identify what this subject teaches beyond its broader topic or nearest existing entry. Paraphrases, alternate questions, and renamings retain the same identity. A separate facet needs a separately supported learning takeaway. Broad and fine subjects can coexist when their takeaways differ.
3. **Scope:** choose `broad_field`, `topic`, `idea`, or `facet_or_application` by the breadth of the takeaway. Scope is neither difficulty nor a mandatory four-level tree. Domain memberships share one identity.
4. **Manifest evidence:** record `id`, `primary_domain`, `inventory_status` (`new` or `existing`), discovery source IDs/locators, likely matches considered, and the duplicate-review decision. Novelty here means absence from the baseline, not unfamiliarity to every person or a newly discovered scientific result.

Preserve registered IDs, original descriptions, and imported source records. Local IDs survive label edits and later batches; a new batch prefix is not grounds to replace an existing local identity. Potential duplicates with unresolved equivalence stay in `issues` and do not count toward the new-identity target.

Also review the three deferred first-batch overlaps: `local:authored:000028` / `Q215712` (Urban heat islands), `local:authored:000654` / `Q36288` (Silk Road exchanges / Silk Road), and `local:authored:000049` / `Q431498` (Confirmation bias). Record proposed `equivalent`, `distinct`, or `unresolved` decisions with supporting evidence in `batch.prior_equivalence_reviews`. Apply no registry migration in this run.

## 3. Research and write the cards

Each accepted identity gets one **30–50-word English card**, counted by whitespace-separated tokens, excluding its title and source links. Explain the intended meaning and one concrete learning opportunity: a mechanism, example, surprising consequence, useful distinction, or documented case.

Make the explanation itself informative. Vary the structure naturally instead of repeatedly ending with a generic promise that exploring or comparing the topic will reveal something. A broad subject can introduce a specific example while retaining its broad identity; a fine subject should explain its particular takeaway. For named subjects, go beyond a biographical or institutional label.

Broad subjects use everyday language. More detailed ideas may use necessary domain vocabulary; briefly explain a central term when otherwise the card's meaning would be hidden. Accuracy takes priority over artificially simplifying a deep concept. Keep assumptions and qualifications needed for the claim. Sources supply the next learning step, so produce one short card per identity.

For every substantive claim, cite a reference actually inspected, with a supporting section/passage locator and a note identifying the claim it supports. Prefer primary, official, or authoritative educational references where available. Wikipedia can support appropriate explanations; retain its section and revision when retrievable. Identity pages establish identity, not automatically the explanation's facts. Distinguish a study's finding, a review's report, a disputed argument, and an editorial learning suggestion.

Use `null` for unavailable revision metadata. Bound repeated access attempts to two per URL before trying alternatives. If accessible evidence remains insufficient, defer the candidate and record the limitation. Search snippets and failed fetches cannot supply uninspected final evidence. A fetch failure is an access limitation rather than proof of a broken source.

## 4. Build defensible relationships

Use `broader_topic`, `facet_of`, `application_of`, or `related_to`. Each target must resolve to a batch entry, an existing canonical identity, or a verified external identity. Seek a defensible broader or application connection for each new fine subject; record missing connections rather than inventing them.

Every relation needs a **topic-specific rationale** stating how the two subjects connect. Explain membership, mechanism, application, or the particular comparison that makes a navigation bridge useful. Generic phrases such as “editorial connection for exploration” are insufficient.

- `source_asserted`: cite the inspected source passage that supports this actual relationship.
- `editorial`: explain your reasoning. Cite evidence for underlying factual premises where applicable, while making the inferred learning connection explicit. A citation to a premise does not turn the inferred bridge into a source assertion.

Use the correct relation type; an analogy or useful comparison belongs in `related_to`, while a supported parent relationship can use the structural types. Relatedness alone establishes neither equivalence nor prerequisites. For repeated validation-control identities, improve justified relations in the new artifact and record changes from batch 001 in the manifest.

## 5. Return one structured candidate file

Write `data/catalog-candidates/research-batch-002.json`. Inspect the destination first; resume a matching partial run or use the next unused batch number rather than overwrite unrelated work.

Retain the first batch's top-level contract: `schema_version: 1`, `batch`, `sources`, `concepts`, `issues`, and `validation`. Put new selection, duplicate-review, and prior-equivalence metadata inside `batch`; put audit results inside `validation`.

Each concept retains these fields: `id`, `label`, `aliases`, `entity_kind` (`idea` or `named_subject`), `scope`, `domains`, `learning_takeaway`, `card`, `original_description`, `identity_urls`, `evidence`, `relations`, `card_version`, and `imported_records`. Preserve original imported text separately; use `null` for an absent original description. Start a first discovery card at version 1; for a revised prior candidate card, increment its version and record the previous version.

Shared source records contain `id`, `title`, `url`, supporting locator, retrieval date, and revision when available. Evidence entries contain `source_id`, `locator`, and claim-support `note`. Relations contain `target_id`, `type`, `source_ids`, `assertion`, and `note`. Keep rejected and unresolved candidates, reasons, and relevant reference IDs visible in `issues`.

## 6. Validate and report honestly

Review every accepted card against its evidence and distinct learning takeaway. Validate strict JSON, unique IDs, preserved source records, reference/target resolution, allowed values, word counts, meaning separation, and manifest totals. Scope and wording checks require reading, not just counting.

If subagents are available, divide research by non-overlapping subject responsibilities and reconcile identities centrally. Use a checker who did not write the audited cards. Freeze a **40-card audit sample** before its source checking: 20 new cards sampled with a recorded reproducible seed, plus 20 non-overlapping risk-selected cards covering ambiguity, named subjects, assumptions, finer applications, and proposed relationships. Read the actual card and relation references. Keep the original sample and findings visible after corrections; replace neither failed cards nor inconvenient findings silently. For a partial run, record the available sample size and any audit shortfall. If an independent checker is unavailable, perform and label a self-review, explicitly reporting that independence was not achieved.

Record reviewed IDs, inspected references, findings, corrections, unresolved claims, reviewer roles, and audit scope. Resolve substantive problems or remove the affected candidate to `issues` before accepting it. A sampled audit certifies only the sampled claims; numerical validation does not certify factual accuracy.

Report accepted/rejected/unresolved counts; new/existing identity counts; new fine-subject counts; coverage by scope and primary domain; ambiguity and equivalence decisions; source-asserted/editorial relation counts; generic-rationale count; fine subjects missing a defensible parent/application link; audit findings before and after correction; elapsed time; and platform-reported usage when available. Label unavailable usage explicitly. Separate `validation.passed` for checked admission requirements from `validation.quality_targets_met` for the pilot's selection and audit targets, listing each unmet target.

Stop at this validation checkpoint and return the file link with a concise outcome and remaining gaps. Keep any partial artifact valid and its status explicit. This run supplies evidence for deciding the next expansion milestone; it does not claim catalog completeness or launch a participant study.
