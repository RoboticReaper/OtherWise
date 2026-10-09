# OtherWise catalog production 001 — independent source and clarity audit

Work in `/Users/baorenliu/Documents/Programming/Python/ProductSpace`. Read the catalog requirements in `docs/superpowers/specs/2026-10-07-recommendation-system-design.md`, the production README/policy, the assigned batch's `audit-sample.json` and `frozen-initial/manifest.json`. The coordinator supplies your exact sampled IDs and output directory. You must not have authored those cards. Write only the assigned audit directory; author repairs are separate.

Inspect the substantive public passages supporting every assigned card claim and all its attached relationships. Reopen sources or inspect preserved original text, recording the actual method and locator. Report inaccessible evidence, uncertainty and errors honestly. A plausible claim, search snippet, Wikidata label or an author's `claims_supported` flag is insufficient verification. Bound repeated URL failures; use an inspectable authoritative alternative or leave the item unresolved.

Judge the 25-word explanation against its scope. It should identify the intended meaning and provide one concrete point to explore. Necessary domain terms are allowed for deeper concepts. Flag missing conditions, jurisdiction, population, historical qualification or ambiguous referents. Broad fields should use everyday language. A named subject needs a learning takeaway beyond its classification. These are evidence/clarity checks, not predictions of human interestingness.

For every relationship, verify the target meaning and the type/assertion against the passage. An editorial link may have sourced premises without a source asserting that taxonomy. An object, context, ingredient, study target or comparison does not automatically establish an application parent. Check all attached edges, including those not cited by the card body.

Write `initial-review.json` with `schema_version:1`, `batch_id`, `reviewer`, `authored_sampled_cards:false`, `draft_candidate_sha256`, `reviews` (array), `source_access_failures`, and `limits`. Each review records:

- `id`, `stratum` (`random` or `risk`), `card_version`, `status` (`verified`, `needs_repair` or `unresolved`).
- `claims`: an array of substantive claim groups with `url`, `locator`, `inspection_mode`, `supported` and concise reasoning. If a group uses several passages, put those three location/method fields in each item of a `passages` array instead.
- `clarity`: `meaning_clear`, `concrete_takeaway`, `qualification_preserved`, `scope_appropriate_wording` (booleans), plus a short note when needed.
- `relations`: one entry per attached edge, with `target_id`, `type`, `assertion`, `supported`, actual source passage and concise reasoning. Record passage locations/methods using the same fields as claims.
- `findings`: severity (`material` or `minor`), affected field, concrete problem, evidence and proposed repair. A substantive citation failure or ambiguity is material; label presentation polish may be minor.

Also save a concise `review.md`, an inspection log and source-derived word budgets. Keep direct quotations short and obey each source's allowance across your notes; record supporting sections without reproducing long passages. Distinguish original findings from later outcomes. Do not change the sample, silently repair an author file or replace a sampled failure with a more favorable card.

If a finding plausibly affects other cards sharing a source or formulation, identify them as follow-ups; the coordinator expands review. After the author repairs a bundle, write a separate `recheck-NNN.json` binding exact current card versions and input hashes. Recheck changed claims and all attached relationships. Preserve `initial-review.json` and the frozen draft unchanged.

Recheck files contain `authored_sampled_cards:false`, `current_input_sha256` mapping project-relative inspected input paths to their SHA256 hashes, and `reviews` with the same fields as the initial review. Each rechecked review also has `current_card_sha256`, computed from the exact assembled current card with `STOCK.digest` in the production `assemble.py` module. A change to any sampled card requires a recheck even if its initial review passed. Keep initial findings in the initial file; a successful recheck records what resolved them.

Return compact counts by random versus risk strata, material/minor findings, unresolved evidence and paths. A passing fixed sample does not certify the unsampled population or establish recommendation effectiveness.
