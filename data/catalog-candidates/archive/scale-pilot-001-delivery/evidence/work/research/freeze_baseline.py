"""Freeze canonical identity mappings and all current candidate provenance.

Read-only inputs. Uses the inspected Inventory class in an isolated namespace,
with its two pure lookup dependencies rather than importing runtime models.
"""
import ast
import hashlib
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUTS = ROOT.parent / 'inputs/unpacked'
PILOT = ROOT / 'data/catalog-candidates/scale-pilot-001'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def dump(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + '\n')

def key(text):
    return re.sub(r'[\s_\-\u2010-\u2015]+', ' ', text.strip().casefold()).strip()

def freeze():
    plan = json.loads((PILOT/'coverage-plan.json').read_text())
    checked = []
    for spec in plan['baseline_inputs']:
        p = INPUTS/spec['path']
        actual = sha(p)
        checked.append(dict(spec, actual_sha256=actual, matches_preparation=actual == spec['sha256'], size_bytes=p.stat().st_size))
    assert all(x['matches_preparation'] for x in checked), 'Baseline changed: reconcile before selection.'
    broad = json.loads((INPUTS/'data/topics.json').read_text())
    graph = json.loads((INPUTS/'data/discovery_graph.json').read_text())
    registry = json.loads((INPUTS/'data/recommendation-identities.json').read_text())
    # This exact class was fully inspected; do not import graph_explorer's runtime.
    tree = ast.parse((INPUTS/'recommendation_lab/inventory.py').read_text())
    selected = ast.Module(body=[n for n in tree.body if isinstance(n,(ast.ClassDef, ast.FunctionDef)) and n.name in {'digest','InventoryConflict','Inventory'}], type_ignores=[])
    env = dict(hashlib=hashlib, json=json, defaultdict=defaultdict, _key=key, graph_concepts=lambda g:[n for n in g['nodes'] if n['kind']=='concept'])
    exec(compile(selected, str(INPUTS/'recommendation_lab/inventory.py'), 'exec'),env)
    inv=env['Inventory'].from_sources(broad, graph, registry)
    assert inv.version == plan['baseline_inventory_fingerprint']
    concepts={}
    for cid,c in inv.concepts.items():
        concepts[cid] = dict(id=cid, label=c['topic'], aliases=sorted(c['aliases']), original_description=c['description'], inventory_records=c['records'], candidate_records=[], domains=[])
        for rec in c['records']:
            if rec['kind']=='broad':
                d=broad[rec['index']].get('domain')
                if d and d not in concepts[cid]['domains']: concepts[cid]['domains'].append(d)
    revisions=[]
    for bid in ['research-batch-001','research-batch-002']:
        path=INPUTS/f'data/catalog-candidates/{bid}.json'
        data=json.loads(path.read_text())
        revisions.append(dict(batch_id=bid, revision=data['batch'].get('revision',1), path=f'../inputs/unpacked/data/catalog-candidates/{bid}.json', sha256=sha(path), concepts=len(data['concepts']), sources=len(data['sources'])))
        for card in data['concepts']:
            cid=card['id']
            base=concepts.setdefault(cid,dict(id=cid,label=card['label'],aliases=[],original_description=card['original_description'],inventory_records=[],candidate_records=[],domains=[]))
            base['aliases']=sorted(set(base['aliases'])|set(card['aliases'])|{card['label']})
            base['candidate_records'].append(dict(batch_id=bid,batch_revision=data['batch'].get('revision',1),record=card))
            base['domains']=sorted(set(base['domains'])|set(card['domains']))
            base['latest_card_version']=card['card_version']
            base['latest_candidate_batch']=bid
    aliases=defaultdict(list)
    for cid,c in concepts.items():
        for label in [c['label'],*c['aliases']]:
            k=key(label)
            if cid not in aliases[k]: aliases[k].append(cid)
    for ids in aliases.values(): ids.sort()
    assert len(concepts)==plan['baseline_identity_count_by_id'],len(concepts)
    index=dict(schema_version=1,pilot_id=plan['pilot_id'],inventory_fingerprint=inv.version,concepts=concepts,aliases=dict(aliases))
    dump(PILOT/'baseline-index.json',index)
    dump(PILOT/'baseline-manifest.json',dict(schema_version=1,pilot_id=plan['pilot_id'],frozen_at=datetime.now(timezone.utc).isoformat(),inputs=checked,active_candidate_revisions=revisions,inventory_identity_count=len(inv.concepts),baseline_identity_count_by_id=len(concepts),baseline_index_sha256=sha(PILOT/'baseline-index.json'),baseline_inventory_fingerprint=inv.version,archived_copies_counted=False,archived_provenance_path='../inputs/unpacked/data/catalog-candidates/archive/research-batch-002',selection_inputs='Public reference material and pinned identity baseline only; no private ratings or held-out judgments.',status='frozen'))
    print(json.dumps(dict(inventory_identities=len(inv.concepts),baseline_identities=len(concepts),aliases=len(aliases),fingerprints_match=True,baseline_index_sha256=sha(PILOT/'baseline-index.json'))))

if __name__=='__main__': freeze()
