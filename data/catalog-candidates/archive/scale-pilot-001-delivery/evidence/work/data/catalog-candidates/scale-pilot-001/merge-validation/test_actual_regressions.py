"""Test the future actual-output runner with five small synthetic batches only."""
import copy
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
WORK=HERE.parents[3]
RUNNER=HERE/'actual_regression_runner.py'
REL='data/catalog-candidates/scale-pilot-001'
def write(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,sort_keys=True,indent=2)+'\n')
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
class ActualRegressionRunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=HERE/'runs')
        self.root=Path(self.temp.name)
        (self.root/'tools').mkdir()
        shutil.copyfile(WORK/'tools/catalog_combiner.py',self.root/'tools/catalog_combiner.py')
        for num,fixture in [(3,'planet'),(4,'element'),(5,'a'),(6,'b'),(7,'link')]:
            d=json.loads((HERE/'fixtures'/f'{fixture}.json').read_text())
            d['batch']['id']=f'research-batch-{num:03d}'
            if num==7: d['concepts'][0]['relations']=[]
            write(self.root/f'data/catalog-candidates/research-batch-{num:03d}.json',d)
        write(self.root/REL/'baseline-index.json',json.loads((HERE/'fixtures/baseline.json').read_text()))
        write(self.root/REL/'identity-decisions.json',json.loads((HERE/'fixtures/distinct-decisions.json').read_text()))
        self.paths=[f'data/catalog-candidates/research-batch-{n:03d}.json' for n in range(3,8)]+[REL+'/baseline-index.json',REL+'/identity-decisions.json']
        self.manifest=self.root/'expected-inputs.json'
        self.refresh_manifest()
        self.protected=self.root/REL/'catalog.json';self.protected.write_text('FINAL CATALOG SENTINEL\n')
        gate=self.root/REL/'merge-validation/gate-results.json';gate.parent.mkdir(parents=True);gate.write_text('ORIGINAL GATE SENTINEL\n')
    def tearDown(self): self.temp.cleanup()
    def refresh_manifest(self): write(self.manifest,dict(schema_version=1,authorization='run_on_final_audited_inputs',expected_sha256={p:sha(self.root/p) for p in self.paths}))
    def invoke(self,run='fixture'):
        return subprocess.run([sys.executable,str(RUNNER),'--work-root',str(self.root),'--fixture-only','--expected-inputs',str(self.manifest),'--run-id',run],capture_output=True,text=True)
    def test_all_regressions_run_isolated_and_leave_canonical_files_unchanged(self):
        before={p:sha(self.root/p) for p in self.paths}
        p=self.invoke();self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        directory=self.root/REL/'merge-validation/actual-regressions/fixture'
        r=json.loads((directory/'regression-results.json').read_text())
        self.assertEqual(r['status'],'passed');self.assertTrue(r['fixture_only'])
        self.assertEqual(r['failed'],[]);self.assertEqual(r['unrun'],[])
        self.assertEqual({p:sha(self.root/p) for p in self.paths},before)
        self.assertEqual(self.protected.read_text(),'FINAL CATALOG SENTINEL\n')
        self.assertEqual((self.root/REL/'merge-validation/gate-results.json').read_text(),'ORIGINAL GATE SENTINEL\n')
        cases={c['name']:c for c in r['cases']}
        required={'actual_unchanged_reverse_repeat','actual_source_scoping','actual_shared_name_aliases','actual_aliases_and_provenance','forced_local_reference_collision','historical_retrieved_at_only','concept_conflict_quarantine','explicit_concept_version_choice','malformed_input_quarantine','unresolved_target_quarantine','equivalence_mechanics','input_integrity'}
        self.assertEqual(set(cases),required)
        self.assertEqual(cases['actual_unchanged_reverse_repeat']['distinct_concept_count'],5)
        self.assertGreater(cases['actual_shared_name_aliases']['shared_alias_group_count'],0)
        for name in ['concept_conflict_quarantine','malformed_input_quarantine','unresolved_target_quarantine']:
            self.assertTrue(cases[name]['last_valid_retained'])
            self.assertEqual(cases[name]['before_sha256'],cases[name]['after_sha256'])
        eq=cases['equivalence_mechanics'];self.assertEqual(eq['mode'],'synthetic_derived_copy')
        self.assertFalse(eq['counts_toward_research'])
        d=json.loads((directory/'equivalence-mechanics/inputs/research-batch-003.json').read_text())
        self.assertFalse(d['batch']['regression_only']['counts_toward_research'])
    def test_stale_hashes_refuse_to_run_without_writing_artifacts(self):
        path=self.root/self.paths[0];path.write_text(path.read_text()+'\n')
        p=self.invoke();self.assertNotEqual(p.returncode,0)
        self.assertIn('input_hash_mismatch',p.stdout+p.stderr)
        self.assertFalse((self.root/REL/'merge-validation/actual-regressions/fixture').exists())
    def test_existing_run_directory_is_never_overwritten(self):
        d=self.root/REL/'merge-validation/actual-regressions/fixture';d.mkdir(parents=True)
        (d/'sentinel').write_text('keep')
        p=self.invoke();self.assertNotEqual(p.returncode,0)
        self.assertIn('run_directory_exists',p.stdout+p.stderr)
        self.assertEqual(list(d.iterdir()),[d/'sentinel'])
    def test_missing_final_authorization_is_refused(self):
        d=json.loads(self.manifest.read_text());d['authorization']='drafts_in_progress';write(self.manifest,d)
        p=self.invoke();self.assertNotEqual(p.returncode,0)
        self.assertIn('final_input_authorization_required',p.stdout+p.stderr)
    def test_missing_actual_ambiguity_is_disclosed_not_synthetically_claimed(self):
        for n in [3,4]:
            p=self.root/f'data/catalog-candidates/research-batch-{n:03d}.json';d=json.loads(p.read_text())
            d['concepts'][0]['label']=f'Unique label {n}';d['concepts'][0]['aliases']=[];write(p,d)
        self.refresh_manifest();p=self.invoke()
        self.assertEqual(p.returncode,1,p.stdout+p.stderr)
        r=json.loads((self.root/REL/'merge-validation/actual-regressions/fixture/regression-results.json').read_text())
        self.assertEqual(r['status'],'partial');self.assertIn('actual_shared_name_aliases',r['unrun'])
    def test_three_actual_meanings_allow_complete_pairwise_distinctness_reviews(self):
        path=self.root/'data/catalog-candidates/research-batch-005.json';d=json.loads(path.read_text())
        d['concepts'][0]['aliases'].append('Mercury');write(path,d)
        path=self.root/REL/'identity-decisions.json';dec=json.loads(path.read_text())
        for other in ['fixture:mercury-planet','fixture:mercury-element']:
            review=copy.deepcopy(dec['distinctness'][0]);review['member_ids']=['fixture:a',other];dec['distinctness'].append(review)
        write(path,dec);self.refresh_manifest();p=self.invoke()
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
if __name__=='__main__': unittest.main(verbosity=2)
