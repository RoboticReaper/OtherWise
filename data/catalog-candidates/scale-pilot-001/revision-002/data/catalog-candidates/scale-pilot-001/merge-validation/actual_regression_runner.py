#!/usr/bin/env python3
"""Hash-gated, isolated regressions. Never writes the accepted pilot catalog."""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import itertools
import json
import re
import shutil
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

HERE=Path(__file__).resolve().parent
DEFAULT_WORK=HERE.parents[3]
PILOT='data/catalog-candidates/scale-pilot-001'
CANDIDATES=[f'data/catalog-candidates/research-batch-{n:03d}.json' for n in range(3,8)]
INPUTS=CANDIDATES+[PILOT+'/baseline-index.json',PILOT+'/identity-decisions.json']
CASE_NAMES=['actual_unchanged_reverse_repeat','actual_source_scoping','actual_shared_name_aliases','actual_aliases_and_provenance','forced_local_reference_collision','historical_retrieved_at_only','concept_conflict_quarantine','explicit_concept_version_choice','malformed_input_quarantine','unresolved_target_quarantine','equivalence_mechanics','input_integrity']

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text())
def write(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def require(condition,message):
    if not condition: raise AssertionError(message)
def empty_decisions(): return dict(schema_version=1,equivalences=[],distinctness=[],unresolved=[],concept_versions={},batch_versions={})

class Runner:
    def __init__(self,root,out,expected,fixture_only):
        self.root=root;self.out=out;self.expected=expected;self.fixture_only=fixture_only
        self.tool=root/'tools/catalog_combiner.py'
        spec=importlib.util.spec_from_file_location('pilot_combiner_for_regression',self.tool)
        self.lib=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.lib)
        self.cases=[];self.commands=[]
        self.protected={p:sha(root/p) for p in INPUTS}
        for p in [PILOT+'/catalog.json',PILOT+'/merge-validation/gate-results.json']:
            if (root/p).exists(): self.protected[p]=sha(root/p)
        self.snapshot=out/'frozen-inputs';self.snapshot.mkdir()
        for p in INPUTS:
            raw=(root/p).read_bytes()
            require(hashlib.sha256(raw).hexdigest()==expected[p],f'input_changed_during_snapshot: {p}')
            (self.snapshot/Path(p).name).write_bytes(raw)
        self.paths=[self.snapshot/Path(p).name for p in CANDIDATES]
        self.docs=[read(p) for p in self.paths]
        self.baseline=self.snapshot/'baseline-index.json'
        self.decisions=read(self.snapshot/'identity-decisions.json')
        write(out/'artifact-role.json',dict(regression_only=True,fixture_only=fixture_only,counts_toward_research=False,can_publish_as_accepted_catalog=False,notice='Mutation cases are software regressions, not factual claims or researched identities. Unchanged snapshots are copied only for reproducible verification.'))
    def case(self,name,fn):
        try:
            data=fn() or {};status=data.pop('status','passed')
            self.cases.append(dict(name=name,status=status,**data));return data
        except Exception as exc:
            self.cases.append(dict(name=name,status='failed',reason=f'{type(exc).__name__}: {exc}'));return None
    def invoke(self,directory,paths,decisions,all_five=True,verify=False,seed=False,expected_code=None):
        directory.mkdir(parents=True,exist_ok=True)
        output=directory/'regression-catalog.json';report=directory/'combiner-report.json'
        if seed: shutil.copyfile(self.valid_output,output)
        before=sha(output) if output.exists() else None
        args=[sys.executable,str(self.tool),'verify-actual' if verify else 'combine','--inputs',*map(str,paths),'--baseline',str(self.baseline),'--decisions',str(decisions),'--output',str(output),'--report',str(report)]
        if all_five: args+=['--require-all-batches']
        p=subprocess.run(args,capture_output=True,text=True,cwd=self.root)
        (directory/'stdout.txt').write_text(p.stdout);(directory/'stderr.txt').write_text(p.stderr)
        self.commands.append(dict(command=args,actual_exit_code=p.returncode,expected_exit_code=1 if expected_code else 0,case_directory=str(directory.relative_to(self.out))))
        require(p.returncode==(1 if expected_code else 0),f'Unexpected combiner exit {p.returncode}: {p.stderr[:1500]}')
        r=read(report)
        if expected_code:
            require(r.get('status')=='quarantined','Rejection was not quarantined.')
            require(expected_code in [e['code'] for e in r.get('errors',[])],f'Expected quarantine code {expected_code}.')
            require(Path(r['quarantine_path']).exists(),'Missing quarantine artifact.')
            after=sha(output);require(before==after,'Last valid output changed during rejection.')
            return dict(expected_quarantine_code=expected_code,last_valid_retained=True,before_sha256=before,after_sha256=after,report=str(report.relative_to(self.out)))
        return read(output),r,output
    def prepare_variant(self,name,documents,decisions=None):
        directory=self.out/name;inputs=directory/'inputs';inputs.mkdir(parents=True)
        docs=copy.deepcopy(documents);dec=copy.deepcopy(self.decisions if decisions is None else decisions)
        paths=[];mapping={}
        for i,d in enumerate(docs):
            d['batch']['regression_only']=dict(case=name,counts_toward_research=False,factual_equivalence_assertion=False,notice='Isolated software regression; do not use as accepted research.')
            p=inputs/(d['batch']['id']+'.json');write(p,d);paths.append(p)
            if len(documents)==5: mapping[sha(self.paths[i])]=sha(p)
        # Only rebind technical exact-file choices in isolated copies. No new research decision is made.
        for choice in [*dec.get('concept_versions',{}).values(),*dec.get('batch_versions',{}).values(),*[e.get('selected_card',{}) for e in dec.get('equivalences',[])]]:
            if choice.get('input_sha256') in mapping: choice['input_sha256']=mapping[choice['input_sha256']]
        dp=inputs/'identity-decisions.json';write(dp,dec)
        return directory,paths,dp,docs
    def mapping(self,decisions):
        return {m:e['canonical_id'] for e in decisions.get('equivalences',[]) for m in e['member_ids']}
    def check_scopes(self,docs,paths,combined,decisions):
        sources={s['id']:s for s in combined['sources']};concepts={c['id']:c for c in combined['concepts']}
        equivalents=self.mapping(decisions);local=defaultdict(set);evidence_count=relation_refs=0
        for doc,path in zip(docs,paths):
            bid=doc['batch']['id'];h=sha(path)
            for s in doc['sources']:
                sid=self.lib.ref_id(bid,s['id']);require(sid in sources,f'Missing scoped source {sid}.')
                out=sources[sid]
                require(out['originating_batch_id']==bid and out['original_id']==s['id'],'Origin namespace mismatch.')
                require(out['originating_input_sha256']==h,'Source input hash mismatch.')
                for k,v in s.items():
                    if k not in {'id','original_id','originating_batch_id','originating_input_sha256'}: require(out.get(k)==v,f'Lost source metadata: {sid}/{k}.')
                local[s['id']].add(bid)
            for c in doc['concepts']:
                cid=equivalents.get(c['id'],c['id']);out=concepts[cid]
                selected=combined['batch']['selected_card_versions'][cid]
                active=(selected['input_sha256']==h and selected['original_id']==c['id']) or c['id'] in equivalents
                if not active: continue
                for e in c['evidence']:
                    expected=copy.deepcopy(e);expected['source_id']=self.lib.ref_id(bid,e['source_id'])
                    require(expected in out['evidence'],f'Evidence mis-scoped for {c["id"]}.');evidence_count+=1
                for r in c['relations']:
                    expected=copy.deepcopy(r);expected['source_ids']=sorted({self.lib.ref_id(bid,s) for s in r['source_ids']});expected['target_id']=equivalents.get(r['target_id'],r['target_id'])
                    require(expected in out['relations'],f'Relation mis-scoped for {c["id"]}.');relation_refs+=len(r['source_ids'])
        return dict(source_count=len(sources),evidence_links_checked=evidence_count,relation_source_links_checked=relation_refs,colliding_local_ids={k:sorted(v) for k,v in sorted(local.items()) if len(v)>1})
    def unchanged(self):
        combined,r,output=self.invoke(self.out/'unchanged',self.paths,self.snapshot/'identity-decisions.json',verify=True)
        self.combined=combined;self.valid_output=output
        input_ids={c['id'] for d in self.docs for c in d['concepts']};mapping=self.mapping(self.decisions)
        require({c['id'] for c in combined['concepts']}=={mapping.get(c,c) for c in input_ids},'Combined identities differ from selected pilot identities.')
        return dict(distinct_concept_count=len(combined['concepts']),reference_count=len(combined['sources']),canonical_content_sha256=r['canonical_content_sha256'],checks=r['passed'],output=str(output.relative_to(self.out)))
    def provenance(self):
        mapping=self.mapping(self.decisions);idx=self.combined['batch']['alias_index'];count=0
        for d,p in zip(self.docs,self.paths):
            h=sha(p);bid=d['batch']['id']
            snapshot=[x for x in self.combined['batch']['input_provenance'] if x['input_sha256']==h]
            require(len(snapshot)==1 and snapshot[0]['candidate_snapshot']==d,'Original candidate snapshot changed.')
            for c in d['concepts']:
                cid=mapping.get(c['id'],c['id']);records=self.combined['batch']['concept_provenance'][cid]
                preserved=[r for r in records if r['input_sha256']==h and r['original_id']==c['id']]
                require(len(preserved)==1 and preserved[0]['original_record']==c,'Original concept provenance changed.')
                require(preserved[0]['reference_namespace']['batch_id']==bid,'Original reference namespace missing.')
                for alias in [c['label'],*c['aliases']]: require(cid in idx.get(self.lib.normalize_alias(alias),[]),f'Alias lost: {alias}.')
                count+=1
        return dict(original_concept_records_checked=count,original_input_snapshots_checked=len(self.docs))
    def shared_names(self):
        groups={a:ids for a,ids in self.combined['batch']['alias_index'].items() if len(ids)>1}
        if not groups: return dict(status='unrun',reason='No actual shared-name group exists in supplied outputs; none is invented.')
        supported_pairs={frozenset(pair) for decision in self.decisions.get('distinctness',[]) for pair in itertools.combinations(decision['member_ids'],2)}
        for alias,ids in groups.items():
            require(all(frozenset(pair) in supported_pairs for pair in itertools.combinations(ids,2)),f'An actual ambiguous alias lacks complete pairwise distinctness reviews: {alias}.')
        return dict(shared_alias_group_count=len(groups),groups=groups)
    def collision(self):
        docs=copy.deepcopy(self.docs);new='REGRESSION_ONLY_SHARED_LOCAL_REFERENCE'
        for d in docs[:2]:
            old=d['concepts'][0]['evidence'][0]['source_id']
            require(not any(s['id']==new for s in d['sources']),'Regression sentinel source ID already exists.')
            for s in d['sources']:
                if s['id']==old: s['id']=new
            for c in d['concepts']:
                for e in c['evidence']:
                    if e['source_id']==old:e['source_id']=new
                for r in c['relations']:r['source_ids']=[new if sid==old else sid for sid in r['source_ids']]
        directory,paths,dp,docs=self.prepare_variant('forced-reference-collision',docs)
        combined,_,_=self.invoke(directory,paths,dp)
        result=self.check_scopes(docs,paths,combined,read(dp))
        require(len(result['colliding_local_ids'].get(new,[]))==2,'Forced collision was not exercised.')
        return dict(mode='regression_only_reference_renaming',counts_toward_research=False,**result)
    def historical(self):
        for d in self.docs:
            for s in d['sources']:
                if 'retrieval_date' not in s and 'T' in str(s.get('retrieved_at','')):
                    out=next(x for x in self.combined['sources'] if x['id']==self.lib.ref_id(d['batch']['id'],s['id']))
                    require('retrieval_date' not in out and out['retrieved_at']==s['retrieved_at'],'Historical timestamp changed.')
                    return dict(mode='actual_timestamp_only_reference',source_id=out['id'],retrieved_at=out['retrieved_at'])
        docs=copy.deepcopy(self.docs);s=docs[0]['sources'][0];s.pop('retrieval_date',None)
        mode='regression_only_date_field_omission'
        if 'T' not in str(s.get('retrieved_at','')):
            s['retrieved_at']='2001-02-03T04:05:06+00:00';mode='regression_only_synthetic_timestamp'
        stamp=s['retrieved_at'];sid=self.lib.ref_id(docs[0]['batch']['id'],s['id'])
        directory,paths,dp,_=self.prepare_variant('historical-timestamp-only',docs)
        combined,_,_=self.invoke(directory,paths,dp)
        source=next(x for x in combined['sources'] if x['id']==sid)
        require('retrieval_date' not in source and source['retrieved_at']==stamp,'Timestamp-only metadata was lost.')
        return dict(mode=mode,counts_toward_research=False,source_id=sid,retrieved_at=stamp,notice='Metadata shape mutation only; no historical browsing claim is made.')
    def derived_pair(self,equivalence=False):
        source=copy.deepcopy(self.docs[0]);c=copy.deepcopy(source['concepts'][0]);c['relations']=[]
        docs=[]
        for i in range(2):
            item=copy.deepcopy(c)
            if equivalence:
                item['id']='regression:equivalence:'+('left' if i==0 else 'right')
                item['label']=c['label']+(' [regression original]' if i==0 else ' [regression alternate name]')
            elif i:
                item['card_version']+=1
                words=item['card'].split();words[0]='REGRESSION-ONLY';item['card']=' '.join(words)
            docs.append(dict(schema_version=1,batch=dict(id=f'research-batch-{i+3:03d}',revision=1,derived_from_input_sha256=sha(self.paths[0]),derived_from_concept_id=c['id'],derivation='Exact source-backed input card copied for isolated mechanics; unrelated relationships removed. Any modified prose/identity is synthetic, not researched.'),sources=copy.deepcopy(source['sources']),concepts=[item],issues=[],validation={}))
        return docs
    def conflict(self):
        docs=self.derived_pair();directory,paths,dp,_=self.prepare_variant('concept-conflict',docs,empty_decisions())
        self.conflict_paths=paths
        return self.invoke(directory,paths,dp,all_five=False,seed=True,expected_code='concept_conflict')
    def version_choice(self):
        docs=self.derived_pair();directory,paths,dp,docs=self.prepare_variant('explicit-version-choice',docs,empty_decisions())
        c=docs[1]['concepts'][0];d=empty_decisions();d['concept_versions'][c['id']]=dict(batch_id=docs[1]['batch']['id'],input_sha256=sha(paths[1]),card_version=c['card_version'],reviewed=True,reason='Regression-only explicit selection of the synthetic competing version; not an acceptance decision for research.')
        write(dp,d);combined,_,_=self.invoke(directory,paths,dp,all_five=False,verify=True)
        require(combined['concepts'][0]['card_version']==c['card_version'],'Explicit choice selected the wrong version.')
        require(len(combined['batch']['concept_provenance'][c['id']])==2,'A conflicting original record was discarded.')
        return dict(mode='synthetic_competing_version_of_actual_card',counts_toward_research=False,selected_input_sha256=sha(paths[1]),original_provenance_records=2)
    def malformed(self):
        docs=copy.deepcopy(self.docs);del docs[0]['concepts'][0]['card']
        directory,paths,dp,_=self.prepare_variant('malformed-input',docs)
        return self.invoke(directory,paths,dp,seed=True,expected_code='missing_field')
    def unresolved(self):
        docs=copy.deepcopy(self.docs);target='regression:deliberately-unresolved-target'
        require(target not in self.lib.baseline_ids(read(self.baseline)) and target not in {c['id'] for d in docs for c in d['concepts']},'Target sentinel unexpectedly exists.')
        docs[0]['concepts'][0]['relations'].append(dict(target_id=target,type='related_to',source_ids=[],assertion='editorial',note='Regression-only deliberately unresolved relationship target.'))
        directory,paths,dp,_=self.prepare_variant('unresolved-target',docs)
        return self.invoke(directory,paths,dp,seed=True,expected_code='unresolved_target')
    def equivalence(self):
        if self.decisions.get('equivalences'):
            self.provenance();self.check_scopes(self.docs,self.paths,self.combined,self.decisions)
            return dict(mode='actual_reviewed_equivalence',reviewed_groups=len(self.decisions['equivalences']),counts_toward_research=False)
        docs=self.derived_pair(equivalence=True);directory,paths,dp,docs=self.prepare_variant('equivalence-mechanics',docs,empty_decisions())
        a,b=[d['concepts'][0] for d in docs];s=docs[0]['sources'][0]
        dec=empty_decisions();dec['equivalences']=[dict(canonical_id=a['id'],member_ids=[a['id'],b['id']],reviewed=True,reason='Synthetic exact-copy equivalence for software regression only; this asserts no equivalence between distinct actual subjects.',evidence=[dict(url=s['url'],locator=s['locator'],note='Provenance of the copied card; equality is established by the regression construction, not an inferred factual equivalence.')],selected_card=dict(concept_id=a['id'],batch_id=docs[0]['batch']['id'],input_sha256=sha(paths[0]),card_version=a['card_version']))]
        write(dp,dec);combined,_,_=self.invoke(directory,paths,dp,all_five=False,verify=True)
        require(len(combined['concepts'])==1,'Synthetic reviewed copies did not collapse.')
        require({a['label'],b['label']}<=set(combined['concepts'][0]['aliases']),'Equivalent-copy aliases were lost.')
        require(len(combined['batch']['concept_provenance'][a['id']])==2,'Equivalent-copy original records were lost.')
        self.check_scopes(docs,paths,combined,dec)
        return dict(mode='synthetic_derived_copy',counts_toward_research=False,factual_equivalence_assertion=False,original_card_id=self.docs[0]['concepts'][0]['id'],retained_provenance_records=2)
    def integrity(self):
        after={p:sha(self.root/p) for p in self.protected}
        require(after==self.protected,'Canonical input, previous catalog or original gate evidence changed during the run.')
        return dict(protected_file_count=len(after),sha256=after)
    def run(self):
        self.case(CASE_NAMES[0],self.unchanged)
        if hasattr(self,'combined'):
            jobs=[(CASE_NAMES[1],lambda:self.check_scopes(self.docs,self.paths,self.combined,self.decisions)),(CASE_NAMES[2],self.shared_names),(CASE_NAMES[3],self.provenance),(CASE_NAMES[4],self.collision),(CASE_NAMES[5],self.historical),(CASE_NAMES[6],self.conflict),(CASE_NAMES[7],self.version_choice),(CASE_NAMES[8],self.malformed),(CASE_NAMES[9],self.unresolved),(CASE_NAMES[10],self.equivalence)]
            for name,fn in jobs:self.case(name,fn)
        else:
            self.cases += [dict(name=n,status='unrun',reason='Unchanged inputs failed; no acceptance or mutation regressions are claimed.') for n in CASE_NAMES[1:-1]]
        self.case(CASE_NAMES[-1],self.integrity)
        failed=[c['name'] for c in self.cases if c['status']=='failed'];unrun=[c['name'] for c in self.cases if c['status']=='unrun']
        result=dict(schema_version=1,status='failed' if failed else 'partial' if unrun else 'passed',fixture_only=self.fixture_only,counts_toward_research=False,final_catalog_written=False,completed_at=datetime.now(timezone.utc).isoformat(),expected_input_sha256=self.expected,combiner_sha256=sha(self.tool),runner_sha256=sha(Path(__file__)),passed=[c['name'] for c in self.cases if c['status']=='passed'],failed=failed,unrun=unrun,cases=self.cases,commands=self.commands,limits=['Regression mechanics do not certify independent audit completion or factual support.','Synthetic mutations and derived subsets never count as accepted research.'])
        write(self.out/'regression-results.json',result)
        print(json.dumps(dict(status=result['status'],fixture_only=self.fixture_only,passed=len(result['passed']),failed=failed,unrun=unrun,report=str(self.out/'regression-results.json')),indent=2))
        return 0 if result['status']=='passed' else 1

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--expected-inputs',required=True);p.add_argument('--run-id',required=True)
    p.add_argument('--work-root',default=str(DEFAULT_WORK));p.add_argument('--fixture-only',action='store_true')
    args=p.parse_args(argv);root=Path(args.work_root).resolve()
    try:
        require(root==DEFAULT_WORK or args.fixture_only,'alternate_work_root_requires_fixture_only')
        require(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}',args.run_id) is not None,'invalid_run_id')
        manifest=read(args.expected_inputs)
        require(manifest.get('authorization')=='run_on_final_audited_inputs','final_input_authorization_required')
        expected=manifest.get('expected_sha256',{})
        require(set(expected)==set(INPUTS),'expected_input_set_must_be_exactly_five_candidates_baseline_and_decisions')
        for rel in INPUTS:require(sha(root/rel)==expected[rel],f'input_hash_mismatch: {rel}')
        out=root/PILOT/'merge-validation/actual-regressions'/args.run_id
        require(not out.exists(),'run_directory_exists')
        out.mkdir(parents=True,exist_ok=False)
        runner=Runner(root,out,expected,args.fixture_only)
        return runner.run()
    except (AssertionError,OSError,ValueError,KeyError) as exc:
        print(str(exc),file=sys.stderr);return 2
if __name__=='__main__':sys.exit(main())
