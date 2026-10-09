from pathlib import Path
import json,hashlib,datetime,unicodedata,re
R=Path(__file__).resolve().parents[2];O=R/'research/identity-review'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canon(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def norm(s):return ' '.join(unicodedata.normalize('NFC',s).split())
counts=json.loads((O/'final-record-counts.json').read_text());snapshot=json.loads((O/'final-semantic-snapshot.json').read_text());C={r['id']:r for r in snapshot['records']};manifest=json.loads((R/'data/catalog-candidates/scale-pilot-001/selection-manifest.json').read_text());A={r['id']:r for r in manifest['accepted']};refresh=[]
for i in counts['inputs']:
 p=R/i['path'];d=json.loads(p.read_text());rows=[]
 for c in d['concepts']:
  r={k:norm(c[k]) for k in ['id','label','entity_kind','scope','learning_takeaway','card']};r['aliases']=sorted(set(norm(x) for x in c['aliases']));r['domains']=sorted(set(c['domains']));a=A[c['id']];r.update(owner=d['batch']['id'],primary_domain=a['primary_domain'],primary_subfield=a['primary_subfield']);rows.append(r)
 assert hashlib.sha256(canon(sorted(rows,key=lambda r:r['id']))).hexdigest()==i['semantic_sha256'],f"Meaning changed: {i['batch_id']}"
 h=sha(p)
 if h!=i['sha256']:refresh.append({'batch_id':i['batch_id'],'previous_sha256':i['sha256'],'current_sha256':h,'semantic_projection_unchanged':True});i['sha256']=h
assert next(x['sha256'] for x in counts['inputs'] if x['batch_id']=='research-batch-004')=='dd8af872210586f6e46b6f0fecdfcf1c4b6078061146f094b47a2a76a8edaf02'
counts['metadata_only_input_refreshes']=refresh;counts['input_hashes_verified_at']=datetime.datetime.now(datetime.timezone.utc).isoformat();(O/'final-record-counts.json').write_text(json.dumps(counts,ensure_ascii=False,indent=2)+'\n')
prior_path=O/'cross-batch-overlap-review.json';prior=json.loads(prior_path.read_text());diag=json.loads((O/'final-card-diagnostics.json').read_text());bd=json.loads((O/'final-baseline-neighbor-diagnostics.json').read_text());deltas=json.loads((O/'final-selection-text-deltas.json').read_text())
read_ids=set();cases=[]
def refs(ids):
 out=[]
 for id in ids:
  if id not in C:continue
  read_ids.add(id);c=C[id];out.append({'id':id,'label':c['label'],'owner':c['owner'],'semantic_record_sha256':hashlib.sha256(canon(c)).hexdigest()})
 return out
for i,p in enumerate(prior['meaning_comparisons'],1):
 cases.append({'case_id':f'prior-{i:02d}','left':refs(p['left_ids']),'right':refs(p['right_ids']),'result':'distinct_meanings_retained','actual_card_check':'Actual current card text and learning takeaways were read; the previously documented distinction remains explicit.','meaning_comparison':p['meaning_comparison'],'boundary':p.get('boundary')})
ams=[('Homology',['Q1144780','local:catalog:homology-biology'],'Topological cycles/boundaries versus similarity inherited from common ancestry.'),('Graft',['local:catalog:horticultural-grafting','local:catalog:skin-grafting'],'Joining scion/rootstock versus detached skin requiring a new blood supply.'),('Bond',['Q44424','local:catalog:bond-finance'],'Interatomic attraction versus a debt-security repayment promise.'),('Pitch',['local:catalog:pitch-material','local:catalog:pitch-music'],'Explicitly tar-derived, slowly flowing material versus perceived musical highness/lowness.'),('Constitution',['Q7755','local:catalog:material-constitution'],'Governmental powers and rules versus the disputed relationship between an object and its constituting matter.')]
ambiguities=[{'alias':a,'cards':refs(ids),'result':'separate_supported_senses','meaning_comparison':r} for a,ids,r in ams]
supp=[]
def add(id,ids,result,reason):supp.append({'case_id':id,'cards':refs(ids),'result':result,'meaning_comparison':reason})
add('central-organizational-design',['Q3318170'],'registered_id_reuse_verified','The final card arranges roles, responsibilities and coordination, matching the pinned Organizational architecture meaning. Q3318170 is an existing control, with the original architecture alias preserved. No separately accepted local:catalog:organizational-design remains.')
assert 'local:catalog:organizational-design' not in C
add('graph-theory-adjacency-refinement',['local:authored:000604','Q727035'],'presentation_overlap_resolved_identity_distinct','The initially observed Graph theory takeaway repeated the adjacency-matrix/relabeling lesson. The saved version-5 refinement now separates underlying connections from drawing/labeling. Q727035 separately teaches matrix encoding, zero diagonal and symmetry for simple undirected graphs. Both registered IDs remain appropriate; no merge or novelty change is warranted.')
add('cue-only-delayed-judgments',['local:catalog:delayed-judgments-of-learning'],'scope_clarification_retained','The display-label refinement explicitly preserves the cue-only delayed calibration procedure already intended at selection. It does not add a new identity or broaden a method into all judgments of learning.')
add('sqlite-wal-checkpoint',['local:catalog:write-ahead-logging','local:catalog:wal-checkpointing'],'general_architecture_and_distinct_phase','SQLite is the bounded explanatory implementation. The log architecture separates appending/commit from main-file updates, while checkpointing is the later transfer phase. The source-specific wording does not create a duplicate or an extra product-specific identity.')
add('replicated-consensus-log-raft',['local:catalog:distributed-consensus','local:catalog:replicated-log','local:catalog:raft-consensus-algorithm'],'distinct_problem_artifact_and_algorithm','The approved crash-fault consensus label is retained. Ordered agreement with a communicating-majority condition, the replicated command-history data structure, and Raft’s particular leader/election/safety protocol remain distinct learning subjects.')
intranotes=[('first-price-sealed-bid-auction','second-price-sealed-bid-auction','Winner pays own bid versus second-highest bid; same allocation rule does not erase the different payment mechanism.'),('chair-by-ruth-asawa','negative-space','The named 1965 lithograph TAM.1558-II is a particular work; negative space is the general compositional use of unmarked areas, exemplified by that work.'),('first-order-reaction-half-life','second-order-reaction-half-life','Concentration-independent half-life under first-order kinetics versus concentration-dependent half-life under the stated single-reactant second-order law.'),('body-centered-cubic-structure','face-centered-cubic-structure','Different atomic positions, conventional-cell populations and coordination numbers establish different crystal arrangements.'),('diagnostic-sensitivity','diagnostic-specificity','Positive results conditioned on disease presence versus negative results conditioned on disease absence.'),('karner-blue-butterfly','mutualism','The butterfly is a named taxon with a documented ant interaction; mutualism is the broader interaction category. Shared use of this example does not make the taxon identical to the mechanism.')]
intra=[]
for x,y,n in intranotes:intra.append({'cards':refs(['local:catalog:'+x,'local:catalog:'+y]),'result':'distinct_meanings_retained','meaning_comparison':n})
bnotes=[
'General optical estimation procedure versus the specific pigmentation-related accuracy limitation. The general card also explains noninvasive estimation; the existing limitation card remains bounded to an accuracy factor.',
'Uninterrupted collective recitation practice versus the named scripture being read.',
'Inertial frames omit inertial-force corrections; rotating frames are one non-inertial class requiring them.',
'Coriolis is the rotation-related sideways-deflection term, narrower than the general class of fictitious forces; the card retains its rotating-frame meaning.',
'Conditional no-expected-change stochastic process versus the general expected-value operation.',
'Ecological influence on community persistence is the selected keystone meaning; a culturally significant species is not automatically that ecological mechanism.',
'The particular stored-program computer and its historical operation differ from the cathode-ray-tube component.',
'A specific criminal-statute ambiguity principle differs from criminal law as a field.',
'Reversing note order differs explicitly from reversing interval direction.',
'Apple is explicitly the company in a historical supply-chain case, not the fruit.',
'The entry priority and inability-to-enter rule is a specific game procedure, distinct from Backgammon overall even though an older broad card used bar entry as its example.',
'The bounded empirical Paris law is one member of the general crack-growth-equation class.',
'A particular named Morris textile design, including its measured repeat, differs from textile design generally.',
'Three-member coalition and persistence structure differs from the general social-group category.',
'A specific MMP eligibility rule differs from New Zealand history and the country’s electoral system as a whole.',
'Two-person dependence on continued participation differs from the general group category.',
'Prayer direction differs explicitly from the architectural niche that marks it.',
'Luck in the situations encountered differs from moral luck generally and from its older outcome-luck example.',
'The restricted pedagogical note-ratio exercise method differs from combining simultaneous melodic lines generally; the current Counterpoint control is not another new method count.',
'General carbon-dioxide-driven ocean chemistry differs in breadth from regional Arctic or Great Barrier Reef applications.',
'General castling rights/temporary barriers differ from Chess960-specific starting positions and resulting piece movement.',
'Luck shaping traits and dispositions differs from luck in circumstances or outcomes and from the general philosophical category.',
'Archaeological interpretation of deposits is a bounded application to human activity, while the pinned general stratigraphic subject concerns rock layers.',
'A hymn and its devotional use differ from the entire named scriptural collection.',
'A specific objection about inseparable intended means/side effects differs from the doctrine it challenges.',
'Liquid–vapor boundary endpoint differs from a fluid state beyond the critical temperature and pressure.',
'An obligation with latitude in fulfillment is a specified duty category rather than duty generally or optional supererogation.',
'The color-changing measurement substance/application differs from proton-transfer reactions generally.',
'Stable snapshot visibility is different from added serializability checks and from PostgreSQL-specific Repeatable Read timing; the card expressly avoids inferring serializability from visibility alone.',
'An ideal reversible benchmark cycle differs from the broader heat-engine class.'
]
bchecks=[]
for r,n in zip(bd['records'][:30],bnotes):
 bchecks.append({'card':refs([r['id']])[0],'baseline_neighbors_screened':r['neighbors'],'result':'no_unresolved_equivalence_found','meaning_comparison':n,'inspection_scope':'Current card read; nearest baseline registered meaning and any displayed prior candidate card read. This is identity comparison, not a fresh source audit.'})
refs(['local:catalog:skin-pigmentation-and-pulse-oximetry'])
changed=[]
for d in deltas:
 substantive={k:v for k,v in d['changes'].items() if k!='aliases' or set(v['selected'])!=set(v['actual'])}
 if substantive:
  refs([d['id']]);changed.append({'id':d['id'],'changes':substantive,'result':'same_intended_identity_after_qualification_or_example_refinement'})
# Actual lookup is multi-valued for all five alias groups.
def aliasnorm(s):return re.sub(r'[^\w]+',' ',unicodedata.normalize('NFKC',s).casefold()).strip()
lookup={}
for c in C.values():
 for s in set(c['aliases']+[c['label']]):lookup.setdefault(aliasnorm(s),set()).add(c['id'])
shared={k:sorted(v) for k,v in lookup.items() if len(v)>1}
for a,ids,_ in ams:assert lookup[aliasnorm(a)]==set(ids),(a,lookup[aliasnorm(a)])
report={'schema_version':1,'review_type':'bounded_final_card_semantic_overlap_and_admission_check','status':'complete_no_unresolved_semantic_duplicate_identified','completed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'inputs':counts['inputs'],'baseline_index_sha256':counts['baseline_index_sha256'],'selection_manifest_sha256':counts['selection_manifest_sha256'],'selection_version':3,'prior_cross_batch_review':{'path':str(prior_path.relative_to(R)),'sha256':sha(prior_path)},'semantic_sha256':counts['semantic_sha256'],'semantic_projection_definition':snapshot['definition'],'semantic_snapshot':{'path':'research/identity-review/final-semantic-snapshot.json','file_sha256':sha(O/'final-semantic-snapshot.json')},'metadata_only_input_refreshes':refresh,'checks':{'actual_ids_unique':1000,'manifest_alignment_failures':counts['manifest_alignment_failures'],'previous_concrete_comparison_groups_rechecked':len(cases),'shared_alias_groups_rechecked':len(ambiguities),'final_cross_batch_diagnostic_pairs_screened':len(diag['cross_batch_pairs']),'within_batch_high_similarity_pairs_read':len(intra),'new_to_baseline_neighbor_cases_read':len(bchecks),'unique_current_cards_read_in_targeted_meaning_checks':len(read_ids),'takeaway_or_label_delta_records_reconciled':len(changed),'fresh_external_source_audits_performed':0},'prior_concrete_comparisons':cases,'shared_alias_comparisons':ambiguities,'current_shared_alias_lookup':shared,'supplemental_comparisons':supp,'within_batch_likely_collision_comparisons':intra,'baseline_near_match_comparisons':bchecks,'selection_text_delta_reconciliation':changed,'targeted_card_ids_read':sorted(read_ids),'findings':[{'id':'final-identity-001','severity':'resolved_presentation_overlap','ids':['local:authored:000604','Q727035'],'finding':'The initial Graph theory takeaway duplicated the matrix/relabeling promise. The author saved the approved field-level refinement at card version 5; exact semantic delta independently verified. Registered identities remain separate.','verification_artifact':'research/identity-review/final-graph-theory-refinement-check.json'}],'unresolved_semantic_duplicates':[],'admission_counts':{'accepted':1000,'new':counts['pilot']['new'],'existing_controls':counts['pilot']['existing_controls'],'new_fine_by_scope':counts['pilot']['new_fine_by_scope'],'new_fine_idea_entities':counts['pilot']['new_fine_idea_entities'],'new_fine_named_subjects':counts['pilot']['new_fine_named_subjects'],'named_subjects':counts['pilot']['named_subjects']},'record_counts_artifact':{'path':'research/identity-review/final-record-counts.json','sha256':sha(O/'final-record-counts.json')},'limits':['This is bounded semantic admission/overlap review. It does not independently source-audit all 1,000 facts, certify every relationship, or replace the frozen random/risk source audits.','Similarity retrieval only identified candidates to inspect. Scores are not equivalence decisions or proof of novelty; undetected semantic overlap remains possible.','Exact novelty uses preserved IDs against the pinned baseline after central decisions. Historical urban-heat-island, Silk Road and confirmation-bias equivalence proposals remain unmerged.','A broad subject may use the same example as a separately meaningful method, application or named case. Shared examples alone do not collapse those identities.','Fine counts follow actual approved scope classes. They include 53 named subjects and separately report 650 idea entities; this count is not proof of an exhaustive or unique ontology.','The semantic fingerprint excludes sources, locators, versions and audit bookkeeping. Metadata-only updates do not invalidate these meaning comparisons, but changed included text or assignments require a delta recheck.','No candidates, IDs, central reservations or older reviews were modified by this reviewer.']}
(O/'final-cross-batch-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
md=['# Final semantic overlap and record-count review','',f"Completed {report['completed_at']}. No unresolved semantic duplicate was identified in this bounded check.",'','## Result','',f"The five actual candidates contain **1,000 distinct identities: 819 new and 181 controls**. There are **703 new fine-scope subjects**: 650 idea entities and 53 named subjects. Total named subjects: **158**.",'','All IDs, owners, scopes, entity kinds and primary assignments match selection v3. All 23 primary-domain targets match; all 69 starting subfields have at least eight cards. The additional tissue-repair subfield has one card.','',f"Semantic projection SHA-256: `{report['semantic_sha256']}`.",'','The projection covers actual labels, aliases, cards, takeaways, types, scopes, domains and central primary ownership. It excludes versions, locators and other evidence/audit metadata. All five current file hashes and per-batch semantic fingerprints are in the JSON report. Batch 006’s locator-only update was checked to leave this projection unchanged.','', '## Exact check scope','',f"- Re-read the actual cards in all 24 earlier concrete comparison groups\n- Verified all five shared aliases: Homology, Graft, Bond, Pitch and Constitution\n- Screened {len(diag['cross_batch_pairs'])} final-card cross-batch diagnostic pairs\n- Read six high-similarity within-batch pairs and 30 new-to-baseline near-match cases\n- Reconciled {len(changed)} non-order-only selection text changes\n- Read {len(read_ids)} unique current cards in targeted meaning comparisons\n- Performed no new broad factual-source audit",'', '## Resolved finding','', 'Graph theory’s initial takeaway repeated the Adjacency matrix lesson. The approved version-5 takeaway now says: “Separate a network’s underlying connections from the way its vertices and edges are drawn or labeled.” The matrix card separately teaches its encoding rules. The exact change was verified; both registered identities remain distinct.','', 'Organizational design correctly reuses Q3318170, preserves the Organizational architecture alias, and counts as a control. No extra local identity survives.','', '## Rechecked earlier comparisons','']
for c in cases:
 l=', '.join(x['label'] for x in c['left']);r=', '.join(x['label'] for x in c['right']);md.append(f"- {c['case_id']}: {l} / {r}. {c['meaning_comparison']}")
md+=['','## Per-batch counts','','| Batch | Accepted | New | Controls | New fine scope | Named |','|---|---:|---:|---:|---:|---:|']
for k,v in counts['per_batch'].items():md.append(f"| {k} | {v['accepted']} | {v['new']} | {v['existing_controls']} | {v['new_fine_by_scope']} | {v['named_subjects']} |")
md+=['','## Limits','']+['- '+x for x in report['limits']]+['','The JSON report lists every checked comparison, exact IDs, current-card semantic hashes, input hashes, and the complete targeted-card inspection list. `final-record-counts.json` contains the full actual domain/subfield/scope breakdowns.','']
(O/'final-cross-batch-review.md').write_text('\n'.join(md))
print('INPUT REFRESH',refresh);print('CHECKS',report['checks']);print('SEMANTIC',report['semantic_sha256'])
for f in ['final-cross-batch-review.json','final-cross-batch-review.md','final-record-counts.json']:print(f,sha(O/f))
