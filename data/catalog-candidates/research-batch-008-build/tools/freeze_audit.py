"""Freeze the initial complete draft and the fixed independent audit sample."""
import argparse
import json
import random
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from assemble import read, sha, stock_module

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    args = parser.parse_args()
    selection = read(ROOT/'selection-manifest.json')
    coverage = read(ROOT/'coverage-plan.json')
    targets = read(ROOT/'audit-target-plan.json')
    candidate = read(args.candidate)
    reserved = {c['id']: c for c in selection['accepted']}
    cards = {c['id']: c for c in candidate['concepts']}
    if set(cards) != set(reserved):
        raise ValueError('Freeze requires the complete reserved initial draft')
    if targets['selection_manifest_sha256'] != sha(ROOT/'selection-manifest.json'):
        raise ValueError('Target plan uses a different reservation snapshot')
    seed = coverage['audit']['seed']
    random_ids = random.Random(seed).sample(sorted(cid for cid in cards
        if reserved[cid]['inventory_status'] == 'proposed_new'), 20)
    risk_ids = [x['id'] for x in targets['targeted']]
    if len(set(random_ids)) != 20 or len(set(risk_ids)) != 20 or set(random_ids) & set(risk_ids):
        raise ValueError('Expected 20 random new cards and 20 disjoint targeted cards')
    if not set(risk_ids) <= set(cards):
        raise ValueError('A predefined risk identity is absent from the initial draft')
    frozen = ROOT/'frozen-initial'
    frozen.mkdir(exist_ok=False)
    files = {}

    def preserve(source, relative):
        destination = frozen/relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        files[str(relative)] = {'path': str(destination), 'sha256': sha(destination)}

    preserve(args.candidate, Path('catalog.json'))
    for name in ('selection-manifest.json', 'identity-decisions.json', 'audit-target-plan.json'):
        preserve(ROOT/name, Path(name))
    for owner in ('science', 'systems', 'culture'):
        for name in ('candidate.json', 'author-review.json', 'research-notes.md', 'approved-selection.json'):
            preserve(ROOT/'research'/owner/name, Path('research')/owner/name)
        for source in sorted((ROOT/'research'/owner).iterdir()):
            if source.is_file() and source.suffix in {'.json', '.md', '.pdf', '.html', '.png'}:
                relative = Path('research')/owner/source.name
                if str(relative) not in files:
                    preserve(source, relative)
    stock = stock_module()
    manifest = dict(schema_version=1, status='initial_draft_frozen',
        frozen_at=datetime.now(timezone.utc).isoformat(), files=files,
        baseline_index_sha256=sha(ROOT/'baseline-index.json'),
        initial_candidate_sha256=sha(frozen/'catalog.json'),
        canonical_content_sha256=candidate['validation']['canonical_content_sha256'],
        limits=['Initial snapshots and the fixed sample remain intact after repairs.'])
    stock.atomic_json(frozen/'manifest.json', manifest)
    risk_reasons = {x['id']: x['reason'] for x in targets['targeted']}
    sources = {s['id']: s for s in candidate['sources']}
    entries = []
    for stratum, ids in (('random_new', random_ids), ('targeted', risk_ids)):
        for cid in ids:
            card = cards[cid]
            source_ids = {e['source_id'] for e in card['evidence']}
            source_ids.update(sid for r in card['relations'] for sid in r['source_ids'])
            bundle = {'concept': card, 'sources': [sources[sid] for sid in sorted(source_ids)]}
            entries.append(dict(id=cid, owner=reserved[cid]['owner'], stratum=stratum,
                reason=risk_reasons.get(cid, 'Deterministic random sample of approved new identities.'),
                primary_domain=card['domains'][0], initial_card_version=card['card_version'],
                initial_card_sha256=stock.digest(card), initial_source_bundle_sha256=stock.digest(bundle),
                snapshot=bundle))
    sample = dict(schema_version=1, batch_id='research-batch-008', status='frozen_before_source_audit',
        initial_freeze_manifest_path=str(frozen/'manifest.json'),
        initial_freeze_manifest_sha256=sha(frozen/'manifest.json'),
        initial_candidate_path=str(frozen/'catalog.json'), initial_candidate_sha256=sha(frozen/'catalog.json'),
        baseline_path=str(ROOT/'baseline-index.json'), baseline_index_sha256=sha(ROOT/'baseline-index.json'),
        selection_manifest_sha256=sha(ROOT/'selection-manifest.json'), random_seed=seed,
        sampling_expression='random.Random(seed).sample(sorted(new_ids), 20)',
        random_ids=random_ids, targeted_ids=risk_ids,
        entries=entries, domain_coverage=sorted({e['primary_domain'] for e in entries}),
        fixed_sample_policy='Preserve IDs and initial snapshots through repairs, removals and rechecks.')
    stock.atomic_json(ROOT/'audit-sample.json', sample)
    for owner in ('science', 'systems', 'culture'):
        folder = ROOT/'audit'/owner
        folder.mkdir(parents=True, exist_ok=True)
        own = [e for e in entries if e['owner'] == owner]
        stock.atomic_json(folder/'assignment.json', dict(schema_version=1, assignment=owner,
            sample_path=str(ROOT/'audit-sample.json'), sample_manifest_sha256=sha(ROOT/'audit-sample.json'),
            initial_candidate_sha256=sample['initial_candidate_sha256'],
            baseline_path=sample['baseline_path'], baseline_index_sha256=sample['baseline_index_sha256'],
            entries=own))
    print(json.dumps(dict(status='frozen', sample_manifest_sha256=sha(ROOT/'audit-sample.json'),
        initial_candidate_sha256=sample['initial_candidate_sha256'],
        domains=len(sample['domain_coverage']), by_owner=dict(Counter(e['owner'] for e in entries))), indent=2))


if __name__ == '__main__':
    main()
