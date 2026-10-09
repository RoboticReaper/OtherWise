"""Stateless serving adapter for the recommendation experiment candidates."""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict

import numpy as np

from explorer import ROOT
from recommendation_lab.history import HistoryConfig
from recommendation_lab.inventory import Inventory
from recommendation_lab.models import MODEL_SPECS, get_model
from recommendation_lab.systems import RecommendationLab, Request


class ModelEngine:
    def __init__(self, broad=None, discovery=None, *, lab=None, registry=None):
        self.broad, self.discovery, self.lab = broad, discovery, lab
        self.registry = registry
        self.ready = False

    def initialize(self):
        if self.ready:
            return
        if self.lab is None:
            self.broad.initialize()
            self.discovery.initialize()
            registry = self.registry
            if registry is None:
                registry = json.loads((ROOT / 'data/recommendation-identities.json').read_text())
            inventory = Inventory.from_sources(self.broad.topics, self.discovery.graph, registry)
            identity = dict(model=self.broad.model_name, inventory_version=inventory.version,
                graph_sha256=self.discovery.graph_sha256,
                embedding_sha256=hashlib.sha256(np.ascontiguousarray(self.broad.topic_vectors).tobytes()).hexdigest())
            self.lab = RecommendationLab(inventory, self.broad.topics, self.discovery.graph,
                self.broad.model, self.broad.topic_vectors, self.discovery.concept_vectors,
                self.discovery.area_vectors, model_identity=identity, cache_interests=False)
        self.lab.reopen()
        self.lab.cache_interests = False
        self.lab.clear_interest_cache()
        self.ready = True

    def available(self, spec):
        return bool(self.ready and self.lab is not None and (not spec.requires_lexical or self.lab.lexical is not None))

    def describe(self):
        return dict(schema_version=1, ready=self.ready,
            inventory_version=self.lab.inventory.version if self.ready else None,
            model_identity=self.lab.model_identity if self.ready else None,
            history_defaults=asdict(HistoryConfig()),
            models=[dict(name=spec.name, variant=spec.variant, role=spec.role,
                ready=self.available(spec), uses_history=spec.uses_history,
                result_kinds=['broad', 'specific'], ranking=asdict(spec.config)) for spec in MODEL_SPECS.values()])

    def recommend(self, model, **values):
        spec = get_model(model)
        if not self.available(spec):
            raise RuntimeError('Recommendation model is unavailable.')
        batch = self.lab.recommend(Request(**values), spec.variant, spec.config,
                                   serving_guards=spec.variant in ('V0', 'V1'))
        return dict(batch, model=spec.name)

    def close(self):
        self.ready = False
        if self.lab is not None:
            self.lab.close()
