"""Production guards: reject overwrites/bad evidence, preserve a last valid file."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from assemble import assemble, publish, Rejected


class ProductionAssemblyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.baseline = self.root/'baseline.json'
        self.approved = self.root/'approved.json'
        self.decisions = self.root/'decisions.json'
        self.input = self.root/'shard.json'
        self.output = self.root/'candidate.json'
        self.report = self.root/'report.json'
        self.base = {'schema_version': 1, 'concepts': {
            'Q1': {'id': 'Q1', 'label': 'Example', 'aliases': [],
                   'original_description': 'Imported wording', 'inventory_records': [{'raw': 'kept'}], 'candidate_records': []},
            'Q2': {'id': 'Q2', 'label': 'Parent', 'aliases': [], 'candidate_records': []}}}
        self.selection = {'schema_version': 1, 'batch_id': 'research-batch-009',
            'prior_accepted_ids': [], 'accepted': [{'id': 'Q1', 'owner': 'science',
            'approved': True, 'identity_reason': 'Verified source subject',
            'scope': 'idea', 'entity_kind': 'idea', 'primary_domain': 'Mathematics',
            'discovery_evidence': [{'url': 'https://example.org/source', 'locator': 'Definition'}]}]}
        self.shard = {'schema_version': 1, 'batch': {'id': 'research-batch-009-science', 'revision': 1},
            'sources': [{'id': 's1', 'title': 'Reference', 'url': 'https://example.org/source',
                'locator': 'Definition', 'revision': None, 'retrieved_at': '2026-10-08T12:00:00Z',
                'inspection_mode': 'text inspection'}],
            'concepts': [{'id': 'Q1', 'label': 'Example', 'aliases': [], 'entity_kind': 'idea',
                'scope': 'idea', 'domains': ['Mathematics'], 'learning_takeaway': 'A useful distinction.',
                'card': 'An explanation preserves its necessary condition.', 'original_description': 'Imported wording',
                'identity_urls': [], 'evidence': [{'source_id': 's1', 'locator': 'Definition', 'note': 'Supports the claim.'}],
                'relations': [{'target_id': 'Q2', 'type': 'broader_topic', 'source_ids': ['s1'],
                    'assertion': 'source_asserted', 'note': 'Source places the idea under this field.'}],
                'card_version': 1, 'imported_records': [{'raw': 'kept'}]}], 'issues': [], 'validation': {}}
        self.write(self.decisions, {'schema_version': 1, 'equivalences': [], 'distinctness': [],
            'unresolved': [], 'batch_versions': {}, 'concept_versions': {}})
        self.sync()

    def write(self, path, value):
        path.write_text(json.dumps(value, sort_keys=True))

    def sync(self):
        self.write(self.baseline, self.base)
        self.selection['baseline_index_sha256'] = hashlib.sha256(self.baseline.read_bytes()).hexdigest()
        self.write(self.approved, self.selection)
        self.shard['batch']['baseline_index_sha256'] = self.selection['baseline_index_sha256']
        self.shard['batch']['global_selection_manifest_sha256'] = hashlib.sha256(self.approved.read_bytes()).hexdigest()
        self.write(self.input, self.shard)

    def run_assemble(self, paths=None):
        return assemble(paths or [self.input], self.baseline, self.decisions, self.approved)

    def test_twenty_five_words_accepted_and_repeated_input_is_idempotent(self):
        self.shard['concepts'][0]['card'] = ' '.join(['word']*25)
        self.sync()
        actual = self.run_assemble()
        self.assertEqual(actual, self.run_assemble([self.input, self.input]))
        self.assertEqual(len(actual['concepts']), 1)

    def test_twenty_six_words_rejected(self):
        self.shard['concepts'][0]['card'] = ' '.join(['word']*26)
        self.sync()
        with self.assertRaises(Rejected): self.run_assemble()

    def test_audit_repair_can_advance_a_new_card_version(self):
        self.shard['concepts'][0]['card_version'] = 2
        self.shard['batch']['repair_history'] = [{'id': 'Q1', 'prior_version': 1, 'card_version': 2,
            'reason': 'Retain a condition identified by the independent audit.',
            'initial_snapshot_sha256': 'a'*64}]
        self.sync()
        self.assertEqual(self.run_assemble()['concepts'][0]['card_version'], 2)

    def test_version_advance_without_repair_history_rejected(self):
        self.shard['concepts'][0]['card_version'] = 2
        self.sync()
        with self.assertRaises(Rejected): self.run_assemble()

    def test_existing_description_cannot_be_rewritten(self):
        self.base['concepts']['Q1']['candidate_records'] = [{'record': {'card': 'A longer legacy card.', 'card_version': 1}}]
        self.sync()
        with self.assertRaises(Rejected): self.run_assemble()

    def test_previous_production_card_cannot_be_counted_twice(self):
        self.selection['prior_accepted_ids'] = ['Q1']
        self.sync()
        with self.assertRaises(Rejected): self.run_assemble()

    def test_original_import_cannot_be_silently_changed(self):
        self.shard['concepts'][0]['original_description'] = 'Changed'
        self.sync()
        with self.assertRaises(Rejected): self.run_assemble()

    def test_unknown_relationship_target_rejected(self):
        self.shard['concepts'][0]['relations'][0]['target_id'] = 'unknown'
        self.sync()
        with self.assertRaises(Rejected): self.run_assemble()

    def test_stale_selection_rejected(self):
        self.base['concepts']['Q2']['label'] = 'Changed baseline'
        self.write(self.baseline, self.base)
        with self.assertRaises(Rejected): self.run_assemble()

    def test_failed_publication_retains_last_valid_candidate(self):
        publish([self.input], self.baseline, self.decisions, self.approved, self.output, self.report)
        prior = self.output.read_bytes()
        self.shard['concepts'][0]['evidence'][0]['source_id'] = 'missing'
        self.sync()
        with self.assertRaises(Rejected):
            publish([self.input], self.baseline, self.decisions, self.approved, self.output, self.report)
        self.assertEqual(self.output.read_bytes(), prior)
        self.assertTrue(json.loads(self.report.read_text())['last_valid_output_retained'])


if __name__ == '__main__': unittest.main()
