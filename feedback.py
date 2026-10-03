"""Explicit, editable local feedback. Curiosity, familiarity and challenge stay separate."""
from __future__ import annotations

import json
import os
import tempfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

PROFILE_PATH = Path(__file__).resolve().parent / '.local' / 'feedback.json'


def new_profile():
    return {'version': 1, 'items': {}, 'exposures': {}}


def _rating(concept_id, curious, known, difficulty, level, area_ids):
    if not isinstance(concept_id, str) or not concept_id.strip():
        raise ValueError('A concept ID is required.')
    if not isinstance(curious, bool) or not isinstance(known, bool):
        raise ValueError('Curious and known must be true or false.')
    if difficulty not in ('none', 'too_basic', 'too_hard'):
        raise ValueError('Difficulty must be none, too_basic, or too_hard.')
    if level is not None and (type(level) is not int or level not in (1, 2, 3)):
        raise ValueError('Presentation level must be 1, 2, 3, or None.')
    if not isinstance(area_ids, list) or any(not isinstance(a, str) or not a for a in area_ids):
        raise ValueError('Area IDs must be a list of nonempty strings.')
    return dict(curious=curious, known=known, difficulty=difficulty, level=level,
                area_ids=list(dict.fromkeys(area_ids)))


def set_feedback(profile, concept_id, *, curious=False, known=False, difficulty='none', level=None, area_ids=None):
    """Replace the latest rating, allowing curious + known/difficulty combinations."""
    rating = _rating(concept_id, curious, known, difficulty, level, [] if area_ids is None else area_ids)
    rating['updated_at'] = datetime.now(timezone.utc).isoformat()
    profile['items'][concept_id] = rating


def clear_feedback(profile, concept_id):
    profile['items'].pop(concept_id, None)


def area_preferences(profile):
    """Local challenge preferences, not competence estimates or graph-depth scores."""
    observations = defaultdict(lambda: {'curious': 0, 'levels': []})
    for rating in profile['items'].values():
        for area in rating['area_ids']:
            obs = observations[area]
            obs['curious'] += int(rating['curious'])
            difficulty, level = rating['difficulty'], rating['level']
            if difficulty == 'too_basic':
                obs['levels'].append(min(3, level + 1) if level is not None else 3)
            elif difficulty == 'too_hard':
                obs['levels'].append(max(1, level - 1) if level is not None else 1)
    return {area: {'curiosity': min(1.0, obs['curious'] / 3),
                   'level': sum(obs['levels']) / len(obs['levels']) if obs['levels'] else None}
            for area, obs in observations.items()}


def record_exposures(profile, rows):
    """Count shown cards by their selected source area; no inferred likes or knowledge."""
    for row in rows:
        area = row['area_id']
        profile['exposures'][area] = profile['exposures'].get(area, 0) + 1


def _validate(profile):
    if not isinstance(profile, dict) or profile.get('version') != 1:
        raise ValueError('Unsupported feedback profile version.')
    if not isinstance(profile.get('items'), dict) or not isinstance(profile.get('exposures'), dict):
        raise ValueError('Invalid feedback profile structure.')
    for concept, rating in profile['items'].items():
        if not isinstance(rating, dict):
            raise ValueError('Invalid feedback profile rating.')
        try:
            _rating(concept, rating['curious'], rating['known'], rating['difficulty'], rating['level'], rating['area_ids'])
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError('Invalid feedback profile rating.') from error
    if any(not isinstance(k, str) or type(v) is not int or v < 0 for k, v in profile['exposures'].items()):
        raise ValueError('Invalid feedback profile exposure counts.')
    return profile


def load_profile(path=PROFILE_PATH):
    path = Path(path)
    if not path.exists():
        return new_profile()
    try:
        return _validate(json.loads(path.read_text()))
    except (json.JSONDecodeError, ValueError) as error:
        raise ValueError(f'Cannot read feedback profile {path}: {error}') from error


def save_profile(profile, path=PROFILE_PATH):
    _validate(profile)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, prefix='.feedback-', suffix='.tmp', delete=False) as handle:
            temporary = Path(handle.name)
            json.dump(profile, handle, indent=2, ensure_ascii=False, allow_nan=False)
            handle.write('\n')
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
