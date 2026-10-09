"""Small identity-preserving transformations for the coordinator's selection freeze."""
from copy import deepcopy

def effective_id(p):
    return p.get('suggested_id') or p['provisional_id']

def is_recommended(p):
    return (p.get('selection_status') in {'proposed','proposed_accept'} or
            p.get('proposal_status') in {'recommended','proposed_accept'} or
            p.get('recommendation')=='accept')

def normalize(p,batch_id,baseline):
    x=deepcopy(p)
    cid=effective_id(p)
    x.update(id=cid,owner=batch_id,originating_batch_id=batch_id,
             author_provisional_id=p['provisional_id'],
             inventory_status='existing' if cid in baseline else 'new')
    domains=list(dict.fromkeys([p['primary_domain'],*p.get('secondary_domains',[])]))
    x['domains']=domains
    x['secondary_domains']=domains[1:]
    aliases=set(p.get('aliases',[]))
    if cid in baseline:
        aliases.update(baseline[cid]['aliases'])
        aliases.add(baseline[cid]['label'])
    x['aliases']=sorted(aliases)
    return x
