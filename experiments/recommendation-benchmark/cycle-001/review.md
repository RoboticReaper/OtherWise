# Recommendation implementation review

Two fresh reviews checked specification/plan compliance and repository engineering standards across the complete implementation. Material findings were reproduced with failing tests, corrected, and covered by regression tests.

- Path-mode overlap quotas now classify distance to every interest while preserving the focus band.
- Source and identity gates verify the trusted inventory and exact source-backed presentation. Authored equivalent concepts retain authored provenance. Batch-level invalidity and wrong automatic resolutions also invalidate empty lists.
- Explicit meanings must belong to the displayed five-choice set; stale and forged selections are rejected.
- Graph membership is an optional hybrid signal. Orphan concepts can remain eligible without fabricated graph paths.
- External reranking has an enforced bounded wait, one occupied worker per lab, validated supplied-ID permutations, and explicit local fallback.
- Existing frozen grades cannot be overwritten. Conflicts require a new evaluator version.
- Cache/report temporary writes are unique and atomic. Nomination and held-out claim publish complete files atomically with exclusive creation.
- Family-bootstrap resampling preserves paired profile labels and counts independent families.
- Legacy request validation runs before downstream lookup; existing engine defaults and map contracts remain compatible.

Final verification: full Python suite **403 passed, 2 skipped**, with one pre-existing Starlette/anyio warning; extension suite **164 passed**. The backend suite needs the normal local process/socket permissions used by existing demo-runtime tests. Focused recommendation tests cover 60 cases, including the review regressions. Public evidence validation recomputed all saved scores and verified 284 frozen judgments. No production provider or HTTP rollout was required for this local experiment stage.
