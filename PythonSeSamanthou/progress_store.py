"""Atomic local progress for macOS/Linux, with a non-destructive v1 migration."""
from copy import deepcopy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import tempfile

from course_loader import valid_id


# This order describes the ORIGINAL seven lessons. Never derive it from a new course order.
LEGACY_IDS = tuple('python-zaklady.' + name for name in (
    'prvni-prikaz', 'promenne', 'pocitani', 'prvni-obrazek', 'cykly', 'podminky', 'funkce'))
LEGACY_COURSE_ID = 'python-zaklady'


class ProgressError(ValueError):
    pass


def decode(raw):
    try:
        data = json.loads(raw.decode('utf-8'))
    except (UnicodeError, ValueError) as exc:
        raise ProgressError('Postup má neplatný obsah; původní soubor zůstává zachovaný.') from exc
    if not isinstance(data, dict):
        raise ProgressError('Postup musí obsahovat objekt.')
    return data


def validate(data):
    if type(data.get('version')) is not int or data['version'] != 2 or not isinstance(data.get('courses'), dict):
        raise ProgressError('Nepodporovaná verze nebo struktura uloženého postupu.')
    for course_id, state in data['courses'].items():
        if not valid_id(course_id) or not isinstance(state, dict):
            raise ProgressError('Neplatná identita kurzu v uloženém postupu.')
        if state.get('current') is not None and not valid_id(state['current']):
            raise ProgressError('Neplatná identita aktuální lekce.')
        completed, drafts = state.get('completed'), state.get('drafts')
        if not isinstance(completed, list) or not all(valid_id(x) for x in completed):
            raise ProgressError('Neplatný seznam dokončených lekcí.')
        if not isinstance(drafts, dict) or not all(valid_id(k) and isinstance(v, str) for k, v in drafts.items()):
            raise ProgressError('Neplatný seznam rozepsaných lekcí.')
    return data


def migrate_v1(data):
    if type(data.get('version', 1)) is not int or data.get('version', 1) != 1:
        raise ProgressError('Původní postup má nepodporovanou verzi; nepřevádím ho.')
    drafts, completed, current = data.get('drafts', {}), data.get('completed', []), data.get('current', 0)
    if not isinstance(drafts, dict) or not all(
            k in {str(i) for i in range(7)} and isinstance(v, str) for k, v in drafts.items()):
        raise ProgressError('Původní rozepsané lekce nelze beze ztráty převést.')
    if not isinstance(completed, list) or not all(type(i) is int and 0 <= i < 7 for i in completed):
        raise ProgressError('Původní seznam dokončených lekcí nelze převést.')
    if type(current) is not int or not 0 <= current < 7:
        raise ProgressError('Původní vybraná lekce není mezi původními sedmi lekcemi.')
    return {'version': 2, 'courses': {LEGACY_COURSE_ID: {
        'current': LEGACY_IDS[current], 'completed': sorted({LEGACY_IDS[i] for i in completed}),
        'drafts': {LEGACY_IDS[int(k)]: v for k, v in drafts.items()}}}}


def read_optional(path):
    try:
        return path.read_bytes()
    except FileNotFoundError:
        return None


class ProgressStore:
    def __init__(self, directory=None):
        self.directory = Path(directory) if directory is not None else Path.home() / '.python_se_samanthou'
        self.path = self.directory / 'prubeh_v2.json'
        self.legacy_path = self.directory / 'prubeh.json'
        self.backup_path = self.directory / 'prubeh_v1_pred_prevodem.json'
        self._revision = None
        self._legacy = None
        self._loaded = False

    def load(self):
        self._loaded = False
        raw = read_optional(self.path)
        self._revision = raw
        self._legacy = None
        warning = ''
        if raw is not None:
            state = validate(decode(raw))
            migrated = state.get('migration', {})
            legacy = read_optional(self.legacy_path)
            if isinstance(migrated, dict) and migrated.get('legacy_sha256') and legacy is not None:
                if hashlib.sha256(legacy).hexdigest() != migrated['legacy_sha256']:
                    warning = 'Původní učebna mezitím změnila svůj postup. Tato verze používá samostatný prubeh_v2.json.'
        else:
            self._legacy = read_optional(self.legacy_path)
            if self._legacy is None:
                state = {'version': 2, 'courses': {}}
            else:
                state = migrate_v1(decode(self._legacy))
                state['migration'] = {'legacy_sha256': hashlib.sha256(self._legacy).hexdigest()}
                warning = 'Původní postup byl načten. Nová verze ukládá samostatně; původní soubor zůstává zachovaný.'
        self._loaded = True
        return deepcopy(state), warning

    def save(self, state):
        if not self._loaded:
            raise ProgressError('Postup nebyl bezpečně načten; ukládání je zastavené.')
        validate(state)
        raw = (json.dumps(state, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
        self.directory.mkdir(parents=True, exist_ok=True)
        # A retained advisory lock serializes two running copies on the same computer.
        with (self.directory / 'prubeh_v2.lock').open('a+b') as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            if read_optional(self.path) != self._revision:
                raise ProgressError('Postup změnila jiná spuštěná učebna. Zkopíruj si pokus a znovu otevři aplikaci.')
            if self._legacy is not None:
                if read_optional(self.legacy_path) != self._legacy:
                    raise ProgressError('Původní postup se během převodu změnil. Zavři původní učebnu a otevři novou znovu.')
                backup = read_optional(self.backup_path)
                if backup is not None and backup != self._legacy:
                    raise ProgressError('Záloha původního postupu už obsahuje jiná data; nepřepisuji ji.')
                if backup is None:
                    fd = os.open(self.backup_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                    with os.fdopen(fd, 'wb') as handle:
                        handle.write(self._legacy)
                        handle.flush()
                        os.fsync(handle.fileno())
            temporary = None
            try:
                with tempfile.NamedTemporaryFile(dir=self.directory, prefix='.prubeh_v2-', suffix='.tmp', delete=False) as handle:
                    temporary = Path(handle.name)
                    handle.write(raw)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temporary, self.path)
                self._revision = raw
                self._legacy = None
            finally:
                # Remove only this save's own unfinished temporary file.
                if temporary is not None and temporary.exists():
                    temporary.unlink()
