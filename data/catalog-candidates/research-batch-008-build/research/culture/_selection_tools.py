"""Local assembly helpers for inspected selection metadata; no API calls."""
import datetime
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1]
BASELINE = json.loads((BASE / "baseline-index.json").read_text())["concepts"]
PAYLOAD = json.loads((HERE / "proposals.json").read_text())


def source(sid, title, url, locator, note, revision=None):
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    item = {
        "id": sid, "title": title, "url": url, "locator": locator,
        "revision": revision, "inspected_at": now, "inspection_mode": "web.open_text",
        "acquisition": {
            "local_inspection_completed_at": now, "remote_retrieval_timestamp": None,
            "time_basis": "Local clock after actual passage inspection; exact remote retrieval time unavailable",
        },
        "passage_notes": [note],
    }
    PAYLOAD["sources_inspected"].append(item)
    return item


def add(slug, label, aliases, domain, subfield, kind, scope, takeaway, src,
        parent=None, relation="broader_topic", assertion="source_asserted",
        parent_note=None, existing=None, near=None, limits=None,
        reason=None, role="primary", locator=None):
    cid = existing or "local:catalog:" + slug
    nearby = near if near is not None else (
        [existing] if existing else [parent] if parent in BASELINE else []
    )
    matches = []
    for match in nearby:
        if isinstance(match, tuple):
            mid, mreason = match
        else:
            mid = match
            mreason = "Same subject; canonical ID reused." if mid == existing else "Nearby broader meaning; source identifies a separately named subject or principle."
        matches.append({"id": mid, "label": BASELINE[mid]["label"], "reason": mreason})
    loc = locator or src["locator"]
    item = {
        "id": cid, "label": label, "aliases": aliases,
        "primary_domain": domain, "primary_subfield": subfield,
        "entity_kind": kind, "scope": scope, "learning_takeaway": takeaway,
        "inventory_status": "existing" if existing else "proposed_new",
        "nearest_baseline_matches": matches,
        "identity_reason": reason or (
            "The inspected meaning is the existing canonical subject; retain its identity."
            if existing else
            "The source names a distinct subject; focused baseline label, alias, and meaning checks found no identity for this subject."
        ),
        "discovery_evidence": [{"url": src["url"], "locator": loc,
                                "note": "Inspected passage names this subject and supports the stated takeaway.", "inspection_mode": src["inspection_mode"]}],
        "proposed_parent": {
            "target_id": parent, "type": relation, "assertion": assertion,
            "url": src["url"], "locator": loc,
            "note": parent_note or "The passage explicitly identifies this relationship.",
        } if parent else None,
        "limits": limits or [], "selection_role": role,
    }
    PAYLOAD["proposals"].append(item)
    return item


def save():
    (HERE / "proposals.json").write_text(json.dumps(PAYLOAD, ensure_ascii=False, indent=2) + "\n")
    (HERE / "sources-inspected.json").write_text(json.dumps(PAYLOAD["sources_inspected"], ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": PAYLOAD["status"], "proposals": len(PAYLOAD["proposals"]),
                      "sources": len(PAYLOAD["sources_inspected"])}, indent=2))
