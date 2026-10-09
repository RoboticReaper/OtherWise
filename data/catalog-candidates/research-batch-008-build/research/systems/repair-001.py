"""Apply the completed independent audit to the existing shard, once.

This does not rebuild selection or run the historical draft builder. All writes
are confined to this researcher directory. Frozen and independent files are read.
"""
import copy
import hashlib
import importlib.util
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
BUILD = ROOT.parents[1]
PROJECT = BUILD.parents[2]
INITIAL_SHA = '757c6d40b709c025da3721534c9d782998517d04f9aff838ff0d457cf10c8524'
BASELINE_SHA = 'e3cd8ebac67579be75742df0bf2f5b2e7781293282345d2286aff205416e0fe2'
GLOBAL_SHA = '5e15d76acee1c29775a9b7b003f7d01447e494974da200c9c15afa3a25f5df9d'
AUDIT_PATH = BUILD / 'audit/systems/initial-review.json'
FROZEN_PATH = BUILD / 'frozen-initial/research/systems/candidate.json'

def read(path):
    return json.loads(Path(path).read_text())

def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()

def write(path, value):
    Path(path).write_bytes(encode(value))

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

if (ROOT / 'repair-001.json').exists():
    raise SystemExit('Repair 001 is already saved; preserve its stable checkpoint.')
assert sha(ROOT / 'candidate.json') == sha(FROZEN_PATH) == INITIAL_SHA
audit = read(AUDIT_PATH)
assert audit['completed_at'] and len(audit['records']) == 13
assert len(audit['supplementary_records']) == 3
audit_rows = {**audit['records'], **audit['supplementary_records']}
assert all(row.get('outcome') in {'verified', 'needs_repair'} for row in audit_rows.values())
assert audit['initial_integrity_verification']['all_13_snapshots_equal_frozen_catalog']
now = datetime.now(timezone.utc).isoformat()
initial = read(ROOT / 'candidate.json')
c = copy.deepcopy(initial)
a = read(ROOT / 'author-review.json')
old_author = copy.deepcopy(a)
approval = read(ROOT / 'approved-selection.json')
baseline = read(BUILD / 'baseline-index.json')
assert sha(BUILD / 'baseline-index.json') == BASELINE_SHA
assert sha(approval['global_selection_manifest_path']) == GLOBAL_SHA
assert sha(ROOT / 'approved-selection.json') == c['batch']['approved_selection_sha256']
assert c['batch']['baseline_index_sha256'] == BASELINE_SHA
assert c['batch']['global_selection_manifest_sha256'] == GLOBAL_SHA

spec = importlib.util.spec_from_file_location('systems_repair_adapter', BUILD / 'tools/assemble.py')
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)
stock = adapter.stock_module()

cards = {row['id']: row for row in c['concepts']}
old_cards = {row['id']: row for row in initial['concepts']}
sources = {row['id']: row for row in c['sources']}
old_sources = {row['id']: row for row in initial['sources']}
affected = sorted(cid for cid, row in audit_rows.items() if row['outcome'] == 'needs_repair')
assert len(affected) == 9
assert set(affected) == {
    'Q11413', 'Q65123731', 'local:catalog:rural-hospitals-theorem',
    'local:catalog:boston-immediate-acceptance-mechanism', 'local:catalog:top-trading-cycles',
    'local:catalog:moral-hazard-in-teams', 'local:catalog:relative-performance-evaluation',
    'local:catalog:tennis-service-let', 'local:catalog:wheelchair-tennis-two-bounce-rule',
}

def local_sid(scoped):
    return scoped.split('::', 1)[1]

source_locators = {
    local_sid(sid): locator for sid, locator in audit['source_record_locator_repairs'].items()
}
source_locators['systems-source-016'] += '; I School Choice assumptions, printed p.732 / PDF p.5, lines 309-313'
source_locators['systems-source-029'] = 'The rules, lines 11-17; Capturing stones and counting liberties, line 25; Strings, lines 40-41; Capturing strings, lines 49-54'
inspection_modes = {
    sid: ('Local visual reading of cached primary PDF, printed pp.324-325 / PDF pp.2-3 (repair-teams-PDF-page-2.png and repair-teams-PDF-page-3.png)'
          if sid == 'systems-source-018' else
          'web.run actual extracted authoritative HTML passage' if sid == 'systems-source-029' else
          'web.run actual extracted primary/official/educational PDF passages')
    for sid in source_locators
}
for sid, locator in source_locators.items():
    source = sources[sid]
    source['locator'] = locator
    source['retrieved_at'] = now
    source['retrieval_date'] = now[:10]
    source['acquired_at'] = now
    source['inspection_mode'] = inspection_modes[sid]
    source['repair_reinspection'] = {
        'repair_id': 'repair-001', 'post_inspection_recorded_at': now,
        'initial_local_inspection_at': old_sources[sid]['retrieved_at'],
        'time_semantics': 'Local timestamp after inspection; exact remote retrieval time unavailable.',
    }
sources['systems-source-009']['title'] = 'Dan Quint, Centralized Matching Markets (part 2), Econ 690 Lecture 14'

evidence_locators = {
    'Q65123731': '2.1 model, PDF p.3, lines 32-46; 2.2 deferred acceptance, PDF p.4, lines 48-66',
    'local:catalog:rural-hospitals-theorem': 'Section 3 fixed responsive hospital quotas, PDF p.7, lines 117-141; section 4 rural hospitals theorem, PDF p.8, lines 143-159',
    'local:catalog:boston-immediate-acceptance-mechanism': 'I.A Boston Student Assignment Mechanism, printed pp.732-733 / PDF pp.5-6, lines 362-432',
    'local:catalog:top-trading-cycles': 'I School Choice assumptions, printed p.732 / PDF p.5, lines 309-313; II.B, printed pp.736-737 / PDF pp.9-10, steps 1-k and propositions 3-4, lines 628-710',
    'local:catalog:moral-hazard-in-teams': 'Abstract and Introduction, printed pp.324-325 / PDF pp.2-3; free-rider discussion, printed p.325 / PDF p.3',
    'local:catalog:relative-performance-evaluation': 'Abstract and Introduction, printed pp.324-325 / PDF pp.2-3; relative-performance evaluation paragraph, printed p.325 / PDF p.3',
    'local:catalog:tennis-service-let': 'Rule 22 The Let During a Service, printed p.9 / PDF p.12, lines 342-350',
    'local:catalog:wheelchair-tennis-two-bounce-rule': 'Rules of Wheelchair Tennis a. The Two Bounce Rule, printed p.16 / PDF p.19, lines 565-571; ordinary boundary Rules 24(c)-25, printed pp.10-11 / PDF pp.13-14, lines 363-364 and 414-430',
    'Q11413': source_locators['systems-source-029'],
}
new_bodies = {
    'Q11413': 'Go is a two-player board game. Adjacent same-color stones connect horizontally or vertically; liberties are empty intersections beside them in those directions. Diagonals supply neither connection nor liberty. Strings without liberties are captured. Under this guide’s territory scoring, empty territory and prisoners contribute to the score.',
    'Q65123731': 'In Gale–Shapley deferred acceptance, each unmatched proposer approaches their best remaining acceptable choice. Recipients hold their best acceptable offer so far, including earlier offers, and reject others. Under fixed strict rankings in the standard one-to-one model, repeating these rounds produces a stable matching.',
    'local:catalog:top-trading-cycles': 'In school-choice top trading cycles with strict preference and priority rankings, each remaining student points to their highest-ranked school with seats; each school points to its highest-priority remaining student. Cycles assign seats, remove assigned students, reduce capacities and remove full schools. Repetition completes the allocation.',
}
for cid in affected:
    row = cards[cid]
    row['card_version'] = old_cards[cid]['card_version'] + 1
    assert len(row['evidence']) == 1
    row['evidence'][0]['locator'] = evidence_locators[cid]
    if cid in new_bodies:
        row['card'] = new_bodies[cid]

rural = cards['local:catalog:rural-hospitals-theorem']['relations'][0]
rural['type'] = 'related_to'
rural['assertion'] = 'editorial'
rural['note'] = 'Editorial comparison: this theorem concerns a many-to-one extension of the pinned one-to-one stable matching problem; Q620702 is not a taxonomy parent.'
cards['local:catalog:relative-performance-evaluation']['relations'][0]['note'] = 'The abstract and introduction explain how peers’ outcomes inform incentive contracts in the model.'
a['reviews']['local:catalog:relative-performance-evaluation']['limits'] = [
    'Bounded to Holmström’s informational model; no universal benefit of competition is claimed.'
]

for cid in affected:
    row = cards[cid]
    review = a['reviews'][cid]
    review.update(outcome='author_rechecked_after_initial_audit', word_count=len(row['card'].split()),
                  card_version=row['card_version'], repair_id='repair-001',
                  previous_selected_version=old_cards[cid]['card_version'],
                  repair_reviewed_at=now, independent_audit_status='repair_awaiting_independent_recheck')
    review['inspected_locators'] = [
        {'source_id': e['source_id'], 'locator': e['locator'],
         'inspection_mode': inspection_modes[e['source_id']]} for e in row['evidence']
    ]
    review['relationship_checks'] = [
        {**copy.deepcopy(rel), 'inspected_locators': [sources[sid]['locator'] for sid in rel['source_ids']],
         'outcome': 'supported_by_reinspected_premises'} for rel in row['relations']
    ]
    review['initial_independent_review_pointer'] = str(AUDIT_PATH.relative_to(PROJECT)) + '#/' + ('records' if cid in audit['records'] else 'supplementary_records') + '/' + cid
for cid, audited in audit_rows.items():
    a['reviews'][cid]['initial_independent_outcome'] = audited['outcome']
    if audited['outcome'] == 'verified':
        a['reviews'][cid]['independent_audit_status'] = 'initial_verified_unchanged_bundle'
a.update(status='complete_author_repair_review', reviewed_at=now)

batch = c['batch']
batch['revision'] = 2
batch['status'] = 'repair_ready_for_independent_recheck'
batch['scope_note'] = 'One approved shard; the completed fixed initial audit is preserved and repair recheck/coordinator acceptance remain pending.'
batch['missing_parent_links'] = [{
    'id': 'local:catalog:rural-hospitals-theorem', 'missing_parent': True,
    'reason_code': 'baseline_one_to_one_target_for_many_to_one_extension',
    'rejected_target_id': 'Q620702', 'rejected_parent_type': 'facet_of',
    'explanation_pointer': 'concepts/local:catalog:rural-hospitals-theorem/relations/0/note',
    'premise_source_ids': ['systems-source-009'],
    'premise_locator': evidence_locators['local:catalog:rural-hospitals-theorem'],
}]
fine = [row for row in c['concepts'] if row['scope'] in {'idea', 'facet_or_application'}]
parent_types = {'broader_topic', 'facet_of', 'application_of'}
batch['graph_coverage'] = {
    'fine_cards': len(fine),
    'fine_with_parent_or_application': sum(any(r['type'] in parent_types for r in row['relations']) for row in fine),
    'fine_with_source_asserted_parent_or_application': sum(any(r['type'] in parent_types and r['assertion'] == 'source_asserted' for r in row['relations']) for row in fine),
    'fine_parent_gaps': ['local:catalog:rural-hospitals-theorem'],
}
for decision in batch['control_version_decisions']:
    decision['selected_card_version'] = cards[decision['id']]['card_version']
    if decision['id'] in affected:
        decision['repair_version_decision'] = {
            'repair_id': 'repair-001', 'previous_selected_version': old_cards[decision['id']]['card_version'],
            'selected_card_version': cards[decision['id']]['card_version'],
        }
batch['repair_history'] = [{
    'repair_id': 'repair-001', 'record_path': str((ROOT / 'repair-001.json').relative_to(PROJECT)),
    'initial_shard_candidate_sha256': INITIAL_SHA,
    'initial_assembled_candidate_sha256': audit['initial_candidate_sha256'],
    'initial_review_path': str(AUDIT_PATH.relative_to(PROJECT)), 'initial_review_sha256': sha(AUDIT_PATH),
    'affected_versions': {cid: {'before': old_cards[cid]['card_version'], 'after': cards[cid]['card_version']} for cid in affected},
}]
c['issues'][2]['note'] = 'Hazard-pointer protection and deferred reclamation were inspected in P2530R3. The friendship-paradox card stays within primary-abstract support. Relative-performance support now includes the inspected primary introduction. Edition-specific DLS mechanics remain qualified.'
c['issues'].extend([
    {'type': 'parent_coverage_gap', 'status': 'reported', 'concept_ids': ['local:catalog:rural-hospitals-theorem'],
     'note': 'See batch.missing_parent_links and the canonical relationship note.'},
    {'type': 'initial_audit_repairs', 'status': 'awaiting_independent_recheck', 'repair_id': 'repair-001',
     'affected_ids': affected, 'note': 'Nine selected versions changed after the completed initial review.'},
])

budgets = {}
for row in c['concepts']:
    used_e = {e['source_id'] for e in row['evidence']}
    used_r = {sid for rel in row['relations'] for sid in rel['source_ids']}
    components = {
        'card_body_words': len(row['card'].split()),
        'learning_takeaway_words': len(row['learning_takeaway'].split()),
        'evidence_note_words': sum(len(e['note'].split()) for e in row['evidence']),
        'relation_note_words': sum(len(rel['note'].split()) for rel in row['relations']),
        'author_limit_words': sum(len(limit.split()) for limit in a['reviews'][row['id']]['limits']),
    }
    for sid in sorted(used_e | used_r):
        value = budgets.setdefault(sid, {'card_words': 0, 'attributed_generated_words': 0,
                                       'concept_ids': [], 'contributions': []})
        value['card_words'] += components['card_body_words']
        value['attributed_generated_words'] += sum(components.values())
        value['concept_ids'].append(row['id'])
        value['contributions'].append({'concept_id': row['id'], 'components': copy.deepcopy(components),
                                      'total_words': sum(components.values()),
                                      'supplies_card': sid in used_e, 'supplies_relation': sid in used_r})
for sid, value in budgets.items():
    value.update(source_url=sources[sid]['url'], summary_word_limit=200,
                 within_limit=value['attributed_generated_words'] <= 200)
by_url = {v['source_url']: {'source_id': sid, **copy.deepcopy(v)} for sid, v in budgets.items()}
assert len(by_url) == len(budgets)
by_url['https://www.rfc-editor.org/rfc/rfc9421.txt'] = {
    'source_id': 'systems-source-006', 'same_work_primary_url': 'https://www.rfc-editor.org/rfc/rfc9421.html',
    'budget_not_reset': True, **copy.deepcopy(budgets['systems-source-006'])}
budget_artifact = {
    'schema_version': 1,
    'accounting': 'Current authored prose: conservative sum of card body, learning takeaway, evidence notes, relation notes and author limits, charged in full to each cited source. Reference titles/locators, audit/version metadata, frozen selection and before-repair inputs, and pre-existing imported records are excluded. After-records in repair-001.json mirror already charged canonical fields. The parent-gap explanation points to the charged canonical relation note. Multi-source cards are charged in full to each URL. The HTML/text representations of RFC 9421 share one budget.',
    'verbatim_generated_quotes': 0, 'by_source': budgets, 'by_url': by_url,
    'over_limit': [sid for sid, value in budgets.items() if not value['within_limit']],
    'repair_id': 'repair-001',
    'preserved_initial_budget_path': str((BUILD / 'frozen-initial/research/systems/word-budget-review.json').relative_to(PROJECT)),
}
assert not budget_artifact['over_limit']
batch['source_summary_budgets'] = {
    sid: {'url': sources[sid]['url'], 'body_words': value['card_words'],
          'alternate_same_work_urls': ['https://www.rfc-editor.org/rfc/rfc9421.txt'] if sid == 'systems-source-006' else [],
          'generated_attributable_words': value['attributed_generated_words'],
          'limit': 200, 'concept_ids': value['concept_ids']} for sid, value in budgets.items()
}

approved_rows = {row['id']: row for row in approval['accepted']}
assert set(cards) == set(approved_rows) and len(cards) == 61
targets = set(baseline['concepts']) | set(approval['all_reserved_ids'])
protected_fields = {'id', 'label', 'aliases', 'entity_kind', 'scope', 'domains', 'learning_takeaway',
                    'original_description', 'identity_urls', 'imported_records'}
for cid, row in cards.items():
    assert all(row[field] == old_cards[cid][field] for field in protected_fields)
    assert row['card_version'] == approved_rows[cid]['required_card_version'] + (1 if cid in affected else 0)
    assert 30 <= len(row['card'].split()) <= 50
    assert all(e['source_id'] in sources for e in row['evidence'])
    assert all(rel['target_id'] in targets and all(sid in sources for sid in rel['source_ids']) for rel in row['relations'])
    if cid not in affected:
        assert row == old_cards[cid]
    if approved_rows[cid]['inventory_status'] == 'existing':
        assert row['original_description'] == baseline['concepts'][cid]['original_description']
        assert row['imported_records'] == baseline['concepts'][cid]['inventory_records']
for before, after in zip(initial['batch']['control_version_decisions'], batch['control_version_decisions']):
    assert all(after[key] == value for key, value in before.items())
for sid, source in sources.items():
    if sid not in source_locators:
        assert source == old_sources[sid]
assert batch['counts'] == initial['batch']['counts']
assert batch['shared_alias_meanings'] == initial['batch']['shared_alias_meanings']

word_range = [min(len(row['card'].split()) for row in c['concepts']), max(len(row['card'].split()) for row in c['concepts'])]
c['validation'].update(status='author_repair_checked', structural_validation='passed',
                       independent_source_audit='initial_complete_repair_recheck_pending',
                       reservation_baseline_target_checks='passed', card_word_range=word_range,
                       all_required_versions=True, required_version_policy='Approved initial version plus one for each repaired card/reference bundle',
                       repaired_bundles=9, initial_audit_review_sha256=sha(AUDIT_PATH))
stock.validate_candidate(c, ROOT / 'candidate.json')

def bundle(document, cid):
    concepts_by_id = {row['id']: row for row in document['concepts']}
    source_by_id = {row['id']: row for row in document['sources']}
    row = concepts_by_id[cid]
    used = {e['source_id'] for e in row['evidence']} | {sid for rel in row['relations'] for sid in rel['source_ids']}
    return {'concept': copy.deepcopy(row), 'sources': [copy.deepcopy(source_by_id[sid]) for sid in sorted(used)]}

changed_bundles = [cid for cid in cards if bundle(initial, cid) != bundle(c, cid)]
assert set(changed_bundles) == set(affected)
candidate_bytes = encode(c)
current_sha = hashlib.sha256(candidate_bytes).hexdigest()
a['candidate_sha256'] = current_sha
records = {}
for cid in affected:
    before, after = bundle(initial, cid), bundle(c, cid)
    fields = [field for field in before['concept'] if before['concept'][field] != after['concept'][field]]
    records[cid] = {
        'before_version': old_cards[cid]['card_version'], 'after_version': cards[cid]['card_version'],
        'changed_concept_fields': fields, 'source_bundle_changed': before['sources'] != after['sources'],
        'initial_raw_card_sha256': stock.digest(before['concept']), 'current_raw_card_sha256': stock.digest(after['concept']),
        'initial_raw_source_bundle_sha256': stock.digest(before), 'current_raw_source_bundle_sha256': stock.digest(after),
        'auditor_initial_assembled_card_sha256': audit_rows[cid]['initial_card_sha256'],
        'auditor_initial_assembled_source_bundle_sha256': audit_rows[cid]['initial_source_bundle_sha256'],
        'initial_review_pointer': a['reviews'][cid]['initial_independent_review_pointer'],
        'initial_findings': copy.deepcopy(audit_rows[cid]['findings']),
        'before': before, 'after': after,
        'author_review_before': old_author['reviews'][cid], 'author_review_after': a['reviews'][cid],
        'source_support': [{'source_id': e['source_id'], 'url': sources[e['source_id']]['url'],
                            'locator': e['locator'], 'inspection_mode': inspection_modes[e['source_id']],
                            'post_inspection_recorded_at': now} for e in cards[cid]['evidence']],
    }
repair = {
    'schema_version': 1, 'id': 'repair-001', 'assignment': 'systems',
    'status': 'repair_ready_for_independent_recheck', 'recorded_at': now,
    'initial_candidate_sha256': INITIAL_SHA, 'current_candidate_sha256': current_sha,
    'initial_assembled_candidate_sha256': audit['initial_candidate_sha256'],
    'frozen_initial_shard_path': str(FROZEN_PATH.relative_to(PROJECT)),
    'initial_review_path': str(AUDIT_PATH.relative_to(PROJECT)), 'initial_review_sha256': sha(AUDIT_PATH),
    'initial_review_completed_at': audit['completed_at'], 'sample_manifest_sha256': audit['sample_manifest_sha256'],
    'global_selection_manifest_sha256': GLOBAL_SHA, 'baseline_index_sha256': BASELINE_SHA,
    'approved_selection_sha256': sha(ROOT / 'approved-selection.json'),
    'affected_versions': batch['repair_history'][0]['affected_versions'],
    'body_changed_ids': sorted(new_bodies), 'changed_bundle_count': 9,
    'source_changes': {sid: {'before': old_sources[sid], 'after': source} for sid, source in sources.items() if sid in source_locators},
    'records': records,
    'parent_gaps': copy.deepcopy(batch['missing_parent_links']),
    'hash_semantics': 'Raw card/bundle hashes use stock.digest; assembled initial hashes retain the auditor’s scoped-source-ID snapshots. File hashes use the exact saved bytes.',
    'preservation_checks': {'all_61_approved_ids_scopes_domains': True, 'both_pinned_hashes': True,
                            'canonical_control_ids': True, 'control_originals_raw_rows_full_prior_records': True,
                            'unaffected_52_bundles_unchanged': True, 'frozen_initial_and_audit_files_unchanged': True},
    'source_reinspection': {'teams_cached_file_sha256': sha(ROOT / 'teams-source.pdf'),
                            'teams_pdf_pages_1based': [2, 3], 'time_semantics': 'Local completion after passage inspection, not a precise remote retrieval time.'},
    'independent_recheck': 'pending', 'usage': {'model_tokens': None, 'cost': None},
}

checks = {key: True for key in (
    'stock_schema', 'registered_or_reserved_targets', 'source_resolution', 'canonical_id_and_versions',
    'exact_original_descriptions', 'raw_import_rows_unchanged', 'full_prior_record_pointers',
    'normalized_alias_checks', 'card_word_budget', 'complete_61', 'exactly_nine_incremented_bundles',
    'unaffected_52_bundles_unchanged', 'collective_source_prose_budgets', 'pinned_hashes_unchanged')}
validation = {
    'schema_version': 1, 'status': 'passed', 'checked_at': now, 'repair_id': 'repair-001',
    'candidate_sha256': current_sha, 'approved_selection_sha256': sha(ROOT / 'approved-selection.json'),
    'global_selection_manifest_sha256': GLOBAL_SHA, 'baseline_index_sha256': BASELINE_SHA,
    'stock_validator': 'adapter.stock_module().validate_candidate', 'checks': checks, 'counts': batch['counts'],
    'version_decisions': batch['repair_history'][0]['affected_versions'], 'independent_recheck': 'pending',
}
handoff = {
    'status': 'repair_ready_for_independent_recheck', 'candidate_sha256': current_sha,
    'candidate_hash_stable_on_repeat_read': True, 'cards': 61, 'new': 55, 'existing_controls': 6,
    'word_range': word_range, 'author_reviews': 61, 'repaired_bundles': 9, 'body_changed_cards': 3,
    'maximum_source_prose_words': max(value['attributed_generated_words'] for value in budgets.values()),
    'checks': checks, 'independent_audit': 'initial_complete_repair_recheck_pending',
}

source_records = read(ROOT / 'source-records.json')
for row in source_records:
    if row['id'] in source_locators:
        row.update(copy.deepcopy(sources[row['id']]))
drafts = read(ROOT / 'card-drafts.json')
drafts.update(new_bodies)
access = read(ROOT / 'source-access-log.json')
access['scope_limits'][0] = 'The friendship-paradox card uses bounded primary-abstract claims. Relative-performance evidence includes the visually inspected primary introduction, printed p.325 / PDF p.3.'
access['repair_001_reinspection'] = [
    {'url': sources[sid]['url'], 'locator': locator, 'inspection_mode': inspection_modes[sid],
     'outcome': 'actual_passages_inspected', 'failed_attempts': 0, 'post_inspection_recorded_at': now,
     'time_semantics': 'Local inspection completion; not an exact remote retrieval timestamp.'}
    for sid, locator in source_locators.items()
]

# All checks have passed in memory. Save the complete checkpoint only now.
(ROOT / 'candidate.json').write_bytes(candidate_bytes)
write(ROOT / 'author-review.json', a)
write(ROOT / 'word-budget-review.json', budget_artifact)
write(ROOT / 'repair-001.json', repair)
write(ROOT / 'draft-validation.json', validation)
write(ROOT / 'final-handoff-validation.json', handoff)
write(ROOT / 'source-records.json', source_records)
write(ROOT / 'card-drafts.json', drafts)
write(ROOT / 'source-access-log.json', access)
assert sha(ROOT / 'candidate.json') == current_sha
assert sha(FROZEN_PATH) == INITIAL_SHA
assert sha(AUDIT_PATH) == repair['initial_review_sha256']
print(json.dumps({'status': handoff['status'], 'candidate_sha256': current_sha,
                  'changed_bundles': len(changed_bundles), 'versions': repair['affected_versions'],
                  'word_range': word_range, 'maximum_source_prose_words': handoff['maximum_source_prose_words'],
                  'repaired_source_budgets': {sid: budgets[sid]['attributed_generated_words'] for sid in source_locators}}, ensure_ascii=False))
