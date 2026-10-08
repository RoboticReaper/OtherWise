import pytest

from recommendation_lab.inventory import Inventory, InventoryConflict


def inventory():
    broad = [
        dict(topic='Go', description='Territorial strategy in a board game.', source='ProductSpace'),
        dict(topic='Go (game)', description='A two-player board game.', wikidata_id='Q11413'),
        dict(topic='Fermentation', description='Preserving foods using microorganisms.', source='ProductSpace'),
    ]
    graph = dict(nodes=[dict(id='Q41760', kind='concept', topic='Fermentation',
                            description='Energy production without oxygen.', wikidata_id='Q41760')])
    registry = dict(version=1, equivalences=[dict(kind='broad', index=0, id='Q11413',
                    evidence='https://www.wikidata.org/wiki/Q11413')], aliases={}, resolver_concepts=[
        dict(id='Q28865', topic='Python (programming language)', description='A programming language.',
             aliases=['Python', 'Python programming'], source_url='https://www.wikidata.org/wiki/Q28865'),
        dict(id='Q271218', topic='Python (snake genus)', description='A genus of snakes.',
             aliases=['Python', 'Python snake'], source_url='https://www.wikidata.org/wiki/Q271218'),
    ])
    return Inventory.from_sources(broad, graph, registry)


def test_only_source_identity_merges_and_descriptions_survive():
    inv = inventory()
    assert inv.source_ids['broad'][0] == inv.source_ids['broad'][1] == 'Q11413'
    assert inv.source_ids['broad'][2] != 'Q41760'
    assert len(inv.concepts['Q11413']['records']) == 2
    assert len(inv.aliases['fermentation']) == 2


def test_local_identity_survives_label_edit_and_content_changes_version():
    a = Inventory.from_sources([dict(topic='Old label', description='First description.')], dict(nodes=[]))
    b = Inventory.from_sources([dict(topic='New label', description='First description.')], dict(nodes=[]))
    assert a.source_ids == b.source_ids
    assert a.version != b.version


def test_ambiguous_alias_does_not_guess_even_with_context():
    inv = inventory()
    result = inv.resolve(['Python', 'programming'])
    assert result[0]['status'] == 'clarification_needed'
    assert {c['id'] for c in result[0]['choices']} == {'Q28865', 'Q271218'}
    assert result[1]['status'] == 'unresolved_phrase'


def test_explicit_choice_is_checked_against_phrase_and_version():
    inv = inventory()
    selected = inv.resolve([dict(phrase='Python', concept_id='Q28865')], inventory_version=inv.version)
    assert selected[0]['concept_id'] == 'Q28865'
    assert selected[0]['text'] == inv.text('Q28865')
    with pytest.raises(InventoryConflict):
        inv.resolve([dict(phrase='Python', concept_id='Q28865')], inventory_version='stale')
    with pytest.raises(ValueError, match='offered'):
        inv.resolve([dict(phrase='Python', concept_id='Q11413')], inventory_version=inv.version)


def test_aliases_resolve_to_same_known_identity():
    inv = inventory()
    assert inv.resolve(['Go (game)'])[0]['concept_id'] == 'Q11413'
    assert inv.resolve(['Go'])[0]['concept_id'] == 'Q11413'
    with pytest.raises(ValueError, match='Duplicate'):
        inv.resolve(['Go', 'Go (game)'])


def test_public_registry_has_reviewed_sport_and_game_identities_and_distinct_senses():
    import json
    from explorer import ROOT, load_catalog
    from graph_explorer import load_graph
    inv = Inventory.from_sources(load_catalog(),load_graph(),json.loads((ROOT/'data/recommendation-identities.json').read_text()))
    for phrase,cid in [('soccer','Q2736'),('Football (soccer)','Q2736'),('Tennis','Q847'),
                       ('Go (game)','Q11413'),('Python programming','Q28865'),('Java island','Q3757'),
                       ('Mercury metal','Q925'),('metabolic fermentation','Q41760')]:
        assert inv.resolve([phrase])[0]['concept_id'] == cid
    for phrase in ('Go','Python','Java','Mercury','Fermentation'):
        assert inv.resolve([phrase])[0]['status'] == 'clarification_needed'
    assert inv.resolve(['food fermentation'])[0]['concept_id'] != 'Q41760'


def test_authored_equivalence_preserves_authored_source_locator():
    record = inventory().concepts['Q11413']['records'][0]
    assert record['source_url'] == 'data/topics.json#record-0'
    assert record['equivalence_evidence'] == 'https://www.wikidata.org/wiki/Q11413'


def test_selected_meaning_must_be_in_recomputed_displayed_choices():
    inv = inventory()
    inv.aliases['many senses'] = set(inv.concepts)
    # Add enough supported choices to exceed the display cap.
    for i in range(6):
        inv.concepts[f'Q{i+900}'] = dict(id=f'Q{i+900}',topic=f'sense {i}',description='A supported sense.',source_url='source')
        inv.aliases['many senses'].add(f'Q{i+900}')
    choices = inv.resolve(['many senses'])[0]['choices']
    hidden = next(iter(inv.aliases['many senses']-{r['id'] for r in choices}))
    with pytest.raises(ValueError,match='offered'):
        inv.resolve([dict(phrase='many senses',concept_id=hidden)],inventory_version=inv.version)


@pytest.mark.parametrize('value', [[], [''], ['x' * 121], ['Python\x00'], [123], ['a'] * 41])
def test_invalid_interests_fail(value):
    with pytest.raises(ValueError):
        inventory().resolve(value)
