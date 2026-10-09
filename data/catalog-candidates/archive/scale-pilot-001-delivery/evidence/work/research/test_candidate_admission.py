import unittest,copy
import candidate_admission as a

class CandidateAdmissionTests(unittest.TestCase):
    def fixtures(self):
        c={'id':'local:new','label':'New','aliases':[],'entity_kind':'idea','scope':'idea','domains':['A'],'learning_takeaway':'A test-only takeaway.','card':' '.join(['fixture']*35),'original_description':None,'identity_urls':['https://example.org/subject'],'evidence':[{'source_id':'s','locator':'Section','note':'Fixture claim.'}],'relations':[],'card_version':1,'imported_records':[]}
        approved={'local:new':{'id':'local:new','primary_domain':'A','scope':'idea','entity_kind':'idea'}}
        data={'schema_version':1,'batch':{'id':'research-batch-003'},'sources':[{'id':'s','title':'Fixture','url':'https://example.org/subject','locator':'Section','retrieved_at':'2020-01-01T00:00:00Z','revision':None}],'concepts':[c],'issues':[],'validation':{}}
        return data,approved
    def test_valid_subject_provenance_and_historical_timestamp_pass(self):
        d,p=self.fixtures();self.assertEqual(a.check(d,p,{}, {},{'local:new'},{'A'},True),[])
    def test_new_identity_needs_inspected_subject_url(self):
        d,p=self.fixtures();d['concepts'][0]['identity_urls']=[]
        self.assertIn('new_identity_url',str(a.check(d,p,{}, {},{'local:new'},{'A'},True)))
    def test_unknown_relation_target_rejected(self):
        d,p=self.fixtures();d['concepts'][0]['relations']=[{'target_id':'absent','type':'related_to','assertion':'editorial','source_ids':['s'],'note':'Fixture.'}]
        self.assertIn('unresolved_target',str(a.check(d,p,{}, {},{'local:new'},{'A'},True)))
    def test_control_imports_and_original_description_preserved(self):
        d,p=self.fixtures();c=d['concepts'][0];c.update(id='Q1',aliases=['Old'],original_description='Original.',imported_records=[{'x':1}]);p={'Q1':dict(p['local:new'],id='Q1')}
        base={'Q1':{'aliases':[],'label':'Old','original_description':'Original.','candidate_records':[]}};snap={'Q1':{'imported_records':[{'x':1}]}}
        self.assertEqual(a.check(d,p,base,snap,{'Q1'},{'A'},True),[])
        c['imported_records']=[];self.assertIn('imported_records_changed',str(a.check(d,p,base,snap,{'Q1'},{'A'},True)))
    def test_final_requires_exact_reserved_set(self):
        d,p=self.fixtures();p['local:other']=dict(p['local:new'],id='local:other')
        self.assertIn('reserved_set_mismatch',str(a.check(d,p,{}, {},set(p),{'A'},True)))
        self.assertEqual(a.check(d,p,{}, {},set(p),{'A'},False),[])
