"""Original MPNet whole-catalog geometry, independently cached from recommendations."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from importlib import metadata as package_metadata
import json
import os
from pathlib import Path
import tempfile
import time

import numpy as np

from .validation import catalog_digest, json_digest, validate_catalog, validate_layout

MODEL_NAME = "sentence-transformers/all-mpnet-base-v2"
ALGORITHM_VERSION = "original-mpnet-umap-b-v4-oriented-layout"
DEFAULT_PARAMETERS = {
    "n_components": 2, "n_neighbors": 12, "min_dist": .40,
    "spread": 1.5, "repulsion_strength": 2.5, "n_epochs": 300,
    "metric": "precomputed", "distance": "acos(clipped_cosine)/pi", "seed": 42,
    "n_jobs": 1, "mds_n_init": 1, "mds_max_iter": 500, "mds_eps": 1e-7,
    "anchor_top_k": 3, "anchor_temperature": 18., "anchor_strength": 0.,
    "neighbor_count": 10,
    "dense_topic_limit": 4096, "distance_block_size": 256,
    "sparse_init": "random",
    "domain_label_neighbors": 32,
}


@dataclass(frozen=True)
class BuildResult:
    asset: dict
    cache_hit: bool
    cache_path: Path
    elapsed_seconds: float


def numerical_versions() -> dict[str, str]:
    versions = {}
    for name in ("numpy", "scipy", "scikit-learn", "umap-learn", "numba", "llvmlite", "pynndescent"):
        try:
            versions[name] = package_metadata.version(name)
        except package_metadata.PackageNotFoundError:
            versions[name] = "not-installed"
    return versions


def unit_vectors(values) -> np.ndarray:
    values = np.asarray(values, dtype=np.float64)
    if values.ndim != 2 or 0 in values.shape or not np.isfinite(values).all():
        raise ValueError("Embeddings must be a nonempty matrix of finite vectors.")
    norms = np.linalg.norm(values, axis=1, keepdims=True)
    if not np.isfinite(norms).all() or np.any(norms < 1e-12):
        raise ValueError("Embeddings cannot contain zero or overflowing vectors.")
    return values / norms


def angular_distances(values) -> np.ndarray:
    normalized = unit_vectors(values)
    angular = np.arccos(np.clip(normalized @ normalized.T, -1., 1.)) / np.pi
    np.fill_diagonal(angular, 0.)
    return angular


def exact_angular_neighbors(values, topic_ids, *, k=10, block_size=256):
    """Exact float64 MPNet neighbors using O(block_size * N + N * k) memory.

    Partial selection retains every cutoff tie before ordering by literal title;
    sorting just an arbitrary argpartition slice would discard correct IDs.
    """
    normalized = unit_vectors(values)
    size = len(normalized)
    if len(topic_ids) != size or len(set(topic_ids)) != size:
        raise ValueError("Neighbor IDs must uniquely identify every vector row.")
    if type(k) is not int or k < 1 or type(block_size) is not int or block_size < 1:
        raise ValueError("Neighbor count and block size must be positive integers.")
    count = min(k, size - 1)
    indices = np.empty((size, count), dtype=np.int32)
    distances = np.empty((size, count), dtype=np.float64)
    names = np.asarray(topic_ids)
    title_rank = np.empty(size, dtype=np.int32)
    title_rank[np.argsort(names)] = np.arange(size)
    if count == 0:
        return indices, distances
    for start in range(0, size, block_size):
        stop = min(start + block_size, size)
        block = normalized[start:stop] @ normalized.T
        np.clip(block, -1., 1., out=block)
        np.arccos(block, out=block)
        block /= np.pi
        for offset, row in enumerate(block):
            index = start + offset
            row[index] = np.inf
            cutoff = np.partition(row, count - 1)[count - 1]
            closer = np.flatnonzero(row < cutoff)
            ties = np.flatnonzero(row == cutoff)
            remaining = count - len(closer)
            if len(ties) > remaining:
                ties = ties[np.argpartition(title_rank[ties], remaining - 1)[:remaining]]
            chosen = np.concatenate((closer, ties))
            chosen = chosen[np.lexsort((title_rank[chosen], row[chosen]))]
            indices[index] = chosen
            distances[index] = row[chosen]
    return indices, distances


def standardize(values) -> np.ndarray:
    centered = np.asarray(values) - np.mean(values, axis=0)
    radius = np.sqrt(np.mean(np.sum(centered * centered, axis=1)))
    if not np.isfinite(radius) or radius < 1e-12:
        raise ValueError("Layout points must have finite nonzero spread.")
    return centered / radius


def anchor_targets(affinities, anchors, *, top_k=3, temperature=18.) -> np.ndarray:
    count = min(top_k, affinities.shape[1])
    # The prototype uses kth=3 with three retained entries. Preserve its order
    # (including floating-point summation order) whenever four domains exist.
    kth = min(count, affinities.shape[1] - 1)
    top = np.argpartition(-affinities, kth, axis=1)[:, :count]
    weights = np.exp(temperature * (np.take_along_axis(affinities, top, axis=1)
                                   - np.max(affinities, axis=1, keepdims=True)))
    weights /= weights.sum(axis=1, keepdims=True)
    return np.sum(anchors[top] * weights[:, :, None], axis=1)


def blend_layout(graph, target, *, strength=.15) -> np.ndarray:
    from scipy.linalg import orthogonal_procrustes
    graph, target = standardize(graph), standardize(target)
    aligned = graph @ orthogonal_procrustes(graph, target)[0]
    return standardize((1 - strength) * aligned + strength * target)


def project_layout(topics, vectors, angular, parameters):
    """Fit seeded B geometry with the approved MDS orientation and anchor weight."""
    try:
        from sklearn.manifold import MDS
        from umap import UMAP
    except ImportError as error:
        raise RuntimeError("Install requirements-layout.txt to build galaxy geometry.") from error
    p = parameters
    domains = sorted({row["domain"] for row in topics})
    options = dict(n_components=p["n_components"], n_neighbors=p["n_neighbors"],
                   min_dist=p["min_dist"], spread=p["spread"],
                   repulsion_strength=p["repulsion_strength"], n_epochs=p["n_epochs"],
                   metric=p["metric"], random_state=p["seed"],
                   n_jobs=p["n_jobs"], init=p["sparse_init"])
    if isinstance(angular, tuple):
        from scipy.sparse import csr_matrix
        indices, distances = angular
        size = len(topics)
        count = min(p["n_neighbors"], size - 1)
        # UMAP's local connectivity expects self as the first zero-distance entry.
        knn_indices = np.column_stack((np.arange(size), indices[:, :count - 1]))
        knn_distances = np.column_stack((np.zeros(size), distances[:, :count - 1]))
        sparse_distances = csr_matrix((distances.ravel(), indices.ravel(),
            np.arange(0, (size + 1) * indices.shape[1], indices.shape[1])), shape=(size, size))
        sparse_distances = sparse_distances.maximum(sparse_distances.T)
        # Spectral initialization on disconnected precomputed graphs can allocate
        # component-by-catalog matrices. Seeded random initialization bounds memory
        # even when distinct domains form disconnected components.
        options.update(n_neighbors=count, init=p["sparse_init"],
                       precomputed_knn=(knn_indices, knn_distances, None))
        angular = sparse_distances
    graph = UMAP(**options).fit_transform(angular)
    assignments = np.array([domains.index(row["domain"]) for row in topics])
    prototypes = unit_vectors(np.array([vectors[assignments == i].mean(axis=0)
                                       for i in range(len(domains))]))
    anchor_dist = np.arccos(np.clip(prototypes @ prototypes.T, -1., 1.)) / np.pi
    np.fill_diagonal(anchor_dist, 0.)
    anchors = standardize(MDS(n_components=p["n_components"], metric=True,
        dissimilarity="precomputed", n_init=p["mds_n_init"], random_state=p["seed"],
        max_iter=p["mds_max_iter"], eps=p["mds_eps"]).fit_transform(anchor_dist))
    target = anchor_targets(vectors @ prototypes.T, anchors,
        top_k=p["anchor_top_k"], temperature=p["anchor_temperature"])
    return blend_layout(graph, target, strength=p["anchor_strength"]), anchors


def nearest_neighbors(angular, topic_ids, *, k=10) -> list[list[dict]]:
    """True high-dimensional nearest neighbors, with deterministic tie ordering."""
    count = min(k, len(topic_ids) - 1)
    names = np.asarray(topic_ids)
    result = []
    for index, distances in enumerate(angular):
        order = np.lexsort((names, distances))
        chosen = [int(i) for i in order if i != index][:count]
        result.append([{"id": topic_ids[i], "distance": float(distances[i])} for i in chosen])
    return result


def domain_label_positions(topics, positions, *, neighbors=32):
    """Place each label on a member of its densest final same-domain cluster.

    MDS anchors guide the geometry but are not locations of the projected stars.
    A mean can also land in empty space between disconnected topic clusters.
    """
    from scipy.spatial import cKDTree
    points = np.asarray(positions, dtype=np.float64)
    domains = sorted({row['domain'] for row in topics})
    result = []
    for domain in domains:
        indices = [i for i, row in enumerate(topics) if row['domain'] == domain]
        own = points[indices]
        count = min(neighbors, len(own))
        if count == 1:
            chosen = 0
        else:
            distances, _ = cKDTree(own).query(own, k=count)
            names = np.asarray([topics[i]['topic'] for i in indices])
            chosen = int(np.lexsort((names, distances[:, -1]))[0])
        result.append(own[chosen])
    return np.asarray(result)


def atomic_json_write(path: Path, payload, *, indent=None) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                prefix=f".{path.name}.", suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(payload, stream, ensure_ascii=False,
                      separators=(",", ":") if indent is None else None,
                      indent=indent, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def build_galaxy(*, topics, vectors, embedding_identity, cache_dir, output_path,
                 model_name=MODEL_NAME, parameters=None) -> BuildResult:
    """Validate inputs, reuse a verified cache, and atomically publish public JSON."""
    started = time.perf_counter()
    validate_catalog(topics)
    original = np.asarray(vectors)
    if original.ndim != 2 or original.shape != (len(topics), 768):
        raise ValueError("Original MPNet embeddings must have one 768-dimensional row per topic.")
    units = unit_vectors(original)
    if not isinstance(embedding_identity, str) or not embedding_identity:
        raise ValueError("An original embedding identity is required.")
    p = dict(DEFAULT_PARAMETERS if parameters is None else parameters)
    if set(p) != set(DEFAULT_PARAMETERS):
        raise ValueError("Layout parameters must include every algorithm parameter.")
    if (type(p["dense_topic_limit"]) is not int or p["dense_topic_limit"] < 1
            or type(p["distance_block_size"]) is not int or p["distance_block_size"] < 1
            or type(p["domain_label_neighbors"]) is not int or p["domain_label_neighbors"] < 1
            or p["sparse_init"] != "random"):
        raise ValueError("Distance limits must be positive integers and sparse initialization random.")
    scalable = len(topics) > p["dense_topic_limit"]
    metadata = {
        "algorithm_version": ALGORITHM_VERSION, "catalog_sha256": catalog_digest(topics),
        "model": model_name, "dimensions": 768, "topic_count": len(topics),
        "domain_count": len({row["domain"] for row in topics}),
        "embedding": {"identity": embedding_identity,
            "sha256": hashlib.sha256(np.ascontiguousarray(original).tobytes()).hexdigest(),
            "dtype": str(original.dtype), "shape": list(original.shape)},
        "parameters": p, "numerical_versions": numerical_versions(),
        "distance_storage": "exact-blockwise-knn" if scalable else "dense-angular",
    }
    cache_key = json_digest(metadata)
    cache_path = Path(cache_dir) / f"{cache_key}.json"
    asset = None
    try:
        envelope = json.loads(cache_path.read_text(encoding="utf-8"))
        candidate = envelope["asset"]
        if envelope["asset_sha256"] != json_digest(candidate) or candidate["metadata"] != metadata:
            raise ValueError("Galaxy cache checksum or metadata mismatch.")
        validate_layout(candidate, topics)
        asset = candidate
    except (OSError, ValueError, TypeError, KeyError, OverflowError):
        # Interrupted or stale local caches are rebuilt from the original vectors.
        pass
    cache_hit = asset is not None
    if asset is None:
        topic_ids = [row["topic"] for row in topics]
        if scalable:
            angular = exact_angular_neighbors(original, topic_ids,
                k=max(p["neighbor_count"], p["n_neighbors"] - 1),
                block_size=p["distance_block_size"])
            indices, distances = angular
            count = min(p["neighbor_count"], len(topics) - 1)
            neighbors = [[{"id": topic_ids[int(indices[row, i])],
                           "distance": float(distances[row, i])} for i in range(count)]
                         for row in range(len(topics))]
        else:
            angular = angular_distances(original)
            neighbors = nearest_neighbors(angular, topic_ids, k=p["neighbor_count"])
        positions, _anchors = project_layout(topics, units, angular, p)
        label_positions = domain_label_positions(topics, positions,
                                                neighbors=p['domain_label_neighbors'])
        domains = sorted({row["domain"] for row in topics})
        asset = {"schema_version": 1, "metadata": metadata, "cache_key": cache_key,
            "domains": [{"id": name, "x": float(label_positions[i, 0]), "y": float(label_positions[i, 1])}
                        for i, name in enumerate(domains)],
            "topics": [{"id": row["topic"], "x": float(positions[i, 0]), "y": float(positions[i, 1]),
                        "neighbors": neighbors[i]} for i, row in enumerate(topics)]}
        validate_layout(asset, topics)
        atomic_json_write(cache_path, {"asset_sha256": json_digest(asset), "asset": asset})
    atomic_json_write(Path(output_path), asset)
    return BuildResult(asset, cache_hit, cache_path, time.perf_counter() - started)
