"""Bookkeeping for the manually researched culture selection; no network or model clients."""
import json, hashlib, collections
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
baseline_path = ROOT / 'baseline-index.json'
baseline = json.loads(baseline_path.read_text())
eligible_doc = json.loads((HERE / 'eligible-identities.json').read_text())
eligible = {x['id']:x for x in eligible_doc['concepts']}
sha = hashlib.sha256(baseline_path.read_bytes()).hexdigest()
sources = json.loads((HERE / 'sources-checkpoint.json').read_text())['sources']
by_source = {x['id']:x for x in sources}

# Every passage below was inspected with web tools before the interruption.
new_sources = [
('nara-primary','History in the Raw','https://www.archives.gov/education/research/history-in-the-raw.html','Main explanation, lines 29–38','turn657view0','2016-08-15',None),
('nara-paris','Treaty of Paris (1783)','https://www.archives.gov/milestone-documents/treaty-of-paris','Introduction, lines 36–38; transcript Articles 1–2, lines 56–61','turn658view0','2025-03-06',None),
('nz-waitangi','Differences between the texts','https://nzhistory.govt.nz/page/differences-between-texts','Opening and First/Second articles, lines 6, 20–27','turn654view1','2026-03-12',None),
('unesco-tordesillas','Registre de la Mémoire du monde: Traité de Tordesillas (Espagne et Portugal), Réf. 2006-43','https://media.unesco.org/sites/default/files/webform/mow001/spain_portugal_treaty_tordesillas_fr_0.pdf','French nomination, PDF page 1 (index 0), summary lines 6–14; page 4 (index 3), lines 111–117','turn642view1',None,'2007-04-10'),
('poets-sonnet','Sonnet','https://poets.org/glossary/sonnet','Definition and traditional forms, lines 28, 38–43','turn578view0',None,None),
('poets-haiku','Haiku','https://poets.org/glossary/haiku','Definition and modern adaptations, lines 28, 38–39','turn684view0',None,None),
('os-motif','What is a Motif?','https://liberalarts.oregonstate.edu/wlf/what-motif','Transcript, lines 34–38','turn627view1',None,'2021-10-26'),
('loc-fable','The Fox & the Grapes — The Aesop for Children','https://read.gov/aesop/005.html','Story and moral, lines 5–14','turn590view2',None,None),
('omt-dynamics','Other Aspects of Notation — Open Music Theory','https://viva.pressbooks.pub/openmusictheory/chapter/other-aspects-of-notation/','Dynamics, lines 1048–1057, 1077','turn683view0',None,None),
('omt-cadence','Classical cadence types — Open Music Theory','https://openmusictheory.github.io/cadenceTypes.html','Opening definition, line 6','turn639view3',None,None),
('omt-fugue','High Baroque Fugal Exposition — Open Music Theory','https://viva.pressbooks.pub/openmusictheory/chapter/high-baroque-fugal-exposition/','Opening explanation and exposition, lines 1048–1059','turn639view1',None,None),
('omt-twelvetone','Twelve-Tone Theory — Basics','https://openmusictheory.github.io/twelveToneBasics.html','Serialism/rows and transformations, lines 5–8, 15–16','turn665view2',None,None),
('pugetsound-nonchord','Introduction to Non-Chord Tones — Music Theory for the 21st-Century Classroom','https://musictheory.pugetsound.edu/mt21c/NonChordTonesIntroduction.html','Definition and classification table, lines 733–755','turn653view3',None,None),
('omt-tritone','Intervals — Open Music Theory','https://viva.pressbooks.pub/openmusictheory/chapter/intervals/','Diminished fifth and augmented fourth, lines 1147, 1236; semitone table, lines 1245–1258','turn673view0',None,None),
('sep-induction','The Problem of Induction','https://plato.stanford.edu/entries/induction-problem/','Opening explanation, lines 13–18','turn581view0','2022-11-22','2018-03-21'),
('iep-fallibilism','Fallibilism','https://iep.utm.edu/fallibil/','Definition and epistemic justification, lines 37–44','turn585view0',None,None),
('sep-kant','Kant’s Moral Philosophy','https://plato.stanford.edu/entries/kant-moral/','Section 5, universal-law formulation, lines 132–134; lying-promise example, line 143','turn585view1',None,None),
('iep-utilitarian','Utilitarianism, Act and Rule','https://iep.utm.edu/util-a-r/','Act/rule contrast, lines 90–93; rules and exceptions, lines 146, 159–162','turn585view2',None,None),
('sep-zeno','Zeno’s Paradoxes','https://plato.stanford.edu/entries/paradox-zeno/','Dichotomy, lines 126–130','turn585view4',None,None),
('sep-ontology','Logic and Ontology','https://plato.stanford.edu/entries/logic-ontology/','What exists and disputed cases, lines 116–119; conceptions of ontology, lines 129–139','turn585view5',None,None),
('sep-metaethics','Metaethics','https://plato.stanford.edu/entries/metaethics/','Opening explanation, lines 13–15','turn665view0','2023-01-24','2007-01-23'),
('uscourts-juries','Types of Juries','https://www.uscourts.gov/court-programs/jury-service/types-juries','Trial jury, lines 571–577; grand jury, line 583','turn627view5',None,None),
('met-mandala','Japanese Mandalas: Emanations and Avatars','https://www.metmuseum.org/exhibitions/listings/2009/japanese-mandalas','Exhibition explanation, lines 67–70','turn650view1',None,None),
('pib-kumbh','The Maha Kumbh Mela 2025: Embracing Unity in the Sacred Waters of Prayagraj','https://static.pib.gov.in/WriteReadData/specificdocs/documents/2024/nov/doc2024115429601.pdf','PDF page 1 (index 0), lines 6–15; page 2 (index 1), lines 25–32','turn657view2',None,'2024-11-05'),
('met-fresco','Italian Painting of the Later Middle Ages','https://www.metmuseum.org/essays/italian-painting-of-the-later-middle-ages','Fresco technique, lines 152–155','turn601view8',None,None),
('met-engraving','Engraving','https://www.metmuseum.org/perspectives/materials-and-techniques-printmaking-engraving','Intaglio and burin, lines 17, 21–24; printing, lines 33–43','turn590view5',None,'2018-12-21'),
('met-etching','Etching','https://www.metmuseum.org/perspectives/materials-and-techniques-printmaking-etching','Ground and acid process, lines 23–36; reversed image, line 46','turn590view6',None,'2018-12-21'),
('met-gouache','Watercolor','https://www.metmuseum.org/perspectives/materials-and-techniques-drawing-watercolor','Opaque gouache/bodycolor and highlights, lines 42–47','turn687view0',None,'2020-05-01'),
('met-stilllife','Still-Life Painting in Northern Europe, 1600–1800','https://www.metmuseum.org/essays/still-life-painting-in-northern-europe-1600-1800','Objects, mortality symbolism, and luxury, lines 132–144','turn676view0',None,'2003-10-01'),
('met-pointillism','Georges Seurat — Study for A Sunday on La Grande Jatte','https://www.metmuseum.org/art/collection/search/437658','Object explanation, lines 10–11; audio transcript, lines 68–71','turn590view7',None,None),
('met-ukiyoe','Woodblock Prints in the Ukiyo-e Style','https://www.metmuseum.org/essays/woodblock-prints-in-the-ukiyo-e-style','Commercial production and four specialists, lines 100–104','turn601view9',None,'2003-10-01'),
('met-genre','Genre Painting in Northern Europe','https://www.metmuseum.org/essays/genre-painting-in-northern-europe','Everyday subjects and moral/social commentary, lines 209, 215–216, 231','turn601view10',None,'2008-04'),
('met-stainedglass','Stained Glass in Medieval Europe','https://www.metmuseum.org/essays/stained-glass-in-medieval-europe','Colored glass, painted details, and lead assembly, lines 109–113','turn721view0',None,'2001-10-01'),
('harvard-shahada','shahadah','https://pluralism.org/shahadah','Glossary definition, line 56','turn708view1',None,None),
('getty-mosaic','Some of Ancient Rome’s Best-Preserved Art','https://www.getty.edu/news/a-brief-introduction-to-roman-mosaics/','Floor durability and tesserae, lines 111–119; color materials, lines 131–132','turn708view2',None,'2016-04-04'),
('moma-colorfield','Mark Rothko’s Color Field Paintings','https://www.moma.org/audio/playlist/354/4963','Transcript: blocks and shades, lines 9–10; layered thin paint, lines 12–14','turn709view0',None,None),
('nga-printmaking','Printmaking Basics','https://www.nga.gov/educational-resources/printmaking-basics','Woodcut relief process, line 266','turn576view7',None,None),
('nz-waitangi-english','Read the Treaty: English text','https://nzhistory.govt.nz/politics/treaty/read-the-treaty/english-text','Introduction and articles, lines 13–18','turn645view3','2023-06-12',None),
('omt-embellishing','Embellishing tones — Open Music Theory','https://openmusictheory.github.io/embellishingTones.html','Passing-tone definition, line 8','turn639view2',None,None),
]
for key,title,url,locator,ref,revision,published in new_sources:
    item = {'id':'culture-'+key,'title':title,'url':url,'locator':locator,'inspection_mode':'web_pdf_text' if '.pdf' in url else 'web_text_open_find','tool_ref':ref,'revision':revision,'word_limit':200,'retrieved_at':'2026-10-09T04:36:47Z','acquisition_metadata':{'time_basis':'Inspection-session UTC checkpoint; individual request timestamps were not captured','session_first_observed_at':'2026-10-09T04:27:54Z','session_last_observed_at':'2026-10-09T04:36:47Z'}}
    if published: item['publication_date']=published
    by_source[item['id']]=item
for key,rev in {'nps-railroad':'2025-04-07','saa-archive':'2016-09-12','cornell-review':'2023-06','cornell-separation':'2024-09','cornell-federal':'2026-08','cornell-retro':'2025-10'}.items():
    by_source['culture-'+key]['revision']=rev
for key,pub in {'yale-sundiata':'2009-09','os-motif':'2021-10-26','os-irony':'2019-11-05','os-plot':'2026-05-14','os-firstperson':'2020-08-12'}.items():
    by_source['culture-'+key]['publication_date']=pub
by_source['culture-esri-gcs']['tool_ref']='turn687view1'
by_source['culture-os-irony']['locator']='Transcript, lines 34–35, 50–51'
by_source['culture-os-irony']['tool_ref']='turn683view2'
by_source['culture-iep-utilitarian']['additional_tool_refs']=['turn585view3']
for item in by_source.values():
    if 'retrieved_at' not in item: item['retrieved_at']=item['acquisition_metadata']['session_observed_at']
    item['word_limit_basis']='Retrieved web source allowance; one combined budget per page/companion source'
    if item['revision']: item['revision_metadata']={'kind':'page_last_reviewed_or_updated' if any(x in item['id'] for x in ['nara','nps','saa','cornell','nz-']) else 'substantive_revision','precision':'month' if len(item['revision'])==7 else 'day'}
by_source['culture-nz-waitangi-english']['budget_group']='culture-nz-waitangi'
by_source['culture-unesco-tordesillas'].pop('publication_date',None)
by_source['culture-unesco-tordesillas']['document_submission_date']='2007-04-10'
by_source['culture-met-mandala']['exhibition_dates']='2009-06-18/2009-11-29'
by_source['culture-met-gouache']['locator']='Transparent medium and white support, lines 7–23; opaque gouache and highlights, lines 42–47'
by_source['culture-met-gouache']['additional_tool_refs']=['turn703view1']
for short in ['met-gouache','harvard-shahada','getty-mosaic','moma-colorfield']:
    item=by_source['culture-'+short]
    item['retrieved_at']='2026-10-09T04:43:15Z'
    item['acquisition_metadata']={'time_basis':'Source inspection-session UTC checkpoint; individual request timestamps not captured','session_observed_at':'2026-10-09T04:43:15Z'}

by_source['culture-met-stainedglass']['retrieved_at']='2026-10-09T04:45:38Z'
by_source['culture-met-stainedglass']['acquisition_metadata']={'time_basis':'Source inspection-session UTC checkpoint; individual request timestamps not captured','session_observed_at':'2026-10-09T04:45:38Z'}

G='Geography & travel';H='History & culture';L='Literature & storytelling';M='Music & performance';P='Philosophy';J='Politics & law';R='Religion & spirituality';A='Visual arts & design'
# id, domain, subfield, kind, scope, source, takeaway, intended meaning, limit, parent, relation type
rows = [
('local:authored:000664',G,'Physical geography','idea','broad_field','iowa-physical','Interactions among water, air, land, and life shape the landscapes physical geographers study.','Physical branch of geography.','Landscape interactions, not an exhaustive field survey.','Q1071','broader_topic'),
('Q309372',G,'Cartography','idea','idea','esri-mercator','Mercator turns constant compass bearings into straight lines while enlarging areas toward the poles.','Conformal cylindrical map projection.','Rhumb lines need not be shortest routes.','Q186386','broader_topic'),
('Q1753196',G,'Cartography','idea','idea','esri-azimuthal','Distances and directions are accurate from the map’s center, not between every pair of points.','Center-based azimuthal map projection.','Distance guarantee applies from the center.','Q186386','broader_topic'),
('Q34027',G,'Geographic coordinates','idea','idea','esri-gcs','Latitude measures north–south angular position from the equator, with poles at ninety degrees.','Angular north–south coordinate.','Geographic coordinate meaning.','Q22664','facet_of'),
('Q36477',G,'Geographic coordinates','idea','idea','esri-gcs','Longitude measures east–west position from a chosen prime meridian; equal degree steps cover less distance near the poles.','Angular east–west coordinate.','Prime meridian must be specified.','Q22664','facet_of'),
('Q22664',G,'Geographic coordinates','idea','topic','esri-gcs','Coordinates need a reference model as well as latitude and longitude to specify Earth locations.','Geographic coordinates, not projected coordinates.','A datum alone is insufficient.','local:authored:000665','broader_topic'),
('Q182139',G,'Physical geography','named_subject','idea','smithsonian-panama','Panama’s land bridge joined the Americas while separating marine populations and changing ocean circulation.','The Central American land bridge.','No disputed exact closure date asserted.',None,None),
('Q189849',G,'Karst landscapes','named_subject','idea','unesco-plitvice','Calcium carbonate deposits build natural barriers that continually reshape this Croatian lake system.','The Croatian national park.','Tufa-building process is the selected angle.',None,None),
('Q112754',H,'Historical evidence','idea','idea','nara-primary','Firsthand records connect us to past participants, but their perspectives and biases still require interpretation.','Firsthand historical evidence.','Primary does not mean unbiased.','Q309','broader_topic'),
('local:authored:000073',H,'Public history','idea','broad_field','ncph-public','Public historians work with communities to interpret the past in museums, archives, and other public settings.','History practice with public audiences.','Collaboration varies across settings.','Q309','broader_topic'),
('Q166118',H,'Archives','idea','topic','saa-archive','Archives select records of lasting value, preserve them, and make documentary evidence available for future use.','Archival organization, not one file.','Archive also names records and buildings.','Q309','broader_topic'),
('Q1506365',H,'African American history','named_subject','topic','nara-migration','Black migration out of the South combined flight from racial oppression with pursuit of work and education.','African American migration, 1910–1970.','Destination discrimination also persisted.','Q309','broader_topic'),
('Q868393',H,'Slavery and self-emancipation','named_subject','idea','nps-railroad','Freedom seekers escaped slavery through many routes, sometimes unaided and sometimes assisted by organized or spontaneous help.','Self-emancipation effort, not a literal railway.','No single organization or uniform route.','Q309','broader_topic'),
('Q472802',H,'Colonial agreements','named_subject','idea','nz-waitangi','Differences between the Māori and English texts shaped disputes over governance and chiefly authority.','The 1840 New Zealand agreement.','Translations conveyed different understandings of authority.','Q309','broader_topic'),
('Q180897',H,'Imperial diplomacy','named_subject','idea','unesco-tordesillas','Spain and Portugal drew an Atlantic dividing line for imperial claims, placing eastern Brazil in Portugal’s sphere.','The 1494 Iberian treaty.','Imperial claims do not establish Indigenous consent.','Q309','broader_topic'),
('Q5086',H,'Cold War history','named_subject','idea','berlin-wall','The wall enclosed West Berlin to stop flight from East Germany and grew into a layered border system.','The 1961–1989 Berlin border system.','Not merely a single concrete wall.','Q309','broader_topic'),
('Q217450',H,'American independence','named_subject','idea','nara-paris','Britain recognized US independence in the peace settlement, which also defined boundaries for the new country.','The 1783 peace treaty.','Distinct from other treaties of Paris.','Q309','broader_topic'),
('Q80056',L,'Poetic forms','idea','idea','poets-sonnet','Traditional sonnets compress thought into fourteen lines, often using a turn to redirect the argument.','The poetic form.','Traditional pattern allows later variations.','local:authored:000404','broader_topic'),
('Q37707',L,'Poetic forms','idea','idea','poets-haiku','Haiku evokes a brief moment through concentrated images; modern adaptations need not follow a fixed syllable count.','The Japanese-derived poetic form.','Modern adaptations need not use fixed counts.','local:authored:000404','broader_topic'),
('Q131361',L,'Literary devices','idea','idea','os-irony','Irony creates gaps between appearance and reality, such as a character’s ignorance of information readers already know.','Literary and rhetorical irony.','Dramatic irony is one example.','Q8242','broader_topic'),
('Q1697305',L,'Narrative patterns','idea','facet_or_application','os-motif','Repeated details can connect scenes and reinforce themes without being the theme themselves.','Recurring narrative detail or pattern.','A motif is not the theme.','Q1318295','facet_of'),
('Q1758354',L,'Narrative structure','idea','facet_or_application','os-plot','Plot orders actions and their consequences into a structure that makes events feel connected.','Narrative events and their arrangement.','One plotting formula is not universal.','Q1318295','facet_of'),
('Q616622',L,'Narrative viewpoint','idea','facet_or_application','os-firstperson','First-person narrators reveal themselves through how they tell events, as well as through what happens.','Narration by an involved “I”.','First-person voice; not exhaustive narrator taxonomy.','Q1318295','facet_of'),
('Q693',L,'Story forms','idea','topic','loc-fable','Animal stories can dramatize human behavior, as the fox dismisses grapes he cannot reach.','Moral story genre, illustrated by Aesop.','One primary story illustrates the genre.','Q8242','broader_topic'),
('Q4026918',L,'Oral epic','named_subject','topic','yale-sundiata','Sundiata’s epic preserves Mali’s founding story through griots, whose performances connect listeners with ancestral memory.','The West African oral epic.','Multiple versions; Niane’s recording is one example.','Q8242','broader_topic'),
('Q164204',M,'Musicology','idea','broad_field','ams-musicology','Musicology investigates how music is made, understood, and used across societies and historical periods.','Scholarly study of music.','Not restricted to European art music.','Q638','broader_topic'),
('Q113558',M,'Musical notation','idea','facet_or_application','omt-dynamics','Dynamic markings guide loudness; a crescendo asks performers to grow louder.','Musical loudness and its markings.','Examples from Western staff notation.','local:authored:000214','facet_of'),
('Q14088448',M,'Musical form','idea','idea','omt-cadence','A cadence coordinates musical motion into a point of arrival that punctuates a phrase or larger unit.','Musical phrase arrival.','Classical tonal context.','local:authored:000214','broader_topic'),
('Q176501',M,'Musical sound','idea','idea','duke-timbre','Different instruments can play the same pitch yet sound distinct because their sound waves have different shapes.','Tone color, not pitch itself.','Wave shape is one explanatory angle.','local:authored:000214','broader_topic'),
('Q181014',M,'Counterpoint','idea','topic','omt-fugue','A fugue introduces its main theme in successive independent voices, building an imitative texture.','Contrapuntal musical procedure.','High Baroque exposition; later forms vary.','local:authored:000214','broader_topic'),
('Q221686',M,'Composition techniques','idea','idea','omt-twelvetone','Twelve-tone composition organizes all twelve pitch classes into ordered rows that can be transformed.','Ordered twelve-pitch-class method.','Serialism also includes other methods.','local:authored:000214','broader_topic'),
('Q3344470',M,'Harmony','idea','facet_or_application','pugetsound-nonchord','Notes outside the current chord can connect chord tones; passing tones move by step through the gap.','Tone outside the sounding harmony.','Passing tone is one type.','local:authored:000214','facet_of'),
('Q623939',M,'Intervals','idea','idea','omt-tritone','In equal temperament, a tritone spans six semitones and can be spelled as an augmented fourth or diminished fifth.','Musical interval, not a three-note chord.','Equal-temperament measurement.','local:authored:000214','broader_topic'),
('Q44325',P,'Metaphysics','idea','topic','sep-ontology','Ontology asks what exists and how to settle disputed cases such as numbers or properties.','Philosophical study of existence.','Not a computing ontology.','local:authored:000431','broader_topic'),
('Q1570367',P,'Epistemology','idea','idea','sep-induction','Past regularities support predictions, but justifying the jump to unobserved cases risks circular reasoning.','Justification problem for inductive inference.','Does not declare prediction useless.','local:authored:000430','broader_topic'),
('Q192600',P,'Epistemology','idea','idea','iep-fallibilism','A belief can be justified without its justification guaranteeing that it is true.','Fallibility of epistemic justification.','Compatible with some accounts of knowledge.','local:authored:000430','broader_topic'),
('Q209681',P,'Moral philosophy','idea','idea','sep-kant','Kant’s universal-law formulation tests whether your action’s guiding rule could be consistently willed for everyone.','Kant’s unconditional moral principle.','One formulation, not Kant’s whole ethics.','local:authored:000429','broader_topic'),
('Q3738092',P,'Consequentialist ethics','idea','idea','iep-utilitarian','Act utilitarianism evaluates each available action by the overall well-being it would produce.','Direct evaluation of individual actions.','Compare available actions.','local:authored:000440','broader_topic'),
('Q651440',P,'Consequentialist ethics','idea','idea','iep-utilitarian','Rule utilitarianism evaluates actions through rules whose general acceptance produces the most well-being.','Evaluation through utility-maximizing rules.','Rule codes can allow exceptions.','local:authored:000440','broader_topic'),
('Q33378',P,'Paradoxes of motion','idea','idea','sep-zeno','One paradox challenges motion because reaching a goal seems to require completing infinitely many halfway steps.','Zeno’s philosophical paradoxes.','Dichotomy is one paradox, not a proof motion fails.','Q5891','broader_topic'),
('Q56003',P,'Moral philosophy','idea','topic','sep-metaethics','Metaethics asks what moral judgments mean and whether or how they can be true.','Foundations and status of moral judgment.','Not a list of practical moral rules.','local:authored:000429','broader_topic'),
('Q1068288',J,'Constitutional safeguards','idea','idea','cornell-due','US due process requires fair procedures when government deprives people of protected life, liberty, or property.','Procedural constitutional protection.','US example; requirements depend on context.','Q11206','broader_topic'),
('Q898871',J,'Constitutional courts','idea','idea','cornell-review','US courts use judicial review to invalidate government actions that conflict with the Constitution.','Constitutional review by courts.','US example; institutional arrangements vary.','Q11206','broader_topic'),
('Q79896',J,'Constitutional structure','idea','topic','cornell-separation','Separating legislative, executive, and judicial functions lets institutions check one another’s power.','Division of governmental functions.','US example; not every system has identical branches.','Q11206','broader_topic'),
('Q204886',J,'Government structure','idea','topic','cornell-federal','Federalism distributes governing authority between national and regional governments, with some powers shared.','Multilevel constitutional government.','US example; divisions vary.','Q36442','broader_topic'),
('Q328293',J,'Constitutional safeguards','idea','idea','cornell-retro','In US law, ex post facto bans prevent retroactive criminal punishment or later increases in punishment.','Retroactive penal legislation.','US constitutional ban, not every retroactive law.','Q11206','broader_topic'),
('Q1323789',J,'Jury functions','idea','idea','uscourts-juries','In US federal courts, grand juries decide whether evidence supports criminal charges, rather than deciding guilt.','Charging jury.','US federal context.','Q36442','broader_topic'),
('Q12602483',J,'Jury functions','idea','idea','uscourts-juries','In US federal trials, petit juries decide verdicts, using different proof standards in criminal and civil cases.','Trial jury.','US federal context.','Q36442','broader_topic'),
('Q219447',J,'Constitutional history','named_subject','idea','parliament-bill','England’s 1689 settlement required Parliament’s agreement for taxation and protected speech within Parliament.','English Bill of Rights, 1689.','Parliamentary speech; not the US Bill of Rights.','Q11206','broader_topic'),
('Q124058',R,'Islamic practices','idea','idea','harvard-zakat','Zakat gives part of accumulated wealth to those in need and is understood as purification of the remaining wealth.','Islamic wealth almsgiving.','No universal threshold or rate asserted.','local:authored:000457','broader_topic'),
('Q41831',R,'Islamic practices','idea','idea','harvard-shahada','The Muslim profession of faith joins belief in God’s oneness with recognition of Muhammad as God’s messenger.','Islamic declaration of faith.','Two linked affirmations, not a full theology.','local:authored:000457','broader_topic'),
('Q35856',R,'Christian practices','idea','idea','harvard-baptism','Baptism marks entry into a Christian community through water; traditions differ over age and method.','Christian water initiation.','Some traditions do not practice outward baptism.','local:authored:000456','broader_topic'),
('Q66086',R,'Christian practices','idea','idea','harvard-communion','The Eucharist gathers Christians around shared sacred bread and wine.','Eucharistic rite, not church-family meaning of communion.','No single denominational account asserted.','local:authored:000456','broader_topic'),
('Q191431',R,'Buddhist visualization','idea','idea','met-mandala','In Esoteric Buddhism, cosmic diagrams guide meditation alongside hand gestures and sacred formulas.','Sacred diagram, not a decorative pattern alone.','One Buddhist use; other traditions also use mandalas.','local:authored:000460','related_to'),
('Q183379',R,'Hindu liberation','idea','idea','harvard-vedanta','Vedanta describes moksha as liberation from rebirth through insight, while its schools disagree about self and ultimate reality.','Hindu liberation from rebirth.','Vedanta example; Hindu accounts differ.','Q9089','broader_topic'),
('Q42927',R,'Buddhist liberation','idea','idea','harvard-nirvana','In Buddhism, nirvana involves extinguishing greed, hatred, and delusion that fuel rebirth.','Buddhist nirvana meaning.','Buddhist usage selected; other senses unaddressed.','local:authored:000460','broader_topic'),
('Q10283',R,'Hindu pilgrimage','named_subject','idea','pib-kumbh','Pilgrims gather at rotating Indian river sites for sacred bathing and the transmission of religious traditions.','The Kumbh Mela gathering tradition.','Purification is a religious belief.','Q9089','broader_topic'),
('Q1473346',A,'Glass art','idea','idea','met-stainedglass','Lead strips join colored glass pieces into window images, while painted details can supply outlines and shadows.','Colored glass used for pictorial windows.','Medieval European construction example.','Q735','broader_topic'),
('Q133067',A,'Mosaic techniques','idea','idea','getty-mosaic','Small pieces of stone, ceramic, or glass can form durable images, as Roman floor mosaics demonstrate.','Art made from assembled small pieces.','Roman floors are one example.','Q735','broader_topic'),
('Q204330',A,'Painting materials','idea','facet_or_application','met-gouache','Gouache’s opaque, matte paint can supply bright highlights within otherwise transparent watercolor compositions.','Opaque water-based paint.','One use within watercolor compositions.','Q11629','facet_of'),
('Q1164982',A,'Abstract painting','idea','topic','moma-colorfield','Large color areas can contain subtle shades; Rothko achieved this through layers of thinned paint.','Color Field painting, not a literal field.','Rothko’s process illustrates one approach.','Q11629','broader_topic'),
('Q170571',A,'Pictorial genres','idea','topic','met-stilllife','Arrangements of ordinary objects can suggest mortality or wealth, as Dutch still lifes show through skulls, watches, and luxuries.','Art genre depicting inanimate objects.','Northern European examples; meanings are not universal.','Q11629','broader_topic'),
('Q200034',A,'Painting techniques','idea','idea','met-pointillism','Small dots of separate colors can blend visually at a distance, as in Seurat’s mature technique.','Painting with discrete colored dots.','Final painting, not the study’s broader patches.','Q11629','broader_topic'),
('Q185905',A,'Japanese art','idea','topic','met-ukiyoe','Commercial ukiyo-e prints depended on coordinated work by designers, carvers, printers, and publishers.','Japanese floating-world art tradition.','Print production is one facet; paintings also exist.','local:authored:000351','related_to'),
('Q214127',A,'Pictorial genres','idea','topic','met-genre','Scenes of ordinary life can carry social commentary, even when their subjects appear familiar.','Depictions of everyday life.','Northern European examples; not all scenes moralize.','Q11629','broader_topic'),
]
assert len(rows)==65
proposals=[]
for identity,domain,subfield,kind,scope,short_source,takeaway,intended,limit,parent,relation in rows:
    source=by_source['culture-'+short_source]
    assert identity in eligible
    b=baseline['concepts'][identity]
    assert not b.get('candidate_records')
    p={'id':identity,'label':b['label'],'aliases':b['aliases'],'primary_domain':domain,'primary_subfield':subfield,'entity_kind':kind,'scope':scope,'learning_takeaway':takeaway,'identity_reason':intended,'discovery_evidence':[{'source_id':source['id'],'url':source['url'],'locator':source['locator'],'support_note':'Supports the selected explanatory takeaway.','inspection_mode':source['inspection_mode'],'tool_ref':source['tool_ref']}],'proposed_parent':None,'limits':[limit]}
    if parent:
        assert parent in baseline['concepts'] and parent!=identity
        p['proposed_parent']={'target_id':parent,'type':relation,'source_ids':[source['id']],'assertion':'editorial','note':'Editorial grouping from the inspected subject.'}
    proposals.append(p)

source_asserted = {
'local:authored:000664':'Physical geography is a branch of geography.',
'Q309372':'Explicitly identified as a map projection.',
'Q1753196':'Explicitly identified as a map projection.',
'Q34027':'Latitude specifies a geographic coordinate component.',
'Q36477':'Longitude specifies a geographic coordinate component.',
'Q112754':'Firsthand records are materials of historical inquiry.',
'local:authored:000073':'Public history interprets the past with publics.',
'Q80056':'Explicitly identified as a poetic form.',
'Q37707':'Explicitly identified as a poetic form.',
'Q131361':'Presented as a literary device.',
'Q1697305':'Repeated patterns operate within narratives.',
'Q1758354':'Plot arranges a narrative’s events.',
'Q616622':'Point of view shapes narrative telling.',
'Q164204':'Musicology is scholarly study of music.',
'Q113558':'Explicit Open Music Theory notation chapter.',
'Q14088448':'Explicit Open Music Theory form lesson.',
'Q181014':'Explicit Open Music Theory counterpoint chapter.',
'Q221686':'Explicit Open Music Theory composition lesson.',
'Q3344470':'Explicit Music Theory harmony chapter.',
'Q623939':'Explicit Open Music Theory interval chapter.',
'Q209681':'A moral principle in Kant’s ethics.',
'Q3738092':'Explicitly distinguished form of utilitarianism.',
'Q651440':'Explicitly distinguished form of utilitarianism.',
'Q124058':'Identified as an Islamic practice.',
'Q41831':'Identified as an Islamic declaration.',
'Q35856':'Identified as Christian initiation.',
'Q66086':'Identified as a Christian rite.',
'Q191431':'Explicit Esoteric Buddhist use of mandalas.',
'Q183379':'Explicit Vedanta context for liberation.',
'Q42927':'Explicit Buddhist meaning of nirvana.',
'Q10283':'Identified as Hindu pilgrimage gathering.',
'Q133067':'Explicitly discussed as an art form.',
'Q1164982':'Explicitly identified as Color Field paintings.',
'Q1473346':'Explicitly identified as stained-glass art.',
'Q170571':'Explicitly identified as a painting genre.',
'Q200034':'Painting technique illustrated through Seurat.',
'Q185905':'Explicit ukiyo-e woodblock print production.',
'Q214127':'Explicitly identified as a painting genre.'
}
for p in proposals:
    if p['id'] in ['Q183379','Q42927']:
        p['proposed_parent']['type']='related_to'
    if p['id'] in source_asserted:
        p['proposed_parent']['assertion']='source_asserted'
        p['proposed_parent']['note']=source_asserted[p['id']]
issues=[
{'id':'culture-equivalence-generalization','status':'excluded_unresolved_equivalence','candidate_id':'Q1501867','existing_card_id':'local:catalog:cartographic-generalization','replacement_id':'Q36477','reason':'Matching subject and alias already have a batch-002 local card; the frozen baseline lacks an equivalence redirect. Preserve both identities and the prior card.'},
{'id':'culture-equivalence-woodcut','status':'excluded_unresolved_equivalence','candidate_id':'Q173242','existing_card_id':'local:catalog:woodcut','replacement_id':'Q204330','reason':'Matching subject and alias already have a batch-002 local card; the frozen baseline lacks an equivalence redirect. Preserve both identities and the prior card.'},
{'id':'culture-perspective-access','status':'excluded_source_unresolved','candidate_id':'Q1900281','replacement_id':'Q170571','reason':'Original source and three bounded alternatives produced no inspectable substantive passage. Do not draft the perspective identity.'},
{'id':'culture-equivalence-fresco','status':'excluded_unresolved_equivalence','candidate_id':'Q134194','existing_card_id':'local:catalog:buon-fresco','replacement_id':'Q1473346','reason':'The intended wet-plaster explanation describes the existing local buon-fresco card. Preserve original identities and card; no broader rewording is counted as a new first card.'},
{'id':'culture-equivalence-engraving','status':'excluded_unresolved_equivalence','candidate_id':'Q139106','existing_card_id':'local:catalog:engraving-printmaking','replacement_id':'Q133067','reason':'The intended burin-and-metal-plate explanation duplicates the existing local printmaking engraving card. Preserve the broader QID and local card separately.'},
{'id':'culture-equivalence-etching','status':'excluded_unresolved_equivalence','candidate_id':'Q186986','existing_card_id':'local:catalog:etching-printmaking','replacement_id':'Q1164982','reason':'The intended acid-ground printmaking explanation duplicates the existing local etching card. Preserve both identities without counting a second first card.'},
{'id':'culture-equivalence-puja','status':'excluded_unresolved_equivalence','candidate_id':'Q10937578','existing_card_id':'local:catalog:puja','replacement_id':'Q41831','reason':'The existing local Puja card already explains Hindu deity worship and offerings. Parenthesized label differences do not create a distinct subject.'},
{'id':'culture-equivalence-trompe-alternative','status':'excluded_unresolved_equivalence','candidate_id':'Q468930','existing_card_id':'local:catalog:trompe-loeil','replacement_id':None,'reason':'Discarded during alternative screening: spelling, apostrophe and ligature differences conceal the existing local subject.'},
{'id':'culture-equivalence-watercolor-alternative','status':'excluded_unresolved_equivalence','candidate_id':'local:authored:000365','other_inventory_id':'Q50030','replacement_id':None,'reason':'Discarded alternative: the same watercolor-painting subject has a separate unassigned QID in the baseline. Neither has a prior card; leave identity reconciliation to the coordinator.'},
{'id':'culture-parent-gaps','status':'reported','candidate_ids':['Q182139','Q189849'],'reason':'The inspected place-specific explanations do not establish a close conceptual parent. Leave parent null.'},
{'id':'culture-source-timestamps','status':'reported','reason':'Source inspection was recorded with session clock observations, not individual network timestamps. retrieved_at is explicitly a session checkpoint.'},
{'id':'culture-selection-stage','status':'awaiting_coordinator_reservations','reason':'Selection only: no discovery card text, author acceptance, or operational import is claimed.'}
]

issue_sources={'culture-equivalence-generalization':'esri-generalization','culture-equivalence-woodcut':'nga-printmaking','culture-equivalence-fresco':'met-fresco','culture-equivalence-engraving':'met-engraving','culture-equivalence-etching':'met-etching','culture-equivalence-puja':'harvard-puja','culture-equivalence-watercolor-alternative':'met-gouache'}
for issue in issues:
    if issue['id'] in issue_sources:
        issue['source_ids']=['culture-'+issue_sources[issue['id']]]

# Bounded attempts and unusable extractions remain visible, distinct from successful inspections.
failures=[]
def failure(url,attempts,result,refs=None,replacement=None,note=None):
    f={'url':url,'attempts':attempts,'outcome':result,'inspection_mode':'web_open_or_find','tool_refs':refs or [],'substantive_passage_inspected':False}
    if replacement: f['replacement_source_id']='culture-'+replacement
    if note: f['note']=note
    failures.append(f)
for slug,attempts,ref in [('sonnet',2,'turn564view0/turn566view0'),('haiku',2,'turn564view1/turn566view1'),('irony',2,None),('fable',1,None)]:
    failure('https://www.poetryfoundation.org/education/glossary/'+slug,attempts,'403 or inaccessible',[ref] if ref else [],{'sonnet':'poets-sonnet','haiku':'poets-haiku','irony':'os-irony','fable':'loc-fable'}[slug])
for slug,rep in [('e/etching','met-etching'),('e/engraving','met-engraving'),('w/woodcut','nga-printmaking'),('f/fresco','met-fresco')]:
    failure('https://www.tate.org.uk/art/art-terms/'+slug,1,'403',replacement=rep)
failure('https://smarthistory.org/neo-impressionist-color-theory/',2,'Internal access errors',['turn575view1','turn576view3'],'met-pointillism')
failure('https://smarthistory.org/technique/linear-perspective/',1,'Internal access error',['turn575view2'],note='Original perspective source; identity excluded.')
failure('https://www.nga.gov/sites/default/files/migrate_images/content/dam/ngaweb/education/learning-resources/teaching-packets/pdfs/european-renaissance-art-tp2.pdf',2,'Empty PDF extraction; screenshot cache miss',['turn653view1','turn655view0'],note='Perspective alternative 1; screenshot page 51 failed.')
failure('https://smarthistory.org/linear-perspective-brunelleschis-experiment/',1,'403',['turn657view1'],note='Perspective alternative 2.')
failure('https://smarthistory.org/space/',1,'403',['turn660view0'],note='Perspective alternative 3; stop the unresolved identity.')
failure('https://www.britannica.com/art/genre-painting',1,'Internal access error',replacement='met-genre')
failure('https://www.poets.org/glossary/sonnet',1,'Internal access error',replacement='poets-sonnet')
failure('https://edblogs.columbia.edu/worldepics/project/epic-of-sundiata/',2,'502',['turn566view3','turn590view3'],'yale-sundiata')
failure('https://ich.unesco.org/en/RL/cultural-space-of-sosso-bala-00009',2,'No usable substantive extraction',replacement='yale-sundiata')
failure('https://teachers.yale.edu/curriculum/units/2009/1/7',1,'Inaccessible HTML',['turn590view4'],'yale-sundiata')
failure(None,1,'Guessed ArcGIS geographic-coordinate URL inaccessible',replacement='esri-gcs',note='Exact original URL was not retained; no passage credited.')
failure('https://www.nationalgeographic.org/resource/geography/',1,'404',replacement='iowa-physical')
failure('https://www.si.edu/newsdesk/releases/recent-connection-between-north-and-south-america-reaffirmed',2,'Timeout',['turn594view6','turn599view2'],'smithsonian-panama')
failure('https://www.loc.gov/programs/teachers/getting-started-with-primary-sources/',1,'403',['turn599view3'],'nara-primary')
failure('https://guides.library.cornell.edu/c.php?g=1023249&p=7412733',1,'Internal access error',['turn652view0'],'nara-primary')
failure('https://guides.library.utoronto.ca/HIS-UTML/primary-vs-secondary-sources',1,'Internal access error',['turn653view2'],'nara-primary')
failure('https://www.archives.gov/education/history-in-the-raw',1,'Inaccessible URL',['turn654view0'],'nara-primary',note='Correct NARA education/research URL inspected on the next attempt.')
failure('https://www.archives.gov/about/info/whats-an-archives',2,'Internal access errors',['turn599view5','turn601view2'],'saa-archive')
failure(None,1,'World Archives Association page inaccessible',replacement='saa-archive',note='Exact attempted URL not retained; no passage credited.')
failure('https://www.berliner-mauer-gedenkstaette.de/en/the-berlin-wall-1961-1989-11.html',1,'Internal access error',replacement='berlin-wall')
failure('https://pressbooks.marshall.edu/introductiontoliterature/chapter/key-components-of-short-stories/',1,'403',['turn590view1'],'os-motif')
failure('https://liberalarts.oregonstate.edu/wlf/what-plot',1,'Inaccessible guessed URL',['turn626view3'],'os-plot')
failure('https://viva.pressbooks.pub/openmusictheory/chapter/timbre/',1,'Internal access error',replacement='duke-timbre')
failure('https://viva.pressbooks.pub/openmusictheory/chapter/fugue/',1,'Internal access error',replacement='omt-fugue')
for url,ref,rep in [
('https://constitution.congress.gov/browse/essay/amdt14-S1-3/ALDE_00013743/','turn629view0','cornell-due'),
('https://constitution.congress.gov/browse/essay/artIII-S1-3/ALDE_00013514/','turn629view1','cornell-review'),
('https://constitution.congress.gov/browse/essay/intro-7-1/ALDE_00000028/','turn629view2','cornell-separation'),
('https://constitution.congress.gov/browse/essay/artI-S10-C1-5/ALDE_00001101/','turn629view3','cornell-retro')]: failure(url,1,'403',[ref],rep)
failure('https://www.law.cornell.edu/wex/separation_of_powers',1,'Initial direct open failed; subsequent clicked URL succeeded',replacement='cornell-separation')
failure('https://teara.govt.nz/en/treaty-of-waitangi/page-2',2,'No usable inspection; follow-up find inaccessible',['turn645view0','turn650view0'],'nz-waitangi')
failure('https://ich.unesco.org/doc/src/33484-EN.pdf?t=1459875512',1,'No usable substantive extraction',['turn642view2'],'pib-kumbh')
failure('https://www.incredibleindia.gov.in/en/festivals-and-events/uttarakhand/kumbh-mela',1,'Page opened but no substantive bathing passage was inspected',replacement='pib-kumbh',note='Navigation/page shell is not discovery evidence.')
failure('https://www.metmuseum.org/essays/still-life-painting-in-northern-europe',1,'Guessed URL inaccessible',['turn671view0'],'met-stilllife')

failure('https://www.moma.org/collection/terms/color-field-painting',2,'Term and works index lacks an explanatory passage',['turn707view0','turn708view0'],'moma-colorfield')

used=collections.defaultdict(list)
for p in proposals:
    for e in p['discovery_evidence']: used[e['source_id']].append(p['id'])
for s in by_source.values():
    s['proposed_card_ids']=used[s['id']]
    s['issue_ids']=[i['id'] for i in issues if s['id'] in i.get('source_ids',[])]
    s['status']='substantive_passage_inspected_used' if used[s['id']] else ('substantive_passage_inspected_for_excluded_candidate' if s['issue_ids'] else 'substantive_passage_inspected_unused')
source_items=list(by_source.values())
doc={'schema_version':1,'assignment':'culture','baseline_index_sha256':sha,'proposals':proposals,'issues':issues,'sources_inspected':source_items}
source_doc={'schema_version':1,'assignment':'culture','status':'selection_ready_awaiting_reservations','inspection_session':{'first_clock_observation':'2026-10-09T04:27:54Z','last_inspection_clock_checkpoint':'2026-10-09T04:45:38Z','individual_fetch_timestamps':'not captured'},'sources':source_items,'failed_or_unusable_attempts':failures,'navigation_only_inspections':[{'url':'https://nzhistory.govt.nz/politics/treaty-of-waitangi/translated-versions','tool_ref':'turn652view2','status':'navigation only; not supporting evidence'}]}

# Conservative pre-draft accounting includes all explanatory proposal strings.
# Repeated serialization/checkpoint copies do not create additional distinct prose.
def explanatory_strings(p):
    values=[p['learning_takeaway'],p['identity_reason'],*p['limits']]
    values += [e['support_note'] for e in p['discovery_evidence']]
    if p['proposed_parent']: values.append(p['proposed_parent']['note'])
    return values
budgets=[]
for s in source_items:
    if s.get('budget_group'): continue
    ids=used[s['id']]
    derived=sum(len(v.split()) for p in proposals if p['id'] in ids for v in explanatory_strings(p))
    derived+=sum(len(i['reason'].split()) for i in issues if s['id'] in i.get('source_ids',[]))
    budgets.append({'source_id':s['id'],'url':s['url'],'word_limit':s['word_limit'],'total_derived_words':derived,'card_ids':ids,'counting_basis':'Selection stage: whitespace tokens in takeaways, intended-meaning notes, limits, support notes, relation notes, and source-tagged exclusion reasons. Metadata and duplicate checkpoint/serialization copies excluded. No cards drafted.','reserved_card_words':25*len(ids),'remaining_after_reserved_cards':s['word_limit']-derived-25*len(ids)})
assert all(x['remaining_after_reserved_cards']>=0 for x in budgets), [(x['source_id'],x['total_derived_words']) for x in budgets if x['remaining_after_reserved_cards']<0]

norm=lambda s:' '.join(s.casefold().split())
collisions=[]
for p in proposals:
    for alias in set([p['label'],*p['aliases']]):
        others=[x for x in baseline['aliases'].get(norm(alias),[]) if x!=p['id']]
        if others: collisions.append({'id':p['id'],'alias':alias,'other_ids':others})
assert not collisions,collisions
quotas=dict(collections.Counter(p['primary_domain'] for p in proposals))
assert quotas==eligible_doc['domain_quotas'],(quotas,eligible_doc['domain_quotas'])
counts={'proposals':len(proposals),'domain_counts':quotas,'scope_counts':dict(collections.Counter(p['scope'] for p in proposals)),'entity_kind_counts':dict(collections.Counter(p['entity_kind'] for p in proposals)),'used_source_count':len([s for s in source_items if used[s['id']]]),'inspected_source_count':len(source_items),'failed_or_unusable_url_records':len(failures),'parent_links':sum(p['proposed_parent'] is not None for p in proposals),'exact_normalized_alias_collisions':len(collisions),'source_asserted_parent_links':sum(bool(p['proposed_parent'] and p['proposed_parent']['assertion']=='source_asserted') for p in proposals),'fine_scope_count':sum(p['scope'] in ['idea','facet_or_application'] for p in proposals),'fine_scope_source_asserted_links':sum(bool(p['proposed_parent'] and p['proposed_parent']['assertion']=='source_asserted') for p in proposals if p['scope'] in ['idea','facet_or_application'])}
checks={'schema_version':1,'assignment':'culture','status':'selection_ready_awaiting_reservations','baseline_index_sha256':sha,'checks':{'unique_ids':len({p['id'] for p in proposals})==65,'eligible_only':all(p['id'] in eligible for p in proposals),'no_existing_candidate_cards':all(not baseline['concepts'][p['id']].get('candidate_records') for p in proposals),'quotas_match':quotas==eligible_doc['domain_quotas'],'all_four_scopes':len(counts['scope_counts'])==4,'at_least_two_broad_fields':counts['scope_counts'].get('broad_field',0)>=2,'relation_targets_exist':all(not p['proposed_parent'] or p['proposed_parent']['target_id'] in baseline['concepts'] for p in proposals),'source_budgets_fit_with_25_words_reserved_per_card':True,'no_exact_alias_collisions':not collisions,'no_card_bodies_drafted':all('card' not in p for p in proposals)},'counts':counts}
for name,value in [('proposals.json',doc),('sources-inspected.json',source_doc),('source-word-budgets.json',{'schema_version':1,'stage':'selection_only','budgets':budgets}),('selection-checks.json',checks)]:
    (HERE/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
checkpoint={'schema_version':1,'status':'selection_ready_awaiting_reservations_not_drafted','baseline_index_sha256':sha,'checkpoint_observed_at':'2026-10-09T04:45:38Z','provisional_identities':[{'id':p['id'],'label':p['label'],'domains':[p['primary_domain']],'source_status':'substantive_passage_inspected'} for p in proposals],'excluded_candidates':[i for i in issues if i['status'].startswith('excluded')]}
(HERE/'selection-checkpoint.json').write_text(json.dumps(checkpoint,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(counts,indent=2))
print('maximum current derived words:',max(x['total_derived_words'] for x in budgets))
print('minimum remaining after reserved cards:',min(x['remaining_after_reserved_cards'] for x in budgets))
