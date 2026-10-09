# OtherWise scale pilot 001 evidence bundle

The final deliverables are work/data/catalog-candidates/scale-pilot-001/catalog.json, work/data/catalog-candidates/research-batch-003.json through research-batch-007.json, and work/docs/catalog-scale-pilot-001-results.md.

Read the results report first. The pilot is complete: 1,000 distinct cards, 819 new identities, 703 new fine-scope subjects (650 idea entities and 53 named subjects), and 158 named subjects. Batch 006 has an eight-card shortfall if the 120-per-batch fine target is interpreted to exclude named subjects. The report preserves audit findings, corrections, source/access limits and that counting distinction.

work/data/catalog-candidates/scale-pilot-001/completion-manifest.json is the final completion record. Earlier manifests and run snapshots describe their historical stages; a pending status in a frozen earlier snapshot does not supersede completion-manifest.json. Finalization/reviewed contains the exact candidates whose card/source records were independently checked, before metadata-only final completion bookkeeping.

Only the five explicitly named candidate files contribute accepted records. Do not recursively import every JSON file. merge-validation contains clearly labeled synthetic fixtures, regression-only variants, quarantine examples and duplicate historical snapshots; they never count as accepted research. The baseline is a separate pinned target/provenance snapshot, not an additional active catalog.

The fixed independent audit has 100 random-new and 100 disjoint risk-selected cards. Additional targeted checks have separate scopes and denominators. Do not pool them into an unbiased defect rate or interpret changed-field checks as exhaustive factual review of every unchanged claim.

Full downloaded public-page captures are not redistributed. Author-written support notes, URLs, locators, timestamps, capture hashes and access logs remain. archive-manifest.json verifies every included file and records omitted capture metadata. The original user-provided inputs, including the transfer ZIP, are included byte-for-byte. This packaging policy is separate from the 29 historical raw acquisition byte gaps reported for batch004.

To reproduce utility tests, work from the work directory:
python3 -m unittest discover -s research -p 'test_*.py' -v
python3 -m unittest discover -s data/catalog-candidates/scale-pilot-001/merge-validation -p 'test_*.py' -v

The actual-output regression runner and its instructions are in merge-validation/ACTUAL-REGRESSIONS.md. Use a new run ID; the retained successful run is final-audited-001. The actual-output-check.sh command verifies the five inputs, reversed order, repeated import and the existing combined output. No operational catalog, identity registry, embeddings, recommender defaults or participant-study files were changed. No further research expansion was executed.
