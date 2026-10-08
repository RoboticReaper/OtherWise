import copy

import numpy as np
import pytest

from recommendation_lab.evaluation import Evaluator, GradeStore, grade_key, make_packet, score_batch, scoreboard


PROFILE = dict(id='fixture', family='fixture', interests=['engineering'], background=None, known_ids=[])
EVALUATOR = Evaluator('fixture-evaluator', 'rubric-v0', 'fixed prompt')


def row(cid='Q1', topic='Method', description='An engineering method.'):
    return dict(concept_id=cid, topic=topic, description=description,
                sources=[dict(source_url=f'https://www.wikidata.org/wiki/{cid}')])


def store_for(rows, values=(3,3,3,None)):
    store = GradeStore(EVALUATOR)
    for r in rows:
        store.add(PROFILE, r, dict(C=values[0], N=values[1], E=values[2], A=values[3],
                  bridge='Engineering method extends the stated interest.', reason='A specific method to explore.'))
    return store


def test_exact_formulas_requested_slots_and_independent_variety_space():
    rows = [row('Q1'), row('Q2', 'Other method')]
    scores = score_batch(PROFILE, dict(status='ok', recommendations=rows), store_for(rows),
                         {'Q1':[1,0], 'Q2':[0,1]}, limit=10)
    assert scores['connection'] == pytest.approx(.2)
    assert scores['discovery'] == pytest.approx(.19)
    assert scores['depth'] == pytest.approx(.185)
    assert scores['variety'] == pytest.approx(.16)  # .6*.2 + .4*.2*.5
    assert scores['accessibility_unknown'] == 2


def test_duplicate_known_and_unsupported_rows_cannot_inflate_scores():
    a,b,c = row('Q1'),row('Q2'),row('Q3')
    c['sources'] = []
    profile = dict(PROFILE, known_ids=['Q2'])
    store = GradeStore(EVALUATOR)
    store.add(profile, a, dict(C=3,N=3,E=3,A=None,bridge='Engineering method.',reason='Specific.'))
    result = score_batch(profile, dict(status='ok',recommendations=[a,a,b,c]), store, {'Q1':[1,0]},limit=10)
    assert result['connection'] == pytest.approx(.1)
    assert result['integrity_failures'] == 3


def test_false_bridge_or_low_connection_fails_shared_gate():
    rows = [row()]
    store = store_for(rows, (1,3,3,None))
    assert score_batch(PROFILE, dict(status='ok',recommendations=rows), store, {'Q1':[1,0]})['discovery'] == 0
    store = GradeStore(EVALUATOR)
    store.add(PROFILE, rows[0], dict(C=3,N=3,E=3,A=None,bridge='',reason='No evidence for a bridge.'))
    assert score_batch(PROFILE, dict(status='ok',recommendations=rows), store, {'Q1':[1,0]})['connection'] == 0


def test_missing_or_stale_grades_make_score_unavailable():
    r = row()
    store = store_for([r])
    changed = dict(r, description='Changed presentation.')
    score = score_batch(PROFILE, dict(status='ok',recommendations=[changed]), store, {'Q1':[1,0]})
    assert score['discovery'] is None
    assert score['missing_grades'] == 1
    assert grade_key(PROFILE,r,EVALUATOR) != grade_key(PROFILE,changed,EVALUATOR)
    assert grade_key(PROFILE,r,EVALUATOR) != grade_key(PROFILE,r,Evaluator('other','rubric-v0','fixed prompt'))


def test_packet_is_blinded_deduplicated_and_import_is_bound_to_identity():
    r = row()
    runs = [dict(profile=PROFILE, batch=dict(algorithm='secret',recommendations=[r]))] * 2
    packet = make_packet(runs,EVALUATOR,seed=42)
    assert len(packet['items']) == 1
    assert 'algorithm' not in str(packet)
    item = packet['items'][0]
    grades = dict(packet_id=packet['packet_id'],evaluator=packet['evaluator'],ratings=[dict(
        key=item['key'],C=3,N=2,E=2,A=None,bridge='Engineering method.',reason='Explore a method.')])
    imported = GradeStore.from_packet(packet, grades)
    assert imported.get(PROFILE,r)['N'] == 2
    bad = copy.deepcopy(grades)
    bad['ratings'][0]['key'] = 'forged'
    with pytest.raises(ValueError):
        GradeStore.from_packet(packet,bad)


def test_cross_metric_champions_refuse_incomplete_systems():
    records = [dict(system='A', profile_id='one', scores=dict(connection=.8,discovery=.5,depth=.6,variety=.4),seconds=.1,cost_usd=0.),
               dict(system='B', profile_id='one', scores=dict(connection=.6,discovery=.7,depth=.7,variety=.6),seconds=.2,cost_usd=0.),
               dict(system='incomplete',profile_id='one',scores=dict.fromkeys(['connection','discovery','depth','variety']),seconds=.01,cost_usd=0.)]
    result = scoreboard(records)
    assert result['champions'] == dict(connection='A',discovery='B',depth='B',variety='B')
    assert result['systems']['incomplete']['eligible_for_selection'] is False
    assert set(result['pareto']) == {'A','B'}


def test_integrity_failure_still_reports_penalized_baseline_score():
    result = scoreboard([dict(system='baseline',profile_id='one',scores=dict(connection=.2,discovery=.1,
        depth=.1,variety=.1,integrity_failures=1),seconds=.1,cost_usd=0.)])
    assert result['systems']['baseline']['connection'] == .2
    assert result['systems']['baseline']['eligible_for_selection'] is False


def test_fabricated_identity_or_mismatched_source_cannot_pass_integrity():
    fake = dict(row('not-inventory'),sources=[dict(source_url='https://example.invalid/fake',source_id='Q900')])
    result = score_batch(PROFILE,dict(status='ok',recommendations=[fake]),store_for([fake]),{'not-inventory':[1,0]})
    assert result['integrity_failures'] == 1
    assert result['connection'] == 0


def test_import_rejects_conflicts_with_existing_frozen_grades():
    packet = make_packet([dict(profile=PROFILE,batch=dict(recommendations=[row()]))],EVALUATOR)
    rating = dict(key=packet['items'][0]['key'],C=3,N=2,E=2,A=None,bridge='Engineering method.',reason='Specific method.')
    initial = dict(packet_id=packet['packet_id'],evaluator=packet['evaluator'],ratings=[rating])
    store = GradeStore.from_packet(packet,initial)
    changed = dict(initial,ratings=[dict(rating,C=2)])
    with pytest.raises(ValueError,match='Conflicting'):
        GradeStore.from_packet(packet,changed,existing=store.to_dict())


def test_invalid_empty_batch_and_wrong_automatic_sense_are_not_selectable():
    from recommendation_lab.inventory import Inventory
    inv = Inventory.from_sources([dict(topic='anchor',description='Engineering anchor.',wikidata_id='Q1'),
                                  dict(topic='method',description='Engineering method.',wikidata_id='Q2')],dict(nodes=[]))
    profile = dict(PROFILE,interests=['anchor'])
    bad = dict(schema_version=2,inventory_version='stale',status='ok',resolutions=[],recommendations=[])
    score = score_batch(profile,bad,GradeStore(EVALUATOR),{},inventory=inv)
    assert score['integrity_failures'] >= 1
    report = scoreboard([dict(system='bad',profile_id='one',scores=score,seconds=.1,cost_usd=0.)])
    assert report['systems']['bad']['eligible_for_selection'] is False
    candidate = dict(concept_id='Q2',topic='method',description='Engineering method.',sources=inv.concepts['Q2']['records'])
    store = GradeStore(EVALUATOR)
    store.add(profile,candidate,dict(C=3,N=2,E=2,A=None,bridge='Engineering method.',reason='Specific method.'))
    wrong = dict(schema_version=2,inventory_version=inv.version,status='ok',algorithm='V3',
                 resolutions=[dict(status='resolved',concept_id='Q3')],recommendations=[candidate])
    score = score_batch(profile,wrong,store,{'Q2':[1,0]},inventory=inv)
    assert score['integrity_failures'] >= 1
    assert score['connection'] == 0


@pytest.mark.parametrize('grade', [dict(C=True,N=2,E=2,A=None),dict(C=4,N=2,E=2,A=None),dict(C=2,N=2,E=2,A=.5)])
def test_invalid_grades_are_rejected(grade):
    with pytest.raises(ValueError):
        GradeStore(EVALUATOR).add(PROFILE,row(),dict(grade,bridge='Bridge',reason='Reason'))
