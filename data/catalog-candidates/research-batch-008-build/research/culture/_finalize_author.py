"""Author corrections and metadata completion before coordinator freezing."""
from datetime import datetime, timezone
from _draft_tools import HERE, read, write, assemble

now = datetime.now(timezone.utc).isoformat()
drafts = read(HERE / 'draft-cards.json')
drafts['local:catalog:ottava-rima']['body'] = drafts['local:catalog:ottava-rima']['body'].replace('alternate three rhymes','alternate two rhymes')
drafts['local:catalog:double-dactyl']['body'] = 'A double dactyl is light verse in two four-line stanzas. Most lines contain two feet, each with a stressed syllable followed by two unstressed ones. Nonsense, a person’s name, one six-syllable word and shorter rhyming endings create a compact compositional puzzle.'
drafts['local:catalog:double-dactyl']['additional_evidence'] = [dict(
    source_id='culture-aap-glossary',locator='Dactyl entry, line 94',note='Metrical foot definition inspected.')]
drafts['local:catalog:khipu']['relations'] = [dict(target_id='Q28573',type='related_to',source_ids=['nist-khipu'],
    assertion='source_asserted',note='NIST documents khipu use throughout the Inca Empire.')]
drafts['local:catalog:khipu']['gap'] = 'The source establishes Inca use of khipus; this setting is retained as related_to rather than made a universal category parent.'
drafts['local:catalog:khipu'].setdefault('limits',[]).append('The Inca Empire relation records a documented use setting, not the full geographical or historical boundary of khipu.')
for d in drafts.values(): assert 30 <= len(d['body'].split()) <= 50
write(HERE / 'draft-cards.json',drafts)

sources = read(HERE / 'draft-sources-inspected.json')
titles = {
 'culture-rgs-geography':'What is geography?',
 'culture-esri-buffer':'How Buffer (Analysis) works',
 'culture-poetry-archive-form':'Form',
 'culture-aap-sestina':'Sestina', 'culture-aap-cento':'Cento', 'culture-aap-haibun':'Haibun', 'culture-aap-triolet':'Triolet',
 'culture-sep-grounding':'Metaphysical Grounding', 'culture-sep-truthmakers':'Truthmakers',
 'culture-sep-fitting-attitudes':'Fitting Attitude Theories of Value',
 'culture-sep-feminist-social-epistemology':'Feminist Social Epistemology',
 'met-lukasa-1977-467-3':'Lukasa (Memory Board)',
 'met-paiza-1993-256':'Safe Conduct Pass (Paiza) with Inscription in Phakpa Script',
 'wsn-shibori':'What is Shibori?',
 'culture-fricker-introduction':'Introduction',
 'culture-uncg-double-dactyl':'double dactyl'
}
for s in sources:
    if s['id'] in titles: s['title'] = titles[s['id']]
    if s['id'] in {'culture-aap-glossary','culture-uncg-double-dactyl','culture-poetry-archive-form'}:
        s.setdefault('selection_inspected_at',s['inspected_at'])
        s['inspected_at']=now
        s['acquisition']['local_inspection_completed_at']=now
write(HERE / 'draft-sources-inspected.json',sources)

access = read(HERE / 'draft-source-access-limits.json')
for family,attempts,error,disposition in [
 ('Poetry Foundation double-dactyl glossary',2,'HTTP 403 in drafting research.','Accessible UNCG instructional text and Academy metrical glossary used; no poem excerpts copied.'),
 ('Butler Word Ways double-dactyl article',2,'Cache misses in drafting research.','Accessible UNCG instructional text used.')
]:
    if not any(x.get('source_family')==family for x in access):
        access.append(dict(source_family=family,exact_url_status='Exact failed URL not retained in this resumed research context.',attempts=attempts,error=error,disposition=disposition,local_recorded_at=now,claim_support=False))
write(HERE / 'draft-source-access-limits.json',access)
assemble()
