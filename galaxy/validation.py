"""Standard-library validation shared by preprocessing and extension packaging."""
from __future__ import annotations

import hashlib
import json
import math


def json_digest(value) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def catalog_digest(catalog: list[dict]) -> str:
    """Hash every public catalog field, preserving the source row order."""
    return json_digest(catalog)


def _number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def validate_catalog(catalog: list[dict]) -> None:
    if not isinstance(catalog, list) or not catalog:
        raise ValueError("The catalog must be a nonempty list.")
    seen = set()
    for row in catalog:
        if not isinstance(row, dict) or any(
            not isinstance(row.get(key), str) or not row[key].strip()
            for key in ("topic", "domain", "description")
        ):
            raise ValueError("Every catalog topic needs a title, domain and description.")
        if row["topic"] in seen:
            raise ValueError("Catalog topic titles must be unique.")
        seen.add(row["topic"])


def validate_layout(payload: dict, catalog: list[dict]) -> None:
    """Raise ValueError for malformed, stale, or mismatched public geometry.

    Catalog topic titles are the identity authority. This does not run a layout,
    load a model, or infer semantic distance from coordinates.
    """
    validate_catalog(catalog)
    if not isinstance(payload, dict) or set(payload) != {"schema_version", "metadata", "cache_key", "domains", "topics"}:
        raise ValueError("Invalid galaxy asset fields.")
    if type(payload["schema_version"]) is not int or payload["schema_version"] != 1:
        raise ValueError("Unsupported galaxy schema version.")
    metadata = payload["metadata"]
    if not isinstance(metadata, dict) or metadata.get("catalog_sha256") != catalog_digest(catalog):
        raise ValueError("Galaxy catalog fingerprint does not match the catalog.")
    if payload["cache_key"] != json_digest(metadata):
        raise ValueError("Galaxy cache key does not match its metadata.")
    if not isinstance(metadata.get("model"), str) or not metadata["model"]:
        raise ValueError("Galaxy model identity is missing.")
    parameters = metadata.get("parameters")
    if not isinstance(parameters, dict) or type(parameters.get("neighbor_count")) is not int or parameters["neighbor_count"] < 1:
        raise ValueError("Galaxy neighbor count is invalid.")
    topic_ids = {row["topic"] for row in catalog}
    domain_ids = {row["domain"] for row in catalog}
    if metadata.get("topic_count") != len(topic_ids) or metadata.get("domain_count") != len(domain_ids) or metadata.get("dimensions") != 768:
        raise ValueError("Galaxy source dimensions or catalog counts are invalid.")
    for field, expected_ids, keys in (
        ("domains", domain_ids, {"id", "x", "y"}),
        ("topics", topic_ids, {"id", "x", "y", "neighbors"}),
    ):
        rows = payload[field]
        if not isinstance(rows, list) or len(rows) != len(expected_ids):
            raise ValueError(f"Galaxy {field} count does not match the catalog.")
        seen = set()
        for row in rows:
            if not isinstance(row, dict) or set(row) != keys:
                raise ValueError(f"Galaxy {field} record is malformed.")
            if not isinstance(row["id"], str) or row["id"] not in expected_ids or row["id"] in seen:
                raise ValueError(f"Galaxy {field} IDs do not match the catalog.")
            if not _number(row["x"]) or not _number(row["y"]):
                raise ValueError("Galaxy coordinates must be finite numbers.")
            seen.add(row["id"])
    count = min(parameters["neighbor_count"], len(topic_ids) - 1)
    for row in payload["topics"]:
        neighbors = row["neighbors"]
        if not isinstance(neighbors, list) or len(neighbors) != count:
            raise ValueError("Galaxy neighbor count does not match its parameters.")
        seen, previous = set(), None
        for neighbor in neighbors:
            if not isinstance(neighbor, dict) or set(neighbor) != {"id", "distance"}:
                raise ValueError("Galaxy neighbor record is malformed.")
            identity, distance = neighbor["id"], neighbor["distance"]
            if not isinstance(identity, str) or identity not in topic_ids or identity == row["id"] or identity in seen:
                raise ValueError("Galaxy neighbor IDs must reference unique other topics.")
            if not _number(distance) or not 0 <= distance <= 1:
                raise ValueError("Galaxy angular distances must be finite and in [0, 1].")
            order = (distance, identity)
            if previous is not None and order < previous:
                raise ValueError("Galaxy neighbors must be sorted by distance, then title.")
            previous = order
            seen.add(identity)
