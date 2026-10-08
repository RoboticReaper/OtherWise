# Catalog coverage and sources

The default fixed catalog contains **31,637 topics across 23 domains**,
including **28,185 additions**. `topics.json` combines the original balanced interests
with non-biographical entries from Wikipedia Vital Articles Level 5. Exact snapshot
counts, filtering totals, domain counts and list revisions are recorded in
`catalog_metadata.json`. Every topic has a literal title, English description,
domain and source. Recommendations embed the title plus description; normal
backend startup and extension use require no Wikipedia or Wikidata API requests.

## Selection

- Preserve all 3,452 previous topic records, including 718 authored ProductSpace
  interests and 2,734 Wikidata concepts selected from Wikimedia's expanded guide.
  Their names and descriptions stay unchanged, so existing saved interests retain
  their IDs. This baseline and its metadata are archived under `archives/`.
- Expand from [Wikipedia Vital Articles Level 5](https://en.wikipedia.org/wiki/Wikipedia:Vital_articles/Level/5),
  following canonical English article titles and their linked Wikidata entities.
  Unlike the previous balanced snapshot, there is no 160-topic domain cap.
- Exclude the People lists, listed company and educational-institution sections,
  explicit individual-work/structure sections, and entities directly marked as
  humans, disambiguation pages, lists, or the excluded work/institution types.
- Require an English Wikidata description of at least three words. Deduplicate
  normalized titles and Wikidata IDs, giving the retained baseline precedence.
- Classify imported topics into the same 23 domains using their actual subsection
  headings. This keeps mixed pages such as philosophy/religion and politics/
  economics from routing every topic through the page title alone.

This is a larger general-interest pool, not equal coverage across domains.
Countries, cities, species, historical events and some named works or fictional
characters may appear alongside abstract concepts. Direct instance-type filters
cannot exclude every subtype. Related concepts and synonyms may remain. English
Wikipedia selection is community-maintained and does not guarantee completeness
or cultural neutrality. Descriptions can be brief or contain errors.

The separate Specific discovery graph (`discovery_graph.json`) retains its curated
concept relationships. The expanded catalog powers Broad discovery, catalog
Focus, local title matching and the whole-catalog Galaxy.

## Provenance and licensing

Imported records include the Wikidata ID/revision, canonical article URL, source
list URL/revision and subsection. List selection and structure are credited to
Wikipedia and Wikimedia contributors. Our filtering and domain grouping are
modifications; the derived selection and grouping are distributed under
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Wikidata labels and short
structured descriptions are [CC0](https://www.wikidata.org/wiki/Wikidata:Licensing).
Article bodies are not copied. Retained authored interests remain in
`curated_topics.json`; the previous Wikimedia guide is attributed in its archived
metadata and [expanded source list](https://meta.wikimedia.org/wiki/List_of_articles_every_Wikipedia_should_have/Expanded).

## Rebuild

From the project directory:

```sh
.venv/bin/python scripts/import_expanded_catalog.py
.venv/bin/python -c 'from service.engine import RecommendationEngine; from service.discovery import DiscoveryEngine; engine = RecommendationEngine(); engine.initialize(); DiscoveryEngine(engine).initialize()'
.venv-layout/bin/python scripts/build_galaxy.py
.venv/bin/python scripts/build_focus_preview.py
.venv/bin/python scripts/build_extension.py
```

Set up `.venv-layout` with `requirements-layout.txt` as described in
[Galaxy preprocessing](../docs/galaxy-preprocessing.md). The layout reads the exact
original-vector cache prepared by the backend; the packaged catalog and layout
must match the backend's catalog and vector fingerprints for Focus to work.
After rebuilding, reload the unpacked extension in Chrome and refresh its tabs.
Saved interests are in browser storage and are not part of the build output.

The importer caches validated public API snapshots under
`.cache/catalog-expansion/responses` so interrupted downloads can resume. Repeated
imports use that snapshot and the archived baseline, rather than accumulating their
own outputs. To intentionally refresh sources, move this cache directory aside
before importing again. A changed snapshot requires new embeddings, layout and
extension packaging. Source-download failures and insubstantial imports leave the
previous catalog intact.

The default unattended importer sends `maxlag=5` and retries temporary errors.
For a human-waiting import, `--interactive` omits the optional maxlag parameter,
consistent with [MediaWiki guidance](https://www.mediawiki.org/wiki/Manual:Maxlag_parameter).
HTTP rate limits and retries still apply. `--workers 3` enables at most three
concurrent batches while keeping the shared request rate at two per second.

Double-click `Start-OtherWise-Local.command` to start the prepared local backend.
Connection details are kept in the private `.cache/demo/connection.json`; see
[backend setup](../docs/demo-backend.md).

## Snapshot domain counts

| Domain | Topics |
|---|---:|
| Biology & nature | 4,328 |
| Chemistry & materials | 1,027 |
| Computing & information | 657 |
| Earth & environment | 1,043 |
| Economics & organizations | 654 |
| Engineering & transport | 2,088 |
| Food & agriculture | 940 |
| Games & sports | 895 |
| Geography & travel | 5,049 |
| Health & medicine | 1,106 |
| History & culture | 3,128 |
| Home & crafts | 481 |
| Learning & language | 753 |
| Literature & storytelling | 350 |
| Mathematics | 1,124 |
| Mind & behavior | 236 |
| Music & performance | 923 |
| Philosophy | 265 |
| Physics & astronomy | 2,222 |
| Politics & law | 1,189 |
| Religion & spirituality | 1,159 |
| Society & relationships | 1,349 |
| Visual arts & design | 671 |
