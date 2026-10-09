# Catalog production 001 implementation plan

**Execution correction, 2026-10-09:** The user intends to send a comprehensive prompt to an external workspace AI, rather than run internal research subagents here. Internal work has stopped. Preserve the 35 individually completed and independently verified cards; hand the remaining 165 to the external AI using `docs/catalog-research-batch-009-external-agent-prompt.md`. The full 200-card checkpoint remains incomplete. Review its returned bundle before the remaining 4,800. The parallel-worker details below record the earlier execution and are not instructions to restart it.

> **For agentic workers:** Use the agreed workspace-agent research workflow. The coordinator executes validation and reconciliation; parallel researchers own separate domain directories, followed by reviewers who did not author the sampled cards.

**Goal:** Add 5,000 distinct first discovery cards, validating the first 200 under the new 25-word limit before producing the remaining 4,800 in 24 further bounded batches.

**Architecture:** Freeze the active inventory and researched-card union. Reserve previously undescribed identities by domain, research source passages, and write original short cards into separate candidate files. Accept each batch only after structural checks, author checks, independent random/risk audits, repairs and preservation checks; retain progress and exact evidence in the production directory.

**Tech stack:** Workspace research agents, web source inspection, JSON artifacts, existing Python catalog validation conventions, local file-management scripts. No per-concept AI API client.

**Spec:** `docs/superpowers/specs/2026-10-07-recommendation-system-design.md`, Catalog scope and discovery cards / Concept identity and inventory, plus the user's approved 200 then 4,800 production milestone.

## Global constraints

- New card bodies contain 1–25 whitespace-separated words; titles and source links are outside the budget.
- Existing descriptions remain byte-identical. Production counts first cards for previously undescribed identities, not rewrites or duplicated records.
- Cover all 23 domain groups and all four scopes, including named subjects when they have a distinct learning takeaway.
- Use canonical identities and retain ambiguity; do not merge labels or nearby embeddings without evidence.
- Preserve imported descriptions/raw records separately from cards and retain inspected source locators.
- Relationships require resolved IDs and supporting factual premises; distinguish source assertions from editorial connections.
- Use the public frozen inventory; private recommendation preference ratings are excluded from selection.
- Keep candidates separate from operational catalog data, embeddings and recommender defaults.
- Report actual usage only when exposed; otherwise record unavailable, never inferred token accounting.

## Review focus

- Compression drops a necessary condition, jurisdiction, population or historical qualification: choose fewer claims and repair before acceptance.
- A named subject receives only a generic classification: require a concrete source-supported learning takeaway.
- An existing identity already has a card: exclude it from production rather than rewriting it.
- A citation identifies the subject but does not substantiate the card: inspect the substantive passage and replace unsupported claims.
- A relation invents a hierarchy from a comparison or context: qualify it as editorial/related_to or record a parent gap.

## Tasks

- [x] Freeze the active union and protect prior card artifacts; baseline is 35,923 identities and 1,467 described identities.
- [x] Research and reserve the first 200 previously undescribed identities in batch 009. Three disjoint domain partitions contain 70 science, 65 systems and 65 culture cards.
- [x] Draft and author-check every accepted card, with exact evidence and original imports, under the 25-word limit.
- [ ] Freeze the draft before choosing 20 deterministic random and 20 disjoint risk samples. Review substantive support, short-card clarity and every attached relation independently; preserve initial findings and rechecks.
- [ ] Validate the candidate, repeated/reversed assembly, unknown targets, stale baselines, word limits, duplicate IDs, and legacy protection. Accept only after all material findings are resolved.
- [ ] On a passing checkpoint, repeat the same process for 24 further batches, maintaining the exclusion set and cumulative accepted count after each batch. A failed gate triggers repair or a valid partial report rather than silent acceptance.
- [ ] Save a combined production candidate, per-batch manifests and a concise final report showing accepted yield, coverage, audits, failures and remaining work.

## Execution ledger

The user explicitly authorized this workflow with “ok. do that”; no further permission is required for reversible research and candidate-file creation. Planning records the already agreed workflow. Production artifacts live in `data/catalog-candidates/catalog-production-001/`; older research/build artifacts are immutable inputs. Operational integration and formal human research remain separate tasks.
