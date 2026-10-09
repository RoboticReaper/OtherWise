"""Coordinator structural/provenance checks; cannot certify substantive source support."""
import importlib.util
from pathlib import Path
SPEC=importlib.util.spec_from_file_location('catalog_combiner',Path(__file__).resolve().parents[1]/'tools/catalog_combiner.py')
COMBINER=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(COMBINER)

def check(data,approved,baseline,imports,reserved_ids,domains,require_full=True):
    failures=[]
    try:COMBINER.validate_candidate(data,'candidate')
    except COMBINER.Rejected as exc:return exc.errors
    def fail(code,cid,reason):failures.append({'code':code,'id':cid,'reason':reason})
    ids={c['id'] for c in data['concepts']}
    if require_full and ids!=set(approved):fail('reserved_set_mismatch',None,'Final candidate IDs do not equal centrally approved owner IDs.')
    elif not ids<=set(approved):fail('unreserved_identity',None,'Candidate contains an identity not reserved to this batch.')
    for c in data['concepts']:
        cid=c['id'];p=approved.get(cid)
        if not p:continue
        if c['scope']!=p['scope'] or c['entity_kind']!=p['entity_kind']:fail('scope_type_changed',cid,'Scope or entity type differs from approved selection without a central amendment.')
        if p['primary_domain'] not in c['domains'] or not set(c['domains'])<=domains:fail('domain_mismatch',cid,'Primary membership missing or unknown domain.')
        if cid not in baseline:
            if not c['identity_urls']:fail('new_identity_url',cid,'New local identity needs an inspected public subject/explanatory URL, not an invented external identifier.')
            if c['original_description'] is not None or c['imported_records']!=[]:fail('new_identity_imports',cid,'A new identity must not claim imported provenance.')
            if c['card_version']<1:fail('invalid_new_version',cid,'First/revised version must be positive.')
        else:
            b=baseline[cid];prior=b.get('candidate_records',[])
            prior_card=prior[-1]['record'] if prior else None
            expected_description=prior_card['original_description'] if prior_card else b['original_description']
            expected_imports=prior_card['imported_records'] if prior_card else imports[cid]['imported_records']
            if c['original_description']!=expected_description:fail('original_description_changed',cid,'Pinned original description changed.')
            if c['imported_records']!=expected_imports:fail('imported_records_changed',cid,'Pinned imported rows changed.')
            preserved=set(b['aliases'])|{b['label']}
            if not preserved<=set(c['aliases'])|{c['label']}:fail('baseline_alias_lost',cid,'A preserved baseline label or alias is absent.')
            if prior_card and c!=prior_card and c['card_version']<=prior_card['card_version']:fail('previous_version_not_incremented',cid,'Changed card/reference record did not increment the latest prior card version.')
        for r in c['relations']:
            if r['target_id'] not in set(baseline)|set(reserved_ids):fail('unresolved_target',cid,r['target_id'])
            if r['target_id']==cid:fail('self_relation',cid,'Self relation.')
    return failures
