"""Immutable, bounded P2-A timeline and source manifest. No live archive reads."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from app.file_persistence import atomic_create_text


class FilmError(ValueError):
    """A film cannot be proved complete or valid."""


def digest(path: Path) -> str:
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def fingerprint(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    """Publish complete JSON exactly once; never replace an earlier revision."""
    atomic_create_text(path, json.dumps(value, ensure_ascii=False, indent=2,
                                       sort_keys=True, allow_nan=False) + '\n')


def _keys(value: Any, expected: str) -> None:
    if not isinstance(value, dict) or set(value) != set(expected.split()):
        raise FilmError('Neplatná struktura projektu.')


def _integer(value: Any, low: int, high: int) -> None:
    if type(value) is not int or not low <= value <= high:
        raise FilmError('Neplatný čas, revize nebo rozměr.')


def source_path(root: Path, source: dict) -> Path:
    """P2-A reads only simple files immediately inside its own sources folder."""
    name = source['file']
    if not isinstance(name, str) or not re.fullmatch(r'[a-z0-9_-]+\.(png|mp4|wav)', name):
        raise FilmError('Neplatná cesta zdroje.')
    directory = root / 'sources'
    path = directory / name
    if directory.is_symlink() or path.is_symlink() or not path.is_file():
        raise FilmError('Zdroj chybí nebo odkazuje mimo projekt.')
    return path


def validate(project: dict, root: Path, *, verify_files: bool = True) -> int:
    """Return total milliseconds. Unknown privacy, fields and versions fail closed."""
    _keys(project, 'schema scope id revision sources shots voices')
    if project['schema'] != 1 or type(project['schema']) is not int or project['scope'] != 'synthetic-p2a':
        raise FilmError('P2-A přijímá pouze svůj syntetický formát v1.')
    if not isinstance(project['id'], str) or not re.fullmatch(r'[a-z0-9-]{1,64}', project['id']):
        raise FilmError('Neplatné ID projektu.')
    _integer(project['revision'], 1, 1_000_000)
    sources, shots, voices = (project[k] for k in ('sources', 'shots', 'voices'))
    if not isinstance(sources, dict) or not 1 <= len(sources) <= 16:
        raise FilmError('Neplatný manifest.')
    for sid, source in sources.items():
        if not re.fullmatch(r'[a-z0-9-]{1,64}', sid):
            raise FilmError('Neplatné ID zdroje.')
        _keys(source, 'file kind revision sha256 duration_ms privacy synthetic')
        if source['kind'] not in ('photo', 'video', 'audio') or source['privacy'] != 'diary' or source['synthetic'] is not True:
            raise FilmError('Nepovolený nebo nejasný zdroj.')
        _integer(source['revision'], 1, 1_000_000)
        _integer(source['duration_ms'], 0 if source['kind'] == 'photo' else 1, 120_000)
        if not isinstance(source['sha256'], str) or not re.fullmatch(r'[a-f0-9]{64}', source['sha256']):
            raise FilmError('Neplatný hash zdroje.')
        path = source_path(root, source)
        if verify_files and digest(path) != source['sha256']:
            raise FilmError('Zdroj se změnil; manifest není platný.')
    if not isinstance(shots, list) or not 1 <= len(shots) <= 16 or not isinstance(voices, list) or len(voices) > 8:
        raise FilmError('Neplatný rozsah časové osy.')
    ids: set[str] = set()
    cursor = 0
    for shot in shots:
        _keys(shot, 'id source source_revision at_ms in_ms out_ms title title_origin manual gain')
        _item(shot, sources, ids)
        if sources[shot['source']]['kind'] not in ('photo', 'video'):
            raise FilmError('Obraz vyžaduje foto nebo video.')
        if shot['at_ms'] != cursor:
            raise FilmError('Obrazová osa má mezeru nebo překryv.')
        if not isinstance(shot['title'], str) or len(shot['title']) > 140 or any(ord(c) < 32 for c in shot['title']):
            raise FilmError('Neplatný titulek.')
        if shot['title_origin'] not in ('synthetic', 'user'):
            raise FilmError('Neznámý původ titulku.')
        cursor += shot['out_ms'] - shot['in_ms']
    _integer(cursor, 1, 120_000)
    ends = []
    for voice in voices:
        _keys(voice, 'id source source_revision at_ms in_ms out_ms manual gain')
        _item(voice, sources, ids)
        if sources[voice['source']]['kind'] != 'audio':
            raise FilmError('Hlas vyžaduje audio.')
        end = voice['at_ms'] + voice['out_ms'] - voice['in_ms']
        if end > cursor:
            raise FilmError('Hlas přesahuje obraz; nejprve doplň obrazovou osu.')
        if any(voice['at_ms'] < b and end > a for a, b in ends):
            raise FilmError('P2-A nepřekrývá více komentářů.')
        ends.append((voice['at_ms'], end))
    return cursor


def _item(item: dict, sources: dict, ids: set[str]) -> None:
    iid = item['id']
    if not isinstance(iid, str) or not re.fullmatch(r'[a-z0-9-]{1,64}', iid) or iid in ids:
        raise FilmError('Neplatné nebo duplicitní ID položky.')
    ids.add(iid)
    if not isinstance(item['source'], str) or item['source'] not in sources:
        raise FilmError('Chybí vazba na zdroj.')
    source = sources[item['source']]
    _integer(item['source_revision'], 1, 1_000_000)
    if item['source_revision'] != source['revision']:
        raise FilmError('Nesouhlasí revize zdroje.')
    for key in ('at_ms', 'in_ms', 'out_ms'):
        _integer(item[key], 0, 120_000)
    if item['out_ms'] <= item['in_ms'] or (source['kind'] != 'photo' and item['out_ms'] > source['duration_ms']):
        raise FilmError('Úsek překračuje zdroj nebo je prázdný.')
    if type(item['manual']) is not bool or type(item['gain']) not in (int, float) or not 0 <= item['gain'] <= 1:
        raise FilmError('Neplatné ruční nastavení nebo hlasitost.')


def load_project(path: Path) -> dict:
    if path.is_symlink() or path.stat().st_size > 128_000:
        raise FilmError('Neplatný soubor projektu.')
    try:
        project = json.loads(path.read_text(encoding='utf-8'))
        validate(project, path.parent)
        return project
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        raise FilmError('Poškozený projekt.') from exc


def save_project(path: Path, project: dict) -> None:
    validate(project, path.parent)
    write_json(path, project)
