"""Bounded public-only UMAP jobs, independent of recommendation compute capacity."""
from __future__ import annotations

from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
import hashlib
from importlib.util import find_spec
import json
import math
import os
from pathlib import Path
import tempfile
import threading

import numpy as np

from explorer import ROOT, topic_texts
from galaxy.preprocessing import (
    ALGORITHM_VERSION, DEFAULT_PARAMETERS, atomic_json_write, domain_label_positions,
    exact_angular_neighbors, numerical_versions, project_layout, unit_vectors,
)
from galaxy.validation import json_digest
from .engine import FocusIdentityConflict


class LayoutBusy(RuntimeError):
    """One distinct public projection is already running."""


class LayoutUnavailable(RuntimeError):
    """The verified public source or optional numerical dependencies are unavailable."""


def require_layout_dependencies():
    # Importing UMAP/Numba can take seconds on a cold process. Keep startup
    # validation cheap and let the single job worker import numerical libraries.
    if any(find_spec(name) is None for name in ('numpy', 'scipy', 'sklearn', 'umap', 'numba', 'pynndescent')):
        raise LayoutUnavailable('Install requirements-layout.txt and restart the backend to generate Galaxy layouts.')


def validate_parameters(parameters):
    limits = {'n_neighbors': (5, 60), 'min_dist': (0, 1),
              'spread': (.5, 3), 'repulsion_strength': (.5, 4)}
    if not isinstance(parameters, dict) or set(parameters) != set(limits):
        raise ValueError('Invalid Galaxy layout parameters.')
    for key, (low, high) in limits.items():
        value = parameters[key]
        if (type(value) not in {int, float} or not math.isfinite(value)
                or not low <= value <= high or (key == 'n_neighbors' and type(value) is not int)):
            raise ValueError('Invalid Galaxy layout parameters.')
    if parameters['min_dist'] > parameters['spread']:
        raise ValueError('Galaxy minimum distance must not exceed spread.')
    return dict(parameters)


def embedding_identity(values):
    raw = np.asarray(values)
    return dict(sha256=hashlib.sha256(np.ascontiguousarray(raw).tobytes()).hexdigest(),
                dtype=str(raw.dtype), shape=list(raw.shape))


class GalaxyLayoutService:
    def __init__(self, engine, *, cache_dir=None, max_results=8):
        if type(max_results) is not int or max_results < 1:
            raise ValueError('Layout cache limit must be a positive integer.')
        self.engine = engine
        self.cache_dir = Path(cache_dir) if cache_dir is not None else ROOT / '.cache/galaxy-layout'
        self.max_results = max_results
        self._lock = threading.RLock()
        self._jobs = OrderedDict()
        self._live_key = None
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='otherwise-galaxy')
        self._closed = False
        self._source = None
        self._source_identity = None
        self._knn = None

    def close(self):
        with self._lock:
            self._closed = True
        self._executor.shutdown(wait=True, cancel_futures=True)

    def source_vectors(self):
        identity = self.engine.focus_identity()
        if self._source is not None and self._source_identity == identity:
            return self._source
        semantic_key = hashlib.sha256(json.dumps({'model': identity['model'],
            'texts': topic_texts(self.engine.topics)}, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        path = Path(self.engine.cache_dir) / f'{semantic_key}.npy'
        if path.exists():
            try:
                raw = np.load(path, allow_pickle=False)
                if embedding_identity(raw) != identity['embedding']:
                    raise ValueError('Embedding source mismatch.')
            except (OSError, ValueError, EOFError) as error:
                raise LayoutUnavailable('Original catalog embeddings failed verification. Rebuild the public embedding cache.') from error
        else:
            # Engines injected with already normalized vectors have no disk cache.
            # Production initialization always writes the original public .npy first.
            raw = np.asarray(self.engine.topic_vectors)
            if (list(raw.shape) != identity['embedding']['shape']
                    or str(raw.dtype) != identity['embedding']['dtype']
                    or not np.allclose(np.linalg.norm(raw, axis=1), 1., rtol=0, atol=1e-12)):
                raise LayoutUnavailable('Original catalog embeddings are unavailable. Rebuild the public embedding cache.')
        unit_vectors(raw)  # Validate finiteness/nonzero vectors before accepting source.
        self._source, self._source_identity, self._knn = raw, identity, None
        return raw

    def start(self, payload):
        parameters = validate_parameters(payload['parameters'])
        source_identity = self.engine.focus_identity()
        supplied = {key: payload[key] for key in ('catalog_sha256', 'model', 'embedding')}
        if supplied != source_identity:
            raise FocusIdentityConflict('Catalog source version conflict.')
        metadata = dict(source_identity, parameters=parameters,
                        algorithm_version=ALGORITHM_VERSION, numerical_versions=numerical_versions())
        key = json_digest(metadata)
        with self._lock:
            if self._closed:
                raise LayoutUnavailable('Galaxy layout service is unavailable.')
            if key in self._jobs:
                job = self._jobs[key]
                if job['status'] != 'failed':
                    self._jobs.move_to_end(key)
                    return self._snapshot(job)
                # A transient failure can retry the same deterministic key.
                # Keep the failed snapshot until capacity/dependencies pass;
                # another live projection still owns the single worker.
            cached = self._load_result(key, source_identity, parameters)
            if cached is not None:
                job = dict(job_id=key, status='ready', stage='ready', result=cached)
                self._jobs[key] = job
                self._trim_jobs()
                return self._snapshot(job)
            if self._live_key is not None:
                raise LayoutBusy('A Galaxy layout is already generating. Try again after it finishes.')
            require_layout_dependencies()
            if len(self.engine.topics) < 3:
                raise LayoutUnavailable('Galaxy layout needs at least three public catalog topics.')
            job = dict(job_id=key, status='queued', stage='queued')
            self._jobs[key] = job
            self._live_key = key
            self._trim_jobs()
            self._executor.submit(self._compute, key, source_identity, parameters)
            return self._snapshot(job)

    def status(self, job_id):
        with self._lock:
            if job_id not in self._jobs:
                raise KeyError(job_id)
            return self._snapshot(self._jobs[job_id])

    @staticmethod
    def _snapshot(job):
        return dict(job)

    def _stage(self, key, stage):
        with self._lock:
            self._jobs[key].update(status='running', stage=stage)

    def _compute(self, key, source_identity, parameters):
        try:
            self._stage(key, 'verifying_source')
            raw = self.source_vectors()
            self._stage(key, 'exact_neighbors')
            neighbors = self._exact_neighbors(raw, source_identity)
            self._stage(key, 'projecting')
            options = dict(DEFAULT_PARAMETERS, **parameters)
            positions, _ = project_layout(self.engine.topics, unit_vectors(raw), neighbors, options)
            self._stage(key, 'placing_labels')
            labels = domain_label_positions(self.engine.topics, positions,
                                           neighbors=options['domain_label_neighbors'])
            domains = sorted({row['domain'] for row in self.engine.topics})
            result = dict(schema_version=1, cache_key=key, **source_identity,
                parameters=parameters,
                topics=[dict(id=row['topic'], x=float(positions[i, 0]), y=float(positions[i, 1]))
                        for i, row in enumerate(self.engine.topics)],
                domains=[dict(id=name, x=float(labels[i, 0]), y=float(labels[i, 1]))
                         for i, name in enumerate(domains)])
            self._validate_result(result, key, source_identity, parameters)
            atomic_json_write(self.cache_dir / f'{key}.json', dict(result=result, sha256=json_digest(result)))
            self._trim_disk()
            terminal = dict(status='ready', stage='ready', result=result)
        except Exception:
            # Numerical errors never expose model credentials or arbitrary inputs.
            terminal = dict(status='failed', stage='failed',
                error='Galaxy layout generation failed. Try generating the preview again. If it keeps failing, verify requirements-layout.txt and the public embedding cache.')
        # Publish terminal status and release capacity together: an identical
        # retry must never race a previous worker's final capacity cleanup.
        with self._lock:
            self._jobs[key].update(**terminal)
            self._live_key = None
            self._trim_jobs()

    def _trim_jobs(self):
        while len(self._jobs) > self.max_results:
            terminal = next((key for key in self._jobs if key != self._live_key), None)
            if terminal is None:
                break
            del self._jobs[terminal]

    def _trim_disk(self):
        files = sorted(self.cache_dir.glob('*.json'), key=lambda path: path.stat().st_mtime_ns, reverse=True)
        for path in files[self.max_results:]:
            path.unlink(missing_ok=True)

    def _validate_result(self, result, key, identity, parameters):
        if (set(result) != {'schema_version', 'cache_key', 'catalog_sha256', 'model', 'embedding', 'parameters', 'topics', 'domains'}
                or result['schema_version'] != 1 or result['cache_key'] != key
                or result['parameters'] != parameters
                or any(result[field] != value for field, value in identity.items())):
            raise ValueError('Invalid layout result source.')
        for field, expected in [('topics', [r['topic'] for r in self.engine.topics]),
                                ('domains', sorted({r['domain'] for r in self.engine.topics}))]:
            rows = result[field]
            if not isinstance(rows, list) or [r['id'] for r in rows] != expected:
                raise ValueError('Invalid layout IDs.')
            for row in rows:
                if set(row) != {'id', 'x', 'y'} or any(type(row[axis]) not in {int, float}
                        or not math.isfinite(row[axis]) for axis in ('x', 'y')):
                    raise ValueError('Invalid layout coordinates.')

    def _load_result(self, key, identity, parameters):
        path = self.cache_dir / f'{key}.json'
        try:
            envelope = json.loads(path.read_text())
            result = envelope['result']
            if envelope['sha256'] != json_digest(result):
                raise ValueError('Layout checksum mismatch.')
            self._validate_result(result, key, identity, parameters)
            path.touch()
            return result
        except (OSError, ValueError, TypeError, KeyError, OverflowError):
            return None

    def _exact_neighbors(self, raw, identity):
        if self._knn is not None:
            return self._knn
        metadata = dict(identity, k=min(59, len(raw) - 1),
                        metric='acos(clipped_cosine)/pi-float64-title-ties-v1')
        key = json_digest(metadata)
        folder = self.cache_dir / 'neighbors'
        path = folder / f'{key}.npz'
        try:
            with np.load(path, allow_pickle=False) as cached:
                indices, distances = cached['indices'], cached['distances']
                header = json.loads(str(cached['metadata']))
                digest = hashlib.sha256(indices.tobytes() + distances.tobytes()).hexdigest()
                if header != metadata or str(cached['sha256']) != digest:
                    raise ValueError('Exact neighbor checksum mismatch.')
            size, count = len(raw), metadata['k']
            if (indices.shape != (size, count) or distances.shape != (size, count)
                    or indices.dtype != np.int32 or distances.dtype != np.float64
                    or np.any(indices < 0) or np.any(indices >= size)
                    or np.any(indices == np.arange(size)[:, None])
                    or not np.isfinite(distances).all() or np.any(distances < 0)
                    or np.any(distances > 1) or np.any(np.diff(distances, axis=1) < 0)):
                raise ValueError('Invalid exact neighbor cache.')
        except (OSError, ValueError, TypeError, KeyError, EOFError):
            indices, distances = exact_angular_neighbors(raw,
                [row['topic'] for row in self.engine.topics], k=59,
                block_size=DEFAULT_PARAMETERS['distance_block_size'])
            folder.mkdir(parents=True, exist_ok=True)
            temporary = None
            try:
                with tempfile.NamedTemporaryFile(dir=folder, suffix='.npz', delete=False) as stream:
                    temporary = Path(stream.name)
                    np.savez_compressed(stream, indices=indices, distances=distances,
                        metadata=json.dumps(metadata, sort_keys=True),
                        sha256=hashlib.sha256(indices.tobytes() + distances.tobytes()).hexdigest())
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temporary, path)
            finally:
                if temporary is not None:
                    temporary.unlink(missing_ok=True)
            # Public source caches are bounded separately from the parameter results.
            old = sorted(folder.glob('*.npz'), key=lambda entry: entry.stat().st_mtime_ns, reverse=True)
            for entry in old[2:]:
                entry.unlink(missing_ok=True)
        self._knn = indices, distances
        return self._knn
