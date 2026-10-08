"""Reproducible public experiments, bounded tuning, and one-use held-out cycles."""
from __future__ import annotations

import hashlib
import json
import re
import tempfile
import os
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from explorer import MODEL_NAME, ROOT, _unit_vectors, load_catalog, topic_texts
from graph_explorer import load_graph, graph_concepts
from .inventory import Inventory, digest
from .systems import RecommendationLab, Request, RankConfig
from .evaluation import METRICS, score_batch, scoreboard

REVISION = 'e8c3b32edf5434bc2275fc9bab85f82640a19130'


def write_json(path, value, *, exclusive=False):
    path = Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w',dir=path.parent,suffix='.tmp',delete=False,encoding='utf-8') as stream:
            temporary = Path(stream.name)
            json.dump(value,stream,indent=2,ensure_ascii=False,allow_nan=False)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        if exclusive:
            os.link(temporary,path)  # Atomic, complete publication; never overwrite a winner.
        else:
            temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def cache_identity(texts, model_identity):
    return digest(dict(texts=texts,model_identity=model_identity,cache_schema=1))


def validate_profiles(profiles):
    ids, families = set(), {}
    if not profiles:
        raise ValueError('A benchmark needs profiles.')
    for profile in profiles:
        if profile['id'] in ids or profile['split'] not in ('development','heldout'):
            raise ValueError('Invalid profile ID or split.')
        ids.add(profile['id'])
        family, split = profile['family'],profile['split']
        if family in families and families[family] != split:
            raise ValueError('A profile family cannot cross benchmark splits.')
        families[family] = split


@dataclass(frozen=True)
class SearchBudget:
    rounds: int = 5
    per_round: int = 20
    patience: int = 2
    min_gain: float = .01

    def validate(self):
        if any(type(v) is not int or v < 1 for v in (self.rounds,self.per_round,self.patience)) or self.rounds > 5 or self.per_round > 20:
            raise ValueError('Search is limited to five rounds and twenty configurations per round.')
        if not isinstance(self.min_gain,(float,int)) or isinstance(self.min_gain,bool) or not np.isfinite(self.min_gain) or self.min_gain < 0:
            raise ValueError('Invalid minimum gain.')


def bounded_search(configs, profiles, evaluate, budget=None):
    budget = budget or SearchBudget()
    budget.validate()
    if not profiles or any(p['split'] != 'development' for p in profiles):
        raise ValueError('Tuning accepts development profiles only.')
    champions, best = dict.fromkeys(METRICS), dict.fromkeys(METRICS,float('-inf'))
    attempts, stale, stop = [], 0, 'exhausted'
    limit = min(len(configs),budget.rounds*budget.per_round)
    for start in range(0,limit,budget.per_round):
        prior = dict(best)
        for config in configs[start:min(start+budget.per_round,limit)]:
            scores = evaluate(config,profiles)
            attempts.append(dict(config=config,scores=scores))
            # An incomplete cross-metric evaluation cannot nominate a champion.
            if any(scores.get(k) is None for k in METRICS):
                continue
            for metric in METRICS:
                if scores[metric] > best[metric]:
                    best[metric],champions[metric] = scores[metric],config
        gained = any(best[k] > prior[k] and (prior[k] == float('-inf') or best[k]-prior[k] >= budget.min_gain) for k in METRICS)
        stale = 0 if gained else stale+1
        if stale >= budget.patience:
            stop = 'patience'
            break
    else:
        if len(configs) > limit:
            stop = 'budget'
    return dict(attempts=attempts,champions=champions,best={k:(v if np.isfinite(v) else None) for k,v in best.items()},stop_reason=stop)


def seal_finalists(directory, champions, identity):
    path = Path(directory)/'nomination.json'
    body = dict(champions=champions,identity=identity)
    nomination = dict(**body,digest=digest(body))
    path.parent.mkdir(parents=True,exist_ok=True)
    try:
        write_json(path,nomination,exclusive=True)
    except FileExistsError:
        if json.loads(path.read_text()) != nomination:
            raise ValueError('Finalists are frozen; create a fresh cycle with new held-out families.')
    return nomination


def claim_heldout(directory, nomination):
    path = Path(directory)/'heldout-receipt.json'
    body = {k:nomination[k] for k in ('champions','identity')}
    saved = Path(directory)/'nomination.json'
    if digest(body) != nomination.get('digest') or not saved.exists() or json.loads(saved.read_text()) != nomination:
        raise ValueError('Unrecognized finalist nomination.')
    receipt = dict(nomination_digest=nomination['digest'],status='claimed',policy='One held-out run; reused cases become history before another tuning cycle.')
    path.parent.mkdir(parents=True,exist_ok=True)
    try:
        write_json(path,receipt,exclusive=True)
    except FileExistsError as error:
        raise ValueError('Held-out split already claimed in this cycle.') from error
    return receipt


def evaluation_space(texts, *, dimensions=2048):
    """A frozen TF-IDF space independent of serving embeddings, not a semantic judge."""
    tokens = {cid:re.findall(r'\w+',text.casefold()) for cid,text in texts.items()}
    df = {}
    for words in tokens.values():
        for word in set(words):
            df[word] = df.get(word,0)+1
    vectors = {}
    for cid,words in tokens.items():
        vector = np.zeros(dimensions,dtype=np.float32)
        for word in words:
            index = int.from_bytes(hashlib.blake2b(word.encode(),digest_size=8).digest(),'big') % dimensions
            vector[index] += math_idf(len(tokens),df[word])
        if not np.any(vector):
            vector[0] = 1
        vectors[cid] = vector/np.linalg.norm(vector)
    identity = dict(method='hashed-tfidf-v1',dimensions=dimensions,texts_sha256=digest(texts),
                    tokenization='unicode-word-casefold',idf='log((1+n)/(1+df))+1',hash='blake2b-64',normalization='l2')
    return vectors,identity


def math_idf(n,df):
    return float(np.log((1+n)/(1+df))+1)


def load_runtime():
    """Offline only: pinned model plus revision-aware caches; never fetch a model."""
    import torch
    import sentence_transformers
    from sentence_transformers import SentenceTransformer
    snapshot = ROOT/'.cache/models/models--sentence-transformers--all-mpnet-base-v2/snapshots'/REVISION
    if not snapshot.is_dir():
        raise RuntimeError(f'Pinned local model is absent: {snapshot}. Install the existing model before running experiments.')
    torch.set_num_threads(4)
    torch.use_deterministic_algorithms(True)
    model = SentenceTransformer(str(snapshot),device='cpu',local_files_only=True)
    broad,graph = load_catalog(),load_graph()
    registry = json.loads((ROOT/'data/recommendation-identities.json').read_text())
    inventory = Inventory.from_sources(broad,graph,registry)
    identity = dict(name=MODEL_NAME,revision=REVISION,device='cpu',normalize_embeddings=True,
                    precision='float32',batch_size=64,max_seq_length=model.max_seq_length,
                    torch=torch.__version__,sentence_transformers=sentence_transformers.__version__)
    audit = json.loads((ROOT/'experiments/recommendation-audit/results.json').read_text()) if (ROOT/'experiments/recommendation-audit/results.json').exists() else {}
    source_hashes = {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ('data/topics.json','data/discovery_graph.json')}
    verified_audit = audit.get('model_snapshot') == REVISION and audit.get('public_source_sha256') == source_hashes
    migration = []
    def public_vectors(rows,kind,old_prefix=''):
        texts = topic_texts(rows)
        contract = dict(**identity,inventory_version=inventory.version,source_kind=kind)
        key = cache_identity(texts,contract)
        path = ROOT/'.cache/recommendation-lab'/f'{key}.npy'
        expected = (len(rows),model.get_embedding_dimension())
        if path.exists():
            values = np.load(path,allow_pickle=False)
            if values.shape == expected:
                return _unit_vectors(values,'Public experiment cache')
        old_key = hashlib.sha256(json.dumps(dict(model=MODEL_NAME,texts=texts),sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        old = ROOT/'.cache/embeddings'/f'{old_prefix}{old_key}.npy'
        old_sha = hashlib.sha256(old.read_bytes()).hexdigest() if old.is_file() else None
        if verified_audit and old_sha in audit.get('embedding_cache_sha256',{}).values():
            values = np.load(old,allow_pickle=False)
            migration.append(dict(kind=kind,verified_audit_sha256=old_sha,new_cache_key=key))
        else:
            values = model.encode(texts,batch_size=64,show_progress_bar=False,convert_to_numpy=True,normalize_embeddings=True)
        if values.shape != expected:
            raise ValueError('Public embedding cache shape mismatch.')
        path.parent.mkdir(parents=True,exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=path.parent,suffix='.tmp',delete=False) as stream:
                temporary = Path(stream.name)
                np.save(stream,values,allow_pickle=False)
            temporary.replace(path)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
        return _unit_vectors(values,'Public embeddings')
    bv = public_vectors(broad,'broad')
    cv = public_vectors(graph_concepts(graph),'specific','discovery-')
    av = public_vectors(graph['areas'],'areas','discovery-')
    lab = RecommendationLab(inventory,broad,graph,model,bv,cv,av,model_identity=identity)
    vectors,eval_identity = evaluation_space({cid:inventory.text(cid) for cid in inventory.concepts})
    runtime = dict(model=identity,inventory_version=inventory.version,public_sources=source_hashes,
                   vectors_sha256={kind:hashlib.sha256(np.ascontiguousarray(values).tobytes()).hexdigest() for kind,values in [('broad',bv),('specific',cv),('areas',av)]},
                   cache_migrations=migration,evaluation_embedding=eval_identity)
    return lab,vectors,runtime


def run_cases(lab, profiles, systems):
    runs = []
    for profile in profiles:
        controls = profile.get('controls',{})
        feedback = {cid:dict(known=True) for cid in profile.get('known_ids',[])}
        request = Request(profile['interests'],inventory_version=lab.inventory.version,feedback=feedback,**controls)
        for system in systems:
            config = RankConfig(**system.get('config',{}))
            first = lab.recommend(request,system['variant'],config)
            warm = lab.recommend(request,system['variant'],config)
            if first['recommendations'] != warm['recommendations']:
                raise ValueError('Seeded outputs changed between first and warm requests.')
            warm['execution']['first_request_seconds'] = first['execution']['seconds']
            runs.append(dict(system=system['name'],profile=profile,batch=warm))
    return runs


def evaluate_runs(runs, store, vectors, *, inventory=None):
    records = []
    for run in runs:
        if not run['profile'].get('quality',True):
            continue
        records.append(dict(system=run['system'],profile_id=run['profile']['id'],family=run['profile']['family'],
            scores=score_batch(run['profile'],run['batch'],store,vectors,limit=run['profile'].get('controls',{}).get('limit',10),inventory=inventory),
            seconds=run['batch']['execution']['seconds'],cost_usd=run['batch']['execution']['serving_cost_usd']))
    return records,scoreboard(records)


def paired_uncertainty(records, champions, *, baseline='V0',seed=42,draws=2000):
    by_system = {}
    for row in records:
        by_system.setdefault(row['system'],{})[row['profile_id']] = row
    result = {}
    rng = np.random.default_rng(seed)
    for metric,champion in champions.items():
        if champion not in by_system or baseline not in by_system:
            continue
        keys = sorted(set(by_system[champion]) & set(by_system[baseline]))
        pairs = {k:by_system[champion][k]['scores'][metric]-by_system[baseline][k]['scores'][metric] for k in keys
                  if by_system[champion][k]['scores'][metric] is not None and by_system[baseline][k]['scores'][metric] is not None}
        if not pairs:
            continue
        families = {}
        for key,delta in pairs.items():
            families.setdefault(by_system[champion][key].get('family',key),[]).append(delta)
        clusters = list(families.values())
        samples = rng.integers(0,len(clusters),size=(draws,len(clusters)))
        boot = [float(np.mean([delta for i in sample for delta in clusters[i]])) for sample in samples]
        result[metric] = dict(champion=champion,baseline=baseline,profile_deltas=pairs,
                             mean_gain=float(np.mean(list(pairs.values()))),bootstrap_95=[float(np.percentile(boot,2.5)),float(np.percentile(boot,97.5))],
                             independent_families=len(families),note='Family cluster bootstrap; small synthetic benchmark, not user satisfaction.')
    return result
