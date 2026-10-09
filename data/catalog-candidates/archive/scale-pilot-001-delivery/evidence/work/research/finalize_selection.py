"""Assemble reviewed selections; never draft cards or alter operational inputs."""
import collections,copy,hashlib,json,sys,unicodedata
from datetime import datetime,timezone
from pathlib import Path
from central_selection import effective_id,is_recommended,normalize

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'data/catalog-candidates/scale-pilot-001'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
def norm(s):return ' '.join(unicodedata.normalize('NFKC',s).casefold().split())

def prepare():
    base=read(P/'baseline-index.json')['concepts'];plan=read(P/'coverage-plan.json')
    crosspath=ROOT/'research/identity-review/cross-batch-overlap-review.json';cross=read(crosspath)
    assert not cross['same_id_cross_batch'] and not cross['unresolved_cross_duplicate_findings']
    assert 'checkpoint' not in cross['status'],cross['status']
    crosshash={x['batch_id']:x['sha256'] for x in cross['inputs']}
    accepted=[];unselected=[];inputs=[];bybatch={};reviews=[]
    for assignment in plan['batches']:
        bid=assignment['id'];num=bid[-3:]
        path=ROOT/f'research/workers/{bid}/selection.proposed.json';data=read(path);h=sha(path)
        assert data.get('completed_at'),bid
        assert h==crosshash[bid],(bid,'cross-batch hash mismatch')
        rp=ROOT/(f'research/identity-review/batch-{num}-review.json' if num in ['004','005'] else f'research/identity-review-culture-life/batch-{num}-review.json')
        review=read(rp);rh=review.get('input_sha256',review.get('input',{}).get('sha256'))
        assert h==rh,(bid,'per-batch review hash mismatch')
        records=review.get('records',review.get('proposal_records',[]))
        assert len(records)==len(data['proposals']),(bid,'review coverage mismatch')
        lookup={r.get('proposed_id',r['proposal_id']):r for r in records}
        recs={r['proposal_id']:r for r in review.get('recommendations',[])}
        constraints={x['id']:[x['condition']] for x in review.get('pre_card_constraints',[])}
        sources={s['id']:s for s in data['sources']}
        selected=[p for p in data['proposals'] if is_recommended(p)]
        if bid=='research-batch-004':
            selected=[p for p in selected if effective_id(p)!='local:catalog:mechanical-stress']
            selected.append(next(p for p in data['proposals'] if effective_id(p)=='local:catalog:three-point-bending-test'))
        assert len(selected)==200,(bid,len(selected))
        selected_original_ids={effective_id(p) for p in selected}
        for q in data['proposals']:
            if effective_id(q) not in selected_original_ids:
                unselected.append(dict(originating_batch_id=bid,proposal=copy.deepcopy(q),central_note='Mechanical stress remains quarantined after central review.' if effective_id(q)=='local:catalog:mechanical-stress' else 'Retained unselected author proposal.'))
        rows=[]
        for proposal in selected:
            oldid=effective_id(proposal);rr=lookup[oldid];detail=recs.get(oldid)
            q=copy.deepcopy(proposal)
            if oldid=='local:catalog:organizational-design':
                q['provisional_id']='Q3318170';q.pop('suggested_id',None)
            x=normalize(q,bid,base);x['author_provisional_id']=proposal['provisional_id'];x['author_effective_id']=oldid
            x['selection_status']='approved_for_card_research';x['source_namespace']=bid
            x['independent_identity_review']={'path':str(rp.relative_to(ROOT)),'sha256':sha(rp),'record':rr,'specific_decision':detail}
            c=list(rr.get('authoring_constraints',[]))+list(constraints.get(oldid,[]))
            if detail:c+=detail.get('authoring_conditions',[])
            x['authoring_constraints']=list(dict.fromkeys(c))
            if rr.get('corrected_baseline_comparisons'):
                x['superseded_author_baseline_matches']=x.get('nearest_baseline_matches',[])
                x['nearest_baseline_matches']=rr['corrected_baseline_comparisons']
            elif detail:
                x['nearest_baseline_matches']=[{'id':cid,'label':base[cid]['label'] if cid in base else cid,'meaning_comparison':detail['meaning_comparison'],'reviewer_decision':detail['recommendation']} for cid in detail.get('compared_ids',[])]
            elif rr.get('baseline_rows_reviewed'):
                x['nearest_baseline_matches']=[{'id':r['id'],'label':r['label'],'meaning_comparison':rr['identity_reason'],'reviewer_decision':rr['advisory_decision']} for r in rr['baseline_rows_reviewed']]
            else:
                x['baseline_comparison_status']='Independent bounded review completed; contextual diagnostics are not relationship assertions or automatic novelty proof.'
            x['duplicate_review_decision']=rr.get('identity_reason', detail['meaning_comparison'] if detail else rr.get('identity_recommendation'))
            x['nearest_sibling_matches']={'review_path':str(crosspath.relative_to(ROOT)),'review_sha256':sha(crosspath),'status':'No unresolved cross-batch duplicate identified in bounded all-five review.'}
            if x['id'] in ['Q43290','local:catalog:mishnah']:x['entity_kind']='named_subject'
            if x['id']=='local:catalog:genetic-mapping':x['aliases']=sorted(set(x['aliases'])|{x['label']});x['label']='Genetic linkage mapping'
            if x['id']=='local:catalog:distributed-consensus':x['aliases']=sorted(set(x['aliases'])|{x['label']});x['label']='Replicated-log consensus under crash faults'
            if x['id']=='local:catalog:pitch-material':
                x['label']='Pitch (tar-derived material)';x['aliases']=sorted(set(x['aliases'])|{'Pitch','Pitch (material)'})
                x['learning_takeaway']='Explain how tar-derived pitch can shatter under a quick blow yet flow extremely slowly over years.'
            if x['id']=='local:catalog:threefold-repetition':x['learning_takeaway']='Explain the claimable three-occurrence draw procedure, including the timing of a claim before a qualifying intended move.'
            if x['id']=='local:authored:000256':
                x['learning_takeaway']='Explain the piece-reuse feature of shogi through a directly supported broad-game overview, leaving the perpetual-check exception to its separate rule card.'
                x['authoring_constraints'].append('Re-inspect an appropriate rule passage for the broad-game overview; do not reuse the perpetual-check takeaway. Any extra source work remains within the original source-attempt bounds.')
            x['discovery_source_ids']=sorted({e['source_id'] for e in x['discovery_references']})
            assert all(s in sources for s in x['discovery_source_ids']),(bid,x['id'],'missing discovery source')
            x['discovery_locators']=[{'source_id':e['source_id'],'locator':e['locator']} for e in x['discovery_references']]
            rows.append(x)
        for domain in assignment['primary_domains']:
            assert sum(x['primary_domain']==domain['domain'] for x in rows)==domain['target_cards']
            for sf in domain['starting_subfields']:
                assert sum(x['primary_domain']==domain['domain'] and x['primary_subfield']==sf for x in rows)>=5,(bid,sf)
        assert {x['scope'] for x in rows}=={'broad_field','topic','idea','facet_or_application'}
        accepted+=rows
        bybatch[bid]={'schema_version':1,'batch_id':bid,'author_input':{'path':str(path.relative_to(ROOT)),'sha256':h},'independent_review':{'path':str(rp.relative_to(ROOT)),'sha256':sha(rp)},'accepted':rows,'sources':data['sources'],'author_issues':data['issues'],'authoring_contract':'research/author-contract.md'}
        inputs.append({'batch_id':bid,'path':str(path.relative_to(ROOT)),'sha256':h,'formal_proposal_count':len(data['proposals']),'recommended_before_central_corrections':200})
        reviews.append({'batch_id':bid,'path':str(rp.relative_to(ROOT)),'sha256':sha(rp),'reviewed_rows':len(records)})
    assert len(accepted)==1000 and len({x['id'] for x in accepted})==1000
    aliases=collections.defaultdict(set)
    for x in accepted:
        for a in [x['label'],*x['aliases']]:aliases[norm(a)].add(x['id'])
    shared={a:sorted(ids) for a,ids in aliases.items() if len(ids)>1}
    counts={}
    for bid,b in bybatch.items():
        rows=b['accepted'];counts[bid]={'selected':len(rows),'new':sum(x['inventory_status']=='new' for x in rows),'existing_controls':sum(x['inventory_status']=='existing' for x in rows),'new_fine':sum(x['inventory_status']=='new' and x['scope'] in {'idea','facet_or_application'} for x in rows),'named_subjects':sum(x['entity_kind']=='named_subject' for x in rows),'scopes':dict(collections.Counter(x['scope'] for x in rows))}
        assert counts[bid]['new']>=160 and counts[bid]['new_fine']>=120 and 20<=counts[bid]['existing_controls']<=40
    return {'schema_version':1,'pilot_id':'scale-pilot-001','status':'ready_to_freeze_pending_shared_alias_decisions','baseline_index_sha256':sha(P/'baseline-index.json'),'baseline_manifest_sha256':sha(P/'baseline-manifest.json'),'author_inputs':inputs,'independent_reviews':reviews,'cross_batch_review':{'path':str(crosspath.relative_to(ROOT)),'sha256':sha(crosspath)},'accepted':accepted,'unselected_proposals':unselected,'counts':counts,'shared_aliases':shared,'by_batch':bybatch}

if __name__=='__main__':
    d=prepare();write(ROOT/'research/selection-preflight.json',d)
    print(json.dumps({'counts':d['counts'],'shared_aliases':d['shared_aliases'],'formal_proposals':sum(x['formal_proposal_count'] for x in d['author_inputs']),'selected':len(d['accepted'])},ensure_ascii=False,indent=2))
