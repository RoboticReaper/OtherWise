# Recommendation experiments implementation plan

Goal: Build runnable recommendation variants, a reproducible evaluation boundary, and a bounded improvement loop with separate champions for four objectives.

Architecture: Preserve the existing engines as controls. A new `recommendation_lab` package owns source-backed identities, meaning resolution, global lexical/semantic/graph retrieval, local ranking, blinded grading packets, scorecards, and experiment artifacts. Inject vectors in unit tests; use the cached MPNet snapshot for real runs. Keep production routes and the pinned map unchanged until selection.

Tech stack: Python, NumPy, SQLite FTS5, existing sentence-transformers, pytest. No additional dependencies.

Spec: [approved design](../specs/2026-10-07-recommendation-system-design.md).

## Global constraints

- Work inline on `codex/recommendation-experiments`; the user explicitly requested implementation. Preserve private pilot material in ignored storage.
- Identity merges require shared QIDs or reviewed mappings. Alias ambiguity must yield choices. Unrecognized phrases remain usable without invented identities.
- Keep inventory, source texts, model revision, controls, evaluator rubric, and split identities in artifacts. Never feed evaluator grades to a serving ranker.
- Eligibility precedes retrieval truncation; enforce all-interest lower bounds and actual-result overlap quotas. Graph membership is an optional signal.
- The user selected the session assistant as evaluator. Store method-blind item judgments with immutable content keys. No paid external calls are needed; missing grades remain unavailable.
- Benchmark results select experimental proxy champions; deployment and claims about actual personal curiosity are separate.

## Review focus

1. Alias/source collisions silently select a meaning — covered by inventory/resolution tests, including Go and both Fermentations.
2. Retrieval drops globally eligible concepts or path mode suggests something near another interest — covered by application tests.
3. Sparse lists, missing grades, duplicates, or stale content inflate metrics — covered by scorecard tests.
4. Tuning uses held-out data or never stops — covered by bounded search and split-lock tests.
5. Model/cache revisions or invalid external orders are silently reused — covered by runtime fingerprint and reranking fallback tests.

### Task 1: Inventory and resolution

Interfaces: `Inventory.from_sources(broad, graph, registry)`, `resolve(interests, inventory_version)`; concept IDs and source variants consumed by Task 2.

- [ ] Write failing tests for source-only merging, label-edit stability, ambiguity, explicit choices, stale versions, forged meanings, known aliases, and unresolved phrases.
- [ ] Implement `recommendation_lab/inventory.py` and a reviewed public identity/alias registry.
- [ ] Run `.venv/bin/python -m pytest -q tests/test_recommendation_inventory.py`. Expected: all tests pass after observed RED.

### Task 2: Executable local systems

Interfaces: `RecommendationLab.recommend(request, variant, config)` returns a versioned batch; identical request/content records consumed by Task 3.

- [ ] Write failing boundary tests using real deterministic vectors for V0/V1 routing, V2 identities, V3 channel ablations, global/path geometry, quotas, feedback, and reproducibility.
- [ ] Implement local systems and FTS5 reciprocal-rank fusion; retain graph provenance and expose score components. Add an optional bounded reranking adapter with validated ID permutations and explicit fallback.
- [ ] Run `.venv/bin/python -m pytest -q tests/test_recommendation_systems.py`. Expected: all pass after observed RED.

### Task 3: Frozen grading and metrics

Interfaces: packet keys bind profile/concept/presentation/rubric/evaluator; scorecards consume batches from Task 2 and frozen grades, never the serving ranker.

- [ ] Write failing tests for exact formulas, requested-slot denominators, duplicate/known/source gates, incomplete grades, version invalidation, independent diversity vectors, and per-goal champions.
- [ ] Implement method-blind packet export/import, four scorecards, cross-metric reports, and Pareto diagnostics.
- [ ] Run `.venv/bin/python -m pytest -q tests/test_recommendation_evaluation.py`. Expected: all pass after observed RED.

### Task 4: Reproducible benchmark and bounded improvement

Interfaces: public benchmark families, runtime identity, frozen configs and grade store feed a bounded development-only search; sealed finalist run consumes nominations once.

- [ ] Write failing tests for cache revision identity, split-family isolation, tuning bounds/patience, missing-grade refusal, and held-out lock.
- [ ] Implement offline cached-model runtime, CLI, versioned manifests/raw outputs/reports, dev search, and held-out receipt. Document commands and grader workflow.
- [ ] Run `.venv/bin/python -m pytest -q tests/test_recommendation_benchmark.py`. Expected: all pass after observed RED.

### Task 5: Real comparison, review, and commit

- [ ] Run all local variants on frozen public development cases; export a randomized blind packet and grade it as the session evaluator before inspecting method scores.
- [ ] Run bounded development configurations, freeze nominations, then evaluate the separate held-out families once. Record uncertainty and evaluator limitations. No automatic deployment.
- [ ] Request one fresh whole-change review, address material findings with regression tests, and run the full Python suite plus relevant existing client checks. Expected: no regressions.
- [ ] Commit public implementation, benchmark evidence, and documentation on the feature branch; exclude all personal pilot data. Leave the branch available for review.

Plan self-review: interfaces are sequential and compatible; identity resolution is shared, baseline meanings remain unchanged in V0/V1, metric keys include presentation/evaluator versions, and held-out selection does not enter tuning.
