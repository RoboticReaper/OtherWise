"""Graph API integration using real ranking and hand-calculated vectors."""
import importlib
import os
from copy import deepcopy

import numpy as np
import pytest
from fastapi.testclient import TestClient

from test_graph_explorer import fixture, vec
from test_service import make_engine
from service.api import create_app


def discovery_engine(tmp_path, distances=None):
    try:
        cls = importlib.import_module('service.discovery').DiscoveryEngine
    except ModuleNotFoundError:
        pytest.fail('The graph service has not been connected.')
    broad = make_engine(['Broad bridge'], [.325], {'Interest': 0, 'Other': .7})
    return cls(broad, graph=fixture(), concept_vectors=vec(distances or [.325]*8),
               area_vectors=vec([0, 0]), cache_dir=tmp_path)


BODY = dict(keywords=['Interest'], mode='global', focus=None, expansion_level=0,
            limit=4, radius=.25, expansion=.15, overlap=0, diversity=0,
            randomness=0, seed=42, exploration_fraction=0, feedback=[], exposures={})
AUTH = {'Authorization': 'Bearer local-test'}


@pytest.mark.skipif(os.getenv('OTHERWISE_RUN_REAL_DISCOVERY') != '1',
                    reason='Opt in to local cached MPNet graph API verification.')
def test_real_mpnet_graph_api_preserves_band_sources_and_known_exclusion():
    from service.discovery import DiscoveryEngine
    from service.engine import RecommendationEngine
    graph = DiscoveryEngine(RecommendationEngine())
    body = dict(keywords=['Gardening'], mode='path', focus='Gardening',
                expansion_level=0, limit=10, seed=42, feedback=[], exposures={},
                exploration_fraction=.3)
    with TestClient(create_app(engine=graph.broad, discovery_engine=graph, token='local-test')) as client:
        response = client.post('/api/discover', headers=AUTH, json=body)
        assert response.status_code == 200
        first = response.json()
        assert len(first['recommendations']) == 10
        assert graph.concept_vectors.shape == (3642, 768)
        for row in first['recommendations']:
            metadata = row['discovery']
            assert .28 - .015 - 1e-9 <= row['distance'] <= .28 + .07 + 1e-9
            assert metadata['graph_path'][-1] == row['topic']
            assert metadata['source_url'] == graph.nodes[metadata['concept_id']]['source_url']
        metadata = first['recommendations'][0]['discovery']
        rating = dict(concept_id=metadata['concept_id'], area_id=metadata['area_id'],
                      curious=True, known=True, difficulty='too_hard')
        rated = client.post('/api/discover', headers=AUTH, json=body | {'feedback':[rating]})
        assert rated.status_code == 200
        assert metadata['concept_id'] not in {r['discovery']['concept_id'] for r in rated.json()['recommendations']}
        assert client.post('/api/discover', headers=AUTH, json=body).json() == first


def test_graph_api_ranks_with_feedback_without_mutating_or_saving_profile(tmp_path):
    graph = discovery_engine(tmp_path)
    original = deepcopy(BODY)
    with TestClient(create_app(engine=graph.broad, discovery_engine=graph, token='local-test')) as client:
        first = client.post('/api/discover', headers=AUTH, json=BODY)
        assert first.status_code == 200
        data = first.json()
        assert data['recommendations'][0]['discovery']['concept_id'] == 'Q0'
        assert data['recommendations'][0]['discovery']['graph_path'] == ['cs', 'Concrete 0']
        assert len(data['graph_sha256']) == 64
        rating = dict(concept_id='Q0', area_id='cs', curious=True, known=True, difficulty='none')
        rated = client.post('/api/discover', headers=AUTH, json=BODY | {'feedback': [rating]})
        assert rated.status_code == 200
        assert 'Q0' not in {r['discovery']['concept_id'] for r in rated.json()['recommendations']}
        assert client.post('/api/discover', headers=AUTH, json=BODY).json() == data
    assert BODY == original
    assert not list(tmp_path.rglob('*.json'))


def test_path_graph_excludes_candidates_familiar_to_other_approved_interests(tmp_path):
    graph = discovery_engine(tmp_path, [.325, .34, .325, .1, .7, .72, .71, .9])
    graph.initialize()
    rows = graph.recommend(**(BODY | dict(keywords=['Interest', 'Other'], mode='path', focus='Interest', expansion=.5, limit=8)))['recommendations']
    assert rows
    assert not {'Q4', 'Q5', 'Q6'} & {r['discovery']['concept_id'] for r in rows}


@pytest.mark.parametrize('patch', [
    {'feedback': [dict(concept_id='unknown', area_id='cs', curious=True, known=False, difficulty='none')]},
    {'feedback': [dict(concept_id='Q0', area_id='music', curious=True, known=False, difficulty='none')]},
    {'feedback': [dict(concept_id='Q0', area_id='cs', curious=1, known=False, difficulty='none')]},
    {'feedback': [dict(concept_id='Q0', area_id='cs', curious=True, known=False, difficulty='none', private_url='private')]},
    {'exposures': {'cs': -1}}, {'exposures': {'unknown': 1}}, {'seed': True},
    {'exploration_fraction': 1.1}, {'history': ['private']},
])
def test_graph_api_rejects_forged_profile_fields_without_echo(tmp_path, patch):
    graph = discovery_engine(tmp_path)
    with TestClient(create_app(engine=graph.broad, discovery_engine=graph, token='local-test')) as client:
        result = client.post('/api/discover', headers=AUTH, json=BODY | patch)
        assert result.status_code == 422
        assert result.json() == {'detail': 'Invalid recommendation request.'}


def test_graph_authentication_precedes_parsing_and_keeps_broad_endpoint_working(tmp_path):
    graph = discovery_engine(tmp_path)
    with TestClient(create_app(engine=graph.broad, discovery_engine=graph, token='local-test')) as client:
        assert client.post('/api/discover', content='not-json').status_code == 401
        assert client.post('/api/discover', headers=AUTH, content='x' * 1_048_577).status_code == 413
        assert client.post('/api/recommend', headers=AUTH, json={k:v for k,v in BODY.items() if k not in {'seed','exploration_fraction','feedback','exposures'}}).status_code == 200


def test_discovery_cache_contains_only_public_embeddings_and_recovers_corruption(tmp_path):
    cls = type(discovery_engine(tmp_path))
    broad = make_engine(['Broad bridge'], [.325], {'Interest':0, 'Other':.7})
    class PublicModel:
        def encode(self, texts, **kwargs):
            return np.tile([1., 0.], (len(texts), 1))
    broad.model = PublicModel()
    first = cls(broad, graph=fixture(), cache_dir=tmp_path)
    first.initialize()
    files = list(tmp_path.glob('discovery-*.npy'))
    assert len(files) == 2
    class CachedModel:
        def encode(self, *args, **kwargs):
            raise AssertionError('Unchanged public vectors must use the cache.')
    broad.model = CachedModel()
    cls(broad, graph=fixture(), cache_dir=tmp_path).initialize()
    files[0].write_bytes(b'corrupt')
    broad.model = PublicModel()
    repaired = cls(broad, graph=fixture(), cache_dir=tmp_path)
    repaired.initialize()
    assert np.isfinite(repaired.concept_vectors).all()
