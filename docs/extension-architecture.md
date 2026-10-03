# OtherWise extension architecture

## Data flow

Chrome history → local adapter/title matching → local candidate inbox → user approval
→ approved-only API request → MPNet catalog recommendations → search/feedback → local map.

The browser is the profile owner. The backend computes recommendations but stores
no user profile. The only persisted embeddings are for the public topic catalog.

## Code boundaries

| Component | Responsibility |
|---|---|
| `extension/background.js` | Chrome events, optional permissions, trusted messages, local storage |
| `extension/controller.js` | Serialized state changes, async cancellation, import/analysis, API/search |
| `extension/core/index.js` | Pure state transitions, topic extraction, hashing, approved-only payload |
| `extension/bridge.js` | UI/runtime messages and user-triggered permission requests |
| `extension/ui/` | Discover, candidate inbox, map and Settings |
| `extension/dev-preview.js` | Explicit sample-only design preview |
| `service/api.py` | Strict authenticated request schema, size/rate/compute bounds, safe errors |
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

The shared-token, one-worker server is suitable for a small hackathon demo.
Deploying a persistent multi-user service would require a different operational
design for authentication, availability and abuse limits.
