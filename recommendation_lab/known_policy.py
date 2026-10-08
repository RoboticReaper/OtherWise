"""Opt-in experimental ranking of unknown concepts inside familiar fields.

The description-shape feature is a disclosed text heuristic. It is not an
evaluator grade, a prerequisite judgment, or a person's measured curiosity.
"""
import math
import re

import numpy as np

from feedback import area_preferences


def content_signal(description):
    text = description.casefold()
    organization = re.search(r'\b(association|society|organization|organisation|institute|university|company|journal|magazine|award)\b', text)
    mechanism = re.search(r'\b(algorithm|method|process|phenomenon|effect|technique|theorem|principle|strategy|measurement|equation|model|mechanism)\b', text)
    explanation = re.search(r'\b(that|where|because|causes|measures|solves|explains|used to|due to|relationships? between)\b', text)
    value = .25 + .4*bool(mechanism) + .25*bool(explanation)
    if organization and not mechanism:
        value = 0.
    return value


def rank_known(candidates, units, request, config, profile, reached):
    defaults = dict(connection=(.95,.05,0.,.05), discovery=(.65,.20,.15,.15),
                    depth=(.65,.35,0.,.10), variety=(.75,.25,0.,.40))[request.goal]
    relevance, content, novelty, diversity = [value if value is not None else defaults[i]
        for i,value in enumerate((config.relevance,config.content,config.novelty,config.diversity))]
    preferences = area_preferences(profile)
    possible_areas = {area for row in candidates for area in reached.get(row.get('id'),{}).get('area_ids',[])}
    minimum = min((request.exposures.get(area,0) for area in possible_areas),default=0)
    least = {area for area in possible_areas if request.exposures.get(area,0)==minimum}
    limit = min(request.limit,len(candidates))
    reserve_target = math.ceil(request.exploration_fraction*limit)
    rng = np.random.default_rng(request.seed)
    jitter = {row['concept_id']:float(rng.uniform(-request.randomness,request.randomness))
              for row in sorted(candidates,key=lambda r:r['catalog_index'])}
    selected, area_counts, anchor_counts, reserved = [], {}, {}, 0
    pool = list(candidates)
    while pool and len(selected)<limit:
        reserve = reserved<reserve_target and any(set(reached.get(r.get('id'),{}).get('area_ids',[])) & least for r in pool)
        available = [r for r in pool if set(reached.get(r.get('id'),{}).get('area_ids',[])) & least] if reserve else pool
        def evaluate(row):
            areas = reached.get(row.get('id'),{}).get('area_ids',[])
            allowed = [area for area in areas if area in least] if reserve else areas
            area = min(allowed,key=lambda a:(area_counts.get(a,0),request.exposures.get(a,0),a)) if allowed else None
            rating = profile['items'].get(row['concept_id'],{})
            preference = preferences.get(area,{'curiosity':0,'level':None})
            redundancy = max(0.,max((float(units[row['catalog_index']] @ units[r['catalog_index']]) for r in selected),default=0.))
            progress = min(1.,row['anchor_distance']/config.distance_cap)
            parts = dict(relevance=relevance*row['retrieval'],content=content*content_signal(row['description']),
                         moderate_distance=novelty*4*progress*(1-progress),diversity=-diversity*redundancy,
                         curiosity=.30*bool(rating.get('curious'))+.18*preference['curiosity'],
                         presentation=-.35 if rating.get('difficulty','none')!='none' else 0.,
                         area_variety=-.04*area_counts.get(area,0) if area is not None else 0.,
                         anchor_variety=-.03*anchor_counts.get(row['nearest_interest'],0),
                         randomness=jitter[row['concept_id']])
            return sum(parts.values()),area,parts
        evaluated = [(row,evaluate(row)) for row in available]
        best,(_,area,parts)=max(evaluated,key=lambda pair:(round(pair[1][0],12),-pair[0]['catalog_index']))
        selected.append(dict(best,score_parts=parts,area_id=area,exploration_pick=bool(reserve)))
        area_counts[area]=area_counts.get(area,0)+1
        anchor_counts[best['nearest_interest']]=anchor_counts.get(best['nearest_interest'],0)+1
        reserved+=int(reserve)
        pool.remove(best)
    return selected
