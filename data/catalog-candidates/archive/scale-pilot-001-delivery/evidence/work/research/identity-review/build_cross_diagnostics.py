from pathlib import Path
import json,hashlib,re,unicodedata,datetime,collections
from sklearn.feature_extraction.text import TfidfVectorizer
R=Path(__file__).resolve().parents[2]; O=R/'research/identity-review'
def norm(s):return re.sub(r'[^a-z0-9]+',' ',unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()).strip()
def accepted(p):
 s=p.get('recommendation',p.get('proposal_status',p.get('selection_status')))
 return s in ['accept','recommended','proposed_accept','proposed','proposed_for_acceptance']
rows=[];inputs=[]
for p in sorted((R/'research/workers').glob('*/selection.proposed.json')):
 d=json.loads(p.read_text());inputs.append({'batch_id':d['batch_id'],'path':str(p.relative_to(R)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'completed_at':d.get('completed_at'),'proposals':len(d['proposals'])})
 for ordinal,x in enumerate(d['proposals'],1):
  if accepted(x):
   y=dict(x);y['batch_id']=d['batch_id'];y['ordinal']=ordinal;y['effective_id']=y.get('suggested_id',y['provisional_id']);rows.append(y)
# Apply only explicit recorded coordinator corrections, keeping untouched source proposals pinned.
correction_path=R/'data/catalog-candidates/scale-pilot-001/selection-corrections.json'
corrections=json.loads(correction_path.read_text())['corrections'] if correction_path.exists() else []
for c in corrections:
 if c['action']=='reuse_existing_identity':
  for r in rows:
   if r['batch_id']==c['batch_id'] and r['provisional_id']==c['provisional_id']:r['effective_id']=c['reserved_id'];r['inventory_status']='existing_control'
 elif c['action']=='quarantine_and_promote_reserve':
  rows=[r for r in rows if not (r['batch_id']==c['batch_id'] and r['provisional_id']==c['provisional_id'])]
  if not any(r['batch_id']==c['batch_id'] and r['effective_id']==c['replacement_id'] for r in rows):
   f=R/f"research/workers/{c['batch_id']}/selection.proposed.json"; d=json.loads(f.read_text());
   for ordinal,x in enumerate(d['proposals'],1):
    if x.get('suggested_id',x['provisional_id'])==c['replacement_id']:
     y=dict(x);y.update(batch_id=c['batch_id'],ordinal=ordinal,effective_id=c['replacement_id']);rows.append(y)
txt=[(r['label']+' ')*2+' '.join(r.get('aliases',[]))+' '+r.get('learning_takeaway','') for r in rows]
v=TfidfVectorizer(stop_words='english',ngram_range=(1,2),sublinear_tf=True);m=v.fit_transform(txt);w=(m@m.T).toarray()
v=TfidfVectorizer(analyzer='char_wb',ngram_range=(3,5));m=v.fit_transform([r['label'] for r in rows]);ch=(m@m.T).toarray();score=.65*w+.35*ch
seen={};pairs=[]
for i,r in enumerate(rows):
 inds=[int(j) for j in score[i].argsort()[::-1] if j!=i and rows[j]['batch_id']!=r['batch_id']][:4]
 for j in inds:
  if score[i,j]<.15:continue
  a,b=sorted([i,j]);seen[(a,b)]=float(score[a,b])
for (i,j),s in sorted(seen.items(),key=lambda z:-z[1]):
 a,b=rows[i],rows[j];pairs.append({'left':{k:a.get(k) for k in ['batch_id','ordinal','effective_id','label','learning_takeaway']},'right':{k:b.get(k) for k in ['batch_id','ordinal','effective_id','label','learning_takeaway']},'score':round(s,4),'word_score':round(float(w[i,j]),4),'label_score':round(float(ch[i,j]),4)})
ids=collections.defaultdict(list);names=collections.defaultdict(list)
for r in rows:
 ids[r['effective_id']].append([r['batch_id'],r['label']])
 for s in set([r['label']]+r.get('aliases',[])):names[norm(s)].append({'batch':r['batch_id'],'id':r['effective_id'],'label':r['label'],'matched_phrase':s})
out={'schema_version':1,'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'diagnostic_only_not_final_admission','inputs':inputs,'corrections_sha256':hashlib.sha256(correction_path.read_bytes()).hexdigest() if correction_path.exists() else None,'selected_counts':dict(collections.Counter(x['batch_id'] for x in rows)),'same_id_cross_batch':{k:v for k,v in ids.items() if len({z[0] for z in v})>1},'shared_names_cross_batch':{k:v for k,v in names.items() if len({z['batch'] for z in v})>1},'ranked_cross_batch_pairs':pairs,'limitations':'Only diagnostic retrieval, never automatic merging or proof of distinctness. Provisional batches may change.'}
(O/'cross-batch-diagnostics.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print('COUNTS',out['selected_counts'],'SAME IDS',out['same_id_cross_batch'],'ALIASES',out['shared_names_cross_batch'],'PAIR COUNT',len(pairs))
for p in pairs:
 a,b=p['left'],p['right'];print(p['score'],a['batch_id'][-3:],a['ordinal'],a['label'],'|',b['batch_id'][-3:],b['ordinal'],b['label'])
