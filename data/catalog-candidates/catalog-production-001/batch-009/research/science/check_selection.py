import collections
import hashlib
import json
import pathlib
import re
import unicodedata

ROOT = pathlib.Path('data/catalog-candidates/catalog-production-001')
OUT = ROOT / 'batch-009/research/science'
base = json.loads((ROOT / 'baseline-index.json').read_text())['concepts']
eligible = {c['id']: c for c in json.loads((OUT / 'eligible-identities.json').read_text())['concepts']}
obj = json.loads((OUT / 'proposals.json').read_text())
proposals = obj['proposals']
sources = {s['id']: s for s in obj['sources_inspected']}
normalize = lambda s: re.sub(r'[^a-z0-9]', '', unicodedata.normalize('NFKD', s).casefold())
prior_names = collections.defaultdict(set)
for cid, c in base.items():
    if not c.get('candidate_records'):
        continue
    names = [c['label']] + c['aliases']
    for r in c['candidate_records']:
        names += [r['record']['label']] + r['record'].get('aliases', [])
    for name in names:
        prior_names[normalize(name)].add(cid)
seen = {}
for p in proposals:
    cid = p['id']
    assert cid in eligible and cid in base
    assert p['label'] == eligible[cid]['label'] == base[cid]['label']
    assert p['aliases'] == eligible[cid]['aliases']
    assert not base[cid].get('candidate_records')
    assert p['scope'] in ['broad_field', 'topic', 'idea', 'facet_or_application']
    assert p['entity_kind'] in ['idea', 'named_subject']
    for name in [p['label']] + p['aliases']:
        norm = normalize(name)
        assert not prior_names.get(norm), (cid, name, prior_names.get(norm))
        assert norm not in seen or seen[norm] == cid
        seen[norm] = cid
    assert p['discovery_evidence']
    for e in p['discovery_evidence']:
        assert e['source_id'] in sources and e['locator'] and e['tool_refs']
        assert e['url'] == sources[e['source_id']]['url']
    r = p['proposed_parent']
    if r:
        assert r['target_id'] in base and r['target_id'] != cid
        assert r['assertion'] in ['source_asserted', 'editorial']
        assert r['type'] in ['broader_topic', 'facet_of', 'application_of', 'related_to']
        assert r['source_ids'] and all(s in sources for s in r['source_ids'])
assert len(proposals) == len({p['id'] for p in proposals}) == 70
excluded = ['Q3001783', 'Q624580', 'Q175751']
assert not set(excluded).intersection(p['id'] for p in proposals)
expected = {**dict.fromkeys(['Biology & nature', 'Chemistry & materials', 'Earth & environment', 'Food & agriculture', 'Health & medicine', 'Home & crafts'], 9), 'Mathematics': 8, 'Physics & astronomy': 8}
domains = collections.Counter(p['primary_domain'] for p in proposals)
assert domains == expected
budgets = json.loads((OUT / 'source-word-budgets.json').read_text())['budgets']
assert len(budgets) == len(sources)
assert all(b['total_derived_words'] <= b['word_limit'] for b in budgets)
fine = [p for p in proposals if p['scope'] in ['idea', 'facet_or_application']]
parents = [p for p in fine if p['proposed_parent'] and p['proposed_parent']['type'] in ['broader_topic', 'facet_of', 'application_of']]
checks = dict(schema_version=1, stage='selection_ready_awaiting_reservations', proposal_count=len(proposals), domain_counts=dict(domains), scope_counts=dict(collections.Counter(p['scope'] for p in proposals)), strict_named_subjects=[dict(id=p['id'], label=p['label']) for p in proposals if p['entity_kind']=='named_subject'], proposed_relations=sum(bool(p['proposed_parent']) for p in proposals), without_proposed_relation=[p['id'] for p in proposals if not p['proposed_parent']], fine_scope_count=len(fine), fine_scope_with_parent_or_application=len(parents), fine_scope_source_asserted_parent_or_application=sum(p['proposed_parent']['assertion']=='source_asserted' for p in parents), fine_scope_parent_coverage=len(parents)/len(fine), fine_scope_parent_assertion_share=sum(p['proposed_parent']['assertion']=='source_asserted' for p in parents)/len(parents), fine_scope_parent_gaps=[p['id'] for p in fine if p not in parents], eligible_id_check='passed', existing_card_and_normalized_alias_check='passed_with_semantic_exclusions', semantic_excluded_ids=excluded, broader_identity_boundary_review_ids=['Q215915','Q172858'], within_selection_alias_check='passed', relation_target_check='passed', sources_count=len(sources), source_passage_locator_check='passed', source_budget_check='passed', max_source_derived_words=max(b['total_derived_words'] for b in budgets), baseline_index_sha256=hashlib.sha256((ROOT/'baseline-index.json').read_bytes()).hexdigest(), proposals_sha256=hashlib.sha256((OUT/'proposals.json').read_bytes()).hexdigest(), card_bodies_written=0, limitations=['Normalized name matching is not exhaustive semantic deduplication; coordinator reservation review remains required.','Three same-subject QIDs were excluded without merging identities or editing prior cards.','Relations are proposals only and require later author checks against actual short cards.','Source budgets conservatively cover selection takeaways, support notes, relation notes and limits; add actual bodies before final checking.','Inspection times are local UTC checkpoints after actual reads, not server acquisition timestamps.','No independent acceptance review has occurred.'])
(OUT/'selection-checks.json').write_text(json.dumps(checks, ensure_ascii=False, indent=2)+'\n')
print(json.dumps({k:checks[k] for k in ['proposal_count','proposals_sha256','fine_scope_with_parent_or_application','fine_scope_source_asserted_parent_or_application','source_budget_check','max_source_derived_words']}))
