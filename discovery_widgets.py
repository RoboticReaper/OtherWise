"""Notebook controls for graph discovery; the search and profile also work without widgets."""
from __future__ import annotations

from copy import deepcopy
from html import escape

import ipywidgets as widgets
import numpy as np
from IPython.display import display

from explorer import interest_texts, parse_interests, recommend
from feedback import (PROFILE_PATH, clear_feedback, load_profile, record_exposures,
                      save_profile, set_feedback)
from graph_explorer import recommend_specific, select_areas

LEVELS = {None: 'Not yet reviewed', 1: 'Accessible introduction', 2: 'Some background helpful', 3: 'Technical treatment'}


def _link(text, url):
    text = escape(str(text))
    return f'<a href="{escape(url, quote=True)}" target="_blank" rel="noopener noreferrer">{text}</a>' if isinstance(url, str) and url.startswith('https://') else text


class DiscoveryPanel:
    def __init__(self, graph, concept_vectors, area_vectors, model, topics, topic_vectors, *,
                 interests, settings=None, profile_path=PROFILE_PATH):
        self.graph, self.concept_vectors, self.area_vectors = graph, concept_vectors, area_vectors
        self.model, self.topics, self.topic_vectors = model, topics, topic_vectors
        self.profile_path, self.profile = profile_path, load_profile(profile_path)
        self.nodes = {n['id']: n for n in graph['nodes']}
        self.last_rows, self.last_settings, self.last_inputs = [], {}, []
        self.last_seeds, self.last_areas, self._undo = None, [], None
        self._exposure_snapshot = {}
        cfg = dict(radius=.28, expansion=.07, overlap=.015, top_k=10, diversity=.2, randomness=.03, seed=42)
        cfg.update(settings or {})
        self.top_k = cfg['top_k']
        self.interest_input = widgets.Textarea(value=', '.join(interests), description='Interests:', layout=widgets.Layout(width='95%',height='60px'))
        self.radius = self._slider('Radius',cfg['radius'],.5)
        self.expansion = self._slider('Expansion',cfg['expansion'],.3)
        self.overlap = self._slider('Overlap',cfg['overlap'],.1)
        self.diversity = self._slider('Diversity',cfg['diversity'],.6,.01)
        self.randomness = self._slider('Variation',cfg['randomness'],.1)
        self.exploration = self._slider('Explore less-seen areas',.3,1.,.1)
        self.repeatable = widgets.Checkbox(value=True, description='Repeatable results')
        self.seed = widgets.BoundedIntText(value=cfg['seed'] if cfg.get('seed') is not None else 42, min=0,max=2**31-1,description='Seed:')
        self.search_button = widgets.Button(description='Explore specific ideas', button_style='primary',icon='search')
        self.undo_button = widgets.Button(description='Undo last feedback',disabled=True)
        self.status = widgets.HTML()
        self.summary = widgets.HTML()
        self.cards = widgets.VBox()
        self.profile_view = widgets.HTML()
        self.saved_choice = widgets.Dropdown(options=[],description='Saved rating:',layout=widgets.Layout(width='90%'))
        self.clear_button = widgets.Button(description='Clear selected rating',disabled=True)
        self.search_button.on_click(lambda _: self.search())
        self.undo_button.on_click(lambda _: self._handle(self.undo_feedback))
        self.clear_button.on_click(lambda _: self._handle(lambda: self.clear_rating(self.saved_choice.value)))
        controls = widgets.Accordion(children=[widgets.VBox([self.radius,self.expansion,self.overlap,self.diversity,self.randomness,widgets.HBox([self.repeatable,self.seed])])],selected_index=None)
        controls.set_title(0,'Distance and ranking settings')
        profile_box=widgets.Accordion(children=[widgets.VBox([self.profile_view,self.saved_choice,self.clear_button])],selected_index=None)
        profile_box.set_title(0,'Your local feedback')
        self.widget=widgets.VBox([self.interest_input,controls,self.exploration,
                                  widgets.HTML('<small>The exploration share reserves places for the least-shown eligible areas. It never widens your distance band.</small>'),
                                  widgets.HBox([self.search_button,self.undo_button]),self.status,self.summary,self.cards,profile_box])
        self._render_profile()

    @staticmethod
    def _slider(label,value,maximum,step=.005):
        return widgets.FloatSlider(value=value,min=0,max=maximum,step=step,description=label,
                                   readout_format='.3f',continuous_update=False,style={'description_width':'170px'},layout=widgets.Layout(width='600px'))

    def _handle(self, action):
        try:
            action()
        except (ValueError, OSError) as error:
            self.status.value=f'<b>{escape(str(error))}</b>'

    def search(self):
        self.search_button.disabled=True
        self.status.value='Finding specific ideas…'
        self.last_rows=[]
        self.cards.children=()
        self.summary.value=''
        try:
            inputs=parse_interests(self.interest_input.value)
            seeds=self.model.encode(interest_texts(inputs,self.topics),normalize_embeddings=True,show_progress_bar=False)
            actual_seed=self.seed.value if self.repeatable.value else int(np.random.default_rng().integers(0,2**31))
            settings=dict(radius=self.radius.value,expansion=self.expansion.value,overlap=self.overlap.value,
                          top_k=self.top_k,diversity=self.diversity.value,randomness=self.randomness.value,
                          seed=actual_seed,exploration_fraction=self.exploration.value)
            queries=[seeds]
            if self.topics:
                broad=recommend(self.topics,self.topic_vectors,inputs,seeds, radius=settings['radius'],expansion=settings['expansion'],
                                overlap=settings['overlap'],top_k=24,diversity=settings['diversity'],randomness=0)
                if broad:
                    queries.append(np.asarray(self.topic_vectors)[[r['catalog_index'] for r in broad]])
            areas=select_areas(self.graph['areas'],self.area_vectors,np.vstack(queries),limit=8)
            self.last_inputs,self.last_seeds,self.last_settings,self.last_areas=inputs,seeds,settings,areas
            self._exposure_snapshot=deepcopy(self.profile['exposures'])
            self._rerank()
            updated_profile=deepcopy(self.profile)
            record_exposures(updated_profile,self.last_rows)
            save_profile(updated_profile,self.profile_path)
            self.profile=updated_profile
            self._render_profile()
            self.status.value='Results use your current feedback. Changes to the controls apply on the next Explore click.'
        except (ValueError,OSError) as error:
            self.last_rows=[]
            self.last_seeds=None
            self.cards.children=()
            self.summary.value=''
            self.status.value=f'<b>{escape(str(error))}</b>'
        finally:
            self.search_button.disabled=False
        return self.last_rows

    def _rerank(self):
        if self.last_seeds is None:
            self._render_profile()
            return
        ranking_profile=deepcopy(self.profile)
        # Hold exposure counts and random draw fixed when reranking feedback so
        # the immediate comparison reflects the rating, not another search.
        ranking_profile['exposures']=self._exposure_snapshot
        self.last_rows=recommend_specific(self.graph,self.concept_vectors,self.last_inputs,self.last_seeds,
                                          area_ids=self.last_areas,profile=ranking_profile,**self.last_settings)
        self._render_results()
        self._render_profile()

    def save_rating(self,concept_id,*,curious,known,difficulty):
        row=next((r for r in self.last_rows if r['id']==concept_id),None)
        if row is None:
            raise ValueError('This card is no longer in the current results. Use a current card or the saved-feedback controls.')
        previous=deepcopy(self.profile['items'].get(concept_id))
        set_feedback(self.profile,concept_id,curious=curious,known=known,difficulty=difficulty,
                     level=row.get('level'),area_ids=[row['area_id']])
        try:
            save_profile(self.profile,self.profile_path)
        except OSError:
            self._restore(concept_id,previous)
            raise
        self._undo=(concept_id,previous)
        self.undo_button.disabled=False
        self._rerank()
        self.status.value=f'Feedback saved for {escape(self.nodes[concept_id]["topic"])}. Results have been reranked.'

    def _restore(self,concept_id,rating):
        if rating is None:
            clear_feedback(self.profile,concept_id)
        else:
            self.profile['items'][concept_id]=rating

    def clear_rating(self,concept_id):
        if concept_id not in self.profile['items']:
            return
        previous=deepcopy(self.profile['items'][concept_id])
        clear_feedback(self.profile,concept_id)
        try:
            save_profile(self.profile,self.profile_path)
        except OSError:
            self._restore(concept_id,previous)
            raise
        self._undo=(concept_id,previous)
        self.undo_button.disabled=False
        self._rerank()
        self.status.value='Rating cleared. Other saved feedback remains in use.'

    def undo_feedback(self):
        if self._undo is None:
            return
        concept_id,old=self._undo
        current=deepcopy(self.profile['items'].get(concept_id))
        self._restore(concept_id,old)
        try:
            save_profile(self.profile,self.profile_path)
        except OSError:
            self._restore(concept_id,current)
            raise
        self._undo=None
        self.undo_button.disabled=True
        self._rerank()
        self.status.value='Last feedback change undone.'

    def _render_results(self):
        rows=self.last_rows
        if not rows:
            self.summary.value='<b>No specific concepts fit this band in the selected graph areas.</b> Adjust the band or interests; snapshot coverage is finite.'
            self.cards.children=()
            return
        target,achieved=rows[0]['exploration_target'],rows[0]['exploration_achieved']
        familiar=sum(r['zone']=='Familiar overlap' for r in rows)
        self.summary.value=(f'<b>{len(rows)} specific ideas</b> · {familiar} familiar bridges · '
                            f'{achieved}/{target} reserved exploration places filled · seed {self.last_settings["seed"]}')
        cards=[]
        for row in rows:
            path=' → '.join(_link(self.nodes[n]['topic'],self.nodes[n].get('source_url')) for n in row['path_ids'])
            hook=row.get('hook') or row['description']
            text=(f'<h4 style="margin:4px 0">{_link(row["topic"],row.get("source_url"))}</h4>'
                  f'<p style="margin:4px 0">{escape(hook)}</p><small>{path}<br>'
                  f'Distance {row["distance"]:.3f} · {escape(LEVELS[row.get("level")])}'
                  + (' · Reserved exploration pick' if row['exploration_pick'] else '')+'</small>')
            rating=self.profile['items'].get(row['id'],{})
            curious=widgets.Checkbox(value=rating.get('curious',False),description='Curious',indent=False,layout=widgets.Layout(width='115px'))
            known=widgets.Checkbox(value=rating.get('known',False),description='Already know',indent=False,layout=widgets.Layout(width='150px'))
            difficulty=widgets.Dropdown(options=[('No difficulty feedback','none'),('Too basic','too_basic'),('Too hard','too_hard')],value=rating.get('difficulty','none'),layout=widgets.Layout(width='210px'))
            save=widgets.Button(description='Save feedback',layout=widgets.Layout(width='135px'))
            def on_save(_,concept_id=row['id'],c=curious,k=known,d=difficulty):
                self._handle(lambda:self.save_rating(concept_id,curious=c.value,known=k.value,difficulty=d.value))
            save.on_click(on_save)
            card=widgets.VBox([widgets.HTML(text),widgets.HBox([curious,known,difficulty,save],layout=widgets.Layout(flex_flow='row wrap'))],
                               layout=widgets.Layout(border='1px solid #ccc',padding='10px',margin='4px 0'))
            cards.append(card)
        self.cards.children=tuple(cards)

    def _render_profile(self):
        entries=self.profile['items']
        self.profile_view.value=(f'<p>{len(entries)} saved concept ratings. Curiosity, familiarity and difficulty are independent. '
                                 'Levels are editorial estimates; unrated concepts do not imply a learning level.</p>'
                                 + ''.join(f'<div><b>{escape(self.nodes.get(k,{}).get("topic",k))}</b>: curious={v["curious"]}, known={v["known"]}, {escape(v["difficulty"])}.</div>' for k,v in entries.items()))
        self.saved_choice.options=[(self.nodes.get(k,{}).get('topic',k),k) for k in entries]
        self.clear_button.disabled=not bool(entries)

    def display(self):
        display(self.widget)
