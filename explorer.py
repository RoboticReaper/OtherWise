"""Topic exploration in embedding space, independent of notebook or web UI."""

from __future__ import annotations

import json
import math
import re
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
MODEL_NAME = "sentence-transformers/all-mpnet-base-v2"
EPSILON = 1e-9


def _key(text: str) -> str:
    key = re.sub(r"[\s_\-\u2010-\u2015]+", " ", text.strip().casefold()).strip()
    return key if any(character.isalnum() for character in key) else ""


def parse_interests(value: str | list[str]) -> list[str]:
    """Accept comma/newline-separated phrases; preserve order and remove repeats."""
    parts = re.split(r"[,;\n]", value) if isinstance(value, str) else value
    interests, seen = [], set()
    for part in parts:
        if not isinstance(part, str):
            raise ValueError("Interests must be text phrases.")
        phrase = part.strip()
        key = _key(phrase)
        if key and key not in seen:
            interests.append(phrase)
            seen.add(key)
    if not interests:
        raise ValueError("Enter at least one interest, such as gardening or photography.")
    return interests


def load_catalog(path: str | Path = ROOT / "data/topics.json") -> list[dict]:
    topics = json.loads(Path(path).read_text())
    if not isinstance(topics, list) or not topics:
        raise ValueError("The catalog must be a nonempty list of topics.")
    seen = set()
    for row in topics:
        if not isinstance(row, dict) or any(
            not isinstance(row.get(field), str) or not row[field].strip()
            for field in ("topic", "domain", "description")
        ):
            raise ValueError("Every topic needs a title, domain and description.")
        key = _key(row["topic"])
        if not key or key in seen:
            raise ValueError("Catalog topic titles must be nonempty and unique.")
        seen.add(key)
    return topics


def topic_texts(topics: list[dict]) -> list[str]:
    return [f"{row['topic']}: {row['description']}" for row in topics]


def interest_texts(interests: list[str], topics: list[dict]) -> list[str]:
    """Use catalog context for exact titles; leave other user phrases unchanged."""
    lookup = {_key(row["topic"]): text for row, text in zip(topics, topic_texts(topics))}
    return [lookup.get(_key(phrase), phrase) for phrase in interests]


def load_model(device: str | None = None):
    """Download once into the project cache, then reuse weights locally."""
    from sentence_transformers import SentenceTransformer
    import torch

    if device is None:
        device = "mps" if torch.backends.mps.is_available() else "cpu"
    return SentenceTransformer(MODEL_NAME, cache_folder=str(ROOT / ".cache/models"), device=device)


def _unit_vectors(values, name: str) -> np.ndarray:
    vectors = np.asarray(values, dtype=float)
    if vectors.ndim != 2 or 0 in vectors.shape or not np.isfinite(vectors).all():
        raise ValueError(f"{name} must be a nonempty matrix of finite vectors.")
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    if np.any(norms < 1e-12) or not np.isfinite(norms).all():
        raise ValueError(f"{name} cannot contain zero-length or overflowing vectors.")
    return vectors / norms


def score_catalog(topics, topic_vectors, interests, interest_vectors) -> list[dict]:
    """Measure each topic against its closest individual interest, in full dimensions."""
    if not interests or any(not isinstance(s, str) or not _key(s) for s in interests):
        raise ValueError("Provide at least one nonempty interest phrase.")
    candidates = _unit_vectors(topic_vectors, "Topic embeddings")
    seeds = _unit_vectors(interest_vectors, "Interest embeddings")
    if len(topics) != len(candidates) or len(interests) != len(seeds):
        raise ValueError("Each topic and interest must have exactly one embedding.")
    if candidates.shape[1] != seeds.shape[1]:
        raise ValueError("Topic and interest embeddings must have matching dimensions.")
    distances = np.arccos(np.clip(candidates @ seeds.T, -1.0, 1.0)) / np.pi
    nearest = np.argmin(distances, axis=1)
    return [
        dict(row, catalog_index=i, nearest_interest=interests[int(nearest[i])],
             distance=float(distances[i, nearest[i]]))
        for i, row in enumerate(topics)
    ]


def nearest_topics(topics, topic_vectors, interests, interest_vectors, top_k=10) -> list[dict]:
    """Ordinary semantic-search baseline, excluding exact input topic titles."""
    if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k < 1:
        raise ValueError("top_k must be a positive integer.")
    input_titles = {_key(s) for s in interests}
    rows = score_catalog(topics, topic_vectors, interests, interest_vectors)
    return sorted((r for r in rows if _key(r["topic"]) not in input_titles),
                  key=lambda r: r["distance"])[:top_k]


def recommend(topics, topic_vectors, interests, interest_vectors, *,
              radius=0.28, expansion=0.07, overlap=0.015, top_k=10,
              diversity=0.20, max_overlap_fraction=0.2, randomness=0.03, seed=None,
              classification_distances=None) -> list[dict]:
    """Search a band around a union of interest neighborhoods.

    All distances are angular: acos(cosine_similarity) / pi, in [0, 1].
    Eligible distances lie in [radius-overlap, radius+expansion]. Candidates
    close to the outward band's midpoint rank first, with a diversity penalty.
    Familiar topics are capped as a fraction of the *actual* returned count.
    Empty or sparse bands are never silently broadened.
    A bounded score perturbation varies close choices. Set seed for repeatability,
    or randomness=0 for deterministic ranking. Randomness cannot change eligibility.
    """
    for name, value in dict(radius=radius, expansion=expansion, overlap=overlap,
                            diversity=diversity, max_overlap_fraction=max_overlap_fraction,
                            randomness=randomness).items():
        if not isinstance(value, (float, int)) or not math.isfinite(value) or not 0 <= value <= 1:
            raise ValueError(f"{name} must be a finite number between 0 and 1.")
    if max_overlap_fraction >= 1:
        raise ValueError("max_overlap_fraction must be below 1 so discovery remains necessary.")
    if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k < 1:
        raise ValueError("top_k must be a positive integer.")
    if seed is not None and (not isinstance(seed, int) or isinstance(seed, bool) or seed < 0):
        raise ValueError("seed must be a nonnegative integer or None.")

    rows = score_catalog(topics, topic_vectors, interests, interest_vectors)
    classifications = _classification_distances(classification_distances,[r['distance'] for r in rows])
    units = _unit_vectors(topic_vectors, "Topic embeddings")
    input_titles = {_key(s) for s in interests}
    lower, upper = max(0.0, radius - overlap), min(1.0, radius + expansion)
    eligible = [r for r in rows if lower - EPSILON <= r["distance"] <= upper + EPSILON
                and r["distance"] > 0.035 and _key(r["topic"]) not in input_titles]
    new = [r for r in eligible if classifications[r['catalog_index']] >= radius - EPSILON]
    familiar = [r for r in eligible if classifications[r['catalog_index']] < radius - EPSILON]

    # n_familiar / (n_familiar + n_new) <= fraction, even for sparse bands.
    familiar_count = min(len(familiar), math.floor(top_k * max_overlap_fraction + EPSILON),
                         math.floor(len(new) * max_overlap_fraction / (1 - max_overlap_fraction) + EPSILON))
    remaining = {"New territory": min(len(new), top_k - familiar_count),
                 "Familiar overlap": familiar_count}
    target = (radius + upper) / 2
    scale = max((upper - radius) / 2, 0.025)
    pool = [dict(r, zone="New territory") for r in new] + [dict(r, zone="Familiar overlap") for r in familiar]
    rng = np.random.default_rng(seed)
    jitter = {r["catalog_index"]: float(rng.uniform(-randomness, randomness)) if randomness else 0.0
              for r in pool}
    selected = []
    while any(remaining.values()):
        available = [r for r in pool if remaining[r["zone"]] > 0]

        def rank(row):
            fit = 1 - min(abs(row["distance"] - target) / scale, 1.0)
            redundancy = max(0.0, max((float(units[row["catalog_index"]] @ units[s["catalog_index"]])
                                      for s in selected), default=0.0))
            score = (1 - diversity) * fit - diversity * redundancy + jitter[row["catalog_index"]]
            return (round(score, 12), -row["catalog_index"])

        best = max(available, key=rank)
        pool.remove(best)
        remaining[best["zone"]] -= 1
        selected.append(dict(best, boundary_offset=best["distance"] - radius))
    return selected


def _classification_distances(values, default):
    """Optional all-interest quota geometry for a separately focused candidate band."""
    result = np.asarray(default if values is None else values,dtype=float)
    if result.shape != (len(default),) or not np.isfinite(result).all() or np.any((result < 0)|(result > 1)):
        raise ValueError('Classification distances must match candidates and lie in [0,1].')
    return result
