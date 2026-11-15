"""Internal Vocabulary EN authoring: preview, staged media, recoverable local apply.

The chat supplies reviewed meanings and image candidates. This module never
calls an LLM, changes learner storage, commits Git, or publishes a website.
"""
from __future__ import annotations

import copy
import csv
import fcntl
import hashlib
import importlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

PROJECT = Path(__file__).resolve().parents[1]
TOOLS = PROJECT.parent / 'VocabularyEN'
CSV = 'VocabularyEN/VocabularyEN.csv'
CATALOG = 'VocabularyEN/vocabulary_en_catalog.json'
DATA = ('docs/data/vocabulary-en.json', 'docs/data/vocabulary-en-audio.json',
        'docs/data/vocabulary-en-sentence-audio.json')
MEDIA = ('docs/assets/vocabulary-en', 'docs/assets/vocabulary-en-thumbs',
         'docs/assets/vocabulary-en-audio', 'docs/assets/vocabulary-en-sentences')
FIELDS = ('en', 'cz', 'sentenceEn', 'sentenceCz', 'partOfSpeech', 'primaryGroup',
          'topicIds', 'difficultyBand', 'teachingType')
POS = {'noun', 'verb', 'adjective', 'adverb', 'pronoun', 'number', 'preposition',
       'conjunction', 'article', 'determiner', 'particle', 'interjection', 'verb-modal', 'other'}


class AuthoringError(ValueError):
    """An exact draft cannot safely continue."""


def _digest(value) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':')).encode()).hexdigest()


def _sha(path: Path) -> str | None:
    if path.is_symlink():
        raise AuthoringError('Symbolický odkaz není povolený autorský cíl.')
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def _atomic(path: Path, data: bytes, *, scratch: Path | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    directory = scratch or path.parent
    directory.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=directory, prefix='.authoring-', delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(data); handle.flush(); os.fsync(handle.fileno())
    os.replace(temporary, path)


def _save(path: Path, value) -> None:
    _atomic(path, (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode())


def _tools():
    if str(TOOLS) not in sys.path:
        sys.path.insert(0, str(TOOLS))
    return tuple(importlib.import_module(name) for name in
                 ('sync_vocabulary_en_to_docs', 'build_vocabulary_en_audio',
                  'build_vocabulary_en_sentence_audio', 'build_audio_casting'))


def parse_input(value) -> list[dict]:
    """One item, a list, or an explicitly headed UTF-8 CSV share one schema."""
    if isinstance(value, str):
        lines = value.lstrip('\ufeff')
        first = lines.splitlines()[0] if lines.splitlines() else ''
        delimiters = [d for d in (';', ',', '\t') if {'EN', 'CZ'} <= set(next(csv.reader([first], delimiter=d)))]
        if len(delimiters) != 1:
            raise AuthoringError('CSV potřebuje jednoznačnou hlavičku EN a CZ.')
        value = list(csv.DictReader(io.StringIO(lines), delimiter=delimiters[0]))
    if isinstance(value, dict):
        value = value.get('items', [value])
    if not isinstance(value, list) or not 1 <= len(value) <= 100:
        raise AuthoringError('Zadej jednu až100 položek.')
    result = []
    for raw in value:
        if not isinstance(raw, dict) or None in raw:
            raise AuthoringError('Neplatné sloupce autorského vstupu.')
        if set(raw)-set(FIELDS)-{'EN','CZ','Sentence','SentenceT'}:
            raise AuthoringError('Neznámé sloupce; technická ID a osobní příznaky se neimportují.')
        item = {k: raw.get(k, raw.get({'en':'EN', 'cz':'CZ', 'sentenceEn':'Sentence',
                                     'sentenceCz':'SentenceT'}.get(k, k))) for k in FIELDS}
        for k in ('en', 'cz', 'sentenceEn', 'sentenceCz', 'primaryGroup'):
            v = item[k]
            if v is not None and not isinstance(v, str):
                raise AuthoringError('Textové pole musí být text.')
            item[k] = ' '.join((v or '').split())
            if len(item[k]) > (1500 if k.startswith('sentence') else 250):
                raise AuthoringError('Autorské pole je příliš dlouhé.')
        if not item['en'] or not item['cz']:
            raise AuthoringError('Každá položka potřebuje EN a CZ.')
        parts = item['partOfSpeech'] or []
        if isinstance(parts, str): parts = parts.split('|')
        if not isinstance(parts, list) or any(not isinstance(p,str) or p not in POS for p in parts):
            raise AuthoringError('Neplatný slovní druh.')
        item['partOfSpeech'] = list(dict.fromkeys(parts))
        topics = item['topicIds'] or ([item['primaryGroup']] if item['primaryGroup'] else [])
        if isinstance(topics, str): topics = topics.split('|')
        if not isinstance(topics, list) or any(not isinstance(x, str) for x in topics):
            raise AuthoringError('Neplatná témata.')
        item['topicIds'] = list(dict.fromkeys(topics))
        band = item['difficultyBand'] if item['difficultyBand'] is not None else 1
        if isinstance(band, str) and band in {'1','2','3'}: band = int(band)
        if type(band) is not int or band not in {1,2,3}:
            raise AuthoringError('Náročnost musí být1/2/3.')
        item['difficultyBand'] = band
        item['teachingType'] = item['teachingType'] or 'word'
        if not isinstance(item['teachingType'],str) or item['teachingType'] not in {'word','interaction','idiom'}:
            raise AuthoringError('Neplatný typ učiva.')
        result.append(item)
    return result


class VocabularyAuthoring:
    def __init__(self, repo_root: Path = PROJECT.parent, *, store_root: Path | None = None,
                 synthesize: Callable | None = None):
        self.repo = Path(repo_root).resolve()
        self.store = Path(store_root or self.repo/'Samantha_Agent/data/private/vocabulary_authoring').resolve()
        self.synthesize = synthesize

    @contextmanager
    def _lock(self):
        self.store.mkdir(parents=True, exist_ok=True)
        if self.store.stat().st_dev != self.repo.stat().st_dev:
            raise AuthoringError('Autorský prostor a zdroj musí být na stejném svazku.')
        with (self.store/'authoring.lock').open('a') as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            try: yield
            finally: fcntl.flock(handle, fcntl.LOCK_UN)

    def _job_path(self, request_id: str) -> Path:
        if not isinstance(request_id, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{7,100}', request_id):
            raise AuthoringError('Neplatná identita dávky.')
        return self.store/request_id/'job.json'

    def _snapshot(self) -> dict:
        paths = {self.repo/p for p in (CSV, CATALOG, *DATA)}
        for directory in (*MEDIA, 'VocabularyEN/Pict'):
            base = self.repo/directory
            if base.exists(): paths.update(p for p in base.rglob('*') if p.is_file())
        head = subprocess.check_output(['git','-C',str(self.repo),'rev-parse','HEAD'], text=True).strip()
        code = [Path(__file__), *(TOOLS/n for n in ('sync_vocabulary_en_to_docs.py',
                'build_vocabulary_en_audio.py','build_vocabulary_en_sentence_audio.py','build_audio_casting.py'))]
        return {'head':head, 'code':_digest({p.name:_sha(p) for p in code}),
                'files':{p.relative_to(self.repo).as_posix():_sha(p) for p in sorted(paths)}}

    def preview(self, items) -> dict:
        rows = parse_input(items)
        source = self._snapshot()
        catalog = json.loads((self.repo/CATALOG).read_text())
        current = json.loads((self.repo/DATA[0]).read_text())['items']
        by_uid = {i['uid']:i for i in current}
        key = lambda en,cz:(en.strip().casefold(),cz.strip().casefold())
        aliases = {key(m['en'],m['cz']):e for e in catalog['entries'] for m in e['matches']}
        groups = {g['id'] for g in catalog['groups']}
        seen, plans = set(), []
        for row in rows:
            pair = key(row['en'],row['cz']); entry = aliases.get(pair)
            status, missing = 'new', []
            if pair in seen: status = 'duplicate-in-batch'
            elif entry:
                item = by_uid.get(entry['uid'])
                status = 'existing' if item and item.get('active',True) else 'retired'
                if item and row['partOfSpeech'] and set(row['partOfSpeech']) != set(item['partOfSpeech']):
                    status = 'needs-review'
            else:
                missing = [k for k in ('sentenceEn','sentenceCz','partOfSpeech','primaryGroup') if not row[k]]
                if missing: status = 'incomplete'
                if row['primaryGroup'] and (row['primaryGroup'] not in groups or
                        row['primaryGroup'] not in row['topicIds'] or not set(row['topicIds']) <= groups):
                    raise AuthoringError('Téma nepatří do současného katalogu.')
            seen.add(pair)
            plans.append({'key':_digest(pair)[:16], 'item':row, 'status':status,
                          'existingUid':entry['uid'] if entry else None, 'missing':missing,
                          'otherMeanings':[i['uid'] for i in current if i['en'].casefold()==row['en'].casefold()]})
        return {'items':plans,'source':source,'digest':_digest({'source':source,'items':rows}),
                'newCount':sum(x['status']=='new' for x in plans),
                'ready':all(x['status'] in {'new','existing','duplicate-in-batch'} for x in plans)}

    def _check_source(self, source: dict, changes: dict | None = None):
        now = self._snapshot(); changes = changes or {}
        if (now['head'],now['code']) != (source['head'],source['code']):
            raise AuthoringError('Zdrojový head nebo autorský kód se změnil.')
        for path, before in source['files'].items():
            actual = now['files'].get(path)
            if actual != before and (path not in changes or actual != changes[path]):
                raise AuthoringError('Souběžně změněný zdroj: '+path)
        for path, actual in now['files'].items():
            if path not in source['files'] and actual != changes.get(path):
                raise AuthoringError('Souběžně přidaný zdroj: '+path)

    def prepare(self, request_id: str, items, *, images: dict[str,str], expected_preview: str,
                confirmed: bool) -> dict:
        if confirmed is not True: raise AuthoringError('Příprava vyžaduje zadaný autorský úkol.')
        rows = parse_input(items)
        image_inputs = {k:{'path':str(Path(p).resolve()),'sha256':_sha(Path(p))} for k,p in images.items()}
        fingerprint = _digest({'items':rows,'images':image_inputs,'preview':expected_preview})
        path = self._job_path(request_id)
        with self._lock():
            if path.exists():
                job = json.loads(path.read_text())
                if job['fingerprint'] != fingerprint: raise AuthoringError('Identita dávky už patří jinému zadání.')
                if job['state'] in {'prepared','applying','applied'}: return self._receipt(job)
                self._check_source(job['source'])
            else:
                preview = self.preview(rows)
                if preview['digest'] != expected_preview or not preview['ready']:
                    raise AuthoringError('Návrh se změnil nebo potřebuje doplnit.')
                additions = [x for x in preview['items'] if x['status']=='new']
                if set(images) != {x['key'] for x in additions}:
                    raise AuthoringError('Každý nový význam potřebuje právě jeden zkontrolovaný obrázek.')
                catalog = json.loads((self.repo/CATALOG).read_text())
                ids = [e['id'] for e in catalog['entries']]
                for saved in self.store.glob('*/job.json'):
                    ids += [e['id'] for e in json.loads(saved.read_text()).get('additions',[])]
                next_id = max(ids,default=0)+1
                for offset,entry in enumerate(additions): entry.update(id=next_id+offset,uid=f'ven-{next_id+offset:04d}')
                job = {'request_id':request_id,'fingerprint':fingerprint,'state':'preparing',
                       'source':preview['source'],'additions':additions,'media':{},'changes':{},
                       'existing':[x['existingUid'] for x in preview['items'] if x['status']=='existing']}
                _save(path,job)
            if not job['additions']:
                job['state']='prepared';job['prepared_digest']=self._seal(job);_save(path,job)
                return self._receipt(job)
            stage = path.parent/'stage'; sync,word,sentence,casting = _tools()
            if not (stage/'inputs.ready').exists():
                for directory in MEDIA:
                    source = self.repo/directory
                    if source.exists(): shutil.copytree(source,stage/directory,dirs_exist_ok=True)
                for relative in (CSV,CATALOG):
                    target = stage/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(self.repo/relative,target)
                self._stage_rows(job,stage,images)
                _atomic(stage/'inputs.ready',b'ready')
            csv_path = stage/CSV; output = stage/'docs'
            rows = sync.load_rows(csv_path);catalog = sync.load_catalog(csv_path)
            bases = [stage/'VocabularyEN/Pict', *sync.build_picture_base_dirs(self.repo,self.repo/CSV)]
            payload,assets = sync.build_export_payload(rows,bases,sync.load_external_mapping(bases,self.repo/CSV),
                sync.discover_picture_stems(bases),output,'vocabulary-en',CSV,catalog)
            sync.write_output(output,payload,assets,'vocabulary-en.json','vocabulary-en',preserve_extra_assets=True)
            original = {i['uid']:i for i in json.loads((self.repo/DATA[0]).read_text())['items']}
            for item in payload['items']:
                if item['uid'] in original:
                    old=original[item['uid']]
                    if any(item[k]!=old[k] for k in ('id','en','cz','sentenceEn','sentenceCz','image','thumbnail','active','selected','hardTraining','wordSets')):
                        raise AuthoringError('Příprava by změnila původní kartu: '+item['uid'])
                elif item['imageSource']!='catalog' or item['imageStem']!='ven'+str(item['id']).zfill(4):
                    raise AuthoringError('Nový obrázek není připnutý ke své kartě.')
            wm=word.build_manifest(payload['items']);sm=sentence.build_manifest(payload['items'])
            jobs={p:(text,word.asset_voice(lang,text)) for p,(text,lang) in word._asset_jobs(wm).items()}
            jobs.update(sentence.jobs(sm))
            synth=self.synthesize or casting.registered_synthesizer()
            for relative,(text,voice) in jobs.items():
                target=output/relative;previous=job['media'].get(relative)
                if target.is_file() and target.stat().st_size>=word.MIN_AUDIO_BYTES:
                    if previous and previous.get('sha256') and previous['sha256']!=_sha(target):
                        raise AuthoringError('Připravené audio bylo změněno.')
                    if previous and previous['state']!='completed':
                        job['media'][relative]={'state':'completed','sha256':_sha(target),'recovered':True};_save(path,job)
                    continue
                if previous:raise AuthoringError('Nejistý zvuk se nebude automaticky opakovat: '+relative)
                job['media'][relative]={'state':'requested'};_save(path,job)
                try:
                    data=synth(text,voice=voice,rate=casting.RATE)
                    if not isinstance(data,bytes) or len(data)<word.MIN_AUDIO_BYTES:raise AuthoringError('Neplatné MP3.')
                    _atomic(target,data)
                except BaseException:
                    job['media'][relative]={'state':'uncertain'};_save(path,job);raise
                job['media'][relative]={'state':'completed','sha256':_sha(target)};_save(path,job)
            _save(output/word.MANIFEST_RELATIVE_PATH,wm);_save(output/sentence.MANIFEST_RELATIVE_PATH,sm)
            word.verify_library(output,csv_path);assert sentence.audit(output,csv_path)['complete']
            changes={}
            candidates=[stage/CSV,stage/CATALOG,*[p for folder in ('docs','VocabularyEN/Pict') for p in (stage/folder).rglob('*') if p.is_file() and not p.name.startswith('.authoring-')]]
            for file in candidates:
                relative=file.relative_to(stage).as_posix();after=_sha(file);before=_sha(self.repo/relative)
                if before==after:continue
                if relative.startswith('docs/assets/') and before is not None:raise AuthoringError('Původní média se nepřepisují.')
                changes[relative]=after
            job.update(state='prepared',changes=changes)
            job['prepared_digest']=self._seal(job);_save(path,job)
            return self._receipt(job)

    def _stage_rows(self, job:dict, stage:Path, images:dict):
        from PIL import Image
        csv_path=stage/CSV;raw=csv_path.read_bytes()
        if not raw.endswith(b'\r\n') or b'\n' in raw.replace(b'\r\n',b''):
            raise AuthoringError('Zdrojové CSV musí zachovat CRLF.')
        fields=next(csv.reader([raw.decode('utf-8-sig').splitlines()[0]]))
        catalog=json.loads((stage/CATALOG).read_text());buffer=io.StringIO(newline='')
        writer=csv.DictWriter(buffer,fieldnames=fields,lineterminator='\r\n')
        for addition in job['additions']:
            item=addition['item'];stem='ven'+str(addition['id']).zfill(4);image=Path(images[addition['key']])
            if image.suffix.lower() not in {'.png','.jpg','.jpeg','.webp'} or image.stat().st_size>25*1024*1024:
                raise AuthoringError('Nepodporovaný nebo příliš velký obrázek.')
            with Image.open(image) as im:im.verify()
            destination=stage/'VocabularyEN/Pict'/(stem+image.suffix.lower())
            destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(image,destination)
            writer.writerow({'EN':item['en'],'CZ':item['cz'],'Order':addition['id'],
                             'Sentence':item['sentenceEn'],'SentenceT':item['sentenceCz'],'WS':'','L':'ne','HT':'ne'})
            related=[]
            for entry in catalog['entries']:
                if any(m['en'].casefold()==item['en'].casefold() for m in entry['matches']):
                    related.append({'uid':entry['uid'],'kind':'same-lemma'})
                    entry['related'].append({'uid':addition['uid'],'kind':'same-lemma'})
            catalog['entries'].append({**{k:item[k] for k in ('partOfSpeech','primaryGroup','topicIds','difficultyBand','teachingType')},
                'id':addition['id'],'uid':addition['uid'],'matches':[{'en':item['en'],'cz':item['cz']}],
                'expressionType':'phrase' if len(item['en'].split())>1 else 'word','active':True,
                'difficultyStatus':'draft','editorialStatus':'reviewed','imageStemOverride':stem,
                'galleryOrder':max((e['galleryOrder'] for e in catalog['entries'] if e['primaryGroup']==item['primaryGroup']),default=0)+1,
                'related':related})
        _atomic(csv_path,raw+buffer.getvalue().encode());_save(stage/CATALOG,catalog)

    @staticmethod
    def _seal(job):
        return _digest({k:job[k] for k in ('request_id','fingerprint','source','additions','changes')})

    @staticmethod
    def _receipt(job):
        return {'request_id':job['request_id'],'state':job['state'],
                'digest':job.get('prepared_digest'),'newCount':len(job['additions']),
                'items':[{'uid':a['uid'],'id':a['id'],'en':a['item']['en'],'cz':a['item']['cz']} for a in job['additions']],
                'existing':job['existing'],'changedFiles':len(job['changes']),
                'generatedAudio':sum(m['state']=='completed' for m in job['media'].values())}

    def status(self, request_id:str) -> dict:
        return self._receipt(json.loads(self._job_path(request_id).read_text()))

    def apply(self, request_id:str, *, expected_digest:str, confirmed:bool) -> dict:
        if confirmed is not True:raise AuthoringError('Zařazení vyžaduje autorské zadání.')
        path=self._job_path(request_id)
        with self._lock():
            job=json.loads(path.read_text())
            if job['state'] not in {'prepared','applying','applied'} or self._seal(job)!=expected_digest or job.get('prepared_digest')!=expected_digest:
                raise AuthoringError('Nepřipravená nebo změněná dávka.')
            if job['state']=='applied':return self._receipt(job)
            changes=job['changes'];stage=path.parent/'stage'
            for relative,after in changes.items():
                allowed=(relative in (CSV,CATALOG,*DATA)
                         or re.fullmatch(r'VocabularyEN/Pict/ven[0-9]+\.(png|jpg|jpeg|webp)',relative)
                         or re.fullmatch(r'docs/assets/vocabulary-en(?:-thumbs)?/[a-z0-9-]+\.(png|jpg|jpeg|webp)',relative)
                         or re.fullmatch(r'docs/assets/vocabulary-en-(?:audio|sentences)/[a-z0-9-]+/[a-f0-9]{20}\.mp3',relative))
                if not allowed or '..' in Path(relative).parts or _sha(stage/relative)!=after:
                    raise AuthoringError('Změněný nebo nepovolený připravený soubor.')
                target=self.repo/relative
                if any(p.is_symlink() for p in [target,*target.parents] if p!=self.repo.parent):
                    raise AuthoringError('Autorský cíl obsahuje symbolický odkaz.')
                if _sha(target) not in {job['source']['files'].get(relative),after}:
                    raise AuthoringError('Cizí změna cíle: '+relative)
            self._check_source(job['source'],changes if job['state']=='applying' else None)
            job['state']='applying';_save(path,job)
            # All bytes have been checked before the first mutation. A retry accepts
            # only original or this exact batch's bytes, never a foreign edit.
            for relative,after in sorted(changes.items()):
                target=self.repo/relative
                current=_sha(target)
                if current not in {job['source']['files'].get(relative),after}:
                    raise AuthoringError('Cíl se změnil během zařazování: '+relative)
                if current!=after:
                    data=(stage/relative).read_bytes()
                    if hashlib.sha256(data).hexdigest()!=after:
                        raise AuthoringError('Připravený soubor se změnil během zařazování.')
                    _atomic(target,data,scratch=path.parent/'writes')
                if _sha(target)!=after:raise AuthoringError('Zápis souboru není potvrzený.')
            self._check_source(job['source'],changes)
            job.update(state='applied',applied_at=datetime.now(timezone.utc).isoformat());_save(path,job)
            return self._receipt(job)
