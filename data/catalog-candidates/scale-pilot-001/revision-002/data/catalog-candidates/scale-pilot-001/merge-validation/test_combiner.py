"""Real CLI contract tests. Removing any corresponding check must fail a case."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
HERE = Path(__file__).resolve().parent
WORK = HERE.parents[3]
TOOL = WORK / 'tools/catalog_combiner.py'
FIX = HERE / 'fixtures'
class CombinerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=HERE/'runs')
        self.root=Path(self.temp.name)
        self.output=self.root/'catalog.json'
        self.report=self.root/'report.json'
    def tearDown(self): self.temp.cleanup()
    def run_cli(self,names,decisions='empty-decisions',command='combine',extra=()):
        args=[sys.executable,str(TOOL),command,'--inputs',*[str(FIX/(x+'.json')) for x in names],'--baseline',str(FIX/'baseline.json'),'--decisions',str(FIX/(decisions+'.json')),'--output',str(self.output),'--report',str(self.report),*extra]
        p=subprocess.run(args,text=True,capture_output=True)
        return p
    def good(self,names,decisions='empty-decisions',command='combine',extra=()):
        p=self.run_cli(names,decisions,command,extra)
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        return json.loads(self.output.read_text())
    def expect_quarantine(self,names,code,decisions='empty-decisions'):
        p=self.run_cli(names,decisions)
        self.assertNotEqual(p.returncode,0)
        self.assertTrue(self.report.exists(),p.stdout+p.stderr)
        r=json.loads(self.report.read_text())
        self.assertEqual(r['status'],'quarantined')
        self.assertIn(code,[x['code'] for x in r['errors']])
        self.assertTrue(Path(r['quarantine_path']).exists())
        return r
    def test_repeated_import_is_idempotent(self):
        a=self.good(['a','b']); original=self.output.read_bytes()
        b=self.good(['a','b','a'])
        self.assertEqual(original,self.output.read_bytes())
        self.assertEqual(a['validation']['canonical_content_sha256'],b['validation']['canonical_content_sha256'])
        self.assertEqual((len(b['concepts']),len(b['sources'])),(2,2))
    def test_reversed_input_order_same_content_and_decisions(self):
        a=self.good(['a','b']); b=self.good(['b','a'])
        self.assertEqual(a,b)
    def test_reviewed_equivalence_keeps_aliases_full_provenance_and_rewrites_targets(self):
        x=self.good(['a','equivalent','link'],'equivalence-decisions')
        self.assertEqual(len(x['concepts']),2)
        c=next(c for c in x['concepts'] if c['id']=='fixture:a')
        self.assertEqual(set(c['aliases']),{'Capillarity','Capillary action'})
        self.assertEqual({e['source_id'] for e in c['evidence']},{'research-batch-003::r1','research-batch-004::r1'})
        self.assertEqual(len(x['batch']['concept_provenance']['fixture:a']),2)
        self.assertEqual(next(c for c in x['concepts'] if c['id']=='fixture:link')['relations'][0]['target_id'],'fixture:a')
        self.assertEqual(x,self.good(['link','equivalent','a'],'equivalence-decisions'))
    def test_similar_names_do_not_make_unreviewed_equivalence_accepted(self):
        self.expect_quarantine(['a','equivalent'],'unreviewed_equivalence','proposed-equivalence')
    def test_same_name_distinct_meanings_retains_all_alias_matches(self):
        x=self.good(['planet','element'],'distinct-decisions')
        self.assertEqual(x['batch']['alias_index']['mercury'],['fixture:mercury-element','fixture:mercury-planet'])
        self.assertEqual(len(x['concepts']),2)
    def test_ambiguous_alias_without_review_is_quarantined(self):
        self.expect_quarantine(['planet','element'],'unreviewed_alias_collision')
    def test_batch_scoped_sources_rewrite_evidence_and_relation_links(self):
        x=self.good(['a','b'])
        self.assertEqual({s['id'] for s in x['sources']},{'research-batch-003::r1','research-batch-004::r1'})
        c=next(c for c in x['concepts'] if c['id']=='fixture:b')
        self.assertEqual(c['evidence'][0]['source_id'],'research-batch-004::r1')
        self.assertEqual(c['relations'][0]['source_ids'],['research-batch-004::r1'])
        self.assertEqual(next(s for s in x['sources'] if s['id']=='research-batch-004::r1')['original_id'],'r1')
    def test_same_url_revisions_and_passages_preserved(self):
        x=self.good(['a','same-url'])
        self.assertEqual(len(x['sources']),3)
        self.assertEqual({s['revision'] for s in x['sources']},{None,'revision-A','revision-B'})
        self.assertIn('Fixture section 2',[s['locator'] for s in x['sources']])
    def test_historical_timestamp_without_date_preserved(self):
        x=self.good(['a']); s=x['sources'][0]
        self.assertNotIn('retrieval_date',s)
        self.assertEqual(s['retrieved_at'],'2024-04-03T12:34:56+00:00')
    def test_conflicting_concept_quarantines_and_retains_last_valid_bytes(self):
        self.good(['a']); before=self.output.read_bytes()
        r=self.expect_quarantine(['a','conflict'],'concept_conflict')
        self.assertEqual(self.output.read_bytes(),before)
        self.assertTrue(r['last_valid_output_retained'])
    def test_explicit_hash_bound_version_choice_works_in_both_orders(self):
        a=self.good(['a','conflict'],'version-decisions')
        self.assertEqual(a['concepts'][0]['card_version'],2)
        self.assertEqual(len(a['batch']['concept_provenance']['fixture:a']),2)
        self.assertEqual(a,self.good(['conflict','a'],'version-decisions'))
    def test_competing_batch_revisions_require_explicit_choice(self):
        self.expect_quarantine(['a','revision2'],'batch_revision_conflict')
        x=self.good(['a','revision2'],'batch-version-decisions')
        self.assertEqual(x['sources'][0]['revision'],'fixture-rev-2')
        self.assertEqual(len(x['batch']['input_provenance']),2)
    def test_malformed_input_and_duplicate_json_keys_do_not_replace_output(self):
        self.good(['a']); before=self.output.read_bytes()
        for fixture,code in [('malformed','missing_field'),('broken-json','malformed_json'),('duplicate-json-key','malformed_json')]:
            with self.subTest(fixture=fixture):
                self.expect_quarantine([fixture],code)
                self.assertEqual(self.output.read_bytes(),before)
    def test_unresolved_target_quarantines_but_pinned_baseline_target_resolves(self):
        x=self.good(['b']); before=self.output.read_bytes()
        self.expect_quarantine(['unresolved'],'unresolved_target')
        self.assertEqual(self.output.read_bytes(),before)
        self.assertNotIn('baseline:mathematics',[c['id'] for c in x['concepts']])
    def test_unresolved_semantic_overlap_with_different_ids_quarantines(self):
        self.expect_quarantine(['a','b'],'unresolved_identity','unresolved-decisions')
    def test_local_source_id_conflict_is_not_silently_overwritten(self):
        self.expect_quarantine(['duplicate-source'],'duplicate_source_id')
    def test_actual_output_verification_runs_repeat_reverse_and_resolution(self):
        self.good(['a','b'],command='verify-actual')
        r=json.loads(self.report.read_text())
        self.assertEqual(r['status'],'passed')
        self.assertEqual(set(r['passed']),{'structural_validation','reversed_input_order','repeated_import','source_and_target_resolution','pilot_only_concepts'})
        self.assertEqual(r['failed'],[])
        self.assertEqual(r['unrun'],[])
    def test_actual_all_five_batch_requirement_cannot_be_mislabeled_complete(self):
        p=self.run_cli(['a','b'],command='verify-actual',extra=['--require-all-batches'])
        self.assertNotEqual(p.returncode,0)
        self.assertTrue(self.report.exists(),p.stdout+p.stderr)
        self.assertIn('missing_pilot_batches',[e['code'] for e in json.loads(self.report.read_text())['errors']])
    def test_original_snapshots_have_explicit_reference_namespaces(self):
        x=self.good(['a','b'])
        item=x['batch']['input_provenance'][0]
        self.assertIn('reference_namespace',item)
        self.assertEqual(item['reference_namespace']['batch_id'],'research-batch-003')
        self.assertEqual(item['reference_namespace']['input_sha256'],item['input_sha256'])
        self.assertEqual(item['candidate_snapshot']['concepts'][0]['evidence'][0]['source_id'],'r1')
        p=x['batch']['concept_provenance']['fixture:a'][0]
        self.assertEqual(p['reference_namespace'],item['reference_namespace'])
        self.assertEqual(p['combined_source_id_map']['r1'],'research-batch-003::r1')
    def test_verify_actual_detects_changed_existing_combined_artifact(self):
        self.good(['a','b'])
        x=json.loads(self.output.read_text()); x['concepts'][0]['label']='Unexpected changed label'
        self.output.write_text(json.dumps(x))
        before=self.output.read_bytes()
        p=self.run_cli(['a','b'],command='verify-actual')
        self.assertNotEqual(p.returncode,0)
        r=json.loads(self.report.read_text())
        self.assertIn('existing_output_mismatch',[e['code'] for e in r['errors']])
        self.assertEqual(self.output.read_bytes(),before)
    def test_invalid_version_choice_cannot_match_a_different_artifact(self):
        self.expect_quarantine(['a','conflict'],'invalid_version_choice','wrong-version-decisions')
    def test_structural_constraints_fail_closed(self):
        for fixture,code in [('word-budget','word_budget'),('missing-retrieval','missing_acquisition_metadata'),('unresolved-source','unresolved_source'),('nonpilot','nonpilot_batch'),('nan-json','malformed_json')]:
            with self.subTest(fixture=fixture): self.expect_quarantine([fixture],code)
    def test_direct_self_relation_is_quarantined(self):
        self.expect_quarantine(['self-relation'],'self_relation')
    def test_equivalence_created_self_relation_is_quarantined(self):
        self.expect_quarantine(['a','equivalent-self'],'self_relation','equivalence-decisions')
    def test_baseline_snapshot_count_does_not_mislabel_control_id(self):
        x=self.good(['a'])
        self.assertNotIn('baseline_concepts_emitted',x['validation'])
        self.assertEqual(x['validation']['baseline_snapshot_records_added'],0)
if __name__=='__main__': unittest.main(verbosity=2)
