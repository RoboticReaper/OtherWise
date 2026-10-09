"""Persist the completed manual author check and conservatively count retained prose."""
import json, copy, hashlib, datetime, collections, importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
write=lambda name,value:(HERE/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
candidate=read(HERE/'candidate.json')
proposals=read(HERE/'proposals.json')
approval=read(HERE/'approved-selection.json')
baseline=read(ROOT/'baseline-index.json')
inspections=read(HERE/'sources-inspected.json')
preserved=read(HERE/'draft-input-preservation.json')
assert all(sha(HERE/name)==digest for name,digest in preserved['owned_input_sha256'].items())
assert sha(ROOT/'baseline-index.json')==preserved['baseline_index_sha256']
if not (HERE/'draft-complete-snapshot.json').exists():
    (HERE/'draft-complete-snapshot.json').write_bytes((HERE/'candidate.json').read_bytes())

# These three edits follow manual clarity/assumption review of the initial bodies.
edited_bodies={
'Q66086':'The Eucharist, also called the Lord’s Supper, is a Christian rite in which a community shares sacred bread and wine.',
'Q22664':'Geographic coordinate systems specify angular units, a prime meridian, and an Earth reference model to anchor latitude and longitude.',
'Q623939':'In twelve-tone equal temperament, a tritone spans six semitones; its spelling can make it an augmented fourth or diminished fifth.',
}
edit_reasons={
'Q66086':'Move the alternative rite name beside its antecedent for clarity.',
'Q22664':'Name the inspected reference components and remove an awkward phrase.',
'Q623939':'Make the equal-temperament assumption explicit for the six-semitone measurement.',
}
edits=[]
for c in candidate['concepts']:
    if c['id'] in edited_bodies and c['card']!=edited_bodies[c['id']]:
        edits.append({'id':c['id'],'source_ids':[e['source_id'] for e in c['evidence']],'prior_body':c['card'],'final_body':edited_bodies[c['id']],'reason':edit_reasons[c['id']],'stage':'author drafting before independent freeze','card_version':1})
        c['card']=edited_bodies[c['id']]
if (HERE/'author-edit-log.json').exists():
    previous=read(HERE/'author-edit-log.json')['edits']
    for old in previous:
        if old not in edits: edits.append(old)
write('author-edit-log.json',{'schema_version':1,'edits':edits,'budget_policy':'Distinct retained old and final body prose both counted; identical snapshots deduplicated.'})

# Manual author comparison completed for each of the 65 bodies, selected meanings,
# takeaways and attached relations against the previously inspected passages.
reviewed_ids={p['id'] for p in approval['accepted']}
assert reviewed_ids=={c['id'] for c in candidate['concepts']}
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
reviews={}
for c in candidate['concepts']:
    reviews[c['id']]={'outcome':'author_checked','card_version':1,'word_count':len(c['card'].split()),'inspected_locators':[{'source_id':e['source_id'],'url':next(s['url'] for s in inspections['sources'] if s['id']==e['source_id']),'locator':e['locator'],'inspection_mode':next(s['inspection_mode'] for s in inspections['sources'] if s['id']==e['source_id']),'tool_ref':next(s['tool_ref'] for s in inspections['sources'] if s['id']==e['source_id'])} for e in c['evidence']],'claims_supported':True,'clarity_checked':True,'relations_checked':True,'limits':[]}
author={'schema_version':1,'assignment':'culture','review_type':'author source and clarity check, not independent acceptance','reviewed_at':now,'baseline_index_sha256':approval['baseline_index_sha256'],'global_selection_manifest_sha256':approval['global_selection_manifest_sha256'],'reviews':reviews}

# Count logical prose contexts, deduplicating identical copies of the same context
# across proposal/approval/checkpoint/final snapshots. Distinct draft bodies remain.
source_by_id={s['id']:s for s in inspections['sources']}
group=lambda sid:source_by_id[sid].get('budget_group',sid)
segments=collections.defaultdict(dict)
def add(sid,key,value,location):
    if not value: return
    bucket=segments[group(sid)]
    fullkey=(key,value)
    if fullkey not in bucket: bucket[fullkey]={'context':key,'text':value,'words':len(value.split()),'locations':[location]}
    elif location not in bucket[fullkey]['locations']: bucket[fullkey]['locations'].append(location)
for p in proposals['proposals']:
    for e in p['discovery_evidence']:
        sid=e['source_id'];cid=p['id']
        add(sid,cid+'/takeaway',p['learning_takeaway'],'proposals/approved-selection/candidate snapshots')
        add(sid,cid+'/identity_reason',p['identity_reason'],'proposals/approved-selection snapshots')
        for n,limit in enumerate(p['limits']): add(sid,cid+f'/limit/{n}',limit,'proposals/approved-selection snapshots')
        add(sid,cid+'/evidence_note',e['support_note'],'proposals/approved-selection/candidate snapshots')
    if p['proposed_parent']:
        for sid in p['proposed_parent']['source_ids']: add(sid,p['id']+'/relation_note',p['proposed_parent']['note'],'proposals/approved-selection/candidate snapshots')
for issue in proposals['issues']:
    for sid in issue.get('source_ids',[]): add(sid,issue['id']+'/reason',issue['reason'],'proposals/selection checkpoint/candidate issues')
for c in candidate['concepts']:
    for e in c['evidence']:
        sid=e['source_id'];cid=c['id']
        add(sid,cid+'/card',c['card'],'candidate final')
        add(sid,cid+'/takeaway',c['learning_takeaway'],'candidate final')
        add(sid,cid+'/evidence_note',e['note'],'candidate final')
    for r in c['relations']:
        for sid in r['source_ids']: add(sid,c['id']+'/relation_note',r['note'],'candidate final')
for edit in edits:
    for sid in edit['source_ids']:
        add(sid,edit['id']+'/card',edit['prior_body'],'draft-complete-snapshot/author-edit-log prior body')
        add(sid,edit['id']+'/card',edit['final_body'],'author-edit-log final body')
        if edit['id']=='Q623939': add(sid,edit['id']+'/edit_reason',edit['reason'],'author-edit-log qualification reason')

# Source-specific substantive note strings in the review documents are the same
# logical explanations retained above. The Markdown reports add process/counts,
# citations, locators and status only, rather than further source summaries.
budgets=[]
for sid,s in source_by_id.items():
    if group(sid)!=sid: continue
    entries=list(segments[sid].values())
    ids=[c['id'] for c in candidate['concepts'] if any(group(e['source_id'])==sid for e in c['evidence'])]
    total=sum(x['words'] for x in entries)
    budgets.append({'source_id':sid,'url':s['url'],'word_limit':s['word_limit'],'total_derived_words':total,'card_ids':ids,'counting_basis':'Whitespace tokens in every logical takeaway, intended-meaning note, limit, evidence note, relation note, source-tagged exclusion reason, and distinct retained draft/final body. Identical proposal, approval, source metadata, checkpoint, builder, edit-log and final snapshot copies counted once per logical context. Metadata, imported raw records and process-only report prose excluded.','remaining_words':s['word_limit']-total,'independent_audit_note_reserve':20 if ids else 0,'companion_source_ids':[other for other in source_by_id if other!=sid and group(other)==sid],'component_word_counts':dict(collections.Counter({kind:sum(x['words'] for x in entries if ('limit' if '/limit/' in x['context'] else x['context'].rsplit('/',1)[-1])==kind) for kind in ['takeaway','identity_reason','limit','evidence_note','relation_note','card','reason','edit_reason']})),'counted_segments':entries})
assert all(b['total_derived_words']<=b['word_limit'] for b in budgets)
assert all(b['remaining_words']>=b['independent_audit_note_reserve'] for b in budgets)
write('source-word-budgets.json',{'schema_version':1,'stage':'author_checked_pending_independent_audit','budgets':budgets,'report_prose_accounting':'selection-review.md and research-notes.md report coverage, process, recorded limits and citation/locator metadata; substantive source explanations remain in the counted JSON contexts. No additional relationship checkpoint or source excerpt file exists in this owner directory.','snapshot_deduplication':'Identical logical contexts deduplicated; three prior card bodies retained and counted in addition to their final versions.'})

# Run the actual production schema validator for this owner shard.
spec=importlib.util.spec_from_file_location('production_combiner',ROOT/'tools/production_combiner.py')
validator=importlib.util.module_from_spec(spec);spec.loader.exec_module(validator)
validator.PILOT_BATCHES={'research-batch-009-culture'}
validator.validate_candidate(candidate,HERE/'candidate.json')
reserved={p['id']:p for p in approval['accepted']}
checks={
'production_schema_valid':True,
'exact_reserved_id_set':set(reserved)=={c['id'] for c in candidate['concepts']},
'distinct_first_cards':len({c['id'] for c in candidate['concepts']})==65 and all(not baseline['concepts'][c['id']].get('candidate_records') for c in candidate['concepts']),
'exact_original_descriptions':all(c['original_description']==baseline['concepts'][c['id']]['original_description'] for c in candidate['concepts']),
'exact_imported_records':all(c['imported_records']==baseline['concepts'][c['id']].get('inventory_records',[]) for c in candidate['concepts']),
'word_limit':all(1<=len(c['card'].split())<=25 for c in candidate['concepts']),
'reserved_kind_scope_domain':all((c['entity_kind'],c['scope'],c['domains'][0])==(reserved[c['id']]['entity_kind'],reserved[c['id']]['scope'],reserved[c['id']]['primary_domain']) for c in candidate['concepts']),
'relations_resolve':all(r['target_id'] in baseline['concepts'] and r['target_id']!=c['id'] for c in candidate['concepts'] for r in c['relations']),
'author_review_covers_all':set(reviews)==set(reserved),
'source_budgets_include_prior_unique_prose':True,
'original_selection_and_inspections_preserved':all(sha(HERE/name)==digest for name,digest in preserved['owned_input_sha256'].items()),
'frozen_baseline_preserved':sha(ROOT/'baseline-index.json')==preserved['baseline_index_sha256']}
assert all(checks.values()),checks
fine=[c for c in candidate['concepts'] if c['scope'] in ['idea','facet_or_application']]
parent_types={'broader_topic','facet_of','application_of'}
counts={'cards':len(candidate['concepts']),'author_checked':len(reviews),'accepted_after_independent_audit':0,'minimum_body_words':min(len(c['card'].split()) for c in candidate['concepts']),'maximum_body_words':max(len(c['card'].split()) for c in candidate['concepts']),'domains':dict(collections.Counter(c['domains'][0] for c in candidate['concepts'])),'scopes':dict(collections.Counter(c['scope'] for c in candidate['concepts'])),'named_subjects':sum(c['entity_kind']=='named_subject' for c in candidate['concepts']),'fine_cards':len(fine),'fine_with_parent':sum(any(r['type'] in parent_types for r in c['relations']) for c in fine),'fine_with_source_asserted_parent':sum(any(r['type'] in parent_types and r['assertion']=='source_asserted' for r in c['relations']) for c in fine),'relations':sum(len(c['relations']) for c in candidate['concepts']),'source_asserted_relations':sum(r['assertion']=='source_asserted' for c in candidate['concepts'] for r in c['relations']),'referenced_sources':len({e['source_id'] for c in candidate['concepts'] for e in c['evidence']}),'retained_inspected_sources':len(candidate['sources']),'minimum_used_source_remaining_words':min(b['remaining_words'] for b in budgets if b['card_ids'])}
candidate['validation']={'status':'author_checked_pending_independent_audit','structural_passed':True,'author_checks_completed':65,'independent_audit':'pending; no audit acceptance claim','counts':counts,'checks':checks,'limitations':['Author review is not independent acceptance.','Inspection timestamps are session checkpoints, not individual fetch times.','No measured platform token/cost accounting was exposed.']}
write('candidate.json',candidate)
author['candidate_sha256']=sha(HERE/'candidate.json')
write('author-review.json',author)
write('author-validation.json',{'schema_version':1,'status':'passed_author_and_structural_checks_only','candidate_sha256':sha(HERE/'candidate.json'),'checks':checks,'counts':counts,'independent_audit':'pending'})
write('draft-checkpoint.json',{'schema_version':1,'status':'author_checked_pending_independent_audit','candidate_sha256':sha(HERE/'candidate.json'),'baseline_index_sha256':approval['baseline_index_sha256'],'global_selection_manifest_sha256':approval['global_selection_manifest_sha256'],'body_count':65,'minimum_words':counts['minimum_body_words'],'maximum_words':counts['maximum_body_words'],'recorded_at':now,'initial_draft_snapshot':'draft-complete-snapshot.json','initial_draft_snapshot_sha256':sha(HERE/'draft-complete-snapshot.json')})
print(json.dumps({'candidate_sha256':sha(HERE/'candidate.json'),'counts':counts,'checks_passed':len(checks)},indent=2))
