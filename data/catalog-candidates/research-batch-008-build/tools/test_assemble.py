import copy
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('batch008_assemble', HERE/'assemble.py')
lib = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lib)
FIXTURES = HERE.parents[1]/'scale-pilot-001/revision-002/data/catalog-candidates/scale-pilot-001/merge-validation/fixtures'


class AssemblyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.doc = json.loads((FIXTURES/'a.json').read_text())
        self.doc['batch']['id'] = 'research-batch-008-science'
        self.baseline = self.root/'baseline.json'
        self.baseline.write_text(json.dumps({'concepts': {'baseline:mathematics': {'latest_card_version': 0}}}))
        cid = self.doc['concepts'][0]['id']
        self.approval = {'schema_version':1,'baseline_index_sha256':lib.sha(self.baseline),'accepted':[{'id':cid,'owner':'science','inventory_status':'proposed_new',
            'approved':True,'identity_reason':'Inspected distinct subject','discovery_evidence':[{
                'url':'https://example.org/source','locator':'Definition','note':'Meaning'}]}]}
        self.approval_path = self.root/'approved.json'
        self.approval_path.write_text(json.dumps(self.approval))
        self.doc['batch']['global_selection_manifest_sha256'] = lib.sha(self.approval_path)
        self.doc['batch']['baseline_index_sha256'] = lib.sha(self.baseline)
        self.path = self.root/'science.json'
        self.save()
        self.decisions = self.root/'decisions.json'
        self.decisions.write_text(json.dumps({'schema_version':1,'equivalences':[],'distinctness':[],
             'unresolved':[],'concept_versions':{},'batch_versions':{}}))

    def tearDown(self):
        self.temp.cleanup()

    def save(self):
        self.path.write_text(json.dumps(self.doc))

    def assemble(self, paths=None):
        return lib.assemble(paths or [self.path], self.baseline, self.decisions, self.approval_path)

    def test_repeat_import_retains_one_record_and_identical_snapshot(self):
        first = self.assemble()
        repeated = self.assemble([self.path,self.path])
        self.assertEqual(first,repeated)
        self.assertEqual(len(first['concepts']),1)
        self.assertEqual(first['batch']['input_provenance'][0]['candidate_snapshot'],self.doc)

    def test_unreserved_or_unreviewed_identity_is_rejected(self):
        self.doc['concepts'][0]['id'] = 'local:unreserved';self.save()
        with self.assertRaises(ValueError): self.assemble()
        self.doc['concepts'][0]['id'] = self.approval['accepted'][0]['id']
        self.approval['accepted'][0]['approved'] = False
        self.approval_path.write_text(json.dumps(self.approval))
        self.doc['batch']['global_selection_manifest_sha256'] = lib.sha(self.approval_path);self.save()
        with self.assertRaises(ValueError): self.assemble()

    def test_changed_reservation_hash_is_rejected(self):
        self.approval_path.write_text(json.dumps(dict(self.approval,revision=2)))
        with self.assertRaises(ValueError): self.assemble()

    def test_changed_pinned_baseline_is_rejected_even_without_new_id_collisions(self):
        self.baseline.write_text(json.dumps({'concepts': {'baseline:mathematics': {'latest_card_version': 1}}}))
        with self.assertRaises(ValueError): self.assemble()

    def test_assigned_owner_cannot_be_replaced_by_another_researcher(self):
        self.approval['accepted'][0]['owner']='systems'
        self.approval_path.write_text(json.dumps(self.approval))
        self.doc['batch']['global_selection_manifest_sha256']=lib.sha(self.approval_path);self.save()
        with self.assertRaises(ValueError):self.assemble()

    def test_control_cannot_be_mislabeled_new_or_reuse_stale_version(self):
        cid=self.doc['concepts'][0]['id']
        self.baseline.write_text(json.dumps({'concepts': {cid: {'latest_card_version': 3}}}))
        self.approval['baseline_index_sha256']=lib.sha(self.baseline)
        self.approval_path.write_text(json.dumps(self.approval))
        self.doc['batch']['global_selection_manifest_sha256']=lib.sha(self.approval_path)
        self.doc['batch']['baseline_index_sha256']=lib.sha(self.baseline);self.save()
        with self.assertRaises(ValueError):self.assemble()
        self.approval['accepted'][0]['inventory_status']='existing'
        self.approval_path.write_text(json.dumps(self.approval))
        self.doc['batch']['global_selection_manifest_sha256']=lib.sha(self.approval_path);self.save()
        with self.assertRaises(ValueError):self.assemble()
        self.doc['concepts'][0]['card_version']=4;self.save()
        self.assertEqual(self.assemble()['concepts'][0]['card_version'],4)

    def test_unknown_shard_is_rejected_and_input_bytes_remain_unchanged(self):
        self.doc['batch']['id']='research-batch-999';self.save();before=self.path.read_bytes()
        with self.assertRaises(ValueError):self.assemble()
        self.assertEqual(before,self.path.read_bytes())

    def test_dangling_target_quarantines_without_replacing_last_valid_output(self):
        output=self.root/'candidate.json';report=self.root/'report.json'
        command=[sys.executable,str(HERE/'assemble.py'),'--inputs',str(self.path),'--baseline',str(self.baseline),
                 '--decisions',str(self.decisions),'--approved',str(self.approval_path),
                 '--output',str(output),'--report',str(report)]
        good=subprocess.run(command,capture_output=True,text=True)
        self.assertEqual(good.returncode,0,good.stderr)
        before=output.read_bytes()
        self.doc['concepts'][0]['relations']=[dict(type='related_to',target_id='missing:target',
            assertion='editorial',source_ids=['r1'],note='Regression-only unresolved target')];self.save()
        bad=subprocess.run(command,capture_output=True,text=True)
        self.assertNotEqual(bad.returncode,0)
        data=json.loads(report.read_text())
        self.assertEqual(data['status'],'quarantined')
        self.assertTrue(data['last_valid_output_retained'])
        self.assertEqual(output.read_bytes(),before)

    def test_reversed_independent_shards_keep_identical_content(self):
        other=json.loads((FIXTURES/'b.json').read_text());other['batch']['id']='research-batch-008-systems'
        self.approval['accepted'].append(dict(self.approval['accepted'][0],id=other['concepts'][0]['id'],owner='systems'))
        self.approval_path.write_text(json.dumps(self.approval));h=lib.sha(self.approval_path)
        self.doc['batch']['global_selection_manifest_sha256']=h;self.save()
        other['batch']['global_selection_manifest_sha256']=h
        other['batch']['baseline_index_sha256']=lib.sha(self.baseline)
        second=self.root/'systems.json';second.write_text(json.dumps(other))
        first=self.assemble([self.path,second]);reverse=self.assemble([second,self.path])
        self.assertEqual(first,reverse)


if __name__=='__main__':unittest.main()
