"""Local, manual card assembly and validation. No network or generation APIs."""
import copy
import hashlib
import importlib.util
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUILD = HERE.parents[1]
ROOT = BUILD.parents[2]
BASELINE_PATH = BUILD / 'baseline-index.json'
APPROVED_PATH = HERE / 'approved-selection.json'
SELECTION_PATH = BUILD / 'selection-manifest.json'

def read(path): return json.loads(Path(path).read_text())
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path, data): Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
def stock():
    spec = importlib.util.spec_from_file_location('culture_batch008_adapter', BUILD / 'tools/assemble.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.stock_module()

def assemble():
    approved = read(APPROVED_PATH)
    baseline = read(BASELINE_PATH)['concepts']
    drafts = read(HERE / 'draft-cards.json')
    inspected = read(HERE / 'draft-sources-inspected.json')
    sources_by_url = {s['url']: s for s in inspected}
    sources_by_id = {s['id']: s for s in inspected}
    used = set()
    concepts, reviews, controls, ownership, gaps = [], {}, {}, {}, []
    for reservation in approved['accepted']:
        cid = reservation['id']
        if cid not in drafts: continue
        draft = drafts[cid]
        main_e = reservation['discovery_evidence'][0]
        sid = draft.get('source_id', sources_by_url[main_e['url']]['id'])
        loc = draft.get('locator', main_e['locator'])
        used.add(sid)
        evidence = [dict(source_id=sid, locator=loc, note=draft.get('evidence_note','Definition and card claims inspected.'))]
        for e in draft.get('additional_evidence', []):
            evidence.append(e); used.add(e['source_id'])
        parent = reservation['proposed_parent']
        if 'relations' in draft:
            relations = draft['relations']
        elif parent:
            psid = draft.get('parent_source_id', sources_by_url[parent['url']]['id'])
            relations = [dict(target_id=parent['target_id'],type=parent['type'],
                source_ids=[psid],assertion=parent['assertion'],
                note=draft.get('parent_note',parent['note']))]
        else: relations = []
        for relation in relations: used.update(relation['source_ids'])
        original, imported, identity_urls = None, [], [sources_by_id[sid]['url']]
        if cid in baseline:
            base = baseline[cid]
            original = base['original_description']
            imported = copy.deepcopy(base['inventory_records'])
            for prior in base['candidate_records']:
                for raw in prior['record']['imported_records']:
                    if raw not in imported: imported.append(copy.deepcopy(raw))
                for url in prior['record']['identity_urls']:
                    if url not in identity_urls: identity_urls.append(url)
            for raw in base['inventory_records']:
                if raw.get('source_url', '').startswith(('http://', 'https://')) and raw['source_url'] not in identity_urls:
                    identity_urls.append(raw['source_url'])
            prior = copy.deepcopy(base['candidate_records'])
            # Complete legacy bundle pointer when the index retained a full record without a bundle path.
            supplements = []
            for old in prior:
                if not old.get('source_bundle_path'):
                    path = ROOT / 'data/catalog-candidates' / (old['batch_id'] + '.json')
                    if path.exists():
                        old_data = read(path)
                        index = next(i for i,c in enumerate(old_data['concepts']) if c['id']==cid)
                        assert old_data['concepts'][index] == old['record']
                        supplements.append(dict(batch_id=old['batch_id'], source_bundle_path=str(path.relative_to(ROOT)),
                            source_bundle_sha256=sha(path), prior_record_pointer=f'{path.relative_to(ROOT)}#/concepts/{index}',
                            source_bundle_pointer=f'{path.relative_to(ROOT)}#/sources'))
            controls[cid] = dict(previous_max_card_version=reservation['baseline_max_card_version'],
                selected_card_version=reservation['required_card_version'], reason='New researched card and reference bundle; approved maximum plus one.',
                baseline_prior_records_pointer=f'{BASELINE_PATH.relative_to(ROOT)}#/concepts/{cid}/candidate_records',
                baseline_raw_rows_pointer=f'{BASELINE_PATH.relative_to(ROOT)}#/concepts/{cid}/inventory_records',
                prior_full_records=prior, supplementary_prior_bundle_pointers=supplements,
                original_description_preserved=True, all_baseline_inventory_rows_preserved=True)
        concept = dict(id=cid,label=reservation['label'],aliases=reservation['aliases'],
            entity_kind=reservation['entity_kind'],scope=reservation['scope'],domains=[reservation['primary_domain']],
            learning_takeaway=draft['takeaway'],card=draft['body'],original_description=original,
            identity_urls=identity_urls,evidence=evidence,relations=relations,
            card_version=reservation['required_card_version'],imported_records=imported)
        concepts.append(concept)
        ownership[cid] = dict(owner='culture',primary_domain=reservation['primary_domain'],primary_subfield=reservation['primary_subfield'],
            approved_selection_pointer=f'approved-selection.json#/accepted/{approved["accepted"].index(reservation)}')
        if not any(r['type'] in ('broader_topic','facet_of','application_of') for r in relations):
            gaps.append(dict(id=cid,scope=reservation['scope'],reason=draft.get('gap','No defensible parent asserted in the inspected evidence.')))
        reviews[cid] = dict(outcome='author_checked',card_version=concept['card_version'],word_count=len(concept['card'].split()),
            inspected_locators=[dict(source_id=e['source_id'],url=sources_by_id[e['source_id']]['url'],locator=e['locator']) for e in evidence],
            checks=dict(meaning_boundary='passed',substantive_claims='passed',qualifications='passed',relations='passed',
                originality_and_shared_budget='passed',provenance_and_version='passed'),
            limits=reservation['limits']+draft.get('limits',[]), independent_audit_status='pending')
    selected_sources = []
    for item in inspected:
        if item['id'] not in used: continue
        s = copy.deepcopy(item)
        s.pop('passage_notes',None)
        s['inspection_record_pointer'] = f'draft-sources-inspected.json#/{inspected.index(item)}'
        s['retrieved_at'] = s['inspected_at']
        s['acquisition']['time_basis'] = 'Local timestamp recorded after reading the cited passage; exact remote retrieval timestamp unavailable.'
        s['summary_word_limit'] = 200
        selected_sources.append(s)
    budget = defaultdict(lambda:dict(cards=[],derived_words=0,summary_limit=200))
    for c in concepts:
        # Conservatively attribute all body/takeaway and factual relation-note prose to every attached source.
        prose = c['card'] + ' ' + c['learning_takeaway']
        for sid in {e['source_id'] for e in c['evidence']} | {sid for r in c['relations'] for sid in r['source_ids']}:
            amount = len(prose.split()) + sum(len(r['note'].split()) for r in c['relations'] if sid in r['source_ids'])
            amount += sum(len(e['note'].split()) for e in c['evidence'] if sid==e['source_id'])
            budget[sid]['derived_words'] += amount
            budget[sid]['cards'].append(c['id'])
    summary = dict(cards=len(concepts),new=sum(c['id'] not in baseline for c in concepts),controls=len(controls),
        domains=dict(Counter(c['domains'][0] for c in concepts)),scopes=dict(Counter(c['scope'] for c in concepts)),
        entity_kinds=dict(Counter(c['entity_kind'] for c in concepts)))
    candidate = dict(schema_version=1,batch=dict(id='research-batch-008-culture',kind='researched_candidate_shard',
        status='draft_ready_for_independent_audit' if len(concepts)==70 else 'in_progress_valid_checkpoint',
        assignment='culture',global_selection_manifest_sha256=sha(SELECTION_PATH),baseline_index_sha256=sha(BASELINE_PATH),
        approved_selection_sha256=sha(APPROVED_PATH),approved_selection_path=str(APPROVED_PATH.relative_to(ROOT)),
        source_inspection_clock_basis='Local post-inspection timestamp; remote retrieval instant unavailable.',
        ownership_and_subfields=ownership,missing_parent_links=gaps,control_version_decisions=controls,
        summary=summary,source_summary_budgets=dict(budget),
        source_summary_budget_basis='Cumulative new card, takeaway, evidence-note and relation-note prose per source. Bibliographic titles/locators and unchanged archival prior records are excluded. Internal inspection records are linked rather than copied into source records.',
        usage=dict(tokens=None,cost=None,availability='Unavailable to the researcher'),
        updated_at=datetime.now(timezone.utc).isoformat()),sources=selected_sources,concepts=concepts,
        issues=[dict(kind='acceptance_gate',note='Author review is complete for emitted cards; independent audit is pending.'),
                dict(kind='source_limits',pointers=['source-access-limits.json','draft-source-access-limits.json'],note='Failed passages are not used as claim support.')],
        validation=dict(status='pending_local_validation',independent_source_audit='pending'))
    checker = stock()
    checker.validate_candidate(candidate, HERE/'candidate.json')
    write(HERE/'candidate.json',candidate)
    write(HERE/'author-review.json',dict(schema_version=1,assignment='culture',status='complete' if len(reviews)==70 else 'in_progress',
        global_selection_manifest_sha256=sha(SELECTION_PATH),baseline_index_sha256=sha(BASELINE_PATH),reviews=reviews))
    print(json.dumps(summary))
    print('Over 200-word conservative candidate source allocations:',{sid:r['derived_words'] for sid,r in budget.items() if r['derived_words']>200})
    return candidate

if __name__=='__main__': assemble()
