import json,hashlib,re,sys,datetime
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
ROOT=Path(__file__).resolve().parents[2]
BPATH=ROOT/'data/catalog-candidates/scale-pilot-001/baseline-index.json'
base=json.loads(BPATH.read_text()); bid=list(base['concepts']); rows=[base['concepts'][i] for i in bid]
def txt(r):
 cs=[x.get('record',x) for x in r.get('candidate_records',[])]
 return (r.get('label','')+' ')*3+' '.join(r.get('aliases',[]))+' '+(r.get('original_description') or '')+' '+' '.join(c.get('learning_takeaway','')+' '+c.get('card','') for c in cs)
base_text=[txt(r) for r in rows]
word=TfidfVectorizer(stop_words='english',ngram_range=(1,2),sublinear_tf=True).fit(base_text)
mat=word.transform(base_text)
char=TfidfVectorizer(analyzer='char_wb',ngram_range=(3,5),sublinear_tf=True).fit([r['label'] for r in rows])
cmat=char.transform([r['label'] for r in rows])
for batch in sys.argv[1:]:
 ppath=ROOT/f'research/workers/research-batch-{batch}/selection.proposed.json'; data=json.loads(ppath.read_text()); out=[]
 for n,p in enumerate(data['proposals'],1):
  q=p['label']+' '+p['label']+' '+' '.join(p.get('aliases',[]))+' '+p.get('learning_takeaway','')
  w=(word.transform([q])@mat.T).toarray()[0]; c=(char.transform([p['label']])@cmat.T).toarray()[0]
  scores=0.65*w+0.35*c; inds=set(scores.argsort()[-7:])|set(w.argsort()[-4:])|set(c.argsort()[-3:]); inds=sorted(inds,key=lambda k:scores[k],reverse=True)
  top=[{'id':bid[i],'label':rows[i]['label'],'description':rows[i].get('original_description'),'score':round(float(scores[i]),4),'word_score':round(float(w[i]),4),'label_score':round(float(c[i]),4)} for i in inds]
  out.append({'ordinal':n,'proposal_id':p['provisional_id'],'label':p['label'],'inventory_status':p.get('inventory_status'),'selection_status':p.get('selection_status'), 'baseline_id_reused':p['provisional_id'] in base['concepts'],'diagnostic_matches':top})
 result={'generated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'baseline_sha256':hashlib.sha256(BPATH.read_bytes()).hexdigest(),'selection_sha256':hashlib.sha256(ppath.read_bytes()).hexdigest(),'limitations':'Lexical diagnostics only. Scores neither prove novelty nor establish equivalence. Human semantic review must inspect concrete subject meaning.','records':out}
 (ROOT/f'research/identity-review/batch-{batch}-diagnostics.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
 print(batch,result['selection_sha256'],len(out))
