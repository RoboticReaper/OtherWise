"""Offline experiment CLI. Run, blind-grade, compare, tune, then hold out once."""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

from explorer import ROOT, load_catalog
from graph_explorer import load_graph
from .inventory import Inventory, digest
from .systems import VARIANTS
from .evaluation import Evaluator, GradeStore, make_packet, METRICS
from .benchmark import (write_json,load_runtime,validate_profiles,run_cases,evaluate_runs,
                        bounded_search,SearchBudget,seal_finalists,claim_heldout,evaluation_space,paired_uncertainty)

DEFAULT_PROFILES = ROOT/'experiments/recommendation-benchmark/profiles.json'
DEFAULT_SYSTEMS = ROOT/'experiments/recommendation-benchmark/systems.json'
DEFAULT_EVALUATOR = Evaluator('session-assistant-review-2026-10-07-v1')


def code_identity():
    paths = sorted((ROOT/'recommendation_lab').glob('*.py')) + [ROOT/'explorer.py',ROOT/'graph_explorer.py',ROOT/'feedback.py']
    return digest({str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})


def load_json(path):
    return json.loads(Path(path).read_text())


def run(args):
    if args.out.exists():
        raise ValueError('Output directory already exists; use a fresh run directory.')
    profiles_document = load_json(args.profiles)
    profiles = profiles_document['profiles']
    validate_profiles(profiles)
    nomination = None
    if args.split == 'heldout':
        if args.cycle is None:
            raise ValueError('Held-out execution requires a frozen development nomination.')
        nomination = load_json(args.cycle/'nomination.json')
        if nomination['identity']['profiles_sha256'] != digest(profiles_document) or nomination['identity']['code_sha256'] != code_identity():
            raise ValueError('Benchmark or implementation changed after finalist nomination.')
        systems = nomination['identity']['finalist_systems']
    else:
        systems = load_json(args.systems)['systems']
    if len({s['name'] for s in systems}) != len(systems) or any(s['variant'] not in VARIANTS for s in systems):
        raise ValueError('System names must be unique and variants valid.')
    profiles = [p for p in profiles if p['split'] == args.split]
    if not profiles:
        raise ValueError('No profiles in this split.')
    start = time.perf_counter()
    lab,vectors,runtime = load_runtime()
    if nomination and nomination['identity']['runtime_fingerprint'] != runtime_fingerprint(runtime):
        raise ValueError('Runtime changed after finalist nomination.')
    if nomination:
        claim_heldout(args.cycle,nomination)
    initialization = time.perf_counter()-start
    runs = run_cases(lab,profiles,systems)
    evaluator = DEFAULT_EVALUATOR if nomination is None else evaluator_from_identity(nomination['identity']['evaluator'])
    packet = make_packet([r for r in runs if r['profile'].get('quality',True)],evaluator,seed=42)
    manifest = dict(schema_version=1,split=args.split,profiles_sha256=digest(profiles_document),
                    code_sha256=code_identity(),runtime=runtime,runtime_fingerprint=runtime_fingerprint(runtime),
                    systems=systems,evaluator=evaluator.identity(),packet_id=packet['packet_id'],
                    initialization_seconds=initialization,nomination_digest=nomination['digest'] if nomination else None,
                    note='Public synthetic profiles; no participant ratings. Cold model setup separate; serving times include first-time interest encoding.')
    write_json(args.out/'manifest.json',manifest)
    write_json(args.out/'outputs.json',runs)
    write_json(args.out/'packet.json',packet)
    structure = {}
    for system in systems:
        selected = [r for r in runs if r['system'] == system['name']]
        structure[system['name']] = dict(cases=len(selected),clarifications=sum(r['batch']['status']=='clarification_needed' for r in selected),
            returned=sum(len(r['batch']['recommendations']) for r in selected),
            empty=sum(r['batch']['status']=='ok' and not r['batch']['recommendations'] for r in selected),
            mean_eligible_recall=sum(r['batch']['diagnostics'].get('eligible_recall') or 0 for r in selected)/len(selected))
    write_json(args.out/'structural.json',structure)
    print(json.dumps(dict(output=str(args.out),cases=len(profiles),systems=len(systems),blind_items=len(packet['items']),initialization_seconds=round(initialization,3))))


def runtime_fingerprint(runtime):
    # Cache migration happened only on the first run, and does not change embeddings.
    return digest({k:v for k,v in runtime.items() if k != 'cache_migrations'})


def evaluator_from_identity(identity):
    evaluator = Evaluator(identity['name'],identity['rubric'],identity['prompt'])
    if evaluator.identity() != identity:
        raise ValueError('Evaluator identity is invalid.')
    return evaluator


def compare(args):
    manifest,runs,packet = [load_json(args.run/name) for name in ('manifest.json','outputs.json','packet.json')]
    if packet['packet_id'] != manifest['packet_id']:
        raise ValueError('Packet does not belong to this run.')
    grades = GradeStore.from_packet(packet,load_json(args.ratings))
    if grades.evaluator.identity() != manifest['evaluator']:
        raise ValueError('Run and grade evaluator versions differ.')
    inventory = Inventory.from_sources(load_catalog(),load_graph(),load_json(ROOT/'data/recommendation-identities.json'))
    vectors,identity = evaluation_space({cid:inventory.text(cid) for cid in inventory.concepts})
    if inventory.version != manifest['runtime']['inventory_version'] or identity != manifest['runtime']['evaluation_embedding']:
        raise ValueError('Inventory/evaluator vectors changed; start a new benchmark.')
    records,report = evaluate_runs(runs,grades,vectors)
    by_kind = {}
    for kind in ('specific','broad'):
        ids = {r['profile']['id'] for r in runs if r['profile'].get('controls',{}).get('result_kind','specific') == kind}
        kind_records = [r for r in records if r['profile_id'] in ids]
        if kind_records:
            from .evaluation import scoreboard
            by_kind[kind] = scoreboard(kind_records)
    # The primary track is specific concepts; broad navigation is reported separately.
    report = dict(by_kind.get('specific',report),by_kind=by_kind)
    primary_ids = {r['profile']['id'] for r in runs if r['profile'].get('controls',{}).get('result_kind','specific') == 'specific'}
    primary_records = [r for r in records if r['profile_id'] in primary_ids]
    report.update(evaluator=grades.evaluator.identity(),split=manifest['split'],packet_id=packet['packet_id'],
                  judgment_count=len(grades.grades),uncertainty=paired_uncertainty(primary_records,report['champions']),
                  status='experimental_proxy_only',second_judge='not performed; user selected session assistant',
                  evaluator_call_cost_usd=0.,evaluator_cost_note='In-session review; existing assistant usage is not estimated as free compute.')
    write_json(args.run/'grades.json',grades.to_dict())
    write_json(args.run/'scores.json',records)
    write_json(args.run/'scoreboard.json',report)
    markdown = ['# Recommendation comparison', '', 'Experimental proxy scores; session assistant judged blinded source-backed items. Actual personal curiosity is unmeasured. No production deployment.', '',
                '| System | Connection | Discovery | Depth | Variety | p95 seconds |', '|---|---:|---:|---:|---:|---:|']
    for name,row in report['systems'].items():
        values = [f'{row[k]:.4f}' if row[k] is not None else 'unavailable' for k in METRICS]
        markdown.append('| '+ ' | '.join([name,*values,f"{row['p95_seconds']:.4f}"])+' |')
    markdown += ['', 'Per-metric experimental winners: '+json.dumps(report['champions']), '',
                 'Variety uses a separately frozen hashed TF-IDF angular space. It measures lexical diversity, with weaker semantic interpretation than an independent semantic encoder.',
                 'These scores depend on a single assistant rubric. A second judge and repeat/order audit are required before an operational selection. Missing grades and integrity failures prevent selection.']
    (args.run/'report.md').write_text('\n'.join(markdown)+'\n')
    print(json.dumps(dict(judgments=len(grades.grades),champions=report['champions'],report=str(args.run/'report.md'))))


def tune(args):
    manifest = load_json(args.run/'manifest.json')
    if manifest['split'] != 'development':
        raise ValueError('Tuning accepts development runs only.')
    runs = load_json(args.run/'outputs.json')
    scores = load_json(args.run/'scoreboard.json')
    profiles = {r['profile']['id']:r['profile'] for r in runs if r['profile'].get('quality',True)}
    names = [s['name'] for s in manifest['systems']]
    result = bounded_search(names,list(profiles.values()),lambda name,p:
        {k:scores['systems'][name][k] if scores['systems'][name]['eligible_for_selection'] else None for k in METRICS},
        SearchBudget(args.rounds,args.per_round,args.patience,.01))
    if any(name is None for name in result['champions'].values()):
        raise ValueError('Complete eligible grades are required before nominating finalists.')
    finalists = set(result['champions'].values()) | {'V0','V1','V2','V3'}
    finalist_systems = [s for s in manifest['systems'] if s['name'] in finalists]
    identity = dict(profiles_sha256=manifest['profiles_sha256'],code_sha256=manifest['code_sha256'],
                    runtime_fingerprint=manifest['runtime_fingerprint'],evaluator=manifest['evaluator'],
                    finalist_systems=finalist_systems,development_packet_id=manifest['packet_id'])
    nomination = seal_finalists(args.cycle,result['champions'],identity)
    write_json(args.cycle/'search.json',result)
    print(json.dumps(dict(champions=result['champions'],stop_reason=result['stop_reason'],attempts=len(result['attempts']),nomination=nomination['digest'])))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command',required=True)
    execute = sub.add_parser('run')
    execute.add_argument('--profiles',type=Path,default=DEFAULT_PROFILES)
    execute.add_argument('--systems',type=Path,default=DEFAULT_SYSTEMS)
    execute.add_argument('--split',choices=['development','heldout'],default='development')
    execute.add_argument('--out',type=Path,required=True)
    execute.add_argument('--cycle',type=Path)
    evaluate = sub.add_parser('compare')
    evaluate.add_argument('--run',type=Path,required=True)
    evaluate.add_argument('--ratings',type=Path,required=True)
    optimize = sub.add_parser('tune')
    optimize.add_argument('--run',type=Path,required=True)
    optimize.add_argument('--cycle',type=Path,required=True)
    optimize.add_argument('--rounds',type=int,default=5)
    optimize.add_argument('--per-round',type=int,default=20)
    optimize.add_argument('--patience',type=int,default=2)
    args = parser.parse_args()
    try:
        dict(run=run,compare=compare,tune=tune)[args.command](args)
    except (ValueError,RuntimeError) as error:
        parser.exit(2,f'{error}\n')


if __name__ == '__main__':
    main()
