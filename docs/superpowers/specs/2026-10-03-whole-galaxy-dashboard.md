# Whole Galaxy and dashboard

User-approved scope: migrate only the whole-catalog Galaxy from local prototype
`fd581ca` on `codex/interest-galaxy-validation`. Work on
`codex/otherwise-development` in an isolated worktree; leave the original checkout
and all prototype experiments intact. The dashboard is a full extension tab sharing
the side panel's local state (explicitly selected by the user).

## Data and geometry

- Original catalog descriptions and normalized 768-dimensional MPNet vectors only.
- Angular distance `acos(clipped cosine) / pi`; true neighbors are calculated here.
- UMAP: precomputed angular metric, 2D, 30 neighbors, min_dist 0.15, seed 42, one job.
- Domain prototype means normalized, metric MDS fitted to their angular distances;
  n_init 1, max_iter 500, eps 1e-7, seed 42. Three nearest domain affinities use
  temperature 18 softmax weighting. RMS-radius normalization and orthogonal
  Procrustes alignment match the prototype; final mixture is 85% UMAP / 15% anchors.
- An independent preprocessing command creates an atomic versioned cache and a
  public distributable artifact. Identity includes catalog, model, vector identity,
  parameters, algorithm version and numerical dependency versions. Validate cache
  contents and ID references before reuse. No generation during UI interaction.
- Preserve the existing canonical catalog-topic string IDs used by the API, local
  interests and recommendations. No array-offset IDs. Reordering cannot misassociate
  positions or neighbors. Renaming a catalog topic is an explicit identity migration.
- Shared asset contract: schema_version 1; metadata and cache_key; `domains` records
  `{id, x, y}` where id is original domain name; `topics` records
  `{id, x, y, neighbors:[{id,distance}]}`. Catalog remains the text authority.

## Product experience

- Whole catalog visible before a user saves any interests. Deterministic coordinates,
  domain colors/labels, literal topic names/descriptions, English/Chinese controls.
- Keyword search; explicit selection and details; true high-dimensional neighbors;
  domain filtering; zoom buttons/wheel, pointer pan, touch pinch and reset view.
- Highlight starting/saved interests, current focus and current recommendations.
  Draw real exploration edges separately from selected-topic neighbor links.
- Selecting a star does not save an interest. An explicit Save interest button uses
  the existing action; approved topics can be chosen as a focus through SET_FOCUS.
  Topics missing from the catalog remain available as local interests, without fake
  coordinates. Numerical distances are never inferred from screen positions.
- Visual direction follows the selected spiral sketch: dark depth, subtle star glow,
  visible trails. No spiral transform distorts the specified UMAP coordinates.
- Dashboard provides full-width Galaxy, Discover/recommendations, and Settings using
  the same bridge and storage as the side panel, with a side-panel Open dashboard
  entry. Ordinary localhost preview is explicitly sample-only and uses no real
  browser data. Product mutations remain inside trusted extension contexts.
- Preserve settings drafts, loaded recommendations, pagination, selections and map
  camera when state/language changes. Resize should preserve world coordinates.

## Validation

Run baseline and final Python/JS suites, real-MPNet integration, and existing UI
checks. Add numerical/cache/ID tests and production browser checks at desktop,
actual side-panel route, 320px and 390px. Verify search, selection, filters, pan,
zoom, resets, bilingual UI, shared tab/panel state, explicit saves, refresh-stable
coordinates, raw descriptions, cache reuse/invalidation, and no private data in
public assets. Deliver an openable preview and packaged extension. No deployment.

## Explicit exclusions

No directional CS-to-Psychology explorer, authored HCI description, experimental
ranking tables, comparison metrics, new recommendation algorithm or 2D ranking.
