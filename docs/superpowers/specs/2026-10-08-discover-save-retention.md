# Discover Save retention

Saving an interest from an open Discover page must keep that page's batch and reading position, including the remaining topics. Mark the saved topic Saved. Preserve original batch source and update time. This is independent of auto-refresh: off sends no new request; on can replace the display when its new result arrives.

Retain one trusted recommendation batch in local state for actions, including noncatalog specific concepts and service-worker restarts. Request invalidation still advances the generation and rejects old responses. The active UI session alone can keep displaying an invalidated batch; leaving Discover or reloading expires that permission. A fresh successful response, even empty, replaces the batch. Manual refresh keeps the old display while waiting, then replaces it on success.

Dismissal still removes a topic. Reset, interest removal, privacy/connection/discovery setting changes clear the retained batch. No history access, external sends, automatic refresh opt-in, API payload changes or new dependencies. Preserve current UI and concurrent work; integrate locally and rebuild the extension.
