"""Integrated weekly guide contract. Pure proposal rendering; no model or writes.

The server copies retained blocks and emits one trusted revision date. Every
old block has an explicit disposition; only historical noise may be retired.
Legacy quality.validate keeps its original retention policy for old receipts.
"""
from dataclasses import dataclass
from datetime import date
import json
import math
import re

from app import recovery_guide_quality as quality
from app.recovery_guide_sources import canonical_json, digest

VERSION = 'integrated_guide_v1'
TITLE = 'OBNOVA SAMANTHY NA NOVÉM MACU'
STAMP = 'Nejnovější update dokumentu z '
APPENDIX = re.compile(r'(?im)^\s*(?:doplnění|dodatek|dodatky|aktualizace\s+(?:kapitoly|ze dne|z\s+\d))\b')
BACKUP_STATISTICS = re.compile(r'(?is)\b(?:záloh\w*|snapshot)\b[^\n]{0,240}\b\d[\d ]*\s*(?:soubor|bajt)')
SNAPSHOT_ID = re.compile(r'(?<!\w)20\d{6}_\d{6}(?:-[a-f0-9]+)?(?!\w)')
REVISION = re.compile(r'(?im)^\s*(?:Nejnovější update dokumentu z\s+\S+|Verze\s+\d[^\n]*)\s*$')
SAFETY = re.compile(r'ne(?:maž|mazat|přepis|opak|spouš|povol)|nejist|neověřen|soukrom|hesl|token|zastav|STOP|nesmí',re.I)
INSTRUCTIONS = '''Výstup týdenní revize je jediný aktuální sjednocený návod.
Neopisuj celý původní text: keep zachová přesné staré bloky programově.
rewrite nahradí vyjmenované bloky novým souvislým textem přímo v kapitole;
insert vloží nový potřebný obsah na příslušné místo. Nepřipojuj DOPLNĚNÍ,
dodatky ani druhé konkurenční znění stejného postupu. Historii, citace a
rozhodnutí uchová program mimo čtenářský text. retire je pouze doložené
odstranění zastaralé poznámky o záloze/verzi, ne potřebného kroku či ochrany.
Každý původní blok musí být právě jednou keep, rewrite nebo retire. Zachovej
pořadí a potřebné oblasti kapitol. Nové i odstraněné tvrzení dolož evidence;
pro nové texty je evidence vždy neprázdná, historické zdroje nejsou live stav.
Odstraň stará pevná snapshot ID, statistiky a dávné přejímací zápisy; výběr
zálohy popiš podle dokončených manifestů. Zachovej potřebné příkazy a data.
Datum záhlaví neposílej: program vloží jediné Nejnovější update dokumentu z
ddmmyyyy podle schváleného data revize. Není to datum zálohy nebo nasazení.
Běžné vztahy slov piš slovy, nepoužívej lomítko jako zkratku cesty. Neznámé
nastavení označ OVĚŘIT a uveď způsob zjištění. Po úplném čtení bez obsahových změn vrať keep; program přesto aktualizuje datum revize. Žádné příkazy nevykonávej.'''


def fail(condition,code):
    if condition:raise quality.QualityError('consolidation_'+code)


def obj(properties):
    return {'type':'object','properties':properties,'required':list(properties),'additionalProperties':False}


def array(items,minimum=0,maximum=1024):
    return {'type':'array','items':items,'minItems':minimum,'maxItems':maximum}


def layout(original):
    heads=quality._headings(original)
    fail(not heads or [int(h[1]) for h in heads]!=list(range(1,len(heads)+1)), 'invalid_chapter_structure')
    fail(len(heads)>32,'too_many_chapters')
    prefix=original[:heads[0].start()]
    removed=[];lines=[]
    for i,line in enumerate(prefix.splitlines(keepends=True)):
        if (i==0 and line.strip()==TITLE) or REVISION.fullmatch(line.rstrip('\r\n')):
            removed.append(digest(line));continue
        lines.append(line)
    sections=[('intro',None,''.join(lines))]
    for i,head in enumerate(heads):
        text=original[head.end():heads[i+1].start() if i+1<len(heads) else None]
        # Heading decoration is controlled metadata, not recoverable user content.
        text=re.sub(r'^\r?\n[=]+\r?\n','',text,count=1)
        sections.append((f'c{i+1:02d}',head[0],text))
    result=[]
    for sid,heading,text in sections:
        blocks=[part.strip('\r\n') for part in re.split(r'\r?\n[ \t]*\r?\n',text) if part.strip()]
        fail(len(blocks)>1024,'too_many_blocks')
        result.append({'id':sid,'heading':heading,'blocks':[{'id':i+1,'text':b} for i,b in enumerate(blocks)],
                      'retirable':[i+1 for i,b in enumerate(blocks) if retirable(b)]})
    return {'sections':result,'removed_frontmatter_sha256':removed}


def retirable(text):
    if SAFETY.search(text):return False
    # Operational instructions are never disposable historical prose.
    if quality.COMMAND.search(text) or quality.SHELL.search(text):return False
    return bool(SNAPSHOT_ID.search(text) or
        re.search(r'(?is)(?:záloh|snapshot).*(?:\d[ \d]*\s*(?:soubor|bajt)|\d{1,2}\.\s*\d{1,2}\.)',text) or
        all(APPENDIX.fullmatch(line.strip()) for line in text.splitlines() if line.strip()))


@dataclass(frozen=True)
class Request:
    envelope: str
    @property
    def payload(self):return json.loads(self.envelope)
    @property
    def sha256(self):return digest(self.envelope)


def prepare(snapshot,findings,day):
    fail(type(day) is not date,'trusted_date_required')
    quality._sources(snapshot)
    quality.safe_text(snapshot.original.text)
    body={'phase':'synthesize','original':snapshot.original.text,'findings':findings,
          'format_contract':VERSION,'snapshot_sha256':snapshot.sha256,'revision_date':day.isoformat(),
          'guide_layout':layout(snapshot.original.text)}
    return Request(canonical_json({'request_id':digest(canonical_json(body)),**body}))


def schema(payload):
    fail(not isinstance(payload,dict) or payload.get('format_contract')!=VERSION,'contract_required')
    body={k:v for k,v in payload.items() if k!='request_id'}
    fail(payload.get('request_id')!=digest(canonical_json(body)),'request_changed')
    fail(payload.get('guide_layout')!=layout(payload['original']),'layout_changed')
    citation=obj({'source':{'type':'string'},'quote':{'type':'string'}})
    evidence=array(citation,1,16)
    sections={}
    for section in payload['guide_layout']['sections']:
        count=len(section['blocks'])
        number={'type':'integer','minimum':1,'maximum':max(1,count)}
        refs=array(number,1,max(1,count))
        write={'text':{'type':'string'},'status':{'type':'string','enum':['documented','unverified']},'evidence':evidence}
        operations=[obj({'action':{'type':'string','enum':['insert']},**write})]
        if count:
            operations.extend([
                obj({'action':{'type':'string','enum':['keep']},'block':number}),
                obj({'action':{'type':'string','enum':['rewrite']},'blocks':refs,**write}),
                obj({'action':{'type':'string','enum':['retire']},'block':number,
                     'reason':{'type':'string'},'evidence':evidence})])
        sections[section['id']]=array({'anyOf':operations},0 if section['id']=='intro' else 1,2048)
    return obj({'request_id':{'type':'string','enum':[payload['request_id']]},'sections':obj(sections)})


def checked(request,snapshot):
    fail(not isinstance(request,Request),'trusted_request_required')
    payload=request.payload
    try:day=date.fromisoformat(payload['revision_date'])
    except (KeyError,TypeError,ValueError):raise quality.QualityError('consolidation_invalid_date') from None
    expected=prepare(snapshot,payload['findings'],day)
    fail(expected.envelope!=request.envelope,'request_binding_changed')
    return payload,day


def keys(value,expected):
    fail(not isinstance(value,dict) or set(value)!=set(expected),'response_shape')


def index(value,count):
    if type(value) is float and math.isfinite(value) and value.is_integer():value=int(value)
    fail(type(value) is not int or not 1<=value<=count,'unknown_block')
    return value


def validate(answer,snapshot,request,*,context=None):
    payload,day=checked(request,snapshot)
    keys(answer,('request_id','sections'))
    fail(answer['request_id']!=payload['request_id'],'response_request_changed')
    sections=payload['guide_layout']['sections'];keys(answer['sections'],[s['id'] for s in sections])
    paragraphs=[];rendered=[];audit=[]
    for section in sections:
        sid=section['id'];blocks={b['id']:b['text'] for b in section['blocks']};used=set();ordered=[]
        operations=answer['sections'][sid]
        fail(not isinstance(operations,list) or len(operations)>2048,'invalid_operations')
        emitted=[]
        for operation in operations:
            fail(not isinstance(operation,dict),'invalid_operation')
            action=operation.get('action');old_ids=[]
            if action=='keep':
                keys(operation,('action','block'));old_ids=[index(operation['block'],len(blocks))]
                row={'text':blocks[old_ids[0]],'status':'unchanged','evidence':[]}
            elif action in {'rewrite','insert'}:
                keys(operation,('action','text','status','evidence',*(['blocks'] if action=='rewrite' else [])))
                if action=='rewrite':
                    fail(not isinstance(operation['blocks'],list) or not operation['blocks'],'invalid_rewrite_blocks')
                    old_ids=[index(n,len(blocks)) for n in operation['blocks']]
                row={k:operation[k] for k in ('text','status','evidence')}
                quality.safe_text(row['text'])
                fail(bool(re.match(r'\s*\[Neověřeno\]',row['text'])),'model_status_prefix')
                for old_id in old_ids:
                    old=blocks[old_id]
                    if old_id not in section['retirable']:
                        fail(any(line.startswith(('    ','\t')) for line in old.splitlines())
                             and old not in row['text'],'protected_procedure_lost')
                        fail(any(m[0].casefold() not in row['text'].casefold()
                                 for m in SAFETY.finditer(old)),'safety_control_lost')
                fail(row['status'] not in {'documented','unverified'},'invalid_new_status')
                fail(not isinstance(row['evidence'],list) or not 1<=len(row['evidence'])<=16,'missing_evidence')
                # An exact old block may be kept, never smuggled as a new grant.
                if row['text'] in snapshot.original.text:
                    row={'text':row['text'],'status':'unchanged','evidence':row['evidence']}
            elif action=='retire':
                keys(operation,('action','block','reason','evidence'))
                old_ids=[index(operation['block'],len(blocks))]
                fail(old_ids[0] not in section['retirable'],'operational_block_retired')
                quality.safe_text(operation['reason']);fail(not operation['reason'].strip(),'missing_retirement_reason')
                fail(not isinstance(operation['evidence'],list) or not 1<=len(operation['evidence'])<=16,'missing_retirement_evidence')
                quality.anchors(operation['evidence'],quality._sources(snapshot))
                row=None
            else:raise quality.QualityError('consolidation_unknown_action')
            fail(len(set(old_ids))!=len(old_ids) or bool(used.intersection(old_ids)),'duplicate_block_coverage')
            used.update(old_ids);ordered.extend(old_ids)
            if row:
                quality.safe_text(row['text'])
                fail(not row['text'].strip(),'empty_block')
                fail(bool(quality._headings(row['text'])),'nested_chapter_heading')
                emitted.append(row);paragraphs.append(row)
            audit.append({'section':sid,'action':action,'old_blocks':old_ids,
                          'new_text_sha256':digest(row['text']) if row else None,
                          'evidence':operation.get('evidence',[]),
                          **({'reason':operation['reason']} if action=='retire' else {})})
        fail(used!=set(blocks),'unaccounted_original_block')
        fail(ordered!=sorted(ordered),'reordered_original_blocks')
        fail(sid!='intro' and not emitted,'empty_chapter')
        # Topic presence is additional, not a claim of full semantic equivalence.
        before='\n'.join(text for n,text in blocks.items() if n not in section['retirable']).casefold()
        after='\n'.join(row['text'] for row in emitted).casefold()
        for topic,words in quality.TOPICS.items():
            fail(any(word in before for word in words) and not any(word in after for word in words), 'topic_lost_'+topic)
        rendered.append((section,emitted))
    quality.validate_content({'paragraphs':paragraphs},snapshot,context=context,integrated=True)
    output=[TITLE,STAMP+day.strftime('%d%m%Y')]
    for section,rows in rendered:
        if section['heading']:output.append(section['heading']+'\n'+'='*len(section['heading']))
        output.extend(('[Neověřeno]\n' if r['status']=='unverified' else '')+r['text'] for r in rows)
    candidate='\n\n'.join(output)+'\n'
    quality.safe_text(candidate)
    fail(bool(APPENDIX.search(candidate)),'appendix_layer')
    fail(bool(SNAPSHOT_ID.search(candidate)),'fixed_backup_snapshot')
    fail(bool(BACKUP_STATISTICS.search(candidate)),'obsolete_backup_statistics')
    fail(len(REVISION.findall(candidate))!=1,'duplicate_revision')
    fail([m[1] for m in quality._headings(candidate)]!=[s['heading'].split('.',1)[0] for s in sections if s['heading']], 'chapter_order')
    return {'candidate':candidate,'candidate_sha256':digest(candidate),'format_contract':VERSION,
            'revision_date':day.isoformat(),'resolved_paragraphs':{'paragraphs':paragraphs},
            'change_audit':audit,'original_frontmatter_removed':payload['guide_layout']['removed_frontmatter_sha256'],
            'semantic_acceptance':'required','publication':'not_authorized'}
