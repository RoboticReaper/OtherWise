# MVP verification — 2026-10-03

## UI update 0.1.1

The pagination, English/Simplified Chinese UI, and Cards/List update passed all
66 JavaScript tests and both browser suites. The original real-model extension
flow still passes its 13 grouped checks. The new UI suite checks 103 fictional
candidates, page-only bulk selection, cross-page approval, last-page deletion,
literal English recommendation data, dirty drafts/caret, local preference
persistence after reload, and compact rows at 390/1100px with no horizontal overflow.
There were no external requests during the UI-only suite. An immediate native
description toggle followed by language switching is covered after fixing its
asynchronous toggle-event race. Independent scoped review found no remaining issues.

Chinese support is limited to UI; this update does not add Chinese support to
the recommendation system or change its request schema.

## Initial MVP

The first OtherWise extension MVP was verified on macOS using Python 3.13,
Node 24, and an isolated Chromium 141 profile. No real user browser history was read.

| Check | Result |
|---|---|
| Full Python suite | 87 passed, including original 33 numerical tests |
| JavaScript core/controller/background suite | 57 passed |
| Real cached MPNet | Both path/global modes returned 10 genuine recommendations |
| Extension browser integration | 13 checks passed against a real test API |
| UI preview | Discover/Map/Settings at 390×850 and 1100×850; 14 interaction/stress checks passed |
| Independent code review | No outstanding actionable findings after two behavior fixes |
| Shared HTTPS endpoint | Missing token → 401; correct token → 200 with 10 real recommendations |
| Demo lifecycle | Local start, authenticated readiness, idempotent rerun, stop, forced-startup-failure cleanup passed |

Browser integration covered opt-in defaults, local history import, candidate
approval, exact five-field approved-only outbound payload, real recommendations,
search without automatic interest approval, explicit save, switching map focus,
ongoing local analysis, pause/resume, history deletion, reset, browser errors and
horizontal overflow. The count groups related assertions as reported by
`scripts/test_extension_browser.mjs`.

The browser test pregrants history and loopback permissions in a **test-only copy**
of the manifest. Production was separately loaded with no history/host grants.
The first optional history grant/listener registration is regression-tested at
the background boundary. Native Chrome permission dialogs were not automated;
the user chooses these during first use. Synthetic pages were fulfilled inside
the isolated test browser; Google/YouTube were not accessed as the user's account.

Independent review found and verified fixes for two issues: clearing derived data
could be undone by the next background scan; global recommendation paths could
link to the wrong saved interest. Clearing now advances the analysis boundary,
and global map paths use the recommendation's actual approved source interest.

Other regression tests cover reset/pause/remove before outbound dispatch, late
responses, safe errors, history deletion during concurrent approval, endpoint
revocation, dismissed-topic suppression and 30-day derived-data expiry.

One upstream Starlette/AnyIO deprecation warning remains in the Python test suite.
It did not fail tests. The temporary HTTPS tunnel is intended for a team demo,
depends on this Mac remaining awake, and receives a new address/code after restart.
