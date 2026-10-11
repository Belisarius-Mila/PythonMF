"""Generated calibration media only; never enumerate Camino's real archive."""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from camino.film.media import FONT, duration_ms, ffmpeg, probe, run
from camino.film.project import FilmError, digest, save_project, write_json


SPEECH = ('Toto je syntetická zkouška filmové dílny Camino. '
          'Vidíme fotografii, celé video na šířku i na výšku a záběr, který se správně otočil. '
          'Komentář pokračuje přes střihy. Šťastnou cestu.')


def create_fixture(root: Path) -> Path:
    """Create all source files in a newly reserved run directory."""
    sources = root / 'sources'
    sources.mkdir(mode=0o700)
    image = Image.new('RGB', (960, 540), '#183c46')
    draw = ImageDraw.Draw(image)
    draw.rectangle((16, 16, 943, 523), outline='#eccb86', width=6)
    draw.ellipse((700, 65, 810, 175), fill='#eccb86')
    draw.polygon([(0, 410), (240, 200), (470, 430), (620, 270), (960, 475), (960, 540), (0, 540)], fill='#34736e')
    draw.text((65, 55), 'CAMINO / P2-A', font=ImageFont.truetype(str(FONT), 43), fill='white')
    draw.text((65, 115), 'Syntetická zkouška', font=ImageFont.truetype(str(FONT), 27), fill='white')
    image.save(sources / 'photo.png')
    # Entire clips, different source frame rates; colored border shows any cropping.
    for name, size, fps, frequency in [('landscape', '640x360', 24, 220), ('portrait', '360x640', 30, 330)]:
        ffmpeg(['-f', 'lavfi', '-i', f'testsrc2=size={size}:rate={fps}',
                '-f', 'lavfi', '-i', f'sine=frequency={frequency}:sample_rate=48000',
                '-t', '5', '-vf', 'drawbox=x=0:y=0:w=iw:h=ih:color=yellow:t=8',
                '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac',
                '-metadata', 'comment=SYNTHETIC-ONLY', str(sources / f'{name}.mp4')])
    # Exercise display-matrix autorotation, not just a physically tall raster.
    ffmpeg(['-display_rotation:v:0', '90', '-i', str(sources / 'landscape.mp4'), '-c', 'copy',
            str(sources / 'rotated.mp4')])
    rotation = probe(sources / 'rotated.mp4')['streams'][0].get('side_data_list', [])
    if not any(abs(s.get('rotation', 0)) == 90 for s in rotation):
        raise FilmError('Syntetický klip nemá požadovanou matici otočení.')
    run(['/usr/bin/say', '-v', 'Zuzana', '-r', '165', '-o', str(root / 'speech-fixture.aiff'), SPEECH])
    ffmpeg(['-i', str(root / 'speech-fixture.aiff'), '-ar', '48000', '-ac', '1', '-c:a', 'pcm_s16le',
            str(sources / 'voice.wav')])
    manifest = {}
    for sid, name, kind in [('photo', 'photo.png', 'photo'), ('landscape', 'landscape.mp4', 'video'),
                             ('portrait', 'portrait.mp4', 'video'), ('rotated', 'rotated.mp4', 'video'),
                             ('voice', 'voice.wav', 'audio')]:
        manifest[sid] = {'file': name, 'kind': kind, 'revision': 1, 'sha256': digest(sources / name),
                         'duration_ms': 0 if kind == 'photo' else duration_ms(probe(sources / name), kind if kind == 'audio' else 'video'),
                         'privacy': 'diary', 'synthetic': True}
    voice_ms = manifest['voice']['duration_ms']
    # Keep a closing picture long enough for the full voice and one final second.
    closing_ms = max(3000, math.ceil((voice_ms + 1000 - 19000) / 1000) * 1000)
    shots, cursor = [], 0
    for n, (sid, length, title) in enumerate([
        ('photo', 4000, 'Český titulek: Příliš žluťoučký kůň'),
        ('landscape', 5000, 'Vodorovné video • celý záběr 0–5 s'),
        ('portrait', 5000, 'Svislé video • celý obraz bez ořezu'),
        ('rotated', 5000, 'Otočení podle metadat • celý záběr'),
        ('photo', closing_ms, 'Šťastnou cestu!'),
    ]):
        shots.append({'id': f'shot-{n}', 'source': sid, 'source_revision': 1,
                      'at_ms': cursor, 'in_ms': 0, 'out_ms': length, 'title': title,
                      'title_origin': 'synthetic', 'manual': False, 'gain': .6})
        cursor += length
    # The closing phrase belongs near the end, with one second of picture after it.
    voice_at_ms = cursor - voice_ms - 1000
    project = {'schema': 1, 'scope': 'synthetic-p2a', 'id': 'camino-p2a-demo', 'revision': 1,
               'sources': manifest, 'shots': shots,
               'voices': [{'id': 'narration', 'source': 'voice', 'source_revision': 1, 'at_ms': voice_at_ms,
                           'in_ms': 0, 'out_ms': voice_ms, 'manual': False, 'gain': 1.0}]}
    path = root / 'project-r1.json'
    save_project(path, project)
    write_json(root / 'fixture.json', {'synthetic': True, 'speech': SPEECH,
               'speech_origin': 'macOS Zuzana; technical fixture only, no cloned or author voice',
               'originals_sha256': {k: s['sha256'] for k, s in manifest.items()}})
    return path
