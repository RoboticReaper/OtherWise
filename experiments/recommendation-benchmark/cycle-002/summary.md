# Recommendation experiment 002: strongest measured systems

**K-connection** is the strongest specific-concept candidate in this comparison. **K-literal** has the highest broad-topic discovery score. **V3** is the faster hybrid control. These are experimental leaders under the fixed assistant rubric; specific-concept improvement remains uncertain across interest families.

## Shortlist

Scores use ten requested slots, source/identity checks, and a clear connection gate. Discovery combines connection, conceptual novelty, exploration value and accessibility; depth emphasizes connection and exploration; variety measures relevant lexical diversity. Higher scores do not establish actual personal curiosity.

| System / evaluated track | Connection | Discovery | Depth | Variety | Warm p95 |
|---|---:|---:|---:|---:|---:|
| Original V0 / specific | 0.6389 | 0.5017 | 0.5481 | 0.5112 | 62 ms |
| **K-connection / specific** | **0.7833** | **0.6303** | **0.6763** | **0.6315** | 28 ms |
| V3 / specific | 0.7444 | 0.5828 | 0.6369 | 0.5930 | 20 ms |
| Original V0 / broad | 0.7556 | 0.5639 | 0.6281 | 0.6130 | 19 ms |
| K-connection / broad | **0.9333** | 0.6706 | **0.7717** | **0.7500** | 26 ms |
| **K-literal / broad** | 0.9167 | **0.6792** | 0.7679 | 0.7376 | 26 ms |

K-connection emphasizes retrieval relevance and applies a small content bonus and soft redundancy penalty. K-literal gives more weight to the user's literal phrase during semantic retrieval, with larger content/novelty/diversity weights. Both use the separately named V5-known policy: exclude verified known concepts and input near-restatements, then allow other unknown concepts within a declared distance cap. This avoids assuming that familiarity with an entire field means familiarity with all its methods.

V3 retains the original distance band and graph/semantic/keyword fusion. It is a useful comparison when the stricter geometric policy or faster specific serving matters. Timing is from one first/warm pair per profile and system, rather than a production load test.

The exact runnable configurations and per-metric leaders are in [shortlist.json](shortlist.json). One system can win multiple metrics; the experiment does not force a different winner for every goal. K-literal's broad discovery lead over K-connection is only 0.0086, so that small distinction remains provisional.

## What was improved and tested

Sixteen declared configurations ran on eight development families: the five initial interest groups and three explicitly historical families from cycle 001. Broad and specific results were separate tracks; seventeen additional cases checked regression behavior. Treatments varied literal/canonical query blending, description-shape features, relevance, novelty, redundancy, and distance caps. The no-content ablation changed only the content weight.

Development nominated the union of both tracks' per-metric leaders plus V0–V3 controls. Eight frozen finalists then ran once on six fresh families: astronomy, organic chemistry, birdwatching, photography, urban planning and economics. Source data, MPNet revision, evaluator, rubric, configuration, split and recommendation-code hashes were frozen first. Final scores did not feed back into ranking or configuration changes.

The session assistant reviewed method-blind source presentations, as requested. There are 486 development and 213 held-out grade keys, each with C/N/E/A, a bridge and a reason. Development reused 149 exact prior profile/content/evaluator keys; 550 new keys were graded in this cycle. All background was unknown, so A is null and contributes the disclosed neutral 0.5. The implementing assistant retained session context; an independent second judge and repeat/order audit were not performed. No additional participant ratings or external evaluator calls were required.

Held-out lists have zero missing grades and zero source/identity integrity failures. Development retains four legacy broad V0/V1 lists with six known/duplicate identity violations; those systems are ineligible for that development track. Ten empty development quality lists also remain in the scores rather than being discarded. [Validation](validation.json) recomputes scores and verifies evidence identities; [review](review.md) records code checks.

## How convincing are the gains?

| Held-out leader versus V0 | Mean gain | Family-bootstrap 95% interval |
|---|---:|---|
| Specific discovery, K-connection | +0.1286 | [-0.0156, +0.2581] |
| Specific depth, K-connection | +0.1282 | [-0.0413, +0.2715] |
| Broad discovery, K-literal | +0.1153 | [+0.0067, +0.2453] |
| Broad depth, K-connection | +0.1436 | [+0.0108, +0.2815] |

All four specific gain intervals include zero. Broad gain intervals are positive under this benchmark, but six synthetic families and one assistant judge limit interpretation. Against V3, specific discovery gains +0.0475 with interval [-0.0684, +0.1564]; broad discovery gains +0.1272 with interval [+0.0191, +0.2508]. Full paired deltas and all metrics are in [uncertainty-by-kind.json](uncertainty-by-kind.json). These are estimates for observed finalist leaders, without adjustment for selecting the maximum among finalists.

The development discovery/depth leader K-canonical did not remain the aggregate final leader. K-connection improved specific discovery on five of six families versus V0, but photography fell from 0.7233 to 0.5183. It still returned weak visual/lighting matches. Birdwatching improved from 0.1467 to 0.3417, yet only five of ten suggestions passed the connection gate. Missing focused coverage and sparse descriptions remain real weaknesses. A larger graph alone does not solve them.

[Frozen-grade weight sensitivity](sensitivity.json) transfers 0.05 between formula weights without retuning: K-connection remains the specific discovery/depth/variety leader, and K-literal remains the broad discovery leader. This checks formula stability, not the accuracy of the assistant's judgments. Production retains its current default.

## Examples for the initial interests

These sourced concepts were actually returned by K-connection on the separate initial interest profiles. They illustrate defensible connections; their familiarity to the user is unknown.

| Interest | Returned concept | Connection to explore |
|---|---|---|
| Computers | [Block floating point](https://www.wikidata.org/wiki/Q25313071) | A shared exponent gives floating-like arithmetic on a fixed-point processor. |
| Engineering | [Continuum mechanics](https://www.wikidata.org/wiki/Q193463) | Model how materials behave as continuous media. |
| Science / technology | [Knowledge-based systems](https://www.wikidata.org/wiki/Q1412694) | Programs reason from a knowledge base to solve complex problems. |
| Tennis | [Infinity Walk](https://www.wikidata.org/wiki/Q17144486) | A coordination-development method connects to movement demands. |
| Soccer | [Behind closed doors](https://www.wikidata.org/wiki/Q489219) | Explore sporting events played without spectators. |

Soccer's weak supply of concrete tactics/mechanisms is visible in the full development lists.

## Run and inspect

With these saved artifacts present and recommendation source matching `6605c85`, run:

```sh
.venv/bin/python experiments/recommendation-benchmark/cycle-002/analyze.py
```

The analyzer verifies saved evidence and regenerates diagnostics; it does not rerun or tune held-out recommendations. Manifests bind source by content hash, so later recommendation-code changes require the frozen source for this validation. Cycle 001 similarly requires its frozen source commit `b419937`.

For new runs, use the [lab workflow](../../../recommendation_lab/README.md). This cycle is closed: its held-out families become historical data for subsequent tuning, which requires a fresh final split. The pinned local model initialized in about 3.4 seconds for the final run. A separate [combined-interest resource probe](resource-probe.json), including initialization and the three shortlist configurations, measured peak resident memory of approximately 1.0 GiB; this was not a production load test. Evaluator usage cost was not measured; no external serving/evaluator calls occurred. Backend checks passed **416 tests** with **2 skips**; extension checks passed **164 tests**.
