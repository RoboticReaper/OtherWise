# Semantic Focus and Galaxy exploration verification

Date: 2026-10-03. **OtherWise 0.1.4 is locally delivered and verified within the
boundaries below.** Final product implementation commit:
`f210ca7737295bc89da31b7886923f1fda886d1a` on `codex/otherwise-development`.
Independent whole-product review and scoped review of `7c55415..f210ca7` are approved,
with no residual findings after keyboard-focus restoration and the browser-test
paint synchronization repair.

This committed report, durable screenshots and delivery audit are the retained
release record. Temporary task scratch will be cleaned; it is not a required
location for understanding or checking this delivery.

## Test evidence and source checkpoints

Tests were run at documented integration checkpoints and affected checks were rerun
after later repairs. **The table does not imply that every command ran on the same
commit.** The final changes were keyboard-focus restoration and test-only paint
synchronization; earlier checks of unchanged areas remain applicable.

| Check | Actual recorded result | Source/evidence boundary |
| --- | --- | --- |
| Final extension build | Passed; 3,452 topics packaged | Latest integrated source; version `0.1.4` |
| Final Node suite | 153/153 passed | Latest integrated source |
| Final workspace browser suite | 5 checks passed | Includes keyboard-entry/return focus restoration |
| Final Galaxy interaction browser suite | 18/18 passed, zero errors | Corrected paint synchronization; production renderer unchanged |
| Galaxy interaction stability check | 3 concurrent runs, each 18/18 passed, zero errors | Test-only repair at `de1f9e3` |
| Python suite | 282 passed, 1 skipped | Earlier integration checkpoint `e33904d`; opt-in cached-vector check skipped by default; known existing Starlette deprecation warning |
| Opt-in real catalog check | 1 passed | Existing MPNet cache and packaged identity; earlier unchanged backend checkpoint |
| UI browser suite | 9 checks passed | Earlier integration checkpoint; isolated fixture profile |
| Real API browser suite | 19 checks passed | Earlier integration checkpoint; cached real service and temporary token; 2 Discover POSTs and 8 Focus POSTs |
| Packaged Galaxy browser suite | 15 checks passed | Earlier integration checkpoint; isolated extension/browser profile |
| Focus component browser suite | 15 checks passed | Earlier unchanged scene checkpoint; real renderer with synthetic geometry and controlled callbacks |
| Retry repair session units | 7 passed | `7c55415`, including the added retry regression; subsequently included in final Node suite |

The two Galaxy paint/color failures were diagnosed rather than discarded. A
controlled held-rAF experiment reproduced the old 40ms assertion sampling stale
paint. The test-only repair waits for actual rendered state; the production Galaxy
renderer was unchanged. The standalone and three concurrent green runs above
replace the failing measurement.

Task 5's pointer defect was independently closed at `c42eca6`: owner-window terminal
cleanup handles both captured drags and one-step direct exits before any in-map
movement. Its repair checks were 15 component, 1 focused direct-exit and 2 timing/
explicit-interruption checks passed. Task 6 integration and retry repairs were
independently approved. Final whole-product review found keyboard return focus
landing on the document body; the fix is now verified by the final workspace suite
and actual CUA interaction below. No open finding remains from these reviews.

## Version and real-vector identity

Source and delivered manifest versions are `0.1.4`. Final source-to-delivery checking
verified all 40 installed files and the ZIP; the audit records each file hash.

The separate Task 7 precision check ran once after adding `rel=0`:

```sh
OTHERWISE_RUN_REAL_FOCUS=1 .venv/bin/python -m pytest -q tests/test_focus_service.py -k real_catalog
```

Result: **1 passed, 21 deselected in 0.22s**, no warnings. The coordinator's integration
opt-in check also passed. `pytest.approx(..., rel=0, abs=1e-12)` prevents the default
relative tolerance from weakening the promised absolute precision.

The check uses the original catalog digest and raw contiguous embedding-cache bytes,
verifies model/dtype/shape against layout metadata, and compares returned distances
with independently normalized vectors at four real catalog centers. The cache has
3,452 rows, 768 dimensions and `float64` dtype. It verifies existing cached vectors,
not network model installation or encoding of new text. The builder includes all
extension sources except tests; the delivered files include the Focus scene,
session, transport, workspace and public assets.

## Actual CUA interaction

Actual browser interaction used the local product
[Dashboard preview](http://127.0.0.1:57316/dashboard.html?preview=1), kept open by its
loopback server. It serves the public catalog and a clearly labeled fixture personal
profile. Get ideas uses three recorded, source-backed Focus batches; **this static
preview makes no live recommendation API request**. Real service requests were
verified separately by the real API browser suite above.

| Surface | Actual interactions observed |
| --- | --- |
| Dashboard 1440×900 | Canvas double-click on Computer science entered Focus; Get ideas showed 10 recorded candidates; Chinese interface selected |
| Dashboard 390px and 320px | Zoom/reset, topic selection and saving Artificial intelligence; exploration mode lit saved Artificial intelligence and its Computer science neighbor |
| Galaxy gray topics | Gray canvas selection opened the chooser, then Festival details; the topic remained unexplored |
| Galaxy controls and return | Domain filtering and search worked; return from Focus preserved camera and query |
| Product `sidepanel.html` 320×850 | Search/filter, explicit Explore, Get ideas, zoom/reset and Botany detail; drag visibly panned without selecting |
| Product `sidepanel.html` 390×850 | DOM size confirmed; actual Focus/zoom/reset interactions |
| Keyboard entry and return after final repair | Keyboard Explore focused visible Back; Enter on Back restored the initiating Explore; Escape also restored Explore |

Five actual CUA screenshots are retained in
`/Users/arthurfu/Documents/OtherWise/.cache/qa/focus-release-0.1.4/`:

- [Desktop Focus](/Users/arthurfu/Documents/OtherWise/.cache/qa/focus-release-0.1.4/focus-desktop.png)
- [Dashboard 390px](/Users/arthurfu/Documents/OtherWise/.cache/qa/focus-release-0.1.4/dashboard-390.png)
- [Dashboard 320px](/Users/arthurfu/Documents/OtherWise/.cache/qa/focus-release-0.1.4/dashboard-320.png)
- [Sidepanel page 390px](/Users/arthurfu/Documents/OtherWise/.cache/qa/focus-release-0.1.4/sidepanel-390.png)
- [Sidepanel page 320px](/Users/arthurfu/Documents/OtherWise/.cache/qa/focus-release-0.1.4/sidepanel-320.png)

Sidepanel checks used the actual product page in a browser tab, not Chrome's native
side-panel container. Native permission prompts were not exercised. Pinch and live
reduced-motion switching are covered by isolated scripts rather than the actual
CUA interaction. Fixture saves and selections do not read or alter the user's real
extension profile or Chrome history. The preview depends on its local server
remaining open; the installed build and screenshots are durable local outputs.

## Historical component evidence and provenance

Earlier focused results provide context, rather than additional final-commit runs:
Task 1 service/API plus real cache had 54 passing tests; Task 2 geometry/protocol
had 23; Task 3's earlier transport/controller Node snapshot had 142; and the earlier
Task 4 repair had 17 browser checks plus 4 activation units. Later final checks are
listed separately above. The known Starlette warning remains documented dependency
noise; the Python run is not described as warning-free.

Earlier component visuals used synthetic geometry/personal state. The five durable
screenshots above instead show actual interaction with the integrated product
preview, while retaining its explicit fixture-data boundary.
[Animation provenance](focus-animation-provenance.md) records the selective
adaptation from `BowenX307/otherwise@8281161`: Orb/starfield rendering primitives
with explicit clock/view inputs and scoped SVG IDs, excluding the teammate mock
API, physical simulation and decorative orbital slots.

## Recorded coordination rulings

All four execution rulings are preserved verbatim here, including costs and
mitigations, so temporary task scratch is not needed to retain those decisions:

> Ruling: Execute independent disjoint-file implementation tasks in parallel as the approved plan and active developer delegation instruction require; root serializes exact-path commits rather than allowing concurrent staging — this saves wall time while avoiding shared-index races — cost if wrong: cross-task integration rework, covered by task and branch reviews.

> Ruling: Reuse completed workers for subsequent tasks when the collaboration service refuses fresh agents with 'agent thread limit reached', while keeping implementation and review on different agents — no close/release tool is available and repeated fresh dispatch was rejected — cost if wrong: retained context may bias task scope; explicit briefs and independent final review mitigate it.

> Ruling: Release Task6's disjoint session/workspace/app integration while Task5 finishes its isolated pointer cleanup, reserving final integration acceptance until both reviews pass — producer interfaces and geometry are approved, the open defect does not change them, and developer instructions favor useful parallel work — cost if wrong: integration rework if gesture repair changes an assumed lifecycle; final component and integration regressions cover that seam.

> Ruling: Adjudicate final-review deferred items explicitly: finalize verification records and local artifact delivery within Task7; retain native Chrome container and permission prompts as unverified; keep deployment/push/hosting and algorithm-quality changes outside this local integration — these follow the approved scope and available evidence — cost if wrong: native-only behavior or ranking quality may require a later validation pass; no claim of those guarantees will be made.

## Reproducing the checks

Use the verified Node 24 runtime and existing cached Python environment:

```sh
export PATH="/Users/arthurfu/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH"
.venv/bin/python -m pytest -q
npm test
npm run build
npm run test:ui
npm run test:browser
npm run test:galaxy
node scripts/test_galaxy_interactions_browser.mjs
node scripts/test_focus_view_browser.mjs
OTHERWISE_RUN_REAL_FOCUS=1 .venv/bin/python -m pytest -q tests/test_focus_service.py -k real_catalog
git diff --check
```

Browser overrides `OTHERWISE_PLAYWRIGHT_MODULE` and `OTHERWISE_CHROMIUM` select the
already installed isolated runtime. The real-service fixture uses cached model data
and a temporary token. Request cancellation, retry, rapid center changes, candidate
paging, saved-interest removal, pinch and live reduced motion have isolated-test
coverage; do not treat that as actual CUA coverage beyond the interaction table.
No secret service token is included in the report or distributed package.

## Privacy and product boundaries

Galaxy positions remain the cached global UMAP plus 15% domain-anchor layout. Focus
uses fixed local radii from angular distances in the original 768-dimensional space;
it does not rank topics by screen distance or recompute UMAP. The direction is a
projection cue, and surrounding-star screen distances are not semantic distances.

Opening or changing Focus is local and does not save an interest, change Discover
or send a request. Explicit Get ideas sends the current catalog ID, catalog/model/
embedding identity and seven recommendation parameters. It sends no saved-interest
profile, browsing history, URLs, titles or descriptions. Discover retains its
approved-interest request rule. Focus caches/centers/cameras are temporary per-window
memory; only the exploration-mode boolean is new persistent state.

Exploration mode starts off. Its lit set contains saved catalog interests, their ten
direct nearest topics and actual searched topics, with no recursive expansion.
Selection or recommendations do not light new regions; a search lights only its
searched target. Chinese support is for interface labels; catalog content stays
original. Focus does not provide a route to a specified endpoint, Chinese
recommendations, knowledge mastery or a demonstrated effect on polarization.

Production must not fall back to sample data. Preview uses the real public catalog
and clearly labeled sample personal state/controlled recommendation fixtures; it
must not read real browser history or imply simulated responses came from the API.
No extension permissions are widened, no model is downloaded for this pass, and
there is no deployment, remote push or teammate-repository modification.

## Verified local delivery

Installed unpacked extension:
`/Users/arthurfu/Documents/OtherWise/dist/otherwise-extension`.
ZIP: `/Users/arthurfu/Documents/OtherWise/dist/OtherWise-extension.zip`.

Before replacing the ignored artifacts, the previous build/ZIP were backed up to
`/Users/arthurfu/Documents/OtherWise/.cache/extension-build-backups/20261003-131326-focus-0.1.4/`;
all 24 prior files were byte-verified. The final delivered build has **40 files with
exact matching hashes**, plus the verified ZIP. The original source checkout remains
clean at `fd581ca`; its branch/source history was not switched or overwritten.
Extension permissions and the user's browser profile/storage remain unchanged.

[Durable delivery audit](/Users/arthurfu/Documents/OtherWise/.cache/qa/focus-release-0.1.4/delivery.json)
records version, source commit/branch, installation/backup paths, all 40 file hashes,
permission parity and ZIP checksum.

ZIP SHA-256:

```text
76d6b205d9f7552d60eceafec5e9a936941e65f7176bb85bd5aca7ac7346dff7
```

Reloading the installed extension is the user's action; no automation operated
`chrome://extensions`. Native Chrome container/permission behavior remains
unverified, as stated above. There was no deployment, remote push, hosting change,
teammate-repository modification or browser-storage migration.
