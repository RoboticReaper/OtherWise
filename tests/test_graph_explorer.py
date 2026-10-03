import math
import numpy as np
import pytest

import graph_explorer as g
from feedback import new_profile, set_feedback


def fixture():
    areas = [dict(id=a, topic=a, description=a, domain=a, category_id='cat:'+a) for a in ['cs', 'music']]
    nodes = [dict(id='cat:'+a, topic=a, description=a, kind='category') for a in ['cs', 'music']]
    nodes += [dict(id=f'Q{i}', topic=f'Concrete {i}', description=f'Example {i}', kind='concept', level=level)
              for i, level in enumerate([1, 2, 3, 1, 2, 3, 2, None])]
    edges = [dict(source='cat:'+('cs' if i<4 else 'music'), target=f'Q{i}', relation='contains_concept', source_url='https://example.org/source') for i in range(8)]
    return dict(version=1, areas=areas, nodes=nodes, edges=edges)


def vec(distances):
    a=np.array(distances)*np.pi
    return np.column_stack([np.cos(a),np.sin(a)])


def run(graph=None, distances=None, **kw):
    opts=dict(radius=.25, expansion=.15, overlap=0, top_k=4, diversity=0, randomness=0, exploration_fraction=0)
    opts.update(kw)
    return g.recommend_specific(graph or fixture(), vec(distances if distances is not None else [.325]*8), ['Interest'], [[1,0]], **opts)


def test_real_paths_cycle_safety_and_multi_parent_deduplication():
    graph=fixture()
    graph['edges'] += [dict(source='cat:cs',target='cat:music',relation='contains_category'),
                       dict(source='cat:music',target='cat:cs',relation='contains_category')]
    rows=g.graph_candidates(graph,['cs'],max_depth=3)
    assert len(rows)==8
    assert next(r for r in rows if r['id']=='Q4')['paths']['cs']==['cat:cs','cat:music','Q4']
    assert len(g.graph_candidates(graph,['cs'],max_depth=1))==4
    assert all(r['kind']=='concept' for r in rows)


def test_final_concepts_obey_band_even_if_parent_was_selected_and_sparse_overlap_cap():
    rows=run(distances=[.1,.24,.27,.3,.32,.37,.4,.6], radius=.25,expansion=.15,overlap=.02,top_k=10)
    assert {r['id'] for r in rows}=={'Q1','Q2','Q3','Q4','Q5','Q6'}
    assert sum(r['zone']=='Familiar overlap' for r in rows)==1
    assert all(.23-1e-9<=r['distance']<=.4+1e-9 for r in rows)
    assert run(distances=[.1]*8)==[]


def test_known_excludes_only_rated_concept_and_curiosity_is_separate():
    p=new_profile()
    set_feedback(p,'Q0',curious=True,known=True,area_ids=['cs'])
    rows=run(profile=p,top_k=8)
    assert 'Q0' not in {r['id'] for r in rows}
    assert {'Q1','Q2','Q3'} <= {r['id'] for r in rows}
    set_feedback(p,'Q0',curious=True,known=False,area_ids=['cs'])
    assert run(profile=p,top_k=1)[0]['id']=='Q0'


def test_difficulty_changes_local_ranking_without_turning_hard_into_dislike():
    p=new_profile()
    set_feedback(p,'Q1',curious=True,difficulty='too_hard',level=2,area_ids=['cs'])
    rows=run(profile=p,area_ids=['cs'],top_k=4)
    assert rows[0]['level']==1
    cs_adjust={r['id']:r['score_parts']['difficulty'] for r in rows}
    assert cs_adjust['Q0']>cs_adjust['Q2']
    assert all(r['score_parts']['difficulty']==0 for r in run(profile=p,area_ids=['music']))
    set_feedback(p,'Q1',curious=True,difficulty='too_basic',level=2,area_ids=['cs'])
    assert run(profile=p,area_ids=['cs'],top_k=1)[0]['id']=='Q2'


def test_exploration_reserve_survives_strong_positive_feedback_on_one_branch():
    p=new_profile(); p['exposures']={'cs':30,'music':0}
    for i in range(4):set_feedback(p,f'Q{i}',curious=True,area_ids=['cs'])
    baseline=run(profile=p,top_k=4,exploration_fraction=0)
    reserved=run(profile=p,top_k=4,exploration_fraction=.5)
    assert sum(r['area_id']=='music' for r in reserved)>=2
    assert sum(r['area_id']=='music' for r in reserved)>sum(r['area_id']=='music' for r in baseline)
    assert sum(r['exploration_pick'] for r in reserved)>=2


def test_random_seed_repeats_but_never_bypasses_known_or_distance_filters():
    p=new_profile();set_feedback(p,'Q0',known=True)
    args=dict(profile=p,randomness=.05,seed=42)
    a=run(**args)
    assert a==run(**args)
    assert all(r['id']!='Q0' for r in a)
    assert a!=run(profile=p,randomness=.05,seed=11)
    assert run(randomness=0,seed=1)==run(randomness=0,seed=99)


def test_known_feedback_preserves_other_concepts_random_draws():
    before=run(top_k=8,randomness=.03,seed=42)
    profile=new_profile();set_feedback(profile,'Q0',known=True)
    after=run(top_k=8,randomness=.03,seed=42,profile=profile)
    original={r['id']:r['score_parts']['randomness'] for r in before}
    assert all(r['score_parts']['randomness']==original[r['id']] for r in after)


def test_unreviewed_levels_are_not_inferred_from_graph_depth():
    p=new_profile();set_feedback(p,'Q5',difficulty='too_hard',level=3,area_ids=['music'])
    row=next(r for r in run(profile=p,top_k=8) if r['id']=='Q7')
    assert row['level'] is None
    assert row['score_parts']['difficulty']==0


def test_area_routing_considers_multiple_queries():
    ids=g.select_areas(fixture()['areas'], [[1,0],[0,1]], [[1,0],[0,1]],limit=2)
    assert set(ids)=={'cs','music'}


@pytest.mark.parametrize('args',[{'radius':float('nan')},{'exploration_fraction':1.1},{'top_k':True},{'area_ids':['missing']},{'seed':-1}])
def test_invalid_options_are_rejected(args):
    with pytest.raises(ValueError):run(**args)
