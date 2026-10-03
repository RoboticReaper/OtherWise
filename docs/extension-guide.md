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

## A two-minute demonstration

The header's **Language / 语言** selector switches between English and Simplified
Chinese and remembers the choice on this device. Chinese support covers UI only:
the recommendation system and local catalog remain English. Enter interests in
English; topic names, domains and descriptions retain their original English text.
Switching language preserves drafts, selected candidates and loaded recommendations.
The **Cards / List** toggle beside **A little beyond** switches recommendations to
compact rows. Both layouts retain search, save and dismiss actions. In List view,
long descriptions can be expanded. The layout preference is also saved locally.

1. Add **Gardening** manually. This saves an interest without accessing history.
   Alternatively, **Review recent browsing** asks Chrome for permission, processes
   up to 5,000 recent visits locally, then shows a candidate inbox. Choose topics and
   **Save selected**. Nothing in this inbox is uploaded before confirmation.
   The candidate inbox shows ten topics per page. Selections remain checked across
   pages; **Select this page** applies only to the visible page. The save button's
   count includes every selected page, so you can confirm the total before saving.
2. Click **Find ideas**. Up to ten nearby topics appear, with the connection to a
   saved interest and Google/YouTube search buttons.
3. Search one topic. Open **Map** to see an exploration path. Searching does not
   change saved interests or indicate expertise.
4. Click **Save interest** when a topic interests you. The next path starts nearby.
   On the map, choose an earlier saved interest and **Explore from here** to return.
5. Switch to **Explore across interests** to use all saved interests. Each new
   confirmed interest after the first onboarding selection increases the range
   once, capped at eight increases. Searches and refreshes do not widen it.

## Optional ongoing updates

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
- Only saved interest names and discovery preferences are sent to the service.
  The server has no profile database or request-body logging. The service and
  HTTPS tunnel also receive network information. This is not anonymous browsing.
- Chrome history deletion removes matching derived evidence and candidates.
  Explicit interests and OtherWise exploration paths remain until removed/reset.
- **Clear browsing data** removes derived evidence and candidates. **Reset OtherWise**
  additionally removes interests, map, settings and access code from the extension.
- No Chrome sync storage, incognito collection, account-wide YouTube history,
  remote metadata fetching, or private-browser-profile access is used.

## Current scope

The catalog contains 3,452 English topics. Local extraction matches page-title
phrases and a few explicit aliases. It can miss implied topics, unrecognized
phrases, missing titles and non-English content. YouTube visits are recognized
from Chrome history; video tags and the account's complete watch history are not
imported. Add an interest manually when needed.

The Galaxy map groups domains and records paths. Distances in its visual layout
are illustrative, not measured embedding distances or knowledge mastery. The
recommendation engine explores semantic topics; it does not assess political
stances or prove an effect on polarization.

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

For an offline design preview, serve `extension/` locally and open
`sidepanel.html?preview=1`. This mode has a prominent sample-data banner and never
reads Chrome history or calls the recommendation server. Production never falls
back to samples.

Automated browser checks use a separate temporary Chromium profile and synthetic
page titles. The integration fixture pregrants history/service permissions in a
test-only copy of the manifest; the distributed manifest retains optional grants.
Native Chrome permission prompts still require the user's choice during install
and first use.

`npm run test:ui` checks pagination with 103 synthetic candidates, cross-page
selection, language persistence and preservation of drafts in an isolated browser.
It uses the same optional Playwright setup described below and makes no API calls.

To rerun the integration check with Node 22+, install Playwright as an optional
development tool (`npm install --no-save playwright`, then `npx playwright install chromium`),
build the extension, and run `npm run test:browser`. It starts its own loopback
test API with a fresh test token, requires the model already cached, and shuts it
down afterward. `OTHERWISE_CHROMIUM` can point to an existing Chromium executable;
`OTHERWISE_PLAYWRIGHT_MODULE` can point to an existing Playwright module. It never
uses your normal browser profile. Temporary fixture profiles contain synthetic
data only and can be removed from the system temporary folder after the run.
