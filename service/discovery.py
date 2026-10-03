"""Stateless graph recommendations; cache only public graph embeddings."""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path

import numpy as np

from explorer import _key, _unit_vectors, interest_texts, parse_interests, recommend, score_catalog, topic_texts
from feedback import new_profile, set_feedback
from graph_explorer import graph_candidates, graph_concepts, load_graph, recommend_specific, select_areas


class DiscoveryEngine:
    def __init__(self, broad, *, graph=None, concept_vectors=None, area_vectors=None, cache_dir=None):
        self.broad = broad
        self.graph = graph
        self.concept_vectors = concept_vectors
        self.area_vectors = area_vectors
        self.cache_dir = Path(cache_dir) if cache_dir is not None else broad.cache_dir
        self.ready = False

    def _vectors(self, texts):
        identity = json.dumps({'model': self.broad.model_name, 'texts': texts}, ensure_ascii=False, sort_keys=True).encode()
        destination = self.cache_dir / f'discovery-{hashlib.sha256(identity).hexdigest()}.npy'
        expected = (len(texts), self.broad.topic_vectors.shape[1])
        try:
            values = _unit_vectors(np.load(destination, allow_pickle=False), 'Graph embeddings')
            if values.shape == expected:
                return values
        except (OSError, ValueError, EOFError):
            pass
        values = _unit_vectors(self.broad.model.encode(texts, batch_size=64, show_progress_bar=False,
                                convert_to_numpy=True, normalize_embeddings=True), 'Graph embeddings')
        if values.shape != expected:
            raise ValueError('Graph embedding dimensions do not match the model.')
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=self.cache_dir, suffix='.npy', delete=False) as stream:
                temporary = Path(stream.name)
                np.save(stream, values, allow_pickle=False)
                stream.flush()
                os.fsync(stream.fileno())
            temporary.replace(destination)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
        return values

    def initialize(self):
        if self.ready:
            return
        self.broad.initialize()
        if self.graph is None:
            self.graph = load_graph()
        self.concepts = graph_concepts(self.graph)
        self.nodes = {n['id']: n for n in self.concepts}
        self.areas = {a['id'] for a in self.graph['areas']}
        self.reached = {r['id']: r for r in graph_candidates(self.graph)}
        self.graph_sha256 = hashlib.sha256(json.dumps(self.graph, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        if self.concept_vectors is None:
            self.concept_vectors = self._vectors(topic_texts(self.concepts))
        if self.area_vectors is None:
            self.area_vectors = self._vectors(topic_texts(self.graph['areas']))
        self.concept_vectors = _unit_vectors(self.concept_vectors, 'Concept embeddings')
        self.area_vectors = _unit_vectors(self.area_vectors, 'Area embeddings')
        dimensions = self.broad.topic_vectors.shape[1]
        if self.concept_vectors.shape != (len(self.concepts), dimensions) or self.area_vectors.shape != (len(self.areas), dimensions):
            raise ValueError('Graph vectors must match public graph identities.')
        self.ready = True

    def _profile(self, feedback, exposures):
        profile = new_profile()
        seen = set()
        for rating in feedback:
            concept, area = rating['concept_id'], rating['area_id']
            if concept in seen or concept not in self.reached or area not in self.reached[concept]['area_ids']:
                raise ValueError('Invalid concept feedback.')
            seen.add(concept)
            set_feedback(profile, concept, curious=rating['curious'], known=rating['known'],
                         difficulty=rating['difficulty'], level=self.nodes[concept].get('level'), area_ids=[area])
        if any(area not in self.areas or type(count) is not int or not 0 <= count <= 1_000_000_000 for area, count in exposures.items()):
            raise ValueError('Invalid area exposures.')
        profile['exposures'] = dict(exposures)
        return profile

    def recommend(self, keywords, *, mode, focus, expansion_level, limit, feedback, exposures,
                  seed=42, exploration_fraction=.3, radius=.28, expansion=.07, overlap=.015,
                  diversity=.2, max_overlap_fraction=.2, randomness=.03):
        if not self.ready:
            raise RuntimeError('Graph recommendations are unavailable.')
        self.broad._validate_options(limit=limit, radius=radius, expansion=expansion, overlap=overlap,
                                    diversity=diversity, max_overlap_fraction=max_overlap_fraction, randomness=randomness)
        interests = parse_interests(keywords)
        if mode not in {'path', 'global'} or focus is not None and focus not in keywords:
            raise ValueError('Invalid discovery mode or focus.')
        if type(expansion_level) is not int or not 0 <= expansion_level <= 8:
            raise ValueError('Invalid expansion level.')
        profile = self._profile(feedback, exposures)
        vectors = _unit_vectors(self.broad.model.encode(interest_texts(interests, self.broad.topics + self.concepts),
                    show_progress_bar=False, convert_to_numpy=True, normalize_embeddings=True), 'Interest embeddings')
        # Even in path mode, exclude familiarity to every approved interest.
        known_titles = {_key(s) for s in interests}
        for row in score_catalog(self.concepts, self.concept_vectors, interests, vectors):
            if row['distance'] <= .035 or _key(row['topic']) in known_titles:
                if row['id'] not in profile['items']:
                    set_feedback(profile, row['id'], known=True)
                else:
                    profile['items'][row['id']]['known'] = True
        seeds, seed_vectors = interests, vectors
        if mode == 'path':
            chosen = _key(focus or keywords[-1])
            index = next(i for i, phrase in enumerate(interests) if _key(phrase) == chosen)
            seeds, seed_vectors = [interests[index]], vectors[[index]]
        expansion = min(expansion + .01 * expansion_level, 1)
        queries = [seed_vectors]
        broad = recommend(self.broad.topics, self.broad.topic_vectors, seeds, seed_vectors, radius=radius,
                          expansion=expansion, overlap=overlap, top_k=24, diversity=diversity, randomness=0)
        if broad:
            queries.append(self.broad.topic_vectors[[r['catalog_index'] for r in broad]])
        areas = select_areas(self.graph['areas'], self.area_vectors, np.vstack(queries), limit=8)
        rows = recommend_specific(self.graph, self.concept_vectors, seeds, seed_vectors,
                                 area_ids=areas, profile=profile, radius=radius, expansion=expansion,
                                 overlap=overlap, top_k=limit, diversity=diversity, randomness=randomness,
                                 seed=seed, exploration_fraction=exploration_fraction, max_overlap_fraction=max_overlap_fraction)
        fields = ('topic', 'domain', 'description', 'nearest_interest', 'distance', 'boundary_offset', 'zone')
        result = [dict(id=r['topic'], **{key:r[key] for key in fields}, discovery=dict(
                    concept_id=r['id'], area_id=r['area_id'], graph_path=r['graph_path'],
                    source_url=r.get('source_url', ''), level=r.get('level'),
                    exploration_pick=r['exploration_pick'], exploration_target=r['exploration_target'],
                    exploration_achieved=r['exploration_achieved'])) for r in rows]
        return dict(recommendations=result, seed=seed, graph_sha256=self.graph_sha256)
