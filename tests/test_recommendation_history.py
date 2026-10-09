"""Dated recommendations tested with independent, worked angular fixtures."""
import math

import numpy as np
import pytest
from dataclasses import replace

from recommendation_lab.systems import Request
from test_recommendation_systems import lab, vec


def history_lab():
    system = lab(4)
    positions = {'start': -.10, 'middle': 0., 'latest': .10, 'other': .85}

    class Encoder:
        def encode(self, texts, **kwargs):
            return np.asarray([vec(positions.get(text, 0.)) for text in texts])

    system.model = Encoder()
    system.concept_vectors[:] = [vec(-.20), vec(.21), vec(.4), vec(.85)]
    system.broad_vectors[:] = system.concept_vectors
    return system


HISTORY = [dict(phrase='start', date='2026-09-01'),
           dict(phrase='middle', date='2026-09-11'),
           dict(phrase='latest', date='2026-09-21')]


def test_trajectory_prefers_the_forward_branch_beyond_recency_only():
    system = history_lab()
    request = Request(HISTORY, limit=1, exploration_fraction=0, diversity=0)
    recent = system.recommend(request, 'history-recency')
    trajectory = system.recommend(request, 'trajectory')
    assert recent['recommendations'][0]['concept_id'] == 'Q100'
    assert trajectory['recommendations'][0]['concept_id'] == 'Q101'
    assert trajectory['execution']['history']['velocity_used'] is True


def test_dates_are_optional_for_static_models_and_dated_repeats_are_known():
    system = lab()
    dated = Request([dict(phrase='engineering', date='2026-09-01'),
                     dict(phrase='engineering', date='2026-09-11')])
    assert system.recommend(dated, 'V3')['recommendations'] == system.recommend(Request(['engineering']), 'V3')['recommendations']
    known = Request([dict(phrase='concept 0', date='2026-09-01'), dict(phrase='concept 0', date='2026-09-11'), 'engineering'])
    assert 'Q100' not in {r['concept_id'] for r in system.recommend(known, 'trajectory')['recommendations']}


def test_temporal_order_comes_from_dates_and_independent_interests_remain_separate():
    system = history_lab()
    request = Request(HISTORY + [dict(phrase='other', date='2026-09-10')], limit=3)
    result = system.recommend(request, 'trajectory')
    shuffled = system.recommend(replace(request, interests=list(reversed(request.interests))), 'trajectory')
    assert [r['concept_id'] for r in result['recommendations']] == [r['concept_id'] for r in shuffled['recommendations']]
    assert [r['score_parts'] for r in result['recommendations']] == [r['score_parts'] for r in shuffled['recommendations']]
    assert result['execution']['history']['strand_count'] == 2
    assert sum(s['direction_status'] == 'usable' for s in result['execution']['history']['strands']) == 1


@pytest.mark.parametrize('interests', [
    ['start', 'middle', 'latest'],
    [dict(item, date='2026-09-01') for item in HISTORY],
    HISTORY[:2],
    [dict(phrase='middle', date=item['date']) for item in HISTORY],
])
def test_missing_sparse_equal_date_or_stationary_history_has_explicit_static_fallback(interests):
    system = history_lab()
    request = Request(interests, limit=2)
    trajectory = system.recommend(request, 'trajectory')
    recent = system.recommend(request, 'history-recency')
    assert trajectory['recommendations'] == recent['recommendations']
    assert trajectory['execution']['history']['velocity_used'] is False
    assert trajectory['execution']['history']['fallback'] == 'recency_only'


def test_path_mode_uses_its_own_strand_but_excludes_all_known_interests():
    system = history_lab()
    request = Request(HISTORY + [dict(phrase='other', date='2026-09-10')], mode='path', focus_index=3)
    result = system.recommend(request, 'trajectory')
    assert result['execution']['history']['velocity_used'] is False
    assert all(row['nearest_interest_distance'] > .035 for row in result['recommendations'])
    assert 'Q103' not in {row['concept_id'] for row in result['recommendations']}


@pytest.mark.parametrize('date', ['2026-02-30', '2026-2-1', '20260901', '2026-09-01T12:00:00',
                                '2026-09-01T00:00:00+00:99', '2026-09-01T00:00:00+24:00',
                                '2026-09-01T00:00:00-01:60', 42, True, 'private invalid date'])
def test_invalid_dates_are_rejected_even_by_static_models(date):
    with pytest.raises(ValueError):
        history_lab().recommend(Request([dict(phrase='start', date=date)]), 'V3')


def test_timezone_equivalent_observations_cannot_create_velocity():
    history = [dict(phrase='start', date='2026-09-01T00:00:00Z'),
               dict(phrase='middle', date='2026-08-31T19:00:00-05:00'),
               dict(phrase='latest', date='2026-09-01T02:00:00+02:00')]
    result = history_lab().recommend(Request(history), 'trajectory')
    assert result['execution']['history']['velocity_used'] is False


def test_extremely_old_observations_have_finite_static_fallback():
    import json
    history = [dict(phrase='start', date='0001-01-01'),
               dict(phrase='middle', date='2000-01-01'),
               dict(phrase='latest', date='9999-01-01')]
    result = history_lab().recommend(Request(history, history_config={'half_life_days': 1}), 'trajectory')
    json.dumps(result, allow_nan=False)
    assert result['execution']['history']['velocity_used'] is False


@pytest.mark.parametrize('repeat_latest', [False, True])
def test_repeating_an_unchanged_set_of_interests_cannot_invent_velocity(repeat_latest):
    system = history_lab()

    class Encoder:
        def encode(self, texts, **kwargs):
            positions = {'first': 0., 'second': .2, 'third': .4}
            return np.asarray([vec(positions.get(text, 0.)) for text in texts])

    system.model = Encoder()
    history = [dict(phrase=phrase, date=date)
               for date in ('2026-09-01', '2026-09-11', '2026-09-21')
               for phrase in ('first', 'second', 'third')]
    if repeat_latest:
        history += [dict(phrase='third', date='2026-09-21')] * 3
    request = Request(history, limit=3)
    result = system.recommend(request, 'trajectory')
    assert result['execution']['history']['velocity_used'] is False
    assert result['execution']['history']['direction_available'] is False
    assert result['recommendations'] == system.recommend(request, 'history-recency')['recommendations']


@pytest.mark.parametrize('variant', ['history-recency', 'trajectory', 'V5-known'])
def test_dated_aliases_choose_static_anchors_independently_of_input_order(variant):
    system = history_lab()
    system.inventory.aliases.update({'alias a': {'Q100'}, 'alias b': {'Q100'}})

    class Encoder:
        def encode(self, texts, **kwargs):
            positions = {'alias a': -.4, 'alias b': .4}
            return np.asarray([vec(positions.get(text, 0.)) for text in texts])

    system.model = Encoder()
    system.broad_vectors[:] = system.concept_vectors[:] = [vec(0.), vec(-.2), vec(.2), vec(.4)]
    history = [dict(phrase='alias a', date='2026-09-01'), dict(phrase='alias b', date='2026-09-11')]
    forward = system.recommend(Request(history, limit=1), variant)
    reversed_order = system.recommend(Request(list(reversed(history)), limit=1), variant)
    assert forward['recommendations'] == reversed_order['recommendations']


def test_expired_direction_is_not_reported_as_used():
    history = [dict(item, date=item['date'].replace('2026', '2000')) for item in HISTORY]
    request = Request(history + [dict(phrase='other', date='2026-09-21')],
                      history_config={'half_life_days': 1})
    system = history_lab()
    result = system.recommend(request, 'trajectory')
    assert all(row['score_parts']['trajectory'] == 0 for row in result['recommendations'])
    assert result['execution']['history']['velocity_used'] is False
    assert result['execution']['history']['fallback'] == 'recency_only'
    assert result['recommendations'] == system.recommend(request, 'history-recency')['recommendations']
