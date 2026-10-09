"""Request-local, dated interest strands; geometry predicts, not measures care."""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from datetime import datetime, timezone

import numpy as np

from .known_policy import content_signal


@dataclass(frozen=True)
class HistoryConfig:
    half_life_days: float = 60.
    forecast_days: float = 14.
    max_step: float = .12
    strand_distance: float = .25

    def validate(self):
        bounds = {'half_life_days': (1, 3650), 'forecast_days': (0, 365),
                  'max_step': (0, .2), 'strand_distance': (.05, .35)}
        for name, (low, high) in bounds.items():
            value = getattr(self, name)
            if type(value) not in (int, float) or not math.isfinite(value) or not low <= value <= high:
                raise ValueError('Invalid history control.')


def date_seconds(value):
    """ISO calendar dates use midnight UTC; timestamps require an explicit zone."""
    if value is None:
        return None
    if not isinstance(value, str) or not re.fullmatch(
        r'\d{4}-\d{2}-\d{2}(?:T(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d'
        r'(?:\.\d{1,6})?(?:Z|[+-](?:[01]\d|2[0-3]):[0-5]\d))?', value
    ):
        raise ValueError('Interest dates must be ISO dates or timezone-qualified timestamps.')
    try:
        moment = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return moment.replace(tzinfo=timezone.utc).timestamp() if moment.tzinfo is None else moment.timestamp()
    except (ValueError, OverflowError, OSError) as exc:
        raise ValueError('Invalid interest date.') from exc


def split_dates(interests):
    records, dates = [], []
    for item in interests:
        record = {'phrase': item} if isinstance(item, str) else item
        if not isinstance(record, dict) or set(record) - {'phrase', 'concept_id', 'date'}:
            raise ValueError('Invalid interest record.')
        dates.append(date_seconds(record.get('date')))
        records.append({key: value for key, value in record.items() if key != 'date'})
    return records, dates


def _unit(vector):
    norm = float(np.linalg.norm(vector))
    if norm < 1e-12:
        raise ValueError('Interest strand has no stable direction.')
    return vector / norm


def _mean_unique(vectors, members):
    return _unit(np.mean(np.unique(vectors[members], axis=0), axis=0))


def _partition_strands(vectors, dates, indices, config, *, timed):
    groups, centers, membership = [], [], {}
    times = sorted({dates[i] if timed else 0. for i in indices})
    for moment in times:
        block = sorted((i for i in indices if (dates[i] if timed else 0.) == moment),
                       key=lambda i: tuple(vectors[i]))
        # Previous-time centers stay fixed throughout a simultaneous block.
        previous_count, current = len(groups), {}
        for index in block:
            key = tuple(vectors[index])
            target = membership.get(key)
            if target is None:
                distances = [math.acos(float(np.clip(vectors[index] @ center, -1, 1))) / math.pi
                             for center in centers]
                if distances and min(distances) <= config.strand_distance:
                    target = int(np.argmin(distances))
                else:
                    target = len(groups)
                    groups.append([])
                    centers.append(vectors[index])
                membership[key] = target
            groups[target].append(index)
            current.setdefault(target, []).append(index)
            if target >= previous_count:
                centers[target] = _mean_unique(vectors, current[target])
        for target, members in current.items():
            centers[target] = _mean_unique(vectors, members)
    return groups


def build_history(vectors, dates, config, *, focus_index=None):
    """Partition independent strands before estimating recency and velocity.

    Undated anchors have their own static strands. Equal-time observations are
    averaged, never ordered. All time weights are relative to submitted dates,
    so replaying a request later does not change its recommendations.
    """
    config.validate()
    strands = []
    dated = [index for index, date in enumerate(dates) if date is not None]
    latest = max((dates[index] for index in dated), default=0.)
    for indices, timed in [(dated, True), ([i for i, d in enumerate(dates) if d is None], False)]:
        group = _partition_strands(vectors, dates, indices, config, timed=timed)
        strands.extend((members, timed) for members in group)
    profiles, details = [], []
    for members, timed in strands:
        status, confidence, speed, step = 'no_dates', 0., 0., 0.
        if timed:
            times = sorted({dates[i] for i in members})
            points = np.asarray([_mean_unique(vectors, [i for i in members if dates[i] == t]) for t in times])
            days = (np.asarray(times) - times[-1]) / 86400.
            weights = np.exp2(days / config.half_life_days)
            center = _unit(np.average(points, axis=0, weights=weights))
            importance = float(np.exp2(-(latest-times[-1]) / (86400.*config.half_life_days)))
            status = 'insufficient_history'
            forecast = center.copy()
            if len(times) >= 3:
                mean_time = float(np.average(days, weights=weights))
                mean_point = np.average(points, axis=0, weights=weights)
                centered_time = days - mean_time
                variance = float(np.sum(weights*centered_time**2))
                slope = (np.sum(weights[:, None]*centered_time[:, None]*(points-mean_point), axis=0) / variance
                         if variance > 1e-12 else np.zeros_like(center))
                residual = points - (mean_point + centered_time[:, None]*slope)
                total = float(np.sum(weights[:, None]*(points-mean_point)**2))
                confidence = max(0., min(1., 1-float(np.sum(weights[:, None]*residual**2))/total)) if total > 1e-12 else 0.
                tangent = slope - center*float(slope @ center)
                speed = float(np.linalg.norm(tangent)) / math.pi
                status = ('insufficient_effective_history' if variance <= 1e-12 else
                          'stationary' if total <= 1e-12 or speed <= 1e-8 else 'inconsistent_history')
                if speed > 1e-8 and confidence >= .5:
                    movement = tangent*config.forecast_days
                    length = float(np.linalg.norm(movement))
                    if length:
                        movement *= min(1., math.tan(math.pi*config.max_step)/length)
                    forecast = _unit(center + movement)
                    step = math.acos(float(np.clip(center @ forecast, -1, 1))) / math.pi
                    status = 'usable' if step > 1e-8 else 'zero_horizon'
        else:
            center = _mean_unique(vectors, members)
            forecast, importance, times = center.copy(), 1., []
        active = focus_index is None or focus_index in members
        if active:
            profiles.append(dict(center=center, forecast=forecast, weight=importance, usable=status == 'usable'))
        details.append(dict(observation_count=len(members), distinct_dates=len(times), active=active,
            direction_status=status, fit_score=confidence, angular_speed_per_day=speed, forecast_step=step))
    return profiles, details


def rank_history(candidates, units, request, config, profile, profiles, *, use_velocity):
    """The two models differ only by the optional forecast-alignment term."""
    selected, pool = [], list(candidates)
    diversity = config.diversity if config.diversity is not None else request.diversity
    rng = np.random.default_rng(request.seed)
    jitter = {row['concept_id']: float(rng.uniform(-request.randomness, request.randomness)) for row in candidates}
    while pool and len(selected) < request.limit:
        def evaluate(row):
            vector = units[row['catalog_index']]
            recent = max(float(vector @ p['center'])*p['weight'] for p in profiles)
            # Associate a candidate with its best recent strand; trajectories from
            # an unrelated strand must not supply an artificial direction boost.
            strand = max(profiles, key=lambda p: float(vector @ p['center'])*p['weight'])
            alignment = (float(vector @ (strand['forecast']-strand['center']))*strand['weight']
                         if use_velocity and strand['usable'] and strand['weight'] > 1e-12 else 0.)
            progress = min(1., row['nearest_interest_distance']/config.distance_cap)
            expansion = 4*progress*(1-progress)
            redundancy = max(0., max((float(vector @ units[s['catalog_index']]) for s in selected), default=0.))
            rating = profile['items'].get(row['concept_id'], {})
            parts = dict(relevance=.55*row['retrieval'], recency=.30*recent,
                trajectory=.35*alignment, content=.05*content_signal(row['description']),
                expansion_opportunity=.25*request.exploration_fraction*expansion,
                diversity=-diversity*redundancy, curiosity=.30*bool(rating.get('curious')),
                presentation=-.35 if rating.get('difficulty', 'none') != 'none' else 0.,
                randomness=jitter[row['concept_id']])
            return sum(parts.values()), parts
        evaluated = [(row, evaluate(row)) for row in pool]
        best, (_, parts) = max(evaluated, key=lambda pair: (round(pair[1][0], 12), -pair[0]['catalog_index']))
        selected.append(dict(best, score_parts=parts))
        pool.remove(best)
    return selected
