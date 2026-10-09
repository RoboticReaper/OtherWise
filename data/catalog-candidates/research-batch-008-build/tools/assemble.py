"""Research batch 008 adapter for the previously verified candidate assembler.

Reads only approved reservations and research shards. No registry import or API.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from functools import lru_cache

HERE = Path(__file__).resolve().parent
STOCK = HERE.parents[1]/'scale-pilot-001/revision-002/tools/catalog_combiner.py'
SHARDS = {'research-batch-008-science','research-batch-008-systems','research-batch-008-culture'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def require(condition, message):
    if not condition:
        raise ValueError(message)


@lru_cache(maxsize=1)
def stock_module():
    # Configure only this new batch's input identities; preserve the original tool.
    spec = importlib.util.spec_from_file_location('batch008_stock_combiner', STOCK)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.PILOT_BATCHES = set(SHARDS)
    module.PILOT_ID = 'research-batch-008'
    return module


def assemble(paths, baseline_path, decisions_path, approval_path):
    approved = read(approval_path)
    require(approved.get('schema_version')==1 and isinstance(approved.get('accepted'),list),
            'Invalid approved selection manifest')
    reservations = {r['id']:r for r in approved['accepted']}
    require(len(reservations)==len(approved['accepted']), 'Reserved IDs must be unique')
    baseline = read(baseline_path)['concepts']
    baseline_sha = sha(baseline_path)
    require(approved.get('baseline_index_sha256')==baseline_sha, 'Approved selections refer to a changed baseline')
    selection_sha = sha(approval_path)
    for path in paths:
        data = read(path)
        bid = data['batch']['id']
        require(bid in SHARDS, f'Unassigned research shard: {bid}')
        require(data['batch'].get('global_selection_manifest_sha256')==selection_sha,
                f'Stale approved reservation hash in {bid}')
        require(data['batch'].get('baseline_index_sha256')==baseline_sha,
                f'Stale pinned baseline hash in {bid}')
        for c in data['concepts']:
            reservation = reservations.get(c['id'], {})
            require(reservation.get('approved') is True and reservation.get('identity_reason')
                    and reservation.get('discovery_evidence'), f'Unreviewed or unreserved identity: {c["id"]}')
            require(reservation.get('owner')==bid.removeprefix('research-batch-008-'),
                    f'Identity was reserved for another researcher: {c["id"]}')
            require(all(e.get('url','').startswith('https://') and e.get('locator')
                        for e in reservation['discovery_evidence']), f'Identity lacks source locators: {c["id"]}')
            existing = c['id'] in baseline
            require(reservation['inventory_status']==('existing' if existing else 'proposed_new'),
                    f'Novelty classification disagrees with baseline: {c["id"]}')
            if existing:
                base = baseline[c['id']]
                require(c['card_version']>base.get('latest_card_version',0),
                        f'New control bundle needs a newer version: {c["id"]}')
    stock = stock_module()
    result = stock.assemble(paths, baseline_path, decisions_path)
    require(len(result['concepts'])<=200, 'The bounded batch may contain at most 200 accepted cards')
    result['batch']['kind'] = 'combined_researched_candidate'
    result['batch']['approved_selection_sha256'] = selection_sha
    result['batch']['approved_selection_snapshot'] = approved
    result['batch']['assembler_dependency_sha256'] = sha(STOCK)
    result['batch']['scope'] = 'One bounded candidate; source audits and operational import are separate acceptance steps.'
    result['validation'].pop('canonical_content_sha256')
    result['validation']['canonical_content_sha256'] = stock.digest(result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, nargs='+', required=True)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--decisions', type=Path, required=True)
    parser.add_argument('--approved', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    stock = stock_module()
    previous = sha(args.output) if args.output.exists() else None
    try:
        result = assemble(args.inputs,args.baseline,args.decisions,args.approved)
        reverse = assemble(list(reversed(args.inputs)),args.baseline,args.decisions,args.approved)
        repeat = assemble(args.inputs+[args.inputs[0]],args.baseline,args.decisions,args.approved)
        require(result==reverse==repeat,'Repeated or reversed inputs change selected content')
        stock.atomic_json(args.output,result)
        stock.atomic_json(args.report,dict(status='passed',distinct_concepts=len(result['concepts']),
            canonical_content_sha256=result['validation']['canonical_content_sha256'],
            output_sha256=sha(args.output),passed=['approved_reservations','structural_validation',
                'source_and_target_resolution','reversed_input_order','repeated_import'],failed=[]))
    except (ValueError,stock.Rejected) as exc:
        stock.atomic_json(args.report,dict(status='quarantined',reason=str(exc),
            last_valid_output_retained=previous is not None and sha(args.output)==previous,
            prior_output_sha256=previous))
        raise SystemExit(1)


if __name__=='__main__':
    main()
