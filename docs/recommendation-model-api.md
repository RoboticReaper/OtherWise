# Selectable recommendation models

The backend exposes the study candidates through `POST /api/recommend`. Discover their exact configurations and runtime readiness with `GET /api/recommend/models`. Start the backend with `.venv/bin/python scripts/start_demo.py --local-only`; shared access uses the existing bearer-token setup. Legacy requests without `model` still use the original backend contract.

| Model ID | Role |
|---|---|
| `K-connection` | Frozen connection-oriented hybrid candidate |
| `K-literal` | Frozen literal-emphasis hybrid candidate |
| `V3` | Hybrid candidate with the original distance band |
| `V0` | Historical ranker with versioned serving guards |
| `semantic-nearest` | Canonical nearest-neighbor relevance baseline |
| `BM25` | Lexical baseline; no semantic fallback when nothing matches |
| `random` | Seeded eligible-topic sanity baseline |
| `history-recency` | History-aware expansion control without direction/velocity |
| `trajectory` | Same history pipeline with direction/velocity alignment |

The catalog also exposes implemented `V1`, `V2`, `V3-no-lexical`, `V3-no-graph`, `V3-no-ranking`, `V3-adaptive` and `V5-known` controls. V4b remains an external-provider adapter, outside the selectable study models.

Raw lab `V0`/`V1` retain the historical lookup and ranking behavior for frozen comparisons. Their model-selected API versions add shared ambiguity handling, explicit meaning choices and known/duplicate output exclusions around that ranker. The guard version appears in `execution.serving_guards` and changes `algorithm_id`; identify this guarded version separately from the raw historical comparator in a study. Guards can shorten a list without refilling or reordering it.

## Requests

```json
{
  "model": "trajectory",
  "interests": [
    {"phrase": "computer science", "date": "2026-09-01"},
    {"phrase": "numerical methods", "date": "2026-09-11"},
    {"phrase": "computational fluid dynamics", "date": "2026-09-21"},
    "soccer"
  ],
  "result_kind": "specific",
  "limit": 10,
  "exploration_fraction": 0.3,
  "seed": 42
}
```

`date` is optional **on each interest**. It means when the user confirmed interest, not when a suggestion was displayed or an article published. Accept `YYYY-MM-DD` (midnight UTC) or an ISO timestamp with a timezone, such as `2026-09-01T12:00:00Z`. Missing dates remain unknown; input-array order never substitutes for dates. Dated repeats of the same identity are valid observations and never produce duplicate static anchors or recommendations. Requests are limited to 40 interest observations and 100 results. `keywords` is an alias for `interests` in model-selected requests.

All models accept dates; static models ignore them after validation and identity deduplication. Plain-text interests continue to work:

```json
{"model": "K-connection", "interests": ["computers", "soccer", "engineering", "tennis"], "limit": 10}
```

`result_kind` is `specific` by default or `broad`. `mode` is `global` by default; `path` uses `focus_index` into the submitted interest list, or the approved `focus` phrase, defaulting to the last interest. Known exclusions still use the entire history. Standard band/diversity controls, `goal`, `seed`, inventory-ID feedback and graph-area exposures follow the lab request contract. Historical band models can legitimately return a short or empty list. Baselines and the history pair instead use the declared `.035 < angular distance <= .50` eligibility policy.

## Meanings and responses

The response includes `model`, algorithm/configuration identity, inventory/model versions, `resolutions`, recommendations with canonical `concept_id`, source records, shared descriptions and diagnostics. An ambiguous phrase returns `status: "clarification_needed"` and no recommendations. Resubmit its selected `concept_id` together with the returned `inventory_version`. A missing or stale revision for an explicit meaning returns HTTP 409. Invalid input returns a generic HTTP 422 without echoing the submitted content. Unready models return HTTP 503.

```json
{
  "model": "trajectory",
  "inventory_version": "<version returned by the backend>",
  "interests": [{"phrase": "Java", "concept_id": "<offered meaning ID>", "date": "2026-09-01"}]
}
```

Known feedback uses inventory identities, for example `"feedback": {"Q123": {"known": true}}`; only submit IDs present in the current inventory. This is distinct from legacy graph feedback on `/api/discover`.

## History controls and interpretation

Optional `history_config` defaults are:

```json
{"half_life_days": 60, "forecast_days": 14, "max_step": 0.12, "strand_distance": 0.25}
```

Bounds are respectively 1–3650 days, 0–365 days, 0–.20 angular distance and .05–.35 angular distance. The model works in the full, fixed embedding space. It partitions dated observations into separate semantic strands against previous-time centers, aggregates unique vectors at equal times, fits a recency-weighted tangent velocity and caps the forecast displacement. Repeated vectors keep their strand membership; repeating an unchanged snapshot cannot invent motion. Undated interests are static anchors. Three distinct times and fit score at least .5 are disclosed implementation heuristics. Sparse, stationary, inconsistent or effectively zero-weight history falls back to the matched recency-only policy; setting forecast or maximum step to zero also disables movement.

`execution.history` reports strand counts, active focus strands, fit scores, angular speed per day, forecast steps, direction availability and whether returned scores used velocity. Fit scores are uncalibrated heuristics. The history pair shares retrieval, exclusions, recency profiles, content features, feedback, diversity and a moderate-distance expansion feature weighted by `exploration_fraction`; trajectory adds only forecast alignment. This supports a controlled comparison. The expansion feature is an opportunity proxy, not measured adoption or breadth gain.

Serving retains no interest history or interest-vector cache between requests. It reuses public catalog/graph vectors and a read-only lexical index. Use the same inventory snapshot, controls and result kind when comparing systems. New models are executable and behavior-tested; their effect on retained interest expansion still requires the deferred longitudinal evaluation.
