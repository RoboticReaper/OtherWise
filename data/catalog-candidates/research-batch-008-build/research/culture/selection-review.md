# Batch 008 culture selection checkpoint

Selection only: **70 primary subjects, 64 proposed new identities and 6 existing controls**, plus three alternatives. All eight domain allocations and all four scopes are represented. Each primary subject has an inspected public passage; the coordinator must reconcile identities and approve reservations before card drafting.

The frozen baseline contains 35,743 active IDs after reviewed redirects. Its SHA256 is `e3cd8ebac67579be75742df0bf2f5b2e7781293282345d2286aff205416e0fe2`. Selection used public references and focused baseline label, alias and nearby-meaning checks. Private preference data was outside the inputs.

| Domain | Primary | New | Controls |
|---|---:|---:|---:|
| Geography & travel | 9 | 8 | 1 |
| History & culture | 9 | 8 | 1 |
| Literature & storytelling | 9 | 8 | 1 |
| Music & performance | 9 | 8 | 1 |
| Philosophy | 9 | 8 | 1 |
| Politics & law | 9 | 8 | 1 |
| Religion & spirituality | 8 | 8 | 0 |
| Visual arts & design | 8 | 8 | 0 |

Measured breadth: 1 broad field, 12 topics, 23 ideas and 34 facets/applications. There are **55 new fine-scope subjects** and **11 actual named subjects**. Eponymous projections, poetic forms and named methods remain ideas. These measurements contribute to the batch’s soft global goals without changing identity decisions.

Of 57 fine-scope primary subjects, 55 have a proposed parent/application edge and 49 have a source-asserted edge (96.5% and 86.0%). Among the 55 new fine subjects, the corresponding counts are 54 and 48. Targets resolve to the baseline or another primary proposal; cross-proposal links remain conditional on global reservations.

Identity decisions and qualifications:

- [Esri’s buffer methods](https://doc.esri.com/en/arcgis-pro/latest/tool-reference/analysis/how-buffer-analysis-works.html) support distinct Euclidean and geodesic construction facets under existing `local:catalog:geographic-buffer`. The software PLANAR option can select geodesic behavior for geographic inputs, so the bare alias “Planar buffering” was removed. Equal-area and conformal classes are broader than the individually named projections.
- [The sestina glossary](https://poets.org/glossary/sestina) supports reuse of `Q1334127`; the named poem Sestina: Altaforte remains distinct. Tritina has its own specified contraction. [Poetry Archive’s form page](https://poetryarchive.org/glossary/form/) is internally inconsistent on the Spenserian rhyme sequence, leaving that alternative excluded.
- [SEP’s grounding entry](https://plato.stanford.edu/entries/grounding/) concerns metaphysical dependence, distinct from grounding in communication. [Epistemic-injustice discussion](https://plato.stanford.edu/entries/feminist-social-epistemology/) supports distinct credibility, interpretive-resource and contributory mechanisms beneath the reused epistemic-injustice ID.
- [The Met’s Lukasa](https://www.metmuseum.org/art/collection/search/690570) and [Phakpa-script pass](https://www.metmuseum.org/art/collection/search/39624) are individual artifact identities with object numbers. Bare Lukasa and Paiza are general categories, not aliases for those objects. Lukasa has no asserted parent because its general category is missing. Mbudye is a separate institution/practice subject.
- [NPS’s Green Book history](https://www.nps.gov/articles/green-book-properties-listed-in-the-national-register-of-historic-places.htm) identifies the publication series, distinct from the film. Its response to segregation is historical placement rather than an application of segregation. [The Port Chicago page](https://www.nps.gov/poch/learn/historyculture/the-mutiny-trial.htm) records 2024 exoneration; contradictory cause and testimony statements are excluded from the takeaway.
- [The National Gugak Center program](https://archive.gugak.go.kr/portal/detail/searchVideoDetail?clipid=39174&recording_type_code=V&system_id=AV) distinguishes Pansori from Sugungga, a particular story. Hare Taryeong denotes a scene. [Kulintang Kultura](https://folkways.si.edu/kulintang-kultura) is an individual album; Kulintang music denotes a tradition, distinct from its namesake instrument.
- [The Vienna Convention](https://legal.un.org/ilc/texts/instruments/english/conventions/1_1_1969.pdf) supports four separately stated rules, with scope and agreement conditions preserved. [Rome Statute Article 17](https://legal.un.org/icc/statute/99_corr/cstatute.htm) supports ICC complementarity in the original corrected text. [Article 8 review](https://ks.echr.coe.int/documents/d/echr-ks/guide_art_8_eng) is an example of existing proportionality; it does not justify a new general identity or universal parent. [UNHCR’s note](https://www.refworld.org/policy/legalguidance/unhcr/1997/en/36258) preserves instrument-specific non-refoulement exceptions.
- [Shikantaza](https://pluralism.org/shikantaza) is a specified zazen approach; [Satori](https://pluralism.org/satori) may instead be a tradition-specific enlightenment synonym, so it remains excluded. Religion takeaways describe practices and attributed doctrine. [Nembutsu’s inspected temple account](https://www.buddhistchurchesofamerica.org/temple/visit/buddhist-temple-of-marin) is limited to Shin Buddhist gratitude practice.
- [The print portfolio article](https://www.metmuseum.org/de/perspectives/lestampe-originale) distinguishes Chine collé, L’Estampe Originale and Redon’s 1895 Buddha lithograph. [The practitioner network](https://shibori.org/what-is-shibori/) identifies shaped-resist methods, while [Kanoko](https://www.metmuseum.org/art/collection/search/45399) and [Itoh’s garment](https://www.metmuseum.org/art/collection/search/79595) have specific technique/artifact boundaries.

Primary selections and inspected locators follow. “New” is a proposal, pending global reconciliation. Full aliases, nearest baseline meanings, takeaway and relation evidence are in `proposals.json`.

## Geography & travel

| Subject | Status / scope | Inspected reference |
|---|---|---|
| Geography | Control; broad_field | [Main text, paragraphs 1–3; “Geography informs us about”; human/physical geography paragraph](https://www.rgs.org/about-us/what-is-geography) |
| Equal Earth projection | New; facet_or_application | [Description; Distortion; Usage](https://doc.esri.com/en/arcgis-pro/latest/help/mapping/properties/equal-earth.html) |
| Natural Earth projection | New; facet_or_application | [Description; Distortion; Limitations](https://doc.esri.com/en/arcgis-pro/latest/help/mapping/properties/natural-earth.html) |
| Goode homolosine projection | New; facet_or_application | [Description; Graticule; Usage; Limitations](https://doc.esri.com/en/arcgis-pro/latest/help/mapping/properties/goode-homolosine.html) |
| Hotine oblique Mercator projection | New; facet_or_application | [Description; Distortion; Usage; Variants](https://doc.esri.com/en/arcgis-pro/latest/help/mapping/properties/hotine-oblique-mercator.html) |
| Peirce quincuncial projection | New; facet_or_application | [Description; Graticule; Distortion; Usage](https://doc.esri.com/en/arcgis-pro/latest/help/mapping/properties/peirce-quincuncial.html) |
| Adams square II projection | New; facet_or_application | [Description; Graticule; Distortion; Usage](https://doc.esri.com/en/arcgis-pro/latest/help/mapping/properties/adams-square-ii.html) |
| Geodesic buffering | New; facet_or_application | [“Euclidean and geodesic buffering”, method bullets and shape-preserving Geodesic option](https://doc.esri.com/en/arcgis-pro/latest/tool-reference/analysis/how-buffer-analysis-works.html) |
| Euclidean buffering | New; facet_or_application | [“Euclidean and geodesic buffering”, method bullets and shape-preserving Geodesic option](https://doc.esri.com/en/arcgis-pro/latest/tool-reference/analysis/how-buffer-analysis-works.html) |

## History & culture

| Subject | Status / scope | Inspected reference |
|---|---|---|
| Khipu | Control; topic | [What is a khipu?, Encoding the Khipu, Khipu Uses (lines 132–157, 194–196)](https://www.nist.gov/nist-museum/standardizing-empire) |
| Chaski (Inca messenger) | New; facet_or_application | [Khipu Uses, line 196](https://www.nist.gov/nist-museum/standardizing-empire) |
| Lukasa memory board (Met 1977.467.3) | New; facet_or_application | [Curatorial description (lines 10–16), Artwork Details](https://www.metmuseum.org/art/collection/search/690570) |
| Mbudye association | New; topic | [Curatorial description, lines 12–13](https://www.metmuseum.org/art/collection/search/690570) |
| Safe Conduct Pass in Phakpa script (Met 1993.256) | New; facet_or_application | [Curatorial description (lines 10–11), Artwork Details](https://www.metmuseum.org/art/collection/search/39624) |
| Sanké Môn | New; topic | [Main French text, lines 24–26, 34–35](https://www.unesco.org/fr/articles/unesco-mali-aux-cotes-des-communautes-et-des-autorites-du-mali-pour-la-celebration-de-la-625-edition) |
| The Negro Motorist Green Book | New; topic | [Opening history, lines 24–38](https://www.nps.gov/articles/green-book-properties-listed-in-the-national-register-of-historic-places.htm) |
| Port Chicago mutiny trial | New; facet_or_application | [Aftermath and Trial Proceedings (lines 39–47); exoneration update (55, 77)](https://www.nps.gov/poch/learn/historyculture/the-mutiny-trial.htm) |
| Civilian Public Service (US, World War II) | New; topic | [Civilian Public Service and Challenges, lines 44–60](https://home.nps.gov/places/patapsco-camp-wwii-civilian-public-service-site.htm) |

## Literature & storytelling

| Subject | Status / scope | Inspected reference |
|---|---|---|
| Sestina | Control; idea | [“Rules of the Sestina Form”; final history paragraphs describing double sestina and tritina](https://poets.org/glossary/sestina) |
| Cento | New; idea | [Definition; “More about the Cento Form”](https://poets.org/glossary/cento) |
| Haibun | New; idea | [Definition; “From A Poet’s Glossary”, prose–haiku relationship](https://poets.org/glossary/haibun) |
| Triolet | New; idea | [“Rules of the Triolet Form”](https://poets.org/glossary/triolet) |
| Clerihew | New; idea | [“About Form”; CLERIHEW; DOUBLE-DACTYL; OTTAVA RIMA; SPENSERIAN STANZA](https://poetryarchive.org/glossary/form/) |
| Double dactyl | New; idea | [“About Form”; CLERIHEW; DOUBLE-DACTYL; OTTAVA RIMA; SPENSERIAN STANZA](https://poetryarchive.org/glossary/form/) |
| Ottava rima | New; idea | [“About Form”; CLERIHEW; DOUBLE-DACTYL; OTTAVA RIMA; SPENSERIAN STANZA](https://poetryarchive.org/glossary/form/) |
| Tritina | New; facet_or_application | [“Rules of the Sestina Form”; final history paragraphs describing double sestina and tritina](https://poets.org/glossary/sestina) |
| Acrostic | New; idea | [ACROSTIC entry, line 38](https://poetryarchive.org/glossary/form/) |

## Music & performance

| Subject | Status / scope | Inspected reference |
|---|---|---|
| Pansori | New; topic | [Program pamphlet text, lines 100–105](https://archive.gugak.go.kr/portal/detail/searchVideoDetail?clipid=39174&recording_type_code=V&system_id=AV) |
| Sugungga | New; facet_or_application | [Program pamphlet text, lines 100–105](https://archive.gugak.go.kr/portal/detail/searchVideoDetail?clipid=39174&recording_type_code=V&system_id=AV) |
| Kulintang music | New; topic | [Lesson introduction and learning objectives, lines 440–455](https://folkways.si.edu/lesson/cultural-preservation-and-adaptation/kundiman-pinpeat-in-US) |
| Kundiman | New; topic | [Lesson introduction and learning objectives, lines 440–455](https://folkways.si.edu/lesson/cultural-preservation-and-adaptation/kundiman-pinpeat-in-US) |
| Pinpeat | New; topic | [Lesson introduction and learning objectives, lines 440–455](https://folkways.si.edu/lesson/cultural-preservation-and-adaptation/kundiman-pinpeat-in-US) |
| Kulintang Kultura: Danongan Kalanduyan and Gong Music of the Philippine Diaspora | New; facet_or_application | [Album description, lines 456–457; Release Info, 505–513](https://folkways.si.edu/kulintang-kultura) |
| Gamelan | Control; topic | [David Harnish’s guest article, lines 450–468](https://folkways.si.edu/news-and-press/unesco-collection-week-34-balinese-court-music) |
| Gamelan gong kebyar | New; facet_or_application | [David Harnish’s guest article, lines 450–468](https://folkways.si.edu/news-and-press/unesco-collection-week-34-balinese-court-music) |
| Kotekan | New; idea | [David Harnish’s guest article, lines 450–468](https://folkways.si.edu/news-and-press/unesco-collection-week-34-balinese-court-music) |

## Philosophy

| Subject | Status / scope | Inspected reference |
|---|---|---|
| Metaphysical grounding | New; idea | [Introduction, strike/picketing example; §1.1](https://plato.stanford.edu/entries/grounding/) |
| Truthmaker theory | New; idea | [Introduction; §1; §2.1 Maximalism](https://plato.stanford.edu/entries/truthmakers/) |
| Truthmaker maximalism | New; facet_or_application | [§2.1 Maximalism](https://plato.stanford.edu/entries/truthmakers/) |
| Fitting-attitude theories of value | New; idea | [Introduction; §3.1 The Wrong Kind of Reason Problem](https://plato.stanford.edu/entries/fitting-attitude-theories/) |
| Wrong kind of reason problem | New; idea | [§3.1 The Wrong Kind of Reason Problem](https://plato.stanford.edu/entries/fitting-attitude-theories/) |
| Epistemic injustice | Control; topic | [§4.1 Epistemic Injustice, Fricker and Dotson paragraphs](https://plato.stanford.edu/entries/feminist-social-epistemology/) |
| Testimonial injustice | New; facet_or_application | [§4.1, Fricker’s testimonial-injustice paragraphs](https://plato.stanford.edu/entries/feminist-social-epistemology/) |
| Hermeneutical injustice | New; facet_or_application | [§4.1, Fricker’s hermeneutical-injustice paragraphs](https://plato.stanford.edu/entries/feminist-social-epistemology/) |
| Contributory injustice | New; facet_or_application | [§4.1, Dotson and Pohlhaus paragraphs](https://plato.stanford.edu/entries/feminist-social-epistemology/) |

## Politics & law

| Subject | Status / scope | Inspected reference |
|---|---|---|
| Treaty reservations | New; facet_or_application | [Articles 2(1)(d), 19, printed pages 2 and 7](https://legal.un.org/ilc/texts/instruments/english/conventions/1_1_1969.pdf) |
| Pacta sunt servanda | New; idea | [Article 26, printed page 10](https://legal.un.org/ilc/texts/instruments/english/conventions/1_1_1969.pdf) |
| Subsequent practice in treaty interpretation | New; facet_or_application | [Article 31(3)(b), printed page 12](https://legal.un.org/ilc/texts/instruments/english/conventions/1_1_1969.pdf) |
| Jus cogens | New; idea | [Article 53, printed page 17](https://legal.un.org/ilc/texts/instruments/english/conventions/1_1_1969.pdf) |
| Complementarity (International Criminal Court) | New; facet_or_application | [Preamble, Article 1, Article 17 (lines 18, 25, 244–258)](https://legal.un.org/icc/statute/99_corr/cstatute.htm) |
| Pilot judgment procedure (European Court of Human Rights) | New; idea | [What is the pilot judgment procedure?, printed page 1, lines 4–18](https://www.echr.coe.int/documents/d/echr/FS_Pilot_judgments_ENG) |
| Margin of appreciation (European human-rights law) | New; idea | [Is the interference necessary in a democratic society?, paragraphs 34–36, printed pages 15–16](https://ks.echr.coe.int/documents/d/echr-ks/guide_art_8_eng) |
| Proportionality (law) | Control; idea | [Is the interference necessary in a democratic society?, paragraphs 34–36, printed pages 15–16](https://ks.echr.coe.int/documents/d/echr-ks/guide_art_8_eng) |
| Non-refoulement | New; idea | [Legal basis, Beneficiaries and Exceptions, lines 44–79, 107–120](https://www.refworld.org/policy/legalguidance/unhcr/1997/en/36258) |

## Religion & spirituality

| Subject | Status / scope | Inspected reference |
|---|---|---|
| Koan | New; idea | [Definition, line 56](https://pluralism.org/koan) |
| Shikantaza | New; facet_or_application | [Definition, line 56](https://pluralism.org/shikantaza) |
| Dhikr | New; facet_or_application | [Definition, line 56](https://pluralism.org/dhikr) |
| Ignatian Examen | New; facet_or_application | [Main explanation and five-step method, lines 85–98](https://www.ignatianspirituality.com/ignatian-prayer/the-examen/) |
| Tashlich | New; facet_or_application | [Yehuda Shurpin’s main explanation, lines 258–265](https://www.chabad.org/library/article_cdo/aid/4501100/jewish/Why-Cant-I-Feed-Fish-at-Tashlich.htm) |
| Taizé meditative singing | New; facet_or_application | [Meditative singing, lines 54–57, 66](https://www.taize.fr/en/songs) |
| Chöd | New; facet_or_application | [Lama Zopa Rinpoche’s teaching, lines 43–52, 101–104](https://www.lamayeshe.com/article/chapter/ch%C3%B6d-slaying-ego) |
| Nembutsu | New; facet_or_application | [Tradition statement and practices, lines 118, 145–165](https://www.buddhistchurchesofamerica.org/temple/visit/buddhist-temple-of-marin) |

## Visual arts & design

| Subject | Status / scope | Inspected reference |
|---|---|---|
| Chine collé | New; idea | [Curatorial article, lines 44–45](https://www.metmuseum.org/de/perspectives/lestampe-originale) |
| L’Estampe Originale | New; facet_or_application | [Curatorial article, lines 13–16, 22, 31–38](https://www.metmuseum.org/de/perspectives/lestampe-originale) |
| The Buddha (Odilon Redon lithograph, 1895) | New; facet_or_application | [Print identification and curatorial explanation, lines 42–45](https://www.metmuseum.org/de/perspectives/lestampe-originale) |
| Shibori | New; topic | [Definition, lines 128–131; Arashi section, 143–148](https://shibori.org/what-is-shibori/) |
| Kanoko shibori | New; facet_or_application | [Curatorial description, lines 10–11; Artwork Details](https://www.metmuseum.org/art/collection/search/45399) |
| Tokuseu Hitome Sohshibori Hon Furisode (Met 1997.228) | New; facet_or_application | [Curatorial description, lines 10–12; object identification, 31–39](https://www.metmuseum.org/art/collection/search/79595) |
| Kintsugi | New; idea | [Exhibition overview, lines 10–11](https://www.metmuseum.org/ja/exhibitions/the-infinite-artistry-of-japanese-ceramics) |
| Gyotaku | New; idea | [Catherine Sutera’s museum account, lines 65–69](https://ocean.si.edu/conservation/get-involved/educational-uses-gyotaku-or-fish-printing) |

## Alternatives and access limits

| Alternative | Decision | Reference |
|---|---|---|
| Spenserian stanza | Unresolved; excluded from primary | [“About Form”; CLERIHEW; DOUBLE-DACTYL; OTTAVA RIMA; SPENSERIAN STANZA](https://poetryarchive.org/glossary/form/) |
| Satori | Unresolved; excluded from primary | [Definition, lines 55–56](https://pluralism.org/satori) |
| Arashi shibori | Supported replacement option; not primary | [Arashi shibori section, lines 143–148](https://shibori.org/what-is-shibori/) |

UNESCO ICH pages returned CAPTCHA, while an accessible UNESCO article supports Sanké Môn. Some Carnegie Hall, Smithsonian media, museum and NOAA routes failed; accessible institutional HTML or alternate official documents supplied the selected evidence. Search snippets only located sources. Failed URLs never support primary takeaways. The access ledger records the known limits without claiming exact attempt counts where unavailable.

The 48 preserved source records identify the actual HTML/PDF text inspection, passage location, available revision and local post-inspection timestamp. Exact remote retrieval timestamps were unavailable. Museum collection descriptions remain curatorial interpretations; legal guides and historical editions retain their stated limits.

Shared-page summary budgets are collective. The Poetry Archive page supports four primary forms and one excluded alternative; its selection takeaways total 65 words. Drafting must keep all prose derived from that page within its retrieval budget or inspect additional independent primary sources. Other shared pages have similarly short selection takeaways; metadata avoids duplicate explanatory prose.

Local checks confirm exact domain totals, six canonical controls, unique proposal/source IDs, normalized alias screening, valid source metadata and parent-target resolution. These structural checks are separate from the coordinator’s independent source audit. No cards, operational imports, registry changes, installs or commits were produced.

**Next step: coordinator global identity reconciliation and approved reservations. Card drafting is stopped at this checkpoint.**
