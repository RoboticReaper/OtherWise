# Interest exploration notebook

Build a minimal, inspectable Python notebook for discovering meaningful topics beyond a user's current interests. The user selected a fixed catalog and notebook; a website can consume the same Python engine later. No web application or server is needed now.

## Representation

Use a fixed catalog of authored everyday interests plus Wikimedia-listed concepts with Wikidata descriptions. Cap broad domains at 160 entries and rotate through source subsections; retain source links and revision metadata. Embed title plus description with the local `sentence-transformers/all-mpnet-base-v2` model. Download the model on first use; subsequent inference runs locally without an API key. For an exact catalog-title input, use the same contextual text as that catalog entry; otherwise embed the user's phrase unchanged. Show this resolution in the notebook.

Normalize embeddings and measure angular distance `acos(cosine_similarity) / pi`. Define the current-interest region as the union of equal-radius neighborhoods around individual interest embeddings. This avoids averaging unrelated interests into one center. The radius is an explicit experimental assumption, not a learned user profile.

For candidate x, let d be its distance to the closest interest. Search the band `radius - overlap <= d <= radius + expansion`, clipped to [0, 1]. Positive `d - radius` measures distance outside the interest region; negative values mark familiar overlap (not an exact interior distance to the union boundary). Exclude input titles and near-identical embeddings. Never fill an empty band with candidates outside it.

Rank eligible candidates toward the middle of the outward band and use a modest pairwise diversity penalty to avoid redundant recommendations. Limit familiar-overlap topics to at most 20% of returned recommendations; fewer results are preferable to violating the band or overlap limit. Report actual topic labels, descriptions, nearest input interest, distance, boundary offset, and familiar/new classification. Contrast these results with an ordinary nearest-neighbor baseline. Add a bounded uniform score perturbation per candidate for small variations; a seed makes it repeatable, zero randomness disables it. Eligibility and overlap limits never depend on randomness.

## Notebook

Provide editable inputs and numeric controls, executable examples, an inspectable embedding table, a baseline comparison, an exact distance histogram with the selected band, a distance-sweep experiment, and an optional 2D PCA projection clearly marked as approximate. All selection occurs in the original embedding space. Keep the core engine independent of notebook widgets so a future website can reuse it.

## Verification and limits

Verify band edges, multiple disjoint interests, overlap fraction, duplicates, diverse selection, empty bands and invalid inputs using hand-constructed vectors. Execute the entire notebook with real model embeddings. A finite catalog and its domain grouping still limit and bias coverage; arbitrary phrases and ambiguous inputs may need refinement. Semantic novelty is a proxy for topic expansion, not proof of viewpoint diversity or reduced polarization.
