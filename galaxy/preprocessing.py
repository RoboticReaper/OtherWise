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
ALGORITHM_VERSION = "original-mpnet-umap-domain-anchors-v1"
DEFAULT_PARAMETERS = {
    "n_components": 2, "n_neighbors": 30, "min_dist": .15,
    "metric": "precomputed", "distance": "acos(clipped_cosine)/pi", "seed": 42,
    "n_jobs": 1, "mds_n_init": 1, "mds_max_iter": 500, "mds_eps": 1e-7,
    "anchor_top_k": 3, "anchor_temperature": 18., "anchor_strength": .15,
    "neighbor_count": 10,
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
    """Fit the approved UMAP + MDS anchors; no experimental text overlays."""
    try:
        from sklearn.manifold import MDS
        from umap import UMAP
    except ImportError as error:
        raise RuntimeError("Install requirements-layout.txt to build galaxy geometry.") from error
    p = parameters
    domains = sorted({row["domain"] for row in topics})
    assignments = np.array([domains.index(row["domain"]) for row in topics])
    prototypes = unit_vectors(np.array([vectors[assignments == i].mean(axis=0)
                                       for i in range(len(domains))]))
    graph = UMAP(n_components=p["n_components"], n_neighbors=p["n_neighbors"],
                 min_dist=p["min_dist"], metric=p["metric"], random_state=p["seed"],
                 n_jobs=p["n_jobs"]).fit_transform(angular)
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


def atomic_json_write(path: Path, payload: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                prefix=f".{path.name}.", suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(payload, stream, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
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
    metadata = {
        "algorithm_version": ALGORITHM_VERSION, "catalog_sha256": catalog_digest(topics),
        "model": model_name, "dimensions": 768, "topic_count": len(topics),
        "domain_count": len({row["domain"] for row in topics}),
        "embedding": {"identity": embedding_identity,
            "sha256": hashlib.sha256(np.ascontiguousarray(original).tobytes()).hexdigest(),
            "dtype": str(original.dtype), "shape": list(original.shape)},
        "parameters": p, "numerical_versions": numerical_versions(),
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
        angular = np.arccos(np.clip(units @ units.T, -1., 1.)) / np.pi
        np.fill_diagonal(angular, 0.)
        positions, anchors = project_layout(topics, units, angular, p)
        neighbors = nearest_neighbors(angular, [row["topic"] for row in topics], k=p["neighbor_count"])
        domains = sorted({row["domain"] for row in topics})
        asset = {"schema_version": 1, "metadata": metadata, "cache_key": cache_key,
            "domains": [{"id": name, "x": float(anchors[i, 0]), "y": float(anchors[i, 1])}
                        for i, name in enumerate(domains)],
            "topics": [{"id": row["topic"], "x": float(positions[i, 0]), "y": float(positions[i, 1]),
                        "neighbors": neighbors[i]} for i, row in enumerate(topics)]}
        validate_layout(asset, topics)
        atomic_json_write(cache_path, {"asset_sha256": json_digest(asset), "asset": asset})
    atomic_json_write(Path(output_path), asset)
    return BuildResult(asset, cache_hit, cache_path, time.perf_counter() - started)
