"""Catalog Focus contracts with known 768-dimensional angular geometry."""
import hashlib
import math
import os
from pathlib import Path

import numpy as np
import pytest

from explorer import recommend
from service.engine import RecommendationEngine
from test_galaxy import fast_projection


NAMES = ['Center', 'Overlap', 'Bridge A', 'Bridge B', 'Too close', 'Outside']
DISTANCES = [0, .27, .31, .34, .1, .8]
OPTIONS = dict(limit=10, radius=.28, expansion=.07, overlap=.015,
               diversity=.20, max_overlap_fraction=.20, randomness=0)


def catalog(names=NAMES):
    return [dict(topic=name, domain='Example', description=f'Original {name}.', source='Public')
            for name in names]


def vectors(distances=DISTANCES, dtype=np.float64):
    result = np.zeros((len(distances), 768), dtype=dtype)
    for index, distance in enumerate(distances):
        result[index, :2] = [math.cos(math.pi * distance), math.sin(math.pi * distance)]
    return result


class CatalogModel:
    def __init__(self, raw=None):
        self.raw = vectors() if raw is None else raw
        self.encode_calls = 0

    def encode(self, texts, **kwargs):
        self.encode_calls += 1
        assert texts == [f'{r["topic"]}: {r["description"]}' for r in catalog()]
        return self.raw


class NoEncoding:
    def encode(self, *args, **kwargs):
        raise AssertionError('Focus must use catalog vectors without encoding.')


def focus_engine(*, raw=None, topics=None):
    engine = RecommendationEngine(topics=catalog() if topics is None else topics,
                                  model=NoEncoding(), topic_vectors=vectors() if raw is None else raw)
    engine.initialize()
    return engine


def test_focus_uses_catalog_vector_without_encoding():
    engine = focus_engine()
    result = engine.recommend_focus('Center', expected_identity=engine.focus_identity(), randomness=0)
    assert result['seed_id'] == 'Center'
    assert {r['id'] for r in result['recommendations']} == {'Bridge A', 'Bridge B'}
    known_distances = dict(zip(NAMES, DISTANCES))
    assert all(abs(r['distance'] - known_distances[r['id']]) < 1e-6 for r in result['recommendations'])
    assert all(r['nearest_interest'] == 'Center' for r in result['recommendations'])
    assert result['schema_version'] == 1
    assert result['algorithm_version'] == 'catalog-focus-band-v1'
    assert set(result) == {'schema_version', 'algorithm_version', 'seed_id',
                           'catalog_sha256', 'model', 'embedding', 'recommendations'}


def test_focus_matches_existing_ranker_and_public_rows():
    engine = focus_engine()
    options = OPTIONS | dict(limit=4, radius=.3, expansion=.1, overlap=.04,
                            diversity=.35, max_overlap_fraction=.5)
    expected = recommend(engine.topics, engine.topic_vectors, ['Center'],
                         engine.topic_vectors[[0]], top_k=options['limit'],
                         **{k: v for k, v in options.items() if k != 'limit'})
    result = engine.recommend_focus('Center', expected_identity=engine.focus_identity(), **options)
    assert [r['id'] for r in result['recommendations']] == [r['topic'] for r in expected]
    for actual, original in zip(result['recommendations'], expected):
        assert set(actual) == {'id', 'topic', 'domain', 'description', 'nearest_interest',
                               'distance', 'boundary_offset', 'zone'}
        assert actual == dict(id=original['topic'], **{k: original[k] for k in actual if k != 'id'})


def test_focus_sparse_band_never_expands_to_fill_limit():
    engine = focus_engine()
    result = engine.recommend_focus('Center', expected_identity=engine.focus_identity(),
                                    limit=100, radius=.30, expansion=.02, randomness=0)
    assert [r['id'] for r in result['recommendations']] == ['Bridge A']
    empty = engine.recommend_focus('Center', expected_identity=engine.focus_identity(),
                                   radius=.5, expansion=.01, randomness=0)
    assert empty['recommendations'] == []


def test_focus_reordering_keeps_seed_and_rows_associated_with_ids():
    engine = focus_engine(raw=vectors()[::-1], topics=catalog()[::-1])
    result = engine.recommend_focus('Center', expected_identity=engine.focus_identity(), randomness=0)
    assert {r['id']: round(r['distance'], 6) for r in result['recommendations']} == {'Bridge A': .31, 'Bridge B': .34}


@pytest.mark.parametrize('dtype', [np.float32, np.float64])
def test_focus_identity_uses_raw_noncontiguous_array_bytes(dtype):
    raw = (vectors(dtype=dtype) * 3)[:, ::-1]
    assert not raw.flags.c_contiguous
    engine = focus_engine(raw=raw)
    embedding = engine.focus_identity()['embedding']
    assert embedding == dict(sha256=hashlib.sha256(np.ascontiguousarray(raw).tobytes()).hexdigest(),
                             dtype=str(raw.dtype), shape=[6, 768])
    embedding['shape'][0] = 999
    assert engine.focus_identity()['embedding']['shape'] == [6, 768]


def test_focus_raw_identity_survives_cache_reload(tmp_path):
    # A real preexisting cache is float32 and nonunit. Rehashing normalized
    # float64 vectors in initialize would incorrectly report another version.
    import json
    from explorer import MODEL_NAME, topic_texts
    raw = vectors(dtype=np.float32) * 3
    key = hashlib.sha256(json.dumps({'model': MODEL_NAME, 'texts': topic_texts(catalog())},
                                  ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    np.save(tmp_path / f'{key}.npy', raw)
    reloaded = RecommendationEngine(topics=catalog(), model=NoEncoding(), cache_dir=tmp_path)
    reloaded.initialize()
    assert reloaded.focus_identity()['embedding']['sha256'] == hashlib.sha256(np.ascontiguousarray(raw).tobytes()).hexdigest()
    assert reloaded.focus_identity()['embedding']['dtype'] == 'float32'
    assert np.linalg.norm(reloaded.topic_vectors, axis=1) == pytest.approx(np.ones(6))


def test_focus_first_encoding_identity_matches_written_cache_and_reload(tmp_path):
    model = CatalogModel(vectors(dtype=np.float32) * 3)
    first = RecommendationEngine(topics=catalog(), model=model, cache_dir=tmp_path)
    first.initialize()
    raw = np.load(next(tmp_path.glob('*.npy')), allow_pickle=False)
    assert model.encode_calls == 1
    assert first.focus_identity()['embedding']['sha256'] == hashlib.sha256(raw.tobytes()).hexdigest()
    assert first.focus_identity()['embedding']['dtype'] == str(raw.dtype)
    cached = RecommendationEngine(topics=catalog(), model=NoEncoding(), cache_dir=tmp_path)
    cached.initialize()
    assert cached.focus_identity() == first.focus_identity()
    assert cached.recommend_focus('Center', expected_identity=first.focus_identity(), randomness=0)['recommendations']


def test_focus_identity_matches_galaxy_metadata(monkeypatch, tmp_path):
    raw = vectors(dtype=np.float32) * 3
    engine = focus_engine(raw=raw)
    layout = fast_projection(monkeypatch).build_galaxy(
        topics=catalog(), vectors=raw, embedding_identity='original-cache',
        cache_dir=tmp_path / 'cache', output_path=tmp_path / 'galaxy.json').asset
    metadata = layout['metadata']
    assert engine.focus_identity() == dict(catalog_sha256=metadata['catalog_sha256'],
        model=metadata['model'], embedding={k: metadata['embedding'][k] for k in ('sha256', 'dtype', 'shape')})


@pytest.mark.parametrize('patch', [dict(limit=True), dict(limit=0), dict(limit=101),
    dict(radius=True), dict(radius='0.2'), dict(expansion=None), dict(overlap=-.01),
    dict(diversity=math.nan), dict(randomness=math.inf), dict(max_overlap_fraction=.96)])
def test_focus_rejects_invalid_controls(patch):
    engine = focus_engine()
    with pytest.raises(ValueError):
        engine.recommend_focus('Center', expected_identity=engine.focus_identity(), **patch)


def test_focus_rejects_unknown_id_and_stale_identity():
    engine = focus_engine()
    with pytest.raises(ValueError):
        engine.recommend_focus('private unknown', expected_identity=engine.focus_identity())
    with pytest.raises(ValueError):
        engine.recommend_focus('Center', expected_identity=engine.focus_identity() | {'model': 'old'})


def test_focus_fails_closed_for_unready_or_non_768_catalog():
    engine = RecommendationEngine(topics=catalog(), model=NoEncoding(), topic_vectors=vectors())
    with pytest.raises(RuntimeError):
        engine.focus_identity()
    bad = focus_engine(raw=vectors()[:, :2])
    with pytest.raises(RuntimeError):
        bad.recommend_focus('Center', expected_identity={})


@pytest.mark.skipif(os.getenv('OTHERWISE_RUN_REAL_FOCUS') != '1',
                    reason='Opt in to local cached MPNet verification.')
def test_real_catalog_focus_matches_packaged_identity():
    import json
    from explorer import load_catalog
    root = Path(__file__).resolve().parents[1]
    metadata = json.loads((root / 'data/galaxy-layout.json').read_text())['metadata']
    topics = load_catalog(root / 'data/topics.json')
    raw = np.load(root / '.cache/embeddings' / f'{metadata["embedding"]["identity"]}.npy',
                  allow_pickle=False)
    expected_identity = dict(catalog_sha256=metadata['catalog_sha256'], model=metadata['model'],
        embedding={k: metadata['embedding'][k] for k in ('sha256', 'dtype', 'shape')})
    assert hashlib.sha256(np.ascontiguousarray(raw).tobytes()).hexdigest() == expected_identity['embedding']['sha256']
    engine = RecommendationEngine(topics=topics, model=NoEncoding(),
                                  cache_dir=root / '.cache/embeddings', model_name=metadata['model'])
    engine.initialize()
    assert engine.focus_identity() == expected_identity
    original = np.asarray(raw, dtype=float)
    units = original / np.linalg.norm(original, axis=1, keepdims=True)
    by_id = {row['topic']: i for i, row in enumerate(topics)}
    total = 0
    for index in [0, len(topics) // 3, len(topics) // 2, len(topics) - 1]:
        topic_id = topics[index]['topic']
        result = engine.recommend_focus(topic_id, expected_identity=expected_identity, randomness=0)
        distances = np.arccos(np.clip(units @ units[index], -1, 1)) / np.pi
        assert result['seed_id'] == topic_id
        for row in result['recommendations']:
            source = topics[by_id[row['id']]]
            assert row['distance'] == pytest.approx(float(distances[by_id[row['id']]]), rel=0, abs=1e-12)
            assert .265 - 1e-9 <= row['distance'] <= .35 + 1e-9
            assert row['description'] == source['description']
            assert row['domain'] == source['domain']
            assert row['nearest_interest'] == topic_id
            assert row['id'] != topic_id
        total += len(result['recommendations'])
    assert total > 0
