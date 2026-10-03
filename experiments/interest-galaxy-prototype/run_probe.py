"""Throwaway Galaxy feasibility probe. Reads public catalog/model; no user data.

Run from the repository root: .venv/bin/python experiments/interest-galaxy-prototype/run_probe.py
Uses the exact existing catalog cache, and local model weights in offline mode.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / ".cache/galaxy-prototype-deps"))

import numpy as np
from scipy.linalg import orthogonal_procrustes
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components, shortest_path
from scipy.stats import spearmanr
from sklearn.decomposition import PCA
from sklearn.manifold import MDS, SpectralEmbedding, trustworthiness
from sklearn.metrics import pairwise_distances
from umap import UMAP

from explorer import MODEL_NAME, load_catalog, load_model, topic_texts

OUT = Path(__file__).parent
SEED = 42
HCI_SOURCE = "https://csed.acm.org/knowledge-areas-human-computer-interaction-hci-cs2013-version/"
HCI_TEXT = (
    "Human-computer interaction: an interdisciplinary field combining computer science, "
    "cognitive psychology, human behavior and design to study and improve how people "
    "interact with computer systems."
)
PAIRS = [
    {
        "id": "cs-psych", "label": "CS → 心理学", "start": "Computer science", "end": "psychology",
        "profiles": [
            "Computer science: the study of computation, algorithms, programming, software, computer systems, and how people use computing technology.",
            "Psychology: the study of human behavior and mental processes, including cognition, perception, attention, memory, emotion, and learning.",
        ],
        "query": "Computer science and psychology: studying human behavior and cognition in relation to computers and interactive technology.",
    },
    {
        "id": "music-math", "label": "音乐 → 数学", "start": "Music", "end": "Mathematics",
        "profiles": [
            "Music: the art and study of sound, melody, harmony, rhythm, composition and performance.",
            "Mathematics: the study of numbers, quantities, patterns, structures, geometry and logical reasoning.",
        ],
        "query": "Music and mathematics: studying numerical patterns, structures and relationships in sound, rhythm and harmony.",
    },
    {
        "id": "bio-engineering", "label": "生物 → 工程", "start": "Biology", "end": "Engineering",
        "profiles": [
            "Biology: the study of living organisms, cells, genetics, evolution and biological systems.",
            "Engineering: applying science and mathematics to design and build useful systems, materials, machines and technologies.",
        ],
        "query": "Biology and engineering: applying engineering methods to living organisms and biological systems, or learning design principles from nature.",
    },
    {
        "id": "cs-music", "label": "CS → 音乐", "start": "Computer science", "end": "Music",
        "profiles": [
            "Computer science: the study of computation, algorithms, programming, software, computer systems, and how people use computing technology.",
            "Music: the art and study of sound, melody, harmony, rhythm, composition and performance.",
        ],
        "query": "Computer science and music: using computation, algorithms and software to create, analyze or interact with musical sound.",
    },
]


def unit(x):
    return x / np.linalg.norm(x, axis=-1, keepdims=True)


def standardize(x):
    y = x - x.mean(axis=0)
    return y / np.sqrt(np.mean(np.sum(y * y, axis=1)))


def neighbor_ids(distance, k=10):
    d = distance.copy()
    np.fill_diagonal(d, np.inf)
    return np.argpartition(d, k - 1, axis=1)[:, :k]


def round_list(x):
    return np.asarray(x).round(5).tolist()


def main():
    topics = load_catalog()
    identity = json.dumps({"model": MODEL_NAME, "texts": topic_texts(topics)}, ensure_ascii=False, sort_keys=True).encode()
    catalog_hash = hashlib.sha256(identity).hexdigest()
    cache = ROOT / ".cache/embeddings" / f"{catalog_hash}.npy"
    vectors = unit(np.load(cache, allow_pickle=False).astype(np.float64))
    assert vectors.shape == (len(topics), 768)
    assert np.isfinite(vectors).all()
    lookup = {r["topic"].lower(): i for i, r in enumerate(topics)}
    domains = sorted({r["domain"] for r in topics})
    domain_ids = np.array([domains.index(r["domain"]) for r in topics])
    prototypes = unit(np.array([vectors[domain_ids == i].mean(axis=0) for i in range(len(domains))]))
    cosine = np.clip(vectors @ vectors.T, -1, 1)
    angular = np.arccos(cosine) / np.pi
    np.fill_diagonal(angular, 0)
    neighbors = neighbor_ids(angular, 15)
    rows = np.repeat(np.arange(len(topics)), 15)
    columns = neighbors.ravel()
    edge_dist = angular[rows, columns]
    sigma = np.maximum(edge_dist.reshape(-1, 15).max(axis=1), 1e-6)
    weights = np.exp(-((edge_dist / np.repeat(sigma, 15)) ** 2))
    adjacency = csr_matrix((weights, (rows, columns)), shape=cosine.shape)
    adjacency = adjacency.maximum(adjacency.T)
    n_components = connected_components(adjacency, directed=False, return_labels=False)
    pca_model = PCA(n_components=2, random_state=SEED)
    pca = standardize(pca_model.fit_transform(vectors))
    spectral = standardize(SpectralEmbedding(n_components=2, affinity="precomputed", random_state=SEED).fit_transform(adjacency))
    # The precomputed angular matrix reuses exactly the service's original metric.
    graph = standardize(UMAP(n_components=2, n_neighbors=30, min_dist=.15,
                             metric="precomputed", random_state=SEED, n_jobs=1).fit_transform(angular))

    # Semantic anchor positions are fitted from domain-prototype angular distances,
    # not assigned arbitrary compass directions by the author.
    anchor_dist = np.arccos(np.clip(prototypes @ prototypes.T, -1, 1)) / np.pi
    np.fill_diagonal(anchor_dist, 0)
    anchors = standardize(MDS(n_components=2, metric=True, dissimilarity="precomputed", n_init=1,
                              random_state=SEED, max_iter=500, eps=1e-7).fit_transform(anchor_dist))
    affinity = vectors @ prototypes.T
    top = np.argpartition(-affinity, 3, axis=1)[:, :3]
    probs = np.exp(18 * (np.take_along_axis(affinity, top, axis=1) - np.max(affinity, axis=1, keepdims=True)))
    probs /= probs.sum(axis=1, keepdims=True)
    anchor_target = standardize(np.sum(anchors[top] * probs[:, :, None], axis=1))
    graph = graph @ orthogonal_procrustes(graph, anchor_target)[0]
    spectral = spectral @ orthogonal_procrustes(spectral, anchor_target)[0]
    pca = pca @ orthogonal_procrustes(pca, anchor_target)[0]
    layouts = {"pca": pca, "spectral": spectral, "graph": graph}
    for strength in [.15, .35, .65, 1.0]:
        layouts[f"anchor-{strength:g}"] = standardize((1 - strength) * graph + strength * anchor_target)

    rng = np.random.default_rng(SEED)
    subset = np.sort(rng.choice(len(topics), 800, replace=False))
    pair_i = rng.integers(0, len(topics), 50000)
    pair_j = rng.integers(0, len(topics), 50000)
    non_self = pair_i != pair_j
    pair_i, pair_j = pair_i[non_self], pair_j[non_self]
    truth_neighbors = neighbor_ids(angular)
    metrics = {}
    for name, xy in layouts.items():
        projected_dist = pairwise_distances(xy)
        visual_neighbors = neighbor_ids(projected_dist)
        recall = np.mean([len(set(a) & set(b)) / 10 for a, b in zip(truth_neighbors, visual_neighbors)])
        metrics[name] = {
            "neighbor_recall_10": float(recall),
            "trustworthiness_800_k10": float(trustworthiness(vectors[subset], xy[subset], n_neighbors=10, metric="cosine")),
            "distance_spearman_50000": float(spearmanr(angular[pair_i, pair_j], projected_dist[pair_i, pair_j]).statistic),
        }
        print(name, json.dumps(metrics[name]), flush=True)

    model = load_model(device="cpu")
    texts = [text for p in PAIRS for text in [*p["profiles"], p["query"]]] + [HCI_TEXT]
    encoded = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    enriched = vectors.copy()
    hci_id = lookup["human-computer interaction"]
    enriched[hci_id] = encoded[-1]
    route_cost = csr_matrix((edge_dist, (rows, columns)), shape=angular.shape)
    route_cost = route_cost.maximum(route_cost.T)
    experiments = []
    for p_index, pair in enumerate(PAIRS):
        start, end = lookup[pair["start"].lower()], lookup[pair["end"].lower()]
        _, predecessors = shortest_path(route_cost, directed=False, indices=start, return_predecessors=True)
        naive_path = [end]
        while naive_path[-1] != start and predecessors[naive_path[-1]] >= 0:
            naive_path.append(int(predecessors[naive_path[-1]]))
        naive_path.reverse()
        variants = {}
        for variant in ["raw", "context", "enriched"]:
            W = enriched if variant == "enriched" else vectors
            if variant == "raw":
                a, b = vectors[start], vectors[end]
                query = unit(a + b)
            else:
                a, b, query = encoded[p_index * 3:p_index * 3 + 3]
            direction = b - a
            t = (W - a) @ direction / (direction @ direction)
            residual = W - a - t[:, None] * direction
            distance_to_axis = np.linalg.norm(residual, axis=1)
            # Local perpendicular coordinate is display-only; x is the selected
            # high-dimensional semantic direction. y has no named semantic meaning.
            local_neighbors = np.argsort(-(W @ query))[:100]
            residual_axis = PCA(n_components=1, random_state=SEED).fit(residual[local_neighbors]).components_[0]
            local_y = residual @ residual_axis
            similarity_a, similarity_b, query_similarity = W @ a, W @ b, W @ query
            score = query_similarity if variant == "raw" else (.45 * query_similarity + .35 * np.minimum(similarity_a, similarity_b) + .1 * (similarity_a + similarity_b))
            order = np.argsort(-score, kind="stable")
            ranks = np.empty(len(topics), dtype=int)
            ranks[order] = np.arange(1, len(topics) + 1)
            candidates = [int(i) for i in order if i not in {start, end} and .1 <= t[i] <= .9]
            # Two proposed waypoints, not a verified academic learning sequence.
            waypoints = []
            for slot in [.3, .7]:
                eligible = [i for i in candidates if i not in waypoints and abs(t[i] - slot) <= .22 and min(similarity_a[i], similarity_b[i]) >= .28]
                if eligible:
                    chosen = max(eligible, key=lambda i: score[i] - .45 * abs(t[i] - slot))
                    waypoints.append(chosen)
                else:
                    waypoints.append(None)
            shown = sorted(set(candidates[:60] + [start, end] + ([hci_id] if p_index == 0 else [])))
            points = []
            for i in shown:
                points.append({"id": i, "t": float(t[i]), "y": float(local_y[i]), "axis_distance": float(distance_to_axis[i]),
                               "a": float(similarity_a[i]), "b": float(similarity_b[i]), "q": float(query_similarity[i]),
                               "score": float(score[i]), "rank": int(ranks[i]), "enriched": bool(variant == "enriched" and i == hci_id)})
            path = [start] + [i for i in waypoints if i is not None] + [end]
            variants[variant] = {
                "points": points, "top": candidates[:12], "waypoints": waypoints,
                "path": path,
                "path_edge_cosines": [float(W[i] @ W[j]) for i, j in zip(path, path[1:])],
                "hci_rank_all_topics": int(ranks[hci_id]), "hci_t": float(t[hci_id]),
                "hci_similarities": [float(similarity_a[hci_id]), float(similarity_b[hci_id])],
                "anchor_profiles": [topic_texts(topics)[start], topic_texts(topics)[end]] if variant == "raw" else pair["profiles"],
                "query": "Normalized midpoint of the two original catalog embeddings" if variant == "raw" else pair["query"],
            }
        experiments.append({**pair, "start_id": start, "end_id": end, "naive_graph_path": naive_path,
                            "naive_graph_edge_cosines": [float(cosine[i, j]) for i, j in zip(naive_path, naive_path[1:])], "variants": variants})
        print(pair["label"], {v: [topics[i]["topic"] for i in variants[v]["path"]] for v in variants}, flush=True)

    summary = {
        "catalog_count": len(topics), "dimensions": vectors.shape[1], "model": MODEL_NAME,
        "catalog_embedding_sha256": catalog_hash, "seed": SEED, "graph_k": 15,
        "graph_components": int(n_components), "pca_variance_retained": float(pca_model.explained_variance_ratio_.sum()),
        "umap": {"n_neighbors": 30, "min_dist": .15, "metric": "precomputed angular distance", "n_jobs": 1},
        "metrics": metrics, "pairs": experiments, "hci_description_overlay": HCI_TEXT,
        "hci_source": HCI_SOURCE, "default_anchor_strength": .15,
        "limits": [
            "Exploratory known-case demonstration, not a held-out benchmark or proof of interdisciplinary relationships.",
            "Only the HCI topic description is enriched; the original catalog and recommendation engine are untouched.",
            "Contextual query texts and profiles are authored and fully exposed in the preview.",
            "Global layout always uses original embeddings; the HCI overlay changes local exploration only.",
            "Distances and semantic relationships are approximate in 2D; route waypoints are candidates, not verified learning prerequisites.",
            "PCA, spectral graph layout, UMAP and four UMAP/anchor blends are compared; parameters are exploratory.",
        ],
    }
    payload = {"summary": summary, "domains": domains,
               "topics": [{"id": i, "topic": r["topic"], "description": r["description"], "domain": int(domain_ids[i]),
                           "source": r.get("source_url", ""), "pca": round_list(pca[i]), "spectral": round_list(spectral[i]), "graph": round_list(graph[i]),
                           "anchor": round_list(anchor_target[i]), "neighbors": truth_neighbors[i].tolist()} for i, r in enumerate(topics)],
               "anchors": round_list(anchors)}
    (OUT / "results.json").write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")
    template = (OUT / "preview.template.html").read_text()
    embedded = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    (OUT / "preview.html").write_text(template.replace("__GALAXY_DATA__", embedded))
    (OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    assert all(np.isfinite(xy).all() for xy in layouts.values())
    assert np.allclose((vectors[start] - vectors[start]) @ (vectors[end] - vectors[start]), 0)
    print("Wrote", OUT / "preview.html", flush=True)


if __name__ == "__main__":
    main()
