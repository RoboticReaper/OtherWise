"""Assess independent source and clarity audit coverage of a fixed sample."""
from collections import Counter

from assemble import STOCK


def assess(sample, cards, initial_reviews, rechecks):
    failures = []
    checks = Counter()

    def check(ok, category, detail):
        checks[category] += 1
        if not ok:
            failures.append({'category': category, 'detail': detail})

    entries = {e['id']: e for e in sample['sample']}
    current = {c['id']: c for c in cards}
    check(len(entries) == len(sample['sample']) == 40, 'fixed_sample', 'Forty distinct sampled cards')
    check(Counter(e['stratum'] for e in entries.values()) == {'random': 20, 'risk': 20},
          'fixed_strata', 'Twenty random and twenty risk cards')
    originals = {}
    for doc in initial_reviews:
        check(doc.get('authored_sampled_cards') is False, 'independent_reviewer', 'Initial review authorship')
        check(doc.get('draft_candidate_sha256') == sample['draft_candidate_sha256'],
              'frozen_draft_binding', 'Initial review uses the frozen candidate')
        for r in doc.get('reviews', []):
            check(r['id'] not in originals, 'one_initial_review', r['id'])
            originals[r['id']] = r
    check(set(originals) == set(entries), 'sample_coverage', 'All fixed sampled IDs reviewed exactly once')
    latest = {}
    for doc in rechecks:
        check(doc.get('authored_sampled_cards') is False, 'independent_reviewer', 'Repair recheck authorship')
        hashes = doc.get('current_input_sha256', {})
        check(bool(hashes) and all(isinstance(v, str) and len(v) == 64 for v in hashes.values()),
              'recheck_input_binding', 'Recheck records exact current input hashes')
        for r in doc.get('reviews', []):
            latest[r['id']] = r

    def inspected(record):
        passages = record.get('passages', [record])
        return bool(passages) and all(p.get('url', '').startswith('https://')
            and bool(p.get('locator')) and bool(p.get('inspection_mode')) for p in passages)

    initial_counts = Counter()
    for cid, e in entries.items():
        original = originals.get(cid)
        card = current.get(cid)
        check(bool(card), 'current_sample_exists', cid)
        if not original or not card:
            continue
        initial_counts[e['stratum']+':'+original['status']] += 1
        check(original.get('stratum') == e['stratum']
              and original.get('card_version') == e['card']['card_version'], 'initial_sample_binding', cid)
        changed = card != e['card']
        needs_recheck = changed or original.get('status') != 'verified' or any(
            f.get('severity') == 'material' for f in original.get('findings', []))
        review = latest.get(cid) if needs_recheck else original
        check(bool(review), 'required_recheck', cid)
        if not review:
            continue
        if needs_recheck:
            check(review.get('current_card_sha256') == STOCK.digest(card), 'current_card_hash', cid)
        check(review.get('status') == 'verified' and review.get('card_version') == card['card_version'],
              'final_review_status_and_version', cid)
        clarity = review.get('clarity', {})
        check(all(clarity.get(k) is True for k in ('meaning_clear', 'concrete_takeaway',
            'qualification_preserved', 'scope_appropriate_wording')), 'short_card_clarity', cid)
        claims = review.get('claims', [])
        check(bool(claims) and all(c.get('supported') is True and inspected(c) for c in claims),
              'substantive_claim_inspection', cid)
        expected = Counter((r['target_id'], r['type'], r['assertion']) for r in card['relations'])
        actual = Counter((r.get('target_id'), r.get('type'), r.get('assertion')) for r in review.get('relations', []))
        check(expected == actual, 'complete_relationship_review', cid)
        check(all(r.get('supported') is True and inspected(r) for r in review.get('relations', [])),
              'relationship_passage_inspection', cid)
        check(not any(f.get('severity') == 'material' for f in review.get('findings', [])),
              'resolved_material_findings', cid)
    return {'status': 'failed' if failures else 'passed', 'total_checks': sum(checks.values()),
            'checks_by_category': dict(checks), 'initial_outcomes': dict(initial_counts),
            'fixed_sample_count': len(entries), 'failures': failures,
            'limitation': 'Audit coverage and bindings do not certify unsampled facts or human interest.'}
