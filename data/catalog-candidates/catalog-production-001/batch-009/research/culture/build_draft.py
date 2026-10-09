"""Assemble manually authored card bodies with exact frozen imports. No model/network clients."""
import json, copy, hashlib, collections, datetime
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
write=lambda name,value:(HERE/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
approved=read(HERE/'approved-selection.json')
baseline=read(ROOT/'baseline-index.json')
proposals=read(HERE/'proposals.json')
inspections=read(HERE/'sources-inspected.json')
assert sha(ROOT/'baseline-index.json')==approved['baseline_index_sha256']
assert sha(HERE.parents[1]/'selection-manifest.json')==approved['global_selection_manifest_sha256']
assert approved['global_selection_manifest_sha256']=='4802e1cc037ce1b0d47479801236fce29b3c759b466c8f1011b3a4c3438b86b8'

cards={
'local:authored:000664':'Physical geography studies how water, air, land, and living things interact to shape Earth’s landscapes.',
'Q309372':'This map projection makes constant compass bearings straight, helping navigation while stretching areas increasingly toward the poles.',
'Q1753196':'This projection preserves distances and directions from its center; those guarantees do not extend to every pair of mapped points.',
'Q34027':'Latitude measures north–south angular position from the equator, reaching 90 degrees at either pole.',
'Q36477':'Longitude measures east–west angular position from a prime meridian; equal degree intervals represent shorter ground distances near the poles.',
'Q22664':'A geographic coordinate system combines latitude and longitude with a reference model, so coordinates identify locations relative to a specified Earth.',
'Q182139':'Panama’s land bridge joined the Americas and closed a marine passage, separating ocean populations and altering circulation.',
'Q189849':'At Croatia’s Plitvice Lakes, calcium carbonate deposits build barriers that continually reshape the lakes and waterfalls.',
'Q112754':'A primary source records a participant’s or witness’s perspective. Firsthand evidence still needs interpretation because its creator can be biased.',
'local:authored:000073':'Public history interprets the past with public audiences and communities, through work such as museums, archives, and oral history.',
'Q166118':'An archive is an organization that preserves selected records of lasting value and makes them available for later research.',
'Q1506365':'From 1910 to 1970, Black Americans left the South in large numbers, escaping racial oppression and seeking work and education.',
'Q868393':'The Underground Railroad encompassed escapes from American slavery along many routes, sometimes unaided and sometimes supported by informal or organized helpers.',
'Q472802':'The Treaty of Waitangi’s Māori and English texts conveyed different understandings of governance and chiefly authority, fueling disputes over their promises.',
'Q180897':'In 1494, Spain and Portugal divided Atlantic imperial claims along a meridian, placing what is now eastern Brazil in Portugal’s sphere.',
'Q5086':'Built to stop flight from East Germany, the Berlin Wall enclosed West Berlin and developed into a layered border system.',
'Q217450':'The 1783 Treaty of Paris ended the American Revolutionary War: Britain recognized US independence, and the settlement defined the new country’s boundaries.',
'Q80056':'A traditional sonnet packs thought into fourteen lines, often pivoting at a turn that redirects the poem’s argument.',
'Q37707':'Haiku concentrates a brief moment into vivid images. Modern adaptations can use juxtaposition without keeping a fixed syllable count.',
'Q131361':'Irony creates a gap between appearances and reality; dramatic irony lets readers understand something a character does not.',
'Q1697305':'A narrative motif is a repeated detail or pattern that connects scenes and helps reinforce a theme.',
'Q1758354':'Plot organizes a story’s actions and consequences, making separate events connect through the structure of their telling.',
'Q616622':'A first-person narrator tells events through an “I”; the voice reveals character through how the story is told.',
'Q693':'A fable dramatizes a lesson: Aesop’s fox cannot reach the grapes, then calls them sour to dismiss his failure.',
'Q4026918':'The Epic of Sundiata carries Mali’s founding story through griots, whose oral performances connect audiences with ancestral memory.',
'Q164204':'Musicology studies how people make, understand, and use music across societies and historical periods, connecting sounds with human lives.',
'Q113558':'Dynamics indicate musical loudness. A crescendo directs performers to become louder, shaping how a passage develops.',
'Q14088448':'In classical tonal music, a cadence coordinates harmony, melody, and rhythm into an arrival that punctuates a phrase or section.',
'Q176501':'Timbre is sound quality beyond pitch: instruments playing the same note can sound different because their pressure waves have different shapes.',
'Q181014':'A fugue builds imitative music from independent voices; in a Baroque exposition, those voices introduce the main theme successively.',
'Q221686':'Twelve-tone composition arranges all twelve pitch classes into an ordered row, then transforms it through operations such as inversion or reversal.',
'Q3344470':'A nonchord tone lies outside the current chord. Passing tones connect chord tones by moving through the intervening notes stepwise.',
'Q623939':'In equal temperament, a tritone spans six semitones; its spelling can make it an augmented fourth or diminished fifth.',
'Q44325':'Ontology asks what exists, including disputed cases such as numbers and properties, and how we might settle those existence questions.',
'Q1570367':'The problem of induction asks why past regularities justify predictions about unobserved cases; appealing to past success risks arguing in a circle.',
'Q192600':'Fallibilism allows justified belief without certainty: the reasons supporting a claim can be good without guaranteeing that the claim is true.',
'Q209681':'Kant’s universal-law formulation asks whether the rule behind your action could be consistently willed as a law for everyone.',
'Q3738092':'Act utilitarianism judges each available action directly by its consequences, favoring the option that produces the greatest overall well-being.',
'Q651440':'Rule utilitarianism judges actions using rules that would produce the greatest overall well-being if generally accepted.',
'Q33378':'Zeno’s dichotomy challenges motion: reaching a destination seems to require completing infinitely many halfway steps before arrival.',
'Q56003':'Metaethics examines moral judgments themselves: what they mean, whether they can be true, and what could justify them.',
'Q1068288':'In US law, due process requires fair procedures when government deprives someone of protected life, liberty, or property.',
'Q898871':'US courts exercise judicial review by invalidating government actions that conflict with the Constitution.',
'Q79896':'In the US system, legislative, executive, and judicial powers sit in different branches that can check one another’s authority.',
'Q204886':'Federalism divides governing authority between national and regional governments; in the US, some powers are shared and others reserved.',
'Q328293':'US constitutional bans on ex post facto laws prohibit retroactive criminal punishment, including later increases in punishment for earlier conduct.',
'Q1323789':'A US federal grand jury decides whether probable cause supports criminal charges; it does not decide guilt.',
'Q12602483':'A US federal petit jury decides trial verdicts, with different proof standards for criminal and civil cases.',
'Q219447':'England’s 1689 Bill of Rights required Parliament’s consent for taxation and protected freedom of speech within Parliament.',
'Q124058':'Zakat is Islamic almsgiving from accumulated wealth to those in need, understood as purification of the wealth that remains.',
'Q41831':'Islam’s profession of faith joins two affirmations: God is one, and Muhammad is God’s messenger.',
'Q35856':'Baptism is Christian initiation through water; traditions vary over infant or adult baptism and how the water is applied.',
'Q66086':'The Eucharist is a Christian rite in which a community shares sacred bread and wine, also called the Lord’s Supper.',
'Q191431':'In Esoteric Buddhism, mandalas are cosmic diagrams used in meditation, often alongside sacred formulas and hand gestures.',
'Q183379':'In Hindu Vedanta, moksha means liberation from rebirth through insight; schools differ on how the self relates to ultimate reality.',
'Q42927':'In Buddhism, nirvana involves extinguishing greed, hatred, and delusion, which are described as fueling the cycle of rebirth.',
'Q10283':'Kumbh Mela brings Hindu pilgrims to rotating Indian river sites for sacred bathing, religious teaching, and exchange among spiritual traditions.',
'Q1473346':'Medieval European stained-glass windows join colored glass with lead strips; artists add painted details for outlines and shadows.',
'Q133067':'A mosaic builds images from small pieces of stone, ceramic, or glass; Roman floor mosaics made pictures durable enough to walk on.',
'Q204330':'Gouache is opaque, matte paint. Artists can add it to transparent watercolors for highlights, as Delacroix did to suggest shining armor.',
'Q1164982':'Color Field paintings emphasize large areas of color; Rothko layered thinned paint so underlying hues shine through and create subtle variations.',
'Q170571':'Still life depicts inanimate objects; Dutch examples use skulls, watches, and luxury goods to suggest mortality or wealth.',
'Q200034':'Pointillism builds paintings from small, separate colored dots that can blend visually at a distance, as in Seurat’s mature work.',
'Q185905':'Ukiyo-e includes Japanese woodblock prints made through coordinated work by designers, carvers, printers, and publishers, bringing popular subjects to commercial audiences.',
'Q214127':'Genre painting portrays everyday life; Northern European examples can carry moral lessons or social commentary through apparently ordinary scenes.',
}
reserved={p['id']:p for p in approved['accepted']}
assert set(cards)==set(reserved)
assert all(1<=len(body.split())<=25 for body in cards.values()),[(k,len(v.split())) for k,v in cards.items() if len(v.split())>25]
concepts=[]
for cid,p in reserved.items():
    base=baseline['concepts'][cid]
    assert not base.get('candidate_records') and not base.get('latest_card')
    evidence=[{'source_id':e['source_id'],'locator':e['locator'],'note':e['support_note']} for e in p['discovery_evidence']]
    urls=list(dict.fromkeys(r['source_url'] for r in base['inventory_records'] if r.get('source_url','').startswith(('https://','http://'))))
    if not urls: urls=[p['discovery_evidence'][0]['url']]
    concept={'id':cid,'label':p['label'],'aliases':copy.deepcopy(p['aliases']),'entity_kind':p['entity_kind'],'scope':p['scope'],'domains':[p['primary_domain']]+[d for d in base.get('domains',[]) if d!=p['primary_domain']],'learning_takeaway':p['learning_takeaway'],'card':cards[cid],'original_description':base['original_description'],'identity_urls':urls,'evidence':evidence,'relations':[copy.deepcopy(p['proposed_parent'])] if p['proposed_parent'] else [],'card_version':1,'imported_records':copy.deepcopy(base.get('inventory_records',[]))}
    concepts.append(concept)
issues=copy.deepcopy(proposals['issues'])
for issue in issues:
    if issue['id']=='culture-selection-stage':
        issue.update(status='resolved_by_global_reservations',reason='Approved selection is frozen. Drafts await completed author review and independent audit.')
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
batch={'id':'research-batch-009-culture','revision':1,'production_id':'catalog-production-001','kind':'production_first_card_candidate_shard','baseline_index_sha256':approved['baseline_index_sha256'],'global_selection_manifest_sha256':approved['global_selection_manifest_sha256'],'approved_owner_selection_sha256':sha(HERE/'approved-selection.json'),'target':65,'language':'en','created_at':now,'word_budget':{'minimum':1,'maximum':25,'counting':'Whitespace-separated card body; title and source links excluded.'},'ownership':{'assignment':'culture','primary_domains':sorted({p['primary_domain'] for p in reserved.values()}),'subfields':sorted({p['primary_subfield'] for p in reserved.values()})},'acquisition_limits':{'url_attempts_max':2,'alternative_sources_max':3,'sources':'Primary, official, or authoritative educational passages; actual inspection methods retained.','time_basis':'Source timestamps refer to observed inspection-session checkpoints, not individual network request times.'},'selection_input_policy':'Frozen public inventory only; private preferences excluded.'}
candidate={'schema_version':1,'batch':batch,'sources':copy.deepcopy(inspections['sources']),'concepts':concepts,'issues':issues,'validation':{'status':'draft_complete_author_review_pending','structural_passed':False,'author_checks_completed':0,'independent_audit':'pending; no acceptance claim'}}
write('candidate.json',candidate)
write('draft-checkpoint.json',{'schema_version':1,'status':'all_65_bodies_drafted_author_review_pending','candidate_sha256':sha(HERE/'candidate.json'),'baseline_index_sha256':batch['baseline_index_sha256'],'global_selection_manifest_sha256':batch['global_selection_manifest_sha256'],'body_count':len(concepts),'minimum_words':min(len(c['card'].split()) for c in concepts),'maximum_words':max(len(c['card'].split()) for c in concepts),'recorded_at':now})
if not (HERE/'selection-source-word-budgets.json').exists():
    (HERE/'selection-source-word-budgets.json').write_bytes((HERE/'source-word-budgets.json').read_bytes())
write('draft-input-preservation.json',{'schema_version':1,'baseline_index_sha256':sha(ROOT/'baseline-index.json'),'owned_input_sha256':{name:sha(HERE/name) for name in ['proposals.json','sources-inspected.json','selection-review.md','approved-selection.json','selection-source-word-budgets.json']}})
print(json.dumps({'drafted':len(concepts),'minimum_words':min(len(c['card'].split()) for c in concepts),'maximum_words':max(len(c['card'].split()) for c in concepts),'candidate_sha256':sha(HERE/'candidate.json')},indent=2))
