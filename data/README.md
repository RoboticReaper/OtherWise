# Catalog coverage and sources

The default fixed catalog contains **3,452 unique topic titles across 23 broad domains**.
Every entry includes a title, description, domain and source. Embeddings use title
plus description. No source API is needed when running recommendations.

## Why this source

The previous catalog contained 4,510 OpenAlex research topics and 718 authored
interests: about 86% research. OpenAlex is useful for scholarly discovery but was
an uneven default for general interests. That catalog and its metadata are kept
under `archives/`.

The replacement uses [Wikimedia's expanded list of articles every Wikipedia should have](https://meta.wikimedia.org/wiki/List_of_articles_every_Wikipedia_should_have/Expanded),
a community-curated general-knowledge list spanning arts, society, science,
history and everyday life. The linked Wikidata entities supply short English
concept descriptions. These are community-maintained descriptions, not generated
summaries. They vary in detail and can contain errors.

## Selection and balance

- Retain 718 authored ProductSpace topics for practical, everyday interests.
- Import 2,734 Wikidata concepts from the curated guide.
- Cap every broad domain at **160 entries**. Rotate through source subsections,
  prioritizing bold foundational entries within each subsection.
- Keep short domains short instead of inventing quota-filling labels.
- Exclude the biography section and sections devoted to individual works,
  buildings, companies or educational institutions. Also exclude entities directly
  marked as humans, disambiguation pages or lists, and entries without a useful
  English description (at least three words).
- Deduplicate normalized titles and imported Wikidata IDs while preserving
  meaningful punctuation such as C++. Related concepts and synonyms can remain. Six reviewed shorthand or ambiguous
  guide titles use clearer Wikidata labels (for example, Country becomes Country
  music); the original `guide_title` is retained, and title deduplication is applied.

This balances broad-domain counts; it does not guarantee cultural neutrality,
equal subtopic representation, equal recommendation frequencies or completeness.
Countries, species and historical events are included alongside abstract concepts.
Authored entries retain their descriptions, with domains regrouped for this catalog.

## Provenance and licensing

Snapshot: **2026-10-02**. `catalog_metadata.json` records exact counts and
selection rules. Imported entries include `wikidata_id`, `source_url`,
`source_revision`, `list_section`, `list_revision` and `subsection`.

Wikidata's structured labels and descriptions are
[CC0](https://www.wikidata.org/wiki/Wikidata:Licensing).
The Wikimedia guide's selection/structure is attributed above under
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/); our derived
selection and grouping are modifications. Per-entry revision IDs identify the
source snapshots. The retained original authored catalog is `curated_topics.json`.

## Rebuild the fixed catalog

From the project directory:

```sh
.venv/bin/python scripts/import_balanced_catalog.py
```

The importer uses the public Meta-Wiki and Wikidata APIs, fetching in sequential
batches and caching responses under `.cache/wikimedia-sections` and
`.cache/wikidata-concepts`. It reuses these snapshots on repeat runs. To intentionally
refresh the source, move those two cache directories aside first. This can change
selected topics and therefore recommendations. Normal notebook runs never import
or update the catalog.

For a human-waiting interactive refresh, `--interactive` omits the optional maxlag
parameter, consistent with [MediaWiki guidance](https://www.mediawiki.org/wiki/Manual:Maxlag_parameter).
The default unattended mode sends maxlag=5 and retries server-lag responses.

## Domain counts

| Domain | Topics |
|---|---:|
| Biology & nature | 160 |
| Chemistry & materials | 160 |
| Computing & information | 160 |
| Earth & environment | 160 |
| Economics & organizations | 160 |
| Engineering & transport | 160 |
| Food & agriculture | 160 |
| Games & sports | 160 |
| Geography & travel | 160 |
| Health & medicine | 160 |
| History & culture | 160 |
| Home & crafts | 121 |
| Learning & language | 160 |
| Literature & storytelling | 111 |
| Mathematics | 160 |
| Mind & behavior | 77 |
| Music & performance | 160 |
| Philosophy | 110 |
| Physics & astronomy | 160 |
| Politics & law | 160 |
| Religion & spirituality | 160 |
| Society & relationships | 160 |
| Visual arts & design | 153 |
