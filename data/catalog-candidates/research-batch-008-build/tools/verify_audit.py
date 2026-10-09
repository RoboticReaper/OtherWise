"""Bind the fixed independent audit and repair rechecks to the final candidate.

This verifies evidence integrity and coverage, not the truth of an uninspected claim.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from assemble import read, sha, stock_module

ROOT = Path(__file__).resolve().parents[1]
OWNERS = ('science', 'systems', 'culture')


def bundle(document, cid):
    card = next(c for c in document['concepts'] if c['id'] == cid)
    sources = {s['id']: s for s in document['sources']}
    used = {e['source_id'] for e in card['evidence']}
    used.update(s for r in card['relations'] for s in r['source_ids'])
    return {'concept': card, 'sources': [sources[s] for s in sorted(used)]}


def relation_checks(record):
    checks = record.get('relation_checks', record.get('relationship_checks', []))
    return [c for c in checks if c.get('outcome', c.get('status')) != 'not_applicable']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    stock = stock_module()
    failures, checks = [], Counter()

    def check(condition, category, detail):
        checks[category] += 1
        if not condition:
            failures.append({'category': category, 'detail': detail})

    candidate = read(args.candidate)
    final_cards = {c['id']: c for c in candidate['concepts']}
    sample = read(ROOT/'audit-sample.json')
    frozen_manifest = read(ROOT/'frozen-initial/manifest.json')
    initial = read(ROOT/'frozen-initial/catalog.json')
    sample_entries = {e['id']: e for e in sample['entries']}
    check(len(sample_entries) == 40, 'fixed_sample', 'Expected 40 fixed sampled IDs')
    check(len(sample['random_ids']) == len(sample['targeted_ids']) == 20
          and not set(sample['random_ids']) & set(sample['targeted_ids']),
          'fixed_sample', 'Expected disjoint strata of 20')
    check(sha(ROOT/'frozen-initial/manifest.json') == sample['initial_freeze_manifest_sha256'],
          'frozen_evidence', 'Initial freeze manifest hash changed')
    for name, entry in frozen_manifest['files'].items():
        check(sha(entry['path']) == entry['sha256'], 'frozen_evidence', name)

    initial_records, supplementary, rechecks = {}, {}, {}
    audit_paths, changes, author_coverage = {}, [], {}
    budget_pages = {}
    for owner in OWNERS:
        raw_path = ROOT/'research'/owner/'candidate.json'
        raw = read(raw_path)
        before = read(ROOT/'frozen-initial/research'/owner/'candidate.json')
        author_path = ROOT/'research'/owner/'author-review.json'
        author = read(author_path)
        raw_ids = {c['id'] for c in raw['concepts']}
        check(set(author['reviews']) == raw_ids, 'author_coverage', owner)
        check(author['candidate_sha256'] == sha(raw_path), 'author_snapshot', owner)
        author_coverage[owner] = len(raw_ids)
        for card in raw['concepts']:
            cid = card['id']
            review = author['reviews'].get(cid, {})
            check(review.get('word_count') == len(card['card'].split()),
                  'author_word_count', cid)
            if 'card_version' in review:
                check(review['card_version'] == card['card_version'], 'author_version', cid)
            old_bundle, new_bundle = bundle(before, cid), bundle(raw, cid)
            changed = old_bundle != new_bundle
            if changed:
                check(card['card_version'] > old_bundle['concept']['card_version'],
                      'repair_version', cid)
                changes.append({'id': cid, 'owner': owner,
                    'before_version': old_bundle['concept']['card_version'],
                    'after_version': card['card_version'],
                    'body_changed': old_bundle['concept']['card'] != card['card'],
                    'relations_changed': old_bundle['concept']['relations'] != card['relations'],
                    'relationship_structure_changed':
                        [{k: r[k] for k in ('target_id', 'type', 'assertion', 'source_ids')}
                         for r in old_bundle['concept']['relations']] !=
                        [{k: r[k] for k in ('target_id', 'type', 'assertion', 'source_ids')}
                         for r in card['relations']],
                    'initial_raw_bundle_sha256': stock.digest(old_bundle),
                    'final_raw_card_sha256': stock.digest(card),
                    'final_raw_bundle_sha256': stock.digest(new_bundle)})
            provenance = candidate['batch']['concept_provenance'][cid][0]
            check(provenance['original_record'] == card
                  and provenance['input_sha256'] == sha(raw_path), 'final_raw_binding', cid)

        if owner == 'science':
            budgets = read(ROOT/'research/science/source-word-budgets.json')['pages']
        elif owner == 'systems':
            budgets = read(ROOT/'research/systems/word-budget-review.json')['by_url']
        else:
            raw_sources = {s['id']: s['url'] for s in raw['sources']}
            budgets = {raw_sources[sid]: details for sid, details
                       in raw['batch']['source_summary_budgets'].items()}
        if isinstance(budgets, list):
            budgets = {b.get('url', b.get('source_url')): b for b in budgets}
        source_urls = {s['id']: s['url'] for s in raw['sources']}
        prose_words = Counter()
        for card in raw['concepts']:
            body_sources = {e['source_id'] for e in card['evidence']}
            used_sources = body_sources | {s for r in card['relations'] for s in r['source_ids']}
            for sid in used_sources:
                prose = [card['card'], card['learning_takeaway']] if sid in body_sources else []
                prose += [e.get('note', '') for e in card['evidence'] if e['source_id'] == sid]
                prose += [r.get('note', '') for r in card['relations'] if sid in r['source_ids']]
                prose_words[source_urls[sid]] += sum(len(text.split()) for text in prose)
        # Retained unused discovery references derive no card prose. A companion
        # text/HTML URL can share one work's budget, but cannot reset that budget.
        check(set(prose_words) <= set(budgets), 'source_budget_coverage', owner)
        actual_source_records = {s['id']: s for s in raw['sources']}
        for url, details in budgets.items():
            total = details.get('total_derived_words', details.get('attributed_generated_words',
                    details.get('total_words', details.get('derived_words'))))
            check(isinstance(total, int) and total <= 200, 'source_word_budget', str(url))
            check(isinstance(total, int) and total >= prose_words[url],
                  'source_budget_recount', str(url) + ': candidate prose lower bound')
            if url not in source_urls.values():
                source = actual_source_records.get(details.get('source_id'), {})
                primary = details.get('same_work_primary_url')
                primary_details = budgets.get(primary, {})
                primary_total = primary_details.get('attributed_generated_words')
                supplemental_urls = {s['url'] for s in source.get('supplemental_inspections', [])}
                check(details.get('budget_not_reset') is True and primary == source.get('url')
                      and url in supplemental_urls and total == primary_total,
                      'same_work_companion_budget', str(url))
            check(url not in budget_pages, 'source_word_budget', 'Duplicate URL: ' + str(url))
            budget_pages[url] = total

        review_path = ROOT/'audit'/owner/'initial-review.json'
        initial_review = read(review_path)
        check(initial_review['sample_manifest_sha256'] == sha(ROOT/'audit-sample.json'),
              'fixed_sample_binding', owner)
        check(initial_review['initial_candidate_sha256'] == sample['initial_candidate_sha256'],
              'initial_candidate_binding', owner)
        check(initial_review['auditor_task_identity'] == '/root/batch008_audit_' + owner,
              'separate_reviewer', owner)
        owner_samples = {e['id'] for e in sample['entries'] if e['owner'] == owner}
        check(set(initial_review['records']) == owner_samples, 'fixed_sample_coverage', owner)
        initial_records.update(initial_review['records'])
        supplementary.update(initial_review.get('supplementary_records', {}))
        recheck_path = ROOT/'audit'/owner/'recheck-001.json'
        recheck = read(recheck_path)
        check(recheck['auditor_task_identity'] == initial_review['auditor_task_identity'],
              'separate_reviewer', owner + ': recheck')
        check(recheck['initial_review_sha256'] == sha(review_path),
              'preserved_initial_review', owner)
        check(sha(recheck['repair_lineage_path']) == recheck['repair_lineage_sha256'],
              'repair_lineage_binding', owner)
        check(recheck['sample_manifest_sha256'] == sha(ROOT/'audit-sample.json'),
              'fixed_sample_binding', owner + ': recheck')
        expected_sha = recheck.get('repaired_candidate_sha256',
                       recheck.get('repaired_science_candidate_sha256',
                       recheck.get('repaired_systems_candidate_sha256')))
        check(expected_sha == sha(raw_path), 'rechecked_input', owner)
        rechecks.update(recheck['records'])
        rechecks.update(recheck.get('supplementary_records', {}))
        audit_paths[owner] = {'author_review_sha256': sha(author_path),
            'final_input_sha256': sha(raw_path), 'initial_review_sha256': sha(review_path),
            'recheck_sha256': sha(recheck_path)}

    check(set(initial_records) == set(sample_entries), 'fixed_sample_coverage', 'All 40 fixed IDs')
    check(not set(supplementary) & set(initial_records), 'supplementary_coverage', 'Overlap with fixed sample')
    check(set(rechecks) == {c['id'] for c in changes},
          'repair_recheck_coverage', 'Every changed raw bundle must be independently rechecked')
    initial_outcomes = {'random_new': Counter(), 'targeted': Counter()}
    final_outcomes = {'random_new': Counter(), 'targeted': Counter()}
    record_bindings, finding_counts = [], Counter()
    initial_relation_count, initial_claim_count, supplementary_relations = 0, 0, 0
    for cid, record in {**initial_records, **supplementary}.items():
        entry = sample_entries.get(cid)
        owner = entry['owner'] if entry else 'systems'
        raw = read(ROOT/'research'/owner/'candidate.json')
        before = read(ROOT/'frozen-initial/research'/owner/'candidate.json')
        initial_bundle = bundle(initial, cid)
        final_bundle = bundle(raw, cid)
        check(record['initial_card_sha256'] == stock.digest(initial_bundle['concept'])
              and record['initial_source_bundle_sha256'] == stock.digest(initial_bundle),
              'initial_snapshot_binding', cid)
        if entry:
            check(record['stratum'] == entry['stratum'], 'fixed_sample_stratum', cid)
            initial_outcomes[entry['stratum']][record['outcome']] += 1
            initial_relation_count += len(relation_checks(record))
            initial_claim_count += len(record['substantive_claim_checks'])
        else:
            supplementary_relations += len(relation_checks(record))
        check(len(relation_checks(record)) == len(initial_bundle['concept']['relations']),
              'all_initial_relations_checked', cid)
        check(bool(record['source_inspections']), 'actual_source_inspection', cid)
        finding_counts['fixed' if entry else 'supplementary'] += len(record['findings'])
        if cid in rechecks:
            result = rechecks[cid]
            check(result['outcome'] == 'verified' and not result.get('new_findings', [])
                  and not result.get('findings', []) and not result.get('unresolved_findings', []),
                  'repair_verified', cid)
            resolutions = result['finding_resolutions']
            check(len(resolutions) == len(record['findings']) and all(
                  f.get('status', f.get('outcome', f.get('resolution'))) == 'resolved'
                  for f in resolutions), 'every_initial_finding_resolved', cid)
            check(result['repaired_card_sha256'] == stock.digest(final_bundle['concept'])
                  and result['repaired_source_bundle_sha256'] == stock.digest(final_bundle),
                  'repaired_snapshot_binding', cid)
            version = result.get('card_version', result.get('current_card_version',
                                 result.get('repaired_card_version')))
            check(version == final_bundle['concept']['card_version'], 'recheck_version', cid)
            check(len(relation_checks(result)) == len(final_bundle['concept']['relations']),
                  'all_repaired_relations_checked', cid)
            check(all(c.get('outcome') == 'verified' for c in relation_checks(result)),
                  'all_repaired_relations_verified', cid)
            check(bool(result['source_inspections']), 'actual_source_reinspection', cid)
            check(all(c.get('outcome') == 'verified' for c in result['substantive_claim_checks']),
                  'repaired_claims_verified', cid)
            final_outcome = result['outcome']
        else:
            check(record['outcome'] == 'verified' and not record['findings'],
                  'unchanged_verified', cid)
            check(bundle(before, cid) == final_bundle, 'unchanged_raw_bundle', cid)
            final_outcome = record['outcome']
        if entry:
            final_outcomes[entry['stratum']][final_outcome] += 1
        record_bindings.append({'id': cid, 'owner': owner,
            'stratum': record['stratum'], 'initial_outcome': record['outcome'],
            'final_outcome': final_outcome, 'rechecked': cid in rechecks,
            'initial_namespaced_card_sha256': stock.digest(initial_bundle['concept']),
            'final_raw_card_sha256': stock.digest(final_bundle['concept']),
            'final_raw_bundle_sha256': stock.digest(final_bundle),
            'final_namespaced_card_sha256': stock.digest(final_cards[cid]),
            'final_namespaced_bundle_sha256': stock.digest(bundle(candidate, cid))})

    report = {'schema_version': 1, 'status': 'failed' if failures else 'passed',
        'checked_at': datetime.now(timezone.utc).isoformat(),
        'candidate_sha256': sha(args.candidate), 'audit_sample_sha256': sha(ROOT/'audit-sample.json'),
        'initial_candidate_sha256': sample['initial_candidate_sha256'],
        'checks_by_category': dict(checks), 'total_checks': sum(checks.values()),
        'author_review_coverage': author_coverage, 'independent_fixed_sample_cards': len(initial_records),
        'initial_stratum_outcomes': {s: dict(v) for s, v in initial_outcomes.items()},
        'final_stratum_outcomes': {s: dict(v) for s, v in final_outcomes.items()},
        'fixed_initial_claim_checks': initial_claim_count,
        'fixed_initial_relation_checks': initial_relation_count,
        'supplementary_cards': len(supplementary), 'supplementary_initial_relation_checks': supplementary_relations,
        'initial_finding_counts': dict(finding_counts), 'repaired_bundles': len(changes),
        'body_changes': sum(c['body_changed'] for c in changes),
        'relationship_changes': sum(c['relations_changed'] for c in changes),
        'relationship_structure_changes': sum(c['relationship_structure_changed'] for c in changes),
        'repair_changes': changes, 'record_bindings': record_bindings,
        'evidence_hashes': audit_paths, 'source_budget_pages': len(budget_pages),
        'maximum_attributed_generated_words_per_source': max(budget_pages.values(), default=0),
        'failures': failures,
        'limits': ['Evidence binding and fixed sample coverage do not establish truth for unsampled claims.',
                   'The targeted and supplementary checks are not random error-rate estimates.',
                   'PDF visual-access failures are recorded in the underlying audits; successful text inspections remain separate.',
                   'Catalog quality checks do not establish human interestingness or retained-interest expansion.',
                   'Actual platform token usage and cost are unavailable.']}
    stock.atomic_json(args.report, report)
    print({k: report[k] for k in ('status', 'total_checks', 'initial_stratum_outcomes',
        'final_stratum_outcomes', 'supplementary_cards', 'repaired_bundles', 'body_changes',
        'relationship_changes', 'maximum_attributed_generated_words_per_source', 'failures')})
    raise SystemExit(bool(failures))


if __name__ == '__main__':
    main()
