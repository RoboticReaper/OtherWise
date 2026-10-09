"""Reproduce the approved revision from pinned inputs and completed reviews."""
from __future__ import annotations
import copy
import importlib.util
from pathlib import Path
from collections import Counter
from urllib.parse import urlparse

import reconcile_catalog as lib

REVISION = Path(__file__).resolve().parents[1]
PROJECT = REVISION.parents[3]
PILOT = REVISION.parent


def build():
    protection = lib.read(REVISION/'original-input-protection.json')['protected_sha256']
    for relative, expected in protection.items():
        lib.require(lib.sha(PROJECT/relative) == expected, f'Protected input changed: {relative}')
    manifest = lib.freeze_baseline(PROJECT, REVISION)
    baseline = lib.read(REVISION/'baseline-index.json')['concepts']
    raw = lib.read(REVISION/'baseline-imported-records.json')['concepts']
    original_paths = [PROJECT/f'data/catalog-candidates/research-batch-{n:03d}.json' for n in range(3, 8)]
    originals = [lib.read(p) for p in original_paths]
    input_hashes = {b['batch']['id']: lib.sha(p) for b, p in zip(originals, original_paths)}
    cards = {c['id']: c for b in originals for c in b['concepts']}
    owners = {c['id']: b['batch']['id'] for b in originals for c in b['concepts']}
    reviews, research_inputs = [], []
    for part in range(1, 4):
        input_path = REVISION/f'research/part-{part:02d}.input.json'
        decision_path = REVISION/f'research/part-{part:02d}.decisions.json'
        assignment = lib.read(input_path)
        decisions = lib.read(decision_path)['decisions']
        expected = {row['id'] for row in assignment['rows']}
        lib.require({r['id'] for r in decisions} == expected and len(decisions) == len(expected),
                    f'Incomplete review partition {part}')
        reviews.extend(decisions)
        research_inputs.append(dict(path=str(decision_path.relative_to(REVISION)), sha256=lib.sha(decision_path)))
    supplement_path = REVISION/'research/supplemental-controls.decisions.json'
    supplemental = lib.read(supplement_path)['decisions']
    expected_controls = {r['candidate_id'] for r in lib.read(REVISION/'research/additional-current-matches.json')['rows']}
    lib.require({r['id'] for r in supplemental} == expected_controls
                and len(supplemental) == len(expected_controls), 'Incomplete supplemental control review')
    reviews.extend(supplemental)
    research_inputs.append(dict(path=str(supplement_path.relative_to(REVISION)), sha256=lib.sha(supplement_path)))
    for review in reviews:
        review.update(reviewed=True, input_sha256=input_hashes[owners[review['id']]],
                      candidate_record_sha256=lib.digest(cards[review['id']]),
                      acceptance='Coordinator accepted this source-grounded meaning decision for candidate revision only.')
    reviews.sort(key=lambda r: r['id'])
    accepted = dict(schema_version=1, scope='112 offered current-inventory matches; no operational identity migration.',
                    review_files=research_inputs, baseline_index_sha256=manifest['baseline_index_sha256'],
                    decisions=reviews)
    lib.write(REVISION/'reconciliation-decisions.json', accepted)
    correction_path = PILOT/'local-review/card-corrections.json'
    corrections = lib.read(correction_path)
    lib.require(lib.sha(PROJECT/corrections['base_batch_path']) == corrections['base_batch_sha256']
                and lib.sha(PILOT/'catalog.json') == corrections['base_combined_sha256'], 'Stale correction input hashes')
    revised, lineage = lib.revise(originals, reviews, baseline, raw, input_hashes, corrections['corrections'])
    mapping = lineage['legacy_id_redirects']
    lineage.update(reconciliation_decisions_sha256=lib.sha(REVISION/'reconciliation-decisions.json'),
                   source_corrections_sha256=lib.sha(correction_path),
                   pinned_current_baseline_sha256=manifest['baseline_index_sha256'],
                   legacy_redirect_scope='Pilot candidate revision; current operational registry and baseline IDs are preserved.')
    lib.write(REVISION/'revision-lineage.json', lineage)
    for batch in revised:
        bid = batch['batch']['id']
        batch['batch'].update(baseline_index_sha256=manifest['baseline_index_sha256'],
            baseline_imported_records_sha256=manifest['baseline_imported_records_sha256'],
            reconciliation_decisions_sha256=lib.sha(REVISION/'reconciliation-decisions.json'),
            revision_lineage_sha256=lib.sha(REVISION/'revision-lineage.json'),
            original_delivery_path=f'../../archive/scale-pilot-001-delivery/evidence/work/data/catalog-candidates/{bid}.json')
        lib.write(REVISION/f'{bid}.json', batch)
    decisions = lib.read(PILOT/'identity-decisions.json')
    for distinction in decisions['distinctness']:
        distinction['member_ids'] = [mapping.get(cid, cid) for cid in distinction['member_ids']]
        for evidence in distinction['evidence']:
            if 'concept_id' in evidence:
                evidence['concept_id'] = mapping.get(evidence['concept_id'], evidence['concept_id'])
        distinction['canonical_id_reconciliation'] = 'Member IDs updated through the reviewed revision mapping; original meaning evidence preserved.'
    for review in reviews:
        for rejected in review.get('rejected_matches', []):
            pair = [mapping.get(review['id'], review['id']), rejected['id']]
            decisions['distinctness'].append(dict(member_ids=pair, reviewed=True, reason=rejected['reason'],
                                                 evidence=copy.deepcopy(review['evidence'])))
    decisions['revision_reconciliation'] = dict(decisions_path='reconciliation-decisions.json',
        sha256=lib.sha(REVISION/'reconciliation-decisions.json'), applied_legacy_id_redirects=mapping,
        known_current_baseline='baseline-index.json', operational_registry_migrated=False)
    lib.write(REVISION/'identity-decisions.json', decisions)
    spec = importlib.util.spec_from_file_location('revision_combiner', REVISION/'tools/catalog_combiner.py')
    combiner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(combiner)
    paths = [REVISION/f'research-batch-{n:03d}.json' for n in range(3, 8)]
    catalog = combiner.assemble(paths, REVISION/'baseline-index.json', REVISION/'identity-decisions.json', require_all=True)
    lib.write(REVISION/'catalog.json', catalog)
    selections = lib.read(PILOT/'selection-manifest.json')['accepted']
    ownership = {mapping.get(r['id'], r['id']): r for r in selections}
    lib.require(len(ownership) == len(catalog['concepts']), 'Selection ownership must survive remapping')
    concepts = catalog['concepts']
    new = [c for c in concepts if c['id'] not in baseline]
    fine = lambda c: c['scope'] in {'idea', 'facet_or_application'}
    relations = [r for c in concepts for r in c['relations']]
    hierarchy = {'facet_of', 'application_of', 'broader_topic'}
    counts = dict(accepted_distinct_ids=len(concepts), new_identities=len(new),
        existing_identities=len(concepts)-len(new), new_fine_scope_subjects=sum(fine(c) for c in new),
        new_fine_idea_entities=sum(fine(c) and c['entity_kind']=='idea' for c in new),
        new_fine_named_subjects=sum(fine(c) and c['entity_kind']=='named_subject' for c in new),
        named_subjects=sum(c['entity_kind']=='named_subject' for c in concepts),
        scopes=dict(Counter(c['scope'] for c in concepts)),
        primary_domains=dict(Counter(ownership[c['id']]['primary_domain'] for c in concepts)),
        primary_subfields=dict(Counter(ownership[c['id']]['primary_subfield'] for c in concepts)),
        source_records=len(catalog['sources']), distinct_source_urls=len({s['url'] for s in catalog['sources']}),
        source_hostnames=len({urlparse(s['url']).hostname for s in catalog['sources']}),
        relations=len(relations), relationship_types=dict(Counter(r['type'] for r in relations)),
        relationship_assertions=dict(Counter(r['assertion'] for r in relations)),
        word_count_min=min(len(c['card'].split()) for c in concepts),
        word_count_max=max(len(c['card'].split()) for c in concepts),
        cards_without_any_relation=sum(not c['relations'] for c in concepts),
        fine_cards_without_any_parent_application_edge=sum(fine(c) and not any(r['type'] in hierarchy for r in c['relations']) for c in concepts),
        fine_cards_without_source_asserted_parent_application_edge=sum(fine(c) and not any(r['type'] in hierarchy and r['assertion']=='source_asserted' for r in c['relations']) for c in concepts))
    batch_counts = []
    for batch, path in zip(revised, paths):
        cards_for_batch = batch['concepts']
        new_for_batch = [c for c in cards_for_batch if c['id'] not in baseline]
        batch_counts.append(dict(id=batch['batch']['id'], revision=batch['batch']['revision'], sha256=lib.sha(path),
            accepted=len(cards_for_batch), new_identities=len(new_for_batch), existing_identities=len(cards_for_batch)-len(new_for_batch),
            new_fine_scope_subjects=sum(fine(c) for c in new_for_batch),
            new_fine_idea_entities=sum(fine(c) and c['entity_kind']=='idea' for c in new_for_batch)))
    metrics = dict(schema_version=1, status='recomputed_against_full_current_baseline',
        baseline_identity_count_by_id=len(baseline), baseline_index_sha256=manifest['baseline_index_sha256'],
        combined_sha256=lib.sha(REVISION/'catalog.json'), canonical_content_sha256=catalog['validation']['canonical_content_sha256'],
        meaning_review_actions=dict(Counter(r['action'] for r in reviews)),
        applied_id_redirects=len(mapping), changed_record_bundles=len(lineage['changed_records']),
        pilot=counts, batches=batch_counts,
        numerical_goals=dict(new_identity_target=800, new_identity_shortfall=max(0,800-len(new)),
                             new_fine_scope_target=600, new_fine_scope_shortfall=max(0,600-counts['new_fine_scope_subjects'])),
        limits=['Novelty here is identity novelty against the pinned inventory, not novelty to a user.',
                'The 112 targeted meaning reviews and prior sampled source checks do not certify unsampled facts.',
                'No extra cards are generated to repair numerical shortfalls.'])
    lib.write(REVISION/'catalog-metrics.json', metrics)
    inputs = {f'data/catalog-candidates/research-batch-{n:03d}.json': lib.sha(path) for n,path in zip(range(3,8), paths)}
    inputs.update({f'data/catalog-candidates/scale-pilot-001/{name}': lib.sha(REVISION/name)
                   for name in ['baseline-index.json','identity-decisions.json']})
    lib.write(REVISION/'data/catalog-candidates/scale-pilot-001/merge-validation/current-revised-inputs.json',
        dict(schema_version=1, authorization='run_on_final_audited_inputs', expected_sha256=inputs,
             scope='Authorizes mechanics tests on this reviewed candidate revision. Historical full source audits retain their original hash scope.'))
    print({'accepted':len(concepts),'new':len(new),'reused_ids':len(mapping),'changed_bundles':len(lineage['changed_records'])})


if __name__ == '__main__':
    build()
