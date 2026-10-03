from copy import deepcopy

import pytest
import feedback


def test_curiosity_and_difficulty_coexist_without_implying_known():
    p = feedback.new_profile()
    feedback.set_feedback(p, 'P', curious=True, known=False, difficulty='too_hard', level=3, area_ids=['cs'])
    assert p['items']['P']['curious'] is True
    assert p['items']['P']['known'] is False
    assert feedback.area_preferences(p)['cs']['level'] == 2
    assert feedback.area_preferences(p)['cs']['curiosity'] > 0
    assert 'music' not in feedback.area_preferences(p)


def test_repeated_saves_replace_rather_than_amplify_and_can_be_cleared():
    p = feedback.new_profile()
    for _ in range(3):
        feedback.set_feedback(p, 'P', curious=True, difficulty='too_basic', level=1, area_ids=['cs'])
    assert len(p['items']) == 1
    assert feedback.area_preferences(p)['cs']['level'] == 2
    feedback.set_feedback(p, 'P', curious=False, known=True, area_ids=['cs'])
    assert feedback.area_preferences(p)['cs']['curiosity'] == 0
    assert feedback.area_preferences(p)['cs']['level'] is None
    feedback.clear_feedback(p, 'P')
    assert not p['items']


def test_profile_round_trip_preserves_known_exposure_and_independent_preferences(tmp_path):
    p = feedback.new_profile()
    feedback.set_feedback(p, 'Q1', curious=True, known=True, area_ids=['a'])
    feedback.record_exposures(p, [{'id': 'Q1', 'area_id': 'a'}, {'id': 'Q2', 'area_id': 'a'}, {'id': 'Q3', 'area_id': 'b'}])
    path = tmp_path / 'private' / 'profile.json'
    feedback.save_profile(p, path)
    assert feedback.load_profile(path) == p
    assert p['exposures'] == {'a': 2, 'b': 1}
    assert feedback.load_profile(tmp_path / 'absent.json') == feedback.new_profile()


def test_invalid_profile_does_not_silently_replace_existing_data(tmp_path):
    path = tmp_path / 'profile.json'
    path.write_text('{broken')
    with pytest.raises(ValueError, match='profile'):
        feedback.load_profile(path)
    p = feedback.new_profile()
    p['items']['x'] = {'curious': 'yes'}
    with pytest.raises(ValueError):
        feedback.save_profile(p, path)
    assert path.read_text() == '{broken'


@pytest.mark.parametrize('change', [{'curious': 'yes'}, {'known': 1}, {'difficulty': 'bad'}, {'level': 0}, {'area_ids': 'cs'}])
def test_invalid_feedback_never_partially_mutates_profile(change):
    p = feedback.new_profile()
    original = deepcopy(p)
    with pytest.raises(ValueError):
        feedback.set_feedback(p, 'x', **change)
    assert p == original
