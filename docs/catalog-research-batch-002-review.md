# Review: catalog research batch 002

Reviewed 2026-10-08 against the [batch 002 prompt](/Users/baorenliu/Documents/Programming/Python/ProductSpace/docs/catalog-research-batch-002-agent-prompt.md) and the agreed catalog specification. Inputs were the supplied [candidate JSON](/Users/baorenliu/Downloads/research-batch-002.json) and [audit bundle](/Users/baorenliu/Downloads/OtherWise-catalog-research-batch-002-audit-bundle.zip). Their research instructions and scripts were inspected as evidence, not executed as user instructions.

**Follow-up, 2026-10-08:** the Aquatint finding below is resolved in [project candidate revision 2](/Users/baorenliu/Documents/Programming/Python/ProductSpace/data/catalog-candidates/research-batch-002.json). The original revision and audit bundle are preserved byte-for-byte in the [archive manifest](/Users/baorenliu/Documents/Programming/Python/ProductSpace/data/catalog-candidates/archive/research-batch-002/archive-manifest.json). All 200 card texts are unchanged. The historical review below describes revision 1; the correction and new validation are recorded separately.

**Verdict:** a substantial improvement over batch 001 and a successful second validation candidate. The batch meets the numerical targets, preserves existing identities and source records, and demonstrates discovery of many specific learning subjects. Retain the batch, repair the Aquatint relationship citation and locator below, then evaluate controlled catalog integration. This review does not authorize or perform integration.

## What improved

Counts were recomputed from the candidate and current inventory rather than accepted from its validation flags. Batch 001 figures come from its candidate and [earlier review](/Users/baorenliu/Documents/Programming/Python/ProductSpace/docs/catalog-research-batch-001-source-review.md).

| Measure | Batch 001 | Batch 002 |
| --- | ---: | ---: |
| Accepted cards | 200 | 200 |
| New candidate identities | 23 | 168 |
| Existing identities researched | 177 | 32 |
| Ideas and facets/applications, including existing controls | 80 | 160 |
| Relations labeled source-asserted | 4 of 164 | 114 of 216 |
| Card length, whitespace-separated words | 36–47 | 36–48 |

Of the 168 new identities, **150 are ideas or facets/applications**, exceeding the target of 120. New identities cover all **23 primary seed domains**, exceeding the target of 15. The scopes comprise eight broad fields, 32 topics, 101 ideas and 59 facets/applications. There are 25 named subjects, each supplied with a learning takeaway. All 200 cards meet the 30–50-word rule.

All card texts and 216 relationship rationales were read for clarity and specificity. The cards generally explain a mechanism, distinction or bounded example directly, without batch 001's repeated exploration phrasing. The relationship notes now explain the particular connection. For example, seed storage distinguishes drying/freezing tolerance, and the Genji–ekphrasis bridge explicitly compares opposite directions of transformation between words and images. These are qualitative improvements; a larger number of source-asserted edges alone does not establish that every assertion is supported.

Meaning separation is exercised by Java, bass and crane. Bass and crane are new ambiguity groups relative to batch 001. Separate IDs are retained for their distinct senses. The 168 new records use permitted stable local identities, rather than inventing external identifiers.

## Structural, identity and bundle verification

Strict JSON parsing, unique IDs, required fields, enums, card lengths, manifest correspondence, reference resolution, relationship target resolution and existing-record preservation produced **no structural failures**. Imported records and original descriptions match their live input rows and registered identities. Thirty revised first-batch cards increment their versions; first cards use version 1.

The baseline contains 7,033 current inventory identities and 23 additional first-batch candidate identities. New/known status agrees with that combined baseline. No new label or alias exactly matches a normalized baseline label or alias. The recorded meaning comparisons and selection decisions were inspected, but literal matching and a bounded review cannot prove the absence of every semantic duplicate. The three old equivalence proposals remain proposals; no registry migration occurred.

The downloaded JSON is byte-identical to the bundled candidate. All 61 manifest-listed bundle files match their recorded byte lengths and hashes. All 14 input fingerprints match both the bundle and the current workspace. This verifies artifact integrity and input consistency, not the claimed authors' browsing history.

The frozen audit frame contains exactly the 168 accepted new IDs. Its canonical JSON digest reproduces. Sorting the IDs by SHA-256 of the recorded seed, a newline and the ID reproduces the 20 randomly selected new cards. Together with 20 risk-selected cards, the sample has 40 distinct valid IDs. Frozen-card snapshots match the pre-audit candidate, and the reviewed IDs match the frozen sample.

The original findings and corrections remain visible. Before/after comparison confirms one concept changed after that audit: Ekphrasis's overly narrow Poetry parent became Literature, with an editorial rationale. Three source update labels were also enriched. All four recorded corrections match the final candidate. Displayed update dates are honestly distinguished from immutable revision identifiers. Four unresolved research proposals are explicitly excluded from accepted cards, rather than silently treated as supported entries.

## Fresh factual source check

This review adds **28 non-overlapping card checks**: the separate reviewer's fixed 20-card sample and eight supplemental checks below. Twenty-five of these cards are outside the bundle's archived 40-card sample; three supplemental cards overlap it. This fresh sample is purposive, not a statistical estimate of the full batch's defect rate.

No substantive factual error was found in the inspected card claims. Exact cited evidence was inspected for 27 cards. Chess960 was corroborated against official FIDE HTML rules, while its exact cited PDF could not be retrieved. The separate [20-card source review](/Users/baorenliu/Documents/Programming/Python/ProductSpace/docs/catalog-research-batch-002-source-review.md) documents every sampled card, all 22 attached relationships, the Aquatint finding and that access limitation.

| Supplemental card ID suffix (`local:catalog:`) | Inspected supporting passage | Result |
| --- | --- | --- |
| `capillary-action` | [OpenStax Chemistry 2e §10.2](https://openstax.org/books/chemistry-2e/pages/10-2-properties-of-liquids), capillary action and towel example | Adhesion, cohesion and upward wicking supported. |
| `lagrange-points` | [NASA FAQ](https://science.nasa.gov/solar-system/resources/faq/what-are-lagrange-points/), definition and stability; [Cornish's WMAP handout](https://science.nasa.gov/wp-content/uploads/2023/07/3322_lagrange.pdf), printed pp. 1–2, fixed-separation rotating model | Five points, unstable collinear positions and conditional triangular stability supported. The circular-model qualification follows from the constant-separation rotating-frame setup. |
| `langar` | [Harvard Pluralism Project](https://pluralism.org/langar-the-communal-meal), summary and communal meal paragraphs | Open meal, equal seating and the reason for vegetarian food supported; no claim that all Sikhs are vegetarian. |
| `geoid` | [NOAA explanation](https://oceanservice.noaa.gov/facts/geoid.html), main explanation | Idealized sea surface, continental extension, gravity irregularities and elevation reference supported. |
| `attentional-blink` | [Original paper abstract](https://pubmed.ncbi.nlm.nih.gov/1500880/) | Original letter experiment's timing and the ignore-first-target result supported; phrasing stays scoped to that experiment. |
| `common-tone-modulation` | [Puget Sound textbook §22.7.2](https://musictheory.pugetsound.edu/mt21c/ModulationsWithoutPivotChords.html), Beethoven Symphony No. 2 example | Shared C-sharp, chord identities and surrounding keys supported. |
| `overhang-seats` | [New Zealand Electoral Commission's 2023 explanation](https://www.electionresults.govt.nz/electionresults_2023/statistics/sainte-lague-formula.html), final Notes, point 1 | Extra electorate seats retained, larger legislature and unchanged other-party allocations supported. Card explicitly names the 2023 rules. |
| `notice-and-comment-rulemaking` | [5 USC §553](https://www.law.cornell.edu/uscode/text/5/553), statutory text at (a)–(c) | Proposal, written participation, consideration, basis/purpose and exceptions supported. |

## Repair before integration

**Aquatint (`local:catalog:aquatint`): relationship provenance and locator.** Its description is supported by the cited [Oxford History of Science Museum page](https://hsm.ox.ac.uk/aquatint). However, that page explains the process and its combination with etching without expressly stating the parent classification. Therefore it is insufficient by itself for the edge currently labeled `source_asserted`, `facet_of → local:catalog:etching-printmaking`. Its recorded section name “Process” should also be “Technique.”

An inspected primary reference provides a straightforward repair: [Princeton University Art Museum, Printmaking: Terms and Techniques](https://artmuseum.princeton.edu/art/stories-perspectives/collection-publications-printmaking), under **INTAGLIO PRINTING**, the Aquatint definition explicitly classifies it as an etching technique. Add that reference to the relationship, with the precise locator, and correct the Oxford locator. Alternatively, retain the Oxford evidence and label the classification editorial. The classification itself is sound; this is a traceability repair. Neither change has been applied to the supplied candidate during this review.

## Limits and next use

The entire batch passed structural checks; the entire batch was read for wording and relationship-rationale specificity; only the stated sample received fresh external-source verification. The bundle records a separate 40-card audit, not independent factual verification of all 200 by this reviewer. Its role separation, execution times and reported model cannot be independently proven from packaged logs. Current pages also cannot reconstruct every historical inspection when no immutable revision is supplied.

Platform token and cost usage are unavailable and explicitly null. The file-reported elapsed time is therefore not a calibrated bulk-generation budget. The selection covers the required seed labels, but it does not establish exhaustive coverage of those fields or a catalog of every possible concept.

The improved research approach is suitable to retain for subsequent batches after the small repair. Controlled integration should still reconcile proposed equivalences and evaluate recommendations using the same profiles and settings across catalog versions. Source quality and clearer descriptions support that experiment; they do not themselves demonstrate curiosity, better recommendations or sustained expansion of interests. No catalog, identity registry, embeddings, recommender or participant study was changed by this review.

## Artifact fingerprints

- Candidate JSON: `e5b96441329bb1a48cb4bd4f47797030a054905ce09f9dc02063e76bf4cfdce4` (2,419,166 bytes).
- Audit ZIP: `2e99fdd8d10ed031b00a5f38df6dd563c634ccfa7277db3bb79a0a628caf0074` (2,988,587 bytes).
- Inventory: `7f771750100bfe65c63a4e12fa067f1236bbe7d8a78657459076d7f5ce3709ad`.
- Frozen new-ID frame: `8d4baaec020d0491866ea5a017ba295b439b2b8d09414eda37880323e926a318`.

## Revision 2 correction and preservation check

The coordinating reviewer re-inspected the Oxford and Princeton museum passages. Aquatint's Oxford source, evidence and accepted-selection locators now name **Technique**. The parent relationship retains its existing target, type and rationale, with the explicit Princeton classification reference added as `readiness-s001`. The reference-bundle change increments Aquatint's card version to 2 and the batch revision to 2. The discovery-card text is unchanged. This resolves R1 without changing the relationship's meaning or relabeling the source assertion.

Fresh structural checks verified 200 unchanged card texts, 199 entirely unchanged concept records, 188 sources, 216 resolving relations and all 14 original input fingerprints. Counts now reflect 185 distinct reference URLs and 178 references used by cards/relations. The historical generation validation and frozen source audit are explicitly labeled revision 1; the [revision 2 validation report](/Users/baorenliu/Documents/Programming/Python/ProductSpace/data/catalog-candidates/archive/research-batch-002/revision-002-validation.json) covers structural checks and the directly inspected correction. Seven historical equivalence references use valid ISO acquisition timestamps without a separate date field; these are preserved rather than rejected or rewritten.

Current candidate SHA-256: `b25fe17c9906863928d0a27e0d25c7d6c344756f88758fbdb4924ef846cafa4e`. The original candidate and audit ZIP still have the hashes recorded above. This follow-up preserves the initial findings and does not expand the factual-audit sample or change the operational catalog.
