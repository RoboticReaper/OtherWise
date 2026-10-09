# Scale pilot 001 — revision 002

Validated candidate revision after the approved current-inventory cleanup. **1,000 cards: 715 new and 285 existing identities.** The current baseline contains 35,032 IDs. The original delivery remains unchanged.

- [Current combined candidate](catalog.json) and [review](../../../../docs/catalog-scale-pilot-001-revision-002-review.md)
- Revised batches: [003](research-batch-003.json), [004](research-batch-004.json), [005](research-batch-005.json), [006](research-batch-006.json), [007](research-batch-007.json)
- [112 reviewed meaning decisions](reconciliation-decisions.json), [legacy redirects and changed records](revision-lineage.json), [assembler decisions](identity-decisions.json)
- [Full current pinned baseline](baseline-manifest.json), [identity index](baseline-index.json), [original source rows](baseline-imported-records.json)
- [Recomputed metrics](catalog-metrics.json), [structural checks](structural-validation.json), [combiner verification](combiner-verification.json), [40 unit tests and repeat-build proof](unit-tests-and-rebuild.json)
- [12 actual-output regressions](data/catalog-candidates/scale-pilot-001/merge-validation/actual-regressions/revision-002-20261008/regression-results.json)
- Source reviews: [part 01](research/part-01.review.md), [part 02](research/part-02.review.md), [part 03](research/part-03.review.md), [four additional controls](research/supplemental-controls.review.md)

`catalog.json` and the five listed revised candidates are the selected revision artifacts. Baseline snapshots, original delivery, research inputs and regression mutations have separate roles. Candidate input status fields describe construction; the hash-bound completion manifest and verification reports establish acceptance of this revision.

For the next catalog selection, rebuild a working index from the actual operational inputs, active candidates 001/002, and this revision's catalog. Apply `revision-lineage.json`'s reviewed legacy redirects in that working index, retaining all original provenance. This revision's `baseline-index.json` records the inventory **before** admitting these pilot cards, so it alone is insufficient for subsequent generation. Preserve the four older explicitly deferred identity proposals until separately reviewed.

The relative links under `data/catalog-candidates/` select these same files for the unchanged regression harness. Synthetic cases are isolated and do not count as research.

To reproduce from the project root:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 data/catalog-candidates/scale-pilot-001/revision-002/tools/build_revision.py
PYTHONDONTWRITEBYTECODE=1 python3 data/catalog-candidates/scale-pilot-001/revision-002/tools/verify_revision.py
```

The build rejects changed protected inputs or incomplete reviews. Reusing unchanged pinned inputs reproduces identical selected bytes. For a changed inventory or new review, create a subsequent documented revision instead of replacing this evidence.
