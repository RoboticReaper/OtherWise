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

## API

`GET /health`: `{ "ready": true }` when the real engine is available; otherwise 503.

`POST /api/recommend`, `Authorization: Bearer <team code>`:

```json
{
  "keywords": ["Gardening"],
  "mode": "path",
  "focus": "Gardening",
  "expansion_level": 0,
  "limit": 10
}
```

Extra fields are rejected. Requests are bounded to 16 KiB, 40 keywords, level 0–8
and limit 1–20. The response supplies topic/domain/description, nearest interest,
distance and zone. The client suppresses topics the user has dismissed locally.
Public catalog vectors are cached; history and submitted interest vectors are not.

The shared-token, one-worker server is suitable for a small hackathon demo.
Deploying a persistent multi-user service would require a different operational
design for authentication, availability and abuse limits.
