# Discover Save Retention Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement inline.

**Goal:** Keep the current Discover batch usable after Save until leaving/reloading or receiving fresh recommendations.
**Architecture:** Retain one trusted batch and its provenance in the reducer, with a unique token. A small UI session helper only permits retained display for an already-open batch. Search resolves retained records through the controller.
**Tech Stack:** Existing vanilla JavaScript reducer/controller/UI and Node tests.
**Spec:** docs/superpowers/specs/2026-10-08-discover-save-retention.md

## Global Constraints

- Automatic refresh off sends no new request.
- Request generation invalidation and privacy/reset clearing remain intact.
- Retained batches stay outside recommendation request payloads.
- Preserve current UI and concurrent work; integrate locally and rebuild the extension.

## Review Focus

- Noncatalog specific concepts remain searchable and savable after the first Save.
- Multiple Saves, dismissal and navigation preserve or expire the correct batch.
- New empty responses replace retained results; equal timestamps still distinguish batches.
- Source interest, topic selection and batch time stay accurate after Save changes focus.
- Privacy, removals, reset and late response guards cannot revive a deleted batch.

### Task 1: Retain trusted action data

Files: extension/core/index.js, extension/controller.js, extension/tests/discovery-session.test.js.
- [x] Add and run regression tests: expected retained topics/search; observed missing batch and rejected search, 3 failures.
- [x] Add recommendationBatch metadata, preserve it only across successful additions, clear it on invalidation, and resolve searches from it.
- [x] Run focused tests; expect all passing.

### Task 2: Scope display to the open page

Files: extension/ui/discovery-session.js, extension/ui/app.js, extension/tests/discovery-session.test.js, scripts/test_ui_browser.mjs, docs/extension-guide.md.
- [x] Add failing UI session tests for Save retention, cursor/provenance, reentry/reload expiration, replacement/empty responses and migration.
- [x] Wire session items into Discover rendering/actions; keep focus after Save.
- [x] Run Node suite, build and verify actual Save/Next/multiple Save/refresh/reentry in sidepanel and dashboard through CUA.
- [x] Independently review, integrate with three-way merges and verify the primary build.
- [x] Archive the temporary worktree and close preview resources.

## Execution record

Diagnosis: regression exercises the actual reducer/controller Save path. `addTopics` calls unconditional invalidate; the autoRefresh flag only controls subsequent fetching. Further speculative hypothesis probes are unnecessary after direct deterministic reproduction. Changes remain local without commits.

Task 1: reducer/controller regressions RED (3 failures) → GREEN (3 passed). Task 2: session helper absent → RED; implementation → GREEN (9 focused cases); full Node suite 235/235 and build passed.

Independent review found an important path-search provenance issue and a minor conflicting Adjust source. Added an actual-controller regression for multiple Saves: RED (Botany instead of Gardening) → GREEN after retaining the batch mode/focus for search lineage; Adjust now uses the same batch source. No other critical or important findings. Final focused cases: 10/10; primary Node suite: 236/236. Browser regression script and app syntax checks passed.

Integrated 10 owned files with clean three-way merges, retaining concurrent guide edits and verifying 43 unrelated files unchanged. Primary extension build succeeded; all 57 packaged extension source files match the unpacked directory and ZIP, ZIP integrity passes, and INSTALL.md matches the guide.

CUA exercised the offline preview from the primary build: 390px sidepanel Save keeps Botany, 1/4, original source/time; Next and another Save keep Landscape architecture at 2/4; Browse retains all four items; remaining-topic Search works; manual refresh replaces with two items; saving then leaving/reentering expires the old batch; Find ideas fetches the remaining item. A new UI boot with an already-invalidated fixture hides the old batch and fetches three current items on demand. At 320px the document width equals the viewport. At 1280×900, Save retains the four-item Browse list and Saved marker; a fresh batch preserves Ecology selection across navigation. No preview console warnings/errors. Automatic refresh timing, service-worker restart and canonical noncatalog Search were verified by controller tests; a live Chrome extension/backend session was not used. Screenshots are saved in the task visualization directory.
