> Final execution: all 12 actual researched-output regressions passed, with no failed or unrun cases. See [actual results](actual-regressions/final-audited-001/regression-results.json) and [published assembly checks](actual-output-results.json). Preparation-time pending statements below are historical.

# Prepared final-output regression runner

**Preparation status: ready. Actual researched-output execution: not run.**

The original pre-research gate evidence is preserved. This new runner was exercised only with small synthetic five-batch test workspaces. The latest isolated utility suite has **31 passing tests**: the original 25 plus six new runner tests. `actual-runner-final-full-suite.txt` records the complete fresh result. Test-first failures are preserved in `actual-runner-red-tests.txt` and `actual-runner-pairwise-red-tests.txt`.

## Final run, only after coordinator authorization

1. Freeze the five final audited canonical candidates, pinned baseline and identity decisions.
2. Record their exact byte SHA-256 values in a manifest matching `actual-regression-expected-inputs.template.json`. Set `authorization` to `run_on_final_audited_inputs` only when the coordinator authorizes this run. Do not fill it from in-progress drafts.
3. From the isolated `work` root, run:

```sh
python data/catalog-candidates/scale-pilot-001/merge-validation/actual_regression_runner.py \
  --expected-inputs data/catalog-candidates/scale-pilot-001/merge-validation/final-audited-inputs.json \
  --run-id final-audited-001
```

The runner reads exactly these seven canonical files:

- `data/catalog-candidates/research-batch-003.json`
- `data/catalog-candidates/research-batch-004.json`
- `data/catalog-candidates/research-batch-005.json`
- `data/catalog-candidates/research-batch-006.json`
- `data/catalog-candidates/research-batch-007.json`
- `data/catalog-candidates/scale-pilot-001/baseline-index.json`
- `data/catalog-candidates/scale-pilot-001/identity-decisions.json`

It refuses a missing authorization marker, stale hash, incomplete/extra manifest input set, unsafe run ID, or existing run directory. It checks hashes again while copying the inputs and verifies the canonical files, any prior canonical catalog, and original gate-results file remain unchanged afterward.

Results go only into a new directory:

`data/catalog-candidates/scale-pilot-001/merge-validation/actual-regressions/final-audited-001/`

The summary is `regression-results.json`; it records passed, failed and unrun cases separately, exact input/tool/runner hashes, commands, output paths and retention hashes. Each case retains its own inputs, reports, stdout/stderr and any quarantine artifacts. Existing runs are never overwritten. Use a new run ID after a correction and provide newly authorized exact hashes.

**The runner never publishes or replaces `scale-pilot-001/catalog.json`.** Its unchanged assembly and all mutation outputs are isolated regression artifacts. The coordinator must separately decide whether the final researched catalog is accepted and published.

## Twelve checks

1. Unchanged five-batch assembly, reversed input order and repeated import, using the existing `verify-actual` command and requiring all five batches. Distinct concepts, references, canonical content and decisions must agree.
2. Independently verify all active source namespaces, original identifiers/metadata/input hashes, and every selected evidence/relationship reference against the actual inputs. Record naturally colliding local IDs.
3. Preserve actual shared-name groups and every supported meaning. Require complete reviewed distinctness coverage, including multiple pairwise decisions for a name with three or more meanings. If no actual ambiguity group exists, report this check unrun rather than inventing one.
4. Verify exact original input/card snapshots, provenance namespaces and alias retention.
5. Rename a used reference in each of two isolated copies to the same local ID. Rewrite the copies' local links, then verify the combined scopes, evidence and relationships independently. This is only a reference-ID collision mutation.
6. Preserve actual `retrieved_at`-only metadata when available. Otherwise remove the redundant date field from a copied source, preserving its original timestamp; if no timestamp exists, use an explicitly synthetic timestamp. The report distinguishes these modes and makes no fabricated historical retrieval claim.
7. Derive a small conflicting-version pair from an actual card/source bundle. The copied relationship list is cleared for this narrow mechanics test, and one copy gets a marked synthetic prose/version change. Verify conflict quarantine and byte-for-byte retention of the previously valid, unchanged assembly.
8. Make an explicit hash-bound choice between those synthetic competing versions. Verify the selected version and both original records survive, including reversed/repeated import checks.
9. Remove a mandatory card field in an isolated five-batch copy. Require malformed-input quarantine and unchanged last-valid bytes.
10. Add an intentionally nonexistent target in an isolated five-batch copy. Require unresolved-target quarantine and unchanged last-valid bytes.
11. Verify actual reviewed-equivalence mechanics if actual merge decisions exist. Otherwise construct two clearly labeled copies of one actual card under synthetic IDs/names, with a reviewed exact-copy mapping only for the software test. Verify one resulting identity, both names, all scoped evidence and both original records. This never claims that two different researched subjects are factually equivalent.
12. Recheck all protected original input/output/gate hashes.

All changed copies carry `batch.regression_only`, `counts_toward_research: false`, and a warning against treating them as accepted research. The run-level `artifact-role.json` labels every artifact as regression-only. Synthetic derived subsets are explicitly reported and do not pretend to be full 1,000-card candidates. The unchanged run always uses all five complete canonical files.

Technical hash-bound choices are rebound only inside mutation copies when an otherwise unchanged decision refers to a file whose regression metadata/reference spelling changed. These are not new research identity decisions.

## Reproduce preparation tests

```sh
python data/catalog-candidates/scale-pilot-001/merge-validation/test_actual_regressions.py
python -m unittest discover -s data/catalog-candidates/scale-pilot-001/merge-validation -p 'test_*.py' -v
```

The runner's `--fixture-only --work-root ...` override exists for those isolated tests. It must not be used to characterize test fixture results as actual researched-output acceptance.

Exit 0 means all regression checks passed; exit 1 means failed or explicitly partial/unrun checks; exit 2 means preflight/input misuse. Regression results do not certify source accuracy or independent audit completion.
