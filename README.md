# OtherWise

Your world, a little wider. OtherWise connects an English Chrome side panel to a
local Python recommendation service. Browsing titles become candidate interests
on the device; only interests explicitly saved by the user reach the service.

## Run the extension demo

1. Install Python dependencies in `.venv`: `python -m pip install -r requirements.txt`.
2. Build the extension: `python scripts/build_extension.py`.
3. Start the backend and optional shared HTTPS demo using
   [the backend guide](docs/demo-backend.md).
4. In Chrome's Extensions page, enable Developer mode and **Load unpacked** →
   `dist/otherwise-extension`.
5. Open OtherWise. In Settings, save the service address and team access code
   from `.cache/demo/connection.json`. Add an interest, or review browsing topics,
   then choose **Find ideas**.

[Extension guide](docs/extension-guide.md) · [Architecture and privacy](docs/extension-architecture.md)

The installable ZIP is `dist/OtherWise-extension.zip`. Unzip it before loading it
in Chrome. No browser model or frontend dependency installation is required.
Python 3.11+ and Chrome 116+ are required; development tests use Node 22+.

Checks: `python -m pytest -q` and `npm test`. Browser regression checks are documented
in the extension guide. The original notebook and its catalog remain available below.

## Notebook exploration

A minimal notebook for discovering meaningful topics beyond your current interests.
It searches an editable catalog of **3,452 topics across 23 domains**, using a local
embedding model and an adjustable band around your existing interests.

## Open the demo

From this project directory:

```sh
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m notebook interest_explorer.ipynb
```

The existing `.venv` is configured. On another machine, create it first with
`python3 -m venv .venv` (Python 3.11+). You can also open the notebook in your IDE
and select this project's `.venv/bin/python` as its kernel.

Choose **Run All**, then edit the interest list and settings or use the notebook's
interactive controls. Saved example outputs let you inspect the demo immediately.
The first model load downloads public weights into `.cache/models`; inference runs
locally and requires no API key. After downloading, set `HF_HUB_OFFLINE=1` if you
want to run without any network requests.

## Controls

- **Interest radius:** how much nearby material counts as already familiar.
- **Expansion:** how far outside that boundary the search may reach.
- **Overlap:** how far the search may reach back inside the familiar region.
- **Diversity:** how strongly to discourage similar results within a list.
- **Randomness:** small variations among close choices; fix the seed to repeat a run.

Start with **radius 0.28, expansion 0.07, overlap 0.015, diversity 0.20, randomness 0.03**.
The notebook includes Close / Balanced / Broader presets, live candidate counts,
and a distance chart. See [the parameter guide](docs/parameter-guide.md) for
practical ranges and an explanation of how each setting changes results.

Recommendations favor the middle of the outward band and reduce repeated semantic
content. At most 20% of returned results can come from familiar overlap. A sparse
band returns fewer results; it never silently expands your chosen limits.

Distances use `acos(cosine similarity) / pi`. Each interest has its own neighborhood;
a topic is unfamiliar only if it is outside **all** those neighborhoods. Search runs
in the full embedding space, not in the notebook's approximate 2D projection.
The radius is an adjustable modeling assumption, not a measured boundary of a person.

## Files

- `interest_explorer.ipynb`: experiments, recommendations, baseline and plots.
- `explorer.py`: reusable embedding and search functions; a future website can call these.
- `data/topics.json`: editable topic titles, domains, descriptions and source metadata.
- `data/catalog_metadata.json`: catalog coverage, provenance and duplicate-removal details.
- `tests/test_explorer.py`: numerical tests independent of model downloads.

Run checks with `python -m pytest -q`.

The default catalog combines **718 authored everyday interests** with
**2,734 concepts from Wikidata**, selected using
[Wikimedia's curated cross-disciplinary list](https://meta.wikimedia.org/wiki/List_of_articles_every_Wikipedia_should_have/Expanded).
Each of 23 broad subjects has a **160-topic cap**, with rotation through
subtopics. [Wikidata descriptions are CC0](https://www.wikidata.org/wiki/Wikidata:Licensing).
The [catalog notes](data/README.md) explain provenance, coverage and refresh steps.
The prior OpenAlex catalog is preserved in `data/archives/topics_openalex.json`.
Count balance does not establish cultural neutrality or exhaustive coverage.

Embedding distance indicates semantic novelty; it does not establish usefulness,
viewpoint diversity or an effect on polarization. Ambiguous inputs work better as
specific phrases. Exact catalog titles use their descriptions for embedding;
unmatched input phrases are embedded as written.

Model: [all-mpnet-base-v2](https://huggingface.co/sentence-transformers/all-mpnet-base-v2)
(768 dimensions, Apache 2.0). Method background:
[Sentence Transformers semantic search](https://www.sbert.net/examples/sentence_transformer/applications/semantic-search/README.html).
