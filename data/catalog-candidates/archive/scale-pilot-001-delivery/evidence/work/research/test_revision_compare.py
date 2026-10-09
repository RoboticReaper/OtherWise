import unittest,copy
from revision_compare import compare
class RevisionCompareTests(unittest.TestCase):
    def data(self):return {'batch':{'revision':1},'sources':[{'id':'s','title':'Old source'}],'concepts':[{'id':'c','card':'Old text','card_version':1,'evidence':[{'source_id':'s'}],'relations':[]}]}
    def test_unchanged_card_keeps_version(self):
        d=self.data();r=compare(d,copy.deepcopy(d));self.assertEqual(r['failures'],[]);self.assertEqual(r['changed_card_ids'],[])
    def test_changed_text_requires_one_version_increment(self):
        a=self.data();b=copy.deepcopy(a);b['concepts'][0]['card']='New text'
        self.assertTrue(compare(a,b)['failures']);b['concepts'][0]['card_version']=2
        self.assertEqual(compare(a,b)['failures'],[]);self.assertEqual(compare(a,b)['changed_card_ids'],['c'])
    def test_source_change_versions_every_affected_card(self):
        a=self.data();b=copy.deepcopy(a);b['sources'][0]['title']='Corrected source'
        self.assertTrue(compare(a,b)['failures']);b['concepts'][0]['card_version']=2
        r=compare(a,b);self.assertEqual(r['failures'],[]);self.assertEqual(r['source_changed_card_ids'],['c'])
    def test_extra_version_without_record_or_source_change_is_flagged(self):
        a=self.data();b=copy.deepcopy(a);b['concepts'][0]['card_version']=2
        self.assertTrue(compare(a,b)['failures'])
