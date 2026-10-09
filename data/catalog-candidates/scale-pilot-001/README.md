# Scale pilot 001

The delivered pilot contains five 200-card candidates and a combined 1,000-ID catalog. Delivered files are preserved unchanged.

**Current candidate: [revision 002](revision-002/README.md), validated after current-inventory reconciliation and both source corrections.** It contains 1,000 cards, including 715 new identities against the full current baseline. [current.json](current.json) identifies the selected revised artifacts. Operational import has not occurred.

- [Local delivery review](../../../docs/catalog-scale-pilot-001-review.md)
- [Completed reconciliation review](../../../docs/catalog-scale-pilot-001-revision-002-review.md)
- [Original worker report](../../../docs/catalog-scale-pilot-001-results.md)
- [Fresh independent source review](../../../docs/catalog-scale-pilot-001-source-review.md)
- [Combined delivered candidate](catalog.json)
- [Fresh structural results](local-review/structural-validation.json)
- [Current-inventory meaning-review queue](local-review/current-baseline-reconciliation.json)
- [Verified wording/citation correction proposals, applied in revision 002](local-review/card-corrections.json)
- [Original archives and receipt](../archive/scale-pilot-001-delivery/receipt.json)

The root `catalog.json` and project-level candidates `research-batch-003.json` through `research-batch-007.json` remain the original delivery. The five candidates and `catalog.json` inside `revision-002/` are the current revised candidate. Historical checkpoints, baseline snapshots and synthetic regression mutations have separate roles; use the current pointer rather than recursively treating every JSON file as a catalog input.

Complete original evidence is preserved in `../archive/scale-pilot-001-delivery/evidence/`. Bundled scripts were inspected before fresh local test execution. Fresh local verification artifacts are distinguished from the original delivered regression run. Downloads originals are retained.
