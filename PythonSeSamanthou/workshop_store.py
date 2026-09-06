"""Private offline experiments, stored independently of course progress."""
from copy import deepcopy
import fcntl
import json
import os
from pathlib import Path
import tempfile
import uuid

from course_loader import valid_id
from progress_store import read_optional

MAX_SOURCE = 50_000


class WorkshopError(ValueError):
    pass


def validate(state):
    if not isinstance(state, dict) or type(state.get('version')) is not int or state['version'] != 1:
        raise WorkshopError('Neznámý formát dílny; uložené pokusy zůstávají zachované.')
    experiments = state.get('experiments')
    if not isinstance(experiments, dict) or len(experiments) > 1000:
        raise WorkshopError('Neplatný seznam pokusů v dílně.')
    if state.get('current') is not None and state['current'] not in experiments:
        raise WorkshopError('Vybraný pokus v dílně chybí.')
    for key, item in experiments.items():
        if not valid_id(key) or not isinstance(item, dict):
            raise WorkshopError('Neplatný záznam pokusu.')
        for field, limit in [('title', 80), ('source', MAX_SOURCE), ('notes', 10_000)]:
            value = item.get(field)
            if not isinstance(value, str) or len(value) > limit:
                raise WorkshopError(f'Pole {field} má neplatný obsah nebo překračuje limit {limit} znaků.')
        if not item['title'].strip() or '\n' in item['title'] or '\r' in item['title']:
            raise WorkshopError('Pokus potřebuje krátký název na jednom řádku.')
    return state


def add_experiment(state, title, source='', notes=''):
    key = 'p-' + uuid.uuid4().hex
    candidate = deepcopy(state)
    candidate['experiments'][key] = {'title': title.strip(), 'source': source, 'notes': notes}
    candidate['current'] = key
    validate(candidate)
    state.update(candidate)
    return key


def import_python(path):
    with Path(path).open('rb') as handle:
        raw = handle.read(MAX_SOURCE * 4 + 4)
    try:
        source = raw.decode('utf-8-sig')
    except UnicodeError as exc:
        raise WorkshopError('Soubor není text Pythonu v kódování UTF-8.') from exc
    if len(source) > MAX_SOURCE or '\x00' in source:
        raise WorkshopError('Pro dílnu vyber textový program do 50 000 znaků.')
    return source


def export_python(path, source):
    # Export always creates a new file; it never replaces another program.
    with Path(path).open('x', encoding='utf-8', newline='') as handle:
        handle.write(source)


class WorkshopStore:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.path = self.directory / 'dilna.json'
        self._loaded = False
        self._revision = None

    def load(self):
        self._loaded = False
        raw = read_optional(self.path)
        try:
            state = {'version': 1, 'current': None, 'experiments': {}} if raw is None else json.loads(raw.decode('utf-8'))
            validate(state)
        except (ValueError, UnicodeError, TypeError) as exc:
            raise WorkshopError(f'Dílnu nelze bezpečně načíst: {exc}') from exc
        self._revision = raw
        self._loaded = True
        return deepcopy(state)

    def save(self, state):
        if not self._loaded:
            raise WorkshopError('Dílna nebyla načtena; uložené pokusy nepřepisuji.')
        validate(state)
        raw = (json.dumps(state, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
        self.directory.mkdir(parents=True, exist_ok=True)
        with (self.directory / 'dilna.lock').open('a+b') as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            if read_optional(self.path) != self._revision:
                raise WorkshopError('Pokusy změnila jiná otevřená dílna. Zkopíruj svůj kód a dílnu znovu otevři.')
            temporary = None
            try:
                with tempfile.NamedTemporaryFile(dir=self.directory, prefix='.dilna-', suffix='.tmp', delete=False) as handle:
                    temporary = Path(handle.name)
                    handle.write(raw)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temporary, self.path)
                self._revision = raw
            finally:
                if temporary is not None and temporary.exists():
                    temporary.unlink()
