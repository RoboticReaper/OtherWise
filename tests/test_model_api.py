"""Selectable study models exercised at the authenticated HTTP boundary."""
from fastapi.testclient import TestClient
import pytest

from service.api import create_app
from test_service import make_engine
from test_recommendation_systems import lab


AUTH = {'Authorization': 'Bearer model-test-token'}


def model_client(system=None):
    from service.models import ModelEngine
    return TestClient(create_app(engine=make_engine(['Bridge'], [.32]),
        model_engine=ModelEngine(lab=system or lab()), token='model-test-token'))


@pytest.mark.parametrize('kind', ['broad', 'specific'])
def test_all_registered_models_are_selectable_through_the_backend(kind):
    with model_client() as client:
        catalog = client.get('/api/recommend/models').json()
        names = {row['name'] for row in catalog['models']}
        assert {'V0', 'V3', 'K-connection', 'K-literal', 'semantic-nearest', 'BM25',
                'random', 'history-recency', 'trajectory'} <= names
        assert catalog['ready'] is True
        assert all(row['ready'] for row in catalog['models'])
        for name in sorted(names):
            response = client.post('/api/recommend', headers=AUTH, json={
                'model': name, 'interests': [{'phrase': 'engineering', 'date': '2026-09-01'}], 'result_kind': kind, 'limit': 3})
            assert response.status_code == 200, (name, response.text)
            assert response.json()['model'] == name
            assert response.json()['status'] == 'ok'
            assert len(response.json()['recommendations']) == 3


def test_dated_history_reaches_the_real_directional_ranker():
    from test_recommendation_history import HISTORY, history_lab
    with model_client(history_lab()) as client:
        payload = {'model': 'trajectory', 'interests': HISTORY, 'limit': 1,
                   'exploration_fraction': 0, 'diversity': 0}
        response = client.post('/api/recommend', headers=AUTH, json=payload)
        assert response.status_code == 200
        assert response.json()['recommendations'][0]['concept_id'] == 'Q101'
        assert response.json()['execution']['history']['velocity_used'] is True
        recent = client.post('/api/recommend', headers=AUTH, json=dict(payload, model='history-recency'))
        assert recent.json()['recommendations'][0]['concept_id'] == 'Q100'


@pytest.mark.parametrize('patch', [
    {'model': 'invented'}, {'interests': []}, {'interests': ['private phrase']*41},
    {'interests': [{'phrase': 'private phrase', 'date': 'private invalid date'}]},
    {'interests': [{'phrase': 'private phrase', 'date': '2026-02-30'}]},
    {'interests': [{'phrase': 'private phrase', 'date': '2026-09-01T00:00:00+00:99'}]},
    {'interests': [{'phrase': 'private phrase', 'date': 42}]},
    {'interests': [{'phrase': 'private phrase', 'extra': 'private'}]},
    {'interests': ['private\nphrase']}, {'interests': [42]},
    {'focus_index': 20}, {'limit': True}, {'seed': -1},
    {'history_config': {'max_step': True}}, {'history_config': {'half_life_days': 0}},
    {'history_config': {'forecast_days': 366}}, {'history_config': {'strand_distance': 'private'}},
    {'raw_url': 'https://private.example'},
])
def test_selected_model_validation_is_bounded_and_never_echoes_input(patch):
    with model_client() as client:
        response = client.post('/api/recommend', headers=AUTH,
            json={'model': 'trajectory', 'interests': ['engineering']} | patch)
        assert response.status_code == 422
        assert response.json() == {'detail': 'Invalid recommendation request.'}
        assert 'private' not in response.text


def test_model_requests_keep_auth_and_the_legacy_keywords_alias():
    with model_client() as client:
        payload = {'model': 'K-connection', 'keywords': ['engineering'],
                   'mode': 'path', 'focus': 'engineering', 'expansion_level': 0, 'limit': 3}
        assert client.post('/api/recommend', json=payload).status_code == 401
        assert client.post('/api/recommend', headers=AUTH, json=payload).status_code == 200


def test_ambiguous_meaning_and_inventory_conflicts_are_explicit():
    system = lab()
    system.inventory.aliases['ambiguous'] = {'Q100', 'Q101'}
    with model_client(system) as client:
        payload = {'model': 'trajectory', 'interests': [{'phrase': 'ambiguous', 'date': '2026-09-01'}]}
        response = client.post('/api/recommend', headers=AUTH, json=payload)
        assert response.json()['status'] == 'clarification_needed'
        assert response.json()['recommendations'] == []
        selected = dict(payload, interests=[{'phrase': 'ambiguous', 'concept_id': 'Q100', 'date': '2026-09-01'}])
        assert client.post('/api/recommend', headers=AUTH, json=selected).status_code == 409
        response = client.post('/api/recommend', headers=AUTH,
            json=dict(selected, inventory_version=system.inventory.version))
        assert response.status_code == 200
        assert 'Q100' not in {r['concept_id'] for r in response.json()['recommendations']}


def test_failed_model_initialization_is_not_advertised_as_ready():
    from service.models import ModelEngine

    class BrokenModels(ModelEngine):
        def initialize(self):
            raise RuntimeError('private credential')

    with TestClient(create_app(engine=make_engine(['Bridge'], [.32]),
        model_engine=BrokenModels(), token='model-test-token')) as client:
        assert client.get('/api/recommend/models').json()['ready'] is False
        assert all(not row['ready'] for row in client.get('/api/recommend/models').json()['models'])
        response = client.post('/api/recommend', headers=AUTH, json={'model': 'trajectory', 'interests': ['engineering']})
        assert response.status_code == 503
        assert 'private' not in response.text


def test_unavailable_lexical_channel_is_not_reported_as_a_successful_model():
    system = lab()
    system.lexical.close()
    system.lexical = None
    with model_client(system) as client:
        statuses = {row['name']: row['ready'] for row in client.get('/api/recommend/models').json()['models']}
        assert statuses['BM25'] is False
        assert statuses['semantic-nearest'] is True
        assert client.post('/api/recommend', headers=AUTH,
            json={'model': 'BM25', 'interests': ['engineering']}).status_code == 503


def test_models_reopen_lexical_resources_across_application_lifespans():
    client = model_client()
    for _ in range(2):
        with client:
            assert all(row['ready'] for row in client.get('/api/recommend/models').json()['models'])
            for model in ('BM25', 'trajectory'):
                response = client.post('/api/recommend', headers=AUTH,
                    json={'model': model, 'interests': ['engineering']})
                assert response.status_code == 200, response.text


@pytest.mark.parametrize('model', ['V0', 'V1'])
def test_legacy_selected_models_respect_explicit_known_identities(model):
    with model_client() as client:
        response = client.post('/api/recommend', headers=AUTH, json={
            'model': model, 'interests': ['engineering'], 'result_kind': 'broad',
            'limit': 100, 'feedback': {'Q100': {'known': True}}})
        assert response.status_code == 200
        batch = response.json()
        assert batch['recommendations']
        assert 'Q100' not in {row['concept_id'] for row in batch['recommendations']}
        assert batch['execution']['serving_guards'] == 'meaning-and-known-exclusions-v1'


@pytest.mark.parametrize('model', ['V0', 'V1'])
def test_legacy_selected_models_require_and_honor_a_meaning_choice(model):
    import numpy as np
    from test_recommendation_systems import vec
    system = lab()
    system.inventory.aliases['ambiguous'] = {'Q100', 'Q101'}
    system.inventory.aliases['aaa alias'] = {'Q100'}

    class Encoder:
        def encode(self, texts, **kwargs):
            return np.asarray([vec(.8) if text in ('ambiguous', 'aaa alias') else vec(0.) for text in texts])

    system.model = Encoder()
    with model_client(system) as client:
        payload = {'model': model, 'interests': ['ambiguous'], 'result_kind': 'broad'}
        ambiguous = client.post('/api/recommend', headers=AUTH, json=payload).json()
        assert ambiguous['status'] == 'clarification_needed'
        assert ambiguous['recommendations'] == []
        chosen = dict(payload, interests=[{'phrase': 'ambiguous', 'concept_id': 'Q100'}],
                      inventory_version=system.inventory.version)
        response = client.post('/api/recommend', headers=AUTH, json=chosen)
        assert response.status_code == 200
        assert response.json()['recommendations']
        assert response.json()['resolutions'][0]['concept_id'] == 'Q100'
        assert 'Q100' not in {row['concept_id'] for row in response.json()['recommendations']}
        dated_aliases = dict(chosen, interests=[{'phrase': 'aaa alias', 'date': '2026-09-01'},
            {'phrase': 'ambiguous', 'concept_id': 'Q100', 'date': '2026-09-11'}])
        response = client.post('/api/recommend', headers=AUTH, json=dated_aliases)
        assert response.status_code == 200
        assert response.json()['recommendations']


def test_raw_historical_lab_is_distinguishable_from_guarded_serving():
    from recommendation_lab.systems import Request
    system = lab()
    request = Request(['engineering'], result_kind='broad', feedback={'Q100': {'known': True}}, limit=100)
    raw = system.recommend(request, 'V0')
    assert 'Q100' in {row['concept_id'] for row in raw['recommendations']}
    with model_client(system) as client:
        served = client.post('/api/recommend', headers=AUTH, json={
            'model': 'V0', 'interests': ['engineering'], 'result_kind': 'broad',
            'feedback': {'Q100': {'known': True}}, 'limit': 100}).json()
        assert raw['algorithm_id'] != served['algorithm_id']
