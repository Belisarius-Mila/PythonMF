#!/usr/bin/env python3
"""Build fixed Scene 6 audio with input- and content-bound receipts."""
import asyncio
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / 'docs/scene06_lake_arrival'
MIRROR = REPO / 'MatysekANJ/web_mmtx/scene06_lake_arrival'
sys.path.insert(0, str(REPO / 'Samantha_Agent'))
from app.capabilities import RiskLevel, get_capability
from app.communication.trusted_external_generation import trusted_external_generation_text_allowed
from app.speech.edge_tts_mp3 import synthesize_edge_tts_mp3

RATE = '-10%'
VOICES = {'bruno':'en-US-GuyNeural','benji':'en-US-AndrewNeural','bunny':'en-US-AnaNeural','sunny':'en-US-MichelleNeural','fiona':'en-US-JennyNeural','logan':'en-US-ChristopherNeural','daisy':'en-US-AnaNeural','freddie':'en-US-GuyNeural','dotty':'en-US-JennyNeural','ollie':'en-US-AndrewNeural'}


def expected(row, lang, data):
    return {'text':row[1 if lang=='en' else 2], 'voice':VOICES[row[0]] if lang=='en' else 'cs-CZ-VlastaNeural', 'rate':RATE, 'sha256':hashlib.sha256(data).hexdigest()}


def validate_binding(row, lang, data, receipt):
    if not receipt or receipt != expected(row, lang, data):
        raise RuntimeError('Zvuk neodpovídá textu, hlasu, rychlosti nebo otisku; původní soubor zachován, je třeba nový verzovaný výstup.')


def decode(data, ffmpeg):
    if not data or len(data)<1000:
        raise RuntimeError('Prázdný nebo příliš krátký zvuk')
    result=subprocess.run([ffmpeg,'-v','error','-i','pipe:0','-f','null','-'],input=data,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,check=False)
    if result.returncode: raise RuntimeError('MP3 nelze dekódovat')


def prepare_parent(path):
    path.parent.mkdir(parents=True,exist_ok=True)


async def generate_one(i, lang, row, bindings, ffmpeg, synth=synthesize_edge_tts_mp3):
    path=ROOT/'audio'/lang/f'{i:03}.mp3'
    key=f'{lang}/{i:03}'
    if path.is_file():
        data=path.read_bytes()
        validate_binding(row,lang,data,bindings.get(key))
        decode(data,ffmpeg)
        return
    if key in bindings:
        raise RuntimeError(f'Chybí soubor k existující účtence {key}; bez automatické obnovy.')
    prepare_parent(path)
    text=row[1 if lang=='en' else 2]
    voice=VOICES[row[0]] if lang=='en' else 'cs-CZ-VlastaNeural'
    import edge_tts.communicate as edge_communicate
    from edge_tts.constants import TRUSTED_CLIENT_TOKEN
    previous=edge_communicate.WSS_URL
    try:
        edge_communicate.WSS_URL='wss://api.msedgeservices.com/tts/cognitiveservices/websocket/v1?Ocp-Apim-Subscription-Key='+TRUSTED_CLIENT_TOKEN
        try: data=await synth(text,voice=voice,rate=RATE)
        except Exception as exc: raise RuntimeError(f'Generování {key} selhalo ({type(exc).__name__}); zastaveno bez opakování.') from None
    finally: edge_communicate.WSS_URL=previous
    decode(data,ffmpeg)
    # Refuse to overwrite a path that appeared during generation.
    with path.open('xb') as handle: handle.write(data)
    bindings[key]=expected(row,lang,data)
    (ROOT/'audio_bindings.json').write_text(json.dumps(bindings,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf8')
    print(key,flush=True)


def sync_assets(story, bindings):
    available={'en':{},'cs':{}}
    for lang in available:
        for i,row in enumerate(story):
            key=f'{lang}/{i:03}'
            rel=Path('audio')/lang/f'{i:03}.mp3';src=ROOT/rel
            if src.is_file():
                validate_binding(row,lang,src.read_bytes(),bindings.get(key))
                available[lang][f'{i:03}']=rel.as_posix();dst=MIRROR/rel
                prepare_parent(dst);shutil.copyfile(src,dst)
    payload='window.SCENE06_AUDIO = '+json.dumps(available,ensure_ascii=False,indent=2)+';\n'
    (ROOT/'audio_manifest.js').write_text(payload,encoding='utf8')
    (MIRROR/'audio_manifest.js').write_text(payload,encoding='utf8')
    shutil.copyfile(ROOT/'audio_bindings.json',MIRROR/'audio_bindings.json')


async def main():
    if sys.argv[1:] not in (['--check'],['--apply']): raise SystemExit('Použij --check nebo výslovné --apply.')
    ffmpeg=shutil.which('ffmpeg')
    if not ffmpeg: raise SystemExit('Chybí ffmpeg: nelze ověřit MP3, síťová generace se nespustí.')
    story=json.loads((ROOT/'story.json').read_text(encoding='utf8'))
    bindings=json.loads((ROOT/'audio_bindings.json').read_text(encoding='utf8'))
    if sys.argv[1:]==['--check']:
        missing=0
        for i,row in enumerate(story):
            for lang in ('en','cs'):
                key=f'{lang}/{i:03}';path=ROOT/'audio'/lang/f'{i:03}.mp3'
                if not path.is_file():
                    if key in bindings: raise RuntimeError(f'Chybí soubor k účtence {key}')
                    missing+=1;continue
                data=path.read_bytes();validate_binding(row,lang,data,bindings.get(key));decode(data,ffmpeg)
        print(f'Audio {len(story)*2-missing}/{len(story)*2}; chybí {missing}')
        if missing: raise SystemExit(1)
        return
    # Validate every existing asset before sending any request.
    for i,row in enumerate(story):
        for lang in ('en','cs'):
            key=f'{lang}/{i:03}';path=ROOT/'audio'/lang/f'{i:03}.mp3'
            if path.is_file():
                data=path.read_bytes();validate_binding(row,lang,data,bindings.get(key));decode(data,ffmpeg)
            elif key in bindings:
                raise RuntimeError(f'Chybí soubor k účtence {key}; generování zastaveno.')
    cap=get_capability('generate_project_audio_asset')
    if cap.risk != RiskLevel.EXTERNAL_GENERATION or cap.tool != 'app.speech.edge_tts_mp3.synthesize_edge_tts_mp3_sync': raise RuntimeError('Nesouhlasí registrovaná capability')
    if not all(trusted_external_generation_text_allowed(t) for row in story for t in row[1:3]): raise RuntimeError('Nepovolený text')
    try:
        for i,row in enumerate(story):
            for lang in ('en','cs'): await generate_one(i,lang,row,bindings,ffmpeg)
    finally:
        sync_assets(story,bindings)
    print('Hotovo',len(story)*2,flush=True)

if __name__=='__main__': asyncio.run(main())
