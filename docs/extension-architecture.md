# OtherWise extension architecture

## Data flow

Chrome history → local adapter/title matching → local candidate inbox → user approval
→ approved-only API request → MPNet catalog recommendations → search/feedback → local map.

Map adds a separate explicit path: catalog selection → temporary local Focus →
**Get ideas** → catalog-ID/version-only Focus request → local candidate scene. Merely
opening Focus does not request recommendations or change the approved-interest flow.

The browser is the profile owner. The backend computes recommendations but stores
no user profile. The only persisted embeddings are for the public topic catalog and public discovery
graph. Specific requests rebuild an ephemeral profile from explicit client ratings.

## Code boundaries

| Component | Responsibility |
|---|---|
| `extension/background.js` | Chrome events, optional permissions, trusted messages, local storage |
| `extension/controller.js` | Serialized state changes, async cancellation, import/analysis, API/search |
| `extension/core/index.js` | Pure state transitions, topic extraction, hashing, approved-only payload |
| `extension/bridge.js` | UI/runtime messages and user-triggered permission requests |
| `extension/ui/` | Discover, candidate inbox, map and Settings |
| `extension/dashboard.html` | Full extension tab sharing the same bridge, reducer and local storage as the side panel |
| `extension/ui/galaxy*.js` | Validated ID join, local public assets, stable camera and canvas renderer |
| `extension/ui/focus*.js` | Fixed local projection, scene primitives, controlled labels and per-window session |
| `extension/focus-transport.js` | Independent authenticated Focus request owner, strict identity/response validation and cancellation |
| `galaxy/`, `scripts/build_galaxy.py` | Independent public-catalog preprocessing and content-addressed layout cache |
| `extension/dev-preview.js` | Explicit sample-only design preview |
| `service/api.py` | Strict authenticated request schema, size/rate/compute bounds, safe errors |
| `service/discovery.py` | Public graph embedding cache, broad-to-area routing, temporary feedback profile and graph recommendations |
| `extension/core/discovery.js` | Validated graph metadata, browser-owned ratings/counters and compact feedback payload |
| `service/engine.py` | Real MPNet initialization, public catalog cache, path/global recommendations |
| `explorer.py` | Shared notebook/engine numerical recommendation methods |

`prepareObservation(historyItem, catalog, settings, now)` is the adapter boundary.
It receives a source URL/title locally and returns topic metadata plus a salted
source hash, hostname, timestamp and source type. Raw inputs do not enter state.
Future site adapters can prepare richer local text or aliases here, while leaving
the consent inbox and backend contract unchanged. Any new site's permissions and
metadata retrieval need their own user-facing consent design.

## State rules

Candidates, saved interests and explored topics are separate. An exploration does
not add an interest. The first explicit approval sets a baseline for comparison.
Later approvals select a new path focus; global expansion grows only for new
confirmations in global mode, never for repeated clicks or duplicate interests.
`SET_FOCUS` chooses an already approved topic without changing the profile/range.

An incrementing generation invalidates delayed requests/analysis after changes,
pause, deletion or reset. Network dispatch and generation checks are serialized,
so a profile removed while permission is being checked cannot be sent afterward.
An already transmitted request cannot be recalled; abort prevents its result from
repopulating local state. Reset also rotates the local hashing salt.

Storage is `chrome.storage.local`, restricted to trusted extension contexts.
Messages accept only this extension's own pages. There are no content scripts.
Production requests omit credentials and reject redirects.

Dashboard and side panel subscribe to the same local state changes. The packaged
Galaxy asset is public and contains coordinates and high-dimensional neighbor IDs;
it contains no browsing evidence or personal profile. Map selection, search,
filtering and camera motion are local view state and do not submit API requests.
The renderer joins by canonical topic title IDs used by the existing service and
reducer, never by layout row offsets. Reordering arrays is safe; renaming a canonical
topic requires an explicit identity migration for existing saved profiles.
Custom interests outside the catalog remain available without fabricated coordinates.
Recommendations still use the original embedding space, independently of the map.

`settings.language` is a local UI preference (`en` or `zh-CN`). Existing installs
default to English. Changing it does not invalidate recommendations, cancel an
active request or trigger automatic refresh, and it never enters the API payload.
Topic titles, domains and descriptions are data and stay in their original language.
Candidate pagination is view state; selections keep topic IDs across pages.
`settings.recommendationView` similarly stores `cards` (the existing default) or
`list`, without changing profile generation, requests or recommendation contents.
Both recommendation layouts paginate the cached batch at ten topics per page.
Dismissing a topic filters locally and fills the current page from the remaining
batch; it does not send another request or send suppressed topics to the server.
Changing numeric `settings.recommendationOptions` invalidates any pending response.
Old installs receive the existing algorithm defaults when these settings are absent.

`settings.galaxyExplorationMode` is a persistent presentation value and
defaults to false, including migration of missing/invalid values. It neither changes
recommendation parameters nor causes a request. The lit set is the union of saved
catalog interests, each interest's ten cached direct nearest topics, and actual
searched catalog topics. Selection, recommendation arrival and temporary centers do
not enter that set; searches light only their target. Removing an interest recomputes
the union without erasing coverage supplied by another interest or a search.

Galaxy/Focus subview, temporary center, selection, camera snapshots, animation phase
and request state belong to each window. Focus does not overwrite Discover focus,
mode or recommendations. A separate per-window result cache holds at most 20 keys,
including endpoint/authorization generation, schema/algorithm version, catalog/model/
embedding identity, center ID and all seven parameters. Cancellation and version
validation keep old-center results out of the current scene. Connection, relevant
permission, reset/clear and parameter changes invalidate the affected Focus channel
and cache; Dashboard, panel and Discover request owners remain independent.

Map searches pass an explicit trusted context: Galaxy uses `{source:'galaxy'}`, while
Focus uses `{source:'focus',centerId}`. The controller validates canonical catalog
IDs and records a real search edge without adding the temporary center to approved
or explored state. Search paths indicate actions, not mastery.

Focus nodes use fixed radii `1000 * acos(clamp(cosine, -1, 1)) / pi`; directions come
from cached Galaxy coordinates. Coincident global coordinates use a deterministic
ID-derived angle. Rendering changes opacity, labels and camera, never semantic
coordinates. Scene-owned Orb and background primitives receive explicit time and
view inputs, share one scene animation loop, pause when hidden/inactive, and stop
motion immediately for a live reduced-motion preference. See
[animation provenance](focus-animation-provenance.md).

## API

`GET /health`: `{ "ready": true }` when the real engine is available; otherwise 503.

`POST /api/recommend`, `Authorization: Bearer <team code>`:

```json
{
  "keywords": ["Gardening"],
  "mode": "path",
  "focus": "Gardening",
  "expansion_level": 0,
  "limit": 10,
  "radius": 0.28,
  "expansion": 0.07,
  "overlap": 0.015,
  "diversity": 0.20,
  "max_overlap_fraction": 0.20,
  "randomness": 0.03
}
```

Extra fields are rejected. Requests are bounded to 16 KiB, 40 keywords, level 0–8
and integer limit 1–100. The six floating-point controls are optional, defaulting
to the values shown above, so older five-field clients remain supported. All must
be finite numbers from 0 to 1, except `max_overlap_fraction`, capped at 0.95.
The effective expansion is `min(expansion + 0.01 * expansion_level, 1)`; the
persisted expansion level still applies if the user switches back to path mode.
The response supplies topic/domain/description, nearest interest,
distance and zone. The client suppresses topics the user has dismissed locally.
The quantity is a maximum: band eligibility, the familiar-content quota, and local
suppression can yield fewer visible topics. No sparse-result fallback widens the band.
Public catalog vectors are cached; history and submitted interest vectors are not.

`POST /api/discover` uses the same recommendation fields plus:

```json
{
  "feedback": [{"concept_id":"Q758780", "area_id":"gardening", "curious":true, "known":false, "difficulty":"none"}],
  "exposures": {"gardening":2},
  "seed": 42,
  "exploration_fraction": 0.3
}
```

This is an addition to the full recommendation request, not a standalone body.
Discovery alone accepts up to 1 MiB, 4,000 ratings and 100 area counters. Booleans,
difficulty (`none`, `too_basic`, `too_hard`), canonical concept/area membership,
unique IDs and integer counter/seed bounds are validated. Authentication precedes
parsing; the route shares the rate limiter and single compute semaphore with broad
and Focus requests. Errors do not echo submitted data. A graph initialization
failure leaves broad/Focus available while discovery returns 503.

The server encodes approved interests against broad and graph context, excludes
concepts matching the title of, or within distance 0.035 of, any approved interest
(including in path mode), routes to
eight areas, and applies the upstream graph ranking/feedback rules. Public graph
vectors are cached by model and content identity; submitted interests, ratings and
profiles are never written to that cache. The response adds `seed`, `graph_sha256`
and nested `discovery` metadata: canonical concept and area IDs, source path/URL,
optional level, reserve membership and achieved/requested reserve counts.

The reducer keeps existing title-based topic IDs and nests canonical graph IDs in
metadata, so saved interests, paths and Galaxy joins preserve their identities.
Ratings and exposure counts are browser-local. A successful fresh batch increments
counts once per accepted returned concept, including cached pagination pages; feedback reranks use the previous seed
and pre-batch counters. Storage must succeed before committing a rating or sending
its rerank. Generations and permission checks prevent stale replies from replacing
current state. Reset rotates the salt and clears feedback drafts in every window.

`POST /api/focus`, using the same bearer code and service permission:

```json
{
  "topic_id": "Gardening",
  "catalog_sha256": "<original catalog digest>",
  "model": "all-mpnet-base-v2",
  "embedding": {"sha256": "<original cache-byte digest>", "dtype": "float64", "shape": [3452, 768]},
  "limit": 10,
  "radius": 0.28,
  "expansion": 0.07,
  "overlap": 0.015,
  "diversity": 0.20,
  "max_overlap_fraction": 0.20,
  "randomness": 0.03
}
```

The digests/dtype/shape come from validated packaged layout metadata; the example
placeholders are not usable identities. The request contains no keywords, personal
profile, history, URLs, titles or topic descriptions. The caller explicitly requests
it through **Get ideas**, even for an unsaved center. It uses the existing normalized
catalog seed vector without new text encoding and does not add Discover's expansion
level. Original catalog/vector identity is preserved before additional normalization;
layout algorithm version and Focus algorithm version are distinct.

The response has `schema_version:1`, `algorithm_version:'catalog-focus-band-v1'`,
`seed_id`, matching catalog/model/embedding identity and `recommendations`. Every
record has a canonical `id`, true angular center distance and the existing result
fields. The client rejects wrong identity/center, unknown or duplicate IDs, excess
quantity, invalid/band-violating distances and incorrect nearest-interest IDs before
rendering or caching. Display text comes from the local canonical catalog.

The route shares authentication, origin, request-size, rate, readiness and compute
bounds with Discover. Failures use controlled errors: 422 invalid ID/parameters,
409 incompatible data, 401 authentication, 429 rate limit and 503 unready/compute
failure. Arbitrary backend errors are not echoed into the interface. Local nearest
topics remain available; the application owner provides localized service/settings
and retry guidance. The renderer neither fetches nor persists personal state.

The shared-token, one-worker server is suitable for a small hackathon demo.
Deploying a persistent multi-user service would require a different operational
design for authentication, availability and abuse limits.
