# Sound effects verification — 2026-10-08

The local extension now uses the user-selected `1.wav` for Save, `2.wav` for
Explore and `Bloom.wav` for a newly lit Galaxy neighborhood. The original files
are unchanged. Packaged copies use a constant gain toward -25 dBFS RMS with a
-3 dBFS peak ceiling, retaining their timing, pitch, stereo channels and 48 kHz
sample rate. Source hashes and applied gains are recorded in
`extension/assets/sounds/provenance.json`.

Automatic audio starts disabled at 20% volume. The bilingual Settings section
offers an enable switch, volume slider and three explicit previews. Settings
persist through the real controller and Chrome storage, share across surfaces,
and do not invalidate recommendations, require permissions or call a service.

Save requires a successful new interest; batch approval is one event.
Explore waits 450 ms for a user-selected Focus center and can repeat for the same
center or domain.
Bloom replaces Save only when an exploration-mode Galaxy is visible and a save
adds at least five newly lit topics; subsequent new neighborhoods can play again.
At the user's request, all long cooldowns and per-domain, per-session and rolling
count limits were removed. Automatic events in a window share only a two-second
cooldown to prevent rapid repeated playback. Ineligible events are discarded.
Navigation, center changes, blur,
hidden documents, mute and close cancel playback; action lifecycle tokens
discard saves that complete after a cancellation, even after returning.

Validation completed:

- Full `npm test`: **226 passed**, Node v24.19.0 (the project requires Node 22+).
  Fifteen focused sound tests include controller acceptance/reload, safe legacy
  defaults, no API/permission calls, state-delta semantics, overlap and search
  exclusion, batch deduplication, exact two-second cooldown boundaries, repeated
  same-domain Explore and Bloom, removal of rolling count limits,
  preview isolation, media failures and lifecycle cancellation.
- `scripts/test_sound_effects_browser.mjs`: **passed** in an isolated Chromium
  profile. All three packaged WAVs decode and reach native `playing` events.
  Checks cover repeated Save, same-domain Explore and replacement Bloom after
  two seconds, rapid-trigger suppression, muted/background
  updates, real side-panel/Dashboard preference synchronization, persistence
  through reload, delayed real saves after navigation and blur/refocus, and
  Chinese controls at 390 px. No page errors or outbound HTTP requests.
- `scripts/test_map_workspace_browser.mjs`: **passed**, covering temporary
  centers, empty Focus, retained cameras/DOM, keyboard entry/return, independent
  windows, localization and offline neighbors. Its unconfigured-service fixture
  now explicitly sets an unconfigured address; the existing local-service
  default may otherwise connect to a running backend.
- Build and whitespace checks passed. WAV bytes and the sound module are present
  in `dist/OtherWise-extension.zip`; archive audio matches the source assets.
- Desktop and 390 px Chinese Settings screenshots were visually inspected.
  Browser results/screenshots are in `.cache/qa/sound-effects/`.

Independent review found and prompted fixes for the real controller's setting
whitelist, audio continuing after returning to Galaxy, and delayed Save audio
after navigation or blur. Regression tests reproduced each issue before repair.

Browser checks verify decoding, playback events and behavior; subjective audio
quality was not assessed by listening. Reload the installed unpacked extension,
then enable or preview sounds under Settings → Sound effects. The user's actual
Chrome profile was not used or reloaded, and no commit, push or release was made.
