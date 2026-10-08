# Recommendation lab

This package runs the recommendation systems without changing the production API or map. Public synthetic benchmark profiles use the five requested interest groups. Personal pilot ratings stay in ignored `.local/` storage.

The controls are V0 (original routing), V1 (every graph area), and V2 (identities/meaning choices). V3 adds semantic/BM25/graph reciprocal-rank fusion and explicit ranking components. Three ablations remove lexical search, graph signals, or the new ranker. V3-adaptive is a separate experiment using angular distance 0.08–0.55 instead of the requested hard band; it is not an implicit slider change. Ranking configurations in `systems.json` vary one serving policy at a time. V4b is an optional adapter contract; no paid provider is configured.

The local model must already exist in `.cache/models/`. The runner uses the pinned MPNet revision, full vectors, CPU deterministic inference, and revision-aware public caches. It does not download a model or persist personal request embeddings. First-run public cache migration requires matching catalog, model revision, and audited embedding file hashes. Model initialization and request encoding are reported separately from warm runs.

Run a fresh development comparison:

```sh
.venv/bin/python -m recommendation_lab run --out .local/recommendation-cycle/development
```

`packet.json` contains randomized, deduplicated, method-blind candidate records. The evaluator selected by the user is the session assistant. Grades are explicit C/N/E/A judgments with a bridge and reason, not conversions of embedding distance. Unknown background gives A=null and a disclosed neutral score. The rubric/prompt/evaluator and exact profile/presentation bind every grade. Algorithm names, ranking components, and timings are absent from the grading packet; the assistant implementing the systems retains session context, so this is weaker blinding than a fresh independent judge.

A ratings file contains the packet's `packet_id` and `evaluator` unchanged, plus `ratings`: records with `key`, `C`, `N`, `E`, `A`, `bridge`, and `reason`. C/N/E/A are integers 0–3; only A may be null. Import and compare:

```sh
.venv/bin/python -m recommendation_lab compare \
  --run .local/recommendation-cycle/development \
  --ratings .local/recommendation-cycle/development/ratings.json
.venv/bin/python -m recommendation_lab tune \
  --run .local/recommendation-cycle/development \
  --cycle .local/recommendation-cycle
.venv/bin/python -m recommendation_lab run --split heldout \
  --cycle .local/recommendation-cycle \
  --out .local/recommendation-cycle/heldout
```

Grade the held-out packet and run `compare` with its ratings. Nomination locks the source/model/evaluator/code/split/config identities. A cycle claims held-out data once; create fresh held-out families before using those results for later tuning. The bounded search accepts development cases only, at most five rounds of twenty configurations, and stops after two rounds without a 0.01 gain. Unrated new candidate content cannot produce a champion. To extend experiments, add candidate configurations, run them, grade only new profile/content keys, and start a new sealed cycle. The CLI does not schedule recurring jobs or deploy anything.

Connection, discovery, depth, and relevant variety are scored separately with requested slots as denominator. Empty slots count zero; missing grades make a score unavailable. Shared gates reject known identities, duplicates, unsupported source records, and C<2. Broad and specific universes have separate scoreboards. Variety uses a separately frozen hashed TF-IDF embedding space, measuring lexical rather than full semantic diversity. Serving rankers never read grades.

The result artifacts include manifests, raw outputs, structural diagnostics, item grades, per-profile scores, cross-metric comparisons, proxy champions, latency/cost Pareto data, and bootstrap uncertainty. Scores describe a single declared assistant rubric. Real curiosity/familiarity, second-judge agreement, sensitivity audits, and production rollout require separate evidence. Do not call an experimental winner a proven personal preference.

Inventory aliases/equivalences are in `data/recommendation-identities.json`. Resolver-only additions do not expand recommendation candidates. Authored local IDs are registered source slots: label edits retain identity; reordering/deleting these records requires an explicit registry migration. Multiple labels/descriptions are preserved; shared labels never merge distinct meanings. Context orders choices but does not auto-resolve ambiguous interests.

Python usage:

```python
from recommendation_lab.benchmark import load_runtime
from recommendation_lab.systems import Request

lab, evaluation_vectors, manifest = load_runtime()
batch = lab.recommend(Request(["computers", "soccer"]), "V3")
# For an ambiguous phrase, inspect batch['resolutions']; resubmit a chosen ID
# with inventory_version=batch['inventory_version'].
```

External reranking accepts at most 30 source-backed results and 20,000 characters. The caller enforces a maximum 20-second wait within the remaining 30-second request budget and allows one worker per lab. Its adapter owns cancellation of underlying network operations and must return an exact ID permutation. A noncooperative adapter occupies that bounded worker until it exits; later calls return a local busy fallback. Invalid output, unavailable configuration, or provider failure retains the local order with a recorded fallback. The experiment package is not an authenticated HTTP service; V2 API/client integration remains a later stage after operational selection.
