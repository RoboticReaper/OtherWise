"""Original-vector galaxy math, identity and cache boundary tests."""
import importlib
import json
import math
from pathlib import Path

import numpy as np
import pytest


def module():
    try:
        return importlib.import_module("galaxy.preprocessing")
    except ModuleNotFoundError:
        pytest.fail("The independent galaxy preprocessing module is not implemented.")


def catalog():
    return [dict(topic=t, domain=d, description=f"Original {t}.", source="Public")
            for t, d in [("North", "A"), ("Near", "A"), ("East", "B"), ("South", "C")]]


def vectors():
    values = np.zeros((4, 768))
    for i, angle in enumerate([0, .1, .5, 1]):
        values[i, :2] = [math.cos(math.pi * angle), math.sin(math.pi * angle)]
    return values


def fast_projection(monkeypatch):
    # Only costly optional UMAP/MDS are replaced; all cache and distance work is real.
    m = module()
    monkeypatch.setattr(m, "project_layout", lambda topics, values, angular, parameters:
                        (values[:, :2], np.array([[float(i), 0.] for i in range(len({r["domain"] for r in topics}))])))
    return m


def build(m, tmp_path, **changes):
    arguments = dict(topics=catalog(), vectors=vectors(), embedding_identity="original-source",
                     cache_dir=tmp_path / "cache", output_path=tmp_path / "galaxy.json")
    arguments.update(changes)
    return m.build_galaxy(**arguments)


def test_angular_distance_normalizes_original_vectors():
    actual = module().angular_distances([[2., 0.], [0., 3.], [-4., 0.]])
    assert actual == pytest.approx(np.array([[0., .5, 1.], [.5, 0., .5], [1., .5, 0.]]))


def test_neighbors_exclude_self_sort_distance_and_break_ties_by_title():
    distances = np.array([[0, .5, .1, .5], [.5, 0, .4, .7], [.1, .4, 0, .6], [.5, .7, .6, 0]])
    result = module().nearest_neighbors(distances, ["Origin", "Zulu", "Close", "Alpha"], k=3)
    assert result[0] == [{"id": "Close", "distance": .1}, {"id": "Alpha", "distance": .5}, {"id": "Zulu", "distance": .5}]


def test_rms_standardization_removes_translation_and_uniform_scale():
    m = module()
    triangle = np.array([[0., 0.], [3., 0.], [0., 3.]])
    result = m.standardize(triangle)
    assert result.mean(axis=0) == pytest.approx([0., 0.])
    assert np.mean(np.sum(result ** 2, axis=1)) == pytest.approx(1.)
    assert m.standardize(7 * triangle + 12) == pytest.approx(result)
    with pytest.raises(ValueError, match="spread"):
        m.standardize(np.ones((3, 2)))


def test_anchor_affinities_use_top_three_and_temperature_18():
    actual = module().anchor_targets(np.array([[.4, .3, .2, .1]]),
        np.array([[1., 0.], [0., 1.], [-1., 0.], [100., 100.]]), top_k=3, temperature=18.)
    denominator = 1 + math.exp(-1.8) + math.exp(-3.6)
    assert actual[0] == pytest.approx([(1 - math.exp(-3.6)) / denominator, math.exp(-1.8) / denominator])


def test_asset_uses_canonical_titles_and_only_public_geometry(monkeypatch, tmp_path):
    result = build(fast_projection(monkeypatch), tmp_path)
    asset = result.asset
    assert not result.cache_hit
    assert asset["schema_version"] == 1
    assert [r["id"] for r in asset["topics"]] == ["North", "Near", "East", "South"]
    assert [r["id"] for r in asset["domains"]] == ["A", "B", "C"]
    assert asset["topics"][0]["neighbors"][0]["id"] == "Near"
    assert asset["topics"][0]["neighbors"][0]["distance"] == pytest.approx(.1)
    assert "Original North" not in json.dumps(asset)
    assert all(set(r) == {"id", "x", "y", "neighbors"} for r in asset["topics"])
    assert json.loads((tmp_path / "galaxy.json").read_text()) == asset


def test_domain_labels_follow_final_star_clusters_instead_of_separate_mds_anchors(monkeypatch, tmp_path):
    m = module()
    topics = [dict(topic=f"Star {i}", domain="A" if i < 5 else "B",
                   description="Public topic description.") for i in range(8)]
    positions = np.array([[0, 0], [.01, 0], [0, .01], [0, .02], [100, 100],
                          [5, 5], [5.01, 5], [5, 5.01]])
    far_anchors = np.array([[-10, 10], [10, -10]])
    monkeypatch.setattr(m, "project_layout", lambda *args: (positions, far_anchors))
    result = build(m, tmp_path, topics=topics, vectors=np.random.default_rng(7).normal(size=(8, 768)))
    for label in result.asset['domains']:
        own = [positions[i] for i, row in enumerate(topics) if row['domain'] == label['id']]
        point = np.array([label['x'], label['y']])
        assert any(np.array_equal(point, member) for member in own)
        center = np.array([0, 0] if label['id'] == 'A' else [5, 5])
        assert np.linalg.norm(point - center) < .1
    assert [[row['x'], row['y']] for row in result.asset['topics']] == positions.tolist()


def test_cache_hit_avoids_projection_and_republishes_output(monkeypatch, tmp_path):
    m = fast_projection(monkeypatch)
    first = build(m, tmp_path)
    (tmp_path / "galaxy.json").unlink()
    def unexpected(*args, **kwargs):
        raise AssertionError("Valid cache should avoid projection.")
    monkeypatch.setattr(m, "project_layout", unexpected)
    second = build(m, tmp_path)
    assert second.cache_hit and second.asset == first.asset
    assert json.loads((tmp_path / "galaxy.json").read_text()) == first.asset


@pytest.mark.parametrize("change", ["description", "domain", "source", "order", "model", "identity", "vectors", "parameters", "algorithm", "libraries"])
def test_cache_invalidates_for_every_source_identity(monkeypatch, tmp_path, change):
    m = fast_projection(monkeypatch)
    first = build(m, tmp_path)
    rows, values, kwargs = catalog(), vectors(), {}
    if change in {"description", "domain", "source"}:
        rows[0][change] += " changed"
    elif change == "order":
        rows, values = rows[::-1], values[::-1]
    elif change == "model":
        kwargs["model_name"] = "different-model"
    elif change == "identity":
        kwargs["embedding_identity"] = "different-source"
    elif change == "vectors":
        values[0, 2] = .25
    elif change == "parameters":
        kwargs["parameters"] = dict(m.DEFAULT_PARAMETERS, anchor_strength=.35)
    elif change == "algorithm":
        monkeypatch.setattr(m, "ALGORITHM_VERSION", "next-version")
    elif change == "libraries":
        monkeypatch.setattr(m, "numerical_versions", lambda: {"numpy": "next-version"})
    second = build(m, tmp_path, topics=rows, vectors=values, **kwargs)
    assert not second.cache_hit
    assert second.asset["cache_key"] != first.asset["cache_key"]


def test_reorder_keeps_coordinates_and_neighbors_associated_with_titles(monkeypatch, tmp_path):
    m = fast_projection(monkeypatch)
    first = build(m, tmp_path).asset
    second = build(m, tmp_path, topics=catalog()[::-1], vectors=vectors()[::-1]).asset
    assert {r["id"]: r for r in first["topics"]} == {r["id"]: r for r in second["topics"]}


@pytest.mark.parametrize("corruption", ["json", "checksum", "missing", "nan", "wrong_id", "self_neighbor", "unknown_neighbor", "duplicate_neighbor", "unordered", "metadata"])
def test_corrupt_cache_recovers(monkeypatch, tmp_path, corruption):
    m = fast_projection(monkeypatch)
    first = build(m, tmp_path)
    cache = Path(first.cache_path)
    if corruption == "json":
        cache.write_text("{not complete")
    else:
        envelope = json.loads(cache.read_text())
        asset, row = envelope["asset"], envelope["asset"]["topics"][0]
        if corruption == "checksum":
            row["x"] += 10
        elif corruption == "missing":
            asset["topics"].pop()
        elif corruption == "nan":
            row["x"] = float("nan")
        elif corruption == "wrong_id":
            row["id"] = "Wrong"
        elif corruption == "self_neighbor":
            row["neighbors"][0]["id"] = row["id"]
        elif corruption == "unknown_neighbor":
            row["neighbors"][0]["id"] = "Unknown"
        elif corruption == "duplicate_neighbor":
            row["neighbors"][1] = row["neighbors"][0]
        elif corruption == "unordered":
            row["neighbors"].reverse()
        elif corruption == "metadata":
            asset["metadata"]["model"] = "wrong model"
        if corruption not in {"checksum", "nan"}:
            envelope["asset_sha256"] = m.json_digest(asset)
        cache.write_text(json.dumps(envelope))
    repaired = build(m, tmp_path)
    assert not repaired.cache_hit and repaired.asset == first.asset
    assert build(m, tmp_path).cache_hit


def test_bad_vectors_and_duplicate_titles_do_not_publish(monkeypatch, tmp_path):
    m = fast_projection(monkeypatch)
    with pytest.raises(ValueError, match="768"):
        build(m, tmp_path, vectors=np.eye(4))
    bad = vectors()
    bad[0] = 0
    with pytest.raises(ValueError, match="zero"):
        build(m, tmp_path, vectors=bad)
    rows = catalog()
    rows[0]["topic"] = rows[1]["topic"]
    with pytest.raises(ValueError, match="unique"):
        build(m, tmp_path, topics=rows)
    assert not (tmp_path / "galaxy.json").exists()


def test_atomic_failure_preserves_previous_output_and_cleans_temp(monkeypatch, tmp_path):
    m = module()
    output = tmp_path / "asset.json"
    output.write_text('{"old":true}\n')
    def interrupted(*args):
        raise OSError("simulated interrupted replacement")
    monkeypatch.setattr(m.os, "replace", interrupted)
    with pytest.raises(OSError):
        m.atomic_json_write(output, {"new": True})
    assert output.read_text() == '{"old":true}\n'
    assert list(tmp_path.iterdir()) == [output]


def test_stdlib_validation_rejects_changed_catalog_and_unknown_neighbors(monkeypatch, tmp_path):
    asset = build(fast_projection(monkeypatch), tmp_path).asset
    validate = importlib.import_module("galaxy").validate_layout
    validate(asset, catalog())
    changed = catalog()
    changed[0]["description"] = "Updated original text."
    with pytest.raises(ValueError):
        validate(asset, changed)
    asset["topics"][0]["neighbors"][0]["id"] = "missing"
    with pytest.raises(ValueError):
        validate(asset, catalog())


def test_standalone_cli_reuses_original_embeddings_and_verified_cache(monkeypatch, tmp_path):
    import hashlib
    import subprocess
    import sys
    m = fast_projection(monkeypatch)
    source = tmp_path / "catalog.json"
    source.write_text(json.dumps(catalog()))
    identity = hashlib.sha256(json.dumps({"model": m.MODEL_NAME,
        "texts": [f"{r['topic']}: {r['description']}" for r in catalog()]},
        ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    embeddings = tmp_path / "embeddings"
    embeddings.mkdir()
    np.save(embeddings / f"{identity}.npy", vectors())
    first = build(m, tmp_path, embedding_identity=identity)
    output = tmp_path / "export.json"
    result = subprocess.run([sys.executable, "scripts/build_galaxy.py", "--catalog", str(source),
        "--embeddings-dir", str(embeddings), "--cache-dir", str(tmp_path / "cache"),
        "--output", str(output)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["cache_hit"] is True
    assert json.loads(output.read_text()) == first.asset


def test_standalone_cli_missing_embeddings_fails_before_output(tmp_path):
    import subprocess
    import sys
    source = tmp_path / "catalog.json"
    source.write_text(json.dumps(catalog()))
    output = tmp_path / "export.json"
    result = subprocess.run([sys.executable, "scripts/build_galaxy.py", "--catalog", str(source),
        "--embeddings-dir", str(tmp_path / "missing"), "--output", str(output)],
        capture_output=True, text=True)
    assert result.returncode != 0
    assert "--encode-missing" in result.stderr
    assert not output.exists()


def test_blend_keeps_exact_fifteen_percent_anchor_contribution():
    # Symmetric shapes have identity Procrustes rotation. The x/y stretch gives a
    # hand-calculated blend that would detect ignoring anchors or changing .15.
    graph = np.array([[1., 0.], [-1., 0.], [0., 1.], [0., -1.]])
    target = np.array([[2., 0.], [-2., 0.], [0., 1.], [0., -1.]])
    x = .85 + .15 * 2 / math.sqrt(2.5)
    y = .85 + .15 / math.sqrt(2.5)
    radius = math.sqrt((x*x + y*y) / 2)
    expected = np.array([[x, 0.], [-x, 0.], [0., y], [0., -y]]) / radius
    assert module().blend_layout(graph, target) == pytest.approx(expected)


def test_approved_b_projection_aligns_orientation_without_blending_anchors(monkeypatch):
    import sys
    import types
    import sklearn.manifold
    m = module()
    observed = {}
    anchors = np.array([[-1., -1.], [1., -1.], [1., 1.], [-1., 1.]])
    rectangle = anchors * [2., 1.]
    graph = rectangle @ np.array([[0., -1.], [1., 0.]]) * 8 + 10
    class RecordingUMAP:
        def __init__(self, **options):
            observed.update(options)
        def fit_transform(self, angular):
            return graph
    class FixedMDS:
        def __init__(self, **options):
            pass
        def fit_transform(self, distances):
            return anchors
    monkeypatch.setitem(sys.modules, 'umap', types.SimpleNamespace(UMAP=RecordingUMAP))
    monkeypatch.setattr(sklearn.manifold, 'MDS', FixedMDS)
    topics = [dict(topic=f'Topic {i}', domain=f'Domain {i}', description='Public') for i in range(4)]
    values = np.zeros((4, 768))
    values[:, :4] = np.eye(4)
    positions, _ = m.project_layout(topics, values, m.angular_distances(values), m.DEFAULT_PARAMETERS)
    assert observed['n_neighbors'] == 12
    assert observed['min_dist'] == .4
    assert observed['spread'] == 1.5
    assert observed['repulsion_strength'] == 2.5
    assert observed['random_state'] == 42
    assert observed['init'] == 'random'
    assert observed['n_epochs'] == 300
    # B uses MDS for orientation, with zero anchor interpolation: a rectangle
    # remains a rectangle instead of becoming the square MDS anchor target.
    assert positions == pytest.approx(rectangle / math.sqrt(5), abs=1e-7)
