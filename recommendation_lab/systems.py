"""One experimental recommendation boundary, with frozen executable controls."""
from __future__ import annotations

import math
import re
import sqlite3
import time
import queue
import threading
from dataclasses import asdict, dataclass, field

import numpy as np

from explorer import EPSILON, _key, _unit_vectors, interest_texts, recommend as broad_recommend
from feedback import new_profile, set_feedback, area_preferences
from graph_explorer import graph_candidates, graph_concepts, recommend_specific, select_areas
from .inventory import digest

VARIANTS = ('V0', 'V1', 'V2', 'V3', 'V3-no-lexical', 'V3-no-graph', 'V3-no-ranking', 'V3-adaptive', 'V4b')
GOALS = ('connection', 'discovery', 'depth', 'variety')


@dataclass
class Request:
    interests: list
    inventory_version: str | None = None
    result_kind: str = 'specific'
    mode: str = 'global'
    focus_index: int | None = None
    goal: str = 'discovery'
    limit: int = 10
    radius: float = .28
    expansion: float = .07
    overlap: float = .015
    diversity: float = .20
    max_overlap_fraction: float = .20
    randomness: float = 0.
    exploration_fraction: float = .30
    expansion_level: int = 0
    feedback: dict = field(default_factory=dict)
    exposures: dict = field(default_factory=dict)
    seed: int = 42

    def validate(self):
        if not isinstance(self.interests,list) or not 1 <= len(self.interests) <= 40:
            raise ValueError('Provide 1–40 interests.')
        if self.result_kind not in ('broad', 'specific') or self.goal not in GOALS or self.mode not in ('global', 'path'):
            raise ValueError('Invalid kind, goal, or mode.')
        if type(self.limit) is not int or not 1 <= self.limit <= 100 or type(self.seed) is not int or not 0 <= self.seed <= 2**32-1:
            raise ValueError('Invalid result limit or seed.')
        if type(self.expansion_level) is not int or not 0 <= self.expansion_level <= 8:
            raise ValueError('Invalid expansion level.')
        if self.mode == 'path':
            if type(self.focus_index) is not int or not 0 <= self.focus_index < len(self.interests):
                raise ValueError('Path mode requires an interest focus index.')
        elif self.focus_index is not None:
            raise ValueError('Global mode has no focus index.')
        for name in ('radius', 'expansion', 'overlap', 'diversity', 'max_overlap_fraction', 'randomness', 'exploration_fraction'):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1:
                raise ValueError(f'Invalid {name}.')
        if self.max_overlap_fraction >= 1:
            raise ValueError('Overlap share must be below one.')


@dataclass(frozen=True)
class RankConfig:
    pool_limit: int = 256
    rrf_k: int = 60
    relevance: float | None = None
    band: float | None = None
    novelty: float | None = None
    diversity: float | None = None

    def validate(self):
        if type(self.pool_limit) is not int or not 1 <= self.pool_limit <= 10000 or type(self.rrf_k) is not int or not 1 <= self.rrf_k <= 1000:
            raise ValueError('Invalid retrieval bounds.')
        for value in (self.relevance, self.band, self.novelty, self.diversity):
            if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1):
                raise ValueError('Ranking weights must be finite in [0,1].')


class LexicalIndex:
    def __init__(self, inventory, broad, concepts):
        self.connection = sqlite3.connect(':memory:')
        self.connection.execute('CREATE VIRTUAL TABLE candidates USING fts5(kind UNINDEXED, idx UNINDEXED, label, aliases, description)')
        for kind, rows in [('broad', broad), ('specific', concepts)]:
            for i, row in enumerate(rows):
                cid = inventory.source_ids[kind][i]
                self.connection.execute('INSERT INTO candidates VALUES (?,?,?,?,?)',
                    (kind, i, row['topic'], ' '.join(sorted(inventory.concepts[cid]['aliases'])), row['description']))
        self.connection.commit()

    def search(self, kind, text):
        # Quoted, bounded tokens make MATCH metacharacters and user SQL inert.
        tokens = list(dict.fromkeys(re.findall(r'\w+', text.casefold())))[:100]
        if not tokens:
            return []
        query = ' OR '.join('"' + token + '"' for token in tokens)
        return [int(r[0]) for r in self.connection.execute(
            'SELECT idx FROM candidates WHERE candidates MATCH ? AND kind = ? ORDER BY bm25(candidates,0,0,3,2,1), CAST(idx AS INTEGER)',
            (query, kind))]


class RecommendationLab:
    def __init__(self, inventory, broad, graph, model, broad_vectors, concept_vectors, area_vectors, *, model_identity):
        self.inventory, self.broad, self.graph, self.model = inventory, broad, graph, model
        self.concepts = graph_concepts(graph)
        self.broad_vectors = _unit_vectors(broad_vectors, 'Broad vectors')
        self.concept_vectors = _unit_vectors(concept_vectors, 'Concept vectors')
        self.area_vectors = _unit_vectors(area_vectors, 'Area vectors')
        dimensions = self.broad_vectors.shape[1]
        if self.broad_vectors.shape != (len(broad), dimensions) or self.concept_vectors.shape != (len(self.concepts), dimensions) or self.area_vectors.shape != (len(graph['areas']), dimensions):
            raise ValueError('Vectors must match the frozen source records.')
        self.model_identity = model_identity
        self.reached = {r['id']: r for r in graph_candidates(graph)}
        self.areas = {r['id']: r for r in graph['areas']}
        self._encoded = {}  # Ephemeral request texts; never persisted by serving.
        self._rerank_slot = threading.BoundedSemaphore(1)
        try:
            self.lexical = LexicalIndex(inventory, broad, self.concepts)
        except sqlite3.OperationalError:
            self.lexical = None

    def _encode(self, texts):
        missing = list(dict.fromkeys(t for t in texts if t not in self._encoded))
        if missing:
            values = _unit_vectors(self.model.encode(missing, batch_size=32, show_progress_bar=False,
                                    convert_to_numpy=True, normalize_embeddings=True), 'Interest vectors')
            if len(values) != len(missing) or values.shape[1] != self.broad_vectors.shape[1]:
                raise ValueError('Interest vector shape differs from the model identity.')
            self._encoded.update(zip(missing, values))
        return np.asarray([self._encoded[t] for t in texts])

    def _profile(self, request):
        if not isinstance(request.feedback, dict) or not isinstance(request.exposures, dict):
            raise ValueError('Feedback and exposures must be mappings.')
        profile = new_profile()
        for cid, rating in request.feedback.items():
            if cid not in self.inventory.concepts or not isinstance(rating, dict) or set(rating) - {'curious', 'known', 'difficulty'}:
                raise ValueError('Invalid concept feedback.')
            source_ids = [r['source_id'] for r in self.inventory.concepts[cid]['records'] if r['kind'] == 'specific']
            graph_row = self.reached.get(source_ids[0], {}) if source_ids else {}
            set_feedback(profile, cid, curious=rating.get('curious', False), known=rating.get('known', False),
                         difficulty=rating.get('difficulty', 'none'), level=graph_row.get('level'), area_ids=graph_row.get('area_ids', []))
        if any(a not in self.areas or type(count) is not int or not 0 <= count <= 1_000_000_000 for a, count in request.exposures.items()):
            raise ValueError('Invalid area exposures.')
        profile['exposures'] = dict(request.exposures)
        return profile

    def _routing(self, phrases, seeds, request):
        indices = [request.focus_index] if request.mode == 'path' else list(range(len(phrases)))
        anchors = seeds[indices]
        proposals = broad_recommend(self.broad, self.broad_vectors, [phrases[i] for i in indices], anchors,
            radius=request.radius, expansion=min(1, request.expansion + .01*request.expansion_level), overlap=request.overlap,
            top_k=24, diversity=request.diversity, randomness=0)
        queries = np.vstack([anchors] + ([self.broad_vectors[[r['catalog_index'] for r in proposals]]] if proposals else []))
        return select_areas(self.graph['areas'], self.area_vectors, queries, limit=8)

    def _legacy(self, request, variant, seeds, phrases, profile):
        indices = [request.focus_index] if request.mode == 'path' else list(range(len(phrases)))
        anchors, anchor_phrases = seeds[indices], [phrases[i] for i in indices]
        opts = dict(radius=request.radius, expansion=min(1, request.expansion + .01*request.expansion_level),
                    overlap=request.overlap, top_k=request.limit, diversity=request.diversity,
                    max_overlap_fraction=request.max_overlap_fraction, randomness=request.randomness, seed=request.seed)
        if request.result_kind == 'broad':
            return broad_recommend(self.broad, self.broad_vectors, anchor_phrases, anchors, **opts)
        distances = np.arccos(np.clip(self.concept_vectors @ seeds.T, -1, 1))/np.pi
        for i, row in enumerate(self.concepts):
            if min(distances[i]) <= .035 or _key(row['topic']) in {_key(p) for p in phrases}:
                if row['id'] not in profile['items']:
                    set_feedback(profile, row['id'], known=True)
                else:
                    profile['items'][row['id']]['known'] = True
        return recommend_specific(self.graph, self.concept_vectors, anchor_phrases, anchors,
            area_ids=self._routing(phrases, seeds, request) if variant == 'V0' else None,
            profile=profile, exploration_fraction=request.exploration_fraction, **opts)

    def recommend(self, request, variant='V3', config=None, *, reranker=None, rerank_timeout=20.):
        start = time.perf_counter()
        request.validate()
        if variant not in VARIANTS:
            raise ValueError('Unknown recommendation variant.')
        config = config or RankConfig()
        config.validate()
        profile = self._profile(request)
        legacy = variant in ('V0', 'V1')
        validated = self.inventory.resolve(request.interests,inventory_version=request.inventory_version)
        if legacy:
            # Preserve old lookup, including its known meaning collisions, for a fair control.
            phrases = [r['phrase'] for r in validated]
            rows = self.broad if request.result_kind == 'broad' else self.broad + self.concepts
            resolutions = [dict(phrase=p, status='legacy_lookup', concept_id=None, text=t, choices=[])
                           for p, t in zip(phrases, interest_texts(phrases, rows))]
        else:
            resolutions = validated
            phrases = [r['phrase'] for r in resolutions]
        batch = dict(schema_version=2, status='ok', algorithm=variant, config=asdict(config),
                     algorithm_id=digest(dict(variant=variant, config=asdict(config), goal=request.goal, version=1)),
                     inventory_version=self.inventory.version, model_identity=self.model_identity,
                     resolutions=resolutions, recommendations=[], execution=dict(external_status='not_requested', serving_cost_usd=0.,
                     eligibility_policy='adaptive-experiment-v1' if variant == 'V3-adaptive' else 'requested-hard-band'), diagnostics={})
        if any(r['status'] == 'clarification_needed' for r in resolutions):
            batch['status'] = 'clarification_needed'
            batch['execution']['seconds'] = time.perf_counter()-start
            return batch
        seeds = self._encode([r['text'] for r in resolutions])
        rows = self.broad if request.result_kind == 'broad' else self.concepts
        units = self.broad_vectors if request.result_kind == 'broad' else self.concept_vectors
        distances = np.arccos(np.clip(units @ seeds.T, -1, 1))/np.pi
        nearest_indices = np.argmin(distances, axis=1)
        nearest = distances[np.arange(len(rows)), nearest_indices]
        anchored = nearest if request.mode == 'global' else distances[:, request.focus_index]
        lower, upper = max(0, request.radius-request.overlap), min(1, request.radius+request.expansion+.01*request.expansion_level)
        if variant == 'V3-adaptive':
            # Explicit experiment: broad anchors often have no specific neighbors inside
            # the old annulus. These bounds are declared, not fitted to held-out results.
            lower, upper = .08, .55
        resolved_ids = {r['concept_id'] for r in resolutions if r['concept_id']}
        explicit_known = {cid for cid, r in request.feedback.items() if r.get('known')}
        candidates, seen = [], set()
        for i, row in enumerate(rows):
            cid = self.inventory.source_ids[request.result_kind][i]
            known = cid in explicit_known or (cid in resolved_ids if not legacy else _key(row['topic']) in {_key(p) for p in phrases})
            eligible = not known and nearest[i] > .035 and lower-EPSILON <= anchored[i] <= upper+EPSILON
            if not legacy:
                eligible = eligible and nearest[i] >= lower-EPSILON and cid not in seen
            if request.result_kind == 'specific' and row['id'] not in self.reached and (legacy or variant == 'V2'):
                eligible = False
            if not eligible:
                continue
            seen.add(cid)
            candidates.append(dict(row, catalog_index=i, concept_id=cid, distance=float(anchored[i]),
                nearest_interest=phrases[int(nearest_indices[i])], anchor_distance=float(anchored[i]),
                nearest_interest_distance=float(nearest[i]), zone='New territory' if nearest[i] >= request.radius-EPSILON else 'Familiar overlap',
                boundary_offset=float(nearest[i]-request.radius)))
        eligible_ids = {r['concept_id'] for r in candidates}
        if legacy:
            selected = self._legacy(request, variant, seeds, phrases, profile)
            if variant == 'V0' and request.result_kind == 'specific':
                routed = {r['id'] for r in graph_candidates(self.graph, self._routing(phrases, seeds, request))}
                reached_ids = {self.inventory.source_ids['specific'][i] for i, row in enumerate(rows) if row['id'] in routed} & eligible_ids
            else:
                reached_ids = eligible_ids
        else:
            if variant != 'V2':
                candidates = self._fuse(candidates, request, variant, config, seeds, distances, phrases,
                                        [r['text'] for r in resolutions])
            reached_ids = {r['concept_id'] for r in candidates}
            if variant in ('V2', 'V3-no-ranking'):
                if request.result_kind == 'specific':
                    allowed = {r['id'] for r in candidates}
                    for row in rows:
                        if row['id'] not in allowed:
                            if row['id'] not in profile['items']:
                                set_feedback(profile, row['id'], known=True)
                            else:
                                profile['items'][row['id']]['known'] = True
                    indices = [request.focus_index] if request.mode == 'path' else list(range(len(phrases)))
                    selected = recommend_specific(self.graph, units, [phrases[i] for i in indices], seeds[indices],
                        profile=profile, radius=request.radius, expansion=upper-request.radius, overlap=request.overlap,
                        top_k=request.limit, diversity=request.diversity, randomness=request.randomness,
                        max_overlap_fraction=request.max_overlap_fraction, seed=request.seed, exploration_fraction=request.exploration_fraction,
                        classification_distances=nearest,include_unlinked=variant == 'V3-no-ranking')
                else:
                    indexes = [r['catalog_index'] for r in candidates]
                    selected = broad_recommend([rows[i] for i in indexes], units[indexes], phrases if request.mode == 'global' else [phrases[request.focus_index]],
                        seeds if request.mode == 'global' else seeds[[request.focus_index]], radius=request.radius,
                        expansion=upper-request.radius, overlap=request.overlap, top_k=request.limit, diversity=request.diversity,
                        randomness=request.randomness, max_overlap_fraction=request.max_overlap_fraction, seed=request.seed,
                        classification_distances=nearest[indexes]) if indexes else []
                    for row in selected:
                        row['catalog_index'] = indexes[row['catalog_index']]
            else:
                selected = self._rank(candidates, units, request, config, profile)
        output = []
        by_index = {r['catalog_index']: r for r in candidates}
        for row in selected:
            i = row['catalog_index']
            source = rows[i]
            cid = self.inventory.source_ids[request.result_kind][i]
            values = by_index.get(i, {})
            graph = None
            if request.result_kind == 'specific' and source['id'] in self.reached:
                reached = self.reached[source['id']]
                area = row.get('area_id', min(reached['area_ids']))
                path = reached['paths'][area]
                labels = {n['id']: n['topic'] for n in self.graph['nodes']}
                graph = dict(area_id=area, area=self.areas[area]['topic'], path_ids=path, path=[labels[n] for n in path], level=source.get('level'))
            output.append(dict(concept_id=cid, topic=source['topic'], description=source['description'],
                sources=self.inventory.concepts[cid]['records'], graph=graph,
                distance=float(row['distance']), anchor_distance=float(anchored[i]), nearest_interest_distance=float(nearest[i]),
                nearest_interest=phrases[int(nearest_indices[i])], zone=values.get('zone', row['zone']),
                score_parts=row.get('score_parts', {}), exploration_pick=row.get('exploration_pick', False)))
        if variant == 'V4b':
            if isinstance(rerank_timeout,bool) or not isinstance(rerank_timeout,(int,float)) or not math.isfinite(rerank_timeout) or not 0 < rerank_timeout <= 20:
                raise ValueError('Reranking deadline must be positive and no more than twenty seconds.')
            deadline = min(rerank_timeout,max(0,30-(time.perf_counter()-start)-.25))
            output, status = self._rerank(output, request, reranker,deadline)
            batch['execution']['external_status'] = status
        batch['recommendations'] = output
        batch['diagnostics'] = dict(eligible_count=len(eligible_ids), retrieved_count=len(reached_ids),
            eligible_recall=len(reached_ids)/len(eligible_ids) if eligible_ids else None,
            returned_count=len(output), duplicate_count=len(output)-len({r['concept_id'] for r in output}),
            overlap_count=sum(r['zone'] == 'Familiar overlap' for r in output),
            exploration_achieved=sum(r['exploration_pick'] for r in output))
        batch['execution']['seconds'] = time.perf_counter()-start
        return batch

    def _fuse(self, candidates, request, variant, config, seeds, distances, phrases, texts):
        if variant != 'V3-no-lexical' and self.lexical is None:
            raise RuntimeError('Lexical index unavailable for this variant.')
        eligible = {r['catalog_index']: r for r in candidates}
        channels = []
        indices = [request.focus_index] if request.mode == 'path' else list(range(len(seeds)))
        for j in indices:
            channels.append(sorted(eligible, key=lambda i: (distances[i,j], i)))
            if variant != 'V3-no-lexical':
                # Resolved meanings supply canonical context, not just an ambiguous surface word.
                text = texts[j]
                channels.append([i for i in self.lexical.search(request.result_kind, text) if i in eligible])
        if variant != 'V3-no-graph' and request.result_kind == 'specific':
            routed = {r['id'] for r in graph_candidates(self.graph, self._routing(phrases, seeds, request))}
            channels.append(sorted((i for i, r in eligible.items() if r['id'] in routed), key=lambda i: (min(distances[i]), i)))
        fused = dict.fromkeys(eligible, 0.)
        for channel in channels:
            for rank, i in enumerate(channel, 1):
                fused[i] += 1/(config.rrf_k+rank)
        maximum = max(fused.values(), default=1.) or 1.
        order = sorted(eligible, key=lambda i: (-fused[i], i))[:config.pool_limit]
        return [dict(eligible[i], retrieval=fused[i]/maximum) for i in order]

    def _rank(self, candidates, units, request, config, profile):
        new_count = sum(r['zone'] == 'New territory' for r in candidates)
        familiar_count = len(candidates)-new_count
        fam = min(familiar_count, math.floor(request.limit*request.max_overlap_fraction+EPSILON),
                  math.floor(new_count*request.max_overlap_fraction/(1-request.max_overlap_fraction)+EPSILON))
        remaining = {'New territory': min(new_count, request.limit-fam), 'Familiar overlap': fam}
        count = sum(remaining.values())
        target = request.radius + min(request.expansion+.01*request.expansion_level, 1-request.radius)/2
        scale = max((target-request.radius), .025)
        default = dict(connection=(.75,.20,.05), discovery=(.55,.25,.20), depth=(.70,.30,0.), variety=(.60,.20,.20))[request.goal]
        weights = [value if value is not None else default[i] for i,value in enumerate((config.relevance,config.band,config.novelty))]
        diversity = config.diversity if config.diversity is not None else (.45 if request.goal == 'variety' else request.diversity)
        prefs = area_preferences(profile)
        least_areas = set()
        for r in candidates:
            least_areas.update(self.reached.get(r.get('id'), {}).get('area_ids', []))
        minimum = min((request.exposures.get(a, 0) for a in least_areas), default=0)
        least_areas = {a for a in least_areas if request.exposures.get(a, 0) == minimum}
        reserve_target = math.ceil(request.exploration_fraction*count)
        rng = np.random.default_rng(request.seed)
        jitter = {r['concept_id']: float(rng.uniform(-request.randomness, request.randomness)) for r in sorted(candidates, key=lambda r:r['catalog_index'])}
        selected, area_counts, reserved = [], {}, 0
        pool = list(candidates)
        while any(remaining.values()):
            available = [r for r in pool if remaining[r['zone']] > 0]
            reserve = reserved < reserve_target and any(set(self.reached.get(r.get('id'), {}).get('area_ids', [])) & least_areas for r in available)
            if reserve:
                available = [r for r in available if set(self.reached.get(r.get('id'), {}).get('area_ids', [])) & least_areas]
            def evaluate(r):
                areas = self.reached.get(r.get('id'), {}).get('area_ids', [])
                allowed = [a for a in areas if a in least_areas] if reserve else areas
                area = min(allowed, key=lambda a:(area_counts.get(a,0),request.exposures.get(a,0),a)) if allowed else None
                rating = profile['items'].get(r['concept_id'], {})
                preference = prefs.get(area, {'curiosity':0,'level':None})
                level, desired = r.get('level'), preference['level']
                redundancy = max(0.,max((float(units[r['catalog_index']] @ units[s['catalog_index']]) for s in selected),default=0.))
                parts = dict(retrieval=weights[0]*r.get('retrieval', 0.),
                    band_fit=weights[1]*(1-min(abs(r['anchor_distance']-target)/scale,1)),
                    outward_distance=weights[2]*min(1,max(0,(r['nearest_interest_distance']-request.radius)/max(request.expansion,.025))),
                    curiosity=.30*bool(rating.get('curious'))+.18*preference['curiosity'],
                    difficulty=.25*(1-abs(level-desired)) if level is not None and desired is not None else 0.,
                    presentation=-.35 if rating.get('difficulty','none') != 'none' else 0.,
                    diversity=-diversity*redundancy, area_variety=-.12*area_counts.get(area,0) if area is not None else 0., randomness=jitter[r['concept_id']])
                return sum(parts.values()), area, parts
            evaluated = [(r,evaluate(r)) for r in available]
            best,(score,area,parts) = max(evaluated,key=lambda pair:(round(pair[1][0],12),-pair[0]['catalog_index']))
            selected.append(dict(best, score_parts=parts, area_id=area, exploration_pick=bool(reserve)))
            area_counts[area] = area_counts.get(area,0)+1
            reserved += int(reserve)
            remaining[best['zone']] -= 1
            pool.remove(best)
        return selected

    def _rerank(self, rows, request, reranker,timeout):
        if reranker is None:
            return rows, 'unconfigured_local_fallback'
        if len(rows) > 30:
            return rows, 'candidate_limit_local_fallback'
        payload = dict(interests=request.interests, goal=request.goal, ids=[r['concept_id'] for r in rows],
                       candidates=[{k:r[k] for k in ('concept_id','topic','description','sources')} for r in rows])
        if len(str(payload)) > 20000:
            return rows, 'input_limit_local_fallback'
        if timeout <= 0:
            return rows, 'deadline_local_fallback'
        if not self._rerank_slot.acquire(blocking=False):
            return rows, 'busy_local_fallback'
        result = queue.Queue(maxsize=1)
        def execute():
            try:
                result.put(('ok',reranker(payload,timeout=timeout)))
            except Exception:
                result.put(('error',None))
            finally:
                self._rerank_slot.release()
        # A noncooperative adapter cannot block the caller or spawn unbounded workers.
        # The adapter still owns cancellation of any underlying network request.
        threading.Thread(target=execute,daemon=True).start()
        try:
            status,order = result.get(timeout=timeout)
            if status != 'ok':
                return rows, 'provider_error_local_fallback'
            if not isinstance(order,list) or not all(isinstance(cid,str) for cid in order) or len(order) != len(rows) or set(order) != set(payload['ids']):
                return rows, 'invalid_output'
            by_id = {r['concept_id']:r for r in rows}
            return [by_id[cid] for cid in order], 'ok'
        except queue.Empty:
                return rows, 'timeout_local_fallback'
