"""Importer behavior against small source-shaped fixtures; no live HTTP required."""
import pytest

from scripts.import_discovery_graph import build_graph, resolve_pages


def balance_fixture():
    graph=dict(version=1,metadata={'max_category_depth':1},areas=[],nodes=[],edges=[])
    for area,domain,count in [('a','Large',20),('b','Large',8),('c','Small',12)]:
        graph['areas'].append(dict(id=area,topic=area,description=area,domain=domain,category_id='cat:'+area))
        graph['nodes'].append(dict(id='cat:'+area,topic=area,description=area,kind='category'))
        for i in range(count):
            qid=area+str(i)
            graph['nodes'].append(dict(id=qid,topic=qid,description='specific concept',kind='concept',level=None))
            graph['edges'].append(dict(source='cat:'+area,target=qid,relation='contains_concept'))
    return graph


def test_domain_budget_is_equal_despite_different_pool_sizes_and_area_counts():
    from scripts.import_discovery_graph import balance_graph
    from graph_explorer import graph_candidates
    raw=balance_fixture()
    result=balance_graph(raw,concepts_per_domain=8)
    assert len(graph_candidates(result,['a','b']))==len(graph_candidates(result,['c']))==8
    assert len(graph_candidates(result,['a']))==len(graph_candidates(result,['b']))==4
    assert result==balance_graph(raw,concepts_per_domain=8)
    assert len(raw['nodes'])==43  # The input snapshot is not mutated.
    source_pairs={(e['source'],e['target']) for e in raw['edges']}
    assert all((e['source'],e['target']) in source_pairs for e in result['edges'])


def test_sparse_domain_reports_shortfall_instead_of_inventing_concepts():
    from scripts.import_discovery_graph import balance_graph
    result=balance_graph(balance_fixture(),concepts_per_domain=16)
    assert result['metadata']['balance']['shortfalls']=={'Small':4}
    assert result['metadata']['balance']['reviewed_shortfalls']['Small']=={'1':2,'2':2,'3':2}


def test_cross_domain_paths_cannot_leak_past_a_selected_domain_pool():
    from scripts.import_discovery_graph import balance_graph
    from graph_explorer import graph_candidates
    raw=balance_fixture()
    raw['edges'].append(dict(source='cat:c',target='cat:a',relation='contains_category'))
    result=balance_graph(raw,concepts_per_domain=8)
    assert len(graph_candidates(result,['c']))==8
    assert len(graph_candidates(result,['a','b']))==8


def test_reviewed_examples_are_spread_across_levels_before_filling_the_domain():
    from scripts.import_discovery_graph import balance_graph
    from graph_explorer import graph_candidates
    raw=balance_fixture()
    for row in raw['nodes']:
        if row['kind']=='concept':
            i=int(row['id'][1:])
            if i<6:row.update(level=1+i//2,hook='A reviewed entry point')
    result=balance_graph(raw,concepts_per_domain=8)
    for ids in [['a','b'],['c']]:
        counts={level:sum(r.get('level')==level for r in graph_candidates(result,ids)) for level in [1,2,3]}
        assert counts=={1:2,2:2,3:2}


def test_uniform_top_up_policy_only_deepens_domains_with_too_few_concepts():
    from scripts.import_discovery_graph import build_balanced_graph
    seeds=[dict(id=d,topic=d,description=d,domain=d,category='Category:'+d) for d in ['Rich','Sparse']]
    categories={'Category:Rich':[article('R1'),article('R2')],
                'Category:Sparse':[category('Branch')], 'Category:Branch':[category('Deeper')],
                'Category:Deeper':[article('S1'),article('S2')]}
    names=['R1','R2','S1','S2']
    result=build_balanced_graph(seeds,
        lambda title:dict(members=categories[title],source_url='https://example.org',truncated=False),
        lambda titles:{t:dict(title=t,wikidata_id=t) for t in titles},
        lambda ids:{i:entity(i) for i in ids},concepts_per_domain=2,max_categories=20)
    assert result['metadata']['balance']['shortfalls']=={}
    assert result['metadata']['balance']['traversal_depth_by_domain']=={'Rich':1,'Sparse':2}


def category(title):
    return {"title": "Category:" + title, "ns": 14, "pageid": 100}


def article(title):
    return {"title": title, "ns": 0, "pageid": 200}


def entity(qid, description="a concrete idea to explore", instance=None):
    claims = [] if instance is None else [{"mainsnak": {"datavalue": {"value": {"id": instance}}}}]
    return {"id": qid, "descriptions": {"en": {"value": description}},
            "claims": {"P31": claims}, "lastrevid": 42}


def import_fixture(categories, pages, entities, seed_options=None, **kwargs):
    seeds = [{"id": "cs", "topic": "Computer science", "description": "Computing and ideas",
              "domain": "Computing", "category": "Category:Computing"}]
    seeds[0].update(seed_options or {})

    def load_category(title):
        value = categories[title]
        if isinstance(value, Exception):
            raise value
        return {"members": value, "source_url": "https://en.wikipedia.org/wiki/" + title,
                "fetched_at": "2026-10-03T00:00:00Z", "truncated": False}

    return build_graph(seeds, load_category,
                       lambda titles: {title: pages[title] for title in titles if title in pages},
                       lambda qids: {qid: entities[qid] for qid in qids if qid in entities},
                       **kwargs)


def test_cycles_terminate_and_shared_entities_retain_both_real_paths():
    # Removing the visited guard hangs; deduping edges by target loses the second path.
    graph = import_fixture({
        "Category:Computing": [category("Theory"), article("Puzzle")],
        "Category:Theory": [category("Computing"), article("Puzzle redirect")],
    }, {"Puzzle": {"title": "Puzzle", "wikidata_id": "Q1", "pageid": 1},
        "Puzzle redirect": {"title": "Puzzle", "wikidata_id": "Q1", "pageid": 1}},
        {"Q1": entity("Q1")}, max_depth=2)
    assert [n["id"] for n in graph["nodes"] if n["kind"] == "concept"] == ["Q1"]
    paths = {(e["source"], e["target"]) for e in graph["edges"]}
    assert ("category:Category:Computing", "Q1") in paths
    assert ("category:Category:Theory", "Q1") in paths
    assert ("category:Category:Theory", "category:Category:Computing") in paths
    assert next(e for e in graph["edges"] if e["source"].endswith("Theory") and e["target"] == "Q1")["membership_title"] == "Puzzle redirect"


def test_filters_people_lists_disambiguation_maintenance_and_broad_area_articles():
    titles = ["Computer science", "List of puzzles", "Person", "Ambiguous", "No description", "Puzzle"]
    pages = {title: {"title": title, "wikidata_id": f"Q{i}", "pageid": i} for i, title in enumerate(titles, 1)}
    entities = {f"Q{i}": entity(f"Q{i}") for i in range(1, 7)}
    entities["Q3"] = entity("Q3", instance="Q5")
    entities["Q4"] = entity("Q4", instance="Q4167410")
    entities["Q5"] = entity("Q5", description="")
    graph = import_fixture({"Category:Computing": [*[article(t) for t in titles],
                          category("Wikipedia maintenance"), category("Computer scientists")]}, pages, entities)
    assert [n["topic"] for n in graph["nodes"] if n["kind"] == "concept"] == ["Puzzle"]
    assert len([n for n in graph["nodes"] if n["kind"] == "category"]) == 1
    assert graph["metadata"]["filtering_counts"]["missing_description"] == 1


def test_limits_are_respected_without_alphabetical_prefix_bias():
    # Sorting then slicing would select A/B/C; stable digest sampling must span the pool.
    names = [f"Idea {letter}" for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"]
    pages = {t: {"title": t, "wikidata_id": f"Q{i}", "pageid": i} for i, t in enumerate(names, 1)}
    entities = {f"Q{i}": entity(f"Q{i}") for i in range(1, 27)}
    graph = import_fixture({"Category:Computing": [*[article(t) for t in names], category("Theory")]},
                           pages, entities, max_depth=0, concepts_per_category=3)
    selected = [n["topic"] for n in graph["nodes"] if n["kind"] == "concept"]
    assert len(selected) == 3
    assert set(selected) != set(names[:3])
    assert all(e["relation"] == "contains_concept" for e in graph["edges"])


def test_preferred_topics_are_only_included_after_verified_membership_and_levels_are_explicit():
    graph = import_fixture({"Category:Computing": [article("P versus NP problem"), article("Other") ]},
        {"P versus NP problem": {"title": "P versus NP problem", "wikidata_id": "Q215206", "pageid": 1},
         "Other": {"title": "Other", "wikidata_id": "Q2", "pageid": 2}},
        {"Q215206": entity("Q215206"), "Q2": entity("Q2")},
        annotations={"P versus NP problem": {"hook": "Can easy-to-check answers always be found quickly?", "level": 1},
                     "Unobserved topic": {"hook": "Not a real membership", "level": 2}})
    concepts = {n["topic"]: n for n in graph["nodes"] if n["kind"] == "concept"}
    assert concepts["P versus NP problem"]["level"] == 1
    assert concepts["P versus NP problem"]["annotation_source"] == "ProductSpace editorial review"
    assert concepts["Other"]["level"] is None
    assert "Unobserved topic" not in concepts


def test_failed_category_is_reported_without_losing_successful_categories():
    graph = import_fixture({"Category:Computing": [category("Broken"), article("Puzzle")],
                            "Category:Broken": RuntimeError("Source unavailable")},
                           {"Puzzle": {"title": "Puzzle", "wikidata_id": "Q1", "pageid": 1}},
                           {"Q1": entity("Q1")})
    assert any(n["id"] == "Q1" for n in graph["nodes"])
    assert graph["metadata"]["complete"] is False
    assert graph["metadata"]["fetch_failures"][0]["category"] == "Category:Broken"


def test_global_and_per_parent_category_budgets_bound_traversal():
    # Ignoring either budget would reach all six children and exceed the graph budget.
    categories = {"Category:Computing": [category(f"Branch {i}") for i in range(6)]}
    categories.update({f"Category:Branch {i}": [] for i in range(6)})
    graph = import_fixture(categories, {}, {}, children_per_category=4, max_categories=3)
    assert len(graph["nodes"]) == 3
    assert len(graph["edges"]) == 2
    reasons = {row["reason"] for row in graph["metadata"]["selection_limits"]}
    assert reasons == {"child_category_cap", "global_category_cap"}


def test_broad_article_redirects_are_excluded_after_resolution():
    # Filtering only the original redirect title would leak the broad area as a concept.
    graph = import_fixture({"Category:Computing": [article("CS") ]},
        {"CS": {"title": "Computer science", "wikidata_id": "Q21198", "pageid": 1}},
        {"Q21198": entity("Q21198")})
    assert not any(node["kind"] == "concept" for node in graph["nodes"])


def test_category_overview_in_another_parent_is_navigation_not_a_final_concept():
    # Per-parent title filtering alone misses an overview that also belongs to its parent's category.
    graph = import_fixture({"Category:Computing": [category("Theory"), article("Theory")],
                            "Category:Theory": []},
                           {"Theory": {"title": "Theory", "wikidata_id": "Q1", "pageid": 1}},
                           {"Q1": entity("Q1")})
    assert not any(node["kind"] == "concept" for node in graph["nodes"])


def test_source_page_normalization_redirects_and_disambiguation_are_preserved():
    # Dropping either alias hop loses the entity for an underscored redirect input.
    query = {"normalized": [{"from": "old_name", "to": "Old name"}],
             "redirects": [{"from": "Old name", "to": "New name"}],
             "pages": [{"title": "New name", "pageid": 7, "ns": 0,
                        "pageprops": {"wikibase_item": "Q7", "disambiguation": ""}},
                       {"title": "Missing", "ns": 0, "missing": True}]}
    pages = resolve_pages(query, ["old_name", "Missing"])
    assert pages["old_name"]["title"] == "New name"
    assert pages["old_name"]["wikidata_id"] == "Q7"
    assert pages["old_name"]["disambiguation"] is True
    assert pages["Missing"]["missing"] is True


def test_per_seed_depth_and_verified_child_preferences_reach_a_specific_problem():
    graph = import_fixture({"Category:Computing": [category("Theory")],
        "Category:Theory": [category("Complexity"), category("Other")],
        "Category:Complexity": [article("Problem") ]},
        {"Problem": {"title": "Problem", "wikidata_id": "Q1", "pageid": 1}},
        {"Q1": entity("Q1")}, children_per_category=1,
        seed_options={"max_depth": 2, "category_preferences": {"Category:Theory": ["Category:Complexity"]}})
    assert any(n["id"] == "Q1" for n in graph["nodes"])
    assert {e["target"] for e in graph["edges"]} == {"category:Category:Theory", "category:Category:Complexity", "Q1"}


@pytest.mark.parametrize("limits", [{"max_depth": -1}, {"concepts_per_category": 0}, {"children_per_category": 0}, {"max_categories": 0}])
def test_invalid_limits_do_not_silently_produce_empty_graphs(limits):
    with pytest.raises(ValueError):
        import_fixture({}, {}, {}, **limits)
