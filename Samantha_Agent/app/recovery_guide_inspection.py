"""Compact evidence on the wire, exact full-path citations in stored findings."""
from copy import deepcopy
import math,re
from app.recovery_guide_sources import canonical_json

SCHEMA = {'type':'object','properties':{
    'covered':{'type':'array','items':{'type':'object','properties':{
        'i':{'type':'integer'},'q':{'type':'string'}},'required':['i','q'],'additionalProperties':False}},
    'notes':{'type':'string'}},'required':['covered','notes'],'additionalProperties':False}


def anchor(text):
    # The live strict-schema backend rejects quote/newline string literals.
    # Choose an exact contiguous excerpt; never normalize source whitespace.
    for span in re.finditer(r'[^"\r\n]+',text):
        value=span.group().strip();words=list(re.finditer(r'\S+',value))[:6]
        if words:return value[:min(words[-1].end(),128)].strip()
    raise ValueError('inspection_no_safe_literal')


def schema(payload):
    choices=[]
    for i,row in enumerate(payload['sources']):
        choices.append({'type':'object','properties':{'i':{'type':'integer','enum':[i]},'q':{'type':'string','enum':[anchor(row['text'])]}},'required':['i','q'],'additionalProperties':False})
    return {'type':'object','properties':{'covered':{'type':'array','items':{'anyOf':choices}},'notes':{'type':'string'}},'required':['covered','notes'],'additionalProperties':False}


def instructions(budget):
    return ('\nINSPECTION OUTPUT: read ALL complete sources and original. covered contains ONLY '
        'entries in sources, never original. Return every explicit integer i exactly once; '
        'q must copy the source citation field EXACTLY, including its Markdown punctuation. '
        'Do not paraphrase citations. notes is at most 150 words, only material recovery findings. '
        f'The ENTIRE response including evidence and reasoning must fit {budget} output tokens.')


def wire(payload):
    value=deepcopy(payload)
    for index,row in enumerate(value['sources']):row.update(i=index,citation=anchor(row['text']))
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
