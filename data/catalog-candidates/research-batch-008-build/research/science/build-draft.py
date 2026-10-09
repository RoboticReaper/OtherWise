"""Build only the approved science draft; never touches operational inputs."""
import copy
import hashlib
import importlib.util
import json
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUILD = HERE.parent.parent
REPO = BUILD.parents[2]
GLOBAL_SHA = "5e15d76acee1c29775a9b7b003f7d01447e494974da200c9c15afa3a25f5df9d"
BASELINE_SHA = "e3cd8ebac67579be75742df0bf2f5b2e7781293282345d2286aff205416e0fe2"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(name, data):
    (HERE / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def main():
    approved = read(HERE / "approved-selection.json")
    baseline_path = Path(approved["baseline_index_path"])
    assert sha(baseline_path) == BASELINE_SHA
    assert sha(approved["global_selection_manifest_path"]) == GLOBAL_SHA
    assert approved["global_selection_manifest_sha256"] == GLOBAL_SHA
    global_selection = read(approved["global_selection_manifest_path"])
    manifest = read(BUILD / "baseline-manifest.json")
    baseline = read(baseline_path)["concepts"]
    reserved = {r["id"]: r for r in approved["accepted"]}
    assert len(reserved) == 69
    bodies = read(HERE / "draft-bodies.json")
    assert set(bodies) <= set(reserved)
    source_map = {s["id"]: s for s in read(HERE / "inspected-sources.json")["sources"]}
    additional = HERE / "additional-sources.json"
    if additional.exists():
        for source in read(additional)["sources"]:
            assert source["id"] not in source_map
            source_map[source["id"]] = source
    used_sources = set()
    concepts, reviews, subfields = [], {}, {}
    budgets = defaultdict(lambda: {"card_words": 0, "supporting_prose_words": 0, "concept_ids": [], "word_limit": 200})
    for cid, reservation in reserved.items():
        if cid not in bodies:
            continue
        draft = bodies[cid]
        assert draft["author_reviewed"] is True
        card = draft["card"]
        assert 30 <= len(card.split()) <= 50, (cid, len(card.split()))
        version = reservation["required_card_version"]
        source_ids = draft.get("source_ids") or [e["source_id"] for e in reservation["discovery_evidence"]]
        evidence = []
        for sid in source_ids:
            assert sid in source_map
            source = source_map[sid]
            evidence.append({"source_id": sid, "locator": draft.get("locators", {}).get(sid, source["locator"]),
                             "note": draft["evidence_notes"].get(sid, draft.get("evidence_note", "Inspected passage supports this card's explanation."))})
        parent = reservation.get("proposed_parent")
        relations = []
        if parent:
            premise_sources = draft.get("parent_source_ids") or [e["source_id"] for e in reservation["discovery_evidence"] if e["url"] == parent["url"]]
            assert premise_sources
            relations.append({"target_id": parent["target_id"], "type": parent["type"], "source_ids": premise_sources,
                              "assertion": parent["assertion"], "note": draft.get("parent_note", parent["note"])})
        for r in reservation.get("proposed_related_relations") or []:
            relations.append({"target_id": r["target_id"], "type": "related_to", "source_ids": r["source_ids"],
                              "assertion": r["assertion"], "note": draft.get("related_notes", {}).get(r["target_id"], r["note"])})
        for r in relations:
            assert r["target_id"] in set(baseline) | set(approved["all_reserved_ids"])
            assert r["target_id"] != cid
            assert all(s in source_map for s in r["source_ids"])
        raw = copy.deepcopy(baseline[cid]["inventory_records"]) if cid in baseline else []
        concept = {"id": cid, "label": reservation["label"], "aliases": reservation["aliases"],
                   "entity_kind": reservation["entity_kind"], "scope": reservation["scope"],
                   "domains": [reservation["primary_domain"]], "learning_takeaway": reservation["learning_takeaway"],
                   "card": card, "original_description": baseline[cid]["original_description"] if cid in baseline else None,
                   "identity_urls": list(dict.fromkeys([source_map[s]["url"] for s in source_ids])),
                   "evidence": evidence, "relations": relations, "card_version": version, "imported_records": raw}
        concepts.append(concept)
        subfields[cid] = {"owner": "science", "primary_subfield": reservation["primary_subfield"],
                          "inventory_status": reservation["inventory_status"], "parent_gap": parent is None and reservation["scope"] in {"idea", "facet_or_application"}}
        used_sources.update(source_ids)
        for r in relations:
            used_sources.update(r["source_ids"])
        reviews[cid] = {"outcome": "author_pass", "card_version": version, "required_card_version": version,
                        "inventory_status": reservation["inventory_status"], "word_count": len(card.split()),
                        "meaning_check": "Reserved subject and shared-name boundary preserved.",
                        "meaning_review_reference": {"approved_selection_path": str(HERE / "approved-selection.json"), "id": cid,
                                                     "fields": ["identity_reason", "nearest_baseline_matches", "aliases"]},
                        "claim_review": draft.get("claim_review", "Every substantive claim checked against the attached inspected passages."),
                        "inspected_locators": [{"source_id": e["source_id"], "locator": e["locator"]} for e in evidence],
                        "relations_reviewed": [{"target_id": r["target_id"], "type": r["type"], "assertion": r["assertion"],
                                                "source_ids": r["source_ids"], "outcome": "author_pass"} for r in relations],
                        "limits": draft.get("limits", reservation["limits"]),
                        "independent_audit": "pending; this is the author's review"}
        # Conservative shared-page accounting charges the entire body/takeaway to
        # every attached explanatory source. Metadata and unchanged raw provenance
        # are not discovery prose; evidence and relationship notes are counted.
        for sid in source_ids:
            budget = budgets[source_map[sid]["url"]]
            budget["card_words"] += len(card.split())
            budget["supporting_prose_words"] += len(concept["learning_takeaway"].split())
            budget["concept_ids"].append(cid)
        for e in evidence:
            budgets[source_map[e["source_id"]]["url"]]["supporting_prose_words"] += len(e["note"].split())
        for r in relations:
            for sid in r["source_ids"]:
                budgets[source_map[sid]["url"]]["supporting_prose_words"] += len(r["note"].split())
        for sid in source_ids:
            budgets[source_map[sid]["url"]]["supporting_prose_words"] += sum(len(x.split()) for x in reviews[cid]["limits"])

    sources = []
    for sid in sorted(used_sources):
        source = copy.deepcopy(source_map[sid])
        source.pop("note", None)
        stamp = source["acquisition"]["local_inspected_at"]
        source.update(retrieved_at=stamp, retrieval_date=stamp[:10],
                      acquisition_qualification="Local post-inspection timestamp/date; exact remote acquisition time unavailable.")
        sources.append(source)
    title_overrides = {
        "science-food-lai": "Leaf Area Index",
        "science-food-stale": "The Stale Seedbed Technique: A Relatively Underused Alternative Weed Management Tactic for Vegetable Production",
        "science-physics-dm": "Essential Radio Astronomy — Chapter 6: Pulsars",
        "science-earth-stokes": "Lagrangian and Eulerian representations of fluid flow — Part 2: Advection of parcels and fields",
        "science-earth-bankfull-usfs": "Stream Simulation: Appendix D—Estimating Design Stream Flows at Road-Stream Crossings",
        "science-home-glossary": "4-H FCS Skill-a-thon: Sewing and Clothing ID",
        "science-health-length": "Crunching Numbers: What Cancer Screening Statistics Really Tell Us",
    }
    for s in sources:
        s["title"] = title_overrides.get(s["id"], s["title"])
        if s["id"] == "science-home-glossary":
            s["revision"] = "Revised March 2023, as stated on PDF cover"
    controls = []
    for ctl in approved["controls"]:
        if ctl["id"] not in bodies:
            continue
        c = copy.deepcopy(ctl)
        c["reason"] = "New researched card/reference bundle; increment the maximum known full prior card version."
        c["prior_full_records"] = []
        for index, prior in enumerate(baseline[ctl["id"]].get("candidate_records", [])):
            pointer = ctl["prior_full_records_pointer"] + "/" + str(index)
            bundle_path = prior.get("source_bundle_path")
            bundle_sha = prior.get("source_bundle_sha256")
            if bundle_path is None:
                # Early batches predate explicit source-bundle metadata in the
                # baseline records; their pinned original candidate is the bundle.
                bundle_path = "data/catalog-candidates/" + prior["batch_id"] + ".json"
                bundle_sha = manifest["inputs_sha256"][bundle_path]
            assert sha(REPO / bundle_path) == bundle_sha
            original_bundle = read(REPO / bundle_path)
            original_concepts = original_bundle["concepts"]
            matches = [r for r in original_concepts if r["id"] == ctl["id"] and r["card_version"] == prior["record"]["card_version"]]
            assert len(matches) == 1 and matches[0] == prior["record"]
            c["prior_full_records"].append({"batch_id": prior["batch_id"], "batch_revision": prior.get("batch_revision"),
                "card_version": prior["record"]["card_version"], "full_record_pointer": pointer + "/record",
                "source_bundle_path": bundle_path, "source_bundle_sha256": bundle_sha,
                "reference_scope": "Original candidate record and original bundle namespace retained at the pinned baseline pointer."})
        controls.append(c)
    notes_path = HERE / "source-notes.json"
    source_notes = read(notes_path)["notes"] if notes_path.exists() else []
    for note in source_notes:
        for sid in note["source_ids"]:
            assert sid in used_sources
            url = source_map[sid]["url"]
            budgets[url]["supporting_prose_words"] += len(note["text"].split())
            budgets[url]["research_note_words"] = budgets[url].get("research_note_words", 0) + len(note["text"].split())
    complete = len(concepts) == 69
    for url, budget in budgets.items():
        budget["total_derived_words"] = budget["card_words"] + budget["supporting_prose_words"]
        budget["within_limit"] = budget["total_derived_words"] <= budget["word_limit"]
    now = datetime.now(timezone.utc).isoformat()
    summary = {"status": "draft_ready_for_independent_audit" if complete else "partial_author_checkpoint",
               "concept_count": len(concepts), "source_count": len(sources),
               "inventory_status_counts": dict(Counter(subfields[c["id"]]["inventory_status"] for c in concepts)),
               "scope_counts": dict(Counter(c["scope"] for c in concepts)),
               "domain_counts": dict(Counter(c["domains"][0] for c in concepts)),
               "named_count": sum(c["entity_kind"] == "named_subject" for c in concepts),
               "word_count_min": min(len(c["card"].split()) for c in concepts),
               "word_count_max": max(len(c["card"].split()) for c in concepts),
               "author_review_count": len(reviews), "independent_audit": "pending",
               "token_usage": None, "cost_usage": None, "external_ai_api_calls": 0}
    candidate = {"schema_version": 1,
        "batch": {"id": "research-batch-008-science", "revision": 1, "assignment": "science", "target_count": 69,
                  "completion_status": summary["status"], "language": "en", "date": now[:10],
                  "global_selection_manifest_sha256": GLOBAL_SHA, "baseline_index_sha256": BASELINE_SHA,
                  "approved_selection_sha256": sha(HERE / "approved-selection.json"),
                  "approved_selection_path": str(HERE / "approved-selection.json"),
                  "selection_input_snapshots": approved["input_snapshots"], "concept_ownership_and_subfields": subfields,
                  "excluded_alternative_ids": [r["proposal"]["id"] for r in global_selection["excluded_alternatives"] if r["owner"] == "science"],
                  "control_version_decisions": controls, "word_budget": [30, 50], "word_counting": "Whitespace-separated body words; label and sources excluded.",
                  "source_acquisition_policy": "retrieved_at/retrieval_date are local post-inspection values, never represented as exact remote acquisition times.",
                  "authoring": "Inspected public primary/official/educational passages; no private ratings; exactly approved primaries; alternatives excluded.",
                  "source_word_budget_path": str(HERE / "source-word-budgets.json")},
        "sources": sources, "concepts": concepts,
        "issues": [{"type": "independent_audit_pending", "note": "This is an author-checked draft, not independent factual acceptance or operational import."},
                   {"type": "usage_unavailable", "note": "Actual tool/model token and cost usage is unavailable; no external AI API calls were used."}],
        "validation": summary}
    spec = importlib.util.spec_from_file_location("batch008_adapter", BUILD / "tools/assemble.py")
    adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)
    stock = adapter.stock_module()
    stock.validate_candidate(candidate, HERE / "candidate.json")
    aliases = defaultdict(set)
    for c in concepts:
        for name in [c["label"], *c["aliases"]]:
            key = stock.normalize_alias(name)
            aliases[key].add(c["id"])
    assert all(len(x) == 1 for x in aliases.values())
    baseline_aliases = defaultdict(set)
    for cid, concept in baseline.items():
        for name in [concept["label"], *concept.get("aliases", [])]:
            baseline_aliases[stock.normalize_alias(name)].add(cid)
    conflicts = [{"alias": key, "draft": sorted(ids), "baseline": sorted(baseline_aliases[key] - ids)}
                 for key, ids in aliases.items() if baseline_aliases[key] - ids]
    assert not conflicts, conflicts
    global_aliases = defaultdict(set)
    for r in global_selection["accepted"]:
        for name in [r["label"], *r["aliases"]]:
            global_aliases[stock.normalize_alias(name)].add(r["id"])
    global_conflicts = [{"alias": key, "draft": sorted(ids), "global": sorted(global_aliases[key] - ids)}
                        for key, ids in aliases.items() if global_aliases[key] - ids]
    assert not global_conflicts, global_conflicts
    for c in concepts:
        if c["id"] in baseline:
            previous = baseline[c["id"]]
            assert c["original_description"] == previous["original_description"]
            assert c["imported_records"] == previous["inventory_records"]
            assert c["card_version"] == previous.get("latest_card_version", 0) + 1
        else:
            assert c["card_version"] == 1 and c["original_description"] is None and c["imported_records"] == []
    summary["stock_validate_candidate"] = "passed"
    summary["aliases_and_targets"] = "passed against frozen baseline and global reservations"
    summary["control_originals_raw_rows_and_prior_bundles"] = "passed"
    summary["shared_page_word_budget"] = "passed" if all(v["within_limit"] for v in budgets.values()) else "needs additional evidence or shorter supporting prose"
    write("candidate.json", candidate)
    write("author-review.json", {"schema_version": 1, "batch_id": "research-batch-008-science", "status": summary["status"], "reviews": reviews})
    write("source-word-budgets.json", {"schema_version": 1, "counting": "Conservative body + takeaway + evidence/relation notes + author limits + substantive research notes by shared URL; unchanged provenance, titles and generic review metadata excluded.", "pages": dict(budgets)})
    write("draft-validation.json", summary)
    print(json.dumps(summary, indent=2))
    over = {url: v["total_derived_words"] for url, v in budgets.items() if not v["within_limit"]}
    if over:
        print("OVER_BUDGET", json.dumps(over, indent=2))


if __name__ == "__main__":
    main()
