"""Check completed-card and referenced-source version lineage between snapshots."""
def refs(c):
    return {e['source_id'] for e in c.get('evidence',[])}|{s for r in c.get('relations',[]) for s in r.get('source_ids',[])}
def content(c):
    return {k:v for k,v in c.items() if k not in {'card_version','previous_card_version','previous_card_sha256','previous_artifact_sha256'}}
def compare(before,after):
    b={c['id']:c for c in before['concepts']};a={c['id']:c for c in after['concepts']}
    bs={s['id']:s for s in before['sources']};ass={s['id']:s for s in after['sources']}
    changed_sources={s for s in set(bs)|set(ass) if bs.get(s)!=ass.get(s)}
    rows=[];failures=[];changed=[];source_changed=[]
    for cid in sorted(set(b)&set(a)):
        fields=sorted(k for k in set(content(b[cid]))|set(content(a[cid])) if content(b[cid]).get(k)!=content(a[cid]).get(k))
        affected=sorted((refs(b[cid])|refs(a[cid]))&changed_sources)
        is_changed=bool(fields or affected)
        expected=b[cid]['card_version']+int(is_changed)
        if a[cid]['card_version']!=expected:failures.append({'id':cid,'code':'version_lineage','expected':expected,'actual':a[cid]['card_version']})
        if is_changed:changed.append(cid)
        if affected:source_changed.append(cid)
        rows.append({'id':cid,'changed':is_changed,'changed_fields':fields,'changed_source_ids':affected,'previous_card_version':b[cid]['card_version'],'current_card_version':a[cid]['card_version']})
    return {'failures':failures,'changed_card_ids':changed,'source_changed_card_ids':source_changed,'changed_source_ids':sorted(changed_sources),'added_ids':sorted(set(a)-set(b)),'removed_ids':sorted(set(b)-set(a)),'records':rows,'limit':'A changed-field/version check does not certify factual support; independent source rechecks remain required.'}
