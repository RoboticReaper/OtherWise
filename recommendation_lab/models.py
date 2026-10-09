"""Named, frozen configurations selectable by serving and study clients."""
from dataclasses import dataclass, field
from types import MappingProxyType

from .systems import RankConfig


@dataclass(frozen=True)
class ModelSpec:
    name: str
    variant: str
    role: str
    config: RankConfig = field(default_factory=RankConfig)
    uses_history: bool = False
    requires_lexical: bool = True


_specs = [
    ModelSpec('K-connection', 'V5-known', 'candidate', RankConfig(relevance=.95, content=.05, novelty=0., diversity=.05)),
    ModelSpec('K-literal', 'V5-known', 'candidate', RankConfig(relevance=.65, content=.2, novelty=.15, diversity=.15, literal_weight=.75)),
    ModelSpec('V0', 'V0', 'historical_baseline', requires_lexical=False),
    ModelSpec('V3', 'V3', 'candidate'),
    ModelSpec('semantic-nearest', 'semantic-nearest', 'relevance_baseline', requires_lexical=False),
    ModelSpec('BM25', 'BM25', 'lexical_baseline'),
    ModelSpec('random', 'random', 'sanity_baseline', requires_lexical=False),
    ModelSpec('history-recency', 'history-recency', 'matched_history_baseline', uses_history=True),
    ModelSpec('trajectory', 'trajectory', 'candidate', uses_history=True),
    ModelSpec('V1', 'V1', 'component_control', requires_lexical=False),
    ModelSpec('V2', 'V2', 'component_control', requires_lexical=False),
    ModelSpec('V3-no-lexical', 'V3-no-lexical', 'component_control', requires_lexical=False),
    ModelSpec('V3-no-graph', 'V3-no-graph', 'component_control'),
    ModelSpec('V3-no-ranking', 'V3-no-ranking', 'component_control'),
    ModelSpec('V3-adaptive', 'V3-adaptive', 'policy_control'),
    ModelSpec('V5-known', 'V5-known', 'policy_control'),
]
MODEL_SPECS = MappingProxyType({spec.name: spec for spec in _specs})


def get_model(name):
    if not isinstance(name, str) or name not in MODEL_SPECS:
        raise ValueError('Unknown recommendation model.')
    return MODEL_SPECS[name]
