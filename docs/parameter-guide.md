# Tuning topic exploration

Start with radius **0.28**, expansion **0.07**, overlap **0.015**, diversity **0.20**,
and randomness **0.03**. These are exploratory defaults for the current MPNet
model and English catalog, not universally optimal or psychologically calibrated values.

| Parameter | Practical starting range | Meaning of a higher value |
|---|---|---|
| Radius | 0.22–0.32 | Calls more nearby material familiar; excludes more direct neighbors from new territory |
| Expansion | 0.03–0.10 | Allows farther topics and moves the ranking target outward |
| Overlap | 0–0.03 | Allows a deeper strip inside the familiar boundary |
| Diversity | 0.10–0.30 | Penalizes recommendations resembling ones already chosen |
| Randomness | 0.01–0.05 | Allows close-scoring candidates to exchange positions or enter the list |

## Picture the band

The input interest itself is distance zero. Radius 0.28 draws the familiar boundary
at 0.28. Overlap 0.015 admits the strip just inside it, starting at 0.265. Expansion
0.07 admits the strip outside it, ending at 0.35. Ranking favors the midpoint of
the outward portion, 0.315, then accounts for diversity and small random variation.

Thus the allowed band is **0.265–0.35**. A candidate close to any of several input
interests is treated as familiar. Raising radius moves the whole band away from
the inputs. Raising expansion widens the band and shifts the preferred distance.
A tiny expansion can still be far away if the radius is high.

Angular distance is `acos(cosine similarity) / pi`:

| Distance | Cosine similarity |
|---:|---:|
| 0.10 | 0.95 |
| 0.20 | 0.81 |
| 0.25 | 0.71 |
| 0.30 | 0.59 |
| 0.35 | 0.45 |
| 0.40 | 0.31 |
| 0.50 | 0.00 |

These are exact numerical correspondences rounded to two decimals. Descriptions
such as "related" or "unfamiliar" are not fixed mathematical thresholds.
The old radius 0.35 / expansion 0.10 favored distance 0.40, already a relatively
weak cosine match. That helped explain some loosely connected recommendations.

## Presets

| Preset | Radius | Expansion | Overlap | Diversity |
|---|---:|---:|---:|---:|
| Close | 0.24 | 0.05 | 0.015 | 0.15 |
| Balanced | 0.28 | 0.07 | 0.015 | 0.20 |
| Broader | 0.32 | 0.09 | 0.02 | 0.25 |

Use the notebook's live candidate counts and actual nearest-topic distances to
judge each input. If too few candidates exist, increase expansion in increments
of about 0.02, checking the words returned. If topics feel disconnected, decrease
radius or expansion. If the list repeats one theme, increase diversity gradually.

Overlap is **a distance, not a percentage**. At most 20% of the returned list may
come from familiar overlap; the engine can return fewer recommendations rather
than break this quota. Diversity is a ranking weight, not an extra search radius.
Neither domain coverage nor embedding distance guarantees viewpoint diversity.

## Random variation

For each search, every eligible candidate receives one score perturbation drawn
uniformly between `-randomness` and `+randomness`. At 0.03 the relative perturbation
between two candidates cannot exceed 0.06 score units. It affects ranking only;
distance eligibility and the overlap quota remain hard constraints.

`seed=42` makes the run repeatable with the same model, data and inputs.
`seed=None` gives each run a fresh draw. `randomness=0` switches variation off.
Close or sparse candidate pools may produce the same result across different seeds.

The notebook uses a fixed seed for saved examples, fresh draws in its interactive
panel by default, and no randomness in the expansion sweep to isolate that setting.

## Observed examples with this catalog

These runs use MPNet, the current 3,452-topic catalog, up to ten results, and
randomness zero to make the presets comparable. They illustrate behavior, not
an evaluation of recommendation quality. The complete seven-interest check is
in `parameter-calibration.json`.

| Interest | Close | Balanced | Broader |
|---|---|---|---|
| gardening | 5 results: Balcony gardening, Botany | 10 results: Ethnobotany, Terrariums | 10 results: Biology, Agroforestry |
| Python programming | 0 results | 10 results: Data science, C++ programming | 10 results: Natural language processing, Statistics |
| rock climbing | 0 results | 7 results: Trail running, Snowboarding | 10 results: Parkour, Rock (geology) |
