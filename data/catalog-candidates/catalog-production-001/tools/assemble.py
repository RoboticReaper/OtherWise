"""Bounded first-card assembly; original card artifacts are read-only inputs."""
import argparse
import copy
import importlib.util
from functools import lru_cache
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('production_combiner', HERE/'production_combiner.py')
STOCK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(STOCK)
Rejected = STOCK.Rejected
sha = STOCK.file_hash
read = lambda path: STOCK.strict_load(path)[0]


def require(condition, code, reason):
    if not condition: STOCK.reject(code, reason)


def assemble(paths, baseline_path, decisions_path, approval_path):
    baseline, baseline_sha = STOCK.strict_load(baseline_path)
    approved, selection_sha = STOCK.strict_load(approval_path)
    require(approved.get('schema_version') == 1 and isinstance(approved.get('accepted'), list),
            'invalid_reservations', 'Approved selection must contain an accepted list.')
    require(approved.get('baseline_index_sha256') == baseline_sha,
            'stale_baseline', 'Selection must refer to the exact frozen baseline.')
    bid = approved.get('batch_id')
    require(isinstance(bid, str) and bid.startswith('research-batch-'),
            'invalid_batch', 'Selection needs a bounded research batch ID.')
    reservations = {r['id']: r for r in approved['accepted']}
    require(len(reservations) == len(approved['accepted']) <= 200,
            'reservation_limit', 'Distinct reservations are bounded at 200 cards.')
    owners = {r['owner'] for r in reservations.values()}
    STOCK.PILOT_ID = bid
    STOCK.PILOT_BATCHES = {bid+'-'+owner for owner in owners}
    prior = set(approved.get('prior_accepted_ids', []))
    seen = set()
    for path in paths:
        data, _ = STOCK.strict_load(path)
        STOCK.validate_candidate(data, path)
        shard = data['batch']['id']
        require(data['batch'].get('global_selection_manifest_sha256') == selection_sha,
                'stale_selection', 'Shard must use the approved selection hash.')
        require(data['batch'].get('baseline_index_sha256') == baseline_sha,
                'stale_baseline', 'Shard must use the frozen baseline hash.')
        for c in data['concepts']:
            cid = c['id']
            r = reservations.get(cid, {})
            require(r.get('approved') is True and r.get('identity_reason') and r.get('discovery_evidence'),
                    'unreserved_identity', f'{cid} lacks an approved evidence-backed reservation.')
            require(shard == bid+'-'+r['owner'], 'wrong_owner', cid)
            require(cid in baseline['concepts'], 'unregistered_identity', cid)
            base = baseline['concepts'][cid]
            require(not base.get('candidate_records') and not base.get('latest_card'),
                    'legacy_overwrite', f'{cid} already has a researched card; production preserves it.')
            require(cid not in prior, 'repeated_production_card', cid)
            if c['card_version'] > 1:
                repairs = data['batch'].get('repair_history', [])
                require(any(h.get('id') == cid and h.get('card_version') == c['card_version']
                            and h.get('prior_version', 0) == c['card_version']-1
                            and h.get('reason') and len(h.get('initial_snapshot_sha256', '')) == 64
                            for h in repairs), 'unrecorded_card_repair', cid)
            require(c['scope'] == r['scope'] and c['entity_kind'] == r['entity_kind']
                    and c['domains'][0] == r['primary_domain'], 'reserved_subject_changed', cid)
            require(c['original_description'] == base.get('original_description'),
                    'original_wording_changed', cid)
            require(c['imported_records'] == base.get('inventory_records', []),
                    'raw_import_changed', cid)
            require(all(e.get('url', '').startswith('https://') and e.get('locator')
                        for e in r['discovery_evidence']), 'missing_discovery_passage', cid)
            seen.add(cid)
    require(seen == set(reservations), 'selection_shortfall', 'Reserved and emitted identities must match.')
    result = STOCK.assemble(paths, baseline_path, decisions_path)
    require(len(result['concepts']) == len(reservations), 'count_changed', 'Reconciliation changed the accepted count.')
    result['batch'].update(kind='production_first_card_candidate',
        approved_selection_sha256=selection_sha, approved_selection_snapshot=approved,
        production_id='catalog-production-001', word_budget={'minimum': 1, 'maximum': 25},
        assembler_dependency_sha256=sha(HERE/'production_combiner.py'))
    result['validation'].pop('canonical_content_sha256', None)
    result['validation']['canonical_content_sha256'] = STOCK.digest(result)
    return result


def publish(paths, baseline, decisions, approved, output, report):
    previous = sha(output) if Path(output).exists() else None
    try:
        result = assemble(paths, baseline, decisions, approved)
        require(result == assemble(list(reversed(paths)), baseline, decisions, approved),
                'order_dependency', 'Reversed input changed the candidate.')
        require(result == assemble(paths+[paths[0]], baseline, decisions, approved),
                'non_idempotent', 'Repeated input changed the candidate.')
        STOCK.atomic_json(output, result)
        STOCK.atomic_json(report, dict(status='passed', candidate_sha256=sha(output),
            accepted_first_cards=len(result['concepts']), reversed_inputs_identical=True,
            repeated_input_identical=True, legacy_rewritten_count=0, failed=[]))
        return result
    except Rejected as exc:
        STOCK.atomic_json(report, dict(status='quarantined', errors=exc.errors,
            prior_output_sha256=previous,
            last_valid_output_retained=previous is not None and sha(output) == previous))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('baseline', 'decisions', 'approved', 'output', 'report'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--inputs', type=Path, nargs='+', required=True)
    args = parser.parse_args()
    try: publish(args.inputs, args.baseline, args.decisions, args.approved, args.output, args.report)
    except Rejected as exc: raise SystemExit(str(exc))
