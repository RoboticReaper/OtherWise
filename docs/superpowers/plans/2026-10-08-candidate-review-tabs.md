# Candidate Review Tabs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan inline.

**Goal:** Keep Interests compact with separate Saved and To review tabs and bounded candidate review.
**Architecture:** Reuse the existing controller and approval actions. Add one small pagination/height helper, tab state in app.js, a native import dialog and scoped workspace CSS.
**Tech Stack:** Vanilla JavaScript, CSS, Node test runner, existing browser regression harness.
**Spec:** docs/superpowers/specs/2026-10-08-candidate-review-tabs.md

## Global Constraints

- Keep this update local and preserve concurrent changes in the primary checkout.
- No backend, dependency, profile or recommendation changes.
- Candidate pages contain five items in the side panel, eight in Dashboard.

## Review Focus

- 306 candidates remain fully reachable without growing the outer page.
- Long titles and 320px Chinese layouts keep footer controls visible.
- Cross-page selections and manual drafts survive tab/main-page navigation.
- Empty review and last-page deletion retain a usable focus target.
- Import dialog closes with Escape and requires explicit import, preserving privacy.

### Task 1: Bounded candidate pagination

**Files:** Create extension/ui/candidate-review.js and extension/tests/candidate-review.test.js.
**Interfaces:** candidateReviewPage(items, page, desktop=false) returns paginate's result. reviewPanelHeight(viewportHeight, panelTop) returns the available height, clamped to 260–680px with 28px bottom space.

- [x] Write tests for all 306 IDs across both page sizes, last-page deletion/empty state, cross-page selection and available viewport height.
- [x] Run the new test file; expect failure because the new helper is absent.
- [x] Implement the helpers using existing paginate and reuse togglePageSelection in the UI.
- [x] Run the new test file; expect all passing.

### Task 2: Tabbed review and import dialog

**Files:** Modify extension/ui/app.js, extension/ui/i18n.js, extension/ui/workbench.css, scripts/test_ui_browser.mjs and docs/extension-guide.md.
**Interfaces:** Consume candidateReviewPage/reviewPanelHeight; use existing importHistory and APPROVE actions unchanged.

- [x] Update browser regression expectations for tab isolation, tab keyboard behavior, footer bounds, five-row pages, preserved selections/drafts, empty and last-page dismissal.
- [x] Implement accessible secondary tabs, bounded list/footer, scroll retention and native import dialog with existing privacy copy.
- [x] Run all Node tests and build; expect passing and generated extension containing the new helper.
- [x] Verify 306 synthetic candidates through actual UI at 320px, 390px and desktop; capture bounds, screenshots, keyboard/dialog/approval checks.
- [x] Request independent code review, address material findings, integrate with three-way merges and verify the final primary build.

## Execution record

Changes remain local; commits are not needed for this user request. Tests and browser evidence are recorded during implementation.

Task 1 complete: new helper absent → RED; Node candidate-review tests → GREEN, 5/5.

Task 2 verification: Node suite 223/223 passed; extension build passed. Actual CUA checks at 320×850 and 390×850: outer document matches viewport; review footer bottom 805px. 306 topics are paginated 5/8 per page. Manual draft, cross-page selection, tab keyboard navigation, native dialog Escape/cancel/7-day retention/explicit import, six-item approval, empty inbox and final-page deletion were verified. Dashboard 1280×900 stays within viewport with footer bottom 855px.
Final review: independent reviewer found no Critical/Important issues; declined to judge none.
Final: minor (deferred): The 260px minimum can require outer scrolling in very short windows or with an expanded guide; documented the fallback.

Final primary integration: preserved 39 other modified files; kept the concurrent sound approval and lifecycle handlers. Primary Node suite 226/226 passed; Python quick suite 407 passed, 2 skipped, 2 layout integration tests deselected (existing Starlette deprecation warning). Build passed and 56 packaged extension files match their sources. Updated the native extension browser regression's history-import navigation to use the tab and explicit dialog submission. Browser scripts were syntax-checked; equivalent visible interactions were performed through CUA instead of running those automation scripts.
