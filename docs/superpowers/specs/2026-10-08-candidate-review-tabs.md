# Compact interest review

The user wants to stop expanded candidate review from stretching the Interests page.

- Interests has Saved / To review tabs. Saved is the default; each tab shows its count.
- Saved retains manual input, saved-interest search/management and Explore recommendations.
- To review uses a viewport-sized workspace with an independently scrolling candidate list.
- Candidate pages contain five items in the side panel, eight in Dashboard. Pagination and Save stay outside the scrolling list.
- Reviewing recent browsing opens a small native dialog containing the time range and existing privacy explanation. Import requires the explicit dialog button.
- Preserve drafts, selected candidates, current candidate page and list scroll when switching tabs or main pages. Reload preserves the selected tab via the URL, consistent with main navigation.
- Tabs support ArrowLeft/ArrowRight/Home/End, selected state, labelled panels and a single keyboard tab stop.
- Empty candidates and deletion of the last item on the last page remain usable. Long titles and Chinese copy stay inside the workspace.
- Retain the existing local-only candidate processing and explicit approval. No backend, dependency, profile or recommendation changes.
- Keep this update local and preserve concurrent changes in the primary checkout.
