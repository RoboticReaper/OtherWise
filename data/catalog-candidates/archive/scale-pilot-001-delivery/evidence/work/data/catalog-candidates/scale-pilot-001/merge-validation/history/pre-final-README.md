# OtherWise pilot combining gate

Status: **passed before bulk research**. These small, labeled synthetic fixtures are not researched cards and must never be counted in the pilot catalog.

## Verified evidence

- `gate-results.json` records 25 passing CLI contract tests, 12 passing gate checks, commands, exit codes, retained-output hashes, and explicit unrun work.
- `commands.json` is the complete command list from the most recent reproducible gate run.
- `results/` holds actual fixture catalogs, reports, stdout/stderr, and quarantined failed inputs. Expected rejection scenarios count as passed only when the expected reason is present and any seeded valid output is byte-preserved.
- The compatibility probe loads the coordinator's actual frozen baseline index and resolves one of its 7,224 IDs. It does not emit baseline snapshot records.
- `red-test-output.txt` preserves the first 18 expected failures before the tool existed. `green-test-output.txt` preserves the first 18 passes.
- Hardening logs preserve initial test-helper mistakes as well as the corrected red run (five expected assertion failures) and the final 25 passing tests. Historical red results are not erased or presented as current failures.

Run from the isolated `work` directory:

```sh
python data/catalog-candidates/scale-pilot-001/merge-validation/run_gate.py
python -m unittest discover -s data/catalog-candidates/scale-pilot-001/merge-validation -p 'test_*.py' -v
python -m py_compile tools/catalog_combiner.py
```

The available isolated utility test suite is fully run. Operational application tests are explicitly unrun because this work does not change that application and the isolated pilot is not its full runtime checkout. No supplied/bundled script was executed.

## CLI

`tools/catalog_combiner.py` is standard-library Python. It performs no network calls and calls no AI service.

```sh
python tools/catalog_combiner.py combine \
  --inputs data/catalog-candidates/research-batch-003.json data/catalog-candidates/research-batch-004.json \
  --baseline data/catalog-candidates/scale-pilot-001/baseline-index.json \
  --decisions data/catalog-candidates/scale-pilot-001/identity-decisions.json \
  --output data/catalog-candidates/scale-pilot-001/catalog.json \
  --report data/catalog-candidates/scale-pilot-001/merge-validation/combine-results.json
```

`combine` explicitly constructs/replaces the combined candidate after all checks pass. `verify-actual` repeats assembly with reversed input order and a repeated first input, compares full canonical content and all decisions/counts, and also verifies an existing combined output matches. A mismatch is quarantined and never overwritten by `verify-actual`; inspect the discrepancy and explicitly use `combine` when a new reviewed snapshot should replace it.

`--require-all-batches` requires all five batch IDs, even for explicitly partial candidates. It does not pretend that each partial batch reached 200 cards. Each input is capped at 200 accepted cards.

The prepared command for the actual five researched outputs is `actual-output-check.sh`. It has **not been run on researched outputs yet**. Run it only after the five candidate files are frozen and all needed identity/version decisions are recorded. This future step is separate from the passed fixture gate.

Exit codes: 0 means passed; 1 means rejected/quarantined; 2 means command/path misuse. Inputs, pinned baseline and decisions are read-only. Input/report/output path collisions are refused. Successful output writes use a flushed temporary file and atomic replacement. Failed validation leaves existing combined output bytes unchanged and preserves input copies plus reason codes in `quarantine/` next to the report.

## Accepted input and output contracts

Candidates retain `schema_version: 1`, `batch`, `sources`, `concepts`, `issues`, `validation`. Only `research-batch-003` through `research-batch-007` may supply active concepts. The validator checks the required concept/source/evidence/relation fields, enums, nonempty claims/locators/rationales, positive card versions, absolute HTTP(S) URLs, local source resolution, the 30–50 whitespace-token card budget, unique local IDs, and a valid acquisition date or ISO acquisition timestamp. Strict JSON rejects duplicate keys and non-finite values.

A historical source with valid ISO `retrieved_at` and no `retrieval_date` is accepted and preserved without fabricating a date. New source acquisition requirements remain in the author contract. Separate source IDs, revisions and passages survive even when their URLs match; there is no URL-based deduplication.

The baseline accepts an object with `concepts` keyed by ID, a `concepts` array, or an `ids` array. Its exact file SHA-256 is pinned into the combined artifact. Its IDs are allowed relationship targets; baseline records are not added to the concept list. A pilot control can legitimately retain a baseline ID; `baseline_snapshot_records_added: 0` describes the absence of a baseline dump, not the absence of controls.

Combined active source IDs are `originating_batch_id::percent_encoded_local_source_id`. Each combined source retains `original_id`, `originating_batch_id`, `originating_input_sha256`, and all original metadata. Active evidence and relationship source IDs are rewritten together; targets of reviewed equivalences are rewritten as well. Direct self-relations and self-relations created by equivalence remapping are quarantined.

`batch.input_provenance` preserves every supplied candidate snapshot, including unselected competing batch snapshots, with an exact byte hash and an explicit original reference namespace `(batch_id, input_sha256)`. Snapshot source IDs and nested historical provenance are intentionally preserved as original evidence rather than silently rewritten. Those references resolve in the embedded original snapshot, not against the active combined registry. Previously explicit historical source origins remain unchanged.

`batch.concept_provenance` preserves full original records, their batch/hash-qualified original namespace, and a `combined_source_id_map` for their selected input sources. `batch.selected_card_versions` identifies each chosen active card. Sources from unchosen concept versions remain in the combined registry and all original snapshots remain available. Sources from unchosen competing batch snapshots remain in that snapshot's historical namespace, so they cannot overwrite the active revision.

`batch.alias_index` maps normalized labels/aliases to all accepted pilot meanings. It is a pilot-only lookup; the pinned baseline remains separate. Normalization uses Unicode NFKC, case folding and whitespace collapse. No fuzzy-label or similarity merge is attempted. Exact multiple-meaning collisions among accepted cards need a reviewed distinctness decision. Additional possible semantic duplicates must be centrally reviewed and listed under unresolved until adjudicated; the tool cannot discover every semantic overlap.

The canonical content hash is SHA-256 of compact, sorted-key UTF-8 JSON, before adding `validation.canonical_content_sha256`. It includes decisions, selected versions, all preserved input provenance and pinned baseline hash. Input order and repeated byte-identical imports cannot change it. It does not contain execution timestamps or arbitrary input paths.

## Identity decisions schema

The coordinator owns this file. Empty lists/maps are valid:

```json
{
  "schema_version": 1,
  "equivalences": [],
  "distinctness": [],
  "unresolved": [],
  "concept_versions": {},
  "batch_versions": {}
}
```

Each reviewed equivalence is:

```json
{
  "canonical_id": "stable:id",
  "member_ids": ["stable:id", "alternate:id"],
  "reviewed": true,
  "reason": "Why inspected evidence establishes one meaning.",
  "evidence": [{"url": "https://example.org/source", "locator": "Exact section", "note": "What establishes equivalence."}],
  "selected_card": {"concept_id": "stable:id", "batch_id": "research-batch-003", "input_sha256": "EXACT_64_HEX_INPUT_FILE_SHA256", "card_version": 1}
}
```

Equivalence groups must be disjoint/centrally flattened. All member IDs must resolve in the accepted inputs or pinned baseline, and the selected card must be present in the selected active input snapshots. The selected card supplies the main text; reviewed member aliases, domains, identity URLs, evidence, relationships and imported records are unioned without losing original records. Equivalence is an explicit review decision; a matching or similar label is never enough. A self-link created by union/remapping requires explicit repair rather than being silently removed.

A distinctness decision has `member_ids`, `reviewed: true`, `reason`, and nonempty `evidence` entries of the same shape. It authorizes the supported meanings to share an alias, without merging them. Record decisions against the final canonical IDs after equivalence reconciliation.

An unresolved review has `member_ids` and `reason`. If those IDs are present in the pilot/pinned baseline and at least one is an accepted pilot ID, assembly rejects it. Excluded unresolved candidates may remain in ordinary batch issues. Unresolved entries are never evidence of new accepted identities.

`concept_versions` maps a conflicting concept ID to `{batch_id, input_sha256, card_version, reviewed: true, reason}`. Any incompatible supplied records under one ID require a choice, regardless of their version numbers or input order. Hashes bind choices to exact artifacts, so stale choices cannot accidentally approve later edits.

`batch_versions` maps a batch ID with competing supplied snapshots to `{input_sha256, reviewed: true, reason}`. No newest-wins, highest-version-wins or last-input-wins rule is used. The rejected/unselected snapshot remains available in historical provenance.

## Boundaries

A structural pass cannot certify source accuracy, inspected passages, novelty, claims of independent review, coverage or yield. The author reviews, central identity reconciliation, frozen independent audits and final pilot report remain separate requirements. Actual researched-output tests remain pending until those outputs exist.
