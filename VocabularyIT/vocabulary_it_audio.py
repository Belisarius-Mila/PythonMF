"""Plan/build IT word and sentence MP3s through the registered project TTS tool.

A durable private request ledger is written before transport. Unknown outcomes
are never retried automatically. Public manifests appear only when every asset
is verified; words and sentences retain distinct IT/CZ namespaces.
"""
from __future__ import annotations
import argparse
import fcntl
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tempfile
from threading import Event, Lock
import unicodedata

from vocabulary_it_catalog import CATALOG, ROOT, all_card_texts, digest, load_catalog, load_rows

RATE='-10%'
VOICES={'it':'it-IT-ElsaNeural','cz':'cs-CZ-VlastaNeural'}
ENDPOINT='wss://api.msedgeservices.com/tts/cognitiveservices/websocket/v1'


def encoded(value):
    return (json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n').encode()


def atomic(path: Path, data: bytes):
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent,prefix='.'+path.name+'.',delete=False) as f:
        f.write(data);f.flush();os.fsync(f.fileno());temp=Path(f.name)
    os.replace(temp,path)


def text(value,kind):
    if not isinstance(value,str) or not value.strip() or len(value)>1500:
        raise ValueError('Chybí nebo je příliš dlouhý zdrojový text; nebude zkrácen.')
    value=unicodedata.normalize('NFC',' '.join(value.split()))
    if kind=='words':
        value=value.replace('(','').replace(')','')
        value=re.sub(r'\s*[,;/]\s*','. ',value)
        value=re.sub(r'\s+([?.!])',r'\1',value)
        value=re.sub(r'\.{2,}','.',value)
    return value.strip()


def asset_path(language,kind,spoken,voices=VOICES):
    voice=voices[language];identity=hashlib.sha256(encoded([voice,RATE,spoken])).hexdigest()
    namespace='audio' if kind=='words' else 'sentences'
    slug=re.sub(r'([a-z])([A-Z])',r'\1-\2',voice).lower()
    return f'assets/vocabulary-it-{namespace}/{slug}/{identity}.mp3'


def load_items(source_root: Path, output_root: Path):
    catalog=load_catalog();rows=load_rows(source_root/'VocabularyIT/VocabularyIT.csv')
    expected={entry['uid']:(entry,body) for entry,body in all_card_texts(rows,catalog)}
    data=json.loads((output_root/'data/vocabulary-it-v2.json').read_text())
    if (data.get('schemaVersion')!=2 or data.get('language')!='it'
            or data.get('provenance',{}).get('catalogSha256')!=digest(CATALOG)
            or data.get('provenance',{}).get('sourceCsvSha256')!=digest(source_root/'VocabularyIT/VocabularyIT.csv')
            or not isinstance(data.get('items'),list) or len(data['items'])!=len(expected)):
        raise ValueError('Webová data nejsou přesným výstupem aktuálního IT katalogu.')
    seen=set()
    for item in data['items']:
        uid=item.get('uid')
        if uid not in expected or uid in seen:raise ValueError('Neznámá nebo duplicitní zvuková identita.')
        entry,body=expected[uid]
        if item.get('active')!=entry['active'] or any(item.get(k)!=v for k,v in body.items()):
            raise ValueError('Webový význam nebo věty se změnily; nejprve obnov export.')
        seen.add(uid)
    return [item for item in data['items'] if item['active']]


def plan(items,voices=VOICES):
    if set(voices)!={'it','cz'} or voices['it'] not in {'it-IT-ElsaNeural','it-IT-IsabellaNeural','it-IT-DiegoNeural'} or voices['cz']!='cs-CZ-VlastaNeural':
        raise ValueError('Neznámý hlasový profil.')
    manifests={};jobs={}
    for kind in ('words','sentences'):
        records={}
        for item in items:
            uid=item['uid'];record={'uid':uid,'sourceIt':item['it'],'sourceCz':item['cz']}
            if uid in records:raise ValueError('Duplicitní UID.')
            if kind=='sentences':record.update(sourceSentenceIt=item['sentenceIt'],sourceSentenceCz=item['sentenceCz'])
            for language,source_field in [('it','it' if kind=='words' else 'sentenceIt'),('cz','cz' if kind=='words' else 'sentenceCz')]:
                spoken=text(item[source_field],kind);path=asset_path(language,kind,spoken,voices)
                record[language]=path;record['spokenIt' if language=='it' else 'spokenCz']=spoken
                job={'path':path,'text':spoken,'voice':voices[language],'rate':RATE,'language':language,'kind':kind}
                if path in jobs and jobs[path]!=job:raise ValueError('Kolize zvukové identity.')
                jobs[path]=job
            records[uid]=record
        manifests[kind]={'schemaVersion':1,'language':'it','kind':kind,'status':'complete','provider':'registered-edge-tts',
                         'rate':RATE,'voices':voices,'items':records,'sourceDigest':hashlib.sha256(encoded(records)).hexdigest()}
    identity=hashlib.sha256(encoded(manifests)).hexdigest()
    return {'schemaVersion':1,'project':'VocabularyIT-audio','digest':identity,'manifests':manifests,'jobs':jobs,
            'stats':{'cards':len(items),'references':len(items)*4,'uniqueAssets':len(jobs),
                     'characters':sum(len(j['text']) for j in jobs.values()),
                     'italianAssets':sum(j['language']=='it' for j in jobs.values()),
                     'czechAssets':sum(j['language']=='cz' for j in jobs.values())}}


def valid_audio(path: Path):
    if not path.is_file() or path.is_symlink() or path.stat().st_size<1000:return False
    command=shutil.which('ffprobe')
    if not command:raise RuntimeError('Chybí ffprobe.')
    result=subprocess.run([command,'-v','error','-show_entries','format=duration:stream=codec_name','-of','json',str(path)],capture_output=True,text=True,timeout=15)
    try:
        data=json.loads(result.stdout)
        return result.returncode==0 and float(data['format']['duration'])>0.05 and any(s['codec_name']=='mp3' for s in data['streams'])
    except (ValueError,KeyError,TypeError):return False


def reuse_index(repo: Path):
    """Only public EN records with explicit exact text, voice and rate match."""
    result={}
    for filename,kind in [('vocabulary-en-audio.json','words'),('vocabulary-en-sentence-audio.json','sentences')]:
        path=repo/'docs/data'/filename
        if not path.is_file():continue
        manifest=json.loads(path.read_text());voice=manifest.get('voices',{}).get('cz',{}).get('id')
        if voice!='cs-CZ-VlastaNeural' or manifest.get('rate')!=RATE:continue
        for record in manifest.get('items',{}).values():
            spoken=record.get('spokenCz');relative=record.get('cz')
            if not isinstance(spoken,str) or not isinstance(relative,str):continue
            parts=PurePosixPath(relative)
            if parts.is_absolute() or '..' in parts.parts or not relative.startswith('assets/vocabulary-en-'):continue
            source=repo/'docs'/relative
            if source.resolve().is_relative_to((repo/'docs').resolve()) and source.is_file():
                result.setdefault((voice,RATE,spoken),source)
    return result


@contextmanager
def registered_generator(*,alternate_endpoint=False):
    sys.path.insert(0,str(ROOT/'Samantha_Agent'))
    from app.capabilities import get_capability, RiskLevel
    from app.speech.edge_tts_mp3 import synthesize_edge_tts_mp3_sync
    capability=get_capability('generate_project_audio_asset')
    if capability.risk!=RiskLevel.EXTERNAL_GENERATION or capability.tool!='app.speech.edge_tts_mp3.synthesize_edge_tts_mp3_sync' or capability.metadata.get('durable_consent')!='trusted_external_generation_v1':
        raise RuntimeError('Nesouhlasí registrovaný zvukový generátor.')
    # One isolated CLI process/batch. All workers share this fixed endpoint;
    # restore after they have joined, never patch/restore between concurrent calls.
    import edge_tts.communicate as communicate
    from edge_tts.constants import TRUSTED_CLIENT_TOKEN
    previous=communicate.WSS_URL
    if alternate_endpoint:communicate.WSS_URL=ENDPOINT+'?Ocp-Apim-Subscription-Key='+TRUSTED_CLIENT_TOKEN
    try:yield synthesize_edge_tts_mp3_sync
    finally:communicate.WSS_URL=previous


def build(plan_data,output: Path,receipt_path: Path,**kwargs):
    receipt_path.parent.mkdir(parents=True,exist_ok=True)
    with receipt_path.with_suffix(receipt_path.suffix+'.lock').open('a+b') as handle:
        try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise ValueError('Tentýž zvukový běh už pracuje; další požadavek se neodešle.') from None
        try:return _build(plan_data,output,receipt_path,**kwargs)
        finally:fcntl.flock(handle,fcntl.LOCK_UN)


def _build(plan_data,output: Path,receipt_path: Path,*,synthesize,reuse=None,uids=None,workers=3,limit=None,source_guard=None):
    if type(workers) is not int or not 1<=workers<=4:raise ValueError('Počet workerů musí být1–4.')
    if limit is not None and (type(limit) is not int or limit<1):raise ValueError('Neplatný limit.')
    output=output.resolve();reuse=reuse or {};lock=Lock();stopped=Event();generated=reused=0
    ledger={'schemaVersion':1,'project':'VocabularyIT-audio','planDigest':plan_data['digest'],'jobs':{}}
    if receipt_path.exists():
        ledger=json.loads(receipt_path.read_text())
        if ledger.get('planDigest')!=plan_data['digest'] or ledger.get('project')!='VocabularyIT-audio':raise ValueError('Účtenka patří jinému zdroji nebo hlasu.')
    jobs=plan_data['jobs'];selected=set(jobs)
    if uids is not None:
        if set(uids)-set(plan_data['manifests']['words']['items']):raise ValueError('Neznámé UID vzorku.')
        selected={record[lang] for manifest in plan_data['manifests'].values() for uid,record in manifest['items'].items() if uid in uids for lang in ('it','cz')}
    pending=[];verified={}
    # Audit all uncertain requests before any new external call.
    for relative,job in jobs.items():
        target=output/relative
        if not target.resolve().is_relative_to(output):raise ValueError('Zvuková cesta mimo výstup.')
        entry=ledger['jobs'].get(relative)
        if entry and entry.get('state') in {'requested','uncertain'}:
            if not (entry.get('sha256') and target.is_file() and digest(target)==entry['sha256'] and valid_audio(target)):
                raise ValueError('Nejistý předchozí požadavek se nesmí automaticky opakovat: '+relative)
        if target.exists():
            if not entry or entry.get('sha256')!=digest(target) or not valid_audio(target):raise ValueError('Existující zvuk nemá platný původ/SHA: '+relative)
            verified[relative]=entry
        elif entry and entry.get('state') in {'completed','reused'}:raise ValueError('Dokončený zvuk se ztratil; nejprve obnov soubor: '+relative)
        elif relative in selected:pending.append((relative,job))
    if limit is not None:pending=pending[:limit]
    def save():atomic(receipt_path,encoded(ledger))
    def generate(pair):
        nonlocal generated,reused
        relative,job=pair;target=output/relative
        with lock:
            if stopped.is_set():return
            if source_guard is not None and not source_guard():
                stopped.set();raise ValueError('Zdroj se změnil, další text se neodešle.')
            if not target.resolve().is_relative_to(output):raise ValueError('Zvuková cesta opustila výstup.')
            source=reuse.get((job['voice'],job['rate'],job['text']))
            ledger['jobs'][relative]={'state':'requested','textDigest':hashlib.sha256(job['text'].encode()).hexdigest()};save()
        try:
            if source is not None:
                if not valid_audio(source):raise ValueError('Zdroj pro znovupoužití není platná MP3.')
                audio=source.read_bytes()
            else:audio=synthesize(job['text'],voice=job['voice'],rate=job['rate'])
            if not isinstance(audio,bytes) or len(audio)<1000:raise ValueError('Syntéza nevrátila MP3.')
            atomic(target,audio)
            if not valid_audio(target):raise ValueError('Neplatná MP3 nebo nulová délka.')
        except Exception:
            stopped.set()
            with lock:ledger['jobs'][relative]['state']='uncertain';save()
            raise
        with lock:
            ledger['jobs'][relative]={'state':'reused' if source else 'completed','sha256':digest(target),'bytes':len(audio)}
            reused+=bool(source);generated+=not bool(source);save()
            if (generated+reused)%25==0 or len(pending)<=40:print(f'Audio: {generated} nových, {reused} převzatých, {len(pending)} v této dávce',flush=True)
    with ThreadPoolExecutor(max_workers=workers) as pool:list(pool.map(generate,pending))
    # Publish neither manifest until both kinds are complete and verified.
    missing=[p for p in jobs if p not in ledger['jobs'] or ledger['jobs'][p].get('state') not in {'completed','reused'}]
    if not missing:
        for relative in jobs:
            if not valid_audio(output/relative) or digest(output/relative)!=ledger['jobs'][relative]['sha256']:raise ValueError('Závěrečná kontrola MP3 selhala.')
        if source_guard is not None and not source_guard():raise ValueError('Zdroj se změnil; nové manifesty se nezveřejní.')
        for kind,manifest in plan_data['manifests'].items():
            manifest=dict(manifest);manifest['assetSha256']={p:ledger['jobs'][p]['sha256'] for p,j in jobs.items() if j['kind']==kind}
            name='vocabulary-it-audio.json' if kind=='words' else 'vocabulary-it-sentence-audio.json';atomic(output/'data'/name,encoded(manifest))
    return {'generated':generated,'reused':reused,'verifiedExisting':len(verified),'missing':len(missing),'complete':not missing,'requestedSubset':len(pending)}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,required=True);parser.add_argument('--output',type=Path,default=ROOT/'docs');parser.add_argument('--apply',action='store_true');parser.add_argument('--receipt',type=Path);parser.add_argument('--uids',nargs='+');parser.add_argument('--workers',type=int,default=3);parser.add_argument('--limit',type=int)
    args=parser.parse_args();planned=plan(load_items(args.root,args.output))
    if not args.apply:print(json.dumps(planned['stats'],ensure_ascii=False));return
    if args.receipt is None:parser.error('--apply vyžaduje privátní --receipt')
    if not args.receipt.resolve().is_relative_to((ROOT/'Samantha_Agent/data/private').resolve()):parser.error('Účtenka musí zůstat v privátním projektovém adresáři.')
    sources=[CATALOG,args.root/'VocabularyIT/VocabularyIT.csv',args.output/'data/vocabulary-it-v2.json']
    pinned={path:digest(path) for path in sources}
    guard=lambda:all(path.is_file() and digest(path)==sha for path,sha in pinned.items())
    with registered_generator() as synthesize:result=build(planned,args.output,args.receipt,synthesize=synthesize,reuse=reuse_index(ROOT),uids=args.uids,workers=args.workers,limit=args.limit,source_guard=guard)
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':main()
