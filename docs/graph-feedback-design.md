# Specific discovery and feedback

The approved extension adds concrete discovery items and explicit local feedback to the existing notebook. MPNet and the user's edited interests/settings stay in place. Wikipedia category membership supplies source-backed paths; Wikidata supplies identifiers and descriptions. This is a finite, documented snapshot with a refresh script, not a complete curriculum.

## Catalog balance

Use all 23 domains from the broad catalog, with three navigation areas and 160
eligible concepts per domain. Select across areas round-robin; reserve two reviewed
examples at each of three levels. All domains share the same traversal policy:
one category level initially, one extra level only if the domain is underfilled.
Reject authored per-seed depth exceptions. Retain only verified source paths and
enforce area catalog selections during traversal so shared categories do not
bypass quotas. Show actual candidate counts in the notebook and fail refreshes
with coverage gaps unless an explicitly partial import is requested. Equal
catalog coverage does not require equal topic proportions in personalized lists.

## Flow

Use semantic matching to shortlist graph areas from the current broad recommendations and interest anchors. Area selection routes retrieval; it does not certify novelty. Follow bounded category paths to concept nodes, deduplicate multi-parent concepts, and recheck every final concept against the original interest vectors and hard angular band. Display the graph path and source. Broad category nodes never become final cards.

Rank with band fit, curiosity, difficulty fit, and pairwise diversity plus bounded random jitter. Do not infer difficulty from graph depth. Only reviewed level annotations influence difficulty matching; other concepts display an unknown level. Familiar-overlap quota remains <=20% of actual results. Reserve a user-selected fraction (default 30%) for the least-exposed eligible areas, subject to distance, known-concept exclusions, and available coverage. This is an observable quota, not a claim of viewpoint diversity.

## Feedback

Persist local profile in `.local/feedback.json`, excluded from Git. Each concept independently stores curious, known, and difficulty feedback (none/too basic/too hard), with the presentation level and area context. Latest feedback replaces that concept's prior rating; repeated saves are not repeated votes. Known concepts are excluded; curiosity does not imply familiarity. Difficulty preferences affect only the rated graph branches; they never change radius or interest seeds. Small curiosity transfer applies only to candidates sharing an area. Areas with contradictory feedback average the directional evidence; unreviewed item levels cannot imply numeric competence. Exposure counts update when interactive results are shown. Provide clear/undo feedback and profile inspection.

## Notebook

Add a self-contained graph discovery section using the existing model, inputs and settings. Show snapshot coverage, source paths, specific recommendations, score explanations, level labels, independent feedback controls, and an exploration-share slider. Saving feedback reranks immediately. Demo comparisons use an in-memory profile and do not write fake user feedback to disk. Existing user inputs and prior notebook experiments remain available.

## Verification

Synthetic vectors and graph fixtures exercise cycle-safe traversal, known suppression, independent feedback axes, local difficulty updates, persistence/replacement, exploration quota, random seed reproducibility and hard band/overlap limits. Execute notebook with real model, inspect CS and current mixed-interest outputs, exercise actual UI callbacks with temporary profiles, and inspect a before/after feedback example.
