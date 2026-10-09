# Batch 008 independent source audit

The initial assembled draft and all three source shards are frozen as byte snapshots with SHA-256 hashes before checking their claims. The audit uses the coverage plan seed `otherwise-batch-008-2026-10-08-v1` to select 20 new identities with `random.Random(seed).sample(sorted(new_ids), 20)`. Another 20 disjoint identities are selected for meaning boundaries, named objects, qualifications, technical mechanisms and graph assertions, while extending domain coverage where possible. Record the targeted selection reasons before the audit begins.

Each sampled identity retains its initial card version, full card, source bundle and all attached relationships. The sample does not change after a finding, repair or removal. An independent checker must not have authored the cards being checked. Checker output is separate from author files.

For each sampled card, inspect the actual cited passages and check the intended subject, each substantive body claim and every attached relationship. Record the URL, locator, actual inspection mode, access failures and limitations. A source-asserted relationship requires the actual directional relation; an editorial relationship requires supported factual premises and an honest inference label. A snippet or identity label cannot establish a substantive explanation.

Record findings against the initial hashes and versions. Preserve those findings when a repaired card passes. Repairs to a card or its reference bundle increment that card's version, retain the prior snapshot and require a recheck of the fixed sampled identity. Separate random findings from targeted findings; report inaccessible evidence rather than marking it verified. After two failed attempts per URL, use at most three alternatives or report the limitation.

Author review covers all submitted cards. Independent source inspection covers these 40 sampled cards and their relationships. Structural validation covers the complete candidate. These are different scopes of evidence; passing the sample does not certify every fact in all 200 cards or measure human interestingness. Actual platform token/cost usage is reported only when exposed.
