"""Exact original-vector neighbors without retaining all catalog distances."""
import math
import importlib.util

import numpy as np
import pytest

from galaxy import preprocessing as galaxy


def test_blockwise_neighbors_match_full_brute_force_with_ties_at_cutoff():
    # Dropping a tied candidate during partial selection would lose Alpha here.
    ids = ["Origin", "Zulu", "Beta", "Alpha", "Opposite", "Near"]
    vectors = np.zeros((6, 768))
    vectors[:, :2] = [[1, 0], [0, 1], [0, 1], [0, 1], [-1, 0], [1, 1]]
    indices, distances = galaxy.exact_angular_neighbors(vectors, ids, k=3, block_size=2)
    assert [ids[index] for index in indices[0]] == ["Near", "Alpha", "Beta"]
    assert distances[0] == pytest.approx([.25, .5, .5])
    # Independent full-matrix oracle, including every row and self exclusion.
    units = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
    full = np.arccos(np.clip(units @ units.T, -1, 1)) / math.pi
    for row in range(len(ids)):
        expected = sorted((float(full[row, other]), ids[other], other)
                          for other in range(len(ids)) if other != row)[:3]
        assert indices[row].tolist() == [entry[2] for entry in expected]
        assert distances[row] == pytest.approx([entry[0] for entry in expected], abs=1e-14)


@pytest.mark.skipif(importlib.util.find_spec("umap") is None, reason="Optional offline layout dependencies")
def test_whole_catalog_sparse_build_publishes_exact_neighbors_without_dense_distances(monkeypatch, tmp_path):
    # Taking the dense distance route for a large pool must fail before publication.
    rng = np.random.default_rng(7)
    vectors = rng.normal(size=(48, 768))
    topics = [dict(topic=f"Topic {index:03}", domain=f"Domain {index % 3}",
                   description="Original description.") for index in range(len(vectors))]
    def forbidden(*args, **kwargs):
        raise AssertionError("Large catalogs cannot allocate a full distance matrix.")
    monkeypatch.setattr(galaxy, "angular_distances", forbidden)
    parameters = dict(galaxy.DEFAULT_PARAMETERS, dense_topic_limit=8, distance_block_size=7,
                      n_neighbors=5, neighbor_count=3)
    result = galaxy.build_galaxy(topics=topics, vectors=vectors, embedding_identity="fixture",
        cache_dir=tmp_path / "cache", output_path=tmp_path / "galaxy.json", parameters=parameters)
    assert result.asset["metadata"]["distance_storage"] == "exact-blockwise-knn"
    assert all(np.isfinite([row["x"], row["y"]]).all() for row in result.asset["topics"])
    units = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
    full = np.arccos(np.clip(units @ units.T, -1, 1)) / math.pi
    for index, row in enumerate(result.asset["topics"]):
        expected = sorted((float(full[index, other]), topics[other]["topic"])
            for other in range(len(topics)) if other != index)[:3]
        assert [neighbor["id"] for neighbor in row["neighbors"]] == [entry[1] for entry in expected]
        assert [neighbor["distance"] for neighbor in row["neighbors"]] == pytest.approx(
            [entry[0] for entry in expected], abs=1e-14)
    # Persisted cache republishes the real geometry without rerunning layout.
    reused = galaxy.build_galaxy(topics=topics, vectors=vectors, embedding_identity="fixture",
        cache_dir=tmp_path / "cache", output_path=tmp_path / "copy.json", parameters=parameters)
    assert reused.cache_hit and reused.asset == result.asset
