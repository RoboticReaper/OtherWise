import math

import numpy as np
import pytest

from explorer import interest_texts, nearest_topics, parse_interests, recommend, topic_texts


def vectors(distances):
    """Unit vectors at known fractions of a half-turn from [1, 0]."""
    angles = np.asarray(distances) * np.pi
    return np.column_stack((np.cos(angles), np.sin(angles)))


def catalog(names):
    return [dict(topic=name, domain="Example", description=f"Exploring {name}.") for name in names]


def search(distances, **settings):
    names = [f"Topic {i}" for i in range(len(distances))]
    return recommend(catalog(names), vectors(distances), ["Interest"], [[1, 0]], **settings)


def test_search_respects_both_band_edges_and_never_fills_outside_it():
    # Dropping either band condition would admit the two excluded topics.
    result = search([0.1, 0.3, 0.4, 0.5, 0.6], radius=0.3, expansion=0.2, overlap=0, top_k=10)
    assert {row["topic"] for row in result} == {"Topic 1", "Topic 2", "Topic 3"}
    assert all(0.3 - 1e-9 <= row["distance"] <= 0.5 + 1e-9 for row in result)


def test_candidates_familiar_to_any_interest_are_not_new():
    # A centroid or averaging distances would wrongly accept the first topic.
    result = recommend(catalog(["Familiar", "Bridge"]), vectors([0.79, 0.4]),
                       ["First", "Second"], vectors([0, 0.8]),
                       radius=0.2, expansion=0.25, overlap=0, top_k=5)
    assert [row["topic"] for row in result] == ["Bridge"]
    assert result[0]["distance"] == pytest.approx(0.4)


def test_overlap_is_allowed_but_remains_a_minority_of_actual_results():
    result = search([0.29, 0.28, 0.31, 0.34, 0.37, 0.39],
                    radius=0.3, expansion=0.1, overlap=0.025, top_k=10)
    assert len(result) == 5
    assert sum(row["zone"] == "Familiar overlap" for row in result) == 1
    assert all(row["distance"] >= 0.275 for row in result)
    sparse = search([0.29, 0.28, 0.34], radius=0.3, expansion=0.1, overlap=0.025, top_k=10)
    assert len(sparse) == 1
    assert sparse[0]["zone"] == "New territory"


def test_exact_titles_and_near_identical_vectors_are_excluded():
    result = recommend(catalog([" MACHINE-learning ", "Synonym", "New idea"]),
                       vectors([0.35, 0.005, 0.4]), ["machine learning"], [[1, 0]],
                       radius=0, expansion=0.5, overlap=0, top_k=5)
    assert [row["topic"] for row in result] == ["New idea"]


def test_expansion_changes_recommendations_and_reports_nearest_input():
    near = search([0.32, 0.4, 0.5], radius=0.3, expansion=0.04, overlap=0, top_k=1)
    farther = search([0.32, 0.4, 0.5], radius=0.3, expansion=0.4, overlap=0, top_k=1)
    assert near[0]["topic"] == "Topic 0"
    assert farther[0]["topic"] == "Topic 2"
    assert farther[0]["nearest_interest"] == "Interest"
    assert farther[0]["boundary_offset"] == pytest.approx(0.2)


def test_diversity_selects_distinct_topics_over_duplicate_embeddings():
    result = recommend(catalog(["A", "Duplicate of A", "Different"]),
                       vectors([0.4, 0.4, -0.4]), ["Interest"], [[1, 0]],
                       radius=0.3, expansion=0.2, overlap=0, top_k=2, diversity=0.3, randomness=0)
    assert [row["topic"] for row in result] == ["A", "Different"]


def test_empty_band_returns_no_recommendations():
    assert search([0.1, 0.8], radius=0.3, expansion=0.1, overlap=0) == []


@pytest.mark.parametrize("settings", [
    {"radius": -0.1}, {"expansion": -0.1}, {"overlap": -0.1},
    {"radius": math.nan}, {"top_k": 0}, {"top_k": 2.5},
    {"diversity": 1.5}, {"max_overlap_fraction": 1.0},
])
def test_invalid_settings_are_rejected(settings):
    with pytest.raises(ValueError):
        search([0.4], **settings)


@pytest.mark.parametrize("interests,seed_vectors", [
    ([], np.empty((0, 2))), ([""], [[1, 0]]),
    (["One"], [[0, 0]]), (["One"], [[math.nan, 0]]),
    (["One", "Two"], [[1, 0]]), (["One"], [[1, 0, 0]]),
])
def test_invalid_interest_vectors_are_rejected(interests, seed_vectors):
    with pytest.raises(ValueError):
        recommend(catalog(["A"]), [[0, 1]], interests, seed_vectors)


def test_vector_magnitude_does_not_change_distance():
    result = recommend(catalog(["A"]), [[0, 5]], ["Interest"], [[12, 0]],
                       radius=0.3, expansion=0.3, overlap=0)
    assert result[0]["distance"] == pytest.approx(0.5)


def test_inputs_are_deduplicated_without_losing_the_original_phrase():
    assert parse_interests(" Gardening, gardening\nMachine learning; MACHINE-learning ") == [
        "Gardening", "Machine learning"]
    with pytest.raises(ValueError):
        parse_interests(" , ; \n")


def test_meaningful_punctuation_preserves_distinct_interests():
    assert parse_interests(["C++", "C#", "C", "c++"]) == ["C++", "C#", "C"]
    topics = catalog(["C", "C++", "C#"])
    assert interest_texts(["C++"], topics) == ["C++: Exploring C++."]


def test_known_titles_use_catalog_context_but_unknown_phrases_remain_intact():
    topics = catalog(["Gardening"])
    assert interest_texts(["GARDENING", "growing herbs on my balcony"], topics) == [
        topic_texts(topics)[0], "growing herbs on my balcony"]


def test_baseline_returns_nearest_topics_in_order_excluding_input_title():
    result = nearest_topics(catalog(["Interest", "Far", "Near"]), vectors([0, 0.5, 0.1]),
                            ["Interest"], [[1, 0]], top_k=2)
    assert [row["topic"] for row in result] == ["Near", "Far"]


def test_randomness_is_reproducible_with_a_seed_and_off_at_zero():
    distances = [0.399 + i * 0.0001 for i in range(16)]
    settings = dict(radius=0.3, expansion=0.2, overlap=0, top_k=5, diversity=0)
    a = search(distances, randomness=0.03, seed=42, **settings)
    assert a == search(distances, randomness=0.03, seed=42, **settings)
    assert a != search(distances, randomness=0.03, seed=43, **settings)
    assert search(distances, randomness=0, seed=1, **settings) == search(distances, randomness=0, seed=99, **settings)


def test_randomness_never_bypasses_band_or_familiar_overlap_quota():
    for seed in range(12):
        rows = search([0.1, 0.27, 0.28, 0.29, 0.31, 0.34, 0.37, 0.4, 0.7],
                      radius=0.3, expansion=0.1, overlap=0.02, top_k=10, randomness=0.1, seed=seed)
        assert len(rows) == 5
        assert all(0.28 - 1e-9 <= r['distance'] <= 0.4 + 1e-9 for r in rows)
        assert sum(r['zone'] == 'Familiar overlap' for r in rows) == 1


@pytest.mark.parametrize('settings', [{'randomness': -0.1}, {'randomness': float('nan')},
                                     {'seed': -1}, {'seed': 2.5}, {'seed': True}])
def test_invalid_randomness_options_are_rejected(settings):
    with pytest.raises(ValueError):
        search([0.4], **settings)
