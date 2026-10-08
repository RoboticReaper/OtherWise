"""Authenticated public layout jobs, source identity, and bounded exact-KNN reuse."""
import hashlib
import importlib
from importlib.util import find_spec
import json
import threading
import time
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient

from service.api import create_app
from service.engine import RecommendationEngine
from test_api import AUTH, TOKEN, PAYLOAD

CONTROLS = dict(n_neighbors=12, min_dist=.4, spread=1.5, repulsion_strength=2.5)


def layout_module():
    try:
        return importlib.import_module('service.galaxy_layout')
    except ModuleNotFoundError:
        pytest.fail('Public Galaxy layout job service is missing.')


def source(tmp_path, *, raw=False):
    rng = np.random.default_rng(82)
    values = rng.normal(size=(18, 768))
    if not raw:
        values /= np.linalg.norm(values, axis=1, keepdims=True)
    topics = [dict(topic=f'Topic {i:02}', domain=f'Domain {i % 3}', description='Public description.')
              for i in range(len(values))]
    engine = RecommendationEngine(topics=topics, topic_vectors=values, model=object(), cache_dir=tmp_path / 'embeddings')
    engine.initialize()
    return engine, values


def request(engine, **controls):
    return dict(**engine.focus_identity(), parameters=CONTROLS | controls)


def wait_ready(service, job):
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        status = service.status(job['job_id'])
        if status['status'] in {'ready', 'failed'}:
            assert status['status'] == 'ready', status
            return status
        time.sleep(.01)
    pytest.fail('Layout job did not finish.')


def fast_projection(monkeypatch, *, started=None, release=None):
    m = layout_module()
    monkeypatch.setattr(m, 'require_layout_dependencies', lambda: None)
    def project(topics, units, neighbors, parameters):
        if started is not None:
            started.set()
            assert release.wait(5)
        return units[:, :2], np.zeros((3, 2))
    monkeypatch.setattr(m, 'project_layout', project)
    return m


def test_jobs_preserve_source_return_only_geometry_and_reuse_key(monkeypatch, tmp_path):
    m = fast_projection(monkeypatch)
    engine, _ = source(tmp_path)
    service = m.GalaxyLayoutService(engine, cache_dir=tmp_path / 'layouts')
    try:
        job = service.start(request(engine))
        done = wait_ready(service, job)
        result = done['result']
        assert set(result) == {'schema_version', 'cache_key', 'catalog_sha256', 'model', 'embedding', 'parameters', 'topics', 'domains'}
        assert result['schema_version'] == 1
        assert result['embedding'] == engine.focus_identity()['embedding']
        assert result['parameters'] == CONTROLS
        assert [row['id'] for row in result['topics']] == [f'Topic {i:02}' for i in range(18)]
        assert [row['id'] for row in result['domains']] == ['Domain 0', 'Domain 1', 'Domain 2']
        assert all(set(row) == {'id', 'x', 'y'} for row in result['topics'])
        assert 'Public description' not in json.dumps(done)
        assert service.start(request(engine))['job_id'] == job['job_id']
    finally:
        service.close()


def test_single_live_job_keeps_duplicate_and_rejects_other_parameters(monkeypatch, tmp_path):
    started, release = threading.Event(), threading.Event()
    m = fast_projection(monkeypatch, started=started, release=release)
    engine, _ = source(tmp_path)
    service = m.GalaxyLayoutService(engine, cache_dir=tmp_path / 'layouts')
    try:
        job = service.start(request(engine))
        assert started.wait(5)
        assert service.start(request(engine))['job_id'] == job['job_id']
        with pytest.raises(m.LayoutBusy):
            service.start(request(engine, n_neighbors=20))
        assert service.status(job['job_id'])['status'] == 'running'
    finally:
        release.set()
        service.close()


def test_exact_knn_reused_across_parameters_and_service_restart(monkeypatch, tmp_path):
    m = fast_projection(monkeypatch)
    engine, _ = source(tmp_path)
    cache = tmp_path / 'layouts'
    service = m.GalaxyLayoutService(engine, cache_dir=cache)
    first = wait_ready(service, service.start(request(engine)))
    service.close()
    def forbidden(*args, **kwargs):
        raise AssertionError('Validated exact source KNN should be reused.')
    monkeypatch.setattr(m, 'exact_angular_neighbors', forbidden)
    restarted = m.GalaxyLayoutService(engine, cache_dir=cache)
    try:
        assert wait_ready(restarted, restarted.start(request(engine)))['result'] == first['result']
        other = wait_ready(restarted, restarted.start(request(engine, n_neighbors=20)))
        assert other['result']['parameters']['n_neighbors'] == 20
        assert other['result']['cache_key'] != first['result']['cache_key']
    finally:
        restarted.close()


def test_raw_cached_source_is_used_instead_of_twice_normalized_engine(monkeypatch, tmp_path):
    m = fast_projection(monkeypatch)
    engine, values = source(tmp_path, raw=True)
    identity = hashlib.sha256(json.dumps({'model': engine.model_name,
        'texts': [f"{r['topic']}: {r['description']}" for r in engine.topics]},
        ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    engine.cache_dir.mkdir()
    np.save(engine.cache_dir / f'{identity}.npy', values)
    service = m.GalaxyLayoutService(engine, cache_dir=tmp_path / 'layouts')
    try:
        assert np.array_equal(service.source_vectors(), values)
        result = wait_ready(service, service.start(request(engine)))['result']
        assert result['embedding']['sha256'] == hashlib.sha256(values.tobytes()).hexdigest()
    finally:
        service.close()


def test_result_and_memory_caches_are_bounded(monkeypatch, tmp_path):
    m = fast_projection(monkeypatch)
    engine, _ = source(tmp_path)
    service = m.GalaxyLayoutService(engine, cache_dir=tmp_path / 'layouts', max_results=2)
    try:
        jobs = [wait_ready(service, service.start(request(engine, min_dist=value))) for value in [.1, .2, .3]]
        assert len(list((tmp_path / 'layouts').glob('*.json'))) == 2
        with pytest.raises(KeyError):
            service.status(jobs[0]['job_id'])
        assert service.status(jobs[-1]['job_id'])['status'] == 'ready'
    finally:
        service.close()


@pytest.mark.parametrize('patch', [dict(n_neighbors=4), dict(n_neighbors=61), dict(n_neighbors=True),
    dict(n_neighbors=12.), dict(min_dist='0.4'), dict(min_dist=True), dict(min_dist=-.1),
    dict(min_dist=1.01), dict(min_dist=float('nan')), dict(spread=.49), dict(spread=3.1),
    dict(min_dist=.8, spread=.5), dict(repulsion_strength=.49), dict(repulsion_strength=4.1),
    dict(repulsion_strength=float('inf')), dict(private='secret')])
def test_layout_api_rejects_invalid_controls_before_computation(monkeypatch, tmp_path, patch):
    m = fast_projection(monkeypatch)
    engine, _ = source(tmp_path)
    service = m.GalaxyLayoutService(engine, cache_dir=tmp_path / 'layouts')
    with TestClient(create_app(engine=engine, token=TOKEN, layout_service=service)) as session:
        response = session.post('/api/galaxy-layout', headers=AUTH | {'Content-Type': 'application/json'},
                                content=json.dumps(request(engine, **patch)))
        assert response.status_code == 422
        assert 'secret' not in response.text
        assert not list((tmp_path / 'layouts').glob('*.json'))


def test_layout_api_auth_source_conflicts_and_polling_has_independent_budget(monkeypatch, tmp_path):
    m = fast_projection(monkeypatch)
    engine, _ = source(tmp_path)
    service = m.GalaxyLayoutService(engine, cache_dir=tmp_path / 'layouts')
    with TestClient(create_app(engine=engine, token=TOKEN, layout_service=service)) as session:
        assert session.post('/api/galaxy-layout', content=b'x' * 20000).status_code == 401
        assert session.get('/api/galaxy-layout/unknown').status_code == 401
        assert session.get('/api/galaxy-layout/unknown', headers=AUTH).status_code == 404
        identity = engine.focus_identity()
        for patch in [dict(catalog_sha256='0' * 64), dict(model='outdated'),
                dict(embedding=identity['embedding'] | {'sha256': '0' * 64}),
                dict(embedding=identity['embedding'] | {'dtype': 'float32'}),
                dict(embedding=identity['embedding'] | {'shape': [19, 768]})]:
            mismatch = session.post('/api/galaxy-layout', headers=AUTH, json=request(engine) | patch)
            assert mismatch.status_code == 409
        response = session.post('/api/galaxy-layout', headers=AUTH, json=request(engine))
        assert response.status_code == 200
        job_id = response.json()['job_id']
        wait_ready(service, response.json())
        for _ in range(40):
            status = session.get('/api/galaxy-layout/' + job_id, headers=AUTH)
            assert status.status_code == 200 and status.json()['status'] == 'ready'
        # Status polls do not consume the recommendation POST budget.
        assert session.post('/api/recommend', headers=AUTH, json=PAYLOAD).status_code != 429
        assert session.get('/health').status_code == 200


def test_missing_dependencies_return_helpful_503(monkeypatch, tmp_path):
    m = layout_module()
    engine, _ = source(tmp_path)
    def unavailable():
        raise m.LayoutUnavailable('Install requirements-layout.txt to generate Galaxy layouts.')
    monkeypatch.setattr(m, 'require_layout_dependencies', unavailable)
    service = m.GalaxyLayoutService(engine, cache_dir=tmp_path / 'layouts')
    with TestClient(create_app(engine=engine, token=TOKEN, layout_service=service)) as session:
        response = session.post('/api/galaxy-layout', headers=AUTH, json=request(engine))
        assert response.status_code == 503
        assert 'requirements-layout.txt' in response.json()['detail']


def test_projection_failure_is_safe_and_releases_capacity(monkeypatch, tmp_path):
    m = fast_projection(monkeypatch)
    engine, _ = source(tmp_path)
    def broken(*args, **kwargs):
        raise RuntimeError('private model credential')
    monkeypatch.setattr(m, 'project_layout', broken)
    service = m.GalaxyLayoutService(engine, cache_dir=tmp_path / 'layouts')
    try:
        job = service.start(request(engine))
        deadline = time.monotonic() + 5
        while service.status(job['job_id'])['status'] != 'failed' and time.monotonic() < deadline:
            time.sleep(.01)
        failed = service.status(job['job_id'])
        assert failed['status'] == 'failed'
        assert 'private' not in json.dumps(failed)
        assert 'result' not in failed
        monkeypatch.setattr(m, 'project_layout', lambda topics, values, angular, parameters: (values[:, :2], None))
        assert wait_ready(service, service.start(request(engine, min_dist=.2)))['status'] == 'ready'
    finally:
        service.close()


@pytest.mark.layout_integration
@pytest.mark.skipif(find_spec('umap') is None, reason='Optional UMAP dependencies')
def test_real_umap_job_produces_finite_public_geometry_and_b_cache(tmp_path):
    m = layout_module()
    m.require_layout_dependencies()
    engine, _ = source(tmp_path)
    service = m.GalaxyLayoutService(engine, cache_dir=tmp_path / 'layouts')
    try:
        result = wait_ready(service, service.start(request(engine, n_neighbors=5)))['result']
        coords = np.array([[r['x'], r['y']] for r in result['topics']])
        assert np.isfinite(coords).all()
        assert np.mean(coords, axis=0) == pytest.approx([0, 0], abs=1e-6)
        assert np.mean(np.sum(coords * coords, axis=1)) == pytest.approx(1, abs=1e-6)
        assert result['embedding'] == engine.focus_identity()['embedding']
    finally:
        service.close()


def test_failed_job_can_retry_identical_parameters_and_keep_its_key(monkeypatch, tmp_path):
    m = fast_projection(monkeypatch)
    engine, _ = source(tmp_path)
    transient = True
    def fail_once(topics, values, angular, parameters):
        nonlocal transient
        if transient:
            transient = False
            raise RuntimeError('temporary numerical failure')
        return values[:, :2], None
    monkeypatch.setattr(m, 'project_layout', fail_once)
    service = m.GalaxyLayoutService(engine, cache_dir=tmp_path / 'layouts')
    try:
        first = service.start(request(engine))
        deadline = time.monotonic() + 5
        while service.status(first['job_id'])['status'] != 'failed' and time.monotonic() < deadline:
            time.sleep(.01)
        assert service.status(first['job_id'])['status'] == 'failed'
        retried = service.start(request(engine))
        assert retried['job_id'] == first['job_id']
        completed = wait_ready(service, retried)
        assert completed['result']['parameters'] == CONTROLS
        assert 'error' not in completed
        assert service.start(request(engine))['status'] == 'ready'
    finally:
        service.close()


def test_retry_of_failed_job_is_busy_while_another_projection_is_running(monkeypatch, tmp_path):
    m = fast_projection(monkeypatch)
    engine, _ = source(tmp_path)
    def broken(*args, **kwargs):
        raise RuntimeError('temporary numerical failure')
    monkeypatch.setattr(m, 'project_layout', broken)
    service = m.GalaxyLayoutService(engine, cache_dir=tmp_path / 'layouts')
    started, release = threading.Event(), threading.Event()
    try:
        failed = service.start(request(engine))
        deadline = time.monotonic() + 5
        while service.status(failed['job_id'])['status'] != 'failed' and time.monotonic() < deadline:
            time.sleep(.01)
        assert service.status(failed['job_id'])['status'] == 'failed'
        def slow(topics, values, angular, parameters):
            started.set()
            assert release.wait(5)
            return values[:, :2], None
        monkeypatch.setattr(m, 'project_layout', slow)
        other = service.start(request(engine, min_dist=.2))
        assert started.wait(5)
        with pytest.raises(m.LayoutBusy):
            service.start(request(engine))
        assert service.status(failed['job_id'])['status'] == 'failed'
        assert service.start(request(engine, min_dist=.2))['job_id'] == other['job_id']
    finally:
        release.set()
        service.close()
