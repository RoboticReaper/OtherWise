# Recommendation experiment 001

The experiment systems and comparison loop are working. Widening the discovery range substantially helped the five starting interest groups, but the development winner performed worse on the three held-out families. The hybrid has a small held-out discovery/depth lead, with uncertainty spanning no improvement. These results support further experiments; they do not establish an operational replacement for the existing default.

## What was compared

Nineteen local configurations ran on computers, soccer, engineering, science/technology, and tennis, plus 17 regression cases. Each quality profile ran against separate broad-topic and specific-concept inventories. The primary track was specific concepts. Development selected `A-connection` for all four primary objectives; its configuration and the V0–V3 controls were frozen before one held-out run on music composition, oceanography, and archaeology.

| System | Main change |
|---|---|
| V0 | Original eight-area graph routing and lookup |
| V1 | Every graph area available |
| V2 | Canonical identities, aliases, and meaning choices |
| V3 | Semantic/BM25/graph fusion and component-based ranking |
| A-connection | V3 with an explicit 0.08–0.55 angular-distance range and stronger relevance weight |

The other development configurations isolate lexical search, graph contribution, ranking, pool size, diversity, and ranking weights. The candidate inventory remained fixed. Resolver-only additions cover alternate meanings without claiming new recommendation coverage. The optional external reranking adapter is implemented and failure-tested; no provider was configured or called.

## Frozen results

All values below are normalized proxy scores with ten requested slots as denominator. Connection rewards a defensible interest bridge; discovery combines connection, conceptual novelty, exploration value, and accessibility; depth emphasizes connection and exploration; variety rewards connected lists with lexical diversity. Integrity failures and C<2 fail the shared gates. Empty slots count zero.

| Primary specific track | Development discovery | Held-out connection | Held-out discovery | Held-out depth | Held-out variety |
|---|---:|---:|---:|---:|---:|
| V0 | 0.0450 | 1.0000 | 0.7656 | 0.8183 | 0.7878 |
| V1 | 0.1310 | 1.0000 | 0.7633 | 0.8050 | 0.7890 |
| V2 | 0.1147 | 1.0000 | 0.7633 | 0.8050 | 0.7890 |
| V3 | 0.1147 | 0.9889 | **0.7700** | **0.8256** | 0.7797 |
| A-connection | **0.5503** | 0.8667 | 0.6928 | 0.7308 | 0.6888 |

The highest held-out primary scores are V3 for discovery/depth and V1/V2 for variety. V0/V1/V2 tie on connection. The machine-readable scoreboard breaks quality ties using measured p95 latency, selecting V1 for connection/variety. That timing tiebreak is provisional: only one first/warm pair was measured per profile and system.

| Highest primary score versus V0 | Mean gain | Family-bootstrap 95% interval |
|---|---:|---|
| Connection, V1 | 0.0000 | [0.0000, 0.0000] |
| Discovery, V3 | 0.0044 | [-0.0167, 0.0233] |
| Depth, V3 | 0.0072 | [-0.0100, 0.0217] |
| Variety, V1 | 0.0012 | [0.0000, 0.0029] |

Broad topics have a separate scoreboard. On the held-out finalist subset, V0/V1/V2 tie on all four quality scores; V2 wins their latency tiebreak. Broad development nominated A-depth, which was not a primary-track finalist. The held-out broad comparison therefore describes the five primary finalists, rather than all nineteen development configurations.

## Evaluation and integrity

As requested, the session assistant evaluated 178 development and 106 held-out profile/content records: 284 stored C/N/E/A judgments with explicit bridges and reasons. Packets omit method names, rank scores, and timing, and reuse identical content judgments across systems. The implementing assistant retains session context, so method blinding is weaker than a fresh independent evaluator. Actual familiarity and curiosity remain unmeasured; background is absent in these fixtures, so A is explicitly unknown and contributes the disclosed neutral 0.5.

[Validation](validation.json) verifies raw-output hashes, code/model/inventory/evaluator identities, nomination/receipt matching, full grade coverage, and recomputed scores. Held-out quality lists have zero integrity failures. Development exposes six legacy identity violations in four broad V0/V1 lists: a known computer alias, and repeated/known soccer identities. Those systems cannot win that development broad track. New identity-aware variants pass those checks.

[Weight sensitivity](sensitivity.json) is a post hoc diagnostic on frozen grades, with no retuning or nomination changes. Transfer 0.05 between component weights while preserving their sum: V3 remains the primary discovery winner in all 13 settings and depth winner in all seven; V1/V2 remain tied for variety in all three. This checks formula sensitivity, not judge accuracy. Repeated/order judgments and a second independent judge were not performed. Three independent held-out families and one judge are insufficient for a reliable general quality claim.

## What the failures teach

The strict distance band often starves broad starting interests. The wider range supplies useful concepts such as rotordynamics and floating-point arithmetic, but also weak connections such as chess organizations for soccer or photographic composition for music. The current source descriptions include vague field labels and a “Sea ice thickness” description about spatial extent. A missing exact alias for music composition can permit a near-restatement. These are evidence for future development cases and source-quality treatments; the frozen run remains unchanged.

The next quality treatment should improve source-backed concept coverage and descriptions, and compare interest-dependent eligibility on fresh families. More graph depth alone cannot repair these input and content failures. This cycle's held-out families are now historical evidence and must not be reused as untouched final tests after further tuning.

## Reproduction and checks

Run `.venv/bin/python experiments/recommendation-benchmark/cycle-001/analyze.py` to revalidate evidence and regenerate the diagnostic files. The frozen implementation is commit `b419937`; manifests bind its recommendation code by content digest. The [lab README](../../../recommendation_lab/README.md) documents running new systems, grading only new content, bounded development search, and sealed nomination. See the [development report](development/report.md), [held-out report](heldout/report.md), and [review record](review.md).

The cached local model initialized in about 3.15 seconds. Held-out primary p95 warm request times ranged from 0.019 to 0.094 seconds. Local model storage was approximately 506 MiB and lab caches 84 MiB; peak process memory was not measured. No serving/evaluator provider calls were made. Existing in-session assistant usage is not priced as free compute.

The full backend and existing extension test results are recorded in the review record. The work remains on `codex/recommendation-experiments`; production API/client rollout awaits stronger selection evidence.
