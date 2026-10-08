import json

import pytest

from recommendation_lab.benchmark import (cache_identity, validate_profiles, SearchBudget,
    bounded_search, seal_finalists, claim_heldout, evaluation_space, run_cases, paired_uncertainty, write_json)


def test_cache_key_changes_with_revision_and_encoding_contract():
    a = cache_identity(['a'], dict(model='mpnet',revision='one',normalize=True))
    assert a != cache_identity(['a'],dict(model='mpnet',revision='two',normalize=True))
    assert a != cache_identity(['a'],dict(model='mpnet',revision='one',normalize=False))


def test_profile_families_cannot_cross_splits():
    profiles = [dict(id='one',family='same',split='development',interests=['a']),
                dict(id='two',family='same',split='heldout',interests=['b'])]
    with pytest.raises(ValueError,match='family'):
        validate_profiles(profiles)
    profiles[1]['family'] = 'different'
    validate_profiles(profiles)


def test_bounded_search_stops_on_patience_and_never_reads_heldout():
    attempted = []
    def evaluate(config, profiles):
        attempted.append(config)
        assert all(p['split'] == 'development' for p in profiles)
        return dict(connection=.5,discovery=.4,depth=.3,variety=.2)
    result = bounded_search(list(range(100)), [dict(split='development')], evaluate,
                            SearchBudget(rounds=5,per_round=2,patience=2,min_gain=.01))
    assert len(attempted) == 6  # initial round plus two unchanged rounds
    assert result['stop_reason'] == 'patience'
    assert result['champions']['discovery'] == 0
    with pytest.raises(ValueError,match='development'):
        bounded_search([1],[dict(split='heldout')],evaluate)


def test_missing_grades_do_not_nominate_a_winner():
    result = bounded_search([1,2], [dict(split='development')],
        lambda c,p:dict(connection=None,discovery=None,depth=None,variety=None))
    assert all(v is None for v in result['champions'].values())
    assert result['stop_reason'] == 'exhausted'


def test_heldout_is_claimed_once_and_finalist_changes_need_a_new_cycle(tmp_path):
    nomination = seal_finalists(tmp_path, {'discovery':'V3'}, {'benchmark':'one','evaluator':'one'})
    receipt = claim_heldout(tmp_path, nomination)
    assert receipt['nomination_digest'] == nomination['digest']
    with pytest.raises(ValueError,match='already'):
        claim_heldout(tmp_path,nomination)
    with pytest.raises(ValueError,match='frozen'):
        seal_finalists(tmp_path, {'discovery':'V2'}, {'benchmark':'one','evaluator':'one'})


def test_diversity_space_is_separate_and_content_versioned():
    vectors, identity = evaluation_space({'a':'soil ecology', 'b':'soil compost', 'c':'computer graphics'})
    assert set(vectors) == {'a','b','c'}
    assert identity['method'] == 'hashed-tfidf-v1'
    _, changed = evaluation_space({'a':'new content','b':'soil compost','c':'computer graphics'})
    assert identity != changed


def test_benchmark_measures_warm_serving_separately_from_first_request():
    class FixtureLab:
        inventory = type('Inventory',(),{'version':'fixture'})()
        calls = 0
        def recommend(self,request,variant,config):
            self.calls += 1
            return dict(recommendations=[],execution=dict(seconds=.8 if self.calls == 1 else .1))
    result = run_cases(FixtureLab(),[dict(id='one',interests=['engineering'])],[dict(name='V3',variant='V3')])
    assert result[0]['batch']['execution']['seconds'] == .1
    assert result[0]['batch']['execution']['first_request_seconds'] == .8


def test_bootstrap_resamples_families_and_preserves_filtered_profile_keys():
    records = []
    for system in ('V0','new'):
        for pid,score in [('missing',None),('one',.1 if system == 'V0' else .4),('two',.2 if system == 'V0' else .5)]:
            records.append(dict(system=system,profile_id=pid,family='same',scores={'discovery':score}))
    result = paired_uncertainty(records,{'discovery':'new'})['discovery']
    assert result['independent_families'] == 1
    assert result['profile_deltas'] == pytest.approx({'one':.3,'two':.3})


def test_concurrent_json_writes_have_private_temporary_files(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    path = tmp_path/'report.json'
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(lambda i:write_json(path,{'value':i}),range(20)))
    assert json.loads(path.read_text())['value'] in range(20)
    assert not list(tmp_path.glob('*.tmp'))


def test_concurrent_identical_nominations_publish_complete_json_once(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _:seal_finalists(tmp_path,{'discovery':'V3'},{'benchmark':'one'}),range(30)))
    assert all(value == results[0] for value in results)
    assert json.loads((tmp_path/'nomination.json').read_text()) == results[0]


def test_nomination_filename_is_invisible_until_json_is_complete(tmp_path,monkeypatch):
    import threading
    from concurrent.futures import ThreadPoolExecutor
    from recommendation_lab import benchmark
    ready,release = threading.Event(),threading.Event()
    original = benchmark.json.dump
    def delayed(value,stream,*args,**kwargs):
        ready.set()
        release.wait(2)
        return original(value,stream,*args,**kwargs)
    monkeypatch.setattr(benchmark.json,'dump',delayed)
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(seal_finalists,tmp_path,{'discovery':'V3'},{'benchmark':'one'})
        try:
            assert ready.wait(2)
            assert not (tmp_path/'nomination.json').exists()
        finally:
            release.set()
        assert future.result()['champions']['discovery'] == 'V3'


def test_nomination_preserves_broad_and_specific_metric_champions(tmp_path):
    import json
    from argparse import Namespace
    from recommendation_lab.__main__ import tune, DEFAULT_EVALUATOR
    from recommendation_lab.evaluation import METRICS
    run=tmp_path/'development'
    run.mkdir()
    names=['V0','V1','V2','V3','specific-winner','broad-winner']
    manifest=dict(split='development',systems=[dict(name=name,variant='V3',config={}) for name in names],
                  profiles_sha256='profiles',code_sha256='code',runtime_fingerprint='runtime',
                  evaluator=DEFAULT_EVALUATOR.identity(),packet_id='packet')
    profiles=[dict(id='specific',family='one',split='development',interests=['example']),
              dict(id='broad',family='one',split='development',interests=['example'],controls=dict(result_kind='broad'))]
    def table(winner):
        return dict(systems={name:dict(eligible_for_selection=True,**{metric:.9 if name==winner else .1 for metric in METRICS}) for name in names})
    report=dict(**table('specific-winner'),by_kind=dict(specific=table('specific-winner'),broad=table('broad-winner')))
    for name,document in [('manifest.json',manifest),('outputs.json',[dict(system='V0',profile=p) for p in profiles]),('scoreboard.json',report)]:
        (run/name).write_text(json.dumps(document))
    cycle=tmp_path/'cycle'
    tune(Namespace(run=run,cycle=cycle,rounds=5,per_round=20,patience=2))
    nomination=json.loads((cycle/'nomination.json').read_text())
    assert {s['name'] for s in nomination['identity']['finalist_systems']}==set(names)
    assert set(nomination['identity']['track_champions']['broad'].values())=={'broad-winner'}
