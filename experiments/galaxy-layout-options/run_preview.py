"""Throwaway A/B/C Galaxy layout comparison using every original public vector.

Run: .venv/bin/python experiments/galaxy-layout-options/run_preview.py
Question: can looser UMAP / local islands / explicit domains make 31k stars usable?
Does not write production assets, settings, or recommendations.
"""
from pathlib import Path
import hashlib
import json
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / '.cache/galaxy-prototype-deps'))

import numpy as np
from scipy.sparse import csr_matrix
from scipy.spatial import cKDTree
from sklearn.manifold import MDS
from umap import UMAP
from galaxy.preprocessing import (unit_vectors, exact_angular_neighbors, standardize,
    anchor_targets, blend_layout, domain_label_positions, numerical_versions)
from galaxy.validation import catalog_digest

OUT = Path(__file__).parent
CACHE = ROOT / '.cache/galaxy-options'
CONFIGS = {
    'A': dict(n_neighbors=60, min_dist=.70, spread=1., repulsion_strength=2., anchor_strength=.05),
    'B': dict(n_neighbors=12, min_dist=.40, spread=1.5, repulsion_strength=2.5, anchor_strength=0.),
}


def split_regions(items, bounds, result):
    """A proportional domain atlas, deliberately distinct from semantic geography."""
    x, y, width, height = bounds
    if len(items) == 1:
        result[items[0][0]] = [x, y, width, height]
        return
    total = sum(size for _, size in items)
    sums = np.cumsum([size for _, size in items])
    cut = int(np.argmin(abs(sums[:-1] - total / 2))) + 1
    fraction = sums[cut - 1] / total
    if width >= height:
        split_regions(items[:cut], [x, y, width * fraction, height], result)
        split_regions(items[cut:], [x + width * fraction, y, width * (1 - fraction), height], result)
    else:
        split_regions(items[:cut], [x, y, width, height * fraction], result)
        split_regions(items[cut:], [x, y + height * fraction, width, height * (1 - fraction)], result)


def domain_atlas(topics, base, domains):
    groups = {d: np.array([i for i, t in enumerate(topics) if t['domain'] == d]) for d in domains}
    boxes = {}
    split_regions(sorted(((d, len(ids)) for d, ids in groups.items()), key=lambda v: (-v[1], v[0])),
                  [-1.5, -1., 3., 2.], boxes)
    result = np.zeros_like(base)
    rng = np.random.default_rng(42)
    for domain, ids in groups.items():
        x, y, width, height = boxes[domain]
        # Same-domain UMAP ordering guides rows; unique grid slots prevent pileups.
        columns = max(1, int(np.ceil(np.sqrt(len(ids) * width / height))))
        ordered = ids[np.argsort(base[ids, 1], kind='stable')]
        row_count = int(np.ceil(len(ids) / columns))
        for row in range(row_count):
            members = ordered[row * columns:(row + 1) * columns]
            members = members[np.argsort(base[members, 0], kind='stable')]
            for column, index in enumerate(members):
                result[index] = [x + width * (.05 + .90 * (column + .5) / columns),
                                 y + height * (.08 + .84 * (row + .5) / row_count)]
                result[index] += rng.uniform(-.1, .1, 2) * [width / columns, height / row_count]
    return result, boxes


def measure(points, truth):
    _, visual = cKDTree(points).query(points, k=11)
    retained = np.mean([len(set(row[1:]) & set(truth[i, :10])) / 10 for i, row in enumerate(visual)])
    span = np.ptp(points, axis=0)
    scale = min(1100 / span[0], 720 / span[1]) * .82
    distances, _ = cKDTree(points).query(points, k=2)
    return dict(neighbor_retention=round(float(retained) * 100, 1),
                overlap_at_08px=round(float(np.mean(distances[:, 1] * scale < 1.6)) * 100, 1))


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    topics = json.loads((ROOT / 'data/topics.json').read_text())
    production = json.loads((ROOT / 'data/galaxy-layout.json').read_text())
    metadata = production['metadata']
    assert catalog_digest(topics) == metadata['catalog_sha256']
    assert all(t['topic'] == p['id'] for t, p in zip(topics, production['topics'], strict=True))
    raw = np.load(ROOT / '.cache/embeddings' / (metadata['embedding']['identity'] + '.npy'))
    assert hashlib.sha256(np.ascontiguousarray(raw).tobytes()).hexdigest() == metadata['embedding']['sha256']
    units = unit_vectors(raw)
    ids = [t['topic'] for t in topics]
    domains = sorted({t['domain'] for t in topics})
    assignments = np.array([domains.index(t['domain']) for t in topics])
    original = np.array([[t['x'], t['y']] for t in production['topics']])
    knn_path = CACHE / (metadata['embedding']['sha256'] + '-k59.npz')
    if knn_path.exists():
        with np.load(knn_path) as cache:
            indices, distances = cache['indices'], cache['distances']
    else:
        print('Computing exact original-vector neighborhoods for all topics.', flush=True)
        indices, distances = exact_angular_neighbors(raw, ids, k=59)
        np.savez_compressed(knn_path, indices=indices, distances=distances)
    prototypes = unit_vectors(np.array([units[assignments == i].mean(axis=0) for i in range(len(domains))]))
    angular = np.arccos(np.clip(prototypes @ prototypes.T, -1, 1)) / np.pi
    np.fill_diagonal(angular, 0)
    anchors = standardize(MDS(n_components=2, metric=True, dissimilarity='precomputed',
        random_state=42, n_init=1, max_iter=500, eps=1e-7).fit_transform(angular))
    target = standardize(anchor_targets(units @ prototypes.T, anchors))
    layouts = {'current': original}
    configurations = {'current': dict(n_neighbors=30, min_dist=.15, spread=1., repulsion_strength=1., anchor_strength=.15)}
    for key, config in CONFIGS.items():
        identity = json.dumps([metadata['embedding']['sha256'], config, numerical_versions()], sort_keys=True)
        path = CACHE / (hashlib.sha256(identity.encode()).hexdigest() + '.npy')
        if path.exists():
            points = np.load(path)
        else:
            start = time.monotonic()
            k = config['n_neighbors'] - 1
            chosen, values = indices[:, :k], distances[:, :k]
            sparse = csr_matrix((values.ravel(), chosen.ravel(), np.arange(0, (len(topics) + 1) * k, k)), shape=(len(topics), len(topics)))
            sparse = sparse.maximum(sparse.T)
            knn = (np.column_stack((np.arange(len(topics)), chosen)), np.column_stack((np.zeros(len(topics)), values)), None)
            options = {name: value for name, value in config.items() if name != 'anchor_strength'}
            print(f'Projecting {key}: {config}', flush=True)
            graph = UMAP(**options, n_components=2, metric='precomputed', precomputed_knn=knn,
                         init='random', random_state=42, n_jobs=1, n_epochs=300).fit_transform(sparse)
            points = blend_layout(graph, target, strength=config['anchor_strength'])
            np.save(path, points)
            print(f'{key} ready in {time.monotonic()-start:.1f}s', flush=True)
        layouts[key], configurations[key] = points, config
    layouts['C'], boxes = domain_atlas(topics, layouts['A'], domains)
    configurations['C'] = dict(base='A', display='proportional domain regions + unique slots guided by local UMAP order')
    summary = {key: dict(parameters=configurations[key], metrics=measure(points, indices)) for key, points in layouts.items()}
    labels = {key: domain_label_positions(topics, points).round(6).tolist() for key, points in layouts.items()}
    lookup = {title: i for i, title in enumerate(ids)}
    data = dict(topic_count=len(topics), domains=domains, summary=summary, regions=boxes,
        topics=[[t['topic'], domains.index(t['domain']), t['description']] for t in topics],
        neighbors=[[[lookup[n['id']], round(n['distance'], 6)] for n in t['neighbors']] for t in production['topics']],
        layouts={key: points.round(6).tolist() for key, points in layouts.items()}, labels=labels,
        provenance=dict(catalog_sha256=metadata['catalog_sha256'], original_vectors=metadata['embedding'],
                        seed=42, numerical_versions=numerical_versions(), purpose='Throwaway read-only design preview'))
    encoded = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c')
    (OUT / 'preview.html').write_text((OUT / 'preview.template.html').read_text().replace('__PREVIEW_DATA__', encoded))
    (OUT / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
    print('Open experiments/galaxy-layout-options/preview.html; all layouts use all public topics.', flush=True)


if __name__ == '__main__': main()
