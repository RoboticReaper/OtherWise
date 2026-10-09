# OtherWise: complete the 200-card short-description validation batch

You have access to the OtherWise workspace at:
`/Users/baorenliu/Documents/Programming/Python/ProductSpace`.

Take responsibility for the unfinished research and writing: inspect reliable sources, verify concept meanings, write accurate short descriptions, check relationships, and return a complete catalog file with supporting evidence. Use your own browsing and workspace tools. Local scripts may help with assembly and validation; this is an agent research task, not a program making an AI API call for every concept.

The immediate deliverable is **200 cards: preserve 35 completed cards and finish the remaining 165**. Each body is **at most 25 words**. Return this checkpoint for review before the remaining 4,800 cards are commissioned. Finish the research and files in this task; do not stop at a proposal or wait for a coordinator to approve individual selections.

## 1. Read the inputs and preserve the existing catalog

Read `CONTEXT.md` and the catalog/identity sections of `docs/superpowers/specs/2026-10-07-recommendation-system-design.md`. Then inspect:

- `data/catalog-candidates/catalog-production-001/baseline-index.json`: frozen public inventory and prior researched cards.
- `data/catalog-candidates/catalog-production-001/baseline-manifest.json`: baseline fingerprint and protected legacy files.
- `data/catalog-candidates/catalog-production-001/batch-009/selection-manifest.json`: the 200 reserved identities, scope/domain assignments, and inspected source leads.
- `data/catalog-candidates/catalog-production-001/batch-009/external-handoff-manifest.json`: the exact 35 completed IDs and 165 unfinished IDs, with protected record hashes.
- `data/catalog-candidates/catalog-production-001/batch-009/completed-cards.json`: the completed concept records and supporting sources to carry forward unchanged.
- `data/catalog-candidates/catalog-production-001/batch-009/source-budget-at-handoff.json`: cumulative source allowances already used, including saved audit prose.
- `data/catalog-candidates/catalog-production-001/excluded-identities.json`: conservative same-subject exclusions.
- `data/catalog-candidates/catalog-production-001/batch-009/frozen-initial/`: the provisional draft and research evidence before its first audit.
- `data/catalog-candidates/catalog-production-001/batch-009/audit/{science,systems,culture}/initial-review.json`: existing independent findings. Also inspect any saved expansion assignments and logs; unfinished follow-ups are not completed checks.

Internal research was stopped when the user clarified that this work should be handed to an external AI. Of 200 drafts, **35 passed author, structural, source, clarity, and relationship checks and are complete**. Preserve those cards and their supporting source content exactly; carry their existing review evidence forward without researching or rewriting them again. The full batch checkpoint remains incomplete. The handoff manifest excludes the assembly-generated `originating_input_sha256` from source-content comparison: that provenance field may refresh truthfully when an input file changes, while the original provenance snapshot remains preserved.

The remaining **165 IDs** include 160 author-checked but not independently reviewed drafts and five cards with recorded material findings. Reuse their research where useful, verify the passages yourself, and finish those entries. Their existing author flags are not proof of completion. If direct counterevidence unexpectedly implicates a protected completed card, report it for review while preserving the record.

The frozen baseline contains 1,467 previously described identities. Preserve those cards and all operational catalog files byte-for-byte. The new word limit applies to this batch; longer legacy descriptions remain valid. Keep imported descriptions/raw records separate and exact. Use the frozen baseline as the authority for original imports, not a fresh network label that may have changed.

Write all new or revised work under:
`data/catalog-candidates/catalog-production-001/batch-009/external-delivery-001/`.
Treat the original research, frozen draft, and audit findings as read-only evidence. If this delivery directory already contains work, resume it without overwriting its recorded history.

Completion criterion: the baseline, 35 completed cards, and original evidence are protected; the 165 unfinished target IDs and their prior issues are understood.

## 2. Research identities, meanings, and learning takeaways

Research the 165 unfinished reserved IDs. Together with the 35 completed cards, they span all 23 domain groups and the four scopes: `broad_field`, `topic`, `idea`, and `facet_or_application`. These are scope classes, not a mandatory four-level tree. Both ideas and named subjects are eligible when they support a distinct learning takeaway.

For every unfinished card, inspect a substantive passage from a primary, official, or authoritative educational source. Search snippets, an identity URL, a Wikidata label, and general model knowledge are discovery leads; they do not substantiate the explanation. Record the source actually inspected, its locator, inspection method, acquisition metadata, and available revision.

Check the intended sense against the frozen identity and original description. Multiword concepts are valid. Separate meanings of a shared word retain separate IDs. Conversely, pluralization, spelling variants, and paraphrases of one subject do not create new concepts. Compare against prior described local identities as well as external IDs; the excluded-ID file contains examples of duplicates missed by exact label matching.

If a reserved ID proves unusable, document the problem and any researched alternative. Keep the original reservation manifest unchanged; report a shortfall or a proposed replacement for review rather than silently substituting IDs or inventing an explanation. Limit each failing URL to two attempts, followed by at most three alternative sources.

Completion criterion: every unfinished ID has a clear meaning and a source-supported learning takeaway, with actual passage evidence and honest unresolved issues; the 35 completed records remain exact.

## 3. Write one short discovery card per identity

The body contains **1–25 whitespace-separated words**. Titles and source links are outside this limit. There is no requirement to fill all 25 words.

Identify the intended meaning and give one concrete mechanism, consequence, distinction, or example worth exploring. Broad fields use everyday language. More specific concepts may use useful domain terminology. Include named subjects through a learning takeaway rather than only their category or fame.

Keep conditions that make a claim accurate: mathematical assumptions, jurisdiction, historical setting, population, uncertainty, and optional effects. Choose fewer claims when space is tight. An illustrative example must remain visibly an example; “can” or “sometimes” must not disappear when that would make the claim universal. Medical and food-preservation cards explain concepts rather than supplying personal treatment, dosing, or processing instructions.

Provide the references actually supporting the body. A citation that supports most of a sentence still leaves an unsupported clause unresolved. Adding a precise adjective or consequence requires evidence too.

For relationships, use resolved target IDs and the allowed types: `broader_topic`, `facet_of`, `application_of`, `related_to`. Mark `source_asserted` only when the inspected passage or explicit source organization establishes that relationship; otherwise use a justified `editorial` connection. An object, ingredient, study target, or nearby category is not automatically a parent. Prefer a precise supported parent and retain an honest gap when none is established.

Completion criterion: all 165 unfinished cards satisfy the word limit, wording rules, and complete claim/relationship support; preserve the 35 completed cards as supplied.

## 4. Resolve the recorded findings and inspect the rest

Preserve the original fixed sample of 20 random and 20 risk cards and its initial findings. Address at least these recorded issues:

- `Q100196` Archaeopteryx: the cited AMNH article does not support the word “long” in the tail description. Inspect and attach the identified substantive alternative, or narrow that detail.
- `Q1381652` Oral rehydration therapy: the cited WHO overview does not support the intravenous-fluid clause. Inspect and attach the identified WHO fact-sheet passage, or narrow the claim without losing necessary qualifications.
- `Q1697305` Motif: the draft makes optional narrative effects categorical. Restore a source-supported qualification.
- `Q10283` Kumbh Mela: inter-tradition exchange exceeds the inspected passage. Substantiate or remove that detail.
- `Q12602483` Petit jury: the parent points to Political science although the passage establishes a court procedure. The reviewer identified `Q837675` Jury as a potentially supported precise parent; verify the target and actual passage before using it.

Also inspect `Q1323789` Grand jury for the same relationship problem. Finish the qualification and citation-coverage follow-ups recorded in the audit directory. A screening flag is not an established failure; decide using the actual claim and passage. Keep follow-up results separate from the original random/risk counts.

Check **every unfinished card** yourself for meaning, claim support, short-card clarity, and all attached edges. Your own checks are author/self-review, even when performed in a later pass. Record that honestly; a self-review does not establish independent acceptance or human interestingness. For the 35 completed cards, retain the existing author and independent-review records with their provenance instead of claiming to have repeated those checks.

Advance `card_version` when unfinished card text, evidence, or relationships change. Retain the previous version and a repair reason, binding the original snapshot hash. Existing provisional cards start at version 1; unchanged cards can retain it. Do not edit the completed cards, frozen draft, or original initial-review files.

Completion criterion: each issue has a visible resolution or unresolved status, every unfinished card has a current-version self-check, and no failed sample or completed card is replaced.

## 5. Assemble and validate the delivery

Use the established schema. Each concept includes:
`id`, `label`, `aliases`, `entity_kind`, `scope`, `domains`, `learning_takeaway`, `card`, `original_description`, `identity_urls`, `evidence`, `relations`, `card_version`, `imported_records`.

Evidence records include `source_id`, `locator`, and `note`. Source records include a unique `id`, `title`, `url`, `locator`, nullable `revision`, a valid ISO acquisition date/time with an honest time basis, `inspection_mode`, and the applicable source word allowance. Relations include `target_id`, `type`, `source_ids`, `assertion`, and `note`.

For compatibility, keep the existing science/systems/culture partition names and shard IDs when preparing inputs. You are producing all three partitions yourself; no coordinator approval step remains. Copy the reservation and identity-decision files unchanged into your delivery directory. Preserve their original SHA256 hashes in every shard.

The local tools in `data/catalog-candidates/catalog-production-001/tools/` can assemble the three candidate inputs and check structural contracts. Inspect their CLI arguments before use. Emit the combined result as `external-delivery-001/catalog.json`. Validation must cover distinct IDs, reservation coverage, 25-word bodies, exact original imports, evidence references, target meanings/resolution, repeated/reversed assembly, version lineage, legacy preservation, and exact preservation of all completed-card/source hashes in the handoff manifest. Numerical validation does not prove factual accuracy.

Maintain source-wide budgets across bodies, takeaways, substantive notes, quotations, retained draft versions, and review/repair prose. Companion representations of a source share its allowance. Deduplicate identical copied snapshots, not genuinely different explanations. Add your new prose to prior retained prose; do not reset a page’s budget for a new pass. Use concise notes and fresh appropriate sources when needed. Avoid long quotations.

Return:

1. `catalog.json`: the single combined candidate file.
2. `research/`: complete shard inputs, inspected-source logs, current ID-keyed author/self-checks, and source-word budgets/ledgers.
3. `repairs.json`: exact before/after changes, issue outcomes, prior/current versions and relevant hashes.
4. `validation.json`: actual checks run, outcomes, unresolved issues and protected-file hashes.
5. `report.md`: distinguish the 35 protected completed cards from the 165 externally researched cards; include valid yield, domain/scope/named-subject coverage, graph gaps, fixed-sample and follow-up outcomes, limitations, and actual usage/time if available. Label unavailable measurements honestly.

Package those files into `OtherWise-catalog-research-batch-009-external-delivery-001.zip` for return, retaining the unzipped workspace files. Confirm that the ZIP contains the final JSON and its supporting files, not just a report or links.

Completion criterion: the files are saved, machine-readable, internally consistent, and ready for an independent review. Report the actual valid yield if fewer than 200 can be completed. Return this checkpoint and stop; the remaining 4,800 follow only after the returned batch is reviewed. Keep operational data, embeddings, recommender defaults, and human-study files unchanged.
