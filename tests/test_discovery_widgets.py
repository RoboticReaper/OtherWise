import json
import numpy as np
import pytest
from discovery_widgets import DiscoveryPanel


class FixedEncoder:
    def encode(self, texts, **kwargs):
        return np.tile([1., 0.], (len(texts), 1))


def panel(tmp_path):
    nodes = [dict(id='cat',topic='Computation',description='Computation',kind='category')]
    nodes += [dict(id=f'Q{i}',topic=f'Problem {i}',description=f'A concrete problem {i}.',kind='concept',level=i+1,source_url='https://example.org') for i in range(3)]
    graph=dict(version=1,metadata={},areas=[dict(id='cs',topic='Computation',description='Study of computation',domain='Computing',category_id='cat')],nodes=nodes,
               edges=[dict(source='cat',target=f'Q{i}',relation='contains_concept') for i in range(3)])
    vectors=np.tile([np.cos(.325*np.pi),np.sin(.325*np.pi)],(3,1))
    return DiscoveryPanel(graph,vectors,[[1,0]],FixedEncoder(),[],np.empty((0,2)),
                          interests=['Computer science'],settings=dict(radius=.25,expansion=.15,overlap=0,top_k=3,randomness=0),
                          profile_path=tmp_path/'profile.json')


def test_ui_saves_combined_feedback_reranks_and_undo_restores(tmp_path):
    p=panel(tmp_path)
    p.search()
    before=p.last_settings.copy()
    p.save_rating('Q1',curious=True,known=False,difficulty='too_hard')
    saved=json.loads((tmp_path/'profile.json').read_text())
    assert saved['items']['Q1']['curious'] and saved['items']['Q1']['difficulty']=='too_hard'
    assert saved['items']['Q1']['known'] is False
    assert p.last_rows[0]['level']==1
    assert p.last_settings==before
    p.undo_feedback()
    assert not p.profile['items']


def test_mark_known_removes_card_and_clear_restores_it(tmp_path):
    p=panel(tmp_path);p.search()
    p.save_rating('Q0',curious=False,known=True,difficulty='none')
    assert 'Q0' not in {r['id'] for r in p.last_rows}
    p.clear_rating('Q0')
    assert 'Q0' in {r['id'] for r in p.last_rows}


def test_invalid_search_clears_stale_results_and_button_recovers(tmp_path):
    p=panel(tmp_path);p.search()
    p.interest_input.value=' , '
    p.search_button.click()
    assert not p.last_rows
    assert p.search_button.disabled is False
    assert p.status.value


def test_failed_save_does_not_count_a_cleared_search_as_exposure(tmp_path,monkeypatch):
    p=panel(tmp_path)
    with monkeypatch.context() as patch:
        def fail(*args):
            raise OSError('disk full')
        patch.setattr('discovery_widgets.save_profile',fail)
        p.search_button.click()
        assert not p.last_rows
        assert not p.profile['exposures']
        assert not (tmp_path/'profile.json').exists()
    p.search_button.click()
    assert len(p.last_rows)==3
    saved=json.loads((tmp_path/'profile.json').read_text())
    assert saved['exposures']=={'cs':3}
    assert p.profile==saved
