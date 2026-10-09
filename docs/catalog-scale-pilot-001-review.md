# OtherWise scale pilot 001 — local delivery review

The findings below describe the original intake. **The approved cleanup is now complete in [candidate revision 002](catalog-scale-pilot-001-revision-002-review.md)**; the original delivery and this historical assessment remain available.

Reviewed 2026-10-08. **The delivered research is a useful, well-documented pilot, with reproducible structural and combining results. It needs current-inventory identity reconciliation, one verified wording correction and a minor citation improvement before operational import or an unrestricted production run.** This assessment concerns catalog data quality; it does not establish recommendation appeal or sustained interest expansion.

The delivered candidates and author report are preserved unchanged. The results below come from fresh local checks and a separate source reviewer, rather than accepting the author's completion statement alone.

## Organization and integrity

- The five candidates are in `data/catalog-candidates/research-batch-003.json` through `research-batch-007.json`.
- The combined candidate and delivered pilot evidence are in [scale-pilot-001](../data/catalog-candidates/scale-pilot-001/README.md). The original [agent results report](catalog-scale-pilot-001-results.md) remains separate from this review.
- The three original ZIPs, complete extracted delivery, [receipt](../data/catalog-candidates/archive/scale-pilot-001-delivery/receipt.json), and original local preparation plan are in `data/catalog-candidates/archive/scale-pilot-001-delivery/`.
- All **873 manifest-listed payload files** reproduce their recorded byte counts and SHA-256 hashes. The other two ZIP entries are the README and manifest. There are no repeated archive paths, traversal paths or symlink members.
- All seven standalone downloaded deliverables match the bundled copies byte for byte. Downloads originals remain available. Bundled `CONTEXT.md`, input snapshots and scripts are archived as evidence; the operational application files were not replaced.

## Freshly reproduced results

| Measure | Verified result |
| --- | ---: |
| Distinct accepted pilot IDs | 1,000 |
| New IDs against the delivered frozen baseline | 819 |
| Existing controls against that baseline | 181 |
| New fine-scope subjects | 703 |
| New fine-scope idea entities / named subjects | 650 / 53 |
| Named subjects, all scopes | 158 |
| Primary domains / starting subfields | 23 / 69 |
| Minimum accepted subjects per starting subfield | 8 |
| Card word counts | 35–50 |
| Scoped source records / distinct URLs | 580 / 579 |
| Relationships: source-asserted / editorial | 563 / 458 |

There are 37 broad fields, 172 topics, 596 ideas and 195 facets/applications. All five batches represent all four scopes and match their primary-domain assignments. The batch-006 fine **idea-entity** count is 112; its scope-based count is 163. The author transparently disclosed the eight-card shortfall under the stricter interpretation. Scope and entity kind should stay separate in future targets.

The [independent local structural check](../data/catalog-candidates/scale-pilot-001/local-review/structural-validation.json) verifies all cards, word budgets, source and target resolution, source namespaces, original records, selected versions, alias lookup, five input snapshots, the combined canonical hash and coverage totals. It passes **against the pinned baseline**. The first intake result that detected a live-input mismatch is preserved in `local-review/initial-intake-validation.json`; that mismatch is assessed below rather than dismissed.

After inspecting the relevant bundled code, fresh execution passed **18 coordinator tests**, **31 combiner/runner tests**, and **12 actual-output regressions**, with zero failed or unrun cases. Those regressions exercise repeated import, reversed order, reference collisions, meaning preservation, explicit version choices, malformed input, missing targets and retention of the last valid output. Their derived mutations are software-test fixtures, not accepted research. Local [test logs](../data/catalog-candidates/scale-pilot-001/local-review/unit-tests.json) and [regression results](../data/catalog-candidates/scale-pilot-001/local-review/actual-regressions.json) retain the commands and results. Original delivered candidate/catalog hashes remain unchanged.

For each original batch audit, the 20 random-new IDs and 20 disjoint risk-selected IDs reproduce from its frozen candidate. All 200 fixed IDs have initial reviewer records. Full frozen card/source packets agree with the preserved candidates. This checks sample integrity and recorded coverage; it cannot independently prove historical browsing or reviewer independence merely from logs.

## Current inventory reconciliation is required

The delivered `data/topics.json` input has **3,452 rows**, while this project's current file has **31,637 rows**. The delivered rows are an exact prefix of the current file. The other four pinned baseline input files match the project. Reproducing the repository's identity rules gives **7,033 runtime identities** for the old topic snapshot and **34,849** for today's runtime inventory. The pilot's separately augmented frozen baseline has 7,224 IDs after prior candidate contributions.

Among the 819 IDs counted as new to that frozen baseline, **108 cards have exact normalized name/alias matches to 109 identities added in the current runtime inventory**. Examples include Activation energy, Binary search, Bond (finance) and 4′33″. Their explanations can still improve existing entries, but they cannot all be treated as independently established new meanings merely because local IDs differ.

The [reconciliation queue](../data/catalog-candidates/scale-pilot-001/local-review/current-baseline-reconciliation.json) contains the candidate takeaway/card and matched live records. **These are possible overlaps, not 108 automatic equivalences.** Verify the meanings, reuse existing registered IDs where equivalent, retain genuinely distinct meanings/facets, rewrite related targets and preserve both sources. Refresh novelty totals only after those decisions. Do not replace the current inventory with the smaller delivered snapshot.

Before another production batch, freeze and fingerprint the complete current inventory, including current candidates, and use it for shared reservations and meaning checks. Generating additional cards against the old baseline would repeat this reconciliation work.

## Fresh source check and correction

A separate reviewer checked **20 cards, four per batch**, and all **21 attached relationships** against public primary/official sources. All 20 lie outside the original frozen samples. This purposeful sample found one substantive description qualification and no other substantive sampled findings; it is not a random error-rate estimate. Full findings, source locators and access limitations are in the [source review](catalog-scale-pilot-001-source-review.md).

**Chemigram** presents oils/varnishes or other resists as required for the overall process. The [V&A's Chemigram entry](https://www.vam.ac.uk/articles/photographic-processes) describes their common use, and [Pierre Cordier's process diagram](https://www.pierrecordier.com/lechimigramme.html) explicitly includes techniques with and without a localizing product. His [definition](https://www.pierrecordier.com/IMG/pdf/definition_EN.pdf) supports creation without a camera or enlarger, in full light. The distinction affects the card, takeaway and editorial comparison wording.

The proposed 39-word replacement was independently checked against those passages:

> A chemigram creates an image by manipulating photographic paper with chemicals, often using oils or varnishes. Working in full light combines the maker’s intervention with chance. The marks emerge from material reactions without a camera recording an external scene.

The [verified correction record](../data/catalog-candidates/scale-pilot-001/local-review/card-corrections.json) preserves the before/after record, proposed card version 2, revised takeaway/evidence/relationship note, extra sources and exact base hashes. It also proposes a minor citation improvement for **Feature (archaeology)**: add the already-present NPS context source to the card's evidence, where it currently supports only the relationship. Root independently inspected that [context passage](https://www.nps.gov/articles/000/what-is-archeological-context.htm); the feature's text and identity need no change. **Neither correction has been applied to the original delivery.** Apply them as recorded candidate revisions during reconciliation, then reassemble and recompute current metrics/manifests. Historical audits continue to describe the exact versions they originally checked.

The clean remaining sample supports bounded confidence in these cards; it does not certify every unsampled fact. The author's existing audits and corrections are useful evidence but do not eliminate the need for sampled external checks.

## Relationship coverage and provenance limits

Of **791 fine-scope cards**, **575 have no parent/application edge of any assertion class**, and **654 have no source-asserted parent/application edge**. Ten cards have no relationship at all. The delivered report uses the word “asserted” with the 575 count, but that number actually describes absence of **any** such edge. This is a reporting-label discrepancy, not evidence that the underlying relationships disappeared.

These gaps are documented rather than filled with invented taxonomy. The descriptions can be used for semantic retrieval, while stronger supported parent/application coverage would help graph-based discovery. Add defensible links where references establish them; keep editorial learning bridges clearly marked.

The delivery intentionally omits full public-page caches. It retains support notes, locators and capture metadata, but those do not reproduce omitted raw bytes. The author's separate 29 historical acquisition-byte gaps remain disclosed. Platform token usage and cost are unavailable, so this review cannot establish production cost per card.

## Next acceptance step

Reconcile against the full current baseline and apply the verified qualification/citation corrections in one versioned revision. Then rerun structural, combining and changed-source checks. The pilot supports continuing this research workflow in bounded batches after that cleanup. It does not justify bypassing independent source checks or claiming exhaustive coverage.
