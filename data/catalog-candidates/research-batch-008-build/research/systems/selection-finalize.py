"""Finalize already inspected systems meanings. Local files only; no card drafting."""
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BUILD = ROOT.parents[1]
PATH = ROOT / 'proposals.json'
baseline_bytes = (BUILD / 'baseline-index.json').read_bytes()
baseline = json.loads(baseline_bytes)
plan = json.loads((BUILD / 'coverage-plan.json').read_text())['assignments']['systems']
doc = json.loads(PATH.read_text())
rows = {p['id']: p for p in doc['proposals']}
now = datetime.now(timezone.utc).isoformat()
normalize = lambda s: re.sub(r'[\s_\-\u2010-\u2015]+', ' ', s.strip().casefold()).strip()

assert len(rows) == len(doc['proposals']) == 61
assert all(p.get('selection_role') == 'primary' for p in doc['proposals'])
assert hashlib.sha256(baseline_bytes).hexdigest() == doc['baseline_index_sha256']

# The accepted meanings and stable IDs stay fixed; these are evidence and wording repairs.
r = rows['local:catalog:http-structured-field-dictionary']
old = r['discovery_evidence'][0]
new_rfc = dict(url='https://www.rfc-editor.org/rfc/rfc9651.html',
    locator='3 Structured Data Types, lines 252-259; 3.2 Dictionaries, lines 330-336; 2.4 compatibility, lines 243-246',
    note='The current Structured Fields specification defines unique-key dictionaries with Items or Inner Lists; RFC 8941 remains historical evidence.',
    inspection_mode='web.run actual official HTML passage')
r['discovery_evidence'] = [new_rfc] + [e for e in r['discovery_evidence'] if e['url'] != new_rfc['url']]
r['proposed_parent'].update(url=new_rfc['url'], locator=new_rfc['locator'],
    note='The specification explicitly defines Dictionaries as a top-level representation for HTTP fields.')
r['limits'] = ['Use RFC 9651 for the current specification; older field definitions can still reference RFC 8941.']

rows['Q65123731']['proposed_parent'].update(type='broader_topic',
    note='The lecture places this solution algorithm within the stable matching problem. Solving a problem does not mean applying that problem.')
rows['Q65123731']['limits'] = ['Stability is under the lecture’s strict preference and matching model; proposers’ optimality is not universal welfare optimality.']
rows['local:catalog:oblivious-http']['proposed_parent'].update(type='facet_of',
    note='RFC 9458 defines an encrypted relaying mechanism for HTTP requests and responses, a distinct protocol facet.')
rows['local:catalog:ephemeron']['proposed_parent']['note'] = 'Editorial learning parent: Racket’s garbage-collection reachability construct belongs within computer science.'
rows['local:catalog:qpack-field-compression']['proposed_parent']['note'] = 'RFC 9204 defines QPACK for HTTP/3 field compression, a specific mechanism within HTTP.'
rows['local:catalog:rural-hospitals-theorem']['limits'] = [
    'Fixed hospital quotas, strict preferences and responsive hospital rankings are required in the inspected formulation; do not transfer the result to arbitrary matching preferences.'
]
rows['local:catalog:rural-hospitals-theorem']['proposed_parent']['note'] = 'Section 4 states an invariance theorem about stable hospital-doctor matchings within the stable matching problem.'
rows['local:catalog:moral-hazard-in-teams']['identity_reason'] = 'The source defines a distinct multiagent model with hidden individual actions, shared output and budget-balance constraints, extending the moral-hazard problem.'
rows['local:catalog:moral-hazard-in-teams']['nearest_baseline_matches'][0]['reason'] = rows['local:catalog:moral-hazard-in-teams']['identity_reason']
rows['local:catalog:relative-performance-evaluation']['learning_takeaway'] = 'Peers’ outcomes can supply information useful for designing an individual’s incentive contract.'
rows['local:catalog:relative-performance-evaluation']['discovery_evidence'][0]['note'] = rows['local:catalog:relative-performance-evaluation']['learning_takeaway']
rows['local:catalog:event-segmentation-theory']['limits'] = ['This is a proposed theory; its particular neural implementation is a hypothesis, rather than a settled identity definition.']
rows['local:catalog:event-segmentation-theory']['proposed_parent']['note'] = 'The authors explicitly frame the theory as an account of perceptual boundaries in continuous activity.'

# The HTML author copy provides an explicit name and timing boundary for unraveling.
r = rows['local:catalog:market-unraveling']
r['label'] = 'Unraveling in matching markets'
r['aliases'] = ['Market unraveling', 'Matching-market unraveling', 'Early contracting in matching markets']
unravel = dict(url='https://stanford.edu/~alroth/jump.html',
    locator='Introduction, lines 87-91 and 146-164; I. Unraveling in a prototypical market, lines 177-197',
    note='Roth and Xing explicitly name appointment-date unraveling: participants transact earlier than competitors, with future qualifications still uncertain.',
    inspection_mode='web.run actual author-hosted HTML passage')
r['discovery_evidence'] = [unravel] + [e for e in r['discovery_evidence'] if e['url'] != unravel['url']]
r['identity_reason'] = 'This subject concerns earlier appointment dates in matching markets. It differs from stable-matching algorithms and adverse-selection explanations of market collapse.'
for near in r['nearest_baseline_matches']:
    near['reason'] = r['identity_reason']
if not any(n['id'] == 'local:catalog:adverse-selection' for n in r['nearest_baseline_matches']):
    r['nearest_baseline_matches'].append(dict(id='local:catalog:adverse-selection',
        label=baseline['concepts']['local:catalog:adverse-selection']['label'],
        reason='The existing insurance-selection meaning concerns changing risk composition; this proposed identity concerns transaction timing.'))
r['proposed_parent'].update(url=unravel['url'], locator=unravel['locator'],
    note='Editorial bridge to stable matching: the authors distinguish appointment-date instability from blocking-pair instability and discuss centralized match procedures.')
r['limits'] = ['The inspected author copy describes historical markets and an idealized four-stage pattern; it does not claim every matching market unravels.',
    'Unraveling here means progressively earlier appointments, rather than adverse-selection market collapse.']

# Printed page numbers are distinct from one-based PDF page numbers.
fivb = 'https://www.fivb.com/wp-content/uploads/2025/01/FIVB-Volleyball_Rules2025_2028-EN.pdf'
for identifier, locator in [
    ('local:catalog:libero-volleyball', '19.3.1, printed p. 42 / PDF p. 44; 19.3.2.1-2, printed p. 43 / PDF p. 45'),
    ('local:catalog:volleyball-rotational-fault', '7.7 Rotational Fault, printed p. 26 / PDF p. 28')]:
    r = rows[identifier]
    for evidence in r['discovery_evidence']:
        if evidence['url'] == fivb:
            evidence.update(locator=locator, inspection_mode='Official PDF extracted locally with pypdf and passage read; earlier web extraction also inspected')
    r['proposed_parent']['locator'] = locator
rows['local:catalog:libero-volleyball']['limits'] = ['Apply FIVB 2025-2028 rules; serving permissions differ in some other volleyball rule sets.']
rows['local:catalog:libero-volleyball']['proposed_parent']['note'] = 'FIVB Rule 19 defines the Libero’s role, playing actions and replacements within volleyball.'

r = rows['local:catalog:duckworth-lewis-stern-method']
r['learning_takeaway'] = 'DLS revises targets when a limited-overs cricket match is interrupted; the historical Standard Edition models overs and wickets as scoring resources.'
r['discovery_evidence'][0]['note'] = 'ICC explicitly names its adopted method for revising targets in interrupted limited-overs matches.'

r = rows['local:catalog:desirable-difficulties']
if not any(n['id'] == 'Q57660658' for n in r['nearest_baseline_matches']):
    r['nearest_baseline_matches'].append(dict(id='Q57660658', label=baseline['concepts']['Q57660658']['label'],
        reason='Sans forgetica is a particular typeface whose imported description invokes desirable difficulty. It is distinct from the general learning principle, and its efficacy is not assumed here.'))

# Preserve import and prior-bundle decisions for each canonical existing control.
for r in doc['proposals']:
    r['alias_checks'] = [dict(query=q, normalized_key=normalize(q), matched_ids=baseline['aliases'].get(normalize(q), [])) for q in [r['label'], *r['aliases']]]
    if r['inventory_status'] == 'existing':
        b = baseline['concepts'][r['id']]
        version = max([b.get('latest_card_version', 0)] + [c.get('record', {}).get('card_version', 0) for c in b.get('candidate_records', [])])
        r['control_record_metadata'] = dict(original_description=b.get('original_description'),
            maximum_prior_card_version=version, next_card_version=version + 1,
            baseline_record_pointer=f"data/catalog-candidates/research-batch-008-build/baseline-index.json#/concepts/{r['id']}",
            imported_provenance=b.get('inventory_records', []),
            prior_bundles=[{k: c.get(k) for k in ['batch_id', 'batch_revision', 'source_bundle_path', 'source_bundle_sha256']} for c in b.get('candidate_records', [])])

# Replace provisional source titles; revisions are explicit where actually known.
source_updates = {
    'systems-source-001': ('The Racket Reference, 16.2 Ephemerons', None),
    'systems-source-002': ('Maged M. Michael, Hazard pointers: Safe memory reclamation for lock-free objects', '2004 primary-paper abstract on IBM Research'),
    'systems-source-003': ('crossbeam_epoch crate documentation', '0.9.21 inspected crate documentation'),
    'systems-source-004': ('RFC 9204: QPACK: Field Compression for HTTP/3', 'RFC 9204'),
    'systems-source-005': ('RFC 8941: Structured Field Values for HTTP', 'RFC 8941; obsoleted by RFC 9651'),
    'systems-source-006': ('RFC 9421: HTTP Message Signatures', 'RFC 9421'),
    'systems-source-007': ('RFC 9458: Oblivious HTTP', 'RFC 9458'),
    'systems-source-008': ('RFC 9162: Certificate Transparency Version 2.0', 'RFC 9162'),
    'systems-source-009': ('Dan Quint, Econ 690 Lecture 14: Matching', None),
    'systems-source-010': ('FAA: Runway Incursions', 'Page last updated 2026-08-31'),
    'systems-source-011': ('FHWA Traffic Signal Timing Manual, Chapter 3: Basic Signal Timing', 'FHWA-HOP-08-024, 2008'),
    'systems-source-012': ('R&A Rules of Golf, Rule 21: Other Forms of Individual Stroke Play and Match Play', None),
    'systems-source-013': ('FIVB Official Volleyball Rules 2025-2028', '2025-2028 edition'),
    'systems-source-014': ('Zacks, Speer, Swallow, Braver and Reynolds, Event Perception: A Mind/Brain Perspective', 'Psychological Bulletin 133(2), March 2007, pp. 273-293; hosted author manuscript'),
    'systems-source-017': ('MIT 6.896 Spring 2010, Lecture 21', 'Spring 2010'),
    'systems-source-034': ('Manu Kapur, Productive Failure: A Hidden Efficacy of Seemingly Unproductive Production', 'Proceedings of the 28th Annual Conference of the Cognitive Science Society, 2006, pp. 1587-1592'),
}
for s in doc['sources_inspected']:
    if s['id'] in source_updates:
        s['title'], s['revision'] = source_updates[s['id']]
    if s['url'] == fivb:
        s['inspection_mode'] = 'Official PDF passages extracted locally with pypdf and read; earlier web extraction also inspected'

def add_source(title, url, revision, mode):
    found = next((s for s in doc['sources_inspected'] if s['url'] == url), None)
    if not found:
        found = dict(id=f"systems-source-{len(doc['sources_inspected']) + 1:03}", title=title,
            url=url, locator='', revision=revision, acquired_at=now,
            acquisition_mode='Local timestamp after reading; exact remote retrieval time unavailable', inspection_mode=mode)
        doc['sources_inspected'].append(found)
    return found

add_source('RFC 9651: Structured Field Values for HTTP', new_rfc['url'], 'RFC 9651, September 2024', new_rfc['inspection_mode'])
add_source('ICC: Duckworth-Lewis-Stern method; Standard Edition fallback methodology',
    'https://images.icc-cricket.com/image/upload/prd/orlbya4cqyhqaceje3b2.pdf', None, 'web.run actual official PDF passage')
add_source('Roth and Xing, Jumping the Gun: Imperfections and Institutions Related to the Timing of Market Transactions',
    unravel['url'], 'AER 84, September 1994, pp. 992-1044; author HTML copy says revised August 1993 and contains the descriptive portion', unravel['inspection_mode'])

# Each source's locators are the union of the passages actually attached to selected meanings.
for s in doc['sources_inspected']:
    locators = []
    for r in doc['proposals']:
        for e in r['discovery_evidence']:
            if e['url'] == s['url'] and e['locator'] not in locators:
                locators.append(e['locator'])
    assert locators, s['id']
    s['locator'] = '; '.join(locators)
    if s['inspection_mode'] == 'web.run actual extracted HTML/PDF passage':
        s['inspection_mode'] = 'web.run actual extracted PDF passage' if '.pdf' in s['url'] else 'web.run actual extracted HTML passage'

domains = Counter(p['primary_domain'] for p in doc['proposals'])
scopes = Counter(p['scope'] for p in doc['proposals'])
inventory = Counter(p['inventory_status'] for p in doc['proposals'])
kinds = Counter(p['entity_kind'] for p in doc['proposals'])
fine = [p for p in doc['proposals'] if p['scope'] in ['idea', 'facet_or_application']]
parented = [p for p in fine if p['proposed_parent']]
asserted = [p for p in parented if p['proposed_parent']['assertion'] == 'source_asserted']
doc['status'] = 'selection_complete_awaiting_reservations'
doc['issues'] = [
    dict(type='measured_named_subject_shortfall', status='reported',
        note='This mechanism-focused shard has 1 named subject, the existing Go board game, and 0 new named subjects. Eponymous algorithms, theories and scoring methods remain ideas; the global named-subject goal is a soft measured goal.'),
    dict(type='bounded_source_access', status='resolved_with_inspected_alternatives',
        note='Some preferred NACTO, Pressbooks, eLife/PMC and Nobel pages returned access errors or client challenges. Inspected FTA, Haskins/author papers, PLOS and Roth-Xing author HTML provide the selected support. Search snippets and the saved stop-signal client-challenge page are excluded as explanatory evidence.'),
    dict(type='selection_evidence_depth', status='bounded_for_reservation',
        note='Hazard pointers and friendship paradox use inspected primary abstracts; relative performance evaluation uses the inspected primary abstract. Detailed mechanisms will need additional passage inspection before drafting claims beyond these selection takeaways. Historical D-L Standard Edition mechanics are distinguished from current professional DLS calculation.')
]
doc['checkpoint_counts'] = dict(total=61, primary_domains=dict(domains))
doc['final_selection_counts'] = dict(primary=61, alternatives=0, inventory_status=dict(inventory),
    scopes=dict(scopes), entity_kinds=dict(kinds), new_fine_scope=sum(p['inventory_status']=='proposed_new' for p in fine),
    fine_scope=len(fine), fine_with_parent=len(parented), fine_with_source_asserted_parent=len(asserted),
    distinct_inspected_source_urls=len(doc['sources_inspected']))
PATH.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + '\n')
(ROOT / 'source-records.json').write_text(json.dumps(doc['sources_inspected'], indent=2, ensure_ascii=False) + '\n')
proposal_hash = hashlib.sha256(PATH.read_bytes()).hexdigest()

# Structural and inventory checks; these do not certify every eventual card claim.
required = ['id','label','aliases','primary_domain','primary_subfield','entity_kind','scope',
    'learning_takeaway','inventory_status','nearest_baseline_matches','identity_reason','discovery_evidence','proposed_parent','limits']
source_by_url = {s['url']: s for s in doc['sources_inspected']}
assert dict(domains) == plan['primary_domains']
assert inventory == Counter(proposed_new=55, existing=6)
assert set(scopes) == {'broad_field','topic','idea','facet_or_application'}
assert any(p['scope']=='broad_field' and p['inventory_status']=='existing' for p in doc['proposals'])
for r in doc['proposals']:
    assert all(k in r for k in required), r['id']
    assert r['entity_kind'] in ['idea','named_subject']
    assert r['discovery_evidence'] and r['nearest_baseline_matches'] and r['learning_takeaway']
    assert all(n['id'] in baseline['concepts'] for n in r['nearest_baseline_matches'])
    assert (r['id'] in baseline['concepts']) == (r['inventory_status']=='existing')
    for e in r['discovery_evidence']:
        assert e['url'] in source_by_url and e['locator'] and e['inspection_mode']
    if r['inventory_status'] == 'proposed_new':
        assert not any(c['matched_ids'] for c in r['alias_checks']), (r['id'],r['alias_checks'])
    if r['proposed_parent']:
        p = r['proposed_parent']
        assert p['target_id'] in baseline['concepts'] or p['target_id'] in rows
        assert p['type'] in ['broader_topic','facet_of','application_of']
        assert p['assertion'] in ['source_asserted','editorial']
        assert p['url'] in source_by_url and p['locator'] and p['note']
for s in doc['sources_inspected']:
    assert all(k in s for k in ['id','title','url','locator','revision','acquired_at','acquisition_mode','inspection_mode'])
    datetime.fromisoformat(s['acquired_at'])
assert len(source_by_url) == len(doc['sources_inspected'])
assert not (ROOT/'candidate.json').exists()
validation = dict(schema_version=1, assignment='systems', checked_at=now,
    baseline_index_sha256=doc['baseline_index_sha256'], proposals_sha256=proposal_hash,
    status=doc['status'], checks=dict(required_fields=True, unique_ids=True, exact_domain_counts=True,
        new_control_counts=True, all_four_scopes=True, existing_broad_control=True,
        normalized_new_alias_collisions=0, nearest_baseline_ids_resolve=True,
        parent_targets_resolve=True, evidence_source_metadata_complete=True, iso_acquisition_metadata=True,
        card_drafting_started=False), counts=doc['final_selection_counts'],
    remaining_gate='Coordinator approved reservations and global selection manifest hash are required before card drafting.')
(ROOT/'selection-validation.json').write_text(json.dumps(validation, indent=2, ensure_ascii=False)+'\n')
(ROOT/'identity-checks.json').write_text(json.dumps(dict(schema_version=1,
    baseline_index_sha256=doc['baseline_index_sha256'], normalizer='casefold; trim; collapse whitespace, underscores, hyphens and U+2010-U+2015 to a single space',
    proposals_sha256=proposal_hash,
    note='Exact checks accompany focused local searches of labels, aliases, imported descriptions and prior cards. A no-alias-match result alone was never treated as proof of a new meaning.',
    subjects=[dict(id=r['id'], alias_checks=r['alias_checks'], nearest_baseline_matches=r['nearest_baseline_matches'],
        identity_reason=r['identity_reason']) for r in doc['proposals']]), indent=2, ensure_ascii=False)+'\n')

def safe(s):
    return str(s).replace('|', '\\|').replace('\n', ' ')

review = [
    '# Systems selection review — batch 008', '',
    'Status: **selection_complete_awaiting_reservations**. This shard contains 61 primary proposals: 55 new identities and 6 canonical existing controls. No alternatives or discovery cards were added. Public passages and the frozen inventory informed selection; private preference ratings were not used.', '',
    f'Frozen baseline: 35,743 active IDs after reviewed redirects; SHA-256 `{doc["baseline_index_sha256"]}`. Final proposals SHA-256: `{proposal_hash}`.', '',
    '| Primary domain | Selected | New | Existing controls |', '| --- | ---: | ---: | ---: |',
]
for domain in plan['primary_domains']:
    group = [r for r in doc['proposals'] if r['primary_domain']==domain]
    review.append(f'| {domain} | {len(group)} | {sum(r["inventory_status"]=="proposed_new" for r in group)} | {sum(r["inventory_status"]=="existing" for r in group)} |')
review += ['',
    f'All four scopes occur: {scopes["broad_field"]} broad fields, {scopes["topic"]} topic, {scopes["idea"]} ideas and {scopes["facet_or_application"]} facets/applications. All 55 new proposals have fine scope. Supported parents occur on {len(parented)}/{len(fine)} fine-scope proposals; {len(asserted)}/{len(fine)} are source asserted. These are selection relationships, subject to the later card and source audit.', '',
    'The named-subject count is 1 existing subject (Go) and 0 new subjects. Theorems, algorithms, scoring systems and psychological theories retain `entity_kind=idea`. The global named-subject goal remains a documented soft goal.', '',
    '## Identity and relationship decisions', '',
    '- Gale–Shapley/deferred acceptance reuses **Q65123731**, whose imported description is “algorithm for solving the stable matching problem.” The [matching lecture, section 2.2](https://users.ssc.wisc.edu/~dquint/econ690/lecture%2014.pdf) describes that same procedure; its parent is the stable matching problem, rather than an application of the problem.',
    '- Go reuses board-game **Q11413**. The shared alias “Go” also matches programming-language **Q37227**; the [British Go Association rules passage](https://britgo.org/intro/intro2.html) fixes the selected game sense.',
    '- The team moral-hazard proposal is `facet_of` the existing moral-hazard identity because the [Holmström primary introduction](https://people.duke.edu/~qc2/BA532/1982%20Rand%20Holmstrom%20team.pdf) identifies a multiagent extension with shared output. It does not apply moral hazard as a method.',
    '- Matching-market unraveling concerns appointment timing, while existing adverse selection concerns risk composition. The [Roth–Xing author copy, Introduction and section I](https://stanford.edu/~alroth/jump.html) explicitly describes the timing phenomenon and distinguishes it from static matching instability.',
    '- Desirable difficulties is the general learning principle. Existing **Q57660658 Sans forgetica** is a particular typeface whose imported wording invokes that principle. [Bjork’s manuscript](https://bjorklab.psych.ucla.edu/wp-content/uploads/sites/13/2016/07/RBjork_inpress.pdf) supports the principle without assuming the typeface’s efficacy.',
    '- Structured-field dictionaries use [RFC 9651, section 3.2](https://www.rfc-editor.org/rfc/rfc9651.html#section-3.2), with RFC 8941 retained as historical evidence. [RFC 9458](https://www.rfc-editor.org/rfc/rfc9458.html) supports Oblivious HTTP as a protocol facet. Mechanisms retain idea kind.', '',
    'Exact label/alias checks use the runtime normalizer. Nearby meanings were also searched in imported descriptions and prior cards. Every new proposal has zero exact normalized baseline alias collisions; the meaning decisions below supply the boundaries that exact strings alone cannot establish. Detailed checks are preserved in `identity-checks.json` and each proposal.', '',
    '## Canonical existing controls', '',
    '| ID | Selected meaning | Maximum prior card version | Version after reservation |', '| --- | --- | ---: | ---: |',
]
for r in doc['proposals']:
    if r['inventory_status']=='existing':
        m=r['control_record_metadata']
        review.append(f'| `{r["id"]}` | {r["label"]} | {m["maximum_prior_card_version"]} | {m["next_card_version"]} |')
review += ['', 'Imported wording, inventory provenance, prior bundle hashes and baseline record pointers are retained in `control_record_metadata`. Imported controls with no known prior discovery card start their researched card at version 1; an existing identity is still an existing control.', '',
    '## Selection ledger', '',
    'Each linked source was actually inspected. The table gives the distinct meaning boundary; the JSON preserves the learning takeaway, exact locator, nearest inventory identities, assertion type and limits.', '',
    '| ID and selected meaning | Inventory | Boundary | Inspected support |', '| --- | --- | --- | --- |',
]
for domain in plan['primary_domains']:
    for r in doc['proposals']:
        if r['primary_domain'] != domain:
            continue
        e=r['discovery_evidence'][0]
        src=source_by_url[e['url']]
        review.append(f'| `{r["id"]}` — {safe(r["label"])} | {r["inventory_status"]} | {safe(r["identity_reason"])} | [{src["id"]}]({e["url"]}); {safe(e["locator"])} |')
review += ['', '## Source depth and limits', '',
    'The source inventory contains 50 distinct inspected URLs, with titles, passage locators, available revisions and ISO local timestamps after reading. Exact remote retrieval times are unavailable and are explicitly distinguished from those local timestamps. The scanned Holmström and Holmström–Milgrom pages were rendered and visually inspected; FAA and FIVB passages were also read from local official PDFs.', '',
    'Hazard pointers and friendship paradox are supported at selection depth by inspected primary abstracts. The relative-performance evaluation takeaway is bounded to the information role named in the Holmström abstract. Later drafting must inspect additional passages before adding mechanisms or assumptions beyond those takeaways.', '',
    'The [ICC DLS page](https://www.icc-cricket.com/about/cricket/rules-and-regulations/duckworth-lewis-stern?appview=true) establishes the adopted target-adjustment subject. Its [linked methodology, opening and section 1](https://images.icc-cricket.com/image/upload/prd/orlbya4cqyhqaceje3b2.pdf) distinguishes the Stern calculator from the historical D-L Standard Edition fallback. The fallback tables are not treated as the current professional DLS formula.', '',
    'Historical and model boundaries remain visible: the Boston mechanism is the 2003-described system; matching invariance requires its stated preference assumptions; Schelling segregation and complex contagion are stylized models; psychological task findings do not give universal individual rates; the Libero permissions are FIVB 2025–2028. Productive Failure source metadata uses the 2006 conference paper, not 2007.', '',
    'Preferred pages that returned access errors or client challenges were replaced with inspected primary or official material. Failed Nobel pages, blocked eLife/PMC pages and the saved stop-signal challenge HTML are not explanatory sources. No selected meaning relies only on a search snippet.', '',
    '## Reservation gate', '',
    'Selection is complete. Card writing remains stopped until the coordinator sends approved reservations and the frozen global selection manifest hash. Future candidate metadata must retain both `global_selection_manifest_sha256` and `baseline_index_sha256`. There is no `candidate.json` in this shard.', '',
]
(ROOT/'selection-review.md').write_text('\n'.join(review))
print(json.dumps(dict(status=doc['status'], proposals_sha256=proposal_hash, counts=doc['final_selection_counts'], validation='passed'), ensure_ascii=False))
