import importlib.util, unittest, hashlib, json, tempfile
from pathlib import Path

SPEC=importlib.util.spec_from_file_location('audit_freeze',Path(__file__).with_name('audit_freeze.py'))
MODULE=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

class AuditFreezeTests(unittest.TestCase):
    def test_random_sample_uses_prescribed_sha256_rule(self):
        ids=[f'id:{i}' for i in range(80)]
        seed='OtherWise-scale-pilot-001:research-batch-003:source-audit'
        expected=sorted(ids,key=lambda cid:hashlib.sha256((seed+'\n'+cid).encode()).hexdigest())[:20]
        self.assertEqual(MODULE.sample_random(ids,seed,20),expected)

    def test_random_sample_is_order_independent_and_unique(self):
        ids=[f'id:{i}' for i in range(30)]
        self.assertEqual(MODULE.sample_random(ids,'seed',20),MODULE.sample_random(list(reversed(ids))+ids,'seed',20))
        self.assertEqual(len(set(MODULE.sample_random(ids,'seed',20))),20)

    def test_partial_sample_does_not_invent_ids(self):
        self.assertEqual(set(MODULE.sample_random(['a','b'],'seed',20)),{'a','b'})

    def test_risk_sample_is_disjoint_and_reports_reasons(self):
        cards=[dict(id=f'id:{i}',entity_kind='named_subject' if i%2 else 'idea',scope=['broad_field','topic','idea','facet_or_application'][i%4],domains=['A' if i%2 else 'B'],relations=[{'assertion':'source_asserted'}],card='Under a simplified model, this effect may change.',evidence=[{'source_id':f's:{i}'}]) for i in range(60)]
        chosen=MODULE.sample_risk(cards,{f'id:{i}' for i in range(20)},20)
        self.assertEqual(len(chosen),20)
        self.assertEqual(len({r['id'] for r in chosen}),20)
        self.assertTrue(all(r['id'] not in {f'id:{i}' for i in range(20)} and r['reason'] for r in chosen))
        self.assertEqual({r['scope'] for r in chosen},{'broad_field','topic','idea','facet_or_application'})

    def test_freeze_is_write_once_and_preserves_exact_candidate(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);candidate=root/'candidate.json';baseline=root/'baseline.json';selection=root/'selection.json'
            cards=[dict(id=f'id:{i}',label=f'Label {i}',entity_kind='idea',scope='idea',domains=['A'],relations=[],card='An example with a qualified mechanism.',evidence=[{'source_id':'s'}]) for i in range(50)]
            candidate.write_text(json.dumps({'batch':{'id':'research-batch-003'},'concepts':cards,'sources':[{'id':'s'}]}))
            baseline.write_text(json.dumps({'concepts':{'id:0':{}}}));selection.write_text('{}')
            out=root/'audit'
            result=MODULE.freeze_candidate(candidate,baseline,selection,out)
            self.assertIsInstance(result,dict)
            self.assertEqual(result['pre_audit_candidate_sha256'],hashlib.sha256(candidate.read_bytes()).hexdigest())
            self.assertEqual((out/'candidate.before-audit.json').read_bytes(),candidate.read_bytes())
            self.assertEqual(len(result['random_sample_ids']),20)
            self.assertEqual(len(result['risk_sample']),20)
            self.assertNotIn('id:0',result['random_sample_ids'])
            self.assertEqual(MODULE.freeze_candidate(candidate,baseline,selection,out),result)
            candidate.write_text(candidate.read_text()+' ')
            with self.assertRaises(ValueError):MODULE.freeze_candidate(candidate,baseline,selection,out)

if __name__=='__main__':unittest.main()
