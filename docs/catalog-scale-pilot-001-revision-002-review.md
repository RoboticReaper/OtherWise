# Scale pilot 001 — reconciled candidate revision 002

Reviewed 2026-10-08. **The approved cleanup is complete.** [Revision 002](../data/catalog-candidates/scale-pilot-001/revision-002/catalog.json) preserves 1,000 discovery cards, reuses verified current identities, applies the two reviewed corrections and passes fresh structural and combining checks. It is a candidate for further catalog work; operational import has not occurred.

The [original intake review](catalog-scale-pilot-001-review.md), delivery, author report and historical audits retain their original hash scope. The pilot's [current pointer](../data/catalog-candidates/scale-pilot-001/current.json) identifies the revised files. Detailed decisions and reproducible tools are linked from the [revision README](../data/catalog-candidates/scale-pilot-001/revision-002/README.md).

## Current baseline and actual yield

The new baseline pins all **31,637 topic rows**, the discovery graph, identity registry and latest active candidates 001/002. The repository's actual `Inventory` implementation gives **34,849 runtime identities**; adding the prior candidates gives **35,032 baseline IDs**. All five source files are copied and fingerprinted in the revision's [baseline manifest](../data/catalog-candidates/scale-pilot-001/revision-002/baseline-manifest.json). Historical archives do not contribute extra active entries.

| Measure | Revised result |
| --- | ---: |
| Distinct pilot cards | 1,000 |
| New identities against the full pinned baseline | 715 |
| Existing identities with researched pilot cards | 285 |
| New fine-scope subjects | 628 |
| New fine-scope idea entities / named subjects | 580 / 48 |
| Named subjects, all scopes | 158 |
| Primary domains | 23 |
| Card word counts | 35–50 |
| Source records / distinct source URLs | 582 / 581 |
| Relationships: source-asserted / editorial | 565 / 458 |

The earlier 819-new count used the smaller delivered baseline. **The current 800-new target has an 85-identity shortfall.** The 600-new-fine-scope target is met; a stricter idea-entity-only interpretation would count 580. All five batches fall below their original 160-new target after reconciliation. Those differences describe actual inventory overlap, rather than rejected descriptions. No replacement cards were generated to satisfy a quota. [Metrics](../data/catalog-candidates/scale-pilot-001/revision-002/catalog-metrics.json) retain per-batch counts and domain/subfield memberships.

## Meaning decisions and corrections

Three separate research reviewers checked the 108 offered matches for formerly new cards. A further check using the actual runtime identity rules found four registered pilot controls with newly available equivalent identities: Worker cooperatives, Lahar, Rain shadow and Unreliable narration. These were reviewed separately. Across **112 decisions**, **108 reuse existing IDs**, two retain distinct meanings and two retain distinct facets. Of the 108 reuses, 104 explain the reduction in new-topic yield; the four controls were already counted as existing.

The reviewed redirects affect this pilot candidate. Original local IDs, complete old records, source namespaces and input hashes remain in [revision lineage](../data/catalog-candidates/scale-pilot-001/revision-002/revision-lineage.json). This does not rewrite the operational registry or settle the four older historical proposals about Urban heat island, Silk Road, Confirmation bias and Material culture.

Raft's consensus protocol remains separate from the watercraft. Rhetorical apostrophe remains separate from punctuation. Chandra reuses the observatory identity while explicitly rejecting the lunar-deity match. Examples such as a particular telescope, bridge mechanism or theorem formulation enrich the explanation of an existing subject without creating an additional identity.

Mulching retains its action identity and gains a supported `related_to` link to the mulch material; the [UMN reference](https://extension.umn.edu/garden-and-home/yard-and-garden/gardening-in-minnesota/mulching-for-soil-and-garden-health) distinguishes the covering material from selecting and applying it. Warranties as quality assurance retains its economic application identity and gains `application_of` Warranty; [OpenStax's mechanism discussion](https://openstax.org/books/principles-economics-3e/pages/16-1-the-problem-of-imperfect-information-and-asymmetric-information) explicitly connects warranties with reassuring buyers about quality. The coordinator separately inspected both passages before accepting these edges.

The Chemigram card now qualifies oils/varnishes as common optional materials, supported by the previously reviewed V&A and Pierre Cordier passages. Feature (archaeology) now includes its existing NPS context source at card level. These are the [two recorded source corrections](../data/catalog-candidates/scale-pilot-001/local-review/card-corrections.json), applied to revised copies. Chemigram is the only changed card body; the other 999 descriptions remain unchanged.

All affected relationship targets and ambiguity decisions were rewritten through the accepted mapping. Registered imported descriptions and full source rows remain separate from the generated cards. This matters for Brouwer's theorem: the imported shorthand omits hypotheses, while its discovery card retains the qualified closed-ball self-map statement. A raw imported description is provenance, not a replacement for the reviewed explanation.

## Fresh verification and remaining limits

- **40 unit tests passed:** nine reconciliation tests and 31 combiner/runner tests. These cover stale/hash-mismatched reviews, unsupported automatic merging, homonyms, canonical collisions, provenance, changed versions, incoming targets and explicit handling of self-edges.
- **12 actual-output regressions passed**, with zero failed or unrun cases and `fixture_only: false`. They operate on exactly the five revised candidates, revised identity decisions and full pinned baseline. Mutation fixtures remain separate from accepted research.
- Independent read-only validation passed **5,410 checks** over the actual records, source/target resolution, raw imports, legacy redirects, changed bundles, selected snapshots and canonical hashes. A repeat build produced identical candidate, catalog, decision and lineage bytes.
- All seven original delivery artifacts and the three operational data inputs remain byte-identical. The protected identity implementation also remains unchanged.

See [structural results](../data/catalog-candidates/scale-pilot-001/revision-002/structural-validation.json), [unit tests and rebuild](../data/catalog-candidates/scale-pilot-001/revision-002/unit-tests-and-rebuild.json), [combiner verification](../data/catalog-candidates/scale-pilot-001/revision-002/combiner-verification.json) and [actual regressions](../data/catalog-candidates/scale-pilot-001/revision-002/data/catalog-candidates/scale-pilot-001/merge-validation/actual-regressions/revision-002-20261008/regression-results.json).

The original fixed audits still describe their original cards. The new meaning reviews inspect the proposed identity matches; they are not a fresh factual audit of all 1,000 cards. Six exact Wikidata refreshes were unavailable (Q844449, Q47607, Q11878049, Q683979, Q281126 and Q223325); their decisions rely on pinned registered descriptions plus inspected authoritative explanations, with access limits retained. Retrieved/indexed item pages also do not establish equality with the imported revision. The reviewer reports preserve these distinctions and failed source attempts.

Graph coverage remains incomplete: **574 of 791 fine-scope cards lack any parent/application edge**, and **653 lack a source-asserted one**. Ten cards have no edge at all. The two defensible added links do not repair the general coverage gap. Acquisition-cache gaps and unavailable platform token/cost metrics remain as disclosed in the original review.

**This supports continuing in bounded, independently checked batches.** Future selection must include the full current inventory, active prior candidates and this revised pilot, honoring its reviewed redirects. Keep originality goals separate from explanation quality and report shortfalls against the actual baseline. This catalog validation does not establish recommendation interestingness or sustained interest expansion.
