# Research batch 008 evidence

One bounded 200-card continuation of the validated catalog workflow. [The agent prompt](../../../docs/catalog-research-batch-008-agent-prompt.md) defines selection, source research, independent audit and acceptance. [Status](status.json) records the current gate.

- [Canonical working baseline](baseline-index.json) and [pinned input manifest](baseline-manifest.json): 35,743 active identities, including the selected pilot revision and 108 reviewed redirects. Four old local baseline IDs are retired in this working index with their full records retained.
- [Coverage and audit plan](coverage-plan.json): 23 domains, public-source selection, 200-card limit and explicit novelty/relationship goals.
- [Preparation checks](preparation-validation.json) and [assembler tests](assembly-unit-tests.txt): current hashes and nine new-batch adapter tests.
- [Frozen selection](selection-manifest.json), [reservation checks](selection-reservation-validation.json) and `selection-snapshots/`: 200 approved subjects, 180 new and 20 existing controls. The 22 named subjects fall three below the soft goal of 25; named methods remain ideas.
- Research partitions: `research/science/`, `research/systems/`, `research/culture/`. All 200 cards and author reviews are complete; each retains approved identities, required control versions and the shared reservation hash.
- [Independent audit protocol](audit-protocol.md): freeze the initial draft before selecting 20 random new cards and 20 disjoint cards with specified risks. Initial evidence and samples remain available through repairs.
- [Initial freeze](frozen-initial/manifest.json) and [fixed sample](audit-sample.json): the 40 independent checks cover all 23 domains. Checker outputs are in `audit/`; initial and repaired results remain separate.
- [Full draft contract checks](draft/contract-validation.json): 1,873 checks passed against frozen catalog inputs, with the [concurrent resolver edit](external-workspace-changes.json) explicitly recorded. The original pinned code is retained; this batch did not modify that backend file.
- [Actual rejection check](regression/actual-rejection-validation.json): an intentionally invalid target is rejected and the previous valid 200-card output remains intact. `regression/` files are software-test evidence, not research candidates or active inventory inputs.

The final researched candidate is [research-batch-008.json](/Users/baorenliu/Documents/Programming/Python/ProductSpace/data/catalog-candidates/research-batch-008.json). Intermediate proposals, draft candidates, historical baseline records and software-test mutations have distinct roles. The current validated pilot remains at `../scale-pilot-001/current.json` throughout this work. Operational import is a separate action.

## Completed acceptance

[Results](/Users/baorenliu/Documents/Programming/Python/ProductSpace/docs/catalog-research-batch-008-results.md), [completion manifest](/Users/baorenliu/Documents/Programming/Python/ProductSpace/data/catalog-candidates/research-batch-008-build/completion-manifest.json), [final contract checks](/Users/baorenliu/Documents/Programming/Python/ProductSpace/data/catalog-candidates/research-batch-008-build/final-contract-validation.json) and [audit summary](/Users/baorenliu/Documents/Programming/Python/ProductSpace/data/catalog-candidates/research-batch-008-build/audit-summary.json) record the completed batch. All 200 cards pass structural/provenance checks and author review. All 40 fixed independent checks plus three supplementary cards pass after repairs, with initial findings retained. Eleven bundles changed, including five descriptions; repaired versions and rechecks are bound to the final bytes.

The named-subject soft goal is short by three. Three fine-scope parent gaps are documented. Author-phase pending labels inside exact input snapshots are historical; the completion manifest resolves those gates for this candidate. Source inspection is sampled, and operational import is still separate.
