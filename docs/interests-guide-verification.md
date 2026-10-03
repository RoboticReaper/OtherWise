# Interests pages and first-run guide

Verified locally on 2026-10-03 for extension 0.1.7.

Interests contains keyword entry, optional history review, candidate approval and
saved-interest management. Discover contains recommendation controls and results,
with a read-only summary and link back to Interests. Switching pages preserves
window drafts and candidate selections; URL navigation preserves the active page
on reload. Map settings and custom-interest actions use the same navigation path.
The Dashboard button continues to open Map.

New empty profiles show a bilingual three-step native-dialog guide. It supports
Next, Back, Skip, Escape and completion, without history permission or recommendation
requests. Dismissal is browser-local and persists across reloads/windows. Settings
can reopen it. Existing saved profiles skip the automatic guide; Reset creates a
fresh profile and restores it. Closing works even when the profile has an old
validation error. Storage failure leaves the choice unsaved and allows retry.

## Evidence

- 164 extension Node tests passed, including tutorial migration/persistence,
  unchanged generation/payload and trusted Interests dashboard routing.
- `test_ui_browser.mjs` passed page separation, draft/selection preservation,
  original pagination/settings/language behavior, three tutorial steps, reload
  persistence and Settings replay/Escape despite a previous error.
- `test_discovery_browser.mjs` passed first-run Skip with zero requests, subsequent
  graph requests, retained rating compatibility, window synchronization, failure
  recovery, reset and Cards/List layouts at 1440, 390 and 320 pixels.
- `test_map_workspace_browser.mjs` passed independent Focus windows, retained
  cameras, keyboard navigation and the corrected Settings URL.
- The final `test_extension_browser.mjs` run passed with the real cached MPNet
  service: broad/Focus/discovery requests, sources, existing-rating compatibility,
  searches, local history review and reset all worked through the split UI.
- Guide and split-page screenshots were inspected. Browser checks use temporary
  profiles and fictional interests; native permission prompts use isolated
  pregranted test copies. No real user browsing/profile was opened or reset.

The ranking backend and public map/catalog assets are unchanged. Build 0.1.7 has
matching package/manifest versions and includes the updated guide source and
installation instructions. QA evidence is ignored by Git under
`.cache/qa/ui-preferences/`, `.cache/qa/discovery/` and `.cache/qa/map-workspace/`.

Reproduce with Node 22+ (verified with bundled Node 24), the project Python
environment and Playwright/Chromium:

```sh
npm test
python scripts/build_extension.py
node scripts/test_ui_browser.mjs
node scripts/test_discovery_browser.mjs
node scripts/test_map_workspace_browser.mjs
```

Set `OTHERWISE_CHROMIUM` and `OTHERWISE_PLAYWRIGHT_MODULE` for a separate browser
runtime. Reload the unpacked extension and refresh existing tabs to use this build.
