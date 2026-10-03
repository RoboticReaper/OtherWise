# Local discovery graph

`discovery_graph.json` is an offline sample of English Wikipedia category
memberships and Wikidata descriptions. It supplements the broad `topics.json`
catalog with concrete concepts.

The current snapshot has **3,642 unique concepts, 69 areas, 319 category nodes,
and 3,919 sourced edges**. It contains **132 distinct reviewed concepts**.
Counts summed across domains are larger because some concepts serve more than
one domain. All 23 domains meet their concept and reviewed-level targets; no
source failures or truncated category enumerations were reported.

## Balance policy

The graph covers all **23 domains** in the original catalog. Each domain has
**three navigation areas** and the same **160-concept budget**. Concepts are
selected round-robin across the areas with deterministic SHA-256 ordering.
A small reviewed sample reserves **two entries per reading level per domain**;
remaining places are filled from unreviewed concepts. Sparse pools can use extra
reviewed entries, and any shortfall is reported rather than filled with invented
concepts. The checked-in snapshot is tested for equal budgets and level coverage.

All areas start with one category-to-category hop. If a domain has fewer than
160 eligible concepts, all three of its areas may search one additional level.
This same rule applies to every domain. Seed-specific depth exceptions are
rejected. A large subject does not receive a larger final allocation just because
Wikipedia supplies more articles or categories for it.

`metadata.balance.coverage` records available and selected counts, reviewed
levels, and shortfalls. The notebook displays the final domain coverage. Counts
are measured on the actual pools used by the recommender. A concept may be
selected in more than one domain but is stored once and recommended once.

Balanced domain counts do not establish cultural, political, or viewpoint
neutrality. The domain grouping and area seeds are editorial choices, and the
source is English Wikipedia. Recommendation lists still depend on the user's
interests, distance band, and feedback; they are not forced to contain an equal
number of results from every domain.

## Source graph and catalog selection

The graph has `version: 1`, `metadata`, `areas`, `nodes`, and `edges`.

- Areas have an ID, topic, description, domain, root `category_id`, and
  `concept_ids` identifying their selected catalog entries.
- Category nodes retain Wikipedia titles and source URLs. Category descriptions
  are explicitly labeled as category labels.
- Concept nodes use Wikidata IDs, English descriptions and revision IDs,
  Wikipedia titles and page IDs, and nullable `level` annotations.
- Edges retain the source category, member, relation, original membership title,
  observation time and API evidence URL. All retained edges came from the API.

Area `concept_ids` are catalog selections, not additional semantic edges. They
prevent shared categories from accidentally exposing another domain's whole
selection and exceeding its budget. Every selected item still needs a real path
from that area's root. Only paths needed for the selected entries are retained.
Redirects retain their original membership title: the source may have listed a
redirect rather than the canonical article.

Category membership is not a prerequisite, subclass, or difficulty relation.
The source may contain cycles and multiple parents. Runtime traversal guards
cycles, applies the area selections, and deduplicates concepts by ID.

## Bounded import

A category contributes at most four child categories and 24 concepts, with a
600-category global safety limit. Up to 72 candidate articles are considered
before Wikidata filtering. Root categories are reserved before children.

The API enumerates at most two pages of 500 members per category. Larger pools
are recorded as truncated. Authored preferences are considered first within the
observed pool, followed by stable hash sampling; this is not a random sample of
the entire encyclopedia. Maintenance categories, people, lists, missing
Wikidata descriptions, and broad area/category overview articles are filtered.
The filters are pragmatic; cultural works, events, species, places and some
organizations can still occur.

`metadata.complete` refers only to the bounded source import: no fetch failures
or truncated enumeration. It does not mean all subjects are fully represented.
`metadata.balance.shortfalls` separately reports unfilled domain budgets, and
`reviewed_shortfalls` reports gaps in the reviewed level samples. The importer
preserves the existing output on source failures or either kind of shortfall
unless `--allow-partial` is explicitly selected.

## Authored hooks and levels

Hooks and levels are ProductSpace editorial annotations, kept separately in the
seed file and applied only to observed source members. Levels describe an
introductory treatment: **1** accessible, **2** some background helpful, **3**
technical. They are not source facts or inferred from graph depth. Unknown levels
stay `null`; the system does not infer a user's competence from them.

## Provenance and licensing

- [Wikipedia category membership API](https://www.mediawiki.org/wiki/API:Categorymembers)
  supplies observed parent/member relationships. Each edge links its source and
  API evidence; local cached responses retain observation times. Category-page
  revision IDs do not freeze the changing membership list.
- [Wikidata data access](https://www.wikidata.org/wiki/Wikidata:Data_access)
  supplies IDs, descriptions, revisions, and instance-of claims for filtering.
  Previously cached descriptions may predate the membership observation.
- [Wikidata structured data is CC0](https://www.wikidata.org/wiki/Wikidata:Licensing).
  Wikipedia category structure is attributed to English Wikipedia contributors
  under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
  Selection, navigation labels, hooks, and reading levels are ProductSpace
  modifications. Wikipedia article prose is not imported.

## Rebuild

```sh
.venv/bin/python scripts/import_discovery_graph.py
.venv/bin/python scripts/import_discovery_graph.py --offline --output /tmp/discovery_graph.json
.venv/bin/python scripts/import_discovery_graph.py --refresh
```

Source requests are sequential, paced, cached under `.cache/discovery-graph`,
and use a project-identified User-Agent with Retry-After handling. The intermediate
pool is cached there as `raw-pool.json` for inspection. Runtime recommendations
only read the saved graph; they make no Wikimedia requests.

`--concepts-per-domain` controls the shared domain budget. Other bounds are
`--depth`, `--children`, `--concepts`, `--max-categories`, and
`--max-member-pages`. An offline cache miss is a reported source failure, never
a fabricated relationship. Cached rebuilds preserve membership evidence.

```sh
.venv/bin/python -m pytest tests/test_graph_import.py tests/test_graph_balance.py -q
```
