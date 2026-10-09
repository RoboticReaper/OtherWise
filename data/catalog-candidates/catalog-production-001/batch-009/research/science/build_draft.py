"""Serialize manually authored cards; never retrieves sources or calls AI APIs."""
import collections
import copy
import hashlib
import json
import pathlib

ROOT = pathlib.Path('data/catalog-candidates/catalog-production-001')
OUT = ROOT / 'batch-009/research/science'
read = lambda name: json.loads((OUT / name).read_text())
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
baseline = json.loads((ROOT / 'baseline-index.json').read_text())
approved = read('approved-selection.json')
proposals = read('proposals.json')
cards = read('draft-cards.json')
reservations = approved['accepted']
assert set(cards) == {p['id'] for p in reservations}
assert sha(ROOT/'baseline-index.json') == approved['baseline_index_sha256']
assert approved['global_selection_manifest_sha256'] == '4802e1cc037ce1b0d47479801236fce29b3c759b466c8f1011b3a4c3438b86b8'
for cid, card in cards.items():
    assert 1 <= len(card.split()) <= 25, (cid, len(card.split()))

inspection = read('sources-inspected.json')
sources = copy.deepcopy(inspection['sources'])
draft_reads = {
    'science-042': ('Ship sandglass and fixed timing, lines 185-187; counting knots, line 207', ['turn739view2']),
    'science-045': ('Introduction and counted-thread definition, lines 34-37; Blackwork, line 45', ['turn739view0']),
    'science-046': ('Quilting definition and layer stitching, lines 35-48; patchwork, lines 59-61', ['turn739view1', 'turn740view0']),
}
for s in sources:
    if s['id'] in draft_reads:
        loc, refs = draft_reads[s['id']]
        entry = dict(inspected_at='2026-10-09T04:55:08Z', inspection_mode='web_open_text', locator=loc, tool_refs=refs)
        if entry not in s.setdefault('additional_inspections', []):
            s['additional_inspections'].append(entry)
        s['tool_refs'] = list(dict.fromkeys(s['tool_refs'] + refs))
        if s['id']=='science-045':
            s['revision'] = 'Last updated 2024-04-17'

concepts = []
for p in reservations:
    cid = p['id']
    b = baseline['concepts'][cid]
    assert not b.get('candidate_records') and not b.get('latest_card')
    evidence = [dict(source_id=e['source_id'], locator=e['locator'], note=e['support_note']) for e in p['discovery_evidence']]
    if cid=='Q38933':
        evidence = [e for e in evidence if e['source_id']=='science-069']
    if cid=='local:authored:000343':
        evidence[0]['locator'] = 'Introduction and counted-thread definition, lines 34-37; Blackwork, line 45'
    if cid=='Q12124':
        evidence[0]['locator'] = 'Red supergiant, line 298; 2019 surface mass ejection, lines 326-330'
    if cid=='Q2469':
        evidence[0]['locator'] = 'Halo and spiral galaxy, lines 312-318; background-quasar absorption, lines 319-324'
    identity_urls = [r['source_url'] for r in b.get('inventory_records', []) if r.get('source_url', '').startswith(('http://','https://'))]
    if not identity_urls:
        identity_urls = [p['discovery_evidence'][0]['url']]
    concepts.append(dict(id=cid,label='pH' if cid=='Q40936' else p['label'],aliases=p['aliases'],entity_kind=p['entity_kind'],scope=p['scope'],domains=[p['primary_domain']]+[d for d in b['domains'] if d!=p['primary_domain']],learning_takeaway=p['learning_takeaway'],card=cards[cid],original_description=b['original_description'],identity_urls=list(dict.fromkeys(identity_urls)),evidence=evidence,relations=[copy.deepcopy(p['proposed_parent'])] if p['proposed_parent'] else [],card_version=1,imported_records=copy.deepcopy(b.get('inventory_records',[]))))
used = {e['source_id'] for c in concepts for e in c['evidence']}
used |= {sid for c in concepts for r in c['relations'] for sid in r['source_ids']}
candidate_sources=[]
for s in sources:
    if s['id'] not in used:
        continue
    r=copy.deepcopy(s)
    r['retrieved_at']=s['inspected_at']
    r['retrieval_date']=s['inspected_at'][:10]
    r['acquisition']=dict(local_inspection_checkpoint=s['inspected_at'],remote_retrieval_timestamp=None,time_basis=s['time_basis'])
    candidate_sources.append(r)
counts=[len(c['card'].split()) for c in concepts]
fine=[c for c in concepts if c['scope'] in ['idea','facet_or_application']]
parents=[c for c in fine if any(r['type'] in ['broader_topic','facet_of','application_of'] for r in c['relations'])]
candidate=dict(schema_version=1,batch=dict(id='research-batch-009-science',revision=1,assignment='science',date='2026-10-08',updated_at='2026-10-09T04:55:08Z',language='en',target_count=70,status='draft_author_check',completion_status='bodies_drafted_author_checks_pending',baseline_index_sha256=approved['baseline_index_sha256'],global_selection_manifest_sha256=approved['global_selection_manifest_sha256'],approved_selection_path=str(OUT/'approved-selection.json'),approved_selection_sha256=sha(OUT/'approved-selection.json'),selection_input_snapshots={'proposals':{'path':str(OUT/'proposals.json'),'sha256':sha(OUT/'proposals.json')}},word_budget={'minimum':1,'maximum':25},word_counting='Whitespace-separated body words; titles and sources excluded.',source_acquisition_policy={'maximum_attempts_per_url':2,'maximum_alternative_sources_after_failure':3,'inspection_requirement':'Actual passage text; search snippets are not substantive evidence.','time_basis':'Local UTC checkpoints after actual reads; remote acquisition times unavailable.'},source_word_budget_path=str(OUT/'source-word-budgets.json'),concept_ownership_and_subfields={p['id']:{'owner':'science','primary_domain':p['primary_domain'],'primary_subfield':p['primary_subfield']} for p in reservations},excluded_alternative_ids=['Q3001783','Q624580','Q175751'],graph_gaps=[c['id'] for c in fine if c not in parents],preserve_existing_cards=True,authoring='Source-grounded drafting in this session; local scripts only serialize and verify artifacts.',external_ai_api_calls=0,token_usage=None,cost_usage=None),sources=candidate_sources,concepts=concepts,issues=copy.deepcopy(proposals['issues']),validation=dict(status='draft_author_check',concept_count=len(concepts),domain_counts=dict(collections.Counter(c['domains'][0] for c in concepts)),scope_counts=dict(collections.Counter(c['scope'] for c in concepts)),named_count=sum(c['entity_kind']=='named_subject' for c in concepts),source_count=len(candidate_sources),relation_count=sum(len(c['relations']) for c in concepts),word_count_min=min(counts),word_count_max=max(counts),card_word_range=[min(counts),max(counts)],fine_scope_count=len(fine),fine_scope_with_parent_or_application=len(parents),fine_scope_source_asserted_parent_or_application=sum(any(r['type'] in ['broader_topic','facet_of','application_of'] and r['assertion']=='source_asserted' for r in c['relations']) for c in parents),original_imports='exact frozen baseline rows',author_review_count=0,independent_audit='pending',external_ai_api_calls=0,token_usage=None,cost_usage=None))
(OUT/'candidate.json').write_text(json.dumps(candidate,ensure_ascii=False,indent=2)+'\n')
inspection['sources']=sources
inspection['status']='draft_author_check'
(OUT/'sources-inspected.json').write_text(json.dumps(inspection,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'concepts':len(concepts),'body_word_range':[min(counts),max(counts)],'used_sources':len(candidate_sources),'candidate_sha256':sha(OUT/'candidate.json')}))
