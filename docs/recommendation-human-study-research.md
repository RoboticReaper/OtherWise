# Research: human evaluation of connected discovery

Checked 2026-10-08. This note distinguishes published findings from a proposed OtherWise study. It does not establish a winning system or a required participant count. The later authorized backend implementation is recorded below; no participant study or production-default change is made here.

## Saved direction for a later chat

On 2026-10-08, the user agreed to blind comparisons plus controlled variants for future formal human-participant research. Formalizing the experimental design is deferred to a new chat. For now, discuss feasible options and candidate roles; do not build an experiment, recruit participants, or treat the proposals below as an approved protocol.

The user clarified that the mission is to broaden the topics a person comes to care about. Immediate curiosity and preference are intermediate signals; the main outcome should concern acquired, sustained interests. This supersedes treating the most appealing suggestion as the goal. The measurements below are proposals to formalize later.

## Candidate systems and baselines for discussion

The proposed compact comparison contains two existing experimental candidates and two baselines, with an additional history-dependent hypothesis candidate:

| System | Role | Reason to consider it | Status |
|---|---|---|---|
| K-connection | Static experimental candidate | Highest observed specific-concept proxy scores; broader eligibility with relevance-oriented hybrid retrieval/ranking; expansion effectiveness unmeasured | Implemented and benchmarked |
| V3 | Alternative experimental candidate | Semantic, lexical and graph fusion with the original strict distance band | Implemented and benchmarked |
| Original V0 | Historical baseline | Tests improvement over the original routed, distance-band pipeline | Implemented frozen reference |
| Semantic nearest neighbors | Simple content-based baseline | Tests whether the additional retrieval/ranking machinery improves on selecting the closest distinct concepts | Implemented and backend-selectable; quality/expansion effects unevaluated |
| Trajectory-guided expansion | Additional hypothesis candidate | Uses interest history to propose plausible next steps and branches beyond established interests | Implemented with a matched recency-only control; expansion effects unevaluated |

For the simple baseline, reuse the shared inventory, embedding model, sense resolution and explicit known/duplicate exclusions, then rank by canonical semantic similarity. Its distance eligibility policy must be declared when the design is formalized. Preserve the original V0 implementation as the historical comparator; silently fixing its resolver or eligibility would create a different baseline.

K-literal remains a reasonable optional candidate if broad-topic discovery or literal-query emphasis is part of the research question. It had the highest observed broad discovery score, with a small advantage over K-connection, and shares the V5-known implementation. Its configuration also changes content, novelty and diversity weights, so comparison with K-connection cannot isolate literal-query weighting. Keep broad-topic and specific-concept tracks separate. [Frozen shortlist](../experiments/recommendation-benchmark/cycle-002/shortlist.json).

A standalone BM25/keyword baseline is useful if the question concerns semantic versus lexical retrieval. Random selection can provide a sanity check, but a claim of improvement should also face a competitive simple baseline. Existing V1/V2 intermediates and V3 channel ablations can support later component questions without all becoming human-study arms. V4b remains an unconfigured external-reranking adapter, not an independently evaluated external-model candidate.

The user subsequently authorized implementing the candidates and specified optional `date` on each interest. These candidates, BM25, seeded random and `history-recency` are now selectable through the [backend model API](recommendation-model-api.md). Readiness is reported per model; this implementation does not launch or formalize a participant study. Historical benchmark results remain separate from the new executable models.

The raw lab V0 remains the historical reference. Its selected-model API wrapper uses disclosed meaning and known-output guards, with a separate algorithm identity. A future study must name the exact version used rather than treating the guarded wrapper as the unchanged historical pipeline.

The importance of competitive simple baselines is supported by recommendation-method research; this motivates the proposed semantic baseline without predicting its human-study result. [Ferrari Dacrema, Cremonesi and Jannach, 2019](https://arxiv.org/abs/1907.06902).

The current systems differ in several components. To identify the effect of exploration distance, description content or a retrieval channel, use variants of one shared pipeline that change only the named component. A whole-system comparison answers overall effectiveness. For ranking comparisons, each concept should use the same frozen description across systems; description enrichment is a separate treatment. The personal blind test did not establish a consistent content-preference winner. Neither it nor the proxy benchmark measured sustained interest expansion, exploration pace or trajectories. Private participant evidence stays in ignored local storage.

**Recommendation:** retain blind comparisons plus controlled variants to screen suggestions and investigate mechanisms. Every occurrence of the same concept uses the same card across systems; different concepts still need their own explanations. Test description enrichment separately. Evaluating retained interest expansion requires longitudinal follow-up and comparison against baseline systems under comparable opportunities. Blinding limits expectations about named systems; it does not remove differences in their outputs or substitute for randomization. This is a design proposal, not an approved participant protocol.

## What question does the experiment answer?

Shani and Gunawardana distinguish offline evaluation, controlled user studies, and online experiments. They recommend choosing the application property and hypothesis first, keeping unrelated variables fixed, and addressing generalization. They also discuss within- versus between-participant designs and order/location counterbalancing. These are complementary tools, not one universally best experiment. [Shani and Gunawardana, *Evaluating Recommendation Systems*](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/EvaluationMetrics.TR_.pdf).

The existing original/V0 and K-connection implementations differ in resolution, retrieval, eligibility, and ranking. A direct comparison therefore estimates the effect of those complete configurations. It cannot identify whether distance, lexical retrieval, coverage, or ranking caused a difference. [Implementation](../recommendation_lab/systems.py), [known-concept policy](../recommendation_lab/known_policy.py), [saved shortlist](../experiments/recommendation-benchmark/cycle-002/shortlist.json).

**Proposed studies:**

| Research question | Randomized comparison | Held constant | Interpretation |
|---|---|---|---|
| Which recommendation pipeline broadens retained interests? | Frozen candidates and baselines above, with longitudinal follow-up | Catalog snapshot, available interest/context/feedback, description renderer, requested list size, interface and time budget | A pipeline comparison; several mechanisms may contribute |
| Do enriched descriptions help people understand and choose concepts? | Existing versus enriched description for the same concept, allocated across participants | Concept identity, interest context, placement, source material for subsequent exploration | A presentation effect, independent of recommendation selection |
| Does a different exploration policy help? | Closely connected, adjacent, and wider exploration policies within one pipeline | Resolver, candidate catalog, lexical/semantic retrieval, content features, descriptions | A policy effect, with the actual distance distribution and perceived connection checked |
| Does a policy change exploration over time? | Persistent participant-level assignment to frozen policies | Interface, exposure opportunities, description and content access | An effect over the stated observation period; not a lifetime personality trait |

For the description experiment, each participant sees only one version of each concept. A participant may see different versions for different concepts, with balanced assignments. Showing both versions sequentially would confound the second rating with prior exposure. If word count differs, the treatment is the complete enrichment package, including additional information; a separate length-matched treatment is needed to isolate writing quality alone. A strategy-by-description factorial can test interaction effects, but requires its own power justification.

Explanation research distinguishes helping people make good decisions from persuading them, and reports that satisfaction and effectiveness can diverge. Thus a more enticing card is not sufficient evidence of better discovery. [Tintarev and Masthoff, 2012](https://link.springer.com/article/10.1007/s11257-011-9117-5).

## Proposed measurements

Before recommendation exposure, participants supply their own interests, intended meanings and relevant context. Establish prior care separately from concept familiarity, before explanatory text reveals its substance, and retain an uncertain option. Someone can recognize a topic without caring about it; interest in a broad field does not establish knowledge of, or interest in, every concept within it.

These are proposed OtherWise outcomes, not validated instruments or finalized endpoints:

| Measure | Proposed operational meaning |
|---|---|
| Retained new-interest acquisition, candidate primary outcome | Distinct topics not endorsed as interests at baseline that become endorsed and meet a declared follow-up criterion for continued care or voluntary re-exploration, per equal recommendation opportunity |
| Breadth of retained interests | Change in coverage of fixed semantic regions or a domain taxonomy defined independently of ranking; calculate from retained interests and report gains and losses |
| Adopted-topic distance, secondary diagnostic | Distribution of each retained new topic's distance to its nearest starting interest in a frozen independent representation; report alongside acquisition and breadth, not as success alone |

Declare topic granularity, endorsement/retention criteria, opportunity denominators and follow-up/missing-data handling later. Distinguish additional depth within a field from broader coverage. Count no extra success for aliases, tiny subdivisions or repeatedly presenting the same topic. A distant topic that nobody comes to care about contributes no acquired-interest success. Baseline-to-follow-up growth alone cannot establish a system's effect because interests can change elsewhere; compare growth across assigned systems.

Selection for optional exploration remains an intermediate endpoint. Record offered diversity, exposure, clicks and curiosity separately from adoption and retention. Source correctness and wrong-sense failures remain separate outcomes. Nguyen and colleagues measured recommended and consumed movie diversity longitudinally using content features independent of the recommender. This supports separating exposure from subsequent behavior, but their observational MovieLens analysis neither demonstrates causal topic-interest expansion nor validates the proposed OtherWise measures. [Nguyen et al., 2014](https://archives.iw3c2.org/www2014/proceedings/proceedings/p677.pdf).

Record curiosity, perceived connection, familiarity, description clarity, and expected accessibility separately. Follow the chosen exploration with experienced interest and a short comprehension check if learning is part of the research claim. A participant can understand an explanation and still dislike the topic. Relative preference is a useful secondary endpoint, with ties and “none” allowed: the best of three weak options is not necessarily good.

Knijnenburg and colleagues separate system properties, perceived qualities, experience, behavior, and personal/situational characteristics. Their framework supports combining self-report with behavior rather than treating clicks, geometric diversity or perceived novelty as interchangeable outcomes. [Knijnenburg et al., 2012](https://pure.tue.nl/ws/portalfiles/portal/3484177/724656348730405.pdf). ResQue offers a complementary questionnaire framework for user experience; adapting questionnaire items to educational discovery requires checking their interpretation rather than assuming the adapted instrument remains validated. [Pu, Chen and Hu, 2011](https://www.comp.hkbu.edu.hk/~lichen/download/p157-pu.pdf).

## Trajectory-guided expansion hypothesis

Direction and velocity in embedding space are a reasonable additional candidate. JODIE learns user/item embedding trajectories from timestamped interactions and projects future embeddings to predict interactions. Its evaluation concerns interaction/state prediction, not expansion of topics users care about; it is a modeling precedent rather than evidence this candidate will broaden interests. [Kumar, Zhang and Leskovec, 2019](https://cs.stanford.edu/~srijan/pubs/jodie-kdd2019.pdf).

For OtherWise, estimate recent direction from timestamped, user-confirmed interest signals, with separate strands for different interests. A switch from soccer to computers should not automatically become a movement vector between them. Use stable embedding coordinates and source text over the observation window; embedding or description changes are not user movement. Velocity requires a declared time/event unit. Smooth noisy signals, express uncertainty and fall back to a static policy when history is insufficient, without presuming a universal minimum history size.

A forecast alone may continue an increasingly narrow thread. The proposed expansion variant should combine plausible next steps with connected branches outside already established interests, using user-tunable exploration. Compare it with static K-connection and the semantic-neighbor relevance baseline. Within a shared history-aware pipeline, compare recency-only history weighting with ordered direction/velocity. Disable the velocity feature while retaining the same recency-weighted profile, retrieval, expansion policy and descriptions. Shuffling history order is a separate sensitivity check because it can also change recency. Next-interaction prediction and retained-interest expansion should remain separate outcomes.

## Assignment, presentation and missing outputs

For an early discovery-choice study, participant-request randomization within balanced blocks is an option. Generate and freeze all arms' outputs from the same input before display. Each request shows one system's list so that seeing a competitor first does not change concept familiarity before the action. Balance systems across participants, topic blocks and session positions. For retained-interest expansion, consider persistent participant-level assignment instead: recommendations can change later interests and history, making carryover part of the outcome. Log repeated concept exposure and predeclare first-exposure and later-exposure analyses. Shared common-interest blocks can complement personalized requests, with the target population and generalization scope declared.

A separate pairwise or three-way blind comparison can efficiently collect relative preferences. Use identical cards for identical concepts, randomize display positions, counterbalance comparison order, and preserve genuine ties and duplicate outputs. Sample ranks or compare fixed-length lists according to a predefined protocol. An individual sampled recommendation estimates a different outcome from a full list's diversity, redundancy and usability. Hide model names and the favored hypothesis; describe this as participant/strategy-blind unless experimenter and analysis blinding are also implemented.

Predeclare treatment of missing slots, errors, all-identical outputs and abstentions. Do not replace a weak or missing result with a handpicked alternative. Retain availability failures in the assigned-opportunity denominator when measuring acquisition. A secondary comparison conditional on all systems having outputs is informative, but changes the question and can introduce selection bias. The requested list size stays fixed, while actual returned length remains an observed system outcome.

## Analysis, pilot and claims

Freeze configurations, seeds, catalog, generated descriptions and analysis rules before confirmatory collection. Preregister one primary endpoint, the main contrasts, exclusions, tie/missing-data rules and stopping rule. Keep exploratory subgroup or distance analyses clearly separate. Do not improve the model on a participant's final judgments and then report those same judgments as unseen evaluation.

Repeated ratings are not independent participants. Use an outcome-appropriate multilevel analysis accounting for participant and, where shared stimuli permit, topic/concept variation and repeated sessions. Specify treatment variation and random effects from the assignment design; report effect estimates and uncertainty. A participant-clustered analysis supports participant-level inference but does not automatically support generalization to new topics. [Barr et al., 2013](https://www.mit.edu/~rplevy/papers/barr-etal-2013-jml.pdf).

Use a separate pilot to test instructions, fatigue, timing, familiarity questions and output handling. Estimate variance/dependence with uncertainty; do not take a small pilot's winner or effect size as guaranteed. Justify the final sample size with a smallest meaningful difference, a chosen power or precision goal, expected attrition, planned comparisons and participant/topic clustering. Simulation can reflect this assignment design. Many judgments from one person cannot replace a sufficient participant sample. [Lakens, 2022](https://doi.org/10.1525/collabra.33267).

For an expansion-rate claim, preregister a duration and measure retained new interests per exposure opportunity or active session, with breadth and repeated-session trajectories. Pair these with baseline care and familiarity; time-on-page alone can also reflect confusion. Persistent assignment is preferable to rapid switching when prior exposure changes knowledge and later recommendations. A short blind preference test can nominate candidates, but cannot measure sustained expansion, exploration speed or prove that a fixed semantic distance band is appropriate.
