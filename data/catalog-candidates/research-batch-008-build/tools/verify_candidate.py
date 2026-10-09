"""Check batch 008's full candidate against its frozen inputs and reservations.

These local checks verify contracts and provenance, not source truth.
"""
import argparse
import copy
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from assemble import sha, read, stock_module

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    failures, checks = [], Counter()

    def check(condition, category, detail):
        checks[category] += 1
        if not condition:
            failures.append({'category': category, 'detail': detail})

    candidate = read(args.candidate)
    manifest = read(ROOT/'baseline-manifest.json')
    baseline = read(ROOT/'baseline-index.json')
    selection = read(ROOT/'selection-manifest.json')
    reservations = {r['id']: r for r in selection['accepted']}
    decisions = read(ROOT/'identity-decisions.json')
    drift_path = ROOT/'external-workspace-changes.json'
    drift_records = read(drift_path)['changes'] if drift_path.exists() else []
    inspected_drift = {d['path']: d for d in drift_records}
    observed_drift = []
    allowed_pairs = {frozenset(d['member_ids']) for d in decisions['distinctness']
                     if d.get('reviewed') is True and d.get('evidence')}
    pinned = baseline['concepts']
    check(sha(ROOT/'baseline-index.json') == manifest['baseline_index_sha256'],
          'pinned_inputs', 'Working baseline changed')
    for path, expected in manifest['inputs_sha256'].items():
        actual = sha(PROJECT/path)
        if actual != expected and path in inspected_drift:
            d = inspected_drift[path]
            accepted = (d.get('accepted_for_frozen_catalog_validation') is True
                and d['expected_pinned_sha256'] == expected
                and d['observed_sha256'] == actual
                and sha(PROJECT/d['pinned_original_snapshot']) == expected
                and sha(PROJECT/d['patch_path']) == d['patch_sha256'])
            check(accepted, 'inspected_external_drift', path)
            if accepted:
                observed_drift.append(d)
        else:
            check(actual == expected, 'pinned_inputs', path)
    for files in selection['input_snapshots'].values():
        for entry in files.values():
            check(sha(PROJECT/entry['path']) == entry['sha256'],
                  'selection_snapshots', entry['path'])
    check(candidate['batch']['approved_selection_snapshot'] == selection,
          'selection_provenance', 'Full reservation snapshot differs')
    check(candidate['batch']['approved_selection_sha256'] == sha(ROOT/'selection-manifest.json'),
          'selection_provenance', 'Reservation hash differs')
    check(candidate['batch']['baseline']['sha256'] == manifest['baseline_index_sha256'],
          'baseline_provenance', 'Candidate baseline hash differs')
    check(candidate['batch']['identity_decisions'] == decisions,
          'identity_provenance', 'Full decisions snapshot differs')
    check(candidate['batch']['identity_decisions_sha256'] == sha(ROOT/'identity-decisions.json'),
          'identity_provenance', 'Decisions hash differs')
    canonical = copy.deepcopy(candidate)
    content_sha = canonical['validation'].pop('canonical_content_sha256')
    check(stock_module().digest(canonical) == content_sha,
          'canonical_digest', 'Candidate content hash differs')

    cards = candidate['concepts']
    ids = {c['id'] for c in cards}
    check(len(ids) == len(cards) <= 200, 'bounded_unique_ids', 'Duplicate IDs or card-limit breach')
    check(ids <= set(reservations), 'reservations', 'Unreserved IDs emitted')
    check(len(ids) == len(reservations), 'selection_completeness',
          'Some reserved subjects were removed; report partial acceptance')
    known = ids | set(pinned)
    source_ids = {s['id'] for s in candidate['sources']}
    check(len(source_ids) == len(candidate['sources']), 'source_resolution', 'Duplicate scoped source IDs')
    aliases = defaultdict(set)
    for c in cards:
        cid = c['id']
        r = reservations[cid]
        check(30 <= len(c['card'].split()) <= 50, 'word_budget', cid)
        check(c['scope'] == r['scope'] and c['entity_kind'] == r['entity_kind'],
              'reserved_subject', cid + ': scope or entity kind differs')
        check(c['domains'][0] == r['primary_domain'], 'domain_ownership', cid)
        check(c['card_version'] >= r['required_card_version'], 'monotonic_versions', cid)
        for alias in [c['label'], *c['aliases']]:
            key = re.sub(r'[\s_\-\u2010-\u2015]+', ' ', alias.strip().casefold()).strip()
            aliases[key].add(cid)
            for other in set(baseline['aliases'].get(key, [])) - {cid}:
                check(frozenset((cid, other)) in allowed_pairs,
                      'baseline_alias_meanings', f'{key}: {cid}, {other}')
        for e in c['evidence']:
            check(e['source_id'] in source_ids, 'source_resolution', cid)
        for relation in c['relations']:
            check(relation['target_id'] in known and relation['target_id'] != cid,
                  'target_resolution', cid + ': ' + relation['target_id'])
            check(bool(relation['source_ids']) and set(relation['source_ids']) <= source_ids,
                  'relation_references', cid + ': ' + relation['target_id'])
        provenance = candidate['batch']['concept_provenance'][cid]
        check(len(provenance) == 1, 'card_snapshot', cid + ': multiple unselected records')
        original = provenance[0]['original_record']
        check(original['card'] == c['card'] and original['card_version'] == c['card_version'],
              'card_snapshot', cid)
        if cid in pinned:
            check(c['original_description'] == pinned[cid]['original_description'],
                  'original_wording', cid)
            for raw in pinned[cid].get('inventory_records', []):
                check(raw in c['imported_records'], 'raw_imported_records', cid)
    for alias, members in aliases.items():
        ordered = sorted(members)
        for i, cid in enumerate(ordered):
            for other in ordered[i+1:]:
                check(frozenset((cid, other)) in allowed_pairs,
                      'cross_card_alias_meanings', f'{alias}: {cid}, {other}')

    for entry in candidate['batch']['input_provenance']:
        owner = entry['batch_id'].removeprefix('research-batch-008-')
        path = ROOT/'research'/owner/'candidate.json'
        check(entry['candidate_snapshot'] == read(path) and entry['input_sha256'] == sha(path),
              'full_source_bundle_snapshot', owner)
        check(entry['selected'] is True, 'full_source_bundle_snapshot', owner + ': not selected')
        snapshot = entry['candidate_snapshot']
        controls = snapshot['batch']['control_version_decisions']
        if isinstance(controls, list):
            controls = {d['id']: d for d in controls}
        control_ids = {c['id'] for c in snapshot['concepts'] if c['id'] in pinned}
        check(set(controls) == control_ids, 'control_history_coverage', owner)
        for cid, decision in controls.items():
            prior_records = decision['prior_full_records']
            expected_records = pinned[cid].get('candidate_records', [])
            check(len(prior_records) == len(expected_records), 'full_prior_records', cid)
            for i, prior in enumerate(prior_records):
                if i >= len(expected_records):
                    continue
                expected = expected_records[i]
                if 'record' in prior:
                    retained = prior['record'] == expected['record']
                else:
                    # An exact pointer into the already hash-checked full baseline is
                    # valid retention; a field named prior_full_records need not inline it.
                    pointer = str((ROOT/'baseline-index.json').relative_to(PROJECT))
                    pointer += f'#/concepts/{cid}/candidate_records/{i}/record'
                    retained = (prior.get('full_record_pointer') == pointer
                                and prior.get('card_version') == expected['record']['card_version'])
                check(retained and prior.get('batch_id') == expected['batch_id']
                      and prior.get('batch_revision') == expected.get('batch_revision'),
                      'full_prior_record_resolution', cid + ': ' + str(i))
                if prior.get('source_bundle_path'):
                    check(sha(PROJECT/prior['source_bundle_path']) == prior['source_bundle_sha256'],
                          'prior_source_bundles', cid + ': ' + prior['source_bundle_path'])
    fine = [c for c in cards if c['scope'] in ('idea', 'facet_or_application')]
    parent_types = {'broader_topic', 'facet_of', 'application_of'}
    counts = {
        'cards': len(cards), 'new_identities': len(ids-set(pinned)),
        'existing_controls': len(ids & set(pinned)),
        'new_fine_scope_subjects': sum(c['id'] not in pinned for c in fine),
        'named_subjects': sum(c['entity_kind'] == 'named_subject' for c in cards),
        'fine_cards': len(fine),
        'fine_with_parent_application': sum(any(r['type'] in parent_types for r in c['relations']) for c in fine),
        'fine_with_source_asserted_parent_application': sum(any(r['type'] in parent_types and r['assertion'] == 'source_asserted' for r in c['relations']) for c in fine),
        'sources': len(source_ids), 'relations': sum(len(c['relations']) for c in cards),
        'domains': dict(Counter(c['domains'][0] for c in cards)),
        'scopes': dict(Counter(c['scope'] for c in cards)),
    }
    status = 'failed' if failures else ('passed_with_recorded_external_drift' if observed_drift else 'passed')
    report = dict(schema_version=1, status=status,
                  checked_at=datetime.now(timezone.utc).isoformat(),
                  candidate_sha256=sha(args.candidate), canonical_content_sha256=content_sha,
                  checks_by_category=dict(checks), total_checks=sum(checks.values()),
                  counts=counts, failures=failures, external_workspace_drift=observed_drift,
                  limits=['Local checks verify structure and provenance; source truth requires separate inspection.'])
    stock_module().atomic_json(args.report, report)
    print(json.dumps({k: report[k] for k in ('status', 'total_checks', 'counts', 'failures')}, indent=2))
    raise SystemExit(bool(failures))


if __name__ == '__main__':
    main()
