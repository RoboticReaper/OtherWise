"""Sourced graph retrieval and inspectable personal ranking for the second stage."""
from __future__ import annotations

import json
import math
from collections import defaultdict, deque
from pathlib import Path

import numpy as np

from explorer import EPSILON, _key, _unit_vectors, score_catalog, _classification_distances
from feedback import area_preferences, new_profile

GRAPH_PATH = Path(__file__).resolve().parent / 'data' / 'discovery_graph.json'


def load_graph(path=GRAPH_PATH):
    graph = json.loads(Path(path).read_text())
    if not isinstance(graph, dict) or graph.get('version') != 1:
        raise ValueError('Unsupported discovery graph version.')
    nodes = graph.get('nodes', [])
    index = {n['id']: n for n in nodes}
    if not nodes or len(index) != len(nodes):
        raise ValueError('Graph nodes must have unique IDs.')
    for node in nodes:
        if node.get('kind') not in ('category', 'concept') or not all(isinstance(node.get(k), str) and node[k].strip() for k in ('id', 'topic', 'description')):
            raise ValueError('Every graph node needs an ID, kind, title and description.')
        if node.get('level') is not None and (type(node['level']) is not int or node['level'] not in (1, 2, 3)):
            raise ValueError('Reviewed levels must be 1, 2, 3, or None.')
    areas = graph.get('areas', [])
    if not areas or len({a['id'] for a in areas}) != len(areas):
        raise ValueError('Graph areas must be nonempty and unique.')
    for area in areas:
        if area['category_id'] not in index or index[area['category_id']]['kind'] != 'category':
            raise ValueError('Each graph area must refer to a category.')
        if 'concept_ids' in area and (not isinstance(area['concept_ids'],list) or
                any(i not in index or index[i]['kind']!='concept' for i in area['concept_ids'])):
            raise ValueError('Area selections must refer to existing concepts.')
    for edge in graph.get('edges', []):
        if edge['source'] not in index or edge['target'] not in index:
            raise ValueError('Graph edges must refer to existing nodes.')
        expected = {'contains_category': 'category', 'contains_concept': 'concept'}.get(edge.get('relation'))
        if index[edge['source']]['kind'] != 'category' or index[edge['target']]['kind'] != expected:
            raise ValueError('Graph edges must retain their category membership meaning.')
    return graph


def graph_concepts(graph):
    """Stable embedding order. Only this ordered list should be passed to the encoder."""
    return [n for n in graph['nodes'] if n['kind'] == 'concept']


def graph_candidates(graph, area_ids=None, max_depth=3):
    if type(max_depth) is not int or not 1 <= max_depth <= 8:
        raise ValueError('Graph traversal depth must be between 1 and 8.')
    areas = {a['id']: a for a in graph['areas']}
    area_ids = list(areas) if area_ids is None else list(dict.fromkeys(area_ids))
    if any(a not in areas for a in area_ids):
        raise ValueError('Unknown graph area.')
    nodes = {n['id']: n for n in graph['nodes']}
    children = defaultdict(list)
    for edge in graph['edges']:
        if edge['relation'] in ('contains_category', 'contains_concept'):
            children[edge['source']].append(edge['target'])
    result = {}
    for area_id in area_ids:
        root = areas[area_id]['category_id']
        allowed = set(areas[area_id]['concept_ids']) if 'concept_ids' in areas[area_id] else None
        queue, visited = deque([(root, [root])]), {root}
        while queue:
            parent, path = queue.popleft()
            if len(path) - 1 >= max_depth:
                continue
            for child in sorted(set(children[parent])):
                if child in visited:
                    continue
                visited.add(child)
                child_path = path + [child]
                if nodes[child]['kind'] == 'concept':
                    if allowed is not None and child not in allowed:
                        continue
                    row = result.setdefault(child, dict(nodes[child], area_ids=[], paths={}))
                    row['area_ids'].append(area_id)
                    row['paths'][area_id] = child_path
                else:
                    queue.append((child, child_path))
    return list(result.values())


def select_areas(areas, area_vectors, query_vectors, limit=8):
    """Route broad recommendations/interest anchors into the most related graph areas."""
    if type(limit) is not int or limit < 1:
        raise ValueError('Area limit must be a positive integer.')
    vectors, queries = _unit_vectors(area_vectors, 'Area vectors'), _unit_vectors(query_vectors, 'Query vectors')
    if len(areas) != len(vectors) or vectors.shape[1] != queries.shape[1]:
        raise ValueError('Area and query embeddings must have matching shapes.')
    similarities = vectors @ queries.T
    # Round robin queries before filling by best score prevents one query taking all slots.
    chosen = []
    order = np.argsort(-similarities, axis=0, kind='stable')
    for rank in range(len(areas)):
        for q in range(len(queries)):
            i = int(order[rank, q])
            if i not in chosen:
                chosen.append(i)
            if len(chosen) >= min(limit, len(areas)):
                return [areas[i]['id'] for i in chosen]
    return [areas[i]['id'] for i in chosen]


def recommend_specific(graph, concept_vectors, interests, interest_vectors, *, area_ids=None,
                       profile=None, radius=.28, expansion=.07, overlap=.015, top_k=10,
                       diversity=.20, randomness=.03, seed=None, exploration_fraction=.30,
                       max_overlap_fraction=.2, classification_distances=None, include_unlinked=False):
    """Follow graph paths, then enforce actual concept distances before personal ranking.

    Reserve up to ceil(exploration_fraction * result count) selections from the
    least-exposed eligible areas. Report any shortfall rather than violating the
    angular band, known exclusions, or the familiar-overlap cap. Reviewed levels
    are editorial presentation estimates; missing levels never imply competence.
    """
    for name, value in dict(radius=radius, expansion=expansion, overlap=overlap, diversity=diversity,
                            randomness=randomness, exploration_fraction=exploration_fraction,
                            max_overlap_fraction=max_overlap_fraction).items():
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1:
            raise ValueError(f'{name} must be a finite number between 0 and 1.')
    if max_overlap_fraction >= 1 or type(top_k) is not int or top_k < 1:
        raise ValueError('Require a positive result count and an overlap fraction below 1.')
    if seed is not None and (type(seed) is not int or seed < 0):
        raise ValueError('Seed must be a nonnegative integer or None.')
    profile = new_profile() if profile is None else profile
    concepts = graph_concepts(graph)
    if not concepts:
        return []
    scores = score_catalog(concepts, concept_vectors, interests, interest_vectors)
    classifications = _classification_distances(classification_distances,[r['distance'] for r in scores])
    units = _unit_vectors(concept_vectors, 'Concept vectors')
    reached = {r['id']: r for r in graph_candidates(graph, area_ids)}
    titles = {_key(s) for s in interests}
    lower, upper = max(0, radius - overlap), min(1, radius + expansion)
    pool = []
    for row in scores:
        rating = profile['items'].get(row['id'], {})
        if (row['id'] not in reached and not include_unlinked) or rating.get('known') or _key(row['topic']) in titles:
            continue
        if not lower - EPSILON <= row['distance'] <= upper + EPSILON or row['distance'] <= .035:
            continue
        provenance = reached.get(row['id'],dict(area_ids=[],paths={}))
        pool.append(dict(row, area_ids=provenance['area_ids'], paths=provenance['paths'],
                         zone='New territory' if classifications[row['catalog_index']] >= radius - EPSILON else 'Familiar overlap',
                         boundary_offset=row['distance'] - radius))
    if not pool:
        return []
    counts = {zone: sum(r['zone'] == zone for r in pool) for zone in ('New territory', 'Familiar overlap')}
    fam = min(counts['Familiar overlap'], math.floor(top_k * max_overlap_fraction + EPSILON),
              math.floor(counts['New territory'] * max_overlap_fraction / (1 - max_overlap_fraction) + EPSILON))
    remaining = {'New territory': min(counts['New territory'], top_k - fam), 'Familiar overlap': fam}
    result_count = sum(remaining.values())
    reserve_target = math.ceil(exploration_fraction * result_count)
    exposures, prefs = profile['exposures'], area_preferences(profile)
    eligible_areas = {a for row in pool for a in row['area_ids']}
    least_seen = min((exposures.get(a, 0) for a in eligible_areas),default=0)
    underexplored = {a for a in eligible_areas if exposures.get(a, 0) == least_seen}
    rng = np.random.default_rng(seed)
    # Draw in stable catalog order so feedback exclusions do not reshuffle noise.
    jitter = {r['id']: float(rng.uniform(-randomness, randomness)) if randomness else 0. for r in concepts}
    areas = {a['id']: a for a in graph['areas']}
    nodes = {n['id']: n for n in graph['nodes']}
    selected, area_counts = [], defaultdict(int)
    target, scale = (radius + upper) / 2, max((upper - radius) / 2, .025)
    reserved = 0
    while any(remaining.values()):
        available = [r for r in pool if remaining[r['zone']] > 0]
        reserve_pool = [r for r in available if set(r['area_ids']) & underexplored]
        reserve = reserved < reserve_target and bool(reserve_pool)
        if reserve:
            available = reserve_pool

        def evaluate(row):
            options = [a for a in row['area_ids'] if not reserve or a in underexplored]
            area = min(options, key=lambda a: (area_counts[a], exposures.get(a, 0), row['area_ids'].index(a))) if options else None
            preference = prefs.get(area, {'curiosity': 0, 'level': None})
            rating = profile['items'].get(row['id'], {})
            fit = 1 - min(abs(row['distance'] - target) / scale, 1)
            curiosity = .30 * bool(rating.get('curious')) + .18 * preference['curiosity']
            level, desired = row.get('level'), preference['level']
            difficulty = .25 * (1 - abs(level - desired)) if level is not None and desired is not None else 0.
            presentation = -.35 if rating.get('difficulty', 'none') != 'none' else 0.
            redundancy = max(0., max((float(units[row['catalog_index']] @ units[s['catalog_index']]) for s in selected), default=0.))
            parts = dict(band_fit=(1-diversity)*fit, curiosity=curiosity, difficulty=difficulty,
                         presentation=presentation, diversity=-diversity*redundancy,
                         area_variety=-.12*area_counts[area] if area is not None else 0., randomness=jitter[row['id']])
            return sum(parts.values()), area, parts, desired

        evaluated = [(row, evaluate(row)) for row in available]
        best, (score, area, parts, desired) = max(evaluated, key=lambda item: (round(item[1][0], 12), -item[0]['catalog_index']))
        path = best['paths'].get(area,[])
        selected.append(dict(best, area_id=area, area=areas[area]['topic'] if area else None,
                             domain=areas[area]['domain'] if area else best.get('domain'),
                             graph_path=[nodes[i]['topic'] for i in path], path_ids=path,
                             preferred_level=desired, score=score, score_parts=parts,
                             exploration_pick=reserve, exploration_target=reserve_target))
        reserved += int(reserve)
        area_counts[area] += 1
        remaining[best['zone']] -= 1
        pool.remove(best)
    for row in selected:
        row['exploration_achieved'] = reserved
    return selected
