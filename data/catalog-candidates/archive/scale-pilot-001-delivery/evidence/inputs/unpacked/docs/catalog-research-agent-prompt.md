# OtherWise catalog research — agent prompt

Work in `/Users/baorenliu/Documents/Programming/Python/ProductSpace`.

Research and write the first **200 verified catalog cards** for OtherWise. You own concept discovery, source research, identity reconciliation, card writing, and quality checking. Return the complete batch in a structured file in this workspace. This is an agent research task; local scripts may help manage files and validate the result. A per-concept AI API client is outside this task.

## Read the agreed requirements

Read applicable workspace instructions and `CONTEXT.md`. Read the **Concept identity and inventory**, **Catalog scope and discovery cards**, and **First catalog-build milestone** sections of `docs/superpowers/specs/2026-10-07-recommendation-system-design.md` before selecting entries. They define the agreed inclusion, identity, wording, and source rules.

Use `data/topics.json`, `data/discovery_graph.json`, and `data/recommendation-identities.json` as seed material. Consult `recommendation_lab/inventory.py` and `recommendation_lab/README.md` when resolving an existing canonical identity. Preserve registered identities, including local authored identities, instead of creating replacements for existing concepts.

The existing importers are bounded samples: some exclude people and other named subjects, remove broad overviews, deduplicate by title, or cap domains. Research according to the agreed requirements rather than inheriting those selection limits. Multiple distinct meanings can share a label.

## Select and research the batch

1. Record a selection manifest spanning the existing broad domains, all four scope classes, and practical as well as academic subjects. Include named subjects, multiword concepts, at least three ambiguous-name groups with multiple meanings, and concepts shared across fields. These cases exercise the catalog contract; the batch does not establish comprehensive coverage. Use public seed/source material rather than private preference ratings or held-out recommender judgments.
2. Research existing entries and additional ideas from references you can actually inspect. Start with relevant Wikidata identities, Wikipedia articles and sections, educational references, official technical documentation, or primary research as appropriate. An entry may have a stable local identity when no verified external identity exists.
3. Include an idea or named subject when its references support a distinct learning takeaway. For each proposed facet, establish what can be learned beyond its parent. Treat a question that merely rephrases an existing idea as another presentation of that identity. For example, “springback in sheet-metal bending” and “why bent metal springs back” would normally describe one idea; a separately documented compensation technique may be another.
4. Reconcile identities before drafting. Reuse verified source IDs; merge additional names for the same established identity; preserve separate identities for different meanings. Record uncertain equivalence cases for review. Name similarity and embedding proximity alone are insufficient evidence for a merge.
5. Write one **30–50-word English card** per accepted identity. Count words by whitespace-separated tokens, excluding the title and reference links. Explain the intended meaning and a concrete point worth exploring, with an example when useful. Broad subjects use everyday language; narrower ideas may use relevant domain terminology. Sources provide the next learning step, so an expanded lesson or a second technical/introductory version is unnecessary.
6. Check the card against its references. Cite the sources actually used for its substantive claims, including a section or other locator when available. A Wikidata identity link alone does not substantiate an explanation derived from another reference. Keep scope labels and editorial connections distinguishable from source assertions.

Cards and source notes must reflect evidence you inspected. If a source cannot be accessed or a claim remains unsupported, record the issue and use a supported alternative or leave the candidate unresolved. Bound repeated attempts; report a shortfall if a blocker prevents completing 200 verified cards.

## Write one catalog file

Write `data/catalog-candidates/research-batch-001.json`. Inspect that path first: resume a matching partial batch or choose the next unused batch number rather than replacing unrelated work. Keep the operational catalog and recommender files intact; this file is a candidate artifact for later integration.

The JSON object has these top-level fields:

- `schema_version`: `1`.
- `batch`: batch ID, target count, language, completion status, date, agent/model identity when available, and the selection manifest.
- `sources`: a shared reference list. Each reference has `id`, `title`, `url`, a section/locator when relevant, retrieval date, and revision when available. Use `null` for unavailable metadata.
- `concepts`: the accepted entries described below.
- `issues`: rejected or unresolved candidates, their reasons, and any supporting reference IDs.
- `validation`: counts and results of the checks below, coverage by domain and scope, ambiguous alias groups, and measured usage or clearly labeled unavailable/estimated usage.

Each concept contains:

| Field | Contents |
|---|---|
| `id` | Existing canonical ID where verified; otherwise a stable new local ID following the workspace convention |
| `label` | A clear name; multiword labels are valid |
| `aliases` | Verified alternate names; different identities can share an alias |
| `entity_kind` | `idea` or `named_subject` |
| `scope` | `broad_field`, `topic`, `idea`, or `facet_or_application`, describing the breadth of its learning takeaway |
| `domains` | One or more relevant fields; shared concepts retain one identity |
| `learning_takeaway` | A short statement explaining the entry's distinct learning value |
| `card` | The 30–50-word explanation |
| `original_description` | Preserved imported description when present; otherwise `null` |
| `identity_urls` | Verified external identity links when present |
| `evidence` | Reference IDs, supporting locators, and brief notes identifying which card claims they support |
| `relations` | Related identity IDs, relation type, evidence/reference IDs, and whether the connection is source-asserted or editorial |

Use relation types `broader_topic`, `facet_of`, `application_of`, or `related_to` only where justified. Targets must resolve to entries in the batch, verified existing inventory identities, or verified external identities. Scope is an editorial breadth classification; category-path depth does not prove scope, difficulty, or prerequisite knowledge. Different meanings retain their own explanations and evidence.

## Validate and finish

Write checkpoints as research progresses. If using subagents, assign non-overlapping research responsibilities where possible, share the identity/selection manifest, and reconcile their outputs into the single final file. Count distinct accepted identities after reconciliation rather than summing draft counts.

Before finishing, validate JSON structure, unique canonical IDs, reference and relation targets, card word counts, distinct meanings, and coverage of the selected cases. Review every accepted card for factual support and scope-appropriate wording. An independent checker can revisit claims against the source material; numerical checks alone do not establish correctness. Keep failures visible in `issues` and `validation`.

Stop at this 200-card checkpoint. Return the file link and a concise report of accepted/rejected/unresolved counts, coverage, identity decisions, remaining gaps, elapsed time, and platform-reported usage when available. Label estimates and unknown measurements honestly. If blocked, return a valid partial file with specific reasons. The next bulk-expansion milestone and budget will be chosen from this result; this batch is not a completeness claim or a human-participant study.
