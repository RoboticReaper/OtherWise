"""Account for authored prose and serialize the completed manual author checks.

No retrieval or AI API calls. Historical proposal literals are counted as well
as the frozen selection and final cards; byte-identical artifact copies are
deduplicated only within the same concept and prose role.
"""
import ast
import collections
import hashlib
import json
import pathlib

ROOT = pathlib.Path('data/catalog-candidates/catalog-production-001')
OUT = ROOT / 'batch-009/research/science'
STAMP = '2026-10-09T04:59:20Z'


def read(name):
    return json.loads((OUT / name).read_text())


def write(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


candidate = read('candidate.json')
selection = read('proposals.json')
inspection = read('sources-inspected.json')
sources = {s['id']: s for s in inspection['sources']}
texts = collections.defaultdict(dict)


def add(sid, cid, role, text):
    if text:
        assert sid in sources, sid
        texts[sid][(cid, role, text)] = text


# Retain the source cost of superseded/rejected selection prose still present
# in the generator. Never execute that generator or mutate frozen selections.
tree = ast.parse((OUT / 'build_selection.py').read_text())
for call in ast.walk(tree):
    if not (isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
            and call.func.id == 'proposal'):
        continue
    args = [ast.literal_eval(a) for a in call.args]
    kwargs = {k.arg: ast.literal_eval(k.value) for k in call.keywords}
    cid, takeaway, sid, note = args[0], args[3], args[4], args[6]
    add(sid, cid, 'learning_takeaway', takeaway)
    add(sid, cid, 'support_note', note)
    parent = args[7] if len(args) > 7 else kwargs.get('parent')
    limits = args[8] if len(args) > 8 else kwargs.get('limits', [])
    if parent:
        add(sid, cid, 'relation_note', parent[3])
    for limit in limits or []:
        add(sid, cid, 'limit', limit)

for p in selection['proposals']:
    sids = {e['source_id'] for e in p['discovery_evidence']}
    if p['proposed_parent']:
        sids.update(p['proposed_parent']['source_ids'])
    for sid in sids:
        add(sid, p['id'], 'learning_takeaway', p['learning_takeaway'])
        for limit in p['limits']:
            add(sid, p['id'], 'limit', limit)
    for e in p['discovery_evidence']:
        add(e['source_id'], p['id'], 'support_note', e['support_note'])
    if p['proposed_parent']:
        for sid in p['proposed_parent']['source_ids']:
            add(sid, p['id'], 'relation_note', p['proposed_parent']['note'])

for c in candidate['concepts']:
    sids = {e['source_id'] for e in c['evidence']}
    sids.update(sid for r in c['relations'] for sid in r['source_ids'])
    for sid in sids:
        # Conservatively charge the full body and takeaway even to a page
        # inspected principally for the relationship.
        add(sid, c['id'], 'card_body', c['card'])
        add(sid, c['id'], 'learning_takeaway', c['learning_takeaway'])
    for e in c['evidence']:
        add(e['source_id'], c['id'], 'support_note', e['note'])
    for r in c['relations']:
        for sid in r['source_ids']:
            add(sid, c['id'], 'relation_note', r['note'])

for issue in selection['issues']:
    for sid in issue.get('source_ids', []):
        add(sid, issue.get('id', '(selection alternative)'), 'issue_outcome',
            issue.get('outcome', '').replace('_', ' '))

basis = (
    'Final shard accounting: whitespace-separated unique selection takeaways, '
    'support notes, relationship notes, limits, linked alternative/boundary '
    'outcomes and card bodies. Includes original proposal literals for '
    'superseded or excluded selections. Full body/takeaway charged '
    'conservatively to every attached claim or relationship source. Exact '
    'copies of a concept/role/text across companion artifacts count once; '
    'body and takeaway remain distinct roles. Titles, inventory names, '
    'locators, URLs and administrative metadata excluded. Research and '
    'review notes contain metadata only; no quotations. Excluded IDs in '
    'card_ids account for retained historical selection prose, not cards.'
)
budgets = []
for sid, s in sources.items():
    rows = texts[sid]
    total = sum(len(t.split()) for t in rows.values())
    assert total <= s['word_limit'], (sid, total)
    budgets.append(dict(source_id=sid, url=s['url'], word_limit=s['word_limit'],
                        total_derived_words=total,
                        card_ids=sorted({key[0] for key in rows if not key[0].startswith('(')}),
                        counting_basis=basis))
groups = collections.defaultdict(list)
for b in budgets:
    groups[sources[b['source_id']].get('budget_group', b['url'])].append(b)
for url, rows in groups.items():
    assert sum(b['total_derived_words'] for b in rows) <= min(b['word_limit'] for b in rows), url
write('source-word-budgets.json', dict(schema_version=1, budgets=budgets))

# These booleans record the author's manual passage/meaning/clarity/relation
# checks, not a conclusion inferred by the structural validation script.
reviews = {}
for c in candidate['concepts']:
    locators = []
    for e in c['evidence']:
        s = sources[e['source_id']]
        locators.append(dict(source_id=s['id'], url=s['url'], locator=e['locator'],
                             inspection_mode=s['inspection_mode'], tool_refs=s['tool_refs'],
                             purpose='card_claims_and_meaning'))
    for r in c['relations']:
        for sid in r['source_ids']:
            s = sources[sid]
            locators.append(dict(source_id=sid, url=s['url'], locator=s['locator'],
                                 additional_inspections=s.get('additional_inspections', []),
                                 inspection_mode=s['inspection_mode'], tool_refs=s['tool_refs'],
                                 purpose='attached_relation', target_id=r['target_id'],
                                 assertion=r['assertion']))
    reviews[c['id']] = dict(outcome='author_checked', card_version=1,
                            word_count=len(c['card'].split()), inspected_locators=locators,
                            claims_supported=True, clarity_checked=True,
                            relations_checked=True, limits=[])
candidate['batch'].update(updated_at=STAMP, status='ready_for_independent_audit',
                          completion_status='author_checked_independent_audit_pending',
                          author_review_path=str(OUT / 'author-review.json'),
                          research_notes_path=str(OUT / 'research-notes.md'))
candidate['validation'].update(status='author_checked_independent_audit_pending',
                               author_review_count=len(reviews),
                               source_word_budgets='all_shard_page_budgets_within_limit',
                               independent_audit='pending')
write('candidate.json', candidate)
write('author-review.json', dict(schema_version=1, batch_id=candidate['batch']['id'],
                                reviewed_at=STAMP, candidate_sha256=sha(OUT / 'candidate.json'),
                                baseline_index_sha256=candidate['batch']['baseline_index_sha256'],
                                global_selection_manifest_sha256=candidate['batch']['global_selection_manifest_sha256'],
                                review_basis='Manual author checks against retained actual passage inspections; independent audit pending.',
                                reviews=reviews))
inspection['status'] = 'draft_ready_for_independent_audit'
write('sources-inspected.json', inspection)
print(json.dumps(dict(concepts=len(candidate['concepts']), author_reviews=len(reviews),
                       source_budget_count=len(budgets),
                       maximum_source_words=max(b['total_derived_words'] for b in budgets),
                       largest_budgets=sorted(((b['source_id'], b['total_derived_words']) for b in budgets),
                                              key=lambda x: x[1], reverse=True)[:6],
                       candidate_sha256=sha(OUT / 'candidate.json'))))
