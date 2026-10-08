# Galaxy layout preview — temporary experiment

Question: how should OtherWise display all 31,637 topics without the dense, oversized star cloud? The user's next step is to choose A, B, C, or a combination. None of these layouts is installed in the extension; this experiment writes only this folder and cached projection results.

Open `preview.html` directly in a browser (self-contained, offline), or serve this directory and open `/preview.html?compare=1`. `?variant=A`, `B`, `C`, and `current` open a particular variant. The switch bar and left/right arrow keys change variants. Search, domain filtering, pan, zoom, topic details, and original-vector neighbors work with the complete real catalog. Controls have no persistence and call no backend.

A uses 60 neighbors, min_dist 0.70, spread 1.0, repulsion 2.0, and 5% domain anchoring: a continuous cloud with lighter stars. B uses 12 neighbors, min_dist 0.40, spread 1.5, repulsion 2.5, and no domain anchoring: local semantic islands with a domain navigation rail. Both recompute UMAP with seed 42, random initialization, 300 epochs, exact angular neighborhoods, and the current cached MPNet 768-dimensional vectors. C partitions proportional rectangles for the 23 domains and gives every topic a distinct grid slot, ordered within each domain using A; its global distances are determined by typography and grouping, not semantic similarity. Current uses the production asset's original positions unchanged.

The original ten neighbors and descriptions are identical in every variant. Catalog digest, vector-byte digest, topic ordering, seed, and numerical versions are recorded/verified in the generator and embedded preview provenance. No private browser history, tokens, or personal state are embedded.

Rebuild in this workspace:

```sh
.venv/bin/python experiments/galaxy-layout-options/run_preview.py
```

The generator uses numerical dependencies in `.cache/galaxy-prototype-deps` if available, otherwise the environment's installed packages. The first run computes exact 59-neighbor arrays and two UMAP projections; subsequent runs reuse caches. Runtime production settings and assets are not changed.

Measurements in `summary.json` compare the same topic population on an idealized 1100×720 canvas, using the same 0.8 px point radius and 82% fit. “Overlap” is the percentage whose nearest other point lies less than 1.6 px away; it is a display-density proxy, not a semantic-quality score. Current 88.6%, A 84.4%, B 87.9%, C 0.0%. A/B's visual improvements also depend on smaller dots and greater canvas space. Increasing UMAP min_dist alone does not make 31,637 dots collision-free after viewport fitting. `neighbor_retention` is the mean overlap of the ten nearest projected points with the ten true original-vector neighbors: current 12.0%, A 8.2%, B 26.1%, C 7.8%. This single local metric does not establish global semantic fidelity or recommendation quality.

Read-only browser smoke validation covers all four variants, count 31,637, real Sushi search and ten original neighbors, Biology & nature filtering (4,328), locked point size, arrow shortcuts without interrupting text input, and 390 px mobile width. Screenshots are under `.cache/qa/galaxy-options/`.

After selection, implement the chosen behavior in the real Galaxy modules and regenerate production assets with their normal version/cache validation. Do not promote this standalone preview wholesale.
