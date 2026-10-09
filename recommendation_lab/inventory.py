"""Identity and interpretation. Labels never establish equivalence by themselves."""
from __future__ import annotations

import hashlib
import json
from collections import defaultdict

from explorer import _key
from graph_explorer import graph_concepts


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(',', ':'), allow_nan=False).encode()).hexdigest()


class InventoryConflict(ValueError):
    """A submitted meaning was offered by another inventory revision."""


class Inventory:
    @classmethod
    def from_sources(cls, broad, graph, registry=None):
        self = cls()
        registry = registry or {}
        self.version = digest(dict(broad=broad, graph=graph, registry=registry))
        self.concepts = {}
        self.aliases = defaultdict(set)
        self.source_ids = {'broad': [], 'specific': []}
        overrides, evidence = {}, {}
        for mapping in registry.get('equivalences', []):
            if not mapping.get('evidence'):
                raise ValueError('Reviewed equivalences need evidence.')
            overrides[mapping['kind'], mapping['index']] = mapping['id']
            evidence[mapping['kind'], mapping['index']] = mapping['evidence']

        def add(concept_id, row, kind, index):
            if not all(isinstance(row.get(k), str) and row[k].strip() for k in ('topic', 'description')):
                raise ValueError('Concepts need labels and descriptions.')
            concept = self.concepts.setdefault(concept_id, dict(id=concept_id, records=[], aliases=set()))
            source = row.get('source', row.get('description_source', 'ProductSpace'))
            record = dict(kind=kind, index=index, topic=row['topic'], description=row['description'],
                          source=source, source_url=row.get('source_url', ''),
                          source_revision=row.get('source_revision'), source_id=row.get('id', concept_id))
            # Authored provenance is a repository record, not an invented web citation.
            if not record['source_url']:
                record['source_url'] = (f"https://www.wikidata.org/wiki/{row['wikidata_id']}" if row.get('wikidata_id')
                    else f'data/topics.json#record-{index}' if kind == 'broad' else f'data/discovery_graph.json#concept-{index}')
            if (kind,index) in evidence:
                record['equivalence_evidence'] = evidence[kind,index]
            concept['records'].append(record)
            concept['aliases'].update([row['topic'], *row.get('aliases', [])])

        for kind, rows in [('broad', broad), ('specific', graph_concepts(graph))]:
            for index, row in enumerate(rows):
                locator = f'{kind}:{index}'
                concept_id = overrides.get((kind, index), row.get('wikidata_id') or row.get('concept_id')
                    or (row.get('id') if kind == 'specific' else None)
                    or registry.get('local_ids', {}).get(locator, f'local:authored:{index:06d}'))
                self.source_ids[kind].append(concept_id)
                add(concept_id, row, kind, index)
        for index, row in enumerate(registry.get('resolver_concepts', [])):
            add(row['id'], row, 'resolver', index)
        for concept_id, aliases in registry.get('aliases', {}).items():
            if concept_id not in self.concepts:
                raise ValueError(f'Alias references unknown concept {concept_id}.')
            self.concepts[concept_id]['aliases'].update(aliases)
        for concept in self.concepts.values():
            # Resolver records offer disambiguated labels; otherwise use the broad record,
            # consistently in both presentation kinds. Preserve all other descriptions.
            record = min(concept['records'], key=lambda r: ({'resolver': 0, 'broad': 1, 'specific': 2}[r['kind']], r['index']))
            concept.update(topic=record['topic'], description=record['description'],
                           source_url=record['source_url'])
            for alias in concept['aliases']:
                self.aliases[_key(alias)].add(concept['id'])
        return self

    def text(self, concept_id):
        concept = self.concepts[concept_id]
        return f"{concept['topic']}: {concept['description']}"

    def choice(self, concept_id):
        concept = self.concepts[concept_id]
        return {k: concept[k] for k in ('id', 'topic', 'description', 'source_url')}

    def resolve(self, interests, *, inventory_version=None, allow_repeated=False):
        if not isinstance(interests, list) or not 1 <= len(interests) <= 40:
            raise ValueError('Provide 1–40 interest records.')
        parsed = []
        for value in interests:
            record = {'phrase': value} if isinstance(value, str) else value
            if not isinstance(record, dict) or set(record) - {'phrase', 'concept_id'}:
                raise ValueError('Invalid interest record.')
            phrase = record.get('phrase')
            if not isinstance(phrase, str) or not 1 <= len(phrase.strip()) <= 120 or not _key(phrase) or any(ord(c) < 32 for c in phrase):
                raise ValueError('Interest phrases must be nonempty bounded text.')
            parsed.append(dict(record, phrase=phrase.strip()))
        if any(p.get('concept_id') is not None for p in parsed) and inventory_version != self.version:
            raise InventoryConflict('Meaning choices require the current inventory version.')
        result, seen = [], set()
        for i, record in enumerate(parsed):
            phrase, selected = record['phrase'], record.get('concept_id')
            offered = self.aliases.get(_key(phrase), set())
            context = set(_key(' '.join(p['phrase'] for j,p in enumerate(parsed) if i != j)).split())
            choices = sorted(offered,key=lambda cid:(-len(context & set(_key(self.text(cid)).split())),cid))[:5]
            if selected is not None and (not isinstance(selected, str) or selected not in choices):
                raise ValueError('Selected meaning was not offered for this phrase.')
            concept_id = selected or (next(iter(offered)) if len(offered) == 1 else None)
            identity = concept_id or f'phrase:{_key(phrase)}'
            if identity in seen and not allow_repeated:
                raise ValueError('Duplicate interest identity.')
            seen.add(identity)
            if concept_id:
                result.append(dict(phrase=phrase, status='resolved', concept_id=concept_id,
                                   text=self.text(concept_id), choices=[]))
            elif offered:
                # This transparent lexical contextual ordering is NOT calibrated confidence.
                result.append(dict(phrase=phrase, status='clarification_needed', concept_id=None,
                                   text=None, choices=[self.choice(cid) for cid in choices],
                                   ordering='context word overlap; no automatic sense selection'))
            else:
                result.append(dict(phrase=phrase, status='unresolved_phrase', concept_id=None,
                                   text=phrase, choices=[]))
        return result
