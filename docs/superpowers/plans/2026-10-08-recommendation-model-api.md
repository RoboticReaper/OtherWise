# Recommendation Model API Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Make the study candidates, baselines and a controlled trajectory/history pair usable through the backend with optional interest dates.

**Architecture:** Extend the existing lab without altering historical ranking policies. A serving adapter shares the initialized production embeddings and exposes a registry through the authenticated API. History computation lives in a separate module and stays request-local.

**Tech Stack:** Python, NumPy, SQLite FTS5, FastAPI, Pydantic, pytest; no new dependencies.

**Spec:** `docs/superpowers/specs/2026-10-08-recommendation-model-api-design.md`

## Global Constraints

- Preserve legacy requests and frozen benchmark data; keep unrelated catalog edits intact.
- Interest dates are optional; no fabricated timestamps or persistent profiles.
- All public API input remains authenticated, bounded and validated without echoing rejected data.
- Current user authorization covers implementation of the discussed design and dated-interest contract; proceed in the existing workspace.

## Review Focus

- Equal dates, reordered history and repeat interests must not invent movement.
- Switching between independent interests must not become one global trajectory.
- Path focus must retain global known exclusions.
- API worker threads must be able to use the initialized lexical index.
- Failed initialization and ambiguity must not look like ready/successful recommendations.

### Task 1: Shared selectable models and simple baselines

Files: `recommendation_lab/models.py`, `recommendation_lab/systems.py`, `tests/test_recommendation_models.py`.
Produces: immutable `MODEL_SPECS`, `get_model(name)` and lab variants `semantic-nearest`, `BM25`, `random`.

- [x] Write and observe failing behavioral tests for the baselines.
- [x] Implement canonical nearest ranking, lexical-only ranking and seeded sampling with common identity exclusions.
- [x] Verify existing K/V variants and new baseline tests.

### Task 2: Dated interest history and matched trajectory pair

Files: `recommendation_lab/history.py`, `recommendation_lab/inventory.py`, `recommendation_lab/systems.py`, `tests/test_recommendation_history.py`.
Produces: `HistoryConfig`, validated date parsing, strand profiles and `history-recency`/`trajectory` variants.

- [x] Write and observe failing tests for optional dates, repeats and directional recommendations.
- [x] Implement time-sorted strands, tangent regression, confidence/fallback, shared expansion ranking and path-aware known exclusions.
- [x] Verify reordered/equal-date/multistrand histories, unsafe input and unchanged static variants.

### Task 3: Backend model selection and real readiness

Files: `service/models.py`, `service/api.py`, `tests/test_model_api.py`, `docs/recommendation-model-api.md` and candidate-status notes.
Consumes: registry and the public lab `recommend` boundary. Produces: `ModelEngine`, `/api/recommend/models` and model-selected `/api/recommend` requests.

- [x] Write and observe failing authenticated HTTP tests for selected models and dated interests.
- [x] Share public vector caches, keep interest encodings request-local, and make lexical access safe across API threads.
- [x] Test failed readiness, meaning/version conflicts, validation privacy and legacy compatibility.
- [x] Document exact model IDs and runnable dated/undated request examples.
- [x] Run the full suite, perform real-model HTTP checks on every selectable model, and obtain independent standards/spec review. Fix material findings and record verification.

## Progress

- Baseline: 151 passed, 1 skipped across recommendation systems/known policy/API/discovery service using `.venv/bin/python -m pytest`.

- Final application suite: `.venv/bin/python -m pytest -q tests --tb=short` — 541 passed, 4 skipped. Demo lifecycle checks ran with access to temporary loopback sockets and test-owned process inspection.
- Real cached MPNet HTTP verification: all 16 selectable models in both result kinds plus the history pair in each kind — 36 successful requests against 31,637 broad topics and 3,642 specific concepts. The dated fixture used active velocity in both result kinds; the matched recency control did not. This confirms readiness, not an expansion effect.
- Syntax verification: `.venv/bin/python -m compileall -q recommendation_lab service`. No static typechecker is configured in this Python repository.
- Standards review: fixed lifecycle resource reopening, deterministic dated-alias anchors and invalid timezone offsets. Review found no documented-standard violation.
- Spec review: fixed false motion from stationary snapshots, expired-direction reporting and legacy serving meaning/known guards. Raw historical lab behavior remains preserved; guarded API algorithm identity is distinct. Regression tests demonstrated failures before the fixes and pass afterward.
