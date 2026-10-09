# Culture independent initial source audit

Auditor: `/root/batch008_audit_culture`. I did not author these cards. All 13 frozen assignments and all 12 attached relations were checked against independently opened source passages and the pinned baseline. The source inspections and full initial hashes are preserved in `initial-review.json`.

Sample SHA256: `5b22b4cd61f691075015997f6c240b3365786131ebe2252f10de6a8e23b15f69`.
Initial assembled candidate SHA256: `75682f9be9a732e2526e916413f6c29efd1c21d86cde5855049b264c98382e0d`.
Baseline SHA256: `e3cd8ebac67579be75742df0bf2f5b2e7781293282345d2286aff205416e0fe2`.

## Random new identities: 3 verified, 0 findings

| Card | Initial outcome | Inspected source |
| --- | --- | --- |
| Pilot judgment procedure | verified | [ECHR factsheet](https://www.echr.coe.int/documents/d/echr/FS_Pilot_judgments_ENG), PDF page 1, lines 4–18 and Rule 61 |
| Tashlich | verified | [Chabad](https://www.chabad.org/library/article_cdo/aid/4501100/jewish/Why-Cant-I-Feed-Fish-at-Tashlich.htm), main explanation, lines 258–265 |
| Gyotaku | verified | [Smithsonian Ocean](https://ocean.si.edu/conservation/get-involved/educational-uses-gyotaku-or-fish-printing), lines 65–69 |

## Targeted identities: 9 verified, 1 needs repair

| Card | Initial outcome | Inspected source |
| --- | --- | --- |
| Euclidean buffering | verified | [Esri](https://doc.esri.com/en/arcgis-pro/latest/tool-reference/analysis/how-buffer-analysis-works.html), lines 74–88 |
| Geodesic buffering | verified | [Esri](https://doc.esri.com/en/arcgis-pro/latest/tool-reference/analysis/how-buffer-analysis-works.html), lines 74–88 |
| Port Chicago mutiny trial | verified | [National Park Service](https://www.nps.gov/poch/learn/historyculture/the-mutiny-trial.htm), lines 39–47, 55, 77 |
| Tritina | verified | [Academy of American Poets](https://poets.org/glossary/sestina), lines 66–67 |
| Pinpeat | verified | [Smithsonian Folkways](https://folkways.si.edu/lesson/cultural-preservation-and-adaptation/kundiman-pinpeat-in-US), introduction and objectives, lines 440–455 |
| Metaphysical grounding | verified | [Stanford Encyclopedia of Philosophy](https://plato.stanford.edu/entries/grounding/), introduction and §1.1 |
| Nembutsu | verified | [Buddhist Churches of America](https://www.buddhistchurchesofamerica.org/temple/visit/buddhist-temple-of-marin), lines 118, 145–165 |
| Non-refoulement | verified | [UNHCR, November 1997](https://www.refworld.org/policy/legalguidance/unhcr/1997/en/36258), Legal basis, Beneficiaries, Exceptions |
| Lukasa (Met 1977.467.3) | verified | [Met object 690570](https://www.metmuseum.org/art/collection/search/690570), lines 10–16 and Object Number |
| Chöd | needs_repair | [LYWA teaching](https://www.lamayeshe.com/article/chapter/ch%C3%B6d-slaying-ego), lines 43–59, 99–104; [LYWA Commentary](https://www.lamayeshe.com/article/chapter/bodhisattva-attitude-commentary), Notes 3 |

**Finding culture-initial-chod-01 — moderate, substantive meaning qualification.** Frozen v1 says “ritual offerings of the body” without specifying visualization. This leaves a literal bodily-sacrifice reading possible. LYWA’s [Commentary, Notes 3](https://www.lamayeshe.com/article/chapter/bodhisattva-attitude-commentary) explicitly identifies the offering as visualization. Replace **ritual** with **visualized**, attach that supplementary evidence, and bump the affected version. The teaching attribution and `application_of → Buddhism` relation pass.

The targeted meanings remain correctly qualified: mathematical Euclidean buffering differs from ArcGIS’s Planar option; the Met card concerns one artifact; Marin’s Nembutsu account is community-specific; non-refoulement retains instrument-specific rules and the November 1997 source date. Every attached relation has a separate direction and target-meaning check in the JSON.

All 12 original URLs and the one supplementary page were accessible; no failed attempts or inaccessible claims were substituted with snippets. Exact remote retrieval timestamps, actual token usage and cost are unavailable. Local post-inspection timestamps are recorded. This is an audit of the assigned sample, not all 200 cards. No author cards, operational files, sample selections or human-study materials were edited. Stop point: initial review, pending coordinator-assigned rechecks.

## Recheck 001 — Chöd v2

**Outcome: verified.** Finding `culture-initial-chod-01` is resolved by replacing “ritual offerings” with “visualized offerings” and attaching [LYWA Commentary, Notes 3](https://www.lamayeshe.com/article/chapter/bodhisattva-attitude-commentary). I independently reopened that note and the [original teaching](https://www.lamayeshe.com/article/chapter/ch%C3%B6d-slaying-ego), lines 23–29, 43–59 and 99–104. The revised 41-word body adds no unsupported claim; the retained `application_of → Buddhism` relation passes again.

Rechecked culture shard SHA256: `996e6b5631aacbe2aa3a63815d90da546e9dd1fcf8ce9021c3dd9ac813a9c111`. New card/source-bundle hashes, exact inspection locators and the finding resolution are in `recheck-001.json`; their raw-shard scope is explicit. Local post-inspection timestamp: `2026-10-09T03:12:05+00:00`. Both URLs were accessible. The initial review and fixed sample remain unchanged.
