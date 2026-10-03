"""Real model-backed recommendation engine; only catalog vectors are cached."""

from __future__ import annotations

import hashlib
import json
import math
import os
import tempfile
from pathlib import Path

import numpy as np

from galaxy import catalog_digest

from explorer import (
    MODEL_NAME, ROOT, _key, _unit_vectors, interest_texts, load_catalog,
    load_model, parse_interests, recommend, score_catalog, topic_texts,
)


class FocusIdentityConflict(ValueError):
    """The requested galaxy source does not match the loaded catalog."""


class UnknownFocusTopic(ValueError):
    """The request does not name an exact canonical catalog topic."""


class RecommendationEngine:
    def __init__(self, *, topics=None, model=None, topic_vectors=None,
                 cache_dir=None, model_name=MODEL_NAME, device=None):
        self.topics = topics
        self.model = model
        self.topic_vectors = topic_vectors
        self.model_name = model_name
        self.device = device
        self.cache_dir = Path(cache_dir) if cache_dir is not None else ROOT / ".cache/embeddings"
        self.ready = False
        self._embedding_identity = None
        self._topic_indices = {}
        self._catalog_sha256 = None

    def initialize(self):
        """Load once at application startup; fail closed when the model fails."""
        if self.ready:
            return
        if self.topics is None:
            self.topics = load_catalog()
        if self.model is None:
            self.model = load_model(device=self.device)
        if self.topic_vectors is None:
            self.topic_vectors = self._catalog_vectors()
        else:
            self._capture_embedding_identity(self.topic_vectors)
        self.topic_vectors = _unit_vectors(self.topic_vectors, "Catalog embeddings")
        if len(self.topic_vectors) != len(self.topics):
            raise ValueError("Catalog embeddings must match catalog size.")
        self._topic_indices = {row["topic"]: i for i, row in enumerate(self.topics)}
        self._catalog_sha256 = catalog_digest(self.topics)
        self.ready = True

    def _catalog_vectors(self):
        # Hash model identity and semantic catalog content, never request data.
        identity = json.dumps({"model": self.model_name, "texts": topic_texts(self.topics)},
                              ensure_ascii=False, sort_keys=True).encode("utf-8")
        filename = self.cache_dir / f"{hashlib.sha256(identity).hexdigest()}.npy"
        try:
            cached = np.load(filename, allow_pickle=False)
            # Preserve the exact source dtype/bytes before normalization.
            self._capture_embedding_identity(cached)
            cached = _unit_vectors(cached, "Cached catalog embeddings")
            if len(cached) == len(self.topics):
                return cached
        except (OSError, ValueError, EOFError):
            pass
        vectors = _unit_vectors(self.model.encode(
            topic_texts(self.topics), batch_size=64, show_progress_bar=False,
            convert_to_numpy=True, normalize_embeddings=True,
        ), "Catalog embeddings")
        # Newly generated identity describes the normalized array saved below.
        self._capture_embedding_identity(vectors)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        # Atomic replacement keeps an interrupted catalog build from poisoning cache.
        with tempfile.NamedTemporaryFile(dir=self.cache_dir, suffix=".npy", delete=False) as stream:
            temporary = Path(stream.name)
            try:
                np.save(stream, vectors, allow_pickle=False)
                stream.flush()
                os.fsync(stream.fileno())
            except BaseException:
                temporary.unlink(missing_ok=True)
                raise
        try:
            temporary.replace(filename)
        finally:
            temporary.unlink(missing_ok=True)
        return vectors

    def _capture_embedding_identity(self, values):
        raw = np.asarray(values)
        self._embedding_identity = {
            "sha256": hashlib.sha256(np.ascontiguousarray(raw).tobytes()).hexdigest(),
            "dtype": str(raw.dtype), "shape": list(raw.shape),
        }

    def focus_identity(self) -> dict:
        """Return the original source identity used by the packaged galaxy."""
        if not self.ready or self.topic_vectors.shape != (len(self.topics), 768):
            raise RuntimeError("Catalog Focus is unavailable.")
        if len(self._topic_indices) != len(self.topics):
            raise RuntimeError("Catalog Focus is unavailable.")
        return {
            "catalog_sha256": self._catalog_sha256, "model": self.model_name,
            "embedding": dict(self._embedding_identity,
                              shape=list(self._embedding_identity["shape"])),
        }

    @staticmethod
    def _validate_options(*, limit, radius, expansion, overlap, diversity,
                          max_overlap_fraction, randomness):
        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError("Invalid recommendation limit.")
        for name, value in dict(radius=radius, expansion=expansion, overlap=overlap,
                                diversity=diversity, max_overlap_fraction=max_overlap_fraction,
                                randomness=randomness).items():
            upper = .95 if name == "max_overlap_fraction" else 1
            if type(value) not in {int, float} or not math.isfinite(value) or not 0 <= value <= upper:
                raise ValueError(f"Invalid recommendation control: {name}.")

    def recommend_focus(self, topic_id: str, *, expected_identity: dict,
                        limit=10, radius=.28, expansion=.07, overlap=.015,
                        diversity=.20, max_overlap_fraction=.20, randomness=.03) -> dict:
        """Rank around one canonical catalog vector without encoding input."""
        identity = self.focus_identity()
        self._validate_options(limit=limit, radius=radius, expansion=expansion,
                               overlap=overlap, diversity=diversity,
                               max_overlap_fraction=max_overlap_fraction, randomness=randomness)
        if not isinstance(topic_id, str) or topic_id not in self._topic_indices:
            raise UnknownFocusTopic("Unknown catalog topic.")
        if expected_identity != identity:
            raise FocusIdentityConflict("Catalog source version conflict.")
        index = self._topic_indices[topic_id]
        rows = recommend(self.topics, self.topic_vectors, [topic_id],
                         self.topic_vectors[[index]], top_k=limit, radius=radius,
                         expansion=expansion, overlap=overlap, diversity=diversity,
                         max_overlap_fraction=max_overlap_fraction, randomness=randomness)
        fields = ("topic", "domain", "description", "nearest_interest", "distance", "boundary_offset", "zone")
        return dict(schema_version=1, algorithm_version="catalog-focus-band-v1",
                    seed_id=topic_id, **identity,
                    recommendations=[dict(id=row["topic"], **{key: row[key] for key in fields})
                                     for row in rows])

    def recommend(self, keywords, *, mode, focus, expansion_level, limit,
                  radius=.28, expansion=.07, overlap=.015, diversity=.20,
                  max_overlap_fraction=.20, randomness=.03):
        if not self.ready:
            raise RuntimeError("Recommendation engine is unavailable.")
        interests = parse_interests(keywords)
        if mode not in {"path", "global"}:
            raise ValueError("Unsupported recommendation mode.")
        if focus is not None and focus not in [phrase.strip() for phrase in keywords]:
            raise ValueError("Focus must be an approved keyword.")
        if type(expansion_level) is not int or not 0 <= expansion_level <= 8:
            raise ValueError("Invalid expansion level.")
        self._validate_options(limit=limit, radius=radius, expansion=expansion,
                               overlap=overlap, diversity=diversity,
                               max_overlap_fraction=max_overlap_fraction, randomness=randomness)
        vectors = self.model.encode(
            interest_texts(interests, self.topics), show_progress_bar=False,
            convert_to_numpy=True, normalize_embeddings=True,
        )
        known_keys = {_key(phrase) for phrase in interests}
        # Path uses the chosen seed's band but still protects all known interests.
        all_scores = score_catalog(self.topics, self.topic_vectors, interests, vectors)
        eligible_indices = [i for i, row in enumerate(all_scores)
                            if _key(row["topic"]) not in known_keys and row["distance"] > .035]
        if not eligible_indices:
            return []
        seeds, seed_vectors = interests, vectors
        if mode == "path":
            chosen = _key(focus or keywords[-1].strip())
            index = next(i for i, phrase in enumerate(interests) if _key(phrase) == chosen)
            seeds, seed_vectors = [interests[index]], np.asarray(vectors)[[index]]
        result = recommend(
            [self.topics[i] for i in eligible_indices], self.topic_vectors[eligible_indices],
            seeds, seed_vectors, radius=radius, expansion=min(expansion + .01 * expansion_level, 1),
            overlap=overlap, diversity=diversity, max_overlap_fraction=max_overlap_fraction,
            randomness=randomness, top_k=limit,
        )
        fields = ("topic", "domain", "description", "nearest_interest", "distance", "boundary_offset", "zone")
        return [dict(id=row["topic"], **{key: row[key] for key in fields}) for row in result]
