import unittest
import central_selection as c

class CentralSelectionTests(unittest.TestCase):
    def test_effective_id_uses_reserved_suggestion_over_temporary_proposal_id(self):
        self.assertEqual(c.effective_id({'provisional_id':'proposal:007:1','suggested_id':'local:catalog:one'}),'local:catalog:one')
        self.assertEqual(c.effective_id({'provisional_id':'Q1'}),'Q1')
    def test_recommendation_normalizes_author_schemas_without_accepting_reserves(self):
        for p in [{'selection_status':'proposed'},{'selection_status':'proposed_accept'},{'proposal_status':'recommended'},{'proposal_status':'proposed_accept'},{'recommendation':'accept'}]:self.assertTrue(c.is_recommended(p))
        for p in [{'proposal_status':'reserve'},{'recommendation':'alternate'},{'proposal_status':'unresolved_access'},{'proposal_status':'rejected_duplicate_owner'}]:self.assertFalse(c.is_recommended(p))
    def test_control_keeps_baseline_aliases_and_primary_domain_first(self):
        p={'provisional_id':'Q1','label':'New label','aliases':['extra'],'primary_domain':'A','secondary_domains':['B','A'],'scope':'idea','entity_kind':'idea','learning_takeaway':'A meaning.'}
        x=c.normalize(p,'research-batch-003',{'Q1':{'aliases':['old label'],'label':'Old label'}})
        self.assertEqual(x.get('id'),'Q1');self.assertEqual(x.get('inventory_status'),'existing');self.assertEqual(x.get('domains'),['A','B']);self.assertIn('old label',x.get('aliases',[]))
    def test_new_identity_is_not_marked_existing_by_label_alone(self):
        p={'provisional_id':'local:new','label':'Old label','aliases':[],'primary_domain':'A','secondary_domains':[],'scope':'idea','entity_kind':'idea','learning_takeaway':'A different sense.'}
        self.assertEqual(c.normalize(p,'research-batch-003',{'Q1':{'aliases':['Old label'],'label':'Old label'}}).get('inventory_status'),'new')

if __name__=='__main__':unittest.main()
