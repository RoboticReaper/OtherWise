"""Study baselines exercised through the shared recommendation boundary."""
import pytest

from recommendation_lab.systems import Request
from test_recommendation_systems import lab


def test_semantic_nearest_returns_closest_distinct_unknown_concepts():
    system = lab()
    result = system.recommend(Request(['engineering'], limit=3,
        feedback={'Q100': {'known': True}}), 'semantic-nearest')
    assert [r['concept_id'] for r in result['recommendations']] == ['Q101', 'Q102', 'Q103']
    assert all(r['sources'] for r in result['recommendations'])


def test_bm25_returns_only_lexical_matches_and_honors_known_exclusions():
    system = lab()
    request = Request(['engineering'], limit=3, feedback={'Q100': {'known': True}})
    assert [r['concept_id'] for r in system.recommend(request, 'BM25')['recommendations']] == ['Q101', 'Q102', 'Q103']
    assert system.recommend(Request(['astronomy']), 'BM25')['recommendations'] == []


def test_random_baseline_is_seeded_and_never_includes_known_concepts():
    system = lab()
    request = Request(['engineering'], limit=6, seed=41, feedback={'Q100': {'known': True}})
    first = system.recommend(request, 'random')['recommendations']
    assert first == system.recommend(request, 'random')['recommendations']
    assert len({r['concept_id'] for r in first}) == 6
    assert 'Q100' not in {r['concept_id'] for r in first}
    request.seed = 42
    assert first != system.recommend(request, 'random')['recommendations']


def test_named_models_preserve_the_frozen_shortlist_configurations():
    from recommendation_lab.models import get_model
    from recommendation_lab.systems import RankConfig

    assert get_model('K-connection').config == RankConfig(relevance=.95, content=.05, novelty=0., diversity=.05)
    assert get_model('K-literal').config == RankConfig(relevance=.65, content=.2, novelty=.15, diversity=.15, literal_weight=.75)
    assert get_model('V0').variant == 'V0'
    with pytest.raises(ValueError, match='Unknown'):
        get_model('invented')
