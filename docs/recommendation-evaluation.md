# Recommendation evaluation design

Updated 2026-10-07. The user requested evaluation without a required human trial. This design maintains a separate automated proxy champion for each objective; it does not claim to measure actual personal curiosity.

The confirmed product goal is tunable, defaulting to unfamiliar, connected discovery. External AI services are acceptable when quality improves. Ambiguous phrases use saved-interest context and offer a meaning choice when uncertainty remains. Definitions are in [CONTEXT.md](../CONTEXT.md); evidence is in [the audit](recommendation-audit.md) and [research](recommendation-research.md).

## What “best” means

“Best” means the highest held-out score under the same frozen evaluator and resource constraints. The evaluator is an explicit product policy. Interestingness to a real person remains unverified unless optional behavioral or human evidence is available.

Use two evaluation layers. Deterministic checks enforce concept identity, sources, known exclusions, duplicates, intended senses on labeled fixtures, and request constraints. An evaluator separate from the recommender grades discovery quality from the same interest/context and source-backed candidate text.

The original reference rubric, rubric-v0, uses 0–3 grades, normalized to [0,1]. The initial personal check is complete; the challenger treatments below are proposed for comparison, with personal evidence retained outside public artifacts. No automated evaluator has been calibrated or algorithm champion selected by that check.

| Component | Question | Default weight |
|---|---|---:|
| Connectedness, C | Is there a clear, defensible bridge to an intended interest? | 40% |
| Meaningful novelty, N | Does it add a distinct, nonobvious idea rather than a synonym or restatement? | 30% |
| Exploration value, E | Does it offer a concrete question, method, phenomenon, or insight worth exploring? | 20% |
| Accessibility, A | Is there a credible starting point, given only the background explicitly available? | 10% |

Novelty here means semantic/conceptual novelty plus observed known/exposure evidence. It does not mean the evaluator knows what this person has learned. With no background evidence, unknown accessibility receives a disclosed neutral 0.5 and an uncertainty marker; it is not guessed from graph depth.

Reject source/identity failures, explicitly known concepts, repeated identities, and connectedness below 2/3 before scoring. A meaningful cross-domain bridge can qualify; a shared word alone cannot. A false or invented bridge does not qualify.

For a passing candidate, the default discovery score is S = 0.40C + 0.30N + 0.20E + 0.10A. Failing candidates contribute zero. Let avg10(X) be the sum of X over distinct passing results divided by ten requested slots. Missing slots contribute zero; missing evaluator grades make the affected score unavailable.

Maintain a separate champion for each frozen scorecard:

| Goal | Metric | Priority |
|---|---|---|
| Connection | ConnectionScore@10 = avg10(C) | Strongest defensible connection |
| Connected discovery, default | DiscoveryScore@10 = avg10(0.40C + 0.30N + 0.20E + 0.10A) | Connected, nonobvious ideas worth exploring |
| Deeper exploration | DepthScore@10 = avg10(0.55C + 0.30E + 0.15A) | Useful and approachable further exploration |
| Relevant variety | RelevantDiversity@10 = 0.60 × avg10(C) + 0.40 × (passing count / 10) × D | A varied list that remains connected |

D is mean pairwise angular distance normalized to [0,1] in a separately frozen evaluator embedding space, over passing concepts only; it is zero for fewer than two. Shared relevance/identity gates prevent unrelated randomness from winning. DiscoveryScore was previously called ProxyDiscovery; human-rated QualifiedDiscovery remains separate.

Report every system on every scorecard. One system may win several tracks. Keep serving latency/cost and Pareto comparisons alongside quality rather than converting dollars into an arbitrary interest score. Ranking weights may be tuned on development cases; the scorecards must stay frozen. These weights and thresholds are declared engineering choices, not scientifically calibrated constants.

## Pilot-informed rubric challengers

The initial check supports testing more specific learning opportunities, finer familiarity scope, clearer connections, and usable entry points. It does not support fitting new numerical weights from a small pooled sample. Preserve rubric-v0 scores and identities. Each treatment below changes one part of the evaluator/presentation contract, receives its own rubric/content version, and must be assessed separately before any combined challenger is tested. Never compare scores from different rubric versions as if they share one scale; reevaluate all finalists under the same version.

**Concrete exploration value.** Use a specific phenomenon, method, strategy, question, or mechanism as the discovery unit. Broad fields can be navigation anchors for finding that unit. For a challenger E rubric, grade 0 for an unidentifiable idea or unsupported claim, 1 for a broad label/vague field without a concrete learning opportunity, 2 for a specific idea with a source-backed explanation of what can be explored, and 3 when that explanation also identifies a concrete mechanism, question, or trade-off. Reward informational content, not description length or dramatic wording. Show a concise connection and a credible starting point; preserve the canonical concept ID and sources rather than inventing an identity for a generated hook. Presentation changes create a new content digest and need fresh grades.

**Connection strength.** Compare the original C >= 2/3 gate against a treatment allowing C >= 1/3 only when an explicit, source-backed bridge is defensible. In that treatment C=0 still fails; a shared word or invented relationship fails regardless of score. Continuous connectedness remains in all four formulas, and the confirmed default stays connected discovery. Calibrate the connection scale and bridge judgments independently; a person's recognized connection and an automated semantic connection are distinct evidence. Neither the personal sample nor a threshold change proves a winning recommender.

**Familiarity scope.** Apply explicit known exclusions to the specific concept/meaning. Familiarity with a field or activity does not exclude every unknown idea within it. Novelty should represent a distinct learning opportunity relative to explicitly supplied background, not an unfamiliar label for something already understood. Preserve familiarity, curiosity/dislike, and presentation feedback separately. Keep conflicting grades/notes visible instead of silently resolving them or inferring an entire personal curriculum.

**Accessibility.** Evaluate the credibility of a starting point using stated background and source-backed prerequisites. Challenging material can have exploration value. Accessibility remains a separately reported graded signal, not a requirement that every suggestion already feel easy. Keep unknown background disclosed; do not replace it with inferred competence.

The original human QualifiedDiscovery@10 definition remains a strict diagnostic for separately collected complete lists. It is not the sole criterion for interest: report observed curiosity and the other dimensions separately, without treating failure on one dimension as proof of no curiosity. Pooled initial ratings yield case-level evidence, not per-system @10 scores. No repeated human rating is required to compare these challenger policies automatically.

## Automated judges

Use a fixed, independently configured evaluator model or evaluator ensemble for C, N, E, and A. The recommender must not grade itself using its own ranking score. Provide identical sourced content, hide algorithm identity, and require structured grades with concise reasons and supporting input evidence. Treat candidate text as data, not judge instructions.

Cache judgments by profile/context, concept ID, content digest, rubric, prompt, and evaluator version so identical candidates receive the same evaluation across variants. Record failures and uncertainty rather than converting a timeout into a negative preference. Without a configured semantic judge, report structural/local diagnostics; do not manufacture a complete proxy score.

Check order/format sensitivity, repeated-judgment stability, and agreement on a fixed audit subset with a second independent judge. Freeze prompts and evaluator versions before the held-out run. Report the subset size and which profiles were checked. Large disagreement or a reversed ranking under modest rubric-weight changes yields an inconclusive comparison rather than an unquestioned winner.

LLM judging is a proposed approximation for this application. Research identifies position, verbosity, and self-enhancement biases; conversational benchmark agreement does not establish discovery-topic curiosity prediction. [Zheng et al., 2023](https://arxiv.org/abs/2306.05685).

## Controlled comparisons

Keep source snapshots, model/input identities, presentation, requested length, controls, feedback, and seeds fixed except for the named treatment.

| Comparison | Treatment | Question |
|---|---|---|
| Retrieval | Current eight-area graph routing versus every area; same encoding/ranking | What eligible concepts does routing discard? |
| Interpretation | Current lookup versus concept identities, aliases, and contextual resolution | Are meanings consistent and alternate-name duplicates suppressed? |
| Retrieval/ranking | Semantic, lexical, graph, and combined retrieval on one inventory; ablate ranking changes separately | Which channels and ranking changes improve the frozen proxy? |
| External assistance | External resolution and candidate reranking, changed separately | Does the proxy gain justify latency, cost, and failures? |
| Inventory | Existing versus a source-backed expansion; fixed pipeline | Does missing-concept coverage improve on untouched inputs? |

Preserve current radius, expansion, overlap, known exclusions, and overlap quotas in the initial comparisons. A separately named adaptive-novelty arm may change eligibility explicitly. Do not silently relax sliders. Different embedding models require separate cache identities and distance calibration; the existing map/Focus contract remains pinned.

## Benchmark and selection

Use public profiles with explicitly stated intended senses, ordinary/niche/mixed interests, ambiguous and contextual phrases, and known exclusions. Artificial background/persona assumptions must be labeled as fixtures. Bare ambiguous inputs have no single correct meaning without further evidence; test clarification rather than inventing an answer.

Keep related profile families in the same development or held-out split. The 17 audited cases are regression/development cases. Freeze catalogs, aliases, prompts, weights, source expansion, and evaluator versions before final evaluation. Keep held-out evaluator judgments out of ranking, prompt examples, resolver calibration, and catalog expansion.

Record item grades, list scores, per-profile failures, wrong-sense and source rates, duplicate rate, full-pool eligible recall, empty lists, evaluator coverage, and repeated-judgment disagreement. Measure cold/warm latency, p50/p95, memory, model/cache footprint, token usage, request cost, and local fallback behavior.

Compare paired per-profile gains and bootstrap uncertainty across held-out profile families. This quantifies benchmark uncertainty, not real-user satisfaction. Each operational champion must improve its frozen scorecard, pass integrity gates, remain stable under the judge/sensitivity checks, and have a reviewed resource trade-off. Otherwise retain the baseline for that track and report what remains unresolved. No human trial is a prerequisite for implementation or selecting metric-specific champions.

## Repeatable improvement loop

Run bounded cycles: freeze data, splits, evaluator, scorecards, and budget; evaluate candidate families on development cases; tune each separately for each scorecard; retain per-track development champions and a cross-metric scoreboard. Change one retrieval, resolution, ranking, or separately versioned inventory treatment at a time.

Initial local tuning limits are five rounds, twenty new configurations per round, and patience of two rounds without a development gain of at least 0.01 on any scorecard. External calls require a configured call/spending budget and stop at its cap. Reuse grades only when profile, concept, content, rubric, prompt, and evaluator identities match.

Nominate finalists and evaluate once on the sealed held-out split. Do not tune against that split every iteration. Once final results influence another cycle, those cases become history/development and a fresh held-out batch is needed. New judge, rubric, model, or inventory versions require reevaluating champions on the same new benchmark. Persist attempted configurations, failures, champions, and Pareto trade-offs; a benchmark run does not deploy a system.

## Optional real-user validation

Human validation is a separate, optional track. A participant can rate a pooled sample once for connectedness, unfamiliarity, curiosity, and accessibility, and those ratings can be reused across algorithms presenting identical content for that participant/profile. Ordinary requests never require a rating form. The user has authorized an initial rubric sanity check of 20–30 suggestions across 3–5 interest profiles, approximately 15–30 minutes. It checks whether criteria reflect their preferences; it is not a statistically powered study. Later checks can target changed champions or obvious failures.

For the initial pooled check, report item-level ratings, unknown/skipped counts, and concrete disagreements with the proposed rubric. Record the first-rating context; familiarity can change after someone explores a suggestion. A pooled sample of five items per profile is not a top-ten algorithm evaluation and cannot select champions. The rating form starts blank, permits “can't judge” or skipping, and sends answers for analysis only when the participant chooses to do so. Personal packets and responses remain in ignored local storage.

For separately collected complete recommendation lists, report **QualifiedDiscovery@10**: distinct items rated at least 2/3 on all four human dimensions and passing integrity checks, divided by ten requested slots. Missing human ratings remain unknown. Do not substitute automated grades into that metric or call a proxy score observed curiosity.

Normal voluntary exploration can later supply additional evidence without a dedicated trial. Searching or clicking alone is not knowledge, liking, or learning. Keep these signals distinct. Work on recommender evaluation documents why conventional accuracy alone does not establish usefulness. [McNee, Riedl and Konstan, 2006](https://grouplens.org/site-content/uploads/accurate-CHI-20061.pdf).
