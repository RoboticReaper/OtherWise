# Recommendation backend audit

Discovery audit, 2026-10-07. Production code, catalogs, dependencies, tests and services were left unchanged. Probes used public phrases, empty in-memory feedback and the existing offline MPNet cache. No private profiles, browser data or connection files were read.

The current system has three separable limits: title resolution changes the meaning and representation of an input; finite catalogs and area routing restrict available suggestions; the ranker optimizes a hand-chosen distance target rather than measured curiosity. Improving one does not establish improvement in the others.

## Observed catalog coverage

Counts below were computed from the current JSON files, not inferred from the README.

| Measure | Observed |
|---|---:|
| Broad topics / domains | 3,452 / 23 |
| Authored / Wikidata broad topics | 718 / 2,734 |
| Broad domains at the 160-topic cap | 18 |
| Smaller broad domains | Mind & behavior 77; Literature & storytelling 111; Philosophy 111; Home & crafts 121; Visual arts & design 152 |
| Graph unique concepts / areas / categories / edges | 3,642 / 69 / 319 / 3,919 |
| Graph domain assignments | 3,680: 160 per domain, with shared concepts stored once |
| Graph concepts with reviewed levels | 132 (3.6%); 3,510 have no level |
| Shared normalized broad/graph titles | 68 |
| Shared titles with different descriptions | 9 |
| Shared titles with conflicting non-null Wikidata IDs | 0 |
| Graph normalized duplicate titles | 0 |
| Graph concepts reachable at traversal depths 1 / 2 / 3 / 8 | 1,092 / 3,642 / 3,642 / 3,642 |

Sources: [catalog metadata](../data/catalog_metadata.json), [graph data](../data/discovery_graph.json), [graph_candidates:53](../graph_explorer.py), [balance_graph:247](../scripts/import_discovery_graph.py). The catalog notes' Philosophy 110 and Visual arts & design 153 are stale; current data and metadata agree on 111 and 152.

These are coverage and text-collision counts, not an adjudicated count of ambiguous meanings. Stripping parenthetical qualifiers creates four broad-title collisions: Go / Go (game), Fish / Fish (food), Good (economics) / good, Mode / Mode (music). Some represent distinct senses. The confirmed Go duplicate matters operationally below.

The broad importer starts from 7,777 guide candidates and a fixed domain cap. It excludes several subject classes, prioritizes foundational entries and rotates source subsections ([import_balanced_catalog.py:105](../scripts/import_balanced_catalog.py), [155](../scripts/import_balanced_catalog.py)). The public raw graph pool has 5,342 concepts; final balancing retains 3,642. The snapshot records 64 child-category caps and 95 article-candidate caps. Thus a complete bounded import still omits knowledge. Current enumeration uses the most recent category members, at most two 500-member pages, followed by reviewed preferences and stable hash sampling ([import_discovery_graph.py:137](../scripts/import_discovery_graph.py), [152](../scripts/import_discovery_graph.py), [398](../scripts/import_discovery_graph.py)). Balanced counts do not imply equal semantic coverage or equal useful-suggestion coverage.

## Input resolution and ranking failure modes

1. **Resolution is exact normalized-title lookup.** Normalization handles case, whitespace and hyphens, but provides no alias, plural, spelling or sense resolution. An exact title becomes `title: description`; any other phrase is embedded as written ([explorer.py:17](../explorer.py), [61](../explorer.py)). Java, Python, Mercury, Python snake, cozy gaming, LLM interpretability and causal representation learning have no exact broad title. This does not mean their subjects are absent: Python programming, Cozy games and Mercury (planet) are present; Mechanistic interpretability exists in the graph. Raw phrase versus contextual catalog text changes the representation as well as the wording.
2. **The same title can change context between endpoints.** Broad input uses the broad catalog; specific input uses broad + graph in that order, so a matching graph entry overwrites the broad description ([service/engine.py:169](../service/engine.py), [service/discovery.py:104](../service/discovery.py)). Fermentation means food transformation in the broad authored entry ([topics.json:67](../data/topics.json)) and anaerobic metabolism in the graph ([discovery_graph.json:13717](../data/discovery_graph.json)). Its first broad result was Food preservation; its first specific result was Thermogenesis. The other eight text changes are not automatically sense conflicts, but all can change vectors.
3. **Exact-title exclusion does not prevent semantic duplicates.** Exact Go is forced to the authored board-game context. The original broad ranker returns Go (game) first, at distance 0.3089, labeled New territory. Both catalog entries describe the same game ([topics.json:1788](../data/topics.json), [16911](../data/topics.json)). No shared canonical identity or alias exclusion connects them; the near-identical threshold is only 0.035 ([explorer.py:143](../explorer.py)).
4. **Area routing is an irreversible filter.** Specific discovery routes interest vectors plus up to 24 broad results to eight areas before considering final concept distances ([service/discovery.py:120](../service/discovery.py)). The round-robin exits once eight unique areas are chosen, so query order and earlier broad picks can determine which later queries receive a turn ([graph_explorer.py:90](../graph_explorer.py)). All available concepts outside those areas are excluded even if they satisfy the exact same band and ranker.
5. **Traversal explains provenance, not a conceptual bridge.** It follows observed category memberships and area allowlists, retaining one breadth-first path per concept per area ([graph_explorer.py:65](../graph_explorer.py)). The current graph is already fully reached by depth two, so increasing runtime depth alone supplies no additional concepts. Category membership does not encode prerequisites, useful next steps or an explanation of why this idea connects to the user's interest ([graph notes](../data/discovery_graph_README.md)).
6. **Ranking has no measured curiosity or usefulness objective.** Broad ranking peaks at the outward midpoint, then subtracts maximum positive cosine redundancy and adds jitter ([explorer.py:155](../explorer.py)). Specific ranking adds fixed curiosity, difficulty and area-variety weights ([graph_explorer.py:177](../graph_explorer.py)); most candidates cannot use difficulty matching because levels are unknown. Gardening's first specific result was Garden World Images, whose description is merely “horticultural image library.” This is a concrete candidate-type example, not proof that a user would dislike it. The service returns neither editorial hooks nor score components ([service/discovery.py:130](../service/discovery.py)), limiting what a user can judge beyond title, short description and source path.

**Path mode needs a clear product decision.** The general README and parameter guide define familiarity using every interest neighborhood ([README.md:118](../README.md), [parameter-guide.md:22](parameter-guide.md)). Extension architecture explicitly promises only exact-title / distance ≤0.035 protection against all approved interests, including path mode ([extension-architecture.md:188](extension-architecture.md)). Both service implementations then measure the band and New territory label against the focus alone ([service/engine.py:174](../service/engine.py), [service/discovery.py:106](../service/discovery.py)). A synthetic two-dimensional probe, using the original services, places a candidate 0.315 from focus and 0.085 from another saved interest: both path endpoints return it as New territory; both global endpoints exclude it. This matches the extension's documented near-identity protection but conflicts with an unconditional interpretation of the general all-neighborhood statement. It is not established here as an implementation bug.

## Real-model baseline and routing ablation

Both arms used identical resolved interest vectors, concept vectors and `recommend_specific` controls. The baseline is the original `DiscoveryEngine.recommend`; the ablation changes only `area_ids` to `None`, allowing all 69 areas. Settings: global mode, radius 0.28, expansion 0.07, overlap 0.015, limit 10, diversity 0.20, randomness 0, seed 42, exploration fraction 0.30, maximum familiar share 0.20, expansion level 0. Empty feedback and exposure dictionaries were used throughout.

“Eligible retained” counts **unique concept IDs** satisfying the original band and exact/near-identity exclusions before final ranking or overlap quotas. Recall is retained / full-graph eligible. “Common final” counts concepts shared by the two returned lists; it is separate from retrieval recall. A zero denominator is shown as —.

| Input | Broad returned | Eligible retained / all | Recall | Specific returned: routed / all | Common final |
|---|---:|---:|---:|---:|---:|
| Gardening | 10 | 17 / 19 | 89.5% | 10 / 10 | 8 |
| Python | 1 | 0 / 0 | — | 0 / 0 | 0 |
| Python snake | 3 | 0 / 1 | 0% | 0 / 1 | 0 |
| Python programming | 10 | 5 / 5 | 100% | 5 / 5 | 5 |
| Java | 7 | 2 / 2 | 100% | 2 / 2 | 2 |
| Java island | 7 | 1 / 1 | 100% | 1 / 1 | 1 |
| Java programming | 10 | 3 / 3 | 100% | 3 / 3 | 3 |
| Mercury | 1 | 0 / 0 | — | 0 / 0 | 0 |
| Mercury metal | 6 | 1 / 1 | 100% | 1 / 1 | 1 |
| Mercury planet | 5 | 0 / 0 | — | 0 / 0 | 0 |
| Fermentation | 10 | 3 / 3 | 100% | 2 / 2 | 2 |
| cozy gaming | 2 | 2 / 2 | 100% | 2 / 2 | 2 |
| LLM interpretability | 0 | 1 / 1 | 100% | 1 / 1 | 1 |
| causal representation learning | 1 | 0 / 2 | 0% | 0 / 2 | 0 |
| Python programming + Gardening | 10 | 22 / 24 | 91.7% | 10 / 10 | 8 |
| Go | 6 | 1 / 2 | 50% | 1 / 2 | 1 |
| Go programming | 5 | 1 / 1 | 100% | 1 / 1 | 1 |

Bare Python's sole broad suggestion is Python programming (0.3016), while Python snake gives Boidae, Chameleon and Snake. Bare Java's first broad suggestion is BASIC; Java island gives Island studies first. Mercury metal still returns Mercury (planet) in its broad list (0.3259), despite the explicit sense qualifier. These observations expose representation and sense problems; embedding distance alone does not verify sense correctness.

All-area retrieval recovers Infrared sensing in snakes (0.3355) for Python snake and Targeted maximum likelihood estimation (0.3383) plus Causal filter (0.3419) for causal representation learning. For Gardening and the mixed profile it adds Plant blindness and Sensory garden. These are candidate-recall gains only; no human labels establish a quality gain. An empty all-area result means this fixed catalog and band have no eligible concept, not that no useful idea exists. Fermentation's three eligible concepts yield two results under the familiar-overlap quota.

Raw public probe rows and settings are saved in [results.json](../experiments/recommendation-audit/results.json), including source-file and embedding-cache fingerprints. The reproduction code below is also saved at `/private/tmp/otherwise-recommendation-routing-probe.py` for this session; from the project root, run `PYTHONPATH=. HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1 .venv/bin/python -B /private/tmp/otherwise-recommendation-routing-probe.py`. The model was loaded directly from local snapshot `e8c3b32edf5434bc2275fc9bab85f82640a19130`, on CPU with deterministic PyTorch operations. Existing content/model-name-matched caches were used: broad `(3452, 768)`, concepts `(3642, 768)`, areas `(69, 768)`, all finite float64 arrays. The cache identity includes model name and input texts, not a pinned model revision ([service/engine.py:63](../service/engine.py), [service/discovery.py:26](../service/discovery.py)).

## Separable experiments

| Change to isolate | Controlled comparison | Diagnostic and outcome needed |
|---|---|---|
| Input resolution | Current lookup vs consistent canonical sense/alias resolution; keep model, pool and ranking fixed | Resolve the Python/Java/Mercury pairs correctly; suppress the Go duplicate. Human confirmation of intended meaning is the reference. |
| Candidate retrieval | Eight areas vs all areas vs eight plus a global candidate reserve; keep input vectors and ranker fixed | Full-pool eligible recall, empty-list frequency, latency and final overlap; then judge recovered candidates for connection, unfamiliarity and curiosity. |
| Catalog coverage | Current pool vs a separately sourced expanded pool; hold resolver and ranker fixed | Held-out niche-input coverage and source quality. More candidates or balanced counts alone do not prove better recommendations. |
| Ranking and distance controls | Current midpoint fit vs nearest-neighbor baseline and separately calibrated novelty preference; keep resolver and candidate pool fixed | Per-user unfamiliarity, understandable connection and desire to explore, plus redundant/familiar/sense-mismatched results. Preserve the ability to tune distance; do not treat 0.28 as a measured knowledge boundary. |

Existing tests chiefly validate geometry, contracts, balance, feedback and provenance ([test_explorer.py:24](../tests/test_explorer.py), [test_graph_balance.py:12](../tests/test_graph_balance.py), [test_discovery_service.py:31](../tests/test_discovery_service.py)). They do not label suggestion quality. The real-model test is opt-in and checks band/source/known exclusion, rather than curiosity. No algorithm is declared best from these unlabeled diagnostics.

## Reproduce the routing counts

Run from the project root. This reads only public catalogs, the public model and public embedding arrays; injected arrays prevent service initialization from writing caches. It prints the original top ten and the all-area top ten with unique IDs.

```sh
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1 .venv/bin/python -B - <<'PY'
from pathlib import Path
import hashlib, json
import numpy as np, torch
from sentence_transformers import SentenceTransformer
from explorer import MODEL_NAME, _key, _unit_vectors, load_catalog, topic_texts, interest_texts, recommend, score_catalog
from graph_explorer import load_graph, graph_concepts, graph_candidates, recommend_specific, select_areas
from service.engine import RecommendationEngine
from service.discovery import DiscoveryEngine
from feedback import new_profile

root = Path.cwd()
torch.set_num_threads(4)
torch.use_deterministic_algorithms(True)
model = SentenceTransformer(str(root / '.cache/models/models--sentence-transformers--all-mpnet-base-v2/snapshots/e8c3b32edf5434bc2275fc9bab85f82640a19130'), device='cpu', local_files_only=True)
b, g = load_catalog(), load_graph()
c = graph_concepts(g)
def cached(rows, prefix=''):
    identity = json.dumps({'model': MODEL_NAME, 'texts': topic_texts(rows)}, ensure_ascii=False, sort_keys=True).encode()
    path = root / '.cache/embeddings' / f'{prefix}{hashlib.sha256(identity).hexdigest()}.npy'
    return _unit_vectors(np.load(path, allow_pickle=False), 'Public cache')
bv, cv, av = cached(b), cached(c, 'discovery-'), cached(g['areas'], 'discovery-')
profiles = [[p] for p in ['Gardening', 'Python', 'Python snake', 'Python programming', 'Java', 'Java island', 'Java programming', 'Mercury', 'Mercury metal', 'Mercury planet', 'Fermentation', 'cozy gaming', 'LLM interpretability', 'causal representation learning', 'Go', 'Go programming']]
profiles.append(['Python programming', 'Gardening'])
phrases = list(dict.fromkeys(p for profile in profiles for p in profile))
texts = list(dict.fromkeys(interest_texts(phrases, b) + interest_texts(phrases, b + c)))
encoded = dict(zip(texts, model.encode(texts, batch_size=32, show_progress_bar=False, convert_to_numpy=True, normalize_embeddings=True)))
class PublicInputs:
    def encode(self, texts, **kwargs):
        return np.asarray([encoded[text] for text in texts])
e = RecommendationEngine(topics=b, model=PublicInputs(), topic_vectors=bv)
e.initialize()
d = DiscoveryEngine(e, graph=g, concept_vectors=cv, area_vectors=av)
d.initialize()
opts = dict(radius=.28, expansion=.07, overlap=.015, diversity=.2, randomness=0, max_overlap_fraction=.2)
for interests in profiles:
    seeds = _unit_vectors(e.model.encode(interest_texts(interests, b + c)), 'Seeds')
    routed = d.recommend(interests, mode='global', focus=None, expansion_level=0, limit=10, feedback=[], exposures={}, seed=42, exploration_fraction=.3, **opts)['recommendations']
    broad = recommend(b, bv, interests, seeds, top_k=24, **opts)
    queries = np.vstack([seeds] + ([bv[[r['catalog_index'] for r in broad]]] if broad else []))
    areas = select_areas(g['areas'], av, queries, limit=8)
    reached = {r['id'] for r in graph_candidates(g, areas)}
    keys = {_key(p) for p in interests}
    eligible = [r for r in score_catalog(c, cv, interests, seeds) if .265-1e-9 <= r['distance'] <= .35+1e-9 and r['distance'] > .035 and _key(r['topic']) not in keys]
    retained = sum(r['id'] in reached for r in eligible)
    all_rows = recommend_specific(g, cv, interests, seeds, area_ids=None, profile=new_profile(), top_k=10, seed=42, exploration_fraction=.3, **opts)
    routed_ids = {r['discovery']['concept_id'] for r in routed}
    all_ids = {r['id'] for r in all_rows}
    print(json.dumps(dict(interests=interests, eligible_all=len(eligible), eligible_routed=retained, recall=retained/len(eligible) if eligible else None, common_final=len(routed_ids & all_ids), routed=[(r['discovery']['concept_id'], r['topic']) for r in routed], all_area=[(r['id'], r['topic']) for r in all_rows]), ensure_ascii=False))
PY
```
