# Whole Galaxy and dashboard implementation plan

**Goal:** Integrate the approved whole-catalog map and a shared-state extension dashboard.
**Architecture:** Precomputed public geometry/neighbor asset; reusable canvas map;
existing local bridge/state shared by side panel and dashboard.
**Tech stack:** Python/NumPy/UMAP/MDS, MV3 JavaScript, Canvas, CSS.
**Spec:** ../specs/2026-10-03-whole-galaxy-dashboard.md

## Constraints and review focus

Original 768D vectors; fixed UMAP+15% parameters; stable existing topic-string IDs;
no experiment overlays, no user-data upload, explicit save/focus actions.
Review stale or mismatched caches, invalid neighbor IDs, empty/sparse personal state,
language/state changes during camera interaction, and custom interests without positions.

## Tasks

1. [x] Preprocessing and asset: independent Python generation, versioned atomic cache,
   numerical/identity tests, real-data build and comparison against original prototype.
   Own `galaxy/`, `scripts/build_galaxy.py`, `requirements-layout.txt`, Python tests,
   and `data/galaxy-layout.json`. Asset contract is in the spec.
2. [x] Reusable Galaxy renderer: pure asset/search/camera helpers plus canvas UI,
   accessible controls, bilingual copy, true neighbors, domain filter and gestures.
   Own `extension/ui/galaxy*` and `extension/tests/galaxy*`; consume catalog and asset.
   Export `createGalaxyMap({container,catalog,layout,state,language,onSave,onFocus,onSearch})`
   returning `{update({state,language}),destroy(),getViewState()}`; accept optional
   `viewState` to restore camera/search/filter/selection on application rerender.
3. [x] Product integration: load static assets once, use renderer for Map, preserve
   view state across rerenders. Add dashboard shell, shared-state launch entry,
   safe explicit preview, responsive styles, build packaging and docs.
4. [x] Verify/review: unit and API regressions, actual data/cache checks, isolated
   browser checks at 320/390/desktop for both product routes, screenshot inspection,
   independent code review and fixes; package, commit on product branch and open preview.

Status and commands are recorded in docs/galaxy-verification.md after execution.
