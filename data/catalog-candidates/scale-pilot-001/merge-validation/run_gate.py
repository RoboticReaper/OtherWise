#!/usr/bin/env python3
"""Persist reproducible fixture-gate commands, outputs, quarantine and results."""
import copy
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
HERE=Path(__file__).resolve().parent
WORK=HERE.parents[3]
FIX=HERE/'fixtures'
RESULTS=HERE/'results'
RESULTS.mkdir(exist_ok=True)
TOOL=WORK/'tools/catalog_combiner.py'
BASELINE=HERE.parent/'baseline-index.json'
commands=[]
def save(path,data): path.write_text(json.dumps(data,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
def execute(name,args,expected=0):
    p=subprocess.run([sys.executable,*map(str,args)],cwd=WORK,text=True,capture_output=True)
    (RESULTS/(name+'.stdout.txt')).write_text(p.stdout)
    (RESULTS/(name+'.stderr.txt')).write_text(p.stderr)
    r=dict(name=name,command=[sys.executable,*map(str,args)],cwd=str(WORK),actual_exit_code=p.returncode,expected_exit_code=expected,status='passed' if p.returncode==expected else 'failed')
    commands.append(r)
    return p,r
p,suite=execute('full-test-suite',['-m','unittest','discover','-s',HERE,'-p','test_*.py','-v'])
unit_tests=[]
for line in (p.stdout+p.stderr).splitlines():
    m=re.match(r'(test_\w+) \((.*?)\) \.\.\. (ok|FAIL|ERROR|skipped.*)',line)
    if m: unit_tests.append(dict(test=m[1],result=m[3]))
def cli(name,inputs,decisions='empty-decisions',expect_code=None,seed=False,baseline=None,command='combine'):
    directory=RESULTS/name; directory.mkdir(exist_ok=True)
    output=directory/'catalog.json'; report=directory/'report.json'
    args=[TOOL,command,'--inputs',*[FIX/(n+'.json') for n in inputs],'--baseline',baseline or FIX/'baseline.json','--decisions',FIX/(decisions+'.json'),'--output',output,'--report',report]
    if seed:
        execute(name+'-last-valid',[TOOL,'combine','--inputs',FIX/'a.json','--baseline',FIX/'baseline.json','--decisions',FIX/'empty-decisions.json','--output',output,'--report',directory/'last-valid-report.json'])
    before=hashlib.sha256(output.read_bytes()).hexdigest() if output.exists() else None
    p,run=execute(name,args,1 if expect_code else 0)
    if report.exists():
        r=json.loads(report.read_text()); run['report']=str(report.relative_to(WORK));run['result_status']=r['status']
        if expect_code:
            run['expected_quarantine_code']=expect_code
            run['quarantine_code_verified']=expect_code in [e['code'] for e in r.get('errors',[])]
            if not run['quarantine_code_verified']: run['status']='failed'
        if seed:
            run['last_valid_sha256_before']=before
            run['last_valid_sha256_after']=hashlib.sha256(output.read_bytes()).hexdigest() if output.exists() else None
            run['retention_verified']=run['last_valid_sha256_before']==run['last_valid_sha256_after']
            if not run['retention_verified']: run['status']='failed'
        if not expect_code: run['canonical_content_sha256']=r.get('canonical_content_sha256');run['counts']=r.get('counts')
    else: run['status']='failed'
    return run
runs={}
for name,inputs,decisions,code,seed in [
    ('base',['a','b'],'empty-decisions',None,False),
    ('repeated-import',['a','b','a'],'empty-decisions',None,False),
    ('reversed-order',['b','a'],'empty-decisions',None,False),
    ('reviewed-equivalence',['a','equivalent','link'],'equivalence-decisions',None,False),
    ('distinct-same-name',['planet','element'],'distinct-decisions',None,False),
    ('same-url-revisions',['a','same-url'],'empty-decisions',None,False),
    ('historical-timestamp',['a'],'empty-decisions',None,False),
    ('conflicting-id',['a','conflict'],'empty-decisions','concept_conflict',True),
    ('malformed-input',['malformed'],'empty-decisions','missing_field',True),
    ('malformed-json',['broken-json'],'empty-decisions','malformed_json',True),
    ('unresolved-target',['unresolved'],'empty-decisions','unresolved_target',True),
    ('unreviewed-equivalence',['a','equivalent'],'proposed-equivalence','unreviewed_equivalence',True),
    ('unresolved-different-ids',['a','b'],'unresolved-decisions','unresolved_identity',True),
    ('explicit-card-version',['a','conflict'],'version-decisions',None,False),
    ('explicit-batch-version',['a','revision2'],'batch-version-decisions',None,False),
    ('direct-self-relation',['self-relation'],'empty-decisions','self_relation',True),
    ('remapped-self-relation',['a','equivalent-self'],'equivalence-decisions','self_relation',True),
]: runs[name]=cli(name,inputs,decisions,code,seed)
runs['actual-command-fixture']=cli('actual-command-fixture',['a','b'],command='verify-actual')
if BASELINE.exists():
    baseline=json.loads(BASELINE.read_text()); target=sorted(baseline['concepts'])[0]
    probe=json.loads((FIX/'a.json').read_text());probe['concepts'][0]['relations']=[dict(target_id=target,type='related_to',source_ids=['r1'],assertion='editorial',note='Labeled fixture tests resolution against one actual pinned baseline target; this is not a researched relationship.')]
    save(FIX/'actual-baseline-probe.json',probe)
    runs['actual-pinned-baseline']=cli('actual-pinned-baseline',['actual-baseline-probe'],baseline=BASELINE)
    runs['actual-pinned-baseline']['pinned_baseline_sha256']=hashlib.sha256(BASELINE.read_bytes()).hexdigest()
    runs['actual-pinned-baseline']['pinned_baseline_id_count']=len(baseline['concepts'])
    runs['actual-pinned-baseline']['resolved_target']=target
else:
    runs['actual-pinned-baseline']=dict(status='unrun',reason='Coordinator baseline-index.json is absent.')
checks={
 'same_unchanged_import_twice':runs['base'].get('canonical_content_sha256')==runs['repeated-import'].get('canonical_content_sha256') and runs['base'].get('counts')==runs['repeated-import'].get('counts'),
 'unchanged_inputs_reversed':runs['base'].get('canonical_content_sha256')==runs['reversed-order'].get('canonical_content_sha256'),
 'reviewed_equivalence_aliases_and_provenance':runs['reviewed-equivalence']['status']=='passed',
 'same_name_distinct_meanings':runs['distinct-same-name']['status']=='passed',
 'batch_scoped_source_ids_and_links':runs['base']['status']=='passed',
 'conflict_quarantine_and_last_valid_retention':runs['conflicting-id']['status']=='passed',
 'malformed_input_quarantine_and_last_valid_retention':runs['malformed-input']['status']=='passed' and runs['malformed-json']['status']=='passed',
 'unresolved_target_quarantine_and_last_valid_retention':runs['unresolved-target']['status']=='passed',
 'historical_iso_timestamp_without_date':runs['historical-timestamp']['status']=='passed',
 'separate_same_url_revisions_and_passages':runs['same-url-revisions']['status']=='passed',
 'explicit_competing_version_choice':runs['explicit-card-version']['status']=='passed' and runs['explicit-batch-version']['status']=='passed',
 'actual_pinned_baseline_loaded':runs['actual-pinned-baseline']['status']=='passed',
}
failed=[k for k,v in checks.items() if not v]+[r['name'] for r in commands if r['status']=='failed']
summary=dict(schema_version=1,status='passed' if not failed else 'failed',completed_at=datetime.now(timezone.utc).isoformat(),fixture_only=True,tool_sha256=hashlib.sha256(TOOL.read_bytes()).hexdigest(),unit_test_count=len(unit_tests),unit_tests=unit_tests,mandatory_gate_cases=checks,passed=sorted(k for k,v in checks.items() if v),failed=failed,unrun=[dict(check='actual_researched_output_repeated_and_reversed_import',reason='Research has not started; command is prepared in README.md and actual-output-check.sh.'),dict(check='operational_application_tests',reason='No operational files changed; this is an isolated pilot utility and its full available suite was run.')],historical_test_first_evidence=[dict(path='red-test-output.txt',result='18 expected test failures before the CLI existed'),dict(path='green-test-output.txt',result='18 passed after first implementation'),dict(path='red-hardening-output.txt',result='One expected failure and one test KeyError before hardening'),dict(path='red-hardening-confirmed-output.txt',result='Three expected failures and two test helper errors; helper was corrected'),dict(path='red-hardening-clean-output.txt',result='Five expected assertion failures before hardening implementation'),dict(path='green-hardening-output.txt',result='25 passed after hardening')],commands=commands,runs=runs,limitations=['Fixtures are synthetic and do not count as researched cards.','Structural checks cannot certify factual support, semantic distinctness beyond supplied reviews, or independent source audit completion.','No bundled input scripts were executed.'])
save(HERE/'gate-results.json',summary)
save(HERE/'commands.json',commands)
print(json.dumps(dict(status=summary['status'],unit_test_count=len(unit_tests),mandatory_gate_cases=checks,failed=failed),indent=2))
sys.exit(0 if not failed else 1)
