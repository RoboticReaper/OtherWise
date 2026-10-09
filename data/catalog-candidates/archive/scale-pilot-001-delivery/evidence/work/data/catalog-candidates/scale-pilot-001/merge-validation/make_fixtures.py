"""Small synthetic fixtures; never researched or counted as pilot cards."""
import copy
import hashlib
import json
from pathlib import Path
HERE = Path(__file__).resolve().parent
F = HERE / 'fixtures'
def save(name, data):
    path = F / name
    path.write_text(json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + '\n')
    return hashlib.sha256(path.read_bytes()).hexdigest()
def source(sid='r1', url='https://example.org/fixture/a', **kw):
    return dict(id=sid, title='Synthetic fixture reference', url=url, locator='Fixture section 1', retrieved_at='2024-04-03T12:34:56+00:00', revision=None, **kw)
def concept(cid, label, **kw):
    d=dict(id=cid, label=label, aliases=[label], entity_kind='idea', scope='idea', domains=['Mathematics'], learning_takeaway='Understand this synthetic mechanism for the labeled fixture only.', card='This synthetic fixture describes a simple mechanism in which a change in one quantity produces a corresponding change in another quantity. Its deliberately explicit explanation supplies enough words to exercise validation without representing a researched catalog card.', original_description=None, identity_urls=['https://example.org/fixture/a'], evidence=[dict(source_id='r1', locator='Fixture section 1', note='Supports the synthetic explanatory claim.')], relations=[], card_version=1, imported_records=[])
    d.update(kw); return d
def batch(bid, concepts, sources=None):
    return dict(schema_version=1, batch=dict(id=bid, revision=1, fixture=True, completion_status='synthetic_fixture', selection_manifest=[]), sources=sources or [source()], concepts=concepts, issues=[], validation={})
empty=dict(schema_version=1, equivalences=[], distinctness=[], unresolved=[], concept_versions={}, batch_versions={})
a=batch('research-batch-003',[concept('fixture:a','Capillarity')])
b=batch('research-batch-004',[concept('fixture:b','Java island',relations=[dict(target_id='baseline:mathematics',type='related_to',source_ids=['r1'],assertion='editorial',note='The fixture uses a baseline target to exercise link resolution.')])],[source(url='https://example.org/fixture/b')])
eq=batch('research-batch-004',[concept('fixture:eq','Capillary action')],[source(url='https://example.org/fixture/equivalence')])
link=batch('research-batch-005',[concept('fixture:link','Linked fixture',relations=[dict(target_id='fixture:eq',type='related_to',source_ids=['r1'],assertion='source_asserted',note='The synthetic passage explicitly connects these fixture subjects.')])])
planet=batch('research-batch-003',[concept('fixture:mercury-planet','Mercury',learning_takeaway='Identify Mercury as a planet rather than the chemical element.')])
element=batch('research-batch-004',[concept('fixture:mercury-element','Mercury',learning_takeaway='Identify Mercury as an element rather than the planet.')])
conflict=batch('research-batch-004',[concept('fixture:a','Capillarity',card_version=2,card='This revised synthetic fixture describes a different mechanism in which a change in one quantity does not produce a corresponding change in another quantity. The incompatible account is retained to require an explicit reviewed version selection before assembly.')])
rev=copy.deepcopy(a); rev['batch']['revision']=2; rev['sources'][0]['revision']='fixture-rev-2'; rev['concepts'][0]['card_version']=2
same_url=copy.deepcopy(b); same_url['sources']=[source(url='https://example.org/fixture/a',retrieval_date='2026-10-08'), source('r2','https://example.org/fixture/a',retrieval_date='2026-10-08')]; same_url['sources'][0]['revision']='revision-A'; same_url['sources'][1]['revision']='revision-B'; same_url['sources'][1]['locator']='Fixture section 2'; same_url['concepts'][0]['evidence'].append(dict(source_id='r2',locator='Fixture section 2',note='Second separately preserved passage supports another premise.'))
bad=copy.deepcopy(a); del bad['concepts'][0]['evidence']
unresolved=copy.deepcopy(a); unresolved['concepts'][0]['relations']=[dict(target_id='fixture:missing',type='related_to',source_ids=['r1'],assertion='editorial',note='This intentionally unresolved target must fail.')]
dup_source=copy.deepcopy(a); dup_source['sources'].append(source(url='https://example.org/fixture/other'))
hashes={}
for name,d in [('a',a),('b',b),('equivalent',eq),('link',link),('planet',planet),('element',element),('conflict',conflict),('revision2',rev),('same-url',same_url),('malformed',bad),('unresolved',unresolved),('duplicate-source',dup_source)]: hashes[name]=save(name+'.json',d)
save('baseline.json',dict(schema_version=1,concepts={'baseline:mathematics':dict(id='baseline:mathematics',label='Mathematics')}))
save('empty-decisions.json',empty)
e=copy.deepcopy(empty); e['equivalences']=[dict(canonical_id='fixture:a',member_ids=['fixture:a','fixture:eq'],reviewed=True,reason='Fixture review verifies the same meaning under two names.',evidence=[dict(url='https://example.org/fixture/equivalence',locator='Fixture section 1',note='Labeled synthetic equivalence evidence.')],selected_card=dict(concept_id='fixture:a',batch_id='research-batch-003',input_sha256=hashes['a'],card_version=1))]; save('equivalence-decisions.json',e)
u=copy.deepcopy(e); u['equivalences'][0]['reviewed']=False; save('proposed-equivalence.json',u)
d=copy.deepcopy(empty); d['distinctness']=[dict(member_ids=['fixture:mercury-planet','fixture:mercury-element'],reviewed=True,reason='Fixture review distinguishes planet and chemical-element senses.',evidence=[dict(url='https://example.org/fixture/mercury',locator='Meaning list',note='The two meanings have separate learning takeaways.')])]; save('distinct-decisions.json',d)
c=copy.deepcopy(empty); c['concept_versions']={'fixture:a':dict(batch_id='research-batch-004',input_sha256=hashes['conflict'],card_version=2,reviewed=True,reason='Reviewer explicitly chooses the revised fixture explanation.')}; save('version-decisions.json',c)
r=copy.deepcopy(empty); r['batch_versions']={'research-batch-003':dict(input_sha256=hashes['revision2'],reviewed=True,reason='Explicitly choose batch revision 2 for this fixture.')}; save('batch-version-decisions.json',r)
u=copy.deepcopy(empty); u['unresolved']=[dict(member_ids=['fixture:a','fixture:b'],reason='An intentionally unresolved semantic-overlap review.')]; save('unresolved-decisions.json',u)
(F/'duplicate-json-key.json').write_text('{"schema_version": 1, "schema_version": 2}\n')
(F/'broken-json.json').write_text('{broken\n')

wrong=copy.deepcopy(c); wrong['concept_versions']['fixture:a']['input_sha256']='0'*64; save('wrong-version-decisions.json',wrong)
short=copy.deepcopy(a); short['concepts'][0]['card']='Too short.'; save('word-budget.json',short)
missing=copy.deepcopy(a); del missing['sources'][0]['retrieved_at']; save('missing-retrieval.json',missing)
unknown=copy.deepcopy(a); unknown['concepts'][0]['evidence'][0]['source_id']='missing'; save('unresolved-source.json',unknown)
nonpilot=copy.deepcopy(a); nonpilot['batch']['id']='research-batch-002'; save('nonpilot.json',nonpilot)
(F/'nan-json.json').write_text('{"schema_version": NaN}\n')

self_link=copy.deepcopy(a); self_link['concepts'][0]['relations']=[dict(target_id='fixture:a',type='related_to',source_ids=['r1'],assertion='editorial',note='This intentionally circular relation must be quarantined.')]; save('self-relation.json',self_link)
eq_self=copy.deepcopy(eq); eq_self['concepts'][0]['relations']=[dict(target_id='fixture:a',type='related_to',source_ids=['r1'],assertion='editorial',note='This would become circular after the reviewed equivalence mapping.')]; save('equivalent-self.json',eq_self)

print(f'Wrote {len(list(F.glob("*.json")))} labeled fixture files.')
