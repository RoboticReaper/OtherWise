#!/usr/bin/env bash
# Run from the isolated work root AFTER researched candidates are frozen.
set -euo pipefail
python tools/catalog_combiner.py verify-actual \
  --inputs data/catalog-candidates/research-batch-003.json \
           data/catalog-candidates/research-batch-004.json \
           data/catalog-candidates/research-batch-005.json \
           data/catalog-candidates/research-batch-006.json \
           data/catalog-candidates/research-batch-007.json \
  --baseline data/catalog-candidates/scale-pilot-001/baseline-index.json \
  --decisions data/catalog-candidates/scale-pilot-001/identity-decisions.json \
  --output data/catalog-candidates/scale-pilot-001/catalog.json \
  --report data/catalog-candidates/scale-pilot-001/merge-validation/actual-output-results.json \
  --require-all-batches
