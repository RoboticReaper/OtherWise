"""Build a fixed, domain-capped catalog from Wikimedia's curated list + Wikidata.

Run from any directory with the project's Python. Public API responses are cached
locally; runtime recommendation needs neither these APIs nor this script.
"""
from __future__ import annotations

import hashlib
import argparse
import json
import re
import time
from collections import Counter, defaultdict, deque
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / ".cache/wikimedia-sections"
ENTITY_CACHE = ROOT / ".cache/wikidata-concepts"
LIST_TITLE = "List of articles every Wikipedia should have/Expanded"
LIST_URL = "https://meta.wikimedia.org/wiki/" + LIST_TITLE.replace(" ", "_")
CAP = 160
# The guide abbreviates these labels (e.g. "Country" and "Major"). Use the
# reviewed English Wikidata label to keep the recommendation understandable.
DESCRIPTIVE_LABEL_IDS = {"Q83440", "Q58795659", "Q12827391", "Q612024", "Q148442", "Q185298"}


def key(text):
    return re.sub(r"[\s_\-\u2010-\u2015]+", " ", text.strip().casefold())


def clean_heading(text):
    return re.sub(r",\s*[\d,]+\s*$", "", text).strip()


def domain_for(section, headings):
    h2, h3 = headings.get(2, ""), headings.get(3, "")
    if section == "Philosophy and religion":
        return "Philosophy" if h2 == "Philosophy" else "Religion & spirituality"
    if section == "Anthropology, psychology and everyday life":
        return "Mind & behavior" if h3 == "Psychology" else "Society & relationships"
    if section == "Mathematics": return "Mathematics"
    if section == "Physical sciences":
        return {"Chemistry": "Chemistry & materials", "Earth science": "Earth & environment",
                "Applied Sciences and Engineering Technology": "Engineering & transport"}.get(h3, "Physics & astronomy")
    if section == "Biology and health sciences":
        return "Health & medicine" if h3 == "Medical sciences" else "Biology & nature"
    if section == "Geography": return "Geography & travel"
    if section == "History": return "History & culture"
    if section == "Arts":
        if h2 == "Language and Literature":
            return "Learning & language" if h3 == "Language" else "Literature & storytelling"
        return {"Music": "Music & performance", "Performing arts": "Music & performance",
                "Recreation: games and sports": "Games & sports"}.get(h3, "Visual arts & design")
    if section == "Society and social sciences":
        return {"Business and economics": "Economics & organizations", "Law": "Politics & law",
                "Politics": "Politics & law", "Public administration, government, military affairs": "Politics & law",
                "Education": "Learning & language", "Information": "Computing & information"}.get(h3, "Society & relationships")
    if section == "Technology":
        return {"Information technology": "Computing & information", "Agriculture and forestry": "Food & agriculture",
                "Domestic science": "Food & agriculture", "Chemical industries": "Chemistry & materials",
                "Materials industries": "Chemistry & materials", "Finished goods": "Home & crafts",
                "Communications and management": "Economics & organizations"}.get(h3, "Engineering & transport")
    raise ValueError(f"Unmapped source section: {section}")


CURATED_DOMAINS = {
    "Nature & food": "Food & agriculture", "Environment & energy": "Earth & environment",
    "Cities & communities": "Society & relationships", "Technology": "Computing & information",
    "Mind & behavior": "Mind & behavior", "Arts & design": "Visual arts & design",
    "History & culture": "History & culture", "Society & governance": "Politics & law",
    "Economy & work": "Economics & organizations", "Science & space": "Physics & astronomy",
    "Health & movement": "Health & medicine", "Language & learning": "Learning & language",
    "Cooking & cuisines": "Food & agriculture", "Coffee, tea & beverages": "Food & agriculture",
    "Music genres & traditions": "Music & performance", "Music making & listening": "Music & performance",
    "Film, television & performance": "Visual arts & design", "Games & interactive worlds": "Games & sports",
    "Sports & physical skills": "Games & sports", "Outdoor recreation & travel": "Geography & travel",
    "Crafts & making": "Home & crafts", "Visual arts & design practice": "Visual arts & design",
    "Home, personal style & everyday life": "Home & crafts", "Literature & writing": "Literature & storytelling",
    "Philosophy & ethical traditions": "Philosophy", "Religion, spirituality & ritual": "Religion & spirituality",
    "Relationships, family & community life": "Society & relationships", "Pets & animal interests": "Biology & nature",
    "Computing & software practice": "Computing & information", "Electronics, engineering & tinkering": "Engineering & transport",
    "Business, organizations & careers": "Economics & organizations", "Economics & financial literacy": "Economics & organizations",
    "Mathematics & reasoning": "Mathematics", "World history & heritage": "History & culture",
    "Geography & place": "Geography & travel", "Education, communication & learning practice": "Learning & language",
    "Law, civic life & social questions": "Politics & law",
}


def curated_domain(row):
    if row["domain"] != "Foundations of natural science": return CURATED_DOMAINS[row["domain"]]
    title = row["topic"]
    if "chemistry" in title.lower(): return "Chemistry & materials"
    if title in {"Geology", "Meteorology", "Oceanography"}: return "Earth & environment"
    if title in {"Paleontology", "Biology", "Genetics", "Microbiology", "Botany", "Zoology", "Ecology", "Neuroscience", "Developmental biology"}:
        return "Biology & nature"
    return "Physics & astronomy"


def parse_section(data):
    parsed = data["parse"]
    section = parsed["title"].rsplit("/", 1)[-1]
    headings, rows = {}, []
    for line in parsed["wikitext"]["*"].splitlines():
        match = re.match(r"^(={2,6})\s*(.*?)\s*\1\s*$", line)
        if match:
            level = len(match[1])
            headings = {k: v for k, v in headings.items() if k < level}
            headings[level] = clean_heading(match[2])
            continue
        if not line.lstrip().startswith("#"): continue
        for qid, title in re.findall(r"\[\[d:(Q\d+)\|([^\]]+)\]\]", line):
            # Keep concepts and cultural/historical subjects, not a biography feed.
            path = " / ".join(headings.values())
            if any(word in path.lower() for word in ("specific works", "specific structures", "companies", "educational institutions")):
                continue
            rows.append(dict(qid=qid, topic=title.replace("''", "").strip(),
                             domain=domain_for(section, headings), subsection=path,
                             priority="'''" in line, list_section=section,
                             list_revision=parsed.get("revid")))
    return rows


def fetch_entities(ids, interactive=False):
    ENTITY_CACHE.mkdir(parents=True, exist_ok=True)
    path = ENTITY_CACHE / (hashlib.sha256("|".join(ids).encode()).hexdigest()[:20] + ".json")
    if path.exists(): return json.loads(path.read_text())["entities"]
    session = requests.Session()
    session.headers["User-Agent"] = "ProductSpaceDemo/1.0 (local educational concept catalog)"
    session.mount("https://", HTTPAdapter(max_retries=Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])))
    for attempt in range(6):
        params = {
            "action": "wbgetentities", "ids": "|".join(ids), "props": "labels|descriptions|claims|info",
            "languages": "en", "format": "json",
        }
        if not interactive: params["maxlag"] = 5
        response = session.get("https://www.wikidata.org/w/api.php", params=params, timeout=45)
        response.raise_for_status()
        data = response.json()
        if data.get("error", {}).get("code") != "maxlag": break
        time.sleep(min(30, max(5, float(response.headers.get("Retry-After", 5)))))
    if "entities" not in data: raise RuntimeError(str(data)[:300])
    # Retain only instance-of claims needed for filtering, keeping the cache compact.
    for entity in data["entities"].values():
        entity["claims"] = {"P31": entity.get("claims", {}).get("P31", [])}
    path.write_text(json.dumps(data, ensure_ascii=False))
    return data["entities"]


def build_catalog(candidates, entities, curated):
    selected, seen_titles, seen_ids = [], set(), set()
    counts = Counter()
    for row in curated:
        domain = curated_domain(row)
        if key(row["topic"]) in seen_titles or counts[domain] >= CAP: continue
        selected.append(dict(row, domain=domain, subsection=row["domain"]))
        seen_titles.add(key(row["topic"])); counts[domain] += 1
    pools = defaultdict(lambda: defaultdict(list))
    reasons = Counter()
    for row in candidates:
        entity = entities.get(row["qid"], {})
        guide_title = row["topic"]
        label = entity.get("labels", {}).get("en", {}).get("value", "").strip()
        if row["qid"] in DESCRIPTIVE_LABEL_IDS and label:
            row = dict(row, topic=label[:1].upper() + label[1:])
        description = entity.get("descriptions", {}).get("en", {}).get("value", "").strip()
        types = {c.get("mainsnak", {}).get("datavalue", {}).get("value", {}).get("id")
                 for c in entity.get("claims", {}).get("P31", [])}
        if "Q5" in types or "Q4167410" in types or "Q13406463" in types:
            reasons["human_disambiguation_or_list"] += 1; continue
        if len(description.split()) < 3:
            reasons["missing_or_too_short_description"] += 1; continue
        if row["qid"] in seen_ids or key(row["topic"]) in seen_titles:
            reasons["duplicate_title_or_entity"] += 1; continue
        pools[row["domain"]][row["subsection"]].append(dict(
            topic=row["topic"], domain=row["domain"], description=description,
            source="Wikidata", source_url=f"https://www.wikidata.org/wiki/{row['qid']}",
            guide_title=guide_title,
            wikidata_id=row["qid"], subsection=row["subsection"],
            source_revision=entity.get("lastrevid"), list_revision=row["list_revision"],
            list_section=row["list_section"], _priority=row["priority"]))
    # Rotate through subtopics, taking foundational (bolded) entries first within
    # each subtopic. Never fill a short domain by overpopulating another domain.
    for domain, subtopics in sorted(pools.items()):
        queues = [deque(sorted(rows, key=lambda r: (not r["_priority"], r["topic"].casefold())))
                  for _, rows in sorted(subtopics.items())]
        while counts[domain] < CAP and any(queues):
            for queue in queues:
                if counts[domain] >= CAP: break
                while queue:
                    row = queue.popleft()
                    if key(row["topic"]) in seen_titles or row["wikidata_id"] in seen_ids: continue
                    row.pop("_priority")
                    selected.append(row); counts[domain] += 1
                    seen_titles.add(key(row["topic"])); seen_ids.add(row["wikidata_id"])
                    break
    return selected, reasons


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interactive", action="store_true", help="Human-waiting run: omit optional maxlag, per Wikimedia's API guidance.")
    args = parser.parse_args()
    CACHE.mkdir(parents=True, exist_ok=True)
    sections = ["Philosophy and religion", "Society and social sciences", "Anthropology, psychology and everyday life",
                "Mathematics", "Physical sciences", "Biology and health sciences", "Technology", "Arts", "Geography", "History"]
    for section in sections:
        path = CACHE / (section.replace(" ", "_") + ".json")
        if path.exists(): continue
        response = requests.get("https://meta.wikimedia.org/w/api.php", params={
            "action": "parse", "page": LIST_TITLE + "/" + section, "prop": "wikitext|revid", "format": "json"
        }, headers={"User-Agent": "ProductSpaceDemo/1.0 (local educational concept catalog)"}, timeout=45)
        response.raise_for_status()
        data = response.json()
        if "parse" not in data: raise RuntimeError(str(data)[:300])
        path.write_text(json.dumps(data, ensure_ascii=False))
    files = sorted(CACHE.glob("*.json"))
    if len(files) != 10:
        raise RuntimeError("Expected the 10 cached Wikimedia section snapshots; see data/README.md.")
    candidates = [r for p in files for r in parse_section(json.loads(p.read_text()))]
    ids = sorted({r["qid"] for r in candidates}, key=lambda x: int(x[1:]))
    batches = [ids[i:i+50] for i in range(0, len(ids), 50)]
    entities = {}
    for i, batch in enumerate(batches):
        entities.update(fetch_entities(batch, interactive=args.interactive))
        if i % 10 == 0: print(f"Descriptions: {min((i+1)*50, len(ids))}/{len(ids)}", flush=True)
    curated = json.loads((ROOT / "data/curated_topics.json").read_text())
    rows, reasons = build_catalog(candidates, entities, curated)
    metadata = dict(snapshot_date=datetime.now(ZoneInfo("America/Chicago")).date().isoformat(),
                    topic_count=len(rows), domain_count=len({r['domain'] for r in rows}),
                    domain_cap=CAP, domains=dict(sorted(Counter(r['domain'] for r in rows).items())),
                    source_counts=dict(Counter(r['source'] for r in rows)),
                    list_url=LIST_URL, source_item_count=len(ids), filtering_counts=dict(reasons),
                    selection="Keep authored concepts, then round-robin source subsections up to 160 per domain; prioritize bold foundational entries within subsections. Never invent topics to fill quotas.",
                    licenses={"Wikidata labels and descriptions": "CC0", "Wikimedia list structure": "CC BY-SA 4.0"},
                    excluded="Biography section, explicitly listed individual works/buildings/companies/educational institutions, entities directly marked as humans/disambiguation/list pages, missing short descriptions.",
                    caveat="Domain caps balance counts, not cultural neutrality or subjective relevance. Subjects, species, places and historical events may all be represented.")
    assert len(rows) == len({key(r['topic']) for r in rows})
    assert max(metadata['domains'].values()) <= CAP
    (ROOT / "data/topics.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False)+"\n")
    (ROOT / "data/catalog_metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False)+"\n")
    print(json.dumps(metadata, indent=2), flush=True)


if __name__ == "__main__": main()
