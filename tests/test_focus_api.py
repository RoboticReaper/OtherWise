"""Focus API validation, privacy and resource protection through real ASGI."""
import asyncio
import json
import threading
from concurrent.futures import ThreadPoolExecutor

import httpx
import pytest
from fastapi.testclient import TestClient

from test_api import AUTH, PAYLOAD, TOKEN, app_factory
from test_focus_service import focus_engine


def payload(engine):
    return dict(topic_id='Center', **engine.focus_identity())


@pytest.fixture
def client():
    engine = focus_engine()
    with TestClient(app_factory(engine=engine, token=TOKEN)) as session:
        yield session, payload(engine)


def test_focus_post_returns_versioned_real_catalog_results(client):
    session, body = client
    response = session.post('/api/focus', headers=AUTH, json=body | {'randomness': 0})
    assert response.status_code == 200
    result = response.json()
    assert result['seed_id'] == 'Center'
    assert {r['id'] for r in result['recommendations']} == {'Bridge A', 'Bridge B'}
    assert result['catalog_sha256'] == body['catalog_sha256']
    assert result['embedding'] == body['embedding']
    assert result['algorithm_version'] == 'catalog-focus-band-v1'


@pytest.mark.parametrize('patch', [dict(keywords=['private phrase']), dict(history=['private url']),
    dict(limit=True), dict(limit=101), dict(radius='0.2'), dict(radius=True), dict(radius=-.01),
    dict(expansion=None), dict(overlap=1.01), dict(diversity=float('nan')),
    dict(randomness=float('inf')), dict(max_overlap_fraction=.96), dict(topic_id=123),
    dict(catalog_sha256='invalid'), dict(model=''), dict(embedding={}),
    dict(embedding={'sha256': 'a' * 64, 'dtype': 'float32', 'shape': [6, 2]}),
    dict(embedding={'sha256': 'a' * 64, 'dtype': 'float32', 'shape': [True, 768]}),
    dict(embedding={'sha256': 'a' * 64, 'dtype': 'float32', 'shape': [6, 768], 'private': 'value'})])
def test_focus_strict_parameters_and_extra_fields_never_echo_input(client, patch):
    session, body = client
    response = session.post('/api/focus', headers=AUTH | {'Content-Type': 'application/json'},
                            content=json.dumps(body | patch))
    assert response.status_code == 422
    assert response.json() == {'detail': 'Invalid recommendation request.'}
    assert 'private' not in response.text


def test_unknown_topic_is_422_and_versions_are_409_without_echo(client):
    session, body = client
    unknown = session.post('/api/focus', headers=AUTH, json=body | {'topic_id': 'private phrase'})
    assert unknown.status_code == 422
    assert 'private' not in unknown.text
    for field, value in [('catalog_sha256', '0' * 64), ('model', 'old'),
                         ('embedding', body['embedding'] | {'sha256': '0' * 64}),
                         ('embedding', body['embedding'] | {'dtype': 'float32'}),
                         ('embedding', body['embedding'] | {'shape': [7, 768]})]:
        response = session.post('/api/focus', headers=AUTH, json=body | {field: value})
        assert response.status_code == 409
        assert value != response.json().get('detail')


@pytest.mark.parametrize('headers', [{}, {'Authorization': 'Bearer wrong'}, {'Authorization': 'Basic test-local-token'}])
def test_focus_authentication_precedes_body_parsing(client, headers):
    session, _ = client
    response = session.post('/api/focus', headers=headers, content=b'private phrase' * 2000)
    assert response.status_code == 401
    assert 'private' not in response.text


def test_focus_missing_fields_and_malformed_json(client):
    session, body = client
    for content in ['{"private phrase":', json.dumps({'topic_id': 'private phrase'})]:
        response = session.post('/api/focus', headers=AUTH, content=content)
        assert response.status_code == 422
        assert 'private' not in response.text


def test_focus_bounds_streamed_body_without_content_length():
    async def check():
        engine = focus_engine()
        app = app_factory(engine=engine, token=TOKEN)
        async def chunks():
            yield b'x' * 8000
            yield b'x' * 9000
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://local.test') as session:
                response = await session.post('/api/focus', headers=AUTH, content=chunks())
                assert response.status_code == 413
    asyncio.run(check())


def test_focus_and_discover_share_the_rate_limit(client):
    session, body = client
    for index in range(30):
        path, data = ('/api/focus', body) if index % 2 else ('/api/recommend', PAYLOAD)
        # Focus fixture deliberately cannot encode Discover; a 503 still counts.
        assert session.post(path, headers=AUTH, json=data).status_code in {200, 503}
    response = session.post('/api/focus', headers=AUTH, json=body)
    assert response.status_code == 429
    assert response.headers['retry-after']


@pytest.mark.parametrize('first_path', ['/api/focus', '/api/recommend'])
def test_focus_and_discover_share_compute_capacity(first_path):
    engine = focus_engine()
    body = payload(engine)
    started, release = threading.Event(), threading.Event()
    class SlowEngine:
        ready = True
        def initialize(self):
            pass
        def recommend(self, *args, **kwargs):
            started.set()
            assert release.wait(5)
            return []
        def recommend_focus(self, *args, **kwargs):
            started.set()
            assert release.wait(5)
            return engine.recommend_focus(*args, **kwargs)
    with TestClient(app_factory(engine=SlowEngine(), token=TOKEN)) as session:
        with ThreadPoolExecutor(max_workers=1) as pool:
            data = body if first_path == '/api/focus' else PAYLOAD
            first = pool.submit(session.post, first_path, headers=AUTH, json=data)
            try:
                assert started.wait(5)
                other_path, other_data = ('/api/recommend', PAYLOAD) if first_path == '/api/focus' else ('/api/focus', body)
                assert session.post(other_path, headers=AUTH, json=other_data).status_code == 429
            finally:
                release.set()
            assert first.result().status_code == 200


def test_focus_computation_failure_releases_semaphore_and_hides_secrets(caplog):
    engine = focus_engine()
    body = payload(engine)
    class FlakyEngine:
        ready = True
        first = True
        def initialize(self):
            pass
        def recommend_focus(self, *args, **kwargs):
            if self.first:
                self.first = False
                raise RuntimeError('private model credential')
            return engine.recommend_focus(*args, **kwargs)
    with TestClient(app_factory(engine=FlakyEngine(), token=TOKEN)) as session:
        failed = session.post('/api/focus', headers=AUTH, json=body)
        assert failed.status_code == 503
        assert session.post('/api/focus', headers=AUTH, json=body).status_code == 200
        assert 'private' not in failed.text + caplog.text


def test_focus_unready_service_fails_closed():
    engine = focus_engine()
    body = payload(engine)
    class BrokenEngine:
        ready = False
        def initialize(self):
            raise RuntimeError('private credential')
    with TestClient(app_factory(engine=BrokenEngine(), token=TOKEN)) as session:
        response = session.post('/api/focus', headers=AUTH, json=body)
        assert response.status_code == 503
        assert 'private' not in response.text


def test_focus_internal_value_error_is_computation_failure():
    engine = focus_engine()
    body = payload(engine)
    class InvalidComputation:
        ready = True
        def initialize(self):
            pass
        def recommend_focus(self, *args, **kwargs):
            raise ValueError('private broken catalog geometry')
    with TestClient(app_factory(engine=InvalidComputation(), token=TOKEN)) as session:
        response = session.post('/api/focus', headers=AUTH, json=body)
        assert response.status_code == 503
        assert 'private' not in response.text
