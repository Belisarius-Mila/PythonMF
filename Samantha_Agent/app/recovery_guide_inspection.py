"""Compact evidence on the wire, exact full-path citations in stored findings."""
from copy import deepcopy
import math
from app.recovery_guide_sources import canonical_json

SCHEMA = {'type':'object','properties':{
    'covered':{'type':'array','items':{'type':'object','properties':{
        'i':{'type':'integer'},'q':{'type':'string'}},'required':['i','q'],'additionalProperties':False}},
    'notes':{'type':'string'}},'required':['covered','notes'],'additionalProperties':False}


def instructions(budget):
    return ('\nINSPECTION OUTPUT: covered contains ONLY entries in sources, never original. '
        'Use the explicit integer i in each source; return covered entries as {i,q}. '
        'q is a short exact quote, preferably 3 to 6 words. notes is at most 150 words, '
        'only material recovery findings. Be concise: the ENTIRE response including '
        f'evidence and reasoning must fit {budget} output tokens. Do not omit sources.')


def wire(payload):
    value=deepcopy(payload)
    for index,row in enumerate(value['sources']):row['i']=index
    return value


def normalize(answer,payload):
    from app.recovery_guide_maintainer import citation
    if not isinstance(answer,dict) or set(answer)!={'covered','notes'} or not isinstance(answer['notes'],str) or not isinstance(answer['covered'],list):raise ValueError('inspection_response_shape')
    if answer['covered'] and all(isinstance(row,dict) and set(row)=={'source','quote'} for row in answer['covered']):return normalize_known(answer,payload)
    rows=payload['sources'];found=set();result=[]
    for row in answer['covered']:
        if isinstance(row,dict) and type(row.get('i')) is float and math.isfinite(row['i']) and row['i'].is_integer():row={**row,'i':int(row['i'])}
        if not isinstance(row,dict) or set(row)!={'i','q'} or type(row['i']) is not int or not 0<=row['i']<len(rows) or row['i'] in found:raise ValueError('inspection_source_identity')
        found.add(row['i']);source=rows[row['i']];item={'source':source['path'],'quote':row['q']};citation(item,{source['path']:source['text']});result.append(item)
    if len(found)!=len(rows):raise ValueError('inspection_incomplete_sources')
    return {'covered':result,'notes':answer['notes']}


def normalize_known(answer,payload):
    """The historical exact-original-only correction, with no invented quotes."""
    from app.recovery_guide_maintainer import citation
    if not isinstance(answer,dict) or set(answer)!={'covered','notes'} or not isinstance(answer['notes'],str) or not isinstance(answer['covered'],list):raise ValueError('known_inspection_shape')
    original=payload['original'];texts={s['path']:s['text'] for s in payload['sources']};rows=answer['covered'];extra=[r for r in rows if isinstance(r,dict) and r.get('source')==original['path']]
    if len(extra)>1:raise ValueError('known_duplicate_original')
    if extra:citation(extra[0],{original['path']:original['text']})
    kept=[r for r in rows if r not in extra]
    if len(kept)!=len(texts) or {r.get('source') for r in kept}!=set(texts):raise ValueError('known_coverage_not_exact')
    for row in kept:citation(row,texts)
    return {'covered':kept,'notes':answer['notes']}
