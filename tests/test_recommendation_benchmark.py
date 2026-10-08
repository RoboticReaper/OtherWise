import json

import pytest

from recommendation_lab.benchmark import (cache_identity, validate_profiles, SearchBudget,
    bounded_search, seal_finalists, claim_heldout, evaluation_space, run_cases)


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
