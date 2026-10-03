# Specific discovery extension verification

Verified locally on 2026-10-03, extension version 0.1.5, on
`codex/otherwise-development`. Upstream `master` recommendation changes were
merged in `36f0eb8`, preserving local Galaxy/Focus development.

## Card simplification in 0.1.6

The full per-card feedback fieldset and all its controls have been removed from
both Cards and List views. Source details, Google/YouTube, Save interest and Not
for me remain. Previously saved feedback remains local and retains management
controls. The original verification below records the 0.1.5 integration; its
feedback-entry UI descriptions are historical.

## Implemented behavior

- Discover switches between the existing broad catalog and sourced graph concepts.
- Specific cards retain graph paths, public source links, optional reading levels
  and achieved/requested exploration reserve counts.
- Curious, Known and difficulty are independent explicit browser-local ratings.
  Saving or undoing reranks the last valid request with the same seed and exposure
  snapshot. Known hides the concept without approving an interest.
- Saved ratings survive reload and synchronize across extension windows. Individual
  clear, one-step undo and clear-all are available. Reset clears unsaved drafts in
  peer windows, not just the initiating window.
- Specific requests send saved interests, explicit ratings and area recommendation
  counts. Broad requests retain their previous format. The backend uses ephemeral
  profiles and persists only public embedding arrays.
- Existing title IDs, saved interests, original catalog/map assets, Galaxy and Focus
  are retained. Graph concepts outside the catalog do not receive invented positions.

## Verification results

| Check | Result |
|---|---|
| Complete Python suite, including real-model opt-in checks | 345 passed |
| Complete extension Node suite using bundled Node 24 | 163 passed |
| Real MPNet graph API | 10 Gardening results; correct sources and distance band; Known excluded; deterministic replay |
| Real packaged extension + local model service | Broad/Focus/discovery APIs, source rendering, feedback rerank and undo passed; 2 broad, 8 Focus and 3 discovery requests |
| Isolated graph UI fixture | Seven requests; feedback/sync/undo, bilingual drafts, failure recovery, clear/reset and privacy checks passed |
| Existing UI regression script | Pagination, settings drafts, language/layout persistence and zero outbound requests passed |
| Existing map workspace regression script | Independent centers, retained cameras, keyboard navigation, local neighbors and guidance passed |
| Specific layout | No horizontal overflow at 1440, 390 and 320 pixels; screenshots inspected |
| Packaging | Self-contained unpacked folder and ZIP built; matching manifest/package version 0.1.5 |

The real-model tests use cached public `all-mpnet-base-v2`, 768 dimensions,
3,642 concepts and 69 areas. All browser profiles and interests are fictional.
The UI fixture checks interface behavior; the separate real-service browser run
checks the actual extension-to-MPNet request path. Native Chrome permission dialogs
are not automated: isolated test copies pregrant loopback access. Production
permissions remain optional. No teammate service, public tunnel, deployment or real
browsing profile was used, and these checks do not establish recommendation quality
or user knowledge.

## Reproduce

Use the project Python environment and Node 22 or newer (verified with Node 24):

```sh
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 OTHERWISE_RUN_REAL_DISCOVERY=1 OTHERWISE_RUN_REAL_FOCUS=1 python -m pytest -q
npm test
python scripts/build_extension.py
node scripts/test_discovery_browser.mjs
node scripts/test_extension_browser.mjs
node scripts/test_ui_browser.mjs
node scripts/test_map_workspace_browser.mjs
```

Browser scripts require Playwright and Chromium. Set `OTHERWISE_PLAYWRIGHT_MODULE`
and `OTHERWISE_CHROMIUM` when using a separate bundled runtime. Real-service checks
require cached MPNet weights and the public catalog embedding cache. QA files are
ignored by Git under `.cache/qa/discovery/`, `.cache/qa/ui-preferences/`,
`.cache/qa/map-workspace/` and `.cache/qa/runtime-*.png`.

Restart the updated host backend and reload the unpacked extension to use the new
endpoint. This local verification did not update an already installed extension,
restart a teammate service or publish the branch.
