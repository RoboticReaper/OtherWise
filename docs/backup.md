# Settings backup and restore

Settings → Import & export provides a local JSON backup. This feature was requested with design choices delegated to the implementer.

## Portable data

Version 1 (`OtherWise-backup`) contains an export timestamp, saved interests, baseline and focus, exploration records and edges, dismissed topics, concept feedback and exposure counts, and portable preferences (language, discovery, recommendation, Galaxy, sound, excluded websites). Topic IDs remain unchanged.

Credentials, service addresses, history permission, browsing evidence and candidates, privacy salt, pending recommendations, undo records, and transient service state are excluded. Import keeps the device's connection, browsing setting, automatic refresh setting and browsing data (except evidence removed by restored website exclusions, as when saving Settings). No network request or permission request is triggered by importing.

## Import behavior

Files are fully validated before any write, both in the page and in the background controller. Reject unsupported versions, invalid records or preferences, files larger than 5 MiB, and arrays exceeding explicit limits. Do not silently truncate. Import performs a single serialized storage write and invalidates pending recommendation, Focus and Galaxy requests after persistence succeeds. Failed validation or failed persistence must leave the current profile intact.

Successful import cancels pending Galaxy previews in every open window. Old jobs cannot resume polling; a fresh preview can reuse the backend's cached result. Failed persistence keeps the original preview active.

The preview shows export time and counts of interests, exploration records and concept feedback. Merge is the default: add missing records, keep local preferences and existing ratings, preserve local interest order, deduplicate repeated imports, and reject more than 40 combined interests. Exposure counts merge by maximum. Replace restores the portable data and preferences and requires a separate acknowledgement. Both modes preserve the local privacy salt. The preview offers export of the current data before replacement.

Unsaved Settings drafts block import; export always uses persisted settings. Success leaves Settings open, clears stale UI selections, and announces completion in the active language. Controls and errors support English and Simplified Chinese. The modal is keyboard accessible and fits a 320px side panel.

## Validation

- Core backup tests: round trip, privacy exclusions, merge conflict rules, duplicate imports, interest limit, malformed/unsupported/oversized files, invalid preferences and topic identities.
- Controller tests: production import route, persistence across reopening, invalid-file atomicity, no network or permission requests.
- `scripts/test_backup_browser.mjs`: real download, file upload, default merge, duplicate import, reload, invalid file, cancellation, acknowledgement, replacement with language change, credential preservation, no history permission, responsive modal and keyboard focus, unsaved draft protection.
- `npm run test:galaxy-invalidation`: real side-panel/Dashboard cancellation for merge, replace and clearing derived data, plus fresh generation with the same backend job ID. Uses temporary profiles and a fictional local service.

Browser evidence is saved under `.cache/qa/backup/` when the browser checks run. The installable build is `dist/OtherWise-extension.zip`.

Verified on 2026-10-08:

- Extension unit tests: 254 passed.
- Backend regular suite: 407 passed, 2 skipped, 2 layout-integration tests deselected.
- Backup browser regression: passed, including actual Chrome extension storage and downloads.
- Existing UI browser regression: passed, with no page errors or external requests.
- Standards and Spec reviews: all reported issues resolved; no remaining actionable findings.
- Extension build and whitespace check: passed.
