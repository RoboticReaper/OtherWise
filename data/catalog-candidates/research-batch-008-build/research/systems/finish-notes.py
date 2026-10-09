"""Write cited audit handoff notes from the final local shard; no card edits."""
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if (ROOT / 'repair-001.json').exists():
    raise SystemExit('Historical initial-handoff notes: use the repaired notes and budget evidence.')
read=lambda p:json.loads(Path(p).read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
c=read(ROOT/'candidate.json')
a=read(ROOT/'author-review.json')
b=read(ROOT/'word-budget-review.json')
v=read(ROOT/'draft-validation.json')
sources={s['id']:s for s in c['sources']}
assert len(c['concepts'])==61 and len(a['reviews'])==61
assert a['candidate_sha256']==v['candidate_sha256']==sha(ROOT/'candidate.json')
assert not b['over_limit']
fine=[x for x in c['concepts'] if x['scope'] in ['idea','facet_or_application']]
parented=[x for x in fine if any(r['type'] in ['broader_topic','facet_of','application_of'] for r in x['relations'])]
asserted=[x for x in parented if any(r['assertion']=='source_asserted' for r in x['relations'])]
domains=Counter(x['domains'][0] for x in c['concepts'])
lines=[
    '# Systems card research — batch 008', '',
    '**Draft ready for independent audit.** The shard contains exactly 61 approved cards: 55 new identities and 6 existing controls. Every body is original English and contains 32–45 whitespace-delimited words. All 61 have completed author review; independent source auditing and coordinator acceptance remain pending.', '',
    f'Candidate SHA-256: `{sha(ROOT/"candidate.json")}`.',
    f'Global selection manifest SHA-256: `{c["batch"]["global_selection_manifest_sha256"]}`.',
    f'Baseline index SHA-256: `{c["batch"]["baseline_index_sha256"]}`.', '',
    '## Coverage and graph', '',
    '| Primary domain | Cards |', '| --- | ---: |',
]
for domain,count in sorted(domains.items()):lines.append(f'| {domain} | {count} |')
lines += ['',
    'Scopes: 2 broad fields, 1 topic, 50 ideas and 8 facets/applications. All 55 new identities have fine scope. The sole named subject is the existing Go board game; named algorithms, theorems, scoring methods and theories remain ideas. The global named-subject target has a reported soft shortfall.', '',
    f'Parent relationships occur on {len(parented)}/{len(fine)} fine-scope cards; {len(asserted)}/{len(fine)} have source-asserted parents. There are no missing fine-scope parent links. Computer science, Engineering and Go have no asserted parent in this shard. Editorial links remain identified as editorial.', '',
    'Canonical control IDs, body versions and graph directions follow the frozen approval. Gale–Shapley uses Q65123731. The alias Go retains its explicit board-game/programming-language distinction. Moral hazard in teams is a facet of moral hazard, and problem-solution links use the approved broader-topic semantics.', '',
    '## Source inspection and qualifications', '',
    'The source bundle contains 52 inspected source records; 50 primary URLs supply the current card or relationship prose. One official text companion is recorded with its HTML RFC work. Records include actual titles, available revisions and ISO retrieval fields explicitly qualified as local inspection completion. Exact remote retrieval timestamps are unavailable. Previously inspected scanned team-incentive pages were rendered and read visually; the official FAA and FIVB PDFs were read locally as well.', '',
    'Hazard-pointer mechanism support was extended with [P2530R3, section 2](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2023/p2530r3.pdf). Its 2023 proposal date is explicit; no current C++ adoption or performance claim is made.', '',
    'The Schelling card uses the inspected [1969 primary paper, pp. 488–491](https://www.uu.nl/sites/default/files/c4_schelling1969_models_segregation.pdf). Author review distinguishes its line model from the later grid presentation preserved in selection. The approved identity and racial-segregation parent remain unchanged.', '',
    'Structured dictionaries cite [RFC 9651, section 3.2](https://www.rfc-editor.org/rfc/rfc9651.html#section-3.2). HTTP message-signature review includes the [official RFC text, sections 1.1 and 7.3.3](https://www.rfc-editor.org/rfc/rfc9421.txt); the digital-signature parent refers to its asymmetric form, while the RFC also permits symmetric MACs.', '',
    'The cricket card separates the adopted [ICC DLS subject](https://www.icc-cricket.com/about/cricket/rules-and-regulations/duckworth-lewis-stern?appview=true) from the [Standard Edition fallback description](https://images.icc-cricket.com/image/upload/prd/orlbya4cqyhqaceje3b2.pdf). Matching-market timing uses the inspected [Roth–Xing author copy](https://stanford.edu/~alroth/jump.html). FIVB locators retain printed/PDF distinctions: Libero pp. 42–43 / PDF pp. 44–45; rotational fault p. 26 / PDF p. 28.', '',
    '## Collective source prose budgets', '',
    'The calculation is preserved in `word-budget-review.json`, both by source ID and by URL, with a per-card component breakdown. `candidate.batch.source_summary_budgets` carries the compact totals. Each supporting URL is conservatively charged for the entire card body, its learning takeaway, all attached evidence notes, all relation notes and the author-review limits. Multi-source cards are charged in full to each source. The RFC 9421 HTML/text representations share one budget.', '',
    'Reference titles and locators, frozen selection inputs and pre-existing imported records are excluded as metadata/input provenance. Research-note references give locators rather than new summaries for tightly shared sources. No generated direct quotations are used. Every charged URL remains within 200 words; the maximum is 198.', '',
    '| Shared source | Supplying cards | Body words | All charged words | Limit |',
    '| --- | --- | ---: | ---: | ---: |',
]
for sid,account in sorted(b['by_source'].items()):
    if len(account['concept_ids'])>1:
        title=sources[sid]['title']
        ids=', '.join(f'`{i}`' for i in account['concept_ids'])
        lines.append(f'| [{title}]({account["source_url"]}) | {ids} | {account["card_words"]} | {account["attributed_generated_words"]} | 200 |')
lines += ['',
    '## Author-reviewed card ledger', '',
    'The source links below identify support for the current bodies. `author-review.json` gives the inspected passages, relationship outcomes, versions and limits for every ID.', '',
    '| ID and title | Words | Version | Sources |', '| --- | ---: | ---: | --- |',
]
for x in c['concepts']:
    refs=', '.join(f'[{e["source_id"]}]({sources[e["source_id"]]["url"]})' for e in x['evidence'])
    lines.append(f'| `{x["id"]}` — {x["label"]} | {len(x["card"].split())} | {x["card_version"]} | {refs} |')
lines += ['',
    '## Control provenance and validation', '',
    'Every control retains `original_description` exactly as the pinned baseline stores it, including null where appropriate. Every raw baseline inventory row is preserved unchanged in `imported_records`. `batch.control_version_decisions` carries the prior full `candidate_records`, baseline pointers, reference-bundle paths/hashes and approved maximum-plus-one version decisions. `baseline.latest_card` is not substituted for a full prior record.', '',
    'The adapter’s `stock_module().validate_candidate` passes. Separate checks pass for exact approved IDs and versions, baseline hashes, source resolution, registered/reserved relationship targets, normalized alias checks, raw control preservation and body budgets. These structural checks and author review do not replace the fixed independent factual audit. Audit samples have not been created, resampled or frozen by this researcher.', '',
    '## Access and usage', '',
    'Some preferred references were inaccessible or lacked extractable passages. They are documented in `source-access-log.json`; failed fetches, client challenges and search snippets are not explanatory evidence. The friendship-paradox and relative-performance cards remain bounded to inspected primary abstracts. All 61 cards have supporting inspected passages, so those access limits cause no card-count shortfall.', '',
    'Per-agent token consumption and monetary cost are unavailable in exposed telemetry and are recorded as null. No API-per-concept generator, installation, commit, operational import or coordinator-file edit was performed. The next step belongs to the coordinator’s independent audit.', '',
]
(ROOT/'research-notes.md').write_text('\n'.join(lines))
print(json.dumps(dict(status='notes_complete', candidate_sha256=sha(ROOT/'candidate.json'),
    cards=len(c['concepts']), author_reviews=len(a['reviews']), source_urls=len(c['sources']),
    maximum_source_prose_words=max(z['attributed_generated_words'] for z in b['by_source'].values())),ensure_ascii=False))
