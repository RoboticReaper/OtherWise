"""Import a bounded Wikipedia category graph with Wikidata descriptions.

All runtime inputs are saved in data/discovery_graph.json. This importer is an
explicit maintenance command; recommendations never need a Wikimedia API call.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from collections import Counter, defaultdict, deque
from copy import deepcopy
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import parse_qs, quote, urlparse

import requests

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
ENWIKI = "https://en.wikipedia.org/w/api.php"
WIKIDATA = "https://www.wikidata.org/w/api.php"
BLOCKED_TYPES = {"Q5", "Q4167410", "Q13406463", "Q4167836"}
MAINTENANCE = re.compile(r"wikipedia|wikiproject|articles? (?:with|needing|lacking)|stubs?$|maintenance|templates|disambiguation|redirects|tracking|cs1 |use dmy|use mdy", re.I)
PEOPLE = re.compile(r"\b(?:people|scientists|researchers|musicians|composers|artists|painters|photographers|psychologists|philosophers|historians|archaeologists|players|chefs|gardeners|designers|theorists|births|deaths)\b", re.I)
CATALOGS = re.compile(r"\b(?:lists|journals|conferences|textbooks|publications|publishers|companies|organizations|museums|portals?)\b|works about|mass media", re.I)
LISTS = re.compile(r"^(?:list(?:s)? of |outline of |glossary of |index of |timeline of )", re.I)


def normalized(title):
    return re.sub(r"[\s_\u2010-\u2015-]+", " ", title.casefold()).strip()


def wiki_url(title):
    return "https://en.wikipedia.org/wiki/" + quote(title.replace(" ", "_"), safe=":()")


def category_id(title):
    return "category:" + title


def allowed_category(title):
    return title.startswith("Category:") and not (MAINTENANCE.search(title) or PEOPLE.search(title) or CATALOGS.search(title) or LISTS.search(title.removeprefix("Category:")))


def sampled(rows, salt, preferred=()):
    """Stable hash order across the observed pool, not its alphabetical prefix."""
    preference = {normalized(title): i for i, title in enumerate(preferred)}
    return sorted(rows, key=lambda row: (preference.get(normalized(row["title"]), len(preference)),
                  hashlib.sha256((salt + "|" + row["title"]).encode()).hexdigest()))


def build_graph(seeds, category_loader, page_loader, entity_loader, *, max_depth=1,
                children_per_category=4, concepts_per_category=24, max_categories=160,
                annotations=None):
    """Transform source records into a bounded graph; loaders also allow offline fixtures.

    Depth counts category-to-category hops. Each visited category can contribute
    article memberships. Edges are emitted only for observed category members.
    """
    if max_depth < 0 or any(value < 1 for value in (children_per_category, concepts_per_category, max_categories)):
        raise ValueError("Depth must be nonnegative and all other limits positive")
    if max_categories < len({seed["category"] for seed in seeds}):
        raise ValueError("max_categories must accommodate every seed category")
    annotations = annotations or {}
    nodes, edges, areas, memberships = {}, {}, [], {}
    filtering, failures, truncated, limited = Counter(), [], [], []
    broad = {normalized(seed["topic"]) for seed in seeds}
    broad.update(normalized(seed["category"].removeprefix("Category:")) for seed in seeds)
    for seed in seeds:
        broad.update(normalized(t) for t in seed.get("exclude_topics", []))

    def add_category(title):
        identifier = category_id(title)
        nodes.setdefault(identifier, dict(id=identifier, topic=title.removeprefix("Category:"),
                         description="Wikipedia category: " + title.removeprefix("Category:"),
                         description_source="Category label", kind="category", source_url=wiki_url(title),
                         wikipedia_title=title))
        return identifier

    # Queue all roots first so a wide first area cannot exhaust other roots' budgets.
    queue, scheduled = deque(), {}
    preferences = {seed["category"]: seed.get("preferred_categories", []) for seed in seeds}
    for seed in seeds:
        preferences.update(seed.get("category_preferences", {}))
    for seed in seeds:
        identifier = add_category(seed["category"])
        areas.append({k: seed[k] for k in ("id", "topic", "description", "domain")} | {"category_id": identifier})
        remaining = seed.get("max_depth", max_depth)
        if remaining < 0:
            raise ValueError("Seed max_depth must be nonnegative")
        if remaining > scheduled.get(seed["category"], -1):
            queue.append((seed["category"], remaining)); scheduled[seed["category"]] = remaining
    visited = {}
    while queue:
        title, remaining = queue.popleft()
        if visited.get(title, -1) >= remaining:
            continue
        visited[title] = remaining
        try:
            record = category_loader(title)
        except (OSError, ValueError, RuntimeError, requests.RequestException) as exc:
            failures.append({"category": title, "error": str(exc)[:240]})
            print(f"Source failure: {title}: {str(exc)[:180]}", flush=True)
            continue
        if record.get("truncated"):
            truncated.append(title)
        source = category_id(title)
        nodes[source]["fetched_at"] = record.get("fetched_at")
        nodes[source]["source_revision"] = record.get("source_revision")
        if record.get("resolved_title"):
            nodes[source]["resolved_title"] = record["resolved_title"]
        if record.get("hidden") or record.get("missing"):
            filtering["hidden_or_missing_category"] += 1
            continue
        members = {row["title"]: row for row in record["members"]}.values()
        children, articles = [], []
        for row in members:
            if row.get("ns") == 14:
                if allowed_category(row["title"]):
                    children.append(row)
                else:
                    filtering["maintenance_people_or_list_category"] += 1
            elif row.get("ns") == 0:
                if LISTS.search(row["title"]) or normalized(row["title"]) in broad or normalized(row["title"]) == normalized(title.removeprefix("Category:")):
                    filtering["broad_area_or_list_article"] += 1
                else:
                    articles.append(row)
        evidence = {"source_url": wiki_url(record.get("resolved_title", title)),
                    "evidence_url": record.get("source_url", wiki_url(title)),
                    "fetched_at": record.get("fetched_at")}
        if remaining > 0:
            chosen = sampled(children, title, preferences.get(title, []))[:children_per_category]
            if len(children) > len(chosen):
                limited.append({"category": title, "reason": "child_category_cap", "observed": len(children), "selected": len(chosen)})
            for row in chosen:
                child = row["title"]
                if child not in scheduled and len(scheduled) >= max_categories:
                    limited.append({"category": child, "reason": "global_category_cap"})
                    continue
                target = add_category(child)
                edges[(source, target)] = dict(source=source, target=target, relation="contains_category",
                                              membership_title=child, **evidence)
                if remaining - 1 > scheduled.get(child, -1):
                    queue.append((child, remaining - 1)); scheduled[child] = remaining - 1
        # Oversample candidates to allow useful results after entity filtering.
        candidates = sampled(articles, title, annotations)[:concepts_per_category * 3]
        if len(articles) > len(candidates):
            limited.append({"category": title, "reason": "article_candidate_cap", "observed": len(articles), "selected": len(candidates)})
        memberships[source] = (source, candidates, evidence)

    broad.update(normalized(node["topic"]) for node in nodes.values())
    titles = sorted({row["title"] for _, rows, _ in memberships.values() for row in rows})
    pages = {}
    for start in range(0, len(titles), 50):
        try:
            pages.update(page_loader(titles[start:start + 50]))
        except (OSError, ValueError, RuntimeError, requests.RequestException) as exc:
            failures.append({"stage": "pages", "titles": titles[start:start + 50], "error": str(exc)[:240]})
    qids = sorted({p["wikidata_id"] for p in pages.values() if p.get("wikidata_id")})
    entities = {}
    for start in range(0, len(qids), 50):
        try:
            entities.update(entity_loader(qids[start:start + 50]))
        except (OSError, ValueError, RuntimeError, requests.RequestException) as exc:
            failures.append({"stage": "entities", "ids": qids[start:start + 50], "error": str(exc)[:240]})
    for source, rows, evidence in memberships.values():
        count, targets = 0, set()
        for row in rows:
            page = pages.get(row["title"], {})
            qid = page.get("wikidata_id")
            if not qid or page.get("missing"):
                filtering["missing_wikidata_or_page"] += 1; continue
            entity = entities.get(qid, {})
            types = {claim.get("mainsnak", {}).get("datavalue", {}).get("value", {}).get("id")
                     for claim in entity.get("claims", {}).get("P31", [])}
            if page.get("disambiguation") or types & BLOCKED_TYPES:
                filtering["human_disambiguation_list_or_category"] += 1; continue
            topic = page.get("title", row["title"])
            if normalized(topic) in broad or LISTS.search(topic):
                filtering["broad_area_or_list_article"] += 1; continue
            description = entity.get("descriptions", {}).get("en", {}).get("value", "").strip()
            if len(description.split()) < 3:
                filtering["missing_description"] += 1; continue
            if qid in targets:
                continue
            targets.add(qid)
            if qid not in nodes:
                node = dict(id=qid, topic=topic, description=description, kind="concept", wikidata_id=qid,
                            source_url="https://www.wikidata.org/wiki/" + qid,
                            description_source="Wikidata", source_revision=entity.get("lastrevid"),
                            wikipedia_title=topic, wikipedia_url=wiki_url(topic),
                            wikipedia_page_id=page.get("pageid"), level=None)
                annotation = annotations.get(topic, annotations.get(row["title"]))
                if annotation:
                    if annotation.get("level") not in (1, 2, 3):
                        raise ValueError("Reviewed levels must be 1, 2, or 3")
                    node.update(hook=annotation["hook"], level=annotation["level"],
                                annotation_source="ProductSpace editorial review")
                nodes[qid] = node
            edges[(source, qid)] = dict(source=source, target=qid, relation="contains_concept",
                                       membership_title=row["title"], **evidence)
            count += 1
            if count == concepts_per_category:
                break
    concept_count = sum(n["kind"] == "concept" for n in nodes.values())
    return dict(version=1, metadata=dict(
        snapshot_date=datetime.now(timezone.utc).date().isoformat(),
        complete=not failures and not truncated,
        completeness_scope="Selected bounded snapshot only; never the complete Wikipedia taxonomy",
        area_count=len(areas), category_count=len(nodes) - concept_count, concept_count=concept_count,
        edge_count=len(edges), reviewed_concept_count=sum(bool(n.get("hook")) for n in nodes.values()),
        max_category_depth=max([max_depth] + [seed.get("max_depth", max_depth) for seed in seeds]),
        default_category_depth=max_depth,
        category_depth_overrides={seed["category"]: seed["max_depth"] for seed in seeds if "max_depth" in seed},
        children_per_category=children_per_category,
        concepts_per_category=concepts_per_category, max_categories=max_categories,
        filtering_counts=dict(filtering), fetch_failures=failures, truncated_categories=truncated,
        selection_limits=limited,
        selection="Manually selected area seeds; observed direct category memberships; preferred reviewed topics then stable SHA-256 sampling; bounded traversal with cycle guard.",
        licenses={"Wikidata descriptions": "CC0", "Wikipedia category structure": "CC BY-SA 4.0"},
        annotation_provenance="Hooks and introductory reading levels are authored ProductSpace editorial judgments, not Wikidata claims. Unreviewed levels are null."),
        areas=areas, nodes=list(nodes.values()), edges=list(edges.values()))


def resolve_pages(query, titles):
    """Resolve API normalization and redirect chains while retaining lookup titles."""
    aliases = {r["from"]: r["to"] for r in query.get("normalized", []) + query.get("redirects", [])}
    pages = {p["title"]: p for p in query["pages"]}
    result = {}
    for title in titles:
        canonical, visited = title, set()
        while canonical in aliases and canonical not in visited:
            visited.add(canonical); canonical = aliases[canonical]
        page = pages.get(canonical, {})
        props = page.get("pageprops", {})
        result[title] = dict(title=canonical, pageid=page.get("pageid"), missing=page.get("missing", False),
                             wikidata_id=props.get("wikibase_item"), disambiguation="disambiguation" in props)
    return result


def balance_graph(graph, *, concepts_per_domain=160):
    """Select equal domain budgets, retaining only observed source paths.

    Area allowlists record the sampled catalog, not extra knowledge-graph edges.
    They stop shared categories from leaking another domain's entire selection.
    """
    from graph_explorer import graph_candidates
    if type(concepts_per_domain) is not int or concepts_per_domain < 1:
        raise ValueError('Concepts per domain must be a positive integer')
    result=deepcopy(graph)
    by_domain=defaultdict(list)
    for area in result['areas']:
        area.pop('concept_ids',None)
        by_domain[area['domain']].append(area)
    depth=graph['metadata'].get('max_category_depth',1)+1
    pools={a['id']: graph_candidates(result,[a['id']],max_depth=depth) for a in result['areas']}
    chosen_paths=[]
    coverage=[]
    for domain,areas in sorted(by_domain.items()):
        ids=set(); assigned={a['id']:[] for a in areas}
        ordered={a['id']:sorted(pools[a['id']],key=lambda r:hashlib.sha256((domain+'|'+a['id']+'|'+r['id']).encode()).hexdigest()) for a in areas}

        def take(predicate,limit):
            added=0
            while added<limit:
                progress=False
                for area in sorted(areas,key=lambda a:(len(assigned[a['id']]),a['id'])):
                    aid=area['id']
                    row=next((r for r in ordered[aid] if r['id'] not in ids and predicate(r)),None)
                    if row is None:continue
                    ids.add(row['id']);assigned[aid].append(row['id'])
                    chosen_paths.append(row['paths'][aid]);added+=1;progress=True
                    if added==limit:break
                if not progress:break

        # Equal small reviewed samples: two entry points at each level per domain.
        for level in (1,2,3):
            take(lambda r:r.get('level')==level,min(2,concepts_per_domain-len(ids)))
        take(lambda r:r.get('level') is None,concepts_per_domain-len(ids))
        # Sparse pools may use extra reviewed entries rather than discard useful data.
        take(lambda r:True,concepts_per_domain-len(ids))
        for area in areas:area['concept_ids']=sorted(assigned[area['id']])
        levels=Counter(r.get('level') for r in result['nodes'] if r['id'] in ids)
        coverage.append(dict(domain=domain,available=len({r['id'] for a in areas for r in pools[a['id']]}),
                             selected=len(ids),reviewed=sum(levels[n] for n in (1,2,3)),
                             reviewed_by_level={str(n):levels[n] for n in (1,2,3)}))
    kept={a['category_id'] for a in result['areas']}
    pairs=set()
    for path in chosen_paths:
        kept.update(path);pairs.update(zip(path,path[1:]))
    result['nodes']=[n for n in result['nodes'] if n['id'] in kept]
    result['edges']=[e for e in result['edges'] if (e['source'],e['target']) in pairs]
    metadata=result['metadata']
    metadata.update(area_count=len(result['areas']),concept_count=sum(n['kind']=='concept' for n in result['nodes']),
                    category_count=sum(n['kind']=='category' for n in result['nodes']),edge_count=len(result['edges']),
                    reviewed_concept_count=sum(n.get('level') is not None for n in result['nodes']))
    reviewed_targets={str(n):max(0,min(2,concepts_per_domain-2*(n-1))) for n in (1,2,3)}
    reviewed_shortfalls={r['domain']:{n:target-r['reviewed_by_level'][n] for n,target in reviewed_targets.items()
                                     if r['reviewed_by_level'][n]<target} for r in coverage}
    metadata['balance']=dict(concepts_per_domain=concepts_per_domain,domain_count=len(by_domain),
                             coverage=coverage,shortfalls={r['domain']:concepts_per_domain-r['selected'] for r in coverage if r['selected']<concepts_per_domain},
                             reviewed_shortfalls={d:levels for d,levels in reviewed_shortfalls.items() if levels},
                             method='Equal domain budgets; round-robin area selection; two reviewed entries per level where available; stable SHA-256 ordering.')
    return result


def build_balanced_graph(seeds, category_loader, page_loader, entity_loader, *, concepts_per_domain=160,
                         max_depth=1, max_categories=600, raw_output=None, **kwargs):
    """Apply the same one-extra-level top-up rule to every underfilled domain."""
    if any('max_depth' in seed for seed in seeds):
        raise ValueError('Balanced imports do not allow seed-specific depth overrides')
    depths={seed['domain']:max_depth for seed in seeds}
    result=None
    for attempt in range(2):
        scoped=[dict(seed,max_depth=depths[seed['domain']]) for seed in seeds]
        raw=build_graph(scoped,category_loader,page_loader,entity_loader,max_depth=max_depth,
                        max_categories=max_categories,**kwargs)
        if raw_output is not None:
            Path(raw_output).parent.mkdir(parents=True,exist_ok=True)
            Path(raw_output).write_text(json.dumps(raw,ensure_ascii=False,indent=2)+'\n')
        result=balance_graph(raw,concepts_per_domain=concepts_per_domain)
        shortfalls=result['metadata']['balance']['shortfalls']
        if not shortfalls or attempt or raw['metadata'].get('fetch_failures'):
            break
        print('Expanding underfilled domains by one category level: '+', '.join(sorted(shortfalls)),flush=True)
        for domain in shortfalls:depths[domain]+=1
    result['metadata']['balance']['traversal_depth_by_domain']=depths
    result['metadata']['balance']['traversal_policy']='Start at the same depth; add one level only for domains below the shared budget.'
    return result


class WikimediaSource:
    """Cached public API access; bounded category enumeration and polite retries."""

    def __init__(self, cache, *, max_member_pages=2, offline=False, refresh=False):
        self.cache = Path(cache)
        self.cache.mkdir(parents=True, exist_ok=True)
        self.max_member_pages, self.offline, self.refresh = max_member_pages, offline, refresh
        self.session = requests.Session()
        self.session.headers["User-Agent"] = "ProductSpaceDiscovery/1.0 (https://github.com/RoboticReaper/OtherWise; local educational category explorer)"
        self.last_request = 0.0
        self.known_entities, self.known_pages = {}, {}
        if not refresh:
            for path in sorted((ROOT / ".cache/wikidata-concepts").glob("*.json")):
                self.known_entities.update(json.loads(path.read_text()).get("entities", {}))
            # Reuse records across changing batch boundaries on repeat imports.
            for path in sorted(self.cache.glob("*.json")):
                record = json.loads(path.read_text())
                payload = record.get("data", {})
                self.known_entities.update(payload.get("entities", {}))
                params = parse_qs(urlparse(record.get("source_url", "")).query)
                if "wikibase_item" in params.get("ppprop", [""])[0] and "pages" in payload.get("query", {}):
                    titles = params.get("titles", [""])[0].split("|")
                    self.known_pages.update(resolve_pages(payload["query"], titles))

    def request(self, endpoint, params):
        params = {"format": "json", "formatversion": 2, **params}
        digest = hashlib.sha256((endpoint + json.dumps(params, sort_keys=True)).encode()).hexdigest()
        path = self.cache / (digest + ".json")
        if path.exists() and not self.refresh:
            return json.loads(path.read_text())
        if self.offline:
            raise RuntimeError("Offline cache miss for " + str(params.get("cmtitle", params.get("titles", params.get("ids", "query")))))
        for attempt in range(4):
            time.sleep(max(0, 0.4 - (time.monotonic() - self.last_request)))
            response = self.session.get(endpoint, params=params, timeout=40)
            self.last_request = time.monotonic()
            if response.status_code in (429, 500, 502, 503, 504) and attempt < 3:
                retry_after = response.headers.get("Retry-After", "")
                try:
                    delay = float(retry_after)
                except ValueError:
                    try:
                        delay = (parsedate_to_datetime(retry_after) - datetime.now(timezone.utc)).total_seconds()
                    except (TypeError, ValueError, OverflowError):
                        delay = max(5, 2 ** attempt)
                print(f"Source returned {response.status_code}; retrying after {max(5, delay):.0f}s", flush=True)
                time.sleep(max(5, delay)); continue
            response.raise_for_status()
            payload = response.json()
            if "error" in payload:
                raise RuntimeError(str(payload["error"]))
            if endpoint == WIKIDATA:
                for entity in payload.get("entities", {}).values():
                    entity["claims"] = {"P31": entity.get("claims", {}).get("P31", [])}
            record = {"data": payload, "source_url": response.url,
                      "fetched_at": datetime.now(timezone.utc).isoformat()}
            path.write_text(json.dumps(record, ensure_ascii=False) + "\n")
            return record
        raise RuntimeError("Wikimedia source retries exhausted")

    def category(self, title):
        info = self.request(ENWIKI, dict(action="query", titles=title, redirects=1, prop="info|pageprops", ppprop="hiddencat"))
        page = info["data"]["query"]["pages"][0]
        resolved = page.get("title", title)
        if page.get("missing"):
            raise RuntimeError("Missing Wikipedia category: " + title)
        members, continuation, sources = [], {}, []
        for _ in range(self.max_member_pages):
            result = self.request(ENWIKI, dict(action="query", list="categorymembers", cmtitle=resolved,
                cmnamespace="0|14", cmsort="timestamp", cmdir="desc", cmlimit=500,
                cmprop="ids|title|timestamp", **continuation))
            sources.append(result["source_url"])
            members.extend(result["data"]["query"]["categorymembers"])
            continuation = result["data"].get("continue", {})
            if not continuation:
                break
        print(f"Category: {resolved.removeprefix('Category:')} ({len(members)} observed members)", flush=True)
        return dict(members=members, source_url=sources[0], query_urls=sources,
                    fetched_at=result["fetched_at"], truncated=bool(continuation),
                    source_revision=page.get("lastrevid"), resolved_title=resolved,
                    hidden="hiddencat" in page.get("pageprops", {}))

    def pages(self, titles):
        missing = [title for title in titles if title not in self.known_pages]
        if missing:
            record = self.request(ENWIKI, dict(action="query", titles="|".join(missing), redirects=1,
                                             prop="pageprops", ppprop="wikibase_item|disambiguation"))
            self.known_pages.update(resolve_pages(record["data"]["query"], missing))
        return {title: self.known_pages[title] for title in titles if title in self.known_pages}

    def entities(self, qids):
        missing = [qid for qid in qids if qid not in self.known_entities]
        if missing:
            record = self.request(WIKIDATA, dict(action="wbgetentities", ids="|".join(missing),
                                  props="descriptions|claims|info", languages="en"))
            self.known_entities.update(record["data"]["entities"])
        return {qid: self.known_entities[qid] for qid in qids if qid in self.known_entities}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=Path, default=ROOT / "data/discovery_seeds.json")
    parser.add_argument("--output", type=Path, default=ROOT / "data/discovery_graph.json")
    parser.add_argument("--cache", type=Path, default=ROOT / ".cache/discovery-graph")
    parser.add_argument("--depth", type=int, default=1)
    parser.add_argument("--children", type=int, default=4)
    parser.add_argument("--concepts", type=int, default=24)
    parser.add_argument("--max-categories", type=int, default=600)
    parser.add_argument("--concepts-per-domain", type=int, default=160)
    parser.add_argument("--max-member-pages", type=int, default=2, help="At most 500 recent members per page; truncation is reported.")
    parser.add_argument("--offline", action="store_true", help="Use cached source responses only.")
    parser.add_argument("--refresh", action="store_true", help="Intentionally replace cached API snapshots.")
    parser.add_argument("--allow-partial", action="store_true", help="Write explicitly marked partial results after source failures.")
    args = parser.parse_args()
    if args.max_member_pages < 1 or (args.offline and args.refresh):
        parser.error("Member pages must be positive; offline and refresh are mutually exclusive")
    seed_data = json.loads(args.seeds.read_text())
    source = WikimediaSource(args.cache, max_member_pages=args.max_member_pages, offline=args.offline, refresh=args.refresh)
    graph = build_balanced_graph(seed_data["areas"], source.category, source.pages, source.entities,
                        max_depth=args.depth, children_per_category=args.children,
                        concepts_per_category=args.concepts, max_categories=args.max_categories,
                        concepts_per_domain=args.concepts_per_domain,
                        raw_output=args.cache / 'raw-pool.json',
                        annotations=seed_data.get("annotations", {}))
    graph["metadata"]["max_member_pages"] = args.max_member_pages
    graph["metadata"]["seeds_file"] = str(args.seeds.name)
    try:
        graph["metadata"]["source_cache"] = str(args.cache.resolve().relative_to(ROOT))
    except ValueError:
        graph["metadata"]["source_cache"] = args.cache.name
    summary = {k: v for k, v in graph["metadata"].items() if k not in ("selection_limits", "source_cache")}
    print(json.dumps(summary, indent=2), flush=True)
    if graph["metadata"]["fetch_failures"] and not args.allow_partial:
        raise SystemExit("Import had source failures; existing output preserved. Retry from cache or opt in with --allow-partial.")
    if graph['metadata']['balance']['shortfalls'] and not args.allow_partial:
        raise SystemExit('Import could not fill every domain budget; existing output preserved. Inspect coverage or opt in with --allow-partial.')
    if graph['metadata']['balance']['reviewed_shortfalls'] and not args.allow_partial:
        raise SystemExit('Reviewed level coverage is incomplete; existing output preserved. Review source concepts or opt in with --allow-partial.')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(".tmp")
    temporary.write_text(json.dumps(graph, indent=2, ensure_ascii=False) + "\n")
    temporary.replace(args.output)


if __name__ == "__main__":
    main()
