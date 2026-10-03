"""Service behavior using hand-calculated angular distances, without downloads."""

import importlib
import math

import numpy as np
import pytest


def service_module():
    try:
        return importlib.import_module("service.engine")
    except ModuleNotFoundError:
        pytest.fail("The recommendation service has not been implemented.")


def vector(distance):
    return [math.cos(distance * math.pi), math.sin(distance * math.pi)]


def rows(names):
    return [dict(topic=name, domain="Example", description=f"Exploring {name}.") for name in names]


class FixedModel:
    def __init__(self, mapping):
        self.mapping = mapping

    def encode(self, texts, **kwargs):
        return np.asarray([vector(self.mapping[text.split(":", 1)[0]]) for text in texts])


def make_engine(names, distances, interests=None):
    mapping = dict(zip(names, distances)) | (interests or {"First": 0, "Second": 0.7})
    engine = service_module().RecommendationEngine(
        topics=rows(names), model=FixedModel(mapping),
        topic_vectors=np.asarray([vector(d) for d in distances]),
    )
    engine.initialize()
    return engine


def test_path_follows_focus_and_excludes_every_approved_title():
    engine = make_engine(["Second", "First bridge", "Second bridge", "Outside"], [.31, .32, 1.02, .5])
    result = engine.recommend(["First", "Second"], mode="path", focus="First", expansion_level=0, limit=10)
    assert [row["id"] for row in result] == ["First bridge"]
    assert result[0]["nearest_interest"] == "First"
    assert result[0]["distance"] == pytest.approx(.32)
    assert result[0]["boundary_offset"] == pytest.approx(.04)


def test_global_uses_nearest_individual_interest():
    engine = make_engine(["First bridge", "Second bridge", "Familiar to second"], [.32, 1.02, .71])
    result = engine.recommend(["First", "Second"], mode="global", focus=None, expansion_level=0, limit=10)
    assert {row["id"] for row in result} == {"First bridge", "Second bridge"}
    assert {row["nearest_interest"] for row in result} == {"First", "Second"}


def test_path_excludes_near_identical_topics_for_other_approved_interests():
    engine = make_engine(["Second synonym", "Bridge"], [.32, -.32], {"First": 0, "Second": .33})
    result = engine.recommend(["First", "Second"], mode="path", focus="First", expansion_level=0, limit=10)
    assert [row["id"] for row in result] == ["Bridge"]


def test_expansion_levels_preserve_band_and_never_fill_empty_results():
    engine = make_engine(["Too close", "Base", "Level eight", "Too far"], [.1, .32, .42, .44])
    base = engine.recommend(["First"], mode="global", focus=None, expansion_level=0, limit=20)
    expanded = engine.recommend(["First"], mode="global", focus=None, expansion_level=8, limit=20)
    assert [row["id"] for row in base] == ["Base"]
    assert {row["id"] for row in expanded} == {"Base", "Level eight"}
    assert all(.265 - 1e-9 <= row["distance"] <= .43 + 1e-9 for row in expanded)
    empty = make_engine(["Too far"], [.8])
    assert empty.recommend(["First"], mode="global", focus=None, expansion_level=8, limit=20) == []


def test_recommendations_are_bounded_unique_and_have_exact_public_contract():
    engine = make_engine(["A", "B", "C"], [.32, .33, .34])
    result = engine.recommend(["First", "FIRST"], mode="global", focus=None, expansion_level=0, limit=2)
    assert len(result) == 2
    assert len({row["id"] for row in result}) == 2
    assert all(row["id"] == row["topic"] for row in result)
    assert set(result[0]) == {"id", "topic", "domain", "description", "nearest_interest", "distance", "boundary_offset", "zone"}


def test_missing_path_focus_uses_most_recent_keyword():
    engine = make_engine(["First bridge", "Second bridge"], [.32, 1.02])
    result = engine.recommend(["First", "Second"], mode="path", focus=None, expansion_level=0, limit=10)
    assert [row["id"] for row in result] == ["Second bridge"]


def test_catalog_cache_reuses_embeddings_but_invalidates_for_catalog_and_model(tmp_path):
    module = service_module()
    topics = rows(["A", "B"])
    first = module.RecommendationEngine(topics=topics, model=FixedModel({"A": .32, "B": .33}), cache_dir=tmp_path, model_name="model-a")
    first.initialize()

    class NoEncoding:
        def encode(self, *args, **kwargs):
            raise AssertionError("Cached catalog should not be encoded again.")

    cached = module.RecommendationEngine(topics=topics, model=NoEncoding(), cache_dir=tmp_path, model_name="model-a")
    cached.initialize()
    np.testing.assert_allclose(cached.topic_vectors, first.topic_vectors)
    changed = module.RecommendationEngine(topics=rows(["C"]), model=FixedModel({"C": .34}), cache_dir=tmp_path, model_name="model-a")
    changed.initialize()
    other_model = module.RecommendationEngine(topics=topics, model=FixedModel({"A": .2, "B": .3}), cache_dir=tmp_path, model_name="model-b")
    other_model.initialize()
    assert len(list(tmp_path.glob("*.npy"))) == 3
    assert not np.allclose(other_model.topic_vectors, first.topic_vectors)


def test_corrupt_cache_is_recomputed(tmp_path):
    module = service_module()
    engine = module.RecommendationEngine(topics=rows(["A"]), model=FixedModel({"A": .32}), cache_dir=tmp_path)
    engine.initialize()
    next(tmp_path.glob("*.npy")).write_bytes(b"not an embedding array")
    fresh = module.RecommendationEngine(topics=rows(["A"]), model=FixedModel({"A": .32}), cache_dir=tmp_path)
    fresh.initialize()
    np.testing.assert_allclose(fresh.topic_vectors, [vector(.32)])


def test_model_device_is_optional_and_portable():
    import inspect
    from explorer import load_model

    assert "device" in inspect.signature(load_model).parameters
    assert inspect.signature(load_model).parameters["device"].default is None


def test_configured_expansion_adds_progress_and_never_widens_an_empty_band():
    engine = make_engine(["Below", "Base", "Later", "Above"], [.2, .42, .5, .61])
    options = dict(mode="path", focus="First", limit=50, radius=.4, expansion=.05,
                   overlap=0, randomness=0)
    base = engine.recommend(["First"], expansion_level=0, **options)
    later = engine.recommend(["First"], expansion_level=8, **options)
    assert [row["id"] for row in base] == ["Base"]
    assert {row["id"] for row in later} == {"Base", "Later"}
    assert all(.4 <= row["distance"] <= .53 for row in later)
    assert engine.recommend(["First"], mode="path", focus="First", expansion_level=8,
                            limit=100, radius=.8, expansion=.01, overlap=0) == []


def test_expansion_progress_is_clamped_when_the_base_is_already_one():
    engine = make_engine(["Opposite"], [1])
    result = engine.recommend(["First"], mode="global", focus=None, expansion_level=8,
                              limit=100, radius=0, expansion=1, randomness=0)
    assert [row["id"] for row in result] == ["Opposite"]


def test_custom_diversity_and_disabled_randomness_affect_real_ranking():
    engine = make_engine(["A", "Duplicate of A", "Different"], [.4, .4, -.4])
    options = dict(mode="path", focus="First", expansion_level=0, limit=2,
                   radius=.3, expansion=.2, overlap=0, randomness=0)
    ordinary = engine.recommend(["First"], diversity=0, **options)
    diverse = engine.recommend(["First"], diversity=.3, **options)
    assert [row["id"] for row in ordinary] == ["A", "Duplicate of A"]
    assert [row["id"] for row in diverse] == ["A", "Different"]


@pytest.mark.parametrize("name", ["radius", "expansion", "overlap", "diversity", "max_overlap_fraction", "randomness"])
@pytest.mark.parametrize("value", [True, "0.2", None, -.01, 1.01, math.nan, math.inf, -math.inf])
def test_direct_engine_rejects_invalid_controls_before_encoding(name, value):
    engine = make_engine(["A"], [.32])

    class NoEncoding:
        def encode(self, *args, **kwargs):
            raise AssertionError("Invalid controls must be rejected before model inference.")

    engine.model = NoEncoding()
    with pytest.raises(ValueError):
        engine.recommend(["First"], mode="path", focus="First", expansion_level=0,
                         limit=10, **{name: value})


@pytest.mark.parametrize("patch", [{"limit": 101}, {"limit": True}, {"max_overlap_fraction": .96}])
def test_direct_engine_enforces_request_capacity_and_familiar_share_bounds(patch):
    engine = make_engine(["A"], [.32])
    with pytest.raises(ValueError):
        engine.recommend(["First"], **(dict(mode="path", focus="First", expansion_level=0, limit=10) | patch))
