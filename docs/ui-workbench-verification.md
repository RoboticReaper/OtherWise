# Clean workbench and single-topic discovery

Verified locally on 2026-10-08. The approved direction is A (clean workbench), with B (one topic at a time) available as a Discover view.

## Result

- Three main navigation entries: Discover, Interests and Map. Settings lives in the header; the side panel has a compact Dashboard shortcut.
- Browse shows a topic chooser and one selected detail. In narrow panels a short chooser sits above the detail; each long region scrolls within the window.
- One at a time uses the same downloaded batch, with Previous/Next and a position counter. Switching views, pages and UI language retains the selected topic in the current window. On opening, the side panel starts Discover in One at a time, and the web Dashboard starts Discover in Browse. Manual switches are local to each page; reopening restores the surface default.
- Search opens Google/YouTube choices. Save interest remains visible. Additional topic actions, long descriptions, graph provenance, history review and settings expand on demand.
- The original navy night-sky palette, ivory text and pale sage accents remain fixed in both system appearances. Static color tokens retain the manifest's Chrome 116 compatibility; older Chrome itself was not run.
- Recommendation requests, saved-interest invalidation, privacy boundaries and Galaxy/Focus algorithms are unchanged.

## Verification

Used Node 24.19.0 and the installed Chromium with disposable profiles and fictional personal data. The fixture discovery service listened only on loopback.

| Check | Result |
| --- | --- |
| `npm test` | 190 passed, 0 failed |
| `npm run test:ui` | 19 checks passed, including independent surface defaults/reopening, 320/390/1100 px, fixed night-sky theme in both system appearances, shared selection, final-topic dismissal, hidden-field validation, page-local view and native map fullscreen |
| `npm run test:discovery` | 10 checks passed: specific concepts, source text, existing feedback/undo, failure recovery and reset synchronization |
| `node scripts/test_map_workspace_browser.mjs` | 5 checks passed: retained cameras/DOM, independent temporary Focus, keyboard return, saved interests and localized service guidance |
| `npm run test:galaxy` | 16 checks passed: real packaged catalog, synchronized language, gestures, narrow layouts, custom interests and offline overlays |
| `python3 scripts/build_extension.py` | Built the unpacked extension and ZIP with 31,637 catalog topics |

An independent code review identified collapsed connection errors, narrow selection visibility and newer-only color syntax. Each was fixed; the first two were reproduced with failing browser checks before the fixes. The final suites returned exit code 0. The UI suite verified that persisted map label changes retain native fullscreen.

Screenshots and detailed results are under `.cache/qa/ui-redesign/`; the combined record is `verification.json`. These are ignored local QA artifacts. The full test against the real model backend was not rerun for this presentation change. The user's installed extension was not reloaded or its profile changed.

## Try it

Reload the unpacked extension in Chrome and reopen its side panel. The refreshed package is `dist/otherwise-extension`, with `dist/OtherWise-extension.zip` for installation elsewhere. A local `dashboard.html?preview=1&view=discover` preview uses fictional samples without importing browser history.

## Surface default follow-up

The side panel and Dashboard now open Discover directly, with independent page-local layouts: One at a time in the side panel and Browse on the Dashboard. Manual switches survive navigation within that page; reopening uses its surface default. Explicit `view` URLs still open the requested page. The new opening/reopening check failed before implementation, then the full UI suite (19 checks) and unit suite (190 tests) passed. Logs for this follow-up are in `.cache/qa/ui-surface-defaults/`. The map/discovery checks above record the earlier redesign verification.

## Night-sky palette correction

Restored the original shared navy, ivory and sage tokens and the original page background gradients. Removed the workbench's system-dependent light/green overrides and declared a dark color scheme on both entry pages. Layout and surface defaults are unchanged. Rebuilt the extension; the unit suite (190 tests) and UI suite (19 checks) passed again, including both system appearances at 390/1100 px. Refreshed and visually inspected the existing Dashboard preview. Logs are in `.cache/qa/ui-star-theme/`.

## Window-height layout and interest landscape follow-up (2026-10-08)

Discover Browse, One at a time, saved/review interests and Galaxy now use the
remaining window height. Recommendation lists, descriptions, interest lists and
Galaxy details own their long-content scrolling. Search/Save and pagination stay
outside those scrolling regions. The getting-started guide retains normal page
flow. Galaxy layout controls and Display & key use native dialogs; narrow selected
details leave a strip for zoom/reset. Search selection dismisses its result overlay
and retains the query. Escape closes a modal before leaving native fullscreen.
Selecting a custom interest closes Display & key and focuses its topic heading.

The wide Interests page includes a local, factual interest landscape: unique saved
and explored counts, the top four known subject areas, separate unclassified/other
counts, and the latest three distinct searched topics. A narrow Overview button
opens the same content in a native dialog. No new stored data or service request
is added. Existing recommendation retention after Save is preserved, including
list and description scroll positions in the current batch.

Current verification uses the Codex in-app browser with fictional personal state
and the packaged public catalog. A loopback, no-cache preview adds 12 recommendations,
24 saved interests, 306 review candidates and a long description; its fixture is
outside the extension source. Before the change, a 1280×800 window measured 1095px
for Browse and 1184px for Galaxy. Updated pages measure 800px at that same viewport.
Browse and Galaxy also fit 390×850, 320×850 and 390×600; wide/narrow interest lists,
review footer, overview dialogs, long descriptions, Search/Save retention, custom
interest selection, map zoom, Focus return and both UI languages were checked.
Native fullscreen was entered; Escape closed each dialog while keeping fullscreen,
then exited fullscreen. Short windows use smaller surrounding margins so content
still has room. This is a page-preview check, not a test of the user's installed
extension or the model backend.

The Node suite passes 242 tests, including five new overview aggregation tests and
a regression test for fullscreen modal Escape order. Browser regression scripts
were updated for the new dialogs and height assertions and syntax-checked; their
full extension-profile suites were not rerun for this follow-up. Independent source
review found wide-interest alignment, narrow map-control overlap and custom-interest
dialog focus issues; all were fixed and reproduced in the page preview.

The unpacked extension and ZIP were rebuilt with 31,637 catalog topics. Their
runtime files and installation guide match the current source. The final preview
was refreshed from that source; proof and measurements are recorded in the ignored
`.cache/qa/compact-viewports/verification.json`, with three screenshots saved in
the current task's visualization directory.
