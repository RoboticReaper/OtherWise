# Interest Galaxy: feasibility prototype

**Throwaway experiment on `codex/interest-galaxy-validation`.** It tests whether the existing 768-dimensional embeddings can support a Galaxy with approximate domain directions and a CS → Psychology exploration corridor. It does not change the extension, API, catalog or production recommendation rules.

Open `preview.html` in a browser. It is self-contained and works without a server or network access. The preview contains four exploration pairs, three local methods, seven global layouts, searchable topics, domain filtering, zoom/pan and the original high-dimensional neighbors of a selected topic. External source links open only when clicked.

## What the experiment found

- Directional exploration is feasible, but the original vectors alone did not reliably discover the requested bridge. HCI was **51st of 3,452 topics** under original midpoint retrieval.
- Authoring fuller CS/Psychology profiles and a question about human behavior, cognition and computing moved HCI to **7th**. Its original catalog description was unchanged.
- Replacing only HCI's description with an explicitly interdisciplinary description moved it to **1st**. The description is a paraphrase grounded in the [ACM HCI curriculum](https://csed.acm.org/knowledge-areas-human-computer-interaction-hci-cs2013-version/). This is a manually improved known example, not evidence of automatic discovery or held-out generalization.
- With that description, the generic two-waypoint rule selected **Computer science → Human-computer interaction → Cognitive psychology → psychology**. No HCI coordinate or mandatory route membership was inserted into the algorithm.
- More context did not improve every example: CS → Music still produced a questionable Information science → Musicology corridor. The full outcomes are retained.
- The current catalog does not contain exact entries for Interaction design, Design psychology, Cognitive science or Ergonomics. A layout cannot reveal a missing topic.

## Global layout comparison

All global layouts use the **original catalog vectors**, including HCI's original description. Coordinates and relative distances in 2D remain approximate.

| Layout | Original top-10 neighbors retained | Trustworthiness, 800-topic sample | Global distance Spearman correlation |
|---|---:|---:|---:|
| PCA | 3.02% | 0.714 | 0.327 |
| Spectral nearest-neighbor graph | 12.06% | 0.788 | 0.301 |
| UMAP | 31.70% | 0.893 | 0.286 |
| UMAP + 15% domain anchors | 27.08% | 0.879 | 0.282 |
| UMAP + 35% domain anchors | 20.61% | 0.849 | 0.275 |
| UMAP + 65% domain anchors | 15.47% | 0.815 | 0.265 |
| Domain anchors only | 10.21% | 0.833 | 0.259 |

PCA's first two components retain 6.48% of embedding variance. UMAP preserves more nearby topics, but its global distance correlation is lower than PCA's. Adding stronger domain anchors further reduces local neighbor retention. The default is the modest **15% blend**, chosen after reviewing this tradeoff, not because it is a proven optimum. Directions are interpretable approximations; even this default loses most of each topic's original top-10 neighbors.

## Method and provenance

- Read the existing cache only after matching the service's SHA-256 identity of model name plus the exact catalog texts. Input shape is 3,452 × 768.
- Use the existing service metric: `acos(cosine similarity) / pi` on normalized embeddings.
- Build a symmetric graph with 15 neighbors per topic. The graph has one connected component. The graph-path control uses angular edge costs, not screen coordinates.
- UMAP uses the original angular distance matrix, `n_neighbors=30`, `min_dist=0.15`, two dimensions and seed 42.
- Form 23 domain prototypes by averaging and normalizing each domain's original vectors. Fit their 2D positions using metric MDS. Each topic gets a weighted target from its three closest domain prototypes. Align UMAP and PCA with those targets before blending.
- This anchor blend is a simple experimental heuristic, not a constrained optimizer. Broad domain averages and single-domain catalog labels are imperfect representations of interdisciplinary topics.
- In local exploration, horizontal position is the projection onto the selected high-dimensional difference vector. Vertical position is PCA of residual vectors among 100 retrieved neighbors; its sign is arbitrary and has no named semantic meaning. With contextual profiles, the actual catalog endpoints need not lie at exactly 0 and 1.
- Raw retrieval uses the normalized endpoint midpoint. Contextual retrieval combines 45% bridge-query similarity, 35% lower endpoint similarity and 20% average endpoint similarity. All authored profiles and query texts are exposed in the preview and results.
- The route rule selects two different candidates near direction positions 0.3 and 0.7, within 0.22, with both endpoint similarities at least 0.28, and a position penalty of 0.45. These are uncalibrated experimental choices. Missing waypoints stay missing. Waypoints are not prerequisites or validated academic relationships.
- Neighbor retention compares full-catalog top-10 lists, so both original and visual lists include all 3,452 topics. Trustworthiness uses a fixed random 800-topic subset with `k=10`; original neighborhoods for that metric are computed within that subset. Global correlation samples up to 50,000 random non-self pairs. These are geometric measurements, not measures of semantic correctness.

## Re-run locally

The original project `.venv`, catalog embedding cache and downloaded model weights must already exist. In this workspace, they are reused without changing the application's dependencies. Install the four optional experiment packages into a separate ignored directory:

```sh
.venv/bin/python -m pip install --target .cache/galaxy-prototype-deps --no-deps -r experiments/interest-galaxy-prototype/requirements-prototype.txt
.venv/bin/python experiments/interest-galaxy-prototype/run_probe.py
```

The generator disables model downloads and uses CPU inference. The original numerical environment was Python 3.13, numpy 2.5.3, scipy 1.18.1, scikit-learn 1.9.1 and sentence-transformers 5.7.0; optional versions are pinned above. Results can vary slightly on other versions/platforms.

Outputs: `preview.html` is the shareable preview; `results.json` holds coordinates, catalog content and numerical evidence; `summary.json` holds metrics, routes and descriptions; `preview.template.html` is the editable shell.

## Validation and next decision

Existing project baseline: **193 Python tests and 69 JavaScript tests passed** with a suitable Node runtime and the required process-read permission. The prototype browser checks covered raw/context/enriched ranks, all four pairs, all seven layouts, search, selection, filtering, reset, no JavaScript errors, and no horizontal page overflow at 320 and 390 pixels. Desktop and narrow-screen screenshots were inspected.

**Recommendation:** a stable UMAP map with light domain guidance plus an explicitly separate local directional view is worth pursuing. A fuller, source-backed multi-domain topic catalog is necessary for dependable bridge discovery. Before production, validate multiple held-out domain pairs with human judgments and tune retrieval/route thresholds against those judgments. This prototype does not establish that arbitrary domain pairs will yield meaningful routes.
