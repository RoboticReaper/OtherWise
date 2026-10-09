"""Check this selection checkpoint; structural/identity checks do not certify facts."""
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUILD = HERE.parent.parent
BASELINE = BUILD / "baseline-index.json"


def normalize(value):
    # Same text normalization used in the frozen catalog's name inventory.
    return re.sub(r"[\s_\-\u2010-\u2015]+", " ", value.strip().casefold())


def main():
    baseline = json.loads(BASELINE.read_text())
    data = json.loads((HERE / "proposals.json").read_text())
    concepts = baseline["concepts"]
    expected = {
        "Biology & nature": 9, "Chemistry & materials": 9,
        "Earth & environment": 9, "Food & agriculture": 9,
        "Health & medicine": 9, "Home & crafts": 8,
        "Mathematics": 8, "Physics & astronomy": 8,
    }
    digest = hashlib.sha256(BASELINE.read_bytes()).hexdigest()
    assert digest == data["baseline_index_sha256"]
    proposals = data["proposals"]
    primary = [p for p in proposals if p["selection_role"] == "primary"]
    assert len(proposals) <= 100
    assert len(primary) == 69
    assert Counter(p["primary_domain"] for p in primary) == Counter(expected)
    assert Counter(p["inventory_status"] for p in primary) == {"existing": 8, "proposed_new": 61}
    assert {p["scope"] for p in primary} == {"broad_field", "topic", "idea", "facet_or_application"}
    assert len({p["id"] for p in proposals}) == len(proposals)
    source_map = {s["id"]: s for s in data["sources_inspected"]}
    assert len(source_map) == len(data["sources_inspected"])
    for s in source_map.values():
        datetime.fromisoformat(s["acquisition"]["local_inspected_at"].replace("Z", "+00:00"))
        assert s["url"].startswith("https://") and s["locator"]

    extra = {
        "kleptoplasty": ["plastid retention", "chloroplast retention", "kleptoplast"],
        "guard-cell": ["guard cells"], "root-hair": ["root hairs"],
        "casparian-strip": ["Casparian band"],
        "apoplast": ["apoplastic"], "symplast": ["symplastic"],
        "glass-transition": ["glass transition", "glass-transition"],
        "physical-aging-polymers": ["physical aging", "physical ageing", "polymer aging"],
        "spinodal-decomposition": ["spinodal"], "photobleaching": ["photobleach"],
        "surface-plasmon-resonance-microscopy": ["surface plasmon", "SPR microscopy"],
        "critical-micelle-concentration": ["micellar", "critical concentration", "micelle"],
        "sperners-lemma": ["Sperner", "fully labelled triangle", "fully labeled triangle"],
        "sperners-theorem": ["Sperner", "antichain"],
        "ham-sandwich-theorem": ["ham sandwich", "Stone Tukey"],
        "desargues-theorem": ["Desargues"], "van-der-waerdens-theorem": ["Waerden"],
        "thue-morse-sequence": ["Thue Morse", "Prouhet"],
        "bayes-factor": ["Bayes factor", "marginal likelihood"],
        "nixtamalization": ["nixtamal", "alkaline maize"],
        "stale-seedbed": ["stale seedbed", "false seedbed"],
        "soil-solarization": ["solarization", "solarisation"],
        "occultation-weed-control": ["occultation", "opaque tarps"],
        "dryeration": ["dryeration"],
        "case-hardening-food-drying": ["case hardening"],
        "degrees-brix": ["Brix", "soluble solids"], "leaf-area-index": ["leaf area"],
        "selvage": ["selvedge", "selvage"],
        "grainline-woven-fabric": ["grainline", "grain line", "woven fabric grain"],
        "basting-sewing": ["basting"], "seam-allowance": ["seam allowance"],
        "wearing-ease": ["wearing ease", "pattern ease"],
        "design-ease": ["design ease"], "gathering-sewing": ["gathering"],
        "length-time-bias": ["length time bias", "length bias", "length biased"],
        "sentinel-lymph-node-biopsy": ["sentinel", "sentinel node"],
        "deprescribing": ["deprescri"], "refeeding-syndrome": ["refeeding"],
        "surgical-anastomosis": ["anastomosis"], "nonunion": ["nonunion", "non union"],
        "negative-pressure-wound-therapy": ["negative pressure", "vacuum assisted closure"],
        "immortal-time-bias": ["immortal time", "immortality bias"],
        "lageos": ["LAGEOS", "Laser Geodynamics"],
        "hayabusa2": ["Hayabusa", "Ryugu"], "101955-bennu": ["Bennu"],
        "gn-z11": ["GN z11"], "dispersion-measure": ["dispersion measure", "electron column"],
        "coherent-dedispersion": ["dedispersion", "de dispersion"],
        "muon-tomography": ["muon tomography", "muon radiography", "muography"],
        "frost-heave": ["frost heave", "frost heaving"], "cryosuction": ["cryosuction"],
        "pycnocline": ["pycnocline"], "halocline": ["halocline"],
        "stokes-drift": ["Stokes drift", "mass transport velocity"],
        "bankfull-discharge": ["bankfull", "channel forming discharge", "effective discharge"],
        "blood-falls": ["Blood Falls"], "ferrar-glacier": ["Ferrar Glacier"],
        "taylor-glacier": ["Taylor Glacier"], "bias-tape": ["bias tape", "bias binding"],
    }
    corpus = {}
    for identity, c in concepts.items():
        corpus[identity] = normalize(" ".join(
            [c["label"], *c.get("aliases", []), c.get("original_description") or ""]
            + [r["record"].get("card", "") for r in c.get("candidate_records", [])]
        ))
    checks = []
    changed_labels = []
    for p in proposals:
        assert "card" not in p
        assert bool(p["discovery_evidence"])
        assert (p["id"] in concepts) == (p["inventory_status"] == "existing")
        for near in p["nearest_baseline_matches"]:
            assert near["id"] in concepts, (p["label"], near)
            canonical = concepts[near["id"]]["label"]
            if near["label"] != canonical:
                changed_labels.append([p["label"], near["label"], canonical])
                near["label"] = canonical
        for e in p["discovery_evidence"]:
            assert e["source_id"] in source_map
            assert e["url"] == source_map[e["source_id"]]["url"]
        parent = p["proposed_parent"]
        if parent:
            assert parent["target_id"] in concepts
            assert parent["assertion"] in {"source_asserted", "editorial"}
            assert parent["type"] in {"broader_topic", "facet_of", "application_of"}
        for related in p.get("proposed_related_relations", []):
            assert related["target_id"] in concepts
            assert related["type"] == "related_to"
        exact = {t: baseline["aliases"].get(normalize(t), []) for t in [p["label"], *p["aliases"]]}
        if p["inventory_status"] == "proposed_new":
            assert not any(exact.values()), (p["label"], exact)
        queries = list(dict.fromkeys([p["label"], *p["aliases"], *extra.get(p["id"].split(":")[-1], [])]))
        focused = []
        for q in queries:
            needle = normalize(q)
            hits = [[identity, concepts[identity]["label"]] for identity, text in corpus.items() if needle in text]
            focused.append({"query": q, "matches": hits[:30], "match_count": len(hits), "truncated": len(hits) > 30})
        checks.append({"id": p["id"], "label": p["label"], "role": p["selection_role"], "exact_alias_checks": exact,
                       "focused_label_alias_description_card_checks": focused, "decision": p["identity_reason"],
                       "nearby_meanings": p["nearest_baseline_matches"]})

    fine = [p for p in primary if p["scope"] in {"idea", "facet_or_application"}]
    summary = {
        "schema_version": 1, "assignment": "science", "status": "selection_complete_awaiting_coordinator_reservations",
        "checked_at": datetime.now(timezone.utc).isoformat(), "baseline_index_sha256": digest,
        "baseline_active_ids": len(concepts), "primary_proposals": len(primary), "alternative_proposals": len(proposals) - len(primary),
        "primary_inventory_status": dict(Counter(p["inventory_status"] for p in primary)),
        "primary_domain_counts": dict(Counter(p["primary_domain"] for p in primary)),
        "primary_scope_counts": dict(Counter(p["scope"] for p in primary)),
        "new_fine_scope": sum(p["inventory_status"] == "proposed_new" for p in fine),
        "named_primary": sum(p["entity_kind"] == "named_subject" for p in primary),
        "fine_scope_parent_count": sum(bool(p["proposed_parent"]) for p in fine),
        "fine_scope_source_asserted_parent_count": sum(bool(p["proposed_parent"]) and p["proposed_parent"]["assertion"] == "source_asserted" for p in fine),
        "inspected_source_records": len(source_map), "inspected_distinct_urls": len({s["url"] for s in source_map.values()}),
        "new_exact_alias_collisions": 0, "unresolved_source_or_target_ids": 0,
        "source_and_identity_review_status": "Actual passage notes and individual meaning decisions are recorded; no independent card audit has occurred.",
        "card_drafting_status": "not_started", "canonical_nearby_labels_corrected": changed_labels,
    }
    data["validation"] = summary
    (HERE / "proposals.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    (HERE / "identity-checks.json").write_text(json.dumps({"summary": summary, "checks": checks}, ensure_ascii=False, indent=2) + "\n")
    (HERE / "selection-validation.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
