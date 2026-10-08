import numpy as np
import pytest

from test_recommendation_systems import lab, vec
from recommendation_lab.inventory import Inventory
from recommendation_lab.systems import RecommendationLab, Request, RankConfig


def fixture(descriptions, distances):
    original = lab(len(descriptions))
    for i, description in enumerate(descriptions):
        original.broad[i]['description'] = description
        original.graph['nodes'][i]['description'] = description
    inventory = Inventory.from_sources(original.broad, original.graph)
    vectors = np.asarray([vec(distance) for distance in distances])
    return RecommendationLab(inventory, original.broad, original.graph, original.model,
                             vectors, vectors, original.area_vectors, model_identity={'revision':'fixture'})


@pytest.mark.parametrize('kind',['broad','specific'])
def test_known_policy_keeps_close_unknown_concepts_and_declares_changed_constraints(kind):
    system = fixture(['an engineering method']*3,[.10,.15,.60])
    request = Request(['engineering'],result_kind=kind,limit=3)
    assert system.recommend(request,'V3')['recommendations'] == []
    response = system.recommend(request,'V5-known')
    assert {r['concept_id'] for r in response['recommendations']} == {'Q100','Q101'}
    assert response['execution']['eligibility_policy'] == 'known-concept-experiment-v1'
    assert response['execution']['overlap_policy'] == 'geometric-diagnostic-only'
    assert all(r['zone']=='Familiar overlap' for r in response['recommendations'])
    assert response['diagnostics']['duplicate_count'] == 0


def test_known_policy_preserves_explicit_known_feedback_and_clarification():
    system = fixture(['an engineering method']*3,[.10,.15,.20])
    response = system.recommend(Request(['engineering'],feedback={'Q100':{'known':True}}),'V5-known')
    assert 'Q100' not in {r['concept_id'] for r in response['recommendations']}
    system.inventory.aliases['ambiguous'] = {'Q101','Q102'}
    assert system.recommend(Request(['ambiguous']),'V5-known')['status']=='clarification_needed'


def test_content_and_relevance_rankers_choose_different_learning_units():
    system = fixture(['a professional engineering association',
                      'an engineering algorithm that solves a design problem'],[.15,.20])
    connection = system.recommend(Request(['engineering'],limit=1),'V5-known',
                                  RankConfig(relevance=1,content=0,novelty=0,diversity=0))
    depth = system.recommend(Request(['engineering'],limit=1),'V5-known',
                             RankConfig(relevance=0,content=1,novelty=0,diversity=0))
    assert connection['recommendations'][0]['concept_id']=='Q100'
    assert depth['recommendations'][0]['concept_id']=='Q101'
    assert depth['recommendations'][0]['score_parts']['content'] > 0
    assert depth['recommendations'][0]['sources']==system.inventory.concepts['Q101']['records']


def test_goal_specific_rankers_and_seeded_outputs_are_reproducible():
    system = fixture(['an engineering association','an algorithm that solves a problem',
                      'a method used to build a machine'],[.15,.20,.30])
    request = Request(['engineering'],goal='depth',randomness=.01)
    first = system.recommend(request,'V5-known')
    repeat = system.recommend(request,'V5-known')
    assert first['recommendations']==repeat['recommendations']
    assert first['recommendations'][0]['topic']!='concept 0'


def test_known_policy_path_relevance_uses_focus_and_keeps_orphan_sources():
    system = lab(2)
    system.concept_vectors[:]=system.broad_vectors[:]=[vec(.10),vec(.40)]
    system.graph['edges']=[]
    system.reached={}
    result=system.recommend(Request(['engineering','second'],mode='path',focus_index=0,limit=1),
                            'V5-known',RankConfig(relevance=1,content=0,novelty=0,diversity=0))
    assert result['recommendations'][0]['concept_id']=='Q100'
    assert result['recommendations'][0]['graph'] is None


@pytest.mark.parametrize('config',[dict(content=-1),dict(content=True),dict(literal_weight=float('nan')),dict(literal_weight=None),
                                    dict(distance_cap=0),dict(distance_cap=.9)])
def test_new_policy_configuration_is_bounded(config):
    with pytest.raises(ValueError):
        lab().recommend(Request(['engineering']),'V5-known',RankConfig(**config))
