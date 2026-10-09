"""Bounded label/alias/description lookup; ranking is diagnostic, not equivalence."""
import json, re, sys, difflib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
B=json.loads((ROOT/'data/catalog-candidates/scale-pilot-001/baseline-index.json').read_text())
def key(s): return re.sub(r'[\s_\-\u2010-\u2015]+',' ',s.strip().casefold())
def search(q,limit=8):
    k=key(q); words=set(re.findall(r'\w+',k)); results=[]
    for cid,c in B['concepts'].items():
        labels=[c['label'],*c['aliases']]
        exact=any(key(s)==k for s in labels)
        score=max(difflib.SequenceMatcher(None,k,key(s)).ratio() for s in labels)
        overlap=max(len(words&set(re.findall(r'\w+',key(s))))/max(1,len(words)) for s in labels)
        if exact or overlap or score>.57:
            results.append((exact,overlap,score,c))
    results.sort(key=lambda x:(-x[0],-x[1],-x[2],x[3]['id']))
    return [dict(id=c['id'],label=c['label'],aliases=c['aliases'],description=c['original_description'],domains=c['domains'],exact_label_match=exact,lexical_score=round(score,3),latest_card_version=c.get('latest_card_version'),latest_candidate_batch=c.get('latest_candidate_batch'),candidate_takeaways=[r['record']['learning_takeaway'] for r in c['candidate_records']]) for exact,overlap,score,c in results[:limit]]
if __name__=='__main__':
    for q in sys.argv[1:]: print(json.dumps(dict(query=q,matches=search(q)),ensure_ascii=False))
