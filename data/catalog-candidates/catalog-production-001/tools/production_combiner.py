# Production-only copy: original pilot tool remains unchanged.
# Sole behavior change in validate_candidate is the new-card 1-25-word range.
#!/usr/bin/env python3
"""Deterministic, fail-closed OtherWise pilot assembly; no network or AI calls.

All inputs are read-only. A failed attempt writes a quarantine/report while the
last valid output remains byte-for-byte intact. See merge-validation/README.md.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import itertools
import json
import os
import re
import sys
import tempfile
import unicodedata
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from urllib.parse import quote, urlsplit

PILOT_ID = 'scale-pilot-001'
PILOT_BATCHES = {f'research-batch-{i:03d}' for i in range(3, 8)}
SCOPES = {'broad_field', 'topic', 'idea', 'facet_or_application'}
RELATIONS = {'broader_topic', 'facet_of', 'application_of', 'related_to'}
CONCEPT_FIELDS = {'id', 'label', 'aliases', 'entity_kind', 'scope', 'domains', 'learning_takeaway', 'card', 'original_description', 'identity_urls', 'evidence', 'relations', 'card_version', 'imported_records'}


def canonical_bytes(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')


def digest(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class Rejected(Exception):
    def __init__(self, errors):
        self.errors = errors
        super().__init__('; '.join(f"{e['code']}: {e['reason']}" for e in errors))


def reject(code, reason, path=None):
    e = {'code': code, 'reason': reason}
    if path is not None:
        e['path'] = str(path)
    raise Rejected([e])


def strict_load(path):
    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f'duplicate JSON key {key!r}')
            result[key] = value
        return result
    def bad_constant(value):
        raise ValueError(f'non-finite JSON value {value}')
    try:
        raw = Path(path).read_bytes()
        value = json.loads(raw.decode('utf-8'), object_pairs_hook=unique_keys, parse_constant=bad_constant)
        return value, hashlib.sha256(raw).hexdigest()
    except (OSError, UnicodeError, ValueError) as exc:
        reject('malformed_json', str(exc), path)


def text(value):
    return isinstance(value, str) and bool(value.strip())


def strings(value, nonempty=False):
    return isinstance(value, list) and (bool(value) or not nonempty) and all(text(x) for x in value)


def valid_url(value):
    if not text(value):
        return False
    parsed = urlsplit(value)
    return parsed.scheme in ('http', 'https') and bool(parsed.netloc)


def valid_date(value, timestamp=False):
    if not text(value):
        return False
    try:
        if timestamp:
            datetime.fromisoformat(value.replace('Z', '+00:00'))
        else:
            date.fromisoformat(value)
        return True
    except ValueError:
        return False


def validate_candidate(data, path):
    errors = []
    def add(code, reason):
        errors.append({'code': code, 'reason': reason, 'path': str(path)})
    if not isinstance(data, dict):
        reject('invalid_schema', 'Candidate must be an object.', path)
    required = {'schema_version', 'batch', 'sources', 'concepts', 'issues', 'validation'}
    for field in sorted(required - data.keys()):
        add('missing_field', f'Missing top-level {field}.')
    if errors:
        raise Rejected(errors)
    if type(data['schema_version']) is not int or data['schema_version'] != 1:
        add('invalid_schema', 'schema_version must be integer 1.')
    if not isinstance(data['batch'], dict) or data['batch'].get('id') not in PILOT_BATCHES:
        add('nonpilot_batch', 'Only research-batch-003 through research-batch-007 may be emitted.')
    if not isinstance(data['issues'], list) or not isinstance(data['validation'], dict):
        add('invalid_schema', 'issues must be an array and validation an object.')
    if not isinstance(data['sources'], list) or not isinstance(data['concepts'], list):
        add('invalid_schema', 'sources and concepts must be arrays.')
        raise Rejected(errors)
    if len(data['concepts']) > 200:
        add('batch_card_limit', 'A pilot batch may contain at most 200 accepted cards.')
    sources = {}
    for index, source in enumerate(data['sources']):
        prefix = f'sources[{index}]'
        if not isinstance(source, dict):
            add('invalid_source', f'{prefix} must be an object.')
            continue
        for field in ('id', 'title', 'url', 'locator', 'revision'):
            if field not in source:
                add('missing_field', f'{prefix}.{field} is required.')
        for field in ('id', 'title', 'locator'):
            if not text(source.get(field)):
                add('invalid_source', f'{prefix}.{field} must be nonempty text.')
        sid = source.get('id')
        if text(sid):
            if sid in sources:
                add('duplicate_source_id', f'{prefix}: local source ID {sid!r} occurs twice.')
            sources[sid] = source
        if not valid_url(source.get('url')):
            add('invalid_source', f'{prefix}.url must be an absolute HTTP(S) URL.')
        acquired = False
        for field, stamp in [('retrieval_date', False), ('retrieved_at', True)]:
            if field in source and source[field] is not None:
                if valid_date(source[field], stamp):
                    acquired = True
                else:
                    add('invalid_acquisition_metadata', f'{prefix}.{field} is not a valid ISO date/timestamp.')
        if not acquired:
            add('missing_acquisition_metadata', f'{prefix} needs a valid retrieval_date or retrieved_at.')
    ids = set()
    for index, concept in enumerate(data['concepts']):
        prefix = f'concepts[{index}]'
        if not isinstance(concept, dict):
            add('invalid_concept', f'{prefix} must be an object.')
            continue
        for field in sorted(CONCEPT_FIELDS - concept.keys()):
            add('missing_field', f'{prefix}.{field} is required.')
        for field in ('id', 'label', 'learning_takeaway', 'card'):
            if not text(concept.get(field)):
                add('invalid_concept', f'{prefix}.{field} must be nonempty text.')
        cid = concept.get('id')
        if text(cid):
            if cid in ids:
                add('duplicate_concept_id', f'{prefix}: concept ID {cid!r} occurs twice in a batch.')
            ids.add(cid)
        if concept.get('entity_kind') not in ('idea', 'named_subject'):
            add('invalid_concept', f'{prefix}.entity_kind is invalid.')
        if concept.get('scope') not in SCOPES:
            add('invalid_concept', f'{prefix}.scope is invalid.')
        for field in ('aliases', 'domains', 'identity_urls'):
            if not strings(concept.get(field), nonempty=(field == 'domains')):
                add('invalid_concept', f'{prefix}.{field} must be an array of nonempty strings.')
        if isinstance(concept.get('identity_urls'), list):
            if any(not valid_url(u) for u in concept['identity_urls']):
                add('invalid_concept', f'{prefix}.identity_urls contains a non-HTTP(S) URL.')
        if concept.get('original_description') is not None and not isinstance(concept['original_description'], str):
            add('invalid_concept', f'{prefix}.original_description must be text or null.')
        if type(concept.get('card_version')) is not int or concept['card_version'] < 1:
            add('invalid_version', f'{prefix}.card_version must be a positive integer.')
        if text(concept.get('card')) and not 1 <= len(concept['card'].split()) <= 25:
            add('word_budget', f'{prefix}.card has {len(concept["card"].split())} whitespace-separated words; expected 1–25.')
        if not isinstance(concept.get('imported_records'), list):
            add('invalid_concept', f'{prefix}.imported_records must be an array.')
        evidence = concept.get('evidence')
        if not isinstance(evidence, list) or not evidence:
            add('invalid_evidence', f'{prefix}.evidence must be a nonempty array.')
        else:
            for e in evidence:
                if not isinstance(e, dict) or any(not text(e.get(k)) for k in ('source_id', 'locator', 'note')):
                    add('invalid_evidence', f'{prefix} contains malformed evidence.')
                elif e['source_id'] not in sources:
                    add('unresolved_source', f'{prefix} evidence refers to absent local source {e["source_id"]}.')
        relations = concept.get('relations')
        if not isinstance(relations, list):
            add('invalid_relation', f'{prefix}.relations must be an array.')
        else:
            for relation in relations:
                if not isinstance(relation, dict):
                    add('invalid_relation', f'{prefix} contains a non-object relation.')
                    continue
                if any(not text(relation.get(k)) for k in ('target_id', 'note')) or relation.get('type') not in RELATIONS or relation.get('assertion') not in ('editorial', 'source_asserted'):
                    add('invalid_relation', f'{prefix} contains a malformed relation.')
                if not strings(relation.get('source_ids'), nonempty=relation.get('assertion') == 'source_asserted'):
                    add('invalid_relation', f'{prefix} relation needs a source_ids array; source_asserted requires at least one.')
                elif any(s not in sources for s in relation['source_ids']):
                    add('unresolved_source', f'{prefix} relation refers to an absent local source.')
    if errors:
        raise Rejected(errors)


def baseline_ids(data):
    if not isinstance(data, dict):
        reject('invalid_baseline', 'Pinned baseline must be an object.')
    values = data.get('concepts', data.get('ids'))
    if isinstance(values, dict):
        ids = list(values)
    elif isinstance(values, list):
        ids = [c.get('id') if isinstance(c, dict) else c for c in values]
    else:
        reject('invalid_baseline', 'Pinned baseline needs a concepts mapping/list or ids list.')
    if not all(text(x) for x in ids) or len(ids) != len(set(ids)):
        reject('invalid_baseline', 'Baseline IDs must be unique nonempty strings.')
    return set(ids)


def decisions_schema(data):
    if not isinstance(data, dict) or data.get('schema_version') != 1:
        reject('invalid_decisions', 'Decisions must be an object with schema_version 1.')
    result = copy.deepcopy(data)
    for key in ('equivalences', 'distinctness', 'unresolved'):
        result.setdefault(key, [])
        if not isinstance(result[key], list) or any(not isinstance(d, dict) for d in result[key]):
            reject('invalid_decisions', f'{key} must be an array of objects.')
    for key in ('concept_versions', 'batch_versions'):
        result.setdefault(key, {})
        if not isinstance(result[key], dict) or any(not isinstance(d, dict) for d in result[key].values()):
            reject('invalid_decisions', f'{key} must map IDs to decision objects.')
    return result


def reviewed(decision):
    return decision.get('reviewed') is True and text(decision.get('reason'))


def members(decision):
    ids = decision.get('member_ids')
    if not strings(ids, True) or len(set(ids)) != len(ids):
        reject('invalid_decisions', 'member_ids must be a nonempty array of unique IDs.')
    return set(ids)


def review_evidence(decision):
    items = decision.get('evidence')
    return isinstance(items, list) and bool(items) and all(isinstance(e, dict) and valid_url(e.get('url')) and text(e.get('locator')) and text(e.get('note')) for e in items)


def unique(items):
    return [json.loads(k) for k in sorted({canonical_bytes(i).decode('utf-8') for i in items})]


def normalize_alias(value):
    return ' '.join(unicodedata.normalize('NFKC', value).casefold().split())


def ref_id(batch_id, source_id):
    return batch_id + '::' + quote(source_id, safe='')


def chosen_record(records, choice, code):
    if not isinstance(choice, dict) or not reviewed(choice):
        reject(code, 'Conflicting records require a reviewed, reasoned, hash-bound version choice.')
    matches = [r for r in records if r['batch_id'] == choice.get('batch_id') and r['input_sha256'] == choice.get('input_sha256') and r['record']['card_version'] == choice.get('card_version') and (choice.get('concept_id') is None or r['record']['id'] == choice['concept_id'])]
    if len(matches) != 1:
        reject('invalid_version_choice', 'Version choice does not select exactly one supplied card snapshot.')
    return matches[0]


def assemble(input_paths, baseline_path, decision_path, require_all=False):
    baseline, baseline_sha = strict_load(baseline_path)
    pinned_ids = baseline_ids(baseline)
    decision_data, decisions_sha = strict_load(decision_path)
    decisions = decisions_schema(decision_data)
    inputs = {}
    for path in input_paths:
        data, sha = strict_load(path)
        validate_candidate(data, path)
        inputs.setdefault(sha, {'sha': sha, 'data': data})
    if not inputs:
        reject('missing_inputs', 'At least one candidate input is required.')
    by_batch = defaultdict(list)
    for item in inputs.values():
        by_batch[item['data']['batch']['id']].append(item)
    if require_all and set(by_batch) != PILOT_BATCHES:
        reject('missing_pilot_batches', 'Missing pilot batches: ' + ', '.join(sorted(PILOT_BATCHES - set(by_batch))))
    selected = []
    for bid in sorted(by_batch):
        variants = by_batch[bid]
        if len(variants) == 1:
            selected.append(variants[0])
        else:
            choice = decisions['batch_versions'].get(bid, {})
            matches = [v for v in variants if v['sha'] == choice.get('input_sha256')]
            if not reviewed(choice) or len(matches) != 1:
                reject('batch_revision_conflict', f'{bid} has competing input snapshots; explicitly choose an input_sha256.')
            selected.append(matches[0])
    all_sources = []
    records = defaultdict(list)
    for item in selected:
        bid = item['data']['batch']['id']
        for source in item['data']['sources']:
            s = copy.deepcopy(source)
            s.update(id=ref_id(bid, source['id']), original_id=source['id'], originating_batch_id=bid, originating_input_sha256=item['sha'])
            all_sources.append(s)
        for original in item['data']['concepts']:
            c = copy.deepcopy(original)
            for e in c['evidence']:
                e['source_id'] = ref_id(bid, e['source_id'])
            for r in c['relations']:
                r['source_ids'] = sorted({ref_id(bid, s) for s in r['source_ids']})
            records[c['id']].append({'batch_id': bid, 'input_sha256': item['sha'], 'record': c, 'original_record': copy.deepcopy(original), 'combined_source_id_map': {source['id']: ref_id(bid, source['id']) for source in item['data']['sources']}})
    accepted_ids = set(records)
    known_ids = accepted_ids | pinned_ids
    for unresolved in decisions['unresolved']:
        group = members(unresolved)
        if group & accepted_ids and group <= known_ids:
            reject('unresolved_identity', f'Accepted identities have an unresolved review: {sorted(group)}. {unresolved.get("reason", "")}')
    equivalents = {}
    equivalence_groups = {}
    for decision in decisions['equivalences']:
        group = members(decision)
        if not reviewed(decision) or not review_evidence(decision):
            reject('unreviewed_equivalence', 'Equivalence needs explicit review, a reason and inspected evidence locators.')
        canonical = decision.get('canonical_id')
        if canonical not in group or not group <= known_ids:
            reject('invalid_equivalence', 'Equivalence canonical/member IDs must resolve in pilot or baseline.')
        if any(cid in equivalents for cid in group):
            reject('overlapping_equivalence', 'Overlapping equivalence groups must be centrally flattened and reviewed.')
        for cid in group:
            equivalents[cid] = canonical
        equivalence_groups[canonical] = decision
    distinct_pairs = set()
    for decision in decisions['distinctness']:
        group = members(decision)
        if not reviewed(decision) or not review_evidence(decision):
            reject('unreviewed_distinctness', 'Distinctness needs explicit review, a reason and inspected evidence locators.')
        if not group <= known_ids:
            reject('invalid_distinctness', 'Distinctness member IDs must resolve in pilot or baseline.')
        distinct_pairs.update(frozenset(pair) for pair in itertools.combinations(group, 2))
    active_records = defaultdict(list)
    originals_by_canonical = defaultdict(list)
    for cid in sorted(records):
        variants = records[cid]
        canonical = equivalents.get(cid, cid)
        originals_by_canonical[canonical].extend(variants)
        if len({digest(r['record']) for r in variants}) > 1:
            selected_record = chosen_record(variants, decisions['concept_versions'].get(cid), 'concept_conflict')
        else:
            selected_record = sorted(variants, key=lambda r: (r['batch_id'], r['input_sha256']))[0]
        active_records[canonical].append(selected_record)
    concepts = []
    chosen_versions = {}
    for cid in sorted(active_records):
        variants = active_records[cid]
        eq = equivalence_groups.get(cid)
        if eq:
            choice = dict(eq.get('selected_card', {}), reviewed=True, reason=eq['reason'])
            picked = chosen_record(variants, choice, 'missing_equivalence_card_choice')
        else:
            picked = variants[0]
        c = copy.deepcopy(picked['record'])
        c['id'] = cid
        chosen_versions[cid] = {k: picked[k] for k in ('batch_id', 'input_sha256')}
        chosen_versions[cid].update(original_id=picked['record']['id'], card_version=c['card_version'])
        if eq:
            c['aliases'] = sorted({name for r in variants for name in [r['record']['label'], *r['record']['aliases']]})
            c['identity_urls'] = sorted({u for r in variants for u in r['record']['identity_urls']})
            c['domains'] = list(c['domains']) + sorted({d for r in variants for d in r['record']['domains']} - set(c['domains']))
            for key in ('evidence', 'relations', 'imported_records'):
                c[key] = unique([v for r in variants for v in r['record'][key]])
        for relation in c['relations']:
            relation['target_id'] = equivalents.get(relation['target_id'], relation['target_id'])
        c['relations'] = unique(c['relations'])
        concepts.append(c)
    final_ids = {c['id'] for c in concepts}
    source_ids = {s['id'] for s in all_sources}
    alias_index = defaultdict(set)
    for c in concepts:
        for label in [c['label'], *c['aliases']]:
            alias_index[normalize_alias(label)].add(c['id'])
        for e in c['evidence']:
            if e['source_id'] not in source_ids:
                reject('unresolved_source', f'{c["id"]} has unresolved combined evidence {e["source_id"]}.')
        for r in c['relations']:
            if r['target_id'] == c['id']:
                reject('self_relation', f'{c["id"]} has a self-relation, possibly introduced by equivalence remapping; review or remove it explicitly.')
            if r['target_id'] not in final_ids | pinned_ids:
                reject('unresolved_target', f'{c["id"]} points to {r["target_id"]}, absent from the combined catalog and pinned baseline.')
            if any(s not in source_ids for s in r['source_ids']):
                reject('unresolved_source', f'{c["id"]} has unresolved combined relation references.')
    for alias, ids in alias_index.items():
        for pair in itertools.combinations(sorted(ids), 2):
            if frozenset(pair) not in distinct_pairs:
                reject('unreviewed_alias_collision', f'Alias {alias!r} names distinct IDs {pair}; review equivalence or distinctness explicitly.')
    provenance = {}
    for cid, variants in sorted(originals_by_canonical.items()):
        provenance[cid] = sorted([{'batch_id': r['batch_id'], 'input_sha256': r['input_sha256'], 'original_id': r['original_record']['id'], 'card_version': r['original_record']['card_version'], 'original_record': r['original_record'], 'reference_namespace': {'batch_id': r['batch_id'], 'input_sha256': r['input_sha256'], 'scope': 'original_snapshot_local_ids'}, 'combined_source_id_map': r['combined_source_id_map']} for r in variants], key=lambda r: (r['batch_id'], r['input_sha256'], r['original_id']))
    active_hashes = {i['sha'] for i in selected}
    result = {
        'schema_version': 1,
        'batch': {
            'id': PILOT_ID, 'kind': 'combined_pilot_candidate',
            'input_provenance': [{'input_sha256': i['sha'], 'batch_id': i['data']['batch']['id'], 'selected': i['sha'] in active_hashes, 'reference_namespace': {'batch_id': i['data']['batch']['id'], 'input_sha256': i['sha'], 'scope': 'original_snapshot_local_ids'}, 'candidate_snapshot': i['data']} for i in sorted(inputs.values(), key=lambda i: (i['data']['batch']['id'], i['sha']))],
            'baseline': {'sha256': baseline_sha, 'identity_count': len(pinned_ids), 'role': 'pinned_target_snapshot_not_emitted'},
            'identity_decisions_sha256': decisions_sha, 'identity_decisions': decisions,
            'selected_card_versions': chosen_versions, 'concept_provenance': provenance,
            'alias_index': {alias: sorted(ids) for alias, ids in sorted(alias_index.items())},
        },
        'sources': sorted(all_sources, key=lambda s: s['id']), 'concepts': concepts,
        'issues': unique([{'originating_batch_id': i['data']['batch']['id'], 'issue': issue} for i in selected for issue in i['data']['issues']]),
        'validation': {
            'structural_passed': True, 'distinct_concept_count': len(concepts), 'reference_count': len(all_sources),
            'relation_count': sum(len(c['relations']) for c in concepts), 'baseline_snapshot_records_added': 0,
            'limit': 'Structural validation does not certify facts, source inspection, semantic distinctness, or independent audit completion.'
        }
    }
    result['validation']['canonical_content_sha256'] = digest(result)
    return result


def atomic_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, prefix='.' + path.name, suffix='.tmp', delete=False) as handle:
        temp = Path(handle.name)
        try:
            json.dump(data, handle, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
            handle.write('\n')
            handle.flush()
            os.fsync(handle.fileno())
        except Exception:
            temp.unlink(missing_ok=True)
            raise
    os.replace(temp, path)


def quarantine(args, errors, prior_sha):
    artifacts = []
    for p in sorted(set(args.inputs)):
        item = {'path': str(Path(p).resolve())}
        try:
            raw = Path(p).read_bytes()
            item.update(sha256=hashlib.sha256(raw).hexdigest(), input_text=raw.decode('utf-8', errors='replace'))
        except OSError as exc:
            item['read_error'] = str(exc)
        artifacts.append(item)
    record = {'status': 'quarantined', 'errors': errors, 'input_artifacts': artifacts}
    qpath = Path(args.report).parent / 'quarantine' / (digest(record) + '.json')
    atomic_json(qpath, record)
    retained = prior_sha is not None and Path(args.output).exists() and file_hash(args.output) == prior_sha
    report = {'status': 'quarantined', 'errors': errors, 'quarantine_path': str(qpath.resolve()), 'last_valid_output_retained': retained, 'last_valid_output_sha256': prior_sha, 'passed': [], 'failed': sorted({e['code'] for e in errors}), 'unrun': ['output_publication']}
    atomic_json(args.report, report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('combine', 'verify-actual'))
    parser.add_argument('--inputs', nargs='+', required=True)
    parser.add_argument('--baseline', required=True)
    parser.add_argument('--decisions', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--report', required=True)
    parser.add_argument('--require-all-batches', action='store_true')
    args = parser.parse_args(argv)
    protected = {Path(p).resolve() for p in [*args.inputs, args.baseline, args.decisions]}
    if Path(args.output).resolve() in protected or Path(args.report).resolve() in protected or Path(args.output).resolve() == Path(args.report).resolve():
        print('Refusing an output/report path that would overwrite an input or each other.', file=sys.stderr)
        return 2
    prior_sha = file_hash(args.output) if Path(args.output).exists() else None
    try:
        result = assemble(args.inputs, args.baseline, args.decisions, args.require_all_batches)
        passed = ['structural_validation', 'source_and_target_resolution', 'pilot_only_concepts']
        if args.command == 'verify-actual':
            reverse = assemble(list(reversed(args.inputs)), args.baseline, args.decisions, args.require_all_batches)
            repeated = assemble(args.inputs + [args.inputs[0]], args.baseline, args.decisions, args.require_all_batches)
            if canonical_bytes(result) != canonical_bytes(reverse):
                reject('input_order_dependence', 'Reversed inputs changed canonical content or decisions.')
            if canonical_bytes(result) != canonical_bytes(repeated):
                reject('repeated_import_changed_output', 'Repeated import changed content, counts or decisions.')
            if Path(args.output).exists():
                existing, _ = strict_load(args.output)
                if canonical_bytes(existing) != canonical_bytes(result):
                    reject('existing_output_mismatch', 'Existing combined artifact differs from the reproducible result; inspect it and explicitly run combine to replace it.')
            passed += ['reversed_input_order', 'repeated_import']
        atomic_json(args.output, result)
        report = {'status': 'passed', 'command': args.command, 'passed': sorted(passed), 'failed': [], 'unrun': [], 'canonical_content_sha256': result['validation']['canonical_content_sha256'], 'output_sha256': file_hash(args.output), 'counts': {k: result['validation'][k] for k in ('distinct_concept_count', 'reference_count', 'relation_count')}, 'all_five_batches_required': args.require_all_batches}
        atomic_json(args.report, report)
        print(json.dumps(report, sort_keys=True))
        return 0
    except Rejected as exc:
        report = quarantine(args, exc.errors, prior_sha)
    except (ValueError, TypeError, KeyError, AttributeError, OSError) as exc:
        report = quarantine(args, [{'code': 'invalid_input', 'reason': f'{type(exc).__name__}: {exc}'}], prior_sha)
    print(json.dumps(report, sort_keys=True), file=sys.stderr)
    return 1


if __name__ == '__main__':
    sys.exit(main())
