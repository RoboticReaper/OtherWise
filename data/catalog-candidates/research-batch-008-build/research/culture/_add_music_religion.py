"""Manually researched music and religion cards; local assembly only."""
from datetime import datetime, timezone
from _draft_tools import HERE, read, write, assemble

sources = read(HERE / 'draft-sources-inspected.json')
now = datetime.now(timezone.utc).isoformat()
new_sources = [
    dict(id='culture-fhl-kundiman', title='More than a Love Song',
         url='https://www.filipinaslibrary.org.ph/himig/more-than-a-love-song/',
         locator='Felipe M. De Leon Jr. essay adaptation, lines 68–78', revision=None,
         passage_notes=['Attributed discussion of devotional subjects, triple meter, melodic syncopation and flexible tempo.']),
    dict(id='culture-mto-tenzer', title='Theory and Analysis of Melody in Balinese Gamelan',
         url='https://mtosmt.org/issues/mto.00.6.2/mto.6.2.tenzer_essay.html',
         locator='Michael S. Tenzer, paragraphs 1.1 and 2.1–2.2, lines 31–32, 65–70',
         revision='Music Theory Online 6(2), May 2000',
         passage_notes=['Court and gong kebyar ensembles; stratified melody; interlocking pairs produce rapid, continuous composite melodic parts.'])
]
for s in new_sources:
    s.update(inspected_at=now, inspection_mode='web.open_text', acquisition=dict(
        local_inspection_completed_at=now,remote_retrieval_timestamp=None,
        time_basis='Local clock after actual passage inspection; exact remote retrieval time unavailable'))
    sources = [old for old in sources if old['id'] != s['id']] + [s]
actual_titles = {
    'gugak-pansori-sugungga': "코로나19 극복을 위한 국악 영상 콘서트 '일일국악': 수궁가(영문 자막)[2020.03.25.] - 01. 수궁가",
    'pluralism-koan':'koan', 'pluralism-shikantaza':'shikantaza', 'pluralism-dhikr':'dhikr',
    'bca-nembutsu':'Visit Our Temple'
}
for s in sources:
    if s['id'] in actual_titles: s['title'] = actual_titles[s['id']]
write(HERE / 'draft-sources-inspected.json',sources)

drafts = read(HERE / 'draft-cards.json')
cards = {
 'local:authored:000211': dict(
    body='Gamelan encompasses ensemble music traditions with differing repertoires and settings. In Bali, gong kebyar uses rapidly changing tempi and interlocking parts; older ceremonial styles documented among Balinese communities in Lombok sound comparatively static. Comparing these settings reveals variation within the same musical tradition.',
    takeaway='Compare repertoire and performance setting within gamelan.',
    parent_note='The article examines contrasting gamelan musical repertoires.',
    additional_evidence=[dict(source_id='culture-mto-tenzer',locator='Paragraphs 1.1 and 2.1–2.2, lines 31–32, 65–70',note='Balinese ensemble and layered melodic context inspected.')],
    limits=['The examples concern Balinese traditions, not every gamelan repertoire.']),
 'local:catalog:gamelan-gong-kebyar': dict(
    body='Gamelan gong kebyar is a Balinese ensemble style that emerged in northern Bali around 1915. Rapid tempo changes and dynamic interlocking parts distinguish its repertoire. An album labeled court music illustrates a contextual trap: most documented performances belonged to other settings.',
    takeaway='Hear musical dynamics while checking performance context.',
    parent_note='Gong kebyar is identified as a gamelan style.'),
 'local:catalog:kotekan': dict(
    body='Kotekan is an interlocking technique in Balinese gamelan. Two musicians divide rapid melodic figures into separate parts whose combination maintains rhythmic continuity. The result belongs to the composition’s melody: listening to either player alone misses the continuous composite line.',
    takeaway='Hear the composite melody across paired parts.',
    source_id='culture-mto-tenzer',locator='Paragraph 2.2, lines 67–70',
    parent_source_id='culture-mto-tenzer',parent_note='Tenzer identifies kotekan within Balinese gamelan texture.'),
 'local:catalog:pansori': dict(
    body='Pansori is a Korean narrative vocal genre performed by one singer and one drummer. The singer develops an epic story through poetic, dramatic and musical expression. Sugungga illustrates how this small performing partnership can carry an extended tale with multiple characters.',
    takeaway='Trace narrative performance through singer and drummer.',
    parent_note='The program identifies pansori as a Korean vocal genre.'),
 'local:catalog:sugungga': dict(
    body='Sugungga, the Tale of the Hare, is a surviving pansori story. A tortoise lures a hare to a sick Dragon King who wants its liver. The hare escapes by claiming the organ remains in the forest, turning verbal ingenuity against royal power.',
    takeaway='Follow the hare’s verbal reversal of royal power.',
    parent_note='Sugungga is explicitly listed among surviving pansori stories.'),
 'local:catalog:kulintang-music': dict(
    body='Kulintang is a gong chime music tradition of the Philippines. The Kulintang Kultura album contrasts traditional ensemble repertoire with diaspora musicians’ combinations of kulintang and electronic, hip hop, rock and jazz styles. Hearing both reveals preservation through changing musical arrangements.',
    takeaway='Compare traditional repertoire with diaspora adaptations.',
    parent_note='The lesson identifies kulintang as Philippine gong chime music.',
    additional_evidence=[dict(source_id='folkways-kulintang-kultura',locator='Album description, lines 456–457',note='Traditional and contemporary repertoire comparison inspected.')]),
 'local:catalog:kulintang-kultura': dict(
    body='Kulintang Kultura honors musician and teacher Danongan Kalanduyan through two contrasting discs. His ensemble performs traditional Philippine gong music on the first; diaspora artists combine kulintang with contemporary genres on the second. Their juxtaposition makes musical inheritance and transformation audible within one collection.',
    takeaway='Compare inheritance and transformation across the album’s discs.',
    parent_note='The album documents traditional and diaspora kulintang music.'),
 'local:catalog:kundiman': dict(
    body='Kundiman is a Filipino song form in triple meter. In Felipe De Leon’s account, flowing melodies and subtle second beat syncopation loosen the beat’s pull. Devotion can address a partner, family, spiritual figure or motherland, extending the form beyond romantic love.',
    takeaway='Connect triple meter and melodic flow with devotion.',
    source_id='culture-fhl-kundiman',locator='Essay adaptation, lines 68–78',
    parent_source_id='culture-fhl-kundiman',parent_note='The essay identifies kundiman as a musical form.',
    limits=['Musical and cultural interpretation is attributed to De Leon’s account.']),
 'local:catalog:pinpeat': dict(
    body='Pinpeat is Cambodia’s court music tradition. Smithsonian’s diaspora lesson asks how Cambodian American artists sustain and transform it in the United States. Studying both settings shows how cultural preservation can include adaptation as musicians encounter new social contexts.',
    takeaway='Compare preservation and adaptation across community settings.',
    parent_note='The lesson identifies pinpeat as Cambodian court music.',
    limits=['The inspected introduction does not establish a detailed instrument inventory.']),
 'local:catalog:koan': dict(
    body='A koan is a paradoxical question that a Zen teacher gives a student for meditation. Its purpose is to interrupt habitual analytical thinking rather than supply an ordinary explanatory answer. The tradition treats this encounter as a possible route toward realization.',
    takeaway='Distinguish a contemplative question from an explanatory answer.',
    parent_note='Zen meditation context motivates this Buddhist practice placement.'),
 'local:catalog:shikantaza': dict(
    body='Shikantaza is the just sitting approach associated with Japanese Soto Zen. In this account, sitting properly in zazen is itself the right state of mind, rather than merely preparation for later enlightenment. The posture expresses realization within the tradition’s understanding.',
    takeaway='Understand sitting as realization within Soto practice.',
    parent_note='The definition presents shikantaza as an approach within zazen.'),
 'local:catalog:dhikr': dict(
    body='Dhikr is devotional remembrance in Sufism, often performed through rhythmic recitation of God’s names or litanies. Some forms include poetry, dance or instruments. The repeated vocal pattern organizes worship, while the varying accompaniments show that remembrance has several forms of expression.',
    takeaway='Recognize repeated remembrance across varied devotional forms.',
    parent_note='The definition explicitly identifies dhikr as Sufi devotion.'),
 'local:catalog:ignatian-examen': dict(
    body='The Ignatian Examen is Christian prayer through reflection on daily experience. One adapted sequence begins with awareness of God, reviews gratitude and emotions, then prays over one feature of the day and looks toward tomorrow. Ordinary events become material for discernment.',
    takeaway='Use daily events as material for reflective prayer.',
    parent_note='The source describes an adapted Christian prayer method.'),
 'local:catalog:tashlich': dict(
    body='Tashlich is a Rosh Hashanah custom of prayer beside water and symbolic casting away of sins. Chabad’s account describes shaking garment corners as part of that symbolism. It distinguishes this ritual action from feeding fish, which is not the custom’s essential act.',
    takeaway='Distinguish ritual symbolism from feeding fish.',
    parent_note='The article identifies Tashlich as a Rosh Hashanah custom.'),
 'local:catalog:taize-meditative-singing': dict(
    body='Taizé meditative singing uses short songs whose few words express faith. Repetition supports shared Christian prayer without requiring a precisely fixed duration. The community recommends learning songs beforehand so attention during prayer can rest on listening and contemplation rather than instruction.',
    takeaway='Connect repetition and preparation with shared prayer.',
    parent_note='Christian worship context motivates this prayer practice placement.'),
 'local:catalog:chod': dict(
    body='Chöd is a Buddhist offering practice directed at cutting self clinging. In Lama Zopa’s teaching, ritual offerings of the body to spirits are connected with examining the apparently inherent self. Fear becomes an occasion to investigate that self’s supposed independent existence.',
    takeaway='Connect offering practice with investigation of self clinging.',
    parent_note='The teaching situates chöd within Buddhist charity and wisdom.',
    limits=['Spirits, offerings and liberation are described as this teacher’s ritual and doctrinal account.']),
 'local:catalog:nembutsu': dict(
    body='Nembutsu is a Buddhist chanting practice. At the Buddhist Temple of Marin, a Jodo Shinshu community, chanting Namo Amida Butsu expresses gratitude. The temple places this chant alongside listening and compassionate living, illustrating a devotional function within one specific Buddhist tradition.',
    takeaway='Recognize gratitude as the chant’s described devotional function.',
    parent_note='The temple identifies Nembutsu within its Buddhist practices.',
    limits=['The inspected Jodo Shinshu temple account does not describe every nembutsu interpretation.'])
}
for cid,c in cards.items():
    assert 30 <= len(c['body'].split()) <= 50, (cid,len(c['body'].split()))
drafts.update(cards)
write(HERE / 'draft-cards.json', drafts)

access = read(HERE / 'draft-source-access-limits.json') if (HERE / 'draft-source-access-limits.json').exists() else []
failures = [
 ('https://slides.com/smithsonianfolkways/asian-pacific-american-music-08-notes/fullscreen?token=9LgeQAjU',2,'Cache miss; both lesson slide links resolve to this URL.','Accessible Folkways lesson introduction retained; detailed slide claims omitted.'),
 ('https://ncca.gov.ph/about-ncca-3/subcommissions/subcommission-on-the-arts-sca/music/art-music-form/',2,'HTTP 502 after bounded retries.','Filipinas Heritage Library’s inspected essay adaptation used.'),
 ('https://ncca.gov.ph/about-culture-and-arts/in-focus/constructing-a-national-identity-through-music/',2,'HTTP 502 after bounded retries.','Filipinas Heritage Library’s inspected essay adaptation used.'),
 ('https://folkways-media.si.edu/docs/folkways/artwork/UNES08011.pdf',2,'Internal retrieval errors.','Pinpeat card limited to inspected lesson introduction.'),
 ('https://gamelan.org.nz/wp-content/uploads/2015/02/Kotekan-article-Balungan.pdf',1,'Timeout.','Tenzer’s inspected scholarly analysis supplies the interlocking mechanism.'),
 ('https://www.gamelan.org/balungan/back_issues/balungan4(2).pdf',1,'URL inaccessible via retrieval tool.','Tenzer’s inspected scholarly analysis used.'),
 ('https://gamelan.org/library/writings/susiloessay.html',2,'First HTTP 404, then internal retrieval error.','Balinese examples grounded in inspected Folkways and Tenzer passages.')
]
for url,attempts,error,disposition in failures:
    if not any(x.get('url')==url for x in access):
        access.append(dict(url=url,attempts=attempts,error=error,disposition=disposition,local_recorded_at=now,claim_support=False))
write(HERE / 'draft-source-access-limits.json', access)
assemble()
