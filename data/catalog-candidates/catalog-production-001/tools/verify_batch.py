"""Verify production contracts, preservation and actual author-review coverage.

This checks local evidence integrity. Independent source inspection supplies the
factual/clarity acceptance gate; numerical passes cannot replace it.
"""
import argparse
import copy
import itertools
import json
from collections import Counter
from pathlib import Path

from assemble import read, sha, STOCK

PRODUCTION = Path(__file__).resolve().parents[1]
PROJECT = PRODUCTION.parents[2]


def verify(batch_dir, candidate_path, report_path):
    baseline_path = PRODUCTION/'baseline-index.json'
    baseline = read(baseline_path)
    manifest = read(PRODUCTION/'baseline-manifest.json')
    selection = read(batch_dir/'selection-manifest.json')
    decisions = read(batch_dir/'identity-decisions.json')
    candidate = read(candidate_path)
    checks = Counter()
    failures = []

    def check(ok, category, detail):
        checks[category] += 1
        if not ok: failures.append(dict(category=category, detail=detail))

    check(sha(baseline_path) == manifest['baseline_index_sha256'], 'frozen_baseline', 'Baseline fingerprint')
    for path, expected in {**manifest['protected_inputs'], **manifest['protected_completed_batch_files']}.items():
        check(sha(PROJECT/path) == expected['sha256'], 'legacy_preservation', path)
    check(sha(PROJECT/manifest['completed_batch_manifest']['path']) == manifest['completed_batch_manifest']['sha256'],
          'legacy_preservation', 'Completed prior batch manifest')
    check(candidate['batch']['approved_selection_snapshot'] == selection, 'selection_snapshot', 'Full reservations')
    check(candidate['batch']['approved_selection_sha256'] == sha(batch_dir/'selection-manifest.json'),
          'selection_hash', 'Approved selection')
    check(candidate['batch']['identity_decisions'] == decisions, 'identity_decisions', 'Full identity decisions')
    check(candidate['batch']['identity_decisions_sha256'] == sha(batch_dir/'identity-decisions.json'),
          'identity_decisions', 'Decision hash')
    canonical = copy.deepcopy(candidate)
    digest = canonical['validation'].pop('canonical_content_sha256')
    check(STOCK.digest(canonical) == digest, 'canonical_digest', 'Assembled candidate')
    cards = candidate['concepts']
    ids = {c['id'] for c in cards}
    reservations = {r['id']: r for r in selection['accepted']}
    check(len(ids) == len(cards) == len(reservations) <= 200, 'bounded_identity_count', 'Distinct first cards')
    check(ids == set(reservations), 'complete_reservations', 'Reserved/emitted IDs')
    check(not ids & set(selection.get('prior_accepted_ids', [])), 'production_deduplication', 'Prior accepted production IDs')
    known = set(baseline['concepts']) | ids
    sources = {s['id']: s for s in candidate['sources']}
    check(len(sources) == len(candidate['sources']), 'source_ids', 'Unique scoped references')
    aliases = {}
    distinct_pairs = {frozenset(pair) for d in decisions.get('distinctness', [])
                      if d.get('reviewed') and d.get('evidence')
                      for pair in itertools.combinations(d['member_ids'], 2)}
    baseline_aliases = {}
    for cid, c in baseline['concepts'].items():
        for a in [c['label'], *c.get('aliases', [])]:
            baseline_aliases.setdefault(STOCK.normalize_alias(a), set()).add(cid)
    reviews = {}
    raw_by_id = {}
    for entry in candidate['batch']['input_provenance']:
        owner = entry['batch_id'].rsplit('-', 1)[1]
        directory = batch_dir/'research'/owner
        raw = read(directory/'candidate.json')
        check(sha(directory/'candidate.json') == entry['input_sha256']
              and raw == entry['candidate_snapshot'], 'full_raw_snapshot', owner)
        author = read(directory/'author-review.json')
        reviews.update(author['reviews'])
        raw_by_id.update({c['id']: c for c in raw['concepts']})
        check((directory/'sources-inspected.json').exists(), 'source_inspection_record', owner)
        check((directory/'source-word-budgets.json').exists(), 'source_budget_record', owner)
    for c in cards:
        cid = c['id']; base = baseline['concepts'][cid]
        check(not base.get('candidate_records') and not base.get('latest_card'), 'first_card_only', cid)
        check(1 <= len(c['card'].split()) <= 25, 'short_card_word_budget', cid)
        check(c['original_description'] == base['original_description'], 'original_import_wording', cid)
        check(c['imported_records'] == base.get('inventory_records', []), 'full_raw_imports', cid)
        for a in [c['label'], *c['aliases']]:
            key = STOCK.normalize_alias(a)
            aliases.setdefault(key, set()).add(cid)
            for other in baseline_aliases.get(key, set())-{cid}:
                check(frozenset((cid, other)) in distinct_pairs, 'reviewed_shared_meanings', f'{a}: {cid}, {other}')
        check(bool(c['evidence']), 'card_evidence', cid)
        for e in c['evidence']:
            check(e['source_id'] in sources and bool(e['locator']), 'evidence_resolution', cid)
        for r in c['relations']:
            check(r['target_id'] in known and r['target_id'] != cid, 'relationship_resolution', cid)
            check(bool(r['source_ids']) and set(r['source_ids']) <= set(sources), 'relationship_premises', cid)
        author = reviews.get(cid, {})
        check(author.get('outcome') == 'author_checked' and author.get('claims_supported') is True
              and author.get('clarity_checked') is True and author.get('relations_checked') is True,
              'author_source_review', cid)
        check(author.get('card_version') == c['card_version'] and author.get('word_count') == len(c['card'].split()),
              'author_review_version', cid)
        check(bool(author.get('inspected_locators')), 'author_inspected_passages', cid)
        provenance = candidate['batch']['concept_provenance'][cid]
        check(len(provenance) == 1 and provenance[0]['original_record'] == raw_by_id[cid], 'exact_card_lineage', cid)
    for alias, members in aliases.items():
        for pair in itertools.combinations(sorted(members), 2):
            check(frozenset(pair) in distinct_pairs, 'reviewed_cross_card_meanings', f'{alias}: {pair}')
    initial_manifest = batch_dir/'frozen-initial/manifest.json'
    if initial_manifest.exists():
        for name, info in read(initial_manifest)['files'].items():
            check(sha(batch_dir/'frozen-initial'/name) == info['sha256'], 'frozen_initial_evidence', name)
    fine = [c for c in cards if c['scope'] in ('idea', 'facet_or_application')]
    parent_types = {'broader_topic', 'facet_of', 'application_of'}
    metrics = dict(cards=len(cards), first_descriptions=len(cards), new_identities=len(ids-set(baseline['concepts'])),
        legacy_rewritten=0, domains=dict(Counter(c['domains'][0] for c in cards)),
        scopes=dict(Counter(c['scope'] for c in cards)),
        named_subjects=sum(c['entity_kind'] == 'named_subject' for c in cards),
        minimum_body_words=min((len(c['card'].split()) for c in cards), default=0),
        maximum_body_words=max((len(c['card'].split()) for c in cards), default=0),
        fine_cards=len(fine), fine_with_parent=sum(any(r['type'] in parent_types for r in c['relations']) for c in fine),
        fine_with_source_asserted_parent=sum(any(r['type'] in parent_types and r['assertion'] == 'source_asserted'
            for r in c['relations']) for c in fine), references=len(sources), relations=sum(len(c['relations']) for c in cards))
    result = dict(schema_version=1, status='failed' if failures else 'passed', candidate_sha256=sha(candidate_path),
        total_checks=sum(checks.values()), checks_by_category=dict(checks), counts=metrics, failures=failures,
        independent_source_audit='Separate mandatory acceptance record; this numerical check does not certify facts.')
    STOCK.atomic_json(report_path, result)
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--batch-dir', type=Path, required=True)
    p.add_argument('--candidate', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    args = p.parse_args()
    result = verify(args.batch_dir, args.candidate, args.report)
    print(json.dumps({k: result[k] for k in ('status', 'total_checks', 'counts', 'failures')}, indent=2))
    raise SystemExit(bool(result['failures']))
