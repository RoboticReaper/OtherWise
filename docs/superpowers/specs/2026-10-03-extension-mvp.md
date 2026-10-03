# OtherWise extension MVP — approved design

The user approved implementation on 2026-10-03 after a 15-question design interview. Continue on codex/otherwise-development in this checkout. Scope: English Chrome MV3 extension, local Chrome history including YouTube visits, Python recommendation API, shared demo from this Mac through a temporary HTTPS tunnel. No account-wide YouTube import, opposing-viewpoint classification, search-box injection, or skill-mastery claims in v1.

## User experience
- English side panel: OtherWise brand, dark midnight/ivory/silver-sage Galaxy aesthetic, serif headings, restrained whitespace. No dashboard clutter. Editable interest chips, candidate inbox, recommendation cards, Google/YouTube search actions.
- Initial history import explicitly requests optional history permission, defaults to 30 days, lets users inspect candidate topics and approve selections. Manual topics work without history permission.
- Two independent opt-in controls: ongoing LOCAL browsing analysis; automatic recommendation refresh following changes to approved interests. Defaults off. Product exploration records are recorded automatically from explicit OtherWise search actions.
- Search means explored, never interested or mastered. Explicit confirmation adds an interest. Rejection suppresses a topic locally. Two-dimensional map groups topics into knowledge domains and links actual exploration paths. Keep initial approved interests as comparison baseline; honor deletions even in baseline.
- Path mode defaults to most recently explicitly confirmed interest as focus. Global mode is configurable; each newly confirmed interest after onboarding raises expansion_level by one, max 8; clicks/refreshes/duplicate approvals never raise it. Server expansion = min(0.07 + 0.01 * level, 0.15). No silent range widening.

## Privacy boundary
- Raw titles/URLs remain local and transient. Rules match title phrases to bundled catalog/aliases; only catalog topics become automatic candidates. Manual input is explicit approval. No browser model download. No remote metadata fetching in v1.
- Local evidence stores URL hash (salted per-install), hostname, topic IDs, source type, time; not raw URLs/titles. Evidence/candidates expire after 30 days. No storage.sync; storage.local restricted to trusted extension contexts. incognito:not_allowed.
- Skip non-HTTP(S), localhost/private-network addresses and editable default blocked domains for common mail, banking, account and document services. Filtering is an aid, not a promise to detect all sensitive topics.
- Pause stops new analysis, invalidates queued work and does not backfill paused intervals. Resume begins now. Background title reconciliation is delayed because onVisited precedes page load; missing titles produce no guesses.
- History deletion removes corresponding local evidence and recomputes candidates. Full deletion clears history-derived data. Explicitly saved interests and OtherWise exploration paths survive until user removes them or resets all data. Reset/revoke changes generation so stale work cannot restore/send deleted data.
- Only approved topic strings + mode/focus/expansion/limit may be sent. No raw history, candidates, timestamps, counts, source evidence or map. Server request schema rejects extra fields; no request body logging, no profile database/analytics. Requests use POST, shared bearer token, bounded sizes/rate and concurrent compute limits. Do not claim anonymity: approved topics and network metadata reach service/tunnel.

## Shared contracts
Bundled catalog records: {id: topic title, topic, domain, description}; id is the exact catalog topic title. Custom manually approved topics may use their trimmed phrase as id.

State (all arrays): schemaVersion=1, generation=0, salt string; settings {browsingEnabled:false, autoRefresh:false, mode:'path', globalLevel:0, endpoint:'http://127.0.0.1:8000', accessToken:'', blockedDomains:string[], analysisSince:0}; approved Topic[] with addedAt; baseline:string[]; candidates Topic[] with count,firstSeen,lastSeen,sources; evidence {sourceHash,host,seenAt,topicIds,source}[]; suppressed:string[]; explored Topic[] with parentId,at; edges {from,to,at}[]; recommendations Recommendation[]; focus:string|null; lastError:string|null; lastUpdated:number|null.

Core module extension/core/index.js exports:
- createState(now=Date.now()) -> State
- reduceState(state, action, now=Date.now()) -> State (immutable)
- prepareObservation(historyItem,catalog,{salt,blockedDomains},now=Date.now()) -> Promise<Evidence|null>; no raw title/URL in result
- hashUrl(url,salt) -> Promise<string>
- buildRequest(state) -> exact wire object; throws when no approved interests
- isAllowedUrl(url,blockedDomains) -> boolean
Actions: INGEST {observations}; APPROVE {ids}; ADD_INTEREST {topic}; REMOVE_INTEREST {id}; DISMISS {id}; EXPLORE {topic,parentId}; SET_SETTINGS {patch}; SET_FOCUS {id}; CLEAR_DERIVED; RESET; DELETE_SOURCES {hashes,all}; RECOMMENDATIONS {items,generation}; ERROR {message}; CLEAR_ERROR. INGEST observations contain topics Topic[] as well as topicIds if needed; persisted evidence drops topics after recompute uses catalog fields available in candidates/approved. Core author may add private helpers but preserve public contract.

UI imports extension/bridge.js: getState(), dispatch(action), importHistory(days), recommend(), search(topic,provider), subscribe(callback). Async methods return State; subscribe returns unsubscribe. UI uses Topic records, never raw history. App may be shown at ?preview=1 with clearly labeled synthetic demonstration data; actual extension always uses chrome runtime. Production must never silently fall back to preview.

Wire POST /api/recommend: {keywords:string[1..40],mode:'path'|'global',focus:string|null,expansion_level:int[0..8],limit:int[1..20]}. focus, when present, must be an approved keyword. Response {recommendations:[{id,topic,domain,description,nearest_interest,distance,boundary_offset,zone}],mode,expansion_level}. Path selects around focus while excluding approved/exact known topics; global uses all approved keywords. Original engine remains reusable; service can filter/deduplicate/oversample without crossing distance band. GET /health returns readiness without secrets. Bearer token required for recommendations, deny if not configured. CORS for explicit origins or chrome-extension scheme (not authentication substitute). No production synthetic model fallback.

## Acceptance
1. Existing 33 algorithm tests remain green; backend auth, invalid/extra payloads, focus/band/known topic behavior covered with deterministic vectors; real MPNet smoke passes.
2. Local tests prove unconfirmed titles never escape request builder, candidates require approval, repeated/search actions do not advance interests, limits enforced, deletion/reset/pause defeat stale results.
3. Unpacked extension imports only after consent; readonly browser history; no actual private history used during automated tests. Isolated browser profile with synthetic fixtures validates consent, inbox, recommendations, feedback, map, settings and reset.
4. Full and narrow UI readable, no unintended horizontal overflow, errors recoverable, offline/tunnel unavailable states visible. Team install bundle and start/stop scripts provided. Logs and credentials stay gitignored. No remote Git push.
