# Galaxy B and layout controls implementation plan

> For agentic workers: implement independent owned subsystems in parallel, then integrate and verify.

Goal: ship the chosen B with readable optional labels, fit/fullscreen and authenticated adjustable-layout previews.
Architecture: cached Python UMAP jobs return public geometry; extension background authenticates requests; Galaxy merges validated geometry per window while Settings persists defaults.
Tech stack: existing Python/FastAPI/NumPy/UMAP and plain JS MV3/canvas.
Spec: docs/superpowers/specs/2026-10-06-galaxy-layout-controls.md

Global constraints: exact 31,637 IDs/vectors and ten-neighbor authority; B defaults from approved preview; no unrelated worktree merge; numerical limits and API contracts from spec; no private data upload; no automatic commits or publishing.
Review focus: invalid/NaN controls; stale cross-window results; unavailable backend/dependencies; reset/permission revocation; narrow/fullscreen label and control collisions.

1. Backend owner: galaxy/preprocessing.py, service/api.py, new service/galaxy_layout.py, Python tests.
- [x] Test strict parameter/source validation, auth, bounded asynchronous jobs and reuse.
- [x] Add B parameters and 300 epochs to preprocessing/version/cache identity; preserve recommendations.
- [x] Implement the POST/GET contract and public coordinate cache/job service.
- [x] Run targeted Python tests including actual UMAP.

2. Galaxy owner: extension/ui/galaxy*.js/css, map-workspace.js, new UI/layout editor and fullscreen helper, renderer tests.
- [x] Test response merge/source identity and label collision/visibility behavior.
- [x] Selectively bring fit/fullscreen behavior from the development worktree, preserve this checkout's expansion.
- [x] Add dedicated toolbar/editor; Generate preview consumes requestGalaxyLayout(parameters), pollGalaxyLayout(jobId), settings saves via onGalaxySettings(patch).
- [x] Improve point/label rendering and handle stale request, activity/destroy/connection reset; keep packaged B on errors.
- [x] Run relevant Node/browser checks.

3. Settings/transport owner: extension/core/galaxy-layout-options.js, core settings reducer, controller.js/background.js, new transport, app.js, main i18n, tests.
- [x] Test strict normalization and identity-validated authenticated public-only transport.
- [x] Persist options and separate label flags without changing recommendation generation.
- [x] Add Settings fields and workspace callbacks. Runtime returns {result} / {error} for new message types.
- [x] Ensure permission checks, source checks, timeout and connection-change invalidation.
- [x] Run relevant Node tests.

4. Integrator: review owned changes; regenerate B asset/offline Focus fixture/package, start backend with numerical dependencies, real API job and isolated browser QA, version/docs and final review.
- [x] Verify all source IDs/neighbors unchanged and B settings match preview.
- [x] Exercise Settings/toolbar/label switches/fit/fullscreen/nondefault job.
- [x] Run whole Python and Node suites plus packaged Galaxy regressions.
- [x] Produce reviewable screenshot and installation ZIP; report meaningful limitations.

Verification evidence: docs/galaxy-layout-controls-verification.md. No automatic commit or publishing; this checkout already owns the expansion changes.
