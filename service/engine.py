"""Real model-backed recommendation engine; only catalog vectors are cached."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path

import numpy as np

from explorer import (
    MODEL_NAME, ROOT, _key, _unit_vectors, interest_texts, load_catalog,
    load_model, parse_interests, recommend, score_catalog, topic_texts,
)


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
        self.topic_vectors = _unit_vectors(self.topic_vectors, "Catalog embeddings")
        if len(self.topic_vectors) != len(self.topics):
            raise ValueError("Catalog embeddings must match catalog size.")
        self.ready = True

    def _catalog_vectors(self):
        # Hash model identity and semantic catalog content, never request data.
        identity = json.dumps({"model": self.model_name, "texts": topic_texts(self.topics)},
                              ensure_ascii=False, sort_keys=True).encode("utf-8")
        filename = self.cache_dir / f"{hashlib.sha256(identity).hexdigest()}.npy"
        try:
            cached = np.load(filename, allow_pickle=False)
            cached = _unit_vectors(cached, "Cached catalog embeddings")
            if len(cached) == len(self.topics):
                return cached
        except (OSError, ValueError, EOFError):
            pass
        vectors = _unit_vectors(self.model.encode(
            topic_texts(self.topics), batch_size=64, show_progress_bar=False,
            convert_to_numpy=True, normalize_embeddings=True,
        ), "Catalog embeddings")
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

    def recommend(self, keywords, *, mode, focus, expansion_level, limit):
        if not self.ready:
            raise RuntimeError("Recommendation engine is unavailable.")
        interests = parse_interests(keywords)
        if mode not in {"path", "global"}:
            raise ValueError("Unsupported recommendation mode.")
        if focus is not None and focus not in [phrase.strip() for phrase in keywords]:
            raise ValueError("Focus must be an approved keyword.")
        if type(expansion_level) is not int or not 0 <= expansion_level <= 8:
            raise ValueError("Invalid expansion level.")
        if type(limit) is not int or not 1 <= limit <= 20:
            raise ValueError("Invalid recommendation limit.")
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
            seeds, seed_vectors, expansion=min(.07 + .01 * expansion_level, .15),
            top_k=limit,
        )
        fields = ("topic", "domain", "description", "nearest_interest", "distance", "boundary_offset", "zone")
        return [dict(id=row["topic"], **{key: row[key] for key in fields}) for row in result]
