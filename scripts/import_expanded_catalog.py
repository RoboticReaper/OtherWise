"""Reproducible offline catalog from Vital Articles Level 5 and Wikidata.

Only this explicit import command contacts source APIs. Cached public responses
make interrupted imports resumable; recommendations read the finished snapshot.
"""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from email.utils import parsedate_to_datetime
import hashlib
import html
import json
from pathlib import Path
import re
import sys
import threading
import time
from urllib.parse import quote
from zoneinfo import ZoneInfo

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from explorer import _key, load_catalog
from galaxy.preprocessing import atomic_json_write

LIST_PAGE = 'Wikipedia:Vital articles/Level 5'
LIST_URL = 'https://en.wikipedia.org/wiki/Wikipedia:Vital_articles/Level_5'
WIKI_API = 'https://en.wikipedia.org/w/api.php'
ENTITY_API = 'https://www.wikidata.org/w/api.php'
EXCLUDED_TYPES = {
    'Q5', 'Q4167410', 'Q13406463',  # person, disambiguation, list
    'Q11424', 'Q571', 'Q482994', 'Q7366', 'Q134556', 'Q5398426',
    'Q7725634', 'Q47461344', 'Q3305213', 'Q860861',  # individual creative works
    'Q4830453', 'Q3918', 'Q3914', 'Q2385804', 'Q41176',
}
NAMESPACES = re.compile(r'^(?:Wikipedia|WP|Category|File|Image|Template|Help|Special|User|Talk|Portal|Draft|Module|Media):', re.I)


def domain_for(page, headings):
    section = page.split('Level 5/', 1)[-1]
    path = (section + ' / ' + ' / '.join(headings.values())).casefold()
    detail = ' / '.join(value for level, value in headings.items() if level >= 2).casefold()
    if section.startswith('Mathematics'): return 'Mathematics'
    if section.startswith('Geography'): return 'Geography & travel'
    if section.startswith('History'): return 'History & culture'
    if section.startswith('Philosophy and religion'):
        specific = ' / '.join(value for level, value in headings.items() if level >= 2)
        return 'Religion & spirituality' if re.search(r'religion|theology|mythology', specific, re.I) else 'Philosophy'
    if section.startswith('Biology and health sciences'):
        return 'Health & medicine' if re.search(r'health|medicine|disease|medical', section.split('/', 1)[-1], re.I) else 'Biology & nature'
    if section.startswith('Physical sciences'):
        if 'chemistry' in path or 'chemical' in path: return 'Chemistry & materials'
        if any(t in path for t in ('earth science', 'geology', 'meteorology', 'climate', 'oceanography')): return 'Earth & environment'
        return 'Physics & astronomy'
    if section.startswith('Technology'):
        # Mixed source pages repeat every subject in their title and level-1
        # heading. Prefer the actual section before falling back to that title.
        if 'medical technology' in detail: return 'Health & medicine'
        if 'biotechnology' in detail: return 'Biology & nature'
        path = detail or path
        if any(t in path for t in ('computing', 'computer', 'information technology', 'software', 'internet', 'communication technology')): return 'Computing & information'
        if any(t in path for t in ('agriculture', 'forestry', 'food processing')): return 'Food & agriculture'
        if 'medical technology' in path: return 'Health & medicine'
        if any(t in path for t in ('chemical', 'materials')): return 'Chemistry & materials'
        return 'Engineering & transport'
    if section.startswith('Everyday life'):
        path = detail or path
        if any(t in path for t in ('family', 'kinship', 'sexuality', 'gender')): return 'Society & relationships'
        if any(t in path for t in ('tourism', 'travel', 'outdoor recreation')): return 'Geography & travel'
        if any(t in path for t in ('sports', 'games', 'recreation')): return 'Games & sports'
        if any(t in path for t in ('food', 'cuisine', 'cooking', 'beverage', 'agriculture')): return 'Food & agriculture'
        if any(t in path for t in ('tourism', 'travel', 'outdoor')): return 'Geography & travel'
        return 'Home & crafts'
    if section.startswith('Arts'):
        path = detail or path
        if any(t in path for t in ('language', 'linguistic')): return 'Learning & language'
        if any(t in path for t in ('music', 'dance', 'theatre', 'theater', 'performance', 'performing arts')): return 'Music & performance'
        if any(t in path for t in ('literature', 'narrative', 'poetry', 'writing')): return 'Literature & storytelling'
        if 'film' in path or 'television' in path: return 'Visual arts & design'
        if section.startswith('Arts/Narrative arts'): return 'Literature & storytelling'
        return 'Visual arts & design'
    if section.startswith('Society and social sciences'):
        path = detail or path
        if any(t in path for t in ('psychology', 'cognition', 'behavior')): return 'Mind & behavior'
        if any(t in path for t in ('education', 'language', 'linguistic', 'learning')): return 'Learning & language'
        if any(t in path for t in ('econom', 'business', 'finance', 'management')): return 'Economics & organizations'
        if any(t in path for t in ('politic', 'law', 'government', 'military')): return 'Politics & law'
        return 'Society & relationships'
    raise ValueError(f'Unmapped Vital Articles section: {section}')


def parse_vital_page(data):
    parsed = data['parse']
    page, headings, rows = parsed['title'], {}, []
    for line in parsed['wikitext']['*'].splitlines():
        match = re.match(r'^(={1,6})\s*(.*?)\s*\1\s*$', line)
        if match:
            level = len(match[1]); headings = {k: v for k, v in headings.items() if k < level}
            headings[level] = re.sub(r'\s*\([^)]*\d[^)]*\)\s*$', '', match[2]).strip()
            continue
        if not re.match(r'^\s*#+', line): continue
        path = ' / '.join(headings.values())
        if re.search(r'specific (?:works|structures|companies)|educational institutions', path, re.I): continue
        for link in re.findall(r'\[\[([^\]]+)\]\]', line):
            article = html.unescape(link.split('|', 1)[0].split('#', 1)[0]).replace('_', ' ').strip()
            if not article or NAMESPACES.match(article.lstrip(':')) or article.startswith(':'): continue
            if article.startswith(('List of ', 'Lists of ')): continue
            rows.append(dict(article=article, domain=domain_for(page, headings), subsection=path,
                             list_page=page, list_revision=parsed['revid']))
            break  # Level annotations and related links are not list entries.
    return rows


def resolve_page_items(data, requested):
    query = data['query']
    aliases = {r['from']: r['to'] for r in query.get('normalized', []) + query.get('redirects', [])}
    pages = {row['title']: row for row in query.get('pages', {}).values()}
    found = {}
    for original in requested:
        title, seen = original, set()
        while title in aliases and title not in seen:
            seen.add(title); title = aliases[title]
        row = pages.get(title, {})
        qid = row.get('pageprops', {}).get('wikibase_item')
        if 'missing' not in row and isinstance(qid, str) and re.fullmatch(r'Q\d+', qid):
            found[original] = (title, qid)
    return found


def usable_title(title):
    """Respect the existing extension's 80-character, public-phrase contract."""
    return (0 < len(title.encode('utf-16-le')) // 2 <= 80
            and any(c.isalnum() for c in title)
            and not re.search(r'[\x00-\x1f\x7f]', title)
            and not re.search(r'^(?:javascript|data|about|chrome|file|ftp|mailto|tel):', title, re.I)
            and not re.search(r'(?:https?:|www\.|[a-z\d._%+-]+@[a-z\d.-]+\.[a-z]{2,}|(?:\b[a-z\d-]+\.)+[a-z]{2,}(?:\b|/))', title, re.I | re.ASCII)
            and '://' not in title)


def merge_catalog(retained, candidates, entities):
    rows = [dict(r) for r in retained]
    titles = {_key(r['topic']) for r in rows}
    ids = {r['wikidata_id'] for r in rows if r.get('wikidata_id')}
    reasons = Counter()
    for candidate in candidates:
        if re.search(r'\bcompanies\b|educational institutions', candidate['subsection'], re.I):
            reasons['excluded_source_section'] += 1; continue
        qid, title = candidate['qid'], candidate['article']
        entity = entities.get(qid)
        if entity is None: raise ValueError(f'Missing fetched Wikidata response for {qid}')
        types = {c.get('mainsnak', {}).get('datavalue', {}).get('value', {}).get('id')
                 for c in entity.get('claims', {}).get('P31', [])}
        if types & EXCLUDED_TYPES:
            reasons['excluded_entity_type'] += 1; continue
        description = entity.get('descriptions', {}).get('en', {}).get('value', '').strip()
        if len(description.split()) < 3:
            reasons['missing_or_short_description'] += 1; continue
        if qid in ids or _key(title) in titles:
            reasons['duplicate_title_or_entity'] += 1; continue
        if not _key(title) or not usable_title(title):
            reasons['invalid_title'] += 1; continue
        rows.append(dict(topic=title, domain=candidate['domain'], description=description,
            source='Wikidata', wikidata_id=qid, source_url=f'https://www.wikidata.org/wiki/{qid}',
            source_revision=entity.get('lastrevid'), wikipedia_url='https://en.wikipedia.org/wiki/'+quote(title.replace(' ', '_'), safe=''),
            list_url='https://en.wikipedia.org/wiki/'+quote(candidate['list_page'].replace(' ', '_'), safe=''),
            list_section=candidate['list_page'].split('Level 5/', 1)[-1],
            list_revision=candidate['list_revision'], subsection=candidate['subsection'],
            selection_source='Wikipedia Vital Articles Level 5'))
        titles.add(_key(title)); ids.add(qid)
    return rows, reasons


class PublicAPI:
    def __init__(self, cache_dir, *, interactive=False):
        self.cache_dir = Path(cache_dir)
        self.interactive = interactive
        self._request_lock = threading.Lock()
        self._next_request = 0.

    @staticmethod
    def validate(data, params):
        if not isinstance(data, dict) or 'error' in data:
            raise ValueError('Source response is not a successful object.')
        if params['action'] == 'parse':
            parsed = data['parse']
            if not isinstance(parsed['title'], str) or not isinstance(parsed['revid'], int) or not isinstance(parsed['wikitext']['*'], str):
                raise ValueError('Incomplete source list snapshot.')
        elif params['action'] == 'query':
            query = data['query']
            pages = query['pages']
            if not isinstance(pages, dict): raise ValueError('Invalid page resolution snapshot.')
            for row in pages.values():
                if not isinstance(row, dict) or not isinstance(row.get('title'), str):
                    raise ValueError('Invalid resolved page record.')
                if 'missing' in row: continue
                if not isinstance(row.get('pageid'), int) or row['pageid'] <= 0:
                    raise ValueError('Incomplete resolved page record.')
                props = row.get('pageprops', {})
                if not isinstance(props, dict) or ('wikibase_item' in props and
                        not isinstance(props['wikibase_item'], str)):
                    raise ValueError('Invalid resolved entity property.')
            aliases = {r['from']: r['to'] for r in query.get('normalized', []) + query.get('redirects', [])}
            found = {r['title'] for r in pages.values()}
            for title in params['titles'].split('|'):
                seen = set()
                while title in aliases and title not in seen:
                    seen.add(title); title = aliases[title]
                if title not in found: raise ValueError('Page resolution snapshot omitted a requested article.')
        elif params['action'] == 'wbgetentities':
            if any(qid not in data['entities'] for qid in params['ids'].split('|')):
                raise ValueError('Entity snapshot omitted a requested ID.')
            for qid in params['ids'].split('|'):
                row = data['entities'][qid]
                if not isinstance(row, dict) or row.get('id') != qid:
                    raise ValueError('Invalid entity record.')
                if 'missing' in row: continue
                if not isinstance(row.get('lastrevid'), int) or row['lastrevid'] <= 0:
                    raise ValueError('Incomplete entity revision information.')
                for field in ('labels', 'descriptions', 'claims'):
                    if not isinstance(row.get(field), dict): raise ValueError('Incomplete entity content.')
                for field in ('labels', 'descriptions'):
                    english = row[field].get('en')
                    if 'en' in row[field] and (not isinstance(english, dict) or not isinstance(english.get('value'), str)):
                        raise ValueError('Invalid English entity text.')
                if any(not isinstance(claims, list) or any(not isinstance(claim, dict) for claim in claims)
                       for claims in row['claims'].values()):
                    raise ValueError('Invalid entity claims.')

    def get(self, endpoint, params):
        identity = json.dumps([endpoint, params], sort_keys=True).encode()
        path = self.cache_dir / (hashlib.sha256(identity).hexdigest()+'.json')
        if path.exists():
            try:
                data = json.loads(path.read_text())
                self.validate(data, params)
                return data
            except (OSError, ValueError, KeyError, TypeError):
                path.unlink(missing_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        for attempt in range(6):
            # Share a modest request budget even when batches use several workers.
            with self._request_lock:
                time.sleep(max(0., self._next_request - time.monotonic()))
                self._next_request = time.monotonic() + .5
            request_params = dict(params, format='json')
            if not self.interactive: request_params['maxlag'] = 5
            response = requests.get(endpoint, params=request_params, timeout=60,
                headers={'User-Agent': 'OtherWise/0.2 (https://github.com/RoboticReaper/OtherWise; public educational interest catalog)'})
            if response.status_code in {429, 500, 502, 503, 504}:
                retry_after = response.headers.get('Retry-After', '0')
                try:
                    delay = float(retry_after)
                except ValueError:
                    try: delay = max(0., parsedate_to_datetime(retry_after).timestamp() - time.time())
                    except (ValueError, TypeError, OverflowError): delay = 5.
                wait = max(2 ** attempt, delay)
                print(f'Source deferred: HTTP {response.status_code}, retry {attempt+1}, wait {wait}s', flush=True)
                time.sleep(wait); continue
            response.raise_for_status()
            data = response.json()
            if data.get('error', {}).get('code') == 'maxlag':
                print(f'Source deferred: maxlag, retry {attempt+1}', flush=True)
                time.sleep(min(30, 2 ** attempt)); continue
            if 'error' in data: raise RuntimeError(f'Source API error: {data["error"]}')
            self.validate(data, params)
            # Claims are needed only to exclude instance types; discard large unrelated claims.
            for entity in data.get('entities', {}).values():
                entity['claims'] = {'P31': entity.get('claims', {}).get('P31', [])}
            atomic_json_write(path, data)
            return data
        raise RuntimeError(f'Public source API did not recover after retries: {params.get("page", params["action"])}. Cached completed batches can be reused on the next run.')


def batches(values, size=50):
    return [values[i:i+size] for i in range(0, len(values), size)]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache-dir', type=Path, default=ROOT / '.cache/catalog-expansion/responses')
    parser.add_argument('--base', type=Path, default=ROOT / 'data/archives/topics_balanced.json')
    parser.add_argument('--output', type=Path, default=ROOT / 'data/topics.json')
    parser.add_argument('--workers', type=int, default=1, choices=range(1, 4))
    parser.add_argument('--interactive', action='store_true', help='Human-waiting import: omit optional maxlag while retaining HTTP rate limits.')
    args = parser.parse_args(argv)
    base_path = args.base if args.base.exists() else args.output
    retained = load_catalog(base_path)
    api = PublicAPI(args.cache_dir, interactive=args.interactive)
    index = api.get(WIKI_API, {'action': 'parse', 'page': LIST_PAGE, 'prop': 'wikitext|revid', 'redirects': 1})
    pages = sorted({link.split('|', 1)[0] for link in re.findall(r'\[\[([^\]]+)\]\]', index['parse']['wikitext']['*'])
                    if link.startswith(LIST_PAGE+'/') and not link.startswith(LIST_PAGE+'/People')})
    if len(pages) < 15: raise ValueError('Vital Articles index did not provide its expected subject sublists.')
    candidates = []
    for page in pages:
        candidates.extend(parse_vital_page(api.get(WIKI_API,
            {'action': 'parse', 'page': page, 'prop': 'wikitext|revid', 'redirects': 1})))
        print(f'Lists: {len(candidates):,} candidates from {page.rsplit("/", 1)[-1]}', flush=True)
    titles = list(dict.fromkeys(r['article'] for r in candidates))
    found = {}
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        def resolve(batch):
            data = api.get(WIKI_API, {'action': 'query', 'titles': '|'.join(batch), 'prop': 'pageprops', 'ppprop': 'wikibase_item', 'redirects': 1})
            return resolve_page_items(data, batch)
        for i, response in enumerate(pool.map(resolve, batches(titles))):
            found.update(response)
            if i % 25 == 0: print(f'Wikipedia IDs: {min((i+1)*50, len(titles)):,}/{len(titles):,}', flush=True)
    resolved = [dict(row, article=found[row['article']][0], qid=found[row['article']][1]) for row in candidates if row['article'] in found]
    qids = sorted({r['qid'] for r in resolved}, key=lambda s: int(s[1:]))
    entities = {}
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        def fetch(batch):
            return api.get(ENTITY_API, {'action': 'wbgetentities', 'ids': '|'.join(batch),
                'props': 'labels|descriptions|claims|info', 'languages': 'en'})['entities']
        for i, response in enumerate(pool.map(fetch, batches(qids))):
            entities.update(response)
            if i % 25 == 0: print(f'Wikidata descriptions: {min((i+1)*50, len(qids)):,}/{len(qids):,}', flush=True)
    rows, reasons = merge_catalog(retained, resolved, entities)
    if len(rows) < len(retained) + 1000: raise ValueError('Import did not produce a substantial validated expansion; existing catalog was left intact.')
    metadata = dict(snapshot_date=datetime.now(ZoneInfo('America/Chicago')).date().isoformat(), topic_count=len(rows),
        domain_count=len({r['domain'] for r in rows}), domain_cap=None,
        domains=dict(sorted(Counter(r['domain'] for r in rows).items())), source_counts=dict(Counter(r['source'] for r in rows)),
        retained_count=len(retained), added_count=len(rows)-len(retained), list_url=LIST_URL,
        source_item_count=len(qids), list_entry_count=len(candidates), unresolved_article_count=len(titles)-len(found),
        filtering_counts=dict(reasons), list_revisions={page: next((r['list_revision'] for r in candidates if r['list_page']==page), None) for page in pages},
        selection='Preserve the balanced catalog; import non-People Vital Articles Level 5 sublists, excluding listed entity types and short descriptions; deduplicate normalized titles and Wikidata IDs. No domain truncation.',
        licenses={'Wikidata labels and descriptions': 'CC0', 'Wikipedia and Wikimedia list selection/structure': 'CC BY-SA 4.0'},
        caveat='Article counts and entity counts are not usable topic counts. Direct P31 filters do not cover every subtype; related concepts and some individual works may remain. English Wikipedia selection is not culturally neutral.')
    # Archive the previous inputs so rebuilding never uses its own expanded output.
    if not args.base.exists(): atomic_json_write(args.base, retained)
    atomic_json_write(args.output, rows, indent=2)
    atomic_json_write(args.output.parent / 'catalog_metadata.json', metadata, indent=2)
    load_catalog(args.output)
    print(json.dumps(metadata, ensure_ascii=False, indent=2), flush=True)


if __name__ == '__main__': main()
