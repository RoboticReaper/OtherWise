# Systems selection review — batch 009

Status: 65 source-backed proposals ready for coordinator reservations. No card bodies have been drafted.

## Identity and ownership checks

- All 65 IDs are distinct, present in the assigned eligible file, and have no prior candidate card in the frozen baseline.
- Labels, aliases, original descriptions and assigned primary domains were compared with the frozen canonical records. No operational data or existing description was changed.
- Baseline SHA-256: `1d1e18e85f9d5cb0ec46c48668a80dc8b9826c78a01a5285540367ffc55474d1`.
- Inventory fingerprint: `7c3499df0aee4b300ce6a11a3a00dc9446b6422e36a7dc1b15ec7ea9db9f27a3`.
- Normalized comparisons include frozen aliases and every historical candidate record label/alias across 1467 described identities. No exact normalized collision was found.
- Two close spelling matches were inspected: Computing/Composting and Socialization/Focalization. These name different subjects.
- Name matching does not establish absence of every differently named semantic duplicate. Coordinator review and global reservations remain necessary.

## Coverage

| Primary domain | Selected | Quota |
| --- | ---: | ---: |
| Computing & information | 10 | 10 |
| Economics & organizations | 9 | 9 |
| Engineering & transport | 10 | 10 |
| Games & sports | 9 | 9 |
| Learning & language | 9 | 9 |
| Mind & behavior | 9 | 9 |
| Society & relationships | 9 | 9 |

| Scope | Count |
| --- | ---: |
| `broad_field` | 5 |
| `idea` | 31 |
| `facet_or_application` | 14 |
| `topic` | 15 |

The selection contains 55 idea identities and 10 named subjects. Forty-five proposals are fine ideas or facets/applications. The five broad fields retain a concrete learning direction; coverage is selective, not comprehensive.

## Evidence and limits

- `sources-inspected.json` retains 64 inspected sources, passage locators, inspection methods, available revisions, tool references and honest acquisition-time bases. No search snippet or identity link alone is used as discovery evidence.
- Nineteen access limitations or failures are retained. Replacements are recorded; four unavailable FIBA sources led to withdrawing the 3x3 basketball candidate and selecting the researched Triple jump identity instead.
- The three shared pages support two proposals each: short-run costs, US Chess piece rules, and World Athletics technical rules. `source-word-budgets.json` counts the takeaway, substantive evidence note, source-specific qualification and attached relation note for each proposal.
- All source totals remain below their retrieved 200-word limits and leave at least 25 words per proposed card. These are selection-stage counts: final bodies and any additional source-derived prose must be recounted. Identical checkpoint/proposal text is one authored summary; bibliographic locators and procedural checks are not treated as source-derived explanation.
- Cross-assignment URL sharing and companion representations must be reconciled by the coordinator before acceptance.
- The Internet Archive institutional page returned no substantive readable passage; the inspected official Wayback help page supplies the selected service example. One service does not stand for the institution's entire mandate.

## Relations

Thirty-seven proposals have supported parent links: 28 source-asserted and 9 editorial. Among the 45 fine ideas/facets, 33 have supported parents (73.3%) and 28 have source-asserted parents (62.2%). Both earlier relationship coverage goals are met; the remaining gaps are retained.

`relationship-evidence.json` records exact short excerpts, surrounding passage locators, tool references, assertion types and verified target labels for 29 relationship inspections. Source assertions require an explicit category, method, component, or learning-process statement. Broad field context alone remains editorial. Two additional authoritative references clarify SVG as an XML application and aspect as a grammatical category.

The following 28 proposals retain an explicit parent gap:

- `Q179310` — Computing
- `Q339338` — Endianness
- `Q189401` — Virtual memory
- `Q245` — Raspberry Pi
- `Q187899` — Deep Blue (chess computer)
- `local:authored:000574` — Microeconomics
- `Q215551` — Comparative advantage
- `Q5970087` — Economies of scale
- `Q223639` — Elasticity (economics)
- `Q806663` — Bank run
- `Q320863` — World Bank Group
- `local:authored:000545` — Civil engineering
- `Q190100` — Bearing (mechanical)
- `Q82412` — Epicyclic gearing
- `Q274897` — Portal (video game)
- `Q49740` — Minecraft
- `Q71910` — Tetris
- `Q136851` — Curling
- `Q255615` — Code-switching
- `local:authored:000685` — Montessori education
- `Q272021` — Gestalt psychology
- `Q783092` — Executive functions
- `Q1860557` — Self-concept
- `Q161272` — social psychology
- `Q841628` — Social stratification
- `Q741550` — Cultural relativism
- `Q461` — Internet Archive
- `Q740308` — UNICEF

## Handoff

`proposals.json` is the reservation input. `selection-validation.json` records reproducible identity, quota, scope, source-budget and parent-target checks. Draft only IDs subsequently present in `approved-selection.json`, preserve existing cards, and keep every new body at most 25 whitespace-separated words.
