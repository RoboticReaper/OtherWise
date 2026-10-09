import copy
import importlib.util
from pathlib import Path
import unittest

TOOL = Path(__file__).resolve().parents[1] / 'tools/reconcile_catalog.py'
spec = importlib.util.spec_from_file_location('reconcile_catalog', TOOL)
lib = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lib)


def card(cid, target=None):
    return dict(id=cid, label='Sample', aliases=['Sample alias'], card='Original card',
                card_version=1, entity_kind='idea', scope='idea', domains=['Science'],
                learning_takeaway='A distinct takeaway', original_description=None,
                imported_records=[], identity_urls=['https://example.org/sample'],
                evidence=[dict(source_id='s1', locator='Definition', note='Support')],
                relations=[] if target is None else [dict(type='related_to', target_id=target,
                    assertion='editorial', source_ids=['s1'], note='Learning bridge')])


class ReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.batches = [dict(schema_version=1, batch=dict(id='research-batch-003', revision=4),
                             sources=[dict(id='s1', url='https://example.org/sample')],
                             concepts=[card('local:new'), card('local:other', 'local:new')],
                             issues=[], validation={})]
        self.hashes = {'research-batch-003': 'original-input-hash'}
        self.baseline = {'Q1': dict(id='Q1', label='Registered sample', aliases=['Registered alias'],
                                   original_description='Imported source wording', latest_card_version=3)}
        self.raw = {'Q1': dict(imported_records=[dict(wikidata_id='Q1', description='Imported source wording')])}
        self.decision = dict(id='local:new', action='reuse_existing', target_id='Q1', reviewed=True,
                             input_sha256=self.hashes['research-batch-003'],
                             candidate_record_sha256=lib.digest(self.batches[0]['concepts'][0]),
                             reason='Inspected same meaning', evidence=[dict(url='https://example.org/sample',
                              locator='Definition', note='Same subject')], proposed_relation=None)

    def run_revision(self, decisions=None, corrections=None):
        return lib.revise(self.batches, [self.decision] if decisions is None else decisions,
                          self.baseline, self.raw, self.hashes, corrections or [])

    def test_reviewed_reuse_rewrites_incoming_edges_preserves_import_and_original(self):
        revised, report = self.run_revision()
        merged, incoming = revised[0]['concepts']
        self.assertEqual(merged['id'], 'Q1')
        self.assertIn('Registered alias', merged['aliases'])
        self.assertEqual(merged['original_description'], 'Imported source wording')
        self.assertEqual(merged['imported_records'], self.raw['Q1']['imported_records'])
        self.assertEqual(merged['card_version'], 4)
        self.assertEqual(incoming['relations'][0]['target_id'], 'Q1')
        self.assertEqual(incoming['card_version'], 2)
        self.assertEqual(report['legacy_id_redirects'], {'local:new': 'Q1'})
        self.assertEqual(report['changed_records'][0]['original_record'], self.batches[0]['concepts'][0])
        self.assertEqual(self.batches[0]['concepts'][0]['id'], 'local:new')

    def test_homonym_review_retains_identity_and_version(self):
        decision = dict(self.decision, action='distinct_meaning', target_id=None)
        revised, report = self.run_revision([decision])
        self.assertEqual(revised[0]['concepts'][0], self.batches[0]['concepts'][0])
        self.assertEqual(report['legacy_id_redirects'], {})

    def test_label_only_or_unresolved_decision_is_rejected(self):
        for decision in [dict(self.decision, reviewed=False), dict(self.decision, evidence=[]),
                         dict(self.decision, action='unresolved')]:
            with self.subTest(decision=decision), self.assertRaises(ValueError):
                self.run_revision([decision])

    def test_stale_record_or_input_hash_is_rejected(self):
        for field in ['candidate_record_sha256', 'input_sha256']:
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.run_revision([dict(self.decision, **{field: 'stale'})])

    def test_missing_registered_target_and_colliding_final_ids_are_rejected(self):
        with self.assertRaises(ValueError):
            self.run_revision([dict(self.decision, target_id='Q999')])
        self.batches[0]['concepts'][1]['id'] = 'Q1'
        with self.assertRaises(ValueError):
            self.run_revision()

    def test_self_edge_after_reuse_is_rejected_for_explicit_review(self):
        self.batches[0]['concepts'][0]['relations'] = [dict(self.batches[0]['concepts'][1]['relations'][0], target_id='Q1')]
        self.decision['candidate_record_sha256'] = lib.digest(self.batches[0]['concepts'][0])
        with self.assertRaises(ValueError):
            self.run_revision()

    def test_correction_applies_once_and_preserves_before_bundle(self):
        before = copy.deepcopy(self.batches[0]['concepts'][1])
        after = dict(before, card='Corrected qualified card', card_version=2)
        correction = dict(id=before['id'], before=before, after=after, additional_sources=[])
        revised, report = self.run_revision(corrections=[correction])
        self.assertEqual(revised[0]['concepts'][1]['card'], after['card'])
        self.assertEqual(revised[0]['concepts'][1]['card_version'], 2)
        self.assertEqual(report['changed_records'][1]['original_record'], before)
        with self.assertRaises(ValueError):
            self.run_revision(corrections=[dict(correction, before=dict(before, card='Stale'))])

    def test_distinct_facet_adds_evidenced_link_without_identity_merge(self):
        proposal = dict(target='Q1', type='application_of', assertion_class='source_asserted',
                        note='Named use of the existing concept', evidence=self.decision['evidence'])
        decision = dict(self.decision, action='distinct_facet', target_id=None, proposed_relation=proposal)
        revised, report = self.run_revision([decision])
        subject = revised[0]['concepts'][0]
        self.assertEqual(subject['id'], 'local:new')
        self.assertEqual(subject['relations'][0]['target_id'], 'Q1')
        self.assertEqual(subject['relations'][0]['source_ids'], ['s1'])
        self.assertEqual(subject['card_version'], 2)
        self.assertEqual(report['legacy_id_redirects'], {})

    def test_repeated_and_reversed_inputs_produce_same_selected_records(self):
        second = dict(self.batches[0], batch=dict(id='research-batch-004', revision=2),
                      concepts=[card('local:third', 'local:new')])
        self.batches.append(second)
        self.hashes['research-batch-004'] = 'second-input-hash'
        first, _ = self.run_revision()
        again, _ = self.run_revision()
        reversed_batches, _ = lib.revise(list(reversed(self.batches)), [self.decision], self.baseline,
                                         self.raw, self.hashes, [])
        self.assertEqual(first, again)
        by_id = lambda batches: {d['batch']['id']: d['concepts'] for d in batches}
        self.assertEqual(by_id(first), by_id(reversed_batches))


if __name__ == '__main__':
    unittest.main()
