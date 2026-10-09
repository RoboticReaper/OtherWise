"""Version a research candidate using explicit, hash-bound meaning reviews.

No production registry writes, network requests, or label-based automatic merges.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
import shutil
import sys


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                         separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_suffix(path.suffix + '.pending')
    pending.write_text(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                 indent=2, allow_nan=False) + '\n')
    pending.replace(path)


def unique(values):
    result, seen = [], set()
    for value in values:
        key = digest(value)
        if key not in seen:
            seen.add(key)
            result.append(copy.deepcopy(value))
    return result


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def inspected(evidence):
    return isinstance(evidence, list) and bool(evidence) and all(
        isinstance(e, dict) and e.get('url', '').startswith('https://')
        and bool(e.get('locator', '').strip()) for e in evidence)


def revise(batches, decisions, baseline, raw_imports, input_hashes, corrections):
    """Return revised copies and full changed-record lineage; reject stale reviews."""
    originals, owners = {}, {}
    for batch in batches:
        bid = batch['batch']['id']
        require(bid in input_hashes, f'Missing input hash for {bid}')
        for record in batch['concepts']:
            require(record['id'] not in originals, f'Duplicate original ID {record["id"]}')
            originals[record['id']] = record
            owners[record['id']] = bid
    reviews, mapping = {}, {}
    for decision in decisions:
        cid = decision['id']
        require(cid in originals and cid not in reviews, f'Unknown or repeated decision {cid}')
        require(decision.get('reviewed') is True and decision.get('reason')
                and inspected(decision.get('evidence')), f'Unreviewed meaning decision {cid}')
        require(decision.get('input_sha256') == input_hashes[owners[cid]]
                and decision.get('candidate_record_sha256') == digest(originals[cid]),
                f'Stale meaning review {cid}')
        action = decision.get('action')
        require(action in {'reuse_existing', 'distinct_meaning', 'distinct_facet'},
                f'Unresolved meaning decision {cid}')
        if action == 'reuse_existing':
            target = decision.get('target_id')
            require(target in baseline and target != cid, f'Invalid registered target for {cid}')
            mapping[cid] = target
        else:
            require(decision.get('target_id') is None, f'Distinct meaning cannot reuse an ID: {cid}')
        reviews[cid] = decision
    final_ids = [mapping.get(cid, cid) for cid in originals]
    require(len(set(final_ids)) == len(final_ids), 'Canonical IDs collide; choose versions explicitly')
    corrected = {}
    for correction in corrections:
        cid = correction['id']
        require(cid in originals and cid not in corrected, f'Unknown or repeated correction {cid}')
        require(correction['before'] == originals[cid], f'Stale correction {cid}')
        require(correction['after']['id'] == cid
                and correction['after']['card_version'] > originals[cid]['card_version'],
                f'Correction needs a new version for {cid}')
        corrected[cid] = correction
    result, changed, added_relations = [], [], []
    for batch in batches:
        out = copy.deepcopy(batch)
        bid = batch['batch']['id']
        sources = {s['id']: s for s in out['sources']}
        for correction in corrections:
            if owners[correction['id']] == bid:
                for source in correction.get('additional_sources', []):
                    require(source['id'] not in sources or sources[source['id']] == source,
                            f'Conflicting correction reference {source["id"]}')
                    sources[source['id']] = copy.deepcopy(source)
        revised_records = []
        for original in batch['concepts']:
            old_id = original['id']
            record = copy.deepcopy(corrected.get(old_id, {}).get('after', original))
            if old_id in mapping:
                cid = mapping[old_id]
                base = baseline[cid]
                record['id'] = cid
                record['aliases'] = sorted(set(record['aliases']) | set(base['aliases']) | {base['label']})
                record['original_description'] = base['original_description']
                record['imported_records'] = unique(record['imported_records']
                                  + raw_imports[cid]['imported_records'])
                if cid.startswith('Q') and cid[1:].isdigit():
                    record['identity_urls'] = sorted(set(record['identity_urls'])
                                          | {f'https://www.wikidata.org/wiki/{cid}'})
            for relation in record['relations']:
                relation['target_id'] = mapping.get(relation['target_id'], relation['target_id'])
            proposal = reviews.get(old_id, {}).get('proposed_relation')
            if proposal:
                require(reviews[old_id]['action'] == 'distinct_facet',
                        f'Unexpected relation proposal for {old_id}')
                require(inspected(proposal.get('evidence')), f'Unevidenced relation for {old_id}')
                require(proposal.get('type') in {'related_to', 'facet_of', 'application_of', 'broader_topic'}
                        and proposal.get('assertion_class') in {'source_asserted', 'editorial'},
                        f'Invalid relation type for {old_id}')
                source_ids = []
                for item in proposal['evidence']:
                    matches = sorted(sid for sid, source in sources.items() if source['url'] == item['url'])
                    require(matches, f'New relation source is absent from batch {bid}: {item["url"]}')
                    source_ids.append(matches[0])
                relation = dict(type=proposal['type'], target_id=proposal['target'],
                                assertion=proposal['assertion_class'], source_ids=sorted(set(source_ids)),
                                note=proposal['note'])
                record['relations'] = unique(record['relations'] + [relation])
                added_relations.append(dict(id=record['id'], relation=relation,
                                            evidence=copy.deepcopy(proposal['evidence'])))
            for relation in record['relations']:
                require(relation['target_id'] != record['id'], f'Self relation after revision: {old_id}')
                require(relation['target_id'] in set(final_ids) | set(baseline),
                        f'Unresolved revised target: {relation["target_id"]}')
            fields = sorted(k for k in set(original) | set(record)
                            if k != 'card_version' and original.get(k) != record.get(k))
            if fields:
                record['card_version'] = max(record['card_version'], original['card_version'] + 1,
                    baseline.get(record['id'], {}).get('latest_card_version', 0) + 1)
                changed.append(dict(original_id=old_id, canonical_id=record['id'], batch_id=bid,
                    original_input_sha256=input_hashes[bid], changed_fields=fields,
                    original_record=copy.deepcopy(original), revised_record_sha256=digest(record),
                    original_card_version=original['card_version'], revised_card_version=record['card_version'],
                    meaning_review=copy.deepcopy(reviews.get(old_id)),
                    correction_applied=old_id in corrected))
            revised_records.append(record)
        out['concepts'] = revised_records
        out['sources'] = list(sources.values())
        out['batch'] = dict(id=bid, pilot_id='scale-pilot-001',
            revision=batch['batch'].get('revision', 1) + 1, kind='versioned_reconciled_candidate',
            previous_input_sha256=input_hashes[bid],
            historical_batch_metadata=copy.deepcopy(batch['batch']),
            historical_audit_scope='Original delivery only; revised records require the new revision checks.')
        out['validation'] = dict(status='awaiting_revised_candidate_validation')
        result.append(out)
    return result, dict(schema_version=1, status='applied_to_candidate_revision',
                        legacy_id_redirects=mapping, reviewed_decisions=len(reviews),
                        changed_records=changed, added_relations=added_relations,
                        applied_corrections=sorted(corrected))


def freeze_baseline(project, destination):
    """Pin actual runtime identity rules plus the two prior accepted candidates."""
    project, destination = Path(project).resolve(), Path(destination).resolve()
    input_paths = ['data/topics.json', 'data/discovery_graph.json', 'data/recommendation-identities.json',
                   'data/catalog-candidates/research-batch-001.json',
                   'data/catalog-candidates/research-batch-002.json']
    manifest_path = destination / 'baseline-manifest.json'
    if manifest_path.exists():
        manifest = read(manifest_path)
        for item in manifest['inputs']:
            require(sha(project/item['path']) == item['sha256'], f'Current baseline changed: {item["path"]}')
            require(sha(destination/item['snapshot']) == item['sha256'], 'Pinned input snapshot changed')
        require(sha(destination/'baseline-index.json') == manifest['baseline_index_sha256'], 'Baseline index changed')
        require(sha(destination/'baseline-imported-records.json') == manifest['baseline_imported_records_sha256'],
                'Baseline raw records changed')
        return manifest
    sys.path.insert(0, str(project))
    from recommendation_lab.inventory import Inventory
    from explorer import _key
    pinned = []
    for relative in input_paths:
        snapshot = 'baseline-inputs/' + relative
        target = destination/snapshot
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(project/relative, target)
        pinned.append(dict(path=relative, snapshot=snapshot, sha256=sha(target), size_bytes=target.stat().st_size))
        require(sha(project/relative) == sha(target), f'Input changed while pinning {relative}')
    broad, graph, registry = [read(destination/'baseline-inputs'/p) for p in input_paths[:3]]
    inventory = Inventory.from_sources(broad, graph, registry)
    concepts, raw = {}, {}
    for cid, concept in inventory.concepts.items():
        concepts[cid] = dict(id=cid, label=concept['topic'], aliases=sorted(concept['aliases']),
            original_description=concept['description'], inventory_records=copy.deepcopy(concept['records']),
            candidate_records=[], domains=[])
        rows = []
        for record in concept['records']:
            kind, index = record['kind'], record['index']
            source_rows = broad if kind == 'broad' else registry['resolver_concepts'] if kind == 'resolver' else [
                          n for n in graph['nodes'] if n['kind'] == 'concept']
            row = copy.deepcopy(source_rows[index])
            row.update(inventory_kind=kind, index=index)
            rows.append(row)
            if kind == 'broad' and row.get('domain'):
                concepts[cid]['domains'].append(row['domain'])
        concepts[cid]['domains'] = sorted(set(concepts[cid]['domains']))
        raw[cid] = dict(original_description=concept['description'], imported_records=rows,
                        previous_candidate_records=[])
    revisions = []
    for relative in input_paths[3:]:
        data = read(destination/'baseline-inputs'/relative)
        bid, revision = data['batch']['id'], data['batch'].get('revision', 1)
        revisions.append(dict(batch_id=bid, revision=revision, sha256=sha(project/relative),
                              path=relative, concepts=len(data['concepts'])))
        for card in data['concepts']:
            cid = card['id']
            base = concepts.setdefault(cid, dict(id=cid, label=card['label'], aliases=[],
                original_description=card['original_description'], inventory_records=[],
                candidate_records=[], domains=[]))
            base['aliases'] = sorted(set(base['aliases']) | set(card['aliases']) | {card['label']})
            previous = dict(batch_id=bid, batch_revision=revision, record=copy.deepcopy(card))
            base['candidate_records'].append(previous)
            base['domains'] = sorted(set(base['domains']) | set(card['domains']))
            base['latest_card_version'] = card['card_version']
            base['latest_candidate_batch'] = bid
            source = raw.setdefault(cid, dict(original_description=base['original_description'],
                                              imported_records=[], previous_candidate_records=[]))
            source['imported_records'] = unique(source['imported_records'] + card['imported_records'])
            source['previous_candidate_records'].append(previous)
    aliases = defaultdict(set)
    for cid, concept in concepts.items():
        for label in [concept['label'], *concept['aliases']]:
            aliases[_key(label)].add(cid)
    index = dict(schema_version=1, pilot_id='scale-pilot-001', inventory_fingerprint=inventory.version,
                 concepts=concepts, aliases={k: sorted(v) for k, v in sorted(aliases.items())})
    write(destination/'baseline-index.json', index)
    write(destination/'baseline-imported-records.json', dict(schema_version=1,
        baseline_index_sha256=sha(destination/'baseline-index.json'), concepts=raw))
    manifest = dict(schema_version=1, pilot_id='scale-pilot-001', revision='002',
        frozen_at=datetime.now(timezone.utc).isoformat(), inputs=pinned, active_candidate_revisions=revisions,
        inventory_identity_count=len(inventory.concepts), baseline_identity_count_by_id=len(concepts),
        baseline_inventory_fingerprint=inventory.version,
        baseline_index_sha256=sha(destination/'baseline-index.json'),
        baseline_imported_records_sha256=sha(destination/'baseline-imported-records.json'),
        identity_implementation_sha256=sha(project/'recommendation_lab/inventory.py'),
        status='frozen_full_current_inventory', archived_copies_counted=False,
        scope='Current runtime inventory and active candidates 001/002 before admitting this pilot revision.')
    write(manifest_path, manifest)
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--freeze-baseline', type=Path, required=True)
    args = parser.parse_args()
    manifest = freeze_baseline(args.project, args.freeze_baseline)
    print(json.dumps({k: manifest[k] for k in ['inventory_identity_count', 'baseline_identity_count_by_id',
                                             'baseline_index_sha256', 'status']}))
