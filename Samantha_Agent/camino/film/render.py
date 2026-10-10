"""Deterministic P2-A export from one immutable synthetic timeline."""

from __future__ import annotations

import math
import os
import shutil
import threading
import time
import uuid
from pathlib import Path

from camino.film.media import duration_ms, ffmpeg, probe, title_image
from camino.film.project import FilmError, digest, fingerprint, load_project, source_path, validate, write_json


PROFILES = {'preview': (1280, 720, 25), 'final': (1920, 1080, 20)}
RESERVE_BYTES = 512 * 1024 * 1024


def directory_bytes(root: Path) -> tuple[int, int]:
    """Count hard-linked publication only once; report logical and allocated bytes."""
    seen, logical, allocated = set(), 0, 0
    for path in root.rglob('*'):
        if not path.is_file() or path.is_symlink():
            continue
        try:
            stat = path.stat()
        except FileNotFoundError:
            # Atomic JSON publication removes its own temporary file while sampled.
            continue
        identity = (stat.st_dev, stat.st_ino)
        if identity not in seen:
            seen.add(identity)
            logical += stat.st_size
            allocated += stat.st_blocks * 512
    return logical, allocated


class DiskMeter:
    """50ms sampled directory peaks, not a claim about whole-volume APFS usage."""

    def __init__(self, root: Path):
        self.root = root
        self.stop = threading.Event()
        self.peak = [0, 0]
        self.error: Exception | None = None
        self.thread = threading.Thread(target=self._sample, daemon=True)

    def sample(self) -> None:
        for i, value in enumerate(directory_bytes(self.root)):
            self.peak[i] = max(self.peak[i], value)

    def _sample(self) -> None:
        try:
            while not self.stop.wait(.05):
                self.sample()
        except Exception as exc:
            self.error = exc

    def __enter__(self):
        self.sample()
        self.thread.start()
        return self

    def __exit__(self, *_):
        self.stop.set()
        self.thread.join()
        self.sample()
        if self.error:
            raise FilmError('Měření disku selhalo; experiment není ověřený.') from self.error


def _inspect_sources(project: dict, root: Path) -> dict:
    metadata = {}
    for sid, source in project['sources'].items():
        info = probe(source_path(root, source))
        expected = 'audio' if source['kind'] == 'audio' else 'video'
        streams = [s for s in info['streams'] if s['codec_type'] == expected]
        if len(streams) != 1:
            raise FilmError('Nejasná nebo chybějící mediální stopa.')
        video = streams[0]
        if expected == 'video' and (video.get('width', 0) > 3840 or video.get('height', 0) > 3840):
            raise FilmError('Zdroj přesahuje rozměrový limit P2-A.')
        if video.get('color_transfer') in ('smpte2084', 'arib-std-b67') or video.get('color_primaries') == 'bt2020':
            raise FilmError('HDR zatím není ověřené; P2-A je odmítne bez změny barev.')
        if source['kind'] != 'photo' and abs(duration_ms(info, expected) - source['duration_ms']) > 50:
            raise FilmError('Délka zdroje nesouhlasí s manifestem.')
        metadata[sid] = info
    return metadata


def render(project_path: Path, profile: str, *, reserve_bytes: int = RESERVE_BYTES) -> dict:
    if profile not in PROFILES:
        raise FilmError('Neznámý profil exportu.')
    root = project_path.parent
    project = load_project(project_path)
    total_ms = validate(project, root)
    metadata = _inspect_sources(project, root)
    # Conservative bounded prototype estimate, not a production disk quota.
    estimate = math.ceil(total_ms / 1000 * 8_000_000) + 32 * 1024 * 1024
    if shutil.disk_usage(root).free < reserve_bytes + estimate:
        raise FilmError('Nedostatek místa pro bezpečný export.')
    output = root / f'{profile}-{uuid.uuid4().hex[:12]}'
    output.mkdir(mode=0o700)
    width, height, quality = PROFILES[profile]
    args: list[str] = []
    graph: list[str] = []
    next_input = 0

    def add_input(path: Path, *, photo: bool = False) -> int:
        nonlocal next_input
        index = next_input
        next_input += 1
        if photo:
            args.extend(['-loop', '1', '-framerate', '30'])
        args.extend(['-protocol_whitelist', 'file,pipe', '-i', str(path)])
        return index

    started = time.monotonic()
    free_before = shutil.disk_usage(root).free
    with DiskMeter(output) as meter:
        for n, shot in enumerate(project['shots']):
            source = project['sources'][shot['source']]
            seconds = (shot['out_ms'] - shot['in_ms']) / 1000
            start, end = shot['in_ms'] / 1000, shot['out_ms'] / 1000
            media = add_input(source_path(root, source), photo=source['kind'] == 'photo')
            title = output / f'title-{n}.png'
            title_image(title, shot['title'], (width, height))
            overlay = add_input(title)
            graph.append(
                f'[{media}:v]trim=start={start}:end={end},setpts=PTS-STARTPTS,fps=30,'
                f'scale={width}:{height}:force_original_aspect_ratio=decrease:force_divisible_by=2,'
                f'pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1,format=yuv420p[base{n}]')
            graph.append(f'[base{n}][{overlay}:v]overlay=eof_action=repeat:shortest=0,trim=duration={seconds}[v{n}]')
            has_audio = any(s['codec_type'] == 'audio' for s in metadata[shot['source']]['streams'])
            if has_audio:
                prefix = f'[{media}:a]atrim=start={start}:end={end},asetpts=PTS-STARTPTS,'
            else:
                prefix = 'anullsrc=r=48000:cl=stereo,'
            graph.append(prefix + f'aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,'
                         f'volume={shot["gain"]},apad,atrim=duration={seconds}[a{n}]')
        labels = ''.join(f'[v{n}][a{n}]' for n in range(len(project['shots'])))
        graph.append(f'{labels}concat=n={len(project["shots"])}:v=1:a=1[video][bed]')
        bed = 'bed'
        voices = []
        for n, voice in enumerate(project['voices']):
            start = voice['at_ms'] / 1000
            end = start + (voice['out_ms'] - voice['in_ms']) / 1000
            graph.append(f'[{bed}]volume=0.2:enable=\'between(t,{start},{end})\'[duck{n}]')
            bed = f'duck{n}'
            index = add_input(source_path(root, project['sources'][voice['source']]))
            graph.append(f'[{index}:a]atrim=start={voice["in_ms"]/1000}:end={voice["out_ms"]/1000},'
                         f'asetpts=PTS-STARTPTS,aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,'
                         f'volume={voice["gain"]},adelay={voice["at_ms"]}:all=1,'
                         f'apad,atrim=duration={total_ms/1000}[voice{n}]')
            voices.append(f'[voice{n}]')
        # .8 headroom; mixing never normalizes the narration away at silence boundaries.
        graph.append(f'[{bed}]{"".join(voices)}amix=inputs={1+len(voices)}:normalize=0:duration=longest,'
                     f'volume=0.8,atrim=duration={total_ms/1000}[audio]')
        partial = output / 'render.partial.mp4'
        ffmpeg([*args, '-filter_complex', ';'.join(graph), '-map', '[video]', '-map', '[audio]',
                '-map_metadata', '-1', '-map_chapters', '-1', '-c:v', 'libx264', '-threads', '2',
                '-preset', 'veryfast', '-crf', str(quality), '-pix_fmt', 'yuv420p',
                '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-movflags', '+faststart', str(partial)])
        info = probe(partial)
        video = next(s for s in info['streams'] if s['codec_type'] == 'video')
        audio = next(s for s in info['streams'] if s['codec_type'] == 'audio')
        if (video['width'], video['height']) != (width, height) or video['codec_name'] != 'h264' or audio['codec_name'] != 'aac':
            raise FilmError('Výstup má chybný formát.')
        if any(abs(duration_ms(info, kind) - total_ms) > 80 for kind in ('video', 'audio')):
            raise FilmError('Výstup usekl nebo prodloužil časovou osu.')
        ffmpeg(['-protocol_whitelist', 'file,pipe', '-i', str(partial), '-f', 'null', '-'])
        validate(project, root)  # No publication if any source changed during export.
        if load_project(project_path) != project:
            raise FilmError('Projekt se během renderu změnil.')
        final = output / 'film.mp4'
        os.link(partial, final)  # Create-only publication, retain failure/intermediate evidence.
        with final.open('rb') as handle:
            os.fsync(handle.fileno())
    receipt = {
        'schema': 1, 'status': 'verified', 'scope': 'synthetic-p2a', 'profile': profile,
        'project_fingerprint': fingerprint(project), 'revision': project['revision'],
        'timeline_ms': total_ms, 'video_ms': duration_ms(info, 'video'),
        'audio_ms': duration_ms(info, 'audio'), 'width': width, 'height': height,
        'output': str(final.relative_to(root)), 'sha256': digest(final), 'bytes': final.stat().st_size,
        'elapsed_seconds': round(time.monotonic() - started, 3),
        'peak_work_logical_bytes': meter.peak[0], 'peak_work_allocated_bytes': meter.peak[1],
        'peak_sampling_ms': 50, 'free_before_bytes': free_before,
        'free_after_bytes': shutil.disk_usage(root).free,
        'decoded_entire_file': True, 'mac_human_playback': 'NOT_VERIFIED',
        'iphone_playback': 'NOT_VERIFIED', 'speech_fixture': 'local-macos-tts-not-author-voice',
    }
    write_json(output / 'receipt.json', receipt)
    return receipt
