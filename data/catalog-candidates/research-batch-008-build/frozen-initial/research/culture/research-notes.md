# Culture shard author handoff — research batch 008

Status: draft ready for independent source audit. The author completed the 70 approved cards and reviews; the coordinator owns freezing, sampling and acceptance. No operational catalog import was performed.

Validated counts: 70 cards, 64 new identities, 6 existing controls, 55 new fine-scope subjects and 11 named subjects. Every body has 30–50 whitespace-separated English words. All four scopes are represented. The named-subject goal is measured, not a reason to invent identities.

Among 57 fine-scope cards, 55 have a supported parent/application edge and 49 have one marked source_asserted. Source assertions cite an actual relationship; editorial historical or learning placements remain marked editorial.

| Primary domain | Cards |
| --- | ---: |
| Geography & travel | 9 |
| Literature & storytelling | 9 |
| Philosophy | 9 |
| Politics & law | 9 |
| Music & performance | 9 |
| History & culture | 9 |
| Visual arts & design | 8 |
| Religion & spirituality | 8 |

| Scope | Cards |
| --- | ---: |
| broad_field | 1 |
| idea | 23 |
| topic | 12 |
| facet_or_application | 34 |

## Inputs and validation

- Global approved selection SHA256: `5e15d76acee1c29775a9b7b003f7d01447e494974da200c9c15afa3a25f5df9d`.
- Baseline index SHA256: `e3cd8ebac67579be75742df0bf2f5b2e7781293282345d2286aff205416e0fe2`.
- Shard approved-selection SHA256: `45bf9093df1bd4e5586e0a7b6209ab97f669ae137161af90dfe9336efc38fbfb`.
- Final candidate SHA256: `22a1080ca727c718605ac21aa8305b0d4614820b52e1d1d44481e4ea0c89b403`.
- [Local check report](/Users/baorenliu/Documents/Programming/Python/ProductSpace/data/catalog-candidates/research-batch-008-build/research/culture/draft-validation.json) verifies the stock adapter validator, pinned hashes, all approved identities and versions, 70 reviews, source and target resolution, exact and punctuation/diacritic alias intersections, domain counts, control provenance and per-source allocations.
- [Author review](/Users/baorenliu/Documents/Programming/Python/ProductSpace/data/catalog-candidates/research-batch-008-build/research/culture/author-review.json) contains outcomes, inspected locators, card versions and limits for every ID. Independent audit status remains pending.

Existing controls retain canonical labels and IDs, exact original descriptions, every baseline raw inventory row, all prior full card records and checked source-bundle hashes. Version selection is approved maximum plus one; new subjects use version 1. Local raw source pointers remain inside the preserved imported rows, while identity_urls contains HTTP(S) references.

## Source and coverage limits

54 public source records have actual titles and valid acquisition timestamps. Each timestamp is explicitly the local clock after passage inspection; the exact remote retrieval instant is unavailable. Stored inspection metadata remains in [draft-sources-inspected.json](/Users/baorenliu/Documents/Programming/Python/ProductSpace/data/catalog-candidates/research-batch-008-build/research/culture/draft-sources-inspected.json), with pointers from the candidate.

Cumulative new body, takeaway, evidence-note and relation-note prose stays within each 200-word source allocation. Bibliographic titles and locators, and unchanged archival prior records, are excluded from that count. The three largest allocations are Fricker’s Introduction (190), the Vienna Convention (185), and the Met portfolio article (182). Poetry forms use several distinct educational sources; the shared Poetry Archive form page supports only ottava rima in the final candidate.

Pinpeat has an evidence-limited definition and a lesson-based comparative takeaway. The accessible introduction supports its selected boundaries; detailed slide and instrument claims were omitted. Religious practice cards preserve tradition-specific or teacher-specific interpretations. Law cards retain instrument, jurisdiction and edition limits. Named artifacts identify the specific work or object rather than a general category.

Actual access outcomes are recorded in [selection limits](/Users/baorenliu/Documents/Programming/Python/ProductSpace/data/catalog-candidates/research-batch-008-build/research/culture/source-access-limits.json) and [drafting limits](/Users/baorenliu/Documents/Programming/Python/ProductSpace/data/catalog-candidates/research-batch-008-build/research/culture/draft-source-access-limits.json). UNESCO ICH CAPTCHA, UNHCR HTTP 429, failed PDFs/slides, NCCA HTTP 502, Poetry Foundation HTTP 403 and unavailable Word Ways/Gamelan routes did not become claim support. Exact failed URLs were not retained for two resumed source-family records, which is stated explicitly. Accessible alternatives carry their own inspected citations.

Satori, Arashi shibori and Spenserian stanza remain excluded alternatives. No substitutions or new identities were added after approval. Token and cost usage are unavailable to this researcher.

## Explicit category gaps

- `Q1071` (Geography): Broad-field control; no higher field asserted.
- `Q603959` (Proportionality (law)): The inspected European rights example does not establish a universal parent for the general legal principle.
- `local:catalog:khipu` (Khipu): The source establishes Inca use of khipus; this setting is retained as related_to rather than made a universal category parent.
- `local:catalog:lukasa-met-1977-467-3` (Lukasa memory board (Met 1977.467.3)): Individual artifact retained; a generic Lukasa parent is absent from approved and baseline targets.

Khipu retains the documented Inca setting as related_to. The six projection methods remain idea. Both buffering methods retain source_asserted facet_of links to geographic-buffer; the ambiguous bare Planar buffering alias is absent. The Itoh garment uses the corrected Met URL ending in 79595.

## Inspected references by card

The locators below apply to the emitted body and its attached relationships. Full source metadata and historical control reference bundles are in the candidate. Version and body word count are separate from the title and references.

| Subject and ID | Words / version | Inspected passages | Attached relationship |
| --- | ---: | --- | --- |
| Geography (`Q1071`) | 41 / v1 | [What is geography?](https://www.rgs.org/about-us/what-is-geography) — Main text, paragraphs 1–3; “Geography informs us about”; human/physical geography paragraph | Explicit gap |
| Sestina (`Q1334127`) | 42 / v2 | [Sestina](https://poets.org/glossary/sestina) — “Rules of the Sestina Form”; final history paragraphs describing double sestina and tritina | broader_topic → Poetry (`local:authored:000404`), source_asserted |
| Epistemic injustice (`Q48970669`) | 42 / v2 | [Introduction](https://www.mirandafricker.com/uploads/1/3/6/2/136236203/introduction.pdf) — Printed page 1, opening definitions and examples | broader_topic → Epistemology (`local:authored:000430`), editorial |
| Proportionality (law) (`Q603959`) | 41 / v1 | [Guide on Article 8 of the European Convention on Human Rights: Right to respect for private and family life, home and correspondence](https://ks.echr.coe.int/documents/d/echr-ks/guide_art_8_eng) — Is the interference necessary in a democratic society?, paragraphs 34–36, printed pages 15–16 | Explicit gap |
| Gamelan (`local:authored:000211`) | 43 / v1 | [UNESCO Collection Week 34: Balinese Court Music](https://folkways.si.edu/news-and-press/unesco-collection-week-34-balinese-court-music) — David Harnish’s guest article, lines 450–468<br>[Theory and Analysis of Melody in Balinese Gamelan](https://mtosmt.org/issues/mto.00.6.2/mto.6.2.tenzer_essay.html) — Paragraphs 1.1 and 2.1–2.2, lines 31–32, 65–70 | broader_topic → Music (`Q638`), source_asserted |
| Acrostic (`local:catalog:acrostic`) | 41 / v1 | [Acrostic](https://poets.org/glossary/acrostic) — Definition and Blake example, lines 28–37 | broader_topic → Poetry (`local:authored:000404`), source_asserted |
| Adams square II projection (`local:catalog:adams-square-ii-projection`) | 43 / v1 | [Adams square II \| ArcGIS Pro documentation](https://doc.esri.com/en/arcgis-pro/latest/help/mapping/properties/adams-square-ii.html) — Description; Graticule; Distortion; Usage | broader_topic → Map projection (`Q186386`), source_asserted |
| Cento (`local:catalog:cento`) | 42 / v1 | [Cento](https://poets.org/glossary/cento) — Definition; “More about the Cento Form” | broader_topic → Poetry (`local:authored:000404`), source_asserted |
| Chaski (Inca messenger) (`local:catalog:chaski`) | 43 / v1 | [Standardizing an Empire](https://www.nist.gov/nist-museum/standardizing-empire) — Khipu Uses, lines 195–196 | facet_of → Inca Empire (`Q28573`), editorial |
| Chine collé (`local:catalog:chine-colle`) | 42 / v1 | [L'Estampe Originale: A Rare Print Portfolio Now Online](https://www.metmuseum.org/de/perspectives/lestampe-originale) — Curatorial article, lines 44–45 | application_of → Printmaking (`local:authored:000351`), source_asserted |
| Chöd (`local:catalog:chod`) | 41 / v1 | [Chöd: Slaying the Ego](https://www.lamayeshe.com/article/chapter/ch%C3%B6d-slaying-ego) — Lama Zopa Rinpoche’s teaching, lines 43–52, 101–104 | application_of → Buddhism (`local:authored:000460`), source_asserted |
| Civilian Public Service (US, World War II) (`local:catalog:civilian-public-service`) | 44 / v1 | [Patapsco Camp (WWII Civilian Public Service Site)](https://home.nps.gov/places/patapsco-camp-wwii-civilian-public-service-site.htm) — Civilian Public Service; In Camp; Challenges, lines 44–59 | application_of → Pacifism (`Q58848`), editorial |
| Clerihew (`local:catalog:clerihew`) | 38 / v1 | [Clerihew](https://poets.org/glossary/Clerihew) — Definition and From A Poet’s Glossary, lines 28–33 | broader_topic → Poetry (`local:authored:000404`), source_asserted |
| Contributory injustice (`local:catalog:contributory-injustice`) | 42 / v1 | [Feminist Social Epistemology](https://plato.stanford.edu/entries/feminist-social-epistemology/) — §4.1 Epistemic Injustice, Dotson and Pohlhaus paragraphs, lines 225–228 | facet_of → Epistemic injustice (`Q48970669`), source_asserted |
| Dhikr (`local:catalog:dhikr`) | 41 / v1 | [dhikr](https://pluralism.org/dhikr) — Definition, line 56 | facet_of → Sufism (`local:authored:000466`), source_asserted |
| Double dactyl (`local:catalog:double-dactyl`) | 41 / v1 | [double dactyl](https://home.uncg.edu/~htkirbys/ast54.htm) — Opening instructional paragraphs, lines 0–3<br>[Glossary of Poetic Terms](https://poets.org/glossary) — Dactyl entry, line 94 | broader_topic → Poetry (`local:authored:000404`), source_asserted |
| Margin of appreciation (European human-rights law) (`local:catalog:echr-margin-of-appreciation`) | 43 / v1 | [Guide on Article 8 of the European Convention on Human Rights: Right to respect for private and family life, home and correspondence](https://ks.echr.coe.int/documents/d/echr-ks/guide_art_8_eng) — Is the interference necessary in a democratic society?, paragraphs 34–36, printed pages 15–16 | application_of → European Convention on Human Rights (`Q183191`), source_asserted |
| Pilot judgment procedure (European Court of Human Rights) (`local:catalog:echr-pilot-judgment-procedure`) | 42 / v1 | [Factsheet – Pilot judgments](https://www.echr.coe.int/documents/d/echr/FS_Pilot_judgments_ENG) — What is the pilot judgment procedure?, printed page 1, lines 4–18 | application_of → European Convention on Human Rights (`Q183191`), source_asserted |
| Equal Earth projection (`local:catalog:equal-earth-projection`) | 37 / v1 | [Equal Earth \| ArcGIS Pro documentation](https://doc.esri.com/en/arcgis-pro/latest/help/mapping/properties/equal-earth.html) — Description; Distortion; Usage | broader_topic → Map projection (`Q186386`), source_asserted |
| Euclidean buffering (`local:catalog:euclidean-buffering`) | 42 / v1 | [How Buffer (Analysis) works](https://doc.esri.com/en/arcgis-pro/latest/tool-reference/analysis/how-buffer-analysis-works.html) — “Euclidean and geodesic buffering”, method bullets and shape-preserving Geodesic option | facet_of → Geographic buffer (`local:catalog:geographic-buffer`), source_asserted |
| Fitting-attitude theories of value (`local:catalog:fitting-attitude-theories-of-value`) | 44 / v1 | [Fitting Attitude Theories of Value](https://plato.stanford.edu/entries/fitting-attitude-theories/) — Introduction, lines 13–20 | broader_topic → Value theory (`Q186531`), source_asserted |
| Gamelan gong kebyar (`local:catalog:gamelan-gong-kebyar`) | 41 / v1 | [UNESCO Collection Week 34: Balinese Court Music](https://folkways.si.edu/news-and-press/unesco-collection-week-34-balinese-court-music) — David Harnish’s guest article, lines 450–468 | facet_of → Gamelan (`local:authored:000211`), source_asserted |
| Geodesic buffering (`local:catalog:geodesic-buffering`) | 43 / v1 | [How Buffer (Analysis) works](https://doc.esri.com/en/arcgis-pro/latest/tool-reference/analysis/how-buffer-analysis-works.html) — “Euclidean and geodesic buffering”, method bullets and shape-preserving Geodesic option | facet_of → Geographic buffer (`local:catalog:geographic-buffer`), source_asserted |
| Goode homolosine projection (`local:catalog:goode-homolosine-projection`) | 41 / v1 | [Goode homolosine \| ArcGIS Pro documentation](https://doc.esri.com/en/arcgis-pro/latest/help/mapping/properties/goode-homolosine.html) — Description; Graticule; Usage; Limitations | broader_topic → Map projection (`Q186386`), source_asserted |
| Gyotaku (`local:catalog:gyotaku`) | 44 / v1 | [Educational Uses of Gyotaku or Fish Printing](https://ocean.si.edu/conservation/get-involved/educational-uses-gyotaku-or-fish-printing) — Catherine Sutera’s museum account, lines 65–69 | application_of → Printmaking (`local:authored:000351`), editorial |
| Haibun (`local:catalog:haibun`) | 43 / v1 | [Haibun](https://poets.org/glossary/haibun) — Definition; “From A Poet’s Glossary”, prose–haiku relationship | broader_topic → Poetry (`local:authored:000404`), source_asserted |
| Hermeneutical injustice (`local:catalog:hermeneutical-injustice`) | 43 / v1 | [Introduction](https://www.mirandafricker.com/uploads/1/3/6/2/136236203/introduction.pdf) — Printed page 1, hermeneutical-injustice definition and harassment example | facet_of → Epistemic injustice (`Q48970669`), source_asserted |
| Hotine oblique Mercator projection (`local:catalog:hotine-oblique-mercator-projection`) | 42 / v1 | [Hotine oblique Mercator \| ArcGIS Pro documentation](https://doc.esri.com/en/arcgis-pro/latest/help/mapping/properties/hotine-oblique-mercator.html) — Description; Distortion; Usage; Variants | broader_topic → Map projection (`Q186386`), source_asserted |
| Complementarity (International Criminal Court) (`local:catalog:icc-complementarity`) | 41 / v1 | [Rome Statute of the International Criminal Court](https://legal.un.org/icc/statute/99_corr/cstatute.htm) — Preamble, Article 1, Article 17 (lines 18, 25, 244–258) | facet_of → International Criminal Court (`Q47488`), source_asserted |
| Ignatian Examen (`local:catalog:ignatian-examen`) | 41 / v1 | [The Daily Examen](https://www.ignatianspirituality.com/ignatian-prayer/the-examen/) — Main explanation and five-step method, lines 85–98 | facet_of → Christian prayer (`Q3627146`), source_asserted |
| Tokuseu Hitome Sohshibori Hon Furisode (Met 1997.228) (`local:catalog:itoh-furisode-met-1997-228`) | 41 / v1 | [Tokuseu Hitome Sohshibori Hon Furisode](https://www.metmuseum.org/art/collection/search/79595) — Curatorial description, lines 10–12; object identification, 31–39 | application_of → Shibori (`local:catalog:shibori`), source_asserted |
| Jus cogens (`local:catalog:jus-cogens`) | 39 / v1 | [Vienna Convention on the Law of Treaties (1969)](https://legal.un.org/ilc/texts/instruments/english/conventions/1_1_1969.pdf) — Article 53, printed page 17 | broader_topic → International law (`Q4394526`), source_asserted |
| Kanoko shibori (`local:catalog:kanoko-shibori`) | 41 / v1 | [Robe (Kosode) with Pines and Interlocking Squares](https://www.metmuseum.org/art/collection/search/45399) — Curatorial description, lines 10–11; Artwork Details | facet_of → Shibori (`local:catalog:shibori`), source_asserted |
| Khipu (`local:catalog:khipu`) | 45 / v2 | [Standardizing an Empire](https://www.nist.gov/nist-museum/standardizing-empire) — What is a khipu?; Encoding the Khipu; Khipu Uses, lines 132–157 and 195 | related_to → Inca Empire (`Q28573`), source_asserted |
| Kintsugi (`local:catalog:kintsugi`) | 43 / v1 | [The Infinite Artistry of Japanese Ceramics](https://www.metmuseum.org/ja/exhibitions/the-infinite-artistry-of-japanese-ceramics) — Exhibition overview, lines 10–11 | application_of → Ceramic art (`Q13464614`), source_asserted |
| Koan (`local:catalog:koan`) | 41 / v1 | [koan](https://pluralism.org/koan) — Definition, line 56 | application_of → Buddhism (`local:authored:000460`), editorial |
| Kotekan (`local:catalog:kotekan`) | 39 / v1 | [Theory and Analysis of Melody in Balinese Gamelan](https://mtosmt.org/issues/mto.00.6.2/mto.6.2.tenzer_essay.html) — Paragraph 2.2, lines 67–70 | application_of → Gamelan (`local:authored:000211`), source_asserted |
| Kulintang Kultura: Danongan Kalanduyan and Gong Music of the Philippine Diaspora (`local:catalog:kulintang-kultura`) | 43 / v1 | [Kulintang Kultura: Danongan Kalanduyan and Gong Music of the Philippine Diaspora](https://folkways.si.edu/kulintang-kultura) — Album description, lines 456–457; Release Info, 505–513 | application_of → Kulintang music (`local:catalog:kulintang-music`), source_asserted |
| Kulintang music (`local:catalog:kulintang-music`) | 40 / v1 | [Cultural Preservation and Adaptation: Kulintang, Kundiman, and Pinpeat in the US](https://folkways.si.edu/lesson/cultural-preservation-and-adaptation/kundiman-pinpeat-in-US) — Lesson introduction and learning objectives, lines 440–455<br>[Kulintang Kultura: Danongan Kalanduyan and Gong Music of the Philippine Diaspora](https://folkways.si.edu/kulintang-kultura) — Album description, lines 456–457 | broader_topic → Music (`Q638`), source_asserted |
| Kundiman (`local:catalog:kundiman`) | 41 / v1 | [More than a Love Song](https://www.filipinaslibrary.org.ph/himig/more-than-a-love-song/) — Essay adaptation, lines 68–78 | broader_topic → Music (`Q638`), source_asserted |
| L’Estampe Originale (`local:catalog:lestampe-originale`) | 39 / v1 | [L'Estampe Originale: A Rare Print Portfolio Now Online](https://www.metmuseum.org/de/perspectives/lestampe-originale) — Curatorial article, lines 13–16, 22, 31–38 | application_of → Printmaking (`local:authored:000351`), source_asserted |
| Lukasa memory board (Met 1977.467.3) (`local:catalog:lukasa-met-1977-467-3`) | 44 / v1 | [Lukasa (Memory Board)](https://www.metmuseum.org/art/collection/search/690570) — Curatorial description, lines 10–16; Artwork Details, object number 1977.467.3 | Explicit gap |
| Mbudye association (`local:catalog:mbudye-association`) | 44 / v1 | [Lukasa (Memory Board)](https://www.metmuseum.org/art/collection/search/690570) — Curatorial description, lines 12–14 | broader_topic → Luba Empire (`Q1768252`), editorial |
| Metaphysical grounding (`local:catalog:metaphysical-grounding`) | 42 / v1 | [Metaphysical Grounding](https://plato.stanford.edu/entries/grounding/) — Introduction, lines 13–18; §1.1 Determination and explanation | broader_topic → Metaphysics (`local:authored:000431`), source_asserted |
| Natural Earth projection (`local:catalog:natural-earth-projection`) | 40 / v1 | [Natural Earth \| ArcGIS Pro documentation](https://doc.esri.com/en/arcgis-pro/latest/help/mapping/properties/natural-earth.html) — Description; Distortion; Limitations | broader_topic → Map projection (`Q186386`), source_asserted |
| The Negro Motorist Green Book (`local:catalog:negro-motorist-green-book`) | 43 / v1 | [Green Book Properties Listed in the National Register of Historic Places](https://www.nps.gov/articles/green-book-properties-listed-in-the-national-register-of-historic-places.htm) — Publication and directory history, lines 24–35 | broader_topic → Racial segregation in the United States (`Q2652357`), editorial |
| Nembutsu (`local:catalog:nembutsu`) | 41 / v1 | [Visit Our Temple](https://www.buddhistchurchesofamerica.org/temple/visit/buddhist-temple-of-marin) — Tradition statement and practices, lines 118, 145–165 | application_of → Buddhism (`local:authored:000460`), source_asserted |
| Non-refoulement (`local:catalog:non-refoulement`) | 40 / v1 | [UNHCR Note on the Principle of Non-Refoulement](https://www.refworld.org/policy/legalguidance/unhcr/1997/en/36258) — Legal basis, Beneficiaries and Exceptions, lines 44–79, 107–120 | broader_topic → International law (`Q4394526`), source_asserted |
| Ottava rima (`local:catalog:ottava-rima`) | 37 / v1 | [Form](https://poetryarchive.org/glossary/form/) — “About Form”; CLERIHEW; DOUBLE-DACTYL; OTTAVA RIMA; SPENSERIAN STANZA | broader_topic → Poetry (`local:authored:000404`), source_asserted |
| Pacta sunt servanda (`local:catalog:pacta-sunt-servanda`) | 34 / v1 | [Vienna Convention on the Law of Treaties (1969)](https://legal.un.org/ilc/texts/instruments/english/conventions/1_1_1969.pdf) — Article 26, printed page 10 | facet_of → Treaty (`Q131569`), source_asserted |
| Safe Conduct Pass in Phakpa script (Met 1993.256) (`local:catalog:paiza-met-1993-256`) | 43 / v1 | [Safe Conduct Pass (Paiza) with Inscription in Phakpa Script](https://www.metmuseum.org/art/collection/search/39624) — Curatorial description, lines 7–11; Artwork Details, object 1993.256 | broader_topic → Yuan dynasty (`Q7313`), editorial |
| Pansori (`local:catalog:pansori`) | 41 / v1 | [코로나19 극복을 위한 국악 영상 콘서트 '일일국악': 수궁가(영문 자막)[2020.03.25.] - 01. 수궁가](https://archive.gugak.go.kr/portal/detail/searchVideoDetail?clipid=39174&recording_type_code=V&system_id=AV) — Program pamphlet text, lines 100–105 | broader_topic → Music (`Q638`), source_asserted |
| Peirce quincuncial projection (`local:catalog:peirce-quincuncial-projection`) | 40 / v1 | [Peirce quincuncial \| ArcGIS Pro documentation](https://doc.esri.com/en/arcgis-pro/latest/help/mapping/properties/peirce-quincuncial.html) — Description; Graticule; Distortion; Usage | broader_topic → Map projection (`Q186386`), source_asserted |
| Pinpeat (`local:catalog:pinpeat`) | 38 / v1 | [Cultural Preservation and Adaptation: Kulintang, Kundiman, and Pinpeat in the US](https://folkways.si.edu/lesson/cultural-preservation-and-adaptation/kundiman-pinpeat-in-US) — Lesson introduction and learning objectives, lines 440–455 | broader_topic → Music (`Q638`), source_asserted |
| Port Chicago mutiny trial (`local:catalog:port-chicago-mutiny-trial`) | 44 / v1 | [The Mutiny Trial](https://www.nps.gov/poch/learn/historyculture/the-mutiny-trial.htm) — The Aftermath and Mutiny; Trial Proceedings; Exoneration, lines 39–47 and 55 | broader_topic → Racial segregation in the United States (`Q2652357`), editorial |
| The Buddha (Odilon Redon lithograph, 1895) (`local:catalog:redon-buddha-1895`) | 39 / v1 | [L'Estampe Originale: A Rare Print Portfolio Now Online](https://www.metmuseum.org/de/perspectives/lestampe-originale) — Print identification and curatorial explanation, lines 42–45 | facet_of → L’Estampe Originale (`local:catalog:lestampe-originale`), source_asserted |
| Sanké Môn (`local:catalog:sanke-mon`) | 44 / v1 | [UNESCO-Mali aux côtés des Communautés et des Autorités du Mali pour la célébration de la 625ᵉ édition du Sanké Môn.](https://www.unesco.org/fr/articles/unesco-mali-aux-cotes-des-communautes-et-des-autorites-du-mali-pour-la-celebration-de-la-625-edition) — Main French text, lines 24–26 and 34–35 | broader_topic → Ritual (`Q189819`), source_asserted |
| Shibori (`local:catalog:shibori`) | 42 / v1 | [What is Shibori?](https://shibori.org/what-is-shibori/) — Definition, lines 128–131 | facet_of → Dyeing (`Q1164991`), source_asserted |
| Shikantaza (`local:catalog:shikantaza`) | 40 / v1 | [shikantaza](https://pluralism.org/shikantaza) — Definition, line 56 | facet_of → Zazen (`Q167894`), source_asserted |
| Subsequent practice in treaty interpretation (`local:catalog:subsequent-practice-treaty-interpretation`) | 35 / v1 | [Vienna Convention on the Law of Treaties (1969)](https://legal.un.org/ilc/texts/instruments/english/conventions/1_1_1969.pdf) — Article 31(3)(b), printed page 12 | facet_of → Treaty (`Q131569`), source_asserted |
| Sugungga (`local:catalog:sugungga`) | 42 / v1 | [코로나19 극복을 위한 국악 영상 콘서트 '일일국악': 수궁가(영문 자막)[2020.03.25.] - 01. 수궁가](https://archive.gugak.go.kr/portal/detail/searchVideoDetail?clipid=39174&recording_type_code=V&system_id=AV) — Program pamphlet text, lines 100–105 | facet_of → Pansori (`local:catalog:pansori`), source_asserted |
| Taizé meditative singing (`local:catalog:taize-meditative-singing`) | 41 / v1 | [The songs of Taizé](https://www.taize.fr/en/songs) — Meditative singing, lines 54–57, 66 | application_of → Christian prayer (`Q3627146`), editorial |
| Tashlich (`local:catalog:tashlich`) | 42 / v1 | [Why Can’t I Feed Fish at Tashlich?](https://www.chabad.org/library/article_cdo/aid/4501100/jewish/Why-Cant-I-Feed-Fish-at-Tashlich.htm) — Yehuda Shurpin’s main explanation, lines 258–265 | facet_of → Rosh Hashanah (`Q131028`), source_asserted |
| Testimonial injustice (`local:catalog:testimonial-injustice`) | 43 / v1 | [Introduction](https://www.mirandafricker.com/uploads/1/3/6/2/136236203/introduction.pdf) — Printed page 1, testimonial-injustice definition and police example | facet_of → Epistemic injustice (`Q48970669`), source_asserted |
| Treaty reservations (`local:catalog:treaty-reservations`) | 32 / v1 | [Vienna Convention on the Law of Treaties (1969)](https://legal.un.org/ilc/texts/instruments/english/conventions/1_1_1969.pdf) — Articles 2(1)(d), 19, printed pages 2 and 7 | facet_of → Treaty (`Q131569`), source_asserted |
| Triolet (`local:catalog:triolet`) | 43 / v1 | [Triolet](https://poets.org/glossary/triolet) — “Rules of the Triolet Form” | broader_topic → Poetry (`local:authored:000404`), source_asserted |
| Tritina (`local:catalog:tritina`) | 40 / v1 | [Sestina](https://poets.org/glossary/sestina) — “Rules of the Sestina Form”; final history paragraphs describing double sestina and tritina | facet_of → Sestina (`Q1334127`), source_asserted |
| Truthmaker maximalism (`local:catalog:truthmaker-maximalism`) | 43 / v1 | [Truthmakers](https://plato.stanford.edu/entries/truthmakers/) — §2.1 Maximalism, lines 181–203 | facet_of → Truthmaker theory (`local:catalog:truthmaker-theory`), source_asserted |
| Truthmaker theory (`local:catalog:truthmaker-theory`) | 40 / v1 | [Truthmakers](https://plato.stanford.edu/entries/truthmakers/) — §1.1 Truthmaking as Entailment, relevance discussion; §1.2, lines 66–85 | broader_topic → Metaphysics (`local:authored:000431`), source_asserted |
| Wrong kind of reason problem (`local:catalog:wrong-kind-of-reason-problem`) | 43 / v1 | [Fitting Attitude Theories of Value](https://plato.stanford.edu/entries/fitting-attitude-theories/) — §3.1 The Wrong Kind of Reason Problem, lines 167–175 | facet_of → Fitting-attitude theories of value (`local:catalog:fitting-attitude-theories-of-value`), source_asserted |

## Handoff boundary

The candidate is stable for coordinator freezing after the checks recorded above. These are author and structural checks; factual acceptance still depends on the independent audit. This author did not choose or resample the audit set.
