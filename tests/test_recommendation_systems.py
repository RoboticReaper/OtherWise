import math

import numpy as np
import pytest

from recommendation_lab.inventory import Inventory
from recommendation_lab.systems import RecommendationLab, Request, RankConfig, VARIANTS


def vec(distance):
    return [math.cos(math.pi * distance), math.sin(math.pi * distance)]


class FixtureEncoder:
    def encode(self, texts, **kwargs):
        return np.asarray([vec(.31) if t.startswith('second') else vec(0) for t in texts])


def lab(count=12):
    broad = [dict(topic=f'concept {i}', description=f'An engineering method {i}.', domain='Engineering',
                  source='Wikidata', wikidata_id=f'Q{i+100}') for i in range(count)]
    nodes = [dict(r, id=r['wikidata_id'], kind='concept', level=None) for r in broad]
    nodes += [dict(id=f'cat{i}', topic=f'area {i}', description='Engineering area.', kind='category') for i in range(count)]
    areas = [dict(id=f'area{i}', topic=f'area {i}', description='Engineering area.', domain='Engineering',
                  category_id=f'cat{i}') for i in range(count)]
    graph = dict(version=1, nodes=nodes, areas=areas,
                 edges=[dict(source=f'cat{i}', target=f'Q{i+100}', relation='contains_concept') for i in range(count)])
    vectors = np.asarray([vec(.30 + .001*i) for i in range(count)])
    inv = Inventory.from_sources(broad, graph)
    return RecommendationLab(inv, broad, graph, FixtureEncoder(), vectors, vectors,
                             np.asarray([vec(0)] * count), model_identity={'revision': 'fixture'})


def test_all_area_control_recovers_eligible_concepts_outside_router():
    system = lab()
    v0 = system.recommend(Request(['engineering'], limit=12), 'V0')
    v1 = system.recommend(Request(['engineering'], limit=12), 'V1')
    assert len(v0['recommendations']) == 8
    assert len(v1['recommendations']) == 12
    assert v0['diagnostics']['eligible_recall'] == pytest.approx(8/12)
    assert v1['diagnostics']['eligible_recall'] == 1


def test_ambiguous_meaning_returns_no_list_and_explicit_known_alias_is_excluded():
    system = lab()
    system.inventory.aliases['ambiguous'] = {'Q100', 'Q101'}
    response = system.recommend(Request(['ambiguous']), 'V2')
    assert response['status'] == 'clarification_needed'
    assert response['recommendations'] == []
    chosen = Request([dict(phrase='ambiguous', concept_id='Q100')], inventory_version=system.inventory.version)
    assert 'Q100' not in {r['concept_id'] for r in system.recommend(chosen, 'V2')['recommendations']}


def test_global_eligibility_is_applied_before_retrieval_pool_truncation():
    system = lab()
    system.concept_vectors[0] = vec(.05)
    response = system.recommend(Request(['engineering'], limit=1), 'V3', RankConfig(pool_limit=1))
    assert len(response['recommendations']) == 1
    assert response['recommendations'][0]['concept_id'] != 'Q100'


def test_path_mode_enforces_lower_bound_against_other_interest():
    system = lab()
    result = system.recommend(Request(['engineering', 'second'], mode='path', focus_index=0), 'V3')
    assert result['recommendations'] == []


def test_sparse_actual_overlap_cap_and_seed_reproducibility():
    system = lab(3)
    system.concept_vectors[:] = [vec(.27), vec(.27), vec(.31)]
    system.broad_vectors[:] = system.concept_vectors
    request = Request(['engineering'], randomness=.02)
    a = system.recommend(request, 'V3')
    b = system.recommend(request, 'V3')
    assert a['recommendations'] == b['recommendations']
    assert len(a['recommendations']) == 1
    assert a['recommendations'][0]['zone'] == 'New territory'


def test_feedback_stays_independent_and_exposure_reservation_has_provenance():
    system = lab()
    request = Request(['engineering'], limit=5, feedback={'Q100': {'known': True},
                      'Q101': {'curious': True, 'difficulty': 'too_hard'}},
                      exposures={f'area{i}': 10 if i else 0 for i in range(12)})
    rows = system.recommend(request, 'V3')['recommendations']
    assert 'Q100' not in {r['concept_id'] for r in rows}
    for row in rows:
        assert row['graph']['path_ids'][-1] == row['concept_id']
        assert row['sources']
    assert any(r['exploration_pick'] for r in rows)


def test_fts_index_failure_is_not_a_silent_ablation():
    system = lab()
    system.lexical = None
    with pytest.raises(RuntimeError, match='Lexical'):
        system.recommend(Request(['engineering']), 'V3')
    assert system.recommend(Request(['engineering']), 'V3-no-lexical')['status'] == 'ok'


def test_goal_and_config_variants_are_validated():
    system = lab()
    assert {'V0', 'V1', 'V2', 'V3', 'V3-no-lexical', 'V3-no-graph', 'V3-no-ranking'} <= set(VARIANTS)
    for bad in [Request(['engineering'], goal='unknown'), Request(['engineering'], limit=True),
                Request(['engineering'], radius=float('nan')), Request(['engineering'], mode='path'),
                Request(['engineering'], seed=-1), Request(['engineering'], feedback={'forged': {'known': True}})]:
        with pytest.raises(ValueError):
            system.recommend(bad, 'V3')


def test_external_order_requires_exact_id_permutation_and_falls_back():
    system = lab()
    request = Request(['engineering'], limit=5)
    baseline = system.recommend(request, 'V3')
    invalid = system.recommend(request, 'V4b', reranker=lambda payload, timeout: ['invented'])
    assert invalid['recommendations'] == baseline['recommendations']
    assert invalid['execution']['external_status'] == 'invalid_output'
    valid = system.recommend(request, 'V4b', reranker=lambda payload, timeout: list(reversed(payload['ids'])))
    assert [r['concept_id'] for r in valid['recommendations']] == list(reversed([r['concept_id'] for r in baseline['recommendations']]))


def test_adaptive_arm_is_explicit_and_does_not_change_hard_band_variants():
    system = lab(3)
    system.concept_vectors[:] = [vec(.05),vec(.42),vec(.48)]
    request = Request(['engineering'])
    assert system.recommend(request,'V3')['recommendations'] == []
    adaptive = system.recommend(request,'V3-adaptive')
    assert {r['concept_id'] for r in adaptive['recommendations']} == {'Q101','Q102'}
    assert adaptive['execution']['eligibility_policy'] == 'adaptive-experiment-v1'


def test_broad_path_legacy_ranker_uses_only_one_focus_vector():
    system = lab()
    response = system.recommend(Request(['engineering','unrelated'],result_kind='broad',mode='path',focus_index=0),'V2')
    assert response['recommendations']
