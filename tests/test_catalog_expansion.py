"""Keep source-list parsing, canonical IDs and existing interests intact."""
from scripts import import_expanded_catalog as importer


def test_vital_parser_uses_article_target_not_navigation_or_display_markup():
    text = '''{{navigation|[[Example]]}}
=Technology=
==Computing==
# {{Icon|GA}} ''' + "'''[[Human–computer interaction|HCI]]'''" + ''' ([[Wikipedia:Vital articles/Level 4|Level 4]])
## [[C++]]
# [[Star Trek: Discovery]]
# [[Category:Computing]]
==Specific companies==
# [[Acme Corporation]]
'''
    rows = importer.parse_vital_page({"parse": {"title": "Wikipedia:Vital articles/Level 5/Technology/Computing",
        "revid": 123, "wikitext": {"*": text}}})
    assert [r["article"] for r in rows] == ["Human–computer interaction", "C++", "Star Trek: Discovery"]
    assert rows[0]["domain"] == "Computing & information"
    assert rows[0]["list_revision"] == 123


def test_page_resolution_follows_normalization_and_redirects_to_one_entity():
    response = {"query": {
        "normalized": [{"from": "human_computer_interaction", "to": "Human computer interaction"}],
        "redirects": [{"from": "Human computer interaction", "to": "Human–computer interaction"}],
        "pages": {"42": {"title": "Human–computer interaction", "pageprops": {"wikibase_item": "Q47146"}},
                  "-1": {"title": "Absent", "missing": ""}}}}
    assert importer.resolve_page_items(response, ["human_computer_interaction", "Absent"]) == {
        "human_computer_interaction": ("Human–computer interaction", "Q47146")}


def entity(qid, description, instance=None):
    return {"id": qid, "descriptions": {"en": {"value": description}}, "lastrevid": 8,
            "claims": {"P31": [] if not instance else [{"mainsnak": {"datavalue": {"value": {"id": instance}}}}]}}


def test_merge_preserves_incumbents_and_filters_duplicate_entities_people_and_empty_descriptions():
    retained = [{"topic": "Gardening", "domain": "Home & crafts", "description": "Growing plants as a hobby", "source": "ProductSpace"},
                {"topic": "HCI", "domain": "Computing & information", "description": "Study of interaction between people and computers", "source": "Wikidata", "wikidata_id": "Q47146"}]
    candidates = [{"article": title, "qid": qid, "domain": "Computing & information", "list_page": "List", "list_revision": 2, "subsection": "Computing"}
                  for title, qid in [("Human–computer interaction", "Q47146"), ("Interaction design", "Q132536"),
                                     ("A Person", "Q1"), ("Empty", "Q2"), ("interaction-design", "Q3")]]
    entities = {"Q47146": entity("Q47146", "a different description"),
                "Q132536": entity("Q132536", "design of interactive products and services"),
                "Q1": entity("Q1", "American software engineer", "Q5"),
                "Q2": entity("Q2", ""), "Q3": entity("Q3", "duplicate normalized topic title")}
    rows, counts = importer.merge_catalog(retained, candidates, entities)
    assert rows[:2] == retained
    assert [r["topic"] for r in rows] == ["Gardening", "HCI", "Interaction design"]
    assert rows[2]["wikidata_id"] == "Q132536"
    assert rows[2]["source_revision"] == 8
    assert counts["duplicate_title_or_entity"] == 2
    assert counts["excluded_entity_type"] == 1
    assert counts["missing_or_short_description"] == 1


def test_merge_does_not_truncate_a_domain_at_160():
    retained = [{"topic": f"Interest {i}", "domain": "Computing & information", "description": "A useful practical interest", "source": "ProductSpace"} for i in range(170)]
    rows, _ = importer.merge_catalog(retained, [], {})
    assert len(rows) == 170


def test_philosophy_and_religion_are_separate_despite_the_shared_page_title():
    page = "Wikipedia:Vital articles/Level 5/Philosophy and religion"
    assert importer.domain_for(page, {1: "Philosophy and religion", 2: "Philosophy", 3: "Ethics"}) == "Philosophy"
    assert importer.domain_for(page, {1: "Philosophy and religion", 2: "Religion", 3: "Buddhism"}) == "Religion & spirituality"


def test_source_cache_reuses_successful_public_responses_offline(tmp_path, monkeypatch):
    class Response:
        status_code = 200
        def raise_for_status(self): pass
        def json(self): return {"parse": {"title": "Fixture", "revid": 9, "wikitext": {"*": "# [[Example]]"}}}
    monkeypatch.setattr(importer.requests, "get", lambda *args, **kwargs: Response())
    api = importer.PublicAPI(tmp_path)
    assert api.get("https://example.test/api", {"action": "parse"})["parse"]["revid"] == 9
    def offline(*args, **kwargs): raise ConnectionError("offline")
    monkeypatch.setattr(importer.requests, "get", offline)
    assert api.get("https://example.test/api", {"action": "parse"})["parse"]["title"] == "Fixture"


def test_mixed_pages_use_specific_subject_headings():
    page = "Wikipedia:Vital articles/Level 5/Society and social sciences/Politics and economics"
    assert importer.domain_for(page, {1: "Politics and economics", 2: "Politics and government", 3: "Political ideologies"}) == "Politics & law"
    assert importer.domain_for(page, {1: "Politics and economics", 2: "Law", 3: "Criminal law"}) == "Politics & law"
    assert importer.domain_for(page, {1: "Politics and economics", 2: "Business and economics", 3: "Banking"}) == "Economics & organizations"
    page = "Wikipedia:Vital articles/Level 5/Technology/Agriculture"
    assert importer.domain_for(page, {1: "Agriculture, biotechnology and medical technology", 2: "Medical technology", 3: "Imaging"}) == "Health & medicine"
    assert importer.domain_for(page, {1: "Agriculture, biotechnology and medical technology", 2: "Agriculture", 3: "Horticulture"}) == "Food & agriculture"


def test_corrupt_or_incomplete_source_cache_is_refetched(tmp_path, monkeypatch):
    import hashlib
    import json
    endpoint = "https://example.test/api"
    params = {"action": "query", "titles": "Gardening"}
    path = tmp_path / (hashlib.sha256(json.dumps([endpoint, params], sort_keys=True).encode()).hexdigest() + ".json")
    class Response:
        status_code = 200
        def raise_for_status(self): pass
        def json(self): return {"query": {"pages": {"1": {"pageid": 1, "ns": 0, "title": "Gardening", "pageprops": {"wikibase_item": "Q11029"}}}}}
    monkeypatch.setattr(importer.requests, "get", lambda *args, **kwargs: Response())
    for contents in ['{"query":', '{"query":{"pages":{}}}']:
        path.write_text(contents)
        assert importer.PublicAPI(tmp_path).get(endpoint, params)["query"]["pages"]["1"]["title"] == "Gardening"


def test_partial_entity_and_page_records_are_rejected_but_explicit_missing_is_valid():
    import pytest
    for row in [None, {}, {"id": "Q1", "lastrevid": 2, "labels": {}, "descriptions": {"en": {"value": None}}, "claims": {}},
                {"id": "Q1", "lastrevid": 2, "labels": {}, "descriptions": {"en": None}, "claims": {}}]:
        with pytest.raises((ValueError, TypeError, KeyError)):
            importer.PublicAPI.validate({"entities": {"Q1": row}}, {"action": "wbgetentities", "ids": "Q1"})
    importer.PublicAPI.validate({"entities": {"Q1": {"id": "Q1", "missing": ""}}}, {"action": "wbgetentities", "ids": "Q1"})
    with pytest.raises((ValueError, TypeError, KeyError)):
        importer.PublicAPI.validate({"query": {"pages": {"1": {"pageid": 1, "title": "Gardening", "pageprops": None}}}}, {"action": "query", "titles": "Gardening"})


def test_company_source_sections_are_excluded_even_when_entity_type_is_a_subclass():
    row = {"article": "Example Corporation", "qid": "Q1", "domain": "Economics & organizations",
           "subsection": "Politics and economics / Companies / Chemical companies", "list_page": "List", "list_revision": 1}
    rows, counts = importer.merge_catalog([], [row], {"Q1": entity("Q1", "American public chemical company", "Q891723")})
    assert rows == []
    assert counts["excluded_source_section"] == 1


def test_travel_performing_arts_and_relationships_follow_actual_list_sections():
    page = 'Wikipedia:Vital articles/Level 5/Everyday life/Sports, games and recreation'
    for section in ['Tourism', 'Outdoor recreation']:
        assert importer.domain_for(page, {1: 'Sports, games and recreation', 2: 'Entertainment', 3: 'Recreation and tourism', 4: section}) == 'Geography & travel'
    assert importer.domain_for(page, {1: 'Sports, games and recreation', 2: 'Sports', 3: 'Football'}) == 'Games & sports'
    for section in ['Family and kinship', 'Sexuality and gender']:
        assert importer.domain_for('Wikipedia:Vital articles/Level 5/Everyday life', {1: 'Everyday life', 2: section}) == 'Society & relationships'
    assert importer.domain_for('Wikipedia:Vital articles/Level 5/Arts/Narrative arts', {1: 'Narrative arts', 2: 'Theatre', 3: 'Comedy'}) == 'Music & performance'
    assert importer.domain_for('Wikipedia:Vital articles/Level 5/Arts/Audiovisual arts', {1: 'Audiovisual arts', 2: 'Performing arts', 3: 'Forms'}) == 'Music & performance'
    assert importer.domain_for('Wikipedia:Vital articles/Level 5/Arts/Narrative arts', {1: 'Narrative arts', 2: 'Fictional and legendary characters', 3: 'Western folklore'}) == 'Literature & storytelling'
    assert importer.domain_for('Wikipedia:Vital articles/Level 5/Arts/Narrative arts', {1: 'Narrative arts', 2: 'Film and television', 3: 'Film genres'}) == 'Visual arts & design'


def test_imported_titles_can_be_saved_under_the_extension_phrase_contract():
    titles = ['Folha de S.Paulo', 'x' * 81, 'Example\tTitle', 'C++', 'Interaction design']
    candidates = [dict(article=title, qid=f'Q{i}', domain='Computing & information',
                       subsection='Computing', list_page='List', list_revision=1)
                  for i, title in enumerate(titles)]
    entities = {r['qid']: entity(r['qid'], 'Useful public topic description') for r in candidates}
    rows, counts = importer.merge_catalog([], candidates, entities)
    assert [r['topic'] for r in rows] == ['C++', 'Interaction design']
    assert counts['invalid_title'] == 3
