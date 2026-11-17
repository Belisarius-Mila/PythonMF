"""Explicit private FR input catalog. No personal data or default data paths.

UIDs are assigned editorially once. CSV Order and learner flags never resolve
identity. A changed spelling, meaning or sentence requires an explicit catalog
revision, not an automatic new UID.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import unicodedata

COLUMNS = ('FR', 'CZ', 'Order', 'Sentence', 'SentenceT', 'L', 'HT', 'gender_fr')
FIELDS = ('fr', 'cz', 'sentenceFr', 'sentenceCz')
PARTS = {'noun', 'verb', 'adjective', 'adverb', 'pronoun', 'number',
         'preposition', 'conjunction', 'article', 'determiner', 'particle',
         'interjection', 'verb-modal'}


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def digest(path):
    return sha(Path(path).read_bytes())


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def identity(body):
    values = tuple(body.get(k) for k in FIELDS)
    if any(not isinstance(v, str) or not v.strip() for v in values):
        raise ValueError('Incomplete source identity.')
    return tuple(unicodedata.normalize('NFC', v.strip()) for v in values)


def body(row):
    return dict(zip(FIELDS, (row['FR'], row['CZ'], row['Sentence'], row['SentenceT'])))


def load_rows(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != COLUMNS:
            raise ValueError('Unexpected CSV columns.')
        rows = list(reader)
    orders = set()
    for row in rows:
        if set(row) != set(COLUMNS) or any(v is None for v in row.values()):
            raise ValueError('Incomplete source row.')
        identity(body(row))
        if (not re.fullmatch(r'[1-9][0-9]*', row['Order']) or row['Order'] in orders
                or row['L'] not in {'ano', 'ne'} or row['HT'] not in {'ano', 'ne'}
                or row['gender_fr'] not in {'', 'm', 'f'}):
            raise ValueError('Invalid source row metadata.')
        orders.add(row['Order'])
    return rows


def validate_catalog(catalog):
    if catalog.get('schemaVersion') != 1 or catalog.get('language') != 'fr':
        raise ValueError('Invalid FR catalog.')
    groups = catalog.get('groups', [])
    group_ids = {g['id'] for g in groups}
    if len(groups) != 18 or group_ids != {f'topic-{n:02d}' for n in range(1, 19)}:
        raise ValueError('Exactly 18 topics required.')
    entries = catalog.get('entries', [])
    if not entries or len(entries) != catalog.get('itemCount'):
        raise ValueError('Invalid catalog size.')
    uids, ids, sources = set(), set(), set()
    for entry in entries:
        uid, number = entry.get('uid'), entry.get('id')
        if (type(number) is not int or number < 1 or number in ids
                or uid != f'vfr-{number:04d}' or uid in uids):
            raise ValueError('Invalid or duplicate permanent identity.')
        uids.add(uid); ids.add(number)
        identity(entry['body'])
        if entry['body'].get('genderFr') not in {'', 'm', 'f'}:
            raise ValueError('Invalid French gender.')
        if (entry.get('primaryGroup') not in group_ids
                or not isinstance(entry.get('topicIds'), list)
                or not set(entry['topicIds']) <= group_ids
                or entry['primaryGroup'] not in entry['topicIds']
                or not entry.get('partOfSpeech') or not set(entry['partOfSpeech']) <= PARTS
                or entry.get('teachingType') not in {'word', 'interaction', 'idiom'}
                or entry.get('expressionType') not in {'word', 'phrase'}
                or type(entry.get('active')) is not bool
                or type(entry.get('difficultyBand')) is not int or entry['difficultyBand'] not in {1, 2, 3}
                or entry.get('difficultyStatus') not in {'proposed', 'reviewed'}
                or entry.get('imageReviewed') is not True
                or entry.get('imageRole') not in {'literal', 'contextual', 'mnemonic'}
                or not re.fullmatch(r'[0-9a-f]{64}', entry.get('imageSha256', ''))):
            raise ValueError('Invalid editorial metadata: ' + uid)
        matches = [entry['sourceIdentity'], *entry.get('omittedSources', [])]
        for match in matches:
            key = identity(match)
            if key in sources:
                raise ValueError('Ambiguous source identity.')
            sources.add(key)
    for entry in entries:
        if (not set(entry.get('related', [])) <= uids
                or entry.get('formOfUid') not in uids | {None}
                or entry['uid'] in entry.get('related', [])):
            raise ValueError('Unknown related meaning.')
    if len(sources) != catalog.get('sourceRowCount'):
        raise ValueError('Catalog must account for every source row.')
    return catalog


def resolve_rows(rows, catalog):
    """Resolve closed source identities; return bodies and private merged hints."""
    validate_catalog(catalog)
    index = {}
    for entry in catalog['entries']:
        for key in [entry['sourceIdentity'], *entry.get('omittedSources', [])]:
            index[identity(key)] = entry['uid']
    seen, hints = set(), {e['uid']: {'learned': False, 'hard': False} for e in catalog['entries']}
    for row in rows:
        key = identity(body(row))
        if key in seen or key not in index:
            raise ValueError('Unknown or duplicated source; revise catalog explicitly.')
        seen.add(key)
        hint = hints[index[key]]
        hint['learned'] |= row['L'] == 'ano'
        hint['hard'] |= row['HT'] == 'ano'
    if seen != set(index):
        raise ValueError('Source selection is incomplete.')
    return catalog['entries'], hints


def safe_file(root, relative):
    """Exact case, regular resident file, no symlinks or traversal."""
    root = Path(root).absolute()
    if (not isinstance(relative, str) or not relative or '\\' in relative
            or relative != PurePosixPath(relative).as_posix()
            or PurePosixPath(relative).is_absolute()
            or any(p in {'', '.', '..'} for p in relative.split('/'))):
        raise ValueError('Unsafe relative file path.')
    path = root
    for part in relative.split('/'):
        if not path.is_dir() or part not in {p.name for p in path.iterdir()}:
            raise ValueError('Missing or wrong-case file: ' + relative)
        path = path / part
        if path.is_symlink():
            raise ValueError('Symlink input is not accepted.')
    if not path.is_file() or getattr(path.stat(), 'st_flags', 0) & 0x40000000:
        raise ValueError('Input is not a resident regular file.')
    return path


def private_output(path):
    """Require an explicit ignored destination inside any Git checkout."""
    path = Path(path).absolute()
    for part in [path, *path.parents]:
        if part.is_symlink():
            raise ValueError('Private output cannot traverse symlinks.')
    for parent in [path, *path.parents]:
        if (parent / '.git').exists():
            relative = path.relative_to(parent)
            if 'docs' in relative.parts or '.git' in relative.parts:
                raise ValueError('Public/Git metadata output is forbidden.')
            result = subprocess.run(['git', '-C', str(parent), 'check-ignore', '-q', '--', str(relative)],
                                    capture_output=True, check=False)
            if result.returncode != 0:
                raise ValueError('Private output must be Git-ignored.')
            tracked = subprocess.run(['git', '-C', str(parent), 'ls-files', '--', str(relative)],
                                     capture_output=True, check=True)
            if tracked.stdout:
                raise ValueError('Private destination contains tracked files.')
            break
    return path
