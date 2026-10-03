# Interest exploration implementation plan

**Goal:** A working notebook for tunable topic discovery from a fixed catalog.

**Architecture:** `explorer.py` owns embedding preparation and reusable vector search. `interest_explorer.ipynb` displays the experiment using `data/topics.json`.

**Tech stack:** Python, Sentence Transformers, NumPy, pandas, matplotlib, Jupyter widgets.

**Spec:** [design.md](design.md)

## Tasks

- [x] Write behavior tests using known vectors for search-band limits, nearest-interest geometry, duplicate exclusion, overlap quota, diversity and invalid/empty input; confirm failure before implementation.
- [x] Implement reusable search and local embedding helpers, then pass the tests.
- [x] Author a catalog of meaningful topic phrases and descriptions across broad domains.
- [x] Create the notebook with editable interests, baseline comparison, exact distance plot, optional projection, controls and a distance-sweep experiment.
- [x] Execute the notebook with real embeddings, inspect recommendations and rendered figures, and document how to run it.

## Review focus

Empty or duplicate input; a band with no catalog coverage; results familiar to any of several disjoint interests; more overlap than promised when fewer results exist; plots that suggest distances different from those used by the algorithm.

## Progress

The workspace contains an empty main.py and an existing Python 3.13 virtual environment, with no Git repository. Work stays in this workspace. Local model inference is the default to avoid API credentials; the first run requires downloading public model weights. A website is explicitly deferred.

Implemented 144 authored topics in 12 domains, with a reusable engine and a 19-cell notebook. All 26 numerical and input-handling tests pass. Real model checks covered gardening, machine learning with photography, and classical music. Notebook controls were exercised with multiple interests, empty input, and an empty search band. Inspected the rendered distance histogram and PCA projection.

Final review found punctuation-based conflation of C++, C# and C, and an empty baseline table error. The punctuation regression was reproduced, fixed, and tested; the baseline table now retains its columns even with no rows. The final notebook execution includes that empty-baseline case.

## Catalog expansion and model update — October 2, 2026

Expanded the catalog to 5,228 unique topic titles across 64 domain labels:
718 authored general-interest entries and 4,510 OpenAlex research topics after
removing six repeated titles. The research snapshot represents 26 fields and
245 subfields. Source metadata, coverage counts, and duplicate records are saved
in `data/catalog_metadata.json`; `data/README.md` explains provenance and coverage.
All original 144 entries retain their titles, domains and descriptions.

Switched to the user-requested `sentence-transformers/all-mpnet-base-v2` model
with 768-dimensional embeddings, preserving the existing MPS device setting.
Refreshed notebook descriptions and examples for the expanded local catalog.

## Balanced catalog and parameter guidance — 2026-10-02

Replaced the default research-heavy catalog with 3,452 topics across 23
broad domains, capped at 160 topics per domain. Preserved the prior OpenAlex
snapshot in data/archives. Added a reusable, cached Wikimedia/Wikidata importer
with provenance, filters and source-subsection rotation.

Added bounded ranking randomness with optional repeatable seeds, gentler defaults,
parameter ranges, three presets, live candidate counts and a randomness experiment.
Distance eligibility and familiar-overlap limits are unchanged.

Validation: 33 behavior tests passed; the full 24-cell notebook executed with
real 768-dimensional MPNet embeddings. Checked seven interests across all three
presets, repeatable and fresh-seed widget searches, empty-input recovery, catalog
rebuild reproducibility, and rendered coverage, distance and projection plots.
