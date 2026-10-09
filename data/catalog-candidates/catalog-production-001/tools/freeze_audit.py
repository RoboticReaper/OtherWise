"""Freeze an assembled draft and select reproducible random/risk audit strata."""
import argparse
import copy
import json
import random
import re
import shutil
from collections import Counter
from pathlib import Path

from assemble import sha, read, STOCK


def freeze(batch_dir, candidate_path, seed):
    candidate = read(candidate_path)
    destination = batch_dir/'frozen-initial'
    if destination.exists(): raise ValueError('Initial audit evidence already exists; preserve the fixed sample.')
    destination.mkdir()
    files = {}
    originals = [candidate_path, batch_dir/'selection-manifest.json', batch_dir/'identity-decisions.json']
    for owner_dir in sorted((batch_dir/'research').iterdir()):
        originals += [p for p in owner_dir.iterdir() if p.is_file() and p.suffix in ('.json', '.md')
                      and p.name != 'eligible-identities.json']
    for path in originals:
        relative = path.relative_to(batch_dir)
        target = destination/relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
        files[str(relative)] = dict(sha256=sha(target), bytes=target.stat().st_size)
    cards = sorted(candidate['concepts'], key=lambda c: c['id'])
    if len(cards) < 40: raise ValueError('Forty disjoint audit cards require at least 40 accepted drafts.')
    generator = random.Random(seed)
    sampled = generator.sample(cards, 20)
    random_ids = {c['id'] for c in sampled}
    remaining = [c for c in cards if c['id'] not in random_ids]

    def risk(c):
        value = 2*(c['entity_kind'] == 'named_subject')+2*(c['scope'] == 'facet_or_application')
        value += int(len(c['card'].split()) >= 23)+int('(' in c['label'])+int(len(c['domains']) > 1)
        value += 2*bool(re.search(r'\b(if|only|unless|under|may|typically|assuming|cannot|when)\b', c['card'], re.I))
        value += bool(c['relations'])
        return value

    ranked = sorted(remaining, key=lambda c: (-risk(c), c['id']))
    targeted = []
    coverage = {c['domains'][0] for c in sampled}
    all_domains = {c['domains'][0] for c in cards}
    reasons = {}
    for domain in sorted(all_domains-coverage):
        c = next(c for c in ranked if c['domains'][0] == domain)
        targeted.append(c); reasons[c['id']] = 'Domain absent from random stratum; highest declared risk score in this domain.'
    scopes = {c['scope'] for c in sampled+targeted}
    for scope in sorted({c['scope'] for c in cards}-scopes):
        c = next(c for c in ranked if c['scope'] == scope and c not in targeted)
        targeted.append(c); reasons[c['id']] = 'Scope absent from current audit coverage; highest declared risk score.'
    for c in ranked:
        if len(targeted) >= 20: break
        if c not in targeted:
            targeted.append(c); reasons[c['id']] = 'Named/facet/qualification/long-body/relationship risk heuristic.'
    if len(targeted) != 20: raise ValueError('Audit coverage requirements exceed the 20-card risk stratum.')
    refs = {s['id']: s for s in candidate['sources']}
    entries = []
    for stratum, group in [('random', sampled), ('risk', targeted)]:
        for c in group:
            source_ids = {e['source_id'] for e in c['evidence']}
            source_ids |= {sid for r in c['relations'] for sid in r['source_ids']}
            provenance = candidate['batch']['concept_provenance'][c['id']]
            entries.append(dict(id=c['id'], stratum=stratum, card=copy.deepcopy(c),
                sources=[refs[sid] for sid in sorted(source_ids)], risk_score=risk(c),
                selection_rationale='Uniform sample without replacement from sorted full draft IDs.'
                    if stratum == 'random' else reasons[c['id']],
                author_assignment=provenance[0]['batch_id'].rsplit('-', 1)[1]))
    result = dict(schema_version=1, batch_id=candidate['batch']['id'], seed=seed,
        draft_candidate_sha256=sha(candidate_path), population_count=len(cards),
        population_ids=[c['id'] for c in cards], random_count=20, risk_count=20,
        risk_is_random=False, sample=entries,
        domains=dict(Counter(e['card']['domains'][0] for e in entries)),
        scopes=dict(Counter(e['card']['scope'] for e in entries)),
        limitation='Fixed sample checks support and clarity; it does not certify unsampled cards or measure human interest.')
    STOCK.atomic_json(batch_dir/'audit-sample.json', result)
    STOCK.atomic_json(destination/'manifest.json', dict(schema_version=1, files=files,
        draft_candidate_sha256=sha(candidate_path), audit_sample_sha256=sha(batch_dir/'audit-sample.json')))
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--batch-dir', type=Path, required=True)
    p.add_argument('--candidate', type=Path, required=True)
    p.add_argument('--seed', required=True)
    args = p.parse_args()
    result = freeze(args.batch_dir, args.candidate, args.seed)
    print(json.dumps({k: result[k] for k in ('batch_id', 'population_count', 'random_count', 'risk_count', 'domains', 'scopes')}, indent=2))
