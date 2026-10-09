import json,hashlib,collections,re,unicodedata,datetime
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
R=Path(__file__).resolve().parents[2];O=R/'research/identity-review'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
canon=lambda v:json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
textnorm=lambda s:' '.join(unicodedata.normalize('NFC',s).split()) if isinstance(s,str) else s
bp=R/'data/catalog-candidates/scale-pilot-001/baseline-index.json';mp=R/'data/catalog-candidates/scale-pilot-001/selection-manifest.json'
b=json.loads(bp.read_text())['concepts'];m=json.loads(mp.read_text());assign={x['id']:x for x in m['accepted']}
rows=[];inputs=[];failures=[];diffs=[]
for p in sorted((R/'data/catalog-candidates').glob('research-batch-00[3-7].json')):
 d=json.loads(p.read_text());bid=d['batch']['id'];batchrows=[]
 for c in d['concepts']:
  a=assign.get(c['id']);
  if a is None:failures.append({'id':c['id'],'error':'no central assignment'});continue
  for key in ['scope','entity_kind']:
   if c[key]!=a[key]:failures.append({'id':c['id'],'field':key,'actual':c[key],'manifest':a[key]})
  if a['owner']!=bid:failures.append({'id':c['id'],'error':'owner differs','actual_batch':bid,'manifest_owner':a['owner']})
  if a['primary_domain'] not in c['domains']:failures.append({'id':c['id'],'error':'primary domain missing from card domains'})
  delta={k:{'selected':a.get(k),'actual':c.get(k)} for k in ['label','aliases','learning_takeaway'] if c.get(k)!=a.get(k)}
  if delta:diffs.append({'id':c['id'],'batch_id':bid,'changes':delta})
  r={k:textnorm(c[k]) for k in ['id','label','entity_kind','scope','learning_takeaway','card']}
  r['aliases']=sorted(set(textnorm(x) for x in c['aliases']));r['domains']=sorted(set(c['domains']));r.update(owner=bid,primary_domain=a['primary_domain'],primary_subfield=a['primary_subfield'])
  rows.append(r);batchrows.append(r)
 inputs.append({'batch_id':bid,'path':str(p.relative_to(R)),'sha256':sha(p),'concepts':len(d['concepts']),'semantic_sha256':hashlib.sha256(canon(sorted(batchrows,key=lambda r:r['id']))).hexdigest()})
rows.sort(key=lambda r:r['id']);ids=[x['id'] for x in rows];counts=collections.Counter(ids)
if any(v>1 for v in counts.values()):failures.append({'error':'duplicate actual concept IDs','ids':[k for k,v in counts.items() if v>1]})
if set(ids)!=set(assign):failures.append({'error':'ID-set mismatch','missing':sorted(set(assign)-set(ids)),'extra':sorted(set(ids)-set(assign))})
projection={'schema_version':1,'definition':'Identity/card semantic projection: NFC and whitespace-normalized id, label, learning_takeaway and card; exact scope/entity_kind; sorted unique aliases/domains; owner/primary_domain/primary_subfield from central selection v3. Excludes card versions, source/evidence/relationship metadata, locators, timestamps and validation/audit bookkeeping. It is a canonical content projection, not a claim that arbitrary paraphrases have identical hashes.','records':rows}
(O/'final-semantic-snapshot.json').write_text(json.dumps(projection,ensure_ascii=False,indent=2)+'\n');semsha=hashlib.sha256(canon(rows)).hexdigest()
def count(rs):
 new=[r for r in rs if r['id'] not in b];f=lambda r:r['scope'] in ['idea','facet_or_application'];n=lambda r:r['entity_kind']=='named_subject'
 return {'accepted':len(rs),'unique_ids':len({r['id'] for r in rs}),'new':len(new),'existing_controls':len(rs)-len(new),'new_fine_by_scope':sum(f(r) for r in new),'new_fine_idea_entities':sum(f(r) and not n(r) for r in new),'new_fine_named_subjects':sum(f(r) and n(r) for r in new),'named_subjects':sum(n(r) for r in rs),'new_named_subjects':sum(n(r) for r in new),'scopes':dict(sorted(collections.Counter(r['scope'] for r in rs).items())),'entity_kinds':dict(sorted(collections.Counter(r['entity_kind'] for r in rs).items())),'primary_domains':dict(sorted(collections.Counter(r['primary_domain'] for r in rs).items())),'primary_subfields':dict(sorted(collections.Counter(r['primary_subfield'] for r in rs).items()))}
per={i['batch_id']:count([r for r in rows if r['owner']==i['batch_id']]) for i in inputs};total=count(rows)
co={'schema_version':1,'computed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'inputs':inputs,'baseline_index_sha256':sha(bp),'selection_manifest_sha256':sha(mp),'selection_version':m['selection_version'],'semantic_sha256':semsha,'semantic_projection_definition':projection['definition'],'counting_rules':{'novelty':'Exact accepted ID absence from the frozen baseline, after recorded central identity adjudications; no historical equivalence proposal is silently applied.','fine':'New identities whose actual scope is idea or facet_or_application, including named subjects of those scopes. Entity-kind split is separately reported to avoid confusing fine scope with entity_kind=idea.','primary_coverage':'Count each ID once under the central primary domain and subfield, never secondary memberships.'},'per_batch':per,'pilot':total,'manifest_alignment_failures':failures,'identity_snapshot_path':'research/identity-review/final-semantic-snapshot.json','selected_text_changes':len(diffs)}
plan_path=R/'data/catalog-candidates/scale-pilot-001/coverage-plan.json';plan=json.loads(plan_path.read_text());starting=[];domain_mismatches=[]
for batch in plan['batches']:
 for dom in batch['primary_domains']:
  actual=per[batch['id']]['primary_domains'].get(dom['domain'],0)
  if actual!=dom['target_cards']:domain_mismatches.append({'batch_id':batch['id'],'domain':dom['domain'],'target':dom['target_cards'],'actual':actual})
  for sub in dom['starting_subfields']:
   actual=sum(r['owner']==batch['id'] and r['primary_domain']==dom['domain'] and r['primary_subfield']==sub for r in rows);starting.append({'batch_id':batch['id'],'domain':dom['domain'],'subfield':sub,'actual':actual})
co['coverage_plan_sha256']=sha(plan_path);co['coverage_checks']={'primary_domain_count':len(total['primary_domains']),'starting_subfield_count':len(starting),'starting_subfield_minimum_actual':min(x['actual'] for x in starting),'starting_subfield_shortfalls':[x for x in starting if x['actual']<plan['minimum_accepted_per_starting_subfield']],'primary_domain_target_mismatches':domain_mismatches,'additional_primary_subfields':sorted(set(r['primary_subfield'] for r in rows)-set(x['subfield'] for x in starting))}
(O/'final-record-counts.json').write_text(json.dumps(co,ensure_ascii=False,indent=2)+'\n');(O/'final-selection-text-deltas.json').write_text(json.dumps(diffs,ensure_ascii=False,indent=2)+'\n')
# Current-card diagnostics; lexical only. Inspect likely pairs rather than use score as a decision.
v=TfidfVectorizer(stop_words='english',ngram_range=(1,2),sublinear_tf=True);tx=[(r['label']+' ')*3+' '.join(r['aliases'])+' '+r['learning_takeaway']+' '+r['card'] for r in rows];mat=v.fit_transform(tx);word=(mat@mat.T).toarray();v=TfidfVectorizer(analyzer='char_wb',ngram_range=(3,5));mat=v.fit_transform([r['label'] for r in rows]);ch=(mat@mat.T).toarray();sim=.75*word+.25*ch
pairset=set()
for i,r in enumerate(rows):
 js=[int(j) for j in sim[i].argsort()[::-1] if j!=i and rows[j]['owner']!=r['owner']][:3]
 for j in js:
  if sim[i,j]>=.14:pairset.add(tuple(sorted([i,j])))
allpairs=[]
for i,j in sorted(pairset,key=lambda z:-sim[z[0],z[1]]):allpairs.append({'left_id':rows[i]['id'],'right_id':rows[j]['id'],'left_label':rows[i]['label'],'right_label':rows[j]['label'],'left_owner':rows[i]['owner'],'right_owner':rows[j]['owner'],'score':round(float(sim[i,j]),5)})
intra=[]
for i in range(len(rows)):
 for j in range(i+1,len(rows)):
  if rows[i]['owner']==rows[j]['owner'] and word[i,j]>.35:intra.append({'left_id':rows[i]['id'],'right_id':rows[j]['id'],'left_label':rows[i]['label'],'right_label':rows[j]['label'],'score':round(float(word[i,j]),5)})
intra.sort(key=lambda x:-x['score'])
diagnostic={'schema_version':1,'semantic_sha256':semsha,'cross_batch_pairs':allpairs,'within_batch_high_word_similarity_pairs':intra,'warning':'Scores only locate likely collisions. No score establishes identity equivalence or novelty.'}
(O/'final-card-diagnostics.json').write_text(json.dumps(diagnostic,ensure_ascii=False,indent=2)+'\n')
print('TOTAL',json.dumps(total));print('PER BATCH',json.dumps({k:{kk:v[kk] for kk in ['accepted','new','existing_controls','new_fine_by_scope','new_fine_idea_entities','new_fine_named_subjects','named_subjects']} for k,v in per.items()}));print('FAILURES',failures);print('SEMANTIC SHA',semsha);print('DIAGNOSTICS',len(allpairs),len(intra));print('DELTA COUNTS',len(diffs));print('LABEL/ALIAS DELTAS',json.dumps([r for r in diffs if any(k in r['changes'] for k in ['label','aliases'])],ensure_ascii=False))
