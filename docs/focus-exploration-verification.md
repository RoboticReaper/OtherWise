# Semantic Focus and Galaxy exploration verification

Date: 2026-10-03. **Preparation draft: final integration, independent review,
interactive verification and local delivery are pending.** Source versions in
`package.json` and `extension/manifest.json` are synchronized to `0.1.4`. This does
not establish that an installable 0.1.4 build has been verified or delivered.

## Evidence from this preparation pass

| Check | Actual result | Boundary |
| --- | --- | --- |
| Source version parity | Both files parse as version `0.1.4` | Source only; final packaged manifest/ZIP still pending |
| Opt-in real cached catalog check | `OTHERWISE_RUN_REAL_FOCUS=1 .venv/bin/python -m pytest -q tests/test_focus_service.py -k real_catalog`: 1 passed, 21 deselected, 0.22s | Existing local MPNet cache; no new encoding or server startup |
| Cached distance assertion | Absolute tolerance `1e-12`, relative tolerance `0` | Independently derived distances across four real catalog centers |
| Build resource inclusion | Existing build copies the entire extension source tree, excluding tests; Focus scene resources exist | Source inspection only; no build was run in this pass |

The cached check uses the original catalog digest and raw contiguous embedding-cache
bytes, verifies model/dtype/shape identity against packaged layout metadata, and
compares returned distances with independently normalized vectors. The inspected
cache has 3,452 rows, 768 dimensions and `float64` dtype. It verifies existing cached
vectors, not network model installation or encoding of new text.

## Historical component evidence

These results came from earlier task implementation/repair reports and are **not
final whole-product results on the eventual release commit**. Reports and detailed
logs are retained locally under `.superpowers/sdd/2026-10-03-focus-exploration/`
and `.cache/qa/`; the coordinator must refresh the final evidence after integration.

| Earlier component check | Recorded result | Limitation |
| --- | --- | --- |
| Task 1 Focus service/API plus real cache | 54 passed; earlier full Python suite 282 passed, 1 opt-in skip | Earlier source snapshot; existing Starlette deprecation warning was reported |
| Task 2 geometry/protocol units | 23 focused tests passed; earlier Node suite 98 passed | Pure contracts/geometry, before later integration |
| Task 3 boundary/transport/controller suite | 142 passed, no warnings | Earlier shared-worktree snapshot; application integration was outside that task |
| Task 4 Galaxy interaction repair | 17 browser checks and 4 activation tests passed | Isolated renderer/browser fixture, not final integrated app |
| Task 5 Focus repair round 1 | 14 component checks, 2 timing checks, 1 touch-transfer check passed | Independent fixture; review still reproduced fast direct-exit drag cleanup failure on `cfd05d1` |

The outstanding Task 5 pointer issue must receive its scoped repair/re-review before
its gate is treated as clear. The historical green fixture moved inside the map
before exiting and did not cover a first movement directly outside it.

Earlier Focus fixture screenshots are at:

- `.cache/qa/focus/dashboard-1440.png`
- `.cache/qa/focus/dashboard-390.png`
- `.cache/qa/focus/dashboard-320.png`
- `.cache/qa/focus/sidebar-320.png`

They show the real scene renderer with synthetic catalog geometry/personal state.
They are neither final application screenshots nor evidence of real API responses.
The source adaptation is documented in [animation provenance](focus-animation-provenance.md):
selected Orb/starfield primitives from `BowenX307/otherwise@8281161`, with explicit
clock/view inputs, scoped SVG IDs and no teammate mock API or physics engine.

## Pending final verification

Use the verified Node 24 runtime before the final Node commands:

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

Browser scripts can use `OTHERWISE_PLAYWRIGHT_MODULE` and `OTHERWISE_CHROMIUM` to
select the already installed isolated test runtime. A final real-service fixture
must use cached model data and a temporary token, without exposing the code in docs.
Record actual exit status/counts, failures and warnings; expected numbers are not
proof of a pass. Only rerun affected checks after scoped repairs and record which
source snapshot they cover.

The root coordinator still owns:

- Task 6 app/settings/error-guidance integration and integration tests, including
  separate per-window LRU20 and request cancellation. Focus renderer error fallback
  is deliberately generic; specific allowlisted service guidance belongs to the app.
- Independent final-product review against baseline `7ab7990`, including permissions,
  request payloads, state isolation, ID/data-version matching and animation lifecycle.
- Actual CUA interaction at Dashboard 1440×900, 390px and 320px, and product
  `sidepanel.html` at 390×850 and 320×850, preserving the requested heights.
- Single/double click, explicit touch/keyboard Explore, gray-star selection, domain
  filters, save/remove/search, candidate paging, return-state restoration, pan/pinch/
  zoom, retry, rapid center changes, live reduced motion and detail scrolling.
- Final screenshots with explicit real/sample boundaries and an openable product
  preview. A tab displaying `sidepanel.html` is not native Chrome side-panel container
  verification; record that boundary if the native container cannot be tested.
- A final build after source integration and any repairs, packaged-version/resource
  checks, backup and delivery to the original ignored installation artifacts.

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

## Pending local delivery

No source checkout, installed extension folder or ZIP has been copied in this
preparation pass. After final verification, back up the original checkout's ignored
`dist/otherwise-extension` and `dist/OtherWise-extension.zip` under
`/Users/arthurfu/Documents/OtherWise/.cache/extension-build-backups/<timestamp>/`.
Then copy the verified build to those original `dist` paths and compare every file
and the ZIP. Preserve the original checkout branch, installed path and Chrome
storage. Reloading the installed extension is the user's action; do not automate
`chrome://extensions`.

The coordinator must replace this draft status with final commit, test evidence,
preview location, screenshots, backup/delivery checks and remaining verified limits
before describing the release as complete.
