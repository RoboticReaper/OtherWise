"""Validate saved evidence and diagnose score-weight sensitivity without tuning.

Run from any directory with the repository's Python environment. This reads the
frozen outputs/grades; it neither reruns recommendations nor changes nominations.
The sensitivity exercise is post hoc and is not another selection scorecard.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from statistics import mean

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))

from explorer import load_catalog
from graph_explorer import load_graph
from recommendation_lab.__main__ import code_identity, runtime_fingerprint
from recommendation_lab.benchmark import evaluate_runs, evaluation_space, write_json
from recommendation_lab.evaluation import GradeStore, valid_source
from recommendation_lab.inventory import Inventory, digest


def read(path):
    return json.loads(path.read_text())


def components(run, store, scores, inventory):
    if scores['integrity_failures'] or scores['missing_grades']:
        return None
    known = set(run['profile'].get('known_ids', []))
    known |= {r['concept_id'] for r in inventory.resolve(run['profile']['interests']) if r['concept_id']}
    known |= {r['concept_id'] for r in run['batch']['resolutions'] if r.get('concept_id')}
    totals = dict(C=0., N=0., E=0., A=0., D=0.)
    seen, passing = set(), 0
    for row in run['batch']['recommendations']:
        cid = row['concept_id']
        if cid in known or cid in seen or not valid_source(row, inventory):
            continue
        seen.add(cid)
        grade = store.get(run['profile'], row)
        assert grade is not None
        if grade['C'] < 2 or not grade['bridge'].strip():
            continue
        passing += 1
        for k in ('C', 'N', 'E', 'A'):
            totals[k] += .5 if grade[k] is None else grade[k] / 3
    assert passing == scores['passing']
    for k in totals:
        totals[k] /= scores['requested']
    totals['D'] = passing / scores['requested'] * scores['diversity']
    return totals


def weight_cases(weights):
    yield 'reference', weights
    for donor in weights:
        for receiver in weights:
            if donor == receiver or weights[donor] < .05:
                continue
            changed = dict(weights)
            changed[donor] -= .05
            changed[receiver] += .05
            yield f'{donor}-0.05/{receiver}+0.05', changed


def main():
    inventory = Inventory.from_sources(load_catalog(), load_graph(), read(ROOT/'data/recommendation-identities.json'))
    vectors, vector_identity = evaluation_space({cid: inventory.text(cid) for cid in inventory.concepts})
    nomination = read(HERE/'nomination.json')
    assert nomination['digest'] == digest({k: v for k, v in nomination.items() if k != 'digest'})
    assert read(HERE/'heldout-receipt.json')['nomination_digest'] == nomination['digest']
    validation, grouped = {}, {}
    formulas = dict(discovery=dict(C=.4, N=.3, E=.2, A=.1),
                    depth=dict(C=.55, E=.3, A=.15), variety=dict(C=.6, D=.4))
    for split in ('development', 'heldout'):
        directory = HERE/split
        manifest, runs, packet = [read(directory/name) for name in ('manifest.json', 'outputs.json', 'packet.json')]
        assert manifest['code_sha256'] == code_identity()
        assert manifest['profiles_sha256'] == digest(read(HERE/'profiles.json'))
        assert manifest['outputs_sha256'] == digest(runs)
        assert manifest['packet_id'] == packet['packet_id']
        assert manifest['runtime_fingerprint'] == runtime_fingerprint(manifest['runtime'])
        assert manifest['runtime']['inventory_version'] == inventory.version
        assert manifest['runtime']['evaluation_embedding'] == vector_identity
        if split == 'heldout':
            assert manifest['nomination_digest'] == nomination['digest']
            assert manifest['systems'] == nomination['identity']['finalist_systems']
            assert manifest['code_sha256'] == nomination['identity']['code_sha256']
            assert manifest['runtime_fingerprint'] == nomination['identity']['runtime_fingerprint']
            assert manifest['evaluator'] == nomination['identity']['evaluator']
        store = GradeStore.from_packet(packet, read(directory/'ratings.json'), existing=read(directory/'grades.json'))
        assert len(store.grades) == len(packet['items'])
        records, _ = evaluate_runs(runs, store, vectors, inventory=inventory)
        saved = read(directory/'scores.json')
        assert len(records) == len(saved)
        for current, previous in zip(records, saved):
            for field in ('system', 'profile_id', 'family', 'seconds', 'cost_usd'):
                assert current[field] == previous[field]
            for field, value in current['scores'].items():
                old = previous['scores'][field]
                assert value == old or (isinstance(value, float) and isinstance(old, float) and math.isclose(value, old, abs_tol=1e-12))
        failures = [dict(system=r['system'], profile_id=r['profile_id'], count=r['scores']['integrity_failures'])
                    for r in records if r['scores']['integrity_failures']]
        validation[split] = dict(request_batches=len(runs), quality_lists=len(records), judgments=len(store.grades),
                                 missing_grades=sum(r['scores']['missing_grades'] for r in records),
                                 empty_quality_lists=sum(r['scores']['returned'] == 0 for r in records),
                                 integrity_failures=failures, outputs_and_scores_verified=True)
        lookup = {(r['system'], r['profile_id']): r['scores'] for r in records}
        for run in runs:
            if not run['profile'].get('quality', True):
                continue
            scores = lookup[run['system'], run['profile']['id']]
            values = components(run, store, scores, inventory)
            if values is None:
                continue
            for metric, weights in formulas.items():
                assert math.isclose(sum(values[k]*w for k, w in weights.items()), scores[metric], abs_tol=1e-12)
            kind = run['profile'].get('controls', {}).get('result_kind', 'specific')
            grouped.setdefault((split, kind), {}).setdefault(run['system'], []).append(values)
    diagnostics = dict(status='post_hoc_diagnostic_only', shift=.05,
                       note='Frozen grades and gates; pairwise weight transfers preserve total weight. No retuning, regrading or nomination changes.',
                       comparisons={})
    for (split, kind), systems in grouped.items():
        expected = max(len(rows) for rows in systems.values())
        systems = {name: rows for name, rows in systems.items() if len(rows) == expected}
        tracks = {}
        for metric, reference in formulas.items():
            cases = []
            for label, weights in weight_cases(reference):
                scores = {name: mean(sum(row[k]*w for k, w in weights.items()) for row in rows)
                          for name, rows in systems.items()}
                maximum = max(scores.values())
                winners = [name for name, value in scores.items() if math.isclose(value, maximum, abs_tol=1e-12)]
                cases.append(dict(case=label, weights=weights, quality_winners=winners, scores=scores))
            tracks[metric] = cases
        diagnostics['comparisons'][f'{split}/{kind}'] = tracks
    write_json(HERE/'validation.json', validation)
    write_json(HERE/'sensitivity.json', diagnostics)
    print(json.dumps(validation, indent=2))
    for kind in ('specific', 'broad'):
        for metric, cases in diagnostics['comparisons'][f'heldout/{kind}'].items():
            patterns = sorted({tuple(case['quality_winners']) for case in cases})
            print(f'heldout/{kind}/{metric}: {len(cases)} weight settings, winner sets {patterns}')


if __name__ == '__main__':
    main()
