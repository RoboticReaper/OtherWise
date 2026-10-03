# OtherWise Extension MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver the approved English Chrome extension, local privacy pipeline, real recommendation API and a usable shared demo.

**Architecture:** Pure JS privacy/state core behind a Chrome service worker; accessible sidepanel UI speaks a fixed bridge. Python FastAPI wraps existing MPNet search, caches catalog embeddings, accepts only confirmed interests and is exposed via an authenticated temporary tunnel.

**Tech Stack:** Native ES modules/CSS/SVG, Chrome MV3, Node built-in tests, Python 3.13, FastAPI, pytest; isolated Chromium browser checks.

**Spec:** docs/superpowers/specs/2026-10-03-extension-mvp.md

## Global Constraints
- English, Chrome history/YouTube visits only, local extraction, no source history transmitted.
- User authorized immediate execution; do not repeat design approval. Work on codex/otherwise-development; no push.
- Data-source permission, local analysis consent and automatic refresh are separate. Initial defaults off.
- Known schema is in spec; never send unapproved topic or local evidence. Global level max 8; no automatic change on clicks.
- Interfaces fixed before independent tasks run. Agents own disjoint files; controller handles integration and reviews.

## Review Focus
- Missing/stale YouTube titles and repeated history events must not create junk or inflate evidence.
- Revocation/deletion while requests are pending must not resurrect data or upload stale profiles.
- Keyword content must not leak through validation errors, query strings, logs or preview fallback.
- Empty catalogs/bands and invalid credentials must show recoverable errors, never fabricated recommendations.
- Narrow side panels and large topic groups must remain operable by keyboard and fit the viewport.

### Task 1: Recommendation service
**Files:** service/*.py, main.py, requirements.txt, tests/test_api.py, tests/test_service.py; narrow change explorer.load_model for optional device selection.
**Interfaces:** exact wire contract in spec; create_app(engine=None, token=None) for testing; production engine loads real MPNet and cached catalog vectors.
- [ ] Write failing auth/schema/route tests plus deterministic path/global/known-topic/range tests.
- [ ] Verify failures; implement bounded stateless service, constant-time token check, cache and sensible CPU/MPS detection.
- [ ] Run full Python suite and real inference request. Record tests and implementation report.

### Task 2: Local state and privacy core
**Files:** extension/core/*.js, extension/tests/core.test.js.
**Interfaces:** index.js exports and exact state/actions from spec; no Chrome API in pure core.
- [ ] Write failing tests for local extraction, URL exclusions, candidate review, payload allowlist, repeated confirmation, stale generations, deletion/expiry/pause.
- [ ] Implement core and adapters with immutable reducer and catalog matching; no raw history persisted.
- [ ] Run Node full core suite and self-review cross-action sequences. Record report.

### Task 3: Sidepanel and map
**Files:** extension/sidepanel.html, extension/ui/*, extension/assets/* as needed.
**Interfaces:** bridge.js functions from spec; both full-tab and sidepanel render same app; strict production/preview separation.
- [ ] Build functional English onboarding/inbox/interest/recommendation/map/settings layouts against contract.
- [ ] Include editable manual interests, candidate approval/dismissal, mode selection, connection/consent controls, searches and reset confirmation.
- [ ] Verify at 390px and full-width with synthetic preview; interactive map labels and keyboard operation. Record report.

### Task 4: Chrome integration and demo tooling
**Files:** extension/manifest.json, background.js, bridge.js, dev-preview.js; scripts/build_extension.py, scripts/start_demo.py, scripts/stop_demo.py, launchers; tests/background and runtime integration.
**Interfaces:** binds core and UI; generates bundled catalog from data/topics.json; makes authenticated POST only through background worker.
- [ ] Write integration tests that enforce sender validation, consent gating, in-flight invalidation and history deletion with an isolated mocked Chrome boundary.
- [ ] Implement single serialized state queue, awaited writes, event guards, delayed title reconciliation and privacy generation checks.
- [ ] Add reproducible ZIP build and local launcher/token management; download cloudflared only for authorized demo sharing.
- [ ] Run actual extension in isolated Chromium with synthetic history and real local API, capture UI screenshots, check network payloads and errors.

### Task 5: Review and handoff
- [ ] Independent cross-system review, repair important findings with regression tests.
- [ ] Run full Python/JS/browser checks once final changes land, verify real authenticated shared endpoint.
- [ ] Write user install/demo guide, package extension and launchers. Commit coherent changes locally, no remote push. Record exact results and limitations.
