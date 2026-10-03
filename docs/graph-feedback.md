# Specific discovery and explicit feedback

Open section **10. Specific ideas and feedback** in `interest_explorer.ipynb`.
The earlier sections inspect broad recommendations. The new section uses a
Wikipedia category graph to retrieve concrete concepts and shows their source
paths. The graph snapshot is separate from the original topic catalog.

Both catalogs use the same 23 broad domains. The graph gives each domain 160
eligible concepts across three navigation areas and a reviewed sample of two
entries at each reading level. Area selections are enforced during traversal,
so shared graph branches cannot bypass the domain budget. Coverage is visible
in the notebook and protected by snapshot regression tests. Equal catalog
coverage does not force equal domain counts in each personalized result list.

## Running it

Run the notebook with the existing project environment. It encodes the graph's
concepts and areas with the same MPNet model. The static examples use empty,
in-memory profiles. Click **Explore specific ideas** in the new panel to use
saved personal feedback. The panel starts with the user's notebook interests and
settings; its controls apply to the next Explore click.

The fixed graph runs offline once model weights are downloaded. Refreshing the
public graph is a separate action documented in `data/discovery_graph_README.md`.

## What happens during search

1. Ordinary broad exploration and the user's original interests route retrieval
   to eight related graph areas using MPNet. This is approximate semantic routing,
   not an assertion that a broad recommendation has an actual graph edge to an area.
2. Bounded breadth-first traversal follows observed category memberships, allowing
   multiple paths to a concept, and deduplicates concepts by ID. Paths explain
   provenance, not prerequisites or teaching order.
3. Actual concept vectors are measured against the original interests. Only
   concepts inside `[radius - overlap, radius + expansion]` (clipped to [0,1])
   can be selected. Exact input titles, near-identical vectors and concepts marked
   known are excluded. The familiar-overlap limit is <=20% of actual results.
4. The eligible concepts are ranked using outward-band fit, explicit curiosity,
   suitable reviewed difficulty, semantic and area variety, and bounded variation.

Area routing never certifies that its descendants are novel. Every final concept
gets its own distance check. Feedback never changes the interest seeds or radius.

## What feedback means

Curiosity, familiarity and challenge preference are independent. A user can be
curious about a concept and find it too hard. The profile stores one latest rating
per concept, its shown area, entry-point level and update time. Repeated saves
replace the previous rating instead of acting as extra votes.

- Curious boosts the concept and modestly favors its shown graph area.
- Already know excludes only the concept ID, including alternate graph paths.
  It does not imply knowing or liking the parent subject.
- Too basic asks for greater depth in the shown area. Too hard asks for a more
  accessible entry point. Reviewed levels are 1 (accessible), 2 (some background),
  and 3 (technical). Feedback asks for a one-level shift, bounded to 1–3. Feedback
  on an unrated entry requests the accessible/technical end of this scale without
  estimating the user's competence. Multiple local ratings average their requested
  levels. Unreviewed candidate levels remain neutral in difficulty scoring.
- The exact entry point rated too basic/hard gets a small ranking penalty to favor
  alternatives. This does not cancel a positive curiosity signal for the area.

**The graph contains no inferred prerequisite edges.** A greater graph depth is
not assumed harder. Level labels and hooks are explicitly authored annotations;
source facts and memberships retain their own provenance.

## How scores are combined

These are transparent demo heuristics, not learned probabilities or validated
measures of personal interest:

- Band fit: `(1 - diversity) * fit`, where fit peaks at the outward midpoint.
- Curiosity: +0.30 for the exact concept; up to +0.18 for its shown area, increasing
  over three distinct curious concept ratings.
- Difficulty: `0.25 * (1 - abs(reviewed_level - preferred_level))`; zero if either
  side is unknown.
- Previously mismatched entry point: -0.35 for its latest too-basic/too-hard rating.
- Redundancy: subtract `diversity * maximum_positive_cosine_with_selected`.
- Area repetition: subtract 0.12 per already selected concept from that source area.
- Variation: one uniform perturbation in `[-randomness, +randomness]` per candidate.

The score components are returned in each result's `score_parts` for inspection.

## Preventing feedback from narrowing every result

The exploration slider reserves `ceil(share * actual_result_count)` selections
from the least-shown areas among the eligible candidate pool. The default is 30%,
an experimental starting choice. Exposure counts record cards shown on Explore
clicks, by their selected source area. Unknown/unseen is not assumed disliked.

Reservations still obey known exclusions, the final distance band and the overlap
quota. If there are too few eligible reserved candidates, the panel shows how many
places were filled. It never invents candidates or silently widens the band.
Initial areas all have equal exposure, so the quota becomes more meaningful after
several Explore clicks. Variety penalties also operate within each returned list.

## Local persistence and editing

The profile lives at `.local/feedback.json`; `.local/` is ignored by Git. It is not
sent to a server. Writes are atomic. A malformed profile produces an error rather
than silently discarding the user's ratings. Static examples use temporary,
in-memory profiles.

Saving a rating immediately reranks the last valid search with the same random
draw and exposure snapshot, making the feedback effect inspectable. Explore
records a new exposure and, when Repeatable is unchecked, uses a fresh seed.
**Undo last feedback** reverses the latest edit; the saved-feedback panel can clear
any rating, including a concept hidden because it is known. New notebook examples
do not write artificial feedback into the live profile.

## Reusable code

- `graph_explorer.py`: graph validation, traversal, area routing and final ranking.
- `feedback.py`: profile editing, preferences, exposure counts and persistence.
- `discovery_widgets.py`: notebook controls using those independent functions.

The existing `explorer.py` continues to supply embeddings and broad search. A future
website can call the same Python functions without running a notebook.
