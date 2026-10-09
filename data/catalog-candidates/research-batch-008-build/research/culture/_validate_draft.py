"""Read-only checks of the finalized culture shard. Never freezes or samples."""
import json
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from _draft_tools import HERE, BUILD, ROOT, read, sha, stock, write

GLOBAL_SHA = '5e15d76acee1c29775a9b7b003f7d01447e494974da200c9c15afa3a25f5df9d'
BASELINE_SHA = 'e3cd8ebac67579be75742df0bf2f5b2e7781293282345d2286aff205416e0fe2'

def strong_alias(value):
    return ''.join(c for c in unicodedata.normalize('NFKD',value).casefold() if c.isalnum())

def validate():
    candidate = read(HERE/'candidate.json')
    approved = read(HERE/'approved-selection.json')
    global_selection = read(BUILD/'selection-manifest.json')
    baseline = read(BUILD/'baseline-index.json')
    plan = read(BUILD/'coverage-plan.json')['assignments']['culture']
    review = read(HERE/'author-review.json')
    checker = stock()
    checker.validate_candidate(candidate,HERE/'candidate.json')
    assert sha(BUILD/'selection-manifest.json') == GLOBAL_SHA
    assert sha(BUILD/'baseline-index.json') == BASELINE_SHA
    assert candidate['batch']['global_selection_manifest_sha256'] == GLOBAL_SHA
    assert candidate['batch']['baseline_index_sha256'] == BASELINE_SHA
    assert candidate['batch']['approved_selection_sha256'] == sha(HERE/'approved-selection.json')
    reservation = {c['id']:c for c in approved['accepted']}
    concepts = {c['id']:c for c in candidate['concepts']}
    assert set(concepts) == set(reservation)
    assert len(concepts) == plan['cards'] == 70
    assert len(concepts) == len(candidate['concepts'])
    assert set(review['reviews']) == set(concepts)
    assert review['status']=='complete'
    source_ids = {s['id'] for s in candidate['sources']}
    assert len(source_ids)==len(candidate['sources'])
    targets = set(baseline['concepts']) | {c['id'] for c in global_selection['accepted']}
    controls = set(concepts) & set(baseline['concepts'])
    assert len(controls)==plan['control_goal']==6
    assert len(set(concepts)-controls)==plan['new_goal']==64
    domains = dict(Counter(c['domains'][0] for c in concepts.values()))
    assert domains == plan['primary_domains']
    assert {c['scope'] for c in concepts.values()}=={'broad_field','topic','idea','facet_or_application'}
    normalized = defaultdict(set)
    strong = defaultdict(set)
    for c in global_selection['accepted']:
        for name in [c['label']]+c['aliases']:
            normalized[checker.normalize_alias(name)].add(c['id'])
            strong[strong_alias(name)].add(c['id'])
    baseline_strong = defaultdict(set)
    for name,ids in baseline['aliases'].items(): baseline_strong[strong_alias(name)].update(ids)
    alias_collisions=[]
    strong_collisions=[]
    for cid,c in concepts.items():
        r=reservation[cid]
        for field in ['label','aliases','entity_kind','scope']:
            assert c[field]==r[field],(cid,field)
        assert c['domains'][0]==r['primary_domain']
        assert c['card_version']==r['required_card_version']
        assert 30 <= len(c['card'].split()) <= 50
        assert review['reviews'][cid]['word_count']==len(c['card'].split())
        assert review['reviews'][cid]['card_version']==c['card_version']
        assert review['reviews'][cid]['outcome']=='author_checked'
        assert review['reviews'][cid]['independent_audit_status']=='pending'
        for name in [c['label']]+c['aliases']:
            exact=(set(baseline['aliases'].get(checker.normalize_alias(name),[])) | normalized[checker.normalize_alias(name)])-{cid}
            if exact:alias_collisions.append(dict(id=cid,name=name,other_ids=sorted(exact)))
            near=(baseline_strong[strong_alias(name)] | strong[strong_alias(name)])-{cid}
            if near:strong_collisions.append(dict(id=cid,name=name,other_ids=sorted(near)))
        for e in c['evidence']: assert e['source_id'] in source_ids
        for relation in c['relations']:
            assert relation['target_id'] in targets
            assert relation['target_id']!=cid
            assert set(relation['source_ids']) <= source_ids
        if cid not in controls:
            assert c['card_version']==1 and c['original_description'] is None and c['imported_records']==[]
            continue
        base=baseline['concepts'][cid]
        assert c['label']==base['label']
        assert c['original_description']==base['original_description']
        assert all(raw in c['imported_records'] for raw in base['inventory_records'])
        decision=candidate['batch']['control_version_decisions'][cid]
        assert decision['previous_max_card_version']==r['baseline_max_card_version']
        assert c['card_version']==r['baseline_max_card_version']+1
        assert decision['prior_full_records']==base['candidate_records']
        bundles=decision['prior_full_records']+decision['supplementary_prior_bundle_pointers']
        for old in bundles:
            if old.get('source_bundle_path'):
                path=Path(old['source_bundle_path'])
                path=path if path.is_absolute() else ROOT/path
                assert path.exists(),(cid,str(path))
                assert sha(path)==old['source_bundle_sha256'],(cid,str(path))
        for old in base['candidate_records']:
            assert all(raw in c['imported_records'] for raw in old['record']['imported_records'])
            if not old.get('source_bundle_path'):
                assert any(s['batch_id']==old['batch_id'] for s in decision['supplementary_prior_bundle_pointers'])
    assert not alias_collisions,alias_collisions
    assert not strong_collisions,strong_collisions
    assert 'Planar buffering' not in concepts['local:catalog:euclidean-buffering']['aliases']
    assert all(concepts[cid]['entity_kind']=='idea' for cid in concepts if cid.endswith('-projection'))
    for cid in ['local:catalog:euclidean-buffering','local:catalog:geodesic-buffering']:
        assert any(r['type']=='facet_of' and r['target_id']=='local:catalog:geographic-buffer' and r['assertion']=='source_asserted' for r in concepts[cid]['relations'])
    assert 'https://www.metmuseum.org/art/collection/search/79595' in concepts['local:catalog:itoh-furisode-met-1997-228']['identity_urls']
    assert not any(cid in concepts for cid in ['local:catalog:satori','local:catalog:arashi-shibori','local:catalog:spenserian-stanza'])
    for sid,budget in candidate['batch']['source_summary_budgets'].items():
        assert sid in source_ids and budget['derived_words']<=budget['summary_limit']==200
    fine=[c for c in concepts.values() if c['scope'] in ['idea','facet_or_application']]
    new_fine=[c for c in fine if c['id'] not in controls]
    has_parent=lambda c,sa=False:any(r['type'] in ['broader_topic','facet_of','application_of'] and (not sa or r['assertion']=='source_asserted') for r in c['relations'])
    result=dict(status='passed',independent_source_audit='pending',
        candidate_sha256=sha(HERE/'candidate.json'),local_checked_at=datetime.now(timezone.utc).isoformat(),
        global_selection_manifest_sha256=GLOBAL_SHA,baseline_index_sha256=BASELINE_SHA,
        checks=dict(stock_schema='passed',approved_identities_scopes_versions='passed',word_counts='passed',
            coverage='passed',source_and_target_resolution='passed',baseline_and_global_aliases='passed',
            punctuation_and_diacritic_aliases='passed',control_original_text_and_raw_rows='passed',
            full_prior_records_and_bundle_hashes='passed',shared_source_summary_allocations='passed',
            special_identity_and_relation_requirements='passed',all_70_author_reviews='passed'),
        counts=dict(cards=70,new=64,controls=6,fine=len(fine),new_fine=len(new_fine),
            named=sum(c['entity_kind']=='named_subject' for c in concepts.values()),
            fine_with_parent=sum(has_parent(c) for c in fine),fine_with_source_asserted_parent=sum(has_parent(c,True) for c in fine)),
        domains=domains,scopes=dict(Counter(c['scope'] for c in concepts.values())),
        sources=len(source_ids),missing_parent_links=candidate['batch']['missing_parent_links'],
        largest_source_allocations=sorted([dict(source_id=sid,derived_words=b['derived_words']) for sid,b in candidate['batch']['source_summary_budgets'].items()],key=lambda x:x['derived_words'],reverse=True)[:5],
        exact_alias_collisions=alias_collisions,strong_alias_collisions=strong_collisions,
        limitations=['Structural and author checks do not substitute for the coordinator’s independent source audit. No sample or freeze was performed by the author.'])
    write(HERE/'draft-validation.json',result)
    print(json.dumps({k:result[k] for k in ['status','candidate_sha256','counts','sources','largest_source_allocations']},ensure_ascii=False))
    return result

if __name__=='__main__': validate()
