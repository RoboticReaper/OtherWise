# Galaxy B and controls verification — 2026-10-06

Built local extension v0.1.12 in the topic-pool expansion checkout. The approved B geometry was regenerated from the unchanged 31,637×768 original MPNet array: maximum difference against the selected real preview is 6.661338147750939e-16. The catalog SHA, embedding identity/bytes, ordered topic IDs and every original ten-neighbor list match the pre-change fingerprints. B parameters are 12 neighbors, min_dist0.40, spread1.5, repulsion2.5, seed42, 300 epochs and zero anchor blend, with MDS/Procrustes preserving orientation. Packaged cache key: `3ea327b35f4611d8c4077cb02b88256385949ad736f63fc234eabf53dd2e0848`.

The existing owned local backend was restarted to load the endpoints and fixes; its endpoint and access code were retained. Pinned layout dependencies were installed in the project venv. A real authenticated job using neighbors20/min_dist0.60/spread1.5/repulsion2.5 completed with all31,637 coordinates. A follow-up public health probe returned ready in15ms; this is an observed local latency, not a guarantee.

Checks completed:

- Full Python suite: 386 passed, 2 skipped, including exact KNN/cache/auth/strict control/source validation, actual UMAP and identical-parameter retry after failure. Existing numerical-library warnings; runtime process/socket tests use escalation.
- Full Node suite: 186 passed, including settings normalization, trusted transport identity/IDs, stale preview completions, labels and async editor Save recovery.
- Real packaged controls browser test: passed; authenticated public-only upload, nondefault UMAP geometry, default save and Settings edit, Restore B, independent windows, fit retaining query/domain/selection, original neighbors, independent label flags, native fullscreen surviving label persistence and Save default, Escape, 390px editor, zero page errors. Test-only copied manifest grants loopback access; history remains ungranted. The user's installed Chrome profile is untouched.
- Packaged Galaxy regression: passed at1440/390/320px, true neighbors, search/filter, language/profile sync, pointer/keyboard/two-finger gestures, custom interests, offline fixture and no outbound requests.
- Map workspace regression: passed; zero-upload local Focus, Settings return, retained cameras/DOM, independent window centers, keyboard focus restoration, offline public candidates and localized error guidance.
- Build and whitespace verification passed; unpacked folder and ZIP contain v0.1.12 and the final B asset.

Corrections exercised during integration: failed jobs can retry identical controls; same-map redraws retain the fullscreen ancestor chain; detached Map return never uses the mounted-map update path; editor Generate/Save controls recover after successful or rejected saves. Progress stage names are localized.

Artifacts: `.cache/qa/galaxy-controls/{galaxy-b,layout-editor,mobile-editor,settings,custom-layout}.png`; browser result and logs in that same directory. Reproduce using `scripts/test_galaxy_controls_browser.mjs` with the documented Playwright runtime variables and an already-started local backend. Existing Galaxy and map workspace browser scripts cover regression behavior.

Custom geometry belongs to the current window. Save default stores parameters for future Generate preview requests; opening another window/reloading starts with the packaged B map. Dynamic preview needs the connected backend; offline B, controls and labels remain usable. Recommendations always use original high-dimensional distances. Reload the installed unpacked extension to pick up this local build; no release, remote push or installed-profile reload was performed.
