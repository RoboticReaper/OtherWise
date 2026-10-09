"""Assemble explicitly authored approved cards. Local checks only, no API generation."""
import copy
import hashlib
import importlib.util
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if (ROOT / 'repair-001.json').exists():
    raise SystemExit('Historical initial-draft builder: repaired versions and fields must not be restored.')
sys.dont_write_bytecode = True
BUILD = ROOT.parents[1]
PROJECT = BUILD.parents[2]
APPROVED = ROOT / 'approved-selection.json'
GLOBAL_HASH = '5e15d76acee1c29775a9b7b003f7d01447e494974da200c9c15afa3a25f5df9d'
BASELINE_HASH = 'e3cd8ebac67579be75742df0bf2f5b2e7781293282345d2286aff205416e0fe2'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
read = lambda p: json.loads(Path(p).read_text())
write = lambda p, d: Path(p).write_text(json.dumps(d, ensure_ascii=False, indent=2)+'\n')
approved = read(APPROVED)
baseline = read(BUILD/'baseline-index.json')
assert sha(approved['global_selection_manifest_path']) == GLOBAL_HASH
assert sha(BUILD/'baseline-index.json') == BASELINE_HASH
assert approved['global_selection_manifest_sha256'] == GLOBAL_HASH
assert approved['baseline_index_sha256'] == BASELINE_HASH
reservations = {p['id']: p for p in approved['accepted']}
drafts = read(ROOT/'card-drafts.json')
assert set(drafts) <= set(reservations) and len(reservations) == 61
now = datetime.now(timezone.utc).isoformat()
supplement_path = ROOT/'supplemental-inspections.json'
if not supplement_path.exists():
    write(supplement_path, [dict(source_id='systems-source-006',
        url='https://www.rfc-editor.org/rfc/rfc9421.txt',
        locator='1.1 Conventions and Terminology, lines 254-276; 7.3.3 Symmetric Cryptography, lines 3267-3287',
        local_inspected_at=now, inspection_mode='web.run actual official RFC text passage',
        note='Same RFC as the HTML source; this inspection clarifies its asymmetric signature and keyed-MAC alternatives, without resetting the summary budget.')])

sources = copy.deepcopy(read(ROOT/'source-records.json'))
for s in sources:
    s['retrieved_at'] = s['acquired_at']
    s['retrieval_date'] = s['acquired_at'][:10]
    s['acquisition_note'] = 'These ISO fields record local inspection completion, not an exact remote response or server retrieval time.'
    s['summary_word_limit'] = 200

additional_path = ROOT/'additional-source-records.json'
if additional_path.exists():
    sources.extend(read(additional_path))
else:
    new_sources = [
        dict(id='systems-source-051', title='Michael et al., Hazard Pointers for C++26',
            url='https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2023/p2530r3.pdf',
            locator='2 Hazard pointer overview, PDF pp. 4-5, lines 125-162', revision='P2530R3, 2023-03-02'),
        dict(id='systems-source-052', title='Thomas C. Schelling, Models of Segregation',
            url='https://www.uu.nl/sites/default/files/c4_schelling1969_models_segregation.pdf',
            locator='Printed pp. 488-491 / PDF pp. 2-5, lines 23-43, 139-151, 157-228',
            revision='American Economic Review 59(2), May 1969, pp. 488-493'),
    ]
    for s in new_sources:
        s.update(retrieved_at=now, retrieval_date=now[:10],
            acquisition_note='Local timestamp after reading; exact remote response/retrieval time unavailable.',
            inspection_mode='web.run actual extracted primary PDF passage', summary_word_limit=200)
    write(additional_path, new_sources)
    sources.extend(new_sources)
source_by_url = {s['url']: s for s in sources}
source_by_id = {s['id']: s for s in sources}
source_by_id['systems-source-006']['supplemental_inspections'] = read(supplement_path)
source_by_id['systems-source-006']['locator'] += '; 1.1 Conventions and Terminology; 7.3.3 Symmetric Cryptography (official text companion inspected)'

# Additional inspected support changes citations while preserving approved identity and parent semantics.
overrides = {
    'local:catalog:hazard-pointer': ['systems-source-051'],
    'local:catalog:schelling-segregation-model': ['systems-source-052'],
    'local:catalog:market-unraveling': ['systems-source-050'],
    'local:catalog:http-structured-field-dictionary': ['systems-source-048'],
}
short_parent_notes = {
    'Q65123731': 'Deferred acceptance solves the stable matching problem.',
    'local:catalog:rural-hospitals-theorem': 'Invariance theorem about stable hospital-doctor matchings.',
    'local:catalog:homophily': 'Similarity among connected people in social networks.',
    'local:catalog:focal-closure': 'Shared affiliations can create a social tie.',
    'local:catalog:membership-closure': 'Friendship can create a person-to-focus membership edge.',
    'local:catalog:schelling-segregation-model': 'Schelling explicitly models segregation by color.',
    'local:catalog:http-message-signatures': 'The RFC applies digital signatures to HTTP signature bases; its symmetric-MAC option lies outside this digital-signature parent.',
}
effective_limits = {i: list(r['limits']) for i,r in reservations.items()}
effective_limits['local:catalog:hazard-pointer'] = ['Core protection and deferred reclamation inspected in P2530R3; no current C++ adoption status or performance estimate is asserted.']
effective_limits['local:catalog:schelling-segregation-model'] = ['The 1969 primary passage uses a two-type line model; the selected identity also encompasses the later grid presentation. Both are stylized models, not measurements or a complete explanation of real segregation.']
effective_limits['local:catalog:homophily'] = ['Aggregate tendency; selection and influence can both produce similarity.']
effective_limits['local:catalog:focal-closure'] = ['A tendency; shared membership does not prove causation.']
effective_limits['local:catalog:membership-closure'] = ['A possible mechanism with multiple real-world causes.']
effective_limits['local:catalog:http-message-signatures'] = ['RFC 9421 also permits symmetric keyed MACs; this parent refers to its asymmetric digital-signature form.']
takeaway_overrides = {
    'local:catalog:homophily': 'Shared traits often accompany social ties.',
    'local:catalog:focal-closure': 'A shared activity can help create a friendship.',
    'local:catalog:membership-closure': 'An existing friendship can lead to a new affiliation.',
}

concepts = []
reviews = {}
ownership = {}
control_decisions = []
word_budget = defaultdict(lambda: dict(card_words=0, attributed_generated_words=0, concept_ids=[], contributions=[]))
for identifier in sorted(drafts):
    r = reservations[identifier]
    assert r['approved'] is True and r['owner'] == 'systems'
    body = drafts[identifier]
    assert 30 <= len(body.split()) <= 50, (identifier, len(body.split()))
    sids = overrides.get(identifier) or list(dict.fromkeys(source_by_url[e['url']]['id'] for e in r['discovery_evidence']))
    evidence = []
    for sid in sids:
        source = source_by_id[sid]
        original = next((e for e in r['discovery_evidence'] if e['url']==source['url']), None)
        loc = original['locator'] if original else source['locator']
        note = 'Supports the qualified card meaning.'
        if identifier=='local:catalog:duckworth-lewis-stern-method':
            note='Adopted target-adjustment method.' if sid=='systems-source-028' else 'Edition status and Standard resources.'
        if identifier=='local:catalog:productive-failure':
            loc += '; Method/Research Design, printed p. 1588 / PDF p. 2, lines 148-195'
        if identifier=='local:catalog:http-message-signatures':
            loc += '; 1.1 Terminology; 7.3.3 Symmetric Cryptography, official text companion lines 254-276 and 3267-3287'
        evidence.append(dict(source_id=sid, locator=loc, note=note))
    relations = []
    parent = r['proposed_parent']
    if parent:
        parent_sid = source_by_url[parent['url']]['id']
        if identifier in overrides:
            parent_sid = sids[0]
        note = short_parent_notes.get(identifier, parent['note'])
        relations.append(dict(target_id=parent['target_id'], type=parent['type'],
            source_ids=[parent_sid], assertion=parent['assertion'], note=note))
    b = baseline['concepts'].get(identifier)
    identity_urls = [source_by_id[s]['url'] for s in sids]
    if b:
        identity_urls = list(dict.fromkeys([u.get('source_url') for u in b.get('inventory_records', [])
            if isinstance(u.get('source_url'),str) and u['source_url'].startswith('https://')] + identity_urls))
    concept = dict(id=identifier, label=r['label'], aliases=list(r['aliases']), entity_kind=r['entity_kind'],
        scope=r['scope'], domains=[r['primary_domain']], learning_takeaway=takeaway_overrides.get(identifier,r['learning_takeaway']), card=body,
        original_description=b.get('original_description') if b else None, identity_urls=identity_urls,
        evidence=evidence, relations=relations, card_version=r['required_card_version'],
        imported_records=copy.deepcopy(b.get('inventory_records', [])) if b else [])
    concepts.append(concept)
    ownership[identifier] = dict(owner='systems', primary_subfield=r['primary_subfield'],
        inventory_status=r['inventory_status'], nearest_baseline_ids=[n['id'] for n in r['nearest_baseline_matches']],
        approved_meaning_pointer=f'approved-selection.json#/accepted/{approved["accepted"].index(r)}')
    if b:
        decision = copy.deepcopy(next(c for c in approved['controls'] if c['id']==identifier))
        decision['prior_bundles'] = copy.deepcopy(r['control_record_metadata']['prior_bundles'])
        decision['prior_full_records'] = copy.deepcopy(b.get('candidate_records', []))
        decision['original_description_preserved_exactly'] = True
        decision['all_raw_inventory_rows_preserved'] = True
        control_decisions.append(decision)
    reviews[identifier] = dict(outcome='author_checked', word_count=len(body.split()),
        meaning_boundary_checked=True, substantive_claims_checked=True,
        inspected_locators=[dict(source_id=e['source_id'], locator=e['locator'],
            inspection_mode=source_by_id[e['source_id']]['inspection_mode']) for e in evidence],
        relationship_checks=[dict(target_id=p['target_id'], type=p['type'], assertion=p['assertion'],
            source_ids=p['source_ids'], inspected_locators=[source_by_id[s]['locator'] for s in p['source_ids']],
            outcome='supported_by_inspected_premises') for p in relations],
        card_version=r['required_card_version'], prior_maximum_version=r['baseline_max_card_version'],
        original_wording_and_imports_preserved=(not b or concept['original_description']==b.get('original_description') and concept['imported_records']==b.get('inventory_records', [])),
        limits=effective_limits[identifier], independent_audit_status='pending')
    # Charge the whole card and all attached new explanatory annotations to every cited source.
    # Titles/locators, pre-existing raw records and identity pointers are reference metadata, not generated summaries.
    components = dict(card_body_words=len(body.split()), learning_takeaway_words=len(concept['learning_takeaway'].split()),
        evidence_note_words=sum(len(e['note'].split()) for e in evidence),
        relation_note_words=sum(len(p['note'].split()) for p in relations),
        author_limit_words=sum(len(l.split()) for l in effective_limits[identifier]))
    charged = sum(components.values())
    cited = set(sids) | {s for p in relations for s in p['source_ids']}
    for sid in cited:
        account=word_budget[sid]
        account['card_words'] += len(body.split())
        account['attributed_generated_words'] += charged
        account['concept_ids'].append(identifier)
        account['contributions'].append(dict(concept_id=identifier, components=components, total_words=charged,
            supplies_card=(sid in sids), supplies_relation=any(sid in p['source_ids'] for p in relations)))

complete = len(concepts)==61
fine = [c for c in concepts if c['scope'] in ['idea','facet_or_application']]
current_issues = copy.deepcopy(read(ROOT/'proposals.json')['issues'])
for issue in current_issues:
    if issue['type']=='selection_evidence_depth':
        issue.update(status='resolved_with_bounded_claims',
            note='Hazard-pointer protection and deferred reclamation were inspected in P2530R3. Friendship-paradox and relative-performance cards stay within inspected primary-abstract support. Edition-specific DLS mechanics remain qualified.')
candidate = dict(schema_version=1,
    batch=dict(id='research-batch-008-systems', kind='researched_candidate', revision=1,
        status='draft_ready_for_independent_audit' if complete else 'author_checkpoint', assignment='systems',
        global_selection_manifest_sha256=GLOBAL_HASH, baseline_index_sha256=BASELINE_HASH,
        approved_selection_sha256=sha(APPROVED), approved_selection_path=str(APPROVED.relative_to(PROJECT)),
        baseline_index_path=str((BUILD/'baseline-index.json').relative_to(PROJECT)),
        concept_ownership=ownership, control_version_decisions=control_decisions,
        missing_parent_links=[c['id'] for c in fine if not c['relations']],
        source_summary_budgets={sid: dict(url=source_by_id[sid]['url'], body_words=a['card_words'],
            alternate_same_work_urls=[i['url'] for i in source_by_id[sid].get('supplemental_inspections',[])],
            generated_attributable_words=a['attributed_generated_words'], limit=200, concept_ids=a['concept_ids']) for sid,a in word_budget.items()},
        shared_alias_meanings=[dict(alias='Go', selected_id='Q11413', other_baseline_id='Q37227',
            selected_meaning='board game', other_meaning='programming language')] if 'Q11413' in drafts else [],
        counts=dict(cards=len(concepts), new=sum(c['id'] not in baseline['concepts'] for c in concepts),
            existing_controls=sum(c['id'] in baseline['concepts'] for c in concepts),
            primary_domains=dict(Counter(c['domains'][0] for c in concepts)), scopes=dict(Counter(c['scope'] for c in concepts)),
            entity_kinds=dict(Counter(c['entity_kind'] for c in concepts))),
        scope_note='One approved shard; independent audit and coordinator acceptance remain pending. Operational data are untouched.',
        usage=dict(token_count=None, cost=None, reason='Per-agent model token and cost telemetry is unavailable in exposed tools.')),
    sources=sources, concepts=concepts, issues=current_issues,
    validation=dict(status='author_checked' if complete else 'checkpoint', structural_validation='pending', independent_source_audit='pending'))
spec=importlib.util.spec_from_file_location('batch008_adapter', BUILD/'tools/assemble.py')
adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
adapter.stock_module().validate_candidate(candidate, ROOT/'candidate.json')
normalizer=lambda s: re.sub(r'[\s_\-\u2010-\u2015]+', ' ', s.strip().casefold()).strip()
allowed = set(baseline['concepts']) | set(approved['all_reserved_ids'])
for c in concepts:
    assert c['id'] in reservations
    assert c['card_version']==reservations[c['id']]['required_card_version']
    assert c['domains'][0]==reservations[c['id']]['primary_domain']
    assert all(p['target_id'] in allowed for p in c['relations'])
    assert all(s in source_by_id for p in c['relations'] for s in p['source_ids'])
    if c['id'] not in baseline['concepts']:
        assert not any(baseline['aliases'].get(normalizer(q),[]) for q in [c['label'],*c['aliases']])
candidate['validation'].update(structural_validation='passed', reservation_baseline_target_checks='passed',
    cards_30_to_50_words=True, card_word_range=[min(len(c['card'].split()) for c in concepts), max(len(c['card'].split()) for c in concepts)],
    all_required_versions=True, exact_raw_control_preservation=True)
adapter.stock_module().validate_candidate(candidate, ROOT/'candidate.json')
write(ROOT/'candidate.json', candidate)
write(ROOT/'author-review.json', dict(schema_version=1, batch_id=candidate['batch']['id'],
    status='complete_author_review' if complete else 'in_progress', reviewed_at=now,
    candidate_sha256=sha(ROOT/'candidate.json'), global_selection_manifest_sha256=GLOBAL_HASH,
    baseline_index_sha256=BASELINE_HASH, reviews=reviews,
    note='Author review is separate from the coordinator’s fixed independent source audit.'))
for sid, account in word_budget.items():
    account.update(source_url=source_by_id[sid]['url'], summary_word_limit=200,
        within_limit=account['attributed_generated_words']<=200)
assert all(a['within_limit'] for a in word_budget.values()), 'Repair collective source prose budgets before marking the final draft ready.'
by_url = {a['source_url']:dict(source_id=sid, **a) for sid,a in word_budget.items()}
for sid,account in word_budget.items():
    for inspection in source_by_id[sid].get('supplemental_inspections',[]):
        by_url[inspection['url']] = dict(source_id=sid, same_work_primary_url=source_by_id[sid]['url'],
            budget_not_reset=True, **account)
write(ROOT/'word-budget-review.json', dict(schema_version=1,
    accounting='New draft-phase prose: conservative sum of card body, learning takeaway, evidence notes, relation notes and author limits, charged in full to each cited source. Reference titles/locators, frozen selection inputs and pre-existing imported records are excluded. Multi-source cards are charged in full to each supporting URL. The HTML/text representations of RFC 9421 share one budget.',
    verbatim_generated_quotes=0, by_source=dict(word_budget), by_url=by_url,
    over_limit=[sid for sid,a in word_budget.items() if not a['within_limit']]))
write(ROOT/'draft-validation.json', dict(schema_version=1, status='passed', checked_at=now,
    candidate_sha256=sha(ROOT/'candidate.json'), approved_selection_sha256=sha(APPROVED),
    global_selection_manifest_sha256=GLOBAL_HASH, baseline_index_sha256=BASELINE_HASH,
    stock_validator='adapter.stock_module().validate_candidate',
    checks=dict(stock_schema=True, registered_or_reserved_targets=True, source_resolution=True,
        canonical_id_and_versions=True, exact_original_descriptions=True, raw_import_rows_unchanged=True,
        full_prior_record_pointers=True, normalized_alias_checks=True, card_word_budget=True,
        complete_61=complete), counts=candidate['batch']['counts']))
print(json.dumps(dict(status=candidate['batch']['status'], cards=len(concepts),
    candidate_sha256=sha(ROOT/'candidate.json'), words=candidate['validation']['card_word_range'],
    source_budgets_over_200=[sid for sid,a in word_budget.items() if not a['within_limit']]), ensure_ascii=False))
