#!/usr/bin/env python3
"""Build public whole-catalog galaxy geometry outside UI and API request handling."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np

from explorer import load_catalog, topic_texts
from galaxy.preprocessing import MODEL_NAME, build_galaxy, unit_vectors


def original_embeddings(topics, directory: Path, *, encode_missing=False):
    # Identical to the recommendation service's original catalog embedding key.
    identity = hashlib.sha256(json.dumps({"model": MODEL_NAME, "texts": topic_texts(topics)},
        ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    path = directory / f"{identity}.npy"
    if path.exists():
        return np.load(path, allow_pickle=False), identity
    if not encode_missing:
        raise ValueError(f"Original catalog embeddings are missing at {path}. "
                         "Run with --encode-missing to encode the unchanged catalog using MPNet.")
    from explorer import load_model
    model = load_model(device="cpu")
    values = unit_vectors(model.encode(topic_texts(topics), convert_to_numpy=True,
        normalize_embeddings=True, show_progress_bar=True))
    if values.shape != (len(topics), 768):
        raise ValueError("MPNet must provide one 768-dimensional vector per original topic.")
    directory.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=directory, suffix=".npy", delete=False) as stream:
            temporary = Path(stream.name)
            np.save(stream, values, allow_pickle=False)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return values, identity


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=ROOT / "data/topics.json")
    parser.add_argument("--embeddings-dir", type=Path, default=ROOT / ".cache/embeddings")
    parser.add_argument("--cache-dir", type=Path, default=ROOT / ".cache/galaxy")
    parser.add_argument("--output", type=Path, default=ROOT / "data/galaxy-layout.json")
    parser.add_argument("--encode-missing", action="store_true",
        help="Encode original catalog texts using MPNet if their embedding cache is absent.")
    args = parser.parse_args(argv)
    try:
        topics = load_catalog(args.catalog)
        vectors, identity = original_embeddings(topics, args.embeddings_dir,
                                                encode_missing=args.encode_missing)
        result = build_galaxy(topics=topics, vectors=vectors, embedding_identity=identity,
                             cache_dir=args.cache_dir, output_path=args.output)
    except (ValueError, OSError, RuntimeError) as error:
        parser.exit(1, f"Galaxy build failed: {error}\n")
    print(json.dumps({"output": str(args.output), "cache_hit": result.cache_hit,
        "elapsed_seconds": round(result.elapsed_seconds, 3), "topics": len(topics),
        "dimensions": vectors.shape[1], "cache_key": result.asset["cache_key"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
