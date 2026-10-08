# Whole Galaxy and dashboard verification

Current expanded B and adjustable-controls verification: [2026-10-06 verification](galaxy-layout-controls-verification.md). The measurements below are the historical 2026-10-03 baseline.

Verified 2026-10-03 in the managed product worktree, branch
`codex/otherwise-development`, starting at `9e6d9a2`. Prototype source was read
from local commit `fd581caed6e8c5fa7570fb5123ee2baa2eec0f41` on
`codex/interest-galaxy-validation`; its original checkout remained clean and on that
commit. No remote prototype fetch or experimental branch merge was used.

## Data and preprocessing

- 3,452 original catalog topics, 23 domains, normalized original 768D MPNet vectors.
- Layout: precomputed angular distance UMAP (30 neighbors, min distance .15,
  seed 42), aligned to top-three MDS domain anchor targets, 15% anchor blend.
- All 3,452 top-ten neighbor sets match the prototype's original-vector neighbors.
- Maximum coordinate difference from its rounded coordinates: `5.200237689351184e-6`;
  maximum domain-anchor difference: `4.839271411483104e-6`.
- Build 20.894s; verified cache reuse 0.233s on this machine. These are observed
  measurements, not a performance guarantee.
- Asset cache key:
  `768064b1828254b042cd328178fda14d1c15d48b72b41795c8157e5f7c4d2c77`.
- Tests cover changed catalog text/order, model, embedding bytes, parameters,
  numerical package versions and algorithm version; malformed caches rebuild.
  Packaging validates before replacing an existing install folder.
- Canonical topic title IDs join source catalog, asset, profile and API. Array
  reordering does not change identities. Topic renaming requires an identity migration.
- No directional CS-to-psychology experiment, custom HCI description, ranking
  comparison or user profile is included in the generated public asset.

## Tests

| Check | Result |
|---|---|
| `.venv/bin/python -m pytest -q` | 229 passed; one existing Starlette/AnyIO deprecation warning |
| `node --test extension/tests/*.test.js` (Node 24) | 82 passed |
| `python3 scripts/build_extension.py` | Validated catalog/layout, unpacked build and v0.1.3 ZIP |
| `node scripts/test_ui_browser.mjs` | Existing candidate/recommendation pagination, compact view, bilingual preferences and settings pass |
| `node scripts/test_extension_browser.mjs` | Real MPNet service, synthetic history, approval boundaries, search/save/focus, pause/deletion/reset pass |
| `node scripts/test_galaxy_browser.mjs` | Full real map and shared-dashboard interactions pass |
| `git diff --check` | Clean |

Browser checks used an isolated temporary Chromium profile, public catalog and
synthetic interests. The Galaxy suite blocks external access through a closed
loopback proxy; it verifies the Google search URL and local exploration state
without depending on Google content. The older end-to-end suite grants optional
permissions only in a test copy; the production manifest's permissions did not grow.

## Interaction and visual checks

- Full catalog visible with no saved interests and no history permission.
- Real dashboard launched from the side panel's button; both subscribe to shared
  `chrome.storage.local`. Interest and language changes propagate both ways.
- Desktop 1440px, dashboard 390px/320px and product side-panel page at 390px:
  keyword/description search, case-insensitive Enter selection, domain filtering,
  neighbor selection, mouse wheel, zoom buttons, drag, keyboard pan/zoom/reset.
- Real canvas pointer hit maps back to its canonical topic ID. Dragging and
  two-pointer Chromium touch pinch do not accidentally select topics.
- Original descriptions and ten displayed neighbor IDs/distances match the asset.
  Chinese affects controls, never topic content.
- Selecting topics does not save them. Searching a catalog-only topic records an
  exploration only; the save action remains explicit. Saved topics can become
  the recommendation focus using the existing path workflow.
- Zoom, search and selection survive language/state rerenders. Refresh loads the
  same static coordinates. Filters dim other domains without changing positions.
- Custom saved topics outside the catalog have a separate accessible list with
  no fabricated coordinates or semantic neighbors.
- Search results have a bounded scroll area on small screens. Inspected screenshots
  confirm readable controls/details and no horizontal page overflow.
- Explicit HTTP preview loads the same real Galaxy with a sample-profile banner.

Independent review found and fixed two integration issues: retrying a parsed but
invalid cached asset now refetches it, and the controller now permits canonical
catalog-only searches while rejecting arbitrary injected topics. Regression tests
were observed failing before those fixes and passing afterward.

Local QA evidence is under `.cache/qa/galaxy/`, `.cache/qa/ui-preferences/`, and
`.cache/qa/galaxy-preprocessing-comparison.json`. Screenshots are generated evidence,
not shipping application dependencies.

## Remaining limits

- Two-dimensional placement approximates semantic relationships; actual neighbors
  and recommendations use original high-dimensional distances. No mastery claim.
- The topic catalog and recommender are English; Chinese is UI support only.
- Browser-tab dashboard requires the extension for the shared real profile. The
  explicit HTTP preview uses isolated sample state; it is not a public website.
- Canvas labels are deliberately reduced at small sizes to avoid overlap. Search,
  domain controls, neighbor buttons and the domain-color key remain accessible.
- Resizing the side-panel page and emulated touch were tested; physical touch-device
  behavior and Chrome's native permission prompts were not manually exercised.
- Regenerating geometry needs the separate pinned Python layout dependencies.
  Normal extension builds use the checked-in asset and do not need UMAP.

## Local delivery

The verified v0.1.3 build was copied back to the existing
`/Users/arthurfu/Documents/OtherWise/dist/otherwise-extension` load path, with every
file checked against the product-worktree build. This preserves Chrome's existing
unpacked-extension path and avoids creating a separate profile through a changed
extension ID. Browser storage was not read or modified by delivery. The previous
build and ZIP are retained in
`/Users/arthurfu/Documents/OtherWise/.cache/extension-build-backups/20261003-040425/`.
Reload the extension card and reopen its panel, then choose **Dashboard ↗**.
The source prototype checkout remained on `fd581ca` with clean tracked status.
