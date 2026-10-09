"""Read-only catalog validation, with a report confined to the owned shard."""
import collections
import datetime
import hashlib
import importlib.util
import json
import pathlib
import sys

sys.dont_write_bytecode = True
ROOT = pathlib.Path('data/catalog-candidates/catalog-production-001')
OUT = ROOT / 'batch-009/research/science'
spec = importlib.util.spec_from_file_location('production_combiner', ROOT / 'tools/production_combiner.py')
combiner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(combiner)
combiner.PILOT_BATCHES = {'research-batch-009-science'}


def read(path):
    return combiner.strict_load(path)[0]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


c = read(OUT / 'candidate.json')
combiner.validate_candidate(c, OUT / 'candidate.json')
b = read(ROOT / 'baseline-index.json')
a = read(OUT / 'approved-selection.json')
p = read(OUT / 'proposals.json')
eligible = {x['id'] for x in read(OUT / 'eligible-identities.json')['concepts']}
reviews = read(OUT / 'author-review.json')
inspections = read(OUT / 'sources-inspected.json')
ledger = read(OUT / 'source-word-budgets.json')
assert sha(OUT / 'proposals.json') == '456278abe2b9908110d0edaa4de2a6d5bbf805d4c20b68c84fadbd00ff328fe8'
assert c['batch']['baseline_index_sha256'] == a['baseline_index_sha256'] == sha(ROOT / 'baseline-index.json')
assert c['batch']['global_selection_manifest_sha256'] == a['global_selection_manifest_sha256'] == '4802e1cc037ce1b0d47479801236fce29b3c759b466c8f1011b3a4c3438b86b8'
assert c['batch']['approved_selection_sha256'] == sha(OUT / 'approved-selection.json')
assert c['batch']['selection_input_snapshots']['proposals']['sha256'] == sha(OUT / 'proposals.json')
accepted = {x['id']: x for x in a['accepted']}
ids = {x['id'] for x in c['concepts']}
assert len(c['concepts']) == len(ids) == len(accepted) == 70
assert ids == set(accepted) == {x['id'] for x in p['proposals']}
assert ids <= eligible
assert not ids & {'Q3001783', 'Q624580', 'Q175751'}
source_map = {x['id']: x for x in c['sources']}
inspection_map = {x['id']: x for x in inspections['sources']}
assert len(source_map) == len(c['sources']) == 74
assert len(inspection_map) == len(inspections['sources']) == 82
assert set(reviews['reviews']) == ids
assert reviews['candidate_sha256'] == sha(OUT / 'candidate.json')
used_sources = set()
fine = []
parents = []
for x in c['concepts']:
    cid = x['id']
    original = b['concepts'][cid]
    reserved = accepted[cid]
    assert not original.get('candidate_records') and not original.get('latest_card')
    assert x['original_description'] == original['original_description']
    assert x['imported_records'] == original.get('inventory_records', [])
    assert x['card_version'] == 1
    assert x['label'] == ('pH' if cid == 'Q40936' else reserved['label'])
    assert x['aliases'] == reserved['aliases']
    assert x['scope'] == reserved['scope'] and x['entity_kind'] == reserved['entity_kind']
    assert x['domains'][0] == reserved['primary_domain']
    assert set(x['domains']) == set(original['domains'])
    assert x['relations'] == ([reserved['proposed_parent']] if reserved['proposed_parent'] else [])
    assert 1 <= len(x['card'].split()) <= 25
    for e in x['evidence']:
        used_sources.add(e['source_id'])
    for r in x['relations']:
        assert r['target_id'] in b['concepts'] or r['target_id'] in ids
        assert r['target_id'] != cid
        used_sources.update(r['source_ids'])
    review = reviews['reviews'][cid]
    assert review['outcome'] == 'author_checked' and review['card_version'] == 1
    assert review['word_count'] == len(x['card'].split())
    assert all(review[k] is True for k in ['claims_supported', 'clarity_checked', 'relations_checked'])
    assert review['limits'] == [] and review['inspected_locators']
    for loc in review['inspected_locators']:
        s = inspection_map[loc['source_id']]
        assert loc['url'] == s['url'] and loc['locator']
        assert loc['inspection_mode'] == s['inspection_mode'] and loc['tool_refs']
        assert set(loc['tool_refs']) <= set(s['tool_refs'])
    if x['scope'] in ('idea', 'facet_or_application'):
        fine.append(x)
        if any(r['type'] in ('broader_topic', 'facet_of', 'application_of') for r in x['relations']):
            parents.append(x)
assert used_sources == set(source_map)
for sid, source in source_map.items():
    inspected = inspection_map[sid]
    assert source['url'] == inspected['url'] and source['tool_refs'] == inspected['tool_refs']
    assert source['inspection_mode'] in ('web_open_text', 'web_pdf_text')
    assert source['acquisition']['remote_retrieval_timestamp'] is None
    assert source['retrieved_at'] == inspected['inspected_at']
budget_map = {x['source_id']: x for x in ledger['budgets']}
assert len(budget_map) == len(ledger['budgets']) == 82
assert set(budget_map) == set(inspection_map)
groups = collections.defaultdict(list)
for sid, row in budget_map.items():
    source = inspection_map[sid]
    assert row['url'] == source['url'] and row['word_limit'] == source['word_limit']
    assert 0 <= row['total_derived_words'] <= row['word_limit']
    assert row['counting_basis'] and isinstance(row['card_ids'], list)
    groups[source.get('budget_group', source['url'])].append(row)
for rows in groups.values():
    assert sum(r['total_derived_words'] for r in rows) <= min(r['word_limit'] for r in rows)
expected_domains = {'Biology & nature': 9, 'Chemistry & materials': 9, 'Earth & environment': 9,
                    'Food & agriculture': 9, 'Health & medicine': 9, 'Home & crafts': 9,
                    'Mathematics': 8, 'Physics & astronomy': 8}
assert dict(collections.Counter(x['domains'][0] for x in c['concepts'])) == expected_domains
assert len(fine) == 50 and len(parents) == 44
assert c['batch']['graph_gaps'] == [x['id'] for x in fine if x not in parents]
assert c['validation']['independent_audit'] == 'pending'
assert c['validation']['author_review_count'] == 70
assert c['batch']['external_ai_api_calls'] == 0
assert c['batch']['token_usage'] is None and c['batch']['cost_usage'] is None
assert (OUT / 'research-notes.md').is_file()
report = dict(schema_version=1, assignment='science',
              checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
              status='structural_checks_passed_ready_for_independent_audit',
              candidate_sha256=sha(OUT / 'candidate.json'),
              author_review_sha256=sha(OUT / 'author-review.json'),
              source_word_budgets_sha256=sha(OUT / 'source-word-budgets.json'),
              sources_inspected_sha256=sha(OUT / 'sources-inspected.json'),
              proposals_sha256=sha(OUT / 'proposals.json'),
              approved_selection_sha256=sha(OUT / 'approved-selection.json'),
              baseline_index_sha256=sha(ROOT / 'baseline-index.json'),
              global_selection_manifest_sha256=a['global_selection_manifest_sha256'],
              concept_count=70, author_review_count=70,
              card_word_range=[min(len(x['card'].split()) for x in c['concepts']),
                               max(len(x['card'].split()) for x in c['concepts'])],
              exact_frozen_imports=True, reserved_eligible_ids_only=True,
              schema_check='production_combiner.validate_candidate; shard ID registered in memory only',
              source_budget_count=len(budget_map),
              maximum_source_derived_words=max(r['total_derived_words'] for r in budget_map.values()),
              source_page_word_limit=200, domain_counts=expected_domains,
              scope_counts=dict(collections.Counter(x['scope'] for x in c['concepts'])),
              named_count=sum(x['entity_kind']=='named_subject' for x in c['concepts']),
              fine_scope_count=len(fine), fine_with_parent_or_application=len(parents),
              source_asserted_fine_parent_count=sum(any(r['assertion']=='source_asserted' and r['type'] in ('broader_topic','facet_of','application_of') for r in x['relations']) for x in parents),
              graph_gap_ids=c['batch']['graph_gaps'],
              independent_audit='pending',
              limitation='Structural checks do not certify unsampled factual accuracy or human interestingness.')
(OUT / 'draft-checks.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
print(json.dumps(report, ensure_ascii=False, indent=2))
