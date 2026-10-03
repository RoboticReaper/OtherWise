# OtherWise extension guide

## Install

1. Unzip `OtherWise-extension.zip` and keep the resulting `otherwise-extension` folder.
2. Open Chrome's **Extensions → Manage extensions** (`chrome://extensions`).
3. Turn on **Developer mode**, click **Load unpacked**, and select that folder.
4. Pin OtherWise in the extensions menu. Click its icon to open the side panel.
5. In **Settings**, paste the host's **Service address** and **Team access code**.
   Click **Save settings** and allow access to that service address when Chrome asks.

The shared demo works while the host's Mac and demo processes are running. A newly
started temporary tunnel can have a different address. The host shares both the
address and code; the ZIP contains neither. The host can use `http://127.0.0.1:8000`
instead. A teammate must use the shared HTTPS address, not their own localhost.

## First opening and page navigation

The side panel starts on **Interests / 兴趣**. New profiles show a short guide beside the current page. It follows Interests,
Discover and Map, and leaves the page controls usable. Use Next/Back to
visit those pages, finish with **Finish guide**, or skip. On narrow screens, the
guide sits above the page in normal flow. Completion and skipping are remembered on this device.
**Settings → Getting started → Show guide** reopens it in either UI language.
The guide does not request history access, read visits or request recommendations.
Existing profiles with saved interests skip the automatic guide.

**Interests** contains the English keyword input, optional history review,
candidate inbox and saved-interest management. **Discover** contains recommendation
controls and results, plus a read-only summary of the interests used. Use
**Explore recommendations** or **Manage interests** to move between the pages.
Draft keyword input, candidate selections and loaded result pagination stay in the
current window when switching pages. The selected page is reflected in its URL,
so reload returns to the selected page. The Dashboard button and Dashboard's
initial no-parameter view open Map. Reset starts a fresh profile and shows the guide
again; it is not a way to refresh recommendations.

## A two-minute demonstration

The header's **Language / 语言** selector switches between English and Simplified
Chinese and remembers the choice on this device. Chinese support covers UI only:
the recommendation system and local catalog remain English. Enter interests in
English; topic names, domains and descriptions retain their original English text.
Switching language preserves drafts, selected candidates and loaded recommendations.
The **Cards / List** toggle beside **A little beyond** switches recommendations to
compact rows. Both layouts retain search, save and dismiss actions. In List view,
long descriptions can be expanded. The layout preference is also saved locally.
Both layouts show ten recommendations per page. Page changes use the already
downloaded batch and do not contact the server.

1. Open **Interests / 兴趣** and add **Gardening** manually. This saves an interest without accessing history.
   Alternatively, **Review recent browsing** asks Chrome for permission, processes
   up to 5,000 recent visits locally, then shows a candidate inbox. Choose topics and
   **Save selected**. Nothing in this inbox is uploaded before confirmation.
   The candidate inbox shows ten topics per page. Selections remain checked across
   pages; **Select this page** applies only to the visible page. The save button's
   count includes every selected page, so you can confirm the total before saving.
2. Open **Discover / 发现**, then click **Find ideas**. Up to ten nearby topics appear by default, with the connection to a
   saved interest and Google/YouTube search buttons.
3. Search one topic. Open **Map** to see the full interest galaxy and your exploration path. Searching does not
   change saved interests or indicate expertise.
4. Click **Save interest** when a topic interests you. The next path starts nearby.
   On the map, choose an earlier saved interest and **Explore from here** to return.
5. Switch to **Explore across interests** to use all saved interests. Each new
   confirmed interest after the first onboarding selection increases the range
   once, capped at eight increases. Searches and refreshes do not widen it.

## Specific concepts and feedback

In Discover, select **What to discover → Specific concepts**, then **Find ideas**.
The same interests, path/global mode, quantity and distance controls now search
3,642 sourced concepts across 69 areas. Every concept shows its observed graph
path, reading level when reviewed, and a link to its public source. A graph path
explains where it was found; it is not a prerequisite sequence or course outline.

Recommendation cards show source details and search/save/dismiss actions, without
Curious/Known/difficulty feedback forms. Previously saved feedback stays in this
browser and continues to affect specific ranking. **Saved feedback** lists these
ratings, ten per page, including concepts absent from the current batch. You can
clear an existing rating or undo the previous change; these actions rerank the last
valid request with the same seed and exposure snapshot. **Save interest** remains
separate from feedback.

**Reserve for less-seen areas** defaults to 30% and reserves positions for eligible
areas with fewer previously returned concepts. The requested share may not be fully achievable;
the interface shows the achieved count. It never expands the distance band.
Refresh starts a new seeded batch; each accepted concept increments its source area’s count once, and reranking does
not add exposures.
Undo works after reopening a window. **Clear all feedback** deletes ratings,
area recommendation counters and undo state while keeping saved interests. Reset removes them
along with the rest of the profile. Switching back to broad topics retains ratings
and returns to the original request format, without sending graph feedback.

Specific discovery sends only saved interest names, discovery parameters, saved
concept/area IDs and ratings, and area exposure counts. It sends no browsing URLs,
page titles, source links or unsaved drafts. The service builds the feedback profile
in memory and persists only public embeddings. A service failure retains saved
ratings; retry with **Find ideas**. The host must restart the updated backend for
`/api/discover`; the first startup may take longer while public graph vectors are
cached. An older backend shows an upgrade message rather than a replacement batch.

Galaxy/Focus continue to use the original broad catalog and fixed layout. Saved
graph concepts outside that catalog appear as custom interests without invented
coordinates. Reading levels are reviewed hints; unreviewed concepts show **Not
reviewed**, and the model does not measure a user's knowledge.

## Optional ongoing updates

### Recommendation settings

In Settings, set the requested quantity from **1 to 100** (default 10). This is
the maximum batch size; each page still shows ten. Saving changed parameters clears
the old batch. Click **Refresh ideas**, or enable automatic refresh, to use them.
Changing these numeric controls never approves or uploads browsing candidates.

Advanced controls expose the existing recommendation engine:

| API parameter | Default | Meaning |
|---|---:|---|
| `radius` | 0.28 | Distance at which a topic enters new territory; larger moves the boundary farther away. |
| `expansion` | 0.07 | Allowed distance outward from that boundary. |
| `overlap` | 0.015 | Allowed distance inward into familiar territory; this is a distance, not a percentage. |
| `max_overlap_fraction` | 0.20 | Maximum familiar share of the actual returned batch; 0.20 means 20%. |
| `diversity` | 0.20 | Preference for variety among selected topics. |
| `randomness` | 0.03 | Small ranking variation within the allowed distance band. |

Distance values use normalized angular distance from 0 to 1. Automatic expansion
adds 0.01 for each saved expansion level, up to eight levels, on top of `expansion`
(total capped at 1). **Reset defaults** edits the form; save to apply the defaults.
See `docs/parameter-guide.md` for tuning examples.

**Why fewer results after Not for me?** Dismissal hides a topic locally. When more
cached results remain, they fill the current page; otherwise the list gets shorter.
Dismissal does not make a new network request. Later responses are also filtered
against the local hidden list, which is never sent to the server. A larger requested
quantity can give you more to browse, but cannot guarantee a full batch: the catalog,
distance band and familiar-content cap still apply. The service never silently
widens your chosen band to fill the list.

### Background controls

Both controls start off and are independent:

- **Review new browsing locally**: recognizes topics from new Chrome visits,
  including YouTube pages. New candidates remain local until confirmed. Turning
  it off pauses analysis; enabling it again starts with new visits, without a
  background import of visits during the pause. A later manual history import is
  a separate explicit action.
- **Refresh ideas when interests change**: automatically requests recommendations
  using already saved interests after relevant changes. It never approves new
  candidates by itself.

The excluded-domain list is editable. Common email, account, document and banking
sites are excluded initially. This list cannot identify every sensitive topic;
review the candidate inbox before saving interests you want to share.

## Data and boundaries

- Raw URLs and page titles are used transiently on the device. Stored browsing
  evidence contains a salted URL hash, hostname, recognized topic IDs and visit time.
  Browsing-derived evidence/candidates expire after 30 days.
- Discover sends saved interest names and discovery preferences. Specific discovery
  additionally sends explicitly saved concept feedback and area exposure counts. Focus sends
  the current catalog topic ID, catalog/model/embedding identity and recommendation
  parameters only after an explicit **Get ideas** request. That topic can be unsaved;
  the Focus request contains no personal interests, browsing history, URLs or titles.
  The server has no profile database or request-body logging. The service and
  HTTPS tunnel also receive network information. This is not anonymous browsing.
- Chrome history deletion removes matching derived evidence and candidates.
  Explicit interests and OtherWise exploration paths remain until removed/reset.
- **Clear browsing data** removes derived evidence and candidates. **Reset OtherWise**
  additionally removes interests, feedback, exposure counts, map, settings and access code from the extension.
- No Chrome sync storage, incognito collection, account-wide YouTube history,
  remote metadata fetching, or private-browser-profile access is used.

## Current scope

The catalog contains 3,452 English topics. Local extraction matches page-title
phrases and a few explicit aliases. It can miss implied topics, unrecognized
phrases, missing titles and non-English content. YouTube visits are recognized
from Chrome history; video tags and the account's complete watch history are not
imported. Add an interest manually when needed.

The Galaxy map projects all public catalog topics into two dimensions, using
UMAP plus 15% domain anchors. This projection is approximate: its screen distances
are not the distances used to rank recommendations or neighbors, or evidence of knowledge mastery. The
recommendation engine explores semantic topics; it does not assess political
stances or prove an effect on polarization.

## Full dashboard and Galaxy

Click **Dashboard ↗** beside the side panel's navigation to open a full browser tab.
It shares saved interests, recommendations, language and settings with the panel
through this extension's local storage. No login, extra permission or data upload
is needed to open the dashboard or browse the public map.

The Galaxy displays all 3,452 catalog topics, even before you save an interest.
Search an English keyword or filter by domain, then select a search result or star.
The details show the original catalog description and ten nearest topics computed
in the original 768-dimensional space. Neighbor links and your recorded exploration
paths have different styles. Saved interests, recommendations and the current focus
are highlighted. Topic selection alone does not change your interests. Use **Save
interest** explicitly to add one; **Explore from here** opens its temporary Focus
neighborhood, including for an unsaved or gray catalog topic.

Drag to pan, use the +/− buttons or mouse wheel to zoom, and **Reset view** to return
to the full map. Touch pinch and keyboard controls are supported. Filtering,
selection and refreshing never recalculate star positions. Chinese changes interface
labels only; topic names and descriptions retain their original language.
Manually saved topics outside the catalog appear separately without invented positions.

## Semantic Focus and exploration mode

Inside **Map**, switch between **Galaxy / Focus**. A single star click opens details;
a double-click or the details' **Explore from here** button enters Focus. The button
also works with a keyboard or touch. Focus initially shows the center and its ten
nearest catalog topics from the local cache, without contacting the service. Use
the center search to choose any catalog topic, including one you have not saved.
The side panel uses a compact scene with scrolling details below the map; Dashboard
provides more room. **Back to Galaxy** restores the view, selection, search and domain
filter from before entering Focus. Escape closes details first, then returns.

**Get ideas** explicitly requests recommendations for the displayed center using
the quantity and numeric controls in Settings. The disclosure beside it explains
what is sent. Focus uses the base expansion setting; Discover's saved-interest
expansion level is not added. Viewing or changing the temporary center neither saves
it nor changes Discover's focus, recommendation mode or batch. Save, dismiss and
Google/YouTube actions remain explicit. A search records the searched topic as
explored; it does not save the topic or light its nearest topics. The temporary
center is the origin of a Focus search path, rather than an old Discover focus.

Nearest topics and recommendations have separate markers and text lists. Candidate
lists show ten rows per page, using the loaded batch. Paging and new batches do not
move existing stars or automatically zoom the camera. The radius is measured angular
distance in the original 768-dimensional vectors; direction comes from the global
map. Distances between surrounding stars on screen are not their semantic distances.
Details show the original catalog description and distance from the center. Overlapping
stars remain independently selectable in the lists. Pan, zoom buttons, wheel and
pinch adjust the view; **Reset view** fits the current scene. Reduced motion disables
waves, breathing and other movement while keeping state visible.

The optional **Galaxy exploration mode** setting starts off and synchronizes between
the panel and Dashboard. When enabled, saved catalog interests and each one's ten
direct nearest topics remain colored; individually searched topics also light up.
This is one layer, not recursive expansion. Other stars stay gray and selectable,
even under a domain filter. Selecting a star or receiving a recommendation does not
light its neighborhood. Removing an interest removes its contribution while retaining
points covered by another interest or a real search. Turning the setting off restores
the full colored map without deleting saved data.

Focus responses and temporary cameras are window-local memory, not lasting personal
records. The separate result cache holds at most 20 request keys. Changing service
configuration, recommendation parameters or relevant permissions invalidates stale
requests/results. Local Galaxy and nearest topics remain usable when recommendations
fail. Configure the service in Settings, retry a temporary failure, or update packaged
data when its version differs from the service. A late result for an old center must
not replace the current scene. Chinese remains interface-only; Focus does not offer
a route to a specified destination, Chinese recommendations or evidence of mastery.

The rendering primitives are selectively adapted from the teammate reference; see
[animation provenance](focus-animation-provenance.md). Current verification and
remaining integration/interaction checks are recorded in
[Focus verification](focus-exploration-verification.md).

## Troubleshooting and development

- **Cannot reach the service**: verify the host has started the demo, check its
  current address, and save Settings again to grant the new address permission.
- **Access code was not accepted**: replace the code with the current host code.
- **Warming up / busy**: wait briefly and retry. The demo loads a real model and
  allows one computation at a time, with 30 authenticated requests per minute.
- **No browsing topics**: visits may have no matching English catalog title, be
  excluded, or be older than the review window. Manual interests still work.
- After rebuilding, click **Reload** on Chrome's OtherWise extension card and
  reopen the side panel. Do not delete the unpacked folder while using it.

For an offline design preview, first build and serve `dist/otherwise-extension/`
locally, then open `dashboard.html?preview=1` or `sidepanel.html?preview=1`.
The public catalog map is real; the personal profile is a sample. This mode has a prominent sample-data banner and never
reads Chrome history or calls the recommendation server. Production never falls
back to samples. Preview tabs do not share a persistent profile; install the extension
to use the shared dashboard and side panel.

Automated browser checks use a separate temporary Chromium profile and synthetic
page titles. The integration fixture pregrants history/service permissions in a
test-only copy of the manifest; the distributed manifest retains optional grants.
Native Chrome permission prompts still require the user's choice during install
and first use.

`npm run test:ui` checks pagination with 103 synthetic candidates, cross-page
selection, language persistence and preservation of drafts in an isolated browser.
It uses the same optional Playwright setup described below and makes no API calls.
`npm run test:galaxy` checks the real packaged catalog map and the shared dashboard
in an isolated extension profile at desktop, side-panel, 390px and 320px widths.

To rerun the integration check with Node 22+, install Playwright as an optional
development tool (`npm install --no-save playwright`, then `npx playwright install chromium`),
build the extension, and run `npm run test:browser`. It starts its own loopback
test API with a fresh test token, requires the model already cached, and shuts it
down afterward. `OTHERWISE_CHROMIUM` can point to an existing Chromium executable;
`OTHERWISE_PLAYWRIGHT_MODULE` can point to an existing Playwright module. It never
uses your normal browser profile. Temporary fixture profiles contain synthetic
data only and can be removed from the system temporary folder after the run.
