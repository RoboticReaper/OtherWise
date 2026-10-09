"""Read-only integration checks, independently comparing original and revised data."""
import hashlib
import json
from pathlib import Path
from collections import Counter

HERE = Path(__file__).resolve().parents[1]
PROJECT = HERE.parents[3]


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                         separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def verify():
    checks = []
    def check(condition, label):
        if not condition:
            raise AssertionError(label)
        checks.append(label)
    protection = read(HERE/'original-input-protection.json')['protected_sha256']
    check(all(sha(PROJECT/path) == expected for path,expected in protection.items()),
          'Original delivery and operational inputs unchanged')
    manifest = read(HERE/'baseline-manifest.json')
    check(all(sha(HERE/r['snapshot']) == sha(PROJECT/r['path']) == r['sha256'] for r in manifest['inputs']),
          'Full current baseline snapshots agree with live input hashes')
    check(sha(HERE/'baseline-index.json') == manifest['baseline_index_sha256']
          and sha(HERE/'baseline-imported-records.json') == manifest['baseline_imported_records_sha256'],
          'Pinned index and original source rows retain their hashes')
    baseline = read(HERE/'baseline-index.json')['concepts']
    raw = read(HERE/'baseline-imported-records.json')['concepts']
    catalog = read(HERE/'catalog.json')
    content = json.loads(json.dumps(catalog))
    canonical = content['validation'].pop('canonical_content_sha256')
    check(digest(content) == canonical, 'Combined canonical content hash reproduces')
    concepts = {c['id']:c for c in catalog['concepts']}
    check(len(concepts) == len(catalog['concepts']) == 1000, 'Exactly 1000 distinct selected identities')
    decisions = read(HERE/'reconciliation-decisions.json')['decisions']
    mapping = {r['id']:r['target_id'] for r in decisions if r['action']=='reuse_existing'}
    lineage = read(HERE/'revision-lineage.json')
    check(mapping == lineage['legacy_id_redirects'] and len(decisions)==112,
          '112 reviewed offered matches and their legacy redirects agree')
    check(all(old not in concepts and new in baseline and new in concepts for old,new in mapping.items()),
          'Reused local IDs are replaced by registered current identities')
    sources = {s['id']:s for s in catalog['sources']}
    changed = {r['original_id']:r for r in lineage['changed_records']}
    originals = []
    body_changes = []
    bundles_changed = []
    for n in range(3,8):
        original = read(PROJECT/f'data/catalog-candidates/research-batch-{n:03d}.json')
        revised_path = HERE/f'research-batch-{n:03d}.json'
        revised = read(revised_path)
        bid = original['batch']['id']
        check(revised['batch']['revision'] == original['batch']['revision']+1,
              f'{bid}: batch revision increments')
        selected = next(p for p in catalog['batch']['input_provenance'] if p['batch_id']==bid)
        check(selected['input_sha256']==sha(revised_path) and selected['candidate_snapshot']==revised,
              f'{bid}: exact selected snapshot preserved')
        revised_cards = {c['id']:c for c in revised['concepts']}
        for old in original['concepts']:
            old_id, cid = old['id'], mapping.get(old['id'],old['id'])
            originals.append(old)
            current, combined = revised_cards[cid], concepts[cid]
            if current != old:
                bundles_changed.append(old_id)
                check(old_id in changed and changed[old_id]['original_record']==old
                      and changed[old_id]['revised_record_sha256']==digest(current),
                      f'{old_id}: original record and changed bundle digest preserved')
                check(current['card_version']>old['card_version'],f'{old_id}: changed bundle version increments')
            if current['card'] != old['card']:
                body_changes.append(old_id)
            if old_id in mapping:
                check(current['original_description']==baseline[cid]['original_description']
                      and all(r in current['imported_records'] for r in raw[cid]['imported_records']),
                      f'{cid}: source wording and complete registered raw rows remain separate from card')
            else:
                check(current['original_description']==old['original_description']
                      and current['imported_records']==old['imported_records'],
                      f'{cid}: original imported provenance retained')
            for edge in old['relations']:
                check(any(e['type']==edge['type'] and e['target_id']==mapping.get(edge['target_id'],edge['target_id'])
                          and e['assertion']==edge['assertion'] for e in current['relations']),
                      f'{cid}: original relation survives target reconciliation')
            check(30<=len(combined['card'].split())<=50,f'{cid}: card length within budget')
            check(combined['card']==current['card'] and combined['card_version']==current['card_version'],
                  f'{cid}: selected card and version agree')
            check(all(e['source_id'] in sources for e in combined['evidence']) and
                  all(r['target_id'] in set(concepts)|set(baseline) and r['target_id']!=cid
                      and all(sid in sources for sid in r['source_ids']) for r in combined['relations']),
                  f'{cid}: sources and nonself targets resolve')
    check(body_changes==['local:catalog:chemigram'], 'Chemigram is the only changed card body')
    check(set(bundles_changed)==set(changed), 'Every changed record has exactly one lineage entry')
    for retained in ['local:catalog:raft-consensus-algorithm','local:catalog:apostrophe-rhetoric',
                     'local:catalog:mulching','local:catalog:warranties-as-quality-assurance']:
        check(retained in concepts and retained not in mapping,f'{retained}: distinct subject retained')
    check(any(r['type']=='application_of' and r['target_id']=='Q329717'
              for r in concepts['local:catalog:warranties-as-quality-assurance']['relations']),
          'Supported warranty application edge is present')
    check(any(r['type']=='related_to' and r['target_id']=='Q549563'
              for r in concepts['local:catalog:mulching']['relations']),
          'Supported mulch material link is present')
    feature = concepts['Q814254']
    check(any(e['source_id']=='research-batch-006::h02' for e in feature['evidence']),
          'Archaeological Feature context source is cited at card level')
    metrics = read(HERE/'catalog-metrics.json')
    check(metrics['combined_sha256']==sha(HERE/'catalog.json')
          and metrics['pilot']['new_identities']==sum(cid not in baseline for cid in concepts),
          'Novelty metrics use the revised artifact and full baseline')
    return dict(schema_version=1,status='passed', checks_passed=len(checks),failed=[],
        accepted_distinct_ids=len(concepts),new_identities=sum(cid not in baseline for cid in concepts),
        reviewed_offered_matches=len(decisions),review_actions=dict(Counter(r['action'] for r in decisions)),
        reused_registered_ids=len(mapping),changed_record_bundles=len(changed),changed_card_bodies=body_changes,
        protected_files=len(protection),combined_sha256=sha(HERE/'catalog.json'),
        canonical_content_sha256=canonical,limit='Structural and revision checks; no certification of every factual claim.')


if __name__ == '__main__':
    result = verify()
    (HERE/'structural-validation.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True))
