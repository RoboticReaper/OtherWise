# Whole-catalog galaxy preprocessing

The extension reads `data/galaxy-layout.json`; map interaction never runs UMAP,
encodes text, or changes recommendation ranking. `data/topics.json` remains the
authority for literal topic titles, domains, descriptions and sources. The layout
contains public geometry and neighbor IDs only, with no interests, visits, paths,
profile data, user settings, filesystem paths, or authored description overlays.

## Build

Use Python 3.13 and the pinned numerical packages for reproduction of this asset:

```sh
python3.13 -m venv .venv-layout
.venv-layout/bin/python -m pip install -r requirements-layout.txt
.venv-layout/bin/python scripts/build_galaxy.py
```

The command reads the original catalog embedding cache from `.cache/embeddings`.
The expected `.npy` filename uses the existing service's SHA-256 key of its model
name and unchanged `"topic: description"` texts in catalog order. No model is
loaded on this path. A missing input fails without publishing an output.

If the original embedding cache does not exist, install the ordinary project
requirements in the same environment and explicitly request original-text encoding:

```sh
.venv-layout/bin/python -m pip install -r requirements.txt
.venv-layout/bin/python scripts/build_galaxy.py --encode-missing
```

This uses `sentence-transformers/all-mpnet-base-v2` on CPU, can download its model
when not already cached, and atomically saves the original normalized 768D vectors.
There is no enrichment step. `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1` can be set
when local model weights are already available and an offline build is desired.

Available path options are `--catalog`, `--embeddings-dir`, `--cache-dir` and
`--output`. Defaults are `data/topics.json`, `.cache/embeddings`, `.cache/galaxy`,
and `data/galaxy-layout.json` relative to the repository. For a fresh reproducibility
check, use a new `--cache-dir` and a separate `--output`; a verified cache hit skips
all projection and pairwise-neighbor computation. JSON stdout reports `cache_hit`,
`elapsed_seconds`, counts, output and cache key.

## Geometry and IDs

1. Load and normalize the original 768D MPNet vectors using float64 arithmetic.
2. Compute angular distances as `acos(clip(cosine, -1, 1)) / pi`, setting the
   diagonal to zero. Select ten other topics per row, sorted by this original
   distance, then literal topic title to resolve ties.
3. Fit UMAP to that precomputed matrix: two dimensions, 30 neighbors,
   `min_dist=0.15`, random seed 42, one job.
4. Average vectors within each literal catalog domain and normalize those means.
   Domain order is sorted by literal name. Fit metric MDS to domain angular
   distances: two dimensions, random seed 42, one initialization, at most 500
   iterations, epsilon `1e-7`. Center and scale the anchors to unit RMS radius.
5. Each topic's target is the weighted mean of its three most similar domain
   anchors. Weights are softmax of cosine affinities multiplied by 18; all other
   domains have zero weight. Center and scale these targets to unit RMS radius.
6. Center and scale UMAP to unit RMS radius and orthogonally align it to those
   targets using Procrustes. Blend 85% aligned UMAP and 15% targets, then center
   and scale the result to unit RMS radius.

Two-dimensional distances are display geometry, never reported semantic distances.
Domain label coordinates are the fitted MDS anchors. Topic IDs always equal the
existing canonical `row["topic"]` strings, and domain IDs equal original domain
names. A renamed topic needs an explicit product identity migration. Reordering a
catalog changes its fingerprint and requires the correspondingly ordered original
embedding cache; positions and neighbors are always exported with title IDs.

The public schema is:

```json
{
  "schema_version": 1,
  "cache_key": "sha256-of-metadata",
  "metadata": {},
  "domains": [{"id": "Original domain name", "x": 0.1, "y": 0.2}],
  "topics": [{"id": "Original topic title", "x": 0.1, "y": 0.2,
              "neighbors": [{"id": "Another original title", "distance": 0.15}]}]
}
```

Metadata records the algorithm version, full ordered catalog fingerprint, model,
vector source identity, byte-content hash, shape and dtype, source dimensions and
counts, all layout parameters, and numerical package versions (NumPy, SciPy,
scikit-learn, UMAP, Numba, llvmlite and PyNNDescent). Catalog text is hashed, not
copied into metadata.

## Cache validation and publication

`.cache/galaxy/<cache_key>.json` is a private build cache envelope containing the
public asset and its SHA-256 content checksum. Every source identity change creates
a different key, including descriptions, domains, source fields, catalog ordering,
model identity, original vector identity/content/dtype, algorithm version,
parameters and numerical library versions.

Before reuse the builder checks the content checksum, exact expected metadata,
schema, full catalog fingerprint, all topic/domain IDs, finite coordinates,
neighbor counts, known distinct non-self neighbors, finite angular distances in
`[0,1]`, and deterministic neighbor ordering. Malformed, incomplete or stale cache
entries are rebuilt. Both cache and output use same-directory temporary files,
flush/fsync, and atomic replacement; failures leave the prior output intact.

`from galaxy import validate_layout` provides the same catalog/asset structural
checks with standard-library imports only, allowing extension packaging to reject
a stale layout without installing numerical dependencies. Validation raises
`ValueError` and does not change files or load a model.

## Provenance and verification

The reference is the whole-catalog geometry in prototype commit
`fd581caed6e8c5fa7570fb5123ee2baa2eec0f41`. Its directional experiments, HCI text
overlay, ranking comparisons and metrics are not imported into production.
The approved original embedding identity is
`91c91f983e4d43d626c483aa64523c8db3a3cd8075b9c2b658d81325a6b9753f`.

The generated asset contains 3,452 topics across 23 domains, based on 3,452 × 768
original vectors. On the implementation machine the first complete build took
20.894 seconds and a verified cache hit took 0.233 seconds. Comparison by canonical
title against the prototype's five-decimal exported coordinates found maximum
coordinate difference `5.200237689351184e-6` and domain-anchor difference
`4.839271411483104e-6`, within rounding error. All 3,452 true top-ten neighbor sets
matched exactly; production additionally sorts each set by angular distance.

The build cache key is
`768064b1828254b042cd328178fda14d1c15d48b72b41795c8157e5f7c4d2c77`.
Pinned numerical packages deliberately preserve the prototype's scikit-learn MDS
behavior; its deprecation notices and UMAP's precomputed-metric inverse-transform
notice do not affect the exported geometry. Future package or algorithm changes
must rebuild the cache and recheck the result.

Run focused verification with:

```sh
.venv/bin/python -m pytest tests/test_galaxy.py -q
```

Tests cover hand-calculated angular distances, normalization, top-three affinity
weights, Procrustes rotation, neighbor ordering, cache reuse/invalidation,
reordered catalog identities, corrupt cache recovery, atomic writes, invalid
vectors, standard-library packaging validation and standalone CLI reuse.
