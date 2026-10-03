"""Catalog regressions: subject balance is measured on actual runtime candidates."""
import json
from collections import Counter
from pathlib import Path

from explorer import load_catalog
from graph_explorer import load_graph, graph_candidates

ROOT=Path(__file__).resolve().parents[1]


def test_snapshot_covers_all_original_domains_with_equal_runtime_budgets():
    graph=load_graph()
    expected={r['domain'] for r in load_catalog()}
    assert {a['domain'] for a in graph['areas']}==expected
    assert Counter(a['domain'] for a in graph['areas'])==dict.fromkeys(expected,3)
    for domain in expected:
        rows=graph_candidates(graph,[a['id'] for a in graph['areas'] if a['domain']==domain])
        assert len(rows)==160,domain
        assert Counter(r['level'] for r in rows if r.get('level') is not None)=={1:2,2:2,3:2},domain
    assert not graph['metadata']['balance']['shortfalls']


def test_seeds_have_no_subject_specific_depth_exceptions():
    seeds=json.loads((ROOT/'data/discovery_seeds.json').read_text())
    assert all('max_depth' not in a for a in seeds['areas'])
