# Catalog research results

This directory stores catalog candidates, source evidence, audits, revisions, and validation tools. These research artifacts are separate from the operational catalog in `data/`; saving them does not import them into the recommendation system.

## Current selections

| Artifact | Role |
| --- | --- |
| [Research batch 001](research-batch-001.json) | Earlier reviewed research batch; source review is in `docs/catalog-research-batch-001-source-review.md`. |
| [Research batch 002](research-batch-002.json) | Earlier reviewed research batch; reviews are in `docs/catalog-research-batch-002-*.md`. |
| [Scale pilot, revision 002](scale-pilot-001/revision-002/README.md) | Selected 1,000-card pilot revision, including reconciliation and validation evidence. It supersedes the initial pilot candidates for subsequent selection. |
| [Research batch 008](research-batch-008.json) | Completed 200-card research batch; [build evidence](research-batch-008-build/README.md) records audits and repairs. |
| [Production 001 / batch 009](catalog-production-001/README.md) | Unfinished 200-card checkpoint: 35 completed cards are protected, and 165 cards remain for the external AI to complete or repair. The full batch has not passed acceptance. |

The frozen production baseline records 1,467 previously described identities. Batch files overlap through controls and revisions; their sizes must not be added to infer distinct catalog coverage.

A storage-time check confirmed that all 35 protected cards and their supporting source records are unchanged. The unfinished batch's science input differs from its embedded draft snapshot only in `batch.updated_at`; the snapshot consistency check therefore fails. Preserve both original records, and resolve this metadata difference in the external delivery's new assembly rather than treating the draft as accepted.

## Preservation and continuation

Existing descriptions retain their original wording and length limits. Newly produced descriptions have a maximum of 25 whitespace-separated words; titles and source links are outside that budget. The current rules are in the [catalog design specification](../../docs/superpowers/specs/2026-10-07-recommendation-system-design.md#catalog-scope-and-discovery-cards).

For the next research step, use the [external AI prompt](../../docs/catalog-research-batch-009-external-agent-prompt.md) and [handoff manifest](catalog-production-001/batch-009/external-handoff-manifest.json). Preserve the [35 completed cards](catalog-production-001/batch-009/completed-cards.json) exactly. Internal research agents are stopped, and the remaining 4,800-card expansion has not started.

`archive/`, earlier pilot files, frozen inputs, and regression fixtures retain historical evidence. They are not additional accepted catalog entries. Historical prompts describe their original runs; the current specification and external handoff govern future work.

Two historical transport artifacts remain local and are excluded by `.gitignore`: the pilot's `access-log.json` and the duplicate evidence-part-02 ZIP containing it. They contain a signed download URL. Selected catalogs, source inspection records, and audit reports are retained on this branch.
