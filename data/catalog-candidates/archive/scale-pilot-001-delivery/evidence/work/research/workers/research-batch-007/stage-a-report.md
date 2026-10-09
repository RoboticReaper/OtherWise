# Research batch 007: Stage A selection handoff

Status: Stage A complete, pending central reconciliation and global selection freeze. This is not an authored or audited candidate catalog.

## Deliverable

`selection.proposed.json` contains 204 proposals: 200 recommended, one supported reserve, and three source-supported proposals excluded because their distinctness remains unresolved.

The recommended set provisionally contains 165 new identities, 130 new fine subjects, 35 existing controls and 30 named learning subjects. Domain totals are exactly Games & sports 45, Music & performance 40, Mind & behavior 45, Philosophy 35, Politics & law 35. All 15 assigned subfields have at least nine proposed subjects. Scopes are three broad fields, 45 topics, 120 ideas and 32 facets/applications.

## Evidence and identity review

- 85 discovery references have inspected passage/section locators, support notes and acquisition metadata.
- `source-inspections.json` has one Stage A author-inspection record per proposal. This is not independent review or later author card review.
- `source-raw/` preserves available public retrieval captures; `access-log.json` includes search-only discovery separately from successful retrieval and failures. The record contains 16 failed retrievals, with no URL failing more than once in preserved captures. These failures do not support accepted claims.
- `baseline-search-results.json` records bounded calls through the supplied baseline search implementation. Relevant baseline meanings, prior candidate takeaways and additional vocabulary neighborhoods were inspected. Selected controls preserve registered IDs, including several nonliteral name matches.
- `identity-decisions.proposed.json` records the proposed comparisons. Baseline lookup is not exhaustive semantic proof. All sibling-batch comparisons remain pending the coordinator.

## Material identity decisions

Rhythmic augmentation, bridge card game, anchoring effect, figure–ground perception, string harmonic, sympathetic resonance, topspin, legal burden of proof and stratified sortition were recognized as controls rather than claimed as novel variants. Confirmation bias retains `local:authored:000049` and its earlier card history. The equivalent baseline `Q431498` remains only an explicitly noted historical equivalence proposal, as instructed.

Three nonrecommended subjects have unresolved distinctness: resultant moral luck overlaps the example already used by the broad moral-luck card; overjustification overlaps the broader motivation-crowding theory; epistemic luck in the researched angle substantially repeats the Gettier problem. They do not contribute to recommended novelty counts. Motivation crowding is retained as an existing control. The independent problem of temporary intrinsics replaces resultant moral luck in the recommended Philosophy set; grounding for coincident objects remains a supported reserve.

Potential ambiguity groups are musical pitch versus batch 004's material pitch, material constitution versus political Constitution (Q7755), and metaphysical presentism versus the baseline historiographic presentism (Q1842346). Alias separation is explicit. No musical-canon proposal is required for this batch.

## Coordination and limits

Batch 005 owns instructional methods. This batch covers memory, perception, judgment, individual motivation, qualified conformity/obedience findings and psychological methods. Measurement-method names were notified to the coordinator for reconciliation with batches 003 and 005. Batch 006 confirmed that Zhuangzi's butterfly dream and the two-truths distinction could be researched here; both have inspected scholarly evidence.

Some selected textbook passages contain simplified models or contested interpretations. Authoring must retain qualifications, notably in psychological findings, regulatory rules, music acoustics and philosophical positions. The FIDE source is explicitly the rules effective 1 January 2023. Historical court cases are sourced as cases, not as individualized current legal advice. References with a displayed update date but no immutable revision identifier retain `revision: null`.

Source reuse was selection-led, not quota-driven: several sources explicitly define multiple independent mechanisms. Later cards must support their exact claims and attached relationships. The worker has authored no discovery-card text, asserted no relationship edges, and performed no independent audit.

## Local verification

`validate_selection.py` passes 21 checks: shape, bounds, unique IDs, exact primary-domain counts, subfield minimums, novelty/control goals, all four scopes, named subjects, valid domain names, source resolution and capture existence, registered-ID consistency, baseline pin and absence of card drafting. These checks are structural, not a substitute for independent factual review.

Only this worker directory was changed. Operational inputs remain read-only. Native-cloud research was used; no Work task, per-concept AI API service or operational-file change was made. Platform token and cost measurements are unavailable and recorded as null. Elapsed wall-clock time is in `research-state.json`.
