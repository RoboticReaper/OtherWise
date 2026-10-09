"""Write cited author handoff notes from the checked shard; no source sampling."""
from collections import defaultdict
from _draft_tools import HERE, BUILD, ROOT, read, sha

candidate=read(HERE/'candidate.json')
validation=read(HERE/'draft-validation.json')
baseline=read(BUILD/'baseline-index.json')['concepts']
global_selection=read(BUILD/'selection-manifest.json')['accepted']
labels={cid:c['label'] for cid,c in baseline.items()}
labels.update({c['id']:c['label'] for c in global_selection})
sources={s['id']:s for s in candidate['sources']}
counts=validation['counts']
lines=[
 '# Culture shard author handoff — research batch 008',
 '',
 'Status: draft ready for independent source audit. The author completed the 70 approved cards and reviews; the coordinator owns freezing, sampling and acceptance. No operational catalog import was performed.',
 '',
 f'Validated counts: {counts["cards"]} cards, {counts["new"]} new identities, {counts["controls"]} existing controls, {counts["new_fine"]} new fine-scope subjects and {counts["named"]} named subjects. Every body has 30–50 whitespace-separated English words. All four scopes are represented. The named-subject goal is measured, not a reason to invent identities.',
 '',
 f'Among {counts["fine"]} fine-scope cards, {counts["fine_with_parent"]} have a supported parent/application edge and {counts["fine_with_source_asserted_parent"]} have one marked source_asserted. Source assertions cite an actual relationship; editorial historical or learning placements remain marked editorial.',
 '',
 '| Primary domain | Cards |',
 '| --- | ---: |'
]
for domain,count in validation['domains'].items():lines.append(f'| {domain} | {count} |')
lines += ['', '| Scope | Cards |', '| --- | ---: |']
for scope,count in validation['scopes'].items():lines.append(f'| {scope} | {count} |')
lines += [
 '', '## Inputs and validation', '',
 f'- Global approved selection SHA256: `{candidate["batch"]["global_selection_manifest_sha256"]}`.',
 f'- Baseline index SHA256: `{candidate["batch"]["baseline_index_sha256"]}`.',
 f'- Shard approved-selection SHA256: `{candidate["batch"]["approved_selection_sha256"]}`.',
 f'- Final candidate SHA256: `{sha(HERE/"candidate.json")}`.',
 f'- [Local check report]({HERE/"draft-validation.json"}) verifies the stock adapter validator, pinned hashes, all approved identities and versions, 70 reviews, source and target resolution, exact and punctuation/diacritic alias intersections, domain counts, control provenance and per-source allocations.',
 f'- [Author review]({HERE/"author-review.json"}) contains outcomes, inspected locators, card versions and limits for every ID. Independent audit status remains pending.',
 '',
 'Existing controls retain canonical labels and IDs, exact original descriptions, every baseline raw inventory row, all prior full card records and checked source-bundle hashes. Version selection is approved maximum plus one; new subjects use version 1. Local raw source pointers remain inside the preserved imported rows, while identity_urls contains HTTP(S) references.',
 '',
 '## Source and coverage limits', '',
 f'{len(sources)} public source records have actual titles and valid acquisition timestamps. Each timestamp is explicitly the local clock after passage inspection; the exact remote retrieval instant is unavailable. Stored inspection metadata remains in [draft-sources-inspected.json]({HERE/"draft-sources-inspected.json"}), with pointers from the candidate.',
 '',
 'Cumulative new body, takeaway, evidence-note and relation-note prose stays within each 200-word source allocation. Bibliographic titles and locators, and unchanged archival prior records, are excluded from that count. The three largest allocations are Fricker’s Introduction (190), the Vienna Convention (185), and the Met portfolio article (182). Poetry forms use several distinct educational sources; the shared Poetry Archive form page supports only ottava rima in the final candidate.',
 '',
 'Pinpeat has an evidence-limited definition and a lesson-based comparative takeaway. The accessible introduction supports its selected boundaries; detailed slide and instrument claims were omitted. Religious practice cards preserve tradition-specific or teacher-specific interpretations. Law cards retain instrument, jurisdiction and edition limits. Named artifacts identify the specific work or object rather than a general category.',
 '',
 f'Actual access outcomes are recorded in [selection limits]({HERE/"source-access-limits.json"}) and [drafting limits]({HERE/"draft-source-access-limits.json"}). UNESCO ICH CAPTCHA, UNHCR HTTP 429, failed PDFs/slides, NCCA HTTP 502, Poetry Foundation HTTP 403 and unavailable Word Ways/Gamelan routes did not become claim support. Exact failed URLs were not retained for two resumed source-family records, which is stated explicitly. Accessible alternatives carry their own inspected citations.',
 '',
 'Satori, Arashi shibori and Spenserian stanza remain excluded alternatives. No substitutions or new identities were added after approval. Token and cost usage are unavailable to this researcher.',
 '',
 '## Explicit category gaps', ''
]
for gap in candidate['batch']['missing_parent_links']:
    lines.append(f'- `{gap["id"]}` ({labels[gap["id"]]}): {gap["reason"]}')
lines += [
 '',
 'Khipu retains the documented Inca setting as related_to. The six projection methods remain idea. Both buffering methods retain source_asserted facet_of links to geographic-buffer; the ambiguous bare Planar buffering alias is absent. The Itoh garment uses the corrected Met URL ending in 79595.',
 '',
 '## Inspected references by card', '',
 'The locators below apply to the emitted body and its attached relationships. Full source metadata and historical control reference bundles are in the candidate. Version and body word count are separate from the title and references.',
 '',
 '| Subject and ID | Words / version | Inspected passages | Attached relationship |',
 '| --- | ---: | --- | --- |'
]
for c in candidate['concepts']:
    refs=[]
    for e in c['evidence']:
        s=sources[e['source_id']]
        refs.append(f'[{s["title"]}]({s["url"]}) — {e["locator"]}')
    evid={e['source_id'] for e in c['evidence']}
    for r in c['relations']:
        for sid in r['source_ids']:
            if sid not in evid:
                s=sources[sid];refs.append(f'[{s["title"]}]({s["url"]}) — {s["locator"]}');evid.add(sid)
    relation='; '.join(f'{r["type"]} → {labels[r["target_id"]]} (`{r["target_id"]}`), {r["assertion"]}' for r in c['relations']) or 'Explicit gap'
    lines.append(f'| {c["label"]} (`{c["id"]}`) | {len(c["card"].split())} / v{c["card_version"]} | '+ '<br>'.join(refs).replace('|','\\|') + f' | {relation} |')
lines += ['', '## Handoff boundary', '', 'The candidate is stable for coordinator freezing after the checks recorded above. These are author and structural checks; factual acceptance still depends on the independent audit. This author did not choose or resample the audit set.', '']
(HERE/'research-notes.md').write_text('\n'.join(lines))
print('Wrote research-notes.md with citations for',len(candidate['concepts']),'cards.')
