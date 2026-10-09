from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime, timezone
from urllib.parse import quote, urlsplit
import copy, hashlib, json, re, unicodedata

ROOT = Path('/Users/baorenliu/Documents/Programming/Python/ProductSpace')
PILOT = ROOT / 'data/catalog-candidates/scale-pilot-001'
OUT = PILOT / 'local-review'
errors = []
def canonical(x):
    return json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
def check(ok, code, detail):
    if not ok:
        errors.append({'code': code, 'detail': detail})
def load(p):
    def keys(rows):
        d = {}
        for k, v in rows:
            if k in d:
                raise ValueError(f'Duplicate key {k} in {p}')
            d[k] = v
        return d
    return json.loads(p.read_text(), object_pairs_hook=keys, parse_constant=lambda v: (_ for _ in ()).throw(ValueError(v)))
def norm(s):
    return ' '.join(unicodedata.normalize('NFKC', s).casefold().split())
def scoped(bid, sid):
    return bid + '::' + quote(sid, safe='')
def risk_features(c):
    f = {'scope:' + c['scope']: 5}
    f.update({'domain:' + d: 4 for d in c['domains'][:1]})
    f.update({'source:' + e['source_id']: 1 for e in c['evidence']})
    if c['entity_kind'] == 'named_subject': f['risk:named_subject'] = 4
    if c['scope'] == 'facet_or_application': f['risk:fine_application_wording'] = 3
    if '(' in c['label']: f['risk:sense_specific_label'] = 4
    if any(r['assertion'] == 'source_asserted' for r in c['relations']): f['risk:source_asserted_relationship'] = 4
    if any(r['assertion'] == 'editorial' for r in c['relations']): f['risk:editorial_relationship'] = 2
    if re.search(r'\b(under|assum|model|may|can|often|typically|conditional|ideal|approximate|experiment|study|studies)\b', c['card'], re.I): f['risk:qualification_or_assumption'] = 4
    return f
def risk_ids(cards, excluded):
    pool = {c['id']: c for c in cards if c['id'] not in excluded}
    covered, ids = set(), []
    while pool and len(ids) < 20:
        ranked = []
        for cid, c in pool.items():
            f = risk_features(c)
            ranked.append((-sum(v for k, v in f.items() if k not in covered), -sum(v for k, v in f.items() if k.startswith('risk:')), hashlib.sha256(('risk\n' + cid).encode()).hexdigest(), cid, f))
        _, _, _, cid, features = min(ranked)
        ids.append(cid); covered.update(features); pool.pop(cid)
    return ids

catalog = load(PILOT / 'catalog.json')
base = load(PILOT / 'baseline-index.json')
base_ids = set(base['concepts'])
selection = load(PILOT / 'selection-manifest.json')
selected = {c['id']: c for c in selection['accepted']}
plan = load(PILOT / 'coverage-plan.json')
baseline_checks = []
for row in load(PILOT / 'baseline-manifest.json')['inputs']:
    actual = sha(ROOT / row['path'])
    frozen_path = ROOT / 'data/catalog-candidates/archive/scale-pilot-001-delivery/evidence/inputs/unpacked' / row['path']
    pinned = sha(frozen_path)
    check(pinned == row['sha256'], 'pinned_baseline_input_changed', row['path'])
    baseline_checks.append({'path': row['path'], 'pinned_sha256': pinned, 'pinned_matches': pinned == row['sha256'], 'current_sha256': actual, 'current_matches': actual == row['sha256']})

active_ids = [c['id'] for c in catalog['concepts']]
all_ids = set(active_ids)
check(len(active_ids) == len(all_ids) == 1000, 'distinct_ids', len(all_ids))
check(all_ids == set(selected), 'selection_ids', 'Combined accepted set differs from selection')
check(len(base_ids) == 7224, 'baseline_count', len(base_ids))
sources = {s['id']: s for s in catalog['sources']}
check(len(sources) == len(catalog['sources']), 'duplicate_sources', len(sources))
scopes = {'broad_field', 'topic', 'idea', 'facet_or_application'}
rel_types = {'broader_topic', 'facet_of', 'application_of', 'related_to'}
required = {'id', 'label', 'aliases', 'entity_kind', 'scope', 'domains', 'learning_takeaway', 'card', 'original_description', 'identity_urls', 'evidence', 'relations', 'card_version', 'imported_records'}
aliases = defaultdict(set)
words = []
rels = []
for c in catalog['concepts']:
    cid = c['id']; n = len(c['card'].split()); words.append(n)
    check(required <= set(c), 'required_fields', cid)
    check(30 <= n <= 50, 'word_count', {'id': cid, 'words': n})
    check(c['scope'] in scopes and c['entity_kind'] in {'idea', 'named_subject'}, 'scope_kind', cid)
    check(type(c['card_version']) is int and c['card_version'] >= 1, 'card_version', cid)
    check(bool(c['evidence']), 'missing_evidence', cid)
    check(c['domains'][0] == selected[cid]['primary_domain'], 'primary_domain', cid)
    for a in [c['label'], *c['aliases']]: aliases[norm(a)].add(cid)
    for e in c['evidence']:
        check(e['source_id'] in sources and bool(e['locator']) and bool(e['note']), 'evidence', cid)
    for r in c['relations']:
        rels.append(r)
        check(r['target_id'] in all_ids | base_ids and r['target_id'] != cid, 'relation_target', cid)
        check(r['type'] in rel_types and r['assertion'] in {'source_asserted', 'editorial'}, 'relation_kind', cid)
        check(all(s in sources for s in r['source_ids']), 'relation_sources', cid)
        check(r['assertion'] != 'source_asserted' or bool(r['source_ids']), 'asserted_without_source', cid)
for s in sources.values():
    check(urlsplit(s['url']).scheme in {'http', 'https'} and bool(urlsplit(s['url']).netloc), 'source_url', s['id'])
    acquired = False
    for k in ['retrieved_at', 'retrieval_date']:
        if s.get(k):
            try: datetime.fromisoformat(s[k].replace('Z', '+00:00')); acquired = True
            except ValueError: check(False, 'source_timestamp', s['id'])
    check(acquired and bool(s['locator']) and 'revision' in s, 'source_metadata', s['id'])
expected_aliases = {k: sorted(v) for k, v in sorted(aliases.items())}
check(expected_aliases == catalog['batch']['alias_index'], 'alias_lookup', 'Alias index differs')

counts, frozen_checks = [], []
combined = {c['id']: c for c in catalog['concepts']}
input_union = set()
for n in range(3, 8):
    bid = f'research-batch-{n:03d}'
    path = ROOT / 'data/catalog-candidates' / (bid + '.json')
    batch = load(path); ids = {c['id'] for c in batch['concepts']}; h = sha(path)
    check(len(ids) == len(batch['concepts']) == 200, 'batch_count', bid)
    check(not (input_union & ids), 'cross_batch_duplicate_ids', bid); input_union |= ids
    check(ids == {cid for cid, p in selected.items() if p['owner'] == bid}, 'batch_ownership', bid)
    check({c['scope'] for c in batch['concepts']} == scopes, 'batch_scopes', bid)
    for s in batch['sources']:
        expected = copy.deepcopy(s)
        expected.update(id=scoped(bid, s['id']), original_id=s['id'], originating_batch_id=bid, originating_input_sha256=h)
        check(sources.get(expected['id']) == expected, 'source_provenance', expected['id'])
    for c in batch['concepts']:
        expected = copy.deepcopy(c)
        for e in expected['evidence']: e['source_id'] = scoped(bid, e['source_id'])
        for r in expected['relations']: r['source_ids'] = sorted({scoped(bid, sid) for sid in r['source_ids']})
        expected['relations'] = [json.loads(k) for k in sorted({canonical(r).decode() for r in expected['relations']})]
        check(combined.get(c['id']) == expected, 'combined_card_changed', c['id'])
        preserved = catalog['batch']['concept_provenance'][c['id']]
        check(len(preserved) == 1 and preserved[0]['original_record'] == c and preserved[0]['input_sha256'] == h, 'concept_provenance', c['id'])
    snapshot = [p for p in catalog['batch']['input_provenance'] if p['batch_id'] == bid]
    check(len(snapshot) == 1 and snapshot[0]['candidate_snapshot'] == batch and snapshot[0]['input_sha256'] == h, 'input_snapshot', bid)
    new = [c for c in batch['concepts'] if c['id'] not in base_ids]
    fine = [c for c in new if c['scope'] in {'idea', 'facet_or_application'}]
    counts.append({'batch': bid, 'accepted': len(ids), 'new': len(new), 'controls': len(ids) - len(new), 'new_fine_scope': len(fine), 'new_fine_ideas': sum(c['entity_kind'] == 'idea' for c in fine), 'named': sum(c['entity_kind'] == 'named_subject' for c in batch['concepts']), 'sha256': h})
    audit = PILOT / 'audits' / bid
    frozen = load(audit / 'sample.frozen.json')
    before = load(audit / 'candidate.before-audit.json')
    packet = load(audit / 'sample-cards.frozen.json')
    frame = sorted({c['id'] for c in before['concepts']} - base_ids)
    seed = f'OtherWise-scale-pilot-001:{bid}:source-audit'
    rand = sorted(frame, key=lambda cid: hashlib.sha256((seed + '\n' + cid).encode()).hexdigest())[:20]
    risk = risk_ids(before['concepts'], set(rand))
    checks = {'hash': sha(audit / 'candidate.before-audit.json') == frozen['pre_audit_candidate_sha256'], 'seed': frozen['seed'] == seed, 'frame': frame == frozen['new_id_frame'], 'random': rand == frozen['random_sample_ids'], 'risk': risk == [r['id'] for r in frozen['risk_sample']], 'sample': frozen['sample_ids'] == rand + risk, 'disjoint_40': len(set(rand + risk)) == 40, 'baseline': frozen['baseline_sha256'] == sha(PILOT / 'baseline-index.json'), 'packet_hash': packet['pre_audit_candidate_sha256'] == frozen['pre_audit_candidate_sha256'], 'packet_sources': packet['all_frozen_sources'] == before['sources']}
    before_cards = {c['id']: c for c in before['concepts']}
    checks['packet_cards'] = [r['id'] for r in packet['sample']] == rand + risk and all(r['card'] == before_cards[r['id']] for r in packet['sample'])
    for k, passed in checks.items(): check(passed, 'audit_' + k, bid)
    frozen_checks.append({'batch': bid, 'checks': checks, 'random': len(rand), 'risk': len(risk)})
check(input_union == all_ids, 'combined_union', 'Combined set differs from five input batches')
coverage = Counter((selected[cid]['primary_domain'], selected[cid]['primary_subfield']) for cid in all_ids)
primary = Counter(selected[cid]['primary_domain'] for cid in all_ids)
starting_counts = []
for b in plan['batches']:
    for d in b['primary_domains']:
        check(primary[d['domain']] == d['target_cards'], 'domain_target', d['domain'])
        for sub in d['starting_subfields']:
            number = coverage[d['domain'], sub]
            check(number >= 5, 'subfield_goal', [d['domain'], sub, number])
            starting_counts.append(number)
hashless = copy.deepcopy(catalog)
reported_canonical = hashless['validation'].pop('canonical_content_sha256')
check(hashlib.sha256(canonical(hashless)).hexdigest() == reported_canonical, 'canonical_hash', reported_canonical)
metrics = load(PILOT / 'catalog-metrics.json')
parent_types = {'broader_topic', 'facet_of', 'application_of'}
missing_asserted = [c['id'] for c in catalog['concepts'] if c['scope'] in {'idea', 'facet_or_application'} and not any(r['type'] in parent_types and r['assertion'] == 'source_asserted' for r in c['relations'])]
missing_any = [c['id'] for c in catalog['concepts'] if c['scope'] in {'idea', 'facet_or_application'} and not any(r['type'] in parent_types for r in c['relations'])]
summary = {'accepted': len(all_ids), 'new': len(all_ids - base_ids), 'controls': len(all_ids & base_ids), 'new_fine_scope': sum(x['new_fine_scope'] for x in counts), 'new_fine_ideas': sum(x['new_fine_ideas'] for x in counts), 'named': sum(x['named'] for x in counts), 'scope_counts': dict(Counter(c['scope'] for c in catalog['concepts'])), 'primary_domains': len(primary), 'starting_subfields': len(starting_counts), 'minimum_starting_subfield_count': min(starting_counts), 'source_records': len(sources), 'source_urls': len({s['url'] for s in sources.values()}), 'source_hostnames': len({urlsplit(s['url']).hostname for s in sources.values()}), 'relationships': len(rels), 'relation_types': dict(Counter(r['type'] for r in rels)), 'relation_assertions': dict(Counter(r['assertion'] for r in rels)), 'card_word_min': min(words), 'card_word_max': max(words), 'fine_without_asserted_parent_or_application': len(missing_asserted), 'fine_without_any_parent_or_application': len(missing_any), 'without_relationship': sum(not c['relations'] for c in catalog['concepts']), 'ambiguous_alias_groups': {a: sorted(ids) for a, ids in aliases.items() if len(ids) > 1}}
for key, actual in [('source_records', len(sources)), ('distinct_source_urls', summary['source_urls']), ('source_hostnames', summary['source_hostnames']), ('relationships', len(rels)), ('word_count_min', min(words)), ('word_count_max', max(words))]:
    check(metrics[key] == actual, 'reported_metric_mismatch', key)
result = {'schema_version': 1, 'checked_at': datetime.now(timezone.utc).isoformat(), 'status': 'passed_against_pinned_baseline' if not errors else 'failed', 'integration_readiness': 'current_baseline_reconciliation_required' if any(not r['current_matches'] for r in baseline_checks) else 'baseline_matches', 'combined_sha256': sha(PILOT / 'catalog.json'), 'summary': summary, 'batches': counts, 'baseline_inputs': baseline_checks, 'frozen_audits': frozen_checks, 'errors': errors, 'limits': ['Checks establish structural consistency and reproducible sampling; they do not certify semantic novelty, factual claims, original browsing or auditor independence.']}
OUT.mkdir(exist_ok=True)
(OUT / 'structural-validation.json').write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
print(json.dumps({'status': result['status'], 'summary': summary, 'errors': errors}, indent=2, ensure_ascii=False))
raise SystemExit(bool(errors))
