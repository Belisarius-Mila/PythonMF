"""Small local FFmpeg boundary and Czech title rasterization."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from camino.film.project import FilmError


FONT = Path('/System/Library/Fonts/Supplemental/Arial.ttf')


def binary(name: str) -> str:
    value = shutil.which(name)
    if not value:
        raise FilmError(f'Chybí místní nástroj {name}.')
    return value


def run(argv: list[str], *, timeout: int = 180) -> subprocess.CompletedProcess:
    """Argument vector only. No shell, remote protocols or inherited stdin."""
    try:
        result = subprocess.run(argv, stdin=subprocess.DEVNULL, capture_output=True,
                                timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise FilmError('Mediální proces se nedokončil.') from exc
    if result.returncode:
        raise FilmError('Mediální proces selhal: ' + result.stderr.decode(errors='replace')[-1200:])
    return result


def ffmpeg(args: list[str], *, timeout: int = 180) -> None:
    run([binary('ffmpeg'), '-nostdin', '-hide_banner', '-v', 'error', '-xerror', '-n',
         '-threads', '2', '-filter_complex_threads', '1', *args], timeout=timeout)


def probe(path: Path) -> dict:
    result = run([binary('ffprobe'), '-v', 'error', '-protocol_whitelist', 'file,pipe',
                  '-show_streams', '-show_format', '-of', 'json', str(path)])
    return json.loads(result.stdout)


def duration_ms(info: dict, kind: str | None = None) -> int:
    stream = next((s for s in info['streams'] if s['codec_type'] == kind), {})
    value = stream.get('duration', info.get('format', {}).get('duration', '0'))
    return round(float(value) * 1000)


def title_image(path: Path, text: str, size: tuple[int, int]) -> None:
    """Text never enters the FFmpeg filter language; preserve Czech glyphs."""
    if not FONT.is_file():
        raise FilmError('Chybí ověřený font Arial pro české titulky.')
    width, height = size
    font = ImageFont.truetype(str(FONT), round(height * .045))
    image = Image.new('RGBA', size)
    draw = ImageDraw.Draw(image)
    lines, line = [], ''
    for word in text.split():
        candidate = (line + ' ' + word).strip()
        if draw.textlength(candidate, font=font) > width * .88:
            if not line or draw.textlength(word, font=font) > width * .88:
                raise FilmError('Titulek má příliš dlouhé slovo.')
            lines.append(line)
            line = word
        else:
            line = candidate
    if line:
        lines.append(line)
    if len(lines) > 3:
        raise FilmError('Titulek se nevejde do tří řádků.')
    line_height = round(height * .06)
    top = height - round(height * .045) - len(lines) * line_height
    if lines:
        draw.rectangle((0, top - 12, width, height), fill=(0, 0, 0, 190))
    for i, line in enumerate(lines):
        draw.text((width / 2, top + i * line_height), line, font=font,
                  anchor='mt', fill='white')
    with path.open('xb') as handle:
        image.save(handle, format='PNG')
