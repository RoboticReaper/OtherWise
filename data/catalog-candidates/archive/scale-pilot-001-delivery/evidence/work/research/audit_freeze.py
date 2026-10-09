"""Deterministic sampling. Risk selection is purposive, never an error-rate frame."""
import hashlib
import re
import json
import shutil
from pathlib import Path
from datetime import datetime,timezone

def freeze_candidate(candidate_path,baseline_path,selection_path,audit_dir):
    candidate_path=Path(candidate_path);audit_dir=Path(audit_dir)
    raw=candidate_path.read_bytes();candidate_sha=hashlib.sha256(raw).hexdigest()
    metadata=audit_dir/'sample.frozen.json'
    if metadata.exists():
        old=json.loads(metadata.read_text())
        if old['pre_audit_candidate_sha256']!=candidate_sha:
            raise ValueError('Refusing to replace a frozen sample with a different candidate.')
        if hashlib.sha256((audit_dir/'candidate.before-audit.json').read_bytes()).hexdigest()!=candidate_sha:
            raise ValueError('Frozen candidate bytes no longer match their recorded hash.')
        return old
    data=json.loads(raw);base=json.loads(Path(baseline_path).read_text())
    cards=data['concepts'];ids=[c['id'] for c in cards]
    if len(ids)!=len(set(ids)):raise ValueError('Cannot freeze duplicate accepted IDs.')
    bid=data['batch']['id'];seed=f'OtherWise-scale-pilot-001:{bid}:source-audit'
    frame=sorted(set(ids)-set(base['concepts']))
    random=sample_random(frame,seed,20);risk=sample_risk(cards,set(random),20)
    sample_ids=random+[x['id'] for x in risk]
    if len(sample_ids)!=len(set(sample_ids)):raise ValueError('Audit samples overlap.')
    result={'schema_version':1,'batch_id':bid,'frozen_at':datetime.now(timezone.utc).isoformat(),'pre_audit_candidate_sha256':candidate_sha,'pre_audit_candidate_size_bytes':len(raw),'baseline_sha256':hashlib.sha256(Path(baseline_path).read_bytes()).hexdigest(),'global_selection_manifest_sha256':hashlib.sha256(Path(selection_path).read_bytes()).hexdigest(),'accepted_ids':sorted(ids),'new_id_frame':frame,'new_id_frame_sha256':hashlib.sha256(json.dumps(frame,ensure_ascii=False,separators=(',',':')).encode()).hexdigest(),'seed':seed,'random_sampling_rule':'Sort new IDs by SHA256(UTF8(seed + newline + ID)); take the first 20.','random_sample_ids':random,'risk_sampling_rule':'Disjoint purposive greedy coverage of scopes, primary domains, sources, named subjects, explicit assumptions and relation assertion types; SHA256 tie-break. See audit_freeze.py.','risk_sample':risk,'sample_ids':sample_ids,'random_sample_shortfall':max(0,20-len(random)),'risk_sample_shortfall':max(0,20-len(risk)),'do_not_pool_as_error_rate':True}
    selected={c['id']:c for c in cards}
    packet={'schema_version':1,'batch_id':bid,'pre_audit_candidate_sha256':candidate_sha,'sample':[],'all_frozen_sources':data['sources']}
    reasons={x['id']:x['reason'] for x in risk}
    for cid in sample_ids:packet['sample'].append({'id':cid,'sample_kind':'random_new' if cid in random else 'risk_selected','selection_reason':'Prescribed deterministic new-ID sample.' if cid in random else reasons[cid],'card':selected[cid]})
    audit_dir.mkdir(parents=True,exist_ok=True)
    if any(audit_dir.iterdir()):raise ValueError('Audit destination contains an incomplete or unrelated freeze; inspect before reuse.')
    (audit_dir/'candidate.before-audit.json').write_bytes(raw)
    (audit_dir/'sample-cards.frozen.json').write_text(json.dumps(packet,ensure_ascii=False,indent=2)+'\n')
    metadata.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    return result

def sample_random(ids,seed,n=20):
    return sorted(set(ids),key=lambda cid:hashlib.sha256((seed+'\n'+cid).encode('utf-8')).hexdigest())[:n]

def risk_features(card):
    features={'scope:'+card['scope']:5}
    for domain in card['domains'][:1]: features['domain:'+domain]=4
    for e in card['evidence']: features['source:'+e['source_id']]=1
    if card['entity_kind']=='named_subject': features['risk:named_subject']=4
    if card['scope']=='facet_or_application': features['risk:fine_application_wording']=3
    if '(' in card.get('label',''): features['risk:sense_specific_label']=4
    if any(r['assertion']=='source_asserted' for r in card['relations']): features['risk:source_asserted_relationship']=4
    if any(r['assertion']=='editorial' for r in card['relations']): features['risk:editorial_relationship']=2
    if re.search(r'\b(under|assum|model|may|can|often|typically|conditional|ideal|approximate|experiment|study|studies)\b',card['card'],re.I): features['risk:qualification_or_assumption']=4
    return features

def sample_risk(cards,excluded,n=20):
    pool={c['id']:c for c in cards if c['id'] not in excluded}
    covered=set(); result=[]
    while pool and len(result)<n:
        ranked=[]
        for cid,c in pool.items():
            f=risk_features(c)
            gain=sum(v for k,v in f.items() if k not in covered)
            risk=sum(v for k,v in f.items() if k.startswith('risk:'))
            ranked.append((-gain,-risk,hashlib.sha256(('risk\n'+cid).encode()).hexdigest(),cid,f))
        _,_,_,cid,features=min(ranked)
        c=pool.pop(cid)
        reasons=sorted(k for k in features if k.startswith('risk:'))
        result.append(dict(id=cid,scope=c['scope'],primary_domain=c['domains'][0],reason='Purposive coverage/risk selection: '+', '.join(reasons or ['scope/source coverage']),features=sorted(features),new_coverage_features=sorted(set(features)-covered)))
        covered.update(features)
    return result
