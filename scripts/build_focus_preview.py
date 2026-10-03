"""Record public-only Focus batches using the real cached 768-D catalog vectors."""
import json
import sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from explorer import load_catalog
from service.engine import RecommendationEngine

class NoEncoding:
    def encode(self, *args, **kwargs):
        raise RuntimeError('Preview generation requires existing public vectors; no model download or encoding.')

metadata = json.loads((ROOT / 'data/galaxy-layout.json').read_text())['metadata']
raw = np.load(ROOT / '.cache/embeddings' / (metadata['embedding']['identity'] + '.npy'), allow_pickle=False)
engine = RecommendationEngine(topics=load_catalog(ROOT / 'data/topics.json'), model=NoEncoding(), topic_vectors=raw, model_name=metadata['model'])
engine.initialize()
identity = {k: metadata[k] for k in ('catalog_sha256', 'model')}
identity['embedding'] = {k: metadata['embedding'][k] for k in ('sha256', 'dtype', 'shape')}
assert engine.focus_identity() == identity
options = dict(limit=10, radius=.28, expansion=.07, overlap=.015, diversity=.2, max_overlap_fraction=.2, randomness=.03)
batches = []
for seed in ('Gardening', 'Computer science', 'psychology'):
    request = dict(topic_id=seed, **identity, **options)
    envelope = engine.recommend_focus(seed, expected_identity=identity, **options)
    batches.append(dict(request=request, envelope=envelope))
result = dict(fixture_version=1, provenance=dict(kind='recorded-public-catalog-focus', generator='scripts/build_focus_preview.py', explanation='Real RecommendationEngine output from the original cached all-mpnet-base-v2 catalog embeddings. Public topics only; no personal state. Recorded sampling is fixed in this file; Refresh reopens the same recorded batch offline.', distance='acos(clamp(cosine,-1,1))/pi', identity=identity), batches=batches)
path = ROOT / 'extension/focus-preview.v1.json'
path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(f'Recorded {len(batches)} public Focus batches in {path}')
