# Batch 007 post-audit repair

Revision 3 is ready for independent recheck of finding 007-R1. Only `local:catalog:issue-preclusion` changed, from card version 1 to 2. All 200 identities and coverage counts are unchanged.

Candidate: `candidate.revised.json`  
SHA-256: `a49d21157db18807479187fa76422fb119b40bc84febdf68d39c04b64114979e`

The 47-word card explicitly requires actual litigation and necessary determination in a valid final judgment. It qualifies who may be bound through a full and fair opportunity to litigate and preserves recognized nonparty exceptions. It does not impose an absolute same-parties requirement.

> In US litigation, issue preclusion can bar relitigation of an issue actually litigated and necessarily decided in a valid final judgment. It generally binds a party who had a full and fair opportunity to litigate, with recognized nonparty exceptions. The issue may recur within a different claim.

Two newly inspected references, Cornell's explicit issue-preclusion entry and the Supreme Court's Taylor v. Sturgell opinion II.A–B, supply the added limits. Their new IDs are `b007-s091` and `b007-s092`; all 90 previous source records remain exactly unchanged. The existing claim-preclusion comparison is unchanged and supported. The candidate now has 92 sources.

`post-audit-corrections.json` preserves the full before/after card, source bundles, author review and inspection records. The original `candidate.authored.json` revision 2 and all prior reports remain unchanged. The frozen initial independent findings remain at SHA-256 `560d4e1d81fa7b1f3199440f1bf46ba5da08f09eb5e0075f1c45cc01995171dd`.

`research/candidate_admission.py` and `research/revision_compare.py` both passed with zero failures against revision 2. The lineage check identifies exactly one changed card and no added or removed identities. The new source work stays within the original source bounds; even counting the existing claim-preclusion comparison source as an alternative, this subject has three references beyond its original collateral-estoppel source. New URL failures: zero.

Admission and lineage checks are structural/provenance checks. Independent recheck of the revised card and added support remains pending.
