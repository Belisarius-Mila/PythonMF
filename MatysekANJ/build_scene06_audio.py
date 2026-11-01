#!/usr/bin/env python3
"""Build fixed Scene 6 audio with input- and content-bound receipts."""
import asyncio
import argparse
from datetime import datetime, timezone
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
from app.speech.azure_tts_mp3 import CharacterBudget, ssml_parts, synthesize_azure_tts_mp3_sync

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


async def synthesize_scene_edge(text, *, voice, rate):
    import edge_tts.communicate as edge_communicate
    from edge_tts.constants import TRUSTED_CLIENT_TOKEN
    previous = edge_communicate.WSS_URL
    try:
        edge_communicate.WSS_URL = 'wss://api.msedgeservices.com/tts/cognitiveservices/websocket/v1?Ocp-Apim-Subscription-Key=' + TRUSTED_CLIENT_TOKEN
        return await synthesize_edge_tts_mp3(text, voice=voice, rate=rate)
    finally:
        edge_communicate.WSS_URL = previous


async def generate_one(i, lang, row, bindings, ffmpeg, synth=synthesize_scene_edge):
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
    try:
        data=await synth(text,voice=voice,rate=RATE)
    except Exception as exc:
        raise RuntimeError(f'Generování {key} selhalo ({type(exc).__name__}); zastaveno bez opakování.') from None
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


def preview_selection(story):
    selected = []
    seen = set()
    for i, row in enumerate(story):
        for lang in ('en', 'cs'):
            voice = VOICES[row[0]] if lang == 'en' else 'cs-CZ-VlastaNeural'
            if voice in seen or (ROOT/'audio'/lang/f'{i:03}.mp3').is_file():
                continue
            seen.add(voice)
            selected.append((i, lang, row))
    return selected


async def generate_preview(story, ffmpeg, synth, budget):
    directory = REPO/'Samantha_Agent/data/private/mmtx/scene06_azure_preview'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    directory.mkdir(parents=True, exist_ok=False)
    receipt = {'provider': 'azure', 'status': 'running', 'clips': [],
               'story_sha256': hashlib.sha256(json.dumps(story, ensure_ascii=False).encode()).hexdigest()}
    def save():
        receipt['reserved_characters'] = budget.reserved
        receipt['character_limit'] = budget.limit
        (directory/'preview.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    try:
        for number, (i, lang, row) in enumerate(preview_selection(story), 1):
            text = row[1 if lang == 'en' else 2]
            voice = VOICES[row[0]] if lang == 'en' else 'cs-CZ-VlastaNeural'
            save()
            data = await synth(text, voice=voice, rate=RATE)
            decode(data, ffmpeg)
            name = f'{number:02}_{voice}_{lang}_{i:03}.mp3'
            with (directory/name).open('xb') as handle:
                handle.write(data)
            receipt['clips'].append({**expected(row, lang, data), 'file': name, 'source': f'{lang}/{i:03}'})
            save()
            print('Ukázka', number, voice, flush=True)
            await asyncio.sleep(4)
        mix_preview(directory, receipt['clips'], ffmpeg)
        receipt['listening_file'] = 'listen_all.mp3'
        receipt['status'] = 'completed'
    except BaseException:
        receipt['status'] = 'failed'
        raise
    finally:
        save()
        print('Ukázky:', directory, flush=True)
    return directory


def mix_preview(directory, clips, ffmpeg):
    if not clips:
        raise RuntimeError('Žádné chybějící hlasy k poslechové ukázce.')
    argv = [ffmpeg, '-nostdin', '-v', 'error', '-n']
    for clip in clips:
        argv += ['-i', str(directory/clip['file'])]
    filters = [f'[{i}:a]apad=pad_dur=1[a{i}]' for i in range(len(clips))]
    filters.append(''.join(f'[a{i}]' for i in range(len(clips))) + f'concat=n={len(clips)}:v=0:a=1[out]')
    argv += ['-filter_complex', ';'.join(filters), '-map', '[out]', '-codec:a',
             'libmp3lame', '-b:a', '48k', '-ar', '24000', str(directory/'listen_all.mp3')]
    result = subprocess.run(argv, capture_output=True, timeout=60, check=False)
    if result.returncode:
        raise RuntimeError('Spojení poslechových ukázek selhalo; jednotlivé MP3 zachované.')
    decode((directory/'listen_all.mp3').read_bytes(), ffmpeg)


async def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    for flag in ('--check', '--apply', '--preview'):
        mode.add_argument(flag, action='store_true')
    parser.add_argument('--provider', choices=('edge', 'azure'), default='edge')
    parser.add_argument('--max-characters', type=int, default=10_000)
    args = parser.parse_args(argv)
    budget = CharacterBudget(args.max_characters)
    if args.preview and args.provider != 'azure':
        parser.error('--preview vyžaduje --provider azure')
    ffmpeg=shutil.which('ffmpeg')
    if not ffmpeg: raise SystemExit('Chybí ffmpeg: nelze ověřit MP3, síťová generace se nespustí.')
    story=json.loads((ROOT/'story.json').read_text(encoding='utf8'))
    bindings=json.loads((ROOT/'audio_bindings.json').read_text(encoding='utf8'))
    if args.check:
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
    cap=get_capability('generate_project_azure_audio_asset' if args.provider == 'azure' else 'generate_project_audio_asset')
    tool = 'app.speech.azure_tts_mp3.synthesize_azure_tts_mp3_sync' if args.provider == 'azure' else 'app.speech.edge_tts_mp3.synthesize_edge_tts_mp3_sync'
    if cap.risk != RiskLevel.EXTERNAL_GENERATION or cap.tool != tool: raise RuntimeError('Nesouhlasí registrovaná capability')
    if not all(trusted_external_generation_text_allowed(t) for row in story for t in row[1:3]): raise RuntimeError('Nepovolený text')
    async def azure_synth(text, *, voice, rate):
        return await asyncio.to_thread(synthesize_azure_tts_mp3_sync, text, voice=voice, rate=rate, budget=budget)
    synth = azure_synth if args.provider == 'azure' else synthesize_scene_edge
    selected = preview_selection(story) if args.preview else [(i, lang, row) for i, row in enumerate(story) for lang in ('en', 'cs') if not (ROOT/'audio'/lang/f'{i:03}.mp3').is_file()]
    if args.provider == 'azure':
        planned = sum(ssml_parts(row[1 if lang == 'en' else 2], VOICES[row[0]] if lang == 'en' else 'cs-CZ-VlastaNeural', RATE)[1] for _, lang, row in selected)
        if planned > budget.limit:
            raise RuntimeError('Plán překračuje limit znaků; žádný požadavek neodeslán.')
        print('Azure plán:', len(selected), 'stop,', planned, 'účtovaných znaků; limit', budget.limit, flush=True)
    if args.preview:
        return await generate_preview(story, ffmpeg, synth, budget)
    try:
        for i,row in enumerate(story):
            for lang in ('en','cs'):
                await generate_one(i,lang,row,bindings,ffmpeg,synth=synth)
                if args.provider == 'azure': await asyncio.sleep(4)
    finally:
        sync_assets(story,bindings)
    print('Hotovo',len(story)*2,flush=True)

if __name__=='__main__': asyncio.run(main())
